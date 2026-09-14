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

    def test_an_open_reference_beside_a_settled_criterion_asks_for_nothing(self):
        """The 0.1.0 defect: an open anchor was read as an outstanding question."""
        report, listing = pair("settled-with-open-reference-case.json")
        self.assertEqual(report["decision"]["improvement_criterion"], "supported")
        self.assertEqual(report["enclosure"], {"lower": "4/5", "upper": "1"})
        self.assertEqual(listing["state"], "already_decided")
        self.assertEqual(listing["observation_list"]["count"], 0)
        self.assertEqual(listing["open_reference_preserved"]["anchors"], ["O"])
        self.assertEqual(listing["settles"]["the_improvement_criterion"], "supported")
        checker.verify(report, listing)

    def test_a_settled_criterion_is_not_a_settled_preference(self):
        """Criterion and preference are different outputs and stay different."""
        case = load("settled-with-open-reference-case.json")
        case["loss"] = {"false_negative": "1", "false_positive": "1", "tolerance": "1/10"}
        case["anchors"][0]["objects"] = []
        case["joint_worlds"][0]["per_anchor"]["F"] = {"objects_present": [], "edges": []}
        report = rounded(packet.build(case))
        listing = rounded(cover.analyse(case))
        self.assertEqual(report["decision"]["improvement_criterion"], "excluded")
        self.assertEqual(listing["state"], "already_decided")
        self.assertEqual(listing["settles"]["the_improvement_criterion"], "excluded")
        self.assertEqual(listing["settles"]["the_preference_output"], report["decision"]["preference"])
        checker.verify(report, listing)

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
        self.assertEqual(listing["state"], "certified_shortest")
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

    def test_a_searched_optimum_is_never_reported_as_a_certificate(self):
        """The 0.1.0 defect: covered was counted as certified, promoting 8 of 386."""
        rng = random.Random(31337)
        certified = searched = 0
        for _ in range(400):
            case = random_case(rng)
            listing = rounded(cover.analyse(case))
            if listing["state"] == "searched_shortest":
                entry = listing["observation_list"]
                self.assertFalse(entry["certified_shortest"])
                self.assertGreater(entry["count"], entry["lower_bound"])
                searched += 1
            if listing["state"] != "certified_shortest":
                continue
            entry = listing["observation_list"]
            self.assertTrue(entry["certified_shortest"])
            self.assertEqual(entry["count"], entry["lower_bound"])
            self.assertLessEqual(entry["count"], entry["checkable_cover"]["count"])
            certified += 1
        self.assertGreater(certified, 100)
        self.assertGreater(searched, 0)

    def test_random_cohorts_verify_against_the_independent_checker(self):
        rng = random.Random(99)
        for _ in range(300):
            case = random_case(rng, objects=rng.randint(2, 6), worlds=rng.randint(2, 5))
            checker.verify(rounded(packet.build(case)), rounded(cover.analyse(case)))


