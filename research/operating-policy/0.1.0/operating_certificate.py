"""Separate filtering, matching, bounds and case arithmetic checks."""
from collections import Counter
from copy import deepcopy
from fractions import Fraction
import math
import time

from operating_sources import ROLES, digest, q, require, w
from operating_math import FAMILIES
from compare_math import checker, graph
from timing_certificate import matching


def decimal(value):
    require(type(value) in (int, float) and math.isfinite(value), 'Nonfinite or nonnumeric source value')
    return Fraction(str(value))


def expected_filter(original, packets, threshold, policy):
    require(Fraction(1, 4) <= threshold <= 1, 'Threshold outside score custody')
    image = deepcopy(original); image['policy_sha256'] = policy; joins = {}
    for role in ROLES:
        source = packets[role][original['id']]
        if source['state'] not in ('processed', 'empty'):
            image[role] = {'state': 'unavailable', 'reason': source['state']+': '+source['reason']}; joins[role] = []; continue
        rows = []; custody = []; occurrences = {}
        for detection in source['detections']:
            box = [decimal(value) for value in detection['xyxy']]; score = decimal(detection['score'])
            require(Fraction(1, 4) < score <= 1, 'Score not in source range')
            reason = 'category_outside_car' if detection['category_id'] != 2 else 'height_below_25' if box[3]-box[1] < 25 else 'score_not_strictly_above_threshold' if score <= threshold else None
            if reason:
                custody.append({'source_detection_id': detection['id'], 'state': 'excluded', 'reason': reason}); continue
            require(detection['category_name'] == 'car', 'Source category mapping differs')
            geometry = list(map(w, box)); signature = digest({'category': 'car', 'xyxy': geometry})
            count = occurrences.get(signature, 0); occurrences[signature] = count+1
            key = 'prediction:'+digest({'signature': signature, 'occurrence': count})
            row = {'id': key, 'xyxy': geometry}; rows.append({**row, 'record_sha256': digest(row)})
            custody.append({'source_detection_id': detection['id'], 'state': 'eligible', 'record_id': key})
        image[role] = {'state': 'observed', 'value': rows}; joins[role] = custody
    return image, joins


def expected_cells(scores):
    breakpoints = {Fraction(1, 4), Fraction(1)}
    for score in scores:
        require(Fraction(1, 4) < score <= 1, 'Threshold event outside source range'); breakpoints.add(score)
    ordered = sorted(breakpoints); result = []
    for index, point in enumerate(ordered):
        right = ordered[index+1] if index+1 < len(ordered) else point
        result.append({'id': 'cell-'+str(index).zfill(4), 'left': w(point), 'right': w(right),
                       'left_closed': True, 'right_closed': point == 1, 'representative': w(point)})
    return result


def verify_proof(key, record, cache):
    image, references = record['image'], record['references']
    require(key == digest({'image': image, 'references': references}), 'Native proof substitutes operands')
    measured = matching(image, references); require(record['measurement'] == measured, 'Independent matching differs')
    compiled = graph(image, references); payload = record['proof']['payload']
    require(record['proof']['graph_sha256'] == digest(compiled), 'Native graph digest differs')
    identity = digest({'graph': compiled, 'payload': payload})
    if identity not in cache['native']:
        tick = time.perf_counter(); checker.check(compiled, payload)
        cache['native_check_seconds'] += time.perf_counter()-tick; cache['native'].add(identity)
    require(payload['result']['enclosure_kind'] == 'exact_for_finite_model'
            and payload['result']['bounds']['lower'] == measured['delta']
            and payload['result']['bounds']['upper'] == measured['delta'], 'Native exact value differs')
    return measured


