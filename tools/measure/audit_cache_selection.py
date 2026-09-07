#!/usr/bin/env python3
"""Reconstruct a declared reference-cache selection from retained raw metadata.

No cache-builder or upstream SDK code is executed. The JSON streaming reader is
shared with the earlier research adapter; the selection calculation is separate.
This audits a pre-point-filter cache, not the complete official benchmark.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from decimal import Decimal
from fractions import Fraction
import json
from pathlib import Path
import sys
import tarfile

from reference_population_audit import canonical
from replay_reference_population_audit import array_rows, digest, read_json, INPUT_NAMES


def literal_assignment(nodes, name):
    values = [ast.literal_eval(n.value) for n in nodes if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    if len(values) != 1:
        raise ValueError("expected one literal assignment: " + name)
    return values[0]


def policy_from_sources(source_dir: Path, historical_splits: Path):
    functions = [n for n in ast.parse((source_dir / "P03.payload").read_text()).body
                 if isinstance(n, ast.FunctionDef) and n.name == "category_to_detection_name"]
    if len(functions) != 1:
        raise ValueError("unrecognized upstream category mapping")
    mapping = literal_assignment(functions[0].body, "detection_mapping")
    ranges = json.loads((source_dir / "P02.payload").read_bytes())["class_range"]
    current = literal_assignment(ast.parse((source_dir / "P06.payload").read_text()).body, "val")
    historical = literal_assignment(ast.parse(historical_splits.read_text()).body, "val")
    if len(set(current)) != len(current) or set(current) != set(historical) or len(set(historical)) != len(historical):
        raise ValueError("retained current and historical validation split differ")
    if set(mapping.values()) != set(ranges) or any(type(v) is not int or v <= 0 for v in ranges.values()):
        raise ValueError("unsupported class-range mapping")
    return {"mapping": mapping, "ranges_m": ranges, "validation_scene_names": sorted(current),
            "distance": "exact squared Euclidean XY distance from keyframe LIDAR_TOP ego pose",
            "boundary": "strictly less than class range", "point_filter_applied": False,
            "bike_rack_filter_applied": False,
            "source_interpretation": "Literal fields from manually inspected, hash-bound upstream code; not a general Python semantics parser"}


def rows_from_tables(meta: Path, wanted: set):
    found = set()
    with tarfile.open(meta, mode="r|gz") as archive:
        for member in archive:
            name = member.name.rsplit("/", 1)[-1]
            if name not in wanted:
                continue
            if name in found or not member.isfile():
                raise ValueError("duplicate or nonregular metadata table: " + name)
            found.add(name)
            for row in array_rows(archive.extractfile(member)):
                if not isinstance(row, dict):
                    raise ValueError("metadata row is not an object")
                yield name, row
            print("read", name, file=sys.stderr, flush=True)
    if found != wanted:
        raise ValueError("missing metadata table")


def insert_unique(table: dict, token: str, value):
    if not isinstance(token, str) or not token or token in table:
        raise ValueError("missing or duplicate token")
    table[token] = value


def xy(values):
    if not isinstance(values, list) or len(values) < 2:
        raise ValueError("missing XY coordinate")
    if any(type(v) not in (int, Decimal) or not Decimal(v).is_finite() for v in values[:2]):
        raise ValueError("invalid XY coordinate")
    return tuple(Fraction(v) for v in values[:2])


def classify(raw_class: str, point, ego, policy):
    det = policy["mapping"].get(raw_class)
    if det is None:
        return "unmapped_category", None, None
    d2 = sum((a - b) ** 2 for a, b in zip(xy(point), xy(ego)))
    return ("included" if d2 < policy["ranges_m"][det] ** 2 else "outside_class_range"), det, d2


def membership_result(expected: set, actual: set, metadata_mismatches: int):
    return {"expected_annotation_count": len(expected), "retained_cache_annotation_count": len(actual),
            "expected_absent_from_cache": len(expected - actual),
            "cache_absent_from_expected": len(actual - expected),
            "cache_metadata_mismatches": metadata_mismatches,
            "status": "supported" if expected == actual and metadata_mismatches == 0 else "contradicted"}


def compute(data_root: Path, output_dir: Path, policy):
    meta = data_root / "meta.tgz"
    names = {"category.json", "instance.json", "sample.json", "scene.json", "sensor.json", "calibrated_sensor.json"}
    tables = {name: {} for name in names}
    for name, row in rows_from_tables(meta, names):
        insert_unique(tables[name], row["token"], row)
    scenes = tables["scene.json"]
    scene_names = [r["name"] for r in scenes.values()]
    if len(scene_names) != len(set(scene_names)):
        raise ValueError("duplicate scene name")
    wanted_scenes = set(policy["validation_scene_names"])
    if not wanted_scenes <= set(scene_names):
        raise ValueError("metadata misses validation scenes")
    val_scenes = {token for token, row in scenes.items() if row["name"] in wanted_scenes}
    samples = {token: row for token, row in tables["sample.json"].items() if row["scene_token"] in val_scenes}
    if not samples or {row["scene_token"] for row in samples.values()} != val_scenes:
        raise ValueError("validation scene missing sample census")
    raw_classes = {token: tables["category.json"][row["category_token"]]["name"]
                   for token, row in tables["instance.json"].items()}
    calibrations = {token for token, row in tables["calibrated_sensor.json"].items()
                    if tables["sensor.json"][row["sensor_token"]]["channel"] == "LIDAR_TOP"}
    del tables
    pose_tokens = {}
    for _, row in rows_from_tables(meta, {"sample_data.json"}):
        if row["sample_token"] in samples and row["calibrated_sensor_token"] in calibrations:
            if type(row["is_key_frame"]) is not bool:
                raise ValueError("invalid keyframe flag")
            if row["is_key_frame"]:
                insert_unique(pose_tokens, row["sample_token"], row["ego_pose_token"])
    if set(pose_tokens) != set(samples):
        raise ValueError("missing keyframe LIDAR_TOP pose reference")
    wanted_poses, poses = set(pose_tokens.values()), {}
    for _, row in rows_from_tables(meta, {"ego_pose.json"}):
        if row["token"] in wanted_poses:
            insert_unique(poses, row["token"], row["translation"])
    if set(poses) != wanted_poses:
        raise ValueError("missing keyframe ego pose")
    cache = {}
    for row in read_json(data_root / "gt_val_cache.json"):
        insert_unique(cache, row["ann_token"], row)
    expected, seen, counts, per_class = set(), set(), Counter(), Counter()
    nonempty_frames, zero_point_count, mismatch_count = set(), 0, 0
    rows_path = output_dir / "annotation-dispositions.private.jsonl"
    with rows_path.open("xb") as stream:
        for _, annotation in rows_from_tables(meta, {"sample_annotation.json"}):
            sample = annotation["sample_token"]
            if sample not in samples:
                continue
            aid = annotation["token"]
            if aid in seen:
                raise ValueError("duplicate validation annotation")
            seen.add(aid)
            raw_class = raw_classes[annotation["instance_token"]]
            ego = poses[pose_tokens[sample]]
            reason, det, d2 = classify(raw_class, annotation["translation"], ego, policy)
            counts[reason] += 1
            metadata_errors = []
            if reason == "included":
                expected.add(aid)
                nonempty_frames.add(sample)
                per_class[det] += 1
                zero_point_count += annotation["num_lidar_pts"] + annotation["num_radar_pts"] == 0
                if aid in cache:
                    actual = cache[aid]
                    requirements = {"sample_token": sample, "instance_token": annotation["instance_token"],
                                    "ts_us": samples[sample]["timestamp"], "cls": det, "raw_cls": raw_class,
                                    "nl": annotation["num_lidar_pts"], "nr": annotation["num_radar_pts"]}
                    metadata_errors = [key for key, val in requirements.items() if actual[key] != val]
                    if xy(actual["xy"]) != xy(annotation["translation"]):
                        metadata_errors.append("xy")
                    if xy(actual["ego_xy"]) != xy(ego):
                        metadata_errors.append("ego_xy")
                    mismatch_count += bool(metadata_errors)
            row = {"annotation_id": aid, "sample_token": sample, "selection_reason": reason,
                   "mapped_class": det, "cache_member": aid in cache, "cache_metadata_errors": metadata_errors,
                   "ego_distance_squared_m2": None if d2 is None else {
                       "numerator": str(d2.numerator), "denominator": str(d2.denominator)}}
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")).encode() + b"\n")
    prediction_census = {}
    for channel, name in (("camera", INPUT_NAMES[2]), ("lidar", INPUT_NAMES[3])):
        keys = set(read_json(data_root / name)["results"])
        prediction_census[channel] = {"frame_count": len(keys), "missing_official_validation_frames": len(set(samples) - keys),
                                     "extra_nonvalidation_frames": len(keys - set(samples))}
    comparison = membership_result(expected, set(cache), mismatch_count)
    result = {"annotation_membership": comparison,
              "validation_scene_count": len(val_scenes), "validation_frame_count": len(samples),
              "frames_with_selected_annotations": len(nonempty_frames),
              "frames_without_selected_annotations": len(set(samples) - nonempty_frames),
              "validation_annotation_count": len(seen), "selection_reason_counts": dict(sorted(counts.items())),
              "included_class_counts": dict(sorted(per_class.items())),
              "included_zero_point_annotations": zero_point_count, "prediction_census": prediction_census,
              "physical_false_positive_rate": None}
    differences = {"expected_absent_from_cache": sorted(expected - set(cache)),
                   "cache_absent_from_expected": sorted(set(cache) - expected)}
    (output_dir / "membership-differences.private.json").write_bytes(canonical(differences))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--source-ledger", type=Path, required=True)
    parser.add_argument("--expected-inputs", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise ValueError("output identity exists; retain it and use a new run identity")
    root = Path(__file__).resolve().parents[2]
    upstream = json.loads(args.source_ledger.read_bytes())
    retained = {entry["source_id"]: entry for entry in upstream["entries"]}
    if len(retained) != len(upstream["entries"]) or set(retained) != {"P02", "P03", "P04", "P05", "P06", "P07"}:
        raise ValueError("incomplete primary-source closure")
    for label, entry in retained.items():
        if digest(args.source_dir / (label + ".payload")) != entry["sha256"]:
            raise ValueError("primary source differs from ledger")
    before = {name: {"sha256": digest(args.data_root / name), "bytes": (args.data_root / name).stat().st_size} for name in INPUT_NAMES}
    if before != json.loads(args.expected_inputs.read_bytes())["inputs"]:
        raise ValueError("raw data differ from retained input declaration")
    historical = root / "evidence/nuscenes_splits_devkit.py"
    policy = policy_from_sources(args.source_dir, historical)
    code = {p.name: digest(p) for p in (Path(__file__), Path(__file__).with_name("replay_reference_population_audit.py"),
                                       Path(__file__).with_name("reference_population_audit.py"))}
    spec = {"artifact_id": "reiyah.cache-selection-spec.0.1.0", "version": "0.1.0", "lifecycle_status": "exploratory",
            "inputs": before, "source_ledger_sha256": digest(args.source_ledger),
            "source_payloads": {k: v["sha256"] for k, v in retained.items()}, "sources": code,
            "historical_split_sha256": digest(historical), "policy": policy,
            "question": "Does the retained cache implement its declared split, mapped-class and strict planar range selection?",
            "success_criterion": "Exact annotation-ID set equality and zero checked cache-field disagreements",
            "failure_criterion": "Any extra or missing ID, or a disagreement in the checked cache fields",
            "scope": "Declared cache policy, with point and bike-rack filters intentionally unapplied; not full SDK conformance"}
    args.output_dir.mkdir(parents=True)
    (args.output_dir / "spec.json").write_bytes(canonical(spec))
    outcome = compute(args.data_root, args.output_dir, policy)
    if any(digest(args.data_root / name) != row["sha256"] for name, row in before.items()):
        raise ValueError("raw input changed during audit")
    if any(digest(Path(__file__).with_name(name)) != value for name, value in code.items()):
        raise ValueError("executed code changed during audit")
    if digest(historical) != spec["historical_split_sha256"] or digest(args.source_ledger) != spec["source_ledger_sha256"]:
        raise ValueError("source declaration changed during audit")
    if any(digest(args.source_dir / (label + ".payload")) != value for label, value in spec["source_payloads"].items()):
        raise ValueError("primary source changed during audit")
    result = {"artifact_id": "reiyah.cache-selection-result.0.1.0", "version": "0.1.0", "lifecycle_status": "exploratory",
              "spec_sha256": digest(args.output_dir / "spec.json"), "result": outcome, "inputs_and_sources_unchanged": True,
              "private_output_closure": [{"path": p.name, "bytes": p.stat().st_size, "sha256": digest(p)}
                                         for p in sorted(args.output_dir.glob("*.private.*"))],
              "limits": ["Current upstream source does not establish the exact historical SDK execution environment",
                         "Literal policy extraction is tied to inspected sources; it is not a generic code verifier",
                         "Selection code is independent of the cache builder; raw data and streaming reader are shared",
                         "Annotation membership is not physical object truth, benchmark compliance or scientific acceptance"]}
    (args.output_dir / "result.json").write_bytes(canonical(result))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
