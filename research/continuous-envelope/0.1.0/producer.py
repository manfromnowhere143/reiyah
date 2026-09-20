"""Exact cone/intersection implementation of the frozen scalar contract."""

from fractions import Fraction as F
from itertools import combinations
from common import parse_case


def solve(case):
    a, b, d, k, tau, points, missing = parse_case(case)
    out = {
        "id": case["id"],
        "physical_status": "unresolved",
        "scope": "authored_conditional_model",
    }
    if missing:
        return dict(out, status="blocked", missing=missing)
    for i, (ti, li, _) in enumerate(points):
        for j, (tj, _, hj) in enumerate(points):
            if li > hj + k * abs(ti - tj):
                return dict(
                    out,
                    status="inconsistent_premises",
                    conflicting_observations=[
                        case["observations"][i]["id"],
                        case["observations"][j]["id"],
                    ],
                )

    def lower(s):
        return max(lo - k * abs(s - t) for t, lo, hi in points)

    def upper(s):
        return min(hi + k * abs(s - t) for t, lo, hi in points)

    candidates = {a - tau, b + tau}
    candidates.update(t for t, _, _ in points if a - tau <= t <= b + tau)
    if k:
        for ti, li, _ in points:
            for tj, lj, _ in points:
                t = (li - lj + k * (ti + tj)) / (2 * k)
                if a - tau <= t <= b + tau:
                    candidates.add(t)
    low, low_s = min((lower(s), s) for s in candidates)
    low_delta = max(-tau, a - low_s)

    width = b - a
    left, right = a - tau, a + tau
    starts = {left, right}
    lines = []
    for t, _, hi in points:
        starts.update(x for x in (t - width, t) if left <= x <= right)
        lines.extend(((-k, hi + k * (t - width)), (F(0), hi), (k, hi - k * t)))
    for (m, c), (n, z) in combinations(lines, 2):
        if m != n:
            x = (z - c) / (m - n)
            if left <= x <= right:
                starts.add(x)

    def window_upper(x):
        return min(hi + k * max(x - t, t - (x + width), F(0)) for t, _, hi in points)

    high = max(window_upper(x) for x in starts)
    best_x = min(x for x in starts if window_upper(x) == high)
    high_delta = a - best_x
    upper_times = {best_x, best_x + width}
    upper_times.update(t for t, _, _ in points if best_x <= t <= best_x + width)
    high_s = min(s for s in upper_times if upper(s) == high)
    status = "supported" if low >= d else "contradicted" if high < d else "unresolved"
    out.update(
        status=status,
        minimum_range_m=[str(low), str(high)],
        lower_witness={
            "envelope": "lower",
            "offset_s": str(low_delta),
            "time_s": str(low_s + low_delta),
            "minimum_m": str(low),
        },
        upper_witness={
            "envelope": "upper",
            "offset_s": str(high_delta),
            "time_s": str(high_s + high_delta),
            "minimum_m": str(high),
        },
        extra_error_allowance_m={
            "support_inclusive": str(low - d) if low >= d else None,
            "contradiction_strict": str(d - high) if high < d else None,
        },
        distinguishing_observation=None,
    )
    if status == "unresolved":
        time = low_s + low_delta
        safe_value = upper(time - high_delta)
        out["distinguishing_observation"] = {
            "physical_time_s": str(time),
            "lower_world_m": str(low),
            "upper_world_m": str(safe_value),
            "absolute_error_strictly_below_m": str((safe_value - low) / 2),
            "scope": "distinguishes_this_pair_only; requires_registered_measurement_clock",
        }
    return out
