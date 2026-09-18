"""Small source-join failure controls; no actual development records."""
from copy import deepcopy
import unittest

from timing_metadata import collect_rows


class MetadataTests(unittest.TestCase):
    def fixture(self):
        selected = {'sample': {'s1': {'token': 's1', 'prev': 's0', 'next': '', 'timestamp': 100, 'scene_token': 'scene'}},
                    'category': {'car': {'name': 'vehicle.car'}, 'other': {'name': 'vehicle.bus'}},
                    'instance': {}, 'sample_annotation': {}}
        rows = [('sample_annotation.json', {'token': 'a0', 'sample_token': 's0', 'instance_token': 'i0'}),
                ('instance.json', {'token': 'i0', 'category_token': 'car'}),
                ('instance.json', {'token': 'i1', 'category_token': 'other'}),
                ('sample.json', {'token': 's0', 'prev': '', 'next': 's1', 'timestamp': 0, 'scene_token': 'scene'})]
        return selected, rows

    def test_order_independent_complete_census(self):
        selected, rows = self.fixture()
        first, counts = collect_rows(selected, rows)
        second, _ = collect_rows(selected, list(reversed(rows)))
        self.assertEqual(first, second); self.assertEqual(counts['instance'], 2)
        self.assertEqual(set(first['instance']), {'i0'}); self.assertEqual(set(first['sample_annotation']), {'a0'})

    def test_explicit_empty_is_distinct_from_missing_sample(self):
        selected, rows = self.fixture(); rows[0][1]['instance_token'] = 'i1'
        tables, _ = collect_rows(selected, rows)
        self.assertEqual(tables['sample_annotation'], {})
        with self.assertRaisesRegex(ValueError, 'Incomplete preceding'):
            collect_rows(selected, rows[:-1])

    def test_scene_start_has_no_fabricated_previous_sample(self):
        selected, rows = self.fixture(); selected['sample']['s1']['prev'] = ''
        tables, _ = collect_rows(selected, rows)
        self.assertEqual(tables['sample'], {}); self.assertEqual(tables['sample_annotation'], {})

    def test_duplicate_record_rejected(self):
        selected, rows = self.fixture()
        with self.assertRaisesRegex(ValueError, 'Duplicate retained'):
            collect_rows(selected, rows + [rows[0]])

    def test_duplicate_instance_rejected(self):
        selected, rows = self.fixture(); extra = deepcopy(rows[0]); extra[1]['token'] = 'a1'
        with self.assertRaisesRegex(ValueError, 'Duplicate instance'):
            collect_rows(selected, rows + [extra])

    def test_cross_scene_link_rejected(self):
        selected, rows = self.fixture(); rows[-1][1]['scene_token'] = 'elsewhere'
        with self.assertRaisesRegex(ValueError, 'Inconsistent preceding'):
            collect_rows(selected, rows)

    def test_inverted_or_equal_time_rejected(self):
        for timestamp in (100, 101):
            selected, rows = self.fixture(); rows[-1][1]['timestamp'] = timestamp
            with self.assertRaisesRegex(ValueError, 'Inconsistent preceding'):
                collect_rows(selected, rows)

    def test_nonreciprocal_sample_link_rejected(self):
        selected, rows = self.fixture(); rows[-1][1]['next'] = 's2'
        with self.assertRaisesRegex(ValueError, 'Inconsistent preceding'):
            collect_rows(selected, rows)

    def test_inherited_record_difference_rejected(self):
        selected, rows = self.fixture(); selected['sample_annotation']['a0'] = {'different': True}
        with self.assertRaisesRegex(ValueError, 'Inherited annotation'):
            collect_rows(selected, rows)

    def test_missing_streamed_table_rejected(self):
        selected, rows = self.fixture()
        with self.assertRaisesRegex(ValueError, 'Missing streamed'):
            collect_rows(selected, [row for row in rows if row[0] != 'instance.json'])

    def test_missing_instance_does_not_become_noncar(self):
        selected, rows = self.fixture(); rows[0][1]['instance_token'] = 'absent'
        with self.assertRaisesRegex(ValueError, 'Missing annotation instance'):
            collect_rows(selected, rows)

    def test_unknown_category_does_not_become_noncar(self):
        selected, rows = self.fixture(); rows[1][1]['category_token'] = 'absent'
        with self.assertRaisesRegex(ValueError, 'Unknown instance category'):
            collect_rows(selected, rows)


if __name__ == '__main__':
    unittest.main()
