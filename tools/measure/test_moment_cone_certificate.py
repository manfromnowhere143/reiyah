"""Adversarial and property tests for the moment-cone certificate pair.

The tests that matter here are the ones that would let a wrong decision through:
a forged certificate, a multiplier that is not nonnegative on [0,1], a measure
with a negative weight, a box claim backed by only a centre calculation, and a
grid failure silently reported as a refutation.
"""
from fractions import Fraction
import copy
import unittest

import moment_cone_certificate as producer
import check_moment_cone_certificate as checker

SMALL_GRID = {"coarse_denominator": 60, "fine_denominator": 6000}


def task(moments, half=None, **extra):
    body = {"schema_id": "reiyah.moment-cone.task",
            "population_label": "test",
            "channel_count": len(moments),
            "moments": list(moments)}
    if half is not None:
        body["rounding_half_width"] = half
    body.update(SMALL_GRID)
    body.update(extra)
    return body


def run(moments, half=None, **extra):
    body = task(moments, half, **extra)
    return body, producer.decide(body)


class ClosedFormOracle(unittest.TestCase):
    """For two channels the [0,1] moment problem has an elementary criterion.

    A measure on [0,1] with moments m1, m2 exists exactly when m1^2 <= m2 <= m1:
    the lower bound is Cauchy-Schwarz, the upper is x^2 <= x on [0,1]. The
    procedure is checked against that criterion rather than against itself.
    """

    def test_two_channel_grid_against_closed_form(self):
        checked = 0
        for numerator in range(1, 12):
            m1 = Fraction(numerator, 12)
            for second in range(0, 13):
                m2 = Fraction(second, 12)
                if m2 > 1:
                    continue
                expected = (m1 * m1 <= m2 <= m1)
                body, report = run([str(m1.numerator) + "/" + str(m1.denominator)
                                    if False else _dec(m1), _dec(m2)])
                verdict = report["verdict"]
                if expected:
                    self.assertIn(verdict, ("feasible_at_centre", "feasible_over_box", "unresolved"),
                                  f"m1={m1} m2={m2} gave {verdict}")
                    if verdict.startswith("feasible"):
                        checker.verify(body, report)
                else:
                    self.assertTrue(verdict.startswith("infeasible"),
                                    f"m1={m1} m2={m2} should be infeasible, got {verdict}")
                    checker.verify(body, report)
                checked += 1
        self.assertGreater(checked, 100)

    def test_point_mass_boundary_is_feasible(self):
        body, report = run(["0.25", "0.0625", "0.015625"])
        self.assertTrue(report["verdict"].startswith("feasible"), report)
        checker.verify(body, report)

    def test_variance_violation_is_infeasible(self):
        body, report = run(["0.5", "0.2"])
        self.assertTrue(report["verdict"].startswith("infeasible"))
        outcome = checker.verify(body, report)
        self.assertEqual(outcome["checked"]["multiplier"], "1")


class RetainedPopulations(unittest.TestCase):
    def test_all_annotated_objects_infeasible_over_box(self):
        body, report = run(["0.207356", "0.102807", "0.069423", "0.055554", "0.047427"],
                           half="0.0000005")
        self.assertEqual(report["verdict"], "infeasible_over_box")
        self.assertEqual(report["certificate"]["form"], "x")
        checker.verify(body, report)

    def test_short_hand_checkable_witness_also_certifies(self):
        """A second, shorter certificate for the same conclusion.

        The procedure selects on box margin and so emits (233, -1145, 1000).
        The three-integer polynomial (23, -115, 100) certifies the same thing with
        a smaller margin and is small enough to check by hand, so it is kept.
        """
        moments = [Fraction(1)] + [Fraction(text) for text in
                                   ("0.207356", "0.102807", "0.069423", "0.055554", "0.047427")]
        halves = [Fraction(1, 2000000)] * 5
        direction = [Fraction(23), Fraction(-115), Fraction(100)]
        coefficients = producer.expand_certificate("x", direction)
        self.assertEqual([str(value) for value in coefficients],
                         ["0", "529", "-5290", "17825", "-23000", "10000"])
        centre = producer.functional(coefficients, moments)
        worst = producer.box_worst_case(coefficients, moments, halves)
        self.assertEqual(centre, Fraction(-164731, 1000000))
        self.assertEqual(worst, Fraction(-136409, 1000000))
        self.assertLess(worst, 0)

    def test_most_observable_is_not_infeasible(self):
        body, report = run(["0.043834", "0.010316", "0.004383", "0.002826", "0.002196"])
        self.assertTrue(report["verdict"].startswith("feasible"), report["verdict"])
        checker.verify(body, report)


