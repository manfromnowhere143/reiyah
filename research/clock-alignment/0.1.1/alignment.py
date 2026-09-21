"""Exact source-order clock constraints and complete constant-family decision."""

import argparse
from bisect import bisect_right
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
import time

from custody import bind, digest, mat_rows, require, write_new

NS = 10**9
EGO = "Test_Scenario_3_Separability_Ego_GPS_ROS.csv"
MAT = "Test_Scenario_3_Separability_Target_BME_Honda.mat"


def decimal_ns(text):
    try:
        value = Decimal(text) * NS
        require(
            value.is_finite() and value == value.to_integral_value(),
            "clock_precision_or_nonfinite",
        )
        return int(value)
    except InvalidOperation as exc:
        raise ValueError("clock_syntax") from exc


def calendar_ns(text, target=False):
    form = "%d-%m-%Y %H:%M:%S" if target else "%Y/%m/%d/%H:%M:%S"
    try:
        base, fraction = text.rsplit(".", 1)
        require(fraction.isdigit() and 1 <= len(fraction) <= 9, "calendar_precision")
        value = datetime.strptime(base, form)
        require(value.strftime(form) == base, "calendar_canonical")
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("calendar_syntax") from exc
    delta = value - datetime(1970, 1, 1)
    return (delta.days * 86400 + delta.seconds) * NS + decimal_ns("0." + fraction)


def gps_ns(week, seconds):
    require(week.isdigit(), "gps_week")
    elapsed = decimal_ns(seconds)
    require(0 <= elapsed < 604800 * NS, "gps_seconds")
    return (315964800 + int(week) * 604800) * NS + elapsed


def ordered(values, reason):
    require(bool(values) and all(type(x) is int for x in values), reason)
    require(all(a < b for a, b in zip(values, values[1:])), reason)


def read_sources(root, freeze):
    with (root / EGO).open(newline="") as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames == freeze["ego_header"], "ego_header")
        rows = list(reader)
    require(
        all(
            set(row) == set(reader.fieldnames) and None not in row.values()
            for row in rows
        ),
        "ego_row",
    )
    gps = [
        gps_ns(row[".gps_time.week_number"], row[".gps_time.week_seconds"])
        for row in rows
    ]
    ros = [calendar_ns(row["time"]) for row in rows]
    mat = mat_rows(root / MAT)
    require(mat[0] == freeze["target_header"], "target_header")
    target = [calendar_ns(row[0], True) for row in mat[1:]]
    ordered(gps, "ego_gps_order")
    ordered(ros, "ego_ros_order")
    ordered(target, "target_order")
    require(len(gps) >= 2, "ego_minimum")
    return gps, ros, target


def allocate(gps, ros, target):
    ordered(gps, "ego_gps_order")
    ordered(ros, "ego_ros_order")
    ordered(target, "target_order")
    require(len(gps) == len(ros) and len(gps) >= 2, "paired_mapping")
    counts = dict(before_support=0, after_support=0, bracketed=0, terminal_endpoint=0)
    constraints = []
    for row, t in enumerate(target):
        if t < gps[0]:
            counts["before_support"] += 1
        elif t > gps[-1]:
            counts["after_support"] += 1
        elif t == gps[-1]:
            counts["terminal_endpoint"] += 1
            value = ros[-1] - t
            constraints.append(
                dict(
                    target_row=row,
                    ego_left=len(gps) - 1,
                    ego_right=len(gps) - 1,
                    lower_ns=value,
                    upper_ns=value,
                    upper_closed=True,
                )
            )
        else:
            counts["bracketed"] += 1
            i = bisect_right(gps, t) - 1
            constraints.append(
                dict(
                    target_row=row,
                    ego_left=i,
                    ego_right=i + 1,
                    lower_ns=ros[i] - t,
                    upper_ns=ros[i + 1] - t,
                    upper_closed=False,
                )
            )
    return counts, constraints


def empty(lower, upper, closed):
    return lower > upper or (lower == upper and not closed)


