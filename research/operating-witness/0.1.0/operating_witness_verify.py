"""Check every new edited world and all inherited case obligations."""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import time

from operating_witness import EDIT_FAMILIES, MAX_NEW_PROOFS, digest, file_binding, put, q, read, require, sources
from operating_certificate import check_case, verify_proof
from compare_math import validate_canvas, validate_rows


def edited_world(original, edit, image):
    require(set(edit) == {'operation', 'removed_reference', 'inserted_reference'}, 'Unexpected edit fields')
    operation = edit['operation']; removed = edit['removed_reference']; inserted = edit['inserted_reference']
    require(operation in ('none', 'deletion', 'insertion', 'replacement'), 'Unknown edit operation')
    require((removed is not None) == (operation in ('deletion', 'replacement'))
            and (inserted is not None) == (operation in ('insertion', 'replacement')), 'Edit cardinality differs')
    identities = [r['id'] for r in original]
    require(len(set(identities)) == len(identities), 'Repeated original reference')
    require(removed is None or removed in identities, 'Removed reference absent')
    require(inserted is None or inserted['id'] not in identities, 'Inserted identity collision')
    rows = [r for r in original if r['id'] != removed]
    if inserted is not None: rows.append(inserted)
    validate_rows(rows); validate_canvas(rows, image)
    return rows


def check_refinement(before, after, bank, detail, proofs):
    if detail['state'] in ('inherited_exact', 'search_incomplete'):
        require(after == before, 'Unsearched or failed state changed')
        if detail['state'] == 'inherited_exact':
            value = before['analysis']['families']['one_edit_per_image']
            require(value['bounds'] == value['attained'] and detail['new_search'] is False, 'Inexact state skipped')
        else:
            require(isinstance(detail.get('error'), str) and detail['error'], 'Failed search lacks reason')
        return []
    require(detail['state'] == 'complete' and detail['new_search'] is True, 'Unknown refinement state')
    found = detail['search']; original = bank['worlds'][bank['original_world']]
    require(found['image_id'] == before['image']['id'], 'Search substitutes image')
    require(found['all_rectangles_exhaustively_searched'] is False and found['axis_cells_exhaustively_searched'] is True,
            'Search scope changed')
    require(found['candidate_rectangles'] <= 100000 and found['base_candidate_evaluations'] <= 2000000,
            'Search limit exceeded')
    prior = before['analysis']['families']['one_edit_per_image']
    require(found['nominal']['edit_bounds'] == prior['bounds'], 'Universal bound changed')
    expected = deepcopy(before); chosen = []; values = []; improves = []; keys = []
    for index, direction in enumerate(('lower', 'upper')):
        witness = found['witnesses'][direction]
        references = edited_world(original, witness['edit'], before['image'])
        require(references == witness['altered_references'], 'Claimed edit and retained world differ')
        key = digest({'image': before['image'], 'references': references}); keys.append(key)
        require(key in proofs, 'New endpoint proof omitted')
        proof = proofs[key]
        require(proof['image'] == before['image'] and proof['references'] == references
                and proof['measurement'] == witness['measurement'] and proof['proof'] == witness['native_proof'],
                'Endpoint evidence binding differs')
        value = q(proof['measurement']['delta']); old_value = q(prior['attained'][index])
        better = value < old_value if index == 0 else value > old_value
        require(q(prior['bounds'][0]) <= value <= q(prior['bounds'][1]), 'World outside universal bound')
        chosen.append(key if better else prior['proof_keys'][index]); improves.append(better)
        values.append(proof['measurement']['delta'] if better else prior['attained'][index])
    for family in EDIT_FAMILIES:
        expected['analysis']['families'][family] = {**prior, 'attained': values, 'proof_keys': chosen}
    require(detail['improved_endpoints'] == improves, 'Improvement label differs')
    require(after == expected, 'Refinement changes another input, family or bound')
    return keys


