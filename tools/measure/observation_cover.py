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

TWO CORRECTIONS, 0.2.0.

An open reference does not by itself mean the decision is waiting. Version 0.1.0
reported `waits_on_a_reference` whenever an anchor was open, including a cohort
whose improvement criterion was already `supported` across the whole open
interval. That was wrong: nothing is waiting when the criterion is already
determined, and saying otherwise sends a lead to look for evidence that cannot
change the answer. The criterion is now read first, and an open reference is
preserved without being turned into an outstanding question.

A searched optimum is not a certificate. Version 0.1.0 called every case with a
shortest list `covered` and then counted `covered` as certified, which promoted
8 of 386 searched optima into certificate results. The state now names which of
the two it is: `certified_shortest` when the packing meets the cover, and
`searched_shortest` when only an exhaustive search says so.

When an open interval is present and the criterion is unresolved, the atoms of the
admitted readings do not determine it, because the open contribution can still move
the value after every atom is settled. No determining list is offered there. What is
reported instead is whether the readings would still disagree at the least and most
favourable open values, so a lead is told whether settling the reference alone could
be enough. That is the live Engine comparison's state and it is reported, not repaired.

Exact rational arithmetic, standard library only, no data read.
"""
from fractions import Fraction
from itertools import combinations
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cohort_packet import CaseError, build  # noqa: E402

VERSION = "0.2.0"
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


def _base(report):
    return {"artifact_id": "reiyah.observation-cover.report", "version": VERSION,
            "cohort_id": report["cohort_id"],
            "improvement_criterion": report["decision"].get("improvement_criterion"),
            "preference": report["decision"].get("preference"),
            "packet_state": report.get("state"),
            "open_anchors": [a["id"] for a in report["anchors"]
                             if a["reference_state"] == "open"],
            "disputed_atoms": None, "observation_list": None}


def analyse(case):
    """The observation list for one cohort, with both sides of its certificate."""
    report, rows = readings(case)
    result = _base(report)
    criterion = result["improvement_criterion"]
    low = Fraction(report["open_contribution"]["lower"])
    high = Fraction(report["open_contribution"]["upper"])

    if report.get("enclosure") is None:
        result["state"] = "not_evaluated"
        result["reason"] = report.get("reason", "the cohort itself is not evaluated")
        return result

    if criterion in ("supported", "excluded"):
        # Nothing is waiting. This holds across the whole open interval, because the
        # criterion was read from the enclosure that already contains it.
        result["state"] = "already_decided"
        result["reason"] = (f"the improvement criterion is {criterion} over the whole enclosure "
                            f"{report['enclosure']['lower']} to {report['enclosure']['upper']}, "
                            "so no further observation changes it")
        result["settles"] = {
            "the_improvement_criterion": criterion,
            "the_preference_output": result["preference"],
            "note": ("a settled criterion is not physical certainty and is not the preference "
                     "output. The preference can remain unresolved while the criterion is not")}
        if result["open_anchors"]:
            result["open_reference_preserved"] = {
                "anchors": result["open_anchors"],
                "contribution": {"lower": str(low), "upper": str(high)},
                "note": ("these references stay open. The decision does not wait on them because "
                         "their whole interval is already inside the criterion")}
        if rows:
            all_atoms = set().union(*(row["atoms"] for row in rows))
            agreed = set.intersection(*(row["atoms"] for row in rows))
            disputed = sorted(all_atoms - agreed)
            result["disputed_atoms"] = {
                "count": len(disputed), "atoms": disputed,
                "basis": "the diff a conventional analyst gets from the same readings"}
        result["observation_list"] = {"count": 0, "atoms": [], "certified_shortest": True,
                                      "lower_bound": 0,
                                      "lower_bound_basis": "the criterion is already determined"}
        return result

    if low != high:
        # Unresolved with an open interval. The atoms cannot determine the criterion,
        # because the open contribution still moves the value after they are settled.
        result["state"] = "waits_on_a_reference"
        result["reason"] = ("an open anchor contributes a count interval no reading can narrow, "
                            "and the criterion is unresolved. The decision waits on a reference "
                            "at these anchors")
        tolerance = Fraction(report["loss"]["tolerance"])
        finite = [Fraction(w["finite_contribution"]) for w in report["joint_worlds"]]
        def disagree(shift):
            verdicts = {_verdict(value + shift, tolerance) for value in finite}
            return len(verdicts) > 1
        result["reference_alone_may_not_settle_it"] = {
            "admitted_readings": len(finite),
            "readings_disagree_at_the_least_favourable_open_value": bool(finite) and disagree(low),
            "readings_disagree_at_the_most_favourable_open_value": bool(finite) and disagree(high),
            "note": ("if either is true, settling the reference can still leave the criterion "
                     "open, and the readings would have to be settled as well")}
        return result

    if not rows:
        result["state"] = "no_admitted_reading"
        result["reason"] = "no joint world is admitted, so no reading fact exists to settle"
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
        # Unresolved with no discordant pair cannot happen on a closed reference; the
        # criterion would be the readings' common verdict. Refuse rather than explain it away.
        raise CaseError("the criterion is unresolved with a closed reference and no discordant "
                        "reading pair, which the equivalence forbids")

    pack = packing(sets)
    greedy = greedy_cover(sets)
    lower = len(pack)
    if len(greedy) == lower:
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
        entry.update({"count": None, "atoms": None, "certified_shortest": False, "search": basis})
        result["state"] = "bracketed"
    else:
        certified = len(cover) == lower
        entry.update({"count": len(cover), "atoms": cover, "search": basis,
                      "certified_shortest": certified, "gap": len(cover) - lower,
                      "shortening_against_the_diff": {
                          "disputed": len(disputed), "certified_list": len(cover),
                          "ratio": (None if not disputed
                                    else str(Fraction(len(cover), len(disputed))))}})
        # A searched optimum and a certificate are different results and are named apart.
        result["state"] = "certified_shortest" if certified else "searched_shortest"
    result["observation_list"] = entry
    result["reason"] = {
        "certified_shortest": (f"{len(cover) if cover else 0} atoms meet every separating set and "
                               f"a packing of {lower} disjoint separating sets forces that length, "
                               "so no shorter list exists"),
        "searched_shortest": (f"an exhaustive search over smaller sizes found no list shorter than "
                              f"{len(cover) if cover else 0}, but the packing only forces {lower}. "
                              "This is a searched optimum and not a minimum size certificate"),
        "bracketed": (f"the candidate atoms exceed the search budget of {SEARCH_BUDGET}, so the "
                      f"shortest list is bracketed between the packing bound {lower} and the "
                      f"exhibited cover of {len(greedy)}"),
    }[result["state"]]
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
