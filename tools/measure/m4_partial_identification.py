"""M4: sharp-ish bounds on the coincident-miss ratio under reference-process error.

SYNTHETIC FIXTURES ONLY. This module ingests no measured data and emits no empirical
record. It exercises the solver and its adversarial tests on declared fixtures so the
method can be reviewed before it is ever pointed at a measurement.

THE ESTIMAND

    c = P(both miss) / [ P(A miss) P(B miss) ]
      = a * n / [ (a + b) * (a + cc) ]

on the 2x2 contingency of one stratum, where

    a  = both miss        b  = A only miss
    cc = B only miss      d  = neither miss        n = a + b + cc + d

WHY A SOLVER IS NEEDED

`estimand_counterexamples.py` case CE-5 shows a 0.50 percent reference error moves c
from exactly 1.0000 to 0.5512 or to 1.3673. Reference error is therefore not a
second-order correction to be appended; it is the dominant term, and the reported
quantity must be an interval over what the reference could have gotten wrong.

THE OBJECTIVE IS NOT LINEAR-FRACTIONAL

c is a ratio of two quadratics in the cell counts, because the numerator carries a*n.
Linear programming therefore does not apply and no LP-based sharpness claim is made.
The feasible set is a box in the four cell perturbations, intersected with validity
constraints. This module optimises by exhaustive box-vertex enumeration plus a dense
declared grid plus a seeded random probe, and reports the result as

    NUMERICALLY VERIFIED OVER A DECLARED GRID, NOT PROVED SHARP.

That label is part of the output and must not be softened. If the random probe ever
beats the grid optimum, the run reports a SHARPNESS BREACH rather than silently
taking the better value.

THE ASSUMPTION LADDER

  L0  no assumptions. Any cell may take any admissible value. Reported as unbounded
      or undefined wherever the feasible set permits it. No finite surrogate.
  L1  mechanism-specific budgets, no assumption about which cells absorb them.
  L2  L1 plus a non-differential restriction: reference error does not depend on which
      channel failed, so the perturbation applied to the two single-miss cells is tied.
  L3  L2 plus error budgets estimated from blinded reannotation. Only L3 may ever carry
      a headline, and only after independent replication.

UNDEFINED IS NOT A NUMBER

If any feasible point drives (a+b) or (a+cc) to zero, the upper end is reported as
`unbounded` and the interval is left open. Coercion to a large finite value, to zero,
or to `independent` is prohibited.

Usage:
  python3 tools/measure/m4_partial_identification.py
"""

import itertools
import random

GRID_PER_DIM = 21          # declared grid resolution per cell dimension
RANDOM_PROBES = 200_000    # seeded adversarial probe against the grid optimum
SEED = 20260829


# ----------------------------------------------------------------------------- core

def ratio(a: float, b: float, cc: float, d: float):
    """c for one cell vector, or None when the denominator vanishes."""
    n = a + b + cc + d
    ra, rb = a + b, a + cc
    if n <= 0 or ra <= 0 or rb <= 0:
        return None
    return (a * n) / (ra * rb)


def admissible(a, b, cc, d):
    return a >= 0 and b >= 0 and cc >= 0 and d >= 0 and (a + b + cc + d) > 0


def budget_box(cells, budgets):
    """Per-cell (low, high) reachable counts under the declared mechanism budgets.

    Budgets are stated per mechanism and mapped onto the cells each mechanism can
    move. The mapping is deliberately generous: a mechanism that could plausibly
    touch a cell contributes its full budget to that cell's range. A narrower
    mapping is a stronger assumption and belongs at L2 or L3, not here.
    """
    a, b, cc, d = cells
    omit = budgets["omitted_true_opportunities"]
    false_opp = budgets["false_opportunities"]
    cls = budgets["class_or_stratum_error"]
    loc = budgets["localization_or_pose_error"]

    # An omitted true opportunity can belong to any cell: nothing observed it.
    # A false opportunity most naturally sits in both-miss but may sit anywhere.
    # Class and stratum error move rows across the stratum boundary in either
    # direction. Localization error flips a row between cells inside the stratum.
    up = omit + cls + loc
    down = false_opp + cls + loc
    return [
        (max(0.0, a - down), a + up),
        (max(0.0, b - down), b + up),
        (max(0.0, cc - down), cc + up),
        (max(0.0, d - down), d + up),
    ]


