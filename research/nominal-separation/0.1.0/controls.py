"""Focused geometric boundary cases and retained-result tamper rejection."""

import argparse
import copy
from fractions import Fraction as F
from pathlib import Path
import tempfile

import reference as conventional
import separation as producer
from custody import identity, read_json, require, verify_files, write_new


def model(times, positions):
    return [
        (t, tuple(F(v) for v in ((x, 0, 0) if type(x) in (int, F) else x)))
        for t, x in zip(times, positions)
    ]


def run_pre():
    records = []

    def case(name, ego, target, decision, drawdown=None):
        result, trace = producer.analyze(ego, target)
        expected, reference_trace = conventional.analyze(ego, target)
        conventional.verify(result, trace, expected, reference_trace)
        require(result["decision"] == decision, name + ":decision")
        if drawdown is not None:
            lo, hi = result["maximum_drawdown_pm"]
            require(lo <= F(drawdown) * 10**12 <= hi, name + ":drawdown")
        records.append(dict(id=name, status="passed"))
        return result, trace

    zero = model([0, 10], [0, 0])
    case("increasing", zero, model([0, 10], [1, 3]), "supported", 0)
    case("decreasing", zero, model([0, 10], [3, 1]), "contradicted", 2)
    case("coincident", zero, zero, "supported", 0)
    case("constant_nonzero", zero, model([0, 10], [2, 2]), "supported", 0)
    case("crossing_zero", zero, model([0, 10], [-1, 1]), "contradicted", 1)
    r, tr = case(
        "increasing_endpoints_hide_interior_dip",
        zero,
        model([0, 10], [(-1, 1, 0), (2, 1, 0)]),
        "contradicted",
    )
    require(
        F(tr[0]["q_end"]) > F(tr[0]["q_start"])
        and F(tr[0]["q_min"]) == 1
        and F(tr[0]["minimum_time_ns"]) == F(10, 3),
        "interior_minimum",
    )
    case(
        "prefix_peak_not_only_adjacent_drop",
        model([0, 8], [0, 0]),
        model([0, 2, 4, 6, 8], [1, 5, 4, 2, 6]),
        "contradicted",
        3,
    )
    case(
        "clipped_common_support",
        model([2, 8], [0, 0]),
        model([0, 10], [0, 10]),
        "supported",
        0,
    )
    case(
        "staggered_knots",
        model([0, 3, 10], [0, 1, 0]),
        model([1, 4, 9], [5, 4, 6]),
        "contradicted",
    )
    case(
        "exact_tiny_reversal",
        zero,
        model([0, 10], [F(1), F(1) - F(1, 10**30)]),
        "contradicted",
        F(1, 10**30),
    )
    case(
        "zero_derivative_increasing",
        zero,
        model([0, 10], [(0, 1, 0), (1, 1, 0)]),
        "supported",
        0,
    )
    require(
        producer.project(0.0, 179.9999) == conventional.position(0.0, 179.9999),
        "antimeridian_projection",
    )
    require(
        producer.project(0.0, -179.9999) == conventional.position(0.0, -179.9999),
        "antimeridian_projection",
    )
    records.append(dict(id="antimeridian_projection", status="passed"))

    def rejected(name, calls):
        for fn in calls:
            try:
                fn()
            except (ValueError, TypeError):
                pass
            else:
                raise ValueError(name + ":accepted_invalid")
        records.append(dict(id=name, status="passed"))

    for name, bad in [
        ("duplicate_clock", model([0, 0], [0, 1])),
        ("reversed_clock", model([1, 0], [0, 1])),
        ("insufficient_rows", model([0], [0])),
        ("no_overlap", model([20, 30], [0, 1])),
        ("single_common_instant", model([10, 20], [0, 1])),
    ]:
        rejected(
            name,
            [
                lambda b=bad: producer.analyze(zero, b),
                lambda b=bad: conventional.analyze(zero, b),
            ],
        )
    for name, coord in [
        ("nonfinite", float("nan")),
        ("boolean", True),
        ("text", "47"),
        ("out_of_range", 91.0),
        ("unsafe_integer", 2**54),
    ]:
        rejected(
            name,
            [
                lambda c=coord: producer.project(c, 0),
                lambda c=coord: conventional.position(c, 0),
            ],
        )
    rejected(
        "calendar_precision",
        [
            lambda: producer.calendar_ns("25-06-2020 09:01:10.1234567891", True),
            lambda: conventional.calendar("25-06-2020 09:01:10.1234567891", True),
        ],
    )
    require(
        producer.calendar_ns("25-06-2020 09:01:10.108", True)
        == conventional.calendar("25-06-2020 09:01:10.108", True),
        "clock_parser_agreement",
    )
    records.append(dict(id="clock_parser_agreement", status="passed"))
    for q in [F(0), F(1), F(2), F(1, 10**60), F(10**20, 3)]:
        a, b = producer.root_bounds(q), conventional.bounds(q)
        require(
            a == b and F(a[0], 10**12) ** 2 <= q <= F(a[1], 10**12) ** 2,
            "sqrt_enclosure",
        )
    records.append(dict(id="sqrt_exact_and_irrational_enclosures", status="passed"))
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "a").write_text("original")
        expected = {"a": identity(root / "a")}
        verify_files(root, expected)
        (root / "a").write_text("changed")
        rejected("source_byte_tamper", [lambda: verify_files(root, expected)])
        rejected(
            "path_traversal", [lambda: verify_files(root, {"../a": expected["a"]})]
        )
        (root / "bad.json").write_text('{"x": 1, "x": 2}')
        rejected("duplicate_json_key", [lambda: read_json(root / "bad.json")])
    return records


