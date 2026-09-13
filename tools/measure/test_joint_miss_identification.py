"""Tests for the identification of the dependence coefficient from observed channels."""
from fractions import Fraction
from itertools import product
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import joint_miss_identification as jm  # noqa: E402

# The worked three channel table where the sign is settled with no reference.
SETTLED = {(0, 0, 1): 23, (0, 1, 0): 6, (0, 1, 1): 7,
           (1, 0, 0): 2, (1, 0, 1): 8, (1, 1, 0): 27}


def pairs(count=200, seed=20260913):
    rng = random.Random(seed)
    for _ in range(count):
        yield jm.two_channel_counts(rng.randint(1, 200), rng.randint(0, 200),
                                    rng.randint(0, 200))


def tables(count=300, seed=13):
    rng = random.Random(seed)
    patterns = [p for p in product([0, 1], repeat=3) if any(p)]
    for _ in range(count):
        yield {p: rng.randint(0, 40) for p in patterns}


class TheCaptureRecaptureFillReturnsItsOwnAssumption(unittest.TestCase):
    def test_the_identity_holds_on_every_two_channel_table(self):
        for counts in pairs():
            parts = jm.margins(counts)
            fill = jm.lincoln_petersen(parts)
            value = jm.coefficient(parts, fill) if fill is not None else None
            if value is None:
                continue
            with self.subTest(counts=counts):
                self.assertEqual(value, Fraction(1))

    def test_it_is_exact_and_not_an_approximation(self):
        parts = jm.margins(jm.two_channel_counts(97, 43, 31))
        value = jm.coefficient(parts, jm.lincoln_petersen(parts))
        self.assertIsInstance(value, Fraction)
        self.assertEqual(value, Fraction(1))

    def test_the_report_names_the_circularity(self):
        report = jm.analyse(jm.two_channel_counts(10, 5, 5))
        plug_in = report["capture_recapture_plug_in"]
        self.assertEqual(plug_in["coefficient_there"], "1")
        self.assertIn("reported its own assumption", plug_in["circularity"])

    def test_the_identity_is_scoped_to_this_estimator_and_its_domain(self):
        """It is not a statement about capture recapture methods in general."""
        plug_in = jm.analyse(jm.two_channel_counts(10, 5, 5))["capture_recapture_plug_in"]
        self.assertIn("not about capture recapture methods in general", plug_in["scope"])
        self.assertEqual(plug_in["defined_when"],
                         "some object is detected by both channels, so w > 0")

    def test_the_fitted_count_need_not_be_an_integer(self):
        """c = 1 is then attained off the grid the count actually lives on."""
        plug_in = jm.analyse(jm.two_channel_counts(10, 5, 5))["capture_recapture_plug_in"]
        self.assertEqual(plug_in["fitted_count"], "5/2")
        self.assertFalse(plug_in["fitted_count_is_an_integer"])

    def test_it_is_absent_where_it_is_undefined(self):
        self.assertIsNone(
            jm.analyse(jm.two_channel_counts(0, 5, 5))["capture_recapture_plug_in"])


class TheSignQuestionReducesExactly(unittest.TestCase):
    """c > 1 if and only if m * w > a * b - u * S, at any number of channels."""

    def test_the_reduction_holds_on_random_three_channel_tables(self):
        for counts in tables():
            parts = jm.margins(counts)
            threshold = jm.sign_threshold(parts)
            if threshold is None:
                continue
            for m in range(0, 60):
                value = jm.coefficient(parts, m)
                if value is None:
                    continue
                with self.subTest(counts=counts, m=m):
                    self.assertEqual(value > 1, Fraction(m) > threshold)

    def test_it_reduces_to_capture_recapture_when_there_are_two_channels(self):
        for counts in pairs(50):
            parts = jm.margins(counts)
            self.assertEqual(parts["u"], 0)
            self.assertEqual(jm.sign_threshold(parts), jm.lincoln_petersen(parts))

    def test_a_bound_above_the_threshold_decides_positive_coupling(self):
        report = jm.analyse(jm.two_channel_counts(10, 5, 5), low=3, high=8)
        self.assertEqual(report["sign_question"]["verdict"]["state"], "c_greater_than_1")

    def test_a_bound_below_the_threshold_decides_the_other_way(self):
        report = jm.analyse(jm.two_channel_counts(10, 5, 5), low=0, high=2)
        self.assertEqual(report["sign_question"]["verdict"]["state"], "c_less_than_1")

    def test_a_bound_spanning_the_threshold_decides_nothing(self):
        report = jm.analyse(jm.two_channel_counts(10, 5, 5), low=0, high=8)
        self.assertEqual(report["sign_question"]["verdict"]["state"], "undetermined")


