"""Export verified derived results without raw geometry or native operands."""
import argparse
import csv
from datetime import datetime, timezone
from fractions import Fraction
import io
import json
from pathlib import Path

from planar_run import file_digest, read


def rational(value):
    return value['numerator'] + '/' + value['denominator']


def public_row(row):
    value = {key: row[key] for key in ('case_id', 'group', 'allocated_images', 'state', 'decision',
                                      'unresolved_reason', 'exact_extrema')}
    value['radius'] = rational(row['radius']); value['failed_images'] = len(row['analysis_failed_images'])
    for key in ('nominal_delta',):
        value[key] = rational(row[key]) if row[key] is not None else None
    for key in ('universal_bounds', 'attained_bounds'):
        for index, name in enumerate(('lower', 'upper')):
            value[key + '_' + name] = rational(row[key][index]) if row[key] is not None else None
    return value


def publish(area, destination):
    run = area / 'runs/planar-01'; results = read(run / 'RESULTS.json'); verification = read(run / 'VERIFICATION.json')
    if verification['results_sha256'] != file_digest(run / 'RESULTS.json') or not verification['all_complete_rows_verified']:
        raise ValueError('Result is not bound to successful verification')
    rows = [public_row(row) for row in results['cases']]
    if len(rows) != 584 or len({(row['case_id'], row['radius']) for row in rows}) != 584:
        raise ValueError('Incomplete or duplicate allocation')
    summaries = []
    for radius in results['radii']:
        selected = [row for row in rows if Fraction(row['radius']) == radius]
        summaries.append({'radius': radius, 'cases': len(selected),
                          'decisions': {state: sum(row['decision'] == state for row in selected)
                                        for state in ('supported', 'excluded', 'unresolved')},
                          'analysis_incomplete_cases': sum(row['state'] == 'analysis_incomplete' for row in selected),
                          'bound_gap_unresolved_cases': sum(row['unresolved_reason'] == 'bound_gap' for row in selected),
                          'opposite_world_cases': sum(row['unresolved_reason'] == 'opposite_worlds' for row in selected),
                          'primary': next(row for row in selected if row['group'] == 'primary')})
    bracket = results['primary_bracket']
    public_bracket = {key: bracket[key] for key in ('state', 'initial', 'final', 'maximum_steps', 'claim')}
    public_bracket['initial_rows'] = [public_row(row) for row in bracket['initial_rows']]
    public_bracket['steps'] = [{**{key: step[key] for key in ('step', 'before', 'midpoint', 'reused_radius', 'outcome', 'after')},
                               'row': public_row(step['row'])} for step in bracket['steps']]
    receipts = []
    for path in sorted((area.parents[1] / 'logs').glob('planar-*-COMPLETED.json')):
        record = read(path)
        receipts.append({'name': path.name, 'sha256': file_digest(path), **{key: record[key] for key in
                         ('started_utc', 'finished_utc', 'seconds', 'exit_code')}})
    totals = {'basis_seconds': 0.0, 'search_seconds': 0.0, 'native_compile_seconds': 0.0,
              'native_proposal_seconds': 0.0, 'native_check_seconds': 0.0,
              'evaluated_points': 0, 'edge_envelope_calls': 0, 'native_proofs_charged_once': 0}
    for entry in results['preparation_entries']:
        record = read(run / entry['path'])
        if record['state'] == 'complete': totals['basis_seconds'] += record['basis']['seconds']
    paid = set()
    for key in results['batch_order']:
        for entry in results['batches'][key]['records']:
            record = read(run / entry['path']); totals['search_seconds'] += record['seconds']
            for counter in ('evaluated_points', 'edge_envelope_calls'): totals[counter] += record.get(counter, 0)
            for proof_key in record.get('new_native_proofs', []):
                if proof_key in paid: raise ValueError('Repeated proof charged twice')
                paid.add(proof_key); cost = record['proofs'][proof_key]['timing']
                for short in ('compile', 'proposal', 'check'): totals['native_' + short + '_seconds'] += cost[short + '_seconds']
    totals['native_proofs_charged_once'] = len(paid)
    summary = {'artifact_id': 'reiyah.translation-2d.public-summary', 'version': '0.1.0', 'status': 'exploratory',
               'derived_data_terms': 'CC BY-NC-SA 4.0 and retained Motional Dataset Terms; see DISTRIBUTION.md',
               'inputs': {name: file_digest(path) for name, path in [('freeze', area / 'FREEZE.json'),
                         ('results', run / 'RESULTS.json'), ('verification', run / 'VERIFICATION.json')]},
               'allocated_images': 64, 'dependent_cases': 73, 'case_radius_rows': 584, 'summaries': summaries,
               'primary_bracket': public_bracket, 'search_totals': results['totals'], 'verification_totals': verification['totals'],
               'synthetic_controls': 33, 'internal_search_seconds': results['seconds'],
               'internal_verification_seconds': verification['seconds'], 'nested_costs_not_additive': totals,
               'known_process_receipts': receipts, 'cost_snapshot_utc': datetime.now(timezone.utc).isoformat(),
               'model_inference_calls': 0, 'new_download_bytes': 0, 'reserved_outcomes_accessed': 0,
               'human_seconds': None, 'full_economic_cost': None, 'independent_scientific_replication': False}
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
    buffer = io.StringIO(newline=''); writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader(); writer.writerows(rows); (destination / 'results.csv').write_text(buffer.getvalue())
    return {'rows': len(rows), 'radii': len(summaries), 'totals': totals}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--area', type=Path, required=True); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); print(json.dumps(publish(args.area.resolve(), args.output.resolve())))
