"""Directed universal-response boundaries, source tampering and actual-result attacks."""

import argparse
import copy
from fractions import Fraction as F
from pathlib import Path
import tempfile

from binding import bind, identity, verify_files
from common import load, require, write_new
from envelope import solve
from check import verify_record
import response_check
import responses
from workflow import Oracle, append_measurement

PRE_IDS = [
    "midpoint-full-partition",
    "point-exact",
    "point-noisy",
    "known-clock-singleton",
    "constant-signal",
    "query-outside-horizon",
    "already-supported",
    "already-contradicted",
    "disconnected-clock-starts",
    "inconsistent-prior",
    "missing-clock",
    "empty-strict-polyhedron",
    "open-projection-endpoint",
    "singleton-projection",
    "tiny-strict-response",
    "wrong-property",
    "noncanonical-rational",
    "negative-error",
    "bool-availability",
    "unregistered-blocked",
    "unavailable-blocked",
    "oracle-no-extrapolation",
    "oracle-no-repeat",
    "source-byte-tamper",
    "frozen-byte-tamper",
]


def pre(packet, sources, freeze):
    cases, oracles = bind(packet, sources, freeze)
    byid = {x["id"]: x for x in cases}
    observed = []

    def equal(name, case, query, guarantee=None):
        actual = responses.plan(case, query)
        response_check.verify(case, query, actual)
        if guarantee is not None:
            require(actual["guaranteed_resolution"] is guarantee, name)
        observed.append(dict(id=name, status="passed"))
        return actual

    source = byid["pair-query-then-complete-support"]
    result = equal(
        "midpoint-full-partition", source["model"], source["queries"][0], False
    )
    require(
        result["response_partition"]
        == [
            dict(
                lower="4",
                upper="5",
                lower_closed=True,
                upper_closed=False,
                status="contradicted",
            ),
            dict(
                lower="5",
                upper="6",
                lower_closed=True,
                upper_closed=False,
                status="unresolved",
            ),
            dict(
                lower="6",
                upper="8",
                lower_closed=True,
                upper_closed=True,
                status="supported",
            ),
        ],
        "midpoint_expected_partition",
    )
    updated, _ = append_measurement(source["model"], source["queries"][0], F(11, 2))
    require(
        solve(updated)["minimum_range_m"] == ["19/4", "11/2"],
        "post_midpoint_complete_bounds",
    )
    point = byid["noiseless-point-equality"]
    equal("point-exact", point["model"], point["queries"][0], True)
    noisy = byid["noisy-point-abstention"]
    r = equal("point-noisy", noisy["model"], noisy["queries"][0], False)
    require(responses.response_status(r, "5") == "unresolved", "noisy_actual_response")
    c = byid["common-clock-needs-more-data"]
    r = equal("known-clock-singleton", c["model"], c["queries"][0], False)
    require(r["feasible_responses"] == ["11/2", "11/2"], "singleton_feasible_response")
    model = copy.deepcopy(point["model"])
    model["motion"]["rate_mps"] = "0"
    model["horizon_s"] = ["0", "2"]
    equal("constant-signal", model, point["queries"][0], True)
    q = copy.deepcopy(point["queries"][0])
    q["time_s"] = "1"
    equal("query-outside-horizon", point["model"], q, False)
    c = byid["already-supported-no-acquisition"]
    equal("already-supported", c["model"], c["queries"][0], True)
    model = copy.deepcopy(point["model"])
    model["observations"][0]["interval_m"] = ["4", "4"]
    r = equal("already-contradicted", model, point["queries"][0], True)
    require(r["possible_statuses"] == ["contradicted"], "already_contradicted")
    model["clock"]["radius_s"] = "2"
    equal("disconnected-clock-starts", model, q, False)
    model = copy.deepcopy(source["model"])
    model["observations"][1]["interval_m"] = ["0", "0"]
    require(
        equal("inconsistent-prior", model, source["queries"][0])["status"]
        == "inconsistent_premises",
        "inconsistent_state",
    )
    model = copy.deepcopy(point["model"])
    model["clock"] = None
    require(equal("missing-clock", model, q)["status"] == "blocked", "missing_state")
    constraints = response_check.domain(F(0), F(1), F(0), F(1))
    require(
        response_check.projected_interval(constraints + [(F(1), F(0), F(0), True)])
        is None,
        "strict_empty_face",
    )
    observed.append(dict(id="empty-strict-polyhedron", status="passed"))
    require(
        response_check.projected_interval(constraints + [(F(0), F(1), F(1), True)])
        == (F(0), F(1), True, False),
        "open_endpoint_projection",
    )
    observed.append(dict(id="open-projection-endpoint", status="passed"))
    require(
        response_check.projected_interval(response_check.domain(F(0), F(0), F(2), F(2)))
        == (F(2), F(2), True, True),
        "singleton_projection",
    )
    observed.append(dict(id="singleton-projection", status="passed"))
    model = copy.deepcopy(point["model"])
    model["observations"][0]["interval_m"] = ["4999999/1000000", "5000001/1000000"]
    r = equal("tiny-strict-response", model, point["queries"][0], True)
    require(
        responses.response_status(r, "4999999/1000000") == "contradicted"
        and responses.response_status(r, "5") == "supported",
        "strict_boundary",
    )

    def rejected(name, functions):
        for fn in functions:
            try:
                fn()
            except (ValueError, TypeError):
                pass
            else:
                raise ValueError("invalid_accepted:" + name)
        observed.append(dict(id=name, status="rejected_as_expected"))

    for name, edit in [
        ("wrong-property", lambda x: x.update(physical_certified=True)),
        ("noncanonical-rational", lambda x: x.update(time_s="0/1")),
        ("negative-error", lambda x: x.update(error_m="-1")),
        ("bool-availability", lambda x: x.update(available=0)),
    ]:
        query = copy.deepcopy(point["queries"][0])
        edit(query)
        rejected(
            name,
            [
                lambda z=query: responses.plan(point["model"], z),
                lambda z=query: response_check.plan(point["model"], z),
            ],
        )
    for name, case_id in [
        ("unregistered-blocked", "unregistered-query"),
        ("unavailable-blocked", "unavailable-query"),
    ]:
        c = byid[case_id]
        require(
            equal(name, c["model"], c["queries"][0])["status"] == "acquisition_blocked",
            "blocked_channel",
        )
    oracle = Oracle(oracles[point["oracle_id"]])
    query = copy.deepcopy(point["queries"][0])
    query["time_s"] = "2"
    rejected("oracle-no-extrapolation", [lambda: oracle.reveal(query)])
    oracle.reveal(point["queries"][0])
    rejected("oracle-no-repeat", [lambda: oracle.reveal(point["queries"][0])])
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        p = root / "operand.json"
        p.write_text("original")
        expected = {p.name: identity(p)}
        p.write_text("changed")
        rejected("source-byte-tamper", [lambda: verify_files(root, expected)])
        p = root / "freeze.json"
        p.write_bytes((packet / "freeze.json").read_bytes() + b" ")
        rejected("frozen-byte-tamper", [lambda: bind(root, sources, freeze)])
    require([x["id"] for x in observed] == PRE_IDS, "control_membership")
    return observed


