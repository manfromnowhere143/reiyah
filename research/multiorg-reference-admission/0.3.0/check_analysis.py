#!/usr/bin/env python3
"""Separately authored, bounded raw-output checker. No producer imports/inference."""
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
MAX_TILES = 512
MAX_RAW_ROWS = 200000
MAX_ARRAY_FILE = 16 * 1024 * 1024
MAX_TOTAL_RAW = 256 * 1024 * 1024
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
CONTRACT_SHA = 'edf53f094e41a219027054c9f70fea1f14bd4081010fd2fafaabca4b4e265e26'
BASE_SHA = 'd27a73f692ab15ec7402ff052c8a7aa0a0ef3539d89dda0ec1c38b8588ce6f08'
SCOPE = 'all_declared_tiles_analysis_score_float32_strictly_gt_0.5_only'
STORAGE = 'not_defined_or_exported_by_this_contract'
IMAGE_ID = 'MultiOrg_v2/test/Macros/Plate_4/image_7/image_7.tiff'
SOURCE = {'image':('8828e0a9f94d6c44ea03be2e62623e812830f339d9c905b7a368edcb7e821eb0',42627969),
          'faster':('fbf748e6d8b896bed9ee1eb15d5dd1409369de5e32c4746c4173aa4c10e7bebd',165472306),
          'yolo':('02ed40f0cbdcf9023390e9723a1c310d5dd3f4d18a3ad1c3774f71ff74969ee6',246090044)}
MAX_ARRAY_FILE = 64*1024*1024
MAX_TOTAL_RAW = 64*1024*1024
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
    return path


def bind_inputs(owner, runner_sha, deadline):
    require(bool(HEX.fullmatch(runner_sha)),'runner digest')
    manifest_path=owner/'inference/pilot-manifest.json'
    manifest=load_json(manifest_path,65536)
    require(set(manifest)=={'protocol','images','models','limits'},'manifest schema')
    require(manifest['limits']=={'wall_seconds':600,'memory_bytes':3221225472,'max_tiles_per_image':512,'max_raw_boxes_per_image':200000},'manifest limits')
    require(len(manifest['images'])==1 and manifest['images'][0]['id']==IMAGE_ID,'frozen single image')
    require(set(manifest['models'])=={'faster','yolo'},'frozen model pair')
    bindings={}
    for name,path,expected in [('runner',owner/'inference/analysis_pair.py',runner_sha),
                               ('original',owner/'inference/run_pair.py',ORIGINAL_SHA),
                               ('projection',owner/'inference/projection.py',PROJECTION_SHA),
                               ('contract',owner/'protocol/analysis-projection.json',CONTRACT_SHA)]:
        actual=hash_file(path,deadline,1024*1024);require(actual==expected,name+' source hash')
        bindings[name]=actual
    require(manifest['protocol']['sha256']==BASE_SHA,'scientific base identity')
    protocol_path=Path(manifest['protocol']['path'])
    require(protocol_path.resolve().is_relative_to(owner),'protocol confinement')
    require(hash_file(protocol_path,deadline,1024*1024)==BASE_SHA,'scientific base bytes')
    for name,record in [('image',manifest['images'][0]['source']),*manifest['models'].items()]:
        path=Path(record['path']);expected,size=SOURCE[name]
        require(path.resolve().is_relative_to(owner) and record['sha256']==expected,'source identity/confinement')
        require(path.stat().st_size==size and hash_file(path,deadline,size)==expected,'source bytes')
        bindings[name]=expected
    # Header only: no asarray(), pixel decoding or preprocessing.
    import tifffile
    with tifffile.TiffFile(manifest['images'][0]['source']['path']) as tf:
        require(len(tf.series)==1,'TIFF series count')
        shape=[int(x) for x in tf.series[0].shape if x!=1]
    require(len(shape)==2 and math.prod(shape)<=80000000,'TIFF squeezed header dimensions')
    resized=[round(x*.5) for x in shape]
    roster=[(r,c) for r in range(0,resized[0],256) for c in range(0,resized[1],256)]
    require(len(roster)==156 and len(roster)<=MAX_TILES,'frozen first image tile roster')
    return {'manifest':manifest,'manifest_sha256':hash_file(manifest_path,deadline,65536),
            'bindings':bindings,'shape':shape,'resized':resized,'roster':roster,
            'image_id':IMAGE_ID,'runner_sha256':runner_sha}


