"""Dominance, feasibility, tied policies and complete Cartesian outcomes."""
from copy import deepcopy
import itertools
import unittest

from operating_frontier import budget_minima, compare_curves, frontier
from operating_certificate import check_curves


def curve(pairs):
    return [{'cell_id': 'c'+str(i), 'false_positives': fp, 'misses': fn} for i, (fp, fn) in enumerate(pairs)]


class FrontierTests(unittest.TestCase):
    def test_nondominance_preserves_all_equal_point_cells(self):
        value = frontier(curve([(2, 3), (1, 3), (1, 3), (0, 5), (3, 2), (3, 4)]))
        self.assertEqual([(row['false_positives'], row['misses']) for row in value], [(0, 5), (1, 3), (3, 2)])
        self.assertEqual(value[1]['cell_ids'], ['c1', 'c2'])

    def test_infeasible_budget_is_not_zero_misses(self):
        rows = budget_minima(curve([(2, 1), (4, 0)]), 4)
        self.assertEqual(rows[0], {'false_positive_budget': 0, 'state': 'infeasible', 'minimum_misses': None, 'cell_ids': []})
        self.assertEqual(rows[2]['minimum_misses'], 1)

    def test_budget_ties_include_feasible_dominated_fp_points(self):
        rows = budget_minima(curve([(1, 2), (2, 2), (0, 3)]), 2)
        self.assertEqual(rows[2]['cell_ids'], ['c0', 'c1'])

    def test_exhaustive_two_point_integer_curves(self):
        points = list(itertools.product(range(3), repeat=2)); tested = 0
        second = curve([(0, 3), (1, 1), (2, 0)])
        for first in itertools.product(points, repeat=2):
            values = curve(first); result = compare_curves(values, second, 3)
            check_curves(values, second, 3, result); tested += 1
        self.assertEqual(tested, 81)

    def test_zero_difference_excludes_strict_replacement(self):
        values = curve([(0, 2), (1, 1)]); result = compare_curves(values, values, 1)
        self.assertEqual(result['nominal_pair_grid']['positive_pairs'], 0)
        self.assertEqual(result['nominal_pair_grid']['nonpositive_pairs'], 4)

    def test_pair_limit_does_not_drop_cells(self):
        values = curve([(0, 2), (1, 1)])
        with self.assertRaisesRegex(ValueError, 'pair limit'): compare_curves(values, values, 2, pair_limit=3)

    def test_forged_minimum_and_omitted_tie_rejected(self):
        values = curve([(0, 2), (0, 2)]); result = compare_curves(values, values, 1)
        for mutate in ('minimum', 'tie'):
            bad = deepcopy(result)
            if mutate == 'minimum': bad['false_positive_budgets'][0]['roles'][0]['minimum_misses'] = 0
            else: bad['frontiers'][0][0]['cell_ids'].pop()
            with self.assertRaises(ValueError): check_curves(values, values, 1, bad)

    def test_pair_grid_cell_omission_rejected(self):
        values = curve([(0, 2), (1, 1)]); result = compare_curves(values, values, 1)
        result['nominal_pair_grid']['rows'].pop()
        with self.assertRaisesRegex(ValueError, 'allocation'): check_curves(values, values, 1, result)

    def test_detector_minimum_omission_rejected(self):
        values = curve([(0, 2), (1, 1)]); result = compare_curves(values, values, 1)
        result['retrospective_minimum_unit_losses'].pop()
        with self.assertRaisesRegex(ValueError, 'omitted'): check_curves(values, values, 1, result)


if __name__ == '__main__':
    unittest.main()
