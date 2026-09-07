#!/usr/bin/env python3
"""Scene-separated, nested evaluation of bounded output-summary monitors."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import roc_auc_score
from threadpoolctl import threadpool_limits

from build_predictive_monitor_dataset import require, read_json
from replay_reference_population_audit import digest


def assignments(groups, folds, seed):
    unique = np.unique(groups)
    require(len(unique) >= folds, "insufficient independent split groups")
    order = np.random.default_rng(seed).permutation(unique)
    return {str(g): i % folds for i, g in enumerate(order)}


def separated_folds(groups, folds, seed):
    mapping = assignments(groups, folds, seed)
    index = np.asarray([mapping[str(g)] for g in groups])
    for fold in range(folds):
        train, test = np.flatnonzero(index != fold), np.flatnonzero(index == fold)
        require(len(train) and len(test) and not set(groups[train]).intersection(groups[test]), "overlapping or empty split")
        yield fold, train, test


def history_matrix(X, scenes, times):
    """Missing history is NaN; ages disclose its presence. No forward access."""
    result = np.full((len(X), 3 * X.shape[1] + 2), np.nan)
    result[:, :X.shape[1]] = X
    for scene in np.unique(scenes):
        indices = np.flatnonzero(scenes == scene)
        indices = indices[np.argsort(times[indices], kind="stable")]
        require(np.all(np.diff(times[indices]) > 0), "history time is not strictly increasing")
        for lag in (1, 2):
            current, past = indices[lag:], indices[:-lag]
            result[current, lag*X.shape[1]:(lag+1)*X.shape[1]] = X[past]
            result[current, 3*X.shape[1] + lag - 1] = (times[current] - times[past]) / 1e6
    return result


def targets_at_horizon(scenes, times, horizon_us, tolerance_us):
    require(horizon_us >= 0 and tolerance_us >= 0, "invalid target clock")
    if horizon_us == 0:
        return np.arange(len(times))
    target = np.full(len(times), -1, dtype=np.int64)
    for scene in np.unique(scenes):
        indices = np.flatnonzero(scenes == scene)
        indices = indices[np.argsort(times[indices], kind="stable")]
        require(np.all(np.diff(times[indices]) > 0), "target clock is not strictly increasing")
        for i, current in enumerate(indices):
            future = indices[i+1:]
            if len(future):
                errors = np.abs(times[future] - times[current] - horizon_us)
                j = int(np.argmin(errors))
                if errors[j] <= tolerance_us:
                    target[current] = future[j]
    return target


def losses(y, p):
    require(y.shape == p.shape and np.isfinite(y).all() and np.isfinite(p).all(), "invalid metric input")
    require(np.all(y >= 0) and np.all(p > 0), "count loss requires nonnegative outcomes and positive predictions")
    term = np.zeros(len(y))
    positive = y > 0
    term[positive] = y[positive] * np.log(y[positive] / p[positive])
    return 2 * (term - y + p)


def group_means(values, groups):
    return np.asarray([float(np.mean(values[groups == g])) for g in np.unique(groups)])


def ratio(a, b):
    return float(a / b) if b else None


def metrics(y, p, groups, alert, high):
    dev = losses(y, p)
    grouped = group_means(dev, groups)
    return {"frames": len(y), "scenes": len(np.unique(groups)), "deviance_frame_mean": float(dev.mean()),
        "deviance_scene_mean": float(grouped.mean()), "mae": float(np.abs(y-p).mean()),
        "observed_mean": float(y.mean()), "predicted_mean": float(p.mean()),
        "predicted_to_observed_count_ratio": ratio(p.sum(), y.sum()),
        "high_count_auc": float(roc_auc_score(high, p)) if len(np.unique(high)) == 2 else None,
        "alert_fraction": float(alert.mean()), "miss_fraction_in_alerts": ratio(y[alert].sum(), y.sum()),
        "misses_outside_alerts": int(y[~alert].sum()), "misses_total": int(y.sum()),
        "mean_misses_unflagged": float(y[~alert].mean()) if (~alert).any() else None,
        "high_count_false_alarm_rate": ratio(np.count_nonzero(alert & ~high), np.count_nonzero(~high)),
        "scene_loss_median": float(np.median(grouped)), "scene_loss_p90": float(np.quantile(grouped, .9)),
        "scene_loss_max": float(grouped.max())}


def new_model(config, seed):
    return HistGradientBoostingRegressor(loss="poisson", max_iter=200, learning_rate=.05,
        early_stopping=False, random_state=seed, **config)


def fit_predict(X, y, train, test, config, seed):
    require(np.isfinite(y[train]).all() and np.all(y[train] >= 0) and y[train].sum() > 0,
            "training target has no positive count or is invalid")
    start = time.perf_counter()
    model = new_model(config, seed).fit(X[train], y[train])
    fitted = time.perf_counter()
    p = model.predict(X[test])
    require(np.isfinite(p).all() and np.all(p > 0), "invalid model prediction")
    return p, {"fit_seconds": fitted - start, "predict_seconds": time.perf_counter() - fitted,
               "prediction_rows": len(test)}


def nested_predict(X, y, scenes, train, test, spec, seed, split_groups=None):
    candidates = []
    inner_groups = (scenes if split_groups is None else split_groups)[train]
    for ci, config in enumerate(spec["tree_candidates"]):
        oof = np.full(len(train), np.nan)
        timings = []
        for fold, itr, ite in separated_folds(inner_groups, spec["inner_folds"], seed):
            p, timing = fit_predict(X, y, train[itr], train[ite], config, seed + fold)
            oof[ite] = p
            timings.append(timing)
        require(np.isfinite(oof).all(), "incomplete inner predictions")
        score = float(group_means(losses(y[train], oof), scenes[train]).mean())
        candidates.append((score, ci, oof, timings))
    score, ci, oof, inner_timings = min(candidates, key=lambda v: (v[0], v[1]))
    p, timing = fit_predict(X, y, train, test, spec["tree_candidates"][ci], seed)
    threshold = float(np.quantile(oof, spec["alert_quantile"], method="higher"))
    return p, threshold, {"candidate_index": ci, "inner_scene_deviance": [v[0] for v in candidates],
                          "inner_selected_timings": inner_timings, "refit_timing": timing,
                          "inner_groups": len(np.unique(inner_groups))}


def paired_band(base, candidate, scenes, seed, repetitions, unit="scene"):
    a, b = group_means(base, scenes), group_means(candidate, scenes)
    require(len(a) == len(b) and len(a), "incomplete paired groups")
    draws = np.random.default_rng(seed).integers(0, len(a), size=(repetitions, len(a)))
    delta = a - b
    band = np.quantile(delta[draws].mean(axis=1), [.025, .975]).tolist()
    rel = 1 - b[draws].mean(axis=1) / a[draws].mean(axis=1) if np.all(a[draws].mean(axis=1) > 0) else None
    return {"groups": len(a), "group_unit": unit,
            "base_group_mean_deviance": float(a.mean()), "candidate_group_mean_deviance": float(b.mean()),
            "improvement": float(delta.mean()), "percentile_95": band,
            "relative_improvement": ratio(delta.mean(), a.mean()),
            "relative_percentile_95": np.quantile(rel, [.025, .975]).tolist() if rel is not None else None,
            "resamples": repetitions, "conditional_on_fixed_predictions": True}


def evaluate(data, spec, output):
    names = data["feature_names"].tolist()
    marginal_cols = [i for i, name in enumerate(names) if not name.startswith("joint.")]
    density_cols = [names.index(n) for n in ("camera.count", "lidar.count")]
    scenes, times = data["scenes"], data["timestamps"]
    X = data["X"]
    variants = {"density_current": X[:, density_cols], "marginal_current": X[:, marginal_cols],
                "joint_current": X, "marginal_history": history_matrix(X[:, marginal_cols], scenes, times),
                "joint_history": history_matrix(X, scenes, times)}
    variants = {name: variants[name] for name in spec["feature_variants"]}
    all_results, private_rows, private_folds = {}, [], []
    for horizon in spec["horizons_us"]:
        target = targets_at_horizon(scenes, times, horizon, spec["horizon_tolerance_us"])
        anchors = np.flatnonzero(target >= 0)
        dest = target[anchors]
        g = scenes[anchors]
        split_groups = data[spec["split_unit"]][anchors]
        require(np.array_equal(g, scenes[dest]), "target crosses scene boundary")
        offset = times[dest] - times[anchors]
        Xs = {name: values[anchors] for name, values in variants.items()}
        union = X[anchors, names.index("joint.union")]
        for target_name in spec["targets"]:
            y = data[target_name][dest].astype(np.float64)
            experiment = f"{target_name}_h{horizon}"
            predictions = {name: np.full(len(y), np.nan) for name in
                (*Xs, "constant", "proportional_union", "shuffled_training_labels", "unavailable_oracle")}
            alert_thresholds = {name: np.full(len(y), np.nan) for name in predictions}
            high_threshold = np.full(len(y), np.nan)
            fold_ids = np.full(len(y), -1)
            fold_results = []
            oracle = data["n_reference" if target_name == "y" else "n_point"][anchors] if horizon == 0 else data[target_name][anchors]
            oracle_X = np.column_stack([Xs["joint_history"], oracle])
            for fold, train, test in separated_folds(split_groups, spec["outer_folds"], spec["seed"]):
                require(not set(g[train]).intersection(g[test]), "split crosses scene boundary")
                q = float(np.quantile(y[train], .75, method="higher"))
                high_threshold[test] = q
                fold_ids[test] = fold
                training_logs, test_logs = set(data["logs"][anchors[train]]), set(data["logs"][anchors[test]])
                row = {"fold": fold, "train_scenes": len(np.unique(g[train])), "test_scenes": len(np.unique(g[test])),
                       "train_frames": len(train), "test_frames": len(test), "high_count_threshold": q,
                       "shared_collection_logs": len(training_logs & test_logs), "models": {}}
                for name, values in Xs.items():
                    p, threshold, fit_record = nested_predict(values, y, g, train, test, spec, spec["seed"] + 100 * fold, split_groups)
                    predictions[name][test] = p
                    alert_thresholds[name][test] = threshold
                    row["models"][name] = {**fit_record, "alert_threshold": threshold,
                        "test": metrics(y[test], p, g[test], p > threshold, y[test] >= q)}
                    print(f"{experiment} fold {fold} {name}: scene deviance {row['models'][name]['test']['deviance_scene_mean']:.6f}", flush=True)
                mean = float(y[train].mean())
                k = float(y[train].sum() / union[train].sum()) if union[train].sum() > 0 else None
                controls = {
                    "constant": (np.full(len(test), mean), mean),
                    "proportional_union": (np.maximum(1e-6, k * union[test]) if k is not None else np.full(len(test), mean),
                        float(np.quantile(np.maximum(1e-6, k*union[train]), .8, method="higher")) if k is not None else mean),
                }
                shuffled = y.copy()
                shuffled[train] = np.random.default_rng(spec["seed"] + fold + 700).permutation(y[train])
                for name, values, label in (("shuffled_training_labels", Xs["joint_history"], shuffled),
                                            ("unavailable_oracle", oracle_X, y)):
                    p, timing = fit_predict(values, label, train, test, spec["tree_candidates"][1], spec["seed"] + fold)
                    # These diagnostic controls do not have fitted alert policies.
                    predictions[name][test] = p
                    row["models"][name] = {"refit_timing": timing, "alert_policy": "not_evaluated",
                        "scene_deviance": float(group_means(losses(y[test], p), g[test]).mean())}
                for name, (p, threshold) in controls.items():
                    predictions[name][test] = p
                    alert_thresholds[name][test] = threshold
                    row["models"][name] = {"alert_threshold": threshold,
                        "test": metrics(y[test], p, g[test], p > threshold, y[test] >= q)}
                fold_results.append(row)
                private_folds.append({"experiment": experiment, "fold": fold,
                    "train_scenes": sorted(set(g[train].tolist())), "test_scenes": sorted(set(g[test].tolist()))})
            require(np.all(fold_ids >= 0), "unassigned outer row")
            model_results = {}
            for name, p in predictions.items():
                require(np.isfinite(p).all() and np.all(p > 0), "incomplete outer predictions")
                has_alerts = np.isfinite(alert_thresholds[name]).all()
                flags = p > alert_thresholds[name] if has_alerts else np.zeros(len(y), dtype=bool)
                metric = metrics(y, p, g, flags, y >= high_threshold)
                if not has_alerts:
                    for field in ("alert_fraction", "miss_fraction_in_alerts", "misses_outside_alerts", "mean_misses_unflagged", "high_count_false_alarm_rate"):
                        metric[field] = None
                    metric["alert_policy"] = "not_evaluated"
                metric["location_groups"] = {}
                for location in np.unique(data["locations"][anchors]):
                    m = data["locations"][anchors] == location
                    metric["location_groups"][str(location)] = {"frames": int(m.sum()), "scenes": len(np.unique(g[m])),
                        "deviance_scene_mean": float(group_means(losses(y[m], p[m]), g[m]).mean()),
                        "mae": float(np.abs(y[m] - p[m]).mean())}
                model_results[name] = metric
            comparisons, log_comparisons = {}, {}
            pairs = (("marginal_history", "joint_history"), ("marginal_current", "joint_current"),
                     ("marginal_current", "marginal_history"), ("density_current", "marginal_current"),
                     ("proportional_union", "joint_history"))
            for base, candidate in pairs:
                if base not in predictions or candidate not in predictions:
                    continue
                comparisons[candidate + "_vs_" + base] = paired_band(losses(y, predictions[base]), losses(y, predictions[candidate]),
                    g, spec["bootstrap_seed"], spec["bootstrap_resamples"])
                log_comparisons[candidate + "_vs_" + base] = paired_band(losses(y, predictions[base]), losses(y, predictions[candidate]),
                    data["logs"][anchors], spec["bootstrap_seed"], spec["bootstrap_resamples"], unit="collection_log")
            report = {"frames": len(anchors), "excluded_clock_anchors": len(scenes) - len(anchors),
                "scenes": len(np.unique(g)), "logs": len(np.unique(data["logs"][anchors])),
                "horizon_us": horizon, "split_unit": spec["split_unit"],
                "actual_target_offset_us": {"min": int(offset.min()), "median": float(np.median(offset)), "max": int(offset.max())},
                "target": target_name, "target_sum": int(y.sum()), "models": model_results,
                "paired_scene_comparisons": comparisons, "paired_log_comparisons": log_comparisons, "folds": fold_results}
            all_results[experiment] = report
            for i, a in enumerate(anchors):
                private_rows.append({"experiment": experiment, "frame": str(data["frames"][a]), "target_frame": str(data["frames"][dest[i]]),
                    "scene": str(g[i]), "log": str(data["logs"][a]), "fold": int(fold_ids[i]), "y": int(y[i]),
                    "high_count_threshold": float(high_threshold[i]),
                    "prediction": {name: float(p[i]) for name, p in predictions.items()},
                    "alert_threshold": {name: float(p[i]) if np.isfinite(p[i]) else None for name, p in alert_thresholds.items()}})
            (output / f"{experiment}.json").write_text(json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n")
    for name, rows in (("predictions.private.jsonl", private_rows), ("folds.private.jsonl", private_folds)):
        with (output / name).open("w") as stream:
            for row in rows:
                stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
    return all_results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    spec = read_json(args.spec)
    root = Path(__file__).resolve().parents[2]
    require(not args.output_dir.exists(), "output identity already exists")
    require(digest(args.dataset) == spec["dataset_sha256"], "dataset digest differs")
    for relative, expected in spec["source_sha256"].items():
        require(digest(root / relative) == expected, "source digest differs: " + relative)
    require(sklearn.__version__ == spec["sklearn_version"] and np.__version__ == spec["numpy_version"], "library version differs")
    args.output_dir.mkdir()
    (args.output_dir / "spec.json").write_bytes(args.spec.read_bytes())
    with np.load(args.dataset, allow_pickle=False) as raw:
        data = {k: raw[k] for k in raw.files}
    with threadpool_limits(limits=1):
        results = evaluate(data, spec, args.output_dir)
    for relative, expected in spec["source_sha256"].items():
        require(digest(root / relative) == expected, "source changed during fitting: " + relative)
    require(digest(args.dataset) == spec["dataset_sha256"], "dataset changed during fitting")
    report = {"artifact_id": "reiyah.predictive-monitor-evaluation.0.1.0", "version": "0.1.0", "lifecycle_status": "exploratory",
              "spec_sha256": digest(args.spec), "experiments": results,
              "split_unit": spec["split_unit"],
              "private_outputs": {p.name: {"sha256": digest(p), "bytes": p.stat().st_size} for p in args.output_dir.glob("*.private.jsonl")},
              "physical_failure_rate": None, "online_warning_lead_time": None, "safety_benefit": None,
              "limits": ["Already explored benchmark; scene-separated interpolation, not new-domain confirmation",
                         "Fixed-prediction scene bootstrap excludes training and shared-log dependence uncertainty",
                         "Targets are misses relative to the selected cache, not independently observed physical hazards",
                         "Metadata-time feature prefixes do not establish detector output availability or latency"]}
    (args.output_dir / "result.json").write_text(json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": "completed", "experiments": list(results), "result_sha256": digest(args.output_dir / "result.json")}), flush=True)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(json.dumps({"status": "invalid", "diagnostic": str(exc)}), file=sys.stderr)
        raise SystemExit(2)
