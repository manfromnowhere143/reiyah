"""Publish derived development results without raw operands or source payloads.

The input is the owned private continuation area. This does not rerun inference,
query an oracle, establish source rights, or independently replicate an assay.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def fraction(value):
    return value['numerator'] + '/' + value['denominator']


def interval_union_seconds(intervals):
    """Measure occupied wall-clock intervals, counting intersections once."""
    ordered = sorted(intervals)
    total = 0.0
    left = right = None
    for start, end in ordered:
        if end < start:
            raise ValueError('Negative wall-clock interval')
        if right is None:
            left, right = start, end
        elif start > right:
            total += (right - left).total_seconds()
            left, right = start, end
        else:
            right = max(right, end)
    return total if right is None else total + (right - left).total_seconds()


def physical_download_totals(rows):
    """Each physical receipt counts, even when an early ordinal was reused."""
    paths = set()
    for row in rows:
        if row['path'] in paths:
            raise ValueError('Repeated receipt path requires explicit reconciliation')
        paths.add(row['path'])
        if type(row['received_bytes']) is not int or row['received_bytes'] < 0:
            raise ValueError('Invalid download byte count')
    return {'physical_receipts': len(rows),
            'new_download_bytes': sum(row['received_bytes'] for row in rows),
            'request_seconds_sum': sum(row['seconds'] for row in rows),
            'unsuccessful_http_or_transport_receipts': sum(
                row.get('error') is not None or row.get('http_status') not in (200, 206)
                for row in rows)}


def costs(area):
    logs = area / 'logs'
    download_path = logs / 'downloads.jsonl'
    downloads = [json.loads(line) for line in download_path.read_text().splitlines()]
    for row in downloads:
        path = area / row['path']
        if path.exists():
            if path.stat().st_size != row['received_bytes'] or digest(path) != row['sha256']:
                raise ValueError('Download receipt does not bind retained payload')
        elif row['received_bytes']:
            raise ValueError('Missing retained download payload')
    records = []
    for index, row in enumerate(downloads):
        records.append({'receipt': 'downloads.jsonl:' + str(index + 1),
                        'category': 'acquisition', 'seconds': row['seconds'],
                        'started_utc': row['started_utc'], 'finished_utc': row['finished_utc'],
                        'received_bytes': row['received_bytes'],
                        'http_status': row.get('http_status'),
                        'failed': row.get('error') is not None or row.get('http_status') not in (200, 206)})
    standalone = {'reader-install.json', 'polars-install.json', 'FALLBACK_INSTALL.json',
                  'FALLBACK_IMPORT_01.json', 'FALLBACK_THREAD_DIAGNOSTIC.json',
                  'FALLBACK_THREAD_DIAGNOSTIC_02.json', 'WORKER_BOUNDARY_01.json',
                  'WORKER_BOUNDARY_02.json'}
    for path in sorted(logs.glob('*.json')):
        if not (path.name.endswith('-COMPLETED.json') or path.name.endswith('_COMPLETED.json')
                or path.name in standalone):
            continue
        row = read(path)
        records.append({'receipt': path.name, 'receipt_sha256': digest(path),
                        'category': 'recorded_process', 'seconds': row['seconds'],
                        'started_utc': row['started_utc'], 'finished_utc': row['finished_utc'],
                        'exit_code': row['exit_code'],
                        'failed': row['exit_code'] != 0 or row.get('error') is not None})
    runtime_path = area / 'private/FALLBACK_RUNTIME_BINDING.json'
    runtime = read(runtime_path)
    records.append({'receipt': 'FALLBACK_RUNTIME_BINDING.json', 'receipt_sha256': digest(runtime_path),
                    'category': 'runtime_custody', **{key: runtime[key] for key in
                    ('started_utc', 'finished_utc', 'seconds')}})
    allocation_path = area / 'private/FALLBACK_ALLOCATION_FREEZE.json'
    allocation = read(allocation_path)
    records.append({'receipt': 'FALLBACK_ALLOCATION_FREEZE.json', 'receipt_sha256': digest(allocation_path),
                    'category': 'image_custody', 'started_utc': allocation['started_utc'],
                    'finished_utc': allocation['completed_utc'],
                    'seconds': allocation['hash_verification_seconds']})
    intervals = [(datetime.fromisoformat(row['started_utc']), datetime.fromisoformat(row['finished_utc']))
                 for row in records]
    duration_only = []
    for name, field in [('NUSCENES_LICENSE_EXTRACTION.json', 'seconds'),
                        ('FALLBACK_IMAGE_DECODE.json', 'seconds'),
                        ('ULTRALYTICS_EXTRACTION_02.json', 'seconds'),
                        ('ADMISSION_TEST_01.json', 'tool_process_wall_seconds')]:
        path = logs / name
        duration_only.append({'receipt': name, 'receipt_sha256': digest(path),
                              'seconds': read(path)[field], 'interval': None})
    early_controls = read(logs / 'CONTROLS_02.json')
    for row in early_controls['checks']:
        duration_only.append({'receipt': 'CONTROLS_02.json:' + row['name'],
                              'seconds': row['test_seconds'], 'interval': None,
                              'scope': 'Test runner reported duration; outer process unmeasured'})
    calls_path = area / 'private/FALLBACK_INFERENCE.jsonl'
    calls = [json.loads(line) for line in calls_path.read_text().splitlines()]
    return {'artifact_id': 'reiyah.public-predictions.known-costs', 'version': '0.1.0',
            'status': 'exploratory', 'snapshot_utc': datetime.now(timezone.utc).isoformat(),
            'downloads': {**physical_download_totals(downloads), 'ledger_sha256': digest(download_path)},
            'recorded_intervals': records,
            'recorded_interval_union_seconds': interval_union_seconds(intervals),
            'recorded_duration_sum_seconds': sum(row['seconds'] for row in records),
            'duration_only_records_not_added_to_union': duration_only,
            'nested_inference': {'calls': len(calls),
                                 'charged_prediction_seconds': sum(row['prediction_call_seconds'] for row in calls),
                                 'forward_seconds': sum(row['forward_seconds'] for row in calls),
                                 'decode_check_seconds': sum(row['decode_check']['seconds'] for row in calls),
                                 'ledger_sha256': digest(calls_path),
                                 'included_in_export_process_intervals': True},
            'not_a_total_work_measure': True,
            'human_seconds': None, 'full_economic_cost': None,
            'unknown_costs': ['Uninstrumented research, coding, source inspection and integration work',
                              'Early failed extraction and reader attempts without retained timing',
                              'Full historical cost of reused runtimes, imagery and annotation custody',
                              'Human preparation, inspection, adjudication and review',
                              'Local hardware depreciation, energy, billing and agreed cost rates'],
            'accounting': ['Do not add nested inference, matching, proof, checking or service durations to outer process time.',
                           'Union covers only recorded command/request intervals, not the session or complete work.',
                           'Duration-only records lack exact intervals and are reported separately.',
                           'Failed attempts and all physical download receipts are retained.'],
            'resource_limits': read(area / 'SESSION.json')['resource_limits']}


def csv_text(fields, rows):
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    return output.getvalue()


def build(area, output):
    assay = area / 'private/comparison-01/runs/assay-02'
    analysis = area / 'private/comparison-01/runs/analysis-01'
    result = read(assay / 'RESULTS.json'); replay = read(assay / 'REPLAY.json')
    full = read(analysis / 'RESULTS.json'); verified = read(analysis / 'VERIFICATION.json')
    if replay['results_sha256'] != digest(assay / 'RESULTS.json') or not replay['all_assigned_rows_verified']:
        raise ValueError('Scored results lack matching replay receipt')
    if verified['results_sha256'] != digest(analysis / 'RESULTS.json'):
        raise ValueError('Full-answer results lack matching verification receipt')
    scored_rows = []
    for entry in result['rows']:
        if digest(assay / entry['path']) != entry['sha256']:
            raise ValueError('Changed scored row')
        row = entry['result']
        scored_rows.append({**{key: row[key] for key in ('arm', 'family', 'case_id', 'group', 'decision', 'queries',
                                                       'query_budget', 'stop_reason', 'elapsed_seconds')},
                            'lower': fraction(row['bounds'][0]), 'upper': fraction(row['bounds'][1])})
    if len(scored_rows) != 876 or len({(r['arm'], r['family'], r['case_id']) for r in scored_rows}) != 876:
        raise ValueError('Incomplete or duplicate frozen allocation')
    analysis_rows = []
    for row in full['cases']:
        analysis_rows.append({**{key: row[key] for key in ('family', 'case_id', 'group', 'decision')},
                              'nominal_delta': fraction(row['nominal_delta']),
                              'lower': fraction(row['bounds'][0]), 'upper': fraction(row['bounds'][1]),
                              'minimum_queries': row['certificate_floor']['minimum_queries'],
                              'opposite_decisions_witnessed': row.get('opposite_decisions_witnessed', False),
                              **{arm + '_queries': row['actual_queries'][arm] for arm in 'ABCD'}})
    if len(analysis_rows) != 219 or len({(r['family'], r['case_id']) for r in analysis_rows}) != 219:
        raise ValueError('Incomplete or duplicate full-answer allocation')
    report = {'artifact_id': 'reiyah.public-predictions.summary', 'version': '0.1.0', 'status': 'exploratory',
              'derived_data_terms': 'CC BY-NC-SA 4.0 and retained Motional Dataset Terms; see DISTRIBUTION.md',
              'inputs': {name: digest(path) for name, path in
                         [('scored_results', assay / 'RESULTS.json'), ('replay', assay / 'REPLAY.json'),
                          ('analysis', analysis / 'RESULTS.json'), ('verification', analysis / 'VERIFICATION.json')]},
              'summaries': replay['summaries'], 'interactions': replay['interactions'],
              'replay_totals': replay['totals'], 'full_answer_verification': verified['totals'],
              'search_totals': full['search_totals'], 'search_failures': full['search_failures'],
              'primary_edit_sensitivity': {key: full['primary_edit_sensitivity'][key] for key in
                                           ('exact', 'lower_bound', 'upper_bound', 'scope', 'nominal_total_delta', 'witness_total_delta')},
              'primary_full_answer_rows': [r for r in analysis_rows if r['case_id'] == 'all-64'],
              'no_human_or_total_cost_savings_established': True, 'independent_scientific_replication': False,
              'reserved_outcome_images_accessed': 0, 'reserved_outcome_images_remaining': 1433}
    output.mkdir(parents=True, exist_ok=True)
    for name, value in [('summary.json', report), ('costs.json', costs(area))]:
        (output / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    (output / 'results.csv').write_text(csv_text(list(scored_rows[0]), scored_rows))
    (output / 'analysis.csv').write_text(csv_text(list(analysis_rows[0]), analysis_rows))
    return {'scored_rows': len(scored_rows), 'full_answer_rows': len(analysis_rows)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--area', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.area.resolve(), args.output.resolve())))