def run_post(result, trace, baseline):
    # The baseline result binds the independently reconstructed complete trace digest.
    require(result == baseline, "baseline_identity")
    conventional.verify(result, trace, baseline, trace)
    records = []
    mutations = [
        (
            "decision",
            lambda r, t: r.update(
                decision="supported"
                if r["decision"] == "contradicted"
                else "contradicted"
            ),
        ),
        ("maximum_drawdown", lambda r, t: r.update(maximum_drawdown_pm=[0, 0])),
        (
            "interval_count",
            lambda r, t: r.update(interval_count=r["interval_count"] + 1),
        ),
        ("source_binding", lambda r, t: r.update(freeze_sha256="0" * 64)),
        ("clock_binding", lambda r, t: r.update(previous_clock_constraints_verified=0)),
        ("invented_property", lambda r, t: r.update(physical_supported=True)),
        ("truncated_trace", lambda r, t: t.pop()),
        ("late_coefficient", lambda r, t: t[-1]["a"].__setitem__(0, "0")),
        ("witness_time", lambda r, t: t[0].update(minimum_time_ns="0")),
        ("source_rows", lambda r, t: t[0].update(ego_rows=[99, 100])),
        ("state", lambda r, t: t[0].update(state="unknown")),
    ]
    for name, mutate in mutations:
        r, t = copy.deepcopy(result), copy.deepcopy(trace)
        mutate(r, t)
        try:
            conventional.verify(r, t, baseline, trace)
        except ValueError:
            records.append(dict(id=name, status="rejected_as_expected"))
        else:
            raise ValueError("mutation_accepted:" + name)
    return records


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["pre", "post"])
    p.add_argument("--output", required=True)
    for name in ("result", "trace", "baseline"):
        p.add_argument("--" + name)
    a = p.parse_args()
    records = (
        run_pre()
        if a.mode == "pre"
        else run_post(read_json(a.result), read_json(a.trace), read_json(a.baseline))
    )
    write_new(
        a.output,
        dict(
            document_id="reiyah.nominal-separation.controls",
            version="0.1.0",
            mode=a.mode,
            status="passed",
            controls=len(records),
            records=records,
            limit="Finite directed implementation checks; not a prevalence estimate or independent replication.",
        ),
    )
    print(dict(mode=a.mode, controls=len(records), status="passed"))


if __name__ == "__main__":
    main()
