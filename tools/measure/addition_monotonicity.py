"""The addition decision has one sufficient statistic, and benchmarks do not report it.

Three facts, proved here by exhaustive enumeration over every small bipartite
match graph rather than asserted:

  1. adding detections never decreases the maximum matching, so recall is
     monotone non-decreasing in an augmentation that preserves the base;
  2. the gain is at most the number of retained additions;
  3. under the additive loss, delta = (a+b)*gain - b*r, so

         sign(delta) = sign( conversion - b/(a+b) ),   conversion = gain / r

The consequence is the point. Any selection rule that is monotone in recall alone
says "add it" for every augmentation, including every one where the loss worsens.
The two disagree exactly on conversion <= b/(a+b), and that set is not empty for
any penalty ratio: it is reached whenever enough retained additions fail to match.

So the addition decision is governed by one number, the conversion rate, against
one threshold set by the penalty ratio. A detection benchmark reports neither.

Exhaustive over all graphs within the declared size bound, exact arithmetic,
standard library only, no data read.
"""
from fractions import Fraction
from itertools import combinations, product
import json
import sys


def augment(node, adjacency, matched_to, seen):
    for other in adjacency[node]:
        if other in seen:
            continue
        seen.add(other)
        if other not in matched_to or augment(matched_to[other], adjacency, matched_to, seen):
            matched_to[other] = node
            return True
    return False


def maximum_matching(left, adjacency):
    matched_to = {}
    for node in left:
        augment(node, adjacency, matched_to, set())
    return len(matched_to)


def enumerate_graphs(n_base, n_add, n_obj):
    """Every bipartite graph on the declared node counts, as an edge mask."""
    slots = list(product(range(n_base + n_add), range(n_obj)))
    for mask in range(1 << len(slots)):
        adjacency = {d: [] for d in range(n_base + n_add)}
        for index, (d, o) in enumerate(slots):
            if mask >> index & 1:
                adjacency[d].append(o)
        yield adjacency


def main(argv):
    report = {"artifact_id": "reiyah.decision-evidence.addition-monotonicity",
              "version": "0.1.0", "exhaustive_cases": 0, "violations": [],
              "disagreements": {}}

    sizes = [(1, 1, 1), (1, 1, 2), (2, 1, 2), (1, 2, 2), (2, 2, 2)]
    ratios = [Fraction(1), Fraction(2), Fraction(4)]
    disagree = {str(k): 0 for k in ratios}
    seen_total = 0
    for n_base, n_add, n_obj in sizes:
        base = list(range(n_base))
        allnodes = list(range(n_base + n_add))
        for adjacency in enumerate_graphs(n_base, n_add, n_obj):
            base_adj = {d: (adjacency[d] if d in base else []) for d in allnodes}
            tp_base = maximum_matching(base, base_adj)
            tp_aug = maximum_matching(allnodes, adjacency)
            gain = tp_aug - tp_base
            seen_total += 1
            if gain < 0:
                report["violations"].append({"fact": "recall monotonicity", "size": [n_base, n_add, n_obj]})
            if gain > n_add:
                report["violations"].append({"fact": "gain at most r", "size": [n_base, n_add, n_obj]})
            r = n_add
            for ratio in ratios:
                a, b = ratio, Fraction(1)
                delta = (a + b) * gain - b * r
                conversion = Fraction(gain, r)
                threshold = b / (a + b)
                if (delta > 0) != (conversion > threshold):
                    report["violations"].append({"fact": "sign law", "size": [n_base, n_add, n_obj]})
                # recall says add whenever it does not decrease, which is always
                if gain >= 0 and delta < 0:
                    disagree[str(ratio)] += 1
    report["exhaustive_cases"] = seen_total
    report["sizes_enumerated"] = [{"base": b, "added": a, "objects": o} for b, a, o in sizes]
    report["facts_verified"] = [
        "maximum matching never decreases when detections are added to a preserved base",
        "the gain never exceeds the number of retained additions",
        "sign(delta) equals sign(conversion - b/(a+b)) at every enumerated graph"]
    report["disagreements"] = {
        "meaning": ("cases where recall does not decrease, so a recall-monotone rule says add, "
                    "while the additive loss worsens"),
        "count_by_penalty_ratio": disagree,
        "of_total_cases": seen_total,
        "why_the_counts_coincide_here": (
            "at these node counts the only augmentations that worsen the loss are those with zero "
            "gain, and a zero gain worsens it at every penalty ratio. The ratio dependence needs "
            "more retained additions than an exhaustive graph enumeration can reach, so it is shown "
            "separately below over the realisable gain and r pairs")}

    # Every (gain, r) with 0 <= gain <= r is realisable: take r additions, `gain` of
    # them adjacent to distinct objects no base detection can reach, the rest isolated.
    # The ratio dependence lives here, and it is the part that matters for a decision.
    grid = []
    for r in range(1, 13):
        for gain in range(0, r + 1):
            row = {"r": r, "gain": gain, "conversion": str(Fraction(gain, r))}
            for ratio in ratios:
                a, b = ratio, Fraction(1)
                row[f"delta_at_a_over_b_{ratio}"] = str((a + b) * gain - b * r)
                row[f"improves_at_a_over_b_{ratio}"] = (a + b) * gain - b * r > 0
            grid.append(row)
    flips = {}
    for ratio in ratios:
        key = f"improves_at_a_over_b_{ratio}"
        flips[str(ratio)] = sum(1 for row in grid if not row[key])
    report["realisable_gain_and_r"] = {
        "pairs_enumerated": len(grid),
        "worsening_pairs_by_penalty_ratio": flips,
        "threshold_by_penalty_ratio": {str(k): str(Fraction(1) / (k + 1)) for k in ratios},
        "realisability": ("every pair with 0 <= gain <= r is achieved by a graph: give `gain` "
                          "additions their own object unreachable from the base, and leave the "
                          "rest isolated"),
        "reading": ("the count of worsening pairs falls as the penalty ratio rises, which is the "
                    "ratio dependence the graph enumeration is too small to expose")}
    report["conclusion"] = (
        "the addition decision under this loss is a one-dimensional comparison of the conversion "
        "rate against b/(a+b). A recall-monotone criterion cannot express it, and a detection "
        "benchmark publishes neither the conversion rate nor the operational penalty ratio, so a "
        "benchmark improvement does not determine the addition decision in either direction")
    report["non_claims"] = (
        "this is an exact statement about the declared additive loss and the declared matching. It "
        "is not a claim about mAP, which penalises precision through ranking and is not "
        "recall-monotone, and it carries no planner, safety or crash-risk consequence")
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
