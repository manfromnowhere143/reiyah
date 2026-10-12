"""Authored controls only. Never reads model/TIFF payloads or runs ONNX."""
import hashlib
import importlib.util
import json
from pathlib import Path
import types
import unittest
import numpy as np
import projection as proposed

OWNER = Path(__file__).resolve().parents[1]
WORKER_SHA = '9a708bf6a22e9350980e0d08d0e90c2c56f7b9cc4a73b7fd55f22c9ef3f33e0c'
worker_path = OWNER/'inference/run_pair.py'
worker_bytes = worker_path.read_bytes()
if hashlib.sha256(worker_bytes).hexdigest() != WORKER_SHA:raise ValueError('worker hash')
worker = types.ModuleType('_bound_original');worker.__file__=str(worker_path)
exec(compile(worker_bytes,str(worker_path),'exec'),worker.__dict__)


def scalar_iou(a,b):
    # Separately implemented scalar evaluation, same declared float32 arithmetic.
    f=np.float32
    iw=max(f(0),f(min(a[2],b[2])-max(a[0],b[0])))
    ih=max(f(0),f(min(a[3],b[3])-max(a[1],b[1])))
    intersection=f(iw*ih)
    area_a=f(f(a[2]-a[0])*f(a[3]-a[1]))
    area_b=f(f(b[2]-b[0])*f(b[3]-b[1]))
    return f(intersection/f(f(area_a+area_b)-intersection))


def full_reference_nms(boxes,scores,order=None):
    # Never imports or calls the producer's NMS.
    if order is None:order=sorted(range(len(scores)),key=lambda i:(-float(scores[i]),i))
    kept=[]
    for current in order:
        if all(scalar_iou(boxes[current],boxes[prior])<=np.float32(.5) for prior in kept):
            kept.append(current)
    return kept


def outputs(rows,dtype=np.float32):
    return [np.asarray(rows,dtype=dtype).reshape(1,-1,5),np.zeros((1,len(rows)),dtype=np.int64)]


def tile(rows,dtype=np.float32,remaining=200000):
    return proposed.project_tile(outputs(rows,dtype),0,0,800,decoder=worker.decode_output,remaining_raw_rows=remaining)


def whole(result):
    return proposed.complete_projection([{'ordinal':0,'projection':result}],expected_tiles=1,raw_cap=200000,nms=worker.stable_nms)


