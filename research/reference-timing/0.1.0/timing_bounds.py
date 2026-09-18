"""Conventional optional-reference bounds and bounded geometric witnesses."""
from fractions import Fraction
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'research/public-predictions/0.1.0'))
from compare_math import (ROLES, checked_ranks, conventional_measure, digest, flow_rank,
                          iou, open_interval, q, validate_canvas, validate_rows, w)
from timing_metadata import require

CONTRACTS = ('current_strict', 'current_partial', 'union_strict', 'union_partial')
MAX_CANDIDATES = 256
MAX_EVALUATIONS = 4096
MAX_ATTAINED_REFERENCES = 128


def optional_bounds(image, ranks, count):
    require(type(count) is int and count >= 0 and len(ranks) == 2, 'Invalid unknown count or rank pair')
    na, nb = [len(image[role]['value']) for role in ROLES]
    ra, rb = ranks
    require(all(type(value) is int for value in ranks) and 0 <= ra <= na and 0 <= rb <= nb, 'Invalid matching ranks')
    center = na-nb+2*(rb-ra)
    base = open_interval(image)
    lower, upper = max(base[0], Fraction(center-2*min(count, na-ra))), min(base[1], Fraction(center+2*min(count, nb-rb)))
    require(lower <= center <= upper, 'Rank pair contradicts the shared prediction identities')
    return lower, upper


def candidates(image, limit=MAX_CANDIDATES):
    require(type(limit) is int and limit >= 0, 'Invalid candidate limit')
    found = set()
    for role in ROLES:
        for row in image[role]['value']:
            x1, y1, x2, y2 = map(q, row['xyxy']); dx, dy = (x2-x1)/4, (y2-y1)/4
            for shift_x, shift_y in [(0, 0), (-dx, 0), (dx, 0), (0, -dy), (0, dy)]:
                geometry = (x1+shift_x, y1+shift_y, x2+shift_x, y2+shift_y)
                if 0 <= geometry[0] < geometry[2] <= image['width'] and 0 <= geometry[1] < geometry[3] <= image['height']:
                    found.add(geometry)
    ordered = sorted(found)
    return {'rectangles': [list(map(w, values)) for values in ordered[:limit]],
            'eligible_before_cap': len(ordered), 'truncated': len(ordered) > limit, 'limit': limit}


def unknown_rectangle(identity, geometry):
    body = {'id': 'timing-unknown:' + identity, 'xyxy': geometry}
    return {**body, 'record_sha256': digest({'basis': 'optional-reference-hypothesis', **body})}


def world_references(known, unknown_ids, indices, pool):
    require(len(indices) <= len(unknown_ids) and len(set(unknown_ids)) == len(unknown_ids), 'Unknown-instance budget exceeded')
    return known + [unknown_rectangle(identity, pool[index]) for identity, index in zip(unknown_ids, indices)]


