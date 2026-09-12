"""Small adversarial controls, constructed data only; no reviewer or image observation."""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('image_fidelity', Path(__file__).with_name('probe.py'))
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ImageFidelityTests(unittest.TestCase):
    # Hard-coded IEEE-754 encodings for 0 and 255, not the producer's conversion.
    ZERO = b'\x00\x00\x00\x00'
    ONE = b'\x00\x00\x80\x3f'
    # Top: red, green. Bottom: blue, white. Native buffer starts with bottom row.
    NATIVE = (ZERO + ZERO + ONE + ONE + ONE * 4 +
              ONE + ZERO + ZERO + ONE + ZERO + ONE + ZERO + ONE)
    RGB = bytes([255, 0, 0, 0, 255, 0, 0, 0, 255, 255, 255, 255])

    def test_asymmetric_coordinates_and_channels(self):
        self.assertEqual(probe.top_left_rgb(self.NATIVE, 2, 2), self.RGB)
        self.assertEqual(probe.compare_pixels(self.NATIVE, self.RGB, 2, 2), probe.digest(self.RGB))

    def test_wrong_orientation(self):
        with self.assertRaisesRegex(ValueError, '^PIXEL_MISMATCH$'):
            probe.compare_pixels(self.NATIVE[32:] + self.NATIVE[:32], self.RGB, 2, 2)

    def test_swapped_channels(self):
        words = [self.NATIVE[i:i+4] for i in range(0, len(self.NATIVE), 4)]
        for i in range(0, len(words), 4):
            words[i], words[i+2] = words[i+2], words[i]
        with self.assertRaisesRegex(ValueError, '^PIXEL_MISMATCH$'):
            probe.compare_pixels(b''.join(words), self.RGB, 2, 2)

    def test_one_valid_byte_changed(self):
        with self.assertRaisesRegex(ValueError, '^PIXEL_MISMATCH$'):
            probe.compare_pixels(self.ONE + self.NATIVE[4:], self.RGB, 2, 2)

    def test_off_grid_values_are_rejected_without_tolerance(self):
        for bits in (1, 0x80000000, 0x7fc00000, 0x7f800000, 0x3f000000, 0x3f800001):
            with self.subTest(bits=bits), self.assertRaisesRegex(ValueError, '^PIXEL_BYTE_GRID$'):
                probe.top_left_rgb(struct.pack('<I', bits) + self.NATIVE[4:], 2, 2)

    def test_alpha_is_not_discarded_silently(self):
        with self.assertRaisesRegex(ValueError, '^PIXEL_ALPHA$'):
            probe.top_left_rgb(self.NATIVE[:12] + self.ZERO + self.NATIVE[16:], 2, 2)

    def test_truncation_and_extra_pixels(self):
        for data in (self.NATIVE[:-4], self.NATIVE + self.ZERO):
            with self.subTest(size=len(data)), self.assertRaisesRegex(ValueError, '^PIXEL_BUFFER_SIZE$'):
                probe.top_left_rgb(data, 2, 2)

    def test_dimensions_are_bounded(self):
        for shape in ((0, 1), (True, 1), (8193, 1), (2000, 2000)):
            with self.subTest(shape=shape), self.assertRaisesRegex(ValueError, '^PIXEL_DIMENSIONS$'):
                probe.dimensions(*shape)

    def test_encoded_dimensions_before_decode(self):
        # Header-only constructed bytes, not a decodable image or reference record.
        header = bytes.fromhex('ffd8 ffc0 0011 08 0002 0003 03 011100 021100 031100 ffd9')
        probe.check_jpeg_header(header, 3, 2)
        with self.assertRaisesRegex(ValueError, '^PIXEL_ENCODED_DIMENSIONS$'):
            probe.check_jpeg_header(header, 1, 1)

    def test_malformed_header_never_reaches_decode(self):
        for header in (b'', bytes.fromhex('ffd8 ffd9'), bytes.fromhex('ffd8 ffc0 ffff ffd9'),
                       bytes.fromhex('ffd8 ffda 0002 ffd9'), bytes.fromhex('ffd8 ffff ff')):
            with self.subTest(header=header), self.assertRaisesRegex(ValueError, '^PIXEL_JPEG_HEADER$'):
                probe.check_jpeg_header(header, 1, 1)

    def test_different_original_is_not_an_identity_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'asset'; p.write_bytes(b'abc')
            self.assertEqual(probe.bound_read(p, 3, probe.digest(b'abc')), b'abc')
            with self.assertRaisesRegex(ValueError, '^PIXEL_IDENTITY$'):
                probe.bound_read(p, 3, probe.digest(b'abd'))
            with self.assertRaisesRegex(ValueError, '^PIXEL_IDENTITY$'):
                probe.bound_read(p, 2, probe.digest(b'ab'))

    def test_output_identity_cannot_be_reused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'report'; probe.write_new(p, b'first')
            with self.assertRaises(FileExistsError):
                probe.write_new(p, b'second')
            self.assertEqual(p.read_bytes(), b'first')


if __name__ == '__main__':
    unittest.main()
