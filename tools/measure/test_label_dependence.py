"""Tests for the label dependence families, their checker and the forgeries it refuses.

The real case is another owner's private export, so the tests that need it are
skipped unless REIYAH_ANNOTATION_CASE points at it. Everything else runs on cases
built here, including the arithmetic that the real result depends on.
"""
import copy
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_label_dependence as checker  # noqa: E402
import cohort_packet as packet  # noqa: E402
import label_dependence as dependence  # noqa: E402

CASE = os.environ.get("REIYAH_ANNOTATION_CASE")
OPERANDS = os.environ.get("REIYAH_OPERANDS")
SECOND = os.environ.get("REIYAH_SECOND_CASE")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DELETION = os.path.join(ROOT, "research", "label-dependence", "0.1.0", "deletion-family.json")
INSERTION = os.path.join(ROOT, "research", "label-dependence", "0.2.0", "insertion-family.json")


def carrier_case():
    """One anchor whose whole gain rests on a single label, and one that does not.

    The added detection reaches `o2` and nothing else does, so deleting `o2` costs
    exactly one unit of gain. `o0` and `o1` are reachable by both configurations,
    so deleting either is absorbed by reassignment.
    """
    return {
        "schema_id": "reiyah.cohort-packet.case", "cohort_id": "carrier",
        "loss": {"false_negative": "1", "false_positive": "1", "tolerance": "1/10"},
        "anchors": [{"id": "A", "weight": "1", "reference_state": "finite",
                     "base_detections": [{"id": "b0", "class": "car"},
                                         {"id": "b1", "class": "car"}],
                     "added_detections": [{"id": "c0", "class": "car"}],
                     "objects": [{"id": "o0", "class": "car"}, {"id": "o1", "class": "car"},
                                 {"id": "o2", "class": "car"}]}],
        "joint_worlds": [{"world_id": "labels", "per_anchor": {"A": {
            "objects_present": ["o0", "o1", "o2"],
            "edges": [["b0", "o0"], ["b1", "o1"], ["c0", "o2"]]}}}],
    }


