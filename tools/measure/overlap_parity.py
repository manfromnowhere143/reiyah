"""What the dependence coefficient adds over ordinary set overlap, which is nothing here.

An Engine consumer checked this lane's selected tables without importing its code
and reported that ordinary Jaccard overlap reproduces the coefficient's ordering
in every comparison. That is the competent conventional analyst this lane is
supposed to beat, so it was given a fair opportunity to succeed, and it succeeded.

THE IDENTITY, DERIVED HERE RATHER THAN ACCEPTED. Take an exactly matched universe:
`N` observed objects, a common unseen count `m`, each channel capturing `k`, pair
intersection `w`, and `d = N - k`. Each channel misses `(N + m) - k = d + m`, and
both miss `(N + m) - (2k - w) = N - 2k + w + m`. So

    c(m) = (N + m) * (N - 2k + w + m) / (d + m)^2

and for two pairs at the same `k`,

    c_1(m) - c_2(m) = (N + m) * (w_1 - w_2) / (d + m)^2.

The factor is strictly positive, so `sign(c_1 - c_2) = sign(w_1 - w_2)`:
**ordering by the coefficient is ordering by intersection size, for every common
unseen count.** Jaccard `w / (2k - w)` has derivative `2k / (2k - w)^2 > 0` in `w`
at `k > 0`, so it induces the same ordering. Checked on 4,000 random
configurations with no disagreement.

THE EMPIRICAL PARITY. The real tables do not have exactly matched marginals, so
the identity is a comparator under its premise rather than a proof about them.
Tested directly instead: across the 270 pairwise comparisons available in this
lane's own retained counts, **Jaccard agrees with the coefficient 270 times out of
270.** The conventional baseline reaches the same conclusion at lower cost.

The consequence is plain. For the ORDERING claim this lane has been making, the
dependence coefficient earns nothing over ordinary overlap. Any value the
instrument holds must be earned elsewhere: faithful source preparation from raw
detections, useful abstention, sensitivity to association error, a cheaper review
procedure, or a better integration choice under the additive loss. Not here.

A SECOND DEFECT, IN THIS LANE'S OWN COMPARISON. The rows labelled label free were
thresholded against the union of what any channel captured, but evaluated against
a smaller per pair universe. Their actual miss fractions are `0.238`, `0.299` and
`0.363`, not the nominal `0.30`, `0.40` and `0.50` of the annotated rows. **The two
views were never compared at matched marginals**, so the earlier observation that
the label free margin was wider does not establish stronger evidence and is
withdrawn.

Exact rational arithmetic, standard library only. Reads one retained counts file.
"""
from fractions import Fraction
import itertools
import json
import os
import random
import sys

VERSION = "0.1.0"
COUNTS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "research", "overlap-parity", "0.1.0", "overlap-counts.json")


class CountsError(Exception):
    """The retained counts are not in the shape this analysis requires."""


def load(path=COUNTS):
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("artifact_id") != "reiyah.overlap-parity.counts":
        raise CountsError("the file is not the retained overlap parity artifact")
    return data


def coefficient(row):
    a = row["population"] - row["captured_first"]
    b = row["population"] - row["captured_second"]
    if a == 0 or b == 0:
        return None
    return Fraction(row["both_missed"] * row["population"], a * b)


def jaccard(row):
    if row["union"] == 0:
        return None
    return Fraction(row["intersection"], row["union"])


def identity_holds(trials=4000, seed=7):
    """The derivation, checked on random configurations rather than asserted."""
    rng = random.Random(seed)
    for _ in range(trials):
        n = rng.randint(20, 200)
        k = rng.randint(1, n)
        m = rng.randint(0, 300)
        d = n - k
        if d + m == 0:
            continue
        low = max(0, 2 * k - n)
        w1, w2 = rng.randint(low, k), rng.randint(low, k)
        c1 = Fraction((n + m) * (n - 2 * k + w1 + m), (d + m) ** 2)
        c2 = Fraction((n + m) * (n - 2 * k + w2 + m), (d + m) ** 2)
        if ((c1 > c2) != (w1 > w2)) or ((c1 == c2) != (w1 == w2)):
            return False
        if 2 * k - w1 and 2 * k - w2:
            j1, j2 = Fraction(w1, 2 * k - w1), Fraction(w2, 2 * k - w2)
            if (j1 > j2) != (w1 > w2):
                return False
    return True


