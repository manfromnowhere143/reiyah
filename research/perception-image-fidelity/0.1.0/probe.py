"""Bounded offline JPEG/buffer conformance probe, not an image viewer or review record."""
import argparse
from array import array
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import sys

VERSION = '0.1.0'
BUILD = 'ec6e62d40fa9'
MAX_PIXELS = 2_000_000
MAX_JPEG_BYTES = 32 << 20


def require(condition, code):
    if not condition:
        raise ValueError(code)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def dimensions(width, height):
    require(type(width) is int and type(height) is int and
            1 <= width <= 8192 and 1 <= height <= 8192 and
            width * height <= MAX_PIXELS, 'PIXEL_DIMENSIONS')


def bound_read(path, size, sha256):
    require(type(size) is int and 0 < size <= MAX_JPEG_BYTES,
            'PIXEL_INPUT_SIZE')
    require(type(sha256) is str and re.fullmatch('[0-9a-f]{64}', sha256),
            'PIXEL_INPUT_DIGEST')
    with Path(path).open('rb') as stream:
        data = stream.read(size + 1)
    require(len(data) == size and digest(data) == sha256, 'PIXEL_IDENTITY')
    return data


def write_new(path, data):
    with Path(path).open('xb') as stream:
        stream.write(data)


def encode(report):
    return (json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def check_jpeg_header(data, width, height):
    # Inspect the baseline header before either decoder allocates pixels. This is
    # not full JPEG/profile validation; that remains required in the comparator.
    require(data.startswith(b'\xff\xd8') and data.endswith(b'\xff\xd9'), 'PIXEL_JPEG_HEADER')
    pos = 2
    while pos < len(data) - 2:
        require(data[pos] == 255, 'PIXEL_JPEG_HEADER')
        while pos < len(data) and data[pos] == 255:
            pos += 1
        require(pos + 3 <= len(data), 'PIXEL_JPEG_HEADER')
        marker = data[pos]
        pos += 1
        length = int.from_bytes(data[pos:pos + 2], 'big')
        require(length >= 2 and pos + length <= len(data), 'PIXEL_JPEG_HEADER')
        if marker == 0xc0:
            require(length == 17 and data[pos + 2] == 8 and data[pos + 7] == 3,
                    'PIXEL_JPEG_HEADER')
            require(int.from_bytes(data[pos + 3:pos + 5], 'big') == height and
                    int.from_bytes(data[pos + 5:pos + 7], 'big') == width,
                    'PIXEL_ENCODED_DIMENSIONS')
            return
        require(marker in (0xe0, 0xdb, 0xc4, 0xdd), 'PIXEL_JPEG_HEADER')
        pos += length
    raise ValueError('PIXEL_JPEG_HEADER')


def top_left_rgb(native, width, height):
    """Invert the pinned RNA byte-buffer conversion exactly; never round arbitrary floats."""
    dimensions(width, height)
    require(len(native) == width * height * 16, 'PIXEL_BUFFER_SIZE')
    inv255 = struct.unpack('<f', struct.pack('<f', 1 / 255))[0]
    # Keys are binary32 bits, so negative zero, NaN and off-grid values fail too.
    lookup = {struct.unpack('<I', struct.pack('<f', i * inv255))[0]: i
              for i in range(256)}
    words = array('I')
    require(words.itemsize == 4, 'PIXEL_RUNTIME')
    words.frombytes(native)
    if sys.byteorder != 'little':
        words.byteswap()
    try:
        rgba = bytes(lookup[word] for word in words)
    except KeyError as exc:
        raise ValueError('PIXEL_BYTE_GRID') from exc
    require(rgba[3::4] == b'\xff' * (width * height), 'PIXEL_ALPHA')
    rgb = bytearray(width * height * 3)
    for channel in range(3):
        rgb[channel::3] = rgba[channel::4]
    stride = width * 3
    return b''.join(rgb[y * stride:(y + 1) * stride]
                    for y in range(height - 1, -1, -1))


def compare_pixels(native, baseline, width, height):
    actual = top_left_rgb(native, width, height)
    require(len(baseline) == width * height * 3, 'PIXEL_BASELINE_SIZE')
    require(actual == baseline, 'PIXEL_MISMATCH')
    return digest(actual)


def native_probe(args):
    import bpy

    dimensions(args.width, args.height)
    require(bpy.app.background and bpy.app.version == (5, 1, 2) and
            bpy.app.build_hash.decode() == BUILD and
            not bpy.context.preferences.filepaths.use_scripts_auto_execute,
            'PIXEL_BLENDER_RUNTIME')
    source = bound_read(args.asset, args.byte_size, args.sha256)
    check_jpeg_header(source, args.width, args.height)
    output = Path(args.output)
    output.mkdir()  # A failed or completed attempt always keeps its own identity.
    snapshot = output / 'source.jpg'
    write_new(snapshot, source)
    image = bpy.data.images.load(str(snapshot.resolve()), check_existing=False)
    require(list(image.size) == [args.width, args.height] and image.channels == 4 and
            not image.is_float and image.source == 'FILE' and image.file_format == 'JPEG' and
            image.colorspace_settings.name == 'sRGB' and not image.use_view_as_render,
            'PIXEL_NATIVE_FORMAT')
    pixels = array('f', [0]) * (args.width * args.height * 4)
    require(pixels.itemsize == 4, 'PIXEL_RUNTIME')
    image.pixels.foreach_get(pixels)
    if sys.byteorder != 'little':
        pixels.byteswap()
    buffer = pixels.tobytes()
    top_left_rgb(buffer, args.width, args.height)  # Fail before issuing a success report.
    write_new(output / 'pixels.rgba-f32le', buffer)
    require(snapshot.read_bytes() == source, 'PIXEL_SNAPSHOT_CHANGED')
    bound_read(args.asset, args.byte_size, args.sha256)
    report = {'artifact_id': 'reiyah.image-fidelity.native', 'version': VERSION,
              'asset': {'byte_size': len(source), 'sha256': digest(source)},
              'dimensions': [args.width, args.height],
              'buffer': {'byte_size': len(buffer), 'sha256': digest(buffer)},
              'format': 'RGBA binary32 little-endian; native bottom row first; opaque byte image',
              'blender': {'version': bpy.app.version_string, 'build_hash': BUILD,
                          'input_colorspace': image.colorspace_settings.name,
                          'use_view_as_render': image.use_view_as_render},
              'scope': 'background buffer only; display and human review not observed'}
    write_new(output / 'report.json', encode(report))


def compare_probe(args):
    from PIL import Image, ImageFile, features, __version__ as pillow_version

    dimensions(args.width, args.height)
    require(pillow_version == '12.3.0' and not ImageFile.LOAD_TRUNCATED_IMAGES,
            'PIXEL_PILLOW_RUNTIME')
    source = bound_read(args.asset, args.byte_size, args.sha256)
    original = bound_read(args.original, args.byte_size, args.sha256)
    require(source == original, 'PIXEL_ORIGINAL')
    check_jpeg_header(source, args.width, args.height)
    # This dependency remains in the conventional Python environment, not Blender.
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from tools.perception_observation.formats import jpeg_profile
    jpeg_profile(source)
    with Image.open(io.BytesIO(original), formats=['JPEG']) as image:
        require(image.mode == 'RGB' and image.size == (args.width, args.height),
                'PIXEL_PILLOW_FORMAT')
        image.load()  # No draft scaling, EXIF transpose, ICC transform or recompression.
        baseline = image.tobytes()
    folder = Path(args.native)
    report_bytes = bound_read(folder / 'report.json', args.report_bytes, args.report_sha256)
    report = json.loads(report_bytes)
    require(report.get('artifact_id') == 'reiyah.image-fidelity.native' and
            report.get('version') == VERSION and
            report.get('dimensions') == [args.width, args.height] and
            report.get('asset') == {'byte_size': args.byte_size, 'sha256': args.sha256} and
            report.get('blender') == {'version': '5.1.2', 'build_hash': BUILD,
                                     'input_colorspace': 'sRGB', 'use_view_as_render': False},
            'PIXEL_NATIVE_BINDING')
    bound_read(folder / 'source.jpg', args.byte_size, args.sha256)
    buffer = bound_read(folder / 'pixels.rgba-f32le', args.width * args.height * 16,
                        report['buffer']['sha256'])
    require(report['buffer']['byte_size'] == len(buffer), 'PIXEL_NATIVE_BINDING')
    rgb_sha256 = compare_pixels(buffer, baseline, args.width, args.height)
    result = {'artifact_id': 'reiyah.image-fidelity.comparison', 'version': VERSION,
              'asset': report['asset'], 'native_report_sha256': digest(report_bytes),
              'dimensions': report['dimensions'], 'rgb_samples': len(baseline),
              'rgb_sha256': rgb_sha256, 'mismatched_samples': 0,
              'coordinate_rule': 'zero-based top-left (x,y): pixel index y*width+x; native RGBA offset 16*((height-1-y)*width+x)',
              'coordinate_limit': 'decoded raster index, not a byte offset in compressed JPEG',
              'baseline': {'pillow': pillow_version, 'libjpeg': features.version_codec('jpg'),
                           'libjpeg_turbo': features.version_feature('libjpeg_turbo')},
              'interactive_display': 'not_observed', 'human_review': 'not_performed',
              'physical_truth': 'not_established'}
    bound_read(args.asset, args.byte_size, args.sha256)
    bound_read(args.original, args.byte_size, args.sha256)
    write_new(args.output, encode(result))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['native', 'compare'])
    parser.add_argument('--asset', required=True)
    parser.add_argument('--byte-size', type=int, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--width', type=int, required=True)
    parser.add_argument('--height', type=int, required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--original')
    parser.add_argument('--native')
    parser.add_argument('--report-bytes', type=int)
    parser.add_argument('--report-sha256')
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    args = parser.parse_args(argv)
    if args.mode == 'compare':
        require(all(v is not None for v in (args.original, args.native, args.report_bytes,
                                           args.report_sha256)), 'PIXEL_COMPARE_ARGUMENTS')
        compare_probe(args)
    else:
        native_probe(args)


if __name__ == '__main__':
    main()
