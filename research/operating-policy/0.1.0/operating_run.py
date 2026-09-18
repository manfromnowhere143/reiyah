"""Execute the frozen retained-score continuum and all diagnostic anchors."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import sys
import time

from operating_sources import (ANCHORS, MAX_COMMON_CELLS, MAX_ROLE_CELLS, ROLES, cells,
    digest, eligible, file_binding, filtered_image, number, put, q, read, require, source_packets, w)
from operating_math import FAMILIES, aggregate, analyze_state, world_banks
from operating_frontier import compare_curves

MAX_STATES = 4096


class RetainedStore(dict):
    def __init__(self, folder, kind):
        super().__init__(); self.folder = folder; self.kind = kind; self.bindings = []; folder.mkdir()

    def __setitem__(self, key, value):
        require(key not in self, 'Cached record overwritten')
        path = self.folder/(key+'.json'); put(path, value)
        self.bindings.append({'key': key, 'kind': self.kind, **file_binding(path)})
        super().__setitem__(key, value)


def load_sources(area):
    freeze = read(area/'FREEZE.json')
    for binding in freeze['bindings']:
        require(file_binding(binding['path']) == binding, 'Frozen operating-policy source changed')
    root = Path(freeze['session_root']); comparison = Path(freeze['comparison'])
    visible = read(comparison/'inputs/visible.json'); packets, bindings, report = source_packets(root, visible)
    qualification = read(freeze['score_qualification'])
    require(qualification['source_bindings'] == bindings and qualification['roles'] == report
            and qualification['threshold_dependent_outcomes_computed'] is False, 'Retained score qualification changed')
    temporal_result = read(freeze['temporal_results']); temporal_verification = read(freeze['temporal_verification'])
    require(temporal_verification['results_sha256'] == file_binding(freeze['temporal_results'])['sha256']
            and temporal_verification['all_complete_rows_verified'], 'Temporal worlds lack their verification')
    entries = {entry['image_id']: entry for entry in temporal_result['image_records']}; banks = {}
    require(set(entries) == {image['id'] for image in visible['images']}, 'Temporal source membership differs')
    for image in visible['images']:
        iid = image['id']; entry = entries[iid]
        require(file_binding(entry['path']) == {key: entry[key] for key in ('path', 'bytes', 'sha256')}, 'Temporal image changed')
        original = read(comparison/'oracle'/(iid+'.json'))['answer']
        edit = read(comparison/'runs/analysis-01'/(iid+'.json')); temporal = read(entry['path'])
        banks[iid] = world_banks(original, edit, temporal)
    scores = {role: [number(detection['score']) for row in packets[role].values()
                    for detection in row['detections'] if eligible(detection)] for role in ROLES}
    role_cells = {role: cells(scores[role], MAX_ROLE_CELLS) for role in ROLES}
    common = cells(scores[ROLES[0]]+scores[ROLES[1]], MAX_COMMON_CELLS)
    return freeze, visible, packets, banks, role_cells, common


def regression_floor(rows, freeze):
    exact = read(Path(freeze['comparison'])/'runs/analysis-01/RESULTS.json')
    timing = read(freeze['temporal_results'])
    prior_temporal = {(row['case_id'], row['contract']): row for row in timing['cases']}
    # The first comparison's bound records use its three named families.
    prior_original = {(row['case_id'], row['family']): row for row in exact['cases']}
    for row in rows:
        if row['family'] in ('exact_projection', 'one_edit_per_image', 'one_edit_global'):
            previous = prior_original[row['case_id'], row['family']]
            require(row['bounds'] == previous['bounds'] and row['decision'] == previous['decision'],
                    'Inherited floor comparison changed')
        else:
            previous = prior_temporal[row['case_id'], row['family']]
            require(row['bounds'] == previous['bounds'] and row['decision'] == previous['decision'],
                    'Inherited temporal floor comparison changed')


def run(area, run_name='operating-01'):
    area = Path(area).resolve(); tick = time.perf_counter(); started = datetime.now(timezone.utc).isoformat()
    freeze, visible, packets, banks, role_cells, common = load_sources(area)
    require(len(visible['images']) == 64 and len(visible['cases']) == 73, 'Declared actual allocation differs')
    output = area/'runs'/run_name; output.mkdir(parents=True)
    put(output/'STARTED.json', {'started_utc': started, 'freeze_sha256': file_binding(area/'FREEZE.json')['sha256'],
        'common_cells': common, 'role_cells': role_cells, 'anchors': list(map(w, ANCHORS)), 'cases': visible['cases'],
        'families': list(FAMILIES), 'status': 'running'})
    proofs = RetainedStore(output/'proofs', 'native_world'); states = RetainedStore(output/'states', 'filtered_image')
    bank_dir = output/'banks'; bank_dir.mkdir(); bank_bindings = []
    for iid, bank in banks.items():
        path = bank_dir/(iid+'.json'); put(path, bank); bank_bindings.append({'image_id': iid, **file_binding(path)})
    threshold_states = {}; primary = next(case for case in visible['cases'] if case['group'] == 'primary')
    def at(threshold):
        if threshold in threshold_states: return threshold_states[threshold]
        keys = {}
        for original in visible['images']:
            image, custody = filtered_image(original, packets, threshold, freeze['policy_sha256'])
            key = digest({'image': image, 'custody': custody})
            if key not in states:
                require(len(states) < MAX_STATES, 'Filtered image state limit')
                analysis = analyze_state(image, banks[image['id']], proofs)
                states[key] = {'image': image, 'custody': custody, 'analysis': analysis}
            keys[image['id']] = key
        threshold_states[threshold] = keys; return keys
    try:
        primary_rows = []
        for cell in common:
            threshold = q(cell['representative']); keys = at(threshold)
            for family in FAMILIES:
                primary_rows.append({'cell_id': cell['id'], **aggregate(primary, family, [keys[iid] for iid in primary['images']], states)})
        anchor_rows = []
        for threshold in ANCHORS:
            keys = at(threshold); this_anchor = []
            for case in visible['cases']:
                for family in FAMILIES:
                    this_anchor.append({'threshold': w(threshold), **aggregate(case, family, [keys[iid] for iid in case['images']], states)})
            if threshold == ANCHORS[0]: regression_floor(this_anchor, freeze)
            anchor_rows.extend(this_anchor)
        curves = {}
        for index, role in enumerate(ROLES):
            curve = []
            for cell in role_cells[role]:
                keys = at(q(cell['representative'])); components = [states[keys[iid]]['analysis'] for iid in primary['images']]
                fp = sum(row['nominal_fp'][index] for row in components); fn = sum(row['nominal_fn'][index] for row in components)
                curve.append({'cell_id': cell['id'], 'false_positives': fp, 'misses': fn,
                              'predictions': sum(row['prediction_counts'][index] for row in components),
                              'matching_rank': sum(row['nominal']['ranks'][index] for row in components),
                              'references': sum(row['nominal_reference_count'] for row in components)})
            curves[role] = curve
        maximum_budget = max(curves[role][0]['predictions'] for role in ROLES)
        frontiers = compare_curves(curves[ROLES[0]], curves[ROLES[1]], maximum_budget)
        curve_path = output/'CURVES.json'; put(curve_path, {'role_cells': role_cells, 'curves': curves, 'comparison': frontiers})
        allocation = {'common_cells': common, 'anchors': list(map(w, ANCHORS)), 'cases': visible['cases'], 'families': list(FAMILIES)}
        result = {'artifact_id': 'reiyah.operating-policy.results', 'version': '0.1.0', 'status': 'exploratory',
            'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(), 'seconds': time.perf_counter()-tick,
            'freeze_sha256': file_binding(area/'FREEZE.json')['sha256'], 'allocation': allocation,
            'primary_rows': primary_rows, 'anchor_rows': anchor_rows, 'curves_source': file_binding(curve_path),
            'state_records': states.bindings, 'proof_records': proofs.bindings, 'world_banks': bank_bindings,
            'distinct_filtered_states': len(states), 'distinct_native_worlds': len(proofs), 'failures': {},
            'primary_decisions': dict(Counter(row['decision'] for row in primary_rows)),
            'anchor_decisions': dict(Counter(row['decision'] for row in anchor_rows)),
            'floor_regression_passed': True, 'human_seconds': None, 'economic_cost': None,
            'new_image_reads': 0, 'new_model_calls': 0, 'reserved_outcomes_accessed': 0,
            'independent_scientific_replication': False}
        put(output/'RESULTS.json', result)
        print(__import__('json').dumps({'primary_rows': len(primary_rows), 'anchor_rows': len(anchor_rows),
            'states': len(states), 'native_proofs': len(proofs), 'primary_decisions': result['primary_decisions'],
            'anchor_decisions': result['anchor_decisions'], 'seconds': result['seconds']}), flush=True)
    except Exception as exc:
        put(output/'FAILURE.json', {'state': 'incomplete', 'error': type(exc).__name__+': '+str(exc),
            'finished_utc': datetime.now(timezone.utc).isoformat(), 'seconds': time.perf_counter()-tick,
            'completed_states': states.bindings, 'completed_proofs': proofs.bindings,
            'complete_allocation_retained_in': 'STARTED.json', 'no_cases_dropped_or_relabelled': True})
        raise


if __name__ == '__main__':
    run(*sys.argv[1:])
