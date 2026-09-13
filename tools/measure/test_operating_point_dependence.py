"""Tests for the independent recomputation and the operating point extension."""
from fractions import Fraction
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import operating_point_dependence as opd  # noqa: E402


class TheRetainedCountsCarryNoRawData(unittest.TestCase):
    def test_no_source_identifier_is_retained(self):
        text = open(opd.COUNTS, encoding="utf-8").read()
        for token in ("ann_token", "instance_token", "sample_token", "detection_score"):
            self.assertNotIn(token, text)

    def test_only_integer_counts_and_provenance_are_retained(self):
        data = opd.load()
        for row in data["rows"]:
            for key, value in row.items():
                if key in ("first", "second", "kind", "modalities"):
                    continue
                with self.subTest(key=key):
                    self.assertIsInstance(value, (int, float))

    def test_the_source_digests_are_recorded(self):
        provenance = opd.load()["source_provenance"]
        self.assertIn("gt_val_cache.json", provenance["sha256"])
        self.assertEqual(len(provenance["sha256"]), 6)
        for digest in provenance["sha256"].values():
            self.assertEqual(len(digest), 64)


class TheCountsAreInternallyConsistent(unittest.TestCase):
    def test_each_pair_partitions_the_population(self):
        data = opd.load()
        population = data["population"]["objects"]
        for row in data["rows"]:
            if "both_missed" not in row:
                continue
            total = (row["both_captured"] + row["first_only"]
                     + row["second_only"] + row["both_missed"])
            with self.subTest(pair=(row["first"], row["second"], row["threshold"])):
                self.assertEqual(total, population)

    def test_the_marginals_agree_with_the_cells(self):
        data = opd.load()
        for row in data["rows"]:
            if "both_missed" not in row:
                continue
            with self.subTest(pair=(row["first"], row["second"], row["threshold"])):
                self.assertEqual(row["first_missed"], row["second_only"] + row["both_missed"])
                self.assertEqual(row["second_missed"], row["first_only"] + row["both_missed"])

    def test_capture_falls_as_the_threshold_rises(self):
        points = opd.by_operating_point()
        fractions = [p["captured_fraction"] for p in points]
        self.assertEqual(fractions, sorted(fractions, reverse=True))


class TheGateBOrderingIsConfirmedAtTheTop(unittest.TestCase):
    def test_the_most_coupled_pair_is_same_modality_at_every_operating_point(self):
        report = opd.summarise()
        self.assertTrue(
            report["independent_recomputation"]["confirmed"][
                "most_coupled_pair_is_same_modality_everywhere"])

    def test_and_it_is_always_a_lidar_pair(self):
        report = opd.summarise()
        self.assertTrue(
            report["independent_recomputation"]["confirmed"]["and_it_is_always_a_lidar_pair"])

    def test_nine_operating_points_were_examined(self):
        self.assertEqual(opd.summarise()["independent_recomputation"]["operating_points_checked"], 9)


class ThePairwiseReadingIsNotSupported(unittest.TestCase):
    """The stronger claim fails, and the counterexample is named rather than smoothed."""

    def test_no_operating_point_has_every_same_kind_pair_above_every_cross_pair(self):
        report = opd.summarise()
        self.assertFalse(
            report["independent_recomputation"]["qualified"][
                "every_same_modality_pair_beats_every_cross_pair_anywhere"])

    def test_the_two_camera_pair_sits_below_a_cross_pair(self):
        point = opd.by_operating_point()[0]
        camera = [p for p in point["pairs"] if p["modalities"] == ["camera", "camera"]][0]
        cross = max(p["value"] for p in point["pairs"] if p["kind"] == "cross_modality")
        self.assertLess(camera["value"], cross)

    def test_even_lidar_dominance_is_not_pairwise_everywhere(self):
        rows = opd.summarise()["rows"]
        failures = [row for row in rows
                    if not row["ordering"]["every_two_lidar_pair_beats_every_cross_pair"]]
        self.assertTrue(failures)
        worst = failures[0]
        self.assertLess(Fraction(worst["two_lidar"][0]), Fraction(worst["cross_modality"][1]))

    def test_the_report_says_a_pairwise_design_rule_would_be_wrong(self):
        reading = opd.summarise()["independent_recomputation"]["qualified"]["reading"]
        self.assertIn("not pair by pair", reading)


class TheMagnitudeMovesWithTheOperatingPoint(unittest.TestCase):
    def test_the_coefficient_falls_towards_one_as_capture_falls(self):
        rows = opd.summarise()["rows"]
        tops = [Fraction(row["two_lidar"][1]) for row in rows]
        self.assertEqual(tops, sorted(tops, reverse=True))
        self.assertGreater(tops[0], 5)
        self.assertLess(tops[-1], Fraction(11, 10))

    def test_the_sweep_moves_the_most_coupled_pair_by_more_than_five_times(self):
        extension = opd.summarise()["extension"]
        self.assertGreater(Fraction(extension["ratio_across_the_sweep"]), 5)

    def test_the_safety_relevant_reading_is_stated(self):
        why = opd.summarise()["extension"]["why_it_matters"]
        self.assertIn("operating point a system runs", why)
        self.assertIn("validated at", why)


class ItClaimsNothingAboutAnyVendor(unittest.TestCase):
    def test_the_scope_names_the_shared_training_split(self):
        scope = opd.summarise()["scope"]
        self.assertIn("share a training split", scope)
        self.assertIn("Nothing here measures any vendor architecture", scope)

    def test_no_statistical_band_is_claimed(self):
        not_established = opd.summarise()["not_established"]
        self.assertTrue(any("resampling band" in item for item in not_established))
        self.assertTrue(any("safety conclusion" in item for item in not_established))

    def test_an_undefined_coefficient_is_none_not_a_number(self):
        self.assertIsNone(opd.coefficient(
            {"both_missed": 0, "first_missed": 0, "second_missed": 5}, 100))


if __name__ == "__main__":
    unittest.main()
