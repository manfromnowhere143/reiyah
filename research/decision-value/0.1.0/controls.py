"""Authored semantic controls and mutations of executed records."""

import argparse
from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path

from contract import FRAME, Refusal, check_frame, check_rows, finite, require, timestamp
from decision import exact_mse, native_matches
from verify import check, pairwise_delta


def refusal(name, reason, action, results):
    try:
        action()
    except Refusal as exc:
        require(str(exc) == reason, "unexpected_refusal:" + name + ":" + str(exc))
        results.append(
            {"id": name, "expected": reason, "actual": str(exc), "passed": True}
        )
    else:
        raise Refusal("accepted_bad_control:" + name)


def authored():
    t = 1760000000.0
    gt = [{"id": "one", "t": t, "q": [0.0, 0.0, 0.0]}]
    poses = {
        mode: [
            [t - 1, 3.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
            [t + 1, 7.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        ]
        for mode in ("online", "offline")
    }
    check_rows(gt, poses, 1)
    results = [{"id": "valid_rows", "passed": True}]
    for name, value, reason in (
        ("nan", float("nan"), "nonfinite"),
        ("infinity", float("inf"), "nonfinite"),
        ("text", "missing", "nonnumeric"),
    ):
        refusal(name, reason, lambda v=value: finite(v), results)
    refusal(
        "millisecond_clock",
        "timestamp_unit_or_epoch",
        lambda: timestamp(t * 1000),
        results,
    )
    refusal(
        "frame_swap",
        "frame_contract",
        lambda: check_frame({**FRAME, "pose": "IMU_center_ENU_m"}),
        results,
    )
    refusal(
        "missing_checkpoint",
        "checkpoint_count",
        lambda: check_rows([], poses, 1),
        results,
    )
    refusal(
        "duplicate_checkpoint",
        "checkpoint_identity",
        lambda: check_rows(gt * 2, poses, 2),
        results,
    )
    bad = deepcopy(poses)
    bad["online"][1][0] = bad["online"][0][0]
    refusal(
        "repeated_timestamp",
        "trajectory_time_order_or_duplicate",
        lambda: check_rows(gt, bad, 1),
        results,
    )
    bad2 = deepcopy(poses)
    bad2["online"][0].pop()
    refusal("short_row", "trajectory_shape", lambda: check_rows(gt, bad2, 1), results)
    refusal(
        "empty_trajectory",
        "empty_trajectory",
        lambda: check_rows(gt, {**poses, "online": []}, 1),
        results,
    )

    class Identity:
        @staticmethod
        def convert_extracted_points_to_utm(points, origin):
            return points

    matches = native_matches(gt, poses["online"], [0, 0, 0], Identity)
    require(len(matches) == 1 and matches[0]["source_row"] == 0, "first_tie")
    results.append({"id": "source_order_tie", "passed": True})
    missing = native_matches(
        [{**gt[0], "t": t + 20}], poses["online"], [0, 0, 0], Identity
    )
    require(missing == [], "missing_pose")
    results.append({"id": "unmatched_pose_retained_missing", "passed": True})
    for name, position, expected in (
        ("smaller", 1.0, -8),
        ("larger", 4.0, 7),
        ("equal", 3.0, 0),
    ):
        other = deepcopy(matches)
        other[0]["position"] = [position, 0.0, 0.0]
        delta = exact_mse(other) - exact_mse(matches)
        require(
            delta == Fraction(expected) == pairwise_delta(matches, other),
            "authored_delta",
        )
        results.append({"id": name, "delta": expected, "passed": True})
    # Exact loss identity at a large common offset, with distinct binary64 operands.
    high_a = [
        {"id": "h", "q": [2.0**40, 0.0, 0.0], "position": [2.0**40 + 0.5, 0.0, 0.0]}
    ]
    high_b = [
        {"id": "h", "q": [2.0**40, 0.0, 0.0], "position": [2.0**40 + 0.25, 0.0, 0.0]}
    ]
    require(
        exact_mse(high_b) - exact_mse(high_a)
        == pairwise_delta(high_a, high_b)
        == Fraction(-3, 16),
        "large_offset",
    )
    results.append({"id": "large_common_offset", "passed": True})
    return results


def mutations(root, folders):
    results = []
    for folder in folders:
        original = json.loads((folder / "result.json").read_text())
        trace = json.loads((folder / "trace.json").read_text())
        check(original, trace, root)
        active = next(
            (i for i, c in enumerate(original["cases"]) if c["status"] != "invalid"),
            None,
        )
        require(active is not None, "no_valid_case_for_mutations")
        complete = next(
            (
                i
                for i, c in enumerate(original["cases"])
                if c["status"] in ("supported", "contradicted", "null")
            ),
            None,
        )
        actions = [
            ("missing_case", "case_cohort", lambda r, t: r["cases"].pop()),
            (
                "physical_claim",
                "claim_scope",
                lambda r, t: r.update(physical_claim="supported"),
            ),
            (
                "frame_swap",
                "frame_contract",
                lambda r, t: r["frame"].update(pose="IMU_center_ENU_m"),
            ),
            (
                "extra_claim",
                "record_fields",
                lambda r, t: r.update(safety_certified=True),
            ),
            (
                "source_binding",
                "result_binding",
                lambda r, t: r.update(source_revision="0" * 40),
            ),
            (
                "checkpoint_count",
                "expected_cohort",
                lambda r, t: r["cases"][active].update(expected_visits=1),
            ),
            (
                "coverage",
                "coverage",
                lambda r, t: r["cases"][active]["modes"]["online"].update(matched=-1),
            ),
            (
                "metric",
                "metric:online_mse",
                lambda r, t: r["cases"][active]["modes"]["online"].update(
                    available_cohort_mse=1e20
                ),
            ),
            (
                "checkpoint_identity",
                "association_trace",
                lambda r, t: t[r["cases"][active]["sequence"]]["online"][0].update(
                    id="different"
                ),
            ),
            (
                "trace_reordering",
                "association_trace",
                lambda r, t: t[r["cases"][active]["sequence"]]["online"].reverse(),
            ),
        ]
        if complete is not None:
            actions += [
                (
                    "decision",
                    "decision_sign",
                    lambda r, t: r["cases"][complete].update(
                        status="contradicted"
                        if r["cases"][complete]["status"] != "contradicted"
                        else "supported"
                    ),
                ),
                (
                    "delta",
                    "metric:delta",
                    lambda r, t: r["cases"][complete].update(delta_m2=12345.0),
                ),
                (
                    "exact_ratio",
                    "exact_ratio",
                    lambda r, t: r["cases"][complete].update(
                        exact_delta_ratio=["123", "1"]
                    ),
                ),
            ]
        else:
            results.append(
                {
                    "arm": original["arm"],
                    "id": "complete_decision_mutations",
                    "status": "unexecuted_no_complete_case",
                }
            )
        for name, reason, mutate in actions:
            record, changed = deepcopy(original), deepcopy(trace)
            mutate(record, changed)
            refusal(
                original["arm"] + ":" + name,
                reason,
                lambda r=record, t=changed: check(r, t, root),
                results,
            )
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("authored", "mutations"))
    parser.add_argument("--vendor", type=Path)
    parser.add_argument("--results", type=Path, nargs="*")
    args = parser.parse_args()
    results = (
        authored() if args.mode == "authored" else mutations(args.vendor, args.results)
    )
    print(json.dumps({"kind": args.mode, "controls": results}, indent=2))


if __name__ == "__main__":
    main()
