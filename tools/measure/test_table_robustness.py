"""Tests for the bounded correction model over an observed capture table."""
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cohort_packet as packet  # noqa: E402
import joint_miss_identification as jm  # noqa: E402
import table_robustness as robust  # noqa: E402

CASES = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "research", "cohort-packet", "0.1.0")


def load(name):
    import json
    with open(os.path.join(CASES, name), "r", encoding="utf-8") as handle:
        return json.load(handle)

RETAINED = {"w": 27, "x": 10, "y": 13, "u": 23}


class TheConditionMatchesTheIdentificationModule(unittest.TestCase):
    """w * (u + m) > x * y is the same statement as m * w > a * b - u * S."""

    def test_the_two_forms_agree_on_random_tables(self):
        rng = random.Random(20260913)
        for _ in range(400):
            w, x, y, u = (rng.randint(0, 40) for _ in range(4))
            counts = {}
            if w:
                counts[(1, 1, 0)] = w
            if x:
                counts[(1, 0, 0)] = x
            if y:
                counts[(0, 1, 0)] = y
            if u:
                counts[(0, 0, 1)] = u
            if not counts:
                continue
            parts = jm.margins(counts)
            for m in range(0, 6):
                value = jm.coefficient(parts, m)
                if value is None:
                    continue
                with self.subTest(table=(w, x, y, u), m=m):
                    self.assertEqual(value > 1, w * (u + m) > x * y)

    def test_the_hardest_unseen_count_is_zero(self):
        parts = jm.margins({(1, 1, 0): 27, (1, 0, 0): 10, (0, 1, 0): 13, (0, 0, 1): 23})
        at_zero = jm.coefficient(parts, 0)
        for m in (1, 5, 50, 5000):
            self.assertGreaterEqual(jm.coefficient(parts, m), min(at_zero, 1))
        self.assertEqual(robust.settles_the_sign(RETAINED), at_zero > 1)


class HowMuchThirdSourceEvidenceIsEnough(unittest.TestCase):
    def test_five_verified_pair_misses_suffice_at_the_observed_margins(self):
        self.assertEqual(robust.smallest_sufficient_u(27, 10, 13), 5)
        self.assertFalse(robust.settles_the_sign({"w": 27, "x": 10, "y": 13, "u": 4}))
        self.assertTrue(robust.settles_the_sign({"w": 27, "x": 10, "y": 13, "u": 5}))

    def test_the_observed_count_is_well_past_the_requirement(self):
        self.assertGreater(RETAINED["u"], 4 * robust.smallest_sufficient_u(27, 10, 13))

    def test_no_amount_of_evidence_suffices_without_a_joint_capture(self):
        self.assertIsNone(robust.smallest_sufficient_u(0, 10, 13))


class MisassociationBindsBeforeSpuriousness(unittest.TestCase):
    """The kinds of error are not equally damaging, and the order is actionable."""

    def tolerance(self, kind):
        source, target = kind.split("_to_") if "_to_" in kind else (kind.split("_")[0], None)
        return robust.single_allowance_tolerance(RETAINED, source, target)

    def test_moving_a_pair_miss_into_a_single_capture_is_the_binding_risk(self):
        moved = self.tolerance("u_to_x")["largest_allowance_that_survives"]
        removed = self.tolerance("u_removed")["largest_allowance_that_survives"]
        self.assertEqual(moved, 12)
        self.assertEqual(removed, 18)
        self.assertLess(moved, removed)

    def test_corrections_that_favour_the_conclusion_never_break_it(self):
        for kind in ("x_to_w", "y_to_w", "x_to_u", "y_to_u", "x_removed", "y_removed"):
            with self.subTest(kind=kind):
                self.assertIsNone(self.tolerance(kind)["breaks_at"])

    def test_the_tolerances_agree_with_direct_evaluation(self):
        for source, target in robust.MOVES:
            entry = robust.single_allowance_tolerance(RETAINED, source, target)
            largest = entry["largest_allowance_that_survives"]
            if largest is None:
                continue
            table = dict(RETAINED)
            table[source] -= largest
            if target:
                table[target] += largest
            with self.subTest(move=(source, target)):
                self.assertTrue(robust.settles_the_sign(table))
            if entry["breaks_at"] is not None:
                table = dict(RETAINED)
                table[source] -= entry["breaks_at"]
                if target:
                    table[target] += entry["breaks_at"]
                self.assertFalse(robust.settles_the_sign(table))


class TheSignSurvivesOrItDoesNot(unittest.TestCase):
    def test_a_modest_budget_leaves_the_conclusion_standing(self):
        result = robust.analyse(RETAINED, {"u_to_x": 2, "u_to_y": 2, "u_removed": 5})
        self.assertTrue(result["sign_survives_every_admissible_table"])
        self.assertGreater(result["worst_admissible_completion"]["margin"], 0)

    def test_a_severe_budget_destroys_it(self):
        result = robust.analyse(
            RETAINED, {"u_to_x": 6, "u_to_y": 6, "u_removed": 11, "w_to_x": 5, "w_removed": 5})
        self.assertFalse(result["sign_survives_every_admissible_table"])
        worst = result["worst_admissible_completion"]
        self.assertLess(worst["margin"], 0)
        self.assertFalse(robust.settles_the_sign(worst["table"]))

    def test_the_worst_completion_is_a_checkable_certificate(self):
        result = robust.analyse(RETAINED, {"u_to_x": 4, "u_removed": 6})
        worst = result["worst_admissible_completion"]
        table = worst["table"]
        self.assertEqual(worst["margin"], table["w"] * table["u"] - table["x"] * table["y"])

    def test_the_adversary_uses_the_dependence_between_counts(self):
        """It moves objects out of u AND into x, which hurts both sides at once."""
        result = robust.analyse(RETAINED, {"u_to_x": 8})
        applied = result["worst_admissible_completion"]["corrections_applied"]
        table = result["worst_admissible_completion"]["table"]
        self.assertEqual(applied.get("u_to_x"), 8)
        self.assertEqual(table["u"], RETAINED["u"] - 8)
        self.assertEqual(table["x"], RETAINED["x"] + 8)

    def test_an_empty_budget_reports_the_observed_table_unchanged(self):
        result = robust.analyse(RETAINED, {})
        self.assertEqual(result["corrected_tables_examined"], 1)
        self.assertEqual(result["worst_admissible_completion"]["table"], RETAINED)


