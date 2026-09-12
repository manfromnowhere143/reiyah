"""Tests for worst group validation, including the defect it corrects in this lane."""
from fractions import Fraction
import copy
import json
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cohort_packet as packet  # noqa: E402
import worst_group as worst  # noqa: E402

CASES = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "research", "cohort-packet", "0.1.0")


def load(name):
    with open(os.path.join(CASES, name), "r", encoding="utf-8") as handle:
        return json.load(handle)


class TheAverageHidesAHarmedGroup(unittest.TestCase):
    """The defect this module corrects: a cohort report that is true and misleading."""

    def test_the_cohort_is_supported_while_a_group_is_harmed(self):
        result = worst.analyse(load("worst-group-masking-case.json"))
        self.assertEqual(result["cohort"]["criterion"], "supported")
        self.assertEqual(result["groups"]["low_light"]["criterion"], "excluded")
        self.assertEqual(result["groups"]["low_light"]["enclosure"],
                         {"lower": "-1", "upper": "-1"})

    def test_the_harmed_group_is_named_rather_than_left_to_be_noticed(self):
        result = worst.analyse(load("worst-group-masking-case.json"))
        self.assertEqual(result["masking"]["groups_excluded_while_the_cohort_is_supported"],
                         ["low_light"])
        self.assertIn("low_light", result["masking"]["finding"])

    def test_the_cohort_report_alone_would_not_have_said_so(self):
        """The number the cohort packet reports is correct, and not enough."""
        report = packet.build(load("worst-group-masking-case.json"))
        self.assertEqual(report["decision"]["improvement_criterion"], "supported")
        self.assertNotIn("low_light", json.dumps(report))


class TheWorstGroupMustBeFoundJointly(unittest.TestCase):
    """Separate per group enclosures lose a decisive negative result."""

    def test_each_group_alone_is_unresolved(self):
        result = worst.analyse(load("worst-group-flip-case.json"))
        for name in ("group_a", "group_b"):
            self.assertEqual(result["groups"][name]["criterion"], "unresolved")
            self.assertEqual(result["groups"][name]["enclosure"],
                             {"lower": "-1", "upper": "1"})

    def test_jointly_some_group_is_harmed_in_every_admitted_reading(self):
        result = worst.analyse(load("worst-group-flip-case.json"))
        self.assertEqual(result["worst_group_enclosure"],
                         {"lower": "-1", "upper": "-1", "criterion": "excluded"})

    def test_the_separate_view_is_strictly_wider_and_is_labelled_a_relaxation(self):
        result = worst.analyse(load("worst-group-flip-case.json"))
        relaxation = result["separate_group_relaxation"]
        self.assertTrue(relaxation["strictly_wider"])
        self.assertEqual((relaxation["lower"], relaxation["upper"]), ("-1", "1"))
        self.assertIn("never the answer", relaxation["status"])

    def test_the_worst_group_differs_between_the_two_readings(self):
        result = worst.analyse(load("worst-group-flip-case.json"))
        chosen = {row["world_id"]: row["worst_group"]
                  for row in result["per_world_worst_group"]}
        self.assertEqual(chosen["a_helped"], "group_b")
        self.assertEqual(chosen["b_helped"], "group_a")


class TheRelaxationInequalityHoldsGenerally(unittest.TestCase):
    """Lower ends agree; the separate upper end is never below the joint one."""

    def grouped_case(self, rng):
        case = copy.deepcopy(load("worst-group-flip-case.json"))
        for anchor in case["anchors"]:
            anchor["group"] = rng.choice(["g0", "g1"])
        for world in case["joint_worlds"]:
            for anchor in case["anchors"]:
                present = rng.random() < 0.5
                aid = anchor["id"]
                world["per_anchor"][aid] = (
                    {"objects_present": [f"{aid}_k", f"{aid}_d"],
                     "edges": [[f"{aid}_b0", f"{aid}_k"], [f"{aid}_b0", f"{aid}_d"],
                               [f"{aid}_c0", f"{aid}_k"]]} if present else
                    {"objects_present": [f"{aid}_k"],
                     "edges": [[f"{aid}_b0", f"{aid}_k"], [f"{aid}_c0", f"{aid}_k"]]})
        return case

    def test_on_random_grouped_cohorts(self):
        rng = random.Random(20260912)
        strict = 0
        for _ in range(200):
            result = worst.analyse(self.grouped_case(rng))
            joint = result["worst_group_enclosure"]
            relaxed = result["separate_group_relaxation"]
            self.assertEqual(Fraction(relaxed["lower"]), Fraction(joint["lower"]))
            self.assertGreaterEqual(Fraction(relaxed["upper"]), Fraction(joint["upper"]))
            if Fraction(relaxed["upper"]) > Fraction(joint["upper"]):
                strict += 1
        self.assertGreater(strict, 0)


class ItReducesToTheCohortWhenThereIsOneGroup(unittest.TestCase):
    def test_an_ungrouped_cohort_has_a_worst_group_equal_to_itself(self):
        for name in ("oppositely-coupled.json", "adaptive-beats-fixed-case.json",
                     "matching-trap-plan-case.json"):
            result = worst.analyse(load(name))
            with self.subTest(case=name):
                self.assertEqual(list(result["groups"]), [worst.UNGROUPED])
                self.assertEqual(result["worst_group_enclosure"]["lower"],
                                 result["cohort"]["enclosure"]["lower"])
                self.assertEqual(result["worst_group_enclosure"]["upper"],
                                 result["cohort"]["enclosure"]["upper"])

    def test_no_masking_is_reported_when_there_is_nothing_to_mask(self):
        result = worst.analyse(load("oppositely-coupled.json"))
        self.assertEqual(result["masking"]["groups_excluded_while_the_cohort_is_supported"], [])


class ItRefusesAGroupItCannotValue(unittest.TestCase):
    def test_a_zero_weight_group_is_refused(self):
        case = load("worst-group-flip-case.json")
        case["anchors"][0]["weight"] = "0"
        case["anchors"][1]["weight"] = "1"
        with self.assertRaises(packet.CaseError) as caught:
            worst.analyse(case)
        self.assertIn("zero total weight", str(caught.exception))

    def test_a_group_that_is_not_a_name_is_refused(self):
        case = load("worst-group-flip-case.json")
        case["anchors"][0]["group"] = 7
        with self.assertRaises(packet.CaseError):
            worst.analyse(case)

    def test_the_scope_says_groups_are_declared_and_not_discovered(self):
        result = worst.analyse(load("worst-group-flip-case.json"))
        self.assertIn("does not discover groups", result["scope"])


if __name__ == "__main__":
    unittest.main()
