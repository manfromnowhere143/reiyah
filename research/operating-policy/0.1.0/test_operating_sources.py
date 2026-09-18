"""Score custody, exact boundaries and duplicate-occurrence controls."""
from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import tempfile
import unittest

from operating_sources import (FLOOR, ROLES, admit, cells, file_binding, filtered_image,
                               filtered_operand, q, source_packets)
from operating_certificate import expected_cells, expected_filter
from test_admission import fixture


def toy_sources(root, change=None):
    allocation, configuration, packet = fixture()
    if change: change(allocation, configuration, packet)
    bindings = []
    for stage in ('export-06-64', 'export-07-64'):
        folder = root/'results'/stage; folder.mkdir(parents=True)
        values = {'ALLOCATION': allocation, 'CONFIGURATION': configuration, 'PACKET': packet,
                  'RESULT': {'admission': admit(allocation, configuration, packet)}}
        for key, value in values.items():
            path = folder/(key+'.json'); path.write_text(json.dumps(value)); bindings.append(file_binding(path))
    custody = root/'private/comparison-01/custody'; custody.mkdir(parents=True)
    (custody/'SOURCE_BINDINGS.json').write_text(json.dumps(bindings))
    images = []
    for index, row in enumerate(packet['images']):
        operand, _ = filtered_operand(row, FLOOR)
        images.append({key: row[key] for key in ('id', 'width', 'height', 'image_sha256')} |
                      {'ordinal': index, 'policy_sha256': '1'*64, 'reference_input_state': 'available',
                       'output_a': operand, 'output_b': deepcopy(operand)})
    return {'images': images, 'cases': []}


class SourceTests(unittest.TestCase):
    def test_complete_score_packet_retains_publisher_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); visible = toy_sources(root)
            packets, bindings, report = source_packets(root, visible)
            self.assertEqual(len(bindings), 8)
            self.assertEqual(report['output_a']['source_states'], {'processed': 1, 'empty': 1})
            self.assertEqual(packets['output_b']['image-2']['state'], 'empty')

    def test_changed_source_bytes_rejected_before_scores(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); visible = toy_sources(root)
            path = root/'results/export-06-64/PACKET.json'; path.write_text(path.read_text()+'\n')
            with self.assertRaisesRegex(ValueError, 'source bytes'): source_packets(root, visible)

    def test_missing_packet_row_cannot_become_empty(self):
        def missing(a, c, p):
            row = p['images'][1]
            for key in ('detections', 'empty_basis', 'source_detection_count'): del row[key]
            row.update(state='missing', reason='Synthetic missing export')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); visible = toy_sources(root, missing)
            with self.assertRaisesRegex(ValueError, 'Incomplete admitted packet'): source_packets(root, visible)

    def test_visible_population_substitution_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); visible = toy_sources(root); visible['images'].pop()
            with self.assertRaisesRegex(ValueError, 'membership'): source_packets(root, visible)

    def test_strict_boundary_removes_equal_scores_together(self):
        row = fixture()[2]['images'][0]; row['detections'] *= 2
        for i, detection in enumerate(row['detections']):
            row['detections'][i] = {**detection, 'id': 'd'+str(i), 'score': 0.5}
        before, _ = filtered_operand(row, Fraction(499, 1000)); at, custody = filtered_operand(row, Fraction(1, 2))
        self.assertEqual(len(before['value']), 2); self.assertEqual(at['value'], [])
        self.assertTrue(all(value['reason'] == 'score_not_strictly_above_threshold' for value in custody))

    def test_duplicate_occurrences_recanonicalize_after_filter(self):
        row = fixture()[2]['images'][0]; source = deepcopy(row['detections'][0])
        row['detections'] = [{**source, 'id': 'first', 'score': 0.4}, {**source, 'id': 'second', 'score': 0.8}]
        other = deepcopy(row); other['detections'] = [{**source, 'id': 'different', 'score': 0.8}]
        initial, _ = filtered_operand(row, FLOOR); selected, joins = filtered_operand(row, Fraction(1, 2))
        equivalent, _ = filtered_operand(other, Fraction(1, 2))
        self.assertNotEqual(initial['value'][1]['id'], selected['value'][0]['id'])
        self.assertEqual(selected, equivalent); self.assertEqual(joins[1]['source_detection_id'], 'second')

    def test_missing_and_filtered_empty_are_distinct_at_one(self):
        row = fixture()[2]['images'][0]; empty, _ = filtered_operand(row, 1)
        missing, _ = filtered_operand({'state': 'failed', 'reason': 'No output'}, 1)
        self.assertEqual(empty, {'state': 'observed', 'value': []})
        self.assertEqual(missing['state'], 'unavailable'); self.assertNotIn('value', missing)

    def test_exact_cells_cover_ties_and_final_endpoint(self):
        events = [Fraction(1, 2), Fraction(1, 2), Fraction(3, 4), Fraction(1)]
        result = cells(events, 10); self.assertEqual(result, expected_cells(events)); self.assertEqual(len(result), 4)
        for point in [Fraction(i, 40) for i in range(10, 41)]:
            containing = [cell for cell in result if q(cell['left']) <= point < q(cell['right'])
                          or cell['right_closed'] and q(cell['left']) == point == q(cell['right'])]
            self.assertEqual(len(containing), 1)
            representative = q(containing[0]['representative'])
            self.assertEqual([event > point for event in events], [event > representative for event in events])

    def test_empty_score_list_still_covers_retained_domain(self):
        result = cells([], 2); self.assertEqual(len(result), 2)
        self.assertEqual(list(map(q, [result[0]['left'], result[0]['right']])), [FLOOR, 1])

    def test_below_floor_and_resource_limit_fail_closed(self):
        row = fixture()[2]['images'][0]
        with self.assertRaisesRegex(ValueError, 'domain'): filtered_operand(row, Fraction(1, 5))
        with self.assertRaisesRegex(ValueError, 'limit'): cells([Fraction(1, 2)], 2)
        with self.assertRaisesRegex(ValueError, 'domain'): cells([FLOOR], 10)

    def test_independent_filter_and_join_agree(self):
        allocation, _, packet = fixture(); row = packet['images'][0]
        image = {key: row[key] for key in ('id', 'width', 'height', 'image_sha256')} | {
            'ordinal': 0, 'policy_sha256': '1'*64, 'reference_input_state': 'available',
            'output_a': {'state': 'observed', 'value': []}, 'output_b': {'state': 'observed', 'value': []}}
        packets = {role: {row['id']: row} for role in ROLES}
        for threshold in (FLOOR, Fraction(4, 5), Fraction(1)):
            self.assertEqual(filtered_image(image, packets, threshold, '2'*64), expected_filter(image, packets, threshold, '2'*64))


if __name__ == '__main__':
    unittest.main()
