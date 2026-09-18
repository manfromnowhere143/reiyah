"""Exhaust a declared one-reference, one-axis translation family per image."""
from fractions import Fraction
from pathlib import Path
import sys
import time

from axis_cells import Cell, minimum_radius, partition, reachable, translate

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'research/public-predictions/0.1.0'))
from admission import digest, require
from compare_math import (ROLES, checked_ranks, decision, flow_rank, iou, linked, measure,
                          q, subject, validate_canvas, validate_image, validate_rows, w)
from geometric_worlds import coordinates, record

RADII = (0, 1, 2, 4, 8, 16, 32, 64)
MAX_CELLS = 100000
MAX_STATES = 50000


def state_cell(state):
    return Cell(q(state['cell'][0]), q(state['cell'][1]))


def enumerate_image(image, references):
    started = time.perf_counter()
    validate_image(image); validate_rows(references); validate_canvas(references, image)
    require(linked(image), 'INPUT', 'Unavailable is not an empty reference')
    require(all(coordinates(row)[3] - coordinates(row)[1] >= 25 for row in references),
            'ELIGIBILITY', 'Reference below declared height threshold')
    nominal = measure(image, references, 'exact_projection', 'conventional')['nominal']
    detections = {row['id']: row for role in ROLES for row in image[role]['value']}
    detection_ids = sorted(detections)
    boxes = [coordinates(detections[did]) for did in detection_ids]
    reference_ids = {row['id'] for row in references}
    original_edges = {(did, row['id']) for did, detection in detections.items() for row in references
                      if iou(detection, row) >= Fraction(1, 2)}
    sentinel = 'translation:graph-only-vertex'
    require(sentinel not in reference_ids, 'IDENTITY', 'Synthetic graph vertex collides')
    cache = {}; states = []; axes = 0
    for index, reference in enumerate(references):
        base = coordinates(reference)
        right = (reference_ids - {reference['id']}) | {sentinel}
        for axis in (0, 1):
            cells, intervals = partition(base, boxes, axis, image['width'], image['height']); axes += 1
            require(len(states) + len(cells) <= MAX_CELLS, 'SEARCH_LIMIT', 'Translation-cell limit reached')
            for ordinal, cell in enumerate(cells):
                position = cell.representative()
                neighbors = tuple(did for did, bounds in zip(detection_ids, intervals)
                                  if bounds is not None and bounds[0] <= position <= bounds[1])
                key = (index, neighbors)
                if key not in cache:
                    require(len(cache) < MAX_STATES, 'SEARCH_LIMIT', 'Translation matching-state limit reached')
                    edges = {(d, r) for d, r in original_edges if r != reference['id']} | {(did, sentinel) for did in neighbors}
                    ranks = [flow_rank({row['id'] for row in image[role]['value']}, right,
                                       {(d, r) for d, r in edges if d in {row['id'] for row in image[role]['value']}})
                             for role in ROLES]
                    counts = [len(image[role]['value']) for role in ROLES]
                    cache[key] = {'ranks': ranks, 'delta': w(Fraction(counts[0] - counts[1] + 2 * (ranks[1] - ranks[0])))}
                infimum, attained = minimum_radius(cell, base[axis])
                states.append({'id': f'reference-{index}:axis-{axis}:cell-{ordinal}',
                               'reference_index': index, 'reference_id': reference['id'], 'axis': axis,
                               'cell': [w(cell.left), w(cell.right)], 'point': cell.point,
                               'neighbors': list(neighbors), 'measurement': cache[key],
                               'radius_infimum': w(infimum), 'infimum_attained': attained})
    return {'image_id': image['id'], 'subject_sha256': subject(image), 'reference_sha256': digest(references),
            'nominal': nominal, 'states': states, 'axes': axes, 'cells': len(states),
            'matching_states': len(cache), 'seconds': time.perf_counter() - started,
            'exhaustive_for_declared_axis_family': True}


def extrema_states(record, radius):
    radius = Fraction(radius)
    require(radius >= 0, 'RADIUS', 'Negative uncertainty radius')
    nominal = q(record['nominal']['delta'])
    low = high = (nominal, None)
    for state in record['states']:
        limit = q(state['radius_infimum'])
        if limit < radius or (limit == radius and state['infimum_attained']):
            value = q(state['measurement']['delta'])
            if value < low[0]:
                low = (value, state)
            if value > high[0]:
                high = (value, state)
    return low, high


