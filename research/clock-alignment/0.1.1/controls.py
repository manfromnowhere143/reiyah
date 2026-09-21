"""Focused boundary/refusal controls and mutations of the actual retained result."""

import argparse
from copy import deepcopy
from pathlib import Path
import tempfile

import alignment as a
from custody import bind, digest, identity, read_json, require, verify_files, write_new
import reference as r


def refuse(call, reason):
    try:
        call()
    except ValueError as exc:
        require(reason in str(exc), "wrong_refusal: " + str(exc))
    else:
        raise ValueError("unexpected_acceptance: " + reason)


def record(i, lo, hi, closed=False):
    return dict(
        target_row=i,
        ego_left=i,
        ego_right=i + 1,
        lower_ns=lo,
        upper_ns=hi,
        upper_closed=closed,
    )


def pre():
    passed = []
    cases = [
        ("no_covered_records", [], "input_blocked", 0),
        ("single_interval", [record(0, 0, 2)], "supported", 1),
        ("common_shift", [record(0, 0, 5), record(1, 2, 4)], "supported", 2),
        ("disjoint_offsets", [record(0, 0, 2), record(1, 3, 5)], "contradicted", 2),
        ("touching_open_end", [record(0, 0, 2), record(1, 2, 4)], "contradicted", 2),
        (
            "touching_closed_end",
            [record(0, 0, 2, True), record(1, 2, 4)],
            "supported",
            2,
        ),
        (
            "terminal_singleton",
            [record(0, 0, 2), record(1, 1, 1, True)],
            "supported",
            2,
        ),
        (
            "terminal_at_open_end",
            [record(0, 0, 2), record(1, 2, 2, True)],
            "contradicted",
            2,
        ),
        (
            "same_upper_strictness",
            [record(0, 1, 1, True), record(1, 0, 1)],
            "contradicted",
            2,
        ),
        (
            "unseen_rows_cannot_restore",
            [record(0, 0, 1), record(1, 2, 3), record(2, -100, 100)],
            "contradicted",
            2,
        ),
    ]
    for name, records, decision, reveals in cases:
        ours, trace = a.reiyah(records)
        expected, prefix = r.reference_decision(records)
        r.same(ours, expected, name)
        r.same(trace, prefix, name + "_trace")
        r.same(a.conventional(records), expected, name + "_conventional")
        require(
            ours["decision"] == decision and ours["logical_reveals"] == reveals, name
        )
        passed.append(name)
    counts, records = a.allocate([0, 10, 20], [100, 110, 120], [-1, 0, 9, 10, 20, 21])
    require(
        counts
        == dict(before_support=1, after_support=1, bracketed=3, terminal_endpoint=1),
        "allocation_counts",
    )
    require(
        [(x["ego_left"], x["ego_right"]) for x in records]
        == [(0, 1), (0, 1), (1, 2), (2, 2)],
        "tie_right_terminal",
    )
    passed.append("all_support_dispositions_and_ties")
    for name, gps, ros, target, reason in [
        ("duplicate_gps", [0, 0], [1, 2], [0], "ego_gps_order"),
        ("reversed_ros", [0, 1], [2, 1], [0], "ego_ros_order"),
        ("duplicate_target", [0, 1], [1, 2], [0, 0], "target_order"),
        ("unpaired_lengths", [0, 1], [1, 2, 3], [0], "paired_mapping"),
        ("missing_gps", [], [], [0], "ego_gps_order"),
    ]:
        refuse(lambda: a.allocate(gps, ros, target), reason)
        passed.append(name)
    actual = a.calendar_ns("25-06-2020 09:01:10.108000001", True)
    require(
        actual == r.integer_ns(r.calendar("25-06-2020 09:01:10.108000001", True)),
        "nanosecond_epoch",
    )
    require(actual == 1593075670108000001, "known_epoch")
    passed.append("large_epoch_one_nanosecond")
    require(a.gps_ns("0", "0") == 315964800000000000, "gps_epoch")
    require(a.gps_ns("2111", "378089.79") == 1593075689790000000, "known_gps_epoch")
    passed.append("gps_origin_and_week")
    for value, reason in [
        ("NaN", "clock_precision_or_nonfinite"),
        ("0.0000000001", "clock_precision_or_nonfinite"),
        ("", "clock_syntax"),
    ]:
        refuse(lambda: a.decimal_ns(value), reason)
        passed.append("refuse_decimal_" + repr(value))
    refuse(lambda: a.gps_ns("2111", "604800"), "gps_seconds")
    passed.append("gps_week_range")
    refuse(lambda: a.calendar_ns("2020/06/25/09:01:10.0000000001"), "calendar_syntax")
    passed.append("calendar_subnanosecond")
    refuse(lambda: a.calendar_ns(""), "calendar_syntax")
    passed.append("missing_calendar")
    with tempfile.TemporaryDirectory(prefix="alignment-controls-") as tmp:
        root = Path(tmp)
        path = root / "body"
        path.write_bytes(b"bound input")
        expected = identity(path)
        path.write_bytes(b"changed input")
        refuse(lambda: verify_files(root, {"body": expected}), "byte_identity")
        path.unlink()
        path.symlink_to(__file__)
        refuse(
            lambda: verify_files(root, {"body": expected}), "missing_or_symlink_source"
        )
    passed.extend(["changed_source_bytes", "source_symlink"])
    return passed


