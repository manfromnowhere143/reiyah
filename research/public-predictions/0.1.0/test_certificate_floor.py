"""Compare the new certificate-size calculation with exhaustive small subsets."""
from itertools import combinations
import random
import unittest

from certificate_floor import minimum_certificate
from compare_math import FAMILIES, decision, interval, w
from test_compare_math import picture, rectangle


def algebraic_case(parameters):
    images, measurements = [], {}
    for index, (radius, nominal, lo, hi) in enumerate(parameters):
        image = picture([], [rectangle('p-' + str(index) + '-' + str(j)) for j in range(radius)], ordinal=index)
        images.append(image)
        measurements[image['id']] = {'nominal': {'delta': w(nominal)}, 'edit_bounds': [w(lo), w(hi)]}
    return images, measurements


def exhaustive(images, measurements, family):
    outcome = decision(interval(images, measurements, family))
    if outcome in ('unresolved', 'input_blocked'):
        return None
    ids = [image['id'] for image in images]
    for count in range(len(ids) + 1):
        for subset in combinations(ids, count):
            if decision(interval(images, {iid: measurements[iid] for iid in subset}, family)) == outcome:
                return count
    raise AssertionError('Full case did not resolve itself')


class FloorControls(unittest.TestCase):
    def test_strict_support_and_nonstrict_exclusion_thresholds(self):
        images, values = algebraic_case([(1, 1, 1, 1), (1, -1, -1, -1)])
        floor = minimum_certificate(images, values, 'exact_projection')
        self.assertEqual(floor['decision'], 'excluded')
        self.assertEqual(floor['minimum_queries'], 1)
        images, values = algebraic_case([(1, 1, 1, 1)] * 3)
        self.assertEqual(minimum_certificate(images, values, 'exact_projection')['minimum_queries'], 2)

    def test_global_penalty_can_make_largest_nominal_gain_a_bad_choice(self):
        images, values = algebraic_case([(3, 3, -1, 3), (2, 2, 2, 2), (2, 2, 2, 2)])
        result = minimum_certificate(images, values, 'one_edit_global')
        self.assertEqual(result['minimum_queries'], 2)
        self.assertEqual(set(result['sufficient_subset']), {'image-01', 'image-02'})

    def test_zero_queries_and_unresolved_are_distinct(self):
        images, values = algebraic_case([(0, 0, 0, 0)])
        self.assertEqual(minimum_certificate(images, values, 'one_edit_global')['minimum_queries'], 0)
        images, values = algebraic_case([(1, 1, -1, 1)])
        result = minimum_certificate(images, values, 'one_edit_per_image')
        self.assertEqual(result['decision'], 'unresolved'); self.assertIsNone(result['minimum_queries'])

    def test_blocked_input_requires_no_fabricated_full_answer(self):
        image = picture([], [], reference='unavailable')
        result = minimum_certificate([image], {}, 'exact_projection')
        self.assertEqual(result['decision'], 'input_blocked'); self.assertIsNone(result['minimum_queries'])

    def test_matches_exhaustive_subsets_for_3600_algebraic_cases(self):
        randomizer = random.Random(1729)
        for index in range(1200):
            parameters = []
            for image in range(1 + index % 6):
                radius = randomizer.randrange(0, 5)
                nominal = randomizer.choice(list(range(-radius, radius + 1, 2)))
                lo = max(-radius, nominal - randomizer.randrange(0, 5))
                hi = min(radius, nominal + randomizer.randrange(0, 5))
                parameters.append((radius, nominal, lo, hi))
            images, values = algebraic_case(parameters)
            for family in FAMILIES:
                with self.subTest(index=index, family=family):
                    self.assertEqual(minimum_certificate(images, values, family)['minimum_queries'],
                                     exhaustive(images, values, family))


if __name__ == '__main__':
    unittest.main()
