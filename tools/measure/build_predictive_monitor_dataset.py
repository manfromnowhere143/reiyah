#!/usr/bin/env python3
"""Offline features and reference-relative targets with separate input paths."""
import argparse
import ast
from collections import Counter, defaultdict
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

from audit_cache_selection import literal_assignment, rows_from_tables
from replay_reference_population_audit import digest, unique_pairs, invalid_constant

CLASSES = ("car", "truck", "bus", "trailer", "construction_vehicle", "pedestrian",
           "motorcycle", "bicycle", "traffic_cone", "barrier")
RANGES = dict(zip(CLASSES, (50, 50, 50, 50, 50, 40, 40, 40, 30, 30)))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value):
    require(type(value) in (int, float, Decimal) and math.isfinite(value), "invalid numeric input")
    return float(value)


def read_json(path):
    """Strict JSON structure, explicitly binary floats for this numeric experiment."""
    with Path(path).open() as stream:
        return json.load(stream, object_pairs_hook=unique_pairs, parse_constant=invalid_constant)


def coverage(predictions, frames):
    require(set(predictions) == set(frames), "prediction frame coverage differs")
    require(all(isinstance(v, list) for v in predictions.values()), "prediction frame is not a list")


def greedy_pairs(source, target, radius=2.):
    """Tuples are (class, score, x, y); stable source/target order resolves ties."""
    require(radius > 0 and math.isfinite(radius), "invalid matching radius")
    if not source or not target:
        return []
    xy_a = np.asarray([r[2:] for r in source], dtype=np.float64)
    xy_b = np.asarray([r[2:] for r in target], dtype=np.float64)
    require(np.isfinite(xy_a).all() and np.isfinite(xy_b).all(), "invalid matching coordinates")
    delta = xy_a[:, None, :] - xy_b[None, :, :]
    distances = np.hypot(delta[:, :, 0], delta[:, :, 1])
    same = np.asarray([r[0] for r in source])[:, None] == np.asarray([r[0] for r in target])[None, :]
    distances[~same] = np.inf
    pairs = []
    for i in sorted(range(len(source)), key=lambda i: -source[i][1]):
        j = int(np.argmin(distances[i]))
        if distances[i, j] < radius:
            pairs.append((i, j))
            distances[:, j] = np.inf
    return pairs


def match_reference(predictions, annotations, ego, radius=2.):
    in_range = [p for p in predictions if math.hypot(p[2] - ego[0], p[3] - ego[1]) < RANGES[p[0]]]
    return {j for _, j in greedy_pairs(in_range, annotations, radius)}


def mean_or_nan(values):
    return float(np.mean(values)) if len(values) else np.nan


def output_features(camera, lidar, ego):
    """No reference, scene ID, future output, motion track or label is accepted."""
    features = {}
    for name, boxes in (("camera", camera), ("lidar", lidar)):
        features[name + ".count"] = float(len(boxes))
        scores = [p[1] for p in boxes]
        distances = [math.hypot(p[2] - ego[0], p[3] - ego[1]) for p in boxes]
        features[name + ".score_mean"] = mean_or_nan(scores)
        features[name + ".score_std"] = float(np.std(scores)) if scores else np.nan
        for q in (.1, .5, .9):
            features[f"{name}.score_q{int(q*100)}"] = float(np.quantile(scores, q)) if scores else np.nan
        features[name + ".range_mean"] = mean_or_nan(distances)
        features[name + ".range_std"] = float(np.std(distances)) if distances else np.nan
        for cls in CLASSES:
            features[f"{name}.class_{cls}"] = float(sum(p[0] == cls for p in boxes))
        for low, high in ((0, 20), (20, 40), (40, 50), (50, math.inf)):
            features[f"{name}.range_{low}_{high}"] = float(sum(low <= d < high for d in distances))
    pairs = greedy_pairs(camera, lidar)
    ia, ib = {i for i, _ in pairs}, {j for _, j in pairs}
    n_either = len(camera) + len(lidar) - len(pairs)
    features.update({
        "joint.paired": float(len(pairs)), "joint.union": float(n_either),
        "joint.camera_only": float(len(camera) - len(pairs)),
        "joint.lidar_only": float(len(lidar) - len(pairs)),
        "joint.agreement": len(pairs) / n_either if n_either else np.nan,
        "joint.paired_score_mean": mean_or_nan([min(camera[i][1], lidar[j][1]) for i, j in pairs]),
        "joint.camera_only_score_mean": mean_or_nan([p[1] for i, p in enumerate(camera) if i not in ia]),
        "joint.lidar_only_score_mean": mean_or_nan([p[1] for i, p in enumerate(lidar) if i not in ib]),
        "joint.vru_unpaired": float(sum(p[0] in ("pedestrian", "bicycle", "motorcycle")
                                      for boxes, taken in ((camera, ia), (lidar, ib))
                                      for i, p in enumerate(boxes) if i not in taken)),
    })
    return features


