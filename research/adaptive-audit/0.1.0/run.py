"""Execute exactly the frozen allocation; all empirical traces remain private."""
from pathlib import Path
from fractions import Fraction as F
import collections,hashlib,json,sys
from methods import Population,ARMS,choose,require
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def put(p,v):Path(p).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def run(freeze_path,area,out):
    packet=Path(__file__).resolve().parent;freeze=read(freeze_path)
    for name,h in freeze['files'].items():require(sha(packet/name)==h,'freeze_'+name)
    for name,h in freeze['private_inputs'].items():require(sha(area/name)==h,'input_'+name)
    for b in read(area/'source-bindings.json'):require(sha(b['path'])==b['sha256'],'source_binding')
    data=read(area/'inputs.json');orders=read(area/'orders.json')
    require(len(data['populations'])==12 and set(orders)=={p['id'] for p in data['populations']},'allocation')
    out.mkdir(parents=True,exist_ok=False);summaries=[];rows=0
    with (out/'paths.jsonl').open('w') as stream:
        for p in data['populations']:
            pop=Population(p);truth=choose(*pop.interval(pop.active));lo,hi=pop.interval(pop.active)
            expected=__import__('math').factorial(pop.n) if p['kind']=='exhaustive' else 128
            require(len(orders[p['id']])==expected,'order_count')
            priority=pop.exact_priority()
            for arm in ARMS:
                allrows=[]
                for r,path in enumerate(orders[p['id']]):
                    row=pop.path(arm,path,r);stream.write(json.dumps(row,sort_keys=True,separators=(',',':'))+'\n');rows+=1;allrows.append(row)
                count=len(allrows)
                false=sum(x['decision'] not in ('unresolved',truth) for x in allrows)
                null_cross=[sum(x['crossed'][k] for x in allrows) if (lo<=0 if k==0 else hi>=0) else 0 for k in range(2)]
                summaries.append({'population':p['id'],'arm':arm,'kind':p['kind'],'orders':count,'original_units':len(p['units']),'active_units':pop.n,'full_mean_interval':[str(lo/len(p['units'])),str(hi/len(p['units']))],'full_decision':truth,'mean_queries':str(F(sum(x['queries'] for x in allrows),count)),'mean_exact_queries':str(F(sum(x['exact_queries'] for x in allrows),count)),'min_queries':min(x['queries'] for x in allrows),'max_queries':max(x['queries'] for x in allrows),'false_decisions':false,'null_crossings':null_cross,'decision_counts':dict(collections.Counter(x['decision'] for x in allrows)),'reason_counts':dict(collections.Counter(x['reason'] for x in allrows)),'priority_exact':priority})
    result={'document_id':'reiyah.adaptive-audit.result','version':'0.1.0','status':'exploratory','freeze_sha256':sha(freeze_path),'paths_sha256':sha(out/'paths.jsonl'),'path_rows':rows,'summaries':summaries,'independent_scientific_replication':False,'reserved_outcomes_accessed':0,'human_seconds':None,'economic_cost':None}
    put(out/'result.json',result);print(json.dumps({'path_rows':rows,'groups':len(summaries),'paths_bytes':(out/'paths.jsonl').stat().st_size}))
if __name__=='__main__':run(*map(Path,sys.argv[1:]))
