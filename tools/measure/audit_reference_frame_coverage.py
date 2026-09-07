#!/usr/bin/env python3
"""Quantify the frame universe omitted by an object-row reference cache.

Retrospective sensitivity analysis; does not expand a frozen study or rewrite AO.
The frame census is derived from supplied prediction keys and independently
cross-checked against sample metadata for their observed scene universe.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import tarfile
from decimal import Decimal

from reference_population_audit import INPUT_VERSION, audit, canonical
from replay_reference_population_audit import INPUT_NAMES, CLASSES, digest, read_json, array_rows, decimal_xy


def frame_universe(cache_samples, prediction_keys, samples):
    if not cache_samples <= prediction_keys:
        raise ValueError("predictions omit cache sample")
    if not prediction_keys <= set(samples):
        raise ValueError("prediction/sample metadata disagreement")
    scenes = {samples[k]["scene_token"] for k in prediction_keys}
    cache_scenes = {samples[k]["scene_token"] for k in cache_samples}
    census = {k for k, row in samples.items() if row["scene_token"] in scenes}
    return {"cache_samples": len(cache_samples), "prediction_samples": len(prediction_keys),
            "omitted_cache_samples": len(prediction_keys - cache_samples),
            "prediction_scene_count": len(scenes), "cache_scene_count": len(cache_scenes),
            "same_scene_universe": scenes == cache_scenes,
            "prediction_keys_equal_metadata_scene_census": prediction_keys == census,
            "metadata_scene_census_samples": len(census)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--prior-replay-spec", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise ValueError("use a new output identity")
    inputs = {name: {"sha256": digest(args.data_root / name), "bytes": (args.data_root / name).stat().st_size}
              for name in INPUT_NAMES}
    prior = json.loads(args.prior_replay_spec.read_bytes())
    if inputs != prior["inputs"]:
        raise ValueError("different inputs from the completed population replay")
    args.output_dir.mkdir(parents=True)
    source_names = (Path(__file__), Path(__file__).with_name("replay_reference_population_audit.py"),
                    Path(__file__).with_name("reference_population_audit.py"))
    spec = {"artifact_id": "reiyah.reference-frame-coverage-spec.0.1.0", "version": "0.1.0",
            "lifecycle_status": "exploratory", "inputs": inputs,
            "sources": {p.name: digest(p) for p in source_names},
            "prospective_claim": False, "score_threshold": "0.3", "radius_m": "2",
            "classes": sorted(CLASSES), "selection": "all prediction keys not represented in the object-row cache"}
    (args.output_dir / "spec.json").write_bytes(canonical(spec))
    cached = {row["sample_token"] for row in read_json(args.data_root / "gt_val_cache.json")}
    keys = None
    omitted_detections = {}
    full_counts = {}
    for channel, filename in (("camera", INPUT_NAMES[2]), ("lidar", INPUT_NAMES[3])):
        predictions = read_json(args.data_root / filename)["results"]
        channel_keys = set(predictions)
        if keys is not None and keys != channel_keys:
            raise ValueError("sensor prediction frame universes differ")
        keys = channel_keys
        missing = keys - cached
        counts = Counter()
        selected = defaultdict(list)
        for sample, rows in predictions.items():
            for index, row in enumerate(rows):
                if row["sample_token"] != sample:
                    raise ValueError("prediction identity mismatch")
                score = row["detection_score"]
                if type(score) not in (int, Decimal) or not Decimal(score).is_finite() or not 0 <= score <= 1:
                    raise ValueError("invalid score")
                if row["detection_name"] in CLASSES and score >= Decimal("0.3"):
                    counts["all_selected"] += 1
                    if sample in missing:
                        selected[sample].append({"id": "prediction-" + str(index), "xy_m": decimal_xy(row["translation"][:2])})
        omitted_detections[channel] = selected
        full_counts[channel] = counts["all_selected"]
        del predictions
    omitted = keys - cached
    samples, annotations = {}, defaultdict(dict)
    tables = set()
    with tarfile.open(args.data_root / "meta.tgz", mode="r|gz") as archive:
        for member in archive:
            name = member.name.rsplit("/", 1)[-1]
            if name not in ("sample.json", "sample_annotation.json") or not member.isfile():
                continue
            if name in tables:
                raise ValueError("duplicate metadata table")
            tables.add(name)
            for row in array_rows(archive.extractfile(member)):
                if name == "sample.json":
                    if row["token"] in samples:
                        raise ValueError("duplicate sample")
                    samples[row["token"]] = row
                elif row["sample_token"] in omitted:
                    if row["token"] in annotations[row["sample_token"]]:
                        raise ValueError("duplicate annotation")
                    annotations[row["sample_token"]][row["token"]] = decimal_xy(row["translation"][:2])
    if tables != {"sample.json", "sample_annotation.json"}:
        raise ValueError("missing metadata tables")
    coverage = frame_universe(cached, keys, samples)
    result = {"artifact_id": "reiyah.reference-frame-coverage.0.1.0", "version": "0.1.0",
              "lifecycle_status": "exploratory", "spec_sha256": digest(args.output_dir / "spec.json"),
              "coverage": coverage, "channels": {},
              "omitted_frames_with_annotations": sum(bool(annotations[s]) for s in omitted),
              "omitted_frames_with_empty_annotation_table": sum(not annotations[s] for s in omitted),
              "omitted_frame_annotation_count": sum(len(annotations[s]) for s in omitted),
              "changes_frozen_study": False,
              "limits": ["The supplied prediction universe is cross-checked against the same observed scenes; official split membership not independently rederived",
                         "Existing AO and study estimands are cache-conditioned; extension is a separate retrospective sensitivity",
                         "Annotation presence and proximity do not establish physical detection correctness"]}
    bundle_path, report_path = args.output_dir / "bundles.jsonl", args.output_dir / "reports.jsonl"
    with bundle_path.open("xb") as bundles, report_path.open("xb") as reports:
        for channel in ("camera", "lidar"):
            counts = Counter()
            for sample in sorted(omitted):
                bundle = {"schema_version": INPUT_VERSION, "artifact_id": "reiyah.omitted-frame." + channel + "." + sample,
                          "upstream_selection_id": "same-prediction-universe-score-0.3.v1",
                          "evaluation_scope_id": "retained-gt-val-cache.v1",
                          "wider_reference_scope_id": "provided-nuscenes-sample-annotation-table.v1", "radius_m": "2",
                          "frames": [{"id": sample, "timestamp_us": samples[sample]["timestamp"],
                                      "coordinate_frame_id": "nuscenes-global-xy-m", "reference_state": "available",
                                      "annotations": [{"id": aid, "xy_m": xy} for aid, xy in sorted(annotations[sample].items())],
                                      "evaluation_annotation_ids": [], "predictions": omitted_detections[channel][sample]}]}
                raw = json.dumps(bundle, sort_keys=True, separators=(",", ":")).encode() + b"\n"
                row = audit(raw)
                bundles.write(raw)
                reports.write(json.dumps(row, sort_keys=True, separators=(",", ":")).encode() + b"\n")
                counts.update(row["counts"])
            result["channels"][channel] = {"all_prediction_frame_selected_detections": full_counts[channel],
                                            "omitted_frame_selected_detections": sum(counts.values()),
                                            "omitted_frame_audit_counts": dict(sorted(counts.items())),
                                            "physical_false_positive_rate": None}
    result["private_output_closure"] = [{"path": p.name, "byte_size": p.stat().st_size, "sha256": digest(p)}
                                        for p in (bundle_path, report_path)]
    if any(digest(args.data_root / name) != binding["sha256"] for name, binding in inputs.items()):
        raise ValueError("input changed")
    if any(digest(p) != spec["sources"][p.name] for p in source_names):
        raise ValueError("source changed")
    result["inputs_unchanged"] = True
    (args.output_dir / "result.json").write_bytes(canonical(result))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
