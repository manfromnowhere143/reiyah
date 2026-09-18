"""Publish derived temporal results without source or witness geometry."""
from collections import Counter
import csv
from datetime import datetime
from fractions import Fraction
import json
from pathlib import Path
import sys

from timing_bounds import CONTRACTS, q
from timing_metadata import file_binding, read, require


def fraction(value):
    return str(q(value)) if value is not None else None


def csv_file(path, rows):
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator='\n'); writer.writeheader(); writer.writerows(rows)


def costs(root):
    phases = []; intervals = []
    for path in sorted((root/'logs').glob('timing-*-COMPLETED.json')):
        value = read(path)
        phases.append({key: value[key] for key in ('stage', 'started_utc', 'finished_utc', 'seconds', 'exit_code', 'error')})
        intervals.append([datetime.fromisoformat(value['started_utc']).timestamp(), datetime.fromisoformat(value['finished_utc']).timestamp()])
    merged = []
    for start, end in sorted(intervals):
        if not merged or start > merged[-1][1]: merged.append([start, end])
        else: merged[-1][1] = max(merged[-1][1], end)
    return {'phases': phases, 'sum_recorded_process_seconds': sum(row['seconds'] for row in phases),
            'union_recorded_process_wall_seconds': sum(end-start for start, end in merged),
            'cutoff_latest_finished_utc': max(row['finished_utc'] for row in phases),
            'human_seconds': None, 'economic_cost': None,
            'scope': 'Snapshot of named retained processes, including failures; nested times are not additional wall cost. Interactive work and complete economics are not fully measured.'}


