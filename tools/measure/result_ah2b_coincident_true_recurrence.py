"""Result AH2b: the reference Result AH2 was missing, coincident TRUE detections' recurrence.

An adversarial reading of Result AH2 pointed out that its reference rates (static annotated
objects 60.5 percent, true camera detections 76.9 percent) are single-channel recurrences, while a
coincident ghost recurs only if BOTH channels re-fire within 2 m of the same map location half a
second later. The fair reference is the recurrence of coincident TRUE detections: a camera true
detection with a lidar true detection within 2 m, recurring as a coincident true pair in the next
keyframe. If coincident ghosts recur far below coincident true pairs, the momentary reading
stands; if they recur about as often, the AH2 gap was a conjunction penalty, not evidence.
Definitions and the recurrence rule are those of Result AH2, imported unchanged; only the two
comparison sets are added. Scene-clustered bootstrap band. Seeded.
"""
import importlib.util
import json
import pathlib
import sys
from collections import defaultdict

import numpy as np
from scipy.spatial import cKDTree

here = pathlib.Path(__file__).parent
spec = importlib.util.spec_from_file_location("ah2", here / "result_ah2_ghost_persistence.py")
ah2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(ah2)
aa, SCORE, R, B, SEED, CH = ah2.aa, ah2.SCORE, ah2.R, ah2.B, ah2.SEED, ah2.CH


def main():
    aa.SCORE = SCORE
    gt = json.load(open(aa.GT)); scene = aa.scenes_from_meta()
    dets = {k: aa.detections(v) for k, v in CH.items()}
    gt_by, ts = defaultdict(list), {}
    for o in gt:
        gt_by[o["sample_token"]].append(o); ts[o["sample_token"]] = o["ts_us"]
    by_scene = defaultdict(list)
    for st in gt_by:
        by_scene[scene[st]].append(st)
    for toks in by_scene.values():
        toks.sort(key=lambda s: ts[s])
    info = {}
    for st, objs in gt_by.items():
        tree = cKDTree(np.array([o["xy"] for o in objs]))
        sets = {}
        for ch in ("camera", "lidar"):
            D = dets[ch].get(st, [])
            P = np.array([[x, y] for _, _, x, y in D]) if D else np.zeros((0, 2))
            d = tree.query(P, k=1)[0] if len(P) else np.zeros(0)
            sets[ch] = (P[d > R].reshape(-1, 2), P[d <= R].reshape(-1, 2))   # (ghosts, true)
        def coinc(A, Bp):
            if len(A) == 0 or len(Bp) == 0:
                return np.zeros((0, 2))
            t = cKDTree(Bp); return np.array([a for a in A if t.query_ball_point(a, R)]).reshape(-1, 2)
        info[st] = {"co_ghost": coinc(sets["camera"][0], sets["lidar"][0]), "co_true": coinc(sets["camera"][1], sets["lidar"][1]),
                    "cam_true": sets["camera"][1], "lid_true": sets["lidar"][1]}
    rows = []
    for sc, toks in by_scene.items():
        for i in range(len(toks) - 1):
            st, nx = toks[i], toks[i + 1]
            if ts[nx] - ts[st] > 1_000_000:
                continue
            a, b = info[st], info[nx]
            def rec(points, target):
                if len(points) == 0:
                    return (0, 0)
                if len(target) == 0:
                    return (len(points), 0)
                t = cKDTree(target); return (len(points), int(sum(1 for p in points if t.query_ball_point(p, R))))
            rows.append((sc, "coincident ghosts (AH2)") + rec(a["co_ghost"], b["co_ghost"]))
            rows.append((sc, "coincident TRUE detections") + rec(a["co_true"], b["co_true"]))
            rows.append((sc, "true camera detections, single channel") + rec(a["cam_true"], b["cam_true"]))
            rows.append((sc, "true lidar detections, single channel") + rec(a["lid_true"], b["lid_true"]))
    rows = np.array(rows, dtype=object); rng = np.random.RandomState(SEED); uniq = sorted(by_scene)
    print("=" * 92)
    print("RESULT AH2b - recurrence of coincident TRUE detections, the reference Result AH2 lacked")
    print(f"camera=Mapillary lidar=Megvii at score >= {SCORE}; recurrence within {R} m in the next keyframe; {len(uniq)} scenes; scene-clustered bootstrap B = {B}")
    print("=" * 92)
    print(f"\n  {'set':<42}{'items':>9}{'recur next keyframe':>22}{'95% band':>18}")
    for k in ("coincident ghosts (AH2)", "coincident TRUE detections", "true camera detections, single channel", "true lidar detections, single channel"):
        m = rows[:, 1] == k; n = rows[m, 2].astype(int); r = rows[m, 3].astype(int); sc = rows[m, 0]
        idx = {s: np.where(sc == s)[0] for s in uniq}; bs = []
        for _ in range(B):
            pick = rng.choice(len(uniq), len(uniq), replace=True); sel = np.concatenate([idx[uniq[j]] for j in pick])
            bs.append(r[sel].sum() / n[sel].sum() if n[sel].sum() else np.nan)
        lo, hi = np.nanpercentile(bs, [2.5, 97.5])
        print(f"  {k:<42}{n.sum():>9}{100*r.sum()/n.sum():>21.1f}%  [{100*lo:.1f}, {100*hi:.1f}]")
    print("\n" + "-" * 92)
    print("NON-CLAIMS: released detector outputs on the public nuScenes validation split, retained as")
    print("proposed. Recurrence separates persistent from momentary, not real from artifactual. One pair,")
    print("one operating point. Not a safety determination. No detector is executed. No released 1.2 byte.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
