"""Which sign survives when the observed capture table itself may be wrong.

The identification result assumes the observed counts are counts of real, unique,
eligible objects with correct cross channel identities. Raw detector output does
not establish that. A false detection, a duplicate, a wrong association or an
eligibility exclusion changes the supposedly observed cells, and the sign
conclusion is a statement about the corrected table, not the raw one.

In the elementary notation, with `w` captured by both channels, `x` by the first
only, `y` by the second only, `u` pair misses seen by an additional source, and
`m` the objects no source saw at all,

    c > 1   if and only if   w * (u + m) > x * y

which is the same condition as `m * w > a * b - u * S`, asserted as a test. No
statistical independence assumption about the additional source appears in it.
That is worth saying precisely, because it is easy to overclaim: the condition
needs the counts to be VALID, which is an observation obligation, and validity is
a different thing from statistical independence and from procedural independence
of review. This module is about the first of the three and says nothing about the
other two.

Since `w >= 0`, the condition is hardest at `m = 0`, so a table settles the sign
for every unseen count exactly when `w * u > x * y`.

THE UNCERTAINTY MODEL. A declared, bounded budget says how many objects in each
observed cell may be wrong, and in which direction. Every allowance is an integer
count of objects, declared by whoever is willing to defend it. Nothing here
invents an error budget, a sampling frame, a probability or a human judgment; the
budget is an input and the module refuses to run without one.

Corrections move objects between cells or remove them, so the counts are NOT
perturbed independently. An object wrongly placed in `u` because the first
channel did detect it leaves `u` and arrives in `x`, which pushes the condition
the wrong way twice. That dependence is the point, and a model that jittered each
count on its own would miss it.

WHAT IS COMPUTED. Every admissible corrected table is enumerated directly, and
the sign is reported as surviving only if it holds for all of them. The adverse
completion that comes closest to breaking it is retained as a certificate, so the
answer can be checked by evaluating one table rather than by trusting this search.
When the budget is too large to enumerate under the declared cap, the result is
`unresolved`: a resource limit is not an impossibility result and is never
reported as one.

Exact integer arithmetic, standard library only, no data read, no probability.
"""
from fractions import Fraction
from itertools import product
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import joint_miss_identification as identification  # noqa: E402

VERSION = "0.3.0"
MAX_TABLES = 4_000_000

# Each allowance names objects leaving one cell for another, or leaving entirely.
MOVES = (("u", "x"), ("u", "y"), ("w", "x"), ("w", "y"),
         ("x", "w"), ("y", "w"), ("x", "u"), ("y", "u"),
         ("w", None), ("x", None), ("y", None), ("u", None))

# For the SIGN claim an adversary only ever moves objects out of the two cells
# that support it, because the other six corrections strictly raise the margin.
# That is a verified optimisation, not an assumption: the default search uses all
# twelve moves, and a test asserts the restricted search returns the same
# breakdown number. The restriction is NOT valid for a declared constant claim,
# where the adversary wants to raise the coefficient rather than lower a margin,
# so it is never applied there.
ADVERSE_FOR_THE_SIGN = (("u", "x"), ("u", "y"), ("w", "x"), ("w", "y"),
                        ("u", None), ("w", None))
MAX_BREAKDOWN_ALLOCATIONS = 5_000_000


class BudgetError(Exception):
    """The declared table or budget is not one this analysis applies to."""


def _count(name, value):
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise BudgetError(f"{name} must be a non negative integer, not {value!r}")
    return value


def move_name(source, target):
    return f"{source}_to_{target}" if target else f"{source}_removed"


def settles_the_sign(table):
    """Does this table settle c > 1 for every unseen count? Hardest at m = 0."""
    return table["w"] * table["u"] > table["x"] * table["y"]


def smallest_sufficient_u(w, x, y):
    """The least `u` that settles the sign, holding the other three counts fixed."""
    _count("w", w), _count("x", x), _count("y", y)
    if w == 0:
        return None
    return x * y // w + 1


def single_allowance_tolerance(observed, source, target):
    """The largest allowance of one correction kind that still settles the sign.

    Reported per kind because the kinds are not equally damaging. Moving an object
    out of the pair miss cell and into a single capture cell hurts the condition on
    both sides at once, while removing it as ineligible hurts only one. The
    difference tells an observation programme which verification is worth doing.
    """
    for cell in "wxyu":
        _count(cell, observed[cell])
    allowance = 0
    limit = observed[source]
    while allowance <= limit:
        table = dict(observed)
        table[source] -= allowance
        if target:
            table[target] += allowance
        if not settles_the_sign(table):
            return {"largest_allowance_that_survives": allowance - 1 if allowance else None,
                    "breaks_at": allowance,
                    "of_how_many_observed": observed[source]}
        allowance += 1
    return {"largest_allowance_that_survives": limit, "breaks_at": None,
            "of_how_many_observed": observed[source],
            "note": "the whole cell may be wrong and the sign still holds"}


