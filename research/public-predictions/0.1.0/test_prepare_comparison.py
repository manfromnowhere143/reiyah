"""Actual adapter failure modes on synthetic prediction and projection rows."""
from copy import deepcopy
import unittest

from admission import digest
from prepare_comparison import prediction_operand, reference_operand


def detection(identity, category=2, coordinates=None, score=0.8):
    return {'id': identity, 'category_id': category, 'category_name': 'car' if category == 2 else 'truck',
            'score': score, 'xyxy': [1, 2, 80, 100] if coordinates is None else coordinates}


class PreparationControls(unittest.TestCase):
    def test_shared_identity_uses_metric_geometry_not_score_or_export_order(self):
        first, _ = prediction_operand({'state': 'processed', 'detections': [detection('different-source-id', score=0.4)]})
        second, _ = prediction_operand({'state': 'processed', 'detections': [detection('another-id', score=0.9)]})
        self.assertEqual(first, second)

    def test_duplicate_predictions_remain_distinct_occurrences(self):
        value, custody = prediction_operand({'state': 'processed', 'detections': [detection('one'), detection('two')]})
        self.assertEqual(len(value['value']), 2)
        self.assertNotEqual(value['value'][0]['id'], value['value'][1]['id'])
        self.assertEqual(len(custody), 2)

    def test_failed_and_missing_do_not_become_empty(self):
        for state in ('failed', 'missing'):
            value, custody = prediction_operand({'state': state, 'reason': 'retained failure'})
            self.assertEqual(value['state'], 'unavailable'); self.assertNotIn('value', value)
        value, _ = prediction_operand({'state': 'empty', 'detections': []})
        self.assertEqual(value, {'state': 'observed', 'value': []})

    def test_category_and_exact_height_exclusions_are_retained(self):
        row = {'state': 'processed', 'detections': [detection('car'), detection('truck', category=7),
            detection('short', coordinates=[1, 10.000000000000002, 80, 35.0])]}
        operand, custody = prediction_operand(row)
        self.assertEqual(len(operand['value']), 1)
        self.assertEqual([value.get('reason') for value in custody], [None, 'category_outside_car', 'height_below_25'])

    def test_source_reference_boundary_change_is_explicit(self):
        row = {'sample_annotation_token': 'boundary', 'sample_data_token': 'camera', 'category_name': 'vehicle.car',
               'bbox_corners': [1, 10.000000000000002, 80, 35.0]}
        source = {'state': 'observed', 'all_projection_rows': [row], 'exclusions': [],
                  'answer': [{'id': 'reference:boundary', 'record_sha256': digest(row), 'xyxy': row['bbox_corners']}]}
        before = deepcopy(source)
        answer, review = reference_operand(source, {'sensor_sample_token': 'camera', 'width': 1600, 'height': 900})
        self.assertEqual(answer, []); self.assertTrue(review['exact_decimal_selection_changed'])
        self.assertEqual(review['state'], 'available'); self.assertEqual(source, before)

    def test_unavailable_reference_has_no_empty_answer(self):
        answer, review = reference_operand({'state': 'unavailable', 'reason': 'projection failed'}, {})
        self.assertIsNone(answer); self.assertEqual(review['state'], 'unavailable')


if __name__ == '__main__':
    unittest.main()