class ForgedCertificates(unittest.TestCase):
    def setUp(self):
        self.body, self.report = run(["0.5", "0.2"])
        self.assertTrue(self.report["verdict"].startswith("infeasible"))

    def _reject(self, mutate):
        forged = copy.deepcopy(self.report)
        mutate(forged)
        with self.assertRaises(checker.Rejected):
            checker.verify(self.body, forged)

    def test_expansion_that_is_not_the_square(self):
        def mutate(report):
            coefficients = report["certificate"]["expanded_coefficients"]
            coefficients[0] = str(Fraction(coefficients[0]) - 1)
        self._reject(mutate)

    def test_multiplier_that_is_negative_somewhere_on_the_interval(self):
        def mutate(report):
            report["certificate"]["form"] = "x-1"
        self._reject(mutate)

    def test_functional_value_overstated(self):
        def mutate(report):
            report["certificate"]["functional_at_centre"] = "-1"
        self._reject(mutate)

    def test_zero_polynomial(self):
        def mutate(report):
            report["certificate"]["polynomial_coefficients"] = ["0", "0", "0"]
            report["certificate"]["expanded_coefficients"] = ["0"] * 3
        self._reject(mutate)

    def test_box_claim_without_box_margin(self):
        body, report = run(["0.207356", "0.102807", "0.069423", "0.055554", "0.047427"],
                           half="0.01")
        self.assertEqual(report["verdict"], "infeasible_at_centre_only")
        checker.verify(body, report)
        forged = copy.deepcopy(report)
        forged["verdict"] = "infeasible_over_box"
        with self.assertRaises(checker.Rejected):
            checker.verify(body, forged)

    def test_report_may_not_narrow_its_own_rounding_box(self):
        """A box verdict must be earned against the box the task declared."""
        body, report = run(["0.207356", "0.102807", "0.069423", "0.055554", "0.047427"],
                           half="0.01")
        self.assertEqual(report["verdict"], "infeasible_at_centre_only")
        forged = copy.deepcopy(report)
        forged["verdict"] = "infeasible_over_box"
        forged["rounding_half_width"] = ["0"] * 5
        forged["certificate"]["functional_box_worst_case"] = \
            forged["certificate"]["functional_at_centre"]
        with self.assertRaises(checker.Rejected):
            checker.verify(body, forged)

    def test_certificate_moved_to_a_different_moment_vector(self):
        other, _ = run(["0.4", "0.3"])
        forged = copy.deepcopy(self.report)
        with self.assertRaises(checker.Rejected):
            checker.verify(other, forged)


class ForgedMeasures(unittest.TestCase):
    def setUp(self):
        self.body, self.report = run(["0.25", "0.0625", "0.015625"])
        self.assertTrue(self.report["verdict"].startswith("feasible"))

    def _reject(self, mutate):
        forged = copy.deepcopy(self.report)
        mutate(forged)
        with self.assertRaises(checker.Rejected):
            checker.verify(self.body, forged)

    def test_negative_weight(self):
        def mutate(report):
            support = report["measure"]["centre"]
            support.append(["1/2", "-1/1000"])
            support.append(["0", "1/1000"])
        self._reject(mutate)

    def test_atom_outside_the_interval(self):
        def mutate(report):
            report["measure"]["centre"][0][0] = "3/2"
        self._reject(mutate)

    def test_weights_do_not_sum_to_one(self):
        def mutate(report):
            atom, weight = report["measure"]["centre"][0]
            report["measure"]["centre"][0] = [atom, str(Fraction(weight) / 2)]
        self._reject(mutate)

    def test_moments_not_reproduced(self):
        def mutate(report):
            report["measure"]["centre"] = [["0", "1/2"], ["1", "1/2"]]
        self._reject(mutate)

    def test_missing_box_corner(self):
        body, report = run(["0.3", "0.2"], half="0.0001")
        self.assertEqual(report["verdict"], "feasible_over_box")
        checker.verify(body, report)
        forged = copy.deepcopy(report)
        forged["measure"]["corners"].pop()
        with self.assertRaises(checker.Rejected):
            checker.verify(body, forged)


