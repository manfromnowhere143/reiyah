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

class ReferenceResolution(unittest.TestCase):
    """What an open comparison costs to close, in adjudications."""

    import reference_resolution as R

    def test_open_reference_gives_exactly_the_coarse_bound(self):
        a = b = Fraction(1)
        weights = [Fraction(1, 2), Fraction(1, 2)]
        additions = [9, 7]
        lower, upper = self.R.enclosure(weights, additions, a, b)
        weighted = sum(w * r for w, r in zip(weights, additions))
        self.assertEqual((lower, upper), (-b * weighted, a * weighted))
        self.assertEqual((lower, upper), (Fraction(-8), Fraction(8)))

    def test_each_adjudication_narrows_by_a_known_amount(self):
        a = b = Fraction(1)
        weights = [Fraction(1, 2), Fraction(1, 2)]
        additions = [9, 7]
        widths = []
        for settled in range(sum(additions) + 1):
            per = [min(settled, additions[0]), max(0, settled - additions[0])]
            lower, upper = self.R.enclosure(weights, additions, a, b, [0, 0], per)
            widths.append(upper - lower)
        self.assertEqual(widths[0], Fraction(16))
        self.assertEqual(widths[-1], Fraction(0))
        steps = {widths[i] - widths[i + 1] for i in range(len(widths) - 1)}
        self.assertEqual(steps, {Fraction(1)})

    def test_threshold_is_the_penalty_ratio(self):
        self.assertEqual(self.R.threshold(Fraction(1), Fraction(1)), Fraction(1, 2))
        self.assertEqual(self.R.threshold(Fraction(4), Fraction(1)), Fraction(1, 5))
        self.assertEqual(self.R.threshold(Fraction(1), Fraction(4)), Fraction(4, 5))

    def test_threshold_agrees_with_the_packet_arithmetic(self):
        """dTP/r > b/(a+b) must agree with delta > 0 computed from a real packet."""
        import glob
        import json
        import os
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                            "evidence", "decision-packet")
        checked = 0
        for path in sorted(glob.glob(os.path.join(root, "*-report.json"))):
            with open(path, "r", encoding="utf-8") as handle:
                entry = json.load(handle)
            a = Fraction(entry["loss"]["false_negative"])
            b = Fraction(entry["loss"]["false_positive"])
            r = entry["retained_additions"]
            for w in entry["worlds"]:
                gain = w["tp_augmented"] - w["tp_base"]
                positive = Fraction(w["delta"]) > 0
                self.assertEqual(positive, Fraction(gain, r) > self.R.threshold(a, b) if r else False)
                checked += 1
        self.assertGreater(checked, 8)

class ConversionRate(unittest.TestCase):
    """The retained full-split measurements, and the arithmetic that reads them."""

    @staticmethod
    def retained():
        import glob
        import json
        import os
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                            "evidence", "decision-packet")
        out = []
        for path in sorted(glob.glob(os.path.join(root, "conversion-*.json"))):
            with open(path, "r", encoding="utf-8") as handle:
                out.append(json.load(handle))
        return out

    def test_every_retained_measurement_is_internally_consistent(self):
        entries = self.retained()
        self.assertGreaterEqual(len(entries), 5)
        for entry in entries:
            population = entry["population"]
            gain = entry["true_positive_gain"]
            self.assertEqual(gain, population["tp_augmented"] - population["tp_base"])
            self.assertTrue(0 <= gain <= population["retained_additions"])
            self.assertEqual(Fraction(entry["conversion_rate"]),
                             Fraction(gain, population["retained_additions"]))

    def test_improvement_flags_match_the_threshold_law(self):
        for entry in self.retained():
            conversion = Fraction(entry["conversion_rate"])
            for ratio_text, flag in entry["improves_loss_at"].items():
                a, b = Fraction(int(ratio_text)), Fraction(1)
                self.assertEqual(flag, conversion > b / (a + b),
                                 f"{entry['base_detector']}+{entry['added_detector']} at {ratio_text}")

    def test_direction_and_operating_point_both_move_the_answer(self):
        """The two facts the findings lead with, read off the retained bytes."""
        by_key = {(e["base_detector"], e["added_detector"], e["rule"]["score_floor"]):
                  Fraction(e["conversion_rate"]) for e in self.retained()}
        forward = by_key[("megvii", "mapillary", "3/10")]
        reverse = by_key[("mapillary", "megvii", "3/10")]
        self.assertLess(forward, reverse)
        loose = by_key[("megvii", "mapillary", "1/10")]
        strict = by_key[("megvii", "mapillary", "1/2")]
        self.assertLess(loose, forward)
        self.assertLess(forward, strict)
        # the operating point moves the required penalty ratio further than the modality does
        span_floor = (1 / loose - 1) / (1 / strict - 1)
        cross = by_key[("megvii", "pointpillars", "3/10")]
        span_modality = max(forward, cross) / min(forward, cross)
        self.assertGreater(span_floor, span_modality)

    def test_exhaustive_monotonicity_record_has_no_violations(self):
        import json
        import os
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                            "evidence", "decision-packet", "addition-monotonicity.json")
        with open(path, "r", encoding="utf-8") as handle:
            record = json.load(handle)
        self.assertEqual(record["violations"], [])
        self.assertGreater(record["exhaustive_cases"], 400)
        counts = record["realisable_gain_and_r"]["worsening_pairs_by_penalty_ratio"]
        values = [counts[k] for k in sorted(counts, key=lambda x: Fraction(x))]
        self.assertEqual(values, sorted(values, reverse=True))

