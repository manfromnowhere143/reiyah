#!/usr/bin/env python3
"""Separately authored Python direct-removal reference and array checker.

No producer, graph builder, ONNX or ONNX Runtime import; no model execution.
suppress() re-expresses ONNX Runtime 1.23.0 CPU helper branch structure and
float32 operation order. Microsoft MIT attribution and license are retained
in THIRD_PARTY_NOTICES.md beside this file.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import numpy as np

ORIGINAL_MODEL_SHA='fbf748e6d8b896bed9ee1eb15d5dd1409369de5e32c4746c4173aa4c10e7bebd'
PRIOR_RESULT_SHA='2b7747c2119f9d79020bf6ebe82c459a408235af81ca58a240aed4803f4bb7f1'
GRAPH_SHA='efdf18c9029db8dca26a70de8103920f18501fbf7ba94fe4ae74ea1b6a43ee77'
RAW='reiyah_validity_v040/unmasked_foreground'
MASK='reiyah_validity_v040/valid_rpn_origin'
SCORE_FLOOR=np.float32(.05)
IOU_THRESHOLD=np.float32(.5)
ANALYSIS_THRESHOLD=np.float32(.5)
BEFORE='/Where_6_output_0'
ORDER6='/TopK_6_output_1'
FG='/Slice_14_output_0'
BOX='/Reshape_93_output_0'
# These precede final selection or preserve the one-class decoded coordinates.
UNCHANGED=(BEFORE,'/ConstantOfShape_11_output_0','/Concat_87_output_0',
    '/TopK_6_output_0',ORDER6,'/Reshape_80_output_0','/Reshape_83_output_0',
    '/bbox_head/fc_cls/Gemm_output_0','/bbox_head/fc_reg/Gemm_output_0',
    '/Softmax_output_0','/Add_37_output_0','/Sub_3_output_0','/Add_40_output_0',
    '/Reshape_88_output_0',BOX)

class Refusal(ValueError):pass

def need(ok,reason):
    if not ok:raise Refusal(reason)

def same(a,b,reason):
    need(a.dtype==b.dtype and a.shape==b.shape and a.tobytes(order='C')==b.tobytes(order='C'),reason)

def array(a,shape,dtype,reason):
    need(isinstance(a,np.ndarray) and a.dtype==np.dtype(dtype) and len(a.shape)==len(shape),reason+' dtype/rank')
    need(a.size<=200000 and all(s is None or s==v for s,v in zip(shape,a.shape)),reason+' shape/cap')
    if a.dtype.kind=='f':need(np.isfinite(a).all(),reason+' finite')
    return a

def fp(value):
    v=np.float32(value);need(np.isfinite(v),'nonfinite float32 NMS arithmetic');return v

def suppress(box1,box2):
    # ORT1.23.0 CPU center_point_box=0 normalizes each opposite-corner pair.
    # Coordinates are [y1,x1,y2,x2] to ORT. Axis interchange leaves IoU unchanged.
    x1lo,x1hi=sorted((box1[1],box1[3]));x2lo,x2hi=sorted((box2[1],box2[3]))
    xlo,xhi=max(x1lo,x2lo),min(x1hi,x2hi)
    if xhi<=xlo:return False
    y1lo,y1hi=sorted((box1[0],box1[2]));y2lo,y2hi=sorted((box2[0],box2[2]))
    ylo,yhi=max(y1lo,y2lo),min(y1hi,y2hi)
    if yhi<=ylo:return False
    intersection=fp(fp(xhi-xlo)*fp(yhi-ylo))
    if intersection<=0:return False
    area1=fp(fp(x1hi-x1lo)*fp(y1hi-y1lo));area2=fp(fp(x2hi-x2lo)*fp(y2hi-y2lo))
    union=fp(fp(area1+area2)-intersection)
    if area1<=0 or area2<=0 or union<=0:return False
    return bool(fp(intersection/union)>IOU_THRESHOLD)

def direct_reference(boxes,scores,rpn_indices,before_count,*,nms_cap=200,final_cap=100,pre_cap=5000):
    """Physically remove only explicit appended origin, then selection and caps.

    Invalid genuine geometry is retained through NMS. The original final >.5
    geometry obligation is enforced after final selection, never by filtering.
    Configurable caps exist for authored controls; empirical caller fixes200/100/5000.
    """
    array(boxes,(None,4),'float32','boxes');k=len(boxes)
    array(scores,(k,),'float32','scores');array(rpn_indices,(k,),'int64','rpn indices')
    need(type(before_count) is int and 0<=before_count<=10000,'pre-append row count')
    need(1<=k<=1000 and k==min(before_count+1,1000),'RPN TopK count')
    need(np.all(rpn_indices>=0) and np.all(rpn_indices<=before_count)
        and len(set(map(int,rpn_indices)))==k,'RPN index domain/uniqueness')
    need(np.all((scores>=0)&(scores<=1)),'probability range')
    need(all(type(v) is int and v>0 for v in (nms_cap,final_cap,pre_cap)) and pre_cap>=k,'cap domain/preselection truncation unsupported')
    valid=[i for i in range(k) if int(rpn_indices[i])<before_count]
    excluded=[i for i in range(k) if int(rpn_indices[i])==before_count]
    # Removal preserves original ROI-index tie order. TopK and NMS both prefer
    # lower input index on equal scores, and pre_cap cannot truncate this graph.
    ordered=sorted(valid,key=lambda i:(-float(scores[i]),i))[:pre_cap]
    selected=[]
    for i in ordered:
        if not scores[i]>SCORE_FLOOR:continue
        if all(not suppress(boxes[i],boxes[j]) for j in selected):
            selected.append(i)
            if len(selected)==nms_cap:break
    all_rows=[np.concatenate((boxes[i],scores[i:i+1])) for i in selected]
    all_rows.append(np.zeros(5,dtype=np.float32)) # explicit final metadata row
    all_rows=np.asarray(all_rows,dtype=np.float32).reshape(1,len(selected)+1,5)
    order=sorted(range(len(selected)+1),key=lambda i:(-float(all_rows[0,i,4]),i))[:final_cap]
    dets=all_rows[:,order,:].copy();labels=np.zeros((1,len(order)),dtype=np.int64)
    rows=[]
    for final,i in enumerate(order):
        roi=None if i==len(selected) else selected[i]
        geometry_positive=bool(dets[0,final,2]>dets[0,final,0] and dets[0,final,3]>dets[0,final,1])
        if roi is not None and dets[0,final,4]>ANALYSIS_THRESHOLD:
            need(geometry_positive,'genuine invalid final analysis geometry at ROI '+str(roi))
        rows.append({'final_row':final,'roi_row':roi,'origin':'final_padding_metadata' if roi is None else 'pre_append_rpn_candidate',
            'rpn_concat_row':None if roi is None else int(rpn_indices[roi]),'positive_raw_extent':geometry_positive,
            'score':float(dets[0,final,4]),'box_xyxy':[float(x) for x in dets[0,final,:4]]})
    return {'dets':dets,'labels':labels,'nms_roi_indices':selected,'final_order':order,'final_concat':all_rows,
        'rows':rows,'excluded_roi_indices':excluded,'valid_roi_indices':valid,'ordered_valid_roi_indices':ordered}

def sorted_ids(scores,cap):
    return np.array(sorted(range(len(scores)),key=lambda i:(-float(scores[i]),i))[:cap],dtype=np.int64)

def compare_taps(baseline,corrected):
    need(set(corrected)==set(baseline)|{RAW,MASK},'complete corrected tap roster')
    for name in UNCHANGED:same(corrected[name],baseline[name],'unaffected bytes changed: '+name)
    before=array(baseline[BEFORE],(1,None,5),'float32','pre-append population');n=before.shape[1]
    indices=array(baseline[ORDER6],(1,None),'int64','TopK6 indices');k=indices.shape[1]
    array(baseline[FG],(1,k,1),'float32','prior raw foreground')
    array(corrected[RAW],(1,k,1),'float32','unmasked foreground');same(corrected[RAW],baseline[FG],'unmasked scores changed')
    mask=array(corrected[MASK],(1,k),'bool','origin mask');same(mask,indices<n,'origin mask not index-derived')
    masked=array(corrected[FG],(1,k,1),'float32','masked foreground')
    expected_masked=baseline[FG].copy();expected_masked[~mask[:,:,None]]=np.float32(0)
    same(masked,expected_masked,'only proven padding score may change')
    boxes=array(baseline[BOX],(1,k,4),'float32','decoded boxes')
    ref=direct_reference(boxes[0],baseline[FG][0,:,0],indices[0],n)
    o7=sorted_ids(masked[0,:,0],5000)
    same(corrected['/TopK_7_output_1'],o7[None,:],'TopK7 sorted index/tie rule')
    same(corrected['/TopK_7_output_0'],masked[:,:,0][:,o7],'TopK7 scores')
    same(corrected['/Reshape_97_output_0'],boxes[:,o7,:],'pre-NMS gathered boxes')
    same(corrected['/Transpose_12_output_0'],masked[:,o7,:].transpose(0,2,1),'pre-NMS scores')
    inverse={int(roi):rank for rank,roi in enumerate(o7)}
    expected_nms=np.asarray([[0,0,inverse[roi]] for roi in ref['nms_roi_indices']],dtype=np.int64).reshape(-1,3)
    same(corrected['/NonMaxSuppression_1_output_0'],expected_nms,'scalar direct-removal NMS selected identities')
    m=len(ref['nms_roi_indices'])
    same(corrected['/Where_10_output_0'],ref['final_concat'][:,:m,:],'selected detection gather')
    same(corrected['/Where_11_output_0'],np.zeros((1,m),np.int64),'selected label gather')
    same(corrected['/ConstantOfShape_15_output_0'],np.zeros((1,1,5),np.float32),'final padding metadata')
    same(corrected['/ConstantOfShape_16_output_0'],np.zeros((1,1),np.int64),'final padding label')
    same(corrected['/Concat_114_output_0'],ref['final_concat'],'final concat')
    same(corrected['/Concat_116_output_0'],np.zeros((1,m+1),np.int64),'final label concat')
    same(corrected['/TopK_8_output_1'],np.array([ref['final_order']],dtype=np.int64),'final sorted identities')
    same(corrected['/TopK_8_output_0'],ref['dets'][:,:,4],'final sorted scores')
    same(corrected['dets'],ref['dets'],'final boxes/scores vs direct removal')
    same(corrected['labels'],ref['labels'],'final labels vs direct removal')
    return {'status':'direct_removal_comparison_passed','rpn_pre_append_rows':n,'roi_count':k,
        'valid_roi_count':len(ref['valid_roi_indices']),'excluded_roi_indices':ref['excluded_roi_indices'],
        'excluded_origins':[{'roi_row':i,'rpn_concat_row':int(indices[0,i]),'reason':'explicit appended RPN operand by index',
            'unmasked_foreground_score':float(baseline[FG][0,i,0]),'masked_foreground_score':float(masked[0,i,0]),
            'decoded_box_xyxy':[float(x) for x in boxes[0,i]]} for i in ref['excluded_roi_indices']],
        'nms_selected_roi_indices':ref['nms_roi_indices'],'final_rows':ref['rows'],
        'raw_and_valid_scores_and_boxes_bitwise_preserved':True,'scalar_nms_selected_identities_equal':True,
        'limits':['Exact exposed graph/tensor and CPU runtime only; not independent science or accuracy evidence.',
            'Scalar float32 operations follow retained ORT1.23.0 CPU source; not a universal compiled-kernel rounding proof.',
            'Finite genuine internal malformed boxes remain in NMS; only final score>.5 positive extent is an admission obligation.',
            'Final appended row is metadata. No geometry-only filtering, model training or threshold change.']}

def unique(pairs):
    result={}
    for key,value in pairs:
        need(key not in result,'duplicate JSON key');result[key]=value
    return result

def parse_json(raw):
    need(len(raw)<=1048576,'JSON byte cap')
    return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(Refusal('nonfinite JSON')))

class Reader:
    def __init__(self):self.inputs={};self.total=0
    def read(self,path,cap):
        path=Path(path).absolute();need(path.is_file() and not path.is_symlink(),'regular input file')
        need(path.stat().st_size<=cap,'file byte cap');raw=path.read_bytes();need(len(raw)<=cap,'file grew over cap')
        sha=hashlib.sha256(raw).hexdigest()
        if str(path) in self.inputs:need(self.inputs[str(path)]==sha,'input changed')
        self.inputs[str(path)]=sha;return raw
    def json(self,path):return parse_json(self.read(path,1048576))
    def array(self,root,desc):
        name=desc['file'];need(isinstance(name,str) and name and not Path(name).is_absolute(),'relative array path')
        need(all(p not in ('.','..') for p in Path(name).parts),'array traversal')
        path=Path(root).absolute()
        for part in Path(name).parts:path=path/part;need(not path.is_symlink(),'array symlink')
        raw=self.read(path,8388608);self.total+=len(raw);need(self.total<=67108864,'aggregate array cap')
        need(type(desc['bytes']) is int and len(raw)==desc['bytes'] and hashlib.sha256(raw).hexdigest()==desc['sha256'],'NPY byte identity')
        f=io.BytesIO(raw);version=np.lib.format.read_magic(f);need(version in ((1,0),(2,0)),'NPY version')
        fn=np.lib.format.read_array_header_1_0 if version==(1,0) else np.lib.format.read_array_header_2_0
        shape,fortran,dtype=fn(f,max_header_size=4096)
        need(dtype.str in ('<f4','<i8','|b1') and not fortran,'NPY dtype/order')
        need(1<=len(shape)<=4 and all(type(v) is int and 0<=v<=200000 for v in shape),'NPY dimensions')
        count=1
        for v in shape:count*=v
        need(count<=200000 and f.tell()+count*dtype.itemsize==len(raw),'NPY payload size')
        a=np.frombuffer(raw,dtype=dtype,count=count,offset=f.tell()).reshape(shape)
        if dtype.kind=='f':need(np.isfinite(a).all(),'nonfinite retained array')
        need(list(shape)==desc['shape'] and dtype.str==desc['dtype'],'NPY declared shape/dtype')
        need(hashlib.sha256(a.tobytes(order='C')).hexdigest()==desc['c_order_data_sha256'],'NPY data identity')
        return a
    def stages(self,path,result,allowed):
        need(isinstance(result.get('arrays'),list) and len(result['arrays'])<=100,'array roster cap')
        out={stage:{} for stage in allowed}
        for desc in result['arrays']:
            stage,name=desc['stage'],desc['name']
            need(stage in out and isinstance(name,str) and name not in out[stage],'array stage/name uniqueness')
            out[stage][name]=self.array(Path(path).parent,desc)
        need(type(result['saved_array_bytes']) is int and result['saved_array_bytes']==sum(x['bytes'] for x in result['arrays']),'array byte accounting')
        return out
    def unchanged(self):
        for p,sha in self.inputs.items():need(hashlib.sha256(Path(p).read_bytes()).hexdigest()==sha,'input changed after comparison')
        return [{'path':p,'sha256':s} for p,s in sorted(self.inputs.items())]

BASELINE_SHA='c9fc9b16bcb6ed4a6f45313d9712fe9671b2943362e67add989a46c964cc2799'
CORRECTED_OBSERVATION_SHA='a26f494f548ed8410a809252b2acaae97e2efa189fcee963a5b8a09dd4c13b63'
TENSOR_NPY_SHA='2603be7a21c1205e0e96af7a0541590a13ef6d50763c42d3cb2f37ac0ef87f18'
TENSOR_DATA_SHA='675a5f2aba2565e568feeb93fddc20aaed89a43a9bbeea393bf6336b84ae49d1'

def complete(record):
    need(record.get('status')=='complete' and record.get('stage')=='complete','complete capture required')
    need(type(record.get('forward_passes_started')) is int and record['forward_passes_started']==2
         and type(record.get('forward_passes_completed')) is int and record['forward_passes_completed']==2,'exact two-pass complete capture')
    need(record.get('onnxruntime_version')=='1.23.0','qualified CPU runtime version')

def check_files(prior_path,result_path,process_path,graph_path,contract_path):
    reader=Reader();raw=reader.read(prior_path,1048576)
    need(hashlib.sha256(raw).hexdigest()==PRIOR_RESULT_SHA,'exact retained prior trace result')
    prior=parse_json(raw);complete(prior)
    graph_raw=reader.read(graph_path,1048576);need(hashlib.sha256(graph_raw).hexdigest()==GRAPH_SHA,'exact original graph description')
    graph=parse_json(graph_raw);need(graph['model_sha256']==ORIGINAL_MODEL_SHA,'original graph model binding')
    result_raw=reader.read(result_path,1048576);result=parse_json(result_raw);complete(result)
    need(result.get('artifact_id')=='reiyah.multiorg.validity-observation' and result.get('version')=='0.4.0','observation artifact identity')
    for key in ('baseline_providers','corrected_providers'):
        need(result.get(key)==['CPUExecutionProvider'],'qualified CPU provider: '+key)
    need(result.get('numpy_version')=='2.2.6','qualified NumPy version')
    process=reader.json(process_path)
    need(process.get('status')=='complete' and type(process.get('returncode')) is int and process['returncode']==0
        and process.get('termination_reason') is None,'complete supervisor process')
    need(process.get('result_sha256')==hashlib.sha256(result_raw).hexdigest(),'process result digest')
    need(process.get('runner_sha256')==result.get('runner_sha256') and process.get('manifest_sha256')==result.get('manifest_sha256'),'process runner/manifest binding')
    bindings=result['source_bindings']
    contract=reader.json(contract_path)
    need(set(contract)=={'artifact_id','version','bindings'} and contract['artifact_id']=='reiyah.multiorg.validity-reference-input-contract'
        and contract['version']=='0.4.0','prospective reference contract identity')
    bound=contract['bindings']
    need(set(bound)=={'manifest','worker','protocol','taps','build','support'},'prospective binding roster')
    for key,ref in bound.items():
        need(isinstance(ref,dict) and set(ref)=={'path','sha256'},'prospective binding schema')
        actual=reader.read(ref['path'],1048576)
        need(hashlib.sha256(actual).hexdigest()==ref['sha256'],'prospective bound bytes changed: '+key)
        claimed=result.get('runner_sha256') if key=='worker' else result.get('manifest_sha256') if key=='manifest' else bindings[key]['sha256']
        need(claimed==ref['sha256'],'observation differs from prospective binding: '+key)
    need(bindings['baseline']['sha256']==BASELINE_SHA,'instrumented baseline model')
    need(bindings['corrected']['sha256']==CORRECTED_OBSERVATION_SHA,'prospectively pinned corrected observation graph')
    need(bindings['tensor']['sha256']==TENSOR_NPY_SHA,'exact tensor NPY binding')
    p=bindings['protocol'];protocol_raw=reader.read(p['path'],1048576)
    need(hashlib.sha256(protocol_raw).hexdigest()==p['sha256'],'protocol byte binding')
    protocol=parse_json(protocol_raw)
    need(protocol.get('worker_contract')=='origin_validity_observation_v040','correction capture contract')
    need(protocol['tensor']=={'dtype':'<f4','shape':[1,3,800,800],'c_order_data_sha256':TENSOR_DATA_SHA},'exact tensor descriptor')
    old=reader.stages(prior_path,prior,('baseline','tapped'))
    new=reader.stages(result_path,result,('baseline','corrected'))
    need(set(new['baseline'])==set(old['tapped']),'complete baseline replay roster')
    for name in old['tapped']:same(new['baseline'][name],old['tapped'][name],'prior baseline replay differs: '+name)
    report=compare_taps(new['baseline'],new['corrected'])
    report.update(prior_all_taps_reproduced_bitwise=True,original_graph_sha256=GRAPH_SHA,
        source_model_sha256=ORIGINAL_MODEL_SHA,corrected_observation_sha256=CORRECTED_OBSERVATION_SHA,
        tensor_c_order_sha256=TENSOR_DATA_SHA,checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        input_bindings=reader.unchanged())
    return report

def main():
    p=argparse.ArgumentParser()
    for key in ('prior-result','result','process','graph','contract','output'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();need(not a.output.exists(),'output already exists')
    try:report=check_files(a.prior_result,a.result,a.process,a.graph,a.contract);exitcode=0
    except Exception as exc:
        report={'status':'refused','error':type(exc).__name__+': '+str(exc),
            'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'scope':'No source or observations changed; refusal retained; no inference or automatic retry.'};exitcode=2
    data=json.dumps(report,indent=2,sort_keys=True,allow_nan=False).encode()+b'\n';need(len(data)<=1048576,'report byte cap')
    with a.output.open('xb') as f:f.write(data)
    print(json.dumps({k:report[k] for k in ('status','error','roi_count','valid_roi_count','excluded_roi_indices','nms_selected_roi_indices') if k in report}))
    raise SystemExit(exitcode)

if __name__=='__main__':main()
