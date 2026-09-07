"""Falsification controls for the portable population auditor, not a benchmark."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reference_population_audit as module

ROOT = Path(__file__).resolve().parents[2]


class ReferencePopulationAuditTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((ROOT / "research/reference-audit/0.1.0/demo.json").read_bytes())

    def run_doc(self, doc):
        return module.audit(module.canonical(doc))

    def test_excluded_annotation_refutes_exhaustive_reference_wording(self):
        result = self.run_doc(self.doc)
        self.assertEqual(result["counts"], {"evaluation_reference_near": 1, "excluded_reference_near": 1,
                         "unmatched_in_supplied_wider_reference": 1, "reference_unknown": 1})
        self.assertEqual(result["rows"][1]["nearest_wider_reference"]["annotation_id"], "excluded-object")
        self.assertIsNone(result["physical_false_positive_rate"])
        self.assertTrue(all(r["physical_object_presence"] == "unknown" for r in result["rows"]))

    def test_input_order_is_not_a_geometric_signal(self):
        original = self.run_doc(self.doc)["rows"]
        self.doc["frames"].reverse()
        for frame in self.doc["frames"]:
            frame["predictions"].reverse()
            if frame["annotations"] is not None:
                frame["annotations"].reverse()
        self.assertEqual(self.run_doc(self.doc)["rows"], original)

    def test_exact_rigid_transform_preserves_witnesses(self):
        original = self.run_doc(self.doc)["rows"]
        for frame in self.doc["frames"]:
            for obj in frame["predictions"] + (frame["annotations"] or []):
                x, y = obj["xy_m"]
                from decimal import Decimal
                obj["xy_m"] = [str(-Decimal(y) + 100), str(Decimal(x) - 30)]
        self.assertEqual(self.run_doc(self.doc)["rows"], original)

    def test_threshold_has_an_exact_inclusive_boundary(self):
        pred = self.doc["frames"][0]["predictions"][1]
        pred["xy_m"] = ["57", "0"]
        self.assertEqual(self.run_doc(self.doc)["rows"][1]["status"], "excluded_reference_near")
        pred["xy_m"] = ["57.000000000001", "0"]
        self.assertEqual(self.run_doc(self.doc)["rows"][1]["status"], "unmatched_in_supplied_wider_reference")

    def test_exact_rationals_survive_json_clients_with_limited_integer_precision(self):
        self.doc["frames"][0]["predictions"][1]["xy_m"] = ["55.000000000001", "0"]
        witness = self.run_doc(self.doc)["rows"][1]["nearest_wider_reference"]
        self.assertEqual(witness["distance_squared_m2"], {
            "numerator": "1", "denominator": "1000000000000000000000000"})

    def test_bounded_distance_work_is_enforced_before_geometry(self):
        frame = self.doc["frames"][0]
        frame["annotations"] = [{"id": "a" + str(i), "xy_m": ["0", "0"]} for i in range(1001)]
        frame["evaluation_annotation_ids"] = []
        frame["predictions"] = [{"id": "p" + str(i), "xy_m": ["0", "0"]} for i in range(1000)]
        with self.assertRaisesRegex(module.AuditInputError, "budget"):
            self.run_doc(self.doc)

    def test_empty_and_unavailable_references_differ(self):
        frame = self.doc["frames"][1]
        before = self.run_doc(self.doc)["rows"][-1]
        frame.update(reference_state="available", annotations=[], evaluation_annotation_ids=[])
        after = self.run_doc(self.doc)["rows"][-1]
        self.assertEqual(before["status"], "reference_unknown")
        self.assertEqual(after["status"], "unmatched_in_supplied_wider_reference")
        self.assertEqual(after["physical_object_presence"], "unknown")

    def test_unknown_states_remain_distinct(self):
        for state in ("withheld", "invalid", "unavailable"):
            self.doc["frames"][1]["reference_state"] = state
            result = self.run_doc(self.doc)["rows"][-1]
            self.assertEqual(result["reference_state"], state)
            self.assertEqual(result["status"], "reference_unknown")

    def test_false_reference_subset_is_rejected(self):
        self.doc["frames"][0]["evaluation_annotation_ids"].append("absent-object")
        with self.assertRaisesRegex(module.AuditInputError, "subset"):
            self.run_doc(self.doc)

    def test_unknown_properties_duplicate_ids_and_boolean_time_are_rejected(self):
        mutations = [lambda d: d.update(phantom=True),
                     lambda d: d["frames"][0].update(timestamp_us=True),
                     lambda d: d["frames"][0]["predictions"].append(d["frames"][0]["predictions"][0]),
                     lambda d: d["frames"][1].update(annotations=[])]
        for mutate in mutations:
            doc = copy.deepcopy(self.doc)
            mutate(doc)
            with self.assertRaises(module.AuditInputError):
                self.run_doc(doc)

    def test_duplicate_json_and_nonfinite_coordinates_are_rejected(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}'):
            with self.assertRaises(module.AuditInputError):
                module.audit(raw)
        for bad in ("NaN", "Infinity", "1e999", 1.25, True):
            self.doc["frames"][0]["predictions"][0]["xy_m"][0] = bad
            with self.assertRaises(module.AuditInputError):
                self.run_doc(self.doc)

    def test_invalid_cli_produces_no_success_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text('{"forged":true}')
            proc = subprocess.run([sys.executable, str(Path(module.__file__)), str(path)], capture_output=True)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, b"")
        self.assertEqual(json.loads(proc.stderr)["status"], "invalid")


if __name__ == "__main__":
    unittest.main()
