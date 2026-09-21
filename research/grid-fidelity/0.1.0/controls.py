"""Finite-world truth checks, strict refusals and actual-output mutations."""

import argparse
import copy
import itertools

import conventional
import native
from adapter import all_cases, validate_case
from binding import verify
from cases import authored, case
from check import baseline_check, check_outputs
from common import (
    Invalid,
    exact,
    load,
    parse,
    require,
    unique,
    witness_error,
    write_new,
)
from workflow import Oracle, run


def rejected(function, reason):
    try:
        function()
    except Invalid as exc:
        require(str(exc) == reason, "wrong_refusal:" + str(exc) + ":" + reason)
    else:
        raise AssertionError("accepted:" + reason)


def finite_truth(raw):
    model = parse(raw)
    baseline_check(raw, model)
    worlds = []
    for z in itertools.product(
        range(model.minimum_integer, model.maximum_integer + 1), repeat=len(model.times)
    ):
        values = [model.quantum * v for v in z]
        if any(values[i] != v for i, v in model.known.items()):
            continue
        if any(
            abs(values[i + 1] - values[i])
            > model.rate * (model.times[i + 1] - model.times[i])
            for i in range(len(values) - 1)
        ):
            continue
        error = max(abs(v - b) for v, b in zip(values, model.baseline))
        worlds.append((z, error))
    partitions = 0
    for engine in (native, conventional):
        result, witness = engine.evaluate(model, model.known)
        if not worlds:
            require(
                result
                == dict(status="inconsistent_premises", uniform_error_range_mps=None)
                and witness is None,
                "enumerated_inconsistency",
            )
            continue
        low, high = min(e for _, e in worlds), max(e for _, e in worlds)
        label = (
            "supported"
            if high <= model.tolerance
            else "contradicted"
            if low > model.tolerance
            else "unresolved"
        )
        require(
            result == dict(status=label, uniform_error_range_mps=[str(low), str(high)]),
            "enumerated_bounds",
        )
        require(
            witness_error(model, model.known, witness["minimum_integers"]) == low,
            "enumerated_minimum_witness",
        )
        require(
            witness_error(model, model.known, witness["maximum_integers"]) == high,
            "enumerated_maximum_witness",
        )
        scores = engine.priorities(model, model.known)
        expected_scores = [
            max(abs(model.quantum * z[i] - model.baseline[i]) for z, _ in worlds)
            for i in range(len(model.times))
        ]
        require(scores == expected_scores, "enumerated_priority")
        for query in range(len(model.times)):
            if query in model.known:
                continue
            cells = []
            replies = sorted({z[query] for z, _ in worlds})
            for reply in replies:
                errors = [e for z, e in worlds if z[query] == reply]
                status = (
                    "supported"
                    if max(errors) <= model.tolerance
                    else "contradicted"
                    if min(errors) > model.tolerance
                    else "unresolved"
                )
                if (
                    cells
                    and cells[-1]["status"] == status
                    and cells[-1]["upper_integer"] == reply - 1
                ):
                    cells[-1]["upper_integer"] = reply
                else:
                    cells.append(
                        dict(lower_integer=reply, upper_integer=reply, status=status)
                    )
            expected = dict(
                status="response_set_computed",
                quantum_mps=str(model.quantum),
                feasible_integer_responses=[replies[0], replies[-1]],
                response_partition=cells,
                possible_statuses=sorted({c["status"] for c in cells}),
                guaranteed_resolution=all(c["status"] != "unresolved" for c in cells),
            )
            require(
                engine.responses(model, model.known, query) == expected,
                "enumerated_complete_partition",
            )
            partitions += 1
    return len(worlds), partitions


