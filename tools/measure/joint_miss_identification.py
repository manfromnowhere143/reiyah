"""What the coefficient c can and cannot be, when the objects that define it are missing.

The dependence estimand of this programme is

    c = P(both channels miss) / ( P(A misses) * P(B misses) )

which `docs/ESTIMAND_RSS_DEFINITION_32.md` binds to the smallest admissible
constant in Definition 32 of the retained primary source. Everything below is an
identification question about that quantity. It estimates nothing, uses no data,
and makes no claim about any real channel pair.

Two channels sort a population of objects into four cells by which of them
detected the object:

    n11  both detected        n10  A only        n01  B only        m  neither

The first three are observable. The fourth is not: an object no channel reported
leaves no trace in any channel's output. It is the joint silent miss, and it is
the numerator of the estimand. Writing `S = n11 + n10 + n01` and `N = S + m`,

    c(m) = m * N / ( (n01 + m) * (n10 + m) )

With `K` channels the same structure holds with more observable cells. For a
declared pair `(A, B)`, write `S` for all observed objects, `a` and `b` for those
`A` and `B` respectively miss, `w` for those both detect, and `u` for those BOTH
miss that some other channel caught. `u` is zero when there are only two channels,
and positive as soon as a third channel sees something they both missed. Then

    c(m) = (u + m) * (S + m) / ( (a + m) * (b + m) )

which reduces to the two channel formula when `u = 0` and `a`, `b` count the
single opposite cells.

Four results follow, in exact rational arithmetic, and the last is the one that
changes what the programme should build.

ONE: c IS NOT IDENTIFIED BY TWO CHANNELS. As `m` runs over the non negative
integers, `c(m)` rises from `0`, reaches an interior maximum above `1`, and falls
back towards `1` from above. So a wide band of values, including every value
between `0` and that maximum, is consistent with exactly the same observed
counts. No amount of care with `n11`, `n10` and `n01` narrows it. Two channels
alone cannot answer the question this programme exists to ask.

TWO: THE STANDARD REPAIR ASSUMES THE ANSWER. Filling the missing cell by the
Lincoln and Petersen capture recapture estimate, `m = n01 * n10 / n11`, gives
`c = 1` exactly, for every `n11`, `n10`, `n01`. That is not an approximation and
not a coincidence: the capture recapture estimator is derived by assuming the two
channels are independent, which is the statement `c = 1`. Any pipeline that fills
the joint silent miss cell that way and then reports `c` has reported its own
assumption. The identity is asserted as a test rather than described.

THREE: THE SIGN QUESTION REDUCES EXACTLY. From the algebra,

    c(m) > 1   if and only if   m * w > a * b - u * S

so asking whether the channels are positively coupled is exactly asking whether
the unobservable count exceeds `(a * b - u * S) / w`. With two channels `u = 0`
and this is `m > n01 * n10 / n11`, the capture recapture figure again. Nothing
more about the reference is needed to settle the sign, and nothing less will do.
A reference programme that bounds the dark figure to an interval decides the sign
if and only if that interval falls entirely on one side of that threshold.

FOUR: A THIRD CHANNEL CAN SETTLE THE SIGN WITH NO REFERENCE AT ALL. If

    a * b  <=  u * S

the threshold is at or below zero, so `c > 1` for EVERY admissible unobservable
count, and the conclusion holds without annotating anything. This cannot happen
with two channels, where `u = 0` forces the threshold positive. It becomes
possible as soon as a third channel observes objects that the pair both missed,
because those objects are direct evidence about the very cell that was
unobservable. Verified on random tables and retained as a worked case.

The practical reading is that the joint silent miss question has two routes, not
one. Bounding the dark figure by reference annotation is the hard route. Adding
an independent channel that sees some of what the pair misses is the other, and
for the sign question it can be sufficient on its own.

A TRAP WORTH NAMING. `c` is NOT monotone in `m`. Bounding `m` to an interval and
evaluating `c` at the two endpoints does not give the range of `c`, because the
maximum is usually interior. The range is computed here by locating the exact
stationary point and testing the integers around it, never by reading endpoints.

HOW THE RANGE IS FOUND. `c` is a ratio of two quadratics in `m`, so the numerator
of `c'(m)` is itself a quadratic,

    -w * m^2 + 2 (ab - uS) m + ( (u+S) ab - uS (a+b) )

and `c` therefore has at most two interior extrema. The range over an interval is
computed by testing the two endpoints and the integers bracketing each real root
of that quadratic, located with exact integer square roots so the bracketing is
proved rather than estimated. No monotonicity is assumed anywhere.

In the two channel case the quadratic reduces to `-n11 m^2 + 2 Q m + S Q` with
`Q = n01 * n10`, which is downward with a non negative value at `m = 0`, so it has
exactly one non negative root and `c` is unimodal: strictly increasing then
strictly decreasing. That is asserted as a test for the two channel case, and it
is a consequence rather than an assumption of the search.

Exact rational arithmetic, standard library only, no data read, no estimate made.
"""
from fractions import Fraction
from itertools import product
import json
import math
import os
import sys

