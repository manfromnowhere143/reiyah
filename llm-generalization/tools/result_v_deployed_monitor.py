"""Result V: the deployed monitor - a coupling-corrected joint-failure risk from outputs alone.

The whole program measured that redundant channels fail together, and Result U showed agreement is
therefore an over-trusted signal. This turns that into an instrument: a monitor that reads only the
channels' outputs on an item, with NO ground truth, and returns a calibrated probability that the
ensemble is wrong, having learned the coupling from a labeled calibration set.

It is held to the standard a deployed instrument must meet:
  - generalization: calibrate on a train split, evaluate on a held-out test split;
  - calibration: expected calibration error (ECE) and Brier score on held-out data;
  - discrimination: ROC AUC on held-out data;
  - it must beat the naive agreement heuristic (risk = 1 - agreement), the ensemble's implicit
    independence assumption, on the same held-out data.

Instance here: seven-model LLM jury on MMLU (per-item outputs with ground truth for calibration and
evaluation). The features are channel-agnostic, so the same monitor form applies to any redundant
channels whose outputs carry a choice and a confidence.

Features per item, from outputs only:
  agreement fraction, mean/min/std of per-model confidence margins, plurality-voters' mean margin,
  vote entropy, number of distinct answers.
Target: the plurality vote is wrong (the ensemble's joint failure).
"""
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
MODELS = ["meta-llama__Llama-2-7b-hf", "meta-llama__Llama-2-13b-hf",
          "meta-llama__Llama-2-70b-hf", "mistralai__Mistral-7B-v0.1",
          "tiiuae__falcon-7b", "mosaicml__mpt-7b", "Qwen__Qwen-7B"]


def load(model):
    rid = f"open-llm-leaderboard-old/details_{model}"
    try:
        files = [f for f in api.list_repo_files(rid, repo_type="dataset")
                 if "hendrycksTest-" in f and f.endswith(".parquet")]
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
            df["margin"] = pr.apply(lambda a: float(np.sort(a)[-1] - np.sort(a)[-2]))
            df["gold"] = df["gold"].astype(int)
            parts.append(df[["qhash", "chosen", "margin", "gold"]])
        except Exception:
            continue
    d = pd.concat(parts).drop_duplicates("qhash").set_index("qhash")
    return d


def ece(y, p, bins=10):
    edges = np.linspace(0, 1, bins + 1)
    e = 0.0
    for b in range(bins):
        m = (p >= edges[b]) & (p < edges[b + 1] if b < bins - 1 else p <= edges[b + 1])
        if m.sum() == 0:
            continue
        e += abs(y[m].mean() - p[m].mean()) * m.sum() / len(y)
    return e


def main():
    print("loading models...", flush=True)
    chosen, margin, gold = {}, {}, None
    for m in MODELS:
        d = load(m)
        if d is None:
            continue
        chosen[m], margin[m] = d["chosen"], d["margin"]
        gold = d["gold"] if gold is None else gold
    C = pd.DataFrame(chosen).dropna().astype(int)
    Mg = pd.DataFrame(margin).loc[C.index]
    G = gold.loc[C.index].astype(int).values
    ch = C.values
    mg = Mg.values
    n, k = ch.shape

    feats, y = [], []
    for i in range(n):
        votes = ch[i]
        vals, cnts = np.unique(votes, return_counts=True)
        plural = vals[np.argmax(cnts)]
        agree = cnts.max() / k
        pv = mg[i][votes == plural]
        p_counts = cnts / k
        feats.append([agree, mg[i].mean(), mg[i].min(), mg[i].std(),
                      pv.mean(), scipy_entropy(p_counts), len(vals)])
        y.append(int(plural != G[i]))     # ensemble (plurality) wrong
    X = np.array(feats); y = np.array(y)
    agree_frac = X[:, 0]

    Xtr, Xte, ytr, yte, atr, ate = train_test_split(
        X, y, agree_frac, test_size=0.4, random_state=20260828, stratify=y)

    base = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
    monitor = CalibratedClassifierCV(base, method="isotonic", cv=5)
    monitor.fit(Xtr, ytr)
    p_mon = monitor.predict_proba(Xte)[:, 1]

    # naive baseline: the ensemble's implicit assumption, risk = 1 - agreement
    p_naive = 1.0 - ate

    print("=" * 88)
    print("RESULT V - the deployed monitor: coupling-corrected joint-failure risk from outputs")
    print(f"seven-model jury on MMLU; train {len(ytr)}, held-out test {len(yte)}; "
          f"base ensemble error {100*y.mean():.1f}%")
    print("=" * 88)
    print("\n  held-out performance (higher AUC better; lower Brier and ECE better):")
    print(f"  {'estimator':<34}{'AUC':>8}{'Brier':>9}{'ECE':>8}")
    print(f"  {'naive: risk = 1 - agreement':<34}{roc_auc_score(yte,p_naive):>8.3f}"
          f"{brier_score_loss(yte,p_naive):>9.3f}{ece(yte,p_naive):>8.3f}")
    print(f"  {'MONITOR: coupling-aware, calibrated':<34}{roc_auc_score(yte,p_mon):>8.3f}"
          f"{brier_score_loss(yte,p_mon):>9.3f}{ece(yte,p_mon):>8.3f}")

    # the load-bearing demonstration: unanimous items on the held-out set
    unan = ate == 1.0
    if unan.sum() > 0:
        true_wrong = yte[unan].mean()
        naive_risk = p_naive[unan].mean()
        mon_risk = p_mon[unan].mean()
        print(f"\n  on held-out UNANIMOUS items ({int(unan.sum())} of {len(yte)}):")
        print(f"    actual wrong rate           : {100*true_wrong:.1f}%")
        print(f"    naive risk (1 - agreement)  : {100*naive_risk:.1f}%   (says unanimity = certainty)")
        print(f"    MONITOR risk                : {100*mon_risk:.1f}%   (learned the coupling)")

    # reliability across monitor risk deciles (held-out)
    print("\n  monitor reliability on held-out data (predicted risk vs actual wrong rate):")
    order = np.argsort(p_mon)
    for q in range(5):
        idx = order[q * len(order)//5:(q+1)*len(order)//5]
        print(f"    risk band {q+1}: predicted {100*p_mon[idx].mean():>5.1f}%   "
              f"actual {100*yte[idx].mean():>5.1f}%   (n={len(idx)})")

    print("\n" + "-" * 88)
    print("NON-CLAIMS: demonstration instrument on public MMLU outputs, retained as proposed. The")
    print("features are channel-agnostic but this is calibrated and evaluated on one benchmark and")
    print("one jury; not a deployed product, not a safety determination, not a driving result. The")
    print("naive baseline is the ensemble's own implicit assumption, shown for contrast. No released")
    print("1.2 byte is involved.")


if __name__ == "__main__":
    main()
