#!/usr/bin/env python3
"""Exercise actual annotation parsers and augmentation without fitting models."""
import argparse
from collections import Counter
import copy
import hashlib
import importlib
import inspect
import json
from pathlib import Path

import numpy as np
import torch

from annotation_velocity_bridge import camera_annotation_with_unavailable_velocity, checked_box_availability
from observed_velocity import lidar_annotation_with_unavailable_velocity, velocity_available

VERSION = "0.1.1"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def same(left, right, reason):
    require(np.array_equal(np.asarray(left), np.asarray(right), equal_nan=True), reason)


def parsers(inputs):
    from mmdet3d.datasets import NuScenesDataset, NuScenesMonoDataset
    groups = []
    for group, directory in (("1", "smoke-train-1-1"), ("2", "smoke-train-2-1"), ("val", "smoke-val-2")):
        root = inputs / directory
        record = json.loads((root / "result.json").read_text())
        require(record["group"] == group and record["failed"] == 0, "smoke group differs")
        cache, coco_path = root / "smoke_infos.pkl", root / "smoke_infos_mono3d.coco.json"
        require(sha(cache) == record["info_cache_sha256"], "smoke lidar cache differs")
        require(sha(coco_path) == record["camera_cache"]["sha256"], "smoke camera cache differs")
        lidar = NuScenesDataset(ann_file=str(cache), data_root=str(root / "sdk-data"), pipeline=[],
                                test_mode=True, use_valid_flag=True, filter_empty_gt=False)
        camera = NuScenesMonoDataset(ann_file=str(coco_path), data_root=str(root / "sdk-data"),
                                    pipeline=[], test_mode=True, filter_empty_gt=False)
        counts = Counter()
        for index, info in enumerate(lidar.data_infos):
            original = lidar.get_ann_info(index)
            adapted = lidar_annotation_with_unavailable_velocity(lidar, index)
            available = checked_box_availability(adapted["gt_bboxes_3d"])
            raw = info["gt_velocity"][info["valid_flag"]]
            same(available, velocity_available(raw), "lidar source availability differs")
            old, new = original["gt_bboxes_3d"].tensor.numpy(), adapted["gt_bboxes_3d"].tensor.numpy()
            same(new[:, :7], old[:, :7], "lidar geometry changed")
            same(new[available, 7:], old[available, 7:], "observed lidar velocity changed")
            same(new[:, 7:], raw.astype(np.float32), "lidar source velocity differs")
            same(adapted["gt_labels_3d"], original["gt_labels_3d"], "lidar classes changed")
            require((old[~available, 7:] == 0).all(), "upstream missing lidar control differs")
            counts.update(lidar_samples=1, lidar_annotations=len(new), lidar_unavailable=int((~available).sum()))
        for image in camera.data_infos:
            annotations = camera.coco.load_anns(camera.coco.get_ann_ids(img_ids=[image["id"]]))
            before = json.dumps(annotations, sort_keys=True)
            original = camera._parse_ann_info(image, copy.deepcopy(annotations))
            adapted = camera_annotation_with_unavailable_velocity(camera, image, annotations)
            require(json.dumps(annotations, sort_keys=True) == before, "camera caller annotations mutated")
            available = checked_box_availability(adapted["gt_bboxes_3d"])
            old, new = original["gt_bboxes_3d"].tensor.numpy(), adapted["gt_bboxes_3d"].tensor.numpy()
            same(new[:, :7], old[:, :7], "camera geometry changed")
            same(new[available, 7:], old[available, 7:], "observed camera velocity changed")
            for key in ("bboxes", "labels", "gt_labels_3d", "attr_labels", "centers2d", "depths", "bboxes_ignore"):
                same(adapted[key], original[key], "camera nonvelocity annotation changed: " + key)
            require((old[~available, 7:] == 0).all(), "upstream missing camera control differs")
            # A separate per-annotation invocation checks the batched row trace.
            kept = [i for i, ann in enumerate(annotations)
                    if len(camera._parse_ann_info(image, [copy.deepcopy(ann)])["gt_labels_3d"])]
            same(adapted["source_annotation_indices"], kept, "camera row trace differs from singleton selection")
            counts.update(camera_images=1, camera_annotations=len(new), camera_unavailable=int((~available).sum()))
        require(counts["lidar_samples"] == record["selected"], "lidar smoke opportunity count differs")
        require(counts["camera_images"] == 6 * record["selected"], "camera smoke opportunity count differs")
        require(counts["lidar_unavailable"] > 0 and counts["camera_unavailable"] > 0, "missing-label cases absent")
        groups.append({"group": group, "counts": dict(counts), "source_result_sha256": sha(root / "result.json"),
                       "lidar_cache_sha256": sha(cache), "camera_cache_sha256": sha(coco_path)})
    return groups


