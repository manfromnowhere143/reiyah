#!/usr/bin/env python3
"""Separate observed-index lineage checker; no model or producer imports."""
import hashlib
import io
import json
import argparse
from pathlib import Path
import numpy as np

GRAPH_SHA = 'efdf18c9029db8dca26a70de8103920f18501fbf7ba94fe4ae74ea1b6a43ee77'
MODEL_SHA = 'fbf748e6d8b896bed9ee1eb15d5dd1409369de5e32c4746c4173aa4c10e7bebd'
RETAINED_SHA = '4a2f29206fbe37b9fa129d237cbab99191029fab52caf7c2e9d4fdde6eff693f'
TENSOR_SHA = '675a5f2aba2565e568feeb93fddc20aaed89a43a9bbeea393bf6336b84ae49d1'
TENSOR_NPY_SHA = '2603be7a21c1205e0e96af7a0541590a13ef6d50763c42d3cb2f37ac0ef87f18'
ALIASES = {
    'rpn_before': '/Where_6_output_0', 'rpn_pad': '/ConstantOfShape_11_output_0',
    'rpn_concat': '/Concat_87_output_0', 'rpn_scores': '/TopK_6_output_0',
    'rpn_order': '/TopK_6_output_1', 'proposals': '/Reshape_80_output_0',
    'rois': '/Reshape_83_output_0', 'probabilities': '/Softmax_output_0',
    'foreground': '/Slice_14_output_0', 'decoded': '/Reshape_93_output_0',
    'pre_scores': '/TopK_7_output_0', 'pre_order': '/TopK_7_output_1',
    'nms_boxes': '/Reshape_97_output_0', 'nms_scores': '/Transpose_12_output_0',
    'nms_indices': '/NonMaxSuppression_1_output_0',
    'nms_dets': '/Where_10_output_0', 'nms_labels': '/Where_11_output_0',
    'final_pad': '/ConstantOfShape_15_output_0', 'final_label_pad': '/ConstantOfShape_16_output_0',
    'final_concat': '/Concat_114_output_0', 'label_concat': '/Concat_116_output_0',
    'final_scores': '/TopK_8_output_0', 'final_order': '/TopK_8_output_1',
    'dets': 'dets', 'labels': 'labels',
}

class Refusal(ValueError): pass

def require(condition, why):
    if not condition: raise Refusal(why)

def same(actual, expected, why):
    require(actual.dtype == expected.dtype and actual.shape == expected.shape
            and actual.tobytes(order='C') == expected.tobytes(order='C'), why)

def shaped(array, pattern, name, kind='f'):
    require(isinstance(array, np.ndarray) and array.ndim == len(pattern), name+' rank')
    require(array.size <= 200000 and not array.dtype.hasobject, name+' element cap')
    require(array.dtype == np.dtype('float32' if kind == 'f' else 'int64'), name+' dtype')
    require(all(expected is None or actual == expected for actual, expected in zip(array.shape, pattern)),name+' shape')
    if kind == 'f': require(np.isfinite(array).all(), name+' finite')
    return array

def topk(scores, values, indices, cap, name):
    shaped(scores, (1,None), name+' source')
    shaped(values, (1,min(cap,scores.shape[1])), name+' values')
    shaped(indices, values.shape, name+' indices', 'i')
    ids=indices[0]
    require(np.all(ids>=0) and np.all(ids<scores.shape[1]) and len(set(map(int,ids)))==len(ids),name+' index domain/uniqueness')
    same(values, scores[:,ids], name+' selected scores')
    require(np.array_equal(values, np.sort(scores,axis=1)[:,::-1][:,:len(ids)]), name+' largest sorted values')
    return ids

def graph_contract(raw):
    require(hashlib.sha256(raw).hexdigest()==GRAPH_SHA,'exact graph description digest')
    graph=json.loads(raw)
    require(graph['model_sha256']==MODEL_SHA and graph['node_count']==1751,'graph model identity')
    nodes={node['name']:node for node in graph['nodes']}
    for name,left,right in [('/Concat_87','/Where_6_output_0','/ConstantOfShape_11_output_0'),
                            ('/Concat_114','/Where_10_output_0','/ConstantOfShape_15_output_0'),
                            ('/Concat_116','/Where_11_output_0','/ConstantOfShape_16_output_0')]:
        node=nodes[name]
        require(node['op']=='Concat' and node['inputs']==[left,right] and node['attributes']=={'axis':1},name+' append topology')
    for number in (6,7,8):
        require(nodes[f'/TopK_{number}']['attributes']=={'axis':1,'largest':1,'sorted':1},'TopK axis/order')
    require(nodes['/NonMaxSuppression_1']['inputs'][:2]==[ALIASES['nms_boxes'],ALIASES['nms_scores']],'observed NMS inputs')
    require(nodes['/Softmax']['attributes']=={'axis':2},'softmax row/class axis')
    return {'graph_sha256':GRAPH_SHA,'model_sha256':MODEL_SHA,'batch_scope':1,'foreground_classes':1}

