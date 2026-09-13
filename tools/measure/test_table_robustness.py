"""Tests for the bounded correction model over an observed capture table."""
from fractions import Fraction
import json
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


class TheBreakdownNumberNeedsNoDeclaredBudget(unittest.TestCase):
    """Inverting the question removes the input nobody could verify.

    A declared correction budget has to be defended, and one smaller than reality
    gives a confident wrong answer. The breakdown number asks instead how many
    recorded objects would have to be wrong, in the most damaging combination,
    before the claim fails. An observation programme can judge that against its
    own process rather than committing to a budget in advance.
    """

    def test_the_sign_survives_eleven_wrong_objects_in_any_combination(self):
        result = robust.breakdown(RETAINED, moves=robust.ADVERSE_FOR_THE_SIGN)
        self.assertEqual(result["breakdown_number"], 12)
        self.assertEqual(result["of_how_many_recorded_objects"], 73)

    def test_mixing_beats_every_single_kind_of_error(self):
        """A per kind tolerance is not a breakdown number, and here it is off by one."""
        twelve_one_way = dict(RETAINED)
        twelve_one_way["u"] -= 12
        twelve_one_way["x"] += 12
        self.assertTrue(robust.settles_the_sign(twelve_one_way))

        six_and_six = dict(RETAINED)
        six_and_six["u"] -= 12
        six_and_six["x"] += 6
        six_and_six["y"] += 6
        self.assertFalse(robust.settles_the_sign(six_and_six))

    def test_every_minimal_attack_on_the_sign_splits_the_pair_misses(self):
        result = robust.breakdown(RETAINED, moves=robust.ADVERSE_FOR_THE_SIGN)
        for attack in result["minimal_breaking_corrections"]:
            with self.subTest(attack=attack["corrections"]):
                self.assertEqual(set(attack["corrections"]), {"u_to_x", "u_to_y"})
                self.assertEqual(sum(attack["corrections"].values()), 12)

    def test_restricting_to_adverse_moves_is_verified_not_assumed(self):
        """The full twelve move search returns the same number, 200 times slower."""
        full = robust.breakdown(RETAINED)
        restricted = robust.breakdown(RETAINED, moves=robust.ADVERSE_FOR_THE_SIGN)
        self.assertEqual(full["breakdown_number"], restricted["breakdown_number"])
        self.assertGreater(full["allocations_examined"],
                           100 * restricted["allocations_examined"])

    def test_a_claim_already_false_needs_no_correction(self):
        result = robust.breakdown({"w": 1, "x": 5, "y": 5, "u": 1})
        self.assertEqual(result["state"], "already_false")

    def test_exhaustion_is_unresolved_and_never_impossibility(self):
        original = robust.MAX_BREAKDOWN_ALLOCATIONS
        robust.MAX_BREAKDOWN_ALLOCATIONS = 20
        try:
            result = robust.breakdown(RETAINED)
            self.assertEqual(result["state"], "unresolved")
            self.assertIn("not a statement that no breakdown exists", result["reason"])
        finally:
            robust.MAX_BREAKDOWN_ALLOCATIONS = original


class RobustnessIsClaimRelative(unittest.TestCase):
    """The sign and the quantitative constant are threatened by opposite errors.

    Definition 32 asks for a constant, not a sign, so this is the robustness that
    an RSS style argument actually depends on, and it is the fragile one.
    """

    def constant_breakdown(self, constant):
        return robust.breakdown(RETAINED, constant=constant, ceiling=12)

    def test_the_observed_constant_breaks_at_a_single_wrong_object(self):
        observed = robust.supremum_over_unseen(RETAINED)
        self.assertEqual(observed, Fraction(1679, 1188))
        self.assertEqual(self.constant_breakdown(observed)["breakdown_number"], 1)

    def test_a_tight_constant_is_far_more_fragile_than_the_sign(self):
        sign = robust.breakdown(RETAINED, moves=robust.ADVERSE_FOR_THE_SIGN)["breakdown_number"]
        constant = self.constant_breakdown(Fraction(3, 2))["breakdown_number"]
        self.assertEqual(constant, 2)
        self.assertLess(constant, sign / 5)

    def test_a_looser_constant_buys_robustness(self):
        numbers = [self.constant_breakdown(k)["breakdown_number"]
                   for k in (Fraction(3, 2), Fraction(8, 5), Fraction(2))]
        self.assertEqual(numbers, sorted(numbers))
        self.assertEqual(numbers, [2, 4, 10])

    def test_the_same_correction_helps_the_sign_and_destroys_the_constant(self):
        """x_to_w raises the margin and raises the coefficient at once."""
        moved = dict(RETAINED)
        moved["x"] -= 2
        moved["w"] += 2
        before = RETAINED["w"] * RETAINED["u"] - RETAINED["x"] * RETAINED["y"]
        after = moved["w"] * moved["u"] - moved["x"] * moved["y"]
        self.assertGreater(after, before)
        self.assertGreater(robust.supremum_over_unseen(moved), Fraction(3, 2))
        self.assertLess(robust.supremum_over_unseen(RETAINED), Fraction(3, 2))

    def test_the_cheapest_attacks_on_the_two_claims_are_different_moves(self):
        sign = robust.breakdown(RETAINED, moves=robust.ADVERSE_FOR_THE_SIGN)
        constant = self.constant_breakdown(Fraction(3, 2))
        sign_moves = set(sign["minimal_breaking_corrections"][0]["corrections"])
        constant_moves = set(constant["minimal_breaking_corrections"][0]["corrections"])
        self.assertFalse(sign_moves & constant_moves)

    def test_the_adverse_restriction_is_not_applied_to_a_constant_claim(self):
        """It is only sound for the sign, and the constant search must not use it."""
        result = self.constant_breakdown(Fraction(3, 2))
        self.assertIn("x_to_w", result["moves_searched"])


