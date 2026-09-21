"""Union-knot exact nominal separation analysis; no physical error model."""

import argparse
from bisect import bisect_right
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from fractions import Fraction as F
import math
from pathlib import Path
import resource
import time

from custody import bind, canonical_digest, mat_rows, read_json, require, write_new

NS = 10**9
SCALE = 10**12
RADIUS = 6371008.8
EGO = "Test_Scenario_3_Separability_Ego_GPS_ROS.csv"
MAT = "Test_Scenario_3_Separability_Target_BME_Honda.mat"


def decimal_ns(text):
    try:
        x = Decimal(text) * NS
        require(x.is_finite() and x == x.to_integral_value(), "clock_precision")
        return int(x)
    except InvalidOperation as exc:
        raise ValueError("clock_syntax") from exc


def calendar_ns(text, target=False):
    form = "%d-%m-%Y %H:%M:%S" if target else "%Y/%m/%d/%H:%M:%S"
    base, fraction = text.rsplit(".", 1)
    require(fraction.isdigit() and 1 <= len(fraction) <= 9, "calendar_precision")
    value = datetime.strptime(base, form)
    require(value.strftime(form) == base, "calendar_canonical")
    delta = value - datetime(1970, 1, 1)
    return (delta.days * 86400 + delta.seconds) * NS + decimal_ns("0." + fraction)


def gps_ns(week, seconds):
    require(week.isdigit(), "gps_week")
    value = decimal_ns(seconds)
    require(0 <= value < 604800 * NS, "gps_seconds")
    return (315964800 + int(week) * 604800) * NS + value


def project(latitude, longitude):
    for x in (latitude, longitude):
        require(
            type(x) in (int, float) and math.isfinite(x), "coordinate_type_or_nonfinite"
        )
        require(not isinstance(x, int) or abs(x) <= 2**53, "unsafe_integer")
    require(-90 <= latitude <= 90 and -180 <= longitude <= 180, "coordinate_range")
    phi, lam = math.radians(latitude), math.radians(longitude)
    h = RADIUS * math.cos(phi)
    return tuple(
        F.from_float(x)
        for x in (h * math.cos(lam), h * math.sin(lam), RADIUS * math.sin(phi))
    )


def validate_model(model):
    require(len(model) >= 2, "minimum_records")
    require(
        all(
            type(t) is int and len(x) == 3 and all(type(v) is F for v in x)
            for t, x in model
        ),
        "model_types",
    )
    require(all(a[0] < b[0] for a, b in zip(model, model[1:])), "time_order")


def inputs(root, f, clock):
    with (root / EGO).open(newline="") as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames == f["ego_header"], "ego_header")
        rows = list(reader)
    require(
        all(set(r) == set(reader.fieldnames) and None not in r.values() for r in rows),
        "ego_row",
    )
    ego, ros = [], []
    for row in rows:
        ego.append(
            (
                gps_ns(row[".gps_time.week_number"], row[".gps_time.week_seconds"]),
                project(float(row[".latitude"]), float(row[".longitude"])),
            )
        )
        ros.append(calendar_ns(row["time"]))
    mat = mat_rows(root / MAT)
    require(mat[0] == f["target_header"], "target_header")
    target = [(calendar_ns(r[0], True), project(r[1], r[2])) for r in mat[1:]]
    validate_model(ego)
    validate_model(target)
    require(all(a < b for a, b in zip(ros, ros[1:])), "ros_order")
    require(
        (len(ego), len(target)) == (f["ego_rows"], f["target_rows"]), "row_allocation"
    )
    times = [t for t, _ in ego]
    constraints = []
    for k, (t, _) in enumerate(target):
        if times[0] <= t <= times[-1]:
            i = bisect_right(times, t) - 1
            j = min(i + 1, len(ego) - 1)
            constraints.append(
                dict(
                    target_row=k,
                    ego_left=i,
                    ego_right=j,
                    lower_ns=ros[i] - t,
                    upper_ns=ros[j] - t,
                    upper_closed=i == j,
                )
            )
    require(
        constraints == read_json(clock / "trace-02.json")["constraints"],
        "previous_clock_binding",
    )
    return ego, target, len(constraints)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def interpolate(model, times, t):
    require(times[0] <= t <= times[-1], "extrapolation")
    i = min(bisect_right(times, t) - 1, len(times) - 2)
    a, b = model[i], model[i + 1]
    u = F(t - a[0], b[0] - a[0])
    return tuple(x + u * (y - x) for x, y in zip(a[1], b[1])), i


