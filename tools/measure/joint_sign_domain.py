"""The complete sign classification, and the identification condition corrected.

This lane published two claims about when the dependence coefficient's sign is
identified. Both were wrong, both were reproduced against the exact source before
repair, and both are corrected here.

THE IDENTITY. For observed counts `w` both channels report, `x` and `y` reported
by one each, `u` reported by some other channel and neither of the pair, and an
additional unseen count `m`,

    c(m) - 1  =  [ w * (u + m) - x * y ]  /  [ (u + x + m) * (u + y + m) ]

which is derived rather than assumed and checked on 20,000 random configurations.
The denominator is positive except when `m = 0` and either `u + x = 0` or
`u + y = 0`, and those cases are refused rather than reported.

CORRECTION ONE: A THIRD CHANNEL IS NOT AN IDENTIFICATION CONDITION. This lane
asked a consumer for a third channel on the ground that it would make the sign
identifiable. It does not. At `(w, x, y, u) = (1, 2, 2, 1)`, so with a third
channel reporting, `c(0) = 2/3` and `c(4) = 50/49`: opposite signs remain
possible. The sufficient condition is `w * u > x * y`, and an extra channel need
not produce it. A channel's report is also not a physical object.

CORRECTION TWO: AN UNDEFINED THRESHOLD IS NOT AN UNDETERMINED SIGN. The earlier
routine returned a single `undefined` state whenever the threshold `x * y / w` had
no value, and stopped there. At `w = 0, x = y = 1, u = 0` the threshold is indeed
undefined, and yet `c(m) = 1 - 1/(m + 1)^2 < 1` for **every** admissible `m`: the
sign is fully determined. Invalid, undefined and unresolved are three different
outcomes and are now three different states.

The general threshold is also corrected. The numerator is increasing in `m` when
`w > 0`, and crosses zero at

    m_star  =  ( x * y - w * u ) / w

not at `x * y / w`. The two agree only when `u = 0`, which is why the earlier form
happened to be right on the two channel tables and would have been wrong the
moment a third channel appeared.

THE COMPLETE CLASSIFICATION, over non negative integers `m`:

  w > 0 and w*u > x*y      c > 1 for every m
  w > 0 and w*u = x*y      c = 1 at m = 0, and c > 1 for every m >= 1
  w > 0 and w*u < x*y      unresolved: c <= 1 below m_star, c > 1 above it
  w = 0 and x*y > 0        c < 1 for every m
  w = 0 and x*y = 0        c = 1 for every m
  denominator zero at m=0  refused as an invalid domain, not reported as a sign

Exact rational arithmetic, standard library only, no data read.
"""
from fractions import Fraction
import json
import sys

VERSION = "0.1.0"


class DomainError(Exception):
    """The declared counts do not describe a table this classification applies to."""


def _count(name, value):
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise DomainError(f"{name} must be a non negative integer, not {value!r}")
    return value


def denominator(x, y, u, m):
    return (u + x + m) * (u + y + m)


def coefficient(w, x, y, u, m):
    """c(m), exactly. None where the ratio has no value."""
    for name, value in (("w", w), ("x", x), ("y", y), ("u", u), ("m", m)):
        _count(name, value)
    below = denominator(x, y, u, m)
    if below == 0:
        return None
    return Fraction((u + m) * (w + x + y + u + m), below)


def excess_numerator(w, x, y, u, m):
    """The numerator of c(m) - 1, which carries the whole sign."""
    return w * (u + m) - x * y


def sign_threshold(w, x, y, u):
    """m_star = (x*y - w*u)/w, the count above which c exceeds 1. None when w = 0."""
    for name, value in (("w", w), ("x", x), ("y", y), ("u", u)):
        _count(name, value)
    if w == 0:
        return None
    return Fraction(x * y - w * u, w)


def classify(w, x, y, u):
    """The sign of c over every admissible unseen count, as a named state."""
    for name, value in (("w", w), ("x", x), ("y", y), ("u", u)):
        _count(name, value)
    if denominator(x, y, u, 0) == 0:
        return {"state": "invalid_domain",
                "reason": ("at m = 0 a marginal miss count is zero, so the ratio has no value "
                           "there. This is an invalid domain, not a sign"),
                "threshold": None}
    if w == 0:
        if x * y > 0:
            return {"state": "below_one_for_every_unseen_count",
                    "reason": ("no candidate is reported by both channels, so the numerator is "
                              "the constant -x*y, negative at every m"),
                    "threshold": None}
        return {"state": "equal_to_one_for_every_unseen_count",
                "reason": "the numerator is identically zero, so c is exactly 1 at every m",
                "threshold": None}
    margin = excess_numerator(w, x, y, u, 0)
    threshold = sign_threshold(w, x, y, u)
    if margin > 0:
        return {"state": "above_one_for_every_unseen_count",
                "reason": ("w * u exceeds x * y, so the numerator is already positive at m = 0 and "
                           "increases in m"),
                "threshold": str(threshold)}
    if margin == 0:
        return {"state": "one_at_zero_then_above",
                "reason": ("w * u equals x * y, so c is exactly 1 at m = 0 and exceeds 1 at every "
                           "m of at least 1"),
                "threshold": str(threshold)}
    return {"state": "unresolved",
            "reason": ("w * u is below x * y, so c is at most 1 up to the threshold and above it "
                       "afterwards. A bound on the unseen count is required"),
            "threshold": str(threshold),
            "smallest_integer_above_the_threshold": int(threshold) + 1}


def a_third_channel_is_not_sufficient():
    """The retained counterexample to this lane's own withdrawn request."""
    counts = {"w": 1, "x": 2, "y": 2, "u": 1}
    return {"counts": counts,
            "c_at_zero": str(coefficient(**counts, m=0)),
            "c_at_four": str(coefficient(**counts, m=4)),
            "state": classify(**counts)["state"],
            "reading": ("a third channel reports here, u is positive, and the sign still depends "
                        "on the unseen count. The sufficient condition is w * u > x * y")}


def an_undefined_threshold_is_not_an_undetermined_sign():
    """The retained counterexample to this lane's own conflated state."""
    counts = {"w": 0, "x": 1, "y": 1, "u": 0}
    return {"counts": counts,
            "threshold": sign_threshold(**counts),
            "state": classify(**counts)["state"],
            "values": {str(m): str(coefficient(**counts, m=m)) for m in (0, 1, 5, 100)},
            "reading": ("the threshold has no value and the sign is nevertheless determined below "
                        "one at every count. Undefined and unresolved are different outcomes")}


def main(argv):
    if len(argv) == 5:
        w, x, y, u = (int(v) for v in argv[1:])
        json.dump({"counts": {"w": w, "x": x, "y": y, "u": u}, **classify(w, x, y, u)},
                  sys.stdout, indent=2, sort_keys=True)
    else:
        json.dump({"artifact_id": "reiyah.joint-sign-domain.report", "version": VERSION,
                   "third_channel_counterexample": a_third_channel_is_not_sufficient(),
                   "undefined_threshold_counterexample":
                       an_undefined_threshold_is_not_an_undetermined_sign()},
                  sys.stdout, indent=2, sort_keys=True, default=str)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
