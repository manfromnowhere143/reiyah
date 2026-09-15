"""Tests for the scale study: its rules, its stopping outcomes and its own repaired defect."""
from fractions import Fraction
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scale_study as study  # noqa: E402

IDENTITY = {"translation": [0.0, 0.0, 0.0], "rotation": [1.0, 0.0, 0.0, 0.0]}


def row(name, x, y, score=0.9):
    return {"detection_name": name, "detection_score": score, "translation": [x, y, 0.0]}


def obj(name, x, y, token="o"):
    return {"c": name, "x": x, "y": y, "t": token}


class Qualification(unittest.TestCase):
    def test_the_score_cutoff_is_inclusive_at_the_declared_value(self):
        kept = study.qualify([row("car", 0, 0, 0.30), row("car", 1, 1, 0.2999)], IDENTITY)
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0]["i"], 0)

    def test_the_range_rule_is_the_common_fifty_metres(self):
        kept = study.qualify([row("car", 50.0, 0), row("car", 50.001, 0)], IDENTITY)
        self.assertEqual(len(kept), 1)

    def test_a_category_outside_the_detection_set_is_dropped(self):
        kept = study.qualify([row("animal", 0, 0), row("car", 0, 0)], IDENTITY)
        self.assertEqual([k["c"] for k in kept], ["car"])

    def test_a_row_without_a_usable_translation_is_dropped_not_guessed(self):
        bad = {"detection_name": "car", "detection_score": 0.9, "translation": None}
        self.assertEqual(study.qualify([bad], IDENTITY), [])

    def test_the_pose_is_applied_rather_than_ignored(self):
        pose = {"translation": [100.0, 0.0, 0.0], "rotation": [1.0, 0.0, 0.0, 0.0]}
        self.assertEqual(len(study.qualify([row("car", 0, 0)], pose)), 0)
        self.assertEqual(len(study.qualify([row("car", 100, 0)], pose)), 1)

    def test_the_source_row_index_is_preserved(self):
        kept = study.qualify([row("animal", 0, 0), row("car", 0, 0), row("car", 1, 0)], IDENTITY)
        self.assertEqual([k["i"] for k in kept], [1, 2])


class Suppression(unittest.TestCase):
    def test_the_two_metre_rule_is_strict(self):
        base = [{"i": 0, "c": "car", "x": 0.0, "y": 0.0}]
        just_inside = [{"i": 1, "c": "car", "x": 1.999, "y": 0.0}]
        exactly_two = [{"i": 1, "c": "car", "x": 2.0, "y": 0.0}]
        self.assertEqual(study.suppress(base, just_inside), [])
        self.assertEqual(len(study.suppress(base, exactly_two)), 1)

    def test_suppression_is_same_class_only(self):
        base = [{"i": 0, "c": "car", "x": 0.0, "y": 0.0}]
        other = [{"i": 1, "c": "truck", "x": 0.0, "y": 0.0}]
        self.assertEqual(len(study.suppress(base, other)), 1)

    def test_a_candidate_is_suppressed_by_an_earlier_retained_candidate(self):
        base = []
        candidates = [{"i": 0, "c": "car", "x": 0.0, "y": 0.0},
                      {"i": 1, "c": "car", "x": 1.0, "y": 0.0}]
        kept = study.suppress(base, candidates)
        self.assertEqual([k["i"] for k in kept], [0])

    def test_the_order_is_ascending_source_index_and_it_matters(self):
        base = []
        candidates = [{"i": 5, "c": "car", "x": 1.0, "y": 0.0},
                      {"i": 2, "c": "car", "x": 0.0, "y": 0.0}]
        kept = study.suppress(base, candidates)
        self.assertEqual([k["i"] for k in kept], [2])


class Arithmetic(unittest.TestCase):
    def frame(self, objects, base, added):
        return study.Frame(objects, base, added)

    def test_the_declared_loss(self):
        f = self.frame([obj("car", 0, 0)], [], [{"i": 0, "c": "car", "x": 0.0, "y": 0.0}])
        self.assertEqual(f.gain(), 1)
        self.assertEqual(f.delta(), Fraction(1))

    def test_an_addition_that_matches_nothing_costs_its_penalty(self):
        f = self.frame([], [], [{"i": 0, "c": "car", "x": 0.0, "y": 0.0}])
        self.assertEqual(f.delta(), Fraction(-1))

    def test_matching_competition_is_preserved(self):
        """The base can be displaced onto another object, so the gain is not per detection."""
        objects = [obj("car", 0, 0, "a"), obj("car", 1.0, 0, "b")]
        base = [{"i": 0, "c": "car", "x": 0.5, "y": 0.0}]
        added = [{"i": 1, "c": "car", "x": 5.0, "y": 0.0}]
        f = self.frame(objects, base, added)
        self.assertEqual(f.gain(), 0)

    def test_the_floor_follows_from_weights_penalties_and_margin(self):
        frames = [self.frame([obj("car", 0, 0)], [], [{"i": 0, "c": "car", "x": 0.0, "y": 0.0}])
                  for _ in range(4)]
        decision = study.decide(frames)
        self.assertEqual(decision, Fraction(1))
        floor = study.arithmetic_floor(decision, frames)
        self.assertEqual(floor["step"], str(Fraction(1, 2)))
        self.assertEqual(floor["k_floor"], 2)