def admissible_tables(observed, budget):
    """Every corrected table the declared budget allows, with its applied moves."""
    ranges = []
    for source, target in MOVES:
        allowance = budget.get(move_name(source, target), 0)
        _count(move_name(source, target), allowance)
        ranges.append(range(allowance + 1))
    total = 1
    for span in ranges:
        total *= len(span)
        if total > MAX_TABLES:
            raise BudgetError(
                f"the declared budget allows more than {MAX_TABLES} corrected tables. This is a "
                "resource limit on this search, not a statement that the sign is undecidable")
    for choice in product(*ranges):
        leaving = {cell: 0 for cell in "wxyu"}
        table = {cell: observed[cell] for cell in "wxyu"}
        applied = {}
        for (source, target), amount in zip(MOVES, choice):
            if not amount:
                continue
            leaving[source] += amount
            table[source] -= amount
            if target:
                table[target] += amount
            applied[move_name(source, target)] = amount
        if any(leaving[cell] > observed[cell] for cell in "wxyu"):
            continue          # cannot move out more objects than the cell holds
        if any(value < 0 for value in table.values()):
            continue
        yield table, applied


def supremum_over_unseen(table):
    """The smallest constant c admissible for this table, over every unseen count."""
    counts = {}
    if table["w"]:
        counts[(1, 1, 0)] = table["w"]
    if table["x"]:
        counts[(1, 0, 0)] = table["x"]
    if table["y"]:
        counts[(0, 1, 0)] = table["y"]
    if table["u"]:
        counts[(0, 0, 1)] = table["u"]
    if not counts:
        return None
    parts = identification.margins(counts)
    span = identification.range_over(parts, 0, None)
    if span.get("state") != "computed":
        return None
    return Fraction(span["supremum"])


def _holds(table, constant):
    """The claim under attack: the sign, or a declared Definition 32 constant."""
    if constant is None:
        return table["w"] * table["u"] > table["x"] * table["y"]
    reached = supremum_over_unseen(table)
    return reached is not None and reached <= constant


def _allocations(total, slots):
    """Every way to split `total` objects across `slots` correction kinds."""
    if slots == 1:
        yield (total,)
        return
    for first in range(total + 1):
        for rest in _allocations(total - first, slots - 1):
            yield (first,) + rest


def _apply(observed, allocation, moves):
    table = dict(observed)
    for (source, target), amount in zip(moves, allocation):
        if not amount:
            continue
        table[source] -= amount
        if target:
            table[target] += amount
    return table


def margin_lower_bound(observed, k):
    """A proved lower bound on the sign margin after at most k elementary moves.

    Derived from the move model alone, in three steps.

    One. `w' >= w - j` where `j` objects leave `w`, and `u' >= u - i` where `i`
    leave `u`. Objects arriving only raise them, so the bounds hold whatever else
    the adversary does.

    Two. With `i + j <= k`, the product is at least `(w-j)(u-i)`, and using fewer
    than `k` moves only raises it, so the minimum sits on `i + j = k`. As a
    function of `j` that is `(w-j)(u-k+j)`, a downward parabola, so it is
    minimised at an endpoint: `j = 0` gives `w(u-k)`, and `j = k` gives `(w-k)u`.
    **Both endpoints must be taken**, because which is smaller depends on whether
    `u` exceeds `w`. A bound quoting only `w(u-k)` is unsound whenever `u > w`;
    that form was checked against exhaustive search on 732 table and k pairs and
    failed 285 of them, while the two endpoint form failed none.

    Three. Each elementary move raises `x' + y'` by at most one, so
    `x' + y' <= x + y + k`, and for non negative integers with a fixed sum the
    product is largest when they are as equal as possible, giving
    `x'y' <= floor((x+y+k)^2 / 4)`.

    Together: `margin >= min(w(u-k), (w-k)u) - floor((x+y+k)^2/4)`, with the
    factors clamped at zero. It is a bound, not the worst case: it was tight on
    354 of those 732 pairs and loose by at most 42 on the rest.
    """
    for cell in "wxyu":
        _count(cell, observed[cell])
    _count("k", k)
    w, x, y, u = (observed[cell] for cell in "wxyu")
    product = min(w * max(0, u - k), max(0, w - k) * u)
    return product - ((x + y + k) ** 2) // 4


