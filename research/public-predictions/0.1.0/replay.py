"""Replay new query histories against conventional arithmetic and native proofs.

This is an independent execution of retained code/data, not independent
scientific replication. No model inference or new observations occur.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time

from admission import digest, encoded, require
from compare_math import (ARMS, FAMILIES, checker, decision, graph, interval, measure, ranking,
                          subject, validate_event, wire_interval)

# The retained predecessor also has an experiment.py. Select this exact file
# explicitly instead of relying on a search path changed by legacy imports.
_spec = importlib.util.spec_from_file_location('public_predictions_experiment', Path(__file__).with_name('experiment.py'))
_experiment = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_experiment)
validate_visible = _experiment.validate_visible


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def put(path, value):
    with Path(path).open('xb') as handle:
        handle.write(encoded(value))


def seconds(value):
    require(type(value) in (float, int) and math.isfinite(value) and value >= 0, 'COST', 'Finite nonnegative measured seconds required')
    return value


def replay_record(row, images, case, oracle):
    begin, result = row['begin'], row['result']; arm, family = begin['arm'], begin['family']
    require(arm in ARMS and family in FAMILIES and begin['case_id'] == case['id'] and begin['group'] == case['group'],
            'HISTORY', 'Unknown or changed context')
    by_id = {image['id']: image for image in images}; selected = [by_id[iid] for iid in case['images']]
    order = ranking(selected, ARMS[arm][0])
    require(begin['ranking'] == order and begin['query_budget'] == len(order), 'SELECTOR', 'Retained ranking or budget differs')
    measured, used, observations, proof_count = {}, [], 0, 0
    pending = None; checkpoint = None; next_kind = 'checkpoint'; expected_timing = Counter()
    service_seconds = 0.0
    for frame in row['history']:
        kind = frame['type']
        require(kind == next_kind, 'HISTORY', 'Observation/checkpoint order differs')
        if kind == 'checkpoint':
            bounds = interval(selected, measured, family); outcome = decision(bounds)
            require(frame['sequence'] == len(used) and frame['bounds'] == wire_interval(bounds) and frame['decision'] == outcome,
                    'STOPPING', 'Retained stopping bound or decision differs')
            checkpoint = frame
            next_kind = 'terminal' if outcome != 'unresolved' or len(used) == len(order) else 'observation'
        elif kind == 'observation':
            event = frame['event']; iid = order[len(used)]; image = by_id[iid]
            request = {'case_id': case['id'], 'arm': arm, 'family': family, 'sequence': len(used) + 1,
                'image_id': iid, 'subject_sha256': subject(image), 'precision': 'whole_image_projection', 'method_version': '0.1.0'}
            references = validate_event(event, request, image)
            retained = oracle(iid)
            require(retained['subject_sha256'] == request['subject_sha256'] and event['source_sha256'] == retained['source_sha256']
                    and references == retained['answer'], 'OBSERVATION', 'Served answer differs from frozen source')
            requested = datetime.fromisoformat(event['requested_utc']); returned = datetime.fromisoformat(event['returned_utc'])
            require(requested.tzinfo is not None and returned.tzinfo is not None and returned >= requested,
                    'COST', 'Observation wall interval differs')
            service_seconds += seconds(event['cost']['service_seconds'])
            pending = (iid, references); observations += 1; next_kind = 'measurement'
        elif kind == 'measurement':
            iid, references = pending; image = by_id[iid]; value = frame['value']
            require(frame['image_id'] == iid and iid not in measured, 'HISTORY', 'Wrong or repeated measured image')
            conventional = measure(image, references, family, 'conventional')
            for key in ('nominal', 'edit_bounds', 'deletion_bases'):
                require(value[key] == conventional[key], 'MATCHING', 'Retained matching or edit envelope differs')
            expected_removed = [base['removed_reference'] for base in conventional['deletion_bases']]
            if ARMS[arm][1] == 'native':
                require([proof['removed_reference'] for proof in value['proofs']] == expected_removed,
                        'PROOF', 'Missing or extra matching proof')
                for proof, base in zip(value['proofs'], conventional['deletion_bases']):
                    refs = [reference for reference in references if reference['id'] != proof['removed_reference']]
                    compiled = graph(image, refs)
                    require(proof['graph_sha256'] == digest(compiled), 'PROOF', 'Graph binding differs')
                    checker.check(compiled, proof['payload']); proof_count += 1
                    require(proof['payload']['result']['bounds']['lower'] == base['measurement']['delta']
                            and proof['payload']['result']['bounds']['upper'] == base['measurement']['delta'],
                            'PROOF', 'Native result differs from independent matching')
            else:
                require(value['proofs'] == [], 'METHOD', 'Unexpected proof cost in conventional arm')
            for key, cost in value['timing'].items():
                expected_timing[key] += seconds(cost)
            require(sum(value['timing'][key] for key in ('compile_seconds', 'proposal_seconds', 'check_seconds'))
                    <= value['timing']['measurement_seconds'] + 1e-9, 'COST', 'Nested computation cost exceeds measurement interval')
            measured[iid] = conventional; used.append(iid); pending = None; next_kind = 'checkpoint'
    require(next_kind == 'terminal' and checkpoint is not None and pending is None, 'HISTORY', 'Incomplete or prematurely stopped case')
    require(result['case_id'] == case['id'] and result['group'] == case['group'] and result['arm'] == arm
            and result['family'] == family and result['query_order'] == used and result['queries'] == len(used)
            and result['query_budget'] == len(order) and result['bounds'] == checkpoint['bounds']
            and result['decision'] == checkpoint['decision'], 'RESULT', 'Final result differs from replay')
    reason = 'decision' if result['decision'] in ('supported', 'excluded') else (
        'input_blocked' if result['decision'] == 'input_blocked' else 'instrument_exhausted')
    require(result['stop_reason'] == reason and result['human_seconds'] is None and result['total_cost'] is None,
            'RESULT', 'Stopping reason or unmeasured human cost changed')
    for key, cost in expected_timing.items():
        require(abs(seconds(result['timing'][key]) - cost) <= 1e-9, 'COST', 'Measured timing total differs')
    for value in result['timing'].values():
        seconds(value)
    nonoverlapping = sum(result['timing'][key] for key in ('measurement_seconds', 'selection_seconds', 'stopping_seconds'))
    require(nonoverlapping <= seconds(result['elapsed_seconds']) + 1e-9, 'COST', 'Case compute exceeds elapsed interval')
    return {'queries': observations, 'proofs': proof_count, 'checkpoints': sum(frame['type'] == 'checkpoint' for frame in row['history']),
            'service_seconds': service_seconds, 'decision': result['decision']}


def check_journal(path, retained):
    current, pending, complete, cases = None, None, False, 0
    with path.open() as handle:
        for line in handle:
            item = json.loads(line)
            require(not complete, 'JOURNAL', 'Journal has data after completion')
            if item['channel'] == 'service':
                require(current is not None and pending == item['event']['request'], 'JOURNAL', 'Unrequested service response')
                current['history'].append({'type': 'observation', 'event': item['event']}); pending = None
                continue
            require(item['channel'] == 'worker' and pending is None, 'JOURNAL', 'Worker skipped a requested response')
            frame = item['frame']; kind = frame['type']
            if kind == 'begin':
                require(current is None, 'JOURNAL', 'Overlapping journal case')
                current = {'begin': frame, 'history': []}
            elif kind == 'query':
                require(current is not None, 'JOURNAL', 'Query outside case'); pending = frame['request']
            elif kind in ('checkpoint', 'measurement'):
                require(current is not None, 'JOURNAL', 'Frame outside case'); current['history'].append(frame)
            elif kind == 'result':
                require(current is not None, 'JOURNAL', 'Result outside case'); current['result'] = frame
                key = (frame['arm'], frame['family'], frame['case_id'])
                require(key in retained and digest(current) == retained[key], 'JOURNAL', 'Incremental history differs from retained row')
                cases += 1; current = None
            elif kind == 'complete':
                require(current is None and cases == 219, 'JOURNAL', 'Incomplete arm journal'); complete = True
            else:
                raise ValueError('Unknown journal frame')
    require(complete and current is None and pending is None, 'JOURNAL', 'Truncated journal')
    return {'path': path.name, 'sha256': file_digest(path), 'cases': cases}


def run(area, run_name='assay-02'):
    area = Path(area).resolve(); run_dir = area / 'runs' / run_name
    started, tick = datetime.now(timezone.utc).isoformat(), time.perf_counter()
    freeze = json.loads((area / 'FREEZE.json').read_text())
    for binding in freeze['bindings']:
        require(file_digest(binding['path']) == binding['sha256'], 'FREEZE', 'Frozen input or implementation changed')
    result_path = run_dir / 'RESULTS.json'; manifest = json.loads(result_path.read_text())
    visible = json.loads((area / 'inputs/visible.json').read_text()); validate_visible(visible)
    require(manifest['freeze_sha256'] == file_digest(area / 'FREEZE.json')
            and manifest['visible_sha256'] == digest(visible), 'FREEZE', 'Result scope differs')
    cases = {case['id']: case for case in visible['cases']}
    expected = {(arm, family, case) for arm in ARMS for family in FAMILIES for case in cases}
    require(len(manifest['rows']) == len(expected), 'ALLOCATION', 'Allocated result omitted')
    totals = Counter(); seen, retained, outcomes, costs = set(), {}, {}, {}
    def oracle(iid):
        return json.loads((area / 'oracle' / (iid + '.json')).read_text())
    for entry in manifest['rows']:
        result = entry['result']; key = (result['arm'], result['family'], result['case_id'])
        require(key in expected and key not in seen, 'ALLOCATION', 'Unknown or duplicate result')
        seen.add(key)
        expected_name = '.'.join(key) + '.json'
        require(entry['path'] == expected_name and file_digest(run_dir / expected_name) == entry['sha256'],
                'BINDING', 'Result row identity differs')
        row = json.loads((run_dir / expected_name).read_text())
        require(row['result'] == result, 'BINDING', 'Index and row result differ')
        check = replay_record(row, visible['images'], cases[result['case_id']], oracle)
        retained[key] = digest(row); outcomes[key] = result
        for name in ('queries', 'proofs', 'checkpoints'):
            totals[name] += check[name]
        totals['service_seconds'] += check['service_seconds']
        costs[key] = check
    require(seen == expected, 'ALLOCATION', 'Result allocation incomplete')
    journals = [check_journal(run_dir / (arm + '.journal.jsonl'), retained) for arm in ARMS]
    interactions = {}
    for aa, bb in (('A', 'B'), ('C', 'D'), ('A', 'C'), ('D', 'B')):
        pairs = [(outcomes[(aa, family, case)], outcomes[(bb, family, case)]) for family in FAMILIES for case in cases]
        interactions[aa + '_vs_' + bb] = {
            'pairs': len(pairs), 'same_ordered_queries': sum(a['query_order'] == b['query_order'] for a, b in pairs),
            'same_query_count': sum(a['queries'] == b['queries'] for a, b in pairs),
            'same_decision': sum(a['decision'] == b['decision'] for a, b in pairs),
            'first_fewer_queries': sum(a['queries'] < b['queries'] for a, b in pairs),
            'second_fewer_queries': sum(a['queries'] > b['queries'] for a, b in pairs),
            'both_zero_queries': sum(a['queries'] == b['queries'] == 0 for a, b in pairs)}
    summaries = []
    for arm in ARMS:
        for family in FAMILIES:
            for group in ('singleton', 'block', 'primary', 'all_dependent_cases'):
                selected = [row for key, row in outcomes.items() if key[:2] == (arm, family)
                            and (group == 'all_dependent_cases' or row['group'] == group)]
                summary = {'arm': arm, 'family': family, 'group': group, 'cases': len(selected),
                    'decisions': dict(sorted(Counter(row['decision'] for row in selected).items())),
                    'queries': sum(row['queries'] for row in selected),
                    'direct_audit_queries': sum(row['query_budget'] for row in selected),
                    'distinct_queried_images': len({iid for row in selected for iid in row['query_order']}),
                    'timing': {key: sum(row['timing'][key] for row in selected) for key in selected[0]['timing']},
                    'elapsed_case_seconds': sum(row['elapsed_seconds'] for row in selected),
                    'service_seconds': sum(costs[(arm, family, row['case_id'])]['service_seconds'] for row in selected),
                    'human_seconds': None, 'full_cost': None}
                summaries.append(summary)
    report = {'artifact_id': 'reiyah.public-predictions.comparison-replay', 'version': '0.1.0',
        'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(), 'seconds': time.perf_counter() - tick,
        'results_sha256': file_digest(result_path), 'replay_implementation_sha256': file_digest(__file__),
        'rows': len(seen), 'totals': dict(totals),
        'interactions': interactions, 'summaries': summaries, 'journals': journals,
        'primary_results': [value for value in outcomes.values() if value['group'] == 'primary'],
        'all_assigned_rows_verified': True, 'independent_replication': False,
        'checked_native_proofs_are_independent_scientific_evidence': False}
    put(run_dir / 'REPLAY.json', report)
    print(json.dumps({'rows': len(seen), 'totals': dict(totals), 'seconds': report['seconds'], 'interactions': interactions}), flush=True)


if __name__ == '__main__':
    run(*sys.argv[1:])
