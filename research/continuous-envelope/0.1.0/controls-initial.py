"""Bounded authored tests, exact grid, expansion identities and forged results."""

from pathlib import Path
from fractions import Fraction as F
from itertools import product
import argparse
import copy
import tempfile
from common import Invalid, frozen, load, parse_case, require, write_new
import producer
import reference


def rejected(fn):
    try:
        fn()
    except Invalid as exc:
        return str(exc)
    raise AssertionError("expected rejection")


def grid_case(l0, l1, w0, w1, k, tau, horizon):
    return {
        "id": "grid",
        "horizon_s": list(horizon),
        "threshold_m": "1",
        "quantity": {
            "kind": "road_projected_signed_clearance",
            "unit": "m",
            "provenance": "authored",
        },
        "motion": {"kind": "global_lipschitz", "rate_mps": str(k)},
        "clock": {"kind": "common_offset", "radius_s": str(tau)},
        "observations": [
            {"id": "first", "time_s": "0", "interval_m": [str(l0), str(l0 + w0)]},
            {"id": "last", "time_s": "2", "interval_m": [str(l1), str(l1 + w1)]},
        ],
    }


def run(cases):
    known = {
        "safe-samples-hidden-dip": ("unresolved", ["4", "6"]),
        "equality-supported": ("supported", ["5", "7"]),
        "observed-violation": ("contradicted", ["2", "4"]),
        "bounded-interval-supported": ("supported", ["5", "7"]),
        "constant-uncertain": ("unresolved", ["4", "6"]),
        "constant-joint-binding": ("supported", ["7", "7"]),
        "motion-inconsistent": ("inconsistent_premises", None),
        "constant-inconsistent": ("inconsistent_premises", None),
        "shared-clock-point": ("unresolved", ["2", "6"]),
        "shared-clock-window": ("unresolved", ["2", "6"]),
        "outside-sample-horizon": ("unresolved", ["3", "7"]),
        "three-interval-dependency": ("supported", ["5", "6"]),
    }
    for case in cases:
        actual = producer.solve(case)
        reference.check(case, actual)
        if case["id"] in known:
            status, bounds = known[case["id"]]
            require(
                (actual["status"], actual.get("minimum_range_m")) == (status, bounds),
                "hand_derived:" + case["id"],
            )
    counts = dict(
        authored_cases=len(cases),
        hand_derived_cases=len(known),
        grid_cases=0,
        interval_expansions=0,
    )
    horizons = (("0", "2"), ("0", "0"), ("1/2", "3/2"))
    for args in product(
        range(3),
        range(3),
        range(2),
        range(2),
        range(3),
        (F(0), F(1, 2), F(1)),
        horizons,
    ):
        case = grid_case(*args)
        actual = producer.solve(case)
        reference.check(case, actual)
        counts["grid_cases"] += 1
        if "minimum_range_m" not in actual:
            continue
        lo, hi = map(F, actual["minimum_range_m"])
        for epsilon in (F(0), F(1, 2), F(2)):
            wider = copy.deepcopy(case)
            for row in wider["observations"]:
                lower, upper = map(F, row["interval_m"])
                row["interval_m"] = [str(lower - epsilon), str(upper + epsilon)]
            expanded = producer.solve(wider)
            reference.check(wider, expanded)
            require(
                expanded["minimum_range_m"] == [str(lo - epsilon), str(hi + epsilon)],
                "expansion_identity",
            )
            counts["interval_expansions"] += 1

    malformed = {}
    seed = copy.deepcopy(cases[0])

    def bad(name, change):
        value = copy.deepcopy(seed)
        change(value)
        malformed[name] = rejected(lambda: parse_case(value))

    bad("unknown_property", lambda x: x.update(unknown=1))
    bad("floating_threshold", lambda x: x.update(threshold_m=5.0))
    bad("boolean_threshold", lambda x: x.update(threshold_m=True))
    bad("noncanonical_rational", lambda x: x.update(threshold_m="10/2"))
    bad("negative_zero", lambda x: x.update(threshold_m="-0"))
    bad("numeric_cap", lambda x: x.update(threshold_m="1000000001"))
    bad("denominator_cap", lambda x: x.update(threshold_m="1/1000001"))
    bad("reversed_horizon", lambda x: x.update(horizon_s=["2", "0"]))
    bad("negative_motion", lambda x: x["motion"].update(rate_mps="-1"))
    bad("negative_clock", lambda x: x["clock"].update(radius_s="-1"))
    bad("per_sample_jitter", lambda x: x["clock"].update(kind="independent_jitter"))
    bad(
        "unlicensed_interpolation",
        lambda x: x["motion"].update(kind="linear_interpolation"),
    )
    bad("physical_claim", lambda x: x["quantity"].update(provenance="calibrated"))
    bad("wrong_units", lambda x: x["quantity"].update(unit="ft"))
    bad("unknown_geometry", lambda x: x["quantity"].update(kind="front_to_front"))
    bad("duplicate_time", lambda x: x["observations"][1].update(time_s="0"))
    bad(
        "duplicate_id",
        lambda x: x["observations"][1].update(id=x["observations"][0]["id"]),
    )
    bad("interval_order", lambda x: x["observations"][0].update(interval_m=["7", "6"]))
    bad("interval_shape", lambda x: x["observations"][0].update(interval_m=["6"]))
    bad("row_property", lambda x: x["observations"][0].update(estimated=True))
    bad("case_identifier", lambda x: x.update(id="../escape"))
    bad("observation_cap", lambda x: x.update(observations=x["observations"] * 9))
    with tempfile.TemporaryDirectory(prefix="envelope-json-") as tmp:
        path = Path(tmp) / "input.json"
        for name, body in (
            ("duplicate_json_key", '{"a":1,"a":2}'),
            ("nonfinite_json", '{"a":NaN}'),
            ("truncated_json", '{"a":'),
        ):
            path.write_text(body)
            malformed[name] = rejected(lambda: load(path))
        path.write_bytes(b" " * 101)
        malformed["file_cap"] = rejected(lambda: load(path, cap=100))

    forgeries = {}
    original = producer.solve(seed)

    def forged(name, change):
        value = copy.deepcopy(original)
        change(value)
        forgeries[name] = rejected(lambda: reference.check(seed, value))

    forged("false_support", lambda x: x.update(status="supported"))
    forged("false_contradiction", lambda x: x.update(status="contradicted"))
    forged("wrong_extremum", lambda x: x.update(minimum_range_m=["5", "6"]))
    forged("physical_promotion", lambda x: x.update(physical_status="supported"))
    forged("wrong_case", lambda x: x.update(id="other"))
    forged("unknown_field", lambda x: x.update(extra=0))
    forged("bad_offset", lambda x: x["lower_witness"].update(offset_s="1"))
    forged("wrong_witness_time", lambda x: x["lower_witness"].update(time_s="0"))
    forged("wrong_witness_minimum", lambda x: x["lower_witness"].update(minimum_m="5"))
    forged("wrong_witness_kind", lambda x: x["upper_witness"].update(envelope="lower"))
    forged(
        "wrong_budget",
        lambda x: x["extra_error_allowance_m"].update(support_inclusive="1"),
    )
    forged(
        "wrong_query_value",
        lambda x: x["distinguishing_observation"].update(upper_world_m="7"),
    )
    forged(
        "wrong_query_precision",
        lambda x: x["distinguishing_observation"].update(
            absolute_error_strictly_below_m="2"
        ),
    )
    forged(
        "overclaimed_query",
        lambda x: x["distinguishing_observation"].update(scope="guaranteed_resolution"),
    )
    forgeries["wrong_result_type"] = rejected(lambda: reference.check(seed, []))
    # Both directions of the strict extra-error boundary are checked exactly.
    for index, epsilon, wanted in (
        (1, F(0), "supported"),
        (1, F(1, 2), "unresolved"),
        (2, F(1), "unresolved"),
        (2, F(1, 2), "contradicted"),
    ):
        case = copy.deepcopy(cases[index])
        for row in case["observations"]:
            lower, upper = map(F, row["interval_m"])
            row["interval_m"] = [str(lower - epsilon), str(upper + epsilon)]
        require(producer.solve(case)["status"] == wanted, "strict_boundary")
    # The separate check remains functional while producer execution is disabled.
    saved = producer.solve
    producer.solve = lambda _: (_ for _ in ()).throw(
        AssertionError("producer_disabled")
    )
    try:
        reference.check(seed, original)
    finally:
        producer.solve = saved
    counts.update(
        malformed_rejections=len(malformed),
        result_forgeries=len(forgeries),
        strict_boundaries=4,
        producer_disabled_checks=1,
    )
    return {
        "document_id": "reiyah.continuous-envelope.controls",
        "version": "0.1.0",
        "status": "pass",
        "counts": counts,
        "malformed": malformed,
        "forgeries": forgeries,
        "scope": "authored_correctness; finite_grid_not_empirical_coverage",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze-sha256", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    cases = frozen(Path(__file__).resolve().parent, args.freeze_sha256)
    report = run(cases)
    report["freeze_sha256"] = args.freeze_sha256
    write_new(args.output, report)
    print(report["counts"])
