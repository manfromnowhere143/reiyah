"""Restricted metadata disclosure profiles; no pixel or point editing."""
from tools.perception_inputs.source_io import require
from tools.perception_windows.payloads import decode_image, decode_points


def jpeg_profile(data):
    """Inspect the complete marker stream, including markers after scan data.

    This is deliberately narrower than JPEG/JFIF validity. A valid file outside
    this disclosure profile is withheld, never silently stripped or recompressed.
    Entropy-coded pixels remain evidence, not a guarantee against steganography.
    """
    def check(ok):
        require(ok, 'OBS_JPEG_PROFILE', 'JPEG is outside the restricted disclosure profile')

    check(data[:2] == b'\xff\xd8')
    pos, segments, in_scan, scans, frames = 2, 0, False, 0, 0
    while pos < len(data):
        if in_scan:
            # Skip entropy bytes; FF00 is a stuffed value, FFD0..FFD7 restart.
            marker_start = data.find(b'\xff', pos)
            check(marker_start >= 0)
            pos = marker_start
        check(data[pos] == 255)
        while pos < len(data) and data[pos] == 255:
            pos += 1
        check(pos < len(data))
        marker = data[pos]; pos += 1
        if in_scan and (marker == 0 or 0xd0 <= marker <= 0xd7):
            continue
        if in_scan:
            check(marker == 0xd9)  # Single interleaved baseline scan; no post-scan payload.
        in_scan = False
        if marker == 0xd9:
            check(pos == len(data) and scans == 1 and frames == 1)
            return
        check(marker in (0xe0, 0xc0, 0xdb, 0xc4, 0xdd, 0xda))
        check(pos + 2 <= len(data))
        length = int.from_bytes(data[pos:pos+2], 'big')
        check(length >= 2 and pos + length <= len(data))
        payload = data[pos+2:pos+length]; pos += length
        if marker == 0xe0:
            check(segments == 0 and len(payload) == 14 and payload[:5] == b'JFIF\0'
                  and payload[5] == 1 and payload[6] <= 2 and payload[7] <= 2
                  and int.from_bytes(payload[8:10], 'big') > 0
                  and int.from_bytes(payload[10:12], 'big') > 0 and payload[12:] == b'\0\0')
        else:
            check(segments > 0)
        if marker == 0xc0:
            frames += 1
            check(frames == 1 and scans == 0 and len(payload) == 15 and payload[0] == 8 and payload[5] == 3)
        if marker == 0xda:
            scans += 1
            check(scans == 1 and frames == 1 and len(payload) == 10 and payload[0] == 3
                  and payload[-3:] == b'\0\x3f\0')
            in_scan = True
        segments += 1
    check(False)


def camera(data, width, height):
    jpeg_profile(data)
    decode_image(data, width, height)
    return data


def ply_header(count):
    return (f'ply\nformat binary_little_endian 1.0\nelement vertex {count}\n'
            'property float x\nproperty float y\nproperty float z\n'
            'property float intensity\nproperty float ring\nend_header\n').encode('ascii')


def lidar(data):
    count = decode_points(data)['point_count']
    return ply_header(count) + data, count


def verify_ply(data, count):
    require(type(count) is int and 0 < count <= (64 << 20)//20,
            'OBS_PLY_PROFILE', 'Invalid declared point count')
    header = ply_header(count)
    require(data.startswith(header) and len(data) == len(header) + count*20,
            'OBS_PLY_PROFILE', 'PLY header or body length differs from the restricted profile')
    require(decode_points(data[len(header):])['point_count'] == count,
            'OBS_PLY_PROFILE', 'Point record count differs')
