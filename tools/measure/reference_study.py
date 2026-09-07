"""Offline, private reference-adjudication sampling and evidence preparation.

Raw inputs are read only. Outputs are created in a new directory, never updated
under an existing identity. No model, network, publication, or judgment authority.
"""
import argparse
import collections
import hashlib
import hmac
import json
import math
import pathlib
import sys
import tarfile

import numpy as np
from scipy.spatial import cKDTree

from result_ao_reference_population_audit import stream_array, digest

VERSION = '0.1.0'
STRATA = ('cache_near_control', 'excluded_annotation_near',
          'full_unmatched_coincident', 'full_unmatched_unpaired')
CHANNELS = ('CAM_FRONT', 'CAM_FRONT_LEFT', 'CAM_FRONT_RIGHT', 'CAM_BACK',
            'CAM_BACK_LEFT', 'CAM_BACK_RIGHT', 'LIDAR_TOP')
INPUTS = ('gt_val_cache.json', 'meta.tgz', 'predictions/mapillary_val.json',
          'predictions/megvii_val.json')


def read_json(path):
    def pairs(items):
        out = {}
        for k, v in items:
            if k in out:
                raise ValueError('Duplicate JSON key: ' + k)
            out[k] = v
        return out
    def invalid(value):
        raise ValueError('Nonfinite JSON constant: ' + value)
    return json.loads(pathlib.Path(path).read_bytes(), object_pairs_hook=pairs,
                      parse_constant=invalid)


def write_new(path, value):
    raw = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n'
    with pathlib.Path(path).open('x') as f:
        f.write(raw)


def bound_protocol(directory, key=None):
    protocol = read_json(directory / 'protocol.json')
    freeze = read_json(directory / 'freeze.json')
    if digest(directory / 'protocol.json') != freeze['protocol_sha256']:
        raise ValueError('Protocol changed after freeze')
    if key is not None and (len(key) != 32 or
            hashlib.sha256(key).hexdigest() != freeze['selection_key_sha256']):
        raise ValueError('Selection key differs from frozen commitment')
    if protocol['version'] not in ('0.1.0', '0.2.0') or protocol['strata'] != list(STRATA):
        raise ValueError('Unsupported protocol version or strata')
    return protocol, freeze


def priority(key, domain, identity):
    return hmac.new(key, json.dumps([domain, identity], separators=(',', ':')).encode(),
                    hashlib.sha256).hexdigest()


def choose(key, domain, identities, count):
    return sorted(identities, key=lambda x: (priority(key, domain, x), x))[:count]


def metadata(archive, names):
    """One read-only pass; duplicate or missing tables are fatal."""
    found = set()
    with tarfile.open(archive, mode='r|gz') as tar:
        for member in tar:
            name = member.name.rsplit('/', 1)[-1]
            if name not in names or not member.isfile():
                continue
            if name in found:
                raise ValueError('Duplicate metadata table: ' + name)
            found.add(name)
            for row in stream_array(tar.extractfile(member)):
                yield name, row
    if found != set(names):
        raise ValueError('Missing metadata tables: ' + str(set(names) - found))


def finite_vector(value, length):
    out = np.asarray(value, dtype=float)
    if out.shape != (length,) or not np.isfinite(out).all():
        raise ValueError('Invalid finite vector')
    return out


def distances(points, reference):
    if not reference:
        raise ValueError('Reference missing; cannot infer absence')
    if not points:
        return np.array([])
    a = np.asarray([finite_vector(p, 2) for p in points])
    b = np.asarray([finite_vector(p, 2) for p in reference])
    return cKDTree(b).query(a)[0]


def strata_for(camera_xy, lidar_xy, cache_xy, full_xy, radius):
    dc = distances(camera_xy, cache_xy)
    df = distances(camera_xy, full_xy)
    dl = distances(lidar_xy, full_xy)
    unmatched_lidar = [p for p, d in zip(lidar_xy, dl) if d > radius]
    coincidence = (cKDTree(unmatched_lidar).query(camera_xy)[0] <= radius
                   if unmatched_lidar and camera_xy else np.zeros(len(camera_xy), dtype=bool))
    labels = [STRATA[0] if a <= radius else STRATA[1] if b <= radius
              else STRATA[2] if c else STRATA[3] for a, b, c in zip(dc, df, coincidence)]
    return labels, dc, df


def hash_inputs(root):
    return {name: {'sha256': digest(root / name), 'bytes': (root / name).stat().st_size}
            for name in INPUTS}