def certified_breakdown(observed, moves=None):
    """The breakdown number for the sign, proved rather than enumerated below it.

    The bound rules out every level it can in constant arithmetic, and the search
    then runs only from the first level the bound cannot rule out. On the retained
    table that is a proof for k <= 11 and a search at k = 12 alone, instead of
    enumerating every level from one.

    The two obligations are different and are reported separately. A breaking
    table is a complete disproof on its own. A proved bound is what rules out the
    cheaper attacks; evaluating one surviving table never does that.
    """
    proved_safe = 0
    available = sum(observed[cell] for cell in "wxyu")
    while proved_safe < available and margin_lower_bound(observed, proved_safe + 1) > 0:
        proved_safe += 1
    found = breakdown(observed, moves=moves, ceiling=available)
    result = {
        "artifact_id": "reiyah.table-robustness.certified-breakdown", "version": VERSION,
        "levels_proved_safe_by_bound": proved_safe,
        "bound_at_the_last_proved_level": margin_lower_bound(observed, proved_safe),
        "bound_at_the_first_unproved_level": margin_lower_bound(observed, proved_safe + 1)
                                             if proved_safe < available else None,
        "search_needed_only_from": proved_safe + 1,
        "obligations": {
            "no_cheaper_attack_exists": ("discharged by the lower bound for every level up to "
                                         f"{proved_safe}, in constant arithmetic per level"),
            "this_attack_works": ("discharged by the explicit breaking table, which is a complete "
                                  "disproof on its own")},
    }
    if found.get("state") == "computed":
        result.update({"state": "computed", "breakdown_number": found["breakdown_number"],
                       "minimal_breaking_corrections": found["minimal_breaking_corrections"],
                       "allocations_examined_by_search": found["allocations_examined"],
                       "bound_and_search_agree": found["breakdown_number"] == proved_safe + 1})
    else:
        result.update({"state": found.get("state"), "reason": found.get("reason")})
    return result


def breakdown(observed, constant=None, ceiling=None, moves=None):
    """The fewest wrong objects that could destroy the claim, with no budget declared.

    A declared correction budget is an input someone has to defend, and a budget
    smaller than reality gives a confident wrong answer. Inverting the question
    removes that dependence: instead of asking whether a claim survives a budget,
    this asks how many objects would have to be wrong, in the most damaging
    combination, before it fails. An observation programme can then judge whether
    that many errors is plausible, which is a question about its own process
    rather than a number it must commit to in advance.

    Returns the breakdown number and every minimal allocation achieving it. They
    are minimal by construction, because no smaller total breaks the claim.
    """
    for cell in "wxyu":
        _count(cell, observed[cell])
    if not _holds(observed, constant):
        return {"state": "already_false",
                "reason": ("the claim does not hold on the observed table itself, so no correction "
                           "is needed to destroy it")}
    moves = tuple(moves) if moves else MOVES
    available = sum(observed[cell] for cell in "wxyu")
    if ceiling is not None:
        # Version 0.2.0 accepted a negative ceiling, searched nothing, and called
        # the empty answer complete. An invalid bound is not a small one.
        _count("the search ceiling", ceiling)
    limit = ceiling if ceiling is not None else available
    examined = 0
    for total in range(1, limit + 1):
        breaking = []
        for allocation in _allocations(total, len(moves)):
            examined += 1
            if examined > MAX_BREAKDOWN_ALLOCATIONS:
                return {"state": "unresolved",
                        "reason": (f"the search passed {MAX_BREAKDOWN_ALLOCATIONS} allocations "
                                   "without reaching a breakdown. This is a resource limit on "
                                   "this search, not a statement that no breakdown exists"),
                        "levels_fully_searched": total - 1,
                        "interrupted_at_level": total,
                        "note": ("totals up to and including the fully searched level were "
                                 "exhausted; the interrupted level was not")}
            leaving = {cell: 0 for cell in "wxyu"}
            for (source, _), amount in zip(moves, allocation):
                leaving[source] += amount
            if any(leaving[cell] > observed[cell] for cell in "wxyu"):
                continue
            table = _apply(observed, allocation, moves)
            if not _holds(table, constant):
                breaking.append({
                    "corrections": {move_name(s, t): n
                                    for (s, t), n in zip(moves, allocation) if n},
                    "table": table,
                    "margin": table["w"] * table["u"] - table["x"] * table["y"]})
        if breaking:
            return {"state": "computed",
                    "breakdown_number": total,
                    "of_how_many_recorded_objects": sum(observed[c] for c in "wxyu"),
                    "minimal_breaking_corrections": breaking,
                    "allocations_examined": examined,
                    "moves_searched": [move_name(s, t) for s, t in moves],
                    "claim": ("c > 1 for every unseen count" if constant is None
                              else f"c <= {constant} for every unseen count"),
                    "reading": (f"the claim fails only if at least {total} recorded objects are "
                                "wrong, in one of the combinations listed. Fewer than that, in any "
                                "combination, leaves it standing")}
    complete = limit >= available
    return {"state": "no_breakdown_within_the_searched_range",
            "levels_fully_searched": limit,
            "objects_available_to_move": available,
            "search_was_exhaustive": complete,
            "reason": (f"no combination of up to {limit} corrections destroys the claim, and {limit} "
                       "covers every object available to move, so this is complete for the moves "
                       "modelled" if complete else
                       f"no combination of up to {limit} corrections destroys the claim. The "
                       f"declared ceiling stops below the {available} objects available to move, "
                       "so a larger combination was never examined and this is not a complete "
                       "answer")}


