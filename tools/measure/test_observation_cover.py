"""Tests for the observation list, its checker, and the forgeries it must refuse."""
import copy
import json
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_observation_cover as checker  # noqa: E402
import cohort_packet as packet  # noqa: E402
import observation_cover as cover  # noqa: E402

CASES = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "research", "cohort-packet", "0.1.0")


def load(name):
    with open(os.path.join(CASES, name), "r", encoding="utf-8") as handle:
        return json.load(handle)


def rounded(value):
    """Through JSON, the way a consumer receives it."""
    return json.loads(json.dumps(value))


def pair(name):
    case = load(name)
    return rounded(packet.build(case)), rounded(cover.analyse(case))


def random_case(rng, objects=4, worlds=4):
    base = [{"id": "b%d" % i, "class": "car"} for i in range(rng.randint(1, 3))]
    added = [{"id": "c%d" % i, "class": "car"} for i in range(rng.randint(1, 2))]
    objs = [{"id": "o%d" % i, "class": "car"} for i in range(objects)]
    joint = []
    for index in range(worlds):
        present = [o["id"] for o in objs if rng.random() < 0.6]
        edges = [[d["id"], o] for d in base + added for o in present if rng.random() < 0.55]
        joint.append({"world_id": "w%d" % index,
                      "per_anchor": {"A": {"objects_present": present, "edges": edges}}})
    return {"schema_id": "reiyah.cohort-packet.case", "cohort_id": "probe",
            "anchors": [{"id": "A", "weight": "1", "reference_state": "finite",
                         "base_detections": base, "added_detections": added, "objects": objs}],
            "joint_worlds": joint,
            "loss": {"false_negative": "1", "false_positive": "1", "tolerance": "0"}}


class ObservationList(unittest.TestCase):
    def test_every_retained_case_verifies(self):
        names = [n for n in sorted(os.listdir(CASES)) if n.endswith(".json")]
        checked = 0
        for name in names:
            case = load(name)
            if case.get("schema_id") != packet.SCHEMA_ID:
                continue
            report, listing = pair(name)
            checker.verify(report, listing)
            checked += 1
        self.assertGreaterEqual(checked, 15)

    def test_the_live_comparison_waits_on_a_reference_not_on_an_atom(self):
        report, listing = pair("open-two-anchor.json")
        self.assertEqual(report["state"], "open_reference_only")
        self.assertEqual(report["enclosure"], {"lower": "-8", "upper": "8"})
        self.assertEqual(listing["state"], "waits_on_a_reference")
        self.assertEqual(listing["open_anchors"], ["A", "B"])
        self.assertIsNone(listing["observation_list"])

    def test_a_decided_cohort_needs_no_observation_though_readings_differ(self):
        report, listing = pair("oppositely-coupled.json")
        self.assertEqual(listing["state"], "already_decided")
        self.assertEqual(listing["disputed_atoms"]["count"], 4)
        self.assertEqual(listing["observation_list"]["count"], 0)
        checker.verify(report, listing)

    def test_the_matching_trap_waits_on_an_edge_not_on_the_presence(self):
        report, listing = pair("matching-trap.json")
        self.assertEqual(report["decision"]["improvement_criterion"], "unresolved")
        self.assertEqual(listing["observation_list"]["atoms"], ["A|edge|b0|d"])
        self.assertTrue(listing["observation_list"]["certified_shortest"])
        checker.verify(report, listing)

    def test_a_large_disputed_set_is_certified_without_any_search(self):
        report, listing = pair("sixteen-candidates-plan-case.json")
        self.assertEqual(listing["state"], "covered")
        entry = listing["observation_list"]
        self.assertEqual(listing["disputed_atoms"]["count"], 32)
        self.assertEqual(entry["count"], 1)
        self.assertTrue(entry["certified_shortest"])
        self.assertIn("not searched", entry["search"])
        checker.verify(report, listing)

    def test_a_list_the_bounds_do_not_pin_is_bracketed_rather_than_claimed(self):
        report, listing = pair("bracketed-observation-case.json")
        self.assertEqual(listing["state"], "bracketed")
        entry = listing["observation_list"]
        self.assertEqual(listing["disputed_atoms"]["count"], 39)
        self.assertIsNone(entry["atoms"])
        self.assertFalse(entry["certified_shortest"])
        self.assertEqual(entry["bracket"], {"lower": 1, "upper": 2})
        self.assertLess(entry["bracket"]["lower"], entry["bracket"]["upper"])
        checker.verify(report, listing)

    def test_a_certified_shortest_list_is_never_larger_than_a_search_finds(self):
        rng = random.Random(31337)
        certified = 0
        for _ in range(400):
            case = random_case(rng)
            listing = rounded(cover.analyse(case))
            if listing["state"] != "covered":
                continue
            entry = listing["observation_list"]
            self.assertGreaterEqual(entry["count"], entry["lower_bound"])
            self.assertLessEqual(entry["count"], entry["checkable_cover"]["count"])
            if entry["certified_shortest"]:
                self.assertEqual(entry["count"], entry["lower_bound"])
                certified += 1
        self.assertGreater(certified, 100)

    def test_random_cohorts_verify_against_the_independent_checker(self):
        rng = random.Random(99)
        for _ in range(300):
            case = random_case(rng, objects=rng.randint(2, 6), worlds=rng.randint(2, 5))
            checker.verify(rounded(packet.build(case)), rounded(cover.analyse(case)))


