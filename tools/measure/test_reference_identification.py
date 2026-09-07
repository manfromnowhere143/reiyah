"""Controls for observational equivalence and the explicitly restricted noise model."""
from fractions import Fraction as F
import itertools
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reference_identification_counterexamples as model


class ReferenceIdentificationTests(unittest.TestCase):
    def test_full_observed_law_is_identical_while_true_dependence_differs(self):
        original = model.independent_world()
        data = model.observed(original)
        alternate = model.world_with_reference_flips(data, (F(0),) * 4)
        self.assertEqual(data, model.observed(alternate))
        self.assertEqual(len(data), 8)
        for pattern, mass in data.items():
            self.assertEqual(mass, F(73 if len(set(pattern)) == 1 else 9, 200))
        self.assertEqual(model.coefficient(model.error_cells(original)), 1)
        self.assertEqual(model.coefficient(model.error_cells(alternate)), F(25, 9))

    def test_difference_persists_within_each_true_class(self):
        original = model.independent_world()
        alternate = model.world_with_reference_flips(model.observed(original), (F(0),) * 4)
        for y in (0, 1):
            self.assertEqual(model.coefficient(model.error_cells(original, condition_truth=y)), 1)
            self.assertEqual(model.coefficient(model.error_cells(alternate, condition_truth=y)), F(25, 9))

    def test_extremal_worlds_use_the_declared_budget_and_preserve_all_observables(self):
        result = model.experiment()
        for row in result["reference_error_budget_sensitivity"]:
            for name, endpoint in zip(("lower_world", "upper_world"), row["sharp_interval"]):
                described = row[name]
                self.assertEqual(described["true_coefficient"], endpoint)
                self.assertEqual(described["reference_error_probability"], row["total_reference_error_budget"])
                joint = {tuple(map(int, key)): F(value) for key, value in described["joint_probabilities"].items()}
                self.assertEqual(model.encode(model.observed(joint)), result["complete_observable_probabilities"])

    def test_independent_lattice_of_coupled_net_transfers_stays_in_bounds(self):
        q = (F(9, 100), F(9, 100), F(9, 100), F(73, 100))
        for step in range(10):
            epsilon = F(step, 100)
            lower, upper = model.symmetric_fixture_bounds(epsilon)
            for i, j in itertools.product(range(-2 * step, 2 * step + 1), repeat=2):
                u, v = F(i, 200), F(j, 200)
                if abs(u) + abs(v) > epsilon:
                    continue
                a, b, c, d = q[0] + u, q[1] + v, q[2] - v, q[3] - u
                value = (a / (a + b)) / (a + c)  # total probability is one
                self.assertGreaterEqual(value, lower)
                self.assertLessEqual(value, upper)

    def test_all_deterministic_truth_assignments_with_small_budget_obey_bounds(self):
        observed = model.observed(model.independent_world())
        patterns = sorted(observed)
        checked = 0
        for labels in itertools.product((0, 1), repeat=8):
            epsilon = sum((observed[key] for key, y in zip(patterns, labels) if y != key[2]), F(0))
            if epsilon > F(9, 100):
                continue
            cells = [F(0)] * 4
            for (a, b, _), y, mass in zip(patterns, labels, (observed[p] for p in patterns)):
                index = {(1, 1): 0, (1, 0): 1, (0, 1): 2, (0, 0): 3}[a ^ y, b ^ y]
                cells[index] += mass
            value = cells[0] / ((cells[0] + cells[1]) * (cells[0] + cells[2]))
            lower, upper = model.symmetric_fixture_bounds(epsilon)
            self.assertTrue(lower <= value <= upper)
            checked += 1
        self.assertGreater(checked, 1)

    def test_minimum_total_flip_budget_for_independence_is_eight_percent_here(self):
        self.assertGreater(model.symmetric_fixture_bounds(F(79, 1000))[0], 1)
        self.assertEqual(model.symmetric_fixture_bounds(F(2, 25))[0], 1)
        self.assertLess(model.symmetric_fixture_bounds(F(81, 1000))[0], 1)

    def test_unsupported_error_budget_is_not_silently_coerced(self):
        for bad in (None, 0.08, True, F(-1, 100), F(1, 10)):
            with self.assertRaises(ValueError):
                model.symmetric_fixture_bounds(bad)

    def test_unrecorded_true_opportunities_change_the_target(self):
        pair = model.experiment()["omitted_opportunity_pair"]
        self.assertEqual(pair["world_one"]["true_coefficient"], "1")
        a, b, c, d = map(F, pair["world_two"]["true_cells"])
        self.assertEqual(a * (a + b + c + d) / ((a + b) * (a + c)), F(67, 49))
        self.assertEqual(pair["same_recorded_cells_in_both_worlds"], ["100", "900", "900", "8100"])


if __name__ == "__main__":
    unittest.main()
