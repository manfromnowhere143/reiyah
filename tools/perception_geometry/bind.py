"""Replay the bound window population, then resolve nominal spatial operands."""
from collections import Counter
from contextlib import ExitStack
import hashlib
import os

from tools.perception_decision.contract import Invalid, parse, wire
from tools.perception_inputs.clock import identity, timestamp
from tools.perception_inputs.sensors import CHANNELS, _rows, _table_streams
from tools.perception_inputs.source_io import require, snapshot
from tools.perception_windows import timeline
from . import algebra

TABLES = ('sensor.json', 'calibrated_sensor.json', 'sample_data.json',
          'scene.json', 'sample.json', 'ego_pose.json')
MAX_CAPTURES = 10_000


def source(spec, limit):
    require(type(spec) is dict and set(spec) == {'path', 'sha256', 'byte_size'} and
            type(spec['path']) is str and 0 < len(spec['path']) <= 4096 and
            type(spec['byte_size']) is int and 0 <= spec['byte_size'] <= limit,
            'GEOMETRY_REQUEST', 'Invalid bounded source descriptor')
    return spec


def read(spec, limit):
    with snapshot(source(spec, limit)) as stream:
        return parse(stream.read())


def matches(actual, expected):
    """Check a typed structural projection; bool must never compare as integer 1."""
    if type(actual) is not type(expected):
        return False
    if type(expected) is dict:
        return all(k in actual and matches(actual[k], v) for k, v in expected.items())
    if type(expected) is list:
        return len(actual) == len(expected) and all(matches(a, e) for a, e in zip(actual, expected))
    return actual == expected


def replay_windows(files, window_report, catalog):
    require(type(window_report) is dict and
            window_report.get('artifact_id') == 'reiyah.perception-windows.report' and
            window_report.get('version') == '0.1.0' and
            window_report.get('profile') == 'all_recorded_captures_closed_plus_minus_2s.0.1.0',
            'GEOMETRY_WINDOW', 'Unsupported window artifact')
    windows = window_report.get('windows')
    require(type(windows) is list and 0 < len(windows) <= 128 and all(type(w) is dict for w in windows),
            'GEOMETRY_WINDOW', 'Expected a bounded window population')
    selection = [{'anchor_id': w.get('anchor_id'), 'sample_token': w.get('sample_token')} for w in windows]
    clocks, selected = timeline.clock_selection(files, catalog, selection)
    groups = timeline.sensor_rows(files, clocks)
    expected = timeline.windows(groups, selected)
    require(matches(windows, expected), 'GEOMETRY_WINDOW_BINDING',
            'Window population, order, captures, channels, clocks or metadata differ from source replay')
    captures = {}
    for w in windows:
        require(set(w['channels']) == set(CHANNELS), 'GEOMETRY_WINDOW', 'Unknown window channel')
        for channel, group in w['channels'].items():
            for r in group['captures']:
                p = r.get('payload')
                require(type(p) is dict and type(p.get('custody_state')) is str and
                        p['custody_state'] in ('not_listed', 'unavailable', 'missing', 'invalid', 'verified') and
                        type(p.get('payload_state')) is str and p['payload_state'] in ('not_checked', 'sensor_invalid', 'decoded'),
                        'GEOMETRY_PAYLOAD_STATE', 'Explicit prior custody and decoding states are required')
                require(p['payload_state'] != 'decoded' or p['custody_state'] == 'verified',
                        'GEOMETRY_PAYLOAD_STATE', 'Decoded payload lacks verified prior custody')
                token = r['sample_data_token']
                record = {k: r[k] for k in ('sample_token', 'capture_timestamp_us', 'calibrated_sensor_token', 'ego_pose_token')}
                record.update(channel=channel, prior_custody_state=p['custody_state'], prior_payload_state=p['payload_state'])
                require(token not in captures or captures[token] == record, 'GEOMETRY_WINDOW_BINDING',
                        'Overlapping windows disagree about a capture')
                captures[token] = record
                require(len(captures) <= MAX_CAPTURES, 'GEOMETRY_LIMIT', 'Too many distinct captures; none are clipped')
    return windows, captures


