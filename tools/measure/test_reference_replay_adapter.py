"""Counterexamples for source identity and exact-number preservation in the adapter."""
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import replay_reference_population_audit as adapter
import audit_reference_frame_coverage as coverage


class TinyChunks(io.BytesIO):
    def read(self, size=-1):
        return super().read(min(size, 3) if size >= 0 else 3)


class ReferenceReplayAdapterTests(unittest.TestCase):
    def write_source(self, root, wrong_xy=False):
        (root / "predictions").mkdir()
        cache = [{"sample_token": "sample1", "ann_token": "a1", "ts_us": 100,
                  "xy": [8 if wrong_xy else 5, 0]}]
        (root / "gt_val_cache.json").write_text(json.dumps(cache))
        tables = {
            "sample.json": [{"token": "sample1", "timestamp": 100}],
            "sample_annotation.json": [{"sample_token": "sample1", "token": "a1", "translation": [5, 0, 0]},
                                       {"sample_token": "sample1", "token": "a2", "translation": [55, 0, 0]}],
        }
        with tarfile.open(root / "meta.tgz", "w:gz") as archive:
            for name, rows in tables.items():
                raw = json.dumps(rows).encode()
                info = tarfile.TarInfo("v1.0-trainval/" + name)
                info.size = len(raw)
                archive.addfile(info, io.BytesIO(raw))
        predictions = {"results": {"sample1": [
            {"sample_token": "sample1", "translation": [55.2, 0, 0], "detection_score": 0.3, "detection_name": "car"},
            {"sample_token": "sample1", "translation": [75, 0, 0], "detection_score": 0.29, "detection_name": "car"},
        ]}}
        for name in ("mapillary_val.json", "megvii_val.json"):
            (root / "predictions" / name).write_text(json.dumps(predictions))
        expected = {"inputs": {name: {"bytes": (root / name).stat().st_size,
                     "sha256": hashlib.sha256((root / name).read_bytes()).hexdigest()} for name in adapter.INPUT_NAMES}}
        path = root / "expected.json"
        path.write_text(json.dumps(expected))
        return path

    def test_incremental_reader_preserves_decimal_tokens_and_utf8(self):
        rows = list(adapter.array_rows(TinyChunks('[{"x":55.000000000000001,"label":"é"}]'.encode())))
        self.assertEqual(rows[0]["x"], Decimal("55.000000000000001"))
        self.assertEqual(adapter.decimal_xy([rows[0]["x"], 0]), ["55.000000000000001", "0"])

    def test_reader_rejects_truncation_duplicates_and_nonfinite(self):
        for raw in (b'[{"x":1}', b'[{},]', b'[{"x":1,"x":2}]', b'[{}]{}', b'[{"x":NaN}]'):
            with self.assertRaises(ValueError):
                list(adapter.array_rows(TinyChunks(raw)))

    def test_cached_coordinates_must_match_original_annotation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_source(root, wrong_xy=True)
            with self.assertRaisesRegex(ValueError, "position"):
                adapter.build_references(root)

    def test_actual_adapter_preserves_threshold_and_source_membership(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected = self.write_source(root)
            output = root / "output"
            proc = subprocess.run([sys.executable, "-B", str(Path(adapter.__file__)), "--data-root", str(root),
                                   "--output-dir", str(output), "--expected-inputs", str(expected)], capture_output=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            result = json.loads(proc.stdout)
            for channel in ("camera", "lidar"):
                self.assertEqual(result["channels"][channel]["selected_predictions"], 1)
                self.assertEqual(result["channels"][channel]["below_threshold"], 1)
                self.assertEqual(result["channels"][channel]["counts"]["excluded_reference_near"], 1)
                self.assertIsNone(result["channels"][channel]["physical_false_positive_rate"])

    def test_changed_input_fails_before_output_identity_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected = self.write_source(root)
            (root / "gt_val_cache.json").write_text("[]")
            output = root / "output"
            proc = subprocess.run([sys.executable, "-B", str(Path(adapter.__file__)), "--data-root", str(root),
                                   "--output-dir", str(output), "--expected-inputs", str(expected)], capture_output=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertFalse(output.exists())
            self.assertEqual(proc.stdout, b"")

    def test_frame_cache_does_not_define_the_prediction_opportunity_universe(self):
        samples = {"with-object": {"scene_token": "scene1"},
                   "without-cached-object": {"scene_token": "scene1"}}
        result = coverage.frame_universe({"with-object"}, set(samples), samples)
        self.assertEqual(result["omitted_cache_samples"], 1)
        self.assertTrue(result["same_scene_universe"])
        self.assertTrue(result["prediction_keys_equal_metadata_scene_census"])

    def test_prediction_keys_are_checked_against_a_separate_frame_census(self):
        samples = {"frame1": {"scene_token": "scene1"}, "frame2": {"scene_token": "scene1"}}
        result = coverage.frame_universe({"frame1"}, {"frame1"}, samples)
        self.assertFalse(result["prediction_keys_equal_metadata_scene_census"])
        with self.assertRaisesRegex(ValueError, "metadata"):
            coverage.frame_universe({"frame1"}, {"frame1", "forged"}, samples)


if __name__ == "__main__":
    unittest.main()
