"""Recheck retained query histories and every scheduled stopping point."""
from fractions import Fraction
import json
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parent))
from compare import (encoded, sha, put, subject, observation, conventional_bounds,
                     additions, decision, request_for)
from tools.perception_revision import contract, audit_checker, localization_checker


def verify_event(case, spec, event, sequence, seen):
    unsigned = {k:v for k,v in event.items() if k!='evidence_sha256'}
    if sha(encoded(unsigned)) != event['evidence_sha256']:
        raise ValueError('Query event digest mismatch')
    key = (event['anchor'],event['object'])
    if event['sequence'] != sequence or key in seen:
        raise ValueError('Query order or repetition mismatch')
    if event['subject_sha256'] != subject(case,key):
        raise ValueError('Query subject mismatch')
    if event['source_input_sha256'] != spec['input_sha256']:
        raise ValueError('Query source mismatch')
    if event['reference_context_sha256'] != case['reference_context_sha256'] or event['cohort_id'] != case['cohort_id']:
        raise ValueError('Query applicability mismatch')
    if event['answer'] != 'present' or event['basis'] != 'hypothetical':
        raise ValueError('Wrong frozen answer model')
    if event['requested_precision'] != 'exact_presence' or event['residual_uncertainty'] != 'none_within_declared_family':
        raise ValueError('Precision changed')
    if event['cost']['observation_units'] != 1 or event['cost']['human_seconds'] is not None or event['cost']['human_cost'] is not None:
        raise ValueError('Observation/human cost mismatch')
    if event['returned_utc'] < event['requested_utc']:
        raise ValueError('Query returned before request')
    seen.add(key)


def verify_run(area, runs, spec, row):
    data=(area/spec['input']).read_bytes()
    if sha(data)!=spec['input_sha256']:
        raise ValueError('Input changed')
    case=contract.parse(data);contract.validate(case)
    directory=runs/(spec['id']+'--'+row['arm'])
    raw=(directory/'history.jsonl').read_bytes()
    if sha(raw)!=row['history_sha256']:
        raise ValueError('History binding mismatch')
    history=[json.loads(line) for line in raw.splitlines()]
    if len(history)!=row['queries']:
        raise ValueError('Omitted incurred queries')
    if spec['family']!='deletion':
        geometry=json.loads((area/spec['geometry']).read_bytes())
        intervals=[]
        for method in ('ordinary','shared_linear'):
            payload=json.loads((directory/(method+'.json')).read_bytes())
            result=localization_checker.check(case,geometry,payload)
            intervals.append(tuple(contract.rational(result['bounds'][k]) for k in ('lower','upper')))
        bounds=(max(v[0] for v in intervals),min(v[1] for v in intervals))
        assert row['final_bounds']==[str(v) for v in bounds]
        assert row['queries']==0
        status=decision(bounds,contract.rational(case['loss']['tolerance']))
        assert row['status']==(status if status!='unresolved' else 'zero_query_control_unresolved')
        return {'queries':0,'stopping_points':1,'proofs':2,'conventional_native_agreements':0}
    seen=set()
    for seq,event in enumerate(history,1):verify_event(case,spec,event,seq,seen)
    checks=sorted(directory.glob('check-*.json'))
    previous=-1;proofs=0;agreements=0;last=None
    for i,path in enumerate(checks):
        check=json.loads(path.read_bytes());q=check['after_queries']
        assert previous < q <= len(history) and (i!=0 or q==0)
        req=request_for(case,[observation(event) for event in history[:q]])
        assert req==check['request'] and sha(encoded(req))==check['request_sha256']
        contract.validate_request(case,req)
        intervals=[]
        for entry in check['proofs']:
            result=audit_checker.check(case,req,entry['payload']);proofs+=1
            if result.get('bounds') is not None:
                intervals.append(tuple(contract.rational(result['bounds'][k]) for k in ('lower','upper')))
        if additions(case):
            conventional=conventional_bounds(case,req)
            assert conventional is not None
            if intervals:
                assert (max(v[0] for v in intervals),min(v[1] for v in intervals))==conventional
                agreements+=1
            bounds=conventional
        else:
            bounds=(max(v[0] for v in intervals),min(v[1] for v in intervals)) if intervals else None
        assert check['bounds']==(None if bounds is None else [str(v) for v in bounds])
        status=decision(bounds,contract.rational(case['loss']['tolerance']))
        assert status==check['decision']
        if i<len(checks)-1:assert status=='unresolved','Queries continued after a decision'
        previous=q;last=check
    assert previous==len(history)
    assert len(checks)==row['stopping_calls']
    assert last['bounds']==row['final_bounds']
    if row['status'] in ('supported','excluded'):assert last['decision']==row['status']
    else:assert last['decision']=='unresolved'
    return {'queries':len(history),'stopping_points':len(checks),'proofs':proofs,
            'conventional_native_agreements':agreements}


def main():
    area,runs=map(Path,sys.argv[1:3]);start=time.perf_counter()
    plan_bytes=(area/'PLAN.json').read_bytes();plan=json.loads(plan_bytes)
    result_bytes=(runs/'RESULTS.json').read_bytes();results=json.loads(result_bytes)
    assert results['plan_sha256']==sha(plan_bytes) and results['complete']
    arms=plan['arms']
    if 'amendment_sha256' in results:
        amendment_bytes=(area/'INTERACTION_PLAN.json').read_bytes()
        assert sha(amendment_bytes)==results['amendment_sha256']
        amendment=json.loads(amendment_bytes)
        assert amendment['base_plan_sha256']==sha(plan_bytes)
        arms=amendment['arms']
    assigned={(s['id'],a) for s in plan['cases'] for a in arms}
    actual=[(r['case'],r['arm']) for r in results['rows']]
    assert len(actual)==len(set(actual)) and set(actual)==assigned
    specs={s['id']:s for s in plan['cases']};counts=[]
    for row in results['rows']:
        counts.append(verify_run(area,runs,specs[row['case']],row))
    report={'result_sha256':sha(result_bytes),'plan_sha256':sha(plan_bytes),
            'replay_source_sha256':sha(Path(__file__).read_bytes()),'rows':len(counts),
            **{k:sum(c[k] for c in counts) for k in counts[0]},
            'seconds':time.perf_counter()-start,'status':'pass',
            'scope':'Current development histories and scheduled stopping points, not physical answer validation or independent scientific replication'}
    put(runs/'REPLAY.json',report)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
