"""Audit full recorded sensor windows without selecting or judging a study cohort."""
import argparse
from collections import Counter, defaultdict
from contextlib import ExitStack
import hashlib
import os
from pathlib import Path
import platform
import sys

from tools.perception_decision.cli import atomic_write
from tools.perception_decision.contract import Invalid, encoded, load
from tools.perception_inputs.sensors import _table_streams
from tools.perception_inputs.source_io import document, require, snapshot
from . import payloads, timeline


def source(spec, limit):
    require(type(spec) is dict and set(spec) == {'path', 'sha256', 'byte_size'} and
            type(spec['path']) is str and 0 < len(spec['path']) <= 4096 and
            type(spec['byte_size']) is int and 0 <= spec['byte_size'] <= limit,
            'WINDOW_REQUEST', 'Invalid bounded source descriptor')
    return spec


def read(spec, limit):
    with snapshot(source(spec, limit)) as stream:
        return document(stream.read())


def runtime():
    result = {'python': platform.python_version(), 'platform': sys.platform, 'byteorder': sys.byteorder}
    try:
        import PIL
        from PIL import Image, ImageFile, features
        result['pillow'] = {'version': PIL.__version__, 'jpeg_version': features.version('jpg'),
            'libjpeg_turbo_version': features.version('libjpeg_turbo'),
            'truncated_image_tolerance': ImageFile.LOAD_TRUNCATED_IMAGES,
            'decoder_module_sha256': hashlib.sha256(Path(Image.core.__file__).read_bytes()).hexdigest()}
    except ImportError:
        result['pillow'] = {'state': 'unavailable'}
    return result


