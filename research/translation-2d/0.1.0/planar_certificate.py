"""Separate geometric, matching and covering-tree checks for planar bounds.

No calls to the producer's overlap envelope, rank-pair enumerator, flow matcher,
subdivision search or world constructor are used here.
"""
from fractions import Fraction
from itertools import product
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'research/reference-translation/0.1.0'))
from axis_certificate import exact_iou, maximum_matching
sys.path.insert(0, str(ROOT / 'research/public-predictions/0.1.0'))
from compare_math import (ROLES, digest, graph, linked, q, require, subject, validate_canvas,
                          validate_image, validate_rows, w)
from tools.perception_revision import checker


def geometry(row):
    return tuple(q(value) for value in row['xyxy'])


def overlap_limits(low, high, extent, left, right):
    """Trapezoid endpoints and peak plateau, separate from slope enumeration."""
    low, high, extent, left, right = map(Fraction, (low, high, extent, left, right))
    require(low <= high and extent > 0 and left < right, 'GEOMETRY', 'Invalid overlap domain')
    def value(position):
        return max(Fraction(0), min(position + extent, right) - max(position, left))
    ends = [value(low), value(high)]
    plateau = sorted((left, right - extent))
    peak = min(extent, right - left) if max(low, plateau[0]) <= min(high, plateau[1]) else max(ends)
    return min(ends), peak


def neighbors(base, detections, region):
    x1, y1, x2, y2 = map(Fraction, region); mandatory, possible = set(), set()
    for did, detection in detections.items():
        first = overlap_limits(x1, x2, base[2] - base[0], detection[0], detection[2])
        second = overlap_limits(y1, y2, base[3] - base[1], detection[1], detection[3])
        area = (base[2] - base[0]) * (base[3] - base[1])
        other_area = (detection[2] - detection[0]) * (detection[3] - detection[1])
        if 3 * first[0] * second[0] >= area + other_area:
            mandatory.add(did)
        if 3 * first[1] * second[1] >= area + other_area:
            possible.add(did)
    return mandatory, possible


def relaxed_pairs(mandatory, possible, a, b):
    """Construct a neighbor-set witness for each possible pair of rank hits."""
    require(mandatory <= possible, 'NEIGHBORS', 'Mandatory edge cannot be impossible')
    result = []
    for first, second in product((0, 1), repeat=2):
        sets = [a, b]; flags = [first, second]; witness = set(mandatory)
        admissible = set(possible)
        for flag, group in zip(flags, sets):
            if not flag:
                admissible -= group
        if not witness <= admissible:
            continue
        for flag, group in zip(flags, sets):
            if flag and not witness & group:
                choices = sorted(admissible & group)
                if choices:
                    witness.add(choices[0])
        if [int(bool(witness & group)) for group in sets] == flags:
            result.append([first, second])
    require(bool(result), 'NEIGHBORS', 'No possible rank pair')
    return result


def independent_measure(image, references):
    ranks = []
    for role in ROLES:
        adjacency = {row['id']: {ref['id'] for ref in references
                     if exact_iou(geometry(row), geometry(ref)) >= Fraction(1, 2)}
                     for row in image[role]['value']}
        ranks.append(maximum_matching(adjacency))
    return {'ranks': ranks, 'delta': w(Fraction(len(image['output_a']['value']) - len(image['output_b']['value'])
                                              + 2 * (ranks[1] - ranks[0])))}


def check_basis(image, references, basis):
    validate_image(image); validate_rows(references); validate_canvas(references, image)
    require(linked(image), 'INPUT', 'Unavailable input cannot supply a planar family')
    require(basis['image_id'] == image['id'] and basis['subject_sha256'] == subject(image)
            and basis['reference_sha256'] == digest(references), 'BINDING', 'Wrong preparation subject')
    nominal = independent_measure(image, references)
    require(basis['nominal_ranks'] == nominal['ranks'] and basis['nominal_delta'] == q(nominal['delta']),
            'MATCHING', 'Incorrect nominal matching')
    require(len(basis['bases']) == len(references), 'ALLOCATION', 'Missing deletion base')
    expected_bases = []
    for index, removed in enumerate(references):
        remaining = [row for i, row in enumerate(references) if i != index]
        ranks, augmentable = [], []
        for role in ROLES:
            adjacency = {row['id']: {ref['id'] for ref in remaining
                         if exact_iou(geometry(row), geometry(ref)) >= Fraction(1, 2)}
                         for row in image[role]['value']}
            rank = maximum_matching(adjacency); ranks.append(rank); eligible = []
            sentinel = 'certificate:abstract-new-reference'
            require(sentinel not in {row['id'] for row in references}, 'IDENTITY', 'Abstract identity collision')
            for did in sorted(adjacency):
                changed = {key: value | ({sentinel} if key == did else set()) for key, value in adjacency.items()}
                after = maximum_matching(changed)
                require(after in (rank, rank + 1), 'MATCHING', 'Invalid one-vertex augmentation')
                if after == rank + 1:
                    eligible.append(did)
            augmentable.append(eligible)
        expected_bases.append({'reference_index': index, 'reference_id': removed['id'], 'ranks': ranks,
                               'augmentable_a': augmentable[0], 'augmentable_b': augmentable[1],
                               'base_delta': len(image['output_a']['value']) - len(image['output_b']['value'])
                                             + 2 * (ranks[1] - ranks[0])})
    require(basis['bases'] == expected_bases, 'MATCHING', 'Augmentability or deletion matching differs')
    expected_calls = 2 + len(references) * (2 + sum(len(image[role]['value']) for role in ROLES))
    require(basis['matching_calls'] == expected_calls, 'ACCOUNTING', 'Preparation call count differs')
    return {'subject_sha256': subject(image), 'reference_sha256': digest(references),
            'basis_sha256': digest(basis), 'bases': expected_bases, 'nominal': q(nominal['delta']),
            'native_payloads': {}}


