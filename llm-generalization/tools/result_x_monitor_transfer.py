"""Result X: does the monitor transfer? Train on one jury, test on a disjoint jury it never saw.

Result V calibrated the coupling-aware monitor on a seven-model jury and evaluated it on held-out
items of the SAME jury. A deployed instrument does not get that luxury: it is fitted once and then
reads channels it has never seen. This is the transfer test.

  jury A: the seven Result V models (Llama x3, Mistral, Falcon, MPT, Qwen)
  jury B: seven models from seven OTHER families, none in jury A
          (Yi, EleutherAI GPT-NeoX, Google Gemma, Microsoft Phi, BigScience BLOOM,
           StabilityAI StableLM, OpenLM OpenLLaMA)

Experiments, all with the monitor fitted ONCE on jury A / MMLU and never refitted:
  X1  jury transfer:            test on jury B / MMLU
  X2  jury + benchmark transfer: test on jury B / ARC-Challenge
  X3  benchmark transfer only:   test on jury A / ARC-Challenge
  X4  jury-size transfer:        test on a five-model subset of jury B / MMLU
Reference ceilings: the in-domain held-out result on each target (fit on a split of the target
itself), so the transfer loss is measured against what recalibration would buy.

Features per item are the Result V features, from outputs only: agreement fraction, mean/min/std
of per-model confidence margins, the plurality voters' mean margin, vote entropy, number of
distinct answers. Target: the plurality vote is wrong. Naive baseline: risk = 1 - agreement.
Seeded; re-runs byte-identically.
"""
import hashlib

import numpy as np
import pandas as pd
from scipy.stats import entropy as scipy_entropy
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from huggingface_hub import HfApi, hf_hub_download

api = HfApi()
JURY_A = ["meta-llama__Llama-2-7b-hf", "meta-llama__Llama-2-13b-hf", "meta-llama__Llama-2-70b-hf",
          "mistralai__Mistral-7B-v0.1", "tiiuae__falcon-7b", "mosaicml__mpt-7b", "Qwen__Qwen-7B"]
JURY_B = ["01-ai__Yi-6B", "EleutherAI__gpt-neox-20b", "google__gemma-7b", "microsoft__phi-2",
          "bigscience__bloom-7b1", "stabilityai__stablelm-base-alpha-7b",
          "openlm-research__open_llama_7b_v2"]
JURY_B5 = JURY_B[:5]
SEED = 20260906
TASKS = {"mmlu": "hendrycksTest-", "arc": "|arc:challenge|"}


def _gold(row):
    """Gold answer index where the file carries one.

    The 2023 format stores an integer `gold`. The 2024 lighteval format stores empty `gold`,
    `gold_index` and `choices` arrays and only `metrics.acc`; its gold is recovered at join time
    from a 2023-format model on the same question (gold is a property of the question, not the
    model) and then checked against `metrics.acc` for every row. Nothing is guessed.
    """
    g = row["gold"]
    if hasattr(g, "__len__") and not isinstance(g, str):
        return int(g[0]) if len(g) == 1 else None
    return int(g)


def load(model, task):
    """Load per-question outputs. Questions join across models and formats by the SHA-256 of the
    verbatim `example` text, which both parquet formats carry; the 2023 `hashes.example` field is
    not used because the 2024 format lacks it. Failures are printed, never silent."""
    rid = f"open-llm-leaderboard-old/details_{model}"
    key = TASKS[task]
    try:
        files = [f for f in api.list_repo_files(rid, repo_type="dataset")
                 if key in f and f.endswith(".parquet")]
    except Exception as e:
        print(f"  FAILED {model} on {task}: {type(e).__name__}", flush=True)
        return None
    if not files:
        print(f"  FAILED {model} on {task}: no parquet files for this task", flush=True)
        return None
    best = pd.Series([f.split("/")[0] for f in files]).value_counts().index[0]
    parts = []
    for f in sorted(x for x in files if x.startswith(best)):
        try:
            df = pd.read_parquet(hf_hub_download(rid, f, repo_type="dataset"))
            df["qhash"] = df["example"].apply(lambda s: hashlib.sha256(str(s).encode()).hexdigest())
            pr = df["predictions"].apply(lambda p: np.array(p, dtype=float))
            df["chosen"] = pr.apply(lambda a: int(np.argmax(a)))
            df["margin"] = pr.apply(lambda a: float(np.sort(a)[-1] - np.sort(a)[-2]))
            df["gold"] = df.apply(_gold, axis=1)
            df["acc"] = df["metrics"].apply(lambda m: float(m["acc"])) if "metrics" in df.columns else df["acc"].astype(float)
            parts.append(df[["qhash", "chosen", "margin", "gold", "acc"]])
        except Exception as e:
            print(f"  FAILED {model} on {task} file {f.split('/')[-1][:60]}: {type(e).__name__}: {e}"[:160], flush=True)
            continue
    if not parts:
        return None
    d = pd.concat(parts).drop_duplicates("qhash").set_index("qhash")
    fmt = "2023" if d["gold"].notna().all() else ("2024, gold recovered at join" if d["gold"].isna().all() else "MIXED")
    print(f"  loaded {model} on {task}: {len(d)} questions (run {best}, {fmt} format)", flush=True)
    return d