def pre():
    contracts = worlds = partitions = 0
    for times in ([0, 1, 2], [0, "3/5", "9/5", "14/5"]):
        for first, last, rate, tol in itertools.product(
            (-1, 0, 1), (-1, 0, 1), (0, 1, 2), ("0", "1/2", "1")
        ):
            n = len(times)
            raw = case(
                "tiny",
                times,
                [first] + [0] * (n - 2) + [last],
                [0, n - 1],
                rate,
                tol,
                quantum="1",
                limits=(-2, 2),
            )["model"]
            w, p = finite_truth(raw)
            contracts += 1
            worlds += w
            partitions += p
    # Interior observation, rational quantum and asymmetric finite domain.
    for middle in ("-1/2", "0", "1/2"):
        raw = case(
            "tiny-pinned",
            [0, 1, 2, 3],
            [0, middle, 0, "1/2"],
            [0, 3],
            1,
            "1/3",
            quantum="1/2",
            limits=(-1, 2),
        )["model"]
        raw["observations"].append(dict(index=1, value_mps=middle))
        w, p = finite_truth(raw)
        contracts += 1
        worlds += w
        partitions += p
    refusals = []
    good = authored()[2]
    mutations = [
        ("fields", lambda x: x["model"].update(unexpected=1)),
        ("native_order", lambda x: x["model"].update(native_times_s=["0", "0", "1"])),
        ("coarse_membership", lambda x: x["model"].update(coarse_indices=[False, 2])),
        (
            "observation_membership",
            lambda x: x["model"]["observations"].append(
                copy.deepcopy(x["model"]["observations"][0])
            ),
        ),
        ("coarse_anchor_missing", lambda x: x["model"]["observations"].pop()),
        ("nonnegative_contract", lambda x: x["model"].update(tolerance_mps="-1")),
        (
            "quantum_positive",
            lambda x: x["model"]["value_domain"].update(quantum_mps="0"),
        ),
        (
            "encoding_bounds",
            lambda x: x["model"]["value_domain"].update(minimum_integer=1001),
        ),
        (
            "unrepresentable_value",
            lambda x: x["model"]["observations"][0].update(value_mps="1/1000"),
        ),
        (
            "encoding_range",
            lambda x: x["model"]["observations"][0].update(value_mps="11"),
        ),
        (
            "availability",
            lambda x: x["model"]["availability"].__setitem__(1, "unknown"),
        ),
        ("rational_canonical", lambda x: x["model"].update(tolerance_mps="0.25")),
        (
            "unrepresentable_value",
            lambda x: x["oracle_values_mps"].__setitem__(1, "1/1000"),
        ),
        (
            "initial_source_binding",
            lambda x: x["oracle_values_mps"].__setitem__(0, "1"),
        ),
        ("oracle_source_mapping", lambda x: x["source_indices"].__setitem__(1, 0)),
    ]
    for reason, mutation in mutations:
        value = copy.deepcopy(good)
        mutation(value)
        rejected(lambda: validate_case(value), reason)
        refusals.append(reason)
    rejected(lambda: unique([("x", 1), ("x", 2)]), "duplicate_json_key")
    refusals.append("duplicate_json_key")
    rejected(lambda: exact("1/0"), "rational_syntax")
    refusals.append("rational_syntax")
    oracle = Oracle(good)
    oracle.acquire(1)
    rejected(lambda: oracle.acquire(1), "oracle_repeat")
    refusals.append("oracle_repeat")
    blocked = copy.deepcopy(good)
    blocked["model"]["availability"][1] = "unregistered"
    rejected(lambda: Oracle(blocked).acquire(1), "oracle_unobtainable")
    refusals.append("oracle_unobtainable")
    m = parse(blocked["model"])
    for engine in (native, conventional):
        rejected(lambda: engine.responses(m, m.known, 1), "query_unobtainable")
        rejected(lambda: engine.responses(m, m.known, 0), "query_membership")
    m = parse(good["model"])
    rejected(lambda: witness_error(m, m.known, [0, 100, 0]), "witness_rate")
    refusals.append("witness_rate")
    # Freeze a full workflow contract as a mutation target; expected final verdicts
    # are derived again by the separate checker, not filled in as constants.
    freeze = verify()
    rows = authored()
    for arm, engine in (("reiyah", native), ("conventional", conventional)):
        results = []
        proofs = []
        for row in rows:
            r, p = run(row, engine, arm)
            results.append(r)
            proofs.append(p)
        output = dict(
            document_id="reiyah.grid-fidelity.workflow",
            version="0.1.0",
            arm=arm,
            freeze_sha256=freeze,
            results=results,
        )
        proof = dict(
            document_id="reiyah.grid-fidelity.proofs",
            version="0.1.0",
            arm=arm,
            freeze_sha256=freeze,
            proofs=proofs,
        )
        check_outputs(rows, output, proof, arm, freeze)
    return dict(
        status="passed",
        finite_contracts=contracts,
        feasible_worlds_enumerated=worlds,
        complete_partitions_against_enumeration=partitions,
        refusal_checks=len(refusals) + 4,
        refusal_reasons=refusals,
        authored_workflow_executions=2 * len(rows),
    )


