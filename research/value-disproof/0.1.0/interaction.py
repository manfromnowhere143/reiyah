"""Fourth arm: candidate selector with conventional stopping, same frozen cases."""
import json
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parent))
import compare


def main():
    area,destination=(Path(v).resolve() for v in sys.argv[1:3])
    plan_bytes=(area/'PLAN.json').read_bytes();plan=json.loads(plan_bytes)
    amendment_bytes=(area/'INTERACTION_PLAN.json').read_bytes();amendment=json.loads(amendment_bytes)
    assert amendment['base_plan_sha256']==compare.sha(plan_bytes)
    assert amendment['driver_sha256']==compare.sha(Path(__file__).read_bytes())
    assert amendment['comparison_driver_sha256']==compare.sha(Path(compare.__file__).read_bytes())
    original_selector=compare.Selector
    compare.Selector=lambda case,arm,sources: original_selector(case,'C',sources)
    destination.mkdir();rows=[];start=time.perf_counter()
    for spec in plan['cases']:
        data=(area/spec['input']).read_bytes();assert compare.sha(data)==spec['input_sha256']
        case=compare.contract.parse(data);compare.contract.validate(case)
        outdir=destination/(spec['id']+'--D');outdir.mkdir()
        if spec['family']=='deletion':
            row=compare.run_deletion(spec,case,'A',area,outdir,plan)
        else:
            row=compare.run_position(spec,case,'A',area,outdir)
        row['arm']='D';rows.append(row)
        print(json.dumps({k:row[k] for k in ('case','arm','status','queries','wall_seconds')}),flush=True)
    compare.put(destination/'RESULTS.json',{'artifact_id':'reiyah.value-disproof.interaction',
        'version':'0.1.0','plan_sha256':compare.sha(plan_bytes),
        'amendment_sha256':compare.sha(amendment_bytes),'complete':len(rows)==len(plan['cases']),
        'rows':rows,'campaign_seconds':time.perf_counter()-start,'human_costs':'unmeasured',
        'outcome_reserved_accessed':False})


if __name__=='__main__':main()
