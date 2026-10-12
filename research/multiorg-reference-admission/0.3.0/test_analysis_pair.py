"""Authored execute-loop integration controls; no model, TIFF or network execution."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('analysis_adapter', ROOT / 'inference/analysis_pair.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


def outputs(high=.9, bad=False, score=None):
    rows = [[0, 0, 0, 0, .4], [0, 0, 20, 20, high]]
    if bad:
        rows[1][:4] = [0, 0, 0, 0]
    if score is not None:
        rows[0][4] = score
    return [np.asarray(rows, dtype=np.float32)[None], np.zeros((1, 2), dtype=np.int64)]


class Harness:
    def __init__(self, directory, emit=None, manifest_edit=None):
        self.root = Path(directory)
        self.original, self.projection, self.supplement = adapter.load_components()
        # Authored I/O fixture has two tiles; production's bound contract remains156.
        self.supplement = copy.deepcopy(self.supplement)
        self.supplement['expected_actual_first_image_tiles_per_model'] = 2
        self.calls = []
        self.emit = emit or (lambda model, tile: outputs(.9 if model == 0 else .8))
        self.manifest = self.root / 'manifest.json'
        m = json.loads((ROOT / 'inference/pilot-manifest.json').read_text())
        if manifest_edit:
            manifest_edit(m)
        self.manifest.write_text(json.dumps(m))
        self.destination = self.root / 'run'

    def run(self):
        original_checked = self.original.checked_file
        harness = self
        sessions = []
        class Session:
            def __init__(self, *args, **kwargs):
                self.model = len(sessions)
                self.tile = 0
                sessions.append(self)
            def get_providers(self): return ['CPUExecutionProvider']
            def get_inputs(self): return [types.SimpleNamespace(name='input', shape=[1, 3, 2, 2], type='tensor(float)')]
            def get_outputs(self):
                return [types.SimpleNamespace(name='dets', shape=[1, None, 5], type='tensor(float)'),
                        types.SimpleNamespace(name='labels', shape=[1, None], type='tensor(int64)')]
            def run(self, names, feed):
                harness.calls.append((self.model, self.tile))
                result = harness.emit(self.model, self.tile)
                self.tile += 1
                return result
        ort = types.SimpleNamespace(SessionOptions=lambda: types.SimpleNamespace(),
              ExecutionMode=types.SimpleNamespace(ORT_SEQUENTIAL=0), InferenceSession=Session)
        class Tiff:
            def __init__(self, *_):
                self.series = [types.SimpleNamespace(shape=(2, 2), asarray=lambda: np.zeros((2, 2), dtype=np.uint16))]
            def __enter__(self): return self
            def __exit__(self, *_): return False
        def checked(record, *args, **kwargs):
            if record['path'].endswith('scientific-base.json'):
                return original_checked(record, *args, **kwargs)
            return b'authored external source bytes; no model or image loaded'
        with patch.dict('sys.modules', {'cv2': types.SimpleNamespace(setNumThreads=lambda _: None),
                'onnxruntime': ort, 'tifffile': types.SimpleNamespace(TiffFile=Tiff)}), \
             patch.object(self.original, 'checked_file', side_effect=checked), \
             patch.object(self.original, 'prepare_image', return_value=(np.zeros((512, 768), dtype=np.uint8), [1, 257], [1024, 1536])), \
             patch.object(self.original, 'model_input', return_value=(np.zeros((1, 3, 2, 2), dtype=np.float32), 800)), \
             patch.object(adapter.resource, 'setrlimit'):
            return adapter.execute(self.manifest, self.destination, original=self.original,
                                   projection=self.projection, supplement=self.supplement)


class Integration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='authored-', dir=ROOT / 'qualification')
        self.addCleanup(self.temp.cleanup)

    def harness(self, **kwargs):
        return Harness(self.temp.name, **kwargs)

    def test_complete_two_models_two_tiles_preserves_all_raw_and_scope(self):
        harness = self.harness()
        final = harness.run()
        self.assertEqual(harness.calls, [(0, 0), (0, 1), (1, 0), (1, 1)])
        self.assertEqual(final['completion_scope'], adapter.SCOPE)
        self.assertEqual(final['storage_output_status'], adapter.STORAGE_STATUS)
        self.assertEqual(final['original_worker_sha256'], adapter.ORIGINAL_SHA)
        self.assertEqual(final['projection_sha256'], adapter.PROJECTION_SHA)
        self.assertEqual(final['supplemental_protocol_sha256'], adapter.SUPPLEMENT_SHA)
        self.assertEqual(len(final['observations']), 2)
        self.assertEqual(len(list((harness.destination / 'raw').glob('*.npy'))), 8)
        for observation in final['observations']:
            image = json.loads((harness.destination / observation['file']).read_text())
            self.assertNotIn('storage_predictions', image)
            self.assertEqual(image['tile_count_completed'], image['tile_count_expected'])
            self.assertEqual(image['raw_onnx_rows'], 4)
            self.assertEqual([p['id'] for p in image['analysis_predictions']], [1, 3])
            self.assertEqual([p['tile_ordinal'] for p in image['analysis_predictions']], [0, 1])
            for tile in image['tiles']:
                self.assertEqual(tile['all_raw_rows'], 2)
                self.assertEqual(tile['high_rows'], 1)
                self.assertEqual(tile['low_rows'], 1)
                self.assertEqual(tile['storage_eligible_low_geometry_anomaly_indices']['raw_nonpositive_extent'], [0])
                self.assertEqual(tile['analysis_original_row_indices'], [1])
                self.assertEqual(tile['tensor']['observation_time'], 'before_session_run')
                self.assertEqual(tile['tensor']['c_order_data_sha256'], hashlib.sha256(np.zeros((1, 3, 2, 2), dtype=np.float32).tobytes()).hexdigest())
                for desc in tile['raw_outputs']:
                    rawpath = harness.destination / desc['file']
                    self.assertEqual(hashlib.sha256(rawpath.read_bytes()).hexdigest(), desc['sha256'])
                    self.assertEqual(rawpath.stat().st_size, desc['bytes'])
                    array = np.load(rawpath, allow_pickle=False)
                    self.assertEqual(array.dtype.str, desc['dtype'])
                    self.assertEqual(list(array.shape), desc['shape'])
        self.assertTrue((harness.destination / 'result.json').exists())

    def test_high_invalid_second_tile_retained_then_refused_without_completion(self):
        harness = self.harness(emit=lambda model, tile: outputs(bad=tile == 1))
        with self.assertRaises(ValueError): harness.run()
        self.assertEqual(harness.calls, [(0, 0), (0, 1)])
        self.assertEqual(len(list((harness.destination / 'raw').glob('*.npy'))), 4)
        receipts = [json.loads(p.read_text()) for p in (harness.destination / 'raw').glob('*.json')]
        self.assertEqual(sorted(p['ordinal'] for p in receipts), [0, 1])
        self.assertFalse((harness.destination / 'result.json').exists())
        self.assertFalse(list(harness.destination.glob('*.json')))

    def test_low_invalid_score_still_rejected_and_raw_preserved(self):
        harness = self.harness(emit=lambda *_: outputs(score=float('nan')))
        with self.assertRaisesRegex(ValueError, 'score'): harness.run()
        self.assertEqual(len(list((harness.destination / 'raw').glob('*.npy'))), 2)
        self.assertFalse((harness.destination / 'result.json').exists())

    def test_raw_row_cap_counts_excluded_rows_before_projection(self):
        harness = self.harness(emit=lambda *_: [np.zeros((1, 200001, 5), dtype=np.float32), np.zeros((1, 200001), dtype=np.int64)])
        with self.assertRaisesRegex(ValueError, 'all-raw-row work cap'): harness.run()
        self.assertEqual(harness.calls, [(0, 0)])
        self.assertEqual(len(list((harness.destination / 'raw').glob('*.npy'))), 2)
        self.assertFalse((harness.destination / 'result.json').exists())

    def test_raw_total_byte_cap_refuses_without_complete_result(self):
        harness = self.harness()
        with patch.object(adapter, 'MAX_RAW_TOTAL_BYTES', 100), self.assertRaisesRegex(ValueError, 'total byte cap'):
            harness.run()
        self.assertFalse((harness.destination / 'result.json').exists())

    def test_raw_store_object_and_per_file_caps(self):
        store = adapter.RawStore(Path(self.temp.name))
        with self.assertRaisesRegex(ValueError, 'non-object'):
            store.save('object', [np.array([object()]), np.array([0])])
        with patch.object(adapter, 'MAX_RAW_FILE_BYTES', 100), self.assertRaisesRegex(ValueError, 'per-file'):
            store.save('size', outputs())

    def test_wrong_first_image_rejected_before_model(self):
        harness = self.harness(manifest_edit=lambda m: m['images'][0].update(id='MultiOrg_v2/test/Macros/Plate_23/image_0/image_0.tiff'))
        with self.assertRaisesRegex(ValueError, 'frozen first image'): harness.run()
        self.assertEqual(harness.calls, [])

    def test_broader_original_memory_limit_rejected(self):
        harness = self.harness(manifest_edit=lambda m: m['limits'].update(memory_bytes=6442450944))
        with self.assertRaisesRegex(ValueError, 'exact single-image resource'): harness.run()
        self.assertEqual(harness.calls, [])

    def test_runtime_failure_mid_image_never_becomes_empty_analysis(self):
        def emit(model, tile):
            if tile == 1: raise RuntimeError('authored ORT failure')
            return outputs()
        harness = self.harness(emit=emit)
        with self.assertRaisesRegex(RuntimeError, 'authored ORT failure'): harness.run()
        self.assertFalse((harness.destination / 'result.json').exists())
        self.assertFalse(list(harness.destination.glob('*.json')))
        self.assertEqual(len(list((harness.destination / 'raw').glob('*.npy'))), 2)

    def test_frozen_tile_population_mismatch_rejects_before_inference(self):
        harness = self.harness()
        harness.supplement['expected_actual_first_image_tiles_per_model'] = 3
        with self.assertRaisesRegex(ValueError, 'frozen whole-image tile population'):
            harness.run()
        self.assertEqual(harness.calls, [])
        self.assertFalse((harness.destination / 'result.json').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
