"""Human channel H6b: is the edge detector's 84.5 percent total-miss rate genuine blindness?

An adversarial reading of H6 said an 84.5 percent total-miss rate for a small edge detector at
score 0.25 on objects a strong detector finds at 0.6 is implausible as genuine blindness and could
be a pipeline defect (resolution, class mapping, or matching). This re-executes H6's detector pass
with the same models, thresholds, alignment and matching, imported by copy, and records per
reference object its box area and class, then reports the total-miss rate by box-size quartile and
by class, the miss rate under looser matching (IoU 0.3) and a looser deployed score (0.10), and
whether the two models' category lists are identical. If misses concentrate in small boxes and fall
only modestly under looser matching, the blindness is genuine and size-driven; if they vanish under
looser matching or differ by class mapping, H6's automation channel was a defect.

Usage: bdda-venv/bin/python human-channel/tools/h6b_blindness_check.py <n_clips> <fps>
"""
import glob
import os
import subprocess
import sys
import tempfile

import numpy as np
import torch
from torchvision.io import read_image
from torchvision.ops import box_iou
from torchvision.models.detection import (
    fasterrcnn_resnet50_fpn_v2, FasterRCNN_ResNet50_FPN_V2_Weights,
    ssdlite320_mobilenet_v3_large, SSDLite320_MobileNet_V3_Large_Weights)

BDDA = "human-channel/bdda/BDDA/validation"
REF_TAU = 0.6
DEP_TAU = 0.25
IOU = 0.5
DRIVE = {"person", "bicycle", "car", "motorcycle", "bus", "truck", "traffic light", "stop sign"}
SX, SY, BAR = 0.8, 0.8, 96


def extract(video, out, fps):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video,
                    "-vf", f"fps={fps}", out], check=False)


