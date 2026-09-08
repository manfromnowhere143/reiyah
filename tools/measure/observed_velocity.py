"""Offline research adapters for unavailable velocity and regression targets."""
import numpy as np
import torch

VERSION = "0.1.0"


def velocity_available(values):
    values = np.asarray(values)
    if values.ndim != 2 or values.shape[1] != 2:
        raise ValueError("velocity must have two components per annotation")
    finite = np.isfinite(values).all(axis=1)
    unavailable = np.isnan(values).all(axis=1)
    if not (finite | unavailable).all():
        raise ValueError("partially unavailable or infinite velocity")
    return finite


def lidar_annotation_with_unavailable_velocity(dataset, index):
    """Preserve original paired velocity after the actual dataset's filtering."""
    info = dataset.data_infos[index]
    keep = info["valid_flag"] if dataset.use_valid_flag else info["num_lidar_pts"] > 0
    original = np.asarray(info["gt_velocity"])[keep].copy()
    available = velocity_available(original)
    annotation = dataset.get_ann_info(index)
    boxes = annotation["gt_bboxes_3d"].tensor
    if boxes.shape != (len(original), 9) or not torch.isfinite(boxes[:, :7]).all():
        raise ValueError("lidar annotation shape or geometry differs")
    boxes[:, 7:9] = boxes.new_tensor(original)
    annotation["velocity_available"] = available.copy()
    return annotation


class ObservedRegressionLoss(torch.nn.Module):
    """Mask before arithmetic, retaining the upstream loss and normalization.

    Callers must validate geometry and paired velocity before target generation.
    NaN denotes an unavailable target. Zero placeholders below are computation
    operands with zero weight and zero gradient, never observed motion labels.
    Availability must be re-derived after object sampling and augmentation.
    """

    def __init__(self, original):
        super().__init__()
        self.original = original

    def forward(self, prediction, target, weight=None, **kwargs):
        if prediction.shape != target.shape:
            raise ValueError("regression prediction and target shapes differ")
        if not torch.isfinite(prediction).all():
            raise ValueError("nonfinite regression prediction")
        if torch.isinf(target).any():
            raise ValueError("infinite regression target")
        available = ~torch.isnan(target)
        if weight is None:
            weight = torch.ones_like(target)
        else:
            weight = torch.broadcast_to(weight, target.shape)
        if not torch.isfinite(weight).all() or (weight < 0).any():
            raise ValueError("invalid regression weight")
        zero = torch.zeros_like(target)
        observed_prediction = torch.where(available, prediction, zero)
        observed_target = torch.where(available, target, zero)
        observed_weight = torch.where(available, weight, zero)
        return self.original(observed_prediction, observed_target,
                             weight=observed_weight, **kwargs)
