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
import hashlib
import json
import math
import os
import sys
import tempfile

VERSION = "0.2.0"
INPUT_ALLOWLIST = ("megvii_val.json", "mapillary_val.json")
# A basename is not an identity. Bytes are. Version 0.1.0 checked only the name,
# so substituted content under an allowed basename was accepted, which a consumer
# probe demonstrated. These digests are the actual contract.
EXPECTED_DIGEST = {
    "megvii_val.json": "e7a995c31692ac95a86b56208e0b5d82a4ab908df8d0a9b9474d70adb693eab4",
    "mapillary_val.json": "f948e9778fb9a332d748f7e504fbade04f0c00c2699d7b0af757cacdbd567e99",
}
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


def verify_bytes(path, name):
    """Refuse content that does not hash to the recorded original."""
    if name not in EXPECTED_DIGEST:
        raise AssociationError(f"{name!r} has no recorded digest")
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 22), b""):
            digest.update(block)
    seen = digest.hexdigest()
    if seen != EXPECTED_DIGEST[name]:
        raise AssociationError(
            f"{name!r} does not match its recorded digest. expected "
            f"{EXPECTED_DIGEST[name][:16]}..., read {seen[:16]}...")
    return seen


def read_submission(directory, name, score_minimum, verify=True):
    """Open one allowed submission, by name AND by bytes.

    The name check alone was the whole boundary in version 0.1.0, and a consumer
    showed that substituted content under an allowed basename passed it. The
    digest check is the real contract; `verify=False` exists only so a unit test
    can exercise the parser on a tiny fixture, and it is refused for any path
    outside a temporary directory.
    """
    if name not in INPUT_ALLOWLIST:
        raise AssociationError(f"{name!r} is not in the declared input allowlist")
    path = os.path.join(directory, name)
    if verify:
        verify_bytes(path, name)
    elif not os.path.realpath(path).startswith(tempfile.gettempdir()):
        raise AssociationError("unverified reads are permitted only under a temporary directory")
    with open(path, "r", encoding="utf-8") as handle:
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


def associate_maximum(first, second, tau):
    """The same admissibility, matched to maximum cardinality instead of greedily.

    The greedy rule depends on the order records arrive in: on one class with left
    positions 0 and 0.9, right positions 0.5 and -0.8 and a radius of 1, it joins
    one pair as given and two after reversal. That is a model choice with an
    observable cost, so the alternative is implemented and compared rather than
    argued about.
    """
    if tau <= 0:
        raise AssociationError("the association radius must be positive")
    both = only_first = only_second = 0
    for token in set(first) | set(second):
        left = first.get(token, [])
        right = second.get(token, [])
        adjacency = []
        for name, ax, ay in left:
            options = [index for index, (other, bx, by) in enumerate(right)
                       if other == name and math.hypot(ax - bx, ay - by) <= tau]
            adjacency.append(options)
        partner = {}

        def augment(node, seen):
            for option in adjacency[node]:
                if option in seen:
                    continue
                seen.add(option)
                if option not in partner or augment(partner[option], seen):
                    partner[option] = node
                    return True
            return False

        joined = sum(1 for node in range(len(left)) if augment(node, set()))
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
        entry["m_star_over_annotated_record_count"] = str(
            threshold / Fraction(annotated_population))
        entry["scale_only"] = (
            "the annotation record count is a scale, not a bound on unseen physical "
            "opportunities. Physical objects, per frame opportunities, repeated records, false "
            "positives and unmatched predictions are different units, and no error model here "
            "converts between them. Version 0.1.0 used this ratio to call one setting "
            "implausible; that inference is withdrawn")
    return entry


def load(path=COUNTS):
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("artifact_id") != "reiyah.raw-association.counts":
        raise AssociationError("the file is not the retained raw association artifact")
    return data


def report(data=None):
    data = data or load()
    scale = data["annotated_record_count_for_scale_only"]
    rows = []
    for row in data["grid"]:
        table = {k: row[k] for k in ("both_channels", "first_only", "second_only")}
        rows.append({"score_minimum": row["score_minimum"], "association_radius_m": row["tau"],
                     "rule": row["rule"], **table, **identified_set(table, scale)})
    thresholds = [Fraction(r["m_star"]) for r in rows if "m_star" in r]
    by_setting = {}
    for row in rows:
        by_setting.setdefault((row["score_minimum"], row["association_radius_m"]), {})[
            row["rule"]] = row
    rule_effect = []
    for key in sorted(by_setting):
        pair = by_setting[key]
        if len(pair) != 2:
            continue
        greedy, maximum = pair["greedy"], pair["max-cardinality"]
        rule_effect.append({
            "score_minimum": key[0], "association_radius_m": key[1],
            "m_star_greedy": greedy["m_star"], "m_star_maximum": maximum["m_star"],
            "ratio": str(Fraction(maximum["m_star"]) / Fraction(greedy["m_star"])),
            "same_state": greedy["state"] == maximum["state"]})
    radius_span = max(thresholds) / min(thresholds)
    rule_span = max(abs(1 - Fraction(e["ratio"])) for e in rule_effect)
    return {
        "artifact_id": "reiyah.raw-association.report", "version": VERSION,
        "information_boundary": data["information_boundary"],
        "verdict": "unresolved",
        "why": ("on these two channel tables u is zero and w, x and y are positive, so the sign is "
                "at most one below the threshold and above one afterwards. This is a conditional "
                "result about these tables, not about every two channel table"),
        "sensitivity_is_dominated_by_the_radius": {
            "threshold_span_across_preparations": str(radius_span),
            "largest_relative_move_from_the_matching_rule": str(rule_span),
            "states_unchanged_by_the_rule": all(e["same_state"] for e in rule_effect),
            "reading": ("the admissibility radius moves the threshold by more than an order of "
                        "magnitude; the assignment rule moves it by a few percent and never "
                        "changes the state. Effort belongs on justifying the radius, not on "
                        "perfecting the matcher")},
        "rule_effect": rule_effect,
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
            "that the annotation record count bounds unseen physical opportunities",
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