def root_bounds(q):
    require(q >= 0, "negative_squared_distance")
    numerator = q.numerator * SCALE**2
    k = math.isqrt(numerator // q.denominator)
    return [k, k if k * k * q.denominator == numerator else k + 1]


def analyze(ego, target):
    validate_model(ego)
    validate_model(target)
    start = max(ego[0][0], target[0][0])
    end = min(ego[-1][0], target[-1][0])
    require(start < end, "no_positive_common_support")
    et, tt = [t for t, _ in ego], [t for t, _ in target]
    knots = sorted({start, end} | {t for t in et + tt if start < t < end})
    trace = []
    peak = peak_time = None
    for left, right in zip(knots, knots[1:]):
        e0, ei = interpolate(ego, et, left)
        e1, _ = interpolate(ego, et, right)
        t0, ti = interpolate(target, tt, left)
        t1, _ = interpolate(target, tt, right)
        a = tuple(y - x for x, y in zip(e0, t0))
        z = tuple(y - x for x, y in zip(e1, t1))
        v = tuple(y - x for x, y in zip(a, z))
        aa, bb, cc = dot(v, v), dot(a, v), dot(a, a)
        qend = dot(z, z)
        u = F(0) if aa == 0 else max(F(0), min(F(1), -bb / aa))
        qmin = aa * u * u + 2 * bb * u + cc
        if peak is None:
            peak, peak_time = cc, left
        pbound, mbound = root_bounds(peak), root_bounds(qmin)
        drop = [max(0, pbound[0] - mbound[1]), max(0, pbound[1] - mbound[0])]
        state = (
            "constant"
            if aa == 0
            else "nondecreasing"
            if bb >= 0
            else "decreasing"
            if bb + aa <= 0
            else "decrease_then_increase"
        )
        trace.append(
            dict(
                start_ns=left,
                end_ns=right,
                ego_rows=[ei, ei + 1],
                target_rows=[ti, ti + 1],
                a=list(map(str, a)),
                v=list(map(str, v)),
                q_start=str(cc),
                q_end=str(qend),
                q_min=str(qmin),
                minimum_time_ns=str(F(left) + u * (right - left)),
                state=state,
                prefix_peak_q=str(peak),
                prefix_peak_time_ns=peak_time,
                drawdown_pm=drop,
            )
        )
        if qend > peak:
            peak, peak_time = qend, right
    counts = {
        s: sum(r["state"] == s for r in trace)
        for s in ("constant", "nondecreasing", "decreasing", "decrease_then_increase")
    }
    violations = [
        i
        for i, r in enumerate(trace)
        if r["state"] in ("decreasing", "decrease_then_increase")
    ]
    witness = max(range(len(trace)), key=lambda i: trace[i]["drawdown_pm"][0])
    maximum = [max(r["drawdown_pm"][k] for r in trace) for k in (0, 1)]

    def used_rows(actor):
        rows = sorted({i for r in trace for i in r[actor + "_rows"]})
        require(rows == list(range(rows[0], rows[-1] + 1)), "noncontiguous_source_use")
        return dict(count=len(rows), first=rows[0], last=rows[-1])

    used_ego, used_target = used_rows("ego"), used_rows("target")

    def dispositions(model):
        return dict(
            before=sum(t < start for t, _ in model),
            within=sum(start <= t <= end for t, _ in model),
            after=sum(t > end for t, _ in model),
        )

    result = dict(
        document_id="reiyah.nominal-separation.result",
        version="0.1.0",
        decision="contradicted" if violations else "supported",
        scope="Complete declared nominal reconstruction only; physical maneuver and clearance unresolved.",
        support_ns=[start, end],
        interval_count=len(trace),
        interval_states=counts,
        first_counterexample_interval=violations[0] if violations else None,
        logical_interval_reveals=violations[0] + 1 if violations else len(trace),
        total_intervals_evaluated=len(trace),
        maximum_drawdown_pm=maximum,
        minimum_scalar_uniform_repair_pm=[str(F(x, 2)) for x in maximum],
        maximum_drawdown_witness_interval=witness,
        start_separation_pm=root_bounds(F(trace[0]["q_start"])),
        end_separation_pm=root_bounds(F(trace[-1]["q_end"])),
        source_rows=dict(ego=len(ego), target=len(target)),
        timestamp_dispositions=dict(ego=dispositions(ego), target=dispositions(target)),
        used_source_rows=dict(ego=used_ego, target=used_target),
        trace_canonical_sha256=canonical_digest(trace),
    )
    return result, trace


def main():
    parser = argparse.ArgumentParser()
    for name in ("numeric", "clock", "sources", "freeze", "result", "trace", "timing"):
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
    ego, target, linked = inputs(Path(args.numeric), f, Path(args.clock))
    prepared = time.perf_counter()
    result, trace = analyze(ego, target)
    calculated = time.perf_counter()
    result.update(freeze_sha256=args.freeze, previous_clock_constraints_verified=linked)
    write_new(args.result, result)
    write_new(args.trace, trace)
    finish = resource.getrusage(resource.RUSAGE_SELF)
    write_new(
        args.timing,
        dict(
            arm="union_knots",
            preparation_seconds=prepared - tick,
            calculation_seconds=calculated - prepared,
            total_through_output_seconds=time.perf_counter() - tick,
            cpu_seconds=finish.ru_utime + finish.ru_stime - cpu.ru_utime - cpu.ru_stime,
            distinct_source_rows_loaded=len(ego) + len(target),
            note="Nested process timer; not full acquisition/engineering economics.",
        ),
    )
    print(
        {
            k: result[k]
            for k in (
                "decision",
                "interval_count",
                "interval_states",
                "maximum_drawdown_pm",
                "logical_interval_reveals",
            )
        }
    )


if __name__ == "__main__":
    main()
