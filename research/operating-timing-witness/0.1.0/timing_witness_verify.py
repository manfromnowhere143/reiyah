"""Separate world reconstruction, matching, pool and complete-case checks."""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
import time

from timing_witness import ROOT, PARTIAL, bound_read, digest, file_binding, put, q, read, require, sources, w
from operating_certificate import check_case, verify_proof
from compare_math import ROLES, validate_canvas, validate_image, validate_rows
from witness_verify import independent_pool, check_search
from timing_certificate import expected_world, independent_bounds, matching
from axis_certificate import exact_iou


def independent_context(state, bank, temporal, family):
    validate_image(state['image'])
    require(family in PARTIAL and state['analysis']['families'][family]['state'] == 'available', 'Absent partial input')
    scope = family.split('_')[0]; census = bank['temporal'][scope]
    unknown = temporal[scope+'_unknown_instances']; known = temporal['known_references']
    require(type(unknown) is list and all(type(x) is str for x in unknown)
            and len(set(unknown)) == len(unknown) and sorted(unknown) == unknown, 'Unavailable or repeated census')
    require(census['state'] == 'available' and census['unknown_ids'] == unknown
            and census['unknown_count'] == len(unknown), 'Wrong census/budget')
    require(bank['worlds'][bank['known_world']] == known, 'Known world substituted')
    validate_rows(known); validate_canvas(known, state['image'])
    require(not ({r['id'] for r in known} & {'timing-unknown:'+u for u in unknown}), 'Known/unknown identity reuse')
    bases = {tuple(map(q, r)) for r in temporal['candidate_pool']['rectangles']}
    for value in bank['temporal'].values():
        if value['state'] == 'available':
            for key in value['worlds']:
                world = bank['worlds'][key]
                require(world[:len(known)] == known, 'Known world changed in bank')
                bases.update(tuple(map(q, r['xyxy'])) for r in world[len(known):])
    return known, unknown, [list(map(w, b)) for b in sorted(bases)]


def expected_seeds(before, known, unknown, pool, proofs, family):
    pred = {r['id']: tuple(map(q, r['xyxy'])) for role in ROLES for r in before['image'][role]['value']}
    lookup = {tuple(n): i for i, n in enumerate(pool['neighborhoods'])}; result = []
    for key in before['analysis']['families'][family]['proof_keys']:
        proof = proofs[key]; world = proof['references']
        require(proof['image'] == before['image'] and world[:len(known)] == known, 'Seed operand substitution')
        added = world[len(known):]; ids = [r['id'] for r in added]
        require(len(ids) == len(set(ids)) and set(ids) <= {'timing-unknown:'+u for u in unknown}, 'Seed identity/budget wrong')
        indices = []
        for row in added:
            n = tuple(k for k in sorted(pred) if exact_iou(pred[k], list(map(q, row['xyxy']))) >= Fraction(1,2))
            if n: indices.append(lookup[n])
        result.append({'indices': sorted(indices), 'measurement': proof['measurement']})
    return result


def reconstruct(known, unknown, pool, endpoint, indices, image):
    require(type(indices) is list and indices == sorted(indices) and len(indices) <= len(unknown), 'World exceeds budget or order')
    expected = [{'operation': 'optional_eligible', 'instance': unknown[i], 'candidate_index': n} for i, n in enumerate(indices)]
    require(endpoint['operations'] == expected and endpoint['absent_or_ineligible'] == unknown[len(indices):], 'Optional operations or identities forged')
    refs = expected_world(known, unknown, indices, pool['rectangles'])
    validate_rows(refs); validate_canvas(refs, image)
    require(all(q(r['xyxy'][3])-q(r['xyxy'][1]) >= 25 for r in refs), 'Reference below eligible height')
    return refs


