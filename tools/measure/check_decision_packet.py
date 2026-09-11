"""Independent checker for a decision packet.

This module imports nothing from the producer and computes no matching. It checks
the two certificates it is handed, which is enough:

    every matching is at most every vertex cover, so a matching M and a cover C
    with |M| = |C| force |M| = max matching = min cover.

That inequality holds for any graph, so the checker needs no bipartite theorem and
no search. It then recomputes the loss difference from the certified counts.

What a confirmation establishes, and only this: the arithmetic of the declared
comparison inside the declared reference interpretations. It says nothing about
whether those interpretations are the right ones, whether the graph reflects the
recording, or whether the population is the intended one. Those are separate
obligations and no packet discharges them.

Shared trusted surface with the producer: the JSON module, the identifier and
rational string conventions declared here, and Python's Fraction and integer
arithmetic. Nothing else.
"""
from fractions import Fraction
import json
import re
import sys

IDENT = re.compile(r"^[A-Za-z0-9_.:-]{1,64}$")
RATIONAL = re.compile(r"^-?(0|[1-9][0-9]*)(/[1-9][0-9]*)?$")
NONNEG = re.compile(r"^(0|[1-9][0-9]*)(/[1-9][0-9]*)?$")
CASE_KEYS = {"schema_id", "anchor_id", "label", "loss", "base_detections",
             "added_detections", "objects", "worlds"}
REPORT_KEYS = {"artifact_id", "version", "anchor_id", "loss", "retained_additions",
               "base_detections", "added_detections", "objects", "worlds",
               "enclosure", "coarse_bound", "scope"}


class Rejected(Exception):
    """The packet does not establish its result."""


