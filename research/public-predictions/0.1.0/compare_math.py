"""Common frozen observation mathematics, with two matching implementations.

No private answer path or prediction runtime is imported. The conventional
max-flow implementation and Engine proof producer/checker are reused from
the preceding research. Both arms receive the same one-edit bound.
"""
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
import sys
import time

from admission import closed, digest, integer, require, sha

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'research/correction-observation/0.1.0'))
from common import (ROLES, conventional_measure, flow_rank, iou, native_graph as predecessor_graph,
                    open_interval, q, validate_rows, w)
from refine import graph_edit_bounds
from tools.perception_revision import checker, contract, kernel

VERSION = '0.1.0'
FAMILIES = ('exact_projection', 'one_edit_per_image', 'one_edit_global')
ARMS = {'A': ('width', 'conventional'), 'B': ('width', 'native'),
        'C': ('count_difference', 'native'), 'D': ('count_difference', 'conventional')}


def subject(image):
    return digest(image)


def linked(image):
    return image['reference_input_state'] == 'available' and all(image[role]['state'] == 'observed' for role in ROLES)


def validate_image(image):
    closed(image, ('id', 'ordinal', 'width', 'height', 'image_sha256', 'policy_sha256',
                   'output_a', 'output_b', 'reference_input_state'), 'visible image')
    require(type(image['id']) is str and image['id'], 'IMAGE', 'Image ID required')
    integer(image['ordinal'], 0, 63, 'ORDINAL')
    integer(image['width'], 1, 32768, 'DIMENSION'); integer(image['height'], 1, 32768, 'DIMENSION')
    sha(image['image_sha256']); sha(image['policy_sha256'])
    require(image['reference_input_state'] in ('available', 'unavailable'), 'STATE', 'Reference availability required')
    for role in ROLES:
        operand = image[role]
        require(type(operand) is dict and operand.get('state') in ('observed', 'unavailable'), 'STATE', 'Operand state required')
        closed(operand, ('state', 'value') if operand['state'] == 'observed' else ('state', 'reason'), 'operand')
        if operand['state'] == 'observed':
            validate_rows(operand['value'])
            validate_canvas(operand['value'], image)
        else:
            require(type(operand['reason']) is str and operand['reason'], 'STATE', 'Unavailable operand requires a reason')
    if all(image[role]['state'] == 'observed' for role in ROLES):
        open_interval(image)  # Also checks consistency of shared IDs and geometry.


def validate_canvas(rows, image):
    for row in rows:
        x1, y1, x2, y2 = map(q, row['xyxy'])
        require(0 <= x1 < x2 <= image['width'] and 0 <= y1 < y2 <= image['height'],
                'COORDINATE', 'Eligible rectangle outside bound image')


def graph(image, references):
    value = predecessor_graph(image, references)
    value['comparison_id'] = 'public-predictions:' + image['id']
    value['cohort_id'] = 'public-predictions:' + subject(image)
    value['assumptions'] = [
        'Frozen local public-checkpoint outputs on exposed development images; supplied projection is a premise.',
        'Exact nominal matching only; the stated residual edit envelope is derived separately.',
        'This graph asserts neither physical truth nor observed human work.']
    return contract.validate(value)


def graph_ranks(image, references, edges, removed=None):
    right = {row['id'] for row in references if row['id'] != removed}
    counts = [len(image[role]['value']) for role in ROLES]
    ranks = []
    for role in ROLES:
        left = {row['id'] for row in image[role]['value']}
        ranks.append(flow_rank(left, right, {(d, r) for d, r in edges if d in left and r in right}))
    return {'ranks': ranks, 'delta': w(counts[0] - counts[1] + 2 * (ranks[1] - ranks[0]))}


def checked_ranks(image, references):
    start = time.perf_counter(); value = graph(image, references); compiled = time.perf_counter()
    payload = kernel.produce(value); proposed = time.perf_counter()
    checker.check(value, payload); checked = time.perf_counter()
    require(payload['result']['enclosure_kind'] == 'exact_for_finite_model', 'BOUND', 'Native exact matching required')
    anchor = payload['proof']['worlds'][0]['anchors'][0]
    ranks = [len(anchor[role]['matching']) for role in ROLES]
    measured = {'ranks': ranks, 'delta': payload['result']['bounds']['lower']}
    proof = {'graph_sha256': digest(value), 'payload': payload}
    return measured, proof, {'compile_seconds': compiled - start, 'proposal_seconds': proposed - compiled,
                             'check_seconds': checked - proposed}


