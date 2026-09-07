"""Completeness attacks use the retained aggregate runs, without private data."""
import copy
import json
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/measure"))
from audit_predictive_monitor_completion import (declared_population, check_log_scene_band,
                                                 finite_number, strict_json)


def fixture(profile="spatial"):
    version = "0.2.0" if profile == "spatial" else "0.1.0"
    spec = json.loads((ROOT / f"research/predictive-monitor/{version}/{profile}-analysis-spec.json").read_text())
    result = json.loads((ROOT / f"evidence/predictive-monitor/{profile}-evaluation-1-result.json").read_text())
    return spec, result


class CompletionControls(unittest.TestCase):
    def test_complete_retained_populations(self):
        for profile in ("scene", "log", "spatial"):
            spec, result = fixture(profile)
            declared_population(spec, result)

    def test_empty_and_partially_omitted_experiments(self):
        spec, result = fixture("scene")
        for experiments in ({}, {k: v for k, v in result["experiments"].items() if k != "y_h1000000"}):
            with self.assertRaisesRegex(ValueError, "planned experiment population"):
                declared_population(spec, dict(result, experiments=experiments))

    def test_model_or_comparison_cannot_disappear(self):
        for key, item, reason in (("models", "marginal_history", "planned model population"),
                                  ("paired_scene_comparisons", "spatial_history_vs_joint_history", "planned comparison population"),
                                  ("paired_log_comparisons", "spatial_history_vs_joint_history", "planned comparison population")):
            spec, result = fixture()
            del result["experiments"]["y_h1000000"][key][item]
            with self.assertRaisesRegex(ValueError, reason):
                declared_population(spec, result)

    def test_log_scene_band_cannot_disappear(self):
        spec, result = fixture()
        del result["experiments"]["y_h1000000"]["log_resampled_equal_scene_comparison"]
        with self.assertRaisesRegex(ValueError, "result presence"):
            declared_population(spec, result)

    def test_private_closure_cannot_disappear_or_escape(self):
        for name in ("predictions.private.jsonl", "folds.private.jsonl", "geometry.private.npz"):
            spec, result = fixture()
            del result["private_outputs"][name]
            with self.assertRaisesRegex(ValueError, "private output population"):
                declared_population(spec, result)
        spec, result = fixture()
        result["private_outputs"]["../external"] = {}
        with self.assertRaisesRegex(ValueError, "private output population"):
            declared_population(spec, result)

    def test_fold_omission_and_target_relabeling(self):
        for mutation, reason in ((lambda r: r["folds"].pop(), "fold population"),
                                 (lambda r: r.update(target="y_point"), "target or horizon"),
                                 (lambda r: r["folds"][0]["models"].pop("spatial_history"), "fold model population")):
            spec, result = fixture()
            mutation(result["experiments"]["y_h1000000"])
            with self.assertRaisesRegex(ValueError, reason):
                declared_population(spec, result)

    def test_invalid_json_and_thresholds(self):
        for text in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'):
            with self.assertRaises(ValueError):
                strict_json(text)
        for value in (None, True, "1", math.nan, math.inf):
            with self.assertRaises(ValueError):
                finite_number(value, "invalid threshold")

    def test_equal_scene_estimand_is_not_equal_log(self):
        # Two scenes in L1, one in L2. y=0 makes deviance exactly 2*p.
        # Scene loss reductions are 2, 2, -2, so the point is 2/3, not 0.
        rows = [{"scene": s, "log": l, "y": 0,
                 "prediction": {"joint_history": a, "spatial_history": b}}
                for s, l, a, b in (("a", "L1", 2., 1.), ("b", "L1", 2., 1.), ("c", "L2", 2., 3.))]
        record = {"sampling_unit": "collection_log", "estimand": "equal_scene_mean_deviance",
                  "logs": 2, "scenes": 3, "seed": 7, "resamples": 1000,
                  "conditional_on_fixed_predictions": True, "improvement": 2/3,
                  "relative_improvement": 1/6, "percentile_95": [-2., 2.],
                  "relative_percentile_95": [-.5, .5]}
        check_log_scene_band(rows, record, 7, 1000)
        for key, value in (("improvement", 0.), ("relative_percentile_95", [.5, .6]),
                           ("relative_percentile_95", []), ("estimand", "equal_log_mean_deviance")):
            with self.assertRaises(ValueError):
                check_log_scene_band(rows, dict(record, **{key: value}), 7, 1000)


if __name__ == "__main__":
    unittest.main()
