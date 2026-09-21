"""Independent conventional protocol replay, source reply checks and native witnesses."""

import argparse
from collections import Counter
import copy
from fractions import Fraction as F
from pathlib import Path
import resource
import time

from binding import bind
from common import load, parse_case, rational, require, write_new
from linear_check import check as check_witness
from linear_check import solve
from response_check import plan


def summary(answer):
    return {
        key: answer[key]
        for key in ("status", "minimum_range_m", "missing")
        if key in answer
    }


def oracle_reply(oracle, query):
    q = F(query["time_s"])
    knots = [tuple(map(F, row)) for row in oracle["knots"]]
    for (left, a), (right, b) in zip(knots, knots[1:]):
        if left <= q <= right:
            value = ((right - q) * a + (q - left) * b) / (right - left)
            return value + F(oracle["reporting_offsets"].get(query["id"], "0"))
    raise ValueError("reference_oracle_outside_support")


def append(case, query, reply):
    result = copy.deepcopy(case)
    q, e = F(query["time_s"]), F(query["error_m"])
    low, high = reply - e, reply + e
    old_index = next(
        (i for i, row in enumerate(result["observations"]) if F(row["time_s"]) == q),
        None,
    )
    merge = dict(
        query_id=query["id"],
        time_s=str(q),
        reported_interval_m=[str(low), str(high)],
        existing_observation_id=None,
        previous_interval_m=None,
        merged_interval_m=None,
    )
    if old_index is None:
        result["observations"].append(
            dict(
                id="measurement-" + query["id"],
                time_s=str(q),
                interval_m=[str(low), str(high)],
            )
        )
    else:
        record = result["observations"][old_index]
        merge["existing_observation_id"] = record["id"]
        merge["previous_interval_m"] = record["interval_m"][:]
        low = max(F(record["interval_m"][0]), low)
        high = min(F(record["interval_m"][1]), high)
        if low > high:
            return None, merge
        record["interval_m"] = [str(low), str(high)]
    result["observations"] = sorted(
        result["observations"], key=lambda r: F(r["time_s"])
    )
    merge["merged_interval_m"] = [str(low), str(high)]
    parse_case(result)
    return result, merge


def conventional(case, oracle):
    model = copy.deepcopy(case["model"])
    current = solve(model)
    initial = summary(current)
    trace, reveals, native_models = [], [], [copy.deepcopy(model)]
    status = "exhausted"
    for query in case["queries"]:
        if current["status"] != "unresolved":
            status = (
                "resolved"
                if current["status"] in ("supported", "contradicted")
                else current["status"]
            )
            break
        predicted = plan(model, query)
        item = dict(
            query_id=query["id"],
            before=summary(current),
            predicted=predicted,
            reported_value_m=None,
            merge=None,
            after=None,
        )
        if predicted["status"] != "response_set_computed":
            status = predicted["status"]
            trace.append(item)
            break
        reply = oracle_reply(oracle, query)
        reveals.append(query["id"])
        updated, merge = append(model, query, reply)
        if updated is None:
            current = dict(status="inconsistent_premises")
        else:
            model = updated
            native_models.append(copy.deepcopy(model))
            current = solve(model)
        item.update(reported_value_m=str(reply), merge=merge, after=summary(current))
        trace.append(item)
        if current["status"] != "unresolved":
            status = (
                "resolved"
                if current["status"] in ("supported", "contradicted")
                else current["status"]
            )
            break
    if not trace and current["status"] != "unresolved":
        status = (
            "resolved"
            if current["status"] in ("supported", "contradicted")
            else current["status"]
        )
    return dict(
        id=case["id"],
        initial=initial,
        final=summary(current),
        workflow_status=status,
        oracle_calls=len(reveals),
        revealed_query_ids=reveals,
        unexecuted_query_ids=[
            q["id"] for q in case["queries"] if q["id"] not in reveals
        ],
        steps=trace,
        evidence_kind="authored_conditional_mechanism",
        physical_status="unresolved",
    ), native_models


def validate_oracle_contract(case, oracle):
    _, _, _, k, _, points, missing = parse_case(case["model"])
    require(not missing, "oracle_contract_missing")
    knots = [tuple(map(F, row)) for row in oracle["knots"]]
    require(
        all(abs(b[1] - a[1]) <= k * (b[0] - a[0]) for a, b in zip(knots, knots[1:])),
        "oracle_rate_contract",
    )
    for t, lo, hi in points:
        value = oracle_reply(oracle, dict(time_s=str(t), id="unreported-prior"))
        require(lo <= value <= hi, "oracle_prior_observation")
    qmap = {q["id"]: q for q in case["queries"]}
    require(set(oracle["reporting_offsets"]) <= set(qmap), "oracle_report_ids")
    violates = any(
        abs(rational(offset)) > F(qmap[key]["error_m"])
        for key, offset in oracle["reporting_offsets"].items()
    )
    require(violates == oracle["fault_injected"], "oracle_fault_disclosure")