VERSION = "0.3.0"


class CountError(Exception):
    """The declared counts do not describe a population this analysis applies to."""


def _nonneg(name, value):
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise CountError(f"{name} must be a non negative integer, not {value!r}")
    return value


def _bound(name, value, allow_none=False):
    """The declared bounds are counts too, and obey the same discipline.

    Version 0.2.0 checked only `value < 0` here, so a boolean passed as an
    integer and was reported back as the count at which an extreme was attained.
    """
    if value is None and allow_none:
        return None
    return _nonneg(name, value)


def _defined_at(parts, m):
    """c is undefined only where a channel misses nothing, which needs m = 0."""
    return (parts["a"] + m) * (parts["b"] + m) != 0


def margins(counts, pair=(0, 1)):
    """S, u, a, b, w for a declared channel pair, from observed pattern counts.

    `counts` maps a detection pattern, a tuple of 0/1 per channel, to the number
    of objects with that pattern. The all zero pattern is the unobservable cell
    and must not appear: it is the quantity this module refuses to invent.
    """
    if not counts:
        raise CountError("no observed pattern counts were declared")
    width = {len(pattern) for pattern in counts}
    if len(width) != 1:
        raise CountError("the declared patterns do not all name the same channels")
    channels = width.pop()
    first, second = pair
    if not 0 <= first < channels or not 0 <= second < channels or first == second:
        raise CountError(f"the declared pair {pair} does not name two distinct channels")
    for pattern, value in counts.items():
        if any(bit not in (0, 1) for bit in pattern):
            raise CountError(f"pattern {pattern} is not a tuple of detection bits")
        _nonneg(f"count for {pattern}", value)
        if not any(pattern):
            raise CountError(
                "the all zero pattern is the unobservable cell and cannot be declared as "
                "observed. It is the quantity under analysis, not an input")
    total = sum(counts.values())
    return {
        "channels": channels,
        "S": total,
        "u": sum(v for k, v in counts.items() if not k[first] and not k[second]),
        "a": sum(v for k, v in counts.items() if not k[first]),
        "b": sum(v for k, v in counts.items() if not k[second]),
        "w": sum(v for k, v in counts.items() if k[first] and k[second]),
    }


def two_channel_counts(n11, n10, n01):
    """The two channel table as observed pattern counts."""
    for name, value in (("n11", n11), ("n10", n10), ("n01", n01)):
        _nonneg(name, value)
    return {(1, 1): n11, (1, 0): n10, (0, 1): n01}


def coefficient(parts, m):
    """c(m) from the margins, exactly. None where the ratio is undefined."""
    if not isinstance(m, (int, Fraction)) or m < 0:
        raise CountError(f"the joint silent miss count must be non negative, not {m!r}")
    denominator = (parts["a"] + m) * (parts["b"] + m)
    if denominator == 0:
        # A channel that misses nothing has a zero miss probability, and the ratio
        # has no value. Undefined, which is neither zero nor one.
        return None
    return Fraction((parts["u"] + m) * (parts["S"] + m), 1) / Fraction(denominator, 1)


def sign_threshold(parts):
    """c > 1 exactly when m exceeds this, when a threshold exists at all.

    The sign condition is `m * w > a * b - u * S`. Dividing by `w` is only
    available when `w > 0`; version 0.2.0 treated the absence of that division as
    the absence of a sign conclusion, which is a different thing. When `w = 0` the
    condition no longer involves `m` at all and the sign is settled outright, so
    `sign_over` is the complete classification and this returns None.
    """
    if parts["w"] == 0:
        return None
    return Fraction(parts["a"] * parts["b"] - parts["u"] * parts["S"], parts["w"])


