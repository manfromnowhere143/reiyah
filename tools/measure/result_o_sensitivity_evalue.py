"""Result O: how strong would an unmeasured common cause have to be to explain the coupling?

Results L, M and N end on the same standing caveat, the honest one that every result in
this workstream declares and none has yet quantified: the residual camera-lidar dependence
is measured after the covariates nuScenes annotates, and an UNMEASURED common cause of both
failures could in principle produce it. Object size and truncation are the named examples;
occlusion beyond the coarse visibility bin is another.

A top team does not declare that and stop. It quantifies it. The standard instrument is the
E-value (VanderWeele and Ding, Annals of Internal Medicine, 2017): the minimum strength of
association, on the risk-ratio scale, that an unmeasured confounder would need with BOTH the
exposure and the outcome, beyond the measured covariates, to fully explain away an observed
conditional association. A large E-value means only an implausibly strong hidden factor could
account for the finding; a small one means a weak hidden factor could.

The framing fits this problem exactly. Take camera failure as the exposure and lidar failure
as the outcome. An unmeasured COMMON CAUSE of both - a latent shared difficulty the five
covariates do not capture - is precisely what the E-value bounds. So the E-value answers the
skeptic's actual objection: how much unmeasured shared difficulty would it take.

METHOD

For each score threshold and each detector pair, on the SAME L5 common support as Results L,
M and N (five admissible confounders, ground-truth-fixed 131,722-row population), compute the
Mantel-Haenszel conditional risk ratio of lidar-miss comparing camera-miss objects to
camera-hit objects:

  per stratum i, from the same 2x2 cells the coefficient uses:
    a = camera miss AND lidar miss      (exposed, outcome)
    b = camera miss AND lidar hit       (exposed, no outcome)
    c = camera hit  AND lidar miss      (unexposed, outcome)
    d = camera hit  AND lidar hit       (unexposed, no outcome)
  RR_MH = sum_i a_i (c_i + d_i) / n_i  /  sum_i c_i (a_i + b_i) / n_i     (Greenland-Robins)

The risk ratio is computed DIRECTLY from the cell counts, with no odds-ratio-to-risk-ratio
approximation, so the common-outcome caveat of the OR E-value does not apply. The
Mantel-Haenszel odds ratio is reported alongside only as a consistency anchor to Result E.

Uncertainty is the identical instance-clustered bootstrap (same seed, same replicate draws).
The E-value is reported for the point estimate and, as VanderWeele and Ding require for a
finding rather than a single number, for the confidence bound nearest the null:

  E(x) = x + sqrt(x * (x - 1))   for x >= 1 ;   E = 1 if the bound is at or below 1.

Usage:
  python3 tools/measure/result_o_sensitivity_evalue.py gt_val_cache.json \
      matched_mapillary.json matched_megvii.json
  python3 tools/measure/result_o_sensitivity_evalue.py gt_val_cache.json \
      matched_mapillary.json matched_pointpillars.json
"""

import json
import math
import sys

import numpy as np

THRESHOLDS = [0.1, 0.2, 0.3, 0.4, 0.5]
MIN_STRATUM = 30
REPS = 1500
SEED = 20260828
MOVING_MPS = 1.0


def band(d):
    return "0-20" if d < 20 else ("20-30" if d < 30 else ("30-40" if d < 40 else "40-50"))


def flatten(raw):
    flat = {}
    for _c, m in raw.items():
        for k, v in m.items():
            flat[int(k)] = v
    return flat


def rr_mh(counts, keep):
    """Mantel-Haenszel conditional risk ratio, exposure = camera miss, outcome = lidar miss."""
    a, b, c, d = (counts[:, k].astype(float) for k in range(4))
    n = a + b + c + d
    m = keep & (n > 0)
    num = (a[m] * (c[m] + d[m]) / n[m]).sum()
    den = (c[m] * (a[m] + b[m]) / n[m]).sum()
    return num / den if den > 0 else float("nan")


def or_mh(counts, keep):
    """Mantel-Haenszel odds ratio, reported only as a consistency anchor to Result E."""
    a, b, c, d = (counts[:, k].astype(float) for k in range(4))
    n = a + b + c + d
    m = keep & (n > 0)
    num = (a[m] * d[m] / n[m]).sum()
    den = (b[m] * c[m] / n[m]).sum()
    return num / den if den > 0 else float("nan")


def evalue(x):
    """VanderWeele and Ding E-value for a risk ratio x (uses 1/x reflection if x < 1)."""
    if not math.isfinite(x) or x <= 0:
        return float("nan")
    r = x if x >= 1 else 1.0 / x
    return r + math.sqrt(r * (r - 1.0))


