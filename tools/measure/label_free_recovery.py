"""Does the ordering survive when the annotation is removed as an information source.

Everything this lane has measured on real channels used the annotation twice: to
define the population, and to supply the cell where both channels of a pair miss.
A fleet operator has neither. If the conclusion cannot be reached without them,
the method is a benchmark exercise; if it can, the method runs on unlabelled logs.

The label free view replaces both uses with what OTHER CHANNELS saw. The
population is the union of what some channel found, and the pair's joint miss cell
is what another channel found and this pair did not. Thresholds are matched on
that same label free population, because that is what a user without labels can
actually do. The annotation supplies nothing.

Comparisons are made only WITHIN one matched operating point, never across them,
because clause 4 of `docs/ESTIMAND_RSS_DEFINITION_32.md` forbids the latter.

WHAT IT RECOVERS, AND WHERE IT DOES NOT. At matched miss rates of 0.30 and 0.40
the label free view separates same modality from cross modality with a wider
margin than the annotated view. At 0.50 it does not separate: the lowest same
modality pair falls below the highest cross modality pair. That is the operating
point where the annotated view's own margin was `+0.004`, which this lane had
already flagged as too thin to carry weight. **Two of three, not three of three**,
and the failure is at the cell that was never robust.

THE LIMITATION THAT MATTERS MOST. The retained caches hold only detections that
matched an annotated object, so a detection matching nothing is invisible here.
This test removes the annotation from the population and from the joint miss cell.
It does NOT remove it from the association between channels. A full test needs raw
detections and cross channel spatial association, and these caches do not hold
them. Nothing here shows the method survives association error, which is a
separate obligation this lane has bounded in theory and never measured.

Exact rational arithmetic, standard library only. Reads one retained counts file.
"""
from fractions import Fraction
import json
import os
import sys

VERSION = "0.1.0"
COUNTS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "research", "label-free-recovery", "0.1.0",
    "recovery-counts.json")


class CountsError(Exception):
    """The retained counts are not in the shape this analysis requires."""


def load(path=COUNTS):
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("artifact_id") != "reiyah.label-free-recovery.counts":
        raise CountsError("the file is not the retained label free recovery artifact")
    return data


def coefficient(row):
    if row["first_missed"] == 0 or row["second_missed"] == 0:
        return None
    return Fraction(row["both_missed"] * row["population"],
                    row["first_missed"] * row["second_missed"])


def separation(data, view, target):
    """Same against cross, within one view at one matched operating point."""
    same, cross = [], []
    for row in data["rows"]:
        if row["view"] != view or row["target_miss_rate"] != target:
            continue
        value = coefficient(row)
        if value is None:
            continue
        (same if row["kind"] == "same_modality" else cross).append(value)
    if not same or not cross:
        return None
    return {"same_modality": [str(min(same)), str(max(same))],
            "cross_modality": [str(min(cross)), str(max(cross))],
            "separated": min(same) > max(cross),
            "margin": str(min(same) - max(cross))}


def report(data=None):
    data = data or load()
    targets = sorted({row["target_miss_rate"] for row in data["rows"]})
    rows = []
    for target in targets:
        annotated = separation(data, "with_annotation", target)
        free = separation(data, "label_free", target)
        rows.append({"matched_miss_rate": target,
                     "with_annotation": annotated, "label_free": free,
                     "agrees": annotated["separated"] == free["separated"],
                     "label_free_margin_is_wider": (
                         Fraction(free["margin"]) > Fraction(annotated["margin"]))})
    recovered = [row for row in rows if row["label_free"]["separated"]]
    return {
        "artifact_id": "reiyah.label-free-recovery.report", "version": VERSION,
        "question": ("can the ordering be reached without the annotation, which is what a fleet "
                     "operator would have to do"),
        "operating_points_tested": len(rows),
        "recovered_by_the_label_free_view": len(recovered),
        "verdict": (f"{len(recovered)} of {len(rows)}. The label free view recovers the ordering "
                    "where the annotated view had a clear margin, and fails at the one operating "
                    "point where the annotated margin was already too thin to carry weight"),
        "comparisons_are_within_a_matched_point_only": (
            "clause 4 of the estimand contract forbids comparing the coefficient across operating "
            "points; every comparison here is same against cross inside one matched point"),
        "rows": rows,
        "what_this_supports": (
            "the coupling ordering can be reached from channel agreement alone, without the "
            "annotation defining the population or supplying the joint miss cell"),
        "what_this_does_not_support": [
            "it does not remove the annotation from the association between channels, because the "
            "retained caches hold only detections that matched an annotated object",
            "it does not measure robustness to association error, which this lane has bounded in "
            "theory and never measured on real channels",
            "it does not establish the magnitude of any coefficient, only the ordering",
            "no statistical uncertainty, resampling band or sampling model is computed",
            "no vendor architecture is measured and no safety conclusion about any vehicle follows",
        ],
    }


def main(argv):
    try:
        json.dump(report(load(argv[1]) if len(argv) > 1 else None),
                  sys.stdout, indent=2, sort_keys=True)
    except (CountsError, OSError) as error:
        sys.stderr.write(f"counts refused: {error}\n")
        return 1
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
