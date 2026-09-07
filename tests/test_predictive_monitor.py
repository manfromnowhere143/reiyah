"""Authored adversarial controls for reference, time and evaluation separation."""
import math
from decimal import Decimal
from pathlib import Path
import sys
import unittest

import numpy as np
from threadpoolctl import threadpool_limits

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "measure"))
from build_predictive_monitor_dataset import (chains, coverage, greedy_pairs, match_reference,
                                              number, output_features)
from evaluate_predictive_monitor import (group_means, history_matrix, losses, metrics,
                                         nested_predict, paired_band, separated_folds,
                                         targets_at_horizon)
from check_predictive_monitor_results import audit_model, auc


class DatasetControls(unittest.TestCase):
    def test_missing_is_not_empty(self):
        coverage({"a": []}, {"a"})
        for bad in ({}, {"a": None}, {"a": [], "b": []}):
            with self.assertRaises(ValueError):
                coverage(bad, {"a"})

    def test_numeric_unknowns_rejected(self):
        self.assertEqual(number(Decimal('.3')), .3)
        for value in (None, True, "1", math.nan, math.inf):
            with self.assertRaises(ValueError):
                number(value)

    def test_geometry_and_ties(self):
        # Stable source tie selects the first; exact 2 m never matches.
        a = [("car", .7, 0., 0.), ("car", .7, .5, 0.)]
        self.assertEqual(greedy_pairs(a, [("car", 0., 1., 0.)]), [(0, 0)])
        self.assertEqual(greedy_pairs(a[:1], [("car", 0., 2., 0.)]), [])
        self.assertEqual(greedy_pairs(a[:1], [("bus", 0., 0., 0.)]), [])
        self.assertEqual(greedy_pairs(a[:1], [("car", 0., -1., 0.), ("car", 0., 1., 0.)]), [(0, 0)])

    def test_prediction_range_boundary(self):
        target = [("car", 0., 49.9, 0.)]
        self.assertEqual(match_reference([("car", .8, 50., 0.)], target, (0., 0.)), set())
        self.assertEqual(match_reference([("car", .8, 49.99, 0.)], target, (0., 0.)), {0})

    def test_unknown_summaries_remain_unknown(self):
        f = output_features([], [], (0., 0.))
        self.assertEqual(f["camera.count"], 0)
        self.assertTrue(math.isnan(f["camera.score_mean"]))
        self.assertTrue(math.isnan(f["joint.agreement"]))
        self.assertTrue(math.isnan(f["joint.paired_score_mean"]))

    def test_reference_change_cannot_change_output_features(self):
        camera, lidar = [("car", .8, 0., 0.)], [("car", .7, 1., 0.)]
        before = output_features(camera, lidar, (0., 0.))
        self.assertEqual(match_reference(camera, [("car", 0., 0., 0.)], (0., 0.)), {0})
        self.assertEqual(match_reference(camera, [], (0., 0.)), set())
        after = output_features(camera, lidar, (0., 0.))
        np.testing.assert_equal(list(before.values()), list(after.values()))

    def test_broken_scene_chain_rejected(self):
        scene = {"s": {"nbr_samples": 2, "first_sample_token": "a", "last_sample_token": "b"}}
        samples = {"a": {"timestamp": 1, "scene_token": "s", "prev": "", "next": "b"},
                   "b": {"timestamp": 2, "scene_token": "s", "prev": "a", "next": ""}}
        self.assertEqual(chains(samples, scene), ["a", "b"])
        samples["b"]["prev"] = ""
        with self.assertRaises(ValueError):
            chains(samples, scene)