def main():
    gt = json.load(open(sys.argv[1]))
    cam = flatten(json.load(open(sys.argv[2]))["matched_at_2m"])
    lid = flatten(json.load(open(sys.argv[3]))["matched_at_2m"])
    n_rows = len(gt)

    inst_index = {}
    instance_ids = np.empty(n_rows, dtype=np.int64)
    tracks = {}
    for i, g in enumerate(gt):
        t = g["instance_token"]
        if t not in inst_index:
            inst_index[t] = len(inst_index)
        instance_ids[i] = inst_index[t]
        tracks.setdefault(t, []).append((g["ts_us"], g["xy"]))
    n_inst = len(inst_index)

    motion = {}
    for t, pts in tracks.items():
        pts.sort()
        if len(pts) < 2:
            motion[t] = "unknown_motion"
            continue
        dt = (pts[-1][0] - pts[0][0]) / 1e6
        dd = math.dist(pts[0][1], pts[-1][1])
        motion[t] = "unknown_motion" if dt <= 0 else (
            "moving" if dd / dt >= MOVING_MPS else "static")

    # L5 five-confounder stratification, identical to Results L, M and N
    index = {}
    sids = np.empty(n_rows, dtype=np.int64)
    for i, g in enumerate(gt):
        k = (g["cls"], band(g["dist"]), g["vis"], g["cond"],
             motion[g["instance_token"]])
        if k not in index:
            index[k] = len(index)
        sids[i] = index[k]
    n_s = len(index)

    n_per = np.bincount(sids, minlength=n_s)
    keep = n_per >= MIN_STRATUM
    support = keep[sids]
    n_support = int(support.sum())

    rng = np.random.default_rng(SEED)
    mults = rng.multinomial(n_inst, np.full(n_inst, 1.0 / n_inst), size=REPS)
    rows_f = support.astype(float)

    def measures(thr):
        cm = np.array([cam.get(i, -1.0) < thr for i in range(n_rows)])
        lm = np.array([lid.get(i, -1.0) < thr for i in range(n_rows)])
        cell = np.where(cm & lm, 0, np.where(cm, 1, np.where(lm, 2, 3)))
        full_code = sids * 4 + cell
        counts = np.bincount(full_code[support],
                             minlength=n_s * 4).reshape(n_s, 4)
        kmask = counts.sum(axis=1) >= MIN_STRATUM
        rr = rr_mh(counts, kmask)
        orr = or_mh(counts, kmask)
        draws = np.empty(REPS)
        for r in range(REPS):
            w = mults[r][instance_ids].astype(float) * rows_f
            wc = np.bincount(full_code, weights=w,
                             minlength=n_s * 4).reshape(n_s, 4)
            draws[r] = rr_mh(wc, kmask)
        lo, hi = np.nanpercentile(draws, [2.5, 97.5])
        return rr, lo, hi, orr

    print("=" * 96)
    print("RESULT O - sensitivity of the conditional coupling to unmeasured confounding")
    print(f"pair fixed by argv[3]={sys.argv[3]}, nuScenes val, five admissible confounders,")
    print(f"instance-clustered bootstrap, {REPS:,} reps, seed {SEED}, common support {n_support:,} rows")
    print("E-value: minimum strength (risk-ratio scale) an unmeasured COMMON CAUSE of both")
    print("camera and lidar failure would need, beyond the five confounders, to explain the")
    print("coupling away. Reported for the point estimate and for the near-null CI bound.")
    print("=" * 96)
    print(f"\n  {'score>=':>7}{'cond. RR (lidar|cam)':>26}{'MH OR':>9}"
          f"{'E-value':>10}{'E-value(CI)':>13}")
    rows_out = []
    for thr in THRESHOLDS:
        rr, lo, hi, orr = measures(thr)
        ev = evalue(rr)
        ev_ci = evalue(lo) if lo > 1.0 else 1.0
        rows_out.append((thr, rr, lo, hi, orr, ev, ev_ci))
        rr_cell = f"{rr:.3f} [{lo:.3f}, {hi:.3f}]"
        print(f"  {thr:>7.2f}{rr_cell:>26}{orr:>9.3f}{ev:>10.3f}{ev_ci:>13.3f}")

    ref = next(r for r in rows_out if r[0] == 0.30)
    print("\n" + "-" * 96)
    print(f"At the score>=0.30 reference point the conditional risk ratio is {ref[1]:.3f}"
          f" [{ref[2]:.3f}, {ref[3]:.3f}].")
    print(f"Its E-value is {ref[5]:.2f}, and the E-value for the near-null 95% bound is"
          f" {ref[6]:.2f}.")
    print("Reading: an unmeasured common cause of camera failure and lidar failure would have")
    print(f"to be associated with EACH, on the risk-ratio scale and after class, range,")
    print(f"visibility, weather and motion, by a factor of at least {ref[5]:.2f} to move the")
    print("point estimate to independence, and by at least the CI figure to make the finding")
    print("compatible with independence at the 95% level. A hidden factor weaker than that on")
    print("either arm cannot account for the coupling; one at least that strong on both could.")
    print("The E-value falls as the threshold tightens, tracking the coupling's own")
    print("attenuation in Result N: the strictest operating points ask the least of a")
    print("confounder, and the loosest ask the most. This is a bound on plausibility, not a")
    print("test that any such confounder exists or is absent.")
    print("-" * 96)
    print("\nNON-CLAIMS: association after declared conditioning, not a causal effect; the")
    print("E-value bounds unmeasured confounding, it does not rule it in or out; bounded by")
    print("nuScenes-annotated covariates; two published detection outputs on one public split;")
    print("retained as proposed; no released 1.2 byte is modified.")


if __name__ == "__main__":
    main()
