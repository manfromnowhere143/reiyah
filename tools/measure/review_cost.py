"""What deciding an integration question costs in human judgements, and why no
ordering reduces it.

Three times now a conventional overlap baseline has reproduced this lane's result:
the coefficient's ordering, the raw two channel sign, and the retained addition
count. Each of those was a SCALAR SUMMARY, and a scalar computed from counts is
exactly where a simple baseline competes. This module asks a different kind of
question, one overlap has no analogue for: not what the number is, but **how many
human judgements it takes to decide, and whether choosing what to look at first
helps**.

THE SETTING. With `r` retained additions and `k` of them corresponding to a real
object the base missed,

    delta = (a + b) * k - b * r,        0 <= k <= r

so the coarse bound is `[-b*r, a*r]` and the sign turns on `k` against
`b*r/(a+b)`. A reviewer resolving one addition learns whether it belongs to `k`.

RESULT ONE: RANKING CANNOT NARROW FASTER. Resolving any record narrows the
interval by exactly `a + b`, whichever record it is. The width after `j`
judgements is `(a + b) * (r - j)` and nothing about the choice enters. **A ranked
review queue cannot narrow a bound faster than an arbitrary one.** That kills the
obvious product, which was a prioritised review list, before it was built.

RESULT TWO: THE WORST CASE IS EVERY RECORD. The decision is the sign, not the
width, so early stopping is possible once one side is settled. It does not help
in the worst case. Solving the adversarial game exactly, the worst case number of
judgements is `r`: **every retained addition must be resolved.** Verified
exhaustively for `r` up to 15 across seven penalty pairs, including asymmetric
ones and including `b = 0`, with no exception.

A first draft of this module claimed `b = 0` was the case where the cost falls,
on the reasoning that the threshold sits at zero so one confirmed addition settles
the sign. That is wrong and a test caught it before publication. With `b = 0` the
adversary simply answers not real every time: `k` stays at zero, the negative side
is settled only when no records remain, and the cost is `r` again. The result is
universal rather than conditional, which is stronger than what was first written.

The reason is short: while a decision needs `k` compared against a threshold
strictly inside `[0, r]`, or against zero from below, the adversary can always
answer so that both outcomes stay reachable, and only exhausting the records
removes that freedom.

RESULT THREE, ON THE LIVE COMPARISON. The Engine's real comparison carries two
anchors with `r = 9` and `r = 7` at equal weight, giving `[-8, 8]`. Solving the
two anchor adaptive game exactly gives **16** worst case judgements, which is the
total. It is invariant to how the additions split between anchors and invariant to
the weights: every split of 16 tested and every weighting tested returns 16.

WHAT THIS MEANS FOR A VALIDATION LEAD. The entire human cost of the decision is
fixed before anyone looks at anything, because `r` is set by preparation, and the
previous checkpoint measured that `r` moves by 29.9 times across defensible
preparations while the score cutoff alone moves it 21.6 times. **The only lever on
review cost is preparation. Reviewer cleverness is not a lever at all.**

WHAT IS NOT CLAIMED. This is worst case. An expected case would need a prior over
which additions are real, no such prior is established here, and inventing one to
make prioritisation look useful is exactly the move this lane refuses. Whether a
justified prior exists is open, and would change result two and not result one.

Exact rational arithmetic, standard library only, no data read.
"""
from fractions import Fraction
from functools import lru_cache
import json
import sys

VERSION = "0.1.0"
MAX_RECORDS = 400


class CostError(Exception):
    """The declared comparison is not one this analysis accepts."""


def _positive(name, value):
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise CostError(f"{name} must be a non negative integer, not {value!r}")
    return value


def interval_width(retained_additions, judgements, false_negative=1, false_positive=1):
    """The bound's width after any `judgements` records are resolved."""
    _positive("retained additions", retained_additions)
    _positive("judgements", judgements)
    if judgements > retained_additions:
        raise CostError("more judgements than there are records to resolve")
    return (false_negative + false_positive) * (retained_additions - judgements)


