"""How much of an annotation conditional verdict rests on any one label.

The conventional answer to this decision treats the benchmark annotation as the
complete and correct reference and reports one number. On the Engine's exported
case that number is a weighted improvement of 1 against a tolerance of 1/10, so
the addition is supported. The number is correct. What it does not say is how much
of itself rests on individual labels being right.

This enumerates a declared family: the unchanged baseline, and each deletion of
exactly one included annotation, one at a time. A deletion is a HYPOTHETICAL
spurious label correction. It is not an observed error, a probability model, a
physical reading or a human admission, and it tests only that one family. Missing
objects, localization error and class error are different families and are not
touched here.

Both matchings are recomputed from scratch in every case. That is not an
efficiency oversight: removing one object can free a detection to match a
different object, so matching competition reassigns, and a per case result
inferred from the baseline would be wrong. The cost of doing it honestly is
measured rather than hidden.

WHAT IS REPORTED. The exact range of weighted deltas across the family, the count
for every criterion and preference outcome, and three outcomes kept apart that are
easy to collapse into one: a loss sign change, a tolerance crossing, and a change
to unresolved. If any deletion changes the criterion, the case is retained with a
source bound witness naming which label and why. If none does, the result is
robustness under this family only, which is a weaker statement than it sounds.

CUSTODY. The case is another owner's export and its object identifiers are source
derived annotation tokens. This module reads it by path under a digest check and
never reproduces an identifier. A witness is named by anchor, class and the local
index of the label inside its anchor, which the owner can resolve and which
carries nothing.

Exact rational arithmetic, standard library only.
"""
from fractions import Fraction
import copy
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from itertools import combinations  # noqa: E402

from cohort_packet import CaseError, build, maximum_matching  # noqa: E402

VERSION = "0.4.0"
PREREGISTRATION = "24cb90eff90f60431fd92cd25e504842eb24898e1ec40c1cc4399601e38cfe5d"
INSERTION_PREREGISTRATION = "38af5ed9442632919b51751ee09693da2a13ca62626291624613f3978a9c8c72"


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def labels(case):
    """Every included annotation, as (anchor, local index, class), in a fixed order."""
    rows = []
    for anchor in case["anchors"]:
        for index, obj in enumerate(anchor.get("objects", [])):
            rows.append({"anchor": anchor["id"], "local_index": index, "class": obj["class"],
                         "_id": obj["id"]})
    return rows


def without(case, anchor_id, object_id):
    """The same case with one annotation removed from the reference and every world."""
    edited = copy.deepcopy(case)
    for anchor in edited["anchors"]:
        if anchor["id"] != anchor_id:
            continue
        anchor["objects"] = [o for o in anchor["objects"] if o["id"] != object_id]
    for world in edited["joint_worlds"]:
        body = world["per_anchor"].get(anchor_id)
        if body is None:
            continue
        body["objects_present"] = [o for o in body["objects_present"] if o != object_id]
        body["edges"] = [e for e in body["edges"] if e[1] != object_id]
    return edited


def unmatched_detections(case):
    """Retained detections the augmented configuration leaves unmatched, per anchor.

    Each one is the subject of exactly one insertion hypothesis: this detection is
    right and the annotation missed the object. Nothing about its position is
    invented, because the position is the detection's own.
    """
    report = build(case)
    out = []
    for world in report["joint_worlds"]:
        for entry in world["anchors"]:
            matched = {pair[0] for pair in entry["augmented_certificate"]["matching"]}
            anchor = next(a for a in case["anchors"] if a["id"] == entry["anchor"])
            rows = anchor["base_detections"] + anchor["added_detections"]
            roles = {d["id"]: "base" for d in anchor["base_detections"]}
            roles.update({d["id"]: "added" for d in anchor["added_detections"]})
            for detection in rows:
                if detection["id"] not in matched:
                    out.append({"anchor": entry["anchor"], "detection": detection["id"],
                                "class": detection["class"], "role": roles[detection["id"]],
                                "world": world["world_id"]})
    return out


class GeometryRequired(ValueError):
    """An insertion needs coordinates, and this module will not guess them."""


