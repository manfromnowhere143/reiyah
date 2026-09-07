#!/usr/bin/env python3
"""Audit the complete frozen monitor experiments, including omitted-result attacks.

This successor leaves the source-bound producer and first numeric checker intact.
It verifies the declared result population before invoking the separate numeric
checker, then independently checks the log-resampled equal-scene estimand.
"""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np

from check_predictive_monitor_results import deviance, mean, require, same


PROFILES = {
    "reiyah.predictive-monitor-analysis-spec.0.1.0":
        ("0.1.0/scene-analysis-spec.json", False),
    "reiyah.predictive-monitor-log-analysis-spec.0.1.0":
        ("0.1.0/log-analysis-spec.json", False),
    "reiyah.predictive-monitor-spatial-spec.0.2.0":
        ("0.2.0/spatial-analysis-spec.json", True),
}
CONTROLS = {"constant", "proportional_union", "shuffled_training_labels", "unavailable_oracle"}
PAIRS = (("marginal_history", "joint_history"),
         ("marginal_current", "joint_current"),
         ("marginal_current", "marginal_history"),
         ("density_current", "marginal_current"),
         ("proportional_union", "joint_history"))


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def strict_json(text):
    def pairs(items):
        result = {}
        for k, v in items:
            require(k not in result, "duplicate JSON property")
            result[k] = v
        return result

    def constant(value):
        raise ValueError("nonfinite JSON number: " + value)

    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def finite_number(value, message):
    require(type(value) in (int, float) and math.isfinite(value), message)


def declared_population(spec, result):
    require(spec["artifact_id"] in PROFILES, "unknown frozen analysis profile")
    spatial = PROFILES[spec["artifact_id"]][1]
    expected = {f"{t}_h{h}" for t in spec["targets"] for h in spec["horizons_us"]}
    require(expected and set(result["experiments"]) == expected, "planned experiment population differs")
    models = set(spec["feature_variants"]) | CONTROLS | ({"spatial_history"} if spatial else set())
    comparisons = ({"spatial_history_vs_joint_history", "spatial_history_vs_marginal_history"}
                   if spatial else {b + "_vs_" + a for a, b in PAIRS if a in models and b in models})
    outputs = {"predictions.private.jsonl", "folds.private.jsonl"}
    if spatial:
        outputs.add("geometry.private.npz")
    require(set(result["private_outputs"]) == outputs, "required private output population differs")
    require(result["split_unit"] == spec["split_unit"], "split unit differs")
    for target in spec["targets"]:
        for horizon in spec["horizons_us"]:
            report = result["experiments"][f"{target}_h{horizon}"]
            require(report["target"] == target and report["horizon_us"] == horizon,
                    "declared target or horizon differs")
            require(report["split_unit"] == spec["split_unit"], "experiment split unit differs")
            require(set(report["models"]) == models, "planned model population differs")
            for key in ("paired_scene_comparisons", "paired_log_comparisons"):
                require(set(report[key]) == comparisons, "planned comparison population differs")
            require(("log_resampled_equal_scene_comparison" in report) == spatial,
                    "log-resampled equal-scene result presence differs")
            require(len(report["folds"]) == spec["outer_folds"] and
                    {f["fold"] for f in report["folds"]} == set(range(spec["outer_folds"])),
                    "reported fold population differs")
            for fold in report["folds"]:
                require(set(fold["models"]) == models, "fold model population differs")
    return models, spatial