def verify_record(actual, expected):
    require(actual == expected, "complete_workflow_mismatch")


def main():
    parser = argparse.ArgumentParser()
    for arg in (
        "freeze-sha256",
        "sources",
        "results",
        "proofs",
        "output",
        "baseline",
        "timing",
    ):
        parser.add_argument("--" + arg, required=True)
    args = parser.parse_args()
    tick, cpu = time.perf_counter(), resource.getrusage(resource.RUSAGE_SELF)
    cases, oracles = bind(Path(__file__).parent, Path(args.sources), args.freeze_sha256)
    actual, proofs = load(args.results), load(args.proofs)
    prepared = time.perf_counter()
    expected, models = [], []
    for case in cases:
        oracle = oracles[case["oracle_id"]]
        validate_oracle_contract(case, oracle)
        result, contexts = conventional(case, oracle)
        expected.append(result)
        models.append(contexts)
    calculated = time.perf_counter()
    report = dict(
        document_id="reiyah.measurement-resolution.results",
        version="0.1.0",
        freeze_sha256=args.freeze_sha256,
        cases=expected,
        final_evidence_counts=dict(
            sorted(Counter(x["final"]["status"] for x in expected).items())
        ),
        workflow_counts=dict(
            sorted(Counter(x["workflow_status"] for x in expected).items())
        ),
        oracle_calls=sum(x["oracle_calls"] for x in expected),
        experiments=len(expected),
        evidence_kind="authored conditional mechanism experiments",
        physical_cases=0,
        physical_qualification="unresolved",
        independent_replication=False,
    )
    verify_record(actual, report)
    require(
        set(proofs) == {"document_id", "version", "freeze_sha256", "cases"}
        and proofs["document_id"] == "reiyah.measurement-resolution.proofs"
        and proofs["version"] == "0.1.0"
        and proofs["freeze_sha256"] == args.freeze_sha256,
        "proof_identity",
    )
    require(len(proofs["cases"]) == len(cases), "proof_allocation")
    native_checks = 0
    for experiment, proof, contexts in zip(cases, proofs["cases"], models):
        require(
            set(proof) == {"id", "stages"}
            and proof["id"] == experiment["id"]
            and len(proof["stages"]) == len(contexts),
            "proof_stage_membership",
        )
        for item, context in zip(proof["stages"], contexts):
            require(
                set(item) == {"model", "result"} and item["model"] == context,
                "proof_model_binding",
            )
            check_witness(context, item["result"])
            native_checks += 1
    partitions = sum(
        step["predicted"]["status"] == "response_set_computed"
        for row in expected
        for step in row["steps"]
    )
    check = dict(
        document_id="reiyah.measurement-resolution.check",
        version="0.1.0",
        status="passed",
        freeze_sha256=args.freeze_sha256,
        experiments=len(expected),
        complete_response_partitions_verified=partitions,
        native_model_witness_stages_verified=native_checks,
        actual_oracle_calls_each_arm=report["oracle_calls"],
        workflow_and_final_counts=report["workflow_counts"],
        false_acceptances=[],
        false_refusals=[],
        comparator="Independent calculation and protocol paths with shared strict parsing/custody, same author and identical authored evidence; no external replication or empirical value estimate.",
        physical_cases=0,
        physical_qualification="unresolved",
    )
    write_new(args.baseline, report)
    write_new(args.output, check)
    finish = resource.getrusage(resource.RUSAGE_SELF)
    write_new(
        args.timing,
        dict(
            arm="conventional_strict_polyhedron_projection",
            preparation_seconds=prepared - tick,
            calculation_seconds=calculated - prepared,
            process_through_check_and_output_seconds=time.perf_counter() - tick,
            cpu_seconds=finish.ru_utime + finish.ru_stime - cpu.ru_utime - cpu.ru_stime,
            logical_oracle_calls=report["oracle_calls"],
            all_oracle_records_loaded_for_preparation=len(oracles),
            scope="Nested process, includes native witness checking after conventional calculation; no full acquisition/engineering savings claim.",
        ),
    )
    print(check)


if __name__ == "__main__":
    main()
