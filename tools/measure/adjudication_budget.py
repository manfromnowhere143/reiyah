"""What closing an open-reference comparison costs, in human judgements.

An open reference returns the bound of ignorance. The contract's decision rules
resolve it as soon as the gain is pinned on one side of a threshold, and that
threshold is available in closed form before any review begins.

For one anchor with r retained additions, nonnegative penalties a and b, and
tolerance t, the reported difference is `(a+b)*g - b*r` for a gain g in [0, r], so

    improvement supported   iff   g  >  tau,      tau = (t + b*r) / (a + b)
    improvement excluded    iff   g  <= tau

Review therefore does not have to determine g. It only has to place g on one side
of tau, which is a sequential threshold test: stop at `ceil(tau + 1)` confirmed
conversions, or at `r - floor(tau)` confirmed non-conversions. Either outcome ends
the review, and the worst case is strictly fewer than r whenever both stopping
counts exceed one.

The expected cost follows once a conversion prior is supplied, and this program
takes that prior from the lane's own measured conversion rate rather than a guess.

Declared model, stated because it is an approximation. A reviewer adjudicates
objects, not detections, and the gain is a maximum matching over the admitted
objects rather than a sum of independent per-addition outcomes. Two retained
additions can still compete for one object, because suppression separates an
addition from the base rather than from another addition. The sequential model
below treats each retained addition as one conversion trial; it is exact when no
two retained additions can match the same object and is an upper bound on the
number of judgements otherwise, since r additions cannot yield more than r gain.

Exact rational arithmetic. Standard library only. No data is read.
"""
from fractions import Fraction
import json
import sys


def threshold(r, a, b, tolerance):
    """The gain threshold tau, above which the improvement is supported."""
    return (tolerance + b * r) / (a + b)


def stopping_counts(r, tau):
    """Confirmed conversions that end the review, and confirmed non-conversions."""
    successes = 0
    while Fraction(successes) <= tau:
        successes += 1
        if successes > r:
            break
    failures = r - int(tau) if tau >= 0 else r
    while r - failures > tau:
        failures += 1
        if failures > r:
            break
    return min(successes, r), min(max(failures, 0), r)


def expected_trials(need_success, need_failure, p):
    """Exact expected trials of a race to `need_success` heads or `need_failure` tails."""
    if need_success <= 0 or need_failure <= 0:
        return Fraction(0)
    memo = {}

    def walk(s, f):
        if s >= need_success or f >= need_failure:
            return Fraction(0)
        key = (s, f)
        if key not in memo:
            memo[key] = 1 + p * walk(s + 1, f) + (1 - p) * walk(s, f + 1)
        return memo[key]

    return walk(0, 0)


def probability_supported(need_success, need_failure, p):
    """Exact probability the race ends in the supported branch."""
    memo = {}

    def walk(s, f):
        if s >= need_success:
            return Fraction(1)
        if f >= need_failure:
            return Fraction(0)
        key = (s, f)
        if key not in memo:
            memo[key] = p * walk(s + 1, f) + (1 - p) * walk(s, f + 1)
        return memo[key]

    return walk(0, 0)


def main(argv):
    a = b = Fraction(1)
    tolerance = Fraction(1, 10)
    # Retained additions per anchor of the open comparison. Structural parameters only.
    anchors = [int(x) for x in argv[1:]] or [9, 7]
    # The lane's measured conversion rate on the full split at the same floor.
    # Corrected 11 September 2026: the earlier 66/223 came from a measurement whose
    # code applied one score floor to base and addition together, omitted keyframes
    # with no reference object and did not range filter predictions. See
    # docs/CONVERSION_CORRECTION_2026-09-11.md.
    prior = Fraction("9878/31047")

    report = {"artifact_id": "reiyah.decision-evidence.adjudication-budget", "version": "0.1.0",
              "loss": {"false_negative": str(a), "false_positive": str(b),
                       "tolerance": str(tolerance)},
              "conversion_prior": {"value": str(prior), "decimal": round(float(prior), 6),
                                   "source": "this lane's corrected full-split measurement at the 0.30 floor, base held fixed",
                                   "status": "a prior, not a property of these anchors"},
              "anchors": []}
    total_worst = 0
    total_expected = Fraction(0)
    for r in anchors:
        tau = threshold(r, a, b, tolerance)
        need_s, need_f = stopping_counts(r, tau)
        worst = need_s + need_f - 1
        expected = expected_trials(need_s, need_f, prior)
        supported = probability_supported(need_s, need_f, prior)
        total_worst += min(worst, r)
        total_expected += expected
        report["anchors"].append({
            "retained_additions": r,
            "gain_threshold_tau": str(tau),
            "supported_needs_conversions": need_s,
            "excluded_needs_non_conversions": need_f,
            "worst_case_judgements": min(worst, r),
            "expected_judgements_at_prior": str(expected),
            "expected_decimal": round(float(expected), 3),
            "probability_supported_at_prior": str(supported),
            "probability_decimal": round(float(supported), 6)})
    report["totals"] = {
        "judgements_if_every_addition_is_adjudicated": sum(anchors),
        "worst_case_with_stopping": total_worst,
        "expected_with_stopping_at_prior": str(total_expected),
        "expected_decimal": round(float(total_expected), 3),
        "saving_against_full_adjudication": round(
            float(Fraction(sum(anchors)) - total_expected), 3)}
    report["prior_sensitivity"] = []
    for text in ("1/10", "9878/31047", "1/2", "3/4"):
        p = Fraction(text)
        rows = []
        for r in anchors:
            tau = threshold(r, a, b, tolerance)
            need_s, need_f = stopping_counts(r, tau)
            rows.append((expected_trials(need_s, need_f, p),
                         probability_supported(need_s, need_f, p)))
        report["prior_sensitivity"].append({
            "conversion_prior": text,
            "expected_total_judgements": round(float(sum(e for e, _s in rows)), 3),
            "probability_supported_each": [round(float(s), 6) for _e, s in rows]})
    report["reading"] = (
        "review does not have to measure the gain. It has to place the gain on one side of tau, "
        "which ends as soon as either stopping count is reached. The budget is therefore bounded "
        "before any judgement is made, and its expected size follows from a measured conversion rate")
    report["non_claims"] = (
        "a declared sequential model over retained additions, not a reviewer protocol, not a "
        "physical reference, and not a claim that any person is available. The prior is measured on "
        "a different population and is falsifiable by the review it budgets")
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