def sign_over(parts, low=0, high=None):
    """The complete sign classification over the declared integer bound.

    Returns a state and the reason for it. Every branch is reachable and each is
    a different fact about the population, so none of them collapses into
    `undetermined`.
    """
    a, b, u, s, w = parts["a"], parts["b"], parts["u"], parts["S"], parts["w"]
    gap = a * b - u * s

    smallest = low if _defined_at(parts, low) else low + 1
    if high is not None and smallest > high:
        return ("undefined",
                "the coefficient is undefined at every count the declared bound allows, because a "
                "channel misses nothing there. An undefined ratio is not a sign")

    if w == 0:
        # The condition m * w > gap loses its dependence on m entirely.
        if gap < 0:
            return ("c_greater_than_1",
                    "no object was detected by both channels, and a * b is below u * S, so c "
                    "exceeds 1 at every admissible count")
        if gap == 0:
            return ("c_equals_1",
                    "no object was detected by both channels, and a * b equals u * S, so c is "
                    "exactly 1 at every admissible count. The coefficient is constant")
        return ("c_less_than_1",
                "no object was detected by both channels, and a * b is above u * S, so c is below "
                "1 at every admissible count")

    threshold = Fraction(gap, w)
    if Fraction(smallest) > threshold:
        return ("c_greater_than_1",
                f"every count the declared bound allows exceeds the threshold {threshold}, so c "
                "exceeds 1")
    if Fraction(smallest) == threshold:
        return ("c_at_least_1",
                f"the smallest count the declared bound allows sits exactly on the threshold "
                f"{threshold}, so c is at least 1 everywhere, reaching 1 only at that count. The "
                "published condition a * b <= u * S covered this case and claimed strict "
                "inequality, which it does not establish")
    if high is None:
        return ("undetermined",
                f"the declared bound is unbounded above and reaches past the threshold "
                f"{threshold}, so both a positively coupled and a not positively coupled "
                "population are consistent with these counts")
    if Fraction(high) <= threshold:
        if Fraction(high) == threshold and Fraction(smallest) == threshold:
            return ("c_equals_1",
                    f"the declared bound pins the count to the threshold {threshold}, where c is "
                    "exactly 1")
        if Fraction(high) < threshold:
            return ("c_less_than_1",
                    f"every count the declared bound allows is below the threshold {threshold}, "
                    "so c is below 1")
        return ("c_at_most_1",
                f"every count the declared bound allows is at or below the threshold {threshold}, "
                "so c is at most 1, reaching 1 at the threshold itself")
    return ("undetermined",
            f"the declared bound spans the threshold {threshold}, so both a positively coupled "
            "and a not positively coupled population are consistent with these counts")


def lincoln_petersen(parts):
    """The dark figure a capture recapture fill would supply, for two channels."""
    if parts["w"] == 0:
        return None
    return Fraction(parts["a"] * parts["b"], parts["w"])


def _stationary_candidates(parts):
    """Integers bracketing every real root of the derivative's quadratic.

    The bracketing uses exact integer square roots, so it is proved rather than
    estimated, and it assumes nothing about monotonicity.
    """
    u, s, a, b, w = parts["u"], parts["S"], parts["a"], parts["b"], parts["w"]
    linear = a * b - u * s
    constant = (u + s) * a * b - u * s * (a + b)
    found = set()
    if w == 0:
        if linear != 0:
            exact = Fraction(-constant, 2 * linear)
            found.update({math.floor(exact), math.ceil(exact)})
    else:
        discriminant = linear * linear + w * constant
        if discriminant >= 0:
            root = math.isqrt(discriminant)
            for sign in (1, -1):
                estimate = (linear + sign * root) // w
                found.update(range(estimate - 2, estimate + 3))
    return {value for value in found if value >= 0}


def _candidates(parts, low, high):
    points = {low, high}
    points.update(value for value in _stationary_candidates(parts) if low <= value <= high)
    return sorted(points)