def verify(taps):
    require(set(ALIASES.values())<=set(taps),'missing required graph tap')
    a={key:taps[name] for key,name in ALIASES.items()}
    before=shaped(a['rpn_before'],(1,None,5),'rpn_before'); n=before.shape[1]
    pad=shaped(a['rpn_pad'],(1,1,5),'rpn_pad')
    require(np.all(pad==0),'RPN constant padding values')
    shaped(a['rpn_concat'],(1,n+1,5),'rpn_concat')
    same(a['rpn_concat'],np.concatenate((before,pad),axis=1),'RPN append bytes')
    order6=topk(a['rpn_concat'][:,:,4],a['rpn_scores'],a['rpn_order'],1000,'TopK6')
    k=len(order6)
    shaped(a['proposals'],(1,k,5),'proposals')
    same(a['proposals'],a['rpn_concat'][:,order6,:],'RPN proposal gather')
    shaped(a['rois'],(k,5),'rois')
    expected_roi=np.concatenate((np.zeros((k,1),dtype=np.float32),a['proposals'][0,:,:4]),axis=1)
    same(a['rois'],expected_roi,'ROI batch/coordinate placement')
    shaped(a['probabilities'],(1,k,2),'probabilities')
    require(np.all((a['probabilities']>=0)&(a['probabilities']<=1)),'probability range')
    shaped(a['foreground'],(1,k,1),'foreground')
    same(a['foreground'],a['probabilities'][:,:,:1],'foreground score slice')
    shaped(a['decoded'],(1,k,4),'decoded per-ROI boxes')
    order7=topk(a['foreground'][:,:,0],a['pre_scores'],a['pre_order'],5000,'TopK7')
    j=len(order7)
    shaped(a['nms_boxes'],(1,j,4),'nms_boxes')
    same(a['nms_boxes'],a['decoded'][:,order7,:],'pre-NMS box gather')
    shaped(a['nms_scores'],(1,1,j),'nms_scores')
    same(a['nms_scores'],np.transpose(a['foreground'][:,order7,:],(0,2,1)),'pre-NMS score gather')
    indices=shaped(a['nms_indices'],(None,3),'nms_indices','i'); m=len(indices)
    require(m<=200 and all(int(b)==0 and int(c)==0 and 0<=int(i)<j for b,c,i in indices),'one-batch/one-class NMS index domain')
    require(len({tuple(map(int,row)) for row in indices})==m,'duplicate observed NMS tuple')
    wanted=np.asarray([[*a['nms_boxes'][0,int(i)],a['nms_scores'][0,0,int(i)]] for _,_,i in indices],dtype=np.float32).reshape(1,m,5)
    shaped(a['nms_dets'],(1,m,5),'nms_dets');same(a['nms_dets'],wanted,'observed NMS row gather')
    shaped(a['nms_labels'],(1,m),'nms_labels','i')
    same(a['nms_labels'],np.zeros((1,m),dtype=np.int64),'observed NMS labels')
    shaped(a['final_pad'],(1,1,5),'final_pad');require(np.all(a['final_pad']==0),'final padding values')
    shaped(a['final_label_pad'],(1,1),'final_label_pad','i');require(np.all(a['final_label_pad']==0),'final padding label')
    shaped(a['final_concat'],(1,m+1,5),'final_concat')
    same(a['final_concat'],np.concatenate((a['nms_dets'],a['final_pad']),axis=1),'final append bytes')
    shaped(a['label_concat'],(1,m+1),'label_concat','i')
    same(a['label_concat'],np.concatenate((a['nms_labels'],a['final_label_pad']),axis=1),'final label append bytes')
    order8=topk(a['final_concat'][:,:,4],a['final_scores'],a['final_order'],100,'TopK8')
    shaped(a['dets'],(1,len(order8),5),'dets');shaped(a['labels'],(1,len(order8)),'labels','i')
    same(a['dets'],a['final_concat'][:,order8,:],'final detection gather')
    same(a['labels'],a['label_concat'][:,order8],'final label gather')
    rows=[]
    for final_row, selected in enumerate(map(int,order8)):
        row={'final_row':final_row,'final_concat_row':selected,'box_xyxy':[float(v) for v in a['dets'][0,final_row,:4]],
             'score':float(a['dets'][0,final_row,4]),'label':int(a['labels'][0,final_row]),
             'zero_coordinates':bool(np.all(a['dets'][0,final_row,:4]==0))}
        if selected==m:
            row.update(origin='final_appended_padding',rpn_concat_row=None,roi_row=None,nms_selected_row=None)
        else:
            nms_row=int(indices[selected,2]);roi_row=int(order7[nms_row]);rpn_row=int(order6[roi_row])
            row.update(origin='rpn_appended_row_through_roi_head' if rpn_row==n else 'pre_append_rpn_candidate',
                       nms_selected_row=selected,pre_nms_row=nms_row,roi_row=roi_row,rpn_concat_row=rpn_row,
                       rpn_score=float(a['proposals'][0,roi_row,4]),foreground_score=float(a['foreground'][0,roi_row,0]))
        rows.append(row)
    return {'status':'observed_index_lineage_checked','all_final_rows':rows,
            'rpn_pre_append_rows':n,'rpn_appended_row_index':n,'rois':k,'pre_nms_rows':j,'observed_nms_selected_rows':m,
            'final_rows':len(rows),'counts':{name:sum(row['origin']==name for row in rows) for name in ('final_appended_padding','rpn_appended_row_through_roi_head','pre_append_rpn_candidate')},
            'limits':['Provenance uses exact graph indices and gather bytes, never geometry equality alone.',
                      'ROI neural features, classifier, box regression and ONNX NMS selection are observed taps, not independently reexecuted.',
                      'One exposed tile, one exact graph, batch1 and one foreground class only.',
                      'An appended origin does not itself authorize deleting a published detector output or altering a scoring contract.']}

