"""Tests for the claim that survives both objections, and for the two withdrawals."""
from fractions import Fraction
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import modality_coupling as mc  # noqa: E402


class TheMarginalControlIsReal(unittest.TestCase):
    def test_every_channel_reaches_its_declared_miss_rate(self):
        self.assertTrue(mc.marginals_are_matched())

    def test_a_drifted_marginal_is_caught(self):
        data = mc.load()
        data["grid"][0]["realised_miss_rate_first"] = 0.9
        self.assertFalse(mc.marginals_are_matched(data))

    def test_the_two_channels_of_a_pair_are_matched_to_each_other(self):
        for entry in mc.load()["grid"]:
            with self.subTest(pair=(entry["first"], entry["second"])):
                self.assertAlmostEqual(entry["realised_miss_rate_first"],
                                       entry["realised_miss_rate_second"], places=2)


class TheOrderingSurvivesEveryControl(unittest.TestCase):
    def test_nine_controlled_comparisons_are_reported(self):
        self.assertEqual(mc.report()["controlled_comparisons"], 9)

    def test_same_modality_is_strictly_above_cross_in_every_one(self):
        report = mc.report()
        self.assertTrue(report["same_modality_strictly_above_cross_in_all_of_them"])
        for row in report["grid"]:
            with self.subTest(rate=row["matched_miss_rate"], cells=row["cells"]):
                self.assertGreater(Fraction(row["gap"]), 0)

    def test_the_ranges_do_not_overlap(self):
        for row in mc.report()["grid"]:
            with self.subTest(rate=row["matched_miss_rate"], cells=row["cells"]):
                self.assertGreater(Fraction(row["same_modality"][0]),
                                   Fraction(row["cross_modality"][1]))

    def test_every_coupling_stays_above_one(self):
        for row in mc.report()["grid"]:
            with self.subTest(rate=row["matched_miss_rate"]):
                self.assertGreater(Fraction(row["cross_modality"][0]), 1)

    def test_conditioning_shrinks_the_coupling_at_every_matched_rate(self):
        report = mc.report()
        for rate in (0.30, 0.40, 0.50):
            rows = [r for r in report["grid"] if r["matched_miss_rate"] == rate]
            tops = [Fraction(r["same_modality"][1]) for r in rows]
            with self.subTest(rate=rate):
                self.assertEqual(tops, sorted(tops, reverse=True))


class TheTwoWithdrawalsAreRecorded(unittest.TestCase):
    """Both were this lane's own published claims and both are now withdrawn."""

    def test_lidar_dominance_is_withdrawn_as_a_marginal_artifact(self):
        note = mc.report()["withdrawn"]["lidar_pairs_are_always_the_most_coupled"]
        self.assertIn("withdrawn", note)
        self.assertIn("detecting more", note)

    def test_the_residual_magnitude_is_withdrawn_as_unidentified(self):
        note = mc.report()["withdrawn"]["a_residual_of_2_22_to_2_31_after_conditioning"]
        self.assertIn("unidentified", note)
        self.assertIn("stratification", note)

    def test_the_magnitude_is_explicitly_not_claimed(self):
        self.assertEqual(mc.report()["retained"]["magnitude"], "not identified and not claimed")

    def test_at_the_loosest_matched_rate_the_camera_pair_is_not_dominated(self):
        """The concrete reason lidar dominance fell: camera pairs catch up."""
        data = mc.load()
        at_half = [e for e in data["grid"] if e["matched_miss_rate"] == 0.50]
        camera = [mc.coefficient(e, 0) for e in at_half
                  if e["modalities"] == ["camera", "camera"]][0]
        lidar = [mc.coefficient(e, 0) for e in at_half
                 if e["modalities"] == ["lidar", "lidar"]]
        self.assertGreater(camera, min(lidar))


class ItDoesNotOverclaim(unittest.TestCase):
    def test_shared_training_data_is_still_named_as_live(self):
        limits = mc.report()["not_settled"]
        self.assertTrue(any("shared training data" in item for item in limits))

    def test_the_sparse_cell_limit_is_named(self):
        limits = mc.report()["not_settled"]
        self.assertTrue(any("five objects per cell" in item for item in limits))

    def test_no_band_or_safety_claim(self):
        limits = mc.report()["not_settled"]
        self.assertTrue(any("no statistical uncertainty" in item for item in limits))
        self.assertTrue(any("no safety conclusion" in item for item in limits))

    def test_an_undefined_coefficient_is_none(self):
        entry = {"conditioned": {"0": {"observed_joint_miss": 5,
                                       "expected_under_conditional_independence": "0"}}}
        self.assertIsNone(mc.coefficient(entry, 0))

    def test_no_source_identifier_is_retained(self):
        text = open(mc.COUNTS, encoding="utf-8").read()
        for token in ("ann_token", "instance_token", "sample_token"):
            self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
