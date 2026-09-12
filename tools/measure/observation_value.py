"""Which observations can change the decision, computed exactly.

A comparison with several admitted joint interpretations is unresolved because the
reviewer does not yet know which one holds. Not every unknown matters. Some
uncertainty cancels: a disputed object neither configuration can match adds one
miss to both and leaves the difference alone, so resolving it cannot move the
enclosure by a single step. Other uncertainty is decisive: a disputed object
reachable only by the base reallocates the matching and flips the sign.

This module separates the two, before any observation is made.

For an atomic question "is object o present at anchor a", the admitted worlds
split into the cells where it is present and where it is absent. Resolving the
question means learning the cell. The question is classified by comparing the
cell enclosures with the enclosure over all worlds:

  decisive        some cell decides the improvement criterion that the full set
                  leaves unresolved, so the observation can end the comparison
  narrowing       no cell decides, but some cell is strictly narrower
  inert           every cell has the identical enclosure; the observation cannot
                  change the decision or the interval at all

An inert question is a reviewer's time spent for nothing, and naming it in advance
is the point. The classification is exact and carries no prior, no sampling model
and no assumption about how likely a world is. It does not rank by probability,
because no probability over reference interpretations has been established here.

Standard library only, exact rational arithmetic, no data read, and no reference
interpretation invented: the questions come from the declared alternatives.
"""
from fractions import Fraction
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cohort_packet import CaseError, build  # noqa: E402

MAX_QUESTIONS = 4096


def enclosure_of(case, world_ids):
    """The enclosure over a named subset of the declared joint worlds."""
    subset = [w for w in case["joint_worlds"] if w["world_id"] in world_ids]
    trimmed = dict(case)
    trimmed["joint_worlds"] = subset
    report = build(trimmed)
    if report.get("enclosure") is None:
        return None, report.get("state")
    return ((Fraction(report["enclosure"]["lower"]),
             Fraction(report["enclosure"]["upper"])), report["decision"])


def atomic_questions(case):
    """Every declared 'is this object present at this anchor' question."""
    questions = []
    for anchor in case["anchors"]:
        if anchor.get("reference_state") != "finite":
            continue
        for entry in anchor.get("objects", []):
            present, absent = set(), set()
            for world in case["joint_worlds"]:
                side = world["per_anchor"].get(anchor["id"])
                if side is None:
                    continue
                if entry["id"] in side.get("objects_present", []):
                    present.add(world["world_id"])
                else:
                    absent.add(world["world_id"])
            if present and absent:
                questions.append({"anchor": anchor["id"], "object": entry["id"],
                                  "present_worlds": sorted(present),
                                  "absent_worlds": sorted(absent)})
            else:
                questions.append({"anchor": anchor["id"], "object": entry["id"],
                                  "present_worlds": sorted(present),
                                  "absent_worlds": sorted(absent),
                                  "already_settled": True})
    if len(questions) > MAX_QUESTIONS:
        raise CaseError("too many atomic questions")
    return questions


def classify(case):
    full = build(case)
    if full.get("enclosure") is None:
        return {"state": full.get("state"), "reason": full.get("reason"), "questions": []}
    low, high = Fraction(full["enclosure"]["lower"]), Fraction(full["enclosure"]["upper"])
    verdict = full["decision"]["improvement_criterion"]
    width = high - low

    rows = []
    for question in atomic_questions(case):
        if question.get("already_settled"):
            rows.append({**question, "classification": "already_settled",
                         "note": "this object has the same presence in every admitted world"})
            continue
        cells = {}
        decisive = False
        narrower = False
        identical = True
        for label, ids in (("present", question["present_worlds"]),
                           ("absent", question["absent_worlds"])):
            span, decision = enclosure_of(case, set(ids))
            cells[label] = {"enclosure": [str(span[0]), str(span[1])],
                            "width": str(span[1] - span[0]),
                            "improvement_criterion": decision["improvement_criterion"],
                            "preference": decision["preference"]}
            if verdict == "unresolved" and decision["improvement_criterion"] != "unresolved":
                decisive = True
            if span[1] - span[0] < width:
                narrower = True
            if (span[0], span[1]) != (low, high):
                identical = False
        rows.append({**question, "cells": cells,
                     "classification": ("decisive" if decisive else
                                        "narrowing" if narrower else
                                        "inert" if identical else "narrowing")})
    return {"state": full["state"],
            "enclosure": full["enclosure"], "width": str(width),
            "improvement_criterion": verdict, "preference": full["decision"]["preference"],
            "questions": rows}


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: observation_value.py CASE.json\n")
        return 2
    with open(argv[1], "r", encoding="utf-8") as handle:
        case = json.load(handle)
    try:
        result = classify(case)
    except CaseError as error:
        sys.stderr.write(f"case refused: {error}\n")
        return 3
    counts = {}
    for row in result["questions"]:
        counts[row["classification"]] = counts.get(row["classification"], 0) + 1
    report = {"artifact_id": "reiyah.observation-value.report", "version": "0.1.0",
              "cohort_id": case.get("cohort_id"), **result, "counts": counts,
              "ranking_basis": ("exact effect on the declared enclosure. No probability over "
                                "reference interpretations is used, because none has been "
                                "established; this is not an expected-value ordering"),
              "scope": ("the declared alternatives only. A question absent from the declared worlds "
                        "is not classified here, and discovering new alternatives is a separate "
                        "obligation this module does not discharge")}
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
