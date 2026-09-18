"""Check temporal source membership and scalar geometry without SDK imports."""
from collections import Counter
from fractions import Fraction
import math

from timing_geometry import alternate_motion, close_coordinates, close_motion, eligible, project
from timing_metadata import require


def expected_context(annotation, previous, sample, previous_sample, timestamp):
    require(type(timestamp) is int and type(sample['timestamp']) is int, 'Invalid camera/sample time')
    if timestamp == sample['timestamp']:
        return {'state': 'available', 'kind': 'current_time', 'amount': '1', 'span_us': None}
    if previous_sample is None:
        return {'state': 'unavailable', 'reason': 'missing_preceding_sample'}
    if previous is None:
        return {'state': 'unavailable', 'reason': 'instance_absent_from_preceding_sample'}
    span = sample['timestamp'] - previous_sample['timestamp']
    if not 1 <= span <= 1_500_000:
        return {'state': 'unavailable', 'reason': 'invalid_or_excessive_sample_span'}
    if timestamp < previous_sample['timestamp'] or timestamp > sample['timestamp']:
        return {'state': 'unavailable', 'reason': 'camera_timestamp_outside_bracket'}
    links = [annotation['instance_token'] == previous['instance_token'], annotation['prev'] == previous['token'],
             previous['next'] == annotation['token'], annotation['sample_token'] == sample['token'],
             previous['sample_token'] == previous_sample['token'], sample['prev'] == previous_sample['token'],
             previous_sample['next'] == sample['token'], sample['scene_token'] == previous_sample['scene_token']]
    if not all(links):
        return {'state': 'unavailable', 'reason': 'inconsistent_instance_or_sample_links'}
    fraction = Fraction(timestamp-previous_sample['timestamp'], span)
    return {'state': 'available', 'kind': 'interpolated', 'amount': str(fraction), 'span_us': span}


def finite_source(annotation):
    require(annotation['visibility_token'] in ('', '1', '2', '3', '4'), 'Unknown visibility input')
    for name, size in [('translation', 3), ('size', 3), ('rotation', 4)]:
        values = annotation[name]
        require(type(values) is list and len(values) == size and all(type(x) in (int, float) and math.isfinite(x) for x in values),
                'Nonfinite or malformed source geometry')
    require(all(value > 0 for value in annotation['size']) and math.hypot(*annotation['rotation']) > 0,
            'Degenerate source geometry')


