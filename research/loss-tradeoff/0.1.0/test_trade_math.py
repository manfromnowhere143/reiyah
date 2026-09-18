from copy import deepcopy
from fractions import Fraction as F
from itertools import product
import unittest

from trade_math import (POLICY, SHARES, bounds, decision, difference, loss, partition,
                        penalty_ratio, transfer, validate_policy)


def matching_sizes(adjacency):
    vertices = sorted(adjacency); found = set()
    def visit(index, occupied, size):
        if index == len(vertices):
            found.add(size); return
        visit(index + 1, occupied, size)
        for right in adjacency[vertices[index]] - occupied:
            visit(index + 1, occupied | {right}, size + 1)
    visit(0, set(), 0)
    return found


class TradeMathControls(unittest.TestCase):
    def test_every_three_by_three_graph_has_maximum_matching_minimum_loss(self):
        edges = list(product(range(3), repeat=2))
        for flags in product((0, 1), repeat=len(edges)):
            adjacency = {left: {right for bit, (a, right) in zip(flags, edges) if bit and a == left} for left in range(3)}
            sizes = matching_sizes(adjacency); maximum = max(sizes)
            for p in SHARES:
                self.assertEqual(loss(3, 3, maximum, p), min(loss(3, 3, size, p) for size in sizes))

    def test_all_small_valid_counts_reference_cardinality_cancels(self):
        for n_a, n_b, refs in product(range(5), repeat=3):
            for m_a, m_b in product(range(min(n_a, refs) + 1), range(min(n_b, refs) + 1)):
                unit = n_a - n_b + 2 * (m_b - m_a)
                for p in SHARES:
                    direct = loss(n_a, refs, m_a, p) - loss(n_b, refs, m_b, p)
                    self.assertEqual(direct, difference(n_a - n_b, m_b - m_a, p))
                    self.assertEqual(direct, transfer(unit, n_a - n_b, p))

    def test_arbitrary_reference_worlds_preserve_extremizer_order(self):
        # Counts change by insertion/deletion; predictions and common penalties do not.
        worlds = [(2, 2, 0), (3, 1, 2), (1, 1, 1), (4, 3, 2)]
        units = [loss(4, t, a, F(1, 2)) * 2 - loss(3, t, b, F(1, 2)) * 2 for t, a, b in worlds]
        low, high = min(units), max(units)
        for p in SHARES:
            direct = [loss(4, t, a, p) - loss(3, t, b, p) for t, a, b in worlds]
            self.assertEqual(bounds((low, high), 1, p), (min(direct), max(direct)))
            self.assertEqual(direct[units.index(low)], min(direct))
            self.assertEqual(direct[units.index(high)], max(direct))

    def test_equal_penalty_scale_and_endpoint_ratios(self):
        self.assertEqual(transfer(F(37, 64), F(7, 16), F(1, 2)), F(37, 128))
        self.assertEqual([penalty_ratio(p) for p in SHARES], [F(0), F(1, 4), F(1, 2), F(1), F(2), F(4), F(8), F(16), None])

    def test_strict_break_even_point_is_excluded(self):
        cells = partition((2, 2), 4); root = next(cell for cell in cells if cell['left'] == cell['right'] == F(3, 4))
        self.assertEqual(root['decision'], 'excluded')
        self.assertEqual(decision(bounds((2, 2), 4, F(3, 4) - F(1, 1000))), 'supported')
        self.assertEqual(decision(bounds((2, 2), 4, F(3, 4) + F(1, 1000))), 'excluded')

    def test_negative_count_difference_reverses_share_direction(self):
        cells = partition((-2, 2), -4)
        self.assertEqual(cells[0]['decision'], 'excluded'); self.assertEqual(cells[-1]['decision'], 'supported')
        at_first = next(cell for cell in cells if cell['point'] and cell['left'] == F(1, 4))
        at_second = next(cell for cell in cells if cell['point'] and cell['left'] == F(3, 4))
        self.assertEqual(at_first['decision'], 'excluded'); self.assertEqual(at_second['decision'], 'unresolved')

    def test_zero_count_difference_and_identically_zero_endpoint(self):
        for interval, expected in [((1, 2), 'supported'), ((-2, 0), 'excluded'), ((0, 2), 'unresolved'), ((0, 0), 'excluded')]:
            cells = partition(interval, 0)
            self.assertEqual(len(cells), 3); self.assertTrue(all(cell['decision'] == expected for cell in cells))

    def test_every_small_interval_partition_covers_domain_and_constant_sign(self):
        for low in range(-5, 6):
            for high in range(low, 6):
                for count in range(-5, 6):
                    cells = partition((low, high), count)
                    self.assertEqual(cells[0]['left'], 0); self.assertEqual(cells[-1]['right'], 1)
                    for first, second in zip(cells, cells[1:]):
                        self.assertEqual(first['right'], second['left']); self.assertNotEqual(first['point'], second['point'])
                    for cell in cells:
                        for numerator in (1, 2, 5, 8, 9):
                            p = cell['left'] + (cell['right'] - cell['left']) * F(numerator, 10)
                            self.assertEqual(decision(bounds((low, high), count, p)), cell['decision'])

    def test_unknown_or_object_dependent_policy_rejected(self):
        validate_policy(deepcopy(POLICY))
        for key, value in [('per_object_weights', {}), ('prediction_sets', 'reference_dependent'), ('domain', ['-1/1', '1/1'])]:
            broken = deepcopy(POLICY); broken[key] = value
            with self.assertRaises(ValueError): validate_policy(broken)

    def test_negative_weights_reversed_bounds_or_invalid_counts_rejected(self):
        for p in (F(-1), F(2)):
            with self.assertRaises(ValueError): transfer(0, 0, p)
        with self.assertRaises(ValueError): bounds((2, -2), 0, F(1, 2))
        with self.assertRaises(ValueError): loss(1, 2, 2, F(1, 2))
        with self.assertRaises(ValueError): loss(True, 2, 1, F(1, 2))


if __name__ == '__main__':
    unittest.main()
