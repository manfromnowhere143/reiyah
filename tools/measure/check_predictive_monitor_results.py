#!/usr/bin/env python3
"""Separately reaggregate retained predictions; do not import the fitting code."""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np  # Archive decoding and seeded bootstrap, not producer imports.


def require(condition, message):
    if not condition:
        raise ValueError(message)


def same(a, b, message):
    if a is None or b is None:
        require(a is b, message)
    else:
        require(math.isfinite(a) and math.isfinite(b) and math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-9), message)


def mean(values):
    return math.fsum(values) / len(values)


def deviance(y, p):
    require(type(y) is int and y >= 0 and type(p) in (int, float) and math.isfinite(p) and p > 0, "invalid prediction or target")
    return 2 * ((y * math.log(y/p) if y else 0) - y + p)


def auc(labels, scores):
    npos, nneg = sum(labels), len(labels) - sum(labels)
    if not npos or not nneg:
        return None
    ordered = sorted(zip(scores, labels))
    rank_sum, i = 0., 0
    while i < len(ordered):
        end = i+1
        while end < len(ordered) and ordered[end][0] == ordered[i][0]:
            end += 1
        rank_sum += (i+1+end)/2 * sum(label for _, label in ordered[i:end])
        i = end
    return (rank_sum - npos*(npos+1)/2) / (npos*nneg)


def audit_model(rows, name, reported):
    require(len(rows) == reported["frames"], "frame denominator differs")
    groups = defaultdict(list)
    ds, errors, counts, predictions, labels, alarms = [], [], [], [], [], []
    policy = []
    for row in rows:
        p, y = row["prediction"][name], row["y"]
        d = deviance(y, p)
        ds.append(d); errors.append(abs(y-p)); counts.append(y); predictions.append(p)
        groups[row["scene"]].append(d)
        labels.append(y >= row["high_count_threshold"])
        threshold = row["alert_threshold"][name]
        policy.append(threshold is not None)
        alarms.append(p > threshold if threshold is not None else False)
    require(len(groups) == reported["scenes"], "scene denominator differs")
    same(mean(ds), reported["deviance_frame_mean"], "frame deviance differs")
    same(mean([mean(v) for v in groups.values()]), reported["deviance_scene_mean"], "scene deviance differs")
    same(mean(errors), reported["mae"], "MAE differs")
    same(mean(counts), reported["observed_mean"], "observed mean differs")
    same(mean(predictions), reported["predicted_mean"], "predicted mean differs")
    same(sum(counts), reported["misses_total"], "total target count differs")
    same(auc(labels, predictions), reported["high_count_auc"], "ROC AUC differs")
    same(math.fsum(predictions) / sum(counts) if sum(counts) else None,
         reported["predicted_to_observed_count_ratio"], "calibration ratio differs")
    require(all(policy) or not any(policy), "mixed alert policy definedness")
    if all(policy):
        remaining = sum(y for y, alarm in zip(counts, alarms) if not alarm)
        same(mean(alarms), reported["alert_fraction"], "alert frequency differs")
        same((sum(counts)-remaining)/sum(counts) if sum(counts) else None,
             reported["miss_fraction_in_alerts"], "captured count fraction differs")
        same(remaining, reported["misses_outside_alerts"], "remaining count differs")
        nonalarms = sum(not a for a in alarms)
        same(remaining/nonalarms if nonalarms else None, reported["mean_misses_unflagged"], "unflagged mean differs")
        nonhigh = sum(not v for v in labels)
        same(sum(a and not h for a, h in zip(alarms,labels))/nonhigh if nonhigh else None,
             reported["high_count_false_alarm_rate"], "false alarm rate differs")
    else:
        for key in ("alert_fraction", "miss_fraction_in_alerts", "misses_outside_alerts", "mean_misses_unflagged", "high_count_false_alarm_rate"):
            require(reported[key] is None, "unevaluated alert policy became a number")
    return ds


