"""New adapter, information-boundary and replacement-observation controls."""
from copy import deepcopy
from fractions import Fraction
import unittest

from admission import Rejected, digest
from compare_math import (FAMILIES, decision, interval, measure, q, ranking, subject,
                          validate_event, validate_image, w)


def rectangle(identity, left=0, top=0, right=100, bottom=100):
    return {'id': identity, 'record_sha256': digest([identity, left, top, right, bottom]),
            'xyxy': [w(Fraction(value)) for value in (left, top, right, bottom)]}


def picture(a, b, ordinal=0, reference='available'):
    return {'id': 'image-' + str(ordinal).zfill(2), 'ordinal': ordinal, 'width': 1600, 'height': 900,
            'image_sha256': 'a' * 64, 'policy_sha256': 'b' * 64,
            'output_a': {'state': 'observed', 'value': a}, 'output_b': {'state': 'observed', 'value': b},
            'reference_input_state': reference}


class ComparisonControls(unittest.TestCase):
    def test_native_and_conventional_match_on_replacement_and_every_deletion(self):
        image = picture([rectangle('a'), rectangle('shared', 200, 0, 300, 100)],
                        [rectangle('b', 100, 0, 200, 100), rectangle('shared', 200, 0, 300, 100)])
        refs = [rectangle('r0'), rectangle('r1', 200, 0, 300, 100)]
        validate_image(image)
        for family in FAMILIES:
            with self.subTest(family=family):
                normal = measure(image, refs, family, 'conventional')
                checked = measure(image, refs, family, 'native')
                for key in ('nominal', 'edit_bounds', 'deletion_bases'):
                    self.assertEqual(normal[key], checked[key])
                self.assertEqual(q(checked['nominal']['delta']), -2)
                self.assertEqual(len(checked['proofs']), 1 if family == 'exact_projection' else 3)

    def test_one_edit_bounds_cover_car_class_entry_exit_and_displacement(self):
        image = picture([rectangle('a')], [rectangle('b', 100, 0, 200, 100)])
        refs = [rectangle('original')]
        measured = measure(image, refs, 'one_edit_per_image', 'conventional')
        lo, hi = map(q, measured['edit_bounds'])
        worlds = [[], refs, refs + [rectangle('inserted', 100, 0, 200, 100)],
                  [rectangle('replacement', 100, 0, 200, 100)], [rectangle('away', 400, 0, 500, 100)]]
        for world in worlds:
            actual = q(measure(image, world, 'exact_projection', 'conventional')['nominal']['delta'])
            self.assertLessEqual(lo, actual); self.assertLessEqual(actual, hi)
        self.assertEqual((lo, hi), (-2, 2))

    def test_global_budget_is_not_spent_once_per_observed_image(self):
        images = [picture([], [rectangle('b' + str(index))], ordinal=index) for index in range(2)]
        measurements = {image['id']: measure(image, [rectangle('reference')], 'one_edit_global', 'conventional')
                        for image in images}
        self.assertEqual(interval(images, measurements, 'exact_projection'), (1, 1))
        self.assertEqual(interval(images, measurements, 'one_edit_global'), (0, 1))
        self.assertEqual(interval(images, measurements, 'one_edit_per_image'), (-1, 1))

    def test_unobserved_global_member_does_not_become_zero(self):
        images = [picture([], [rectangle('b' + str(index))], ordinal=index) for index in range(2)]
        measured = {images[0]['id']: measure(images[0], [rectangle('reference')], 'one_edit_global', 'conventional')}
        self.assertEqual(interval(images, measured, 'one_edit_global'), (-1, 1))
        self.assertEqual(decision(interval(images, measured, 'one_edit_global')), 'unresolved')

    def test_missing_reference_and_missing_prediction_are_blocked(self):
        image = picture([], [], reference='unavailable')
        self.assertIsNone(interval([image], {}, 'exact_projection'))
        self.assertEqual(ranking([image], 'width'), [])
        image = picture([], []); image['output_a'] = {'state': 'unavailable', 'reason': 'Failed export'}
        validate_image(image)
        self.assertEqual(decision(interval([image], {}, 'exact_projection')), 'input_blocked')

    def test_identical_outputs_need_zero_queries_even_if_nonempty(self):
        image = picture([rectangle('same')], [rectangle('same')])
        self.assertEqual(ranking([image], 'width'), [])
        for family in FAMILIES:
            self.assertEqual(interval([image], {}, family), (0, 0))
            self.assertEqual(decision(interval([image], {}, family)), 'excluded')

    def test_selector_information_boundary_rejects_hidden_reference_fields(self):
        image = picture([rectangle('a')], [rectangle('b')])
        for key, value in [('original_reference', []), ('corrected_count', 2),
                           ('reference_sha256', 'c' * 64), ('reference_edges', [])]:
            with self.subTest(key=key):
                changed = deepcopy(image); changed[key] = value
                with self.assertRaises(Rejected):
                    validate_image(changed)

    def test_selector_cells_have_fixed_distinct_priorities(self):
        widest = picture([rectangle('a0'), rectangle('a1', 200, 0, 300, 100)],
                         [rectangle('b0', 400, 0, 500, 100), rectangle('b1', 600, 0, 700, 100)], ordinal=0)
        imbalance = picture([], [rectangle('b2'), rectangle('b3', 200, 0, 300, 100),
                                 rectangle('b4', 400, 0, 500, 100)], ordinal=1)
        self.assertEqual(ranking([widest, imbalance], 'width'), ['image-00', 'image-01'])
        self.assertEqual(ranking([widest, imbalance], 'count_difference'), ['image-01', 'image-00'])

    def test_stale_or_changed_observation_is_rejected(self):
        image = picture([], [rectangle('b')])
        request = {'image_id': image['id'], 'subject_sha256': subject(image), 'family': 'one_edit_global', 'sequence': 1}
        event = {'request': request, 'answer': [rectangle('r')], 'source_sha256': 'c' * 64,
            'basis': 'published_annotation_projection', 'residual': 'one_edit_global',
            'requested_utc': '2026-09-18T00:00:00+00:00', 'returned_utc': '2026-09-18T00:00:00+00:00',
            'cost': {'observation_units': 1, 'human_seconds': None, 'human_cost': None, 'service_seconds': 0.0}}
        event['evidence_sha256'] = digest(event)
        self.assertEqual(validate_event(event, request, image), event['answer'])
        changed = deepcopy(event); changed['answer'] = []
        with self.assertRaises(Rejected):
            validate_event(changed, request, image)
        changed = deepcopy(request); changed['sequence'] = 2
        with self.assertRaises(Rejected):
            validate_event(event, changed, image)
        changed = deepcopy(event); changed['cost']['observation_units'] = True
        changed['evidence_sha256'] = digest({key: value for key, value in changed.items() if key != 'evidence_sha256'})
        with self.assertRaises(Rejected):
            validate_event(changed, request, image)

    def test_reused_detection_identity_cannot_change_geometry(self):
        image = picture([rectangle('same')], [rectangle('same', 1, 0, 101, 100)])
        with self.assertRaises(ValueError):
            validate_image(image)


if __name__ == '__main__':
    unittest.main()
