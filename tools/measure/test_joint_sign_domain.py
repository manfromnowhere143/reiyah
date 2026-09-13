"""Tests for the corrected sign classification and the two retained counterexamples."""
from fractions import Fraction
import itertools
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import joint_sign_domain as jsd  # noqa: E402


class TheIdentityIsDerivedAndChecked(unittest.TestCase):
    def test_it_holds_on_random_configurations(self):
        rng = random.Random(11)
        for _ in range(4000):
            w, x, y, u = (rng.randint(0, 12) for _ in range(4))
            m = rng.randint(0, 40)
            value = jsd.coefficient(w, x, y, u, m)
            if value is None:
                continue
            with self.subTest(counts=(w, x, y, u, m)):
                self.assertEqual(value - 1, Fraction(jsd.excess_numerator(w, x, y, u, m),
                                                     jsd.denominator(x, y, u, m)))

    def test_the_denominator_vanishes_only_at_zero_with_an_empty_margin(self):
        self.assertEqual(jsd.denominator(0, 4, 0, 0), 0)
        self.assertGreater(jsd.denominator(0, 4, 0, 1), 0)
        self.assertGreater(jsd.denominator(0, 4, 1, 0), 0)


class AThirdChannelIsNotAnIdentificationCondition(unittest.TestCase):
    """Retained counterexample to this lane's own withdrawn consumer request."""

    def test_opposite_signs_remain_possible_with_a_third_channel_reporting(self):
        counts = dict(w=1, x=2, y=2, u=1)
        self.assertGreater(counts["u"], 0)
        self.assertLess(jsd.coefficient(**counts, m=0), 1)
        self.assertGreater(jsd.coefficient(**counts, m=4), 1)
        self.assertEqual(jsd.classify(**counts)["state"], "unresolved")

    def test_the_sufficient_condition_is_the_product_inequality(self):
        self.assertEqual(jsd.classify(w=5, x=1, y=1, u=1)["state"],
                         "above_one_for_every_unseen_count")
        self.assertGreater(5 * 1, 1 * 1)

    def test_the_counterexample_is_exported(self):
        retained = jsd.a_third_channel_is_not_sufficient()
        self.assertEqual(retained["c_at_zero"], "2/3")
        self.assertEqual(retained["c_at_four"], "50/49")
        self.assertIn("w * u > x * y", retained["reading"])


class AnUndefinedThresholdIsNotAnUndeterminedSign(unittest.TestCase):
    """Retained counterexample to this lane's own conflated state."""

    def test_the_sign_is_determined_where_the_threshold_is_not(self):
        counts = dict(w=0, x=1, y=1, u=0)
        self.assertIsNone(jsd.sign_threshold(**counts))
        self.assertEqual(jsd.classify(**counts)["state"], "below_one_for_every_unseen_count")
        for m in (0, 1, 5, 100, 10 ** 5):
            self.assertLess(jsd.coefficient(**counts, m=m), 1)

    def test_a_zero_numerator_gives_exactly_one_everywhere(self):
        counts = dict(w=0, x=0, y=3, u=2)
        self.assertEqual(jsd.classify(**counts)["state"], "equal_to_one_for_every_unseen_count")
        for m in (0, 3, 50):
            self.assertEqual(jsd.coefficient(**counts, m=m), 1)

    def test_an_empty_margin_at_zero_is_an_invalid_domain_not_a_sign(self):
        self.assertEqual(jsd.classify(w=3, x=0, y=4, u=0)["state"], "invalid_domain")
        self.assertIsNone(jsd.coefficient(w=3, x=0, y=4, u=0, m=0))


class TheThresholdFormulaIsCorrected(unittest.TestCase):
    def test_it_subtracts_the_third_channel_term(self):
        self.assertEqual(jsd.sign_threshold(w=2, x=3, y=4, u=1), Fraction(12 - 2, 2))

    def test_it_reduces_to_the_old_form_only_when_u_is_zero(self):
        self.assertEqual(jsd.sign_threshold(w=2, x=3, y=4, u=0), Fraction(12, 2))
        self.assertNotEqual(jsd.sign_threshold(w=2, x=3, y=4, u=1), Fraction(12, 2))

    def test_the_threshold_really_separates_the_sign(self):
        for w, x, y, u in ((2, 3, 4, 1), (1, 5, 5, 2), (3, 7, 2, 0)):
            threshold = jsd.sign_threshold(w, x, y, u)
            for m in range(0, 40):
                value = jsd.coefficient(w, x, y, u, m)
                if value is None:
                    continue
                with self.subTest(counts=(w, x, y, u), m=m):
                    self.assertEqual(value > 1, Fraction(m) > threshold)


class TheClassificationIsExhaustivelyConsistent(unittest.TestCase):
    def test_every_small_table_agrees_with_direct_evaluation(self):
        checked = 0
        for w, x, y, u in itertools.product(range(0, 6), repeat=4):
            state = jsd.classify(w, x, y, u)["state"]
            values = [jsd.coefficient(w, x, y, u, m) for m in range(0, 50)]
            values = [v for v in values if v is not None]
            checked += 1
            with self.subTest(counts=(w, x, y, u)):
                if state == "above_one_for_every_unseen_count":
                    self.assertTrue(all(v > 1 for v in values))
                elif state == "below_one_for_every_unseen_count":
                    self.assertTrue(all(v < 1 for v in values))
                elif state == "equal_to_one_for_every_unseen_count":
                    self.assertTrue(all(v == 1 for v in values))
                elif state == "one_at_zero_then_above":
                    self.assertEqual(values[0], 1)
                    self.assertTrue(all(v > 1 for v in values[1:]))
                elif state == "unresolved":
                    self.assertTrue(any(v <= 1 for v in values))
        self.assertEqual(checked, 6 ** 4)

    def test_negative_and_boolean_counts_are_refused(self):
        for bad in ((-1, 1, 1, 1), (1, True, 1, 1)):
            with self.subTest(counts=bad):
                with self.assertRaises(jsd.DomainError):
                    jsd.classify(*bad)


if __name__ == "__main__":
    unittest.main()