class Arithmetic(unittest.TestCase):
    def test_a_single_carrier_label_flips_the_criterion(self):
        case = carrier_case()
        baseline = dependence.evaluate(case)
        self.assertEqual(baseline["weighted_delta"], "1")
        self.assertEqual(baseline["criterion"], "supported")
        without = dependence.evaluate(dependence.without(case, "A", "o2"))
        self.assertEqual(without["weighted_delta"], "-1")
        self.assertEqual(without["criterion"], "excluded")

    def test_reassignment_absorbs_a_deletion_that_is_not_a_carrier(self):
        case = carrier_case()
        case["joint_worlds"][0]["per_anchor"]["A"]["edges"].append(["c0", "o0"])
        baseline = dependence.evaluate(case)
        after = dependence.evaluate(dependence.without(case, "A", "o0"))
        self.assertEqual(baseline["per_anchor"]["A"]["tp_augmented"], 3)
        self.assertEqual(after["per_anchor"]["A"]["tp_augmented"], 2)
        self.assertEqual(after["per_anchor"]["A"]["tp_base"], 1)

    def test_deleting_a_label_removes_it_from_every_world_and_edge(self):
        case = carrier_case()
        edited = dependence.without(case, "A", "o1")
        self.assertNotIn("o1", [o["id"] for o in edited["anchors"][0]["objects"]])
        body = edited["joint_worlds"][0]["per_anchor"]["A"]
        self.assertNotIn("o1", body["objects_present"])
        self.assertTrue(all(edge[1] != "o1" for edge in body["edges"]))
        packet.build(edited)

    def test_the_checker_reaches_the_same_numbers_by_its_own_matcher(self):
        case = carrier_case()
        mine = dependence.evaluate(case)
        theirs = checker.decide(case)
        self.assertEqual(mine["weighted_delta"], theirs["weighted_delta"])
        self.assertEqual(mine["criterion"], theirs["criterion"])
        self.assertEqual(mine["per_anchor"]["A"]["tp_augmented"],
                         theirs["per_anchor"]["A"]["tp_augmented"])

    def test_an_insertion_at_an_unmatched_detection_can_only_help_that_configuration(self):
        from fractions import Fraction
        case = carrier_case()
        case["joint_worlds"][0]["per_anchor"]["A"]["edges"] = [["b0", "o0"], ["b1", "o1"]]
        coordinates = {"A": {"b0": (Fraction(0), Fraction(0)), "b1": (Fraction(10), Fraction(0)),
                             "c0": (Fraction(20), Fraction(0))}}
        candidates = dependence.unmatched_detections(case)
        self.assertTrue(any(c["detection"] == "c0" for c in candidates))
        target = next(c for c in candidates if c["detection"] == "c0")
        before = dependence.evaluate(case)
        after = dependence.evaluate(dependence.with_insertions(case, [target], coordinates))
        self.assertGreater(float(after["weighted_delta"]), float(before["weighted_delta"]))

    def test_the_insertion_rule_is_a_distance_and_not_a_graph_neighbourhood(self):
        """The consumer's control: two detections sharing an object, 3 metres apart."""
        from fractions import Fraction
        case = {
            "schema_id": "reiyah.cohort-packet.case", "cohort_id": "insertion-geometry-control",
            "loss": {"false_negative": "1", "false_positive": "1", "tolerance": "0"},
            "anchors": [{"id": "A", "weight": "1", "reference_state": "finite",
                         "base_detections": [{"id": "d_left", "class": "car"}],
                         "added_detections": [{"id": "d_right", "class": "car"}],
                         "objects": [{"id": "o_mid", "class": "car"}]}],
            "joint_worlds": [{"world_id": "labels", "per_anchor": {"A": {
                "objects_present": ["o_mid"],
                "edges": [["d_left", "o_mid"], ["d_right", "o_mid"]]}}}]}
        coordinates = {"A": {"d_left": (Fraction(0), Fraction(0)),
                             "d_right": (Fraction(3), Fraction(0))}}
        target = [c for c in dependence.unmatched_detections(case)
                  if c["detection"] == "d_right"]
        edited = dependence.with_insertions(case, target, coordinates)
        new = [e for e in edited["joint_worlds"][0]["per_anchor"]["A"]["edges"]
               if e[1].startswith("inserted-")]
        self.assertEqual(new, [["d_right", "inserted-0"]])

    def test_a_partial_coordinate_map_is_refused_not_silently_used(self):
        """A map missing a same class detection drops an eligible edge."""
        from fractions import Fraction
        case = {
            "schema_id": "reiyah.cohort-packet.case", "cohort_id": "partial-map-control",
            "loss": {"false_negative": "1", "false_positive": "1", "tolerance": "0"},
            "anchors": [{"id": "A", "weight": "1", "reference_state": "finite",
                         "base_detections": [{"id": "b_near", "class": "car"}],
                         "added_detections": [{"id": "c_here", "class": "car"}],
                         "objects": [{"id": "o0", "class": "car"}]}],
            "joint_worlds": [{"world_id": "labels", "per_anchor": {"A": {
                "objects_present": ["o0"], "edges": [["b_near", "o0"]]}}}]}
        target = [c for c in dependence.unmatched_detections(case)
                  if c["detection"] == "c_here"]
        complete = {"A": {"b_near": (Fraction(1), Fraction(0)),
                          "c_here": (Fraction(0), Fraction(0))}}
        edges = [e for e in dependence.with_insertions(case, target, complete)
                 ["joint_worlds"][0]["per_anchor"]["A"]["edges"] if e[1].startswith("inserted-")]
        self.assertEqual(len(edges), 2)
        with self.assertRaises(dependence.GeometryRequired) as caught:
            dependence.with_insertions(case, target,
                                       {"A": {"c_here": (Fraction(0), Fraction(0))}})
        self.assertIn("partial map", str(caught.exception))

    def test_an_insertion_without_coordinates_is_refused_not_guessed(self):
        case = carrier_case()
        target = dependence.unmatched_detections(case)[:1] or [
            {"anchor": "A", "detection": "c0", "class": "car", "role": "added"}]
        with self.assertRaises(dependence.GeometryRequired):
            dependence.with_insertions(case, target, None)

    def test_the_three_outcomes_are_kept_apart(self):
        case = carrier_case()
        baseline, rows, results = dependence.family(case)
        events = dependence.classify(baseline, results, None)
        self.assertIn("strict_loss_sign_changes", events)
        self.assertIn("falls_to_zero_without_changing_sign", events)
        self.assertIn("tolerance_crossings", events)
        self.assertIn("changes_to_unresolved", events)


