"""Tests for the annotation inaccessible constructor and its unresolved verdict."""
from fractions import Fraction
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import raw_association as ra  # noqa: E402


class TheInformationBoundaryIsEnforced(unittest.TestCase):
    def test_the_module_names_no_data_file_outside_the_allowlist(self):
        """Every .json literal in the module is either an allowed submission or
        this lane's own retained counts. Prose mentioning annotations is fine;
        naming an annotation FILE is not."""
        source = open(ra.__file__, encoding="utf-8").read()
        literals = set(re.findall(r"[\w.-]+\.json", source))
        permitted = set(ra.INPUT_ALLOWLIST) | {"association-counts.json"}
        self.assertTrue(literals)
        self.assertEqual(literals - permitted, set())

    def test_the_only_file_open_is_guarded_by_the_allowlist(self):
        source = open(ra.__file__, encoding="utf-8").read()
        reader = source[source.index("def read_submission"):source.index("def associate")]
        self.assertIn("if name not in INPUT_ALLOWLIST", reader)
        self.assertLess(reader.index("INPUT_ALLOWLIST"), reader.index("open("))

    def test_a_file_outside_the_allowlist_is_refused(self):
        with self.assertRaises(ra.AssociationError) as caught:
            ra.read_submission("/tmp", "gt_val_cache.json", 0.3)
        self.assertIn("not in the declared input allowlist", str(caught.exception))

    def test_the_excluded_information_is_named(self):
        excluded = ra.report()["information_boundary"]["excluded"]
        self.assertTrue(any("matched_" in item for item in excluded))
        self.assertTrue(any("tuned against annotations" in item for item in excluded))

    def test_the_annotated_population_is_used_only_for_scale(self):
        note = ra.load()["annotated_population_note"]
        self.assertIn("no threshold, no filter and no association", note)


class TheAssociationRuleBehavesAsDeclared(unittest.TestCase):
    def test_same_class_within_radius_joins_one_to_one(self):
        a = {"f": [("car", 0.0, 0.0), ("car", 10.0, 0.0)]}
        b = {"f": [("car", 0.4, 0.0)]}
        self.assertEqual(ra.associate(a, b, 1.0),
                         {"both_channels": 1, "first_only": 1, "second_only": 0})

    def test_a_different_class_never_joins(self):
        a = {"f": [("car", 0.0, 0.0)]}
        b = {"f": [("pedestrian", 0.1, 0.0)]}
        self.assertEqual(ra.associate(a, b, 5.0),
                         {"both_channels": 0, "first_only": 1, "second_only": 1})

    def test_unmatched_detections_stay_visible(self):
        a = {"f": [("car", 0.0, 0.0)]}
        b = {"f": [("car", 50.0, 0.0)]}
        table = ra.associate(a, b, 2.0)
        self.assertEqual(table["first_only"] + table["second_only"], 2)
        self.assertEqual(table["both_channels"], 0)

    def test_one_detection_cannot_serve_two_partners(self):
        a = {"f": [("car", 0.0, 0.0), ("car", 0.2, 0.0)]}
        b = {"f": [("car", 0.1, 0.0)]}
        table = ra.associate(a, b, 1.0)
        self.assertEqual(table["both_channels"], 1)
        self.assertEqual(table["first_only"], 1)

    def test_a_nonpositive_radius_is_refused(self):
        with self.assertRaises(ra.AssociationError):
            ra.associate({}, {}, 0)


class TheRawDataDoesNotSupportASign(unittest.TestCase):
    def test_the_verdict_is_unresolved(self):
        self.assertEqual(ra.report()["verdict"], "unresolved")

    def test_every_row_reports_a_threshold_and_not_a_value(self):
        for row in ra.report()["rows"]:
            with self.subTest(row=(row["score_minimum"], row["association_radius_m"])):
                self.assertEqual(row["state"], "unresolved")
                self.assertIn("m_star", row)
                self.assertNotIn("coefficient", row)

    def test_the_threshold_moves_by_more_than_ten_times(self):
        spread = ra.report()["m_star_spread"]
        self.assertGreater(Fraction(spread["ratio"]), 10)

    def test_one_setting_needs_more_unseen_than_annotated_objects(self):
        report = ra.report()
        self.assertTrue(report["at_least_one_setting_makes_positive_coupling_implausible"])
        flagged = [r for r in report["rows"] if r["would_need_more_unseen_than_annotated"]]
        self.assertEqual(len(flagged), 1)
        self.assertEqual(flagged[0]["association_radius_m"], 1.0)

    def test_the_threshold_matches_x_times_y_over_w(self):
        for row in ra.report()["rows"]:
            expected = Fraction(row["first_only"] * row["second_only"], row["both_channels"])
            with self.subTest(row=row["association_radius_m"]):
                self.assertEqual(Fraction(row["m_star"]), expected)

    def test_no_candidates_leaves_the_threshold_undefined(self):
        self.assertIsNone(ra.sign_threshold(
            {"both_channels": 0, "first_only": 3, "second_only": 4}))


class ItDoesNotOverclaim(unittest.TestCase):
    def test_the_overlap_baseline_is_said_to_share_the_problem(self):
        note = ra.report()["the_overlap_baseline_shares_this"]
        self.assertIn("property of the setting", note)

    def test_a_joined_pair_is_not_called_a_physical_object(self):
        limits = ra.report()["not_established"]
        self.assertTrue(any("candidate under a declared rule" in item for item in limits))

    def test_the_modality_comparison_is_declared_out_of_reach(self):
        limits = ra.report()["not_established"]
        self.assertTrue(any("modality comparison" in item for item in limits))

    def test_the_exposure_state_is_recorded(self):
        note = ra.report()["exposure"]
        self.assertIn("retrospective falsification", note)
        self.assertIn("not", note)


if __name__ == "__main__":
    unittest.main()
