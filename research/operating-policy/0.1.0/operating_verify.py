"""Verify threshold coverage, all worlds, full cases and operating frontiers."""
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
import sys
import time

from operating_sources import ANCHORS, ROLES, digest, file_binding, q, put, read, require
from operating_math import FAMILIES
from operating_run import load_sources, regression_floor
from operating_certificate import (check_case, check_curves, decimal, expected_cells,
                                   expected_filter, independent_analysis, verify_proof)


def check_bank(bank, original, edit, temporal):
    worlds = {}; deletions = []; edit_worlds = []
    def add(rows):
        key = digest(rows); worlds[key] = rows; return key
    original_key = add(original)
    for identity in [None]+[row['id'] for row in original]:
        remaining = [row for row in original if row['id'] != identity]; key = add(remaining)
        deletions.append({'removed_reference': identity, 'world': key}); edit_worlds.append(key)
    require(edit['search_state'] == 'complete', 'Unverified edit bank')
    for endpoint in ('lower', 'upper'):
        source = edit['search']['witnesses'][endpoint]; change = source['edit']
        removed, inserted = change['removed_reference'], change['inserted_reference']; operation = change['operation']
        require(operation in ('none', 'deletion', 'insertion', 'replacement')
                and (removed is not None) == (operation in ('deletion', 'replacement'))
                and (inserted is not None) == (operation in ('insertion', 'replacement')),
                'Invalid inherited edit operation')
        require(removed is None or removed in {row['id'] for row in original}, 'Deleted reference not present')
        altered = [row for row in original if row['id'] != removed]+([] if inserted is None else [inserted])
        require(altered == source['altered_references'], 'Edited world source differs'); edit_worlds.append(add(altered))
    known = temporal['known_references']; known_key = add(known); scopes = {}
    for scope in ('current', 'union'):
        unknown = temporal[scope+'_unknown_instances']
        if unknown is None:
            scopes[scope] = {'state': 'input_blocked', 'reason': 'preceding_census_unavailable'}; continue
        identities = {'timing-unknown:'+token for token in unknown}; admitted = {known_key}
        for proof in temporal['proofs'].values():
            refs = proof['references']; tail = refs[len(known):]; ids = [row['id'] for row in tail]
            if refs[:len(known)] == known and len(set(ids)) == len(ids) and all(key in identities for key in ids):
                admitted.add(add(refs))
        scopes[scope] = {'state': 'available', 'unknown_ids': unknown, 'unknown_count': len(unknown), 'worlds': sorted(admitted)}
    expected = {'worlds': worlds, 'original_world': original_key, 'known_world': known_key,
                'deletions': deletions, 'edit_worlds': sorted(set(edit_worlds)), 'temporal': scopes}
    require(bank == expected, 'Inherited world bank or optional census changed')


def bound_read(entry):
    require(file_binding(entry['path']) == {key: entry[key] for key in ('path', 'bytes', 'sha256')}, 'Result bytes changed')
    return read(entry['path'])


