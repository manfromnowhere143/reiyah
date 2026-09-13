"""What the original rows decide about an integration choice, which is not much.

This consumes the Engine's `original-predictions-0.1.0` packet: 4,876 submitted
rows over 16 already exposed development frames, every row carrying its own source
index, byte offset, size and digest, with no association, filtering or reference
performed by the producer. It is the first time this lane has worked from original
submitted rows rather than annotation matched caches.

THE ENGINEERING QUESTION. Does the added detector deserve further integration
work? The Engine's additive loss answers it,

    delta = (a + b) * (TP_augmented - TP_base) - b * r

and `r`, the retained additions, is the one term computable without any reference.
Whatever the references turn out to be, `delta` lies in `[-b*r, a*r]`, so `r`
alone fixes how wide the answer can be.

THE RESULT: ABSTAIN, AND THE BOUND ITSELF IS NOT DETERMINED. Without admitted
references `TP_base` and `TP_augmented` are unknown, so the sign of `delta` is
open and this module returns an abstention rather than a recommendation. That much
was expected. What was not is that **`r` is not determined by the rows either**.
Over these exact 4,876 rows it runs from 139 to 2,661 across preparations that are
all defensible, so the coarse bound runs from `[-139, 139]` to `[-2661, 2661]`.

WHICH CHOICE CARRIES IT. Separating the two preparation knobs on the same rows:

    the score cutoff, from none to 0.3      about 8.8 times
    the association radius, 0.5 m to 4 m    about 2.7 times

**The score cutoff dominates the association radius by roughly three to one.**
That is the actionable part, and it is not what this lane expected: the previous
checkpoint found the radius dominant for the dependence threshold, and for the
integration bound it is the score cutoff instead. Different decisions are
sensitive to different preparation choices, and neither can be assumed from the
other.

WHAT THIS IS NOT. The Engine's real comparison is `[-8, 8]` over two windows, and
these are 16 frames, so the two are not the same scope and the numbers are not
comparable. The distance between them is preparation this lane does not own and
must not duplicate. Nothing here says the Engine's preparation is wrong; it says
that the quantity a validation lead would rely on is mostly a function of
preparation rather than of the detector outputs, and that the preparation
therefore has to be justified rather than inherited.

A competent analyst with ordinary overlap computes the same `r`, because unmatched
additions are an overlap quantity. The parity holds again. What overlap does not
report is the sensitivity decomposition above, and that is the whole of the added
value here.

Exact integer counts, standard library only. Reads one retained counts file.
"""
from fractions import Fraction
import json
import os
import sys

VERSION = "0.1.0"
COUNTS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "research", "preparation-sensitivity", "0.1.0",
    "retained-addition-counts.json")


class PacketError(Exception):
    """The consumed packet is not one this analysis accepts."""


def load(path=COUNTS):
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("artifact_id") != "reiyah.preparation-sensitivity.counts":
        raise PacketError("the file is not the retained preparation sensitivity artifact")
    consumed = data["consumed_packet"]
    if consumed["association_performed_by_producer"]:
        raise PacketError("the producer performed association; this analysis needs original rows")
    if consumed["reference_judgments_admitted"]:
        raise PacketError("the packet admits reference judgements; none may be assumed here")
    return data


def coarse_bound(retained_additions, false_negative=1, false_positive=1):
    """delta lies here whatever the references are: [-b*r, a*r]."""
    if retained_additions < 0:
        raise PacketError("the retained addition count cannot be negative")
    return {"lower": str(-false_positive * retained_additions),
            "upper": str(false_negative * retained_additions)}


def decide(retained_additions):
    """The integration verdict the rows support, which is an abstention."""
    if retained_additions == 0:
        return {"state": "no_addition_retained",
                "reason": ("every added row associates with a base row, so the loss is exactly "
                           "zero and the addition changes nothing under this preparation")}
    return {"state": "abstain",
            "reason": ("without admitted references TP_base and TP_augmented are unknown, so the "
                       "sign of the additive loss is open. The rows bound it and do not decide it"),
            "bound": coarse_bound(retained_additions)}


def spread(rows, key, fixed):
    """How much one preparation knob moves the retained additions, holding the other."""
    other = "association_radius_m" if key == "score_minimum" else "score_minimum"
    values = [row["retained_additions"] for row in rows if row[other] == fixed]
    if len(values) < 2 or min(values) == 0:
        return None
    return Fraction(max(values), min(values))


def report(data=None):
    data = data or load()
    rows = data["grid"]
    enriched = [{**row, **decide(row["retained_additions"]),
                 "coarse_bound": coarse_bound(row["retained_additions"])} for row in rows]
    radii = sorted({row["association_radius_m"] for row in rows})
    scores = sorted({row["score_minimum"] for row in rows})
    by_score = spread(rows, "score_minimum", fixed=radii[len(radii) // 2])
    by_radius = spread(rows, "association_radius_m", fixed=scores[len(scores) // 2])
    counts = [row["retained_additions"] for row in rows]
    return {
        "artifact_id": "reiyah.preparation-sensitivity.report", "version": VERSION,
        "consumed_packet": data["consumed_packet"],
        "engineering_question": "does the added detector deserve further integration work",
        "verdict": "abstain",
        "why": ("without admitted references the additive loss has an open sign. The rows bound it "
                "and do not decide it"),
        "and_the_bound_is_not_determined_either": {
            "retained_additions_span": [min(counts), max(counts)],
            "coarse_bound_span": [coarse_bound(min(counts)), coarse_bound(max(counts))],
            "ratio": str(Fraction(max(counts), min(counts)))},
        "which_preparation_choice_carries_it": {
            "score_cutoff": str(by_score) if by_score else None,
            "association_radius": str(by_radius) if by_radius else None,
            "dominant": ("score_cutoff" if by_score and by_radius and by_score > by_radius
                         else "association_radius"),
            "reading": ("the previous checkpoint found the radius dominant for the dependence "
                        "threshold. For the integration bound the score cutoff dominates instead. "
                        "Different decisions are sensitive to different preparation choices and "
                        "neither can be assumed from the other")},
        "the_overlap_baseline_gets_the_same_number": (
            "unmatched additions are an overlap quantity, so a competent analyst computes the same "
            "r. The parity holds. What overlap does not report is the sensitivity decomposition"),
        "rows": enriched,
        "not_established": [
            "any comparison with the Engine's real two window result; that is a different scope "
            "and the distance between them is preparation this lane does not own",
            "that any preparation here is the right one; each is defensible and they disagree",
            "any value for TP_base or TP_augmented, which need admitted references",
            "that a joined pair is a physical object",
            "any statistical uncertainty, sampling model or safety conclusion",
        ],
        "observation_that_would_settle_it": (
            "a declared per row coordinate and timing uncertainty for these rows would justify an "
            "association radius instead of leaving it chosen, and admitted references would close "
            "the sign. Neither exists in this lane's custody"),
    }


def main(argv):
    try:
        json.dump(report(load(argv[1]) if len(argv) > 1 else None),
                  sys.stdout, indent=2, sort_keys=True)
    except (PacketError, OSError) as error:
        sys.stderr.write(f"refused: {error}\n")
        return 1
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
