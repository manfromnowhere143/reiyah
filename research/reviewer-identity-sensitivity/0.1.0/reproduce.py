"""Exact recorded-reviewer-ID sensitivity; no inference about physical truth."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import platform
import time

NO_MAJORITY = "no_strict_majority"
SOURCE_SHA256 = "1eb5506f328316f46fa5a036486b05689f4d504602895b80c87ee8bda0e0dd1d"
SOURCE_BYTES = 8568020
CLASSES = ("person", "rider", "car", "truck", "bus", "train", "motorcycle", "bicycle", "cantsolve")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def strict_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def load_json(raw):
    def reject_constant(value):
        raise ValueError("nonfinite JSON constant: " + value)
    return json.loads(raw, object_pairs_hook=strict_object,
                      parse_constant=reject_constant)


def outcome(choices):
    require(len(choices) > 0, "empty response world")
    counts = Counter(choices)
    winners = [c for c, count in counts.items() if 2 * count > len(choices)]
    require(len(winners) <= 1, "multiple strict majorities")
    return winners[0] if winners else NO_MAJORITY


def validate_supports(supports, classes):
    require(bool(classes) and len(set(classes)) == len(classes), "invalid classes")
    require(all(isinstance(c, str) and c for c in classes), "invalid class name")
    require(NO_MAJORITY not in classes, "reserved outcome name")
    require(bool(supports), "empty reviewer population")
    allowed = set(classes)
    for support in supports:
        require(isinstance(support, (set, frozenset)) and bool(support), "empty or invalid support")
        require(support <= allowed, "undeclared response class")


def check_assignment(supports, assignment):
    require(isinstance(assignment, list) and len(assignment) == len(supports),
            "assignment membership mismatch")
    require(all(c in support for c, support in zip(assignment, supports)),
            "assignment outside observed support")


def balanced_assignment(supports, classes):
    """Ordinary bipartite matching against floor(n/2) slots per class."""
    validate_supports(supports, classes)
    capacity = len(supports) // 2
    occupied = {}

    def augment(group, visited):
        for label in classes:
            if label not in supports[group]:
                continue
            for slot in range(capacity):
                key = (label, slot)
                if key in visited:
                    continue
                visited.add(key)
                if key not in occupied or augment(occupied[key], visited):
                    occupied[key] = group
                    return True
        return False

    for group in range(len(supports)):
        if not augment(group, set()):
            return None
    assignment = [None] * len(supports)
    for (label, _), group in occupied.items():
        assignment[group] = label
    check_assignment(supports, assignment)
    require(outcome(assignment) == NO_MAJORITY, "unbalanced matching witness")
    return assignment


def hall_obstruction(supports, classes):
    """Separate subset-count characterization, without calling the matcher."""
    validate_supports(supports, classes)
    capacity = len(supports) // 2
    for mask in range(1 << len(classes)):
        selected = {c for i, c in enumerate(classes) if mask & (1 << i)}
        forced = [i for i, support in enumerate(supports) if support <= selected]
        if len(forced) > capacity * len(selected):
            return {"classes": sorted(selected), "forced_group_indices": forced,
                    "available_slots": capacity * len(selected)}
    return None


def characterize(supports, classes=CLASSES):
    """Sharp marginal count bounds AND jointly attainable majority outcomes."""
    validate_supports(supports, classes)
    n = len(supports)
    bounds = {}
    witnesses = {}
    possible = []
    for label in classes:
        lower = sum(support == {label} for support in supports)
        upper = sum(label in support for support in supports)
        low_world = [min(support - {label}) if support - {label} else label
                     for support in supports]
        high_world = [label if label in support else min(support) for support in supports]
        for world, expected in ((low_world, lower), (high_world, upper)):
            check_assignment(supports, world)
            require(world.count(label) == expected, "class endpoint witness mismatch")
        bounds[label] = {"lower": lower, "upper": upper, "denominator": n}
        if 2 * upper > n:
            require(outcome(high_world) == label, "majority witness mismatch")
            possible.append(label)
            witnesses[label] = high_world
    balanced = balanced_assignment(supports, classes)
    obstruction = hall_obstruction(supports, classes)
    require((balanced is None) == (obstruction is not None), "matching/Hall disagreement")
    if balanced is not None:
        possible.append(NO_MAJORITY)
        witnesses[NO_MAJORITY] = balanced
    require(bool(possible), "empty attainable outcome set")
    return {"group_count": n, "class_count_bounds": bounds,
            "possible_outcomes": sorted(possible), "outcome_witnesses": witnesses,
            "no_majority_obstruction": obstruction}


def procedure_entries(obj, procedure):
    entries = []
    if procedure == "proposed":
        require(isinstance(obj["annotation_info"], dict), "invalid proposed records")
        for reviewer, responses in obj["annotation_info"].items():
            require(isinstance(responses, list) and responses, "missing proposed responses")
            entries.extend((reviewer, response) for response in responses)
    elif procedure == "no_proposal":
        require(isinstance(obj["unbiased_annotation_info"], list), "invalid no-proposal records")
        for record in obj["unbiased_annotation_info"]:
            require(isinstance(record, dict) and record, "missing no-proposal response")
            entries.extend(record.items())
    else:
        raise ValueError("unknown procedure")
    require(bool(entries), "missing response population")
    for reviewer, response in entries:
        require(isinstance(reviewer, str) and reviewer, "missing reviewer identifier")
        require(isinstance(response, dict) and set(response) == {"vote", "time"},
                "changed response schema")
        require(response["vote"] in CLASSES, "undeclared vote")
        duration = response["time"]
        require(type(duration) in (int, float) and duration >= 0, "invalid stored duration")
    return entries


def analyze_source(data):
    require(data["classes"] == list(CLASSES), "changed class vocabulary/order")
    require(isinstance(data["objects"], dict) and len(data["objects"]) == 388,
            "image roster mismatch")
    require(sum(len(objects) for objects in data["objects"].values()) == 1000,
            "object roster mismatch")
    rows = []
    ids = set()
    for image_name, objects in sorted(data["objects"].items()):
        for object_index, obj in enumerate(objects):
            require(obj["mo_id"] not in ids, "duplicate object identifier")
            ids.add(obj["mo_id"])
            for procedure in ("proposed", "no_proposal"):
                entries = procedure_entries(obj, procedure)
                raw_votes = [response["vote"] for _, response in entries]
                frequency_key = "frequencies" if procedure == "proposed" else "unbiased_frequencies"
                frequencies = obj[frequency_key]
                require(isinstance(frequencies, dict) and set(frequencies) <= set(CLASSES),
                        "invalid stored frequency classes")
                require(all(type(v) is int and v >= 0 for v in frequencies.values()),
                        "invalid stored frequency count")
                require(Counter(raw_votes) == Counter(frequencies), "stored frequency mismatch")
                groups = defaultdict(list)
                for reviewer, response in entries:
                    groups[reviewer].append(response["vote"])
                ordered_ids = sorted(groups)
                supports = [frozenset(groups[i]) for i in ordered_ids]
                characterized = characterize(supports)
                raw = outcome(raw_votes)
                rows.append({"image_name": image_name, "object_index": object_index,
                             "object_id": obj["mo_id"], "procedure": procedure,
                             "raw_entry_count": len(entries), "raw_outcome": raw,
                             "reviewer_ids": ordered_ids,
                             "repeated_id": len(entries) != len(groups),
                             "conflicting_id": any(len(support) > 1 for support in supports),
                             **characterized})
    return rows


def aggregate(rows):
    result = {}
    ordinary = set(CLASSES) - {"cantsolve"}
    for procedure in ("proposed", "no_proposal"):
        selected = [r for r in rows if r["procedure"] == procedure]
        require(len(selected) == 1000, "procedure roster mismatch")
        counts = Counter()
        transitions = Counter()
        raw_outcomes = Counter()
        possibilities = Counter()
        for row in selected:
            raw = row["raw_outcome"]
            possible = set(row["possible_outcomes"])
            raw_outcomes[raw] += 1
            possibilities[len(possible)] += 1
            counts["objects"] += 1
            counts["raw_response_entries"] += row["raw_entry_count"]
            counts["distinct_ID_object_pairs"] += row["group_count"]
            counts["objects_with_repeated_ID"] += row["repeated_id"]
            counts["objects_with_conflicting_responses_under_an_ID"] += row["conflicting_id"]
            counts["raw_outcome_invariant"] += possible == {raw}
            counts["raw_outcome_not_invariant"] += possible != {raw}
            counts["unique_normalized_outcome_different_from_raw"] += len(possible) == 1 and raw not in possible
            counts["multiple_normalized_outcomes"] += len(possible) > 1
            counts["raw_outcome_not_attainable"] += raw not in possible
            counts["raw_ordinary_majority_can_lose_majority"] += raw in ordinary and NO_MAJORITY in possible
            counts["raw_ordinary_majority_can_switch_ordinary_class"] += raw in ordinary and bool((possible & ordinary) - {raw})
            counts["raw_ordinary_majority_can_become_cantsolve"] += raw in ordinary and "cantsolve" in possible
            counts["raw_no_majority_can_gain_ordinary_majority"] += raw == NO_MAJORITY and bool(possible & ordinary)
            counts["raw_cantsolve_can_change"] += raw == "cantsolve" and possible != {raw}
            counts["normalized_no_majority_possible"] += NO_MAJORITY in possible
            counts["no_majority_infeasible_with_Hall_obstruction"] += row["no_majority_obstruction"] is not None
            for label in possible:
                transitions[(raw, label)] += 1
        result[procedure] = {
            **dict(sorted(counts.items())),
            "primary_fraction": str(Fraction(counts["raw_outcome_not_invariant"], counts["objects"])),
            "raw_outcome_counts": dict(sorted(raw_outcomes.items())),
            "attainable_outcome_count_histogram": {str(n): count for n, count in sorted(possibilities.items())},
            "raw_to_attainable_pairs": [
                {"raw": raw, "attainable": label, "objects": count}
                for (raw, label), count in sorted(transitions.items())],
            "pair_count_interpretation": "Possibilities overlap; these are not transition probabilities or jointly observed changes."
        }
    return result


def write_json(path, value):
    with path.open("x") as handle:
        handle.write(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected", type=Path)
    args = parser.parse_args()
    started = time.perf_counter()
    require(not args.output.exists(), "output must be a fresh directory")
    args.output.mkdir(parents=True)
    raw = args.data.read_bytes()
    require(len(raw) == SOURCE_BYTES and hashlib.sha256(raw).hexdigest() == SOURCE_SHA256,
            "input bytes differ from the frozen source")
    protocol_raw = Path(__file__).with_name("protocol.json").read_bytes()
    protocol = load_json(protocol_raw)
    require(protocol["source"]["sha256"] == SOURCE_SHA256, "protocol/source mismatch")
    rows = analyze_source(load_json(raw))
    summary = {
        "artifact_id": "reiyah.reviewer-identity-sensitivity.result",
        "version": "0.1.0", "lifecycle_status": "exploratory",
        "source_sha256": SOURCE_SHA256,
        "protocol_sha256": hashlib.sha256(protocol_raw).hexdigest(),
        "object_records": 1000, "image_groups": 388, "procedure_object_rows": len(rows),
        "procedures": aggregate(rows),
        "verification": {"matching_Hall_agreements": len(rows),
                         "class_endpoint_witness_pairs_checked": len(rows) * len(CLASSES)},
        "scope": "Exact recorded-ID policy sensitivity on a complete selected object file; not physical truth, detector evaluation, independent-voter inference or work saving."
    }
    write_json(args.output / "result.json", summary)
    write_json(args.output / "private_rows.json", rows)
    if args.expected:
        require(summary == load_json(args.expected.read_bytes()), "retained result mismatch")
    write_json(args.output / "execution.json", {
        "python": platform.python_version(), "platform": platform.platform(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "wall_seconds": time.perf_counter() - started,
        "timing_scope": "Inside main, including reading, analysis and output; excludes imports, acquisition, preparation and human work."
    })
    print(json.dumps(summary, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