def check_log_scene_band(rows, record, seed, repetitions):
    """Different accumulation from the producer; preserve equal-scene weights.

    A log with two scenes contributes two scene means whenever it is drawn.
    Giving every log one averaged loss would change the target estimand.
    """
    scenes = defaultdict(list)
    scene_logs = {}
    for row in rows:
        scene = row["scene"]
        require(scene not in scene_logs or scene_logs[scene] == row["log"], "scene spans collection logs")
        scene_logs[scene] = row["log"]
        scenes[scene].append(row)
    per_scene = {s: (mean([deviance(r["y"], r["prediction"]["joint_history"]) for r in rs]),
                     mean([deviance(r["y"], r["prediction"]["spatial_history"]) for r in rs]))
                 for s, rs in scenes.items()}
    logs = sorted(set(scene_logs.values()))
    sums = [[], [], []]
    for log in logs:
        values = [per_scene[s] for s in sorted(per_scene) if scene_logs[s] == log]
        sums[0].append(math.fsum(v[0] for v in values))
        sums[1].append(math.fsum(v[1] for v in values))
        sums[2].append(len(values))
    a, b, n = (np.asarray(v) for v in sums)
    require(len(logs) and np.all(a > 0), "undefined log-scene relative interval")
    draws = np.random.default_rng(seed).integers(len(logs), size=(repetitions, len(logs)))
    aa, bb, nn = a[draws].sum(axis=1), b[draws].sum(axis=1), n[draws].sum(axis=1)
    expected = {"sampling_unit": "collection_log", "estimand": "equal_scene_mean_deviance",
                "logs": len(logs), "scenes": len(scenes), "seed": seed, "resamples": repetitions,
                "conditional_on_fixed_predictions": True}
    for key, value in expected.items():
        require(record[key] == value, "log-scene interval metadata differs: " + key)
    same(record["improvement"], float((a.sum() - b.sum()) / n.sum()), "log-scene point differs")
    same(record["relative_improvement"], float(1 - b.sum() / a.sum()), "log-scene relative point differs")
    for key, values in (("percentile_95", (aa - bb) / nn), ("relative_percentile_95", 1 - bb / aa)):
        require(len(record[key]) == 2, "log-scene interval endpoints missing")
        for got, wanted in zip(record[key], np.quantile(values, [.025, .975])):
            same(got, float(wanted), "log-scene interval differs")


