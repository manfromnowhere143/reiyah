#!/usr/bin/env python3
"""Versioned host resource admission and sampled supervision for one owned worker.

Derived from Reiyah's retained 0.2.1 supervisor; no historical file is changed.
Only the worker enters the byte-bound network-denial policy. Samples do not
reserve APFS capacity or establish a continuous floor, hard RSS bound, child-
process containment, crash durability, scientific validity or build authority.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import stat
import subprocess
import sys
import time

VERSION='0.1.0'
POLICY=b'(version 1)\n(allow default)\n(deny network*)\n'
POLICY_SHA256='5c358b8d847211333e7ba22df82d84f796b5f30a41a2682209a949d783adbd08'
FLOOR=4*1024**3
MAX_JOURNAL=8*1024**2
MAX_LOG=8*1024**2
MAX_RECEIPT=65536
MAX_FILES=10000
MAX_WALK_SECONDS=1.0
CHILD_FSIZE=67108864


def require(condition,message):
    if not condition:raise ValueError(message)


def encode(obj):return (json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def digest(path,maximum=300000000):
    path=Path(path);require(path.is_file() and not path.is_symlink() and path.stat().st_size<=maximum,'bound regular file/byte cap')
    h=hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda:f.read(1048576),b''):h.update(part)
    return h.hexdigest()


def contained(owner,path,exists=True):
    path=Path(path).absolute();require(path.is_relative_to(owner),'path outside owner')
    for item in (path,*path.parents):
        if item==owner:break
        require(not item.is_symlink(),'symlink in owned path')
    require(path.resolve(strict=exists).is_relative_to(owner),'resolved path outside owner')
    if exists:require(path.is_file(),'regular bound file required')
    return path


def read_json(path):
    require(path.stat().st_size<=1048576,'JSON byte cap')
    def unique(pairs):
        obj={}
        for key,value in pairs:
            require(key not in obj,'duplicate JSON property');obj[key]=value
        return obj
    return json.loads(path.read_bytes(),object_pairs_hook=unique,
        parse_constant=lambda value:(_ for _ in ()).throw(ValueError('nonfinite JSON '+value)))


def positive_int(value,lower,upper,label):require(type(value) is int and lower<=value<=upper,label)


def capacity_plan(path,sha):
    require(digest(path,1048576)==sha,'capacity plan digest');p=read_json(path)
    require(type(p) is dict and set(p)=={'artifact_id','version','free_disk_floor_bytes','output_budget_bytes','margin_bytes','max_output_files',
        'preflight_samples','sample_period_seconds','max_sample_gap_seconds'},'capacity plan schema')
    require(p['artifact_id']=='reiyah.resource-admission.capacity-plan' and p['version']==VERSION,'capacity plan identity')
    positive_int(p['free_disk_floor_bytes'],FLOOR,1024**4,'floor must preserve at least 4 GiB')
    positive_int(p['output_budget_bytes'],MAX_RECEIPT,1024**3,'prospective output budget')
    positive_int(p['margin_bytes'],1,4*1024**3,'prospective margin')
    positive_int(p['max_output_files'],4,MAX_FILES,'prospective output file count')
    positive_int(p['preflight_samples'],2,20,'preflight sample count')
    for key in ('sample_period_seconds','max_sample_gap_seconds'):
        require(type(p[key]) in (int,float) and math.isfinite(p[key]),'finite numeric '+key)
    require(.1<=p['sample_period_seconds']<=1 and p['sample_period_seconds']<=p['max_sample_gap_seconds']<=5,'sample period/gap limits')
    return p


def bindings(owner,manifest,runner,runner_sha256):
    require(digest(runner,1048576)==runner_sha256,'worker digest mismatch')
    m=read_json(manifest);require(type(m) is dict and set(m)=={'protocol','images','models','limits'},'manifest envelope schema')
    require(type(m['images']) is list and 0<len(m['images'])<=4 and type(m['models']) is dict and len(m['models'])<=32,'source roster bounds')
    require(all(type(row) is dict and 'source' in row for row in m['images']),'image source schema')
    refs=[m['protocol'],*m['models'].values(),*(row['source'] for row in m['images'])]
    pins=[(runner,runner_sha256),(manifest,digest(manifest,1048576))]
    for row in refs:
        require(type(row) is dict and set(row)=={'path','sha256'},'source binding schema')
        path=contained(owner,row['path']);sha=row['sha256']
        require(type(sha) is str and len(sha)==64 and digest(path)==sha,'source digest mismatch');pins.append((path,sha))
    limits=m['limits'];require(type(limits) is dict,'limits schema')
    wall,memory=limits['wall_seconds'],limits['memory_bytes']
    require(type(wall) in (int,float) and math.isfinite(wall) and 0<wall<=600,'wall limit')
    positive_int(memory,1,3*1024**3,'memory limit at most 3 GiB')
    return m,pins


def disk_observation(path):
    v=os.statvfs(path)
    return {'available_bytes':v.f_bavail*v.f_frsize,'free_including_reserved_bytes':v.f_bfree*v.f_frsize,
            'total_bytes':v.f_blocks*v.f_frsize,'fragment_bytes':v.f_frsize,
            'measurement':'statvfs_f_bavail_times_f_frsize; no purgeable estimate'}


def rss_observation(pid):
    result=subprocess.run(['/bin/ps','-o','rss=','-p',str(pid)],capture_output=True,text=True,timeout=2)
    if result.returncode!=0 or not result.stdout.strip():raise RuntimeError('RSS observation unavailable')
    return int(result.stdout.strip())*1024


def output_observation(output,artifacts):
    start=time.monotonic();paths=[]
    if output.exists():
        require(output.is_dir() and not output.is_symlink(),'output directory changed type')
        stack=[output]
        while stack:
            require(time.monotonic()-start<=MAX_WALK_SECONDS,'output inventory duration limit')
            with os.scandir(stack.pop()) as entries:
                for entry in entries:
                    require(len(paths)<MAX_FILES,'output inventory file limit');p=Path(entry.path)
                    require(not entry.is_symlink(),'output symlink refused')
                    info=entry.stat(follow_symlinks=False)
                    if stat.S_ISDIR(info.st_mode):stack.append(p)
                    else:require(stat.S_ISREG(info.st_mode),'output special file refused');paths.append(p)
                    require(len(stack)<=MAX_FILES and time.monotonic()-start<=MAX_WALK_SECONDS,'output inventory bound')
    paths += [p for p in artifacts if p.exists()]
    logical=allocated=0
    for path in paths:
        info=path.lstat();require(stat.S_ISREG(info.st_mode),'artifact regular file required')
        logical+=info.st_size;allocated+=info.st_blocks*512
    return {'file_count':len(paths),'logical_bytes':logical,'allocated_bytes':allocated,
        'walk_seconds':time.monotonic()-start,'measurement':'sum st_size and st_blocks*512; shared/extents/metadata/APFS purgeable or exclusive deletion yield not measured'}


class Journal:
    def __init__(self,path):self.path=path;self.stream=path.open('xb');self.bytes=0;self.count=0
    def append(self,row):
        require(self.count<8192,'resource sample count cap')
        data=encode(row);require(len(data)<=8192 and self.bytes+len(data)<=MAX_JOURNAL,'resource journal byte cap')
        self.stream.write(data);self.stream.flush();os.fsync(self.stream.fileno())
        self.bytes+=len(data);self.count+=1
    def close(self):self.stream.close()


def supervise(owner,manifest,runner,runner_sha256,python,output,capacity,capacity_sha256,*,disk_provider=None,rss_provider=None):
    owner=Path(owner).resolve(strict=True);manifest=contained(owner,manifest);runner=contained(owner,runner);capacity=contained(owner,capacity)
    output=contained(owner,output,exists=False);require(output.parent.is_dir() and not output.exists(),'output must be new')
    paths={key:output.with_suffix(suffix) for key,suffix in {'receipt':'.process.json','pending':'.process.pending','log':'.log','policy':'.sandbox.sb','samples':'.resources.jsonl'}.items()}
    require(output not in paths.values() and len(set(paths.values()))==5 and all(not p.exists() and not p.is_symlink() for p in paths.values()),'new exclusive process artifacts required')
    plan=capacity_plan(capacity,capacity_sha256)
    disk=disk_provider or disk_observation;rss=rss_provider or rss_observation
    start=time.monotonic();process=None;journal=None;last_sample=None;last_phase=None;begin=None;worker_end=None;pins=[];trigger=None;sample_errors=[]
    record={'artifact_id':'reiyah.resource-admission.supervisor-receipt','version':VERSION,'status':'refused','returncode':None,
        'termination_reason':None,'worker_pid':None,'worker_launched':False,'peak_sampled_rss_bytes':None,
        'runner_sha256':runner_sha256,'manifest_sha256':digest(manifest,1048576),'capacity_plan_sha256':capacity_sha256,
        'supervisor_sha256':digest(Path(__file__),1048576),'policy_sha256':POLICY_SHA256,'capacity_plan':plan,
        'observation_provider_mode':'authored_injected' if disk_provider is not None or rss_provider is not None else 'system',
        'memory_boundary':'sampled_RSS_not_hard_address_space_or_process_tree_limit','network_boundary':'worker_only_host_observer_outside_sandbox',
        'capacity_boundary':'admission_observations_not_reservation_or_continuous_floor_guarantee',
        'output_budget_scope':'logical byte cap across worker output directory plus process log, policy, samples and receipt; two transient64KiB receipt links and next8KiB sample reserved in observed budget checks',
        'allocation_budget_scope':'logical cap plus max_output_files*(filesystem fragment_bytes-1) rounding allowance; metadata, shared extents and APFS-exclusive allocation remain unmeasured; margin is additional and no physical guarantee is made',
        'bindings_verified_before_launch':False,'bindings_unchanged_after_worker':None,
        'receipt_compatibility':'new schema; historical pair checkers not qualified for this supervisor',
        'receipt_publication':'exclusive pending write and file fsync before no-overwrite hard-link publication; no directory-fsync or crash-durability claim; pending file alone is not an accepted receipt',
        'sample_journal':paths['samples'].name,'log':paths['log'].name,'sample_errors':sample_errors,'sampling_gaps':[],
        'resource_caps':{'journal_bytes':MAX_JOURNAL,'log_bytes':MAX_LOG,'receipt_bytes':MAX_RECEIPT,'output_files':MAX_FILES,'walk_seconds':MAX_WALK_SECONDS,'child_fsize_bytes':CHILD_FSIZE}}
    record['admission_required_available_bytes']=None

    def sample(phase):
        nonlocal last_sample,last_phase
        now=time.monotonic();seq=journal.count;row={'sequence':seq,'phase':phase,'unix_time_ns':time.time_ns(),'elapsed_seconds':now-start,
            'worker_elapsed_seconds':None if begin is None else (worker_end if worker_end is not None else now)-begin,'worker_pid':None if process is None else process.pid,
            'disk':None,'output':None,'rss_bytes':None,'rss_state':'not_launched' if process is None else 'not_observed','errors':[]}
        gap=None if last_sample is None else now-last_sample;row['gap_seconds']=gap
        # Binding preflight is also observed; a long blind interval refuses launch.
        if gap is not None and gap>plan['max_sample_gap_seconds']:
            row['errors'].append('sampling_gap');record['sampling_gaps'].append({'sequence':seq,'seconds':gap,'previous_phase':last_phase,'phase':phase})
        try:
            d=disk(output.parent);require(type(d) is dict and set(d)=={'available_bytes','free_including_reserved_bytes','total_bytes','fragment_bytes','measurement'},'disk observation schema')
            for key in ('available_bytes','free_including_reserved_bytes','total_bytes','fragment_bytes'):positive_int(d[key],1 if key=='fragment_bytes' else 0,2**63-1,'disk integer '+key)
            require(d['available_bytes']<=d['free_including_reserved_bytes']<=d['total_bytes'],'disk capacity order')
            require(type(d['measurement']) is str and len(d['measurement'])<=256,'disk measurement label');row['disk']=d
        except Exception as exc:row['errors'].append('disk: '+type(exc).__name__+': '+str(exc))
        try:row['output']=output_observation(output,list(paths.values()))
        except Exception as exc:row['errors'].append('output: '+type(exc).__name__+': '+str(exc))
        if process is not None:
            if process.poll() is None:
                try:
                    value=rss(process.pid);positive_int(value,0,2**63-1,'RSS integer');row['rss_bytes']=value;row['rss_state']='observed'
                    record['peak_sampled_rss_bytes']=max(record['peak_sampled_rss_bytes'] or 0,value)
                except Exception as exc:
                    if process.poll() is None:row['errors'].append('rss: '+type(exc).__name__+': '+str(exc));row['rss_state']='error_live_worker'
                    else:row['rss_state']='worker_exited_during_observation'
            else:row['rss_state']='worker_exited_before_observation'
        row['duration_seconds']=time.monotonic()-now
        if row['disk'] is not None:
            slack=plan['max_output_files']*(row['disk']['fragment_bytes']-1)
            budget=plan['output_budget_bytes']+slack
            record['admission_required_available_bytes']=plan['free_disk_floor_bytes']+budget+plan['margin_bytes']
            row['prospective_allocation_budget_bytes']=budget;row['allocation_rounding_allowance_bytes']=slack
            if row['output'] is not None:
                used=max(row['output']['logical_bytes'],row['output']['allocated_bytes'])
                row['remaining_allocation_budget_bytes']=max(0,budget-used)
                row['required_available_bytes']=plan['free_disk_floor_bytes']+plan['margin_bytes']+(budget if phase in ('preflight','before_launch') else max(0,budget-used))
        if row['duration_seconds']>plan['max_sample_gap_seconds']:row['errors'].append('sample_duration')
        if row['errors']:sample_errors.append({'sequence':seq,'errors':row['errors']})
        journal.append(row);last_sample=now;last_phase=phase
        return row

    def cause(row,admission=False):
        if row['errors']:return 'resource_observation_failed'
        if row['disk']['available_bytes']<plan['free_disk_floor_bytes']:return 'capacity_admission' if admission else 'disk_floor'
        required=record['admission_required_available_bytes'] if admission else row['required_available_bytes']
        if row['disk']['available_bytes']<required:return 'capacity_admission' if admission else 'remaining_capacity'
        if row['output']['logical_bytes']+2*MAX_RECEIPT+8192>plan['output_budget_bytes'] or row['output']['allocated_bytes']+2*MAX_RECEIPT+8192>row['prospective_allocation_budget_bytes']:return 'output_budget'
        if row['output']['file_count']+2>plan['max_output_files']:return 'output_file_budget'
        if paths['log'].exists() and paths['log'].stat().st_size>MAX_LOG:return 'log_budget'
        if row['worker_elapsed_seconds'] is not None and row['worker_elapsed_seconds']>wall:return 'wall_limit'
        if row['rss_bytes'] is not None and row['rss_bytes']>memory:return 'memory_limit'
        return None

    def stop(reason,row):
        nonlocal trigger
        if record['termination_reason'] is None:
            record['termination_reason']=reason;trigger=row;record['trigger_sample']=row
        if process is not None and process.poll() is None:process.kill();process.wait(timeout=5)

    wall=memory=None
    try:
        journal=Journal(paths['samples'])
        row=sample('preflight');reason=cause(row,True)
        if reason:stop(reason,row)
        else:
            m,pins=bindings(owner,manifest,runner,runner_sha256);pins.append((capacity,capacity_sha256))
            record['bindings_verified_before_launch']=True
            wall,memory=m['limits']['wall_seconds'],m['limits']['memory_bytes'];record['limits']={'wall_seconds':wall,'memory_bytes':memory}
            for _ in range(plan['preflight_samples']-1):
                time.sleep(plan['sample_period_seconds']);row=sample('preflight');reason=cause(row,True)
                if reason:stop(reason,row);break
        if record['termination_reason'] is None:
            require(hashlib.sha256(POLICY).hexdigest()==POLICY_SHA256,'policy constant')
            with paths['policy'].open('xb') as f:f.write(POLICY);f.flush();os.fsync(f.fileno())
            require(digest(paths['policy'])==POLICY_SHA256,'materialized policy changed')
            pins.append((paths['policy'],POLICY_SHA256))
            entry=Path(python).absolute();require(entry.is_file(),'Python entrypoint missing')
            command=['/usr/bin/sandbox-exec','-f',str(paths['policy']),str(entry),'-B',str(runner),'--worker','--manifest',str(manifest),'--output',str(output)]
            record['command']=command
            with paths['log'].open('xb') as log:
                row=sample('before_launch');reason=cause(row,True)
                if reason:stop(reason,row)
                else:
                    contained(owner,output,exists=False)
                    require(not output.exists() and not output.is_symlink(),'output created before launch')
                    def child_limits():
                        cpu=max(1,math.ceil(wall*2));resource.setrlimit(resource.RLIMIT_CPU,(cpu,cpu+2));resource.setrlimit(resource.RLIMIT_FSIZE,(CHILD_FSIZE,CHILD_FSIZE))
                    env=os.environ.copy();env.update({'PYTHONDONTWRITEBYTECODE':'1','OMP_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'2','MKL_NUM_THREADS':'2','CUDA_VISIBLE_DEVICES':''})
                    process=subprocess.Popen(command,cwd=owner,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True,preexec_fn=child_limits)
                    begin=time.monotonic();record.update(status='failed',worker_launched=True,worker_pid=process.pid)
                    while process.poll() is None:
                        row=sample('running');reason=cause(row)
                        if reason:stop(reason,row);break
                        time.sleep(plan['sample_period_seconds'])
                    worker_end=time.monotonic()
                    if process.returncode!=0 and record['termination_reason'] is None:stop('worker_exit',sample('stop'))
                    if process.returncode==0 and record['termination_reason'] is None:
                        for path,sha in pins:require(digest(path)==sha,'bound input changed during execution')
                        record['bindings_unchanged_after_worker']=True
                        result_path=contained(owner,output/'result.json');result=read_json(result_path)
                        require(type(result) is dict and result.get('status')=='complete','worker result incomplete')
                        require(record['peak_sampled_rss_bytes'] is not None,'worker RSS never observed')
                        record['result_sha256']=digest(result_path,1048576);record['status']='complete'
        # A stop sample follows the exact triggering sample without replacing it.
        if record['termination_reason'] is not None and (last_phase!='stop'):
            sample('stop')
    except Exception as exc:
        stop(record['termination_reason'] or 'supervisor_error',trigger)
        record['error']=type(exc).__name__+': '+str(exc)
        if journal is not None:
            try:sample('stop')
            except Exception as stop_exc:record['stop_observation_error']=type(stop_exc).__name__+': '+str(stop_exc)
    finally:
        if process is not None and process.poll() is None:process.kill();process.wait(timeout=5)
        if process is not None and worker_end is None:worker_end=time.monotonic()
        if process is not None:record['returncode']=process.returncode
        try:
            if journal is not None:
                row=sample('final');reason=cause(row,not record['worker_launched'])
                if reason:
                    stop(reason,row)
                    if record['status']=='complete':record['status']='failed';record.pop('result_sha256',None)
                journal.close();record['resource_samples_sha256']=digest(paths['samples'],MAX_JOURNAL);record['sample_count']=journal.count
        except Exception as exc:
            record['final_observation_error']=type(exc).__name__+': '+str(exc);record['termination_reason']=record['termination_reason'] or 'final_observation_failed'
            record['status']='failed' if record['worker_launched'] else 'refused';record.pop('result_sha256',None)
            if journal is not None:journal.close()
        if record['termination_reason'] is not None and record['status']=='complete':record['status']='failed';record.pop('result_sha256',None)
        record['wall_seconds']=time.monotonic()-start
        record['worker_wall_seconds']=None if begin is None else worker_end-begin
        record['receipt_persisted']=True
        try:
            data=encode(record);require(len(data)<=MAX_RECEIPT,'receipt byte cap')
            with paths['pending'].open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
            os.link(paths['pending'],paths['receipt'])
            paths['pending'].unlink()
        except Exception as exc:
            record['receipt_persisted']=False;record['status']='failed' if record['worker_launched'] else 'refused'
            record['receipt_persistence_error']=type(exc).__name__+': '+str(exc)
            record['final_receipt_exists_after_persistence_error']=paths['receipt'].exists()
            print('Resource receipt persistence failed; no complete receipt is established.',file=sys.stderr)
    return record


def main():
    p=argparse.ArgumentParser()
    for flag in ('owner','manifest','runner','runner-sha256','python','output','capacity-plan','capacity-plan-sha256'):p.add_argument('--'+flag,required=True)
    a=p.parse_args();result=supervise(a.owner,a.manifest,a.runner,a.runner_sha256,a.python,a.output,a.capacity_plan,a.capacity_plan_sha256)
    print(json.dumps(result,sort_keys=True,allow_nan=False));return 0 if result['status']=='complete' and result['receipt_persisted'] else 1


if __name__=='__main__':raise SystemExit(main())
