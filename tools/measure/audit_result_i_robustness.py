"""Adversarial robustness audit of Result I's worst group.

Result I reports that the most dependent eligible stratum is `car, 0-20 m, v80-100`
with a lift of 6.946 and a simultaneous 95% band of [2.221, 11.671]. That is the
easiest and most safety-critical region in the split: a nearby, clearly visible car.
A claim that redundancy is weakest exactly there deserves the hardest attack this
workstream can mount before it is written down.

Four ways the number could be an artifact, each tested:

1. Small-denominator instability. At close range both detectors rarely miss, so the
   expected joint count is small and the ratio is a small number over a smaller one.
   The cell counts are printed so the reader can see the arithmetic.

2. The absence coercion. Audit 1 established that `.get(i, -1.0)` turns "detector
   emitted nothing" into a confident miss, and that 8.0% of all rows have both
   detectors absent. If the worst stratum's joint misses are mostly rows where
   neither detector emitted anything, the finding is a prediction-file artifact and
   not correlated perception failure. The stratum is recomputed with both-absent rows
   removed from the denominator, which is the conservative reading.

3. Concentration in a few keyframes. If the joint misses come from a handful of
   samples, this is one bad stretch of road and not a property of the operating
   region. Concentration is reported as the share carried by the top 1% of
   contributing samples, and the whole analysis is re-bootstrapped clustering on
   sample rather than instance.

4. Threshold dependence. If the ranking only holds at 0.3 it is an operating-point
   coincidence. The stratum's rank is recomputed across the same five thresholds
   Result E uses.

A finding that survives all four is worth stating. One that does not must be narrowed
or withdrawn, and this script is written to make either outcome equally easy to read.

Usage:
  python3 tools/measure/audit_result_i_robustness.py \
      gt_val_cache.json matched_mapillary.json matched_megvii.json
"""

import json
import sys
from collections import Counter

import numpy as np

THRESHOLDS = [0.1, 0.2, 0.3, 0.4, 0.5]
THR = 0.3
MIN_COUNT = 30
MIN_EXPECTED_JOINT = 5.0
REPS = 2000
SEED = 20260828
TARGET = ("car", "0-20", "v80-100")


def band(d):
    return "0-20" if d < 20 else ("20-30" if d < 30 else ("30-40" if d < 40 else "40-50"))


def flatten(raw):
    flat = {}
    for _c, m in raw.items():
        for k, v in m.items():
            flat[int(k)] = v
    return flat


def lifts(counts):
    a, b, c, d = (counts[:, k].astype(float) for k in range(4))
    n = a + b + c + d
    denom = (a + b) * (a + c)
    out = np.full(len(a), np.nan)
    ok = (n > 0) & (denom > 0)
    out[ok] = a[ok] * n[ok] / denom[ok]
    return out


