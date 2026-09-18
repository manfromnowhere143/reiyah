"""Retain public scalar results without private source or witness operands."""
from collections import Counter
import csv
from datetime import datetime
import json
from pathlib import Path
import sys

from witness_pool import q
from timing_metadata import file_binding, read, require


def scalar(value):
    return str(q(value)) if value is not None else None


def csv_file(path, rows):
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)


def run(area, destination):
    area = Path(area).resolve(); destination = Path(destination).resolve(); root = area.parent.parent
    freeze = read(area/'FREEZE.json'); result_path = area/'runs/witness-01/RESULTS.json'
    verification_path = area/'runs/witness-01/VERIFICATION.json'; result = read(result_path); verified = read(verification_path)
    require(verified['results_sha256'] == file_binding(result_path)['sha256']
            and verified['all_assigned_rows_accounted_for'] and verified['all_complete_rows_verified']
            and verified['universal_decisions_unchanged'], 'Verified full allocation required')
    parent = read(freeze['parent_results']); old = {(row['case_id'], row['contract']): row for row in parent['cases']}
    rows = []
    for value in result['cases']:
        previous = old[value['case_id'], value['contract']]; bounds = value['bounds']; attained = value['attained']
        rows.append({'case_id': value['case_id'], 'group': value['group'], 'contract': value['contract'],
            'allocated_images': value['allocated_images'], 'blocked_image_count': len(value['blocked_images']),
            'decision': value['decision'], 'previous_evidence': previous['evidence'], 'evidence': value['evidence'],
            'mean_lower': scalar(bounds[0]) if bounds else None, 'mean_upper': scalar(bounds[1]) if bounds else None,
            'previous_attained_lower': scalar(previous['attained'][0]) if attained else None,
            'previous_attained_upper': scalar(previous['attained'][1]) if attained else None,
            'attained_lower': scalar(attained[0]) if attained else None, 'attained_upper': scalar(attained[1]) if attained else None})
    components = []; pool_totals = Counter(); stops = Counter(); native_cost = Counter(); new_proofs = 0
    for entry in result['image_records']:
        if entry['state'] != 'refined': continue
        record = read(entry['path']); detail = record['refinement']; pool = detail['pool']
        if pool is not None:
            for key in ('base_count', 'axis_sweeps', 'axis_cells', 'unique_rectangles', 'empty_neighborhood_rectangles'):
                pool_totals[key] += pool[key]
            pool_totals['nonempty_neighborhoods'] += len(pool['neighborhoods']); pool_totals['searched_images'] += 1
        parent_record = read(detail['parent_source']['path'])
        for key, proof in record['proofs'].items():
            if key not in parent_record['proofs']:
                new_proofs += 1; native_cost.update(proof['native_timing'])
        for name, value in detail['contracts'].items():
            complete = value['state'] == 'complete'; search = value.get('search'); inherited = parent_record['contracts'][name]
            current = record['contracts'][name]
            if complete and value['reused_from'] is None: stops[search['stop']] += 1
            components.append({'image_id': entry['image_id'], 'contract': name, 'state': value['state'],
                'unknown_instances': current['unknown_count'], 'neighborhoods': len(pool['neighborhoods']) if pool else None,
                'unique_flow_measurements': search['unique_flow_measurements'] if complete else 0,
                'reused_from': value.get('reused_from'), 'stop': search['stop'] if complete else None,
                'universal_lower': scalar(current['bounds'][0]), 'universal_upper': scalar(current['bounds'][1]),
                'previous_attained_lower': scalar(inherited['attained'][0]), 'previous_attained_upper': scalar(inherited['attained'][1]),
                'attained_lower': scalar(current['attained'][0]), 'attained_upper': scalar(current['attained'][1])})
    phases = []; intervals = []
    for path in sorted((root/'logs').glob('witness-*-COMPLETED.json')):
        value = read(path); phases.append({key: value[key] for key in ('stage', 'started_utc', 'finished_utc', 'seconds', 'exit_code', 'error')})
        intervals.append((datetime.fromisoformat(value['started_utc']).timestamp(), datetime.fromisoformat(value['finished_utc']).timestamp()))
    merged = []
    for left, right in sorted(intervals):
        if not merged or left > merged[-1][1]: merged.append([left, right])
        else: merged[-1][1] = max(merged[-1][1], right)
    summary = {'artifact_id': 'reiyah.reference-witness.public-summary', 'version': '0.1.0', 'status': 'exploratory',
        'freeze_sha256': file_binding(area/'FREEZE.json')['sha256'], 'frozen_utc': freeze['frozen_utc'],
        'frozen_bindings': len(freeze['bindings']), 'results_sha256': file_binding(result_path)['sha256'],
        'verification_sha256': file_binding(verification_path)['sha256'], 'parent_commit': freeze['candidate_parent_commit'],
        'allocated_images': 64, 'allocated_cases': 73, 'allocated_rows': 292,
        'target_pairs': 14, 'target_images': 12, 'target_gap_rows': [row for row in rows if row['previous_evidence'] == 'bound_gap'],
        'primary': [row for row in rows if row['group'] == 'primary'],
        'decisions': dict(Counter(row['decision'] for row in rows)), 'case_evidence': verified['case_evidence'],
        'universal_decisions_unchanged': True, 'all_seven_target_rows_have_opposite_worlds': all(row['evidence'] == 'opposite_worlds' for row in rows if row['previous_evidence'] == 'bound_gap'),
        'pool_totals': dict(pool_totals), 'unique_flow_measurements': verified['unique_flow_measurements_checked'],
        'stop_counts_without_reuse': dict(stops), 'new_native_proofs': new_proofs,
        'all_native_proofs_checked': verified['unique_native_proofs_checked'], 'nested_new_native_seconds': dict(native_cost),
        'nested_verifier_native_check_seconds': verified['native_check_seconds'], 'retained_search_failures': result['failures'],
        'cost_snapshot': {'phases': phases, 'sum_recorded_process_seconds': sum(value['seconds'] for value in phases),
            'union_recorded_process_wall_seconds': sum(right-left for left, right in merged),
            'cutoff_latest_finished_utc': max(value['finished_utc'] for value in phases),
            'scope': 'Completed named phases before packaging; excludes this publisher, review, later checks and push. Nested times are not additive. Interactive engineering and full economic cost are not measured.'},
        'synthetic_unit_controls': 21, 'tiny_exhaustive_multiset_comparisons': 96,
        'new_downloaded_asset_bytes': 0, 'new_image_reads': 0, 'model_inference_calls': 0,
        'reserved_outcomes_accessed': 0, 'reserved_images_closed': 1433,
        'human_seconds': None, 'economic_cost': None, 'independent_scientific_replication': False,
        'all_arbitrary_rectangles_searched': False}
    csv_file(destination/'results.csv', rows); csv_file(destination/'components.csv', components)
    (destination/'summary.json').write_text(json.dumps(summary, sort_keys=True, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'rows': len(rows), 'components': len(components), 'new_native_proofs': new_proofs,
                      'summary_sha256': file_binding(destination/'summary.json')['sha256']}), flush=True)


if __name__ == '__main__':
    run(*sys.argv[1:])