class StoppingOutcomes(unittest.TestCase):
    def frames_from(self, spec):
        return [study.Frame(o, b, a) for o, b, a in spec]

    def test_an_empty_reference_is_its_own_outcome(self):
        frames = self.frames_from([([], [], [{"i": 0, "c": "car", "x": 0.0, "y": 0.0}])])
        self.assertEqual(study.unit(frames)["status"], "empty_reference")

    def test_a_missing_input_is_its_own_outcome(self):
        self.assertEqual(study.unit([])["status"], "missing_input")

    def test_an_unsupported_baseline_is_reported_not_discarded(self):
        frames = self.frames_from([([obj("car", 9, 9)], [], [{"i": 0, "c": "car", "x": 0.0,
                                                              "y": 0.0}])])
        result = study.unit(frames)
        self.assertEqual(result["status"], "unsupported_baseline")
        self.assertEqual(result["decision"], "-1")

    def test_a_supported_unit_is_certified_at_its_floor(self):
        frames = self.frames_from([([obj("car", 0, 0)], [],
                                    [{"i": 0, "c": "car", "x": 0.0, "y": 0.0}])])
        result = study.unit(frames)
        self.assertEqual(result["status"], "certified_at_floor")
        self.assertEqual(result["k_floor"], 1)
        self.assertEqual(result["k_observed"], 1)
        self.assertEqual(result["fragility_ratio"], "1")
        self.assertTrue(Fraction(result["verified_decision_after"]) <= study.TOLERANCE)

    def test_the_budget_is_an_outcome_and_not_a_silent_truncation(self):
        frames = self.frames_from([([obj("car", 0, 0)], [],
                                    [{"i": 0, "c": "car", "x": 0.0, "y": 0.0}])])
        self.assertEqual(study.unit(frames, budget=0)["status"], "budget_exhausted")


class TheRepairedDefect(unittest.TestCase):
    """Deletions inside one frame are not additive; the witness must reverify."""

    def test_two_labels_whose_singleton_losses_do_not_add(self):
        # One addition reaching two objects. Deleting either alone loses nothing,
        # because the addition reassigns to the other. Deleting both loses one.
        objects = [obj("car", 0.0, 0.0, "a"), obj("car", 0.5, 0.0, "b")]
        added = [{"i": 0, "c": "car", "x": 0.25, "y": 0.0}]
        f = study.Frame(objects, [], added)
        self.assertEqual(f.gain(), 1)
        self.assertEqual(f.gain(frozenset([0])), 1)
        self.assertEqual(f.gain(frozenset([1])), 1)
        self.assertEqual(f.gain(frozenset([0, 1])), 0)

    def test_the_reported_witness_is_verified_by_full_recomputation(self):
        frames = [study.Frame([obj("car", 0, 0)], [], [{"i": 0, "c": "car", "x": 0.0, "y": 0.0}])
                  for _ in range(3)]
        result = study.unit(frames)
        self.assertIn("verified_decision_after", result)
        self.assertLessEqual(Fraction(result["verified_decision_after"]), study.TOLERANCE)


class AgainstAnOrdinaryImplementation(unittest.TestCase):
    """A separate matcher and separate edge construction must reach the same decision."""

    @staticmethod
    def ordinary(objects, base, added):
        def near(d, o):
            return d["c"] == o["c"] and math.hypot(d["x"] - o["x"], d["y"] - o["y"]) < 2.0

        def size(dets):
            pairs = [(i, j) for i, d in enumerate(dets) for j, o in enumerate(objects)
                     if near(d, o)]
            adjacency = {}
            for left, right in pairs:
                adjacency.setdefault(left, []).append(right)
            assigned = {}

            def walk(node, seen):
                for other in adjacency.get(node, ()):
                    if other in seen:
                        continue
                    seen.add(other)
                    if other not in assigned or walk(assigned[other], seen):
                        assigned[other] = node
                        return True
                return False

            return sum(1 for i in range(len(dets)) if walk(i, set()))

        return Fraction(2) * (size(base + added) - size(base)) - Fraction(len(added))

    def test_agreement_on_constructed_frames(self):
        import random
        rng = random.Random(4242)
        for _ in range(300):
            objects = [obj(rng.choice(("car", "truck")), rng.uniform(0, 12), rng.uniform(0, 12),
                           "o%d" % i) for i in range(rng.randint(0, 6))]
            base = [{"i": i, "c": rng.choice(("car", "truck")), "x": rng.uniform(0, 12),
                     "y": rng.uniform(0, 12)} for i in range(rng.randint(0, 5))]
            added = [{"i": 100 + i, "c": rng.choice(("car", "truck")), "x": rng.uniform(0, 12),
                      "y": rng.uniform(0, 12)} for i in range(rng.randint(0, 4))]
            mine = study.Frame(objects, base, added).delta()
            self.assertEqual(mine, self.ordinary(objects, base, added))


if __name__ == "__main__":
    unittest.main()
