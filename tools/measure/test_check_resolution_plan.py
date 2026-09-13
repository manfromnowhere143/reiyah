"""Adversaries for the resolution plan checker.

Every test here forges a plan a careless reader would accept and requires the
checker to name the defect. A checker that only agrees with the planner is not
a check, so the honest plans are included too: they must be accepted.
"""
import copy
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_resolution_plan as checker  # noqa: E402
import cohort_packet as producer  # noqa: E402
import resolution_plan as planner  # noqa: E402

CASES = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "research", "cohort-packet", "0.1.0")


def load(name):
    with open(os.path.join(CASES, name), "r", encoding="utf-8") as handle:
        return json.load(handle)


class AcceptsHonestPlans(unittest.TestCase):
    def test_every_retained_case_is_accepted(self):
        for name in ("matching-trap-plan-case.json", "three-copies-plan-case.json",
                     "sixteen-candidates-plan-case.json", "conditional-inertness-case.json",
                     "adaptive-beats-fixed-case.json", "geometry-ambiguity-plan-case.json",
                     "open-two-anchor.json"):
            case = load(name)
            with self.subTest(case=name):
                checker.check(case, planner.plan(case))


class TheOracleIsNotTheSameProgram(unittest.TestCase):
    """A feasibility ladder must agree with the minimiser on the depth."""

    def test_oracle_confirms_each_depth_and_refuses_one_less(self):
        for name in ("matching-trap-plan-case.json", "three-copies-plan-case.json",
                     "adaptive-beats-fixed-case.json"):
            case = load(name)
            result = planner.plan(case)
            depth = result["worst_case_observations"]
            questions = checker.permitted_questions(case)
            worlds = frozenset(w["world_id"] for w in case["joint_worlds"])
            with self.subTest(case=name):
                self.assertTrue(checker.resolvable_within(case, worlds, depth, questions, {}))
                if depth:
                    self.assertFalse(
                        checker.resolvable_within(case, worlds, depth - 1, questions, {}))


class AdaptiveCanBeatEveryFixedSet(unittest.TestCase):
    """The retained witness that a fixed resolving set cannot certify a plan."""

    def test_the_fixed_bound_is_strictly_larger_on_the_witness_case(self):
        case = load("adaptive-beats-fixed-case.json")
        result = planner.plan(case)
        findings = checker.check(case, result)
        fixed = findings["minimum_fixed_resolving_set"]["size"]
        self.assertEqual(result["worst_case_observations"], 2)
        self.assertEqual(fixed, 3)
        self.assertTrue(findings["minimum_fixed_resolving_set"]["strict_here"])

    def test_the_plan_asks_a_different_question_after_each_answer(self):
        result = planner.plan(load("adaptive-beats-fixed-case.json"))
        present = result["plan"]["if_present"]["ask"]
        absent = result["plan"]["if_absent"]["ask"]
        self.assertNotEqual(present, absent)
        self.assertNotIn(result["plan"]["ask"], (present, absent))


