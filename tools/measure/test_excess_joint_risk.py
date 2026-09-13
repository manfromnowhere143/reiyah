"""Tests for the permitted quantity, the withdrawal, and the two further corrections."""
from fractions import Fraction
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import excess_joint_risk as ejr  # noqa: E402


class TheRatioIsNotComparableAcrossOperatingPoints(unittest.TestCase):
    """Clause 4 of the estimand contract, and the violation it caught."""

    def test_the_withdrawal_names_the_clause_and_the_counterexample(self):
        why = ejr.report()["withdrawn"]["why"]
        self.assertIn("estimand contract", why)
        self.assertIn("CE-4", why)

    def test_the_withdrawal_credits_the_external_review(self):
        self.assertEqual(ejr.report()["withdrawn"]["found_by"],
                         "an external review, not by this lane")

    def test_the_ratio_and_the_burden_move_in_opposite_directions(self):
        """The artifact, shown rather than asserted."""
        rows = ejr.sweep()
        top = max(rows, key=lambda r: Fraction(r["captured_fraction"]))
        peak = max(rows, key=lambda r: Fraction(r["excess_per_thousand"][1]))
        self.assertGreater(Fraction(top["ratio"][1]), Fraction(peak["ratio"][1]))
        self.assertLess(Fraction(top["excess_per_thousand"][1]),
                        Fraction(peak["excess_per_thousand"][1]))


class TheAbsoluteExcessIsWellDefinedEverywhere(unittest.TestCase):
    def test_it_needs_no_nonzero_marginal(self):
        row = {"population": 100, "both_missed": 0, "first_missed": 0, "second_missed": 5}
        self.assertEqual(ejr.excess(row), 0)
        self.assertIsNone(ejr.ratio(row))

    def test_independence_gives_exactly_zero(self):
        row = {"population": 100, "both_missed": 6, "first_missed": 20, "second_missed": 30}
        self.assertEqual(ejr.excess(row), 0)
        self.assertEqual(ejr.ratio(row), 1)

    def test_it_is_exact_rational_arithmetic(self):
        row = {"population": 7, "both_missed": 1, "first_missed": 3, "second_missed": 2}
        self.assertIsInstance(ejr.excess(row), Fraction)
        self.assertEqual(ejr.excess(row), Fraction(1, 7) - Fraction(3, 7) * Fraction(2, 7))

    def test_the_burden_peaks_away_from_the_highest_capture(self):
        report = ejr.report()
        peak = Fraction(report["what_the_absolute_excess_does"]["peak_at_captured_fraction"])
        highest = max(Fraction(r["captured_fraction"]) for r in report["sweep"])
        self.assertLess(peak, highest)


class TheFailureIsDiffuse(unittest.TestCase):
    """The blind spot atlas idea, refuted by this lane's own data."""

    def test_the_worst_five_percent_carries_far_less_than_half(self):
        share = ejr.report()["failure_is_diffuse_not_localised"][
            "worst_five_percent_of_population_carries"]
        self.assertLess(Fraction(share[1]), Fraction(1, 5))

    def test_the_worst_quarter_carries_well_under_three_quarters(self):
        share = ejr.report()["failure_is_diffuse_not_localised"]["worst_quarter_carries"]
        self.assertLess(Fraction(share[1]), Fraction(1, 2))
        self.assertGreater(Fraction(share[0]), Fraction(1, 4))

    def test_the_consequence_is_stated(self):
        note = ejr.report()["failure_is_diffuse_not_localised"]["consequence"]
        self.assertIn("no small region to exclude", note)
        self.assertIn("refuted", note)


class TheNoveltyClaimIsCorrected(unittest.TestCase):
    def test_label_free_assessment_is_not_claimed_as_new(self):
        note = ejr.report()["novelty_corrected"]["not_claimed"]
        self.assertIn("without a reference truth is new", note)

    def test_the_prior_art_is_named_with_venues(self):
        prior = ejr.report()["novelty_corrected"]["prior_art"]
        self.assertTrue(any("IEEE Transactions on Reliability, 2019" in item for item in prior))
        self.assertTrue(any("AISTATS 2015" in item for item in prior))

    def test_the_narrow_claim_is_stated_instead(self):
        narrow = ejr.report()["novelty_corrected"]["what_may_be_narrow_and_new"]
        self.assertIn("Definition 32 constant", narrow)
        self.assertIn("Nothing wider", narrow)


class ItDoesNotOverclaim(unittest.TestCase):
    def test_the_identification_problem_is_left_open(self):
        limits = ejr.report()["not_settled"]
        self.assertTrue(any("open identification problem" in item for item in limits))

    def test_the_architecture_comparison_is_marked_suggestive(self):
        limits = ejr.report()["not_settled"]
        self.assertTrue(any("suggestive, not established" in item for item in limits))

    def test_no_source_identifier_is_retained(self):
        text = open(ejr.COUNTS, encoding="utf-8").read()
        for token in ("ann_token", "instance_token", "sample_token"):
            self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
