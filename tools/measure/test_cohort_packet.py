"""Conformance and adversarial tests for the weighted cohort comparison.

Every population here is synthetic and labelled synthetic. The conformance cases
are the Engine lane's published reference examples, recomputed by a differently
structured implementation.
"""
from fractions import Fraction
import copy
import unittest

import check_cohort_packet as checker
import cohort_packet as producer

UNIT = {"false_negative": "1", "false_positive": "1", "tolerance": "1/10"}
POS = {"b0": Fraction(0), "c0": Fraction(3), "k": Fraction(3, 2), "d": Fraction(-1)}


def trap_anchor(anchor_id, weight):
    return {"id": anchor_id, "weight": weight, "reference_state": "finite",
            "base_detections": [{"id": "b0", "class": "car"}],
            "added_detections": [{"id": "c0", "class": "car"}],
            "objects": [{"id": "k", "class": "car"}, {"id": "d", "class": "car"}]}


def trap_side(present):
    objs = ["k", "d"] if present else ["k"]
    return {"objects_present": objs,
            "edges": [[d, o] for d in ("b0", "c0") for o in objs if abs(POS[d] - POS[o]) < 2]}


def cohort(cohort_id, anchors, worlds, loss=None):
    return {"schema_id": "reiyah.cohort-packet.case", "cohort_id": cohort_id,
            "loss": dict(loss or UNIT), "anchors": anchors, "joint_worlds": worlds}


class ConformanceWithTheEngineExamples(unittest.TestCase):
    """The published reference results, reached by a different implementation."""

    def test_oppositely_coupled_anchors(self):
        case = cohort("oppositely-coupled",
                      [trap_anchor("A", "1/2"), trap_anchor("B", "1/2")],
                      [{"world_id": "A_present", "per_anchor": {"A": trap_side(True),
                                                                "B": trap_side(False)}},
                       {"world_id": "B_present", "per_anchor": {"A": trap_side(False),
                                                                "B": trap_side(True)}}])
        report = producer.build(case)
        checker.verify(case, report)
        self.assertEqual(report["enclosure"], {"lower": "0", "upper": "0"},
                         "the Engine publishes a joint [0, 0]")
        self.assertEqual(report["separate_anchor_relaxation"]["lower"], "-1")
        self.assertEqual(report["separate_anchor_relaxation"]["upper"], "1")

    def test_single_matching_trap(self):
        case = cohort("matching-trap", [trap_anchor("A", "1")],
                      [{"world_id": "absent", "per_anchor": {"A": trap_side(False)}},
                       {"world_id": "present", "per_anchor": {"A": trap_side(True)}}])
        report = producer.build(case)
        checker.verify(case, report)
        self.assertEqual(report["enclosure"], {"lower": "-1", "upper": "1"})

    def test_unreachable_disputed_object_cancels(self):
        """A disputed object neither configuration can match leaves the difference alone."""
        anchor = {"id": "A", "weight": "1", "reference_state": "finite",
                  "base_detections": [{"id": "b0", "class": "car"}],
                  "added_detections": [{"id": "c0", "class": "car"}],
                  "objects": [{"id": "n0", "class": "car"}, {"id": "n3", "class": "car"},
                              {"id": "far", "class": "car"}]}
        near = {"objects_present": ["n0", "n3"], "edges": [["b0", "n0"], ["c0", "n3"]]}
        with_far = {"objects_present": ["n0", "n3", "far"],
                    "edges": [["b0", "n0"], ["c0", "n3"]]}
        case = cohort("unreachable", [anchor],
                      [{"world_id": "near_only", "per_anchor": {"A": near}},
                       {"world_id": "with_far", "per_anchor": {"A": with_far}}])
        report = producer.build(case)
        checker.verify(case, report)
        self.assertEqual(report["enclosure"], {"lower": "1", "upper": "1"},
                         "the Engine publishes a paired delta of [1, 1]")


