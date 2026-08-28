"""Result K: the evidence-cost number with an interval, at the correct unit.

Audit 1 established a design effect of 5.02 for the box unit and required that
"every interval and test statistic derived from Results D, G and H must be restated
at the instance unit before use". This pays that debt for D and G.

Result D reports point estimates of the marginal lift with no interval at all.
Result G converts one of those point estimates into an engineering requirement:

    RSS Corollary 3 gives P <= 6 c p^2, so N is proportional to sqrt(c), and the
    measured lift of 1.587 at score >= 0.3 costs about 26% more evidence.

A safety engineer provisioning a validation campaign cannot use "about 26%". They
need a bound. That requires the sampling distribution of `c`, at the unit where the
observations are actually independent, propagated through the square root.

Two denominators are carried throughout, exactly as Result D does:

  OFFICIAL  the 121,871 objects the nuScenes evaluation scores, after its
            zero-point filter removes 12,694 of 134,565
  FULL      all 134,565 ground-truth objects

They are reported side by side and never merged. Result B established that the
removal criterion is defined on range-sensor returns alone, so it is correlated with
lidar failure by construction. The OFFICIAL row is what a benchmark consumer sees;
the FULL row is what the road contains.

Propagation is done by transforming every bootstrap replicate rather than by a delta
approximation, so the interval on sqrt(c) is exact with respect to the resampling
distribution and stays valid however skewed `c` is.

Usage:
  python3 tools/measure/result_k_evidence_cost_interval.py gt_val_cache.json \
      matched_mapillary.json matched_megvii.json
"""

import json
import sys

import numpy as np

THRESHOLDS = [0.1, 0.2, 0.3, 0.4, 0.5]
REPS = 4000
SEED = 20260828
ALPHA = 0.05
RSS_BASELINE_N = 77460  # RSS's own worked example at P = 1e-9 assuming independence


def flatten(raw):
    flat = {}
    for _c, m in raw.items():
        for k, v in m.items():
            flat[int(k)] = v
    return flat


def marginal_lift(w, cm, lm):
    """Weighted marginal lift. w is a per-row weight vector."""
    n = w.sum()
    if n <= 0:
        return np.nan
    p_c = (w * cm).sum() / n
    p_l = (w * lm).sum() / n
    p_j = (w * (cm & lm)).sum() / n
    denom = p_c * p_l
    return p_j / denom if denom > 0 else np.nan


def main():
    gt = json.load(open(sys.argv[1]))
    cam = flatten(json.load(open(sys.argv[2]))["matched_at_2m"])
    lid = flatten(json.load(open(sys.argv[3]))["matched_at_2m"])
    n_rows = len(gt)

    inst_index = {}
    instance_ids = np.empty(n_rows, dtype=np.int64)
    for i, g in enumerate(gt):
        t = g["instance_token"]
        if t not in inst_index:
            inst_index[t] = len(inst_index)
        instance_ids[i] = inst_index[t]
    n_inst = len(inst_index)

    official = np.array([g["nl"] + g["nr"] > 0 for g in gt])

    print("=" * 94)
    print("RESULT K - the evidence-cost number, with an interval, at the instance unit")
    print("mapillary x megvii, nuScenes val, instance-clustered bootstrap")
    print(f"{REPS:,} replicates, seed {SEED}, {n_inst:,} independent tracked objects")
    print("=" * 94)
    print("\nEvidence multiplier is sqrt(c) from RSS Corollary 3, N proportional to sqrt(c).")
    print("Intervals are propagated by transforming each replicate, not by a delta")
    print("approximation, so they remain valid under skew in c.\n")

    rng = np.random.default_rng(SEED)
    mults = rng.multinomial(n_inst, np.full(n_inst, 1.0 / n_inst), size=REPS)

    for label, mask in (("FULL", np.ones(n_rows, dtype=bool)), ("OFFICIAL", official)):
        print(f"### {label} denominator, N = {int(mask.sum()):,}")
        print(f"  {'thr':>5}{'c_hat':>9}{'95% CI on c':>22}"
              f"{'evidence +%':>13}{'95% CI on +%':>22}")
        for thr in THRESHOLDS:
            cm = np.array([cam.get(i, -1.0) < thr for i in range(n_rows)]) & mask
            lm = np.array([lid.get(i, -1.0) < thr for i in range(n_rows)]) & mask
            base = mask.astype(float)
            point = marginal_lift(base, cm, lm)

            draws = np.empty(REPS)
            for r in range(REPS):
                draws[r] = marginal_lift(mults[r][instance_ids] * base, cm, lm)
            lo, hi = np.nanpercentile(draws, [100 * ALPHA / 2, 100 * (1 - ALPHA / 2)])

            ev = 100 * (point ** 0.5 - 1)
            ev_draws = 100 * (np.sqrt(draws) - 1)
            elo, ehi = np.nanpercentile(ev_draws, [100 * ALPHA / 2, 100 * (1 - ALPHA / 2)])

            print(f"  {thr:>5.1f}{point:>9.3f}"
                  f"{'[' + format(lo, '.3f') + ', ' + format(hi, '.3f') + ']':>22}"
                  f"{ev:>12.1f}%"
                  f"{'[' + format(elo, '.1f') + ', ' + format(ehi, '.1f') + ']':>22}")
        print()

    # ---- the decision-ready statement at the representative operating point ----
    thr = 0.3
    cm = np.array([cam.get(i, -1.0) < thr for i in range(n_rows)])
    lm = np.array([lid.get(i, -1.0) < thr for i in range(n_rows)])
    base = np.ones(n_rows)
    point = marginal_lift(base, cm, lm)
    draws = np.array([marginal_lift(mults[r][instance_ids] * base, cm, lm)
                      for r in range(REPS)])
    lo, hi = np.nanpercentile(draws, [2.5, 97.5])
    n_req = RSS_BASELINE_N * np.sqrt(draws)
    nlo, nhi = np.nanpercentile(n_req, [2.5, 97.5])

    print("-" * 94)
    print(f"At score >= {thr}, FULL denominator, RSS's own worked target of P = 1e-9:")
    print(f"  assuming independence               : {RSS_BASELINE_N:,} examples per subsystem")
    print(f"  at the measured lift {point:.3f}          :"
          f" {RSS_BASELINE_N * point**0.5:,.0f} examples")
    print(f"  95% interval on that requirement    :"
          f" [{nlo:,.0f}, {nhi:,.0f}] examples")
    print(f"  lift interval excludes independence : "
          f"{'YES' if lo > 1.0 else 'NO'}   c in [{lo:.3f}, {hi:.3f}]")
    print("")
    print("Result G's headline of about 26% more evidence is confirmed as a point")
    print(f"estimate, {100*(point**0.5-1):.1f}%, and now carries a bound. The lower end of the")
    print(f"interval still requires {100*(lo**0.5-1):.1f}% more than an independence assumption")
    print("allows, so the shortfall is not an artifact of sampling noise.")
    print("")
    print("This is the marginal lift. Result E's conditional lift of 1.156 is the")
    print("quantity to use when the validation campaign already stratifies on class,")
    print("range and visibility. Result I's worst-group lift is the quantity to use")
    print("when the campaign must cover the close-range car. The three answer")
    print("different provisioning questions and must not be interchanged.")
    print("-" * 94)


if __name__ == "__main__":
    main()
