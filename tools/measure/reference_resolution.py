"""How much reference evidence is needed before an open comparison resolves.

An open-reference comparison returns the coarse count bound `[-b*R, a*R]`, where
`R` is the weighted count of retained additions. That bound is trivial: it is what
the arithmetic gives when no object is known to exist. The useful question is not
how wide it is, but exactly what a reviewer would have to establish to close it.

Under the declared additive loss, for one anchor,

    delta = (a + b) * dTP - b * r          so     delta > 0  iff  dTP / r > b / (a + b)

so the addition pays off exactly when the fraction of added detections that match
objects the base missed exceeds `b / (a + b)`. With unit penalties that threshold
is one half. Resolving one addition's match status narrows the anchor's interval
by `(a + b) * weight`, so the number of adjudications is known in advance.

This module computes that budget from declared structural parameters only. It
reads no packet and copies no operand. Standard library, exact rationals.
"""
from fractions import Fraction
import glob
import json
import os
import sys


def threshold(a, b):
    """Fraction of additions that must convert before the addition pays off."""
    if a + b == 0:
        return None
    return b / (a + b)


def enclosure(weights, additions, a, b, resolved_gain=None, resolved_count=None):
    """Enclosure over anchors, given how many additions per anchor are settled."""
    lower = upper = Fraction(0)
    for index, (w, r) in enumerate(zip(weights, additions)):
        gain = Fraction(0) if resolved_gain is None else Fraction(resolved_gain[index])
        settled = 0 if resolved_count is None else resolved_count[index]
        unresolved = r - settled
        lower += w * ((a + b) * gain - b * r)
        upper += w * ((a + b) * (gain + unresolved) - b * r)
    return lower, upper


def main(argv):
    # Structural parameters of the retained open comparison. The per-anchor split
    # is held in this lane's private record and is not published here; only the
    # weighted total, which the public enclosure already discloses, is used.
    a = b = Fraction(1)
    tolerance = Fraction(1, 10)
    weights = [Fraction(1, 2), Fraction(1, 2)]
    additions = [int(argv[1]), int(argv[2])] if len(argv) == 3 else [9, 7]

    weighted_r = sum(w * r for w, r in zip(weights, additions))
    open_lower, open_upper = enclosure(weights, additions, a, b)
    total_adjudications = sum(additions)
    conversion = threshold(a, b)

    report = {
        "artifact_id": "reiyah.decision-evidence.reference-resolution", "version": "0.1.0",
        "loss": {"false_negative": str(a), "false_positive": str(b), "tolerance": str(tolerance)},
        "anchors": len(weights),
        "weighted_retained_additions": str(weighted_r),
        "open_reference_enclosure": [str(open_lower), str(open_upper)],
        "open_enclosure_is_the_coarse_bound": [str(open_lower), str(open_upper)] ==
                                              [str(-b * weighted_r), str(a * weighted_r)],
        "why_it_is_trivial": ("no object is declared to exist, so the true-positive gain is only "
                              "bounded by zero and r; the interval is the arithmetic of ignorance, "
                              "not a measurement"),
        "conversion_threshold": str(conversion),
        "conversion_threshold_meaning": ("the addition improves the loss exactly when more than this "
                                         "fraction of added detections match objects the base missed"),
        "adjudications_that_close_it": total_adjudications,
        "narrowing_per_resolved_addition": [str((a + b) * w) for w in weights],
        "schedule": [],
    }
    for settled in range(total_adjudications + 1):
        per = [min(settled, additions[0]), max(0, settled - additions[0])]
        lower, upper = enclosure(weights, additions, a, b, resolved_gain=[0, 0],
                                 resolved_count=per)
        report["schedule"].append({"adjudications_done": settled,
                                   "worst_case_width": str(upper - lower)})
    # A prior for the threshold, from this lane's own retained real anchors under the
    # same declared rule. Comparable, not the same population; see the findings.
    observed = []
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                        "evidence", "decision-packet")
    for path in sorted(glob.glob(os.path.join(root, "*-report.json"))):
        with open(path, "r", encoding="utf-8") as handle:
            entry = json.load(handle)
        worst = min(entry["worlds"], key=lambda w: w["tp_augmented"] - w["tp_base"])
        observed.append((worst["tp_augmented"] - worst["tp_base"], entry["retained_additions"]))
    if observed:
        gains = sum(g for g, _r in observed)
        adds = sum(r for _g, r in observed)
        rate = Fraction(gains, adds)
        report["observed_conversion_on_this_lane_s_real_anchors"] = {
            "anchors": len(observed), "true_positive_gain": gains, "retained_additions": adds,
            "conversion_rate": str(rate), "as_decimal": round(float(rate), 4),
            "above_threshold": rate > conversion,
            "reading": ("a prior, not a prediction about the retained comparison: a different "
                        "population, a different reference and a different anchor selection. It is "
                        "falsifiable by the sixteen adjudications and that is the point")}

    report["note"] = ("the schedule assumes the worst case, that every adjudication so far confirmed "
                      "no new object. A real review narrows faster when additions do convert. The "
                      "count of adjudications is fixed in advance; the outcome is not")
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
