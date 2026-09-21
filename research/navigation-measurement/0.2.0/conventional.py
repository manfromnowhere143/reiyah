"""Original-coordinate conventional envelopes and continuous response projection."""

from fractions import Fraction as F
from itertools import combinations

from common import require
from response_check import domain, pieces, projected_interval, response_partition


def baseline(knots, t):
    require(knots[0][0] <= t <= knots[-1][0], "baseline_no_extrapolation")
    for (a, va), (b, vb) in zip(knots, knots[1:]):
        if a <= t <= b:
            return va + (vb - va) * (t - a) / (b - a)
    raise AssertionError("baseline_segment")


def limits(observed, k, t):
    return max(v - k * abs(t - s) for s, v in observed), min(
        v + k * abs(t - s) for s, v in observed
    )


def feasible(observed, k):
    return all(abs(v - w) <= k * abs(t - s) for t, v in observed for s, w in observed)


def spline_piece(knots, middle):
    for (a, va), (b, vb) in zip(knots, knots[1:]):
        if a <= middle <= b:
            slope = (vb - va) / (b - a)
            return slope, va - slope * a
    raise AssertionError("spline_piece")


def error_bounds(observed, knots, k, tolerance):
    if not feasible(observed, k):
        return dict(status="inconsistent_premises")
    require(
        all(abs(vb - va) <= k * (b - a) for (a, va), (b, vb) in zip(knots, knots[1:])),
        "baseline_rate_premise",
    )
    low_error = max(abs(v - baseline(knots, t)) for t, v in observed)
    cuts = [t for t, _ in observed + knots]
    points = set()
    for a, b in pieces(knots[0][0], knots[-1][0], cuts):
        middle = (a + b) / 2
        lowers, uppers = {}, {}
        for t, value in observed:
            sign = F(1) if middle >= t else F(-1)
            slope, intercept = -k * sign, value + k * sign * t
            lowers[slope] = max(intercept, lowers.get(slope, intercept))
            slope, intercept = k * sign, value - k * sign * t
            uppers[slope] = min(intercept, uppers.get(slope, intercept))
        points.update((a, b))
        for lines in (lowers, uppers):
            for (s, c), (u, d) in combinations(lines.items(), 2):
                if s != u:
                    x = (d - c) / (s - u)
                    if a <= x <= b:
                        points.add(x)
    witnesses = []
    for t in sorted(points):
        lo, hi = limits(observed, k, t)
        b = baseline(knots, t)
        witnesses.extend(((b - lo, t, "lower", lo, b), (hi - b, t, "upper", hi, b)))
    value, t, side, signal, nominal = max(witnesses, key=lambda r: (r[0], -r[1], r[2]))
    return dict(
        status="supported"
        if value <= tolerance
        else "contradicted"
        if low_error > tolerance
        else "unresolved",
        uniform_error_range_mps=[str(low_error), str(value)],
        maximum_witness=dict(
            time_s=str(t),
            envelope=side,
            value_mps=str(signal),
            baseline_mps=str(nominal),
            absolute_error_mps=str(value),
        ),
        minimum_witness="min(max(baseline,lower_envelope),upper_envelope)",
    )


def next_index(observed, knots, k, available, times):
    ranked = []
    for i in available:
        t = times[i]
        lo, hi = limits(observed, k, t)
        b = baseline(knots, t)
        ranked.append((max(b - lo, hi - b), -i, i))
    return max(ranked)[2]


def response_plan(observed, knots, k, tolerance, q):
    require(feasible(observed, k), "conventional_feasibility")
    require(
        all(abs(v - baseline(knots, t)) <= tolerance for t, v in observed),
        "conventional_prior_satisfying_world",
    )
    require(
        all(abs(vb - va) <= k * (b - a) for (a, va), (b, vb) in zip(knots, knots[1:])),
        "baseline_rate_premise",
    )
    low, high = limits(observed, k, q)
    unsafe = []
    corners = [t for t, _ in observed + knots] + [q]
    for a, b in pieces(knots[0][0], knots[-1][0], corners):
        midpoint = (a + b) / 2
        bs, bi = spline_piece(knots, midpoint)
        signq = F(1) if midpoint >= q else F(-1)
        # Existence of one lower-envelope violation, with all lower cones below b-e.
        constraints = domain(a, b, low, high)
        for t, value in observed:
            sign = F(1) if midpoint >= t else F(-1)
            constraints.append(
                (-k * sign - bs, F(0), bi - tolerance - value - k * sign * t, True)
            )
        constraints.append(
            (-k * signq - bs, F(1), bi - tolerance - k * signq * q, True)
        )
        projected = projected_interval(constraints)
        if projected is not None:
            unsafe.append(projected)
        # Existence of one upper-envelope violation, with all upper cones above b+e.
        constraints = domain(a, b, low, high)
        for t, value in observed:
            sign = F(1) if midpoint >= t else F(-1)
            constraints.append(
                (bs - k * sign, F(0), value - k * sign * t - bi - tolerance, True)
            )
        constraints.append(
            (bs - k * signq, F(-1), -k * signq * q - bi - tolerance, True)
        )
        projected = projected_interval(constraints)
        if projected is not None:
            unsafe.append(projected)
    nominal = baseline(knots, q)
    a, b = max(low, nominal - tolerance), min(high, nominal + tolerance)
    safe = [(a, b, True, True)] if a <= b else []
    partition = response_partition(low, high, safe, unsafe)
    return dict(
        status="response_set_computed",
        feasible_responses=[str(low), str(high)],
        response_partition=partition,
        guaranteed_resolution=all(x["status"] != "unresolved" for x in partition),
        possible_statuses=sorted({x["status"] for x in partition}),
    )
