"""Independent checker for a moment-cone report.

This module imports nothing from the producer. It re-derives every quantity it
confirms from the task and the report's own witness, using exact rational
arithmetic and no optimiser, root finder or grid.

What a confirmation establishes, and only this:

  infeasible  the stated polynomial is nonnegative on [0,1] by its declared
              multiplier-times-square form, its expansion is the stated
              coefficient vector, and its expectation is negative for the
              declared moments, or for every vector in the declared box;
  feasible    the stated atoms lie in [0,1], the weights are nonnegative and sum
              to one, and the declared moments are reproduced exactly; and for a
              whole-box verdict, that the supplied corner set is exactly the
              corner set the task declares.

The corner rule is stated positively on purpose. Version `0.1.0` of this module
checked that every supplied corner was a corner and that the count was right, and
a report that padded each corner with an extra unconstrained coordinate defeated
its duplicate test, presenting two copies of one corner as both. The retained
input is under `evidence/moment-cone/retained-failures/`. Counting is not
coverage; this version compares sets.

Shared trusted surface with the producer, and nothing else: the JSON module, the
decimal and rational string conventions declared here, and Python's Fraction and
integer arithmetic. No producer search, optimisation, elimination or grid code is
imported or reimplemented.
"""
from fractions import Fraction
from math import comb
import hashlib
import json
import re
import sys

DECIMAL = re.compile(r"^-?(0|[1-9][0-9]*)(\.[0-9]+)?$")
RATIONAL = re.compile(r"^-?(0|[1-9][0-9]*)(/[1-9][0-9]*)?$")
MULTIPLIERS = {
    "1": [Fraction(1)],
    "x": [Fraction(0), Fraction(1)],
    "1-x": [Fraction(1), Fraction(-1)],
    "x(1-x)": [Fraction(0), Fraction(1), Fraction(-1)],
}
MAX_CHANNELS = 12
MAX_NUMERIC_CHARS = 4096
MAX_SUPPORT_ATOMS = 8192
MAX_CORNERS = 1 << MAX_CHANNELS
TASK_KEYS = {"schema_id", "population_label", "channel_count", "moments",
             "silence_histogram", "rounding_half_width", "coarse_denominator",
             "fine_denominator"}
REPORT_KEYS = {"artifact_id", "version", "population_label", "channel_count", "moments",
               "rounding_half_width", "verdict", "reason", "certificate", "measure",
               "notes", "atom_count", "atom_grid", "box_state", "silence_histogram",
               "opportunities"}
CERTIFICATE_KEYS = {"form", "polynomial_coefficients", "expanded_coefficients",
                    "functional_at_centre", "functional_box_worst_case", "box_margin_ratio"}
MEASURE_KEYS = {"centre", "corners"}
CORNER_KEYS = {"moments", "support"}
VERDICTS = {"infeasible_over_box", "infeasible_at_centre_only", "infeasible_exact",
            "feasible_over_box", "feasible_at_centre", "feasible_exact", "unresolved"}
EXACT_VERDICTS = {"infeasible_exact", "feasible_exact"}


class Rejected(Exception):
    """The report does not establish its verdict."""


def _no_duplicate_keys(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise Rejected(f"duplicate JSON key {key!r}")
        seen[key] = value
    return seen


def load(path):
    """Parse JSON, refusing duplicate keys rather than silently keeping the last."""
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle, object_pairs_hook=_no_duplicate_keys)


def _numeric(text, pattern, what):
    if not isinstance(text, str):
        raise Rejected(f"{what} is not a string: {text!r}")
    if len(text) > MAX_NUMERIC_CHARS:
        raise Rejected(f"{what} exceeds {MAX_NUMERIC_CHARS} characters")
    if not pattern.match(text):
        raise Rejected(f"{what} is not in the declared form: {text!r}")
    return Fraction(text)


def decimal(text):
    return _numeric(text, DECIMAL, "value")


def exact(text):
    return _numeric(text, RATIONAL, "value")


def only_known(body, allowed, what):
    if not isinstance(body, dict):
        raise Rejected(f"{what} is not an object")
    unknown = sorted(set(body) - allowed)
    if unknown:
        raise Rejected(f"{what} carries unknown fields: {unknown}")


def polynomial_product(left, right):
    out = [Fraction(0)] * (len(left) + len(right) - 1)
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            out[i + j] += a * b
    return out


# ------------------------------------------------------------------ the task