def independent_analysis(image, bank, proofs):
    keys = {world: digest({'image': image, 'references': references}) for world, references in bank['worlds'].items()}
    require(all(key in proofs for key in keys.values()), 'World bank proof omitted')
    for world, key in keys.items():
        require(proofs[key]['image'] == image and proofs[key]['references'] == bank['worlds'][world], 'World bank operand changed')
    nominal_key = keys[bank['original_world']]; known_key = keys[bank['known_world']]
    nominal = proofs[nominal_key]['measurement']; known = proofs[known_key]['measurement']
    lefts = [{row['id'] for row in image[role]['value']} for role in ROLES]; na, nb = map(len, lefts)
    cap = len(lefts[0] ^ lefts[1]); lower = []; upper = []
    for deletion in bank['deletions']:
        ra, rb = proofs[keys[deletion['world']]]['measurement']['ranks']
        lower.append(na-nb+2*rb-2*min(na, ra+1))
        upper.append(na-nb+2*min(nb, rb+1)-2*ra)
    edit_bounds = [max(-cap, min(lower)), min(cap, max(upper))]
    def checked_contract(bounds, world_keys):
        smallest = sorted(world_keys, key=lambda key: (q(proofs[key]['measurement']['delta']), key))[0]
        largest = sorted(world_keys, key=lambda key: (-q(proofs[key]['measurement']['delta']), key))[0]
        attained = [proofs[key]['measurement']['delta'] for key in (smallest, largest)]
        require(bounds[0] <= q(attained[0]) <= q(attained[1]) <= bounds[1], 'World lies outside derived bounds')
        return {'state': 'available', 'bounds': list(map(w, bounds)), 'attained': attained, 'proof_keys': [smallest, largest]}
    center = q(nominal['delta']); families = {'exact_projection': checked_contract([center, center], [nominal_key])}
    for family in ('one_edit_global', 'one_edit_per_image'):
        families[family] = checked_contract(edit_bounds, [keys[key] for key in bank['edit_worlds']])
    for scope in ('current', 'union'):
        source = bank['temporal'][scope]
        if source['state'] == 'input_blocked':
            for suffix in ('strict', 'partial'):
                families[scope+'_'+suffix] = {'state': 'input_blocked', 'reason': 'preceding_census_unavailable',
                                              'bounds': None, 'attained': None, 'proof_keys': None}
            continue
        k = len(source['unknown_ids']); require(source['unknown_count'] == k, 'Unknown count changed')
        ra, rb = known['ranks']
        bounds = [max(-cap, na-nb+2*(rb-min(na,ra+k))), min(cap, na-nb+2*(min(nb,rb+k)-ra))]
        families[scope+'_partial'] = checked_contract(bounds, [keys[key] for key in source['worlds']])
        if k:
            families[scope+'_strict'] = {'state': 'input_blocked', 'reason': 'motion_unavailable_for_census_instances',
                                        'bounds': None, 'attained': None, 'proof_keys': None}
        else:
            center = q(known['delta']); families[scope+'_strict'] = checked_contract([center, center], [known_key])
    nr = len(bank['worlds'][bank['original_world']])
    return {'families': families, 'world_proof_keys': keys, 'nominal_proof_key': nominal_key, 'known_proof_key': known_key,
            'nominal': nominal, 'nominal_reference_count': nr, 'prediction_counts': [na, nb],
            'nominal_fp': [na-nominal['ranks'][0], nb-nominal['ranks'][1]],
            'nominal_fn': [nr-rank for rank in nominal['ranks']]}


def check_case(row, case, family, expected_state_keys, states, proofs):
    require(row['case_id'] == case['id'] and row['group'] == case['group'] and row['family'] == family
            and row['membership'] == case['images'] and row['allocated_images'] == len(case['images'])
            and row['state_keys'] == expected_state_keys, 'Case allocation or filtered state changed')
    components = [states[key]['analysis'] for key in expected_state_keys]
    values = [component['families'][family] for component in components]
    blocked = [iid for iid, value in zip(case['images'], values) if value['state'] != 'available']
    require(row['blocked_images'] == blocked, 'Blocked image omitted')
    if blocked:
        require(row['state'] == row['decision'] == 'input_blocked'
                and all(row[key] is None for key in ('bounds', 'attained', 'evidence', 'world_proof_keys')),
                'Missing input became filtered empty or a decision')
        return
    size = len(values); bounds = []; attained = []; worlds = []
    nominal = [q(component['nominal']['delta']) for component in components]; total = sum(nominal, Fraction(0))
    for endpoint in (0, 1):
        if family == 'one_edit_global':
            candidates = [total-nominal[i]+q(value['bounds'][endpoint]) for i, value in enumerate(values)]
            attainable = [total-nominal[i]+q(value['attained'][endpoint]) for i, value in enumerate(values)]
            if endpoint == 0:
                bound = min(candidates); value = min(attainable)
            else:
                bound = max(candidates); value = max(attainable)
            chosen = attainable.index(value)
            keys = [component['nominal_proof_key'] if i != chosen else values[i]['proof_keys'][endpoint]
                    for i, component in enumerate(components)]
        else:
            bound = sum((q(value['bounds'][endpoint]) for value in values), Fraction(0))
            value = sum((q(value['attained'][endpoint]) for value in values), Fraction(0))
            keys = [record['proof_keys'][endpoint] for record in values]
        require(sum((q(proofs[key]['measurement']['delta']) for key in keys), Fraction(0)) == value, 'Composed world value differs')
        bounds.append(bound/size); attained.append(value/size); worlds.append(keys)
    decision = 'supported' if bounds[0] > 0 else 'excluded' if bounds[1] <= 0 else 'unresolved'
    evidence = 'universal_bound' if decision != 'unresolved' else 'opposite_worlds' if attained[0] <= 0 < attained[1] else 'bound_gap'
    require(row['state'] == 'available' and row['bounds'] == list(map(w, bounds)) and row['attained'] == list(map(w, attained))
            and row['decision'] == decision and row['evidence'] == evidence and row['world_proof_keys'] == worlds,
            'Case bounds, attained worlds or decision differ')