def _no_duplicate_keys(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise Rejected(f"duplicate JSON key {key!r}")
        seen[key] = value
    return seen


def load(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle, object_pairs_hook=_no_duplicate_keys)


def ident(value, what):
    if not isinstance(value, str) or not IDENT.match(value):
        raise Rejected(f"{what} is not a neutral identifier: {value!r}")
    return value


def exact(text, what, pattern=RATIONAL):
    if not isinstance(text, str) or not pattern.match(text):
        raise Rejected(f"{what} is not an exact rational string: {text!r}")
    return Fraction(text)


def only_known(body, allowed, what):
    if not isinstance(body, dict):
        raise Rejected(f"{what} is not an object")
    unknown = sorted(set(body) - allowed)
    if unknown:
        raise Rejected(f"{what} carries unknown fields: {unknown}")


def certify(certificate, edges, allowed_detections, what):
    """Return the certified maximum matching size, or reject.

    Checks, in order: the matching uses declared edges, is one to one on both
    sides, and uses only permitted detections; the cover is a genuine vertex
    cover of every declared edge; the two have equal size.
    """
    only_known(certificate, {"matching", "cover"}, what)
    matching = certificate.get("matching")
    if not isinstance(matching, list):
        raise Rejected(f"{what} has no matching")
    left, right = set(), set()
    for pair in matching:
        if not isinstance(pair, list) or len(pair) != 2:
            raise Rejected(f"{what} matching entry is malformed")
        detection, obj = ident(pair[0], "matched detection"), ident(pair[1], "matched object")
        if detection not in allowed_detections:
            raise Rejected(f"{what} matches a detection not in this configuration")
        if (detection, obj) not in edges:
            raise Rejected(f"{what} matches a pair that is not an edge")
        if detection in left or obj in right:
            raise Rejected(f"{what} matching is not one to one")
        left.add(detection)
        right.add(obj)
    cover = certificate.get("cover")
    only_known(cover if isinstance(cover, dict) else {}, {"detections", "objects"}, f"{what} cover")
    cover_detections = {ident(v, "cover detection") for v in cover.get("detections", [])}
    cover_objects = {ident(v, "cover object") for v in cover.get("objects", [])}
    if len(cover_detections) != len(cover.get("detections", [])):
        raise Rejected(f"{what} cover repeats a detection")
    if len(cover_objects) != len(cover.get("objects", [])):
        raise Rejected(f"{what} cover repeats an object")
    for detection, obj in edges:
        if detection not in allowed_detections:
            continue
        if detection not in cover_detections and obj not in cover_objects:
            raise Rejected(f"{what} cover misses an edge")
    size = len(cover_detections) + len(cover_objects)
    if len(matching) != size:
        raise Rejected(f"{what} matching has {len(matching)} pairs against a cover of {size}")
    return len(matching)


def verify(case, report):
    only_known(case, CASE_KEYS, "case")
    only_known(report, REPORT_KEYS, "report")
    if case.get("schema_id") != "reiyah.decision-packet.case":
        raise Rejected("case schema_id is not the expected one")
    if report.get("anchor_id") != case.get("anchor_id"):
        raise Rejected("report anchor does not match the case")

    classes = {}
    base, added = [], []
    for role, sink in (("base_detections", base), ("added_detections", added)):
        for entry in case.get(role, []):
            name = ident(entry.get("id", ""), "detection id")
            if name in classes:
                raise Rejected(f"detection {name} is declared twice")
            classes[name] = ident(entry.get("class", ""), "detection class")
            sink.append(name)
    if set(base) & set(added):
        raise Rejected("base preservation is violated: a detection is both base and added")
    if report.get("base_detections") != base or report.get("added_detections") != added:
        raise Rejected("report configurations do not match the case")
    r = report.get("retained_additions")
    if not isinstance(r, int) or isinstance(r, bool) or r != len(added):
        raise Rejected("retained additions do not equal the declared added detections")

    objects = {}
    for entry in case.get("objects", []):
        name = ident(entry.get("id", ""), "object id")
        if name in objects:
            raise Rejected(f"object {name} is declared twice")
        objects[name] = ident(entry.get("class", ""), "object class")

    a = exact(case["loss"]["false_negative"], "false_negative", NONNEG)
    b = exact(case["loss"]["false_positive"], "false_positive", NONNEG)
    if (exact(report["loss"]["false_negative"], "report fn", NONNEG) != a
            or exact(report["loss"]["false_positive"], "report fp", NONNEG) != b):
        raise Rejected("report loss does not match the case")

    case_worlds = {}
    for world in case.get("worlds", []):
        world_id = ident(world.get("world_id", ""), "world_id")
        if world_id in case_worlds:
            raise Rejected(f"case repeats world {world_id}")
        case_worlds[world_id] = world
    reported = report.get("worlds")
    if not isinstance(reported, list) or len(reported) != len(case_worlds):
        raise Rejected("report does not cover exactly the declared reference interpretations")

    deltas, seen = [], set()
    for entry in reported:
        world_id = ident(entry.get("world_id", ""), "world_id")
        if world_id in seen or world_id not in case_worlds:
            raise Rejected(f"world {world_id} is repeated or undeclared")
        seen.add(world_id)
        declared = case_worlds[world_id]
        present = [ident(v, "present object") for v in declared.get("objects_present", [])]
        if entry.get("objects_present") != present:
            raise Rejected(f"world {world_id} present objects do not match the case")
        edges = set()
        for pair in declared.get("edges", []):
            detection, obj = ident(pair[0], "edge detection"), ident(pair[1], "edge object")
            if detection not in classes:
                raise Rejected(f"world {world_id} edge names an undeclared detection")
            if obj not in present:
                raise Rejected(f"world {world_id} edge names an object not present")
            if classes[detection] != objects.get(obj):
                raise Rejected(f"world {world_id} edge joins different classes")
            edges.add((detection, obj))
        if {tuple(pair) for pair in entry.get("edges", [])} != edges:
            raise Rejected(f"world {world_id} report edges do not equal the case edges")
        tp_base = certify(entry.get("base_certificate", {}), edges, set(base),
                          f"world {world_id} base")
        tp_aug = certify(entry.get("augmented_certificate", {}), edges, set(base) | set(added),
                         f"world {world_id} augmented")
        if entry.get("tp_base") != tp_base or entry.get("tp_augmented") != tp_aug:
            raise Rejected(f"world {world_id} states counts its certificates do not support")
        if not 0 <= tp_aug - tp_base <= r:
            raise Rejected(f"world {world_id} violates 0 <= TP gain <= r")
        delta = (a + b) * (tp_aug - tp_base) - b * r
        if exact(entry.get("delta", ""), f"world {world_id} delta") != delta:
            raise Rejected(f"world {world_id} delta is not the declared loss difference")
        deltas.append(delta)

    lower, upper = min(deltas), max(deltas)
    if (exact(report["enclosure"]["lower"], "enclosure lower") != lower
            or exact(report["enclosure"]["upper"], "enclosure upper") != upper):
        raise Rejected("enclosure does not equal the range over the declared worlds")
    if not (-b * r <= lower and upper <= a * r):
        raise Rejected("enclosure escapes the coarse count bound")
    return {"anchor": report["anchor_id"], "worlds_checked": len(deltas),
            "retained_additions": r,
            "enclosure": {"lower": str(lower), "upper": str(upper)},
            "matcher_invoked": False,
            "establishes": "the arithmetic of this comparison inside the declared interpretations",
            "does_not_establish": ["that the declared interpretations are the right ones",
                                   "that the graph reflects the recording",
                                   "that the population is the intended one",
                                   "any physical, planner or risk consequence"]}


def main(argv):
    if len(argv) != 3:
        sys.stderr.write("usage: check_decision_packet.py CASE.json REPORT.json\n")
        return 2
    try:
        outcome = verify(load(argv[1]), load(argv[2]))
    except (Rejected, KeyError, TypeError, IndexError, ValueError) as error:
        sys.stderr.write(f"REJECTED: {error}\n")
        return 1
    json.dump({"result": "confirmed", **outcome}, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