def build(request):
    require(type(request) is dict and set(request) == {'artifact_id', 'version', 'catalog', 'metadata', 'inventory', 'raw_root', 'anchors'} and
            request['artifact_id'] == 'reiyah.perception-windows.request' and request['version'] == '0.1.0',
            'WINDOW_REQUEST', 'Unsupported window request')
    require(type(request['raw_root']) is str and 0 < len(request['raw_root']) <= 4096 and
            Path(request['raw_root']).is_absolute(), 'WINDOW_REQUEST', 'Raw root must be an explicit absolute path')
    catalog = read(request['catalog'], 128 << 20)
    require(type(catalog) is dict and type(catalog.get('sources')) is dict and
            type(catalog['sources'].get('metadata')) is dict, 'WINDOW_CATALOG', 'Catalog has no metadata binding')
    meta = source(request['metadata'], 1 << 30)
    require(all(meta[k] == catalog['sources']['metadata'].get(k) for k in ('sha256', 'byte_size')),
            'WINDOW_CATALOG', 'Window and catalog metadata identities differ')
    assets = payloads.inventory(read(request['inventory'], 64 << 20))
    with snapshot(meta) as stream, ExitStack() as stack:
        files = _table_streams(stream, stack, ('sensor.json', 'calibrated_sensor.json',
                                            'sample_data.json', 'scene.json', 'sample.json'))
        table_identities = {}
        for name, table in sorted(files.items()):
            size = table.seek(0, os.SEEK_END)
            table.seek(0)
            table_identities[name] = {'byte_size': size, 'sha256': hashlib.file_digest(table, 'sha256').hexdigest()}
            table.seek(0)
        actual, selected = timeline.clock_selection(files, catalog, request['anchors'])
        groups = timeline.sensor_rows(files, actual)
        windows = timeline.windows(groups, selected)
    observations = {}
    root_fd = os.open(request['raw_root'], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for window in windows:
            for channel, group in window['channels'].items():
                for capture in group['captures']:
                    name = capture['filename']
                    if name not in observations:
                        observations[name] = payloads.inspect(root_fd, capture, assets, channel)
                    capture['payload'] = observations[name]
                good = [r['capture_timestamp_us'] for r in group['captures'] if r['payload']['payload_state'] == 'decoded']
                group['decoded_capture_count'] = len(good)
                group['decoded_timing'] = {
                    'capture_span_us': [good[0], good[-1]] if good else None,
                    'max_inter_capture_gap_us': max((b-a for a,b in zip(good,good[1:])), default=None),
                    'start_to_first_capture_us': good[0]-window['context_window_us'][0] if good else None,
                    'last_capture_to_end_us': window['context_window_us'][1]-good[-1] if good else None}
                group['all_recorded_payloads_decoded'] = bool(group['captures']) and len(good) == len(group['captures'])
            window['recorded_window_complete'] = window['has_declared_scene_context'] and all(
                g['all_recorded_payloads_decoded'] and g['start_boundary']['state'] == g['end_boundary']['state'] == 'bracketed'
                for g in window['channels'].values())
            window['reference_review_readiness'] = 'not_established'
    finally:
        os.close(root_fd)
    digests = defaultdict(list)
    for path, row in observations.items():
        if row['custody_state'] == 'verified':
            digests[row['expected_sha256']].append(path)
    return {'artifact_id': 'reiyah.perception-windows.report', 'version': '0.1.0', 'lifecycle_status': 'exploratory',
        'request_sha256': hashlib.sha256(encoded(request)).hexdigest(),
        'inputs': {k: request[k] for k in ('catalog', 'metadata', 'inventory')}, 'raw_root': request['raw_root'],
        'metadata_tables': table_identities,
        'profile': 'all_recorded_captures_closed_plus_minus_2s.0.1.0', 'windows': windows,
        'summary': {'anchors': len(windows), 'required_capture_occurrences': sum(
                g['capture_count'] for w in windows for g in w['channels'].values()),
            'distinct_required_payloads': len(observations),
            'custody_states': dict(sorted(Counter(r['custody_state'] for r in observations.values()).items())),
            'payload_states': dict(sorted(Counter(r['payload_state'] for r in observations.values()).items())),
            'complete_recorded_windows': sum(w['recorded_window_complete'] for w in windows),
            'repeated_verified_digest_groups': sum(len(v) > 1 for v in digests.values())},
        'repeated_verified_digests': [{'sha256': h, 'filenames': paths} for h,paths in sorted(digests.items()) if len(paths) > 1],
        'physical_coverage': 'not_established', 'independent_review': 'not_performed', 'selected_study_cohort': None,
        'limits': ['Recorded stream coverage and full decoding do not establish continuous observation or physical visibility.',
                   'Expected raw hashes come from the declared custody inventory, not from independent publisher authentication.',
                   'Calibration accuracy, coordinate transforms, exposure duration, point acquisition times and online availability are not validated.',
                   'No minimum temporal resolution for physical review is asserted; capture gaps and missing context remain explicit.',
                   'No files outside the closed window are opened. Boundary witnesses are metadata only.']}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request', type=Path, required=True); p.add_argument('--request-sha256', required=True)
    p.add_argument('--output', type=Path, required=True); args = p.parse_args(argv)
    try:
        require(not args.output.exists(), 'OUTPUT_EXISTS', 'Output identity is already consumed')
        request = load(args.request, args.request_sha256, validate_input=False)
        root = Path(__file__).resolve().parent.parent
        paths = sorted(p for folder in ('perception_windows', 'perception_inputs', 'perception_decision') for p in (root/folder).glob('*.py'))
        def identities():
            return [[str(p.relative_to(root)), hashlib.sha256(p.read_bytes()).hexdigest()] for p in paths]
        code, environment = identities(), runtime()
        result = build(request)
        require(code == identities() and environment == runtime(), 'WINDOW_CODE_CHANGED', 'Implementation/runtime identity changed during audit')
        result.update(source_identities=code, runtime=environment, request_file_sha256=args.request_sha256)
        data = encoded(result)
        require(len(data) <= 128 << 20, 'WINDOW_OUTPUT_SIZE', 'Report exceeds limit; no capture is clipped')
        atomic_write(args.output, data)
        sys.stdout.buffer.write(encoded({'output': str(args.output), 'sha256': hashlib.sha256(data).hexdigest(),
                                        'byte_size': len(data), 'summary': result['summary']}))
        return 0
    except Invalid as exc:
        sys.stderr.buffer.write(encoded({'status': 'invalid', **exc.diagnostic()}))
    except OSError as exc:
        sys.stderr.buffer.write(encoded({'status': 'invalid', 'code': 'IO_ERROR', 'detail': str(exc)}))
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
