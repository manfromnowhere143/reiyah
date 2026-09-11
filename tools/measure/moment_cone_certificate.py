"""Exact decision procedure for the truncated Hausdorff moment problem on [0,1].

Given the subset-averaged k-wise silence moments of K binary channels, decide
whether any probability measure on [0,1] reproduces them, which is exactly the
question of whether the exchangeable version-population model can represent that
population. Both verdicts carry a witness that a separate checker can verify
without invoking this module:

  infeasible  a polynomial h, nonnegative on [0,1] by construction, whose
              expectation under the declared moments is strictly negative;
  feasible    an atomic probability measure with rational atoms in [0,1] whose
              moments equal the declared ones exactly.

A grid can prove feasibility, because a grid measure is a measure. A grid can
never prove infeasibility. That asymmetry is enforced here: infeasibility is
decided only by an exact algebraic certificate over the whole continuum.

Exact rational arithmetic throughout. Standard library only. No network.
"""
from fractions import Fraction
from math import comb
import json
import re
import sys

SCHEMA_ID = "reiyah.moment-cone.task"
VERSION = "0.1.0"
MAX_ATOMS = 4096
MAX_COUNT = 10 ** 15
MAX_CHANNELS = 12
SMALL_WITNESS_BOUND = 100000

DECIMAL = re.compile(r"^-?(0|[1-9][0-9]*)(\.[0-9]+)?$")


class TaskError(ValueError):
    """The task is not admissible. Never downgraded to a favourable verdict."""


def rational(text):
    """Parse a plain decimal string exactly. Floats are refused on purpose."""
    if not isinstance(text, str) or not DECIMAL.match(text):
        raise TaskError(f"expected a plain decimal string, got {text!r}")
    return Fraction(text)


# ---------------------------------------------------------------- linear algebra

def ldl_negative_direction(matrix):
    """Return an exact rational v with v^T M v < 0, or None if M is PSD.

    Symmetric elimination producing M = L D L^T. A negative pivot d_i yields
    v = L^{-T} e_i with v^T M v = d_i. A zero pivot whose remaining row is not
    zero leaves the matrix undecided by this routine, reported as None with a
    reason so the caller can refuse rather than guess.
    """
    n = len(matrix)
    work = [row[:] for row in matrix]
    lower = [[Fraction(1) if i == j else Fraction(0) for j in range(n)] for i in range(n)]
    for i in range(n):
        pivot = work[i][i]
        if pivot == 0:
            if any(work[r][i] != 0 for r in range(i + 1, n)):
                return None, "zero_pivot_with_nonzero_column"
            continue
        if pivot < 0:
            direction = [Fraction(0)] * n
            direction[i] = Fraction(1)
            for row in range(i - 1, -1, -1):
                acc = Fraction(0)
                for col in range(row + 1, n):
                    acc += lower[col][row] * direction[col]
                direction[row] = -acc
            return direction, None
        for r in range(i + 1, n):
            factor = work[r][i] / pivot
            lower[r][i] = factor
            for c in range(i, n):
                work[r][c] -= factor * work[i][c]
    return None, None


