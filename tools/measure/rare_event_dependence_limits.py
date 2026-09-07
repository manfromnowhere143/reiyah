#!/usr/bin/env python3
"""Deterministic synthetic limits for passive dependence measurement.

No real data, simulation, inference on a vehicle, or safety-budget calculator.
Probability tables, total-variation bounds and logarithm enclosures use Fraction.
See docs/RSS_TRANSFER_AND_RARE_EVENT_LIMITS_2026-09-07.md for assumptions/proofs.
"""

from fractions import Fraction as F
import json


def rational(value):
    if isinstance(value, bool) or not isinstance(value, (int, F)):
        raise ValueError("an exact integer or Fraction is required")
    value = F(value)
    if max(value.numerator.bit_length(), value.denominator.bit_length()) > 1024:
        raise ValueError("input exceeds the rational operand limit")
    return value


def positive_integer(value):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("a positive integer is required")
    return value


def law(p_a, p_b, joint):
    """Cell order: both fail, A only, B only, neither."""
    p_a, p_b, joint = map(rational, (p_a, p_b, joint))
    cells = (joint, p_a - joint, p_b - joint, 1 - p_a - p_b + joint)
    if any(x < 0 or x > 1 for x in cells):
        raise ValueError("infeasible Bernoulli joint law")
    return cells


def checked_law(cells):
    if len(cells) != 4:
        raise ValueError("four Bernoulli cells are required")
    cells = tuple(map(rational, cells))
    if sum(cells) != 1 or any(x < 0 for x in cells):
        raise ValueError("probability mass must be nonnegative and sum to one")
    return cells


def coincidence(cells):
    a, b, c, _ = checked_law(cells)
    denominator = (a + b) * (a + c)
    return a / denominator if denominator else None


def total_variation(first, second):
    first, second = checked_law(first), checked_law(second)
    return sum(abs(a - b) for a, b in zip(first, second)) / 2


def iid_test_power_bound(first, second, n, alpha):
    """For any test with E_first[test] <= alpha: E_second[test] <= this.

    Uses TV(P**n,Q**n) <= n TV(P,Q), an upper bound, not exact test power.
    Independent, identically distributed complete observations are assumed.
    """
    n = positive_integer(n)
    alpha = rational(alpha)
    if not 0 <= alpha <= 1:
        raise ValueError("alpha must lie in [0,1]")
    return min(F(1), alpha + n * total_variation(first, second))