def check_pair(before, after, bank, temporal, family, detail, inherited, new, pools, cache, pair):
    known, unknown, bases = independent_context(before, bank, temporal, family)
    prior = before['analysis']['families'][family]
    center = matching(before['image'], known)
    require(independent_bounds(before['image'], center, len(unknown)) == prior['bounds'], 'Inherited bound does not match fixed operands')
    if detail['state'] == 'inherited_exact':
        require(prior['bounds'] == prior['attained'] and detail == {'state': 'inherited_exact', 'new_search': False}
                and before == after, 'Incorrect exact inheritance')
        return set(), 0
    if detail['state'] == 'search_incomplete':
        require(before == after and isinstance(detail.get('error'), str) and detail['error'], 'Failed attempt changed evidence')
        keys = set(detail['retained_attempt_proof_keys']); require(keys <= set(new), 'Failed attempt proof missing')
        return keys, 0
    require(detail['state'] == 'complete', 'Unknown refinement state')
    pool_key = digest({'image': before['image'], 'known': known, 'bases': bases})
    require(detail['pool_key'] == pool_key and pool_key in pools, 'Pool context changed')
    pool = pools[pool_key]
    if pool_key not in cache['pools']:
        require(pool == independent_pool(before['image'], known, bases), 'Pool coverage or matching neighborhood differs')
        cache['pools'].add(pool_key)
    seeds = expected_seeds(before, known, unknown, pool, inherited, family)
    require(detail['seeds'] == seeds, 'Seed remapping differs')
    key = digest({'image': before['image'], 'known': known, 'unknown': unknown, 'pool': pool, 'seeds': seeds, 'bounds': prior['bounds']})
    require(detail['search_key'] == key, 'Reuse context changed')
    found = detail['search']; count = 0
    require(found['known'] == center and found['bounds'] == prior['bounds'], 'Known matching or bound changed')
    if detail['reused_from'] is None:
        require(detail['new_search'] is True and key not in cache['searches'], 'Duplicate charged search')
        count = check_search(before['image'], known, unknown, pool, seeds, found)
        cache['searches'][key] = (pair, found)
    else:
        require(detail['new_search'] is False and cache['searches'].get(key) == (detail['reused_from'], found), 'Invalid identity reuse')
    require(len(detail['endpoints']) == 2, 'Endpoint omitted')
    expected = deepcopy(before); keys = []; values = []; improved = []; used = set()
    for i, (endpoint, world) in enumerate(zip(detail['endpoints'], found['worlds'])):
        refs = reconstruct(known, unknown, pool, endpoint, world['indices'], before['image'])
        k = digest({'image': before['image'], 'references': refs}); used.add(k)
        require(endpoint['proof_key'] == k and k in new, 'Wrong or absent proof')
        record = new[k]
        require(record['image'] == before['image'] and record['references'] == refs
                and record['measurement'] == world['measurement'], 'Proof-to-world binding differs')
        value = q(record['measurement']['delta'])
        require(q(prior['bounds'][0]) <= value <= q(prior['bounds'][1]), 'COUNTEREXAMPLE to inherited bound')
        better = value < q(prior['attained'][i]) if i == 0 else value > q(prior['attained'][i])
        improved.append(better); keys.append(k if better else prior['proof_keys'][i])
        values.append(record['measurement']['delta'] if better else prior['attained'][i])
    expected['analysis']['families'][family] = {**prior, 'attained': values, 'proof_keys': keys}
    require(after == expected and detail['improved_endpoints'] == improved, 'Input, threshold, bound or other family changed')
    return used, count


def check_rows(parent, result, allocation, states, proofs, failures):
    changes = []; refinements = []; gaps = []; classifications = []
    target_set = {tuple(r) for r in allocation['target_rows']}
    for section in ('primary_rows', 'anchor_rows'):
        require(len(result[section]) == len(parent[section]), 'Parent row omitted')
        for i, (old, row) in enumerate(zip(parent[section], result[section])):
            identity = 'cell_id' if section == 'primary_rows' else 'threshold'
            require(row[identity] == old[identity] and row['family'] == old['family'], 'Wrong cutoff or family')
            case = {'id': old['case_id'], 'group': old['group'], 'images': old['membership']}
            check_case(row, case, old['family'], old['state_keys'], states, proofs)
            require(all(row[k] == old[k] for k in ('state', 'decision', 'bounds', 'membership', 'blocked_images')), 'Universal result changed')
            if row['attained'] is not None:
                require(q(row['attained'][0]) <= q(old['attained'][0]) and q(row['attained'][1]) >= q(old['attained'][1]), 'Inherited witness lost')
            if row['attained'] != old['attained']: refinements.append([section, i])
            if row['evidence'] != old['evidence']:
                require(old['evidence'] == 'bound_gap' and row['evidence'] == 'opposite_worlds', 'Evidence regressed')
                changes.append([section, i])
            if row['evidence'] == 'bound_gap': gaps.append([section, i])
            if (section, i) in target_set:
                failed = [k+':'+row['family'] for k in row['state_keys'] if k+':'+row['family'] in failures]
                label = 'opposing_worlds_established' if row['evidence'] == 'opposite_worlds' else 'search_incomplete' if failed else 'still_bound_gap'
                classifications.append({'section': section, 'index': i, 'classification': label, 'failed_components': failed})
        require(dict(Counter(r['evidence'] or 'input_blocked' for r in result[section])) == result['evidence_counts'][section], 'Counts differ')
    require(classifications == result['target_classifications'], 'Target disposition omitted or changed')
    return changes, refinements, gaps