class TemporalAndMetricControls(unittest.TestCase):
    def test_separate_auc_handles_ties_and_undefinedness(self):
        self.assertEqual(auc([False, True, True], [1.,1.,2.]), .75)
        self.assertIsNone(auc([True,True], [1.,2.]))

    def test_separate_reaggregation_rejects_forged_result(self):
        rows = [{"scene": s,"y":y,"prediction":{"m":p},"high_count_threshold":1,
                 "alert_threshold":{"m":t}} for s,y,p,t in
                (("a",0,1.,.5),("b",1,1.,1.),("b",2,2.,1.5))]
        report = {"frames":3,"scenes":2,"deviance_frame_mean":2/3,"deviance_scene_mean":1.,
                  "mae":1/3,"observed_mean":1.,"predicted_mean":4/3,"predicted_to_observed_count_ratio":4/3,
                  "high_count_auc":.75,"alert_fraction":2/3,"miss_fraction_in_alerts":2/3,
                  "misses_outside_alerts":1,"mean_misses_unflagged":1.,"high_count_false_alarm_rate":1.,"misses_total":3}
        audit_model(rows,"m",report)
        for field,value in (("deviance_frame_mean",0.),("misses_outside_alerts",0),
                            ("frames",2),("miss_fraction_in_alerts",None)):
            with self.assertRaises(ValueError):
                audit_model(rows,"m",dict(report,**{field:value}))

    def test_future_outputs_cannot_change_past_history(self):
        x = np.arange(8., dtype=float).reshape(4, 2)
        scene, time = np.array(["s"]*4), np.arange(4)*500000
        a = history_matrix(x, scene, time)
        x[3] = 10000
        b = history_matrix(x, scene, time)
        np.testing.assert_equal(a[:3], b[:3])
        self.assertTrue(np.isnan(a[0, 2:]).all())
        self.assertEqual(a[2, -1], 1.)

    def test_history_never_crosses_scene(self):
        a = history_matrix(np.arange(4.).reshape(4, 1), np.array(["a", "a", "b", "b"]), np.array([1,2,1,2]))
        self.assertTrue(np.isnan(a[2, 1:]).all())

    def test_future_joins_and_gaps(self):
        scenes = np.array(["a"]*4 + ["b"])
        times = np.array([0, 500000, 1000000, 2100000, 1000000])
        got = targets_at_horizon(scenes, times, 1000000, 150000)
        np.testing.assert_equal(got, [2, -1, 3, -1, -1])
        np.testing.assert_equal(targets_at_horizon(scenes, times, 0, 0), np.arange(5))

    def test_all_folds_exclude_all_test_scenes(self):
        groups = np.repeat(np.array(["a","b","c","d","e","f"]), [1,2,3,4,5,6])
        seen = []
        for _, train, test in separated_folds(groups, 3, 7):
            self.assertFalse(set(groups[train]) & set(groups[test]))
            seen.extend(test.tolist())
        self.assertEqual(sorted(seen), list(range(len(groups))))

    def test_log_split_keeps_related_scenes_together(self):
        scenes = np.array(["a", "b", "c", "d", "e", "f"])
        logs = np.array(["drive1", "drive1", "drive2", "drive2", "drive3", "drive3"])
        for _, train, test in separated_folds(logs, 3, 8):
            self.assertFalse(set(logs[train]) & set(logs[test]))
            self.assertFalse(set(scenes[train]) & set(scenes[test]))

    def test_proper_loss_and_unequal_scene_weights(self):
        y, p = np.array([0., 1., 2.]), np.array([1., 1., 2.])
        np.testing.assert_allclose(losses(y, p), [2., 0., 0.])
        np.testing.assert_allclose(group_means(losses(y,p), np.array(["a","b","b"])), [2.,0.])
        with self.assertRaises(ValueError):
            losses(y, np.array([0., 1., 2.]))

    def test_undefined_metrics_are_null(self):
        m = metrics(np.zeros(3), np.ones(3), np.array(["a","b","b"]),
                    np.zeros(3, dtype=bool), np.zeros(3, dtype=bool))
        self.assertIsNone(m["miss_fraction_in_alerts"])
        self.assertIsNone(m["predicted_to_observed_count_ratio"])
        self.assertIsNone(m["high_count_auc"])
        self.assertEqual(m["frames"], 3)

    def test_pairing_not_difference_of_unpaired_intervals(self):
        g = np.array(["a","b","c"])
        a, b = np.array([100., 10., 1.]), np.array([99., 9., 0.])
        r = paired_band(a, b, g, 1, 100)
        self.assertEqual(r["percentile_95"], [1.,1.])

    def test_test_labels_cannot_change_fit_or_alert_threshold(self):
        g = np.repeat(np.array(["a","b","c","d","e"]), 8)
        x = np.arange(40., dtype=float).reshape(-1,1)
        y = (np.arange(40)%4 + 1).astype(float)
        train, test = np.arange(32), np.arange(32,40)
        spec = {"inner_folds": 3, "alert_quantile": .8,
                "tree_candidates": [{"max_leaf_nodes": 3, "min_samples_leaf": 2, "l2_regularization": 1.}]}
        with threadpool_limits(limits=1):
            a, ta, _ = nested_predict(x, y, g, train, test, spec, 2)
            y[test] = 100000
            b, tb, _ = nested_predict(x, y, g, train, test, spec, 2)
        np.testing.assert_array_equal(a,b)
        self.assertEqual(ta,tb)


if __name__ == "__main__":
    unittest.main()