class TwoChannelsDoNotIdentifyTheCoefficient(unittest.TestCase):
    def test_the_unbounded_range_spans_values_below_and_above_one(self):
        report = jm.analyse(jm.two_channel_counts(10, 5, 5))
        unbounded = report["coefficient_range_with_no_bound_at_all"]
        self.assertLess(Fraction(unbounded["minimum"]), 1)
        self.assertGreater(Fraction(unbounded["maximum"]), 1)

    def test_the_supremum_is_the_interior_maximum(self):
        unbounded = jm.analyse(jm.two_channel_counts(10, 5, 5))[
            "coefficient_range_with_no_bound_at_all"]
        self.assertEqual(unbounded["maximum"], "4/3")
        self.assertEqual(unbounded["maximum_at_m"], 10)

    def test_a_reference_is_required_for_the_sign(self):
        report = jm.analyse(jm.two_channel_counts(10, 5, 5))
        self.assertFalse(report["sign_question"]["settled_without_any_reference"])
        self.assertIn("entirely on one side of the threshold",
                      report["what_a_reference_must_deliver"])

    def test_no_two_channel_table_can_settle_the_sign_by_itself(self):
        """u is zero without a third channel, so the threshold is never negative."""
        for counts in pairs(80):
            threshold = jm.sign_threshold(jm.margins(counts))
            if threshold is None:
                continue
            with self.subTest(counts=counts):
                self.assertGreaterEqual(threshold, 0)


class AThirdChannelCanSettleTheSignWithoutAReference(unittest.TestCase):
    """The result that changes what the programme has to build."""

    def test_the_threshold_falls_below_zero_on_the_worked_table(self):
        parts = jm.margins(SETTLED)
        self.assertGreater(parts["u"], 0)
        self.assertLess(jm.sign_threshold(parts), 0)

    def test_the_coefficient_exceeds_one_for_every_admissible_dark_figure(self):
        parts = jm.margins(SETTLED)
        for m in (0, 1, 2, 7, 50, 1000, 10 ** 6):
            with self.subTest(m=m):
                self.assertGreater(jm.coefficient(parts, m), 1)

    def test_the_report_says_no_reference_is_needed_for_the_sign(self):
        report = jm.analyse(SETTLED)
        self.assertTrue(report["sign_question"]["settled_without_any_reference"])
        self.assertEqual(report["sign_question"]["verdict"]["state"], "c_greater_than_1")
        self.assertIn("nothing, for the sign question",
                      report["what_a_reference_must_deliver"])

    def test_it_is_the_third_channel_doing_the_work(self):
        """Collapsing the third channel away puts the threshold back above zero."""
        collapsed = {}
        for pattern, value in SETTLED.items():
            key = pattern[:2]
            if not any(key):
                continue          # these objects become unobservable again
            collapsed[key] = collapsed.get(key, 0) + value
        self.assertGreaterEqual(jm.sign_threshold(jm.margins(collapsed)), 0)


class TheLimitIsNotAnAttainedExtreme(unittest.TestCase):
    """An earlier version folded the limit into the extremes. They stay distinct."""

    def test_a_descending_coefficient_has_an_unattained_infimum_of_one(self):
        unbounded = jm.analyse(SETTLED)["coefficient_range_with_no_bound_at_all"]
        self.assertEqual(unbounded["infimum"], "1")
        self.assertFalse(unbounded["infimum_attained"])
        self.assertIsNone(unbounded["minimum"])
        self.assertTrue(unbounded["no_minimum_exists"])

    def test_an_attained_minimum_is_reported_as_attained(self):
        unbounded = jm.analyse(jm.two_channel_counts(10, 5, 5))[
            "coefficient_range_with_no_bound_at_all"]
        self.assertEqual(unbounded["infimum"], "0")
        self.assertTrue(unbounded["infimum_attained"])

    def test_the_limit_is_never_reached_at_any_count(self):
        parts = jm.margins(SETTLED)
        for m in (10 ** 3, 10 ** 6, 10 ** 9):
            self.assertNotEqual(jm.coefficient(parts, m), 1)


