"""Package verified scalar operating curves without source detection joins."""
from collections import Counter
import csv
from datetime import datetime
import json
from pathlib import Path
import sys

from operating_sources import ROLES, file_binding, q, read, require
from operating_math import FAMILIES

NAMES = dict(zip(ROLES, ('YOLO11n', 'YOLO26n')))


def scalar(value):
    return str(q(value)) if value is not None else None


def csv_file(path, rows):
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)


def public_row(value):
    bounds, attained = value['bounds'], value['attained']
    return {'case_id': value['case_id'], 'group': value['group'], 'family': value['family'],
            'allocated_images': value['allocated_images'], 'blocked_image_count': len(value['blocked_images']),
            'decision': value['decision'], 'evidence': value['evidence'],
            'mean_lower': scalar(bounds[0]) if bounds else None, 'mean_upper': scalar(bounds[1]) if bounds else None,
            'attained_lower': scalar(attained[0]) if attained else None, 'attained_upper': scalar(attained[1]) if attained else None}


def cell_fields(cell):
    return {'cell_id': cell['id'], 'threshold_left': scalar(cell['left']), 'threshold_right': scalar(cell['right']),
            'left_closed': cell['left_closed'], 'right_closed': cell['right_closed']}


def cost_snapshot(root):
    phases = []; intervals = []
    for path in sorted((root/'logs').glob('operating-*-COMPLETED.json')):
        value = read(path); phases.append({key: value[key] for key in ('stage', 'started_utc', 'finished_utc', 'seconds', 'exit_code', 'error')})
        intervals.append((datetime.fromisoformat(value['started_utc']).timestamp(), datetime.fromisoformat(value['finished_utc']).timestamp()))
    merged = []
    for start, end in sorted(intervals):
        if not merged or start > merged[-1][1]: merged.append([start, end])
        else: merged[-1][1] = max(merged[-1][1], end)
    return {'phases': phases, 'sum_recorded_process_seconds': sum(row['seconds'] for row in phases),
            'union_recorded_wall_seconds': sum(end-start for start, end in merged),
            'cutoff_latest_finished_utc': max(row['finished_utc'] for row in phases),
            'scope': 'Completed named phases before publishing, including the first failed controls. Excludes this publisher, later figure/check/review/push and unmeasured interactive work. Internal timers and native costs are nested.'}


