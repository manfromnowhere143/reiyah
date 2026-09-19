"""Separate algebra and source checker, v0.1.0; imports no producer."""
from pathlib import Path
from fractions import Fraction as Q
from math import factorial,isqrt
import collections,hashlib,itertools,json,random,sys

ARMS=('fixed_half','alpha_d10','alpha_d100')
class VerificationError(ValueError):pass
def need(c,reason):
    if not c:raise VerificationError(reason)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def text(x):return 'null_impossible' if x is None else str(x)
def sign(lo,hi):return 'supported' if lo>0 else 'excluded' if hi<=0 else 'unresolved'
def number(s):
    need(type(s) is str,'rational_string')
    try:v=Q(s)
    except (ValueError,ZeroDivisionError):raise VerificationError('rational_value')
    need(str(v)==s,'rational_canonical');return v

class Reference:
    def __init__(self,p):
        need(set(p)=={'id','kind','units'} and p['kind'] in ('sampled','exhaustive'),'population_properties')
        need(type(p['id']) is str and bool(p['id']),'population_identity')
        need(type(p['units']) is list and 0<len(p['units'])<=64,'population_size')
        ids=[];self.bounds=[];self.ends=[]
        for u in p['units']:
            need(set(u)=={'id','bound','lower','upper','status'},'unit_properties')
            need(type(u['id']) is str and u['id'] and u['id'] not in ids,'unit_identity');ids.append(u['id'])
            b,l,h=map(number,(u['bound'],u['lower'],u['upper']))
            need(b>=0 and -b<=l<=h<=b,'unit_range')
            need(u['status'] in ('observed','reference_interval','missing','unmeasured','out_of_distribution','sensor_invalid','abstained'),'unit_status')
            if u['status']=='observed':need(l==h,'observed_interval')
            if u['status'] not in ('observed','reference_interval'):need(l==-b and h==b,'unavailable_interval')
            self.bounds.append(b);self.ends.append((l,h))
        self.p=p;self.active=[i for i,b in enumerate(self.bounds) if b];self.n=len(self.active)
        scale=max(self.bounds);self.x=([(l+scale)/(2*scale) for l,h in self.ends],[(scale-h)/(2*scale) for l,h in self.ends]) if scale else ([],[])
        self.totals=[sum((direction[i] for i in self.active),Q(0)) for direction in self.x]
        self.full=[sum((e[k] for e in self.ends),Q(0)) for k in (0,1)]
        self.truth=sign(*self.full);self.support_checks=0;self.drift_checks=0
    def reference_step(self,arm,t,S,e,x,direction):
        m=(Q(self.n,2)-S)/(self.n-t)
        null=self.totals[direction]<=Q(self.n,2)
        actual=(self.totals[direction]-S)/(self.n-t)
        if null:need(actual<=m,'null_mean');self.drift_checks+=1
        if m<0:
            need(not null,'null_impossible_under_null');return None
        if m==0:
            if null:need(actual==0,'zero_null_mean')
            return None if e is None or x>0 else e
        if m>=1:return e
        if arm=='fixed_half':
            eta=m+(1-m)/2
        else:
            d={'alpha_d10':10,'alpha_d100':100}[arm]
            root=isqrt((2**48)//(d+t))
            # Check the exact downward sqrt bound independently.
            need(root*root*(d+t)<=2**48<(root+1)**2*(d+t),'epsilon_rounding')
            eps=Q(root,8*2**24)
            eta=min(Q(1),max((Q(3,4)*d+S)/(d+t),m+eps))
        need(m<=eta<=1,'alternative_range')
        f0=(1-eta)/(1-m);f1=eta/m
        need(f0>=0 and f1>=f0,'factor_support');self.support_checks+=2
        if null:need(actual*f1+(1-actual)*f0<=1,'null_drift')
        factor=x*f1+(1-x)*f0
        return None if e is None else e*factor
    def expected(self,arm,order,rep):
        need(arm in ARMS,'unknown_arm')
        need(len(order)==self.n and all(type(i) is int for i in order) and len(set(order))==self.n and set(order)==set(self.active),'order_membership')
        seen_sum=[Q(0),Q(0)];e=[Q(1),Q(1)];ever=[False,False]
        lo=-sum(self.bounds);hi=sum(self.bounds);first=None;exact=None;h=hashlib.sha256()
        for t in range(self.n+1):
            vals=list(map(text,e))
            h.update((json.dumps([t,str(lo),str(hi),*vals],separators=(',',':'))+'\n').encode())
            state=sign(lo,hi);c=[v is None or v>=40 for v in e]
            ever=[v or w for v,w in zip(ever,c)]
            if exact is None and (state!='unresolved' or t==self.n):exact=(t,state)
            if first is None:
                if state!='unresolved':first=(t,state,'logical',vals)
                elif t==self.n:first=(t,'unresolved','residual_reference',vals)
                elif c==[True,True]:first=(t,'unresolved','statistical_conflict',vals)
                elif c[0]:first=(t,'supported','statistical',vals)
                elif c[1]:first=(t,'excluded','statistical',vals)
            if t<self.n:
                i=order[t]
                for k in (0,1):
                    x=self.x[k][i]
                    e[k]=self.reference_step(arm,t,seen_sum[k],e[k],x,k);seen_sum[k]+=x
                lo+=self.ends[i][0]+self.bounds[i];hi+=self.ends[i][1]-self.bounds[i]
        return {'population':self.p['id'],'arm':arm,'replicate':rep,'queries':first[0],'decision':first[1],'reason':first[2],'wealth_at_stop':first[3],'exact_queries':exact[0],'exact_decision':exact[1],'crossed':ever,'trace_sha256':h.hexdigest()}
    def verify_row(self,row,order):
        expected=self.expected(row['arm'],order,row['replicate'])
        need(set(row)==set(expected),'path_properties')
        for key,value in expected.items():need(row[key]==value,'path_'+key)
    def priority(self):
        order=sorted(self.active,key=lambda i:(-self.bounds[i],self.p['units'][i]['id']))
        lo=-sum(self.bounds);hi=sum(self.bounds)
        for t in range(self.n+1):
            state=sign(lo,hi)
            if state!='unresolved' or t==self.n:return {'queries':t,'decision':state}
            i=order[t];lo+=self.ends[i][0]+self.bounds[i];hi+=self.ends[i][1]-self.bounds[i]

def verify_sources(area,populations):
    bindings=read(area/'source-bindings.json')
    need(len(bindings)==5,'source_binding_count')
    for b in bindings:need(sha(b['path'])==b['sha256'],'source_binding')
    byname={Path(b['path']).name:Path(b['path']) for b in bindings}
    r=read(byname['RESULTS.json']);v=read(byname['VERIFICATION.json'])
    need(v['results_sha256']==sha(byname['RESULTS.json']) and v['all_complete_rows_verified'] and v['all_assigned_rows_accounted_for'],'parent_verification')
    need(r['freeze_sha256']==sha(byname['FREEZE.json']),'parent_freeze')
    ctx=read(byname['CONTEXTS.json']);pool=read(byname['COMPONENTS.json'])
    need(len(ctx)==64 and r['source_admission']['contexts_sha256']==sha(byname['CONTEXTS.json']) and r['source_admission']['components_sha256']==sha(byname['COMPONENTS.json']),'parent_components')
    def priorq(v):return Q(int(v['numerator']),int(v['denominator']))
    checked=0
    for family in ('exact_projection','planar_translation_5_1','one_edit_per_image'):
        p=populations['exposed_'+family];need([u['id'] for u in p['units']]==sorted(ctx),'source_membership')
        for u in p['units']:
            c=ctx[u['id']];counts=[len(c['image'][key]['value']) for key in ('output_a','output_b')]
            need(Q(u['bound'])==sum(counts),'source_bound')
            f=c['families'][family]
            for k,key in enumerate(f['worlds']):
                component=pool[key];ranks=component['measurement']['ranks']
                need(component['image_id']==u['id'] and component['prediction_counts']==counts,'source_identity')
                delta=counts[0]-counts[1]+2*(ranks[1]-ranks[0])
                need(Q(u['lower' if k==0 else 'upper'])==delta==priorq(f['unit_bounds'][k])==priorq(component['measurement']['delta']),'source_endpoint')
                checked+=1
    return checked

def verify(freeze_path,area,run,out):
    packet=Path(__file__).resolve().parent;freeze=read(freeze_path)
    for name,value in freeze['files'].items():need(sha(packet/name)==value,'freeze_'+name)
    for name,value in freeze['private_inputs'].items():need(sha(area/name)==value,'input_'+name)
    data=read(area/'inputs.json');pops={p['id']:p for p in data['populations']}
    need(len(pops)==len(data['populations'])==12,'allocation')
    need(read(packet/'authored-inputs.json')['populations']==data['populations'][:9],'authored_input_binding')
    source_checks=verify_sources(area,pops);orders=read(area/'orders.json')
    need(set(orders)==set(pops),'order_allocation')
    need({k:orders[k] for k in list(pops)[:9]}==read(packet/'authored-orders.json'),'authored_orders')
    refs={k:Reference(p) for k,p in pops.items()}
    for pid,ref in refs.items():
        seq=orders[pid]
        if ref.p['kind']=='exhaustive':expected=[list(x) for x in itertools.permutations(ref.active)]
        else:
            expected=[]
            for r in range(128):
                seed=int.from_bytes(hashlib.sha256(f'reiyah.adaptive-audit.v1/{pid}/{r}'.encode()).digest(),'big')
                x=ref.active.copy();random.Random(seed).shuffle(x);expected.append(x)
        need(seq==expected,'frozen_order_generation')
    result=read(run/'result.json');need(result['freeze_sha256']==sha(freeze_path),'run_freeze')
    need(result['paths_sha256']==sha(run/'paths.jsonl'),'run_paths')
    seen=set();groups={};rows=0
    with (run/'paths.jsonl').open() as stream:
        for line in stream:
            row=json.loads(line);pid=row['population'];arm=row['arm'];r=row['replicate'];key=(pid,arm,r)
            need(pid in refs and arm in ARMS and type(r) is int and 0<=r<len(orders[pid]),'path_allocation')
            need(key not in seen,'duplicate_path');seen.add(key);refs[pid].verify_row(row,orders[pid][r]);rows+=1
            groups.setdefault((pid,arm),[]).append(row)
    need(rows==11712==result['path_rows'] and len(groups)==36,'complete_allocation')
    summary=[]
    for p in data['populations']:
        pid=p['id'];ref=refs[pid];lo,hi=ref.full
        for arm in ARMS:
            g=groups[(pid,arm)];n=len(g);need(n==len(orders[pid]),'complete_group')
            false=sum(x['decision']!='unresolved' and x['decision']!=ref.truth for x in g)
            null_cross=[sum(x['crossed'][k] for x in g) if (lo<=0 if k==0 else hi>=0) else 0 for k in (0,1)]
            if p['kind']=='exhaustive':
                need(n==factorial(ref.n),'exhaustive_mass')
                need(Q(false,n)<=Q(1,20),'false_decision_bound')
                need(all(Q(count,n)<=Q(1,40) for count in null_cross),'directional_error_bound')
            summary.append({'population':pid,'arm':arm,'kind':p['kind'],'orders':n,'original_units':len(p['units']),'active_units':ref.n,'full_mean_interval':[str(lo/len(p['units'])),str(hi/len(p['units']))],'full_decision':ref.truth,'mean_queries':str(Q(sum(x['queries'] for x in g),n)),'mean_exact_queries':str(Q(sum(x['exact_queries'] for x in g),n)),'min_queries':min(x['queries'] for x in g),'max_queries':max(x['queries'] for x in g),'false_decisions':false,'null_crossings':null_cross,'decision_counts':dict(collections.Counter(x['decision'] for x in g)),'reason_counts':dict(collections.Counter(x['reason'] for x in g)),'priority_exact':ref.priority()})
    need(summary==result['summaries'],'result_summary')
    report={'document_id':'reiyah.adaptive-audit.verification','version':'0.1.0','passed':True,'checked_paths':rows,'checked_groups':len(groups),'source_endpoints_bound':source_checks,'factor_support_checks':sum(r.support_checks for r in refs.values()),'null_drift_checks':sum(r.drift_checks for r in refs.values()),'paths_sha256':sha(run/'paths.jsonl'),'result_sha256':sha(run/'result.json'),'freeze_sha256':sha(freeze_path),'large_sample_coverage_established':False,'parent_geometry_proofs_replayed':False,'independent_scientific_replication':False}
    Path(out).write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':verify(*map(Path,sys.argv[1:]))
