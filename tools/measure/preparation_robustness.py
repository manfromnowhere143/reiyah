"""Auditing one of this lane's own published claims across admissible preparations.

The claim under audit is this lane's own, from `modality-coupling-0.1.0`: same
modality detector pairs are more coupled than cross modality pairs at matched miss
rates. It carries an engineering consequence, which is to buy sensor diversity
rather than software diversity, so it is worth knowing whether it survives the
preparation choices an analyst is free to make.

THE DISCIPLINE, WHICH MATTERS MORE THAN THE METHOD. The family of alternative
preparations was written down and digested **before any result was computed**, at
`8e633b95e594c8b9c13061cb0af2ce19e0049a317013f3687a3c742144ac367c`, so that
widening it after seeing the outcome would be visible. Forty eight preparations,
formed from class scope, range band and visibility floor. Each is a standard
published evaluation scope choice and **none changes any detector's output**: they
change which annotated objects are in scope.

The detector score cutoff is deliberately excluded from that family. Raising it
changes the system being evaluated, so a flip obtained that way would be a
configuration comparison and not uncertainty about one fixed configuration. It is
held fixed at the matched miss rate instead.

THE RESULT: THE CLAIM IS NOT ROBUST. The predicate holds in 30 preparations, fails
in **5**, and is undefined in 13 where a marginal vanishes or the population is too
small. The five failures are not scattered: **every one of them is a close range
scope.** At vehicles within 30 metres the ordering interleaves, with
`centerpoint/pointpillars` at 2.092, a same modality pair, falling below
`centerpoint/fcos3d` at 2.124 and `fcos3d/megvii` at 2.118, both cross modality.

The margin matters as much as the sign. At full scope the claim holds by `+0.3523`
with all four same modality pairs above all six cross pairs. At close range
vehicles it fails by `-0.0317`. That is thin, and this lane has already been
burned once by a thin margin, so the failure is reported with its margin attached
and the thinness stated rather than a bare boolean.

WHAT THE COMPARATOR GETS. The baseline is the ordinary full grid over the same
family, which is multiverse analysis in the sense of Bell, Kampman, Dodge and
Lawrence, NeurIPS 2022. **This lane ran that grid, so the grid is not a competitor
it beat; it is the method that produced the result.** Nothing here outperforms an
analyst who sweeps the same family. What the procedure adds is the pre-registered
family, the separation of evaluation scope from configuration change, and the
named responsible pair. That is discipline, not algorithmic advantage, and it
should not be sold as one.

Exact rational arithmetic, standard library only. Reads one retained grid.
"""
from fractions import Fraction
import json
import os
import sys

VERSION = "0.1.0"
COUNTS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "research", "preparation-robustness", "0.1.0",
    "preparation-grid.json")
PREREGISTRATION = os.path.join(os.path.dirname(COUNTS), "PREREGISTRATION.json")
THIN = Fraction(1, 10)


class GridError(Exception):
    """The retained grid is not one this audit accepts."""


def load(path=COUNTS):
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("artifact_id") != "reiyah.preparation-robustness.counts":
        raise GridError("the file is not the retained preparation robustness grid")
    return data


def margin(row):
    """min(same) - max(cross), the quantity the predicate thresholds at zero."""
    if row.get("state") != "computed":
        return None
    return Fraction(row["same_min"]) - Fraction(row["cross_max"])


def outcome(data=None):
    data = data or load()
    rows = data["grid"]
    holds = [r for r in rows if r.get("predicate") is True]
    fails = [r for r in rows if r.get("predicate") is False]
    undefined = [r for r in rows if r.get("predicate") is None]
    return {"preparations": len(rows), "holds": len(holds), "fails": len(fails),
            "undefined": len(undefined),
            "verdict": ("flip_witness" if fails and holds else
                        "robust" if not fails and holds else "unresolved")}


def flip_witnesses(data=None):
    data = data or load()
    out = []
    for row in data["grid"]:
        if row.get("predicate") is not False:
            continue
        gap = margin(row)
        out.append({"class_scope": row["P1"], "range_band": row["P2"],
                    "visibility_floor": row["P3"], "population": row["population"],
                    "same_modality": [row["same_min"], row["same_max"]],
                    "cross_modality": [row["cross_min"], row["cross_max"]],
                    "margin": str(gap), "thin": abs(gap) < THIN})
    return out


def report(data=None):
    data = data or load()
    result = outcome(data)
    witnesses = flip_witnesses(data)
    holding = [margin(r) for r in data["grid"] if r.get("predicate") is True]
    bands = {w["range_band"] for w in witnesses}
    return {
        "artifact_id": "reiyah.preparation-robustness.report", "version": VERSION,
        "named_claim": data["named_claim"],
        "claim_published_by_this_lane_in": "modality-coupling-0.1.0",
        "preregistration_sha256": data["preregistration_sha256"],
        "family_kind": data["family_kind"],
        "excluded_as_configuration_change": data["excluded_as_configuration_change"],
        **result,
        "flip_witnesses": witnesses,
        "every_failure_shares_a_range_band": len(bands) == 1,
        "the_shared_band": sorted(bands),
        "largest_holding_margin": str(max(holding)) if holding else None,
        "worst_failing_margin": str(min(Fraction(w["margin"]) for w in witnesses))
                                if witnesses else None,
        "margins_are_thin_where_it_fails": all(w["thin"] for w in witnesses),
        "baseline": {
            "method": "the ordinary full grid over the same family, which is multiverse analysis",
            "citation": ("Bell, Kampman, Dodge and Lawrence, Modeling the Machine Learning "
                         "Multiverse, NeurIPS 2022, arXiv:2206.05985v2"),
            "honest_position": ("this lane ran that grid, so the grid is not a competitor it beat, "
                                "it is the method that produced the result. Nothing here "
                                "outperforms an analyst sweeping the same family")},
        "what_the_discipline_added": [
            "the family was digested before any result was computed, so widening it afterwards "
            "would be visible",
            "evaluation scope was separated from configuration change, so a score cutoff flip "
            "cannot be passed off as uncertainty about a fixed configuration",
            "the responsible pair is named rather than left as a boolean",
        ],
        "not_established": [
            "anything about physical risk, human effort or industry practice",
            "that the close range structure has the causal reading it suggests",
            "any independent human reference; this is retrospective and annotation conditional",
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
