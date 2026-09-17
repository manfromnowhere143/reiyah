"""Four sequential policy workers; only the parent services private oracle queries.

This is dataflow isolation, not an OS sandbox or independent blinding. The workers
receive one visible input path and queried answers over stdin, never the oracle path.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from common import (ARMS, FAMILIES, VERSION, conventional_measure, decision, digest, file_digest,
                    interval, native_measure, need, put, ranking, subject, utc, validate_event,
                    wire_interval)


def emit(value):
    print(json.dumps(value, separators=(',', ':')), flush=True)


def worker(visible_path, arm):
    visible = json.loads(Path(visible_path).read_text())
    by_id = {im['id']: im for im in visible['images']}
    policy, stopping = ARMS[arm]
    worker_start = time.perf_counter()
    for family in FAMILIES:
        for case in visible['cases']:
            start = time.perf_counter(); started = utc()
            images = [by_id[i] for i in case['images']]
            measurements = {}; used = []
            tick = time.perf_counter(); order = ranking(images, policy)
            timing = {'selection_seconds': time.perf_counter() - tick, 'measurement_seconds': 0,
                      'stopping_seconds': 0, 'compile_seconds': 0, 'proposal_seconds': 0, 'check_seconds': 0}
            emit({'type': 'begin', 'case_id': case['id'], 'group': case['group'], 'family': family,
                  'arm': arm, 'started_utc': started, 'query_budget': len(order), 'ranking': order})
            while True:
                need(time.perf_counter() - worker_start < 600, 'Worker elapsed budget exceeded')
                tick = time.perf_counter(); bounds = interval(images, measurements, family)
                outcome = decision(bounds)
                timing['stopping_seconds'] += time.perf_counter() - tick
                emit({'type': 'checkpoint', 'sequence': len(used), 'bounds': wire_interval(bounds), 'decision': outcome})
                if outcome != 'unresolved' or len(used) == len(order):
                    break
                iid = order[len(used)]; image = by_id[iid]
                need(iid not in measurements, 'Repeated query')
                request = {'case_id': case['id'], 'arm': arm, 'family': family, 'sequence': len(used) + 1,
                           'image_id': iid, 'subject_sha256': subject(image), 'precision': 'whole_image_reference',
                           'method_version': VERSION}
                emit({'type': 'query', 'request': request})
                event = json.loads(sys.stdin.readline())
                references = validate_event(event, request)
                tick = time.perf_counter()
                measured = (native_measure if stopping == 'native' else conventional_measure)(image, references)
                timing['measurement_seconds'] += time.perf_counter() - tick
                for key, value in measured.get('timing', {}).items():
                    timing[key] += value
                measurements[iid] = measured; used.append(iid)
                emit({'type': 'measurement', 'image_id': iid, 'value': measured})
            emit({'type': 'result', 'case_id': case['id'], 'group': case['group'], 'arm': arm,
                  'family': family, 'decision': outcome, 'bounds': wire_interval(bounds), 'queries': len(used),
                  'query_order': used, 'query_budget': len(order), 'timing': timing,
                  'elapsed_seconds': time.perf_counter() - start,
                  'completed_utc': utc(), 'human_seconds': None, 'total_cost': None,
                  'stop_reason': 'decision' if outcome in ('supported', 'excluded') else
                                 'input_blocked' if outcome == 'input_blocked' else 'instrument_exhausted'})
    emit({'type': 'complete', 'worker_seconds': time.perf_counter() - worker_start})


def run(area):
    area = Path(area).resolve()
    run_dir = area / 'runs/assay-01'; run_dir.mkdir()
    started = utc(); tick = time.perf_counter()
    entries = []; workers = []
    visible_path = area / 'inputs/visible.json'
    visible = json.loads(visible_path.read_text())
    by_id = {im['id']: im for im in visible['images']}
    for arm in ARMS:
        cmd = [sys.executable, '-B', str(Path(__file__).resolve()), '--worker', str(visible_path), arm]
        worker_tick = time.perf_counter()
        env = os.environ.copy(); env.pop('PYTHONPATH', None)
        with (run_dir / (arm + '.stderr.txt')).open('x') as error:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=error,
                                    text=True, cwd=str(Path(__file__).parent), env=env)
            row = None
            for line in proc.stdout:
                frame = json.loads(line)
                if frame['type'] == 'begin':
                    need(row is None, 'Overlapping case')
                    row = {'begin': frame, 'history': []}; seen = set()
                elif frame['type'] == 'query':
                    request = frame['request']; iid = request['image_id']
                    need(iid not in seen and iid in by_id, 'Duplicate/unknown oracle request')
                    need(request['subject_sha256'] == subject(by_id[iid]), 'Wrong oracle subject')
                    need(request['case_id'] == row['begin']['case_id'] and request['arm'] == arm
                         and request['family'] == row['begin']['family'], 'Wrong oracle context')
                    seen.add(iid); service_tick = time.perf_counter(); requested = utc()
                    # The only run-time private-answer read is this requested singleton.
                    answer = json.loads((area / 'oracle' / (iid + '.json')).read_text())
                    need(answer['subject_sha256'] == request['subject_sha256'], 'Stale source applicability')
                    event = {'request': request, 'answer': answer['answer'], 'source_sha256': answer['source_sha256'],
                             'basis': 'published_correction_replay', 'residual': request['family'],
                             'requested_utc': requested, 'returned_utc': utc(),
                             'cost': {'observation_units': 1, 'human_seconds': None, 'human_cost': None,
                                      'service_seconds': time.perf_counter() - service_tick}}
                    event['evidence_sha256'] = digest(event)
                    row['history'].append({'type': 'observation', 'event': event})
                    proc.stdin.write(json.dumps(event) + '\n'); proc.stdin.flush()
                elif frame['type'] in ('checkpoint', 'measurement'):
                    need(row is not None, 'Frame outside case')
                    row['history'].append(frame)
                elif frame['type'] == 'result':
                    row['result'] = frame
                    name = arm + '.' + frame['family'] + '.' + frame['case_id'] + '.json'
                    put(run_dir / name, row)
                    entries.append({'path': name, 'sha256': file_digest(run_dir / name), 'result': frame})
                    row = None
                elif frame['type'] == 'complete':
                    workers.append({'arm': arm, 'worker_seconds': frame['worker_seconds'],
                                    'process_seconds': time.perf_counter() - worker_tick})
                else:
                    raise ValueError('Unknown worker frame')
            proc.stdin.close(); returncode = proc.wait()
            need(returncode == 0 and row is None, 'Worker failed; retain stderr and partial rows')
        print(json.dumps({'arm': arm, 'completed_rows': len(entries)}), flush=True)
    need(len(entries) == len(visible['cases']) * len(ARMS) * len(FAMILIES), 'Allocated case omitted')
    put(run_dir / 'RESULTS.json', {'artifact_id': 'reiyah.correction-observation.results', 'version': VERSION,
        'started_utc': started, 'completed_utc': utc(), 'seconds': time.perf_counter() - tick,
        'visible_sha256': file_digest(visible_path), 'freeze_sha256': file_digest(area / 'FREEZE.json'),
        'workers': workers, 'rows': entries})


if __name__ == '__main__':
    if sys.argv[1] == '--worker':
        worker(*sys.argv[2:])
    else:
        need(sys.argv[1] == '--run', 'Use --run AREA')
        run(sys.argv[2])