def read_task(task):
    """Parse and validate the task. Explicit nulls are refused, not defaulted."""
    """Derive the moments and the rounding box from the task alone.

    The box never comes from the report. A report permitted to declare its own
    box could buy a whole-box verdict it has not earned.
    """
    only_known(task, TASK_KEYS, "task")
    if task.get("schema_id") != "reiyah.moment-cone.task":
        raise Rejected("task schema_id is not the expected one")
    for field in ("silence_histogram", "moments", "rounding_half_width",
                  "coarse_denominator", "fine_denominator"):
        if field in task and task[field] is None:
            raise Rejected(f"task {field} is present and null; omit the key or give a value")
    if "silence_histogram" in task and "moments" in task:
        raise Rejected("task gives both a silence histogram and moments")
    count = task.get("channel_count")
    if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= MAX_CHANNELS:
        raise Rejected("task channel_count is not an integer in range")
    histogram = task.get("silence_histogram")
    if histogram is not None:
        if "moments" in task:
            raise Rejected("task gives both a silence histogram and moments")
        if "rounding_half_width" in task:
            raise Rejected("a silence histogram is exact and admits no rounding box")
        if not isinstance(histogram, list) or len(histogram) != count + 1:
            raise Rejected("silence_histogram must carry channel_count + 1 entries")
        for value in histogram:
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise Rejected("silence_histogram entries must be nonnegative integers")
        total = sum(histogram)
        if total <= 0:
            raise Rejected("silence_histogram is empty")
        moments = [Fraction(1)]
        for k in range(1, count + 1):
            numerator = sum(histogram[s] * comb(s, k) for s in range(count + 1))
            moments.append(Fraction(numerator, total * comb(count, k)))
        for value in moments:
            if not 0 <= value <= 1:
                raise Rejected("a derived moment lies outside [0,1]")
        return count, moments, [Fraction(0)] * count
    values = task.get("moments")
    if not isinstance(values, list) or len(values) != count:
        raise Rejected("task moments must be a list of channel_count entries")
    moments = [Fraction(1)] + [decimal(text) for text in values]
    for value in moments:
        if not 0 <= value <= 1:
            raise Rejected("every task moment must lie in [0,1]")
    declared = task.get("rounding_half_width")
    if declared is None:
        half_widths = [Fraction(0)] * count
    elif isinstance(declared, str):
        half_widths = [decimal(declared)] * count
    elif isinstance(declared, list):
        if len(declared) != count:
            raise Rejected("task rounding widths do not match the moment count")
        half_widths = [decimal(text) for text in declared]
    else:
        raise Rejected("task rounding_half_width is not admissible")
    if any(value < 0 for value in half_widths):
        raise Rejected("negative rounding width")
    return count, moments, half_widths


def declared_corners(moments, half_widths):
    """The exact corner set of the declared box, as a set of rational tuples.

    A coordinate of zero width contributes one value, not two, so a degenerate
    box has exactly one corner rather than 2^K copies of one point.
    """
    corners = [(moments[0],)]
    for index, half in enumerate(half_widths):
        centre = moments[index + 1]
        offsets = (Fraction(0),) if half == 0 else (-half, half)
        corners = [corner + (centre + offset,) for corner in corners for offset in offsets]
        if len(corners) > MAX_CORNERS:
            raise Rejected("declared box has more corners than the limit permits")
    return set(corners)


# ------------------------------------------------------------- infeasibility

