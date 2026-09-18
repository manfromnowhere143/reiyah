from copy import deepcopy
from fractions import Fraction as F
import unittest

from planar_run import bracket_step, case_row, radius_key
from planar_verify import check_bracket, check_case
from planar_search import RADII, prepare, search, w
from test_planar_search import box, image


class PlanarRunControls(unittest.TestCase):
    def simple(self):
        im = image([], [box('b')]); refs = [box('r')]; basis = prepare(im, refs)
        return im, refs, basis, {'id': 'primary', 'group': 'primary', 'images': [im['id']]}

    def bracket_fixture(self):
        im, refs, basis, primary = self.simple(); batches = {}; native_cache = {}
        def evaluate(radius):
            key = radius_key(radius)
            reused = key in batches
            if not reused:
                batches[key] = {im['id']: search(im, refs, basis, radius, native_cache=native_cache)}
            return case_row(primary, batches[key], radius), reused
        for radius in RADII: evaluate(F(radius))
        lower, upper = F(0), F(8); initial = [evaluate(lower)[0], evaluate(upper)[0]]; steps = []
        for index in range(8):
            before = [w(lower), w(upper)]; midpoint = (lower + upper) / 2; row, reused = evaluate(midpoint)
            lower, upper, outcome = bracket_step(lower, upper, row)
            steps.append({'step': index, 'before': before, 'midpoint': w(midpoint), 'reused_radius': reused,
                          'row': row, 'outcome': outcome, 'after': [w(lower), w(upper)]})
            if outcome in ('bound_gap', 'analysis_incomplete'): break
        report = {'initial': [w(F(0)), w(F(8))], 'initial_rows': initial, 'maximum_steps': 8,
                  'steps': steps, 'state': outcome if outcome in ('bound_gap', 'analysis_incomplete') else 'step_limit',
                  'final': [w(lower), w(upper)]}
        return primary, batches, report

    def test_complete_decisions_and_actual_opposite_worlds(self):
        im, refs, basis, case = self.simple()
        for radius, expected in [(0, 'supported'), (6, 'unresolved')]:
            records = {im['id']: search(im, refs, basis, radius)}
            row = case_row(case, records, radius)
            self.assertEqual(row['decision'], expected)
            self.assertEqual(check_case(row, case, records, F(radius)), expected)
            if expected == 'unresolved': self.assertEqual(row['unresolved_reason'], 'opposite_worlds')

    def test_failed_allocated_image_stays_incomplete(self):
        im, refs, basis, case = self.simple(); case['images'].append('failed-image')
        records = {im['id']: search(im, refs, basis, 0), 'failed-image': {'state': 'analysis_incomplete', 'error': 'missing source'}}
        row = case_row(case, records, 0)
        self.assertEqual(row['analysis_failed_images'], ['failed-image']); self.assertIsNone(row['decision'])
        self.assertEqual(check_case(row, case, records, F(0)), 'analysis_incomplete')
        broken = deepcopy(row); broken['decision'] = 'supported'
        with self.assertRaises(ValueError): check_case(broken, case, records, F(0))
        broken = deepcopy(row); broken['analysis_failed_images'] = []
        with self.assertRaises(ValueError): check_case(broken, case, records, F(0))

    def test_bound_gap_is_distinct_from_opposite_worlds(self):
        im = image([box('a', 15, 10, 15, 30)], [box('b')]); refs = [box('r')]
        records = {im['id']: search(im, refs, prepare(im, refs), 10, maximum_regions=1)}
        case = {'id': 'gap', 'group': 'singleton', 'images': [im['id']]}; row = case_row(case, records, 10)
        self.assertEqual(row['unresolved_reason'], 'bound_gap'); check_case(row, case, records, F(10))
        broken = deepcopy(row); broken['unresolved_reason'] = 'opposite_worlds'
        with self.assertRaises(ValueError): check_case(broken, case, records, F(10))

    def test_case_membership_and_world_binding_cannot_be_omitted(self):
        im, refs, basis, case = self.simple(); records = {im['id']: search(im, refs, basis, 0)}
        row = case_row(case, records, 0); row['worlds']['lower'] = []
        with self.assertRaises(ValueError): check_case(row, case, records, F(0))

    def test_eight_step_bracket_reuses_fixed_radius_and_bounds_diagonal_threshold(self):
        primary, batches, report = self.bracket_fixture(); lower, upper = check_bracket(report, primary, batches)
        self.assertTrue(report['steps'][0]['reused_radius']); self.assertEqual(len(report['steps']), 8)
        self.assertLessEqual(upper - lower, F(1, 32)); self.assertTrue(5 < lower < upper < 6)
        # Exact symmetric square condition: (30-r)^2 >= 600 still matches at equality.
        self.assertGreaterEqual((30 - lower) ** 2, 600); self.assertLess((30 - upper) ** 2, 600)

    def test_unsupported_bracket_update_or_false_reuse_rejected(self):
        primary, batches, report = self.bracket_fixture()
        broken = deepcopy(report); broken['steps'][0]['outcome'] = 'attained_excluding_world'
        with self.assertRaises(ValueError): check_bracket(broken, primary, batches)
        broken = deepcopy(report); broken['steps'][0]['reused_radius'] = False
        with self.assertRaises(ValueError): check_bracket(broken, primary, batches)
        broken = deepcopy(report); broken['final'][0] = w(F(8))
        with self.assertRaises(ValueError): check_bracket(broken, primary, batches)

    def test_bracket_gap_does_not_move_an_endpoint(self):
        row = {'radius': w(F(4)), 'state': 'complete', 'universal_bounds': [w(F(-1)), w(F(3))],
               'attained_bounds': [w(F(1)), w(F(3))]}
        self.assertEqual(bracket_step(0, 8, row), (F(0), F(8), 'bound_gap'))
        row['state'] = 'analysis_incomplete'
        self.assertEqual(bracket_step(0, 8, row), (F(0), F(8), 'analysis_incomplete'))

    def test_wrong_midpoint_rejected(self):
        with self.assertRaises(ValueError): bracket_step(0, 8, {'radius': w(F(3)), 'state': 'analysis_incomplete'})


if __name__ == '__main__':
    unittest.main()