def chains(samples, scenes):
    ordered = []
    for scene_id, scene in sorted(scenes.items()):
        rows = sorted((r["timestamp"], token) for token, r in samples.items() if r["scene_token"] == scene_id)
        require(len(rows) == scene["nbr_samples"] and rows, "scene count differs")
        require(rows[0][1] == scene["first_sample_token"] and rows[-1][1] == scene["last_sample_token"], "scene endpoint differs")
        for i, (time, token) in enumerate(rows):
            require(type(time) is int and time > 0, "invalid timestamp")
            require(i == 0 or rows[i-1][0] < time, "non-increasing scene time")
            require(samples[token]["prev"] == (rows[i-1][1] if i else "") and
                    samples[token]["next"] == (rows[i+1][1] if i+1 < len(rows) else ""), "broken scene chain")
        ordered.extend(token for _, token in rows)
    require(len(ordered) == len(samples), "unresolved sample scene")
    return ordered


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    spec = read_json(args.spec)
    root = Path(__file__).resolve().parents[2]
    require(not args.output_dir.exists(), "output identity already exists")
    for relative, expected in spec["source_sha256"].items():
        require(digest(root / relative) == expected, "source digest differs: " + relative)
    for relative, expected in spec["input_sha256"].items():
        require(digest(args.data_root / relative) == expected, "input digest differs: " + relative)
    require(spec["score_threshold"] == .3 and spec["matching_radius_m"] == 2., "unsupported operating point")
    args.output_dir.mkdir()
    args.output_dir.joinpath("spec.json").write_bytes(args.spec.read_bytes())
    val = literal_assignment(ast.parse((root / spec["split_source"]).read_text()).body, "val")
    scenes, samples, logs, sensors, calibrated = {}, {}, {}, {}, {}
    tables = {"scene.json", "sample.json", "log.json", "sensor.json", "calibrated_sensor.json"}
    meta = args.data_root / "meta.tgz"
    for name, row in rows_from_tables(meta, tables):
        if name == "scene.json" and row["name"] in val:
            require(row["token"] not in scenes, "duplicate scene")
            scenes[row["token"]] = row
        elif name == "sample.json":
            require(row["token"] not in samples, "duplicate sample")
            samples[row["token"]] = row
        elif name == "log.json":
            logs[row["token"]] = row
        elif name == "sensor.json":
            sensors[row["token"]] = row["channel"]
        elif name == "calibrated_sensor.json":
            calibrated[row["token"]] = row["sensor_token"]
    require(Counter(s["name"] for s in scenes.values()) == Counter(val), "official scene membership differs")
    samples = {t: r for t, r in samples.items() if r["scene_token"] in scenes}
    frames = chains(samples, scenes)
    print(f"metadata population: {len(frames)} frames, {len(scenes)} scenes", flush=True)
    ego_ids = {}
    for _, row in rows_from_tables(meta, {"sample_data.json"}):
        if row["sample_token"] in samples and row["is_key_frame"] and sensors[calibrated[row["calibrated_sensor_token"]]] == "LIDAR_TOP":
            require(row["sample_token"] not in ego_ids, "duplicate lidar keyframe")
            ego_ids[row["sample_token"]] = row["ego_pose_token"]
    require(set(ego_ids) == set(samples), "missing lidar ego metadata")
    wanted_ego, poses = set(ego_ids.values()), {}
    for _, row in rows_from_tables(meta, {"ego_pose.json"}):
        if row["token"] in wanted_ego:
            require(row["token"] not in poses, "duplicate ego pose")
            poses[row["token"]] = [number(v) for v in row["translation"][:2]]
    require(set(poses) == wanted_ego, "unresolved ego pose")
    ego = {t: poses[p] for t, p in ego_ids.items()}
    detections, totals = {}, {}
    for channel, relative in spec["prediction_files"].items():
        raw = read_json(args.data_root / relative)["results"]
        coverage(raw, frames)
        by_frame = {}
        raw_count = 0
        for token in frames:
            boxes = []
            for box in raw[token]:
                raw_count += 1
                score = number(box["detection_score"])
                require(0 <= score <= 1, "score outside [0,1]")
                xy = tuple(number(v) for v in box["translation"][:2])
                require(len(xy) == 2, "invalid translation")
                if box["detection_name"] in CLASSES and score >= spec["score_threshold"]:
                    boxes.append((box["detection_name"], score, *xy))
            by_frame[token] = boxes
        detections[channel] = by_frame
        totals[channel] = {"raw": raw_count, "at_operating_point": sum(map(len, by_frame.values()))}
        del raw
        print(f"read {channel} outputs: {totals[channel]}", flush=True)
    # The feature table is completed before the annotation cache is opened.
    feature_rows = [output_features(detections["camera"][t], detections["lidar"][t], ego[t]) for t in frames]
    names = list(feature_rows[0])
    require(all(list(r) == names for r in feature_rows), "feature schema differs")
    X = np.asarray([[r[n] for n in names] for r in feature_rows], dtype=np.float64)
    feature_sha = hashlib.sha256(X.tobytes()).hexdigest()
    print(f"output-only feature table completed: {X.shape}", flush=True)
    gt = read_json(args.data_root / "gt_val_cache.json")
    by_frame = defaultdict(list)
    for i, row in enumerate(gt):
        require(row["sample_token"] in samples and row["cls"] in CLASSES, "cache membership invalid")
        require(type(row["nl"]) is int and type(row["nr"]) is int and row["nl"] >= 0 and row["nr"] >= 0, "point count invalid")
        require(max(abs(number(v) - e) for v, e in zip(row["ego_xy"], ego[row["sample_token"]])) < 1e-8, "cache ego differs from independent metadata")
        by_frame[row["sample_token"]].append(i)
    matches = {c: np.zeros(len(gt), dtype=bool) for c in detections}
    y, y_point, n_reference, n_point = [], [], [], []
    for t in frames:
        indices = by_frame[t]
        annotations = [(gt[i]["cls"], 0., *[number(v) for v in gt[i]["xy"]]) for i in indices]
        for channel in detections:
            for j in match_reference(detections[channel][t], annotations, ego[t]):
                matches[channel][indices[j]] = True
        selected = [i for i in indices if not matches["camera"][i] and not matches["lidar"][i]]
        y.append(len(selected))
        y_point.append(sum(gt[i]["nl"] + gt[i]["nr"] > 0 for i in selected))
        n_reference.append(len(indices))
        n_point.append(sum(gt[i]["nl"] + gt[i]["nr"] > 0 for i in indices))
    # A separately written, inherited scalar matcher checks every annotation flag.
    import match as historical
    match_checks = {}
    for channel in detections:
        preds = {t: [{"detection_name": b[0], "detection_score": b[1], "translation": b[2:]}
                     for b in detections[channel][t]] for t in frames}
        flags = np.zeros(len(gt), dtype=bool)
        for cls in CLASSES:
            idx = {t: [i for i in ids if gt[i]["cls"] == cls] for t, ids in by_frame.items()}
            m, _, _, _ = historical.match_class(idx, gt, preds, cls, 2., ego)
            flags[list(m)] = True
        mismatch = int(np.count_nonzero(flags != matches[channel]))
        require(mismatch == 0, "independent matcher disagreement: " + channel)
        match_checks[channel] = {"annotations_compared": len(gt), "matched": int(flags.sum()), "mismatches": mismatch}
        print(f"scalar matcher agreement {channel}: {match_checks[channel]}", flush=True)
    require(hashlib.sha256(X.tobytes()).hexdigest() == feature_sha, "reference processing changed feature matrix")
    scene = np.asarray([samples[t]["scene_token"] for t in frames])
    data_path = args.output_dir / "dataset.private.npz"
    np.savez_compressed(data_path, X=X, feature_names=np.asarray(names), frames=np.asarray(frames),
        scenes=scene, timestamps=np.asarray([samples[t]["timestamp"] for t in frames], dtype=np.int64),
        logs=np.asarray([scenes[s]["log_token"] for s in scene]),
        locations=np.asarray([logs[scenes[s]["log_token"]]["location"] for s in scene]),
        y=np.asarray(y), y_point=np.asarray(y_point), n_reference=np.asarray(n_reference), n_point=np.asarray(n_point),
        camera_match=matches["camera"], lidar_match=matches["lidar"])
    for relative, expected in spec["input_sha256"].items():
        require(digest(args.data_root / relative) == expected, "input changed during computation")
    report = {"artifact_id": "reiyah.predictive-monitor-dataset.0.1.0", "version": "0.1.0", "lifecycle_status": "exploratory",
        "spec_sha256": digest(args.spec), "dataset_sha256": digest(data_path), "dataset_bytes": data_path.stat().st_size,
        "feature_matrix_raw_sha256": feature_sha, "frames": len(frames), "scenes": len(scenes),
        "logs": len(set(scenes[s]["log_token"] for s in scene)), "feature_names": names,
        "frames_without_cache_annotations": int(np.count_nonzero(np.asarray(n_reference) == 0)),
        "reference_annotations": sum(n_reference), "point_positive_annotations": sum(n_point),
        "joint_misses": sum(y), "point_positive_joint_misses": sum(y_point),
        "predictions": totals, "match_checks": match_checks,
        "physical_joint_misses": None, "online_output_availability": "unmeasured"}
    (args.output_dir / "result.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True), flush=True)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(json.dumps({"status": "invalid", "diagnostic": str(exc)}), file=sys.stderr)
        raise SystemExit(2)