def positions(operands_path):
    """Detection coordinates per anchor, from the common operands.

    Exact rationals, not floats, because the 2 metre rule is a strict inequality and
    a boundary case decided by rounding would be a silent error.
    """
    with open(operands_path, "r", encoding="utf-8") as handle:
        operands = json.load(handle)
    out = {}
    for anchor in operands["anchors"]:
        rows = {}
        for record in anchor["qualified_records"]:
            body = record["record"]
            rows[record["detection"]["id"]] = (
                Fraction(int(body["xy"][0]["numerator"]), int(body["xy"][0]["denominator"])),
                Fraction(int(body["xy"][1]["numerator"]), int(body["xy"][1]["denominator"])))
        out[anchor["anchor_id"]] = rows
    return out


def with_insertions(case, hypotheses, coordinates):
    """The same case with a missed object added at each named detection's own position.

    0.4.0 CORRECTION. Version 0.2.0 joined the inserted object to every same class
    detection that already shared one of its detection's objects. That is a graph
    neighbourhood and not a distance. The consumer's retained control shows the gap:
    detections at (0, 0) and (3, 0) sharing an object at (1.5, 0), and an insertion at
    (3, 0). Under the declared strict 2 metre rule only the detection at (3, 0)
    reaches it; the graph rule connects both. On the first case all 20 singles and
    190 pairs happened to agree with the coordinates, which is luck and not a reason.

    Reachability is now the declared rule applied to the supplied coordinates: same
    class, strictly within 2 metres of the insertion's position. Coordinates are
    required. Without them this raises rather than falling back on a heuristic.
    """
    if not coordinates:
        raise GeometryRequired(
            "an insertion needs the detection coordinates from the common operands. "
            "The graph neighbourhood rule used in 0.2.0 is withdrawn because it is not a "
            "distance, and no substitute is guessed here")
    edited = copy.deepcopy(case)
    by_anchor = {}
    for index, row in enumerate(hypotheses):
        by_anchor.setdefault(row["anchor"], []).append((index, row))
    for anchor in edited["anchors"]:
        rows = by_anchor.get(anchor["id"])
        if not rows:
            continue
        for index, row in rows:
            anchor["objects"].append({"id": f"inserted-{index}", "class": row["class"]})
    for world in edited["joint_worlds"]:
        for anchor_id, body in world["per_anchor"].items():
            rows = by_anchor.get(anchor_id)
            if not rows:
                continue
            here = coordinates.get(anchor_id)
            if not here:
                raise GeometryRequired(f"no coordinates supplied for anchor {anchor_id}")
            source = next(a for a in case["anchors"] if a["id"] == anchor_id)
            classes = {d["id"]: d["class"]
                       for d in source["base_detections"] + source["added_detections"]}
            for index, row in rows:
                name = f"inserted-{index}"
                if row["detection"] not in here:
                    raise GeometryRequired(f"no coordinate for detection {row['detection']}")
                x, y = here[row["detection"]]
                body["objects_present"].append(name)
                for detection, klass in sorted(classes.items()):
                    if klass != row["class"] or detection not in here:
                        continue
                    other = here[detection]
                    if (x - other[0]) ** 2 + (y - other[1]) ** 2 < 4:
                        body["edges"].append([detection, name])
    return edited


def evaluate(case):
    """The declared decision on one case, recomputed in full."""
    report = build(case)
    decision = report["decision"]
    per_anchor = {}
    for world in report["joint_worlds"]:
        for entry in world["anchors"]:
            per_anchor[entry["anchor"]] = {
                "delta": entry["delta"], "tp_base": entry["tp_base"],
                "tp_augmented": entry["tp_augmented"]}
    return {"enclosure": report["enclosure"],
            "weighted_delta": report["enclosure"]["lower"],
            "criterion": decision["improvement_criterion"],
            "preference": decision["preference"],
            "per_anchor": per_anchor,
            "point": report["enclosure"]["lower"] == report["enclosure"]["upper"]}


def family(case):
    """The baseline and every single deletion, each recomputed from scratch."""
    baseline = evaluate(case)
    rows = labels(case)
    results = []
    for row in rows:
        edited = without(case, row["anchor"], row["_id"])
        outcome = evaluate(edited)
        results.append({"anchor": row["anchor"], "local_index": row["local_index"],
                        "class": row["class"], "outcome": outcome})
    return baseline, rows, results