def run(area, destination):
    area = Path(area).resolve(); destination = Path(destination).resolve(); root = area.parent.parent
    freeze = read(area/'FREEZE.json'); output = area/'runs/operating-01'
    result_path = output/'RESULTS.json'; verification_path = output/'VERIFICATION.json'
    result, checked = read(result_path), read(verification_path); curves = read(result['curves_source']['path'])
    require(checked['results_sha256'] == file_binding(result_path)['sha256'] and checked['all_assigned_rows_verified']
            and checked['all_source_score_joins_verified'] and checked['floor_regression_passed'], 'Verified full study required')
    cells = {row['id']: row for row in result['allocation']['common_cells']}
    primary = [{**cell_fields(cells[row['cell_id']]), **public_row(row)} for row in result['primary_rows']]
    anchors = [{'threshold': scalar(row['threshold']), **public_row(row)} for row in result['anchor_rows']]
    individual = []; lookup = {}
    for role in ROLES:
        by_cell = {row['id']: row for row in curves['role_cells'][role]}
        lookup[role] = {row['cell_id']: row for row in curves['curves'][role]}
        for row in curves['curves'][role]:
            individual.append({'model': NAMES[role], **cell_fields(by_cell[row['cell_id']]),
                **{key: row[key] for key in ('false_positives', 'misses', 'predictions', 'matching_rank', 'references')},
                'unit_loss': row['false_positives']+row['misses']})
    frontier = []
    for role, points in zip(ROLES, curves['comparison']['frontiers']):
        for point in points:
            frontier.append({'model': NAMES[role], 'false_positives': point['false_positives'], 'misses': point['misses'],
                             'attained_cell_ids': ' '.join(point['cell_ids'])})
    budgets = []
    for row in curves['comparison']['false_positive_budgets']:
        a, b = row['roles']
        budgets.append({'false_positive_budget': row['false_positive_budget'], 'old_state': a['state'], 'new_state': b['state'],
            'old_minimum_misses': a['minimum_misses'], 'new_minimum_misses': b['minimum_misses'],
            'old_attained_cell_ids': ' '.join(a['cell_ids']), 'new_attained_cell_ids': ' '.join(b['cell_ids']),
            'miss_difference_old_minus_new': row['miss_difference_old_minus_new'], 'comparison': row['comparison']})
    minimum_losses = []
    for role, value in zip(ROLES, curves['comparison']['retrospective_minimum_unit_losses']):
        by_cell = {row['id']: row for row in curves['role_cells'][role]}
        minimum_losses.append({'model': NAMES[role], 'minimum_unit_loss': value['minimum_unit_loss'],
            'attained_cells': [{**cell_fields(by_cell[key]), **lookup[role][key]} for key in value['cell_ids']]})
    counts = {}
    for label, rows in [('primary_continuum', primary), ('diagnostic_anchors', anchors)]:
        counts[label] = {family: {'decisions': dict(Counter(row['decision'] for row in rows if row['family'] == family)),
                                 'evidence': dict(Counter(row['evidence'] for row in rows if row['family'] == family and row['evidence'] is not None))}
                         for family in FAMILIES}
    regions = []
    for row in budgets:
        if regions and regions[-1]['comparison'] == row['comparison']:
            regions[-1]['last_budget'] = row['false_positive_budget']
        else:
            regions.append({'first_budget': row['false_positive_budget'], 'last_budget': row['false_positive_budget'], 'comparison': row['comparison']})
    native_cost = Counter()
    for entry in result['proof_records']: native_cost.update(read(entry['path'])['native_timing'])
    grid = curves['comparison']['nominal_pair_grid']; qualification = read(freeze['score_qualification'])
    summary = {'artifact_id': 'reiyah.operating-policy.public-summary', 'version': '0.1.0', 'status': 'exploratory',
        'freeze_sha256': file_binding(area/'FREEZE.json')['sha256'], 'frozen_utc': freeze['frozen_utc'],
        'frozen_bindings': len(freeze['bindings']), 'policy_sha256': freeze['policy_sha256'],
        'results_sha256': file_binding(result_path)['sha256'], 'verification_sha256': file_binding(verification_path)['sha256'],
        'curves_and_full_pair_grid_sha256': result['curves_source']['sha256'],
        'allocated_images': 64, 'allocated_cases': 73, 'common_threshold_cells': checked['common_threshold_cells'],
        'individual_threshold_cells': checked['individual_threshold_cells'], 'primary_rows': len(primary), 'anchor_rows': len(anchors),
        'distinct_filtered_image_states': checked['filtered_states'], 'distinct_native_proofs': checked['native_proofs'],
        'nominal_pair_grid': {key: grid[key] for key in ('allocated_pairs', 'positive_pairs', 'nonpositive_pairs')},
        'source_qualification': qualification['roles'], 'counts': counts,
        'primary_anchors': [row for row in anchors if row['group'] == 'primary'],
        'retrospective_minimum_unit_losses': minimum_losses, 'frontier_points': [len(points) for points in curves['comparison']['frontiers']],
        'false_positive_budget_comparison_regions': regions, 'budget_69': budgets[69],
        'floor_regression_passed': True, 'retained_actual_failures': result['failures'],
        'controls': {'unit_tests': 31, 'exhaustive_tiny_frontier_comparisons': 81, 'full_synthetic_images': 64,
                     'full_synthetic_rows': 4130, 'full_synthetic_native_proofs': 1440},
        'first_control_failure': freeze['first_control_failure_retained'],
        'cost_snapshot': cost_snapshot(root), 'nested_native_seconds': dict(native_cost),
        'nested_verifier_native_check_seconds': checked['native_check_seconds'],
        'new_downloaded_asset_bytes': 0, 'new_image_reads': 0, 'model_inference_calls': 0,
        'reserved_outcomes_accessed': 0, 'reserved_images_closed': 1433, 'human_seconds': None, 'economic_cost': None,
        'scores_assumed_calibrated': False, 'thresholds_selected_for_deployment': False,
        'independent_scientific_replication': False,
        'limitations': ['Exposed development cohort and conditional projected references; no held-out policy validation.',
            'Only stricter filtering of retained postprocessed outputs; no below-floor completeness claim or new model execution.',
            'Finite inherited world banks may leave bound gaps at changed thresholds; no new geometric search.',
            'Overlapping rows and threshold cells are not independent decisions, frequencies or probabilities.',
            'Matched false-positive budgets and minimum losses use reference outcomes retrospectively; no deployment policy is selected.']}
    for name, rows in [('primary-thresholds', primary), ('anchor-cases', anchors), ('detector-curves', individual),
                       ('frontier', frontier), ('matched-fp-budgets', budgets)]: csv_file(destination/(name+'.csv'), rows)
    (destination/'summary.json').write_text(json.dumps(summary, sort_keys=True, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'primary_rows': len(primary), 'anchor_rows': len(anchors), 'individual_curve_rows': len(individual),
                      'frontier_rows': len(frontier), 'budget_rows': len(budgets), 'summary': file_binding(destination/'summary.json')}), flush=True)


if __name__ == '__main__':
    run(*sys.argv[1:])
