"""Bounded spatial refinement with complete covering trees and attained worlds."""
from fractions import Fraction
from pathlib import Path
import sys
import time

from planar_math import domain, edge_envelope, points, rank_enclosure, split

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'research/public-predictions/0.1.0'))
from admission import digest, require
from compare_math import (ROLES, checked_ranks, flow_rank, iou, linked, q, subject, validate_canvas,
                          validate_image, validate_rows, w)
from geometric_worlds import coordinates, record

MAX_REGIONS = 2048
MAX_DEPTH = 24
RADII = (0, 1, 2, 4, 8, 16, 32, 64)


def prepare(image, references):
    tick = time.perf_counter(); validate_image(image); validate_rows(references); validate_canvas(references, image)
    require(linked(image), 'INPUT', 'Unavailable reference is not an empty answer')
    detections = {row['id']: row for role in ROLES for row in image[role]['value']}
    edges = {(did, ref['id']) for did, detection in detections.items() for ref in references
             if iou(detection, ref) >= Fraction(1, 2)}
    reference_ids = {row['id'] for row in references}; sentinel = 'planar:abstract-new-reference'
    require(sentinel not in reference_ids, 'IDENTITY', 'Abstract vertex identity collides')
    left_sets = [{row['id'] for row in image[role]['value']} for role in ROLES]
    counts = list(map(len, left_sets))
    original_ranks = [flow_rank(left, reference_ids, {(d, r) for d, r in edges if d in left}) for left in left_sets]
    bases = []; matching_calls = 2
    for index, reference in enumerate(references):
        right = reference_ids - {reference['id']}; ranks, augmentation = [], []
        for left in left_sets:
            base_edges = {(d, r) for d, r in edges if d in left and r in right}
            rank = flow_rank(left, right, base_edges); matching_calls += 1; ranks.append(rank)
            augmentable = []
            for did in sorted(left):
                after = flow_rank(left, right | {sentinel}, base_edges | {(did, sentinel)}); matching_calls += 1
                require(after in (rank, rank + 1), 'MATCHING', 'Single reference changed rank by more than one')
                if after > rank:
                    augmentable.append(did)
            augmentation.append(augmentable)
        bases.append({'reference_index': index, 'reference_id': reference['id'], 'ranks': ranks,
                      'augmentable_a': augmentation[0], 'augmentable_b': augmentation[1],
                      'base_delta': counts[0] - counts[1] + 2 * (ranks[1] - ranks[0])})
    return {'image_id': image['id'], 'subject_sha256': subject(image), 'reference_sha256': digest(references),
            'nominal_delta': counts[0] - counts[1] + 2 * (original_ranks[1] - original_ranks[0]),
            'nominal_ranks': original_ranks, 'bases': bases, 'matching_calls': matching_calls,
            'seconds': time.perf_counter() - tick}


def moved_world(image, references, index, position, radius):
    if index is None:
        return references, {'operation': 'none'}
    source = references[index]; base = coordinates(source); x, y = map(Fraction, position)
    dx, dy = x - base[0], y - base[1]
    require(max(abs(dx), abs(dy)) <= radius, 'RADIUS', 'Candidate exceeds displacement radius')
    translated = record((x, y, x + base[2] - base[0], y + base[3] - base[1]))
    require(translated['id'] not in {row['id'] for row in references}, 'IDENTITY', 'Translated identity collides')
    world = [row for i, row in enumerate(references) if i != index] + [translated]
    validate_rows(world); validate_canvas(world, image)
    return world, {'operation': 'translation_2d', 'source_reference_id': source['id'],
                   'source_reference_sha256': source['record_sha256'], 'reference_index': index,
                   'position': [w(x), w(y)], 'offset': [w(dx), w(dy)],
                   'linf_distance': w(max(abs(dx), abs(dy))), 'translated_reference': translated}


