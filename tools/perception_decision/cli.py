"""Offline command interface. Verification precedes atomic, non-overwriting output."""
import argparse
import hashlib
import os
from pathlib import Path
import sys
import tempfile

from .checker import check
from .contract import Invalid, MAX_PACKET_BYTES, SCHEMA, encoded, load
from .kernel import produce


def implementation_digest():
    paths = sorted(Path(__file__).parent.glob('*.py')) + [SCHEMA]
    record = [(p.name, hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths]
    return hashlib.sha256(encoded(record)).hexdigest()


def atomic_write(path, data):
    """Commit a complete file without replacing an existing output identity."""
    target = Path(path)
    fd, temporary = tempfile.mkstemp(prefix='.perception-decision-', dir=target.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, target)
    finally:
        os.unlink(temporary)


def run(input_path, expected, output):
    case = load(input_path, expected)
    payload = produce(case)
    check(case, payload)
    packet = {'artifact_id': 'reiyah.perception-decision.packet', 'version': '0.1.0',
              'comparison_id': case['comparison_id'], 'input_sha256': expected,
              'producer_sha256': implementation_digest(), 'payload': payload}
    data = encoded(packet)
    if len(data) > MAX_PACKET_BYTES:
        raise Invalid('PACKET_SIZE', 'Checked proof exceeds the packet byte limit')
    atomic_write(output, data)
    return {'output': str(output), 'sha256': hashlib.sha256(data).hexdigest(),
            'certificate_checked': True, 'result': payload['result']}


def verify(input_path, expected, packet_path, packet_digest):
    case = load(input_path, expected)
    packet = load(packet_path, packet_digest, MAX_PACKET_BYTES, validate_input=False)
    required = {'artifact_id', 'version', 'comparison_id', 'input_sha256', 'producer_sha256', 'payload'}
    if type(packet) is not dict or set(packet) != required:
        raise Invalid('PACKET_SCHEMA', 'Unexpected packet fields')
    if (packet['artifact_id'] != 'reiyah.perception-decision.packet' or packet['version'] != '0.1.0'
            or packet['comparison_id'] != case['comparison_id'] or packet['input_sha256'] != expected):
        raise Invalid('PACKET_BINDING', 'Packet refers to a different comparison, input or version')
    digest = packet['producer_sha256']
    if type(digest) is not str or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
        raise Invalid('PACKET_SCHEMA', 'Malformed producer identity')
    return {'certificate_checked': True, 'result': check(case, packet['payload']),
            'producer_matches_current_source': digest == implementation_digest()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    for command in ('run', 'verify'):
        sub = subs.add_parser(command)
        sub.add_argument('--input', type=Path, required=True)
        sub.add_argument('--input-sha256', required=True)
        if command == 'run':
            sub.add_argument('--output', type=Path, required=True)
        else:
            sub.add_argument('--packet', type=Path, required=True)
            sub.add_argument('--packet-sha256', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'run':
            result = run(args.input, args.input_sha256, args.output)
        else:
            result = verify(args.input, args.input_sha256, args.packet, args.packet_sha256)
    except Invalid as exc:
        sys.stderr.buffer.write(encoded({'status': 'error', **exc.diagnostic()}))
        return 2
    except OSError as exc:
        sys.stderr.buffer.write(encoded({'status': 'error', 'code': 'IO_ERROR', 'detail': str(exc)}))
        return 2
    sys.stdout.buffer.write(encoded(result))
    return 0 if result['result']['model_status'] == 'consistent' else 3