def check_curves(first, second, maximum_budget, report):
    expected_frontiers = []
    for curve in (first, second):
        pairs = {(row['false_positives'], row['misses']) for row in curve}
        nondominated = sorted(pair for pair in pairs if not any(other != pair and other[0] <= pair[0] and other[1] <= pair[1] for other in pairs))
        expected_frontiers.append([{'false_positives': fp, 'misses': fn, 'cell_ids': [row['cell_id'] for row in curve
                                  if row['false_positives'] == fp and row['misses'] == fn]} for fp, fn in nondominated])
    require(report['frontiers'] == expected_frontiers, 'Frontier omits an attained nondominated point or tie')
    require(len(report['false_positive_budgets']) == maximum_budget+1, 'Budget allocation differs')
    for budget, row in enumerate(report['false_positive_budgets']):
        expected = []
        for curve in (first, second):
            admitted = [point for point in curve if point['false_positives'] <= budget]
            miss = min((point['misses'] for point in admitted), default=None)
            expected.append({'false_positive_budget': budget, 'state': 'available' if admitted else 'infeasible',
                             'minimum_misses': miss, 'cell_ids': [point['cell_id'] for point in admitted if point['misses'] == miss]})
        available = all(value['state'] == 'available' for value in expected)
        delta = expected[0]['minimum_misses']-expected[1]['minimum_misses'] if available else None
        kind = 'unavailable' if not available else 'new_fewer_misses' if delta > 0 else 'old_fewer_misses' if delta < 0 else 'equal_misses'
        require(row == {'false_positive_budget': budget, 'roles': expected, 'miss_difference_old_minus_new': delta,
                        'comparison': kind}, 'Budget minimum, infeasibility or tie differs')
    grid = report['nominal_pair_grid']; require(grid['new_cell_ids'] == [row['cell_id'] for row in second]
            and len(grid['rows']) == len(first) and grid['allocated_pairs'] == len(first)*len(second), 'Pair grid allocation differs')
    positive = nonpositive = 0
    for point, row in zip(first, grid['rows']):
        expected = [point['false_positives']+point['misses']-(other['false_positives']+other['misses']) for other in second]
        require(row == {'old_cell_id': point['cell_id'], 'old_minus_new_total_loss': expected}, 'Pair grid loss differs')
        positive += sum(value > 0 for value in expected); nonpositive += sum(value <= 0 for value in expected)
    require(grid['positive_pairs'] == positive and grid['nonpositive_pairs'] == nonpositive, 'Pair-grid aggregate differs')
    require(len(report['retrospective_minimum_unit_losses']) == 2, 'Detector loss minimum omitted')
    for curve, selected in zip((first, second), report['retrospective_minimum_unit_losses']):
        low = min(point['false_positives']+point['misses'] for point in curve)
        require(selected == {'minimum_unit_loss': low, 'cell_ids': [point['cell_id'] for point in curve
                                  if point['false_positives']+point['misses'] == low]}, 'Retrospective unit-loss minimum differs')
    require(report['thresholds_selected_for_deployment'] is False, 'Development frontier became a deployment policy')
