"""Adversarial audit of the Result H accuracy claim.

Two documents state, as a measured finding:

  docs/GATE_B_SESSION_HANDOFF.md:64
    "joint-failure odds rise with the accuracy of both models: 7.01, 15.86, 31.99"
  docs/GATE_B_MEASUREMENT_CONTRACT.md:60
    "Joint-failure odds rise with the accuracy of both models."

The contract row is labelled `measured`. This audit asks what computation produced it.

The answer is that none did. tools/measure/result_h.py defines

    MAP = {"mapillary": 29.8, "megvii": 51.9, "pointpillars": 29.5, "centerpoint": 61.6}

and never references it again. No script in tools/measure/ regresses, ranks, correlates
or tests an odds ratio against accuracy. The three numbers are the three same-modality
Mantel-Haenszel odds ratios in evidence/measurement/result_h.txt, read in ascending
order. Sorting three numbers and narrating the sort is not a measurement.

This audit runs the tests the claim would need, on the published numbers alone, so it
is reproducible from committed evidence without the CenterPoint and PointPillars
match files.

Usage:
  python3 tools/measure/audit_result_h_accuracy_claim.py
"""

from itertools import permutations

# Exactly as published in evidence/measurement/result_h.txt.
PAIRS = [
    # name_a, name_b, marginal_c, conditional_c, conditional_mh_or
    ("centerpoint", "megvii", 2.698, 1.725, 31.988),
    ("centerpoint", "pointpillars", 1.966, 1.386, 15.863),
    ("megvii", "pointpillars", 1.712, 1.313, 7.010),
]

# Exactly as hardcoded in tools/measure/result_h.py, where it is never used.
MAP = {"mapillary": 29.8, "megvii": 51.9, "pointpillars": 29.5, "centerpoint": 61.6}

# Provenance of each accuracy figure, from docs/GATE_B_SESSION_HANDOFF.md section 4
# and docs/GATE_B_MEASUREMENT_CONTRACT.md section 4.
VALIDATED = {"mapillary": True, "megvii": True, "pointpillars": True,
             "centerpoint": False}


def monotone(seq):
    return all(x < y for x, y in zip(seq, seq[1:]))


