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

    def test_the_annotated_count_is_labelled_scale_only(self):
        note = ra.load()["scale_note"]
        self.assertIn("not a bound on unseen physical opportunities", note)
        self.assertIn("different units", note)


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
        sensitivity = ra.report()["sensitivity_is_dominated_by_the_radius"]
        self.assertGreater(Fraction(sensitivity["threshold_span_across_preparations"]), 10)

    def test_no_row_claims_implausibility_from_the_annotation_count(self):
        """Version 0.1.0 called one setting implausible on this basis. Withdrawn."""
        for row in ra.report()["rows"]:
            with self.subTest(radius=row["association_radius_m"], rule=row["rule"]):
                self.assertNotIn("would_need_more_unseen_than_annotated", row)

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


class TheBoundaryIsBytesNotBasenames(unittest.TestCase):
    """Reproduced consumer probe: version 0.1.0 accepted substituted content."""

    def test_substituted_bytes_under_an_allowed_basename_are_refused(self):
        import json as _json, tempfile
        directory = tempfile.mkdtemp()
        with open(os.path.join(directory, "megvii_val.json"), "w", encoding="utf-8") as handle:
            _json.dump({"results": {}}, handle)
        with self.assertRaises(ra.AssociationError) as caught:
            ra.read_submission(directory, "megvii_val.json", 0.3)
        self.assertIn("does not match its recorded digest", str(caught.exception))

    def test_a_name_without_a_recorded_digest_is_refused(self):
        with self.assertRaises(ra.AssociationError):
            ra.verify_bytes("/tmp/nothing.json", "gt_val_cache.json")

    def test_unverified_reads_are_confined_to_a_temporary_directory(self):
        with self.assertRaises(ra.AssociationError) as caught:
            ra.read_submission("/etc", "megvii_val.json", 0.3, verify=False)
        self.assertIn("temporary directory", str(caught.exception))

    def test_the_mechanism_scope_is_declared(self):
        scope = ra.load()["information_boundary"]["mechanism_scope"]
        self.assertIn("not an operating system sandbox", scope)
        self.assertIn("historical exposure", scope.lower())


class TheAssociationRuleIsAMeasuredChoice(unittest.TestCase):
    """Reproduced consumer probe: greedy joins depend on record order."""

    def instance(self):
        return ({"f": [("car", 0.0, 0.0), ("car", 0.9, 0.0)]},
                {"f": [("car", 0.5, 0.0), ("car", -0.8, 0.0)]})

    def test_greedy_depends_on_the_order_records_arrive_in(self):
        left, right = self.instance()
        reversed_left = {"f": list(reversed(left["f"]))}
        self.assertEqual(ra.associate(left, right, 1.0)["both_channels"], 1)
        self.assertEqual(ra.associate(reversed_left, right, 1.0)["both_channels"], 2)

    def test_maximum_cardinality_does_not(self):
        left, right = self.instance()
        reversed_left = {"f": list(reversed(left["f"]))}
        self.assertEqual(ra.associate_maximum(left, right, 1.0)["both_channels"], 2)
        self.assertEqual(ra.associate_maximum(reversed_left, right, 1.0)["both_channels"], 2)

    def test_maximum_is_never_below_greedy(self):
        import random as _random
        rng = _random.Random(5)
        for _ in range(200):
            left = {"f": [("car", rng.uniform(-5, 5), rng.uniform(-5, 5)) for _ in range(rng.randint(0, 6))]}
            right = {"f": [("car", rng.uniform(-5, 5), rng.uniform(-5, 5)) for _ in range(rng.randint(0, 6))]}
            with self.subTest(sizes=(len(left["f"]), len(right["f"]))):
                self.assertGreaterEqual(ra.associate_maximum(left, right, 1.5)["both_channels"],
                                        ra.associate(left, right, 1.5)["both_channels"])

    def test_on_the_real_tables_the_rule_never_changes_the_state(self):
        report = ra.report()
        self.assertTrue(report["sensitivity_is_dominated_by_the_radius"]["states_unchanged_by_the_rule"])
        for entry in report["rule_effect"]:
            with self.subTest(setting=(entry["score_minimum"], entry["association_radius_m"])):
                self.assertTrue(entry["same_state"])

    def test_the_radius_matters_far_more_than_the_rule(self):
        sensitivity = ra.report()["sensitivity_is_dominated_by_the_radius"]
        self.assertGreater(Fraction(sensitivity["threshold_span_across_preparations"]), 10)
        self.assertLess(Fraction(sensitivity["largest_relative_move_from_the_matching_rule"]),
                        Fraction(1, 10))


class TheAnnotationCountIsScaleNotABound(unittest.TestCase):
    def test_the_implausibility_inference_is_withdrawn(self):
        report = ra.report()
        self.assertNotIn("at_least_one_setting_makes_positive_coupling_implausible", report)
        limits = report["not_established"]
        self.assertTrue(any("bounds unseen physical opportunities" in item for item in limits))

    def test_every_row_labels_the_ratio_as_scale_only(self):
        for row in ra.report()["rows"]:
            with self.subTest(rule=row["rule"]):
                self.assertIn("scale_only", row)
                self.assertIn("different units", row["scale_only"])


if __name__ == "__main__":
    unittest.main()
