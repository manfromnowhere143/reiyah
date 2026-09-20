"""Conventional segment-pair checker; imports no production evaluator."""
from fractions import Fraction as F
from format import validate, digest, VERSION, Invalid

def reference_world(case, w):
    row = {"world_id": w["id"], "status": "blocked", "reason": "missing_bound_trace",
           "minimum_observed_gap": None, "minimum_at": None, "full_horizon": False}
    if w["ego"] is None or w["lead"] is None or w["actor_id"] is None:
        return row
    traces = []
    for role in ("ego", "lead"):
        tr = w[role]
        traces.append([(F(t) + F(tr["clock_shift"]), F(x)) for t, x in tr["samples"]])
    a, b = traces
    start, end = [F(x) for x in case["claim"]["window"]]
    pairs = []
    full = False
    linear = case["model"]["interpolation"] == "piecewise_linear"
    if linear:
        # Each degenerate segment retains a lone sample. Each nondegenerate
        # overlap has affine gap; its minimum is attained at an endpoint.
        def pieces(points):
            return list(zip(points, points[1:])) if len(points) > 1 else [(points[0], points[0])]
        for (t0, x0), (t1, x1) in pieces(a):
            for (u0, y0), (u1, y1) in pieces(b):
                left, right = max(t0, u0, start), min(t1, u1, end)
                if left > right:
                    continue
                for at in (left, right):
                    x = x0 if t0 == t1 else ((t1-at)*x0+(at-t0)*x1)/(t1-t0)
                    y = y0 if u0 == u1 else ((u1-at)*y0+(at-u0)*y1)/(u1-u0)
                    pairs.append((y-x, at))
        full = a[0][0] <= start and b[0][0] <= start and a[-1][0] >= end and b[-1][0] >= end
    else:
        for t, x in a:
            for u, y in b:
                if t == u and start <= t <= end:
                    pairs.append((y-x, t))
    if not pairs:
        row.update(status="unresolved", reason="no_common_time")
        return row
    gap, when = sorted(pairs)[0]
    row["minimum_observed_gap"], row["minimum_at"], row["full_horizon"] = str(gap), str(when), full
    if gap < F(case["claim"]["minimum_gap"]):
        row.update(status="contradicted", reason="clearance_violation")
    elif full:
        row.update(status="supported", reason="complete_linear_horizon")
    else:
        row.update(status="unresolved", reason="partial_horizon" if linear else "interpolation_unqualified")
    return row

def reference(case):
    validate(case)  # Shared format gate only; arithmetic and reduction separate.
    rows = [reference_world(case, w) for w in case["worlds"]]
    if len(rows) == 0:
        status = "inconsistent_premises"
    elif all(r["status"] == "supported" for r in rows):
        status = "supported"
    elif all(r["status"] == "contradicted" for r in rows):
        status = "contradicted"
    elif all(r["status"] == "blocked" for r in rows):
        status = "blocked"
    else:
        status = "unresolved"
    return {"schema_version": VERSION, "case_id": case["case_id"],
            "input_sha256": digest(case), "scope": "authored_conditional_clearance_only",
            "status": status, "worlds": rows, "safety": "not_assessed", "reasoning_grounding": "not_assessed"}

def verify(case, result):
    expected = reference(case)
    if result != expected:
        raise Invalid("result_mismatch")
    return expected

if __name__ == "__main__":
    import argparse, json
    from pathlib import Path
    from format import load_json
    from binding import verify_freeze
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    freeze = verify_freeze(root)
    allocation = load_json(root/"allocation.json")
    result = load_json(args.results)
    assert result["allocation_sha256"] == digest(allocation)
    assert result["freeze_sha256"] == freeze
    assert set(result) == {"document_id","version","freeze_sha256","allocation_sha256","cases"}
    assert result["document_id"] == "reiyah.frontier-expansion.results" and result["version"] == VERSION
    assert len(result["cases"]) == len(allocation["cases"])
    for entry, output in zip(allocation["cases"], result["cases"]):
        verify(entry["case"], output)
        assert output["status"] == entry["expected"]
    summary = {"document_id":"reiyah.frontier-expansion.verification","version":VERSION,
               "freeze_sha256":freeze,"results_sha256":digest(result),"cases_checked":len(result["cases"]),
               "all_equal_to_conventional":True,"checker":"separate segment-pair arithmetic; shared format gate",
               "independent_replication":False}
    Path(args.output).write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary))
