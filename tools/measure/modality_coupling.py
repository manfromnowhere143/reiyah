"""What survives when the coefficient is attacked with its own weaknesses.

Two objections deflate most of what this lane reported yesterday, and both are
right.

OBJECTION ONE, THE COEFFICIENT IS NOT MARGINAL FREE. `c` rises as miss rates
fall, which the operating point sweep showed directly. The lidar channels here
simply detect more than the camera channels, with miss rates of 0.11 to 0.14
against 0.23 to 0.24. So the finding that the most coupled pair is always a lidar
pair may be nothing but an artifact of lidar detecting more. It is. Thresholding
every channel to the SAME miss rate removes it: at a matched rate of 0.50 the two
camera pair is MORE coupled than every lidar pair, and the reported lidar
dominance reverses. That claim is withdrawn.

OBJECTION TWO, COARSE STRATA MANUFACTURE RESIDUE. Conditioning on a bucketed
variable leaves within bucket variation, and that alone produces apparent
residual coupling. Refining the stratification from 1 cell to 25,285 pulls the
two lidar residue from 3.83 down to 1.41, and it is still falling at the finest
level the data supports. So the residue reported yesterday as 2.22 to 2.31 is not
a property of the channels; it is a property of the stratification. That magnitude
is withdrawn as unidentified.

WHAT SURVIVES BOTH, AND EVERYTHING ELSE. One ordering. At every matched miss rate,
at every stratification level, at every operating point, and under a marginal free
odds ratio, **same modality pairs are strictly more coupled than cross modality
pairs, with no overlap between the two ranges.** Nine of nine controlled
comparisons here, on top of nine operating points and seven stratification
refinements.

The magnitude is not identified and is not claimed. The ordering is, and it is the
part a design decision can rest on: two channels of the same kind fail together
more than two channels of different kinds, and holding difficulty and detection
rate fixed does not remove it.

Exact rational arithmetic, standard library only. Reads one retained counts file.
"""
from fractions import Fraction
import json
import os
import sys

VERSION = "0.1.0"
COUNTS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "research", "modality-coupling", "0.1.0",
    "matched-marginal-counts.json")


class CountsError(Exception):
    """The retained counts are not in the shape this analysis requires."""


def load(path=COUNTS):
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("artifact_id") != "reiyah.modality-coupling.counts":
        raise CountsError("the file is not the retained matched marginal count artifact")
    return data


def coefficient(entry, level):
    """The coupling for one pair, at one matched miss rate, at one conditioning level."""
    cell = entry["conditioned"][str(level)]
    expected = Fraction(cell["expected_under_conditional_independence"])
    if expected == 0:
        return None
    return Fraction(cell["observed_joint_miss"], 1) / expected


def separation(data=None, level=0, target=None):
    """Do same modality pairs strictly exceed every cross modality pair here?"""
    data = data or load()
    same, cross = [], []
    for entry in data["grid"]:
        if target is not None and entry["matched_miss_rate"] != target:
            continue
        value = coefficient(entry, level)
        if value is None:
            continue
        (same if entry["kind"] == "same_modality" else cross).append(value)
    if not same or not cross:
        return None
    return {"same_modality": [str(min(same)), str(max(same))],
            "cross_modality": [str(min(cross)), str(max(cross))],
            "strictly_separated": min(same) > max(cross),
            "gap": str(min(same) - max(cross))}


def marginals_are_matched(data=None, tolerance=Fraction(1, 500)):
    """Every channel really was thresholded to the declared miss rate."""
    data = data or load()
    for entry in data["grid"]:
        target = Fraction(str(entry["matched_miss_rate"]))
        for field in ("realised_miss_rate_first", "realised_miss_rate_second"):
            if abs(Fraction(str(entry[field])) - target) > tolerance:
                return False
    return True


def report(data=None):
    data = data or load()
    targets = sorted({entry["matched_miss_rate"] for entry in data["grid"]})
    levels = sorted({int(k) for entry in data["grid"] for k in entry["conditioned"]})
    grid = []
    for target in targets:
        for level in levels:
            result = separation(data, level, target)
            cell = data["grid"][0]["conditioned"][str(level)]
            grid.append({"matched_miss_rate": target, "conditioning_level": level,
                         "conditioning_variables": cell["variables"], "cells": cell["cells"],
                         **result})
    return {
        "artifact_id": "reiyah.modality-coupling.report", "version": VERSION,
        "marginals_verified_matched": marginals_are_matched(data),
        "controlled_comparisons": len(grid),
        "same_modality_strictly_above_cross_in_all_of_them": all(
            row["strictly_separated"] for row in grid),
        "withdrawn": {
            "lidar_pairs_are_always_the_most_coupled": (
                "withdrawn. It was an artifact of the lidar channels detecting more. At a matched "
                "miss rate of 0.50 the two camera pair exceeds every lidar pair"),
            "a_residual_of_2_22_to_2_31_after_conditioning": (
                "withdrawn as unidentified. Refining the stratification pulls it to 1.41 and it is "
                "still falling at the finest level the data supports, so the number described the "
                "stratification rather than the channels")},
        "retained": {
            "claim": ("same modality pairs are strictly more coupled than cross modality pairs, "
                      "with no overlap between the ranges"),
            "survives": ["matched miss rates", "conditioning on physical difficulty",
                         "refinement of that conditioning", "every operating point",
                         "a marginal free odds ratio"],
            "magnitude": "not identified and not claimed"},
        "grid": grid,
        "not_settled": [
            "shared training data remains a live candidate for the ordering itself, since all "
            "five channels are public research detectors trained on the same split",
            "the finest stratification averages about five objects per cell, where the pooled "
            "estimator is not reliable, so the decay of the magnitude is not extrapolated",
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
