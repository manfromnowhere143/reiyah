"""Exhaustive authored models and required rejection controls; no real observations."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json
from pathlib import Path

import analyze
import verify


def run(cases_path, result_path):
    raw, packet = analyze.load(cases_path)
    result = json.loads(result_path.read_bytes())
    verify.verify(raw, packet, result)
    subsets = [[x for i, x in enumerate(("A", "B", "C")) if mask & (1 << i)]
               for mask in range(1, 8)]
    families = [("three_worlds_two_binary_queries_deterministic", ["q1", "q2"],
                 [[[a, b]] for a, b in product(("0", "1"), repeat=2)]),
                ("three_worlds_one_binary_query_set_valued", ["q1"],
                 [[["0"]], [["1"]], [["0"], ["1"]]])]
    reports = []
    for name, queries, supports in families:
        counts = {}
        digest = hashlib.sha256()
        count = 0
        for responses in product(supports, repeat=3):
            for decisions in product(subsets, repeat=3):
                case = {"id": "exhaustive", "decision_ids": ["A", "B", "C"],
                        "query_ids": queries, "worlds": [
                            {"id": str(i), "acceptable_decisions": decisions[i],
                             "outcome_vectors": responses[i]} for i in range(3)]}
                got = analyze.analyze(case)
                depth = verify.tree_depth(case)
                expected = ("not_guaranteed_resolvable" if depth is None else
                            "decision_already_justified" if depth == 0 else
                            "resolvable_with_declared_observations")
                if got["state"] != expected:
                    raise AssertionError((name, case, got, depth))
                # Verify every terminal membership, decision and obstruction too.
                one_packet = {k: v for k, v in packet.items() if k != "cases"}
                one_packet["cases"] = [case]
                case_raw = json.dumps(one_packet, sort_keys=True).encode()
                one = {"artifact_id": "reiyah.resolution-identifiability.result",
                       "version": "0.1.0", "lifecycle_status": "exploratory",
                       "input_sha256": hashlib.sha256(case_raw).hexdigest(),
                       "physical_channel_qualified": False, "cases": [got]}
                verify.verify(case_raw, one_packet, one)
                counts[expected] = counts.get(expected, 0) + 1
                count += 1
                digest.update(json.dumps([case, got, depth], sort_keys=True).encode() + b"\n")
        reports.append({"family": name, "models_checked": count,
                        "states": counts, "transcript_sha256": digest.hexdigest()})

    rejections = []

    def reject(name, expected, action):
        try:
            action()
        except ValueError as exc:
            if str(exc) != expected:
                raise AssertionError((name, "wrong rejection", str(exc), expected)) from exc
        else:
            raise AssertionError((name, "accepted"))
        rejections.append({"case": name, "reason": expected, "state": "rejected"})

    bad = deepcopy(packet); bad["cases"][0]["worlds"] = []
    reject("no_worlds", "WORLD_COUNT", lambda: analyze.validate(bad))
    bad = deepcopy(packet); bad["cases"][0]["worlds"][0]["outcome_vectors"] = []
    reject("empty_support", "SUPPORT_COUNT", lambda: analyze.validate(bad))
    bad = deepcopy(packet); bad["cases"][0]["worlds"][0]["outcome_vectors"] = [[]]
    reject("incomplete_vector", "VECTOR_LENGTH", lambda: analyze.validate(bad))
    bad = deepcopy(packet); bad["cases"][0]["worlds"][0]["acceptable_decisions"] = ["invented"]
    reject("unknown_decision", "DECISION_ID", lambda: analyze.validate(bad))
    bad = deepcopy(packet); bad["cases"][0]["surprise"] = True
    reject("unknown_property", "PROPERTIES", lambda: analyze.validate(bad))
    bad = deepcopy(packet); bad["cases"][0]["worlds"][1]["id"] = "original"
    reject("duplicate_world", "DUPLICATE_SYMBOL", lambda: analyze.validate(bad))
    bad = deepcopy(packet); bad["observation_model"] = "assumed_independent_marginals"
    reject("unsupported_model", "OBSERVATION_MODEL_UNSUPPORTED", lambda: analyze.validate(bad))
    bad = deepcopy(packet); bad["cases"][0]["worlds"][0]["outcome_vectors"][0][0] = None
    reject("null_coercion", "OUTCOME_TYPE", lambda: analyze.validate(bad))
    bad = deepcopy(packet); bad["cases"][0]["worlds"][0]["acceptable_decisions"] = []
    reject("empty_acceptable_decisions", "MEMBERSHIP_SIZE", lambda: analyze.validate(bad))
    reject("duplicate_property", "DUPLICATE_PROPERTY",
           lambda: json.loads('{"id": "a", "id": "b"}', object_pairs_hook=analyze.reject_duplicates))

    bad = deepcopy(result); bad["cases"][0]["state"] = "resolvable_with_declared_observations"
    reject("forged_state", "TREE_STATE", lambda: verify.verify(raw, packet, bad))
    bad = deepcopy(result); bad["cases"][0]["cells"][0]["obstruction_world_ids"] = ["invented"]
    reject("invented_witness", "WITNESS_MEMBERSHIP", lambda: verify.verify(raw, packet, bad))
    bad = deepcopy(result); bad["cases"][0]["cells"][0]["compatible_world_ids"].pop()
    reject("deleted_compatible_world", "WORLD_MEMBERSHIP", lambda: verify.verify(raw, packet, bad))
    bad = deepcopy(result); bad["cases"][0]["cells"][0]["acceptable_decisions"] = ["A"]
    reject("invented_safe_decision", "CELL_DECISIONS", lambda: verify.verify(raw, packet, bad))
    bad = deepcopy(result); bad["cases"][0]["cells"] = []
    reject("missing_cell", "CELL_MEMBERSHIP", lambda: verify.verify(raw, packet, bad))
    bad = deepcopy(result); bad["input_sha256"] = "0" * 64
    reject("changed_input_digest", "INPUT_DIGEST", lambda: verify.verify(raw, packet, bad))
    bad = deepcopy(result); bad["physical_channel_qualified"] = True
    reject("fabricated_physical_qualification", "PHYSICAL_QUALIFICATION",
           lambda: verify.verify(raw, packet, bad))
    bad = deepcopy(result); bad["cases"][5]["cells"][0]["obstruction_world_ids"].pop()
    reject("pair_in_place_of_triple_obstruction", "WITNESS_INTERSECTION",
           lambda: verify.verify(raw, packet, bad))
    altered = deepcopy(packet)
    third = deepcopy(altered["cases"][0]["worlds"][0]); third["id"] = "duplicate_information"
    altered["cases"][0]["worlds"].append(third)
    altered_raw = json.dumps(altered, sort_keys=True).encode()
    bad = analyze.produce(altered_raw, altered)
    bad["cases"][0]["cells"][0]["obstruction_world_ids"] = sorted(
        w["id"] for w in altered["cases"][0]["worlds"])
    reject("redundant_obstruction", "WITNESS_REDUNDANT",
           lambda: verify.verify(altered_raw, altered, bad))

    invalid_inputs = []
    malformed = deepcopy(packet); malformed["cases"][0]["worlds"] = []
    invalid_inputs.append(("checker_no_worlds", "INPUT_WORLDS", malformed))
    malformed = deepcopy(packet); malformed["cases"][0]["worlds"][0]["outcome_vectors"] = []
    invalid_inputs.append(("checker_empty_support", "INPUT_SUPPORT", malformed))
    malformed = deepcopy(packet); malformed["cases"][0]["worlds"][0]["outcome_vectors"] = [[]]
    invalid_inputs.append(("checker_incomplete_vector", "INPUT_VECTOR", malformed))
    malformed = deepcopy(packet); malformed["cases"][0]["worlds"][0]["acceptable_decisions"] = ["X"]
    invalid_inputs.append(("checker_unknown_decision", "INPUT_DECISION", malformed))
    malformed = deepcopy(packet); malformed["cases"][0]["worlds"][1]["id"] = "original"
    invalid_inputs.append(("checker_duplicate_world", "INPUT_DUPLICATE", malformed))
    malformed = deepcopy(packet); malformed["observation_model"] = "independent_marginals"
    invalid_inputs.append(("checker_wrong_model", "INPUT_OBSERVATION_MODEL", malformed))
    malformed = deepcopy(packet); malformed["cases"][0]["worlds"][0]["outcome_vectors"][0][0] = None
    invalid_inputs.append(("checker_null_response", "INPUT_OUTCOME", malformed))
    for name, expected, malformed in invalid_inputs:
        malformed_raw = json.dumps(malformed, sort_keys=True).encode()
        reject(name, expected, lambda: verify.verify(malformed_raw, malformed, result))
    reject("checker_duplicate_property", "DUPLICATE_PROPERTY",
           lambda: verify.parse(b'{"id":"a","id":"b"}'))
    reject("checker_raw_object_mismatch", "PARSED_INPUT_MISMATCH",
           lambda: verify.verify(raw, altered, result))

    joint = deepcopy(packet["cases"][2])
    for w in joint["worlds"]:
        w["outcome_vectors"] = [list(v) for v in product(("0", "1"), repeat=2)]
    original = analyze.analyze(packet["cases"][2])["state"]
    product_model = analyze.analyze(joint)["state"]
    assert original == "resolvable_with_declared_observations"
    assert product_model == "not_guaranteed_resolvable"
    return {"artifact_id": "reiyah.resolution-identifiability.challenge", "version": "0.1.0",
            "status": "pass", "exhaustive_families": reports,
            "total_models_checked": sum(r["models_checked"] for r in reports),
            "rejections": rejections, "rejection_count": len(rejections),
            "correlation_control": {"joint_support": original, "product_of_marginals": product_model,
                                    "interpretation": "The larger product support is conservative, but cannot prove actual impossibility for the smaller joint model."},
            "scope": "Dependent authored finite models, not empirical trials, error rates or measured savings"}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cases", type=Path, required=True)
    ap.add_argument("--result", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    report = run(args.cases, args.result)
    with args.output.open("x") as stream:
        stream.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