MIN_JURY = 5


def jury_frame(models, task):
    """Join a jury on common question hashes; auto-drop non-joining models like Result W; recover
    gold for gold-less files from a gold-bearing model and verify it against every row's acc."""
    data = {m: d for m in models if (d := load(m, task)) is not None}
    def ov(a, b):
        inter = len(data[a].index.intersection(data[b].index))
        return inter >= 0.5 * min(len(data[a]), len(data[b]))
    ref = max(data, key=lambda m: sum(ov(m, o) for o in data if o != m))
    keep = [m for m in data if m == ref or ov(m, ref)]
    dropped = [m for m in data if m not in keep]
    if dropped:
        print(f"  dropped (non-joining hashes) on {task}: {[d.split('__')[-1] for d in dropped]}")
    common = None
    for m in keep:
        common = data[m].index if common is None else common.intersection(data[m].index)
    gold_src = [m for m in keep if data[m]["gold"].notna().all()]
    if not gold_src:
        raise SystemExit(f"no gold-bearing model on {task}; cannot recover gold")
    gold = data[gold_src[0]]["gold"].loc[common].astype(int)
    for m in gold_src[1:]:
        assert (data[m]["gold"].loc[common].astype(int) == gold).all(), f"gold disagrees: {m}"
    verified = []
    for m in keep:
        d = data[m].loc[common]
        agree = float(((d["chosen"] == gold).astype(float) == d["acc"]).mean())
        tag = "file gold" if d["gold"].notna().all() else "recovered gold"
        print(f"  gold check {m.split('__')[-1]} on {task}: acc == (chosen == gold) on "
              f"{100*agree:.2f}% of {len(d)} rows ({tag})", flush=True)
        if agree < 0.99:
            print(f"  REFUSED {m.split('__')[-1]} on {task}: acc does not reproduce from chosen and gold")
            continue
        verified.append(m)
    keep = verified
    ch = pd.DataFrame({m: data[m]["chosen"].loc[common] for m in keep}).astype(int)
    mg = pd.DataFrame({m: data[m]["margin"].loc[common] for m in keep})
    return ch, mg, gold, keep


def features(ch, mg, gold):
    ch, mg, G = ch.values, mg.values, gold.values
    n, k = ch.shape
    X, y = [], []
    for i in range(n):
        votes = ch[i]
        vals, cnts = np.unique(votes, return_counts=True)
        plural = vals[np.argmax(cnts)]
        pv = mg[i][votes == plural]
        X.append([cnts.max() / k, mg[i].mean(), mg[i].min(), mg[i].std(), pv.mean(),
                  scipy_entropy(cnts / k), len(vals)])
        y.append(int(plural != G[i]))
    return np.array(X), np.array(y)


def ece(y, p, bins=10):
    edges = np.linspace(0, 1, bins + 1)
    e = 0.0
    for b in range(bins):
        m = (p >= edges[b]) & (p < edges[b + 1] if b < bins - 1 else p <= edges[b + 1])
        if m.sum():
            e += abs(y[m].mean() - p[m].mean()) * m.sum() / len(y)
    return e


def fit(X, y):
    base = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
    mon = CalibratedClassifierCV(base, method="isotonic", cv=5)
    mon.fit(X, y)
    return mon


