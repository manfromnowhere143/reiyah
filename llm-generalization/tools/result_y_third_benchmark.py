"""Result Y: does the LLM law replicate on a THIRD benchmark? The second red-team of Results T, U, W.

Same seven candidate models, same estimand, same join-and-auto-drop rule as Result W, on a task
named on the command line (default hellaswag, the leaderboard's 10-shot commonsense completion
task, four choices). This file is a copy of the Result W tool with the task parameterized; the
Result W tool itself is historical bytes and is not edited.
"""
from itertools import combinations

import numpy as np
import pandas as pd
from huggingface_hub import HfApi, hf_hub_download

api = HfApi()
MODELS = [
    ("meta-llama__Llama-2-7b-hf", "Llama"), ("meta-llama__Llama-2-13b-hf", "Llama"),
    ("meta-llama__Llama-2-70b-hf", "Llama"), ("mistralai__Mistral-7B-v0.1", "Mistral"),
    ("tiiuae__falcon-7b", "Falcon"), ("mosaicml__mpt-7b", "MPT"), ("Qwen__Qwen-7B", "Qwen"),
]
import sys
TASK = sys.argv[1] if len(sys.argv) > 1 else "hellaswag"


def load(model):
    rid = f"open-llm-leaderboard-old/details_{model}"
    try:
        files = [f for f in api.list_repo_files(rid, repo_type="dataset")
                 if f"|{TASK}|" in f and f.endswith(".parquet")]
    except Exception:
        return None
    if not files:
        return None
    best = pd.Series([f.split("/")[0] for f in files]).value_counts().index[0]
    parts = []
    for f in sorted(x for x in files if x.startswith(best)):
        try:
            df = pd.read_parquet(hf_hub_download(rid, f, repo_type="dataset"))
            df["qhash"] = df["hashes"].apply(lambda h: h["example"])
            pr = df["predictions"].apply(lambda p: np.array(p, dtype=float))
            df["chosen"] = pr.apply(lambda a: int(np.argmax(a)))
            df["gold"] = df["gold"].astype(int)
            parts.append(df[["qhash", "acc", "chosen", "gold"]])
        except Exception:
            continue
    if not parts:
        return None
    d = pd.concat(parts).drop_duplicates("qhash").set_index("qhash")
    print(f"  loaded {model}: {len(d)} questions", flush=True)
    return d


