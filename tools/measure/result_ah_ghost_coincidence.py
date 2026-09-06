"""Result AH: ghost-ghost coincidence between the camera and the lidar.

RSS Corollary 3 assumes c-approximate independence for both mistake types, miss-miss and
ghost-ghost, and the register's evidence-cost claim lists "measure ghost-ghost dependence" as its
third unmet condition. Every coefficient in this program so far is a miss coefficient. This is
the first ghost coefficient.

Definitions, stated in advance:
  ghost:        a detection (score >= 0.30, ten classes) with NO annotated object of ANY class
                within 2 m of its center. All annotations count, including the ones the benchmark
                deletes for having no lidar or radar return, so a detection near a real but
                unreturned object is not a ghost. Class-agnostic, so a duplicate or misclassified
                report of a real object is not a ghost either: a ghost asserts an object where
                there is none.
  coincidence:  a camera ghost with a lidar ghost within 2 m (and the reverse conditional).
  observed:     P(lidar ghost within 2 m | camera ghost), pooled over keyframes.
  null:         the same probability when, in each keyframe, the lidar ghosts are rotated about
                the ego position by a uniformly random angle, which keeps every keyframe's lidar
                ghost count and every ghost's range from the ego but destroys any spatial relation
                to the camera ghosts. K = 100 rotations per keyframe, seeded. A second, deterministic
                null rotates by exactly 180 degrees. Ego position comes from the annotation cache
                (a runtime quantity, not ground truth about objects).
                A third, geometry-preserving null takes the lidar ghosts of the SAME scene ten
                keyframes (about 5 s) earlier or later, expressed in that keyframe's ego frame using
                the heading recovered from the ego track, and places them in the current keyframe's
                ego frame: same road, same sensor, a different instant. Persistent shared structure
                (a reflective barrier both channels hallucinate at, or a real object the annotation
                missed) survives this null; an instantaneous shared hallucination does not.
                Keyframes whose ego moved under 0.5 m to the next keyframe have no heading and are
                excluded from this null, with the count reported.
  coefficient:  c_ghost = observed / null, the same form as the miss coefficient.
  band:         scene-clustered bootstrap over keyframes (B = 500) on the ratio of pooled counts,
                scenes from the scene table in the pinned meta.tgz.
Also reported: per camera-ghost class for the two largest classes, the reverse conditional, and a
sanity row that applies the identical machinery to REAL detections (a camera true detection with
a lidar true detection within 2 m), where a large coefficient is expected because real objects
are where real objects are.
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
SCORE, R, K, B, SEED = 0.30, 2.0, 100, 500, 20260906
CH = {"camera": "predictions/mapillary_val.json", "lidar": "predictions/megvii_val.json"}


def main():
    aa.SCORE = SCORE
    gt = json.load(open(aa.GT)); scene = aa.scenes_from_meta()
    dets = {k: aa.detections(v) for k, v in CH.items()}
    gt_xy, ego = defaultdict(list), {}
    for o in gt:
        gt_xy[o["sample_token"]].append(o["xy"]); ego[o["sample_token"]] = o["ego_xy"]
    rng = np.random.RandomState(SEED)
    # ego heading per keyframe from the ego track within each scene, for the time-shift null
    by_scene = defaultdict(list)
    for st in gt_xy:
        by_scene[scene[st]].append(st)
    ts = {o["sample_token"]: o["ts_us"] for o in gt}
    heading, shift_partner = {}, {}
    for sc, toks in by_scene.items():
        toks.sort(key=lambda s: ts[s])
        for i, st in enumerate(toks):
            nxt = toks[i + 1] if i + 1 < len(toks) else None
            prv = toks[i - 1] if i > 0 else None
            ref = nxt or prv
            if ref is None:
                continue
            dx, dy = (ego[ref][0] - ego[st][0], ego[ref][1] - ego[st][1]) if nxt else (ego[st][0] - ego[prv][0], ego[st][1] - ego[prv][1])
            if np.hypot(dx, dy) >= 0.5:
                heading[st] = np.arctan2(dy, dx)
            cands = [toks[j] for j in (i + 10, i - 10) if 0 <= j < len(toks)]
            shift_partner[st] = cands
    n_no_heading = sum(1 for st in gt_xy if st not in heading)
    def to_ego(P, st):
        rel = P - np.array(ego[st]); h = heading[st]; c, s = np.cos(-h), np.sin(-h)
        return np.column_stack([rel[:, 0] * c - rel[:, 1] * s, rel[:, 0] * s + rel[:, 1] * c])
    def from_ego(Q, st):
        h = heading[st]; c, s = np.cos(h), np.sin(h)
        return np.column_stack([Q[:, 0] * c - Q[:, 1] * s, Q[:, 0] * s + Q[:, 1] * c]) + np.array(ego[st])
    ghost_cache = {}
    per = []   # per keyframe: scene, n_cam_ghost, obs_coinc, null_coinc_mean, null180, n_lid_ghost, rev_obs, rev_null, real rows
    cls_rows = defaultdict(lambda: [0, 0.0, 0])
    for st in sorted(gt_xy):
        G = np.array(gt_xy[st]); tree = cKDTree(G)
        ex, ey = ego[st]
        out = {}
        for ch in ("camera", "lidar"):
            D = dets[ch].get(st, [])
            if not D:
                out[ch] = (np.zeros((0, 2)), np.zeros(0, bool), []); continue
            P = np.array([[x, y] for _, _, x, y in D])
            d, _ = tree.query(P, k=1)
            out[ch] = (P, d > R, [c for c, _, _, _ in D])
        Pc, gc, cc = out["camera"]; Pl, gl, _ = out["lidar"]
        cam_g, lid_g = Pc[gc], Pl[gl]
        cam_r, lid_r = Pc[~gc], Pl[~gl]
        def coinc(A, Bp):
            if len(A) == 0 or len(Bp) == 0:
                return 0
            t = cKDTree(Bp); return int(sum(1 for a in A if t.query_ball_point(a, R)))
        def rotated(Bp, theta):
            if len(Bp) == 0:
                return Bp
            rel = Bp - np.array([ex, ey]); c, s = np.cos(theta), np.sin(theta)
            return np.column_stack([rel[:, 0] * c - rel[:, 1] * s, rel[:, 0] * s + rel[:, 1] * c]) + np.array([ex, ey])
        ghost_cache[st] = lid_g
        obs = coinc(cam_g, lid_g)
        null = np.mean([coinc(cam_g, rotated(lid_g, th)) for th in rng.uniform(0, 2 * np.pi, K)]) if len(cam_g) and len(lid_g) else 0.0
        null180 = coinc(cam_g, rotated(lid_g, np.pi))
        rev_obs = coinc(lid_g, cam_g)
        rev_null = np.mean([coinc(lid_g, rotated(cam_g, th)) for th in rng.uniform(0, 2 * np.pi, K)]) if len(cam_g) and len(lid_g) else 0.0
        real_obs = coinc(cam_r, lid_r)
        real_null = np.mean([coinc(cam_r, rotated(lid_r, th)) for th in rng.uniform(0, 2 * np.pi, K)]) if len(cam_r) and len(lid_r) else 0.0
        per.append((scene[st], len(cam_g), obs, null, null180, len(lid_g), rev_obs, rev_null, len(cam_r), real_obs, real_null, st))
        if len(cam_g) and len(lid_g):
            tl = cKDTree(lid_g)
            for a, c in zip(Pc[gc], [c for c, g in zip(cc, gc) if g]):
                cls_rows[c][0] += 1; cls_rows[c][2] += int(bool(tl.query_ball_point(a, R)))
            # class-level null: share of the keyframe null spread across its camera ghosts
            for c in set(c for c, g in zip(cc, gc) if g):
                nc = sum(1 for cc_, g in zip(cc, gc) if g and cc_ == c)
                cls_rows[c][1] += null * nc / len(cam_g)
    # time-shift null, second pass: needs every keyframe's lidar ghosts cached
    shift_obs, shift_null, shift_n = [], [], []
    for row in per:
        st = row[11]
        cam_g_st = None
        D = dets["camera"].get(st, [])
        if D and st in heading:
            P = np.array([[x, y] for _, _, x, y in D]); d, _ = cKDTree(np.array(gt_xy[st])).query(P, k=1); cam_g_st = P[d > R]
        partners = [q for q in shift_partner.get(st, []) if q in heading and q in ghost_cache and len(ghost_cache[q])]
        if cam_g_st is None or len(cam_g_st) == 0 or not partners:
            shift_obs.append(0.0); shift_null.append(0.0); shift_n.append(0.0); continue
        vals = []
        for q in partners:
            moved = from_ego(to_ego(ghost_cache[q], q), st)
            tq = cKDTree(moved); vals.append(sum(1 for a in cam_g_st if tq.query_ball_point(a, R)))
        shift_n.append(len(cam_g_st)); shift_obs.append(row[2]); shift_null.append(float(np.mean(vals)))
    shift_obs, shift_null, shift_n = map(np.array, (shift_obs, shift_null, shift_n))
    per = np.array(per, dtype=object)
    scenes = per[:, 0]; A = per[:, 1:11].astype(float)
    n_cam_g, obs, null, null180, n_lid_g, rev_obs, rev_null, n_cam_r, real_obs, real_null = A.T
    n_cam, n_lid = sum(len(dets["camera"].get(st, [])) for st in gt_xy), sum(len(dets["lidar"].get(st, [])) for st in gt_xy)
    print("=" * 92)
    print("RESULT AH - ghost-ghost coincidence: do the camera and the lidar report phantom objects at the same places?")
    print(f"camera=Mapillary lidar=Megvii at score >= {SCORE}; {len(per)} keyframes; ghost = no annotated object of any class within {R} m")
    print(f"camera detections {n_cam}, ghosts {int(n_cam_g.sum())} ({100*n_cam_g.sum()/n_cam:.1f}%); "
          f"lidar detections {n_lid}, ghosts {int(n_lid_g.sum())} ({100*n_lid_g.sum()/n_lid:.1f}%)")
    print(f"rotation null: K = {K} per keyframe; band: scene-clustered bootstrap, B = {B}, seed {SEED}")
    print(f"time-shift null: {int((shift_n > 0).sum())} keyframes with a heading and a partner ten keyframes away; "
          f"{n_no_heading} keyframes without a heading (ego moved under 0.5 m)")
    print("=" * 92)

    def ratio(num, den, mask=None):
        m = np.ones(len(num), bool) if mask is None else mask
        return num[m].sum() / den[m].sum() if den[m].sum() > 0 else np.nan
    def band(num, den):
        uniq = np.unique(scenes); idx = {s: np.where(scenes == s)[0] for s in uniq}
        vals = []
        for _ in range(B):
            pick = rng.choice(len(uniq), len(uniq), replace=True)
            rows = np.concatenate([idx[uniq[j]] for j in pick])
            vals.append(num[rows].sum() / den[rows].sum() if den[rows].sum() > 0 else np.nan)
        return np.nanpercentile(vals, [2.5, 97.5])
    rows = [("P(lidar ghost within 2 m | camera ghost), observed", obs, n_cam_g),
            ("same, rotation null", null, n_cam_g),
            ("same, 180-degree null", null180, n_cam_g),
            ("P(camera ghost within 2 m | lidar ghost), observed", rev_obs, n_lid_g),
            ("same, rotation null", rev_null, n_lid_g),
            ("sanity: P(lidar TRUE detection within 2 m | camera TRUE detection), observed", real_obs, n_cam_r),
            ("same, rotation null", real_null, n_cam_r),
            ("P(lidar ghost within 2 m | camera ghost), keyframes with a time-shift partner", shift_obs, shift_n),
            ("same, within-scene time-shift null (about 5 s, same road, same sensor)", shift_null, shift_n)]
    print(f"\n  {'quantity':<78}{'value':>9}{'95% band':>18}")
    for name, num, den in rows:
        lo, hi = band(num, den)
        print(f"  {name:<78}{100*ratio(num, den):>8.2f}%  [{100*lo:.2f}, {100*hi:.2f}]")
    print(f"\n  {'coefficient':<78}{'value':>9}{'95% band':>18}")
    for name, num, den in (("c_ghost, camera -> lidar, against the rotation null", obs, null),
                           ("c_ghost, camera -> lidar, against the 180-degree null", obs, null180),
                           ("c_ghost, lidar -> camera, against the rotation null", rev_obs, rev_null),
                           ("c_real (sanity), camera -> lidar true detections", real_obs, real_null),
                           ("c_ghost, camera -> lidar, against the within-scene time-shift null", shift_obs, shift_null)):
        lo, hi = band(num, den)
        print(f"  {name:<78}{ratio(num, den):>9.2f}  [{lo:.2f}, {hi:.2f}]")
    print("\n  camera ghosts by class (observed coincidence / null share):")
    for c, (n, nl, o) in sorted(cls_rows.items(), key=lambda z: -z[1][0])[:6]:
        print(f"    {c:<20} n={n:>6}  observed {100*o/n:>6.2f}%  null {100*nl/n:>6.2f}%  c_ghost {o/nl if nl else float('nan'):>6.2f}")
    print("\n" + "-" * 92)
    print("NON-CLAIMS: released detector outputs on the public nuScenes validation split, retained as")
    print("proposed. A ghost is defined against the annotation set, which is itself a reference process")
    print("with unknown error (register: reference-error-identification unknown); an unannotated real")
    print("object makes both channels' true reports look like coincident ghosts, so c_ghost is an")
    print("upper bound in that direction and the class-agnostic 2 m rule is deliberately lenient in the")
    print("other. The rotation null keeps range but not the road geometry, so part of any excess is")
    print("shared scene structure, exactly as the marginal miss coefficient includes shared difficulty.")
    print("One pair, one operating point. Not a safety determination. No detector is executed. No")
    print("released 1.2 byte is involved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
