"""Separate complete-census SQL check; imports no producer or adapter code."""
import argparse,collections,csv,decimal,fractions,hashlib,json,pathlib,re,sqlite3
TASKS=['0back','1back','2back','audiobook listening','auditory gaming','auditory texting','baseline','ebook reading','gaming','texting']
KEYS={'id','driver','task','event','outcome','reaction_ms','event_ms','end_ms','source_sha256','status','issues'}
def pairs_hook(pairs):
 if len(dict(pairs))!=len(pairs):raise ValueError('duplicate_json_key')
 return dict(pairs)
def read(path):
 b=pathlib.Path(path).read_bytes()
 if len(b)>1024*1024:raise ValueError('size')
 return json.loads(b,object_pairs_hook=pairs_hook,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite')))
def check(data,result,raw_root=None):
 if set(result)!={'artifact_id','version','primary_status','coverage','overall','primary','by_task','by_event','by_task_event','by_driver_event','discordant_witnesses','claims'} or result['artifact_id']!='reiyah.takeover-outcome.result' or result['version']!='0.1.0':raise ValueError('result_identity')
 if set(data)!= {'artifact_id','version','source_doi','license','records'}:raise ValueError('document')
 if [data[k] for k in ('artifact_id','version','source_doi','license')]!=['reiyah.takeover-outcome.records','0.1.0','10.5281/zenodo.14185964','CC-BY-4.0']:raise ValueError('identity')
 records=data['records'];expected={f'D{i:02}/'+task for i in range(1,51) for task in TASKS}
 if len(records)!=500 or {r['id'] for r in records}!=expected:raise ValueError('coverage')
 valid=[];statuses=collections.Counter();raw_checked=0
 for r in records:
  if set(r)!=KEYS or r['id']!=r['driver']+'/'+r['task']:raise ValueError('record_shape')
  if r['status'] not in ['valid','invalid','missing'] or not isinstance(r['issues'],list):raise ValueError('status')
  statuses[r['status']]+=1
  if r['source_sha256'] is not None and not re.fullmatch('[0-9a-f]{64}',r['source_sha256']):raise ValueError('digest')
  if r['status']=='valid':
   if r['issues'] or r['source_sha256'] is None or r['event'] not in ['F','L','R'] or r['outcome'] not in ['Success','Failure']:raise ValueError('valid_fields')
   ts=[]
   for k in ['reaction_ms','event_ms','end_ms']:
    v=r[k]
    if not isinstance(v,str) or len(v)>40 or re.fullmatch('[0-9]+(?:[.][0-9]+)?',v) is None:raise ValueError('time')
    q=fractions.Fraction(v)
    if q>10000000:raise ValueError('time_range')
    ts.append(q)
   if ts[2]<ts[0]+ts[1]:raise ValueError('time_order')
   valid.append(r)
  else:
   if not r['issues']:raise ValueError('issue_missing')
   if r['status']=='missing' and any(r[k] is not None for k in ['reaction_ms','event_ms','end_ms','event','outcome','source_sha256']):raise ValueError('missing_fields')
  if raw_root is not None:
   path=pathlib.Path(raw_root)/r['driver']/r['task']/'takeoverScenarioInformations.csv'
   if r['status']=='missing':
    if path.exists():raise ValueError('falsely_missing')
    continue
   b=path.read_bytes()
   if hashlib.sha256(b).hexdigest()!=r['source_sha256']:raise ValueError('raw_digest')
   cells=list(csv.reader(b.decode('utf-8-sig').splitlines(),strict=True));raw_checked+=1
   if len(cells)!=2:raise ValueError('raw_rows')
   if r['status']=='valid':
    raw=dict(zip(cells[0],cells[1],strict=True))
    for a,k in [('reactionTime','reaction_ms'),('criticalEventOccurrenceTime','event_ms'),('scenarioEndTime','end_ms')]:
     if raw[a]!=r[k]:raise ValueError('source_value')
    if raw['takeoverResult']!=r['outcome'] or {'front_vehicle':'F','left_pedestrian':'L','right_pedestrian':'R'}[raw['criticalEventType']]!=r['event']:raise ValueError('source_label')
   elif r['id']=='D11/gaming':
    if cells[0][-1]!='' or cells[1][-1]!='1' or len(cells[0])!=20 or len(cells[1])!=20 or r['issues']!=['source_header']:raise ValueError('invalid_witness')
   else:raise ValueError('unchecked_invalid_source')
 db=sqlite3.connect(':memory:')
 db.create_collation('rational',lambda a,b:(fractions.Fraction(a)>fractions.Fraction(b))-(fractions.Fraction(a)<fractions.Fraction(b)))
 db.execute('CREATE TABLE t(id TEXT PRIMARY KEY, driver TEXT, task TEXT, event TEXT, outcome TEXT, reaction TEXT COLLATE rational)')
 db.executemany('INSERT INTO t VALUES(?,?,?,?,?,?)',[(r['id'],r['driver'],r['task'],r['event'],r['outcome'],r['reaction_ms']) for r in valid])
 joined=db.execute("SELECT f.id,s.id,f.driver,f.event,f.reaction,s.reaction,CASE WHEN f.reaction<s.reaction THEN 'discordant' WHEN f.reaction>s.reaction THEN 'concordant' ELSE 'tied' END FROM t f JOIN t s ON f.driver=s.driver AND f.event=s.event WHERE f.outcome='Failure' AND s.outcome='Success' ORDER BY f.id,s.id").fetchall()
 counts=collections.Counter(x[6] for x in joined)
 witness=[{'failure_id':x[0],'success_id':x[1],'event':x[3],'failure_ms':str(fractions.Fraction(x[4])),'success_ms':str(fractions.Fraction(x[5]))} for x in joined if x[6]=='discordant']
 primary={k:counts[k] for k in ['discordant','concordant','tied']}
 primary.update(eligible_pairs=len(joined),drivers_with_eligible_pairs=len({x[2] for x in joined}),drivers_with_discordance=len({x[2] for x in joined if x[6]=='discordant'}),observed_monotone_counterexample=bool(counts['discordant']))
 if result['primary']!=primary or result['discordant_witnesses']!=witness:raise ValueError('pair_or_witness_mismatch')
 def summary(group):
  times=[fractions.Fraction(x['reaction_ms']) for x in group]
  windows=[fractions.Fraction(x['end_ms'])-fractions.Fraction(x['event_ms']) for x in group]
  follow=[w-t for w,t in zip(windows,times)]
  result={'trials':len(group),'success':sum(x['outcome']=='Success' for x in group),'failure':sum(x['outcome']=='Failure' for x in group),'mean_reaction_ms':str(sum(times)/len(times)) if times else None,'nonpositive_followup':sum(x<=0 for x in follow)}
  for k,vals in [('reaction_range_ms',times),('post_initiation_followup_range_ms',follow),('event_to_end_range_ms',windows)]:result[k]=[str(min(vals)),str(max(vals))] if vals else None
  return result
 if result['overall']!=summary(valid):raise ValueError('overall')
 for key,dims,keys in [('by_task',['task'],[(t,) for t in TASKS]),('by_event',['event'],[(e,) for e in ['F','L','R']]),('by_task_event',['task','event'],[(t,e) for t in TASKS for e in ['F','L','R']]),('by_driver_event',['driver','event'],[(f'D{i:02}',e) for i in range(1,51) for e in ['F','L','R']])]:
  if len(result[key])!=len(keys):raise ValueError('stratum_coverage')
  for row,values in zip(result[key],keys):
   target=dict(zip(dims,values));g=[r for r in valid if all(r[k]==v for k,v in target.items())];expected_row={**target,**summary(g)}
   if key=='by_driver_event':
    hits=collections.Counter(x[6] for x in joined if x[2]==target['driver'] and x[3]==target['event'])
    expected_row.update({k:hits[k] for k in ['discordant','concordant','tied']})
   if row!=expected_row:raise ValueError('stratum_value')
 if result['coverage']!={'expected':500,'valid':statuses['valid'],'missing':statuses['missing'],'invalid':statuses['invalid']}:raise ValueError('status_count')
 expected_status='incomplete' if len(valid)!=500 else ('falsified_on_recorded_cohort' if counts['discordant'] else 'not_falsified_on_recorded_cohort')
 if result['primary_status']!=expected_status or result['claims']!={'causal_effect':False,'physical_recovery':False,'population_risk':False,'superiority':False,'work_savings':False}:raise ValueError('claim')
 return {'artifact_id':'reiyah.takeover-outcome.verification','version':'0.1.0','verified':True,'method':'Separately authored SQL self-join with exact rational ordering; full strata and witness comparison','expected_records':500,'valid_records':len(valid),'raw_sources_checked':raw_checked,'pair_rows_checked':len(joined),'discordant_witnesses_checked':len(witness),'strata_checked':193,'independent_scientific_replication':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--records',required=True);p.add_argument('--result',required=True);p.add_argument('--raw-root');p.add_argument('--output',required=True);a=p.parse_args()
 pathlib.Path(a.output).write_text(json.dumps(check(read(a.records),read(a.result),a.raw_root),indent=2)+'\n')
