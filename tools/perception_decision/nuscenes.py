"""Exact, per-frame normalization for the declared nested nuScenes comparison.

This module accepts already source-verified frame rows. It does not select a cohort,
establish physical reference truth, or verify caller-supplied upstream source hashes.
"""
from decimal import Decimal
from fractions import Fraction
import hashlib
import re

from .contract import Invalid, encoded, wire

CLASSES = frozenset(('car', 'truck', 'bus', 'trailer', 'construction_vehicle',
                     'pedestrian', 'motorcycle', 'bicycle', 'traffic_cone', 'barrier'))
UNAVAILABLE = frozenset(('missing', 'unmeasured', 'sensor_invalid', 'abstained', 'outside_support', 'unknown'))
POLICY = 'reiyah.nuscenes-nested-comparison.0.1.0'
MAX_FRAME_PREDICTIONS = 512


def _number(value):
    # Callers should use json.loads(..., parse_float=Decimal) on verified source bytes.
    if type(value) is int and abs(value) <= 10**12:
        return Fraction(value)
    if type(value) is Decimal and value.is_finite():
        _, digits, exponent = value.as_tuple()
        if len(digits) <= 32 and -32 <= exponent <= 12 and value.copy_abs() <= 10**12:
            return Fraction(value)
    raise Invalid('ADAPTER_NUMBER', 'Use bounded finite source Decimal or integer values; binary floats are not accepted')


def _availability(output):
    if type(output) is not dict or type(output.get('state')) is not str:
        raise Invalid('ADAPTER_AVAILABILITY', 'An explicit availability record is required')
    if output.get('state') == 'observed':
        if (set(output) != {'state', 'value'} or type(output['value']) is not list
                or len(output['value']) > MAX_FRAME_PREDICTIONS):
            raise Invalid('ADAPTER_AVAILABILITY', 'Malformed or oversized observed frame output')
    elif (output.get('state') not in UNAVAILABLE or set(output) != {'state', 'reason'}
          or type(output['reason']) is not str or not 0 < len(output['reason']) <= 1024):
        raise Invalid('ADAPTER_AVAILABILITY', 'An unavailable output requires its state and reason, without a value')