class FloorAndRatio(unittest.TestCase):
    """A comfortable margin can make robustness arithmetic rather than evidence."""

    def test_the_floor_follows_from_weights_penalties_and_margin(self):
        case = carrier_case()
        floor = dependence.arithmetic_floor(case)
        self.assertEqual(floor["margin"], "9/10")
        self.assertEqual(floor["largest_single_step"], "2")
        self.assertEqual(floor["k_floor"], 1)

    def test_a_wider_margin_raises_the_floor_so_no_single_deletion_can_cross(self):
        """The confound, in one case: breakdown 2, yet as fragile as arithmetic allows."""
        case = {
            "schema_id": "reiyah.cohort-packet.case", "cohort_id": "wide-margin",
            "loss": {"false_negative": "1", "false_positive": "1", "tolerance": "0"},
            "anchors": [{"id": "A", "weight": "1", "reference_state": "finite",
                         "base_detections": [],
                         "added_detections": [{"id": "c%d" % i, "class": "car"} for i in range(3)],
                         "objects": [{"id": "o%d" % i, "class": "car"} for i in range(3)]}],
            "joint_worlds": [{"world_id": "labels", "per_anchor": {"A": {
                "objects_present": ["o0", "o1", "o2"],
                "edges": [["c0", "o0"], ["c1", "o1"], ["c2", "o2"]]}}}]}
        floor = dependence.arithmetic_floor(case)
        self.assertEqual(floor["weighted_delta"], "3")
        self.assertEqual(floor["largest_single_step"], "2")
        self.assertEqual(floor["k_floor"], 2)
        for single in ("o0", "o1", "o2"):
            after = dependence.evaluate(dependence.without(case, "A", single))
            self.assertEqual(after["criterion"], "supported", single)
        result = dependence.breakdown(case)
        self.assertEqual(result["k_observed"], 2)
        self.assertTrue(result["at_the_arithmetic_floor"])
        self.assertEqual(result["fragility_ratio"], "1")

    def test_a_case_at_its_floor_is_reported_as_such(self):
        case = carrier_case()
        result = dependence.breakdown(case)
        self.assertEqual(result["state"], "found")
        self.assertEqual(result["k_observed"], 1)
        self.assertEqual(result["k_floor"], 1)
        self.assertTrue(result["at_the_arithmetic_floor"])
        self.assertEqual(result["fragility_ratio"], "1")

    def test_redundancy_shows_as_a_ratio_above_one(self):
        """Two labels each absorbed alone, decisive together. No pruning could find this."""
        case = {
            "schema_id": "reiyah.cohort-packet.case", "cohort_id": "redundant",
            "loss": {"false_negative": "1", "false_positive": "1", "tolerance": "1/10"},
            "anchors": [{"id": "A", "weight": "1", "reference_state": "finite",
                         "base_detections": [],
                         "added_detections": [{"id": "c0", "class": "car"}],
                         "objects": [{"id": "o0", "class": "car"}, {"id": "o1", "class": "car"}]}],
            "joint_worlds": [{"world_id": "labels", "per_anchor": {"A": {
                "objects_present": ["o0", "o1"],
                "edges": [["c0", "o0"], ["c0", "o1"]]}}}]}
        baseline = dependence.evaluate(case)
        self.assertEqual(baseline["criterion"], "supported")
        for single in ("o0", "o1"):
            self.assertEqual(
                dependence.evaluate(dependence.without(case, "A", single))["criterion"],
                "supported")
        result = dependence.breakdown(case)
        self.assertEqual(result["k_observed"], 2)
        self.assertEqual(result["k_floor"], 1)
        self.assertFalse(result["at_the_arithmetic_floor"])
        self.assertEqual(result["fragility_ratio"], "2")

    def test_the_search_brackets_rather_than_claims_past_its_budget(self):
        case = carrier_case()
        result = dependence.breakdown(case, budget=0)
        self.assertEqual(result["state"], "bracketed")
        self.assertIsNone(result["witness"])
        self.assertIn("no smallest set is claimed", result["conclusion"])


