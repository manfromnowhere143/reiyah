"""Declared motion-model projection through the retained official SDK.

Every car is joined before visibility or score inspection. Missing motion is
an explicit unavailable object, never a stationary or empty reference.
"""
from copy import deepcopy
from fractions import Fraction
import math

from timing_metadata import require

MAX_BRACKET_US = 1_500_000


def vector(value, size, positive=False):
    require(type(value) is list and len(value) == size
            and all(type(x) in (int, float) and math.isfinite(x) for x in value), 'Invalid finite vector')
    require(not positive or all(x > 0 for x in value), 'Nonpositive box dimensions')
    return [float(x) for x in value]


def quaternion(value):
    values = vector(value, 4)
    require(math.hypot(*values) > 0, 'Zero quaternion')
    return values


def car_census(selected, preceding, sample_token):
    sample = selected['sample'][sample_token]
    current = {}
    for annotation in selected['sample_annotation'].values():
        if annotation['sample_token'] != sample_token:
            continue
        instance = selected['instance'][annotation['instance_token']]
        if selected['category'][instance['category_token']]['name'] != 'vehicle.car':
            continue
        key = annotation['instance_token']
        require(key not in current, 'Duplicate current car instance')
        current[key] = annotation
    previous = {}; previous_sample = None
    if sample['prev']:
        previous_sample = preceding['sample'][sample['prev']]
        require(previous_sample['scene_token'] == sample['scene_token']
                and previous_sample['next'] == sample_token, 'Broken preceding sample link')
        for annotation in preceding['sample_annotation'].values():
            if annotation['sample_token'] != sample['prev']:
                continue
            key = annotation['instance_token']
            require(key not in previous, 'Duplicate previous car instance')
            instance = preceding['instance'][key]
            require(selected['category'][instance['category_token']]['name'] == 'vehicle.car', 'Noncar in preceding census')
            previous[key] = annotation
    return current, previous, previous_sample


def bracket(current, previous, sample, previous_sample, camera_timestamp):
    require(type(camera_timestamp) is int and type(sample['timestamp']) is int, 'Noninteger timestamp')
    current_time = sample['timestamp']
    if camera_timestamp == current_time:
        return {'state': 'available', 'kind': 'current_time', 'amount': '1', 'span_us': None}
    if previous_sample is None:
        return {'state': 'unavailable', 'reason': 'missing_preceding_sample'}
    if previous is None:
        return {'state': 'unavailable', 'reason': 'instance_absent_from_preceding_sample'}
    require(type(previous_sample['timestamp']) is int, 'Noninteger preceding timestamp')
    previous_time = previous_sample['timestamp']; span = current_time - previous_time
    if not 0 < span <= MAX_BRACKET_US:
        return {'state': 'unavailable', 'reason': 'invalid_or_excessive_sample_span'}
    if not previous_time <= camera_timestamp <= current_time:
        return {'state': 'unavailable', 'reason': 'camera_timestamp_outside_bracket'}
    if (current['instance_token'] != previous['instance_token']
            or current['prev'] != previous['token'] or previous['next'] != current['token']
            or current['sample_token'] != sample['token'] or previous['sample_token'] != previous_sample['token']
            or sample['prev'] != previous_sample['token'] or previous_sample['next'] != sample['token']
            or sample['scene_token'] != previous_sample['scene_token']):
        return {'state': 'unavailable', 'reason': 'inconsistent_instance_or_sample_links'}
    return {'state': 'available', 'kind': 'interpolated',
            'amount': str(Fraction(camera_timestamp - previous_time, span)), 'span_us': span}


def sdk_motion(current, previous, context):
    require(context['state'] == 'available', 'Unavailable motion cannot be interpolated')
    import numpy as np
    from pyquaternion import Quaternion
    center = vector(current['translation'], 3); dimensions = vector(current['size'], 3, True)
    rotation = Quaternion(quaternion(current['rotation']))
    if context['kind'] == 'interpolated':
        start = vector(previous['translation'], 3); q0 = Quaternion(quaternion(previous['rotation']))
        amount = float(Fraction(context['amount']))
        center = [float(np.interp(amount, [0.0, 1.0], [a, b])) for a, b in zip(start, center)]
        rotation = Quaternion.slerp(q0=q0, q1=rotation, amount=amount)
    rotation = rotation.normalised
    return {'translation': center, 'rotation': [float(x) for x in rotation.elements], 'size': dimensions}


