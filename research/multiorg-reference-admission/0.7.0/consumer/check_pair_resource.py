#!/usr/bin/env python3
"""Resource-custody wrapper around the unchanged selected-cohort numerical checker.

The wrapper reports its own identity separately; no original receipt is changed,
no model is executed, and self-consistent records do not authenticate execution.
"""
import argparse
import datetime
import hashlib
import itertools
from pathlib import Path
import sys
import time
import types
import resource_gate as g


def bound_module(path,sha,name):
    raw=Path(path).read_bytes();g.equal(hashlib.sha256(raw).hexdigest(),sha,'bound module digest')
    mod=types.ModuleType(name);mod.__file__=str(path);exec(compile(raw,str(path),'exec'),mod.__dict__);return mod


def verify_freeze(owner,path,sha,required,deadline):
    g.equal(g.hash_file(path,deadline,1048576),sha,'execution freeze digest');freeze=g.read_json(path)
    bindings=freeze.get('bindings');g.require(type(bindings) is dict and 0<len(bindings)<=512,'freeze binding roster')
    for filename,expected in required.items():
        name=str(Path(filename).relative_to(owner));g.require(name in bindings,'required frozen path '+name);g.equal(bindings[name].get('sha256'),expected,'required frozen digest '+name)
    for name,pin in bindings.items():
        g.require(type(name) is str and not Path(name).is_absolute() and '..' not in Path(name).parts,'freeze relative path')
        p=g.confined(owner,owner/name);g.require(type(pin) is dict and set(pin)=={'sha256','bytes'},'freeze pin schema')
        g.integer(pin['bytes'],0,512*1024**2,'frozen byte cap');g.equal(p.stat().st_size,pin['bytes'],'frozen byte length');g.equal(g.hash_file(p,deadline),pin['sha256'],'frozen bytes changed')
    return len(bindings)


def verify_runtime(before,after,deadline):
    g.require(type(before) is dict and type(after) is dict and set(before)==set(after),'runtime audit schema correspondence')
    g.equal({k:v for k,v in before.items() if k!='at'},{k:v for k,v in after.items() if k!='at'},'runtime before/after differs')
    before_time=audit_time(before['at']);after_time=audit_time(after['at']);g.require(after_time>before_time,'runtime after timestamp must follow before')
    for key,value in {'status':'passed','failures':[],'unrecorded_files':[]}.items():g.equal(before.get(key),value,'runtime '+key)
    venv=Path(before['venv']);g.require(venv.is_absolute() and venv.is_dir(),'retained runtime root')
    files=before['checked_files'];records=before['records'];excluded=before['excluded_record_entries']
    g.require(type(files) is list and 0<len(files)<=20000 and type(records) is list and 0<len(records)<=128 and type(excluded) is list and len(excluded)<=512,'runtime roster bounds')
    g.equal(before['hashed_entries_checked'],len(files),'runtime hashed count');g.equal(before['record_count'],len(records),'runtime record count')
    seen=set()
    for row in files+records:
        allowed={'path','sha256','bytes','record_match'} if 'record_match' in row else {'path','sha256'}
        g.require(type(row) is dict and set(row)==allowed,'runtime file schema')
        name=row['path'];g.require(type(name) is str and not Path(name).is_absolute() and '..' not in Path(name).parts and name not in seen,'runtime unique relative file')
        seen.add(name);p=g.confined(venv,venv/name)
        if 'record_match' in row:
            g.equal(row['record_match'],True,'runtime RECORD match');g.integer(row['bytes'],0,512*1024**2,'runtime file bytes');g.equal(p.stat().st_size,row['bytes'],'runtime file length')
        g.equal(g.hash_file(p,deadline),row['sha256'],'current runtime file changed')
    pins=before['runtime_pins'];g.require(type(pins) is dict and 1<=len(pins)<=8,'runtime executable/config pins')
    for name,pin in pins.items():
        p=Path(name);g.require(p.is_absolute() and type(pin) is dict and set(pin)=={'sha256','bytes'},'runtime absolute pin')
        g.equal(p.stat().st_size,pin['bytes'],'runtime pin size');g.equal(g.hash_file(p,deadline),pin['sha256'],'runtime pin digest')
    python=Path(before['python_entrypoint']);g.equal(str(python.resolve(strict=True)),before['python_resolved_identity'],'runtime Python resolved identity')
    g.require(str(python.resolve()) in pins,'resolved interpreter explicitly pinned')
    return {'status':'runtime_report_and_current_declared_bytes_checked','hashed_entries':len(files),'records':len(records),'excluded_unhashed_entries':len(excluded),
        'before_at':before['at'],'after_at':after['at'],'limitations':before['limitations']}


