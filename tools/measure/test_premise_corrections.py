"""Tests for the premise corrections, recomputed a second way."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import premise_corrections as corrections  # noqa: E402

# The original submissions live outside this repository under another owner. They are read
# read only and never copied in. Point REIYAH_GATE_B_DIR at them to run the binding test.
SUBMISSIONS = os.environ.get("REIYAH_GATE_B_DIR",
                             os.path.join(os.path.expanduser("~"), "workspace", "reiyah-gate-b"))


class Grid(unittest.TestCase):
    def setUp(self):
        self.data = corrections.load()

    def test_the_grid_is_the_one_the_record_names(self):
        result = corrections.report()
        self.assertEqual(result["corrects"]["version"], "0.2.0")
        self.assertEqual(result["corrects"]["preregistration_sha256"],
                         "8e633b95e594c8b9c13061cb0af2ce19e0049a317013f3687a3c742144ac367c")

    def test_cutoff_movement_counted_a_second_way(self):
        reference = self.data["reference_cutoffs_at_full_scope"]
        moved, all_five, computed = 0, 0, 0
        for row in self.data["grid"]:
            arm = row["matched_rate"]
            if arm["state"] != "computed":
                continue
            computed += 1
            changed = [name for name in reference if arm["cutoffs"][name] != reference[name]]
            moved += 1 if changed else 0
            all_five += 1 if len(changed) == 5 else 0
        found = corrections.cutoff_changes(self.data)
        self.assertEqual(computed, 35)
        self.assertEqual(found["rows_computed_in_the_matched_arm"], computed)
        self.assertEqual(found["moved_at_least_one"], moved)
        self.assertEqual(found["moved_all_five"], all_five)
        self.assertEqual(found["rows_not_computed"], 13)

    def test_the_two_unchanged_rows_are_the_full_population(self):
        found = corrections.cutoff_changes(self.data)
        self.assertEqual(len(found["moved_none"]), 2)
        populations = {row["population"] for row in self.data["grid"]
                       if [row["P1"], row["P2"], row["P3"]] in found["moved_none"]}
        self.assertEqual(populations, {corrections.POPULATION})

    def test_within_50m_is_the_identity_on_this_population(self):
        found = corrections.duplicate_preparations(self.data)
        self.assertEqual(found["labels"], 48)
        self.assertEqual(found["distinct_preparations"], 33)
        self.assertEqual(found["within_50m_is_the_identity_in"], 12)
        for entry in found["duplicates"]:
            populations = {row["population"] for row in self.data["grid"]
                           if [row["P1"], row["P2"], row["P3"]] in entry["labels"]}
            self.assertEqual(len(populations), 1)

    def test_a_grid_with_no_duplicates_reports_none(self):
        data = json.loads(json.dumps(self.data))
        for index, row in enumerate(data["grid"]):
            row["population"] = 1000 + index
        found = corrections.duplicate_preparations(data)
        self.assertEqual(found["duplicate_groups"], 0)
        self.assertEqual(found["distinct_preparations"], 48)


class TieRule(unittest.TestCase):
    def test_the_rule_is_read_off_synthetic_scores_not_assumed(self):
        directory = tempfile.mkdtemp()
        scores = {"car": {str(i): 0.5 for i in range(10)}}
        scores["car"].update({str(i): 0.9 for i in range(10, 15)})
        for name in ("centerpoint", "fcos3d", "mapillary", "megvii", "pointpillars"):
            with open(os.path.join(directory, "matched_%s.json" % name), "w",
                      encoding="utf-8") as handle:
                json.dump({"matched_at_2m": scores}, handle)
        data = json.loads(json.dumps(corrections.load()))
        for row in data["grid"]:
            if [row["P1"], row["P2"], row["P3"]] == ["all_classes", "all_ranges", "all_visibility"]:
                row["fixed_cutoff"]["kept_counts"] = {name: 5 for name in
                                                      data["reference_cutoffs_at_full_scope"]}
        data["reference_cutoffs_at_full_scope"] = {name: 0.5 for name in
                                                   data["reference_cutoffs_at_full_scope"]}
        found = corrections.tie_rule(directory, data)
        self.assertEqual(found["state"], "recomputed")
        self.assertEqual(found["tie_rule"], "strictly greater than the cutoff")
        for entry in found["detectors"].values():
            self.assertEqual(entry["kept_strictly_above"], 5)
            self.assertEqual(entry["kept_at_or_above"], 15)
            self.assertEqual(entry["tied_exactly_at_the_cutoff"], 10)

    def test_absent_submissions_are_reported_unavailable_not_filled_in(self):
        found = corrections.tie_rule(None, corrections.load())
        self.assertEqual(found["state"], "unavailable")
        self.assertIn("gt_val_cache.json", found["inputs_expected"])
        self.assertNotIn("detectors", found)

    @unittest.skipUnless(os.path.isdir(SUBMISSIONS), "original submissions not present")
    def test_the_stored_counts_are_reproduced_from_the_original_submissions(self):
        found = corrections.tie_rule(SUBMISSIONS, corrections.load())
        self.assertEqual(found["state"], "recomputed")
        self.assertEqual(found["tie_rule"], "strictly greater than the cutoff")
        self.assertEqual(found["residual_mismatch_objects"], 22)
        self.assertEqual(found["residual_mismatch_rate"], "22/134565")
        for name, expected in corrections.SUBMISSION_DIGESTS.items():
            if name in found["inputs"]:
                self.assertEqual(found["inputs"][name], expected)
        point = found["detectors"]["pointpillars"]
        self.assertFalse(point["matched_target_94196_attainable"])
        self.assertEqual(point["nearest_attainable_below_94196"], 94174)
        self.assertEqual(point["nearest_attainable_above_94196"], 94200)
        self.assertEqual(point["tied_exactly_at_the_cutoff"], 26)
        for name in ("centerpoint", "fcos3d", "mapillary", "megvii"):
            self.assertTrue(found["detectors"][name]["matched_target_94196_attainable"])


class Membership(unittest.TestCase):
    """Equal totals are not equal members. The 33 is only earned on source rows."""

    def test_absent_source_rows_leave_the_stronger_claim_unaccepted(self):
        found = corrections.membership(None, corrections.load())
        self.assertEqual(found["state"], "unavailable")
        self.assertIn("gt_val_cache.json", found["input_expected"])
        self.assertNotIn("distinct_memberships", found)

    def test_the_control_shows_what_the_aggregate_method_gets_wrong(self):
        control = corrections.equal_counts_different_members()
        self.assertTrue(control["aggregate_signature_equal"])
        self.assertFalse(control["membership_digest_equal"])
        self.assertEqual(control["two_selections"]["shared_rows"], 0)

    @unittest.skipUnless(os.path.isdir(SUBMISSIONS), "annotation cache not present")
    def test_membership_is_verified_on_exact_source_rows(self):
        found = corrections.membership(SUBMISSIONS, corrections.load())
        self.assertEqual(found["state"], "verified")
        self.assertTrue(found["input_matches_the_bound_digest"])
        self.assertEqual(found["labels"], 48)
        self.assertEqual(found["distinct_memberships"], 33)
        self.assertEqual(found["duplicate_membership_groups"], 15)
        self.assertEqual(found["rows_inside_a_duplicate_group"], 30)
        self.assertEqual(found["aggregate_groups_not_confirmed_by_membership"], [])
        self.assertEqual(found["membership_duplicates_the_aggregate_grouping_missed"], [])

    @unittest.skipUnless(os.path.isdir(SUBMISSIONS), "annotation cache not present")
    def test_a_predicate_that_does_not_reproduce_the_populations_draws_no_conclusion(self):
        data = json.loads(json.dumps(corrections.load()))
        for row in data["grid"]:
            if row["P2"] == "within_30m":
                row["population"] += 1
        found = corrections.membership(SUBMISSIONS, data)
        self.assertEqual(found["state"], "predicates_not_bound")
        self.assertTrue(found["labels_not_reproduced"])
        self.assertNotIn("distinct_memberships", found)


if __name__ == "__main__":
    unittest.main()
