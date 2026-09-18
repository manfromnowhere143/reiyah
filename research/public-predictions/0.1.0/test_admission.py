"""Synthetic rejection controls; none of these rows are research observations."""
from copy import deepcopy
import unittest
from admission import Rejected, admit, digest


def fixture():
    allocation = {'artifact_id': 'reiyah.public-predictions.allocation', 'version': '0.1.0',
        'exposure': 'development', 'population_id': 'synthetic-controls',
        'membership_basis': 'retained_image_bytes', 'source_binding_sha256': 'a' * 64,
        'images': [{'id': 'image-1', 'width': 200, 'height': 100, 'image_sha256': 'b' * 64},
                   {'id': 'image-2', 'width': 200, 'height': 100, 'image_sha256': 'c' * 64}]}
    configuration = {'artifact_id': 'reiyah.public-predictions.configuration', 'version': '0.1.0',
        'checkpoint_sha256': 'd' * 64,
        'runtime': {'name': 'synthetic', 'version': '0', 'device': 'none', 'precision': 'float32',
                    'binding_sha256': 'e' * 64},
        'preprocessing': {'color': 'RGB', 'resize': 'none', 'normalization': 'none', 'binding_sha256': 'e' * 64},
        'postprocessing': {'method': 'nms', 'confidence': 0.25, 'confidence_operator': 'gt', 'iou_threshold': 0.7,
            'maximum_detections': 300, 'class_agnostic': False, 'multi_label': False, 'binding_sha256': 'e' * 64},
        'categories': [{'id': 2, 'name': 'car'}], 'batch_size': 1,
        'coordinate_output': 'continuous_pixel_xyxy_clipped', 'rounding': 'none_source_float',
        'implementation_sha256': 'e' * 64}
    packet = {'artifact_id': 'reiyah.public-predictions.packet', 'version': '0.1.0',
        'allocation_sha256': digest(allocation), 'configuration_sha256': digest(configuration),
        'checkpoint_sha256': configuration['checkpoint_sha256'], 'source_binding_sha256': 'f' * 64,
        'images': []}
    for i, image in enumerate(allocation['images']):
        packet['images'].append({**image, 'configuration_sha256': digest(configuration),
            'state': 'processed' if i == 0 else 'empty',
            'detections': [{'id': 'detection-0', 'category_id': 2, 'category_name': 'car',
                            'score': 0.8, 'xyxy': [10, 10, 70, 80]}] if i == 0 else [],
            'source_detection_count': 1 if i == 0 else 0,
            'empty_basis': None if i == 0 else 'publisher_explicit_empty'})
    return allocation, configuration, packet


