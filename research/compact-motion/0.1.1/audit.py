"""Full selected-stream serialization and clock diagnostics. No clearance decision."""

import argparse
from collections import Counter
import csv
from datetime import datetime
from decimal import Decimal
import math
from pathlib import Path
import statistics

from binding import bind, mat_rows, require, write_new

EGO = "Test_Scenario_3_Separability_Ego_GPS_ROS.csv"
TARGET = "Test_Scenario_3_Separability_Target_BME_Honda.csv"
MAT = TARGET.removesuffix(".csv") + ".mat"
TARGET_HEADER = ["Time", "Latitude", "Longitude", "LatStdDev", "LongStdDev", "Heading"]
EGO_HEADER = [
    "time",
    ".header.seq",
    ".header.stamp.secs",
    ".header.stamp.nsecs",
    ".header.frame_id",
    ".gps_time.week_number",
    ".gps_time.week_seconds",
    ".status",
    ".pos_type",
    ".latitude",
    ".longitude",
    ".height",
    ".undulation",
    ".north_vel",
    ".east_vel",
    ".up_vel",
    ".roll_deg",
    ".pitch_deg",
    ".azimuth_deg",
    ".std_latitude",
    ".std_longitude",
    ".std_height",
    ".std_north_vel",
    ".std_east_vel",
    ".std_up_vel",
    ".std_roll",
    ".std_pitch",
    ".std_azimuth",
]
RADIUS = 6371008.8


def rows(path, header):
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        require(reader.fieldnames == header, "csv_header")
        result = list(reader)
    require(
        result
        and all(set(r) == set(header) and None not in r.values() for r in result),
        "csv_row_shape",
    )
    return result


def number(value):
    if value == "":
        return "missing", None
    try:
        x = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("numeric_syntax") from exc
    if math.isnan(x):
        return "nan", None
    if math.isinf(x):
        return "positive_infinity" if x > 0 else "negative_infinity", None
    return "finite", x


def availability(values):
    count = Counter(number(x)[0] for x in values)
    return {
        kind: count[kind]
        for kind in (
            "finite",
            "missing",
            "nan",
            "positive_infinity",
            "negative_infinity",
        )
    }


def decimal_places(values):
    counts = Counter(
        str(max(0, -Decimal(x).as_tuple().exponent))
        for x in values
        if number(x)[0] == "finite"
    )
    return dict(sorted(counts.items(), key=lambda x: int(x[0])))


def calendar(value, form):
    d = datetime.strptime(value, form) - datetime(1970, 1, 1)
    return Decimal(d.days * 86400 + d.seconds) + Decimal(d.microseconds) / 1000000


def clock_values(row):
    ns = int(row[".header.stamp.nsecs"])
    week = int(row[".gps_time.week_number"])
    seconds = Decimal(row[".gps_time.week_seconds"])
    require(0 <= ns < 1000000000, "nanosecond_range")
    require(
        week >= 0 and seconds.is_finite() and 0 <= seconds < 604800, "gps_time_range"
    )
    h = Decimal(int(row[".header.stamp.secs"])) + Decimal(ns) / 1000000000
    g = Decimal(315964800 + week * 604800) + seconds
    r = calendar(row["time"], "%Y/%m/%d/%H:%M:%S.%f")
    return r, h, g


def decimals(values):
    if not values:
        return {"count": 0, "minimum": None, "median": None, "maximum": None}
    return {
        "count": len(values),
        "minimum": str(min(values)),
        "median": str(statistics.median(values)),
        "maximum": str(max(values)),
    }


def timeline(values):
    steps = [b - a for a, b in zip(values, values[1:])]
    return {
        "records": len(values),
        "duplicates": len(values) - len(set(values)),
        "non_increasing_steps": sum(x <= 0 for x in steps),
        "increments_seconds": decimals(steps),
    }


