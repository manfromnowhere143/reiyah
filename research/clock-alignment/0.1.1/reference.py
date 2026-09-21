"""Separate rational clock parser, monotone association and all-record verifier."""

import argparse
import csv
from datetime import date
from fractions import Fraction
import json
from pathlib import Path
import re

from custody import bind, digest, mat_rows, read_json, require, write_new

BILLION = 1_000_000_000


def calendar(text, target=False):
    pattern = (
        r"(\d{2})-(\d{2})-(\d{4}) (\d{2}):(\d{2}):(\d{2})\.(\d{1,9})"
        if target
        else r"(\d{4})/(\d{2})/(\d{2})/(\d{2}):(\d{2}):(\d{2})\.(\d{1,9})"
    )
    match = re.fullmatch(pattern, text)
    require(match is not None, "reference_calendar_syntax")
    a, b, c, h, m, s, frac = match.groups()
    y, mo, d = (int(c), int(b), int(a)) if target else (int(a), int(b), int(c))
    require(int(h) < 24 and int(m) < 60 and int(s) < 60, "reference_calendar_range")
    days = date(y, mo, d).toordinal() - date(1970, 1, 1).toordinal()
    return Fraction(days * 86400 + int(h) * 3600 + int(m) * 60 + int(s)) + Fraction(
        int(frac), 10 ** len(frac)
    )


def integer_ns(seconds):
    value = seconds * BILLION
    require(value.denominator == 1, "reference_clock_precision")
    return value.numerator


def reference_inputs(root, freeze):
    with (root / "Test_Scenario_3_Separability_Ego_GPS_ROS.csv").open(
        newline=""
    ) as stream:
        table = list(csv.reader(stream))
    require(table[0] == freeze["ego_header"], "reference_ego_header")
    header = {name: i for i, name in enumerate(table[0])}
    require(all(len(row) == len(table[0]) for row in table), "reference_ego_shape")
    gps, ros = [], []
    for row in table[1:]:
        week = row[header[".gps_time.week_number"]]
        require(re.fullmatch(r"[0-9]+", week) is not None, "reference_week")
        second = Fraction(row[header[".gps_time.week_seconds"]])
        require(0 <= second < 7 * 86400, "reference_week_seconds")
        origin = (date(1980, 1, 6).toordinal() - date(1970, 1, 1).toordinal()) * 86400
        gps.append(Fraction(origin + int(week) * 7 * 86400) + second)
        ros.append(calendar(row[header["time"]]))
    data = mat_rows(root / "Test_Scenario_3_Separability_Target_BME_Honda.mat")
    require(data[0] == freeze["target_header"], "reference_mat_header")
    target = [calendar(row[0], True) for row in data[1:]]
    for values in [gps, ros, target]:
        require(
            values and all(a < b for a, b in zip(values, values[1:])), "reference_order"
        )
        for x in values:
            integer_ns(x)
    require(len(gps) >= 2 and len(gps) == len(ros), "reference_mapping_shape")
    counts = dict(before_support=0, after_support=0, bracketed=0, terminal_endpoint=0)
    records = []
    cursor = 0
    for index, t in enumerate(target):
        if t < gps[0]:
            counts["before_support"] += 1
            continue
        if t > gps[-1]:
            counts["after_support"] += 1
            continue
        while cursor + 1 < len(gps) and gps[cursor + 1] <= t:
            cursor += 1
        endpoint = cursor == len(gps) - 1
        counts["terminal_endpoint" if endpoint else "bracketed"] += 1
        j = cursor if endpoint else cursor + 1
        records.append(
            dict(
                target_row=index,
                ego_left=cursor,
                ego_right=j,
                lower_ns=integer_ns(ros[cursor] - t),
                upper_ns=integer_ns(ros[j] - t),
                upper_closed=endpoint,
            )
        )
    return len(gps), len(target), counts, records


def extrema(records):
    if not records:
        return None
    lo = max(records, key=lambda r: r["lower_ns"])
    hi = min(records, key=lambda r: (r["upper_ns"], r["upper_closed"]))
    low, high = lo["lower_ns"], hi["upper_ns"]
    return dict(
        lower_ns=low,
        upper_ns=high,
        upper_closed=hi["upper_closed"],
        lower_witness=lo["target_row"],
        upper_witness=hi["target_row"],
        empty=low > high or (low == high and not hi["upper_closed"]),
    )