def read_raw(root,record,expected_name,seen,deadline):
    require(isinstance(record,dict) and set(record)=={'file','sha256','bytes','dtype','shape','c_order_data_sha256'},'raw descriptor schema')
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
    require(array.dtype.str==record['dtype'] and list(array.shape)==record['shape'],'raw dtype/shape')
    require(digest(array.tobytes(order='C'))==record['c_order_data_sha256'],'raw C-order content digest')
    seen[expected_name]=record['bytes']
    require(sum(seen.values())<=MAX_TOTAL_RAW,'total raw array byte cap')
    return array


def verify_output(root,context,receipt,deadline):
    root=Path(root).resolve()
    if not root.exists():
        require(receipt.get('status')=='failed' and receipt.get('runner_sha256')==context['runner_sha256'], 'absent output requires bound failed receipt')
        return {'status':'failed_before_output_creation','complete_pairs':0,'models':[],
                'raw_array_files_checked':0,'limitations':['No raw observations exist; missing is not empty.']}
    require(root.is_dir(),'output directory')
    roster=context['roster'];shape=context['shape'];resized=context['resized'];image=context['image_id']
    result_path=root/'result.json';complete=result_path.exists()
    require(receipt.get('runner_sha256')==context['runner_sha256'],'process runner binding')
    if complete:
        require(receipt.get('status')=='complete' and receipt.get('returncode')==0 and receipt.get('termination_reason') is None,'successful process receipt')
        result=load_json(result_path)
        require(result.get('artifact_id')=='reiyah.multiorg.analysis-projection.run' and result.get('status')=='complete','run result identity')
        require(result.get('completion_scope')==SCOPE and result.get('storage_output_status')==STORAGE,'run endpoint scope')
        require('storage_predictions' not in result,'forbidden storage claim')
        require(result.get('config')==FIXED_CONFIG,'run fixed configuration')
        require(result.get('manifest')==context['manifest'] and result.get('manifest_sha256')==context['manifest_sha256'],'run manifest binding')
        for key,expected in [('runner_sha256',context['runner_sha256']),('original_worker_sha256',ORIGINAL_SHA),('projection_sha256',PROJECTION_SHA),('supplemental_protocol_sha256',CONTRACT_SHA)]:
            require(result.get(key)==expected,'run '+key)
        require(len(result.get('observations',[]))==2,'complete model pair observation count')
    else:
        result=None
        require(receipt.get('status')=='failed','partial attempt must remain failed')
    seen={};models=[];all_ledgers=[];terminal_refusal=None;last_model_had_partial=False
    for model in ('faster','yolo'):
        stem=digest(canonical([image,model]));side=800 if model=='faster' else 416
        files=[]
        for path in (root/'raw').glob(stem+'-*.json') if (root/'raw').is_dir() else []:
            suffix=path.name[len(stem)+1:-5]
            require(suffix.isdecimal() and str(int(suffix))==suffix,'ledger ordinal filename')
            files.append((int(suffix),path))
        files.sort()
        require(len(files)<=len(roster) and [i for i,_ in files]==list(range(len(files))),'partial ledger must be a contiguous prefix')
        require(not (last_model_had_partial and files),'later model after incomplete earlier model')
        total=0;observed_total=0;all_high=[];checked_tiles=[];refusals=[]
        for ordinal,path in files:
            require(time.monotonic()<deadline,'checker wall cap')
            require(terminal_refusal is None,'raw ledger continued after scientific refusal')
            ledger=load_json(path,1024*1024);r,c=roster[ordinal]
            all_ledgers.append(str(path.relative_to(root)))
            checks={'image_id':image,'model':model,'ordinal':ordinal,'rescaled_row':r,'rescaled_column':c,
                    'image_shape_hw':shape,'rescaled_shape_hw':resized,'tile_count_expected':len(roster),
                    'resized_side':side,'image_source_sha256':context['bindings']['image'],
                    'model_source_sha256':context['bindings'][model],'all_raw_rows_completed_before_tile':total,
                    'status':'raw_outputs_retained_before_projection'}
            for key,value in checks.items():require(ledger.get(key)==value,'raw ledger '+key)
            tensor=ledger.get('tensor',{})
            require(tensor.get('dtype')==np.dtype(np.float32).str and tensor.get('shape')==[1,3,side,side] and tensor.get('observation_time')=='before_session_run' and isinstance(tensor.get('c_order_data_sha256'),str) and HEX.fullmatch(tensor['c_order_data_sha256']),'tensor identity metadata')
            descriptors=ledger.get('raw_outputs');require(isinstance(descriptors,list) and len(descriptors)==2,'two raw arrays')
            arrays=[read_raw(root,desc,f'raw/{stem}-{ordinal}-{i}.npy',seen,deadline) for i,desc in enumerate(descriptors)]
            require(arrays[0].ndim>=2 and ledger.get('observed_detection_rows')==arrays[0].shape[1],'observed raw row count')
            observed_total+=int(arrays[0].shape[1])
            try:
                checked=scalar_tile(*arrays,r,c,side,MAX_RAW_ROWS-total)
            except Refusal as exc:
                terminal_refusal={'model':model,'tile_ordinal':ordinal,'independently_observed_violation':str(exc)}
                refusals.append(terminal_refusal)
                require(not complete,'complete run contains raw semantic refusal')
                continue
            for item in checked['projected']:
                item.update({'id':total+item['row'],'tile_ordinal':ordinal,'original_row_index':item['row']})
                all_high.append(item)
            total+=checked['all_raw_rows']
            checked_tiles.append((ledger,checked))
        image_path=root/(stem+'.json')
        if image_path.exists():
            require(len(checked_tiles)==len(roster) and not refusals,'completed image has missing/invalid tiles')
            img=load_json(image_path,16*1024*1024)
            require(img.get('artifact_id')=='reiyah.multiorg.analysis-projection.image' and img.get('status')=='complete','image result identity')
            for key,value in [('image_id',image),('model',model),('image_shape_hw',shape),('rescaled_shape_hw',resized),('tile_count_expected',len(roster)),('tile_count_completed',len(roster)),('raw_onnx_rows',total),('completion_scope',SCOPE),('storage_output_status',STORAGE),('supplemental_protocol_sha256',CONTRACT_SHA),('projection_sha256',PROJECTION_SHA),('original_worker_sha256',ORIGINAL_SHA)]:
                require(img.get(key)==value,'image '+key)
            require('storage_predictions' not in img,'forbidden image storage export')
            require(len(img['tiles'])==len(roster),'image tile trace count')
            for trace,(ledger,checked) in zip(img['tiles'],checked_tiles):
                for key,value in ledger.items():
                    # Status belongs to the preprojection receipt, not completed trace.
                    if key!='status':require(trace.get(key)==value,'tile trace '+key)
                for key in ('all_raw_rows','high_rows','low_rows','storage_eligible_rows','below_storage_floor_rows','raw_above_half_converted_not_above_half_rows'):
                    require(trace.get(key)==checked[key],'tile count '+key)
                require(trace.get('analysis_original_row_indices')==[x['row'] for x in checked['projected']],'tile high membership')
                require(trace.get('low_geometry_anomaly_indices')==checked['low_geometry_anomalies'],'all-low anomaly indices')
                require(trace.get('storage_eligible_low_geometry_anomaly_indices')==checked['storage_eligible_low_geometry_anomalies'],'storage-low anomaly indices')
                require(trace.get('low_transformed_geometry')=='not_evaluated_not_claimed_valid','low geometry nonclaim')
            kept=scalar_nms(all_high,deadline)
            expected=[{'id':x['id'],'tile_ordinal':x['tile_ordinal'],'original_row_index':x['original_row_index'],'box_xyxy':[int(v) for v in x['box']],'score':float(x['score'])} for x in kept]
            require(img.get('analysis_predictions')==expected,'independent analysis predictions mismatch')
            outside=sum(any([x['box'][0]<0,x['box'][1]<0,x['box'][2]>shape[1],x['box'][3]>shape[0]]) for x in kept)
            require(img.get('empty_analysis')==(not bool(kept)) and img.get('analysis_outside_image')==outside,'analysis empty/outside status')
            if complete:
                matches=[x for x in result['observations'] if x.get('model')==model and x.get('image_id')==image]
                require(len(matches)==1,'observation identity')
                observation=matches[0]
                require(observation.get('file')==image_path.name and observation.get('sha256')==hash_file(image_path,deadline,16*1024*1024) and observation.get('bytes')==image_path.stat().st_size,'observation file binding')
                require(observation.get('analysis_count')==len(kept) and observation.get('raw_onnx_rows')==total and observation.get('completion_scope')==SCOPE,'observation counts/scope')
            models.append({'model':model,'status':'complete_analysis_image_verified','raw_rows':total,'tiles':len(checked_tiles),'analysis_count':len(kept)})
        else:
            require(not complete,'complete run missing model image result')
            last_model_had_partial=True
            models.append({'model':model,'status':'partial_or_unobserved','raw_rows_in_qualified_tiles':total,'raw_rows_in_retained_tiles':observed_total,'retained_tiles':len(files),'qualified_tiles':len(checked_tiles),'refusals':refusals})
    actual_raw={str(p.relative_to(root)) for p in (root/'raw').glob('*.npy')} if (root/'raw').is_dir() else set()
    actual_ledgers={str(p.relative_to(root)) for p in (root/'raw').glob('*.json')} if (root/'raw').is_dir() else set()
    require(actual_ledgers==set(all_ledgers),'unrecognized raw receipt')
    orphans=sorted(actual_raw-set(seen))
    require(not complete or not orphans,'complete run orphan raw arrays')
    if complete:require(result.get('raw_array_files_bytes')==sum(seen.values()),'total raw retention bytes')
    return {'status':'complete_pair_verified' if complete else 'failed_attempt_partial_ledger_checked',
            'complete_pairs':int(complete),'models':models,'raw_array_files_checked':len(seen),
            'raw_array_file_bytes_checked':sum(seen.values()),'unbound_partial_array_files':orphans,
            'terminal_semantic_refusal':terminal_refusal,'scope':SCOPE,'storage_output_status':STORAGE,
            'limitations':['No inference or pixel preprocessing was rerun.','TIFF header shape and full input-file hashes are checked; tensor hashes are metadata only, not independently reconstructed content.','Scalar coordinate/NMS verification shares numpy float32 runtime semantics, not producer/helper code.','No reference matching, model superiority, physical truth or complete-work claim.','Unbound partial arrays, if any, are not counted as qualified observations.']}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--owner',required=True);parser.add_argument('--output',required=True)
    parser.add_argument('--runner-sha256',required=True);parser.add_argument('--report',required=True)
    args=parser.parse_args();started=time.monotonic();deadline=started+MAX_SECONDS
    owner=Path(args.owner).resolve(strict=True);root=Path(args.output).resolve()
    report_path=Path(args.report)
    require(root.is_relative_to(owner),'output owner confinement')
    require(report_path.parent.resolve().is_relative_to(owner) and not report_path.exists(),'new private checker report')
    context=bind_inputs(owner,args.runner_sha256,deadline)
    receipt_path=root.with_suffix('.process.json');receipt=load_json(receipt_path,1024*1024)
    report=verify_output(root,context,receipt,deadline)
    report.update({'checker_sha256':hash_file(Path(__file__),deadline,1024*1024),
                   'manifest_sha256':context['manifest_sha256'],'source_bindings':context['bindings'],
                   'process_receipt_sha256':hash_file(receipt_path,deadline,1024*1024),
                   'wall_seconds':time.monotonic()-started,'check_budget_seconds':MAX_SECONDS})
    with report_path.open('x') as stream:json.dump(report,stream,sort_keys=True,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({'status':report['status'],'complete_pairs':report['complete_pairs'],'report':str(report_path)}))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
