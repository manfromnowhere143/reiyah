"""Finite, conditional observation-resolvability control; standard library only.

The supplied supports and acceptable decisions are premises, not physical evidence.
This is an offline research calculation, not an observation selector.
"""
import argparse
import hashlib
import json
from pathlib import Path

MODEL = "declared_complete_finite_read_only_joint_outcomes"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def keys(value, expected):
    require(type(value) is dict and set(value) == set(expected), "PROPERTIES")


def names(value, maximum, empty=False):
    require(type(value) is list and (empty or bool(value)) and len(value) <= maximum,
            "MEMBERSHIP_SIZE")
    require(all(type(x) is str and 0 < len(x) <= 80 for x in value), "SYMBOL_TYPE")
    require(len(set(value)) == len(value), "DUPLICATE_SYMBOL")


def validate_case(case):
    keys(case, ("id", "decision_ids", "query_ids", "worlds"))
    names([case["id"]], 1)
    names(case["decision_ids"], 16)
    names(case["query_ids"], 8, empty=True)
    worlds = case["worlds"]
    require(type(worlds) is list and 0 < len(worlds) <= 32, "WORLD_COUNT")
    ids = []
    rows = 0
    for w in worlds:
        keys(w, ("id", "acceptable_decisions", "outcome_vectors"))
        ids.append(w["id"])
        names(w["acceptable_decisions"], 16)
        require(set(w["acceptable_decisions"]) <= set(case["decision_ids"]), "DECISION_ID")
        support = w["outcome_vectors"]
        require(type(support) is list and 0 < len(support) <= 256, "SUPPORT_COUNT")
        for vector in support:
            require(type(vector) is list and len(vector) == len(case["query_ids"]),
                    "VECTOR_LENGTH")
            require(all(type(x) is str and 0 < len(x) <= 80 for x in vector), "OUTCOME_TYPE")
        require(len({tuple(v) for v in support}) == len(support), "DUPLICATE_VECTOR")
        rows += len(support)
    names(ids, 32)
    require(rows <= 2048, "ROW_BUDGET")


def validate(packet):
    keys(packet, ("artifact_id", "version", "observation_model", "cases"))
    require(packet["artifact_id"] == "reiyah.resolution-identifiability.cases"
            and packet["version"] == "0.1.0", "IDENTITY")
    require(packet["observation_model"] == MODEL, "OBSERVATION_MODEL_UNSUPPORTED")
    require(type(packet["cases"]) is list and 0 < len(packet["cases"]) <= 64, "CASE_COUNT")
    for case in packet["cases"]:
        validate_case(case)
    names([case["id"] for case in packet["cases"]], 64)


def intersection(worlds, decisions):
    common = set(decisions)
    for world in worlds:
        common.intersection_update(world["acceptable_decisions"])
    return sorted(common)


def analyze(case):
    validate_case(case)
    worlds = {w["id"]: w for w in case["worlds"]}
    cells = {}
    for w in case["worlds"]:
        for vector in w["outcome_vectors"]:
            cells.setdefault(tuple(vector), []).append(w["id"])
    output = []
    for vector, ids in sorted(cells.items()):
        ids = sorted(ids)
        common = intersection([worlds[i] for i in ids], case["decision_ids"])
        core = []
        if not common:
            core = ids[:]
            for i in ids:
                reduced = [j for j in core if j != i]
                if not intersection([worlds[j] for j in reduced], case["decision_ids"]):
                    core = reduced
        output.append({"outcomes": list(vector), "compatible_world_ids": ids,
                       "acceptable_decisions": common, "obstruction_world_ids": core})
    initial = intersection(case["worlds"], case["decision_ids"])
    state = ("decision_already_justified" if initial else
             "not_guaranteed_resolvable" if any(not c["acceptable_decisions"] for c in output)
             else "resolvable_with_declared_observations")
    return {"case_id": case["id"], "state": state,
            "initial_acceptable_decisions": initial, "cells": output}


def reject_duplicates(pairs):
    obj = {}
    for key, value in pairs:
        require(key not in obj, "DUPLICATE_PROPERTY")
        obj[key] = value
    return obj


def load(path):
    raw = Path(path).read_bytes()
    require(len(raw) <= 2 * 1024 * 1024, "INPUT_BYTES")
    return raw, json.loads(raw, object_pairs_hook=reject_duplicates)


def produce(raw, packet):
    validate(packet)
    return {"artifact_id": "reiyah.resolution-identifiability.result", "version": "0.1.0",
            "lifecycle_status": "exploratory", "input_sha256": hashlib.sha256(raw).hexdigest(),
            "physical_channel_qualified": False,
            "cases": [analyze(c) for c in packet["cases"]]}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cases", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    raw, packet = load(args.cases)
    result = produce(raw, packet)
    with args.output.open("x") as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
