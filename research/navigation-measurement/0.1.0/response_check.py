"""Independent all-response verification via exact strict polyhedron projection."""

from fractions import Fraction as F
from itertools import combinations

from common import keys, parse_case, rational, require
from linear_check import solve


def projected_interval(constraints):
    """Each row (a,b,c,strict) means a*time+b*reply <= c, or < c."""
    vertices = set()
    for one, two in combinations(constraints, 2):
        a, b, c, _ = one
        d, e, f, _ = two
        determinant = a * e - b * d
        if determinant:
            x, y = (c * e - b * f) / determinant, (a * f - c * d) / determinant
            if all(u * x + v * y <= w for u, v, w, _ in constraints):
                vertices.add((x, y))
    if not vertices:
        return None

    def strict_feasible(points):
        x = sum(p[0] for p in points) / len(points)
        y = sum(p[1] for p in points) / len(points)
        return all(
            a * x + b * y < c if strict else a * x + b * y <= c
            for a, b, c, strict in constraints
        )

    if not strict_feasible(vertices):
        return None
    low, high = min(y for _, y in vertices), max(y for _, y in vertices)
    return (
        low,
        high,
        strict_feasible([p for p in vertices if p[1] == low]),
        strict_feasible([p for p in vertices if p[1] == high]),
    )


def pieces(low, high, corners):
    knots = sorted({low, high} | {x for x in corners if low <= x <= high})
    return list(zip(knots, knots[1:])) if len(knots) > 1 else [(low, high)]


def domain(lo, hi, ylo, yhi):
    return [
        (F(-1), F(0), -lo, False),
        (F(1), F(0), hi, False),
        (F(0), F(-1), -ylo, False),
        (F(0), F(1), yhi, False),
    ]


def member(value, intervals):
    return any(
        (value > lo or (value == lo and lc)) and (value < hi or (value == hi and hc))
        for lo, hi, lc, hc in intervals
    )


def response_partition(low, high, safe, unsafe):
    coordinates = sorted({low, high} | {r[i] for r in safe + unsafe for i in (0, 1)})
    atoms = []
    for i, left in enumerate(coordinates):
        atoms.append((left, left, True, True, left))
        if i + 1 < len(coordinates):
            right = coordinates[i + 1]
            atoms.append((left, right, False, False, (left + right) / 2))
    rows = []
    for left, right, lc, hc, probe in atoms:
        s, u = member(probe, safe), member(probe, unsafe)
        require(s or u, "reference_uncovered_response")
        state = "unresolved" if s and u else "supported" if s else "contradicted"
        row = dict(
            lower=str(left),
            upper=str(right),
            lower_closed=lc,
            upper_closed=hc,
            status=state,
        )
        if rows and rows[-1]["status"] == state:
            require(
                rows[-1]["upper"] == row["lower"] and (rows[-1]["upper_closed"] or lc),
                "reference_partition_gap",
            )
            rows[-1].update(upper=str(right), upper_closed=hc)
        else:
            rows.append(row)
    return rows


def plan(case, query):
    keys(query, ("id", "time_s", "error_mps", "clock_registration", "available"))
    from common import identifier

    identifier(query["id"])
    q = rational(query["time_s"])
    error = rational(query["error_mps"])
    require(error >= 0 and type(query["available"]) is bool, "reference_query")
    require(
        query["clock_registration"] in (None, "same_recording_axis"),
        "reference_clock_kind",
    )
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
    require(not missing, "reference_missing")
    ylo = max(v - k * abs(t - q) for t, v, _ in points) - error
    yhi = min(v + k * abs(t - q) for t, _, v in points) + error
    safe, unsafe = [], []
    for left, right in pieces(a - tau, b + tau, [q] + [t for t, _, _ in points]):
        mid = (left + right) / 2
        constraints = domain(left, right, ylo, yhi)
        for t, lo, _ in points:
            slope = k if mid < t else -k
            intercept = lo - slope * t
            constraints.append((slope, F(0), d - intercept, True))
        slope = k if mid < q else -k
        constraints.append((slope, F(1), d + error + slope * q, True))
        projection = projected_interval(constraints)
        if projection is not None:
            unsafe.append(projection)
    width = b - a
    times = [t for t, _, _ in points] + [q]
    for left, right in pieces(
        a - tau, a + tau, [x for t in times for x in (t, t - width)]
    ):
        mid = (left + right) / 2
        constraints = domain(left, right, ylo, yhi)

        def distance_line(t):
            if mid < t - width:
                return -k, k * (t - width)
            if mid > t:
                return k, -k * t
            return F(0), F(0)

        for t, _, hi in points:
            slope, intercept = distance_line(t)
            constraints.append((-slope, F(0), hi + intercept - d, False))
        slope, intercept = distance_line(q)
        constraints.append((-slope, F(-1), error + intercept - d, False))
        projection = projected_interval(constraints)
        if projection is not None:
            safe.append(projection)
    partition = response_partition(ylo, yhi, safe, unsafe)
    return dict(
        status="response_set_computed",
        feasible_responses=[str(ylo), str(yhi)],
        response_partition=partition,
        guaranteed_resolution=not any(p["status"] == "unresolved" for p in partition),
        possible_statuses=sorted({p["status"] for p in partition}),
    )


def verify(case, query, actual):
    require(actual == plan(case, query), "response_partition_mismatch")