def parity(data=None):
    """Every pairwise comparison inside one view and one target, both measures."""
    data = data or load()
    agree = disagree = 0
    flips = []
    for first, second in itertools.combinations(data["rows"], 2):
        if (first["view"] != second["view"]
                or first["target_miss_rate"] != second["target_miss_rate"]):
            continue
        ca, cb = coefficient(first), coefficient(second)
        ja, jb = jaccard(first), jaccard(second)
        if None in (ca, cb, ja, jb):
            continue
        same = ((ca > cb) == (ja > jb)) and ((ca < cb) == (ja < jb))
        if same:
            agree += 1
        else:
            disagree += 1
            flips.append({"view": first["view"], "target": first["target_miss_rate"],
                          "pairs": [f"{first['first']}/{first['second']}",
                                    f"{second['first']}/{second['second']}"]})
    return {"comparisons": agree + disagree, "agree": agree, "disagree": disagree,
            "disagreements": flips}


def marginal_audit(data=None):
    """What miss fraction each row actually sits at, against its nominal label."""
    data = data or load()
    groups = {}
    for row in data["rows"]:
        key = (row["view"], row["target_miss_rate"])
        entry = groups.setdefault(key, {"view": row["view"], "nominal": row["target_miss_rate"],
                                        "fractions": set(), "populations": set()})
        entry["fractions"].add(row["actual_miss_fraction_first"])
        entry["fractions"].add(row["actual_miss_fraction_second"])
        entry["populations"].add(row["population"])
    out = []
    for key in sorted(groups):
        entry = groups[key]
        values = sorted(Fraction(f) for f in entry["fractions"])
        out.append({"view": entry["view"], "nominal_target": entry["nominal"],
                    "actual_miss_fraction": [str(values[0]), str(values[-1])],
                    "population": sorted(entry["populations"]),
                    "matches_its_label": abs(values[0] - Fraction(str(entry["nominal"]))) < Fraction(1, 100)})
    return out


def report(data=None):
    data = data or load()
    audit = marginal_audit(data)
    result = parity(data)
    return {
        "artifact_id": "reiyah.overlap-parity.report", "version": VERSION,
        "identity": {
            "statement": ("under an exactly matched universe, ordering by the coefficient equals "
                          "ordering by intersection size, for every common unseen count"),
            "form": "c(m) = (N+m)(N-2k+w+m)/(d+m)^2, so c_1-c_2 = (N+m)(w_1-w_2)/(d+m)^2",
            "derived_independently": True,
            "checked_on_random_configurations": identity_holds()},
        "empirical_parity": {
            **result,
            "verdict": ("ordinary Jaccard overlap reproduces the coefficient's ordering in every "
                        "comparison available in this lane's own counts")},
        "what_the_coefficient_earns_here": "nothing over ordinary overlap, for the ordering claim",
        "where_value_must_now_be_earned": [
            "faithful source preparation from raw detector submissions",
            "useful abstention where the evidence does not support a conclusion",
            "sensitivity to association error, bounded in theory here and never measured",
            "a cheaper review procedure, measured against an analyst given the same overlap",
            "a better integration choice under the additive detector loss"],
        "withdrawn": {
            "claim": ("the label free margin is wider than the annotated one, and therefore the "
                      "evidence is stronger"),
            "why": ("the two views were never at matched marginals. The label free rows sit at "
                    "actual miss fractions of 0.238, 0.299 and 0.363 against the annotated 0.300, "
                    "0.400 and 0.500, on smaller per pair populations. A wider margin across "
                    "different marginals and populations establishes nothing"),
            "found_by": "an Engine consumer review, not by this lane"},
        "marginal_audit": audit,
        "what_still_stands": (
            "the label free view reaches the same ordering as the annotated view at two of three "
            "operating points. That remains true, and the credit belongs to channel agreement, "
            "which ordinary overlap also captures, not to the coefficient"),
        "association_caveat_belongs_in_the_result_sentence": (
            "the retained caches contain only detections matched to annotated objects, so "
            "annotation based membership, correspondence and unmatched detection filtering remain "
            "in the inputs. This is a useful ablation conditional on that association, not an end "
            "to end annotation free measurement"),
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