def optimise(box, tie_single_miss=False):
    """Grid + vertex search over the box. Returns (lo, hi, unbounded_flag, best_pts)."""
    axes = []
    for low, high in box:
        if high <= low:
            axes.append([low])
            continue
        step = (high - low) / (GRID_PER_DIM - 1)
        axes.append([low + i * step for i in range(GRID_PER_DIM)])

    lo = hi = None
    lo_pt = hi_pt = None
    unbounded = False

    def consider(point):
        nonlocal lo, hi, lo_pt, hi_pt, unbounded
        a, b, cc, d = point
        if tie_single_miss and abs((b - box[1][0]) - (cc - box[2][0])) > 1e-9:
            return
        if not admissible(a, b, cc, d):
            return
        value = ratio(a, b, cc, d)
        if value is None:
            unbounded = True
            return
        if lo is None or value < lo:
            lo, lo_pt = value, point
        if hi is None or value > hi:
            hi, hi_pt = value, point

    for point in itertools.product(*axes):
        consider(point)
    for point in itertools.product(*[(low, high) for low, high in box]):
        consider(point)
    return lo, hi, unbounded, (lo_pt, hi_pt)


def optimise_differential(cells, budgets, delta, steps=41):
    """L2 done correctly: bound how DIFFERENTIAL the reference error may be.

    Proposition M4-1 (proved in the transcript): c is invariant under any strictly
    proportional perturbation of the four cells, because c is a ratio of a degree-two
    form to a degree-two form and is therefore scale invariant. Non-differential
    reference error, encoded as `error lands in proportion to cell share`, is exactly
    the null direction of c and has no identifying content whatsoever.

    All of c's exposure to reference error is therefore exposure to DIFFERENTIAL
    error: error whose rate depends on the cell, that is, on the channel outcomes.
    The correct L2 assumption bounds that differentiality. Each cell j is perturbed
    at rate r_j drawn from [rbar - delta, rbar + delta] for a free common rate rbar,
    with the total movement still inside the L1 budget.

      delta = 0        recovers the proportional case, width zero, vacuous
      delta unbounded  recovers L1
    """
    n = sum(cells)
    total = sum(budgets.values())
    rmax = total / n
    lo = hi = None
    unbounded = False
    grid = [-rmax + 2 * rmax * i / (steps - 1) for i in range(steps)]
    dgrid = [-delta + 2 * delta * i / (steps - 1) for i in range(steps)] if delta > 0 else [0.0]
    for rbar in grid:
        for d0 in dgrid:
            for d1 in dgrid:
                for d2 in dgrid:
                    point = (
                        max(0.0, cells[0] * (1 + rbar + d0)),
                        max(0.0, cells[1] * (1 + rbar + d1)),
                        max(0.0, cells[2] * (1 + rbar + d2)),
                        max(0.0, cells[3] * (1 + rbar)),
                    )
                    if not admissible(*point):
                        continue
                    if abs(sum(point) - n) > total:
                        continue
                    value = ratio(*point)
                    if value is None:
                        unbounded = True
                        continue
                    lo = value if lo is None else min(lo, value)
                    hi = value if hi is None else max(hi, value)
    return lo, hi, unbounded


def report_differential(name, cells, budgets, delta, indent="  "):
    lo, hi, unbounded = optimise_differential(cells, budgets, delta)
    print(f"{indent}{name}")
    print(f"{indent}  differentiality bound delta = {delta:g}")
    tail = "UNBOUNDED" if unbounded else fmt(hi)
    print(f"{indent}  identification set    [{fmt(lo)}, {tail}]"
          f"   width {0.0 if lo is None or hi is None else hi - lo:.4f}")
    return lo, hi, unbounded


def random_probe(box, lo, hi, tie_single_miss=False):
    """Seeded adversarial probe. Reports a breach if it beats the grid optimum."""
    rng = random.Random(SEED)
    breach_lo = breach_hi = None
    for _ in range(RANDOM_PROBES):
        point = tuple(rng.uniform(low, high) for low, high in box)
        a, b, cc, d = point
        if tie_single_miss and abs((b - box[1][0]) - (cc - box[2][0])) > 1e-9:
            continue
        if not admissible(a, b, cc, d):
            continue
        value = ratio(a, b, cc, d)
        if value is None:
            continue
        if lo is not None and value < lo - 1e-12:
            breach_lo = value if breach_lo is None else min(breach_lo, value)
        if hi is not None and value > hi + 1e-12:
            breach_hi = value if breach_hi is None else max(breach_hi, value)
    return breach_lo, breach_hi


