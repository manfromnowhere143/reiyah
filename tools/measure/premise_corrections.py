"""Corrections to the premises under the preparation robustness reading.

Version 0.2.0 of the grid stands. What is corrected here is what was said about
it. Five premises were challenged by the consumer and a sixth was found in this
lane. Each is answered by recomputing from bytes rather than by rereading prose,
and where a fact is not derivable from committed bytes that is said instead of
filled in.

1  SCOPE AND CUTOFF. "Every preparation changed every cutoff" was wrong. Of the
   35 computed matched rate rows, 33 move at least one stored cutoff and 31 move
   all five. Two move none, and both of those are the full population compared
   with itself, which is not a scope change at all.

2  THE RESIDUAL MISMATCH. Four detectors miss 40369 of 134565 at full scope and
   PointPillars misses 40391, a residual of 22 objects, 0.00016349 in rate. The
   kept counts are reproduced exactly by keeping a prediction whose score is
   strictly greater than the cutoff. The mismatch is not a rounding display and
   not a tolerance choice: PointPillars publishes 9370 distinct scores over
   115805 covered objects, 26 of them exactly at its cutoff, so the attainable
   kept counts step from 94174 straight to 94200. The matched value 94196 lies
   between two adjacent attainable counts and no cutoff of any precision reaches
   it. Exact marginal matching is obstructed by the granularity of one published
   submission.

3  NOT AN IMPOSSIBILITY. Zero exact matches in this fixed cutoff family is a
   limitation of this design. It is not a theorem about subsetting. Scope
   conditional statistics remain definable, and a descriptive comparison, a
   matched marginal comparison and a claim about a dependence mechanism stay
   three different things.

4  SENSITIVITY IS NOT CAUSE. The counterfactual cutoff calculation shows that the
   reported ordering moves when the cutoffs move. It does not identify a physical
   cause and does not rule out an interaction between scope and cutoff. A fixed
   numerical cutoff and a fixed achieved rate are different fixings.

5  PARITY IS A HYPOTHESIS. The parities this lane found constrain the methods and
   problems they were found on. Broader analysis parity is a hypothesis, and any
   integration advantage has to be measured against an analyst with ordinary
   source tracing, viewing and verification tools.

6  FOUND HERE, NOT REPORTED TO US. The grid's 48 labels do not name 48 distinct
   preparations. `within_50m` is the identity on this population, because the
   cache reaches 50 metres and no further, so it duplicates `all_ranges` in 12
   pairs. Three more pairs coincide because the excluded static furniture all
   lies within 30 metres. Fifteen of the 48 rows are duplicates of another row,
   and every rate computed over the grid as though it had 48 independent
   preparations is computed over 33.

Standard library only. The grid is read from committed bytes. The tie rule
recomputation reads the original submissions, which live outside this repository
under another owner, and is reported as unavailable when they are not present.
"""
from fractions import Fraction
import hashlib
import json
import os
import sys

VERSION = "0.3.0"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GRID = os.path.join(ROOT, "research", "preparation-robustness", "0.2.0", "preparation-grid.json")
POPULATION = 134565