class TheLowerBoundIsAProofNotASearch(unittest.TestCase):
    """A conventional argument that discharges the obligation the search cannot.

    Evaluating one adverse table proves that attack works. It does not prove no
    cheaper attack exists. The bound discharges exactly that second obligation,
    in constant arithmetic per level.
    """

    def exhaustive_worst(self, table, k):
        worst = None
        for total in range(0, k + 1):
            for allocation in robust._allocations(total, len(robust.ADVERSE_FOR_THE_SIGN)):
                leaving = {cell: 0 for cell in "wxyu"}
                for (source, _), amount in zip(robust.ADVERSE_FOR_THE_SIGN, allocation):
                    leaving[source] += amount
                if any(leaving[cell] > table[cell] for cell in "wxyu"):
                    continue
                corrected = robust._apply(table, allocation, robust.ADVERSE_FOR_THE_SIGN)
                margin = (corrected["w"] * corrected["u"]
                          - corrected["x"] * corrected["y"])
                if worst is None or margin < worst:
                    worst = margin
        return worst

    def test_it_never_overstates_on_the_retained_table(self):
        for k in range(0, 13):
            with self.subTest(k=k):
                self.assertLessEqual(robust.margin_lower_bound(RETAINED, k),
                                     self.exhaustive_worst(RETAINED, k))

    def test_it_is_tight_from_two_moves_onward_and_loose_by_one_below(self):
        """A bound, not the worst case. Stating where it is tight is part of the claim."""
        self.assertEqual(self.exhaustive_worst(RETAINED, 0)
                         - robust.margin_lower_bound(RETAINED, 0), 2)
        self.assertEqual(self.exhaustive_worst(RETAINED, 1)
                         - robust.margin_lower_bound(RETAINED, 1), 1)
        for k in range(2, 13):
            with self.subTest(k=k):
                self.assertEqual(robust.margin_lower_bound(RETAINED, k),
                                 self.exhaustive_worst(RETAINED, k))

    def test_it_never_overstates_on_random_tables(self):
        rng = random.Random(20260913)
        checked = 0
        for _ in range(40):
            table = {cell: rng.randint(1, 10) for cell in "wxyu"}
            for k in range(0, min(4, table["u"]) + 1):
                checked += 1
                with self.subTest(table=table, k=k):
                    self.assertLessEqual(robust.margin_lower_bound(table, k),
                                         self.exhaustive_worst(table, k))
        self.assertGreater(checked, 100)

    def test_the_single_endpoint_form_is_unsound_and_the_counterexample_is_retained(self):
        """w*(u-k) alone fails whenever u exceeds w. Reproduced, not asserted."""
        table = {"w": 2, "x": 10, "y": 13, "u": 4}
        k = 1
        naive = table["w"] * (table["u"] - k) - ((table["x"] + table["y"] + k) ** 2) // 4
        true_worst = self.exhaustive_worst(table, k)
        self.assertGreater(naive, true_worst)
        self.assertEqual(naive, -138)
        self.assertEqual(true_worst, -139)
        self.assertLessEqual(robust.margin_lower_bound(table, k), true_worst)

    def test_the_two_endpoints_coincide_when_the_pair_misses_do_not_exceed_the_joint_captures(self):
        self.assertLessEqual(RETAINED["u"], RETAINED["w"])
        w, u, k = RETAINED["w"], RETAINED["u"], 11
        self.assertEqual(min(w * (u - k), (w - k) * u), w * (u - k))

    def test_the_bound_proves_eleven_safe_and_the_witness_breaks_twelve(self):
        self.assertEqual(robust.margin_lower_bound(RETAINED, 11), 35)
        self.assertEqual(robust.margin_lower_bound(RETAINED, 12), -9)
        witness = {"w": 27, "x": 17, "y": 18, "u": 11}
        self.assertEqual(witness["w"] * witness["u"] - witness["x"] * witness["y"], -9)
        self.assertFalse(robust.settles_the_sign(witness))


