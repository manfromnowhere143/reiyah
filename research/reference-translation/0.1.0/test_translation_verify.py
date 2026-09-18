from copy import deepcopy
from fractions import Fraction as F
import unittest

from test_translation_search import picture, rectangle
from translation_search import checked_extrema, enumerate_image, minimum_affected, primary_critical_radius, q, w
from translation_run import case_rows
from translation_verify import (check_affected, check_critical, check_partition, check_radius, check_world, extrema)


class TranslationVerificationControls(unittest.TestCase):
    def setUp(self):
        self.image = picture([], [rectangle('b')]); self.references = [rectangle('r')]
        self.result = enumerate_image(self.image, self.references)

    def verified(self):
        return check_partition(self.image, self.references, self.result)

    def test_complete_partition_and_actual_extrema_verify(self):
        verified = self.verified(); proofs = {}
        for radius in [0, 1, 10, 11, 64]:
            witnesses = checked_extrema(self.image, self.references, self.result, radius, proofs)
            bounds = check_radius(self.image, self.references, verified, witnesses, F(radius), proofs)
            self.assertEqual(bounds, (1 if radius <= 10 else -1, 1))

    def test_missing_cell_and_forged_matching_rejected(self):
        missing = deepcopy(self.result); missing['states'].pop(); missing['cells'] -= 1
        with self.assertRaises(ValueError):
            check_partition(self.image, self.references, missing)
        changed = deepcopy(self.result); changed['states'][0]['measurement']['delta'] = w(F(17))
        with self.assertRaises(ValueError):
            check_partition(self.image, self.references, changed)

    def test_open_cell_cannot_claim_inclusive_activation(self):
        changed = deepcopy(self.result)
        state = next(s for s in changed['states'] if not s['infimum_attained'] and q(s['radius_infimum']) == 10)
        state['infimum_attained'] = True
        with self.assertRaises(ValueError):
            check_partition(self.image, self.references, changed)

    def test_world_cannot_exceed_radius_or_change_shape(self):
        verified = self.verified(); proofs = {}
        witnesses = checked_extrema(self.image, self.references, self.result, 11, proofs)
        with self.assertRaises(ValueError):
            check_world(self.image, self.references, verified, witnesses['lower'], F(10), proofs)
        changed = deepcopy(witnesses['lower']); changed['edit']['translated_reference']['xyxy'][2] = w(F(100))
        with self.assertRaises(ValueError):
            check_world(self.image, self.references, verified, changed, F(11), proofs)
        changed = deepcopy(witnesses['lower']); changed['edit']['second_reference'] = 'invented'
        with self.assertRaises(ValueError):
            check_world(self.image, self.references, verified, changed, F(11), proofs)

    def test_proof_bytes_cannot_change_after_current_world_check(self):
        verified = self.verified(); proofs = {}
        witnesses = checked_extrema(self.image, self.references, self.result, 11, proofs)
        check_radius(self.image, self.references, verified, witnesses, F(11), proofs)
        key = witnesses['lower']['proof_key']; proofs[key]['proof']['payload']['unexpected'] = True
        with self.assertRaises(ValueError):
            check_world(self.image, self.references, verified, witnesses['lower'], F(11), proofs)

    def test_critical_attainment_and_inflated_radius_rejected(self):
        verified = {self.image['id']: self.verified()}
        critical = primary_critical_radius({self.image['id']: self.result})
        check_critical(verified, critical)
        changed = deepcopy(critical); changed['attained'] = True; changed['witness_radius'] = changed['radius_infimum']
        with self.assertRaises(ValueError):
            check_critical(verified, changed)
        changed = {'radius_infimum': w(F(11)), 'attained': True, 'witness_radius': w(F(11)),
                   'lower_total_before_infimum': w(F(-1)), 'lower_total_at_infimum': w(F(-1))}
        with self.assertRaises(ValueError):
            check_critical(verified, changed)

    def test_affected_image_floor_checks_both_sufficiency_and_minimality(self):
        downward = {'a': F(2), 'b': F(2), 'c': F(2)}
        good = minimum_affected(F(3), downward); check_affected(F(3), downward, good)
        inflated = deepcopy(good); inflated.update(minimum_images=3, image_ids=['a', 'b', 'c'],
                                                   witness_total=w(F(-3)), one_fewer_maximum_damage=w(F(4)))
        with self.assertRaises(ValueError):
            check_affected(F(3), downward, inflated)
        with self.assertRaises(ValueError):
            check_affected(F(3), downward, {'minimum_images': None})

    def test_failed_image_does_not_become_an_empty_reference(self):
        image = self.image; value = deepcopy(self.result); proofs = {}
        value['radii'] = {str(radius): checked_extrema(image, self.references, value, radius, proofs)
                          for radius in [0, 1, 2, 4, 8, 16, 32, 64]}
        visible = {'cases': [{'id': 'good', 'group': 'singleton', 'images': [image['id']]},
                             {'id': 'failed', 'group': 'singleton', 'images': ['image-01']},
                             {'id': 'both', 'group': 'primary', 'images': [image['id'], 'image-01']}]}
        rows = case_rows(visible, {image['id']: value}, {'image-01': {'state': 'analysis_incomplete'}})
        self.assertEqual(len(rows), 24)
        self.assertEqual(sum(row['state'] == 'analysis_incomplete' for row in rows), 16)
        self.assertTrue(all(row['bounds'] is None for row in rows if row['state'] == 'analysis_incomplete'))

    def test_empty_complete_population_is_not_a_zero_radius_result(self):
        with self.assertRaises(ValueError):
            primary_critical_radius({})
        with self.assertRaises(ValueError):
            primary_critical_radius({self.image['id']: self.result}, maximum=-1)


if __name__ == '__main__':
    unittest.main()
