"""Independent cardinality checks for conditional temporal reference worlds."""
from fractions import Fraction
from pathlib import Path
import sys
import time

from timing_bounds import ROLES, digest, q, w
from timing_metadata import require

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'research/reference-translation/0.1.0'))
from axis_certificate import exact_iou, maximum_matching
from compare_math import checker, graph


def matching(image, references):
    ranks = []
    for role in ROLES:
        adjacency = {row['id']: {ref['id'] for ref in references
                     if exact_iou(list(map(q, row['xyxy'])), list(map(q, ref['xyxy']))) >= Fraction(1, 2)}
                     for row in image[role]['value']}
        ranks.append(maximum_matching(adjacency))
    delta = len(image[ROLES[0]]['value'])-len(image[ROLES[1]]['value'])+2*(ranks[1]-ranks[0])
    return {'ranks': ranks, 'delta': w(delta)}


def known_from_source(source):
    result = []
    for value in source['known_objects']:
        body = {'id': 'reference:'+value['annotation_token'],
                'xyxy': [w(Fraction(str(x))) for x in value['projection']['xyxy']]}
        result.append({**body, 'record_sha256': digest({'basis': 'declared_camera_time_motion_model', 'object': value, **body})})
    return result


def check_alternate_edges(image, known, source):
    for reference, coordinates in zip(known, source['alternative_coordinates']):
        alternative = [Fraction(str(x)) for x in coordinates]
        for role in ROLES:
            for prediction in image[role]['value']:
                geometry = list(map(q, prediction['xyxy']))
                require((exact_iou(geometry, list(map(q, reference['xyxy']))) >= Fraction(1, 2))
                        == (exact_iou(geometry, alternative) >= Fraction(1, 2)), 'Numerical projection changes a matching edge')


def check_pool(image, record):
    geometries = set()
    for role in ROLES:
        for prediction in image[role]['value']:
            x0, y0, x1, y1 = map(q, prediction['xyxy'])
            for axis, sign in [(0, 0), (0, -1), (0, 1), (1, -1), (1, 1)]:
                values = [x0, y0, x1, y1]
                offset = sign*(values[axis+2]-values[axis])/4
                values[axis] += offset; values[axis+2] += offset
                if values[0] >= 0 and values[1] >= 0 and values[2] <= image['width'] and values[3] <= image['height']:
                    geometries.add(tuple(values))
    require(record == {'rectangles': [list(map(w, values)) for values in sorted(geometries)[:256]],
                       'eligible_before_cap': len(geometries), 'truncated': len(geometries) > 256, 'limit': 256},
            'Declared candidate pool or truncation differs')


def expected_world(known, unknown_ids, indices, pool):
    require(type(indices) is list and len(indices) <= len(unknown_ids), 'World exceeds unknown-instance budget')
    result = list(known)
    for identity, index in zip(unknown_ids, indices):
        require(type(index) is int and 0 <= index < len(pool), 'World uses an undeclared candidate')
        body = {'id': 'timing-unknown:'+identity, 'xyxy': pool[index]}
        result.append({**body, 'record_sha256': digest({'basis': 'optional-reference-hypothesis', **body})})
    require(len(result) <= 128, 'Attained world exceeds native reference limit')
    return result


def independent_bounds(image, measured, count):
    a, b = (set(row['id'] for row in image[role]['value']) for role in ROLES)
    ra, rb = measured['ranks']; na, nb = len(a), len(b)
    lo = na-nb+2*(rb-min(na, ra+count))
    hi = na-nb+2*(min(nb, rb+count)-ra)
    shared_limit = len(a ^ b)
    return [w(max(-shared_limit, lo)), w(min(shared_limit, hi))]


def check_proof(key, value, image, expected, cache):
    require(value['references'] == expected and key == digest({'image_id': image['id'], 'references': expected}),
            'Proof substitutes geometry or image identity')
    measured = matching(image, expected)
    require(value['measurement'] == measured, 'Matching cardinality or delta differs')
    native = graph(image, expected); payload = value['proof']['payload']
    require(value['proof']['graph_sha256'] == digest(native), 'Native operand digest differs')
    identity = digest({'graph': native, 'payload': payload})
    if identity not in cache['native']:
        tick = time.perf_counter(); checker.check(native, payload)
        cache['native_check_seconds'] += time.perf_counter()-tick; cache['native'].add(identity)
    require(payload['result']['enclosure_kind'] == 'exact_for_finite_model'
            and payload['result']['bounds']['lower'] == measured['delta']
            and payload['result']['bounds']['upper'] == measured['delta'], 'Native proof claims a different exact value')
    return measured


def check_search(found, image, known, unknown_ids, pool):
    center = matching(image, known)
    require(found['known'] == center and found['unknown_ids'] == unknown_ids and found['unknown_count'] == len(unknown_ids),
            'Search changed known evidence or unknown membership')
    bounds = independent_bounds(image, center, len(unknown_ids))
    require(found['bounds'] == bounds and found['evaluation_limit'] == 4096, 'Universal bound or declared search limit differs')
    counted = 0
    for direction, endpoint in [('lower', 0), ('upper', 1)]:
        selected = []; previous = center
        require(len(found['steps'][direction]) <= len(unknown_ids), 'Search consumes too many unknown instances')
        for step in found['steps'][direction]:
            tested = step['tested_candidates']; chosen = step['chosen_candidate']
            require(type(tested) is int and 0 <= tested <= len(pool), 'Invalid candidate evaluation count')
            counted += tested
            if chosen is not None:
                require(type(chosen) is int and 0 <= chosen < tested, 'Chosen candidate was not evaluated')
                selected.append(chosen)
                current = matching(image, expected_world(known, unknown_ids, selected, pool))
                require(q(current['delta']) < q(previous['delta']) if direction == 'lower'
                        else q(current['delta']) > q(previous['delta']), 'Search step did not strictly improve its direction')
                previous = current
            require(step['result'] == previous, 'Search step matching differs')
        world = found['worlds'][direction]
        require(world['candidate_indices'] == selected and world['measurement'] == previous
                and world['endpoint_attained'] is (q(previous['delta']) == q(bounds[endpoint])), 'Attained endpoint claim differs')
        require(world['stop'] in ('unknown_budget_exhausted', 'universal_endpoint_attained', 'attained_reference_limit',
                                 'evaluation_limit', 'no_strict_single_addition_improvement'), 'Unknown search termination')
        if world['stop'] == 'universal_endpoint_attained':
            require(world['endpoint_attained'], 'Search stopped on an unattained bound')
        if world['stop'] == 'unknown_budget_exhausted':
            require(len(selected) == len(unknown_ids), 'Unknown budget was not exhausted')
        if world['stop'] == 'attained_reference_limit':
            require(len(known)+len(selected) == 128, 'Reference limit was not reached')
    require(counted == found['candidate_evaluations'] and counted <= 4096, 'Search budget exceeded or evaluations omitted')
    return bounds