def report(label, y, p_mon, p_naive, agree):
    print(f"\n  {label}")
    print(f"    n = {len(y)}, jury (plurality) wrong rate {100*y.mean():.1f}%")
    print(f"    {'estimator':<28}{'AUC':>8}{'Brier':>9}{'ECE':>8}")
    print(f"    {'naive: 1 - agreement':<28}{roc_auc_score(y,p_naive):>8.3f}"
          f"{brier_score_loss(y,p_naive):>9.3f}{ece(y,p_naive):>8.3f}")
    print(f"    {'monitor (no refit)':<28}{roc_auc_score(y,p_mon):>8.3f}"
          f"{brier_score_loss(y,p_mon):>9.3f}{ece(y,p_mon):>8.3f}")
    un = agree == 1.0
    if un.sum():
        print(f"    unanimous items ({int(un.sum())}): actual wrong {100*y[un].mean():.1f}%, "
              f"naive risk {100*p_naive[un].mean():.1f}%, monitor risk {100*p_mon[un].mean():.1f}%")
    order = np.argsort(p_mon)
    bands = []
    for q in range(5):
        idx = order[q*len(order)//5:(q+1)*len(order)//5]
        bands.append(f"{100*p_mon[idx].mean():.0f}/{100*y[idx].mean():.0f}")
    print(f"    reliability bands predicted/actual %: {'  '.join(bands)}")


def ceiling(X, y, label):
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.4, random_state=SEED, stratify=y)
    mon = fit(Xtr, ytr)
    p = mon.predict_proba(Xte)[:, 1]
    print(f"    in-domain ceiling on {label} (refit on its own split, held-out): "
          f"AUC {roc_auc_score(yte,p):.3f}  Brier {brier_score_loss(yte,p):.3f}  ECE {ece(yte,p):.3f}")


def main():
    print("loading juries...", flush=True)
    A_m = jury_frame(JURY_A, "mmlu")
    B_m = jury_frame(JURY_B, "mmlu")
    A_a = jury_frame(JURY_A, "arc")
    B_a = jury_frame(JURY_B, "arc")
    XA, yA = features(*A_m[:3])
    monitor = fit(XA, yA)                       # fitted once, never refitted
    print("=" * 92)
    print("RESULT X - monitor transfer: fitted once on jury A / MMLU, read on juries it never saw")
    print(f"jury A: {len(A_m[3])} models, {len(yA)} MMLU items, jury wrong rate {100*yA.mean():.1f}%")
    print(f"jury B on MMLU: {[m.split('__')[-1] for m in B_m[3]]}")
    print(f"jury B on ARC : {[m.split('__')[-1] for m in B_a[3]]}")
    print("=" * 92)

    def run(label, frame, subset=None):
        ch, mg, gold, keep = frame
        if subset:
            cols = [m for m in keep if m in subset]
            ch, mg = ch[cols], mg[cols]
            keep = cols
        names = [m.split("__")[-1] for m in keep]
        if len(keep) < MIN_JURY:
            print(f"\n  {label}\n    NOT RUN: jury has {len(keep)} models ({names}), below the "
                  f"minimum of {MIN_JURY}; a two- or three-model vote is not the instrument under test")
            return
        X, y = features(ch, mg, gold)
        p_mon = monitor.predict_proba(X)[:, 1]
        report(f"{label}  [{len(keep)} models: {', '.join(names)}]", y, p_mon, 1.0 - X[:, 0], X[:, 0])
        ceiling(X, y, label.split(":")[0])

    run("X1: jury B / MMLU  (unseen families)", B_m)
    run("X2: jury B / ARC-Challenge  (unseen jury AND unseen benchmark)", B_a)
    run("X3: jury A / ARC-Challenge  (unseen benchmark only)", A_a)
    run("X4: five-model subset of jury B / MMLU  (unseen jury, different size)", B_m, B_m[3][:5])

    print("\n" + "-" * 92)
    print("NON-CLAIMS: public leaderboard outputs, retained as proposed. Transfer is between two")
    print("juries of public base models on two benchmarks; not a deployed product, not a safety")
    print("determination, not a driving result. The naive baseline is the ensemble's own implicit")
    print("assumption. Margins are per-model log-prob gaps and are not rescaled between juries, by")
    print("design: a deployed monitor would not know the new channels' scales either. No released")
    print("1.2 byte is involved.")


if __name__ == "__main__":
    main()
