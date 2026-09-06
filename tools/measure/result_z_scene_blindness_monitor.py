"""Result Z: a scene-level joint-blindness monitor from sensor outputs alone.

Result V built a coupling-aware monitor for an LLM jury and Result X showed it transfers across
juries. The program has asserted, without testing, that the same form applies to two sensors. This
is that test, on the driving channels themselves.

The question a fused perception stack cannot answer from its own outputs is how many present
objects BOTH sensors are blind to right now. That count is invisible at runtime by construction. A
monitor can still estimate it, from what the two channels do report: how many detections each
channel makes, how many of them agree, how confident the agreeing and disagreeing detections are.
The coupling the program measured (Results L to R) is exactly what makes those output patterns
informative about the invisible count.

  channels: Mapillary (camera) and Megvii (lidar), released nuScenes val predictions, at the
            program's 0.30 operating point
  unit:     one keyframe (sample). Features from the two channels' detections in that sample only.
  target:   the number of annotated objects in that sample that both channels missed, where a
            miss is the validated per-object matcher (matched_*.json, gated at published mAP)
            finding no detection at or above 0.30 within 2 m.
  split:    scene-clustered, from the nuScenes scene table read directly out of the pinned
            metadata archive meta.tgz (SHA-256 db48746b...) at the repository root. The cache
            carries no scene token. A timestamp-gap segmentation is computed as a cross-check and
            every scene must lie inside one segment, or the run is refused.
  model:    Poisson regression on standardized features, fitted on training scenes only.
  baselines: (a) constant: the training-set mean count; (b) proportional: a scalar fraction of the
            number of objects the fusion reports (fitted on training scenes). Baseline (b) is the
            best a stack can do that assumes what it sees is what there is.
  metrics:  held-out Spearman and Pearson correlation, mean absolute error, calibration by
            predicted-count quintile, and ROC AUC for flagging the top-quartile blind frames.
            Five-fold grouped cross-validation over scenes reports mean and spread.
Seeded; re-runs byte-identically.
"""
import json
import math
import sys
import tarfile
from collections import defaultdict

import numpy as np
from scipy.stats import spearmanr, pearsonr
from sklearn.linear_model import PoissonRegressor
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

SCORE = 0.30
MATCH_M = 2.0
SEED = 20260906
GT = "gt_val_cache.json"
CH = {"camera": ("matched_mapillary.json", "predictions/mapillary_val.json"),
      "lidar": ("matched_megvii.json", "predictions/megvii_val.json")}
CLASSES = ["car", "truck", "bus", "trailer", "construction_vehicle", "pedestrian", "motorcycle",
           "bicycle", "traffic_cone", "barrier"]


def load_matched(path):
    m = json.load(open(path))["matched_at_2m"]
    out = {}
    for cls, d in m.items():
        for gi, s in d.items():
            out[int(gi)] = float(s)
    return out


def detections(path):
    r = json.load(open(path))["results"]
    out = {}
    for st, boxes in r.items():
        out[st] = [(b["detection_name"], float(b["detection_score"]), b["translation"][0], b["translation"][1])
                   for b in boxes if float(b["detection_score"]) >= SCORE and b["detection_name"] in CLASSES]
    return out


def cross_match(da, db):
    """Greedy same-class center-distance matching of channel A detections to channel B detections
    within MATCH_M, highest scores first. Output-only: no ground truth is touched."""
    used = set()
    pairs = []
    by_cls_b = defaultdict(list)
    for j, (c, s, x, y) in enumerate(db):
        by_cls_b[c].append(j)
    for i in sorted(range(len(da)), key=lambda i: -da[i][1]):
        c, s, x, y = da[i]
        best, bd = None, MATCH_M
        for j in by_cls_b[c]:
            if j in used:
                continue
            d = math.hypot(x - db[j][2], y - db[j][3])
            if d < bd:
                best, bd = j, d
        if best is not None:
            used.add(best)
            pairs.append((i, best))
    return pairs