def run(area, destination):
    area = Path(area).resolve(); destination = Path(destination).resolve(); root = area.parent.parent
    freeze_path = area/'FREEZE.json'; freeze = read(freeze_path)
    result_path = area/'runs/timing-01/RESULTS.json'; verification_path = area/'runs/timing-01/VERIFICATION.json'
    result, verified = read(result_path), read(verification_path)
    require(verified['results_sha256'] == file_binding(result_path)['sha256'] and verified['all_images_complete'], 'Verified complete computation required')
    records = {entry['image_id']: read(entry['path']) for entry in result['image_records']}
    projected = {iid: read(value['projection_source']['path']) for iid, value in records.items()}
    image_rows = []; shifts = []; transitions = Counter(); stops = Counter(); candidate_evaluations = flow_calls = 0
    for iid, value in records.items():
        source = projected[iid]; pairs = value['projection_changes']['paired_changes']
        shifts.extend(q(row['maximum_coordinate_change']) for row in pairs); transitions.update(value['projection_changes']['counts'])
        for scope, search in value['searches'].items():
            if value['search_reuse'][scope] is None:
                candidate_evaluations += search['candidate_evaluations']; flow_calls += search['unique_flow_measurements']
                stops.update(world['stop'] for world in search['worlds'].values())
        image_rows.append({'image_id': iid, 'camera_minus_sample_us': source['camera_minus_sample_us'],
            'current_cars': len(source['current_census']), 'modeled_cars': sum(row['state'] == 'modeled' for row in source['objects']),
            'unknown_current_cars': len(value['current_unknown_instances']), 'preceding_census_state': source['preceding_census_state'],
            'preceding_only_cars': len(source['preceding_only_instances']) if source['preceding_only_instances'] is not None else None,
            'unknown_union_cars': len(value['union_unknown_instances']) if value['union_unknown_instances'] is not None else None,
            'known_eligible_references': len(value['known_references']),
            'paired_coordinate_changes': len(pairs), 'maximum_paired_coordinate_change': fraction(value['projection_changes']['maximum_coordinate_change']),
            'original_nominal_delta': fraction(value['original_nominal']['delta']),
            'known_only_world_delta': fraction(value['known_only_measurement']['delta'])})
    rows = []
    for value in result['cases']:
        bounds, attained = value['bounds'], value['attained']
        original = sum((q(records[iid]['original_nominal']['delta']) for iid in value['membership']), Fraction(0))/value['allocated_images']
        rows.append({'case_id': value['case_id'], 'group': value['group'], 'contract': value['contract'],
            'allocated_images': value['allocated_images'], 'blocked_image_count': len(value['blocked_images']),
            'decision': value['decision'], 'evidence': value['evidence'], 'mean_lower': fraction(bounds[0]) if bounds else None,
            'mean_upper': fraction(bounds[1]) if bounds else None, 'attained_lower': fraction(attained[0]) if attained else None,
            'attained_upper': fraction(attained[1]) if attained else None, 'original_nominal_mean': str(original)})
    by_contract = []
    for name in CONTRACTS:
        selected = [row for row in rows if row['contract'] == name]; counts = Counter(row['decision'] for row in selected)
        by_contract.append({'contract': name, 'rows': len(selected), **{key: counts[key] for key in ('supported', 'excluded', 'unresolved', 'input_blocked')},
                            'opposite_worlds': sum(row['evidence'] == 'opposite_worlds' for row in selected),
                            'bound_gaps': sum(row['evidence'] == 'bound_gap' for row in selected)})
    cutoffs = [Fraction(0), Fraction(1, 4), Fraction(1, 2), Fraction(1), Fraction(2), Fraction(4), Fraction(8), Fraction(16), Fraction(32), Fraction(64)]
    bins = [{'lower': str(a), 'upper': str(b), 'left_closed': True, 'right_closed': False,
             'objects': sum(a <= value < b for value in shifts)} for a, b in zip(cutoffs, cutoffs[1:])]
    bins.append({'lower': '64', 'upper': None, 'left_closed': True, 'right_closed': False, 'objects': sum(value >= 64 for value in shifts)})
    native_cost = Counter()
    for value in records.values():
        for proof in value['proofs'].values(): native_cost.update(proof['native_timing'])
    summary = {'artifact_id': 'reiyah.reference-timing.public-summary', 'version': '0.1.0', 'status': 'exploratory',
        'freeze_sha256': file_binding(freeze_path)['sha256'], 'frozen_utc': freeze['frozen_utc'], 'frozen_bindings': len(freeze['bindings']),
        'results_sha256': file_binding(result_path)['sha256'], 'verification_sha256': file_binding(verification_path)['sha256'],
        'allocated_images': 64, 'allocated_cases': 73, 'allocated_rows': 292, 'all_computations_complete': True,
        'by_contract': by_contract, 'primary': [row for row in rows if row['group'] == 'primary'],
        'unresolved_bound_gaps': [row for row in rows if row['evidence'] == 'bound_gap'],
        'source_object_counts': verified['source_object_counts'], 'numerical_diagnostics': verified['numerical_diagnostics'],
        'source_and_matching_totals': verified['totals'], 'eligibility_transitions': dict(transitions),
        'paired_projection_changes': {'objects': len(shifts), 'maximum_coordinate_change': str(max(shifts)) if shifts else None,
                                      'bins': bins, 'scope': 'Declared model change, not measured annotation error; pairs eligible in both projections only.'},
        'constructive_search': {'candidate_evaluations': candidate_evaluations, 'unique_flow_measurements': flow_calls,
                                'stop_counts_without_reused_searches': dict(stops), 'unique_native_proofs': verified['unique_native_proofs_checked'],
                                'nested_native_seconds': dict(native_cost)},
        'cost_snapshot': costs(root), 'new_downloaded_asset_bytes': 0, 'model_inference_calls': 0, 'new_image_reads': 0,
        'retained_session_downloaded_asset_bytes': 227930532, 'retained_session_charged_inference_seconds': 11.847570213954896,
        'reserved_outcomes_accessed': 0, 'reserved_images_closed': 1433, 'human_seconds': None, 'economic_cost': None,
        'independent_scientific_replication': False, 'empirical_annotation_error_rate': None,
        'controls': {'unit_tests': 51, 'cross_runtime_synthetic_images': 8, 'synthetic_case_contract_rows': 36, 'adversarial_probes': 13},
        'limits': ['Fixed current or adjacent-sample annotation census; unannotated objects outside both censuses are not covered.',
                   'Known motion-model projections are conditional premises, not corrected physical truth.',
                   'Optional-box bounds may be loose; seven case rows retain a bound gap.',
                   'Overlapping development cases do not measure independent decisions, human costs, safety or savings.']}
    csv_file(destination/'results.csv', rows); csv_file(destination/'image-summary.csv', image_rows)
    (destination/'summary.json').write_text(json.dumps(summary, sort_keys=True, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'rows': len(rows), 'image_rows': len(image_rows), 'by_contract': by_contract,
                      'summary_sha256': file_binding(destination/'summary.json')['sha256']}))


if __name__ == '__main__':
    run(*sys.argv[1:])
