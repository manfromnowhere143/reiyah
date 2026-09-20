"""Interpret recorded longitudinal proxies; never promote them to physical truth."""
from fractions import Fraction as F
from common import integer, number, require, validate

FOOT = F(381, 1250)
THRESHOLD = F(5)

def allocate(seeds):
    anchors = []
    seen = set()
    for seed in seeds:
        if seed["vehicle_id"] not in seen:
            anchors.append(seed)
            seen.add(seed["vehicle_id"])
        if len(anchors) == 8:
            break
    require(len(anchors) == 8, "insufficient_selected_identities")
    return anchors

def evaluate(seeds, rows):
    validate(seeds, rows)
    anchors = allocate(seeds)
    begin = min(integer(a["global_time"]) for a in anchors)
    end = max(integer(a["global_time"]) for a in anchors) + 2000
    require(end - begin <= 10000, "query_time_span")
    ids = {a[k] for a in anchors for k in ("vehicle_id", "preceding")}
    index = {}
    for row in rows:
        require(row["vehicle_id"] in ids and begin <= integer(row["global_time"]) <= end, "query_membership")
        key = row["vehicle_id"], integer(row["global_time"])
        require(key not in index, "duplicate_identity_time")
        index[key] = row
    output = []
    for i, anchor in enumerate(anchors):
        t0 = integer(anchor["global_time"])
        times = range(t0, t0+2001, 100)
        reasons = set()
        gaps, residuals = [], []
        lengths = {"ego": set(), "lead": set()}
        for at in times:
            ego = index.get((anchor["vehicle_id"], at))
            lead = index.get((anchor["preceding"], at))
            if ego is None or lead is None:
                reasons.add("missing_expected_frame")
                continue
            if integer(ego["frame_id"]) != integer(anchor["frame_id"]) + (at-t0)//100 or ego["frame_id"] != lead["frame_id"]:
                reasons.add("clock_frame_mismatch")
            if ego["preceding"] != anchor["preceding"]:
                reasons.add("lead_binding_changed")
            if ego["lane_id"] != anchor["lane_id"] or lead["lane_id"] != anchor["lane_id"] or integer(anchor["lane_id"]) == 0:
                reasons.add("lane_binding_changed")
            if ego["vehicle_id"] == lead["vehicle_id"]:
                reasons.add("self_lead")
            for role, row in (("ego", ego), ("lead", lead)):
                lengths[role].add(number(row["v_length"]))
            rear_proxy = (number(lead["local_y"]) - number(lead["v_length"])) * FOOT
            front_proxy = number(ego["local_y"]) * FOOT
            gaps.append((rear_proxy-front_proxy, F(at-t0, 1000)))
            residuals.append(abs(number(lead["local_y"])-number(ego["local_y"])-number(ego["space_headway"])))
        if any(len(values)>1 for values in lengths.values()):
            reasons.add("length_changes")
        for actor in (anchor["vehicle_id"], anchor["preceding"]):
            if any(t0 <= at <= t0+2000 and (at-t0) % 100 for ident, at in index if ident == actor):
                reasons.add("off_grid_frame")
        qualified = not reasons and len(gaps) == 21
        minimum = min(gaps) if qualified else None
        output.append({
            "case_id": f"PM{i+1:02d}",
            "qualification": "admitted_annotation_only" if qualified else "unresolved_source_binding",
            "reasons": sorted(reasons), "paired_samples": len(gaps),
            "recorded_sample_obligation": ("supported" if minimum[0] >= THRESHOLD else "contradicted") if qualified else "not_evaluated",
            "minimum_proxy_metres": str(minimum[0]) if qualified else None,
            "minimum_at_relative_seconds": str(minimum[1]) if qualified else None,
            "margin_above_five_metres": str(minimum[0]-THRESHOLD) if qualified else None,
            "front_headway_max_residual_feet": str(max(residuals)) if qualified else None,
            "physical_continuous_clearance": "unresolved",
            "physical_missing": ["calibrated_position_and_dimension_bounds", "common_clock_error_bounds", "projected_bumper_geometry", "intersample_motion_bounds"],
            "safety": "not_assessed"
        })
    return output
