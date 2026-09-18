"""Identical finite operands for conventional matching and native checking."""
from fractions import Fraction

from operating_sources import ROLES, digest, q, require, w
from compare_math import checked_ranks, conventional_measure, open_interval
from geometric_worlds import alter
from refine import graph_edit_bounds
from timing_bounds import optional_bounds

FAMILIES = ('exact_projection', 'one_edit_per_image', 'one_edit_global',
            'current_strict', 'current_partial', 'union_strict', 'union_partial')
MAX_PROOFS = 20000


def world_banks(original, edit_record, temporal):
    worlds = {}; edit_ids = []; deletions = []
    def keep(references):
        key = digest(references); worlds.setdefault(key, references); return key
    original_key = keep(original)
    for removed in [None]+[row['id'] for row in original]:
        key = keep([row for row in original if row['id'] != removed])
        deletions.append({'removed_reference': removed, 'world': key}); edit_ids.append(key)
    require(edit_record['search_state'] == 'complete', 'Inherited edit witness search incomplete')
    for direction in ('lower', 'upper'):
        record = edit_record['search']['witnesses'][direction]
        expected = alter(original, record['edit'])
        require(record['altered_references'] == expected, 'Inherited edit geometry differs')
        edit_ids.append(keep(expected))
    known = temporal['known_references']; known_key = keep(known); banks = {}
    for scope in ('current', 'union'):
        unknown = temporal[scope+'_unknown_instances']
        if unknown is None:
            banks[scope] = {'state': 'input_blocked', 'reason': 'preceding_census_unavailable'}; continue
        allowed = {'timing-unknown:'+identity for identity in unknown}; selected = {known_key}
        for proof in temporal['proofs'].values():
            references = proof['references']
            if references[:len(known)] != known:
                continue
            added = references[len(known):]; ids = [row['id'] for row in added]
            if len(ids) == len(set(ids)) and set(ids) <= allowed:
                selected.add(keep(references))
        banks[scope] = {'state': 'available', 'unknown_ids': unknown, 'unknown_count': len(unknown),
                        'worlds': sorted(selected)}
    return {'worlds': worlds, 'original_world': original_key, 'known_world': known_key,
            'deletions': deletions, 'edit_worlds': sorted(set(edit_ids)), 'temporal': banks}


def measured_world(image, references, cache):
    key = digest({'image': image, 'references': references})
    if key not in cache:
        require(len(cache) < MAX_PROOFS, 'Native world certificate limit')
        conventional = conventional_measure(image, references); native, proof, timing = checked_ranks(image, references)
        require(conventional == native, 'Conventional and native matching disagree')
        cache[key] = {'image': image, 'references': references, 'measurement': conventional,
                      'proof': proof, 'native_timing': timing}
    return key


