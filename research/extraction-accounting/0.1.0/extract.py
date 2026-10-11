"""Versioned offline camera/gaze extraction with explicit cohort accounting.

No model, data discovery, metric, or physical synchronization claim. A caller
must declare the complete cohort and expected output count before execution.
"""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

VERSION = '0.1.0'
ROLES = ('camera', 'gaze')


class Invalid(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def decode(data):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'Duplicate JSON field')
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=unique_pairs)


def fingerprint(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), 'Expected a regular, non-symlink file')
    digest, size = hashlib.sha256(), 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
            size += len(block)
    return {'sha256': digest.hexdigest(), 'bytes': size}


def keys(value, expected):
    require(type(value) is dict and set(value) == set(expected), 'Missing or unknown fields')


def valid_digest(value):
    return type(value) is str and re.fullmatch('[a-f0-9]{64}', value) is not None


def validate(plan):
    keys(plan, ('artifact_id', 'version', 'fps', 'clips'))
    require(plan['artifact_id'] == 'reiyah.extraction-plan' and plan['version'] == VERSION, 'Unknown plan/version')
    require(type(plan['fps']) is str, 'Frame rate must be a canonical rational string')
    try:
        fps = Fraction(plan['fps'])
    except (ValueError, ZeroDivisionError) as exc:
        raise Invalid('Invalid frame rate') from exc
    require(str(fps) == plan['fps'] and 0 < fps <= 60, 'Noncanonical or out-of-range frame rate')
    require(type(plan['clips']) is list and 1 <= len(plan['clips']) <= 128, 'Declare a nonempty bounded cohort')
    ids = set()
    for clip in plan['clips']:
        keys(clip, ('id', 'expected_frames', *ROLES))
        require(type(clip['id']) is str and re.fullmatch('[A-Za-z0-9_-]{1,80}', clip['id']) is not None,
                'Unsafe or missing clip identifier')
        require(clip['id'] not in ids, 'Duplicate clip identifier')
        ids.add(clip['id'])
        require(type(clip['expected_frames']) is int and 1 <= clip['expected_frames'] <= 1000,
                'Declare a positive frame count up to 1000; missing is not zero')
        for role in ROLES:
            keys(clip[role], ('path', 'sha256'))
            require(type(clip[role]['path']) is str and Path(clip[role]['path']).is_absolute(), 'Require absolute local source paths')
            require(valid_digest(clip[role]['sha256']), 'Require an expected source digest')
    return plan


def write_new(path, value):
    with Path(path).open('xb') as stream:
        stream.write(encoded(value))


def inventory(directory, expected):
    rows = []
    try:
        for path in sorted(directory.iterdir()):
            rows.append({'name': path.name, **fingerprint(path)})
    except (OSError, Invalid) as exc:
        return {'state': 'failed', 'reason': 'unreadable_frame', 'detail': str(exc), 'files': rows}
    names = [f'frame-{n:06d}.jpg' for n in range(1, expected + 1)]
    reason = ('frame_membership_mismatch' if [r['name'] for r in rows] != names else
              'empty_frame_file' if any(r['bytes'] == 0 for r in rows) else None)
    return {'state': 'complete' if reason is None else 'failed', 'reason': reason, 'files': rows}


def extract_stream(source, directory, expected, fps, executable, timeout):
    directory.mkdir(parents=True)
    frames = directory / 'frames'
    frames.mkdir()
    record = {'source': source, 'state': 'not_started', 'reason': None, 'before': None,
              'after': None, 'process': None, 'frames': None}
    try:
        record['before'] = fingerprint(source['path'])
    except FileNotFoundError:
        record.update(state='missing', reason='source_missing')
        return record
    except (OSError, Invalid) as exc:
        # is_file() returns False for an absent path; distinguish absence explicitly.
        missing = not Path(source['path']).exists()
        record.update(state='missing' if missing else 'failed',
                      reason='source_missing' if missing else 'source_unreadable', detail=str(exc))
        return record
    if record['before']['sha256'] != source['sha256'] or record['before']['bytes'] == 0:
        record.update(state='failed', reason='source_identity_or_empty_input')
        return record
    argv = [str(executable), '-nostdin', '-n', '-hide_banner', '-loglevel', 'error',
            '-xerror', '-abort_on', 'empty_output', '-protocol_whitelist', 'file',
            '-threads', '1', '-i', source['path'], '-map', '0:v:0', '-an', '-sn', '-dn',
            '-filter_threads', '1', '-vf', 'fps=' + fps, '-threads', '1',
            '-frames:v', str(expected + 1), '-start_number', '1',
            str(frames / 'frame-%06d.jpg')]
    process = {'argv': argv, 'returncode': None, 'error': None, 'timeout_seconds': timeout}
    with (directory/'stdout.txt').open('xb') as stdout, (directory/'stderr.txt').open('xb') as stderr:
        try:
            run = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=timeout, check=False)
            process['returncode'] = run.returncode
        except subprocess.TimeoutExpired:
            process['error'] = 'timeout'
        except OSError as exc:
            process.update(error='process_start_failed', detail=str(exc))
    process['stdout'] = fingerprint(directory/'stdout.txt')
    process['stderr'] = fingerprint(directory/'stderr.txt')
    record['process'] = process
    record['frames'] = inventory(frames, expected)
    try:
        record['after'] = fingerprint(source['path'])
    except (OSError, Invalid):
        record['after'] = None
    reason = ('extraction_timeout' if process['error'] == 'timeout' else
              'extraction_process_failed' if process['error'] or process['returncode'] != 0 else
              'source_changed' if record['after'] != record['before'] else record['frames']['reason'])
    record.update(state='processed' if reason is None else 'failed', reason=reason)
    return record


