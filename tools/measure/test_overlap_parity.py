"""Tests for the parity with ordinary overlap, and the marginal defect."""
from fractions import Fraction
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import overlap_parity as op  # noqa: E402


class TheIdentityIsDerivedNotAccepted(unittest.TestCase):
    def test_it_holds_on_random_configurations(self):
        self.assertTrue(op.identity_holds())

    def test_the_algebra_matches_a_direct_count(self):
        """c(m) computed from the closed form equals c computed from raw cells."""
        n, k, m, w = 100, 60, 37, 45
        d = n - k
        closed = Fraction((n + m) * (n - 2 * k + w + m), (d + m) ** 2)
        population = n + m
        both = population - (2 * k - w)
        direct = Fraction(both * population, (population - k) * (population - k))
        self.assertEqual(closed, direct)

    def test_the_ordering_is_invariant_to_the_unseen_count(self):
        n, k, w1, w2 = 90, 50, 30, 41
        d = n - k
        for m in (0, 1, 17, 500, 10 ** 6):
            first = Fraction((n + m) * (n - 2 * k + w1 + m), (d + m) ** 2)
            second = Fraction((n + m) * (n - 2 * k + w2 + m), (d + m) ** 2)
            with self.subTest(m=m):
                self.assertEqual(first < second, w1 < w2)

    def test_jaccard_is_strictly_increasing_in_the_intersection(self):
        k = 40
        values = [Fraction(w, 2 * k - w) for w in range(0, k + 1)]
        self.assertEqual(values, sorted(values))


class OrdinaryOverlapReachesTheSameConclusion(unittest.TestCase):
    def test_it_agrees_on_every_available_comparison(self):
        result = op.parity()
        self.assertEqual(result["comparisons"], 270)
        self.assertEqual(result["disagree"], 0)
        self.assertEqual(result["agree"], 270)

    def test_the_report_states_the_coefficient_earns_nothing_here(self):
        self.assertEqual(op.report()["what_the_coefficient_earns_here"],
                         "nothing over ordinary overlap, for the ordering claim")

    def test_where_value_must_be_earned_is_enumerated(self):
        places = op.report()["where_value_must_now_be_earned"]
        self.assertTrue(any("raw detector submissions" in p for p in places))
        self.assertTrue(any("association error" in p for p in places))
        self.assertTrue(any("additive detector loss" in p for p in places))


class TheMarginsWereNeverMatched(unittest.TestCase):
    def test_the_label_free_rows_miss_their_nominal_target(self):
        for entry in op.marginal_audit():
            if entry["view"] == "label_free":
                with self.subTest(target=entry["nominal_target"]):
                    self.assertFalse(entry["matches_its_label"])

    def test_the_annotated_rows_do_match_their_target(self):
        for entry in op.marginal_audit():
            if entry["view"] == "with_annotation":
                with self.subTest(target=entry["nominal_target"]):
                    self.assertTrue(entry["matches_its_label"])

    def test_the_actual_fractions_are_the_reported_ones(self):
        free = [e for e in op.marginal_audit() if e["view"] == "label_free"]
        actual = [round(float(Fraction(e["actual_miss_fraction"][0])), 3) for e in free]
        self.assertEqual(actual, [0.238, 0.299, 0.363])

    def test_the_wider_margin_claim_is_withdrawn(self):
        withdrawn = op.report()["withdrawn"]
        self.assertIn("wider", withdrawn["claim"])
        self.assertIn("never at matched marginals", withdrawn["why"])
        self.assertIn("Engine consumer review", withdrawn["found_by"])

    def test_the_label_free_populations_are_smaller(self):
        for entry in op.marginal_audit():
            if entry["view"] == "label_free":
                self.assertLess(max(entry["population"]), 134565)


class TheAssociationCaveatIsInTheResultSentence(unittest.TestCase):
    def test_it_is_not_only_a_later_limitation(self):
        caveat = op.report()["association_caveat_belongs_in_the_result_sentence"]
        self.assertIn("conditional on that association", caveat)
        self.assertIn("not an end to end annotation free measurement", caveat)

    def test_what_still_stands_credits_overlap_not_the_coefficient(self):
        stands = op.report()["what_still_stands"]
        self.assertIn("not to the coefficient", stands)

    def test_an_undefined_coefficient_is_none(self):
        self.assertIsNone(op.coefficient(
            {"population": 10, "captured_first": 10, "captured_second": 3, "both_missed": 0}))

    def test_an_empty_union_gives_no_jaccard(self):
        self.assertIsNone(op.jaccard({"intersection": 0, "union": 0}))


if __name__ == "__main__":
    unittest.main()
