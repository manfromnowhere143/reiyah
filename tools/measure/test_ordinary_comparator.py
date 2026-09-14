"""Tests for the end to end comparison, including the results that go against this lane."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_cohort_packet as packet_checker  # noqa: E402
import check_observation_cover as cover_checker  # noqa: E402
import ordinary_comparator as comparator  # noqa: E402

ARTIFACT = os.path.join(comparator.ROOT, "research", "comparator", "0.2.0", "end-to-end.json")
ENGINE_CASE = os.environ.get("REIYAH_ENGINE_CASE")


class EndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = comparator.report()

    def test_every_selected_case_is_bound_by_digest(self):
        for entry in self.result["cases"]:
            path = os.path.join(comparator.ROOT, entry["identity"]["path"])
            self.assertEqual(entry["identity"]["sha256"], comparator.digest(path))

    def test_the_live_comparison_is_still_open_at_minus_eight_to_eight(self):
        live = next(e for e in self.result["cases"] if e["case"] == "open-two-anchor.json")
        self.assertEqual(live["instrument"]["state"], "open_reference_only")
        self.assertEqual(live["instrument"]["enclosure"], {"lower": "-8", "upper": "8"})
        self.assertEqual(live["instrument"]["improvement_criterion"], "unresolved")
        self.assertEqual(live["observations_that_would_change_the_decision"]["state"],
                         "waits_on_a_reference")
        self.assertIsNone(live["observations_that_would_change_the_decision"]["certified_list"])

    def test_no_case_claims_a_resolved_real_verdict(self):
        live = next(e for e in self.result["cases"] if e["case"] == "open-two-anchor.json")
        self.assertEqual(live["identity"]["admitted_readings"], 0)
        self.assertEqual(live["witness_or_obstruction"]["kind"], "obstruction")

    def test_every_decided_case_carries_a_matching_that_meets_its_cover(self):
        decided = [e for e in self.result["cases"]
                   if e["witness_or_obstruction"]["kind"] == "witness"]
        self.assertGreaterEqual(len(decided), 3)
        for entry in decided:
            self.assertTrue(entry["witness_or_obstruction"]
                            ["every_matching_meets_a_cover_of_equal_size"])

    def test_every_unresolved_case_names_its_discordant_readings_or_its_open_anchor(self):
        for entry in self.result["cases"]:
            if entry["instrument"]["improvement_criterion"] != "unresolved":
                continue
            obstruction = entry["witness_or_obstruction"]
            self.assertEqual(obstruction["kind"], "obstruction")
            self.assertTrue(obstruction.get("discordant_pairs")
                            or obstruction["name"] == "no admitted reading")

    def test_the_equivalence_that_limits_this_lane_is_reported_and_holds(self):
        checked = 0
        for entry in self.result["cases"]:
            equivalence = entry["conventional"]["equivalence"]
            if equivalence.get("holds") is None:
                continue
            self.assertTrue(equivalence["holds"])
            checked += 1
        self.assertGreaterEqual(checked, 6)

    def test_the_costs_name_where_this_lane_is_behind(self):
        summary = self.result["costs"]["summary"]
        self.assertTrue(summary["where_it_is_behind"])
        self.assertTrue(summary["where_it_is_level"])
        self.assertIsNone(self.result["costs"]["human_effort"]["value"])
        self.assertEqual(self.result["costs"]["human_effort"]["state"], "unmeasured")

    def test_the_observation_list_is_shorter_than_the_diff_it_replaces(self):
        value = self.result["costs"]["interpretation"]["value"]
        self.assertLess(value["certified_or_checkable_list"], value["diff_the_analyst_gets_free"])
        self.assertGreaterEqual(value["cases_counted"], 6)

    def test_the_checkers_import_nothing_from_the_producers(self):
        for module in (packet_checker, cover_checker):
            with open(module.__file__, "r", encoding="utf-8") as handle:
                text = handle.read()
            for producer in ("cohort_packet", "observation_cover", "conventional_comparator"):
                self.assertNotIn(f"import {producer}", text)

    def test_every_conformance_instance_was_accepted_by_both_checkers(self):
        conformance = self.result["synthetic_conformance"]
        self.assertEqual(conformance["instances"],
                         conformance["instances_both_checkers_accepted"])
        self.assertGreaterEqual(conformance["instances"], 1000)
        for name in ("bracketed", "certified_shortest", "searched_shortest", "already_decided"):
            self.assertGreater(conformance["states"][name], 0, name)

    def test_a_searched_optimum_is_counted_apart_from_a_certificate(self):
        """The 0.1.0 defect: 386 covered were all reported certified; 378 are."""
        conformance = self.result["synthetic_conformance"]
        states = conformance["states"]
        self.assertEqual(states["certified_shortest"] + states["searched_shortest"], 386)
        self.assertEqual(states["certified_shortest"], 378)
        self.assertEqual(states["searched_shortest"], 8)
        self.assertEqual(conformance["cases_needing_a_list"],
                         states["certified_shortest"] + states["searched_shortest"]
                         + states["bracketed"])
        self.assertEqual(conformance["certified_shortest_share"], "378 of 717")
        self.assertEqual(conformance["searched_but_not_certified"], 8)

    def test_the_first_searched_but_uncertified_instance_is_where_it_was_reported(self):
        listing = comparator.roundtrip(
            __import__("observation_cover").analyse(comparator.synthetic_case(4, 9)))
        self.assertEqual(listing["state"], "searched_shortest")
        self.assertFalse(listing["observation_list"]["certified_shortest"])
        self.assertEqual(listing["observation_list"]["count"], 2)
        self.assertEqual(listing["observation_list"]["lower_bound"], 1)

    def test_the_checking_cost_is_stated_in_traced_operations(self):
        """The 0.1.0 claim of linear checking is corrected, not optimised away."""
        cost = self.result["checking_cost"]
        traced = {row["discordant_pairs"]: row for row in cost["traced"]}
        self.assertEqual(traced[8]["pair_verdict_comparisons"], 36)
        self.assertEqual(traced[16]["pair_verdict_comparisons"], 136)
        self.assertEqual(traced[32]["pair_verdict_comparisons"], 528)
        for row in cost["traced"]:
            self.assertEqual(row["pair_verdict_comparisons"],
                             row["admitted_readings"] * (row["admitted_readings"] - 1) // 2)
            self.assertEqual(row["supplied_certificate_atoms"], 1)
        self.assertIn("not timing", cost["note"])

    def test_the_engine_case_is_acknowledged_without_being_copied_in(self):
        record = self.result["engine_case_compatibility"]
        if record["state"] == "unavailable":
            self.assertEqual(record["expected_sha256"], comparator.ENGINE_CASE_SHA256)
            self.skipTest("the owner's private case was not supplied to this run")
        self.assertEqual(record["state"], "checked")
        self.assertEqual(record["sha256"], comparator.ENGINE_CASE_SHA256)
        self.assertEqual(record["admitted_readings"], 0)
        self.assertEqual(record["result"]["enclosure"], {"lower": "-8", "upper": "8"})
        self.assertEqual(record["result"]["improvement_criterion"], "unresolved")
        self.assertEqual(record["result"]["observation_state"], "waits_on_a_reference")
        self.assertIsNone(record["result"]["observation_list"])
        self.assertEqual([row["base_detections"] for row in record["structure"]], [48, 37])
        self.assertEqual([row["added_detections"] for row in record["structure"]], [9, 7])
        text = json.dumps(record)
        self.assertNotIn("row-00", text)

    def test_a_case_whose_digest_does_not_match_is_refused(self):
        path = os.path.join(comparator.ROOT, "research", "cohort-packet", "0.1.0",
                            "open-two-anchor.json")
        record = comparator.compatibility(path)
        self.assertEqual(record["state"], "digest_mismatch")
        self.assertNotIn("result", record)

    def test_the_conformance_generator_is_deterministic(self):
        first = comparator.synthetic_case(6, 3)
        second = comparator.synthetic_case(6, 3)
        self.assertEqual(first, second)

    def test_the_retained_artifact_matches_a_fresh_run(self):
        if not os.path.exists(ARTIFACT):
            self.skipTest("artifact not written yet")
        with open(ARTIFACT, "r", encoding="utf-8") as handle:
            stored = json.load(handle)
        for stored_case, fresh_case in zip(stored["cases"], self.result["cases"]):
            self.assertEqual(stored_case["identity"], fresh_case["identity"])
            self.assertEqual(stored_case["instrument"], fresh_case["instrument"])
            self.assertEqual(stored_case["observations_that_would_change_the_decision"],
                             fresh_case["observations_that_would_change_the_decision"])
        self.assertEqual(stored["synthetic_conformance"]["states"],
                         self.result["synthetic_conformance"]["states"])
        self.assertEqual(stored["checking_cost"]["traced"], self.result["checking_cost"]["traced"])


if __name__ == "__main__":
    unittest.main()