class ProjectionControls(unittest.TestCase):
    def test_valid_full_comparator_500_authored_arrays(self):
        rng=np.random.default_rng(8122026)
        choices=np.array([.0,.04,.05,.49,.5,np.nextafter(np.float32(.5),np.float32(1)),.7,.9,.9],dtype=np.float32)
        for case in range(500):
            n=case%31
            xy=rng.integers(-20,40,(n,2));size=rng.integers(2,30,(n,2))
            rows=np.column_stack((xy,xy+size,rng.choice(choices,n))).astype(np.float32)
            out=outputs(rows)
            full_boxes,full_scores,_=worker.decode_output(out,0,0,800)
            full_ids=np.flatnonzero(out[0][0,:,4]>=np.float32(.05))
            selected=full_reference_nms(full_boxes,full_scores)
            expected=[(0,int(full_ids[i])) for i in selected if full_scores[i]>.5]
            got=whole(tile(rows))
            self.assertEqual(got['analysis_row_ids'],expected,msg=f'authored case {case}')
            self.assertEqual(got['all_raw_rows'],n)

    def test_equal_score_stable_original_order(self):
        result=whole(tile([[0,0,10,10,.8],[0,0,10,10,.8],[50,50,60,60,.8]]))
        self.assertEqual(result['analysis_row_ids'],[(0,0),(0,2)])

    def test_strict_half_and_float32_boundary(self):
        half=float(np.float32(.5));below=float(np.nextafter(np.float32(.5),np.float32(0)))
        above=float(np.nextafter(np.float32(.5),np.float32(1)))
        rounds_to_half=.5+2**-26
        p=tile([[0,0,10,10,below],[20,0,30,10,half],[40,0,50,10,above],[60,0,70,10,rounds_to_half]],np.float64)
        self.assertEqual(p['original_row_indices'].tolist(),[2])
        self.assertEqual(p['raw_above_half_converted_not_above_half_rows'],1)

    def test_low_invalid_recorded_without_defined_full_storage_claim(self):
        p=tile([[0,0,0,0,.357],[5,5,10,10,.9],[1,1,2,2,0]])
        self.assertEqual(p['low_geometry_anomalies']['raw_nonpositive_extent'].tolist(),[0])
        self.assertEqual(p['all_raw_rows'],3)
        self.assertEqual(p['decoder_subset_counts']['onnx_rows'],1)
        self.assertEqual(p['storage_output_status'],'not_defined_or_exported_by_this_contract')
        self.assertEqual(whole(p)['analysis_row_ids'],[(0,1)])

    def test_padding_and_storage_anomalies_remain_distinct(self):
        p=tile([[0,0,0,0,0],[0,0,0,0,.35],[1,1,10,10,.8]])
        self.assertEqual(p['low_geometry_anomalies']['raw_nonpositive_extent'].tolist(),[0,1])
        self.assertEqual(p['storage_eligible_low_geometry_anomalies']['raw_nonpositive_extent'].tolist(),[1])
        self.assertEqual(p['below_storage_floor_rows'],1)
        out=outputs([[0,0,0,0,0],[1,1,10,10,.8]]);out[1][0,0]=99
        q=proposed.project_tile(out,0,0,800,decoder=worker.decode_output,remaining_raw_rows=2)
        self.assertEqual(q['high_rows'],1)

    def test_every_valid_low_completion_has_same_high_result_256_cases(self):
        rng=np.random.default_rng(4321)
        high=np.array([[0,0,20,20,.9],[1,1,21,21,.8],[40,40,60,60,.7]],dtype=np.float32)
        reference=whole(tile(high))['analysis_row_ids']
        for _ in range(256):
            lowxy=rng.integers(-100,100,(6,2));lowwh=rng.integers(2,60,(6,2))
            lows=np.column_stack((lowxy,lowxy+lowwh,np.full(6,.4))).astype(np.float32)
            # Interleave lower rows without changing high relative order.
            rows=np.vstack((lows[:2],high[:1],lows[2:4],high[1:],lows[4:]))
            box,score,_=worker.decode_output(outputs(rows),0,0,800)
            keep=full_reference_nms(box,score)
            full_high=[i for i in keep if score[i]>.5]
            remap={2:0,5:1,6:2}
            self.assertEqual([(0,remap[i]) for i in full_high],reference)

    def test_high_invalid_raw_geometry_rejected(self):
        with self.assertRaisesRegex(ValueError,'undefined high-score geometry'):tile([[0,0,0,0,.6]])

    def test_high_float32_collapse_rejected(self):
        with self.assertRaisesRegex(ValueError,'undefined high-score geometry'):tile([[16777216,1,16777217,2,.6]],np.float64)

    def test_high_decoded_floor_collapse_rejected(self):
        with self.assertRaisesRegex(ValueError,'floor produced degenerate'):tile([[.1,.1,.11,.11,.6]],np.float64)

    def test_unknown_nonfinite_or_out_of_range_score_rejected_even_on_invalid_low_box(self):
        for value in [float('nan'),float('inf'),float('-inf'),-.1,1.1]:
            with self.subTest(score=str(value)),self.assertRaisesRegex(ValueError,'invalid score'):
                tile([[0,0,0,0,value]])

    def test_nonfinite_coordinates_rejected_at_every_score_level(self):
        for score in [0,.04,.4,.8]:
            for value in [float('nan'),float('inf'),float('-inf')]:
                with self.subTest(score=score,value=str(value)),self.assertRaisesRegex(ValueError,'nonfinite raw coordinate'):
                    tile([[value,0,2,2,score]])

    def test_float32_coordinate_overflow_rejected_at_every_score_level(self):
        for score in [0,.04,.4,.8]:
            with self.subTest(score=score),self.assertRaisesRegex(ValueError,'nonfinite float32 coordinate conversion'):
                tile([[1e300,0,2e300,2,score]],np.float64)

    def test_all_raw_work_count_before_filtering(self):
        with self.assertRaisesRegex(ValueError,'all-raw-row work cap'):
            tile([[0,0,0,0,0]]*10,remaining=9)
        p=tile([[0,0,0,0,0]]*10,remaining=10)
        self.assertEqual(p['all_raw_rows'],10);self.assertEqual(p['high_rows'],0)
        with self.assertRaisesRegex(ValueError,'all-raw-row work cap'):
            proposed.complete_projection([{'ordinal':0,'projection':p},{'ordinal':1,'projection':p}],expected_tiles=2,raw_cap=19,nms=worker.stable_nms)

    def test_complete_tile_coverage_and_stable_cross_tile_ties(self):
        p=tile([[0,0,10,10,.8]])
        valid=[{'ordinal':0,'projection':p},{'ordinal':1,'projection':p}]
        got=proposed.complete_projection(valid,expected_tiles=2,raw_cap=200000,nms=worker.stable_nms)
        self.assertEqual(got['analysis_row_ids'],[(0,0)])
        for bad in [valid[:1],[valid[0],valid[0]],list(reversed(valid))]:
            with self.assertRaises(ValueError):proposed.complete_projection(bad,expected_tiles=2,raw_cap=200000,nms=worker.stable_nms)

    def test_required_labels_and_shapes_fail_closed(self):
        out=outputs([[0,0,10,10,.4]]);out[1][0,0]=1
        with self.assertRaisesRegex(ValueError,'foreground label'):
            proposed.project_tile(out,0,0,800,decoder=worker.decode_output,remaining_raw_rows=10)
        for out in [[np.zeros((1,1,4)),np.zeros((1,1),dtype=np.int64)],[np.zeros((1,1,5)),np.zeros((1,1),dtype=float)]]:
            with self.assertRaises(ValueError):proposed.project_tile(out,0,0,800,decoder=worker.decode_output,remaining_raw_rows=10)

    def test_low_first_traversal_counterexample(self):
        boxes=np.array([[0,0,10,10],[0,0,10,10]],dtype=np.float32);scores=np.array([.4,.9],dtype=np.float32)
        wrong=full_reference_nms(boxes,scores,order=[0,1])
        self.assertEqual([i for i in wrong if scores[i]>.5],[])
        self.assertEqual(full_reference_nms(boxes[1:],scores[1:]),[0])

    def test_global_score_updating_counterexample(self):
        # A specific global renormalizer, not a claim that every Soft-NMS fails.
        boxes=np.array([[0,0,10,10],[20,20,30,30],[40,40,50,50]],dtype=np.float32)
        fixed=np.array([.6,.4,.4],dtype=np.float32)
        all_updated=fixed/fixed.sum(dtype=np.float32)
        high_updated=fixed[:1]/fixed[:1].sum(dtype=np.float32)
        full_kept=full_reference_nms(boxes,all_updated)
        self.assertEqual([i for i in full_kept if all_updated[i]>.5],[])
        self.assertEqual([i for i in full_reference_nms(boxes[:1],high_updated) if high_updated[i]>.5],[0])

    def test_original_worker_unchanged_and_raw_arrays_unchanged(self):
        self.assertEqual(hashlib.sha256(worker_path.read_bytes()).hexdigest(),WORKER_SHA)
        out=outputs([[0,0,0,0,.4],[1,2,10,20,.8]])
        original=[a.tobytes() for a in out]
        proposed.project_tile(out,0,0,800,decoder=worker.decode_output,remaining_raw_rows=2)
        self.assertEqual(original,[a.tobytes() for a in out])


if __name__=='__main__':unittest.main(verbosity=2)