def classify(baseline, results, tolerance):
    """Three outcomes that are different events, kept apart."""
    base_delta = Fraction(baseline["weighted_delta"])
    sign_changes, to_zero, crossings, unresolved = [], [], [], []
    deltas = []
    for row in results:
        delta = Fraction(row["outcome"]["weighted_delta"])
        deltas.append(delta)
        name = {"anchor": row["anchor"], "local_index": row["local_index"],
                "class": row["class"], "weighted_delta": str(delta),
                "baseline_weighted_delta": str(base_delta)}
        # A strict sign change and a fall to zero are different events. The first says the
        # addition became harmful; the second says it stopped helping. Only one of those
        # happened here, and calling them the same thing would overstate the finding.
        if (delta > 0 and base_delta < 0) or (delta < 0 and base_delta > 0):
            sign_changes.append(name)
        elif delta == 0 and base_delta != 0:
            to_zero.append(name)
        if row["outcome"]["criterion"] != baseline["criterion"]:
            crossings.append(dict(name, criterion=row["outcome"]["criterion"],
                                  preference=row["outcome"]["preference"]))
        if row["outcome"]["criterion"] == "unresolved":
            unresolved.append(name)
    return {"strict_loss_sign_changes": sign_changes,
            "falls_to_zero_without_changing_sign": to_zero,
            "tolerance_crossings": crossings,
            "changes_to_unresolved": unresolved,
            "weighted_delta_range": {"lowest": str(min(deltas)) if deltas else None,
                                     "highest": str(max(deltas)) if deltas else None},
            "distinct_weighted_deltas": sorted({str(d) for d in deltas},
                                               key=lambda s: Fraction(s))}