def verify(area, output):
    started = datetime.now(timezone.utc).isoformat(); tick = time.perf_counter()
    frozen, allocation, parent, states, inherited, banks, temporal = sources(area)
    path = area/'analysis/RESULTS.json'; result = read(path)
    require(result['freeze_sha256'] == file_binding(area/'FREEZE.json')['sha256'], 'Freeze binding differs')
    require([[e['key'], e['family']] for e in result['refined_pairs']] == allocation['target_pairs'], 'Pairs missing or reordered')
    pools = {e['key']: bound_read(e) for e in result['pools']}
    require(len(pools) == len(result['pools']), 'Duplicate pool')
    new = {}; cache = {'native': set(), 'native_check_seconds': 0., 'pools': set(), 'searches': {}}
    for e in result['new_proofs']:
        key = e['key']; require(key not in new, 'Duplicate new proof'); new[key] = bound_read(e)
        verify_proof(key, new[key], cache)
        if key in inherited:
            require(all(inherited[key][f] == new[key][f] for f in ('image','references','measurement','proof')), 'Inherited proof collision')
    used = set(); failed = {}; pair_states = Counter(); measurements = 0; improved = 0; search_stops = Counter()
    for e in result['refined_pairs']:
        key, family = e['key'], e['family']; before = states[key]; iid = before['image']['id']
        require(key == digest({'image': before['image'], 'custody': before['custody']}), 'Filtered state identity differs')
        record = bound_read(e); detail = record['refinement']
        keys, count = check_pair(before, record['state'], banks[iid], temporal[iid], family, detail, inherited, new, pools, cache, [key,family])
        used.update(keys); measurements += count; states[key] = record['state']; pair_states[detail['state']] += 1
        improved += sum(detail.get('improved_endpoints', []))
        if detail['state'] == 'search_incomplete': failed[key+':'+family] = detail['error']
        elif detail['state'] == 'complete' and detail['new_search']: search_stops[detail['search']['stop']] += 1
    require(used == set(new) and failed == result['failures'], 'Attempt/proof/failure inventory differs')
    attempts = bound_read(result['search_attempts'])
    successful = [{'key': k, 'pair': pair, 'search': found} for k, (pair, found) in sorted(cache['searches'].items())]
    require(all(r in attempts for r in successful) and len({r['key'] for r in attempts}) == len(attempts), 'Search attempt inventory differs')
    if not failed: require(attempts == successful, 'Unexplained search attempt')
    require(cache['pools'] <= set(pools), 'Missing checked pool')
    changes, refinements, gaps = check_rows(parent, result, allocation, states, {**inherited, **new}, failed)
    target_set = {tuple(r) for r in allocation['target_rows']}
    report = {'artifact_id': 'reiyah.operating-timing-witness.verification', 'version': '0.1.0',
        'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(), 'seconds': time.perf_counter()-tick,
        'results_sha256': file_binding(path)['sha256'], 'freeze_sha256': file_binding(area/'FREEZE.json')['sha256'],
        'all_7707_parent_rows_checked': True, 'all_universal_decisions_unchanged': True,
        'inherited_proofs_exact_bound': len(inherited), 'new_proofs_checked': len(new),
        'unique_native_proofs_checked': len(cache['native']), 'native_check_seconds': cache['native_check_seconds'],
        'pair_states': dict(pair_states), 'unique_searches': len(cache['searches']), 'unique_pools': len(cache['pools']),
        'unique_flow_measurements_checked': measurements, 'improved_pair_endpoints': improved,
        'search_stops': dict(search_stops), 'changed_evidence_rows': changes, 'refined_interval_rows': refinements,
        'nontarget_refined_interval_rows': [r for r in refinements if tuple(r) not in target_set],
        'remaining_gap_rows': gaps, 'failures': failed, 'target_classifications': dict(Counter(r['classification'] for r in result['target_classifications'])),
        'verifier_sha256': file_binding(__file__)['sha256'], 'independent_scientific_replication': False}
    put(output, report)
    print({k: report[k] for k in ('pair_states','unique_searches','unique_pools','new_proofs_checked','target_classifications','seconds')}, flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('area', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); verify(a.area, a.output)
