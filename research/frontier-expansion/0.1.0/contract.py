"""Exact merged-knot clearance calculation; offline authored research only."""
from format import Q, Invalid, rational, validate, digest, VERSION

def aligned(trace):
    shift = rational(trace["clock_shift"])
    return [(rational(t) + shift, rational(x)) for t, x in trace["samples"]]

def interpolate(points, t):
    for at, x in points:
        if at == t:
            return x
    for (a, x), (b, y) in zip(points, points[1:]):
        if a < t < b:
            return x + (y - x) * (t - a) / (b - a)
    raise Invalid("extrapolation")

def world_result(case, world):
    result = {"world_id": world["id"], "status": "blocked", "reason": "missing_bound_trace",
              "minimum_observed_gap": None, "minimum_at": None, "full_horizon": False}
    if world["ego"] is None or world["lead"] is None or world["actor_id"] is None:
        return result
    ego, lead = aligned(world["ego"]), aligned(world["lead"])
    start, end = map(rational, case["claim"]["window"])
    threshold = rational(case["claim"]["minimum_gap"])
    linear = case["model"]["interpolation"] == "piecewise_linear"
    lo, hi = max(start, ego[0][0], lead[0][0]), min(end, ego[-1][0], lead[-1][0])
    full = linear and lo == start and hi == end
    if linear:
        knots = sorted({lo, hi} | {t for t, _ in ego + lead if lo <= t <= hi}) if lo <= hi else []
    else:
        knots = sorted({t for t, _ in ego} & {t for t, _ in lead} & {t for t, _ in ego if start <= t <= end})
    if not knots:
        result.update(status="unresolved", reason="no_common_time")
        return result
    values = [(interpolate(lead, t) - interpolate(ego, t), t) for t in knots]
    gap, at = min(values)
    if gap < threshold:
        status, reason = "contradicted", "clearance_violation"
    elif full:
        status, reason = "supported", "complete_linear_horizon"
    else:
        status, reason = "unresolved", "interpolation_unqualified" if not linear else "partial_horizon"
    result.update(status=status, reason=reason, minimum_observed_gap=str(gap), minimum_at=str(at), full_horizon=full)
    return result

def aggregate(rows):
    statuses = {r["status"] for r in rows}
    if not rows:
        return "inconsistent_premises"
    if statuses == {"supported"}:
        return "supported"
    if statuses == {"contradicted"}:
        return "contradicted"
    if statuses == {"blocked"}:
        return "blocked"
    return "unresolved"

def evaluate(case):
    validate(case)
    rows = [world_result(case, w) for w in case["worlds"]]
    return {"schema_version": VERSION, "case_id": case["case_id"],
            "input_sha256": digest(case), "scope": "authored_conditional_clearance_only",
            "status": aggregate(rows), "worlds": rows,
            "safety": "not_assessed", "reasoning_grounding": "not_assessed"}
