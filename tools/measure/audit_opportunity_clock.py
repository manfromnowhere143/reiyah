#!/usr/bin/env python3
"""Metadata-only opportunity clock census; no annotations or predictions read."""
import argparse
import ast
from collections import Counter
import json
from pathlib import Path
import sys

from audit_cache_selection import literal_assignment, rows_from_tables
from replay_reference_population_audit import digest, read_json


TABLES = {"scene.json", "sample.json", "sample_data.json", "sensor.json", "calibrated_sensor.json"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique(table, token, value):
    require(isinstance(token, str) and bool(token) and token not in table, "missing or repeated metadata identity")
    table[token] = value


def timestamp(value):
    require(type(value) is int and value > 0, "invalid capture or sample timestamp")
    return value


def summarize(scenes, samples, records, calibrated, sensors, validation_names, required_channels, context_us):
    require(type(context_us) is int and context_us >= 0, "invalid context duration")
    require(len(validation_names) == len(set(validation_names)), "duplicate requested scene name")
    require(required_channels and len(required_channels) == len(set(required_channels)), "invalid channel set")
    chosen = {token: row for token, row in scenes.items() if row["name"] in validation_names}
    require(Counter(row["name"] for row in chosen.values()) == Counter(validation_names), "official scene membership differs")
    frame_ids = {token for token, row in samples.items() if row["scene_token"] in chosen}
    require(bool(frame_ids), "empty official sample population")
    by_frame = {token: {} for token in frame_ids}
    for token, frame, cal, captured in records:
        if frame not in frame_ids:
            continue
        require(cal in calibrated and calibrated[cal] in sensors, "unresolved sensor calibration identity")
        channel = sensors[calibrated[cal]]
        if channel not in required_channels:
            continue
        require(channel not in by_frame[frame], "multiple keyframes for the same sample and channel")
        by_frame[frame][channel] = {"sample_data_token": token, "capture_timestamp_us": timestamp(captured)}
    deltas = {channel: [] for channel in required_channels}
    gaps, rows, per_scene = [], [], []
    for scene_id, scene in sorted(chosen.items()):
        require(type(scene["nbr_samples"]) is int and scene["nbr_samples"] > 0, "invalid declared scene sample count")
        ordered = sorted(((timestamp(samples[t]["timestamp"]), t) for t in frame_ids if samples[t]["scene_token"] == scene_id))
        require(bool(ordered) and len(ordered) == scene["nbr_samples"], "scene sample count differs")
        require(ordered[0][1] == scene["first_sample_token"] and ordered[-1][1] == scene["last_sample_token"], "scene endpoint identity differs")
        times = [t for t, _ in ordered]
        require(all(a < b for a, b in zip(times, times[1:])), "non-increasing sample clock")
        gaps.extend(b - a for a, b in zip(times, times[1:]))
        eligible = 0
        for index, (time, frame) in enumerate(ordered):
            sample = samples[frame]
            require(sample["prev"] == (ordered[index - 1][1] if index else "") and
                    sample["next"] == (ordered[index + 1][1] if index + 1 < len(ordered) else ""), "sample chain differs from time ordering")
            context = time - times[0] >= context_us and times[-1] - time >= context_us
            eligible += context
            channels = {}
            for channel in required_channels:
                record = by_frame[frame].get(channel)
                if record is None:
                    channels[channel] = {"metadata_state": "missing", "capture_delta_us": None,
                                         "payload_validity": "not_checked", "online_availability_time": "unmeasured"}
                else:
                    delta = record["capture_timestamp_us"] - time
                    deltas[channel].append(delta)
                    channels[channel] = {**record, "metadata_state": "present", "capture_delta_us": delta,
                                         "payload_validity": "not_checked", "online_availability_time": "unmeasured"}
            rows.append({"scene_token": scene_id, "sample_token": frame, "anchor_timestamp_us": time,
                         "has_declared_scene_context": context, "channels": channels})
        per_scene.append({"scene_token": scene_id, "frame_count": len(ordered), "context_anchor_count": eligible,
                          "scene_extent_us": times[-1] - times[0]})
    offsets = {}
    for channel, values in deltas.items():
        absolute = sorted(abs(v) for v in values)
        offsets[channel] = {"metadata_present": len(values), "metadata_missing": len(frame_ids) - len(values),
                            "signed_min_us": min(values) if values else None, "signed_max_us": max(values) if values else None,
                            "absolute_p95_nearest_rank_us": absolute[(95 * len(absolute) + 99) // 100 - 1] if absolute else None,
                            "later_than_anchor_capture_count": sum(v > 0 for v in values)}
    result = {"validation_scene_count": len(chosen), "sample_anchor_count": len(frame_ids),
              "clock_context_us_each_side": context_us, "context_anchor_count": sum(r["context_anchor_count"] for r in per_scene),
              "scenes_with_context_anchors": sum(r["context_anchor_count"] > 0 for r in per_scene),
              "adjacent_anchor_gap_us": {"count": len(gaps), "min": min(gaps) if gaps else None, "max": max(gaps) if gaps else None},
              "per_channel": offsets,
              "anchors_with_all_required_keyframe_metadata": sum(all(v["metadata_state"] == "present" for v in r["channels"].values()) for r in rows),
              "sensor_payload_validity": "not_checked", "online_availability_times": "unmeasured",
              "physical_opportunity_completeness": "unknown", "physical_joint_error_coefficient": None,
              "pilot_selection": "not_performed"}
    return result, rows, per_scene


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--meta", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    spec = read_json(args.spec)
    require(set(spec) == {"artifact_id", "version", "lifecycle_status", "metadata_sha256", "source_sha256",
                         "split_source", "validation_scene_name_count", "required_channels", "context_us_each_side"},
            "missing or unknown clock specification property")
    require(spec["artifact_id"] == "reiyah.opportunity-clock-spec.0.1.0" and spec["version"] == "0.1.0"
            and spec["lifecycle_status"] == "exploratory", "unsupported clock specification")
    require(not args.output_dir.exists(), "output identity already exists")
    require(digest(args.meta) == spec["metadata_sha256"], "metadata bytes differ")
    for relative, expected in spec["source_sha256"].items():
        require(digest(root / relative) == expected, "source bytes differ: " + relative)
    split = root / spec["split_source"]
    validation_names = literal_assignment(ast.parse(split.read_text()).body, "val")
    require(len(validation_names) == spec["validation_scene_name_count"], "split cardinality differs")
    args.output_dir.mkdir()
    args.output_dir.joinpath("spec.json").write_bytes(args.spec.read_bytes())
    scenes, samples, sensors, calibrated, records = {}, {}, {}, {}, []
    table_counts = Counter()
    keyframe_tokens = set()
    for name, row in rows_from_tables(args.meta, TABLES):
        table_counts[name] += 1
        if name == "scene.json":
            unique(scenes, row["token"], {k: row[k] for k in ("name", "nbr_samples", "first_sample_token", "last_sample_token")})
        elif name == "sample.json":
            unique(samples, row["token"], {k: row[k] for k in ("scene_token", "timestamp", "prev", "next")})
        elif name == "sensor.json":
            unique(sensors, row["token"], row["channel"])
        elif name == "calibrated_sensor.json":
            unique(calibrated, row["token"], row["sensor_token"])
        else:
            require(type(row["is_key_frame"]) is bool, "invalid keyframe state")
            if row["is_key_frame"]:
                require(row["token"] not in keyframe_tokens and len(records) < 600000, "duplicate or excessive keyframe records")
                keyframe_tokens.add(row["token"])
                records.append((row["token"], row["sample_token"], row["calibrated_sensor_token"], timestamp(row["timestamp"])))
    result, rows, per_scene = summarize(scenes, samples, records, calibrated, sensors, validation_names,
                                       spec["required_channels"], spec["context_us_each_side"])
    closure = []
    for name, values in (("frame-clock.private.jsonl", rows), ("scene-clock.private.jsonl", per_scene)):
        path = args.output_dir / name
        with path.open("w") as stream:
            for row in values:
                stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
        closure.append({"path": name, "sha256": digest(path), "bytes": path.stat().st_size})
    report = {"artifact_id": "reiyah.opportunity-clock-audit.0.1.0", "version": "0.1.0", "lifecycle_status": "exploratory",
              "spec_sha256": digest(args.spec), "metadata_tables_read": dict(table_counts), "result": result,
              "private_output_closure": closure,
              "limits": ["No annotation or prediction table was parsed; selection depends only on official scene membership and clock extent",
                         "Sensor metadata presence does not establish payload validity, online availability or physical observability",
                         "Context eligibility measures scene extent, not continuous visibility or adequate reference coverage",
                         "No pilot sample, independent labels, physical error rate or safety claim was produced"]}
    raw = json.dumps(report, indent=2, sort_keys=True) + "\n"
    (args.output_dir / "result.json").write_text(raw)
    print(raw, end="")


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"status": "invalid", "diagnostic": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