SUBMISSION_DIGESTS = {
    "gt_val_cache.json": "7a7fb7c3913496a64bede26468d7f4b976366ccc8a3825092e16805363ea53fd",
    "matched_centerpoint.json": "6a8be866b3316857f44787a3676b1557d9d8dfb6a945f16f469bb10877326275",
    "matched_fcos3d.json": "dd7fa5d2fe13b34a4bf6762f4c8cd512e629c88bcbbb5227dfa58cf46ae8cdf4",
    "matched_mapillary.json": "a8fef4a1e7dbf0fed84ae1220332fcb97196e468ebf23cb77fe835871466caca",
    "matched_megvii.json": "2ce14fcca8235438d2f9b2ab844f83e21413e97a2ab0cf597f445bac6e35a0c1",
    "matched_pointpillars.json": "46b0f70daf6e18f08a4a439c502e7026c2b5d67bcffbb2109f92b314478f484e",
}


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def load(path=GRID):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def cutoff_changes(data):
    """Premise 1, recomputed: how many computed rows move how many cutoffs."""
    reference = data["reference_cutoffs_at_full_scope"]
    names = sorted(reference)
    histogram, unchanged = {}, []
    computed = 0
    for row in data["grid"]:
        arm = row["matched_rate"]
        if arm["state"] != "computed":
            continue
        computed += 1
        moved = sum(1 for name in names if arm["cutoffs"][name] != reference[name])
        histogram[moved] = histogram.get(moved, 0) + 1
        if moved == 0:
            unchanged.append([row["P1"], row["P2"], row["P3"]])
    largest, where = 0.0, None
    for row in data["grid"]:
        arm = row["matched_rate"]
        if arm["state"] != "computed":
            continue
        for name in names:
            gap = abs(arm["cutoffs"][name] - reference[name])
            if gap > largest:
                largest, where = gap, {"preparation": [row["P1"], row["P2"], row["P3"]],
                                       "detector": name, "from": reference[name],
                                       "to": arm["cutoffs"][name]}
    return {"rows_total": len(data["grid"]), "rows_computed_in_the_matched_arm": computed,
            "rows_not_computed": len(data["grid"]) - computed,
            "moved_cutoff_histogram": {str(k): v for k, v in sorted(histogram.items())},
            "moved_at_least_one": sum(v for k, v in histogram.items() if k >= 1),
            "moved_all_five": histogram.get(len(names), 0),
            "moved_none": unchanged,
            "largest_move": {"size": round(largest, 6), "where": where},
            "correction": ("the claim that every preparation moved every cutoff is withdrawn. "
                           "The two rows that move nothing are the full population compared with "
                           "itself, which is not a scope change")}


def duplicate_preparations(data):
    """Premise 6, found here: how many of the 48 labels name a distinct preparation."""
    names = sorted(data["reference_cutoffs_at_full_scope"])
    groups = {}
    for row in data["grid"]:
        arm = row["fixed_cutoff"]
        if arm["state"] != "computed":
            continue
        key = (row["population"], tuple(arm["kept_counts"][name] for name in names))
        groups.setdefault(key, []).append([row["P1"], row["P2"], row["P3"]])
    duplicates = [{"population": key[0], "kept_counts": list(key[1]), "labels": rows}
                  for key, rows in sorted(groups.items()) if len(rows) > 1]
    within_50m = [entry for entry in duplicates
                  if sorted(row[1] for row in entry["labels"]) == ["all_ranges", "within_50m"]]
    return {"labels": len(data["grid"]), "distinct_preparations": len(groups),
            "duplicate_groups": len(duplicates),
            "rows_inside_a_duplicate_group": sum(len(e["labels"]) for e in duplicates),
            "within_50m_is_the_identity_in": len(within_50m),
            "duplicates": duplicates,
            "finding": ("the cache reaches 50 metres and no further, so within_50m selects the "
                        "whole population and duplicates all_ranges. The remaining coincidences "
                        "are preparations that happen to select the same rows on this population"),
            "consequence": ("any share computed over the grid as though its 48 labels were 48 "
                            "independent preparations is computed over fewer")}


def scores_by_object(path):
    """Best matched score per object, from one original submission."""
    with open(path, "r", encoding="utf-8") as handle:
        rows = json.load(handle)["matched_at_2m"]
    best = {}
    for entries in rows.values():
        for key, value in entries.items():
            index = int(key)
            score = float(value)
            if score > best.get(index, -1.0):
                best[index] = score
    return best