class OpenReferenceIsNotAnEmptyWorld(unittest.TestCase):
    def test_all_open_gives_the_weighted_count_bound(self):
        """The Engine's two real anchors, r = 9 and 7 at half weight, give [-8, 8]."""
        anchors = [{"id": "A", "weight": "1/2", "reference_state": "open",
                    "base_detections": [], "added_detections":
                        [{"id": f"c{i}", "class": "car"} for i in range(9)], "objects": []},
                   {"id": "B", "weight": "1/2", "reference_state": "open",
                    "base_detections": [], "added_detections":
                        [{"id": f"c{i}", "class": "car"} for i in range(7)], "objects": []}]
        case = cohort("open-two-anchor", anchors, [])
        report = producer.build(case)
        checker.verify(case, report)
        self.assertEqual(report["state"], "open_reference_only")
        self.assertEqual(report["enclosure"], {"lower": "-8", "upper": "8"})

    def test_open_anchor_may_not_declare_objects(self):
        anchors = [{"id": "A", "weight": "1", "reference_state": "open",
                    "base_detections": [], "added_detections": [{"id": "c0", "class": "car"}],
                    "objects": [{"id": "k", "class": "car"}]}]
        with self.assertRaises(producer.CaseError):
            producer.build(cohort("bad-open", anchors, []))

    def test_finite_anchor_without_a_world_is_unresolved_not_empty(self):
        """An absent world must not be read as a world in which nothing exists."""
        case = cohort("no-worlds", [trap_anchor("A", "1")], [])
        report = producer.build(case)
        self.assertEqual(report["state"], "unresolved")
        self.assertIsNone(report["enclosure"])
        self.assertEqual(report["decision"]["improvement_criterion"], "not_evaluated")
        checker.verify(case, report)


class AdversarialCases(unittest.TestCase):
    def setUp(self):
        self.case = cohort("oppositely-coupled",
                           [trap_anchor("A", "1/2"), trap_anchor("B", "1/2")],
                           [{"world_id": "A_present", "per_anchor": {"A": trap_side(True),
                                                                     "B": trap_side(False)}},
                            {"world_id": "B_present", "per_anchor": {"A": trap_side(False),
                                                                     "B": trap_side(True)}}])
        self.report = producer.build(self.case)
        checker.verify(self.case, self.report)

    def reject(self, mutate, fragment):
        forged = copy.deepcopy(self.report)
        mutate(forged)
        with self.assertRaises(checker.Rejected) as caught:
            checker.verify(self.case, forged)
        self.assertIn(fragment, str(caught.exception))

    def test_the_relaxation_may_not_be_offered_as_the_joint_result(self):
        def mutate(report):
            report["enclosure"] = dict(report["separate_anchor_relaxation"])
            report["enclosure"].pop("status", None)
        self.reject(mutate, "enclosure is not the range")

    def test_a_joint_world_may_not_omit_a_finite_anchor(self):
        def mutate(report):
            report["joint_worlds"][0]["anchors"] = report["joint_worlds"][0]["anchors"][:1]
        self.reject(mutate, "does not evaluate exactly the finite anchors")

    def test_an_adverse_world_may_not_be_dropped(self):
        self.reject(lambda r: r["joint_worlds"].pop(), "exactly the declared joint worlds")

    def test_an_anchor_may_not_be_scored_in_a_different_world(self):
        """Swapping one anchor's side breaks the same-world requirement."""
        def mutate(report):
            world = report["joint_worlds"][0]
            for row in world["anchors"]:
                if row["anchor"] == "B":
                    row["objects_present"] = ["k", "d"]
        self.reject(mutate, "present objects differ from the case")

    def test_weights_must_match_the_case(self):
        def mutate(report):
            report["anchors"][0]["weight"] = "3/4"
        self.reject(mutate, "reported weight")

    def test_tolerance_must_match_the_case(self):
        def mutate(report):
            report["loss"]["tolerance"] = "5"
        self.reject(mutate, "tolerance does not match")

    def test_uncertified_count_is_refused(self):
        def mutate(report):
            report["joint_worlds"][0]["anchors"][0]["tp_augmented"] += 1
        self.reject(mutate, "uncertified counts")

    def test_weighted_value_must_be_recomputed(self):
        def mutate(report):
            report["joint_worlds"][0]["finite_contribution"] = "7"
        self.reject(mutate, "weighted value is wrong")

    def test_decision_must_follow_from_the_enclosure(self):
        def mutate(report):
            report["decision"]["improvement_criterion"] = "supported"
        self.reject(mutate, "does not follow from the enclosure")

    def test_checker_runs_no_matcher(self):
        self.assertFalse(checker.verify(self.case, self.report)["matcher_invoked"])

    def test_weights_must_sum_to_one(self):
        bad = cohort("bad-weights", [trap_anchor("A", "1/2"), trap_anchor("B", "1/4")],
                     [{"world_id": "w", "per_anchor": {"A": trap_side(True),
                                                       "B": trap_side(True)}}])
        with self.assertRaises(producer.CaseError):
            producer.build(bad)

    def test_a_world_missing_an_anchor_is_refused_at_build(self):
        bad = cohort("partial", [trap_anchor("A", "1/2"), trap_anchor("B", "1/2")],
                     [{"world_id": "w", "per_anchor": {"A": trap_side(True)}}])
        with self.assertRaises(producer.CaseError):
            producer.build(bad)


