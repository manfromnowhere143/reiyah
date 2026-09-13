#!/usr/bin/env python3
"""Bounded synthetic conformance of shared graphs to original joint worlds."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
from itertools import combinations, permutations, product
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tests.test_perception_reference import inputs, object_at, world
from tools import perception_reference as reference
from tools.perception_decision import checker, contract, kernel


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def digest(value):
    return hashlib.sha256(contract.encoded(value)).hexdigest()


def number(value):
    return Fraction(int(value["numerator"]), int(value["denominator"]))


def wire(value):
    value = Fraction(value)
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def require(condition, code):
    if not condition:
        raise AssertionError(code)


def partitions(items):
    if not items:
        return [()]
    previous = partitions(items[:-1])
    item = items[-1]
    result = []
    for blocks in previous:
        result.append(blocks + ((item,),))
        for index in range(len(blocks)):
            result.append(blocks[:index] + (blocks[index] + (item,),) + blocks[index + 1:])
    return sorted(result)


PARTITIONS = partitions(tuple(range(4)))
RECIPES = tuple(product(range(15), range(15), range(3), range(2), range(2), range(2)))


def make_case(index):
    left, right, geometry, classes, spelling, unequal_weights = RECIPES[index]
    args = list(inputs(2))
    spec, comparison, normalizations, catalog = args
    sources = {}
    if unequal_weights:
        for ai in range(2):
            comparison["anchors"][ai]["weight"] = wire(Fraction(ai + 1, 3))
            normalizations[ai]["normalized_anchor_sha256"] = digest(comparison["anchors"][ai])
    for wi, pair in enumerate(((left, right), (right, left))):
        objects_at_anchors = []
        for ai, partition_index in enumerate(pair):
            objects = []
            for oi, block in enumerate(PARTITIONS[partition_index]):
                name = "object-" + str(oi) if spelling else "group-" + "-".join(map(str, block))
                members = [f"a{ai}-proposal-{n}" for n in block]
                if spelling and wi == 1:
                    members.reverse()
                x = (Fraction(3, 2) if geometry == 0 else
                     Fraction(3 * (min(block) % 2)) if geometry == 1 else
                     Fraction(4 * min(block) - 2))
                label = "truck" if classes and sum(block) % 2 else "car"
                obj = object_at(name, x, label=label, time=(ai + 1) * 1_000_000, members=members)
                source = {"evidence_kind": "synthetic", "case": index, "world": f"world-{wi}",
                          "anchor": f"anchor-{ai}", "object": {k: v for k, v in obj.items() if k != "record_sha256"}}
                obj["record_sha256"] = digest(source)
                sources[obj["record_sha256"]] = source
                objects.append(obj)
            objects_at_anchors.append(objects)
        w = world(f"world-{wi}", objects_at_anchors)
        w["basis_sha256"] = digest({"synthetic_case": index, "world": w})
        spec["worlds"].append(w)
    spec["inputs"] = {"comparison_sha256": digest(comparison), "normalizations_sha256": digest(normalizations),
                      "catalog_sha256": digest(catalog)}
    return args, sources


def cardinality(left, right, edges):
    """Enumerate injections by cardinality, without an augmenting-path routine."""
    for size in range(min(len(left), len(right)), -1, -1):
        for detections in combinations(left, size):
            for objects in permutations(right, size):
                if all(pair in edges for pair in zip(detections, objects)):
                    return size
    raise AssertionError("EMPTY_MATCHING_MISSING")


def inspect(args, sources, compiled, receipt, packet):
    spec, original, normalizations, catalog = args
    require(receipt["reference_semantic_sha256"] == digest(spec), "SOURCE_BINDING")
    require(receipt["compiled_input_sha256"] == digest(compiled), "COMPILED_BINDING")
    require(set(compiled) == set(original) and all(compiled[key] == value for key, value in original.items()
            if key not in ("model", "anchors", "assumptions")), "ORIGINAL_OPERANDS")
    require(compiled["assumptions"][:len(original["assumptions"])] == original["assumptions"], "ORIGINAL_ASSUMPTIONS")
    original_anchors = {a["id"]: a for a in original["anchors"]}
    require(len(compiled["anchors"]) == len(original_anchors) and
            {a["id"] for a in compiled["anchors"]} == set(original_anchors), "ORIGINAL_ANCHORS")
    for anchor in compiled["anchors"]:
        before = original_anchors[anchor["id"]]
        require(set(anchor) == set(before) and all(anchor[key] == value for key, value in before.items()
                if key != "reference"), "ORIGINAL_OPERANDS")
    require([r["world_id"] for r in receipt["world_encodings"]] == [w["id"] for w in spec["worlds"]], "WORLD_IDENTITIES")
    require(len(packet["proof"]["worlds"]) == len(spec["worlds"]) == 2, "JOINT_WORLD_COUNT")
    require(all(a["reference"]["state"] == "finite" for a in compiled["anchors"]), "UNEXPECTED_OPEN")
    proof_worlds = {tuple(w["assignment"]): {a["anchor"]: a for a in w["anchors"]} for w in packet["proof"]["worlds"]}
    normals = {r["anchor_id"]: r for r in normalizations}
    clocks = {r["sample_token"]: r for r in catalog["anchors"]}
    fn, fp = (number(original["loss"][name]) for name in ("false_negative", "false_positive"))
    total_losses, world_graphs, mappings_seen, edge_count = [], [], 0, 0
    node_identities = {}
    for source_world, encoding in zip(spec["worlds"], receipt["world_encodings"]):
        assignment = {q["variable"]: q["value"] for q in encoding["when"]}
        proof = proof_worlds[tuple(assignment[v] for v in compiled["model"]["variables"])]
        source_anchors = {a["anchor_id"]: a for a in source_world["anchors"]}
        total, graphs = Fraction(0), []
        for anchor in compiled["anchors"]:
            name = anchor["id"]
            records = source_anchors[name]["objects"]
            originals = {o["id"]: o for o in records}
            require(len(originals) == len(records), "ORIGINAL_OBJECT_IDENTITY")
            normal = normals[name]
            clock = clocks[normal["sample_token"]]
            require(all(o["timestamp_us"] == clock["anchor_timestamp_us"] for o in records), "SCOPE_TIME")
            require(all(sum(number(q) ** 2 for q in o["xy"]) <= 2500 and o["class"] in ("car", "truck") for o in records), "SCOPE_OBJECT")
            for obj in records:
                source = sources[obj["record_sha256"]]
                require(digest(source) == obj["record_sha256"] and source["object"] == {k: v for k, v in obj.items() if k != "record_sha256"}, "ORIGINAL_RECORD")
                require(source["evidence_kind"] == "synthetic" and source["world"] == source_world["id"] and source["anchor"] == name, "ORIGINAL_SOURCE_CONTEXT")
            mappings = [r for r in receipt["object_mapping"] if r["world_id"] == source_world["id"] and r["anchor_id"] == name]
            mapped = {r["graph_id"]: r["object_id"] for r in mappings}
            require(len(mappings) == len(mapped) == len(originals) and set(mapped.values()) == set(originals), "PROVENANCE_POPULATION")
            for row in mappings:
                obj = originals[row["object_id"]]
                require(row["members"] == obj["members"] and row["record_sha256"] == obj["record_sha256"], "ORDERED_PROVENANCE")
                signature = (tuple(sorted(obj["members"])), obj["class"], obj["timestamp_us"], tuple(map(number, obj["xy"])))
                key = (name, row["graph_id"])
                require(node_identities.setdefault(key, signature) == signature, "SHARED_NODE_IDENTITY")
            mappings_seen += len(mappings)
            active = lambda row: all(assignment[q["variable"]] == q["value"] for q in row["when"])
            ref = anchor["reference"]
            objects = [r["id"] for r in ref["objects"] if active(r)]
            require(len(objects) == len(set(objects)) and set(objects) == set(mapped), "ACTIVE_OBJECT_SET")
            detections = {r["detection"]["id"]: r["record"] for r in normal["qualified_records"]}
            base = [r["id"] for r in original_anchors[name]["base"]["value"]]
            augmented = base + [r["id"] for r in original_anchors[name]["additions"]["value"]]
            require(len(base) == 1 and len(augmented) == 2, "RETAINED_ADDITION")
            expected_edges = {(did, oid) for did in augmented for oid, obj in originals.items()
                              if detections[did]["class"] == obj["class"] and
                              sum((number(a) - number(b)) ** 2 for a, b in zip(detections[did]["xy"], obj["xy"])) < 4}
            edges = [(e["detection"], mapped[e["object"]]) for e in ref["edges"] if e["object"] in objects and active(e)]
            require(len(edges) == len(set(edges)) and set(edges) == expected_edges, "EXACT_ORIGINAL_EDGES")
            m0 = cardinality(base, list(originals), expected_edges)
            m1 = cardinality(augmented, list(originals), expected_edges)
            require(len(proof[name]["base"]["matching"]) == m0 and len(proof[name]["augmented"]["matching"]) == m1, "ORIGINAL_MAXIMUM_MATCHING")
            loss0 = fn * (len(originals) - m0) + fp * (len(base) - m0)
            loss1 = fn * (len(originals) - m1) + fp * (len(augmented) - m1)
            delta = loss0 - loss1
            require(delta == (fn + fp) * (m1 - m0) - fp * (len(augmented) - len(base)), "ADDITIVE_IDENTITY")
            total += number(original_anchors[name]["weight"]) * delta
            graphs.append({"anchor": name, "objects": sorted(originals), "edges": sorted(expected_edges),
                           "base_matching_size": m0, "augmented_matching_size": m1, "delta": str(delta)})
            edge_count += len(edges)
        total_losses.append(total)
        world_graphs.append({"world": source_world["id"], "anchors": graphs, "weighted_delta": str(total)})
    require(mappings_seen == len(receipt["object_mapping"]), "EXTRA_PROVENANCE")
    actual = [number(packet["result"]["bounds"][key]) for key in ("lower", "upper")]
    require(actual == [min(total_losses), max(total_losses)], "JOINT_LOSS")
    require(packet["result"]["physical_coverage"] == "not_established", "PHYSICAL_SCOPE")
    return world_graphs, edge_count


def run_case(index):
    args, sources = make_case(index)
    original_digest = digest(args)
    compiled, receipt = reference.compile_model(*args)
    packet = kernel.produce(compiled)
    with patch.object(kernel, "_matching_certificate", side_effect=AssertionError("PRODUCER_CALLED_BY_CHECKER")):
        checker.check(compiled, packet)
    graphs, edges = inspect(args, sources, compiled, receipt, packet)
    require(digest(args) == original_digest, "ORIGINAL_INPUT_MUTATION")
    row = {"case": index, "recipe": list(RECIPES[index]), "input_sha256": original_digest,
           "source_records_sha256": digest(sources), "compiled_sha256": digest(compiled),
           "compilation_sha256": digest(receipt), "checked_packet_sha256": digest(packet),
           "original_world_graphs_sha256": digest(graphs), "weighted_world_deltas": [w["weighted_delta"] for w in graphs],
           "bounds": [str(number(packet["result"]["bounds"][key])) for key in ("lower", "upper")],
           "source_mappings": len(receipt["object_mapping"]), "original_active_edges": edges,
           "compiled_nodes": sum(len(a["reference"]["objects"]) for a in compiled["anchors"])}
    return row, {"inputs": args, "synthetic_source_records": sources, "compiled": compiled,
                 "compilation": receipt, "checked_packet": packet, "original_world_graphs": graphs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--limit", type=int, default=len(RECIPES))
    group.add_argument("--case", type=int)
    args = parser.parse_args()
    if args.case is not None:
        if not 0 <= args.case < len(RECIPES):
            parser.error("Case outside declared domain")
        row, complete = run_case(args.case)
        print(json.dumps({"row": row, **complete}, sort_keys=True, indent=2))
        return
    if not 1 <= args.limit <= len(RECIPES):
        parser.error("Limit outside declared domain")
    sequence = hashlib.sha256()
    bounds = Counter()
    mapping_count = edge_count = nodes = 0
    for index in range(args.limit):
        row, _ = run_case(index)
        raw = encode(row)
        sequence.update(raw)
        sys.stdout.buffer.write(raw)
        bounds[tuple(row["bounds"])] += 1
        mapping_count += row["source_mappings"]
        edge_count += row["original_active_edges"]
        nodes += row["compiled_nodes"]
    summary = {"artifact_id": "reiyah.engine.partition-conformance.result", "version": "0.1.0",
               "cases_checked": args.limit, "declared_cases": len(RECIPES), "complete_declared_grid": args.limit == len(RECIPES),
               "partitions": len(PARTITIONS), "partition_definition": [list(map(list, p)) for p in PARTITIONS],
               "case_rows_sha256": sequence.hexdigest(), "source_mappings_checked": mapping_count,
               "original_active_edges_checked": edge_count, "compiled_nodes_checked": nodes,
               "bounds_counts": [{"bounds": list(key), "count": count} for key, count in sorted(bounds.items())],
               "compiler_sha256": hashlib.sha256((ROOT / 'tools/perception_reference.py').read_bytes()).hexdigest(),
               "evidence_kind": "synthetic_compiler_conformance", "human_references": "none_admitted",
               "physical_coverage": "not_established", "real_bounds": ["-8", "8"]}
    sys.stdout.buffer.write(encode(summary))


if __name__ == "__main__":
    main()
