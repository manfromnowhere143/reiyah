"""Tests for the exact resolution planner, including an independent minimality check."""
from fractions import Fraction
from itertools import combinations
import json
import os
import unittest

import cohort_packet as producer
import resolution_plan as planner

CASES = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "research", "cohort-packet", "0.1.0")

LOSS = {"false_negative": "1", "false_positive": "1", "tolerance": "1/10"}
POS = {"b0": Fraction(0), "c0": Fraction(3), "k": Fraction(3, 2), "d": Fraction(-1)}


def trap_case():
    def side(present):
        objs = ["k", "d"] if present else ["k"]
        return {"objects_present": objs,
                "edges": [[x, y] for x in ("b0", "c0") for y in objs if abs(POS[x] - POS[y]) < 2]}
    return {"schema_id": "reiyah.cohort-packet.case", "cohort_id": "trap", "loss": dict(LOSS),
            "anchors": [{"id": "A", "weight": "1", "reference_state": "finite",
                         "base_detections": [{"id": "b0", "class": "car"}],
                         "added_detections": [{"id": "c0", "class": "car"}],
                         "objects": [{"id": "k", "class": "car"}, {"id": "d", "class": "car"}]}],
            "joint_worlds": [{"world_id": "absent", "per_anchor": {"A": side(False)}},
                             {"world_id": "present", "per_anchor": {"A": side(True)}}]}


def geometry_ambiguity_case():
    """Two worlds that agree on which objects exist and differ only on admitted edges."""
    anchor = {"id": "A", "weight": "1", "reference_state": "finite",
              "base_detections": [{"id": "b0", "class": "car"}],
              "added_detections": [{"id": "c0", "class": "car"}],
              "objects": [{"id": "k", "class": "car"}, {"id": "d", "class": "car"}]}
    reachable = {"objects_present": ["k", "d"],
                 "edges": [["b0", "k"], ["c0", "k"], ["b0", "d"]]}
    unreachable = {"objects_present": ["k", "d"], "edges": [["b0", "k"], ["c0", "k"]]}
    return {"schema_id": "reiyah.cohort-packet.case", "cohort_id": "geometry-ambiguity",
            "loss": dict(LOSS), "anchors": [anchor],
            "joint_worlds": [{"world_id": "d_reachable", "per_anchor": {"A": reachable}},
                             {"world_id": "d_unreachable", "per_anchor": {"A": unreachable}}]}


def multi_question_case():
    """Three independent copies, so no single question can decide."""
    anchor = {"id": "A", "weight": "1", "reference_state": "finite",
              "base_detections": [{"id": f"b{i}", "class": "car"} for i in range(3)],
              "added_detections": [{"id": f"c{i}", "class": "car"} for i in range(3)],
              "objects": [{"id": f"k{i}", "class": "car"} for i in range(3)]
                         + [{"id": f"d{i}", "class": "car"} for i in range(3)]}
    offset = {f"b{i}": Fraction(6 * i) for i in range(3)}
    offset.update({f"c{i}": Fraction(6 * i + 3) for i in range(3)})
    offset.update({f"k{i}": Fraction(6 * i) + Fraction(3, 2) for i in range(3)})
    offset.update({f"d{i}": Fraction(6 * i) - 1 for i in range(3)})

    def side(mask):
        objs = [f"k{i}" for i in range(3)] + [f"d{i}" for i in range(3) if mask[i]]
        dets = [f"b{i}" for i in range(3)] + [f"c{i}" for i in range(3)]
        return {"objects_present": objs,
                "edges": [[d, o] for d in dets for o in objs if abs(offset[d] - offset[o]) < 2]}

    worlds = []
    for bits in range(8):
        mask = [bool(bits >> i & 1) for i in range(3)]
        worlds.append({"world_id": "m" + "".join("1" if m else "0" for m in mask),
                       "per_anchor": {"A": side(mask)}})
    return {"schema_id": "reiyah.cohort-packet.case", "cohort_id": "three-copies",
            "loss": dict(LOSS), "anchors": [anchor], "joint_worlds": worlds}


def minimum_fixed_resolving_set(case):
    """Independent brute force: smallest set of questions that decides every cell.

    Non-adaptive, enumerated directly over question subsets rather than by the
    planner's recursion, so agreement is evidence about the quantity.
    """
    questions = planner.presence_questions(case)
    worlds = [w["world_id"] for w in case["joint_worlds"]]
    for size in range(0, len(questions) + 1):
        for chosen in combinations(range(len(questions)), size):
            cells = {}
            for world in worlds:
                key = tuple(world in questions[i]["yes"] for i in chosen)
                cells.setdefault(key, []).append(world)
            if all(planner.criterion_for(case, set(group)) != "unresolved"
                   for group in cells.values()):
                return size
    return None


