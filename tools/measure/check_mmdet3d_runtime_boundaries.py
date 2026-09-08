#!/usr/bin/env python3
"""Known-bad image fixtures and unknown-velocity check in the pinned runtime."""
import argparse
from pathlib import Path

from audit_mmdet3d_inputs import (camera_inverse_preserving_velocity, decode_image,
                                isolated_camera_export, sha, write_json)


def main():
    import cv2
    import numpy as np
    import torch
    from mmdet3d.core.bbox import CameraInstance3DBoxes
    from mmdet3d.datasets.nuscenes_mono_dataset import output_to_nusc_box, nusc_box_to_cam_box3d
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(exist_ok=False)
    success, encoded = cv2.imencode(".jpg", np.full((3, 4, 3), 80, dtype=np.uint8))
    if not success:
        raise ValueError("synthetic JPEG creation failed")
    good = args.output / "known-good.jpg"
    good.write_bytes(encoded.tobytes())
    decoded, _ = decode_image(good, 3, 4)
    if decoded.shape != (3, 4, 3):
        raise ValueError("known-good image did not decode")
    results = []
    for name, payload, dimensions, expected in (
        ("truncated-jpeg", encoded.tobytes()[:-1], (3, 4), "incomplete JPEG envelope"),
        ("invalid-jpeg-body", b"\xff\xd8invalid\xff\xd9", (3, 4), "decoded camera shape or type differs"),
        ("wrong-camera-dimensions", encoded.tobytes(), (4, 3), "decoded camera shape or type differs"),
    ):
        path = args.output / (name + ".jpg")
        path.write_bytes(payload)
        try:
            decode_image(path, *dimensions)
        except ValueError as error:
            if str(error) != expected:
                raise
        else:
            raise ValueError("known-bad image accepted: " + name)
        results.append({"fixture": name, "state": "rejected", "reason": expected})
    prediction = {"boxes_3d": CameraInstance3DBoxes([[0., 0., 10., 4., 2., 1., .2, np.nan, np.nan]],
                                                  box_dim=9, origin=(.5, .5, .5)),
                  "scores_3d": torch.tensor([.9]), "labels_3d": torch.tensor([0]),
                  "attrs_3d": torch.tensor([6])}
    boxes, _ = isolated_camera_export(prediction, output_to_nusc_box)
    restored, _, _ = camera_inverse_preserving_velocity(boxes, nusc_box_to_cam_box3d)
    if not torch.isnan(restored.tensor[:, 7:9]).all() or not torch.isnan(prediction["boxes_3d"].tensor[:, 7:9]).all():
        raise ValueError("unavailable velocity was altered")
    write_json(args.output / "result.json", {"version": "0.1.0", "producer_sha256": sha(__file__),
                                           "known_good_image": "passed", "known_bad_images": results,
                                           "inverse_unavailable_velocity": "preserved_as_unavailable",
                                           "detector_inference": "not_run"})


if __name__ == "__main__":
    main()
