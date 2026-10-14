"""Read-only acceptance of the exact 0.6.1 resource receipt and sampled journal.

Integrity checks do not authenticate a wholly fabricated consistent history,
reserve APFS capacity, or establish scientific or continuous resource validity.
"""
import hashlib
import json
import math
from pathlib import Path
import time

SUPERVISOR='cc275f8ca48eb832001ca78be8d8614f7c74f2dfd228139551d8c94f449ec698'
WORKER='7b2991f6b68719d815afc8137e563fc6d12e868689132850c9b9a483d957de1e'
NUMERICAL='2cefacc5c6fef3e6c61ae944b16d4d23542ea7cbe03d47773604f808e124a431'
POLICY='5c358b8d847211333e7ba22df82d84f796b5f30a41a2682209a949d783adbd08'
CAPS={'journal_bytes':8388608,'log_bytes':8388608,'receipt_bytes':65536,'output_files':10000,'walk_seconds':1.0,'child_fsize_bytes':67108864}
PLAN_KEYS={'artifact_id','version','free_disk_floor_bytes','output_budget_bytes','margin_bytes','max_output_files','preflight_samples','sample_period_seconds','max_sample_gap_seconds'}
RECEIPT_KEYS=set('artifact_id version status returncode termination_reason worker_pid worker_launched peak_sampled_rss_bytes runner_sha256 manifest_sha256 capacity_plan_sha256 supervisor_sha256 policy_sha256 capacity_plan observation_provider_mode memory_boundary network_boundary capacity_boundary output_budget_scope allocation_budget_scope bindings_verified_before_launch bindings_unchanged_after_worker receipt_compatibility receipt_publication sample_journal log sample_errors sampling_gaps resource_caps admission_required_available_bytes limits command result_sha256 resource_samples_sha256 sample_count wall_seconds worker_wall_seconds receipt_persisted'.split())
ROW_KEYS=set('sequence phase unix_time_ns elapsed_seconds worker_elapsed_seconds worker_pid disk output rss_bytes rss_state errors gap_seconds duration_seconds prospective_allocation_budget_bytes allocation_rounding_allowance_bytes remaining_allocation_budget_bytes required_available_bytes'.split())


def require(value,why):
    if not value:raise ValueError(why)


def canonical(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def equal(a,b,why):require(canonical(a)==canonical(b),why)
def integer(v,lo,hi,why):require(type(v) is int and lo<=v<=hi,why)
def number(v,lo,hi,why):require(type(v) in (float,int) and math.isfinite(v) and lo<=v<=hi,why)


def parse(raw):
    def unique(items):
        result={}
        for key,value in items:require(key not in result,'duplicate JSON key');result[key]=value
        return result
    return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda v:(_ for _ in ()).throw(ValueError('nonfinite JSON')))


def hash_file(path,deadline,cap=512*1024**2):
    p=Path(path);require(p.is_file() and not p.is_symlink() and p.stat().st_size<=cap,'bound regular file/size')
    h=hashlib.sha256()
    with p.open('rb') as f:
        for data in iter(lambda:f.read(1024**2),b''):
            require(time.monotonic()<deadline,'consumer wall cap');h.update(data)
    return h.hexdigest()


def read_json(path,cap=1048576):
    p=Path(path);require(p.is_file() and not p.is_symlink() and p.stat().st_size<=cap,'JSON file/size');return parse(p.read_bytes())


def confined(owner,path):
    p=Path(path);require(p.is_absolute() and p.is_relative_to(owner),'absolute owned path')
    for q in (p,*p.parents):
        if q==owner:break
        require(not q.is_symlink(),'symlink in owned path')
    require(p.resolve().is_relative_to(owner),'resolved path confinement');return p


def validate_plan(p):
    require(type(p) is dict and set(p)==PLAN_KEYS,'capacity schema')
    equal([p['artifact_id'],p['version']],['reiyah.resource-admission.capacity-plan','0.1.0'],'capacity identity')
    for k,lo,hi in [('free_disk_floor_bytes',4*1024**3,1024**4),('output_budget_bytes',65536,1024**3),('margin_bytes',1,4*1024**3),('max_output_files',4,10000),('preflight_samples',2,20)]:integer(p[k],lo,hi,'capacity '+k)
    number(p['sample_period_seconds'],.1,1,'sample period');number(p['max_sample_gap_seconds'],p['sample_period_seconds'],5,'sample gap')


def journal_rows(raw):
    require(len(raw)<=8388608 and raw.endswith(b'\n'),'complete bounded newline-terminated journal')
    lines=raw.splitlines();require(4<=len(lines)<=8192 and all(0<len(x)+1<=8192 for x in lines),'journal row limits')
    return [parse(x) for x in lines]