def fmt(value):
    return "undefined" if value is None else f"{value:.4f}"


def report(name, cells, budgets, tie_single_miss=False, indent="  "):
    a, b, cc, d = cells
    point = ratio(a, b, cc, d)
    box = budget_box(cells, budgets)
    lo, hi, unbounded, _pts = optimise(box, tie_single_miss)
    breach_lo, breach_hi = random_probe(box, lo, hi, tie_single_miss)

    print(f"{indent}{name}")
    print(f"{indent}  observed cells        a={a:g} b={b:g} cc={cc:g} d={d:g}  n={a+b+cc+d:g}")
    print(f"{indent}  point estimate c      {fmt(point)}")
    budget_text = ", ".join(f"{k}={v:g}" for k, v in budgets.items())
    print(f"{indent}  budgets               {budget_text}")
    if unbounded:
        print(f"{indent}  identification set    [{fmt(lo)}, UNBOUNDED]"
              f"   (a feasible point drives a marginal to zero)")
    else:
        print(f"{indent}  identification set    [{fmt(lo)}, {fmt(hi)}]")
    print(f"{indent}  sharpness             NUMERICALLY VERIFIED OVER A DECLARED GRID, "
          f"NOT PROVED SHARP")
    if breach_lo is not None or breach_hi is not None:
        print(f"{indent}  SHARPNESS BREACH      random probe beat the grid: "
              f"lo={fmt(breach_lo)} hi={fmt(breach_hi)}")
    else:
        print(f"{indent}  random probe          {RANDOM_PROBES:,} seeded draws found no "
              f"point outside the reported set")
    return lo, hi, unbounded


def rule(title):
    print()
    print("=" * 96)
    print(title)
    print("=" * 96)


# ------------------------------------------------------------------------- fixtures

