"""Check actual saved conversion, endpoint proofs and complete tiny-world losses."""

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from fixtures import large_cases, refusal_cases, small_cases  # noqa: E402
from reference import classify, exhaustive, graph, rational, validate_certificate, wire  # noqa: E402
from tools.perception_decision import checker as old_checker, contract as old_contract  # noqa: E402
from tools.perception_revision import (
    audit,
    audit_checker,
    contract as revision,
    monotone_producer,
)  # noqa: E402

RULE = "reiyah.authored-independent-presence-to-deletions:0.1.0"


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(value):
    encoded = (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode()
        + b"\n"
    )
    return sha256(encoded).hexdigest()


def check_conversion(original, actual):
    old_contract.validate(original)
    require(original["evidence_kind"] == "synthetic", "research_scope")
    require(not original["model"]["clauses"], "model_clauses")
    expected = deepcopy(original)
    expected["artifact_id"] = "reiyah.perception-revision.input"
    source = digest(original)
    context = digest({"rule": RULE, "source_sha256": source})
    expected["reference_context_sha256"] = context
    expected["model"] = {"variables": [], "clauses": []}
    used = set()
    mapping, observations = [], []
    for anchor in expected["anchors"]:
        require(
            all(anchor[r]["state"] == "observed" for r in ("base", "additions")),
            "outputs_unavailable",
        )
        require(anchor["reference"]["state"] == "finite", "open_reference")
        require(
            all(not e["when"] for e in anchor["reference"]["edges"]), "conditional_edge"
        )
        anchor["output_a"] = anchor.pop("base")
        anchor["output_b"] = {
            "state": "observed",
            "value": deepcopy(anchor["output_a"]["value"])
            + anchor.pop("additions")["value"],
        }
        for obj in anchor["reference"]["objects"]:
            literals = obj["when"]
            require(
                not literals or (len(literals) == 1 and literals[0]["value"] is True),
                "object_condition",
            )
            variable = literals[0]["variable"] if literals else None
            if variable is not None:
                require(variable not in used, "shared_presence_variable")
                used.add(variable)
            else:
                evidence = digest(
                    {
                        "rule": RULE,
                        "source_sha256": source,
                        "anchor": anchor["id"],
                        "object": obj["id"],
                        "premise": "mandatory_in_original_model",
                    }
                )
                observations.append(
                    {
                        "anchor": anchor["id"],
                        "object": obj["id"],
                        "outcome": "present",
                        "evidence_sha256": evidence,
                    }
                )
            mapping.append(
                {"anchor": anchor["id"], "object": obj["id"], "variable": variable}
            )
            obj["when"] = []
    request = {
        "artifact_id": "reiyah.perception-revision.audit-request",
        "version": "0.1.0",
        "comparison_id": original["comparison_id"],
        "reference_context_sha256": context,
        "family": "reference_deletions",
        "deletion_budget": len(used),
        "observation_basis": "hypothetical",
        "observations": observations,
    }
    full = {
        "rule": RULE,
        "source_sha256": source,
        "mapping": mapping,
        "dropped_unused_variables": [
            v for v in original["model"]["variables"] if v not in used
        ],
        "case": expected,
        "request": request,
        "scope": "authored_model_premises_only_no_new_observations",
    }
    require(actual == full, "conversion_identity")
    revision.validate(actual["case"])
    revision.validate_request(actual["case"], actual["request"])