def unique(pairs):
    value={}
    for key,item in pairs:
        require(key not in value,'duplicate JSON key')
        value[key]=item
    return value

def json_bytes(raw):
    require(len(raw)<=1048576,'JSON byte cap')
    return json.loads(raw,object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(Refusal('nonfinite JSON')))

class Reader:
    def __init__(self): self.inputs={};self.total_arrays=0
    def read(self,path,cap):
        path=Path(path).absolute()
        require(path.is_file() and not path.is_symlink(),'regular file required')
        require(path.stat().st_size<=cap,'file byte cap')
        raw=path.read_bytes();require(len(raw)<=cap,'file grew over byte cap')
        digest=hashlib.sha256(raw).hexdigest()
        if str(path) in self.inputs:require(self.inputs[str(path)]==digest,'input changed between reads')
        self.inputs[str(path)]=digest
        return raw
    def json(self,path):return json_bytes(self.read(path,1048576))
    def array(self,root,desc):
        name=desc['file'];require(isinstance(name,str) and name and not Path(name).is_absolute(),'relative array path')
        require(all(part not in ('..','.') for part in Path(name).parts),'array traversal')
        path=Path(root).absolute()
        for part in Path(name).parts:
            path=path/part;require(not path.is_symlink(),'array symlink')
        raw=self.read(path,8388608)
        self.total_arrays+=len(raw);require(self.total_arrays<=67108864,'aggregate array byte cap')
        require(type(desc['bytes']) is int and len(raw)==desc['bytes'] and hashlib.sha256(raw).hexdigest()==desc['sha256'],'NPY byte identity')
        stream=io.BytesIO(raw);version=np.lib.format.read_magic(stream)
        require(version in ((1,0),(2,0)),'NPY version')
        header_reader=np.lib.format.read_array_header_1_0 if version==(1,0) else np.lib.format.read_array_header_2_0
        shape,fortran,dtype=header_reader(stream,max_header_size=4096)
        require(dtype.str in ('<f4','<i8') and not fortran,'NPY dtype/order')
        require(1<=len(shape)<=4 and all(type(x) is int and 0<=x<=200000 for x in shape),'NPY dimension domain')
        count=1
        for x in shape:count*=x
        require(count<=200000 and stream.tell()+count*dtype.itemsize==len(raw),'NPY payload length/element cap')
        array=np.frombuffer(raw,dtype=dtype,count=count,offset=stream.tell()).reshape(shape)
        if dtype.kind=='f':require(np.isfinite(array).all(),'NPY nonfinite float')
        require(list(shape)==desc['shape'] and dtype.str==desc['dtype'],'NPY declared shape/dtype')
        require(hashlib.sha256(array.tobytes(order='C')).hexdigest()==desc['c_order_data_sha256'],'NPY data digest')
        return array
    def unchanged(self):
        for filename,digest in self.inputs.items():
            require(hashlib.sha256(Path(filename).read_bytes()).hexdigest()==digest,'input changed during check')
        return [{'path':p,'sha256':h} for p,h in sorted(self.inputs.items())]

