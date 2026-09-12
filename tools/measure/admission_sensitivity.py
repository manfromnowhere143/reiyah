"""How much of a verdict comes from the detectors, and how much from the admission.

The conventional comparator established that on a finite cohort this lane's
enclosure is exactly the conventional method run once per admitted reading. The
whole value of the instrument therefore rests on the set of admitted readings,
and nothing in this lane has ever said what makes that set valid. Every number
published here inherits the assumption. This measures what it carries.

MONOTONE ADMISSION. If the admitted set W is contained in W', the enclosure over
W is contained in the enclosure over W'. Immediate, since the enclosure is the
range of the world values plus a fixed open contribution, and a range over a
larger set contains the range over a smaller one.

THE ASYMMETRY THAT MATTERS. Removing admitted readings can only narrow the
enclosure, so it can only make a verdict MORE decisive: a `supported` stays
supported and an `excluded` stays excluded, while an `unresolved` may become
decided. Admitting one more reading can only widen, so it can only DESTROY a
decisive verdict, never create one. Therefore:

  a decisive verdict rests entirely on the claim that the admitted set is
  complete, and no evidence inside the cohort can support that claim;

  an unresolved verdict cannot be rescued by admitting more readings. It can only
  be settled by ruling readings out, which takes evidence, which is what the
  resolution plan is for.

The two kinds of answer rest on two different assumptions, and only one of them is
the kind an observation can discharge.

HOW MUCH IS ASSERTED. The coarse bound is the structural limit given the anchors,
the retained additions and the loss. It holds whatever anyone admits. The admitted
enclosure sits inside it, and the difference is the part of the possible answer
space eliminated by the choice of readings rather than by the detectors:

  asserted_share = ( (E_low - C_low) + (C_high - E_high) ) / ( C_high - C_low )

A share near one means the conclusion is mostly a consequence of whoever chose
the readings. This is reported for every cohort, including the ones this lane is
pleased with.

REQUIRED EXCLUSION. For a decisive verdict the report states the exact sentence
that must be true of every reading nobody admitted, and says whether the coarse
bound permits such a reading to exist. If it does, the verdict is only as strong
as the completeness claim, and the report says so in those words.

No reading is invented, admitted, ranked or excluded here. This program measures
the dependence; it does not discharge it.

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
MAX_WORLDS = 32


def enclosure_over(case, world_ids):
    """The enclosure and criterion over a subset of the admitted readings."""
    trimmed = dict(case)
    trimmed["joint_worlds"] = [w for w in case["joint_worlds"] if w["world_id"] in world_ids]
    report = build(trimmed)
    if report.get("enclosure") is None:
        return None
    return (Fraction(report["enclosure"]["lower"]), Fraction(report["enclosure"]["upper"]),
            report["decision"]["improvement_criterion"])


def analyse(case):
    report = build(case)
    if report.get("enclosure") is None:
        return {"artifact_id": "reiyah.admission-sensitivity.report", "version": VERSION,
                "state": report.get("state"), "reason": report.get("reason")}
    worlds = [w["world_id"] for w in case["joint_worlds"]]
    if len(worlds) > MAX_WORLDS:
        raise CaseError("too many admitted readings for an exhaustive sensitivity report")
    tolerance = Fraction(str(case["loss"]["tolerance"]))
    low = Fraction(report["enclosure"]["lower"])
    high = Fraction(report["enclosure"]["upper"])
    coarse_low = Fraction(report["coarse_bound"]["lower"])
    coarse_high = Fraction(report["coarse_bound"]["upper"])
    criterion = report["decision"]["improvement_criterion"]

    span = coarse_high - coarse_low
    asserted = ((low - coarse_low) + (coarse_high - high)) / span if span else Fraction(0)

    # Which admitted readings hold the endpoints up.
    load_bearing = []
    for name in worlds:
        without = enclosure_over(case, set(worlds) - {name})
        if without is None:
            continue
        load_bearing.append({
            "world_id": name,
            "enclosure_without_it": {"lower": str(without[0]), "upper": str(without[1])},
            "criterion_without_it": without[2],
            "moves_an_endpoint": without[0] != low or without[1] != high,
            "changes_the_verdict": without[2] != criterion})

    # Omission can only narrow, so it can only sharpen. Verified, not assumed.
    omission_can_weaken = any(
        entry["criterion_without_it"] == "unresolved" and criterion != "unresolved"
        for entry in load_bearing)

    if criterion == "supported":
        required = ("no admissible reading of this cohort has a value at or below the tolerance "
                    f"{tolerance}")
        permitted = coarse_low <= tolerance
        margin = low - tolerance
    elif criterion == "excluded":
        required = f"no admissible reading of this cohort has a value above the tolerance {tolerance}"
        permitted = coarse_high > tolerance
        margin = tolerance - high
    else:
        required = ("nothing. An unresolved verdict makes no claim about readings nobody "
                    "admitted, because admitting more of them cannot change it")
        permitted = None
        margin = None

    return {
        "artifact_id": "reiyah.admission-sensitivity.report", "version": VERSION,
        "cohort_id": report["cohort_id"],
        "admitted_readings": len(worlds),
        "enclosure": report["enclosure"],
        "criterion": criterion,
        "coarse_bound": report["coarse_bound"],
        "how_much_is_asserted": {
            "asserted_share": str(asserted),
            "meaning": ("the fraction of the structurally possible answer space eliminated by the "
                        "choice of admitted readings rather than by the detectors. The coarse "
                        "bound holds whatever anyone admits"),
            "eliminated_below": str(low - coarse_low),
            "eliminated_above": str(coarse_high - high)},
        "required_exclusion": {
            "statement": required,
            "such_a_reading_is_structurally_permitted": permitted,
            "margin_to_the_tolerance": str(margin) if margin is not None else None,
            "consequence": (
                "the verdict stands only if the admitted set is complete, and no evidence inside "
                "this cohort can establish that" if permitted else
                "the coarse bound rules such a reading out by itself, so the verdict does not "
                "depend on the admitted set being complete" if permitted is False else
                "no completeness claim is being made")},
        "load_bearing_readings": load_bearing,
        "omission_asymmetry": {
            "claim": ("removing admitted readings can only narrow the enclosure, so it can only "
                      "make a verdict more decisive. Admitting one more can only widen it, so it "
                      "can only destroy a decisive verdict, never create one"),
            "a_single_omission_weakened_the_verdict": omission_can_weaken,
            "note": ("if that flag is ever true, this claim is wrong and the defect is here, not "
                     "in the cohort")},
        "scope": ("the declared anchors, loss and admitted readings. This program measures how much "
                  "a verdict depends on the admission decision. It does not invent, admit, rank or "
                  "exclude any reading, and it cannot discharge the dependence it measures"),
    }


def monotone_admission_holds(case):
    """Check that a larger admitted set gives a containing enclosure, exhaustively."""
    worlds = [w["world_id"] for w in case["joint_worlds"]]
    if not worlds or len(worlds) > 8:
        return None
    for size in range(1, len(worlds) + 1):
        for smaller in combinations(worlds, size):
            inner = enclosure_over(case, set(smaller))
            if inner is None:
                continue
            for extra in worlds:
                if extra in smaller:
                    continue
                outer = enclosure_over(case, set(smaller) | {extra})
                if outer is None:
                    continue
                if not (outer[0] <= inner[0] and outer[1] >= inner[1]):
                    return False
    return True


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: admission_sensitivity.py CASE.json\n")
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
