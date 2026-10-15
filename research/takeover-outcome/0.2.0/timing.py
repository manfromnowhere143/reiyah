"""Exact arithmetic on recorded timestamps; no inferred outcome-event time."""
import argparse,fractions,json,pathlib,statistics
import analyze
F=fractions.Fraction

def audit(data):
 rows=analyze.validate(data);timelines=[]
 for r in rows:
  if r['status']!='valid':continue
  event=r['event_ms'];first=event+r['reaction_ms'];end=r['end_ms']
  timelines.append({'id':r['id'],'event_type':r['event'],'recorded_outcome':r['outcome'],'critical_event_ms':str(event),'first_action_ms_derived':str(first),'scenario_end_ms':str(end),'event_to_end_ms':str(end-event),'post_action_to_end_ms':str(end-first),'outcome_event_ms':None,'outcome_event_time_status':'not_recorded_in_summary','censoring_status':'not_qualified'})
 def ranges(items):
  result={'records':len(items)}
  for key in ['event_to_end_ms','post_action_to_end_ms']:
   values=[F(x[key]) for x in items]
   result[key]={'min':str(min(values)),'median':str(statistics.median(values)),'max':str(max(values)),'nonpositive':sum(x<=0 for x in values)} if values else None
  return result
 return {'artifact_id':'reiyah.takeover-outcome.timing','version':'0.2.0','arithmetic_coverage':{'expected':500,'usable':len(timelines),'unavailable':500-len(timelines)},'overall':ranges(timelines),'by_event_outcome':[{'event':e,'outcome':o,**ranges([r for r in timelines if r['event_type']==e and r['recorded_outcome']==o])} for e in ['F','L','R'] for o in ['Success','Failure']],'timelines':timelines,'qualification':{'recorded_timestamp_arithmetic':'supported_on_valid_rows','actual_failure_event_time':'not_recorded_in_summary','censoring_and_monitoring_interval':'not_qualified','shared_recovery_horizon':'not_qualified','release_bound_capture_runtime':'not_established','first_action_available_before_critical_event':False,'readiness_model_admitted':False,'Gate_A_operator_accepted':False}}

def check(data,result):
 # Independently reconstruct exact derived quantities through Decimal operands.
 import decimal
 decimal.getcontext().prec=100
 if result['artifact_id']!='reiyah.takeover-outcome.timing' or result['version']!='0.2.0':raise ValueError('timing_identity')
 valid=[r for r in data['records'] if r['status']=='valid'];seen=set()
 if len(result['timelines'])!=len(valid):raise ValueError('timing_coverage')
 byid={r['id']:r for r in valid}
 for t in result['timelines']:
  if t['id'] not in byid or t['id'] in seen:raise ValueError('timing_membership')
  seen.add(t['id']);r=byid[t['id']];d=decimal.Decimal
  event=d(r['event_ms']);first=event+d(r['reaction_ms']);end=d(r['end_ms'])
  expected={'critical_event_ms':event,'first_action_ms_derived':first,'scenario_end_ms':end,'event_to_end_ms':end-event,'post_action_to_end_ms':end-first}
  for k,v in expected.items():
   if F(t[k])!=F(v):raise ValueError('timing_value')
  if t['event_type']!=r['event'] or t['recorded_outcome']!=r['outcome'] or t['outcome_event_ms'] is not None or t['outcome_event_time_status']!='not_recorded_in_summary' or t['censoring_status']!='not_qualified':raise ValueError('invented_outcome_time')
 q=result['qualification']
 if q!={'recorded_timestamp_arithmetic':'supported_on_valid_rows','actual_failure_event_time':'not_recorded_in_summary','censoring_and_monitoring_interval':'not_qualified','shared_recovery_horizon':'not_qualified','release_bound_capture_runtime':'not_established','first_action_available_before_critical_event':False,'readiness_model_admitted':False,'Gate_A_operator_accepted':False}:raise ValueError('false_timing_qualification')
 # Full report identity (including all group summaries) is also checked on replay.
 if result!=audit(data):raise ValueError('timing_report')
 return {'artifact_id':'reiyah.takeover-outcome.timing-verification','version':'0.2.0','timelines_checked':len(seen),'decimal_fraction_values_agree':True,'recovery_timing_qualified':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--records',required=True);p.add_argument('--output',required=True);p.add_argument('--verification',required=True);a=p.parse_args()
 data=analyze.load(a.records);result=audit(data);verification=check(data,result)
 pathlib.Path(a.output).write_text(json.dumps(result,indent=2)+'\n');pathlib.Path(a.verification).write_text(json.dumps(verification,indent=2)+'\n')
