"""Building the capture table from raw detector submissions, with no annotation.

Every real measurement this lane has made used caches that contain only detections
already matched to annotated objects. Annotation based membership, correspondence
and unmatched detection filtering were therefore inside the inputs. This module
goes to the original submitted detector outputs instead and builds the table with
the annotation inaccessible.

THE INFORMATION BOUNDARY, DECLARED. The constructor reads two files and nothing
else. No annotation file, no matched cache, no ground truth cache, no frame list
derived from annotations, no class filter derived from annotations, and no
threshold or association rule chosen by looking at annotations. `INPUT_ALLOWLIST`
names what may be opened; `EXCLUDED_INFORMATION` names what must not be, and a
test asserts the constructor's own source text opens nothing else.

THE ASSOCIATION RULE IS A CHOICE, AND IT IS NOT FREE. Two detections in the same
frame become one candidate object when they carry the same class label and lie
within `tau` metres of each other in the submitted global frame, matched one to
one, nearest first. A joined pair is a candidate, not a physical object. An
unmatched detection stays visible as an unmatched detection rather than being
discarded or promoted.

WHAT THE RAW DATA WILL NOT SUPPORT. Two channels give no third observer, so the
cell counting objects both channels missed is empty by construction. The sign of
the dependence coefficient then turns entirely on the unseen count `m`, through
`c > 1` exactly when `m * w > x * y`, so the sign is identified only above the
threshold

    m_star  =  x * y / w.

That threshold is not stable. Across score cutoffs of 0.2 to 0.5 and association
radii of 1 to 4 metres, all defensible, `m_star` runs from 11,771 to 162,021, a
spread of about fourteen times. At one of those settings it exceeds the number of
objects the public annotation records at all, which would make positive coupling
implausible rather than merely unproven.

**So on raw two channel detections with the annotation inaccessible, the sign is
not identified.** This module reports an identified set and the threshold, never a
number. The same dependence holds for the ordinary overlap baseline, whose
intersection count is the same `w`: this is a property of the setting, not a
defect of one statistic.

These are exposed nuScenes validation submissions, so any comparison against the
annotation afterwards is a reproducible retrospective falsification and not a
blind validation.

Standard library only. Exact integer counts; rational arithmetic for thresholds.
"""
from fractions import Fraction
import collections
import json
import math
import os
import sys

VERSION = "0.1.0"
INPUT_ALLOWLIST = ("megvii_val.json", "mapillary_val.json")
EXCLUDED_INFORMATION = (
    "any annotation or ground truth file",
    "any matched_* cache, which contains only annotation matched detections",
    "any frame list, class filter or score threshold chosen by inspecting annotations",
    "any association rule tuned against annotations",
)
COUNTS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "research", "raw-association", "0.1.0", "association-counts.json")


class AssociationError(Exception):
    """The declared inputs or rule are not ones this constructor accepts."""


def read_submission(directory, name, score_minimum):
    """Open one allowed submission and keep class and planar position only."""
    if name not in INPUT_ALLOWLIST:
        raise AssociationError(f"{name!r} is not in the declared input allowlist")
    with open(os.path.join(directory, name), "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    frames = collections.defaultdict(list)
    for token, detections in payload["results"].items():
        for record in detections:
            if record["detection_score"] >= score_minimum:
                frames[token].append((record["detection_name"],
                                      record["translation"][0], record["translation"][1]))
    return frames


def associate(first, second, tau):
    """Same class, one to one, nearest within tau. Unmatched stay visible."""
    if tau <= 0:
        raise AssociationError("the association radius must be positive")
    both = only_first = only_second = 0
    for token in set(first) | set(second):
        left = first.get(token, [])
        right = second.get(token, [])
        by_class = collections.defaultdict(list)
        for index, (name, x, y) in enumerate(right):
            by_class[name].append((index, x, y))
        taken = set()
        joined = 0
        for name, ax, ay in left:
            best = None
            for index, bx, by in by_class.get(name, ()):
                if index in taken:
                    continue
                distance = math.hypot(ax - bx, ay - by)
                if distance <= tau and (best is None or distance < best[0]):
                    best = (distance, index)
            if best is not None:
                taken.add(best[1])
                joined += 1
        both += joined
        only_first += len(left) - joined
        only_second += len(right) - joined
    return {"both_channels": both, "first_only": only_first, "second_only": only_second}


def sign_threshold(table):
    """m_star = x*y/w. Above it the coefficient exceeds 1, below it does not."""
    if table["both_channels"] == 0:
        return None
    return Fraction(table["first_only"] * table["second_only"], table["both_channels"])


def identified_set(table, annotated_population=None):
    """What the raw data supports, which is a set and a threshold, never a number."""
    threshold = sign_threshold(table)
    if threshold is None:
        return {"state": "undefined",
                "reason": "no candidate was seen by both channels, so the threshold has no value"}
    entry = {"state": "unresolved",
             "reason": ("two channels give no third observer, so the cell counting objects both "
                        "missed is empty by construction and the sign turns entirely on the unseen "
                        "count"),
             "coefficient_exceeds_one_when": "the unseen count exceeds m_star",
             "m_star": str(threshold)}
    if annotated_population:
        entry["m_star_over_annotated_population"] = str(
            threshold / Fraction(annotated_population))
        entry["would_need_more_unseen_than_annotated"] = threshold > annotated_population
    return entry


def load(path=COUNTS):
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("artifact_id") != "reiyah.raw-association.counts":
        raise AssociationError("the file is not the retained raw association artifact")
    return data


def report(data=None):
    data = data or load()
    population = data["annotated_population_for_scale_only"]
    rows = []
    for row in data["grid"]:
        table = {k: row[k] for k in ("both_channels", "first_only", "second_only")}
        rows.append({"score_minimum": row["score_minimum"], "association_radius_m": row["tau"],
                     **table, **identified_set(table, population)})
    thresholds = [Fraction(r["m_star"]) for r in rows if "m_star" in r]
    return {
        "artifact_id": "reiyah.raw-association.report", "version": VERSION,
        "information_boundary": {"opened": list(INPUT_ALLOWLIST),
                                 "excluded": list(EXCLUDED_INFORMATION)},
        "verdict": "unresolved",
        "why": ("on raw two channel detections with the annotation inaccessible, the sign of the "
                "dependence coefficient is not identified"),
        "m_star_spread": {"lowest": str(min(thresholds)), "highest": str(max(thresholds)),
                          "ratio": str(max(thresholds) / min(thresholds))},
        "at_least_one_setting_makes_positive_coupling_implausible": any(
            r.get("would_need_more_unseen_than_annotated") for r in rows),
        "the_overlap_baseline_shares_this": (
            "the intersection count w is the same quantity the Jaccard baseline uses, so its "
            "ordering moves with the association radius too. This is a property of the setting, "
            "not a defect of one statistic"),
        "exposure": ("these are exposed nuScenes validation submissions, so any later comparison "
                     "against the annotation is a reproducible retrospective falsification and not "
                     "a blind validation"),
        "rows": rows,
        "not_established": [
            "that a joined pair is a physical object; it is a candidate under a declared rule",
            "any modality comparison, which needs channels this input set does not contain",
            "any value for the coefficient, only a threshold and an identified set",
            "any statistical uncertainty, sampling model or safety conclusion",
        ],
    }


def main(argv):
    try:
        json.dump(report(load(argv[1]) if len(argv) > 1 else None),
                  sys.stdout, indent=2, sort_keys=True)
    except (AssociationError, OSError) as error:
        sys.stderr.write(f"refused: {error}\n")
        return 1
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
