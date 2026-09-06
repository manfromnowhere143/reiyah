"""Review instrument, part 3: an attack suite, each attack with its pass criterion written first.

A reviewer's third move is to try to break the result cheaply. These are the cheap breaks, run
against retained definitions with the tools imported unchanged, each with a criterion stated
here before the run. A failed attack is a finding, never softened.

  ATK-1  label permutation, sensor disagreement monitor (Result AA form, primary pair, linear):
         realness labels permuted over the whole dataset, model refit on the training scenes,
         read on the held-out scenes against their permuted labels, so the null removes every
         feature-label association including the scene-level base rate and the model is scored
         against labels drawn from the same null. Criterion: permuted AUC in [0.47, 0.53] on each
         of 3 permutations, and the unpermuted AUC exceeds the permuted mean by at least 0.15.
         Failure would mean the pipeline manufactures discrimination from noise.
         (The first draft permuted within scene and scored against the true held-out labels; it
         reported 0.61 to 0.64 because scene-level features still predicted each scene's realness
         rate, which is signal, not leakage. That draft is recorded as a defect of the attack and
         corrected here.)
  ATK-2  label permutation, LLM monitor (Result V form on jury A / MMLU): same corrected design and
         criterion. (The first draft scored a noise-fitted model against the true labels and
         reported 0.36 to 0.65, the signature of a nearly constant predictor, not of leakage.)
  ATK-3  leave-one-model-out, MMLU jury (Result T definitions via the Result X loader): for each
         of the 7 six-model juries, marginal mean c above 1, conditional mean c above 1, and
         effective independent models below 0.7 of the jury size. Failure would mean one model
         carries the law.
  ATK-4  leave-one-class-out, primary pair marginal inflation at 0.30 (Result AF definitions):
         for each of the 10 classes dropped, P(both miss) / product above 1. Failure would mean one
         class carries the coupling.
  ATK-5  seed sensitivity, Result AF full-jury effective independence band: seeds 1, 2, 3 with
         B = 300; each band must overlap the retained band [2.08, 2.13]. Failure would mean the
         retained band is a seed artifact.
Advisory under the repository's law; never independent. Seeded; re-runs byte-identically.
"""
import importlib.util
import json
import pathlib
import sys
from collections import defaultdict
from itertools import combinations

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

here = pathlib.Path(__file__).parent
SEED = 20260906


def load(name, sub=None):
    p = (here.parent.parent / sub / name) if sub else here / name
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def permute_within(y, groups, rng):
    out = y.copy()
    for g in np.unique(groups):
        idx = np.where(groups == g)[0]
        out[idx] = y[idx][rng.permutation(len(idx))]
    return out


