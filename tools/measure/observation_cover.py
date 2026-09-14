"""Which observations the decision actually waits on.

The enclosure answers "supported, excluded or unresolved". When it is unresolved
it does not yet say what a perception validation lead should go and look at. The
naive answer is the whole disputed set: every presence and every admitted edge
that the readings do not agree on. That list is free, since an analyst holding
the same readings gets it by diffing them, and on a real cohort it is long.

This module computes a shorter list and certifies it.

  ATOM        one reading fact at one anchor: an object is present, or a named
              detection could have matched a named object.
  DISPUTED    an atom the admitted readings do not agree on.
  SEPARATING  for two readings with opposite verdicts, the atoms where they differ.
              At least one of those atoms has to be settled, whatever else is.
  COVER       a set of atoms meeting every separating set. Settle those and the
              verdict is fixed for every admitted reading, no matter how the rest
              of the disputed atoms fall.

So the shortest observation list is a minimum hitting set over the separating
sets of discordant reading pairs. That is the same shape of problem as the
matching already certified in this lane, and it carries the same kind of
two sided certificate:

  UPPER   a cover, checked in linear time by hitting every separating set.
  LOWER   a family of pairwise disjoint separating sets. Every cover must spend
          at least one atom inside each of them, so a packing of size k forces
          every cover to have size at least k.

When the two meet, the list is proved shortest and no search runs at all. That is
the case worth having, because it survives a disputed set far past any budget an
exact search could afford.

When a cover of size k meets a packing of size k, the list is proved shortest and
no search has to be trusted. When it does not, the gap is reported as a gap. The
bound is not tightened by assertion and the search is not presented as a proof.

WHAT THIS IS NOT. The cover is a function of the admitted readings, so a
conventional analyst holding those readings could compute it too. Nothing here is
inaccessible to them. What is measured is how much shorter the certified list is
than the disputed set they get by diffing, and whether the shortness can be
checked without rerunning the search.

An anchor with an open reference is not covered by any reading, so a cohort with
an open anchor whose count interval spans the tolerance is reported as waiting on
a reference rather than on an atom. That is the live Engine comparison's state
and it is reported, not repaired.

Exact rational arithmetic, standard library only, no data read.
"""
from fractions import Fraction
from itertools import combinations
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cohort_packet import CaseError, build  # noqa: E402

VERSION = "0.1.0"
SEARCH_BUDGET = 22


def atoms_of(world):
    """Every reading fact this world asserts, as sorted stable strings."""
    facts = set()
    for entry in world["anchors"]:
        anchor = entry["anchor"]
        for name in entry["objects_present"]:
            facts.add(f"{anchor}|present|{name}")
        for detection, obj in entry["edges"]:
            facts.add(f"{anchor}|edge|{detection}|{obj}")
    return facts


def _verdict(value, tolerance):
    return "supported" if value > tolerance else "excluded"


def readings(case):
    """One conventional verdict per admitted reading, with its reading facts."""
    report = build(case)
    tolerance = Fraction(report["loss"]["tolerance"])
    low = Fraction(report["open_contribution"]["lower"])
    rows = []
    for world in report["joint_worlds"]:
        value = Fraction(world["finite_contribution"]) + low
        rows.append({"world_id": world["world_id"], "value": value,
                     "verdict": _verdict(value, tolerance), "atoms": atoms_of(world)})
    return report, rows


def separating_sets(rows):
    """The atoms that distinguish each pair of readings with opposite verdicts."""
    out = []
    for left, right in combinations(range(len(rows)), 2):
        if rows[left]["verdict"] == rows[right]["verdict"]:
            continue
        difference = rows[left]["atoms"] ^ rows[right]["atoms"]
        out.append({"worlds": [rows[left]["world_id"], rows[right]["world_id"]],
                    "atoms": difference})
    return out


def packing(sets):
    """A pairwise disjoint subfamily. Its size lower bounds every cover."""
    chosen, used = [], set()
    for entry in sorted(sets, key=lambda s: (len(s["atoms"]), s["worlds"])):
        if entry["atoms"] & used:
            continue
        chosen.append(entry)
        used |= entry["atoms"]
    return chosen


def greedy_cover(sets):
    """A cover built by always taking an atom that meets the most unmet sets.

    It is a cover, so it is checked in linear time like any other, and it exists
    at every size. It is not claimed to be shortest. Reported together with the
    packing bound it brackets the shortest list between two checkable numbers.
    """
    remaining = [set(entry["atoms"]) for entry in sets]
    chosen = []
    while remaining:
        counts = {}
        for family in remaining:
            for atom in family:
                counts[atom] = counts.get(atom, 0) + 1
        atom = min(counts, key=lambda name: (-counts[name], name))
        chosen.append(atom)
        remaining = [family for family in remaining if atom not in family]
    return sorted(chosen)


