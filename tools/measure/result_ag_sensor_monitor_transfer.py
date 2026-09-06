"""Result AG: does the object-level sensor monitor transfer across detector pairs?

Result X showed the LLM monitor transfers across juries. Result AD showed the object-level sensor
monitor reads cross-channel context with a boosted model. This asks the sensor analogue of X: fit
the boosted per-object monitor ONCE on one detector pair (Mapillary x Megvii at 0.30, training
scenes) and read it, without refit, on a second camera (FCOS3D x Megvii), a second lidar
(Mapillary x PointPillars) and a second operating point (Mapillary x Megvii at 0.50), on the
held-out scenes, against the naive score-alone baseline and the in-domain ceiling (refit on the
target's own training scenes). The registered reconsideration requirement for AD asked for a
held-out detector pair; this is it, with the same features, labels and self-check as Result AA.

The row-building logic is a copy of Result AA's (that tool is historical bytes). It is
self-checked: on the primary configuration the copy must reproduce AA's row count and realness
rates exactly, or the run is refused.
"""
import importlib.util
import json
import math
import pathlib
import sys
from collections import defaultdict

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import roc_auc_score, brier_score_loss

here = pathlib.Path(__file__).parent
spec = importlib.util.spec_from_file_location("aa", here / "result_aa_disagreement_monitor.py")
aa = importlib.util.module_from_spec(spec); spec.loader.exec_module(aa)
SEED = 20260906
CONFIGS = [
    ("P1 Mapillary x Megvii @0.30", {"camera": ("matched_mapillary.json", "predictions/mapillary_val.json"),
                                    "lidar": ("matched_megvii.json", "predictions/megvii_val.json")}, 0.30),
    ("P2 FCOS3D x Megvii @0.30", {"camera": ("matched_fcos3d.json", "predictions/fcos3d_val.json"),
                                  "lidar": ("matched_megvii.json", "predictions/megvii_val.json")}, 0.30),
    ("P3 Mapillary x PointPillars @0.30", {"camera": ("matched_mapillary.json", "predictions/mapillary_val.json"),
                                          "lidar": ("matched_pointpillars.json", "predictions/pointpillars-val.json")}, 0.30),
    ("P4 Mapillary x Megvii @0.50", {"camera": ("matched_mapillary.json", "predictions/mapillary_val.json"),
                                    "lidar": ("matched_megvii.json", "predictions/megvii_val.json")}, 0.50),
]
EXPECT_P1 = (90946, 37142, 53804)


def build_rows(gt, ch, score, scene):
    """Copy of Result AA's row construction with the score threshold as a parameter."""
    aa.SCORE = score
    matched = {k: aa.load_matched(v[0]) for k, v in ch.items()}
    dets = {k: aa.detections(v[1]) for k, v in ch.items()}
    gt_by_sample, ego = defaultdict(list), {}
    for gi, o in enumerate(gt):
        gt_by_sample[o["sample_token"]].append(gi); ego[o["sample_token"]] = o["ego_xy"]
    rows, labels, groups, chan = [], [], [], []
    check = defaultdict(lambda: [0, 0])
    for st in sorted(gt_by_sample):
        gis = gt_by_sample[st]
        gt_rows = [(gt[gi]["cls"], gt[gi]["xy"][0], gt[gi]["xy"][1]) for gi in gis]
        da, db = dets["camera"].get(st, []), dets["lidar"].get(st, [])
        ab = aa.greedy_match(da, [(c, x, y) for c, s, x, y in db])
        agreed_a, agreed_b = set(ab), set(ab.values())
        n_both = len(ab); n_either = len(da) + len(db) - n_both
        agree = n_both / n_either if n_either else 0.0
        s_both = float(np.mean([min(da[i][1], db[j][1]) for i, j in ab.items()])) if ab else 0.0
        n_only = {"camera": len(da) - n_both, "lidar": len(db) - n_both}
        lab = {"camera": aa.greedy_match(da, gt_rows), "lidar": aa.greedy_match(db, gt_rows)}
        for c_, d, l in (("camera", da, lab["camera"]), ("lidar", db, lab["lidar"])):
            real_gi = {gis[j] for j in l.values()}
            for gi in gis:
                if matched[c_].get(gi, 0.0) >= score:
                    check[c_][0] += 1; check[c_][1] += int(gi in real_gi)
        ex, ey = ego[st]
        for c_, own, other, agreed in (("camera", da, db, agreed_a), ("lidar", db, da, agreed_b)):
            for i, (c, s, x, y) in enumerate(own):
                if i in agreed:
                    continue
                near = [math.hypot(x - ox, y - oy) for _, _, ox, oy in other]
                nearest = min(near) if near else 50.0
                rows.append([s, math.hypot(x - ex, y - ey), aa.CLS_IDX[c], 1.0 if c_ == "lidar" else 0.0,
                             agree, n_only["camera"], n_only["lidar"], min(nearest, 50.0),
                             sum(1 for d in near if d <= 5.0), s_both])
                labels.append(int(i in lab[c_])); groups.append(scene[st]); chan.append(c_)
    for c_ in ("camera", "lidar"):
        n, ok = check[c_]
        if ok / n < 0.99:
            raise SystemExit(f"REFUSED: labeler does not reproduce the validated matcher on {c_}")
    return np.array(rows), np.array(labels), np.array(groups), np.array(chan)


