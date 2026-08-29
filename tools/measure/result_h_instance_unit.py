"""Result H restated at the instance unit, with the excluded detector removed.

Audit 1 required that "every interval and test statistic derived from Results D, G
and H must be restated at the instance unit before use". Result K paid that debt for
D and G. This pays it for H, and in doing so finds that H is smaller than published
for two reasons that have nothing to do with the unit.

WHAT CHANGES, AND WHY

1. CenterPoint is REMOVED. Result J excluded it for weak provenance: its prediction
   bytes come from a third-party mirror whose variant is unconfirmed, and its 61.59
   reconstruction was never validated against a confirmed published figure. Result H
   predates that decision and uses CenterPoint in three of its six pairs, including
   two of its three same-modality pairs. A detector excluded in one result cannot
   remain admitted in another. `matched_centerpoint.json` is also absent from this
   worktree, so the published Result H table is not reproducible here at all.

2. The unit becomes the tracked instance. Result H iterated over box rows and
   reported no interval of any kind. Audit 1 measured a design effect of 5.02 at the
   box unit, so box-level counts are not a sample size.

WHAT SURVIVES

Three admissible detectors give three pairs: one same-modality and two
cross-modality. One pair is not a replicated arm. The preregistration in
`docs/PREREGISTRATION_MODALITY_CONTRAST_0_1_0.md` section 5 requires each arm to
contain at least two pairs sharing no channel, and states that otherwise the result
is `inconclusive` by construction. That requirement is applied here to this result.

METHOD

The bootstrap is the one Result K uses: a multinomial resample over tracked
instances, with the SAME replicate weights applied to every pair so the difference
between arms keeps the correlation induced by shared data. Stratum eligibility is
fixed on the observed data before resampling, so the eligible set does not drift
between replicates.

Usage:
  python3 tools/measure/result_h_instance_unit.py gt_val_cache.json \
      mapillary=matched_mapillary.json megvii=matched_megvii.json \
      pointpillars=matched_pointpillars.json
"""

import json
import sys

import numpy as np

THR = 0.3
MIN_STRATUM = 30
REPS = 2000
SEED = 20260829
ALPHA = 0.05

MODALITY = {"mapillary": "camera", "megvii": "lidar", "pointpillars": "lidar"}
EXCLUDED = {"centerpoint": "weak provenance, excluded by Result J and not readmitted"}


def flatten(matched):
    out = {}
    for _cls, m in matched.items():
        for k, v in m.items():
            out[int(k)] = v
    return out


def band(d):
    return "0-20" if d < 20 else ("20-30" if d < 30 else ("30-40" if d < 40 else "40-50"))


def marginal_c(w, am, bm):
    n = w.sum()
    if n <= 0:
        return np.nan
    p_a = (w * am).sum() / n
    p_b = (w * bm).sum() / n
    p_j = (w * (am & bm)).sum() / n
    d = p_a * p_b
    return p_j / d if d > 0 else np.nan


def conditional_c(w, am, bm, strat, n_strata, eligible):
    ns = np.bincount(strat, weights=w, minlength=n_strata)
    a_s = np.bincount(strat, weights=w * am, minlength=n_strata)
    b_s = np.bincount(strat, weights=w * bm, minlength=n_strata)
    j_s = np.bincount(strat, weights=w * (am & bm), minlength=n_strata)
    safe = np.where(ns > 0, ns, 1.0)
    obs = j_s[eligible].sum()
    exp = (a_s[eligible] * b_s[eligible] / safe[eligible]).sum()
    return obs / exp if exp > 0 else np.nan


def ci(draws):
    return np.nanpercentile(draws, [100 * ALPHA / 2, 100 * (1 - ALPHA / 2)])


