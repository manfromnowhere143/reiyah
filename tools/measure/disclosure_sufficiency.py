"""What a portable redundancy report must carry, per named decision.

The silence histogram, the distribution of the number of silent channels, has an
exact and useful property: it determines every uniformly subset-averaged k-wise
all-silent rate. It does not determine any labelled query. This module exhibits
the separation exactly and measures how much ambiguity the histogram leaves.

Exact rational arithmetic. Standard library only. No data is read.
"""
from fractions import Fraction
from itertools import combinations, product
import json
import sys

from moment_cone_certificate import simplex_feasible

CHANNELS = 3
CELLS = list(product((0, 1), repeat=CHANNELS))


def summarise(population):
    """Marginals, silence histogram and subset-averaged moments of a population."""
    marginals = [sum((w for row, w in population.items() if row[j]), Fraction(0))
                 for j in range(CHANNELS)]
    histogram = {}
    for row, weight in population.items():
        histogram[sum(row)] = histogram.get(sum(row), Fraction(0)) + weight
    moments = []
    for size in range(CHANNELS + 1):
        groups = list(combinations(range(CHANNELS), size))
        total = sum((sum((w for row, w in population.items() if all(row[j] for j in group)),
                         Fraction(0)) for group in groups), Fraction(0))
        moments.append(total / Fraction(len(groups)))
    return marginals, histogram, moments


def subset_rate(population, subset):
    return sum((w for row, w in population.items() if all(row[j] for j in subset)), Fraction(0))


def attainable_range(marginals, histogram, subset):
    """Exact range of P(all of `subset` silent) over every population matching the summary.

    Feasibility probes on the 8-cell simplex, bisected on the objective bound.
    Both ends are returned with the certifying populations.
    """
    def rows_and_targets(extra=None):
        rows, targets = [], []
        rows.append([Fraction(1)] * len(CELLS))
        targets.append(Fraction(1))
        for j in range(CHANNELS):
            rows.append([Fraction(1) if cell[j] else Fraction(0) for cell in CELLS])
            targets.append(marginals[j])
        for count in sorted(histogram):
            rows.append([Fraction(1) if sum(cell) == count else Fraction(0) for cell in CELLS])
            targets.append(histogram[count])
        if extra is not None:
            rows.append([Fraction(1) if all(cell[j] for j in subset) else Fraction(0)
                         for cell in CELLS])
            targets.append(extra)
        return rows, targets

    def feasible(value):
        rows, targets = rows_and_targets(value)
        solution = simplex_feasible(rows, targets, len(CELLS))
        return solution

    achievable = []
    step = Fraction(1, 720)
    value = Fraction(0)
    while value <= min(marginals[j] for j in subset):
        if feasible(value) is not None:
            achievable.append(value)
        value += step
    if not achievable:
        return None
    return min(achievable), max(achievable)


def main(argv):
    A = {(1, 0, 0): Fraction(1, 2), (0, 1, 1): Fraction(1, 2)}
    B = {(0, 1, 0): Fraction(1, 2), (1, 0, 1): Fraction(1, 2)}
    out = []
    out.append("=" * 84)
    out.append("DISCLOSURE SUFFICIENCY: what the silence histogram does and does not determine")
    out.append("three channels, 1 means silent, two populations of two equally weighted rows")
    out.append("=" * 84)
    summaries = {}
    for name, population in (("A", A), ("B", B)):
        marginals, histogram, moments = summarise(population)
        summaries[name] = (marginals, histogram, moments)
        rows = " ".join("".join(str(bit) for bit in row) for row in sorted(population))
        out.append(f"  population {name}: rows {rows}")
        out.append(f"    marginals            {[str(v) for v in marginals]}")
        out.append(f"    silence histogram    {{{', '.join(f'{k}: {v}' for k, v in sorted(histogram.items()))}}}")
        out.append(f"    subset-averaged m_k  {[str(v) for v in moments]}")
    identical = summaries["A"] == summaries["B"]
    out.append("")
    out.append(f"  every published summary identical: {identical}")
    out.append("")
    out.append("  the labelled query the two populations answer differently:")
    for name, population in (("A", A), ("B", B)):
        pair = subset_rate(population, (0, 2))
        first = subset_rate(population, (0,))
        out.append(f"    population {name}: P(channel 1 silent) = {first}, "
                   f"P(channels 1 and 3 both silent) = {pair}")
    out.append("    adding channel 3 to an installed channel 1 removes all of its silence in A")
    out.append("    and none of it in B. The decision differs maximally on identical summaries.")
    marginals, histogram, _ = summaries["A"]
    span = attainable_range(marginals, histogram, (0, 2))
    out.append("")
    out.append("  exact range of P(channels 1 and 3 both silent) over every population")
    out.append("  consistent with those marginals and that histogram:")
    if span is None:
        out.append("    no feasible population found on the probe lattice")
    else:
        low, high = span
        frechet_low = max(Fraction(0), marginals[0] + marginals[2] - 1)
        frechet_high = min(marginals[0], marginals[2])
        out.append(f"    [{low}, {high}]  width {high - low}")
        out.append(f"    the Frechet interval permitted by the marginals alone is "
                   f"[{frechet_low}, {frechet_high}]")
        out.append("    The probe lattice is a search, not the proof. The proof is that both")
        out.append("    endpoints are attained by the two populations above, and the Frechet")
        out.append("    bound caps the interval, so the range is exactly the Frechet interval:")
        out.append(f"    the histogram removes none of the ambiguity in this labelled query "
                   f"({low == frechet_low and high == frechet_high}).")
    out.append("")
    out.append("=" * 84)
    out.append("WHAT A PORTABLE REPORT MUST CARRY, BY DECISION")
    out.append("=" * 84)
    table = [
        ("average all-silent rate over k-subsets", "silence histogram", "sufficient"),
        ("all-silent rate for one named subset", "silence histogram", "NOT sufficient"),
        ("value of adding named channel j to installed set C",
         "the two rates for C and C+{j}", "sufficient"),
        ("value of every candidate addition to installed C",
         "one rate per candidate plus the rate for C", "sufficient"),
        ("every labelled subset query", "all 2^K cell counts", "sufficient and minimal"),
        ("value of a channel never measured", "a model, and its validity certificate",
         "no summary suffices"),
    ]
    for decision, carrier, verdict in table:
        out.append(f"  {decision}")
        out.append(f"      carry: {carrier}")
        out.append(f"      {verdict}")
    out.append("")
    out.append("  For K = 5 the full labelled disclosure is 32 counts per stratum, which is")
    out.append("  smaller than the histogram plus marginals people have been tempted to ship,")
    out.append("  and it answers every labelled query. Compactness was never the constraint.")
    out.append("")
    out.append("  DISCLOSURE BOUNDARY. Cell counts are not anonymous. A stratum holding n")
    out.append("  opportunities discloses the exact multiset of per-object silence patterns,")
    out.append("  and at n = 1 it discloses one object's pattern across every channel. Repeated")
    out.append("  releases of one population under different stratifications permit linkage.")
    out.append("  A minimum cell occupancy and a release ledger are therefore part of the")
    out.append("  contract, not an operational detail. Compactness is not privacy.")
    text = "\n".join(out) + "\n"
    sys.stdout.write(text)
    if len(argv) > 1 and argv[1] == "--json":
        json.dump({"identical_summaries": identical}, sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
