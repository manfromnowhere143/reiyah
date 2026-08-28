"""Build joint-performance records at the unit the contract actually models.

The executable contract requires that every opportunity row bind the SAME
object and that occurred_at be strictly increasing. That is not an accident and
it is not a limitation: it says the opportunity unit is one common object
observed over a time series, which the mathematical specification states in
section 5.11 as "every row binds the common object".

An earlier attempt built one record holding 134,565 rows spanning every object.
That is the wrong unit and the contract correctly refuses it.

nuScenes objects are tracked, so the data already has the right shape: 8,976
distinct instances in the validation split, mean 15 observations each, and no
instance carries two observations at the same timestamp. One record per
instance fits the contract exactly.

This is also the correct statistical unit. Treating ~15 near-identical boxes of
one tracked object as independent observations is the clustering error flagged
in our own traps table. The contract's structure encodes the right unit.

Usage:
  python3 tools/measure/build_joint_records_per_instance.py gt_val_cache.json \\
      first=matched_mapillary.json second=matched_megvii.json out.jsonl [--threshold 0.3]
"""
import collections
import datetime as dt
import json
import sys

THR = 0.3
args, kw = [], {}
for a in sys.argv[1:]:
    if a.startswith("--threshold"):
        THR = float(a.split("=", 1)[1])
    elif "=" in a:
        k, v = a.split("=", 1); kw[k] = v
    else:
        args.append(a)

gt = json.load(open(args[0]))
out_path = args[1]


def flat(path):
    m = {}
    for _c, d in json.load(open(path))["matched_at_2m"].items():
        for k, v in d.items():
            m[int(k)] = v
    return m


first, second = flat(kw["first"]), flat(kw["second"])


