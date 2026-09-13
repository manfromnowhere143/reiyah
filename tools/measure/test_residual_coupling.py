"""Tests for the residual coupling that survives conditioning on difficulty."""
from fractions import Fraction
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import residual_coupling as rc  # noqa: E402


class TheStratifiedCountsAreConsistent(unittest.TestCase):
    def test_each_stratification_partitions_the_population(self):
        data = rc.load()
        for pair in data["pairs"]:
            for name, entry in pair["strata"].items():
                if "cells" not in entry:
                    continue
                with self.subTest(pair=pair["first"], variable=name):
                    self.assertEqual(sum(c["objects"] for c in entry["cells"]),
                                     pair["population"])

    def test_each_stratification_preserves_the_marginals(self):
        data = rc.load()
        for pair in data["pairs"]:
            for name, entry in pair["strata"].items():
                if "cells" not in entry:
                    continue
                with self.subTest(pair=pair["first"], variable=name):
                    self.assertEqual(sum(c["first_missed"] for c in entry["cells"]),
                                     pair["first_missed"])
                    self.assertEqual(sum(c["both_missed"] for c in entry["cells"]),
                                     pair["both_missed"])

    def test_no_cell_exceeds_its_own_population(self):
        for pair in rc.load()["pairs"]:
            for entry in pair["strata"].values():
                for cell in entry.get("cells", []):
                    with self.subTest(cell=cell["level"]):
                        self.assertLessEqual(cell["both_missed"],
                                             min(cell["first_missed"], cell["second_missed"]))
                        self.assertLessEqual(cell["first_missed"], cell["objects"])

    def test_no_source_identifier_is_retained(self):
        text = open(rc.COUNTS, encoding="utf-8").read()
        for token in ("ann_token", "instance_token", "sample_token"):
            self.assertNotIn(token, text)


class DifficultyDoesNotExplainTheCoupling(unittest.TestCase):
    """The innocent reading is that hard objects are hard for everyone. It is not enough."""

    def test_the_combined_variables_explain_a_majority_but_not_all(self):
        share = rc.report()["explained_by_the_combined_variables"]
        self.assertGreater(Fraction(share["lowest"]), Fraction(1, 2))
        self.assertLess(Fraction(share["highest"]), 1)

    def test_coupling_survives_in_every_pair(self):
        for row in rc.report()["rows"]:
            with self.subTest(pair=row["pair"]):
                self.assertGreater(Fraction(row["within"][rc.COMBINED]), 1)

    def test_two_lidar_pairs_retain_about_twice_the_cross_modality_residue(self):
        residual = rc.report()["after_holding_difficulty_fixed"]
        lidar_low = Fraction(residual["two_lidar"][0])
        cross_high = Fraction(residual["cross_modality"][1])
        self.assertGreater(lidar_low, Fraction(22, 10))
        self.assertLess(cross_high, Fraction(16, 10))
        self.assertGreater(lidar_low / cross_high, Fraction(13, 10))

    def test_the_ordering_survives_conditioning(self):
        self.assertTrue(rc.report()["every_two_lidar_pair_still_above_every_other_pair"])

    def test_scene_condition_explains_nothing(self):
        self.assertTrue(rc.report()["scene_condition_explains_nothing"])


class TheArithmeticIsTheStratifiedComparison(unittest.TestCase):
    def test_within_equals_observed_over_expected_under_conditional_independence(self):
        pair = rc.load()["pairs"][0]
        entry = pair["strata"]["object_class"]
        observed = sum(c["both_missed"] for c in entry["cells"])
        expected = sum(Fraction(c["first_missed"] * c["second_missed"], c["objects"])
                       for c in entry["cells"] if c["objects"])
        self.assertEqual(rc.within(pair, "object_class"), Fraction(observed, 1) / expected)

    def test_a_single_stratum_reproduces_the_marginal(self):
        """Conditioning on a constant must change nothing."""
        pair = rc.load()["pairs"][0]
        pair["strata"]["constant"] = {"levels": 1, "cells": [
            {"level": "all", "objects": pair["population"],
             "first_missed": pair["first_missed"], "second_missed": pair["second_missed"],
             "both_missed": pair["both_missed"]}]}
        self.assertEqual(rc.within(pair, "constant"), rc.marginal(pair))

    def test_the_explained_share_is_zero_when_nothing_is_explained(self):
        pair = rc.load()["pairs"][0]
        pair["strata"]["constant"] = {"levels": 1, "cells": [
            {"level": "all", "objects": pair["population"],
             "first_missed": pair["first_missed"], "second_missed": pair["second_missed"],
             "both_missed": pair["both_missed"]}]}
        self.assertEqual(rc.explained_share(pair, "constant"), 0)

    def test_an_undefined_coefficient_is_none(self):
        self.assertIsNone(rc.marginal(
            {"first_missed": 0, "second_missed": 3, "both_missed": 0, "population": 10}))


class ItDoesNotOverclaim(unittest.TestCase):
    def test_the_report_says_unexplained_is_not_unexplainable(self):
        limits = rc.report()["not_settled"]
        self.assertTrue(any("not unexplainable" in item for item in limits))

    def test_shared_training_data_is_named_as_a_live_candidate(self):
        limits = rc.report()["not_settled"]
        self.assertTrue(any("shared training data" in item for item in limits))

    def test_no_vendor_or_safety_claim_is_made(self):
        limits = rc.report()["not_settled"]
        self.assertTrue(any("no safety conclusion" in item for item in limits))


if __name__ == "__main__":
    unittest.main()
