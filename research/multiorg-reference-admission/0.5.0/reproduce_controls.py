#!/usr/bin/env python3
"""Replay the adjacent 0.5.0 authored controls; no detector model is executed."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import unittest


FILES = (
    'reproduce_controls.py', 'complete_pair.py', 'run_pair.py', 'projection.py',
    'test_complete_pair.py', 'admit_tile.py', 'reference_core.py',
    'test_admit_tile.py', 'check_pair.py', 'reconstruct_inputs.py',
    'test_check_pair.py', 'test_reconstruct_inputs.py', 'THIRD_PARTY_NOTICES.md',
)
SUITES = ('test_admit_tile', 'test_check_pair', 'test_reconstruct_inputs')
PACKAGES = ('numpy', 'onnxruntime', 'scikit-image', 'opencv-python-headless', 'tifffile')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.started_ids = []
        self.passed_ids = []

    def startTest(self, test):
        self.started_ids.append(test.id())
        super().startTest(test)

    def addSuccess(self, test):
        self.passed_ids.append(test.id())
        super().addSuccess(test)


def run(output):
    start = time.monotonic()
    root = Path(__file__).resolve().parent
    output.mkdir(parents=False, exist_ok=False)
    report = {
        'artifact_id': 'reiyah.multiorg.complete-pair.authored-control-replay',
        'version': '0.5.0', 'status': 'failed',
        'scope': 'Authored arrays, mocked model sessions and installed ORT Python failure policy. No empirical model inference, source acquisition or private manifest replay.',
        'optional_private_manifest_controls_run': False,
        'empirical_forward_passes': 0, 'unittest_suites': [],
        'count_unit': 'Named worker controls plus unittest test cases; subtests and data iterations are not extra cases.',
    }
    before = {}
    try:
        for name in FILES:
            path = root / name
            if not path.is_file() or path.is_symlink():
                raise ValueError('Missing regular adjacent source: ' + name)
            before[name] = digest(path)
        report['source_sha256_before'] = before
        report['runtime'] = {'python': platform.python_version(), 'executable': sys.executable,
                             'packages': {name: importlib.metadata.version(name) for name in PACKAGES}}
        if sys.flags.optimize:
            raise ValueError('Assertions must be enabled; do not use -O or PYTHONOPTIMIZE')
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONOPTIMIZE='')
        receipt = output / 'worker-controls.json'
        command = [sys.executable, '-B', str(root / 'test_complete_pair.py'), '--output', str(receipt)]
        with (output / 'worker.stdout').open('xb') as out, (output / 'worker.stderr').open('xb') as err:
            process = subprocess.run(command, cwd=root, env=env, stdout=out, stderr=err, timeout=120, check=False)
        worker = {'returncode': process.returncode, 'receipt': receipt.name, 'controls_executed': None}
        report['worker'] = worker
        if receipt.is_file():
            data = json.loads(receipt.read_bytes())
            controls = data.get('controls')
            if (data.get('status') != 'passed' or type(data.get('count')) is not int
                    or not isinstance(controls, list) or not all(isinstance(x, str) for x in controls)
                    or data['count'] != len(controls) or len(set(controls)) != len(controls)
                    or data.get('empirical_forward_passes') != 0 or 'static_manifest_sha256' in data):
                raise ValueError('Worker control receipt is incomplete or outside default replay scope')
            expected_scripts = {name: before[name] for name in ('complete_pair.py', 'test_complete_pair.py', 'run_pair.py', 'projection.py')}
            if data.get('scripts') != expected_scripts:
                raise ValueError('Worker receipt source identity mismatch')
            worker.update(controls_executed=data['count'], controls=controls, receipt_sha256=digest(receipt))
        # The subprocess isolates the worker's mock patches from these test suites.
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(root))
        for name in SUITES:
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromName(name)
            discovered = suite.countTestCases()
            with (output / (name + '.log')).open('x', encoding='utf-8') as log:
                result = unittest.TextTestRunner(stream=log, verbosity=2, resultclass=RecordedResult).run(suite)
            report['unittest_suites'].append({
                'module': name, 'discovered_test_cases': discovered, 'tests_run': result.testsRun,
                'started_ids': result.started_ids, 'passed_ids': result.passed_ids,
                'failures': [test.id() for test, _ in result.failures],
                'errors': [test.id() for test, _ in result.errors],
                'skipped': [{'test': test.id(), 'reason': reason} for test, reason in result.skipped],
                'expected_failures': [test.id() for test, _ in result.expectedFailures],
                'unexpected_successes': [test.id() for test in result.unexpectedSuccesses],
                'loader_errors': list(loader.errors),
                'status': 'passed' if result.wasSuccessful() and result.testsRun == discovered
                    and discovered > 0 and not result.skipped and not result.expectedFailures else 'failed',
            })
        worker_count = worker['controls_executed']
        report['completed_control_count'] = (worker_count + sum(x['tests_run'] for x in report['unittest_suites'])) if worker_count is not None else None
        report['unittest_test_cases_run'] = sum(x['tests_run'] for x in report['unittest_suites'])
        if process.returncode == 0 and worker_count is not None and worker_count > 0 and all(x['status'] == 'passed' for x in report['unittest_suites']):
            report['status'] = 'passed'
    except Exception as exc:
        report['error'] = {'type': type(exc).__name__, 'message': str(exc)}
    finally:
        after = {name: digest(root / name) if (root / name).is_file() else None for name in before}
        report['source_sha256_after'] = after
        report['source_bytes_unchanged'] = bool(before) and before == after
        if not report['source_bytes_unchanged']:
            report['status'] = 'failed'
        report['wall_seconds'] = time.monotonic() - start
        write(output / 'report.json', report)
    print(json.dumps({'status': report['status'], 'completed_control_count': report.get('completed_control_count'), 'report': str(output / 'report.json')}))
    return 0 if report['status'] == 'passed' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New directory under an existing parent; must not already exist.')
    args = parser.parse_args()
    raise SystemExit(run(args.output.absolute()))


if __name__ == '__main__':
    main()
