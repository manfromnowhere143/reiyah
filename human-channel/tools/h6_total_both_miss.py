"""Human channel H6: the total-both-miss, objects a deployed detector and the human are BOTH blind to.

H5 measured the cross-agent coincidence on objects the detector at least weakly saw, and found
independence there. The deeper and more dangerous question is the total joint silent miss: objects
that are really present, that the automation detects NOT AT ALL, and that the human also does not
attend. That needs a reference for "present" beyond the deployed detector, which BDD-A does not
carry as boxes and BDD100K's labels cannot be joined to (renumbered clip ids, no mapping).

The correct construction without an impossible join: a STRONG reference detector defines the
objects present; a weaker, realistic DEPLOYED detector is the automation channel; its misses on the
reference objects, including the ones it gives zero detection to, are genuine automation blindness.

  reference (objects present) = Faster R-CNN ResNet50-FPN v2, driving classes, score >= REF_TAU
  automation channel          = SSDLite MobileNetV3 (a realistic edge detector), score >= DEP_TAU
  automation miss on a reference object = no SSDLite box overlaps it (IoU >= 0.5) at DEP_TAU
  human miss                  = gaze-heatmap density on the reference box below the per-run median
  c = P(both miss) / [ P(auto miss) * P(human miss) ]

This includes the TOTAL misses H5 could not see. It is the honest joint silent miss on the
detectable-by-a-strong-model set, still a lower bound on the true one (the strong reference also
misses the very hardest objects), but far closer than H5.

Usage: bdda-venv/bin/python human-channel/tools/h6_total_both_miss.py <n_clips> <fps>
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
    rows = []   # (auto_miss(bool), gaze_att)
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
                depb = db[dk] if dk else torch.zeros((0, 4))
                # match reference -> deployed by IoU
                if len(depb):
                    iou = box_iou(refb, depb)
                    matched = (iou.max(dim=1).values >= IOU).numpy()
                else:
                    matched = np.zeros(len(refb), dtype=bool)
                for j, bb in enumerate(refb):
                    auto_miss = not matched[j]
                    gx1, gy1 = int(max(0, bb[0]*SX)), int(max(0, BAR+bb[1]*SY))
                    gx2, gy2 = int(min(1024, bb[2]*SX)), int(min(768, BAR+bb[3]*SY))
                    if gx2 <= gx1 or gy2 <= gy1:
                        continue
                    att = float(gimg[gy1:gy2, gx1:gx2].mean()) / gmax
                    rows.append((cid, auto_miss, att))
        if (ci + 1) % 20 == 0:
            print(f"  ...{ci+1} clips, {len(rows)} reference objects", flush=True)

    n = len(rows)
    clip_ids = np.array([r[0] for r in rows])
    auto = np.array([r[1] for r in rows], dtype=bool)
    att = np.array([r[2] for r in rows])
    np.savez("human-channel/evidence/h6_raw.npz", clip=clip_ids, auto=auto, att=att)
    med = float(np.median(att))
    human = att < med

    def coef_of(mask_auto, mask_hum):
        nn = len(mask_auto)
        aa = int((mask_auto & mask_hum).sum())
        pa = float(mask_auto.mean()); ph = float(mask_hum.mean()); pb = aa/nn
        return pb/(pa*ph) if pa*ph > 0 else float("nan")

    a = int((auto & human).sum()); b = int((auto & ~human).sum())
    c = int((~auto & human).sum()); d = int((~auto & ~human).sum())
    p_a = (a+b)/n; p_h = (a+c)/n; p_b = a/n
    coef = coef_of(auto, human)

    # clip-clustered bootstrap CI (resample whole clips, objects correlated within a clip)
    uniq = np.unique(clip_ids)
    idx_by_clip = {cl: np.where(clip_ids == cl)[0] for cl in uniq}
    rng = np.random.default_rng(20260828)
    draws = []
    for _ in range(1500):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        sel = np.concatenate([idx_by_clip[cl] for cl in pick])
        draws.append(coef_of(auto[sel], human[sel]))
    lo, hi = np.nanpercentile(draws, [2.5, 97.5])

    print("=" * 84)
    print("HUMAN CHANNEL H6 - the total-both-miss (deployed automation totally blind AND human ignores)")
    print(f"BDD-A validation, {len(clips)} clips, {n_frames} frames, {n} reference objects")
    print(f"reference: FasterRCNN-v2 >= {REF_TAU}; deployed: SSDLite >= {DEP_TAU}; IoU {IOU}")
    print("=" * 84)
    print(f"\n  automation miss = deployed detector has NO box on the object (total/operating miss)")
    print(f"  human miss = gaze attention below median ({med:.3f})")
    print(f"  P(automation totally misses a present object): {100*p_a:.1f}%")
    print(f"  P(human misses)                              : {100*p_h:.1f}%")
    print(f"  P(BOTH miss = the joint silent miss)         : {100*p_b:.1f}%")
    print(f"  expected if independent                      : {100*p_a*p_h:.1f}%")
    print(f"  coefficient c                                : {coef:.3f}")
    print(f"  clip-clustered bootstrap 95% CI              : [{lo:.3f}, {hi:.3f}]  ({len(uniq)} clips)")
    excl = "excludes 1.0" if (hi < 1.0 or lo > 1.0) else "includes 1.0 -> indistinguishable from independence"
    print(f"  verdict                                      : {excl}")
    print(f"  2x2 [both,autoOnly,humOnly,neither]          : {a}, {b}, {c}, {d}")
    print("\n" + "-" * 84)
    print("NON-CLAIMS: reference is a strong detector, not human GT, so this is the joint miss on")
    print("the strong-model-detectable set, still a lower bound; BDD-A gaze is in-lab aggregate;")
    print("SSDLite is one edge detector, not any product; descriptive, not clustered; research-use")
    print("data (Xia 2018); proposed; no released 1.2 byte involved.")


if __name__ == "__main__":
    main()
