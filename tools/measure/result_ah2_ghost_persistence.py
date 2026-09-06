"""Result AH2: are coincident ghosts persistent structure or momentary shared hallucination?

Result AH found camera and lidar ghosts coincide six-fold beyond a same-road, different-instant
null and named its own biggest threat: a real object the annotation missed makes both channels'
true reports look like coincident ghosts. Such an object is static in map coordinates across
consecutive keyframes (0.5 s apart), so a coincident ghost caused by it recurs at the same map
location in the next keyframe. A shared momentary hallucination does not. This measures the
recurrence rate of coincident ghosts against the recurrence rate of three comparison sets, all in
global map coordinates within the same scene:

  coincident ghosts:   camera ghost with a lidar ghost within 2 m (Result AH definition)
  lone camera ghosts:  camera ghost with no lidar ghost within 2 m
  lone lidar ghosts:   lidar ghost with no camera ghost within 2 m
  true detections:     camera detections with an annotated object within 2 m (static and moving)
  static true objects: annotated objects whose annotated position moves under 0.5 m to the next
                       keyframe (a ceiling for how persistent a static real thing looks)

Recurrence: the same kind of item (for ghosts, a coincident ghost pair; for lone ghosts, a ghost
of the same channel; for true detections, a camera detection) exists within 2 m of the same map
location in the next keyframe of the same scene. Scene-clustered bootstrap bands. Seeded.
"""
import importlib.util
import json
import pathlib
import sys
from collections import defaultdict

import numpy as np
from scipy.spatial import cKDTree

here = pathlib.Path(__file__).parent
spec = importlib.util.spec_from_file_location("aa", here / "result_aa_disagreement_monitor.py")
aa = importlib.util.module_from_spec(spec); spec.loader.exec_module(aa)
SCORE, R, B, SEED = 0.30, 2.0, 500, 20260906
CH = {"camera": "predictions/mapillary_val.json", "lidar": "predictions/megvii_val.json"}


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
    # per keyframe: ghost sets, coincident pairs, true detections, static annotated objects
    info = {}
    for st, objs in gt_by.items():
        G = np.array([o["xy"] for o in objs]); tree = cKDTree(G)
        out = {}
        for ch in ("camera", "lidar"):
            D = dets[ch].get(st, [])
            P = np.array([[x, y] for _, _, x, y in D]) if D else np.zeros((0, 2))
            d = tree.query(P, k=1)[0] if len(P) else np.zeros(0)
            out[ch] = (P, d > R)
        Pc, gc = out["camera"]; Pl, gl = out["lidar"]
        cam_g, lid_g, cam_t = Pc[gc], Pl[gl], Pc[~gc]
        tl = cKDTree(lid_g) if len(lid_g) else None
        tc = cKDTree(cam_g) if len(cam_g) else None
        co = np.array([a for a in cam_g if tl is not None and tl.query_ball_point(a, R)]) if len(cam_g) else np.zeros((0, 2))
        lone_c = np.array([a for a in cam_g if tl is None or not tl.query_ball_point(a, R)]) if len(cam_g) else np.zeros((0, 2))
        lone_l = np.array([b for b in lid_g if tc is None or not tc.query_ball_point(b, R)]) if len(lid_g) else np.zeros((0, 2))
        info[st] = {"co": co.reshape(-1, 2), "lone_c": lone_c.reshape(-1, 2), "lone_l": lone_l.reshape(-1, 2),
                    "cam_t": cam_t.reshape(-1, 2), "cam_all": Pc, "cam_g": cam_g.reshape(-1, 2), "lid_g": lid_g.reshape(-1, 2),
                    "inst": {o["instance_token"]: np.array(o["xy"]) for o in objs}}
    # static annotated objects: instance present next keyframe within 0.5 m
    rows = []  # (scene, kind, n, recurred)
    kinds = ("coincident ghosts", "lone camera ghosts", "lone lidar ghosts", "true camera detections", "static annotated objects")
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
            rows.append((sc, kinds[0]) + rec(a["co"], b["co"]))
            rows.append((sc, kinds[1]) + rec(a["lone_c"], b["cam_g"]))
            rows.append((sc, kinds[2]) + rec(a["lone_l"], b["lid_g"]))
            rows.append((sc, kinds[3]) + rec(a["cam_t"], b["cam_all"]))
            static = [p for k, p in a["inst"].items() if k in b["inst"] and np.hypot(*(b["inst"][k] - p)) < 0.5]
            # static objects "recur" if a camera detection of any kind sits within 2 m next keyframe: the visibility ceiling
            rows.append((sc, kinds[4]) + rec(np.array(static).reshape(-1, 2), b["cam_all"]))
    rows = np.array(rows, dtype=object)
    rng = np.random.RandomState(SEED)
    print("=" * 92)
    print("RESULT AH2 - persistence of coincident ghosts across consecutive keyframes (0.5 s), map coordinates")
    print(f"camera=Mapillary lidar=Megvii at score >= {SCORE}; ghost and coincidence as in Result AH; {len(by_scene)} scenes")
    print(f"scene-clustered bootstrap, B = {B}, seed {SEED}")
    print("=" * 92)
    print(f"\n  {'set':<28}{'items':>9}{'recur within 2 m next keyframe':>34}{'95% band':>18}")
    uniq = sorted(by_scene)
    for k in kinds:
        m = rows[:, 1] == k
        n = rows[m, 2].astype(int); r = rows[m, 3].astype(int); sc = rows[m, 0]
        point = r.sum() / n.sum()
        idx = {s: np.where(sc == s)[0] for s in uniq}
        bs = []
        for _ in range(B):
            pick = rng.choice(len(uniq), len(uniq), replace=True)
            sel = np.concatenate([idx[uniq[j]] for j in pick])
            bs.append(r[sel].sum() / n[sel].sum() if n[sel].sum() else np.nan)
        lo, hi = np.nanpercentile(bs, [2.5, 97.5])
        print(f"  {k:<28}{n.sum():>9}{100*point:>33.1f}%  [{100*lo:.1f}, {100*hi:.1f}]")
    print("\n" + "-" * 92)
    print("NON-CLAIMS: released detector outputs on the public nuScenes validation split, retained as")
    print("proposed. Recurrence in map coordinates over 0.5 s cannot separate a static unannotated")
    print("object from a static reflective artifact both channels hallucinate at; it separates persistent")
    print("from momentary. Ego-static keyframes are included (map coordinates do not depend on ego")
    print("motion). One pair, one operating point. Not a safety determination. No detector is executed.")
    print("No released 1.2 byte is involved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
