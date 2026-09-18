"""Frozen four-cell comparison; a parent service supplies requested answers.

Workers have an explicit visible packet and pipe-delivered responses. On this
Mac the worker sandbox also denies the private report sources and networking.
This is tested process separation, not independent human blinding.
"""
from datetime import datetime, timezone
import errno
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

from admission import closed, digest, encoded, require
from compare_math import (ARMS, FAMILIES, ROOT, VERSION, decision, interval, measure, ranking,
                          subject, validate_event, validate_image, wire_interval)


def utc():
    return datetime.now(timezone.utc).isoformat()


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def put(path, value):
    with Path(path).open('xb') as handle:
        handle.write(encoded(value))


def emit(value):
    print(json.dumps(value, separators=(',', ':'), allow_nan=False), flush=True)


def validate_visible(visible):
    closed(visible, ('artifact_id', 'version', 'images', 'cases', 'information'), 'visible packet')
    require(visible['artifact_id'] == 'reiyah.public-predictions.visible' and visible['version'] == VERSION,
            'VISIBLE', 'Unknown visible packet')
    require(len(visible['images']) == 64 and len(visible['cases']) == 73, 'ALLOCATION', 'Frozen case count differs')
    for image in visible['images']:
        validate_image(image)
    by_id = {image['id']: image for image in visible['images']}
    require(len(by_id) == 64 and [image['ordinal'] for image in visible['images']] == list(range(64)),
            'ALLOCATION', 'Image identity or order differs')
    expected = [{'id': image['id'], 'group': 'singleton', 'images': [image['id']]} for image in visible['images']]
    expected += [{'id': 'block-' + str(index // 8).zfill(2), 'group': 'block',
                  'images': [image['id'] for image in visible['images'][index:index + 8]]} for index in range(0, 64, 8)]
    expected.append({'id': 'all-64', 'group': 'primary', 'images': list(by_id)})
    require(visible['cases'] == expected, 'ALLOCATION', 'Frozen case membership differs')
    return by_id


def worker(visible_path, visible_sha256, arm):
    require(file_digest(visible_path) == visible_sha256, 'VISIBLE', 'Visible input changed')
    visible = json.loads(Path(visible_path).read_text()); by_id = validate_visible(visible)
    policy, stopping = ARMS[arm]; worker_tick = time.perf_counter()
    for family in FAMILIES:
        for case in visible['cases']:
            started, tick = utc(), time.perf_counter()
            images = [by_id[iid] for iid in case['images']]; measurements = {}; used = []
            choose_tick = time.perf_counter(); order = ranking(images, policy)
            timing = {'selection_seconds': time.perf_counter() - choose_tick, 'measurement_seconds': 0.0,
                      'stopping_seconds': 0.0, 'compile_seconds': 0.0, 'proposal_seconds': 0.0, 'check_seconds': 0.0}
            emit({'type': 'begin', 'case_id': case['id'], 'group': case['group'], 'family': family,
                  'arm': arm, 'started_utc': started, 'query_budget': len(order), 'ranking': order})
            while True:
                require(time.perf_counter() - worker_tick < 1800, 'BUDGET', 'Worker elapsed budget exceeded')
                stop_tick = time.perf_counter(); bounds = interval(images, measurements, family); outcome = decision(bounds)
                timing['stopping_seconds'] += time.perf_counter() - stop_tick
                emit({'type': 'checkpoint', 'sequence': len(used), 'bounds': wire_interval(bounds), 'decision': outcome})
                if outcome != 'unresolved' or len(used) == len(order):
                    break
                iid = order[len(used)]; image = by_id[iid]
                request = {'case_id': case['id'], 'arm': arm, 'family': family, 'sequence': len(used) + 1,
                    'image_id': iid, 'subject_sha256': subject(image), 'precision': 'whole_image_projection', 'method_version': VERSION}
                emit({'type': 'query', 'request': request})
                line = sys.stdin.readline(); require(bool(line), 'OBSERVATION', 'Observation service closed')
                event = json.loads(line); references = validate_event(event, request, image)
                measured = measure(image, references, family, stopping)
                for key, seconds in measured['timing'].items():
                    timing[key] += seconds
                measurements[iid] = measured; used.append(iid)
                emit({'type': 'measurement', 'image_id': iid, 'value': measured})
            emit({'type': 'result', 'case_id': case['id'], 'group': case['group'], 'arm': arm, 'family': family,
                'decision': outcome, 'bounds': wire_interval(bounds), 'queries': len(used), 'query_order': used,
                'query_budget': len(order), 'timing': timing, 'elapsed_seconds': time.perf_counter() - tick,
                'completed_utc': utc(), 'human_seconds': None, 'total_cost': None,
                'stop_reason': 'decision' if outcome in ('supported', 'excluded') else
                    'input_blocked' if outcome == 'input_blocked' else 'instrument_exhausted'})
    emit({'type': 'complete', 'worker_seconds': time.perf_counter() - worker_tick})


def sandbox_policy(visible_path):
    report_root = ROOT.parents[2]
    require(report_root.name == 'reports', 'ISOLATION', 'Expected owned report candidate')
    runtime = Path(sys.prefix).resolve()
    directories = {ROOT, runtime, runtime / 'bin', visible_path.parent}
    for path in (ROOT, runtime / 'bin', visible_path.parent):
        directories.update(path.parents)
    metadata_rules = ' '.join('(literal ' + json.dumps(str(path)) + ')' for path in sorted(directories))
    # Allow only public code, this process's selected existing runtime, and the
    # one prediction-only visible file within the report tree. No oracle path
    # or frozen source manifest is passed as an exception.
    return '\n'.join([
        '(version 1)', '(allow default)', '(deny network*)',
        '(deny file-read* (subpath ' + json.dumps(str(report_root)) + '))',
        '(deny file-read* (subpath "/Users/danielwahnich/workspace"))',
        '(allow file-read* (subpath ' + json.dumps(str(ROOT)) + '))',
        '(allow file-read* (subpath ' + json.dumps(str(runtime)) + '))',
        '(allow file-read* (literal ' + json.dumps(str(visible_path)) + '))',
        '(allow file-read-metadata ' + metadata_rules + ')',
        '(deny file-write*)'])


def probe(visible_path, denied_path):
    value = json.loads(Path(visible_path).read_text()); validate_visible(value)
    denied = False
    try:
        Path(denied_path).read_bytes()
    except PermissionError:
        denied = True
    require(denied, 'ISOLATION', 'Private-source canary was readable')
    with socket.socket() as connection:
        code = connection.connect_ex(('127.0.0.1', 9))
    require(code in (errno.EPERM, errno.EACCES), 'ISOLATION', 'Network probe was not permission-denied')
    emit({'visible_read': True, 'private_source_read_denied': True, 'network_permission_denied': True,
          'probe_is_independent_blinding': False})


def run(area, run_name='assay-01'):
    area = Path(area).resolve(); started, tick = utc(), time.perf_counter()
    freeze_path = area / 'FREEZE.json'; freeze = json.loads(freeze_path.read_text())
    for binding in freeze['bindings']:
        require(file_digest(binding['path']) == binding['sha256'], 'FREEZE', 'Frozen comparison source changed')
    require(run_name.replace('-', '').isalnum(), 'OUTPUT', 'Simple fresh run identifier required')
    run_dir = area / 'runs' / run_name; run_dir.mkdir(parents=True)
    visible_path = area / 'inputs/visible.json'; visible_sha = file_digest(visible_path)
    visible = json.loads(visible_path.read_text()); by_id = validate_visible(visible)
    by_case = {case['id']: case for case in visible['cases']}
    policy = sandbox_policy(visible_path)
    (run_dir / 'WORKER_SANDBOX.sb').write_text(policy + '\n')
    canary = area / 'custody/BOUNDARY_SENTINEL.txt'
    require(canary.read_text() == 'Private boundary probe; no reference data.\n', 'ISOLATION', 'Expected benign canary')
    prefix = ['/usr/bin/sandbox-exec', '-p', policy, sys.executable, '-B', str(Path(__file__).resolve())]
    env = {key: value for key, value in os.environ.items() if key in
           ('PATH', 'LANG', 'LC_ALL', 'PYTHONNOUSERSITE', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS')}
    probe_cmd = prefix + ['--probe', str(visible_path), str(canary)]
    probe_tick = time.perf_counter()
    boundary = subprocess.run(probe_cmd, capture_output=True, text=True, cwd=ROOT, env=env, timeout=60)
    put(run_dir / 'BOUNDARY_PROBE.json', {'command': probe_cmd, 'exit_code': boundary.returncode,
        'stdout': boundary.stdout, 'stderr': boundary.stderr, 'seconds': time.perf_counter() - probe_tick})
    require(boundary.returncode == 0, 'ISOLATION', 'Worker boundary probe failed; retained output')
    entries, workers = [], []
    for arm in ARMS:
        cmd = prefix + ['--worker', str(visible_path), visible_sha, arm]
        put(run_dir / (arm + '.COMMAND.json'), {'command': cmd, 'environment': env, 'cwd': str(ROOT)})
        worker_tick = time.perf_counter(); row = None; completed = False; seen_cases = set(); worker_seconds = None
        with (run_dir / (arm + '.stderr')).open('x') as error, (run_dir / (arm + '.journal.jsonl')).open('xb') as journal:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=error,
                                    text=True, cwd=ROOT, env=env)
            try:
                for line in proc.stdout:
                    require(len(line) <= 16 * 1024 * 1024, 'FRAME', 'Worker frame exceeds retained limit')
                    frame = json.loads(line)
                    journal.write(encoded({'channel': 'worker', 'frame': frame})); journal.flush()
                    if frame['type'] == 'begin':
                        require(row is None and frame['arm'] == arm and frame['family'] in FAMILIES,
                                'HISTORY', 'Invalid or overlapping case')
                        require(frame['case_id'] in by_case, 'HISTORY', 'Unknown case')
                        allocated = by_case[frame['case_id']]
                        expected_order = ranking([by_id[iid] for iid in allocated['images']], ARMS[arm][0])
                        require(frame['group'] == allocated['group'] and frame['ranking'] == expected_order
                                and frame['query_budget'] == len(expected_order), 'HISTORY', 'Case membership or ranking changed')
                        key = (frame['family'], frame['case_id'])
                        require(key not in seen_cases, 'HISTORY', 'Repeated case')
                        seen_cases.add(key); row = {'begin': frame, 'history': []}; seen = set()
                    elif frame['type'] == 'query':
                        require(row is not None, 'HISTORY', 'Query outside case')
                        request = frame['request']; iid = request['image_id']
                        require(iid in by_id and iid not in seen and request['subject_sha256'] == subject(by_id[iid]),
                                'OBSERVATION', 'Duplicate, unknown or wrong-subject query')
                        require(request['case_id'] == row['begin']['case_id'] and request['arm'] == arm
                                and request['family'] == row['begin']['family']
                                and request['sequence'] == len(seen) + 1
                                and row['begin']['ranking'][len(seen)] == iid,
                                'OBSERVATION', 'Query sequence or context differs')
                        seen.add(iid); requested, service_tick = utc(), time.perf_counter()
                        # Only this parent reads the requested answer. Neither
                        # the path nor another image's digest goes to the worker.
                        answer = json.loads((area / 'oracle' / (iid + '.json')).read_text())
                        require(answer['subject_sha256'] == request['subject_sha256'], 'OBSERVATION', 'Stale answer subject')
                        event = {'request': request, 'answer': answer['answer'], 'source_sha256': answer['source_sha256'],
                            'basis': 'published_annotation_projection', 'residual': request['family'],
                            'requested_utc': requested, 'returned_utc': utc(),
                            'cost': {'observation_units': 1, 'human_seconds': None, 'human_cost': None,
                                     'service_seconds': time.perf_counter() - service_tick}}
                        event['evidence_sha256'] = digest(event)
                        journal.write(encoded({'channel': 'service', 'event': event})); journal.flush()
                        row['history'].append({'type': 'observation', 'event': event})
                        proc.stdin.write(json.dumps(event, allow_nan=False) + '\n'); proc.stdin.flush()
                    elif frame['type'] in ('checkpoint', 'measurement'):
                        require(row is not None, 'HISTORY', 'Frame outside case')
                        row['history'].append(frame)
                    elif frame['type'] == 'result':
                        require(row is not None and frame['arm'] == arm and frame['case_id'] == row['begin']['case_id']
                                and frame['family'] == row['begin']['family'], 'HISTORY', 'Result context differs')
                        row['result'] = frame
                        name = arm + '.' + frame['family'] + '.' + frame['case_id'] + '.json'
                        put(run_dir / name, row)
                        entries.append({'path': name, 'sha256': file_digest(run_dir / name), 'result': frame})
                        journal.flush(); os.fsync(journal.fileno()); row = None
                    elif frame['type'] == 'complete':
                        require(row is None and len(seen_cases) == 73 * len(FAMILIES), 'HISTORY', 'Incomplete worker allocation')
                        completed = True; worker_seconds = frame['worker_seconds']
                    else:
                        raise ValueError('Unknown worker frame')
                proc.stdin.close(); returncode = proc.wait(timeout=30)
                require(returncode == 0 and row is None and completed, 'WORKER', 'Worker failed; journal and stderr retained')
            finally:
                if proc.poll() is None:
                    proc.kill(); proc.wait(timeout=30)
            workers.append({'arm': arm, 'worker_seconds': worker_seconds, 'process_seconds': time.perf_counter() - worker_tick})
        print(json.dumps({'arm': arm, 'completed_rows': len(entries)}), flush=True)
    require(len(entries) == len(ARMS) * len(FAMILIES) * len(visible['cases']), 'ALLOCATION', 'Assigned result omitted')
    put(run_dir / 'RESULTS.json', {'artifact_id': 'reiyah.public-predictions.comparison-results', 'version': VERSION,
        'started_utc': started, 'finished_utc': utc(), 'seconds': time.perf_counter() - tick,
        'freeze_sha256': file_digest(freeze_path), 'visible_sha256': visible_sha, 'workers': workers, 'rows': entries,
        'human_seconds': None, 'economic_cost': None, 'independent_replication': False})


if __name__ == '__main__':
    if sys.argv[1] == '--worker':
        worker(*sys.argv[2:])
    elif sys.argv[1] == '--probe':
        probe(*sys.argv[2:])
    else:
        require(sys.argv[1] == '--run', 'COMMAND', 'Use --run COMPARISON_AREA [RUN_NAME]')
        run(*sys.argv[2:])
