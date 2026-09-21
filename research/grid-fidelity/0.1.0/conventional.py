"""Conventional integer path propagation, exact feasibility search and projections.

This module imports only contract helpers, never the Reiyah decision solver.
"""

from math import ceil, floor, lcm

from common import require


def propagate(model, known, band=None, extra=None):
    n = len(model.times)
    low = [model.minimum_integer] * n
    high = [model.maximum_integer] * n
    for i, v in known.items():
        z = v / model.quantum
        require(z.denominator == 1, "unrepresentable_value")
        require(model.minimum_integer <= z <= model.maximum_integer, "encoding_range")
        low[i] = high[i] = z.numerator
    if band is not None:
        for i, b in enumerate(model.baseline):
            low[i] = max(low[i], ceil((b - band) / model.quantum))
            high[i] = min(high[i], floor((b + band) / model.quantum))
    if extra is not None:
        i, a, b = extra
        low[i], high[i] = max(low[i], a), min(high[i], b)
    capacity = []
    for i in range(n - 1):
        budget = (model.times[i + 1] - model.times[i]) * model.rate / model.quantum
        capacity.append(budget.numerator // budget.denominator)
    for i in range(1, n):
        low[i] = max(low[i], low[i - 1] - capacity[i - 1])
        high[i] = min(high[i], high[i - 1] + capacity[i - 1])
    for i in range(n - 2, -1, -1):
        low[i] = max(low[i], low[i + 1] - capacity[i])
        high[i] = min(high[i], high[i + 1] + capacity[i])
    return None if any(a > b for a, b in zip(low, high)) else (low, high)


def minimum_band(model, known, feasible):
    # Every achievable objective is a multiple of q/L, where L contains the
    # denominators of the coarse reconstruction in encoded-integer units.
    denominator = lcm(*((b / model.quantum).denominator for b in model.baseline))
    step = model.quantum / denominator
    upper_value = max(
        abs(model.quantum * z - b) for z, b in zip(feasible[0], model.baseline)
    )
    upper = upper_value / step
    require(upper.denominator == 1, "objective_grid")
    a, b = -1, upper.numerator
    while b - a > 1:
        middle = (a + b) // 2
        if propagate(model, known, step * middle) is None:
            a = middle
        else:
            b = middle
    return step * b


def evaluate(model, known):
    feasible = propagate(model, known)
    if feasible is None:
        return dict(status="inconsistent_premises", uniform_error_range_mps=None), None
    lower, upper = feasible
    low = minimum_band(model, known, feasible)
    errors = [
        max(abs(model.quantum * z - b) for z, b in zip(row, model.baseline))
        for row in feasible
    ]
    high = max(errors)
    status = (
        "supported"
        if high <= model.tolerance
        else "contradicted"
        if low > model.tolerance
        else "unresolved"
    )
    band_box = propagate(model, known, low)
    require(band_box is not None, "conventional_minimum_attainment")
    witness = dict(
        minimum_integers=band_box[0],
        maximum_integers=lower if errors[0] >= errors[1] else upper,
    )
    return dict(status=status, uniform_error_range_mps=[str(low), str(high)]), witness


def priorities(model, known):
    low, high = propagate(model, known)
    return [
        max(
            abs(model.quantum * low[i] - model.baseline[i]),
            abs(model.quantum * high[i] - model.baseline[i]),
        )
        for i in range(len(low))
    ]


def responses(model, known, query):
    require(
        type(query) is int and 0 <= query < len(model.times) and query not in known,
        "query_membership",
    )
    require(model.available[query] == "available", "query_unobtainable")
    feasible = propagate(model, known)
    require(feasible is not None, "query_inconsistent_family")
    left, right = feasible[0][query], feasible[1][query]
    safe = propagate(model, known, model.tolerance)
    good = None if safe is None else (safe[0][query], safe[1][query])
    unsafe = []
    for i, b in enumerate(model.baseline):
        too_low = ceil((b - model.tolerance) / model.quantum) - 1
        too_high = floor((b + model.tolerance) / model.quantum) + 1
        for a, z in (
            (model.minimum_integer, too_low),
            (too_high, model.maximum_integer),
        ):
            box = propagate(model, known, extra=(i, a, z))
            if box is not None:
                unsafe.append((box[0][query], box[1][query]))
    cuts = {left, right + 1}
    for a, b in unsafe + ([] if good is None else [good]):
        cuts.update((a, b + 1))
    cells = []
    for a, b in zip(sorted(cuts), sorted(cuts)[1:]):
        has_good = good is not None and good[0] <= a <= good[1]
        has_bad = any(x <= a <= y for x, y in unsafe)
        require(has_good or has_bad, "projection_coverage")
        label = (
            "unresolved"
            if has_good and has_bad
            else "supported"
            if has_good
            else "contradicted"
        )
        if cells and cells[-1]["status"] == label:
            cells[-1]["upper_integer"] = b - 1
        else:
            cells.append(dict(lower_integer=a, upper_integer=b - 1, status=label))
    labels = sorted({cell["status"] for cell in cells})
    return dict(
        status="response_set_computed",
        quantum_mps=str(model.quantum),
        feasible_integer_responses=[left, right],
        response_partition=cells,
        possible_statuses=labels,
        guaranteed_resolution="unresolved" not in labels,
    )
