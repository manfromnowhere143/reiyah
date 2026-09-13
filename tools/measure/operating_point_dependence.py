"""Where redundancy fails worst, measured against the operating point.

The Gate B measurement lane established that redundancy across genuinely
different kinds buys independence while redundancy across similar kinds does not,
and reported a dependence coefficient for sensor pairs. This is an independent
recomputation from the retained capture counts by a different route, and an
extension: the same coefficient measured across the operating point.

The estimand is the one bound in `docs/ESTIMAND_RSS_DEFINITION_32.md`,

    c = P(both channels miss) / ( P(A misses) * P(B misses) )

computed here over the annotated population with the annotation treated as the
observer that defines that population. Every count is an integer taken from the
retained aggregate file; no raw record, score, token or source identifier enters
this lane.

WHAT THE RECOMPUTATION CONFIRMS, AND WHAT IT QUALIFIES. At every operating point
examined the most coupled pair is a same modality pair, and it is always a lidar
pair. That is the Gate B claim as that lane carefully stated it, reached here from
different counts and a different calculation.

The stronger reading, that every same modality pair beats every cross modality
pair, is NOT supported. It fails at every operating point examined, for two
separate reasons. The two camera pair sits below the most coupled cross modality
pair almost throughout, which the Gate B lane had already noted. And near a
captured fraction of 0.79 a camera and lidar pair reaches 1.569 while a lidar pair
sits at 1.386, so even lidar dominance is not pairwise. Same kind redundancy is
more coupled AT THE TOP, not pair by pair, and a design rule stated pairwise would
be wrong.

WHAT THE EXTENSION ADDS, AND WHY IT MATTERS. The magnitude is not robust at all.
`c` falls towards 1 as the score threshold rises and the captured fraction drops,
and it grows sharply as the threshold falls and capture approaches the annotated
population. A safety argument is written at the operating point a system actually
runs at, which is the high capture end, and that is precisely where the
independence assumption is worst. A redundancy claim validated at a conservative
operating point can look sound and be wrong by a large factor at the operating
point it ships at.

This says nothing about any vendor's architecture. These are five public research
detectors sharing a training split, and shared provenance is one reason a
coefficient exceeds 1. What transfers is the method and the shape of the curve,
not the numbers.

Exact rational arithmetic, standard library only. Reads one retained counts file.
"""
from fractions import Fraction
import json
import os
import sys

VERSION = "0.1.0"
COUNTS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "research", "operating-point-dependence", "0.1.0",
    "capture-counts.json")


class CountsError(Exception):
    """The retained counts are not in the shape this analysis requires."""


def load(path=COUNTS):
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("artifact_id") != "reiyah.operating-point-dependence.counts":
        raise CountsError("the file is not the retained capture count artifact")
    return data


def coefficient(row, population):
    """c for one pair at one operating point, exactly. None where undefined."""
    first, second = row["first_missed"], row["second_missed"]
    if first == 0 or second == 0:
        # A channel that misses nothing has a zero miss probability and the ratio
        # has no value. Undefined is not one and is not zero.
        return None
    return Fraction(row["both_missed"] * population, first * second)


def by_operating_point(data=None):
    """Every pair's coefficient, grouped by operating point."""
    data = data or load()
    population = data["population"]["objects"]
    recall = {row["threshold"]: row["recall_of_union"]
              for row in data["rows"] if "recall_of_union" in row}
    points = {}
    for row in data["rows"]:
        if "both_missed" not in row:
            continue
        value = coefficient(row, population)
        entry = points.setdefault(row["threshold"], {
            "threshold": row["threshold"], "captured_fraction": recall.get(row["threshold"]),
            "pairs": []})
        entry["pairs"].append({"pair": f"{row['first']}/{row['second']}", "kind": row["kind"],
                               "modalities": row["modalities"],
                               "coefficient": None if value is None else str(value),
                               "value": value})
    return [points[k] for k in sorted(points)]


def ordering(point):
    """Three separate questions about one operating point.

    Reported separately because they have different answers, and collapsing them
    into one boolean is how a design rule ends up stated pair by pair when only
    the weaker version is true.
    """
    same = [p["value"] for p in point["pairs"]
            if p["kind"] == "same_modality" and p["value"] is not None]
    cross = [p["value"] for p in point["pairs"]
             if p["kind"] == "cross_modality" and p["value"] is not None]
    lidar = [p["value"] for p in point["pairs"]
             if p["modalities"] == ["lidar", "lidar"] and p["value"] is not None]
    if not same or not cross:
        return None
    others = cross + [v for v in same if v not in lidar]
    return {
        "most_coupled_pair_is_same_modality": max(same) > max(cross),
        "most_coupled_pair_is_two_lidar": bool(lidar) and max(lidar) > max(others),
        "every_same_modality_pair_beats_every_cross_pair": min(same) > max(cross),
        "every_two_lidar_pair_beats_every_cross_pair": bool(lidar) and min(lidar) > max(cross),
    }


