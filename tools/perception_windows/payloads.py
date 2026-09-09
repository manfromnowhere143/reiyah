"""Identity verification and full decoding on the same bounded raw bytes."""
from array import array
from contextlib import ExitStack, contextmanager
import hashlib
import io
import math
import os
import stat
import sys

from tools.perception_decision.contract import Invalid
from tools.perception_inputs.source_io import digest_value, require
from .timeline import relative_path

MAX_ASSET_BYTES = 64 << 20


def inventory(value):
    require(type(value) is dict and set(value) == {'artifact_id', 'version', 'assets'} and
            value['artifact_id'] == 'reiyah.perception-windows.assets' and value['version'] == '0.1.0',
            'WINDOW_INVENTORY', 'Unsupported asset inventory')
    rows = value['assets']
    require(type(rows) is list and len(rows) <= 200_000, 'WINDOW_INVENTORY', 'Invalid asset inventory size')
    result = {}
    for row in rows:
        require(type(row) is dict, 'WINDOW_INVENTORY', 'Malformed asset record')
        name = relative_path(row.get('filename'))
        require(name not in result, 'WINDOW_INVENTORY', 'Repeated asset path')
        if row.get('state') == 'retained':
            require(set(row) == {'filename', 'state', 'byte_size', 'sha256'} and
                    type(row['byte_size']) is int and 0 <= row['byte_size'] <= MAX_ASSET_BYTES and digest_value(row['sha256']),
                    'WINDOW_INVENTORY', 'Invalid retained asset identity')
        else:
            require(set(row) == {'filename', 'state', 'reason'} and row['state'] == 'unavailable' and
                    type(row['reason']) is str and 0 < len(row['reason']) <= 512,
                    'WINDOW_INVENTORY', 'Unknown custody is not an empty sensor output')
        result[name] = row
    return result


@contextmanager
def asset_file(root_fd, filename):
    """Open through directory descriptors; reject symlinks at every relative step."""
    parts = relative_path(filename).split('/')
    with ExitStack() as stack:
        directory = root_fd
        for part in parts[:-1]:
            directory = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            stack.callback(os.close, directory)
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW, dir_fd=directory)
        stream = stack.enter_context(os.fdopen(fd, 'rb'))
        require(stat.S_ISREG(os.fstat(fd).st_mode), 'WINDOW_ASSET_TYPE', 'Raw asset is not a regular file')
        yield stream


def raw_bytes(root_fd, spec):
    with asset_file(root_fd, spec['filename']) as stream:
        data = stream.read(spec['byte_size'] + 1)
    require(len(data) == spec['byte_size'], 'WINDOW_ASSET_SIZE', 'Raw asset length differs from retained identity')
    require(hashlib.sha256(data).hexdigest() == spec['sha256'], 'WINDOW_ASSET_DIGEST', 'Raw asset digest differs')
    return data


def decode_points(data):
    require(bool(data) and len(data) % 20 == 0, 'WINDOW_LIDAR_LAYOUT', 'Require nonempty five-float point records')
    values = array('f')
    require(values.itemsize == 4, 'WINDOW_RUNTIME', 'This runtime does not provide four-byte floats')
    values.frombytes(data)
    if sys.byteorder != 'little':
        values.byteswap()
    require(all(math.isfinite(v) for v in values), 'WINDOW_LIDAR_NONFINITE', 'Nonfinite raw point field')
    return {'point_count': len(values)//5, 'encoding': 'little_endian_float32_x_y_z_intensity_ring',
            'per_point_acquisition_time': 'unavailable', 'physical_point_validity': 'not_established'}


def decode_image(data, width, height):
    try:
        from PIL import Image, ImageFile
    except ImportError as exc:
        raise Invalid('WINDOW_DECODER_UNAVAILABLE', 'Pillow JPEG decoder is unavailable') from exc
    require(not ImageFile.LOAD_TRUNCATED_IMAGES, 'WINDOW_DECODER_CONFIGURATION', 'Truncated-image tolerance must be disabled')
    require(data.startswith(b'\xff\xd8') and data.endswith(b'\xff\xd9'), 'WINDOW_JPEG_ENVELOPE', 'Incomplete JPEG envelope')
    try:
        with Image.open(io.BytesIO(data), formats=['JPEG']) as image:
            require(image.format == 'JPEG' and image.size == (width, height) and image.mode == 'RGB',
                    'WINDOW_IMAGE_SHAPE', 'Decoded format, dimensions or color mode differ from metadata')
            image.load()  # Header inspection/verify alone does not force all pixels to decode.
    except (OSError, SyntaxError, ValueError, Image.DecompressionBombError) as exc:
        if isinstance(exc, Invalid):
            raise
        raise Invalid('WINDOW_IMAGE_DECODE', 'JPEG decoder rejected the bound bytes') from exc
    return {'width': width, 'height': height, 'mode': 'RGB', 'full_pixel_decode': True,
            'physical_visibility': 'not_established'}


def inspect(root_fd, record, assets, channel):
    spec = assets.get(record['filename'])
    if spec is None:
        return {'custody_state': 'not_listed', 'payload_state': 'not_checked', 'diagnostic': 'No retained identity for this required capture'}
    if spec['state'] == 'unavailable':
        return {'custody_state': 'unavailable', 'payload_state': 'not_checked', 'diagnostic': spec['reason']}
    bound = {'expected_sha256': spec['sha256'], 'expected_byte_size': spec['byte_size']}
    try:
        data = raw_bytes(root_fd, spec)
    except FileNotFoundError:
        return {**bound, 'custody_state': 'missing', 'payload_state': 'not_checked', 'diagnostic': 'Retained path is absent'}
    except (Invalid, OSError) as exc:
        return {**bound, 'custody_state': 'invalid', 'payload_state': 'not_checked',
                'diagnostic': exc.code if isinstance(exc, Invalid) else 'WINDOW_ASSET_IO'}
    try:
        decoded = decode_points(data) if channel == 'LIDAR_TOP' else decode_image(data, record['width'], record['height'])
    except Invalid as exc:
        unavailable = exc.code in ('WINDOW_DECODER_UNAVAILABLE', 'WINDOW_DECODER_CONFIGURATION', 'WINDOW_RUNTIME')
        return {**bound, 'custody_state': 'verified', 'payload_state': 'not_checked' if unavailable else 'sensor_invalid',
                'diagnostic': exc.code}
    return {**bound, 'custody_state': 'verified', 'payload_state': 'decoded', 'decoded': decoded}
