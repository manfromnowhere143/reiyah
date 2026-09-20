"""Adversarial controls for universal export admission and equal-information stopping."""

import argparse
import copy
from pathlib import Path

from binding import read_json, require, write_new
from decision import (
    Oracle,
    conventional_method,
    decision_bind,
    interval_method,
    measured,
)
from decision_check import reference_states, verify


def record(population):
    return {
        "document_id": "reiyah.compact-motion.decision",
        "version": "0.1.0",
        "status": "exploratory",
        "analysis_freeze_sha256": "control",
        "decision_freeze_sha256": "control",
        "population_records": len(population),
        "allocated_decisions": 1,
        "shared_binding_and_decode": {"wall_seconds": 0.0, "process_cpu_seconds": 0.0},
        "reiyah": measured(interval_method, population),
        "conventional": measured(conventional_method, population),
        "source_acquisition_charged_separately_once": True,
        "logical_reveal_is_not_physical_acquisition": True,
        "physical_clearance": "unresolved",
        "independent_baseline_authorship": False,
    }


def pre():
    equal = (["1", "2"], [1.0, 2.0])
    different = (["1", "2"], [1.0, 3.0])
    unknown = (["NaN", "2"], [1.0, 2.0])
    partial_difference = (["NaN", "2"], [1.0, 3.0])
    cases = [
        ("all_equal", [equal, equal], ["equal", "equal"], "supported", 2),
        (
            "first_counterexample",
            [different, equal],
            ["different", "equal"],
            "contradicted",
            1,
        ),
        (
            "late_counterexample",
            [equal, unknown, different],
            ["equal", "unknown", "different"],
            "contradicted",
            3,
        ),
        ("all_unknown", [unknown, unknown], ["unknown", "unknown"], "unresolved", 2),
        (
            "partial_counterexample",
            [partial_difference],
            ["different"],
            "contradicted",
            1,
        ),
        ("unknown_not_equal", [unknown, equal], ["unknown", "equal"], "unresolved", 2),
    ]
    results = []
    for name, population, states, answer, queries in cases:
        value = record(population)
        checked = verify(value, states, "control", "control")
        require(
            checked["complete_reference"] == answer
            and checked["logical_queries_each"] == queries,
            "hand_expectation",
        )
        results.append({"id": name, "status": "pass"})
    for function in (interval_method, conventional_method):
        try:
            function(Oracle([]))
        except ValueError as exc:
            require(str(exc) == "empty_population", "wrong_empty_rejection")
        else:
            raise AssertionError("empty_population_accepted")
    results.append({"id": "empty_population_both", "status": "pass"})
    return results


def post(sources, analysis, supplement, result):
    freeze = read_json(Path(__file__).parent / "freeze.json")
    states = reference_states(sources, freeze)
    verify(result, states, analysis, supplement)
    mutations = [
        (
            "false_acceptance",
            lambda r: r["reiyah"].update(
                decision="supported"
                if r["reiyah"]["decision"] != "supported"
                else "contradicted"
            ),
        ),
        (
            "forged_upper_bound",
            lambda r: r["reiyah"]["trace"][0].update(upper_mismatches=0),
        ),
        (
            "wrong_query_identity",
            lambda r: r["conventional"].update(query_indices=[999999]),
        ),
        ("negative_cost", lambda r: r["reiyah"].update(wall_seconds=-1.0)),
        ("physical_promotion", lambda r: r.update(physical_clearance="supported")),
        ("wrong_freeze", lambda r: r.update(decision_freeze_sha256="0" * 64)),
    ]
    results = []
    for name, mutate in mutations:
        bad = copy.deepcopy(result)
        mutate(bad)
        require(bad != result, "mutation_must_change_value")
        try:
            verify(bad, states, analysis, supplement)
        except ValueError as exc:
            results.append({"id": name, "status": "pass", "rejection": str(exc)})
        else:
            raise AssertionError("forged_decision_accepted")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["pre", "post"])
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--decision-freeze", required=True)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    decision_bind(
        Path(__file__).parent, args.sources, args.freeze, args.decision_freeze
    )
    rows = (
        pre()
        if args.phase == "pre"
        else post(
            args.sources, args.freeze, args.decision_freeze, read_json(args.result)
        )
    )
    result = {
        "document_id": "reiyah.compact-motion.decision-controls",
        "version": "0.1.0",
        "phase": args.phase,
        "status": "pass",
        "decision_freeze_sha256": args.decision_freeze,
        "results": rows,
    }
    write_new(args.output, result)
    print({"phase": args.phase, "controls": len(rows), "status": "pass"})
