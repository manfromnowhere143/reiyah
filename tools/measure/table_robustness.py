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
from itertools import product
import json
import os
import sys

VERSION = "0.1.0"
MAX_TABLES = 4_000_000

# Each allowance names objects leaving one cell for another, or leaving entirely.
MOVES = (("u", "x"), ("u", "y"), ("w", "x"), ("w", "y"),
         ("x", "w"), ("y", "w"), ("x", "u"), ("y", "u"),
         ("w", None), ("x", None), ("y", None), ("u", None))


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
            "certificate": ("evaluate w * u - x * y on this table. The claim is checked by one "
                            "evaluation, not by trusting this search")},
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
        result = analyse(declared["observed_table"], declared.get("budget", {}))
    except (BudgetError, KeyError) as error:
        sys.stderr.write(f"declaration refused: {error}\n")
        return 1
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