def features(da, db):
    pairs = cross_match(da, db)
    ia = {i for i, _ in pairs}
    ib = {j for _, j in pairs}
    n_a, n_b, n_both = len(da), len(db), len(pairs)
    n_only_a, n_only_b = n_a - n_both, n_b - n_both
    n_either = n_a + n_b - n_both
    sa = np.array([s for _, s, _, _ in da]) if da else np.zeros(0)
    sb = np.array([s for _, s, _, _ in db]) if db else np.zeros(0)
    s_both = np.array([min(da[i][1], db[j][1]) for i, j in pairs]) if pairs else np.zeros(0)
    s_only_a = np.array([da[i][1] for i in range(n_a) if i not in ia]) if n_only_a else np.zeros(0)
    s_only_b = np.array([db[j][1] for j in range(n_b) if j not in ib]) if n_only_b else np.zeros(0)
    m = lambda v: float(v.mean()) if len(v) else 0.0
    agree = n_both / n_either if n_either else 0.0
    vru_only = sum(1 for i in range(n_a) if i not in ia and da[i][0] in ("pedestrian", "bicycle", "motorcycle")) + \
               sum(1 for j in range(n_b) if j not in ib and db[j][0] in ("pedestrian", "bicycle", "motorcycle"))
    return [n_a, n_b, n_both, n_only_a, n_only_b, n_either, agree, m(sa), m(sb), m(s_both),
            m(s_only_a), m(s_only_b), float((np.concatenate([sa, sb]) < 0.5).mean()) if n_either else 0.0,
            vru_only], n_either


def scenes_from_meta(path="meta.tgz"):
    """sample_token -> scene_token from the nuScenes tables inside the pinned archive."""
    with tarfile.open(path, "r:gz") as tf:
        samples = json.load(tf.extractfile("v1.0-trainval/sample.json"))
    return {s["token"]: s["scene_token"] for s in samples}, {s["token"]: s["timestamp"] for s in samples}


def scenes_from_timestamps(sample_ts):
    order = sorted(sample_ts, key=lambda st: sample_ts[st])
    scene, sid, prev = {}, 0, None
    for st in order:
        if prev is not None and sample_ts[st] - prev > 2_000_000:
            sid += 1
        scene[st] = sid
        prev = sample_ts[st]
    return scene


