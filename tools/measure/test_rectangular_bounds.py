"""Analytic, degeneracy, algebra-checker and CLI counterexamples for ratio bounds."""
import copy
from fractions import Fraction as F
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rectangular_coincidence_bounds as solver
from check_rectangular_bounds import verify_bound


def independent_ratio(point):
    total = sum(point)
    if total == 0:
        return None
    joint = point[0] / total
    marginal_a = (point[0] + point[1]) / total
    marginal_b = (point[0] + point[2]) / total
    return None if not marginal_a or not marginal_b else joint / marginal_a / marginal_b


class RectangularBoundsTests(unittest.TestCase):
    def test_exact_maximum_between_historical_grid_points(self):
        result = solver.bound_ratio([[0, 11], [1, 1], [1, 1], [1, 1]])
        self.assertEqual(result["supremum"]["supremum_enclosure"], ["9/8", "9/8"])
        self.assertEqual(result["supremum"]["witness"]["cell_masses"], ["3", "1", "1", "1"])
        self.assertEqual(verify_bound(result)["status"], "verified")

    def test_undefined_face_has_a_finite_unattained_supremum(self):
        result = solver.bound_ratio([[0, 1], [0, 0], [10, 10], [90, 90]])
        self.assertTrue(result["undefined_positive_universe_feasible"])
        self.assertEqual(result["infimum"]["value"], "101/11")
        self.assertEqual(result["supremum"]["supremum_enclosure"], ["10", "10"])
        self.assertFalse(result["supremum"]["attained_on_defined_domain"])
        verify_bound(result)

    def test_genuine_divergence_has_a_positive_domain_sequence(self):
        result = solver.bound_ratio([[0, 1], [0, 0], [0, 0], [1, 1]])
        self.assertEqual(result["supremum"]["kind"], "unbounded")
        for k in (1, 10, 100, 10000):
            self.assertEqual(independent_ratio((F(1, k), F(0), F(0), F(1))), 1 + k)
        verify_bound(result)

    def test_defined_zero_coexists_with_undefined_and_empty_cases(self):
        result = solver.bound_ratio([[0, 0], [0, 1], [0, 1], [0, 1]])
        self.assertTrue(result["defined_domain_exists"])
        self.assertTrue(result["undefined_positive_universe_feasible"])
        self.assertTrue(result["empty_universe_feasible"])
        self.assertEqual(result["infimum"]["value"], "0")
        self.assertEqual(result["supremum"]["supremum_enclosure"], ["0", "0"])
        verify_bound(result)

    def test_entirely_undefined_domain_is_not_infinite_or_zero(self):
        result = solver.bound_ratio([[0, 0], [0, 0], [10, 10], [90, 90]])
        self.assertFalse(result["defined_domain_exists"])
        self.assertIsNone(result["infimum"])
        self.assertIsNone(result["supremum"])
        verify_bound(result)

    def test_empty_universe_is_distinct_from_positive_undefined_universe(self):
        result = solver.bound_ratio([[0, 0]] * 4)
        self.assertEqual(result["state"], "empty_universe_only")
        self.assertTrue(result["empty_universe_feasible"])
        self.assertFalse(result["undefined_positive_universe_feasible"])
        verify_bound(result)

    def test_zero_neither_mass_prevents_false_divergence(self):
        result = solver.bound_ratio([[0, 1], [0, 0], [0, 0], [0, 0]])
        self.assertEqual(result["infimum"]["value"], "1")
        self.assertEqual(result["supremum"]["supremum_enclosure"], ["1", "1"])
        self.assertFalse(result["undefined_positive_universe_feasible"])
        verify_bound(result)

    def test_irrational_stationary_point_has_an_algebra_checked_enclosure(self):
        result = solver.bound_ratio([[0, 10], [1, 1], [2, 2], [3, 3]])
        upper = result["supremum"]
        self.assertEqual(upper["witness"]["kind"], "unique_stationary_root")
        self.assertTrue(upper["requested_width_met"])
        self.assertLessEqual(F(upper["enclosure_width"]), F(1, 10**12))
        verify_bound(result)

    def test_exhausted_refinement_budget_preserves_validity_and_reports_precision(self):
        result = solver.bound_ratio([[0, 10], [1, 1], [2, 2], [3, 3]], max_refinements=0)
        self.assertFalse(result["supremum"]["requested_width_met"])
        self.assertEqual(result["supremum"]["refinements"], 0)
        verify_bound(result)

    def test_channel_exchange_and_mass_scaling_preserve_bounds(self):
        box = [[F(0), F(10)], [F(1), F(3)], [F(2), F(4)], [F(1), F(3)]]
        original = solver.bound_ratio(box)
        for transformed in ([box[0], box[2], box[1], box[3]], [[v * F(7, 3) for v in pair] for pair in box]):
            changed = solver.bound_ratio(transformed)
            self.assertEqual(changed["infimum"]["value"], original["infimum"]["value"])
            self.assertEqual(changed["supremum"]["supremum_enclosure"], original["supremum"]["supremum_enclosure"])
            verify_bound(changed)

    def test_checker_rejects_grid_value_presented_as_a_global_upper_bound(self):
        result = solver.bound_ratio([[0, 11], [1, 1], [1, 1], [1, 1]])
        result["supremum"].update(supremum_enclosure=["253/225", "253/225"], witness={
            "kind": "defined_point", "cell_masses": ["11/4", "1", "1", "1"], "coefficient": "253/225"})
        with self.assertRaisesRegex(ValueError, "upper bound excludes"):
            verify_bound(result)

    def test_checker_rejects_feasible_point_presented_as_global_infimum(self):
        result = solver.bound_ratio([[0, 11], [1, 1], [1, 1], [1, 1]])
        result["infimum"].update(value="1", witness={
            "kind": "defined_point", "cell_masses": ["1", "1", "1", "1"], "coefficient": "1"})
        with self.assertRaisesRegex(ValueError, "lower bound exceeds"):
            verify_bound(result)

    def test_checker_rejects_changed_stationary_polynomial(self):
        result = solver.bound_ratio([[0, 10], [1, 1], [2, 2], [3, 3]])
        result["supremum"]["witness"]["derivative_polynomial_coefficients"][0] = "-2"
        with self.assertRaisesRegex(ValueError, "wrong stationary polynomial"):
            verify_bound(result)

    def test_checker_rejects_unbounded_exponential_literal_before_arithmetic(self):
        result = solver.bound_ratio([[0, 11], [1, 1], [1, 1], [1, 1]])
        result["infimum"]["value"] = "1e999999999999999999999999"
        with self.assertRaisesRegex(ValueError, "bounded exact rational"):
            verify_bound(result)

    def test_checker_rejects_false_infinity_for_an_undefined_face(self):
        result = solver.bound_ratio([[0, 1], [0, 0], [10, 10], [90, 90]])
        result["supremum"] = copy.deepcopy(solver.bound_ratio([[0, 1], [0, 0], [0, 0], [1, 1]])["supremum"])
        with self.assertRaisesRegex(ValueError, "undefined does not imply"):
            verify_bound(result)

    def test_checker_rejects_finite_claim_on_a_diverging_domain(self):
        result = solver.bound_ratio([[0, 1], [0, 0], [0, 0], [1, 1]])
        result["supremum"] = copy.deepcopy(solver.bound_ratio([[0, 1], [0, 0], [10, 10], [90, 90]])["supremum"])
        with self.assertRaisesRegex(ValueError, "finite bound on an unbounded"):
            verify_bound(result)

    def test_checker_rejects_false_precision_and_boolean_coercion(self):
        result = solver.bound_ratio([[0, 10], [1, 1], [2, 2], [3, 3]], max_refinements=0)
        result["supremum"]["requested_width_met"] = True
        with self.assertRaisesRegex(ValueError, "precision"):
            verify_bound(result)
        result = solver.bound_ratio([[0, 1], [1, 1], [1, 1], [1, 1]])
        result["defined_domain_exists"] = 1
        with self.assertRaisesRegex(ValueError, "feasibility"):
            verify_bound(result)

    def test_checker_rejects_unattained_limit_as_a_defined_point(self):
        result = solver.bound_ratio([[0, 1], [0, 0], [10, 10], [90, 90]])
        result["supremum"]["attained_on_defined_domain"] = True
        with self.assertRaisesRegex(ValueError, "unattained limit"):
            verify_bound(result)

    def test_missing_float_negative_and_reversed_constraints_are_rejected(self):
        for bad in ([[None, 1], [1, 1], [1, 1], [1, 1]], [[0.0, 1], [1, 1], [1, 1], [1, 1]],
                    [[-1, 1], [1, 1], [1, 1], [1, 1]], [[2, 1], [1, 1], [1, 1], [1, 1]]):
            with self.assertRaises(ValueError):
                solver.bound_ratio(bad)

    def test_finite_lattice_and_independent_quadratic_checks(self):
        intervals = [(F(low), F(high)) for low in range(3) for high in range(low, 3)]
        for box in itertools.product(intervals, repeat=4):
            result = solver.bound_ratio(box, tolerance=F(1, 10**8))
            verify_bound(result)
            values = []
            for point in itertools.product(*[sorted({lo, hi, (lo + hi) / 2}) for lo, hi in box]):
                value = independent_ratio(point)
                if value is not None:
                    values.append(value)
            self.assertEqual(bool(values), result["defined_domain_exists"])
            if not values:
                continue
            self.assertLessEqual(F(result["infimum"]["value"]), min(values))
            if result["supremum"]["kind"] == "finite":
                self.assertGreaterEqual(F(result["supremum"]["supremum_enclosure"][1]), max(values))

    def test_actual_cli_and_independent_checker_reject_tampered_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = {"schema_version": "reiyah.rectangular-coincidence-input.v1", "artifact_id": "test.rectangle",
                        "box": [["0", "11"], ["1", "1"], ["1", "1"], ["1", "1"]],
                        "tolerance": "1/1000000000000", "max_refinements": 256}
            source, report = root / "input.json", root / "report.json"
            source.write_text(json.dumps(original))
            produced = subprocess.run([sys.executable, "-B", solver.__file__, str(source)], capture_output=True)
            self.assertEqual(produced.returncode, 0, produced.stderr)
            report.write_bytes(produced.stdout)
            checker = Path(solver.__file__).with_name("check_rectangular_bounds.py")
            checked = subprocess.run([sys.executable, "-B", str(checker), str(source), str(report)], capture_output=True)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            forged = json.loads(produced.stdout)
            forged["result"]["supremum"]["supremum_enclosure"] = ["1", "1"]
            report.write_text(json.dumps(forged))
            rejected = subprocess.run([sys.executable, "-B", str(checker), str(source), str(report)], capture_output=True)
            self.assertEqual(rejected.returncode, 2)
            self.assertEqual(rejected.stdout, b"")
            self.assertEqual(json.loads(rejected.stderr)["status"], "invalid")


if __name__ == "__main__":
    unittest.main()
