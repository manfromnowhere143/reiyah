"""Exact 2D rectangle compilation into the existing conditional graph contract.

Inputs are qualified operands, not raw model predictions or physical truth.
One Boolean chooses the entire before/after reference set at each anchor.
"""
import copy
from fractions import Fraction
import hashlib

from .contract import (DIRECTORY, MAX_INPUT_BYTES, MAX_WORK, ROLES, encoded, rational,
                       require, schema_check, unique, validate)

BOX_SCHEMA = DIRECTORY / 'box-alternatives.schema.json'
MAX_COORDINATE = 10_000_000


def rectangle(row):
    values = tuple(rational(v) for v in row['xyxy'])
    require(all(abs(v) <= MAX_COORDINATE for v in values),
            'BOX_COORDINATE', 'Pixel coordinate exceeds the declared magnitude limit')
    require(values[0] < values[2] and values[1] < values[3],
            'BOX_AREA', 'Continuous rectangles require strictly positive width and height')
    return values


def overlap(a, b, threshold):
    intersection = max(Fraction(0), min(a[2], b[2]) - max(a[0], b[0])) * max(
        Fraction(0), min(a[3], b[3]) - max(a[1], b[1]))
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - intersection
    return intersection >= threshold * union


def compile_alternatives(source):
    require(len(encoded(source)) <= MAX_INPUT_BYTES, 'INPUT_SIZE', 'Rectangle input exceeds byte limit')
    schema_check(source, BOX_SCHEMA)
    threshold = rational(source['iou_threshold'])
    require(0 < threshold <= 1, 'BOX_IOU', 'IoU threshold must be in (0,1]')
    unique([a['id'] for a in source['anchors']], 'rectangle anchors')
    variables = set(source['model']['variables'])
    prepared, pairs = [], 0
    # Validate every record and reserve all pair comparisons before constructing edges.
    for anchor in source['anchors']:
        detections = {}
        for role in ROLES:
            rows = anchor[role].get('value', [])
            unique([row['id'] for row in rows], anchor['id'] + ':' + role)
            for row in rows:
                geometry = rectangle(row)
                item = (row['record_sha256'], geometry)
                require(row['id'] not in detections or detections[row['id']] == item,
                        'BOX_COMMON_OUTPUT', 'Shared detection has inconsistent digest or geometry')
                detections[row['id']] = item
        ref = anchor['reference']
        references = []
        if ref['state'] == 'alternatives':
            require(ref['variable'] in variables, 'UNKNOWN_VARIABLE', 'Undeclared rectangle reference choice')
            for choice, state in ((False, 'before'), (True, 'after')):
                unique([row['id'] for row in ref[state]], anchor['id'] + ':' + state)
                for row in ref[state]:
                    references.append((state + ':' + row['id'], rectangle(row),
                                       [{'variable': ref['variable'], 'value': choice}]))
            pairs += len(detections) * len(references)
        prepared.append((anchor, detections, references))
    require(pairs <= MAX_WORK, 'BOX_WORK_LIMIT', 'Rectangle pair-comparison limit exceeded')
    context = {'version': '0.1.0', 'coordinate_system': source['coordinate_system'],
               'iou_threshold': source['iou_threshold'], 'cohort_id': source['cohort_id'],
               'model': source['model'], 'assumptions': source['assumptions'],
               'references': [(a['id'], a['reference']) for a in source['anchors']]}
    result = {key: copy.deepcopy(source[key]) for key in
              ('version', 'comparison_id', 'cohort_id', 'evidence_kind', 'loss', 'model')}
    result.update(artifact_id='reiyah.perception-revision.input', input_scope='normalized_research_graphs',
                  reference_context_sha256=hashlib.sha256(encoded(context)).hexdigest(),
                  assumptions=list(source['assumptions']) + [
                      'Rectangle source SHA256: ' + hashlib.sha256(encoded(source)).hexdigest(),
                      'Whole-image alternatives only; arbitrary corrections and physical completeness are not established.'],
                  anchors=[])
    for anchor, detections, references in prepared:
        row = {'id': anchor['id'], 'weight': copy.deepcopy(anchor['weight'])}
        for role in ROLES:
            row[role] = copy.deepcopy(anchor[role])
            if row[role]['state'] == 'observed':
                row[role]['value'] = [{'id': r['id'], 'record_sha256': r['record_sha256']}
                                      for r in anchor[role]['value']]
        if anchor['reference']['state'] == 'open':
            row['reference'] = copy.deepcopy(anchor['reference'])
        else:
            row['reference'] = {
                'state': 'finite',
                'objects': [{'id': oid, 'when': when} for oid, _, when in references],
                'edges': [{'detection': did, 'object': oid, 'when': when}
                          for oid, geometry, when in references
                          for did, (_, box) in sorted(detections.items())
                          if overlap(box, geometry, threshold)]}
        result['anchors'].append(row)
    # Includes joint clauses, exact weights, native node/edge caps and canonical rationals.
    validate(result)
    require(len(encoded(result)) <= MAX_INPUT_BYTES, 'OUTPUT_SIZE', 'Compiled graph exceeds byte limit')
    return result
