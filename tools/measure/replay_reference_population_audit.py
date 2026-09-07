#!/usr/bin/env python3
"""Replay the portable auditor on the exact retained AO population.

Local, retrospective research only. The adapter binds cached inclusion IDs to
the original annotation tokens and coordinates. It does not reconstruct the
nuScenes SDK's filtering policy or supply an independent physical reference.
Private per-frame bundles and reports never belong in public Git.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import codecs
from decimal import Decimal
import gc
import hashlib
import json
from pathlib import Path
import sys
import tarfile

from reference_population_audit import INPUT_VERSION, audit, canonical

INPUT_NAMES = ("gt_val_cache.json", "meta.tgz", "predictions/mapillary_val.json",
               "predictions/megvii_val.json")
CLASSES = frozenset(("car", "truck", "bus", "trailer", "construction_vehicle", "pedestrian",
                     "motorcycle", "bicycle", "traffic_cone", "barrier"))


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def unique_pairs(items):
    value = {}
    for key, item in items:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def invalid_constant(_):
    raise ValueError("nonfinite input constant")


def read_json(path: Path):
    with path.open() as handle:
        return json.load(handle, parse_float=Decimal, object_pairs_hook=unique_pairs,
                         parse_constant=invalid_constant)


def array_rows(handle):
    """Incremental strict array framing; preserve each numeric decimal token."""
    decoder = json.JSONDecoder(parse_float=Decimal, object_pairs_hook=unique_pairs,
                               parse_constant=invalid_constant)
    utf8 = codecs.getincrementaldecoder("utf-8")()
    buffer, ended = "", False

    def fill():
        nonlocal buffer, ended
        chunk = handle.read(1024 * 1024)
        ended = not chunk
        buffer += utf8.decode(chunk, final=ended)

    def strip():
        nonlocal buffer
        while not buffer.strip() and not ended:
            fill()
        buffer = buffer.lstrip()

    strip()
    if not buffer.startswith("["):
        raise ValueError("metadata is not an array")
    buffer = buffer[1:]
    after_row, after_comma = False, False
    while True:
        strip()
        if buffer.startswith("]"):
            if after_comma:
                raise ValueError("trailing comma")
            buffer = buffer[1:]
            while not ended:
                fill()
            if buffer.strip():
                raise ValueError("trailing content")
            return
        if not buffer:
            raise ValueError("truncated metadata")
        if after_row:
            if buffer[0] != ",":
                raise ValueError("missing separator")
            buffer, after_row, after_comma = buffer[1:], False, True
            continue
        try:
            row, stop = decoder.raw_decode(buffer)
        except json.JSONDecodeError:
            if ended:
                raise
            fill()
            continue
        yield row
        buffer, after_row, after_comma = buffer[stop:], True, False


def decimal_xy(values):
    if not isinstance(values, list) or len(values) != 2:
        raise ValueError("invalid XY shape")
    result = []
    for value in values:
        if type(value) not in (int, Decimal) or not Decimal(value).is_finite():
            raise ValueError("invalid coordinate")
        result.append(format(Decimal(value), "f"))
    return result


def build_references(data_root: Path):
    cache = read_json(data_root / "gt_val_cache.json")
    cached = defaultdict(dict)
    timestamps = {}
    for row in cache:
        sample, aid = row["sample_token"], row["ann_token"]
        if aid in cached[sample]:
            raise ValueError("duplicate cache annotation")
        if sample in timestamps and timestamps[sample] != row["ts_us"]:
            raise ValueError("mixed cache timestamps")
        cached[sample][aid] = decimal_xy(row["xy"])
        timestamps[sample] = row["ts_us"]
    del cache
    wider, samples = defaultdict(dict), {}
    names = {"sample.json", "sample_annotation.json"}
    found = set()
    with tarfile.open(data_root / "meta.tgz", mode="r|gz") as archive:
        for member in archive:
            name = member.name.rsplit("/", 1)[-1]
            if name not in names or not member.isfile():
                continue
            if name in found:
                raise ValueError("duplicate metadata table")
            found.add(name)
            for row in array_rows(archive.extractfile(member)):
                if name == "sample.json" and row["token"] in cached:
                    if row["token"] in samples:
                        raise ValueError("duplicate sample token")
                    samples[row["token"]] = row
                elif name == "sample_annotation.json" and row["sample_token"] in cached:
                    values = wider[row["sample_token"]]
                    if row["token"] in values:
                        raise ValueError("duplicate annotation token")
                    values[row["token"]] = decimal_xy(row["translation"][:2])
            print("read", name, file=sys.stderr, flush=True)
    if found != names or set(cached) != set(wider) or set(cached) != set(samples):
        raise ValueError("incomplete metadata coverage")
    for sample, annotations in cached.items():
        if timestamps[sample] != samples[sample]["timestamp"]:
            raise ValueError("cache/sample timestamp mismatch")
        for aid, xy in annotations.items():
            if aid not in wider[sample] or [Decimal(v) for v in xy] != [Decimal(v) for v in wider[sample][aid]]:
                raise ValueError("cache ID or position differs from original annotation table")
    return cached, wider, timestamps


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-inputs", type=Path, required=True,
                        help="frozen study selection JSON containing input sizes and digests")
    args = parser.parse_args()
    if args.output_dir.exists():
        raise ValueError("output identity exists; use a new run directory")
    before = {name: {"sha256": digest(args.data_root / name), "bytes": (args.data_root / name).stat().st_size}
              for name in INPUT_NAMES}
    expected_raw = args.expected_inputs.read_bytes()
    expected = json.loads(expected_raw)["inputs"]
    if any(before[name] != expected[name] for name in INPUT_NAMES):
        raise ValueError("raw inputs differ from frozen reference-study inputs")
    args.output_dir.mkdir(parents=True)
    tool = Path(__file__).with_name("reference_population_audit.py")
    spec = {"artifact_id": "reiyah.reference-population-real-replay.0.1.0", "version": "0.1.0",
            "lifecycle_status": "exploratory", "inputs": before,
            "expected_input_record_sha256": hashlib.sha256(expected_raw).hexdigest(),
            "adapter_sha256": digest(Path(__file__)), "auditor_sha256": digest(tool),
            "classes": sorted(CLASSES), "score_threshold": "0.3", "radius_m": "2",
            "selection": "all and only sample tokens in the retained ground-truth cache",
            "raw_numeric_policy": "decimal tokens retained exactly; no coordinate rounding"}
    (args.output_dir / "spec.json").write_bytes(canonical(spec))
    cached, wider, timestamps = build_references(args.data_root)
    closure = []
    channels = {}
    for channel, name in (("camera", INPUT_NAMES[2]), ("lidar", INPUT_NAMES[3])):
        predictions = read_json(args.data_root / name)["results"]
        if not set(cached) <= set(predictions):
            raise ValueError("missing prediction sample must not be treated as empty")
        counts = Counter()
        selected_count = rejected_class = below_threshold = 0
        bundle_path = args.output_dir / (channel + ".bundles.jsonl")
        report_path = args.output_dir / (channel + ".reports.jsonl")
        with bundle_path.open("xb") as bundles, report_path.open("xb") as reports:
            for index, sample in enumerate(sorted(cached)):
                chosen = []
                for position, row in enumerate(predictions[sample]):
                    if row["sample_token"] != sample:
                        raise ValueError("prediction/sample identity mismatch")
                    score = row["detection_score"]
                    if type(score) not in (int, Decimal) or not Decimal(score).is_finite() or not 0 <= score <= 1:
                        raise ValueError("invalid score")
                    if row["detection_name"] not in CLASSES:
                        rejected_class += 1
                    elif score < Decimal("0.3"):
                        below_threshold += 1
                    else:
                        chosen.append({"id": "prediction-" + str(position), "xy_m": decimal_xy(row["translation"][:2])})
                bundle = {"schema_version": INPUT_VERSION,
                          "artifact_id": "reiyah.reference-audit." + channel + "." + sample,
                          "upstream_selection_id": "retained-ao-score-0.3-ten-classes.v1",
                          "evaluation_scope_id": "retained-gt-val-cache.v1",
                          "wider_reference_scope_id": "provided-nuscenes-sample-annotation-table.v1",
                          "radius_m": "2", "frames": [{
                              "id": sample, "timestamp_us": timestamps[sample],
                              "coordinate_frame_id": "nuscenes-global-xy-m",
                              "reference_state": "available",
                              "annotations": [{"id": aid, "xy_m": xy} for aid, xy in sorted(wider[sample].items())],
                              "evaluation_annotation_ids": sorted(cached[sample]), "predictions": chosen}]}
                raw = json.dumps(bundle, sort_keys=True, separators=(",", ":")).encode() + b"\n"
                report = audit(raw)
                bundles.write(raw)
                reports.write(json.dumps(report, sort_keys=True, separators=(",", ":")).encode() + b"\n")
                counts.update(report["counts"])
                selected_count += len(chosen)
                if (index + 1) % 500 == 0:
                    print(channel, index + 1, "samples", selected_count, "predictions", file=sys.stderr, flush=True)
        channels[channel] = {"samples": len(cached), "selected_predictions": selected_count,
                             "rejected_class": rejected_class, "below_threshold": below_threshold,
                             "counts": dict(sorted(counts.items())),
                             "physical_false_positive_rate": None}
        closure.extend({"path": path.name, "byte_size": path.stat().st_size, "sha256": digest(path)}
                       for path in (bundle_path, report_path))
        del predictions
        gc.collect()
    after = {name: {"sha256": digest(args.data_root / name), "bytes": (args.data_root / name).stat().st_size}
             for name in INPUT_NAMES}
    if before != after:
        raise ValueError("inputs changed during replay")
    if spec["auditor_sha256"] != digest(tool) or spec["adapter_sha256"] != digest(Path(__file__)):
        raise ValueError("executed code changed during replay")
    result = {"artifact_id": "reiyah.reference-population-real-replay-result.0.1.0", "version": "0.1.0",
              "lifecycle_status": "exploratory", "spec_sha256": digest(args.output_dir / "spec.json"),
              "channels": channels, "inputs_unchanged": True, "cache_annotation_membership_and_xy_verified": True,
              "private_output_closure": closure,
              "limitations": ["Same retained predictions and reference as AO, not independent sensor inference",
                              "An independent numeric implementation, not independent annotation truth",
                              "Raw bundles and per-prediction reports retained privately",
                              "Upstream evaluator filtering policy not independently reconstructed"]}
    (args.output_dir / "result.json").write_bytes(canonical(result))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
