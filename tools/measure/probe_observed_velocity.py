#!/usr/bin/env python3
"""Exercise actual configured losses and heads using synthetic target tensors."""
import argparse
import copy
import hashlib
import importlib
import inspect
import json
from pathlib import Path

import numpy as np
import torch

from observed_velocity import ObservedRegressionLoss, velocity_available


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def evaluate(loss, target, weights, safe, device):
    prediction = torch.tensor([[1., 2.], [3., -4.]], device=device, requires_grad=True)
    target = torch.tensor(target, device=device)
    weights = torch.tensor(weights, device=device)
    function = ObservedRegressionLoss(loss) if safe else loss
    value = function(prediction, target, weight=weights, avg_factor=2.)
    value.backward()
    gradient = prediction.grad.detach()
    return {"loss_state": "finite" if torch.isfinite(value) else "nonfinite",
            "loss": float(value.detach()) if torch.isfinite(value) else None,
            "gradient_finite": bool(torch.isfinite(gradient).all()),
            "gradient": gradient.cpu().tolist() if torch.isfinite(gradient).all() else None}


def component_checks(configs, device):
    from mmdet.models import build_loss
    results = []
    for name, config in configs.items():
        loss = build_loss(config)
        known = [[0., 0.], [1., -2.]]
        unavailable = [[0., 0.], [float("nan"), float("nan")]]
        weights = [[1., 1.], [1., 1.]]
        original = evaluate(loss, known, weights, False, device)
        corrected = evaluate(loss, known, weights, True, device)
        require(original == corrected, "fully observed loss or gradient changed")
        masked = evaluate(loss, unavailable, weights, True, device)
        require(masked["loss_state"] == "finite" and masked["gradient_finite"], "masked loss invalid")
        require(masked["gradient"][1] == [0., 0.], "unknown velocity receives gradient")
        require(masked["gradient"][0] == original["gradient"][0] and any(masked["gradient"][0]), "observed zero velocity was masked")
        all_missing = evaluate(loss, [[float("nan")] * 2] * 2, weights, True, device)
        require(all_missing["loss"] == 0. and all_missing["gradient"] == [[0., 0.], [0., 0.]], "all-unavailable contribution")
        results.append({"architecture": name, "device": device, "loss_config": dict(config),
                        "all_observed": original, "masked_unavailable": masked,
                        "upstream_with_nan_and_zero_weight": evaluate(loss, unavailable, [[1., 1.], [0., 0.]], False, device),
                        "upstream_after_zero_imputation": evaluate(loss, [[0., 0.], [0., 0.]], weights, False, device),
                        "all_unavailable_contribution": all_missing,
                        "all_unavailable_estimated_velocity_error": None})
    return results


def predictions(head, shapes, device, camera=False):
    def tensor(channels, shape):
        value = torch.zeros((1, channels, *shape), device=device, requires_grad=True) + 0.
        value.retain_grad()
        return value
    if camera:
        return [[tensor(channels, shape) for shape in shapes]
                for channels in (head.num_classes, 9, 2, head.num_attrs, 1)]
    return [[{key: tensor(channels, shapes[0]) for key, channels in
              (("heatmap", count), ("reg", 2), ("height", 1), ("dim", 3), ("rot", 2), ("vel", 2))}]
            for count in head.num_classes]


