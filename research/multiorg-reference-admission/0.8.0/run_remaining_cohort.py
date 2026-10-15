"""One fixed attempt per remaining image, qualified guard and consumer, no retry."""
from pathlib import Path
import datetime,hashlib,json,os,signal,subprocess,time
P=Path(__file__).resolve().parent
ORIG=Path('/Users/danielwahnich/.codex/reports/reiyah/owned-trial-frontier-2026-10-12-pz2p4ld2')
PY=str(ORIG/'runtime/venv/bin/python')
WORKER='7b2991f6b68719d815afc8137e563fc6d12e868689132850c9b9a483d957de1e'
SUPERVISOR='cc275f8ca48eb832001ca78be8d8614f7c74f2dfd228139551d8c94f449ec698'
CONSUMER='420e2aeacebbb3fc2502084c5195aa6fb5eab4c773d95f37394960ce87376e96'
GATE='b2782d4234af6cb248e2899671cae6afdecb9c870f109e16b19323213b828638'
NUMERICAL='2cefacc5c6fef3e6c61ae944b16d4d23542ea7cbe03d47773604f808e124a431'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def verify(freeze):
    for name,pin in freeze['bindings'].items():
        p=P/name
        if p.is_symlink() or p.stat().st_size!=pin['bytes'] or sha(p)!=pin['sha256']:raise ValueError('frozen file changed: '+name)
def observe_window(count=2):
    plan=json.loads((P/'execution/shared/capacity-plan.json').read_text());samples=[]
    for i in range(20):
        s=os.statvfs(P);available=s.f_bavail*s.f_frsize
        required=plan['free_disk_floor_bytes']+plan['margin_bytes']+count*(plan['output_budget_bytes']+plan['max_output_files']*(s.f_frsize-1))+20971520
        samples.append({'sequence':i,'at':now(),'monotonic':time.monotonic(),'available':available,'fragment_size':s.f_frsize,'remaining_pairs':count,'required':required})
        if available<required:break
        if i<19:time.sleep(.5)
    return {'samples':samples,'passed':len(samples)==20 and all(s['available']>=s['required'] for s in samples),'scope':'Sampled full remaining-cohort budget plus floor/margin/metadata; no shared filesystem reservation.'}
def run_capture(command,stdout,stderr,timeout):
    """On timeout stop only this invocation and observed direct worker children."""
    started=time.monotonic();timed_out=False;proc=None;cleanup=[]
    with stdout.open('xb') as out,stderr.open('xb') as err:
        try:
            proc=subprocess.Popen(command,cwd=P,stdout=out,stderr=err,stdin=subprocess.DEVNULL,start_new_session=True)
            try:proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:timed_out=True
        finally:
            if proc is not None and proc.poll() is None:
                try:
                    status=subprocess.run(['/bin/ps','-axo','pid=,ppid='],capture_output=True,text=True,timeout=3)
                    if status.returncode!=0:raise RuntimeError('child discovery nonzero exit')
                    children=[]
                    for line in status.stdout.splitlines():
                        pid,ppid=map(int,line.split())
                        if ppid==proc.pid:children.append(pid)
                    for pid in children:
                        try:os.kill(pid,signal.SIGKILL);cleanup.append({'action':'kill_observed_direct_child','pid':pid})
                        except ProcessLookupError:cleanup.append({'action':'observed_child_already_exited','pid':pid})
                except BaseException as exc:
                    cleanup.append({'action':'child_discovery_or_stop_failed','error_type':type(exc).__name__,'descendant_cleanup_verified':False})
                finally:
                    try:os.killpg(proc.pid,signal.SIGKILL);cleanup.append({'action':'kill_owned_outer_group','pid':proc.pid})
                    except ProcessLookupError:cleanup.append({'action':'outer_already_exited','pid':proc.pid})
                    finally:
                        try:proc.wait(timeout=5)
                        finally:
                            write(stdout.with_name(stdout.name+'.cleanup.json'),{'actions':cleanup,'outer_returncode':proc.returncode,'limitation':'Observed direct children only; child discovery failure does not establish complete descendant cleanup.'})
    return {'returncode':proc.returncode,'timed_out':timed_out,'wall_seconds':time.monotonic()-started}
def budget_admission(i):
    plan=json.loads((P/'PLAN.json').read_text())
    elapsed=time.monotonic()-plan['monotonic_start']
    remaining=plan['owner_wall_budget_seconds']-elapsed
    required=(4-i)*(660+120+300+20)+plan['prelaunch_reserve_seconds']
    row={'at':now(),'elapsed_owner_seconds':elapsed,'remaining_seconds':remaining,'required_seconds':required,
         'passed':remaining>=required,'historical_active_effort':'unknown, not reset','remaining_pairs':4-i}
    write(P/f'execution/image-{i}/budget-admission.json',row)
    if not row['passed']:raise ValueError('remaining time cannot cover runs, checks and closeout')