class SingleAnnotationSource:
    def __init__(self, selected, sample_data, annotation, modeled):
        self.selected = selected; self.sample_data = sample_data
        self.annotation = annotation; self.modeled = modeled

    def get(self, name, token):
        if name == 'sample_annotation':
            require(token == self.annotation['token'], 'Wrong annotation requested')
            return {**deepcopy(self.annotation), 'category_name': 'vehicle.car'}
        if name == 'sample_data':
            require(token == self.sample_data['token'], 'Wrong camera record requested')
            return {**deepcopy(self.sample_data), 'sensor_modality': 'camera'}
        result = deepcopy(self.selected[name][token])
        if name == 'sample':
            result['anns'] = [self.annotation['token']]
        return result

    def get_box(self, token):
        from nuscenes.utils.data_classes import Box
        from pyquaternion import Quaternion
        require(token == self.annotation['token'], 'Wrong modeled annotation requested')
        return Box(self.modeled['translation'], self.modeled['size'], Quaternion(self.modeled['rotation']),
                   name='vehicle.car', token=token)


def sdk_project(selected, sample_data, annotation, modeled):
    from nuscenes.scripts import export_2d_annotations_as_json as publisher
    require(annotation['visibility_token'] in ('', '1', '2', '3', '4'), 'Unknown visibility cannot become an empty projection')
    source = SingleAnnotationSource(selected, sample_data, annotation, modeled)
    # The pinned script exposes its source through a module global. This
    # single-threaded adapter restores that global after each isolated call.
    absent = object(); inherited = getattr(publisher, 'nusc', absent)
    publisher.nusc = source
    try:
        rows = publisher.get_2d_boxes(sample_data['token'], ['', '1', '2', '3', '4'])
    finally:
        if inherited is absent:
            del publisher.nusc
        else:
            publisher.nusc = inherited
    require(len(rows) <= 1, 'One annotation produced multiple projections')
    if not rows:
        return {'state': 'modeled', 'eligibility': 'outside_canvas', 'xyxy': None, 'record': None}
    row = rows[0]
    # Convert the SDK's numpy scalar outputs to the same JSON float boundary
    # used by the inherited projection adapter, then validate their values.
    coordinates = vector([float(value) for value in row['bbox_corners']], 4)
    row['bbox_corners'] = coordinates
    x1, y1, x2, y2 = coordinates
    require(0 <= x1 < x2 <= sample_data['width'] and 0 <= y1 < y2 <= sample_data['height'],
            'Invalid positive-area projected rectangle')
    height = Fraction(str(y2)) - Fraction(str(y1))
    return {'state': 'modeled', 'eligibility': 'eligible' if height >= 25 else 'height_below_25',
            'xyxy': coordinates, 'record': row}


def project_current(selected, sample_data, annotation, previous, previous_sample):
    sample = selected['sample'][sample_data['sample_token']]
    try:
        context = bracket(annotation, previous, sample, previous_sample, sample_data['timestamp'])
        if context['state'] != 'available':
            return {'instance_token': annotation['instance_token'], 'annotation_token': annotation['token'],
                    'state': 'unavailable', 'reason': context['reason'], 'context': context,
                    'modeled': None, 'projection': None}
        modeled = sdk_motion(annotation, previous, context)
        projection = sdk_project(selected, sample_data, annotation, modeled)
        return {'instance_token': annotation['instance_token'], 'annotation_token': annotation['token'],
                'state': 'modeled', 'context': context, 'modeled': modeled, 'projection': projection}
    except (ValueError, KeyError, TypeError, ArithmeticError, AttributeError, AssertionError) as exc:
        return {'instance_token': annotation['instance_token'], 'annotation_token': annotation['token'],
                'state': 'unavailable', 'reason': 'invalid_motion_or_projection',
                'error': type(exc).__name__ + ': ' + str(exc), 'context': None, 'modeled': None, 'projection': None}
