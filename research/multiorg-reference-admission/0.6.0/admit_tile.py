#!/usr/bin/env python3
"""Corrected variant's own observed-origin admission. No original baseline.

NN computation is not independently reexecuted. The unchanged0.4 reference
re-expresses ORT1.23.0 helper arithmetic; see THIRD_PARTY_NOTICES.md.
"""
from pathlib import Path
import hashlib
import types
import numpy as np

CORE_SHA='428579d22cfa49588c76172999c90beab3cb57e13a04540aa5bdc6ac413f1d7c'
raw=Path(__file__).with_name('reference_core.py').read_bytes()
if hashlib.sha256(raw).hexdigest()!=CORE_SHA:raise ValueError('reference core binding')
c=types.ModuleType('_bound_reference_core');c.__file__=str(Path(__file__).with_name('reference_core.py'))
exec(compile(raw,c.__file__,'exec'),c.__dict__)
Refusal=c.Refusal
# Ordered graph fetch roster. Maximum dimensions come from firstNMS1000,
# TopK6 1000, finalNMS200 and finalTopK100; one batch/foreground class.
SPECS=[('dets','<f4',(1,100,5)),('labels','<i8',(1,100)),
('/Where_6_output_0','<f4',(1,1000,5)),('/ConstantOfShape_11_output_0','<f4',(1,1,5)),
('/Concat_87_output_0','<f4',(1,1001,5)),('/TopK_6_output_0','<f4',(1,1000)),
('/Reshape_80_output_0','<f4',(1,1000,5)),('/Reshape_83_output_0','<f4',(1000,5)),
('/bbox_head/fc_cls/Gemm_output_0','<f4',(1000,2)),('/bbox_head/fc_reg/Gemm_output_0','<f4',(1000,4)),
('/Softmax_output_0','<f4',(1,1000,2)),('/Add_37_output_0','<f4',(1,1000,1,4)),
('/Sub_3_output_0','<f4',(1,1000,1,2)),('/Add_40_output_0','<f4',(1,1000,1,2)),
('/Reshape_88_output_0','<f4',(1,1000,4)),('/Slice_14_output_0','<f4',(1,1000,1)),
('/Reshape_93_output_0','<f4',(1,1000,4)),('/TopK_7_output_0','<f4',(1,1000)),
('/Reshape_97_output_0','<f4',(1,1000,4)),('/Transpose_12_output_0','<f4',(1,1,1000)),
('/Where_10_output_0','<f4',(1,200,5)),('/ConstantOfShape_15_output_0','<f4',(1,1,5)),
('/Concat_114_output_0','<f4',(1,201,5)),('/TopK_8_output_0','<f4',(1,100)),
('/TopK_6_output_1','<i8',(1,1000)),('/TopK_7_output_1','<i8',(1,1000)),
('/NonMaxSuppression_1_output_0','<i8',(200,3)),('/Where_11_output_0','<i8',(1,200)),
('/ConstantOfShape_16_output_0','<i8',(1,1)),('/Concat_116_output_0','<i8',(1,201)),
('/TopK_8_output_1','<i8',(1,100)),
('reiyah_validity_v040/unmasked_foreground','<f4',(1,1000,1)),
('reiyah_validity_v040/valid_rpn_origin','|b1',(1,1000))]
NAMES=tuple(row[0] for row in SPECS)
MAX_PAYLOAD_BYTES=sum(int(np.prod(shape))*np.dtype(dtype).itemsize for _,dtype,shape in SPECS)
MAX_TILE_NPY_BYTES=MAX_PAYLOAD_BYTES+4096*len(SPECS)