def selection(args):
    key = args.key_file.read_bytes()
    protocol, freeze = bound_protocol(args.protocol_dir, key)
    if args.output_dir.exists():
        raise ValueError('Output directory already exists; use a new run identity')
    before = hash_inputs(args.data_root)
    cache = read_json(args.data_root / INPUTS[0])
    cached = collections.defaultdict(list)
    for row in cache:
        cached[row['sample_token']].append(row['xy'])
    samples, annotations = {}, collections.defaultdict(list)
    print('Reading complete annotation table and sample chronology', file=sys.stderr, flush=True)
    for name, row in metadata(args.data_root / 'meta.tgz',
                              {'sample.json', 'sample_annotation.json'}):
        if name == 'sample.json':
            if row['token'] in samples:
                raise ValueError('Duplicate sample token')
            samples[row['token']] = row
        elif row['sample_token'] in cached:
            annotations[row['sample_token']].append(row['translation'][:2])
    if not set(cached) <= set(samples) or set(cached) != set(annotations):
        raise ValueError('Reference sample coverage mismatch')
    scenes = sorted({samples[token]['scene_token'] for token in cached})
    revised = protocol['version'] == '0.2.0'
    m = len(scenes) if revised else protocol['scenes_to_sample']
    if not 1 <= m <= len(scenes):
        raise ValueError('Invalid scene sampling budget')
    picked_scenes = choose(key, 'scene-selection', scenes, m)
    predictions = []
    for filename in INPUTS[2:]:
        data = read_json(args.data_root / filename)['results']
        if not set(cached) <= set(data):
            raise ValueError('Prediction file omits sample keys: ' + filename)
        predictions.append(data)
    cells = {(s, g): [] for s in scenes for g in STRATA}
    qualified = []
    for sample in sorted(cached):
        arrays = []
        for pred in predictions:
            rows = []
            for index, row in enumerate(pred[sample]):
                score = row['detection_score']
                if not isinstance(score, (float, int)) or not 0 <= score <= 1:
                    raise ValueError('Invalid detection score')
                if row['sample_token'] != sample:
                    raise ValueError('Detection sample identity mismatch')
                finite_vector(row['translation'], 3)
                if score >= protocol['score_threshold']:
                    rows.append((index, row))
            arrays.append(rows)
        labels, dc, df = strata_for(
            [r['translation'][:2] for _, r in arrays[0]],
            [r['translation'][:2] for _, r in arrays[1]], cached[sample],
            annotations[sample], protocol['association_radius_m'])
        scene = samples[sample]['scene_token']
        for (index, row), group, a, b in zip(arrays[0], labels, dc, df):
            ident = sample + ':' + str(index)
            cells[(scene, group)].append(ident)
            qualified.append((ident, scene, sample, group, row, float(a), float(b)))
    k = None if revised else protocol['cases_per_scene_stratum']
    selected = set()
    population = []
    group_sizes = {g: sum(len(v) for (s, h), v in cells.items() if h == g) for g in STRATA}
    if revised:
        for group in STRATA:
            identities = [ident for (s, g), rows in cells.items() if g == group for ident in rows]
            selected.update(choose(key, 'within-stratum:' + group, identities,
                                   protocol['cases_per_stratum']))
    for (scene, group), identities in sorted(cells.items()):
        n = (sum(ident in selected for ident in identities) if revised else
             min(k, len(identities)) if scene in picked_scenes else 0)
        if not revised:
            selected.update(choose(key, 'within-cell:' + scene + ':' + group, identities, n))
        population.append({'scene_token': scene, 'stratum': group,
                           'population_n': len(identities), 'sample_n': n,
                           'scene_selected': None if revised else scene in picked_scenes})
    cases = []
    for ident, scene, sample, group, prediction, a, b in qualified:
        if ident not in selected:
            continue
        n = group_sizes[group] if revised else len(cells[scene, group])
        ns = min(protocol['cases_per_stratum'] if revised else k, n)
        cases.append({'case_id': priority(key, 'blind-case-id', ident)[:24],
                      'source_detection_id': ident, 'scene_token': scene,
                      'sample_token': sample, 'stratum': group, 'prediction': prediction,
                      'cache_distance_m': a, 'complete_reference_distance_m': b,
                      'scene_inclusion_probability': None if revised else m / len(scenes),
                      'within_cell_inclusion_probability': None if revised else ns / n,
                      'inclusion_probability': ns / n if revised else m / len(scenes) * ns / n})
    if len({c['case_id'] for c in cases}) != len(cases):
        raise ValueError('Opaque case identifier collision')
    needed_samples = set()
    for case in cases:
        center = samples[case['sample_token']]
        for token in (center['prev'], center['token'], center['next']):
            if token:
                if token not in samples or samples[token]['scene_token'] != center['scene_token']:
                    raise ValueError('Broken scene chronology')
                needed_samples.add(token)
    if before != hash_inputs(args.data_root):
        raise ValueError('Inputs changed during selection')
    result = {'artifact_id': 'reiyah.reference-study.selection.0.1.0', 'version': VERSION,
              'protocol_sha256': freeze['protocol_sha256'],
              'selection_key_sha256': freeze['selection_key_sha256'],
              'inputs': before, 'population_scenes': len(scenes),
              'sampled_scenes': len({c['scene_token'] for c in cases}),
              'sampling_design': 'within_stratum_srs' if revised else 'two_stage_scene_srs',
              'population_cells': population, 'cases': sorted(cases, key=lambda c: c['case_id']),
              'samples': {t: samples[t] for t in sorted(needed_samples)},
              'judgments_collected': 0, 'status': 'selected_awaiting_sensor_evidence'}
    args.output_dir.mkdir(mode=0o700, parents=True)
    write_new(args.output_dir / 'selection.private.json', result)
    write_new(args.output_dir / 'selection-aggregate.json', {
        'artifact_id': 'reiyah.reference-study.selection-aggregate.0.1.0', 'version': VERSION,
        'protocol_sha256': result['protocol_sha256'],
        'selection_sha256': digest(args.output_dir / 'selection.private.json'),
        'selection_key_sha256': result['selection_key_sha256'], 'inputs': before,
        'population_scenes': len(scenes), 'sampled_scenes': result['sampled_scenes'],
        'sampling_design': result['sampling_design'], 'selected_cases': len(cases),
        'groups': {g: {'population_n': sum(len(v) for (s, h), v in cells.items() if h == g),
                       'selected_n': sum(c['stratum'] == g for c in cases),
                       'empty_population_scene_cells': sum(not cells[s, g] for s in scenes),
                       'scenes_represented': len({c['scene_token'] for c in cases if c['stratum'] == g})}
                   for g in STRATA},
        'independent_judgments': 0, 'physical_performance_point_estimate': None})
    print(json.dumps({'selected_cases': len(cases), 'scenes': result['sampled_scenes']}))