def smallest_cover(sets, universe):
    """A shortest set of atoms meeting every separating set, or a budget refusal."""
    if not sets:
        return [], "no discordant reading pair, so nothing has to be settled"
    candidates = sorted(set().union(*(s["atoms"] for s in sets)) & universe)
    if len(candidates) > SEARCH_BUDGET:
        return None, (f"{len(candidates)} candidate atoms exceeds the search budget of "
                      f"{SEARCH_BUDGET}; no shortest cover is claimed")
    families = [s["atoms"] for s in sets]
    for size in range(1, len(candidates) + 1):
        for combination in combinations(candidates, size):
            picked = set(combination)
            if all(picked & family for family in families):
                return sorted(combination), "exhaustive over smaller sizes"
    return None, "no cover exists over the candidate atoms, which cannot happen if the sets are nonempty"


def analyse(case):
    """The observation list for one cohort, with both sides of its certificate."""
    report, rows = readings(case)
    result = {"artifact_id": "reiyah.observation-cover.report", "version": VERSION,
              "cohort_id": report["cohort_id"],
              "improvement_criterion": report["decision"].get("improvement_criterion"),
              "packet_state": report.get("state")}

    open_anchors = [a["id"] for a in report["anchors"] if a["reference_state"] == "open"]
    low = Fraction(report["open_contribution"]["lower"])
    high = Fraction(report["open_contribution"]["upper"])
    if open_anchors and low != high:
        result["state"] = "waits_on_a_reference"
        result["open_anchors"] = open_anchors
        result["reason"] = ("an open anchor contributes a count interval no reading can narrow. "
                            "The decision waits on a reference at these anchors, not on any "
                            "atom of an admitted reading")
        result["disputed_atoms"] = None
        result["observation_list"] = None
        return result
    if not rows:
        result["state"] = "no_admitted_reading"
        result["reason"] = "no joint world is admitted, so no reading fact exists to settle"
        result["disputed_atoms"] = None
        result["observation_list"] = None
        return result

    all_atoms = set().union(*(row["atoms"] for row in rows))
    agreed = set.intersection(*(row["atoms"] for row in rows))
    disputed = sorted(all_atoms - agreed)
    sets = separating_sets(rows)
    result["readings"] = [{"world_id": r["world_id"], "value": str(r["value"]),
                           "verdict": r["verdict"]} for r in rows]
    result["disputed_atoms"] = {"count": len(disputed), "atoms": disputed,
                                "basis": "the diff a conventional analyst gets from the same readings"}

    if not sets:
        result["state"] = "already_decided"
        result["reason"] = ("every admitted reading gives the same verdict, so no observation "
                            "changes the decision. The disputed atoms are free to remain disputed")
        result["observation_list"] = {"count": 0, "atoms": [], "certified_shortest": True,
                                      "lower_bound": 0, "lower_bound_basis": "no discordant pair"}
        return result

    pack = packing(sets)
    greedy = greedy_cover(sets)
    lower = len(pack)
    if len(greedy) == lower:
        # The packing already forces this length, so the search would only confirm it.
        cover, basis = greedy, "not searched; the greedy cover meets the packing bound"
    else:
        cover, basis = smallest_cover(sets, all_atoms)
    entry = {"lower_bound": lower,
             "lower_bound_basis": (f"{lower} pairwise disjoint separating sets, each of which "
                                   "every cover must spend an atom inside"),
             "packing": [{"worlds": p["worlds"], "atoms": sorted(p["atoms"])} for p in pack],
             "separating_sets": [{"worlds": s["worlds"], "atoms": sorted(s["atoms"])} for s in sets],
             "checkable_cover": {"count": len(greedy), "atoms": greedy,
                                 "basis": "greedy, a cover and nothing more"},
             "bracket": {"lower": lower, "upper": len(greedy)}}
    if cover is None:
        entry.update({"count": None, "atoms": None, "certified_shortest": False,
                      "search": basis})
        result["state"] = "bracketed"
    else:
        entry.update({"count": len(cover), "atoms": cover, "search": basis,
                      "certified_shortest": len(cover) == lower})
        result["state"] = "covered"
        entry["gap"] = len(cover) - lower
        entry["shortening_against_the_diff"] = {
            "disputed": len(disputed), "certified_list": len(cover),
            "ratio": (None if not disputed else str(Fraction(len(cover), len(disputed))))}
    result["observation_list"] = entry
    result["scope"] = ("the admitted readings only. Settling the listed atoms fixes the verdict "
                       "across those readings; it says nothing about a reading nobody admitted, "
                       "and it is not a physical measurement plan")
    return result


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: observation_cover.py CASE.json\n")
        return 2
    with open(argv[1], "r", encoding="utf-8") as handle:
        case = json.load(handle)
    try:
        result = analyse(case)
    except CaseError as error:
        sys.stderr.write(f"case refused: {error}\n")
        return 1
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