def audit_time(value):
    g.require(type(value) is str and len(value)<=64,'runtime timestamp string')
    parsed=datetime.datetime.fromisoformat(value);g.require(parsed.tzinfo is not None and parsed.utcoffset() is not None,'timezone-aware runtime timestamp')
    return parsed.timestamp()


def load_contract(owner,path,sha,deadline):
    path=g.confined(owner,path);g.equal(g.hash_file(path,deadline,1048576),sha,'consumer contract digest');obj=g.read_json(path)
    g.require(type(obj) is dict and set(obj)=={'artifact_id','version','sources','paths','python_entrypoint','outer_wall_limit_seconds'},'consumer contract schema')
    g.equal([obj['artifact_id'],obj['version']],['reiyah.multiorg.resource-consumer-contract','0.1.0'],'consumer contract identity')
    names={'supervisor','worker','numerical_checker','manifest','protocol','capacity_plan','runtime_before'}
    g.require(type(obj['sources']) is dict and set(obj['sources'])==names,'contract source roster')
    sources={};pins={}
    for key,ref in obj['sources'].items():
        g.require(type(ref) is dict and set(ref)=={'path','sha256'},'source schema');p=g.confined(owner,ref['path'])
        g.equal(g.hash_file(p,deadline),ref['sha256'],'source '+key);sources[key]=p;pins[str(p)]=ref['sha256']
    for key,sha in {'supervisor':g.SUPERVISOR,'worker':g.WORKER,'numerical_checker':g.NUMERICAL}.items():g.equal(obj['sources'][key]['sha256'],sha,'qualified source identity '+key)
    g.require(type(obj['paths']) is dict and set(obj['paths'])=={'output','outer','stdout','stderr','runtime_after','freeze'},'contract destination roster')
    paths={key:g.confined(owner,value) for key,value in obj['paths'].items()};g.require(len(set(paths.values()))==len(paths),'unique destination paths')
    g.require(not (set(paths.values()) & (set(sources.values())|{path})),'destination aliases frozen source or contract')
    g.number(obj['outer_wall_limit_seconds'],600,900,'bounded outer supervisor observation')
    g.require(type(obj['python_entrypoint']) is str and Path(obj['python_entrypoint']).is_absolute(),'Python entrypoint')
    pins[str(path)]=g.hash_file(path,deadline);pins[str(Path(__file__).resolve())]=g.hash_file(__file__,deadline)
    pins[str(Path(g.__file__).resolve())]=g.hash_file(g.__file__,deadline)
    return obj,sources,paths,pins