def rotation_wxyz(quaternion):
    w, x, y, z = finite_vector(quaternion, 4)
    norm = w*w + x*x + y*y + z*z
    if abs(norm - 1) > 1e-5:
        raise ValueError('Quaternion is not unit length')
    # nuScenes scalar-first convention; no dependency on a library default ordering.
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


def global_to_sensor(point, ego, calibration):
    p = rotation_wxyz(ego['rotation']).T @ (
        finite_vector(point, 3) - finite_vector(ego['translation'], 3))
    return rotation_wxyz(calibration['rotation']).T @ (
        p - finite_vector(calibration['translation'], 3))


def camera_projection(point, intrinsic, width, height):
    p = finite_vector(point, 3)
    matrix = np.asarray(intrinsic, dtype=float)
    if matrix.shape != (3, 3) or not np.isfinite(matrix).all() or width <= 0 or height <= 0:
        raise ValueError('Invalid camera geometry')
    if p[2] <= 0:
        return {'state': 'behind_camera', 'pixel_xy': None, 'depth_m': float(p[2])}
    q = matrix @ p
    if q[2] <= 0:
        raise ValueError('Invalid homogeneous camera projection')
    uv = q[:2] / q[2]
    inside = 0 <= uv[0] < width and 0 <= uv[1] < height
    return {'state': 'inside_image' if inside else 'outside_image',
            'pixel_xy': uv.tolist(), 'depth_m': float(p[2])}


def safe_asset(root, relative):
    p = pathlib.PurePosixPath(relative)
    if p.is_absolute() or '..' in p.parts or not p.parts or p.parts[0] not in ('samples', 'sweeps'):
        raise ValueError('Unsafe dataset asset path')
    path = (root / str(p)).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Dataset asset escapes source root')
    return path