class InadmissibleTasks(unittest.TestCase):
    def test_float_moments_are_refused(self):
        body = task(["0.5"])
        body["moments"] = [0.5]
        with self.assertRaises(producer.TaskError):
            producer.decide(body)

    def test_moment_outside_unit_interval(self):
        with self.assertRaises(producer.TaskError):
            producer.decide(task(["1.5"]))

    def test_moment_count_mismatch(self):
        body = task(["0.5", "0.2"])
        body["channel_count"] = 3
        with self.assertRaises(producer.TaskError):
            producer.decide(body)

    def test_negative_rounding_width(self):
        with self.assertRaises(producer.TaskError):
            producer.decide(task(["0.5"], half="-0.1"))

    def test_unknown_schema(self):
        body = task(["0.5"])
        body["schema_id"] = "something.else"
        with self.assertRaises(producer.TaskError):
            producer.decide(body)

    def test_inadmissible_grid(self):
        with self.assertRaises(producer.TaskError):
            producer.decide(task(["0.5"], coarse_denominator=1, fine_denominator=1))


class UnresolvedIsNeverFavourable(unittest.TestCase):
    def test_off_grid_boundary_vector_returns_unresolved_not_infeasible(self):
        """A grid that cannot represent a feasible vector must not refute it.

        At m2 = m1^2 the Cauchy-Schwarz equality forces a single atom at m1, so
        the only representing measure is the point mass at 123/1000, which is on
        no grid used here. The procedure must say unresolved. Reporting
        infeasibility from a grid failure is the error this design exists to
        prevent, and is the defect in the predecessor's grid-refinement argument.
        """
        body = task(["0.123", "0.015129"])
        report = producer.decide(body)
        self.assertEqual(report["verdict"], "unresolved")
        self.assertIsNone(report["certificate"])
        checker.verify(body, report)

    def test_rounding_a_feasible_vector_can_make_it_infeasible(self):
        """Retained failure: my own first fixture was wrong, and it matters.

        m1 = 1/7, m2 = 1/49 is feasible by a point mass. Printed to six decimals
        it becomes 0.142857, 0.020408, which falls below m1^2 by 1.2e-07 and is
        genuinely infeasible. Any refutation computed from rounded moments must
        therefore be shown to hold across the whole rounding box before it can be
        read as a statement about the population.
        """
        exact_pair = task(["0.142857142857142857", "0.020408163265306122"])
        rounded = task(["0.142857", "0.020408"])
        rounded_report = producer.decide(rounded)
        self.assertTrue(rounded_report["verdict"].startswith("infeasible"))
        checker.verify(rounded, rounded_report)
        widened = task(["0.142857", "0.020408"], half="0.0000005")
        widened_report = producer.decide(widened)
        self.assertNotEqual(widened_report["verdict"], "infeasible_over_box")
        self.assertGreater(len(exact_pair["moments"]), 0)

    def test_box_straddling_the_boundary_is_reported_as_such(self):
        """A point mass vector has no room around it; the box state must say so."""
        body = task(["0.25", "0.0625"], half="0.0001")
        report = producer.decide(body)
        self.assertEqual(report["verdict"], "feasible_at_centre")
        self.assertEqual(report.get("box_state"), "contains_infeasible_corner")
        checker.verify(body, report)


class DisclosureSufficiency(unittest.TestCase):
    """The silence histogram does not determine a labelled channel decision.

    Two populations on three channels with identical marginals, identical S
    histograms and identical subset-averaged moments differ maximally in what
    adding channel 3 to channel 1 is worth. Any portable report claiming to
    answer that question must therefore carry more than the histogram.
    """

    A = {(1, 0, 0): Fraction(1, 2), (0, 1, 1): Fraction(1, 2)}
    B = {(0, 1, 0): Fraction(1, 2), (1, 0, 1): Fraction(1, 2)}

    @staticmethod
    def summary(population):
        from itertools import combinations
        marginals = tuple(sum(w for row, w in population.items() if row[j]) for j in range(3))
        histogram = {}
        for row, weight in population.items():
            histogram[sum(row)] = histogram.get(sum(row), 0) + weight
        subset = []
        for size in range(4):
            groups = list(combinations(range(3), size))
            subset.append(sum((sum((w for row, w in population.items()
                                     if all(row[j] for j in group)), Fraction(0)))
                              for group in groups) / Fraction(len(groups)))
        return marginals, tuple(sorted(histogram.items())), tuple(subset)

    def test_summaries_agree_but_the_decision_differs(self):
        self.assertEqual(self.summary(self.A), self.summary(self.B))
        pair_a = sum(w for row, w in self.A.items() if row[0] and row[2])
        pair_b = sum(w for row, w in self.B.items() if row[0] and row[2])
        self.assertEqual(pair_a, Fraction(0))
        self.assertEqual(pair_b, Fraction(1, 2))
        self.assertNotEqual(pair_a, pair_b)

    def test_moment_procedure_cannot_distinguish_them(self):
        """Both populations present the identical task, so the same verdict is correct."""
        moments = [_dec(value) for value in self.summary(self.A)[2][1:]]
        body_a, report_a = run(moments)
        body_b, report_b = run(moments)
        self.assertEqual(report_a["verdict"], report_b["verdict"])
        checker.verify(body_a, report_a)