class Forgeries(unittest.TestCase):
    def setUp(self):
        self.case = carrier_case()
        baseline, rows, results = dependence.family(self.case)
        self.report = {
            "artifact_id": "reiyah.label-dependence.report",
            "baseline": baseline,
            "events": dependence.classify(baseline, results, None),
            "robust_under_this_family": False, "breakdown_number": 1}
        checker.verify(self.case, self.report)

    def refuse(self, mutate, fragment):
        forged = copy.deepcopy(self.report)
        mutate(forged)
        with self.assertRaises(checker.Rejected) as caught:
            checker.verify(self.case, forged)
        self.assertIn(fragment, str(caught.exception))

    def test_a_witness_that_does_not_flip_is_refused(self):
        def swap(forged):
            forged["events"]["tolerance_crossings"] = [
                {"anchor": "A", "local_index": 0, "class": "car", "weighted_delta": "-1"}]
        self.refuse(swap, "does not change the criterion")

    def test_a_witness_of_the_wrong_class_is_refused(self):
        def wrong(forged):
            forged["events"]["tolerance_crossings"][0]["class"] = "pedestrian"
        self.refuse(wrong, "not a pedestrian")

    def test_a_witness_outside_the_anchor_is_refused(self):
        def outside(forged):
            forged["events"]["tolerance_crossings"][0]["local_index"] = 99
        self.refuse(outside, "outside")

    def test_a_false_baseline_is_refused(self):
        self.refuse(lambda f: f["baseline"].__setitem__("weighted_delta", "5"),
                    "the case gives")

    def test_a_robustness_claim_contradicted_by_its_own_witness_is_refused(self):
        self.refuse(lambda f: f.__setitem__("robust_under_this_family", True),
                    "claims robustness while carrying a witness")

    def test_a_breakdown_of_one_with_no_witness_is_refused(self):
        def empty(forged):
            forged["events"]["tolerance_crossings"] = []
        self.refuse(empty, "breakdown number of one is claimed with no witness")

    def test_a_misreported_delta_is_refused(self):
        self.refuse(lambda f: f["events"]["tolerance_crossings"][0].__setitem__(
            "weighted_delta", "7"), "recomputes to")


@unittest.skipUnless(CASE and os.path.exists(CASE), "the owner's annotation case is not supplied")
class TheRealCase(unittest.TestCase):
    """The result itself, checked against retained artifacts rather than rerun prose."""

    def test_the_deletion_family_reproduces_and_every_witness_verifies(self):
        with open(CASE, "r", encoding="utf-8") as handle:
            case = json.load(handle)
        with open(DELETION, "r", encoding="utf-8") as handle:
            stored = json.load(handle)
        fresh = dependence.analyse(CASE)
        self.assertEqual(fresh["case_sha256"], stored["case_sha256"])
        self.assertEqual(fresh["baseline"]["weighted_delta"], "1")
        self.assertEqual(fresh["baseline"]["criterion"], "supported")
        self.assertEqual(fresh["family"]["declared_cases"], 107)
        self.assertEqual(len(fresh["events"]["tolerance_crossings"]), 6)
        self.assertEqual(len(fresh["events"]["strict_loss_sign_changes"]), 0)
        self.assertEqual(fresh["events"]["weighted_delta_range"],
                         {"lowest": "0", "highest": "1"})
        self.assertEqual(fresh["breakdown_number"], 1)
        result = checker.verify(case, fresh)
        self.assertEqual(result["witnesses_confirmed"], 6)

    @unittest.skipUnless(OPERANDS and os.path.exists(OPERANDS or ""), "operands not supplied")
    def test_the_insertion_family_never_lowers_the_verdict(self):
        fresh = dependence.insertion_family(CASE, OPERANDS)
        with open(INSERTION, "r", encoding="utf-8") as handle:
            stored = json.load(handle)
        self.assertEqual(fresh["candidates"], stored["candidates"])
        self.assertEqual(fresh["singles"]["criterion_changes"], 0)
        self.assertEqual(fresh["singles"]["weighted_delta_range"],
                         {"lowest": "1", "highest": "2"})
        self.assertIsNone(fresh["pairs"]["witness"])
        self.assertIsNone(fresh["breakdown_number"])
        self.assertEqual(fresh["pairs"]["cases"], 190)
        self.assertEqual(fresh["pairs"]["weighted_delta_range"],
                         {"lowest": "1", "highest": "3"})

    def test_the_first_case_sits_exactly_at_its_arithmetic_floor(self):
        result = dependence.fragility(CASE)
        self.assertEqual(result["arithmetic_floor"]["k_floor"], 1)
        self.assertEqual(result["arithmetic_floor"]["margin"], "9/10")
        self.assertEqual(result["breakdown"]["k_observed"], 1)
        self.assertTrue(result["breakdown"]["at_the_arithmetic_floor"])
        self.assertEqual(result["reading"]["fragility_ratio"], "1")

    def test_no_source_identifier_reaches_a_retained_artifact(self):
        import re
        for path in (DELETION, INSERTION):
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
            self.assertEqual(re.findall(r"\b[0-9a-f]{32}\b", text), [])
            self.assertEqual(re.findall(r"configuration-\d+-row-\d+", text), [])


