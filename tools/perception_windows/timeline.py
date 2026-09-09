"""All recorded captures in a closed clock window, with explicit stream endpoints."""
from collections import defaultdict
from pathlib import PurePosixPath

from tools.perception_inputs.clock import CONTEXT_US, identity, population, timestamp
from tools.perception_inputs.sensors import CHANNELS, _rows
from tools.perception_inputs.source_io import document, require

MAX_SELECTED_ROWS = 400_000


def relative_path(value):
    require(type(value) is str and 0 < len(value) <= 1024 and '\\' not in value and '\0' not in value,
            'WINDOW_PATH', 'Invalid relative sensor path')
    p = PurePosixPath(value)
    require(not p.is_absolute() and all(part not in ('', '.', '..') for part in value.split('/')),
            'WINDOW_PATH', 'Sensor paths must be canonical and relative')
    return value


def clock_selection(files, catalog, selected):
    require(catalog.get('artifact_id') == 'reiyah.perception-inputs.catalog' and catalog.get('version') == '0.1.0',
            'WINDOW_CATALOG', 'Unsupported source catalog')
    rows = catalog.get('anchors')
    require(type(rows) is list and 0 < len(rows) <= 50_000, 'WINDOW_CATALOG', 'Invalid clock population')
    by_sample = {}
    for row in rows:
        require(type(row) is dict, 'WINDOW_CATALOG', 'Malformed clock row')
        sample = identity(row.get('sample_token'))
        require(sample not in by_sample, 'WINDOW_CATALOG', 'Duplicate clock anchor')
        identity(row.get('scene_name')); identity(row.get('scene_token')); timestamp(row.get('anchor_timestamp_us'))
        require(type(row.get('has_declared_scene_context')) is bool and
                type(row.get('context_window_us')) is list and len(row['context_window_us']) == 2 and
                all(type(t) is int for t in row['context_window_us']), 'WINDOW_CATALOG', 'Invalid clock state types')
        require(type(row.get('keyframe_metadata')) is dict and set(row['keyframe_metadata']) == set(CHANNELS) and
                all(type(v) is dict for v in row['keyframe_metadata'].values()),
                'WINDOW_CATALOG', 'Invalid keyframe channel states')
        by_sample[sample] = row
    require(type(selected) is list and 0 < len(selected) <= 128, 'WINDOW_SELECTION', 'Invalid requested population')
    names, ids, tokens = set(), set(), set()
    for row in selected:
        require(type(row) is dict and set(row) == {'anchor_id', 'sample_token'}, 'WINDOW_SELECTION', 'Invalid requested anchor')
        aid, token = identity(row['anchor_id']), identity(row['sample_token'])
        require(aid not in ids and token not in tokens and token in by_sample, 'WINDOW_SELECTION', 'Repeated or unknown requested anchor')
        ids.add(aid); tokens.add(token)
        names.add(by_sample[token]['scene_name'])
    tables = {}
    for name in ('scene.json', 'sample.json'):
        data = files[name].read((16 << 20) + 1)
        require(len(data) <= 16 << 20, 'METADATA_SIZE', 'Clock table exceeds its limit')
        tables[name] = document(data)
        require(type(tables[name]) is list and len(tables[name]) <= 50_000, 'METADATA_TABLE', 'Invalid clock table')
    actual = population(tables, sorted(names))
    # Recompute complete selected-scene clocks, including endpoints, from the metadata.
    fields = ('sample_token', 'scene_token', 'scene_name', 'anchor_timestamp_us',
              'context_window_us', 'has_declared_scene_context')
    require({a['sample_token'] for a in actual} ==
            {a['sample_token'] for a in rows if a.get('scene_name') in names},
            'WINDOW_CATALOG', 'Selected-scene clock population differs from metadata')
    for a in actual:
        require(all(by_sample[a['sample_token']].get(k) == a[k] for k in fields),
                'WINDOW_CATALOG', 'Clock or context differs from bound metadata')
    return actual, {r['anchor_id']: by_sample[r['sample_token']] for r in selected}