def search(image, known, unknown_ids, pool_record, evaluation_limit=MAX_EVALUATIONS):
    tick = time.perf_counter(); validate_rows(known); validate_canvas(known, image)
    require(type(evaluation_limit) is int and evaluation_limit >= 0, 'Invalid evaluation budget')
    require(unknown_ids == sorted(set(unknown_ids)), 'Unknown instances require a sorted unique census')
    pool = pool_record['rectangles']; predictions = {row['id']: row for role in ROLES for row in image[role]['value']}
    base_edges = {(key, row['id']) for key, detection in predictions.items() for row in known if iou(detection, row) >= Fraction(1, 2)}
    neighborhoods = [{key for key, detection in predictions.items() if iou(detection, {'xyxy': geometry}) >= Fraction(1, 2)}
                     for geometry in pool]
    base_right = {row['id'] for row in known}; cache = {}; solver_calls = 0
    def measure(indices):
        nonlocal solver_calls
        key = tuple(indices)
        if key in cache:
            return cache[key]
        right = base_right | {'timing-unknown:' + value for value in unknown_ids[:len(indices)]}
        edges = base_edges | {(detection, 'timing-unknown:' + identity)
                              for identity, index in zip(unknown_ids, indices) for detection in neighborhoods[index]}
        ranks = []
        for role in ROLES:
            left = {row['id'] for row in image[role]['value']}
            ranks.append(flow_rank(left, right, {(a, b) for a, b in edges if a in left}))
        delta = len(image[ROLES[0]]['value']) - len(image[ROLES[1]]['value']) + 2*(ranks[1]-ranks[0])
        result = {'ranks': ranks, 'delta': w(delta)}; cache[key] = result; solver_calls += 1
        return result
    nominal = measure([]); enclosure = optional_bounds(image, nominal['ranks'], len(unknown_ids))
    evaluations = 0; worlds = {}; steps = {}
    for direction, index in [('lower', 0), ('upper', 1)]:
        selected = []; current = nominal; trace = []; stop = 'unknown_budget_exhausted'
        for _ in range(len(unknown_ids)):
            if q(current['delta']) == enclosure[index]:
                stop = 'universal_endpoint_attained'; break
            if len(known) + len(selected) >= MAX_ATTAINED_REFERENCES:
                stop = 'attained_reference_limit'; break
            best = current; best_index = None; evaluated = 0
            for candidate_index in range(len(pool)):
                if evaluations >= evaluation_limit:
                    stop = 'evaluation_limit'; break
                trial = measure(selected + [candidate_index]); evaluations += 1; evaluated += 1
                better = q(trial['delta']) < q(best['delta']) if direction == 'lower' else q(trial['delta']) > q(best['delta'])
                if better:
                    best = trial; best_index = candidate_index
            trace.append({'tested_candidates': evaluated, 'chosen_candidate': best_index, 'result': best})
            if best_index is not None:
                selected.append(best_index); current = best
            if evaluations >= evaluation_limit:
                stop = 'evaluation_limit'; break
            if best_index is None:
                stop = 'no_strict_single_addition_improvement'; break
        worlds[direction] = {'candidate_indices': selected, 'measurement': current,
                             'endpoint_attained': q(current['delta']) == enclosure[index], 'stop': stop}
        steps[direction] = trace
    require(enclosure[0] <= q(worlds['lower']['measurement']['delta']) <= q(nominal['delta'])
            <= q(worlds['upper']['measurement']['delta']) <= enclosure[1], 'Attained world outside universal enclosure')
    return {'known': nominal, 'bounds': list(map(w, enclosure)), 'unknown_count': len(unknown_ids),
            'unknown_ids': unknown_ids, 'worlds': worlds, 'steps': steps, 'candidate_evaluations': evaluations,
            'unique_flow_measurements': solver_calls, 'evaluation_limit': evaluation_limit,
            'seconds': time.perf_counter() - tick}


def certify(image, known, unknown_ids, indices, pool, proof_cache):
    references = world_references(known, unknown_ids, indices, pool)
    key = digest({'image_id': image['id'], 'references': references})
    if key not in proof_cache:
        direct = conventional_measure(image, references)
        native, proof, timing = checked_ranks(image, references)
        require(direct == native, 'Conventional/native matching disagreement')
        proof_cache[key] = {'references': references, 'measurement': direct, 'proof': proof, 'native_timing': timing}
    return key


def outcome(bounds):
    if bounds is None:
        return 'input_blocked'
    return 'supported' if bounds[0] > 0 else 'excluded' if bounds[1] <= 0 else 'unresolved'


def case_rows(cases, records):
    rows = []
    for case in cases:
        for contract in CONTRACTS:
            members = case['images']; blocked = [iid for iid in members if records[iid]['contracts'][contract]['state'] != 'available']
            base = {'case_id': case['id'], 'group': case['group'], 'contract': contract,
                    'allocated_images': len(members), 'membership': members, 'blocked_images': blocked}
            if blocked:
                rows.append({**base, 'state': 'input_blocked', 'bounds': None, 'attained': None,
                             'decision': 'input_blocked', 'evidence': None, 'worlds': None})
                continue
            values = [records[iid]['contracts'][contract] for iid in members]
            bounds = [sum((q(value['bounds'][j]) for value in values), Fraction(0))/len(members) for j in (0, 1)]
            attained = [sum((q(value['attained'][j]) for value in values), Fraction(0))/len(members) for j in (0, 1)]
            decision = outcome(bounds)
            evidence = ('opposite_worlds' if attained[0] <= 0 < attained[1] else 'bound_gap') if decision == 'unresolved' else 'universal_bound'
            rows.append({**base, 'state': 'available', 'bounds': list(map(w, bounds)), 'attained': list(map(w, attained)),
                         'decision': decision, 'evidence': evidence,
                         'worlds': [[{'image_id': iid, 'proof_key': records[iid]['contracts'][contract]['proof_keys'][j]}
                                    for iid in members] for j in (0, 1)]})
    return rows
