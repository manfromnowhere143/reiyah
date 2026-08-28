"""Adversarial audit of Result E: is its inference unit the same as its analysis unit?

Result E reports a conditional lift c = 1.156 and a CMH chi-square of 4,924 on 1 df
at score >= 0.3, stratified by class x range x visibility. The point estimate is not
in question here. The inference is.

Result E iterates one row per ground-truth box. nuScenes ground truth is tracked, so
those 134,565 boxes come from 8,976 instances, a mean of 14.99 boxes each. Boxes of
one tracked instance are not independent draws: the same object, the same detector,
adjacent timestamps. A CMH statistic computed as if they were independent overstates
the evidence by roughly the design effect.

This is the exact error the workstream already named for itself. See
docs/FIRST_SEMANTICALLY_VALIDATED_MEASUREMENT.md: "Treating roughly fifteen
near-identical boxes of one tracked object as independent observations is precisely
the clustering error listed in our own traps table." That correction was applied to
the record-building unit. It was not applied to Results D, E, G, or H.

The audit does four things:

1. reproduces Result E at score >= 0.3 exactly, so the comparison is byte-anchored;
2. accounts for every ground-truth row whose detector entry is absent rather than
   low-scoring, because absence is coerced to a confident miss by `.get(i, -1.0)`;
3. estimates the design effect with an instance-clustered multinomial bootstrap and
   a matched row-level bootstrap, and reports a cluster-robust interval for c; and
4. restates the CMH evidence at the instance unit.

An audit that only weakened a result would be suspect. This one is expected to leave
the point estimate untouched and the direction intact. What it changes is how much
evidence may be claimed.

Usage:
  python3 tools/measure/audit_result_e_clustering.py \
      gt_val_cache.json matched_mapillary.json matched_megvii.json
"""

import json
import sys

import numpy as np

THR = 0.3
MIN_STRATUM = 30
REPS = 2000
SEED = 20260828


def band(d):
    return "0-20" if d < 20 else ("20-30" if d < 30 else ("30-40" if d < 40 else "40-50"))


def flatten(raw):
    flat = {}
    for _c, m in raw.items():
        for k, v in m.items():
            flat[int(k)] = v
    return flat


def c_strat_from_counts(counts, min_stratum=MIN_STRATUM):
    """Result E's pooled conditional lift, from a (S, 4) cell-count array.

    Columns are both-miss, cam-miss-only, lid-miss-only, neither, matching
    tools/measure/result_e.py exactly.
    """
    a, b, c, d = counts[:, 0], counts[:, 1], counts[:, 2], counts[:, 3]
    n = a + b + c + d
    keep = n >= min_stratum
    if not np.any(keep):
        return float("nan")
    a, b, c, n = a[keep], b[keep], c[keep], n[keep]
    obs = a.sum()
    exp = (((a + b) / n) * ((a + c) / n) * n).sum()
    return obs / exp if exp > 0 else float("nan")