def post(args, freeze):
    result = read_json(args.result)
    trace = read_json(args.trace)
    inputs = r.reference_inputs(Path(args.retained_sources), freeze)
    trace_sha = digest(args.trace)
    r.verify(result, trace, inputs, args.freeze_sha256, trace_sha)
    passed = []
    for name, change in [
        (
            "decision",
            lambda x: x["reiyah"].update(
                decision="supported"
                if x["reiyah"]["decision"] != "supported"
                else "contradicted"
            ),
        ),
        ("population", lambda x: x.update(target_records=x["target_records"] + 1)),
        ("freeze", lambda x: x.update(freeze_sha256="0" * 64)),
        (
            "acquisition_claim",
            lambda x: x.update(logical_reveals_are_acquisitions=True),
        ),
        ("physical_claim", lambda x: x.update(physical_clearance="supported")),
        (
            "baseline_queries",
            lambda x: x["conventional"].update(
                logical_reveals=x["conventional"]["logical_reveals"] + 1
            ),
        ),
        ("unknown_field", lambda x: x.update(unexpected=True)),
    ]:
        altered = deepcopy(result)
        change(altered)
        refuse(
            lambda: r.verify(altered, trace, inputs, args.freeze_sha256, trace_sha),
            "result_reference_disagreement",
        )
        passed.append(name)
    require(
        bool(trace["constraints"]) and bool(trace["trace"]),
        "post_requires_executed_constraints",
    )
    for name, change in [
        (
            "source_row",
            lambda x: x["constraints"][0].update(
                ego_left=x["constraints"][0]["ego_left"] + 1
            ),
        ),
        (
            "constraint_endpoint",
            lambda x: x["constraints"][0].update(
                lower_ns=x["constraints"][0]["lower_ns"] + 1
            ),
        ),
        ("prefix_witness", lambda x: x["trace"][-1].update(lower_witness=-1)),
        ("missing_constraint", lambda x: x["constraints"].pop()),
    ]:
        altered = deepcopy(trace)
        change(altered)
        refuse(
            lambda: r.verify(result, altered, inputs, args.freeze_sha256, trace_sha),
            "trace_reference_disagreement",
        )
        passed.append(name)
    return passed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["pre", "post"])
    for name in ("retained-sources", "sources", "freeze-sha256", "out"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--result")
    parser.add_argument("--trace")
    args = parser.parse_args()
    freeze = bind(
        Path(__file__).resolve().parent,
        Path(args.retained_sources),
        Path(args.sources),
        args.freeze_sha256,
    )
    passed = pre() if args.mode == "pre" else post(args, freeze)
    out = dict(
        document_id="reiyah.clock-alignment.controls",
        version="0.1.0",
        phase=args.mode,
        status="pass",
        freeze_sha256=args.freeze_sha256,
        count=len(passed),
        controls=passed,
    )
    write_new(args.out, out)
    print(out)


if __name__ == "__main__":
    main()
