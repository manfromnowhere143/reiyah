"""Result R: does the coupling rise with detector accuracy, or is that just Result P?

Measured at a fixed operating threshold, the conditional coefficient rises with lidar
accuracy (camera x PointPillars 1.096, x Megvii 1.151, x CenterPoint 1.216). But Result P
showed c = P(both)/(P_A P_B) is deflated by the marginal miss rates, and a stronger detector
has a LOWER miss rate, which inflates c for arithmetic reasons alone. So the apparent
accuracy-coupling trend is confounded and must not be claimed until it is disentangled.

This disentangles it by comparing the lidars at a MATCHED marginal miss rate. For each lidar,
the script finds the score threshold that produces a chosen global miss rate P_B, holds the
camera fixed, and computes the L5 conditional coefficient there. If c still rises with the
detector's accuracy when every detector is set to the same miss rate, the effect is real; if
it flattens, the raw trend was the Result P marginal artifact.

Same L5 five-confounder stratification, same common support, same instance-clustered bootstrap.

Usage:
  python3 tools/measure/result_r_accuracy_coupling.py gt_val_cache.json matched_mapillary.json \
      matched_pointpillars.json matched_megvii.json matched_centerpoint.json
"""
import json
import math
import sys

import numpy as np

CAM_THR = 0.3
TARGET_PB = [0.40, 0.45, 0.50, 0.55]
MIN_STRATUM = 30
REPS = 1500
SEED = 20260828


def band(d):
    return "0-20" if d < 20 else ("20-30" if d < 30 else ("30-40" if d < 40 else "40-50"))


def flatten(raw):
    flat = {}
    for _c, m in raw.items():
        for k, v in m.items():
            flat[int(k)] = v
    return flat


def c_strat(counts, keep):
    a, b, c, d = (counts[:, k].astype(float) for k in range(4))
    n = a + b + c + d
    m = keep & (n > 0)
    if not np.any(m):
        return float("nan")
    obs = a[m].sum()
    exp = (((a[m] + b[m]) / n[m]) * ((a[m] + c[m]) / n[m]) * n[m]).sum()
    return obs / exp if exp > 0 else float("nan")


def main():
    gt = json.load(open(sys.argv[1]))
    cam = flatten(json.load(open(sys.argv[2]))["matched_at_2m"])
    lidars = {}
    for path in sys.argv[3:]:
        name = path.replace("matched_", "").replace(".json", "")
        lidars[name] = flatten(json.load(open(path))["matched_at_2m"])
    n = len(gt)

    inst_index = {}
    instance_ids = np.empty(n, dtype=np.int64)
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
            motion[t] = "unknown_motion"; continue
        dt = (pts[-1][0]-pts[0][0])/1e6; dd = math.dist(pts[0][1], pts[-1][1])
        motion[t] = "unknown_motion" if dt <= 0 else ("moving" if dd/dt >= 1.0 else "static")

    idx = {}; sid = np.empty(n, dtype=np.int64)
    for i, g in enumerate(gt):
        k = (g["cls"], band(g["dist"]), g["vis"], g["cond"], motion[g["instance_token"]])
        if k not in idx: idx[k] = len(idx)
        sid[i] = idx[k]
    n_s = len(idx)
    keep_support = np.bincount(sid, minlength=n_s) >= MIN_STRATUM
    support = keep_support[sid]

    rng = np.random.default_rng(SEED)
    mults = rng.multinomial(n_inst, np.full(n_inst, 1.0/n_inst), size=REPS)
    rows_f = support.astype(float)

    cm = np.array([cam.get(i, -1.0) < CAM_THR for i in range(n)])

    # per-lidar score array (missing detection -> -1 so it always counts as a miss)
    lid_scores = {name: np.array([d.get(i, -1.0) for i in range(n)]) for name, d in lidars.items()}

    def pb_at(scores, thr):
        return float((scores < thr).mean())

    def thr_for_pb(scores, target):
        # binary search the threshold giving global miss rate ~ target
        lo, hi = 0.0, 1.0
        for _ in range(40):
            mid = (lo+hi)/2
            if pb_at(scores, mid) < target:
                lo = mid
            else:
                hi = mid
        return (lo+hi)/2

    def cond_c(lm):
        cell = np.where(cm & lm, 0, np.where(cm, 1, np.where(lm, 2, 3)))
        full = sid*4 + cell
        counts = np.bincount(full[support], minlength=n_s*4).reshape(n_s, 4)
        kmask = counts.sum(axis=1) >= MIN_STRATUM
        point = c_strat(counts, kmask)
        draws = np.empty(REPS)
        for r in range(REPS):
            w = mults[r][instance_ids].astype(float)*rows_f
            wc = np.bincount(full, weights=w, minlength=n_s*4).reshape(n_s, 4)
            draws[r] = c_strat(wc, kmask)
        lo, hi = np.nanpercentile(draws, [2.5, 97.5])
        return point, lo, hi

    ACC = {"pointpillars": 29.5, "megvii": 51.9, "centerpoint": 57.4}
    order = sorted(lidars.keys(), key=lambda x: ACC.get(x, 0))

    print("=" * 92)
    print("RESULT R - conditional coupling vs detector accuracy, at MATCHED miss rate")
    print(f"camera fixed at score>={CAM_THR}; each lidar thresholded to a common miss rate P_B;")
    print(f"L5 five confounders; instance-clustered bootstrap {REPS} reps seed {SEED}")
    print("=" * 92)
    print("\nReference: c at each lidar's own default score>=0.3 (marginals NOT matched)")
    for name in order:
        lm = lid_scores[name] < 0.3
        pb = float(lm.mean()); pt, lo, hi = cond_c(lm)
        print(f"  {name:<13} acc {ACC.get(name,0):>4} mAP  P_B={pb:.3f}  c={pt:.3f} [{lo:.3f},{hi:.3f}]")

    for target in TARGET_PB:
        print(f"\nMatched miss rate P_B = {target:.2f}  (each lidar thresholded to this rate)")
        print(f"  {'lidar':<13}{'acc mAP':>8}{'thr used':>10}{'actual P_B':>12}"
              f"{'conditional c':>22}")
        for name in order:
            thr = thr_for_pb(lid_scores[name], target)
            lm = lid_scores[name] < thr
            pb = float(lm.mean()); pt, lo, hi = cond_c(lm)
            cell = f"{pt:.3f} [{lo:.3f}, {hi:.3f}]"
            print(f"  {name:<13}{ACC.get(name,0):>8}{thr:>10.3f}{pb:>12.3f}{cell:>22}")
    print("\n" + "-" * 92)
    print("If c rises with accuracy DOWN each matched-P_B block, the accuracy-coupling effect is")
    print("real and not the Result P marginal artifact. If it is flat, the raw trend was marginal.")
    print("Property of the estimand on public data; not a causal or safety determination.")


if __name__ == "__main__":
    main()
