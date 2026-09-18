"""Project only the frozen exposed images using the retained official devkit.

The annotation source remains a supplied geometric proxy. No model output is
read, and no detection loss is calculated here. Raw and derived records stay
in a fresh private directory; only their availability may enter a worker's
initial visible packet.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import sys
import time
import zipfile

from admission import encoded, digest, number, require
from local_export import ALLOCATION_SHA256, read_bound

REPOSITORY = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY / 'tools/measure'))
from reference_study import metadata

ARCHIVE_SHA256 = 'db48746b10e3544d5ef619eaa3d687e3960626fe1b4422ed856711da5aa7325b'
SDK_WHEEL_SHA256 = '76cee0e7f96ec96d6269ee3acb4ff69e8ac2f9413e974d9eb542233ea7479bf1'
TABLES = ('ego_pose', 'instance', 'category', 'calibrated_sensor', 'scene',
          'sample_data', 'sample_annotation', 'sensor', 'sample')


def utc():
    return datetime.now(timezone.utc).isoformat()


def file_binding(path):
    path = Path(path).resolve()
    h = hashlib.sha256(); size = 0
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(block); size += len(block)
    return {'path': str(path), 'sha256': h.hexdigest(), 'bytes': size}


def put(path, value):
    with Path(path).open('xb') as handle:
        handle.write(encoded(value))


def keep_once(table, row):
    require(type(row) is dict and type(row.get('token')) is str and row['token'],
            'METADATA', 'Record token missing')
    require(row['token'] not in table, 'METADATA', 'Duplicate retained record')
    table[row['token']] = row


def collect(archive, images):
    """One streaming archive pass; retain only selected records and join keys."""
    targets = {image['sensor_sample_token'] for image in images}
    poses = {image['evidence']['ego_pose']['token'] for image in images}
    calibrations = {image['evidence']['calibration']['token'] for image in images}
    samples = set(); seen = {name: 0 for name in TABLES}
    tables = {name: {} for name in TABLES}
    for filename, row in metadata(archive, [name + '.json' for name in TABLES]):
        name = filename[:-5]; seen[name] += 1
        if name == 'ego_pose' and row['token'] not in poses:
            continue
        if name == 'calibrated_sensor' and row['token'] not in calibrations:
            continue
        if name == 'sample_data':
            if row['token'] not in targets:
                continue
            samples.add(row['sample_token'])
        if name in ('sample', 'sample_annotation'):
            # The pinned archive places the complete sample_data table before
            # both dependent tables. Reject another order instead of dropping rows.
            require(set(tables['sample_data']) == targets, 'METADATA_ORDER', 'Image join table incomplete')
            sample_token = row['token'] if name == 'sample' else row['sample_token']
            if sample_token not in samples:
                continue
        keep_once(tables[name], row)
    require(set(tables['sample_data']) == targets and set(tables['sample']) == samples,
            'COVERAGE', 'Selected image or sample metadata missing')
    require(set(tables['ego_pose']) == poses and set(tables['calibrated_sensor']) == calibrations,
            'COVERAGE', 'Selected pose or calibration missing')
    instances = {row['instance_token'] for row in tables['sample_annotation'].values()}
    require(instances <= set(tables['instance']), 'COVERAGE', 'Annotation instance missing')
    tables['instance'] = {key: tables['instance'][key] for key in sorted(instances)}
    scenes = {row['scene_token'] for row in tables['sample'].values()}
    require(scenes <= set(tables['scene']), 'COVERAGE', 'Selected scene missing')
    tables['scene'] = {key: tables['scene'][key] for key in sorted(scenes)}
    return tables, seen


def qualify(tables, images):
    """Join completeness, custody and time must be checked before projection."""
    joined = copy.deepcopy(tables)
    for sample in joined['sample'].values():
        sample['anns'] = []
    for annotation in joined['sample_annotation'].values():
        instance = joined['instance'][annotation['instance_token']]
        category = joined['category'][instance['category_token']]
        annotation['category_name'] = category['name']
        joined['sample'][annotation['sample_token']]['anns'].append(annotation['token'])
    applicability = []
    for image in images:
        sd = joined['sample_data'][image['sensor_sample_token']]
        calibration = joined['calibrated_sensor'][sd['calibrated_sensor_token']]
        sensor = joined['sensor'][calibration['sensor_token']]
        pose = joined['ego_pose'][sd['ego_pose_token']]
        sample = joined['sample'][sd['sample_token']]
        require(sd['is_key_frame'] is True and sensor['modality'] == 'camera'
                and sensor['channel'] == 'CAM_FRONT', 'SOURCE', 'Only frozen front-camera keyframes qualify')
        require((sd['width'], sd['height']) == (image['width'], image['height']) == (1600, 900),
                'DIMENSION', 'Projection canvas differs from source bytes')
        evidence = image['evidence']
        require(sd['filename'] == evidence['relative_asset_path'] and sd['timestamp'] == evidence['sensor_timestamp_us'],
                'SOURCE', 'Image filename or camera timestamp differs')
        require(calibration == evidence['calibration'] and pose == evidence['ego_pose'],
                'SOURCE', 'Frozen calibration or pose differs from archive')
        read_bound({'path': image['image_path'], 'sha256': image['image_sha256'], 'bytes': image['bytes']})
        sd['sensor_modality'] = sensor['modality']; sd['channel'] = sensor['channel']
        applicability.append({'image_id': image['id'], 'image_sha256': image['image_sha256'],
            'sample_data_token': sd['token'], 'sample_token': sample['token'], 'scene_token': sample['scene_token'],
            'sensor_timestamp_us': sd['timestamp'], 'annotation_sample_timestamp_us': sample['timestamp'],
            'camera_minus_sample_us': sd['timestamp'] - sample['timestamp'],
            'calibration_sha256': digest(calibration), 'ego_pose_sha256': digest(pose),
            'annotation_tokens': sample['anns'], 'annotation_time_interpolation': False})
    return joined, applicability


def classify_projection(rows, image):
    eligible, exclusions, found = [], [], set()
    for row in rows:
        token = row['sample_annotation_token']
        require(token not in found, 'REFERENCE', 'Duplicate projected annotation')
        found.add(token)
        require(row['sample_data_token'] == image['sensor_sample_token'], 'REFERENCE', 'Projection image differs')
        xyxy = [float(value) for value in row['bbox_corners']]
        require(len(xyxy) == 4 and all(math.isfinite(value) for value in xyxy), 'REFERENCE', 'Nonfinite projection')
        x1, y1, x2, y2 = xyxy
        require(0 <= x1 < x2 <= image['width'] and 0 <= y1 < y2 <= image['height'],
                'REFERENCE', 'Projection outside the declared positive-area canvas')
        reason = 'category_outside_car' if row['category_name'] != 'vehicle.car' else (
            'height_below_25' if number(y2) - number(y1) < 25 else None)
        if reason is not None:
            exclusions.append({'record': row, 'reason': reason})
        else:
            eligible.append({'id': 'reference:' + token, 'record_sha256': digest(row), 'xyxy': xyxy})
    require(len(eligible) <= 128, 'REFERENCE_LIMIT', 'Existing matching adapter reference limit exceeded')
    return eligible, exclusions


def run(allocation_path, archive_path, sdk_wheel, output):
    start, tick = utc(), time.perf_counter()
    allocation_raw = read_bound({'path': str(Path(allocation_path).resolve()), 'sha256': ALLOCATION_SHA256})
    allocation = json.loads(allocation_raw); images = allocation['images']
    require(len(images) == 64 and len({image['id'] for image in images}) == 64,
            'ALLOCATION', 'Complete frozen allocation required')
    output = Path(output).resolve()
    require(not output.exists() and output.parent.is_dir(), 'OUTPUT', 'Fresh private output required')
    output.mkdir()
    archive_binding = file_binding(archive_path)
    require(archive_binding['sha256'] == ARCHIVE_SHA256, 'SOURCE', 'Annotation archive differs')
    wheel_binding = file_binding(sdk_wheel)
    require(wheel_binding['sha256'] == SDK_WHEEL_SHA256, 'SOURCE', 'Devkit wheel differs')
    require(importlib.metadata.version('nuscenes-devkit') == '1.2.0', 'RUNTIME', 'Devkit version differs')
    from nuscenes.scripts import export_2d_annotations_as_json as publisher
    from nuscenes.nuscenes import NuScenes
    members = []
    with zipfile.ZipFile(sdk_wheel) as wheel:
        for relative in ('nuscenes/scripts/export_2d_annotations_as_json.py', 'nuscenes/nuscenes.py',
                         'nuscenes/utils/geometry_utils.py', 'nuscenes/utils/data_classes.py'):
            installed = Path(publisher.__file__).resolve().parents[2] / relative
            raw = wheel.read(relative)
            require(installed.read_bytes() == raw, 'RUNTIME', 'Installed devkit source differs from retained wheel')
            members.append({'member': relative, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)})
    preparation_tick = time.perf_counter()
    tables, scanned = collect(archive_path, images)
    joined, applicability = qualify(tables, images)
    put(output / 'SELECTED_METADATA.json', tables)
    put(output / 'APPLICABILITY.json', applicability)
    metadata_seconds = time.perf_counter() - preparation_tick

    class SelectedArchive:
        get_box = NuScenes.get_box

        def get(self, table, token):
            # The publisher augments annotation dictionaries. Do not mutate the
            # retained source or share those mutations between images.
            return copy.deepcopy(joined[table][token])

    publisher.nusc = SelectedArchive()
    statuses = []
    for image, source in zip(images, applicability):
        began, image_tick = utc(), time.perf_counter()
        try:
            projections = publisher.get_2d_boxes(image['sensor_sample_token'], ['', '1', '2', '3', '4'])
            eligible, exclusions = classify_projection(projections, image)
            record = {'image_id': image['id'], 'image_sha256': image['image_sha256'],
                'state': 'observed', 'answer': eligible, 'source_applicability': source,
                'all_projection_rows': projections, 'exclusions': exclusions,
                'basis': 'published_annotation_projection', 'human_review': False}
        except Exception as exc:
            record = {'image_id': image['id'], 'image_sha256': image['image_sha256'],
                'state': 'unavailable', 'reason': type(exc).__name__ + ': ' + str(exc),
                'source_applicability': source, 'basis': 'published_annotation_projection', 'human_review': False}
        put(output / (image['id'] + '.json'), record)
        statuses.append({'image_id': image['id'], 'state': record['state'],
            'record_sha256': digest(record), 'started_utc': began, 'finished_utc': utc(),
            'seconds': time.perf_counter() - image_tick,
            'eligible_count': len(record['answer']) if record['state'] == 'observed' else None})
    result = {'artifact_id': 'reiyah.public-predictions.projection-result', 'version': '0.1.0',
        'started_utc': start, 'finished_utc': utc(), 'seconds': time.perf_counter() - tick,
        'metadata_seconds': metadata_seconds, 'allocation_sha256': ALLOCATION_SHA256,
        'source_archive': archive_binding, 'sdk_wheel': wheel_binding, 'verified_sdk_members': members,
        'runtime': {name: importlib.metadata.version(name) for name in
                    ('nuscenes-devkit', 'numpy', 'scipy', 'pyquaternion', 'shapely')},
        'records_scanned_by_table': scanned, 'selected_records_by_table': {name: len(rows) for name, rows in tables.items()},
        'images': statuses, 'scored_model_comparisons': 0, 'rec_d_outcomes_accessed': 0,
        'projection_is_physical_truth': False, 'human_seconds': None, 'economic_cost': None}
    put(output / 'RESULT.json', result)
    print(json.dumps({'allocated': len(images), 'observed': sum(row['state'] == 'observed' for row in statuses),
                      'seconds': result['seconds'], 'metadata_seconds': metadata_seconds}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--allocation', required=True); parser.add_argument('--archive', required=True)
    parser.add_argument('--sdk-wheel', required=True); parser.add_argument('--output', required=True)
    args = parser.parse_args()
    run(args.allocation, args.archive, args.sdk_wheel, args.output)
