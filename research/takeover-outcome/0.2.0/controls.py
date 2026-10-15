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
reject_both('unknown_as_success',lambda d:d['records'][-1].update(status='valid',issues=[],outcome='Success',event=None,reaction_ms=None,source_sha256=None))
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
# Additional essential-field and timing controls.
import prepare_records,timing,csv,io
header=prepare_records.PREFIX+prepare_records.SUFFIX
values=['right_pedestrian','1000','5000','Success','600']+['0']*14
def encoded(h,v):
 stream=io.StringIO();writer=csv.writer(stream);writer.writerow(h);writer.writerow(v);return stream.getvalue().encode()
original,details=prepare_records.parse(encoded(header,values))
projected,details=prepare_records.parse(encoded(header+[''],values+['1']))
assert projected==original and not details['full_header_matches'] and not details['workload_suffix_consumed']
checks.append('irrelevant_suffix_does_not_change_required_fields')
for name,h,v in [('required_duplicate',header+['reactionTime'],values+['1']),('missing_required',header[1:],values[1:]),('unequal_width',header,values+['1']),('empty_outcome',header,values[:3]+['']+values[4:]),('nonfinite_source_time',header,values[:4]+['NaN']+values[5:]),('negative_source_time',header,values[:4]+['-1']+values[5:])]:
 try:prepare_records.parse(encoded(h,v))
 except ValueError:checks.append(name)
 else:raise AssertionError(name)
t=timing.audit(base);timing.check(base,t)
for name,mutate in [('scenario_end_as_outcome',lambda x:x['timelines'][0].update(outcome_event_ms=x['timelines'][0]['scenario_end_ms'])),('fabricated_common_horizon',lambda x:x['qualification'].update(shared_recovery_horizon='qualified')),('admitted_model',lambda x:x['qualification'].update(readiness_model_admitted=True))]:
 bad=copy.deepcopy(t);mutate(bad)
 try:timing.check(base,bad)
 except ValueError:checks.append(name)
 else:raise AssertionError(name)
example=json.load(open(ROOT/'timing-counterexample.json'));summary=example['shared_summary']
for world in example['unobserved_completions']:
 assert summary['event_ms']<=world['failure_event_ms']<=summary['end_ms']
 assert world['failure_after_first_action']==(world['failure_event_ms']>summary['event_ms']+summary['reaction_ms'])
assert len({w['failure_after_first_action'] for w in example['unobserved_completions']})==2
checks.append('unidentified_failure_order_witness')
print(json.dumps({'artifact_id':'reiyah.takeover-outcome.controls','version':'0.2.0','passed':len(checks),'checks':checks},indent=2))
