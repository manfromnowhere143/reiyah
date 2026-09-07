#!/usr/bin/env python3
"""Independent floating-point spatial-index comparison of retained exact audits.

The comparator does not import the auditor or adapter. Shared source bundles
remain a limitation: this tests numerical classifications, not source truth.
"""
import argparse
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import sys

import numpy as np
import scipy
from scipy.spatial import cKDTree


def compare(bundles: Path, reports: Path) -> dict:
    count, frames = 0, 0
    statuses = Counter()
    min_margin = None
    with bundles.open("rb") as source, reports.open("rb") as output:
        for raw, retained in itertools.zip_longest(source, output):
            if raw is None or retained is None:
                raise ValueError("bundle/report cardinality mismatch")
            bundle, report = json.loads(raw), json.loads(retained)
            if hashlib.sha256(raw).hexdigest() != report["input_sha256"]:
                raise ValueError("report input binding mismatch")
            expected = []
            for frame in sorted(bundle["frames"], key=lambda r: r["id"]):
                frames += 1
                predictions = sorted(frame["predictions"], key=lambda r: r["id"])
                if frame["reference_state"] != "available":
                    kinds = ["reference_unknown"] * len(predictions)
                else:
                    selected = set(frame["evaluation_annotation_ids"])
                    positions = np.asarray([[float(v) for v in p["xy_m"]] for p in predictions], dtype=np.float64).reshape(-1, 2)
                    distances = []
                    for keep in (lambda r: r["id"] in selected, lambda r: True):
                        values = [[float(v) for v in r["xy_m"]] for r in frame["annotations"] if keep(r)]
                        ds = cKDTree(values).query(positions)[0] if values else np.full(len(predictions), np.inf)
                        distances.append(ds)
                        finite = ds[np.isfinite(ds)]
                        if len(finite):
                            margin = float(np.min(np.abs(finite - float(bundle["radius_m"]))))
                            min_margin = margin if min_margin is None else min(min_margin, margin)
                    kinds = ["evaluation_reference_near" if a <= float(bundle["radius_m"])
                             else "excluded_reference_near" if b <= float(bundle["radius_m"])
                             else "unmatched_in_supplied_wider_reference" for a, b in zip(*distances)]
                expected += [(frame["id"], p["id"], status) for p, status in zip(predictions, kinds)]
            actual = [(r["frame_id"], r["prediction_id"], r["status"]) for r in report["rows"]]
            if actual != expected:
                raise ValueError("exact and spatial-index classifications disagree")
            if report["physical_false_positive_rate"] is not None or any(r["physical_object_presence"] != "unknown" for r in report["rows"]):
                raise ValueError("unearned physical conclusion")
            count += len(expected)
            statuses.update(status for _, _, status in expected)
    return {"frames": frames, "predictions": count, "classification_disagreements": 0,
            "counts": dict(sorted(statuses.items())), "minimum_floating_point_distance_to_radius_m": min_margin,
            "margin_scope": "Numerical diagnostic on input coordinates, not a physical error bound"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root", type=Path, required=True)
    args = parser.parse_args()
    r = args.private_root
    result = {"artifact_id": "reiyah.reference-audit-numerical-comparison.0.1.0", "version": "0.1.0",
              "lifecycle_status": "exploratory", "comparator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "environment": {"python": sys.version, "numpy": np.__version__, "scipy": scipy.__version__},
              "scope": "Every retained per-prediction classification; source bundle construction is shared",
              "camera": compare(r / "real-replay-1/camera.bundles.jsonl", r / "real-replay-1/camera.reports.jsonl"),
              "lidar": compare(r / "real-replay-1/lidar.bundles.jsonl", r / "real-replay-1/lidar.reports.jsonl"),
              "omitted_frames": compare(r / "frame-coverage-1/bundles.jsonl", r / "frame-coverage-1/reports.jsonl")}
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
