"""Independent checker for an observation list.

Imports nothing from the producer, runs no search and computes no matching. It
reads the case bytes, the cohort packet report and the observation report, and
establishes exactly this:

  READINGS     each reported verdict follows from the packet's own per world
               certificates and the declared tolerance, not from a stored string.
  ATOMS        the disputed set is the one the case bytes actually support.
  SEPARATION   every pair of readings with opposite verdicts appears, and each
               reported separating set is exactly where those two readings differ.
  COVER        the reported list meets every separating set, so settling it fixes
               the verdict across the admitted readings.
  LOWER BOUND  the reported packing members are genuine separating sets and are
               pairwise disjoint, so no list shorter than the packing exists.
  SHORTEST     a claim of shortest is accepted only when the cover and the packing
               have the same size. A search is never taken as evidence.

What it refuses, by name: a cover that misses a separating set, a packing whose
members overlap, a packing member that is not a real separating set, a discordant
pair left out of the report, a verdict that the packet's certificates do not give,
an atom that no reading asserts, and a shortest claim the packing does not force.

What it cannot establish: that the admitted readings are the right readings, that
any of them is physically true, or that settling an atom is practically possible.

Shared trusted surface with the producer: the JSON module, Python's Fraction and
integer arithmetic, and the atom string convention declared here. Nothing else.
"""
from fractions import Fraction
import json
import re
import sys

RATIONAL = re.compile(r"^-?(0|[1-9][0-9]*)(/[1-9][0-9]*)?$")


class Rejected(Exception):
    """The observation list does not establish its result."""


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


def rational(text, what):
    if not isinstance(text, str) or not RATIONAL.match(text):
        raise Rejected(f"{what} is not an exact rational: {text!r}")
    return Fraction(text)


def atoms_from_packet_world(world):
    """The reading facts a packet world asserts, recomputed from its own entries."""
    facts = set()
    for entry in world.get("anchors", []):
        anchor = entry.get("anchor")
        if not isinstance(anchor, str):
            raise Rejected("a packet world entry has no anchor name")
        for name in entry.get("objects_present", []):
            if not isinstance(name, str):
                raise Rejected("a present object is not a name")
            facts.add(f"{anchor}|present|{name}")
        for edge in entry.get("edges", []):
            if not isinstance(edge, list) or len(edge) != 2:
                raise Rejected("a packet world edge is malformed")
            facts.add(f"{anchor}|edge|{edge[0]}|{edge[1]}")
    return facts


def world_value(world, packet):
    """Recompute the world's finite contribution from the reported certificates."""
    a = rational(packet["loss"]["false_negative"], "false_negative")
    b = rational(packet["loss"]["false_positive"], "false_positive")
    weights = {row["id"]: rational(row["weight"], "weight") for row in packet["anchors"]}
    retained = {row["id"]: row["retained_additions"] for row in packet["anchors"]}
    total = Fraction(0)
    for entry in world["anchors"]:
        anchor = entry["anchor"]
        if anchor not in weights:
            raise Rejected(f"world names anchor {anchor} which the packet does not declare")
        base = len(entry["base_certificate"]["matching"])
        augmented = len(entry["augmented_certificate"]["matching"])
        if base != entry["tp_base"] or augmented != entry["tp_augmented"]:
            raise Rejected(f"anchor {anchor} reports a count its own certificate does not show")
        gain = augmented - base
        r = retained[anchor]
        if not 0 <= gain <= r:
            raise Rejected(f"anchor {anchor} reports a gain outside 0..r")
        total += weights[anchor] * ((a + b) * gain - b * r)
    if str(total) != world["finite_contribution"]:
        raise Rejected(f"world {world['world_id']} reports {world['finite_contribution']} "
                       f"but its certificates give {total}")
    return total


