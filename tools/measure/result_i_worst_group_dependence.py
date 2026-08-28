"""Result I: where is redundancy weakest? Worst-group dependence, done to our own contract.

Result E reports a pooled conditional lift of 1.156 at score >= 0.3. Pooling is exactly
what `docs/SCIENTIFIC_CHARTER.md` section 9.7 forbids as a final answer:

    "Every eligible group's denominator, epistemic-state counts, estimate, uncertainty,
     and validity must be reported. An empty, underpowered, missing, or invalid group
     must remain explicit; it cannot be dropped so that a different group becomes the
     reported worst group."

and `docs/MATHEMATICAL_SPECIFICATION.md` section 5.7 requires the universe to be
partitioned exactly into sufficient, observed-insufficient and unknown groups, with the
direction declared, all ties recorded, and any unknown group making the overall result
unknown.

A pooled lift of 1.156 is compatible with near-independence almost everywhere and severe
dependence in one operating region. For a redundancy argument only the second matters. If
camera and lidar fail together at 1.05x expected for easy near cars and 2x for distant
pedestrians, "1.156" is the wrong number to design against.

This is the first time the Reiyah worst-group contract is executed on measured data rather
than on a fixture.

## Declared before inspection

Direction. Larger lift is worse. Redundancy buys least where channels fail together most.

Estimand. Per stratum s, the within-stratum lift

    c_s = a_s * n_s / ((a_s + b_s) * (a_s + c_s))

with a = both miss, b = camera miss only, c = lidar miss only, n = stratum size. This is
the same quantity Result E pools, evaluated within a group instead of across groups.

Universe. Class x range band x annotated visibility, the identical stratification Result E
uses. The universe is fixed by that choice, not by what turns out to be interesting.

Eligibility, all three required and all fixed here before any stratum is ranked:
  1. n_s >= 30 ground-truth boxes, the MIN_STRATUM already used by Results E and H;
  2. expected joint misses >= 5, below which the ratio is not usefully estimable; and
  3. a finite simultaneous interval.

A stratum failing any criterion with every operand observed is `insufficient`. It stays
visible and is barred from the extremum. A stratum with a non-observed operand is
`unknown`; any unknown makes the overall result unknown. Here every count is observed, so
the unknown set is expected to be empty and the result identified. That is checked, not
assumed.

Uncertainty. Instance-clustered multinomial bootstrap, because Audit 1 established a design
effect of 5.02 at the box unit. Simultaneous coverage across all eligible strata by the
bootstrap max-t method, so the reported worst group is not a multiplicity artifact. A
per-stratum interval would be the wrong tool: we are selecting an extremum over 132
comparisons.

Usage:
  python3 tools/measure/result_i_worst_group_dependence.py \
      gt_val_cache.json matched_mapillary.json matched_megvii.json
"""

import json
import sys

import numpy as np

THR = 0.3
MIN_COUNT = 30
MIN_EXPECTED_JOINT = 5.0
REPS = 2000
SEED = 20260828
ALPHA = 0.05


def band(d):
    return "0-20" if d < 20 else ("20-30" if d < 30 else ("30-40" if d < 40 else "40-50"))


def flatten(raw):
    flat = {}
    for _c, m in raw.items():
        for k, v in m.items():
            flat[int(k)] = v
    return flat