def measure(image, references, family, method):
    require(linked(image) and family in FAMILIES and method in ('conventional', 'native'), 'METHOD', 'Unknown or blocked measurement')
    validate_rows(references); validate_canvas(references, image)
    start = time.perf_counter()
    removals = [None] + ([row['id'] for row in references] if family != 'exact_projection' else [])
    bases, proofs = [], []
    timing = {'compile_seconds': 0.0, 'proposal_seconds': 0.0, 'check_seconds': 0.0}
    if method == 'conventional':
        tick = time.perf_counter()
        detections = {row['id']: row for role in ROLES for row in image[role]['value']}
        edges = {(did, row['id']) for did, detection in detections.items() for row in references
                 if iou(detection, row) >= Fraction(1, 2)}
        timing['compile_seconds'] = time.perf_counter() - tick
        for removed in removals:
            bases.append(graph_ranks(image, references, edges, removed))
    else:
        for removed in removals:
            selected = [row for row in references if row['id'] != removed]
            measured, proof, cost = checked_ranks(image, selected)
            bases.append(measured); proofs.append({'removed_reference': removed, **proof})
            for key, seconds in cost.items():
                timing[key] += seconds
    nominal = bases[0]
    bounds = (q(nominal['delta']), q(nominal['delta'])) if family == 'exact_projection' else graph_edit_bounds(image, bases)
    require(bounds[0] <= q(nominal['delta']) <= bounds[1], 'BOUND', 'Residual envelope excludes the unedited premise')
    return {'nominal': nominal, 'edit_bounds': [w(value) for value in bounds],
            'deletion_bases': [{'removed_reference': removed, 'measurement': base} for removed, base in zip(removals, bases)],
            'proofs': proofs, 'timing': {**timing, 'measurement_seconds': time.perf_counter() - start}}


def interval(images, measurements, family):
    require(family in FAMILIES and images, 'FAMILY', 'Unknown family or empty case')
    if not all(linked(image) for image in images):
        return None
    lower = upper = Fraction(0); downward, upward = [], []
    for image in images:
        if image['id'] not in measurements:
            lo, hi = open_interval(image)
        else:
            measured = measurements[image['id']]
            nominal = q(measured['nominal']['delta']); lo = hi = nominal
            edit_lo, edit_hi = map(q, measured['edit_bounds'])
            if family == 'one_edit_per_image':
                lo, hi = edit_lo, edit_hi
            elif family == 'one_edit_global':
                downward.append(nominal - edit_lo); upward.append(edit_hi - nominal)
        lower += lo; upper += hi
    if family == 'one_edit_global':
        lower -= max(downward, default=0); upper += max(upward, default=0)
    return lower / len(images), upper / len(images)


def decision(bounds):
    if bounds is None:
        return 'input_blocked'
    return 'supported' if bounds[0] > 0 else 'excluded' if bounds[1] <= 0 else 'unresolved'


def wire_interval(bounds):
    return None if bounds is None else [w(value) for value in bounds]


def ranking(images, policy):
    require(policy in ('width', 'count_difference'), 'SELECTOR', 'Unknown selector')
    if not all(linked(image) for image in images):
        return []
    eligible = [image for image in images if open_interval(image)[0] != open_interval(image)[1]]
    def key(image):
        size = open_interval(image)[1]
        difference = abs(len(image['output_a']['value']) - len(image['output_b']['value']))
        return (-size, image['ordinal']) if policy == 'width' else (-difference, -size, image['ordinal'])
    return [image['id'] for image in sorted(eligible, key=key)]


def validate_event(event, request, image):
    closed(event, ('request', 'answer', 'source_sha256', 'basis', 'residual', 'requested_utc',
                   'returned_utc', 'cost', 'evidence_sha256'), 'observation')
    require(event['request'] == request and request['subject_sha256'] == subject(image),
            'OBSERVATION', 'Wrong query subject, sequence or context')
    require(event['basis'] == 'published_annotation_projection' and event['residual'] == request['family'],
            'OBSERVATION', 'Observation basis or residual premise changed')
    sha(event['source_sha256'])
    require(event['evidence_sha256'] == digest({key: value for key, value in event.items() if key != 'evidence_sha256'}),
            'OBSERVATION', 'Observation bytes changed')
    closed(event['cost'], ('observation_units', 'human_seconds', 'human_cost', 'service_seconds'), 'observation cost')
    require(type(event['cost']['observation_units']) is int and event['cost']['observation_units'] == 1
            and event['cost']['human_seconds'] is None
            and event['cost']['human_cost'] is None, 'COST', 'No measured human work is available')
    validate_rows(event['answer']); validate_canvas(event['answer'], image)
    return event['answer']