def execute(owner,contract_path,contract_sha,freeze_sha,deadline):
    obj,sources,paths,pins=load_contract(owner,contract_path,contract_sha,deadline)
    freeze_count=verify_freeze(owner,paths['freeze'],freeze_sha,pins,deadline)
    before=g.read_json(sources['runtime_before'],16*1024**2);after=g.read_json(paths['runtime_after'],16*1024**2)
    runtime=verify_runtime(before,after,deadline);g.equal(obj['python_entrypoint'],before['python_entrypoint'],'exact audited Python entrypoint')
    g.equal(str(Path(sys.executable).resolve()),before['python_resolved_identity'],'consumer interpreter must be audited interpreter')
    g.equal(str(Path(sys.prefix).resolve()),str(Path(before['venv']).resolve()),'consumer must run in audited virtual environment')
    root=paths['output'];g.require(root.is_dir() and not root.is_symlink(),'actual output directory');g.require(not root.with_suffix('.process.pending').exists(),'unfinished receipt publication')
    rp=root.with_suffix('.process.json');jp=root.with_suffix('.resources.jsonl');pp=root.with_suffix('.sandbox.sb');lp=root.with_suffix('.log')
    for p in (rp,jp,pp,lp):g.confined(owner,p)
    observation_paths={'outer':paths['outer'],'stdout':paths['stdout'],'stderr':paths['stderr'],'process_receipt':rp,'journal':jp,'policy':pp,'worker_log':lp,'runtime_after':paths['runtime_after'],'result':root/'result.json'}
    observed={key:{'path':str(path),'sha256':g.hash_file(path,deadline),'bytes':path.stat().st_size} for key,path in observation_paths.items()}
    g.equal(g.hash_file(pp,deadline,4096),g.POLICY,'materialized worker policy')
    receipt=g.read_json(rp,65536);returned=g.read_json(paths['stdout'],65536);outer=g.read_json(paths['outer'],1048576)
    g.equal(paths['stderr'].stat().st_size,0,'successful supervisor stderr must be empty')
    plan=g.read_json(sources['capacity_plan']);manifest=g.read_json(sources['manifest']);g.validate_plan(plan)
    g.require(lp.is_file() and lp.stat().st_size<=8388608,'bounded worker log');g.require(jp.stat().st_size<=8388608,'journal byte cap')
    raw=jp.read_bytes();rows=g.journal_rows(raw)
    g.require(audit_time(before['at'])<=rows[0]['unix_time_ns']/1e9 and audit_time(after['at'])>=rows[-1]['unix_time_ns']/1e9,'runtime report timestamps must enclose resource samples')
    command=[obj['python_entrypoint'],'-B',str(sources['supervisor']),'--owner',str(owner),'--manifest',str(sources['manifest']),
        '--runner',str(sources['worker']),'--runner-sha256',g.WORKER,'--python',obj['python_entrypoint'],'--output',str(root),
        '--capacity-plan',str(sources['capacity_plan']),'--capacity-plan-sha256',obj['sources']['capacity_plan']['sha256']]
    worker_command=['/usr/bin/sandbox-exec','-f',str(pp),obj['python_entrypoint'],'-B',str(sources['worker']),'--worker','--manifest',str(sources['manifest']),'--output',str(root)]
    expected={'outer_wall_limit_seconds':obj['outer_wall_limit_seconds'],'outer':{'command':command,'freeze_sha256':freeze_sha,'supervisor_sha256':g.SUPERVISOR,
        'manifest_sha256':obj['sources']['manifest']['sha256'],'stdout_sha256':g.hash_file(paths['stdout'],deadline,65536),'stderr_sha256':g.hash_file(paths['stderr'],deadline,65536),
        'worker_log_sha256':g.hash_file(lp,deadline,8388608),'worker_log_bytes':lp.stat().st_size},
        'receipt':{'manifest_sha256':obj['sources']['manifest']['sha256'],'capacity_plan_sha256':obj['sources']['capacity_plan']['sha256'],'capacity_plan':plan,
        'result_sha256':g.hash_file(root/'result.json',deadline,1048576),'resource_samples_sha256':hashlib.sha256(raw).hexdigest(),'sample_journal':jp.name,'log':lp.name,
        'command':worker_command,'limits':{k:manifest['limits'][k] for k in ('wall_seconds','memory_bytes')}}}
    gate=g.validate_success(receipt,returned,outer,rows,expected)
    numerical=bound_module(sources['numerical_checker'],g.NUMERICAL,'_unchanged_numerical_checker')
    context=numerical.bind_inputs(owner,sources['manifest'],g.WORKER,obj['sources']['manifest']['sha256'],obj['sources']['protocol']['sha256'],deadline)
    pair=numerical.verify_output(root,context,receipt,deadline);g.equal([pair['status'],pair['complete_pairs']],['complete_pair_verified',1],'complete numerical result required')
    g.equal(pair['result_sha256'],observed['result']['sha256'],'numeric result custody')
    verify_freeze(owner,paths['freeze'],freeze_sha,pins,deadline)
    for key,path in observation_paths.items():g.equal(g.hash_file(path,deadline),observed[key]['sha256'],'observation changed during checking '+key)
    current=final_inventory(root,[rp,jp,pp,lp],deadline)
    last_line_bytes=len(raw.splitlines(keepends=True)[-1]);last=rows[-1]['output']
    g.equal(current['logical_bytes'],last['logical_bytes']+last_line_bytes+rp.stat().st_size,'final logical inventory and receipt/journal growth')
    g.equal(current['file_count'],last['file_count']+1,'final file roster growth')
    g.require(current['logical_bytes']<=plan['output_budget_bytes'] and current['allocated_bytes']<=rows[-1]['prospective_allocation_budget_bytes'],'current retained output budget')
    result={'artifact_id':'reiyah.multiorg.resource-qualified-pair-check','version':'0.1.0','status':'complete_pair_verified','complete_pairs':1,
        'consumer_sha256':g.hash_file(__file__,deadline),'resource_gate_sha256':g.hash_file(g.__file__,deadline),'numerical_checker_sha256':g.NUMERICAL,
        'contract_sha256':contract_sha,'freeze_sha256':freeze_sha,'frozen_files_checked_before_and_after':freeze_count,'resource_admission':gate,'runtime':runtime,
        'image_id':context['image_id'],'image_contract_sha256':context['image_contract_sha256'],'manifest_sha256':context['manifest_sha256'],
        'source_bindings':context['bindings'],'input_reconstruction':context['input_reconstruction'],'numerical_result':pair,
        'observations':observed,'retained_output_inventory':current,
        'limitations':['The wrapper source is distinct from the unchanged numerical checker; downstream acceptance must qualify this composition.',
            'Hashes and consistent records do not authenticate a wholly fabricated execution history or establish independent scientific replication.',
            'No inference, reference matching, superiority, work advantage, filesystem reservation or continuous resource guarantee is produced by this consumer.']}
    return result


