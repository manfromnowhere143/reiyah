"""Human channel H5b: the cross-agent coefficient of H5 with a clip-clustered band.

H5 reported the cross-agent coincidence coefficient (automation miss x human inattention on the
detector's own detections) as a point estimate, 0.972 on 13,904 objects. This is the same
measurement, unchanged in every definition (same detector, weights, floor, operating threshold,
driving classes, gaze alignment, median split), with the clip id recorded per object so that a
clip-clustered bootstrap band can be put on the coefficient, as H6 already has. The raw per-object
rows are saved so the band can be recomputed without re-executing the detector.

Usage: bdda-venv/bin/python human-channel/tools/h5b_cross_agent_interval.py <n_clips> <fps>
"""
import glob
import os
import subprocess
import sys
import tempfile

import numpy as np
import torch
from torchvision.io import read_image
from torchvision.models.detection import (fasterrcnn_resnet50_fpn,
                                          FasterRCNN_ResNet50_FPN_Weights)

BDDA = "human-channel/bdda/BDDA/validation"
FLOOR = 0.3            # object plausibly present
TAU = 0.5             # automation operating threshold; score in [FLOOR,TAU) = automation miss
DRIVE = {"person", "bicycle", "car", "motorcycle", "bus", "truck",
         "traffic light", "stop sign"}
SX, SY, BAR = 0.8, 0.8, 96   # gaze alignment constants


def extract(video, out, fps):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video,
                    "-vf", f"fps={fps}", out], check=False)


def main():
    n_clips = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    fps = float(sys.argv[2]) if len(sys.argv) > 2 else 0.4

    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    w = FasterRCNN_ResNet50_FPN_Weights.DEFAULT
    model = fasterrcnn_resnet50_fpn(weights=w).eval().to(dev)
    cats = w.meta["categories"]

    clips = sorted(glob.glob(f"{BDDA}/camera_videos/*.mp4"))[:n_clips]
    rows = []   # (clip, score, gaze_att, class)
    n_frames = 0
    for ci, cam in enumerate(clips):
        cid = os.path.splitext(os.path.basename(cam))[0]
        gaze = f"{BDDA}/gazemap_videos/{cid}_pure_hm.mp4"
        if not os.path.exists(gaze):
            continue
        with tempfile.TemporaryDirectory() as td:
            extract(cam, f"{td}/c_%03d.jpg", fps)
            extract(gaze, f"{td}/g_%03d.jpg", fps)
            cfr = sorted(glob.glob(f"{td}/c_*.jpg"))
            for cf in cfr:
                gf = cf.replace("/c_", "/g_")
                if not os.path.exists(gf):
                    continue
                img = read_image(cf).float() / 255.0
                gimg = read_image(gf).float().mean(0)   # gaze grayscale HxW (768x1024)
                gmax = float(gimg.max()) + 1e-6
                with torch.no_grad():
                    out = model([img.to(dev)])[0]
                sc = out["scores"].cpu().numpy()
                lb = out["labels"].cpu().numpy()
                bx = out["boxes"].cpu().numpy()
                n_frames += 1
                for s, l, b in zip(sc, lb, bx):
                    if s < FLOOR:
                        continue
                    name = cats[l]
                    if name not in DRIVE:
                        continue
                    gx1, gy1 = b[0] * SX, BAR + b[1] * SY
                    gx2, gy2 = b[2] * SX, BAR + b[3] * SY
                    gx1, gx2 = int(max(0, gx1)), int(min(1024, gx2))
                    gy1, gy2 = int(max(0, gy1)), int(min(768, gy2))
                    if gx2 <= gx1 or gy2 <= gy1:
                        continue
                    att = float(gimg[gy1:gy2, gx1:gx2].mean()) / gmax   # 0..1 relative attention
                    rows.append((cid, float(s), att, name))
        if (ci + 1) % 20 == 0:
            print(f"  ...{ci+1} clips, {len(rows)} objects", flush=True)

    n = len(rows)
    clip_ids = np.array([r[0] for r in rows])
    scores = np.array([r[1] for r in rows])
    att = np.array([r[2] for r in rows])
    np.savez("human-channel/evidence/h5b_raw.npz", clip=clip_ids, score=scores, att=att)
    print("=" * 84)
    print("HUMAN CHANNEL H5b - cross-agent joint with a clip-clustered band")
    print(f"BDD-A validation, {len(clips)} clips, {n_frames} frames, {n} driving objects")
    print("=" * 84)

    med_att = float(np.median(att))
    auto_miss = scores < TAU
    human_miss = att < med_att
    a = int((auto_miss & human_miss).sum())
    b = int((auto_miss & ~human_miss).sum())
    c = int((~auto_miss & human_miss).sum())
    d = int((~auto_miss & ~human_miss).sum())
    p_auto = (a + b) / n
    p_hum = (a + c) / n
    p_both = a / n
    coef = p_both / (p_auto * p_hum) if p_auto * p_hum > 0 else float("nan")
    print(f"\n  automation miss = score < {TAU}; human miss = gaze attention < median ({med_att:.3f})")
    print(f"  P(automation miss)              : {100*p_auto:.1f}%")
    print(f"  P(human miss)                   : {100*p_hum:.1f}%")
    print(f"  P(both miss)                    : {100*p_both:.1f}%")
    print(f"  expected if independent         : {100*p_auto*p_hum:.1f}%")
    print(f"  cross-agent coefficient c       : {coef:.3f}")
    print(f"  2x2 counts [both,autoOnly,humOnly,neither]: {a}, {b}, {c}, {d}")

    # clip-clustered bootstrap band (resample whole clips; objects are correlated within a clip)
    uniq = np.unique(clip_ids)
    idx_by_clip = {cl: np.where(clip_ids == cl)[0] for cl in uniq}
    rng = np.random.default_rng(20260906)
    boots = []
    for _ in range(2000):
        pick = rng.choice(uniq, len(uniq), replace=True)
        sel = np.concatenate([idx_by_clip[cl] for cl in pick])
        am, hm = auto_miss[sel], att[sel] < med_att
        pa, ph, pb = am.mean(), hm.mean(), (am & hm).mean()
        boots.append(pb / (pa * ph) if pa * ph > 0 else np.nan)
    lo, hi = np.nanpercentile(boots, [2.5, 97.5])
    print(f"  clip-clustered bootstrap 95% band: [{lo:.3f}, {hi:.3f}]  ({len(uniq)} clips, B = 2000)")

    # correlation of the two continuous channels
    if n > 2:
        r = float(np.corrcoef(scores, att)[0, 1])
        print(f"\n  Pearson corr(automation score, human attention): {r:+.3f}")
        print("  positive means the machine is unsure about the same objects people ignore.")

    print("\n" + "-" * 84)
    print("NON-CLAIMS: same measurement as H5 with a band; the median split is recomputed on the")
    print("full sample and held fixed inside the bootstrap. BDD-A gaze is an in-lab aggregate over observers, not one naturalistic")
    print("driver; object set is detector detections (a lower bound, objects both totally missed")
    print("are unobservable without GT boxes); descriptive, not clustered; c > 1 includes shared")
    print("scene difficulty, not claimed as pure latent dependence. Research-use data (Xia 2018),")
    print("retained as proposed; no released 1.2 byte involved.")


if __name__ == "__main__":
    main()