class AdmissionTests(unittest.TestCase):
    def reject(self, change, code):
        allocation, configuration, packet = fixture()
        change(allocation, configuration, packet)
        with self.assertRaises(Rejected) as caught:
            admit(allocation, configuration, packet)
        self.assertEqual(caught.exception.code, code)

    def test_complete_export_preserves_explicit_empty(self):
        result = admit(*fixture())
        self.assertTrue(result['complete_usable_export'])
        self.assertEqual(result['states'], {'processed': 1, 'empty': 1})
        self.assertEqual(result['detections'], 1)
        self.assertFalse(result['scientific_acceptance'])

    def test_missing_and_failed_remain_blocked_allocation_members(self):
        for state in ('missing', 'failed'):
            allocation, configuration, packet = fixture()
            row = packet['images'][1]
            for key in ('detections', 'source_detection_count', 'empty_basis'):
                del row[key]
            row.update(state=state, reason='Synthetic unavailable input')
            result = admit(allocation, configuration, packet)
            self.assertEqual(result['allocated_images'], 2)
            self.assertEqual(result['blocked_images'], ['image-2'])
            self.assertFalse(result['complete_usable_export'])

    def test_absent_row_never_becomes_empty(self):
        self.reject(lambda a, c, p: p['images'].pop(), 'COVERAGE')

    def test_unknown_member_cannot_replace_missing_member(self):
        self.reject(lambda a, c, p: p['images'][1].update(id='different-image'), 'COVERAGE')

    def test_duplicate_image_cannot_fill_coverage(self):
        self.reject(lambda a, c, p: p['images'].__setitem__(1, deepcopy(p['images'][0])), 'DUPLICATE_IMAGE')

    def test_duplicate_allocation_rejected(self):
        self.reject(lambda a, c, p: a['images'].__setitem__(1, deepcopy(a['images'][0])), 'DUPLICATE_IMAGE')

    def test_image_dimensions_and_byte_identity_bound(self):
        self.reject(lambda a, c, p: p['images'][0].update(width=201), 'DIMENSION_MISMATCH')
        self.reject(lambda a, c, p: p['images'][0].update(image_sha256='0' * 64), 'IMAGE_BINDING')

    def test_false_empty_and_missing_with_detections_rejected(self):
        self.reject(lambda a, c, p: p['images'][0].update(state='empty'), 'EMPTY_STATE')
        self.reject(lambda a, c, p: p['images'][1].update(state='processed'), 'EMPTY_STATE')
        self.reject(lambda a, c, p: p['images'][1].update(state='missing', reason='absent'), 'FIELDS')
        self.reject(lambda a, c, p: p['images'][1].update(empty_basis=None), 'EMPTY_BASIS')

    def test_declared_filter_empty_does_not_claim_publisher_empty(self):
        allocation, configuration, packet = fixture()
        packet['images'][1].update(source_detection_count=3, empty_basis='frozen_filter')
        self.assertTrue(admit(allocation, configuration, packet)['complete_usable_export'])
        packet['images'][1]['empty_basis'] = 'publisher_explicit_empty'
        with self.assertRaises(Rejected) as caught:
            admit(allocation, configuration, packet)
        self.assertEqual(caught.exception.code, 'EMPTY_BASIS')

    def test_category_names_and_ids_are_jointly_checked(self):
        for change in ({'category_id': 99}, {'category_name': 'person'}, {'category_id': True}):
            self.reject(lambda a, c, p: p['images'][0]['detections'][0].update(change), 'CATEGORY_MISMATCH')

    def test_duplicate_detection_id_is_not_silently_deduplicated(self):
        def duplicate(a, c, p):
            row = p['images'][0]
            row['detections'].append(deepcopy(row['detections'][0])); row['source_detection_count'] = 2
        self.reject(duplicate, 'DUPLICATE_DETECTION')

    def test_invalid_geometry_and_nonfinite_numbers(self):
        for coordinates in ([10, 10, 10, 80], [70, 10, 10, 80], [-1, 10, 70, 80],
                            [10, 10, 201, 80], [10, 10, 70, 101]):
            self.reject(lambda a, c, p: p['images'][0]['detections'][0].update(xyxy=coordinates), 'COORDINATE')
        for value in (float('nan'), float('inf'), -float('inf'), True, '10'):
            self.reject(lambda a, c, p: p['images'][0]['detections'][0].update(xyxy=[value, 10, 70, 80]), 'NUMBER')

    def test_confidence_threshold_and_maximum_are_obligations(self):
        self.reject(lambda a, c, p: p['images'][0]['detections'][0].update(score=0.25), 'SCORE')
        self.reject(lambda a, c, p: p['images'][0]['detections'][0].update(score=0.2499), 'SCORE')
        self.reject(lambda a, c, p: p['images'][0]['detections'][0].update(score=1.001), 'SCORE')
        self.reject(lambda a, c, p: p['images'][0].update(source_detection_count=0), 'SOURCE_COUNT')

    def test_inconsistent_postprocessing_is_rejected_even_with_matching_packet_header(self):
        self.reject(lambda a, c, p: p['images'][1].update(configuration_sha256='0' * 64), 'POSTPROCESSING_CHANGED')
        def change_settings(a, c, p):
            c['postprocessing']['confidence'] = 0.5
            p['configuration_sha256'] = digest(c)
        self.reject(change_settings, 'POSTPROCESSING_CHANGED')

    def test_changed_checkpoint_configuration_and_allocation_rejected(self):
        self.reject(lambda a, c, p: p.update(checkpoint_sha256='0' * 64), 'CHECKPOINT_BINDING')
        self.reject(lambda a, c, p: c.update(rounding='decimal_6'), 'CONFIGURATION_BINDING')
        self.reject(lambda a, c, p: a.update(population_id='different-population'), 'ALLOCATION_BINDING')

    def test_unknown_fields_reserved_scope_and_unpinned_images_rejected(self):
        self.reject(lambda a, c, p: p.update(hidden_answer='forbidden'), 'FIELDS')
        self.reject(lambda a, c, p: a.update(exposure='outcome_reserved'), 'EXPOSURE')
        self.reject(lambda a, c, p: a['images'][0].update(image_sha256=None), 'DIGEST')


if __name__ == '__main__':
    unittest.main()
