"""Tests for the conventional comparator, including the results that limit this lane."""
from fractions import Fraction
import json
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cohort_packet as packet  # noqa: E402
import conventional_comparator as conventional  # noqa: E402

CASES = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "research", "cohort-packet", "0.1.0")


def load(name):
    with open(os.path.join(CASES, name), "r", encoding="utf-8") as handle:
        return json.load(handle)


def random_finite_case(rng):
    """A cohort with every anchor finite, built only from declared pieces."""
    anchors, worlds = [], []
    count = rng.randint(1, 3)
    names = [f"A{i}" for i in range(count)]
    weights = [Fraction(1, count)] * count
    for name in names:
        anchors.append({
            "id": name, "weight": str(weights[0]), "reference_state": "finite",
            "base_detections": [{"id": f"{name}_b0", "class": "car"}],
            "added_detections": [{"id": f"{name}_c0", "class": "car"}],
            "objects": [{"id": f"{name}_k", "class": "car"}, {"id": f"{name}_d", "class": "car"}]})
    for index in range(rng.randint(1, 4)):
        per = {}
        for name in names:
            if rng.random() < 0.5:
                per[name] = {"objects_present": [f"{name}_k", f"{name}_d"],
                             "edges": [[f"{name}_b0", f"{name}_k"], [f"{name}_b0", f"{name}_d"],
                                       [f"{name}_c0", f"{name}_k"]]}
            else:
                per[name] = {"objects_present": [f"{name}_k"],
                             "edges": [[f"{name}_b0", f"{name}_k"], [f"{name}_c0", f"{name}_k"]]}
        worlds.append({"world_id": f"w{index}", "per_anchor": per})
    seen, unique = set(), []
    for world in worlds:
        key = json.dumps(world["per_anchor"], sort_keys=True)
        if key not in seen:
            seen.add(key)
            unique.append(world)
    for position, world in enumerate(unique):
        world["world_id"] = f"w{position}"
    return {"schema_id": "reiyah.cohort-packet.case", "cohort_id": "random",
            "anchors": anchors, "joint_worlds": unique,
            "loss": {"false_negative": "1", "false_positive": "1",
                     "tolerance": str(rng.choice(["0", "1/10", "1/2"]))}}


class TheEquivalenceOnFiniteCohorts(unittest.TestCase):
    """On a finite cohort the instrument's unresolved state IS reading disagreement.

    This is the result that limits the claim, not the one that supports it.
    """

    def test_it_holds_on_every_retained_case_where_it_applies(self):
        for name in sorted(os.listdir(CASES)):
            if not name.endswith(".json") or name == "answer-prerequisites.json":
                continue
            case = load(name)
            if "joint_worlds" not in case:
                continue
            result = conventional.compare(case)
            if not result.get("equivalence_applies"):
                continue
            with self.subTest(case=name):
                self.assertTrue(result["equivalence"]["holds"])

    def test_it_holds_on_random_finite_cohorts(self):
        rng = random.Random(20260912)
        applied = 0
        for _ in range(300):
            case = random_finite_case(rng)
            result = conventional.compare(case)
            if not result.get("equivalence_applies"):
                continue
            applied += 1
            self.assertTrue(result["equivalence"]["holds"], case)
        self.assertGreater(applied, 250)

    def test_disagreement_and_unresolved_are_the_same_event(self):
        rng = random.Random(7)
        seen_both = {"unresolved": 0, "decided": 0}
        for _ in range(200):
            case = random_finite_case(rng)
            result = conventional.compare(case)
            if not result.get("equivalence_applies"):
                continue
            verdicts = {r["verdict"] for r in
                        result["conventional_single_interpretation"]["readings"]}
            criterion = result["instrument"]["improvement_criterion"]
            if len(verdicts) > 1:
                self.assertEqual(criterion, "unresolved")
                seen_both["unresolved"] += 1
            else:
                self.assertNotEqual(criterion, "unresolved")
                seen_both["decided"] += 1
        self.assertGreater(seen_both["unresolved"], 0)
        self.assertGreater(seen_both["decided"], 0)

    def test_when_the_readings_agree_the_instrument_only_confirms(self):
        for name in ("oppositely-coupled.json", "separated-geometry-observation-case.json"):
            result = conventional.compare(load(name))
            with self.subTest(case=name):
                self.assertIn("confirmation only", result["what_the_instrument_adds"])
                verdicts = {r["verdict"] for r in
                            result["conventional_single_interpretation"]["readings"]}
                self.assertEqual(len(verdicts), 1)
                self.assertEqual(result["instrument"]["improvement_criterion"], verdicts.pop())