def check_infeasible(report, moments, half_widths, require_box):
    certificate = report.get("certificate")
    only_known(certificate if isinstance(certificate, dict) else {}, CERTIFICATE_KEYS,
               "certificate")
    if not isinstance(certificate, dict):
        raise Rejected("verdict claims infeasibility with no certificate")
    form = certificate.get("form")
    if form not in MULTIPLIERS:
        raise Rejected(f"certificate multiplier {form!r} is not an admitted nonnegative form")
    raw = certificate.get("polynomial_coefficients")
    if not isinstance(raw, list) or not raw:
        raise Rejected("certificate polynomial is missing")
    direction = [exact(text) for text in raw]
    if all(value == 0 for value in direction):
        raise Rejected("certificate polynomial is identically zero")
    rebuilt = polynomial_product(MULTIPLIERS[form], polynomial_product(direction, direction))
    claimed_raw = certificate.get("expanded_coefficients")
    if not isinstance(claimed_raw, list):
        raise Rejected("certificate expansion is missing")
    claimed = [exact(text) for text in claimed_raw]
    if len(claimed) != len(rebuilt):
        raise Rejected("claimed expansion has the wrong degree")
    if claimed != rebuilt:
        raise Rejected("claimed expansion does not equal multiplier times square")
    if len(claimed) > len(moments):
        raise Rejected("certificate degree exceeds the declared moments")
    centre = sum(coefficient * moments[power] for power, coefficient in enumerate(claimed))
    if centre != exact(certificate.get("functional_at_centre", "0")):
        raise Rejected("stated functional value at the printed moments is wrong")
    if centre >= 0:
        raise Rejected("functional at the printed moments is not negative")
    slack = sum(abs(coefficient) * half_widths[power - 1]
                for power, coefficient in enumerate(claimed) if power > 0)
    worst = centre + slack
    if worst != exact(certificate.get("functional_box_worst_case", "0")):
        raise Rejected("stated box worst case is wrong")
    if require_box and worst >= 0:
        raise Rejected("verdict claims box infeasibility but the box worst case is not negative")
    return {"multiplier": form, "degree": len(claimed) - 1,
            "functional_at_centre": str(centre), "functional_box_worst_case": str(worst)}


# --------------------------------------------------------------- feasibility

def check_measure(support, targets, what):
    if not isinstance(support, list) or not support:
        raise Rejected(f"{what} has no support")
    if len(support) > MAX_SUPPORT_ATOMS:
        raise Rejected(f"{what} exceeds the support size limit")
    parsed = []
    for entry in support:
        if not isinstance(entry, list) or len(entry) != 2:
            raise Rejected(f"{what} support entry is not an atom and weight pair")
        atom, weight = exact(entry[0]), exact(entry[1])
        if not 0 <= atom <= 1:
            raise Rejected(f"{what} atom {entry[0]} is outside [0,1]")
        if weight < 0:
            raise Rejected(f"{what} weight {entry[1]} is negative")
        parsed.append((atom, weight))
    if sum(weight for _, weight in parsed) != 1:
        raise Rejected(f"{what} weights do not sum to 1")
    for power, target in enumerate(targets):
        if sum(weight * atom ** power for atom, weight in parsed) != target:
            raise Rejected(f"{what} moment {power} is not the declared value")
    return len(parsed)


def check_feasible(report, count, moments, half_widths, require_box):
    measure = report.get("measure")
    only_known(measure if isinstance(measure, dict) else {}, MEASURE_KEYS, "measure")
    if not isinstance(measure, dict):
        raise Rejected("verdict claims feasibility with no measure")
    centre_atoms = check_measure(measure.get("centre"), moments, "centre measure")
    if not require_box:
        return {"centre_atoms": centre_atoms, "corners_checked": 0}

    expected = declared_corners(moments, half_widths)
    corners = measure.get("corners")
    if not isinstance(corners, list):
        raise Rejected("verdict claims whole-box feasibility with no corner list")
    if len(corners) != len(expected):
        raise Rejected(f"expected {len(expected)} declared corners, found {len(corners)}")
    supplied = set()
    for corner in corners:
        only_known(corner if isinstance(corner, dict) else {}, CORNER_KEYS, "corner")
        raw = corner.get("moments")
        if not isinstance(raw, list) or len(raw) != count + 1:
            raise Rejected(f"a corner does not carry exactly {count + 1} moments")
        targets = [exact(text) for text in raw]
        key = tuple(targets)
        if key in supplied:
            raise Rejected("a declared corner is supplied more than once")
        if key not in expected:
            raise Rejected("a supplied corner is not a corner of the declared box")
        supplied.add(key)
        check_measure(corner.get("support"), targets, "corner measure")
    if supplied != expected:
        raise Rejected("the supplied corners do not cover the declared box")
    return {"centre_atoms": centre_atoms, "corners_checked": len(supplied),
            "corners_declared": len(expected)}


# ------------------------------------------------------------------- verify

