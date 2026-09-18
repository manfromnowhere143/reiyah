"""Exact boundary and admissible-edit controls on synthetic geometry."""
from fractions import Fraction
import random
import unittest

from admission import Rejected
from compare_math import iou, q, validate_canvas, validate_rows
from geometric_worlds import (alter, candidate_rectangles, coordinates, record, search_image,
                              sweep, translation_interval)
from test_compare_math import picture, rectangle


class GeometryControls(unittest.TestCase):
    def test_horizontal_and_vertical_closed_half_iou_boundaries(self):
        base = tuple(map(Fraction, (0, 0, 100, 100)))
        detection = tuple(map(Fraction, (100, 0, 200, 100)))
        bounds = translation_interval(base, detection, 0, 300, 300)
        self.assertEqual(bounds, (Fraction(200, 3), Fraction(400, 3)))
        self.assertEqual(translation_interval((0, 0, 100, 100), (100, 0, 200, 100), 0, 300, 300), bounds)
        for position in bounds:
            shifted = record((position, 0, position + 100, 100))
            self.assertEqual(iou(shifted, record(detection)), Fraction(1, 2))
        self.assertEqual(translation_interval(base, (0, 100, 100, 200), 1, 300, 300), bounds)

    def test_nonoverlap_and_infeasible_shape_have_no_match_interval(self):
        self.assertIsNone(translation_interval((0, 0, 100, 100), (0, 200, 100, 300), 0, 400, 400))
        self.assertIsNone(translation_interval((0, 0, 1, 400), (0, 0, 100, 100), 0, 400, 400))

    def test_sweep_keeps_a_neighborhood_existing_at_only_one_endpoint(self):
        base = tuple(map(Fraction, (0, 0, 90, 90)))
        detections = [tuple(map(Fraction, values)) for values in [(0, 0, 90, 90), (60, 0, 150, 90)]]
        patterns = {tuple(index for index, detection in enumerate(detections)
                          if iou(record(candidate), record(detection)) >= Fraction(1, 2))
                    for candidate in sweep(base, detections, 0, 300, 300)}
        self.assertEqual(patterns, {(), (0,), (1,), (0, 1)})

    def test_interval_formula_matches_8400_rational_position_checks(self):
        randomizer = random.Random(7331)
        checked = 0
        for _ in range(200):
            x, y = randomizer.randrange(200), randomizer.randrange(200)
            width, height = randomizer.randrange(1, 101), randomizer.randrange(25, 101)
            base = tuple(map(Fraction, (x, y, x + width, y + height)))
            x, y = randomizer.randrange(200), randomizer.randrange(200)
            dw, dh = randomizer.randrange(1, 101), randomizer.randrange(25, 101)
            detection = tuple(map(Fraction, (x, y, x + dw, y + dh)))
            for axis in (0, 1):
                extent = base[axis + 2] - base[axis]
                bounds = translation_interval(base, detection, axis, 400, 400)
                for index in range(21):
                    position = (400 - extent) * Fraction(index, 20)
                    candidate = list(base); candidate[axis] = position; candidate[axis + 2] = position + extent
                    actual = iou(record(candidate), record(detection)) >= Fraction(1, 2)
                    predicted = bounds is not None and bounds[0] <= position <= bounds[1]
                    self.assertEqual(actual, predicted); checked += 1
        self.assertEqual(checked, 8400)

    def test_all_constructed_candidates_obey_canvas_and_height(self):
        image = picture([rectangle('edge', 0, 0, 40, 25)], [rectangle('other', 1560, 875, 1600, 900)])
        candidates, _ = candidate_rectangles(image, [])
        for candidate in candidates:
            validate_rows([candidate]); validate_canvas([candidate], image)

    def test_one_edit_operations_are_exact_and_reject_bad_identities(self):
        refs = [rectangle('old')]; inserted = rectangle('new', 100, 0, 200, 100)
        self.assertEqual(alter(refs, {'operation': 'deletion', 'removed_reference': 'old', 'inserted_reference': None}), [])
        self.assertEqual(alter(refs, {'operation': 'replacement', 'removed_reference': 'old', 'inserted_reference': inserted}), [inserted])
        for edit in [
            {'operation': 'insertion', 'removed_reference': 'old', 'inserted_reference': inserted},
            {'operation': 'replacement', 'removed_reference': 'missing', 'inserted_reference': inserted},
            {'operation': 'insertion', 'removed_reference': None, 'inserted_reference': refs[0]}]:
            with self.assertRaises(Rejected):
                alter(refs, edit)

    def test_adverse_displacement_worlds_are_checked_and_reverse_decision(self):
        image = picture([rectangle('a')], [rectangle('b', 100, 0, 200, 100)])
        result = search_image(image, [rectangle('original')])
        self.assertEqual(q(result['witnesses']['lower']['measurement']['delta']), -2)
        self.assertEqual(q(result['witnesses']['upper']['measurement']['delta']), 2)
        self.assertFalse(result['all_rectangles_exhaustively_searched'])
        self.assertTrue(result['axis_cells_exhaustively_searched'])


if __name__ == '__main__':
    unittest.main()
