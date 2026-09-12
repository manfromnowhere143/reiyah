"""Tests for admission sensitivity, including the result that humbles this lane."""
from fractions import Fraction
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import admission_sensitivity as sens  # noqa: E402
import conventional_comparator as conventional  # noqa: E402

CASES = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "research", "cohort-packet", "0.1.0")


def cases():
    for name in sorted(os.listdir(CASES)):
        if not name.endswith(".json") or name == "answer-prerequisites.json":
            continue
        with open(os.path.join(CASES, name), "r", encoding="utf-8") as handle:
            case = json.load(handle)
        if "joint_worlds" in case:
            yield name, case


def load(name):
    with open(os.path.join(CASES, name), "r", encoding="utf-8") as handle:
        return json.load(handle)


class AdmissionIsMonotone(unittest.TestCase):
    def test_a_larger_admitted_set_gives_a_containing_enclosure(self):
        for name, case in cases():
            holds = sens.monotone_admission_holds(case)
            if holds is None:
                continue
            with self.subTest(case=name):
                self.assertTrue(holds)

    def test_removing_a_reading_never_weakened_a_verdict(self):
        """Omission can only sharpen. If this ever fails the defect is in the module."""
        for name, case in cases():
            result = sens.analyse(case)
            if "criterion" not in result:
                continue
            with self.subTest(case=name):
                self.assertFalse(result["omission_asymmetry"]["a_single_omission_weakened_the_verdict"])

    def test_a_decisive_verdict_survives_every_single_omission(self):
        for name, case in cases():
            result = sens.analyse(case)
            if result.get("criterion") not in ("supported", "excluded"):
                continue
            for entry in result["load_bearing_readings"]:
                with self.subTest(case=name, removed=entry["world_id"]):
                    self.assertEqual(entry["criterion_without_it"], result["criterion"])


class EveryDecisiveVerdictRestsOnCompleteness(unittest.TestCase):
    """The finding. It is not favourable and it is not softened."""

    def decisive(self):
        for name, case in cases():
            result = sens.analyse(case)
            if result.get("criterion") in ("supported", "excluded"):
                yield name, result

    def test_there_are_decisive_cases_to_talk_about(self):
        self.assertGreaterEqual(len(list(self.decisive())), 4)

    def test_the_admitted_readings_pin_the_value_to_a_point(self):
        for name, result in self.decisive():
            with self.subTest(case=name):
                self.assertEqual(result["enclosure"]["lower"], result["enclosure"]["upper"])

    def test_the_admission_carries_the_whole_conclusion(self):
        for name, result in self.decisive():
            with self.subTest(case=name):
                self.assertEqual(Fraction(result["how_much_is_asserted"]["asserted_share"]), 1)

    def test_a_verdict_destroying_reading_is_structurally_permitted_in_all_of_them(self):
        for name, result in self.decisive():
            with self.subTest(case=name):
                self.assertTrue(
                    result["required_exclusion"]["such_a_reading_is_structurally_permitted"])
                self.assertIn("only if the admitted set is complete",
                              result["required_exclusion"]["consequence"])

    def test_the_required_exclusion_names_the_tolerance(self):
        result = sens.analyse(load("worst-group-masking-case.json"))
        self.assertEqual(result["criterion"], "supported")
        self.assertIn("at or below the tolerance", result["required_exclusion"]["statement"])


class AnUnresolvedVerdictClaimsNothingAboutOmittedReadings(unittest.TestCase):
    def test_it_makes_no_completeness_claim(self):
        result = sens.analyse(load("adaptive-beats-fixed-case.json"))
        self.assertEqual(result["criterion"], "unresolved")
        self.assertIsNone(result["required_exclusion"]["such_a_reading_is_structurally_permitted"])
        self.assertIn("nothing", result["required_exclusion"]["statement"])

    def test_the_live_comparison_eliminates_nothing(self):
        result = sens.analyse(load("open-two-anchor.json"))
        self.assertEqual(Fraction(result["how_much_is_asserted"]["asserted_share"]), 0)
        self.assertEqual(result["enclosure"], result["coarse_bound"])


class ASingleAdmittedReadingIsTheConventionalAnalyst(unittest.TestCase):
    """The synthesis with the comparator result, asserted rather than implied."""

    def test_one_reading_gives_a_point_answer_and_asserts_everything(self):
        case = load("worst-group-masking-case.json")
        self.assertEqual(len(case["joint_worlds"]), 1)
        result = sens.analyse(case)
        self.assertEqual(Fraction(result["how_much_is_asserted"]["asserted_share"]), 1)

    def test_the_instrument_and_the_comparator_agree_exactly_there(self):
        case = load("worst-group-masking-case.json")
        comparison = conventional.compare(case)
        readings = comparison["conventional_single_interpretation"]["readings"]
        self.assertEqual(len(readings), 1)
        self.assertEqual(comparison["instrument"]["improvement_criterion"], readings[0]["verdict"])
        self.assertIn("confirmation only", comparison["what_the_instrument_adds"])


class ItRefusesWhatItCannotEnumerate(unittest.TestCase):
    def test_too_many_readings_is_refused_before_the_work(self):
        case = load("adaptive-beats-fixed-case.json")
        original = sens.MAX_WORLDS
        sens.MAX_WORLDS = 2
        try:
            with self.assertRaises(Exception):
                sens.analyse(case)
        finally:
            sens.MAX_WORLDS = original

    def test_it_says_it_cannot_discharge_the_dependence_it_measures(self):
        result = sens.analyse(load("adaptive-beats-fixed-case.json"))
        self.assertIn("cannot discharge the dependence", result["scope"])


if __name__ == "__main__":
    unittest.main()