def analyse(observed, budget):
    """Does the sign survive every admissible corrected table?"""
    for cell in "wxyu":
        if cell not in observed:
            raise BudgetError(f"the observed table has no {cell!r} count")
        _count(cell, observed[cell])
    if not isinstance(budget, dict):
        raise BudgetError("a declared correction budget is required; none is invented here")
    unknown = set(budget) - {move_name(s, t) for s, t in MOVES}
    if unknown:
        raise BudgetError(f"the budget names corrections this model does not define: {sorted(unknown)}")

    observed_settles = settles_the_sign(observed)
    worst = None
    worst_moves = None
    examined = 0
    for table, applied in admissible_tables(observed, budget):
        examined += 1
        margin = table["w"] * table["u"] - table["x"] * table["y"]
        if worst is None or margin < worst[0]:
            worst = (margin, table)
            worst_moves = applied

    survives = worst[0] > 0
    return {
        "artifact_id": "reiyah.table-robustness.report", "version": VERSION,
        "observed_table": dict(observed),
        "observed_settles_the_sign": observed_settles,
        "observed_margin": observed["w"] * observed["u"] - observed["x"] * observed["y"],
        "declared_budget": dict(budget),
        "corrected_tables_examined": examined,
        "sign_survives_every_admissible_table": survives,
        "worst_admissible_completion": {
            "table": worst[1], "margin": worst[0],
            "corrections_applied": worst_moves or {},
            "settles_the_sign": worst[0] > 0,
            "certificate": (
                "this table breaks the claim, and one evaluation of w * u - x * y on it confirms "
                "that. A breaking table is a complete disproof by itself"
                if worst[0] <= 0 else
                "this table has the smallest margin the search found, and evaluating it confirms "
                "only that this table does not break the claim. It is NOT a one line proof that "
                "no admissible table does; that rests on the enumeration being complete for the "
                "declared budget, which is a property of the search and not of this table")},
        "tolerance_by_correction_kind": {
            move_name(source, target): single_allowance_tolerance(observed, source, target)
            for source, target in MOVES},
        "smallest_sufficient_u_at_the_observed_w_x_y": smallest_sufficient_u(
            observed["w"], observed["x"], observed["y"]),
        "condition": "c > 1 for every unseen count if and only if w * u > x * y",
        "what_the_budget_is": (
            "a declared, bounded count of objects that may be misplaced or ineligible in each "
            "direction. It is an input defended by whoever declares it. No error budget, sampling "
            "frame, probability or human judgment is invented here"),
        "what_validity_is_not": (
            "valid counts are an observation obligation. Validity of the source facts, statistical "
            "independence of the channels, and procedural independence of a review are three "
            "different things, and only the first is addressed here"),
        "scope": ("a finite population identification statement about declared counts under a "
                  "declared correction budget. It carries no statistical uncertainty, no sampling "
                  "model and no claim about physical accuracy"),
    }


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: table_robustness.py INPUT.json\n")
        return 2
    with open(argv[1], "r", encoding="utf-8") as handle:
        declared = json.load(handle)
    try:
        if "observed_table" not in declared:
            raise BudgetError("the input declares no observed_table")
        wants_breakdown = declared.get("breakdown", False)
        has_budget = "budget" in declared
        if wants_breakdown and has_budget:
            raise BudgetError(
                "declare either a budget analysis or a budget free breakdown, not both. They "
                "answer different questions")
        if wants_breakdown:
            result = breakdown(declared["observed_table"])
        elif not has_budget:
            # Version 0.2.0 turned a missing budget into an empty one, which is a
            # different request with a different answer. Missing, null and an
            # explicitly empty budget are three different declarations.
            raise BudgetError(
                "no budget was declared. A budget analysis requires an explicit \"budget\" "
                "object, which may be empty to mean no corrections are admitted. To ask the "
                "budget free question instead, declare \"breakdown\": true")
        elif declared["budget"] is None:
            raise BudgetError(
                "the declared budget is null. Use an empty object to admit no corrections, or "
                "\"breakdown\": true to ask the budget free question")
        else:
            result = analyse(declared["observed_table"], declared["budget"])
    except (BudgetError, KeyError) as error:
        sys.stderr.write(f"declaration refused: {error}\n")
        return 1
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
