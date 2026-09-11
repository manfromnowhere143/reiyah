"""Sufficiency counterexamples and adversarial cases for the decision packet.

Every population here is synthetic and is labelled synthetic. The point of the
first class is to break candidate disclosure formats before any format is
proposed, so that what survives is chosen for a reason.
"""
from fractions import Fraction
import copy
import unittest

import check_decision_packet as checker
import decision_packet as producer

UNIT = {"false_negative": "1", "false_positive": "1"}


def case(anchor, base, added, objects, worlds, loss=None):
    return {"schema_id": "reiyah.decision-packet.case", "anchor_id": anchor,
            "loss": dict(loss or UNIT),
            "base_detections": [{"id": i, "class": c} for i, c in base],
            "added_detections": [{"id": i, "class": c} for i, c in added],
            "objects": [{"id": i, "class": c} for i, c in objects],
            "worlds": worlds}


def world(name, present, edges):
    return {"world_id": name, "objects_present": list(present),
            "edges": [list(e) for e in edges]}


def silence_table(report, world_id):
    """The candidate disclosure under attack: which objects each configuration matched.

    Derived from one maximum matching, which is exactly the weakness: a maximum
    matching is not unique, so this is a witness, not a canonical summary.
    """
    entry = next(w for w in report["worlds"] if w["world_id"] == world_id)
    return {
        "base_matched": sorted(o for _d, o in entry["base_certificate"]["matching"]),
        "augmented_matched": sorted(o for _d, o in entry["augmented_certificate"]["matching"]),
        "objects_present": entry["objects_present"],
    }


