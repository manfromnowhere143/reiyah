from fractions import Fraction as F
from itertools import product
from pathlib import Path
import random
import sys
import unittest

from planar_math import domain, edge_envelope, increment_pairs, overlap_range, points, rank_enclosure, split

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'research/reference-translation/0.1.0'))
from axis_certificate import exact_iou, maximum_matching


def subsets(values):
    values = list(values)
    return [{value for index, value in enumerate(values) if mask & (1 << index)} for mask in range(1 << len(values))]


class PlanarMathControls(unittest.TestCase):
    def test_joint_shared_neighbors_remove_false_independent_rank_pairs(self):
        self.assertEqual(increment_pairs(set(), {'x'}, {'x'}, {'x'}), [(0, 0), (1, 1)])
        self.assertEqual(rank_enclosure(3, set(), {'x'}, {'x'}, {'x'})[0], (3, 3))
        self.assertEqual(increment_pairs({'x'}, {'x'}, {'x'}, {'x'}), [(1, 1)])
        self.assertNotIn((1, 0), increment_pairs(set(), {'x', 'y'}, {'x'}, {'x', 'y'}))

    def test_every_three_neighbor_interval_and_augmentable_pair(self):
        universe = {0, 1, 2}; choices = subsets(universe); checked = 0
        for modes in product(range(3), repeat=3):
            must = {i for i, mode in enumerate(modes) if mode == 2}
            may = {i for i, mode in enumerate(modes) if mode != 0}
            for aa, bb in product(choices, repeat=2):
                actual = {(int(bool(n & aa)), int(bool(n & bb))) for n in choices if must <= n <= may}
                self.assertEqual(set(increment_pairs(must, may, aa, bb)), actual); checked += 1
        self.assertEqual(checked, 1728)

    def test_augmentable_single_neighbors_characterize_every_small_graph(self):
        edges = list(product(range(3), range(3))); neighbors = subsets(range(3))
        for mask in range(1 << len(edges)):
            adjacency = {left: {right for i, (first, right) in enumerate(edges) if first == left and mask & (1 << i)}
                         for left in range(3)}
            base = maximum_matching(adjacency)
            augmented = {left for left in adjacency if maximum_matching(
                {key: values | ({3} if key == left else set()) for key, values in adjacency.items()}) == base + 1}
            for neighborhood in neighbors:
                rank = maximum_matching({left: values | ({3} if left in neighborhood else set()) for left, values in adjacency.items()})
                self.assertEqual(rank - base, int(bool(neighborhood & augmented)))

    def test_exact_threshold_and_true_two_coordinate_displacement(self):
        box = (F(10), F(10), F(40), F(40))
        only_x = edge_envelope(box, box, (0, 10, 20, 10))
        both = edge_envelope(box, box, (0, 0, 20, 20))
        self.assertTrue(only_x['must'])
        self.assertFalse(both['must']); self.assertTrue(both['may'])
        self.assertEqual(only_x['minimum_intersection'], 600)
        self.assertEqual(both['minimum_intersection'], 400)
        self.assertLess(exact_iou((20, 20, 50, 50), box), F(1, 2))

    def test_overlap_envelope_contains_independent_rational_grid(self):
        rng = random.Random(1931)
        for _ in range(100):
            base = (F(20), F(20), F(50), F(60)); radius = F(rng.randint(0, 20), 2)
            x, y, width, height = [rng.randint(a, b) for a, b in [(0, 60), (0, 60), (5, 35), (25, 40)]]
            detection = tuple(map(F, (x, y, x + width, y + height))); region = domain(base, radius, 100, 100)
            envelope = edge_envelope(base, detection, region)
            for px, py in product(range(5), repeat=2):
                tx = region[0] + (region[2] - region[0]) * F(px, 4)
                ty = region[1] + (region[3] - region[1]) * F(py, 4)
                iou = exact_iou((tx, ty, tx + 30, ty + 40), detection)
                if envelope['must']:
                    self.assertGreaterEqual(iou, F(1, 2))
                if not envelope['may']:
                    self.assertLess(iou, F(1, 2))

    def test_image_boundary_and_closed_split_coverage(self):
        root = domain((0, 0, 30, 30), 8, 100, 100)
        self.assertEqual(root, (0, 0, 8, 8))
        axis, first, second = split(root)
        self.assertEqual(axis, 0); self.assertEqual(first, (0, 0, 4, 8)); self.assertEqual(second, (4, 0, 8, 8))
        for x, y in product(range(17), repeat=2):
            point = (F(x, 2), F(y, 2))
            self.assertTrue(any(r[0] <= point[0] <= r[2] and r[1] <= point[1] <= r[3] for r in (first, second)))
        self.assertEqual(points(domain((10, 10, 40, 40), 0, 100, 100)), [(10, 10)])

    def test_invalid_domains_and_neighbor_intervals_rejected(self):
        for radius in [-1]:
            with self.assertRaises(ValueError): domain((0, 0, 30, 30), radius, 100, 100)
        with self.assertRaises(ValueError): increment_pairs({'absent'}, set(), set(), set())
        with self.assertRaises(ValueError): overlap_range(2, 1, 10, 0, 10)
        with self.assertRaises(ValueError): split((0, 0, 0, 0))


if __name__ == '__main__':
    unittest.main()
