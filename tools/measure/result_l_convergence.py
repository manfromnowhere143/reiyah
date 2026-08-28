"""Result L: does the conditional coefficient converge, and to what?

The Gate B handoff names this the second open question. Result E's conditional lift
fell 1.525, 1.318, 1.156 as stratification deepened, "without obviously converging".
Everything downstream depends on where that sequence goes. If it converges to 1.0 the
dependence in Results D, E, I and J is shared difficulty and nothing more. If it
converges above 1.0 the two channels fail together beyond what their common inputs
explain, and RSS Definition 32's independence assumption fails on evidence.

## Two design problems the naive sequence has

**Mediators.** The handoff flags the trap: `num_lidar_pts` is arguably a mediator of
lidar failure rather than a confounder, so conditioning on it may delete the path being
measured. This script decides the question rather than leaving it open, and then
demonstrates the error deliberately so the size of it is on record.

A covariate is admissible here only if it is a common cause of both channels' failure
and is not itself produced by either detector:

  class            admissible; a property of the object
  range band       admissible; geometry, prior to both detectors
  visibility       admissible; nuScenes occlusion annotation, a cause of failure in
                   both channels, not an output of either detector
  weather/lighting admissible; `clear`, `rain`, `night` are scene conditions
  motion state     admissible; derived from the ground-truth track, not from any
                   detector output
  num_lidar_pts    NOT admissible; it is the lidar return itself. It sits on the causal
                   path from object to lidar failure. Conditioning on it blocks the very
                   path being measured and would drive the coefficient toward 1 for
                   mechanical reasons, not evidential ones.
  num_radar_pts    NOT admissible; neither detector consumes radar, but radar return
                   correlates strongly with lidar return, so conditioning on it partially
                   blocks the same path.

**Changing denominators.** Each added dimension multiplies the strata and pushes more
rows below the thin-stratum floor. A sequence computed on shrinking populations confounds
"conditioning removed association" with "the population changed". This script therefore
reports the sequence twice: as published, and on a common support fixed to the rows that
survive the deepest admissible level, so every level is estimated on the identical
population and only the conditioning varies.

Uncertainty is an instance-clustered bootstrap throughout, per Audit 1.

Usage:
  python3 tools/measure/result_l_convergence.py gt_val_cache.json \
      matched_mapillary.json matched_megvii.json
"""

import json
import math
import sys

import numpy as np

