"""Separate adaptive-tree and terminal-cell checker; imports no producer code."""
import argparse
from functools import lru_cache
import hashlib
from itertools import product
import json
from pathlib import Path


def check(ok, why):
    if not ok:
        raise ValueError(why)


def parse(raw):
    check(len(raw) <= 2 * 1024 * 1024, "INPUT_BYTES")

    def pairs(items):
        out = {}
        for key, value in items:
            check(key not in out, "DUPLICATE_PROPERTY")
            out[key] = value
        return out

    return json.loads(raw, object_pairs_hook=pairs)


def input_contract(packet):
    """Validate premises independently before taking intersections, including empty sets."""
    def fields(obj, names):
        check(type(obj) is dict and set(obj) == set(names), "INPUT_PROPERTIES")

    def symbols(values, limit, allow_empty=False):
        check(type(values) is list and len(values) <= limit and (allow_empty or bool(values)),
              "INPUT_MEMBERSHIP")
        check(all(type(v) is str and 0 < len(v) <= 80 for v in values), "INPUT_SYMBOL")
        check(len(set(values)) == len(values), "INPUT_DUPLICATE")

    fields(packet, ["artifact_id", "version", "observation_model", "cases"])
    check(packet["artifact_id"] == "reiyah.resolution-identifiability.cases"
          and packet["version"] == "0.1.0", "INPUT_IDENTITY")
    check(packet["observation_model"] == "declared_complete_finite_read_only_joint_outcomes",
          "INPUT_OBSERVATION_MODEL")
    check(type(packet["cases"]) is list and 0 < len(packet["cases"]) <= 64, "INPUT_CASES")
    for case in packet["cases"]:
        fields(case, ["id", "decision_ids", "query_ids", "worlds"])
        symbols([case["id"]], 1)
        symbols(case["decision_ids"], 16)
        symbols(case["query_ids"], 8, allow_empty=True)
        check(type(case["worlds"]) is list and 0 < len(case["worlds"]) <= 32, "INPUT_WORLDS")
        row_count = 0
        for w in case["worlds"]:
            fields(w, ["id", "acceptable_decisions", "outcome_vectors"])
            symbols(w["acceptable_decisions"], 16)
            check(all(d in case["decision_ids"] for d in w["acceptable_decisions"]), "INPUT_DECISION")
            support = w["outcome_vectors"]
            check(type(support) is list and 0 < len(support) <= 256, "INPUT_SUPPORT")
            for vector in support:
                check(type(vector) is list and len(vector) == len(case["query_ids"]), "INPUT_VECTOR")
                check(all(type(v) is str and 0 < len(v) <= 80 for v in vector), "INPUT_OUTCOME")
            check(len({tuple(v) for v in support}) == len(support), "INPUT_DUPLICATE_VECTOR")
            row_count += len(support)
        symbols([w["id"] for w in case["worlds"]], 32)
        check(row_count <= 2048, "INPUT_ROWS")
    symbols([c["id"] for c in packet["cases"]], 64)


def common(worlds, decision_ids):
    return sorted(d for d in decision_ids
                  if all(d in w["acceptable_decisions"] for w in worlds))


def tree_depth(case):
    """Enumerate policies via all remaining actions and every possible answer.

    None means no guaranteed decision tree. This diagnoses these finite controls;
    depths are counts of hypothetical actions, not measured human costs.
    """
    atoms = [(i, tuple(v)) for i, w in enumerate(case["worlds"])
             for v in w["outcome_vectors"]]

    @lru_cache(None)
    def visit(indices, remaining):
        check(visit.cache_info().misses <= 65536, "ORACLE_WORK_LIMIT")
        ids = {atoms[i][0] for i in indices}
        if common([case["worlds"][i] for i in ids], case["decision_ids"]):
            return 0
        feasible_depths = []
        for q in remaining:
            answers = sorted({atoms[i][1][q] for i in indices})
            children = [visit(tuple(i for i in indices if atoms[i][1][q] == answer),
                              tuple(a for a in remaining if a != q)) for answer in answers]
            if all(d is not None for d in children):
                feasible_depths.append(1 + max(children))
        return min(feasible_depths) if feasible_depths else None

    return visit(tuple(range(len(atoms))), tuple(range(len(case["query_ids"]))))