class ItRefusesWhatItCannotDefend(unittest.TestCase):
    def test_a_budget_is_required_and_never_invented(self):
        with self.assertRaises(robust.BudgetError):
            robust.analyse(RETAINED, None)
        self.assertIn("No error budget", robust.analyse(RETAINED, {})["what_the_budget_is"])

    def test_an_undefined_correction_kind_is_refused(self):
        with self.assertRaises(robust.BudgetError) as caught:
            robust.analyse(RETAINED, {"u_to_elsewhere": 3})
        self.assertIn("does not define", str(caught.exception))

    def test_negative_and_boolean_allowances_are_refused(self):
        for bad in ({"u_to_x": -1}, {"u_to_x": True}):
            with self.subTest(budget=bad):
                with self.assertRaises(robust.BudgetError):
                    robust.analyse(RETAINED, bad)

    def test_a_budget_too_large_to_enumerate_is_unresolved_not_impossible(self):
        original = robust.MAX_TABLES
        robust.MAX_TABLES = 50
        try:
            with self.assertRaises(robust.BudgetError) as caught:
                robust.analyse(RETAINED, {"u_to_x": 10, "u_to_y": 10, "u_removed": 10})
            self.assertIn("not a statement that the sign is undecidable", str(caught.exception))
        finally:
            robust.MAX_TABLES = original

    def test_more_objects_cannot_leave_a_cell_than_it_holds(self):
        tables = list(robust.admissible_tables({"w": 2, "x": 1, "y": 1, "u": 1},
                                               {"u_to_x": 3, "u_removed": 3}))
        for table, _ in tables:
            with self.subTest(table=table):
                self.assertTrue(all(value >= 0 for value in table.values()))

    def test_validity_is_not_independence(self):
        note = robust.analyse(RETAINED, {})["what_validity_is_not"]
        self.assertIn("statistical", note)
        self.assertIn("procedural independence", note)


class ACoefficientCertificateIsNotAnIntegrationDecision(unittest.TestCase):
    """The bridge to the question the Engine actually asks.

    `ghost-burden-none` and `ghost-burden-three` have the SAME capture table: the
    same object captured by both channels, the same object by the base only. A
    detection that matches nothing changes no cell of that table, so it changes no
    coefficient bound. It does change the additive loss, and the integration
    verdict flips. A certificate about the coefficient supports the conclusion it
    is about and does not stand in for the decision.
    """

    def reports(self):
        return (packet.build(load("ghost-burden-none.json")),
                packet.build(load("ghost-burden-three.json")))

    def test_the_capture_structure_is_identical(self):
        none, three = self.reports()
        for field in ("tp_base", "tp_augmented"):
            self.assertEqual(none["joint_worlds"][0]["anchors"][0][field],
                             three["joint_worlds"][0]["anchors"][0][field])
        self.assertEqual(none["joint_worlds"][0]["anchors"][0]["objects_present"],
                         three["joint_worlds"][0]["anchors"][0]["objects_present"])

    def test_only_the_false_positive_burden_differs(self):
        none, three = self.reports()
        self.assertEqual(none["anchors"][0]["retained_additions"], 1)
        self.assertEqual(three["anchors"][0]["retained_additions"], 4)

    def test_the_integration_verdict_flips(self):
        none, three = self.reports()
        self.assertEqual(none["decision"]["improvement_criterion"], "supported")
        self.assertEqual(three["decision"]["improvement_criterion"], "excluded")

    def test_the_ghost_detections_match_nothing(self):
        case = load("ghost-burden-three.json")
        edges = {tuple(e) for e in case["joint_worlds"][0]["per_anchor"]["A"]["edges"]}
        ghosts = {d["id"] for d in case["anchors"][0]["added_detections"]
                  if d["id"].startswith("g")}
        self.assertEqual(len(ghosts), 3)
        self.assertFalse({e for e in edges if e[0] in ghosts})

    def test_the_additive_loss_assumptions_are_preserved(self):
        """Base detections, matching competition, weights and tolerance all stand."""
        for name in ("ghost-burden-none.json", "ghost-burden-three.json"):
            case = load(name)
            with self.subTest(case=name):
                self.assertEqual(case["loss"]["tolerance"], "1/10")
                self.assertEqual(case["anchors"][0]["weight"], "1")
                self.assertTrue(case["anchors"][0]["base_detections"])
                report = packet.build(case)
                entry = report["joint_worlds"][0]["anchors"][0]
                self.assertIn("base_certificate", entry)
                self.assertIn("augmented_certificate", entry)


if __name__ == "__main__":
    unittest.main()
