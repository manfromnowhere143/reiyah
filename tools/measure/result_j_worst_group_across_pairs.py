"""Result J: is the worst group a property of one pair, or of the operating region?

Result I found that for `mapillary x megvii` the most dependent eligible stratum is
`car, 0-20 m, v80-100` at lift 6.946, against a pooled 1.156. One pair cannot tell us
whether that is a fact about those two detectors or a fact about that region of the
driving problem.

This runs the identical worst-group contract over every available detector pair. Three
detectors give three pairs, two crossing modality and one within it:

    mapillary   MonoDIS        camera   29.8 mAP published, 29.58 reproduced
    megvii      CBGS           lidar    51.9 mAP published, 51.97 reproduced
    pointpillars PointPillars  lidar    29.5 mAP published, 29.54 reproduced

CenterPoint is deliberately excluded. Its predictions come from a third-party mirror
that `docs/GATE_B_MEASUREMENT_CONTRACT.md` marks "explicitly weaker provenance", and its
accuracy figure is reconstructed and unconfirmed. Audit 2 withdrew a claim that leaned on
it. It is not readmitted here.

The question has a clean falsifier. If each pair's worst group is a different stratum,
the Result I finding is about a detector pair and should be stated that way. If the same
region is worst across pairs that share no modality, it is a property of the operating
region, and every redundancy argument that pools over regions is under-provisioned in the
same place regardless of which sensors are combined.

Everything is declared exactly as in Result I: larger lift is worse, the universe is
class x range band x visibility, eligibility is n >= 30 and expected joint >= 5 and a
finite simultaneous interval, uncertainty is an instance-clustered bootstrap, and
multiplicity is handled by a bootstrap max-t band across each pair's eligible strata.
Nothing is re-tuned per pair.

Usage:
  python3 tools/measure/result_j_worst_group_across_pairs.py gt_val_cache.json \
      mapillary=matched_mapillary.json megvii=matched_megvii.json \
      pointpillars=matched_pointpillars.json
"""

import json
import sys
from itertools import combinations

import numpy as np

THR = 0.3
MIN_COUNT = 30
MIN_EXPECTED_JOINT = 5.0
REPS = 2000
SEED = 20260828
ALPHA = 0.05