class Forgeries(unittest.TestCase):
    """Each of these is a report a producer could emit to look better than it is."""

    def setUp(self):
        self.report, self.listing = pair("three-copies-plan-case.json")
        self.assertEqual(self.listing["state"], "covered")

    def refuse(self, mutate, fragment):
        forged = copy.deepcopy(self.listing)
        mutate(forged)
        with self.assertRaises(checker.Rejected) as caught:
            checker.verify(self.report, forged)
        self.assertIn(fragment, str(caught.exception))

    def test_a_list_that_misses_a_separating_set_is_refused(self):
        def drop(forged):
            forged["observation_list"]["atoms"] = forged["observation_list"]["atoms"][:1]
            forged["observation_list"]["count"] = 1
            forged["observation_list"]["gap"] = 1 - forged["observation_list"]["lower_bound"]
        self.refuse(drop, "misses the separating set")

    def test_an_overlapping_packing_is_refused(self):
        def duplicate(forged):
            entry = forged["observation_list"]["packing"][0]
            forged["observation_list"]["packing"] = [entry, copy.deepcopy(entry)]
            forged["observation_list"]["lower_bound"] = 2
            forged["observation_list"]["bracket"]["lower"] = 2
        self.refuse(duplicate, "overlap")

    def test_a_packing_member_that_is_not_a_separating_set_is_refused(self):
        def invent(forged):
            member = copy.deepcopy(forged["observation_list"]["packing"][0])
            member["atoms"] = ["A|present|nowhere"]
            forged["observation_list"]["packing"].append(member)
            forged["observation_list"]["lower_bound"] += 1
            forged["observation_list"]["bracket"]["lower"] += 1
        self.refuse(invent, "not a genuine separating set")

    def test_a_dropped_discordant_pair_is_refused(self):
        def drop(forged):
            forged["observation_list"]["separating_sets"] = \
                forged["observation_list"]["separating_sets"][:-1]
        self.refuse(drop, "discordant pairs missing")

    def test_a_widened_separating_set_is_refused(self):
        def widen(forged):
            forged["observation_list"]["separating_sets"][0]["atoms"].append("A|present|x1")
        self.refuse(widen, "not where those readings differ")

    def test_a_shortest_claim_the_packing_does_not_force_is_refused(self):
        def inflate(forged):
            forged["observation_list"]["certified_shortest"] = True
            forged["observation_list"]["packing"] = forged["observation_list"]["packing"][:1]
            forged["observation_list"]["lower_bound"] = 1
            forged["observation_list"]["bracket"]["lower"] = 1
        self.refuse(inflate, "without a packing of the same size")

    def test_a_reported_verdict_the_certificates_do_not_give_is_refused(self):
        def flip(forged):
            for row in forged["readings"]:
                row["verdict"] = "supported" if row["verdict"] == "excluded" else "excluded"
        self.refuse(flip, "but its own certificates give")

    def test_a_shrunken_disputed_set_is_refused(self):
        def shrink(forged):
            forged["disputed_atoms"]["atoms"] = forged["disputed_atoms"]["atoms"][:1]
            forged["disputed_atoms"]["count"] = 1
        self.refuse(shrink, "not the one the readings support")

    def test_a_settled_claim_over_disagreeing_readings_is_refused(self):
        def settle(forged):
            forged["state"] = "already_decided"
            forged["observation_list"] = {"count": 0, "atoms": []}
        self.refuse(settle, "settled while readings disagree")

    def test_an_inflated_matching_in_the_packet_is_refused(self):
        forged_packet = copy.deepcopy(self.report)
        world = forged_packet["joint_worlds"][0]["anchors"][0]
        world["tp_augmented"] += 1
        with self.assertRaises(checker.Rejected) as caught:
            checker.verify(forged_packet, self.listing)
        self.assertIn("certificate does not show", str(caught.exception))

    def test_an_open_anchor_hidden_behind_a_list_is_refused(self):
        report, _ = pair("open-two-anchor.json")
        forged = copy.deepcopy(self.listing)
        forged["cohort_id"] = report["cohort_id"]
        with self.assertRaises(checker.Rejected) as caught:
            checker.verify(report, forged)
        self.assertIn("does not wait on a reference", str(caught.exception))

    def test_duplicate_json_keys_are_refused(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_forged_cover.json")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write('{"state": "covered", "state": "already_decided"}')
        try:
            with self.assertRaises(checker.Rejected):
                checker.load(path)
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
