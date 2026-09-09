"""Explicit keyframe metadata and nominal ego-position joins; no raw payload claim."""
from contextlib import ExitStack
from pathlib import PurePosixPath
import tarfile
import tempfile

from tools.perception_decision.contract import Invalid, wire
from tools.perception_decision.nuscenes import _number
from .clock import identity, timestamp
from .source_io import JSONStream, require

CHANNELS = ('LIDAR_TOP', 'CAM_FRONT', 'CAM_FRONT_LEFT', 'CAM_FRONT_RIGHT',
            'CAM_BACK', 'CAM_BACK_LEFT', 'CAM_BACK_RIGHT')
TABLES = ('sensor.json', 'calibrated_sensor.json', 'sample_data.json', 'ego_pose.json')


def _table_streams(stream, stack, tables=TABLES):
    """Copy selected tables to unlinked descriptors to resolve forward references."""
    files, seen, expanded = {}, set(), 0
    try:
        with tarfile.open(fileobj=stream, mode='r|gz') as archive:
            for member in archive:
                path = PurePosixPath(member.name)
                require(not path.is_absolute() and '..' not in path.parts and '\\' not in member.name and
                        member.name not in seen and (member.isfile() or member.isdir()) and len(seen) < 10000,
                        'METADATA_ARCHIVE', 'Unsafe, duplicate or unsupported archive member')
                seen.add(member.name)
                expanded += member.size
                require(0 <= member.size and expanded <= 4 << 30, 'METADATA_SIZE', 'Expanded metadata exceeds its limit')
                if path.name not in tables:
                    continue
                require(member.name == 'v1.0-trainval/' + path.name and member.isfile() and path.name not in files,
                        'METADATA_ARCHIVE', 'Ambiguous sensor table identity')
                output = stack.enter_context(tempfile.TemporaryFile(mode='w+b'))
                source = archive.extractfile(member)
                require(source is not None, 'METADATA_ARCHIVE', 'Missing sensor table bytes')
                copied = 0
                while chunk := source.read(1 << 20):
                    copied += len(chunk)
                    require(copied <= member.size, 'METADATA_SIZE', 'Sensor table exceeds its declared size')
                    output.write(chunk)
                require(copied == member.size, 'METADATA_SIZE', 'Truncated sensor table')
                output.seek(0)
                files[path.name] = output
    except (tarfile.TarError, EOFError) as exc:
        raise Invalid('METADATA_ARCHIVE', 'Malformed sensor metadata archive') from exc
    require(set(files) == set(tables), 'METADATA_TABLE', 'Required sensor table is absent')
    return files


def _rows(stream, limit):
    reader = JSONStream(stream)
    yield from reader.objects(limit)
    reader.finish()