def reiyah(constraints):
    lower = upper = lower_row = upper_row = None
    closed = False
    trace = []
    for k, row in enumerate(constraints, 1):
        if lower is None or row["lower_ns"] > lower:
            lower, lower_row = row["lower_ns"], row["target_row"]
        if (
            upper is None
            or row["upper_ns"] < upper
            or (row["upper_ns"] == upper and closed and not row["upper_closed"])
        ):
            upper, closed, upper_row = (
                row["upper_ns"],
                row["upper_closed"],
                row["target_row"],
            )
        state = (
            "contradicted"
            if empty(lower, upper, closed)
            else "supported"
            if k == len(constraints)
            else "unresolved"
        )
        trace.append(
            dict(
                reveals=k,
                lower_ns=lower,
                upper_ns=upper,
                upper_closed=closed,
                lower_witness=lower_row,
                upper_witness=upper_row,
                decision=state,
            )
        )
        if state == "contradicted":
            break
    if not trace:
        return dict(
            decision="input_blocked",
            logical_reveals=0,
            interval=None,
            witness_rows=[],
            distinct_ego_records_revealed=0,
        ), trace
    last = trace[-1]
    seen = constraints[: len(trace)]
    summary = dict(
        decision=last["decision"],
        logical_reveals=len(trace),
        interval={k: last[k] for k in ("lower_ns", "upper_ns", "upper_closed")},
        witness_rows=sorted({lower_row, upper_row}),
        distinct_ego_records_revealed=len(
            {r[k] for r in seen for k in ("ego_left", "ego_right")}
        ),
    )
    return summary, trace


def conventional(constraints):
    # Independent extremum scan; equal early-stop permission and source order.
    minimum_upper = maximum_lower = None
    upper_included = True
    lo_id = hi_id = None
    source_rows = set()
    for n, item in enumerate(constraints, 1):
        source_rows.update([item["ego_left"], item["ego_right"]])
        if maximum_lower is None or item["lower_ns"] > maximum_lower:
            maximum_lower, lo_id = item["lower_ns"], item["target_row"]
        key = (item["upper_ns"], item["upper_closed"])
        if minimum_upper is None or key < (minimum_upper, upper_included):
            minimum_upper, upper_included = key
            hi_id = item["target_row"]
        if maximum_lower > minimum_upper or (
            maximum_lower == minimum_upper and not upper_included
        ):
            answer = "contradicted"
            break
    else:
        answer = "supported" if constraints else "input_blocked"
        n = len(constraints)
    return dict(
        decision=answer,
        logical_reveals=n,
        interval=None
        if not constraints
        else dict(
            lower_ns=maximum_lower, upper_ns=minimum_upper, upper_closed=upper_included
        ),
        witness_rows=sorted({lo_id, hi_id}) if constraints else [],
        distinct_ego_records_revealed=len(source_rows),
    )


def main():
    parser = argparse.ArgumentParser()
    for name in (
        "retained-sources",
        "sources",
        "freeze-sha256",
        "out",
        "trace",
        "timings",
    ):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    packet = Path(__file__).resolve().parent
    tick, cpu = time.perf_counter(), time.process_time()
    freeze = bind(
        packet, Path(args.retained_sources), Path(args.sources), args.freeze_sha256
    )
    gps, ros, target = read_sources(Path(args.retained_sources), freeze)
    counts, constraints = allocate(gps, ros, target)
    timings = dict(
        shared_binding_decode_allocation=dict(
            wall_seconds=time.perf_counter() - tick,
            cpu_seconds=time.process_time() - cpu,
        )
    )
    tick, cpu = time.perf_counter(), time.process_time()
    ours, trace = reiyah(constraints)
    timings["reiyah"] = dict(
        wall_seconds=time.perf_counter() - tick, cpu_seconds=time.process_time() - cpu
    )
    tick, cpu = time.perf_counter(), time.process_time()
    baseline = conventional(constraints)
    timings["conventional"] = dict(
        wall_seconds=time.perf_counter() - tick, cpu_seconds=time.process_time() - cpu
    )
    write_new(
        args.trace,
        dict(
            document_id="reiyah.clock-alignment.prefix-trace",
            version="0.1.0",
            freeze_sha256=args.freeze_sha256,
            constraints=constraints,
            trace=trace,
        ),
    )
    result = dict(
        document_id="reiyah.clock-alignment.result",
        version="0.1.0",
        status="exploratory",
        freeze_sha256=args.freeze_sha256,
        allocated_decisions=1,
        ego_records=len(gps),
        target_records=len(target),
        dispositions=counts,
        admitted_constraints=len(constraints),
        reiyah=ours,
        conventional=baseline,
        trace_sha256=digest(args.trace),
        physical_clearance="unresolved",
        physical_cases=0,
        logical_reveals_are_acquisitions=False,
        independent_baseline_authorship=False,
        actual_acquisition_saving_established=False,
    )
    write_new(args.out, result)
    write_new(args.timings, timings)
    print(result)


if __name__ == "__main__":
    main()
