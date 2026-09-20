"""Byte admission only; no world construction or matching algorithm."""
from pathlib import Path
from fractions import Fraction
import hashlib, json

ROOT=Path(__file__).resolve().parents[3]
PACKET=Path(__file__).resolve().parent
OLD=Path('/Users/danielwahnich/.codex/reports/reiyah/value-10h-2026-09-18-c1y8k9yc/private')
LAST=Path('/Users/danielwahnich/.codex/reports/reiyah/operating-timing-2026-09-19-3r3g4m8z/private/study-01')
ROLES=('output_a','output_b')
FAMILIES=('current_partial','union_partial')
def require(ok,message):
    if not ok: raise ValueError(message)
def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
def binding(path):
    p=Path(path); b=p.read_bytes(); return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def put(path,value):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f: json.dump(value,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
def q(value):
    if isinstance(value,dict):
        z=Fraction(int(value['numerator']),int(value['denominator']))
        require(value=={'numerator':str(z.numerator),'denominator':str(z.denominator)},'noncanonical rational')
        return z
    return Fraction(value)
def w(value):
    z=Fraction(value);return {'numerator':str(z.numerator),'denominator':str(z.denominator)}
def read(path): return json.loads(Path(path).read_text())
def load_sources():
    entries={}
    def get(path,expected=None):
        b=binding(path)
        if expected:require(b=={k:expected[k] for k in b},'source binding differs')
        entries[b['path']]=b;return read(path)
    first=get(OLD/'operating-witness-01/analysis/RESULTS.json')
    vfirst=get(OLD/'operating-witness-01/VERIFICATION.json')
    require(vfirst['results_sha256']==binding(OLD/'operating-witness-01/analysis/RESULTS.json')['sha256'] and vfirst['all_7707_parent_rows_checked'],'earlier verification absent')
    policy=get(OLD/'operating-policy-01/runs/operating-01/RESULTS.json')
    parent=get(LAST/'analysis/RESULTS.json');verified=get(LAST/'VERIFICATION.json')
    require(verified['results_sha256']==binding(LAST/'analysis/RESULTS.json')['sha256'] and verified['all_7707_parent_rows_checked'] and verified['all_universal_decisions_unchanged'],'latest verification absent')
    targets=[{'section':section,'index':i,'row_sha256':digest(row)} for section in ('primary_rows','anchor_rows') for i,row in enumerate(parent[section]) if row['family'] in FAMILIES and row['decision']=='unresolved']
    require(len(targets)==623,'target population differs')
    rows=[parent[t['section']][t['index']] for t in targets]
    require(all(r['evidence']=='opposite_worlds' for r in rows),'inherited witness gap')
    needed_states={k for r in rows for k in r['state_keys']}
    states={e['key']:get(e['path'],e) for e in policy['state_records'] if e['key'] in needed_states}
    for records in (first['refined_states'],parent['refined_pairs']):
        for e in records:
            if e['key'] in needed_states:states[e['key']]=get(e['path'],e)['state']
    images={v['image']['id'] for v in states.values()}
    banks={e['image_id']:get(e['path'],e) for e in policy['world_banks'] if e['image_id'] in images}
    proof_entries={e['key']:e for records in (policy['proof_records'],first['new_proofs'],parent['new_proofs']) for e in records}
    needed_proofs={k for r in rows for endpoint in r['world_proof_keys'] for k in endpoint}
    proofs={k:get(proof_entries[k]['path'],proof_entries[k]) for k in sorted(needed_proofs)}
    pairs=sorted({(k,r['family']) for r in rows for k in r['state_keys']})
    for k,f in pairs:
        state=states[k]; bank=banks[state['image']['id']];c=bank['temporal'][f.removesuffix('_partial')]
        require(c['state']=='available' and c['unknown_count']==len(c['unknown_ids']) and c['unknown_ids']==sorted(set(c['unknown_ids'])),'census unavailable/invalid')
        require(state['analysis']['families'][f]['state']=='available','state unavailable')
    return {'parent':parent,'states':states,'banks':banks,'proofs':proofs,'targets':targets,'pairs':pairs,'bindings':sorted(entries.values(),key=lambda e:e['path'])}
def context(data,key,family):
    state=data['states'][key];bank=data['banks'][state['image']['id']]
    return state['image'],bank['worlds'][bank['known_world']],bank['temporal'][family.removesuffix('_partial')]['unknown_ids']
def guard(area):
    f=read(PACKET/'freeze.json')
    for e in f['implementation']:
        b=binding(ROOT/e['path']);require(b['sha256']==e['sha256'] and b['bytes']==e['bytes'],'implementation changed')
    require(binding(Path(area)/'ALLOCATION.json')['sha256']==f['allocation_sha256'],'allocation changed')
    for e in read(Path(area)/'ALLOCATION.json')['bindings']:require(binding(e['path'])==e,'frozen source changed')
    return f
