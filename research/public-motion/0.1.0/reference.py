"""Separate conventional row join and arithmetic; imports no producer."""
from fractions import Fraction
from common import require, validate

def evaluate_reference(seeds, rows):
    validate(seeds, rows)  # Shared shape gate, no selection, join or result arithmetic.
    first = {}
    for seed in seeds:
        first.setdefault(seed["vehicle_id"], seed)
    chosen = list(first.values())[:8]
    require(len(chosen) == 8, "insufficient_selected_identities")
    window_low = min(int(s["global_time"]) for s in chosen)
    window_high = max(int(s["global_time"]) for s in chosen)+2000
    require(window_high-window_low <= 10000, "query_time_span")
    wanted = {s[field] for s in chosen for field in ("vehicle_id", "preceding")}
    tuples = [(r["vehicle_id"], int(r["global_time"])) for r in rows]
    require(len(tuples) == len(set(tuples)), "duplicate_identity_time")
    require(all(r["vehicle_id"] in wanted and window_low <= int(r["global_time"]) <= window_high for r in rows), "query_membership")
    results = []
    for ordinal, seed in enumerate(chosen, 1):
        start = int(seed["global_time"])
        ego_rows = [r for r in rows if r["vehicle_id"] == seed["vehicle_id"] and start <= int(r["global_time"]) <= start+2000]
        lead_rows = [r for r in rows if r["vehicle_id"] == seed["preceding"] and start <= int(r["global_time"]) <= start+2000]
        faults, matched = set(), []
        for offset in range(21):
            at = start + offset*100
            left = [r for r in ego_rows if int(r["global_time"]) == at]
            right = [r for r in lead_rows if int(r["global_time"]) == at]
            if not left or not right:
                faults.add("missing_expected_frame")
                continue
            e, l = left[0], right[0]
            matched.append((offset, e, l))
            if int(e["frame_id"]) != int(seed["frame_id"])+offset or int(l["frame_id"]) != int(e["frame_id"]):
                faults.add("clock_frame_mismatch")
            if e["preceding"] != seed["preceding"]:
                faults.add("lead_binding_changed")
            if not (e["lane_id"] == l["lane_id"] == seed["lane_id"]) or seed["lane_id"] == "0":
                faults.add("lane_binding_changed")
            if e["vehicle_id"] == l["vehicle_id"]:
                faults.add("self_lead")
        if any((int(r["global_time"])-start) % 100 for r in ego_rows+lead_rows):
            faults.add("off_grid_frame")
        if any(len({Fraction(item[pos]["v_length"]) for item in matched})>1 for pos in (1, 2)):
            faults.add("length_changes")
        ok = not faults and len(matched) == 21
        minimum = None
        residual = None
        if ok:
            values = []
            residual_values = []
            for offset, ego, lead in matched:
                difference_feet = Fraction(lead["local_y"])-Fraction(ego["local_y"])-Fraction(lead["v_length"])
                values.append((difference_feet*Fraction(3048,10000), Fraction(offset,10)))
                residual_values.append(abs(Fraction(lead["local_y"])-Fraction(ego["local_y"])-Fraction(ego["space_headway"])))
            minimum = sorted(values)[0]
            residual = max(residual_values)
        results.append({
            "case_id": "PM"+str(ordinal).zfill(2),
            "qualification": "admitted_annotation_only" if ok else "unresolved_source_binding",
            "reasons": sorted(faults), "paired_samples": len(matched),
            "recorded_sample_obligation": ("contradicted" if minimum[0] < 5 else "supported") if ok else "not_evaluated",
            "minimum_proxy_metres": str(minimum[0]) if ok else None,
            "minimum_at_relative_seconds": str(minimum[1]) if ok else None,
            "margin_above_five_metres": str(minimum[0]-5) if ok else None,
            "front_headway_max_residual_feet": str(residual) if ok else None,
            "physical_continuous_clearance": "unresolved",
            "physical_missing": ["calibrated_position_and_dimension_bounds", "common_clock_error_bounds", "projected_bumper_geometry", "intersample_motion_bounds"],
            "safety": "not_assessed"
        })
    return results
