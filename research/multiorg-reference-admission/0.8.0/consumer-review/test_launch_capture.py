"""Harmless process lifecycle controls; never calls the cohort main or window."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('reviewed_launcher', ROOT / 'run_remaining_cohort.py')
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
SOURCE_SHA = hashlib.sha256((ROOT / 'run_remaining_cohort.py').read_bytes()).hexdigest()
REAL_RUN = subprocess.run
REAL_POPEN = subprocess.Popen
ROWS = []


def alive(pid):
    result = REAL_RUN(['/bin/ps', '-o', 'stat=', '-p', str(pid)], capture_output=True, text=True)
    return result.returncode == 0 and bool(result.stdout.strip()) and not result.stdout.strip().startswith('Z')


def dead_soon(pid):
    for _ in range(40):
        if not alive(pid): return True
        time.sleep(.025)
    return False


def stop(pid):
    try: os.kill(pid, signal.SIGKILL)
    except ProcessLookupError: pass


def run_case(name, action):
    started = time.monotonic()
    try:
        detail = action()
        ROWS.append({'name': name, 'status': 'passed', 'detail': detail, 'seconds': time.monotonic() - started})
    except BaseException as exc:
        ROWS.append({'name': name, 'status': 'failed', 'error': type(exc).__name__ + ': ' + str(exc), 'seconds': time.monotonic() - started})


def positive():
    with tempfile.TemporaryDirectory(prefix='reiyah-capture-positive-') as directory:
        d = Path(directory)
        with patch.object(M, 'P', d):
            result = M.run_capture([sys.executable, '-B', '-c', "import sys;print('actual stdout');print('actual stderr',file=sys.stderr)"], d/'out', d/'err', 3)
        assert set(result) == {'returncode', 'timed_out', 'wall_seconds'}
        assert result['returncode'] == 0 and result['timed_out'] is False
        assert (d/'out').read_bytes() == b'actual stdout\n' and (d/'err').read_bytes() == b'actual stderr\n'
        assert not (d/'out.cleanup.json').exists()
        return result


def nonzero():
    with tempfile.TemporaryDirectory(prefix='reiyah-capture-nonzero-') as directory:
        d = Path(directory)
        with patch.object(M, 'P', d):
            result = M.run_capture([sys.executable, '-B', '-c', 'raise SystemExit(7)'], d/'out', d/'err', 3)
        assert result['returncode'] == 7 and result['timed_out'] is False
        return result


def exclusive():
    with tempfile.TemporaryDirectory(prefix='reiyah-capture-exclusive-') as directory:
        d = Path(directory); (d/'out').write_bytes(b'preserved')
        with patch.object(M.subprocess, 'Popen') as spawned:
            try: M.run_capture(['unused'], d/'out', d/'err', 1)
            except FileExistsError: pass
            else: raise AssertionError('existing stdout was overwritten')
        assert not spawned.called and (d/'out').read_bytes() == b'preserved'
        return {'spawned': False, 'original_bytes_preserved': True}


def timeout_case(discovery_failure=None):
    with tempfile.TemporaryDirectory(prefix='reiyah-capture-timeout-') as directory:
        d = Path(directory)
        code = "import os,subprocess,sys,time;from pathlib import Path;Path('outer.pid').write_text(str(os.getpid()));child=subprocess.Popen([sys.executable,'-B','-c','import time;time.sleep(30)'],start_new_session=True);Path('child.pid').write_text(str(child.pid));time.sleep(30)"
        child_pid = outer_pid = None
        def discover(*args, **kwargs):
            if discovery_failure == 'timeout': raise subprocess.TimeoutExpired(args[0], 3)
            if discovery_failure == 'malformed': return subprocess.CompletedProcess(args[0], 0, stdout='malformed row\n', stderr='')
            if discovery_failure == 'nonzero': return subprocess.CompletedProcess(args[0], 1, stdout='', stderr='authored refusal')
            return REAL_RUN(*args, **kwargs)
        try:
            with patch.object(M, 'P', d), patch.object(M.subprocess, 'run', side_effect=discover):
                result = M.run_capture([sys.executable, '-B', '-c', code], d/'out', d/'err', .4)
            outer_pid = int((d/'outer.pid').read_text()); child_pid = int((d/'child.pid').read_text())
            assert result['returncode'] == -signal.SIGKILL and result['timed_out'] is True
            assert dead_soon(outer_pid)
            cleanup = json.loads((d/'out.cleanup.json').read_text())
            assert any(row['action'] == 'kill_owned_outer_group' for row in cleanup['actions'])
            if discovery_failure:
                errors = [r for r in cleanup['actions'] if r['action'] == 'child_discovery_or_stop_failed']
                assert len(errors) == 1 and errors[0]['descendant_cleanup_verified'] is False
                survived = alive(child_pid)
                assert survived, 'fixture should show undiscovered independent-session child remains'
            else:
                survived = not dead_soon(child_pid)
                assert not survived
            return {'capture': result, 'cleanup': cleanup, 'independent_child_survived_launcher': survived,
                    'test_harness_cleanup': 'known fixture child killed in finally when discovery failed'}
        finally:
            for name in ('child.pid', 'outer.pid'):
                if (d/name).exists(): stop(int((d/name).read_text()))


def interrupted():
    with tempfile.TemporaryDirectory(prefix='reiyah-capture-interrupt-') as directory:
        d = Path(directory); instances = []
        class InterruptOnce(REAL_POPEN):
            def wait(self, timeout=None):
                if not getattr(self, '_review_interrupted', False):
                    self._review_interrupted = True
                    raise KeyboardInterrupt('authored interruption')
                return super().wait(timeout=timeout)
        def spawn(*args, **kwargs):
            proc = InterruptOnce(*args, **kwargs); instances.append(proc); return proc
        try:
            with patch.object(M, 'P', d), patch.object(M.subprocess, 'Popen', side_effect=spawn):
                try: M.run_capture([sys.executable, '-B', '-c', 'import time;time.sleep(30)'], d/'out', d/'err', 3)
                except KeyboardInterrupt: pass
                else: raise AssertionError('interrupt swallowed')
            assert instances and dead_soon(instances[0].pid)
            assert (d/'out.cleanup.json').exists()
            return {'interrupt_propagated': True, 'owned_outer_stopped': True}
        finally:
            for proc in instances:
                if proc.poll() is None: stop(proc.pid); proc.wait(timeout=3)


run_case('actual_positive_stdout_stderr', positive)
run_case('actual_nonzero_not_coerced', nonzero)
run_case('existing_output_never_overwritten_or_spawned', exclusive)
run_case('actual_timeout_stops_observed_separate_session_child_and_outer', timeout_case)
for kind in ('timeout', 'malformed', 'nonzero'):
    run_case('child_discovery_' + kind + '_still_stops_outer_and_records_uncertainty', lambda kind=kind: timeout_case(kind))
run_case('interruption_runs_cleanup_and_propagates', interrupted)
assert SOURCE_SHA == hashlib.sha256((ROOT/'run_remaining_cohort.py').read_bytes()).hexdigest(), 'source changed during controls'
report = {'source_sha256': SOURCE_SHA, 'test_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'scope': 'Authored harmless processes only; no cohort main, capacity window, models, data, or inference.',
          'passed': sum(r['status']=='passed' for r in ROWS), 'total': len(ROWS), 'cases': ROWS}
with (ROOT/'consumer-review/LAUNCH_CONTROLS.json').open('x') as f: json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({'passed': report['passed'], 'total': report['total'], 'source_sha256': SOURCE_SHA}))
raise SystemExit(0 if report['passed'] == report['total'] else 1)