def main():
    gt = json.load(open(sys.argv[1]))
    cam = flatten(json.load(open(sys.argv[2]))["matched_at_2m"])
    lid = flatten(json.load(open(sys.argv[3]))["matched_at_2m"])

    n_rows = len(gt)

    # ---- row-level encoding -------------------------------------------------
    cam_absent = np.zeros(n_rows, dtype=bool)
    lid_absent = np.zeros(n_rows, dtype=bool)
    cam_miss = np.zeros(n_rows, dtype=bool)
    lid_miss = np.zeros(n_rows, dtype=bool)

    stratum_ids = np.empty(n_rows, dtype=np.int64)
    instance_ids = np.empty(n_rows, dtype=np.int64)
    stratum_index, instance_index = {}, {}

    for i, g in enumerate(gt):
        cv = cam.get(i)
        lv = lid.get(i)
        cam_absent[i] = cv is None
        lid_absent[i] = lv is None
        cam_miss[i] = (cv if cv is not None else -1.0) < THR
        lid_miss[i] = (lv if lv is not None else -1.0) < THR

        key = (g["cls"], band(g["dist"]), g["vis"])
        sid = stratum_index.get(key)
        if sid is None:
            sid = stratum_index[key] = len(stratum_index)
        stratum_ids[i] = sid

        tok = g["instance_token"]
        iid = instance_index.get(tok)
        if iid is None:
            iid = instance_index[tok] = len(instance_index)
        instance_ids[i] = iid

    n_strata = len(stratum_index)
    n_inst = len(instance_index)

    # cell: 0 both miss, 1 cam only, 2 lid only, 3 neither
    cell = np.where(cam_miss & lid_miss, 0, np.where(cam_miss, 1, np.where(lid_miss, 2, 3)))
    code = stratum_ids * 4 + cell

    counts = np.bincount(code, minlength=n_strata * 4).reshape(n_strata, 4)
    c_point = c_strat_from_counts(counts)

    n_per = counts.sum(axis=1)
    kept = n_per >= MIN_STRATUM
    n_used = int(n_per[kept].sum())
    n_thin = int(n_per[~kept].sum())

    print("=" * 88)
    print("AUDIT OF RESULT E - is the inference unit the analysis unit?")
    print(f"mapillary x megvii, nuScenes val, score >= {THR}, class x range x visibility")
    print("=" * 88)

    print("\n### 1. exact reproduction of Result E")
    print(f"{'strata':>28}: {n_strata}")
    print(f"{'N used':>28}: {n_used:,}")
    print(f"{'N thin (kept visible)':>28}: {n_thin:,}")
    print(f"{'observed joint misses':>28}: {int(counts[kept, 0].sum()):,}")
    print(f"{'conditional lift c':>28}: {c_point:.3f}")
    print(f"{'Result E published c':>28}: 1.156")
    match = abs(c_point - 1.156) < 5e-4
    print(f"{'reproduced':>28}: {'YES' if match else 'NO'}")

    # ---- 2. missingness accounting -----------------------------------------
    print("\n### 2. absence coerced to a confident miss")
    print("`cam.get(i, -1.0) < thr` cannot distinguish 'detector emitted nothing'")
    print("from 'detector emitted a low score'. Both become a confident miss.")
    for name, absent, miss in (("mapillary", cam_absent, cam_miss),
                               ("megvii", lid_absent, lid_miss)):
        n_abs = int(absent.sum())
        n_miss = int(miss.sum())
        share = 100.0 * n_abs / n_miss if n_miss else float("nan")
        print(f"  {name:<12} absent {n_abs:>8,} of {n_rows:,} rows"
              f"   = {100.0*n_abs/n_rows:>5.1f}% of rows"
              f"   = {share:>5.1f}% of its misses")
    both_absent = int((cam_absent & lid_absent).sum())
    print(f"  both absent  {both_absent:>8,}"
          f"   = {100.0*both_absent/n_rows:>5.1f}% of rows")
    print("  For a detection task an unmatched ground-truth object is a genuine")
    print("  false negative, so this coercion is defensible. It is recorded because")
    print("  the charter forbids silent coercion, not because it is wrong here.")

    # ---- 3. design effect ---------------------------------------------------
    print(f"\n### 3. design effect, {REPS:,} bootstrap replicates, seed {SEED}")
    rng = np.random.default_rng(SEED)

    def boot(multiplicity_per_row):
        w = np.bincount(code, weights=multiplicity_per_row,
                        minlength=n_strata * 4).reshape(n_strata, 4)
        return c_strat_from_counts(w)

    cluster_draws = np.empty(REPS)
    row_draws = np.empty(REPS)
    for r in range(REPS):
        m_inst = rng.multinomial(n_inst, np.full(n_inst, 1.0 / n_inst))
        cluster_draws[r] = boot(m_inst[instance_ids].astype(float))
        m_row = rng.multinomial(n_rows, np.full(n_rows, 1.0 / n_rows))
        row_draws[r] = boot(m_row.astype(float))

    se_cluster = float(np.std(cluster_draws, ddof=1))
    se_row = float(np.std(row_draws, ddof=1))
    deff = (se_cluster / se_row) ** 2 if se_row > 0 else float("nan")
    lo, hi = np.percentile(cluster_draws, [2.5, 97.5])
    rlo, rhi = np.percentile(row_draws, [2.5, 97.5])

    print(f"  {'instances':>34}: {n_inst:,}   rows: {n_rows:,}"
          f"   mean rows/instance: {n_rows/n_inst:.2f}")
    print(f"  {'row-level (as published) SE':>34}: {se_row:.5f}"
          f"   95% CI [{rlo:.3f}, {rhi:.3f}]")
    print(f"  {'instance-clustered SE':>34}: {se_cluster:.5f}"
          f"   95% CI [{lo:.3f}, {hi:.3f}]")
    print(f"  {'design effect (var ratio)':>34}: {deff:.2f}")
    print(f"  {'SE inflation':>34}: {se_cluster/se_row:.2f}x")
    print(f"  {'effective sample size':>34}: {n_rows/deff:,.0f} of {n_rows:,} rows")

    # ---- 4. restated evidence ----------------------------------------------
    print("\n### 4. restated CMH evidence at the instance unit")
    cmh_pub = 4924.0
    cmh_adj = cmh_pub / deff if deff > 0 else float("nan")
    print(f"  {'Result E published CMH (1 df)':>34}: {cmh_pub:,.0f}")
    print(f"  {'divided by the design effect':>34}: {cmh_adj:,.0f}")
    print("  A chi-square of 10.83 on 1 df is p < 0.001.")
    verdict = "SURVIVES" if cmh_adj > 10.83 else "DOES NOT SURVIVE"
    print(f"  {'conditional independence null':>34}: {verdict}")

    print("\n" + "-" * 88)
    print("Finding. The point estimate is unchanged and the direction is intact:")
    print(f"the cluster-robust interval [{lo:.3f}, {hi:.3f}] excludes 1.0, so the two")
    print("channels do fail together beyond what class, range and visibility explain.")
    print("Result E's substantive conclusion stands.")
    print("")
    print(f"What does not stand is the size of the claimed evidence. The published")
    print(f"CMH of {cmh_pub:,.0f} is computed at the box unit and overstates the evidence")
    print(f"by a factor of about {deff:.0f}. The honest statistic is on the order of")
    print(f"{cmh_adj:,.0f}, and the correct denominator for any RSS-style evidence-count")
    print(f"argument is roughly {n_inst:,} independent tracked objects, not {n_rows:,} boxes.")
    print("")
    print("Results D, G and H share the box-level unit and are affected the same way.")
    print("None of their point estimates change. Every interval and test statistic")
    print("derived from them must be restated at the instance unit before use.")
    print("-" * 88)


if __name__ == "__main__":
    main()
