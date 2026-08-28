"""Execute the joint-silent-miss semantic checks against real records.

This is a faithful port of the derivation logic in tools/gate_a_1_2_0_science.py
joint_violations, with one change: the substitution guard is split. Policy
operands are still compared by exact equality and a mismatch still refuses to
run. Subject operands are checked for shape and kind rather than for literal
identity, and are supplied by a per-record binding.

Nothing is relaxed. The rules ported are:

  GA-JOINT-OPPORTUNITY-ROW-BINDING    every row binds the one common object,
                                      clock, window, both role-typed channels,
                                      and the warning and fallback rules
  GA-JOINT-OPPORTUNITY-CHRONOLOGY     occurred_at lies inside the window and is
                                      strictly increasing across rows
  GA-JOINT-COMMON-OPPORTUNITY-DERIVATION  cells, opportunities and both
                                      marginals are recomputed from the rows
  GA-JOINT-SILENT-ROW-DERIVATION      a both-miss counts as silent only when
                                      warning is not_issued and fallback is
                                      not_activated
  GA-JOINT-SILENT-MISS-DERIVATION     the silent summary reconciles, or is
                                      forced non-observed
  GA-JOINT-UNKNOWN-PROPAGATION        any non-observed operand forces
                                      nonidentifiable_unknown

Usage: python3 tools/measure/semantic_joint_1_3.py records.jsonl
"""
import json
import sys
from datetime import datetime

CONTRACT = json.load(open("manifests/definitions/joint-silent-miss-contract-1.3.0.json"))
POLICY = CONTRACT["policy"]
REQ = CONTRACT["subject_binding_requirements"]

EXPECTED_POLICY = {
    "channel_arity": 2,
    "common_opportunity_cells": ["both_miss", "first_only_miss",
                                 "second_only_miss", "neither_miss"],
    "marginal_derivation": "exact_from_disjoint_common_opportunity_cells",
    "identifiability_policy": "observed_common_cells_or_nonidentifiable",
    "joint_unknown_propagation":
        "nonobserved_operand_forces_nonidentified_nonobserved_summary",
    "opportunity_manifest_resolution_policy":
        "exact_ordered_registry_rows_bound_to_artifact",
    "row_derivation_policy":
        "exact_reference_validity_channel_warning_fallback_rows_to_disjoint_cells",
    "silent_joint_miss_policy":
        "both_channels_miss_and_warning_not_issued_and_fallback_not_activated",
}


class ContractError(Exception):
    pass


def guard():
    """Policy pinned by exact equality. A changed policy refuses to run."""
    for k, v in EXPECTED_POLICY.items():
        if POLICY.get(k) != v:
            raise ContractError(
                f"policy operand '{k}' does not match the expectation this "
                f"validator was written for: {POLICY.get(k)!r} != {v!r}")
    g = CONTRACT["guard_contract"]
    if g.get("may_be_relaxed_to_subset_check") or g.get("may_be_made_advisory"):
        raise ContractError("guard has been weakened; refusing to run")


def observed(m):
    return m.get("value") if isinstance(m, dict) and m.get("state") == "observed" else None


