"""Operands that let another engineer verify one detector-addition decision.

The Engine compares a base configuration with an augmented one that preserves
every base detection, under a declared additive loss, inside a shared reference
interpretation. For nonnegative false-negative and false-positive penalties a and
b, r retained additions, and TP the maximum same-class one-to-one matched count:

    delta(w) = (a + b) * (TP_augmented(w) - TP_base(w)) - b * r

Three obligations are kept apart throughout, because they need different things:

  calculate  TP_base, TP_augmented and r per anchor per world. Three integers.
  verify     a structure a reader can check without trusting the producer, and
             without running a matcher: the match graph plus, for each
             configuration, a matching and a vertex cover of equal size.
  justify    evidence that the reference interpretations are the right ones.
             Nothing in this module supplies it, and no aggregate can.

A matching M and a vertex cover C with |M| = |C| certify optimality for any
graph: every matching is at most every cover, so |M| <= max <= min <= |C| = |M|.
The checker uses only that inequality, so it never computes a matching.

Exact integer arithmetic with Fraction weights. Standard library only. No network.
Synthetic examples are labelled synthetic; this module reads no dataset.
"""
from fractions import Fraction
import json
import re
import sys

SCHEMA_ID = "reiyah.decision-packet.case"
VERSION = "0.1.0"
MAX_NODES = 4096
MAX_EDGES = 65536
MAX_WORLDS = 256
IDENT = re.compile(r"^[A-Za-z0-9_.:-]{1,64}$")


class CaseError(ValueError):
    """The case is not admissible. Never downgraded to a favourable answer."""


def ident(value, what):
    if not isinstance(value, str) or not IDENT.match(value):
        raise CaseError(f"{what} is not a neutral identifier: {value!r}")
    return value


def rational(text, what):
    if not isinstance(text, str) or not re.match(r"^(0|[1-9][0-9]*)(/[1-9][0-9]*)?$", text):
        raise CaseError(f"{what} is not a nonnegative exact rational string: {text!r}")
    return Fraction(text)


def _augment(node, adjacency, matched_to, seen):
    for other in adjacency[node]:
        if other in seen:
            continue
        seen.add(other)
        if other not in matched_to or _augment(matched_to[other], adjacency, matched_to, seen):
            matched_to[other] = node
            return True
    return False


def maximum_matching(left, adjacency):
    """A maximum matching and a vertex cover of equal size.

    The cover is read off the alternating reachability from unmatched left nodes,
    which is the standard construction. The checker does not reproduce any of
    this; it only checks the two objects it is handed.
    """
    matched_to = {}
    for node in sorted(left):
        _augment(node, adjacency, matched_to, set())
    matching = {node: other for other, node in matched_to.items()}
    reached_left = {node for node in left if node not in matching}
    reached_right = set()
    queue = sorted(reached_left)
    while queue:
        node = queue.pop()
        for other in adjacency[node]:
            if matching.get(node) == other or other in reached_right:
                continue
            reached_right.add(other)
            partner = matched_to.get(other)
            if partner is not None and partner not in reached_left:
                reached_left.add(partner)
                queue.append(partner)
    cover_left = sorted(set(left) - reached_left)
    cover_right = sorted(reached_right)
    return ([[node, matching[node]] for node in sorted(matching)],
            {"detections": cover_left, "objects": cover_right})


def read_world(world, detections, objects):
    """Validate one reference interpretation and return its adjacency."""
    world_id = ident(world.get("world_id", ""), "world_id")
    present = world.get("objects_present")
    if not isinstance(present, list):
        raise CaseError(f"world {world_id} has no objects_present list")
    present_set = []
    for name in present:
        ident(name, "present object")
        if name not in objects:
            raise CaseError(f"world {world_id} presents undeclared object {name}")
        if name in present_set:
            raise CaseError(f"world {world_id} repeats object {name}")
        present_set.append(name)
    edges = world.get("edges")
    if not isinstance(edges, list):
        raise CaseError(f"world {world_id} has no edge list")
    if len(edges) > MAX_EDGES:
        raise CaseError(f"world {world_id} exceeds the edge limit")
    seen = set()
    adjacency = {name: [] for name in detections}
    for edge in edges:
        if not isinstance(edge, list) or len(edge) != 2:
            raise CaseError(f"world {world_id} has a malformed edge")
        detection, obj = ident(edge[0], "edge detection"), ident(edge[1], "edge object")
        if detection not in detections:
            raise CaseError(f"world {world_id} edge names undeclared detection {detection}")
        if obj not in present_set:
            raise CaseError(f"world {world_id} edge names an object not present in it")
        if detections[detection] != objects[obj]:
            raise CaseError(f"world {world_id} edge joins different classes")
        if (detection, obj) in seen:
            raise CaseError(f"world {world_id} repeats an edge")
        seen.add((detection, obj))
        adjacency[detection].append(obj)
    for name in adjacency:
        adjacency[name].sort()
    return world_id, present_set, sorted(seen), adjacency


