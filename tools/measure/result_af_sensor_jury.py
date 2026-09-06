"""Result AF: the sensor jury, in the LLM jury's own quantity.

Result T stated the LLM finding in one number: a seven-model jury has the effective diversity of
3.6 independent models, from the observed rate at which all models fail on the same item against
the rate independence predicts. The sensor arm of the law has never been stated in that quantity.
This does so for the four-detector jury on nuScenes val (two cameras, two lidars), per object, at
the program's 0.30 operating point, with an instance-clustered bootstrap band, and for every
sub-jury: the two cameras, the two lidars, each camera-lidar pair, and each triple.

  miss_m(o) = detector m has no match at or above 0.30 on annotated object o (validated matcher)
  P(all miss) observed / product of P(miss_m)  = inflation over independence
  n_eff = log P(all miss) / log(mean miss rate)   (the Result T definition, applied verbatim)
  c(i, j) for pairs, as everywhere in the program (marginal, at this operating point)

Also reported: the same quantities on the eligible objects only (any lidar or radar return), the
benchmark's own denominator. Seeded; re-runs byte-identically.
"""
import json
import sys
from collections import defaultdict
from itertools import combinations

import numpy as np

SCORE, SEED, B = 0.30, 20260906, 1000
GT = "gt_val_cache.json"
DET = {"Mapillary (camera)": "matched_mapillary.json", "FCOS3D (camera)": "matched_fcos3d.json",
       "Megvii (lidar)": "matched_megvii.json", "PointPillars (lidar)": "matched_pointpillars.json"}
KIND = {"Mapillary (camera)": "camera", "FCOS3D (camera)": "camera", "Megvii (lidar)": "lidar", "PointPillars (lidar)": "lidar"}


def load_matched(path):
    out = {}
    for cls, d in json.load(open(path))["matched_at_2m"].items():
        for gi, s in d.items():
            out[int(gi)] = float(s)
    return out


def stats(M, rows):
    """M: n x k miss matrix (bool). Returns inflation, n_eff, and pairwise c for rows."""
    W = M[rows]
    p = W.mean(axis=0)
    p_all = W.all(axis=1).mean()
    infl = p_all / np.prod(p) if np.prod(p) > 0 else np.nan
    n_eff = np.log(p_all) / np.log(p.mean()) if 0 < p_all and 0 < p.mean() < 1 else np.nan
    return infl, n_eff, p_all


def main():
    gt = json.load(open(GT))
    names = list(DET)
    matched = [load_matched(DET[n]) for n in names]
    n = len(gt)
    M = np.array([[matched[k].get(i, 0.0) < SCORE for k in range(len(names))] for i in range(n)])
    elig = np.array([(o["nl"] + o["nr"]) > 0 for o in gt])
    inst = np.array([o["instance_token"] for o in gt])
    groups = defaultdict(list)
    for i, t in enumerate(inst):
        groups[t].append(i)
    gkeys = list(groups)
    rng = np.random.RandomState(SEED)
    print("=" * 92)
    print("RESULT AF - the sensor jury in the LLM jury's quantity: effective independent channels")
    print(f"nuScenes val, {n} annotated objects ({elig.sum()} with any lidar or radar return), {len(gkeys)} tracked instances,")
    print(f"four detectors at score >= {SCORE}; instance-clustered bootstrap, B = {B}, seed {SEED}")
    print("=" * 92)
    print("\n  per-detector miss rate, all objects:")
    for k, nm in enumerate(names):
        print(f"    {nm:<24}{100*M[:, k].mean():>7.1f}%   (eligible only {100*M[elig, k].mean():.1f}%)")

    def boot(cols, mask):
        rows = np.where(mask)[0]
        sub = M[:, cols]
        point = stats(sub, rows)
        bs = []
        # resample tracked instances, then keep only the masked objects of each drawn instance, so
        # the bootstrap population equals the point-estimate population (an earlier draft kept whole
        # instances and the eligible-only band excluded its own point; recorded and corrected)
        inst_rows = {g: [i for i in groups[g] if mask[i]] for g in gkeys}
        keys_in = [g for g in gkeys if inst_rows[g]]
        for _ in range(B):
            pick = rng.choice(len(keys_in), len(keys_in), replace=True)
            idx = np.concatenate([inst_rows[keys_in[j]] for j in pick])
            bs.append(stats(sub, idx))
        bs = np.array(bs, dtype=float)
        lo, hi = np.nanpercentile(bs, [2.5, 97.5], axis=0)
        return point, lo, hi

    juries = [("full jury: 2 cameras + 2 lidars", [0, 1, 2, 3]),
              ("two cameras", [0, 1]), ("two lidars", [2, 3]),
              ("Mapillary x Megvii (camera x lidar)", [0, 2]), ("Mapillary x PointPillars", [0, 3]),
              ("FCOS3D x Megvii", [1, 2]), ("FCOS3D x PointPillars", [1, 3]),
              ("2 cameras + Megvii", [0, 1, 2]), ("2 cameras + PointPillars", [0, 1, 3]),
              ("Mapillary + 2 lidars", [0, 2, 3]), ("FCOS3D + 2 lidars", [1, 2, 3])]
    for label, mask in (("all annotated objects", np.ones(n, bool)), ("eligible objects only", elig)):
        print(f"\n  {label}:")
        print(f"    {'jury':<38}{'k':>3}{'P(all miss)':>13}{'inflation':>22}{'effective independent':>26}")
        for jl, cols in juries:
            (infl, neff, pall), (ilo, nlo, plo), (ihi, nhi, phi) = boot(cols, mask)
            print(f"    {jl:<38}{len(cols):>3}{100*pall:>12.1f}%{infl:>9.2f} [{ilo:.2f}, {ihi:.2f}]"
                  f"{neff:>10.2f} [{nlo:.2f}, {nhi:.2f}] of {len(cols)}")

    print("\n  reading against the LLM juries (Results T, W, Y): 7 models on MMLU 3.60 [3.53, 3.68] of 7;")
    print("  6 on ARC-Challenge 1.64 [1.57, 1.71] of 6; 7 on HellaSwag 1.28 [1.27, 1.30] of 7.")
    print("\n" + "-" * 92)
    print("NON-CLAIMS: released detector outputs on the public nuScenes validation split, marginal")
    print("coefficients at one operating point including shared scene difficulty, retained as proposed.")
    print("Miss is the validated matcher's absence of a match at 0.30; the two cameras and two lidars")
    print("were all trained on the nuScenes training split, a shared-data threat already on record.")
    print("Descriptive, not a safety determination, not a certificate about any deployed system. No")
    print("detector is executed. No released 1.2 byte is involved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