def tie_rule(directory, data):
    """Premise 2, recomputed: which rule reproduces the stored counts, and what blocks a match."""
    if not directory or not os.path.isdir(directory):
        return {"state": "unavailable",
                "reason": ("the original submissions live outside this repository under another "
                           "owner and were not supplied to this run"),
                "inputs_expected": SUBMISSION_DIGESTS}
    reference = data["reference_cutoffs_at_full_scope"]
    full = next(row for row in data["grid"]
                if [row["P1"], row["P2"], row["P3"]] == ["all_classes", "all_ranges", "all_visibility"])
    stored = full["fixed_cutoff"]["kept_counts"]
    detectors, bound = {}, {}
    for name in sorted(reference):
        path = os.path.join(directory, "matched_%s.json" % name)
        if not os.path.exists(path):
            return {"state": "unavailable", "reason": f"missing {path}",
                    "inputs_expected": SUBMISSION_DIGESTS}
        bound["matched_%s.json" % name] = digest(path)
        scores = scores_by_object(path)
        cutoff = reference[name]
        values = sorted(scores.values(), reverse=True)
        strict = sum(1 for score in values if score > cutoff)
        inclusive = sum(1 for score in values if score >= cutoff)
        attainable, run, seen = set(), 0, None
        for score in values:
            if seen is not None and score != seen:
                attainable.add(run)
            run += 1
            seen = score
        attainable.add(run)
        target = stored[name]
        detectors[name] = {
            "cutoff": cutoff, "covered_objects": len(scores), "distinct_scores": len(set(values)),
            "kept_strictly_above": strict, "kept_at_or_above": inclusive,
            "tied_exactly_at_the_cutoff": inclusive - strict,
            "stored_kept_count": target,
            "rule_that_reproduces_it": ("strictly greater than the cutoff" if strict == target
                                        else "at or above the cutoff" if inclusive == target
                                        else "neither"),
            "matched_target_94196_attainable": 94196 in attainable,
            "nearest_attainable_below_94196": max((k for k in attainable if k <= 94196), default=0),
            "nearest_attainable_above_94196": min((k for k in attainable if k >= 94196), default=None),
        }
    rules = {entry["rule_that_reproduces_it"] for entry in detectors.values()}
    misses = {name: POPULATION - entry["stored_kept_count"] for name, entry in detectors.items()}
    spread = max(misses.values()) - min(misses.values())
    return {"state": "recomputed", "inputs": bound, "detectors": detectors,
            "tie_rule": ("strictly greater than the cutoff" if rules == {"strictly greater than the cutoff"}
                         else "not a single rule across detectors"),
            "full_scope_misses": misses,
            "residual_mismatch_objects": spread,
            "residual_mismatch_rate": str(Fraction(spread, POPULATION)),
            "why_no_exact_match": ("the matched target is not an attainable kept count for every "
                                   "detector, so no cutoff of any precision produces it"),
            "correction": ("the marginals are described as approximately matched. They are not "
                           "matched, the gap is stated in objects and in rate, and the obstruction "
                           "is the score granularity of one submission, not a tolerance choice")}


def report(submissions=None, path=GRID):
    data = load(path)
    return {
        "artifact_id": "reiyah.preparation-robustness.premise-corrections",
        "version": VERSION,
        "corrects": {"artifact": "reiyah.preparation-robustness.counts", "version": "0.2.0",
                     "sha256": digest(path),
                     "preregistration_sha256": data["preregistration_sha256"],
                     "what_is_corrected": "the interpretation only. The grid's numbers stand"},
        "premise_1_scope_and_cutoff": cutoff_changes(data),
        "premise_2_residual_mismatch": tie_rule(submissions, data),
        "premise_3_not_an_impossibility": {
            "earlier": "zero exact matches was read as a limit on subsetting",
            "correction": ("it is an empirical limitation of this fixed cutoff family on this "
                           "population. Scope conditional statistics remain definable"),
            "kept_distinct": ["a descriptive comparison", "a matched marginal comparison",
                              "a claim about a dependence mechanism"]},
        "premise_4_sensitivity_is_not_cause": {
            "earlier": "the counterfactual cutoff calculation was read as isolating a cause",
            "correction": ("it identifies numerical sensitivity under this procedure. It does not "
                           "identify a physical cause and does not rule out a scope by cutoff "
                           "interaction"),
            "kept_distinct": ["a fixed numerical cutoff", "a fixed achieved operating rate"]},
        "premise_5_parity_is_a_hypothesis": {
            "earlier": "the parities were read as a general property of this kind of analysis",
            "correction": ("they constrain the methods and problems they were found on. Broader "
                           "parity is a hypothesis, and an integration advantage has to be "
                           "measured against an analyst with ordinary tools"),
            "measured_so_far": "research/comparator/0.1.0/end-to-end.json"},
        "premise_6_duplicate_preparations": duplicate_preparations(data),
        "scope": ("this record corrects what was said about the retained grid. It does not "
                  "recompute the grid, does not change the preregistration, and creates no new "
                  "result about coupling"),
    }


def main(argv):
    submissions = None
    destination = None
    for argument in argv[1:]:
        if argument.startswith("--submissions="):
            submissions = argument.split("=", 1)[1]
        else:
            destination = argument
    result = report(submissions)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if destination:
        with open(destination, "w", encoding="utf-8") as handle:
            handle.write(text)
        return 0
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
