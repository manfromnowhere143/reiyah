"""Project the frozen temporal model without reading prediction geometry."""
from collections import Counter
from datetime import datetime, timezone
import importlib.metadata
from pathlib import Path
import sys
import time

from timing_geometry import alternate_motion, close_coordinates, close_motion, project
from timing_metadata import file_binding, put, read, require
from timing_model import car_census, project_current


def project_image(image_id, applicability, selected, preceding):
    sd = selected['sample_data'][applicability['sample_data_token']]
    sample = selected['sample'][sd['sample_token']]
    require(sd['sample_token'] == applicability['sample_token'] and sd['timestamp'] == applicability['sensor_timestamp_us']
            and sample['timestamp'] == applicability['annotation_sample_timestamp_us']
            and sd['is_key_frame'] is True and sd['width'] == 1600 and sd['height'] == 900,
            'Inherited image membership or time differs')
    current, previous, previous_sample = car_census(selected, preceding, sample['token'])
    pose = selected['ego_pose'][sd['ego_pose_token']]; calibration = selected['calibrated_sensor'][sd['calibrated_sensor_token']]
    objects = []; failures = []
    for instance, annotation in sorted(current.items()):
        value = project_current(selected, sd, annotation, previous.get(instance), previous_sample)
        if value['state'] == 'modeled':
            try:
                context = value['context']
                alternate = alternate_motion(annotation, previous.get(instance), context['amount'], context['kind'])
                diagnostic = close_motion(value['modeled'], alternate)
                alternative_projection = project(alternate, pose, calibration, sd['width'], sd['height'])
                discrepancy = close_coordinates(value['projection']['xyxy'], alternative_projection)
                value['numerical_check'] = {'state': 'passed', 'alternative_projection': alternative_projection,
                                             'coordinate_absolute_error': discrepancy, **diagnostic}
            except Exception as exc:
                failure = {'instance_token': instance, 'error': type(exc).__name__ + ': ' + str(exc)}
                failures.append(failure); value['numerical_check'] = {'state': 'failed', **failure}
        else:
            value['numerical_check'] = {'state': 'not_applicable_to_unavailable_motion'}
        objects.append(value)
    counts = Counter(value['projection']['eligibility'] if value['state'] == 'modeled' else value['reason'] for value in objects)
    return {'image_id': image_id, 'state': 'complete' if not failures else 'numerical_verification_failed',
            'sample_data_token': sd['token'], 'sample_token': sample['token'], 'scene_token': sample['scene_token'],
            'camera_minus_sample_us': sd['timestamp']-sample['timestamp'],
            'current_census': sorted(current), 'preceding_census_state': 'available' if previous_sample is not None else 'unavailable',
            'preceding_census': sorted(previous) if previous_sample is not None else None,
            'preceding_only_instances': sorted(set(previous)-set(current)) if previous_sample is not None else None,
            'objects': objects, 'counts': dict(counts), 'numerical_failures': failures}


def run(area, run_name='projection-01'):
    area = Path(area).resolve(); started = datetime.now(timezone.utc).isoformat(); tick = time.perf_counter()
    freeze_path = area/'FREEZE.json'; freeze = read(freeze_path)
    require(freeze['actual_temporal_projection_before_freeze'] is False, 'Projection was not frozen before execution')
    for binding in freeze['bindings']:
        require(file_binding(binding['path']) == binding, 'Frozen source or code differs')
    runtime = read(freeze['sdk_runtime'])
    require(sys.version == runtime['python'] and str(Path(sys.executable).resolve()) == runtime['executable'],
            'Projection Python runtime differs')
    require({name: importlib.metadata.version(name) for name in runtime['versions']} == runtime['versions'],
            'Projection numerical dependency versions differ')
    selected = read(freeze['selected_metadata']); preceding = read(freeze['preceding_metadata'])
    applicability = read(freeze['applicability'])
    require(len(applicability) == 64 and len({row['image_id'] for row in applicability}) == 64,
            'Complete frozen allocation required')
    require({row['sample_data_token'] for row in applicability} == set(selected['sample_data']), 'Camera census differs')
    output = area/'runs'/run_name; output.mkdir(parents=True)
    records = []; counts = Counter(); states = Counter(); failures = []
    for row in applicability:
        image_tick = time.perf_counter(); iid = row['image_id']
        try:
            value = project_image(iid, row, selected, preceding)
            counts.update(value['counts'])
        except Exception as exc:
            value = {'image_id': iid, 'state': 'projection_failed', 'error': type(exc).__name__ + ': ' + str(exc)}
        value['seconds'] = time.perf_counter()-image_tick; states[value['state']] += 1
        if value['state'] != 'complete':
            failures.append({'image_id': iid, 'state': value['state']})
        path = output/(iid+'.json'); put(path, value)
        records.append({'image_id': iid, **file_binding(path)})
    result = {'artifact_id': 'reiyah.reference-timing.projection', 'version': '0.1.0',
              'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(), 'seconds': time.perf_counter()-tick,
              'freeze_sha256': file_binding(freeze_path)['sha256'], 'allocated_images': 64, 'image_records': records,
              'states': dict(states), 'object_counts': dict(counts), 'failures': failures,
              'new_image_reads': 0, 'model_calls': 0, 'scored_comparisons': 0, 'reserved_outcomes_accessed': 0,
              'human_seconds': None, 'economic_cost': None}
    put(output/'RESULTS.json', result)
    print(__import__('json').dumps({key: result[key] for key in ('states', 'object_counts', 'failures', 'seconds')}), flush=True)


if __name__ == '__main__':
    run(*sys.argv[1:])