def main():
    print(f"loading models on {TASK}...", flush=True)
    acc, chosen, gold, fams = {}, {}, None, {}
    for m, fam in MODELS:
        d = load(m)
        if d is None:
            continue
        acc[m], chosen[m] = (d["acc"] == 1).astype(int), d["chosen"]
        fams[m] = fam
        gold = d["gold"] if gold is None else gold
    # auto-drop models whose question hashes do not join (different prompt format).
    # reference is the model that overlaps the MOST others (the majority group).
    def ov(a, b):
        inter = len(acc[a].index.intersection(acc[b].index))
        return inter >= 0.5 * min(len(acc[a]), len(acc[b]))
    ref = max(acc, key=lambda m: sum(ov(m, o) for o in acc if o != m))
    keep = [m for m in acc if m == ref or ov(m, ref)]
    dropped = [m for m in acc if m not in keep]
    if dropped:
        print(f"  dropped (non-joining hashes): {[d.split('__')[-1] for d in dropped]}")
    acc = {m: acc[m] for m in keep}
    chosen = {m: chosen[m] for m in keep}
    A = pd.DataFrame(acc).dropna()
    common = A.index
    Ch = pd.DataFrame(chosen).loc[common].astype(int)
    G = gold.loc[common].astype(int)
    names = list(A.columns)
    W = (A == 0).values.astype(int)
    n = len(A)
    print("=" * 84)
    print(f"RESULT Y - the LLM law on a third benchmark")
    print(f"{len(names)} models, {n} questions answered by all")
    print("=" * 84)

    def marg_c(i, j):
        wi, wj = W[:, i], W[:, j]
        return (wi & wj).mean() / (wi.mean() * wj.mean()) if wi.mean() * wj.mean() > 0 else np.nan

    def cond_c(i, j, bins=5):
        others = [k for k in range(len(names)) if k not in (i, j)]
        if not others or W.shape[0] == 0:
            return np.nan
        diff = (1 - W[:, others]).mean(axis=1)
        q = np.quantile(diff, np.linspace(0, 1, bins + 1)); q[-1] += 1e-9
        num = den = 0.0
        for b in range(bins):
            mm = (diff >= q[b]) & (diff < q[b + 1])
            if mm.sum() < 15:
                continue
            wi, wj = W[mm, i], W[mm, j]
            num += (wi & wj).sum(); den += wi.mean() * wj.mean() * mm.sum()
        return num / den if den > 0 else np.nan

    pairs = list(combinations(range(len(names)), 2))
    same = [(i, j) for i, j in pairs if fams[names[i]] == fams[names[j]]]
    cross = [(i, j) for i, j in pairs if fams[names[i]] != fams[names[j]]]
    print(f"\n  marginal c: mean {np.mean([marg_c(*p) for p in pairs]):.3f}, "
          f"same-family {np.mean([marg_c(*p) for p in same]):.3f}, "
          f"cross-family {np.mean([marg_c(*p) for p in cross]):.3f}")
    print(f"  conditional c: mean {np.nanmean([cond_c(*p) for p in pairs]):.3f}, "
          f"same {np.nanmean([cond_c(*p) for p in same]):.3f}, "
          f"cross {np.nanmean([cond_c(*p) for p in cross]):.3f}")

    p_each = W.mean(axis=0)
    p_all = (W.sum(axis=1) == len(names)).mean()
    pbar = p_each.mean()
    n_eff = np.log(p_all) / np.log(pbar) if 0 < pbar < 1 and p_all > 0 else np.nan
    print(f"  {len(names)}-model jury: P(all wrong) {100*p_all:.2f}% vs indep {100*np.prod(p_each):.3f}% "
          f"= {p_all/np.prod(p_each):.0f}x; effective independent models {n_eff:.2f}")

    C = Ch.values
    Gv = G.values
    Cor = (C == Gv[:, None])
    agr_corr, agr_wrong = [], []
    for i, j in pairs:
        ag = C[:, i] == C[:, j]
        if ag.sum() == 0:
            continue
        agr_corr.append((ag & Cor[:, i] & Cor[:, j]).sum() / ag.sum())
        agr_wrong.append((ag & ~Cor[:, i] & ~Cor[:, j]).sum() / ag.sum())
    unan = (C == C[:, [0]]).all(axis=1)
    unan_wrong = ((unan) & ~Cor[:, 0]).sum() / max(unan.sum(), 1)
    print(f"\n  agreement: P(correct|two agree) {100*np.mean(agr_corr):.1f}%, "
          f"P(both wrong|agree) {100*np.mean(agr_wrong):.1f}%")
    print(f"  unanimous {100*unan.sum()/n:.1f}% of questions, of those wrong {100*unan_wrong:.1f}%")

    print("\n  --- replication reference: MMLU (T/U) and ARC-Challenge (W) ---")
    print("  MMLU: marginal 1.32 (same 1.52 > cross 1.29), conditional 1.10, jury eff 3.6,")
    print("        agree->correct 64.8%, unanimous->wrong 10.4%.")
    print("  ARC:  marginal 1.76 (same 1.87 > cross 1.73), conditional 1.05, jury eff 1.6,")
    print("        agree->correct 57.9%, unanimous->wrong 37.2%.")
    print(f"  If {TASK} shows the same pattern (c>1, same>cross, agreement over-trusted), the law")
    print("  holds; the size of the conditional residual is reported as measured, not assumed.")
    print("\n" + "-" * 84)
    print(f"NON-CLAIMS: public leaderboard outputs on a third benchmark ({TASK}, leaderboard v1 setting);")
    print("same estimand; marginal c includes shared difficulty; descriptive, proposed; a")
    print("robustness replication, not a driving result. No released 1.2 byte involved.")


if __name__ == "__main__":
    main()
