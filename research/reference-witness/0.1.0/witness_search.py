"""Bounded breadth-first multiset search with sound descendant pruning."""
from collections import deque
from fractions import Fraction
import time

from witness_pool import ROLES, iou, q, require, w
from timing_bounds import flow_rank, optional_bounds

MAX_MEASUREMENTS = 50000
MAX_REFERENCES = 128


def graph_search(image, known_ids, base_edges, neighborhoods, unknown_count, seeds=(),
                 measurement_limit=MAX_MEASUREMENTS, reference_limit=MAX_REFERENCES):
    require(type(unknown_count) is int and unknown_count >= 0, 'Unknown count must be explicit')
    require(type(measurement_limit) is int and measurement_limit >= 1
            and type(reference_limit) is int and reference_limit >= len(known_ids), 'Invalid search limit')
    lefts = [{row['id'] for row in image[role]['value']} for role in ROLES]
    require(len(known_ids) == len(set(known_ids)), 'Repeated known reference identity')
    prediction_ids = set.union(*lefts)
    require(all(set(values) <= prediction_ids and values for values in neighborhoods), 'Invalid neighborhood')
    require(all(left in prediction_ids and right in known_ids for left, right in base_edges), 'Invalid known edge')
    cache = {}; transcript = []; measured = 0
    def measure(indices, seed=False):
        nonlocal measured
        key = tuple(indices)
        if key in cache:
            return cache[key]
        if measured >= measurement_limit:
            return None
        right = {('known', value) for value in known_ids} | {('optional', i) for i in range(len(key))}
        edges = {(a, ('known', b)) for a, b in base_edges}
        edges.update((left, ('optional', j)) for j, index in enumerate(key) for left in neighborhoods[index])
        # The existing max-flow interface requires sortable homogeneous IDs.
        aliases = {value: 'r'+str(j) for j, value in enumerate(sorted(right))}
        ranks = [flow_rank(left, set(aliases.values()), {(a, aliases[b]) for a, b in edges if a in left}) for left in lefts]
        result = {'ranks': ranks, 'delta': w(len(lefts[0])-len(lefts[1])+2*(ranks[1]-ranks[0]))}
        cache[key] = result
        measured += 1; transcript.append({'indices': list(key), 'measurement': result, 'seed': seed})
        return result
    nominal = measure((), True); bounds = optional_bounds(image, nominal['ranks'], unknown_count)
    best = [{'indices': [], 'measurement': nominal}, {'indices': [], 'measurement': nominal}]
    def retain(indices, result):
        for endpoint in (0, 1):
            better = q(result['delta']) < q(best[endpoint]['measurement']['delta']) if endpoint == 0 else q(result['delta']) > q(best[endpoint]['measurement']['delta'])
            if better:
                best[endpoint] = {'indices': list(indices), 'measurement': result}
    seed_limit = False
    for seed in seeds:
        indices = seed['indices']
        require(indices == sorted(indices) and len(indices) <= unknown_count
                and len(indices)+len(known_ids) <= reference_limit
                and all(type(index) is int and 0 <= index < len(neighborhoods) for index in indices), 'Invalid seed world')
        value = measure(indices, True)
        if value is None:
            seed_limit = True; break
        require(value == seed['measurement'], 'Inherited seed changed matching ranks')
        retain(indices, value)
    queue = deque([()]); expanded = pruned = 0; reference_cut = False
    stop = 'evaluation_limit' if seed_limit else None
    while queue and stop is None:
        if all(q(best[i]['measurement']['delta']) == bounds[i] for i in (0, 1)):
            stop = 'universal_endpoints_attained'; break
        indices = queue.popleft(); current = cache[indices]
        remain = unknown_count-len(indices)
        enclosure = optional_bounds(image, current['ranks'], remain)
        if enclosure[0] >= q(best[0]['measurement']['delta']) and enclosure[1] <= q(best[1]['measurement']['delta']):
            pruned += 1; continue
        if remain == 0:
            continue
        if len(indices)+len(known_ids) >= reference_limit:
            reference_cut = True; continue
        expanded += 1
        for index in range(indices[-1] if indices else 0, len(neighborhoods)):
            child = indices+(index,); value = measure(child)
            if value is None:
                stop = 'evaluation_limit'; break
            retain(child, value); queue.append(child)
            if all(q(best[i]['measurement']['delta']) == bounds[i] for i in (0, 1)):
                stop = 'universal_endpoints_attained'; break
    if stop is None:
        stop = 'reference_limit' if reference_cut else 'finite_pool_exhausted'
    require(bounds[0] <= q(best[0]['measurement']['delta']) <= q(nominal['delta'])
            <= q(best[1]['measurement']['delta']) <= bounds[1], 'Attained world violates universal enclosure')
    return {'known': nominal, 'bounds': list(map(w, bounds)), 'worlds': best, 'stop': stop,
            'unknown_count': unknown_count, 'measurement_limit': measurement_limit, 'reference_limit': reference_limit,
            'unique_flow_measurements': measured, 'expanded_nodes': expanded, 'pruned_nodes': pruned,
            'reference_cut_encountered': reference_cut, 'transcript': transcript,
            'universal_endpoints_attained': all(q(best[i]['measurement']['delta']) == bounds[i] for i in (0, 1)),
            'finite_pool_search_complete': stop in ('universal_endpoints_attained', 'finite_pool_exhausted')}


def search(image, known, unknown_ids, pool, seeds=()):
    tick = time.perf_counter()
    require(unknown_ids == sorted(set(unknown_ids)), 'Unknown instances require a sorted unique census')
    predictions = {row['id']: row for role in ROLES for row in image[role]['value']}
    edges = {(identity, row['id']) for identity, detection in predictions.items() for row in known
             if iou(detection, row) >= Fraction(1, 2)}
    found = graph_search(image, [row['id'] for row in known], edges, pool['neighborhoods'], len(unknown_ids), seeds)
    return {**found, 'unknown_ids': unknown_ids, 'seconds': time.perf_counter()-tick}
