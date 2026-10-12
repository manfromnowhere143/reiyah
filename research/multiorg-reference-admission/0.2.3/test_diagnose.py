#!/usr/bin/env python3
"""Authored diagnostics controls only: no empirical images/models/inference."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
import numpy as np

OWNER = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('diagnose', OWNER / 'inference/diagnose.py')
diag = importlib.util.module_from_spec(spec); spec.loader.exec_module(diag)


def outputs(rows, dtype=np.float64):
    return [np.asarray([rows], dtype=dtype), np.zeros((1, len(rows)), dtype=np.int64)]


class DiagnosticControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='authored-', dir=OWNER / 'qualification')
        self.base = Path(self.temp.name)
        self.worker = diag.load_worker()
        self.capture = diag.Capture(self.base / 'capture', self.worker)
        self.original = diag.install(self.worker, self.capture)

    def tearDown(self):
        self.temp.cleanup()

    def read(self):
        return json.loads((self.base / 'capture/diagnostic.json').read_text())

    def capture_failure(self, out, expected, side=800):
        originals = [x.copy() for x in out] if isinstance(out, list) and all(isinstance(x, np.ndarray) for x in out) else None
        with self.assertRaisesRegex(Exception, expected):
            self.worker.decode_output(out, 256, 512, side)
        if originals:
            for old, current in zip(originals, out):
                np.testing.assert_array_equal(old, current)
                self.assertEqual(old.dtype, current.dtype)
        return self.read()

    def test_exact_worker_binding_and_unchanged_execute(self):
        self.assertEqual(hashlib.sha256((OWNER/'inference/run_pair.py').read_bytes()).hexdigest(), diag.WORKER_SHA256)
        fresh = diag.load_worker()
        self.assertEqual(self.worker.execute.__code__.co_code, fresh.execute.__code__.co_code)
        self.assertEqual(self.worker.execute.__code__.co_consts, fresh.execute.__code__.co_consts)
        other = self.base/'tampered.py'; other.write_bytes((OWNER/'inference/run_pair.py').read_bytes()+b'\n')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):diag.load_worker(other)

    def test_valid_decode_equality_and_input_immutability(self):
        out = outputs([[0,1,10,20,.6],[2,4,30,45,.99]])
        before = [x.tobytes() for x in out]
        expected = self.original(out,256,512,800)
        observed = self.worker.decode_output(out,256,512,800)
        for a,b in zip(expected[:2],observed[:2]):np.testing.assert_array_equal(a,b)
        self.assertEqual(expected[2],observed[2])
        self.assertEqual(before,[x.tobytes() for x in out])
        self.assertFalse(self.capture.directory.exists())

    def test_below_floor_degenerate_padding_is_unchanged(self):
        out = outputs([[0,0,0,0,0],[1,1,1,1,.049],[1,1,10,10,.5]],np.float32)
        out[1][0,1]=99
        actual = self.worker.decode_output(out,0,0,800)
        expected = self.original(out,0,0,800)
        self.assertEqual(actual[2],{'onnx_rows':3,'below_storage_floor':2})
        np.testing.assert_array_equal(actual[0],expected[0])
        self.assertFalse(self.capture.directory.exists())

    def test_raw_degenerate_capture_and_exact_npy(self):
        out = outputs([[1,2,1,3,.7]])
        r = self.capture_failure(out,'degenerate retained detector box')
        self.assertEqual(r['offending_raw_nonpositive_extent_count'],1)
        self.assertEqual(r['offending_strictly_positive_raw_float32_collapse_count'],0)
        raw = np.load(self.capture.directory/'raw_output_0.npy',allow_pickle=False)
        self.assertEqual(raw.dtype,out[0].dtype); self.assertEqual(raw.tobytes(),out[0].tobytes())
        self.assertEqual(r['row_summaries'][0]['raw_score']['float_hex'],float(out[0][0,0,4]).hex())

    def test_float32_collapse_distinct_from_raw(self):
        r = self.capture_failure(outputs([[16777216,2,16777217,3,.8]]),'degenerate retained detector box')
        row=r['row_summaries'][0]
        self.assertFalse(row['raw_nonpositive_extent'])
        self.assertTrue(row['strictly_positive_raw_collapsed_in_float32'])
        self.assertEqual(r['offending_strictly_positive_raw_float32_collapse_count'],1)

    def test_float32_overflow_is_not_finite_precision_collapse(self):
        with np.errstate(over='ignore'):
            r=self.capture_failure(outputs([[1e300,2,2e300,3,.8]]),'degenerate retained detector box')
        row=r['row_summaries'][0]
        self.assertTrue(row['raw_coordinates_finite'])
        self.assertFalse(row['float32_coordinates_finite'])
        self.assertFalse(row['strictly_positive_raw_collapsed_in_float32'])
        self.assertTrue(row['finite_raw_became_nonfinite_float32'])
        self.assertEqual(r['offending_strictly_positive_raw_float32_collapse_count'],0)
        self.assertEqual(r['offending_finite_raw_nonfinite_float32_count'],1)

    def test_indices_storage_analysis_and_multiple_offending_rows(self):
        r=self.capture_failure(outputs([[0,0,0,0,.0],[1,1,9,9,.6],[2,3,2,4,.5],[4,5,6,5,.05]]),'degenerate retained detector box')
        self.assertEqual([x['original_row_index'] for x in r['row_summaries']],[2,3])
        self.assertTrue(all(x['float32_score_gte_storage_floor'] for x in r['row_summaries']))
        self.assertFalse(any(x['float32_score_gt_analysis_threshold'] for x in r['row_summaries']))
        self.assertEqual(np.load(self.capture.directory/'offending_original_row_indices.npy',allow_pickle=False).tolist(),[2,3])

    def test_later_floor_refusal_is_separate(self):
        r=self.capture_failure(outputs([[.1,.1,.11,.11,.9]]),'floor produced degenerate retained box')
        self.assertEqual(r['guard_stage'],'after_original_scaling_offset_floor')
        self.assertFalse(r['row_summaries'][0]['float32_nonpositive_extent'])
        self.assertIn('diagnostic_reconstructed_pre_floor',r['arrays'])
        divided=np.load(self.capture.directory/'diagnostic_reconstructed_pre_floor.npy',allow_pickle=False)
        final=np.load(self.capture.directory/'decoder_box.npy',allow_pickle=False)
        np.testing.assert_array_equal(np.floor(divided).astype(np.float32),final)

    def test_malformed_output_count(self):
        r=self.capture_failure([np.zeros((1,2,5))],'exactly dets and labels')
        self.assertFalse(r['context']['execute_frame_verified'])
        self.assertEqual(r['output_count'],1)
        self.assertTrue(r['arrays']['raw_output_0']['retained'])

    def test_malformed_shape(self):
        r=self.capture_failure([np.zeros((1,2,4)),np.zeros((1,2),dtype=np.int64)],'unexpected detector output shape')
        self.assertEqual(r['arrays']['raw_output_0']['shape'],[1,2,4])

    def test_invalid_confidence_and_nonfinite_raw_preserved(self):
        out=outputs([[0,1,10,20,float('nan')]])
        r=self.capture_failure(out,'invalid confidence or nonfinite output')
        raw=np.load(self.capture.directory/'raw_output_0.npy',allow_pickle=False)
        self.assertTrue(np.isnan(raw[0,0,4]))
        self.assertEqual(r['exception']['type'],'ValueError')

    def test_invalid_class_guard(self):
        out=outputs([[1,2,3,4,.9]]);out[1][0,0]=1
        r=self.capture_failure(out,'unexpected foreground class')
        self.assertEqual(r['guard_stage'],'other_original_guard')
        self.assertEqual(np.load(self.capture.directory/'raw_output_1.npy',allow_pickle=False).tolist(),[[1]])

    def test_object_dtype_never_pickled(self):
        out=[np.array([[[0,1,2,3,.9]]],dtype=object),np.zeros((1,1),dtype=np.int64)]
        r=self.capture_failure(out,'')
        self.assertFalse(r['arrays']['raw_output_0']['retained'])
        self.assertFalse((self.capture.directory/'raw_output_0.npy').exists())
        self.assertTrue(r['capture_refusals'])

    def test_logging_failure_preserves_same_exception(self):
        seen=[]
        def failed(exc,*args):seen.append(exc);raise OSError('authored log failure')
        self.capture.save=failed
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            try:self.worker.decode_output(outputs([[1,2,1,3,.7]]),0,0,800)
            except ValueError as error:self.assertIs(error,seen[0])
            else:self.fail('original exception suppressed')
        self.assertIn('diagnostic_capture_failed:OSError',stderr.getvalue())

    def test_capture_size_refusal_still_preserves_original_guard(self):
        with patch.object(diag,'MAX_ARRAY_BYTES',4):
            r=self.capture_failure(outputs([[1,2,1,3,.7]]),'degenerate retained detector box')
        self.assertFalse(r['arrays']['raw_output_0']['retained'])
        self.assertTrue(r['capture_refusals'])
        self.assertEqual(r['exception']['message'],'degenerate retained detector box')
        self.assertNotIn('offending_row_count',r)
        self.assertIn('row_analysis_size_or_dtype_cap',r['capture_refusals'])

    def test_analysis_row_cap_precedes_index_allocation(self):
        with patch.object(diag,'MAX_ANALYSIS_ROWS',1),patch.object(np,'flatnonzero',side_effect=AssertionError('must not allocate indices')):
            r=self.capture_failure(outputs([[1,2,1,3,.7],[2,2,2,4,.9]]),'degenerate retained detector box')
        self.assertIn('row_analysis_size_or_dtype_cap',r['capture_refusals'])
        self.assertNotIn('offending_row_count',r)

    def test_total_capture_byte_cap(self):
        with patch.object(diag,'MAX_CAPTURE_BYTES',4500):
            r=self.capture_failure(outputs([[1,2,1,3,.7]]),'degenerate retained detector box')
        self.assertLessEqual(r['retained_array_file_bytes'],4500)
        self.assertTrue(r['capture_refusals'])

    def test_summary_truncation_preserves_total_and_indices(self):
        with patch.object(diag,'MAX_ROW_SUMMARIES',1):
            r=self.capture_failure(outputs([[1,2,1,3,.7],[2,2,2,4,.9]]),'degenerate retained detector box')
        self.assertEqual(r['offending_row_count'],2)
        self.assertEqual(len(r['row_summaries']),1)
        self.assertTrue(r['row_summaries_truncated'])
        self.assertEqual(np.load(self.capture.directory/'offending_original_row_indices.npy',allow_pickle=False).tolist(),[0,1])

    def test_existing_capture_path_not_overwritten(self):
        self.capture.directory.mkdir();marker=self.capture.directory/'marker';marker.write_bytes(b'unchanged')
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaisesRegex(ValueError,'degenerate retained detector box'):
                self.worker.decode_output(outputs([[1,2,1,3,.7]]),0,0,800)
        self.assertEqual(marker.read_bytes(),b'unchanged')

    def test_actual_execute_context_with_authored_sessions(self):
        import onnxruntime as ort
        import tifffile
        import resource
        manifest=self.base/'manifest.json';manifest.write_text('{}')
        out=self.base/'execute-output'
        self.capture.directory=out/'decode-diagnostic'
        m={'limits':{'wall_seconds':30,'max_tiles_per_image':4,'max_raw_boxes_per_image':100},
           'models':{'faster':{'path':'authored-faster','sha256':'a'*64},'yolo':{'path':'authored-yolo','sha256':'b'*64}},
           'protocol':{'path':'authored-protocol','sha256':self.worker.PROTOCOL_SHA256},
           'images':[{'id':'authored-image','source':{'path':'authored-image','sha256':'c'*64}}]}
        sessions=[]
        class Session:
            def __init__(self,*a,**k):self.n=0;sessions.append(self)
            def get_providers(self):return ['CPUExecutionProvider']
            def get_inputs(self):return [types.SimpleNamespace(name='input',shape=[1,3,2,2],type='tensor(float)')]
            def get_outputs(self):return [types.SimpleNamespace(name='dets',shape=[1,1,5],type='tensor(float)'),types.SimpleNamespace(name='labels',shape=[1,1],type='tensor(int64)')]
            def run(self,*a,**k):
                self.n+=1
                return outputs([[1,2,1 if len(sessions)==2 and self.n==2 else 10,20,.7]])
        class TIFF:
            def __init__(self,*a):self.series=[types.SimpleNamespace(shape=(2,2),asarray=lambda:np.zeros((2,2),dtype=np.uint16))]
            def __enter__(self):return self
            def __exit__(self,*a):return False
        with patch.object(self.worker,'validated_manifest',return_value=m),patch.object(self.worker,'checked_file',return_value=b'authored'),patch.object(self.worker,'prepare_image',return_value=(np.zeros((512,768),dtype=np.uint8),(1,257),(2,2))),patch.object(self.worker,'model_input',return_value=(np.zeros((1,3,2,2),dtype=np.float32),800)),patch.object(ort,'InferenceSession',Session),patch.object(tifffile,'TiffFile',TIFF),patch.object(resource,'setrlimit'):
            with self.assertRaisesRegex(ValueError,'degenerate retained detector box'):
                self.worker.execute(manifest,out)
        r=json.loads((self.capture.directory/'diagnostic.json').read_text())
        c=r['context']
        self.assertTrue(c['execute_frame_verified'])
        self.assertEqual((c['model'],c['image_id'],c['ordinal'],c['rescaled_row'],c['rescaled_column']),('yolo','authored-image',1,0,256))
        self.assertEqual(c['tensor']['shape'],[1,3,2,2])
        self.assertEqual(c['tensor']['c_order_data_sha256'],hashlib.sha256(np.zeros((1,3,2,2),dtype=np.float32).tobytes()).hexdigest())
        self.assertEqual(len(sessions),2)
        self.assertEqual([s.n for s in sessions],[2,2])


if __name__=='__main__':unittest.main(verbosity=2)