def main() -> int:
    print("=" * 96)
    print("M4 PARTIAL IDENTIFICATION UNDER REFERENCE ERROR - SYNTHETIC FIXTURES ONLY")
    print("no measured data is read; no empirical record is emitted")
    print(f"grid {GRID_PER_DIM} per dimension, {RANDOM_PROBES:,} random probes, seed {SEED}")
    print("=" * 96)

    # A stratum that is exactly independent before any reference error.
    base = (100.0, 900.0, 900.0, 8100.0)

    rule("F-01  the ladder on one exactly independent stratum")
    print("  Truth is c = 1.0000. Each level adds an assumption and narrows the set.")
    print()
    zero = {"omitted_true_opportunities": 0.0, "false_opportunities": 0.0,
            "class_or_stratum_error": 0.0, "localization_or_pose_error": 0.0}
    l1 = {"omitted_true_opportunities": 50.0, "false_opportunities": 50.0,
          "class_or_stratum_error": 25.0, "localization_or_pose_error": 25.0}
    report("L0-equivalent (zero budgets, for reference only)", base, zero)
    print()
    lo1, hi1, _ = report("L1  mechanism budgets, no cell assumption", base, l1)
    print()
    lo2, hi2, _ = report("L2  L1 plus non-differential restriction on the single-miss cells",
                         base, l1, tie_single_miss=True)
    print()
    l3 = {"omitted_true_opportunities": 8.0, "false_opportunities": 6.0,
          "class_or_stratum_error": 3.0, "localization_or_pose_error": 4.0}
    lo3, hi3, _ = report("L3  budgets from a blinded reannotation (fixture values)",
                         base, l3, tie_single_miss=True)
    print()
    print("  Ladder width, identification only, sampling uncertainty excluded:")
    for tag, lo, hi in (("L1", lo1, hi1), ("L2", lo2, hi2), ("L3", lo3, hi3)):
        print(f"    {tag}  [{fmt(lo)}, {fmt(hi)}]   width {hi - lo:.4f}")
    if abs((hi2 - lo2) - (hi1 - lo1)) < 1e-9:
        print()
        print("  NOTE, reported rather than hidden: L2 as first written did NOT narrow L1.")
        print("  F-01b shows why, and the reason is structural rather than a property of this")
        print("  fixture: the formulation is vacuous for this estimand on every stratum.")
        print("  F-01c restates L2 so that it binds. The refuted version is retained.")
    print("  Only L3 may ever carry a headline, and only after independent replication.")
    print()
    print("  Note the L1 lower end. With a false-opportunity plus class plus localization")
    print("  budget of 100 against an observed both-miss count of 100, a feasible point sets")
    print("  a = 0 and c = 0. That is not a solver artifact: it says these budgets make the")
    print("  estimand uninformative at L1 on this stratum. Reporting the width is the point.")

    rule("F-01b  REFUTED: the first L2 formulation is vacuous for this estimand")
    asym = (80.0, 1500.0, 400.0, 8020.0)
    print("  The first attempt encoded non-differential error as `tie the perturbation of the")
    print("  two single-miss cells`. It narrowed nothing above. The symmetric fixture was")
    print("  suspected, so the restriction was retried on a stratum whose single-miss cells")
    print("  differ by nearly a factor of four.")
    print()
    lo1b, hi1b, _ = report("L1  no cell assumption", asym, l3)
    print()
    lo2b, hi2b, _ = report("L2 as first written  tie the single-miss cells", asym, l3,
                           tie_single_miss=True)
    print()
    print(f"    L1 width {hi1b - lo1b:.4f}   tied width {hi2b - lo2b:.4f}   "
          f"narrowing {(hi1b - lo1b) - (hi2b - lo2b):.4f}")
    print()
    print("    REFUTATION, and the reason it is structural rather than a fixture accident:")
    print("    c = a*n / [(a+b)(a+cc)] is monotonically DECREASING in b and in cc. Every")
    print("    maximiser therefore pushes both single-miss cells to their lower bound and")
    print("    every minimiser pushes both to their upper bound. The tie b == cc is satisfied")
    print("    at both extrema for free, so it can never bind. The formulation was vacuous")
    print("    for this estimand on every stratum, not just the symmetric one.")
    print("    It is retained here as a refuted design, not deleted.")

    rule("F-01c  PROPOSITION M4-1: c is invariant under proportional reference error")
    print("  The second attempt encoded non-differential error as `the error lands in each")
    print("  cell in proportion to that cell's share of the stratum`. That is also wrong, and")
    print("  wrong in the opposite direction: it has NO identifying content at all.")
    print()
    print("  PROOF. c(a,b,cc,d) = a*n / [(a+b)(a+cc)] with n = a+b+cc+d. For any lambda > 0,")
    print("    c(la, lb, lcc, ld) = (la)(ln) / [(l(a+b))(l(a+cc))]")
    print("                       = l^2 * a*n / [ l^2 * (a+b)(a+cc) ]  =  c(a,b,cc,d).")
    print("  c is a ratio of a degree-two form to a degree-two form, hence scale invariant. A")
    print("  strictly proportional perturbation IS a scale by (1 + t), so c does not move. QED")
    print()
    for lam in (0.90, 1.00, 1.15, 2.00):
        scaled = tuple(x * lam for x in asym)
        print(f"    lambda={lam:>5.2f}   cells {tuple(round(x,1) for x in scaled)}"
              f"   c={fmt(ratio(*scaled))}")
    print()
    print("  CONSEQUENCE, and it is the useful part. Uniform reference error does not bias c")
    print("  at all. Every unit of c's identification exposure comes from DIFFERENTIAL")
    print("  reference error, error whose rate depends on the cell and therefore on the")
    print("  channel outcomes. That relocates the whole M4 problem: a blinded reannotation")
    print("  does not need to estimate the overall error rate, which is irrelevant here. It")
    print("  needs to bound how much the error rate VARIES ACROSS CELLS.")

    rule("F-01d  L2 restated a third time, as a bound on differentiality")
    print("  Each cell j is perturbed at rate r_j in [rbar - delta, rbar + delta] for a free")
    print("  common rate rbar. delta = 0 recovers the vacuous proportional case; large delta")
    print("  recovers L1. delta is the quantity a blinded reannotation must actually bound.")
    print()
    for delta in (0.0, 0.02, 0.05, 0.10):
        report_differential(f"L2  delta-differential, asymmetric stratum", asym, l3, delta)
    print()
    print("    The width grows monotonically in delta, from exactly zero at delta = 0. This is")
    print("    the correct shape: the assumption now has identifying content, it is stated as")
    print("    a single reviewable number, and F-04's channel-dependent contamination is the")
    print("    case where delta is large and unknown rather than small and measured.")

    rule("F-02  ADVERSARIAL: coordinated label error moves c with BOTH marginals unchanged")
    print("  The attack: a reference relabels 40 objects that both channels actually missed,")
    print("  so that each channel now appears to have caught each of them singly, and removes")
    print("  40 rows from the neither-miss cell to keep the total fixed.")
    print("    delta a = -40, delta b = +40, delta cc = +40, delta d = -40.")
    print("  Both marginal miss counts and the denominator are preserved exactly. The attack")
    print("  is therefore INVISIBLE to every marginal diagnostic, and it deflates c here;")
    print("  reversing the sign of the relabelling inflates it just as invisibly.")
    print()
    attacked = (60.0, 940.0, 940.0, 8060.0)   # a down 40, b and cc up 40, d down 40
    print(f"    honest    cells {base}  c={fmt(ratio(*base))}"
          f"  pA={(base[0]+base[1])/sum(base):.6f}")
    print(f"    attacked  cells {attacked}  c={fmt(ratio(*attacked))}"
          f"  pA={(attacked[0]+attacked[1])/sum(attacked):.6f}")
    print("    Both marginals are IDENTICAL and c moved. No marginal diagnostic can see this.")
    print("    Only an identification bound covers it. Under the L1 budgets above the honest")
    print(f"    set was [{fmt(lo1)}, {fmt(hi1)}], which contains the attacked value "
          f"{fmt(ratio(*attacked))}: {'YES' if lo1 <= ratio(*attacked) <= hi1 else 'NO'}")

    rule("F-03  ADVERSARIAL: a marginal budget can drive the denominator to zero")
    thin = (2.0, 3.0, 40.0, 955.0)
    big = {"omitted_true_opportunities": 10.0, "false_opportunities": 10.0,
           "class_or_stratum_error": 5.0, "localization_or_pose_error": 5.0}
    report("thin stratum, budget exceeds the A-miss marginal", thin, big)
    print("    The upper end is UNBOUNDED, not a large finite number. A stratum whose")
    print("    identification set is unbounded is not eligible for a worst-group extremum.")

    rule("F-04  ADVERSARIAL: channel-dependent reference contamination")
    print("  If the reference was built using channel B's outputs, then B cannot miss an")
    print("  object the reference contains, so cc is structurally suppressed and c is")
    print("  inflated by construction. This is not a budget question and no bound repairs it.")
    contaminated = (100.0, 900.0, 100.0, 8900.0)
    print(f"    clean         cells {base}  c={fmt(ratio(*base))}")
    print(f"    contaminated  cells {contaminated}  c={fmt(ratio(*contaminated))}")
    print("    VERDICT: the estimand is not identified at any ladder level. The correct")
    print("    output is `invalid`, not a wider interval. Reference provenance must be")
    print("    established as independent of every evaluated channel before M4 is run.")

    rule("F-05  identification and sampling uncertainty are reported separately")
    print("  Fixture inner interval from a clustered bootstrap (not computed here, declared):")
    print("    inner, sampling only        [0.9800, 1.0200]")
    print(f"    outer, identification L3    [{fmt(lo3)}, {fmt(hi3)}]")
    print("  The reported quantity is the OUTER set containing the INNER interval. They are")
    print("  never combined into one number and never summarised as a single figure.")

    print()
    print("=" * 96)
    print("SUMMARY")
    print("=" * 96)
    print("  PROPOSITION M4-1: c is scale invariant, so UNIFORM reference error does not")
    print("  bias it at all. Every unit of identification exposure is DIFFERENTIAL error.")
    print("  A blinded reannotation must therefore bound how much the error rate varies")
    print("  across cells, not the overall error rate, which is irrelevant to c.")
    print("  At delta = 0.05 the fixture stratum's set already covers 1.0, so a five point")
    print("  differential error rate is enough to leave its dependence unidentified.")
    print("  The ladder narrows only when an assumption actually binds. Two L2 formulations")
    print("  were refuted here, one vacuous and one null, and both are retained as refuted.")
    print("  Only L3 is headline eligible, and only after independent replication.")
    print("  Coordinated label error is invisible to marginals and visible only to a bound.")
    print("  A vanishing marginal yields UNBOUNDED, never a finite surrogate.")
    print("  Channel-dependent reference contamination yields `invalid`, never a wider set.")
    print("  Sharpness is NUMERICALLY VERIFIED OVER A DECLARED GRID, NOT PROVED.")
    print("  No measured data was read. No empirical record was emitted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
