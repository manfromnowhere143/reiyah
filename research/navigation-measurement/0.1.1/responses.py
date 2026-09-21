"""Analytic complete response partition, using exact bad-time and safe-window sets."""

from fractions import Fraction as F

from common import keys, parse_case, rational, require
from envelope import solve


def parse_query(query):
    keys(query, ("id", "time_s", "error_mps", "clock_registration", "available"))
    from common import identifier

    identifier(query["id"])
    q, e = rational(query["time_s"]), rational(query["error_mps"])
    require(e >= 0 and type(query["available"]) is bool, "query_error_or_availability")
    require(
        query["clock_registration"] in (None, "same_recording_axis"), "query_clock_kind"
    )
    return q, e


def canonical_partition(low, high, boundaries, classify):
    knots = sorted(
        {low, high} | {x for x in boundaries if x is not None and low < x < high}
    )
    atoms = []
    for index, value in enumerate(knots):
        atoms.append([value, value, True, True, classify(value)])
        if index + 1 < len(knots):
            right = knots[index + 1]
            atoms.append([value, right, False, False, classify((value + right) / 2)])
    merged = []
    for lo, hi, lc, hc, state in atoms:
        if merged and merged[-1][4] == state:
            require(merged[-1][1] == lo and (merged[-1][3] or lc), "partition_gap")
            merged[-1][1], merged[-1][3] = hi, hc
        else:
            merged.append([lo, hi, lc, hc, state])
    return [
        dict(
            lower=str(lo), upper=str(hi), lower_closed=lc, upper_closed=hc, status=state
        )
        for lo, hi, lc, hc, state in merged
    ]


def bad_extremes(points, k, d, low, high):
    def lower(t):
        return max(lo - k * abs(t - s) for s, lo, _ in points)

    knots = {low, high}
    if k:
        for t, lo, _ in points:
            if lo >= d:
                radius = (lo - d) / k
                knots.update(x for x in (t - radius, t + radius) if low <= x <= high)
    ordered = sorted(knots)
    closure = {x for x in ordered if lower(x) < d}
    for a, b in zip(ordered, ordered[1:]):
        if lower((a + b) / 2) < d:
            closure.update((a, b))
    return [min(closure), max(closure)] if closure else None


def safe_windows(points, k, d, low, high, width):
    intervals = [(low, high)]
    for t, _, hi in points:
        if hi >= d:
            continue
        if k == 0:
            return []
        radius = (d - hi) / k
        cutlo, cuthi = t - radius - width, t + radius
        remaining = []
        for a, b in intervals:
            if b <= cutlo or a >= cuthi:
                remaining.append((a, b))
            else:
                if a <= cutlo:
                    remaining.append((a, cutlo))
                if cuthi <= b:
                    remaining.append((cuthi, b))
        intervals = remaining
    return intervals


def plan(case, query):
    q, e = parse_query(query)
    initial = solve(case)
    if initial["status"] in ("blocked", "inconsistent_premises"):
        return dict(
            status=initial["status"],
            response_partition=None,
            guaranteed_resolution=None,
        )
    if not query["available"] or query["clock_registration"] is None:
        return dict(
            status="acquisition_blocked",
            reason="unavailable" if not query["available"] else "unregistered_clock",
            response_partition=None,
            guaranteed_resolution=None,
        )
    a, b, d, k, tau, points, missing = parse_case(case)
    require(not missing, "missing_after_initial_solve")
    low = max(lo - k * abs(q - t) for t, lo, _ in points) - e
    high = min(hi + k * abs(q - t) for t, _, hi in points) + e
    bad = bad_extremes(points, k, d, a - tau, b + tau)
    windows = safe_windows(points, k, d, a - tau, a + tau, b - a)
    support = None if bad is None else d + e + k * max(abs(x - q) for x in bad)
    safe = (
        None
        if not windows
        else d
        - e
        - k * max(max(x - q, q - x - (b - a), F(0)) for pair in windows for x in pair)
    )

    def classify(y):
        yes = support is None or y >= support
        no = safe is None or y < safe
        require(not (yes and no), "conflicting_response_predicates")
        return "supported" if yes else "contradicted" if no else "unresolved"

    partition = canonical_partition(low, high, (support, safe), classify)
    return dict(
        status="response_set_computed",
        feasible_responses=[str(low), str(high)],
        response_partition=partition,
        guaranteed_resolution=all(row["status"] != "unresolved" for row in partition),
        possible_statuses=sorted({row["status"] for row in partition}),
    )


def response_status(plan_result, value):
    value = F(value)
    require(plan_result["status"] == "response_set_computed", "query_not_computed")
    found = []
    for row in plan_result["response_partition"]:
        lo, hi = F(row["lower"]), F(row["upper"])
        if (value > lo or (value == lo and row["lower_closed"])) and (
            value < hi or (value == hi and row["upper_closed"])
        ):
            found.append(row["status"])
    require(len(found) <= 1, "overlapping_partition")
    return found[0] if found else "inconsistent_premises"
