"""Edit-budget composition controls using supplied synthetic component bounds."""
import unittest

from analyze_results import compose, minimal_primary_edits
from compare_math import q, w
from test_compare_math import picture, rectangle


def components(count, nominal=1, lower=-1, achieved=-1, complete=True):
    images = [picture([], [rectangle('prediction-' + str(index))], ordinal=index) for index in range(count)]
    records = {image['id']: {'image_id': image['id'], 'search_state': 'complete' if complete else 'incomplete',
        'nominal': {'nominal': {'delta': w(nominal)}, 'edit_bounds': [w(lower), w(nominal)]},
        'search': {'witnesses': {'lower': {'measurement': {'delta': w(achieved)}},
                                 'upper': {'measurement': {'delta': w(nominal)}}}}} for image in images}
    return images, records


class CompositionControls(unittest.TestCase):
    def test_global_world_changes_at_most_one_image(self):
        images, records = components(3)
        world = compose(images, records, 'one_edit_global', 'lower')
        self.assertEqual(len(world['edited_images']), 1)
        self.assertEqual(q(world['delta']), q(w(1)) / 3)
        self.assertEqual(world['decision'], 'supported')

    def test_correlated_per_image_world_can_reverse_nominal_decision(self):
        images, records = components(3)
        world = compose(images, records, 'one_edit_per_image', 'lower')
        self.assertEqual(len(world['edited_images']), 3)
        self.assertEqual(q(world['delta']), -1)
        self.assertEqual(world['decision'], 'excluded')

    def test_minimum_edited_images_respects_zero_exclusion_boundary(self):
        images, records = components(2)
        result = minimal_primary_edits(images, records)
        self.assertEqual((result['lower_bound'], result['upper_bound']), (1, 1))
        self.assertEqual(q(result['witness_total_delta']), 0)
        self.assertTrue(result['exact'])
        images, records = components(3)
        result = minimal_primary_edits(images, records)
        self.assertEqual((result['lower_bound'], result['upper_bound']), (2, 2))

    def test_unachieved_bound_retains_a_count_gap(self):
        images, records = components(2, nominal=2, lower=-2, achieved=0)
        result = minimal_primary_edits(images, records)
        self.assertEqual((result['lower_bound'], result['upper_bound']), (1, 2))
        self.assertFalse(result['exact'])

    def test_incomplete_search_does_not_fabricate_an_adverse_world(self):
        images, records = components(2, complete=False)
        world = compose(images, records, 'one_edit_per_image', 'lower')
        self.assertEqual(world['edited_images'], [])
        self.assertEqual(world['decision'], 'supported')
        result = minimal_primary_edits(images, records)
        self.assertEqual(result['lower_bound'], 1); self.assertIsNone(result['upper_bound'])

    def test_already_excluded_nominal_needs_no_adverse_edit(self):
        images, records = components(2, nominal=0, lower=-2, achieved=-2)
        result = minimal_primary_edits(images, records)
        self.assertEqual((result['lower_bound'], result['upper_bound']), (0, 0))


if __name__ == '__main__':
    unittest.main()
