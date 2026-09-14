"""Independent checker for a claimed label dependence witness.

A report saying "six labels each carry the verdict" is worth nothing unless each
one can be checked without trusting the search that found it. Each witness is one
line of arithmetic away from being confirmed or refused, and this module does that
arithmetic itself.

Imports nothing from the producer. It parses the case, deletes the named label,
runs its own maximum matching, recomputes the declared loss, and compares the
criterion with the one the witness claims. A witness that does not flip the
criterion is refused by name.

  delta_i = (a + b) * (TP_augmented - TP_base) - b * r
  D       = sum_i weight_i * delta_i
  supported iff D > tolerance, excluded iff D <= tolerance on a point enclosure.

What it refuses: a witness whose deletion does not change the criterion, a witness
naming a label that is not there, a claimed baseline the case does not produce, a
count that does not match its own list, and a report whose claimed robustness is
contradicted by a witness it carries.

What it cannot establish: that any annotation is actually wrong, that a deletion
is the right correction, or anything at all about the physical scene. Deleting a
label is a hypothesis this checker evaluates, not evidence it accepts.

Shared trusted surface with the producer: the JSON module, Python's Fraction and
integer arithmetic. The matcher here is written separately.
"""
from fractions import Fraction
import json
import sys


class Rejected(Exception):
    """The label dependence claim does not hold."""


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


def matching_size(left, adjacency):
    """A maximum bipartite matching, by augmenting paths. No producer code."""
    assigned = {}

    def augment(node, seen):
        for other in adjacency.get(node, ()):
            if other in seen:
                continue
            seen.add(other)
            if other not in assigned or augment(assigned[other], seen):
                assigned[other] = node
                return True
        return False

    return sum(1 for node in left if augment(node, set()))


def decide(case, drop=None):
    """The declared decision on the case, optionally without one annotation."""
    loss = case["loss"]
    a = Fraction(loss["false_negative"])
    b = Fraction(loss["false_positive"])
    tolerance = Fraction(loss["tolerance"])
    worlds = case["joint_worlds"]
    if len(worlds) != 1:
        raise Rejected("this checker handles a single admitted reading, which is what a "
                       "benchmark annotation supplies")
    world = worlds[0]["per_anchor"]
    total = Fraction(0)
    per_anchor = {}
    for anchor in case["anchors"]:
        if anchor["reference_state"] != "finite":
            raise Rejected(f"anchor {anchor['id']} is not finite")
        weight = Fraction(anchor["weight"])
        body = world[anchor["id"]]
        removed = drop["object"] if drop and drop["anchor"] == anchor["id"] else None
        present = [o for o in body["objects_present"] if o != removed]
        if removed is not None and removed not in body["objects_present"]:
            raise Rejected(f"the witness names object index it cannot find at {anchor['id']}")
        base = [d["id"] for d in anchor["base_detections"]]
        added = [d["id"] for d in anchor["added_detections"]]
        allowed = set(present)
        adjacency = {}
        for detection, obj in body["edges"]:
            if obj in allowed:
                adjacency.setdefault(detection, []).append(obj)
        base_adjacency = {d: v for d, v in adjacency.items() if d in set(base)}
        tp_base = matching_size(sorted(base), base_adjacency)
        tp_all = matching_size(sorted(base + added), adjacency)
        r = len(added)
        delta = (a + b) * (tp_all - tp_base) - b * r
        total += weight * delta
        per_anchor[anchor["id"]] = {"tp_base": tp_base, "tp_augmented": tp_all,
                                    "delta": str(delta)}
    criterion = "supported" if total > tolerance else "excluded"
    return {"weighted_delta": str(total), "criterion": criterion, "per_anchor": per_anchor}


def object_at(case, anchor_id, local_index):
    for anchor in case["anchors"]:
        if anchor["id"] != anchor_id:
            continue
        objects = anchor["objects"]
        if not 0 <= local_index < len(objects):
            raise Rejected(f"local index {local_index} is outside {anchor_id}")
        return objects[local_index]["id"], objects[local_index]["class"]
    raise Rejected(f"no anchor named {anchor_id}")


def verify(case, report):
    """Establish every claimed witness, or raise Rejected naming the one that fails."""
    if report.get("artifact_id") != "reiyah.label-dependence.report":
        raise Rejected("unexpected artifact_id")
    baseline = decide(case)
    claimed = report.get("baseline") or {}
    if claimed.get("weighted_delta") != baseline["weighted_delta"]:
        raise Rejected(f"the report's baseline is {claimed.get('weighted_delta')} but the case "
                       f"gives {baseline['weighted_delta']}")
    if claimed.get("criterion") != baseline["criterion"]:
        raise Rejected("the report's baseline criterion is not the one the case gives")

    events = report.get("events") or {}
    crossings = events.get("tolerance_crossings") or []
    confirmed = []
    for witness in crossings:
        object_id, klass = object_at(case, witness["anchor"], witness["local_index"])
        if klass != witness["class"]:
            raise Rejected(f"witness at {witness['anchor']}[{witness['local_index']}] is a "
                           f"{klass}, not a {witness['class']}")
        outcome = decide(case, {"anchor": witness["anchor"], "object": object_id})
        if outcome["criterion"] == baseline["criterion"]:
            raise Rejected(f"witness at {witness['anchor']}[{witness['local_index']}] does not "
                           "change the criterion")
        if outcome["weighted_delta"] != witness["weighted_delta"]:
            raise Rejected(f"witness at {witness['anchor']}[{witness['local_index']}] reports "
                           f"{witness['weighted_delta']} but recomputes to "
                           f"{outcome['weighted_delta']}")
        confirmed.append({"anchor": witness["anchor"], "local_index": witness["local_index"],
                          "class": klass, "weighted_delta": outcome["weighted_delta"],
                          "criterion": outcome["criterion"]})
    if report.get("robust_under_this_family") and crossings:
        raise Rejected("the report claims robustness while carrying a witness against it")
    if report.get("breakdown_number") == 1 and not crossings:
        raise Rejected("a breakdown number of one is claimed with no witness")
    return {"baseline": baseline, "witnesses_confirmed": len(confirmed),
            "witnesses": confirmed,
            "established": [
                "the baseline verdict follows from the case under the declared loss",
                "every claimed witness changes the criterion when its label is deleted",
                "every witness reports the weighted delta this checker recomputes"],
            "not_established": [
                "that any annotation is wrong",
                "that a deletion is the right correction",
                "anything about the physical scene"]}


def main(argv):
    if len(argv) != 3:
        sys.stderr.write("usage: check_label_dependence.py CASE.json REPORT.json\n")
        return 2
    try:
        result = verify(load(argv[1]), load(argv[2]))
    except Rejected as error:
        sys.stderr.write(f"rejected: {error}\n")
        return 1
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