class CornerCoverage(unittest.TestCase):
    """The whole-box feasibility path, attacked directly.

    Version 0.1.0 of the checker confirmed that every supplied corner was a
    corner and that the count was right. A report that padded each corner with an
    extra unconstrained coordinate defeated its duplicate test and presented two
    copies of one corner as both, concealing a corner whose variance is negative.
    The retained input is
    evidence/moment-cone/retained-failures/corner-forgery-accepted-by-b0c33d9.json.
    These tests fix the repaired invariant: the supplied corner set must equal the
    declared corner set exactly, and each corner must carry its own measure.
    """

    TASK = {"schema_id": "reiyah.moment-cone.task", "channel_count": 2,
            "moments": ["0.5", "0.25"], "rounding_half_width": ["0", "0.01"]}
    UPPER = {"moments": ["1", "1/2", "13/50"],
             "support": [["2/5", "1/2"], ["3/5", "1/2"]]}

    def report(self, corners, **overrides):
        body = {"moments": self.TASK["moments"], "rounding_half_width": ["0", "1/100"],
                "verdict": "feasible_over_box",
                "measure": {"centre": [["1/2", "1"]], "corners": corners}}
        body.update(overrides)
        return body

    def reject(self, report, fragment, task=None):
        with self.assertRaises(checker.Rejected) as caught:
            checker.verify(task or self.TASK, report)
        self.assertIn(fragment, str(caught.exception))

    def test_the_lower_corner_really_is_impossible(self):
        """The premise of the whole attack: variance at the low corner is negative."""
        self.assertEqual(Fraction("0.24") - Fraction("0.5") ** 2, Fraction(-1, 100))

    def test_retained_forgery_is_rejected(self):
        padded_a = {"moments": ["1", "1/2", "13/50", "7/50"],
                    "support": [["2/5", "1/2"], ["3/5", "1/2"]]}
        padded_b = {"moments": ["1", "1/2", "13/50", "169/1250"],
                    "support": [["0", "1/26"], ["13/25", "25/26"]]}
        self.reject(self.report([padded_a, padded_b]), "exactly 3 moments")

    def test_duplicate_declared_corner_is_rejected(self):
        self.reject(self.report([dict(self.UPPER), dict(self.UPPER)]), "more than once")

    def test_corner_outside_the_declared_box_is_rejected(self):
        stray = {"moments": ["1", "1/2", "1/4"], "support": [["1/2", "1"]]}
        self.reject(self.report([dict(self.UPPER), stray]), "not a corner of the declared box")

    def test_omitted_corner_is_rejected(self):
        self.reject(self.report([dict(self.UPPER)]), "expected 2 declared corners")

    def test_extra_corner_is_rejected(self):
        self.reject(self.report([dict(self.UPPER)] * 3), "expected 2 declared corners")

    def test_the_impossible_corner_cannot_be_satisfied(self):
        """Coverage plus per-corner verification is what actually protects here."""
        low = {"moments": ["1", "1/2", "6/25"], "support": [["1/2", "1"]]}
        self.reject(self.report([dict(self.UPPER), low]), "corner measure moment 2")

    def test_corner_order_does_not_matter(self):
        """An honest report is accepted whichever order it lists the corners in."""
        low_moments = ["1", "1/2", "6/25"]
        with self.assertRaises(checker.Rejected):
            checker.verify(self.TASK, self.report([dict(self.UPPER),
                                                   {"moments": low_moments,
                                                    "support": [["1/2", "1"]]}]))
        body, report = run(["0.3", "0.2"], half="0.0001")
        self.assertEqual(report["verdict"], "feasible_over_box")
        checker.verify(body, report)
        shuffled = copy.deepcopy(report)
        shuffled["measure"]["corners"].reverse()
        checker.verify(body, shuffled)

    def test_report_may_not_narrow_its_own_box(self):
        self.reject(self.report([dict(self.UPPER)] * 2, rounding_half_width=["0", "0"]),
                    "rounding box does not equal")

    def test_zero_width_box_cannot_carry_a_whole_box_verdict(self):
        task = dict(self.TASK)
        task["rounding_half_width"] = ["0", "0"]
        body = self.report([dict(self.UPPER)], rounding_half_width=["0", "0"])
        self.reject(body, "zero-width box", task=task)

    def test_degenerate_coordinate_halves_the_corner_count(self):
        moments = [Fraction(1), Fraction("0.5"), Fraction("0.25")]
        self.assertEqual(len(checker.declared_corners(moments, [Fraction(0), Fraction("0.01")])), 2)
        self.assertEqual(len(checker.declared_corners(moments, [Fraction("0.01"), Fraction("0.01")])), 4)
        self.assertEqual(len(checker.declared_corners(moments, [Fraction(0), Fraction(0)])), 1)