def sensor_rows(files, anchors):
    sensors, cals = {}, {}
    for row in _rows(files['sensor.json'], 10_000):
        token = identity(row.get('token'))
        require(token not in sensors and type(row.get('channel')) is str, 'WINDOW_METADATA', 'Invalid sensor identity')
        c = row['channel']
        require(c not in CHANNELS or row.get('modality') == ('lidar' if c == 'LIDAR_TOP' else 'camera'),
                'WINDOW_METADATA', 'Sensor modality differs')
        sensors[token] = c
    for row in _rows(files['calibrated_sensor.json'], 50_000):
        token, sensor = identity(row.get('token')), identity(row.get('sensor_token'))
        require(token not in cals and sensor in sensors, 'WINDOW_METADATA', 'Unresolved or duplicate calibration')
        cals[token] = sensors[sensor]
    samples = {a['sample_token']: a['scene_token'] for a in anchors}
    groups, tokens, paths = defaultdict(list), set(), set()
    for row in _rows(files['sample_data.json'], 5_000_000):
        require(type(row.get('sample_token')) is str, 'WINDOW_METADATA', 'Capture has no sample identity')
        if row['sample_token'] not in samples:
            continue
        cal = identity(row.get('calibrated_sensor_token'))
        require(cal in cals, 'WINDOW_METADATA', 'Unresolved capture calibration')
        channel = cals[cal]
        if channel not in CHANNELS:
            continue
        token, path = identity(row.get('token')), relative_path(row.get('filename'))
        require(token not in tokens and path not in paths and len(tokens) < MAX_SELECTED_ROWS,
                'WINDOW_METADATA', 'Repeated capture/path or selected-scene row limit exceeded')
        tokens.add(token); paths.add(path)
        require(type(row.get('is_key_frame')) is bool, 'WINDOW_METADATA', 'Keyframe status is not Boolean')
        prev, following = row.get('prev'), row.get('next')
        for neighbor in (prev, following):
            if neighbor != '':
                identity(neighbor)
        width, height = row.get('width'), row.get('height')
        require(type(width) is int and type(height) is int and 0 <= width <= 16_384 and 0 <= height <= 16_384,
                'WINDOW_METADATA', 'Invalid capture dimensions')
        camera = channel != 'LIDAR_TOP'
        require((0 < width * height <= 32_000_000 if camera else width == height == 0) and
                row.get('fileformat') == ('jpg' if camera else 'pcd'), 'WINDOW_METADATA', 'Unsupported raw sensor encoding')
        require(path.startswith(('samples/' if row['is_key_frame'] else 'sweeps/') + channel + '/') and
                path.endswith('.jpg' if camera else '.pcd.bin'), 'WINDOW_METADATA', 'Capture path disagrees with channel/format')
        groups[(samples[row['sample_token']], channel)].append({
            'sample_data_token': token, 'sample_token': row['sample_token'], 'capture_timestamp_us': timestamp(row.get('timestamp')),
            'calibrated_sensor_token': cal, 'ego_pose_token': identity(row.get('ego_pose_token')),
            'filename': path, 'is_key_frame': row['is_key_frame'], 'width': width, 'height': height,
            'prev': prev, 'next': following})
    for rows in groups.values():
        rows.sort(key=lambda r: r['capture_timestamp_us'])
        for i, row in enumerate(rows):
            require((i == 0 or rows[i-1]['capture_timestamp_us'] < row['capture_timestamp_us']) and
                    row['prev'] == (rows[i-1]['sample_data_token'] if i else '') and
                    row['next'] == (rows[i+1]['sample_data_token'] if i+1 < len(rows) else ''),
                    'WINDOW_CHAIN', 'Sensor links, scene boundaries or timestamp order disagree')
    return groups


def windows(groups, selected):
    result = []
    for aid, anchor in selected.items():
        lo, hi = anchor['context_window_us']
        require(hi-lo == 2*CONTEXT_US, 'WINDOW_TIME', 'Unexpected context duration')
        channels = {}
        for channel in CHANNELS:
            rows = groups.get((anchor['scene_token'], channel), [])
            keyframes = [r for r in rows if r['is_key_frame'] and r['sample_token'] == anchor['sample_token']]
            expected = anchor.get('keyframe_metadata', {}).get(channel, {})
            if expected.get('metadata_state') == 'present':
                require(len(keyframes) == 1 and all(keyframes[0][k] == expected.get(k) for k in
                        ('sample_data_token', 'capture_timestamp_us', 'filename', 'calibrated_sensor_token', 'ego_pose_token')),
                        'WINDOW_CATALOG', 'Keyframe catalog binding differs')
            else:
                require(expected.get('metadata_state') == 'missing' and not keyframes,
                        'WINDOW_CATALOG', 'Keyframe missingness differs')
            captures = [dict(r) for r in rows if lo <= r['capture_timestamp_us'] <= hi]
            before = next((r for r in reversed(rows) if r['capture_timestamp_us'] <= lo), None)
            after = next((r for r in rows if r['capture_timestamp_us'] >= hi), None)
            def boundary(row):
                return ({'state': 'bracketed', 'sample_data_token': row['sample_data_token'],
                         'capture_timestamp_us': row['capture_timestamp_us']} if row else
                        {'state': 'recorded_stream_endpoint' if rows else 'no_recorded_stream'})
            times = [r['capture_timestamp_us'] for r in captures]
            channels[channel] = {'start_boundary': boundary(before), 'end_boundary': boundary(after),
                'capture_count': len(captures), 'captures': captures,
                'timing': {'capture_span_us': [times[0], times[-1]] if times else None,
                    'max_inter_capture_gap_us': max((b-a for a,b in zip(times,times[1:])), default=None),
                    'start_to_first_capture_us': times[0]-lo if times else None,
                    'last_capture_to_end_us': hi-times[-1] if times else None},
                'continuous_temporal_coverage': 'not_established', 'online_availability_time': 'unmeasured'}
        result.append({'anchor_id': aid, 'sample_token': anchor['sample_token'], 'scene_token': anchor['scene_token'],
                       'anchor_timestamp_us': anchor['anchor_timestamp_us'], 'context_window_us': [lo,hi],
                       'has_declared_scene_context': anchor['has_declared_scene_context'], 'channels': channels})
    return result