def transforms(output):
    import mmcv
    from mmdet3d.core.bbox import LiDARInstance3DBoxes, CameraInstance3DBoxes
    from mmdet3d.core.points import LiDARPoints
    from mmdet3d.datasets.pipelines import GlobalRotScaleTrans, RandomFlip3D, ObjectSample, ObjectRangeFilter
    rows = np.array([[0, 0, 0, 2, 2, 2, 0, 0, 0], [10, 0, 0, 2, 2, 2, 0, 2, 3],
                     [20, 0, 0, 2, 2, 2, 0, np.nan, np.nan]], dtype=np.float32)
    results = []
    for kind, cls in (("lidar", LiDARInstance3DBoxes), ("camera", CameraInstance3DBoxes)):
        boxes = cls(rows.copy(), box_dim=9)
        example = {"gt_bboxes_3d": boxes, "bbox3d_fields": ["gt_bboxes_3d"], "img_fields": [],
                   "gt_labels_3d": np.array([0, 1, 2]), "flip": True, "flip_direction": "horizontal"}
        if kind == "lidar":
            example["points"] = LiDARPoints(np.array([[0, 0, 0, 1, 0]], dtype=np.float32), points_dim=5)
            example = GlobalRotScaleTrans(rot_range=[.31, .31], scale_ratio_range=[1.07, 1.07], translation_std=[0, 0, 0])(example)
        example = RandomFlip3D(sync_2d=True, flip_ratio_bev_horizontal=1.)(example)
        final = example["gt_bboxes_3d"].tensor.numpy()
        same(checked_box_availability(example["gt_bboxes_3d"]), [True, True, False], "augmentation changed availability")
        expected = rows[1, 7:9].copy()
        if kind == "lidar":
            c, s = np.cos(.31), np.sin(.31)
            expected = np.array([2 * c + 3 * s, -2 * s + 3 * c]) * 1.07
            expected[1] *= -1
        else:
            expected[0] *= -1
        require(np.allclose(final[1, 7:9], expected, atol=1e-6, rtol=1e-6), "known velocity transformation differs")
        same(final[0, 7:9], [0., 0.], "observed zero changed")
        results.append({"case": kind + "_training_transforms", "observed_zero_retained": True,
                        "unavailable_pair_retained": True, "known_velocity_matches_separate_formula": True})
    # Exercise the real object sampler, including a sampled unavailable label.
    entries = []
    for i in (1, 2):
        path = output / ("synthetic-object-" + str(i) + ".bin")
        np.array([[0, 0, 0, 1, 0]], dtype=np.float32).tofile(path)
        entries.append({"name": "car", "path": path.name, "box3d_lidar": rows[i].copy(),
                        "num_points_in_gt": 1, "difficulty": 0})
    db_path = output / "synthetic-dbinfos.pkl"
    mmcv.dump({"car": entries}, str(db_path))
    sampler = ObjectSample(db_sampler=dict(type="DataBaseSampler", info_path=str(db_path), data_root=str(output),
                           rate=1., prepare={}, sample_groups={"car": 3}, classes=["car"],
                           points_loader=dict(type="LoadPointsFromFile", coord_type="LIDAR", load_dim=5, use_dim=5)))
    example = {"gt_bboxes_3d": LiDARInstance3DBoxes(rows[:1].copy(), box_dim=9), "gt_labels_3d": np.array([0]),
               "points": LiDARPoints(np.array([[0, 0, 0, 1, 0]], dtype=np.float32), points_dim=5)}
    sampled = sampler(example)
    available = checked_box_availability(sampled["gt_bboxes_3d"])
    require(len(available) == 3 and available.sum() == 2, "actual sampler lost unknown velocity")
    sampled = ObjectRangeFilter(point_cloud_range=[-5, -5, -5, 15, 5, 5])(sampled)
    available = checked_box_availability(sampled["gt_bboxes_3d"])
    require(len(available) == 2 and available.all(), "availability did not follow filtered boxes")
    results.append({"case": "actual_object_sampling_and_range_filter", "sampled_boxes": 3,
                    "sampled_unavailable": 1, "after_range_filter_boxes": 2, "after_range_filter_unavailable": 0})
    rejected = []
    for name, col, value in (("nan_geometry", 0, np.nan), ("negative_dimension", 3, -1.),
                              ("partial_velocity", 7, np.nan), ("infinite_velocity", 7, np.inf)):
        bad = rows[:1].copy(); bad[0, col] = value
        try:
            checked_box_availability(LiDARInstance3DBoxes(bad, box_dim=9))
        except ValueError as error:
            rejected.append({"case": name, "reason": str(error)})
        else:
            raise ValueError("malformed annotation accepted: " + name)
    return results, rejected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(exist_ok=False)
    np.random.seed(20260908)
    groups = parsers(args.inputs)
    augmented, rejected = transforms(args.output)
    modules = {}
    for name in ("mmdet3d.datasets.nuscenes_dataset", "mmdet3d.datasets.nuscenes_mono_dataset",
                 "mmdet3d.datasets.pipelines.transforms_3d", "mmdet3d.datasets.pipelines.dbsampler",
                 "mmdet3d.core.bbox.structures.lidar_box3d", "mmdet3d.core.bbox.structures.cam_box3d"):
        path = Path(inspect.getfile(importlib.import_module(name)))
        modules[name] = {"path": str(path), "sha256": sha(path)}
    result = {"artifact_id": "reiyah.annotation-velocity-probe." + VERSION, "version": VERSION,
              "lifecycle_status": "exploratory", "producer_sha256": sha(__file__), "modules": modules,
              "adapters": {name: sha(Path(__file__).with_name(name)) for name in ("observed_velocity.py", "annotation_velocity_bridge.py")},
              "groups": groups, "synthetic_augmentation": augmented, "rejected": rejected,
              "detector_fits": 0, "sensor_inference": "not_run", "limit": "Parser smoke population plus synthetic augmentation, not full training readiness"}
    (args.output / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, sort_keys=True, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
