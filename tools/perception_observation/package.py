"""Explicit projection, raw-byte revalidation, and separately bound disclosure seal."""
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import re

from tools.perception_decision.cli import atomic_write
from tools.perception_decision.contract import Invalid, encoded, parse
from tools.perception_geometry.bind import read
from tools.perception_inputs.sensors import CHANNELS
from tools.perception_inputs.source_io import digest_value, require
from tools.perception_windows import payloads
from tools.perception_windows.__main__ import runtime
from tools.perception_windows.timeline import relative_path
from . import contract, formats


def code_identities():
    root = Path(__file__).resolve().parent.parent
    return [[str(p.relative_to(root)), hashlib.sha256(p.read_bytes()).hexdigest()]
            for folder in ('perception_observation', 'perception_geometry', 'perception_windows',
                           'perception_inputs', 'perception_decision')
            for p in sorted((root/folder).glob('*.py'))]


def descriptor(filename, data):
    return {'filename': filename, 'byte_size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def same_identity(a, b):
    return (type(a) is dict and type(b) is dict and type(a.get('byte_size')) is int
            and type(b.get('byte_size')) is int and a['byte_size'] == b['byte_size']
            and digest_value(a.get('sha256')) and a['sha256'] == b.get('sha256'))


def source_text(value):
    require(type(value) is str and 0 < len(value) <= 4096, 'OBS_SOURCE', 'Invalid required source string')
    return value


def source_time(value):
    return contract.integer(value, 0, 2**63-2_000_001, 'OBS_SOURCE')


def projected_transform(value):
    require(type(value) is dict and value.get('state') in ('available', 'unavailable'),
            'OBS_SOURCE', 'Invalid source transform state')
    result = {'state': value['state']}
    if value['state'] == 'available':
        require('matrix' in value, 'OBS_SOURCE', 'Missing nominal matrix')
        result['matrix'] = deepcopy(value['matrix'])
    else:
        require(value.get('matrix') is None, 'OBS_SOURCE', 'Unavailable source carries a matrix')
    contract.transform(result)
    return result


def projected_intrinsic(value, channel):
    require(type(value) is dict and type(value.get('state')) is str,
            'OBS_SOURCE', 'Missing source intrinsic state')
    result = {'state': value['state']}
    if value['state'] == 'available':
        require('matrix' in value, 'OBS_SOURCE', 'Missing nominal camera intrinsics')
        result['matrix'] = deepcopy(value['matrix'])
    contract.intrinsic(result, channel)
    return result


def project(request, windows, geometry):
    """Consume only the checked geometry report's declared raw-window population.

    This consumer checks joins and numeric forms; the upstream spatial computation
    remains a bound dependency, not a theorem re-proved by these disclosure checks.
    Extra upstream prose is deliberately ignored and never copied into the package.
    """
    require(type(windows) is dict and windows.get('artifact_id') == 'reiyah.perception-windows.report'
            and windows.get('version') == '0.1.0'
            and windows.get('profile') == 'all_recorded_captures_closed_plus_minus_2s.0.1.0',
            'OBS_SOURCE', 'Unsupported source window report')
    require(type(geometry) is dict and geometry.get('artifact_id') == 'reiyah.perception-geometry.report'
            and geometry.get('version') == '0.1.0'
            and geometry.get('profile') == 'nominal_wxyz_column_rigid_capture_time.0.1.0',
            'OBS_SOURCE', 'Unsupported source geometry report')
    require(type(geometry.get('inputs')) is dict and type(windows.get('inputs')) is dict
            and same_identity(geometry['inputs'].get('window_report'), request['window_report'])
            and same_identity(windows['inputs'].get('inventory'), request['inventory']),
            'OBS_BINDING', 'Geometry, windows and asset inventory are not bound to the same inputs')
    ws, gs = windows.get('windows'), geometry.get('windows')
    require(type(ws) is list and type(gs) is list and 0 < len(ws) == len(gs) <= 128
            and type(geometry.get('captures')) is dict and type(geometry.get('calibrations')) is dict,
            'OBS_SOURCE', 'Invalid source population containers')
    result = {'artifact_id': 'reiyah.perception-observation.package', 'version': '0.1.0',
              'profile': contract.PROFILE, 'package_id': request['package_id'],
              'phase': 'unassisted_discovery', 'captures': [], 'windows': []}
    source_captures, tokens, mappings, filenames, anchors = {}, {}, [], {}, set()
    for wi, (w, g) in enumerate(zip(ws, gs), 1):
        require(type(w) is dict and type(g) is dict, 'OBS_SOURCE', 'Malformed source window')
        for key in ('anchor_id', 'sample_token'):
            require(source_text(w.get(key)) == g.get(key), 'OBS_BINDING', 'Source window identity differs')
        anchor = source_time(w.get('anchor_timestamp_us'))
        require(type(g.get('anchor_timestamp_us')) is int and g['anchor_timestamp_us'] == anchor,
                'OBS_BINDING', 'Source anchor clocks differ')
        require(w['anchor_id'] not in anchors, 'OBS_BINDING', 'Repeated source anchor')
        anchors.add(w['anchor_id'])
        for window in (w, g):
            interval = window.get('context_window_us')
            require(type(interval) is list and len(interval) == 2 and all(type(t) is int for t in interval)
                    and interval == [anchor-2_000_000, anchor+2_000_000], 'OBS_SOURCE', 'Unexpected source interval')
        contract.closed(w.get('channels'), CHANNELS, 'OBS_SOURCE')
        require(type(g.get('captures')) is list and len(g['captures']) <= contract.MAX_CAPTURES,
                'OBS_SOURCE', 'Invalid source relative-transform population')
        gw = {}
        for r in g['captures']:
            require(type(r) is dict, 'OBS_SOURCE', 'Malformed source relative transform')
            token = source_text(r.get('sample_data_token'))
            require(token not in gw, 'OBS_BINDING', 'Duplicate relative-transform occurrence')
            gw[token] = r
        out = {'id': f'window-{wi:04d}', 'interval_us': [-2_000_000, 2_000_000], 'channels': {}}
        seen = []
        for channel in CHANNELS:
            group = w['channels'][channel]
            require(type(group) is dict and type(group.get('captures')) is list
                    and len(group['captures']) <= contract.MAX_CAPTURES,
                    'OBS_SOURCE', 'Invalid source channel population')
            bounds = {}
            for side in ('start', 'end'):
                boundary = group.get(side+'_boundary')
                require(type(boundary) is dict, 'OBS_SOURCE', 'Missing recording boundary')
                bounds[side] = boundary.get('state')
            target = {'recording_boundary': bounds, 'captures': []}
            for r in group['captures']:
                require(type(r) is dict, 'OBS_SOURCE', 'Malformed source capture')
                token = source_text(r.get('sample_data_token'))
                require(token in gw and token not in seen, 'OBS_BINDING', 'Capture missing or repeated in geometry')
                seen.append(token)
                capture_time = source_time(r.get('capture_timestamp_us'))
                fields = {k: source_text(r.get(k)) for k in ('sample_token', 'calibrated_sensor_token', 'ego_pose_token')}
                fields.update(channel=channel, capture_timestamp_us=capture_time)
                gc = geometry['captures'].get(token)
                require(type(gc) is dict and all(type(gc.get(k)) is type(v) and gc[k] == v for k,v in fields.items()),
                        'OBS_BINDING', 'Capture channel, clock or pose/calibration join differs')
                cal = geometry['calibrations'].get(fields['calibrated_sensor_token'])
                require(type(cal) is dict and cal.get('channel') == channel, 'OBS_BINDING', 'Calibration channel differs')
                name = relative_path(r.get('filename'))
                shape = None if channel == 'LIDAR_TOP' else [r.get('width'), r.get('height')]
                intrinsic = projected_intrinsic(cal.get('intrinsic'), channel)
                row = fields | {'filename': name, 'image_shape': shape, 'intrinsic': intrinsic}
                require(token not in source_captures or source_captures[token] == row,
                        'OBS_BINDING', 'Overlapping windows disagree about raw evidence')
                require(name not in filenames or filenames[name] == token,
                        'OBS_BINDING', 'Different captures alias one source file')
                if token not in tokens:
                    require(len(tokens) < contract.MAX_CAPTURES, 'OBS_LIMIT', 'Too many captures; none are clipped')
                    cid = f'capture-{len(tokens)+1:06d}'
                    tokens[token] = cid; source_captures[token] = row; filenames[name] = token
                    result['captures'].append({'id': cid, 'channel': channel, 'image_shape': shape,
                                               'intrinsic': intrinsic, 'evidence': {'state': 'not_checked'}})
                gr = gw[token]; dt = capture_time-anchor
                require(type(gr.get('capture_minus_anchor_us')) is int and gr['capture_minus_anchor_us'] == dt,
                        'OBS_BINDING', 'Relative capture clock differs')
                target['captures'].append({'capture_id': tokens[token], 'time_offset_us': dt,
                    'sensor_to_anchor_ego': projected_transform(gr.get('nominal_sensor_to_anchor_ego'))})
            out['channels'][channel] = target
        require(seen == list(gw), 'OBS_BINDING', 'Geometry occurrence population or order differs')
        result['windows'].append(out)
        mappings.append({'window_id': out['id'], 'anchor_id': w['anchor_id'], 'sample_token': w['sample_token'],
                         'scene_token': w.get('scene_token'), 'anchor_timestamp_us': anchor})
    require(set(tokens) == set(geometry['captures']), 'OBS_BINDING', 'Geometry capture union differs')
    contract.validate(result)
    return result, source_captures, tokens, mappings


def disclose(root_fd, row, spec, cid):
    if spec is None:
        return {'state': 'not_listed'}, None
    if spec['state'] == 'unavailable':
        return {'state': 'unavailable'}, None
    try:
        data = payloads.raw_bytes(root_fd, spec)
    except FileNotFoundError:
        return {'state': 'missing'}, None
    except (Invalid, OSError):
        return {'state': 'invalid'}, None
    try:
        if row['channel'] == 'LIDAR_TOP':
            data, count = formats.lidar(data)
            return {'state': 'delivered', 'asset': descriptor(f'assets/{cid}.ply', data), 'point_count': count}, data
        data = formats.camera(data, *row['image_shape'])
        return {'state': 'delivered', 'asset': descriptor(f'assets/{cid}.jpg', data)}, data
    except Invalid as exc:
        if exc.code == 'OBS_JPEG_PROFILE':
            state = 'withheld'
        elif exc.code in ('WINDOW_DECODER_UNAVAILABLE', 'WINDOW_DECODER_CONFIGURATION', 'WINDOW_RUNTIME'):
            state = 'not_checked'
        else:
            state = 'sensor_invalid'
        return {'state': state}, None


def build(request, output, custody):
    contract.closed(request, ('artifact_id', 'version', 'package_id', 'window_report', 'geometry_report', 'inventory', 'raw_root'),
                    'OBS_REQUEST')
    require(request['artifact_id'] == 'reiyah.perception-observation.request' and request['version'] == '0.1.0'
            and type(request['package_id']) is str and re.fullmatch('[0-9a-f]{32}', request['package_id']) is not None,
            'OBS_REQUEST', 'Unsupported request identity')
    require(type(request['raw_root']) is str and Path(request['raw_root']).is_absolute(),
            'OBS_REQUEST', 'Explicit absolute raw root is required')
    output, custody = Path(output), Path(custody)
    require(not os.path.lexists(output) and not os.path.lexists(custody), 'OUTPUT_EXISTS', 'Output identity already exists')
    require(not custody.resolve().is_relative_to(output.resolve()), 'OBS_CUSTODY', 'Custody must be outside the disclosure directory')
    code, environment = code_identities(), runtime()
    windows = read(request['window_report'], contract.MAX_MANIFEST)
    geometry = read(request['geometry_report'], contract.MAX_MANIFEST)
    assets = payloads.inventory(read(request['inventory'], 64 << 20))
    manifest, source_rows, tokens, window_mapping = project(request, windows, geometry)
    needed = [assets.get(row['filename']) for row in source_rows.values()]
    require(sum(s['byte_size']+1024 for s in needed if s and s['state'] == 'retained') <= contract.MAX_TOTAL,
            'OBS_LIMIT', 'Declared evidence exceeds package bound; no population is clipped')
    # Directory creation is non-overwriting. Failure retains an unsealed partial
    # directory. Two output locations are not claimed to form an atomic transaction.
    root_fd = os.open(request['raw_root'], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        output.mkdir(mode=0o700)
        (output/'assets').mkdir(mode=0o700)
        mapping = []
        for record, (token, row) in zip(manifest['captures'], source_rows.items()):
            spec = assets.get(row['filename'])
            evidence, data = disclose(root_fd, row, spec, tokens[token])
            record['evidence'] = evidence
            if data is not None:
                atomic_write(output/evidence['asset']['filename'], data)
            mapping.append({'capture_id': tokens[token], 'sample_data_token': token, 'source': row,
                            'raw_identity': spec, 'disclosed_evidence': evidence})
    finally:
        os.close(root_fd)
    summary = contract.validate(manifest)
    data = encoded(manifest)
    require(len(data) <= contract.MAX_MANIFEST, 'OBS_LIMIT', 'Manifest exceeds byte bound')
    atomic_write(output/'manifest.json', data)
    atomic_write(output/'READ_ME.txt', contract.GUIDE)
    seal = {'artifact_id': 'reiyah.perception-observation.seal', 'version': '0.1.0',
            'package_id': request['package_id'], 'manifest': descriptor('manifest.json', data),
            'guide': descriptor('READ_ME.txt', contract.GUIDE)}
    seal_bytes = encoded(seal); seal_digest = hashlib.sha256(seal_bytes).hexdigest()
    require(code == code_identities() and environment == runtime(), 'OBS_CODE_CHANGED', 'Code or runtime changed during packaging')
    custody_record = {'artifact_id': 'reiyah.perception-observation.custody', 'version': '0.1.0',
        'lifecycle_status': 'exploratory', 'request': request, 'request_sha256': hashlib.sha256(encoded(request)).hexdigest(),
        'output': str(output.resolve()), 'expected_seal_sha256': seal_digest, 'source_identities': code,
        'runtime': environment, 'windows': window_mapping, 'captures': mapping, 'summary': summary,
        'geometry_computation': 'bound_upstream_dependency_not_reproved_by_disclosure_checks',
        'authority': 'byte_custody_only_not_human_independence_or_physical_truth',
        'blinding': 'declared_metadata_allowlist_not_source_anonymity_or_pixel_steganography_protection'}
    atomic_write(custody, encoded(custody_record))
    # Last write marks completion. The expected digest lives in separate custody.
    atomic_write(output/'SEAL.json', seal_bytes)
    return {'package_id': request['package_id'], 'seal_sha256': seal_digest, 'summary': summary}


def read_relative(root_fd, name, limit, expected):
    with payloads.asset_file(root_fd, name) as stream:
        data = stream.read(limit+1)
    require(len(data) <= limit and hashlib.sha256(data).hexdigest() == expected,
            'OBS_FILE_IDENTITY', 'Disclosed bytes differ from the expected identity')
    return data


def verify(output, expected_seal):
    require(digest_value(expected_seal), 'OBS_SEAL', 'Separately retained expected seal digest is required')
    fd = os.open(output, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        require(set(os.listdir(fd)) == {'SEAL.json', 'manifest.json', 'READ_ME.txt', 'assets'},
                'OBS_FILE_SET', 'Package is incomplete or includes unexpected material')
        seal = parse(read_relative(fd, 'SEAL.json', 8192, expected_seal))
        contract.closed(seal, ('artifact_id', 'version', 'package_id', 'manifest', 'guide'))
        require(seal['artifact_id'] == 'reiyah.perception-observation.seal' and seal['version'] == '0.1.0',
                'OBS_SEAL', 'Unsupported completion seal')
        contract.identity(seal['manifest'], 'manifest.json', contract.MAX_MANIFEST)
        contract.identity(seal['guide'], 'READ_ME.txt', len(contract.GUIDE))
        manifest_bytes = read_relative(fd, 'manifest.json', seal['manifest']['byte_size'], seal['manifest']['sha256'])
        require(len(manifest_bytes) == seal['manifest']['byte_size'], 'OBS_FILE_IDENTITY', 'Manifest length differs')
        guide = read_relative(fd, 'READ_ME.txt', seal['guide']['byte_size'], seal['guide']['sha256'])
        require(guide == contract.GUIDE and len(guide) == seal['guide']['byte_size'], 'OBS_GUIDE', 'Guide is not the fixed disclosure profile')
        manifest = parse(manifest_bytes); summary = contract.validate(manifest)
        require(seal['package_id'] == manifest['package_id'], 'OBS_SEAL', 'Package identity differs')
        expected_files = {r['evidence']['asset']['filename'].split('/')[1]
                          for r in manifest['captures'] if r['evidence']['state'] == 'delivered'}
        assets_fd = os.open('assets', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
        try:
            require(set(os.listdir(assets_fd)) == expected_files, 'OBS_FILE_SET', 'Missing or unexpected raw evidence file')
        finally:
            os.close(assets_fd)
        for row in manifest['captures']:
            e = row['evidence']
            if e['state'] != 'delivered':
                continue
            spec = e['asset']
            data = read_relative(fd, spec['filename'], spec['byte_size'], spec['sha256'])
            require(len(data) == spec['byte_size'], 'OBS_FILE_IDENTITY', 'Evidence length differs')
            if row['channel'] == 'LIDAR_TOP':
                formats.verify_ply(data, e['point_count'])
            else:
                formats.camera(data, *row['image_shape'])
        return {'package_id': manifest['package_id'], 'seal_sha256': expected_seal,
                'disclosure_verified': True, 'summary': summary}
    finally:
        os.close(fd)