def main():
    freeze=json.loads((P/'EXECUTION_FREEZE.json').read_text());verify(freeze);freeze_sha=sha(P/'EXECUTION_FREEZE.json')
    assert sha(Path(__file__))==freeze['bindings'][Path(__file__).name]['sha256']
    write(P/'COHORT_LAUNCH.json',{'at':now(),'freeze_sha256':freeze_sha,'max_pairs':2,'attempts_per_pair':1,'no_retry':True})
    runs=[];stop=None;started=time.monotonic()
    try:
        for i in (2,3):
            budget_admission(i)
            verify(freeze);d=P/f'execution/image-{i}';out=d/'actual-run'
            capacity=observe_window(4-i);write(d/'cohort-capacity-window.json',capacity)
            if not capacity['passed']:raise ValueError('remaining-cohort capacity admission refused before model launch')
            contract_path=d/'consumer-contract.json';contract=json.loads(contract_path.read_text());sources=contract['sources']
            command=[PY,'-B',sources['supervisor']['path'],'--owner',str(P),'--manifest',sources['manifest']['path'],'--runner',sources['worker']['path'],'--runner-sha256',WORKER,'--python',PY,'--output',str(out),'--capacity-plan',sources['capacity_plan']['path'],'--capacity-plan-sha256',sources['capacity_plan']['sha256']]
            write(d/'LAUNCH.json',{'at':now(),'command':command,'freeze_sha256':freeze_sha,'attempt':1})
            outer=run_capture(command,d/'launch.stdout',d/'launch.stderr',660)
            log=out.with_suffix('.log')
            outer.update(artifact_id='reiyah.resource-admission.outer-execution',version='0.1.0',command=command,freeze_sha256=freeze_sha,supervisor_sha256=SUPERVISOR,manifest_sha256=sources['manifest']['sha256'],stdout_sha256=sha(d/'launch.stdout'),stderr_sha256=sha(d/'launch.stderr'),worker_log_sha256=sha(log) if log.exists() else None,worker_log_bytes=log.stat().st_size if log.exists() else None)
            write(d/'outer.json',outer);runs.append({'index':i,'outer':outer,'consumer_returncode':None});print(json.dumps({'image':i,'outer_returncode':outer['returncode'],'timed_out':outer['timed_out']}),flush=True)
            verify(freeze)
            if outer['returncode']!=0 or outer['timed_out']:raise ValueError('supervisor refusal: no later images or retry')
            after=P/f'runtime-audit/after-image-{i}.json'
            audit_command=['/usr/bin/sandbox-exec','-f',str(P/'execution/shared/check.sandbox.sb'),PY,'-B',str(P/'runtime-audit/audit.py'),'--old',str(ORIG),'--output',str(after)]
            audit=run_capture(audit_command,P/f'runtime-audit/after-image-{i}.stdout',P/f'runtime-audit/after-image-{i}.stderr',120)
            write(P/f'runtime-audit/after-image-{i}-execution.json',{'command':audit_command,**audit})
            if audit['returncode']!=0 or audit['timed_out']:raise ValueError('runtime re-audit failed')
            review=P/f'review/image-{i}';review.mkdir(parents=True)
            report=review/'PAIR_CHECK.json'
            check_command=['/usr/bin/sandbox-exec','-f',str(P/'execution/shared/check.sandbox.sb'),PY,'-B',str(P/'consumer/check_pair_resource.py'),'--owner',str(P),'--contract',str(contract_path),'--contract-sha256',sha(contract_path),'--freeze-sha256',freeze_sha,'--report',str(report)]
            checked=run_capture(check_command,review/'check.stdout',review/'check.stderr',300)
            checked.update(artifact_id='reiyah.multiorg.resource-consumer-execution',version='0.1.0',report_sha256=sha(report) if report.exists() else None,consumer_sha256=CONSUMER,resource_gate_sha256=GATE,numerical_checker_sha256=NUMERICAL,contract_sha256=sha(contract_path),freeze_sha256=freeze_sha,command=check_command)
            write(review/'CHECK_EXECUTION.json',checked);runs[-1]['consumer_returncode']=checked['returncode'];verify(freeze)
            print(json.dumps({'image':i,'consumer_returncode':checked['returncode']}),flush=True)
            if checked['returncode']!=0 or checked['timed_out']:raise ValueError('complete pair consumer refused: no later images or retry')
            result=json.loads(report.read_text())
            if result['status']!='complete_pair_verified' or result['complete_pairs']!=1:raise ValueError('pair not admitted')
        return 0
    except BaseException as exc:
        stop=type(exc).__name__+': '+str(exc);raise
    finally:
        unchanged=True
        try:verify(freeze)
        except Exception:unchanged=False
        write(P/'COHORT_EXECUTION_CLOSEOUT.json',{'at':now(),'status':'complete_two_pairs' if stop is None and len(runs)==2 else 'stopped','runs':runs,'stop_reason':stop,'wall_seconds':time.monotonic()-started,'frozen_bindings_unchanged':unchanged,'new_inference_owner_closed':True,'no_retry':True})
if __name__=='__main__':raise SystemExit(main())
