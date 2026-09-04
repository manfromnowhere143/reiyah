"""Result N: does the conditional coefficient survive the score threshold, or is 0.3 lucky?

Results L and M report the conditional coefficient at score >= 0.3 only. A reviewer's
first cheap attack is that the threshold is arbitrary: pick a stricter one and the
residual dependence might evaporate, which would make the RSS Definition 32 objection an
artifact of one operating point.

Result D already answered this for the MARGINAL coefficient: it falls as the threshold
rises (2.271, 1.878, 1.587, 1.363, 1.239 at 0.1..0.5). That is expected and says nothing
about mechanism, because the marginal number is shared difficulty plus residual coupling
together. The open question is whether the CONDITIONAL coefficient - the one left after
class, range, visibility, weather and motion are stripped out, the one that actually
indicts independence - stays above 1.0 across the operating range.

This runs Results L and M's exact L5 machinery at each threshold and changes nothing else:
same five admissible confounders, same MIN_STRATUM floor, same instance-clustered
bootstrap, same seed, and the SAME common support - which is fixed by ground-truth stratum
counts and is therefore identical at every threshold, so only the miss definition varies
and never the population or the conditioning.

Reported at each threshold, on the fixed common support:
  marginal c (L0)      shared difficulty + residual coupling, for reference vs Result D
  conditional c (L5)   residual coupling after five admissible confounders - the test

Usage:
  python3 tools/measure/result_n_threshold_robustness.py gt_val_cache.json \
      matched_mapillary.json matched_megvii.json
  python3 tools/measure/result_n_threshold_robustness.py gt_val_cache.json \
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


def c_strat(counts, keep_mask):
    a, b, c, d = (counts[:, k].astype(float) for k in range(4))
    n = a + b + c + d
    m = keep_mask & (n > 0)
    if not np.any(m):
        return float("nan")
    obs = a[m].sum()
    exp = (((a[m] + b[m]) / n[m]) * ((a[m] + c[m]) / n[m]) * n[m]).sum()
    return obs / exp if exp > 0 else float("nan")


def main():
    gt = json.load(open(sys.argv[1]))
    cam = flatten(json.load(open(sys.argv[2]))["matched_at_2m"])
    lid = flatten(json.load(open(sys.argv[3]))["matched_at_2m"])
    n_rows = len(gt)

    # instance ids and motion state, from ground truth only - identical to Results L and M
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

    # L0 (marginal) and L5 (five admissible confounders) strata encodings - THR-independent
    def key_L0(g):
        return ("all",)

    def key_L5(g):
        return (g["cls"], band(g["dist"]), g["vis"], g["cond"],
                motion[g["instance_token"]])

    def encode(key_fn):
        index = {}
        ids = np.empty(n_rows, dtype=np.int64)
        for i, g in enumerate(gt):
            k = key_fn(g)
            if k not in index:
                index[k] = len(index)
            ids[i] = index[k]
        return ids, len(index)

    sids0, n_s0 = encode(key_L0)
    sids5, n_s5 = encode(key_L5)

    # common support: strata whose GROUND-TRUTH count clears the floor. This depends only
    # on stratum populations, not on any detector score, so it is the identical population
    # at every threshold - the point of the design.
    n_per5 = np.bincount(sids5, minlength=n_s5)
    keep5 = n_per5 >= MIN_STRATUM
    support = keep5[sids5]
    n_support = int(support.sum())

    rng = np.random.default_rng(SEED)
    mults = rng.multinomial(n_inst, np.full(n_inst, 1.0 / n_inst), size=REPS)
    rows_f = support.astype(float)

    def coeff(sids, n_s, cell):
        """point c and clustered-bootstrap 95% CI for one stratification, on the support."""
        full_code = sids * 4 + cell
        counts = np.bincount(full_code[support],
                             minlength=n_s * 4).reshape(n_s, 4)
        keep = counts.sum(axis=1) >= MIN_STRATUM
        point = c_strat(counts, keep)
        draws = np.empty(REPS)
        for r in range(REPS):
            w = mults[r][instance_ids].astype(float) * rows_f
            wc = np.bincount(full_code, weights=w,
                             minlength=n_s * 4).reshape(n_s, 4)
            draws[r] = c_strat(wc, keep)
        lo, hi = np.nanpercentile(draws, [2.5, 97.5])
        return point, lo, hi

    print("=" * 94)
    print("RESULT N - does the conditional coefficient survive the score threshold?")
    print(f"pair fixed by argv[3]={sys.argv[3]}, nuScenes val, instance-clustered"
          f" bootstrap, {REPS:,} reps, seed {SEED}")
    print(f"common support: {n_support:,} rows, fixed by ground-truth stratum counts,"
          f" identical at every threshold")
    print("=" * 94)
    print(f"\n  {'score >=':>9}{'marginal c (L0)':>26}{'conditional c (L5)':>30}"
          f"{'L5 excl 1.0':>13}")
    header_ci = "[lo, hi]"
    print(f"  {'':>9}{header_ci:>26}{header_ci:>30}")
    rows_out = []
    for thr in THRESHOLDS:
        cm = np.array([cam.get(i, -1.0) < thr for i in range(n_rows)])
        lm = np.array([lid.get(i, -1.0) < thr for i in range(n_rows)])
        cell = np.where(cm & lm, 0, np.where(cm, 1, np.where(lm, 2, 3)))
        c0, lo0, hi0 = coeff(sids0, n_s0, cell)
        c5, lo5, hi5 = coeff(sids5, n_s5, cell)
        excl = "YES" if lo5 > 1.0 else "NO"
        rows_out.append((thr, c0, lo0, hi0, c5, lo5, hi5, excl))
        m_cell = f"{c0:.3f} [{lo0:.3f}, {hi0:.3f}]"
        c_cell = f"{c5:.3f} [{lo5:.3f}, {hi5:.3f}]"
        print(f"  {thr:>9.2f}{m_cell:>26}{c_cell:>30}{excl:>13}")

    all_excl = all(r[7] == "YES" for r in rows_out)
    c5_vals = [r[4] for r in rows_out]
    print("\n" + "-" * 94)
    if all_excl:
        print("The conditional coefficient stays above independence at every threshold from")
        print(f"0.1 to 0.5. Range of terminal c: {min(c5_vals):.3f} to {max(c5_vals):.3f}.")
        print("The residual camera-lidar coupling is not an artifact of the 0.3 operating")
        print("point. Where the marginal coefficient falls with the threshold - shared")
        print("difficulty thinning out as only confident detections remain - the coupling")
        print("that survives conditioning does not fall to independence anywhere measured.")
    else:
        first_fail = next(r[0] for r in rows_out if r[7] == "NO")
        print("The conditional coefficient does NOT exclude independence at every threshold.")
        print(f"First threshold whose 95% interval includes 1.0: score >= {first_fail}.")
        print("This is an honest limit of the finding and is reported as measured: the")
        print("residual coupling is significant at operating thresholds below that point")
        print("and is not distinguishable from independence at or above it.")
    print("-" * 94)
    print("\nNON-CLAIMS: association after declared conditioning, not a causal effect;")
    print("bounded by nuScenes-annotated covariates; two published detection outputs on one")
    print("public split; retained as proposed; no released 1.2 byte is modified.")


if __name__ == "__main__":
    main()