def verify(packet, report):
    """Establish the observation list, or raise Rejected naming the violated property."""
    if report.get("artifact_id") != "reiyah.observation-cover.report":
        raise Rejected("unexpected artifact_id")
    if report.get("cohort_id") != packet.get("cohort_id"):
        raise Rejected("the observation report and the packet name different cohorts")
    state = report.get("state")
    if state not in ("waits_on_a_reference", "no_admitted_reading", "already_decided",
                     "covered", "bracketed"):
        raise Rejected(f"unknown state {state!r}")

    open_low = rational(packet["open_contribution"]["lower"], "open lower")
    open_high = rational(packet["open_contribution"]["upper"], "open upper")
    if state == "waits_on_a_reference":
        if open_low == open_high:
            raise Rejected("a reference is claimed to be waited on while no open anchor "
                           "contributes an interval")
        return {"state": state, "established": ["an open anchor leaves an interval no reading narrows"]}
    if open_low != open_high:
        raise Rejected("an open interval is present yet the report does not wait on a reference")

    tolerance = rational(packet["loss"]["tolerance"], "tolerance")
    worlds = packet.get("joint_worlds", [])
    if state == "no_admitted_reading":
        if worlds:
            raise Rejected("no admitted reading is claimed while the packet reports worlds")
        return {"state": state, "established": ["the packet admits no reading"]}
    if not worlds:
        raise Rejected("the packet admits no reading yet a list is reported")

    seen, rows = set(), []
    for world in worlds:
        name = world["world_id"]
        if name in seen:
            raise Rejected(f"world {name} appears twice")
        seen.add(name)
        value = world_value(world, packet) + open_low
        rows.append({"world_id": name, "verdict": "supported" if value > tolerance else "excluded",
                     "atoms": atoms_from_packet_world(world)})
    by_name = {row["world_id"]: row for row in rows}

    for row in report.get("readings", []):
        mine = by_name.get(row["world_id"])
        if mine is None:
            raise Rejected(f"report names world {row['world_id']} which the packet does not")
        if row["verdict"] != mine["verdict"]:
            raise Rejected(f"world {row['world_id']} is reported {row['verdict']} but its own "
                           f"certificates give {mine['verdict']}")

    all_atoms = set().union(*(row["atoms"] for row in rows))
    agreed = set.intersection(*(row["atoms"] for row in rows))
    disputed = all_atoms - agreed
    declared = report.get("disputed_atoms") or {}
    if set(declared.get("atoms") or []) != disputed:
        raise Rejected("the reported disputed set is not the one the readings support")
    if declared.get("count") != len(disputed):
        raise Rejected("the disputed count does not match its own list")

    required = {}
    for left in range(len(rows)):
        for right in range(left + 1, len(rows)):
            if rows[left]["verdict"] == rows[right]["verdict"]:
                continue
            key = (rows[left]["world_id"], rows[right]["world_id"])
            required[key] = rows[left]["atoms"] ^ rows[right]["atoms"]

    listing = report.get("observation_list") or {}
    if state == "already_decided":
        if required:
            raise Rejected("the decision is claimed settled while readings disagree")
        if listing.get("count") not in (0, None) or listing.get("atoms"):
            raise Rejected("a settled decision reports a nonempty list")
        return {"state": state, "readings": len(rows), "disputed": len(disputed),
                "established": ["every admitted reading gives the same verdict"]}
    if not required:
        raise Rejected("a list is reported while every reading agrees")

    reported_sets = {}
    for entry in listing.get("separating_sets", []):
        key = tuple(entry["worlds"])
        if key in reported_sets:
            raise Rejected(f"separating set {key} is reported twice")
        reported_sets[key] = set(entry["atoms"])
    if set(reported_sets) != set(required):
        missing = sorted(set(required) - set(reported_sets))
        extra = sorted(set(reported_sets) - set(required))
        raise Rejected(f"discordant pairs missing {missing}, unsupported pairs reported {extra}")
    for key, atoms in reported_sets.items():
        if atoms != required[key]:
            raise Rejected(f"separating set {key} is not where those readings differ")

    pack = [set(entry["atoms"]) for entry in listing.get("packing", [])]
    names = [tuple(entry["worlds"]) for entry in listing.get("packing", [])]
    for index, (atoms, key) in enumerate(zip(pack, names)):
        if key not in required or atoms != required[key]:
            raise Rejected(f"packing member {key} is not a genuine separating set")
        for other in pack[:index]:
            if atoms & other:
                raise Rejected("packing members overlap, so they force no bound")
    lower = len(pack)
    if listing.get("lower_bound") != lower:
        raise Rejected("the reported lower bound is not the size of its own packing")

    checkable = listing.get("checkable_cover") or {}
    for label, atoms in (("checkable_cover", set(checkable.get("atoms") or [])),
                         ("observation_list", set(listing.get("atoms") or []))):
        if label == "observation_list" and listing.get("atoms") is None:
            continue
        if not atoms <= all_atoms:
            raise Rejected(f"{label} names an atom no reading asserts")
        for key, family in required.items():
            if not atoms & family:
                raise Rejected(f"{label} misses the separating set {key}, so settling it "
                               "leaves the verdict open")
    if checkable.get("count") != len(set(checkable.get("atoms") or [])):
        raise Rejected("the checkable cover count does not match its own list")

    if state == "covered":
        cover = listing.get("atoms")
        if cover is None:
            raise Rejected("state covered reports no list")
        if listing.get("count") != len(set(cover)):
            raise Rejected("the list count does not match its own list")
        if listing.get("certified_shortest") and len(set(cover)) != lower:
            raise Rejected("shortest is claimed without a packing of the same size")
        if listing.get("gap") != len(set(cover)) - lower:
            raise Rejected("the reported gap is not cover size minus packing size")
    else:
        if listing.get("atoms") is not None or listing.get("certified_shortest"):
            raise Rejected("state bracketed reports a shortest list")

    bracket = listing.get("bracket") or {}
    if bracket.get("lower") != lower or bracket.get("upper") != checkable.get("count"):
        raise Rejected("the bracket does not match the packing and the checkable cover")
    if bracket["lower"] > bracket["upper"]:
        raise Rejected("the bracket is inverted")

    return {"state": state, "readings": len(rows), "disputed": len(disputed),
            "discordant_pairs": len(required), "lower_bound": lower,
            "checkable_cover": checkable.get("count"),
            "certified_shortest": bool(listing.get("certified_shortest")),
            "established": [
                "every reported verdict follows from the packet's own certificates",
                "the disputed set is the one the readings support",
                "every discordant pair appears with its exact separating set",
                "the reported lists meet every separating set",
                "the packing is disjoint, so no shorter list exists than its size"]}


def main(argv):
    if len(argv) != 3:
        sys.stderr.write("usage: check_observation_cover.py PACKET.json COVER.json\n")
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