def range_over(parts, low=0, high=None):
    """The exact range of c as m runs over the INTEGERS in [low, high].

    The identified set is discrete, because m counts objects. The interval
    reported is its enclosure, not a claim that every value inside is reachable.

    Version 0.2.0 handled an unbounded upper end by inventing a ceiling from the
    stationary points and reporting the extremes over that truncated window. Where
    no stationary point existed the window was two integers wide, and the reported
    lower value was simply not the smallest: on w=10, x=y=10, u=10 it named 21/11
    at m=1 while m=2 gives 11/6 and no minimum exists at all. The candidates are
    now the bound's own ends together with the stationary points inside it, which
    is complete because c has at most two interior extrema, and the limit at
    infinity is carried separately with an attainment flag.
    """
    low = _bound("the lower bound on the joint silent miss count", low)
    high = _bound("the upper bound on the joint silent miss count", high, allow_none=True)
    if high is not None and high < low:
        raise CountError("the upper bound is below the lower bound")

    points = {low} if high is None else {low, high}
    points.update(m for m in _stationary_candidates(parts)
                  if m >= low and (high is None or m <= high))
    values = [(m, coefficient(parts, m)) for m in sorted(points)]
    values = [(m, v) for m, v in values if v is not None]
    if not values:
        return {"state": "undefined",
                "reason": ("the coefficient is undefined at every count the declared bound "
                           "allows, because a channel misses nothing there")}

    lowest = min(values, key=lambda pair: pair[1])
    highest = max(values, key=lambda pair: pair[1])
    result = {"state": "computed",
              "identified_set": ("discrete: the joint silent miss count is an integer, so the "
                                 "values below enclose the identified set rather than listing it"),
              "bounded_above": high is not None}
    if high is not None:
        result.update({"minimum": str(lowest[1]), "minimum_at_m": lowest[0],
                       "maximum": str(highest[1]), "maximum_at_m": highest[0],
                       "infimum": str(lowest[1]), "infimum_attained": True,
                       "supremum": str(highest[1]), "supremum_attained": True})
        return result

    # Unbounded above. c tends to 1, and that limit is reached only if c is
    # constant at 1. An unattained limit is not a minimum and is not reported as
    # one: the minimum and maximum fields appear only when they exist.
    limit = Fraction(1)
    constant = all(value == limit for _, value in values) and parts["w"] == 0
    result["as_m_grows"] = {"limit": "1", "attained": bool(constant)}
    if limit < lowest[1]:
        result.update({"infimum": "1", "infimum_attained": False})
        result["minimum"] = None
        result["no_minimum_exists"] = True
    else:
        result.update({"infimum": str(lowest[1]), "infimum_attained": True,
                       "minimum": str(lowest[1]), "minimum_at_m": lowest[0]})
    if limit > highest[1]:
        result.update({"supremum": "1", "supremum_attained": False})
        result["maximum"] = None
        result["no_maximum_exists"] = True
    else:
        result.update({"supremum": str(highest[1]), "supremum_attained": True,
                       "maximum": str(highest[1]), "maximum_at_m": highest[0]})
    return result


def _admissible_constant(parts, low, high):
    """The smallest constant `c` that Definition 32 admits, over every allowed count.

    Definition 32 of the retained primary source states `P[r1 and r2] <= c P[r1]
    P[r2]`: a QUANTITATIVE upper constant, not a sign. A sign verdict does not
    discharge it. The supremum of the coefficient over every admissible
    unobservable count is exactly the smallest constant that holds whatever that
    count turns out to be, so it is computed here and reported as what it is.

    An earlier version of this lane's document said a third channel "can give only
    the sign unless the dark figure is also bounded". This lane's own arithmetic
    contradicted that: the retained three channel table bounds the coefficient
    above by 1679/1188 with no bound on the dark figure at all.
    """
    span = range_over(parts, low, high)
    if span.get("state") != "computed":
        return {"state": "undefined",
                "reason": span.get("reason", "the coefficient has no value over this bound")}
    return {"state": "computed",
            "smallest_admissible_constant": span["supremum"],
            "attained": span["supremum_attained"],
            "holds_for": ("every unobservable count the declared bound allows, with no further "
                          "assumption about that count"),
            "definition": ("the smallest c with P[both miss] <= c P[A misses] P[B misses], which "
                           "is Definition 32's constant for this pair and stratum"),
            "what_it_does_not_supply": (
                "Definition 32 is one ingredient. A majority vote redundancy argument of the kind "
                "in Corollary 3 also needs marginal miss bounds for each channel and a specified "
                "safety critic event, and it covers ghost mistakes as well as misses. None of "
                "those is computed here")}


