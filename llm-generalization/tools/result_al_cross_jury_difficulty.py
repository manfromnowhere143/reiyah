"""Result AL: the conditional coefficient with difficulty measured by an independent jury.

Result T conditions each pair on question difficulty measured by the other models of the SAME
jury, leave-the-pair-out. An adversarial reading objected that the proxy is built from the same
coupled jury. This measures difficulty with the OTHER jury: for every jury A pair, difficulty is
the fraction of jury B models (seven other families, none in jury A) that answer the question
wrong, in five quantiles; and the reverse for jury B pairs. Everything else is Result T's
definition. If the cross-jury conditional coefficient stays above 1, the residual is not an
artifact of the proxy's provenance. MMLU only, where both juries join on all 13,937 questions.
Loading is imported from the Result X tool unchanged. Question-resampled bootstrap bands, B = 500.
"""
import importlib.util
import pathlib
from itertools import combinations

import numpy as np

spec = importlib.util.spec_from_file_location("rx", pathlib.Path(__file__).with_name("result_x_monitor_transfer.py"))
rx = importlib.util.module_from_spec(spec); spec.loader.exec_module(rx)
FAM_A = {"meta-llama__Llama-2-7b-hf": "Llama", "meta-llama__Llama-2-13b-hf": "Llama", "meta-llama__Llama-2-70b-hf": "Llama",
         "mistralai__Mistral-7B-v0.1": "Mistral", "tiiuae__falcon-7b": "Falcon", "mosaicml__mpt-7b": "MPT", "Qwen__Qwen-7B": "Qwen"}
B, SEED = 500, 20260906


def cond_c(W, i, j, diff, bins=5):
    q = np.quantile(diff, np.linspace(0, 1, bins + 1)); q[-1] += 1e-9
    num = den = 0.0
    for b in range(bins):
        m = (diff >= q[b]) & (diff < q[b + 1])
        if m.sum() < 20:
            continue
        wi, wj = W[m, i], W[m, j]
        num += (wi & wj).sum(); den += wi.mean() * wj.mean() * m.sum()
    return num / den if den > 0 else np.nan


def stats(WA, WB, rows, fams):
    WA, WB = WA[rows], WB[rows]
    k = WA.shape[1]; pairs = list(combinations(range(k), 2))
    diff_B = WB.mean(axis=1)                       # difficulty from the other jury, all its members
    own, cross = [], []
    for i, j in pairs:
        others = [o for o in range(k) if o not in (i, j)]
        own.append(cond_c(WA, i, j, WA[:, others].mean(axis=1)))
        cross.append(cond_c(WA, i, j, diff_B))
    own, cross = np.array(own), np.array(cross)
    same = np.array([fams[i] == fams[j] for i, j in pairs]) if fams else None
    out = {"same-jury difficulty (Result T definition), mean": np.nanmean(own), "other-jury difficulty, mean": np.nanmean(cross),
           "other-jury difficulty, per-pair min": np.nanmin(cross), "other-jury difficulty, per-pair max": np.nanmax(cross)}
    if same is not None and same.any():
        out["other-jury difficulty, same-family"] = np.nanmean(cross[same]); out["other-jury difficulty, cross-family"] = np.nanmean(cross[~same])
        out["other-jury difficulty, same minus cross"] = np.nanmean(cross[same]) - np.nanmean(cross[~same])
    return out


def main():
    A = rx.jury_frame(rx.JURY_A, "mmlu"); Bj = rx.jury_frame(rx.JURY_B, "mmlu")
    common = A[0].index.intersection(Bj[0].index)
    WA = (A[0].loc[common].values != A[2].loc[common].values[:, None]); WB = (Bj[0].loc[common].values != Bj[2].loc[common].values[:, None])
    famsA = [FAM_A[m] for m in A[3]]
    rng = np.random.RandomState(SEED); n = len(common)
    print("=" * 92)
    print("RESULT AL - the conditional coefficient with difficulty measured by an independent jury")
    print(f"MMLU, {n} questions answered by both juries; jury A {len(A[3])} models, jury B {len(Bj[3])} models; B = {B}, seed {SEED}")
    print("=" * 92)
    for label, W1, W2, fams in (("jury A pairs, difficulty from jury B", WA, WB, famsA), ("jury B pairs, difficulty from jury A", WB, WA, None)):
        point = stats(W1, W2, np.arange(n), fams)
        boots = {k: [] for k in point}
        for _ in range(B):
            s = stats(W1, W2, rng.randint(0, n, n), fams)
            for k, v in s.items():
                boots[k].append(v)
        print(f"\n  {label}:")
        print(f"    {'quantity':<52}{'point':>9}{'2.5%':>9}{'97.5%':>9}")
        for k, v in point.items():
            lo, hi = np.nanpercentile(boots[k], [2.5, 97.5])
            print(f"    {k:<52}{v:>9.3f}{lo:>9.3f}{hi:>9.3f}")
    print("\n" + "-" * 92)
    print("NON-CLAIMS: public leaderboard outputs, retained as proposed. Difficulty from the other jury")
    print("is still a proxy (the fraction of seven other models that err); it is independent of the pair")
    print("being measured but not of item difficulty as such. MMLU only. No LLM is executed. No")
    print("released 1.2 byte is involved.")


if __name__ == "__main__":
    main()
