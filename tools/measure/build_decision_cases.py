"""Build real decision-packet cases for one base-plus-camera comparison.

This produces neutral cases for the `decision_packet` producer from retained
detector outputs and a retained annotation cache, under one explicitly declared
comparison rule. It emits neutral identifiers only: no annotation, instance or
sample token, no coordinate, no path and no score leaves this program.

It does **not** reproduce the Engine's own two anchors, and the two must not be
combined. The correspondence gaps are computed and emitted with the output rather
than left to a reader to notice. A matching detector name does not establish
matching rows, thresholds, clocks or reference rules.

The declared rule, which is the Engine's stated comparison policy applied to a
population this program can state exactly:

  base            one lidar detector's released detections
  addition        one camera detector's released detections
  score floor     applied to both, declared below
  classes         the ten nuScenes detection classes
  range           annotations within the declared horizontal distance of the ego
  matching        same class, strict centre distance below the declared radius
  suppression     an addition is dropped when a retained same-class detection of
                  the base lies strictly within the suppression radius
  reference       the retained annotation cache, with a declared disputed set

Aggregate structure only. Standard library plus the retained files, read only.
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
RULE = {"score_floor": "0.30", "match_radius_m": "2", "suppression_radius_m": "2",
        "max_range_m": "50", "classes": list(CLASSES)}


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def square(ax, ay, bx, by):
    return (Fraction(str(ax)) - Fraction(str(bx))) ** 2 + (Fraction(str(ay)) - Fraction(str(by))) ** 2


def load_detections(path, floor, keep):
    """Detections at or above the floor, for the wanted samples, in file order."""
    with open(path, "r", encoding="utf-8") as handle:
        results = json.load(handle)["results"]
    out = {}
    for token in keep:
        rows = results.get(token, [])
        selected = []
        for index, row in enumerate(rows):
            if row["detection_name"] not in CLASSES:
                continue
            if Fraction(str(row["detection_score"])) < floor:
                continue
            selected.append({"order": index, "cls": row["detection_name"],
                             "x": row["translation"][0], "y": row["translation"][1],
                             "score": Fraction(str(row["detection_score"]))})
        selected.sort(key=lambda d: (-d["score"], d["order"]))
        out[token] = selected
    return out


def build_case(anchor, objects, base, added, match_r2):
    """One neutral case: base preserved, additions suppressed, edges by class and radius."""
    obj_entries, obj_pos = [], []
    for index, obj in enumerate(objects):
        name = f"o{index}"
        obj_entries.append({"id": name, "class": obj["cls"]})
        obj_pos.append((name, obj["cls"], obj["x"], obj["y"], obj["disputed"]))
    det_pos = []
    base_entries = []
    for index, det in enumerate(base):
        name = f"b{index}"
        base_entries.append({"id": name, "class": det["cls"]})
        det_pos.append((name, det["cls"], det["x"], det["y"]))
    added_entries = []
    for index, det in enumerate(added):
        name = f"c{index}"
        added_entries.append({"id": name, "class": det["cls"]})
        det_pos.append((name, det["cls"], det["x"], det["y"]))

    def edges_for(present):
        out = []
        for dname, dcls, dx, dy in det_pos:
            for oname, ocls, ox, oy, _disputed in obj_pos:
                if oname not in present or dcls != ocls:
                    continue
                if square(dx, dy, ox, oy) < match_r2:
                    out.append([dname, oname])
        return out

    everything = [name for name, _c, _x, _y, _d in obj_pos]
    undisputed = [name for name, _c, _x, _y, disputed in obj_pos if not disputed]
    worlds = [{"world_id": "w_all", "objects_present": everything,
               "edges": edges_for(set(everything))}]
    if undisputed != everything:
        worlds.append({"world_id": "w_undisputed", "objects_present": undisputed,
                       "edges": edges_for(set(undisputed))})
    return {"schema_id": "reiyah.decision-packet.case", "anchor_id": anchor,
            "loss": {"false_negative": "1", "false_positive": "1"},
            "base_detections": base_entries, "added_detections": added_entries,
            "objects": obj_entries, "worlds": worlds}


def main(argv):
    if len(argv) != 5:
        sys.stderr.write("usage: build_decision_cases.py CACHE_DIR PRED_DIR ANCHORS OUT_DIR\n")
        return 2
    cache, preds, anchors_wanted, out_dir = argv[1], argv[2], int(argv[3]), argv[4]
    floor = Fraction(RULE["score_floor"])
    match_r2 = Fraction(RULE["match_radius_m"]) ** 2
    suppress_r2 = Fraction(RULE["suppression_radius_m"]) ** 2
    max_range = Fraction(RULE["max_range_m"])

    sources = {"gt_val_cache.json": os.path.join(cache, "gt_val_cache.json"),
               "megvii_val.json": os.path.join(preds, "megvii_val.json"),
               "mapillary_val.json": os.path.join(preds, "mapillary_val.json")}
    before = {name: digest(path) for name, path in sources.items()}
    started = time.time()

    with open(sources["gt_val_cache.json"], "r", encoding="utf-8") as handle:
        ground_truth = json.load(handle)
    by_sample = {}
    for row in ground_truth:
        by_sample.setdefault(row["sample_token"], []).append(row)
    # Deterministic, declared selection: sorted sample order, fixed stride, no outcome seen.
    ordered = sorted(by_sample)
    stride = max(1, len(ordered) // anchors_wanted)
    chosen = ordered[::stride][:anchors_wanted]

    base_all = load_detections(sources["megvii_val.json"], floor, chosen)
    added_all = load_detections(sources["mapillary_val.json"], floor, chosen)

    os.makedirs(out_dir, exist_ok=True)
    summary = {"artifact_id": "reiyah.decision-packet.real-cases", "version": "0.1.0",
               "rule": RULE, "base_detector": "megvii", "added_detector": "mapillary",
               "anchor_selection": ("sorted sample order with a fixed stride, fixed before any "
                                    "outcome was computed; one anchor is one keyframe"),
               "anchors": [], "inputs": before}
    for index, token in enumerate(chosen):
        rows = [r for r in by_sample[token] if r["cls"] in CLASSES
                and Fraction(str(r["dist"])) <= max_range]
        objects = [{"cls": r["cls"], "x": r["xy"][0], "y": r["xy"][1],
                    "disputed": (r["nl"] == 0 and r["nr"] == 0)} for r in rows]
        base = base_all[token]
        retained = []
        for det in added_all[token]:
            if any(det["cls"] == b["cls"] and square(det["x"], det["y"], b["x"], b["y"]) < suppress_r2
                   for b in base):
                continue
            retained.append(det)
        anchor = f"real.megvii-plus-mapillary.{index:02d}"
        case = build_case(anchor, objects, base, retained, match_r2)
        with open(os.path.join(out_dir, f"{anchor}.json"), "w", encoding="utf-8") as handle:
            json.dump(case, handle, indent=2, sort_keys=True)
            handle.write("\n")
        summary["anchors"].append({
            "anchor_id": anchor, "objects": len(objects),
            "disputed_objects": sum(1 for o in objects if o["disputed"]),
            "base_detections": len(base), "camera_before_suppression": len(added_all[token]),
            "retained_additions": len(retained),
            "worlds": len(case["worlds"]),
            "edges_in_widest_world": len(case["worlds"][0]["edges"])})

    after = {name: digest(path) for name, path in sources.items()}
    if before != after:
        sys.stderr.write("REFUSED: an input changed during the run\n")
        return 1
    summary["inputs_unchanged_across_the_run"] = True
    summary["elapsed_seconds"] = round(time.time() - started, 2)
    summary["peak_memory_mb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                                      / (1024 * 1024), 1)
    summary["correspondence_gaps_against_the_engine_comparison"] = [
        "population: these anchors are keyframes selected here by a stated stride; the Engine's "
        "comparison has two anchors inside two previously exposed development windows",
        "reference: the objects here come from the retained filtered annotation cache, while the "
        "Engine admits unfiltered source annotations; the object sets are not the same",
        "disputed set: zero lidar and zero radar returns is the alternative axis declared here, "
        "and is not the Engine's joint reference alternative construction",
        "clock and geometry: positions are taken as recorded in the retained cache and outputs, "
        "with no timing or calibration reconciliation performed",
        "therefore these numbers are not the Engine's and must not be combined with them"]
    summary["disclosure"] = (
        "neutral identifiers, class labels, edge structure and counts only. No annotation, "
        "instance or sample token, no coordinate, no score and no path is emitted. Edge structure "
        "still carries information: degree patterns and object counts describe scene density, and "
        "a small anchor could in principle be linked to a recording by someone holding the source. "
        "This is a stated limit, not a claim of anonymity")
    json.dump(summary, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
