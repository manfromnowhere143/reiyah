from fractions import Fraction as F
import itertools
import unittest

from axis_cells import Cell, edge_interval, minimum_radius, partition, reachable, translate


def iou(a, b):
    inter = max(F(0), min(a[2], b[2]) - max(a[0], b[0])) * max(F(0), min(a[3], b[3]) - max(a[1], b[1]))
    return inter / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter)


class AxisCellControls(unittest.TestCase):
    def test_boundary_included_open_loss_not_attained(self):
        base = (F(10), F(0), F(40), F(30))
        self.assertEqual(edge_interval(base, base, 0, 100, 100), (0, 20))
        cells, _ = partition(base, [base], 0, 100, 100)
        point = next(c for c in cells if c.point and c.left == 20)
        beyond = next(c for c in cells if not c.point and c.left == 20)
        self.assertEqual(iou(translate(base, 0, 20), base), F(1, 2))
        self.assertEqual(minimum_radius(point, 10), (10, True))
        self.assertEqual(minimum_radius(beyond, 10), (10, False))
        self.assertIsNone(reachable(beyond, 10, 10))
        position = reachable(beyond, 10, F(10001, 1000))
        self.assertGreater(position, 20)
        self.assertLess(iou(translate(base, 0, position), base), F(1, 2))

    def test_zero_radius_inside_open_cell_is_reachable(self):
        self.assertEqual(reachable(Cell(F(0), F(10)), 5, 0), 5)
        self.assertEqual(minimum_radius(Cell(F(0), F(10)), 5), (0, True))
        self.assertIsInstance(Cell(0, 1).representative(), F)

    def test_canvas_and_no_movement_axis(self):
        base = (F(0), F(10), F(100), F(40))
        cells, _ = partition(base, [base], 0, 100, 100)
        self.assertEqual(cells, [Cell(F(0), F(0))])
        self.assertEqual(reachable(cells[0], 0, 64), 0)
        self.assertEqual(edge_interval((0, 0, 30, 30), (0, 70, 30, 100), 0, 100, 100), None)

    def test_exhaustive_rational_positions_and_cell_constancy(self):
        checked = 0
        for x, width, other_x, other_width, axis in itertools.product([0, 7, 60], [9, 21, 36], [0, 11, 60], [9, 21, 34], [0, 1]):
            base = tuple(map(F, (x, 3, x + width, 33)))
            detection = tuple(map(F, (other_x, 0, other_x + other_width, 30)))
            cells, intervals = partition(base, [detection], axis, 100, 100)
            interval = intervals[0]
            for cell in cells:
                positions = [cell.left] if cell.point else [(cell.left * n + cell.right) / (n + 1) for n in [1, 2, 7]]
                values = []
                for position in positions:
                    actual = iou(translate(base, axis, position), detection) >= F(1, 2)
                    expected = interval is not None and interval[0] <= position <= interval[1]
                    self.assertEqual(actual, expected); values.append(actual); checked += 1
                    self.assertTrue(cell.contains(position))
                self.assertEqual(len(set(values)), 1)
        self.assertGreater(checked, 700)

    def test_closed_radius_band_at_open_cell_edge(self):
        cell = Cell(F(10), F(20))
        self.assertIsNone(reachable(cell, 0, 10))
        self.assertEqual(reachable(cell, 0, 12), 11)
        self.assertEqual(minimum_radius(cell, 30), (10, False))
        self.assertIsNone(reachable(cell, 30, 10))
        self.assertEqual(reachable(cell, 30, 12), 19)

    def test_invalid_geometry_and_negative_radius_rejected(self):
        with self.assertRaises(ValueError):
            partition((-1, 0, 30, 30), [], 0, 100, 100)
        with self.assertRaises(ValueError):
            edge_interval((0, 0, 0, 30), (0, 0, 30, 30), 0, 100, 100)
        with self.assertRaises(ValueError):
            reachable(Cell(F(0), F(1)), 0, -1)


if __name__ == '__main__':
    unittest.main()
