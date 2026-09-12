"""Independent checker for a weighted cohort comparison.

Imports nothing from the producer and computes no matching. Every matching is at
most every vertex cover, so a matching and a cover of equal size force optimality
for any graph; that inequality is the whole verification apparatus.

What a confirmation establishes:

  every joint world covers exactly the finite anchors; at each anchor in each world
  both configurations are checked in that same world; the weighted sum is the
  declared per-world value; the enclosure is the range of those values widened by
  the declared open contribution; and the decision follows from the enclosure and
  the declared tolerance.

What it refuses, by name: a joint world that omits a finite anchor, an anchor
evaluated in a different world from its cohort, a reported enclosure narrower than
the worlds support, an open reference presented as a world with no objects, and a
separate per-anchor relaxation offered as the joint result.

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
CASE_KEYS = {"schema_id", "cohort_id", "label", "loss", "anchors", "joint_worlds"}
REPORT_KEYS = {"artifact_id", "version", "cohort_id", "loss", "anchors", "open_contribution",
               "joint_worlds", "decision", "enclosure", "coarse_bound", "state", "reason",
               "separate_anchor_relaxation", "scope"}


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
        raise Rejected(f"{what} is not an exact rational: {text!r}")
    return Fraction(text)


def only_known(body, allowed, what):
    if not isinstance(body, dict):
        raise Rejected(f"{what} is not an object")
    unknown = sorted(set(body) - allowed)
    if unknown:
        raise Rejected(f"{what} carries unknown fields: {unknown}")


def certify(certificate, edges, allowed, what):
    only_known(certificate, {"matching", "cover"}, what)
    matching = certificate.get("matching")
    if not isinstance(matching, list):
        raise Rejected(f"{what} has no matching")
    left, right = set(), set()
    for pair in matching:
        if not isinstance(pair, list) or len(pair) != 2:
            raise Rejected(f"{what} matching entry is malformed")
        detection, obj = ident(pair[0], "matched detection"), ident(pair[1], "matched object")
        if detection not in allowed:
            raise Rejected(f"{what} matches a detection not in this configuration")
        if (detection, obj) not in edges:
            raise Rejected(f"{what} matches a pair that is not an edge")
        if detection in left or obj in right:
            raise Rejected(f"{what} matching is not one to one")
        left.add(detection)
        right.add(obj)
    cover = certificate.get("cover")
    only_known(cover if isinstance(cover, dict) else {}, {"detections", "objects"}, f"{what} cover")
    cover_d = list(cover.get("detections", []))
    cover_o = list(cover.get("objects", []))
    if len(set(cover_d)) != len(cover_d) or len(set(cover_o)) != len(cover_o):
        raise Rejected(f"{what} cover repeats a vertex")
    cover_d, cover_o = set(cover_d), set(cover_o)
    for detection, obj in edges:
        if detection in allowed and detection not in cover_d and obj not in cover_o:
            raise Rejected(f"{what} cover misses an edge")
    if len(matching) != len(cover_d) + len(cover_o):
        raise Rejected(f"{what} matching and cover differ in size")
    return len(matching)


def verify(case, report):
    only_known(case, CASE_KEYS, "case")
    only_known(report, REPORT_KEYS, "report")
    if case.get("schema_id") != "reiyah.cohort-packet.case":
        raise Rejected("case schema_id is not the expected one")
    if report.get("cohort_id") != case.get("cohort_id"):
        raise Rejected("report cohort does not match the case")

    a = exact(case["loss"]["false_negative"], "fn", NONNEG)
    b = exact(case["loss"]["false_positive"], "fp", NONNEG)
    tolerance = exact(case["loss"]["tolerance"], "tolerance", NONNEG)
    for key, value in (("false_negative", a), ("false_positive", b), ("tolerance", tolerance)):
        if exact(report["loss"][key], f"report {key}", NONNEG) != value:
            raise Rejected(f"report {key} does not match the case")

    anchors, classes, objects = {}, {}, {}
    for entry in case.get("anchors", []):
        name = ident(entry.get("id", ""), "anchor id")
        if name in anchors:
            raise Rejected(f"anchor {name} declared twice")
        weight = exact(entry.get("weight", ""), f"weight of {name}", NONNEG)
        state = entry.get("reference_state")
        if state not in ("finite", "open"):
            raise Rejected(f"anchor {name} has no admissible reference_state")
        cls, base, added = {}, [], []
        for role, sink in (("base_detections", base), ("added_detections", added)):
            for row in entry.get(role, []):
                did = ident(row.get("id", ""), "detection id")
                if did in cls:
                    raise Rejected(f"anchor {name} declares detection {did} twice")
                cls[did] = ident(row.get("class", ""), "detection class")
                sink.append(did)
        objs = {}
        for row in entry.get("objects", []):
            oid = ident(row.get("id", ""), "object id")
            objs[oid] = ident(row.get("class", ""), "object class")
        if state == "open" and objs:
            raise Rejected(f"anchor {name} is open yet declares objects")
        anchors[name] = {"weight": weight, "state": state, "base": base, "added": added,
                         "r": len(added)}
        classes[name] = cls
        objects[name] = objs
    if sum(entry["weight"] for entry in anchors.values()) != 1:
        raise Rejected("anchor weights do not sum to 1")
    reported = {entry["id"]: entry for entry in report.get("anchors", [])}
    if set(reported) != set(anchors):
        raise Rejected("report anchors do not match the case anchors")
    for name, entry in anchors.items():
        if exact(reported[name]["weight"], "reported weight", NONNEG) != entry["weight"]:
            raise Rejected(f"reported weight for {name} is wrong")
        if reported[name]["reference_state"] != entry["state"]:
            raise Rejected(f"reported reference_state for {name} is wrong")
        if reported[name]["retained_additions"] != entry["r"]:
            raise Rejected(f"reported retained additions for {name} is wrong")

    finite = sorted(n for n, e in anchors.items() if e["state"] == "finite")
    open_low = sum((anchors[n]["weight"] * (-b * anchors[n]["r"])
                    for n in anchors if anchors[n]["state"] == "open"), Fraction(0))
    open_high = sum((anchors[n]["weight"] * (a * anchors[n]["r"])
                     for n in anchors if anchors[n]["state"] == "open"), Fraction(0))
    if (exact(report["open_contribution"]["lower"], "open lower") != open_low
            or exact(report["open_contribution"]["upper"], "open upper") != open_high):
        raise Rejected("open contribution does not equal the weighted count interval")

    case_worlds = {}
    for body in case.get("joint_worlds", []):
        name = ident(body.get("world_id", ""), "world_id")
        if name in case_worlds:
            raise Rejected(f"case repeats joint world {name}")
        case_worlds[name] = body

    if report.get("state") == "unresolved":
        if finite and case_worlds:
            raise Rejected("unresolved claimed while finite anchors have admitted worlds")
        return {"state": "unresolved", "worlds_checked": 0, "matcher_invoked": False,
                "note": "an unresolved cohort asserts nothing and is accepted as such"}

    worlds = report.get("joint_worlds")
    if not isinstance(worlds, list) or len(worlds) != len(case_worlds):
        raise Rejected("report does not cover exactly the declared joint worlds")
    values, seen = [], set()
    for entry in worlds:
        name = ident(entry.get("world_id", ""), "world_id")
        if name in seen or name not in case_worlds:
            raise Rejected(f"joint world {name} repeated or undeclared")
        seen.add(name)
        declared = case_worlds[name].get("per_anchor", {})
        if sorted(declared) != finite:
            raise Rejected(f"joint world {name} does not cover exactly the finite anchors")
        covered = [row["anchor"] for row in entry.get("anchors", [])]
        if sorted(covered) != finite:
            raise Rejected(f"report world {name} does not evaluate exactly the finite anchors")
        value = Fraction(0)
        for row in entry["anchors"]:
            name_a = ident(row["anchor"], "anchor")
            side = declared[name_a]
            present = [ident(v, "present object") for v in side.get("objects_present", [])]
            if row.get("objects_present") != present:
                raise Rejected(f"world {name} anchor {name_a} present objects differ from the case")
            edges = set()
            for pair in side.get("edges", []):
                d, o = ident(pair[0], "edge detection"), ident(pair[1], "edge object")
                if d not in classes[name_a]:
                    raise Rejected("edge names an undeclared detection")
                if o not in present:
                    raise Rejected("edge names an object not present")
                if classes[name_a][d] != objects[name_a].get(o):
                    raise Rejected("edge joins different classes")
                edges.add((d, o))
            if {tuple(p) for p in row.get("edges", [])} != edges:
                raise Rejected(f"world {name} anchor {name_a} edges differ from the case")
            entry_a = anchors[name_a]
            tp_base = certify(row.get("base_certificate", {}), edges, set(entry_a["base"]),
                              f"world {name} anchor {name_a} base")
            tp_aug = certify(row.get("augmented_certificate", {}), edges,
                             set(entry_a["base"]) | set(entry_a["added"]),
                             f"world {name} anchor {name_a} augmented")
            if row.get("tp_base") != tp_base or row.get("tp_augmented") != tp_aug:
                raise Rejected(f"world {name} anchor {name_a} states uncertified counts")
            gain = tp_aug - tp_base
            if not 0 <= gain <= entry_a["r"]:
                raise Rejected(f"world {name} anchor {name_a} violates 0 <= gain <= r")
            delta = (a + b) * gain - b * entry_a["r"]
            if exact(row.get("delta", ""), "anchor delta") != delta:
                raise Rejected(f"world {name} anchor {name_a} delta is wrong")
            value += entry_a["weight"] * delta
        if exact(entry.get("finite_contribution", ""), "world value") != value:
            raise Rejected(f"world {name} weighted value is wrong")
        values.append(value)

    if values:
        lower, upper = min(values) + open_low, max(values) + open_high
    else:
        lower, upper = open_low, open_high
    if (exact(report["enclosure"]["lower"], "enclosure lower") != lower
            or exact(report["enclosure"]["upper"], "enclosure upper") != upper):
        raise Rejected("enclosure is not the range the declared worlds support")
    decision = ("supported" if lower > tolerance else
                "excluded" if upper <= tolerance else "unresolved")
    if report["decision"]["improvement_criterion"] != decision:
        raise Rejected("improvement criterion does not follow from the enclosure")
    relaxation = report.get("separate_anchor_relaxation")
    if relaxation is not None:
        rlow = exact(relaxation["lower"], "relaxation lower")
        rhigh = exact(relaxation["upper"], "relaxation upper")
        if rlow > lower or rhigh < upper:
            raise Rejected("the separate relaxation is narrower than the joint enclosure, "
                           "which is impossible; a relaxation can only be wider or equal")
    return {"state": report.get("state"), "worlds_checked": len(values),
            "finite_anchors": len(finite), "matcher_invoked": False,
            "enclosure": {"lower": str(lower), "upper": str(upper)},
            "decision": decision,
            "establishes": "the joint weighted comparison inside the declared interpretations",
            "does_not_establish": ["that the declared interpretations are admitted by review",
                                   "that any object exists",
                                   "physical coverage, planner behaviour or risk"]}


def main(argv):
    if len(argv) != 3:
        sys.stderr.write("usage: check_cohort_packet.py CASE.json REPORT.json\n")
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
