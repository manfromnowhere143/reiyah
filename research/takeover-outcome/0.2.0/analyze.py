"""Finite recorded-outcome audit. Standard library, no trained or fitted model."""
import argparse,bisect,collections,copy,fractions,hashlib,json,pathlib,re
TASKS=('0back','1back','2back','audiobook listening','auditory gaming','auditory texting','baseline','ebook reading','gaming','texting')
FIELDS={'id','driver','task','event','outcome','reaction_ms','event_ms','end_ms','source_sha256','status','issues'}
def unique(pairs):
 d={}
 for k,v in pairs:
  if k in d:raise ValueError('duplicate_json_key')
  d[k]=v
 return d
def load(path):
 raw=pathlib.Path(path).read_bytes()
 if len(raw)>1024*1024:raise ValueError('input_size')
 return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite_json')))
def validate(data):
 if not isinstance(data,dict) or set(data)!={'artifact_id','version','source_doi','license','records'}:raise ValueError('document_fields')
 if (data['artifact_id'],data['version'],data['source_doi'],data['license'])!=('reiyah.takeover-outcome.records','0.2.0','10.5281/zenodo.14185964','CC-BY-4.0'):raise ValueError('document_identity')
 rows=copy.deepcopy(data['records']);expected={(f'D{i:02}',t) for i in range(1,51) for t in TASKS};seen=set()
 if not isinstance(rows,list) or len(rows)!=500:raise ValueError('coverage')
 for r in rows:
  if not isinstance(r,dict) or set(r)!=FIELDS:raise ValueError('record_fields')
  if type(r['driver']) is not str or type(r['task']) is not str:raise ValueError('record_identity')
  key=(r['driver'],r['task'])
  if key not in expected or key in seen or r['id']!='/'.join(key):raise ValueError('record_identity')
  seen.add(key)
  if r['status'] not in ('valid','invalid','missing'):raise ValueError('record_status')
  if not isinstance(r['issues'],list) or any(type(s) is not str or not s for s in r['issues']):raise ValueError('record_issues')
  h=r['source_sha256']
  if h is not None and (type(h) is not str or len(h)!=64 or any(c not in '0123456789abcdef' for c in h)):raise ValueError('source_digest')
  if r['status']!='valid':
   if not r['issues']:raise ValueError('missing_issue')
   if r['status']=='missing' and any(r[k] is not None for k in ('event','outcome','reaction_ms','event_ms','end_ms','source_sha256')):raise ValueError('missing_state')
   continue
  if r['issues'] or h is None:raise ValueError('valid_evidence')
  if r['event'] not in ('F','L','R') or r['outcome'] not in ('Success','Failure'):raise ValueError('event_or_outcome')
  for k in ('reaction_ms','event_ms','end_ms'):
   if type(r[k]) is not str or len(r[k])>40 or not re.fullmatch(r'[0-9]+(?:\.[0-9]+)?',r[k]):raise ValueError('decimal_time')
   r[k]=fractions.Fraction(r[k])
   if r[k]>10000000:raise ValueError('decimal_time')
  if r['end_ms']<r['event_ms']+r['reaction_ms']:raise ValueError('time_order')
 return rows

def summarize(rows):
 n=len(rows);reaction=[r['reaction_ms'] for r in rows]
 follow=[r['end_ms']-r['event_ms']-r['reaction_ms'] for r in rows]
 window=[r['end_ms']-r['event_ms'] for r in rows]
 return {'trials':n,'success':sum(r['outcome']=='Success' for r in rows),'failure':sum(r['outcome']=='Failure' for r in rows),'mean_reaction_ms':str(fractions.Fraction(sum(reaction),n)) if n else None,'reaction_range_ms':[min(reaction),max(reaction)] if n else None,'post_initiation_followup_range_ms':[min(follow),max(follow)] if n else None,'nonpositive_followup':sum(x<=0 for x in follow),'event_to_end_range_ms':[min(window),max(window)] if n else None}

def analyze(data):
 rows=validate(data);valid=[r for r in rows if r['status']=='valid'];groups=collections.defaultdict(list)
 for r in valid:groups[(r['driver'],r['event'])].append(r)
 strata=[];witnesses=[];totals={'discordant':0,'concordant':0,'tied':0};eligible_drivers=set();discordant_drivers=set()
 for i in range(1,51):
  for event in ('F','L','R'):
   driver=f'D{i:02}';g=groups[(driver,event)]
   success=sorted(r['reaction_ms'] for r in g if r['outcome']=='Success')
   failure=[r for r in g if r['outcome']=='Failure']
   d=sum(len(success)-bisect.bisect_right(success,r['reaction_ms']) for r in failure)
   c=sum(bisect.bisect_left(success,r['reaction_ms']) for r in failure)
   t=len(success)*len(failure)-d-c
   if d+c+t:eligible_drivers.add(driver)
   if d:discordant_drivers.add(driver)
   for k,v in [('discordant',d),('concordant',c),('tied',t)]:totals[k]+=v
   strata.append({'driver':driver,'event':event,**summarize(g),'discordant':d,'concordant':c,'tied':t})
   for f in failure:
    for s in g:
     if s['outcome']=='Success' and f['reaction_ms']<s['reaction_ms']:
      witnesses.append({'failure_id':f['id'],'success_id':s['id'],'event':event,'failure_ms':f['reaction_ms'],'success_ms':s['reaction_ms']})
 witnesses.sort(key=lambda w:(w['failure_id'],w['success_id']))
 status='incomplete' if len(valid)!=500 else ('falsified_on_recorded_cohort' if totals['discordant'] else 'not_falsified_on_recorded_cohort')
 result={'artifact_id':'reiyah.takeover-outcome.result','version':'0.2.0','primary_status':status,'coverage':{'expected':500,'valid':len(valid),'missing':sum(r['status']=='missing' for r in rows),'invalid':sum(r['status']=='invalid' for r in rows)},'overall':summarize(valid),'primary':{**totals,'eligible_pairs':sum(totals.values()),'drivers_with_eligible_pairs':len(eligible_drivers),'drivers_with_discordance':len(discordant_drivers),'observed_monotone_counterexample':bool(totals['discordant'])},'by_task':[{'task':t,**summarize([r for r in valid if r['task']==t])} for t in TASKS],'by_event':[{'event':e,**summarize([r for r in valid if r['event']==e])} for e in ('F','L','R')],'by_task_event':[{'task':t,'event':e,**summarize([r for r in valid if r['task']==t and r['event']==e])} for t in TASKS for e in ('F','L','R')],'by_driver_event':strata,'discordant_witnesses':witnesses,'claims':{'causal_effect':False,'physical_recovery':False,'population_risk':False,'superiority':False,'work_savings':False}}
 return json.loads(json.dumps(result,default=lambda value:str(value) if isinstance(value,fractions.Fraction) else value))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--records',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 pathlib.Path(a.output).write_text(json.dumps(analyze(load(a.records)),indent=2)+'\n')