def rigid_record(row):
    fields = ('translation', 'rotation')
    missing = [k for k in fields if row is None or row.get(k) is None]
    if missing:
        return {'state': 'missing', 'missing_fields': missing}, None
    try:
        matrix = algebra.rigid(row['translation'], row['rotation'])
        q = algebra.vector(row['rotation'], 4)
        return {'state': 'available', 'translation': [wire(v) for v in algebra.vector(row['translation'], 3)],
                'quaternion_wxyz': [wire(v) for v in q], 'quaternion_squared_norm': wire(sum(v*v for v in q)),
                'matrix': algebra.matrix_wire(matrix)}, matrix
    except Invalid as exc:
        return {'state': 'invalid', 'diagnostic': exc.diagnostic()}, None


def time_record(row):
    if row is None or row.get('timestamp') is None:
        return {'state': 'missing', 'timestamp_us': None}
    try:
        return {'state': 'available', 'timestamp_us': timestamp(row['timestamp'])}
    except Invalid as exc:
        return {'state': 'invalid', 'timestamp_us': None, 'diagnostic': exc.diagnostic()}


def intrinsic_record(row, channel):
    if channel == 'LIDAR_TOP':
        return {'state': 'not_applicable'}
    if row is None or row.get('camera_intrinsic') is None:
        return {'state': 'missing'}
    try:
        return {'state': 'available', 'matrix': algebra.matrix_wire(algebra.intrinsic(row['camera_intrinsic'])),
                'distortion_and_image_rectification': 'not_established'}
    except Invalid as exc:
        return {'state': 'invalid', 'diagnostic': exc.diagnostic()}


def operands(files, captures):
    wanted_cals = {r['calibrated_sensor_token']: r['channel'] for r in captures.values()}
    wanted_poses = {r['ego_pose_token'] for r in captures.values()}
    calibrations, poses, cal_matrices, pose_matrices = {}, {}, {}, {}
    files['calibrated_sensor.json'].seek(0)
    for row in _rows(files['calibrated_sensor.json'], 50_000):
        token = identity(row.get('token'))
        if token not in wanted_cals:
            continue
        require(token not in calibrations, 'GEOMETRY_JOIN', 'Duplicate requested calibration')
        rig, matrix = rigid_record(row)
        calibrations[token] = {'sensor_token': identity(row.get('sensor_token')), 'channel': wanted_cals[token],
                               'rigid': rig, 'intrinsic': intrinsic_record(row, wanted_cals[token])}
        cal_matrices[token] = matrix
    for token, channel in sorted(wanted_cals.items()):
        if token not in calibrations:
            calibrations[token] = {'sensor_token': None, 'channel': channel, 'rigid': rigid_record(None)[0],
                                   'intrinsic': intrinsic_record(None, channel)}
            cal_matrices[token] = None
    for row in _rows(files['ego_pose.json'], 5_000_000):
        token = identity(row.get('token'))
        if token not in wanted_poses:
            continue
        require(token not in poses, 'GEOMETRY_JOIN', 'Duplicate requested ego pose')
        rig, matrix = rigid_record(row)
        poses[token] = {'rigid': rig, 'time': time_record(row)}
        pose_matrices[token] = matrix
    for token in sorted(wanted_poses):
        if token not in poses:
            poses[token] = {'rigid': rigid_record(None)[0], 'time': time_record(None)}
            pose_matrices[token] = None
    return calibrations, poses, cal_matrices, pose_matrices


def transform_record(matrix, reasons):
    return {'state': 'available' if matrix is not None else 'unavailable',
            'reasons': reasons, 'matrix': algebra.matrix_wire(matrix) if matrix is not None else None}


