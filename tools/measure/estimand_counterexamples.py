"""Deterministic counterexamples for the joint-miss dependence estimand.

Every number below is closed-form arithmetic on declared probability models. There
is no sampling, no seed, and no data. Re-running must reproduce the transcript
byte for byte.

The estimand under test is

    c_s = P_s(M_A = 1 and M_B = 1) / [ P_s(M_A = 1) P_s(M_B = 1) ]

which is the smallest constant satisfying the one-sided c-approximate independence
inequality of RSS Definition 32 for that stratum and channel pair. See
docs/PRIMARY_SOURCE_CUSTODY_2026-08-29.md entry S-01 for the retained primary text.

Each case shows that a value of c is consistent with a data-generating process that
the value alone cannot distinguish. Together they are the evidence for the
non-identification statement in docs/ESTIMAND_RSS_DEFINITION_32.md section 4.

Usage:
  python3 tools/measure/estimand_counterexamples.py
"""

from fractions import Fraction as F


def mixture(components):
    """components: list of (weight, theta_A, theta_B) with channels conditionally
    independent GIVEN the component. Returns exact (pA, pB, pAB, c)."""
    pA = sum(w * a for w, a, _ in components)
    pB = sum(w * b for w, _, b in components)
    pAB = sum(w * a * b for w, a, b in components)
    c = pAB / (pA * pB) if pA * pB != 0 else None
    return pA, pB, pAB, c


def cells(a, b, cc, d):
    """a=both miss, b=A only, cc=B only, d=neither. Returns (n, pA, pB, pAB, c)."""
    n = a + b + cc + d
    pA = F(a + b, n)
    pB = F(a + cc, n)
    pAB = F(a, n)
    c = pAB / (pA * pB) if pA * pB != 0 else None
    return n, pA, pB, pAB, c


def line(label, pA, pB, pAB, c, width=54):
    cs = "undefined" if c is None else f"{float(c):.4f}"
    print(f"  {label:<{width}} pA={float(pA):.6f}  pB={float(pB):.6f}  "
          f"pAB={float(pAB):.6f}  c={cs}")


def rule(title):
    print()
    print("=" * 96)
    print(title)
    print("=" * 96)