class ParserAndFieldDiscipline(unittest.TestCase):
    def setUp(self):
        self.body, self.report = run(["0.25", "0.0625", "0.015625"])
        self.assertTrue(self.report["verdict"].startswith("feasible"))

    def reject(self, task, report, fragment):
        with self.assertRaises(checker.Rejected) as caught:
            checker.verify(task, report)
        self.assertIn(fragment, str(caught.exception))

    def test_duplicate_json_keys_are_refused(self):
        import tempfile, os
        handle, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(handle, "w") as stream:
            stream.write('{"verdict": "unresolved", "verdict": "feasible_over_box"}')
        try:
            with self.assertRaises(checker.Rejected):
                checker.load(path)
        finally:
            os.unlink(path)

    def test_unknown_task_field(self):
        task = copy.deepcopy(self.body)
        task["extra"] = 1
        self.reject(task, self.report, "task carries unknown fields")

    def test_unknown_certificate_field(self):
        body, report = run(["0.5", "0.2"])
        report["certificate"]["hint"] = "trust me"
        self.reject(body, report, "certificate carries unknown fields")

    def test_zero_denominator_is_refused(self):
        forged = copy.deepcopy(self.report)
        forged["measure"]["centre"] = [["1/0", "1"]]
        self.reject(self.body, forged, "not in the declared form")

    def test_oversized_numeric_string_is_refused(self):
        forged = copy.deepcopy(self.report)
        forged["measure"]["centre"] = [["1/" + "9" * 5000, "1"]]
        self.reject(self.body, forged, "exceeds")

    def test_float_in_a_report_is_refused(self):
        forged = copy.deepcopy(self.report)
        forged["measure"]["centre"] = [[0.25, 1.0]]
        self.reject(self.body, forged, "not a string")

    def test_boolean_channel_count_is_refused(self):
        task = copy.deepcopy(self.body)
        task["channel_count"] = True
        self.reject(task, self.report, "channel_count is not an integer in range")

    def test_zero_weight_atoms_are_permitted(self):
        allowed = copy.deepcopy(self.report)
        allowed["measure"]["centre"] = allowed["measure"]["centre"] + [["1", "0"]]
        checker.verify(self.body, allowed)

    def test_centre_only_verdict_claims_no_corners(self):
        outcome = checker.verify(self.body, self.report)
        self.assertEqual(outcome["checked"]["corners_checked"], 0)

    def test_task_moment_count_must_match_channel_count(self):
        task = copy.deepcopy(self.body)
        task["channel_count"] = 2
        self.reject(task, self.report, "list of channel_count entries")


class RetainedRealCertificatesStillPass(unittest.TestCase):
    """The three real-summary certificates, rerun through the repaired checker."""

    CASES = {
        "all-annotated-objects": (["0.207356", "0.102807", "0.069423", "0.055554", "0.047427"],
                                  "infeasible_over_box"),
        "four-channel-robustness": (["0.215738", "0.109442", "0.072654", "0.060246"],
                                    "infeasible_over_box"),
        "most-observable": (["0.043834", "0.010316", "0.004383", "0.002826", "0.002196"],
                            "feasible_over_box"),
    }

    def test_all_three(self):
        for name, (moments, expected) in self.CASES.items():
            body, report = run(moments, half="0.0000005")
            self.assertEqual(report["verdict"], expected, name)
            outcome = checker.verify(body, report)
            self.assertEqual(outcome["verdict"], expected, name)
            if expected == "feasible_over_box":
                self.assertEqual(outcome["checked"]["corners_checked"],
                                 outcome["checked"]["corners_declared"], name)


