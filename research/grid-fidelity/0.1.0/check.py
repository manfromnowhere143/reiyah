"""Separate protocol replay. Does not invoke the producing workflow or oracle."""

import argparse
from fractions import Fraction
from pathlib import Path

import conventional
from adapter import all_cases
from binding import verify
from common import exact, keys, load, parse, require, witness_error, write_new


def source_check(source_root):
    if source_root is None:
        return dict(source_packets_checked=0, selected_values_checked=0)
    root = Path(source_root)
    data = (root / "ncom-sample-tail.bin").read_bytes()
    decoded = load(root / "decoded-01.json")
    rows = decoded["rows"]
    require(len(data) == 72000 and len(rows) == 1000, "source_population")
    for i in range(1000):
        packet = data[72 * i : 72 * (i + 1)]
        require(packet[0] == 231 and packet[21] == 4, "source_packet_mode")
        for end in (22, 61, 71):
            require(sum(packet[1:end]) % 256 == packet[end], "source_checksum")
    minute = int.from_bytes(data[63:67], "little", signed=True)
    require(data[62] == 0 and minute >= 1000, "preceding_minute_anchor")
    initial = int.from_bytes(data[73:75], "little")
    for index in range(1, 102):
        packet = data[72 * index : 72 * (index + 1)]
        ms = int.from_bytes(packet[1:3], "little")
        unsigned = packet[43] + 256 * packet[44] + 65536 * packet[45]
        value = unsigned - (16777216 if unsigned >= 8388608 else 0)
        require(
            value != -8388608 and ms == initial + (index - 1) * 10 and ms < 60000,
            "selected_encoding_clock",
        )
        row = rows[index]
        require(
            row["index"] == index
            and row["byte_offset"] == 72 * index
            and row["north_velocity_units"] == value
            and row["time_ms"] == minute * 60000 + ms,
            "selected_decoded_binding",
        )
        if packet[62] == 0:
            reported = int.from_bytes(packet[63:67], "little", signed=True)
            require(reported == minute, "selected_minute_change")
    return dict(source_packets_checked=1000, selected_values_checked=101)


def baseline_check(raw, model):
    # Separately reconstruct every baseline ordinate directly from raw anchors.
    samples = {x["index"]: Fraction(x["value_mps"]) for x in raw["observations"]}
    for i, t in enumerate(raw["native_times_s"]):
        a, b = next(
            (a, b)
            for a, b in zip(raw["coarse_indices"], raw["coarse_indices"][1:])
            if a <= i <= b
        )
        ta, tb, ti = (Fraction(raw["native_times_s"][j]) for j in (a, b, i))
        expected = ((tb - ti) * samples[a] + (ti - ta) * samples[b]) / (tb - ta)
        require(expected == model.baseline[i], "baseline_reconstruction")


