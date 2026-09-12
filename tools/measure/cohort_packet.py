"""A weighted cohort comparison over shared joint reference interpretations.

The single-anchor `decision_packet` verifies one anchor. The declared comparison is
a weighted cohort, and a cohort is not the sum of its anchors:

    D(w) = sum_i weight_i * delta_i(w)      over one shared joint world w
    enclosure = [ min_w D(w), max_w D(w) ]

Taking each anchor's own extremum and adding them is a relaxation, not the answer.
Two half weight copies of the matching trap whose disputed presence is constrained
to be opposite give a joint enclosure of exactly [0, 0], while the summed separate
extrema give [-1, 1]. This module computes the joint quantity and refuses the
relaxation.

Both configurations are evaluated in the **same** world before weighting, every
joint world must cover every finite anchor, and an anchor whose reference is open
contributes its count interval `[-b*r, a*r]` rather than being silently treated as
a world with no objects. An open reference is not an empty finite world; emptying
it would assert that nothing exists, which is the opposite of not knowing.

Exact integer and Fraction arithmetic. Standard library only. No data is read, and
no reference interpretation is invented: a cohort with no admitted joint world and
any finite anchor is reported unresolved rather than computed.
"""
from fractions import Fraction
from itertools import product
import json
import re
import sys

SCHEMA_ID = "reiyah.cohort-packet.case"
VERSION = "0.1.0"
MAX_ANCHORS = 64
MAX_WORLDS = 512
MAX_NODES = 1024
MAX_EDGES = 65536
IDENT = re.compile(r"^[A-Za-z0-9_.:-]{1,64}$")


class CaseError(ValueError):
    """The case is not admissible. Never downgraded to a favourable answer."""


def ident(value, what):
    if not isinstance(value, str) or not IDENT.match(value):
        raise CaseError(f"{what} is not a neutral identifier: {value!r}")
    return value


def nonneg(text, what):
    if not isinstance(text, str) or not re.match(r"^(0|[1-9][0-9]*)(/[1-9][0-9]*)?$", text):
        raise CaseError(f"{what} is not a nonnegative exact rational: {text!r}")
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
    """A maximum matching and a vertex cover of equal size, certifying optimality."""
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
    return ([[node, matching[node]] for node in sorted(matching)],
            {"detections": sorted(set(left) - reached_left), "objects": sorted(reached_right)})


def read_anchor(entry):
    anchor = ident(entry.get("id", ""), "anchor id")
    weight = nonneg(entry.get("weight", ""), f"weight of {anchor}")
    state = entry.get("reference_state")
    if state not in ("finite", "open"):
        raise CaseError(f"anchor {anchor} reference_state must be finite or open")
    classes, base, added = {}, [], []
    for role, sink in (("base_detections", base), ("added_detections", added)):
        rows = entry.get(role)
        if not isinstance(rows, list):
            raise CaseError(f"anchor {anchor} {role} must be a list")
        for row in rows:
            name = ident(row.get("id", ""), "detection id")
            if name in classes:
                raise CaseError(f"anchor {anchor} declares detection {name} twice")
            classes[name] = ident(row.get("class", ""), "detection class")
            sink.append(name)
    if len(classes) > MAX_NODES:
        raise CaseError(f"anchor {anchor} exceeds the node limit")
    objects = {}
    for row in entry.get("objects", []):
        name = ident(row.get("id", ""), "object id")
        if name in objects:
            raise CaseError(f"anchor {anchor} declares object {name} twice")
        objects[name] = ident(row.get("class", ""), "object class")
    if state == "open" and (entry.get("objects") or []):
        raise CaseError(f"anchor {anchor} is open yet declares objects; an open reference "
                        "has no admitted object set")
    return {"id": anchor, "weight": weight, "state": state, "classes": classes,
            "base": base, "added": added, "objects": objects, "r": len(added)}