def summarise(data=None):
    """The recomputation and the extension, as one reportable object."""
    points = by_operating_point(data)
    rows = []
    for point in points:
        same = [p["value"] for p in point["pairs"]
                if p["modalities"] == ["lidar", "lidar"] and p["value"] is not None]
        camera = [p["value"] for p in point["pairs"]
                  if p["modalities"] == ["camera", "camera"] and p["value"] is not None]
        cross = [p["value"] for p in point["pairs"]
                 if p["kind"] == "cross_modality" and p["value"] is not None]
        rows.append({
            "threshold": point["threshold"],
            "captured_fraction": point["captured_fraction"],
            "two_lidar": [str(min(same)), str(max(same))] if same else None,
            "two_camera": [str(min(camera)), str(max(camera))] if camera else None,
            "cross_modality": [str(min(cross)), str(max(cross))] if cross else None,
            "ordering": ordering(point)})
    highest = points[0]
    lowest = points[-1]
    top = max(p["value"] for p in highest["pairs"] if p["value"] is not None)
    bottom = max(p["value"] for p in lowest["pairs"] if p["value"] is not None)
    return {
        "artifact_id": "reiyah.operating-point-dependence.report", "version": VERSION,
        "estimand": "the coefficient bound in docs/ESTIMAND_RSS_DEFINITION_32.md",
        "independent_recomputation": {
            "claim_being_rechecked": ("redundancy across genuinely different kinds buys "
                                      "independence; redundancy across similar kinds does not, "
                                      "established by the Gate B measurement lane"),
            "operating_points_checked": len(rows),
            "confirmed": {
                "most_coupled_pair_is_same_modality_everywhere": all(
                    row["ordering"]["most_coupled_pair_is_same_modality"] for row in rows),
                "and_it_is_always_a_lidar_pair": all(
                    row["ordering"]["most_coupled_pair_is_two_lidar"] for row in rows)},
            "qualified": {
                "every_same_modality_pair_beats_every_cross_pair_anywhere": any(
                    row["ordering"]["every_same_modality_pair_beats_every_cross_pair"]
                    for row in rows),
                "every_two_lidar_pair_beats_every_cross_pair_anywhere": any(
                    row["ordering"]["every_two_lidar_pair_beats_every_cross_pair"]
                    for row in rows),
                "reading": ("same kind redundancy is more coupled at the top, not pair by pair. "
                            "A design rule stated pairwise would be wrong")},
            "status": ("an independent recomputation from retained aggregate counts, not a new "
                       "claim and not a replacement for that lane's own evidence")},
        "extension": {
            "finding": ("the ordering is robust to the operating point and the magnitude is not. "
                        "The coefficient falls towards 1 as capture falls and rises sharply as "
                        "capture approaches the annotated population"),
            "most_coupled_at_highest_capture": str(top),
            "most_coupled_at_lowest_capture": str(bottom),
            "ratio_across_the_sweep": str(top / bottom) if bottom else None,
            "why_it_matters": ("a safety argument is written at the operating point a system runs "
                               "at, which is the high capture end, and that is where the "
                               "independence assumption is worst. A redundancy claim validated at "
                               "a conservative operating point can look sound and be wrong by a "
                               "large factor where it ships")},
        "rows": rows,
        "scope": ("five public research detectors over one annotated validation population at one "
                  "match rule. They share a training split, and shared provenance is one reason a "
                  "coefficient exceeds 1. Nothing here measures any vendor architecture, and the "
                  "numbers do not transfer; the method and the shape of the curve are what do"),
        "not_established": [
            "any statistical uncertainty, resampling band or sampling model",
            "that the annotated population is physically complete",
            "that any deployed system has this coefficient",
            "any safety conclusion about any vehicle"],
    }


def main(argv):
    try:
        report = summarise(load(argv[1]) if len(argv) > 1 else None)
    except (CountsError, OSError) as error:
        sys.stderr.write(f"counts refused: {error}\n")
        return 1
    json.dump(report, sys.stdout, indent=2, sort_keys=True, default=str)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
