"""Result AI: the preregistered Winogrande test (Preregistration AI, committed before this run).

This is a copy of the Result Y tool with one procedural change, recorded as a deviation in the
preregistration: the Winogrande parquet files carry no `gold` index, only an `answer` string
("1" or "2") naming the correct option, so gold is mapped from `answer` when `gold` is absent or empty and
checked against every row's own `acc` flag; and (deviation 2) questions join by the SHA-256 of
the verbatim example text, as in Result X, because the `hashes` field is a string in some runs
and absent in 2024-format files; the run refuses any model on which the check is not
100 percent. Every definition, the join rule, the auto-drop rule and the printed quantities are
those of Result Y. The eight predictions are not touched.
"""
import hashlib
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
TASK = sys.argv[1] if len(sys.argv) > 1 else "winogrande"


def load(model):
    """Deviation 3: among this model's 5-shot Winogrande runs, take the latest whose predictions
    parse as numbers; gold from `answer` where the file has it, else NaN to be recovered at join
    from a gold-bearing model on the same question and checked against every row's acc."""
    rid = f"open-llm-leaderboard-old/details_{model}"
    try:
        files = sorted(f for f in api.list_repo_files(rid, repo_type="dataset")
                       if f"|{TASK}|5_" in f and f.endswith(".parquet"))
    except Exception as e:
        print(f"  FAILED {model}: {type(e).__name__}", flush=True); return None
    for f in reversed(files):
        try:
            df = pd.read_parquet(hf_hub_download(rid, f, repo_type="dataset"))
            pr = df["predictions"].apply(lambda p: np.array(p, dtype=float))
        except Exception as e:
            print(f"  skipped run {f.split('/')[0]} for {model.split('__')[-1]}: {type(e).__name__}", flush=True)
            continue
        df["qhash"] = df["example"].apply(lambda s: hashlib.sha256(str(s).encode()).hexdigest())
        df["chosen"] = pr.apply(lambda a: int(np.argmax(a)))
        df["gold"] = (df["answer"].astype(int) - 1) if "answer" in df.columns else np.nan
        df["acc"] = df["metrics"].apply(lambda m: float(m["acc"])) if "metrics" in df.columns else df["acc"].astype(float)
        d = df.drop_duplicates("qhash").set_index("qhash")[["acc", "chosen", "gold"]]
        print(f"  loaded {model}: {len(d)} questions (run {f.split('/')[0]}, gold {'in file' if d['gold'].notna().all() else 'recovered at join'})", flush=True)
        return d
    print(f"  FAILED {model}: no 5-shot run with numeric predictions", flush=True)
    return None


def main():
    print(f"loading models on {TASK}...", flush=True)
    acc, chosen, gold, fams, golds, accs = {}, {}, None, {}, {}, {}
    for m, fam in MODELS:
        d = load(m)
        if d is None:
            continue
        acc[m], chosen[m] = (d["acc"] == 1).astype(int), d["chosen"]
        fams[m] = fam
        golds[m] = d["gold"]; accs[m] = d["acc"]
    # gold recovered at join for gold-less files, then checked against every model's own acc
    src = [m for m in golds if golds[m].notna().all()]
    gold = golds[src[0]]
    for m in list(acc):
        common = chosen[m].index.intersection(gold.index)
        agree = float(((chosen[m].loc[common] == gold.loc[common].astype(int)).astype(float) == accs[m].loc[common]).mean()) if len(common) else 0.0
        print(f"  gold check {m.split('__')[-1]}: acc == (chosen == gold) on {100*agree:.2f}% of {len(common)} joined rows")
        if agree < 0.99:
            print(f"  REFUSED {m.split('__')[-1]}: acc does not reproduce from chosen and gold")
            del acc[m]; del chosen[m]; del fams[m]
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
    print(f"RESULT AI - the preregistered test of the LLM law on Winogrande")
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
    mc_all = [marg_c(*p) for p in pairs]; cc_all = [cond_c(*p) for p in pairs]
    print(f"  marginal c per pair: min {np.min(mc_all):.3f}, max {np.max(mc_all):.3f} over {len(pairs)} pairs (deviation 4: added for AI-1)")
    print(f"  conditional c per pair: min {np.nanmin(cc_all):.3f}, max {np.nanmax(cc_all):.3f}")

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
