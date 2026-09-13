"""The viewer's selection and discovery's evidence locator have distinct bounds."""
import struct
import unittest

from tools import perception_viewer as viewer
from tools.perception_decision.contract import Invalid
from tools.perception_discovery import records


class SelectionEvidenceTests(unittest.TestCase):
    def test_large_valid_selection_is_preserved_then_refused_without_truncation(self):
        # Synthetic byte records only. No scene, inspection or human is implied.
        count = 5000
        body = b''.join(struct.pack('<5f', i, 0, 0, 1, 0) for i in range(count))
        rows = [(i, *row) for i, row in enumerate(struct.iter_unpack('<5f', body))]
        capture = {'channel': 'LIDAR_TOP', 'evidence': {'state': 'delivered', 'point_count': count}}
        for size in (4096, 4097):
            with self.subTest(selected_points=size):
                selected = list(range(size))
                # Current native extraction uses this all-record check and keeps
                # the complete returned selection. It has no locator-sized cap.
                checked = viewer.verify_rows(body, rows, selected, viewer.IDENTITY)
                self.assertEqual(checked, selected)
                locator = {'kind': 'point_indices', 'indices': checked}
                if size == 4096:
                    records.locator(locator, capture)
                else:
                    with self.assertRaises(Invalid) as caught:
                        records.locator(locator, capture)
                    self.assertEqual(caught.exception.code, 'DISCOVERY_LOCATOR')
                self.assertEqual(locator['indices'], selected)
                self.assertEqual(len(locator['indices']), size)


if __name__ == '__main__':
    unittest.main()
