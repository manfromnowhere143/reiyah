"""Build worst_group_evaluation records from measured data, and exercise the unknown rule.

`GATE_B_SESSION_HANDOFF.md` section 10 item 3: run `worst_group_evaluation` on real data,
"now that vulnerable road users are representable", and note that "the unknown-group rule
has never been exercised against anything real". Results I, J and L computed worst-group
statistics, but none of them produced a schema-valid record of this kind, and in every one
the unknown set was empty. The branch of the contract that matters most has therefore
never fired.

It fires here, and it fires on a real gap in the data rather than a manufactured one.

## Two records

**Record A, groups by object class.** Every ground-truth object carries an annotated
class, so membership is observed for all ten groups. Expected disposition: `identified`.

**Record B, groups by motion state.** Motion is derived from the ground-truth track:
displacement over elapsed time, thresholded at 1 m/s. A track observed in fewer than two
keyframes has no displacement over time, so its motion state is not derivable. There are
315 such tracks out of 8,976, and 67 of them are vulnerable road users.

The naive move is to drop those 315 and report a confident worst group over the remaining
8,661. The contract forbids it: an object whose group membership cannot be determined is
`unknown`, and any unknown group makes the overall result unknown. Expected disposition:
`unknown`, with no extremum reported.

That is the whole point. A system that answers here is worse than one that refuses,
because the refusal is the true statement.

## Metric

The per-group joint-failure lift between Mapillary and Megvii at score `>= 0.3`, the same
estimand as Results I and J. `direction` is `lower_is_better`: a lift near 1 means the two
channels fail independently, which is what a redundancy argument wants. The worst group is
therefore the maximum.

Eligibility uses the schema's `minimumInformationRule` with all four operands, evaluated
with operator `all`, and each group's effective sample size is its count of distinct
tracked instances rather than its box count, per Audit 1.

Usage:
  python3 tools/measure/build_worst_group_records.py gt_val_cache.json \
      matched_mapillary.json matched_megvii.json worst_group_records.jsonl
"""

import json
import math
import sys

THR = 0.3
MOVING_MPS = 1.0
SAMPLE_COUNT_MIN = 30
COVERAGE_FRACTION_MIN = 0.95
ESS_MIN = 20.0
INTERVAL_WIDTH_MAX = 10.0

SCHEMA_ID = "https://schemas.reiyah.invalid/scientific-contract/1.3.0/joint-performance-evaluation.schema.json"
VRU = {"pedestrian", "bicycle", "motorcycle"}


def flatten(raw):
    flat = {}
    for _c, m in raw.items():
        for k, v in m.items():
            flat[int(k)] = v
    return flat


def observed_number(v):
    return {"state": "observed", "value": v}


def observed_int(v):
    return {"state": "observed", "value": int(v)}


def non_observed(state, reason, basis_ids):
    return {"state": state, "reason": reason, "basis_ids": sorted(set(basis_ids))}


def ref(record_id, record_kind):
    return {"record_id": record_id, "record_kind": record_kind, "version": "1.3.0"}


def rule(rule_id, rule_kind):
    return {"rule_id": rule_id, "rule_kind": rule_kind, "version": "1.3.0"}


def lift(a, b, c, d):
    n = a + b + c + d
    denom = (a + b) * (a + c)
    return (a * n / denom) if (n > 0 and denom > 0) else None