def validate_tile(a):
    c.need(isinstance(a,dict) and tuple(a)==NAMES,'exact ordered33-output roster')
    for name,dtype,bounds in SPECS:
        value=a[name]
        c.need(isinstance(value,np.ndarray) and value.dtype.str==dtype and value.ndim==len(bounds),name+' dtype/rank')
        c.need(all(actual<=cap for actual,cap in zip(value.shape,bounds)),name+' shape cap')
        if value.dtype.kind=='f':c.need(np.isfinite(value).all(),name+' finite')
    n=a[c.BEFORE].shape[1];k=a[c.ORDER6].shape[1]
    c.array(a[c.BEFORE],(1,n,5),'float32','before');c.need(n<=1000,'first NMS cap')
    c.array(a[c.ORDER6],(1,k),'int64','origin indices');c.need(k==min(n+1,1000),'TopK6 count')
    c.same(a['/ConstantOfShape_11_output_0'],np.zeros((1,1,5),np.float32),'explicit RPN append')
    concat=np.concatenate((a[c.BEFORE],a['/ConstantOfShape_11_output_0']),axis=1)
    c.same(a['/Concat_87_output_0'],concat,'RPN concat bytes')
    ids6=c.sorted_ids(concat[0,:,4],1000)
    c.same(a[c.ORDER6],ids6[None,:],'TopK6 sorted origin indices')
    c.same(a['/TopK_6_output_0'],concat[:,:,4][:,ids6],'TopK6 values')
    props=concat[:,ids6,:];c.same(a['/Reshape_80_output_0'],props,'proposal gather')
    rois=np.concatenate((np.zeros((k,1),np.float32),props[0,:,:4]),axis=1)
    c.same(a['/Reshape_83_output_0'],rois,'ROI placement')
    for name,shape in [('/bbox_head/fc_cls/Gemm_output_0',(k,2)),('/bbox_head/fc_reg/Gemm_output_0',(k,4)),
        ('/Softmax_output_0',(1,k,2)),('/Add_37_output_0',(1,k,1,4)),('/Sub_3_output_0',(1,k,1,2)),
        ('/Add_40_output_0',(1,k,1,2)),('/Reshape_88_output_0',(1,k,4)),(c.BOX,(1,k,4)),(c.RAW,(1,k,1))]:
        c.array(a[name],shape,'float32',name)
    probabilities=a['/Softmax_output_0'];c.need(np.all((probabilities>=0)&(probabilities<=1)),'probability range')
    c.same(a[c.RAW],probabilities[:,:,:1],'raw foreground slice')
    c.same(a[c.BOX],a['/Reshape_88_output_0'],'single-class decoded row placement')
    mask=ids6[None,:]<n;c.same(a[c.MASK],mask,'origin mask by indices')
    masked=a[c.RAW].copy();masked[~mask[:,:,None]]=np.float32(0)
    c.same(a[c.FG],masked,'masked foreground values')
    ref=c.direct_reference(a[c.BOX][0],a[c.RAW][0,:,0],ids6,n)
    ids7=c.sorted_ids(masked[0,:,0],5000)
    c.same(a['/TopK_7_output_1'],ids7[None,:],'TopK7 indices')
    c.same(a['/TopK_7_output_0'],masked[:,:,0][:,ids7],'TopK7 values')
    c.same(a['/Reshape_97_output_0'],a[c.BOX][:,ids7,:],'pre-NMS box gather')
    c.same(a['/Transpose_12_output_0'],masked[:,ids7,:].transpose(0,2,1),'pre-NMS score gather')
    inverse={int(roi):i for i,roi in enumerate(ids7)};m=len(ref['nms_roi_indices'])
    nms=np.array([[0,0,inverse[i]] for i in ref['nms_roi_indices']],np.int64).reshape(m,3)
    c.same(a['/NonMaxSuppression_1_output_0'],nms,'direct NMS selected identities')
    c.same(a['/Where_10_output_0'],ref['final_concat'][:,:m,:],'NMS detections')
    c.same(a['/Where_11_output_0'],np.zeros((1,m),np.int64),'NMS labels')
    c.same(a['/ConstantOfShape_15_output_0'],np.zeros((1,1,5),np.float32),'final padding')
    c.same(a['/ConstantOfShape_16_output_0'],np.zeros((1,1),np.int64),'final padding label')
    c.same(a['/Concat_114_output_0'],ref['final_concat'],'final concat')
    c.same(a['/Concat_116_output_0'],np.zeros((1,m+1),np.int64),'final label concat')
    c.same(a['/TopK_8_output_1'],np.array([ref['final_order']],np.int64),'finalTopK indices')
    c.same(a['/TopK_8_output_0'],ref['dets'][:,:,4],'finalTopK values')
    c.same(a['dets'],ref['dets'],'final detections');c.same(a['labels'],ref['labels'],'final labels')
    return {'status':'corrected_variant_tile_admitted','scope':'own raw-head/index/direct-selection contract; no original baseline comparison',
        'original_baseline_comparison_performed':False,'pre_append_rpn_rows':n,'roi_rows':k,'final_raw_rows':len(ref['rows']),
        'excluded_roi_indices':ref['excluded_roi_indices'],'selected_roi_indices':ref['nms_roi_indices'],'final_rows':ref['rows'],
        'final_padding_rows':sum(x['origin']=='final_padding_metadata' for x in ref['rows']),
        'excluded_origins':[{'roi_row':i,'rpn_concat_row':int(ids6[i]),'reason':'explicit appended RPN operand by index',
            'unmasked_foreground_score':float(a[c.RAW][0,i,0]),'decoded_box_xyxy':[float(x) for x in a[c.BOX][0,i]]}
            for i in ref['excluded_roi_indices']]}
