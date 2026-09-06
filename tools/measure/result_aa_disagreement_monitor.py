"""Result AA: a per-object disagreement monitor on the driving channels.

Result Z found that at the scene level the coupling-aware monitor form does not beat density,
because a jointly missed object leaves no output. This changes the estimand to the one place a
runtime redundancy question does leave an output: a DISAGREEMENT, an object reported by exactly
one of the two channels. The stack must decide whether to trust it. The question is whether
cross-channel context, what the other channel reports nearby and how much the channels agree in
this keyframe, predicts whether the lone detection is real, beyond the detector's own confidence.

  channels: Mapillary (camera) and Megvii (lidar) released nuScenes val predictions at 0.30
  unit:     one single-channel detection (no same-class detection of the other channel within 2 m)
  label:    real if an annotated object of the same class lies within 2 m, one-to-one, assigned
            greedily by score across the keyframe. This labeling matcher is self-checked against
            the validated per-object matcher: every annotated object the validated matcher scored
            at or above 0.30 must correspond to a detection this labeler marks real.
  features: own: score, class, distance from ego, channel.
            context (output-only): keyframe agreement fraction, counts of single-channel
            detections per channel, distance to the nearest other-channel detection of any class,
            number of other-channel detections within 5 m, mean score of agreeing pairs.
  models:   (a) score alone, isotonic-calibrated: the detector's own confidence;
            (b) own features only, logistic + isotonic: no cross-channel context;
            (c) own + context, logistic + isotonic: the coupling-aware monitor.
  split:    scene-clustered from the scene table in the pinned meta.tgz; 60 held-out scenes, then
            five-fold grouped cross-validation. Metrics: AUC, Brier, ECE, per channel.
Seeded; re-runs byte-identically.
"""
import json
import math
import sys
import tarfile
from collections import defaultdict

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SCORE, MATCH_M, SEED = 0.30, 2.0, 20260906
GT = "gt_val_cache.json"
CH = {"camera": ("matched_mapillary.json", "predictions/mapillary_val.json"),
      "lidar": ("matched_megvii.json", "predictions/megvii_val.json")}
CLASSES = ["car", "truck", "bus", "trailer", "construction_vehicle", "pedestrian", "motorcycle",
           "bicycle", "traffic_cone", "barrier"]
CLS_IDX = {c: i for i, c in enumerate(CLASSES)}


def load_matched(path):
    out = {}
    for cls, d in json.load(open(path))["matched_at_2m"].items():
        for gi, s in d.items():
            out[int(gi)] = float(s)
    return out


def detections(path):
    out = {}
    for st, boxes in json.load(open(path))["results"].items():
        out[st] = [(b["detection_name"], float(b["detection_score"]), b["translation"][0], b["translation"][1])
                   for b in boxes if float(b["detection_score"]) >= SCORE and b["detection_name"] in CLASSES]
    return out


def greedy_match(src, dst, same_class=True):
    """Greedy one-to-one center-distance matching within MATCH_M, highest source score first.
    src rows (cls, score, x, y); dst rows (cls, x, y). Returns dict src_index -> dst_index."""
    used, out = set(), {}
    by_cls = defaultdict(list)
    for j, (c, x, y) in enumerate(dst):
        by_cls[c if same_class else "*"].append(j)
    for i in sorted(range(len(src)), key=lambda i: -src[i][1]):
        c, s, x, y = src[i]
        best, bd = None, MATCH_M
        for j in by_cls[c if same_class else "*"]:
            if j in used:
                continue
            d = math.hypot(x - dst[j][1], y - dst[j][2])
            if d < bd:
                best, bd = j, d
        if best is not None:
            used.add(best); out[i] = best
    return out


def scenes_from_meta(path="meta.tgz"):
    with tarfile.open(path, "r:gz") as tf:
        samples = json.load(tf.extractfile("v1.0-trainval/sample.json"))
    return {s["token"]: s["scene_token"] for s in samples}


