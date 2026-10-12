#!/usr/bin/env python3
"""Authored controls; these tests never read retained annotation payloads."""
import copy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import audit


def manifest():
    parent = "MultiOrg_v2/test/Normal/Plate_authored/image_0/"
    sources = []
    for p in audit.PROCEDURES:
        suffix = "t0_A" if p == "t0" else p
        sources.append({"procedure": p, "source_path": parent + "image_0_" + suffix + ".json", "local_path": suffix + ".json", "byte_size": 2, "sha256": hashlib.sha256(b"{}").hexdigest(), "transport_valid": True})
    return {"artifact_id": "reiyah.multiorg.annotation-manifest", "version": "0.1.0", "images": [{"tiff_path": parent + "image_0.tiff", "annotations": sources}]}


class Controls(unittest.TestCase):
    def test_valid_roster(self):
        self.assertEqual(audit.validate_manifest(manifest(), 1), 6)

    def test_duplicate_key_and_nonfinite_rejected(self):
        for text in [b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}']:
            with self.assertRaises(ValueError):
                audit.strict_json(text)

    def test_roster_omission_or_unknown_property(self):
        bad = manifest(); bad["images"][0]["annotations"].pop()
        with self.assertRaises(ValueError): audit.validate_manifest(bad, 1)
        bad = manifest(); bad["approval"] = True
        with self.assertRaises(ValueError): audit.validate_manifest(bad, 1)

    def test_wrong_procedure_image_and_source_reuse(self):
        for field, value in [("procedure", "t0"), ("source_path", "MultiOrg_v2/test/Normal/wrong_t1_A.json"), ("local_path", "t0_A.json")]:
            bad = manifest(); bad["images"][0]["annotations"][1][field] = value
            with self.assertRaises(ValueError): audit.validate_manifest(bad, 1)

    def test_traversal_and_symlink(self):
        for value in ["../source", "/source", "a/../source", "a//source", "a/./source"]:
            with self.assertRaises(ValueError): audit.relative(value)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / "real").write_bytes(b"{}")
            (root / "alias").symlink_to(root / "real")
            with self.assertRaises(ValueError): audit.source_path(root, "alias")

    def test_changed_bytes_and_length_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "raw"; path.write_bytes(b"{}")
            self.assertEqual(audit.bound_bytes(path, 2, hashlib.sha256(b"{}").hexdigest(), 8), b"{}")
            path.write_bytes(b"[]")
            with self.assertRaises(ValueError): audit.bound_bytes(path, 2, hashlib.sha256(b"{}").hexdigest(), 8)
            with self.assertRaises(ValueError): audit.bound_bytes(path, 1, hashlib.sha256(b"[").hexdigest(), 8)

    def test_hash_selection_keeps_ineligible_out(self):
        rows = [{"tiff_path": str(i), "selection_sha256": audit.selection_hash(str(i)), "native_object_cap_eligible": i != 4} for i in range(8)]
        expected = sorted((r for r in rows if r["native_object_cap_eligible"]), key=lambda r: (r["selection_sha256"], r["tiff_path"]))[:4]
        self.assertEqual(audit.select(rows), [r["tiff_path"] for r in expected])
        self.assertEqual(audit.select([]), [])

    def test_actual_shape_authored_geometry(self):
        value = {"0": [[3, 40], [8, 40], [8, 46], [3, 46]]}
        result = audit.annotation_geometry(value, "source.json")
        self.assertEqual(result["box_count"], 1)
        self.assertEqual(result["negative_coordinate_boxes"], 0)
        value["0"].reverse()
        self.assertEqual(audit.annotation_geometry(value, "source.json"), result)

    def test_fractional_coordinates_are_exact(self):
        raw = b'{"0":[[0.1,2.2],[0.3,2.2],[0.3,2.4],[0.1,2.4]]}'
        parsed = audit.strict_json(raw)
        self.assertEqual(parsed["0"][0][0], Decimal("0.1"))
        self.assertEqual(audit.annotation_geometry(parsed, "source.json")["box_count"], 1)

    def test_non_rectangles_and_nonfinite_refused(self):
        bad = [[], [[0, 0], [0, 1], [0, 2], [0, 3]], [[0, 0], [1, 1], [2, 0], [1, -1]],
               [[0, 0], [1, 0], [1, 1], [1, 1]], [[True, 0], [1, 0], [1, 1], [0, 1]],
               [[Decimal("NaN"), 0], [1, 0], [1, 1], [0, 1]], [["0", 0], [1, 0], [1, 1], [0, 1]]]
        for corners in bad:
            with self.assertRaises(ValueError): audit.annotation_geometry({"0": corners}, "source.json")

    def test_negative_coordinates_retained_not_repaired(self):
        value = {"0": [[-1, 0], [1, 0], [1, 1], [-1, 1]]}
        before = copy.deepcopy(value)
        self.assertEqual(audit.annotation_geometry(value, "source.json")["negative_coordinate_boxes"], 1)
        self.assertEqual(value, before)

    def test_empty_source_and_source_qualified_identity(self):
        self.assertEqual(audit.annotation_geometry({}, "source.json")["box_count"], 0)
        value = {"0": [[0, 0], [1, 0], [1, 1], [0, 1]]}
        a = audit.annotation_geometry(value, "A.json")
        b = audit.annotation_geometry(value, "B.json")
        self.assertNotEqual(a["source_qualified_ids_sha256"], b["source_qualified_ids_sha256"])

    def test_transport_false_and_boolean_byte_size_refused(self):
        for field, value in [("transport_valid", False), ("transport_valid", 1), ("byte_size", True)]:
            bad = manifest(); bad["images"][0]["annotations"][0][field] = value
            with self.assertRaises(ValueError): audit.validate_manifest(bad, 1)

    def test_full_census_and_incomplete_census_never_selects(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = {"artifact_id": "reiyah.multiorg.annotation-manifest", "version": "0.1.0", "images": []}
            for index in range(55):
                entry = copy.deepcopy(manifest()["images"][0])
                old = "image_0"
                new = "image_" + str(index)
                entry["tiff_path"] = entry["tiff_path"].replace(old, new)
                for source in entry["annotations"]:
                    source["source_path"] = source["source_path"].replace(old, new)
                    source["local_path"] = "raw/" + source["source_path"]
                    count = 43 if index == 0 else 42 if index == 1 else 1
                    if index == 1 and source["procedure"] in ("t0", "t1_A"):
                        count = 43
                    data = json.dumps({str(i): [[0, 0], [1, 0], [1, 1], [0, 1]] for i in range(count)}).encode()
                    source["byte_size"], source["sha256"] = len(data), hashlib.sha256(data).hexdigest()
                    path = root / source["local_path"]; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
                packet["images"].append(entry)
            result = audit.audit_manifest(packet, root)
            self.assertEqual(result["status"], "eligible_subset")
            self.assertEqual(result["valid_annotation_file_count"], 165)
            self.assertEqual(result["eligible_images"], 54)
            by_path = {row["tiff_path"]: row for row in result["images"]}
            self.assertFalse(by_path[packet["images"][0]["tiff_path"]]["native_object_cap_eligible"])
            self.assertEqual(by_path[packet["images"][1]["tiff_path"]]["sum_reference_objects"], 128)
            self.assertEqual(len(result["selected_images"]), 4)
            source = packet["images"][2]["annotations"][0]
            body = b"authored unavailable transport, not JSON"
            (root / source["local_path"]).write_bytes(body)
            source.update(transport_valid=False, byte_size=len(body), sha256=hashlib.sha256(body).hexdigest())
            result = audit.audit_manifest(packet, root)
            self.assertEqual(result["status"], "incomplete_census")
            self.assertEqual(result["valid_annotation_file_count"], 164)
            self.assertEqual(result["failed_annotation_file_count"], 1)
            self.assertEqual(result["selected_images"], [])
            self.assertIsNone(result["feasibility_pilot"])
            self.assertIsNone(result["eligible_images"])
            row = next(row for row in result["images"] if row["tiff_path"] == packet["images"][2]["tiff_path"])
            self.assertIsNone(row["annotation_counts"]["t0"])
            self.assertIsNone(row["sum_reference_objects"])
            self.assertEqual(row["annotation_states"]["t0"], "transport_unavailable")
            (root / "raw/MultiOrg_v2/test/extra.json").write_bytes(b"{}")
            with self.assertRaisesRegex(ValueError, "missing or extra"):
                audit.audit_manifest(packet, root)


if __name__ == "__main__":
    unittest.main()
