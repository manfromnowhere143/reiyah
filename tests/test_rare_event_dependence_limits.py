"""Exact small-population controls for the synthetic feasibility derivation."""

from fractions import Fraction as F
from copy import deepcopy
from itertools import product
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "measure"))
from rare_event_dependence_limits import (
    build_report, coincidence, iid_test_power_bound, law, log_enclosure,
    mixture_report, total_variation, zero_event_sample_requirement,
)
from check_rare_event_limits import check_report


class RareEventLimitsTests(unittest.TestCase):
    def test_rare_full_laws_keep_marginals_and_change_only_dependence(self):
        p = F(1, 100000)
        rows = [law(p, p, c * p * p) for c in (1, 2)]
        for c, (a, b, d, e) in zip((1, 2), rows):
            self.assertEqual(a + b, p)
            self.assertEqual(a + d, p)
            self.assertEqual(a + b + d + e, 1)
            self.assertEqual(coincidence((a, b, d, e)), c)
        self.assertEqual(total_variation(*rows), F(1, 5000000000))
        self.assertEqual(iid_test_power_bound(*rows, 100000, F(1, 20)), F(2501, 50000))

    def test_product_law_bound_by_direct_enumeration(self):
        # No product-TV function from the producer is used in this enumeration.
        for p in (F(1, 10), F(1, 4), F(1, 2)):
            first, second = law(p, p, p * p), law(p, p, 2 * p * p)
            single = total_variation(first, second)
            for n in range(1, 5):
                distance = F(0)
                for sequence in product(range(4), repeat=n):
                    left = right = F(1)
                    for state in sequence:
                        left *= first[state]
                        right *= second[state]
                    distance += abs(left - right) / 2
                self.assertLessEqual(distance, min(1, n * single))

    def test_zero_event_integer_bound_against_exact_small_powers(self):
        for q in (F(1, 2), F(1, 5), F(1, 10), F(1, 100)):
            for alpha in (F(1, 20), F(1, 10), F(1, 3)):
                r = zero_event_sample_requirement(q, alpha)
                n = r["n"]
                self.assertLessEqual((1 - q) ** n, alpha)
                self.assertGreater((1 - q) ** (n - 1), alpha)

    def test_published_large_integer_requirements(self):
        report = build_report()
        self.assertEqual([r["n"] for r in report["zero_event_rules"]],
                         [299572, 29957322735, 14978661367])
        self.assertEqual(report["rare_pair"]["necessary_n_from_tv_union_bound"], 4500000000)
        self.assertIsNone(report["safety_validation_budget"])
        self.assertIsNone(report["observed_physical_performance"])

    def test_exact_integer_log_boundary(self):
        for q, alpha, expected in [(F(1, 2), F(1, 4), 2),
                                    (F(1, 10), F(9, 10) ** 17, 17),
                                    (F(9, 10), F(1, 10), 1)]:
            r = zero_event_sample_requirement(q, alpha)
            self.assertEqual(r["n"], expected)
            self.assertEqual(r["method"], "exact_rational_power_boundary_resolution")

    def test_mixing_both_directions(self):
        rows = build_report()["mixture_controls"]
        first, second = rows.values()
        self.assertEqual(first["stratum_c"], ["1", "1"])
        self.assertEqual(first["conditional_aggregate_c"], "1")
        self.assertEqual(first["mixture_c"], "202/121")
        self.assertEqual(second["stratum_c"], ["8/5", "2/5"])
        self.assertEqual(second["mixture_c"], "1")

    def test_undefined_is_not_independence(self):
        row = law(0, F(1, 10), 0)
        self.assertIsNone(coincidence(row))
        r = mixture_report([1], [row])
        self.assertIsNone(r["mixture_c"])
        self.assertIsNone(r["conditional_aggregate_c"])

    def test_log_enclosures_refine_and_preserve_sign(self):
        for x in (F(1, 20), F(1), F(5, 4), F(2), F(20)):
            coarse = log_enclosure(x, 8)
            fine = log_enclosure(x, 16)
            self.assertLessEqual(coarse[0], fine[0])
            self.assertLessEqual(fine[0], fine[1])
            self.assertLessEqual(fine[1], coarse[1])
            reciprocal = log_enclosure(1 / x, 16)
            self.assertEqual(reciprocal, (-fine[1], -fine[0]))

    def test_reject_infeasible_and_coerced_inputs(self):
        for args in [(F(1, 10), F(1, 10), F(1, 5)), (True, 0, 0), (.1, .1, 0)]:
            with self.assertRaises(ValueError):
                law(*args)
        for args in [(0, F(1, 20)), (1, F(1, 20)), (F(1, 10), 0)]:
            with self.assertRaises(ValueError):
                zero_event_sample_requirement(*args)
        with self.assertRaises(ValueError):
            mixture_report([F(1, 2)], [law(0, 0, 0)])
        with self.assertRaises(ValueError):
            iid_test_power_bound(law(0, 0, 0), law(0, 0, 0), True, F(1, 20))

    def test_separate_numeric_checker(self):
        checked = check_report(build_report())
        self.assertEqual(checked["status"], "pass")
        self.assertEqual(len(checked["numeric_checks"]), 6)

    def test_separate_checker_rejects_forged_conclusions(self):
        report = build_report()
        forged = deepcopy(report)
        forged["rare_pair"]["any_test_power_upper_bound"] = "19/20"
        with self.assertRaises(ValueError):
            check_report(forged)
        forged = deepcopy(report)
        forged["zero_event_rules"][1]["n"] -= 1
        with self.assertRaises(ValueError):
            check_report(forged)
        forged = deepcopy(report)
        forged["observed_physical_performance"] = 0
        with self.assertRaises(ValueError):
            check_report(forged)
        forged = deepcopy(report)
        next(iter(forged["mixture_controls"].values()))["stratum_c"][0] = "100"
        with self.assertRaises(ValueError):
            check_report(forged)


if __name__ == "__main__":
    unittest.main()