def ece(y, p, bins=10):
    edges = np.linspace(0, 1, bins + 1); e = 0.0
    for b in range(bins):
        m = (p >= edges[b]) & (p < edges[b + 1] if b < bins - 1 else p <= edges[b + 1])
        if m.sum():
            e += abs(y[m].mean() - p[m].mean()) * m.sum() / len(y)
    return e


def main():
    gt = json.load(open(GT))
    matched = {k: load_matched(v[0]) for k, v in CH.items()}
    dets = {k: detections(v[1]) for k, v in CH.items()}
    scene = scenes_from_meta()
    gt_by_sample, ego = defaultdict(list), {}
    for gi, o in enumerate(gt):
        gt_by_sample[o["sample_token"]].append(gi)
        ego[o["sample_token"]] = o["ego_xy"]

    rows, labels, groups, chan_of, check = [], [], [], [], defaultdict(lambda: [0, 0])
    for st in sorted(gt_by_sample):
        gis = gt_by_sample[st]
        gt_rows = [(gt[gi]["cls"], gt[gi]["xy"][0], gt[gi]["xy"][1]) for gi in gis]
        da, db = dets["camera"].get(st, []), dets["lidar"].get(st, [])
        # cross-channel agreement (output-only)
        ab = greedy_match(da, [(c, x, y) for c, s, x, y in db])
        agreed_a, agreed_b = set(ab), set(ab.values())
        n_both = len(ab); n_either = len(da) + len(db) - n_both
        agree = n_both / n_either if n_either else 0.0
        s_both = float(np.mean([min(da[i][1], db[j][1]) for i, j in ab.items()])) if ab else 0.0
        n_only = {"camera": len(da) - n_both, "lidar": len(db) - n_both}
        # labels from the labeling matcher, and its self-check against the validated matcher
        lab = {"camera": greedy_match(da, gt_rows), "lidar": greedy_match(db, gt_rows)}
        for ch, d, l in (("camera", da, lab["camera"]), ("lidar", db, lab["lidar"])):
            real_gi = {gis[j] for j in l.values()}
            for gi in gis:
                if matched[ch].get(gi, 0.0) >= SCORE:
                    check[ch][0] += 1
                    check[ch][1] += int(gi in real_gi)
        ex, ey = ego[st]
        for ch, own, other, agreed in (("camera", da, db, agreed_a), ("lidar", db, da, agreed_b)):
            for i, (c, s, x, y) in enumerate(own):
                if i in agreed:
                    continue
                dist_ego = math.hypot(x - ex, y - ey)
                near = [math.hypot(x - ox, y - oy) for _, _, ox, oy in other]
                nearest = min(near) if near else 50.0
                within5 = sum(1 for d in near if d <= 5.0)
                rows.append([s, dist_ego, CLS_IDX[c], 1.0 if ch == "lidar" else 0.0,
                             agree, n_only["camera"], n_only["lidar"], min(nearest, 50.0), within5, s_both])
                labels.append(int(i in lab[ch]))
                groups.append(scene[st]); chan_of.append(ch)
    X, y, groups, chan_of = np.array(rows), np.array(labels), np.array(groups), np.array(chan_of)

    print("=" * 92)
    print("RESULT AA - per-object disagreement monitor: is a single-channel detection real?")
    print(f"camera=Mapillary lidar=Megvii at score >= {SCORE}; {len(gt_by_sample)} keyframes; "
          f"{len(y)} single-channel detections ({(chan_of=='camera').sum()} camera-only, {(chan_of=='lidar').sum()} lidar-only); "
          f"real in {100*y.mean():.1f}% (camera-only {100*y[chan_of=='camera'].mean():.1f}%, lidar-only {100*y[chan_of=='lidar'].mean():.1f}%)")
    for ch in ("camera", "lidar"):
        n, ok = check[ch]
        print(f"  labeler self-check, {ch}: {ok} of {n} objects the validated matcher scored >= {SCORE} are marked real by the labeler ({100*ok/n:.2f}%)")
    print("=" * 92)
    for ch in ("camera", "lidar"):
        n, ok = check[ch]
        if ok / n < 0.99:
            print("REFUSED: labeling matcher does not reproduce the validated matcher")
            return 1

    OWN = [0, 1, 2, 3]; ALL = list(range(X.shape[1]))
    one_hot = np.eye(len(CLASSES))[X[:, 2].astype(int)]
    def design(cols):
        base = X[:, [c for c in cols if c != 2]]
        return np.hstack([base, one_hot]) if 2 in cols else base

    def fit_eval(tr, te):
        res = {}
        iso = IsotonicRegression(out_of_bounds="clip").fit(X[tr, 0], y[tr])
        res["score alone"] = iso.predict(X[te, 0])
        for name, cols in (("own features", OWN), ("own + context", ALL)):
            D = design(cols)
            base = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000))
            mon = CalibratedClassifierCV(base, method="isotonic", cv=5).fit(D[tr], y[tr])
            res[name] = mon.predict_proba(D[te])[:, 1]
        return res

    rng = np.random.RandomState(SEED)
    sc_ids = np.unique(groups); rng.shuffle(sc_ids)
    te_sc = set(sc_ids[: int(0.4 * len(sc_ids))])
    te_mask = np.array([g in te_sc for g in groups])
    te, tr = np.where(te_mask)[0], np.where(~te_mask)[0]
    res = fit_eval(tr, te)
    for ch in ("camera", "lidar", "both"):
        m = np.ones(len(te), bool) if ch == "both" else (chan_of[te] == ch)
        print(f"\n  held-out scenes ({len(te_sc)} of {len(sc_ids)}), {ch}-only detections, n = {m.sum()}, real {100*y[te][m].mean():.1f}%:")
        print(f"    {'estimator':<16}{'AUC':>8}{'Brier':>9}{'ECE':>8}")
        for name in ("score alone", "own features", "own + context"):
            p = res[name][m]
            print(f"    {name:<16}{roc_auc_score(y[te][m], p):>8.3f}{brier_score_loss(y[te][m], p):>9.3f}{ece(y[te][m], p):>8.3f}")

    print("\n  five-fold grouped cross-validation over scenes, all single-channel detections:")
    acc = defaultdict(list)
    for trf, tef in GroupKFold(n_splits=5).split(X, y, groups):
        r = fit_eval(trf, tef)
        for name, p in r.items():
            acc[name].append((roc_auc_score(y[tef], p), brier_score_loss(y[tef], p), ece(y[tef], p)))
    for name in ("score alone", "own features", "own + context"):
        a = np.array(acc[name])
        print(f"    {name:<16}AUC {a[:,0].mean():.3f} +/- {a[:,0].std():.3f}   Brier {a[:,1].mean():.3f} +/- {a[:,1].std():.3f}   ECE {a[:,2].mean():.3f} +/- {a[:,2].std():.3f}")

    print("\n  context-only signal, held out: AUC of each context feature alone against realness")
    names = ["agreement", "n_only_camera", "n_only_lidar", "nearest_other_channel_m", "other_within_5m", "score_of_agreeing_pairs"]
    for k, nm in zip(range(4, 10), names):
        a = roc_auc_score(y[te], X[te, k]); a = max(a, 1 - a)
        print(f"    {nm:<26}{a:.3f}")

    print("\n" + "-" * 92)
    print("NON-CLAIMS: two released detectors on the public nuScenes validation split, retained as")
    print("proposed. Realness is defined by a same-class annotated object within 2 m, a labeling")
    print("matcher self-checked against the validated per-object matcher. Descriptive, not a safety")
    print("determination, not a certificate about any deployed system. Logistic and isotonic models")
    print("are fitted; no detector is executed. No released 1.2 byte is involved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