def ceil_fraction(x):
    return -(-x.numerator // x.denominator)


def _log_unit_interval(x, terms):
    # 1 <= x <= 2. log(x) = 2 sum_{k>=0} z**(2k+1)/(2k+1).
    z = (x - 1) / (x + 1)
    lower = 2 * sum(z ** (2 * k + 1) / (2 * k + 1) for k in range(terms))
    tail = 2 * z ** (2 * terms + 1) / ((2 * terms + 1) * (1 - z * z))
    return lower, lower + tail


def log_enclosure(value, terms):
    """Rational lower/upper bounds; positive logarithm arguments only."""
    value = rational(value)
    positive_integer(terms)
    if value <= 0 or terms > 128:
        raise ValueError("positive argument and at most 128 terms required")
    if value < 1:
        lo, hi = log_enclosure(1 / value, terms)
        return -hi, -lo
    exponent = 0
    while value > 2:
        value /= 2
        exponent += 1
    lo, hi = _log_unit_interval(value, terms)
    two_lo, two_hi = _log_unit_interval(F(2), terms)
    return lo + exponent * two_lo, hi + exponent * two_hi


def zero_event_sample_requirement(q, alpha):
    """Minimum fixed n for (1-q)**n <= alpha, certified by rational bounds.

    This is the zero-event exact-binomial rule. It is neither an optimal-test
    lower bound nor a powered design, and does not guarantee zero observations.
    """
    q, alpha = map(rational, (q, alpha))
    if not 0 < q < 1 or not 0 < alpha < 1:
        raise ValueError("q and alpha must lie strictly inside (0,1)")
    for terms in (8, 16, 32, 64, 128):
        l_lo, l_hi = log_enclosure(1 / alpha, terms)
        d_lo, d_hi = log_enclosure(1 / (1 - q), terms)
        lower, upper = l_lo / d_hi, l_hi / d_lo
        n_lo, n_hi = ceil_fraction(lower), ceil_fraction(upper)
        if n_lo == n_hi:
            return {"n": n_lo, "log_series_terms": terms,
                    "method": "rational_log_enclosures_with_equal_ceiling",
                    "ratio_lower": str(lower), "ratio_upper": str(upper)}
        # Exact integer logarithm ratios may straddle a ceiling forever. Resolve
        # small candidates using rational powers rather than rounding a bound.
        power_bits = n_hi * max((1 - q).numerator.bit_length(), (1 - q).denominator.bit_length())
        if n_hi - n_lo <= 4 and power_bits <= 100000:
            for n in range(n_lo, n_hi + 1):
                if (1 - q) ** n <= alpha and (1 - q) ** (n - 1) > alpha:
                    return {"n": n, "log_series_terms": terms,
                            "method": "exact_rational_power_boundary_resolution",
                            "ratio_lower": str(lower), "ratio_upper": str(upper)}
    raise ArithmeticError("integer boundary unresolved at the declared precision limit")


def mixture_report(weights, laws):
    if len(weights) != len(laws) or not laws:
        raise ValueError("matching nonempty weights and laws required")
    weights = tuple(map(rational, weights))
    laws = tuple(map(checked_law, laws))
    if any(w < 0 for w in weights) or sum(weights) != 1:
        raise ValueError("nonnegative weights must sum to one")
    mixed = tuple(sum(w * row[k] for w, row in zip(weights, laws)) for k in range(4))
    expected = sum(w * (a + b) * (a + c) for w, (a, b, c, _) in zip(weights, laws))
    return {"weights": list(map(str, weights)),
            "stratum_laws": [list(map(str, row)) for row in laws],
            "stratum_c": [None if (v := coincidence(row)) is None else str(v) for row in laws],
            "mixture_law": list(map(str, mixed)),
            "mixture_c": None if (v := coincidence(mixed)) is None else str(v),
            "conditional_aggregate_c": str(mixed[0] / expected) if expected else None}


def build_report():
    p, alpha = F(1, 100000), F(1, 20)
    first, second = law(p, p, p * p), law(p, p, 2 * p * p)
    n = 100000
    tv = total_variation(first, second)
    desired_power = F(19, 20)
    return {
        "artifact_id": "reiyah.rare-event-dependence-limits.2026-09-07",
        "version": "0.1.0", "lifecycle_status": "exploratory",
        "evidence_kind": "authored_exact_synthetic_derivation",
        "assumptions": ["iid opportunity draws", "perfect reference",
                        "both Bernoulli channel outcomes observed on every draw",
                        "fixed known marginal rates", "fixed testing horizon",
                        "no informative side observations or transport assumptions"],
        "observed_physical_performance": None,
        "safety_validation_budget": None,
        "rare_pair": {
            "marginal_a": str(p), "marginal_b": str(p),
            "null_law": list(map(str, first)), "alternative_law": list(map(str, second)),
            "null_c": str(coincidence(first)), "alternative_c": str(coincidence(second)),
            "single_observation_tv": str(tv), "n": n, "alpha": str(alpha),
            "any_test_power_upper_bound": str(iid_test_power_bound(first, second, n, alpha)),
            "desired_power": str(desired_power),
            "necessary_n_from_tv_union_bound": ceil_fraction((desired_power - alpha) / tv),
            "necessary_n_is_sufficient": False,
        },
        "zero_event_rules": [
            {"event": event, "probability_threshold": str(q), "alpha": str(alpha),
             **zero_event_sample_requirement(q, alpha)}
            for event, q in [("single_channel_failure", p),
                             ("joint_failure_at_c_1", p * p),
                             ("joint_failure_at_c_2", 2 * p * p)]
        ],
        "mixture_controls": {
            "conditional_independence_does_not_bound_mixture_c": mixture_report(
                [F(1, 2), F(1, 2)], [law(F(1, 1000), F(1, 1000), F(1, 1000000)),
                                      law(F(1, 100), F(1, 100), F(1, 10000))]),
            "mixture_bound_does_not_require_every_conditional_bound": mixture_report(
                [F(1, 2), F(1, 2)], [law(F(1, 2), F(1, 2), F(2, 5)),
                                      law(F(1, 2), F(1, 2), F(1, 10))]),
        },
        "claim_boundary": "No optimal sample complexity, real error rate, universal impossibility, novelty, or RSS refutation claimed.",
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2, sort_keys=True))
