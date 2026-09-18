"""Bind final accounting additions; retain new-study timers without double charging."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time


def need(ok, message):
    if not ok: raise ValueError(message)


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text(), parse_float=Decimal)
def utc(): return datetime.now(timezone.utc).isoformat()


def put(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, default=lambda v: format(v, 'f')); stream.write('\n')


def freeze(root, area):
    need(not area.exists(), 'Final appendix already exists'); area.mkdir(parents=True)
    paths = {
        'private/mission-costs-01/report-02/RECONCILIATION.json': 'core',
        'private/mission-costs-01/report-02/VERIFICATION.json': 'core_verification',
        'private/mission-costs-01/supplement-report-01/SUPPLEMENT.json': 'supplement',
        'private/mission-costs-01/supplement-report-01/VERIFICATION.json': 'supplement_verification',
        'private/mission-costs-01/OUTCOMES-02.json': 'outcome_inventory',
        'private/mission-costs-01/FOLLOWUP-OUTCOMES-02.json': 'outcome_followup_inventory',
        'private/mission-costs-01/SNAPSHOT_02_LAUNCH.json': 'additional_outer:preparation',
        'logs/cost-reconcile-02-COMPLETED.json': 'additional_outer:accounting',
        'logs/cost-verify-02-COMPLETED.json': 'additional_outer:verification',
        'private/operating-witness-01/CSV_NORMALIZATION.json': 'additional_outer:packaging',
        'private/operating-witness-01/PUBLICATION_CORRECTION.json': 'additional_outer:packaging',
        'private/operating-witness-01/analysis/RESULTS.json': 'nested:operating-witness-analysis-01',
        'private/operating-witness-01/VERIFICATION.json': 'nested:operating-witness-verify-01',
        'candidate/research/operating-witness/0.1.0/summary.json': 'published_snapshot_alias',
        'logs/operating-witness-analysis-01-COMPLETED.json': 'owner',
        'logs/operating-witness-verify-01-COMPLETED.json': 'owner',
        'private/mission-costs-01/TOOL_OBSERVATIONS.json': 'tool_duration_only'}
    result = read(root / 'private/operating-witness-01/analysis/RESULTS.json')
    for section in ('refined_states', 'new_proofs'):
        for entry in result[section]:
            path = Path(entry['path']); need(path.is_relative_to(root), 'New timer source escapes packet')
            need(sha(path) == entry['sha256'] and path.stat().st_size == entry['bytes'], 'New-study source changed')
            paths[path.relative_to(root).as_posix()] = 'nested_or_copied:operating-witness-analysis-01'
    records = []
    for name, role in sorted(paths.items()):
        path = root / name; need(path.is_file() and not path.is_symlink(), 'Appendix input absent')
        target = area / 'inputs' / name; target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(path, target)
        need(sha(path) == sha(target), 'Input changed during copy')
        records.append({'path': name, 'role': role, 'bytes': target.stat().st_size, 'sha256': sha(target)})
    code = Path(__file__).resolve(); shutil.copyfile(code, area / code.name)
    put(area / 'FREEZE.json', {'artifact_id': 'reiyah.mission-costs.final-appendix-freeze', 'version': '0.1.0',
        'cutoff_utc': utc(), 'inputs': records, 'implementation_sha256': sha(code), 'reserved_images_closed': 1433})
    print({'bindings': len(records), 'freeze_sha256': sha(area / 'FREEZE.json')})


def checked_inputs(area):
    frozen = read(area / 'FREEZE.json'); need(sha(Path(__file__)) == frozen['implementation_sha256'], 'Appendix code changed')
    values = {}
    for row in frozen['inputs']:
        path = area / 'inputs' / row['path']; need(path.stat().st_size == row['bytes'] and sha(path) == row['sha256'],
                                                'Final appendix source changed')
        values[row['path']] = read(path)
    return frozen, values


def report(root, area, output):
    from cost_math import event_totals
    from cost_collect import time_fields
    from cost_verify import sweep_seconds
    tick = time.perf_counter(); frozen, values = checked_inputs(area)
    role = {row['role']: values[row['path']] for row in frozen['inputs'] if not row['role'].startswith('additional_outer:')}
    core = role['core']; supplemental = role['supplement']
    core_path = area / 'inputs/private/mission-costs-01/report-02/RECONCILIATION.json'
    need(role['core_verification']['report_sha256'] == sha(core_path), 'Core verification/report mismatch')
    need(role['supplement_verification']['report_sha256'] ==
         sha(area / 'inputs/private/mission-costs-01/supplement-report-01/SUPPLEMENT.json'), 'Supplement mismatch')
    events, nested = [], []
    for entry in frozen['inputs']:
        value = values[entry['path']]; kind = entry['role']
        if kind.startswith('additional_outer:'):
            need(value.get('exit_code', 0) == 0, 'Additional failed process needs explicit status accounting')
            events.append({'id': 'appendix:' + entry['path'], 'source': entry['path'], 'category': kind.split(':')[1],
                           'status': 'completed', 'started_utc': value['started_utc'],
                           'finished_utc': value['finished_utc'], 'seconds': format(value['seconds'], 'f')})
        elif kind.startswith(('nested:', 'nested_or_copied:')) or kind == 'published_snapshot_alias':
            nested.extend({'source': entry['path'], 'accounting': kind, **timer} for timer in time_fields(value))
    need(len(events) == 5, 'Additional outer allocation changed')
    combined = core['events'] + events
    totals = event_totals(combined, core['original_start_utc'], frozen['cutoff_utc'])
    need(sweep_seconds(combined) == Decimal(totals['interval_union_seconds']), 'Separate interval sweep differs')
    tools = role['tool_duration_only']['observations']
    for row in tools:
        need(row['interval'] is None and Fraction(row['seconds']) >= 0, 'Tool observation invents interval')
    result = {'artifact_id': 'reiyah.mission-costs.final-appendix', 'version': '0.1.0',
              'cutoff_utc': frozen['cutoff_utc'], 'freeze_sha256': sha(area / 'FREEZE.json'),
              'core_report_sha256': sha(core_path), 'additional_outer_events': events,
              'combined_outer_totals': totals, 'separate_endpoint_sweep_matches': True,
              'nested_new_study_timer_references': nested, 'tool_duration_only_observations': tools,
              'duration_only_totals': {
                  'core_records': len(core['duration_only']),
                  'core_seconds': format(sum((Decimal(r['seconds']) for r in core['duration_only']), Decimal(0)), 'f'),
                  'supplement_reader_records': supplemental['additional_reader_duration_only_records'],
                  'supplement_reader_seconds': supplemental['additional_reader_duration_token_sum_seconds'],
                  'supplement_failed_tool_records': supplemental['failed_tool_duration_only_records'],
                  'supplement_failed_tool_seconds': supplemental['failed_tool_duration_token_sum_seconds'],
                  'additional_tool_records': len(tools),
                  'additional_tool_seconds': format(sum((Decimal(r['seconds']) for r in tools), Decimal(0)), 'f')},
              'no_duration_only_or_nested_value_added_to_outer_union': True,
              'post_cutoff_work_not_included_here': True, 'human_seconds': None, 'full_economic_cost': None,
              'total_useful_work_seconds': None, 'reserved_images_closed': 1433,
              'independent_scientific_replication': False, 'internal_seconds': time.perf_counter() - tick}
    need('/Users/' not in json.dumps(result, default=str), 'Private path in appendix')
    put(output, result)
    print({'outer_events': totals['events'], 'interval_union_seconds': totals['interval_union_seconds'],
           'nested_timer_references': len(nested), 'report_sha256': sha(output)})


def verify(area, path, output):
    from cost_verify import sweep_seconds
    tick = time.perf_counter(); frozen, values = checked_inputs(area); actual = read(path)
    base = values['private/mission-costs-01/report-02/RECONCILIATION.json']; events = list(base['events'])
    extras = {entry['path']: values[entry['path']] for entry in frozen['inputs'] if entry['role'].startswith('additional_outer:')}
    need(set(extras) == {r['source'] for r in actual['additional_outer_events']}, 'Additional inventory differs')
    for event in actual['additional_outer_events']:
        original = extras[event['source']]
        need(all(event[k] == original[k] for k in ('started_utc', 'finished_utc')), 'Extra interval differs')
        need(Fraction(event['seconds']) == Fraction(original['seconds']), 'Extra duration differs'); events.append(event)
    need(len(events) == actual['combined_outer_totals']['events'], 'Combined event count differs')
    need(sum((Fraction(r['seconds']) for r in events), Fraction(0)) ==
         Fraction(actual['combined_outer_totals']['duration_sum_seconds']), 'Rational combined duration differs')
    need(sweep_seconds(events) == Decimal(actual['combined_outer_totals']['interval_union_seconds']), 'Union differs')
    for timer in actual['nested_new_study_timer_references']:
        value = values[timer['source']]
        for key in timer['field'].split('/')[1:]: value = value[int(key)] if isinstance(value, list) else value[key]
        need(Fraction(value) == Fraction(timer['seconds']), 'Nested source timer differs')
    need(actual['freeze_sha256'] == sha(area / 'FREEZE.json'), 'Appendix freeze differs')
    record = {'artifact_id': 'reiyah.mission-costs.final-appendix-verification', 'version': '0.1.0',
              'report_sha256': sha(path), 'freeze_sha256': sha(area / 'FREEZE.json'),
              'source_bindings_checked': len(frozen['inputs']), 'all_additional_interval_sources_match': True,
              'rational_outer_sum_matches': True, 'separate_endpoint_sweep_matches': True,
              'nested_timer_values_checked': len(actual['nested_new_study_timer_references']),
              'independent_scientific_replication': False, 'seconds': time.perf_counter() - tick}
    put(output, record); print(record)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--root', type=Path, required=True)
    p.add_argument('--area', type=Path, required=True); p.add_argument('--output', type=Path)
    p.add_argument('--freeze', action='store_true'); p.add_argument('--verify', type=Path); a = p.parse_args()
    sys.path.insert(0, str(a.root / 'candidate/research/mission-costs/0.1.0'))
    if a.freeze: freeze(a.root.resolve(), a.area.resolve())
    elif a.verify: verify(a.area.resolve(), a.verify, a.output)
    else: report(a.root.resolve(), a.area.resolve(), a.output)