def main() -> int:
    gt = json.load(open(sys.argv[1]))
    det = {}
    for arg in sys.argv[2:]:
        name, path = arg.split("=", 1)
        det[name] = flatten(json.load(open(path))["matched_at_2m"])
    n_rows = len(gt)

    inst_index, instance_ids = {}, np.empty(n_rows, dtype=np.int64)
    strat_index, strat = {}, np.empty(n_rows, dtype=np.int64)
    for i, g in enumerate(gt):
        t = g["instance_token"]
        if t not in inst_index:
            inst_index[t] = len(inst_index)
        instance_ids[i] = inst_index[t]
        key = (g["cls"], band(g["dist"]), g["vis"])
        if key not in strat_index:
            strat_index[key] = len(strat_index)
        strat[i] = strat_index[key]
    n_inst, n_strata = len(inst_index), len(strat_index)

    counts = np.bincount(strat, minlength=n_strata)
    eligible = counts >= MIN_STRATUM

    print("=" * 96)
    print("RESULT H RESTATED - instance unit, CenterPoint removed")
    print(f"nuScenes val, score >= {THR}, instance-clustered bootstrap")
    print(f"{REPS:,} replicates, seed {SEED}, {n_inst:,} tracked objects, "
          f"{n_rows:,} boxes")
    print("=" * 96)
    print()
    print("EXCLUDED, carried forward from Result J and not readmitted:")
    for name, why in EXCLUDED.items():
        print(f"  {name:<16} {why}")
    print(f"  Admitted detectors: {', '.join(sorted(det))}")
    print(f"  Eligible strata (n >= {MIN_STRATUM}): {int(eligible.sum())} of {n_strata}")
    print()

    names = sorted(det)
    pairs = [(a, b) for i, a in enumerate(names) for b in names[i + 1:]]

    masks = {}
    for name in names:
        d = det[name]
        masks[name] = np.array([d.get(i, -1.0) < THR for i in range(n_rows)])

    rng = np.random.default_rng(SEED)
    mults = rng.multinomial(n_inst, np.full(n_inst, 1.0 / n_inst), size=REPS)

    base = np.ones(n_rows)
    point_m, point_c, draws_m, draws_c, kind = {}, {}, {}, {}, {}
    for a, b in pairs:
        am, bm = masks[a], masks[b]
        point_m[(a, b)] = marginal_c(base, am, bm)
        point_c[(a, b)] = conditional_c(base, am, bm, strat, n_strata, eligible)
        kind[(a, b)] = ("SAME modality" if MODALITY[a] == MODALITY[b]
                        else "cross-modality")
        dm = np.empty(REPS)
        dc = np.empty(REPS)
        for r in range(REPS):
            w = mults[r][instance_ids].astype(float)
            dm[r] = marginal_c(w, am, bm)
            dc[r] = conditional_c(w, am, bm, strat, n_strata, eligible)
        draws_m[(a, b)] = dm
        draws_c[(a, b)] = dc

    print(f"{'pair':<30}{'modalities':<18}{'marginal c':>11}"
          f"{'95% CI':>20}{'cond. c':>10}{'95% CI':>20}")
    for a, b in sorted(pairs, key=lambda p: -point_m[p]):
        lm, hm = ci(draws_m[(a, b)])
        lc, hc = ci(draws_c[(a, b)])
        print(f"{a + ' x ' + b:<30}{MODALITY[a] + '/' + MODALITY[b]:<18}"
              f"{point_m[(a, b)]:>11.3f}"
              f"{'[' + format(lm, '.3f') + ', ' + format(hm, '.3f') + ']':>20}"
              f"{point_c[(a, b)]:>10.3f}"
              f"{'[' + format(lc, '.3f') + ', ' + format(hc, '.3f') + ']':>20}"
              f"   {kind[(a, b)]}")

    same = [p for p in pairs if kind[p] == "SAME modality"]
    cross = [p for p in pairs if kind[p] == "cross-modality"]

    print()
    print("-" * 96)
    print(f"same-modality pairs : {len(same)}   {[f'{a} x {b}' for a, b in same]}")
    print(f"cross-modality pairs: {len(cross)}  {[f'{a} x {b}' for a, b in cross]}")
    print()

    for label, point, draws in (("marginal", point_m, draws_m),
                                ("conditional", point_c, draws_c)):
        s_pt = float(np.mean([point[p] for p in same]))
        c_pt = float(np.mean([point[p] for p in cross]))
        d_draws = np.array([
            np.mean([draws[p][r] for p in same]) - np.mean([draws[p][r] for p in cross])
            for r in range(REPS)
        ])
        lo, hi = ci(d_draws)
        excl = "EXCLUDES zero" if lo > 0 or hi < 0 else "INCLUDES zero"
        print(f"{label:<12} same mean {s_pt:.3f}   cross mean {c_pt:.3f}   "
              f"difference {s_pt - c_pt:+.3f}   95% CI [{lo:+.3f}, {hi:+.3f}]   {excl}")

    print()
    print("-" * 96)
    print("ARM REPLICATION CHECK, applied from the preregistration section 5")
    print("-" * 96)
    ok_same = len(same) >= 2
    ok_cross = len(cross) >= 2
    print(f"  same-modality arm  : {len(same)} pair(s)   "
          f"{'OK' if ok_same else 'FAILS the two-pair requirement'}")
    print(f"  cross-modality arm : {len(cross)} pair(s)  "
          f"{'OK' if ok_cross else 'FAILS the two-pair requirement'}")
    if not (ok_same and ok_cross):
        print()
        print("  VERDICT: INCONCLUSIVE by construction.")
        print("  The same-modality arm rests on a single pair, so its arm has no internal")
        print("  replication and its interval cannot separate a modality effect from a")
        print("  property of that one detector pair. The two cross-modality pairs also share")
        print("  Mapillary, so that arm has no independent replication either. Whatever the")
        print("  difference and its interval say, the design cannot support a supported or")
        print("  contradicted state. This is a design verdict fixed before the numbers were")
        print("  read, and it is not overturned by the numbers.")
    print()
    print("  What Result H claimed: same-modality and cross-modality 'separate completely'")
    print("  across six pairs and three lidar architectures. After removing an excluded")
    print("  detector, three pairs remain, two of the three same-modality pairs are gone,")
    print("  and the published claim's evidence base does not exist in this worktree.")
    print()
    print("NON-CLAIMS: no scientific support, no safety finding, no vendor comparison, no")
    print("operator acceptance. Observational, one split, no reference-error bound, and the")
    print("reference-error identification state remains unknown.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
