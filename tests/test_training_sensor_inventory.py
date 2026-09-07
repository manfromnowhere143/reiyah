"""Authored counterexamples for incomplete or misleading file-availability reports."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "measure"))
import inventory_training_sensors as inventory


def fixture():
    channels = inventory.CHANNELS
    tables = {
        "scene.json": [{"token": "s" + split, "name": split, "log_token": "l" + split, "nbr_samples": 1}
                       for split in ("train", "val")],
        "sample.json": [{"token": "f" + split, "scene_token": "s" + split} for split in ("train", "val")],
        "log.json": [{"token": "l" + split} for split in ("train", "val")],
        "sensor.json": [{"token": c, "channel": c} for c in channels],
        "calibrated_sensor.json": [{"token": "cal" + c, "sensor_token": c} for c in channels],
    }
    rows = [{"token": split + c, "sample_token": "f" + split, "calibrated_sensor_token": "cal" + c,
             "is_key_frame": True, "filename": "samples/" + c + "/" + split + ".bin"}
            for split in ("train", "val") for c in channels]
    rows.append({"token": "sweep", "sample_token": "ftrain", "calibrated_sensor_token": "calLIDAR_TOP",
                 "is_key_frame": False, "filename": "sweeps/LIDAR_TOP/train.bin"})
    return tables, rows


class TrainingSensorInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / "data"
        self.data.mkdir()
        tables, rows = fixture()
        self.header, self.assets = inventory.make_request(tables, rows, {"train"}, {"val"})

    def request(self, name="request.gz", header=None, assets=None):
        path = self.root / name
        inventory.write_request(path, header or self.header, self.assets if assets is None else assets)
        return path

    def scan(self, request, roots=None):
        return inventory.scan(request, inventory.digest(request), roots or [self.data], self.root / "result")

    def test_no_files_preserves_full_denominators(self):
        report = self.scan(self.request())
        self.assertEqual(report["asset_count"], 15)
        self.assertEqual(sum(r["states"].get("missing", 0) for r in report["by_channel"]), 15)
        self.assertEqual(report["frames"], {"train": {"incomplete_or_unresolved": 1}, "val": {"incomplete_or_unresolved": 1}})
        self.assertEqual(report["sensor_payload_validity"], "not_checked")

    def test_complete_validation_does_not_make_training_complete(self):
        for row in self.assets:
            if row["split"] == "val":
                path = self.data / row["filename"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"authored test payload, not a valid sensor file")
        report = self.scan(self.request())
        self.assertEqual(report["frames"]["val"], {"all_seven_present_nonempty": 1})
        self.assertEqual(report["frames"]["train"], {"incomplete_or_unresolved": 1})
        self.assertEqual(report["model_training_readiness"], "not_established")

    def test_links_empty_files_and_directories_are_not_available_files(self):
        (self.data / "empty").touch()
        (self.data / "directory").mkdir()
        (self.data / "link").symlink_to(self.root, target_is_directory=True)
        self.assertEqual(inventory.observe(self.data, "empty")["state"], "empty")
        self.assertEqual(inventory.observe(self.data, "directory")["state"], "not_regular")
        self.assertEqual(inventory.observe(self.data, "link/anything")["state"], "symlink_unresolved")
        with patch.object(Path, "lstat", side_effect=PermissionError):
            self.assertEqual(inventory.observe(self.data, "inaccessible")["state"], "unreadable_metadata")

    def test_multiple_copies_retain_unresolved_identity(self):
        candidates = [{"state": "present_nonempty", "bytes": 3}, {"state": "present_nonempty", "bytes": 7}]
        self.assertEqual(inventory.combined_state(candidates), "multiple_nonempty_uncompared")

    def test_bad_metadata_and_paths_rejected(self):
        tables, rows = fixture()
        for bad in (".", "../escape", "/absolute", "x/../escape", "a//b", "a/./b", "a\\b", "a\x00b"):
            with self.subTest(path=bad), self.assertRaisesRegex(ValueError, "unsafe asset path"):
                inventory.relative_file(bad)
        with self.assertRaisesRegex(ValueError, "missing keyframe channel"):
            inventory.make_request(tables, rows[1:], {"train"}, {"val"})
        with self.assertRaisesRegex(ValueError, "duplicate asset identity"):
            inventory.make_request(tables, rows + [rows[0]], {"train"}, {"val"})
        with self.assertRaisesRegex(ValueError, "overlapping official split"):
            inventory.make_request(tables, rows, {"train"}, {"train", "val"})

    def test_truncated_request_cannot_emit_success(self):
        request = self.request(assets=self.assets[:-1])
        with self.assertRaisesRegex(ValueError, "asset count differs"):
            self.scan(request)
        self.assertFalse((self.root / "result/result.json").exists())

    def test_duplicate_request_cannot_emit_success(self):
        assets = self.assets + [copy.deepcopy(self.assets[0])]
        request = self.request(header=dict(self.header, asset_count=len(assets)), assets=assets)
        with self.assertRaisesRegex(ValueError, "duplicate request asset"):
            self.scan(request)
        self.assertFalse((self.root / "result/result.json").exists())

    def test_forged_population_and_missing_channel_rejected(self):
        for label, header, assets, message in (
            ("population", dict(self.header, sample_counts={"train": 2, "val": 1}), self.assets, "population differs"),
            ("channel", dict(self.header, asset_count=14), self.assets[1:], "missing keyframe channel"),
            ("empty", dict(self.header, asset_count=0), [], "empty"),
        ):
            with self.subTest(label=label):
                request = self.request(name=label + ".gz", header=header, assets=assets)
                output = self.root / label
                with self.assertRaisesRegex(ValueError, message):
                    inventory.scan(request, inventory.digest(request), [self.data], output)
                self.assertFalse((output / "result.json").exists())

    def test_request_identity_and_repeat_output_rejected(self):
        request = self.request()
        with self.assertRaisesRegex(ValueError, "identity differs"):
            inventory.scan(request, "0" * 64, [self.data], self.root / "bad")
        self.assertFalse((self.root / "bad").exists())
        self.scan(request)
        with self.assertRaises(FileExistsError):
            self.scan(request)

    def test_request_bytes_are_reproducible(self):
        a, b = self.request("a.gz"), self.request("b.gz")
        self.assertEqual(a.read_bytes(), b.read_bytes())


if __name__ == "__main__":
    unittest.main()
