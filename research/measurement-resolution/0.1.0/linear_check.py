"""Separate conventional LP vertex enumeration; imports no producer."""

from fractions import Fraction as F
from itertools import combinations
from common import parse_case, require, rational, keys


def vertices(inequalities):
    """a*x+b*z <= c; unbounded vertical side is harmless for chosen objective."""
    answer = set()
    for (a, b, c), (d, e, f) in combinations(inequalities, 2):
        det = a * e - b * d
        if det:
            x, z = (c * e - b * f) / det, (a * f - c * d) / det
            if all(p * x + q * z <= r for p, q, r in inequalities):
                answer.add((x, z))
    require(answer, "reference_empty_vertices")
    return answer


def lower_min(points, k, start, end):
    knots = sorted({start, end, *(t for t, _, _ in points if start <= t <= end)})
    if start == end:
        return max(lo - k * abs(start - t) for t, lo, _ in points)
    answers = []
    for left, right in zip(knots, knots[1:]):
        mid = (left + right) / 2
        constraints = [(F(-1), F(0), -left), (F(1), F(0), right)]
        for t, lo, _ in points:
            slope = k if mid < t else -k
            intercept = lo - slope * t
            constraints.append((slope, F(-1), -intercept))
        answers.extend(z for x, z in vertices(constraints))
    return min(answers)


def upper_best(points, k, start, end, width):
    if start == end:
        return min(
            hi
            + k
            * (
                start - t
                if t < start
                else t - start - width
                if t > start + width
                else F(0)
            )
            for t, _, hi in points
        )
    knots = sorted(
        {
            start,
            end,
            *(x for t, _, _ in points for x in (t - width, t) if start <= x <= end),
        }
    )
    answers = []
    for left, right in zip(knots, knots[1:]):
        mid = (left + right) / 2
        constraints = [(F(-1), F(0), -left), (F(1), F(0), right)]
        for t, _, hi in points:
            if mid < t - width:
                slope, intercept = -k, hi + k * (t - width)
            elif mid > t:
                slope, intercept = k, hi - k * t
            else:
                slope, intercept = F(0), hi
            constraints.append((-slope, F(1), intercept))
        answers.extend(z for x, z in vertices(constraints))
    return max(answers)


def solve(case):
    a, b, d, k, tau, points, missing = parse_case(case)
    if missing:
        return {"status": "blocked", "missing": missing}
    # Independent feasibility check: each interval intersects the propagated
    # lower requirements of every other interval. No vacuous success.
    for t, _, hi in points:
        if max(lo - k * abs(t - u) for u, lo, _ in points) > hi:
            return {"status": "inconsistent_premises"}
    lo = lower_min(points, k, a - tau, b + tau)
    hi = upper_best(points, k, a - tau, a + tau, b - a)
    return {
        "status": "supported"
        if lo >= d
        else "contradicted"
        if hi < d
        else "unresolved",
        "minimum_range_m": [str(lo), str(hi)],
    }


def check(case, result):
    expected = solve(case)
    require(type(result) is dict, "result_shape")
    base_keys = {"id", "physical_status", "scope", "status"}
    require(
        result.get("id") == case["id"]
        and result.get("physical_status") == "unresolved"
        and result.get("scope") == "authored_conditional_model",
        "result_scope",
    )
    require(result.get("status") == expected["status"], "result_status")
    a, b, d, k, tau, points, missing = parse_case(case)
    if missing:
        keys(result, base_keys | {"missing"})
        require(result["missing"] == missing, "result_missing")
        return
    if expected["status"] == "inconsistent_premises":
        keys(result, base_keys | {"conflicting_observations"})
        ids = result["conflicting_observations"]
        require(type(ids) is list and len(ids) == 2, "conflict_shape")
        rows = {row["id"]: p for row, p in zip(case["observations"], points)}
        require(all(i in rows for i in ids), "conflict_id")
        ti, li, _ = rows[ids[0]]
        tj, _, hj = rows[ids[1]]
        require(li > hj + k * abs(ti - tj), "conflict_not_real")
        return
    keys(
        result,
        base_keys
        | {
            "minimum_range_m",
            "lower_witness",
            "upper_witness",
            "extra_error_allowance_m",
            "distinguishing_observation",
        },
    )
    require(result["minimum_range_m"] == expected["minimum_range_m"], "result_extrema")
    low, high = map(F, expected["minimum_range_m"])
    for kind, target in (("lower", low), ("upper", high)):
        w = result[kind + "_witness"]
        keys(w, ("envelope", "offset_s", "time_s", "minimum_m"))
        require(w["envelope"] == kind, "witness_kind")
        delta, t, minimum = (
            rational(v, operand=False)
            for v in (w["offset_s"], w["time_s"], w["minimum_m"])
        )
        require(
            -tau <= delta <= tau and a <= t <= b and minimum == target, "witness_domain"
        )
        nominal = t - delta
        actual = (
            max(lo - k * abs(nominal - u) for u, lo, _ in points)
            if kind == "lower"
            else min(hi + k * abs(nominal - u) for u, _, hi in points)
        )
        require(actual == target, "witness_value")
        whole = (
            lower_min(points, k, a - delta, b - delta)
            if kind == "lower"
            else upper_best(points, k, a - delta, a - delta, b - a)
        )
        require(whole == target, "witness_whole_horizon")
    require(
        result["extra_error_allowance_m"]
        == {
            "support_inclusive": str(low - d) if low >= d else None,
            "contradiction_strict": str(d - high) if high < d else None,
        },
        "error_allowance",
    )
    query = result["distinguishing_observation"]
    if expected["status"] != "unresolved":
        require(query is None, "spurious_query")
        return
    keys(
        query,
        (
            "physical_time_s",
            "lower_world_m",
            "upper_world_m",
            "absolute_error_strictly_below_m",
            "scope",
        ),
    )
    require(
        query["scope"]
        == "distinguishes_this_pair_only; requires_registered_measurement_clock",
        "query_scope",
    )
    t, lo, hi, eps = (
        rational(v, operand=False)
        for v in (
            query["physical_time_s"],
            query["lower_world_m"],
            query["upper_world_m"],
            query["absolute_error_strictly_below_m"],
        )
    )
    require(a <= t <= b and lo < d <= hi and eps == (hi - lo) / 2, "query_separation")
    dl, du = (
        F(result["lower_witness"]["offset_s"]),
        F(result["upper_witness"]["offset_s"]),
    )
    require(
        lo == max(lower - k * abs(t - dl - u) for u, lower, _ in points),
        "query_lower_world",
    )
    require(
        hi == min(h + k * abs(t - du - u) for u, _, h in points), "query_upper_world"
    )