def check_conventional(original, actual):
    require(
        set(actual) == {"bounds", "decision", "endpoints", "method"},
        "conventional_fields",
    )
    require(
        actual["method"] == "scipy_assignment_with_matching_cover_checks",
        "conventional_method",
    )
    require(len(actual["endpoints"]) == 2, "conventional_endpoints")
    fn, fp = (
        rational(original["loss"][k]) for k in ("false_negative", "false_positive")
    )
    values = []
    for bit, endpoint in zip((False, True), actual["endpoints"]):
        require(
            set(endpoint) == {"all_variables", "anchors"}
            and endpoint["all_variables"] is bit,
            "endpoint_identity",
        )
        require(len(endpoint["anchors"]) == len(original["anchors"]), "endpoint_cohort")
        env = {v: bit for v in original["model"]["variables"]}
        total = rational({"numerator": "0", "denominator": "1"})
        for source, row in zip(original["anchors"], endpoint["anchors"]):
            require(
                set(row) == {"anchor", "base", "augmented"}
                and row["anchor"] == source["id"],
                "endpoint_anchor",
            )
            objects, edges = graph(source, env)
            aa = [d["id"] for d in source["base"]["value"]]
            bb = aa + [d["id"] for d in source["additions"]["value"]]
            ca = validate_certificate(
                aa, {(d, o) for d, o in edges if d in aa}, row["base"]
            )
            cb = validate_certificate(bb, edges, row["augmented"])
            loss_a = fn * (len(objects) - ca) + fp * (len(aa) - ca)
            loss_b = fn * (len(objects) - cb) + fp * (len(bb) - cb)
            total += rational(source["weight"]) * (loss_a - loss_b)
        values.append(total)
    require(values[0] <= values[1], "endpoint_order")
    expected = {"lower": wire(values[0]), "upper": wire(values[1])}
    require(actual["bounds"] == expected, "conventional_bounds")
    require(
        actual["decision"]
        == classify(*values, rational(original["loss"]["tolerance"])),
        "conventional_decision",
    )
    return values


def check_case(original, row, tiny):
    require(
        set(row)
        == {
            "id",
            "input_sha256",
            "conversion",
            "engine",
            "legacy",
            "conventional",
            "seconds",
        },
        "row_fields",
    )
    require(
        row["id"] == original["comparison_id"]
        and row["input_sha256"] == digest(original),
        "input_identity",
    )
    check_conversion(original, row["conversion"])
    converted = row["conversion"]
    payload = row["engine"]["payload"]
    require(set(row["engine"]) == {"payload", "mapped_decision"}, "engine_fields")
    require(
        audit_checker.check(converted["case"], converted["request"], payload)
        == payload["result"],
        "engine_packet",
    )
    bounds = payload["result"]["bounds"]
    require(
        bounds is not None
        and payload["result"]["enclosure_kind"] == "exact_for_finite_error_family",
        "exact_bounds_unavailable",
    )
    require(payload["result"]["observation_basis"] == "hypothetical", "claim_scope")
    values = check_conventional(original, row["conventional"])
    require(bounds == row["conventional"]["bounds"], "arm_disagreement")
    require(
        row["engine"]["mapped_decision"] == row["conventional"]["decision"],
        "mapped_decision",
    )
    require(
        old_checker.check(original, row["legacy"]) == row["legacy"]["result"],
        "legacy_packet",
    )
    worlds = 0
    if tiny:
        truth = exhaustive(original)
        worlds = len(truth)
        require(values == [min(truth), max(truth)], "finite_truth")
        require(row["legacy"]["result"]["bounds"] == bounds, "legacy_finite_agreement")
    return worlds


