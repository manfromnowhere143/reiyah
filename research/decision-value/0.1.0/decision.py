"""Frozen nominal decision experiment. Third-party bytes must be supplied privately."""

import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
import time

from contract import (
    COUNTS,
    FRAME,
    MODES,
    QUESTION_SHA256,
    SEQUENCES,
    SCOPE,
    Refusal,
    bind_sources,
    check_frame,
    read_case,
    require,
    vendor_modules,
)


def verdict(delta):
    return "supported" if delta < 0 else "contradicted" if delta > 0 else "null"


def exact_mse(matches):
    return sum(
        (Fraction(x) - Fraction(y)) ** 2
        for row in matches
        for x, y in zip(row["position"], row["q"])
    ) / len(matches)


def native_matches(gt, rows, origin, coords):
    result = []
    for visit, g in enumerate(gt):
        index = min(range(len(rows)), key=lambda j: (abs(rows[j][0] - g["t"]), j))
        dt = abs(rows[index][0] - g["t"])
        if dt > 2.0:
            continue
        point = coords.convert_extracted_points_to_utm(
            [{"position": rows[index][1:4].copy()}], origin
        )[0]["position"]
        result.append(
            {
                "visit": visit,
                "id": g["id"],
                "source_row": index,
                "dt": dt,
                "position": [float(x) for x in point],
                "q": g["q"],
            }
        )
    return result


def conventional_matches(root, seq, mode, gt, poses, origin, modules):
    # Uses the original publisher parser, selector, converter and associations.
    _, readers, _, evaluator = modules
    import numpy as np

    gt_path = root / "ground_truth" / (seq + ".csv")
    native_gt = readers.read_ground_truth(str(gt_path))
    require(
        [p["id"] for p in native_gt] == [g["id"] for g in gt],
        "publisher_checkpoint_identity",
    )
    ts_rows = [{"point_id": p["id"], "timestamp": p["timestamp"]} for p in native_gt]
    path = root / "trajectories/fast_lio_sam" / seq / ("traj_" + mode + ".txt")
    assocs = (
        evaluator.evaluate_trajectory(
            str(path), ts_rows, {g["id"]: g for g in native_gt}, origin
        )
        or []
    )
    ts, positions = readers.read_tum_trajectory(str(path))
    require(ts.tolist() == [r[0] for r in poses], "publisher_timestamp_parse")
    require(positions.tolist() == [r[1:4] for r in poses], "publisher_position_parse")
    by_id = {g["id"]: (i, g) for i, g in enumerate(gt)}
    result = []
    for assoc in assocs:
        visit, g = by_id[assoc["gt_idx"]]
        index = int(np.argmin(np.abs(ts - g["t"])))
        result.append(
            {
                "visit": visit,
                "id": g["id"],
                "source_row": index,
                "dt": abs(float(ts[index]) - g["t"]),
                "position": [float(x) for x in assoc["extracted_point"]["position"]],
                "q": [float(x) for x in assoc["gt_point"]["position"]],
            }
        )
    return result, assocs


def case(root, seq, count, arm, modules):
    gt, poses, origin = read_case(root, seq, count)
    traces, modes = {}, {}
    for mode in MODES:
        if arm == "reiyah":
            matches = native_matches(gt, poses[mode], origin, modules[0])
            mse = float(exact_mse(matches)) if matches else None
            rmse = math.sqrt(mse) if mse is not None else None
        else:
            matches, assocs = conventional_matches(
                root, seq, mode, gt, poses[mode], origin, modules
            )
            rmse = modules[2].absolute_errors(assocs)["rmse_3d"] if assocs else None
            mse = rmse * rmse if rmse is not None else None
        require(
            [m["visit"] for m in matches] == sorted({m["visit"] for m in matches}),
            "association_identity",
        )
        traces[mode] = matches
        modes[mode] = {
            "matched": len(matches),
            "missing_ids": [
                g["id"] for g in gt if g["id"] not in {m["id"] for m in matches}
            ],
            "max_dt_seconds": max((m["dt"] for m in matches), default=None),
            "available_cohort_mse": mse,
            "available_cohort_rmse": rmse,
        }
    complete = all(m["matched"] == count for m in modes.values())
    delta = None
    ratio = None
    if complete:
        if arm == "reiyah":
            exact = exact_mse(traces["offline"]) - exact_mse(traces["online"])
            delta = float(exact)
            ratio = [str(exact.numerator), str(exact.denominator)]
            status = verdict(exact)
        else:
            delta = (
                modes["offline"]["available_cohort_mse"]
                - modes["online"]["available_cohort_mse"]
            )
            status = verdict(delta)
    else:
        status = "blocked"
    return {
        "sequence": seq,
        "expected_visits": count,
        "status": status,
        "modes": modes,
        "delta_m2": delta,
        "exact_delta_ratio": ratio,
    }, traces


def run(root, arm):
    started = time.perf_counter()
    revision = bind_sources(root)
    check_frame(FRAME)
    modules = vendor_modules(root)
    cases, traces = [], {}
    for seq, count in zip(SEQUENCES, COUNTS):
        try:
            result, trace = case(root, seq, count, arm, modules)
        except (Refusal, OSError, ValueError) as exc:
            result = {
                "sequence": seq,
                "expected_visits": count,
                "status": "invalid",
                "reason": str(exc),
                "delta_m2": None,
            }
            trace = {}
        cases.append(result)
        traces[seq] = trace
    record = {
        "document_id": "reiyah.decision-value.result",
        "version": "0.1.0",
        "arm": arm,
        "question_sha256": QUESTION_SHA256,
        "source_revision": revision,
        "scope": SCOPE,
        "frame": FRAME,
        "physical_claim": "unresolved",
        "cases": cases,
        "workflow_seconds": time.perf_counter() - started,
    }
    return record, traces


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("arm", choices=("reiyah", "conventional"))
    parser.add_argument("vendor", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    record, trace = run(args.vendor, args.arm)
    args.output.mkdir(exist_ok=False)
    for name, value in (("result.json", record), ("trace.json", trace)):
        (args.output / name).write_text(
            json.dumps(value, indent=2, allow_nan=False) + "\n"
        )
    print(json.dumps(record, allow_nan=False))


if __name__ == "__main__":
    main()