def main():
    results = []
    def verdict(name, ok, detail):
        results.append((name, ok, detail)); print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}", flush=True)
    print("=" * 92); print("REVIEW INSTRUMENT 3: attack suite"); print("=" * 92)
    rng = np.random.RandomState(SEED)

    # ATK-1 sensor disagreement monitor, linear, primary pair
    ag = load("result_ag_sensor_monitor_transfer.py")
    aa = ag.aa
    gt = json.load(open(aa.GT)); scene = aa.scenes_from_meta()
    X, y, g, c = ag.build_rows(gt, ag.CONFIGS[0][1], 0.30, scene)
    sc_ids = np.unique(g); r2 = np.random.RandomState(SEED); r2.shuffle(sc_ids)
    te_sc = set(sc_ids[: int(0.4 * len(sc_ids))])
    te = np.where(np.array([gg in te_sc for gg in g]))[0]; tr = np.where(np.array([gg not in te_sc for gg in g]))[0]
    D = ag.design(X, list(range(10)))
    def fit_lin(Dtr, ytr):
        return CalibratedClassifierCV(make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000)), method="isotonic", cv=5).fit(Dtr, ytr)
    auc_true = roc_auc_score(y[te], fit_lin(D[tr], y[tr]).predict_proba(D[te])[:, 1])
    perm = []
    for k in range(3):
        yp = y[rng.permutation(len(y))]
        perm.append(roc_auc_score(yp[te], fit_lin(D[tr], yp[tr]).predict_proba(D[te])[:, 1]))
    ok = all(0.47 <= a <= 0.53 for a in perm) and auc_true - np.mean(perm) >= 0.15
    verdict("ATK-1 sensor monitor label permutation", ok, f"true AUC {auc_true:.3f}, permuted {[round(a, 3) for a in perm]}")

    # ATK-2 LLM monitor
    rx = load("result_x_monitor_transfer.py", "llm-generalization/tools")
    A = rx.jury_frame(rx.JURY_A, "mmlu"); XA, yA = rx.features(*A[:3])
    from sklearn.model_selection import train_test_split
    Xtr, Xte, ytr, yte = train_test_split(XA, yA, test_size=0.4, random_state=SEED, stratify=yA)
    auc_true2 = roc_auc_score(yte, rx.fit(Xtr, ytr).predict_proba(Xte)[:, 1])
    perm2 = []
    for _ in range(3):
        yp = yA[rng.permutation(len(yA))]
        Xtr_p, Xte_p, ytr_p, yte_p = train_test_split(XA, yp, test_size=0.4, random_state=SEED, stratify=yp)
        perm2.append(roc_auc_score(yte_p, rx.fit(Xtr_p, ytr_p).predict_proba(Xte_p)[:, 1]))
    ok = all(0.47 <= a <= 0.53 for a in perm2) and auc_true2 - np.mean(perm2) >= 0.15
    verdict("ATK-2 LLM monitor label permutation", ok, f"true AUC {auc_true2:.3f}, permuted {[round(a, 3) for a in perm2]}")

    # ATK-3 leave-one-model-out
    ch, mg, gold, keep = A
    W = (ch.values != gold.values[:, None]); names = [m.split("__")[-1] for m in keep]
    fam = {n: ("Llama" if "Llama" in n else n.split("-")[0]) for n in names}
    def stats(Wsub, nsub):
        k = Wsub.shape[1]; pairs = list(combinations(range(k), 2))
        marg, cond = [], []
        for i, j in pairs:
            wi, wj = Wsub[:, i], Wsub[:, j]; marg.append((wi & wj).mean() / (wi.mean() * wj.mean()))
            others = [o for o in range(k) if o not in (i, j)]; diff = Wsub[:, others].mean(axis=1)
            q = np.quantile(diff, np.linspace(0, 1, 6)); q[-1] += 1e-9; num = den = 0.0
            for b in range(5):
                m = (diff >= q[b]) & (diff < q[b + 1])
                if m.sum() >= 20:
                    num += (Wsub[m, i] & Wsub[m, j]).sum(); den += Wsub[m, i].mean() * Wsub[m, j].mean() * m.sum()
            cond.append(num / den if den else np.nan)
        p = Wsub.mean(axis=0); p_all = Wsub.all(axis=1).mean()
        return np.mean(marg), np.nanmean(cond), np.log(p_all) / np.log(p.mean())
    rows, ok = [], True
    for d in range(len(names)):
        cols = [i for i in range(len(names)) if i != d]
        m_, c_, n_ = stats(W[:, cols], [names[i] for i in cols])
        good = m_ > 1 and c_ > 1 and n_ < 0.7 * len(cols)
        ok &= good; rows.append(f"drop {names[d]}: marg {m_:.3f} cond {c_:.3f} n_eff {n_:.2f}/{len(cols)}")
    verdict("ATK-3 leave-one-model-out, MMLU jury", ok, "; ".join(rows))

    # ATK-4 leave-one-class-out, primary pair marginal inflation at 0.30
    af = load("result_af_sensor_jury.py")
    cam = af.load_matched("matched_mapillary.json"); lid = af.load_matched("matched_megvii.json")
    cls = np.array([o["cls"] for o in gt])
    M = np.array([[cam.get(i, 0.0) < 0.30, lid.get(i, 0.0) < 0.30] for i in range(len(gt))])
    rows, ok = [], True
    for cname in sorted(set(cls)):
        keep_rows = np.where(cls != cname)[0]
        infl, neff, pall = af.stats(M, keep_rows)
        ok &= infl > 1; rows.append(f"drop {cname}: {infl:.3f}")
    verdict("ATK-4 leave-one-class-out, camera x lidar inflation", ok, "; ".join(rows))

    # ATK-5 seed sensitivity of the AF full-jury band
    names4 = list(af.DET); matched = [af.load_matched(af.DET[n]) for n in names4]
    M4 = np.array([[matched[k].get(i, 0.0) < 0.30 for k in range(4)] for i in range(len(gt))])
    inst = np.array([o["instance_token"] for o in gt]); groups = defaultdict(list)
    for i, t in enumerate(inst):
        groups[t].append(i)
    gkeys = list(groups); ok, rows = True, []
    for seed in (1, 2, 3):
        r = np.random.RandomState(seed); vals = []
        for _ in range(300):
            pick = r.choice(len(gkeys), len(gkeys), replace=True)
            idx = np.concatenate([groups[gkeys[j]] for j in pick])
            vals.append(af.stats(M4, idx)[1])
        lo, hi = np.percentile(vals, [2.5, 97.5])
        overlap = not (hi < 2.08 or lo > 2.13); ok &= overlap
        rows.append(f"seed {seed}: [{lo:.2f}, {hi:.2f}]")
    verdict("ATK-5 seed sensitivity, AF full-jury band vs retained [2.08, 2.13]", ok, "; ".join(rows))

    fails = [n for n, o, _ in results if not o]
    print(f"\n  RESULT: {'PASS' if not fails else 'FAIL'}  ({len(fails)} attack(s) succeeded: {fails})")
    print("\n" + "-" * 92)
    print("NON-CLAIMS: advisory self-review with criteria stated in advance; passing an attack is not")
    print("independent validation. No detector or LLM is executed. No released 1.2 byte is involved.")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