def join(files, anchors):
    sensors, calibrated = {}, {}
    for row in _rows(files['sensor.json'], 10000):
        require(type(row.get('channel')) is str and type(row.get('modality')) is str,
                'SENSOR_METADATA', 'Sensor channel and modality are required')
        token = identity(row.get('token'))
        require(token not in sensors, 'SENSOR_METADATA', 'Duplicate sensor identity')
        if row['channel'] in CHANNELS:
            require(row['modality'] == ('lidar' if row['channel'] == 'LIDAR_TOP' else 'camera'),
                    'SENSOR_METADATA', 'Requested channel has an inconsistent modality')
        sensors[token] = row['channel']
    for row in _rows(files['calibrated_sensor.json'], 50000):
        token, sensor = identity(row.get('token')), identity(row.get('sensor_token'))
        require(token not in calibrated and sensor in sensors, 'SENSOR_METADATA', 'Duplicate or unresolved calibration identity')
        calibrated[token] = sensor
    by_sample = {a['sample_token']: {} for a in anchors}
    used_tokens, wanted_poses = set(), set()
    for row in _rows(files['sample_data.json'], 5_000_000):
        require(type(row.get('is_key_frame')) is bool, 'SENSOR_METADATA', 'Keyframe state must be Boolean')
        if not row['is_key_frame']:
            continue
        sample = identity(row.get('sample_token'))
        if sample not in by_sample:
            continue
        token, cal = identity(row.get('token')), identity(row.get('calibrated_sensor_token'))
        require(cal in calibrated, 'SENSOR_METADATA', 'Unresolved requested-frame calibration')
        channel = sensors[calibrated[cal]]
        if channel not in CHANNELS:
            continue
        pose = identity(row.get('ego_pose_token'))
        file = row.get('filename')
        require(type(file) is str and 0 < len(file) <= 1024 and '\\' not in file and '\0' not in file and
                not PurePosixPath(file).is_absolute() and '..' not in PurePosixPath(file).parts,
                'SENSOR_METADATA', 'Invalid relative sensor payload path')
        require(token not in used_tokens and channel not in by_sample[row['sample_token']],
                'SENSOR_METADATA', 'Repeated sample/channel or sample-data identity')
        used_tokens.add(token)
        record = {'metadata_state': 'present', 'sample_data_token': token, 'calibrated_sensor_token': cal,
                  'ego_pose_token': pose, 'capture_timestamp_us': timestamp(row.get('timestamp')), 'filename': file,
                  'payload_validity': 'not_checked', 'online_availability_time': 'unmeasured'}
        by_sample[row['sample_token']][channel] = record
        if channel == 'LIDAR_TOP':
            wanted_poses.add(pose)
    poses = {}
    for row in _rows(files['ego_pose.json'], 5_000_000):
        token = identity(row.get('token'))
        if token not in wanted_poses:
            continue
        require(token not in poses, 'SENSOR_METADATA', 'Duplicate requested ego-pose identity')
        xyz = row.get('translation')
        require(type(xyz) is list and len(xyz) == 3, 'SENSOR_METADATA', 'Requested ego pose has no XYZ translation')
        poses[token] = {'timestamp_us': timestamp(row.get('timestamp')), 'xy': [wire(_number(v)) for v in xyz[:2]]}
    for anchor in anchors:
        channels = {}
        for channel in CHANNELS:
            value = by_sample[anchor['sample_token']].get(channel)
            if value is None:
                value = {'metadata_state': 'missing', 'capture_delta_us': None,
                         'payload_validity': 'not_checked', 'online_availability_time': 'unmeasured'}
            else:
                value['capture_delta_us'] = value['capture_timestamp_us'] - anchor['anchor_timestamp_us']
            channels[channel] = value
        lidar = channels['LIDAR_TOP']
        pose = poses.get(lidar.get('ego_pose_token'))
        if lidar['metadata_state'] == 'missing' or pose is None:
            ego = {'state': 'missing', 'reason': 'LIDAR_TOP keyframe or referenced ego pose is absent'}
        elif not (pose['timestamp_us'] == lidar['capture_timestamp_us'] == anchor['anchor_timestamp_us']):
            ego = {'state': 'unknown', 'reason': 'Pose, lidar capture and anchor timestamps differ; no interpolation policy',
                   'pose_timestamp_us': pose['timestamp_us'], 'lidar_timestamp_us': lidar['capture_timestamp_us']}
        else:
            ego = {'state': 'observed', 'value': pose['xy'], 'ego_pose_token': lidar['ego_pose_token'],
                   'timestamp_us': pose['timestamp_us'], 'interpretation': 'nominal_metadata_pose_not_physical_accuracy'}
        anchor['keyframe_metadata'], anchor['nominal_ego_xy'] = channels, ego
    return {'required_channels': list(CHANNELS), 'requested_pose_count': len(wanted_poses), 'resolved_pose_count': len(poses),
            'anchor_ego_states': {state: sum(a['nominal_ego_xy']['state'] == state for a in anchors)
                                  for state in ('observed', 'missing', 'unknown')},
            'missing_keyframe_metadata': {c: sum(a['keyframe_metadata'][c]['metadata_state'] == 'missing' for a in anchors) for c in CHANNELS},
            'scope': 'requested_validation_keyframes_and_lidar_poses_only', 'sensor_payload_validity': 'not_checked'}


def enrich(stream, anchors):
    with ExitStack() as stack:
        return join(_table_streams(stream, stack), anchors)
