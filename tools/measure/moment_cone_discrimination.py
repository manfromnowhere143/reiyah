"""What a moment-cone rejection does and does not distinguish.

Audit AV uses representability by a scalar iid mixture to decide whether a
mixture-based bound has an identified set. That use is sound. A reader will
naturally over-read a rejection as evidence that the channels fail together, and
this module shows exactly why that reading is wrong.

Two controls, both exact, both with no dependence to explain them:

  heterogeneity alone rejects, for independent channels.  For K mutually
      independent Bernoulli channels with fixed rates p_i,
      m2 - m1^2 = -Var(p)/(K-1), the variance taken uniformly over the named
      channels. Any spread in the rates then puts the vector strictly outside the
      cone with no coupling present.

      Correction of 11 September 2026: an earlier version of this module said
      heterogeneity alone forces the violation, without the independence premise.
      That is too strong. In general

          m2 - m1^2 = meanCov - Var(p)/(K-1)

      where meanCov is the mean covariance over distinct channel pairs. Positive
      dependence can offset the heterogeneity penalty, so a heterogeneous and
      dependent population can sit inside the cone. Cone membership therefore
      isolates neither coupling nor heterogeneity, which is a stronger statement
      than the one it replaces, and the earlier wording is retained in Git history.

  perfect coupling is accepted.  For identical, perfectly coupled channels
      X_i = Z with P(Z) = p, every m_k equals p and the mixture
      (1-p) delta_0 + p delta_1 represents the vector exactly, while a further
      identical channel adds no protection at all.

So on the axis the program cares about, the diagnostic runs backwards: maximum
dependence passes and mere heterogeneity fails. It is an assumption check for a
mixture model, not a measure of coupling.

Exact rational arithmetic. Standard library only. No data is read.
"""
from fractions import Fraction
from functools import reduce
from itertools import combinations
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from moment_cone_certificate import (  # noqa: E402
    expand_certificate, functional, integerise, ldl_negative_direction, required_matrices)

# Exact marginal silent rates of the five retained channels, at the 0.10 floor, on
# all 134,565 annotation rows. Produced by next_channel_decision.py from the caches.
MEASURED_RATES = {
    "mapillary": Fraction(42214, 134565),
    "fcos3d": Fraction(40881, 134565),
    "megvii": Fraction(18091, 134565),
    "pointpillars": Fraction(23387, 134565),
    "centerpoint": Fraction(14938, 134565),
}


def independent_moments(rates):
    """Subset-averaged k-wise all-silent moments of the independent product."""
    channels = len(rates)
    out = [Fraction(1)]
    for k in range(1, channels + 1):
        groups = list(combinations(range(channels), k))
        total = sum((reduce(lambda a, b: a * b, (rates[i] for i in group), Fraction(1))
                     for group in groups), Fraction(0))
        out.append(total / len(groups))
    return out


def mean_pair_covariance(law, channels):
    """Mean covariance over distinct channel pairs, for an explicit joint law."""
    rates = [sum((w for x, w in law.items() if x[i]), Fraction(0)) for i in range(channels)]
    pairs = list(combinations(range(channels), 2))
    total = Fraction(0)
    for i, j in pairs:
        joint = sum((w for x, w in law.items() if x[i] and x[j]), Fraction(0))
        total += joint - rates[i] * rates[j]
    return total / len(pairs), rates


def variance(rates):
    channels = len(rates)
    mean = sum(rates, Fraction(0)) / channels
    return sum(((p - mean) ** 2 for p in rates), Fraction(0)) / channels


def decide(moments, channels):
    """Infeasible with a witness, or None. Uses the certificate path only."""
    for form, matrix in required_matrices(moments, channels):
        direction, _reason = ldl_negative_direction(matrix)
        if direction is None:
            continue
        direction = integerise(direction)
        coefficients = expand_certificate(form, direction)
        value = functional(coefficients, moments)
        if value < 0:
            return {"form": form,
                    "polynomial_coefficients": [str(v) for v in direction],
                    "functional": str(value)}
    return None