def mutations(record):
    controls = []
    original = list(small_cases())[-1]
    row = record["cases"][511]
    cases = []

    def add(name, change):
        forged = deepcopy(row)
        change(forged)
        cases.append((name, forged))

    add("source_binding", lambda x: x.update(input_sha256="f" * 64))
    add(
        "mapping_variable",
        lambda x: x["conversion"]["mapping"][0].update(variable="invented"),
    )
    add(
        "converted_context",
        lambda x: x["conversion"]["case"].update(reference_context_sha256="e" * 64),
    )
    add(
        "request_context",
        lambda x: x["conversion"]["request"].update(reference_context_sha256="e" * 64),
    )
    add(
        "invented_external_observation",
        lambda x: x["conversion"]["request"].update(
            observation_basis="supplied_external_records"
        ),
    )
    add(
        "removed_mandatory_premise",
        lambda x: x["conversion"]["request"]["observations"].pop(),
    )
    add("wrong_budget", lambda x: x["conversion"]["request"].update(deletion_budget=1))
    add(
        "engine_matching",
        lambda x: x["engine"]["payload"]["proof"]["worlds"][0]["upper"][0]["output_b"][
            "matching"
        ].pop(),
    )
    add(
        "conventional_matching",
        lambda x: x["conventional"]["endpoints"][0]["anchors"][0]["augmented"][
            "matching"
        ].pop(),
    )
    add(
        "converted_bound",
        lambda x: x["engine"]["payload"]["result"]["bounds"].update(
            lower=wire(rational({"numerator": "99", "denominator": "1"}))
        ),
    )
    for name, forged in cases:
        rejected = False
        try:
            check_case(original, forged, True)
        except (ValueError, AssertionError, old_contract.Invalid):
            rejected = True
        require(rejected, "mutation_accepted:" + name)
        controls.append({"id": name, "rejected": True})
    competition = large_cases()[2]
    forged = deepcopy(record["cases"][514])
    forged["engine"]["mapped_decision"] = {
        "improvement_criterion": "excluded",
        "preference": "prefer_base",
    }
    rejected = False
    try:
        check_case(competition, forged, False)
    except (ValueError, AssertionError, old_contract.Invalid):
        rejected = True
    require(rejected, "insufficient_misread_as_worse")
    controls.append({"id": "insufficient_misread_as_worse", "rejected": True})
    for name, key, value in [
        ("empirical_promotion", "empirical_cases", 1),
        ("novel_solver_claim", "novel_solver", True),
        ("advantage_claim", "comparative_advantage", "established"),
        ("independent_authorship_claim", "independent_authorship", True),
    ]:
        forged = deepcopy(record)
        forged[key] = value
        rejected = False
        try:
            verify(forged)
        except ValueError:
            rejected = True
        require(rejected, "mutation_accepted:" + name)
        controls.append({"id": name, "rejected": True})
    forged = deepcopy(record)
    forged["cases"].pop()
    rejected = False
    try:
        verify(forged)
    except ValueError:
        rejected = True
    require(rejected, "missing_case")
    controls.append({"id": "missing_case", "rejected": True})
    return controls


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    args = parser.parse_args()
    target = Path(args.output)
    require(not target.exists(), "output_exists")
    record = json.loads(Path(args.input).read_text())
    with (
        patch.object(
            audit, "world_proposal", side_effect=AssertionError("producer disabled")
        ),
        patch.object(
            monotone_producer,
            "propose",
            side_effect=AssertionError("producer disabled"),
        ),
    ):
        worlds = verify(record)
        controls = mutations(record)
    result = {
        "document_id": "reiyah.presence-endpoints.check",
        "version": "0.1.0",
        "status": "passed",
        "small_cases": 512,
        "original_worlds": worlds,
        "large_cases": 6,
        "guard_controls": len(record["guard_controls"]),
        "saved_result_mutations": controls,
        "engine_producers_disabled": True,
        "independent_authorship": False,
        "claim_scope": "Authored representation-compatibility study; existing solver reused; no new observations.",
    }
    with target.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result))


def verify(record):
    require(
        record["document_id"] == "reiyah.presence-endpoints.execution"
        and record["version"] == "0.1.0",
        "record_identity",
    )
    require(record["status"] == "executed_check_pending", "execution_status")
    require(
        record["actual_new_observations"] == 0
        and record["empirical_cases"] == 0
        and record["production_code_changed"] is False
        and record["novel_solver"] is False
        and record["comparative_advantage"] == "not_established"
        and record["independent_authorship"] is False,
        "claim_scope",
    )
    originals = list(small_cases()) + large_cases()
    require(len(record["cases"]) == len(originals) == 518, "case_cohort")
    worlds = 0
    for i, (original, row) in enumerate(zip(originals, record["cases"])):
        worlds += check_case(original, row, i < 512)
    expected = [
        {"id": name, "expected": code, "observed": code, "passed": True}
        for name, code, _ in refusal_cases()
    ]
    require(record["guard_controls"] == expected, "guard_controls")
    require(worlds == 1728, "world_cohort")
    return worlds


if __name__ == "__main__":
    main()
