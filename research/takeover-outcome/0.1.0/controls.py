"""Boundary controls for exact comparisons, explicit missingness and forged results."""
import copy,json,pathlib,tempfile
import analyze,verify
ROOT=pathlib.Path(__file__).parent
base=analyze.load(ROOT/'records.json');result=analyze.analyze(base);checks=[]
def reject_both(name,mutate):
 d=copy.deepcopy(base);mutate(d)
 for label,fn in [('producer',lambda:analyze.analyze(d)),('checker',lambda:verify.check(d,result))]:
  try:fn()
  except (ValueError,KeyError,TypeError):checks.append(name+':'+label)
  else:raise AssertionError(name+':'+label)
reject_both('duplicate_trial',lambda d:d['records'].__setitem__(1,copy.deepcopy(d['records'][0])))
reject_both('omitted_trial',lambda d:d['records'].pop())
reject_both('extra_property',lambda d:d['records'][0].update(hidden=True))
reject_both('unknown_outcome',lambda d:d['records'][0].update(outcome='Normal'))
reject_both('float_timestamp',lambda d:d['records'][0].update(reaction_ms=600.0))
reject_both('nonfinite_time',lambda d:d['records'][0].update(reaction_ms='NaN'))
reject_both('negative_time',lambda d:d['records'][0].update(reaction_ms='-1'))
reject_both('end_before_reaction',lambda d:d['records'][0].update(end_ms='1'))
reject_both('unknown_as_success',lambda d:d['records'][-1].update(status='valid',issues=[],outcome='Success'))
for key,value in [('primary_status','supported'),('artifact_id','forged'),('claims',{**result['claims'],'physical_recovery':True})]:
 r=copy.deepcopy(result);r[key]=value
 try:verify.check(base,r)
 except ValueError:checks.append('forged_'+key)
 else:raise AssertionError(key)
for name,mutate in [('omitted_witness',lambda r:r['discordant_witnesses'].pop()),('false_pair_count',lambda r:r['primary'].update(discordant=0)),('omitted_empty_stratum',lambda r:r['by_driver_event'].pop())]:
 r=copy.deepcopy(result);mutate(r)
 try:verify.check(base,r)
 except ValueError:checks.append(name)
 else:raise AssertionError(name)
# All500 expected opportunities remain, but unavailable answers never become normal/zero.
d=copy.deepcopy(base)
for row in d['records']:
 row.update(status='missing',issues=['authored_missing_control'],event=None,outcome=None,reaction_ms=None,event_ms=None,end_ms=None,source_sha256=None)
r=analyze.analyze(d);verify.check(d,r)
assert r['primary_status']=='incomplete' and r['overall']['mean_reaction_ms'] is None and r['coverage']['missing']==500
checks.append('all_missing_stays_incomplete')
# Values separated far below binary64 precision still produce the correct exact ordering.
for i,(outcome,time) in enumerate([('Success','1.00000000000000000001'),('Success','1.00000000000000000003'),('Failure','1.00000000000000000002'),('Failure','1.00000000000000000001')]):
 d['records'][i].update(status='valid',issues=[],event='F',outcome=outcome,reaction_ms=time,event_ms='0',end_ms='3',source_sha256='0'*64)
r=analyze.analyze(d);verify.check(d,r)
assert [r['primary'][k] for k in ['discordant','concordant','tied']]==[2,1,1]
checks.append('exact_sub_binary64_order_and_ties')
# JSON duplicate fields cannot silently replace the original value.
with tempfile.TemporaryDirectory() as tmp:
 path=pathlib.Path(tmp)/'duplicate.json';path.write_text('{"x":1,"x":2}')
 for label,fn in [('producer',analyze.load),('checker',verify.read)]:
  try:fn(path)
  except ValueError:checks.append('duplicate_json:'+label)
  else:raise AssertionError(label)
print(json.dumps({'artifact_id':'reiyah.takeover-outcome.controls','version':'0.1.0','passed':len(checks),'checks':checks},indent=2))