class TheEquivalenceNeedsEveryAnchorFinite(unittest.TestCase):
    """Stated for finite cohorts only, and the boundary is checked rather than assumed."""

    def test_an_open_anchor_takes_the_case_outside_the_claim(self):
        result = conventional.compare(load("open-two-anchor.json"))
        self.assertFalse(result["equivalence_applies"])
        self.assertIsNone(result["equivalence"]["holds"])

    def test_agreeing_readings_can_still_be_unresolved_when_an_anchor_is_open(self):
        """The instrument is NOT reading disagreement once a reference is missing."""
        case = load("matching-trap-plan-case.json")
        case["anchors"][0]["weight"] = "1/2"
        case["anchors"].append({
            "id": "B", "weight": "1/2", "reference_state": "open",
            "base_detections": [], "added_detections": [{"id": "B_c0", "class": "car"}],
            "objects": []})
        readings = conventional.single_interpretation_readings(case)
        report = packet.build(case)
        self.assertEqual(report["decision"]["improvement_criterion"], "unresolved")
        self.assertTrue(readings)
        result = conventional.compare(case)
        self.assertFalse(result["equivalence_applies"])


class TreatingMissingAsEmptyIsNotNeutral(unittest.TestCase):
    """The case FOR the instrument, computed rather than asserted."""

    def test_on_the_live_comparison_it_returns_the_lower_endpoint_exactly(self):
        case = load("open-two-anchor.json")
        reading = conventional.complete_annotation_reading(case)
        report = packet.build(case)
        self.assertEqual(reading["value_with_the_least_favourable_admitted_reading"], "-8")
        self.assertEqual(report["enclosure"], {"lower": "-8", "upper": "8"})
        self.assertTrue(reading["equals_the_lower_endpoint_of_the_true_bound"])

    def test_the_assumed_contribution_is_minus_b_times_r(self):
        case = load("open-two-anchor.json")
        reading = conventional.complete_annotation_reading(case)
        report = packet.build(case)
        expected = sum((Fraction(a["weight"]) * -Fraction(str(case["loss"]["false_positive"]))
                        * a["retained_additions"]
                        for a in report["anchors"] if a["reference_state"] != "finite"),
                       Fraction(0))
        self.assertEqual(reading["contribution_from_treating_missing_as_empty"], str(expected))

    def test_it_never_exceeds_the_most_favourable_admissible_value(self):
        """An assumption about missing data, always pointing the same way."""
        case = load("open-two-anchor.json")
        reading = conventional.complete_annotation_reading(case)
        report = packet.build(case)
        self.assertLessEqual(
            Fraction(reading["value_with_the_most_favourable_admitted_reading"]),
            Fraction(report["enclosure"]["upper"]))
        self.assertLess(
            Fraction(reading["contribution_from_treating_missing_as_empty"]),
            Fraction(report["open_contribution"]["upper"]))


class TheComparatorGetsEqualInformation(unittest.TestCase):
    def test_it_is_given_the_same_loss_and_tolerance(self):
        case = load("adaptive-beats-fixed-case.json")
        result = conventional.compare(case)
        for item in ("the additive loss", "the tolerance", "the admitted readings"):
            self.assertIn(item, result["shared_with_the_comparator"])

    def test_the_same_tolerance_rule_decides_both(self):
        """A point estimate and an enclosure endpoint are judged by one rule."""
        case = load("adaptive-beats-fixed-case.json")
        tolerance = Fraction(str(case["loss"]["tolerance"]))
        for reading in conventional.single_interpretation_readings(case):
            expected = "supported" if Fraction(reading["finite_value"]) > tolerance else "excluded"
            self.assertEqual(reading["verdict"], expected)


if __name__ == "__main__":
    unittest.main()
