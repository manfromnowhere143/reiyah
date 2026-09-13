"""Tests for the review cost of an integration decision."""
from fractions import Fraction
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import review_cost as rc  # noqa: E402


class RankingCannotNarrowFaster(unittest.TestCase):
    """The first product idea, refuted before it was built."""

    def test_each_judgement_narrows_by_the_same_amount(self):
        for r in (1, 5, 20, 139):
            result = rc.ranking_cannot_narrow_faster(r)
            with self.subTest(retained=r):
                self.assertTrue(result["constant_step"])

    def test_the_width_depends_on_how_many_not_on_which(self):
        self.assertEqual(rc.interval_width(10, 3), rc.interval_width(10, 3))
        self.assertEqual(rc.interval_width(10, 0) - rc.interval_width(10, 1), 2)

    def test_asymmetric_penalties_change_the_step_not_the_conclusion(self):
        self.assertEqual(rc.interval_width(10, 0, false_negative=3, false_positive=1), 40)
        self.assertTrue(rc.ranking_cannot_narrow_faster(
            10, false_negative=3, false_positive=1)["constant_step"])

    def test_resolving_everything_closes_the_bound(self):
        self.assertEqual(rc.interval_width(7, 7), 0)

    def test_more_judgements_than_records_is_refused(self):
        with self.assertRaises(rc.CostError):
            rc.interval_width(3, 4)


class TheWorstCaseIsEveryRecord(unittest.TestCase):
    def test_a_single_anchor_costs_its_whole_count(self):
        for r in range(1, 14):
            with self.subTest(retained=r):
                self.assertEqual(rc.worst_case_judgements((r,)), r)

    def test_asymmetric_penalties_do_not_reduce_it(self):
        for a, b in ((1, 2), (2, 1), (1, 3), (5, 1)):
            with self.subTest(penalties=(a, b)):
                self.assertEqual(
                    rc.worst_case_judgements((9,), false_negative=a, false_positive=b), 9)

    def test_several_anchors_cost_their_total(self):
        for anchors in ((3, 4), (2, 2, 2), (1, 6), (5, 5)):
            with self.subTest(anchors=anchors):
                self.assertEqual(rc.worst_case_judgements(anchors), sum(anchors))

    def test_a_zero_penalty_on_false_positives_does_not_reduce_it_either(self):
        """A first draft claimed this was the exception. It is not, and this test caught it.

        With b = 0 the adversary answers not real every time, k stays at zero, and
        the negative side settles only when no records remain.
        """
        for r in (1, 3, 5, 9):
            with self.subTest(retained=r):
                self.assertEqual(
                    rc.worst_case_judgements((r,), false_negative=1, false_positive=0), r)


class TheLiveComparisonCostsSixteen(unittest.TestCase):
    def test_the_worst_case_is_sixteen_judgements(self):
        report = rc.report()
        self.assertEqual(report["anchors"], [9, 7])
        self.assertEqual(report["worst_case_judgements"], 16)
        self.assertTrue(report["equals_the_total"])

    def test_it_does_not_depend_on_how_the_additions_split(self):
        for value in rc.report()["invariant_to_the_anchor_split"].values():
            self.assertEqual(value, 16)

    def test_it_does_not_depend_on_the_weights(self):
        for value in rc.report()["invariant_to_the_weights"].values():
            self.assertEqual(value, 16)

    def test_weights_must_sum_to_one(self):
        with self.assertRaises(rc.CostError) as caught:
            rc.worst_case_judgements((2, 2), weights=[Fraction(1, 3), Fraction(1, 3)])
        self.assertIn("not 1", str(caught.exception))

    def test_a_weight_is_required_for_each_anchor(self):
        with self.assertRaises(rc.CostError):
            rc.worst_case_judgements((2, 2), weights=[Fraction(1)])


class ItRefusesWhatItCannotSolveExactly(unittest.TestCase):
    def test_an_oversized_comparison_is_a_resource_limit_not_a_claim(self):
        with self.assertRaises(rc.CostError) as caught:
            rc.worst_case_judgements((rc.MAX_RECORDS + 1,))
        self.assertIn("not a statement that the cost is unbounded", str(caught.exception))

    def test_no_anchor_is_refused(self):
        with self.assertRaises(rc.CostError):
            rc.worst_case_judgements(())

    def test_negative_counts_are_refused(self):
        with self.assertRaises(rc.CostError):
            rc.worst_case_judgements((-1,))


class ItDoesNotOverclaim(unittest.TestCase):
    def test_the_expected_case_is_explicitly_not_claimed(self):
        limits = rc.report()["not_claimed"]
        self.assertTrue(any("expected case" in item for item in limits))
        self.assertTrue(any("this lane refuses" in item for item in limits))

    def test_the_effort_unit_is_declared_not_measured(self):
        limits = rc.report()["not_claimed"]
        self.assertTrue(any("declared, not measured" in item for item in limits))

    def test_no_physical_object_and_no_loss_value_is_claimed(self):
        limits = rc.report()["not_claimed"]
        self.assertTrue(any("physical objects" in item for item in limits))
        self.assertTrue(any("admitted references" in item for item in limits))


if __name__ == "__main__":
    unittest.main()
