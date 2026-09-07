#!/usr/bin/env python3
"""Verify exact latent-world witnesses, clock aggregates and retained execution."""
import argparse
from fractions import Fraction as F
import hashlib
import itertools
import json
from pathlib import Path
import sys


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_world(record):
    world = {tuple(map(int, key)): F(value) for key, value in record["joint_probabilities"].items()}
    require(set(world) == set(itertools.product((0, 1), repeat=4)), "incomplete probability world")
    require(sum(world.values()) == 1 and min(world.values()) >= 0, "invalid probability world")
    observation = {bits: sum(p for (y, a, b, r), p in world.items() if (a, b, r) == bits)
                   for bits in itertools.product((0, 1), repeat=3)}
    order = ((True, True), (True, False), (False, True), (False, False))
    for reference in (False, True):
        cells = [sum(p for (y, a, b, r), p in world.items() if (a != (r if reference else y), b != (r if reference else y)) == errors)
                 for errors in order]
        pa, pb, joint = cells[0] + cells[1], cells[0] + cells[2], cells[0]
        require(pa > 0 and pb > 0, "unexpected undefined coefficient in authored world")
        prefix = "reference_relative" if reference else "true"
        require(record[prefix + "_error_cells"] == [str(v) for v in cells], "wrong reported error cells")
        require(F(record[prefix + "_coefficient"]) == joint / pa / pb, "wrong reported coefficient")
    for value in (0, 1):
        mass = sum(p for (y, _, _, _), p in world.items() if y == value)
        pa = sum(p for (y, a, _, _), p in world.items() if y == value and a != y) / mass
        pb = sum(p for (y, _, b, _), p in world.items() if y == value and b != y) / mass
        joint = sum(p for (y, a, b, _), p in world.items() if y == value and a != y and b != y) / mass
        require(F(record["true_coefficient_given_truth"][str(value)]) == joint / pa / pb, "wrong conditional coefficient")
    error = sum(p for (y, _, _, r), p in world.items() if y != r)
    require(F(record["reference_error_probability"]) == error, "wrong reference error probability")
    return {"".join(map(str, key)): str(value) for key, value in observation.items()}


def sensitivity_table(result):
    rows = ["| Total binary reference-flip budget | Sharp lower coefficient | Sharp upper coefficient |",
            "| --- | ---: | ---: |"]
    for row in result["reference_error_budget_sensitivity"]:
        rows.append(f"| {row['total_reference_error_budget']} | {row['sharp_interval'][0]} | {row['sharp_interval'][1]} |")
    return "\n".join(rows)


