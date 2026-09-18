from fractions import Fraction as F
import itertools
import random
import unittest

from axis_cells import edge_interval, partition
from axis_certificate import (checked_radius_membership, exact_iou, expected_cells, maximum_matching,
                              piecewise_interval)


class AxisCertificateControls(unittest.TestCase):
    def test_piecewise_overlap_matches_direct_rational_geometry(self):
        rng = random.Random(1847)
        for _ in range(300):
            x, y, width, height = (F(rng.randint(0, 50), 2), F(rng.randint(0, 20)),
                                   F(rng.randint(1, 60)), F(rng.randint(25, 50)))
            dx, dy, dw, dh = (F(rng.randint(0, 50), 2), F(rng.randint(0, 20)),
                              F(rng.randint(1, 60)), F(rng.randint(25, 50)))
            base = (x, y, x + width, y + height); detection = (dx, dy, dx + dw, dy + dh)
            for axis in [0, 1]:
                interval = piecewise_interval(base, detection, axis, 100, 100)
                self.assertEqual(interval, edge_interval(base, detection, axis, 100, 100))
                cells, _ = expected_cells(base, [detection], axis, 100, 100)
                actual, _ = partition(base, [detection], axis, 100, 100)
                self.assertEqual(cells, [(c.left, c.right) for c in actual])
                for left, right in cells:
                    pos = (left + right) / 2
                    moved = list(base); extent = base[axis + 2] - base[axis]
                    moved[axis] = pos; moved[axis + 2] = pos + extent
                    self.assertEqual(exact_iou(moved, detection) >= F(1, 2),
                                     interval is not None and interval[0] <= pos <= interval[1])

    def test_matching_cardinality_against_every_small_graph(self):
        edges = list(itertools.product(range(3), range(3)))
        for mask in range(1 << len(edges)):
            selected = {edge for i, edge in enumerate(edges) if mask & (1 << i)}
            adjacency = {left: {right for first, right in selected if first == left} for left in range(3)}
            best = 0
            for size in range(1, 4):
                for subset in itertools.combinations(selected, size):
                    if len({left for left, _ in subset}) == len({right for _, right in subset}) == size:
                        best = max(best, size)
            self.assertEqual(maximum_matching(adjacency), best)

    def test_independent_radius_intersection_preserves_open_boundaries(self):
        self.assertFalse(checked_radius_membership(F(10), F(20), F(0), F(10)))
        self.assertTrue(checked_radius_membership(F(10), F(10), F(0), F(10)))
        self.assertTrue(checked_radius_membership(F(10), F(20), F(15), F(0)))
        self.assertFalse(checked_radius_membership(F(10), F(20), F(30), F(10)))
        self.assertTrue(checked_radius_membership(F(10), F(20), F(30), F(1001, 100)))


if __name__ == '__main__':
    unittest.main()
