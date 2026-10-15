"""Fill only frozen descriptor slots after complete pair admission."""
from pathlib import Path
import datetime,hashlib,json,time
P=Path(__file__).resolve().parent
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def write(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
freeze=json.loads((P/'EXECUTION_FREEZE.json').read_text())
for n,b in freeze['bindings'].items():
    q=P/n;assert q.stat().st_size==b['bytes'] and sha(q)==b['sha256'],n
closed=json.loads((P/'COHORT_EXECUTION_CLOSEOUT.json').read_text())
assert closed['status']=='complete_two_pairs' and closed['frozen_bindings_unchanged']
outer=json.loads((P/'COHORT_LAUNCH_EXECUTION.json').read_text())
assert outer['returncode']==0 and outer['timed_out'] is False
template=P/'matching-execution/input-template.json';x=json.loads(template.read_text())
for i,bundle in enumerate(x['pairs']):
    for k,d in bundle.items():
        if not isinstance(d,dict):continue
        q=Path(d['path']);assert q.is_file() and not q.is_symlink()
        actual=sha(q)
        if i>=2 and k!='resource_contract':
            assert d['sha256']=='FILL_ONLY_AFTER_COMPLETE_PAIR_ADMISSION';d['sha256']=actual
        else:assert d['sha256']==actual
    report=json.loads(Path(bundle['pair_checker']['path']).read_text())
    execution=json.loads(Path(bundle['checker_execution']['path']).read_text())
    assert report['status']=='complete_pair_verified' and report['complete_pairs']==1
    assert execution['returncode']==0 and execution['report_sha256']==bundle['pair_checker']['sha256']
write(P/'matching-execution/input.json',x)
files=set()
def add(q):
    q=Path(q)
    assert q.is_file() and not q.is_symlink(),str(q)
    files.add(q)
for n in freeze['bindings']:add(P/n)
for n in ('EXECUTION_FREEZE.json','FREEZE_REVIEW.json','COHORT_EXECUTION_CLOSEOUT.json','COHORT_LAUNCH_EXECUTION.json','prepare_matching.py'):add(P/n)
for q in (P/'matching-execution').iterdir():
    if q.is_file():add(q)
for n in json.loads((P/'matching/DEPENDENCIES.json').read_text()):add(P/'candidate'/n)
refmanifest=Path(x['reference_manifest']['path']);add(refmanifest)
ref=json.loads(refmanifest.read_text())
selected=[b['image_id'] for b in x['pairs']]
for r in ref['images']:
    if r['tiff_path'] in selected:
        for a in r['annotations']:
            q=Path(x['reference_root'])/a['local_path'];assert q.stat().st_size==a['byte_size'] and sha(q)==a['sha256'];add(q)
for i,b in enumerate(x['pairs']):
    for d in b.values():
        if isinstance(d,dict):add(d['path'])
    # Bind every complete retained output, not partial outputs from other attempts.
    for q in Path(b['pair']['path']).parent.rglob('*'):
        if q.is_file():add(q)
    if i>0:
        c=json.loads(Path(b['resource_contract']['path']).read_text())
        for d in c['sources'].values():add(d['path'])
        for name,q in c['paths'].items():
            if name!='output':add(q)
        owner=Path(c['paths']['freeze']).parent
        histfreeze=json.loads(Path(c['paths']['freeze']).read_text())
        for n,pin in histfreeze['bindings'].items():
            q=owner/n;assert q.stat().st_size==pin['bytes'] and sha(q)==pin['sha256'];add(q)
        report=json.loads(Path(b['pair_checker']['path']).read_text())
        for d in report['observations'].values():
            if isinstance(d,dict) and 'path' in d:add(d['path'])
        runtime=json.loads(Path(c['sources']['runtime_before']['path']).read_text())
        for d in runtime['checked_files']+runtime['records']:add(Path(runtime['venv'])/d['path'])
        for path in runtime['runtime_pins']:add(path)
    else:
        owner=Path(b['pair']['path']).parents[2]
        add(owner/'EXECUTION_FREEZE.json')
        for d in json.loads((owner/'EXECUTION_FREEZE.json').read_text())['bindings']:
            q=owner/d['path'];assert q.stat().st_size==d['bytes'] and sha(q)==d['sha256'];add(q)
runtime=json.loads((P/'matching-execution/runtime-before.json').read_text())
for d in runtime['files']:add(d['path'])
add(runtime['python_resolved_path'])
rows=[]
for q in sorted(files):
    name=str(q.relative_to(P)) if q.is_relative_to(P) else str(q)
    rows.append({'path':name,'sha256':sha(q),'bytes':q.stat().st_size})
write(P/'MATCHING_FREEZE.json',{'artifact_id':'reiyah.multiorg.cohort-completion.matching-freeze','version':'0.8.0',
 'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bindings':rows,
 'scope':'All four complete pairs and their original custody, exact references, current runtime, native and matching sources. No changed comparison after outcomes.'})
print(json.dumps({'status':'frozen','files':len(rows),'input_sha256':sha(P/'matching-execution/input.json'),'freeze_sha256':sha(P/'MATCHING_FREEZE.json')}))
