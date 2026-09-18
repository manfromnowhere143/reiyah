from copy import deepcopy
from fractions import Fraction as F
import unittest

from translation_search import (attained_world, checked_extrema, digest, enumerate_image, extrema_states,
                                measure, minimum_affected, primary_critical_radius, q, record, w)


def rectangle(identity, left=10, top=0, width=30, height=30):
    xyxy = [w(F(v)) for v in [left, top, left + width, top + height]]
    return {'id': identity, 'record_sha256': digest({'id': identity, 'xyxy': xyxy}), 'xyxy': xyxy}


def picture(a, b, ordinal=0):
    return {'id': 'image-' + str(ordinal).zfill(2), 'ordinal': ordinal, 'width': 100, 'height': 100,
            'image_sha256': 'a' * 64, 'policy_sha256': 'b' * 64,
            'output_a': {'state': 'observed', 'value': a}, 'output_b': {'state': 'observed', 'value': b},
            'reference_input_state': 'available'}


class TranslationSearchControls(unittest.TestCase):
    def test_unattained_critical_radius_has_an_actual_later_world(self):
        image = picture([], [rectangle('b')]); refs = [rectangle('r')]
        result = enumerate_image(image, refs)
        critical = primary_critical_radius({image['id']: result})
        self.assertEqual(q(critical['radius_infimum']), 10)
        self.assertFalse(critical['attained'])
        self.assertEqual(q(critical['lower_total_at_infimum']), 1)
        self.assertEqual(q(critical['right_limit_lower_total']), -1)
        radius = q(critical['witness_radius'])
        self.assertGreater(radius, 10)
        proof_cache = {}; witnesses = checked_extrema(image, refs, result, radius, proof_cache)
        self.assertEqual(q(witnesses['lower']['delta']), -1)
        self.assertLessEqual(q(witnesses['lower']['edit']['distance']), radius)
        self.assertEqual(extrema_states(result, 10)[0][0], 1)
        self.assertTrue(proof_cache)

    def test_attained_critical_radius_includes_iou_equality(self):
        image = picture([rectangle('a', 30)], [rectangle('b')]); refs = [rectangle('r')]
        result = enumerate_image(image, refs)
        critical = primary_critical_radius({image['id']: result})
        self.assertEqual(q(critical['radius_infimum']), 10)
        self.assertTrue(critical['attained'])
        self.assertEqual(q(critical['lower_total_at_infimum']), 0)
        self.assertEqual(extrema_states(result, F(999, 100))[0][0], 2)

    def test_no_excluding_world_within_declared_maximum(self):
        image = picture([], [rectangle('b')]); refs = [rectangle('r')]
        result = enumerate_image(image, refs)
        critical = primary_critical_radius({image['id']: result}, maximum=10)
        self.assertIsNone(critical['radius_infimum'])
        self.assertEqual(q(critical['lower_total_at_maximum']), 1)

    def test_correlated_world_needs_two_of_three_images(self):
        records = {}
        for i in range(3):
            image = picture([], [rectangle('b')], i)
            records[image['id']] = enumerate_image(image, [rectangle('r')])
        critical = primary_critical_radius(records)
        self.assertEqual(q(critical['radius_infimum']), 10)
        self.assertFalse(critical['attained'])
        downward = {iid: q(value['nominal']['delta']) - extrema_states(value, 11)[0][0]
                    for iid, value in records.items()}
        count = minimum_affected(3, downward)
        self.assertEqual(count['minimum_images'], 2)
        self.assertEqual(q(count['one_fewer_maximum_damage']), 2)
        self.assertEqual(q(count['witness_total']), -1)

    def test_empty_reference_and_shared_prediction_states(self):
        image = picture([], [rectangle('b')]); result = enumerate_image(image, [])
        self.assertEqual(result['states'], [])
        self.assertEqual(extrema_states(result, 64)[0][0], -1)
        self.assertEqual(primary_critical_radius({image['id']: result})['attained'], True)
        same = rectangle('shared')
        image = picture([same], [deepcopy(same)])
        result = enumerate_image(image, [rectangle('r')])
        for radius in [0, 1, 10, 64]:
            lo, hi = extrema_states(result, radius)
            self.assertEqual((lo[0], hi[0]), (0, 0))

    def test_duplicate_occurrences_and_direct_geometric_enumeration(self):
        image = picture([rectangle('a1', 30), rectangle('a2', 30)],
                        [rectangle('b1'), rectangle('b2', 60)])
        refs = [rectangle('r1'), rectangle('r2', 60)]
        result = enumerate_image(image, refs)
        nominal = q(result['nominal']['delta'])
        # These 30x30 aligned fixtures have integer IoU transition positions.
        # A half-pixel independent grid covers their endpoints/open cells.
        for radius in [0, 1, 5, 10, 11, 20, 64]:
            values = [nominal]
            for index, reference in enumerate(refs):
                base = list(map(q, reference['xyxy']))
                for axis in [0, 1]:
                    for half in range(141):
                        position = F(half, 2)
                        if abs(position - base[axis]) > radius:
                            continue
                        changed = list(base); changed[axis] = position; changed[axis + 2] = position + 30
                        world = [row for i, row in enumerate(refs) if i != index] + [record(changed)]
                        values.append(q(measure(image, world, 'exact_projection', 'conventional')['nominal']['delta']))
            low, high = extrema_states(result, radius)
            self.assertEqual((low[0], high[0]), (min(values), max(values)))

    def test_unavailable_input_and_ineligible_reference_rejected(self):
        image = picture([], []); image['reference_input_state'] = 'unavailable'
        with self.assertRaises(ValueError):
            enumerate_image(image, [])
        with self.assertRaises(ValueError):
            enumerate_image(picture([], []), [rectangle('short', height=24)])

    def test_affected_count_cannot_use_unattainable_negative_damage(self):
        with self.assertRaises(ValueError):
            minimum_affected(1, {'image-00': F(-1)})
        result = minimum_affected(5, {'image-00': F(2), 'image-01': F(2)})
        self.assertIsNone(result['minimum_images'])
        self.assertEqual(q(result['maximum_damage']), 4)


if __name__ == '__main__':
    unittest.main()
