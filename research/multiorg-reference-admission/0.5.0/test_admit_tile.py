import copy
import unittest
import numpy as np
import admit_tile as h

def fixture(n=3):
    k=min(n+1,1000);a={}
    before=np.zeros((1,n,5),np.float32)
    if n==3:before[0]=[[0,0,10,10,.9],[40,40,50,50,.7],[20,20,30,30,.8]]
    elif n==1000:
        before[0,:,0]=np.arange(n)*20;before[0,:,1]=1;before[0,:,2]=before[0,:,0]+10;before[0,:,3]=11;before[0,:,4]=.8
    elif n!=0:raise AssertionError('authored fixture n')
    concat=np.concatenate((before,np.zeros((1,1,5),np.float32)),1)
    ids=np.array([0,2,1,3] if n==3 else range(k),np.int64)
    props=concat[:,ids,:];boxes=props[:,:,:4].copy()
    fg=np.array([.8,.7,.1,.9] if n==3 else [.9] if n==0 else [.01]*k,np.float32).reshape(1,k,1)
    masked=fg.copy();masked[:,ids==n,:]=0
    o7=np.arange(k,dtype=np.int64)
    m=3 if n==3 else 0
    dets=np.array([[[0,0,10,10,.8],[20,20,30,30,.7],[40,40,50,50,.1]]],np.float32) if n==3 else np.empty((1,0,5),np.float32)
    final=np.concatenate((dets,np.zeros((1,1,5),np.float32)),1)
    known={'dets':final,'labels':np.zeros((1,m+1),np.int64),'/Where_6_output_0':before,
        '/ConstantOfShape_11_output_0':np.zeros((1,1,5),np.float32),'/Concat_87_output_0':concat,
        '/TopK_6_output_0':concat[:,:,4][:,ids],'/TopK_6_output_1':ids[None,:],'/Reshape_80_output_0':props,
        '/Reshape_83_output_0':np.concatenate((np.zeros((k,1),np.float32),props[0,:,:4]),1),
        '/bbox_head/fc_cls/Gemm_output_0':np.zeros((k,2),np.float32),'/bbox_head/fc_reg/Gemm_output_0':np.zeros((k,4),np.float32),
        '/Softmax_output_0':np.concatenate((fg,1-fg),2),'/Add_37_output_0':np.zeros((1,k,1,4),np.float32),
        '/Sub_3_output_0':boxes[:,:,:2].reshape(1,k,1,2),'/Add_40_output_0':boxes[:,:,2:].reshape(1,k,1,2),
        '/Reshape_88_output_0':boxes.copy(),'/Reshape_93_output_0':boxes.copy(),'/Slice_14_output_0':masked,
        '/TopK_7_output_0':masked[:,:,0],'/TopK_7_output_1':o7[None,:],'/Reshape_97_output_0':boxes.copy(),
        '/Transpose_12_output_0':masked.transpose(0,2,1),'/NonMaxSuppression_1_output_0':np.array([[0,0,i] for i in range(m)],np.int64).reshape(m,3),
        '/Where_10_output_0':dets,'/Where_11_output_0':np.zeros((1,m),np.int64),
        '/ConstantOfShape_15_output_0':np.zeros((1,1,5),np.float32),'/ConstantOfShape_16_output_0':np.zeros((1,1),np.int64),
        '/Concat_114_output_0':final.copy(),'/Concat_116_output_0':np.zeros((1,m+1),np.int64),
        '/TopK_8_output_0':final[:,:,4],'/TopK_8_output_1':np.arange(m+1,dtype=np.int64)[None,:],
        h.c.RAW:fg,h.c.MASK:(ids<n)[None,:]}
    return {name:known[name] for name in h.NAMES}

class Tests(unittest.TestCase):
    def test_complete_own_contract_no_baseline(self):
        a=fixture();before={k:v.tobytes() for k,v in a.items()};r=h.validate_tile(a)
        self.assertFalse(r['original_baseline_comparison_performed']);self.assertEqual(r['selected_roi_indices'],[0,1,2]);self.assertEqual(r['excluded_roi_indices'],[3])
        self.assertEqual(before,{k:v.tobytes() for k,v in a.items()})
    def test_no_genuine_proposals(self):
        r=h.validate_tile(fixture(0));self.assertEqual(r['selected_roi_indices'],[]);self.assertEqual(r['final_padding_rows'],1)
    def test_appended_origin_not_in_topk(self):
        r=h.validate_tile(fixture(1000));self.assertEqual(r['excluded_roi_indices'],[]);self.assertEqual(r['roi_rows'],1000)
    def test_missing_extra_reordered_roster(self):
        for mode in ('missing','extra','reordered'):
            a=fixture()
            if mode=='missing':del a[h.NAMES[3]]
            elif mode=='extra':a['extra']=np.zeros(1)
            else:a=dict(reversed(list(a.items())))
            with self.subTest(mode=mode),self.assertRaises(h.Refusal):h.validate_tile(a)
    def test_shifted_mask_origin_score_box(self):
        for name in (h.c.MASK,h.c.ORDER6,h.c.RAW,h.c.FG,h.c.BOX,'/TopK_7_output_1','/NonMaxSuppression_1_output_0','dets'):
            a=fixture();a[name]=a[name].copy()
            if a[name].dtype.kind=='b':a[name].flat[0]=False
            else:a[name].flat[0]+=1
            with self.subTest(name=name),self.assertRaises(h.Refusal):h.validate_tile(a)
    def test_bad_high_geometry_retained_then_refused(self):
        a=fixture()
        for name in (h.c.BOX,'/Reshape_88_output_0'):a[name]=a[name].copy();a[name][0,0,:]=0
        with self.assertRaisesRegex(h.Refusal,'genuine invalid'):h.validate_tile(a)
    def test_batch_nonfinite_type_and_cap(self):
        for mode in ('batch','nonfinite','dtype','cap'):
            a=fixture()
            if mode=='batch':a[h.c.BEFORE]=np.zeros((2,3,5),np.float32)
            elif mode=='nonfinite':a[h.c.RAW]=a[h.c.RAW].copy();a[h.c.RAW].flat[0]=np.nan
            elif mode=='dtype':a[h.c.MASK]=a[h.c.MASK].astype(np.int64)
            else:a[h.c.BEFORE]=np.zeros((1,1001,5),np.float32)
            with self.subTest(mode=mode),self.assertRaises(h.Refusal):h.validate_tile(a)
    def test_byte_budget(self):
        self.assertEqual(h.MAX_PAYLOAD_BYTES,249096);self.assertEqual(h.MAX_TILE_NPY_BYTES,384264)
        self.assertEqual(len(h.NAMES),33)

if __name__=='__main__':unittest.main()