class ExactSilenceHistogram(unittest.TestCase):
    """The exact input form, which removes the rounding box entirely.

    Where the integer silence counts are known, the subset-averaged moments are
    exact rationals and no rounding argument is needed. These are the strongest
    certificates in the lane and the ones a reader should check first.
    """

    HISTOGRAMS = {
        "all annotated objects": ([70970, 25485, 18533, 7727, 5468, 6382], "infeasible_exact"),
        "four channels": ([75804, 24292, 19683, 6679, 8107], "infeasible_exact"),
        "most observable": ([21344, 2475, 864, 232, 79, 55], "feasible_exact"),
        "radar returns at least 3": ([14881, 3526, 1950, 725, 458, 350], "feasible_exact"),
        "range 0-20 m": ([38411, 8225, 4199, 1629, 1047, 1113], "feasible_exact"),
        "range 20-30 m": ([19597, 7705, 5496, 2331, 1391, 1723], "feasible_exact"),
        "range 30-40 m": ([9092, 6128, 5462, 2120, 1628, 1956], "infeasible_exact"),
        "range 40-50 m": ([3870, 3427, 3376, 1647, 1402, 1590], "infeasible_exact"),
    }
    # Every verdict the redundancy-scaling lane reached by grid refinement, for
    # comparison. This lane reaches them by exact certificate and they all agree.
    GRID_VERDICT = {
        "all annotated objects": "REFUTED", "most observable": "not refuted",
        "radar returns at least 3": "not refuted", "range 0-20 m": "not refuted",
        "range 20-30 m": "not refuted", "range 30-40 m": "REFUTED",
        "range 40-50 m": "REFUTED",
    }
    PRINTED = {
        "all annotated objects": ["0.207356", "0.102807", "0.069423", "0.055554", "0.047427"],
        "four channels": ["0.215738", "0.109442", "0.072654", "0.060246"],
        "most observable": ["0.043834", "0.010316", "0.004383", "0.002826", "0.002196"],
    }
    # Published row counts, which the histograms must reproduce.
    OPPORTUNITIES = {
        "all annotated objects": 134565, "four channels": 134565, "most observable": 25049,
        "radar returns at least 3": 21890, "range 0-20 m": 54624, "range 20-30 m": 38243,
        "range 30-40 m": 26386, "range 40-50 m": 15312,
    }

    def task(self, counts):
        return {"schema_id": "reiyah.moment-cone.task",
                "channel_count": len(counts) - 1,
                "silence_histogram": list(counts)}

    def test_each_population_decides_exactly(self):
        for name, (counts, expected) in self.HISTOGRAMS.items():
            body = self.task(counts)
            report = producer.decide(body)
            self.assertEqual(report["verdict"], expected, name)
            self.assertEqual(report["rounding_half_width"], ["0"] * (len(counts) - 1), name)
            outcome = checker.verify(body, report)
            self.assertEqual(outcome["verdict"], expected, name)

    def test_every_histogram_sums_to_its_published_row_count(self):
        for name, (counts, _) in self.HISTOGRAMS.items():
            self.assertEqual(sum(counts), self.OPPORTUNITIES[name], name)

    def test_exact_verdicts_agree_with_the_grid_verdicts(self):
        """Two independent methods, seven populations, no disagreement."""
        for name, expected in self.GRID_VERDICT.items():
            counts, verdict = self.HISTOGRAMS[name]
            report = producer.decide(self.task(counts))
            reached = "REFUTED" if report["verdict"] == "infeasible_exact" else "not refuted"
            self.assertEqual(reached, expected, name)
            self.assertEqual(report["verdict"], verdict, name)

    def test_exact_moments_round_to_the_published_decimals(self):
        """The histograms are the ones the published summaries determine."""
        for name, (counts, _) in self.HISTOGRAMS.items():
            if name not in self.PRINTED:
                continue
            channels = len(counts) - 1
            moments, total = producer.moments_from_histogram(counts, channels)
            self.assertEqual(total, sum(counts))
            for index, printed in enumerate(self.PRINTED[name]):
                self.assertLessEqual(abs(moments[index + 1] - Fraction(printed)),
                                     Fraction(1, 2000000), f"{name} moment {index + 1}")

    def test_histogram_and_moments_together_are_refused(self):
        body = self.task([1, 1, 1])
        body["moments"] = ["0.5", "0.25"]
        with self.assertRaises(producer.TaskError):
            producer.decide(body)

    def test_histogram_with_a_rounding_box_is_refused(self):
        body = self.task([1, 1, 1])
        body["rounding_half_width"] = "0.001"
        with self.assertRaises(producer.TaskError):
            producer.decide(body)

    def test_non_integer_and_negative_counts_are_refused(self):
        for bad in ([1, 1, "2"], [1, -1, 2], [1, True, 2], [0, 0, 0]):
            with self.assertRaises(producer.TaskError):
                producer.decide(self.task(bad))

    def test_wrong_histogram_length_is_refused(self):
        body = {"schema_id": "reiyah.moment-cone.task", "channel_count": 5,
                "silence_histogram": [1, 2, 3]}
        with self.assertRaises(producer.TaskError):
            producer.decide(body)

    def test_exact_verdict_requires_an_exact_task(self):
        body, report = run(["0.207356", "0.102807", "0.069423", "0.055554", "0.047427"],
                           half="0.0000005")
        forged = copy.deepcopy(report)
        forged["verdict"] = "infeasible_exact"
        with self.assertRaises(checker.Rejected):
            checker.verify(body, forged)

    def test_box_verdict_is_refused_for_an_exact_task(self):
        body = self.task(self.HISTOGRAMS["all annotated objects"][0])
        report = producer.decide(body)
        forged = copy.deepcopy(report)
        forged["verdict"] = "infeasible_over_box"
        with self.assertRaises(checker.Rejected):
            checker.verify(body, forged)

    def test_report_may_not_restate_a_different_histogram(self):
        body = self.task(self.HISTOGRAMS["all annotated objects"][0])
        report = producer.decide(body)
        forged = copy.deepcopy(report)
        forged["silence_histogram"] = [70971, 25485, 18533, 7727, 5468, 6381]
        with self.assertRaises(checker.Rejected):
            checker.verify(body, forged)

    def test_report_moments_must_be_the_histogram_moments(self):
        body = self.task(self.HISTOGRAMS["all annotated objects"][0])
        report = producer.decide(body)
        forged = copy.deepcopy(report)
        forged["moments"][0] = "1/2"
        with self.assertRaises(checker.Rejected):
            checker.verify(body, forged)

    def test_a_histogram_with_no_silence_anywhere_is_feasible(self):
        """Everything easy for every channel: the point mass at zero."""
        body = self.task([100, 0, 0])
        report = producer.decide(body)
        self.assertEqual(report["verdict"], "feasible_exact")
        checker.verify(body, report)