def utc(us):
    return dt.datetime.fromtimestamp(us / 1e6, dt.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def ref(rid, kind):
    return {"record_id": rid, "record_kind": kind, "version": "1.3.0"}


CH_FIRST = ref("reiyah.channel.nuscenes.mapillary-monodis-camera",
               "reiyah.kind.observation_channel")
CH_SECOND = ref("reiyah.channel.nuscenes.megvii-cbgs-lidar",
                "reiyah.kind.observation_channel")
W_RULE = {"rule_id": "reiyah.rule.no-warning-channel-in-source",
          "rule_kind": "reiyah.kind.event_rule", "version": "1.3.0"}
F_RULE = {"rule_id": "reiyah.rule.no-fallback-procedure-in-source",
          "rule_kind": "reiyah.kind.event_rule", "version": "1.3.0"}
BASIS = ["reiyah.basis.nuscenes-detection-benchmark-scope"]
NO_WARN = {"rule_ref": W_RULE, "outcome": {"state": "unmeasured",
           "reason": "the source contains no warning-issuing subsystem", "basis_ids": BASIS}}
NO_FALL = {"rule_ref": F_RULE, "outcome": {"state": "unmeasured",
           "reason": "the source contains no fallback procedure", "basis_ids": BASIS}}

# The object kind follows the road user, which v1.2 could not express because it
# pinned every opportunity object to a vehicle by const.
OBJ_KIND = collections.defaultdict(lambda: "reiyah.kind.vehicle_object", {
    "pedestrian": "reiyah.kind.vulnerable_road_user_object",
    "bicycle": "reiyah.kind.vulnerable_road_user_object",
    "motorcycle": "reiyah.kind.vulnerable_road_user_object",
    "traffic_cone": "reiyah.kind.static_obstacle_object",
    "barrier": "reiyah.kind.static_obstacle_object",
})

by_instance = collections.defaultdict(list)
for i, g in enumerate(gt):
    by_instance[g["instance_token"]].append(i)

n_rec = 0
kind_counts = collections.Counter()
with open(out_path, "w") as fh:
    for inst, idxs in by_instance.items():
        idxs.sort(key=lambda i: gt[i]["ts_us"])          # strictly increasing
        g0 = gt[idxs[0]]
        kind = OBJ_KIND[g0["cls"]]
        kind_counts[kind] += 1
        obj = ref(f"reiyah.object.nuscenes.instance.{inst}", kind)

        rows, cells = [], collections.Counter()
        for i in idxs:
            g = gt[i]
            fm = first.get(i, -1.0) < THR
            sm = second.get(i, -1.0) < THR
            cells["both_miss" if fm and sm else "first_only_miss" if fm
                  else "second_only_miss" if sm else "neither_miss"] += 1
            rows.append({
                "opportunity_id": f"reiyah.opportunity.nuscenes-val.{g['ann_token']}",
                "object_ref": obj,
                "clock_id": "reiyah.clock.nuscenes-sample-utc",
                "window_id": f"reiyah.window.nuscenes-val.instance.{inst}",
                "occurred_at": {"state": "observed", "value": utc(g["ts_us"])},
                "reference_state": {"state": "observed", "value": "opportunity_present"},
                "reference_validity": {"state": "observed", "value": "valid"},
                "channels": [
                    {"channel_ref": CH_FIRST, "role": "machine_perception",
                     "outcome": {"state": "observed", "value": "miss" if fm else "detected"}},
                    {"channel_ref": CH_SECOND, "role": "machine_perception",
                     "outcome": {"state": "observed", "value": "miss" if sm else "detected"}},
                ],
                "warning": NO_WARN, "fallback": NO_FALL,
            })

        n = len(rows)
        rec = {
            "schema_id": "https://schemas.reiyah.invalid/scientific-contract/1.3.0/joint-performance-evaluation.schema.json",
            "schema_version": "1.3.0",
            "artifact_id": f"reiyah.artifact.joint-performance-nuscenes-val.instance.{inst}",
            "record_kind": "result", "version": "0.1.0", "lifecycle_status": "proposed",
            "lifecycle_history": [{
                "event_id": f"reiyah.event.joint-performance-nuscenes-val.instance.{inst}.proposed",
                "sequence": 1, "prior_status": None, "status": "proposed",
                "recorded_at": "2026-08-28T00:00:00Z",
                "actor": {"actor_id": "reiyah.actor.gate-b-measurement",
                          "actor_type": "derived_process", "version": "1.3.0",
                          "role": "deterministic offline measurement over published artifacts"},
                "rationale": "one tracked object observed over a strictly ordered time series",
                "evidence_refs": [], "prior_artifact": None}],
            "protocol_release_id": "reiyah.protocol.harbor-gate-a@1.2.0",
            "mission_release_id": "reiyah.mission@1.1.0",
            "created_at": "2026-08-28T00:00:00Z",
            "runtime_execution_authorized": False, "scientific_claim_authorized": False,
            "evaluation_id": f"reiyah.evaluation.nuscenes-val.instance.{inst}",
            "study_ref": {"state": "unmeasured", "reason": "secondary analysis of published artifacts", "basis_ids": BASIS},
            "dataset_ref": ref("reiyah.dataset.nuscenes-v1.0-trainval-val-split", "reiyah.kind.dataset_release"),
            "odd_ref": {"state": "unmeasured", "reason": "the source declares no operational design domain", "basis_ids": BASIS},
            "benchmark_ref": ref("reiyah.benchmark.nuscenes-detection-cvpr-2019", "reiyah.kind.benchmark_release"),
            "joint_silent_miss": {
                "estimand_ref": ref("reiyah.estimand.joint-silent-miss-rate", "reiyah.kind.estimand_definition"),
                "opportunity_rule_ref": {"rule_id": "reiyah.rule.nuscenes-annotated-object-in-class-range",
                                         "rule_kind": "reiyah.kind.opportunity_rule", "version": "1.3.0"},
                "opportunity_set_ref": ref(f"reiyah.opportunity-set.nuscenes-val.instance.{inst}",
                                           "reiyah.kind.opportunity_set"),
                "opportunity_window": {"clock_id": "reiyah.clock.nuscenes-sample-utc",
                                       "window_id": f"reiyah.window.nuscenes-val.instance.{inst}",
                                       "opened_at": utc(gt[idxs[0]]["ts_us"]),
                                       "closed_at": utc(gt[idxs[-1]]["ts_us"])},
                "channel_contract": {"first": {"role": "machine_perception", "channel_ref": CH_FIRST},
                                     "second": {"role": "machine_perception", "channel_ref": CH_SECOND}},
                "opportunity_rows": rows,
                "common_opportunity_cells": {k: {"state": "observed", "value": cells[k]}
                                             for k in ("both_miss", "first_only_miss",
                                                       "second_only_miss", "neither_miss")},
                # Unknown propagation is CONDITIONAL on the unknown operand being
                # reached. Warning and fallback are consulted only for a both-miss
                # row. If this object was never missed by both channels there is
                # nothing whose silence needs establishing, every operand is
                # observed, and the silent count is knowably zero. Declaring the
                # summary unknown regardless was our error, caught by executing
                # the semantic rules rather than reading them.
                "identifiability": ("nonidentifiable_unknown" if cells["both_miss"]
                                    else "identified_from_common_opportunities"),
                "opportunities": {"state": "observed", "value": n},
                "first_misses": {"state": "observed", "value": cells["both_miss"] + cells["first_only_miss"]},
                "second_misses": {"state": "observed", "value": cells["both_miss"] + cells["second_only_miss"]},
                "joint_misses": ({"state": "unmeasured",
                                  "reason": "silent joint miss requires warning not_issued and fallback not_activated; neither is observed and this object has at least one both-channel miss",
                                  "basis_ids": BASIS}
                                 if cells["both_miss"]
                                 else {"state": "observed", "value": 0}),
                "joint_miss_risk": ({"state": "unmeasured",
                                     "reason": "derived from joint_misses, which is not establishable for this object",
                                     "basis_ids": BASIS}
                                    if cells["both_miss"]
                                    else {"state": "observed", "value": 0.0}),
            },
        }
        for k in ("selective_evaluation", "ood_evaluation", "conformal_evaluation",
                  "transfer_evaluation", "worst_group_evaluation"):
            rec[k] = {"state": "unmeasured", "reason": f"{k} is out of scope for this record", "basis_ids": BASIS}
        rec["evidence_binding"] = {"state": "unmeasured",
                                   "reason": "Gate A 1.2 exposes only an explicit evidence-gap binding",
                                   "basis_ids": BASIS}
        fh.write(json.dumps(rec, separators=(",", ":")) + "\n")
        n_rec += 1

print(f"records written : {n_rec:,}  (one per tracked object)")
print(f"rows total      : {len(gt):,}")
print("object kinds    : " + ", ".join(f"{k.rsplit('.',1)[-1]}={v:,}" for k, v in kind_counts.most_common()))
print(f"wrote {out_path}")
