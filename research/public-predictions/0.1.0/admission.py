"""Bound a complete 2D development export to its allocation and frozen settings.

This checks supplied packet semantics. It does not establish model provenance,
permission, image correspondence, physical truth, or independent reproduction.
Source qualification and source-byte verification are separate obligations.
"""
from collections import Counter
from fractions import Fraction
import hashlib
import json
import math
import re

VERSION = '0.1.0'
MAX_IMAGES = 5000
MAX_DETECTIONS = 1000
MAX_DIMENSION = 32768
AVAILABLE = frozenset(('processed', 'empty'))


class Rejected(ValueError):
    def __init__(self, code, detail):
        super().__init__(code + ': ' + detail)
        self.code = code


def require(condition, code, detail):
    if not condition:
        raise Rejected(code, detail)


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def closed(value, fields, context):
    require(type(value) is dict and set(value) == set(fields), 'FIELDS', context)


def identifier(value):
    require(type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}', value),
            'IDENTITY', 'A bounded simple identifier is required')


def sha(value):
    require(type(value) is str and re.fullmatch('[0-9a-f]{64}', value),
            'DIGEST', 'A lowercase SHA-256 is required')


def integer(value, low, high, code):
    require(type(value) is int and low <= value <= high, code, 'Integer outside declared range')


def number(value):
    require(type(value) in (int, float) and math.isfinite(value), 'NUMBER', 'Finite numeric value required')
    # JSON's shortest decimal spelling is the declared numeric interpretation.
    # Exporters retain the untouched source bytes separately.
    return Fraction(str(value))


def title(value, expected):
    require(value.get('artifact_id') == expected and value.get('version') == VERSION,
            'VERSION', 'Unsupported artifact identity or version')


def validate_allocation(allocation):
    closed(allocation, ('artifact_id', 'version', 'exposure', 'population_id',
                        'membership_basis', 'source_binding_sha256', 'images'), 'allocation')
    title(allocation, 'reiyah.public-predictions.allocation')
    require(allocation['exposure'] == 'development', 'EXPOSURE', 'Only exposed development is admitted')
    identifier(allocation['population_id']); sha(allocation['source_binding_sha256'])
    require(allocation['membership_basis'] in ('retained_image_bytes', 'publisher_keys_and_dimensions'),
            'MEMBERSHIP_BASIS', 'Image identity basis must be explicit')
    images = allocation['images']
    require(type(images) is list and 0 < len(images) <= MAX_IMAGES, 'IMAGE_LIMIT', 'Bounded allocation required')
    found = {}
    for image in images:
        closed(image, ('id', 'width', 'height', 'image_sha256'), 'allocated image')
        identifier(image['id'])
        require(image['id'] not in found, 'DUPLICATE_IMAGE', image['id'])
        for key in ('width', 'height'):
            integer(image[key], 1, MAX_DIMENSION, 'DIMENSION')
        if allocation['membership_basis'] == 'retained_image_bytes' or image['image_sha256'] is not None:
            sha(image['image_sha256'])
        found[image['id']] = image
    return found


def validate_configuration(configuration):
    closed(configuration, ('artifact_id', 'version', 'checkpoint_sha256', 'runtime', 'preprocessing',
                           'postprocessing', 'categories', 'batch_size', 'coordinate_output',
                           'rounding', 'implementation_sha256'), 'configuration')
    title(configuration, 'reiyah.public-predictions.configuration')
    sha(configuration['checkpoint_sha256']); sha(configuration['implementation_sha256'])
    closed(configuration['runtime'], ('name', 'version', 'device', 'precision', 'binding_sha256'), 'runtime')
    for key in ('name', 'version', 'device', 'precision'):
        require(type(configuration['runtime'][key]) is str and configuration['runtime'][key],
                'SETTING', 'Explicit runtime setting required')
    sha(configuration['runtime']['binding_sha256'])
    closed(configuration['preprocessing'], ('color', 'resize', 'normalization', 'binding_sha256'), 'preprocessing')
    for key in ('color', 'resize', 'normalization'):
        require(type(configuration['preprocessing'][key]) is str and configuration['preprocessing'][key],
                'SETTING', 'Explicit preprocessing setting required')
    sha(configuration['preprocessing']['binding_sha256'])
    post = configuration['postprocessing']
    closed(post, ('method', 'confidence', 'confidence_operator', 'iou_threshold', 'maximum_detections', 'class_agnostic',
                  'multi_label', 'binding_sha256'), 'postprocessing')
    require(post['method'] in ('nms', 'end_to_end'), 'POSTPROCESSING', 'Declared decoding mode required')
    require(0 <= number(post['confidence']) <= 1, 'CONFIDENCE', 'Confidence outside [0,1]')
    require(post['confidence_operator'] == 'gt', 'CONFIDENCE', 'This adapter requires a strict confidence cutoff')
    if post['method'] == 'nms':
        require(0 < number(post['iou_threshold']) <= 1, 'NMS_IOU', 'NMS IoU outside (0,1]')
    else:
        require(post['iou_threshold'] is None, 'POSTPROCESSING', 'End-to-end mode has no external NMS threshold')
    integer(post['maximum_detections'], 1, MAX_DETECTIONS, 'DETECTION_LIMIT')
    require(type(post['class_agnostic']) is bool and type(post['multi_label']) is bool,
            'SETTING', 'Boolean class semantics required')
    sha(post['binding_sha256'])
    integer(configuration['batch_size'], 1, 64, 'BATCH_SIZE')
    require(configuration['coordinate_output'] == 'continuous_pixel_xyxy_clipped',
            'COORDINATE_SYSTEM', 'Only explicitly clipped continuous pixel rectangles are admitted')
    require(configuration['rounding'] in ('none_source_float', 'decimal_6'), 'ROUNDING', 'Unknown rounding policy')
    categories = configuration['categories']
    require(type(categories) is list and 0 < len(categories) <= 1000, 'CATEGORY', 'Explicit category map required')
    found, names = {}, set()
    for category in categories:
        closed(category, ('id', 'name'), 'category')
        integer(category['id'], 0, 1000000, 'CATEGORY')
        require(type(category['name']) is str and 0 < len(category['name']) <= 128,
                'CATEGORY', 'Category name required')
        require(category['id'] not in found and category['name'] not in names, 'CATEGORY', 'Repeated category')
        found[category['id']] = category['name']; names.add(category['name'])
    return found