def arithmetic_floor(case):
    """The fewest deletions that could cross the tolerance, on arithmetic alone.

    Deleting one annotation reduces its anchor's gain by at most one, so it moves
    the weighted decision by at most `(a + b) * weight_i`. With `k` deletions the
    decision can fall by at most `k` times the largest such step. So no set smaller
    than

        k_floor = ceil( (D - tolerance) / max_i (a + b) * weight_i )

    can change the criterion, whatever the labels are.

    This matters because a case with a comfortable margin can be robust to any
    single deletion for a reason that has nothing to do with its labels. Reporting
    that as robustness would be a false result, and the two cases this lane is
    comparing do not share a margin or a weighting.
    """
    loss = case["loss"]
    a = Fraction(loss["false_negative"])
    b = Fraction(loss["false_positive"])
    tolerance = Fraction(loss["tolerance"])
    baseline = evaluate(case)
    decision = Fraction(baseline["weighted_delta"])
    step = max((a + b) * Fraction(anchor["weight"]) for anchor in case["anchors"])
    margin = decision - tolerance
    if margin <= 0:
        return {"criterion": baseline["criterion"], "margin": str(margin),
                "largest_single_step": str(step), "k_floor": 0,
                "note": "the criterion is not supported, so no deletion is needed to change it"}
    floor = -((-margin) // step)
    return {"criterion": baseline["criterion"], "weighted_delta": str(decision),
            "tolerance": str(tolerance), "margin": str(margin),
            "largest_single_step": str(step), "k_floor": int(floor),
            "why": ("one deletion moves one anchor's gain by at most one, so the decision moves "
                    "by at most (a + b) times that anchor's weight"),
            "consequence": ("no set of fewer than k_floor deletions can change the criterion on "
                            "this case, whatever its labels are. Robustness below k_floor is "
                            "arithmetic and is not evidence about the annotation")}


def breakdown(case, budget=250000):
    """The smallest set of deletions that changes the criterion, searched by size.

    No pruning by single deletion effect is applied, and that is deliberate. Two
    labels can each be absorbed alone and decisive together: the matching reassigns
    around either one, and not around both. A search that discarded labels with no
    individual effect would miss exactly those, so every subset is recomputed.
    """
    baseline = evaluate(case)
    rows = labels(case)
    floor = arithmetic_floor(case)
    start = time.perf_counter()
    evaluations = 0
    for size in range(max(1, floor["k_floor"]), len(rows) + 1):
        total = 1
        for index in range(size):
            total = total * (len(rows) - index) // (index + 1)
        if evaluations + total > budget:
            return {"state": "bracketed", "k_floor": floor["k_floor"],
                    "searched_up_to": size - 1, "evaluations": evaluations,
                    "budget": budget, "witness": None,
                    "seconds": round(time.perf_counter() - start, 3),
                    "conclusion": (f"no set of {size - 1} or fewer deletions changes the criterion; "
                                   f"size {size} exceeds the declared evaluation budget and no "
                                   "smallest set is claimed")}
        for chosen in combinations(rows, size):
            evaluations += 1
            edited = case
            for row in chosen:
                edited = without(edited, row["anchor"], row["_id"])
            outcome = evaluate(edited)
            if outcome["criterion"] != baseline["criterion"]:
                return {"state": "found", "k_observed": size, "k_floor": floor["k_floor"],
                        "at_the_arithmetic_floor": size == floor["k_floor"],
                        "fragility_ratio": str(Fraction(size, max(floor["k_floor"], 1))),
                        "evaluations": evaluations,
                        "seconds": round(time.perf_counter() - start, 3),
                        "witness": [{"anchor": r["anchor"], "local_index": r["local_index"],
                                     "class": r["class"]} for r in chosen],
                        "weighted_delta": outcome["weighted_delta"],
                        "criterion": outcome["criterion"]}
    return {"state": "none_exists", "k_floor": floor["k_floor"], "evaluations": evaluations,
            "seconds": round(time.perf_counter() - start, 3), "witness": None}


def fragility(path, expected=None, budget=250000):
    """The comparable quantity across cases with different weights and margins."""
    found = digest(path)
    if expected is not None and found != expected:
        return {"state": "digest_mismatch", "expected_sha256": expected, "found_sha256": found}
    with open(path, "r", encoding="utf-8") as handle:
        case = json.load(handle)
    floor = arithmetic_floor(case)
    result = breakdown(case, budget)
    return {
        "artifact_id": "reiyah.label-dependence.fragility", "version": VERSION,
        "case_sha256": found,
        "arithmetic_floor": floor,
        "breakdown": result,
        "reading": ({"fragility_ratio": result.get("fragility_ratio"),
                     "meaning": ("one means the verdict is as fragile as its own arithmetic "
                                 "allows: the smallest set that could possibly cross does cross. "
                                 "Larger means the labels carry real redundancy")}
                    if result.get("state") == "found" else
                    {"fragility_ratio": None,
                     "meaning": ("the search did not reach a smallest set within its budget, so no "
                                 "ratio is claimed")}),
        "scope": ("deletions only, one supplied benchmark interpretation. The ratio compares a "
                  "case against its own arithmetic, which is what makes two cases with different "
                  "weights and margins comparable at all. It is not a probability"),
    }


def analyse(path, expected=None):
    """The whole declared family on one case, with its costs."""
    found = digest(path)
    if expected is not None and found != expected:
        return {"state": "digest_mismatch", "expected_sha256": expected, "found_sha256": found}
    with open(path, "r", encoding="utf-8") as handle:
        case = json.load(handle)
    tolerance = Fraction(case["loss"]["tolerance"])

    start = time.perf_counter()
    baseline, rows, results = family(case)
    elapsed = time.perf_counter() - start

    counts = {}
    for row in results:
        key = (row["outcome"]["criterion"], row["outcome"]["preference"])
        counts[" / ".join(key)] = counts.get(" / ".join(key), 0) + 1
    events = classify(baseline, results, tolerance)

    return {
        "artifact_id": "reiyah.label-dependence.report", "version": VERSION,
        "preregistration_sha256": PREREGISTRATION,
        "case_sha256": found,
        "family": {"declared_cases": len(rows) + 1, "baseline": 1, "deletions": len(rows)},
        "baseline": baseline,
        "tolerance": str(tolerance),
        "outcome_counts": counts,
        "events": events,
        "robust_under_this_family": not events["tolerance_crossings"],
        "breakdown_number": (1 if events["tolerance_crossings"] else None),
        "breakdown_meaning": ("the smallest number of single label deletions in this family that "
                              "changes the improvement criterion. One means the verdict does not "
                              "survive a single spurious annotation among the named witnesses"),
        "cost": {"seconds": round(elapsed, 4),
                 "recomputations": 2 * (len(rows) + 1) * len(case["anchors"]),
                 "note": ("every case recomputes both matchings at both anchors. A result inferred "
                          "from the baseline would miss matching reassignment")},
        "scope": ("one deletion family on one supplied benchmark interpretation. Robustness here "
                  "is robustness to single spurious labels and to nothing else. It is not a label "
                  "accuracy assessment, a physical reference or evidence of decision value"),
    }


def insertion_family(path, operands_path, expected=None, pairs=True):
    """The declared insertion family: one missed object per unmatched retained detection."""
    found = digest(path)
    if expected is not None and found != expected:
        return {"state": "digest_mismatch", "expected_sha256": expected, "found_sha256": found}
    coordinates = positions(operands_path)
    with open(path, "r", encoding="utf-8") as handle:
        case = json.load(handle)
    baseline = evaluate(case)
    candidates = unmatched_detections(case)
    start = time.perf_counter()
    singles = []
    for index, row in enumerate(candidates):
        outcome = evaluate(with_insertions(case, [row], coordinates))
        singles.append({"anchor": row["anchor"], "class": row["class"], "role": row["role"],
                        "outcome": outcome})
    crossings = [s for s in singles if s["outcome"]["criterion"] != baseline["criterion"]]
    deltas = [Fraction(s["outcome"]["weighted_delta"]) for s in singles]
    result = {
        "artifact_id": "reiyah.label-dependence.insertion-report", "version": VERSION,
        "preregistration_sha256": INSERTION_PREREGISTRATION,
        "case_sha256": found,
        "baseline": baseline,
        "candidates": {"total": len(candidates),
                       "by_role": {role: sum(1 for c in candidates if c["role"] == role)
                                   for role in ("base", "added")},
                       "by_anchor": {a["id"]: sum(1 for c in candidates if c["anchor"] == a["id"])
                                     for a in case["anchors"]}},
        "singles": {"cases": len(singles),
                    "weighted_delta_range": {"lowest": str(min(deltas)) if deltas else None,
                                             "highest": str(max(deltas)) if deltas else None},
                    "distinct_weighted_deltas": sorted({str(d) for d in deltas},
                                                       key=lambda t: Fraction(t)),
                    "criterion_changes": len(crossings),
                    "witnesses": [{"anchor": c["anchor"], "class": c["class"], "role": c["role"],
                                   "weighted_delta": c["outcome"]["weighted_delta"],
                                   "criterion": c["outcome"]["criterion"]}
                                  for c in crossings[:12]]},
        "geometry": ("the declared strict 2 metre rule applied to the supplied coordinates. The "
                     "0.2.0 graph neighbourhood rule is withdrawn"),
        "direction": ("an insertion that only the added configuration reaches raises the delta; "
                      "one that the base also reaches does not. Which way the annotation actually "
                      "fails is not established here"),
    }
    if not crossings and pairs:
        pair_deltas = []
        found_pair = None
        for i in range(len(candidates)):
            for j in range(i + 1, len(candidates)):
                outcome = evaluate(with_insertions(case, [candidates[i], candidates[j]],
                                                   coordinates))
                pair_deltas.append(Fraction(outcome["weighted_delta"]))
                if outcome["criterion"] != baseline["criterion"]:
                    found_pair = {"first": {"anchor": candidates[i]["anchor"],
                                            "class": candidates[i]["class"],
                                            "role": candidates[i]["role"]},
                                  "second": {"anchor": candidates[j]["anchor"],
                                             "class": candidates[j]["class"],
                                             "role": candidates[j]["role"]},
                                  "weighted_delta": outcome["weighted_delta"],
                                  "criterion": outcome["criterion"]}
                    break
            if found_pair:
                break
        result["pairs"] = {
            "searched": True, "cases": len(pair_deltas), "witness": found_pair,
            "weighted_delta_range": {"lowest": str(min(pair_deltas)) if pair_deltas else None,
                                     "highest": str(max(pair_deltas)) if pair_deltas else None},
            "conclusion": ("a pair changes the criterion" if found_pair
                           else "no single and no pair changes the criterion"),
            "note": ("the pair extrema are recorded separately from the singles. 0.2.0 reported "
                     "the singles range only, which understated the reach of this family")}
    result["breakdown_number"] = (1 if crossings else
                                  (2 if result.get("pairs", {}).get("witness") else None))
    result["cost"] = {"seconds": round(time.perf_counter() - start, 4)}
    result["scope"] = ("one insertion rule on one supplied benchmark interpretation. Counts of "
                       "hypothetical corrections are not likelihoods, and no claim is made about "
                       "how often this annotation actually misses an object")
    return result


def main(argv):
    if len(argv) not in (2, 3):
        sys.stderr.write("usage: label_dependence.py CASE.json [EXPECTED_SHA256]\n")
        return 2
    try:
        result = analyse(argv[1], argv[2] if len(argv) == 3 else None)
    except CaseError as error:
        sys.stderr.write(f"case refused: {error}\n")
        return 1
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
