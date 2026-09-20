"""Separate arithmetic reference. Shares only custody and MAT container decoding."""

import argparse
import calendar as calendar_module
from collections import Counter
import csv
from datetime import datetime
from fractions import Fraction
import math
from pathlib import Path

from binding import bind, digest, mat_rows, read_json, require, write_new


def numeric(value):
    if value == "":
        return "missing", None
    x = float(value)
    if not math.isfinite(x):
        return (
            "nan"
            if math.isnan(x)
            else "positive_infinity"
            if x > 0
            else "negative_infinity"
        ), None
    return "finite", x


def census(tokens):
    result = dict.fromkeys(
        ["finite", "missing", "nan", "positive_infinity", "negative_infinity"], 0
    )
    for token in tokens:
        result[numeric(token)[0]] += 1
    return result


def time_fraction(value, form):
    d = datetime.strptime(value, form)
    return Fraction(calendar_module.timegm(d.timetuple())) + Fraction(
        d.microsecond, 1000000
    )


def decimal_text(value):
    # All temporal operands have finite decimal expansions, including even medians.
    sign = "-" if value < 0 else ""
    n, d = abs(value.numerator), value.denominator
    whole, rem = divmod(n, d)
    digits = []
    while rem:
        require(len(digits) < 32, "nondecimal_time")
        digit, rem = divmod(rem * 10, d)
        digits.append(str(digit))
    return sign + str(whole) + ("." + "".join(digits) if digits else "")


