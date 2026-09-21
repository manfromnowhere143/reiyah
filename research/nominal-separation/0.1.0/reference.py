"""Separate clock parsing and segment-pair conventional geometry calculation."""

import argparse
import csv
from datetime import date
from fractions import Fraction
import math
from pathlib import Path
import re
import resource
import time

from custody import bind, canonical_digest, mat_rows, read_json, require, write_new


def calendar(text, target=False):
    pattern = (
        r"(\d{2})-(\d{2})-(\d{4}) (\d{2}):(\d{2}):(\d{2})\.(\d{1,9})"
        if target
        else r"(\d{4})/(\d{2})/(\d{2})/(\d{2}):(\d{2}):(\d{2})\.(\d{1,9})"
    )
    match = re.fullmatch(pattern, text)
    require(match is not None, "reference_calendar")
    a, b, c, h, m, s, frac = match.groups()
    year, month, day = (int(c), int(b), int(a)) if target else (int(a), int(b), int(c))
    require(int(h) < 24 and int(m) < 60 and int(s) < 60, "reference_clock_range")
    value = Fraction(
        (date(year, month, day).toordinal() - date(1970, 1, 1).toordinal()) * 86400
        + int(h) * 3600
        + int(m) * 60
        + int(s)
    ) + Fraction(int(frac), 10 ** len(frac))
    return nanoseconds(value)


def nanoseconds(value):
    ns = value * 1_000_000_000
    require(ns.denominator == 1, "reference_precision")
    return ns.numerator


def position(lat, lon):
    require(
        all(
            type(x) in (int, float)
            and math.isfinite(x)
            and (type(x) is not int or abs(x) <= 2**53)
            for x in (lat, lon)
        ),
        "reference_coordinate",
    )
    require(abs(lat) <= 90 and abs(lon) <= 180, "reference_coordinate_range")
    # The operation order is part of the declared nominal binary64 model.
    vertical_angle = math.radians(lat)
    horizontal_angle = math.radians(lon)
    horizontal_radius = 6371008.8 * math.cos(vertical_angle)
    xyz = (
        horizontal_radius * math.cos(horizontal_angle),
        horizontal_radius * math.sin(horizontal_angle),
        6371008.8 * math.sin(vertical_angle),
    )
    # A second parameterization checks gross compilation mistakes, not sensor error.
    colatitude = math.radians(90 - lat)
    alternative = (
        6371008.8 * math.sin(colatitude) * math.cos(horizontal_angle),
        6371008.8 * math.sin(colatitude) * math.sin(horizontal_angle),
        6371008.8 * math.cos(colatitude),
    )
    require(
        max(abs(x - y) for x, y in zip(xyz, alternative)) < 1e-6,
        "projection_crosscheck",
    )
    return tuple(Fraction(x) for x in xyz)


def validate(model):
    require(len(model) > 1, "reference_minimum")
    require(
        all(
            type(t) is int and len(x) == 3 and all(type(v) is Fraction for v in x)
            for t, x in model
        ),
        "reference_model",
    )
    for i in range(1, len(model)):
        require(model[i - 1][0] < model[i][0], "reference_order")


def read_inputs(root, f, clock):
    with (root / "Test_Scenario_3_Separability_Ego_GPS_ROS.csv").open(
        newline=""
    ) as stream:
        rows = list(csv.reader(stream))
    require(
        rows[0] == f["ego_header"] and all(len(r) == len(rows[0]) for r in rows),
        "reference_ego_shape",
    )
    cols = {v: i for i, v in enumerate(rows[0])}
    ego, ros = [], []
    origin = (date(1980, 1, 6).toordinal() - date(1970, 1, 1).toordinal()) * 86400
    for r in rows[1:]:
        week, second = (
            r[cols[".gps_time.week_number"]],
            Fraction(r[cols[".gps_time.week_seconds"]]),
        )
        require(
            re.fullmatch(r"[0-9]+", week) is not None and 0 <= second < 604800,
            "reference_gps",
        )
        t = nanoseconds(origin + int(week) * 604800 + second)
        ego.append(
            (t, position(float(r[cols[".latitude"]]), float(r[cols[".longitude"]])))
        )
        ros.append(calendar(r[cols["time"]]))
    cells = mat_rows(root / "Test_Scenario_3_Separability_Target_BME_Honda.mat")
    require(cells[0] == f["target_header"], "reference_target_header")
    target = [(calendar(r[0], True), position(r[1], r[2])) for r in cells[1:]]
    validate(ego)
    validate(target)
    require(
        len(ego) == f["ego_rows"] and len(target) == f["target_rows"],
        "reference_allocation",
    )
    require(
        all(ros[i] < ros[i + 1] for i in range(len(ros) - 1)), "reference_ros_order"
    )
    cursor, records = 0, []
    for k, (t, _) in enumerate(target):
        if t < ego[0][0] or t > ego[-1][0]:
            continue
        while cursor + 1 < len(ego) and ego[cursor + 1][0] <= t:
            cursor += 1
        j = min(cursor + 1, len(ego) - 1)
        records.append(
            dict(
                target_row=k,
                ego_left=cursor,
                ego_right=j,
                lower_ns=ros[cursor] - t,
                upper_ns=ros[j] - t,
                upper_closed=cursor == j,
            )
        )
    require(
        records == read_json(clock / "trace-02.json")["constraints"],
        "reference_clock_binding",
    )
    return ego, target, len(records)


