"""The safety quantity the ratio was standing in for, and three corrections.

`docs/ESTIMAND_RSS_DEFINITION_32.md` carries a normative clause, number 4:

    "c is not comparable across operating points. Any contrast must match or
     condition on marginals."

and counterexample CE-4 shows why: one channel's operating point moved with the
coupling structure untouched sends `c` from 1.8186 to 1.2262. This lane published
a document that compared `c` across nine operating points and read the 5.29 times
movement as evidence that independence is worst where a system deploys. **That
violated this programme's own binding rule**, and an external review caught it.

The permitted quantity is the ABSOLUTE excess joint miss rate,

    delta  =  P(both miss)  -  P(A misses) * P(B misses)

which is the extra joint failures per object above independence. It is not a
ratio of two shrinking marginals, so it carries no normalisation artifact, and it
is the quantity a safety budget is actually denominated in.

WHAT IT SHOWS, AND IT REVERSES THE EARLIER READING. The absolute excess does not
rise towards the deployment end. It **peaks at intermediate capture**, near 0.90,
and falls away on both sides. At the highest capture examined it is 38.8 to 87.4
per thousand objects, BELOW the 66.2 to 139.5 at capture 0.898. So the ratio rose
while the burden fell, which is exactly the artifact CE-4 predicts. The sentence
"independence is worst exactly where safety cases live" is withdrawn, not
softened.

A SECOND CORRECTION, ON NOVELTY. Assessing sensor reliability and error
dependence without a reference truth is not new. Berk, Schubert, Kroll, Buschardt
and Straub, "Reliability Assessment of Safety-Critical Sensor Information: Does
One Need a Reference Truth?", IEEE Transactions on Reliability, 2019, addresses
that category directly, and estimating classifier accuracies from unlabelled
predictions is established statistics, for instance Jaffe, Nadler and Kluger,
AISTATS 2015. Any novelty this lane holds is narrower: a label free sign and
bound for this particular Definition 32 constant, under stated assumptions, with
a breakdown guarantee. That is what should be claimed, and nothing wider.

A THIRD RESULT, NEGATIVE. If the coupling were concentrated in a small region of
the population, a designer could restrict the operating domain and recover
redundancy. It is not. The worst 5 percent of the population by excess carries
only 7 to 14 percent of the total excess, and the worst 25 percent carries 31 to
45. **The failure is diffuse.** There is no small blind spot to exclude, and the
tempting product idea of a blind spot atlas is refuted by this lane's own data.

Exact rational arithmetic, standard library only. Reads one retained counts file.
"""
from fractions import Fraction
import json
import os
import sys

VERSION = "0.1.0"
COUNTS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "research", "excess-joint-risk", "0.1.0", "excess-counts.json")


class CountsError(Exception):
    """The retained counts are not in the shape this analysis requires."""


def load(path=COUNTS):
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("artifact_id") != "reiyah.excess-joint-risk.counts":
        raise CountsError("the file is not the retained excess joint risk artifact")
    return data


def excess(row):
    """delta = P(both miss) - P(A misses) P(B misses), exactly."""
    n = Fraction(row["population"])
    return (Fraction(row["both_missed"]) / n
            - Fraction(row["first_missed"]) / n * Fraction(row["second_missed"]) / n)


def ratio(row):
    """c, retained only to show what it does where it is not comparable."""
    if row["first_missed"] == 0 or row["second_missed"] == 0:
        return None
    return Fraction(row["both_missed"] * row["population"],
                    row["first_missed"] * row["second_missed"])


def sweep(data=None):
    """Both quantities across the operating point, so the divergence is visible."""
    data = data or load()
    points = {}
    for row in data["operating_point_sweep"]:
        entry = points.setdefault(row["threshold"], {
            "threshold": row["threshold"],
            "captured_fraction": Fraction(row["union_captured"], row["population"]),
            "excess": [], "ratio": []})
        entry["excess"].append(excess(row))
        value = ratio(row)
        if value is not None:
            entry["ratio"].append(value)
    out = []
    for key in sorted(points):
        entry = points[key]
        out.append({
            "threshold": key, "captured_fraction": str(entry["captured_fraction"]),
            "excess_per_thousand": [str(min(entry["excess"]) * 1000),
                                    str(max(entry["excess"]) * 1000)],
            "ratio": [str(min(entry["ratio"])), str(max(entry["ratio"]))]})
    return out


def report(data=None):
    data = data or load()
    rows = sweep(data)
    peak = max(rows, key=lambda r: Fraction(r["excess_per_thousand"][1]))
    highest_capture = max(rows, key=lambda r: Fraction(r["captured_fraction"]))
    concentration = data["excess_concentration_at_matched_0_30"]
    worst_five = [Fraction(c["excess_share_by_population_percent"]["5"]) for c in concentration]
    worst_quarter = [Fraction(c["excess_share_by_population_percent"]["25"]) for c in concentration]
    return {
        "artifact_id": "reiyah.excess-joint-risk.report", "version": VERSION,
        "withdrawn": {
            "claim": ("independence is worst exactly where safety cases live, at the high capture "
                      "operating point"),
            "why": ("it compared c across operating points, which clause 4 of this programme's own "
                    "estimand contract forbids, and CE-4 shows the movement can be pure "
                    "normalisation with the coupling structure untouched"),
            "found_by": "an external review, not by this lane"},
        "permitted_quantity": "the absolute excess joint miss rate, P(both) minus P(A) P(B)",
        "what_the_absolute_excess_does": {
            "peak_at_captured_fraction": peak["captured_fraction"],
            "peak_excess_per_thousand": peak["excess_per_thousand"],
            "at_highest_capture": highest_capture["excess_per_thousand"],
            "reading": ("the burden peaks at intermediate capture and falls away on both sides. "
                        "The ratio rose while the burden fell, which is the artifact CE-4 predicts")},
        "failure_is_diffuse_not_localised": {
            "worst_five_percent_of_population_carries": [str(min(worst_five)), str(max(worst_five))],
            "worst_quarter_carries": [str(min(worst_quarter)), str(max(worst_quarter))],
            "consequence": ("there is no small region to exclude from an operating domain. A blind "
                            "spot atlas would have nothing to point at, and that product idea is "
                            "refuted by this lane's own data")},
        "novelty_corrected": {
            "not_claimed": ("that assessing sensor reliability or error dependence without a "
                            "reference truth is new"),
            "prior_art": ["Berk, Schubert, Kroll, Buschardt and Straub, Reliability Assessment of "
                          "Safety-Critical Sensor Information: Does One Need a Reference Truth?, "
                          "IEEE Transactions on Reliability, 2019",
                          "Jaffe, Nadler and Kluger, estimating classifier accuracies from "
                          "unlabelled predictions, AISTATS 2015"],
            "what_may_be_narrow_and_new": ("a label free sign and bound for this particular "
                                           "Definition 32 constant, under stated assumptions, with "
                                           "a breakdown guarantee. Nothing wider")},
        "sweep": rows,
        "not_settled": [
            "whether any part of the ratio's movement reflects changing dependence rather than "
            "normalisation is an open identification problem and is not answered here",
            "the architecture against modality comparison rests on two same modality pairs per "
            "cell and is suggestive, not established",
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