def post(source_root, outputs, proofs):
    freeze = verify()
    cases = all_cases(source_root)
    check_outputs(cases, outputs, proofs, "reiyah", freeze)
    target = next(
        i
        for i, x in enumerate(outputs["results"])
        if x["evidence_kind"] == "exposed_recorded_development" and x["records"]
    )

    def modify_result(out, key, value):
        out["results"][target][key] = value

    tests = [
        (
            "decision_bounds",
            lambda o, p: p["proofs"][target]["stages"][0]["decision"].update(
                uniform_error_range_mps=["0", "0"]
            ),
        ),
        (
            "maximum_witness",
            lambda o, p: p["proofs"][target]["stages"][0]["witness"].update(
                maximum_integers=p["proofs"][target]["stages"][0]["witness"][
                    "minimum_integers"
                ]
            ),
        ),
        (
            "complete_response_partition",
            lambda o, p: o["results"][target]["records"][0]["predicted"][
                "response_partition"
            ].pop(),
        ),
        (
            "complete_response_partition",
            lambda o, p: o["results"][target]["records"][0]["predicted"].update(
                guaranteed_resolution=not o["results"][target]["records"][0][
                    "predicted"
                ]["guaranteed_resolution"]
            ),
        ),
        (
            "query_protocol",
            lambda o, p: o["results"][target]["records"][0].update(source_index=999999),
        ),
        (
            "reply_source",
            lambda o, p: o["results"][target]["records"][0].update(value_mps="0"),
        ),
        (
            "response_class",
            lambda o, p: o["results"][target]["records"][0].update(
                predicted_response_class="supported"
            ),
        ),
        ("query_accounting", lambda o, p: modify_result(o, "oracle_calls", 0)),
        (
            "remaining_information",
            lambda o, p: modify_result(o, "unqueried_indices", []),
        ),
        ("case_count", lambda o, p: o["results"].pop()),
        ("fields", lambda o, p: o.update(physical_qualification="supported")),
        ("output_binding", lambda o, p: o.update(freeze_sha256="0" * 64)),
    ]
    passed = []
    for reason, mutation in tests:
        a, b = copy.deepcopy(outputs), copy.deepcopy(proofs)
        mutation(a, b)
        rejected(lambda: check_outputs(cases, a, b, "reiyah", freeze), reason)
        passed.append(reason)
    return dict(
        status="passed", actual_output_mutations=len(passed), expected_rejections=passed
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("pre", "post"))
    parser.add_argument("--sources")
    parser.add_argument("--results")
    parser.add_argument("--proofs")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    freeze = verify()
    result = (
        pre()
        if args.mode == "pre"
        else post(args.sources, load(args.results), load(args.proofs))
    )
    result.update(
        document_id="reiyah.grid-fidelity.controls",
        version="0.1.0",
        mode=args.mode,
        freeze_sha256=freeze,
    )
    write_new(args.output, result)
    print(result)


if __name__ == "__main__":
    main()
