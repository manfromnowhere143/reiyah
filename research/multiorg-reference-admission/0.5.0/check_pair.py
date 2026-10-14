#!/usr/bin/env python3
"""Separate whole-image scalar checker; shared byte-bound origin admission only.
No producer imports, original-model counterfactual, or model inference."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import re
import time
import numpy as np

MAX_SECONDS = 300
MAX_TILES = 156
MAX_RAW_ROWS = 200000
MAX_ARRAY_FILE = 64 * 1024 * 1024
MAX_TOTAL_RAW = 128 * 1024 * 1024
HEX = re.compile(r'[0-9a-f]{64}\Z')


class Refusal(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Refusal(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_json(path, cap=4*1024*1024):
    path=Path(path)
    require(path.is_file() and not path.is_symlink(), 'JSON file type')
    require(path.stat().st_size<=cap, 'JSON byte cap')
    def pairs(items):
        result={}
        for key,value in items:
            require(key not in result, 'duplicate JSON property')
            result[key]=value
        return result
    return json.loads(path.read_bytes(),object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(Refusal('nonfinite JSON token')))


def scalar_tile(dets, labels, row, column, side, remaining):
    """Independent scalar reconstruction; input arrays remain unchanged."""
    require(isinstance(dets,np.ndarray) and dets.ndim==3 and dets.shape[0]==1 and dets.shape[2]==5, 'detection shape')
    require(np.issubdtype(dets.dtype,np.floating), 'real floating detections')
    require(isinstance(labels,np.ndarray) and labels.shape==dets.shape[:2] and np.issubdtype(labels.dtype,np.integer), 'label shape/dtype')
    count=dets.shape[1]
    require(count<=remaining, 'all-raw-row work cap')
    f=np.float32
    factor=f(512/side)
    result={'all_raw_rows':count,'high_rows':0,'low_rows':0,'storage_eligible_rows':0,'below_storage_floor_rows':0,
            'raw_above_half_converted_not_above_half_rows':0,
            'low_geometry_anomalies':{name:[] for name in ('raw_nonfinite','raw_nonpositive_extent','conversion_nonfinite','finite_conversion_nonpositive_extent')},
            'storage_eligible_low_geometry_anomalies':{name:[] for name in ('raw_nonfinite','raw_nonpositive_extent','conversion_nonfinite','finite_conversion_nonpositive_extent')},
            'projected':[]}
    for index in range(count):
        raw=dets[0,index]
        require(math.isfinite(float(raw[4])) and 0<=raw[4]<=1, 'unknown nonfinite or invalid score')
        require(all(math.isfinite(float(value)) for value in raw[:4]), 'nonfinite raw coordinate in any row')
        with np.errstate(over='ignore', invalid='ignore'):
            converted=[f(value) for value in raw]
        require(all(math.isfinite(float(value)) for value in converted[:4]), 'nonfinite float32 coordinate conversion in any row')
        score=converted[4]; high=bool(score>f(.5)); storage=bool(score>=f(.05))
        if storage:require(labels[0,index]==0, 'invalid required foreground label')
        result['high_rows']+=int(high);result['low_rows']+=int(not high)
        result['storage_eligible_rows']+=int(storage);result['below_storage_floor_rows']+=int(not storage)
        result['raw_above_half_converted_not_above_half_rows']+=int(raw[4]>.5 and not high)
        raw_positive=bool(raw[2]>raw[0] and raw[3]>raw[1])
        converted_positive=bool(converted[2]>converted[0] and converted[3]>converted[1])
        if not high:
            anomaly='raw_nonpositive_extent' if not raw_positive else ('finite_conversion_nonpositive_extent' if not converted_positive else None)
            if anomaly:
                result['low_geometry_anomalies'][anomaly].append(index)
                if storage:result['storage_eligible_low_geometry_anomalies'][anomaly].append(index)
            continue
        require(raw_positive and converted_positive, 'undefined high-score geometry')
        box=[]
        for axis,value in enumerate(converted[:4]):
            scaled=f(value*factor)
            shifted=f(scaled+f(column if axis in (0,2) else row))
            divided=f(shifted/f(.5))
            box.append(f(np.floor(divided)))
        require(box[2]>box[0] and box[3]>box[1], 'floor produced degenerate retained box')
        result['projected'].append({'row':index,'box':box,'score':score})
    return result


def scalar_iou(a,b):
    f=np.float32
    width=max(f(0),f(min(a[2],b[2])-max(a[0],b[0])))
    height=max(f(0),f(min(a[3],b[3])-max(a[1],b[1])))
    intersection=f(width*height)
    aa=f(f(a[2]-a[0])*f(a[3]-a[1]));bb=f(f(b[2]-b[0])*f(b[3]-b[1]))
    return f(intersection/f(f(aa+bb)-intersection))


def scalar_nms(rows, deadline):
    f=np.float32
    for row in rows:
        b=row['box'];score=row['score']
        require(all(math.isfinite(float(v)) and abs(v)<=1e9 for v in b) and math.isfinite(float(score)), 'invalid NMS arrays')
        area=f(f(b[2]-b[0])*f(b[3]-b[1]))
        require(area>0, 'invalid NMS area')
    ordered=sorted(range(len(rows)),key=lambda index:(-float(rows[index]['score']),index))
    kept=[]; comparisons=0
    for index in ordered:
        require(time.monotonic()<deadline, 'checker wall cap')
        suppressed=False
        for previous in kept:
            comparisons+=1
            if comparisons%1024==0:require(time.monotonic()<deadline, 'checker wall cap')
            if scalar_iou(rows[index]['box'],rows[previous]['box'])>f(.5):
                suppressed=True;break
        if not suppressed:kept.append(index)
    return [rows[index] for index in kept]

ORIGINAL_SHA = '9a708bf6a22e9350980e0d08d0e90c2c56f7b9cc4a73b7fd55f22c9ef3f33e0c'
PROJECTION_SHA = '7cf0103cd7876585004310f6a3457add033bab2bc91b8b5ca750b15982a47425'
SCOPE = 'all_declared_tiles_analysis_score_float32_strictly_gt_0.5_only'
STORAGE = 'not_defined_or_exported_by_this_contract'
IMAGE_ID = 'MultiOrg_v2/test/Macros/Plate_4/image_7/image_7.tiff'
SOURCE = {'image':('8828e0a9f94d6c44ea03be2e62623e812830f339d9c905b7a368edcb7e821eb0',42627969),
          'faster':('a26f494f548ed8410a809252b2acaae97e2efa189fcee963a5b8a09dd4c13b63',165474438),
          'yolo':('02ed40f0cbdcf9023390e9723a1c310d5dd3f4d18a3ad1c3774f71ff74969ee6',246090044)}
MAX_ARRAY_FILE = 64*1024*1024
MAX_TOTAL_RAW = 128*1024*1024
FIXED_CONFIG = {'window_original':1024,'downsample':2,'overlap':0.5,'nms_iou':0.5,
                'storage_score_gte':0.05,'analysis_score_gt':0.5,'diameter_filter':None,
                'boundary_policy':'preserve_decoded_coordinates_and_report',
                'nms_tie_policy':'descending_float32_score_then_tile_row_order_and_output_row',
                'provider':'CPUExecutionProvider','intra_threads':2,'inter_threads':1}


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def hash_file(path,deadline,cap=None):
    path=Path(path)
    require(path.is_file() and not path.is_symlink(),'bound file type')
    if cap is not None:require(path.stat().st_size<=cap,'bound file size cap')
    h=hashlib.sha256()
    with path.open('rb') as stream:
        while True:
            require(time.monotonic()<deadline,'checker wall cap')
            data=stream.read(1024*1024)
            if not data:break
            h.update(data)
    return h.hexdigest()


def relative_file(root,name):
    require(isinstance(name,str) and name and not Path(name).is_absolute() and '..' not in Path(name).parts,'relative file path')
    path=root/name
    require(path.resolve().is_relative_to(root.resolve()),'file confinement')
    require(not path.is_symlink(),'file symlink')
    for parent in path.parents:
        if parent==root:break
        require(not parent.is_symlink(),'directory symlink')
    return path


def read_raw(root,record,expected_name,seen,deadline):
    require(isinstance(record,dict) and set(record)=={'name','file','sha256','bytes','dtype','shape','c_order_data_sha256'},'raw descriptor schema')
    require(record['file']==expected_name and expected_name not in seen,'raw filename/uniqueness')
    require(type(record['bytes']) is int and 0<record['bytes']<=MAX_ARRAY_FILE,'raw file bound')
    path=relative_file(root,expected_name)
    require(path.stat().st_size==record['bytes'],'raw file byte count')
    require(hash_file(path,deadline,MAX_ARRAY_FILE)==record['sha256'],'raw file digest')
    data=path.read_bytes()
    header_stream=io.BytesIO(data)
    version=np.lib.format.read_magic(header_stream)
    require(version in ((1,0),(2,0)), 'NPY format version')
    reader=np.lib.format.read_array_header_1_0 if version==(1,0) else np.lib.format.read_array_header_2_0
    shape,fortran,dtype=reader(header_stream,max_header_size=4096)
    require(not dtype.hasobject and math.prod(shape)*dtype.itemsize<=MAX_ARRAY_FILE, 'NPY header allocation cap')
    require(header_stream.tell()+math.prod(shape)*dtype.itemsize==len(data), 'NPY exact payload length')
    array=np.load(io.BytesIO(data),allow_pickle=False,max_header_size=4096)
    require(isinstance(array,np.ndarray) and not array.dtype.hasobject,'numeric NPY only')
    require(array.nbytes<=MAX_ARRAY_FILE,'array memory bound')
    require(array.dtype.str==record['dtype'] and canonical(list(array.shape))==canonical(record['shape']),'raw dtype/shape')
    require(digest(array.tobytes(order='C'))==record['c_order_data_sha256'],'raw C-order content digest')
    seen[expected_name]=record['bytes']
    require(sum(seen.values())<=MAX_TOTAL_RAW,'total raw array byte cap')
    return array


ADMISSION_SHA='7b665ff849c2ba5a383e414de7d62fede77273dbb9f19f08057756bddc04cb17'
CORE_SHA='428579d22cfa49588c76172999c90beab3cb57e13a04540aa5bdc6ac413f1d7c'
RECONSTRUCTION_SHA='113a0c18174367ee42db1130ab5d9ec9de92ec13fe10c32b2bafba0a00fcc3dc'
ROSTER_SHA='7de68d1d0f6ca67d143c3db3a40efa3d4d4d70f657d031371229262483a1ce35'
TAPS_SHA='c08932819200b816fa9c0dca38bf32e159325aa0a9e46cb7ada071c004acb8ba'
VARIANTS={'faster':'reiyah.multiorg.validity-preserving-export.observation/0.4.0','yolo':'MultiOrg-2026-released-YOLO-unchanged'}
LIMITS={'wall_seconds':600,'memory_bytes':3221225472,'max_tiles_per_image':156,'max_raw_boxes_per_image':200000,'max_array_file_bytes':67108864,'max_array_total_bytes':134217728}


def equal(actual,expected,message):
    require(canonical(actual)==canonical(expected),message)


def bound_module(name,filename,expected):
    import types
    path=Path(__file__).with_name(filename);raw=path.read_bytes()
    require(digest(raw)==expected,'checker dependency '+filename)
    mod=types.ModuleType(name);mod.__file__=str(path)
    exec(compile(raw,str(path),'exec'),mod.__dict__)
    return mod


def admission_module():
    require(digest(Path(__file__).with_name('reference_core.py').read_bytes())==CORE_SHA,'reference core digest')
    return bound_module('_admission','admit_tile.py',ADMISSION_SHA)


def inside(owner,path):
    path=Path(path)
    require(path.is_absolute() and '..' not in path.parts,'absolute bound source')
    require(path.resolve(strict=True).is_relative_to(owner),'source confinement')
    current=path
    while current!=owner:
        require(not current.is_symlink(),'source symlink');current=current.parent
    require(path.is_file(),'source regular file')
    return path


def bind_inputs(owner,runner_sha,manifest_sha,protocol_sha,deadline):
    for value in (runner_sha,manifest_sha,protocol_sha):require(bool(HEX.fullmatch(value)),'prospective digest')
    mp=inside(owner,owner/'execution/manifest.json');m=load_json(mp,1048576)
    require(hash_file(mp,deadline)==manifest_sha,'manifest prospective digest')
    require(set(m)=={'protocol','images','models','limits'},'manifest schema')
    equal(m['limits'],LIMITS,'resource contract')
    equal([x['id'] for x in m['images']],[IMAGE_ID],'first image identity')
    pins={'protocol':protocol_sha,'image':SOURCE['image'][0],**{k:v[0] for k,v in SOURCE.items() if k!='image'},
          'original':ORIGINAL_SHA,'projection':PROJECTION_SHA,'taps':TAPS_SHA,
          'origin_reference':ADMISSION_SHA,'reference_core':CORE_SHA,'input_roster':ROSTER_SHA}
    refs={'protocol':m['protocol'],'image':m['images'][0]['source'],**m['models']}
    equal(sorted(refs),sorted(pins),'exact source binding roster')
    paths={}
    for key,ref in refs.items():
        require(isinstance(ref,dict) and set(ref)=={'path','sha256'},'source descriptor')
        path=inside(owner,ref['path']);paths[key]=path
        require(ref['sha256']==pins[key] and hash_file(path,deadline,300000000)==pins[key],'source bytes '+key)
        if key in SOURCE:require(path.stat().st_size==SOURCE[key][1],'source length '+key)
    runner=inside(owner,owner/'implementation/complete_pair.py')
    require(hash_file(runner,deadline,1048576)==runner_sha,'runner exact bytes')
    protocol=load_json(paths['protocol']);r=load_json(paths['input_roster'])
    require(protocol['worker_contract']=='complete_first_image_analysis_pair_v050','protocol contract')
    equal(protocol['model_variants'],VARIANTS,'protocol variants');equal(protocol['config'],FIXED_CONFIG,'fixed configuration')
    equal(protocol['limits'],LIMITS,'protocol limits');equal(protocol['model_order'],['faster','yolo'],'model order')
    roster=[(i,j) for i in range(0,2860,256) for j in range(0,3192,256)]
    equal(protocol['tile_roster'],[list(x) for x in roster],'protocol full roster')
    recon=bound_module('_reconstruction','reconstruct_inputs.py',RECONSTRUCTION_SHA)
    reconstruction=recon.check(paths['image'],paths['input_roster'],deadline)
    return {'manifest':m,'manifest_sha256':manifest_sha,'protocol_sha256':protocol_sha,'source_bindings':refs,
            'bindings':pins,'shape':[5720,6385],'resized':[2860,3192],'padded':[3328,3584],
            'roster':roster,'image_id':IMAGE_ID,'runner_sha256':runner_sha,'tensors':r['tensors'],
            'input_reconstruction':reconstruction,'admission':admission_module()}


def check_trace(trace,ledger,checked,origin):
    expected={**ledger,'status':'tile_analysis_projection_defined','origin_admission':origin,
        **{key:checked[key] for key in ('all_raw_rows','high_rows','low_rows','storage_eligible_rows','below_storage_floor_rows','raw_above_half_converted_not_above_half_rows')},
        'analysis_original_row_indices':[x['row'] for x in checked['projected']],
        'low_geometry_anomaly_indices':checked['low_geometry_anomalies'],
        'storage_eligible_low_geometry_anomaly_indices':checked['storage_eligible_low_geometry_anomalies'],
        'low_transformed_geometry':'not_evaluated_not_claimed_valid'}
    equal(trace,expected,'complete tile admission receipt')


def verify_output(root,context,receipt,deadline):
    root=Path(root).resolve();require(root.is_dir(),'output directory exists')
    require(all((root/name).is_dir() and not (root/name).is_symlink() for name in ('raw','admissions')),'raw/admission directories cannot be symlinks')
    require(receipt.get('runner_sha256')==context['runner_sha256'],'process runner binding')
    equal(receipt.get('manifest_sha256'),context['manifest_sha256'],'process manifest binding')
    equal(receipt.get('network_boundary'),'worker_only_host_observer_outside_sandbox','process network boundary')
    equal(receipt.get('policy_sha256'),'5c358b8d847211333e7ba22df82d84f796b5f30a41a2682209a949d783adbd08','process policy bytes')
    require(type(receipt.get('wall_seconds')) in (int,float) and math.isfinite(receipt['wall_seconds']) and receipt['wall_seconds']>=0,'finite supervisor wall time')
    complete=(root/'result.json').exists()
    require(not (complete and (root/'failure.json').exists()),'contradictory result/failure')
    if complete:
        require(receipt.get('status')=='complete' and type(receipt.get('returncode')) is int and receipt['returncode']==0 and receipt.get('termination_reason') is None,'successful supervisor')
    else:require(receipt.get('status')=='failed','partial process remains failed')
    record_path=root/('result.json' if complete else 'failure.json')
    require(record_path.exists(),'structured worker result/failure required; abrupt absence is unqualified')
    result=load_json(record_path,64*1024*1024)
    record_hash=hash_file(record_path,deadline,64*1024*1024)
    if complete:
        equal(receipt.get('result_sha256'),record_hash,'supervisor exact result binding')
        peak=receipt.get('peak_sampled_rss_bytes');require(type(peak) is int and 0<=peak<=LIMITS['memory_bytes'],'sampled RSS boundary')
        wall=result.get('wall_seconds');require(type(wall) in (int,float) and math.isfinite(wall) and 0<=wall<=LIMITS['wall_seconds'],'worker wall boundary')
    require(result.get('artifact_id')=='reiyah.multiorg.complete-analysis-pair' and result.get('version')=='0.5.0','run identity')
    require(result.get('status')==('complete' if complete else 'failed'),'run status')
    require(result.get('completion_scope')==SCOPE and result.get('storage_output_status')==STORAGE,'endpoint scope')
    require('storage_predictions' not in result,'forbidden storage claim')
    for key,value in [('config',FIXED_CONFIG),('manifest',context['manifest']),('manifest_sha256',context['manifest_sha256']),
        ('source_bindings',context['source_bindings']),('runner_sha256',context['runner_sha256']),('protocol_sha256',context['protocol_sha256']),
        ('original_worker_sha256',ORIGINAL_SHA),('projection_sha256',PROJECTION_SHA),('model_variants',VARIANTS),
        ('expected_tiles_per_model',len(context['roster'])),('actual_tile_roster',[list(x) for x in context['roster']]),
        ('actual_image_shapes',{'original':context['shape'],'rescaled':context['resized'],'padded':context['padded']})]:
        equal(result.get(key),value,'run '+key)
    require(result.get('fallback_policy')=='constructor_enable_fallback_false_and_session_disable_fallback; no hidden retry','fallback policy')
    roster=context['roster'];shape=context['shape'];image=context['image_id'];helper=context['admission']
    seen={};models=[];all_ledgers=[];all_admissions=[];terminal=None;earlier_incomplete=False;observations=[];coverage={}
    for model in ('faster','yolo'):
        stem=digest(canonical([image,model]));side=800 if model=='faster' else 416
        files=[]
        for path in (root/'raw').glob(stem+'-*.json'):
            suffix=path.name[len(stem)+1:-5]
            require(suffix.isdecimal() and str(int(suffix))==suffix,'ledger ordinal filename')
            files.append((int(suffix),path))
        files.sort()
        equal([i for i,_ in files],list(range(len(files))),'contiguous raw prefix')
        require(len(files)<=len(roster) and not (earlier_incomplete and files),'raw coverage/order')
        total=0;observed=0;high=[];checked_tiles=[];admitted=0;unadmitted=False
        for ordinal,path in files:
            require(time.monotonic()<deadline,'checker wall cap')
            require(terminal is None and not unadmitted,'raw rows continued after refused/unadmitted tile')
            ledger=load_json(path,1048576);all_ledgers.append(str(path.relative_to(root)));row,col=roster[ordinal]
            checks={'image_id':image,'model':model,'model_variant':VARIANTS[model],'ordinal':ordinal,'rescaled_row':row,'rescaled_column':col,
                'image_shape_hw':shape,'rescaled_shape_hw':context['resized'],'tile_count_expected':len(roster),'resized_side':side,
                'image_source_sha256':context['bindings']['image'],'model_source_sha256':context['bindings'][model],
                'all_raw_rows_completed_before_tile':total,'status':'raw_outputs_retained_before_admission'}
            for key,value in checks.items():equal(ledger.get(key),value,'raw '+key)
            ti=(0 if model=='faster' else len(roster))+ordinal
            equal(ledger.get('tensor'),{**context['tensors'][ti]['tensor'],'observation_time':'before_session_run'},'reconstructed input tensor identity')
            descs=ledger.get('raw_outputs');names=list(helper.NAMES) if model=='faster' else ['dets','labels']
            require(isinstance(descs,list),'raw descriptors')
            equal([x.get('name') for x in descs],names,'exact named raw output order')
            arrays={name:read_raw(root,d,f'raw/{stem}-{ordinal}-{i}.npy',seen,deadline) for i,(name,d) in enumerate(zip(names,descs))}
            require(arrays['dets'].ndim==3,'raw detection rank')
            equal(ledger.get('observed_detection_rows'),int(arrays['dets'].shape[1]),'observed raw row count')
            observed+=int(arrays['dets'].shape[1]);ap=root/'admissions'/(stem+'-'+str(ordinal)+'.json')
            try:
                for name,array in arrays.items():
                    require(array.dtype.str==('|b1' if name==getattr(helper.c,'MASK','') else '<i8' if name=='labels' else array.dtype.str),'raw prescribed dtype')
                    if array.dtype.kind=='f':require(np.isfinite(array).all(),'all raw finite')
                require(arrays['dets'].dtype.str=='<f4' and arrays['labels'].dtype.str=='<i8','final raw dtypes')
                origin=helper.validate_tile(arrays) if model=='faster' else None
                checked=scalar_tile(arrays['dets'],arrays['labels'],row,col,side,MAX_RAW_ROWS-total)
            except (Refusal,helper.Refusal) as exc:
                terminal={'model':model,'tile_ordinal':ordinal,'independently_observed_violation':str(exc)}
                require(not complete and not ap.exists(),'invalid tile was claimed admitted/complete')
                continue
            if ap.exists():
                trace=load_json(ap,1048576);check_trace(trace,ledger,checked,origin)
                all_admissions.append(str(ap.relative_to(root)));admitted+=1
            else:
                require(not complete,'complete run missing admission receipt');unadmitted=True
            for item in checked['projected']:
                item.update(id=total+item['row'],tile_ordinal=ordinal,original_row_index=item['row']);high.append(item)
            total+=checked['all_raw_rows'];checked_tiles.append((ledger,checked,origin))
        image_path=root/(stem+'.json');image_complete=image_path.exists()
        coverage[model]={'captured':len(files),'admitted':admitted,'complete':image_complete}
        if image_complete:
            require(len(checked_tiles)==len(roster) and admitted==len(roster),'image incomplete tile population')
            img=load_json(image_path,64*1024*1024)
            require(img.get('artifact_id')=='reiyah.multiorg.complete-analysis-image' and img.get('version')=='0.5.0' and img.get('status')=='complete','image identity')
            for key,value in [('image_id',image),('model',model),('model_variant',VARIANTS[model]),('model_source_sha256',context['bindings'][model]),
                ('image_shape_hw',shape),('rescaled_shape_hw',context['resized']),('tile_count_expected',len(roster)),('tile_count_completed',len(roster)),
                ('raw_onnx_rows',total),('completion_scope',SCOPE),('storage_output_status',STORAGE),('protocol_sha256',context['protocol_sha256']),
                ('projection_sha256',PROJECTION_SHA),('original_worker_sha256',ORIGINAL_SHA),('providers',['CPUExecutionProvider']),
                ('onnx_output_names',list(helper.NAMES) if model=='faster' else ['dets','labels'])]:equal(img.get(key),value,'image '+key)
            require('storage_predictions' not in img,'no storage export')
            require(len(img.get('tiles',[]))==len(roster),'image full trace cardinality')
            for ordinal,(trace,parts) in enumerate(zip(img['tiles'],checked_tiles)):
                check_trace(trace,*parts)
                equal(trace,load_json(root/'admissions'/(stem+'-'+str(ordinal)+'.json'),1048576),'image trace matches persisted admission')
            kept=scalar_nms(high,deadline)
            expected=[{'id':x['id'],'tile_ordinal':x['tile_ordinal'],'original_row_index':x['original_row_index'],
                       'box_xyxy':[int(v) for v in x['box']],'score':float(x['score'])} for x in kept]
            equal(img.get('analysis_predictions'),expected,'independent whole-image predictions')
            outside=sum(x['box'][0]<0 or x['box'][1]<0 or x['box'][2]>shape[1] or x['box'][3]>shape[0] for x in kept)
            equal(img.get('empty_analysis'),not bool(kept),'empty analysis status');equal(img.get('analysis_outside_image'),int(outside),'outside count')
            observations.append({'file':image_path.name,'sha256':hash_file(image_path,deadline),'bytes':image_path.stat().st_size,
                'image_id':image,'model':model,'model_variant':VARIANTS[model],'analysis_count':len(kept),'raw_onnx_rows':total,'completion_scope':SCOPE})
            models.append({'model':model,'status':'complete_analysis_image_verified','raw_rows':total,'tiles':admitted,'analysis_count':len(kept)})
        else:
            require(not complete,'complete run missing image result');earlier_incomplete=True
            models.append({'model':model,'status':'partial_or_unobserved','raw_rows_in_qualified_tiles':total,'raw_rows_in_retained_tiles':observed,'retained_tiles':len(files),'qualified_tiles':len(checked_tiles),'persisted_admissions':admitted})
    equal(result.get('observations'),observations,'all complete model observations')
    equal(result.get('tile_coverage'),coverage,'captured/admitted/complete coverage')
    equal({str(p.relative_to(root)) for p in (root/'raw').glob('*.json')}==set(all_ledgers),True,'unrecognized raw ledger')
    require({str(p.relative_to(root)) for p in (root/'admissions').glob('*.json')}==set(all_admissions),'unrecognized admission')
    actual_raw={str(p.relative_to(root)) for p in (root/'raw').glob('*.npy')};orphans=sorted(actual_raw-set(seen))
    require(not complete or not orphans,'complete orphan arrays')
    for key,paths in [('last_raw_receipt',all_ledgers),('last_admission_receipt',all_admissions)]:
        expected=None
        if paths:
            path=root/paths[-1];expected={'file':paths[-1],'sha256':hash_file(path,deadline),'bytes':path.stat().st_size}
        equal(result.get(key),expected,'last receipt pointer')
    captured=sum(v['captured'] for v in coverage.values())
    completed=result.get('forward_passes_completed');started=result.get('forward_passes_started')
    require(type(completed) is int and type(started) is int and captured<=completed<=started<=2*len(roster) and started-completed<=1,'forward accounting')
    if complete:
        equal([started,completed,captured],[2*len(roster)]*3,'complete forward coverage')
        equal(result.get('stage'),'complete','completion stage')
        equal(result.get('raw_array_files_bytes'),sum(seen.values()),'complete array bytes')
        equal(result.get('raw_array_file_count'),len(seen),'complete array file count')
    return {'status':'complete_pair_verified' if complete else 'failed_attempt_partial_ledger_checked','complete_pairs':int(complete),
        'result_sha256':record_hash if complete else None,'failure_sha256':record_hash if not complete else None,'observations':observations,
        'models':models,'raw_array_files_checked':len(seen),'raw_array_file_bytes_checked':sum(seen.values()),
        'unbound_partial_array_files':orphans,'terminal_semantic_refusal':terminal,'scope':SCOPE,'storage_output_status':STORAGE,
        'limitations':['The checker performs no inference; no reference matching, model superiority or work advantage established.',
        'Origin admission reuses the byte-bound separately authored direct-removal checker; whole-image transforms/NMS are separate scalar code.',
        'Input tensor content is reconstructed using the same pinned numerical libraries; same-study checking, not independent scientific replication.',
        'Corrected Faster tiles have no original-model counterfactual; only their own observed origin and selection contract is checked.',
        'Missing observations never count as empty; unbound partial arrays are not qualified observations.']}


def main():
    p=argparse.ArgumentParser()
    for name in ('owner','output','runner-sha256','manifest-sha256','protocol-sha256','report'):p.add_argument('--'+name,required=True)
    a=p.parse_args();start=time.monotonic();deadline=start+MAX_SECONDS;owner=Path(a.owner).resolve(strict=True);root=Path(a.output).resolve()
    report=Path(a.report);require(root.is_relative_to(owner) and report.parent.resolve().is_relative_to(owner) and not report.exists(),'output/report confinement and new report')
    context=bind_inputs(owner,a.runner_sha256,a.manifest_sha256,a.protocol_sha256,deadline)
    pp=root.with_suffix('.process.json');receipt=load_json(pp,1048576)
    result=verify_output(root,context,receipt,deadline)
    result.update(checker_sha256=hash_file(__file__,deadline),manifest_sha256=context['manifest_sha256'],source_bindings=context['bindings'],
        process_receipt_sha256=hash_file(pp,deadline),input_reconstruction=context['input_reconstruction'],wall_seconds=time.monotonic()-start,check_budget_seconds=MAX_SECONDS)
    with report.open('x') as f:json.dump(result,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
    print(json.dumps({'status':result['status'],'complete_pairs':result['complete_pairs']}))

if __name__=='__main__':main()