class RefusesForgedPlans(unittest.TestCase):
    def setUp(self):
        self.case = load("adaptive-beats-fixed-case.json")
        self.honest = planner.plan(self.case)

    def forge(self, mutate):
        result = copy.deepcopy(self.honest)
        mutate(result)
        with self.assertRaises(checker.PlanRefused) as caught:
            checker.check(self.case, result)
        return str(caught.exception)

    def test_understating_the_depth_is_refused(self):
        def mutate(result):
            result["worst_case_observations"] = 1
        self.assertIn("its own tree needs 2", self.forge(mutate))

    def test_overstating_the_depth_is_refused(self):
        """A wasteful plan is a correct tree. Only the oracle sees it is not optimal."""
        questions = checker.permitted_questions(self.case)
        order = [("A", "A_d"), ("B", "B_d"), ("C", "C_d")]

        def valid_tree(cell):
            """A genuinely correct tree that always asks A first: every node splits
            the cell it is given and every leaf carries the recomputed verdict."""
            verdict = checker._criterion(self.case, set(cell))
            if verdict in checker.DECIDED:
                return {"ask": None, "decided": verdict, "depth": 0}
            for key in order:
                yes = questions[key]
                left = frozenset(w for w in cell if w in yes)
                right = frozenset(w for w in cell if w not in yes)
                if not left or not right:
                    continue
                a, b = valid_tree(left), valid_tree(right)
                return {"ask": {"anchor": key[0], "object": key[1]},
                        "decided": None, "depth": 1 + max(a["depth"], b["depth"]),
                        "if_present": a, "if_absent": b}
            raise AssertionError("the fixture could not build a tree")

        worlds = frozenset(w["world_id"] for w in self.case["joint_worlds"])
        tree = valid_tree(worlds)
        self.assertEqual(tree["depth"], 3)
        forged = dict(self.honest, plan=tree, worst_case_observations=3,
                      first_question=tree["ask"])
        with self.assertRaises(checker.PlanRefused) as caught:
            checker.check(self.case, forged)
        self.assertIn("the oracle resolves within 2", str(caught.exception))

    def test_a_truncated_tree_is_refused(self):
        def mutate(result):
            result["plan"]["if_present"] = {"ask": None, "decided": "supported", "depth": 0}
            result["worst_case_observations"] = 1
            result["plan"]["depth"] = 1
        self.assertIn("not a decision", self.forge(mutate))

    def test_a_flipped_leaf_verdict_is_refused(self):
        def mutate(result):
            leaf = result["plan"]["if_present"]["if_present"]
            leaf["decided"] = "excluded" if leaf["decided"] == "supported" else "supported"
        self.assertIn("the cohort packet says", self.forge(mutate))

    def test_an_invented_question_is_refused(self):
        def mutate(result):
            result["plan"]["ask"] = {"anchor": "A", "object": "A_does_not_exist"}
            result["first_question"] = result["plan"]["ask"]
        self.assertIn("not a question this checker derived", self.forge(mutate))

    def test_swapping_the_branches_is_refused(self):
        def mutate(result):
            node = result["plan"]
            node["if_present"], node["if_absent"] = node["if_absent"], node["if_present"]
        self.assertIn("does not divide", self.forge(mutate))

    def test_first_question_must_match_the_root(self):
        def mutate(result):
            result["first_question"] = {"anchor": "A", "object": "A_d"}
        self.assertIn("first_question", self.forge(mutate))

    def test_a_decided_cell_may_not_be_asked_about(self):
        def mutate(result):
            leaf = result["plan"]["if_present"]["if_present"]
            leaf.clear()
            leaf.update({"ask": {"anchor": "A", "object": "A_d"}, "depth": 1, "decided": None,
                         "if_present": {"ask": None, "decided": "supported", "depth": 0},
                         "if_absent": {"ask": None, "decided": "supported", "depth": 0}})
        self.assertIn("already decided", self.forge(mutate))