def reference_decision(records):
    # All-prefix extrema, deliberately separate from the incremental scan.
    # Binary search is valid: once infeasible, adding constraints cannot restore it.
    final = extrema(records)
    if final is None:
        return dict(
            decision="input_blocked",
            logical_reveals=0,
            interval=None,
            witness_rows=[],
            distinct_ego_records_revealed=0,
        ), []
    a, b = 1, len(records)
    if final["empty"]:
        while a < b:
            mid = (a + b) // 2
            if extrema(records[:mid])["empty"]:
                b = mid
            else:
                a = mid + 1
        count = a
    else:
        count = len(records)
    trace = []
    # At most 4,437 small prefixes in this frozen population; exact and bounded.
    for n in range(1, count + 1):
        e = extrema(records[:n])
        decision = (
            "contradicted"
            if e.pop("empty")
            else "supported"
            if n == len(records)
            else "unresolved"
        )
        trace.append(dict(reveals=n, **e, decision=decision))
    last = trace[-1]
    prefix = records[:count]
    summary = dict(
        decision=last["decision"],
        logical_reveals=count,
        interval={k: last[k] for k in ["lower_ns", "upper_ns", "upper_closed"]},
        witness_rows=sorted({last["lower_witness"], last["upper_witness"]}),
        distinct_ego_records_revealed=len(
            {r[k] for r in prefix for k in ["ego_left", "ego_right"]}
        ),
    )
    return summary, trace


def same(actual, expected, reason):
    require(
        json.dumps(actual, sort_keys=True, allow_nan=False)
        == json.dumps(expected, sort_keys=True, allow_nan=False),
        reason,
    )


def verify(result, trace, inputs, freeze_sha, trace_sha):
    ego, n, counts, records = inputs
    summary, prefix = reference_decision(records)
    expected = dict(
        document_id="reiyah.clock-alignment.result",
        version="0.1.0",
        status="exploratory",
        freeze_sha256=freeze_sha,
        allocated_decisions=1,
        ego_records=ego,
        target_records=n,
        dispositions=counts,
        admitted_constraints=len(records),
        reiyah=summary,
        conventional=summary,
        trace_sha256=trace_sha,
        physical_clearance="unresolved",
        physical_cases=0,
        logical_reveals_are_acquisitions=False,
        independent_baseline_authorship=False,
        actual_acquisition_saving_established=False,
    )
    same(result, expected, "result_reference_disagreement")
    same(
        trace,
        dict(
            document_id="reiyah.clock-alignment.prefix-trace",
            version="0.1.0",
            freeze_sha256=freeze_sha,
            constraints=records,
            trace=prefix,
        ),
        "trace_reference_disagreement",
    )
    full = extrema(records)
    certificate = []
    if summary["decision"] == "contradicted":
        certificate = [
            row for row in records if row["target_row"] in summary["witness_rows"]
        ]
        require(extrema(certificate)["empty"], "certificate_not_infeasible")
    witness = None
    if full is not None and not full["empty"]:
        witness = Fraction(full["lower_ns"] + full["upper_ns"], 2)
        require(
            all(
                r["lower_ns"] <= witness
                and (
                    witness <= r["upper_ns"]
                    if r["upper_closed"]
                    else witness < r["upper_ns"]
                )
                for r in records
            ),
            "feasible_witness_failed",
        )
    return dict(
        document_id="reiyah.clock-alignment.check",
        version="0.1.0",
        status="pass",
        freeze_sha256=freeze_sha,
        all_constraints_checked=len(records),
        prefixes_checked=len(prefix),
        full_intersection=full,
        early_certificate=certificate,
        feasible_offset_ns=None if witness is None else str(witness),
        decision=summary["decision"],
        logical_reveals=summary["logical_reveals"],
        false_acceptance=0,
        false_refusal=0,
        allocated_decisions=1,
        independent_authorship=False,
        physical_clearance="unresolved",
    )


def main():
    parser = argparse.ArgumentParser()
    for name in (
        "retained-sources",
        "sources",
        "freeze-sha256",
        "result",
        "trace",
        "out",
    ):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    packet = Path(__file__).resolve().parent
    freeze = bind(
        packet, Path(args.retained_sources), Path(args.sources), args.freeze_sha256
    )
    inputs = reference_inputs(Path(args.retained_sources), freeze)
    checked = verify(
        read_json(args.result),
        read_json(args.trace),
        inputs,
        args.freeze_sha256,
        digest(args.trace),
    )
    checked["result_sha256"] = digest(args.result)
    checked["trace_sha256"] = digest(args.trace)
    write_new(args.out, checked)
    print(checked)


if __name__ == "__main__":
    main()
