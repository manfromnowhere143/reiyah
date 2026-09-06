"""Result AC: intervals for every LLM-jury coefficient, on all three benchmarks.

Results T, U, W and Y report point estimates. The program's own rule for the sensors is never to
quote a coefficient without its band. This puts a question-resampled bootstrap interval on every
headline LLM quantity, on MMLU, ARC-Challenge and HellaSwag, with the same seven candidate models,
the same join and auto-drop rule, and the same definitions as Result T (marginal c; conditional c
by leave-the-pair-out difficulty quintiles; effective independent models as log P(all wrong) over
log of the mean error rate) and Result U (agreement is the argmax choice).

The unit of resampling is the question, which is the unit of the join. Questions are not clustered
further: the leaderboard files carry no subject grouping that survives the join for every model.
B = 1000 resamples, seeded. Data loading is imported from the Result X tool unchanged.
"""
import importlib.util
import pathlib
from itertools import combinations

import numpy as np

spec = importlib.util.spec_from_file_location("rx", pathlib.Path(__file__).with_name("result_x_monitor_transfer.py"))
rx = importlib.util.module_from_spec(spec); spec.loader.exec_module(rx)
rx.TASKS["hellaswag"] = "|hellaswag|"

FAMILY = {"meta-llama__Llama-2-7b-hf": "Llama", "meta-llama__Llama-2-13b-hf": "Llama",
          "meta-llama__Llama-2-70b-hf": "Llama", "mistralai__Mistral-7B-v0.1": "Mistral",
          "tiiuae__falcon-7b": "Falcon", "mosaicml__mpt-7b": "MPT", "Qwen__Qwen-7B": "Qwen"}
B, SEED = 1000, 20260906


def stats(W, C, fams, rows):
    """All headline quantities on the questions indexed by rows. W wrong (n x k), C chosen."""
    W, C = W[rows], C[rows]
    n, k = W.shape
    pairs = list(combinations(range(k), 2))
    marg, cond, same_flag, agree_corr = [], [], [], []
    for i, j in pairs:
        wi, wj = W[:, i], W[:, j]
        pi, pj = wi.mean(), wj.mean()
        marg.append((wi & wj).mean() / (pi * pj))
        others = [o for o in range(k) if o not in (i, j)]
        diff = W[:, others].mean(axis=1)
        q = np.quantile(diff, np.linspace(0, 1, 6)); q[-1] += 1e-9
        num = den = 0.0
        for b in range(5):
            m = (diff >= q[b]) & (diff < q[b + 1])
            if m.sum() < 20:
                continue
            a, c = W[m, i], W[m, j]
            num += (a & c).sum(); den += a.mean() * c.mean() * m.sum()
        cond.append(num / den if den > 0 else np.nan)
        same_flag.append(fams[i] == fams[j])
        ag = C[:, i] == C[:, j]
        agree_corr.append((~wi[ag]).mean() if ag.sum() else np.nan)
    marg, cond, same_flag = np.array(marg), np.array(cond), np.array(same_flag)
    p_each = W.mean(axis=0); p_all = (W.sum(axis=1) == k).mean()
    n_eff = np.log(p_all) / np.log(p_each.mean()) if p_all > 0 else np.nan
    unan = (C == C[:, [0]]).all(axis=1)
    unan_wrong = W[unan, 0].mean() if unan.sum() else np.nan
    out = {"marginal c, mean": marg.mean(), "marginal c, cross-family": marg[~same_flag].mean(),
           "conditional c, mean": np.nanmean(cond), "conditional c, cross-family": np.nanmean(cond[~same_flag]),
           "P(all wrong) / independent": p_all / np.prod(p_each), "effective independent models": n_eff,
           "P(correct | two agree), mean": np.nanmean(agree_corr), "unanimous share": unan.mean(),
           "unanimous-yet-wrong": unan_wrong}
    if same_flag.any():
        out["marginal c, same-family"] = marg[same_flag].mean()
        out["conditional c, same-family"] = np.nanmean(cond[same_flag])
        out["same minus cross, marginal"] = marg[same_flag].mean() - marg[~same_flag].mean()
        out["same minus cross, conditional"] = np.nanmean(cond[same_flag]) - np.nanmean(cond[~same_flag])
    return out


def main():
    rng = np.random.RandomState(SEED)
    print("=" * 92)
    print("RESULT AC - bootstrap intervals for every LLM-jury coefficient, three benchmarks")
    print(f"question-resampled, B = {B}, seed {SEED}; definitions as Results T and U")
    print("=" * 92)
    for task in ("mmlu", "arc", "hellaswag"):
        ch, mg, gold, keep = rx.jury_frame(rx.JURY_A, task)
        W = (ch.values != gold.values[:, None]); C = ch.values
        fams = [FAMILY[m] for m in keep]
        n = len(W)
        point = stats(W, C, fams, np.arange(n))
        boots = {k: [] for k in point}
        for b in range(B):
            s = stats(W, C, fams, rng.randint(0, n, n))
            for k, v in s.items():
                boots[k].append(v)
        print(f"\n  {task}: {len(keep)} models ({', '.join(m.split('__')[-1] for m in keep)}), {n} questions")
        print(f"    {'quantity':<34}{'point':>9}{'2.5%':>9}{'97.5%':>9}")
        for k, v in point.items():
            lo, hi = np.nanpercentile(boots[k], [2.5, 97.5])
            print(f"    {k:<34}{v:>9.3f}{lo:>9.3f}{hi:>9.3f}")
    print("\n" + "-" * 92)
    print("NON-CLAIMS: public leaderboard outputs, retained as proposed. Intervals are question-")
    print("resampled percentile bootstraps and describe sampling variation over questions only; they")
    print("do not cover model selection, prompt format, or benchmark choice. Descriptive, not a safety")
    print("determination, not a driving result. No LLM is executed. No released 1.2 byte is involved.")


if __name__ == "__main__":
    main()
