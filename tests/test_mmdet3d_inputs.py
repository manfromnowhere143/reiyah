"""Critical payload rejection and export-custody controls; no model is mocked."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

import numpy as np

SOURCE = Path(__file__).resolve().parents[1] / "tools/measure/audit_mmdet3d_inputs.py"
SPEC = importlib.util.spec_from_file_location("input_audit", SOURCE)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class InputBoundaryTest(unittest.TestCase):
    def test_point_payload_preserves_every_scalar(self):
        expected = np.array([[1., -2., .3, 254., 17.], [0., 0., -3., 7., 2.]], dtype="<f4")
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "points.bin"
            path.write_bytes(expected.tobytes())
            actual, digest = audit.decode_points(path)
            np.testing.assert_array_equal(actual, expected)
            self.assertEqual(digest, audit.sha(path))

    def test_truncated_point_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "points.bin"
            for payload in (b"", bytes(19), bytes(21)):
                path.write_bytes(payload)
                with self.assertRaisesRegex(ValueError, "payload length"):
                    audit.decode_points(path)

    def test_unavailable_or_infinite_point_is_not_imputed(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "points.bin"
            for unknown in (np.nan, np.inf, -np.inf):
                path.write_bytes(np.asarray([[unknown, 0., 0., 0., 0.]], dtype="<f4").tobytes())
                with self.assertRaisesRegex(ValueError, "nonfinite"):
                    audit.decode_points(path)

    def test_quaternion_is_scalar_first_and_preserves_length(self):
        r = audit.rotation([np.sqrt(.5), 0., 0., np.sqrt(.5)])
        np.testing.assert_allclose(r @ [1., 0., 0.], [0., 1., 0.], atol=1e-14)
        np.testing.assert_allclose(r.T @ r, np.eye(3), atol=1e-14)

    def test_invalid_quaternion_is_not_normalized_to_confidence(self):
        for value in ([0., 0., 0., 0.], [2., 0., 0., 0.], [np.nan, 0., 0., 0.], [1., 0., 0.]):
            with self.assertRaisesRegex(ValueError, "invalid quaternion"):
                audit.rotation(value)

    def test_exporter_cannot_change_prediction_or_return_an_alias(self):
        prediction = {"boxes": np.array([[4.2, 1.6, 1.8]]), "nested": {"labels": [2]}}
        original = copy.deepcopy(prediction)
        def mutating_exporter(value):
            value["boxes"][:] = value["boxes"][:, [2, 0, 1]]
            value["nested"]["labels"].append(3)
            return value
        first = audit.isolated_camera_export(prediction, mutating_exporter)
        second = audit.isolated_camera_export(prediction, mutating_exporter)
        np.testing.assert_array_equal(prediction["boxes"], original["boxes"])
        self.assertEqual(prediction["nested"], original["nested"])
        np.testing.assert_array_equal(first["boxes"], second["boxes"])
        first["boxes"][:] = 0.
        np.testing.assert_array_equal(prediction["boxes"], original["boxes"])

    def test_selected_iteration_does_not_reindex_sdk_lookups(self):
        class Table:
            sample = [{"token": "a"}, {"token": "b"}, {"token": "c"}]
            index = {"a": 0, "b": 1, "c": 2}
            def get(self, name, token):
                return getattr(self, name)[self.index[token]]
        source = Table()
        view = audit.SelectedSampleView(source, [source.sample[2]])
        self.assertEqual(list(view.sample), [{"token": "c"}])
        self.assertEqual(view.get("sample", "c"), {"token": "c"})
        self.assertEqual(view.get("sample", "a"), {"token": "a"})
        self.assertEqual(len(source.sample), 3)


if __name__ == "__main__":
    unittest.main()
