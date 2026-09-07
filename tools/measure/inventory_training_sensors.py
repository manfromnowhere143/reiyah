#!/usr/bin/env python3
"""Metadata-bound camera keyframe and lidar-file availability census.

Private requests and per-file observations stay outside public Git. File size
is not sensor validity, content identity, training provenance or readiness.
The scan command uses only the standard library and never opens model weights.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat

VERSION = "0.1.0"
CHANNELS = tuple(sorted(("CAM_FRONT", "CAM_FRONT_LEFT", "CAM_FRONT_RIGHT",
                         "CAM_BACK", "CAM_BACK_LEFT", "CAM_BACK_RIGHT", "LIDAR_TOP")))
TABLES = {"scene.json", "sample.json", "log.json", "sensor.json", "calibrated_sensor.json"}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def unique(rows, key="token"):
    out = {}
    for row in rows:
        token = row[key]
        if not isinstance(token, str) or not token or token in out:
            raise ValueError("missing or duplicate metadata identity")
        out[token] = row
    return out


def relative_file(value):
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ValueError("unsafe asset path")
    p = PurePosixPath(value)
    if not p.parts or p.is_absolute() or p.as_posix() != value or any(x in (".", "..") for x in p.parts):
        raise ValueError("unsafe asset path")
    return p


def make_request(tables, sample_data, train, val):
    if not train or not val or train & val:
        raise ValueError("empty or overlapping official split")
    scenes = unique(tables["scene.json"])
    names = unique(scenes.values(), "name")
    logs = unique(tables["log.json"])
    if not (train | val) <= names.keys():
        raise ValueError("official scene missing")
    sensors = unique(tables["sensor.json"])
    calibrated = unique(tables["calibrated_sensor.json"])
    samples = unique(tables["sample.json"])
    counts = Counter(r["scene_token"] for r in samples.values())
    if set(counts) - scenes.keys() or any(counts[t] != s["nbr_samples"] for t, s in scenes.items()):
        raise ValueError("scene sample count differs")
    selected = {}
    for token, sample in samples.items():
        scene = scenes[sample["scene_token"]]
        if scene["name"] in train | val:
            log = logs[scene["log_token"]]
            selected[token] = {"sample_token": token, "scene": scene["name"],
                               "log": log["token"], "split": "train" if scene["name"] in train else "val"}
    seen_files, seen_tokens, keyframes, assets = set(), set(), set(), []
    for row in sample_data:
        if type(row["is_key_frame"]) is not bool:
            raise ValueError("invalid keyframe flag")
        if row["sample_token"] not in samples:
            raise ValueError("unknown sample-data sample")
        channel = sensors[calibrated[row["calibrated_sensor_token"]]["sensor_token"]]["channel"]
        if row["sample_token"] not in selected or channel not in CHANNELS:
            continue
        if not row["is_key_frame"] and channel != "LIDAR_TOP":
            continue
        filename = relative_file(row["filename"]).as_posix()
        if filename in seen_files or row["token"] in seen_tokens:
            raise ValueError("duplicate asset identity")
        seen_files.add(filename)
        seen_tokens.add(row["token"])
        kind = "keyframe" if row["is_key_frame"] else "sweep"
        if kind == "keyframe":
            key = (row["sample_token"], channel)
            if key in keyframes:
                raise ValueError("duplicate keyframe channel")
            keyframes.add(key)
        assets.append(dict(selected[row["sample_token"]], filename=filename, channel=channel,
                           kind=kind, sample_data_token=row["token"]))
    if keyframes != {(token, channel) for token in selected for channel in CHANNELS}:
        raise ValueError("missing keyframe channel metadata")
    assets.sort(key=lambda r: r["filename"])
    return {"artifact_id": "reiyah.training-sensor-request." + VERSION, "version": VERSION,
            "scope": "six camera keyframes and LIDAR_TOP keyframes/sweeps assigned to official train/val samples",
            "channels": list(CHANNELS), "asset_count": len(assets),
            "sample_counts": dict(Counter(r["split"] for r in selected.values())),
            "scene_counts": dict(Counter("train" if n in train else "val" for n in train | val))}, assets


def write_request(path, header, assets):
    with Path(path).open("xb") as raw, gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as out:
        out.write(encoded(header))
        for row in assets:
            out.write(encoded(row))


def prepare(args):
    from audit_cache_selection import rows_from_tables
    from prepare_training_overlap_probe import literal
    if digest(args.meta) != args.meta_sha256 or digest(args.splits) != args.splits_sha256:
        raise ValueError("input identity differs")
    tree = ast.parse(args.splits.read_text())
    train, val = literal(tree, "train"), literal(tree, "val")
    tables = defaultdict(list)
    for name, row in rows_from_tables(args.meta, TABLES):
        tables[name].append(row)
    header, assets = make_request(tables, (r for _, r in rows_from_tables(args.meta, {"sample_data.json"})), train, val)
    header["inputs"] = {"metadata_sha256": args.meta_sha256, "splits_sha256": args.splits_sha256,
                        "builder_sha256": digest(__file__),
                        "metadata_reader_sha256": digest(Path(__file__).with_name("audit_cache_selection.py")),
                        "array_reader_sha256": digest(Path(__file__).with_name("replay_reference_population_audit.py")),
                        "split_reader_sha256": digest(Path(__file__).with_name("prepare_training_overlap_probe.py"))}
    write_request(args.output, header, assets)
    print(json.dumps(dict(header, request_sha256=digest(args.output)), sort_keys=True))


def observe(root, filename):
    """Never follow a link within a declared root; inventory is for immutable mounts."""
    parts = relative_file(filename).parts
    path = root
    try:
        for i, part in enumerate(parts):
            path = path / part
            value = path.lstat()
            if stat.S_ISLNK(value.st_mode):
                return {"state": "symlink_unresolved", "bytes": None}
            if i < len(parts) - 1 and not stat.S_ISDIR(value.st_mode):
                return {"state": "not_regular", "bytes": None}
        if not stat.S_ISREG(value.st_mode):
            return {"state": "not_regular", "bytes": None}
        return {"state": "present_nonempty" if value.st_size > 0 else "empty", "bytes": value.st_size}
    except FileNotFoundError:
        return {"state": "missing", "bytes": None}
    except PermissionError:
        return {"state": "unreadable_metadata", "bytes": None}
    except OSError as error:
        return {"state": "stat_error", "bytes": None, "errno": error.errno}


def combined_state(candidates):
    states = [r["state"] for r in candidates]
    n = states.count("present_nonempty")
    if n > 1:
        return "multiple_nonempty_uncompared"
    if n == 1:
        return "present_nonempty"
    return "missing" if all(s == "missing" for s in states) else "unresolved"


def scan(request, expected_sha256, roots, output):
    if digest(request) != expected_sha256:
        raise ValueError("request identity differs")
    roots = [Path(r).resolve(strict=True) for r in roots]
    if not roots or len(set(roots)) != len(roots) or not all(r.is_dir() for r in roots):
        raise ValueError("invalid or duplicate roots")
    output = Path(output)
    output.mkdir(exist_ok=False)
    counters, by_log, frames, sizes = defaultdict(Counter), defaultdict(Counter), defaultdict(dict), Counter()
    files, tokens, scenes = set(), set(), defaultdict(set)
    observation = output / "files.private.jsonl.gz"
    with gzip.open(request, "rt") as source, observation.open("xb") as raw, gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as out:
        header = json.loads(next(source))
        if header["artifact_id"] != "reiyah.training-sensor-request." + VERSION or header["channels"] != list(CHANNELS):
            raise ValueError("unsupported request")
        for line in source:
            row = json.loads(line)
            filename = relative_file(row["filename"]).as_posix()
            if filename in files or row["sample_data_token"] in tokens:
                raise ValueError("duplicate request asset")
            if row["channel"] not in CHANNELS or row["split"] not in ("train", "val") or row["kind"] not in ("keyframe", "sweep"):
                raise ValueError("invalid request classification")
            if row["kind"] == "sweep" and row["channel"] != "LIDAR_TOP":
                raise ValueError("unsupported sweep channel")
            files.add(filename)
            tokens.add(row["sample_data_token"])
            candidates = [dict(root=i, **observe(root, filename)) for i, root in enumerate(roots)]
            state = combined_state(candidates)
            counters[(row["split"], row["channel"], row["kind"])][state] += 1
            by_log[(row["split"], row["log"])][state] += 1
            scenes[row["split"]].add(row["scene"])
            if state == "present_nonempty":
                sizes[(row["split"], row["kind"])] += next(r["bytes"] for r in candidates if r["state"] == "present_nonempty")
            if row["kind"] == "keyframe":
                key = (row["split"], row["sample_token"])
                if row["channel"] in frames[key]:
                    raise ValueError("duplicate request keyframe channel")
                frames[key][row["channel"]] = state
            out.write(encoded(dict(row, candidates=candidates, availability=state)))
    if len(files) != header["asset_count"] or not files:
        raise ValueError("request asset count differs or empty")
    sample_counts = Counter(s for s, _ in frames)
    if dict(sample_counts) != header["sample_counts"] or {s: len(v) for s, v in scenes.items()} != header["scene_counts"]:
        raise ValueError("request population differs")
    if any(set(v) != set(CHANNELS) for v in frames.values()):
        raise ValueError("request missing keyframe channel")
    frame_counts = defaultdict(Counter)
    for (split, _), channels in frames.items():
        state = "all_seven_present_nonempty" if all(v == "present_nonempty" for v in channels.values()) else "incomplete_or_unresolved"
        frame_counts[split][state] += 1
    report = {"artifact_id": "reiyah.training-sensor-inventory." + VERSION, "version": VERSION,
              "lifecycle_status": "exploratory", "request": header, "request_sha256": expected_sha256,
              "scanner_sha256": digest(__file__), "observation_sha256": digest(observation),
              "root_count": len(roots), "asset_count": len(files),
              "by_channel": [{"split": s, "channel": c, "kind": k, "states": dict(v)} for (s, c, k), v in sorted(counters.items())],
              "by_log": [{"split": s, "log": log, "states": dict(v)} for (s, log), v in sorted(by_log.items())],
              "frames": {s: dict(v) for s, v in sorted(frame_counts.items())},
              "single_present_copy_bytes": [{"split": s, "kind": k, "bytes": v} for (s, k), v in sorted(sizes.items())],
              "sensor_payload_validity": "not_checked", "model_training_readiness": "not_established",
              "limits": ["File size/metadata only; payload content, readability, calibration, decoding and provenance not validated",
                         "Multiple nonempty copies are unresolved without content comparison; per-root states remain private",
                         "Archives and roots outside the declared scan are not searched",
                         "Lidar sweeps are grouped by metadata sample association, not a particular loader's temporal support",
                         "Observation assumes immutable roots; not a race-resistant scanner for changing filesystems"]}
    (output / "roots.private.json").write_bytes(encoded([str(p) for p in roots]))
    (output / "result.json").write_bytes(encoded(report))
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    b = sub.add_parser("prepare")
    b.add_argument("--meta", type=Path, required=True)
    b.add_argument("--splits", type=Path, required=True)
    b.add_argument("--meta-sha256", required=True)
    b.add_argument("--splits-sha256", required=True)
    b.add_argument("--output", type=Path, required=True)
    s = sub.add_parser("scan")
    s.add_argument("--request", type=Path, required=True)
    s.add_argument("--request-sha256", required=True)
    s.add_argument("--root", type=Path, action="append", required=True)
    s.add_argument("--output-dir", type=Path, required=True)
    args = p.parse_args()
    if args.command == "prepare":
        prepare(args)
    else:
        result = scan(args.request, args.request_sha256, args.root, args.output_dir)
        print(json.dumps({k: v for k, v in result.items() if k not in ("request", "by_log")}, sort_keys=True))


if __name__ == "__main__":
    main()
