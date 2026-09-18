"""Extract derived tables from the verified private translation study."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rational(value):
    return value['numerator'] + '/' + value['denominator']


def publish(area, output):
    run = area / 'runs/translation-01'; result = read(run / 'RESULTS.json'); verification = read(run / 'VERIFICATION.json')
    if verification['results_sha256'] != digest(run / 'RESULTS.json') or not verification['all_assigned_rows_verified']:
        raise ValueError('Results do not match their verification receipt')
    rows = []
    for row in result['cases']:
        if row['state'] != 'complete':
            raise ValueError('This completed report must not silently omit a failed row')
        count = row['minimum_affected']['minimum_images']
        rows.append({**{key: row[key] for key in ('case_id', 'group', 'radius', 'allocated_images', 'state', 'decision')},
                     'nominal_delta': rational(row['nominal_delta']), 'lower': rational(row['bounds'][0]),
                     'upper': rational(row['bounds'][1]),
                     'minimum_images_for_excluding_world': count if count is not None else 'not_possible_in_family'})
    if len(rows) != 584 or len({(r['case_id'], r['radius']) for r in rows}) != 584:
        raise ValueError('Incomplete or duplicate allocation')
    summaries = []
    for radius in result['radii']:
        selected = [r for r in rows if r['radius'] == radius]
        summaries.append({'radius': radius, 'cases': len(selected),
                          'decisions': {state: sum(r['decision'] == state for r in selected)
                                        for state in ('supported', 'excluded', 'unresolved')},
                          'primary': next(r for r in selected if r['group'] == 'primary')})
    critical = {key: value for key, value in result['primary_critical_radius'].items()
                if key not in ('minimum_affected_at_witness_radius', 'extra_witness_seconds')}
    count = result['primary_critical_radius'].get('minimum_affected_at_witness_radius')
    if count is not None:
        critical['minimum_affected_at_witness_radius'] = {key: value for key, value in count.items() if key != 'image_ids'}
    receipts = []
    for path in sorted((area.parents[1] / 'logs').glob('translation-*-COMPLETED.json')):
        row = read(path)
        receipts.append({'name': path.name, 'sha256': digest(path), **{key: row[key] for key in
                         ('started_utc', 'finished_utc', 'seconds', 'exit_code')}})
    summary = {'artifact_id': 'reiyah.reference-translation.public-summary', 'version': '0.1.0', 'status': 'exploratory',
               'derived_data_terms': 'CC BY-NC-SA 4.0 and retained Motional Dataset Terms; see DISTRIBUTION.md',
               'inputs': {name: digest(path) for name, path in [('freeze', area / 'FREEZE.json'),
                         ('results', run / 'RESULTS.json'), ('verification', run / 'VERIFICATION.json')]},
               'allocated_images': 64, 'dependent_cases': 73, 'case_radius_rows': 584, 'failed_images': result['failures'],
               'summaries': summaries, 'primary_critical_radius': critical, 'search_totals': result['totals'],
               'verification_totals': verification['totals'], 'synthetic_controls': 26,
               'internal_search_seconds': result['seconds'], 'internal_verification_seconds': verification['seconds'],
               'known_process_receipts': receipts, 'cost_snapshot_utc': datetime.now(timezone.utc).isoformat(),
               'model_inference_calls': 0, 'new_download_bytes': 0, 'reserved_outcomes_accessed': 0,
               'human_seconds': None, 'full_economic_cost': None, 'independent_scientific_replication': False}
    output.mkdir(parents=True, exist_ok=True)
    (output / 'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
    buffer = io.StringIO(newline=''); writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader(); writer.writerows(rows); (output / 'results.csv').write_text(buffer.getvalue())
    return {'rows': len(rows), 'radii': len(summaries)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--area', type=Path, required=True); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); print(json.dumps(publish(args.area.resolve(), args.output.resolve())))