def check_files(graph_path,result_path,process_path,retained_ledger,retained_root):
    reader=Reader();graph=graph_contract(reader.read(graph_path,1048576))
    result_raw=reader.read(result_path,1048576);result=json_bytes(result_raw)
    process=reader.json(process_path)
    require(process.get('status')=='complete' and type(process.get('returncode')) is int and process['returncode']==0
        and process.get('termination_reason') is None,'complete supervisor process')
    require(process.get('result_sha256')==hashlib.sha256(result_raw).hexdigest(),'process result binding')
    require(result.get('status')=='complete' and result.get('stage')=='complete'
        and type(result.get('forward_passes_completed')) is int and result['forward_passes_completed']==2
        and type(result.get('forward_passes_started')) is int and result['forward_passes_started']==2,'complete two-pass trace')
    require(result.get('runner_sha256')==process.get('runner_sha256') and result.get('manifest_sha256')==process.get('manifest_sha256'),'process runner/manifest agreement')
    require(result['source_bindings']['baseline']['sha256']==MODEL_SHA,'original model binding')
    require(result['source_bindings']['tensor']['sha256']==TENSOR_NPY_SHA,'reconstructed tensor NPY binding')
    refs={}
    for key in ('protocol','taps'):
        ref=result['source_bindings'][key];raw=reader.read(ref['path'],1048576)
        require(hashlib.sha256(raw).hexdigest()==ref['sha256'],'bound '+key+' source')
        refs[key]=json_bytes(raw)
    require(refs['protocol']['tensor']=={'dtype':'<f4','shape':[1,3,800,800],'c_order_data_sha256':TENSOR_SHA},'exact tensor protocol descriptor')
    roster=refs['taps'];require(isinstance(roster,list) and len(roster)<=64,'tap roster count')
    tapnames=[row['name'] for row in roster]
    require(len(set(tapnames))==len(tapnames) and not {'dets','labels'}&set(tapnames),'unique additional taps')
    retained_raw=reader.read(retained_ledger,1048576)
    require(hashlib.sha256(retained_raw).hexdigest()==RETAINED_SHA,'exact original tile9 ledger')
    retained=json_bytes(retained_raw)
    require(retained['model_source_sha256']==MODEL_SHA and retained['tensor']['c_order_data_sha256']==TENSOR_SHA,'retained model/tensor')
    require(len(retained['raw_outputs'])==2,'retained output roster')
    old={name:reader.array(retained_root,desc) for name,desc in zip(('dets','labels'),retained['raw_outputs'])}
    arrays=result['arrays'];require(isinstance(arrays,list) and len(arrays)<=68,'array descriptor count')
    bystage={'baseline':{},'tapped':{}}
    for desc in arrays:
        stage,name=desc['stage'],desc['name']
        require(stage in bystage and isinstance(name,str) and name not in bystage[stage],'stage/name uniqueness')
        bystage[stage][name]=reader.array(Path(result_path).parent,desc)
    require(set(bystage['baseline'])=={'dets','labels'},'baseline output roster')
    require(set(bystage['tapped'])==set(tapnames)|{'dets','labels'},'exact declared tapped output roster')
    for tap in roster:
        array=bystage['tapped'][tap['name']]
        require(type(tap['rank']) is int and array.ndim==tap['rank'] and tap['elem_type'] in (1,7),'declared tap rank/type')
        require(array.dtype.str==('<f4' if tap['elem_type']==1 else '<i8'),'declared tap dtype')
    require(type(result['saved_array_bytes']) is int and result['saved_array_bytes']==sum(d['bytes'] for d in arrays),'saved array byte accounting')
    for name in ('dets','labels'):
        require(name in bystage['tapped'],'missing final tapped output')
        same(old[name],bystage['baseline'][name],'baseline/prior '+name+' exact parity')
        same(old[name],bystage['tapped'][name],'tapped/prior '+name+' exact parity')
    report=verify(bystage['tapped'])
    report.update(graph=graph,prior_baseline_tapped_byte_parity=True,
        checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        input_bindings=reader.unchanged())
    return report

def main():
    parser=argparse.ArgumentParser()
    for key in ('graph','result','process','retained-ledger','retained-root','output'):
        parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args()
    report=check_files(args.graph,args.result,args.process,args.retained_ledger,args.retained_root)
    data=json.dumps(report,sort_keys=True,indent=2,allow_nan=False).encode()+b'\n'
    require(len(data)<=1048576,'report byte cap')
    with args.output.open('xb') as f:f.write(data)
    print(json.dumps({'status':report['status'],'final_rows':report['final_rows'],'counts':report['counts']}))

if __name__=='__main__':main()
