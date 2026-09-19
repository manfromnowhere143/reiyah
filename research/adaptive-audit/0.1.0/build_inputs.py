"""Prepare exposed endpoints and authored allocations; no stopping outcomes."""
from pathlib import Path
from fractions import Fraction
import hashlib,itertools,json,random,sys

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def put(p,v):Path(p).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def q(v):return Fraction(int(v['numerator']),int(v['denominator']))
def authored():
    def pop(name,values,kind):
        return {'id':name,'kind':kind,'units':[{'id':f'u{i:02}','bound':'1','lower':str(Fraction(v[0])),'upper':str(Fraction(v[1])),'status':'observed' if v[0]==v[1] else 'reference_interval'} for i,v in enumerate(values)]}
    def exact(v):return [(x,x) for x in v]
    return [
      pop('small_positive',exact(['3/4']*4+['-1/4']*2),'exhaustive'),
      pop('small_negative',exact(['-3/4']*4+['1/4']*2),'exhaustive'),
      pop('small_tie',exact(['1','-1']*3),'exhaustive'),
      pop('small_interval',[('-1/2','1/2')]*6,'exhaustive'),
      pop('large_positive',exact(['1/2']*64),'sampled'),
      pop('large_negative',exact(['-1/2']*64),'sampled'),
      pop('large_tie',exact(['1','-1']*32),'sampled'),
      pop('large_binary_margin',exact(['1']*48+['-1']*16),'sampled'),
      pop('large_interval',[('-1/4','1/4')]*64,'sampled')]
def build(source,area,public):
    area.mkdir(parents=True,exist_ok=False)
    run=source/'runs/trade-01';r=read(run/'RESULTS.json');v=read(run/'VERIFICATION.json')
    assert v['all_assigned_rows_accounted_for'] and v['all_complete_rows_verified']
    assert v['results_sha256']==digest(run/'RESULTS.json') and not r['failures']
    assert r['freeze_sha256']==digest(source/'FREEZE.json')
    assert r['source_admission']['contexts_sha256']==digest(run/'CONTEXTS.json')
    assert r['source_admission']['components_sha256']==digest(run/'COMPONENTS.json')
    ctx=read(run/'CONTEXTS.json');pool=read(run/'COMPONENTS.json')
    assert len(ctx)==64
    populations=authored()
    families=['exact_projection','planar_translation_5_1','one_edit_per_image']
    for family in families:
        units=[]
        for iid,c in sorted(ctx.items()):
            counts=[len(c['image'][role]['value']) for role in ('output_a','output_b')]
            b=sum(counts);bounds=c['families'][family]['unit_bounds']
            assert c['count_difference']==counts[0]-counts[1]
            assert -b<=q(bounds[0])<=q(bounds[1])<=b
            units.append({'id':iid,'bound':str(b),'lower':str(q(bounds[0])),'upper':str(q(bounds[1])),'status':'observed' if bounds[0]==bounds[1] else 'reference_interval'})
        populations.append({'id':'exposed_'+family,'kind':'sampled','units':units})
    inputs={'document_id':'reiyah.adaptive-audit.inputs','version':'0.1.0','populations':populations}
    put(area/'inputs.json',inputs)
    put(public/'authored-inputs.json',{**inputs,'populations':populations[:9]})
    orders={}
    for p in populations:
        active=[i for i,u in enumerate(p['units']) if Fraction(u['bound'])>0]
        if p['kind']=='exhaustive':seq=[list(x) for x in itertools.permutations(active)]
        else:
            seq=[]
            for r in range(128):
                seed=int.from_bytes(hashlib.sha256(f"reiyah.adaptive-audit.v1/{p['id']}/{r}".encode()).digest(),'big')
                path=active.copy();random.Random(seed).shuffle(path);seq.append(path)
        orders[p['id']]=seq
    put(area/'orders.json',orders);put(public/'authored-orders.json',{p['id']:orders[p['id']] for p in populations[:9]})
    bindings=[{'path':str(source/'FREEZE.json'),'sha256':digest(source/'FREEZE.json')}]
    bindings += [{'path':str(run/n),'sha256':digest(run/n)} for n in ['RESULTS.json','VERIFICATION.json','CONTEXTS.json','COMPONENTS.json']]
    put(area/'source-bindings.json',bindings)
    put(public/'input-bindings.json',{'version':'0.1.0','private_inputs_sha256':digest(area/'inputs.json'),'private_orders_sha256':digest(area/'orders.json'),'source_bindings':bindings,'units':{p['id']:len(p['units']) for p in populations},'source_geometry_verification':'exact-bound completed predecessor; not rerun','reserved_outcomes_accessed':0})
    print(json.dumps({'prepared_populations':len(populations),'exhaustive_orders':4*720,'sampled_orders':8*128,'source_bindings':len(bindings),'new_stopping_outcomes_computed':False}))
if __name__=='__main__':build(*map(Path,sys.argv[1:]))