def main():
    print("=" * 88)
    print("AUDIT OF THE RESULT H ACCURACY CLAIM")
    print('"joint-failure odds rise with the accuracy of both models: 7.01, 15.86, 31.99"')
    print("=" * 88)

    print("\n### 1. provenance of the claim")
    print("  stated in : docs/GATE_B_SESSION_HANDOFF.md, docs/GATE_B_MEASUREMENT_CONTRACT.md")
    print("  labelled  : 'measured' in the contract results table")
    print("  computed  : nowhere. result_h.py binds MAP and never reads it.")
    print("  status    : a prose ordering of three published numbers")

    print("\n### 2. does 'accuracy of both models' even order the pairs?")
    print(f"  {'pair':<30}{'min mAP':>9}{'sum mAP':>9}{'cond c':>9}{'MH OR':>10}")
    for a, b, mc, cc, orr in PAIRS:
        print(f"  {a + ' x ' + b:<30}{min(MAP[a], MAP[b]):>9.1f}"
              f"{MAP[a] + MAP[b]:>9.1f}{cc:>9.3f}{orr:>10.3f}")

    tied = [(a, b, orr) for a, b, _mc, _cc, orr in PAIRS
            if min(MAP[a], MAP[b]) == 29.5]
    print("\n  Two pairs share an identical weaker-model accuracy of 29.5 mAP:")
    for a, b, orr in tied:
        print(f"    {a} x {b:<16} MH OR = {orr:.3f}")
    if len(tied) == 2:
        ratio = max(t[2] for t in tied) / min(t[2] for t in tied)
        print(f"  Their odds ratios differ by {ratio:.2f}x at the same weaker-model")
        print("  accuracy. 'The accuracy of both models' therefore does not order")
        print("  these data unless 'both' silently means the sum, which is a")
        print("  different and unstated claim.")

    print("\n### 3. evidential weight of a monotone trend on three points")
    orders = list(permutations(range(3)))
    mono_up = sum(1 for p in orders if monotone([PAIRS[i][4] for i in p]))
    mono_any = sum(1 for p in orders
                   if monotone([PAIRS[i][4] for i in p])
                   or monotone([PAIRS[i][4] for i in p][::-1]))
    print(f"  permutations of three distinct values      : {len(orders)}")
    print(f"  that are monotone increasing               : {mono_up}"
          f"   p = {mono_up/len(orders):.3f}")
    print(f"  that are monotone in either direction      : {mono_any}"
          f"   p = {mono_any/len(orders):.3f}")
    print("  Under a random assignment of the three odds ratios to the three")
    print("  accuracy ranks, a perfect monotone trend arises one time in six.")
    print("  No conventional threshold is met. There is no test statistic to")
    print("  report because there is no test.")

    print("\n### 4. the three points are not three independent observations")
    detectors = sorted({d for a, b, *_ in PAIRS for d in (a, b)})
    print(f"  detectors involved: {', '.join(detectors)}")
    for d in detectors:
        appears = sum(1 for a, b, *_ in PAIRS if d in (a, b))
        print(f"    {d:<14} appears in {appears} of the 3 pairs")
    print("  Every detector appears in two pairs, so the three odds ratios share")
    print("  detectors pairwise. They cannot be treated as independent draws.")

    print("\n### 5. one accuracy figure is not validated")
    for d in sorted(MAP):
        if any(d in (a, b) for a, b, *_ in PAIRS):
            n = sum(1 for a, b, *_ in PAIRS if d in (a, b))
            mark = "validated" if VALIDATED[d] else "NOT VALIDATED"
            print(f"    {d:<14} {MAP[d]:>5.1f} mAP   {mark:<14} in {n} of 3 pairs")
    unval = [d for d in MAP if not VALIDATED[d]
             and any(d in (a, b) for a, b, *_ in PAIRS)]
    n_unval = sum(1 for a, b, *_ in PAIRS if any(d in (a, b) for d in unval))
    print(f"  {n_unval} of the 3 points depend on an accuracy figure the workstream")
    print("  itself records as reconstructed and unconfirmed, from a source it")
    print("  marks 'explicitly weaker provenance'.")

    print("\n### 6. the headline switches to the more dramatic metric")
    print("  Result G states that the lift c, not the odds ratio, 'is the number")
    print("  that belongs against Corollary 3'. The same three pairs in that metric:")
    for a, b, _mc, cc, orr in PAIRS:
        print(f"    {a + ' x ' + b:<30}  c = {cc:.3f}   MH OR = {orr:.3f}")
    spread_c = max(p[3] for p in PAIRS) / min(p[3] for p in PAIRS)
    spread_or = max(p[4] for p in PAIRS) / min(p[4] for p in PAIRS)
    print(f"  spread in c      : {spread_c:.2f}x")
    print(f"  spread in MH OR  : {spread_or:.2f}x")
    print("  The quoted figures are the metric with the widest spread, while the")
    print("  workstream's own analysis names the other one as operative.")

    print("\n" + "-" * 88)
    print("Finding. The claim 'joint-failure odds rise with the accuracy of both")
    print("models' is not supported and must not carry the label 'measured'.")
    print("")
    print("It is an ordering of three non-independent odds ratios, two of which")
    print("depend on an unvalidated accuracy figure, expressed in a metric the")
    print("workstream's own analysis does not treat as operative, with a")
    print("permutation p of 0.167 for the trend and no interval on any point.")
    print("Two pairs at identical weaker-model accuracy differ by 2.26x, so the")
    print("stated covariate does not even order the observations.")
    print("")
    print("This does not touch Result H's supported finding. Same-modality and")
    print("cross-modality pairs do separate on these six measurements, and that")
    print("separation is what the script computes. The accuracy sentence is a")
    print("separate assertion that no computation produced.")
    print("")
    print("Required action: withdraw the accuracy sentence from the contract")
    print("results table and the handoff, or demote it to a proposed question")
    print("with the design that would answer it, namely more detectors, validated")
    print("accuracy for every one, a pre-declared metric, and intervals that")
    print("respect both the pair-sharing and the instance clustering.")
    print("-" * 88)


if __name__ == "__main__":
    main()