def main():
    n_clips = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    fps = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
    dev = "mps" if torch.backends.mps.is_available() else "cpu"

    rw = FasterRCNN_ResNet50_FPN_V2_Weights.DEFAULT
    ref = fasterrcnn_resnet50_fpn_v2(weights=rw).eval().to(dev)
    rcats = rw.meta["categories"]
    dw = SSDLite320_MobileNet_V3_Large_Weights.DEFAULT
    dep = ssdlite320_mobilenet_v3_large(weights=dw).eval().to(dev)
    dcats = dw.meta["categories"]

    clips = sorted(glob.glob(f"{BDDA}/camera_videos/*.mp4"))[:n_clips]
    rows = []   # (clip, miss@iou0.5, miss@iou0.3, miss@dep0.10, area, class, gaze_att)
    print(f"  category lists identical: {list(rcats) == list(dcats)}", flush=True)
    n_frames = 0
    for ci, cam in enumerate(clips):
        cid = os.path.splitext(os.path.basename(cam))[0]
        gaze = f"{BDDA}/gazemap_videos/{cid}_pure_hm.mp4"
        if not os.path.exists(gaze):
            continue
        with tempfile.TemporaryDirectory() as td:
            extract(cam, f"{td}/c_%03d.jpg", fps)
            extract(gaze, f"{td}/g_%03d.jpg", fps)
            for cf in sorted(glob.glob(f"{td}/c_*.jpg")):
                gf = cf.replace("/c_", "/g_")
                if not os.path.exists(gf):
                    continue
                img = (read_image(cf).float() / 255.0).to(dev)
                gimg = read_image(gf).float().mean(0)
                gmax = float(gimg.max()) + 1e-6
                with torch.no_grad():
                    ro = ref([img])[0]
                    do = dep([img])[0]
                n_frames += 1
                # reference objects: driving classes, confident
                rb, rs, rl = ro["boxes"].cpu(), ro["scores"].cpu(), ro["labels"].cpu()
                rk = [i for i in range(len(rs)) if rs[i] >= REF_TAU and rcats[rl[i]] in DRIVE]
                if not rk:
                    continue
                refb = rb[rk]
                # deployed detections (driving, operating threshold)
                db, ds, dl = do["boxes"].cpu(), do["scores"].cpu(), do["labels"].cpu()
                dk = [i for i in range(len(ds)) if ds[i] >= DEP_TAU and dcats[dl[i]] in DRIVE]
                dk_loose = [i for i in range(len(ds)) if ds[i] >= 0.10 and dcats[dl[i]] in DRIVE]
                depb = db[dk] if dk else torch.zeros((0, 4))
                depb_loose = db[dk_loose] if dk_loose else torch.zeros((0, 4))
                if len(depb):
                    iou = box_iou(refb, depb)
                    matched = (iou.max(dim=1).values >= IOU).numpy()
                    matched_loose_iou = (iou.max(dim=1).values >= 0.3).numpy()
                else:
                    matched = np.zeros(len(refb), dtype=bool); matched_loose_iou = matched.copy()
                if len(depb_loose):
                    matched_loose_score = (box_iou(refb, depb_loose).max(dim=1).values >= IOU).numpy()
                else:
                    matched_loose_score = np.zeros(len(refb), dtype=bool)
                for j, bb in enumerate(refb):
                    auto_miss = not matched[j]
                    area = float((bb[2] - bb[0]) * (bb[3] - bb[1]))
                    rcls = rcats[rl[rk[j]]]
                    gx1, gy1 = int(max(0, bb[0]*SX)), int(max(0, BAR+bb[1]*SY))
                    gx2, gy2 = int(min(1024, bb[2]*SX)), int(min(768, BAR+bb[3]*SY))
                    if gx2 <= gx1 or gy2 <= gy1:
                        continue
                    att = float(gimg[gy1:gy2, gx1:gx2].mean()) / gmax
                    rows.append((cid, auto_miss, not matched_loose_iou[j], not matched_loose_score[j], area, rcls, att))
        if (ci + 1) % 20 == 0:
            print(f"  ...{ci+1} clips, {len(rows)} reference objects", flush=True)

    n = len(rows)
    miss = np.array([r[1] for r in rows], dtype=bool); miss_iou3 = np.array([r[2] for r in rows], dtype=bool)
    miss_s10 = np.array([r[3] for r in rows], dtype=bool); area = np.array([r[4] for r in rows]); rcls = np.array([r[5] for r in rows])
    print("=" * 84)
    print("HUMAN CHANNEL H6b - is the edge detector's total-miss rate genuine, size-driven blindness?")
    print(f"BDD-A validation, {len(clips)} clips, {n_frames} frames, {n} reference objects (same definitions as H6)")
    print("=" * 84)
    print(f"\n  total-miss rate, H6 definition (score >= {DEP_TAU}, IoU >= {IOU}): {100*miss.mean():.1f}%")
    print(f"  under looser matching (IoU >= 0.3)                      : {100*miss_iou3.mean():.1f}%")
    print(f"  under a looser deployed score (>= 0.10)                 : {100*miss_s10.mean():.1f}%")
    q = np.quantile(area, [0.25, 0.5, 0.75])
    print(f"\n  by reference box area quartile (pixels^2 in the 720x1280 frame):")
    for lo, hi, name in ((0, q[0], "smallest quarter"), (q[0], q[1], "second"), (q[1], q[2], "third"), (q[2], area.max() + 1, "largest quarter")):
        m = (area >= lo) & (area < hi)
        print(f"    {name:<18} area {lo:>8.0f} to {hi:>8.0f}: n={m.sum():>6}  miss {100*miss[m].mean():>5.1f}%  (IoU 0.3: {100*miss_iou3[m].mean():>5.1f}%, score 0.10: {100*miss_s10[m].mean():>5.1f}%)")
    print(f"\n  by reference class:")
    for c in sorted(set(rcls), key=lambda c: -(rcls == c).sum()):
        m = rcls == c
        print(f"    {c:<14} n={m.sum():>6}  miss {100*miss[m].mean():>5.1f}%")
    print("\n" + "-" * 84)
    print("NON-CLAIMS: same detectors, thresholds, alignment and matching as H6; a diagnostic of the")
    print("automation channel's miss rate, not a re-measurement of the coefficient. Research-use data")
    print("(Xia 2018), retained as proposed; no released 1.2 byte involved.")


if __name__ == "__main__":
    main()
