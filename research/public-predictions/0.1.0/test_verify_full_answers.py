"""Independent verification controls for floors, worlds and edit thresholds."""
from copy import deepcopy
import unittest

from admission import Rejected
from analyze_results import compose, minimal_primary_edits
from certificate_floor import minimum_certificate
from compare_math import q, w
from geometric_worlds import search_image
from test_analyze_results import components
from test_certificate_floor import algebraic_case
from test_compare_math import picture, rectangle
from verify_full_answers import verify_component, verify_composition, verify_edit_threshold, verify_floor


class AnalysisVerificationControls(unittest.TestCase):
    def test_minimum_query_claim_is_verified_and_inflation_is_rejected(self):
        images, values = algebraic_case([(1, 1, 1, 1)] * 3)
        floor = minimum_certificate(images, values, 'exact_projection')
        self.assertTrue(verify_floor(images, values, 'exact_projection', floor)['optimality_checked'])
        changed = deepcopy(floor); changed['minimum_queries'] = 3
        changed['sufficient_subset'] = [image['id'] for image in images]
        changed['subset_bounds'] = changed['full_bounds']
        with self.assertRaises(Rejected):
            verify_floor(images, values, 'exact_projection', changed)

    def test_global_penalty_floor_has_a_separate_optimality_check(self):
        images, values = algebraic_case([(3, 3, -1, 3), (2, 2, 2, 2), (2, 2, 2, 2)])
        floor = minimum_certificate(images, values, 'one_edit_global')
        self.assertEqual(verify_floor(images, values, 'one_edit_global', floor)['minimum_queries'], 2)

    def test_actual_adverse_component_and_canvas_are_checked(self):
        image = picture([rectangle('a')], [rectangle('b', 100, 0, 200, 100)])
        refs = [rectangle('observed')]; search = search_image(image, refs)
        record = {'image_id': image['id'], 'nominal': search['nominal'], 'search_state': 'complete', 'search': search}
        result = verify_component(image, refs, record)
        self.assertEqual((result['lower'], result['upper']), (-2, 2))
        changed = deepcopy(record)
        changed['search']['witnesses']['upper']['edit']['inserted_reference']['xyxy'][0] = w(-1)
        with self.assertRaises(Rejected):
            verify_component(image, refs, changed)

    def test_composed_world_cannot_spend_global_budget_twice(self):
        images, records = components(3)
        checked = {image['id']: {'nominal': q(w(1)), 'lower': q(w(-1)), 'upper': q(w(1))} for image in images}
        world = compose(images, records, 'one_edit_per_image', 'lower')
        self.assertEqual(verify_composition(images, checked, 'one_edit_per_image', world), -1)
        with self.assertRaises(Rejected):
            verify_composition(images, checked, 'one_edit_global', world)
        changed = deepcopy(world); changed['complete_case_membership'] = changed['complete_case_membership'][:-1]
        with self.assertRaises(Rejected):
            verify_composition(images, checked, 'one_edit_per_image', changed)

    def test_exact_threshold_needs_both_impossibility_and_a_real_reversal(self):
        images, records = components(3)
        checked = {image['id']: {'nominal': q(w(1)), 'lower': q(w(-1)), 'upper': q(w(1))} for image in images}
        result = minimal_primary_edits(images, records)
        self.assertEqual(verify_edit_threshold(images, records, checked, result)['minimum_affected_images'], 2)
        changed = deepcopy(result); changed['lower_bound'] = 3
        with self.assertRaises(Rejected):
            verify_edit_threshold(images, records, checked, changed)
        changed = deepcopy(result); changed['witness_total_delta'] = w(1)
        with self.assertRaises(Rejected):
            verify_edit_threshold(images, records, checked, changed)


if __name__ == '__main__':
    unittest.main()