def analyse(counts, pair=(0, 1), low=0, high=None):
    """The identification report for one declared channel pair."""
    parts = margins(counts, pair)
    low = _bound("the lower bound on the joint silent miss count", low)
    high = _bound("the upper bound on the joint silent miss count", high, allow_none=True)
    threshold = sign_threshold(parts)
    fill = lincoln_petersen(parts)
    state, reason = sign_over(parts, low, high)
    everywhere, _ = sign_over(parts, 0, None)
    settled_without_reference = everywhere not in ("undetermined", "undefined")

    fitted = None
    if fill is not None:
        fitted = {
            "estimator": "the two channel Lincoln and Petersen plug in",
            "defined_when": "some object is detected by both channels, so w > 0",
            "fitted_count": str(fill),
            "fitted_count_is_an_integer": fill.denominator == 1,
            "coefficient_there": str(coefficient(parts, fill)),
            "circularity": ("this estimator is derived by assuming the two channels are "
                            "independent, which is the statement c = 1, so the plug in returns "
                            "c = 1 exactly for every table. A pipeline that fills the "
                            "unobservable cell this way and then reports c has reported its own "
                            "assumption"),
            "scope": ("a statement about this estimator on its defined domain, not about capture "
                      "recapture methods in general. Estimators that model dependence explicitly, "
                      "or that use more than two channels, are not covered by it. Where the "
                      "fitted count is not an integer, c = 1 is attained only off the integer "
                      "grid the count actually lives on")}

    return {
        "artifact_id": "reiyah.joint-miss-identification.report", "version": VERSION,
        "channels": parts["channels"],
        "declared_pair": list(pair),
        "observed_margins": {"all_observed": parts["S"], "pair_both_miss_observed": parts["u"],
                             "first_misses": parts["a"], "second_misses": parts["b"],
                             "pair_both_detect": parts["w"]},
        "unobservable_cell": ("the objects no channel reported. It is part of the numerator of c "
                              "and it is never supplied here"),
        "coefficient_defined_at_zero": _defined_at(parts, 0),
        "declared_bound_on_the_unobservable_cell": {"low": low, "high": high},
        "coefficient_range_under_the_declared_bound": range_over(parts, low, high),
        "coefficient_range_with_no_bound_at_all": range_over(parts, 0, None),
        "capture_recapture_plug_in": fitted,
        "sign_question": {
            "reduction": "c > 1 if and only if m * w > a * b - u * S",
            "threshold": str(threshold) if threshold is not None else None,
            "threshold_absent_because": (None if threshold is not None else
                                         "w is zero, so the condition does not involve m and the "
                                         "sign is settled outright rather than left open"),
            "settled_without_any_reference": settled_without_reference,
            "verdict": {"state": state, "reason": reason},
            "verdict_over_every_admissible_count": everywhere},
        "definition_32_constant": _admissible_constant(parts, low, high),
        "what_a_reference_must_deliver": (
            "a bound on the number of objects no channel reported, tight enough to fall entirely "
            "on one side of the threshold. Tighter buys precision in c; looser leaves the sign "
            "open however many objects are annotated"
            if not settled_without_reference else
            "nothing, for the sign question. The observed margins settle the sign at every "
            "admissible count, so no bound on the unobservable cell can change it"),
        "non_monotonicity": (
            "c is not monotone in the unobservable count, so evaluating it at the ends of a bound "
            "is not its range. The range here is computed from the exact stationary points"),
        "scope": ("an identification statement about declared counts. No population is sampled, no "
                  "channel is named, no value of c is estimated, and nothing here establishes that "
                  "any real pair of channels is or is not positively coupled"),
    }


def main(argv):
    if len(argv) not in (4, 5, 6):
        sys.stderr.write("usage: joint_miss_identification.py N11 N10 N01 [LOW [HIGH]]\n")
        return 2
    try:
        counts = two_channel_counts(*(int(argv[i]) for i in (1, 2, 3)))
        low = int(argv[4]) if len(argv) > 4 else 0
        high = None if len(argv) < 6 or argv[5] == "none" else int(argv[5])
        result = analyse(counts, (0, 1), low, high)
    except (CountError, ValueError) as error:
        sys.stderr.write(f"counts refused: {error}\n")
        return 1
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