def main() -> int:
    print("=" * 96)
    print("ESTIMAND COUNTEREXAMPLES - exact arithmetic, no sampling, no data")
    print("c_s = P_s(both miss) / [P_s(A miss) P_s(B miss)]   (RSS Definition 32 constant)")
    print("=" * 96)

    rule("CE-1  c > 1 with ZERO channel coupling: residual difficulty heterogeneity alone")
    comp = [(F(1, 2), F(4, 10), F(4, 10)), (F(1, 2), F(2, 100), F(2, 100))]
    pA, pB, pAB, c = mixture(comp)
    print("  Two equally weighted latent difficulty regimes. Within each regime the two")
    print("  channels are EXACTLY conditionally independent. No common cause, no shared")
    print("  component, no coupling of any kind.")
    print("    regime u: weight 1/2, theta_A = theta_B = 0.40")
    print("    regime v: weight 1/2, theta_A = theta_B = 0.02")
    line("pooled over the unmodelled regime", pA, pB, pAB, c)
    print(f"  Conclusion: c = {float(c):.4f} > 1 is produced by incomplete stratification alone.")
    print("  c > 1 is therefore NOT evidence of common-cause coupling.")

    rule("CE-2  c < 1 with NO diversity mechanism: anti-correlated difficulty alone")
    comp = [(F(1, 2), F(4, 10), F(2, 100)), (F(1, 2), F(2, 100), F(4, 10))]
    pA, pB, pAB, c = mixture(comp)
    print("  Same construction, but the regimes are hard for opposite channels.")
    print("    regime u: weight 1/2, theta_A = 0.40, theta_B = 0.02")
    print("    regime v: weight 1/2, theta_A = 0.02, theta_B = 0.40")
    print("  Channels remain EXACTLY conditionally independent within each regime.")
    line("pooled over the unmodelled regime", pA, pB, pAB, c)
    print(f"  Conclusion: c = {float(c):.4f} < 1 arises with no protective mechanism and no")
    print("  intervention on channel construction. c < 1 is NOT evidence that diversity")
    print("  protected the system.")

    rule("CE-3  pooled c near independence while a subgroup is severely coupled")
    strata = [
        ("bulk    (mass 0.99, independent)", F(99, 100), F(1, 10), F(1, 10), F(1, 100)),
        ("subgroup(mass 0.01, coupled)   ", F(1, 100), F(1, 10), F(1, 10), F(5, 100)),
    ]
    pA = sum(w * a for _, w, a, _, _ in strata)
    pB = sum(w * b for _, w, _, b, _ in strata)
    pAB = sum(w * j for _, w, _, _, j in strata)
    for name, w, a, b, j in strata:
        line(name, a, b, j, j / (a * b))
    line("POOLED", pA, pB, pAB, pAB / (pA * pB))
    print(f"  Pooled c = {float(pAB/(pA*pB)):.4f}. Worst subgroup c = 5.0000.")
    print("  Both marginals are identical everywhere, so no marginal diagnostic can")
    print("  reveal the subgroup. Only the worst-group partition can.")

    rule("CE-4  c moves when ONE channel's operating point moves, coupling unchanged")
    base = [(F(1, 2), F(4, 10), None), (F(1, 2), F(2, 100), None)]
    for tag, tb in (("tau_1: theta_B = (0.40, 0.02)", (F(4, 10), F(2, 100))),
                    ("tau_2: theta_B = (0.50, 0.30)", (F(5, 10), F(30, 100)))):
        comp = [(base[i][0], base[i][1], tb[i]) for i in range(2)]
        pA, pB, pAB, c = mixture(comp)
        line(tag, pA, pB, pAB, c)
    print("  Channel A is untouched and the conditional-independence structure is untouched.")
    print("  Only B's operating point moved. c is not invariant to operating point, so a")
    print("  reported c is meaningless without both marginals and the declared operating point.")

    rule("CE-5  reference error alone moves c in BOTH directions from exact independence")
    n, pA, pB, pAB, c = cells(100, 900, 900, 8100)
    line("TRUTH: a=100 b=900 c=900 d=8100 (exactly independent)", pA, pB, pAB, c)
    n2, pA2, pB2, pAB2, c2 = cells(50, 900, 900, 8100)
    line("omit 50 TRUE both-miss opportunities (0.50% of universe)", pA2, pB2, pAB2, c2)
    n3, pA3, pB3, pAB3, c3 = cells(150, 900, 900, 8100)
    line("add 50 FALSE opportunities no channel can detect     ", pA3, pB3, pAB3, c3)
    print(f"  A 0.50% reference error moves c from exactly 1.0000 to {float(c2):.4f} or "
          f"{float(c3):.4f}.")
    print("  Direction depends only on which way the reference errs. Omission of hard")
    print("  objects deflates c; phantom undetectable labels inflate it. Both are plausible.")
    print("  This is why reference-error partial identification is P0 and must be carried")
    print("  in the same contract as the estimate, not appended to it.")

    rule("CE-6  zero denominator: c is undefined, never zero, never one")
    n4, pA4, pB4, pAB4, c4 = cells(0, 0, 5, 995)
    line("channel A never misses in this stratum                ", pA4, pB4, pAB4, c4)
    print("  P(A miss) = 0 makes the denominator zero. The correct output is the explicit")
    print("  undefined state. Coercing it to 0, 1, or 'independent' is prohibited.")

    print()
    print("=" * 96)
    print("SUMMARY")
    print("=" * 96)
    print("  c > 1 alone       : consistent with coupling OR incomplete stratification")
    print("                      OR correlated reference error. Not identified.")
    print("  c < 1 alone       : consistent with diversity benefit OR anti-correlated")
    print("                      difficulty OR reference error OR sampling noise. Not identified.")
    print("  pooled c alone    : can be arbitrarily close to 1 with an arbitrarily bad subgroup.")
    print("  c without marginals, operating point, denominator and clustering unit: not")
    print("                      interpretable at all.")
    print("  No value of c, at any confidence level, is causal evidence about channel design.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
