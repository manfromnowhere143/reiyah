import datetime
import unittest

from report_results import interval_union_seconds, physical_download_totals


class CostControls(unittest.TestCase):
    def test_nested_overlapping_and_adjacent_intervals_count_once(self):
        start = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
        intervals = [(start + datetime.timedelta(seconds=a), start + datetime.timedelta(seconds=b))
                     for a, b in [(9, 12), (0, 10), (2, 3), (12, 14), (20, 21), (20, 21)]]
        self.assertEqual(interval_union_seconds(intervals), 15)
        self.assertEqual(interval_union_seconds([]), 0)

    def test_negative_interval_rejected(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        with self.assertRaises(ValueError):
            interval_union_seconds([(now, now - datetime.timedelta(seconds=1))])

    def test_reused_ordinal_is_not_a_free_download(self):
        rows = [{'id': 'duplicate', 'path': path, 'received_bytes': size,
                 'seconds': 2, 'error': None, 'http_status': code}
                for path, size, code in [('a', 7, 200), ('b', 11, 401)]]
        result = physical_download_totals(rows)
        self.assertEqual(result['new_download_bytes'], 18)
        self.assertEqual(result['physical_receipts'], 2)
        self.assertEqual(result['unsuccessful_http_or_transport_receipts'], 1)

    def test_ambiguous_repeated_path_rejected(self):
        row = {'path': 'a', 'received_bytes': 3, 'seconds': 1, 'http_status': 200}
        with self.assertRaises(ValueError):
            physical_download_totals([row, row])


if __name__ == '__main__':
    unittest.main()
