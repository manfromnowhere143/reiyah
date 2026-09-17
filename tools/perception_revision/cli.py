"""Offline revision commands with selected input digests and checked outputs."""
import argparse
import hashlib
from pathlib import Path
import sys

from tools.perception_decision.cli import atomic_write
from tools.perception_decision.contract import load as legacy_load
from . import audit, audit_checker, checker, kernel
from .boxes import BOX_SCHEMA, compile_alternatives
from .contract import (AUDIT_SCHEMA, SCHEMA, Invalid, MAX_INPUT_BYTES, MAX_PACKET_BYTES, encoded, from_addition,
                       load, load_bytes, rebind_observations, require, validate_request)


def implementation_digest():
    root = Path(__file__).resolve().parents[2]
    paths = sorted(Path(__file__).parent.glob('*.py'))
    paths += sorted((root / 'tools/perception_decision').glob('*.py'))
    paths += [SCHEMA, AUDIT_SCHEMA, BOX_SCHEMA, root / 'research/perception-decision/0.1.0/input.schema.json']
    rows = [(str(p.relative_to(root)), hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths]
    return hashlib.sha256(encoded(rows)).hexdigest()


def request_input(case, path, digest):
    return validate_request(case, load_bytes(path, digest, validate_input=False))


def read_packet(case, input_digest, path, digest, request_digest=None):
    packet = load_bytes(path, digest, MAX_PACKET_BYTES, validate_input=False)
    fields = {'artifact_id', 'version', 'comparison_id', 'input_sha256', 'producer_sha256', 'payload'}
    if request_digest is not None:
        fields.add('request_sha256')
    require(type(packet) is dict and set(packet) == fields, 'PACKET_SCHEMA', 'Unexpected packet fields')
    artifact = 'reiyah.perception-revision.audit-packet' if request_digest is not None else 'reiyah.perception-revision.packet'
    require(packet['artifact_id'] == artifact and packet['version'] == '0.1.0'
            and packet['comparison_id'] == case['comparison_id'] and packet['input_sha256'] == input_digest,
            'PACKET_BINDING', 'Wrong comparison, input, version or packet kind')
    if request_digest is not None:
        require(packet['request_sha256'] == request_digest, 'PACKET_BINDING', 'Wrong audit observations or error model')
    producer = packet['producer_sha256']
    require(type(producer) is str and len(producer) == 64 and all(c in '0123456789abcdef' for c in producer),
            'PACKET_SCHEMA', 'Malformed producer digest')
    return packet


def write_output(path, value, limit=MAX_PACKET_BYTES):
    data = encoded(value)
    require(len(data) <= limit, 'OUTPUT_SIZE', 'Output exceeds its declared input or packet byte limit')
    atomic_write(path, data)
    return {'output': str(path), 'sha256': hashlib.sha256(data).hexdigest()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    for command in ('from-addition', 'from-box-alternatives', 'run', 'verify', 'audit', 'verify-audit', 'rebind-audit'):
        sub = subs.add_parser(command)
        sub.add_argument('--input', type=Path, required=True)
        sub.add_argument('--input-sha256', required=True)
        if command in ('verify', 'verify-audit'):
            sub.add_argument('--packet', type=Path, required=True)
            sub.add_argument('--packet-sha256', required=True)
        else:
            sub.add_argument('--output', type=Path, required=True)
        if command in ('audit', 'verify-audit', 'rebind-audit'):
            sub.add_argument('--request', type=Path, required=True)
            sub.add_argument('--request-sha256', required=True)
        if command == 'audit':
            sub.add_argument('--candidate', type=Path)
            sub.add_argument('--candidate-sha256')
            sub.add_argument('--proof-method', choices=('legacy', 'components'), default='legacy')
        if command in ('run', 'rebind-audit'):
            sub.add_argument('--prior-input', type=Path, required=command == 'rebind-audit')
            sub.add_argument('--prior-input-sha256', required=command == 'rebind-audit')
        if command == 'run':
            sub.add_argument('--prior-packet', type=Path)
            sub.add_argument('--prior-packet-sha256')
    args = parser.parse_args(argv)
    try:
        if args.command == 'from-box-alternatives':
            source = load_bytes(args.input, args.input_sha256, validate_input=False)
            converted = compile_alternatives(source)
            answer = write_output(args.output, converted, MAX_INPUT_BYTES)
            answer['scope'] = 'Declared 2D reference alternatives; no universal correction or physical-truth claim'
        elif args.command == 'from-addition':
            converted = from_addition(legacy_load(args.input, args.input_sha256))
            answer = write_output(args.output, converted, MAX_INPUT_BYTES)
            answer['scope'] = 'Declared legacy augmented output; not standalone detector B'
        else:
            case = load(args.input, args.input_sha256)
            if args.command == 'rebind-audit':
                previous = load(args.prior_input, args.prior_input_sha256)
                request = request_input(previous, args.request, args.request_sha256)
                answer = write_output(args.output, rebind_observations(previous, request, case), MAX_INPUT_BYTES)
                answer['scope'] = 'Same declared reference context; no new physical validation'
            elif args.command in ('verify', 'verify-audit'):
                request = request_input(case, args.request, args.request_sha256) if args.command == 'verify-audit' else None
                packet = read_packet(case, args.input_sha256, args.packet, args.packet_sha256,
                                     args.request_sha256 if request is not None else None)
                result = audit_checker.check(case, request, packet['payload']) if request is not None else checker.check(case, packet['payload'])
                answer = {'certificate_checked': True, 'result': result,
                          'producer_matches_current_source': packet['producer_sha256'] == implementation_digest()}
            else:
                packet = {'artifact_id': 'reiyah.perception-revision.packet', 'version': '0.1.0',
                          'comparison_id': case['comparison_id'], 'input_sha256': args.input_sha256,
                          'producer_sha256': implementation_digest()}
                counters = None
                if args.command == 'audit':
                    request = request_input(case, args.request, args.request_sha256)
                    require(bool(args.candidate) == bool(args.candidate_sha256), 'CANDIDATE_BINDING', 'Candidate requires an expected digest')
                    candidate = load_bytes(args.candidate, args.candidate_sha256, validate_input=False) if args.candidate else None
                    payload = audit.produce(case, request, candidate, method=args.proof_method)
                    audit_checker.check(case, request, payload)
                    packet.update(artifact_id='reiyah.perception-revision.audit-packet', request_sha256=args.request_sha256)
                else:
                    prior_args = (args.prior_input, args.prior_input_sha256, args.prior_packet, args.prior_packet_sha256)
                    require(not any(prior_args) or all(prior_args), 'PRIOR_BINDING', 'All four prior input/packet bindings are required')
                    prior = None
                    if all(prior_args):
                        old = load(args.prior_input, args.prior_input_sha256)
                        previous = read_packet(old, args.prior_input_sha256, args.prior_packet, args.prior_packet_sha256)
                        prior = old, previous['payload']
                    counters = {'reused_certificates': 0, 'computed_certificates': 0}
                    payload = kernel.produce(case, prior=prior, counters=counters)
                    checker.check(case, payload)
                packet['payload'] = payload
                answer = {**write_output(args.output, packet), 'certificate_checked': True, 'result': payload['result']}
                if counters is not None:
                    answer['producer_path_counts'] = counters
                    answer['cost_scope'] = 'Counters are producer observations; they do not establish avoided inference or total savings'
    except Invalid as exc:
        sys.stderr.buffer.write(encoded({'status': 'error', **exc.diagnostic()}))
        return 2
    except OSError as exc:
        sys.stderr.buffer.write(encoded({'status': 'error', 'code': 'IO_ERROR', 'detail': str(exc)}))
        return 2
    sys.stdout.buffer.write(encoded(answer))
    return 0 if 'result' not in answer or answer['result']['model_status'] == 'consistent' else 3