def distance(csv_lat, csv_lon, mat_lat, mat_lon):
    require(
        all(math.isfinite(x) for x in (csv_lat, csv_lon, mat_lat, mat_lon)),
        "nonfinite_coordinate",
    )
    require(
        abs(csv_lat) <= 90
        and abs(mat_lat) <= 90
        and abs(csv_lon) <= 180
        and abs(mat_lon) <= 180,
        "coordinate_range",
    )
    p, q = math.radians(csv_lat), math.radians(mat_lat)
    a = (
        math.sin((p - q) / 2) ** 2
        + math.cos(p) * math.cos(q) * math.sin(math.radians(csv_lon - mat_lon) / 2) ** 2
    )
    return 2 * RADIUS * math.asin(math.sqrt(min(1.0, max(0.0, a))))


def floats(values):
    return {
        "count": len(values),
        "maximum": max(values) if values else None,
        "mean": math.fsum(values) / len(values) if values else None,
    }


def compare(target, matrix):
    require(matrix[0] == TARGET_HEADER, "mat_column_identity")
    mrows = matrix[1:]
    mismatch = [
        i + 1 for i, (a, b) in enumerate(zip(target, mrows)) if a["Time"] != b[0]
    ]
    out = {
        "csv_records": len(target),
        "mat_records": len(mrows),
        "timestamp_mismatch_rows": mismatch,
    }
    if len(target) != len(mrows) or mismatch:
        return out | {
            "status": "row_identity_failed",
            "numeric_columns": None,
            "spherical_displacement_m": None,
        }
    numeric = {}
    for j, name in enumerate(TARGET_HEADER[1:], 1):
        pairs = [(number(a[name]), number(b[j])) for a, b in zip(target, mrows)]
        valid = [(a[1], b[1]) for a, b in pairs if a[0] == b[0] == "finite"]
        diffs = [abs(a - b) for a, b in valid]
        numeric[name] = floats(diffs) | {
            "different_binary_values": sum(a != b for a, b in valid),
            "unavailable_pairs": len(pairs) - len(valid),
            "availability_mismatch_pairs": sum(a[0] != b[0] for a, b in pairs),
        }
    displacements = []
    for a, b in zip(target, mrows):
        xy = [number(a["Latitude"]), number(a["Longitude"]), number(b[1]), number(b[2])]
        if all(x[0] == "finite" for x in xy):
            displacements.append(distance(*(x[1] for x in xy)))
    return out | {
        "status": "row_identity_agreed",
        "numeric_columns": numeric,
        "spherical_displacement_m": floats(displacements),
    }


def analyze(sources):
    ego, target = rows(sources / EGO, EGO_HEADER), rows(sources / TARGET, TARGET_HEADER)
    r, h, g = map(list, zip(*(clock_values(row) for row in ego)))
    target_times = [calendar(row["Time"], "%d-%m-%Y %H:%M:%S.%f") for row in target]
    return {
        "document_id": "reiyah.compact-motion.result",
        "version": "0.1.0",
        "status": "exploratory",
        "ego_records": len(ego),
        "target_records": len(target),
        "ego_numeric_availability": {
            k: availability([x[k] for x in ego]) for k in EGO_HEADER[9:]
        },
        "target_numeric_availability": {
            k: availability([x[k] for x in target]) for k in TARGET_HEADER[1:]
        },
        "target_coordinate_decimal_places": {
            k: decimal_places([x[k] for x in target]) for k in ["Latitude", "Longitude"]
        },
        "ego_status": dict(sorted(Counter(x[".status"] for x in ego).items())),
        "ego_position_type": dict(sorted(Counter(x[".pos_type"] for x in ego).items())),
        "timelines": {
            "ego_calendar_text": timeline(r),
            "ego_header": timeline(h),
            "ego_gps": timeline(g),
            "target_calendar_text": timeline(target_times),
        },
        "clock_differences_seconds": {
            "calendar_text_minus_header": decimals([a - b for a, b in zip(r, h)]),
            "gps_epoch_plus_week_minus_header": decimals([a - b for a, b in zip(g, h)]),
        },
        "target_serialization": compare(target, mat_rows(sources / MAT)),
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
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    bind(Path(__file__).parent, args.sources, args.freeze)
    result = analyze(args.sources)
    result["freeze_sha256"] = args.freeze
    write_new(args.output, result)
    print(
        {
            "output": str(args.output),
            "ego_records": result["ego_records"],
            "target_records": result["target_records"],
            "physical_clearance": "unresolved",
        }
    )