class Forgeries(unittest.TestCase):
    """Each of these is a report a producer could emit to look better than it is."""

    def setUp(self):
        self.report, self.listing = pair("three-copies-plan-case.json")
        self.assertEqual(self.listing["state"], "certified_shortest")

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
            forged["observation_list"]["packing"] = forged["observation_list"]["packing"][:1]
            forged["observation_list"]["lower_bound"] = 1
            forged["observation_list"]["bracket"]["lower"] = 1
            forged["observation_list"]["gap"] = forged["observation_list"]["count"] - 1
        self.refuse(inflate, "certified_shortest does not match")

    def test_a_searched_optimum_relabelled_as_certified_is_refused(self):
        def relabel(forged):
            forged["observation_list"]["packing"] = forged["observation_list"]["packing"][:1]
            forged["observation_list"]["lower_bound"] = 1
            forged["observation_list"]["bracket"]["lower"] = 1
            forged["observation_list"]["gap"] = forged["observation_list"]["count"] - 1
            forged["observation_list"]["certified_shortest"] = False
        self.refuse(relabel, "disagrees with its own certificate")

    def test_an_unknown_field_is_refused(self):
        self.refuse(lambda forged: forged.__setitem__("extra", {"anything": 1}),
                    "fields this checker does not know")

    def test_a_missing_required_field_is_refused(self):
        self.refuse(lambda forged: forged.pop("preference"), "omits required fields")

    def test_a_criterion_the_packet_does_not_report_is_refused(self):
        self.refuse(lambda forged: forged.__setitem__("improvement_criterion", "supported"),
                    "improvement criterion is not the packet")

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
            forged["observation_list"] = {"count": 0, "atoms": [], "lower_bound": 0}
            forged["settles"] = {"the_improvement_criterion": "supported",
                                 "the_preference_output": forged["preference"]}
            forged.pop("readings")
            forged.pop("scope")
        self.refuse(settle, "already_decided is claimed while the criterion is")

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
        self.assertIn("packet state is not the packet", str(caught.exception))

    def test_duplicate_json_keys_are_refused(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_forged_cover.json")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write('{"state": "covered", "state": "already_decided"}')
        try:
            with self.assertRaises(checker.Rejected):
                checker.load(path)
        finally:
            os.remove(path)


class OpenStateForgeries(unittest.TestCase):
    """The 0.1.0 checker returned early on an open reference and checked nothing after it.

    Every forgery here was accepted by 0.1.0 on an unchanged, valid open packet.
    """

    def setUp(self):
        self.report, self.listing = pair("open-two-anchor.json")
        self.assertEqual(self.listing["state"], "waits_on_a_reference")
        checker.verify(self.report, self.listing)

    def refuse(self, mutate, fragment):
        forged = copy.deepcopy(self.listing)
        mutate(forged)
        with self.assertRaises(checker.Rejected) as caught:
            checker.verify(self.report, forged)
        self.assertIn(fragment, str(caught.exception))

    def test_invented_open_anchor_names_are_refused(self):
        self.refuse(lambda f: f.__setitem__("open_anchors", ["not-an-anchor", "invented"]),
                    "reported open anchors are not the packet")

    def test_a_false_supported_criterion_is_refused(self):
        self.refuse(lambda f: f.__setitem__("improvement_criterion", "supported"),
                    "improvement criterion is not the packet")

    def test_an_invented_certified_list_is_refused(self):
        def invent(forged):
            forged["observation_list"] = {"count": 1, "atoms": ["A|present|ghost"],
                                          "certified_shortest": True, "lower_bound": 1,
                                          "bracket": {"lower": 1, "upper": 1}}
        self.refuse(invent, "carries an observation list")

    def test_an_invented_disputed_set_is_refused(self):
        self.refuse(lambda f: f.__setitem__("disputed_atoms",
                                            {"count": 1, "atoms": ["A|present|ghost"],
                                             "basis": "invented"}),
                    "not the one the readings support")

    def test_an_unknown_field_is_refused(self):
        self.refuse(lambda f: f.__setitem__("extra_unknown_field", {"anything": 1}),
                    "fields this checker does not know")

    def test_a_false_preference_is_refused(self):
        self.refuse(lambda f: f.__setitem__("preference", "prefer_augmented"),
                    "preference is not the packet")

    def test_a_false_packet_state_is_refused(self):
        self.refuse(lambda f: f.__setitem__("packet_state", "computed"),
                    "packet state is not the packet")

    def test_a_false_disagreement_flag_is_refused(self):
        self.refuse(lambda f: f["reference_alone_may_not_settle_it"].__setitem__(
            "readings_disagree_at_the_most_favourable_open_value", True), "recomputes to")

    def test_an_inflated_reading_count_is_refused(self):
        self.refuse(lambda f: f["reference_alone_may_not_settle_it"].__setitem__(
            "admitted_readings", 2), "admitted reading count is not the packet")

    def test_a_waiting_claim_on_a_settled_criterion_is_refused(self):
        report, listing = pair("settled-with-open-reference-case.json")
        forged = copy.deepcopy(listing)
        forged["state"] = "waits_on_a_reference"
        forged["observation_list"] = None
        forged.pop("settles")
        forged.pop("open_reference_preserved")
        forged["reference_alone_may_not_settle_it"] = {
            "admitted_readings": 1,
            "readings_disagree_at_the_least_favourable_open_value": False,
            "readings_disagree_at_the_most_favourable_open_value": False, "note": ""}
        with self.assertRaises(checker.Rejected) as caught:
            checker.verify(report, forged)
        self.assertIn("while the criterion is", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
