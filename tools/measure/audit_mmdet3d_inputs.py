#!/usr/bin/env python3
"""Execute a private, metadata-selected payload/loader audit in MMDetection3D.

Requires the separately retained runtime and subset identities. Uses the actual
installed framework; no replacement model, decoder, registry or box class.
The output is an engineering smoke result, never detector performance.
"""
import argparse
from collections import Counter
import copy
import hashlib
import importlib
import importlib.util
import inspect
import json
from pathlib import Path

VERSION = "0.1.1"
SEEDS = (20260907, 20260908)
CHANNELS = ("CAM_FRONT", "CAM_FRONT_RIGHT", "CAM_FRONT_LEFT",
            "CAM_BACK", "CAM_BACK_LEFT", "CAM_BACK_RIGHT")
CONFIGS = {
    "camera": "configs/fcos3d/fcos3d_r101_caffe_fpn_gn-head_dcn_2x8_1x_nus-mono3d_finetune.py",
    "lidar": "configs/centerpoint/centerpoint_0075voxel_second_secfpn_circlenms_4x8_cyclic_20e_nus.py",
}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def array_sha(value):
    import numpy as np
    a = np.ascontiguousarray(value)
    return hashlib.sha256(str((a.dtype.str, a.shape)).encode() + a.tobytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def rotation(q):
    import numpy as np
    q = np.asarray(q, dtype=np.float64)
    if q.shape != (4,) or not np.isfinite(q).all() or abs(np.linalg.norm(q)-1) > 1e-6:
        raise ValueError("invalid quaternion")
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


def sensor_transform(nusc, token):
    import numpy as np
    sd = nusc.get("sample_data", token)
    cal = nusc.get("calibrated_sensor", sd["calibrated_sensor_token"])
    pose = nusc.get("ego_pose", sd["ego_pose_token"])
    t = np.eye(4)
    t[:3, :3] = rotation(pose["rotation"]) @ rotation(cal["rotation"])
    t[:3, 3] = rotation(pose["rotation"]) @ cal["translation"] + pose["translation"]
    return t


def decode_points(path):
    import numpy as np
    data = Path(path).read_bytes()
    if not data or len(data) % 20:
        raise ValueError("invalid five-float point payload length")
    points = np.frombuffer(data, dtype="<f4").reshape(-1, 5)
    if not np.isfinite(points).all():
        raise ValueError("nonfinite raw point payload")
    return points, hashlib.sha256(data).hexdigest()


def decode_image(path, height, width):
    import cv2
    import numpy as np
    data = Path(path).read_bytes()
    if not data.startswith(b"\xff\xd8") or not data.endswith(b"\xff\xd9"):
        raise ValueError("incomplete JPEG envelope")
    image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None or image.shape != (height, width, 3) or image.dtype != np.uint8:
        raise ValueError("decoded camera shape or type differs")
    return image, hashlib.sha256(data).hexdigest()


def isolated_camera_export(detection, exporter):
    """Keep an upstream exporter from changing its caller's tensors."""
    return exporter(copy.deepcopy(detection))


def camera_inverse_preserving_velocity(boxes, inverse):
    """Retain the camera's x,z velocity through the historical inverse."""
    import numpy as np
    result = inverse(copy.deepcopy(boxes))
    velocity = np.asarray([b.velocity[[0, 2]] for b in boxes]).reshape(-1, 2)
    result[0].tensor[:, 7:9] = result[0].tensor.new_tensor(velocity)
    return result


class SelectedSampleView:
    """Limit converter iteration while SDK lookups keep their original index."""
    def __init__(self, nusc, samples):
        self._source = nusc
        self.sample = samples

    def __getattr__(self, name):
        return getattr(self._source, name)


def camera_export_probe():
    import numpy as np
    import torch
    from mmdet3d.core.bbox import CameraInstance3DBoxes
    from mmdet3d.datasets.nuscenes_mono_dataset import output_to_nusc_box, nusc_box_to_cam_box3d
    values = [[2., 1., 18., 4.2, 1.6, 1.8, 0.3, 1.1, 0.2],
              [-3., 2., 25., 0.7, 1.9, 0.6, -1.2, 0., 0.]]
    detection = {"boxes_3d": CameraInstance3DBoxes(values, box_dim=9, origin=(.5, .5, .5)),
                 "scores_3d": torch.tensor([.9, .8]), "labels_3d": torch.tensor([0, 7]),
                 "attrs_3d": torch.tensor([6, 3])}
    original = detection["boxes_3d"].tensor.clone()
    first, _ = output_to_nusc_box(detection)
    after_first = detection["boxes_3d"].tensor.clone()
    second, _ = output_to_nusc_box(detection)
    safe_input = copy.deepcopy(detection)
    safe_input["boxes_3d"].tensor.copy_(original)
    safe_before = safe_input["boxes_3d"].tensor.clone()
    a, _ = isolated_camera_export(safe_input, output_to_nusc_box)
    b, _ = isolated_camera_export(safe_input, output_to_nusc_box)
    safe_unchanged = torch.equal(safe_before, safe_input["boxes_3d"].tensor)
    safe_equal = all(np.array_equal(x.wlh, y.wlh) and np.array_equal(x.center, y.center)
                     and np.array_equal(x.orientation.elements, y.orientation.elements) for x, y in zip(a, b))
    if not safe_unchanged or not safe_equal:
        raise ValueError("isolated camera export is not repeatable and nonmutating")
    expected = np.asarray(values)[:, [5, 3, 4]]
    if not np.allclose([x.wlh for x in a], expected, atol=1e-4, rtol=0):
        raise ValueError("camera dimension convention differs")
    back, _, _ = nusc_box_to_cam_box3d(copy.deepcopy(a))
    back_cpu = back.tensor.cpu().numpy()
    corrected, _, _ = camera_inverse_preserving_velocity(a, nusc_box_to_cam_box3d)
    corrected_cpu = corrected.tensor.cpu().numpy()
    if not np.allclose(corrected_cpu, original.numpy(), atol=1e-4, rtol=0, equal_nan=True):
        raise ValueError("camera inverse does not preserve the native box and velocity")
    # The historical inverse takes velocity[:2] from a camera box although
    # camera planar velocity occupies x,z. Record, do not silently fix it.
    return {
        "native_input_rows": values,
        "upstream_mutates_input": not torch.equal(original, after_first),
        "upstream_first_dimensions": [x.wlh.tolist() for x in first],
        "upstream_second_dimensions": [x.wlh.tolist() for x in second],
        "upstream_first_second_equal": all(np.array_equal(x.wlh, y.wlh) for x, y in zip(first, second)),
        "isolated_export_input_unchanged": safe_unchanged,
        "isolated_export_repeat_equal": safe_equal,
        "inverse_max_box_parameter_error": float(np.max(np.abs(back_cpu[:, :7]-original.numpy()[:, :7]))),
        "inverse_velocity_expected": original.numpy()[:, 7:].tolist(),
        "inverse_velocity_observed": back_cpu[:, 7:].tolist(),
        "corrected_inverse_velocity": corrected_cpu[:, 7:].tolist(),
        "corrected_inverse_max_parameter_error": float(np.max(np.abs(corrected_cpu-original.numpy()))),
        "limit": "Synthetic adapter probe; does not establish why historical detector metrics differ",
    }


def pipeline_input(info, camera=False):
    from mmdet3d.core.bbox import CameraInstance3DBoxes, LiDARInstance3DBoxes, Box3DMode
    r = {"img_fields": [], "bbox3d_fields": [], "pts_mask_fields": [],
         "pts_seg_fields": [], "bbox_fields": [], "mask_fields": [], "seg_fields": []}
    if camera:
        r.update(img_info={"filename": info["data_path"], "cam_intrinsic": info["cam_intrinsic"]},
                 img_prefix="", box_type_3d=CameraInstance3DBoxes, box_mode_3d=Box3DMode.CAM)
    else:
        r.update(pts_filename=info["lidar_path"], sweeps=copy.deepcopy(info["sweeps"]),
                 timestamp=info["timestamp"]/1e6, box_type_3d=LiDARInstance3DBoxes,
                 box_mode_3d=Box3DMode.LIDAR)
    return r


def expected_points(key, sweeps, choices, timestamp, pad):
    import numpy as np
    base = key.copy()
    base[:, 4] = 0
    parts = [base]
    if pad and not sweeps:
        keep = ~((np.abs(base[:, 0]) < 1) & (np.abs(base[:, 1]) < 1))
        parts.extend([base[keep]] * 9)
    for i in choices:
        info, raw = sweeps[i]
        keep = ~((np.abs(raw[:, 0]) < 1) & (np.abs(raw[:, 1]) < 1))
        points = raw[keep].copy()
        points[:, :3] = points[:, :3] @ info["sensor2lidar_rotation"].T
        points[:, :3] += info["sensor2lidar_translation"]
        points[:, 4] = timestamp/1e6-info["timestamp"]/1e6
        parts.append(points)
    return np.concatenate(parts)


def check_voxels(points, config):
    import numpy as np
    import torch
    from mmdet3d.ops import Voxelization
    operation = Voxelization(**config).eval()
    voxels, coords, numbers = operation(torch.from_numpy(points))
    actual_coords, actual_numbers, actual_voxels = coords.numpy(), numbers.numpy(), voxels.numpy()
    size = np.asarray(config["voxel_size"], dtype=np.float32)
    low = np.asarray(config["point_cloud_range"][:3], dtype=np.float32)
    high = np.asarray(config["point_cloud_range"][3:], dtype=np.float32)
    grid = np.round((high-low)/size).astype(int)
    cells = np.floor((points[:, :3]-low)/size).astype(int)
    valid = ((cells >= 0) & (cells < grid)).all(axis=1)
    max_voxels = config["max_voxels"][-1] if isinstance(config["max_voxels"], (list, tuple)) else config["max_voxels"]
    table = {}
    for point, cell in zip(points[valid], cells[valid]):
        key = tuple(cell[::-1])
        if key not in table:
            if len(table) >= max_voxels:
                continue
            table[key] = []
        if len(table[key]) < config["max_num_points"]:
            table[key].append(point)
    if not np.array_equal(actual_coords, np.asarray(list(table), dtype=np.int32)):
        raise ValueError("voxel coordinates or first-occurrence order differs")
    if not np.array_equal(actual_numbers, [len(v) for v in table.values()]):
        raise ValueError("voxel occupancy or truncation differs")
    for i, values in enumerate(table.values()):
        if not np.array_equal(actual_voxels[i, :len(values)], values):
            raise ValueError("voxel contents differ")
    return {"input_points": len(points), "in_range_points": int(valid.sum()), "voxels": len(table),
            "retained_points": int(actual_numbers.sum()), "coordinate_sha256": array_sha(actual_coords),
            "contents_sha256": array_sha(actual_voxels)}


def audit_sample(nusc, sample, info, cfgs, pipelines, output):
    import numpy as np
    from mmdet3d.datasets.pipelines import Compose
    result = {"sample_token": sample["token"], "state": "passed", "files": [], "cameras": []}
    if info["token"] != sample["token"]:
        raise ValueError("cache opportunity identity differs")
    key_sd = nusc.get("sample_data", sample["data"]["LIDAR_TOP"])
    inverse = np.linalg.inv(sensor_transform(nusc, key_sd["token"]))
    current = key_sd
    expected_tokens = []
    while current["prev"] and len(expected_tokens) < 10:
        current = nusc.get("sample_data", current["prev"])
        if nusc.get("sample", current["sample_token"])["scene_token"] != sample["scene_token"]:
            raise ValueError("sweep crosses scene")
        expected_tokens.append(current["token"])
    if [s["sample_data_token"] for s in info["sweeps"]] != expected_tokens:
        raise ValueError("converter temporal source population differs")
    key, digest = decode_points(info["lidar_path"])
    result["files"].append({"filename": key_sd["filename"], "sha256": digest, "rows": len(key), "kind": "lidar"})
    sweeps = []
    errors = []
    for sweep in info["sweeps"]:
        sd = nusc.get("sample_data", sweep["sample_data_token"])
        transform = inverse @ sensor_transform(nusc, sd["token"])
        error = max(float(np.max(np.abs(transform[:3, :3]-sweep["sensor2lidar_rotation"]))),
                    float(np.max(np.abs(transform[:3, 3]-sweep["sensor2lidar_translation"]))))
        if error > 1e-8 or not np.isfinite(error):
            raise ValueError("converter sensor transform differs")
        errors.append(error)
        raw, digest = decode_points(sweep["data_path"])
        sweeps.append((sweep, raw))
        result["files"].append({"filename": sd["filename"], "sha256": digest, "rows": len(raw), "kind": "lidar"})
    result["candidate_sweeps"] = len(sweeps)
    result["max_transform_error"] = max(errors, default=0.)
    result["padded_repeated_keyframes"] = 9 if not sweeps else 0
    outputs = {}
    for rule in ("recipe", "nearest"):
        hashes, selections = [], []
        for seed in SEEDS:
            np.random.seed(seed)
            loader = Compose([
                dict(type="LoadPointsFromFile", coord_type="LIDAR", load_dim=5, use_dim=5),
                dict(type="LoadPointsFromMultiSweeps", sweeps_num=9, use_dim=[0, 1, 2, 3, 4],
                     pad_empty_sweeps=True, remove_close=True, test_mode=rule == "nearest")])
            actual = loader(pipeline_input(info))["points"].tensor.numpy()
            choices = list(range(len(sweeps))) if len(sweeps) <= 9 else (
                list(range(9)) if rule == "nearest" else np.random.RandomState(seed).choice(len(sweeps), 9, replace=False).tolist())
            expected = expected_points(key, sweeps, choices, info["timestamp"], True)
            if actual.shape != expected.shape or not np.allclose(actual, expected, atol=1e-4, rtol=1e-6):
                raise ValueError("actual point loader differs from explicit payload calculation")
            hashes.append(array_sha(actual))
            selections.append(choices)
            if rule == "nearest" and seed == SEEDS[0]:
                result["voxelization"] = check_voxels(actual, cfgs["lidar"].model.pts_voxel_layer)
        outputs[rule] = {"point_hashes": hashes, "candidate_indices": selections,
                         "equal_across_seeds": hashes[0] == hashes[1]}
    if not outputs["nearest"]["equal_across_seeds"]:
        raise ValueError("nearest-sweep result depends on seed")
    result["sweep_rules"] = outputs
    full_hashes = []
    for seed in SEEDS:
        np.random.seed(seed)
        full = pipelines["lidar"](pipeline_input(info))
        full_hashes.append(array_sha(full["points"][0].data.numpy()))
    result["actual_test_pipeline"] = {"hashes": full_hashes, "equal_across_seeds": full_hashes[0] == full_hashes[1]}
    normalization = cfgs["camera"].img_norm_cfg
    for channel in CHANNELS:
        cam = info["cams"][channel]
        sd = nusc.get("sample_data", sample["data"][channel])
        if cam["sample_data_token"] != sd["token"]:
            raise ValueError("converter camera opportunity differs")
        image, digest = decode_image(cam["data_path"], sd["height"], sd["width"])
        result["files"].append({"filename": sd["filename"], "sha256": digest, "kind": "camera",
                                "height": sd["height"], "width": sd["width"]})
        actual = pipelines["camera"](pipeline_input(cam, camera=True))
        tensor = actual["img"][0].data.numpy()
        meta = actual["img_metas"][0].data
        if not np.array_equal(meta["cam2img"], cam["cam_intrinsic"]) or meta["flip"]:
            raise ValueError("camera intrinsics or unaugmented flip state differs")
        expected = image.astype(np.float32)
        if normalization["to_rgb"]:
            expected = expected[:, :, ::-1]
        expected = (expected-np.asarray(normalization["mean"], dtype=np.float32)) / np.asarray(normalization["std"], dtype=np.float32)
        padded = np.zeros((int(np.ceil(sd["height"]/32)*32), int(np.ceil(sd["width"]/32)*32), 3), dtype=np.float32)
        padded[:sd["height"], :sd["width"]] = expected
        expected = padded.transpose(2, 0, 1)
        if tensor.shape != expected.shape or not np.allclose(tensor, expected, atol=1e-4, rtol=1e-6):
            raise ValueError("actual camera normalization or padding differs")
        result["cameras"].append({"channel": channel, "shape": list(tensor.shape),
                                  "tensor_sha256": array_sha(tensor),
                                  "max_normalization_error": float(np.max(np.abs(tensor-expected)))})
    velocity = info["gt_velocity"]
    finite = np.isfinite(velocity).all(axis=1)
    unavailable = np.isnan(velocity).all(axis=1)
    if not np.all(finite | unavailable):
        raise ValueError("mixed unavailable annotation velocity")
    result["annotations"] = {"count": len(info["gt_boxes"]), "finite_velocity": int(finite.sum()),
                              "unavailable_velocity": int(unavailable.sum()),
                              "zero_sensor_point_reference": int((~info["valid_flag"]).sum())}
    return result


def run(args):
    import numpy as np
    import mmcv
    from nuscenes.nuscenes import NuScenes
    from mmdet3d.datasets.pipelines import Compose
    if sha(args.selection) != args.selection_sha256 or sha(args.runtime_identity) != args.runtime_identity_sha256:
        raise ValueError("selection or runtime identity differs")
    identity = json.loads(args.runtime_identity.read_text())
    for name, expected in identity["modules"].items():
        path = Path(expected["path"])
        if name.startswith("mmdet3d.") or name in ("torch", "mmcv", "mmdet", "mmdet3d", "nuscenes.nuscenes"):
            path = Path(inspect.getfile(importlib.import_module(name)))
        if sha(path) != expected["sha256"]:
            raise ValueError("loaded runtime source identity differs: " + name)
    bound_file = args.subset / "result.json"
    if sha(bound_file) != args.subset_sha256:
        raise ValueError("subset result identity differs")
    bound = json.loads(bound_file.read_text())
    for table, expected in bound["tables"].items():
        if sha(args.subset / "v1.0-trainval" / (table + ".json")) != expected["sha256"]:
            raise ValueError("subset metadata identity differs")
    args.output.mkdir(exist_ok=False)
    data_root = args.output / "sdk-data"
    data_root.mkdir()
    (data_root / "v1.0-trainval").symlink_to(args.subset / "v1.0-trainval", target_is_directory=True)
    for name in ("samples", "sweeps", "maps"):
        (data_root / name).symlink_to(args.payload_root / name, target_is_directory=True)
    nusc = NuScenes(version="v1.0-trainval", dataroot=str(data_root), verbose=True)
    selected = [r for r in json.loads(args.selection.read_text()) if r["group"] == args.group]
    if not selected or len({r["sample_token"] for r in selected}) != len(selected):
        raise ValueError("empty or duplicate selected population")
    samples = []
    for row in selected:
        sample = nusc.get("sample", row["sample_token"])
        scene = nusc.get("scene", sample["scene_token"])
        if (sample["timestamp"] != row["timestamp"] or scene["token"] != row["scene_token"]
                or scene["log_token"] != row["log_token"] or scene["name"] != row["scene_name"]):
            raise ValueError("selected metadata identity differs")
        samples.append(sample)
    cfgs = {name: mmcv.Config.fromfile(str(args.framework / path)) for name, path in CONFIGS.items()}
    pipelines = {name: Compose(cfg.test_pipeline) for name, cfg in cfgs.items()}
    if cfgs["lidar"].test_pipeline[1].get("test_mode", False):
        raise ValueError("historical recipe sweep mode unexpectedly differs")
    spec = importlib.util.spec_from_file_location("retained_converter", args.framework / "tools/data_converter/nuscenes_converter.py")
    converter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(converter)
    scenes = {s["scene_token"] for s in samples}
    train, validation = converter._fill_trainval_infos(SelectedSampleView(nusc, samples), scenes if args.group != "val" else set(),
                                                      scenes if args.group == "val" else set(), max_sweeps=10)
    infos = train if args.group != "val" else validation
    other = validation if args.group != "val" else train
    if other or [r["token"] for r in infos] != [s["token"] for s in samples]:
        raise ValueError("converter dropped, reordered or added selected opportunities")
    cache = args.output / "smoke_infos.pkl"
    mmcv.dump({"infos": infos, "metadata": {"version": "v1.0-trainval"}}, str(cache))
    write_json(args.output / "resolved-pipelines.json",
               {k: {"test_pipeline": v.test_pipeline, "model_input": v.model.get("pts_voxel_layer", {})} for k, v in cfgs.items()})
    write_json(args.output / "camera-export-probe.json", camera_export_probe())
    records = []
    with (args.output / "samples.private.jsonl").open("w") as stream:
        for i, (sample, info) in enumerate(zip(samples, infos)):
            try:
                record = audit_sample(nusc, sample, info, cfgs, pipelines, args.output)
            except Exception as error:
                record = {"sample_token": sample["token"], "state": "failed",
                          "error_type": type(error).__name__, "error": str(error)}
            records.append(record)
            stream.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
            print(json.dumps({"finished": i+1, "total": len(samples), "state": record["state"]}), flush=True)
    passed = [r for r in records if r["state"] == "passed"]
    coco_summary = {"state": "not_run_due_to_failed_smoke"}
    if len(passed) == len(records):
        # This exporter reopens only the freshly generated, private pickle.
        # Never pass a historical/untrusted pickle to this entry point.
        converter.export_2d_annotation(str(data_root), str(cache), "v1.0-trainval", mono3d=True)
        coco_path = args.output / "smoke_infos_mono3d.coco.json"
        coco = json.loads(coco_path.read_text())
        expected_images = [info["cams"][channel]["sample_data_token"] for info in infos for channel in CHANNELS]
        if [image["id"] for image in coco["images"]] != expected_images:
            raise ValueError("camera annotation cache opportunity population differs")
        velocities = np.asarray([a["velo_cam3d"] for a in coco["annotations"]])
        finite = np.isfinite(velocities).all(axis=1)
        unavailable = np.isnan(velocities).all(axis=1)
        if not (finite | unavailable).all():
            raise ValueError("camera cache has mixed unavailable velocity")
        coco_summary = {"state": "created", "sha256": sha(coco_path), "images": len(coco["images"]),
                        "annotations": len(coco["annotations"]), "finite_velocity": int(finite.sum()),
                        "unavailable_velocity": int(unavailable.sum()),
                        "format_limit": "Upstream JSON may contain NaN for unavailable velocity; private model cache, not strict evidence JSON"}
    result = {"artifact_id": "reiyah.mmdet3d-input-smoke." + VERSION, "version": VERSION,
              "lifecycle_status": "exploratory", "group": args.group,
              "selected": len(samples), "passed": len(passed), "failed": len(records)-len(passed),
              "subset_sha256": args.subset_sha256, "selection_sha256": args.selection_sha256,
              "runtime_identity_sha256": args.runtime_identity_sha256, "producer_sha256": sha(__file__),
              "sample_rows_sha256": sha(args.output / "samples.private.jsonl"), "info_cache_sha256": sha(cache),
              "camera_cache": coco_summary,
              "candidate_sweep_counts": dict(Counter(r["candidate_sweeps"] for r in passed)),
              "recipe_seed_changed_points": sum(not r["sweep_rules"]["recipe"]["equal_across_seeds"] for r in passed),
              "full_pipeline_seed_changed_points": sum(not r["actual_test_pipeline"]["equal_across_seeds"] for r in passed),
              "nearest_seed_changed_points": sum(not r["sweep_rules"]["nearest"]["equal_across_seeds"] for r in passed),
              "limits": ["Metadata-selected smoke population, not all sensor payloads",
                         "No detector prediction, fitting, calibration or full training object database",
                         "Upstream unavailable velocity and input mutation stay explicit",
                         "No Gate A acceptance or independent scientific verification"]}
    write_json(args.output / "result.json", result)
    if result["failed"]:
        raise ValueError("selected payload or model preprocessing failed; all selected states retained")
    print(json.dumps(result, sort_keys=True), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("selection", "runtime-identity", "subset", "payload-root", "framework", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("selection-sha256", "runtime-identity-sha256", "subset-sha256", "group"):
        parser.add_argument("--" + name, required=True)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
