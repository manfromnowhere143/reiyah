"""Refine finite one-edit witnesses on immutable retained filtered operands."""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'research/operating-policy/0.1.0'))
from operating_sources import digest, file_binding, put, q, read, require
from operating_math import aggregate
from geometric_worlds import search_image

EDIT_FAMILIES = ('one_edit_global', 'one_edit_per_image')
MAX_STATES = 185
MAX_NEW_PROOFS = 370


def targets(parent):
    rows = [(section, index, row) for section in ('primary_rows', 'anchor_rows')
            for index, row in enumerate(parent[section])
            if row['family'] in EDIT_FAMILIES and row['evidence'] == 'bound_gap']
    return rows, sorted({key for _, _, row in rows for key in row['state_keys']})


def refine(state, bank, proofs):
    result = deepcopy(state); prior = state['analysis']['families']['one_edit_per_image']
    require(prior['state'] == 'available', 'One-edit input unavailable')
    if prior['attained'] == prior['bounds']:
        return result, {'state': 'inherited_exact', 'new_search': False}
    found = search_image(state['image'], bank['worlds'][bank['original_world']])
    require(found['nominal']['edit_bounds'] == prior['bounds'], 'Search changes universal bounds')
    chosen, improved = [], []
    for index, direction in enumerate(('lower', 'upper')):
        world = found['witnesses'][direction]
        value = q(world['measurement']['delta']); previous = q(prior['attained'][index])
        better = value < previous if index == 0 else value > previous
        require(q(prior['bounds'][0]) <= value <= q(prior['bounds'][1]), 'Witness outside universal bounds')
        key = digest({'image': state['image'], 'references': world['altered_references']})
        record = {'image': state['image'], 'references': world['altered_references'],
                  'measurement': world['measurement'], 'proof': world['native_proof'],
                  'native_timing': world['native_timing']}
        if key not in proofs:
            require(len(proofs) < MAX_NEW_PROOFS, 'Endpoint proof allocation exceeded')
            proofs[key] = record
        else:
            require(all(proofs[key][k] == record[k] for k in ('image', 'references', 'measurement', 'proof')),
                    'Repeated proof key has different content')
        chosen.append(key if better else prior['proof_keys'][index]); improved.append(better)
    updated = {**prior, 'attained': [found['witnesses'][direction]['measurement']['delta'] if better
                                   else prior['attained'][index]
                                   for index, (direction, better) in enumerate(zip(('lower', 'upper'), improved))],
               'proof_keys': chosen}
    for family in EDIT_FAMILIES:
        require(state['analysis']['families'][family] == prior, 'One-edit component families differ')
        result['analysis']['families'][family] = deepcopy(updated)
    return result, {'state': 'complete', 'new_search': True, 'search': found, 'improved_endpoints': improved}


def freeze(session, area):
    require(not area.exists(), 'Witness area already exists'); area.mkdir(parents=True)
    parent_area = session / 'private/operating-policy-01'
    parent_path = parent_area / 'runs/operating-01/RESULTS.json'
    verify_path = parent_path.with_name('VERIFICATION.json')
    parent = read(parent_path); checked = read(verify_path)
    require(checked['results_sha256'] == file_binding(parent_path)['sha256']
            and checked['all_assigned_rows_verified'] and checked['all_source_score_joins_verified'],
            'Parent lacks complete verification')
    rows, keys = targets(parent)
    require(len(rows) == 110 and len(keys) == MAX_STATES, 'Declared target allocation differs')
    paths = {parent_path, verify_path, parent_area / 'FREEZE.json'}
    for binding in read(parent_area / 'FREEZE.json')['bindings']:
        require(file_binding(binding['path']) == binding, 'Inherited frozen dependency changed')
        paths.add(Path(binding['path']))
    controls = session / 'logs/operating-witness-controls-01-COMPLETED.json'
    require(read(controls)['exit_code'] == 0, 'New synthetic controls did not pass')
    paths.update(session / ('logs/operating-witness-controls-01' + suffix)
                 for suffix in ('-STARTED.json', '-COMPLETED.json', '.stdout', '.stderr'))
    for section in ('state_records', 'proof_records', 'world_banks'):
        for entry in parent[section]:
            path = Path(entry['path']); require(file_binding(path) == {k: entry[k] for k in ('path', 'bytes', 'sha256')},
                                               'Parent dependent bytes changed')
            paths.add(path)
    paths.update(path for path in Path(__file__).parent.iterdir() if path.suffix in ('.py', '.md'))
    state_entries = {r['key']: r for r in parent['state_records']}
    incomplete = []
    for key in keys:
        a = read(state_entries[key]['path'])['analysis']['families']['one_edit_per_image']
        if a['bounds'] != a['attained']: incomplete.append(key)
    require(len(incomplete) == 98, 'Declared search-state count differs')
    value = {'artifact_id': 'reiyah.operating-witness.freeze', 'version': '0.1.0', 'status': 'exploratory',
             'frozen_utc': datetime.now(timezone.utc).isoformat(), 'parent_results': str(parent_path),
             'parent_verification': str(verify_path), 'bindings': [file_binding(p) for p in sorted(paths)],
             'target_rows': [[section, index] for section, index, _ in rows], 'target_states': keys,
             'search_states': incomplete, 'previous_outcomes_known': True,
             'new_search_outcomes_before_freeze': False, 'reserved_outcomes_accessed': 0}
    put(area / 'FREEZE.json', value)
    print({'bindings': len(value['bindings']), 'target_rows': len(rows), 'target_states': len(keys),
           'search_states': len(incomplete), 'freeze_sha256': file_binding(area / 'FREEZE.json')['sha256']})