def normalize_frame(*, sample_token, anchor_id, ego_xy, weight, base, camera, source_sha256):
    """Return a normalized core anchor plus a complete selection/suppression receipt.

    source_sha256 names base, camera and clock source observations. An unavailable
    frame may retain a known parent-source digest; None means that source identity
    is unavailable. Full-source checking is upstream.
    """
    if type(sample_token) is not str or not 0 < len(sample_token) <= 96:
        raise Invalid('ADAPTER_SAMPLE', 'A bounded sample identity is required')
    if type(anchor_id) is not str or re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}', anchor_id) is None:
        raise Invalid('ADAPTER_SAMPLE', 'A bounded anchor identity is required')
    if (type(weight) is not Fraction or not 0 <= weight <= 1
            or len(str(weight.numerator)) > 18 or len(str(weight.denominator)) > 18):
        raise Invalid('ADAPTER_WEIGHT', 'Supply a nonnegative Fraction within the core rational limits')
    if type(ego_xy) not in (list, tuple) or len(ego_xy) != 2:
        raise Invalid('ADAPTER_COORDINATES', 'The clock-bound global ego XY is required')
    ego = tuple(map(_number, ego_xy))
    _availability(base)
    _availability(camera)
    if type(source_sha256) is not dict or set(source_sha256) != {'base', 'camera', 'clock'}:
        raise Invalid('ADAPTER_SOURCE', 'Name the base, camera and clock source identities')
    for role, observed in [('clock', True), ('base', base['state'] == 'observed'), ('camera', camera['state'] == 'observed')]:
        digest = source_sha256[role]
        if observed or digest is not None:
            if type(digest) is not str or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
                raise Invalid('ADAPTER_SOURCE', 'Observed source requires a SHA-256 identity')
    trace = []

    def qualify(output, role):
        selected = []
        if output['state'] != 'observed':
            return selected
        for index, row in enumerate(output['value']):
            if type(row) is not dict or row.get('sample_token') != sample_token:
                raise Invalid('ADAPTER_SAMPLE', 'A prediction belongs to another sample or has no sample identity')
            label = row.get('detection_name')
            if type(label) is not str or label not in CLASSES:
                raise Invalid('ADAPTER_CLASS', 'Unknown detector class; no class is silently mapped or dropped')
            center = row.get('translation')
            if type(center) not in (list, tuple) or len(center) != 3:
                raise Invalid('ADAPTER_COORDINATES', 'Prediction translation must name its three source components')
            x, y = map(_number, center[:2])
            score = _number(row.get('detection_score'))
            if not 0 <= score <= 1:
                raise Invalid('ADAPTER_SCORE', 'Detection score is outside [0,1]')
            score_ok = score >= Fraction(3, 10)
            range_ok = (x - ego[0]) ** 2 + (y - ego[1]) ** 2 <= 2500
            entry = {'source': role, 'source_index': index, 'score_eligible': score_ok,
                     'range_eligible': range_ok, 'retention': 'ineligible', 'blocked_by': None}
            trace.append(entry)
            if not (score_ok and range_ok):
                continue
            record = {'policy': POLICY, 'sample_token': sample_token, 'source': role,
                      'source_sha256': source_sha256[role], 'source_index': index,
                      'class': label, 'xy': [wire(x), wire(y)], 'score': wire(score)}
            node = {'id': role + ':' + str(index), 'record_sha256': hashlib.sha256(encoded(record)).hexdigest()}
            selected.append({'node': node, 'record': record, 'label': label, 'xy': (x, y), 'score': score,
                             'index': index, 'trace': entry})
        return selected

    base_rows = qualify(base, 'base')
    camera_rows = qualify(camera, 'camera')
    normalized_base = ({'state': 'observed', 'value': [r['node'] for r in base_rows]}
                       if base['state'] == 'observed' else dict(base))
    for row in base_rows:
        row['trace']['retention'] = 'base_retained'
    if camera['state'] != 'observed':
        additions = dict(camera)
    elif base['state'] != 'observed':
        additions = {'state': 'unknown', 'reason': 'Camera retention cannot be determined without the base output'}
        for row in camera_rows:
            row['trace']['retention'] = 'unknown_base_unavailable'
    else:
        retained = list(base_rows)
        added = []
        for row in sorted(camera_rows, key=lambda r: (-r['score'], r['index'])):
            x, y = row['xy']
            blocker = next((other for other in retained if other['label'] == row['label'] and
                            (x-other['xy'][0])**2 + (y-other['xy'][1])**2 < 4), None)
            if blocker is None:
                retained.append(row)
                added.append(row['node'])
                row['trace']['retention'] = 'addition_retained'
            else:
                row['trace']['retention'] = 'suppressed'
                row['trace']['blocked_by'] = blocker['node']['id']
        additions = {'state': 'observed', 'value': added}
    anchor = {'id': anchor_id, 'weight': wire(weight), 'base': normalized_base, 'additions': additions,
              'reference': {'state': 'open', 'reason': 'No reviewed physical-reference constraints supplied'}}
    receipt = {'artifact_id': 'reiyah.perception-decision.normalization', 'version': '0.1.0',
               'policy': POLICY, 'sample_token': sample_token, 'anchor_id': anchor_id,
               'ego_xy': [wire(q) for q in ego], 'source_sha256': dict(source_sha256),
               'source_availability': {'base': base['state'], 'camera': camera['state']},
               'normalized_anchor_sha256': hashlib.sha256(encoded(anchor)).hexdigest(),
               'qualified_records': [{'detection': row['node'], 'record': row['record']}
                                     for row in base_rows + camera_rows],
               'trace': trace, 'input_counts': {'base': len(base['value']) if base['state'] == 'observed' else None,
                                                'camera': len(camera['value']) if camera['state'] == 'observed' else None},
               'reference_scope': 'open_unreviewed', 'upstream_source_verification': 'caller_obligation',
               'unused_prediction_fields': ['translation_z', 'size', 'rotation', 'velocity', 'attribute_name']}
    return anchor, receipt