def validate_success(receipt,returned,outer,rows,expected):
    require(type(receipt) is dict and set(receipt)==RECEIPT_KEYS,'complete receipt exact schema')
    equal(returned,receipt,'returned and retained receipt differ')
    require(type(outer) is dict and set(outer)==set('artifact_id version returncode timed_out wall_seconds command freeze_sha256 supervisor_sha256 manifest_sha256 stdout_sha256 stderr_sha256 worker_log_sha256 worker_log_bytes'.split()),'outer exact schema')
    equal([outer['artifact_id'],outer['version'],outer['returncode'],outer['timed_out']],['reiyah.resource-admission.outer-execution','0.1.0',0,False],'outer successful exit required')
    number(outer['wall_seconds'],0,expected['outer_wall_limit_seconds'],'outer wall budget')
    for key in ('command','freeze_sha256','supervisor_sha256','manifest_sha256','stdout_sha256','stderr_sha256','worker_log_sha256','worker_log_bytes'):equal(outer[key],expected['outer'][key],'outer '+key)
    integer(outer['worker_log_bytes'],0,8388608,'outer worker log length')
    equal([receipt['artifact_id'],receipt['version'],receipt['status'],receipt['returncode'],receipt['termination_reason']],['reiyah.resource-admission.supervisor-receipt','0.1.0','complete',0,None],'supervisor complete identity')
    for key in ('worker_launched','receipt_persisted','bindings_verified_before_launch','bindings_unchanged_after_worker'):equal(receipt[key],True,'receipt '+key)
    for key in ('sample_errors','sampling_gaps'):equal(receipt[key],[],'no resource observations missing/errored')
    for key,value in {'runner_sha256':WORKER,'supervisor_sha256':SUPERVISOR,'policy_sha256':POLICY,
        'observation_provider_mode':'system','network_boundary':'worker_only_host_observer_outside_sandbox','resource_caps':CAPS}.items():equal(receipt[key],value,'receipt '+key)
    for key in ('manifest_sha256','capacity_plan_sha256','capacity_plan','result_sha256','resource_samples_sha256','sample_journal','log','command','limits'):equal(receipt[key],expected['receipt'][key],'receipt expected '+key)
    for key in ('memory_boundary','capacity_boundary','output_budget_scope','allocation_budget_scope','receipt_compatibility','receipt_publication'):require(type(receipt[key]) is str and 0<len(receipt[key])<=1024,'receipt scope string')
    plan=receipt['capacity_plan'];validate_plan(plan);limits=receipt['limits']
    equal(set(limits)=={'wall_seconds','memory_bytes'},True,'resource limit schema')
    number(limits['wall_seconds'],0.000001,600,'worker wall ceiling');integer(limits['memory_bytes'],1,3221225472,'worker memory ceiling')
    integer(receipt['worker_pid'],1,2**31-1,'worker PID');integer(receipt['sample_count'],4,8192,'sample count');equal(receipt['sample_count'],len(rows),'journal complete count')
    number(receipt['wall_seconds'],0,outer['wall_seconds']+1e-6,'supervisor time enclosed by outer')
    number(receipt['worker_wall_seconds'],0,min(limits['wall_seconds'],receipt['wall_seconds']),'worker wall observation')
    n=plan['preflight_samples'];require(len(rows)>=n+3,'complete sample phase coverage')
    require(all(type(r) is dict for r in rows),'journal rows must be objects')
    equal([r.get('phase') for r in rows],['preflight']*n+['before_launch']+['running']*(len(rows)-n-2)+['final'],'complete journal phase order')
    rss_values=[];previous=None;worker_offset=None
    for i,row in enumerate(rows):
        require(type(row) is dict and set(row)==ROW_KEYS,'sample exact schema');equal(row['sequence'],i,'sample ordinal');equal(row['errors'],[],'sample errors')
        integer(row['unix_time_ns'],1,2**63-1,'sample clock timestamp');number(row['elapsed_seconds'],0,receipt['wall_seconds'],'sample elapsed')
        number(row['duration_seconds'],0,plan['max_sample_gap_seconds'],'sample duration')
        require(row['elapsed_seconds']+row['duration_seconds']<=receipt['wall_seconds']+1e-6,'sample duration enclosed')
        if previous is None:equal(row['gap_seconds'],None,'first sample no invented gap')
        else:
            number(row['gap_seconds'],0,plan['max_sample_gap_seconds'],'sample gap')
            require(abs(row['gap_seconds']-(row['elapsed_seconds']-previous['elapsed_seconds']))<=1e-6,'gap chronology')
            require(row['gap_seconds']+1e-6>=previous['duration_seconds'],'sample overlap')
            if row['phase']=='preflight' or (row['phase']=='running' and previous['phase']=='running'):require(row['gap_seconds']+1e-6>=plan['sample_period_seconds'],'sample interval minimum')
        pre=row['phase'] in ('preflight','before_launch')
        equal(row['worker_pid'],None if pre else receipt['worker_pid'],'sample PID')
        if pre:
            equal([row['worker_elapsed_seconds'],row['rss_bytes'],row['rss_state']],[None,None,'not_launched'],'prelaunch worker state')
        else:
            number(row['worker_elapsed_seconds'],0,receipt['worker_wall_seconds'],'sample worker elapsed')
            if row['phase']=='final':
                equal(row['worker_elapsed_seconds'],receipt['worker_wall_seconds'],'final observed worker time')
                equal(row['rss_state'],'worker_exited_before_observation','final worker exit was already observed')
            else:
                offset=row['elapsed_seconds']-row['worker_elapsed_seconds']
                if worker_offset is None:worker_offset=offset
                require(abs(offset-worker_offset)<=1e-6,'worker clock origin')
            if row['rss_state']=='observed':
                integer(row['rss_bytes'],0,limits['memory_bytes'],'sampled RSS cap');rss_values.append(row['rss_bytes']);require(row['phase']=='running','RSS observed only while running')
            else:
                equal(row['rss_bytes'],None,'unobserved RSS unknown')
                require(row['rss_state'] in ('worker_exited_before_observation','worker_exited_during_observation'),'RSS observation state')
                require(row['phase']=='final' or i==len(rows)-2,'no later running sample after observed exit')
        disk=row['disk'];out=row['output']
        require(type(disk) is dict and set(disk)==set('available_bytes free_including_reserved_bytes total_bytes fragment_bytes measurement'.split()),'disk schema')
        for k in ('available_bytes','free_including_reserved_bytes','total_bytes','fragment_bytes'):integer(disk[k],1 if k=='fragment_bytes' else 0,2**63-1,'disk '+k)
        require(disk['available_bytes']<=disk['free_including_reserved_bytes']<=disk['total_bytes'],'disk order')
        equal(disk['measurement'],'statvfs_f_bavail_times_f_frsize; no purgeable estimate','system disk measurement')
        require(type(out) is dict and set(out)==set('file_count logical_bytes allocated_bytes walk_seconds measurement'.split()),'output measurement schema')
        integer(out['file_count'],0,plan['max_output_files']-2,'file budget');integer(out['logical_bytes'],0,2**63-1,'logical bytes');integer(out['allocated_bytes'],0,2**63-1,'allocated bytes')
        require(out['allocated_bytes']%512==0,'allocated block units');number(out['walk_seconds'],0,min(1.0,row['duration_seconds']+1e-6),'bounded output walk')
        require(type(out['measurement']) is str and 0<len(out['measurement'])<=512,'allocation scope')
        slack=plan['max_output_files']*(disk['fragment_bytes']-1);budget=plan['output_budget_bytes']+slack;remaining=max(0,budget-max(out['logical_bytes'],out['allocated_bytes']))
        required=plan['free_disk_floor_bytes']+plan['margin_bytes']+(budget if pre else remaining)
        for key,value in {'allocation_rounding_allowance_bytes':slack,'prospective_allocation_budget_bytes':budget,'remaining_allocation_budget_bytes':remaining,'required_available_bytes':required}.items():equal(row[key],value,'sample budget arithmetic '+key)
        require(disk['available_bytes']>=required and out['logical_bytes']+139264<=plan['output_budget_bytes'] and out['allocated_bytes']+139264<=budget,'sample capacity/output bounds')
        previous=row
    require(rss_values,'at least one actual RSS observation');equal(receipt['peak_sampled_rss_bytes'],max(rss_values),'peak RSS recomputation')
    require(worker_offset+1e-6>=rows[n]['elapsed_seconds']+rows[n]['duration_seconds'],'worker began before prelaunch sample completed')
    require(worker_offset+receipt['worker_wall_seconds']<=rows[-1]['elapsed_seconds']+1e-6,'worker finish after final sample')
    equal(receipt['admission_required_available_bytes'],plan['free_disk_floor_bytes']+plan['margin_bytes']+rows[-1]['prospective_allocation_budget_bytes'],'declared admission threshold')
    return {'status':'resource_receipt_and_journal_checked','samples':len(rows),'peak_sampled_rss_bytes':max(rss_values),'scope':'Sampled admission and retained execution records only; no reservation, continuous bound, process-tree or crash-durability claim.'}
