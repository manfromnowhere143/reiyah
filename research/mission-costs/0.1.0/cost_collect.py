"""Freeze and reconcile an explicitly bounded, private receipt inventory."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import shutil

from cost_math import decimal, download_totals, event_totals, inference_totals, micros, require, wire

HERE = Path(__file__).resolve().parent
SINGLES = {'reader-install.json', 'polars-install.json', 'FALLBACK_INSTALL.json',
           'FALLBACK_IMPORT_01.json', 'FALLBACK_THREAD_DIAGNOSTIC.json',
           'FALLBACK_THREAD_DIAGNOSTIC_02.json', 'WORKER_BOUNDARY_01.json',
           'WORKER_BOUNDARY_02.json', 'timing-csv-normalization-01.json'}
DURATIONS = {'NUSCENES_LICENSE_EXTRACTION.json': 'seconds',
             'FALLBACK_IMAGE_DECODE.json': 'seconds', 'ULTRALYTICS_EXTRACTION_02.json': 'seconds',
             'ADMISSION_TEST_01.json': 'tool_process_wall_seconds'}
STUDIES = ['public-predictions', 'reference-translation', 'translation-2d', 'loss-tradeoff',
           'reference-timing', 'reference-witness', 'operating-policy']


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text(), parse_float=Decimal)


def lines(path):
    return [json.loads(line, parse_float=Decimal) for line in path.read_text().splitlines()]


def put(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, indent=2, sort_keys=True, default=lambda v: wire(v)); handle.write('\n')


def safe(root, relative):
    require(isinstance(relative, str) and not Path(relative).is_absolute()
            and '..' not in Path(relative).parts, 'Source path must be relative without traversal')
    path = root / relative
    require(path.is_file() and not path.is_symlink(), 'Source must be a regular nonsymlink file')
    require(path.resolve().is_relative_to(root.resolve()), 'Source escapes owned packet')
    return path


def bind(root, path):
    relative = path.relative_to(root).as_posix()
    path = safe(root, relative)
    return {'path': relative, 'bytes': path.stat().st_size, 'sha256': digest(path)}


def inputs(root):
    selected = list((root / 'logs').glob('*.json')) + [root / 'logs/downloads.jsonl']
    selected += list(root.glob('PUSH-*.json'))
    selected += list((root / 'private').glob('export-*-REQUEST.json'))
    selected += list((root / 'private').glob('edgefirst-*-membership*.json'))
    selected += [p for name in ['PARQUET_READER_ATTEMPTS.json', 'POLARS_PACKET_STRUCTURE.json',
                 'ACQUISITION_CHECKPOINT_01.json', 'ACQUISITION_CHECKPOINT_02.json', 'EXPORT_CHECKPOINT_03.json']
                 if (p := root / 'private' / name).is_file()]
    selected += list((root / 'results').glob('*/RESULT.json'))
    if (root / 'private/projection-01/RESULT.json').is_file():
        selected.append(root / 'private/projection-01/RESULT.json')
    selected += [root / name for name in ['SESSION.json', 'checkpoints/INTERRUPTION_01.json',
                'private/FALLBACK_INFERENCE.jsonl', 'private/FALLBACK_RUNTIME_BINDING.json',
                'private/FALLBACK_ALLOCATION_FREEZE.json']]
    for study in STUDIES:
        p = root / 'candidate/research' / study / '0.1.0/summary.json'
        require(p.is_file(), 'Published summary absent: ' + study)
        selected.append(p)
    selected.append(root / 'candidate/research/public-predictions/0.1.0/costs.json')
    return sorted(set(selected))


def freeze(root, output):
    output = output.resolve()
    require(output.is_relative_to(root), 'Freeze must remain inside the owned packet')
    require(not output.exists(), 'Freeze output already exists')
    output.mkdir(parents=True)
    sources = [bind(root, path) for path in inputs(root)]
    projection = output / 'inputs'
    for row in sources:
        target = projection / row['path']; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(safe(root, row['path']), target)
        require(target.stat().st_size == row['bytes'] and digest(target) == row['sha256'], 'Input changed during snapshot')
    payloads = []
    for row in lines(root / 'logs/downloads.jsonl'):
        b = bind(root, safe(root, row['path']))
        require(b['sha256'] == row['sha256'] and b['bytes'] == row['received_bytes'], 'Payload receipt mismatch')
        payloads.append(b)
    code = [bind(root, p) for p in sorted(HERE.iterdir()) if p.suffix in ('.py', '.md')]
    record = {'artifact_id': 'reiyah.mission-costs.freeze', 'version': '0.1.0',
              'cutoff_utc': datetime.now(timezone.utc).isoformat(),
              'source_projection': projection.relative_to(root).as_posix(),
              'sources': sources, 'download_payloads': payloads, 'implementation': code,
              'reserved_outcomes_accessed': False, 'source_scope': 'Explicit receipt inventory; not every uninstrumented action'}
    put(output / 'FREEZE.json', record)
    return {'sources': len(sources), 'payloads': len(payloads), 'implementation': len(code),
            'freeze_sha256': digest(output / 'FREEZE.json'), 'cutoff_utc': record['cutoff_utc']}


def verify_bindings(root, frozen):
    seen = set()
    for section in ('sources', 'download_payloads', 'implementation'):
        for row in frozen[section]:
            require(set(row) == {'path', 'bytes', 'sha256'}, 'Unexpected binding fields')
            require((section, row['path']) not in seen, 'Duplicate source binding')
            seen.add((section, row['path']))
            base = source_root(root, frozen) if section == 'sources' else root
            path = safe(base, row['path'])
            require(path.stat().st_size == row['bytes'] and digest(path) == row['sha256'], 'Frozen source changed')


def source_root(root, frozen):
    relative = frozen.get('source_projection', '.')
    require(not Path(relative).is_absolute() and '..' not in Path(relative).parts, 'Invalid projection path')
    base = root / relative
    require(base.is_dir() and base.resolve().is_relative_to(root.resolve()), 'Source projection escapes packet')
    return base


def category(name):
    if name.startswith('export-'): return 'export'
    if 'control' in name or 'synthetic' in name or 'WORKER_BOUNDARY' in name: return 'controls_and_probes'
    if any(w in name for w in ('verification', 'replay', 'consistency', 'gate-b-check')): return 'verification'
    if any(w in name for w in ('figure', 'publish', 'normalization')): return 'packaging'
    if any(w in name for w in ('projection', 'metadata', 'preparation', 'freeze', 'qualification')): return 'preparation'
    if any(w in name for w in ('analysis', 'search', 'assay')): return 'comparison_and_analysis'
    return 'setup_and_diagnostics'


def event(identifier, source, group, row, finish='finished_utc', seconds='seconds', status=None):
    if status is None:
        status = ('failed' if row.get('error') is not None or row.get('exit_code', 0) != 0 else 'completed')
    return {'id': identifier, 'source': source, 'category': group, 'status': status,
            'started_utc': row['started_utc'], 'finished_utc': row[finish], 'seconds': wire(row[seconds])}


def time_fields(value, path=''):
    """Diagnostic references only; these copied/nested fields are never summed."""
    out = []
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(child, (dict, list)):
                out += time_fields(child, path + '/' + key)
            elif 'seconds' in key:
                require(child is None or type(child) in (Decimal, int, str), 'Unexpected timer type')
                if child is not None:
                    out.append({'field': path + '/' + key, 'seconds': wire(child)})
    elif isinstance(value, list):
        for i, child in enumerate(value): out += time_fields(child, path + '/' + str(i))
    return out


def reconcile(root, frozen):
    source_paths = {row['path']: row for row in frozen['sources']}
    projection = source_root(root, frozen)
    get = lambda name: read(safe(projection if name in source_paths else root, name))
    session = get('SESSION.json')
    events, durations, coverage, references = [], [], [], []
    launch_by_request, requests = {}, {}
    log_names = {Path(p).name for p in source_paths if p.startswith('logs/') and p.endswith('.json')}
    for name in sorted(log_names):
        source = 'logs/' + name; row = get(source)
        disposition = 'untimed_context_or_review'
        if name.endswith(('-COMPLETED.json', '_COMPLETED.json')):
            start_name = name.replace('COMPLETED.json', 'STARTED.json')
            require(start_name in log_names, 'Completion has no retained start')
            start = get('logs/' + start_name)
            require(all(key in row and row[key] == value for key, value in start.items()), 'Start/completion fields differ')
            events.append(event(source, source, category(name), row)); disposition = 'outer_process'
            if name.startswith('export-'): launch_by_request[row['request_sha256']] = row
        elif name.endswith(('-STARTED.json', '_STARTED.json')):
            require(name.replace('STARTED.json', 'COMPLETED.json') in log_names, 'Started phase has no completion')
            disposition = 'paired_start_not_added'
        elif name in SINGLES:
            events.append(event(source, source, category(name), row)); disposition = 'outer_process'
        elif name in DURATIONS:
            durations.append({'id': source, 'source': source, 'field': DURATIONS[name],
                              'seconds': wire(row[DURATIONS[name]]), 'interval': None})
            disposition = 'duration_only_not_added_to_union'
        elif name == 'CONTROLS_02.json':
            for check in row['checks']:
                durations.append({'id': source + ':' + check['name'], 'source': source,
                                  'field': check['name'] + '/test_seconds', 'seconds': wire(check['test_seconds']),
                                  'interval': None})
            disposition = 'duration_only_not_added_to_union'
        elif 'seconds' in row and name != 'FALLBACK_IMPORT_01_REVIEW.json':
            require(False, 'Unclassified outer timer: ' + name)
        if name == 'FALLBACK_IMPORT_01_REVIEW.json':
            original = get('logs/FALLBACK_IMPORT_01.json')
            for key in ('started_utc', 'finished_utc', 'seconds', 'exit_code'):
                require(row[key] == original[key], 'Review alias timing changed')
            disposition = 'alias_of_logs/FALLBACK_IMPORT_01.json'
        coverage.append({'source': source, 'sha256': source_paths[source]['sha256'], 'disposition': disposition})
        references += [{'source': source, **f, 'accounting': 'diagnostic_reference_not_additive'} for f in time_fields(row)]
    for source in sorted(source_paths):
        if source.startswith('PUSH-'):
            row = get(source)
            require(row.get('status') == 'pushed_and_read_back' or row.get('publisher_readback') is True,
                    'Publication receipt needs explicit status accounting')
            events.append(event(source, source, 'publication_and_readback', row))
            references += [{'source': source, **f, 'accounting': 'publication_internal_not_additive'}
                           for f in time_fields(row) if f['field'] != '/seconds']
        elif source.startswith('private/export-') and source.endswith('-REQUEST.json'):
            requests[source_paths[source]['sha256']] = get(source)
        elif source.startswith('candidate/research/'):
            references += [{'source': source.removeprefix('candidate/'), **f,
                            'accounting': 'published_snapshot_reference_not_additive'} for f in time_fields(get(source))]
        elif (source.startswith('private/edgefirst-') or source in
              ('private/PARQUET_READER_ATTEMPTS.json', 'private/POLARS_PACKET_STRUCTURE.json')):
            row = get(source)
            for timer in time_fields(row):
                parent = row
                for key in timer['field'].split('/')[1:-1]:
                    parent = parent[int(key)] if isinstance(parent, list) else parent[key]
                durations.append({'id': source + ':' + timer['field'], 'source': source,
                                  **timer, 'interval': None, 'reported_state': parent.get('state')})
        elif source.endswith('/RESULT.json') or source.startswith(('private/ACQUISITION_CHECKPOINT_',
                                                                   'private/EXPORT_CHECKPOINT_')):
            references += [{'source': source, **f, 'accounting': 'nested_or_snapshot_reference_not_additive'}
                           for f in time_fields(get(source))]
    for name, finish, field in [('private/FALLBACK_RUNTIME_BINDING.json', 'finished_utc', 'seconds'),
                               ('private/FALLBACK_ALLOCATION_FREEZE.json', 'completed_utc', 'hash_verification_seconds')]:
        events.append(event(name, name, 'custody', get(name), finish, field))
    downloads = lines(projection / 'logs/downloads.jsonl')
    download_rows = []
    for index, row in enumerate(downloads):
        identifier = 'download-' + str(index + 1).zfill(4)
        failed = row.get('error') is not None or row.get('http_status') not in (200, 206)
        events.append(event(identifier, 'logs/downloads.jsonl:' + str(index + 1), 'acquisition', row,
                            status='failed' if failed else 'completed'))
        application_error = None
        if row['path'].endswith('.json'):
            try:
                payload = get(row['path'])
                application_error = isinstance(payload, dict) and payload.get('error') is not None
            except (ValueError, UnicodeDecodeError):
                pass
        download_rows.append({'event_id': identifier, 'receipt_id': row['id'], 'body_bytes': row['received_bytes'],
                              'http_status': row.get('http_status'), 'transport_or_http_failed': failed,
                              'json_top_level_error_present': application_error,
                              'source_admission_established_by_http': False})
    inference = inference_totals(lines(projection / 'private/FALLBACK_INFERENCE.jsonl'), requests, launch_by_request)
    amounts = download_totals(downloads)
    require(amounts['physical_received_body_bytes'] <= session['resource_limits']['new_download_bytes'], 'Download cap exceeded')
    require(decimal(inference['charged_prediction_seconds']) <= session['resource_limits']['cumulative_inference_seconds'], 'Inference cap exceeded')
    require(inference['models_with_calls'] <= session['resource_limits'].get('models', 2), 'Model cap exceeded')
    require(inference['distinct_images'] <= session['resource_limits'].get('maximum_development_images', 64), 'Image cap exceeded')
    totals = event_totals(events, session['started_utc'], frozen['cutoff_utc'])
    interruption = get('checkpoints/INTERRUPTION_01.json')
    continuity = {'session_elapsed_seconds': wire(Decimal(micros(frozen['cutoff_utc']) - micros(session['started_utc'])) / 1000000),
                  'recorded_excluded_gap_seconds': None, 'remaining_window_is_not_verified_useful_time': True}
    if interruption:
        gap_start = micros(interruption['last_retained_file_write_utc'])
        gap_end = micros(interruption['resumed_clock_observation_utc'])
        excluded = Decimal(gap_end - gap_start) / 1000000
        require(excluded == decimal(interruption['unobserved_gap_seconds_excluded']), 'Interruption duration mismatch')
        require(all(not (micros(row['started_utc']) < gap_end and micros(row['finished_utc']) > gap_start)
                    for row in events), 'Recorded cost interval intersects excluded gap; reconcile explicitly')
        continuity.update(recorded_excluded_gap_seconds=wire(excluded),
                          remaining_window_upper_bound_seconds=wire(decimal(continuity['session_elapsed_seconds']) - excluded),
                          earliest_adjusted_ten_hour_point=interruption['earliest_ten_hour_point_after_excluded_gap'])
    return {'artifact_id': 'reiyah.mission-costs.reconciliation', 'version': '0.1.0', 'status': 'exploratory',
            'cutoff_utc': frozen['cutoff_utc'], 'original_start_utc': session['started_utc'],
            'source_bindings': len(source_paths), 'log_receipts': len(log_names), 'coverage': coverage,
            'events': events, 'outer_totals': totals, 'duration_only': durations,
            'diagnostic_timer_references': references, 'download_rows': download_rows,
            'downloads': amounts, 'inference': inference, 'resource_limits': session['resource_limits'],
            'continuity': continuity,
            'human_seconds': None, 'full_economic_cost': None, 'total_useful_work_seconds': None,
            'reserved_images_closed': 1433, 'new_inference_calls': 0,
            'unknowns': ['Uninstrumented coding, research, review, integration and commands',
                         'Early extraction and other attempts lacking timers; recorded reader durations are retained separately',
                         'Human inspection, adjudication, customer delays and demand',
                         'Historical acquisition/setup of reused runtimes, images and metadata',
                         'Network bytes outside retained HTTP response bodies',
                         'Hardware depreciation, electricity, prices and billing'],
            'not_total_work_or_savings_evidence': True, 'independent_replication': False}


def main():
    p = argparse.ArgumentParser(); p.add_argument('--root', type=Path, required=True)
    p.add_argument('--freeze', type=Path); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(); root = args.root.resolve()
    if args.freeze is None:
        print(json.dumps(freeze(root, args.output), sort_keys=True)); return
    frozen = read(args.freeze); verify_bindings(root, frozen)
    report = reconcile(root, frozen)
    require(not args.output.exists(), 'Report output already exists')
    args.output.mkdir(parents=True)
    report['freeze_sha256'] = digest(args.freeze)
    put(args.output / 'RECONCILIATION.json', report)
    print(json.dumps({'outer_totals': report['outer_totals'], 'downloads': report['downloads'],
                      'inference': report['inference'], 'report_sha256': digest(args.output / 'RECONCILIATION.json')}, sort_keys=True))


if __name__ == '__main__':
    main()