def seed_positions(image, references, radius, axis_witnesses):
    lookup = {row['id']: index for index, row in enumerate(references)}; found = []
    for witness in axis_witnesses or []:
        edit = witness['edit']
        if edit['operation'] == 'none':
            continue
        require(edit['operation'] == 'translation' and edit['source_reference_id'] in lookup,
                'SEED', 'Axis seed is not an existing-reference translation')
        index = lookup[edit['source_reference_id']]; source = references[index]
        base = coordinates(source); changed = coordinates(edit['translated_reference'])
        require(edit['source_reference_sha256'] == source['record_sha256'] and
                changed[2] - changed[0] == base[2] - base[0] and changed[3] - changed[1] == base[3] - base[1],
                'SEED', 'Axis seed changed source or shape')
        moved_world(image, references, index, changed[:2], radius)
        found.append((index, changed[:2]))
    return found


def search(image, references, basis, radius, axis_witnesses=None, native_cache=None,
           maximum_regions=MAX_REGIONS, maximum_depth=MAX_DEPTH):
    tick = time.perf_counter(); radius = Fraction(radius)
    require(0 <= radius <= 64 and basis['subject_sha256'] == subject(image)
            and basis['reference_sha256'] == digest(references), 'BINDING', 'Wrong radius or preparation context')
    require(type(maximum_regions) is int and len(references) <= maximum_regions <= MAX_REGIONS
            and type(maximum_depth) is int and 0 <= maximum_depth <= MAX_DEPTH,
            'LIMIT', 'Invalid or enlarged search limit')
    native_cache = {} if native_cache is None else native_cache
    detections = {row['id']: row for role in ROLES for row in image[role]['value']}
    best = {'lower': {'delta': basis['nominal_delta'], 'reference_index': None, 'position': None},
            'upper': {'delta': basis['nominal_delta'], 'reference_index': None, 'position': None}}
    point_cache = {}; envelope_calls = 0

    def candidate(index, position):
        position = tuple(map(Fraction, position)); key = (index, position)
        if key in point_cache:
            return point_cache[key]
        base = basis['bases'][index]; geometry = coordinates(references[index])
        box = record((position[0], position[1], position[0] + geometry[2] - geometry[0],
                      position[1] + geometry[3] - geometry[1]))
        augment_a, augment_b = set(base['augmentable_a']), set(base['augmentable_b'])
        neighbors = {did for did in augment_a | augment_b if iou(detections[did], box) >= Fraction(1, 2)}
        delta = base['base_delta'] + 2 * (int(bool(neighbors & augment_b)) - int(bool(neighbors & augment_a)))
        point_cache[key] = delta
        if delta < best['lower']['delta']:
            best['lower'] = {'delta': delta, 'reference_index': index, 'position': position}
        if delta > best['upper']['delta']:
            best['upper'] = {'delta': delta, 'reference_index': index, 'position': position}
        return delta

    for index, position in seed_positions(image, references, radius, axis_witnesses):
        candidate(index, position)

    nodes = []; leaves = set()

    def evaluate(index, path, region):
        nonlocal envelope_calls
        base = basis['bases'][index]; geometry = coordinates(references[index])
        augment_a, augment_b = set(base['augmentable_a']), set(base['augmentable_b'])
        must, may = set(), set()
        for did in sorted(augment_a | augment_b):
            envelope = edge_envelope(geometry, coordinates(detections[did]), region); envelope_calls += 1
            if envelope['must']:
                must.add(did)
            if envelope['may']:
                may.add(did)
        bounds, pairs = rank_enclosure(base['base_delta'], must, may, augment_a, augment_b)
        for position in points(region, geometry[:2]):
            value = candidate(index, position)
            require(bounds[0] <= value <= bounds[1], 'BOUND', 'Attained point violates geometric envelope')
        node = {'reference_index': index, 'path': path, 'domain': [w(value) for value in region],
                'bounds': list(bounds), 'increment_pairs': [list(pair) for pair in pairs], 'children': None,
                'stop_reason': None}
        nodes.append(node); leaves.add(len(nodes) - 1)
        return len(nodes) - 1

    roots = []
    for index, source in enumerate(references):
        roots.append(evaluate(index, '', domain(coordinates(source), radius, image['width'], image['height'])))

    def gap(node):
        return max(best['lower']['delta'] - node['bounds'][0], node['bounds'][1] - best['upper']['delta'], 0)

    while True:
        active = []
        for ni in sorted(leaves):
            node = nodes[ni]
            if not gap(node):
                node['stop_reason'] = 'covered_by_attained_extrema'
            elif len(node['path']) >= maximum_depth:
                node['stop_reason'] = 'depth_limit'
            else:
                active.append(ni)
        if not active:
            break
        if len(nodes) + 2 > maximum_regions:
            for ni in active:
                nodes[ni]['stop_reason'] = 'region_limit'
            break
        selected = min(active, key=lambda ni: (-gap(nodes[ni]), nodes[ni]['reference_index'], nodes[ni]['path']))
        node = nodes[selected]; region = tuple(map(q, node['domain']))
        require(region[0] < region[2] or region[1] < region[3], 'BOUND', 'Point domain cannot retain a matching gap')
        axis, first, second = split(region)
        left = evaluate(node['reference_index'], node['path'] + '0', first)
        right = evaluate(node['reference_index'], node['path'] + '1', second)
        node['children'] = [left, right]; node['split_axis'] = axis; node['stop_reason'] = 'split'
        leaves.remove(selected)
    universal = [min([basis['nominal_delta']] + [nodes[ni]['bounds'][0] for ni in leaves]),
                 max([basis['nominal_delta']] + [nodes[ni]['bounds'][1] for ni in leaves])]
    attained = [best['lower']['delta'], best['upper']['delta']]
    proofs, witnesses, new_proofs, reused_proofs = {}, {}, [], []
    for direction in ('lower', 'upper'):
        found = best[direction]
        world, edit = moved_world(image, references, found['reference_index'], found['position'], radius)
        key = digest({'subject_sha256': subject(image), 'references': world})
        if key not in native_cache:
            measured, proof, timing = checked_ranks(image, world)
            native_cache[key] = {'measurement': measured, 'proof': proof, 'timing': timing,
                                 'subject_sha256': subject(image), 'reference_sha256': digest(world)}
            new_proofs.append(key)
        else:
            reused_proofs.append(key)
        require(q(native_cache[key]['measurement']['delta']) == found['delta'], 'MATCHING', 'Attained native world differs')
        proofs[key] = native_cache[key]
        witnesses[direction] = {'delta': w(Fraction(found['delta'])), 'edit': edit, 'proof_key': key}
    unresolved = [ni for ni in sorted(leaves) if gap(nodes[ni])]
    require(universal[0] <= attained[0] <= attained[1] <= universal[1], 'BOUND', 'Final enclosure excludes attained values')
    return {'image_id': image['id'], 'subject_sha256': subject(image), 'reference_sha256': digest(references),
            'basis_sha256': digest(basis), 'radius': w(radius), 'nominal_delta': basis['nominal_delta'],
            'roots': roots, 'nodes': nodes, 'leaf_indices': sorted(leaves), 'unresolved_leaf_indices': unresolved,
            'universal_bounds': [w(Fraction(value)) for value in universal],
            'attained_bounds': [w(Fraction(value)) for value in attained], 'exact_extrema': universal == attained,
            'state': 'exact_extrema' if universal == attained else 'bounded_with_gap',
            'limits': {'maximum_regions': maximum_regions, 'maximum_depth': maximum_depth},
            'stopped_limits': sorted({nodes[ni]['stop_reason'] for ni in unresolved}),
            'witnesses': witnesses, 'proofs': proofs, 'new_native_proofs': new_proofs,
            'reused_native_proofs': reused_proofs, 'evaluated_points': len(point_cache),
            'edge_envelope_calls': envelope_calls, 'seconds': time.perf_counter() - tick}
