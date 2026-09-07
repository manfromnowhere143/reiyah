#!/usr/bin/env python3
"""Load a real subset with nuScenes SDK and write private temporal source rows.

No model, camera pixels or point payloads are loaded. Geometry is compared with
an explicit matrix calculation on the first scene/sample in each selected log.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import importlib
import importlib.metadata
import json
from pathlib import Path
import platform

from inventory_training_sensors import CHANNELS, digest, encoded, relative_file


def rotation(values):
    import numpy as np
    q = np.asarray(values, dtype=float)
    if q.shape != (4,) or not np.isfinite(q).all() or abs(np.linalg.norm(q) - 1) > 1e-6:
        raise ValueError("invalid rotation quaternion")
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


def temporal_sources(nusc, sample, maximum_previous=10):
    channels = sample["data"]
    if not set(CHANNELS) <= channels.keys():
        raise ValueError("SDK sample missing requested channel")
    lidar = nusc.get("sample_data", channels["LIDAR_TOP"])
    sweeps, seen, current = [], {lidar["token"]}, lidar
    while current["prev"] and len(sweeps) < maximum_previous:
        previous = nusc.get("sample_data", current["prev"])
        parent = nusc.get("sample", previous["sample_token"])
        if (previous["token"] in seen or previous["channel"] != "LIDAR_TOP"
                or previous["next"] != current["token"] or previous["timestamp"] >= current["timestamp"]
                or parent["scene_token"] != sample["scene_token"]):
            raise ValueError("invalid temporal source boundary")
        seen.add(previous["token"])
        sweeps.append(previous)
        current = previous
    keys = [nusc.get("sample_data", channels[c]) for c in CHANNELS]
    if any(r["sample_token"] != sample["token"] or not r["is_key_frame"] for r in keys):
        raise ValueError("invalid SDK keyframe source")
    return keys, sweeps


def geometry_smoke(nusc):
    import numpy as np
    from nuscenes.utils.geometry_utils import BoxVisibility
    first_by_log = {}
    for scene in sorted(nusc.scene, key=lambda r: r["name"]):
        first_by_log.setdefault(scene["log_token"], scene["first_sample_token"])
    max_center, max_orientation = 0.0, 0.0
    calls, boxes_checked, velocities = 0, 0, Counter()
    for token in first_by_log.values():
        sample = nusc.get("sample", token)
        for channel in CHANNELS:
            sd = nusc.get("sample_data", sample["data"][channel])
            cal = nusc.get("calibrated_sensor", sd["calibrated_sensor_token"])
            pose = nusc.get("ego_pose", sd["ego_pose_token"])
            path, boxes, intrinsic = nusc.get_sample_data(sd["token"], box_vis_level=BoxVisibility.NONE)
            if Path(path) != Path(nusc.dataroot) / sd["filename"] or {b.token for b in boxes} != set(sample["anns"]):
                raise ValueError("SDK geometry opportunity population differs")
            if channel.startswith("CAM_") and not np.array_equal(intrinsic, cal["camera_intrinsic"]):
                raise ValueError("SDK camera intrinsics differ")
            r_pose, r_cal = rotation(pose["rotation"]), rotation(cal["rotation"])
            for box in boxes:
                ann = nusc.get("sample_annotation", box.token)
                expected = r_cal.T @ (r_pose.T @ (np.asarray(ann["translation"]) - pose["translation"]) - cal["translation"])
                orientation = r_cal.T @ r_pose.T @ rotation(ann["rotation"])
                center_error = float(np.max(np.abs(box.center - expected)))
                orientation_error = float(np.max(np.abs(box.orientation.rotation_matrix - orientation)))
                if (not np.isfinite([center_error, orientation_error]).all() or center_error > 1e-8
                        or orientation_error > 1e-8 or not np.array_equal(box.wlh, ann["size"])):
                    raise ValueError("SDK geometry differs from explicit transform")
                max_center = max(max_center, center_error)
                max_orientation = max(max_orientation, orientation_error)
                boxes_checked += 1
            calls += 1
        for ann in sample["anns"]:
            value = nusc.box_velocity(ann)
            state = "finite" if np.isfinite(value).all() else "all_nan_unavailable" if np.isnan(value).all() else "invalid_mixed"
            if state == "invalid_mixed":
                raise ValueError("invalid SDK velocity output")
            velocities[state] += 1
    if not boxes_checked:
        raise ValueError("empty geometry smoke")
    return {"selection": "first sample of lexicographically first scene in every selected log; all seven channels",
            "logs": len(first_by_log), "sensor_calls": calls, "boxes_checked": boxes_checked,
            "max_center_error_m": max_center, "max_rotation_matrix_error": max_orientation,
            "velocity_states": dict(velocities), "tolerance": "1e-8 absolute"}


def run(args):
    import nuscenes.nuscenes as sdk_source
    from nuscenes.nuscenes import NuScenes
    if importlib.metadata.version("nuscenes-devkit") != "1.2.0" or digest(sdk_source.__file__) != args.sdk_source_sha256:
        raise ValueError("SDK implementation identity differs")
    helper_hashes = {"nuscenes.utils.data_classes": "9fd4eb980630af3177768e248de4fa48f5cacf36a1327ec16da56cdc9a64a3ae",
                     "nuscenes.utils.geometry_utils": "6dca908d593e90645d67f0ddf00f3ca7d4d45f6fcf12933da0a70f9eb62caf33",
                     "nuscenes.utils.map_mask": "257e621ab54a73d6b0fb3455aeded45359577630545dd2d44cd90dcadbfc6340"}
    if any(digest(importlib.import_module(name).__file__) != sha for name, sha in helper_hashes.items()):
        raise ValueError("SDK helper identity differs")
    result_file = args.subset / "result.json"
    if digest(result_file) != args.subset_result_sha256 or digest(args.request) != args.request_sha256:
        raise ValueError("input identity differs")
    bound = json.loads(result_file.read_bytes())
    for name, row in bound["tables"].items():
        path = args.subset / "v1.0-trainval" / (name + ".json")
        if digest(path) != row["sha256"]:
            raise ValueError("subset table identity differs")
    maps_record = args.maps / "result.json"
    if digest(maps_record) != args.maps_result_sha256:
        raise ValueError("map identity differs")
    maps = json.loads(maps_record.read_bytes())
    if maps["metadata_sha256"] != bound["source"]["metadata_sha256"]:
        raise ValueError("maps and subset metadata differ")
    # Exact retained maps are copied into a new SDK data root. No sensor path is
    # faked or replaced with an empty stand-in to satisfy an existence check.
    args.output.mkdir(exist_ok=False)
    import shutil
    data = args.output / "sdk-data"
    data.mkdir()
    (data / "v1.0-trainval").symlink_to((args.subset / "v1.0-trainval").resolve(), target_is_directory=True)
    (data / "maps").mkdir()
    map_rows = json.loads((args.subset / "v1.0-trainval/map.json").read_bytes())
    map_files = {}
    for row in map_rows:
        filename = relative_file(row["filename"]).as_posix()
        if len(Path(filename).parts) != 2 or not filename.startswith("maps/"):
            raise ValueError("unsupported map path")
        expected = maps["files"][filename]
        source = args.maps / filename
        if digest(source) != expected["sha256"]:
            raise ValueError("map payload identity differs")
        shutil.copyfile(source, data / filename)
        map_files[filename] = expected
    nusc = NuScenes(version="v1.0-trainval", dataroot=str(data), verbose=True)
    if any(len(getattr(nusc, t)) != row["rows"] for t, row in bound["tables"].items()):
        raise ValueError("SDK table count differs")
    # Bind SDK-derived filenames to the earlier frozen, fully inventoried request.
    available = set()
    with gzip.open(args.request, "rt") as stream:
        header = json.loads(next(stream))
        if header["inputs"]["metadata_sha256"] != bound["source"]["metadata_sha256"]:
            raise ValueError("request metadata differs")
        count = 0
        for line in stream:
            row = json.loads(line)
            count += 1
            if row["sample_token"] in nusc._token2ind["sample"]:
                available.add((row["sample_data_token"], row["filename"]))
        if count != header["asset_count"]:
            raise ValueError("request population differs")
    observed, sweep_counts, opportunities, annotation_count = set(), Counter(), 0, 0
    plan = args.output / "temporal-sources.private.jsonl.gz"
    with plan.open("xb") as raw, gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as stream:
        for sample in sorted(nusc.sample, key=lambda r: r["token"]):
            keys, sweeps = temporal_sources(nusc, sample)
            records = keys + sweeps
            for r in records:
                pair = (r["token"], relative_file(r["filename"]).as_posix())
                if pair not in available:
                    raise ValueError("SDK temporal source outside inventoried request")
                observed.add(pair)
            sweep_counts[len(sweeps)] += 1
            opportunities += 1
            annotation_count += len(sample["anns"])
            stream.write(encoded({"sample_token": sample["token"], "annotation_tokens": sorted(sample["anns"]),
                                  "keyframes": [{"token": r["token"], "filename": r["filename"], "channel": r["channel"]} for r in keys],
                                  "previous_lidar_candidates": [{"token": r["token"], "filename": r["filename"]} for r in sweeps]}))
    if opportunities != len(nusc.sample) or annotation_count != len(nusc.sample_annotation):
        raise ValueError("temporal source opportunity population differs")
    geometry = geometry_smoke(nusc)
    if digest(result_file) != args.subset_result_sha256 or digest(args.request) != args.request_sha256:
        raise ValueError("input changed during smoke")
    for name, row in bound["tables"].items():
        if digest(args.subset / "v1.0-trainval" / (name + ".json")) != row["sha256"]:
            raise ValueError("subset changed during smoke")
    result = {"artifact_id": "reiyah.nuscenes-subset-sdk-smoke.0.1.0", "version": "0.1.0",
              "lifecycle_status": "exploratory", "subset_result_sha256": args.subset_result_sha256,
              "source_sha256": digest(__file__), "sdk_source_sha256": args.sdk_source_sha256,
              "sdk_helper_sha256": helper_hashes,
              "sdk_version": importlib.metadata.version("nuscenes-devkit"), "python": platform.python_version(),
              "dependency_versions": {name: importlib.metadata.version(name) for name in
                                      ("numpy", "pyquaternion", "pillow", "opencv-python-headless", "scipy", "scikit-learn")},
              "request_sha256": args.request_sha256, "maps_result_sha256": args.maps_result_sha256,
              "maps": map_files, "samples": opportunities, "annotations": annotation_count,
              "unique_requested_sensor_files": len(observed), "previous_lidar_counts": dict(sorted(sweep_counts.items())),
              "converter_max_sweeps": 10, "recipe_loader_sweeps_num": 9,
              "loader_selection": "not_run; all cached candidates audited",
              "temporal_source_sha256": digest(plan), "geometry": geometry,
              "sensor_payload_decoding": "not_run", "object_point_database": "not_built", "model_training": "not_run",
              "limits": ["SDK metadata and explicit coordinate transforms only; not a detector preprocessing or prediction test",
                         "Temporal lists include up to ten real previous lidar candidates; the recipe can draw nine of ten",
                         "Camera/lidar payloads are not local to this SDK root and are not opened",
                         "Unavailable velocity stays NaN; no zero substitution", "No causal or independent physical-reference claim"]}
    (args.output / "result.json").write_bytes(encoded(result))
    print(json.dumps(result, sort_keys=True))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("subset", "request", "maps", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    for name in ("subset-result", "request", "maps-result", "sdk-source"):
        p.add_argument("--" + name + "-sha256", required=True)
    run(p.parse_args())


if __name__ == "__main__":
    main()
