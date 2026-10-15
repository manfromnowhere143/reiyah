"""Recheck completed observations without inference or edits to closed owners."""
from pathlib import Path
import hashlib, importlib.util, json, sys, time
P=Path(__file__).resolve().parent
BASE=P.parent
OLD=BASE/'multiorg-capacity-recovery-2026-10-14-ycbwa8ii'
FIRST=BASE/'multiorg-complete-pair-2026-10-14-gfyxnffu'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def module(p,n):
    sys.path.insert(0,str(p.parent))
    s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def strip_times(x):
    if isinstance(x,dict):return {k:strip_times(v) for k,v in x.items() if k not in ('wall_seconds',)}
    if isinstance(x,list):return [strip_times(v) for v in x]
    return x
which=sys.argv[1];start=time.monotonic();t=json.loads((P/'matching-execution/input-template.json').read_text())
idx=0 if which=='legacy' else 1;bundle=t['pairs'][idx]
for v in bundle.values():
    if isinstance(v,dict):assert sha(Path(v['path']))==v['sha256']
profile=json.loads((P/'matching/contract.json').read_text())['profiles'][idx]
expected=json.loads(Path(bundle['pair_checker']['path']).read_text())
if which=='legacy':
    source=FIRST/'reference/check_pair.py';assert sha(source)==profile['checker_sha256']
    freeze=json.loads((FIRST/'EXECUTION_FREEZE.json').read_text())
    for r in freeze['bindings']:
        q=FIRST/r['path'];assert q.stat().st_size==r['bytes'] and sha(q)==r['sha256']
    c=module(source,'legacy_checker')
    ctx=c.bind_inputs(FIRST,profile['worker_sha256'],profile['manifest_sha256'],profile['protocol_sha256'],start+300)
    root=FIRST/'execution/actual-run';pp=root.with_suffix('.process.json')
    actual=c.verify_output(root,ctx,c.load_json(pp,1048576),start+300)
    actual.update(checker_sha256=sha(source),manifest_sha256=ctx['manifest_sha256'],source_bindings=ctx['bindings'],
                  process_receipt_sha256=sha(pp),input_reconstruction=ctx['input_reconstruction'],check_budget_seconds=300)
else:
    source=OLD/'consumer/check_pair_resource.py';assert sha(source)==profile['consumer_sha256']
    c=module(source,'resource_checker')
    actual=c.execute(OLD,Path(bundle['resource_contract']['path']),bundle['resource_contract']['sha256'],expected['freeze_sha256'],start+300)
    actual['check_budget_seconds']=300
assert strip_times(actual)==strip_times(expected),'replayed non-timing result differs'
report={'artifact_id':'reiyah.multiorg.completed-pair-reuse','version':'0.8.0','status':'passed','kind':which,
        'image_id':bundle['image_id'],'original_bundle':bundle,'source_sha256':sha(source),
        'raw_arrays_rechecked':actual.get('numerical_result',actual)['raw_array_files_checked'],
        'non_timing_fields_match':True,'model_forwards':0,'wall_seconds':time.monotonic()-start,
        'scope':'Whole-output numerical recheck and input reconstruction; old owner unchanged. Same-investigation checking, not independent replication.'}
(P/'reuse').mkdir(exist_ok=True)
with (P/'reuse'/f'{which}.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({k:report[k] for k in ('status','kind','raw_arrays_rechecked','model_forwards','wall_seconds')}))