def check_world(image, references, checked, witness, radius, proofs):
    edit = witness['edit']
    if edit['operation'] == 'none':
        require(edit == {'operation': 'none'}, 'EDIT', 'Unexpected no-edit contents')
        world = references
    else:
        require(set(edit) == {'operation', 'source_reference_id', 'source_reference_sha256', 'reference_index',
                              'position', 'offset', 'linf_distance', 'translated_reference'}
                and edit['operation'] == 'translation_2d', 'EDIT', 'Unknown planar edit')
        index = edit['reference_index']
        require(type(index) is int and 0 <= index < len(references), 'EDIT', 'Unknown reference index')
        source = references[index]; base = geometry(source); row = edit['translated_reference']; box = geometry(row)
        require(edit['source_reference_id'] == source['id']
                and edit['source_reference_sha256'] == source['record_sha256'], 'EDIT', 'Wrong source reference')
        require(box[2] - box[0] == base[2] - base[0] and box[3] - box[1] == base[3] - base[1],
                'EDIT', 'Reference shape changed')
        offset = (box[0] - base[0], box[1] - base[1]); distance = max(map(abs, offset))
        require(tuple(map(q, edit['position'])) == box[:2] and tuple(map(q, edit['offset'])) == offset,
                'EDIT', 'Position or offset differs')
        require(q(edit['linf_distance']) == distance <= radius, 'RADIUS', 'Translation exceeds radius')
        require(row['id'] not in {ref['id'] for ref in references}, 'IDENTITY', 'Moved reference identity collides')
        world = [ref for i, ref in enumerate(references) if i != index] + [row]
    validate_rows(world); validate_canvas(world, image)
    require(len(world) == len(references), 'EDIT', 'Reference cardinality changed')
    key = digest({'subject_sha256': subject(image), 'references': world})
    require(witness['proof_key'] == key and key in proofs, 'PROOF', 'Wrong world proof identity')
    proof = proofs[key]; measured = independent_measure(image, world)
    require(proof['subject_sha256'] == subject(image) and proof['reference_sha256'] == digest(world),
            'PROOF', 'Proof context differs')
    require(proof['measurement'] == measured and q(witness['delta']) == q(measured['delta']),
            'MATCHING', 'Claimed world is not attained')
    native = graph(image, world)
    require(proof['proof']['graph_sha256'] == digest(native), 'PROOF', 'Wrong native graph')
    if key in checked['native_payloads']:
        require(checked['native_payloads'][key] == digest(proof), 'PROOF', 'Checked proof bytes changed')
    else:
        checker.check(native, proof['proof']['payload'])
        checked['native_payloads'][key] = digest(proof)
    return q(measured['delta'])