class TheRangeIsNotReadOffTheEndpoints(unittest.TestCase):
    def test_the_interior_maximum_exceeds_both_endpoints(self):
        parts = jm.margins(jm.two_channel_counts(10, 5, 5))
        ends = [jm.coefficient(parts, m) for m in (2, 30)]
        self.assertGreater(jm.coefficient(parts, 10), max(ends))

    def test_the_module_reports_the_interior_value(self):
        declared = jm.analyse(jm.two_channel_counts(10, 5, 5), low=2, high=30)[
            "coefficient_range_under_the_declared_bound"]
        self.assertEqual(declared["maximum"], "4/3")
        self.assertEqual(declared["maximum_at_m"], 10)
        self.assertNotIn(declared["maximum_at_m"], (2, 30))

    def test_the_bracketing_finds_the_true_extremes(self):
        """Checked against a full scan, on two and three channel tables alike."""
        for counts in list(pairs(20)) + list(tables(20)):
            parts = jm.margins(counts)
            low, high = 0, 400
            report = jm.range_over(parts, low, high)
            if report["state"] != "computed":
                continue
            scan = [jm.coefficient(parts, m) for m in range(low, high + 1)]
            scan = [v for v in scan if v is not None]
            with self.subTest(counts=counts):
                self.assertEqual(Fraction(report["maximum"]), max(scan))
                self.assertEqual(Fraction(report["minimum"]), min(scan))


class DegenerateCountsAreStatesNotZeros(unittest.TestCase):
    def test_no_joint_detection_removes_the_threshold_but_not_the_sign(self):
        """Reproduced defect: 0.2.0 reported undetermined here."""
        report = jm.analyse(jm.two_channel_counts(0, 5, 5))
        self.assertIsNone(report["sign_question"]["threshold"])
        self.assertIn("settled outright", report["sign_question"]["threshold_absent_because"])
        self.assertEqual(report["sign_question"]["verdict"]["state"], "c_less_than_1")

    def test_a_channel_that_misses_nothing_leaves_the_ratio_undefined(self):
        self.assertIsNone(jm.coefficient(jm.margins(jm.two_channel_counts(10, 0, 0)), 0))

    def test_the_unobservable_cell_cannot_be_declared_as_observed(self):
        with self.assertRaises(jm.CountError) as caught:
            jm.margins({(0, 0): 5, (1, 1): 3})
        self.assertIn("the quantity under analysis, not an input", str(caught.exception))

    def test_negative_counts_are_refused(self):
        with self.assertRaises(jm.CountError):
            jm.two_channel_counts(-1, 1, 1)

    def test_an_upper_bound_below_the_lower_bound_is_refused(self):
        with self.assertRaises(jm.CountError):
            jm.range_over(jm.margins(jm.two_channel_counts(10, 5, 5)), low=9, high=3)


class ItEstimatesNothing(unittest.TestCase):
    def test_the_scope_disclaims_estimation(self):
        scope = jm.analyse(jm.two_channel_counts(10, 5, 5))["scope"]
        for phrase in ("No population is sampled", "no channel is named",
                       "no value of c is estimated"):
            self.assertIn(phrase, scope)


class ADefinition32ConstantIsQuantitativeNotASign(unittest.TestCase):
    """The retained primary text states P[both] <= c P[A] P[B]: a constant, not a sign.

    An earlier version of this lane's document said a third channel "can give only
    the sign unless the dark figure is also bounded". This lane's own arithmetic
    contradicted it, and the supremum it already computed is exactly the smallest
    admissible constant.
    """

    def test_a_constant_is_supplied_with_no_reference_at_all(self):
        for counts, expected in ((SETTLED, "1679/1188"),
                                 (jm.two_channel_counts(10, 5, 5), "4/3")):
            constant = jm.analyse(counts)["definition_32_constant"]
            with self.subTest(counts=counts):
                self.assertEqual(constant["state"], "computed")
                self.assertEqual(constant["smallest_admissible_constant"], expected)

    def test_the_constant_really_bounds_every_admissible_count(self):
        for counts in (SETTLED, jm.two_channel_counts(10, 5, 5)):
            parts = jm.margins(counts)
            bound = Fraction(jm.analyse(counts)["definition_32_constant"][
                "smallest_admissible_constant"])
            for m in (0, 1, 2, 9, 37, 500, 10 ** 5):
                value = jm.coefficient(parts, m)
                if value is None:
                    continue
                with self.subTest(counts=counts, m=m):
                    self.assertLessEqual(value, bound)

    def test_it_is_the_smallest_such_constant(self):
        parts = jm.margins(SETTLED)
        bound = Fraction(jm.analyse(SETTLED)["definition_32_constant"][
            "smallest_admissible_constant"])
        attained = any(jm.coefficient(parts, m) == bound for m in range(0, 200))
        self.assertTrue(attained)

    def test_the_report_says_what_definition_32_does_not_supply(self):
        constant = jm.analyse(SETTLED)["definition_32_constant"]
        missing = constant["what_it_does_not_supply"]
        self.assertIn("marginal miss bounds", missing)
        self.assertIn("safety critic event", missing)
        self.assertIn("ghost", missing)

    def test_a_tighter_reference_bound_gives_a_tighter_constant(self):
        loose = Fraction(jm.analyse(jm.two_channel_counts(10, 5, 5))[
            "definition_32_constant"]["smallest_admissible_constant"])
        tight = Fraction(jm.analyse(jm.two_channel_counts(10, 5, 5), low=0, high=2)[
            "definition_32_constant"]["smallest_admissible_constant"])
        self.assertLess(tight, loose)