def bounds(value):
    require(value >= 0, "reference_negative_square")
    numerator, denominator = value.numerator * 10**24, value.denominator
    lower = math.isqrt(numerator // denominator)
    upper = lower + (lower * lower * denominator != numerator)
    require(
        lower**2 * denominator <= numerator <= upper**2 * denominator,
        "root_certificate",
    )
    require(upper - lower <= 1, "root_width")
    return [lower, upper]


def squared(vector):
    return sum(v**2 for v in vector)


def analyze(ego, target):
    validate(ego)
    validate(target)
    low, high = max(ego[0][0], target[0][0]), min(ego[-1][0], target[-1][0])
    require(low < high, "reference_no_common_support")
    i = j = 0
    segments = []
    while i < len(ego) - 1 and j < len(target) - 1:
        left = max(ego[i][0], target[j][0])
        right = min(ego[i + 1][0], target[j + 1][0])
        if left < right:
            e_velocity = tuple(
                (b - a) / (ego[i + 1][0] - ego[i][0])
                for a, b in zip(ego[i][1], ego[i + 1][1])
            )
            t_velocity = tuple(
                (b - a) / (target[j + 1][0] - target[j][0])
                for a, b in zip(target[j][1], target[j + 1][1])
            )
            velocity = tuple(b - a for a, b in zip(e_velocity, t_velocity))
            relative = tuple(
                target[j][1][k]
                + t_velocity[k] * (left - target[j][0])
                - ego[i][1][k]
                - e_velocity[k] * (left - ego[i][0])
                for k in range(3)
            )
            span = right - left
            derivative_half = sum(x * v for x, v in zip(relative, velocity))
            curvature = squared(velocity)
            offset = (
                Fraction(0)
                if curvature == 0
                else min(Fraction(span), max(Fraction(0), -derivative_half / curvature))
            )
            minimum = squared(tuple(x + offset * v for x, v in zip(relative, velocity)))
            q0 = squared(relative)
            q1 = squared(tuple(x + span * v for x, v in zip(relative, velocity)))
            state = (
                "constant"
                if curvature == 0
                else "nondecreasing"
                if derivative_half >= 0
                else "decreasing"
                if derivative_half + span * curvature <= 0
                else "decrease_then_increase"
            )
            segments.append(
                dict(
                    start_ns=left,
                    end_ns=right,
                    ego_rows=[i, i + 1],
                    target_rows=[j, j + 1],
                    a=list(map(str, relative)),
                    v=[str(v * span) for v in velocity],
                    q_start=str(q0),
                    q_end=str(q1),
                    q_min=str(minimum),
                    minimum_time_ns=str(left + offset),
                    state=state,
                )
            )
        e_end, t_end = ego[i + 1][0], target[j + 1][0]
        if e_end <= t_end:
            i += 1
        if t_end <= e_end:
            j += 1
    # Ordered endpoint records give prefix maxima. Convexity proves no interior maximum is omitted.
    peak_q = Fraction(segments[0]["q_start"])
    peak_t = low
    for segment in segments:
        p, m = bounds(peak_q), bounds(Fraction(segment["q_min"]))
        segment.update(
            prefix_peak_q=str(peak_q),
            prefix_peak_time_ns=peak_t,
            drawdown_pm=[max(0, p[0] - m[1]), max(0, p[1] - m[0])],
        )
        end_q = Fraction(segment["q_end"])
        if end_q > peak_q:
            peak_q, peak_t = end_q, segment["end_ns"]
    counts = dict(constant=0, nondecreasing=0, decreasing=0, decrease_then_increase=0)
    first = None
    for index, row in enumerate(segments):
        counts[row["state"]] += 1
        if first is None and Fraction(row["q_min"]) < Fraction(row["q_start"]):
            first = index
    drops = [row["drawdown_pm"] for row in segments]
    maximum = [max(pair[0] for pair in drops), max(pair[1] for pair in drops)]
    witness = next(i for i, pair in enumerate(drops) if pair[0] == maximum[0])

    def distribution(model):
        before = sum(1 for t, _ in model if t < low)
        after = sum(1 for t, _ in model if t > high)
        return dict(before=before, within=len(model) - before - after, after=after)

    used = {}
    for actor in ("ego", "target"):
        indices = {x for row in segments for x in row[actor + "_rows"]}
        first_index, last_index = min(indices), max(indices)
        require(
            len(indices) == last_index - first_index + 1,
            "reference_noncontiguous_source_use",
        )
        used[actor] = dict(count=len(indices), first=first_index, last=last_index)
    result = dict(
        document_id="reiyah.nominal-separation.result",
        version="0.1.0",
        decision="supported" if first is None else "contradicted",
        scope="Complete declared nominal reconstruction only; physical maneuver and clearance unresolved.",
        support_ns=[low, high],
        interval_count=len(segments),
        interval_states=counts,
        first_counterexample_interval=first,
        logical_interval_reveals=len(segments) if first is None else first + 1,
        total_intervals_evaluated=len(segments),
        maximum_drawdown_pm=maximum,
        minimum_scalar_uniform_repair_pm=[str(Fraction(x, 2)) for x in maximum],
        maximum_drawdown_witness_interval=witness,
        start_separation_pm=bounds(Fraction(segments[0]["q_start"])),
        end_separation_pm=bounds(Fraction(segments[-1]["q_end"])),
        source_rows=dict(ego=len(ego), target=len(target)),
        timestamp_dispositions=dict(ego=distribution(ego), target=distribution(target)),
        used_source_rows=used,
        trace_canonical_sha256=canonical_digest(segments),
    )
    return result, segments


def verify(actual_result, actual_trace, expected_result, expected_trace):
    require(actual_trace == expected_trace, "complete_trace_mismatch")
    require(actual_result == expected_result, "result_mismatch")
    require(
        actual_result["trace_canonical_sha256"] == canonical_digest(actual_trace),
        "trace_digest",
    )


def main():
    parser = argparse.ArgumentParser()
    for name in (
        "numeric",
        "clock",
        "sources",
        "freeze",
        "result",
        "trace",
        "check",
        "baseline",
        "timing",
    ):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    tick, cpu = time.perf_counter(), resource.getrusage(resource.RUSAGE_SELF)
    f = bind(
        Path(__file__).parent,
        Path(args.numeric),
        Path(args.clock),
        Path(args.sources),
        args.freeze,
    )
    ego, target, linked = read_inputs(Path(args.numeric), f, Path(args.clock))
    prepared = time.perf_counter()
    expected, trace = analyze(ego, target)
    calculated = time.perf_counter()
    expected.update(
        freeze_sha256=args.freeze, previous_clock_constraints_verified=linked
    )
    verify(read_json(args.result), read_json(args.trace), expected, trace)
    check = dict(
        document_id="reiyah.nominal-separation.check",
        version="0.1.0",
        status="passed",
        freeze_sha256=args.freeze,
        all_intervals_verified=len(trace),
        previous_clock_constraints_verified=linked,
        complete_trace_sha256=canonical_digest(trace),
        decision=expected["decision"],
        comparison="Exact agreement with separately implemented conventional segment-pair calculation; same author, decoder, mathematical assumptions and supplied records. No independent authorship or advantage established.",
        false_acceptances=[],
        false_refusals=[],
        physical_claim="unresolved",
        physical_cases=0,
    )
    write_new(args.baseline, expected)
    write_new(args.check, check)
    finish = resource.getrusage(resource.RUSAGE_SELF)
    write_new(
        args.timing,
        dict(
            arm="conventional_segment_pairs",
            preparation_seconds=prepared - tick,
            calculation_seconds=calculated - prepared,
            total_through_check_and_output_seconds=time.perf_counter() - tick,
            cpu_seconds=finish.ru_utime + finish.ru_stime - cpu.ru_utime - cpu.ru_stime,
            distinct_source_rows_loaded=len(ego) + len(target),
            note="Includes producer-output checking beyond arm calculation; nested timer, not acquisition/engineering economics.",
        ),
    )
    print(check)


if __name__ == "__main__":
    main()
