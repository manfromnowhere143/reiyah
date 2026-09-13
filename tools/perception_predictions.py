"""Prepare exact submitted prediction rows for exposed offline research.

This is source custody, not annotation-free physical inference or admission.
No association, score/class filtering, deduplication or numeric rewriting occurs.
"""
import argparse
from collections import Counter
import hashlib
import io
import os
from pathlib import Path
import re
import sys

from tools.perception_decision import contract
from tools.perception_decision.cli import atomic_write
from tools.perception_decision.nuscenes import MAX_FRAME_PREDICTIONS, UNAVAILABLE
from tools.perception_inputs import source_io
from tools.perception_inputs.catalog import META_FIELDS
from tools.perception_inputs.source_io import JSONStream, digest_value, private_output_path, require, snapshot

ROOT = Path(__file__).resolve().parent.parent
REQUEST_LIMIT = 1 << 20
MAX_FRAMES = 256
MAX_SOURCES = 8
MAX_SELECTED_BYTES = 24 << 20
MAX_SELECTED_ROWS = 65536
MAX_PACKET_BYTES = 64 << 20
EXPOSURE = 'exposed_retrospective_development'


def closed(value, fields):
    require(type(value) is dict and set(value) == set(fields),
            'PREDICTIONS_REQUEST', 'Unknown or missing request fields')


def identifier(value):
    require(type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', value),
            'PREDICTIONS_REQUEST', 'Require a bounded simple identifier')
    return value


def sample_token(value):
    require(type(value) is str and re.fullmatch(r'[0-9a-f]{32}', value),
            'PREDICTIONS_SAMPLE', 'Require a source sample token')
    return value


def validate_request(request):
    closed(request, ('artifact_id', 'version', 'exposure', 'sources', 'frames'))
    require(request['artifact_id'] == 'reiyah.perception-predictions.request' and
            request['version'] == '0.1.0' and request['exposure'] == EXPOSURE,
            'PREDICTIONS_REQUEST', 'Unsupported identity, version or exposure scope')
    sources, frames = request['sources'], request['frames']
    require(type(sources) is list and 0 < len(sources) <= MAX_SOURCES and
            type(frames) is list and 0 < len(frames) <= MAX_FRAMES,
            'PREDICTIONS_LIMIT', 'Require bounded nonempty source and frame selections')
    ids, tokens = set(), set()
    for frame in frames:
        closed(frame, ('id', 'sample_token'))
        fid, token = identifier(frame['id']), sample_token(frame['sample_token'])
        require(fid not in ids and token not in tokens, 'PREDICTIONS_REQUEST', 'Repeated frame or source sample')
        ids.add(fid); tokens.add(token)
    ids = set()
    for source in sources:
        require(type(source) is dict and type(source.get('state')) is str,
                'PREDICTIONS_REQUEST', 'An explicit source state is required')
        if source['state'] == 'observed':
            closed(source, ('id', 'state', 'path', 'byte_size', 'sha256'))
            require(type(source['path']) is str and 0 < len(source['path']) <= 4096 and
                    '\0' not in source['path'] and Path(source['path']).is_absolute() and
                    type(source['byte_size']) is int and 0 <= source['byte_size'] <= source_io.MAX_SOURCE_BYTES and
                    digest_value(source['sha256']), 'PREDICTIONS_REQUEST', 'Require exact original source identity')
        else:
            closed(source, ('id', 'state', 'reason'))
            require(source['state'] in UNAVAILABLE and type(source['reason']) is str and
                    0 < len(source['reason']) <= 1024, 'PREDICTIONS_REQUEST', 'Malformed unavailable source')
        sid = identifier(source['id'])
        require(sid not in ids, 'PREDICTIONS_REQUEST', 'Repeated configuration identity')
        ids.add(sid)
    return request


def identities():
    # Shared framing, strict request parsing, output writer and fixed format constants.
    names = ('tools/perception_predictions.py', 'tools/perception_inputs/source_io.py',
             'tools/perception_inputs/catalog.py', 'tools/perception_decision/contract.py',
             'tools/perception_decision/cli.py', 'tools/perception_decision/nuscenes.py')
    return {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names}


def row_spans(data, offset):
    """Index objects within an exact original array; retain zero-based source order."""
    reader, spans = JSONStream(io.BytesIO(data)), []
    reader.expect('[')
    if reader.peek() != ']':
        while True:
            require(len(spans) < MAX_FRAME_PREDICTIONS, 'PREDICTIONS_LIMIT', 'Too many prediction rows')
            _, span = reader.value(dict)
            spans.append({'source_index': len(spans), **span, 'byte_offset': offset + span['byte_offset']})
            if reader.peek() == ']':
                break
            reader.expect(',')
    reader.expect(']'); reader.finish()
    return spans


