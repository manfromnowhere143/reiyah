"""Synthetic numeric controls for the separately implemented export check."""
import unittest
import numpy as np
from decode_check import compare, decode


def raw_head(entries):
    result = np.zeros((1, 84, len(entries)), dtype=np.float32)
    for i, (center, score, category) in enumerate(entries):
        result[0, :4, i] = center
        result[0, 4 + category, i] = score
    return result


class DecodeTests(unittest.TestCase):
    def test_same_class_nms_and_different_class_survival(self):
        raw = raw_head([([320, 320, 100, 80], 0.9, 2),
                        ([320, 320, 100, 80], 0.8, 2),
                        ([320, 320, 100, 80], 0.7, 0)])
        result = decode(raw, end_to_end=False, width=640, height=640)
        self.assertEqual(result.shape, (2, 6))
        np.testing.assert_array_equal(result[:, 5], [2, 0])
        np.testing.assert_array_equal(result[:, :4], [[270, 280, 370, 360], [270, 280, 370, 360]])

    def test_threshold_equality_is_excluded(self):
        raw = raw_head([([10, 10, 5, 5], 0.25, 2)])
        self.assertEqual(decode(raw, end_to_end=False, width=640, height=640).shape, (0, 6))
        raw = np.array([[[0, 0, 10, 10, 0.25, 2]]], dtype=np.float32)
        self.assertEqual(decode(raw, end_to_end=True, width=640, height=640).shape, (0, 6))

    def test_inverse_letterbox_and_clipping(self):
        raw = np.array([[[0, 140, 640, 500, 0.5, 2],
                         [-10, 130, 650, 510, 0.4, 2]]], dtype=np.float32)
        result = decode(raw, end_to_end=True, width=1600, height=900)
        np.testing.assert_array_equal(result[:, :4], [[0, 0, 1600, 900], [0, 0, 1600, 900]])
        self.assertEqual(len(result), 2)  # No invented NMS on an end-to-end head.

    def test_maximum_truncates_after_confidence_filter(self):
        raw = np.array([[[0, 0, 10, 10, 0.1, 2], [1, 1, 11, 11, 0.7, 2],
                         [2, 2, 12, 12, 0.8, 2]]], dtype=np.float32)
        result = decode(raw, end_to_end=True, width=640, height=640, maximum=1)
        self.assertEqual(len(result), 1)
        self.assertEqual(float(result[0, 0]), 1.0)  # Preserve publisher end-to-end order.

    def test_comparison_rejects_omissions_and_class_or_order_changes(self):
        rows = np.array([[0, 0, 10, 10, 0.8, 2], [20, 20, 30, 30, 0.7, 0]], dtype=np.float32)
        self.assertEqual(compare(rows, rows)['detections'], 2)
        for changed in (rows[:1], rows[::-1]):
            with self.assertRaises(ValueError):
                compare(rows, changed)
        changed = rows.copy(); changed[0, 5] = 0
        with self.assertRaises(ValueError):
            compare(rows, changed)

    def test_shapes_and_nonfinite_raw_values_fail(self):
        for raw in (np.zeros((2, 84, 1), dtype=np.float32), np.full((1, 84, 1), np.nan, dtype=np.float32)):
            with self.assertRaises(ValueError):
                decode(raw, end_to_end=False, width=640, height=640)


if __name__ == '__main__':
    unittest.main()