@unittest.skipUnless(SECOND and os.path.exists(SECOND or ""), "the second case is not supplied")
class TheSecondCase(unittest.TestCase):
    """Replication, and the floor that stops a forced zero being read as robustness."""

    def test_its_floor_is_two_so_no_single_deletion_could_ever_cross(self):
        with open(SECOND, "r", encoding="utf-8") as handle:
            case = json.load(handle)
        floor = dependence.arithmetic_floor(case)
        self.assertEqual(floor["weighted_delta"], "2/7")
        self.assertEqual(floor["margin"], "13/70")
        self.assertEqual(floor["largest_single_step"], "1/7")
        self.assertEqual(floor["k_floor"], 2)

    def test_the_retained_singles_and_breakdown_reproduce(self):
        with open(os.path.join(ROOT, "research", "label-dependence", "0.4.0",
                               "second-case-singles.json"), encoding="utf-8") as handle:
            singles = json.load(handle)
        self.assertEqual(singles["family"]["deletions"], 737)
        self.assertEqual(singles["criterion_changes"], 0)
        self.assertEqual(singles["criterion_counts"], {"supported": 737})
        self.assertEqual(singles["signed_loss_difference_range"],
                         {"lowest": "1/7", "highest": "2/7"})
        self.assertEqual(singles["gain_carrying_labels"]["count"], 53)
        with open(os.path.join(ROOT, "research", "label-dependence", "0.4.0",
                               "second-case-breakdown.json"), encoding="utf-8") as handle:
            breakdown = json.load(handle)
        self.assertEqual(breakdown["k_floor"], 2)
        self.assertEqual(breakdown["k_observed"], 2)
        self.assertEqual(breakdown["fragility_ratio"], "1")
        self.assertEqual(breakdown["witness_outcome"]["criterion"], "excluded")

    def test_the_witness_verifies_by_recomputation(self):
        with open(SECOND, "r", encoding="utf-8") as handle:
            case = json.load(handle)
        with open(os.path.join(ROOT, "research", "label-dependence", "0.4.0",
                               "second-case-breakdown.json"), encoding="utf-8") as handle:
            breakdown = json.load(handle)
        rows = {(r["anchor"], r["local_index"]): r for r in dependence.labels(case)}
        edited = case
        for named in breakdown["witness"]:
            row = rows[(named["anchor"], named["local_index"])]
            self.assertEqual(row["class"], named["class"])
            edited = dependence.without(edited, row["anchor"], row["_id"])
        outcome = dependence.evaluate(edited)
        self.assertEqual(outcome["weighted_delta"], "0")
        self.assertEqual(outcome["criterion"], "excluded")
        self.assertEqual(dependence.evaluate(case)["criterion"], "supported")


if __name__ == "__main__":
    unittest.main()