def verify(area):
    tick = time.perf_counter(); started = datetime.now(timezone.utc).isoformat()
    frozen, parent, states, banks = sources(area)
    path = area / 'analysis/RESULTS.json'; result = read(path)
    require(result['freeze_sha256'] == file_binding(area / 'FREEZE.json')['sha256'], 'Result freeze differs')
    require([r['key'] for r in result['refined_states']] == frozen['target_states'], 'Target states missing or reordered')
    proofs = {r['key']: read(r['path']) for r in parent['proof_records']}; inherited = set(proofs)
    new = {}; cache = {'native': set(), 'native_check_seconds': 0.0}
    for entry in result['new_proofs']:
        require(file_binding(entry['path']) == {k: entry[k] for k in ('path', 'bytes', 'sha256')}, 'New proof bytes changed')
        key = entry['key']; require(key not in new, 'Repeated new proof'); new[key] = read(entry['path'])
        verify_proof(key, new[key], cache)
        if key in proofs:
            require(all(proofs[key][field] == new[key][field] for field in ('image', 'references', 'measurement', 'proof')),
                    'New proof collides with a different inherited world')
        proofs[key] = new[key]
    require(len(new) <= MAX_NEW_PROOFS, 'Proof limit exceeded')
    referenced = set(); states_checked = Counter(); failures = {}; improved_endpoints = 0; pool_totals = Counter()
    for entry in result['refined_states']:
        require(file_binding(entry['path']) == {k: entry[k] for k in ('path', 'bytes', 'sha256')}, 'New state bytes changed')
        key = entry['key']; record = read(entry['path']); detail = record['refinement']; before = states[key]
        referenced.update(check_refinement(before, record['state'], banks[before['image']['id']], detail, new))
        states_checked[detail['state']] += 1; states[key] = record['state']
        if detail['state'] == 'complete':
            improved_endpoints += sum(detail['improved_endpoints'])
            for field in ('candidate_rectangles', 'candidate_bases', 'neighborhoods', 'base_candidate_evaluations'):
                pool_totals[field] += detail['search'][field]
        elif detail['state'] == 'search_incomplete': failures[key] = detail['error']
    require(referenced == set(new) and failures == result['failures'], 'Proof or failure inventory differs')
    changes, target_changes, gap_rows = [], [], []
    target_ids = {tuple(row) for row in frozen['target_rows']}
    for section in ('primary_rows', 'anchor_rows'):
        require(len(result[section]) == len(parent[section]), 'Case allocation changed')
        for index, (old, row) in enumerate(zip(parent[section], result[section])):
            identity = 'cell_id' if section == 'primary_rows' else 'threshold'
            require(row[identity] == old[identity] and row['family'] == old['family'], 'Case cell identity changed')
            case = {'id': old['case_id'], 'group': old['group'], 'images': old['membership']}
            check_case(row, case, old['family'], old['state_keys'], states, proofs)
            require(all(row[k] == old[k] for k in ('state', 'decision', 'bounds', 'membership', 'blocked_images')),
                    'Universal decision or allocation changed')
            if row['evidence'] != old['evidence']:
                require(old['evidence'] == 'bound_gap' and row['evidence'] == 'opposite_worlds', 'Evidence regressed')
                changes.append([section, index])
                if (section, index) in target_ids: target_changes.append([section, index])
            if row['evidence'] == 'bound_gap': gap_rows.append([section, index])
        count = dict(Counter(row['evidence'] or 'input_blocked' for row in result[section]))
        require(count == result['evidence_counts'][section], 'Evidence summary differs')
    return {'artifact_id': 'reiyah.operating-witness.verification', 'version': '0.1.0',
            'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(), 'seconds': time.perf_counter() - tick,
            'results_sha256': file_binding(path)['sha256'], 'freeze_sha256': file_binding(area / 'FREEZE.json')['sha256'],
            'all_7707_parent_rows_checked': True, 'all_universal_decisions_unchanged': True,
            'inherited_proofs_bound_to_prior_verification': len(inherited), 'new_endpoint_proofs_checked': len(new),
            'native_check_seconds': cache['native_check_seconds'], 'states': dict(states_checked),
            'improved_image_endpoints': improved_endpoints, 'pool_totals': dict(pool_totals),
            'changed_rows': changes, 'changed_target_rows': target_changes, 'remaining_gap_rows': gap_rows,
            'failures': failures, 'independent_scientific_replication': False,
            'verifier_sha256': file_binding(Path(__file__))['sha256']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--area', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); args = p.parse_args()
    value = verify(args.area.resolve()); put(args.output, value)
    print(__import__('json').dumps({k: value[k] for k in ('states', 'improved_image_endpoints', 'new_endpoint_proofs_checked', 'seconds')}))
