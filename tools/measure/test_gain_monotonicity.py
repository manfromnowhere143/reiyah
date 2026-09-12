"""Tests for the gain monotonicity theorem and for the limit of its hypothesis."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cohort_packet as packet  # noqa: E402
import check_resolution_plan as checker  # noqa: E402
import gain_monotonicity as theorem  # noqa: E402
import resolution_plan as planner  # noqa: E402

CASES = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "research", "cohort-packet", "0.1.0")


def load(name):
    with open(os.path.join(CASES, name), "r", encoding="utf-8") as handle:
        return json.load(handle)


TRAP = (["b0"], ["c0"], ["k", "d"],
        {("b0", "k"), ("b0", "d"), ("c0", "k")})


class EveryStepOfTheProof(unittest.TestCase):
    def test_the_defect_identity_holds(self):
        base, added, objects, edges = TRAP
        for present in theorem.subsets(objects):
            self.assertTrue(
                theorem.check_defect_identity(base, added, list(present), edges))

    def test_the_deficiency_function_is_supermodular(self):
        base, added, objects, edges = TRAP
        for present in theorem.subsets(objects):
            self.assertTrue(
                theorem.check_supermodular(base + added, list(present), edges))

    def test_a_base_maximizer_meets_a_full_maximizer_in_a_base_maximizer(self):
        base, added, objects, edges = TRAP
        for present in theorem.subsets(objects):
            self.assertTrue(
                theorem.check_intersection_lemma(base, added, list(present), edges))

    def test_the_conclusion_holds_on_every_small_instance(self):
        checked, failure = theorem.exhaustive(max_base=2, max_added=1, max_objects=3)
        self.assertIsNone(failure)
        self.assertGreater(checked, 600)

    def test_the_conclusion_holds_on_sampled_larger_instances(self):
        checked, failure = theorem.randomised(trials=40)
        self.assertIsNone(failure)
        self.assertEqual(checked, 40)


class TheHypothesisIsNecessary(unittest.TestCase):
    """The theorem holds for a fixed edge set. Worlds need not share one.

    An earlier version of this lane's document said a falling world value is
    something "the additive loss does not permit". That is true only when the
    worlds agree about which detection could have matched which object. They are
    not required to, and this case is the retained instance where they do not.
    """

    def case(self):
        return load("adaptive-beats-fixed-varying-edges-case.json")

    def test_the_value_falls_as_objects_are_added(self):
        report = packet.build(self.case())
        value = {w["world_id"]: w["finite_contribution"] for w in report["joint_worlds"]}
        present = {w["world_id"]: set(w["per_anchor"]["A"]["objects_present"])
                   for w in self.case()["joint_worlds"]}
        self.assertTrue(present["c_only"] < present["a_and_c"])
        self.assertEqual(value["c_only"], "1")
        self.assertEqual(value["a_and_c"], "-1")

    def test_the_two_worlds_disagree_about_the_edges(self):
        """The fall is bought with an edge disagreement, not with the loss."""
        edges = {w["world_id"]: {tuple(e) for e in w["per_anchor"]["A"]["edges"]}
                 for w in self.case()["joint_worlds"]}
        self.assertIn(("c0", "dC"), edges["c_only"])
        self.assertNotIn(("c0", "dC"), edges["a_and_c"])

    def test_a_single_edge_set_would_have_forbidden_it(self):
        """Fixing either world's edges restores monotonicity, as the theorem says."""
        base, added, objects = ["b0"], ["c0"], ["k", "dA", "dC"]
        for edges in ({("b0", "k"), ("c0", "dC")},
                      {("b0", "k"), ("b0", "dA"), ("b0", "dC")}):
            with self.subTest(edges=sorted(edges)):
                self.assertIsNone(theorem.check_instance(base, added, objects, edges))

    def test_it_is_still_a_strict_adaptive_gap(self):
        case = self.case()
        result = planner.plan(case)
        findings = checker.check(case, result)
        self.assertEqual(result["worst_case_observations"], 2)
        self.assertEqual(findings["minimum_fixed_resolving_set"]["size"], 3)

    def test_the_gap_is_reached_with_one_anchor_and_four_worlds(self):
        case = self.case()
        self.assertEqual(len(case["anchors"]), 1)
        self.assertEqual(len(case["joint_worlds"]), 4)


if __name__ == "__main__":
    unittest.main()