def post(actual, baseline):
    verify_record(actual, baseline)
    records = []

    def target(report):
        return next(
            c for c in report["cases"] if c["id"] == "pair-query-then-complete-support"
        )

    mutations = [
        (
            "false_guarantee",
            lambda r: target(r)["steps"][0]["predicted"].update(
                guaranteed_resolution=True
            ),
        ),
        (
            "omit_unresolved_response_cell",
            lambda r: target(r)["steps"][0]["predicted"]["response_partition"].pop(1),
        ),
        (
            "strict_boundary_inclusion",
            lambda r: target(r)["steps"][0]["predicted"]["response_partition"][
                0
            ].update(upper_closed=True),
        ),
        (
            "wrong_actual_reply",
            lambda r: target(r)["steps"][0].update(reported_value_m="4"),
        ),
        (
            "wrong_after_decision",
            lambda r: target(r)["steps"][0]["after"].update(status="supported"),
        ),
        ("missing_final_acquisition", lambda r: target(r)["steps"].pop()),
        ("wrong_oracle_cost", lambda r: target(r).update(oracle_calls=0)),
        (
            "changed_model_scope",
            lambda r: target(r).update(physical_status="supported"),
        ),
        ("case_omitted", lambda r: r["cases"].pop()),
        ("wrong_freeze", lambda r: r.update(freeze_sha256="0" * 64)),
    ]
    for name, mutate in mutations:
        bad = copy.deepcopy(actual)
        mutate(bad)
        try:
            verify_record(bad, baseline)
        except ValueError:
            records.append(dict(id=name, status="rejected_as_expected"))
        else:
            raise ValueError("mutation_accepted:" + name)
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("pre", "post"))
    for arg in ("sources", "freeze-sha256", "output"):
        parser.add_argument("--" + arg, required=True)
    parser.add_argument("--results")
    parser.add_argument("--baseline")
    args = parser.parse_args()
    packet = Path(__file__).parent
    bind(packet, Path(args.sources), args.freeze_sha256)
    records = (
        pre(packet, Path(args.sources), args.freeze_sha256)
        if args.mode == "pre"
        else post(load(args.results), load(args.baseline))
    )
    write_new(
        args.output,
        dict(
            document_id="reiyah.measurement-resolution.controls",
            version="0.1.0",
            mode=args.mode,
            status="passed",
            count=len(records),
            records=records,
            scope="Directed mathematical and tamper controls, not empirical coverage or additional independent experiments.",
        ),
    )
    print(dict(mode=args.mode, count=len(records), status="passed"))


if __name__ == "__main__":
    main()