def world_for(anchor, body):
    present = []
    for name in body.get("objects_present", []):
        ident(name, "present object")
        if name not in anchor["objects"]:
            raise CaseError(f"world presents object {name} undeclared at anchor {anchor['id']}")
        if name in present:
            raise CaseError(f"world repeats object {name} at anchor {anchor['id']}")
        present.append(name)
    edges = body.get("edges")
    if not isinstance(edges, list):
        raise CaseError(f"world has no edge list at anchor {anchor['id']}")
    if len(edges) > MAX_EDGES:
        raise CaseError("world exceeds the edge limit")
    seen, adjacency = set(), {name: [] for name in anchor["classes"]}
    for edge in edges:
        if not isinstance(edge, list) or len(edge) != 2:
            raise CaseError(f"malformed edge at anchor {anchor['id']}")
        detection, obj = ident(edge[0], "edge detection"), ident(edge[1], "edge object")
        if detection not in anchor["classes"]:
            raise CaseError(f"edge names undeclared detection {detection}")
        if obj not in present:
            raise CaseError(f"edge names object {obj} not present in this world")
        if anchor["classes"][detection] != anchor["objects"][obj]:
            raise CaseError("edge joins different classes")
        if (detection, obj) in seen:
            raise CaseError("world repeats an edge")
        seen.add((detection, obj))
        adjacency[detection].append(obj)
    for name in adjacency:
        adjacency[name].sort()
    return present, sorted(seen), adjacency


