"""What fraction of an added detector's retained detections finds a missed object.

Under the additive false-negative and false-positive loss, for a base
configuration and an augmentation that preserves every base detection,

    delta = (a + b) * (TP_augmented - TP_base) - b * r

so the addition improves the loss exactly when

    conversion = (TP_augmented - TP_base) / r  >  b / (a + b)

`conversion` is therefore the sufficient statistic for the addition decision under
this loss, and `b / (a + b)` is its threshold. This module measures the conversion
rate of one camera detector added to one lidar detector, per keyframe, over a whole
declared evaluation split, using maximum same-class one-to-one matching.

Detection benchmarks report neither quantity. That is the point of measuring it.

Aggregate counts only: no token, coordinate, score or path is emitted. Standard
library plus the retained files, read only.
"""
from fractions import Fraction
import hashlib
import json
import os
import resource
import sys
import time

CLASSES = ("barrier", "bicycle", "bus", "car", "construction_vehicle", "motorcycle",
           "pedestrian", "traffic_cone", "trailer", "truck")


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def augment(node, adjacency, matched_to, seen):
    for other in adjacency[node]:
        if other in seen:
            continue
        seen.add(other)
        if other not in matched_to or augment(matched_to[other], adjacency, matched_to, seen):
            matched_to[other] = node
            return True
    return False


def max_matching(left, adjacency):
    matched_to = {}
    for node in left:
        augment(node, adjacency, matched_to, set())
    return len(matched_to)


def main(argv):
    if len(argv) != 6:
        sys.stderr.write("usage: conversion_rate.py CACHE_DIR PRED_DIR BASE ADDED FLOOR\n")
        return 2
    cache, preds, base_name, added_name, floor_text = argv[1:]
    floor = Fraction(floor_text)
    match_r2 = Fraction(4)          # 2 m centre distance, squared
    suppress_r2 = Fraction(4)       # 2 m suppression, squared
    max_range = Fraction(50)

    def prediction_path(name):
        """The retained files are not consistently named, so both forms are accepted."""
        for suffix in ("_val.json", "-val.json"):
            candidate = os.path.join(preds, name + suffix)
            if os.path.exists(candidate):
                return name + suffix, candidate
        raise FileNotFoundError(f"no retained prediction file for {name}")

    base_file, base_path = prediction_path(base_name)
    added_file, added_path = prediction_path(added_name)
    sources = {"gt_val_cache.json": os.path.join(cache, "gt_val_cache.json"),
               base_file: base_path, added_file: added_path}
    before = {k: digest(v) for k, v in sources.items()}
    started = time.time()

    with open(sources["gt_val_cache.json"], "r", encoding="utf-8") as handle:
        ground_truth = json.load(handle)
    objects = {}
    for row in ground_truth:
        if row["cls"] in CLASSES and Fraction(str(row["dist"])) <= max_range:
            objects.setdefault(row["sample_token"], []).append(
                (row["cls"], Fraction(str(row["xy"][0])), Fraction(str(row["xy"][1]))))

    def detections(path):
        with open(path, "r", encoding="utf-8") as handle:
            results = json.load(handle)["results"]
        out = {}
        for token, rows in results.items():
            keep = [(r["detection_name"], Fraction(str(r["translation"][0])),
                     Fraction(str(r["translation"][1])))
                    for r in rows if r["detection_name"] in CLASSES
                    and Fraction(str(r["detection_score"])) >= floor]
            if keep:
                out[token] = keep
        return out

    base_all = detections(base_path)
    added_all = detections(added_path)

    totals = {"keyframes": 0, "objects": 0, "base_detections": 0,
              "camera_before_suppression": 0, "retained_additions": 0,
              "tp_base": 0, "tp_augmented": 0}
    per_class = {c: {"retained_additions": 0, "gain": 0} for c in CLASSES}

    for token, objs in objects.items():
        base = base_all.get(token, [])
        cam = added_all.get(token, [])
        retained = []
        for det in cam:
            if any(det[0] == b[0] and (det[1] - b[1]) ** 2 + (det[2] - b[2]) ** 2 < suppress_r2
                   for b in base):
                continue
            retained.append(det)
        allnodes = base + retained

        def adjacency_for(dets):
            adj = {}
            for i, (cls, x, y) in enumerate(dets):
                adj[i] = [j for j, (ocls, ox, oy) in enumerate(objs)
                          if ocls == cls and (x - ox) ** 2 + (y - oy) ** 2 < match_r2]
            return adj

        tp_base = max_matching(range(len(base)), adjacency_for(base))
        tp_aug = max_matching(range(len(allnodes)), adjacency_for(allnodes))
        gain = tp_aug - tp_base
        if not 0 <= gain <= len(retained):
            raise ValueError("gain outside [0, r]")
        totals["keyframes"] += 1
        totals["objects"] += len(objs)
        totals["base_detections"] += len(base)
        totals["camera_before_suppression"] += len(cam)
        totals["retained_additions"] += len(retained)
        totals["tp_base"] += tp_base
        totals["tp_augmented"] += tp_aug
        for cls, _x, _y in retained:
            per_class[cls]["retained_additions"] += 1

    gain = totals["tp_augmented"] - totals["tp_base"]
    r = totals["retained_additions"]
    conversion = Fraction(gain, r) if r else None
    after = {k: digest(v) for k, v in sources.items()}
    if before != after:
        sys.stderr.write("REFUSED: an input changed during the run\n")
        return 1

    report = {
        "artifact_id": "reiyah.decision-evidence.conversion-rate", "version": "0.1.0",
        "base_detector": base_name, "added_detector": added_name,
        "rule": {"score_floor": str(floor), "match_radius_m": "2", "suppression_radius_m": "2",
                 "max_range_m": "50", "classes": list(CLASSES),
                 "matching": "maximum same-class one-to-one, per keyframe"},
        "population": totals,
        "true_positive_gain": gain,
        "conversion_rate": str(conversion) if conversion is not None else None,
        "conversion_decimal": round(float(conversion), 6) if conversion is not None else None,
        "threshold_by_penalty_ratio": {
            "a_over_b_1": "1/2", "a_over_b_2": "1/3", "a_over_b_4": "1/5", "a_over_b_9": "1/10"},
        "improves_loss_at": {str(k): (conversion > Fraction(1, k + 1)) if conversion else None
                             for k in (1, 2, 4, 9)},
        "inputs": before, "inputs_unchanged_across_the_run": True,
        "elapsed_seconds": round(time.time() - started, 2),
        "peak_memory_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024), 1),
        "scope": ("one declared rule on one public split with released detector outputs, against the "
                  "retained filtered annotation cache. Reference relative, descriptive, no sampling "
                  "statement, and not a claim about any deployed stack"),
    }
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