def assess(windows, captures, calibrations, poses, cal_matrices, pose_matrices):
    global_matrices = {}
    for token, r in captures.items():
        cal, pose = calibrations[r['calibrated_sensor_token']], poses[r['ego_pose_token']]
        t = pose['time']['timestamp_us']
        aligned = pose['time']['state'] == 'available' and t == r['capture_timestamp_us']
        r['pose_time'] = {'state': ('aligned' if aligned else 'mismatch') if t is not None else pose['time']['state'],
                          'timestamp_us': t, 'pose_minus_capture_us': t-r['capture_timestamp_us'] if t is not None else None}
        reasons = []
        for role, state in (('calibration', cal['rigid']['state']), ('pose', pose['rigid']['state'])):
            if state != 'available':
                reasons.append(role + '_' + state)
        if not aligned:
            reasons.append('pose_time_' + r['pose_time']['state'])
        matrix = None if reasons else algebra.multiply(pose_matrices[r['ego_pose_token']], cal_matrices[r['calibrated_sensor_token']])
        global_matrices[token] = matrix
        r['nominal_sensor_to_global'] = transform_record(matrix, reasons)
        r['nominal_global_to_sensor'] = transform_record(algebra.inverse(matrix) if matrix is not None else None, reasons)
    result = []
    for w in windows:
        keys = [r for r in w['channels']['LIDAR_TOP']['captures']
                if r['is_key_frame'] and r['sample_token'] == w['sample_token']]
        anchor_pose, anchor_matrix, reasons = None, None, []
        if len(keys) != 1:
            reasons.append('anchor_lidar_keyframe_missing')
        else:
            row = keys[0]; anchor_pose = row['ego_pose_token']; pose = poses[anchor_pose]
            if row['capture_timestamp_us'] != w['anchor_timestamp_us']:
                reasons.append('anchor_lidar_time_mismatch')
            if pose['time']['state'] != 'available' or pose['time']['timestamp_us'] != w['anchor_timestamp_us']:
                reasons.append('anchor_pose_time_' + (pose['time']['state'] if pose['time']['state'] != 'available' else 'mismatch'))
            if pose['rigid']['state'] != 'available':
                reasons.append('anchor_pose_' + pose['rigid']['state'])
            if not reasons:
                anchor_matrix = pose_matrices[anchor_pose]
        entries = []
        for channel in CHANNELS:
            for r in w['channels'][channel]['captures']:
                token = r['sample_data_token']; matrix = global_matrices[token]
                why = reasons + captures[token]['nominal_sensor_to_global']['reasons']
                relative = None if why else algebra.multiply(algebra.inverse(anchor_matrix), matrix)
                dt = r['capture_timestamp_us'] - w['anchor_timestamp_us']
                entries.append({'sample_data_token': token, 'capture_minus_anchor_us': dt,
                                'recorded_time_relation': 'equal' if dt == 0 else 'different',
                                'nominal_sensor_to_anchor_ego': transform_record(relative, why),
                                'object_position_at_anchor_time': 'unmeasured'})
        result.append({k: w[k] for k in ('anchor_id', 'sample_token', 'anchor_timestamp_us', 'context_window_us')} |
                      {'anchor_ego_pose_token': anchor_pose, 'nominal_anchor_ego_to_global': transform_record(anchor_matrix, reasons),
                       'captures': entries})
    return result


