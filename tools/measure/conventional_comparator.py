"""What a competent conventional analyst concludes from the same evidence.

This lane has repeatedly said that its instrument is worth having and has never
said, in a checkable way, what it is worth having *instead of*. That is the
question here, and it is asked so that the answer can come out unfavourable.

The comparator is not a straw man. It is given the same anchors, the same
detections, the same additive loss and the same tolerance. It differs in exactly
one respect, which is the respect in which conventional detection benchmarking
actually differs: it commits to a single reading of the reference and reports a
number. Two such readings are standard practice and both are implemented.

  complete_annotation   the annotation is true and complete. Anything the
                        detector reports that the annotation does not contain is
                        a false positive, and where the reference is absent that
                        means nothing is there.
  single_interpretation where several readings are admitted, take one and report
                        its point value.

Two results follow, and only one of them favours the instrument.

EQUIVALENCE. If every anchor is finite, the enclosure returns `unresolved`
exactly when the single-interpretation verdicts disagree across the admitted
worlds, and otherwise it returns their common verdict. So on a finite cohort the
instrument tells a conventional analyst nothing they could not have found by
running their own method once per admitted reading and comparing. What it adds is
that the comparison is made, and made by default. When the readings agree, the
instrument contributes confirmation and nothing else, and it should say so.

BIAS. If an anchor is open, the complete-annotation reading contributes exactly
`-b * r` there: every retained addition is counted as a false positive because
nothing is recorded to match it. That is not a neutral default. It is the most
adverse value the anchor can take, and it is reached by an assumption about
missing data rather than by a measurement of it. On a cohort whose anchors are
all open the reading equals the lower endpoint of the true bound exactly.

The first result limits the instrument's claim. The second is the case for it.
Both are computed here rather than asserted.

Exact rational arithmetic, standard library only, no data read. Imports
`cohort_packet` for the enclosure it is being compared against, and recomputes
the conventional readings itself.
"""
from fractions import Fraction
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cohort_packet import CaseError, build  # noqa: E402

VERSION = "0.1.0"


def _verdict(value, tolerance):
    """The same rule the enclosure uses, applied to a single number."""
    return "supported" if value > tolerance else "excluded"


def single_interpretation_readings(case):
    """One conventional point estimate per admitted reading, same loss, same tolerance."""
    report = build(case)
    tolerance = Fraction(str(case["loss"]["tolerance"]))
    open_low = Fraction(report["open_contribution"]["lower"])
    open_high = Fraction(report["open_contribution"]["upper"])
    readings = []
    for world in report["joint_worlds"]:
        finite = Fraction(world["finite_contribution"])
        readings.append({
            "world_id": world["world_id"],
            "finite_value": str(finite),
            "verdict": _verdict(finite + open_low, tolerance),
            "verdict_if_open_anchors_were_most_favourable": _verdict(finite + open_high, tolerance),
        })
    return readings


def complete_annotation_reading(case):
    """The analyst who treats the annotation as true and complete.

    Every anchor without a recorded object contributes `-b * r`: the additions
    there are counted as false positives because nothing is recorded to match.
    """
    report = build(case)
    b = Fraction(str(case["loss"]["false_positive"]))
    tolerance = Fraction(str(case["loss"]["tolerance"]))
    open_part = Fraction(0)
    open_anchors = []
    for anchor in report["anchors"]:
        if anchor["reference_state"] == "finite":
            continue
        weight = Fraction(anchor["weight"])
        open_part += weight * (-b * anchor["retained_additions"])
        open_anchors.append(anchor["id"])
    finite_values = [Fraction(w["finite_contribution"]) for w in report["joint_worlds"]]
    # Where readings are admitted the analyst still has to pick one. Both extremes
    # are reported so the choice is visible rather than hidden in a default.
    lowest = min(finite_values) if finite_values else Fraction(0)
    highest = max(finite_values) if finite_values else Fraction(0)
    return {
        "open_anchors_treated_as_empty": open_anchors,
        "contribution_from_treating_missing_as_empty": str(open_part),
        "value_with_the_least_favourable_admitted_reading": str(lowest + open_part),
        "value_with_the_most_favourable_admitted_reading": str(highest + open_part),
        "verdict_either_way": (_verdict(lowest + open_part, tolerance)
                               if _verdict(lowest + open_part, tolerance)
                               == _verdict(highest + open_part, tolerance) else "depends"),
        "equals_the_lower_endpoint_of_the_true_bound":
            str(lowest + open_part) == report["enclosure"]["lower"],
    }


def compare(case):
    """The instrument against the comparator, on one cohort."""
    report = build(case)
    if report.get("enclosure") is None:
        return {"artifact_id": "reiyah.conventional-comparator.report", "version": VERSION,
                "state": report.get("state"), "reason": report.get("reason"),
                "comparison": "not evaluated; the cohort itself is not evaluated"}
    criterion = report["decision"]["improvement_criterion"]
    readings = single_interpretation_readings(case)
    verdicts = sorted({r["verdict"] for r in readings})
    every_anchor_finite = all(a["reference_state"] == "finite" for a in report["anchors"])

    if not readings:
        agreement = "no admitted reading, so the conventional method has nothing to run"
        instrument_adds = ("the conventional method must still produce a number, and does so by "
                           "assuming what is missing. The instrument reports that nothing is known")
    elif len(verdicts) == 1:
        agreement = f"every admitted reading gives {verdicts[0]!r}"
        instrument_adds = ("confirmation only. A conventional analyst committing to any admitted "
                           "reading reaches the same verdict, and the enclosure agrees with it")
    else:
        agreement = "the admitted readings disagree: " + ", ".join(
            f"{r['world_id']}={r['verdict']}" for r in readings)
        instrument_adds = ("the conventional verdict here is decided by which reading is chosen, "
                           "not by the detectors. The enclosure reports that, and a single point "
                           "estimate cannot")

    result = {
        "artifact_id": "reiyah.conventional-comparator.report", "version": VERSION,
        "cohort_id": report["cohort_id"],
        "shared_with_the_comparator": ["the anchors", "the detections", "the additive loss",
                                       "the tolerance", "the admitted readings"],
        "instrument": {"enclosure": report["enclosure"], "improvement_criterion": criterion},
        "conventional_single_interpretation": {"readings": readings, "agreement": agreement},
        "conventional_complete_annotation": complete_annotation_reading(case),
        "what_the_instrument_adds": instrument_adds,
        "equivalence_applies": every_anchor_finite and bool(readings),
    }
    if result["equivalence_applies"]:
        expected = "unresolved" if len(verdicts) > 1 else verdicts[0]
        result["equivalence"] = {
            "claim": ("with every anchor finite, the criterion is unresolved exactly when the "
                      "single-interpretation verdicts disagree, and is their common verdict "
                      "otherwise"),
            "expected_criterion": expected,
            "observed_criterion": criterion,
            "holds": expected == criterion}
    else:
        result["equivalence"] = {
            "claim": "not applicable: the equivalence is stated only for a cohort whose anchors "
                     "are all finite and which admits at least one reading",
            "holds": None}
    return result


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: conventional_comparator.py CASE.json\n")
        return 2
    with open(argv[1], "r", encoding="utf-8") as handle:
        case = json.load(handle)
    try:
        result = compare(case)
    except CaseError as error:
        sys.stderr.write(f"case refused: {error}\n")
        return 1
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
