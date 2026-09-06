"""Result T: the independence assumption beyond driving - do LLM juries fail together?

The whole program measured whether redundant channels fail independently, the assumption every
safety and ensemble argument leans on. This carries the identical estimand to a different domain:
LLM ensembles and LLM-as-judge. Self-consistency, majority vote, and multi-model juries all assume
the models err independently, so aggregating cuts error. Do they?

Data: the public v1 Open LLM Leaderboard per-question results (open-llm-leaderboard-old), MMLU,
5-shot, per-question correctness (acc, 0/1). Questions join across models by a hash of the example.
Same method as the camera-lidar work: public per-item predictions, the Definition 32 coefficient.

  wrong_m(q) = model m answered question q incorrectly
  c(i,j) = P(both wrong) / [ P(i wrong) * P(j wrong) ]      c = 1 independence, c > 1 fail together

Two refinements matched to the rest of the program:
  - conditional c: condition on question difficulty measured by the OTHER models (leave-the-pair
    out mean correctness), stratified, so the coupling is beyond shared question difficulty.
  - same-family vs cross-family: do models of one lineage fail together more than models of
    different lineages, the LLM analogue of same-modality vs cross-modality sensors.
"""
import sys
from itertools import combinations

import numpy as np
import pandas as pd
from huggingface_hub import HfApi, hf_hub_download

api = HfApi()
MODELS = [
    ("meta-llama__Llama-2-7b-hf", "Llama"),
    ("meta-llama__Llama-2-13b-hf", "Llama"),
    ("meta-llama__Llama-2-70b-hf", "Llama"),
    ("mistralai__Mistral-7B-v0.1", "Mistral"),
    ("tiiuae__falcon-7b", "Falcon"),
    ("mosaicml__mpt-7b", "MPT"),
    ("Qwen__Qwen-7B", "Qwen"),
]


def load_model(model):
    rid = f"open-llm-leaderboard-old/details_{model}"
    try:
        files = [f for f in api.list_repo_files(rid, repo_type="dataset")
                 if "hendrycksTest-" in f and f.endswith(".parquet")]
    except Exception as e:
        print(f"  skip {model}: {type(e).__name__}", flush=True)
        return None
    if not files:
        return None
    # pick the single most complete timestamp
    ts = [f.split("/")[0] for f in files]
    best = pd.Series(ts).value_counts().index[0]
    files = sorted(f for f in files if f.startswith(best))
    parts = []
    for f in files:
        try:
            df = pd.read_parquet(hf_hub_download(rid, f, repo_type="dataset"))
            df["qhash"] = df["hashes"].apply(lambda h: h["example"])
            parts.append(df[["qhash", "acc"]])
        except Exception:
            continue
    if not parts:
        return None
    s = pd.concat(parts).drop_duplicates("qhash").set_index("qhash")["acc"]
    print(f"  loaded {model}: {len(s)} questions", flush=True)
    return s


def main():
    print("loading models...", flush=True)
    series, fams = {}, {}
    for m, fam in MODELS:
        s = load_model(m)
        if s is not None:
            series[m] = s
            fams[m] = fam
    M = pd.DataFrame(series).dropna()          # questions all models answered
    wrong = (M == 0).astype(int)
    names = list(M.columns)
    n_q = len(M)
    print("=" * 88)
    print("RESULT T - the independence assumption beyond driving: LLM juries")
    print(f"MMLU 5-shot, {len(names)} models, {n_q} questions answered by all")
    print("=" * 88)
    print("\n  per-model error rate:")
    for m in names:
        print(f"    {m:<32} {fams[m]:<8} wrong {100*wrong[m].mean():.1f}%")

    W = wrong.values  # n_q x n_models
    idx = {m: k for k, m in enumerate(names)}

    def marg_c(i, j):
        wi, wj = W[:, i], W[:, j]
        pi, pj = wi.mean(), wj.mean()
        pb = (wi & wj).mean()
        return pb / (pi * pj) if pi * pj > 0 else np.nan

    def cond_c(i, j, bins=5):
        # difficulty = mean correctness of the OTHER models (leave the pair out)
        others = [k for k in range(len(names)) if k not in (i, j)]
        diff = (1 - W[:, others]).mean(axis=1)   # fraction of others WRONG = harder
        q = np.quantile(diff, np.linspace(0, 1, bins + 1))
        q[-1] += 1e-9
        num = den = 0.0
        for b in range(bins):
            m = (diff >= q[b]) & (diff < q[b + 1])
            if m.sum() < 20:
                continue
            wi, wj = W[m, i], W[m, j]
            pi, pj = wi.mean(), wj.mean()
            num += (wi & wj).sum()
            den += pi * pj * m.sum()
        return num / den if den > 0 else np.nan

    pairs = list(combinations(range(len(names)), 2))
    same = [(i, j) for i, j in pairs if fams[names[i]] == fams[names[j]]]
    cross = [(i, j) for i, j in pairs if fams[names[i]] != fams[names[j]]]

    print(f"\n  marginal coefficient c across all {len(pairs)} model pairs:")
    mc = [marg_c(i, j) for i, j in pairs]
    print(f"    mean {np.mean(mc):.3f}, range [{np.min(mc):.3f}, {np.max(mc):.3f}]")
    print(f"  same-family pairs ({len(same)}): mean marginal c = "
          f"{np.mean([marg_c(i,j) for i,j in same]):.3f}"
          if same else "  (no same-family pairs)")
    print(f"  cross-family pairs ({len(cross)}): mean marginal c = "
          f"{np.mean([marg_c(i,j) for i,j in cross]):.3f}")

    print(f"\n  CONDITIONAL c (beyond shared question difficulty), all pairs:")
    cc = [cond_c(i, j) for i, j in pairs]
    print(f"    mean {np.nanmean(cc):.3f}, range [{np.nanmin(cc):.3f}, {np.nanmax(cc):.3f}]")
    if same:
        print(f"  same-family conditional c : {np.nanmean([cond_c(i,j) for i,j in same]):.3f}")
    print(f"  cross-family conditional c: {np.nanmean([cond_c(i,j) for i,j in cross]):.3f}")

    # effective number of independent models for the full jury
    p_each = W.mean(axis=0)
    p_all_wrong = (W.sum(axis=1) == len(names)).mean()
    p_indep = np.prod(p_each)
    infl = p_all_wrong / p_indep if p_indep > 0 else np.nan
    pbar = p_each.mean()
    n_eff = np.log(p_all_wrong) / np.log(pbar) if 0 < pbar < 1 and p_all_wrong > 0 else np.nan
    print(f"\n  the {len(names)}-model jury, all wrong on the same question:")
    print(f"    observed P(all wrong)      : {100*p_all_wrong:.2f}%")
    print(f"    if independent (prod p)    : {100*p_indep:.4f}%")
    print(f"    inflation over independence: {infl:.0f}x")
    print(f"    effective independent models: {n_eff:.2f}  (you have {len(names)}, you got ~{n_eff:.1f})")

    print("\n" + "-" * 88)
    print("NON-CLAIMS: public leaderboard per-question correctness on one benchmark (MMLU 5-shot);")
    print("the estimand is the same as the sensor and human work; c > 1 includes shared question")
    print("difficulty at the marginal level (the conditional c removes the measurable part of it);")
    print("descriptive, retained as proposed; a generalization demonstration, not a driving result.")


if __name__ == "__main__":
    main()
