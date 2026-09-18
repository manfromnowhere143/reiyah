"""Publish scalar row outcomes while retaining actual worlds privately."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import csv
from pathlib import Path

from operating_witness import file_binding, put, q, read, require


def wire(value):
    if value is None: return ''
    value = q(value)
    return str(value.numerator) + '/' + str(value.denominator)


def publish(session, area, output):
    result = read(area / 'analysis/RESULTS.json'); checked = read(area / 'VERIFICATION.json')
    frozen = read(area / 'FREEZE.json'); parent = read(frozen['parent_results'])
    require(checked['results_sha256'] == file_binding(area / 'analysis/RESULTS.json')['sha256']
            and checked['all_7707_parent_rows_checked'] and checked['all_universal_decisions_unchanged'],
            'Unverified result cannot be published')
    fields = ['section', 'row_index', 'cell_id', 'threshold', 'case_id', 'group', 'family',
              'allocated_images', 'blocked_image_count', 'decision', 'previous_evidence', 'evidence',
              'mean_lower', 'mean_upper', 'previous_attained_lower', 'previous_attained_upper',
              'attained_lower', 'attained_upper', 'selected_target']
    targets = {tuple(row) for row in frozen['target_rows']}; counts = {}; rows = []
    for section in ('primary_rows', 'anchor_rows'):
        for index, row in enumerate(result[section]):
            previous = parent[section][index]
            record = {k: row.get(k, '') for k in ('cell_id', 'threshold', 'case_id', 'group', 'family', 'allocated_images', 'decision')}
            record.update(section=section, row_index=index, blocked_image_count=len(row['blocked_images']),
                          previous_evidence=previous['evidence'] or '', evidence=row['evidence'] or '',
                          selected_target=(section, index) in targets)
            for prefix, values in [('mean', row['bounds']), ('previous_attained', previous['attained']), ('attained', row['attained'])]:
                for endpoint, suffix in enumerate(('lower', 'upper')):
                    record[prefix + '_' + suffix] = wire(values[endpoint]) if values is not None else ''
            rows.append(record)
        counts[section] = {'decisions': dict(Counter(r['decision'] for r in result[section])),
                           'evidence': dict(Counter(r['evidence'] or 'input_blocked' for r in result[section]))}
    with (output / 'results.csv').open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fields, lineterminator='\n'); writer.writeheader(); writer.writerows(rows)
    costs = []
    for phase in ['operating-witness-controls-01', 'operating-witness-freeze-01',
                  'operating-witness-analysis-01', 'operating-witness-verify-01']:
        receipt = read(session / 'logs' / (phase + '-COMPLETED.json'))
        costs.append({k: receipt[k] for k in ('stage', 'started_utc', 'finished_utc', 'seconds', 'exit_code', 'error')})
    summary = {'artifact_id': 'reiyah.operating-witness.public-summary', 'version': '0.1.0', 'status': 'exploratory',
               'snapshot_utc': datetime.now(timezone.utc).isoformat(), 'parent_commit': '1672e33718043dbfd0955f834faadc3c33714fd7',
               'freeze_sha256': file_binding(area / 'FREEZE.json')['sha256'], 'frozen_utc': frozen['frozen_utc'],
               'frozen_bindings': len(frozen['bindings']), 'results_sha256': checked['results_sha256'],
               'verification_sha256': file_binding(area / 'VERIFICATION.json')['sha256'],
               'source_outcomes_known_before_followup': True, 'target_rows': len(targets),
               'target_rows_now_with_opposite_worlds': len(checked['changed_target_rows']),
               'all_changed_rows': len(checked['changed_rows']), 'remaining_gap_rows': len(checked['remaining_gap_rows']),
               'allocated_rows': len(rows), 'counts': counts, 'allocated_filtered_states': len(frozen['target_states']),
               'states': checked['states'], 'improved_image_endpoints': checked['improved_image_endpoints'],
               'new_endpoint_proofs_checked': checked['new_endpoint_proofs_checked'],
               'inherited_proofs_bound_to_prior_verification': checked['inherited_proofs_bound_to_prior_verification'],
               'native_check_seconds_nested_in_verification': checked['native_check_seconds'],
               'pool_totals': checked['pool_totals'], 'retained_failures': result['failures'],
               'all_universal_decisions_unchanged': True, 'all_arbitrary_rectangles_searched': False,
               'synthetic_controls': 8, 'synthetic_case_compositions': 56,
               'phase_costs_before_publication': costs, 'internal_analysis_seconds': result['seconds'],
               'internal_verification_seconds': checked['seconds'], 'new_image_reads': 0, 'new_model_calls': 0,
               'new_download_bytes': 0, 'reserved_images_closed': 1433, 'reserved_outcomes_accessed': 0,
               'human_seconds': None, 'full_economic_cost': None, 'independent_scientific_replication': False}
    require('/Users/' not in str(summary), 'Private path in public summary')
    put(output / 'summary.json', summary)
    print({'rows': len(rows), 'changed_targets': summary['target_rows_now_with_opposite_worlds'],
           'remaining_gaps': summary['remaining_gap_rows']})


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--session', type=Path, required=True)
    p.add_argument('--area', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); publish(a.session.resolve(), a.area.resolve(), a.output.resolve())