def check_search(image, references, checked, result, radius):
    radius = Fraction(radius)
    require(0 <= radius <= 64 and q(result['radius']) == radius, 'RADIUS', 'Wrong search radius')
    require(result['image_id'] == image['id'] and result['subject_sha256'] == checked['subject_sha256'] == subject(image)
            and result['reference_sha256'] == checked['reference_sha256'] == digest(references)
            and result['basis_sha256'] == checked['basis_sha256'], 'BINDING', 'Search context differs')
    require(result['nominal_delta'] == checked['nominal'], 'MATCHING', 'Nominal delta differs')
    limits = result['limits']; nodes = result['nodes']
    require(set(limits) == {'maximum_regions', 'maximum_depth'}
            and type(limits['maximum_regions']) is int and len(references) <= limits['maximum_regions'] <= 2048
            and type(limits['maximum_depth']) is int and 0 <= limits['maximum_depth'] <= 24
            and len(nodes) <= limits['maximum_regions'], 'LIMIT', 'Search work limit exceeded')
    require(len(result['roots']) == len(references), 'COVERAGE', 'Missing reference root')
    detections = {row['id']: geometry(row) for role in ROLES for row in image[role]['value']}
    visited = set(); leaves = set()

    def visit(ni, index, path, expected_region):
        require(type(ni) is int and 0 <= ni < len(nodes) and ni not in visited, 'COVERAGE', 'Repeated or absent region')
        visited.add(ni); node = nodes[ni]
        require(node['reference_index'] == index and node['path'] == path
                and tuple(map(q, node['domain'])) == expected_region, 'COVERAGE', 'Region identity or coverage differs')
        require(len(path) <= limits['maximum_depth'], 'LIMIT', 'Region exceeds depth limit')
        base = checked['bases'][index]; a, b = set(base['augmentable_a']), set(base['augmentable_b'])
        mandatory, possible = neighbors(geometry(references[index]), {did: detections[did] for did in a | b}, expected_region)
        pairs = relaxed_pairs(mandatory, possible, a, b)
        values = [base['base_delta'] + 2 * (second - first) for first, second in pairs]
        require(node['increment_pairs'] == pairs and node['bounds'] == [min(values), max(values)],
                'BOUND', 'Region relaxed bound differs')
        if node['children'] is None:
            leaves.add(ni)
            require('split_axis' not in node, 'COVERAGE', 'Leaf claims a split')
            return
        children = node['children']
        require(type(children) is list and len(children) == 2 and node['stop_reason'] == 'split',
                'COVERAGE', 'Split requires both retained children')
        x1, y1, x2, y2 = expected_region
        require(x1 < x2 or y1 < y2, 'COVERAGE', 'Degenerate region cannot split')
        axis = 0 if x2 - x1 >= y2 - y1 else 1
        require(node['split_axis'] == axis, 'COVERAGE', 'Wrong deterministic split axis')
        if axis == 0:
            mid = (x1 + x2) / 2; regions = [(x1, y1, mid, y2), (mid, y1, x2, y2)]
        else:
            mid = (y1 + y2) / 2; regions = [(x1, y1, x2, mid), (x1, mid, x2, y2)]
        for child, digit, region in zip(children, ('0', '1'), regions):
            require(child > ni, 'COVERAGE', 'Child must follow its parent')
            visit(child, index, path + digit, region)

    for index, root in enumerate(result['roots']):
        box = geometry(references[index]); width, height = box[2] - box[0], box[3] - box[1]
        legal = (max(Fraction(0), box[0] - radius), max(Fraction(0), box[1] - radius),
                 min(Fraction(image['width']) - width, box[0] + radius),
                 min(Fraction(image['height']) - height, box[1] + radius))
        visit(root, index, '', legal)
    require(visited == set(range(len(nodes))) and result['leaf_indices'] == sorted(leaves),
            'COVERAGE', 'Orphan region or omitted leaf')
    universal = [min([checked['nominal']] + [nodes[ni]['bounds'][0] for ni in leaves]),
                 max([checked['nominal']] + [nodes[ni]['bounds'][1] for ni in leaves])]
    require(set(result['witnesses']) == {'lower', 'upper'}, 'PROOF', 'Missing attained extremum')
    attained = [check_world(image, references, checked, result['witnesses'][direction], radius, result['proofs'])
                for direction in ('lower', 'upper')]
    require(set(result['proofs']) == {row['proof_key'] for row in result['witnesses'].values()},
            'PROOF', 'Extra unchecked proof')
    require(universal[0] <= attained[0] <= checked['nominal'] <= attained[1] <= universal[1],
            'BOUND', 'Attained and universal bounds disagree')
    require(list(map(q, result['universal_bounds'])) == universal and list(map(q, result['attained_bounds'])) == attained,
            'BOUND', 'Reported final interval differs')
    exact = universal == attained
    require(result['exact_extrema'] is exact and result['state'] == ('exact_extrema' if exact else 'bounded_with_gap'),
            'BOUND', 'Bound gap misrepresented as exact')
    unresolved = []
    for ni in sorted(leaves):
        node = nodes[ni]; gap = node['bounds'][0] < attained[0] or node['bounds'][1] > attained[1]
        if gap:
            unresolved.append(ni)
            reason = 'depth_limit' if len(node['path']) >= limits['maximum_depth'] else 'region_limit'
            require(node['stop_reason'] == reason, 'LIMIT', 'Wrong retained work-limit reason')
            if reason == 'region_limit':
                require(len(nodes) + 2 > limits['maximum_regions'], 'LIMIT', 'Search stopped before its region limit')
        else:
            require(node['stop_reason'] == 'covered_by_attained_extrema', 'BOUND', 'Covered leaf mislabeled')
    require(result['unresolved_leaf_indices'] == unresolved
            and result['stopped_limits'] == sorted({nodes[ni]['stop_reason'] for ni in unresolved}),
            'COVERAGE', 'Unresolved region omitted')
    for key in result['new_native_proofs'] + result['reused_native_proofs']:
        require(key in result['proofs'], 'ACCOUNTING', 'Unbound proof cost entry')
    require(len(result['new_native_proofs']) == len(set(result['new_native_proofs']))
            and len(result['new_native_proofs']) + len(result['reused_native_proofs']) == 2,
            'ACCOUNTING', 'Proof operation count differs')
    return {'universal': universal, 'attained': attained, 'nominal': checked['nominal'],
            'exact': exact, 'regions': len(nodes), 'unresolved_regions': len(unresolved)}