def check_rows_and_folds(spec, result, cases, mappings, data, models):
    require(set(cases) == set(result["experiments"]), "prediction experiment population differs")
    wanted_maps = {(e, f) for e in result["experiments"] for f in range(spec["outer_folds"])}
    require(set(mappings) == wanted_maps, "private fold population differs")
    for experiment, rows in cases.items():
        report = result["experiments"][experiment]
        for row in rows:
            require(set(row["prediction"]) == models and set(row["alert_threshold"]) == models,
                    "row model population differs")
            require(type(row["fold"]) is int and 0 <= row["fold"] < spec["outer_folds"], "invalid outer fold")
            finite_number(row["high_count_threshold"], "invalid high-count threshold")
            for model in models:
                deviance(row["y"], row["prediction"][model])
                threshold = row["alert_threshold"][model]
                if model in {"shuffled_training_labels", "unavailable_oracle"}:
                    require(threshold is None, "diagnostic control acquired an alert policy")
                else:
                    finite_number(threshold, "invalid alert threshold")
        scenes, logs = {r["scene"] for r in rows}, {r["log"] for r in rows}
        require(len(scenes) == report["scenes"] and len(logs) == report["logs"], "group denominator differs")
        require(report["excluded_clock_anchors"] == len(data["frames"]) - len(rows), "excluded anchor denominator differs")
        require(sum(r["y"] for r in rows) == report["target_sum"], "experiment target sum differs")
        group = "log" if spec["split_unit"] == "logs" else "scene"
        ordered = np.random.default_rng(spec["seed"]).permutation(sorted({r[group] for r in rows}))
        assignment = {str(g): i % spec["outer_folds"] for i, g in enumerate(ordered)}
        require(all(r["fold"] == assignment[r[group]] for r in rows), "seeded outer assignment differs")
        for fold in report["folds"]:
            f = fold["fold"]
            train, test = [r for r in rows if r["fold"] != f], [r for r in rows if r["fold"] == f]
            require(train and test, "empty outer fold")
            mapping = mappings[(experiment, f)]
            for key, selected in (("train_scenes", train), ("test_scenes", test)):
                names = sorted({r["scene"] for r in selected})
                require(sorted(mapping[key]) == names, "fold complement differs")
                require(fold[key] == len(names), "fold scene denominator differs")
            require(fold["train_frames"] == len(train) and fold["test_frames"] == len(test), "fold frame denominator differs")
            require(fold["shared_collection_logs"] == len({r["log"] for r in train} & {r["log"] for r in test}),
                    "reported collection-log overlap differs")
        for key, unit in (("paired_scene_comparisons", "scene"), ("paired_log_comparisons", "collection_log")):
            for comparison in report[key].values():
                require(comparison["group_unit"] == unit and comparison["resamples"] == spec["bootstrap_resamples"]
                        and comparison["conditional_on_fixed_predictions"] is True, "paired interval metadata differs")
                same(comparison["relative_improvement"],
                     comparison["improvement"] / comparison["base_group_mean_deviance"], "paired relative point differs")
                require(len(comparison["percentile_95"]) == len(comparison["relative_percentile_95"]) == 2,
                        "paired interval endpoints missing")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "audit output already exists")
    root = Path(__file__).resolve().parents[2]
    spec = strict_json((args.run_dir / "spec.json").read_text())
    result = strict_json((args.run_dir / "result.json").read_text())
    models, spatial = declared_population(spec, result)
    canonical_spec = root / "research/predictive-monitor" / PROFILES[spec["artifact_id"]][0]
    require(sha(canonical_spec) == sha(args.run_dir / "spec.json") == result["spec_sha256"], "frozen specification differs")
    bindings = {root / p: digest for p, digest in spec["source_sha256"].items()}
    bindings.update({args.dataset: spec["dataset_sha256"], args.run_dir / "result.json": sha(args.run_dir / "result.json")})
    for name, record in result["private_outputs"].items():
        path = args.run_dir / name
        require(path.stat().st_size == record["bytes"], "private output size differs")
        bindings[path] = record["sha256"]
    for path, digest in bindings.items():
        require(sha(path) == digest, "bound input differs: " + path.name)
    cases, mappings = defaultdict(list), {}
    for line in (args.run_dir / "predictions.private.jsonl").read_text().splitlines():
        row = strict_json(line)
        cases[row["experiment"]].append(row)
    for line in (args.run_dir / "folds.private.jsonl").read_text().splitlines():
        row = strict_json(line)
        key = row["experiment"], row["fold"]
        require(key not in mappings, "duplicate private fold")
        mappings[key] = row
    with np.load(args.dataset, allow_pickle=False) as archive:
        data = {k: archive[k] for k in archive.files}
    check_rows_and_folds(spec, result, cases, mappings, data, models)
    if spatial:
        for name, report in result["experiments"].items():
            check_log_scene_band(cases[name], report["log_resampled_equal_scene_comparison"],
                                 spec["bootstrap_seed"], spec["bootstrap_resamples"])
    with tempfile.TemporaryDirectory(prefix="reiyah-monitor-numeric-") as temporary:
        numeric_output = Path(temporary) / "numeric.json"
        child = subprocess.run([sys.executable, "-B", str(root / "tools/measure/check_predictive_monitor_results.py"),
                                "--run-dir", str(args.run_dir), "--dataset", str(args.dataset),
                                "--output", str(numeric_output)], capture_output=True, text=True)
        require(child.returncode == 0 and numeric_output.is_file(), "numeric checker failed: " + child.stderr[-500:])
        numeric = strict_json(numeric_output.read_text())
        require(numeric["status"] == "pass" and {r["experiment"] for r in numeric["checked"]} == set(cases),
                "numeric checker completion differs")
    for path, digest in bindings.items():
        require(sha(path) == digest, "bound input changed during audit: " + path.name)
    report = {"artifact_id": "reiyah.predictive-monitor-completion-audit.0.1.0", "version": "0.1.0",
              "status": "pass", "lifecycle_status": "exploratory", "result_sha256": sha(args.run_dir / "result.json"),
              "spec_sha256": sha(canonical_spec), "auditor_sha256": sha(Path(__file__)),
              "numeric_audit": numeric, "complete_planned_experiments": sorted(cases),
              "log_resampled_equal_scene_checked": spatial,
              "limits": ["Computational audit of fixed shared predictions, not independent physical validation",
                         "Does not refit models, verify runtime timings or reconstruct internal tuning predictions",
                         "Producer process completion must also be checked against its retained process capture"]}
    args.output.write_text(json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError, ZeroDivisionError) as error:
        print(json.dumps({"status": "invalid", "diagnostic": str(error)}), file=sys.stderr)
        raise SystemExit(2)