def admit(allocation, configuration, packet):
    """Reject incomplete coverage; explicit unavailable rows remain in the report."""
    expected = validate_allocation(allocation)
    categories = validate_configuration(configuration)
    closed(packet, ('artifact_id', 'version', 'allocation_sha256', 'configuration_sha256',
                    'checkpoint_sha256', 'source_binding_sha256', 'images'), 'packet')
    title(packet, 'reiyah.public-predictions.packet')
    require(packet['allocation_sha256'] == digest(allocation), 'ALLOCATION_BINDING', 'Allocation changed')
    config_sha = digest(configuration)
    require(packet['configuration_sha256'] == config_sha, 'CONFIGURATION_BINDING', 'Configuration changed')
    require(packet['checkpoint_sha256'] == configuration['checkpoint_sha256'],
            'CHECKPOINT_BINDING', 'Checkpoint changed')
    sha(packet['source_binding_sha256'])
    rows = packet['images']
    require(type(rows) is list and len(rows) == len(expected), 'COVERAGE', 'One explicit row per allocated image required')
    found, states, blocked, detection_count = set(), Counter(), [], 0
    for row in rows:
        require(type(row) is dict, 'FIELDS', 'Image row must be an object')
        state = row.get('state')
        require(state in ('processed', 'empty', 'failed', 'missing'), 'STATE', 'Explicit export state required')
        fields = ('id', 'width', 'height', 'image_sha256', 'configuration_sha256', 'state')
        fields += ('detections', 'source_detection_count', 'empty_basis') if state in AVAILABLE else ('reason',)
        closed(row, fields, 'export image')
        iid = row['id']; identifier(iid)
        require(iid not in found, 'DUPLICATE_IMAGE', iid)
        require(iid in expected, 'COVERAGE', 'Image outside allocation')
        found.add(iid); states[state] += 1
        require(row['configuration_sha256'] == config_sha, 'POSTPROCESSING_CHANGED', iid)
        require((row['width'], row['height']) == (expected[iid]['width'], expected[iid]['height']),
                'DIMENSION_MISMATCH', iid)
        # bool compares equal to int in Python; reject it independently.
        for key in ('width', 'height'):
            integer(row[key], 1, MAX_DIMENSION, 'DIMENSION')
        require(row['image_sha256'] == expected[iid]['image_sha256'], 'IMAGE_BINDING', iid)
        if state not in AVAILABLE:
            require(type(row['reason']) is str and 0 < len(row['reason']) <= 2048,
                    'STATE', 'Unavailable export needs a reason')
            blocked.append(iid)
            continue
        detections = row['detections']
        require(type(detections) is list and len(detections) <= configuration['postprocessing']['maximum_detections'],
                'DETECTION_LIMIT', iid)
        require((state == 'empty') == (len(detections) == 0), 'EMPTY_STATE', 'Processed and empty are distinct')
        integer(row['source_detection_count'], len(detections), MAX_DETECTIONS, 'SOURCE_COUNT')
        require(row['empty_basis'] in ('publisher_explicit_empty', 'frozen_filter') if state == 'empty'
                else row['empty_basis'] is None, 'EMPTY_BASIS', 'Empty output must have a declared basis')
        if row['empty_basis'] == 'publisher_explicit_empty':
            require(row['source_detection_count'] == 0, 'EMPTY_BASIS', 'Source was not empty')
        detection_ids = set()
        for detection in detections:
            closed(detection, ('id', 'category_id', 'category_name', 'score', 'xyxy'), 'detection')
            identifier(detection['id'])
            require(detection['id'] not in detection_ids, 'DUPLICATE_DETECTION', iid)
            detection_ids.add(detection['id'])
            cid = detection['category_id']
            require(type(cid) is int and cid in categories and detection['category_name'] == categories[cid],
                    'CATEGORY_MISMATCH', iid)
            require(number(configuration['postprocessing']['confidence']) < number(detection['score']) <= 1,
                    'SCORE', 'Score violates frozen confidence filter')
            xyxy = detection['xyxy']
            require(type(xyxy) is list and len(xyxy) == 4, 'COORDINATE', 'Four coordinates required')
            x1, y1, x2, y2 = map(number, xyxy)
            require(0 <= x1 < x2 <= row['width'] and 0 <= y1 < y2 <= row['height'],
                    'COORDINATE', 'Rectangle outside declared pixel domain or has no area')
        detection_count += len(detections)
    require(found == set(expected), 'COVERAGE', 'Allocation member missing')
    return {'artifact_id': 'reiyah.public-predictions.admission', 'version': VERSION,
            'packet_sha256': digest(packet), 'allocation_sha256': digest(allocation),
            'configuration_sha256': config_sha, 'allocated_images': len(expected),
            'states': dict(sorted(states.items())), 'blocked_images': blocked,
            'detections': detection_count,
            'complete_usable_export': not blocked,
            'source_qualification': 'separate_required_obligation',
            'scientific_acceptance': False}
