"""Tests for recovering the ordering without the annotation."""
from fractions import Fraction
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import label_free_recovery as lfr  # noqa: E402


class TheLabelFreeViewUsesNoAnnotation(unittest.TestCase):
    def test_its_population_is_the_union_of_what_channels_saw(self):
        data = lfr.load()
        free = [r for r in data["rows"] if r["view"] == "label_free"]
        for row in free:
            with self.subTest(pair=(row["first"], row["second"])):
                self.assertLessEqual(row["population"], data["label_free_population"])

    def test_the_annotated_view_uses_the_larger_annotated_population(self):
        data = lfr.load()
        self.assertGreater(data["annotated_population"], data["label_free_population"])
        for row in data["rows"]:
            if row["view"] == "with_annotation":
                self.assertEqual(row["population"], data["annotated_population"])

    def test_the_joint_miss_cell_differs_between_the_views(self):
        data = lfr.load()
        pairs = {}
        for row in data["rows"]:
            if row["target_miss_rate"] != 0.30:
                continue
            pairs.setdefault((row["first"], row["second"]), {})[row["view"]] = row["both_missed"]
        for pair, views in pairs.items():
            with self.subTest(pair=pair):
                self.assertNotEqual(views["with_annotation"], views["label_free"])

    def test_the_association_limitation_is_stated_in_the_counts(self):
        note = lfr.load()["association_limitation"]
        self.assertIn("does NOT remove it from the association", note)


class ItRecoversTheOrderingWhereTheSignalIsReal(unittest.TestCase):
    def test_two_of_three_operating_points_recover(self):
        report = lfr.report()
        self.assertEqual(report["operating_points_tested"], 3)
        self.assertEqual(report["recovered_by_the_label_free_view"], 2)

    def test_it_recovers_at_the_two_tighter_operating_points(self):
        for row in lfr.report()["rows"]:
            if row["matched_miss_rate"] in (0.30, 0.40):
                with self.subTest(rate=row["matched_miss_rate"]):
                    self.assertTrue(row["label_free"]["separated"])
                    self.assertTrue(row["agrees"])

    def test_where_it_recovers_the_margin_is_wider_than_with_the_annotation(self):
        for row in lfr.report()["rows"]:
            if row["label_free"]["separated"]:
                with self.subTest(rate=row["matched_miss_rate"]):
                    self.assertTrue(row["label_free_margin_is_wider"])

    def test_the_failure_is_where_the_annotated_margin_was_already_thin(self):
        failing = [r for r in lfr.report()["rows"] if not r["label_free"]["separated"]]
        self.assertEqual(len(failing), 1)
        row = failing[0]
        self.assertEqual(row["matched_miss_rate"], 0.50)
        self.assertLess(Fraction(row["with_annotation"]["margin"]), Fraction(1, 100))
        self.assertLess(Fraction(row["label_free"]["margin"]), 0)

    def test_the_verdict_states_two_of_three(self):
        self.assertIn("2 of 3", lfr.report()["verdict"])


class ItRespectsTheEstimandContract(unittest.TestCase):
    def test_comparisons_stay_inside_one_matched_operating_point(self):
        note = lfr.report()["comparisons_are_within_a_matched_point_only"]
        self.assertIn("forbids comparing the coefficient across operating points", note)

    def test_every_row_compares_same_against_cross_at_one_rate(self):
        report = lfr.report()
        rates = [row["matched_miss_rate"] for row in report["rows"]]
        self.assertEqual(len(rates), len(set(rates)))


class ItDoesNotOverclaim(unittest.TestCase):
    def test_association_error_is_named_as_unmeasured(self):
        limits = lfr.report()["what_this_does_not_support"]
        self.assertTrue(any("association error" in item for item in limits))

    def test_only_the_ordering_is_claimed_not_a_magnitude(self):
        limits = lfr.report()["what_this_does_not_support"]
        self.assertTrue(any("only the ordering" in item for item in limits))

    def test_an_undefined_coefficient_is_none(self):
        self.assertIsNone(lfr.coefficient(
            {"first_missed": 0, "second_missed": 2, "both_missed": 0, "population": 9}))

    def test_no_source_identifier_is_retained(self):
        text = open(lfr.COUNTS, encoding="utf-8").read()
        for token in ("ann_token", "instance_token", "sample_token"):
            self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
