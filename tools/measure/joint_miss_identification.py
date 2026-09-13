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

VERSION = "0.2.0"


class CountError(Exception):
    """The declared counts do not describe a population this analysis applies to."""


def _nonneg(name, value):
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise CountError(f"{name} must be a non negative integer, not {value!r}")
    return value


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
    """c > 1 exactly when m exceeds this. None when both channels detect nothing jointly."""
    if parts["w"] == 0:
        return None
    return Fraction(parts["a"] * parts["b"] - parts["u"] * parts["S"], parts["w"])


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
    """The exact range of c as m runs over the integers in [low, high]."""
    if low < 0:
        raise CountError("the lower bound on the joint silent miss count cannot be negative")
    if high is not None and high < low:
        raise CountError("the upper bound is below the lower bound")

    unbounded = high is None
    ceiling = high
    if unbounded:
        reach = max(_stationary_candidates(parts), default=low)
        ceiling = max(low, reach + 1)

    values = [(m, coefficient(parts, m)) for m in _candidates(parts, low, ceiling)]
    values = [(m, v) for m, v in values if v is not None]
    if not values:
        return {"state": "undefined",
                "reason": ("every admissible joint silent miss count leaves a channel with no "
                           "misses at all, so the ratio has no value")}

    lowest = min(values, key=lambda pair: pair[1])
    highest = max(values, key=lambda pair: pair[1])
    result = {"state": "computed",
              "lower": str(lowest[1]), "lower_at_m": lowest[0],
              "upper": str(highest[1]), "upper_at_m": highest[0],
              "bounded_above": not unbounded}
    if not unbounded:
        return result

    # With no upper bound, c tends to 1 as m grows. That limit is part of the
    # range's closure and is NOT reached at any count. An earlier version reported
    # only the extremes over the candidate integers, which understated the reach
    # of the range whenever c descended towards 1 from one side. An unattained
    # limit and an attained extreme are different things and stay different here.
    limit = Fraction(1)
    result["as_m_grows"] = {"limit": "1", "attained": False}
    if limit < lowest[1]:
        result["infimum"] = "1"
        result["infimum_attained"] = False
        result["lower_is_the_smallest_attained_value"] = True
    else:
        result["infimum"] = str(lowest[1])
        result["infimum_attained"] = True
    if limit > highest[1]:
        result["supremum"] = "1"
        result["supremum_attained"] = False
        result["upper_is_the_largest_attained_value"] = True
    else:
        result["supremum"] = str(highest[1])
        result["supremum_attained"] = True
    return result


def analyse(counts, pair=(0, 1), low=0, high=None):
    """The identification report for one declared channel pair."""
    parts = margins(counts, pair)
    threshold = sign_threshold(parts)
    fill = lincoln_petersen(parts)

    if threshold is None:
        sign = {"state": "undetermined",
                "reason": ("no object was detected by both named channels, so the threshold is "
                           "undefined and the sign question has no reduction here")}
    elif threshold < 0:
        sign = {"state": "c_greater_than_1",
                "reason": ("the threshold is below zero, so c exceeds 1 for every admissible "
                           "joint silent miss count. The other channels already observe enough of "
                           "what this pair both missed to settle the sign without a reference")}
    elif high is not None and Fraction(high) <= threshold:
        sign = {"state": "c_at_most_1",
                "reason": (f"the declared bound puts the joint silent miss count at or below "
                           f"{threshold}, so c is at most 1")}
    elif Fraction(low) > threshold:
        sign = {"state": "c_greater_than_1",
                "reason": (f"the declared bound puts the joint silent miss count above "
                           f"{threshold}, so c exceeds 1")}
    else:
        sign = {"state": "undetermined",
                "reason": (f"the declared bound spans the threshold {threshold}, so both a "
                           "positively coupled and a not positively coupled population are "
                           "consistent with these counts")}

    settled_without_reference = threshold is not None and threshold < 0
    return {
        "artifact_id": "reiyah.joint-miss-identification.report", "version": VERSION,
        "channels": parts["channels"],
        "declared_pair": list(pair),
        "observed_margins": {"all_observed": parts["S"], "pair_both_miss_observed": parts["u"],
                             "first_misses": parts["a"], "second_misses": parts["b"],
                             "pair_both_detect": parts["w"]},
        "unobservable_cell": ("the objects no channel reported. It is part of the numerator of c "
                              "and it is never supplied here"),
        "declared_bound_on_the_unobservable_cell": {"low": low, "high": high},
        "coefficient_range_under_the_declared_bound": range_over(parts, low, high),
        "coefficient_range_with_no_bound_at_all": range_over(parts, 0, None),
        "capture_recapture": {
            "dark_figure": str(fill) if fill is not None else None,
            "coefficient_there": (str(coefficient(parts, fill)) if fill is not None else None),
            "circularity": ("for two channels, filling the unobservable cell this way gives c = 1 "
                            "exactly, because the estimator is derived by assuming the channels "
                            "are independent, which is the statement c = 1. A pipeline that does "
                            "this and reports c has reported its own assumption")},
        "sign_question": {
            "reduction": "c > 1 if and only if m * w > a * b - u * S",
            "threshold": str(threshold) if threshold is not None else None,
            "settled_without_any_reference": settled_without_reference,
            "verdict": sign},
        "what_a_reference_must_deliver": (
            "a bound on the number of objects no channel reported, tight enough to fall entirely "
            "on one side of the threshold. Tighter buys precision in c; looser leaves the sign "
            "open however many objects are annotated"
            if not settled_without_reference else
            "nothing, for the sign question. The observed margins already place the threshold "
            "below zero, so no bound on the unobservable cell can change the sign"),
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