def scan(stream, selected):
    """Scan the entire submitted document before claiming a selected key is absent.

    Only container shape and sample joins are checked. Other row fields, unknown
    fields and nonfinite source literals stay verbatim. Consumers must validate
    the numeric/geometry/class premises of their own computations.
    """
    reader, spans, header, fields = JSONStream(stream), {}, None, set()
    frame_count, row_count = 0, 0
    for name in reader.members(2):
        fields.add(name)
        if name == 'meta':
            header, _ = reader.value(dict)
            require(set(header) == META_FIELDS and all(type(v) is bool for v in header.values()),
                    'PREDICTIONS_FORMAT', 'Unsupported source modality declaration')
        elif name == 'results':
            for token in reader.members(50000):
                sample_token(token)
                rows, span = reader.value(list)
                require(len(rows) <= MAX_FRAME_PREDICTIONS and all(
                    type(row) is dict and row.get('sample_token') == token for row in rows),
                    'PREDICTIONS_FORMAT', 'Oversized frame or incorrect source sample join')
                frame_count += 1; row_count += len(rows)
                if token in selected:
                    spans[token] = {**span, 'row_count': len(rows)}
        else:
            require(False, 'PREDICTIONS_FORMAT', 'Unknown source top-level field')
    reader.finish()
    require(fields == {'meta', 'results'}, 'PREDICTIONS_FORMAT', 'Incomplete prediction source')
    return spans, {'producer_modality_declaration': header,
                   'full_document_frames': frame_count, 'full_document_rows': row_count}


def materialize(request, expected):
    validate_request(request)
    code = identities()
    frames = [{**frame, 'predictions': {}} for frame in request['frames']]
    selected = {frame['sample_token'] for frame in frames}
    files, inventory, total_bytes, total_rows = {}, [], 0, 0
    for source_index, source in enumerate(request['sources']):
        sid = source['id']
        if source['state'] != 'observed':
            inventory.append(dict(source))
            for frame in frames:
                frame['predictions'][sid] = {key: source[key] for key in ('state', 'reason')}
            continue
        with snapshot(source) as stream:
            spans, meta = scan(stream, selected)
            inventory.append({**source, **meta})
            for frame_index, frame in enumerate(frames):
                span = spans.get(frame['sample_token'])
                if span is None:
                    frame['predictions'][sid] = {'state': 'missing', 'source_sha256': source['sha256'],
                                                'reason': 'No results key in the completely scanned verified source'}
                    continue
                total_bytes += span['byte_size']; total_rows += span['row_count']
                require(total_bytes <= MAX_SELECTED_BYTES and total_rows <= MAX_SELECTED_ROWS,
                        'PREDICTIONS_LIMIT', 'Selected original bytes or rows exceed the packet bound')
                stream.seek(span['byte_offset']); data = stream.read(span['byte_size'])
                require(hashlib.sha256(data).hexdigest() == span['sha256'],
                        'PREDICTIONS_SOURCE', 'Selected array differs from its verified original span')
                rows = row_spans(data, span['byte_offset'])
                require(len(rows) == span['row_count'], 'PREDICTIONS_SOURCE', 'Row inventory differs')
                name = f'frames/frame-{frame_index:04d}-source-{source_index:02d}.json'
                files[name] = data
                frame['predictions'][sid] = {'state': 'observed', 'source_sha256': source['sha256'],
                                            'file': name, **span, 'rows': rows}
    summary = {sid: {'states': dict(sorted(Counter(f['predictions'][sid]['state'] for f in frames).items())),
                     'observed_rows': sum(f['predictions'][sid].get('row_count', 0) for f in frames)}
               for sid in (s['id'] for s in request['sources'])}
    require(code == identities(), 'PREDICTIONS_CODE', 'Producer source changed during preparation')
    packet = {'artifact_id': 'reiyah.perception-predictions.packet', 'version': '0.1.0',
              'request_sha256': expected, 'exposure': EXPOSURE, 'producer_source_sha256': code,
              'sources': inventory, 'frames': frames, 'summary': summary,
              'row_index_origin': 0, 'byte_offset_origin': 'start_of_original_submission',
              'row_encoding': 'exact_original_utf8_bytes_no_numeric_rewriting',
              'selection_authority': 'explicit_request_not_verified_independent_of_prior_annotations',
              'coordinate_authority': 'nominal_submission_global_frame_not_physical_accuracy',
              'source_validation': 'bounded_containers_and_sample_joins_only',
              'association_performed': False, 'reference_judgments_admitted': False,
              'decision_evaluated': False, 'human_assistance_released': False}
    files['PREDICTIONS.json'] = contract.encoded(packet)
    require(sum(map(len, files.values())) <= MAX_PACKET_BYTES, 'PREDICTIONS_LIMIT', 'Packet byte bound exceeded')
    return files, summary


