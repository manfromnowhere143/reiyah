"""Conversion rate with every population and threshold choice declared separately.

Version `0.1.0` of `conversion_rate.py` carried three defects, found in external
review and reproduced here. They are retained rather than repaired in place:

  1. one score floor was applied to the base and the addition together, so a floor
     sweep changed the installed configuration as well as the candidate. Any
     reading of that sweep as an operating point of the addition is void.
  2. keyframes with no eligible reference object were skipped, because the loop
     iterated the annotation table. Those frames carry additions and no possible
     gain, so omitting them biases conversion upward.
  3. the declared range limit was applied to annotations and not to predictions,
     so far predictions inflated the retained count and biased conversion
     downward.

This version takes each choice as a separate declared parameter and reports the
variant it ran. Nothing is defaulted silently.

Ego position is read from the annotation cache, so a keyframe with no annotation
row has no ego and its predictions cannot be range filtered. That case is counted
and reported rather than hidden; with `include_empty_frames` on and range
filtering on, such frames are reported as `unrangeable` and excluded from the
range-filtered variant, which is stated in the output.

Aggregate counts only. Standard library, exact rationals, read only.
"""
from fractions import Fraction
import hashlib
import json
import os
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


def prediction_path(preds, name):
    for suffix in ("_val.json", "-val.json"):
        candidate = os.path.join(preds, name + suffix)
        if os.path.exists(candidate):
            return name + suffix, candidate
    raise FileNotFoundError(f"no retained prediction file for {name}")


def load(path, floor):
    with open(path, "r", encoding="utf-8") as handle:
        results = json.load(handle)["results"]
    out = {}
    for token, rows in results.items():
        out[token] = [(r["detection_name"], Fraction(str(r["translation"][0])),
                       Fraction(str(r["translation"][1])))
                      for r in rows if r["detection_name"] in CLASSES
                      and Fraction(str(r["detection_score"])) >= floor]
    return out


def main(argv):
    if len(argv) != 9:
        sys.stderr.write(
            "usage: conversion_rate_v2.py CACHE PRED BASE ADDED BASE_FLOOR ADDED_FLOOR "
            "INCLUDE_EMPTY_FRAMES RANGE_ON_PREDICTIONS\n")
        return 2
    cache, preds, base_name, added_name = argv[1:5]
    base_floor, added_floor = Fraction(argv[5]), Fraction(argv[6])
    include_empty = argv[7] == "yes"
    range_predictions = argv[8] == "yes"
    match_r2 = Fraction(4)
    suppress_r2 = Fraction(4)
    max_range2 = Fraction(2500)

    base_file, base_path = prediction_path(preds, base_name)
    added_file, added_path = prediction_path(preds, added_name)
    sources = {"gt_val_cache.json": os.path.join(cache, "gt_val_cache.json"),
               base_file: base_path, added_file: added_path}
    before = {k: digest(v) for k, v in sources.items()}
    started = time.time()

    with open(sources["gt_val_cache.json"], "r", encoding="utf-8") as handle:
        ground_truth = json.load(handle)
    objects, ego = {}, {}
    for row in ground_truth:
        token = row["sample_token"]
        ego.setdefault(token, (Fraction(str(row["ego_xy"][0])), Fraction(str(row["ego_xy"][1]))))
        if row["cls"] in CLASSES and Fraction(str(row["dist"])) ** 2 <= max_range2:
            objects.setdefault(token, []).append(
                (row["cls"], Fraction(str(row["xy"][0])), Fraction(str(row["xy"][1]))))

    base_all = load(base_path, base_floor)
    added_all = load(added_path, added_floor)

    tokens = set(base_all) | set(added_all) if include_empty else set(objects)
    unrangeable = 0
    totals = {"keyframes": 0, "frames_without_reference_objects": 0,
              "objects": 0, "base_detections": 0, "candidates_before_suppression": 0,
              "retained_additions": 0, "tp_base": 0, "tp_augmented": 0}

    for token in sorted(tokens):
        objs = objects.get(token, [])
        base = base_all.get(token, [])
        cand = added_all.get(token, [])
        if range_predictions:
            here = ego.get(token)
            if here is None:
                unrangeable += 1
                continue
            ex, ey = here
            base = [d for d in base if (d[1] - ex) ** 2 + (d[2] - ey) ** 2 <= max_range2]
            cand = [d for d in cand if (d[1] - ex) ** 2 + (d[2] - ey) ** 2 <= max_range2]
        retained = []
        for det in cand:
            if any(det[0] == b[0] and (det[1] - b[1]) ** 2 + (det[2] - b[2]) ** 2 < suppress_r2
                   for b in base):
                continue
            retained.append(det)

        def adjacency_for(dets):
            return {i: [j for j, (ocls, ox, oy) in enumerate(objs)
                        if ocls == cls and (x - ox) ** 2 + (y - oy) ** 2 < match_r2]
                    for i, (cls, x, y) in enumerate(dets)}

        tp_base = max_matching(range(len(base)), adjacency_for(base))
        tp_aug = max_matching(range(len(base + retained)), adjacency_for(base + retained))
        if not 0 <= tp_aug - tp_base <= len(retained):
            raise ValueError("gain outside [0, r]")
        totals["keyframes"] += 1
        if not objs:
            totals["frames_without_reference_objects"] += 1
        totals["objects"] += len(objs)
        totals["base_detections"] += len(base)
        totals["candidates_before_suppression"] += len(cand)
        totals["retained_additions"] += len(retained)
        totals["tp_base"] += tp_base
        totals["tp_augmented"] += tp_aug

    gain = totals["tp_augmented"] - totals["tp_base"]
    r = totals["retained_additions"]
    conversion = Fraction(gain, r) if r else None
    after = {k: digest(v) for k, v in sources.items()}
    if before != after:
        sys.stderr.write("REFUSED: an input changed during the run\n")
        return 1
    json.dump({
        "artifact_id": "reiyah.decision-evidence.conversion-rate", "version": "0.2.0",
        "base_detector": base_name, "added_detector": added_name,
        "variant": {"base_score_floor": str(base_floor), "added_score_floor": str(added_floor),
                    "include_frames_without_reference_objects": include_empty,
                    "range_limit_applied_to_predictions": range_predictions,
                    "match_radius_m": "2", "suppression_radius_m": "2", "max_range_m": "50"},
        "population": totals,
        "frames_skipped_for_unknown_ego": unrangeable,
        "true_positive_gain": gain,
        "conversion_rate": str(conversion) if conversion else None,
        "conversion_decimal": round(float(conversion), 6) if conversion else None,
        "break_even_a_over_b": str(1 / conversion - 1) if conversion else None,
        "inputs": before, "elapsed_seconds": round(time.time() - started, 2),
        "scope": ("one declared variant on one public split with released detector outputs against "
                  "the retained filtered annotation cache. Reference relative, descriptive, finite "
                  "population, no sampling statement"),
    }, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