def run(plan, output, executable, timeout=30):
    validate(plan)
    require(type(timeout) is int and 1 <= timeout <= 120, 'Invalid timeout')
    executable = Path(executable).resolve(strict=True)
    tool_identity = fingerprint(executable)
    output = Path(output).absolute()
    # The caller must allocate a fresh destination; never reuse partial frames.
    output.mkdir(parents=True, exist_ok=False)
    write_new(output/'plan.json', plan)
    ledger = {'artifact_id': 'reiyah.extraction-ledger', 'version': VERSION,
              'plan_sha256': sha(encoded(plan)), 'tool': {'path': str(executable), **tool_identity},
              'accounting_status': 'blocked', 'measurement_status': 'not_performed',
              'synchronization': 'not_established', 'clips': []}
    # Every declared clip is attempted/accounted, including after another fails.
    for clip in plan['clips']:
        streams = {role: extract_stream(clip[role], output/clip['id']/role,
                    clip['expected_frames'], plan['fps'], executable, timeout) for role in ROLES}
        ledger['clips'].append({'id': clip['id'], 'expected_frames': clip['expected_frames'],
                               'state': 'processed' if all(s['state']=='processed' for s in streams.values()) else 'blocked',
                               'streams': streams})
    if all(c['state'] == 'processed' for c in ledger['clips']):
        ledger['accounting_status'] = 'complete'
    write_new(output/'ledger.json', ledger)
    return ledger


def require_complete(plan, output, expected_ledger_sha256):
    """Recheck exact membership/bytes before returning any pairs to a consumer.

    Integrity checking is conditional on a trusted process/ledger origin. It is
    not attestation of decoder execution, true capture time or physical events.
    """
    validate(plan)
    output = Path(output)
    raw = (output/'ledger.json').read_bytes()
    require(valid_digest(expected_ledger_sha256) and sha(raw)==expected_ledger_sha256, 'Ledger digest mismatch')
    ledger = decode(raw)
    keys(ledger, ('artifact_id', 'version', 'plan_sha256', 'tool', 'accounting_status',
                  'measurement_status', 'synchronization', 'clips'))
    require(ledger['artifact_id']=='reiyah.extraction-ledger' and ledger['version']==VERSION, 'Unknown ledger/version')
    require(ledger['plan_sha256']==sha(encoded(plan)) and (output/'plan.json').read_bytes()==encoded(plan), 'Plan mismatch')
    require(ledger['accounting_status']=='complete' and ledger['measurement_status']=='not_performed'
            and ledger['synchronization']=='not_established', 'Incomplete cohort or promoted measurement')
    require([c['id'] for c in ledger['clips']]==[c['id'] for c in plan['clips']], 'Clip membership changed')
    pairs = []
    for clip, recorded in zip(plan['clips'], ledger['clips']):
        require(recorded['expected_frames']==clip['expected_frames'] and recorded['state']=='processed', 'Clip disposition changed')
        require(set(recorded['streams'])==set(ROLES), 'Stream membership changed')
        for role in ROLES:
            stream = recorded['streams'][role]
            require(stream['state']=='processed' and stream['reason'] is None
                    and stream['process']['returncode']==0 and stream['process']['error'] is None, 'Failed process')
            require(stream['source']==clip[role] and stream['before']==stream['after']
                    and stream['after']==fingerprint(clip[role]['path'])
                    and stream['after']['sha256']==clip[role]['sha256'], 'Source identity changed')
            directory = output/clip['id']/role
            for channel in ('stdout','stderr'):
                require(fingerprint(directory/(channel+'.txt'))==stream['process'][channel], 'Process log changed')
            actual = inventory(directory/'frames', clip['expected_frames'])
            require(actual['state']=='complete' and actual==stream['frames'], 'Frame membership or bytes changed')
        pairs.extend((output/clip['id']/'camera/frames'/f'frame-{n:06d}.jpg',
                      output/clip['id']/'gaze/frames'/f'frame-{n:06d}.jpg')
                     for n in range(1, clip['expected_frames'] + 1))
    return tuple(pairs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ffmpeg', type=Path, required=True)
    args = parser.parse_args()
    try:
        with args.plan.open('rb') as stream:
            data = stream.read(1024 * 1024 + 1)
        require(len(data)<=1024*1024 and valid_digest(args.plan_sha256) and sha(data)==args.plan_sha256, 'Plan digest or size mismatch')
        plan = decode(data)
        ledger = run(plan, args.output, args.ffmpeg)
        digest = sha((args.output/'ledger.json').read_bytes())
        if ledger['accounting_status']=='complete':
            pairs = require_complete(plan, args.output, digest)
            print(json.dumps({'accounting_status':'complete','frame_pairs':len(pairs),'ledger_sha256':digest,
                              'measurement_status':'not_performed','synchronization':'not_established'}))
            return 0
        print(json.dumps({'accounting_status':'blocked','ledger_sha256':digest,'measurement_status':'not_performed'}))
        return 3
    except (Invalid, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'accounting_status':'invalid','detail':str(exc)}),file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
