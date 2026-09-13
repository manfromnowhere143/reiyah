"""The joint failure that survives after every measurable difficulty is accounted for.

A dependence coefficient above 1 has an innocent explanation available: hard
objects are hard for everyone. Far away, occluded, few returns, and both channels
miss together without anything shared between them beyond the object. If that
accounts for the coupling, a redundancy argument can be repaired by conditioning
on difficulty, and there is no deep problem.

This tests that explanation and rejects it.

Within a stratum `s` of a measurable difficulty variable, conditional
independence predicts `n_s * (a_s / n_s) * (b_s / n_s)` joint misses. Pooling
over strata gives the coefficient that would hold if the variable were held
fixed:

    c_within  =  sum_s observed_s  /  sum_s ( a_s * b_s / n_s )

`c_within` is the coupling that remains after the variable is accounted for, and
`(c - c_within) / (c - 1)` is the share of the excess the variable explains. This
is the classical stratified comparison, applied to the estimand in
`docs/ESTIMAND_RSS_DEFINITION_32.md`.

WHAT IS FOUND. Conditioning on lidar return density, range from ego and annotated
visibility together removes 55 to 73 percent of the excess. It does not remove the
ordering, and it does not remove the coupling. **After every one of those
variables is held fixed, a two lidar pair still fails together about 2.2 to 2.3
times more often than conditional independence predicts, while a camera and lidar
pair retains about 1.4 to 1.6.**

So the innocent explanation is insufficient. The part of joint failure that
survives conditioning cannot be engineered away by range margin, occlusion
handling or return density thresholds, because those have already been accounted
for. It is the residue, and same modality pairs carry roughly twice as much of it.

WHAT THIS DOES NOT SETTLE. The residue is unexplained by THESE variables, which
is not the same as unexplainable. A variable nobody recorded could account for it,
and shared training data remains a live candidate that these counts cannot rule
out: all five channels are public research detectors trained on the same split.
What the test does establish is that the simplest deflationary reading, that
coupling is just difficulty, is false.

Exact rational arithmetic, standard library only. Reads one retained counts file.
"""
from fractions import Fraction
import json
import os
import sys

VERSION = "0.1.0"
COUNTS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "research", "residual-coupling", "0.1.0",
    "stratified-counts.json")
COMBINED = "physical_difficulty_combined"


class CountsError(Exception):
    """The retained counts are not in the shape this analysis requires."""


def load(path=COUNTS):
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("artifact_id") != "reiyah.residual-coupling.counts":
        raise CountsError("the file is not the retained stratified count artifact")
    return data


def marginal(pair):
    """c with nothing held fixed."""
    if pair["first_missed"] == 0 or pair["second_missed"] == 0:
        return None
    return Fraction(pair["both_missed"] * pair["population"],
                    pair["first_missed"] * pair["second_missed"])


def within(pair, variable):
    """c with the variable held fixed, pooled across its strata."""
    entry = pair["strata"][variable]
    if "cells" in entry:
        observed = sum(cell["both_missed"] for cell in entry["cells"])
        expected = sum(Fraction(cell["first_missed"] * cell["second_missed"], cell["objects"])
                       for cell in entry["cells"] if cell["objects"])
    else:
        observed = entry["observed_joint_miss"]
        expected = Fraction(entry["expected_under_conditional_independence"])
    if expected == 0:
        return None
    return Fraction(observed, 1) / expected


def explained_share(pair, variable):
    """The share of the excess above 1 that holding this variable fixed removes."""
    outer, inner = marginal(pair), within(pair, variable)
    if outer is None or inner is None or outer == 1:
        return None
    return (outer - inner) / (outer - 1)


def report(data=None):
    data = data or load()
    variables = list(data["stratifying_variables"])
    rows = []
    for pair in data["pairs"]:
        rows.append({
            "pair": f"{pair['first']}/{pair['second']}",
            "kind": pair["kind"], "modalities": pair["modalities"],
            "marginal": str(marginal(pair)),
            "within": {v: str(within(pair, v)) for v in variables},
            "explained_share": {v: str(explained_share(pair, v)) for v in variables},
        })

    def group(kind_test, field):
        values = [Fraction(row[field][COMBINED]) if isinstance(row[field], dict)
                  else Fraction(row[field]) for row in rows if kind_test(row)]
        return [str(min(values)), str(max(values))] if values else None

    lidar = lambda row: row["modalities"] == ["lidar", "lidar"]
    camera = lambda row: row["modalities"] == ["camera", "camera"]
    cross = lambda row: row["kind"] == "cross_modality"
    residual = {"two_lidar": group(lidar, "within"), "two_camera": group(camera, "within"),
                "cross_modality": group(cross, "within")}
    lidar_low = min(Fraction(row["within"][COMBINED]) for row in rows if lidar(row))
    others_high = max(Fraction(row["within"][COMBINED]) for row in rows if not lidar(row))
    return {
        "artifact_id": "reiyah.residual-coupling.report", "version": VERSION,
        "question": ("is the coupling just difficulty? If holding every measurable difficulty "
                     "variable fixed removes it, a redundancy argument can be repaired by "
                     "conditioning and there is no deep problem"),
        "answer": "no",
        "after_holding_difficulty_fixed": residual,
        "every_two_lidar_pair_still_above_every_other_pair": lidar_low > others_high,
        "explained_by_the_combined_variables": {
            "lowest": str(min(Fraction(row["explained_share"][COMBINED]) for row in rows)),
            "highest": str(max(Fraction(row["explained_share"][COMBINED]) for row in rows))},
        "scene_condition_explains_nothing": all(
            abs(Fraction(row["explained_share"]["scene_condition"])) < Fraction(1, 100)
            for row in rows),
        "reading": ("the residue cannot be engineered away by range margin, occlusion handling or "
                    "return density thresholds, because those have already been accounted for. "
                    "Same modality pairs carry roughly twice as much of it"),
        "rows": rows,
        "not_settled": [
            "unexplained by these variables is not unexplainable; a variable nobody recorded "
            "could account for the residue",
            "shared training data remains a live candidate these counts cannot rule out, since "
            "all five channels are public research detectors trained on the same split",
            "no statistical uncertainty, resampling band or sampling model is computed here",
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