def final_inventory(root,artifacts,deadline):
    logical=allocated=count=0
    for path in itertools.chain(root.rglob('*'),artifacts):
        g.require(time.monotonic()<deadline,'consumer wall cap');g.require(not path.is_symlink(),'output symlink')
        if path.is_dir():continue
        g.require(path.is_file(),'output regular file');count+=1;g.require(count<=10000,'retained output file cap')
        info=path.stat();logical+=info.st_size;allocated+=info.st_blocks*512
    return {'file_count':count,'logical_bytes':logical,'allocated_bytes':allocated,'scope':'Logical bytes and summed st_blocks*512, not exclusive APFS occupancy.'}


def main():
    p=argparse.ArgumentParser()
    for key in ('owner','contract','contract-sha256','freeze-sha256','report'):p.add_argument('--'+key,required=True)
    a=p.parse_args();start=time.monotonic();owner=Path(a.owner).resolve(strict=True);report=g.confined(owner,a.report);g.require(not report.exists(),'new report only')
    result=execute(owner,Path(a.contract),a.contract_sha256,a.freeze_sha256,start+300);result.update(wall_seconds=time.monotonic()-start,check_budget_seconds=300)
    with report.open('xb') as f:f.write(g.canonical(result)+b'\n')
    print(g.canonical({'status':result['status'],'complete_pairs':1}).decode())


if __name__=='__main__':main()