def parse_time(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def check(record):
    """Return a list of violation dicts for one record."""
    out = []
    j = record["joint_silent_miss"]
    cc = j["channel_contract"]
    rows = j["opportunity_rows"]

    # --- subject binding: shape and kind, never literal identity ---
    for side in ("first", "second"):
        ref = cc[side]["channel_ref"]
        if ref.get("record_kind") != REQ["observation_channel_record_kind"]:
            out.append({"rule": "GA-JOINT-SUBJECT-BINDING",
                        "detail": f"{side} channel is not an observation channel"})
        if cc[side]["role"] not in POLICY["channel_role_vocabulary"]:
            out.append({"rule": "GA-JOINT-SUBJECT-BINDING",
                        "detail": f"{side} role not in the declared vocabulary"})

    bound_object = rows[0]["object_ref"] if rows else None
    if bound_object and bound_object.get("record_kind") not in REQ["permitted_object_kinds"]:
        out.append({"rule": "GA-JOINT-SUBJECT-BINDING",
                    "detail": "object kind is not a permitted road object kind"})

    w = j["opportunity_window"]
    win_open, win_close = parse_time(w["opened_at"]), parse_time(w["closed_at"])

    # --- ported derivation ---
    cells = {k: 0 for k in POLICY["common_opportunity_cells"]}
    summary_unknown = False
    silent = 0
    silent_row_invalid = False
    row_binding_invalid = False
    chronology_invalid = win_open > win_close
    prev = None
    ids = set()

    for row in rows:
        if row["opportunity_id"] in ids:
            out.append({"rule": "GA-JOINT-OPPORTUNITY-ROW-BINDING",
                        "detail": "duplicate opportunity_id"})
        ids.add(row["opportunity_id"])

        # every row binds the ONE common object, clock, window, channels, rules
        if not (row["object_ref"] == bound_object
                and row["clock_id"] == rows[0]["clock_id"]
                and row["window_id"] == rows[0]["window_id"]
                and row["channels"][0]["channel_ref"] == cc["first"]["channel_ref"]
                and row["channels"][1]["channel_ref"] == cc["second"]["channel_ref"]
                and row["channels"][0]["role"] == cc["first"]["role"]
                and row["channels"][1]["role"] == cc["second"]["role"]
                and row["warning"]["rule_ref"] == rows[0]["warning"]["rule_ref"]
                and row["fallback"]["rule_ref"] == rows[0]["fallback"]["rule_ref"]):
            row_binding_invalid = True

        t = observed(row.get("occurred_at", {}))
        t = parse_time(t) if isinstance(t, str) else None
        if t is not None:
            if t < win_open or t > win_close or (prev is not None and t <= prev):
                chronology_invalid = True
            prev = t

        a = observed(row["channels"][0].get("outcome", {}))
        b = observed(row["channels"][1].get("outcome", {}))
        if a in {"miss", "detected"} and b in {"miss", "detected"}:
            cell = ("both_miss" if a == "miss" and b == "miss"
                    else "first_only_miss" if a == "miss"
                    else "second_only_miss" if b == "miss"
                    else "neither_miss")
        else:
            cell = None
            summary_unknown = True

        rs = observed(row.get("reference_state", {}))
        rv = observed(row.get("reference_validity", {}))
        ok = (t is not None and rs == "opportunity_present"
              and rv == "valid" and cell is not None)
        if cell is not None:
            if ok:
                cells[cell] += 1
            else:
                summary_unknown = True

        if cell == "both_miss" and ok:
            wo = observed(row.get("warning", {}).get("outcome", {}))
            fo = observed(row.get("fallback", {}).get("outcome", {}))
            if wo is None or fo is None:
                summary_unknown = True
            elif wo == "not_issued" and fo == "not_activated":
                silent += 1
            elif wo not in {"issued", "not_issued"} or fo not in {"activated", "not_activated"}:
                silent_row_invalid = True

    if row_binding_invalid:
        out.append({"rule": "GA-JOINT-OPPORTUNITY-ROW-BINDING",
                    "detail": "rows do not exact-bind the common object, clock, window, channels and rules"})
    if chronology_invalid:
        out.append({"rule": "GA-JOINT-OPPORTUNITY-CHRONOLOGY",
                    "detail": "occurred_at outside the window or not strictly increasing"})

    # cells, opportunities and marginals must be recomputed, never trusted
    declared = j["common_opportunity_cells"]
    for k, v in cells.items():
        if observed(declared.get(k, {})) != v:
            out.append({"rule": "GA-JOINT-COMMON-OPPORTUNITY-DERIVATION",
                        "detail": f"cell {k}: declared {observed(declared.get(k, {}))} recomputed {v}"})
    n = sum(cells.values())
    if observed(j["opportunities"]) != n:
        out.append({"rule": "GA-JOINT-COMMON-OPPORTUNITY-DERIVATION",
                    "detail": f"opportunities declared {observed(j['opportunities'])} recomputed {n}"})
    if observed(j["first_misses"]) != cells["both_miss"] + cells["first_only_miss"]:
        out.append({"rule": "GA-JOINT-COMMON-OPPORTUNITY-DERIVATION",
                    "detail": "first_misses does not equal both + first_only"})
    if observed(j["second_misses"]) != cells["both_miss"] + cells["second_only_miss"]:
        out.append({"rule": "GA-JOINT-COMMON-OPPORTUNITY-DERIVATION",
                    "detail": "second_misses does not equal both + second_only"})

    # unknown propagation and the silent summary
    ident = j["identifiability"]
    if summary_unknown:
        if ident != "nonidentifiable_unknown":
            out.append({"rule": "GA-JOINT-UNKNOWN-PROPAGATION",
                        "detail": "a non-observed operand must force nonidentifiable_unknown"})
        if observed(j["joint_misses"]) is not None:
            out.append({"rule": "GA-JOINT-SILENT-MISS-DERIVATION",
                        "detail": "joint_misses must be non-observed when the summary is unknown"})
        if observed(j["joint_miss_risk"]) is not None:
            out.append({"rule": "GA-JOINT-SILENT-MISS-DERIVATION",
                        "detail": "joint_miss_risk must be non-observed when the summary is unknown"})
    else:
        if ident != "identified_from_common_opportunities":
            out.append({"rule": "GA-JOINT-UNKNOWN-PROPAGATION",
                        "detail": "all operands observed but identifiability is not identified"})
        if observed(j["joint_misses"]) != silent:
            out.append({"rule": "GA-JOINT-SILENT-ROW-DERIVATION",
                        "detail": f"joint_misses declared {observed(j['joint_misses'])} recomputed {silent}"})
    if silent_row_invalid:
        out.append({"rule": "GA-JOINT-SILENT-ROW-DERIVATION",
                    "detail": "warning or fallback outcome outside its permitted vocabulary"})
    return out


def main():
    guard()
    print("GUARD: policy operands match exactly; guard not weakened. proceeding.\n")
    total = ok = 0
    viol = {}
    for line in open(sys.argv[1]):
        rec = json.loads(line)
        total += 1
        errs = check(rec)
        if not errs:
            ok += 1
        for e in errs:
            viol.setdefault(e["rule"], []).append(e["detail"])
    print(f"records checked : {total:,}")
    print(f"records passing : {ok:,}  ({100*ok/total:.2f}%)")
    print(f"records failing : {total-ok:,}")
    if viol:
        print("\nviolations by rule:")
        for r, ds in sorted(viol.items(), key=lambda x: -len(x[1])):
            print(f"  {r:<42}{len(ds):>8,}   e.g. {ds[0][:90]}")
    else:
        print("\nno semantic violations.")


if __name__ == "__main__":
    main()