def verify(task, report):
    count, moments, half_widths = read_task(task)
    exact_task = task.get("silence_histogram") is not None
    only_known(report, REPORT_KEYS, "report")
    if task.get("silence_histogram") is not None:
        if report.get("silence_histogram") != task.get("silence_histogram"):
            raise Rejected("report silence histogram does not match the task")
        if [exact(text) for text in report.get("moments", [])] != moments[1:]:
            raise Rejected("report moments are not the exact moments of the declared histogram")
    elif report.get("moments") != task.get("moments"):
        raise Rejected("report moments do not match the task moments")
    if "channel_count" in report:
        stated_count = report["channel_count"]
        if not isinstance(stated_count, int) or isinstance(stated_count, bool):
            raise Rejected("report channel_count is not an integer")
        if stated_count != count:
            raise Rejected("report channel_count does not match the task")
    if "opportunities" in report and report["opportunities"] is not None:
        stated = report["opportunities"]
        if not isinstance(stated, int) or isinstance(stated, bool):
            raise Rejected("report opportunities is not an integer")
        if not exact_task or stated != sum(task["silence_histogram"]):
            raise Rejected("report opportunities is not the total of the declared histogram")
    stated_raw = report.get("rounding_half_width")
    if not isinstance(stated_raw, list) or len(stated_raw) != count:
        raise Rejected("report does not restate the rounding box for every moment")
    if [exact(text) for text in stated_raw] != half_widths:
        raise Rejected("report rounding box does not equal the task rounding box")
    verdict = report.get("verdict")
    if verdict not in VERDICTS:
        raise Rejected(f"unknown verdict {verdict!r}")
    exact_input = task.get("silence_histogram") is not None
    # `unresolved` asserts nothing, so it is valid for either task form. Rejecting an
    # honest abstention would push a producer towards manufacturing a witness.
    if verdict != "unresolved" and (verdict in EXACT_VERDICTS) != exact_input:
        raise Rejected("an exact verdict requires an exact silence-histogram task, and vice versa")
    if verdict == "infeasible_exact":
        detail = check_infeasible(report, moments, half_widths, True)
    elif verdict == "feasible_exact":
        detail = check_feasible(report, count, moments, half_widths, False)
    elif verdict == "infeasible_over_box":
        detail = check_infeasible(report, moments, half_widths, True)
    elif verdict == "infeasible_at_centre_only":
        detail = check_infeasible(report, moments, half_widths, False)
    elif verdict == "feasible_over_box":
        if all(value == 0 for value in half_widths):
            raise Rejected("a zero-width box cannot support a whole-box feasibility verdict")
        detail = check_feasible(report, count, moments, half_widths, True)
    elif verdict == "feasible_at_centre":
        detail = check_feasible(report, count, moments, half_widths, False)
    else:
        detail = {"note": "an unresolved verdict asserts nothing and is accepted as such"}
    return {"verdict": verdict, "checked": detail}


UNVERIFIED_REPORT_FIELDS = ("artifact_id", "version", "population_label", "reason",
                            "notes", "atom_count", "atom_grid", "box_state")
ASSERTIONS_CHECKED = {
    "infeasible": ["the multiplier is one of the four forms nonnegative on [0,1]",
                   "the stated expansion equals multiplier times the square of the stated polynomial",
                   "the linear functional at the declared moments is the stated value and is negative",
                   "the box worst case is the stated value, and is negative for a whole-box verdict"],
    "feasible": ["every atom lies in [0,1] and every weight is nonnegative",
                 "the weights sum to one",
                 "the declared moments are reproduced exactly",
                 "for a whole-box verdict, the supplied corner set equals the declared corner set"],
    "unresolved": ["nothing; an unresolved verdict asserts nothing and is accepted as such"],
}


def digest(path):
    with open(path, "rb") as handle:
        return "sha256:" + hashlib.sha256(handle.read()).hexdigest()


def main(argv):
    if len(argv) != 3:
        sys.stderr.write("usage: check_moment_cone_certificate.py TASK.json REPORT.json\n")
        return 2
    try:
        task, report = load(argv[1]), load(argv[2])
        outcome = verify(task, report)
    except (Rejected, KeyError, TypeError, IndexError, ValueError) as error:
        sys.stderr.write(f"REJECTED: {error}\n")
        return 1
    verdict = outcome["verdict"]
    family = ("unresolved" if verdict == "unresolved"
              else "infeasible" if verdict.startswith("infeasible") else "feasible")
    receipt = {
        "task_sha256": digest(argv[1]),
        "report_sha256": digest(argv[2]),
        "assertions_checked": ASSERTIONS_CHECKED[family],
        "fields_not_verified": [name for name in UNVERIFIED_REPORT_FIELDS if name in report],
        "note": ("this receipt binds the exact bytes checked. Fields listed as not verified carry "
                 "no confirmation of any kind, including the population label, which is not custody"),
    }
    json.dump({"result": "confirmed", **outcome, "receipt": receipt},
              sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