def head_check(config, device, camera):
    from mmdet3d.models import build_head
    from mmdet3d.core.bbox import CameraInstance3DBoxes, LiDARInstance3DBoxes
    config = copy.deepcopy(config)
    head = build_head(config).to(device)
    original = head.loss_bbox
    if camera:
        shapes = [(4, 4), (2, 2), (1, 1), (1, 1), (1, 1)]
    else:
        grid = head.train_cfg.grid_size
        stride = head.train_cfg.out_size_factor
        shapes = [(grid[1] // stride, grid[0] // stride)]
    outcomes = []
    for missing, safe in ((False, False), (False, True), (True, False), (True, True)):
        head.loss_bbox = ObservedRegressionLoss(original) if safe else original
        pred = predictions(head, shapes, device, camera)
        velocity = [float("nan")] * 2 if missing else [1., 2.]
        if camera:
            box = CameraInstance3DBoxes([[0., 0., 10., 4., 2., 1., 0., *velocity]], box_dim=9, origin=(.5, .5, .5)).to(device)
            losses = head.loss(*pred, [torch.tensor([[0., 0., 32., 32.]], device=device)],
                               [torch.tensor([0], device=device)], [box], [torch.tensor([0], device=device)],
                               [torch.tensor([[16., 16.]], device=device)], [torch.tensor([10.], device=device)],
                               [torch.tensor([6], device=device)], [dict(cam2img=np.eye(3))])
            value = sum(losses[k] for k in ("loss_offset", "loss_depth", "loss_size", "loss_rotsin", "loss_velo"))
            leaves = pred[1]
            velocity_leaves = leaves
        else:
            box = LiDARInstance3DBoxes([[0., 0., 0., 4., 2., 1., 0., *velocity]], box_dim=9, origin=(.5, .5, .5)).to(device)
            losses = head.loss([box], [torch.tensor([0], device=device)], pred)
            value = sum(v for k, v in losses.items() if k.endswith("loss_bbox"))
            leaves = [row[0][key] for row in pred for key in ("reg", "height", "dim", "rot", "vel")]
            velocity_leaves = [row[0]["vel"] for row in pred]
        value.backward()
        gradients = [leaf.grad for leaf in leaves if leaf.grad is not None]
        selected = [leaf.grad[:, 7:9] if camera else leaf.grad for leaf in velocity_leaves if leaf.grad is not None]
        geometry = [g[:, :7] for g in gradients] if camera else [row[0][key].grad for row in pred for key in ("reg", "height", "dim", "rot")]
        finite = all(bool(torch.isfinite(g).all()) for g in gradients)
        row = {"unknown_velocity": missing, "masked_loss": safe,
               "regression_loss_state": "finite" if torch.isfinite(value) else "nonfinite",
               "regression_loss": float(value.detach()) if torch.isfinite(value) else None,
               "gradient_finite": finite,
               "full_gradient_sha256": hashlib.sha256(b"".join(g.cpu().numpy().tobytes() for g in gradients)).hexdigest() if finite else None,
               "geometry_gradient_sha256": hashlib.sha256(b"".join(g.cpu().numpy().tobytes() for g in geometry if g is not None)).hexdigest(),
               "velocity_gradient_l1": float(sum(g.abs().sum() for g in selected)) if finite else None}
        if safe:
            require(row["regression_loss_state"] == "finite" and finite, "actual head masked loss invalid")
            require(all(torch.isfinite(v).all() for v in losses.values()), "actual head has a nonfinite loss component")
            require((row["velocity_gradient_l1"] == 0.) if missing else (row["velocity_gradient_l1"] > 0.), "actual head velocity gradient")
        outcomes.append(row)
    require(outcomes[0]["regression_loss"] == outcomes[1]["regression_loss"] and outcomes[0]["velocity_gradient_l1"] == outcomes[1]["velocity_gradient_l1"], "observed head loss changed")
    require(outcomes[0]["full_gradient_sha256"] == outcomes[1]["full_gradient_sha256"], "observed head gradients changed")
    require(outcomes[0]["geometry_gradient_sha256"] == outcomes[3]["geometry_gradient_sha256"], "masking unavailable velocity changed geometry gradients")
    return {"architecture": "FCOS3D" if camera else "CenterPoint", "device": device, "cases": outcomes}


def main():
    import mmcv
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(exist_ok=False)
    torch.manual_seed(20260908)
    root = Path("/mmdetection3d")
    camera = mmcv.Config.fromfile(str(root / "configs/fcos3d/fcos3d_r101_caffe_fpn_gn-head_dcn_2x8_1x_nus-mono3d_finetune.py"))
    lidar = mmcv.Config.fromfile(str(root / "configs/centerpoint/centerpoint_0075voxel_second_secfpn_circlenms_4x8_cyclic_20e_nus.py"))
    modules = {}
    for name in ("mmdet3d.models.dense_heads.centerpoint_head", "mmdet3d.models.dense_heads.fcos_mono3d_head", "mmdet.models.losses.smooth_l1_loss", "mmdet.models.losses.utils"):
        module = importlib.import_module(name)
        path = Path(inspect.getfile(module))
        retained = args.output / (name.replace(".", "__") + ".py")
        retained.write_bytes(path.read_bytes())
        modules[name] = {"sha256": sha(path), "retained_file": retained.name, "path": str(path)}
    components, heads = [], []
    for device in ("cpu", "cuda"):
        require(device == "cpu" or torch.cuda.is_available(), "CUDA runtime unavailable")
        configs = {"CenterPoint": lidar.model.pts_bbox_head.loss_bbox, "FCOS3D": camera.model.bbox_head.loss_bbox}
        components.extend(component_checks(configs, device))
        lconfig = copy.deepcopy(lidar.model.pts_bbox_head)
        lconfig.update(train_cfg=lidar.model.train_cfg.pts, test_cfg=lidar.model.test_cfg.pts)
        cconfig = copy.deepcopy(camera.model.bbox_head)
        cconfig.update(train_cfg=camera.model.train_cfg, test_cfg=camera.model.test_cfg)
        heads.extend([head_check(lconfig, device, False), head_check(cconfig, device, True)])
    rejected = []
    for name, values in (("partial_unknown", [[np.nan, 0.]]), ("infinite_velocity", [[np.inf, 0.]]), ("wrong_width", [[1.]])):
        try:
            velocity_available(values)
        except ValueError as error:
            rejected.append({"case": name, "reason": str(error)})
        else:
            raise ValueError("invalid velocity accepted")
    require(velocity_available([[0., 0.], [np.nan, np.nan]]).tolist() == [True, False], "observed zero and unavailable velocity collapsed")
    from mmdet.models import build_loss
    guarded = ObservedRegressionLoss(build_loss(lidar.model.pts_bbox_head.loss_bbox))
    for name, prediction, target, weight, reason in (
        ("nan_prediction_at_unknown_target", [np.nan, 0.], [np.nan, np.nan], [0., 0.], "nonfinite regression prediction"),
        ("infinite_prediction", [np.inf, 0.], [0., 0.], [1., 1.], "nonfinite regression prediction"),
        ("infinite_target", [0., 0.], [np.inf, 0.], [1., 1.], "infinite regression target"),
        ("nan_weight", [0., 0.], [0., 0.], [np.nan, 1.], "invalid regression weight"),
        ("negative_weight", [0., 0.], [0., 0.], [-1., 1.], "invalid regression weight"),
        ("shape_mismatch", [0.], [0., 0.], [1., 1.], "regression prediction and target shapes differ"),
    ):
        try:
            guarded(torch.tensor(prediction), torch.tensor(target), torch.tensor(weight), avg_factor=1.)
        except ValueError as error:
            require(str(error) == reason, "wrong regression rejection reason")
            rejected.append({"case": name, "reason": str(error)})
        else:
            raise ValueError("invalid regression case accepted")
    result = {"artifact_id": "reiyah.observed-velocity-probe.0.1.1", "version": "0.1.1", "lifecycle_status": "exploratory",
              "producer_sha256": sha(__file__), "adapter_sha256": sha(Path(__file__).with_name("observed_velocity.py")),
              "modules": modules, "component_checks": components, "head_checks": heads, "rejected": rejected,
              "detector_fits": 0, "sensor_inference": "not_run", "limit": "Synthetic tensors exercise actual losses and target generation; no detector accuracy or full training readiness"}
    (args.output / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