def verify(raw, packet, result):
    check(parse(raw) == packet, "PARSED_INPUT_MISMATCH")
    input_contract(packet)
    check(set(result) == {"artifact_id", "version", "lifecycle_status", "input_sha256",
                          "physical_channel_qualified", "cases"}, "RESULT_PROPERTIES")
    check(result["artifact_id"] == "reiyah.resolution-identifiability.result"
          and result["version"] == "0.1.0" and result["lifecycle_status"] == "exploratory",
          "RESULT_IDENTITY")
    check(result["input_sha256"] == hashlib.sha256(raw).hexdigest(), "INPUT_DIGEST")
    check(result["physical_channel_qualified"] is False, "PHYSICAL_QUALIFICATION")
    check(type(result["cases"]) is list and len(result["cases"]) == len(packet["cases"]),
          "CASE_MEMBERSHIP")
    reports = []
    for case, got in zip(packet["cases"], result["cases"]):
        check(set(got) == {"case_id", "state", "initial_acceptable_decisions", "cells"},
              "CASE_PROPERTIES")
        check(got["case_id"] == case["id"], "CASE_ID")
        depth = tree_depth(case)
        state = ("not_guaranteed_resolvable" if depth is None else
                 "decision_already_justified" if depth == 0 else
                 "resolvable_with_declared_observations")
        check(got["state"] == state, "TREE_STATE")
        check(got["initial_acceptable_decisions"] == common(case["worlds"], case["decision_ids"]),
              "INITIAL_DECISIONS")
        alphabets = [sorted({v[q] for w in case["worlds"] for v in w["outcome_vectors"]})
                     for q in range(len(case["query_ids"]))]
        candidates = 1
        for alphabet in alphabets:
            candidates *= len(alphabet)
        check(candidates <= 65536, "CELL_WORK_LIMIT")
        expected = []
        for vector in product(*alphabets):
            compatible = [w for w in case["worlds"] if list(vector) in w["outcome_vectors"]]
            if compatible:
                expected.append((vector, compatible))
        check(len(got["cells"]) == len(expected), "CELL_MEMBERSHIP")
        obstruction_sizes = []
        for cell, (vector, compatible) in zip(got["cells"], expected):
            check(set(cell) == {"outcomes", "compatible_world_ids", "acceptable_decisions",
                                "obstruction_world_ids"}, "CELL_PROPERTIES")
            check(cell["outcomes"] == list(vector), "CELL_VECTOR")
            check(cell["compatible_world_ids"] == sorted(w["id"] for w in compatible),
                  "WORLD_MEMBERSHIP")
            allowed = common(compatible, case["decision_ids"])
            check(cell["acceptable_decisions"] == allowed, "CELL_DECISIONS")
            ids = cell["obstruction_world_ids"]
            check(type(ids) is list and all(type(i) is str for i in ids)
                  and len(set(ids)) == len(ids), "WITNESS_TYPE")
            if allowed:
                check(ids == [], "SPURIOUS_OBSTRUCTION")
            else:
                check(bool(ids) and set(ids) <= {w["id"] for w in compatible}, "WITNESS_MEMBERSHIP")
                core = [w for w in compatible if w["id"] in ids]
                check(not common(core, case["decision_ids"]), "WITNESS_INTERSECTION")
                for w in core:
                    check(bool(common([x for x in core if x != w], case["decision_ids"])),
                          "WITNESS_REDUNDANT")
                obstruction_sizes.append(len(core))
        reports.append({"case_id": case["id"], "state": state,
                        "minimum_worst_case_action_count": depth,
                        "cells_verified": len(expected), "obstruction_sizes": obstruction_sizes})
    return {"artifact_id": "reiyah.resolution-identifiability.verification", "version": "0.1.0",
            "status": "pass", "scope": "Finite authored models; independent code paths, not scientific review",
            "cases": reports}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cases", type=Path, required=True)
    ap.add_argument("--result", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    raw = args.cases.read_bytes()
    report = verify(raw, parse(raw), parse(args.result.read_bytes()))
    with args.output.open("x") as stream:
        stream.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