def main(argv):
    report = {"artifact_id": "reiyah.moment-cone.discrimination", "version": "0.1.0",
              "controls": {}}

    identity = []
    for rates in ([Fraction(1, 4), Fraction(3, 4)],
                  [Fraction(1, 10), Fraction(1, 5), Fraction(7, 10)],
                  [Fraction(1, 3)] * 4,
                  list(MEASURED_RATES.values())):
        moments = independent_moments(rates)
        left = moments[2] - moments[1] ** 2
        right = -variance(rates) / (len(rates) - 1)
        identity.append({"rates": [str(p) for p in rates], "m2_minus_m1_squared": str(left),
                         "minus_variance_over_k_minus_1": str(right), "equal": left == right})
    report["controls"]["variance_identity"] = {
        "statement": "for mutually independent Bernoulli channels, m2 - m1^2 = -Var(p)/(K-1)",
        "cases": identity,
        "all_equal": all(case["equal"] for case in identity)}

    rates = list(MEASURED_RATES.values())
    moments = independent_moments(rates)
    witness = decide(moments, len(rates))
    report["controls"]["measured_rates_under_independence"] = {
        "channels": list(MEASURED_RATES),
        "rates": {name: str(value) for name, value in MEASURED_RATES.items()},
        "variance_over_named_channels": str(variance(rates)),
        "moments": [str(value) for value in moments[1:]],
        "verdict": "infeasible" if witness else "not refuted by the certificate path",
        "witness": witness,
        "dependence_present": False,
        "reading": ("these five channels, made mutually independent at their own measured rates, "
                    "already fall outside the cone. A rejection therefore cannot be read as "
                    "evidence that the channels fail together")}

    coupled = []
    for p in (Fraction(1, 10), Fraction(1, 2), Fraction(9, 10)):
        moments = [Fraction(1)] + [p] * 5
        witness = decide(moments, 5)
        coupled.append({"p": str(p), "moments": [str(p)] * 5,
                        "verdict": "infeasible" if witness else "representable",
                        "representing_measure": f"(1 - {p}) delta_0 + {p} delta_1",
                        "benefit_of_one_more_identical_channel": "0"})
    report["controls"]["perfect_coupling"] = {
        "statement": "identical perfectly coupled channels give m_k = p for every k",
        "cases": coupled,
        "all_representable": all(case["verdict"] == "representable" for case in coupled)}

    # The general decomposition, which is what bounds the reading.
    law = {(1, 1, 1): Fraction(1, 4), (0, 0, 0): Fraction(1, 2),
           (1, 0, 0): Fraction(1, 8), (1, 1, 0): Fraction(1, 8)}
    cov, rates = mean_pair_covariance(law, 3)
    m1 = sum(rates, Fraction(0)) / 3
    pairs = list(combinations(range(3), 2))
    m2 = sum((sum((w for x, w in law.items() if x[i] and x[j]), Fraction(0))
              for i, j in pairs), Fraction(0)) / len(pairs)
    report["controls"]["general_decomposition"] = {
        "statement": "m2 - m1^2 = meanCov - Var(p)/(K-1) for any joint law",
        "example": "a heterogeneous and dependent law that still satisfies the second moment condition",
        "rates": [str(r) for r in rates],
        "variance": str(variance(rates)), "mean_pair_covariance": str(cov),
        "m2_minus_m1_squared": str(m2 - m1 ** 2),
        "identity_holds": m2 - m1 ** 2 == cov - variance(rates) / 2,
        "inside_the_second_moment_condition": m2 - m1 ** 2 >= 0,
        "reading": ("positive dependence can offset the heterogeneity penalty, so cone membership "
                    "isolates neither coupling nor heterogeneity")}

    report["conclusion"] = (
        "the diagnostic tests representability by a scalar iid mixture. For independent channels, "
        "heterogeneous rates alone reject; perfect coupling is accepted; and in general "
        "m2 - m1^2 = meanCov - Var(p)/(K-1), so a heterogeneous dependent population can sit inside "
        "the cone. Membership isolates neither coupling nor heterogeneity. It is an assumption "
        "check for a mixture-based bound and no verdict of it should be quoted as a dependence result")
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