def attained_world(image, references, state, radius):
    if state is None:
        return references, {'operation': 'none'}
    index = state['reference_index']; reference = references[index]
    require(reference['id'] == state['reference_id'], 'IDENTITY', 'Translation reference changed')
    base = coordinates(reference); axis = state['axis']
    position = reachable(state_cell(state), base[axis], radius)
    require(position is not None, 'RADIUS', 'Claimed translation cell is unreachable')
    translated = record(translate(base, axis, position))
    require(translated['id'] not in {row['id'] for row in references}, 'IDENTITY', 'Translated identity collides')
    world = [row for i, row in enumerate(references) if i != index] + [translated]
    validate_rows(world); validate_canvas(world, image)
    return world, {'operation': 'translation', 'source_reference_id': reference['id'],
                   'source_reference_sha256': reference['record_sha256'], 'axis': axis,
                   'position': w(position), 'distance': w(abs(position - base[axis])),
                   'translated_reference': translated}


def checked_extrema(image, references, image_record, radius, proof_cache):
    outputs = {}
    for direction, (delta, state) in zip(('lower', 'upper'), extrema_states(image_record, radius)):
        world, edit = attained_world(image, references, state, radius)
        cache_key = digest({'subject_sha256': subject(image), 'references': world})
        if cache_key not in proof_cache:
            measured, proof, timing = checked_ranks(image, world)
            proof_cache[cache_key] = {'measurement': measured, 'proof': proof, 'timing': timing,
                                    'subject_sha256': subject(image), 'reference_sha256': digest(world)}
        checked = proof_cache[cache_key]
        require(q(checked['measurement']['delta']) == delta, 'MATCHING', 'Cell graph differs from attained geometric world')
        outputs[direction] = {'delta': w(delta), 'state_id': None if state is None else state['id'],
                              'edit': edit, 'proof_key': cache_key}
    return outputs


def minimum_affected(nominal, downward):
    """Exact image count when each per-image minimum is attained."""
    nominal = Fraction(nominal)
    if nominal <= 0:
        return {'minimum_images': 0, 'image_ids': [], 'witness_total': w(nominal),
                'reason': 'Nominal world already excludes strict improvement.'}
    ordered = sorted(downward.items(), key=lambda item: (-item[1], item[0]))
    require(all(value >= 0 for _, value in ordered), 'BOUND', 'Negative adverse improvement')
    damage = Fraction(0); selected = []
    for iid, value in ordered:
        previous = damage
        if value == 0:
            continue
        damage += value; selected.append(iid)
        if damage >= nominal:
            return {'minimum_images': len(selected), 'image_ids': selected,
                    'witness_total': w(nominal - damage), 'one_fewer_maximum_damage': w(previous)}
    return {'minimum_images': None, 'image_ids': None, 'witness_total': None,
            'maximum_damage': w(damage), 'reason': 'No excluding world in the declared radius family.'}


def primary_critical_radius(records, maximum=64):
    """Earliest lower-total crossing, preserving open-cell activation."""
    maximum = Fraction(maximum)
    require(records and 0 <= maximum <= 64 and all(
        row.get('exhaustive_for_declared_axis_family') is True and iid == row.get('image_id')
        for iid, row in records.items()), 'INPUT', 'Complete image records and a declared nonnegative radius required')
    best = {iid: q(row['nominal']['delta']) for iid, row in records.items()}
    nominal = sum(best.values(), Fraction(0))
    if nominal <= 0:
        return {'radius_infimum': w(Fraction(0)), 'attained': True, 'witness_radius': w(Fraction(0)),
                'lower_total_at_infimum': w(nominal), 'reason': 'Nominal world already excludes improvement.'}
    events = {}
    for iid, row in records.items():
        for state in row['states']:
            radius = q(state['radius_infimum']); delta = q(state['measurement']['delta'])
            if delta >= best[iid] or radius > maximum or (radius == maximum and not state['infimum_attained']):
                continue
            events.setdefault(radius, []).append((iid, delta, state['infimum_attained']))
    points = sorted(events)
    for index, radius in enumerate(points):
        before = sum(best.values(), Fraction(0))
        for iid, delta, attained in events[radius]:
            if attained:
                best[iid] = min(best[iid], delta)
        at = sum(best.values(), Fraction(0))
        if at <= 0:
            return {'radius_infimum': w(radius), 'attained': True, 'witness_radius': w(radius),
                    'lower_total_before_infimum': w(before), 'lower_total_at_infimum': w(at)}
        for iid, delta, attained in events[radius]:
            if not attained:
                best[iid] = min(best[iid], delta)
        after = sum(best.values(), Fraction(0))
        if after <= 0:
            next_radius = min(maximum, points[index + 1] if index + 1 < len(points) else maximum)
            require(radius < next_radius, 'RADIUS', 'No admitted radius above open infimum')
            return {'radius_infimum': w(radius), 'attained': False,
                    'witness_radius': w((radius + next_radius) / 2),
                    'lower_total_before_infimum': w(before), 'lower_total_at_infimum': w(at),
                    'right_limit_lower_total': w(after)}
    return {'radius_infimum': None, 'attained': None, 'witness_radius': None,
            'maximum_radius': w(maximum), 'lower_total_at_maximum': w(sum(best.values(), Fraction(0))),
            'reason': 'No excluding world up to the declared maximum radius.'}