def check_case(case, result, proof, arm):
    model = parse(case["model"])
    baseline_check(case["model"], model)
    keys(
        result,
        "id arm evidence_kind initial final workflow_status oracle_calls query_indices unqueried_indices records",
    )
    keys(proof, "id stages")
    require(
        result["id"] == proof["id"] == model.identifier
        and result["arm"] == arm
        and result["evidence_kind"] == case["evidence_kind"],
        "case_binding",
    )
    records, stages = result["records"], proof["stages"]
    require(
        type(records) is list
        and type(stages) is list
        and len(stages) == len(records) + 1,
        "stage_count",
    )
    known = dict(model.known)
    queries = []
    for step, stage in enumerate(stages):
        keys(stage, "step known_indices decision witness")
        require(
            stage["step"] == step and stage["known_indices"] == sorted(known),
            "stage_identity",
        )
        decision, _ = conventional.evaluate(model, known)
        require(stage["decision"] == decision, "decision_bounds")
        witness = stage["witness"]
        if decision["status"] == "inconsistent_premises":
            require(witness is None, "inconsistent_witness")
        else:
            keys(witness, "minimum_integers maximum_integers")
            low, high = map(exact, decision["uniform_error_range_mps"])
            require(
                witness_error(model, known, witness["minimum_integers"]) == low,
                "minimum_witness",
            )
            require(
                witness_error(model, known, witness["maximum_integers"]) == high,
                "maximum_witness",
            )
        require(
            (result["initial"] if step == 0 else records[step - 1]["after"])
            == decision,
            "stage_link",
        )
        candidates = [
            i
            for i in range(len(model.times))
            if i not in known and model.available[i] == "available"
        ]
        if step == len(records):
            require(result["final"] == decision, "final_binding")
            expected = (
                decision["status"]
                if decision["status"] != "unresolved"
                else "acquisition_blocked"
                if len(known) < len(model.times)
                else "exhausted"
            )
            require(
                decision["status"] != "unresolved" or not candidates, "premature_stop"
            )
            require(result["workflow_status"] == expected, "workflow_status")
            break
        require(
            decision["status"] == "unresolved" and candidates,
            "unauthorized_acquisition",
        )
        record = records[step]
        keys(
            record,
            "step before predicted query_index source_index value_mps predicted_response_class after",
        )
        require(
            record["step"] == step and record["before"] == decision, "record_identity"
        )
        scores = conventional.priorities(model, known)
        query = sorted(candidates, key=lambda i: (-scores[i], i))[0]
        require(
            record["query_index"] == query
            and record["source_index"] == case["source_indices"][query],
            "query_protocol",
        )
        require(record["value_mps"] == case["oracle_values_mps"][query], "reply_source")
        prediction = conventional.responses(model, known, query)
        require(record["predicted"] == prediction, "complete_response_partition")
        value = Fraction(record["value_mps"])
        tick = value / model.quantum
        require(tick.denominator == 1, "reply_encoding")
        matching = [
            cell["status"]
            for cell in prediction["response_partition"]
            if cell["lower_integer"] <= tick <= cell["upper_integer"]
        ]
        require(len(matching) <= 1, "partition_overlap")
        label = matching[0] if matching else "outside_current_family"
        require(record["predicted_response_class"] == label, "response_class")
        expected_after = label if matching else "inconsistent_premises"
        require(record["after"]["status"] == expected_after, "response_recomputation")
        known[query] = value
        queries.append(query)
    require(
        result["oracle_calls"] == len(queries) and result["query_indices"] == queries,
        "query_accounting",
    )
    require(
        result["unqueried_indices"]
        == [i for i in range(len(model.times)) if i not in known],
        "remaining_information",
    )
    values = list(map(Fraction, case["oracle_values_mps"]))
    rate_ok = all(
        abs(b - a) <= model.rate * (t1 - t0)
        for a, b, t0, t1 in zip(values, values[1:], model.times, model.times[1:])
    )
    actual_error = max(abs(v - b) for v, b in zip(values, model.baseline))
    actual = (
        ("supported" if actual_error <= model.tolerance else "contradicted")
        if rate_ok
        else "inconsistent_premises"
    )
    if rate_ok and result["final"]["status"] in ("supported", "contradicted"):
        require(result["final"]["status"] == actual, "false_decision")
    return dict(
        id=model.identifier,
        evidence_kind=case["evidence_kind"],
        arm=arm,
        status=result["final"]["status"],
        workflow_status=result["workflow_status"],
        oracle_calls=len(queries),
        model_stages=len(stages),
        complete_response_partitions=len(records),
        actual_recorded_error_mps=str(actual_error),
        full_record_rate_premise="satisfied" if rate_ok else "violated",
        full_record_decision=actual,
    )


def check_outputs(cases, outputs, proofs, arm, freeze):
    keys(outputs, "document_id version arm freeze_sha256 results")
    keys(proofs, "document_id version arm freeze_sha256 proofs")
    require(
        outputs["document_id"] == "reiyah.grid-fidelity.workflow"
        and proofs["document_id"] == "reiyah.grid-fidelity.proofs",
        "output_identity",
    )
    require(
        outputs["version"] == proofs["version"] == "0.1.0"
        and outputs["arm"] == proofs["arm"] == arm
        and outputs["freeze_sha256"] == proofs["freeze_sha256"] == freeze,
        "output_binding",
    )
    require(
        len(outputs["results"]) == len(proofs["proofs"]) == len(cases), "case_count"
    )
    return [
        check_case(c, r, p, arm)
        for c, r, p in zip(cases, outputs["results"], proofs["proofs"])
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources")
    parser.add_argument("--reiyah", required=True)
    parser.add_argument("--reiyah-proofs", required=True)
    parser.add_argument("--conventional", required=True)
    parser.add_argument("--conventional-proofs", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    freeze = verify()
    cases = all_cases(args.sources)
    counts = source_check(args.sources)
    checked = []
    for arm in ("reiyah", "conventional"):
        checked.extend(
            check_outputs(
                cases,
                load(getattr(args, arm)),
                load(getattr(args, arm + "_proofs")),
                arm,
                freeze,
            )
        )
    write_new(
        args.output,
        dict(
            document_id="reiyah.grid-fidelity.check",
            version="0.1.0",
            freeze_sha256=freeze,
            status="passed",
            comparisons=checked,
            counts=counts,
            false_acceptances=[],
            false_refusals=[],
            physical_cases=0,
            physical_qualification="unresolved",
            independent_replication=False,
            scope="Development only. Independent protocol replay uses conventional solver; tiny exhaustive enumeration separately tests both algorithms. Shared author, parser and contract.",
        ),
    )
    print(
        dict(
            status="passed",
            case_arm_executions=len(checked),
            model_stages=sum(r["model_stages"] for r in checked),
            complete_response_partitions=sum(
                r["complete_response_partitions"] for r in checked
            ),
            **counts,
        )
    )


if __name__ == "__main__":
    main()
