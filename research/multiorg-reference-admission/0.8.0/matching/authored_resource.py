"""Authored record fixtures only, never an empirical execution receipt."""
import copy
import json
from pathlib import Path
import resource_gate as g

def fixture():
    plan={'artifact_id':'reiyah.resource-admission.capacity-plan','version':'0.1.0','free_disk_floor_bytes':4*1024**3,'output_budget_bytes':1024**2,
        'margin_bytes':1024**2,'max_output_files':100,'preflight_samples':2,'sample_period_seconds':.1,'max_sample_gap_seconds':2}
    rows=[]
    for i,(phase,elapsed) in enumerate(zip(['preflight','preflight','before_launch','running','running','final'],[0.,.2,.21,.23,.43,.6])):
        pre=phase in ('preflight','before_launch');observed=phase=='running';budget=plan['output_budget_bytes']+100*4095;remaining=budget-4096
        row={'sequence':i,'phase':phase,'unix_time_ns':10**18+i*10**8,'elapsed_seconds':elapsed,'worker_elapsed_seconds':None if pre else (.35 if phase=='final' else elapsed-.22),
            'worker_pid':None if pre else 123,'disk':{'available_bytes':8*1024**3,'free_including_reserved_bytes':9*1024**3,'total_bytes':16*1024**3,'fragment_bytes':4096,'measurement':'statvfs_f_bavail_times_f_frsize; no purgeable estimate'},
            'output':{'file_count':3,'logical_bytes':1000,'allocated_bytes':4096,'walk_seconds':.0001,'measurement':'authored summed block observation'},
            'rss_bytes':1000000 if observed else None,'rss_state':'not_launched' if pre else 'observed' if observed else 'worker_exited_before_observation',
            'errors':[],'gap_seconds':None if i==0 else elapsed-rows[-1]['elapsed_seconds'],'duration_seconds':.001,
            'prospective_allocation_budget_bytes':budget,'allocation_rounding_allowance_bytes':409500,'remaining_allocation_budget_bytes':remaining,
            'required_available_bytes':plan['free_disk_floor_bytes']+plan['margin_bytes']+(budget if pre else remaining)}
        rows.append(row)
    receipt={k:'authored scope' for k in g.RECEIPT_KEYS}
    receipt.update(artifact_id='reiyah.resource-admission.supervisor-receipt',version='0.1.0',status='complete',returncode=0,termination_reason=None,
        worker_pid=123,worker_launched=True,peak_sampled_rss_bytes=1000000,runner_sha256=g.WORKER,manifest_sha256='1'*64,capacity_plan_sha256='2'*64,
        supervisor_sha256=g.SUPERVISOR,policy_sha256=g.POLICY,capacity_plan=plan,observation_provider_mode='system',network_boundary='worker_only_host_observer_outside_sandbox',
        bindings_verified_before_launch=True,bindings_unchanged_after_worker=True,sample_journal='run.resources.jsonl',log='run.log',sample_errors=[],sampling_gaps=[],
        resource_caps=g.CAPS,admission_required_available_bytes=plan['free_disk_floor_bytes']+plan['margin_bytes']+rows[-1]['prospective_allocation_budget_bytes'],
        limits={'wall_seconds':600,'memory_bytes':3221225472},command=['authored worker command'],result_sha256='3'*64,resource_samples_sha256='4'*64,
        sample_count=6,wall_seconds=.7,worker_wall_seconds=.35,receipt_persisted=True)
    outer={'artifact_id':'reiyah.resource-admission.outer-execution','version':'0.1.0','returncode':0,'timed_out':False,'wall_seconds':1.,'command':['authored supervisor command'],
        'freeze_sha256':'5'*64,'supervisor_sha256':g.SUPERVISOR,'manifest_sha256':'1'*64,'stdout_sha256':'6'*64,'stderr_sha256':'7'*64,'worker_log_sha256':'8'*64,'worker_log_bytes':0}
    expected={'outer_wall_limit_seconds':660,'outer':{k:outer[k] for k in ('command','freeze_sha256','supervisor_sha256','manifest_sha256','stdout_sha256','stderr_sha256','worker_log_sha256','worker_log_bytes')},
        'receipt':{k:receipt[k] for k in ('manifest_sha256','capacity_plan_sha256','capacity_plan','result_sha256','resource_samples_sha256','sample_journal','log','command','limits')}}
    return copy.deepcopy((receipt,outer,rows,expected))


