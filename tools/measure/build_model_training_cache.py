#!/usr/bin/env python3
"""Build fresh, contained historical model caches without fitting a detector."""
import argparse
from collections import Counter
import hashlib
import importlib
import importlib.util
import inspect
import json
from pathlib import Path
import shutil

VERSION = "0.1.0"
SUBSETS = {
    "1": (15085, "a438ef8558bfe79de79221f825593289ee294a9a3c612c4b49a1f0f034cc0fe0"),
    "2": (13045, "5e08b07eb283e4ce4727f0aa8fb60c603851eeef3da94c023ab7adcd98a919b2"),
    "val": (6019, "e73ec9590f5357e2d1e1f63a8bcc41327b23fa606976655330d8ec0c985646a0"),
}
CHANNELS = ("CAM_FRONT", "CAM_FRONT_RIGHT", "CAM_FRONT_LEFT", "CAM_BACK", "CAM_BACK_LEFT", "CAM_BACK_RIGHT")
RUNTIME = "5fcffa8ad39cee3b0c51726184bc56fbdc71972906d7b935f2d627692b444d2f"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for data in iter(lambda: stream.read(1 << 20), b""):
            h.update(data)
    return h.hexdigest()


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def write(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def velocity_counts(values):
    import numpy as np
    values = np.asarray(values).reshape(-1, 2)
    available = np.isfinite(values).all(axis=1)
    missing = np.isnan(values).all(axis=1)
    require((available | missing).all(), "invalid or partially unavailable velocity")
    return {"total": len(values), "observed": int(available.sum()), "unavailable": int(missing.sum())}


def main():
    import mmcv
    import numpy as np
    from nuscenes.nuscenes import NuScenes
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=tuple(SUBSETS), required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    expected_count, subset_sha = SUBSETS[args.group]
    subset = args.inputs / "subsets" / args.group
    require(sha(subset / "result.json") == subset_sha, "subset identity differs")
    bound = json.loads((subset / "result.json").read_bytes())
    for table, value in bound["tables"].items():
        require(sha(subset / "v1.0-trainval" / (table + ".json")) == value["sha256"], "subset table identity differs")
    require(sha(args.inputs / "result.json") == RUNTIME, "runtime record identity differs")
    runtime = json.loads((args.inputs / "result.json").read_bytes())
    for name, value in runtime["modules"].items():
        path = Path(value["path"])
        if name.startswith("mmdet3d.") or name in ("torch", "mmcv", "mmdet", "mmdet3d", "nuscenes.nuscenes"):
            path = Path(inspect.getfile(importlib.import_module(name)))
        require(sha(path) == value["sha256"], "runtime source differs: " + name)
    require(shutil.disk_usage(args.output.parent).free >= 30_000_000_000, "insufficient output storage reserve")
    args.output.mkdir(exist_ok=False)
    sdk_root = args.output / "sdk-data"
    sdk_root.mkdir()
    (sdk_root / "v1.0-trainval").symlink_to(subset / "v1.0-trainval", target_is_directory=True)
    for name in ("samples", "sweeps", "maps"):
        (sdk_root / name).symlink_to(args.payload / name, target_is_directory=True)
    nusc = NuScenes(version="v1.0-trainval", dataroot=str(sdk_root), verbose=True)
    require(len(nusc.sample) == expected_count, "subset sample count differs")
    converter_path = Path("/mmdetection3d/tools/data_converter/nuscenes_converter.py")
    spec = importlib.util.spec_from_file_location("bound_converter", converter_path)
    converter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(converter)
    scenes = {r["token"] for r in nusc.scene}
    train, val = converter._fill_trainval_infos(nusc, scenes if args.group != "val" else set(),
                                               scenes if args.group == "val" else set(), max_sweeps=10)
    infos, other = (train, val) if args.group != "val" else (val, train)
    require(not other and [r["token"] for r in infos] == [r["token"] for r in nusc.sample], "converter opportunity population differs")
    totals, sweep_counts, positions = Counter(), Counter(), []
    samples_path = args.output / "samples.private.jsonl"
    with samples_path.open("x") as stream:
        for index, (info, sample) in enumerate(zip(infos, nusc.sample)):
            if index % 1000 == 0:
                require(shutil.disk_usage(args.output).free >= 30_000_000_000, "output storage reserve exhausted")
            require(info["timestamp"] == sample["timestamp"], "sample timestamp differs")
            require(len(info["gt_boxes"]) == len(sample["anns"]), "lidar reference population differs")
            require(np.isfinite(info["gt_boxes"]).all() and (info["gt_boxes"][:, 3:6] > 0).all(), "invalid reference geometry")
            velocity = velocity_counts(info["gt_velocity"])
            scene = nusc.get("scene", sample["scene_token"])
            key = nusc.get("sample_data", sample["data"]["LIDAR_TOP"])
            current, expected = key, []
            while current["prev"] and len(expected) < 10:
                current = nusc.get("sample_data", current["prev"])
                require(nusc.get("sample", current["sample_token"])["scene_token"] == scene["token"], "sweep crosses scene")
                expected.append(current["token"])
            require([s["sample_data_token"] for s in info["sweeps"]] == expected, "temporal candidates differ")
            for channel in CHANNELS:
                require(info["cams"][channel]["sample_data_token"] == sample["data"][channel], "camera opportunity differs")
            sweep_counts[len(expected)] += 1
            totals.update(velocity)
            row = {"sample_token": sample["token"], "scene_token": scene["token"], "log_token": scene["log_token"],
                   "cache_index": index, "candidate_sweep_tokens": expected, "annotation_tokens": sample["anns"],
                   "lidar_velocity": velocity, "valid_sensor_reference": int(info["valid_flag"].sum()),
                   "zero_sensor_point_reference": int((~info["valid_flag"]).sum()),
                   "camera_tokens": [sample["data"][c] for c in CHANNELS]}
            stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
            positions.append(sample["token"])
    cache = args.output / "model_infos.pkl"
    mmcv.dump({"infos": infos, "metadata": {"version": "v1.0-trainval"}}, str(cache))
    converter.export_2d_annotation(str(sdk_root), str(cache), "v1.0-trainval", mono3d=True)
    coco_path = args.output / "model_infos_mono3d.coco.json"
    coco = json.loads(coco_path.read_text())
    require([r["id"] for r in coco["images"]] == [r["cams"][c]["sample_data_token"] for r in infos for c in CHANNELS], "camera cache opportunity population differs")
    image_ids = {r["id"] for r in coco["images"]}
    require(len(image_ids) == expected_count * 6 and all(r["image_id"] in image_ids for r in coco["annotations"]), "camera cache reference containment")
    camera_velocity = velocity_counts([r["velo_cam3d"] for r in coco["annotations"]])
    result = {"artifact_id": "reiyah.full-model-training-cache." + VERSION, "version": VERSION,
              "lifecycle_status": "exploratory", "group": args.group, "samples": expected_count,
              "producer_sha256": sha(__file__), "converter_sha256": sha(converter_path),
              "runtime_identity_sha256": RUNTIME, "subset_sha256": subset_sha,
              "samples_sha256": sha(samples_path), "info_cache_sha256": sha(cache), "info_cache_bytes": cache.stat().st_size,
              "camera_cache_sha256": sha(coco_path), "camera_cache_bytes": coco_path.stat().st_size,
              "camera_images": len(coco["images"]), "camera_annotations": len(coco["annotations"]),
              "lidar_velocity": dict(totals), "camera_velocity": camera_velocity, "candidate_sweep_counts": dict(sweep_counts),
              "source_group_containment": "passed", "object_point_database": "not_built_here",
              "detector_fits": 0, "sensor_inference": "not_run", "payload_decoding": "not_run_here",
              "limits": ["Full upstream metadata/annotation caches; raw velocities remain NaN in private model cache, never observed zeros",
                         "Camera cache follows upstream visibility/category/projection filters; it is not the physical opportunity reference",
                         "Training consumers and loss masking require their own checks; no training readiness or accuracy established"]}
    write(args.output / "result.json", result)
    print(json.dumps(result, sort_keys=True, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