class RefusesForgedNegatives(unittest.TestCase):
    def test_claiming_unresolvable_when_a_plan_exists_is_refused(self):
        case = load("adaptive-beats-fixed-case.json")
        report = producer.build(case)
        forged = {"artifact_id": planner.ARTIFACT_ID, "version": planner.REPORT_VERSION,
                  "state": "unresolvable_by_declared_questions",
                  "enclosure": report["enclosure"],
                  "improvement_criterion": report["decision"]["improvement_criterion"],
                  "witness_cell": ["b_only", "c_only"], "reason": "invented"}
        with self.assertRaises(checker.PlanRefused) as caught:
            checker.check(case, forged)
        self.assertIn("the oracle found a plan", str(caught.exception))

    def test_an_empty_population_may_not_be_called_geometry_ambiguity(self):
        """Retained defect: version 0.1.0 described zero worlds this way."""
        case = load("open-two-anchor.json")
        report = producer.build(case)
        forged = {"artifact_id": planner.ARTIFACT_ID, "version": planner.REPORT_VERSION,
                  "state": "unresolvable_by_declared_questions",
                  "enclosure": report["enclosure"],
                  "improvement_criterion": report["decision"]["improvement_criterion"],
                  "indistinguishable_world_groups": [], "witness_cell": [],
                  "reason": "some admitted worlds differ in a way questions cannot separate"}
        with self.assertRaises(checker.PlanRefused) as caught:
            checker.check(case, forged)
        self.assertIn("the case declares none", str(caught.exception))

    def test_geometry_ambiguity_needs_an_undivided_witness(self):
        case = load("geometry-ambiguity-plan-case.json")
        honest = planner.plan(case)
        forged = dict(honest, witness_cell=[honest["witness_cell"][0]])
        with self.assertRaises(checker.PlanRefused) as caught:
            checker.check(case, forged)
        self.assertIn("a witness of at least 2 world(s) is required", str(caught.exception))

    def test_no_admitted_reference_is_refused_when_worlds_exist(self):
        case = load("adaptive-beats-fixed-case.json")
        report = producer.build(case)
        forged = {"artifact_id": planner.ARTIFACT_ID, "version": planner.REPORT_VERSION,
                  "state": "no_admitted_reference", "reason": "invented",
                  "enclosure": report["enclosure"],
                  "improvement_criterion": report["decision"]["improvement_criterion"]}
        with self.assertRaises(checker.PlanRefused) as caught:
            checker.check(case, forged)
        self.assertIn("the case declares 4 joint worlds", str(caught.exception))

    def test_an_unknown_state_is_refused(self):
        case = load("adaptive-beats-fixed-case.json")
        with self.assertRaises(checker.PlanRefused):
            checker.check(case, {"state": "looks_fine"})