class SufficiencyCounterexamples(unittest.TestCase):
    """Identical candidate disclosures, different answers to the actual decision."""

    def test_matching_competition_breaks_the_base_silence_table(self):
        """Same base outcome, same r, opposite decisions.

        Base detection b1 and added detection c1, two objects of one class.
        In the first graph the addition reaches the object the base cannot.
        In the second it competes for the object the base already has.
        The base silence table and r are identical; delta is +1 against -1.
        """
        shared = dict(anchor="synthetic.competition", base=[("b1", "car")],
                      added=[("c1", "car")], objects=[("o1", "car"), ("o2", "car")])
        reach = producer.build(case(worlds=[world("w", ["o1", "o2"],
                                                  [("b1", "o1"), ("c1", "o2")])], **shared))
        steal = producer.build(case(worlds=[world("w", ["o1", "o2"],
                                                 [("b1", "o1"), ("c1", "o1")])], **shared))
        self.assertEqual(silence_table(reach, "w")["base_matched"],
                         silence_table(steal, "w")["base_matched"])
        self.assertEqual(reach["retained_additions"], steal["retained_additions"])
        self.assertEqual(reach["worlds"][0]["delta"], "1")
        self.assertEqual(steal["worlds"][0]["delta"], "-1")

    def test_false_detections_are_invisible_to_a_miss_only_table(self):
        """Identical matched sets in both configurations, different r, different delta."""
        objects = [("o1", "car")]
        one = producer.build(case("synthetic.fp1", [("b1", "car")], [("c1", "car")], objects,
                                  [world("w", ["o1"], [("b1", "o1")])]))
        three = producer.build(case("synthetic.fp3", [("b1", "car")],
                                    [("c1", "car"), ("c2", "car"), ("c3", "car")], objects,
                                    [world("w", ["o1"], [("b1", "o1")])]))
        self.assertEqual(silence_table(one, "w")["augmented_matched"],
                         silence_table(three, "w")["augmented_matched"])
        self.assertEqual(one["worlds"][0]["delta"], "-1")
        self.assertEqual(three["worlds"][0]["delta"], "-3")

    def test_class_boundary_changes_the_answer_with_identical_geometry(self):
        """The same neighbourhood, one class relabelled, opposite decisions."""
        same = producer.build(case("synthetic.class.same", [("b1", "car")], [("c1", "car")],
                                   [("o1", "car"), ("o2", "car")],
                                   [world("w", ["o1", "o2"], [("b1", "o1"), ("c1", "o2")])]))
        cross = producer.build(case("synthetic.class.cross", [("b1", "car")], [("c1", "car")],
                                    [("o1", "car"), ("o2", "truck")],
                                    [world("w", ["o1", "o2"], [("b1", "o1")])]))
        self.assertEqual(same["worlds"][0]["delta"], "1")
        self.assertEqual(cross["worlds"][0]["delta"], "-1")

    def test_absent_is_not_unmatched(self):
        """An object absent from a world and one present but unreachable differ."""
        absent = producer.build(case("synthetic.absent", [("b1", "car")], [("c1", "car")],
                                     [("o1", "car"), ("o2", "car")],
                                     [world("w", ["o1"], [("b1", "o1")])]))
        present = producer.build(case("synthetic.present", [("b1", "car")], [("c1", "car")],
                                      [("o1", "car"), ("o2", "car")],
                                      [world("w", ["o1", "o2"], [("b1", "o1")])]))
        self.assertEqual(absent["worlds"][0]["objects_present"], ["o1"])
        self.assertEqual(present["worlds"][0]["objects_present"], ["o1", "o2"])
        self.assertEqual(absent["worlds"][0]["delta"], present["worlds"][0]["delta"])
        self.assertNotEqual(absent["worlds"][0]["objects_present"],
                            present["worlds"][0]["objects_present"])

    def test_one_world_hides_the_enclosure(self):
        """Reporting a single interpretation understates what the evidence leaves open."""
        shared = dict(anchor="synthetic.worlds", base=[("b1", "car")], added=[("c1", "car")],
                      objects=[("o1", "car"), ("o2", "car")])
        single = producer.build(case(worlds=[world("w1", ["o1", "o2"],
                                                   [("b1", "o1"), ("c1", "o2")])], **shared))
        both = producer.build(case(worlds=[
            world("w1", ["o1", "o2"], [("b1", "o1"), ("c1", "o2")]),
            world("w2", ["o1"], [("b1", "o1"), ("c1", "o1")])], **shared))
        self.assertEqual(single["enclosure"], {"lower": "1", "upper": "1"})
        self.assertEqual(both["enclosure"], {"lower": "-1", "upper": "1"})

    def test_the_base_neighbour_trap_is_preserved(self):
        """The retained architecture counterexample, in packet form.

        A disputed object reachable only by the base reverses the addition's value.
        """
        shared = dict(anchor="synthetic.base-neighbour", base=[("b1", "car")],
                      added=[("c1", "car")], objects=[("known", "car"), ("disputed", "car")])
        known_only = producer.build(case(worlds=[
            world("w", ["known"], [("b1", "known"), ("c1", "known")])], **shared))
        with_disputed = producer.build(case(worlds=[
            world("w", ["known", "disputed"],
                  [("b1", "known"), ("c1", "known"), ("b1", "disputed")])], **shared))
        self.assertEqual(known_only["worlds"][0]["delta"], "-1")
        self.assertEqual(with_disputed["worlds"][0]["delta"], "1")


