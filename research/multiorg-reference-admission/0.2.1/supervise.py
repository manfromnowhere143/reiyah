#!/usr/bin/env python3
"""Host resource observer; only the byte-bound worker enters network denial.

A process-completion receipt is not evidence of a scientific result. Numerical
and domain validation remains the worker's responsibility. RSS is sampled and
is not an instantaneous hard address-space or process-tree containment bound.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

POLICY = b'(version 1)\n(allow default)\n(deny network*)\n'
POLICY_SHA256 = '5c358b8d847211333e7ba22df82d84f796b5f30a41a2682209a949d783adbd08'


def digest(path, maximum=300000000):
    if path.stat().st_size > maximum:
        raise ValueError('input byte cap')
    h = hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda: f.read(1048576), b''): h.update(data)
    return h.hexdigest()


def contained(owner, path, exists=True):
    p = Path(path).resolve(strict=exists)
    if not p.is_relative_to(owner) or (exists and not p.is_file()):
        raise ValueError('path outside owner or not regular file')
    return p


def read_json(path):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            if key in out: raise ValueError('duplicate JSON property')
            out[key] = value
        return out
    if path.stat().st_size > 1048576: raise ValueError('JSON byte cap')
    return json.loads(path.read_text(), object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def bindings(owner, manifest, runner, runner_sha256):
    if digest(runner, 1048576) != runner_sha256:
        raise ValueError('worker digest mismatch')
    m = read_json(manifest)
    if not isinstance(m, dict) or set(m) != {'protocol', 'images', 'models', 'limits'}:
        raise ValueError('manifest envelope schema')
    if not isinstance(m['images'], list) or not isinstance(m['models'], dict):
        raise ValueError('source collection types')
    refs = [m['protocol']] + list(m['models'].values())
    refs += [row['source'] for row in m['images']]
    pins = [(runner, runner_sha256), (manifest, digest(manifest, 1048576))]
    for row in refs:
        if not isinstance(row, dict) or set(row) != {'path', 'sha256'}:
            raise ValueError('source binding schema')
        p = contained(owner, row['path'])
        sha = row['sha256']
        if not isinstance(sha, str) or len(sha) != 64 or digest(p) != sha:
            raise ValueError('source digest mismatch')
        pins.append((p, sha))
    limits = m['limits']
    if not isinstance(limits, dict): raise ValueError('limits schema')
    wall, memory = limits['wall_seconds'], limits['memory_bytes']
    if type(wall) not in (int, float) or not math.isfinite(wall) or not 0 < wall <= 600:
        raise ValueError('wall limit')
    if type(memory) is not int or not 1 <= memory <= 6442450944:
        raise ValueError('memory limit')
    return m, pins


def supervise(owner, manifest, runner, runner_sha256, python, output,
              sample_seconds=0.2, free_disk_floor=4294967296):
    import shutil
    owner = Path(owner).resolve(strict=True)
    manifest, runner = contained(owner, manifest), contained(owner, runner)
    output = contained(owner, output, exists=False)
    if not output.parent.is_dir() or output.exists(): raise ValueError('output must be new')
    receipt_path = output.with_suffix('.process.json')
    log_path = output.with_suffix('.log')
    policy_path = output.with_suffix('.sandbox.sb')
    if any(p.exists() for p in (receipt_path, log_path, policy_path)):
        raise ValueError('process artifacts already exist')
    if not 0.01 <= sample_seconds <= 1: raise ValueError('sampling period')
    record = {'status': 'failed', 'returncode': None, 'termination_reason': None,
              'worker_pid': None, 'peak_sampled_rss_bytes': 0,
              'sampling_period_seconds': sample_seconds,
              'memory_boundary': 'sampled_RSS_not_hard_address_space_limit',
              'network_boundary': 'worker_only_host_observer_outside_sandbox',
              'policy_sha256': POLICY_SHA256, 'runner_sha256': runner_sha256,
              'log': log_path.name}
    process = None
    start = time.monotonic()
    try:
        m, pins = bindings(owner, manifest, runner, runner_sha256)
        record['manifest_sha256'] = digest(manifest, 1048576)
        if shutil.disk_usage(owner).free < free_disk_floor: raise ValueError('free disk floor')
        if hashlib.sha256(POLICY).hexdigest() != POLICY_SHA256: raise ValueError('policy constant changed')
        with policy_path.open('xb') as f: f.write(POLICY)
        if digest(policy_path) != POLICY_SHA256: raise ValueError('materialized policy changed')
        wall, memory = m['limits']['wall_seconds'], m['limits']['memory_bytes']
        def child_limits():
            cpu = max(1, math.ceil(wall * 2))
            resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 2))
            resource.setrlimit(resource.RLIMIT_FSIZE, (67108864, 67108864))
        env = os.environ.copy()
        env.update({'PYTHONDONTWRITEBYTECODE': '1', 'OMP_NUM_THREADS': '2',
                    'OPENBLAS_NUM_THREADS': '1', 'VECLIB_MAXIMUM_THREADS': '2',
                    'MKL_NUM_THREADS': '2', 'CUDA_VISIBLE_DEVICES': ''})
        # Preserve the venv entrypoint: resolving its symlink changes sys.prefix.
        python_entrypoint = Path(python).absolute()
        if not python_entrypoint.is_file(): raise ValueError('Python entrypoint missing')
        command = ['/usr/bin/sandbox-exec', '-f', str(policy_path), str(python_entrypoint),
                   '-B', str(runner), '--worker', '--manifest', str(manifest), '--output', str(output)]
        record['command'] = command
        with log_path.open('xb') as log:
            process = subprocess.Popen(command, cwd=owner, env=env, stdin=subprocess.DEVNULL,
                                       stdout=log, stderr=log, start_new_session=True,
                                       preexec_fn=child_limits)
            record['worker_pid'] = process.pid
            begin = time.monotonic()
            while process.poll() is None:
                sample = subprocess.run(['/bin/ps', '-o', 'rss=', '-p', str(process.pid)],
                                        capture_output=True, text=True, timeout=2)
                if sample.returncode == 0 and sample.stdout.strip():
                    rss = int(sample.stdout.strip()) * 1024
                    record['peak_sampled_rss_bytes'] = max(record['peak_sampled_rss_bytes'], rss)
                elif process.poll() is None:
                    raise RuntimeError('RSS observation failed for live owned worker')
                elapsed = time.monotonic() - begin
                if elapsed > wall: record['termination_reason'] = 'wall_limit'
                elif record['peak_sampled_rss_bytes'] > memory: record['termination_reason'] = 'memory_limit'
                elif shutil.disk_usage(owner).free < free_disk_floor: record['termination_reason'] = 'disk_floor'
                if record['termination_reason']:
                    # Kill precisely the worker this observer created, never a name match.
                    process.kill(); process.wait(timeout=5); break
                time.sleep(sample_seconds)
        record['returncode'] = process.returncode
        if process.returncode != 0 and record['termination_reason'] is None:
            record['termination_reason'] = 'worker_exit'
        if process.returncode == 0:
            for p, sha in pins:
                if digest(p) != sha: raise ValueError('bound input changed during execution')
            result_path = output / 'result.json'
            result = read_json(result_path)
            if result.get('status') != 'complete': raise ValueError('worker result incomplete')
            record['result_sha256'] = digest(result_path, 67108864)
            record['status'] = 'complete'
    except Exception as exc:
        record['termination_reason'] = record['termination_reason'] or 'supervisor_error'
        record['error'] = type(exc).__name__ + ': ' + str(exc)
    finally:
        if process is not None and process.poll() is None:
            process.kill(); process.wait(timeout=5)
        if process is not None: record['returncode'] = process.returncode
        record['wall_seconds'] = time.monotonic() - start
        receipt_path.write_text(json.dumps(record, indent=2, allow_nan=False) + '\n')
    return record


def main():
    p = argparse.ArgumentParser()
    for flag in ['owner', 'manifest', 'runner', 'runner-sha256', 'python', 'output']:
        p.add_argument('--' + flag, required=True)
    a = p.parse_args()
    result = supervise(a.owner, a.manifest, a.runner, a.runner_sha256, a.python, a.output)
    print(json.dumps(result))
    return 0 if result['status'] == 'complete' else 1


if __name__ == '__main__': raise SystemExit(main())