class Boosted:
    def __init__(self, max_iter=None):
        self.max_iter = max_iter
    def get_params(self, deep=True):
        return {"max_iter": self.max_iter}
    def set_params(self, **p):
        self.max_iter = p.get("max_iter", self.max_iter); return self
    def fit(self, X, y):
        self.m = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, random_state=SEED).fit(X, y)
        self.classes_ = self.m.classes_; return self
    def predict_proba(self, X):
        return self.m.predict_proba(X)
    def predict(self, X):
        return self.m.predict(X)
    def __sklearn_tags__(self):
        from sklearn.utils import Tags, ClassifierTags, TargetTags
        return Tags(estimator_type="classifier", target_tags=TargetTags(required=True), classifier_tags=ClassifierTags())


def design(X, cols):
    one_hot = np.eye(len(aa.CLASSES))[X[:, 2].astype(int)]
    base = X[:, [c for c in cols if c != 2]]
    return np.hstack([base, one_hot]) if 2 in cols else base


def fit(D, y):
    return CalibratedClassifierCV(Boosted(), method="isotonic", cv=5).fit(D, y)


def main():
    gt = json.load(open(aa.GT)); scene = aa.scenes_from_meta()
    OWN, ALL = [0, 1, 2, 3], list(range(10))
    data = {label: build_rows(gt, ch, score, scene) for label, ch, score in CONFIGS}
    X1, y1, g1, c1 = data[CONFIGS[0][0]]
    got = (len(y1), int((c1 == "camera").sum()), int((c1 == "lidar").sum()))
    print("=" * 92)
    print("RESULT AG - sensor monitor transfer: boosted per-object monitor fitted once on P1, read on P2, P3, P4")
    print(f"self-check against Result AA on P1: rows {got} expected {EXPECT_P1}")
    print("=" * 92)
    if got != EXPECT_P1:
        print("REFUSED: row construction does not reproduce Result AA"); return 1
    rng = np.random.RandomState(SEED)
    sc_ids = np.unique(g1); rng.shuffle(sc_ids)
    te_sc = set(sc_ids[: int(0.4 * len(sc_ids))])
    tr1 = np.where(np.array([g not in te_sc for g in g1]))[0]
    mon_own = fit(design(X1[tr1], OWN), y1[tr1])
    mon_all = fit(design(X1[tr1], ALL), y1[tr1])
    for label, ch, score in CONFIGS:
        X, y, g, c = data[label]
        te = np.where(np.array([gg in te_sc for gg in g]))[0]; tr = np.where(np.array([gg not in te_sc for gg in g]))[0]
        iso = IsotonicRegression(out_of_bounds="clip").fit(X[tr, 0], y[tr])
        p_naive = iso.predict(X[te, 0])
        p_own = mon_own.predict_proba(design(X[te], OWN))[:, 1]
        p_all = mon_all.predict_proba(design(X[te], ALL))[:, 1]
        ceil = fit(design(X[tr], ALL), y[tr]).predict_proba(design(X[te], ALL))[:, 1]
        tag = "in-domain (fitted on P1 training scenes)" if label.startswith("P1") else "TRANSFER, no refit"
        print(f"\n  {label}  [{tag}]  held-out scenes, n = {len(te)}, real {100*y[te].mean():.1f}%")
        print(f"    {'estimator':<44}{'AUC':>8}{'Brier':>9}{'ECE':>8}")
        for name, p in (("score alone, calibrated on target", p_naive), ("P1 monitor, own features", p_own),
                        ("P1 monitor, own + context", p_all), ("in-domain ceiling, own + context, refit", ceil)):
            print(f"    {name:<44}{roc_auc_score(y[te], p):>8.3f}{brier_score_loss(y[te], p):>9.3f}{aa.ece(y[te], p):>8.3f}")
        for ch_ in ("camera", "lidar"):
            m = c[te] == ch_
            print(f"      {ch_}-only (n={m.sum()}): P1 own+context AUC {roc_auc_score(y[te][m], p_all[m]):.3f}, "
                  f"ceiling {roc_auc_score(y[te][m], ceil[m]):.3f}, score alone {roc_auc_score(y[te][m], p_naive[m]):.3f}")
    print("\n" + "-" * 92)
    print("NON-CLAIMS: released detector outputs on the public nuScenes validation split, retained as")
    print("proposed. Transfer is across detector pairs that share the nuScenes training split and, in")
    print("P2 and P3, share one channel with P1. One boosted model class, no tuning. Descriptive, not a")
    print("safety determination. No detector is executed. No released 1.2 byte is involved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