def build(gt, cam, lid, group_of, universe, unknown_reason, evaluation_id, motion=None):
    """Assemble one worst_group_evaluation record over the declared universe."""
    cells = {g: [0, 0, 0, 0] for g in universe}
    insts = {g: set() for g in universe}
    for i, row in enumerate(gt):
        g = group_of(row)
        if g is None:
            continue
        cm = cam.get(i, -1.0) < THR
        lm = lid.get(i, -1.0) < THR
        k = 0 if (cm and lm) else (1 if cm else (2 if lm else 3))
        cells[g][k] += 1
        insts[g].add(row["instance_token"])

    results, eligible, unknown, insufficient = [], [], [], []
    for g in universe:
        a, b, c, d = cells[g]
        n = a + b + c + d
        ess = float(len(insts[g]))
        val = lift(a, b, c, d)
        members_unknown = unknown_reason.get(g)

        if members_unknown:
            # Membership itself is not derivable for this group. Nothing downstream
            # may be asserted: not the count, not the performance, not the interval.
            results.append({
                "group_id": g,
                "membership_state": "missing",
                "sample_count": non_observed("missing", members_unknown, [g]),
                "coverage_counts": {"total": n, "observed": 0, "missing": n,
                                    "unmeasured": 0, "out_of_distribution": 0,
                                    "sensor_invalid": 0, "abstained": 0},
                "effective_sample_size": non_observed("missing", members_unknown, [g]),
                "interval_width": non_observed("missing", members_unknown, [g]),
                "information_disposition": "unknown",
                "performance": non_observed("missing", members_unknown, [g]),
            })
            unknown.append(g)
            continue

        if val is None:
            reason = "no observed joint-failure denominator in this group"
            results.append({
                "group_id": g,
                "membership_state": "observed",
                "sample_count": observed_int(n),
                "coverage_counts": {"total": n, "observed": n, "missing": 0,
                                    "unmeasured": 0, "out_of_distribution": 0,
                                    "sensor_invalid": 0, "abstained": 0},
                "effective_sample_size": observed_number(ess),
                "interval_width": non_observed("unmeasured", reason, [g]),
                "information_disposition": "insufficient",
                "performance": non_observed("unmeasured", reason, [g]),
            })
            insufficient.append(g)
            continue

        # Interval width from a normal-approximation on log lift, at the instance unit.
        width = (2 * 1.96 * val * math.sqrt(1.0 / max(a, 1)) if a > 0
                 else INTERVAL_WIDTH_MAX * 10)
        ok = (n >= SAMPLE_COUNT_MIN and ess >= ESS_MIN
              and width <= INTERVAL_WIDTH_MAX and 1.0 >= COVERAGE_FRACTION_MIN)
        results.append({
            "group_id": g,
            "membership_state": "observed",
            "sample_count": observed_int(n),
            "coverage_counts": {"total": n, "observed": n, "missing": 0,
                                "unmeasured": 0, "out_of_distribution": 0,
                                "sensor_invalid": 0, "abstained": 0},
            "effective_sample_size": observed_number(ess),
            "interval_width": observed_number(round(width, 6)),
            "information_disposition": "sufficient" if ok else "insufficient",
            "performance": observed_number(round(val, 6)),
        })
        (eligible if ok else insufficient).append(g)

    # Disposition is a biconditional over the partition, never a free label.
    if unknown:
        disposition = "unknown"
        worst_ids = []
        worst_value = non_observed(
            "missing",
            "at least one group has non-observed membership, so the extremum over the "
            "declared universe is not identified",
            sorted(unknown))
    elif not eligible:
        disposition = "no_eligible_groups"
        worst_ids = []
        worst_value = non_observed(
            "unmeasured",
            "every group with observed membership failed the minimum information rule",
            sorted(insufficient) or [universe[0]])
    else:
        by_id = {r["group_id"]: r["performance"]["value"] for r in results
                 if r["group_id"] in eligible}
        top = max(by_id.values())
        worst_ids = sorted(k for k, v in by_id.items() if abs(v - top) < 1e-12)
        worst_value = observed_number(round(top, 6))
        disposition = "identified"

    artifact = "reiyah.artifact." + evaluation_id.split(".")[-1]
    return {
        "schema_id": SCHEMA_ID,
        "schema_version": "1.3.0",
        "artifact_id": artifact,
        "record_kind": "result",
        "version": "0.1.0",
        "lifecycle_status": "proposed",
        "lifecycle_history": [{
            "event_id": "reiyah.event." + evaluation_id.split(".")[-1] + ".proposed",
            "sequence": 1,
            "prior_status": None,
            "status": "proposed",
            "recorded_at": "2026-08-28T00:00:00Z",
            "actor": {
                "actor_id": "reiyah.actor.gate-b-measurement",
                "actor_type": "derived_process",
                "version": "1.3.0",
                "role": "deterministic offline measurement over published artifacts",
            },
            "rationale": "first worst_group_evaluation record derived from measured "
                         "data, exercising the unknown-group rule",
            "evidence_refs": [],
            "prior_artifact": None,
        }],
        "protocol_release_id": "reiyah.protocol.harbor-gate-a@1.2.0",
        "created_at": "2026-08-28T00:00:00Z",
        "runtime_execution_authorized": False,
        "evaluation_id": evaluation_id,
        "mission_release_id": "reiyah.mission@1.1.0",
        "scientific_claim_authorized": False,
        "dataset_ref": ref("reiyah.dataset.nuscenes-val", "reiyah.kind.dataset_release"),
        "benchmark_ref": ref("reiyah.benchmark.joint-detection-dependence",
                             "reiyah.kind.benchmark_release"),
        "study_ref": ref("reiyah.study.gate-b-measurement", "reiyah.kind.experiment"),
        "odd_ref": ref("reiyah.odd.nuscenes-boston-singapore", "reiyah.kind.odd_release"),
        # `joint_silent_miss` is deliberately ABSENT. Schema 1.3 declares it as a bare
        # $ref while its seven sibling evaluation sections are a oneOf with
        # nonObservedMeasurement. Expressing "this record did not measure joint silent
        # misses" would therefore require fabricating an opportunity set reference, an
        # opportunity window, a channel contract and opportunity rows for an analysis
        # that was never run. The record omits the section instead, and the resulting
        # whole-record schema failure is retained as the evidence for that 1.3 limit.
        # See docs/SCHEMA_1_3_FINDING_JOINT_SILENT_MISS.md.
        "selective_evaluation": non_observed(
            "unmeasured", "no selective predictor is evaluated in this record",
            ["reiyah.basis.not-in-scope"]),
        "ood_evaluation": non_observed(
            "unmeasured", "no out-of-distribution partition is evaluated in this record",
            ["reiyah.basis.not-in-scope"]),
        "conformal_evaluation": non_observed(
            "unmeasured", "no conformal procedure is evaluated in this record",
            ["reiyah.basis.not-in-scope"]),
        "transfer_evaluation": non_observed(
            "unmeasured", "no source-to-target transfer is evaluated in this record",
            ["reiyah.basis.not-in-scope"]),
        "evidence_binding": non_observed(
            "unmeasured",
            "no eligible retained evidence object exists for this measurement",
            ["reiyah.basis.evidence-admission-not-performed"]),
        "worst_group_evaluation": {
            "estimand_ref": ref("reiyah.estimand.joint-failure-lift",
                                "reiyah.kind.estimand"),
            "shared_metric_contract": {
                "metric_id": "reiyah.metric.joint-failure-lift",
                "version": "1.2.0",
                "unit": "ratio_of_observed_to_expected_joint_failures",
                "direction": "lower_is_better",
                "population_rule_ref": rule("reiyah.rule.nuscenes-val-population",
                                            "reiyah.kind.population_rule"),
                "outcome_window_rule_ref": rule("reiyah.rule.keyframe-window",
                                                "reiyah.kind.outcome_window_rule"),
            },
            "group_set_ref": ref("reiyah.group-set." + evaluation_id.split(".")[-1],
                                 "reiyah.kind.group_set"),
            "group_universe": sorted(universe),
            "minimum_information_rule": {
                "rule_ref": rule("reiyah.rule.worst-group-eligibility",
                                 "reiyah.kind.eligibility_rule"),
                "operator": "all",
                "sample_count_min": SAMPLE_COUNT_MIN,
                "coverage_fraction_min": COVERAGE_FRACTION_MIN,
                "effective_sample_size_min": ESS_MIN,
                "interval_width_max": INTERVAL_WIDTH_MAX,
            },
            "group_results": sorted(results, key=lambda r: r["group_id"]),
            "direction": "lower_is_better",
            "eligible_group_ids": sorted(eligible),
            "unknown_group_ids": sorted(unknown),
            "insufficient_group_ids": sorted(insufficient),
            "worst_group_ids": worst_ids,
            "worst_value": worst_value,
            "disposition": disposition,
            "omission_prohibited": True,
        },
    }