class WhatTheDiagnosticDistinguishes(unittest.TestCase):
    """The controls that bound how a moment-cone verdict may be read.

    A rejection is caused by spread in the channel rates, not by coupling, and
    perfect coupling is accepted. Anyone quoting a rejection as evidence that
    channels fail together is reading it backwards.
    """

    import moment_cone_discrimination as D

    def test_variance_identity_holds_for_random_rate_vectors(self):
        import random
        random.seed(20260910)
        for _ in range(200):
            k = random.randint(2, 6)
            rates = [Fraction(random.randint(1, 999), 1000) for _ in range(k)]
            moments = self.D.independent_moments(rates)
            self.assertEqual(moments[2] - moments[1] ** 2,
                             -self.D.variance(rates) / (k - 1))

    def test_general_decomposition_holds_for_arbitrary_joint_laws(self):
        """m2 - m1^2 = meanCov - Var(p)/(K-1), the correction of 11 September 2026.

        The earlier claim that heterogeneity alone forces the violation held only
        under independence. Positive dependence can offset the penalty.
        """
        import random
        from itertools import combinations, product
        random.seed(20260911)
        checked = 0
        for _ in range(500):
            k = random.randint(2, 4)
            cells = list(product((0, 1), repeat=k))
            weights = [Fraction(random.randint(0, 9), 9) for _ in cells]
            total = sum(weights, Fraction(0))
            if total == 0:
                continue
            law = {c: w / total for c, w in zip(cells, weights) if w > 0}
            rates = [sum((w for x, w in law.items() if x[i]), Fraction(0)) for i in range(k)]
            m1 = sum(rates, Fraction(0)) / k
            pairs = list(combinations(range(k), 2))
            m2 = sum((sum((w for x, w in law.items() if x[i] and x[j]), Fraction(0))
                      for i, j in pairs), Fraction(0)) / len(pairs)
            cov = sum((sum((w for x, w in law.items() if x[i] and x[j]), Fraction(0))
                       - rates[i] * rates[j] for i, j in pairs), Fraction(0)) / len(pairs)
            self.assertEqual(m2 - m1 ** 2, cov - self.D.variance(rates) / (k - 1))
            checked += 1
        self.assertGreater(checked, 400)

    def test_a_heterogeneous_dependent_law_can_satisfy_the_condition(self):
        """So cone membership isolates neither coupling nor heterogeneity."""
        law = {(1, 1, 1): Fraction(1, 4), (0, 0, 0): Fraction(1, 2),
               (1, 0, 0): Fraction(1, 8), (1, 1, 0): Fraction(1, 8)}
        cov, rates = self.D.mean_pair_covariance(law, 3)
        self.assertNotEqual(self.D.variance(rates), Fraction(0))
        self.assertGreater(cov, Fraction(0))
        m1 = sum(rates, Fraction(0)) / 3
        from itertools import combinations
        pairs = list(combinations(range(3), 2))
        m2 = sum((sum((w for x, w in law.items() if x[i] and x[j]), Fraction(0))
                  for i, j in pairs), Fraction(0)) / len(pairs)
        self.assertGreaterEqual(m2 - m1 ** 2, Fraction(0))

    def test_equal_rates_sit_exactly_on_the_boundary(self):
        rates = [Fraction(3, 7)] * 4
        moments = self.D.independent_moments(rates)
        self.assertEqual(moments[2] - moments[1] ** 2, Fraction(0))
        self.assertEqual(self.D.variance(rates), Fraction(0))

    def test_the_measured_rates_reject_under_pure_independence(self):
        rates = list(self.D.MEASURED_RATES.values())
        moments = self.D.independent_moments(rates)
        witness = self.D.decide(moments, len(rates))
        self.assertIsNotNone(witness, "independence at the measured rates should reject")
        self.assertLess(Fraction(witness["functional"]), 0)

    def test_perfect_coupling_is_accepted(self):
        for p in (Fraction(1, 10), Fraction(1, 2), Fraction(9, 10)):
            moments = [Fraction(1)] + [p] * 5
            self.assertIsNone(self.D.decide(moments, 5), f"p={p}")
            body = {"schema_id": "reiyah.moment-cone.task", "channel_count": 5,
                    "moments": [str(float(p))] * 5, **SMALL_GRID}
            report = producer.decide(body)
            self.assertTrue(report["verdict"].startswith("feasible"), f"p={p}")
            checker.verify(body, report)

    def test_the_coordinator_worked_example(self):
        moments = self.D.independent_moments([Fraction(1, 4), Fraction(3, 4)])
        self.assertEqual(moments[1], Fraction(1, 2))
        self.assertEqual(moments[2], Fraction(3, 16))
        square = [Fraction(1, 4), Fraction(-1), Fraction(1)]
        self.assertEqual(sum(c * moments[k] for k, c in enumerate(square)), Fraction(-1, 16))