def build(case):
    if case.get("schema_id") != SCHEMA_ID:
        raise CaseError("unexpected schema_id")
    cohort = ident(case.get("cohort_id", ""), "cohort_id")
    loss = case.get("loss", {})
    a = nonneg(loss.get("false_negative", ""), "false_negative penalty")
    b = nonneg(loss.get("false_positive", ""), "false_positive penalty")
    tolerance = nonneg(loss.get("tolerance", ""), "tolerance")

    rows = case.get("anchors")
    if not isinstance(rows, list) or not rows:
        raise CaseError("a cohort needs at least one anchor")
    if len(rows) > MAX_ANCHORS:
        raise CaseError("too many anchors")
    anchors, seen = [], set()
    for entry in rows:
        anchor = read_anchor(entry)
        if anchor["id"] in seen:
            raise CaseError(f"anchor {anchor['id']} is declared twice")
        seen.add(anchor["id"])
        anchors.append(anchor)
    total_weight = sum((anchor["weight"] for anchor in anchors), Fraction(0))
    if total_weight != 1:
        raise CaseError(f"anchor weights sum to {total_weight}, not 1")

    finite = [anchor for anchor in anchors if anchor["state"] == "finite"]
    open_anchors = [anchor for anchor in anchors if anchor["state"] == "open"]
    open_low = sum((anchor["weight"] * (-b * anchor["r"]) for anchor in open_anchors), Fraction(0))
    open_high = sum((anchor["weight"] * (a * anchor["r"]) for anchor in open_anchors), Fraction(0))

    joint = case.get("joint_worlds")
    if not isinstance(joint, list):
        raise CaseError("joint_worlds must be a list")
    if len(joint) > MAX_WORLDS:
        raise CaseError("too many joint worlds")

    report = {"artifact_id": "reiyah.cohort-packet.report", "version": VERSION,
              "cohort_id": cohort,
              "loss": {"false_negative": str(a), "false_positive": str(b),
                       "tolerance": str(tolerance)},
              "anchors": [{"id": anchor["id"], "weight": str(anchor["weight"]),
                           "reference_state": anchor["state"],
                           "retained_additions": anchor["r"]} for anchor in anchors],
              "open_contribution": {"lower": str(open_low), "upper": str(open_high)},
              "joint_worlds": [], "decision": {}, "enclosure": None}

    if finite and not joint:
        report["state"] = "unresolved"
        report["reason"] = ("a finite anchor is declared with no admitted joint world. An open "
                            "reference is not an empty world and none is invented here")
        report["decision"] = {"improvement_criterion": "not_evaluated", "preference": "not_evaluated"}
        return report

    world_names, lows, highs = set(), [], []
    for body in joint:
        name = ident(body.get("world_id", ""), "world_id")
        if name in world_names:
            raise CaseError(f"joint world {name} is declared twice")
        world_names.add(name)
        per_anchor = body.get("per_anchor")
        if not isinstance(per_anchor, dict):
            raise CaseError(f"joint world {name} has no per_anchor mapping")
        covered = set(per_anchor)
        required = {anchor["id"] for anchor in finite}
        if covered != required:
            raise CaseError(f"joint world {name} must cover exactly the finite anchors; "
                            f"missing {sorted(required - covered)}, extra {sorted(covered - required)}")
        entries, value = [], Fraction(0)
        for anchor in finite:
            present, edges, adjacency = world_for(anchor, per_anchor[anchor["id"]])
            base_adj = {d: (adjacency[d] if d in anchor["base"] else []) for d in anchor["classes"]}
            base_match, base_cover = maximum_matching(anchor["base"], base_adj)
            aug_match, aug_cover = maximum_matching(anchor["base"] + anchor["added"], adjacency)
            gain = len(aug_match) - len(base_match)
            if not 0 <= gain <= anchor["r"]:
                raise CaseError(f"world {name} anchor {anchor['id']} violates 0 <= gain <= r")
            delta = (a + b) * gain - b * anchor["r"]
            value += anchor["weight"] * delta
            entries.append({"anchor": anchor["id"], "objects_present": present,
                            "edges": [[d, o] for d, o in edges],
                            "tp_base": len(base_match), "tp_augmented": len(aug_match),
                            "delta": str(delta),
                            "base_certificate": {"matching": base_match, "cover": base_cover},
                            "augmented_certificate": {"matching": aug_match, "cover": aug_cover}})
        report["joint_worlds"].append({"world_id": name, "anchors": entries,
                                       "finite_contribution": str(value)})
        lows.append(value + open_low)
        highs.append(value + open_high)

    if not lows:
        lows, highs = [open_low], [open_high]
        report["state"] = "open_reference_only"
        report["reason"] = "every anchor is open; the enclosure is the weighted count bound"
    else:
        report["state"] = "computed"
    lower, upper = min(lows), max(highs)
    report["enclosure"] = {"lower": str(lower), "upper": str(upper)}
    report["coarse_bound"] = {
        "lower": str(sum((anchor["weight"] * (-b * anchor["r"]) for anchor in anchors), Fraction(0))),
        "upper": str(sum((anchor["weight"] * (a * anchor["r"]) for anchor in anchors), Fraction(0)))}
    report["decision"] = {
        "improvement_criterion": ("supported" if lower > tolerance else
                                  "excluded" if upper <= tolerance else "unresolved"),
        "preference": ("prefer_augmented" if lower > tolerance else
                       "prefer_base" if upper < -tolerance else
                       "equivalent_within_tolerance" if lower >= -tolerance and upper <= tolerance
                       else "unresolved")}
    report["separate_anchor_relaxation"] = relaxation(anchors, finite, joint, a, b, open_low, open_high)
    report["scope"] = ("the declared cohort, the declared joint worlds and the declared additive "
                       "loss. An enclosure over admitted worlds is not physical coverage, and the "
                       "separate relaxation is reported only to show it is wider, never as a result")
    return report


def relaxation(anchors, finite, joint, a, b, open_low, open_high):
    """Each anchor's own extremum, summed. A relaxation, reported to be refused."""
    if not finite or not joint:
        return None
    low = high = Fraction(0)
    for anchor in finite:
        values = []
        for body in joint:
            present, _edges, adjacency = world_for(anchor, body["per_anchor"][anchor["id"]])
            base_adj = {d: (adjacency[d] if d in anchor["base"] else []) for d in anchor["classes"]}
            base_match, _c = maximum_matching(anchor["base"], base_adj)
            aug_match, _c2 = maximum_matching(anchor["base"] + anchor["added"], adjacency)
            values.append((a + b) * (len(aug_match) - len(base_match)) - b * anchor["r"])
        low += anchor["weight"] * min(values)
        high += anchor["weight"] * max(values)
    return {"lower": str(low + open_low), "upper": str(high + open_high),
            "status": "a relaxation of the joint enclosure, never the declared result"}


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: cohort_packet.py CASE.json\n")
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