def same_files(output, files):
    output = Path(output)
    require(not output.is_symlink() and output.is_dir(), 'PREDICTIONS_PACKET', 'Require a real packet directory')
    require(not (output/'frames').is_symlink() and (output/'frames').is_dir() and
            {p.name for p in output.iterdir()} == {'PREDICTIONS.json', 'frames'},
            'PREDICTIONS_PACKET', 'Unexpected packet entries')
    expected_names = {Path(name).name for name in files if name.startswith('frames/')}
    require({p.name for p in (output/'frames').iterdir()} == expected_names,
            'PREDICTIONS_PACKET', 'Missing or extra frame files')
    for name, data in files.items():
        path = output/name
        require(not path.is_symlink() and path.is_file() and path.stat().st_size == len(data),
                'PREDICTIONS_PACKET', 'Packet file type or size differs')
        with path.open('rb') as stream:
            require(stream.read(len(data)+1) == data, 'PREDICTIONS_PACKET', 'Packet differs from exact source replay')


def request_file(path, expected):
    return validate_request(contract.load(path, expected, REQUEST_LIMIT, validate_input=False))


def prepare(request_path, expected, output):
    request = request_file(request_path, expected)
    target = Path(output)
    require(target.is_absolute() and target.parent.is_dir(), 'PREDICTIONS_OUTPUT', 'Require an absolute fresh private output')
    require(not os.path.lexists(target), 'OUTPUT_EXISTS', 'Refuse an existing output identity')
    forbidden = [ROOT, Path(request_path).resolve().parent]
    forbidden += [Path(s['path']).resolve().parent for s in request['sources'] if s['state'] == 'observed']
    target = private_output_path(target, forbidden, 'PREDICTIONS_OUTPUT', 'Output must be outside code and input directories')
    files, summary = materialize(request, expected)
    request_file(request_path, expected)
    target.mkdir(mode=0o700); (target/'frames').mkdir(mode=0o700)
    for name in sorted(n for n in files if n != 'PREDICTIONS.json'):
        atomic_write(target/name, files[name])
    # The complete manifest appears last; an interrupted write cannot claim completion.
    atomic_write(target/'PREDICTIONS.json', files['PREDICTIONS.json'])
    same_files(target, files)
    return {'status': 'prepared', 'packet_sha256': hashlib.sha256(files['PREDICTIONS.json']).hexdigest(),
            'summary': summary, 'decision_evaluated': False}


def check(request_path, expected, packet, packet_sha256):
    """Replay original sources. This shares the producer, not an independent proof."""
    contract.load(Path(packet)/'PREDICTIONS.json', packet_sha256, MAX_PACKET_BYTES, validate_input=False)
    files, summary = materialize(request_file(request_path, expected), expected)
    require(hashlib.sha256(files['PREDICTIONS.json']).hexdigest() == packet_sha256,
            'PREDICTIONS_PACKET', 'Expected packet differs from original source replay')
    same_files(packet, files)
    return {'status': 'source_replay_matches', 'packet_sha256': packet_sha256,
            'summary': summary, 'independent_checker': False, 'decision_evaluated': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('prepare', 'check'):
        cmd = sub.add_parser(name)
        cmd.add_argument('--request', type=Path, required=True)
        cmd.add_argument('--request-sha256', required=True)
        if name == 'prepare':
            cmd.add_argument('--output', type=Path, required=True)
        else:
            cmd.add_argument('--packet', type=Path, required=True)
            cmd.add_argument('--packet-sha256', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'prepare':
            result = prepare(args.request, args.request_sha256, args.output)
        else:
            result = check(args.request, args.request_sha256, args.packet, args.packet_sha256)
        sys.stdout.buffer.write(contract.encoded(result))
        return 0
    except contract.Invalid as exc:
        diagnostic = exc.diagnostic()
    except OSError as exc:
        diagnostic = {'code': 'IO_ERROR', 'detail': str(exc)}
    sys.stderr.buffer.write(contract.encoded({'status': 'invalid', 'decision_evaluated': False, **diagnostic}))
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