def prepare(args):
    protocol, freeze = bound_protocol(args.protocol_dir)
    chosen = read_json(args.selection)
    if chosen['protocol_sha256'] != freeze['protocol_sha256']:
        raise ValueError('Selection protocol mismatch')
    if args.output_dir.exists():
        raise ValueError('Output directory already exists')
    if digest(args.metadata_archive) != chosen['inputs']['meta.tgz']['sha256']:
        raise ValueError('Metadata differs from selected input')
    sample_set = set(chosen['samples'])
    sd, calibrations, sensors = {}, {}, {}
    print('Binding sensor samples and calibration', file=sys.stderr, flush=True)
    for name, row in metadata(args.metadata_archive,
                              {'sample_data.json', 'calibrated_sensor.json', 'sensor.json'}):
        if name == 'sample_data.json' and row['is_key_frame'] and row['sample_token'] in sample_set:
            if row['token'] in sd:
                raise ValueError('Duplicate sensor sample')
            sd[row['token']] = row
        elif name == 'calibrated_sensor.json':
            calibrations[row['token']] = row
        elif name == 'sensor.json':
            sensors[row['token']] = row
    wanted_pose = {row['ego_pose_token'] for row in sd.values()}
    poses = {}
    print('Binding per-sensor ego poses', file=sys.stderr, flush=True)
    for _, row in metadata(args.metadata_archive, {'ego_pose.json'}):
        if row['token'] in wanted_pose:
            if row['token'] in poses:
                raise ValueError('Duplicate ego pose')
            poses[row['token']] = row
    if set(poses) != wanted_pose:
        raise ValueError('Missing per-sensor ego pose')
    by_frame = collections.defaultdict(dict)
    for row in sd.values():
        channel = sensors[calibrations[row['calibrated_sensor_token']]['sensor_token']]['channel']
        if channel in CHANNELS:
            if channel in by_frame[row['sample_token']]:
                raise ValueError('Duplicate keyframe channel')
            by_frame[row['sample_token']][channel] = row
    retrieval = {}
    packets = []
    for case in chosen['cases']:
        center = chosen['samples'][case['sample_token']]
        evidence = []
        for offset, token in ((-1, center['prev']), (0, center['token']), (1, center['next'])):
            for channel in CHANNELS:
                eid = f'{offset:+d}:{channel}'
                row = by_frame[token].get(channel) if token else None
                if row is None:
                    evidence.append({'evidence_id': eid, 'channel': channel,
                                     'frame_offset': offset, 'state': 'scene_boundary' if not token
                                     else 'metadata_missing', 'asset_sha256': None})
                    continue
                calib = calibrations[row['calibrated_sensor_token']]
                ego = poses[row['ego_pose_token']]
                if ego['timestamp'] != row['timestamp']:
                    raise ValueError('Ego pose does not match sensor timestamp')
                safe_asset(pathlib.Path('/private-dataset-root'), row['filename'])
                retrieval[row['filename']] = {'filename': row['filename'],
                                             'sensor_sample_token': row['token']}
                xyz = global_to_sensor(case['prediction']['translation'], ego, calib)
                dt = (row['timestamp'] - center['timestamp']) / 1e6
                item = {'evidence_id': eid, 'channel': channel, 'frame_offset': offset,
                        'state': 'awaiting_asset', 'asset_sha256': None,
                        'relative_asset_path': row['filename'], 'sensor_timestamp_us': row['timestamp'],
                        'sample_time_offset_s': dt, 'sensor_sample_token': row['token'],
                        'ego_pose': ego, 'calibration': calib,
                        'calibration_accuracy': 'unknown', 'per_point_acquisition_time': 'unavailable',
                        'candidate_sensor_xyz_m': xyz.tolist(),
                        'conditional_motion_displacement_m': [abs(dt) * v for v in
                            protocol['timing_sensitivity_speed_bounds_mps']]}
                if channel.startswith('CAM'):
                    item.update(image_width=row['width'], image_height=row['height'],
                                projection=camera_projection(xyz, calib['camera_intrinsic'],
                                                             row['width'], row['height']))
                evidence.append(item)
        packets.append({'artifact_id': 'reiyah.reference-study.blind-packet.0.1.0',
                        'version': VERSION, 'case_id': case['case_id'],
                        'protocol_sha256': freeze['protocol_sha256'],
                        'candidate_sample_timestamp_us': center['timestamp'],
                        'candidate_global_center_m': case['prediction']['translation'],
                        'candidate_motion': 'unknown', 'reference_annotation_labels': 'withheld',
                        'marker_semantics': 'Fixed world location at candidate sample time; not a trajectory',
                        'evidence': evidence})
    if digest(args.metadata_archive) != chosen['inputs']['meta.tgz']['sha256']:
        raise ValueError('Metadata changed while preparing packets')
    args.output_dir.mkdir(parents=True, mode=0o700)
    write_new(args.output_dir / 'packets.private.json', packets)
    write_new(args.output_dir / 'retrieval.private.json', {
        'artifact_id': 'reiyah.reference-study.retrieval.0.1.0', 'version': VERSION,
        'selection_sha256': digest(args.selection), 'protocol_sha256': freeze['protocol_sha256'],
        'assets': [retrieval[k] for k in sorted(retrieval)]})
    print(json.dumps({'packets': len(packets), 'unique_assets': len(retrieval)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    select = sub.add_parser('select')
    select.add_argument('--data-root', type=pathlib.Path, required=True)
    select.add_argument('--key-file', type=pathlib.Path, required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('--selection', type=pathlib.Path, required=True)
    prep.add_argument('--metadata-archive', type=pathlib.Path, required=True)
    for p in (select, prep):
        p.add_argument('--protocol-dir', type=pathlib.Path, required=True)
        p.add_argument('--output-dir', type=pathlib.Path, required=True)
    args = parser.parse_args()
    if args.command == 'select':
        selection(args)
    else:
        prepare(args)


if __name__ == '__main__':
    main()