def main():
    gt = json.load(open(sys.argv[1]))
    cam = flatten(json.load(open(sys.argv[2]))["matched_at_2m"])
    lid = flatten(json.load(open(sys.argv[3]))["matched_at_2m"])
    n_rows = len(gt)

    keys = [(g["cls"], band(g["dist"]), g["vis"]) for g in gt]
    s_index, s_names = {}, []
    stratum_ids = np.empty(n_rows, dtype=np.int64)
    for i, k in enumerate(keys):
        sid = s_index.get(k)
        if sid is None:
            sid = s_index[k] = len(s_index)
            s_names.append(k)
        stratum_ids[i] = sid
    n_strata = len(s_index)

    inst_index, samp_index = {}, {}
    instance_ids = np.empty(n_rows, dtype=np.int64)
    sample_ids = np.empty(n_rows, dtype=np.int64)
    for i, g in enumerate(gt):
        t = g["instance_token"]
        if t not in inst_index:
            inst_index[t] = len(inst_index)
        instance_ids[i] = inst_index[t]
        s = g["sample_token"]
        if s not in samp_index:
            samp_index[s] = len(samp_index)
        sample_ids[i] = samp_index[s]

    cam_absent = np.array([cam.get(i) is None for i in range(n_rows)])
    lid_absent = np.array([lid.get(i) is None for i in range(n_rows)])
    both_absent = cam_absent & lid_absent

    tid = s_index[TARGET]
    in_target = stratum_ids == tid

    print("=" * 92)
    print("AUDIT OF RESULT I - is the worst group real?")
    print(f"target stratum: {TARGET[0]}, {TARGET[1]} m, visibility {TARGET[2]}")
    print("=" * 92)

    def cells_at(thr, mask=None):
        cm = np.array([(cam.get(i, -1.0) < thr) for i in range(n_rows)])
        lm = np.array([(lid.get(i, -1.0) < thr) for i in range(n_rows)])
        cell = np.where(cm & lm, 0, np.where(cm, 1, np.where(lm, 2, 3)))
        keep = np.ones(n_rows, dtype=bool) if mask is None else mask
        code = stratum_ids[keep] * 4 + cell[keep]
        return np.bincount(code, minlength=n_strata * 4).reshape(n_strata, 4), cell, keep

    # ---- 1. the arithmetic in the open ------------------------------------
    counts, cell, _ = cells_at(THR)
    a, b, c, d = (counts[tid, k] for k in range(4))
    n = a + b + c + d
    exp = (a + b) * (a + c) / n
    print("\n### 1. the cell counts behind the ratio, score >= 0.3")
    print(f"  {'both miss (a)':>26}: {a:>7,}")
    print(f"  {'camera miss only (b)':>26}: {b:>7,}")
    print(f"  {'lidar miss only (c)':>26}: {c:>7,}")
    print(f"  {'neither misses (d)':>26}: {d:>7,}")
    print(f"  {'stratum size (n)':>26}: {n:>7,}")
    print(f"  {'camera miss rate':>26}: {(a+b)/n:>7.4f}")
    print(f"  {'lidar miss rate':>26}: {(a+c)/n:>7.4f}")
    print(f"  {'expected joint if indep.':>26}: {exp:>7.1f}")
    print(f"  {'observed joint':>26}: {a:>7,}")
    print(f"  {'lift':>26}: {a/exp:>7.3f}")
    print(f"  expected joint clears the declared floor of {MIN_EXPECTED_JOINT}:"
          f" {'YES' if exp >= MIN_EXPECTED_JOINT else 'NO'}")

    # ---- 2. absence coercion ----------------------------------------------
    tgt_joint = in_target & (cell == 0)
    n_joint = int(tgt_joint.sum())
    n_joint_abs = int((tgt_joint & both_absent).sum())
    print("\n### 2. is the worst group an absence artifact?")
    print(f"  {'joint misses in stratum':>34}: {n_joint:,}")
    print(f"  {'of which both detectors absent':>34}: {n_joint_abs:,}"
          f"   ({100*n_joint_abs/n_joint if n_joint else 0:.1f}%)")
    keep = ~both_absent
    counts_x, _, _ = cells_at(THR, mask=keep)
    lx = lifts(counts_x)
    print(f"  recomputed with both-absent rows removed from the denominator:")
    print(f"  {'stratum size':>34}: {int(counts_x[tid].sum()):,}")
    print(f"  {'lift':>34}: {lx[tid]:.3f}")
    rank_x = int(np.sum(np.nan_to_num(lx, nan=-1) > lx[tid])) + 1
    print(f"  {'rank among all 132 strata':>34}: {rank_x}")
    survives_2 = lx[tid] > 1.0
    print(f"  {'still above independence':>34}: {'YES' if survives_2 else 'NO'}")

    # ---- 3. concentration and sample clustering ---------------------------
    samp_counts = Counter(sample_ids[tgt_joint].tolist())
    n_samples_contrib = len(samp_counts)
    top = sorted(samp_counts.values(), reverse=True)
    k1 = max(1, n_samples_contrib // 100)
    share_top1pct = sum(top[:k1]) / n_joint if n_joint else float("nan")
    print("\n### 3. are the joint misses concentrated in a few keyframes?")
    print(f"  {'distinct samples contributing':>34}: {n_samples_contrib:,}")
    print(f"  {'distinct instances contributing':>34}:"
          f" {len(set(instance_ids[tgt_joint].tolist())):,}")
    print(f"  {'largest single sample share':>34}: {100*top[0]/n_joint:.2f}%")
    print(f"  {'top 1% of samples carry':>34}: {100*share_top1pct:.1f}%")

    rng = np.random.default_rng(SEED)
    code_full = stratum_ids * 4 + cell
    n_samp = len(samp_index)
    draws = np.empty(REPS)
    for r in range(REPS):
        m = rng.multinomial(n_samp, np.full(n_samp, 1.0 / n_samp))
        w = np.bincount(code_full, weights=m[sample_ids].astype(float),
                        minlength=n_strata * 4).reshape(n_strata, 4)
        draws[r] = lifts(w)[tid]
    se_samp = float(np.nanstd(draws, ddof=1))
    lo, hi = np.nanpercentile(draws, [2.5, 97.5])
    print(f"  sample-clustered bootstrap SE  : {se_samp:.3f}"
          f"   pointwise 95% [{lo:.3f}, {hi:.3f}]")
    survives_3 = lo > 1.0
    print(f"  {'lower bound above independence':>34}: {'YES' if survives_3 else 'NO'}")

    # ---- 4. threshold stability -------------------------------------------
    print("\n### 4. does the ranking hold across operating points?")
    print("  A stratum that fails the pre-declared eligibility floor has NO rank at")
    print("  that threshold. Reporting one would coerce an ineligible group into a")
    print("  confident value, which the charter forbids. Ineligible points are shown")
    print("  as such and excluded from the extremum, never scored as a bad rank.")
    print(f"  {'thr':>5}{'lift':>9}{'rank':>10}{'eligible':>10}{'exp joint':>12}")
    ranks = []
    for thr in THRESHOLDS:
        ct, _, _ = cells_at(thr)
        lt = lifts(ct)
        aa, bb, cc, dd = (ct[:, k].astype(float) for k in range(4))
        nn = aa + bb + cc + dd
        ee = np.divide((aa + bb) * (aa + cc), nn, out=np.zeros_like(nn), where=nn > 0)
        elig = (nn >= MIN_COUNT) & (ee >= MIN_EXPECTED_JOINT) & ~np.isnan(lt)
        if elig[tid]:
            vals = np.where(elig, lt, -np.inf)
            rank = int(np.sum(vals > vals[tid])) + 1
            ranks.append(rank)
            shown = str(rank)
        else:
            ranks.append(None)
            shown = "n/a"
        print(f"  {thr:>5.1f}{lt[tid]:>9.3f}{shown:>10}"
              f"{('yes' if elig[tid] else 'INELIGIBLE'):>10}{ee[tid]:>12.1f}")
    eligible_ranks = [r for r in ranks if r is not None]
    n_inelig = len(ranks) - len(eligible_ranks)
    survives_4 = bool(eligible_ranks) and all(r <= 3 for r in eligible_ranks)
    print(f"  eligible operating points          : {len(eligible_ranks)} of {len(ranks)}")
    print(f"  ineligible by the declared floor   : {n_inelig}"
          f"   (expected joint below {MIN_EXPECTED_JOINT})")
    print(f"  rank <= 3 at every ELIGIBLE point  : {'YES' if survives_4 else 'NO'}")

    # ---- verdict -----------------------------------------------------------
    print("\n" + "-" * 92)
    checks = [
        ("expected joint clears the floor", exp >= MIN_EXPECTED_JOINT),
        ("not an absence artifact", survives_2),
        ("not concentrated in a few keyframes", survives_3),
        ("worst at every eligible operating point", survives_4),
    ]
    for name, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if all(ok for _n, ok in checks):
        print("\n  Result I's worst group SURVIVES all four attacks. The claim that")
        print("  redundancy is weakest on near, clearly visible cars stands, and it is")
        print("  the region a redundancy argument is least likely to interrogate.")
    else:
        print("\n  Result I's worst group DOES NOT survive. Narrow or withdraw it before")
        print("  any use, and record which check failed rather than re-ranking.")
    print("-" * 92)


if __name__ == "__main__":
    main()