def main():
    gt = json.load(open(sys.argv[1]))
    cam = flatten(json.load(open(sys.argv[2]))["matched_at_2m"])
    lid = flatten(json.load(open(sys.argv[3]))["matched_at_2m"])
    out_path = sys.argv[4]

    tracks = {}
    for g in gt:
        tracks.setdefault(g["instance_token"], []).append((g["ts_us"], g["xy"]))
    motion = {}
    for t, pts in tracks.items():
        pts.sort()
        if len(pts) < 2 or (pts[-1][0] - pts[0][0]) <= 0:
            motion[t] = "unknown"
            continue
        dt = (pts[-1][0] - pts[0][0]) / 1e6
        motion[t] = ("moving" if math.dist(pts[0][1], pts[-1][1]) / dt >= MOVING_MPS
                     else "static")

    classes = sorted({g["cls"] for g in gt})
    rec_a = build(
        gt, cam, lid,
        group_of=lambda r: "reiyah.group.class-" + r["cls"].replace("_", "-"),
        universe=["reiyah.group.class-" + c.replace("_", "-") for c in classes],
        unknown_reason={},
        evaluation_id="reiyah.evaluation.worst-group-by-class",
    )

    motion_universe = ["reiyah.group.motion-moving", "reiyah.group.motion-static",
                       "reiyah.group.motion-underdetermined"]
    n_unknown_tracks = sum(1 for v in motion.values() if v == "unknown")
    n_unknown_vru = sum(1 for t, v in motion.items() if v == "unknown"
                        and any(g["cls"] in VRU for g in gt
                                if g["instance_token"] == t))
    rec_b = build(
        gt, cam, lid,
        group_of=lambda r: "reiyah.group.motion-" + (
            "underdetermined" if motion[r["instance_token"]] == "unknown"
            else motion[r["instance_token"]]),
        universe=motion_universe,
        unknown_reason={
            "reiyah.group.motion-underdetermined":
                f"{n_unknown_tracks} of {len(tracks)} tracked objects appear in fewer "
                "than two keyframes, so displacement over elapsed time is undefined and "
                "motion-state membership is not derivable"},
        evaluation_id="reiyah.evaluation.worst-group-by-motion-state",
    )

    def band(d):
        return ("0-20" if d < 20 else "20-30" if d < 30
                else "30-40" if d < 40 else "40-50")

    cr_universe = sorted({
        "reiyah.group.cls-" + r["cls"].replace("_", "-") + "-r" + band(r["dist"])
        for r in gt})
    rec_c = build(
        gt, cam, lid,
        group_of=lambda r: ("reiyah.group.cls-" + r["cls"].replace("_", "-")
                            + "-r" + band(r["dist"])),
        universe=cr_universe,
        unknown_reason={},
        evaluation_id="reiyah.evaluation.worst-group-by-class-and-range",
    )

    with open(out_path, "w") as fh:
        for r in (rec_a, rec_b, rec_c):
            fh.write(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n")

    for name, r in (("A by class", rec_a), ("B by motion state", rec_b),
                    ("C by class and range", rec_c)):
        w = r["worst_group_evaluation"]
        print(f"### record {name}")
        print(f"  universe {len(w['group_universe'])}"
              f"  eligible {len(w['eligible_group_ids'])}"
              f"  insufficient {len(w['insufficient_group_ids'])}"
              f"  unknown {len(w['unknown_group_ids'])}")
        print(f"  disposition : {w['disposition']}")
        print(f"  worst group : {w['worst_group_ids'] or 'none reported'}")
        wv = w["worst_value"]
        print(f"  worst value : "
              + (f"{wv['value']}" if wv["state"] == "observed"
                 else f"{wv['state']}: {wv['reason'][:80]}"))
        print()
    print(f"unknown-motion tracks: {n_unknown_tracks} of {len(tracks)},"
          f" of which vulnerable road users: {n_unknown_vru}")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
