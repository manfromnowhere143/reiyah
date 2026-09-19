"""Exhaustive order producer; research version 0.1.0."""
from pathlib import Path
from fractions import Fraction as F
import csv
import hashlib
import json
import sys
import time
from methods import ARMS, logical, walk

def main():
    freeze_path, dest = map(Path, sys.argv[1:])
    freeze = json.loads(freeze_path.read_text())
    root = Path(__file__).resolve().parent
    for name, expected in freeze['files'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != expected:
            raise ValueError('freeze_digest_mismatch:'+name)
    fixtures = json.loads((root/'fixtures.json').read_text())
    assert len(fixtures['populations']) == 28
    dest.mkdir(parents=True, exist_ok=False)
    rows=0; summaries=[]; times=[]
    fields=('population','arm','order','probability','exact_stop','exact_decision','stat_stop','stat_decision',
            'stat_reason','e_lower_at_stop','e_upper_at_stop','lower_ever_crossed','upper_ever_crossed')
    with (dest/'paths.csv').open('w', newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=fields,lineterminator='\n');writer.writeheader()
        for pop in fixtures['populations']:
            allocated={'population':pop['id'],'state':'running'}
            (dest/'CURRENT.json').write_text(json.dumps(allocated)+'\n')
            truth, lo, hi=logical(pop,set(range(len(pop['units']))))
            for arm in ARMS:
                start=time.perf_counter();count=0;mass=F(0);es=F(0);ss=F(0);error=F(0);early=F(0);stat=F(0)
                for row in walk(pop,arm):
                    writer.writerow(row);rows+=1;count+=1;p=F(row['probability']);mass+=p
                    es+=p*int(row['exact_stop']);ss+=p*int(row['stat_stop'])
                    if row['stat_decision']!='unresolved' and row['stat_decision']!=truth:error+=p
                    if int(row['stat_stop'])<int(row['exact_stop']):early+=p
                    if row['stat_reason']=='statistical':stat+=p
                assert mass==1
                summaries.append({'population':pop['id'],'arm':arm,'orders':count,'full_interval':[str(lo),str(hi)],
                                  'full_decision':truth,'expected_exact_queries':str(es),'expected_stat_queries':str(ss),
                                  'false_decision_probability':str(error),'early_stop_probability':str(early),
                                  'statistical_decision_probability':str(stat)})
                times.append({'population':pop['id'],'arm':arm,'enumeration_seconds':time.perf_counter()-start,'orders':count})
    result={'document_id':'reiyah.sequential-audit.result','version':'0.1.0','status':'exploratory',
            'freeze_sha256':hashlib.sha256(freeze_path.read_bytes()).hexdigest(), 'path_rows':rows,
            'paths_sha256':hashlib.sha256((dest/'paths.csv').read_bytes()).hexdigest(), 'summaries':summaries,
            'all_allocated_populations_retained':True, 'empirical_or_customer_evidence':False}
    (dest/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    (dest/'timing.json').write_text(json.dumps(times,indent=2)+'\n')
    (dest/'CURRENT.json').write_text(json.dumps({'state':'complete','path_rows':rows})+'\n')
    print(json.dumps({'populations':28,'arms':len(ARMS),'path_rows':rows,'completed':True}))

if __name__=='__main__':main()