def sources(area):
    frozen = read(area / 'FREEZE.json')
    for binding in frozen['bindings']:
        require(file_binding(binding['path']) == binding, 'Frozen operating-witness input changed')
    parent = read(frozen['parent_results']); checked = read(frozen['parent_verification'])
    require(checked['results_sha256'] == file_binding(frozen['parent_results'])['sha256']
            and checked['all_assigned_rows_verified'], 'Parent verification binding differs')
    rows, keys = targets(parent)
    require([[s, i] for s, i, _ in rows] == frozen['target_rows'] and keys == frozen['target_states'],
            'Target allocation changed')
    states = {e['key']: read(e['path']) for e in parent['state_records']}
    banks = {e['image_id']: read(e['path']) for e in parent['world_banks']}
    return frozen, parent, states, banks


def run(area):
    tick = time.perf_counter(); started = datetime.now(timezone.utc).isoformat()
    frozen, parent, states, banks = sources(area)
    output = area / 'analysis'; output.mkdir(); (output / 'states').mkdir(); (output / 'proofs').mkdir()
    proofs, records, failures = {}, [], {}
    for key in frozen['target_states']:
        old = states[key]
        try:
            updated, search = refine(old, banks[old['image']['id']], proofs)
        except Exception as exc:
            updated = old; search = {'state': 'search_incomplete', 'new_search': True,
                                     'error': type(exc).__name__ + ': ' + str(exc)}
            failures[key] = search['error']
        path = output / 'states' / (key + '.json'); put(path, {'state': updated, 'refinement': search})
        records.append({'key': key, **file_binding(path)}); states[key] = updated
    proof_records = []
    for key, record in sorted(proofs.items()):
        path = output / 'proofs' / (key + '.json'); put(path, record)
        proof_records.append({'key': key, **file_binding(path)})
    result = {}
    for section in ('primary_rows', 'anchor_rows'):
        result[section] = []
        for old in parent[section]:
            case = {'id': old['case_id'], 'group': old['group'], 'images': old['membership']}
            row = aggregate(case, old['family'], old['state_keys'], states)
            identity = 'cell_id' if section == 'primary_rows' else 'threshold'
            row[identity] = old[identity]
            require(all(row[k] == old[k] for k in ('state', 'decision', 'bounds', 'membership', 'blocked_images')),
                    'Witness refinement changed a universal result')
            result[section].append(row)
    counts = {section: dict(Counter(row['evidence'] or 'input_blocked' for row in result[section]))
              for section in ('primary_rows', 'anchor_rows')}
    result.update({'artifact_id': 'reiyah.operating-witness.results', 'version': '0.1.0', 'status': 'exploratory',
                   'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(),
                   'seconds': time.perf_counter() - tick, 'freeze_sha256': file_binding(area / 'FREEZE.json')['sha256'],
                   'refined_states': records, 'new_proofs': proof_records, 'failures': failures,
                   'evidence_counts': counts, 'reserved_outcomes_accessed': 0, 'new_image_reads': 0,
                   'new_model_calls': 0, 'new_download_bytes': 0, 'human_seconds': None, 'full_economic_cost': None,
                   'independent_scientific_replication': False})
    put(output / 'RESULTS.json', result)
    print(__import__('json').dumps({'counts': counts, 'failures': failures, 'new_proofs': len(proofs), 'seconds': result['seconds']}))


def main():
    p = argparse.ArgumentParser(); p.add_argument('--area', type=Path, required=True)
    p.add_argument('--freeze', action='store_true'); p.add_argument('--session', type=Path); a = p.parse_args()
    if a.freeze: freeze(a.session.resolve(), a.area.resolve())
    else: run(a.area.resolve())


if __name__ == '__main__': main()
