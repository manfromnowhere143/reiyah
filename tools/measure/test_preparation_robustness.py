"""Tests for the pre-registered audit of this lane's own modality claim."""
from fractions import Fraction
import hashlib
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import headline_audit as ha  # noqa: E402
import preparation_robustness as pr  # noqa: E402


class TheFamilyWasFixedBeforeTheResult(unittest.TestCase):
    def test_the_grid_carries_the_preregistration_digest(self):
        data = pr.load()
        actual = hashlib.sha256(open(pr.PREREGISTRATION, "rb").read()).hexdigest()
        self.assertEqual(data["preregistration_sha256"], actual)

    def test_the_preregistration_declares_the_whole_family(self):
        declared = json.load(open(pr.PREREGISTRATION))
        family = declared["admissible_preparation_family"]
        self.assertEqual(len(family["P1_class_scope"]) * len(family["P2_range_band"])
                         * len(family["P3_visibility_floor"]), family["total_preparations"])
        self.assertEqual(family["total_preparations"], len(pr.load()["grid"]))

    def test_the_grid_contains_exactly_the_declared_preparations(self):
        declared = json.load(open(pr.PREREGISTRATION))["admissible_preparation_family"]
        seen = {(row["P1"], row["P2"], row["P3"]) for row in pr.load()["grid"]}
        expected = {(a, b, c) for a in declared["P1_class_scope"]
                    for b in declared["P2_range_band"] for c in declared["P3_visibility_floor"]}
        self.assertEqual(seen, expected)

    def test_the_score_cutoff_is_excluded_as_a_configuration_change(self):
        declared = json.load(open(pr.PREREGISTRATION))
        excluded = declared["explicitly_excluded_from_the_uncertainty_family"]
        self.assertIn("changes the system being evaluated", excluded["detector_score_cutoff"])
        self.assertNotIn("score", str(declared["admissible_preparation_family"]).lower())


class TheClaimIsNotRobust(unittest.TestCase):
    def test_the_verdict_is_a_flip_witness(self):
        self.assertEqual(pr.outcome()["verdict"], "flip_witness")

    def test_five_preparations_fail_and_thirty_hold(self):
        result = pr.outcome()
        self.assertEqual(result["fails"], 5)
        self.assertEqual(result["holds"], 30)
        self.assertEqual(result["undefined"], 13)
        self.assertEqual(result["preparations"], 48)

    def test_every_failure_is_a_close_range_scope(self):
        report = pr.report()
        self.assertTrue(report["every_failure_shares_a_range_band"])
        self.assertEqual(report["the_shared_band"], ["within_30m"])

    def test_the_failing_margins_are_negative_and_the_holding_ones_positive(self):
        for witness in pr.flip_witnesses():
            with self.subTest(scope=(witness["class_scope"], witness["range_band"])):
                self.assertLess(Fraction(witness["margin"]), 0)
        self.assertGreater(Fraction(pr.report()["largest_holding_margin"]), 0)

    def test_at_least_one_failure_is_not_a_knife_edge(self):
        worst = Fraction(pr.report()["worst_failing_margin"])
        self.assertLess(worst, -pr.THIN)

    def test_the_margin_is_the_predicate_quantity(self):
        for row in pr.load()["grid"]:
            if row.get("state") != "computed":
                continue
            gap = pr.margin(row)
            with self.subTest(scope=(row["P1"], row["P2"], row["P3"])):
                self.assertEqual(row["predicate"], gap > 0)


class TheBaselineIsNotBeaten(unittest.TestCase):
    def test_the_grid_is_named_as_the_method_not_a_competitor(self):
        note = pr.report()["baseline"]["honest_position"]
        self.assertIn("not a competitor it beat", note)
        self.assertIn("Nothing here outperforms", note)

    def test_the_prior_art_is_cited(self):
        self.assertIn("NeurIPS 2022", pr.report()["baseline"]["citation"])

    def test_what_was_added_is_called_discipline_not_advantage(self):
        added = pr.report()["what_the_discipline_added"]
        self.assertEqual(len(added), 3)
        self.assertTrue(any("digested before any result" in item for item in added))


class TheHeadlineRegisterReflectsIt(unittest.TestCase):
    def test_the_three_review_cost_headlines_are_withdrawn(self):
        report = ha.audit()
        self.assertEqual(report["withdrawn"], 3)

    def test_the_modality_headline_is_now_qualified_not_standing(self):
        entry = [e for e in ha.REGISTER if e["headline"].startswith("same modality")][0]
        self.assertEqual(entry["status"], "qualified")
        self.assertEqual(len(entry["refuted_by"]), 1)
        self.assertIn("within 30 metres", entry["qualification"])

    def test_every_cited_artifact_exists(self):
        for finding in ha.audit()["findings"]:
            with self.subTest(headline=finding["headline"][:40]):
                self.assertEqual(finding["cited_artifacts_missing"], [])

    def test_the_audit_says_what_it_cannot_do(self):
        limits = ha.audit()["what_this_does_not_do"]
        self.assertTrue(any("nobody registered" in item for item in limits))
        self.assertTrue(any("unexamined, not confirmed" in item for item in limits))


if __name__ == "__main__":
    unittest.main()