class NextChannelBenefit(unittest.TestCase):
    """The restricted miss-only query, and what the histogram cannot answer."""

    def test_benefit_identity_on_explicit_cells(self):
        import next_channel_decision as N
        counts = {(True, True, False): 3, (True, True, True): 2,
                  (False, True, True): 5, (False, False, False): 10}
        total = sum(counts.values())
        base = N.all_silent(counts, (0, 1), total)
        joint = N.all_silent(counts, (0, 1, 2), total)
        self.assertEqual(base, Fraction(5, 20))
        self.assertEqual(joint, Fraction(2, 20))
        self.assertEqual(base - joint, Fraction(3, 20))

    def test_the_histogram_cannot_answer_it(self):
        """The retained counterexample, restated as the decision it breaks."""
        A = {(1, 0, 0): Fraction(1, 2), (0, 1, 1): Fraction(1, 2)}
        B = {(0, 1, 0): Fraction(1, 2), (1, 0, 1): Fraction(1, 2)}
        for population, expected in ((A, Fraction(1, 2)), (B, Fraction(0))):
            base = sum((w for row, w in population.items() if row[0]), Fraction(0))
            joint = sum((w for row, w in population.items() if row[0] and row[2]), Fraction(0))
            self.assertEqual(base - joint, expected)


def _dec(value):
    """Exact decimal string for a rational with a terminating expansion, else nearest."""
    from decimal import Decimal, getcontext
    getcontext().prec = 40
    return str(Decimal(value.numerator) / Decimal(value.denominator))


if __name__ == "__main__":
    unittest.main()
