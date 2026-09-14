"""Why this claim cannot be audited across evaluation scopes, and the flip that was not one.

Version 0.1.0 of this module reported a flip witness: the modality claim held in
30 pre-registered evaluation scopes and failed in 5, every failure at close range.
A consumer required each comparison to state whether it changes scope, operating
point, evidence interpretation, or several of these. Answering that question
withdrew the flip.

WHAT WENT WRONG. Each preparation re-thresholded every detector to the same miss
rate **inside its own subset**. That keeps marginals comparable, which the estimand
contract requires, and it silently moves the score cutoff with the scope. On
vehicles within 30 metres at the best visibility band the cutoffs move by up to
`+0.521`. So every one of the 48 preparations changed the evaluation scope **and**
the operating point of every detector, and the checkpoint did not say so.

Holding the cutoffs at their full scope values instead, so the configuration is
genuinely fixed, **all five failing cells hold**, by margins from `+0.151` to
`+1.512`. **The flip was an operating point effect, not a scope effect, and it is
withdrawn.**

AND THE OTHER ARM IS NOT CLEAN EITHER. Fixing the cutoffs leaves the marginals
unmatched: in **0 of 48** preparations do the five detectors reach the same miss
rate, and this lane's own estimand contract states that the coefficient is not
comparable across marginals. The one failure in that arm, vulnerable road users
within 30 metres, spans achieved miss rates from `0.210` to `0.337`, so it is not
a clean counterexample either.

THE RESULT IS AN OBSTRUCTION, NOT AN ANSWER.

    matched rate arm    marginals comparable, operating point moves with the scope
    fixed cutoff arm    operating point fixed, marginals never matched

**No preparation in this family isolates the scope effect for this estimand.** That
is a structural statement about auditing a marginal dependent quantity across
population subsets, and it is worth more than the flip would have been, because it
says why the audit cannot be completed rather than reporting a result that a
second question dissolves.

What survives is narrower and stated with its scope attached: the claim holds at
full scope with matched marginals, and this family cannot extend it to sub scopes.

Exact rational arithmetic, standard library only. Reads one retained grid.
"""
from fractions import Fraction
import json
import os
import sys

VERSION = "0.2.0"
COUNTS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "research", "preparation-robustness", "0.2.0",
    "preparation-grid.json")
PREREGISTRATION = os.path.join(os.path.dirname(os.path.dirname(COUNTS)), "0.1.0",
                               "PREREGISTRATION.json")
ARMS = ("matched_rate", "fixed_cutoff")


class GridError(Exception):
    """The retained grid is not one this audit accepts."""


def load(path=COUNTS):
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("artifact_id") != "reiyah.preparation-robustness.counts":
        raise GridError("the file is not the retained preparation robustness grid")
    if data.get("version") != VERSION:
        raise GridError(f"this module reads grid {VERSION}, not {data.get('version')}")
    return data


def computed(data, arm):
    return [row for row in data["grid"] if row.get(arm, {}).get("state") == "computed"]


def cutoff_movement(data):
    """How far the score cutoff moves from its full scope value in the matched arm."""
    reference = data["reference_cutoffs_at_full_scope"]
    worst = None
    for row in computed(data, "matched_rate"):
        cuts = row["matched_rate"]["cutoffs"]
        move = max(abs(cuts[n] - reference[n]) for n in reference)
        if worst is None or move > worst["largest_move"]:
            worst = {"scope": [row["P1"], row["P2"], row["P3"]], "largest_move": move,
                     "cutoffs": cuts, "reference": reference}
    return worst


def arm_summary(data, arm):
    rows = computed(data, arm)
    fails = [r for r in rows if not r[arm]["predicate"]]
    matched = [r for r in rows if r[arm]["marginals_matched"]]
    return {"computed": len(rows), "fails": len(fails),
            "preparations_with_matched_marginals": len(matched),
            "failing_scopes": [[r["P1"], r["P2"], r["P3"]] for r in fails]}


def report(data=None):
    data = data or load()
    matched = arm_summary(data, "matched_rate")
    fixed = arm_summary(data, "fixed_cutoff")
    movement = cutoff_movement(data)
    return {
        "artifact_id": "reiyah.preparation-robustness.report", "version": VERSION,
        "named_claim": data["named_claim"],
        "preregistration_sha256": data["preregistration_sha256"],
        "withdrawn": {
            "claim": ("the modality claim is not robust to evaluation scope, with five flip "
                      "witnesses at close range"),
            "why": ("every preparation re-thresholded each detector inside its own subset, so it "
                    "changed the operating point as well as the scope. With the cutoffs held at "
                    "their full scope values all five failing cells hold"),
            "largest_cutoff_movement": movement},
        "arms": {"matched_rate": matched, "fixed_cutoff": fixed},
        "neither_arm_isolates_the_scope": {
            "matched_rate": "marginals comparable, operating point moves with the scope",
            "fixed_cutoff": (f"operating point fixed, marginals matched in "
                             f"{fixed['preparations_with_matched_marginals']} of "
                             f"{fixed['computed']} preparations"),
            "consequence": ("no preparation in this family isolates the scope effect for this "
                            "estimand, because the coefficient is marginal dependent and a "
                            "population subset changes the marginals")},
        "what_survives": ("the claim holds at full scope with matched marginals. This family "
                          "cannot extend it to sub scopes, and the scope is part of the claim"),
        "what_the_consumer_requirement_bought": (
            "asking what each comparison changes withdrew a published flip witness and replaced it "
            "with a structural obstruction. The requirement did the work, not the method"),
        "not_established": [
            "that the claim fails in any sub scope; the one fixed cutoff failure spans unmatched "
            "miss rates from 0.210 to 0.337 and is not a clean counterexample",
            "anything about physical risk, human effort or industry practice",
            "any independent human reference; retrospective and annotation conditional",
            "any change to the live Engine comparison, which remains [-8,8]",
        ],
    }


def main(argv):
    try:
        json.dump(report(load(argv[1]) if len(argv) > 1 else None),
                  sys.stdout, indent=2, sort_keys=True)
    except (GridError, OSError) as error:
        sys.stderr.write(f"refused: {error}\n")
        return 1
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
