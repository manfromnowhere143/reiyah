"""Small analytic and rejection controls for source diagnostics, not driving cases."""

import argparse
import copy
from decimal import Decimal
import math
from pathlib import Path
import tempfile

import audit
from binding import bind, digest, read_json, require, verify_files, write_new
import check


def run_pre():
    results = []

    def test(name, action):
        action()
        results.append({"id": name, "status": "pass"})

    def close(a, b, tol=1e-6):
        require(abs(a - b) <= tol, "analytic_expectation")

    def rejects(action, reason):
        try:
            action()
        except ValueError as exc:
            require(reason in str(exc), "wrong_rejection")
        else:
            raise AssertionError("accepted_invalid_control")

    test("coincident", lambda: close(audit.distance(47, 17, 47, 17), 0))
    expected = 6371008.8 * math.pi / 180 * 0.0001
    test(
        "latitude_step_analytic",
        lambda: close(audit.distance(0, 0, 0.0001, 0), expected),
    )
    test(
        "longitude_step_reference",
        lambda: close(check.chord_distance(0, 0, 0, 0.0001), expected),
    )
    test(
        "antimeridian",
        lambda: close(audit.distance(0, 179.9999, 0, -179.9999), expected * 2),
    )
    test(
        "nonfinite_coordinate_rejected",
        lambda: rejects(
            lambda: audit.distance(math.nan, 0, 0, 0), "nonfinite_coordinate"
        ),
    )
    test(
        "latitude_range_rejected",
        lambda: rejects(lambda: audit.distance(91, 0, 0, 0), "coordinate_range"),
    )
    expected_availability = dict(
        finite=1, missing=1, nan=1, positive_infinity=1, negative_infinity=1
    )
    test(
        "missing_and_nonfinite_distinct",
        lambda: require(
            audit.availability(["0", "", "NaN", "inf", "-inf"])
            == expected_availability,
            "availability",
        ),
    )
    test(
        "precision_exponent",
        lambda: require(
            audit.decimal_places(["1.000", "1.5e-3", "NaN"]) == {"3": 1, "4": 1},
            "precision",
        ),
    )
    row = {
        "time": "1980/01/06/00:00:00.000000",
        ".header.stamp.secs": "315964800",
        ".header.stamp.nsecs": "12345",
        ".gps_time.week_number": "0",
        ".gps_time.week_seconds": "0",
    }
    test(
        "exact_clock_fraction",
        lambda: require(
            audit.clock_values(row)
            == (
                Decimal("315964800"),
                Decimal("315964800.000012345"),
                Decimal("315964800"),
            ),
            "clock",
        ),
    )
    test(
        "nanosecond_boundary",
        lambda: rejects(
            lambda: audit.clock_values(row | {".header.stamp.nsecs": "1000000000"}),
            "nanosecond_range",
        ),
    )
    test(
        "gps_week_boundary",
        lambda: rejects(
            lambda: audit.clock_values(row | {".gps_time.week_seconds": "604800"}),
            "gps_time_range",
        ),
    )
    test(
        "gps_nonfinite",
        lambda: rejects(
            lambda: audit.clock_values(row | {".gps_time.week_seconds": "NaN"}),
            "gps_time_range",
        ),
    )
    sample = dict(
        zip(audit.TARGET_HEADER, ["01-01-2020 00:00:00.000", "0", "0", "NaN", "1", "2"])
    )
    matrix = [audit.TARGET_HEADER, [sample["Time"], 0.0, 0.0, math.nan, 1.0, 2.0]]
    test(
        "unavailable_difference_not_zero",
        lambda: require(
            audit.compare([sample], matrix)["numeric_columns"]["LatStdDev"]["maximum"]
            is None,
            "unknown",
        ),
    )
    altered = copy.deepcopy(matrix)
    altered[1][0] = "01-01-2020 00:00:00.001"
    test(
        "row_identity_no_repair",
        lambda: require(
            audit.compare([sample], altered)["status"] == "row_identity_failed",
            "identity",
        ),
    )
    test(
        "row_count_no_truncation",
        lambda: require(
            audit.compare([sample, sample], matrix)["status"] == "row_identity_failed",
            "count",
        ),
    )
    with tempfile.TemporaryDirectory(prefix="compact-controls-") as directory:
        root = Path(directory)
        file = root / "fixture.csv"
        file.write_text("Time,Latitude\na,1,extra\n")
        test(
            "malformed_csv_row",
            lambda: rejects(
                lambda: audit.rows(file, ["Time", "Latitude"]), "csv_row_shape"
            ),
        )
        test(
            "wrong_csv_header",
            lambda: rejects(
                lambda: audit.rows(file, audit.TARGET_HEADER), "csv_header"
            ),
        )
        records = {file.name: {"bytes": file.stat().st_size, "sha256": digest(file)}}
        test("source_identity_good", lambda: verify_files(root, records))
        file.write_text("Time,Latitude\na,2,extra\n")
        test(
            "source_same_size_mutation",
            lambda: rejects(lambda: verify_files(root, records), "byte_identity"),
        )
        file.unlink()
        test(
            "source_absent",
            lambda: rejects(
                lambda: verify_files(root, records), "missing_or_symlink_source"
            ),
        )
    return results


def run_post(sources, freeze, actual):
    expected = check.reference(sources, freeze)
    expected["freeze_sha256"] = actual["freeze_sha256"]
    check.compare_result(actual, expected)
    mutations = [
        ("record_count", ["ego_records"], actual["ego_records"] + 1),
        (
            "clock_difference",
            ["clock_differences_seconds", "gps_epoch_plus_week_minus_header", "median"],
            "0",
        ),
        (
            "distance",
            ["target_serialization", "spherical_displacement_m", "maximum"],
            actual["target_serialization"]["spherical_displacement_m"]["maximum"] + 1,
        ),
        ("physical_promotion", ["scope", "calibrated_error_bound"], True),
        ("closed_reserve", ["scope", "reserved_images_closed"], 0),
    ]
    rows = []
    for name, path, value in mutations:
        bad = copy.deepcopy(actual)
        current = bad
        for key in path[:-1]:
            current = current[key]
        require(current[path[-1]] != value, "mutation_must_change_value")
        current[path[-1]] = value
        try:
            check.compare_result(bad, expected)
        except ValueError as exc:
            rows.append({"id": name, "status": "pass", "rejection": str(exc)})
        else:
            raise AssertionError("forged_result_accepted")
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["pre", "post"])
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--result", type=Path)
    args = parser.parse_args()
    freeze = bind(Path(__file__).parent, args.sources, args.freeze)
    results = (
        run_pre()
        if args.phase == "pre"
        else run_post(args.sources, freeze, read_json(args.result))
    )
    result = {
        "document_id": "reiyah.compact-motion.controls",
        "version": "0.1.0",
        "phase": args.phase,
        "status": "pass",
        "freeze_sha256": args.freeze,
        "results": results,
    }
    write_new(args.output, result)
    print({"phase": args.phase, "controls": len(results), "status": "pass"})
