"""Preserve unavailable velocity through the pinned offline annotation parser."""
import copy
import numpy as np
import torch

from observed_velocity import velocity_available

VERSION = "0.1.0"


def checked_box_availability(boxes):
    """Validate geometry before deriving availability from paired velocity."""
    values = boxes.tensor
    if values.ndim != 2 or values.shape[1] != 9:
        raise ValueError("annotation boxes must have nine columns")
    if not torch.isfinite(values[:, :7]).all() or not (values[:, 3:6] > 0).all():
        raise ValueError("invalid annotation geometry")
    return velocity_available(values[:, 7:9].detach().cpu().numpy())


def camera_annotation_with_unavailable_velocity(dataset, image_info, annotations):
    """Use upstream filtering, trace retained rows, then restore source labels.

    On a private copy, attribute integers temporarily carry input row indices
    through the actual parser. Restore the real attributes before returning.
    This avoids implementing a second, potentially divergent selection policy.
    Callers must bind the pinned parser and rederive availability after transforms.
    """
    tagged = copy.deepcopy(annotations)
    for index, row in enumerate(tagged):
        row["attribute_id"] = index
    result = dataset._parse_ann_info(image_info, tagged)
    indices = result["attr_labels"]
    if (indices.ndim != 1 or not np.issubdtype(indices.dtype, np.integer)
            or len(set(indices.tolist())) != len(indices)
            or (indices < 0).any() or (indices >= len(annotations)).any()):
        raise ValueError("camera parser row trace differs")
    selected = [annotations[int(index)] for index in indices]
    original = np.asarray([row["velo_cam3d"] for row in selected], dtype=np.float32).reshape(-1, 2)
    available = velocity_available(original)
    boxes = result["gt_bboxes_3d"].tensor
    if boxes.shape != (len(selected), 9):
        raise ValueError("camera parser annotation count differs")
    boxes[:, 7:9] = boxes.new_tensor(original)
    result["attr_labels"] = np.asarray([row["attribute_id"] for row in selected], dtype=np.int64)
    if not np.array_equal(checked_box_availability(result["gt_bboxes_3d"]), available):
        raise ValueError("camera availability differs after restoration")
    result["velocity_available"] = available.copy()
    result["source_annotation_indices"] = indices.copy()
    return result