THR = 0.3
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

    # instance ids and derived motion state, from ground truth only
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

    cm = np.array([cam.get(i, -1.0) < THR for i in range(n_rows)])
    lm = np.array([lid.get(i, -1.0) < THR for i in range(n_rows)])
    cell = np.where(cm & lm, 0, np.where(cm, 1, np.where(lm, 2, 3)))

    LEVELS = [
        ("L0 none (marginal)", lambda g: ("all",)),
        ("L1 + class", lambda g: (g["cls"],)),
        ("L2 + range band", lambda g: (g["cls"], band(g["dist"]))),
        ("L3 + visibility", lambda g: (g["cls"], band(g["dist"]), g["vis"])),
        ("L4 + weather/lighting",
         lambda g: (g["cls"], band(g["dist"]), g["vis"], g["cond"])),
        ("L5 + motion state",
         lambda g: (g["cls"], band(g["dist"]), g["vis"], g["cond"],
                    motion[g["instance_token"]])),
    ]
    MEDIATOR = ("L6 + lidar point count (INADMISSIBLE)",
                lambda g: (g["cls"], band(g["dist"]), g["vis"], g["cond"],
                           motion[g["instance_token"]],
                           "0" if g["nl"] == 0 else ("1-5" if g["nl"] <= 5 else
                                                     ("6-20" if g["nl"] <= 20 else "20+"))))

    def encode(key_fn):
        index, ids = {}, np.empty(n_rows, dtype=np.int64)
        for i, g in enumerate(gt):
            k = key_fn(g)
            if k not in index:
                index[k] = len(index)
            ids[i] = index[k]
        return ids, len(index)

    rng = np.random.default_rng(SEED)
    mults = rng.multinomial(n_inst, np.full(n_inst, 1.0 / n_inst), size=REPS)

    def evaluate(key_fn, restrict=None):
        sids, n_s = encode(key_fn)
        rows = np.ones(n_rows, dtype=bool) if restrict is None else restrict
        code = sids[rows] * 4 + cell[rows]
        counts = np.bincount(code, minlength=n_s * 4).reshape(n_s, 4)
        n_per = counts.sum(axis=1)
        keep = n_per >= MIN_STRATUM
        point = c_strat(counts, keep)
        draws = np.empty(REPS)
        full_code = sids * 4 + cell
        for r in range(REPS):
            w = mults[r][instance_ids].astype(float) * rows
            wc = np.bincount(full_code, weights=w,
                             minlength=n_s * 4).reshape(n_s, 4)
            draws[r] = c_strat(wc, keep)
        lo, hi = np.nanpercentile(draws, [2.5, 97.5])
        return dict(c=point, lo=lo, hi=hi, strata=n_s,
                    used=int(n_per[keep].sum()), thin=int(n_per[~keep].sum()),
                    keep=keep, sids=sids)

    print("=" * 94)
    print("RESULT L - does the conditional coefficient converge, and to what?")
    print(f"mapillary x megvii, nuScenes val, score >= {THR}, instance-clustered"
          f" bootstrap, {REPS:,} reps")
    print("=" * 94)

    print("\n### sequence as published: cumulative conditioning, population varies")
    print(f"  {'level':<34}{'strata':>8}{'N used':>10}{'N thin':>8}"
          f"{'c':>8}{'95% CI':>20}")
    results = []
    for label, fn in LEVELS:
        r = evaluate(fn)
        results.append((label, r))
        print(f"  {label:<34}{r['strata']:>8}{r['used']:>10,}{r['thin']:>8,}"
              f"{r['c']:>8.3f}"
              f"{'[' + format(r['lo'], '.3f') + ', ' + format(r['hi'], '.3f') + ']':>20}")

    # ---- common support -----------------------------------------------------
    deepest_label, deepest_fn = LEVELS[-1]
    dr = results[-1][1]
    support = dr["keep"][dr["sids"]]
    print(f"\n### same sequence on a COMMON SUPPORT fixed by {deepest_label.strip()}")
    print(f"  every level below is estimated on the identical {int(support.sum()):,} rows,")
    print("  so a change in c is conditioning and not a change of population")
    print(f"  {'level':<34}{'strata':>8}{'N used':>10}{'N thin':>8}"
          f"{'c':>8}{'95% CI':>20}")
    cs_seq = []
    for label, fn in LEVELS:
        r = evaluate(fn, restrict=support)
        cs_seq.append((label, r))
        print(f"  {label:<34}{r['strata']:>8}{r['used']:>10,}{r['thin']:>8,}"
              f"{r['c']:>8.3f}"
              f"{'[' + format(r['lo'], '.3f') + ', ' + format(r['hi'], '.3f') + ']':>20}")

    # ---- convergence diagnosis ---------------------------------------------
    seq = [r["c"] for _l, r in cs_seq]
    steps = [seq[i] - seq[i - 1] for i in range(1, len(seq))]
    last = cs_seq[-1][1]
    print("\n### convergence diagnosis, on the common support")
    print(f"  sequence      : {', '.join(f'{v:.3f}' for v in seq)}")
    print(f"  step sizes    : {', '.join(f'{v:+.3f}' for v in steps)}")
    print(f"  final step    : {steps[-1]:+.4f}")
    print(f"  terminal c    : {last['c']:.3f}   95% CI"
          f" [{last['lo']:.3f}, {last['hi']:.3f}]")
    shrinking = all(abs(steps[i]) <= abs(steps[i - 1]) + 1e-9
                    for i in range(1, len(steps)))
    print(f"  steps monotonically shrinking in magnitude : "
          f"{'YES' if shrinking else 'NO'}")
    print(f"  terminal lower bound above 1.0             : "
          f"{'YES' if last['lo'] > 1.0 else 'NO'}")

    # ---- the mediator demonstration ----------------------------------------
    print("\n### the mediator error, performed deliberately")
    ml, mfn = MEDIATOR
    mr = evaluate(mfn, restrict=support)
    print(f"  {ml}")
    print(f"  strata {mr['strata']}, N used {mr['used']:,}, N thin {mr['thin']:,}")
    print(f"  c = {mr['c']:.3f}   95% CI [{mr['lo']:.3f}, {mr['hi']:.3f}]")
    print(f"  apparent extra shrinkage vs L5: {mr['c'] - last['c']:+.3f}")
    print("  This number is NOT a better estimate. `num_lidar_pts` is the lidar return")
    print("  itself, so conditioning on it blocks the path from object to lidar failure")
    print("  that the coefficient is measuring. The shrinkage is mechanical. It is")
    print("  recorded here so that anyone who reaches for this covariate can see what")
    print("  it does and why the number must not be used.")

    print("\n" + "-" * 94)
    if last["lo"] > 1.0:
        print(f"The conditional coefficient does not fall to independence. On a fixed")
        print(f"population with five admissible confounders it is {last['c']:.3f}, with a")
        print(f"cluster-robust 95% interval of [{last['lo']:.3f}, {last['hi']:.3f}] that excludes 1.0.")
        print("")
        print("Result E's open question is answered for the covariates available here:")
        print("shared observable difficulty explains most of the marginal association")
        print("and does not explain all of it. Camera and lidar fail together beyond")
        print("what class, range, visibility, weather and motion account for.")
    else:
        print("The conditional coefficient's interval includes 1.0 once the population")
        print("is held fixed. The dependence claim must be narrowed accordingly, and")
        print("Results D, E, I and J restated as shared difficulty until a design that")
        print("can separate them is available.")
    print("")
    print("This is bounded by the covariates nuScenes annotates. Unmeasured common")
    print("causes remain possible and no adjustment set here is claimed to be")
    print("sufficient for identification. The result is association after declared")
    print("conditioning, not a causal effect.")
    print("-" * 94)


if __name__ == "__main__":
    main()