MODALITY = {"mapillary": "camera", "megvii": "lidar", "pointpillars": "lidar"}


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
    det = {}
    for arg in sys.argv[2:]:
        name, path = arg.split("=", 1)
        det[name] = flatten(json.load(open(path))["matched_at_2m"])
    n_rows = len(gt)

    s_index, s_names = {}, []
    stratum_ids = np.empty(n_rows, dtype=np.int64)
    inst_index = {}
    instance_ids = np.empty(n_rows, dtype=np.int64)
    for i, g in enumerate(gt):
        key = (g["cls"], band(g["dist"]), g["vis"])
        if key not in s_index:
            s_index[key] = len(s_index)
            s_names.append(key)
        stratum_ids[i] = s_index[key]
        tok = g["instance_token"]
        if tok not in inst_index:
            inst_index[tok] = len(inst_index)
        instance_ids[i] = inst_index[tok]
    n_strata, n_inst = len(s_index), len(inst_index)

    miss = {name: np.array([d.get(i, -1.0) < THR for i in range(n_rows)])
            for name, d in det.items()}

    print("=" * 96)
    print("RESULT J - is the worst group a property of the pair, or of the region?")
    print(f"nuScenes val, score >= {THR}, universe = class x range x visibility"
          f" ({n_strata} strata)")
    print("direction declared before inspection: LARGER LIFT IS WORSE")
    print("CenterPoint excluded: weaker provenance, unconfirmed accuracy")
    print("=" * 96)

    rng = np.random.default_rng(SEED)
    summary = []

    for a_name, b_name in combinations(sorted(det), 2):
        am, bm = miss[a_name], miss[b_name]
        cell = np.where(am & bm, 0, np.where(am, 1, np.where(bm, 2, 3)))
        code = stratum_ids * 4 + cell
        counts = np.bincount(code, minlength=n_strata * 4).reshape(n_strata, 4)
        a, b, c, d = (counts[:, k].astype(float) for k in range(4))
        n_s = a + b + c + d
        exp = np.divide((a + b) * (a + c), n_s, out=np.zeros_like(n_s), where=n_s > 0)
        point = lifts(counts)

        draws = np.empty((REPS, n_strata))
        for r in range(REPS):
            m = rng.multinomial(n_inst, np.full(n_inst, 1.0 / n_inst))
            w = np.bincount(code, weights=m[instance_ids].astype(float),
                            minlength=n_strata * 4).reshape(n_strata, 4)
            draws[r] = lifts(w)
        se = np.nanstd(draws, axis=0, ddof=1)

        observed = ~np.isnan(point) & (n_s > 0)
        unknown = int((~observed).sum())
        sufficient = (observed & (n_s >= MIN_COUNT) & (exp >= MIN_EXPECTED_JOINT)
                      & np.isfinite(se) & (se > 0))
        insufficient = int((observed & ~sufficient).sum())

        pooled_mask = n_s >= MIN_COUNT
        pooled = float(a[pooled_mask].sum() / exp[pooled_mask].sum())

        mods = f"{MODALITY[a_name]}/{MODALITY[b_name]}"
        kind = "SAME" if MODALITY[a_name] == MODALITY[b_name] else "cross"
        print(f"\n### {a_name} x {b_name}   [{mods}, {kind}-modality]")
        print(f"  partition: sufficient {int(sufficient.sum())},"
              f" insufficient {insufficient}, unknown {unknown}"
              f"   exact: {int(sufficient.sum()) + insufficient + unknown == n_strata}")

        if unknown:
            print("  An unknown group is present; the worst-group result is UNKNOWN.")
            continue
        if not sufficient.any():
            print("  disposition: no_eligible_groups")
            continue

        idx = np.flatnonzero(sufficient)
        dev = np.abs(draws[:, idx] - point[idx]) / np.where(se[idx] > 0, se[idx], np.nan)
        crit = float(np.nanpercentile(np.nanmax(dev, axis=1), 100 * (1 - ALPHA)))
        order = idx[np.argsort(-point[idx])]
        w = order[0]
        k = int(np.flatnonzero(idx == w)[0])
        lo = point[w] - crit * se[w]
        hi = point[w] + crit * se[w]
        ties = int(sum(1 for j in idx if abs(point[j] - point[w]) < 1e-9))

        print(f"  pooled lift over eligible strata : {pooled:.3f}")
        print(f"  {'worst group':>33}: {s_names[w][0]}, {s_names[w][1]} m,"
              f" {s_names[w][2]}")
        print(f"  {'worst group lift':>33}: {point[w]:.3f}"
              f"   simultaneous 95% [{lo:.3f}, {hi:.3f}]  (max-t {crit:.2f})")
        print(f"  {'worst group size':>33}: {int(n_s[w]):,} boxes,"
              f" {int(counts[w, 0]):,} joint misses, ties {ties}")
        print(f"  {'top three':>33}: " + " | ".join(
            f"{s_names[j][0]} {s_names[j][1]} {s_names[j][2]} {point[j]:.2f}"
            for j in order[:3]))
        print(f"  {'evidence cost, pooled vs worst':>33}:"
              f" {100*(pooled**0.5-1):.1f}% vs {100*(point[w]**0.5-1):.1f}%")
        summary.append((a_name, b_name, kind, pooled, s_names[w], point[w], lo, hi,
                        [s_names[j] for j in order[:3]]))

    # ---- cross-pair verdict ------------------------------------------------
    print("\n" + "=" * 96)
    print("### does the same region come worst across pairs?")
    print(f"  {'pair':<32}{'kind':>7}{'pooled':>9}{'worst lift':>12}   worst group")
    for a_name, b_name, kind, pooled, wname, wval, lo, hi, _top in summary:
        print(f"  {a_name + ' x ' + b_name:<32}{kind:>7}{pooled:>9.3f}{wval:>12.3f}"
              f"   {wname[0]}, {wname[1]} m, {wname[2]}")

    worst_names = [s[4] for s in summary]
    same_worst = len(set(worst_names)) == 1
    car_close = [s for s in summary
                 if s[4][0] == "car" and s[4][1] in ("0-20", "20-30")]
    top3_car_close = [
        s for s in summary
        if any(t[0] == "car" and t[1] in ("0-20", "20-30") for t in s[8])
    ]

    print("\n" + "-" * 96)
    print(f"  identical worst stratum in all {len(summary)} pairs : "
          f"{'YES' if same_worst else 'NO'}")
    print(f"  worst stratum is a close-range car          : "
          f"{len(car_close)} of {len(summary)} pairs")
    print(f"  a close-range car in the top three          : "
          f"{len(top3_car_close)} of {len(summary)} pairs")
    lows = [s[6] for s in summary]
    print(f"  every worst-group lower bound above 1.0     : "
          f"{'YES' if all(l > 1.0 for l in lows) else 'NO'}"
          f"   (min {min(lows):.3f})")

    print("")
    if len(car_close) == len(summary) and all(l > 1.0 for l in lows):
        print("  The worst region is not a property of one detector pair. It is the")
        print("  close-range car, for a camera/lidar pair and for a lidar/lidar pair")
        print("  alike, with every simultaneous lower bound above independence.")
        print("  A redundancy argument pooled over regions is under-provisioned in the")
        print("  same place no matter which sensors are combined.")
    elif len(top3_car_close) == len(summary):
        print("  The exact worst stratum differs by pair, but a close-range car is in")
        print("  the top three for every pair. The regional reading is supported; the")
        print("  single-stratum reading is not, and Result I must be stated as one")
        print("  pair's extremum within a consistently worst region.")
    else:
        print("  The worst stratum does not agree across pairs. Result I must be")
        print("  stated as a property of the mapillary x megvii pair only, and the")
        print("  regional claim is withdrawn.")
    print("-" * 96)


if __name__ == "__main__":
    main()