def build(request):
    require(type(request) is dict and set(request) == {'artifact_id', 'version', 'window_report', 'catalog', 'metadata'} and
            request['artifact_id'] == 'reiyah.perception-geometry.request' and request['version'] == '0.1.0',
            'GEOMETRY_REQUEST', 'Unsupported geometry request')
    report = read(request['window_report'], 128 << 20)
    catalog = read(request['catalog'], 128 << 20)
    meta = source(request['metadata'], 1 << 30)
    require(type(report) is dict and type(report.get('inputs')) is dict and type(catalog) is dict and
            type(catalog.get('sources')) is dict, 'GEOMETRY_BINDING', 'Missing upstream source identities')
    for role in ('catalog', 'metadata'):
        old = report['inputs'].get(role)
        require(type(old) is dict and all(request[role][k] == old.get(k) for k in ('byte_size', 'sha256')),
                'GEOMETRY_BINDING', 'Window and requested source identities differ')
    old = catalog['sources'].get('metadata')
    require(type(old) is dict and all(meta[k] == old.get(k) for k in ('byte_size', 'sha256')),
            'GEOMETRY_BINDING', 'Catalog and geometry metadata identities differ')
    with snapshot(meta) as stream, ExitStack() as stack:
        files = _table_streams(stream, stack, TABLES)
        table_ids = {}
        for name, table in sorted(files.items()):
            size = table.seek(0, os.SEEK_END); table.seek(0)
            table_ids[name] = {'byte_size': size, 'sha256': hashlib.file_digest(table, 'sha256').hexdigest()}
            table.seek(0)
        require(type(report.get('metadata_tables')) is dict and all(
                report['metadata_tables'].get(n) == table_ids[n] for n in TABLES if n != 'ego_pose.json'),
                'GEOMETRY_BINDING', 'Window metadata tables differ from the requested archive')
        windows, captures = replay_windows(files, report, catalog)
        calibrations, poses, cm, pm = operands(files, captures)
        relations = assess(windows, captures, calibrations, poses, cm, pm)
    def counts(values):
        return dict(sorted(Counter(values).items()))
    return {'artifact_id': 'reiyah.perception-geometry.report', 'version': '0.1.0', 'lifecycle_status': 'exploratory',
            'profile': 'nominal_wxyz_column_rigid_capture_time.0.1.0',
            'inputs': {k: request[k] for k in ('window_report', 'catalog', 'metadata')}, 'metadata_tables': table_ids,
            'calibrations': calibrations, 'ego_poses': poses, 'captures': captures, 'windows': relations,
            'summary': {'anchors': len(relations), 'distinct_captures': len(captures),
                        'capture_occurrences': sum(len(w['captures']) for w in relations),
                        'calibrations': len(calibrations), 'ego_poses': len(poses),
                        'nominal_global_transform_states': counts(r['nominal_sensor_to_global']['state'] for r in captures.values()),
                        'pose_time_states': counts(r['pose_time']['state'] for r in captures.values()),
                        'calibration_states': counts(r['rigid']['state'] for r in calibrations.values()),
                        'intrinsic_states': counts(r['intrinsic']['state'] for r in calibrations.values()),
                        'pose_states': counts(r['rigid']['state'] for r in poses.values()),
                        'anchor_transform_states': counts(w['nominal_anchor_ego_to_global']['state'] for w in relations),
                        'relative_transform_states': counts(r['nominal_sensor_to_anchor_ego']['state'] for w in relations for r in w['captures']),
                        'recorded_time_relations': counts(r['recorded_time_relation'] for w in relations for r in w['captures'])},
            'uncertainty': {'calibration_accuracy': 'unmeasured', 'pose_accuracy': 'unmeasured',
                            'clock_synchronization_accuracy': 'unmeasured', 'camera_exposure_duration': 'unmeasured',
                            'lidar_per_point_acquisition_times': 'unmeasured', 'object_motion': 'unmeasured',
                            'online_availability_time': 'unmeasured', 'physical_reference_coverage': 'not_established'},
            'raw_payloads_reopened': False, 'reference_review_readiness': 'not_established', 'selected_study_cohort': None,
            'limits': ['Transforms operate on nominal coordinate systems at the recorded capture time; they do not propagate objects to anchor time.',
                       'A shared metadata timestamp does not establish simultaneous physical exposure, per-point acquisition or delivery time.',
                       'Near-unit quaternion normalization and the intrinsic-form check are format policies, not physical calibration validation.',
                       'Window population and metadata are replayed; earlier raw custody/decoder assertions are inherited by exact artifact identity.',
                       'No image projection, point-cloud merging, object discovery, independent judgment or physical coverage is produced.']}