def clock_table(report):
    rows = ["| Channel | Keyframe metadata present | Missing | Earliest offset, us | Latest offset, us | Absolute p95, us | Captured after anchor |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for channel, row in sorted(report["result"]["per_channel"].items()):
        cells = [row[k] for k in ("metadata_present", "metadata_missing", "signed_min_us", "signed_max_us",
                                  "absolute_p95_nearest_rank_us", "later_than_anchor_capture_count")]
        rows.append("| " + channel + " | " + " | ".join("unknown" if v is None else f"{v:,}" for v in cells) + " |")
    return "\n".join(rows)


def check_clock(report, private_run):
    for item in report["private_output_closure"]:
        path = private_run / item["path"]
        require(digest(path) == item["sha256"] and path.stat().st_size == item["bytes"], "clock output closure differs")
    rows = [json.loads(line) for line in (private_run / "frame-clock.private.jsonl").read_text().splitlines()]
    scenes = [json.loads(line) for line in (private_run / "scene-clock.private.jsonl").read_text().splitlines()]
    out = report["result"]
    require(len(rows) == len({r["sample_token"] for r in rows}) == out["sample_anchor_count"], "clock frame identity or count differs")
    require(len(scenes) == len({r["scene_token"] for r in scenes}) == out["validation_scene_count"], "clock scene identity or count differs")
    context = 0
    gaps = []
    for scene in scenes:
        frames = sorted((r for r in rows if r["scene_token"] == scene["scene_token"]), key=lambda r: r["anchor_timestamp_us"])
        times = [r["anchor_timestamp_us"] for r in frames]
        eligible = [t - times[0] >= out["clock_context_us_each_side"] and times[-1] - t >= out["clock_context_us_each_side"] for t in times]
        require(len(frames) == scene["frame_count"] and sum(eligible) == scene["context_anchor_count"], "per-scene clock aggregate differs")
        require(all(type(r["has_declared_scene_context"]) is bool and r["has_declared_scene_context"] == keep for r, keep in zip(frames, eligible)), "clock eligibility differs")
        gaps.extend(b - a for a, b in zip(times, times[1:]));context += sum(eligible)
    require(context == out["context_anchor_count"], "context population differs")
    require(out["adjacent_anchor_gap_us"] == {"count": len(gaps), "min": min(gaps), "max": max(gaps)}, "sample clock gaps differ")
    for channel, aggregate in out["per_channel"].items():
        values = []
        for frame in rows:
            row = frame["channels"][channel]
            require(row["payload_validity"] == "not_checked" and row["online_availability_time"] == "unmeasured", "unearned sensor validity or availability")
            if row["metadata_state"] == "present":
                require(row["capture_delta_us"] == row["capture_timestamp_us"] - frame["anchor_timestamp_us"], "wrong capture offset")
                values.append(row["capture_delta_us"])
            else:
                require(row["metadata_state"] == "missing" and row["capture_delta_us"] is None, "missing capture became a number")
        absolute = sorted(map(abs, values))
        expected = {"metadata_present": len(values), "metadata_missing": len(rows) - len(values),
                    "signed_min_us": min(values) if values else None, "signed_max_us": max(values) if values else None,
                    "absolute_p95_nearest_rank_us": absolute[(95 * len(absolute) + 99) // 100 - 1] if absolute else None,
                    "later_than_anchor_capture_count": sum(v > 0 for v in values)}
        require(aggregate == expected, "clock channel aggregate differs")
    complete = sum(all(c["metadata_state"] == "present" for c in r["channels"].values()) for r in rows)
    require(complete == out["anchors_with_all_required_keyframe_metadata"], "complete-channel metadata count differs")
    require(out["physical_joint_error_coefficient"] is None and out["online_availability_times"] == "unmeasured"
            and out["sensor_payload_validity"] == "not_checked" and out["pilot_selection"] == "not_performed", "unearned physical or study conclusion")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--baseline-root", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    evidence = root / "evidence/reference-identification"
    data = json.loads((evidence / "counterexamples-0.1.0.json").read_bytes())
    require(data["source_sha256"] == digest(root / "tools/measure/reference_identification_counterexamples.py"), "counterexample source differs")
    worlds = data["observationally_equivalent_worlds"]
    for world in worlds.values():
        require(check_world(world) == data["complete_observable_probabilities"], "observational equivalence fails")
    require({w["true_coefficient"] for w in worlds.values()} == {"1", "25/9"}, "different true-coefficient witness lost")
    require(data["true_coefficient_point_identified"] is False, "counterexample was promoted to point identification")
    forged = dict(next(iter(worlds.values())))
    forged["true_coefficient"] = "2"
    try:
        check_world(forged)
    except ValueError as exc:
        require(str(exc) == "wrong reported coefficient", "unexpected altered-world rejection reason")
    else:
        raise ValueError("altered coefficient was not rejected")
    for row in data["reference_error_budget_sensitivity"]:
        epsilon = F(row["total_reference_error_budget"])
        a = F(9, 100)
        endpoints = [(a - epsilon) / (2 * a - epsilon)**2, a / (4 * a * a - epsilon * epsilon)]
        require(row["sharp_interval"] == list(map(str, endpoints)), "derived sharp interval differs")
        for name, endpoint in zip(("lower_world", "upper_world"), endpoints):
            world = row[name]
            require(check_world(world) == data["complete_observable_probabilities"] and F(world["true_coefficient"]) == endpoint
                    and F(world["reference_error_probability"]) == epsilon, "extremum probability witness differs")
    pair = data["omitted_opportunity_pair"]
    recorded = list(map(F, pair["same_recorded_cells_in_both_worlds"]))
    added = pair["world_two"]["unrecorded_true_both_errors"]
    require(type(added) is int and added >= 0 and pair["world_one"]["unrecorded_true_both_errors"] == 0,
            "invalid omitted-opportunity count")
    augmented = [recorded[0] + added, *recorded[1:]]
    require(augmented == list(map(F, pair["world_two"]["true_cells"])), "omitted-opportunity cells differ")
    for name, cells in (("world_one", recorded), ("world_two", augmented)):
        a, b, c, d = cells
        require(F(pair[name]["true_coefficient"]) == a * sum(cells) / ((a + b) * (a + c)), "wrong omitted-opportunity coefficient")
    for name, published, tests in (("regression", None, 8), ("counterexamples", "counterexamples-0.1.0.json", None),
                                   ("clock-regression", None, 6), ("clock-audit", "clock-audit-0.1.0.json", None)):
        capture = json.loads((evidence / (name + "-capture-0.1.0.json")).read_bytes())
        require(capture["exit_code"] == 0 and capture["gate_a_release"] is False, "process did not complete successfully in its scope")
        for path, expected in capture["sources"].items():
            require(digest(root / path) == expected, "process source differs")
        for kind, binding in capture["streams"].items():
            path = args.task_root / "checks" / (name + "." + kind)
            require(digest(path) == binding["sha256"] and path.stat().st_size == binding["bytes"], "process stream differs")
        if published:
            require((evidence / published).read_bytes() == (args.task_root / "checks" / (name + ".stdout")).read_bytes(), "published output differs from completed stdout")
        if tests:
            text = (args.task_root / "checks" / (name + ".stderr")).read_text()
            require(f"Ran {tests} tests in " in text and text.endswith("\n\nOK\n"), "successful test summary differs")
    clock = json.loads((evidence / "clock-audit-0.1.0.json").read_bytes())
    run = args.task_root / "private/clock-audit-1"
    require((run / "result.json").read_bytes() == (evidence / "clock-audit-0.1.0.json").read_bytes(), "private clock completion differs")
    require(digest(run / "spec.json") == clock["spec_sha256"] == digest(evidence / "clock-spec-0.1.0.json"), "clock specification differs")
    check_clock(clock, run)
    forged = json.loads(json.dumps(clock))
    forged["result"]["physical_joint_error_coefficient"] = 0
    try:
        check_clock(forged, run)
    except ValueError as exc:
        require(str(exc) == "unearned physical or study conclusion", "unexpected unmeasured-to-zero rejection reason")
    else:
        raise ValueError("unmeasured physical coefficient was allowed to become zero")
    for entry in json.loads((evidence / "source-ledger-0.1.0.json").read_bytes())["entries"]:
        if entry["state"] in ("retained_private", "reused_retained_private"):
            payload = args.task_root / "external-sources" / (entry["source_id"] + ".payload")
            require(digest(payload) == entry["sha256"], "retained primary-source bytes differ")
        else:
            require(entry["state"] == "retrieval_failed" and entry["gate_a_evidence_eligible"] is False, "failed source was admitted")
    text = (root / "docs/REFERENCE_IDENTIFICATION_FINDINGS_2026-09-07.md").read_text()
    require(text.count(sensitivity_table(data)) == 1, "identification table differs")
    clock_text = (root / "docs/OPPORTUNITY_CLOCK_AUDIT_2026-09-07.md").read_text()
    require(clock_text.count(clock_table(clock)) == 1, "clock table differs")
    allowed = {"README.md", "docs/SESSION_HANDOFF.md", "docs/GATE_B_SESSION_HANDOFF.md", "docs/RESEARCH_CONTINUATION_2026-09-07.md"}
    compared, bound = 0, {}
    for before in args.baseline_root.rglob("*"):
        if before.is_file() and "__pycache__" not in before.parts:
            relative = before.relative_to(args.baseline_root)
            if str(relative) not in allowed:
                require((root / relative).is_file() and digest(before) == digest(root / relative), "predecessor changed: " + str(relative))
                compared += 1
    for path in root.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            relative = path.relative_to(root)
            if path.parent == evidence and path.name in ("verification-0.1.0.json", "gate-b-check-0.1.0.json"):
                continue
            if not (args.baseline_root / relative).is_file() or str(relative) in allowed:
                bound[str(relative)] = digest(path)
    print(json.dumps({"artifact_id": "reiyah.reference-identification-verification.0.1.0", "version": "0.1.0", "status": "pass",
                      "mode": "development", "gate_a_release": False, "operator_acceptance": "unaccepted",
                      "scope": ["Exact probability witnesses recomputed without importing their producer", "Clock private-row reaggregation",
                                "Completed process/source closure and numerical tables", "Predecessor byte preservation except four navigation documents"],
                      "unchanged_predecessor_files": compared, "bound_files": bound,
                      "limits": ["No independent human review", "No rereading raw metadata in this verifier", "No physical reference, sampling or safety acceptance"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        print(json.dumps({"status": "invalid", "diagnostic": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
