"""Build a real joint-performance-evaluation record under the v1.3 contract.

This is the first time a Reiyah scientific schema is asked to hold measured
data rather than a hand-authored fixture. The v1.2 synthetic fixture carries
four opportunity rows. This carries 134,565, one per annotated object that
survives the official class-range filter.

Two channels, ordered, each declaring its role:
  first   machine_perception   camera-only detector
  second  machine_perception   lidar-only detector

Under v1.2 this record was unrepresentable: that contract names its channels
human_channel and automation_channel, so a camera-versus-lidar comparison had
to misuse a field name. v1.3 replaces the two named properties with an ordered
role-bearing pair, which is the whole reason v1.3 exists.

Usage:
  python3 tools/measure/build_joint_record.py gt_val_cache.json \\
      first=matched_mapillary.json second=matched_megvii.json out.json [--threshold 0.3]
"""
import datetime as dt
import json
import sys

THR = 0.3
args, kw = [], {}
for a in sys.argv[1:]:
    if a.startswith("--threshold"):
        THR = float(a.split("=", 1)[1]) if "=" in a else THR
    elif "=" in a:
        k, v = a.split("=", 1)
        kw[k] = v
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


first = flat(kw["first"])
second = flat(kw["second"])


def utc(us):
    return dt.datetime.fromtimestamp(us / 1e6, dt.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def ref(rid, kind):
    return {"record_id": rid, "record_kind": kind, "version": "1.3.0"}


CH_FIRST = ref("reiyah.channel.nuscenes.mapillary-monodis-camera",
               "reiyah.kind.observation_channel")
CH_SECOND = ref("reiyah.channel.nuscenes.megvii-cbgs-lidar",
                "reiyah.kind.observation_channel")

# A detection channel emits no warning and has no fallback procedure. Those
# operands are genuinely absent rather than negative, so they carry an explicit
# non-observed state with a reason and a basis, per the status model.
ABSENT_WARNING = {
    "rule_ref": {"rule_id": "reiyah.rule.no-warning-channel-in-source",
                 "rule_kind": "reiyah.kind.event_rule", "version": "1.3.0"},
    "outcome": {"state": "unmeasured",
                "reason": ("the source is an offline detection benchmark; it contains no "
                           "warning-issuing subsystem, so warning issuance is unmeasured "
                           "rather than not_issued"),
                "basis_ids": ["reiyah.basis.nuscenes-detection-benchmark-scope"]}
}
ABSENT_FALLBACK = {
    "rule_ref": {"rule_id": "reiyah.rule.no-fallback-procedure-in-source",
                 "rule_kind": "reiyah.kind.event_rule", "version": "1.3.0"},
    "outcome": {"state": "unmeasured",
                "reason": ("the source is an offline detection benchmark; it contains no "
                           "fallback procedure, so activation is unmeasured rather than "
                           "not_activated"),
                "basis_ids": ["reiyah.basis.nuscenes-detection-benchmark-scope"]}
}

rows = []
both = f_only = s_only = neither = 0
ts_min, ts_max = None, None

for i, g in enumerate(gt):
    fm = first.get(i, -1.0) < THR
    sm = second.get(i, -1.0) < THR
    if fm and sm:
        both += 1
    elif fm:
        f_only += 1
    elif sm:
        s_only += 1
    else:
        neither += 1
    ts = g["ts_us"]
    ts_min = ts if ts_min is None else min(ts_min, ts)
    ts_max = ts if ts_max is None else max(ts_max, ts)
    rows.append({
        "opportunity_id": f"reiyah.opportunity.nuscenes-val.{g['ann_token']}",
        "object_ref": ref(f"reiyah.object.nuscenes.{g['ann_token']}",
                          "reiyah.kind.annotated_road_object"),
        "clock_id": "reiyah.clock.nuscenes-sample-utc",
        "window_id": "reiyah.window.nuscenes-val-keyframe",
        "occurred_at": {"state": "observed", "value": utc(ts)},
        "reference_state": {"state": "observed", "value": "opportunity_present"},
        "reference_validity": {"state": "observed", "value": "valid"},
        "channels": [
            {"channel_ref": CH_FIRST, "role": "machine_perception",
             "outcome": {"state": "observed", "value": "miss" if fm else "detected"}},
            {"channel_ref": CH_SECOND, "role": "machine_perception",
             "outcome": {"state": "observed", "value": "miss" if sm else "detected"}},
        ],
        "warning": ABSENT_WARNING,
        "fallback": ABSENT_FALLBACK,
    })

n = len(rows)
record = {
    "schema_id": "https://schemas.reiyah.invalid/scientific-contract/1.3.0/joint-performance-evaluation.schema.json",
    "schema_version": "1.3.0",
    "artifact_id": "reiyah.artifact.joint-performance-nuscenes-val-camera-lidar",
    "record_kind": "result",
    "version": "0.1.0",
    "lifecycle_status": "proposed",
    "lifecycle_history": [{
        "event_id": "reiyah.event.joint-performance-nuscenes-val-camera-lidar.proposed",
        "sequence": 1,
        "prior_status": None,
        "status": "proposed",
        "recorded_at": "2026-08-28T00:00:00Z",
        "actor": {
            "actor_id": "reiyah.actor.gate-b-measurement",
            "actor_type": "derived_process",
            "version": "1.3.0",
            "role": "deterministic offline measurement over published artifacts"
        },
        "rationale": ("first application of a Reiyah scientific contract to measured data "
                      "rather than to a synthetic fixture"),
        "evidence_refs": [],
        "prior_artifact": None
    }],
    "protocol_release_id": "reiyah.protocol.harbor-gate-a@1.2.0",
    "mission_release_id": "reiyah.mission@1.1.0",
    "created_at": "2026-08-28T00:00:00Z",
    "runtime_execution_authorized": False,
    "scientific_claim_authorized": False,
    "evaluation_id": "reiyah.evaluation.nuscenes-val-camera-lidar-joint-miss",
    "study_ref": {"state": "unmeasured",
                  "reason": "no authorized study exists; this is a secondary analysis of published artifacts",
                  "basis_ids": ["reiyah.basis.gate-b-measurement-contract"]},
    "dataset_ref": ref("reiyah.dataset.nuscenes-v1.0-trainval-val-split",
                       "reiyah.kind.dataset_release"),
    "odd_ref": {"state": "unmeasured",
                "reason": "the source declares no operational design domain",
                "basis_ids": ["reiyah.basis.nuscenes-detection-benchmark-scope"]},
    "benchmark_ref": ref("reiyah.benchmark.nuscenes-detection-cvpr-2019",
                         "reiyah.kind.benchmark_release"),
    "joint_silent_miss": {
        "estimand_ref": ref("reiyah.estimand.joint-silent-miss-rate",
                            "reiyah.kind.estimand_definition"),
        "opportunity_rule_ref": {"rule_id": "reiyah.rule.nuscenes-annotated-object-in-class-range",
                                 "rule_kind": "reiyah.kind.opportunity_rule", "version": "1.3.0"},
        "opportunity_set_ref": ref("reiyah.opportunity-set.nuscenes-val-in-range",
                                   "reiyah.kind.opportunity_set"),
        "opportunity_window": {
            "clock_id": "reiyah.clock.nuscenes-sample-utc",
            "window_id": "reiyah.window.nuscenes-val-keyframe",
            "opened_at": utc(ts_min), "closed_at": utc(ts_max)},
        "channel_contract": {
            "first": {"role": "machine_perception", "channel_ref": CH_FIRST},
            "second": {"role": "machine_perception", "channel_ref": CH_SECOND}},
        "opportunity_rows": rows,
        "common_opportunity_cells": {
            "both_miss": {"state": "observed", "value": both},
            "first_only_miss": {"state": "observed", "value": f_only},
            "second_only_miss": {"state": "observed", "value": s_only},
            "neither_miss": {"state": "observed", "value": neither}},
        # A joint miss is SILENT only when both channels miss AND no warning was
        # issued AND no fallback activated. This source observes neither warning
        # nor fallback, so silence is not establishable and the silent-miss
        # summary is nonidentifiable. both_miss is measured; silent joint miss
        # is not. Conflating them was our error, caught by the semantic contract
        # after JSON Schema had passed the record.
        "identifiability": "nonidentifiable_unknown",
        "opportunities": {"state": "observed", "value": n},
        "first_misses": {"state": "observed", "value": both + f_only},
        "second_misses": {"state": "observed", "value": both + s_only},
        "joint_misses": {
            "state": "unmeasured",
            "reason": ("silent joint miss requires warning not_issued and fallback "
                       "not_activated; this source observes neither, so the count of "
                       "SILENT joint misses is not establishable. The count of "
                       "both-channel misses is observed and is carried in "
                       "common_opportunity_cells.both_miss"),
            "basis_ids": ["reiyah.basis.nuscenes-detection-benchmark-scope"]},
        "joint_miss_risk": {
            "state": "unmeasured",
            "reason": "derived from joint_misses, which is not establishable from this source",
            "basis_ids": ["reiyah.basis.nuscenes-detection-benchmark-scope"]},
    },
}

for k in ("selective_evaluation", "ood_evaluation", "conformal_evaluation",
          "transfer_evaluation", "worst_group_evaluation"):
    record[k] = {"state": "unmeasured",
                 "reason": f"{k} is out of scope for this record, which measures joint misses only",
                 "basis_ids": ["reiyah.basis.gate-b-measurement-contract"]}
record["evidence_binding"] = {
    "state": "unmeasured",
    "reason": ("Gate A 1.2 exposes only an explicit evidence-gap binding and has no eligible "
               "scientific-evidence resolver; this record therefore binds no evidence object"),
    "basis_ids": ["reiyah.basis.gate-a-1.2-evidence-gap-envelope"]}

json.dump(record, open(out_path, "w"), separators=(",", ":"))
print(f"rows            : {n:,}")
print(f"cells           : both={both:,} first_only={f_only:,} second_only={s_only:,} neither={neither:,}")
print(f"joint miss risk : {both/n:.6f}")
print(f"window          : {utc(ts_min)} .. {utc(ts_max)}")
print(f"wrote {out_path}")
