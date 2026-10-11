"""Reconstruct every source row and enumerate all one-response-per-ID worlds.

Deliberately does not import the result producer, its matching, or its Hall check.
Identifiers and individual responses remain in the caller's private input/output.
"""
import argparse
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
from fractions import Fraction

SOURCE_SHA256 = "1eb5506f328316f46fa5a036486b05689f4d504602895b80c87ee8bda0e0dd1d"
NONE = "no_strict_majority"


def require(value, message):
    if not value:
        raise ValueError(message)


def exactly(left, right):
    """JSON count 0, false and 0.0 have distinct meanings and types."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(exactly(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(exactly(a, b) for a, b in zip(left, right))
    return left == right


def read_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    def nonfinite(value):
        raise ValueError("nonfinite JSON constant")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def majority(values):
    counts = Counter(values)
    most, number = counts.most_common(1)[0]
    return most if number > len(values) / 2 else NONE


def verify(data_path, rows_path, result_path):
    raw = data_path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == SOURCE_SHA256, "source hash mismatch")
    data = read_json(raw)
    rows = read_json(rows_path.read_bytes())
    indexed = {}
    for row in rows:
        require(type(row["object_index"]) is int, "invalid object index type")
        key = (row["image_name"], row["object_index"], row["procedure"])
        require(key not in indexed, "duplicate result row")
        indexed[key] = row
    expected_keys = set()
    world_count = 0
    max_worlds = 0
    bound_pairs = 0
    witnesses = 0
    observations = {"proposed": [], "no_proposal": []}
    for image_name, objects in data["objects"].items():
        for index, obj in enumerate(objects):
            for arm in ("proposed", "no_proposal"):
                key = (image_name, index, arm)
                expected_keys.add(key)
                require(key in indexed, "missing result row")
                row = indexed[key]
                grouped = {}
                votes = []
                if arm == "proposed":
                    source_entries = [(k, response) for k, records in obj["annotation_info"].items()
                                      for response in records]
                else:
                    source_entries = [(k, response) for record in obj["unbiased_annotation_info"]
                                      for k, response in record.items()]
                for identity, response in source_entries:
                    grouped.setdefault(identity, []).append(response["vote"])
                    votes.append(response["vote"])
                identities = sorted(grouped)
                supports = [sorted(set(grouped[k])) for k in identities]
                require(exactly(row["object_id"], obj["mo_id"]), "object join mismatch")
                require(row["reviewer_ids"] == identities, "reviewer membership mismatch")
                require(exactly(row["group_count"], len(supports)), "group count mismatch")
                require(exactly(row["raw_entry_count"], len(votes)), "raw count mismatch")
                require(row["raw_outcome"] == majority(votes), "raw outcome mismatch")
                require(exactly(row["repeated_id"], len(votes) > len(supports)), "repeat flag mismatch")
                require(exactly(row["conflicting_id"], any(len(s) > 1 for s in supports)), "conflict flag mismatch")
                # This finite sample is small enough for direct enumeration.
                total = 1
                for support in supports:
                    total *= len(support)
                require(total <= 65536, "enumeration budget exceeded; result unverified")
                world_count += total
                max_worlds = max(max_worlds, total)
                lows = {c: len(supports) + 1 for c in data["classes"]}
                highs = {c: -1 for c in data["classes"]}
                outcomes = set()
                for world in itertools.product(*supports):
                    counts = Counter(world)
                    outcomes.add(majority(world))
                    for label in data["classes"]:
                        lows[label] = min(lows[label], counts[label])
                        highs[label] = max(highs[label], counts[label])
                require(set(row["possible_outcomes"]) == outcomes, "attainable outcomes mismatch")
                observations[arm].append((votes, grouped, outcomes))
                require(len(row["possible_outcomes"]) == len(outcomes), "duplicate outcome")
                require(set(row["class_count_bounds"]) == set(data["classes"]), "class roster mismatch")
                for label in data["classes"]:
                    require(exactly(row["class_count_bounds"][label], {
                        "lower": lows[label], "upper": highs[label], "denominator": len(supports)}),
                        "sharp bound mismatch")
                    bound_pairs += 1
                require(set(row["outcome_witnesses"]) == outcomes, "witness coverage mismatch")
                for label, witness in row["outcome_witnesses"].items():
                    require(len(witness) == len(supports), "witness length mismatch")
                    require(all(value in support for value, support in zip(witness, supports)),
                            "witness outside support")
                    require(majority(witness) == label, "witness does not yield claimed outcome")
                    witnesses += 1
                obstruction = row["no_majority_obstruction"]
                if NONE in outcomes:
                    require(obstruction is None, "false obstruction")
                else:
                    require(isinstance(obstruction, dict), "missing obstruction")
                    labels = set(obstruction["classes"])
                    require(labels <= set(data["classes"]), "invalid obstruction classes")
                    forced = [i for i, support in enumerate(supports) if set(support) <= labels]
                    slots = len(labels) * (len(supports) // 2)
                    require(exactly(obstruction["forced_group_indices"], forced) and
                            exactly(obstruction["available_slots"], slots) and len(forced) > slots,
                            "invalid Hall obstruction")
    require(set(indexed) == expected_keys, "extra or missing result rows")
    require(len(expected_keys) == 2000, "full scope not verified")
    result = read_json(result_path.read_bytes())
    require(result["source_sha256"] == SOURCE_SHA256 and
            exactly(result["procedure_object_rows"], 2000) and
            exactly(result["object_records"], 1000) and exactly(result["image_groups"], 388),
            "aggregate scope mismatch")
    require(exactly(result["verification"], {
        "matching_Hall_agreements": len(expected_keys),
        "class_endpoint_witness_pairs_checked": bound_pairs}), "verification count mismatch")
    ordinary = set(data["classes"]) - {"cantsolve"}
    for arm, records in observations.items():
        observed = result["procedures"][arm]
        raw = [majority(votes) for votes, _, _ in records]
        possible = [outcomes for _, _, outcomes in records]
        pairs = Counter((r, label) for r, world_set in zip(raw, possible) for label in world_set)
        expected = {
            "objects": len(records),
            "raw_response_entries": sum(len(v) for v, _, _ in records),
            "distinct_ID_object_pairs": sum(len(g) for _, g, _ in records),
            "objects_with_repeated_ID": sum(len(v) > len(g) for v, g, _ in records),
            "objects_with_conflicting_responses_under_an_ID": sum(
                any(len(set(v)) > 1 for v in g.values()) for _, g, _ in records),
            "raw_outcome_invariant": sum(all(o == r for o in w) for r, w in zip(raw, possible)),
            "raw_outcome_not_invariant": sum(any(o != r for o in w) for r, w in zip(raw, possible)),
            "unique_normalized_outcome_different_from_raw": sum(len(w) == 1 and r not in w for r, w in zip(raw, possible)),
            "multiple_normalized_outcomes": sum(len(w) > 1 for w in possible),
            "raw_outcome_not_attainable": sum(r not in w for r, w in zip(raw, possible)),
            "raw_ordinary_majority_can_lose_majority": sum(r in ordinary and NONE in w for r, w in zip(raw, possible)),
            "raw_ordinary_majority_can_switch_ordinary_class": sum(r in ordinary and any(o in ordinary and o != r for o in w) for r, w in zip(raw, possible)),
            "raw_ordinary_majority_can_become_cantsolve": sum(r in ordinary and "cantsolve" in w for r, w in zip(raw, possible)),
            "raw_no_majority_can_gain_ordinary_majority": sum(r == NONE and any(o in ordinary for o in w) for r, w in zip(raw, possible)),
            "raw_cantsolve_can_change": sum(r == "cantsolve" and any(o != r for o in w) for r, w in zip(raw, possible)),
            "normalized_no_majority_possible": sum(NONE in w for w in possible),
            "no_majority_infeasible_with_Hall_obstruction": sum(NONE not in w for w in possible),
            "raw_outcome_counts": dict(Counter(raw)),
            "attainable_outcome_count_histogram": {str(n): count for n, count in Counter(map(len, possible)).items()},
            "raw_to_attainable_pairs": [{"raw": r, "attainable": o, "objects": count}
                                        for (r, o), count in sorted(pairs.items())],
        }
        expected["primary_fraction"] = str(Fraction(expected["raw_outcome_not_invariant"], len(records)))
        require(set(observed) == set(expected) | {"pair_count_interpretation"},
                "aggregate field roster mismatch")
        for field, value in expected.items():
            require(exactly(observed[field], value), "aggregate mismatch: " + arm + "/" + field)
    return {"artifact_id": "reiyah.reviewer-identity-sensitivity.enumeration-verification",
            "version": "0.1.0", "status": "pass", "rows": len(expected_keys),
            "enumerated_object_procedure_worlds": world_count,
            "maximum_worlds_in_one_row": max_worlds,
            "sharp_class_bound_pairs": bound_pairs, "outcome_witnesses": witnesses,
            "source_sha256": SOURCE_SHA256,
            "rows_sha256": hashlib.sha256(rows_path.read_bytes()).hexdigest(),
            "aggregate_result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
            "all_reported_aggregate_counts_verified": True,
            "scope": "Separate same-agent implementation; exhaustive for each observed row, not independent scientific replication or a cross-object joint world."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--rows", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.data, args.rows, args.result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