def check_band(rows, base, candidate, group_key, result, seed, repetitions):
    grouped = defaultdict(lambda: [[], []])
    for r in rows:
        grouped[r[group_key]][0].append(deviance(r["y"], r["prediction"][base]))
        grouped[r[group_key]][1].append(deviance(r["y"], r["prediction"][candidate]))
    means = [(mean(grouped[k][0]), mean(grouped[k][1])) for k in sorted(grouped)]
    require(len(means) == result["groups"], "paired population differs")
    a, b = np.asarray(means).T
    same(float(a.mean()), result["base_group_mean_deviance"], "paired base differs")
    same(float(b.mean()), result["candidate_group_mean_deviance"], "paired candidate differs")
    same(float((a-b).mean()), result["improvement"], "paired difference differs")
    selected = np.random.default_rng(seed).integers(len(a), size=(repetitions,len(a)))
    absolute = (a[selected] - b[selected]).mean(axis=1)
    relative = 1-b[selected].mean(axis=1)/a[selected].mean(axis=1)
    for produced, recomputed in zip(result["percentile_95"], np.percentile(absolute,[2.5,97.5])):
        same(produced, float(recomputed), "paired absolute interval differs")
    for produced, recomputed in zip(result["relative_percentile_95"], np.percentile(relative,[2.5,97.5])):
        same(produced, float(recomputed), "paired relative interval differs")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "checker output already exists")
    spec = json.loads((args.run_dir / "spec.json").read_bytes())
    result_path = args.run_dir / "result.json"
    result = json.loads(result_path.read_bytes())
    require(hashlib.sha256(args.dataset.read_bytes()).hexdigest() == spec["dataset_sha256"], "dataset changed")
    require(hashlib.sha256((args.run_dir / "spec.json").read_bytes()).hexdigest() == result["spec_sha256"], "spec changed")
    for name, record in result["private_outputs"].items():
        p = args.run_dir/name
        require(p.stat().st_size == record["bytes"] and hashlib.sha256(p.read_bytes()).hexdigest() == record["sha256"], "private closure differs")
    with np.load(args.dataset,allow_pickle=False) as raw:
        data = {k:raw[k] for k in raw.files}
    frame_index = {str(t):i for i,t in enumerate(data["frames"])}
    cases = defaultdict(list)
    with (args.run_dir/"predictions.private.jsonl").open() as stream:
        for line in stream:
            row = json.loads(line)
            cases[row["experiment"]].append(row)
    fold_maps = {}
    with (args.run_dir/"folds.private.jsonl").open() as stream:
        for line in stream:
            row = json.loads(line)
            key = row["experiment"],row["fold"]
            require(key not in fold_maps, "repeated fold mapping")
            require(not set(row["train_scenes"]) & set(row["test_scenes"]), "train/test scene overlap")
            fold_maps[key] = row
    checked = []
    for name, report in result["experiments"].items():
        rows = cases[name]
        require(len({r["frame"] for r in rows}) == len(rows) == report["frames"], "frame duplication or omission")
        by_scene = defaultdict(list)
        for i, scene in enumerate(data["scenes"]):
            by_scene[str(scene)].append(i)
        expected = {}
        for indices in by_scene.values():
            indices.sort(key=lambda i: data["timestamps"][i])
            for position,a in enumerate(indices):
                if report["horizon_us"] == 0:
                    expected[str(data["frames"][a])] = a
                else:
                    future = indices[position+1:]
                    if future:
                        chosen = min(future,key=lambda j: (abs(int(data["timestamps"][j]-data["timestamps"][a])-report["horizon_us"]), int(data["timestamps"][j])))
                        if abs(int(data["timestamps"][chosen]-data["timestamps"][a])-report["horizon_us"]) <= spec["horizon_tolerance_us"]:
                            expected[str(data["frames"][a])] = chosen
        require(set(expected) == {r["frame"] for r in rows}, "clock-selected anchor population differs")
        for row in rows:
            a, dest = frame_index[row["frame"]], frame_index[row["target_frame"]]
            require(expected[row["frame"]] == dest, "future target identity differs")
            require(int(data[report["target"]][dest]) == row["y"], "retained target differs")
            require(str(data["scenes"][a]) == row["scene"] and str(data["logs"][a]) == row["log"], "metadata identity differs")
            mapping = fold_maps[(name,row["fold"])]
            require(row["scene"] in mapping["test_scenes"] and row["scene"] not in mapping["train_scenes"], "test assignment differs")
        for fold in range(spec["outer_folds"]):
            train, test = [r for r in rows if r["fold"] != fold], [r for r in rows if r["fold"] == fold]
            q = sorted(r["y"] for r in train)[math.ceil(.75*(len(train)-1))]
            require(all(r["high_count_threshold"] == q for r in test), "high-count cutoff is not training-only")
            if spec["split_unit"] == "logs":
                require(not {r["log"] for r in train} & {r["log"] for r in test}, "train/test log overlap")
        for model, record in report["models"].items():
            audit_model(rows,model,record)
        for key, record in report["paired_scene_comparisons"].items():
            candidate, base = key.split("_vs_")
            check_band(rows,base,candidate,"scene",record,spec["bootstrap_seed"],spec["bootstrap_resamples"])
        for key, record in report["paired_log_comparisons"].items():
            candidate, base = key.split("_vs_")
            check_band(rows,base,candidate,"log",record,spec["bootstrap_seed"],spec["bootstrap_resamples"])
        checked.append({"experiment":name,"rows":len(rows),"models":len(report["models"]),
                        "scene_comparisons":len(report["paired_scene_comparisons"]),"log_comparisons":len(report["paired_log_comparisons"])})
    require(result["physical_failure_rate"] is None and result["online_warning_lead_time"] is None and result["safety_benefit"] is None,
            "unmeasured physical/operational outcome became a number")
    audit = {"artifact_id":"reiyah.predictive-monitor-independent-reaggregation.0.1.0","version":"0.1.0",
             "status":"pass","lifecycle_status":"exploratory","checked":checked,
             "result_sha256":hashlib.sha256(result_path.read_bytes()).hexdigest(),
             "checker_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             "limits":["Separate numeric implementation over shared retained predictions; no independent human review",
                       "Does not refit models, reproduce internal tuning predictions, or validate physical reference truth"]}
    args.output.write_text(json.dumps(audit,sort_keys=True,indent=2)+'\n')
    print(json.dumps(audit,sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print(json.dumps({"status":"invalid","diagnostic":str(exc)}),file=sys.stderr)
        raise SystemExit(2)