class TheCertifiedBreakdownCostsFarLess(unittest.TestCase):
    def test_it_agrees_with_the_full_enumeration(self):
        certified = robust.certified_breakdown(RETAINED, moves=robust.ADVERSE_FOR_THE_SIGN)
        full = robust.breakdown(RETAINED)
        self.assertEqual(certified["breakdown_number"], full["breakdown_number"])
        self.assertTrue(certified["bound_and_search_agree"])

    def test_the_proof_removes_every_level_below(self):
        certified = robust.certified_breakdown(RETAINED, moves=robust.ADVERSE_FOR_THE_SIGN)
        self.assertEqual(certified["levels_proved_safe_by_bound"], 11)
        self.assertEqual(certified["search_needed_only_from"], 12)
        self.assertGreater(certified["bound_at_the_last_proved_level"], 0)
        self.assertLessEqual(certified["bound_at_the_first_unproved_level"], 0)

    def test_the_two_obligations_are_reported_separately(self):
        obligations = robust.certified_breakdown(
            RETAINED, moves=robust.ADVERSE_FOR_THE_SIGN)["obligations"]
        self.assertIn("lower bound", obligations["no_cheaper_attack_exists"])
        self.assertIn("complete disproof", obligations["this_attack_works"])


class TheCertificateDoesNotOverstateWhatOneTableProves(unittest.TestCase):
    def test_a_breaking_table_is_called_a_complete_disproof(self):
        result = robust.analyse(
            RETAINED, {"u_to_x": 6, "u_to_y": 6, "u_removed": 11, "w_to_x": 5, "w_removed": 5})
        self.assertFalse(result["sign_survives_every_admissible_table"])
        self.assertIn("complete disproof",
                      result["worst_admissible_completion"]["certificate"])

    def test_a_surviving_table_is_not_called_a_proof(self):
        result = robust.analyse(RETAINED, {"u_to_x": 2})
        self.assertTrue(result["sign_survives_every_admissible_table"])
        certificate = result["worst_admissible_completion"]["certificate"]
        self.assertIn("NOT a one line proof", certificate)
        self.assertIn("property of the search", certificate)


class TheInterfaceDistinguishesMissingFromEmpty(unittest.TestCase):
    def run_cli(self, payload):
        import subprocess, tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(payload, handle)
            path = handle.name
        module = os.path.join(os.path.dirname(os.path.abspath(__file__)), "table_robustness.py")
        return subprocess.run([sys.executable, "-B", module, path],
                              capture_output=True, text=True)

    def test_a_missing_budget_is_refused_rather_than_silently_emptied(self):
        done = self.run_cli({"observed_table": RETAINED})
        self.assertEqual(done.returncode, 1)
        self.assertIn("no budget was declared", done.stderr)

    def test_a_null_budget_is_refused_separately(self):
        done = self.run_cli({"observed_table": RETAINED, "budget": None})
        self.assertEqual(done.returncode, 1)
        self.assertIn("null", done.stderr)

    def test_an_explicitly_empty_budget_is_honoured(self):
        done = self.run_cli({"observed_table": RETAINED, "budget": {}})
        self.assertEqual(done.returncode, 0)
        self.assertEqual(json.loads(done.stdout)["declared_budget"], {})

    def test_a_budget_free_breakdown_must_be_asked_for_explicitly(self):
        done = self.run_cli({"observed_table": RETAINED, "breakdown": True})
        self.assertEqual(done.returncode, 0)
        self.assertEqual(json.loads(done.stdout)["breakdown_number"], 12)

    def test_asking_for_both_is_refused(self):
        done = self.run_cli({"observed_table": RETAINED, "budget": {}, "breakdown": True})
        self.assertEqual(done.returncode, 1)
        self.assertIn("not both", done.stderr)


class AnInvalidBoundIsNotASmallOne(unittest.TestCase):
    def test_a_negative_ceiling_is_refused(self):
        with self.assertRaises(robust.BudgetError):
            robust.breakdown(RETAINED, ceiling=-1)

    def test_a_boolean_ceiling_is_refused(self):
        with self.assertRaises(robust.BudgetError):
            robust.breakdown(RETAINED, ceiling=True)

    def test_a_truncated_search_is_not_called_complete(self):
        result = robust.breakdown(RETAINED, moves=robust.ADVERSE_FOR_THE_SIGN, ceiling=5)
        self.assertEqual(result["state"], "no_breakdown_within_the_searched_range")
        self.assertFalse(result["search_was_exhaustive"])
        self.assertIn("not a complete answer", result["reason"])

    def test_an_interrupted_level_is_distinguished_from_the_finished_ones(self):
        original = robust.MAX_BREAKDOWN_ALLOCATIONS
        robust.MAX_BREAKDOWN_ALLOCATIONS = 30
        try:
            result = robust.breakdown(RETAINED)
            self.assertEqual(result["state"], "unresolved")
            self.assertEqual(result["interrupted_at_level"],
                             result["levels_fully_searched"] + 1)
        finally:
            robust.MAX_BREAKDOWN_ALLOCATIONS = original


if __name__ == "__main__":
    unittest.main()