def build(case):
    """Produce the verifiable operands for one anchor."""
    if case.get("schema_id") != SCHEMA_ID:
        raise CaseError("unexpected schema_id")
    anchor = ident(case.get("anchor_id", ""), "anchor_id")
    loss = case.get("loss", {})
    a = rational(loss.get("false_negative", ""), "false_negative penalty")
    b = rational(loss.get("false_positive", ""), "false_positive penalty")

    detections = {}
    for role in ("base_detections", "added_detections"):
        entries = case.get(role)
        if not isinstance(entries, list):
            raise CaseError(f"{role} must be a list")
        for entry in entries:
            if not isinstance(entry, dict):
                raise CaseError(f"{role} entry is not an object")
            name = ident(entry.get("id", ""), "detection id")
            if name in detections:
                raise CaseError(f"detection {name} is declared twice")
            detections[name] = ident(entry.get("class", ""), "detection class")
    if len(detections) > MAX_NODES:
        raise CaseError("too many detections")
    base = [ident(e["id"], "base id") for e in case["base_detections"]]
    added = [ident(e["id"], "added id") for e in case["added_detections"]]
    augmented = base + added
    if set(base) & set(added):
        raise CaseError("a detection is both base and added; base preservation is violated")
    r = len(added)

    objects = {}
    for entry in case.get("objects", []):
        name = ident(entry.get("id", ""), "object id")
        if name in objects:
            raise CaseError(f"object {name} is declared twice")
        objects[name] = ident(entry.get("class", ""), "object class")
    if len(objects) > MAX_NODES:
        raise CaseError("too many objects")

    worlds = case.get("worlds")
    if not isinstance(worlds, list) or not worlds:
        raise CaseError("at least one reference interpretation is required")
    if len(worlds) > MAX_WORLDS:
        raise CaseError("too many reference interpretations")

    results, seen_worlds = [], set()
    for world in worlds:
        world_id, present, edges, adjacency = read_world(world, detections, objects)
        if world_id in seen_worlds:
            raise CaseError(f"world {world_id} is declared twice")
        seen_worlds.add(world_id)
        base_adj = {d: (adjacency[d] if d in base else []) for d in detections}
        base_match, base_cover = maximum_matching(base, base_adj)
        aug_match, aug_cover = maximum_matching(augmented, adjacency)
        tp_base, tp_aug = len(base_match), len(aug_match)
        if not 0 <= tp_aug - tp_base <= r:
            raise CaseError(f"world {world_id} violates 0 <= TP gain <= r")
        delta = (a + b) * (tp_aug - tp_base) - b * r
        results.append({
            "world_id": world_id,
            "objects_present": present,
            "edges": [[d, o] for d, o in edges],
            "tp_base": tp_base, "tp_augmented": tp_aug,
            "base_certificate": {"matching": base_match, "cover": base_cover},
            "augmented_certificate": {"matching": aug_match, "cover": aug_cover},
            "delta": str(delta),
        })

    values = [Fraction(entry["delta"]) for entry in results]
    return {
        "artifact_id": "reiyah.decision-packet.report", "version": VERSION,
        "anchor_id": anchor,
        "loss": {"false_negative": str(a), "false_positive": str(b)},
        "retained_additions": r,
        "base_detections": base, "added_detections": added,
        "objects": sorted(objects),
        "worlds": results,
        "enclosure": {"lower": str(min(values)), "upper": str(max(values))},
        "coarse_bound": {"lower": str(-b * r), "upper": str(a * r)},
        "scope": ("one anchor, the declared reference interpretations only, and the declared "
                  "additive loss. Not F1, not planner behaviour, not crash risk. An enclosure over "
                  "declared worlds is not physical confidence coverage"),
    }


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: decision_packet.py CASE.json\n")
        return 2
    with open(argv[1], "r", encoding="utf-8") as handle:
        case = json.load(handle)
    try:
        report = build(case)
    except CaseError as error:
        sys.stderr.write(f"case refused: {error}\n")
        return 3
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