def persist(path,obj):
    path.write_bytes(g.canonical(obj)+b'\n')
    return {'path':str(path),'sha256':__import__('hashlib').sha256(path.read_bytes()).hexdigest()}

def sha(path):return __import__('hashlib').sha256(path.read_bytes()).hexdigest()

def wrap(folder,bundle,profile,old_check):
    # A tiny fabricated receipt population, explicitly limited to admission tests.
    receipt,outer,rows,_=fixture();owner=folder;output=folder
    plan=folder/'capacity.json';persist(plan,receipt['capacity_plan'])
    sources={name:{'path':str(folder/(name+'.source')),'sha256':digest} for name,digest in {
        'supervisor':g.SUPERVISOR,'worker':g.WORKER,'numerical_checker':g.NUMERICAL,'manifest':profile['manifest_sha256'],
        'protocol':profile['protocol_sha256'],'runtime_before':'a'*64}.items()}
    sources['capacity_plan']={'path':str(plan),'sha256':sha(plan)}
    paths={name:str(folder/(name+'.json')) for name in ('outer','stdout','stderr','runtime_after','freeze')};paths['output']=str(output)
    cp=folder/'consumer-contract.json';contract={'artifact_id':'reiyah.multiorg.resource-consumer-contract','version':'0.1.0','sources':sources,'paths':paths,'python_entrypoint':'/authored/python','outer_wall_limit_seconds':660}
    bundle['resource_contract']=persist(cp,contract);profile['resource_contract_sha256']=sha(cp)
    # The files have prescribed names in the real consumer; keep those exact here.
    oldpair=Path(bundle['pair']['path']);newpair=folder/'result.json';oldpair.rename(newpair);bundle['pair']['path']=str(newpair)
    pp=output.with_suffix('.process.json');bundle['supervisor']={'path':str(pp),'sha256':''}
    obs_paths={'outer':Path(paths['outer']),'stdout':Path(paths['stdout']),'stderr':Path(paths['stderr']),
        'runtime_after':Path(paths['runtime_after']),'result':newpair,'process_receipt':pp,
        'journal':output.with_suffix('.resources.jsonl'),'policy':output.with_suffix('.sandbox.sb'),'worker_log':output.with_suffix('.log')}
    obs_paths['journal'].write_bytes(b''.join(g.canonical(r)+b'\n' for r in rows));obs_paths['policy'].write_bytes(b'(version 1)\n(allow default)\n(deny network*)\n')
    obs_paths['stderr'].write_bytes(b'');obs_paths['worker_log'].write_bytes(b'authored log\n');persist(obs_paths['runtime_after'],{'authored_only':True})
    required={str(cp):sha(cp),str(owner/'consumer/check_pair_resource.py'):profile['consumer_sha256'],str(owner/'consumer/resource_gate.py'):profile['resource_gate_sha256'],**{d['path']:d['sha256'] for d in sources.values()}}
    bindings={str(Path(p).relative_to(owner)):{'sha256':digest,'bytes':0} for p,digest in required.items()}
    freeze=Path(paths['freeze']);persist(freeze,{'bindings':bindings})
    receipt.update(manifest_sha256=profile['manifest_sha256'],capacity_plan_sha256=sha(plan),result_sha256=bundle['pair']['sha256'],
        sample_journal=obs_paths['journal'].name,log=obs_paths['worker_log'].name,resource_samples_sha256=sha(obs_paths['journal']),
        command=['/usr/bin/sandbox-exec','-f',str(obs_paths['policy']),'/authored/python','-B',sources['worker']['path'],'--worker','--manifest',sources['manifest']['path'],'--output',str(output)])
    persist(pp,receipt);bundle['supervisor']['sha256']=sha(pp);persist(obs_paths['stdout'],receipt)
    outer.update(command=['/authored/python','-B',sources['supervisor']['path'],'--owner',str(owner),'--manifest',sources['manifest']['path'],
        '--runner',sources['worker']['path'],'--runner-sha256',g.WORKER,'--python','/authored/python','--output',str(output),'--capacity-plan',str(plan),'--capacity-plan-sha256',sha(plan)],
        freeze_sha256=sha(freeze),manifest_sha256=profile['manifest_sha256'],stdout_sha256=sha(obs_paths['stdout']),stderr_sha256=sha(obs_paths['stderr']),worker_log_sha256=sha(obs_paths['worker_log']),worker_log_bytes=obs_paths['worker_log'].stat().st_size)
    persist(obs_paths['outer'],outer)
    numeric={k:old_check[k] for k in ('status','complete_pairs','result_sha256','observations')}
    numeric.update(failure_sha256=None,unbound_partial_array_files=[],terminal_semantic_refusal=None,scope=__import__('input_gate').SCOPE,storage_output_status=__import__('input_gate').STORAGE)
    check={'artifact_id':'reiyah.multiorg.resource-qualified-pair-check','version':'0.1.0','status':'complete_pair_verified','complete_pairs':1,
        'consumer_sha256':profile['consumer_sha256'],'resource_gate_sha256':profile['resource_gate_sha256'],'numerical_checker_sha256':profile['numerical_checker_sha256'],
        'contract_sha256':sha(cp),'freeze_sha256':sha(freeze),'frozen_files_checked_before_and_after':len(bindings),
        'resource_admission':{'status':'resource_receipt_and_journal_checked','samples':6,'peak_sampled_rss_bytes':1000000,'scope':'Sampled admission and retained execution records only; no reservation, continuous bound, process-tree or crash-durability claim.'},
        'runtime':{'status':'runtime_report_and_current_declared_bytes_checked'},'input_reconstruction':{'status':'all_declared_tensor_identities_reconstructed','version':'0.6.0','image_id':profile['image_id'],
            'image_sha256':profile['image_sha256'],'tensor_count':2*profile['tiles'],'tiles_per_model':profile['tiles']},
        'image_id':profile['image_id'],'image_contract_sha256':profile['image_contract_sha256'],'manifest_sha256':profile['manifest_sha256'],
        'source_bindings':old_check['source_bindings'],'numerical_result':numeric,
        'observations':{k:{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for k,p in obs_paths.items()}}
    bundle['pair_checker']=persist(Path(bundle['pair_checker']['path']),check)
    policy=owner/'execution/shared/check.sandbox.sb';policy.parent.mkdir(parents=True);policy.write_bytes(obs_paths['policy'].read_bytes())
    execution={'artifact_id':'reiyah.multiorg.resource-consumer-execution','version':'0.1.0','returncode':0,'timed_out':False,'wall_seconds':1,
        'report_sha256':bundle['pair_checker']['sha256'],**{k:check[k] for k in ('consumer_sha256','resource_gate_sha256','numerical_checker_sha256','contract_sha256','freeze_sha256')},
        'command':['/usr/bin/sandbox-exec','-f',str(policy),'/authored/python','-B',str(owner/'consumer/check_pair_resource.py'),'--owner',str(owner),
            '--contract',str(cp),'--contract-sha256',sha(cp),'--freeze-sha256',sha(freeze),'--report',bundle['pair_checker']['path']]}
    bundle['checker_execution']=persist(Path(bundle['checker_execution']['path']),execution)


def rewrite(root,manifest,bundle,objects):
    check=objects['pair_checker'];check['numerical_result']['result_sha256']=bundle['pair']['sha256']
    objects['supervisor']['result_sha256']=bundle['pair']['sha256'];bundle['supervisor']=persist(Path(bundle['supervisor']['path']),objects['supervisor'])
    paths=check['observations'];persist(Path(paths['stdout']['path']),objects['supervisor'])
    outer=json.loads(Path(paths['outer']['path']).read_bytes());outer['stdout_sha256']=sha(Path(paths['stdout']['path']));persist(Path(paths['outer']['path']),outer)
    for d in paths.values():
        p=Path(d['path']);d.update(sha256=sha(p),bytes=p.stat().st_size)
    bundle['pair_checker']=persist(Path(bundle['pair_checker']['path']),check);objects['checker_execution']['report_sha256']=bundle['pair_checker']['sha256']
    bundle['checker_execution']=persist(Path(bundle['checker_execution']['path']),objects['checker_execution'])
    return persist(root/'input.json',manifest)