class Planning(unittest.TestCase):
    def test_matching_trap_needs_one_observation_and_names_it(self):
        result = planner.plan(trap_case())
        self.assertEqual(result["state"], "resolvable")
        self.assertEqual(result["worst_case_observations"], 1)
        self.assertEqual(result["first_question"], {"anchor": "A", "object": "d"})

    def test_geometry_ambiguity_is_unresolvable_by_presence_questions(self):
        result = planner.plan(geometry_ambiguity_case())
        self.assertEqual(result["state"], "unresolvable_by_declared_questions")
        self.assertEqual(result["indistinguishable_world_groups"],
                         [["d_reachable", "d_unreachable"]])
        self.assertIsNone(minimum_fixed_resolving_set(geometry_ambiguity_case()))

    def test_three_copies_need_more_than_one(self):
        case = multi_question_case()
        result = planner.plan(case)
        self.assertEqual(result["state"], "resolvable")
        self.assertGreater(result["worst_case_observations"], 1)

    def test_adaptive_depth_never_exceeds_the_brute_force_fixed_set(self):
        """A fixed resolving set is one valid strategy, so the optimum is at most its size."""
        for case in (trap_case(), multi_question_case()):
            fixed = minimum_fixed_resolving_set(case)
            self.assertIsNotNone(fixed)
            result = planner.plan(case)
            self.assertLessEqual(result["worst_case_observations"], fixed)

    def test_the_named_first_question_really_decides_both_branches_when_depth_is_one(self):
        case = trap_case()
        result = planner.plan(case)
        self.assertEqual(result["worst_case_observations"], 1)
        node = result["plan"]
        for branch in ("if_present", "if_absent"):
            self.assertEqual(node[branch]["depth"], 0)
            self.assertIn(node[branch]["decided"], ("supported", "excluded"))

    def test_no_probability_or_expectation_is_reported(self):
        text = repr(planner.plan(trap_case()))
        for word in ("probability", "prior", "expected", "likelihood"):
            self.assertNotIn(word, text)

    def test_an_already_decided_cohort_needs_no_observation(self):
        case = trap_case()
        case["loss"]["tolerance"] = "5"
        result = planner.plan(case)
        self.assertEqual(result["worst_case_observations"], 0)
        self.assertIsNone(result["first_question"])

    def test_resource_bound_is_enforced_before_searching(self):
        case = multi_question_case()
        original = planner.MAX_QUESTIONS
        planner.MAX_QUESTIONS = 1
        try:
            with self.assertRaises(planner.CaseError):
                planner.plan(case)
        finally:
            planner.MAX_QUESTIONS = original


class AnEmptyPopulationIsNotAnAmbiguousOne(unittest.TestCase):
    """Retained defect from version 0.1.0.

    A cohort with no admitted joint world was reported as
    `unresolvable_by_declared_questions`, with an empty list of
    indistinguishable worlds and a reason describing worlds that could not be
    told apart. There were no worlds. The absence of a reference basis was
    dressed up as an observed property of a model that had never been stated.
    """

    def case(self):
        path = os.path.join(CASES, "open-two-anchor.json")
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def test_zero_admitted_worlds_is_reported_as_a_missing_reference(self):
        result = planner.plan(self.case())
        self.assertEqual(result["state"], "no_admitted_reference")

    def test_zero_admitted_worlds_is_never_called_geometry_ambiguity(self):
        result = planner.plan(self.case())
        self.assertNotEqual(result["state"], "unresolvable_by_declared_questions")
        for word in ("indistinguishable", "cannot separate", "differ only"):
            self.assertNotIn(word, result["reason"])

    def test_the_conditional_count_bound_is_preserved(self):
        result = planner.plan(self.case())
        self.assertEqual(result["enclosure"], {"lower": "-8", "upper": "8"})
        self.assertEqual(result["improvement_criterion"], "unresolved")

    def test_the_missing_prerequisite_is_named_rather_than_implied(self):
        result = planner.plan(self.case())
        self.assertIn("reference", result["prerequisite"])

    def test_an_ambiguity_claim_must_carry_a_witness_of_two_or_more_worlds(self):
        path = os.path.join(CASES, "geometry-ambiguity-plan-case.json")
        with open(path, "r", encoding="utf-8") as handle:
            finite = json.load(handle)
        result = planner.plan(finite)
        self.assertEqual(result["state"], "unresolvable_by_declared_questions")
        self.assertGreaterEqual(len(result["witness_cell"]), 2)
        self.assertEqual(planner.criterion_for(finite, set(result["witness_cell"])),
                         "unresolved")


class AnUnanswerableQuestionIsNotAFreeOne(unittest.TestCase):
    """The depth is a guarantee only under a declared answer model."""

    def case(self):
        path = os.path.join(CASES, "adaptive-beats-fixed-case.json")
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def test_the_answer_model_is_reported_as_an_assumption(self):
        result = planner.plan(self.case())
        self.assertIn("not an observation", result["answer_model"]["status"])

    def test_marking_a_question_unanswerable_removes_it_from_the_plan(self):
        case = self.case()
        for anchor in case["anchors"]:
            if anchor["id"] == "B":
                for entry in anchor["objects"]:
                    if entry["id"] == "B_d":
                        entry["answerable"] = False
        result = planner.plan(case)
        asked = {(q["anchor"], q["object"]) for q in planner.presence_questions(case)}
        self.assertNotIn(("B", "B_d"), asked)
        self.assertNotEqual(result.get("first_question"),
                            {"anchor": "B", "object": "B_d"})

    def test_removing_answerable_questions_can_make_the_comparison_unresolvable(self):
        case = self.case()
        for anchor in case["anchors"]:
            for entry in anchor["objects"]:
                if entry["id"].endswith("_d") and anchor["id"] in ("A", "C"):
                    entry["answerable"] = False
        result = planner.plan(case)
        self.assertEqual(result["state"], "blocked_by_unanswerable_questions")
        self.assertGreaterEqual(len(result["witness_cell"]), 2)
        self.assertTrue(result["withheld_questions"])

    def test_an_unanswerable_obstacle_is_not_reported_as_an_ambiguous_reference(self):
        """The two causes are different and the wrong one is the flattering one."""
        case = self.case()
        for anchor in case["anchors"]:
            for entry in anchor["objects"]:
                if entry["id"].endswith("_d") and anchor["id"] in ("A", "C"):
                    entry["answerable"] = False
        result = planner.plan(case)
        self.assertNotEqual(result["state"], "unresolvable_by_declared_questions")
        self.assertIn("observation procedure", result["reason"])


if __name__ == "__main__":
    unittest.main()