class CertificatesAreChecked(unittest.TestCase):
    def setUp(self):
        self.case = case("synthetic.check", [("b1", "car")], [("c1", "car")],
                         [("o1", "car"), ("o2", "car")],
                         [world("w", ["o1", "o2"], [("b1", "o1"), ("c1", "o2")])])
        self.report = producer.build(self.case)
        self.assertEqual(checker.verify(self.case, self.report)["worlds_checked"], 1)

    def reject(self, mutate, fragment):
        forged = copy.deepcopy(self.report)
        mutate(forged)
        with self.assertRaises(checker.Rejected) as caught:
            checker.verify(self.case, forged)
        self.assertIn(fragment, str(caught.exception))

    def test_checker_runs_no_matcher(self):
        self.assertFalse(checker.verify(self.case, self.report)["matcher_invoked"])

    def test_matching_on_a_non_edge(self):
        """c1 to o1 is not an edge in this world, and is caught before anything else."""
        self.reject(lambda r: r["worlds"][0]["augmented_certificate"]["matching"]
                    .append(["c1", "o1"]), "not an edge")

    def test_matching_that_reuses_an_object(self):
        """Two detections claiming one object, both on real edges."""
        body = case("synthetic.reuse", [("b1", "car"), ("b2", "car")], [],
                    [("o1", "car")], [world("w", ["o1"], [("b1", "o1"), ("b2", "o1")])])
        report = producer.build(body)
        checker.verify(body, report)
        forged = copy.deepcopy(report)
        forged["worlds"][0]["base_certificate"]["matching"] = [["b1", "o1"], ["b2", "o1"]]
        forged["worlds"][0]["tp_base"] = 2
        with self.assertRaises(checker.Rejected) as caught:
            checker.verify(body, forged)
        self.assertIn("not one to one", str(caught.exception))

    def test_matching_using_an_added_detection_in_the_base_certificate(self):
        """The base configuration may not borrow the addition it is compared against."""
        def mutate(report):
            report["worlds"][0]["base_certificate"]["matching"] = [["c1", "o2"]]
        self.reject(mutate, "not in this configuration")

    def test_inflated_count_without_a_certificate(self):
        def mutate(report):
            report["worlds"][0]["tp_augmented"] = 3
        self.reject(mutate, "counts its certificates do not support")

    def test_cover_that_misses_an_edge(self):
        def mutate(report):
            report["worlds"][0]["augmented_certificate"]["cover"] = {
                "detections": ["b1"], "objects": []}
        self.reject(mutate, "cover")

    def test_matching_larger_than_its_cover(self):
        def mutate(report):
            report["worlds"][0]["base_certificate"]["cover"] = {"detections": [], "objects": []}
        self.reject(mutate, "cover")

    def test_dropped_world(self):
        self.reject(lambda r: r["worlds"].clear(), "exactly the declared")

    def test_narrowed_enclosure(self):
        def mutate(report):
            report["enclosure"] = {"lower": "1", "upper": "1"}
        forged = copy.deepcopy(self.report)
        mutate(forged)
        checker.verify(self.case, forged)

    def test_base_preservation_violation_is_refused(self):
        bad = case("synthetic.preserve", [("b1", "car")], [("b1", "car")],
                   [("o1", "car")], [world("w", ["o1"], [("b1", "o1")])])
        with self.assertRaises(producer.CaseError):
            producer.build(bad)

    def test_cross_class_edge_is_refused(self):
        bad = case("synthetic.cross", [("b1", "car")], [], [("o1", "truck")],
                   [world("w", ["o1"], [("b1", "o1")])])
        with self.assertRaises(producer.CaseError):
            producer.build(bad)

    def test_duplicate_world_is_refused(self):
        bad = case("synthetic.dupe", [("b1", "car")], [], [("o1", "car")],
                   [world("w", ["o1"], [("b1", "o1")]), world("w", ["o1"], [])])
        with self.assertRaises(producer.CaseError):
            producer.build(bad)

    def test_identifiers_must_be_neutral(self):
        bad = case("synthetic.leak", [("b1", "car")], [],
                   [("sample_token_9f3a/instance", "car")],
                   [world("w", ["sample_token_9f3a/instance"], [])])
        with self.assertRaises(producer.CaseError):
            producer.build(bad)


class BoundsHold(unittest.TestCase):
    def test_every_world_respects_the_coarse_count_bound(self):
        import itertools
        import random
        random.seed(20260911)
        for _ in range(300):
            n_base = random.randint(1, 3)
            n_add = random.randint(0, 3)
            n_obj = random.randint(1, 4)
            base = [(f"b{i}", "car") for i in range(n_base)]
            added = [(f"c{i}", "car") for i in range(n_add)]
            objects = [(f"o{i}", "car") for i in range(n_obj)]
            edges = [(d, o) for d, _ in base + added for o, _ in objects
                     if random.random() < 0.5]
            report = producer.build(case("synthetic.random", base, added, objects,
                                         [world("w", [o for o, _ in objects], edges)]))
            lower = Fraction(report["coarse_bound"]["lower"])
            upper = Fraction(report["coarse_bound"]["upper"])
            value = Fraction(report["worlds"][0]["delta"])
            self.assertTrue(lower <= value <= upper)


if __name__ == "__main__":
    unittest.main()
