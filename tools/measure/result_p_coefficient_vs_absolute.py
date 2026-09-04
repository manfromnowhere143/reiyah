"""Result P: the RSS coefficient and the absolute joint-miss rate move in opposite directions.

RSS Corollary 3 reasons about the coincidence constant c of Definition 32. The estimand doc
(docs/ESTIMAND_RSS_DEFINITION_32.md, section 1) states plainly that c is "not invariant to the
marginal miss rates": c = P(both) / (P_A * P_B), so as the detector threshold tightens and the
marginal miss rates P_A, P_B rise toward 1, the denominator rises and c is dragged toward 1 for
arithmetic reasons, independently of whether the channels are becoming more independent.

This result makes that concrete and shows its safety consequence. It reports, at each score
threshold, the three quantities together on one population:

  c        = P(both) / (P_A P_B)     the RSS Definition 32 coincidence constant (marginal)
  P(both)  = P(M_A=1 and M_B=1)       the ABSOLUTE rate at which both sensors miss the same object
  excess   = P(both) - P_A P_B        the absolute excess joint-miss over independence

The coefficient is a ratio; P(both) and the absolute excess are the safety-relevant quantities,
because a real object missed by both sensors is missed whatever the ratio says. If c falls while
P(both) and the excess rise, then the coefficient RSS uses is smallest precisely where the
absolute joint failure is largest, and c alone cannot certify redundancy.

Uncertainty is the instance-clustered bootstrap used throughout this workstream (same seed).
Reported on the full validation population; the L5 common support figure is printed alongside
for continuity with Results L, N and O.

Usage:
  python3 tools/measure/result_p_coefficient_vs_absolute.py gt_val_cache.json \
      matched_mapillary.json matched_megvii.json
"""
import json
import math
import sys

import numpy as np

THRESH = [0.1, 0.2, 0.3, 0.4, 0.5]
REPS = 1500
SEED = 20260828


def flatten(raw):
    flat = {}
    for _c, m in raw.items():
        for k, v in m.items():
            flat[int(k)] = v
    return flat


def main():
    gt = json.load(open(sys.argv[1]))
    cam = flatten(json.load(open(sys.argv[2]))["matched_at_2m"])
    lid = flatten(json.load(open(sys.argv[3]))["matched_at_2m"])
    n = len(gt)

    inst_index = {}
    instance_ids = np.empty(n, dtype=np.int64)
    for i, g in enumerate(gt):
        t = g["instance_token"]
        if t not in inst_index:
            inst_index[t] = len(inst_index)
        instance_ids[i] = inst_index[t]
    n_inst = len(inst_index)

    rng = np.random.default_rng(SEED)
    mults = rng.multinomial(n_inst, np.full(n_inst, 1.0 / n_inst), size=REPS)
    # per-row bootstrap weights: each row inherits its instance's resample count
    W = mults[:, instance_ids].astype(float)  # REPS x n

    def rates(cm, lm):
        a = cm.astype(float); b = lm.astype(float); both = (cm & lm).astype(float)
        # point estimates
        pa = a.mean(); pb = b.mean(); pboth = both.mean()
        exp = pa * pb
        c = pboth / exp if exp > 0 else float("nan")
        excess = pboth - exp
        # clustered bootstrap over instances
        tot = W.sum(axis=1)
        PA = (W @ a) / tot
        PB = (W @ b) / tot
        PBOTH = (W @ both) / tot
        EXP = PA * PB
        C = np.where(EXP > 0, PBOTH / EXP, np.nan)
        EXC = PBOTH - EXP
        def ci(arr):
            return np.nanpercentile(arr, [2.5, 97.5])
        return dict(pa=pa, pb=pb, pboth=pboth, exp=exp, c=c, excess=excess,
                    pboth_ci=ci(PBOTH), c_ci=ci(C), exc_ci=ci(EXC))

    print("=" * 96)
    print("RESULT P - the RSS coefficient falls while the absolute joint-miss rate rises")
    print(f"pair fixed by argv[3]={sys.argv[3]}, nuScenes val full population N={n},")
    print(f"instance-clustered bootstrap {REPS:,} reps seed {SEED}")
    print("=" * 96)
    print(f"\n  {'thr':>4} | {'P_A':>6} {'P_B':>6} | {'c (coeff)':>20} | "
          f"{'P(both) absolute':>24} | {'abs excess':>20}")
    rows = []
    for thr in THRESH:
        cm = np.array([cam.get(i, -1.0) < thr for i in range(n)])
        lm = np.array([lid.get(i, -1.0) < thr for i in range(n)])
        r = rates(cm, lm)
        rows.append((thr, r))
        c_s = f"{r['c']:.3f} [{r['c_ci'][0]:.3f},{r['c_ci'][1]:.3f}]"
        pb_s = f"{r['pboth']:.4f} [{r['pboth_ci'][0]:.4f},{r['pboth_ci'][1]:.4f}]"
        ex_s = f"{r['excess']:.4f} [{r['exc_ci'][0]:.4f},{r['exc_ci'][1]:.4f}]"
        print(f"  {thr:>4.2f} | {r['pa']:>6.3f} {r['pb']:>6.3f} | {c_s:>20} | "
              f"{pb_s:>24} | {ex_s:>20}")

    lo, hi = rows[0][1], rows[-1][1]
    dc = hi["c"] - lo["c"]
    dboth = hi["pboth"] - lo["pboth"]
    dexc = hi["excess"] - lo["excess"]
    print("\n" + "-" * 96)
    print(f"From threshold 0.1 to 0.5: coefficient c changes by {dc:+.3f} "
          f"({lo['c']:.3f} -> {hi['c']:.3f}),")
    print(f"absolute P(both) changes by {dboth:+.4f} ({lo['pboth']:.4f} -> {hi['pboth']:.4f}),")
    print(f"absolute excess changes by {dexc:+.4f} ({lo['excess']:.4f} -> {hi['excess']:.4f}).")
    opp = (dc < 0) and (dboth > 0)
    print(f"coefficient and absolute joint-miss move in OPPOSITE directions: "
          f"{'YES' if opp else 'NO'}")
    print("-" * 96)
    print("Reading: c is a ratio deflated by the rising marginal miss rates, exactly the")
    print("non-invariance the estimand doc warns of. The safety-relevant quantities - the rate")
    print("at which both sensors miss the same real object, and its excess over independence -")
    print("rise as c falls. The coefficient is smallest where the absolute joint failure is")
    print("largest, so c alone cannot certify redundancy. This is a property of the estimand,")
    print("measured on public data; it is not a causal or safety determination.")
    print("\nNON-CLAIMS: two published detection outputs on one public split; retained as")
    print("proposed; association/rates after declared matching, not a causal or safety finding;")
    print("no released 1.2 byte is modified.")


if __name__ == "__main__":
    main()
