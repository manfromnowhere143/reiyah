"""Result S: the corrected safety calculus, RSS Corollary 3 with the coefficient measured.

RSS (arXiv:1708.06374) argues direct statistical validation of a vehicle needs evidence on the
order of 1/P_e examples, infeasible for P_e ~ 1e-9. Corollary 3 escapes this with redundancy:
if a dangerous outcome needs BOTH subsystems to fail and they are c-approximately independent
(Definition 32), then P(both) <= 6 c p^2, so validating each subsystem to single-channel error
p = sqrt(P_e / (6 c)) suffices, and the required evidence is

    N(c, P_e) = 1 / p = sqrt( 6 c / P_e ).

The whole reduction turns on c, which RSS assumes near 1 and never estimates. Every figure below
uses the c we MEASURED on public detectors, fed back into RSS's own formula. Nothing here is a
certification; it is the honest correction to a published number.

Key facts carried in:
  - N scales as sqrt(c). A measured c inflates required evidence by sqrt(c) over independence.
  - The safety-relevant coefficient is the MARGINAL c (Result G): a deployed system integrates
    over the operating distribution and cannot condition, so P(both) = c_marginal P_A P_B.
  - c_marginal is operating-point dependent (Result P), so the correction is a range, not a point.
  - c_marginal is a LOWER bound (Result A): the benchmark deletes camera-only-visible objects
    before scoring, biasing the estimate toward independence.
  - RSS models only automation-automation redundancy. If a safety case additionally credits the
    HUMAN as a redundant channel (L2/L3), that redundancy carries its own measured dependence
    (H3, c ~ 1.46) which RSS does not correct at all. Credited layers compound.

Usage:
  python3 tools/measure/result_s_corrected_safety_calculus.py gt_val_cache.json \
      matched_mapillary.json matched_megvii.json
"""
import json
import math
import sys

THRESH = [0.1, 0.2, 0.3, 0.4, 0.5]
P_TARGET = 1e-9          # RSS's own worked-example target
RSS_CONST = 6.0          # the constant in P(both) <= 6 c p^2
C_HUMAN = 1.46           # measured human observation-response coefficient (Result H3)
LOWER_BOUND_NOTE = 0.03  # Result D: censoring inflates the official estimate ~3%; c is a floor


def flatten(raw):
    flat = {}
    for _c, m in raw.items():
        for k, v in m.items():
            flat[int(k)] = v
    return flat


def N(c, P=P_TARGET):
    return math.sqrt(RSS_CONST * c / P)


def main():
    gt = json.load(open(sys.argv[1]))
    cam = flatten(json.load(open(sys.argv[2]))["matched_at_2m"])
    lid = flatten(json.load(open(sys.argv[3]))["matched_at_2m"])
    n = len(gt)

    # marginal c per operating threshold: c = P(both miss) / (P_A P_B)
    marg = {}
    for thr in THRESH:
        a = [1 if cam.get(i, -1.0) < thr else 0 for i in range(n)]
        b = [1 if lid.get(i, -1.0) < thr else 0 for i in range(n)]
        pa = sum(a) / n
        pb = sum(b) / n
        pboth = sum(1 for i in range(n) if a[i] and b[i]) / n
        marg[thr] = pboth / (pa * pb) if pa * pb > 0 else float("nan")

    print("=" * 90)
    print("RESULT S - the corrected safety calculus (RSS Corollary 3 with c measured)")
    print(f"pair fixed by argv[3]={sys.argv[3]}; target P_e = {P_TARGET:.0e}")
    print("=" * 90)

    # 1. reproduce RSS's own claim as the self-check
    n_indep = N(1.0)
    print("\n### self-check: RSS's own worked example (c = 1) ###")
    print(f"  N(c=1, P_e=1e-9) = sqrt(6 / 1e-9) = {n_indep:,.0f}")
    print(f"  RSS states 'on the order of 10^5'. Reproduced: {n_indep:,.0f} ~ 10^5. OK")

    # 2. the corrected requirement, per operating point, from the MEASURED marginal c
    print("\n### automation redundancy (camera x lidar), evidence corrected by measured c ###")
    print(f"  {'score>=':>8}{'marginal c':>12}{'sqrt(c) infl':>14}"
          f"{'N corrected':>16}{'extra vs RSS':>16}")
    for thr in THRESH:
        c = marg[thr]
        infl = math.sqrt(c)
        nc = N(c)
        print(f"  {thr:>8.2f}{c:>12.3f}{infl:>14.3f}{nc:>16,.0f}{nc - n_indep:>16,.0f}")

    c03 = marg[0.3]
    print("\n### the headline number ###")
    print(f"  At a 0.30 operating point the measured marginal coefficient is {c03:.3f}.")
    print(f"  RSS's independence-based evidence figure is understated by a factor of")
    print(f"  sqrt({c03:.3f}) = {math.sqrt(c03):.3f}, i.e. at least {100*(math.sqrt(c03)-1):.0f}% more")
    print(f"  validation evidence is required than Corollary 3 claims, for this pair.")
    print(f"  This is a LOWER bound: the benchmark removes camera-only-visible objects before")
    print(f"  scoring (Result A), biasing the coefficient toward independence.")

    # 3. the human layer RSS ignores entirely
    print("\n### the human redundancy RSS does not model ###")
    print(f"  If the safety case credits the human as a redundant channel (L2/L3), that")
    print(f"  redundancy carries its own measured dependence c = {C_HUMAN} (Result H3),")
    print(f"  a further sqrt({C_HUMAN}) = {math.sqrt(C_HUMAN):.3f}x that RSS corrects by 0.")
    print(f"  Two credited redundancy layers compound: automation sqrt({c03:.3f}) times")
    print(f"  human sqrt({C_HUMAN}) = {math.sqrt(c03)*math.sqrt(C_HUMAN):.3f}x the RSS evidence figure.")

    # 4. effective independent channels, an interpretation
    pa = sum(1 for i in range(n) if cam.get(i, -1.0) < 0.3) / n
    pb = sum(1 for i in range(n) if lid.get(i, -1.0) < 0.3) / n
    p = math.sqrt(pa * pb)
    n_eff = 2 + math.log(c03) / math.log(p) if 0 < p < 1 else float("nan")
    print("\n### interpretation: effective number of independent channels ###")
    print(f"  Two channels with dependence c={c03:.3f} at miss rates ({pa:.2f}, {pb:.2f}) provide")
    print(f"  the joint-failure protection of {n_eff:.2f} truly-independent channels, not 2.")
    print(f"  You provisioned two sensors and received the redundancy of {n_eff:.2f}.")
    print(f"  (This quantity depends on the operating miss rate; stated as illustrative.)")

    print("\n" + "-" * 90)
    print("NON-CLAIMS: a correction to a published formula using coefficients measured on two")
    print("public detection outputs, retained as proposed. Not a certification, not a required")
    print("evidence figure for any real system, not a safety determination. RSS's constant 6 and")
    print("the sqrt(c) scaling are reproduced from the retained primary text; c is a lower bound.")


if __name__ == "__main__":
    main()
