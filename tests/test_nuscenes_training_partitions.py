"""Counterexamples for cross-partition references and altered metadata values."""
import copy
from decimal import Decimal
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "measure"))
import build_nuscenes_training_partitions as builder


def fixture():
    rows = {t: [] for t in builder.FIELDS}
    for table in ("category", "attribute", "visibility"):
        rows[table] = [{"token": table, "name": table}]
    rows["sensor"] = [{"token": c, "channel": c} for c in builder.CHANNELS]
    rows["calibrated_sensor"] = [{"token": c, "sensor_token": c} for c in builder.CHANNELS]
    rows["map"] = [{"token": "map", "filename": "maps/map.png", "log_tokens": ["u", "v", "unavailable"]}]
    for group in ("u", "v"):
        rows["log"].append({"token": group})
        rows["scene"].append({"token": group, "log_token": group, "name": group,
                              "nbr_samples": 2, "first_sample_token": group + "0", "last_sample_token": group + "1"})
        rows["instance"].append({"token": group, "category_token": "category", "nbr_annotations": 2,
                                 "first_annotation_token": group + "0", "last_annotation_token": group + "1"})
        for i in range(2):
            token = group + str(i)
            prev, nxt = ("", group + "1") if i == 0 else (group + "0", "")
            rows["sample"].append({"token": token, "scene_token": group, "timestamp": i + 1, "prev": prev, "next": nxt})
            rows["ego_pose"].append({"token": token, "translation": [Decimal("1.000000000000000000123"), 0, 0]})
            rows["sample_annotation"].append({"token": token, "sample_token": token, "instance_token": group,
                                              "visibility_token": "visibility", "attribute_tokens": ["attribute"],
                                              "prev": prev, "next": nxt})
            for c in builder.CHANNELS:
                rows["sample_data"].append({"token": c + token, "sample_token": token, "ego_pose_token": token,
                                            "calibrated_sensor_token": c, "timestamp": i + 1, "is_key_frame": True,
                                            "filename": "samples/" + c + "/" + token,
                                            "prev": c + prev if prev else "", "next": c + nxt if nxt else ""})
    return rows


def radar_boundary_fixture():
    rows = fixture()
    rows["scene"][1]["log_token"] = "u"
    rows["sensor"].append({"token": "radar", "channel": "RADAR_FRONT", "modality": "radar"})
    rows["calibrated_sensor"].append({"token": "radar", "sensor_token": "radar"})
    for sample in ("u0", "u1", "v0", "v1"):
        group, i = sample[0], int(sample[1])
        rows["sample_data"].append({"token": "radar" + sample, "sample_token": sample, "ego_pose_token": sample,
                                    "calibrated_sensor_token": "radar", "timestamp": i + 1 + (group == "v"),
                                    "is_key_frame": True, "filename": "samples/radar/boundary" if sample in ("u1", "v0") else "samples/radar/" + sample,
                                    "prev": "radar" + group + "0" if i else "", "next": "radar" + group + "1" if not i else ""})
    return rows


class NuScenesPartitionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def index(self, rows=None, name="index.sqlite"):
        path = self.root / name
        builder.create_index(path, ((t + ".json", r) for t, table in (rows or fixture()).items() for r in table),
                             {"metadata_sha256": "test-fixture"})
        return path

    def subset(self, path, logs=None, scenes=None, dest="subset"):
        return builder.materialize(path, builder.digest(path), logs or ["u"], scenes or ["u"], self.root / dest, {})

    def test_actual_output_preserves_decimals_and_projects_only_map_references(self):
        path = self.index()
        report = self.subset(path)
        self.assertEqual(report["tables"]["sample_data"]["rows"], 14)
        self.assertEqual(report["tables"]["sample_annotation"]["rows"], 2)
        self.assertEqual(report["outside_subset_references"], 0)
        out = self.root / "subset/v1.0-trainval"
        poses = builder.read_json(out / "ego_pose.json")
        self.assertEqual(poses[0]["translation"][0], Decimal("1.000000000000000000123"))
        self.assertEqual(builder.read_json(out / "map.json")[0]["log_tokens"], ["u"])
        for table in builder.FIELDS:
            if table == "map":
                continue
            source = {r["token"]: r for r in fixture()[table]}
            for row in builder.read_json(out / (table + ".json")):
                self.assertEqual(row, source[row["token"]])
        self.subset(path, dest="again")
        for table in builder.FIELDS:
            self.assertEqual((out / (table + ".json")).read_bytes(),
                             (self.root / "again/v1.0-trainval" / (table + ".json")).read_bytes())

    def test_dangling_reference_and_duplicate_identity_fail_before_complete_marker(self):
        for label in ("dangling", "duplicate", "attribute"):
            rows = fixture()
            if label == "dangling":
                rows["sample_data"][0]["ego_pose_token"] = "absent"
            elif label == "attribute":
                rows["sample_annotation"][0]["attribute_tokens"] = ["absent"]
            else:
                rows["sample_data"].append(copy.deepcopy(rows["sample_data"][0]))
            with self.subTest(label=label), self.assertRaises((ValueError, sqlite3.IntegrityError)):
                self.index(rows, label + ".sqlite")
            with sqlite3.connect(self.root / (label + ".sqlite")) as db:
                self.assertEqual(db.execute("SELECT name FROM sqlite_master WHERE name='provenance'").fetchall(), [])

    def test_cross_partition_temporal_reference_is_rejected_even_if_target_exists_globally(self):
        path = self.index()
        with sqlite3.connect(path) as db:
            db.execute("UPDATE sample_data SET prev=? WHERE token=?", (builder.CHANNELS[0] + "v0", builder.CHANNELS[0] + "u0"))
        with self.assertRaisesRegex(ValueError, "reference outside subset: sample_data.prev"):
            self.subset(path)
        self.assertFalse((self.root / "subset/result.json").exists())

    def test_corrupt_sequence_counts_and_endpoints_are_rejected(self):
        for field, value in (("nbr_samples", 3), ("first_sample_token", "u1")):
            rows = fixture()
            rows["scene"][0][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "invalid scene"):
                self.index(rows, field + ".sqlite")

    def test_nonreciprocal_chain_and_missing_channel_are_rejected(self):
        rows = fixture()
        rows["sample"][1]["prev"] = ""
        with self.assertRaisesRegex(ValueError, "disconnected sample chain"):
            self.index(rows, "chain.sqlite")
        rows = fixture()
        rows["sample_data"] = [r for r in rows["sample_data"] if not r["token"].startswith(builder.CHANNELS[0])]
        with self.assertRaisesRegex(ValueError, "missing keyframe channel"):
            self.index(rows, "channel.sqlite")

    def test_duplicate_keyframe_and_unsafe_sensor_path_are_rejected(self):
        rows = fixture()
        extra = dict(rows["sample_data"][0], token="extra", filename="samples/extra", prev="", next="")
        rows["sample_data"].append(extra)
        with self.assertRaisesRegex(ValueError, "duplicate keyframe channel"):
            self.index(rows, "duplicate-channel.sqlite")
        rows = fixture()
        rows["sample_data"][0]["filename"] = "../escape"
        with self.assertRaisesRegex(ValueError, "unsafe asset path"):
            self.index(rows, "escape.sqlite")

    def test_whole_log_population_and_unknown_logs_are_checked(self):
        path = self.index()
        for logs, scenes, message in ((["u"], ["v"], "scene names differ"),
                                     (["u", "u"], ["u"], "duplicate partition"),
                                     (["absent"], ["u"], "unknown partition log")):
            with self.subTest(logs=logs), self.assertRaisesRegex(ValueError, message):
                self.subset(path, logs, scenes)

    def test_missing_or_ambiguous_map_reference_cannot_emit_success(self):
        for label in ("missing", "ambiguous"):
            rows = fixture()
            if label == "missing":
                rows["map"][0]["log_tokens"] = ["v"]
            else:
                rows["map"].append(dict(rows["map"][0], token="another"))
            path = self.index(rows, label + ".sqlite")
            with self.subTest(label=label), self.assertRaisesRegex(ValueError, "log to map reference"):
                self.subset(path, dest=label)
            self.assertFalse((self.root / label / "result.json").exists())

    def test_identity_and_output_reuse_rejected(self):
        path = self.index()
        with self.assertRaisesRegex(ValueError, "index identity differs"):
            builder.materialize(path, "0" * 64, ["u"], ["u"], self.root / "bad", {})
        self.subset(path)
        with self.assertRaises(FileExistsError):
            self.subset(path)

    def test_unsupported_numeric_and_reference_types_rejected(self):
        for value in (float("nan"), 1.5, Decimal("Infinity")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                builder.exact_json(value)
        rows = fixture()
        rows["sample_annotation"][0]["attribute_tokens"] = "attribute"
        with self.assertRaisesRegex(ValueError, "invalid reference list"):
            self.index(rows)

    def test_source_radar_boundary_alias_preserves_both_records(self):
        path = self.index(radar_boundary_fixture())
        report = self.subset(path, scenes=["u", "v"])
        self.assertEqual(report["tables"]["sample_data"]["rows"], 32)
        self.assertEqual(report["source"]["filename_aliases"]["radar_boundary_filename_aliases"], 1)
        data = builder.read_json(self.root / "subset/v1.0-trainval/sample_data.json")
        aliases = [r for r in data if r["filename"] == "samples/radar/boundary"]
        self.assertEqual({r["token"] for r in aliases}, {"radaru1", "radarv0"})

    def test_cross_log_changed_pose_and_nonradar_aliases_are_rejected(self):
        for label in ("cross-log", "pose", "camera"):
            rows = radar_boundary_fixture()
            if label == "cross-log":
                rows["scene"][1]["log_token"] = "v"
            elif label == "pose":
                rows["ego_pose"][2]["translation"][2] = 1
            else:
                rows["sensor"][-1]["modality"] = "camera"
            with self.subTest(label=label), self.assertRaisesRegex(ValueError, "unsupported filename alias"):
                self.index(rows, label + ".sqlite")


if __name__ == "__main__":
    unittest.main()
