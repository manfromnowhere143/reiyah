"""Strict common input contract; no decision arithmetic or physical guarantee."""

import csv
import hashlib
import importlib
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SEQUENCES = (
    "construction_seq1",
    "construction_seq2",
    "stadtgarten_seq1",
    "stadtgarten_seq2",
)
COUNTS = (16, 16, 36, 19)
MODES = ("online", "offline")
SCOPE = "nominal_recorded_reference_completed_map"
QUESTION_SHA256 = "be684b107146c47833b0247c258fa0abb59fc625f3e83b6cb0e6819158b52eb7"
FRAME = {
    "pose": "base_center_ENU_m",
    "reference": "publisher_ETRS89_UTM32N_m",
    "clock": "unix_seconds",
    "transform": "publisher_coords_py_minus_48.22m_ENU_up",
    "physical_bound": "unqualified",
}


class Refusal(ValueError):
    pass


def require(test, reason):
    if not test:
        raise Refusal(reason)


def finite(value):
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise Refusal("nonnumeric") from exc
    require(math.isfinite(result), "nonfinite")
    return result


def timestamp(value):
    result = finite(value)
    # Published recordings are in 2025; this rejects unit/epoch mismatches,
    # not timestamp calibration errors within this documented calendar year.
    require(1735689600 <= result < 1767225600, "timestamp_unit_or_epoch")
    return result


def check_frame(frame):
    require(frame == FRAME, "frame_contract")


def check_rows(gt, poses, count):
    require(len(gt) == count, "checkpoint_count")
    ids = [g["id"] for g in gt]
    require(all(ids) and len(set(ids)) == count, "checkpoint_identity")
    require(all(len(g["q"]) == 3 for g in gt), "checkpoint_shape")
    for row in gt:
        timestamp(row["t"])
        for val in row["q"]:
            finite(val)
    times = [g["t"] for g in gt]
    require(all(a < b for a, b in zip(times, times[1:])), "checkpoint_time_order")
    for mode in MODES:
        rows = poses[mode]
        require(bool(rows), "empty_trajectory")
        for row in rows:
            require(len(row) == 8, "trajectory_shape")
            timestamp(row[0])
            for val in row[1:]:
                finite(val)
        times = [row[0] for row in rows]
        require(
            all(a < b for a, b in zip(times, times[1:])),
            "trajectory_time_order_or_duplicate",
        )


def read_case(root, sequence, count):
    path = root / "ground_truth" / (sequence + ".csv")
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        require(
            reader.fieldnames
            == ["point_id", "easting", "northing", "height", "env", "timestamp"],
            "checkpoint_columns",
        )
        gt = []
        for row in reader:
            require(
                None not in row and all(x is not None for x in row.values()),
                "checkpoint_shape",
            )
            gt.append(
                {
                    "id": row["point_id"],
                    "t": timestamp(row["timestamp"]),
                    "q": [finite(row[k]) for k in ("easting", "northing", "height")],
                }
            )
    directory = root / "trajectories/fast_lio_sam" / sequence
    origin = json.loads((directory / "enu_origin.json").read_text())
    require(isinstance(origin, list) and len(origin) == 3, "origin_shape")
    origin = [finite(x) for x in origin]
    require(-90 <= origin[0] <= 90 and -180 <= origin[1] <= 180, "origin_units")
    poses = {}
    for mode in MODES:
        rows = []
        for line in (directory / ("traj_" + mode + ".txt")).read_text().splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            tokens = line.split()
            require(len(tokens) == 8, "trajectory_shape")
            rows.append([timestamp(tokens[0]), *map(finite, tokens[1:])])
        poses[mode] = rows
    check_rows(gt, poses, count)
    return gt, poses, origin


def bind_sources(root):
    ledger = json.loads((HERE / "sources.json").read_text())
    require(
        hashlib.sha256((HERE / "QUESTION.md").read_bytes()).hexdigest()
        == QUESTION_SHA256,
        "question_identity",
    )
    for row in ledger["files"]:
        path = root / row["path"]
        require(path.is_file(), "source_missing:" + row["path"])
        body = path.read_bytes()
        require(
            len(body) == row["bytes"]
            and hashlib.sha256(body).hexdigest() == row["sha256"],
            "source_identity:" + row["path"],
        )
    return ledger["revision"]


def vendor_modules(root):
    sys.path.insert(0, str((root / "eval").resolve()))
    modules = [
        importlib.import_module(name)
        for name in ("coords", "readers", "metrics", "eval")
    ]
    for module in modules:
        require(
            Path(module.__file__).resolve().parent == (root / "eval").resolve(),
            "vendor_module_path",
        )
    return modules
