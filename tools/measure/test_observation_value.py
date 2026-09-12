"""Tests for the observation classifier and the repaired preference check."""
from fractions import Fraction
import copy
import itertools
import unittest

import check_cohort_packet as checker
import cohort_packet as producer
import observation_value as value

POS = {"b0": Fraction(0), "c0": Fraction(3), "k": Fraction(3, 2), "d": Fraction(-1)}
LOSS = {"false_negative": "1", "false_positive": "1", "tolerance": "1/10"}


def trap_case():
    """Base and addition compete for one object; a disputed object only the base reaches."""
    def side(present):
        objs = ["k", "d"] if present else ["k"]
        return {"objects_present": objs,
                "edges": [[d, o] for d in ("b0", "c0") for o in objs if abs(POS[d] - POS[o]) < 2]}
    anchor = {"id": "A", "weight": "1", "reference_state": "finite",
              "base_detections": [{"id": "b0", "class": "car"}],
              "added_detections": [{"id": "c0", "class": "car"}],
              "objects": [{"id": "k", "class": "car"}, {"id": "d", "class": "car"}]}
    return {"schema_id": "reiyah.cohort-packet.case", "cohort_id": "trap", "loss": dict(LOSS),
            "anchors": [anchor],
            "joint_worlds": [{"world_id": "absent", "per_anchor": {"A": side(False)}},
                             {"world_id": "present", "per_anchor": {"A": side(True)}}]}


def separated_case():
    """Same disputed object, but the addition has its own object, so nothing competes."""
    anchor = {"id": "A", "weight": "1", "reference_state": "finite",
              "base_detections": [{"id": "b0", "class": "car"}],
              "added_detections": [{"id": "c0", "class": "car"}],
              "objects": [{"id": "n0", "class": "car"}, {"id": "n3", "class": "car"},
                          {"id": "far", "class": "car"}, {"id": "d", "class": "car"}]}

    def world(name, far, disputed):
        objs = ["n0", "n3"] + (["far"] if far else []) + (["d"] if disputed else [])
        edges = [["b0", "n0"], ["c0", "n3"]] + ([["b0", "d"]] if disputed else [])
        return {"world_id": name, "per_anchor": {"A": {"objects_present": objs, "edges": edges}}}

    return {"schema_id": "reiyah.cohort-packet.case", "cohort_id": "separated", "loss": dict(LOSS),
            "anchors": [anchor],
            "joint_worlds": [world("no_far_no_d", False, False), world("far_no_d", True, False),
                             world("no_far_d", False, True), world("far_d", True, True)]}


class Classification(unittest.TestCase):
    def test_a_competing_disputed_object_is_decisive(self):
        result = value.classify(trap_case())
        rows = {row["object"]: row for row in result["questions"]}
        self.assertEqual(rows["k"]["classification"], "already_settled")
        self.assertEqual(rows["d"]["classification"], "decisive")
        self.assertEqual(rows["d"]["cells"]["absent"]["improvement_criterion"], "excluded")
        self.assertEqual(rows["d"]["cells"]["present"]["improvement_criterion"], "supported")

    def test_an_unreachable_object_is_inert(self):
        result = value.classify(separated_case())
        rows = {row["object"]: row for row in result["questions"]}
        self.assertEqual(rows["far"]["classification"], "inert")

    def test_the_same_object_is_decisive_or_inert_by_geometry_not_identity(self):
        """Relevance is a property of the local matching structure, not of the object."""
        trap = {r["object"]: r["classification"] for r in value.classify(trap_case())["questions"]}
        sep = {r["object"]: r["classification"] for r in value.classify(separated_case())["questions"]}
        self.assertEqual(trap["d"], "decisive")
        self.assertEqual(sep["d"], "inert")

    def test_inert_classification_survives_exhaustive_falsification(self):
        """Resolving an inert question must not move the enclosure on any admitted subset."""
        case = separated_case()
        ids = [w["world_id"] for w in case["joint_worlds"]]
        far_present = {"far_no_d", "far_d"}
        checked = changed = 0
        for size in range(1, len(ids) + 1):
            for subset in itertools.combinations(ids, size):
                chosen = set(subset)
                cells = (chosen & far_present, chosen - far_present)
                if not all(cells):
                    continue
                whole = dict(case)
                whole["joint_worlds"] = [w for w in case["joint_worlds"] if w["world_id"] in chosen]
                reference = producer.build(whole)["enclosure"]
                for cell in cells:
                    part = dict(case)
                    part["joint_worlds"] = [w for w in case["joint_worlds"]
                                            if w["world_id"] in cell]
                    checked += 1
                    if producer.build(part)["enclosure"] != reference:
                        changed += 1
        self.assertGreater(checked, 10)
        self.assertEqual(changed, 0)

    def test_no_probability_is_asserted(self):
        """The ordering is by exact effect; no prior over interpretations exists."""
        result = value.classify(trap_case())
        text = repr(result)
        for word in ("probability", "prior", "expected_value", "likelihood"):
            self.assertNotIn(word, text)


class PreferenceIsChecked(unittest.TestCase):
    """Version 0.1.0 emitted a preference and never verified it."""

    def setUp(self):
        self.case = trap_case()
        self.report = producer.build(self.case)
        checker.verify(self.case, self.report)

    def test_forged_preference_is_refused(self):
        for bogus in ("prefer_augmented", "prefer_base", "equivalent_within_tolerance"):
            forged = copy.deepcopy(self.report)
            forged["decision"]["preference"] = bogus
            with self.assertRaises(checker.Rejected) as caught:
                checker.verify(self.case, forged)
            self.assertIn("preference does not follow", str(caught.exception))

    def test_honest_preference_is_confirmed(self):
        outcome = checker.verify(self.case, self.report)
        self.assertEqual(outcome["preference"], "unresolved")

    def test_unresolved_cohort_must_pair_not_evaluated(self):
        case = trap_case()
        case["joint_worlds"] = []
        report = producer.build(case)
        checker.verify(case, report)
        forged = copy.deepcopy(report)
        forged["decision"]["preference"] = "prefer_augmented"
        with self.assertRaises(checker.Rejected):
            checker.verify(case, forged)

    def test_preference_agrees_with_the_declared_rule_across_tolerances(self):
        for tol, lo, hi, expect in (("1/10", "-1", "1", "unresolved"),
                                    ("5", "-1", "1", "equivalent_within_tolerance")):
            case = trap_case()
            case["loss"]["tolerance"] = tol
            report = producer.build(case)
            self.assertEqual(report["enclosure"], {"lower": lo, "upper": hi})
            self.assertEqual(report["decision"]["preference"], expect)
            checker.verify(case, report)


if __name__ == "__main__":
    unittest.main()
