"""Tests for the obstructed audit and the fourth withdrawal."""
from fractions import Fraction
import hashlib
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import headline_audit as ha  # noqa: E402
import preparation_robustness as pr  # noqa: E402


class TheFamilyWasStillFixedBeforeTheResult(unittest.TestCase):
    def test_the_grid_carries_the_preregistration_digest(self):
        actual = hashlib.sha256(open(pr.PREREGISTRATION, "rb").read()).hexdigest()
        self.assertEqual(pr.load()["preregistration_sha256"], actual)

    def test_the_grid_contains_exactly_the_declared_preparations(self):
        declared = json.load(open(pr.PREREGISTRATION))["admissible_preparation_family"]
        seen = {(r["P1"], r["P2"], r["P3"]) for r in pr.load()["grid"]}
        expected = {(a, b, c) for a in declared["P1_class_scope"]
                    for b in declared["P2_range_band"] for c in declared["P3_visibility_floor"]}
        self.assertEqual(seen, expected)

    def test_the_family_was_not_widened(self):
        self.assertEqual(len(pr.load()["grid"]),
                         json.load(open(pr.PREREGISTRATION))[
                             "admissible_preparation_family"]["total_preparations"])


class EveryComparisonDeclaresWhatItChanges(unittest.TestCase):
    """The consumer requirement that withdrew the flip."""

    def test_each_row_records_cutoffs_rates_and_membership(self):
        for row in pr.load()["grid"]:
            for arm in pr.ARMS:
                entry = row.get(arm, {})
                if entry.get("state") != "computed":
                    continue
                with self.subTest(scope=(row["P1"], row["P2"]), arm=arm):
                    self.assertEqual(len(entry["cutoffs"]), 5)
                    self.assertEqual(len(entry["achieved_miss_rates"]), 5)
                    self.assertEqual(len(entry["kept_counts"]), 5)

    def test_each_row_states_what_it_changes(self):
        for row in pr.load()["grid"]:
            if row.get("state") == "too_small":
                continue
            with self.subTest(scope=(row["P1"], row["P2"], row["P3"])):
                self.assertIn("evaluation_scope", row["what_this_comparison_changes"])

    def test_the_matched_arm_moves_the_operating_point(self):
        movement = pr.cutoff_movement(pr.load())
        self.assertGreater(movement["largest_move"], 0.5)


class TheFlipWitnessIsWithdrawn(unittest.TestCase):
    def test_the_report_records_the_withdrawal_and_its_reason(self):
        withdrawn = pr.report()["withdrawn"]
        self.assertIn("not robust to evaluation scope", withdrawn["claim"])
        self.assertIn("changed the operating point", withdrawn["why"])

    def test_the_previously_failing_cells_hold_when_the_cutoff_is_fixed(self):
        data = pr.load()
        previously = {("vehicles_only", "within_30m"), ("exclude_static_furniture", "within_30m")}
        checked = 0
        for row in data["grid"]:
            if (row["P1"], row["P2"]) not in previously:
                continue
            matched = row.get("matched_rate", {})
            fixed = row.get("fixed_cutoff", {})
            if matched.get("state") != "computed" or fixed.get("state") != "computed":
                continue
            if matched["predicate"]:
                continue
            checked += 1
            with self.subTest(scope=(row["P1"], row["P2"], row["P3"])):
                self.assertTrue(fixed["predicate"])
                self.assertGreater(Fraction(fixed["margin"]), 0)
        self.assertEqual(checked, 5)

    def test_the_fourth_withdrawal_is_registered(self):
        entry = [e for e in ha.REGISTER if e["headline"].startswith("the modality claim is not")][0]
        self.assertEqual(entry["status"], "withdrawn")
        self.assertEqual(len(entry["refuted_by"]), 1)


class NeitherArmIsolatesTheScope(unittest.TestCase):
    def test_the_fixed_arm_never_matches_the_marginals(self):
        self.assertEqual(pr.arm_summary(pr.load(), "fixed_cutoff")[
            "preparations_with_matched_marginals"], 0)

    def test_the_matched_arm_matches_marginals_only_sometimes(self):
        summary = pr.arm_summary(pr.load(), "matched_rate")
        self.assertGreater(summary["preparations_with_matched_marginals"], 0)
        self.assertLess(summary["preparations_with_matched_marginals"], summary["computed"])

    def test_the_obstruction_is_stated_as_the_result(self):
        note = pr.report()["neither_arm_isolates_the_scope"]["consequence"]
        self.assertIn("no preparation in this family isolates the scope effect", note)
        self.assertIn("marginal dependent", note)

    def test_the_single_fixed_arm_failure_is_not_called_clean(self):
        limits = pr.report()["not_established"]
        self.assertTrue(any("not a clean counterexample" in item for item in limits))


class ItCreditsTheRequirementNotTheMethod(unittest.TestCase):
    def test_the_report_says_the_requirement_did_the_work(self):
        note = pr.report()["what_the_consumer_requirement_bought"]
        self.assertIn("The requirement did the work, not the method", note)

    def test_the_surviving_claim_carries_its_scope(self):
        note = pr.report()["what_survives"]
        self.assertIn("at full scope with matched marginals", note)
        self.assertIn("scope is part of the claim", note)

    def test_a_grid_of_the_wrong_version_is_refused(self):
        data = pr.load()
        data["version"] = "0.1.0"
        import tempfile
        path = os.path.join(tempfile.mkdtemp(), "grid.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle)
        with self.assertRaises(pr.GridError):
            pr.load(path)


if __name__ == "__main__":
    unittest.main()
