"""Closed allowlist for the reviewer-facing observation artifact."""
from collections import Counter
import re

from tools.perception_decision.contract import rational
from tools.perception_inputs.sensors import CHANNELS
from tools.perception_inputs.source_io import digest_value, require

MAX_MANIFEST = 128 << 20
MAX_TOTAL = 2 << 30
MAX_CAPTURES = 10_000
PROFILE = 'unassisted_raw_relative_time.0.1.0'
STATES = ('delivered', 'not_listed', 'unavailable', 'missing', 'invalid',
          'sensor_invalid', 'not_checked', 'withheld')
GUIDE = b'''Reiyah raw observation package, profile 0.1.0

This package supports the proposed unassisted object-discovery phase.
Review each recorded camera and lidar capture in each declared window. Record
what you can and cannot observe; an unavailable capture is not an empty scene.
Do not consult annotations, detector outputs or the separate custody record.
No human review has been supplied or certified by this package.

manifest.json lists neutral windows, captures and files. Relative times are
microseconds from the window anchor. All windows cover the closed interval
[-2000000,2000000]. Recording boundaries describe the metadata stream only.
They do not establish uninterrupted physical observation or adequate sampling.

Camera JPEG bytes are unchanged. The restricted file profile allows only a
basic JFIF application header, with no thumbnails, other application headers or
comments. Passing it does not establish anonymization or absence of information
encoded in pixels. Images, file hashes and sensor geometry may identify public
source data. This is a restriction on model/reference hints, not anonymity.

Lidar PLY files contain the unchanged little-endian float32 point records in
their original sensor frame: x,y,z in metres, intensity and ring. There is no
filtering, downsampling, reordering, accumulation or inferred per-point time.
The PLY wrapper adds a fixed format header; it is not a reconstructed surface.

Available 4x4 matrices map column homogeneous coordinates from the capture's
sensor frame into the anchor ego coordinate frame. The spatial transform does
not transport a moving object to the anchor time. Camera intrinsics are nominal;
distortion, physical calibration accuracy, clock accuracy, object motion,
exposure duration and online availability remain unmeasured or unestablished.
Do not treat exact rational coordinates as exact physical measurements.

SEAL.json binds the manifest and this guide. The complete directory must be
checked using its separately retained expected seal digest before use. A seal
proves byte identity, not source correctness, human independence, complete
physical references, study readiness or permission for any safety claim.
'''


def closed(value, fields, code='OBS_SCHEMA'):
    require(type(value) is dict and set(value) == set(fields), code, 'Unexpected or missing fields')


def integer(value, lo, hi, code='OBS_SCHEMA'):
    require(type(value) is int and lo <= value <= hi, code, 'Invalid bounded integer')
    return value


def matrix(value, n):
    require(type(value) is list and len(value) == n and
            all(type(row) is list and len(row) == n for row in value), 'OBS_MATRIX', 'Invalid matrix shape')
    result = []
    for row in value:
        out = []
        for q in row:
            closed(q, ('numerator', 'denominator'), 'OBS_MATRIX')
            require(type(q['numerator']) is str and type(q['denominator']) is str
                    and re.fullmatch(r'-?(0|[1-9][0-9]{0,255})', q['numerator']) is not None
                    and re.fullmatch(r'[1-9][0-9]{0,255}', q['denominator']) is not None,
                    'OBS_MATRIX', 'Invalid bounded rational representation')
            v = rational(q)
            require(abs(v) <= 10**12, 'OBS_MATRIX', 'Matrix operand exceeds format bound')
            out.append(v)
        result.append(out)
    if n == 4:
        r = result
        require(r[3] == [0, 0, 0, 1] and all(
            sum(r[k][i]*r[k][j] for k in range(3)) == int(i == j)
            for i in range(3) for j in range(3)), 'OBS_MATRIX', 'Transform is not rigid')
        det = sum(r[0][i]*(r[1][(i+1)%3]*r[2][(i+2)%3]-r[1][(i+2)%3]*r[2][(i+1)%3]) for i in range(3))
        require(det == 1, 'OBS_MATRIX', 'Transform changes handedness')
    else:
        r = result
        require(r[2] == [0, 0, 1] and r[1][0] == 0 and r[0][0] > 0 and r[1][1] > 0,
                'OBS_MATRIX', 'Invalid camera intrinsic form')
    return result


def transform(value):
    require(type(value) is dict and value.get('state') in ('available', 'unavailable'),
            'OBS_SCHEMA', 'Invalid transform state')
    closed(value, ('state', 'matrix') if value['state'] == 'available' else ('state',))
    if value['state'] == 'available':
        matrix(value['matrix'], 4)


def intrinsic(value, channel):
    require(type(value) is dict and type(value.get('state')) is str, 'OBS_SCHEMA', 'Invalid intrinsic state')
    state = value['state']
    allowed = ('not_applicable',) if channel == 'LIDAR_TOP' else ('available', 'missing', 'invalid')
    require(state in allowed, 'OBS_SCHEMA', 'Intrinsic state differs from channel type')
    closed(value, ('state', 'matrix') if state == 'available' else ('state',))
    if state == 'available':
        matrix(value['matrix'], 3)