class TheSixConsumerForgeries(unittest.TestCase):
    """Reproduced from an Engine consumer review of checker 0.1.0.

    All six were ACCEPTED by checker 0.1.0. Each is reconstructed here from this
    lane's own retained cases, which are byte identical to the ones the consumer
    used, so the regression does not depend on a private packet. Version 0.1.0
    verified the plan tree and took the reported enclosure, criterion and witness
    identities on trust in every state but `resolvable`. The repair recomputes
    every stated fact and verifies that a witness names real, distinct, declared
    worlds.
    """

    def honest(self, name):
        case = load(name)
        return case, planner.plan(case), producer.build(case)

    def refuse(self, case, forged):
        with self.assertRaises(checker.PlanRefused) as caught:
            checker.check(case, forged)
        return str(caught.exception)

    def test_one_an_altered_open_enclosure_is_refused(self):
        case, honest, _ = self.honest("open-two-anchor.json")
        forged = dict(honest, enclosure={"lower": "100", "upper": "100"})
        self.assertIn("the report states enclosure", self.refuse(case, forged))

    def test_two_an_altered_open_criterion_is_refused(self):
        case, honest, _ = self.honest("open-two-anchor.json")
        forged = dict(honest, improvement_criterion="supported")
        self.assertIn("the cohort packet computes", self.refuse(case, forged))

    def test_three_an_altered_adaptive_criterion_is_refused(self):
        case, honest, _ = self.honest("adaptive-beats-fixed-case.json")
        forged = dict(honest, improvement_criterion="supported")
        self.assertIn("the cohort packet computes", self.refuse(case, forged))

    def test_four_an_invented_witness_identity_is_refused(self):
        case, honest, _ = self.honest("geometry-ambiguity-plan-case.json")
        forged = dict(honest, witness_cell=["invented_a", "invented_b"])
        self.assertIn("which the case does not declare", self.refuse(case, forged))

    def test_five_a_false_single_world_state_is_refused(self):
        case, honest, _ = self.honest("geometry-ambiguity-plan-case.json")
        forged = dict(honest, state="undecided_single_world", witness_cell=[])
        self.assertIn("a witness of at least 1 world(s) is required",
                      self.refuse(case, forged))

    def test_five_b_a_two_world_cell_is_not_a_single_world(self):
        case, honest, _ = self.honest("geometry-ambiguity-plan-case.json")
        forged = dict(honest, state="undecided_single_world")
        message = self.refuse(case, forged)
        self.assertTrue("names 2 worlds" in message or "every anchor finite" in message, message)

    def test_six_a_zero_world_case_may_not_claim_ambiguity(self):
        case, honest, report = self.honest("open-two-anchor.json")
        forged = dict(honest, state="unresolvable_by_declared_questions",
                      witness_cell=["invented_a", "invented_b"],
                      indistinguishable_world_groups=[["invented_a", "invented_b"]])
        self.assertIn("the case declares none", self.refuse(case, forged))

    def test_a_repeated_witness_world_is_refused(self):
        case, honest, _ = self.honest("geometry-ambiguity-plan-case.json")
        name = honest["witness_cell"][0]
        forged = dict(honest, witness_cell=[name, name])
        self.assertIn("repeats a world", self.refuse(case, forged))

    def test_the_advertised_interface_version_is_the_emitted_one(self):
        """The exchange advertised 0.2.0 while the report carried no version at all."""
        case, honest, _ = self.honest("adaptive-beats-fixed-case.json")
        self.assertEqual(honest["artifact_id"], checker.ARTIFACT_ID)
        self.assertIn(honest["version"], checker.ACCEPTED_REPORT_VERSIONS)
        forged = dict(honest, version="0.2.0")
        self.assertIn("interface version", self.refuse(case, forged))

    def test_seven_a_decided_and_divisible_witness_is_refused_on_a_blocked_report(self):
        """Consumer probe: 0.2.0 checked the obstruction premises for a geometry
        ambiguity and for no other state, so a blocked report could name a cell
        that was both decided and separated by a permitted question."""
        case = load("constructed-withheld-witness.json")
        honest = planner.plan(case)
        self.assertEqual(honest["state"], "blocked_by_unanswerable_questions")
        forged = dict(honest, witness_cell=["w1", "w2"],
                      withheld_questions=[{"anchor": "anchor_a", "object": "Y"}])
        self.assertEqual(checker._criterion(case, {"w1", "w2"}), "supported")
        with self.assertRaises(checker.PlanRefused) as caught:
            checker.check(case, forged)
        self.assertIn("witnesses no obstruction", str(caught.exception))

    def test_seven_b_a_separable_witness_is_refused_even_when_undecided(self):
        case = load("constructed-withheld-witness.json")
        honest = planner.plan(case)
        forged = dict(honest, witness_cell=["w0", "w2"],
                      withheld_questions=[{"anchor": "anchor_a", "object": "Y"}])
        with self.assertRaises(checker.PlanRefused) as caught:
            checker.check(case, forged)
        self.assertIn("witnesses no obstruction", str(caught.exception))

    def test_eight_a_report_without_identity_is_refused(self):
        """Consumer probe: absent artifact_id and version were accepted."""
        case = load("adaptive-beats-fixed-case.json")
        honest = planner.plan(case)
        for missing, phrase in (("artifact_id", "declares no artifact_id"),
                                ("version", "declares no interface version")):
            forged = {k: v for k, v in honest.items() if k != missing}
            with self.subTest(missing=missing):
                with self.assertRaises(checker.PlanRefused) as caught:
                    checker.check(case, forged)
                self.assertIn(phrase, str(caught.exception))

    def test_every_witnessed_state_shares_one_obstruction_contract(self):
        """The premises are checked in one place so no state can omit them."""
        source = open(os.path.join(os.path.dirname(os.path.abspath(checker.__file__)),
                                   "check_resolution_plan.py"), encoding="utf-8").read()
        call_sites = source.count("_verify_obstruction(case, cell, questions")
        definitions = source.count("def _verify_obstruction(")
        self.assertEqual(definitions, 1)
        self.assertEqual(call_sites - definitions, 4)

    def test_the_three_honest_reports_are_still_accepted(self):
        for name in ("open-two-anchor.json", "adaptive-beats-fixed-case.json",
                     "geometry-ambiguity-plan-case.json"):
            case, honest, _ = self.honest(name)
            with self.subTest(case=name):
                checker.check(case, honest)


if __name__ == "__main__":
    unittest.main()