def lifts(counts):
    """Per-stratum lift from an (S, 4) cell array. NaN where undefined."""
    a = counts[:, 0].astype(float)
    b = counts[:, 1].astype(float)
    c = counts[:, 2].astype(float)
    d = counts[:, 3].astype(float)
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

    stratum_ids = np.empty(n_rows, dtype=np.int64)
    instance_ids = np.empty(n_rows, dtype=np.int64)
    cells = np.empty(n_rows, dtype=np.int64)
    s_index, i_index, s_names = {}, {}, []

    for i, g in enumerate(gt):
        cm = cam.get(i, -1.0) < THR
        lm = lid.get(i, -1.0) < THR
        cells[i] = 0 if (cm and lm) else (1 if cm else (2 if lm else 3))

        key = (g["cls"], band(g["dist"]), g["vis"])
        sid = s_index.get(key)
        if sid is None:
            sid = s_index[key] = len(s_index)
            s_names.append(key)
        stratum_ids[i] = sid

        tok = g["instance_token"]
        iid = i_index.get(tok)
        if iid is None:
            iid = i_index[tok] = len(i_index)
        instance_ids[i] = iid

    n_strata, n_inst = len(s_index), len(i_index)
    code = stratum_ids * 4 + cells
    counts = np.bincount(code, minlength=n_strata * 4).reshape(n_strata, 4)

    a, b, c, d = (counts[:, k].astype(float) for k in range(4))
    n_s = a + b + c + d
    exp_joint = np.divide((a + b) * (a + c), n_s, out=np.zeros_like(n_s),
                          where=n_s > 0)
    point = lifts(counts)

    print("=" * 92)
    print("RESULT I - worst-group dependence: where does redundancy buy least?")
    print(f"mapillary x megvii, nuScenes val, score >= {THR}")
    print("direction declared before inspection: LARGER LIFT IS WORSE")
    print("=" * 92)

    # ---- bootstrap ---------------------------------------------------------
    rng = np.random.default_rng(SEED)
    draws = np.empty((REPS, n_strata))
    for r in range(REPS):
        m = rng.multinomial(n_inst, np.full(n_inst, 1.0 / n_inst))
        w = np.bincount(code, weights=m[instance_ids].astype(float),
                        minlength=n_strata * 4).reshape(n_strata, 4)
        draws[r] = lifts(w)

    se = np.nanstd(draws, axis=0, ddof=1)

    # ---- eligibility partition, declared criteria --------------------------
    observed = ~np.isnan(point) & (n_s > 0)
    unknown = ~observed
    finite_se = observed & np.isfinite(se) & (se > 0)
    sufficient = observed & (n_s >= MIN_COUNT) & (exp_joint >= MIN_EXPECTED_JOINT) & finite_se
    insufficient = observed & ~sufficient

    print("\n### universe partition, criteria fixed before ranking")
    print(f"  criteria: n_s >= {MIN_COUNT}, expected joint >= {MIN_EXPECTED_JOINT},"
          f" finite simultaneous interval")
    print(f"  {'strata in universe':>34}: {n_strata}")
    print(f"  {'sufficient':>34}: {int(sufficient.sum())}"
          f"   covering {int(n_s[sufficient].sum()):,} boxes")
    print(f"  {'observed-insufficient':>34}: {int(insufficient.sum())}"
          f"   covering {int(n_s[insufficient].sum()):,} boxes")
    print(f"  {'unknown':>34}: {int(unknown.sum())}")
    total = int(sufficient.sum() + insufficient.sum() + unknown.sum())
    print(f"  {'exact partition':>34}: {total} == {n_strata}"
          f"   {'OK' if total == n_strata else 'BROKEN'}")

    if unknown.any():
        print("\n  An unknown group is present. Per the mathematical specification the")
        print("  overall worst-group result is UNKNOWN and no extremum may be reported.")
        return

    if not sufficient.any():
        print("\n  disposition: no_eligible_groups")
        return

    # ---- simultaneous max-t band over eligible strata ----------------------
    idx = np.flatnonzero(sufficient)
    dev = np.abs(draws[:, idx] - point[idx]) / np.where(se[idx] > 0, se[idx], np.nan)
    maxt = np.nanmax(dev, axis=1)
    crit = float(np.nanpercentile(maxt, 100 * (1 - ALPHA)))
    lo = point[idx] - crit * se[idx]
    hi = point[idx] + crit * se[idx]

    print(f"\n### simultaneous {int((1-ALPHA)*100)}% band over"
          f" {len(idx)} eligible strata")
    print(f"  bootstrap max-t critical value : {crit:.3f}"
          f"   (a per-stratum z would be 1.96)")
    print(f"  multiplicity penalty           : {crit/1.96:.2f}x wider than a naive interval")

    # ---- the extremum, with ties -------------------------------------------
    order = idx[np.argsort(-point[idx])]
    worst_val = point[order[0]]
    ties = [j for j in idx if abs(point[j] - worst_val) < 1e-9]

    print("\n### ten most dependent eligible strata")
    print(f"  {'class':<26}{'range':>7}{'visibility':>12}{'n':>8}{'lift':>8}"
          f"{'simultaneous 95%':>22}")
    for j in order[:10]:
        cls, bnd, vis = s_names[j]
        k = int(np.flatnonzero(idx == j)[0])
        print(f"  {cls:<26}{bnd:>7}{vis:>12}{int(n_s[j]):>8,}{point[j]:>8.3f}"
              f"{'[' + format(lo[k], '.3f') + ', ' + format(hi[k], '.3f') + ']':>22}")

    print("\n### least dependent eligible strata, for contrast")
    for j in order[-3:]:
        cls, bnd, vis = s_names[j]
        k = int(np.flatnonzero(idx == j)[0])
        print(f"  {cls:<26}{bnd:>7}{vis:>12}{int(n_s[j]):>8,}{point[j]:>8.3f}"
              f"{'[' + format(lo[k], '.3f') + ', ' + format(hi[k], '.3f') + ']':>22}")

    if insufficient.any():
        print(f"\n### observed-insufficient strata, retained and barred from the extremum")
        ins = np.flatnonzero(insufficient)
        ins = ins[np.argsort(-np.nan_to_num(point[ins]))][:6]
        for j in ins:
            cls, bnd, vis = s_names[j]
            why = []
            if n_s[j] < MIN_COUNT:
                why.append(f"n={int(n_s[j])}<{MIN_COUNT}")
            if exp_joint[j] < MIN_EXPECTED_JOINT:
                why.append(f"exp_joint={exp_joint[j]:.1f}<{MIN_EXPECTED_JOINT}")
            pv = "undefined" if np.isnan(point[j]) else f"{point[j]:.3f}"
            print(f"  {cls:<26}{bnd:>7}{vis:>12}{int(n_s[j]):>8,}{pv:>8}"
                  f"   {', '.join(why)}")
        if int(insufficient.sum()) > 6:
            print(f"  ... and {int(insufficient.sum()) - 6} more, none eligible for the extremum")

    # ---- headline ----------------------------------------------------------
    kw = int(np.flatnonzero(idx == order[0])[0])
    pooled = float(counts[:, 0][n_s >= MIN_COUNT].sum() /
                   (exp_joint[n_s >= MIN_COUNT].sum()))
    cls, bnd, vis = s_names[order[0]]

    print("\n" + "-" * 92)
    print(f"Pooled conditional lift, Result E            : {pooled:.3f}")
    print(f"Worst eligible group lift                    : {worst_val:.3f}"
          f"   [{lo[kw]:.3f}, {hi[kw]:.3f}] simultaneous")
    print(f"Worst group                                  : {cls}, {bnd} m, visibility {vis}")
    print(f"Worst group size                             : {int(n_s[order[0]]):,} boxes")
    print(f"Ties at the extremum                         : {len(ties)}")
    print(f"Aggregate-to-worst gap                       : {worst_val - pooled:+.3f}"
          f"   ({100*(worst_val-1)/(pooled-1) if pooled > 1 else float('nan'):.0f}%"
          f" of the pooled excess over independence)")
    print("")
    if lo[kw] > 1.0:
        print("The worst eligible group's simultaneous lower bound exceeds 1.0, so its")
        print("dependence is not a multiplicity artifact of ranking 132 strata.")
    else:
        print("The worst eligible group's simultaneous lower bound does not exceed 1.0.")
        print("After honest multiplicity correction the extremum is not established.")
    print("")
    print("Consequence for a redundancy argument. Result G converts a lift into an")
    print("evidence requirement through N proportional to sqrt(c). Applied to the")
    print(f"pooled {pooled:.3f} that is {100*(pooled**0.5 - 1):.1f}% more evidence. Applied to the worst")
    print(f"eligible group it is {100*(worst_val**0.5 - 1):.1f}% more. A safety case that designs to the")
    print("pooled figure under-provisions exactly the region where the two channels")
    print("are least independent.")
    print("-" * 92)


if __name__ == "__main__":
    main()