class TheSixReproducedIdentificationDefects(unittest.TestCase):
    """Every counterexample an Engine review raised against version 0.2.0.

    Each was reproduced against the exact source before any repair, and each is
    retained here with the behaviour that was wrong and the behaviour that
    replaces it. They were three separate kinds of fault: code defects, an
    incomplete classification, and prose broader than what was computed.
    """

    def test_one_the_boundary_the_published_condition_got_wrong(self):
        """Published prose said a*b <= u*S gives c > 1. At equality c(0) = 1."""
        counts = {(1, 1, 0): 1, (1, 0, 1): 1, (0, 1, 1): 1, (0, 0, 1): 1}
        parts = jm.margins(counts)
        self.assertEqual(parts["a"] * parts["b"], parts["u"] * parts["S"])
        self.assertEqual(jm.coefficient(parts, 0), Fraction(1))
        state, reason = jm.sign_over(parts, 0, None)
        self.assertEqual(state, "c_at_least_1")
        self.assertIn("does not establish", reason)

    def test_two_a_range_with_no_minimum_reports_none(self):
        """0.2.0 named 21/11 the smallest value; m = 2 gives 11/6."""
        counts = {(1, 1, 0): 10, (0, 0, 1): 10}
        parts = jm.margins(counts)
        self.assertLess(jm.coefficient(parts, 2), jm.coefficient(parts, 1))
        unbounded = jm.range_over(parts, 0, None)
        self.assertIsNone(unbounded["minimum"])
        self.assertTrue(unbounded["no_minimum_exists"])
        self.assertEqual(unbounded["infimum"], "1")
        self.assertFalse(unbounded["infimum_attained"])
        self.assertEqual(unbounded["maximum"], "2")

    def test_three_zero_joint_detections_still_settle_the_sign(self):
        """0.2.0 reported undetermined; c(m) = 1 - 1/(m+1)^2 is below 1 always."""
        parts = jm.margins(jm.two_channel_counts(0, 1, 1))
        for m in (0, 1, 5, 1000):
            self.assertLess(jm.coefficient(parts, m), 1)
        self.assertEqual(jm.sign_over(parts, 0, None)[0], "c_less_than_1")

    def test_four_an_undefined_coefficient_is_not_a_sign_verdict(self):
        """0.2.0 reported c_at_most_1 where the ratio had no value."""
        parts = jm.margins(jm.two_channel_counts(10, 0, 5))
        self.assertIsNone(jm.coefficient(parts, 0))
        self.assertEqual(jm.sign_over(parts, 0, 0)[0], "undefined")
        report = jm.analyse(jm.two_channel_counts(10, 0, 5), low=0, high=0)
        self.assertEqual(report["sign_question"]["verdict"]["state"], "undefined")
        self.assertFalse(report["coefficient_defined_at_zero"])

    def test_five_a_constant_coefficient_attains_its_limit(self):
        """0.2.0 declared the limit never attained, which a constant one contradicts."""
        parts = jm.margins({(0, 0, 1): 10})
        for m in (0, 3, 99):
            self.assertEqual(jm.coefficient(parts, m), Fraction(1))
        self.assertEqual(jm.sign_over(parts, 0, None)[0], "c_equals_1")
        unbounded = jm.range_over(parts, 0, None)
        self.assertTrue(unbounded["as_m_grows"]["attained"])

    def test_six_boolean_bounds_are_refused(self):
        parts = jm.margins(jm.two_channel_counts(10, 5, 5))
        for bad in ({"low": True}, {"high": False}):
            with self.subTest(bound=bad):
                with self.assertRaises(jm.CountError):
                    jm.range_over(parts, **bad)

    def test_the_identified_set_is_declared_discrete(self):
        """Counts are integers, so an interval encloses the set, it does not list it."""
        unbounded = jm.range_over(jm.margins(jm.two_channel_counts(10, 5, 5)), 0, None)
        self.assertIn("discrete", unbounded["identified_set"])

    def test_the_retained_three_channel_result_survives_every_repair(self):
        report = jm.analyse(SETTLED)
        self.assertEqual(report["sign_question"]["verdict"]["state"], "c_greater_than_1")
        self.assertEqual(report["sign_question"]["threshold"], "-491/27")
        self.assertTrue(report["sign_question"]["settled_without_any_reference"])


if __name__ == "__main__":
    unittest.main()
