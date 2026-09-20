"""Complete-source reference and prefix verification; no producer import."""

import argparse
import csv
import math
from pathlib import Path

from binding import bind, digest, mat_rows, read_json, require, verify_files, write_new


def reference_states(sources, freeze):
    spec = freeze["csv_inputs"]["target"]
    with (sources / spec["file"]).open(newline="") as file:
        csv_rows = list(csv.reader(file))
    mat = mat_rows(sources / freeze["mat_input"])
    require(csv_rows[0] == mat[0] == spec["header"], "reference_decision_columns")
    require(len(csv_rows) == len(mat) and len(mat) > 1, "reference_decision_length")
    require(all(len(row) == 6 for row in csv_rows), "reference_decision_row")
    states = []
    for row, original in zip(csv_rows[1:], mat[1:]):
        require(row[0] == original[0], "reference_decision_time")
        mismatch, unavailable = False, False
        for j in [1, 2]:
            if (
                row[j] == ""
                or not math.isfinite(float(row[j]))
                or not math.isfinite(original[j])
            ):
                unavailable = True
            elif float(row[j]) != original[j]:
                mismatch = True
        states.append(
            "different" if mismatch else "unknown" if unavailable else "equal"
        )
    return states


def verify(result, states, analysis_digest, decision_digest):
    require(
        type(result) is dict
        and set(result)
        == {
            "document_id",
            "version",
            "status",
            "analysis_freeze_sha256",
            "decision_freeze_sha256",
            "population_records",
            "allocated_decisions",
            "shared_binding_and_decode",
            "reiyah",
            "conventional",
            "source_acquisition_charged_separately_once",
            "logical_reveal_is_not_physical_acquisition",
            "physical_clearance",
            "independent_baseline_authorship",
        },
        "decision_result_fields",
    )
    require(
        result["document_id"] == "reiyah.compact-motion.decision"
        and result["version"] == "0.1.0"
        and result["status"] == "exploratory",
        "decision_result_identity",
    )
    require(
        result["analysis_freeze_sha256"] == analysis_digest
        and result["decision_freeze_sha256"] == decision_digest,
        "decision_result_freeze",
    )
    n = len(states)
    require(
        type(result["population_records"]) is int
        and result["population_records"] == n
        and type(result["allocated_decisions"]) is int
        and result["allocated_decisions"] == 1,
        "decision_population",
    )
    count_diff, count_unknown = states.count("different"), states.count("unknown")
    full = (
        "contradicted" if count_diff else "unresolved" if count_unknown else "supported"
    )
    queries = states.index("different") + 1 if count_diff else n
    expected_trace = []
    for k in range(queries + 1):
        prefix = states[:k]
        lower, upper = prefix.count("different"), n - prefix.count("equal")
        answer = (
            "contradicted" if lower else "supported" if upper == 0 else "unresolved"
        )
        expected_trace.append(
            dict(
                queries=k,
                lower_mismatches=lower,
                upper_mismatches=upper,
                decision=answer,
            )
        )
        require(
            lower <= count_diff and upper >= count_diff + count_unknown,
            "complete_reference_outside_bounds",
        )
    for name in ["reiyah", "conventional"]:
        arm = result[name]
        fields = {
            "decision",
            "queries",
            "query_indices",
            "wall_seconds",
            "process_cpu_seconds",
        }
        if name == "reiyah":
            fields.add("trace")
        require(set(arm) == fields, "decision_arm_fields")
        require(
            arm["decision"] == full
            and type(arm["queries"]) is int
            and arm["queries"] == queries,
            "decision_or_stop",
        )
        require(
            arm["query_indices"] == list(range(queries))
            and all(type(i) is int for i in arm["query_indices"]),
            "decision_query_identity",
        )
        if name == "reiyah":
            require(
                type(arm["trace"]) is list
                and all(
                    type(row) is dict
                    and all(
                        type(row.get(k)) is int
                        for k in ["queries", "lower_mismatches", "upper_mismatches"]
                    )
                    for row in arm["trace"]
                ),
                "bound_integer_types",
            )
            require(arm["trace"] == expected_trace, "complete_prefix_bounds")
    require(
        set(result["shared_binding_and_decode"])
        == {"wall_seconds", "process_cpu_seconds"},
        "shared_cost_fields",
    )
    for record in [
        result["reiyah"],
        result["conventional"],
        result["shared_binding_and_decode"],
    ]:
        for key in ["wall_seconds", "process_cpu_seconds"]:
            require(
                type(record[key]) is float
                and math.isfinite(record[key])
                and record[key] >= 0,
                "invalid_cost",
            )
    require(
        result["physical_clearance"] == "unresolved"
        and result["independent_baseline_authorship"] is False
        and result["logical_reveal_is_not_physical_acquisition"] is True
        and result["source_acquisition_charged_separately_once"] is True,
        "decision_scope",
    )
    return {
        "complete_reference": full,
        "population_records": n,
        "full_reference_different": count_diff,
        "full_reference_equal": states.count("equal"),
        "full_reference_unknown": count_unknown,
        "logical_queries_each": queries,
        "resolved_decisions_each": int(full != "unresolved"),
        "unresolved_decisions_each": int(full == "unresolved"),
        "false_acceptances_each": 0,
        "false_refusals_each": 0,
        "complete_bound_trace_rows": len(expected_trace),
        "method_decision_parity": True,
        "query_advantage": False,
        "actual_acquisition_saving_established": False,
        "cost_check_scope": "finite nonnegative recorded timers only; outer process measured separately",
        "independent_replication": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--decision-freeze", required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    packet = Path(__file__).parent
    freeze = bind(packet, args.sources, args.freeze)
    require(
        digest(packet / "decision-freeze.json") == args.decision_freeze,
        "decision_freeze_identity",
    )
    supplement = read_json(packet / "decision-freeze.json")
    require(
        supplement["analysis_freeze_sha256"] == args.freeze, "analysis_freeze_identity"
    )
    verify_files(packet, supplement["files"])
    result = {
        "document_id": "reiyah.compact-motion.decision-check",
        "version": "0.1.0",
        "status": "pass",
        "analysis_freeze_sha256": args.freeze,
        "decision_freeze_sha256": args.decision_freeze,
        "result_sha256": digest(args.result),
    }
    result.update(
        verify(
            read_json(args.result),
            reference_states(args.sources, freeze),
            args.freeze,
            args.decision_freeze,
        )
    )
    write_new(args.output, result)
    print(result)