class IndependentConventionalCalculation(unittest.TestCase):
    """A tiny exhaustive calculation, structured differently from the producer.

    It enumerates every subset of detections as a candidate matching rather than
    running augmenting paths, so agreement is evidence about the quantity and not
    about one implementation.
    """

    @staticmethod
    def brute_tp(detections, objects, edges):
        from itertools import permutations
        best = 0
        for size in range(min(len(detections), len(objects)), 0, -1):
            if size <= best:
                break
            for chosen in permutations(objects, size):
                for subset in permutations(detections, size):
                    if all((d, o) in edges for d, o in zip(subset, chosen)):
                        best = max(best, size)
                        break
                if best >= size:
                    break
            if best >= size:
                break
        return best

    def test_agreement_on_every_small_graph(self):
        from itertools import product as iproduct
        a = b = Fraction(1)
        checked = 0
        for n_base, n_add, n_obj in ((1, 1, 2), (2, 1, 2), (1, 2, 2), (2, 2, 2)):
            base = [f"b{i}" for i in range(n_base)]
            added = [f"c{i}" for i in range(n_add)]
            objs = [f"o{i}" for i in range(n_obj)]
            slots = [(d, o) for d in base + added for o in objs]
            for mask in range(1 << len(slots)):
                edges = {slots[i] for i in range(len(slots)) if mask >> i & 1}
                anchor = {"id": "A", "weight": "1", "reference_state": "finite",
                          "base_detections": [{"id": d, "class": "car"} for d in base],
                          "added_detections": [{"id": d, "class": "car"} for d in added],
                          "objects": [{"id": o, "class": "car"} for o in objs]}
                world = {"objects_present": objs, "edges": [list(e) for e in sorted(edges)]}
                report = producer.build(cohort("tiny", [anchor],
                                               [{"world_id": "w", "per_anchor": {"A": world}}]))
                row = report["joint_worlds"][0]["anchors"][0]
                self.assertEqual(row["tp_base"], self.brute_tp(base, objs, edges))
                self.assertEqual(row["tp_augmented"], self.brute_tp(base + added, objs, edges))
                delta = (a + b) * (row["tp_augmented"] - row["tp_base"]) - b * len(added)
                self.assertEqual(Fraction(row["delta"]), delta)
                checked += 1
        # 16 + 64 + 64 + 256 graphs; the count is asserted exactly so a silently
        # shrinking enumeration cannot pass as a full sweep.
        self.assertEqual(checked, 400)


if __name__ == "__main__":
    unittest.main()
