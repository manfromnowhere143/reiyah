#!/usr/bin/env python3
"""Audit saved tiles after this study's disk-floor SIGKILL; never complete a pair.

Reuses the exact frozen0.6 custody, origin and scalar per-tile checks. It neither
imports a producer nor runs a model, whole-image NMS, or reference matching.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import time
import types

CHECKER_SHA='2cefacc5c6fef3e6c61ae944b16d4d23542ea7cbe03d47773604f808e124a431'
WORKER_SHA='7b2991f6b68719d815afc8137e563fc6d12e868689132850c9b9a483d957de1e'
POLICY_SHA='5c358b8d847211333e7ba22df82d84f796b5f30a41a2682209a949d783adbd08'
MAX_SECONDS=300


def frozen_checker(owner,support=None):
    path=(Path(support) if support else Path(owner)/'reference')/'check_pair.py';raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=CHECKER_SHA:raise ValueError('frozen checker digest')
    module=types.ModuleType('_frozen_saved_pair_checker');module.__file__=str(path)
    exec(compile(raw,str(path),'exec'),module.__dict__)
    return module


def check_process(c,process,context):
    c.require(process.get('status')=='failed' and type(process.get('returncode')) is int and process['returncode']==-9
              and process.get('termination_reason')=='disk_floor','specific abrupt disk-floor failure required')
    for key,value in [('runner_sha256',context['runner_sha256']),('manifest_sha256',context['manifest_sha256']),
       ('policy_sha256',POLICY_SHA),('network_boundary','worker_only_host_observer_outside_sandbox')]:c.equal(process.get(key),value,'process '+key)
    c.require('result_sha256' not in process,'failed process cannot assert a complete result digest')
    for key in ('wall_seconds','peak_sampled_rss_bytes'):
        value=process.get(key);c.require(type(value) in (float,int) and math.isfinite(value) and value>=0,'finite process resource observation')
    c.require(type(process['peak_sampled_rss_bytes']) is int and process['peak_sampled_rss_bytes']<=context['limits']['memory_bytes'],'sampled RSS within declared disk-floor case')


def inventory(c,root,deadline):
    c.require(root.is_dir() and not root.is_symlink(),'real output directory')
    records={};array_total=0;other_total=0
    for path in sorted(root.rglob('*')):
        c.require(not path.is_symlink(),'output symlink refused')
        if path.is_dir():
            c.require(path.parent==root and path.name in ('raw','admissions'),'unexpected nested output directory');continue
        c.require(len(records)<7000,'inventory file cap')
        name=str(path.relative_to(root));c.relative_file(root,name)
        cap=64*1024*1024 if path.suffix=='.npy' else 32*1024*1024
        digest=c.hash_file(path,deadline,cap);size=path.stat().st_size
        if path.suffix=='.npy':array_total+=size
        else:other_total+=size
        c.require(array_total<=128*1024*1024 and other_total<=64*1024*1024,'inventory aggregate byte cap')
        records[name]={'file':name,'bytes':size,'sha256':digest}
    return records


def frozen_bindings(c,owner,freeze_path,freeze_sha,manifest_path,context,deadline):
    owner=Path(owner).resolve(strict=True)
    c.equal(c.hash_file(freeze_path,deadline,1048576),freeze_sha,'prospective execution freeze digest')
    freeze=c.load_json(freeze_path,1048576)
    c.equal(freeze.get('artifact_id'),'reiyah.multiorg.selected-cohort.execution-freeze','freeze identity')
    c.equal(freeze.get('version'),'0.6.0','freeze version')
    c.equal(freeze.get('pair_worker_sha256'),WORKER_SHA,'freeze worker')
    c.equal(freeze.get('pair_checker_sha256'),CHECKER_SHA,'freeze checker')
    bindings=freeze.get('bindings');c.require(type(bindings) is dict and 0<len(bindings)<=128,'freeze binding roster')
    required={'implementation/complete_pair.py':WORKER_SHA,'reference/check_pair.py':CHECKER_SHA,
              str(Path(manifest_path).resolve().relative_to(owner)):context['manifest_sha256']}
    for name,sha in required.items():
        c.require(name in bindings,'required freeze binding');c.equal(bindings[name].get('sha256'),sha,'required freeze identity')
    for name,entry in bindings.items():
        c.require(type(entry) is dict and set(entry)=={'sha256','bytes'} and type(entry['bytes']) is int and 0<=entry['bytes']<=512*1024*1024,'freeze entry schema')
        path=c.relative_file(owner,name);c.equal(path.stat().st_size,entry['bytes'],'frozen byte length')
        c.equal(c.hash_file(path,deadline,512*1024*1024),entry['sha256'],'frozen file digest')
    return len(bindings)


def termination_inventory(c,owner,root,record,actual):
    c.equal(record.get('artifact_id'),'reiyah.multiorg.terminated-attempt.inventory','termination inventory identity')
    c.equal(record.get('version'),'0.6.0','termination inventory version')
    c.equal(record.get('status'),'inventory_only_not_output_admission','inventory is not admission')
    files={str((root/name).relative_to(owner)):{'sha256':row['sha256'],'bytes':row['bytes']} for name,row in actual.items()}
    c.equal(record.get('files'),files,'retained post-stop inventory exact files')
    for key,value in {'file_count':len(files),'total_bytes':sum(x['bytes'] for x in files.values()),
        'raw_numpy_files':sum(n.endswith('.npy') and '/raw/' in n for n in files),
        'raw_ledger_files':sum(n.endswith('.json') and '/raw/' in n for n in files),
        'worker_admission_files':sum(n.endswith('.json') and '/admissions/' in n for n in files),
        'worker_terminal_record_present':False}.items():c.equal(record.get(key),value,'termination inventory '+key)


def audit_saved(c,root,context,process,deadline):
    root=Path(root);check_process(c,process,context)
    c.require(not (root/'result.json').exists() and not (root/'failure.json').exists(),'terminal worker record exists; different audit required')
    before=inventory(c,root,deadline)
    c.require((root/'raw').is_dir() and (root/'admissions').is_dir(),'retained output directories')
    helper=context['admission'];roster=context['roster'];image=context['image_id']
    seen={};qualified_files=set();tiles=[];rejected=[];earlier_incomplete=False;model_rows=[]
    for model in ('faster','yolo'):
        stem=c.digest(c.canonical([image,model]));side=800 if model=='faster' else 416
        files=[]
        for path in (root/'raw').glob(stem+'-*.json'):
            suffix=path.name[len(stem)+1:-5];c.require(suffix.isdecimal() and str(int(suffix))==suffix,'canonical receipt ordinal')
            files.append((int(suffix),path))
        files.sort();c.equal([i for i,_ in files],list(range(len(files))),'contiguous saved raw receipt prefix')
        c.require(len(files)<=len(roster) and not (earlier_incomplete and files),'model order/coverage boundary')
        total=0;valid=0;admitted=0;ended=False
        for ordinal,path in files:
            c.require(time.monotonic()<deadline,'audit wall cap');c.require(not ended,'receipt continued after missing/refused admission')
            ap=root/'admissions'/(stem+'-'+str(ordinal)+'.json');stage='raw_receipt';checks={}
            try:
                ledger=c.load_json(path,1048576);row,col=roster[ordinal]
                checks={'image_id':image,'model':model,'model_variant':c.VARIANTS[model],'ordinal':ordinal,'rescaled_row':row,'rescaled_column':col,
                    'image_shape_hw':context['shape'],'rescaled_shape_hw':context['resized'],'tile_count_expected':len(roster),'resized_side':side,
                    'image_source_sha256':context['bindings']['image'],'model_source_sha256':context['bindings'][model],
                    'all_raw_rows_completed_before_tile':total,'status':'raw_outputs_retained_before_admission'}
                for key,value in checks.items():c.equal(ledger.get(key),value,'raw '+key)
                ti=(0 if model=='faster' else len(roster))+ordinal
                c.equal(ledger.get('tensor'),{**context['tensors'][ti]['tensor'],'observation_time':'before_session_run'},'independently reconstructed tensor identity')
                desc=ledger.get('raw_outputs');names=list(helper.NAMES) if model=='faster' else ['dets','labels']
                c.require(type(desc) is list,'raw descriptor list');c.equal([d.get('name') for d in desc],names,'exact named array roster')
                stage='raw_arrays';arrays={name:c.read_raw(root,d,f'raw/{stem}-{ordinal}-{i}.npy',seen,deadline) for i,(name,d) in enumerate(zip(names,desc))}
                c.require(arrays['dets'].ndim==3 and arrays['dets'].dtype.str=='<f4' and arrays['labels'].dtype.str=='<i8','raw detection dtype/rank')
                c.equal(ledger.get('observed_detection_rows'),int(arrays['dets'].shape[1]),'raw row count')
                stage='tile_semantics';origin=helper.validate_tile(arrays) if model=='faster' else None
                checked=c.scalar_tile(arrays['dets'],arrays['labels'],row,col,side,c.MAX_RAW_ROWS-total)
                total+=checked['all_raw_rows'];valid+=1
                qualified_files.add(str(path.relative_to(root)));qualified_files.update(d['file'] for d in desc)
                item={'model':model,'ordinal':ordinal,'raw_rows':checked['all_raw_rows'],'capture_status':'saved_capture_passed_per_tile_checks',
                      'producer_admission':'missing','origin_status':origin['status'] if origin is not None else 'not_applicable_to_unchanged_yolo'}
                tiles.append(item);stage='producer_admission'
                if ap.exists():
                    trace=c.load_json(ap,1048576);c.check_trace(trace,ledger,checked,origin)
                    qualified_files.add(str(ap.relative_to(root)));admitted+=1;item['producer_admission']='persisted_and_verified'
                else:ended=True
            except (ValueError,OSError,KeyError,TypeError) as exc:
                if time.monotonic()>=deadline:raise TimeoutError('audit wall cap') from exc
                rejected.append({'model':model,'ordinal':ordinal,'stage':stage,'file':str((ap if stage=='producer_admission' else path).relative_to(root)),
                                 'reason':type(exc).__name__+': '+str(exc),'qualified_as_complete_pair':False})
                if stage=='producer_admission' and tiles and tiles[-1]['model']==model and tiles[-1]['ordinal']==ordinal:tiles[-1]['producer_admission']='invalid_or_incomplete'
                ended=True
        earlier_incomplete=valid!=len(roster) or admitted!=len(roster)
        model_rows.append({'model':model,'saved_raw_receipt_files':len(files),'validated_capture_tiles':valid,'verified_persisted_admissions':admitted,
            'raw_rows_in_validated_capture_tiles':total,'expected_tiles':len(roster),'complete_model_endpoint':'not_evaluated_not_claimed'})
    after=inventory(c,root,deadline);c.equal(after,before,'partial output changed during audit')
    unqualified=[value for name,value in before.items() if name not in qualified_files]
    return {'artifact_id':'reiyah.multiorg.abrupt-termination.saved-tiles-audit','version':'0.1.0','status':'failed_attempt_saved_tiles_audited',
        'original_attempt_status':'failed','termination_reason':'disk_floor','terminal_worker_record':'absent_not_manufactured',
        'complete_pairs':0,'complete_model_endpoints':0,'full_image_nms_performed':False,'reference_matching_performed':False,'inference_performed':False,
        'image_id':image,'image_contract_sha256':context['image_contract_sha256'],'models':model_rows,'tiles':tiles,'rejected_receipts':rejected,
        'inventory':list(before.values()),'unqualified_or_inflight_files':unqualified,'output_bytes_unchanged_during_audit':True,
        'forward_accounting':{'returned_outputs_with_validated_tile_receipt_lower_bound':sum(v['validated_capture_tiles'] for v in model_rows),
           'total_forward_starts':None,'total_forward_completions':None,'inflight_forward_state':'unknown','unrecorded_work':'unknown_not_zero'},
        'scope':'Post-stop checking of retained records only. Shared frozen per-tile checker and reconstructed input identities. No terminal record, missing image, original-model counterfactual, full-image NMS, reference result or complete cohort is fabricated.'}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--support',help='Directory holding the exact qualified checker and sibling helpers; default OWNER/reference')
    for name in ('owner','manifest','manifest-sha256','protocol-sha256','output','report','process-sha256','freeze-sha256','inventory-sha256'):p.add_argument('--'+name,required=True)
    a=p.parse_args();start=time.monotonic();deadline=start+MAX_SECONDS;owner=Path(a.owner).resolve(strict=True);root=Path(a.output).resolve();report=Path(a.report)
    c=frozen_checker(owner,a.support);c.require(root.is_relative_to(owner) and report.parent.resolve().is_relative_to(owner) and not report.exists(),'private new audit destination')
    context=c.bind_inputs(owner,a.manifest,WORKER_SHA,a.manifest_sha256,a.protocol_sha256,deadline)
    freeze_path=owner/'EXECUTION_FREEZE.json';inventory_path=owner/'TERMINATED_INVENTORY.json'
    frozen_count=frozen_bindings(c,owner,freeze_path,a.freeze_sha256,a.manifest,context,deadline)
    c.equal(c.hash_file(inventory_path,deadline,4*1024*1024),a.inventory_sha256,'retained inventory digest')
    retained_inventory=c.load_json(inventory_path,4*1024*1024)
    termination_inventory(c,owner,root,retained_inventory,inventory(c,root,deadline))
    process_path=root.with_suffix('.process.json');policy_path=root.with_suffix('.sandbox.sb')
    c.require(c.hash_file(policy_path,deadline,4096)==POLICY_SHA,'materialized worker policy bytes')
    c.equal(c.hash_file(process_path,deadline,1048576),a.process_sha256,'exact failed supervisor receipt')
    process=c.load_json(process_path,1048576);result=audit_saved(c,root,context,process,deadline)
    termination_inventory(c,owner,root,retained_inventory,{r['file']:r for r in result['inventory']})
    c.equal(c.hash_file(process_path,deadline,1048576),a.process_sha256,'supervisor receipt unchanged')
    c.equal(c.hash_file(policy_path,deadline,4096),POLICY_SHA,'materialized worker policy unchanged')
    c.equal(c.hash_file(inventory_path,deadline,4*1024*1024),a.inventory_sha256,'retained inventory unchanged')
    frozen_bindings(c,owner,freeze_path,a.freeze_sha256,a.manifest,context,deadline)
    result.update(auditor_sha256=c.hash_file(__file__,deadline),shared_frozen_checker_sha256=CHECKER_SHA,runner_sha256=WORKER_SHA,
        manifest_sha256=context['manifest_sha256'],protocol_sha256=context['protocol_sha256'],source_bindings=context['bindings'],
        process_receipt_sha256=c.hash_file(process_path,deadline),materialized_policy_sha256=POLICY_SHA,input_reconstruction=context['input_reconstruction'],
        prospective_freeze_sha256=a.freeze_sha256,terminated_inventory_sha256=a.inventory_sha256,frozen_files_verified_before_and_after=frozen_count,
        wall_seconds=time.monotonic()-start,budget_seconds=MAX_SECONDS)
    with report.open('x') as f:json.dump(result,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
    print(json.dumps({'status':result['status'],'complete_pairs':0,'model_prefixes':result['models'],'unqualified_files':len(result['unqualified_or_inflight_files'])}))

if __name__=='__main__':main()
