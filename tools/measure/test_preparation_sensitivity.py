"""Tests for the bounded end to end case over original submitted rows."""
from fractions import Fraction
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preparation_sensitivity as ps  # noqa: E402


class ThePacketIsConsumedAsOriginalRows(unittest.TestCase):
    def test_the_producer_performed_no_association(self):
        self.assertFalse(ps.load()["consumed_packet"]["association_performed_by_producer"])

    def test_no_reference_judgement_is_admitted(self):
        self.assertFalse(ps.load()["consumed_packet"]["reference_judgments_admitted"])

    def test_a_packet_with_producer_association_is_refused(self):
        data = ps.load()
        data["consumed_packet"]["association_performed_by_producer"] = True
        import json, tempfile
        path = os.path.join(tempfile.mkdtemp(), "counts.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle)
        with self.assertRaises(ps.PacketError) as caught:
            ps.load(path)
        self.assertIn("producer performed association", str(caught.exception))

    def test_every_selected_row_carried_its_own_digest(self):
        self.assertEqual(ps.load()["consumed_packet"]["rows_with_per_row_digests"], 4876)

    def test_the_exposure_state_is_carried_through(self):
        self.assertIn("exposed", ps.load()["consumed_packet"]["exposure"])


class TheRowsDoNotDecideTheIntegrationQuestion(unittest.TestCase):
    def test_the_verdict_is_abstain(self):
        self.assertEqual(ps.report()["verdict"], "abstain")

    def test_every_row_abstains_rather_than_recommending(self):
        for row in ps.report()["rows"]:
            with self.subTest(row=(row["score_minimum"], row["association_radius_m"])):
                self.assertIn(row["state"], ("abstain", "no_addition_retained"))

    def test_a_zero_retained_addition_is_its_own_state(self):
        self.assertEqual(ps.decide(0)["state"], "no_addition_retained")
        self.assertNotIn("bound", ps.decide(0))

    def test_the_coarse_bound_is_symmetric_at_unit_penalties(self):
        self.assertEqual(ps.coarse_bound(7), {"lower": "-7", "upper": "7"})

    def test_unequal_penalties_move_the_bound(self):
        self.assertEqual(ps.coarse_bound(5, false_negative=2, false_positive=3),
                         {"lower": "-15", "upper": "10"})

    def test_a_negative_count_is_refused(self):
        with self.assertRaises(ps.PacketError):
            ps.coarse_bound(-1)


class TheBoundItselfIsNotDetermined(unittest.TestCase):
    def test_the_retained_additions_span_an_order_of_magnitude(self):
        span = ps.report()["and_the_bound_is_not_determined_either"]
        self.assertGreater(Fraction(span["ratio"]), 10)

    def test_the_score_cutoff_dominates_the_association_radius(self):
        which = ps.report()["which_preparation_choice_carries_it"]
        self.assertEqual(which["dominant"], "score_cutoff")
        self.assertGreater(Fraction(which["score_cutoff"]), Fraction(which["association_radius"]))

    def test_the_dominance_reverses_the_previous_checkpoint(self):
        note = ps.report()["which_preparation_choice_carries_it"]["reading"]
        self.assertIn("previous checkpoint found the radius dominant", note)
        self.assertIn("neither can be assumed from the other", note)

    def test_every_bound_is_consistent_with_its_count(self):
        for row in ps.report()["rows"]:
            with self.subTest(count=row["retained_additions"]):
                self.assertEqual(row["coarse_bound"],
                                 ps.coarse_bound(row["retained_additions"]))


class ItDoesNotOverclaim(unittest.TestCase):
    def test_no_comparison_with_the_engine_result_is_made(self):
        limits = ps.report()["not_established"]
        self.assertTrue(any("two window result" in item for item in limits))
        self.assertTrue(any("preparation this lane does not own" in item for item in limits))

    def test_the_overlap_parity_is_stated_again(self):
        note = ps.report()["the_overlap_baseline_gets_the_same_number"]
        self.assertIn("parity holds", note)

    def test_the_settling_observation_is_named(self):
        note = ps.report()["observation_that_would_settle_it"]
        self.assertIn("coordinate and timing uncertainty", note)
        self.assertIn("admitted references", note)

    def test_no_physical_object_is_declared(self):
        limits = ps.report()["not_established"]
        self.assertTrue(any("joined pair is a physical object" in item for item in limits))


if __name__ == "__main__":
    unittest.main()