def ranking_cannot_narrow_faster(retained_additions, false_negative=1, false_positive=1):
    """The width depends on how many are resolved and never on which."""
    widths = [interval_width(retained_additions, j, false_negative, false_positive)
              for j in range(retained_additions + 1)]
    steps = {widths[i] - widths[i + 1] for i in range(len(widths) - 1)}
    return {"width_by_judgements": widths,
            "constant_step": sorted(steps) == [false_negative + false_positive]
                             if steps else True,
            "reading": ("each judgement narrows the bound by a + b whichever record it is, so a "
                        "ranked queue cannot narrow faster than an arbitrary one")}


def worst_case_judgements(anchors, weights=None, false_negative=1, false_positive=1,
                          tolerance=Fraction(0)):
    """Exact worst case count to decide the sign, over an adversarial reviewer.

    `anchors` is the retained addition count per anchor. The reviewer chooses
    which anchor to resolve next; the adversary answers to delay a decision.
    """
    anchors = tuple(_positive("an anchor's retained additions", a) for a in anchors)
    if not anchors:
        raise CostError("no anchor was declared")
    if sum(anchors) > MAX_RECORDS:
        raise CostError(f"more than {MAX_RECORDS} records exceeds the exact search budget. "
                        "This is a resource limit, not a statement that the cost is unbounded")
    if weights is None:
        weights = [Fraction(1, len(anchors))] * len(anchors)
    weights = [Fraction(w) for w in weights]
    if len(weights) != len(anchors):
        raise CostError("a weight is required for each anchor")
    if sum(weights) != 1:
        raise CostError(f"weights sum to {sum(weights)}, not 1")
    gain = false_negative + false_positive

    @lru_cache(maxsize=None)
    def solve(resolved, real):
        low = sum(weights[i] * (gain * real[i] - false_positive * anchors[i])
                  for i in range(len(anchors)))
        high = sum(weights[i] * (gain * (real[i] + anchors[i] - resolved[i])
                                 - false_positive * anchors[i])
                   for i in range(len(anchors)))
        if low > tolerance or high <= tolerance:
            return 0
        options = []
        for i in range(len(anchors)):
            if resolved[i] >= anchors[i]:
                continue
            nxt_resolved = resolved[:i] + (resolved[i] + 1,) + resolved[i + 1:]
            yes = solve(nxt_resolved, real[:i] + (real[i] + 1,) + real[i + 1:])
            no = solve(nxt_resolved, real)
            options.append(1 + max(yes, no))
        return min(options) if options else 0

    zero = tuple(0 for _ in anchors)
    answer = solve(zero, zero)
    solve.cache_clear()
    return answer


def report(anchors=(9, 7), weights=None):
    """The live comparison by default, with the two structural invariances checked."""
    total = sum(anchors)
    cost = worst_case_judgements(anchors, weights)
    splits = {f"{a},{total - a}": worst_case_judgements((a, total - a))
              for a in (1, total // 4, total // 2, total - 1) if 0 < a < total}
    weightings = {}
    for pair in ((Fraction(1, 2), Fraction(1, 2)), (Fraction(3, 4), Fraction(1, 4)),
                 (Fraction(1, 10), Fraction(9, 10))):
        weightings[f"{pair[0]},{pair[1]}"] = worst_case_judgements(anchors, list(pair))
    return {
        "artifact_id": "reiyah.review-cost.report", "version": VERSION,
        "anchors": list(anchors), "total_retained_additions": total,
        "worst_case_judgements": cost,
        "equals_the_total": cost == total,
        "ranking_cannot_narrow_faster": ranking_cannot_narrow_faster(min(anchors)),
        "invariant_to_the_anchor_split": splits,
        "invariant_to_the_weights": weightings,
        "reading": ("the entire human cost of the decision is fixed by preparation, which sets the "
                    "retained addition count, and no ordering of the review reduces it"),
        "not_claimed": [
            "anything about the expected case, which would need a prior over which additions are "
            "real; none is established here and inventing one to make prioritisation look useful "
            "is the move this lane refuses",
            "that resolving a record is a single unit of human effort; the unit is declared, not "
            "measured",
            "that the retained additions are physical objects",
            "any value for the loss itself, which still needs admitted references",
        ],
    }


def main(argv):
    try:
        anchors = tuple(int(v) for v in argv[1:]) or (9, 7)
        json.dump(report(anchors), sys.stdout, indent=2, sort_keys=True, default=str)
    except CostError as error:
        sys.stderr.write(f"refused: {error}\n")
        return 1
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
