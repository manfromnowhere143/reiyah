"""Counterexamples for reference-cache selection; authored data, no benchmark."""
from decimal import Decimal
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_cache_selection as audit


POLICY = {"mapping": {"vehicle.car": "car"}, "ranges_m": {"car": 50},
          "validation_scene_names": ["scene-val"]}


def fixture(root, change=None):
    tables = {
        "scene.json": [{"token": "scene", "name": "scene-val"}],
        "sample.json": [{"token": s, "scene_token": "scene", "timestamp": t} for s, t in (("frame", 10), ("empty", 20))],
        "category.json": [{"token": "category", "name": "vehicle.car"}],
        "instance.json": [{"token": "instance", "category_token": "category"}],
        "sensor.json": [{"token": "sensor", "channel": "LIDAR_TOP"}],
        "calibrated_sensor.json": [{"token": "calibration", "sensor_token": "sensor"}],
        "sample_data.json": [{"token": "sd-" + s, "sample_token": s, "is_key_frame": True,
                              "calibrated_sensor_token": "calibration", "ego_pose_token": "pose-" + s} for s in ("frame", "empty")],
        "ego_pose.json": [{"token": "pose-" + s, "translation": [0, 0, 0]} for s in ("frame", "empty")],
        "sample_annotation.json": [{"token": aid, "sample_token": "frame", "instance_token": "instance",
                                    "translation": [x, 0, 0], "num_lidar_pts": 0, "num_radar_pts": 0}
                                   for aid, x in (("inside", 1), ("boundary", 50))],
    }
    cache = [{"ann_token": "inside", "sample_token": "frame", "instance_token": "instance", "ts_us": 10,
              "cls": "car", "raw_cls": "vehicle.car", "nl": 0, "nr": 0, "xy": [1, 0], "ego_xy": [0, 0]}]
    if change:
        change(tables, cache)
    with tarfile.open(root / "meta.tgz", "w:gz") as archive:
        for name, rows in tables.items():
            raw = json.dumps(rows).encode()
            info = tarfile.TarInfo("v1.0-trainval/" + name)
            info.size = len(raw)
            archive.addfile(info, io.BytesIO(raw))
    (root / "gt_val_cache.json").write_text(json.dumps(cache))
    (root / "predictions").mkdir()
    for channel in ("mapillary", "megvii"):
        (root / "predictions" / (channel + "_val.json")).write_text(json.dumps({"results": {"frame": [], "empty": []}}))


class CacheSelectionTests(unittest.TestCase):
    def test_range_boundary_is_strict_and_exact(self):
        self.assertEqual(audit.classify("vehicle.car", [50, 0], [0, 0], POLICY)[0], "outside_class_range")
        self.assertEqual(audit.classify("vehicle.car", [Decimal("49.99999999999999999999"), 0], [0, 0], POLICY)[0], "included")
        self.assertEqual(audit.classify("vehicle.car", [150, 10], [100, 10], POLICY)[0], "outside_class_range")

    def test_unmapped_category_is_not_an_included_negative(self):
        self.assertEqual(audit.classify("human.pedestrian.stroller", [0, 0], [0, 0], POLICY), ("unmapped_category", None, None))

    def test_id_swap_refutes_equal_counts(self):
        result = audit.membership_result({"a", "b"}, {"a", "c"}, 0)
        self.assertEqual(result["status"], "contradicted")
        self.assertEqual(result["expected_absent_from_cache"], 1)
        self.assertEqual(result["cache_absent_from_expected"], 1)

    def test_zero_point_selection_and_empty_frame_census_survive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); fixture(root); out = root / "out"; out.mkdir()
            result = audit.compute(root, out, POLICY)
        self.assertEqual(result["annotation_membership"]["status"], "supported")
        self.assertEqual(result["included_zero_point_annotations"], 1)
        self.assertEqual(result["validation_frame_count"], 2)
        self.assertEqual(result["frames_without_selected_annotations"], 1)
        self.assertIsNone(result["physical_false_positive_rate"])

    def test_correct_ids_do_not_hide_wrong_cache_geometry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); fixture(root, lambda tables, cache: cache[0].update(ego_xy=[1, 0]))
            out = root / "out"; out.mkdir(); result = audit.compute(root, out, POLICY)
        self.assertEqual(result["annotation_membership"]["status"], "contradicted")
        self.assertEqual(result["annotation_membership"]["cache_metadata_mismatches"], 1)

    def test_missing_pose_is_invalid_not_empty_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); fixture(root, lambda tables, cache: tables["ego_pose.json"].pop())
            out = root / "out"; out.mkdir()
            with self.assertRaisesRegex(ValueError, "missing keyframe ego pose"):
                audit.compute(root, out, POLICY)
            self.assertFalse((out / "result.json").exists())

    def test_duplicate_keyframe_cannot_silently_select_last_pose(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root, lambda tables, cache: tables["sample_data.json"].append(dict(tables["sample_data.json"][0])))
            out = root / "out"; out.mkdir()
            with self.assertRaisesRegex(ValueError, "duplicate token"):
                audit.compute(root, out, POLICY)

    def test_split_reconstruction_never_executes_python(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); historical = root / "old.py"
            (root / "P03.payload").write_text("def category_to_detection_name(name):\n detection_mapping = {'vehicle.car': 'car'}\n")
            (root / "P02.payload").write_text('{"class_range":{"car":50}}')
            (root / "P06.payload").write_text("raise RuntimeError('must not execute')\nval = ['scene-val']\n")
            historical.write_text("val = ['scene-val']\n")
            self.assertEqual(audit.policy_from_sources(root, historical)["validation_scene_names"], ["scene-val"])
            historical.write_text("val = ['another-scene']\n")
            with self.assertRaisesRegex(ValueError, "split differ"):
                audit.policy_from_sources(root, historical)

    def test_cli_rejects_duplicate_source_ids_before_creating_a_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); ledger = root / "ledger.json"
            ledger.write_text(json.dumps({"entries": [{"source_id": "P02"}] * 2}))
            out = root / "out"
            proc = subprocess.run([sys.executable, "-B", audit.__file__, "--data-root", str(root),
                                   "--source-dir", str(root), "--source-ledger", str(ledger),
                                   "--expected-inputs", str(root / "absent.json"), "--output-dir", str(out)], capture_output=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(proc.stdout, b"")
            self.assertFalse(out.exists())
            self.assertIn(b"incomplete primary-source closure", proc.stderr)


if __name__ == "__main__":
    unittest.main()