def run(area, run_name='operating-01'):
    area = Path(area).resolve(); tick = time.perf_counter(); started = datetime.now(timezone.utc).isoformat()
    freeze, visible, packets, source_banks, role_cells, common = load_sources(area)
    output = area/'runs'/run_name; result_path = output/'RESULTS.json'; result = read(result_path)
    require(result['freeze_sha256'] == file_binding(area/'FREEZE.json')['sha256'] and result['failures'] == {},
            'Result freeze differs or is incomplete')
    scores = {role: [decimal(detection['score']) for source in packets[role].values() for detection in source['detections']
                    if detection['category_id'] == 2 and decimal(detection['xyxy'][3])-decimal(detection['xyxy'][1]) >= 25]
              for role in ROLES}
    for role in ROLES: require(role_cells[role] == expected_cells(scores[role]), 'Individual threshold coverage differs')
    require(common == expected_cells(scores[ROLES[0]]+scores[ROLES[1]]), 'Common threshold coverage differs')
    require(result['allocation'] == {'common_cells': common, 'anchors': [dict(numerator=str(value.numerator), denominator=str(value.denominator)) for value in ANCHORS],
            'cases': visible['cases'], 'families': list(FAMILIES)}, 'Declared allocation changed')
    comparison = Path(freeze['comparison']); temporal = read(freeze['temporal_results'])
    temporal_entries = {row['image_id']: row for row in temporal['image_records']}; banks = {}
    for entry in result['world_banks']:
        iid = entry['image_id']; require(iid in source_banks and iid not in banks, 'World-bank image repeated or unknown')
        bank = bound_read(entry); original = read(comparison/'oracle'/(iid+'.json'))['answer']
        edit = read(comparison/'runs/analysis-01'/(iid+'.json')); temporal_record = bound_read(temporal_entries[iid])
        check_bank(bank, original, edit, temporal_record); banks[iid] = bank
    require(set(banks) == set(source_banks), 'World-bank allocation omitted')
    proofs = {}; cache = {'native': set(), 'native_check_seconds': 0.0}
    for entry in result['proof_records']:
        key = entry['key']; require(key not in proofs and entry['kind'] == 'native_world', 'Repeated or invalid proof entry')
        proof = bound_read(entry); verify_proof(key, proof, cache); proofs[key] = proof
    require(len(proofs) == result['distinct_native_worlds'] <= 20000, 'Native proof count or limit differs')
    states = {}; used_proofs = set()
    for entry in result['state_records']:
        key = entry['key']; require(key not in states and entry['kind'] == 'filtered_image', 'Repeated or invalid state entry')
        state = bound_read(entry); require(key == digest({'image': state['image'], 'custody': state['custody']}), 'Filtered state identity changed')
        require(state['image']['id'] in banks and state['analysis'] == independent_analysis(state['image'], banks[state['image']['id']], proofs),
                'Filtered state bounds or loss counts differ')
        states[key] = state; used_proofs.update(state['analysis']['world_proof_keys'].values())
    require(used_proofs == set(proofs) and len(states) == result['distinct_filtered_states'] <= 4096,
            'Unexplained proof, missing state or state limit exceeded')
    threshold_keys = {}; used_states = set()
    def at(threshold):
        if threshold in threshold_keys: return threshold_keys[threshold]
        found = {}
        for original in visible['images']:
            image, custody = expected_filter(original, packets, threshold, freeze['policy_sha256'])
            key = digest({'image': image, 'custody': custody}); require(key in states, 'Threshold lacks its complete filtered input')
            require(states[key]['image'] == image and states[key]['custody'] == custody, 'Score filter or source join differs')
            found[image['id']] = key; used_states.add(key)
        threshold_keys[threshold] = found; return found
    primary = next(case for case in visible['cases'] if case['group'] == 'primary')
    lookup = {case['id']: case for case in visible['cases']}; cell_lookup = {cell['id']: cell for cell in common}
    seen = set()
    for row in result['primary_rows']:
        key = row['cell_id'], row['family']; require(key[0] in cell_lookup and key[1] in FAMILIES and key not in seen,
                                                   'Repeated or unknown primary cell/family')
        seen.add(key); inputs = at(q(cell_lookup[key[0]]['representative']))
        check_case(row, primary, key[1], [inputs[iid] for iid in primary['images']], states, proofs)
    require(seen == {(cell['id'], family) for cell in common for family in FAMILIES}, 'Primary cell allocation omitted')
    seen = set(); floor = []
    for row in result['anchor_rows']:
        threshold = q(row['threshold']); key = threshold, row['case_id'], row['family']
        require(threshold in ANCHORS and key[1] in lookup and key[2] in FAMILIES and key not in seen, 'Repeated or unknown anchor allocation')
        seen.add(key); case = lookup[key[1]]; inputs = at(threshold)
        check_case(row, case, key[2], [inputs[iid] for iid in case['images']], states, proofs)
        if threshold == ANCHORS[0]: floor.append(row)
    require(seen == {(threshold, case, family) for threshold in ANCHORS for case in lookup for family in FAMILIES},
            'Diagnostic anchor allocation omitted')
    regression_floor(floor, freeze); require(result['floor_regression_passed'] is True, 'Inherited floor regression missing')
    curves_record = bound_read(result['curves_source']); require(curves_record['role_cells'] == role_cells, 'Curve cell domains differ')
    curves = curves_record['curves']; require(set(curves) == set(ROLES), 'Detector curve omitted')
    for index, role in enumerate(ROLES):
        require(len(curves[role]) == len(role_cells[role]), 'Individual curve allocation omitted')
        for cell, row in zip(role_cells[role], curves[role]):
            inputs = at(q(cell['representative'])); values = [states[inputs[iid]]['analysis'] for iid in primary['images']]
            n = sum(value['prediction_counts'][index] for value in values)
            rank = sum(value['nominal']['ranks'][index] for value in values); refs = sum(value['nominal_reference_count'] for value in values)
            require(row == {'cell_id': cell['id'], 'false_positives': n-rank, 'misses': refs-rank,
                            'predictions': n, 'matching_rank': rank, 'references': refs}, 'Detector curve count differs')
    check_curves(curves[ROLES[0]], curves[ROLES[1]], max(curves[role][0]['predictions'] for role in ROLES), curves_record['comparison'])
    require(used_states == set(states), 'Unexplained filtered image state')
    for name in ('primary', 'anchor'):
        require(result[name+'_decisions'] == dict(Counter(row['decision'] for row in result[name+'_rows'])), 'Decision aggregate differs')
    report = {'artifact_id': 'reiyah.operating-policy.verification', 'version': '0.1.0',
        'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(), 'seconds': time.perf_counter()-tick,
        'results_sha256': file_binding(result_path)['sha256'], 'verifier_sha256': file_binding(__file__)['sha256'],
        'all_assigned_rows_verified': True, 'all_source_score_joins_verified': True, 'floor_regression_passed': True,
        'primary_rows': len(result['primary_rows']), 'anchor_rows': len(result['anchor_rows']),
        'filtered_states': len(states), 'native_proofs': len(proofs), 'native_check_seconds': cache['native_check_seconds'],
        'common_threshold_cells': len(common), 'individual_threshold_cells': [len(role_cells[role]) for role in ROLES],
        'nominal_threshold_pairs': curves_record['comparison']['nominal_pair_grid']['allocated_pairs'],
        'human_seconds': None, 'economic_cost': None, 'independent_scientific_replication': False}
    put(output/'VERIFICATION.json', report); print(__import__('json').dumps(report), flush=True)


if __name__ == '__main__':
    run(*sys.argv[1:])
