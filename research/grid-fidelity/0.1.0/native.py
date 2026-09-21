"""Exact finite-encoding envelope and complete obtainable reply sets."""

from fractions import Fraction
from math import ceil, floor

from common import integer_value, require


def distances(model):
    prefix = [0]
    for a, b in zip(model.times, model.times[1:]):
        prefix.append(prefix[-1] + floor(model.rate * (b - a) / model.quantum))
    return [[abs(a - b) for b in prefix] for a in prefix]


def bounds(model, known, band=None):
    distance = distances(model)
    n = len(model.times)
    pins = {i: integer_value(model, v) for i, v in known.items()}
    lower = [
        max([model.minimum_integer] + [v - distance[i][j] for j, v in pins.items()])
        for i in range(n)
    ]
    upper = [
        min([model.maximum_integer] + [v + distance[i][j] for j, v in pins.items()])
        for i in range(n)
    ]
    if band is not None:
        lo = [
            max(lower_bound, ceil((b - band) / model.quantum))
            for lower_bound, b in zip(lower, model.baseline)
        ]
        hi = [
            min(u, floor((b + band) / model.quantum))
            for u, b in zip(upper, model.baseline)
        ]
        lower = [max(lo[j] - distance[i][j] for j in range(n)) for i in range(n)]
        upper = [min(hi[j] + distance[i][j] for j in range(n)) for i in range(n)]
    if any(lower_bound > u for lower_bound, u in zip(lower, upper)):
        return None
    return lower, upper, distance


def minimum(model, lower, upper, distance):
    base = [b / model.quantum for b in model.baseline]
    epsilon = max(
        [Fraction(0)]
        + [lower_bound - b for lower_bound, b in zip(lower, base)]
        + [b - u for b, u in zip(base, upper)]
    )
    for i, a in enumerate(base):
        for j, b in enumerate(base):
            c = b + distance[i][j]
            midpoint = (a + c) / 2
            rounding = min(midpoint - floor(midpoint), ceil(midpoint) - midpoint)
            epsilon = max(epsilon, (a - c) / 2 + rounding)
    return epsilon * model.quantum


def evaluate(model, known):
    box = bounds(model, known)
    if box is None:
        return dict(status="inconsistent_premises", uniform_error_range_mps=None), None
    lower, upper, distance = box
    low = minimum(model, lower, upper, distance)
    lower_error = max(abs(model.quantum * z - b) for z, b in zip(lower, model.baseline))
    upper_error = max(abs(model.quantum * z - b) for z, b in zip(upper, model.baseline))
    high = max(lower_error, upper_error)
    status = (
        "supported"
        if high <= model.tolerance
        else "contradicted"
        if low > model.tolerance
        else "unresolved"
    )
    safe_box = bounds(model, known, low)
    require(safe_box is not None, "native_minimum_attainment")
    witness = dict(
        minimum_integers=safe_box[0],
        maximum_integers=lower if lower_error >= upper_error else upper,
    )
    return dict(status=status, uniform_error_range_mps=[str(low), str(high)]), witness


def priorities(model, known):
    lower, upper, _ = bounds(model, known)
    return [
        max(abs(model.quantum * lower_bound - b), abs(model.quantum * u - b))
        for lower_bound, u, b in zip(lower, upper, model.baseline)
    ]


def responses(model, known, query):
    require(
        type(query) is int and 0 <= query < len(model.times) and query not in known,
        "query_membership",
    )
    require(model.available[query] == "available", "query_unobtainable")
    box = bounds(model, known)
    require(box is not None, "query_inconsistent_family")
    lower, upper, distance = box
    start, end = lower[query], upper[query]
    all_lo, all_hi = start, end
    for i, b in enumerate(model.baseline):
        safe_lo = ceil((b - model.tolerance) / model.quantum)
        safe_hi = floor((b + model.tolerance) / model.quantum)
        if lower[i] < safe_lo:
            all_lo = max(all_lo, safe_lo + distance[i][query])
        if upper[i] > safe_hi:
            all_hi = min(all_hi, safe_hi - distance[i][query])
    any_box = bounds(model, known, model.tolerance)
    any_lo, any_hi = (
        (any_box[0][query], any_box[1][query]) if any_box else (end + 1, start - 1)
    )
    points = sorted(
        {start, end + 1}
        | {
            max(start, min(end + 1, x))
            for x in (all_lo, all_hi + 1, any_lo, any_hi + 1)
        }
    )
    cells = []
    for left, right in zip(points, points[1:]):
        status = (
            "supported"
            if all_lo <= left <= all_hi
            else "unresolved"
            if any_lo <= left <= any_hi
            else "contradicted"
        )
        if cells and cells[-1]["status"] == status:
            cells[-1]["upper_integer"] = right - 1
        else:
            cells.append(
                dict(lower_integer=left, upper_integer=right - 1, status=status)
            )
    return dict(
        status="response_set_computed",
        quantum_mps=str(model.quantum),
        feasible_integer_responses=[start, end],
        response_partition=cells,
        possible_statuses=sorted({c["status"] for c in cells}),
        guaranteed_resolution=all(c["status"] != "unresolved" for c in cells),
    )