class AdjudicationBudget(unittest.TestCase):
    """The stopping rule, checked against an independent simulation and by hand."""

    import adjudication_budget as B

    def test_threshold_matches_the_contract_decision_rule(self):
        """tau is where (a+b)g - b*r crosses the tolerance."""
        a = b = Fraction(1)
        t = Fraction(1, 10)
        for r in range(1, 20):
            tau = self.B.threshold(r, a, b, t)
            for gain in range(0, r + 1):
                delta = (a + b) * gain - b * r
                self.assertEqual(delta > t, Fraction(gain) > tau, f"r={r} gain={gain}")

    def test_stopping_counts_are_the_smallest_that_decide(self):
        a = b = Fraction(1)
        t = Fraction(1, 10)
        for r in range(1, 20):
            tau = self.B.threshold(r, a, b, t)
            need_s, need_f = self.B.stopping_counts(r, tau)
            # need_s conversions force the supported branch whatever the rest do
            self.assertGreater(Fraction(need_s), tau)
            if need_s > 1:
                self.assertLessEqual(Fraction(need_s - 1), tau)
            # need_f failures force the excluded branch whatever the rest do
            self.assertLessEqual(Fraction(r - need_f), tau)
            if need_f > 1:
                self.assertGreater(Fraction(r - need_f + 1), tau)

    def test_expected_trials_matches_an_independent_simulation(self):
        import random
        random.seed(20260911)
        p = Fraction(66, 223)
        for need_s, need_f in ((5, 5), (4, 4), (3, 7)):
            exact = float(self.B.expected_trials(need_s, need_f, p))
            trials = 0
            runs = 40000
            threshold = float(p)
            for _ in range(runs):
                s = f = 0
                while s < need_s and f < need_f:
                    if random.random() < threshold:
                        s += 1
                    else:
                        f += 1
                    trials += 1
            simulated = trials / runs
            self.assertAlmostEqual(exact, simulated, delta=0.08,
                                   msg=f"{need_s}/{need_f}: exact {exact} simulated {simulated}")

    def test_probability_supported_is_a_probability_and_monotone_in_the_prior(self):
        values = [self.B.probability_supported(5, 5, Fraction(k, 20)) for k in range(0, 21)]
        for value in values:
            self.assertTrue(0 <= value <= 1)
        self.assertEqual(values, sorted(values))
        self.assertEqual(self.B.probability_supported(5, 5, Fraction(1, 2)), Fraction(1, 2))

    def test_fair_prior_gives_an_even_split_by_symmetry(self):
        """With equal stopping counts and p = 1/2 the race is symmetric."""
        for need in (2, 3, 5, 8):
            self.assertEqual(self.B.probability_supported(need, need, Fraction(1, 2)),
                             Fraction(1, 2))

    def test_worst_case_is_reported_honestly(self):
        """For these anchors stopping saves nothing in the worst case, and says so."""
        a = b = Fraction(1)
        t = Fraction(1, 10)
        for r in (9, 7):
            tau = self.B.threshold(r, a, b, t)
            need_s, need_f = self.B.stopping_counts(r, tau)
            self.assertEqual(min(need_s + need_f - 1, r), r)