def main():
    gt = json.load(open(GT))
    matched = {k: load_matched(v[0]) for k, v in CH.items()}
    dets = {k: detections(v[1]) for k, v in CH.items()}
    sample_ts = {}
    per_sample_gt = defaultdict(list)
    for gi, o in enumerate(gt):
        per_sample_gt[o["sample_token"]].append(gi)
        sample_ts[o["sample_token"]] = o["ts_us"]
    scene_tok, ts_all = scenes_from_meta()
    scene = {st: scene_tok[st] for st in sample_ts}
    n_scenes = len(set(scene.values()))
    # cross-check over every validation keyframe the detectors were scored on, including the
    # keyframes with no annotated object (absent from the cache), so no false gap appears
    val_tokens = set(dets["lidar"].keys()) | set(dets["camera"].keys())
    segment = scenes_from_timestamps({st: ts_all[st] for st in val_tokens})
    n_seg = len(set(segment.values()))
    seg_of_scene = defaultdict(set)
    for st in val_tokens:
        seg_of_scene[scene_tok[st]].add(segment[st])
    split_scenes = sum(1 for v in seg_of_scene.values() if len(v) > 1)
    print("=" * 92)
    print("RESULT Z - scene-level joint-blindness monitor from camera and lidar outputs alone")
    print(f"channels camera=Mapillary lidar=Megvii at score >= {SCORE}; {len(val_tokens)} keyframes scored, "
          f"{len(per_sample_gt)} with annotated objects; {len(gt)} objects; {n_scenes} scenes from the scene "
          f"table; {n_seg} timestamp-gap segments over all keyframes as a cross-check, "
          f"{split_scenes} scenes straddle a segment")
    print("=" * 92)
    if n_scenes != 150 or split_scenes != 0:
        print("REFUSED: scene table does not give the 150 validation scenes nested inside timestamp segments")
        return 1

    X, y, y_elig, groups, n_seen, toks = [], [], [], [], [], []
    for st, gis in per_sample_gt.items():
        da, db = dets["camera"].get(st, []), dets["lidar"].get(st, [])
        f, n_either = features(da, db)
        jm = sum(1 for gi in gis if matched["camera"].get(gi, 0.0) < SCORE and matched["lidar"].get(gi, 0.0) < SCORE)
        jm_e = sum(1 for gi in gis if (gt[gi]["nl"] + gt[gi]["nr"]) > 0 and matched["camera"].get(gi, 0.0) < SCORE and matched["lidar"].get(gi, 0.0) < SCORE)
        X.append(f); y.append(jm); y_elig.append(jm_e); groups.append(scene[st]); n_seen.append(n_either); toks.append(st)
    X, y, y_elig, groups, n_seen = map(np.array, (X, y, y_elig, groups, n_seen))
    print(f"\n  joint-miss count per keyframe: mean {y.mean():.2f}, median {np.median(y):.0f}, max {y.max()}, "
          f"zero in {100*(y==0).mean():.1f}% of keyframes; objects per keyframe mean {np.mean([len(v) for v in per_sample_gt.values()]):.1f}; "
          f"fusion reports {n_seen.mean():.1f} objects per keyframe")
    print(f"  (eligible-only target, objects with any lidar or radar return: mean {y_elig.mean():.2f})")

    def fit_eval(tr, te, target):
        sc = StandardScaler().fit(X[tr])
        mon = PoissonRegressor(alpha=1e-3, max_iter=2000).fit(sc.transform(X[tr]), target[tr])
        p = mon.predict(sc.transform(X[te]))
        const = np.full(len(te), target[tr].mean())
        k = target[tr].sum() / max(n_seen[tr].sum(), 1)
        prop = k * n_seen[te]
        t = target[te]
        top = t >= np.quantile(target[tr], 0.75)
        out = {}
        for name, q in (("constant", const), ("proportional", prop), ("monitor", p)):
            varies = float(np.ptp(q)) > 0.0
            out[name] = (float(spearmanr(q, t).correlation) if varies else 0.0,
                         float(pearsonr(q, t)[0]) if varies else 0.0,
                         float(np.abs(q - t).mean()),
                         float(roc_auc_score(top, q)) if varies and 0 < top.mean() < 1 else 0.5)
        return out, p, t

    rng = np.random.RandomState(SEED)
    sc_ids = np.unique(groups); rng.shuffle(sc_ids)
    te_sc = set(sc_ids[: int(0.4 * len(sc_ids))])
    te_mask = np.array([g in te_sc for g in groups])
    te = np.where(te_mask)[0]; tr = np.where(~te_mask)[0]
    for label, target in (("all annotated objects", y), ("eligible objects only", y_elig)):
        out, p, t = fit_eval(tr, te, target)
        print(f"\n  held-out scenes ({len(te_sc)} of {len(sc_ids)}; {len(te)} keyframes), target = joint misses over {label}:")
        print(f"    {'estimator':<16}{'Spearman':>10}{'Pearson':>9}{'MAE':>8}{'AUC top-quartile':>18}")
        for name in ("constant", "proportional", "monitor"):
            s, r, mae, auc = out[name]
            print(f"    {name:<16}{s:>10.3f}{r:>9.3f}{mae:>8.2f}{auc:>18.3f}")
        if label.startswith("all"):
            order = np.argsort(p)
            bands = []
            for q in range(5):
                idx = order[q*len(order)//5:(q+1)*len(order)//5]
                bands.append(f"{p[idx].mean():.1f}/{t[idx].mean():.1f}")
            print(f"    calibration by predicted quintile, predicted/actual joint misses: {'  '.join(bands)}")

    print("\n  five-fold grouped cross-validation over scenes, target = all annotated objects:")
    rows = defaultdict(list)
    for trf, tef in GroupKFold(n_splits=5).split(X, y, groups):
        out, _, _ = fit_eval(trf, tef, y)
        for name in ("constant", "proportional", "monitor"):
            rows[name].append(out[name])
    for name in ("constant", "proportional", "monitor"):
        a = np.array(rows[name])
        print(f"    {name:<16}Spearman {a[:,0].mean():.3f} +/- {a[:,0].std():.3f}   MAE {a[:,2].mean():.2f} +/- {a[:,2].std():.2f}   "
              f"AUC {a[:,3].mean():.3f} +/- {a[:,3].std():.3f}")

    sc = StandardScaler().fit(X[tr])
    mon = PoissonRegressor(alpha=1e-3, max_iter=2000).fit(sc.transform(X[tr]), y[tr])
    names = ["n_cam", "n_lidar", "n_both", "n_only_cam", "n_only_lidar", "n_either", "agreement", "score_cam",
             "score_lidar", "score_both", "score_only_cam", "score_only_lidar", "frac_low_score", "vru_disagreements"]
    print("\n  monitor coefficients on standardized features (log rate):")
    for n, c in sorted(zip(names, mon.coef_), key=lambda z: -abs(z[1])):
        print(f"    {n:<18}{c:>+8.3f}")

    print("\n" + "-" * 92)
    print("NON-CLAIMS: two released detectors on the public nuScenes validation split, retained as")
    print("proposed. The target counts annotated objects both channels missed, a lower bound on what")
    print("is present. Scenes come from the scene table in the pinned metadata archive. Descriptive,")
    print("not a safety determination, not a certificate about any deployed system. A Poisson")
    print("regression is fitted; no detector is executed. No released 1.2 byte is involved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