def check_source_image(record, applicability, selected, preceding):
    sd = selected['sample_data'][applicability['sample_data_token']]; sample = selected['sample'][sd['sample_token']]
    require(record['image_id'] == applicability['image_id'] and record['sample_data_token'] == sd['token']
            and record['sample_token'] == sample['token'] and record['scene_token'] == sample['scene_token']
            and record['camera_minus_sample_us'] == sd['timestamp']-sample['timestamp'], 'Projection source identity differs')
    current = {}
    for annotation in selected['sample_annotation'].values():
        if annotation['sample_token'] == sample['token']:
            instance = selected['instance'][annotation['instance_token']]
            if selected['category'][instance['category_token']]['name'] == 'vehicle.car':
                require(annotation['instance_token'] not in current, 'Duplicate current census instance')
                current[annotation['instance_token']] = annotation
    previous = {}; previous_sample = preceding['sample'][sample['prev']] if sample['prev'] else None
    if previous_sample is not None:
        require(previous_sample['next'] == sample['token'] and previous_sample['scene_token'] == sample['scene_token'],
                'Invalid prior scene/sample link')
        for annotation in preceding['sample_annotation'].values():
            if annotation['sample_token'] == previous_sample['token']:
                instance = preceding['instance'][annotation['instance_token']]
                require(selected['category'][instance['category_token']]['name'] == 'vehicle.car', 'Noncar predecessor')
                require(annotation['instance_token'] not in previous, 'Duplicate preceding census instance')
                previous[annotation['instance_token']] = annotation
    previous_keys = sorted(previous) if previous_sample is not None else None
    missing_previous = sorted(set(previous)-set(current)) if previous_sample is not None else None
    require(record['current_census'] == sorted(current) and record['preceding_census'] == previous_keys
            and record['preceding_only_instances'] == missing_previous
            and record['preceding_census_state'] == ('available' if previous_sample is not None else 'unavailable'),
            'Current or preceding census changed; absent cannot become empty')
    require(len(record['objects']) == len(current) and [row['instance_token'] for row in record['objects']] == sorted(current),
            'Car object membership omitted, duplicated or reordered')
    pose = selected['ego_pose'][sd['ego_pose_token']]; calibration = selected['calibrated_sensor'][sd['calibrated_sensor_token']]
    numerical = Counter(); counts = Counter(); unknown = []; references = []; alternatives = []
    for row in record['objects']:
        key = row['instance_token']; annotation = current[key]; before = previous.get(key)
        require(row['annotation_token'] == annotation['token'], 'Annotation identity differs')
        expected = expected_context(annotation, before, sample, previous_sample, sd['timestamp'])
        if expected['state'] == 'unavailable':
            require(row['state'] == 'unavailable' and row['reason'] == expected['reason'] and row['context'] == expected
                    and row['modeled'] is None and row['projection'] is None, 'Missing motion became a modeled observation')
            unknown.append(key); counts[row['reason']] += 1
            continue
        failure = None; alternate = coordinates = None
        try:
            finite_source(annotation)
            if before is not None and expected['kind'] == 'interpolated':
                # The previous dimensions are deliberately not interpolated;
                # only its center and rotation participate in this model.
                for name, length in [('translation', 3), ('rotation', 4)]:
                    values = before[name]
                    require(len(values) == length and all(type(x) in (int, float) and math.isfinite(x) for x in values),
                            'Invalid previous interpolation operand')
                require(math.hypot(*before['rotation']) > 0, 'Zero preceding quaternion')
            alternate = alternate_motion(annotation, before, expected['amount'], expected['kind'])
            coordinates = project(alternate, pose, calibration, sd['width'], sd['height'])
        except Exception as exc:
            failure = type(exc).__name__ + ': ' + str(exc)
        if failure is not None:
            require(row['state'] == 'unavailable' and row['reason'] == 'invalid_motion_or_projection'
                    and row['modeled'] is None and row['projection'] is None, 'Invalid geometry became usable')
            unknown.append(key); counts[row['reason']] += 1
            continue
        require(row['state'] == 'modeled' and row['context'] == expected, 'Usable source has an unexplained projection failure')
        diagnostic = close_motion(row['modeled'], alternate)
        disagreement = close_coordinates(row['projection']['xyxy'], coordinates)
        expected_eligibility = 'outside_canvas' if coordinates is None else 'eligible' if eligible(coordinates) else 'height_below_25'
        require(row['projection']['state'] == 'modeled' and row['projection']['eligibility'] == expected_eligibility,
                'Modeled reference eligibility differs')
        require(row['numerical_check'] == {'state': 'passed', 'alternative_projection': coordinates,
                'coordinate_absolute_error': disagreement, **diagnostic}, 'Numerical diagnostic differs')
        if coordinates is None:
            require(row['projection']['record'] is None, 'Absent projection retains a box record')
        else:
            raw = row['projection']['record']
            expected_raw = {name: annotation[name] for name in ('attribute_tokens', 'instance_token', 'next', 'num_lidar_pts',
                                                              'num_radar_pts', 'prev', 'visibility_token')}
            expected_raw.update(sample_annotation_token=annotation['token'], sample_data_token=sd['token'],
                                category_name='vehicle.car', bbox_corners=row['projection']['xyxy'], filename=sd['filename'])
            require(raw == expected_raw, 'SDK projection source record differs')
        if expected_eligibility == 'eligible':
            references.append(row); alternatives.append(coordinates)
        counts[expected_eligibility] += 1
        numerical['modeled_objects_checked'] += 1
        for name, value in [('maximum_coordinate_error', disagreement), ('maximum_center_error', diagnostic['center_absolute_error']),
                            ('maximum_rotation_matrix_error', diagnostic['rotation_matrix_absolute_error'])]:
            numerical[name] = max(numerical[name], value)
    require(record['state'] == 'complete' and record['numerical_failures'] == [] and record['counts'] == dict(counts),
            'Projection state or object accounting differs')
    return {'current_unknown': sorted(unknown), 'union_unknown': sorted(set(unknown) | set(missing_previous))
            if previous_sample is not None else None, 'known_objects': references,
            'alternative_coordinates': alternatives, 'numerical': dict(numerical), 'counts': dict(counts)}