def integerise(vector):
    """Scale a rational vector to coprime integers, sign fixed by the last entry."""
    denominator = 1
    for value in vector:
        denominator = denominator * value.denominator // _gcd(denominator, value.denominator)
    scaled = [int(value * denominator) for value in vector]
    common = 0
    for value in scaled:
        common = _gcd(common, abs(value))
    if common > 1:
        scaled = [value // common for value in scaled]
    for value in reversed(scaled):
        if value != 0:
            if value < 0:
                scaled = [-v for v in scaled]
            break
    return [Fraction(v) for v in scaled]


def _gcd(a, b):
    while b:
        a, b = b, a % b
    return a


# ------------------------------------------------------------ moment structure

def required_matrices(moments, degree):
    """The matrices whose positive semidefiniteness the [0,1] problem requires.

    moments is indexed from 0 with moments[0] = 1. Each entry pairs a matrix with
    the multiplier form of the certificate it generates.
    """
    if degree % 2 == 1:
        half = (degree - 1) // 2
        first = [[moments[i + j + 1] for j in range(half + 1)] for i in range(half + 1)]
        second = [[moments[i + j] - moments[i + j + 1] for j in range(half + 1)]
                  for i in range(half + 1)]
        return [("x", first), ("1-x", second)]
    half = degree // 2
    first = [[moments[i + j] for j in range(half + 1)] for i in range(half + 1)]
    if half == 0:
        return [("1", first)]
    second = [[moments[i + j + 1] - moments[i + j + 2] for j in range(half)]
              for i in range(half)]
    return [("1", first), ("x(1-x)", second)]


def expand_certificate(form, direction):
    """Coefficients of h(x) = multiplier(x) * p(x)^2, p from `direction`.

    Every admitted multiplier is nonnegative on [0,1], and a square is
    nonnegative everywhere, so h is nonnegative on [0,1] by construction.
    """
    square = [Fraction(0)] * (2 * len(direction) - 1)
    for i, vi in enumerate(direction):
        for j, vj in enumerate(direction):
            square[i + j] += vi * vj
    multipliers = {"1": [Fraction(1)],
                   "x": [Fraction(0), Fraction(1)],
                   "1-x": [Fraction(1), Fraction(-1)],
                   "x(1-x)": [Fraction(0), Fraction(1), Fraction(-1)]}
    if form not in multipliers:
        raise TaskError(f"unknown certificate form {form!r}")
    factor = multipliers[form]
    out = [Fraction(0)] * (len(square) + len(factor) - 1)
    for i, ci in enumerate(factor):
        for j, cj in enumerate(square):
            out[i + j] += ci * cj
    return out


def functional(coefficients, moments):
    """Sum_k a_k m_k, the expectation of h under a measure with those moments."""
    total = Fraction(0)
    for power, coefficient in enumerate(coefficients):
        if power >= len(moments):
            raise TaskError("certificate degree exceeds the declared moments")
        total += coefficient * moments[power]
    return total


def box_worst_case(coefficients, moments, half_widths):
    """The largest value Sum_k a_k m_k can take over the declared rounding box.

    moments[0] = 1 is exact, so index 0 contributes no slack.
    """
    total = functional(coefficients, moments)
    slack = Fraction(0)
    for power, coefficient in enumerate(coefficients):
        if power == 0:
            continue
        slack += abs(coefficient) * half_widths[power - 1]
    return total + slack


# ---------------------------------------------------------------- exact simplex

def simplex_feasible(rows, targets, column_count):
    """Phase-one simplex over the rationals. Returns a nonnegative solution or None.

    Bland's rule is used so termination is guaranteed without an anti-cycling
    heuristic. `rows` is a list of coefficient lists; `targets` the right side.
    """
    height = len(rows)
    tableau = []
    for index in range(height):
        row = [Fraction(value) for value in rows[index]]
        target = Fraction(targets[index])
        if target < 0:
            row = [-value for value in row]
            target = -target
        artificial = [Fraction(1) if k == index else Fraction(0) for k in range(height)]
        tableau.append(row + artificial + [target])
    total_columns = column_count + height
    cost = [Fraction(0)] * (total_columns + 1)
    for row in tableau:
        for index in range(total_columns + 1):
            cost[index] -= row[index]
    for index in range(column_count, total_columns):
        cost[index] = Fraction(0)
    basis = [column_count + index for index in range(height)]
    for _ in range(200000):
        entering = None
        for index in range(total_columns):
            if cost[index] < 0:
                entering = index
                break
        if entering is None:
            break
        leaving, best = None, None
        for index in range(height):
            if tableau[index][entering] > 0:
                ratio = tableau[index][total_columns] / tableau[index][entering]
                if best is None or ratio < best or (ratio == best and basis[index] < basis[leaving]):
                    best, leaving = ratio, index
        if leaving is None:
            return None
        pivot = tableau[leaving][entering]
        tableau[leaving] = [value / pivot for value in tableau[leaving]]
        for index in range(height):
            if index != leaving and tableau[index][entering] != 0:
                factor = tableau[index][entering]
                tableau[index] = [a - factor * b for a, b in zip(tableau[index], tableau[leaving])]
        if cost[entering] != 0:
            factor = cost[entering]
            cost = [a - factor * b for a, b in zip(cost, tableau[leaving])]
        basis[leaving] = entering
    else:
        return None
    if -cost[total_columns] != 0:
        return None
    solution = [Fraction(0)] * column_count
    for index in range(height):
        if basis[index] < column_count:
            solution[basis[index]] = tableau[index][total_columns]
    return solution


def atom_grid(coarse, fine):
    """A declared rational grid on [0,1], refined near zero where small moments live.

    The coarse part covers the interval uniformly. The fine part adds `coarse`
    further atoms between 0 and coarse/fine, because a population whose channels
    are rarely silent has all of its mass close to zero.
    """
    if coarse < 2 or fine < coarse:
        raise TaskError("atom grid denominators are not admissible")
    atoms = {Fraction(j, coarse) for j in range(coarse + 1)}
    atoms |= {Fraction(j, fine) for j in range(1, coarse + 1)}
    ordered = sorted(atoms)
    if len(ordered) > MAX_ATOMS:
        raise TaskError("atom grid exceeds the declared maximum")
    return ordered


def reduce_direction(direction, form, moments, half_widths):
    """Find the smallest-integer direction that still certifies over the box.

    The exact elimination direction certifies but can carry very large integers.
    A witness a reader can check by hand is worth more than a tidy derivation, so
    the direction is rounded to successively finer denominators and the first one
    that still yields a strictly negative box worst case is kept. The original is
    returned unchanged when no smaller one certifies.
    """
    lead = next((value for value in reversed(direction) if value != 0), None)
    if lead is None:
        return direction
    scaled = [value / lead for value in direction]
    exact_input = all(value == 0 for value in half_widths)
    best, best_score = None, None
    for denominator in (2, 4, 8, 10, 20, 40, 100, 200, 500, 1000, 2000, 10000, 100000):
        candidate = integerise([Fraction(round(value * denominator), denominator)
                                for value in scaled])
        if all(value == 0 for value in candidate):
            continue
        if max(abs(value) for value in candidate) > SMALL_WITNESS_BOUND:
            continue
        coefficients = expand_certificate(form, candidate)
        centre = functional(coefficients, moments)
        worst = box_worst_case(coefficients, moments, half_widths)
        if centre >= 0 or worst >= 0:
            continue
        if exact_input:
            # No box to optimise against, so prefer the witness a reader can check.
            score = -max(abs(value) for value in candidate)
        else:
            score = -centre / (worst - centre)
        if best_score is None or score > best_score:
            best, best_score = candidate, score
    return best if best is not None else direction


def measure_for(moments, atoms):
    """An exact rational atomic measure matching `moments`, or None."""
    degree = len(moments) - 1
    rows = [[atom ** power for atom in atoms] for power in range(degree + 1)]
    weights = simplex_feasible(rows, moments, len(atoms))
    if weights is None:
        return None
    support = [(atom, weight) for atom, weight in zip(atoms, weights) if weight != 0]
    for power in range(degree + 1):
        if sum(weight * atom ** power for atom, weight in support) != moments[power]:
            return None
    return support


def box_corners(moments, half_widths):
    """The corners of the declared rounding box, moments[0] held exact.

    A coordinate whose half width is zero contributes one value, not two. Without
    that the degenerate box would be enumerated as 2^n copies of a single point.
    """
    corners = [[moments[0]]]
    for index, half in enumerate(half_widths):
        centre = moments[index + 1]
        offsets = (Fraction(0),) if half == 0 else (-half, half)
        grown = []
        for corner in corners:
            for offset in offsets:
                grown.append(corner + [centre + offset])
        corners = grown
    return corners


# ------------------------------------------------------------------- decision

def moments_from_histogram(counts, channels):
    """Exact subset-averaged moments from an integer silence histogram.

    counts[s] is the number of opportunities on which exactly s channels were
    silent. Because these are counts, the moments are exact rationals and no
    rounding box exists. This is the strongest available input form and it is
    preferred over printed decimals wherever the counts are known.
    """
    if len(counts) != channels + 1:
        raise TaskError("silence_histogram must carry channel_count + 1 entries")
    for value in counts:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise TaskError("silence_histogram entries must be nonnegative integers")
        if value > MAX_COUNT:
            raise TaskError("silence_histogram entry exceeds the declared limit")
    total = sum(counts)
    if total <= 0:
        raise TaskError("silence_histogram is empty")
    moments = [Fraction(1)]
    for k in range(1, channels + 1):
        numerator = sum(counts[s] * comb(s, k) for s in range(channels + 1))
        moments.append(Fraction(numerator, total * comb(channels, k)))
    return moments, total


def decide(task):
    """Decide one task. Returns a report dict; never raises for an adverse result."""
    if task.get("schema_id") != SCHEMA_ID:
        raise TaskError("unexpected schema_id")
    channels = task["channel_count"]
    if not isinstance(channels, int) or isinstance(channels, bool) or not 1 <= channels <= MAX_CHANNELS:
        raise TaskError("channel_count out of range")
    # Absent and explicitly null are different. A key present with a null value is a
    # statement the caller made, and the schema forbids it, so it is refused here
    # rather than silently read as the default.
    for field in ("silence_histogram", "moments", "rounding_half_width",
                  "coarse_denominator", "fine_denominator"):
        if field in task and task[field] is None:
            raise TaskError(f"{field} is present and null; omit the key or give a value")
    if "silence_histogram" in task and "moments" in task:
        raise TaskError("give either silence_histogram or moments, never both")
    if "silence_histogram" not in task and "moments" not in task:
        raise TaskError("give either silence_histogram or moments")
    histogram = task.get("silence_histogram")
    if histogram is not None:
        if not isinstance(histogram, list):
            raise TaskError("silence_histogram must be a list")
        if len(histogram) > MAX_CHANNELS + 1:
            raise TaskError("silence_histogram exceeds the declared channel limit")
        if "rounding_half_width" in task:
            raise TaskError("a silence histogram is exact and admits no rounding box")
        moments, opportunities = moments_from_histogram(histogram, channels)
        values = [str(value) for value in moments[1:]]
    else:
        opportunities = None
        values = task["moments"]
        if not isinstance(values, list):
            raise TaskError("moments must be a list")
        if len(values) != channels:
            raise TaskError("moment count must equal channel_count")
        moments = [Fraction(1)] + [rational(text) for text in values]
    for value in moments:
        if not 0 <= value <= 1:
            raise TaskError("every moment must lie in [0,1]")
    half_text = task.get("rounding_half_width")
    if histogram is not None:
        half_text = None
    if half_text is None:
        half_widths = [Fraction(0)] * channels
    elif isinstance(half_text, str):
        half_widths = [rational(half_text)] * channels
    else:
        half_widths = [rational(text) for text in half_text]
    if len(half_widths) != channels or any(value < 0 for value in half_widths):
        raise TaskError("rounding_half_width is not admissible")

    report = {
        "artifact_id": "reiyah.moment-cone.report",
        "version": VERSION,
        "population_label": task.get("population_label"),
        "channel_count": channels,
        "moments": values,
        "silence_histogram": list(histogram) if histogram is not None else None,
        "opportunities": opportunities,
        "rounding_half_width": [str(value) for value in half_widths],
        "verdict": "unresolved",
        "reason": None,
        "certificate": None,
        "measure": None,
        "notes": [],
    }

    for form, matrix in required_matrices(moments, channels):
        direction, failure = ldl_negative_direction(matrix)
        if failure is not None:
            report["notes"].append(f"{form}: {failure}")
            continue
        if direction is None:
            continue
        direction = integerise(direction)
        reduced = reduce_direction(direction, form, moments, half_widths)
        if functional(expand_certificate(form, reduced), moments) < 0:
            direction = reduced
        coefficients = expand_certificate(form, direction)
        centre = functional(coefficients, moments)
        worst = box_worst_case(coefficients, moments, half_widths)
        if centre >= 0:
            report["notes"].append(f"{form}: direction did not yield a negative functional")
            continue
        report["certificate"] = {
            "form": form,
            "polynomial_coefficients": [str(value) for value in direction],
            "expanded_coefficients": [str(value) for value in coefficients],
            "functional_at_centre": str(centre),
            "functional_box_worst_case": str(worst),
            "box_margin_ratio": str(-centre / (worst - centre)) if worst != centre else "exact",
        }
        if histogram is not None:
            report["verdict"] = "infeasible_exact"
            report["reason"] = "an exact nonnegative polynomial has negative expectation for the exact moments of the declared silence histogram"
        elif worst < 0:
            report["verdict"] = "infeasible_over_box"
            report["reason"] = "an exact nonnegative polynomial has negative expectation for every moment vector in the declared box"
        else:
            report["verdict"] = "infeasible_at_centre_only"
            report["reason"] = "the certificate is negative at the printed moments but not across the whole rounding box"
        return report

    for field in ("coarse_denominator", "fine_denominator"):
        if field in task:
            value = task[field]
            if not isinstance(value, int) or isinstance(value, bool):
                raise TaskError(f"{field} must be an integer")
            if not 2 <= value <= MAX_ATOMS * 1000:
                raise TaskError(f"{field} is outside the admitted range")
    if "coarse_denominator" in task or "fine_denominator" in task:
        ladder = [(int(task.get("coarse_denominator", 60)),
                   int(task.get("fine_denominator", 6000)))]
    else:
        ladder = [(60, 6000), (120, 12000), (240, 24000)]
    centre_measure, grid = None, None
    for coarse, fine in ladder:
        grid = atom_grid(coarse, fine)
        centre_measure = measure_for(moments, grid)
        if centre_measure is not None:
            report["atom_grid"] = {"coarse_denominator": coarse, "fine_denominator": fine}
            break
    report["atom_count"] = len(grid) if grid else 0
    if centre_measure is None:
        report["verdict"] = "unresolved"
        report["reason"] = ("no certificate of infeasibility and no measure on the declared "
                            "rational atom grid; the procedure is sound, meaning every verdict it "
                            "gives carries a witness, but its search is not complete, so a feasible "
                            "vector whose only measures use atoms off the grid is reported here as "
                            "unresolved rather than decided")
        return report
    corner_measures = []
    for corner in box_corners(moments, half_widths):
        if any(not 0 <= value <= 1 for value in corner):
            corner_measures = None
            report["notes"].append("a box corner leaves [0,1]")
            break
        found = measure_for(corner, grid)
        if found is None:
            corner_measures = None
            hostile = None
            for form, matrix in required_matrices(corner, channels):
                direction, _ = ldl_negative_direction(matrix)
                if direction is not None:
                    hostile = form
                    break
            if hostile is not None:
                report["notes"].append(
                    f"a box corner is itself infeasible ({hostile} form); the printed vector lies "
                    "near the boundary of the moment set and the box straddles it")
                report["box_state"] = "contains_infeasible_corner"
            else:
                report["notes"].append("a box corner was not representable on the declared grid")
                report["box_state"] = "uncertified_grid_failure"
            break
        corner_measures.append({
            "moments": [str(value) for value in corner],
            "support": [[str(atom), str(weight)] for atom, weight in found],
        })
    if histogram is not None:
        report["verdict"] = "feasible_exact"
        report["reason"] = "the exact moments of the declared silence histogram are representable by an explicit atomic measure on [0,1]"
        report["measure"] = {"centre": [[str(a), str(w)] for a, w in centre_measure],
                             "corners": []}
    elif corner_measures is not None and any(value > 0 for value in half_widths):
        report["box_state"] = "certified_feasible"
        report["verdict"] = "feasible_over_box"
        report["reason"] = "every corner of the declared box is representable, and the moment set is convex, so the whole box is"
        report["measure"] = {"centre": [[str(a), str(w)] for a, w in centre_measure],
                             "corners": corner_measures}
    else:
        report["verdict"] = "feasible_at_centre"
        report["reason"] = "the printed moment vector is representable by an explicit atomic measure on [0,1]"
        report["measure"] = {"centre": [[str(a), str(w)] for a, w in centre_measure],
                             "corners": corner_measures or []}
    return report


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: moment_cone_certificate.py TASK.json\n")
        return 2
    with open(argv[1], "r", encoding="utf-8") as handle:
        task = json.load(handle)
    try:
        report = decide(task)
    except TaskError as error:
        sys.stderr.write(f"task refused: {error}\n")
        return 3
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