def time_summary(values):
    ordered = sorted(values)
    n = len(ordered)
    if not n:
        return {"count": 0, "minimum": None, "median": None, "maximum": None}
    mid = ordered[n // 2] if n % 2 else (ordered[n // 2 - 1] + ordered[n // 2]) / 2
    return {
        "count": n,
        "minimum": decimal_text(ordered[0]),
        "median": decimal_text(mid),
        "maximum": decimal_text(ordered[-1]),
    }


def timeline(values):
    delta = [values[i] - values[i - 1] for i in range(1, len(values))]
    return {
        "records": len(values),
        "duplicates": sum(n - 1 for n in Counter(values).values()),
        "non_increasing_steps": len([x for x in delta if x <= 0]),
        "increments_seconds": time_summary(delta),
    }


def chord_distance(lat1, lon1, lat2, lon2):
    def vector(lat, lon):
        phi, theta = lat * math.pi / 180, lon * math.pi / 180
        return (
            math.cos(phi) * math.cos(theta),
            math.cos(phi) * math.sin(theta),
            math.sin(phi),
        )

    chord = math.dist(vector(lat1, lon1), vector(lat2, lon2))
    return 12742017.6 * math.asin(min(1.0, chord / 2))


def summary(values):
    n = len(values)
    return {
        "count": n,
        "maximum": sorted(values)[-1] if n else None,
        "mean": sum(values) / n if n else None,
    }


def compare_result(actual, expected, path=""):
    if isinstance(expected, dict):
        require(
            type(actual) is dict and actual.keys() == expected.keys(),
            "result_keys:" + path,
        )
        return sum(
            compare_result(actual[k], v, path + "/" + k) for k, v in expected.items()
        )
    if isinstance(expected, list):
        require(
            type(actual) is list and len(actual) == len(expected), "result_list:" + path
        )
        return sum(
            compare_result(a, b, path + f"/{i}")
            for i, (a, b) in enumerate(zip(actual, expected))
        )
    if type(expected) is float:
        require(
            type(actual) in (float, int) and math.isfinite(actual),
            "result_number:" + path,
        )
        tolerance = 1e-6 if "spherical_displacement_m" in path else 1e-12
        require(abs(actual - expected) <= tolerance, "result_arithmetic:" + path)
    elif type(expected) is str and (
        "increments_seconds" in path or "clock_differences_seconds" in path
    ):
        require(
            type(actual) is str and Fraction(actual) == Fraction(expected),
            "result_time:" + path,
        )
    else:
        require(
            type(actual) is type(expected) and actual == expected,
            "result_value:" + path,
        )
    return 1


def reference(sources, freeze):
    tables = {}
    for role, spec in freeze["csv_inputs"].items():
        with (sources / spec["file"]).open(newline="") as f:
            data = list(csv.reader(f))
        require(data[0] == spec["header"] and len(data) > 1, "reference_header")
        require(all(len(row) == len(data[0]) for row in data[1:]), "reference_row")
        tables[role] = {
            name: [row[i] for row in data[1:]] for i, name in enumerate(data[0])
        }
    e, t = tables["ego"], tables["target"]
    n, nt = len(e["time"]), len(t["Time"])
    r = [time_fraction(v, "%Y/%m/%d/%H:%M:%S.%f") for v in e["time"]]
    h, g = [], []
    for i in range(n):
        nano = int(e[".header.stamp.nsecs"][i])
        week = int(e[".gps_time.week_number"][i])
        second = Fraction(e[".gps_time.week_seconds"][i])
        require(
            0 <= nano <= 999999999 and week >= 0 and 0 <= second < 604800,
            "reference_clock_range",
        )
        h.append(Fraction(int(e[".header.stamp.secs"][i])) + Fraction(nano, 1000000000))
        g.append(Fraction(315964800) + week * 604800 + second)
    times = [time_fraction(v, "%d-%m-%Y %H:%M:%S.%f") for v in t["Time"]]
    precision = {}
    for key in ("Latitude", "Longitude"):
        result = Counter()
        for token in t[key]:
            if numeric(token)[0] == "finite":
                text = token.lower().split("e")
                exponent = int(text[1]) if len(text) > 1 else 0
                places = len(text[0].split(".")[1]) if "." in text[0] else 0
                result[str(max(0, places - exponent))] += 1
        precision[key] = dict(result)
    m = mat_rows(sources / freeze["mat_input"])
    header = freeze["csv_inputs"]["target"]["header"]
    require(m[0] == header, "reference_mat_columns")
    mismatches = [
        i + 1 for i in range(min(nt, len(m) - 1)) if t["Time"][i] != m[i + 1][0]
    ]
    serial = {
        "csv_records": nt,
        "mat_records": len(m) - 1,
        "timestamp_mismatch_rows": mismatches,
    }
    if nt != len(m) - 1 or mismatches:
        serial.update(
            status="row_identity_failed",
            numeric_columns=None,
            spherical_displacement_m=None,
        )
    else:
        columns = {}
        for col, key in enumerate(header[1:], 1):
            differences = []
            changed = unavailable = mismatch = 0
            for i, token in enumerate(t[key]):
                a, b = numeric(token), numeric(m[i + 1][col])
                mismatch += a[0] != b[0]
                if a[0] == b[0] == "finite":
                    differences.append(abs(a[1] - b[1]))
                    changed += a[1] != b[1]
                else:
                    unavailable += 1
            columns[key] = summary(differences) | {
                "different_binary_values": changed,
                "unavailable_pairs": unavailable,
                "availability_mismatch_pairs": mismatch,
            }
        distances = []
        for i in range(nt):
            vals = [
                numeric(t["Latitude"][i]),
                numeric(t["Longitude"][i]),
                numeric(m[i + 1][1]),
                numeric(m[i + 1][2]),
            ]
            if all(v[0] == "finite" for v in vals):
                lat1, lon1, lat2, lon2 = [v[1] for v in vals]
                require(
                    -90 <= lat1 <= 90
                    and -90 <= lat2 <= 90
                    and -180 <= lon1 <= 180
                    and -180 <= lon2 <= 180,
                    "reference_position_range",
                )
                distances.append(chord_distance(lat1, lon1, lat2, lon2))
        serial.update(
            status="row_identity_agreed",
            numeric_columns=columns,
            spherical_displacement_m=summary(distances),
        )
    return {
        "document_id": "reiyah.compact-motion.result",
        "version": "0.1.0",
        "status": "exploratory",
        "ego_records": n,
        "target_records": nt,
        "ego_numeric_availability": {
            k: census(e[k]) for k in freeze["csv_inputs"]["ego"]["header"][9:]
        },
        "target_numeric_availability": {k: census(t[k]) for k in header[1:]},
        "target_coordinate_decimal_places": precision,
        "ego_status": dict(Counter(e[".status"])),
        "ego_position_type": dict(Counter(e[".pos_type"])),
        "timelines": {
            "ego_calendar_text": timeline(r),
            "ego_header": timeline(h),
            "ego_gps": timeline(g),
            "target_calendar_text": timeline(times),
        },
        "clock_differences_seconds": {
            "calendar_text_minus_header": time_summary([r[i] - h[i] for i in range(n)]),
            "gps_epoch_plus_week_minus_header": time_summary(
                [g[i] - h[i] for i in range(n)]
            ),
        },
        "target_serialization": serial,
        "scope": {
            "physical_cases": 0,
            "physical_clearance": "unresolved",
            "actor_time_join_performed": False,
            "calibrated_error_bound": False,
            "comparative_value_established": False,
            "reserved_images_closed": 1433,
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    freeze = bind(Path(__file__).parent, args.sources, args.freeze)
    expected = reference(args.sources, freeze)
    expected["freeze_sha256"] = args.freeze
    checked = compare_result(read_json(args.result), expected)
    result = {
        "document_id": "reiyah.compact-motion.check",
        "version": "0.1.0",
        "status": "pass",
        "freeze_sha256": args.freeze,
        "result_sha256": digest(args.result),
        "leaves_checked": checked,
        "shared_components": ["byte binding", "SciPy MAT decoder"],
        "distinct_calculations": [
            "CSV traversal",
            "numeric census",
            "clock rational arithmetic",
            "unit-vector chord distances",
        ],
        "independent_replication": False,
    }
    write_new(args.output, result)
    print(result)
