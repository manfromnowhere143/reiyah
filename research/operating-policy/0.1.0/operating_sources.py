"""Qualify retained scores and create exact stricter-output policies."""
from collections import Counter
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'research/public-predictions/0.1.0'))
sys.path.insert(0, str(ROOT/'research/reference-timing/0.1.0'))
from admission import AVAILABLE, admit, digest, number
from compare_math import ROLES, q, validate_image, w
from timing_metadata import file_binding, put, read, require

FLOOR = Fraction(1, 4)
ANCHORS = tuple(map(Fraction, ('1/4', '7/20', '1/2', '13/20', '4/5', '9/10', '19/20', '1')))
MAX_ROLE_CELLS = 1024
MAX_COMMON_CELLS = 2048


def eligible(detection):
    return detection['category_id'] == 2 and number(detection['xyxy'][3])-number(detection['xyxy'][1]) >= 25


def filtered_operand(row, threshold):
    threshold = Fraction(threshold)
    require(FLOOR <= threshold <= 1, 'Threshold outside retained-score domain')
    if row['state'] not in AVAILABLE:
        return {'state': 'unavailable', 'reason': row['state']+': '+row['reason']}, []
    records = []; custody = []; occurrences = Counter()
    for detection in row['detections']:
        score = number(detection['score'])
        require(FLOOR < score <= 1, 'Source score violates retained floor')
        reason = ('category_outside_car' if detection['category_id'] != 2 else
                  'height_below_25' if not eligible(detection) else
                  'score_not_strictly_above_threshold' if score <= threshold else None)
        if reason:
            custody.append({'source_detection_id': detection['id'], 'state': 'excluded', 'reason': reason}); continue
        require(detection['category_name'] == 'car', 'Car mapping differs')
        geometry = [w(number(value)) for value in detection['xyxy']]
        signature = digest({'category': 'car', 'xyxy': geometry})
        occurrence = occurrences[signature]; occurrences[signature] += 1
        identity = 'prediction:'+digest({'signature': signature, 'occurrence': occurrence})
        record = {'id': identity, 'record_sha256': digest({'id': identity, 'xyxy': geometry}), 'xyxy': geometry}
        records.append(record); custody.append({'source_detection_id': detection['id'], 'state': 'eligible', 'record_id': identity})
    return {'state': 'observed', 'value': records}, custody


def filtered_image(original, packets, threshold, policy_sha256):
    image = deepcopy(original); image['policy_sha256'] = policy_sha256; custody = {}
    for role in ROLES:
        operand, rows = filtered_operand(packets[role][original['id']], threshold)
        image[role] = operand; custody[role] = rows
    validate_image(image)
    return image, custody


def cells(scores, limit):
    scores = [Fraction(value) for value in scores]
    require(all(FLOOR < value <= 1 for value in scores), 'Score event outside admitted domain')
    points = sorted({FLOOR, Fraction(1), *scores}); result = []
    for left, right in zip(points, points[1:]):
        result.append({'id': 'cell-'+str(len(result)).zfill(4), 'left': w(left), 'right': w(right),
                       'left_closed': True, 'right_closed': False, 'representative': w(left)})
    result.append({'id': 'cell-'+str(len(result)).zfill(4), 'left': w(1), 'right': w(1),
                   'left_closed': True, 'right_closed': True, 'representative': w(1)})
    require(type(limit) is int and len(result) <= limit, 'Threshold cell limit')
    return result


def source_packets(root, visible):
    root = Path(root).resolve(); retained = read(root/'private/comparison-01/custody/SOURCE_BINDINGS.json')
    prior = {row['path']: row for row in retained}; packets = {}; bindings = []; report = {}
    wanted = {image['id']: image for image in visible['images']}
    require(len(wanted) == len(visible['images']), 'Repeated visible image')
    for role, stage in zip(ROLES, ('export-06-64', 'export-07-64')):
        folder = root/'results'/stage; values = {}
        for name in ('ALLOCATION', 'CONFIGURATION', 'PACKET', 'RESULT'):
            path = folder/(name+'.json'); binding = file_binding(path)
            require(prior.get(str(path)) == binding, 'Original admitted source bytes changed')
            values[name] = read(path); bindings.append(binding)
        configuration = values['CONFIGURATION']; packet = values['PACKET']; post = configuration['postprocessing']
        require(number(post['confidence']) == FLOOR and post['confidence_operator'] == 'gt', 'Retained score floor changed')
        admission = admit(values['ALLOCATION'], configuration, packet)
        require(admission == values['RESULT']['admission'] and admission['complete_usable_export'], 'Incomplete admitted packet')
        rows = {row['id']: row for row in packet['images']}
        require(len(rows) == len(packet['images']) and set(rows) == set(wanted), 'Prediction image membership differs')
        count = 0; scores = []; states = Counter()
        for iid, row in rows.items():
            require(all(row[key] == wanted[iid][key] for key in ('width', 'height', 'image_sha256')), 'Image identity differs')
            require(row['state'] in AVAILABLE, 'Missing input cannot become empty')
            operand, custody = filtered_operand(row, FLOOR)
            require(operand == wanted[iid][role], 'Floor eligible operands differ from preceding comparison')
            require(len(custody) == len(row['detections']), 'Source detection omitted')
            states[row['state']] += 1; count += len(operand['value'])
            scores.extend(number(detection['score']) for detection in row['detections'] if eligible(detection))
        packets[role] = rows
        report[role] = {'stage': stage, 'images': len(rows), 'source_states': dict(states),
                        'all_class_detections': sum(len(row['detections']) for row in rows.values()),
                        'eligible_floor_detections': count, 'distinct_eligible_scores': len(set(scores)),
                        'confidence_floor': w(FLOOR), 'confidence_operator': 'gt', 'postprocessing_method': post['method'],
                        'minimum_eligible_score': w(min(scores)) if scores else None,
                        'maximum_eligible_score': w(max(scores)) if scores else None}
    return packets, bindings, report


def qualify(root, destination):
    root = Path(root).resolve(); visible_path = root/'private/comparison-01/inputs/visible.json'; visible = read(visible_path)
    _, bindings, report = source_packets(root, visible)
    require(len(visible['images']) == 64 and len(visible['cases']) == 73, 'Wrong development allocation')
    result = {'artifact_id': 'reiyah.operating-policy.score-qualification', 'version': '0.1.0',
        'visible_source': file_binding(visible_path), 'source_bindings': bindings, 'roles': report,
        'threshold_dependent_outcomes_computed': False, 'reference_outcomes_read': False,
        'source_images_read': 0, 'new_inference_calls': 0, 'reserved_outcomes_accessed': 0,
        'scope': 'Complete retained postprocessed packets above strict score floor only; scores are not assumed calibrated.'}
    put(destination, result); print(__import__('json').dumps(result), flush=True)


if __name__ == '__main__':
    qualify(*sys.argv[1:])