def analyze_state(image, bank, cache):
    require(all(image[role]['state'] == 'observed' for role in ROLES), 'Unavailable prediction cannot be filtered empty')
    keys = {world: measured_world(image, references, cache) for world, references in bank['worlds'].items()}
    nominal_key = keys[bank['original_world']]; known_key = keys[bank['known_world']]
    nominal = cache[nominal_key]['measurement']; known = cache[known_key]['measurement']
    deletion_measurements = [cache[keys[row['world']]]['measurement'] for row in bank['deletions']]
    edit_bounds = graph_edit_bounds(image, deletion_measurements)
    def contract(bounds, candidates):
        low = min(candidates, key=lambda key: (q(cache[key]['measurement']['delta']), key))
        high = min(candidates, key=lambda key: (-q(cache[key]['measurement']['delta']), key))
        attained = [cache[key]['measurement']['delta'] for key in (low, high)]
        require(bounds[0] <= q(attained[0]) <= q(attained[1]) <= bounds[1], 'World bank violates its universal bound')
        return {'state': 'available', 'bounds': list(map(w, bounds)), 'attained': attained, 'proof_keys': [low, high]}
    center = q(nominal['delta']); families = {'exact_projection': contract((center, center), [nominal_key])}
    families['one_edit_per_image'] = contract(edit_bounds, [keys[key] for key in bank['edit_worlds']])
    families['one_edit_global'] = families['one_edit_per_image']
    for scope in ('current', 'union'):
        value = bank['temporal'][scope]
        if value['state'] == 'input_blocked':
            blocked = {'state': 'input_blocked', 'reason': value['reason'], 'bounds': None, 'attained': None, 'proof_keys': None}
            families[scope+'_strict'] = blocked; families[scope+'_partial'] = blocked; continue
        count = value['unknown_count']; bounds = optional_bounds(image, known['ranks'], count)
        families[scope+'_partial'] = contract(bounds, [keys[key] for key in value['worlds']])
        if count:
            families[scope+'_strict'] = {'state': 'input_blocked', 'reason': 'motion_unavailable_for_census_instances',
                'bounds': None, 'attained': None, 'proof_keys': None}
        else:
            center = q(known['delta']); families[scope+'_strict'] = contract((center, center), [known_key])
    counts = [len(image[role]['value']) for role in ROLES]; reference_count = len(bank['worlds'][bank['original_world']])
    return {'families': families, 'world_proof_keys': keys, 'nominal_proof_key': nominal_key, 'known_proof_key': known_key,
            'nominal': nominal, 'nominal_reference_count': reference_count, 'prediction_counts': counts,
            'nominal_fp': [count-rank for count, rank in zip(counts, nominal['ranks'])],
            'nominal_fn': [reference_count-rank for rank in nominal['ranks']]}


def aggregate(case, family, state_keys, states):
    require(family in FAMILIES and len(case['images']) == len(state_keys) and case['images'], 'Invalid case allocation')
    components = [states[key] for key in state_keys]
    require([row['image']['id'] for row in components] == case['images'], 'Case membership substituted')
    values = [row['analysis']['families'][family] for row in components]
    blocked = [iid for iid, value in zip(case['images'], values) if value['state'] == 'input_blocked']
    base = {'case_id': case['id'], 'group': case['group'], 'family': family, 'membership': case['images'],
            'state_keys': state_keys, 'allocated_images': len(state_keys), 'blocked_images': blocked}
    if blocked:
        return {**base, 'state': 'input_blocked', 'decision': 'input_blocked', 'bounds': None,
                'attained': None, 'evidence': None, 'world_proof_keys': None}
    size = len(values); bounds = []; attained = []; worlds = []
    for endpoint in (0, 1):
        if family == 'one_edit_global':
            centers = [q(row['analysis']['nominal']['delta']) for row in components]; total = sum(centers, Fraction(0))
            difference = [q(value['bounds'][endpoint])-center for value, center in zip(values, centers)]
            achieved = [q(value['attained'][endpoint])-center for value, center in zip(values, centers)]
            selection = min(range(size), key=lambda i: (achieved[i] if endpoint == 0 else -achieved[i], i))
            bounds.append((total+(min(difference) if endpoint == 0 else max(difference)))/size)
            attained.append((total+achieved[selection])/size)
            worlds.append([value['proof_keys'][endpoint] if index == selection else components[index]['analysis']['nominal_proof_key']
                           for index, value in enumerate(values)])
        else:
            bounds.append(sum((q(value['bounds'][endpoint]) for value in values), Fraction(0))/size)
            attained.append(sum((q(value['attained'][endpoint]) for value in values), Fraction(0))/size)
            worlds.append([value['proof_keys'][endpoint] for value in values])
    decision = 'supported' if bounds[0] > 0 else 'excluded' if bounds[1] <= 0 else 'unresolved'
    evidence = 'universal_bound' if decision != 'unresolved' else 'opposite_worlds' if attained[0] <= 0 < attained[1] else 'bound_gap'
    return {**base, 'state': 'available', 'bounds': list(map(w, bounds)), 'attained': list(map(w, attained)),
            'decision': decision, 'evidence': evidence, 'world_proof_keys': worlds}