def identity(value, expected_name, limit):
    closed(value, ('filename', 'byte_size', 'sha256'))
    require(value['filename'] == expected_name and digest_value(value['sha256']),
            'OBS_SCHEMA', 'Unexpected file name or digest')
    integer(value['byte_size'], 1, limit)


def validate(value):
    closed(value, ('artifact_id', 'version', 'profile', 'package_id', 'phase', 'captures', 'windows'))
    require(value['artifact_id'] == 'reiyah.perception-observation.package' and value['version'] == '0.1.0'
            and value['profile'] == PROFILE and value['phase'] == 'unassisted_discovery'
            and type(value['package_id']) is str and re.fullmatch('[0-9a-f]{32}', value['package_id']) is not None,
            'OBS_SCHEMA', 'Unsupported package identity or disclosure profile')
    rows = value['captures']
    require(type(rows) is list and 0 < len(rows) <= MAX_CAPTURES, 'OBS_SCHEMA', 'Invalid capture population')
    captures, total = {}, 0
    for i, r in enumerate(rows, 1):
        closed(r, ('id', 'channel', 'image_shape', 'intrinsic', 'evidence'))
        cid = f'capture-{i:06d}'
        require(r['id'] == cid and type(r['channel']) is str and r['channel'] in CHANNELS,
                'OBS_SCHEMA', 'Noncanonical capture ID or unknown sensor orientation')
        channel = r['channel']; shape = r['image_shape']
        if channel == 'LIDAR_TOP':
            require(shape is None, 'OBS_SCHEMA', 'Lidar cannot carry image dimensions')
        else:
            require(type(shape) is list and len(shape) == 2, 'OBS_SCHEMA', 'Missing image dimensions')
            for side in shape:
                integer(side, 1, 8192)
            require(shape[0]*shape[1] <= 32_000_000, 'OBS_SCHEMA', 'Image exceeds pixel limit')
        intrinsic(r['intrinsic'], channel)
        e = r['evidence']
        require(type(e) is dict and type(e.get('state')) is str and e['state'] in STATES,
                'OBS_SCHEMA', 'Unknown evidence state')
        if e['state'] == 'delivered':
            is_lidar = channel == 'LIDAR_TOP'
            closed(e, ('state', 'asset', 'point_count') if is_lidar else ('state', 'asset'))
            identity(e['asset'], f'assets/{cid}.'+('ply' if is_lidar else 'jpg'), (64 << 20)+1024)
            if is_lidar:
                integer(e['point_count'], 1, (64 << 20)//20)
            total += e['asset']['byte_size']
        else:
            closed(e, ('state',))
        captures[cid] = r
    require(total <= MAX_TOTAL, 'OBS_LIMIT', 'Total evidence exceeds package limit')
    windows = value['windows']
    require(type(windows) is list and 0 < len(windows) <= 128, 'OBS_SCHEMA', 'Invalid window population')
    seen = set(); occurrences = 0
    for i, w in enumerate(windows, 1):
        closed(w, ('id', 'interval_us', 'channels'))
        require(w['id'] == f'window-{i:04d}' and type(w['interval_us']) is list
                and len(w['interval_us']) == 2 and all(type(x) is int for x in w['interval_us'])
                and w['interval_us'] == [-2_000_000, 2_000_000], 'OBS_SCHEMA', 'Invalid window ID or interval')
        closed(w['channels'], CHANNELS)
        window_seen = set()
        for channel, g in w['channels'].items():
            closed(g, ('recording_boundary', 'captures'))
            closed(g['recording_boundary'], ('start', 'end'))
            require(all(type(s) is str and s in ('bracketed', 'recorded_stream_endpoint', 'no_recorded_stream')
                        for s in g['recording_boundary'].values()), 'OBS_SCHEMA', 'Invalid recording boundary')
            require(type(g['captures']) is list and len(g['captures']) <= MAX_CAPTURES,
                    'OBS_SCHEMA', 'Invalid channel population')
            last = -2_000_001
            for r in g['captures']:
                closed(r, ('capture_id', 'time_offset_us', 'sensor_to_anchor_ego'))
                cid = r['capture_id']
                require(type(cid) is str and cid in captures and cid not in window_seen
                        and captures[cid]['channel'] == channel, 'OBS_SCHEMA', 'Duplicate or misjoined capture')
                dt = integer(r['time_offset_us'], -2_000_000, 2_000_000)
                require(dt > last, 'OBS_SCHEMA', 'Channel captures are not strictly chronological')
                last = dt
                transform(r['sensor_to_anchor_ego'])
                seen.add(cid); window_seen.add(cid); occurrences += 1
                require(occurrences <= 50_000, 'OBS_LIMIT', 'Too many window occurrences')
    require(seen == set(captures), 'OBS_SCHEMA', 'Unreferenced evidence or empty opportunity population')
    return {'windows': len(windows), 'distinct_captures': len(captures), 'capture_occurrences': occurrences,
            'evidence_states': dict(sorted(Counter(r['evidence']['state'] for r in rows).items())),
            'delivered_bytes': total, 'human_review': 'not_established', 'physical_reference_coverage': 'not_established'}
