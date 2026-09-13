"""Conventional selective retrieval audit; no Engine producer/parser imports.

This small comparator requires each selected token to have one literal ASCII JSON
key occurrence. It checks selected arrays/rows, not the producer's complete-source
framing, unavailable states, full-file row counts or modality declarations.
"""
import argparse
from decimal import Decimal
import hashlib
import json
import mmap
from pathlib import Path
import re


def pairs(items):
    result = {}
    for key, value in items:
        assert key not in result, 'Duplicate property'
        result[key] = value
    return result


DECODER = json.JSONDecoder(object_pairs_hook=pairs, parse_float=Decimal, parse_constant=Decimal)


def selected_array(source, token):
    # The independent locator has a narrower explicit syntax domain than the Engine.
    matches = list(re.finditer(b'"'+token.encode('ascii')+b'"[ \t\r\n]*:', source))
    assert len(matches) == 1, 'Expected exactly one literal selected sample key'
    start = matches[0].end()
    while source[start:start+1] in (b' ', b'\t', b'\r', b'\n'):
        start += 1
    # These retained arrays fit in 1 MiB. Trim only a cut UTF-8 suffix from the
    # lookahead; JSON raw_decode must finish inside the available valid prefix.
    lookahead = source[start:start+(1 << 20)+4]
    for trim in range(4):
        try:
            text = (lookahead[:-trim] if trim else lookahead).decode('utf-8')
            break
        except UnicodeDecodeError:
            if trim == 3:
                raise
    values, end = DECODER.raw_decode(text)
    assert type(values) is list and len(values) <= 512
    array = text[:end].encode('utf-8')
    assert len(array) <= 1 << 20
    rows, position = [], 1
    for index, value in enumerate(values):
        while text[position] in ' \t\r\n':
            position += 1
        assert type(value) is dict and value['sample_token'] == token
        decoded, stop = DECODER.raw_decode(text, position)
        raw = text[position:stop].encode('utf-8')
        assert type(decoded) is dict
        rows.append({'source_index': index, 'byte_offset': start+len(text[:position].encode('utf-8')),
                     'byte_size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
        position = stop
        while text[position] in ' \t\r\n':
            position += 1
        if index+1 < len(values):
            assert text[position] == ','
            position += 1
    return array, start, rows


def audit(request_path, request_sha256, packet_dir, packet_sha256):
    request_data = Path(request_path).read_bytes()
    assert hashlib.sha256(request_data).hexdigest() == request_sha256
    request = json.loads(request_data, object_pairs_hook=pairs)
    assert request['artifact_id'] == 'reiyah.perception-predictions.request' and request['version'] == '0.1.0'
    packet_dir = Path(packet_dir)
    packet_data = (packet_dir/'PREDICTIONS.json').read_bytes()
    assert hashlib.sha256(packet_data).hexdigest() == packet_sha256
    packet = json.loads(packet_data, object_pairs_hook=pairs)
    assert packet['artifact_id'] == 'reiyah.perception-predictions.packet' and packet['version'] == '0.1.0'
    assert packet['request_sha256'] == request_sha256 and packet['row_index_origin'] == 0
    assert request['exposure'] == packet['exposure'] == 'exposed_retrospective_development'
    assert packet['association_performed'] is False and packet['reference_judgments_admitted'] is False
    assert packet['decision_evaluated'] is False and packet['human_assistance_released'] is False
    assert [(f['id'], f['sample_token']) for f in packet['frames']] == [
        (f['id'], f['sample_token']) for f in request['frames']], 'Selected frame identity/order changed'
    expected_sources = [s['id'] for s in request['sources']]
    assert len(expected_sources) == len(set(expected_sources))
    assert [s['id'] for s in packet['sources']] == expected_sources
    for frame in packet['frames']:
        assert set(frame['predictions']) == set(expected_sources)
    totals, selected_bytes, files = {}, 0, set()
    for source_index, spec in enumerate(request['sources']):
        assert spec['state'] == 'observed', 'This comparator supports observed selected arrays only'
        assert all(packet['sources'][source_index][key] == value for key, value in spec.items())
        totals[spec['id']] = 0
        with open(spec['path'], 'rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as original:
            assert len(original) == spec['byte_size']
            assert hashlib.sha256(original).hexdigest() == spec['sha256']
            for frame_index, frame in enumerate(packet['frames']):
                array, offset, rows = selected_array(original, frame['sample_token'])
                view = frame['predictions'][spec['id']]
                assert view['state'] == 'observed' and view['source_sha256'] == spec['sha256']
                assert view['row_count'] == len(rows) and view['rows'] == rows, 'Omitted, reordered or misbound original row'
                assert view['byte_offset'] == offset and view['byte_size'] == len(array)
                assert view['sha256'] == hashlib.sha256(array).hexdigest()
                name = f'frames/frame-{frame_index:04d}-source-{source_index:02d}.json'
                assert view['file'] == name and name not in files
                target = packet_dir/name
                assert not target.is_symlink() and target.read_bytes() == array
                files.add(name); totals[spec['id']] += len(rows); selected_bytes += len(array)
            # Detect modification of the mapped original bytes during this audit.
            # Path replacement is outside this check; this is not a copied snapshot.
            assert hashlib.sha256(original).hexdigest() == spec['sha256']
    assert {str(p.relative_to(packet_dir)) for p in packet_dir.rglob('*') if p.is_file()} == files|{'PREDICTIONS.json'}
    assert packet['summary'] == {sid: {'observed_rows': total, 'states': {'observed': len(request['frames'])}}
                                 for sid, total in totals.items()}
    return {'artifact_id': 'reiyah.perception-predictions.conventional-audit', 'version': '0.1.0',
            'status': 'all_selected_original_rows_agree', 'request_sha256': request_sha256,
            'packet_sha256': packet_sha256, 'selected_frames': len(request['frames']),
            'rows': totals, 'selected_original_bytes': selected_bytes,
            'shared_trusted_code': 'Python runtime and standard library; no Engine producer or framing imports',
            'not_checked': ['complete-source JSON framing and counts', 'unavailable sources or absent sample keys',
                            'physical validity', 'association correctness', 'historical selection independence']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True)
    parser.add_argument('--request-sha256', required=True)
    parser.add_argument('--packet', required=True)
    parser.add_argument('--packet-sha256', required=True)
    args = parser.parse_args()
    try:
        result = audit(args.request, args.request_sha256, args.packet, args.packet_sha256)
    except (AssertionError, OSError, ValueError, KeyError, IndexError, TypeError) as exc:
        print(json.dumps({'status': 'invalid_or_outside_comparator_scope', 'detail': str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
