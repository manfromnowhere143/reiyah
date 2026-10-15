"""Describe recorded clocks, missingness and categorical runs without recovery labels."""
import argparse,collections,csv,hashlib,itertools,json,pathlib
from decimal import Decimal,InvalidOperation
CODES={'Environment.txt':{'EnvironmentalEvent':set(range(7))},'Vehicle.txt':{'InteractionSignal':set(range(17)),'AutomationMode':{-1,0,1,2,3}}}
def require(ok,why):
 if not ok:raise ValueError(why)
def number(raw):
 if raw=='':return 'missing',None
 try:
  require(len(raw)<=128,'numeric_token_length');x=Decimal(raw)
 except InvalidOperation:return 'invalid',None
 if not x.is_finite():return 'nonfinite',None
 return 'finite',x
def code(raw,allowed):
 state,x=number(raw)
 if state!='finite':return state
 if x!=x.to_integral_value() or int(x) not in allowed:return 'invalid_code:'+raw
 return str(int(x))
def canonical(x):return format(x.normalize(),'f') if x else '0'
def inspect(path):
 path=pathlib.Path(path);rules=CODES[path.name];times=[];time_text=[];gaps=collections.Counter();code_values={f:[] for f in rules};fields={};previous=None
 with path.open(newline='',encoding='utf-8') as f:
  reader=csv.reader(f);header=next(reader);require(len(header)==len(set(header)) and 'time' in header and set(rules)<=set(header),'headers')
  for name in header:fields[name]={'states':collections.Counter(),'first_finite_row':None,'last_finite_row':None,'distance_unavailable_99000':0}
  for i,row in enumerate(reader):
   require(len(row)==len(header),'row_width');d=dict(zip(header,row));state,t=number(d['time']);require(state=='finite','time_not_finite')
   if previous is not None:gaps[canonical(t-previous)]+=1
   previous=t;times.append(t);time_text.append(d['time'])
   for name,raw in d.items():
    state,x=number(raw);v=fields[name];v['states'][state]+=1
    if state=='finite':
     if v['first_finite_row'] is None:v['first_finite_row']=i
     v['last_finite_row']=i
     if name.startswith('DistanceTo') and 'Vehicle' in name and x==99000:v['distance_unavailable_99000']+=1
   for name,allowed in rules.items():code_values[name].append(code(d[name],allowed))
 require(times,'empty_records')
 runs={}
 for name,values in code_values.items():
  segments=[];start=0
  for stop in range(1,len(values)+1):
   if stop==len(values) or values[stop]!=values[start]:
    segments.append({'value':values[start],'first_row':start,'last_row':stop-1,'first_time':canonical(times[start]),'last_time':canonical(times[stop-1]),'next_record_time':canonical(times[stop]) if stop<len(values) else None});start=stop
  runs[name]={'counts':dict(sorted(collections.Counter(values).items())),'segments':segments}
 for v in fields.values():v['states']=dict(sorted(v['states'].items()))
 report={'file':path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'header':header,'rows':len(times),'first_time':canonical(times[0]),'last_time':canonical(times[-1]),'time_differences':dict(sorted(gaps.items(),key=lambda p:Decimal(p[0]))),'strictly_increasing':all(Decimal(x)>0 for x in gaps),'exact_row_index_over_256':all(t*256==i for i,t in enumerate(times)),'time_unit':'not_explicitly_named_in_retained_dictionary_or_file_header','fields':fields,'codes':runs}
 return report,times,time_text,code_values

def analyze(environment,vehicle):
 er,et,es,ec=inspect(environment);vr,vt,vs,vc=inspect(vehicle)
 equal=len(et)==len(vt) and et==vt
 tor=[s for s in vr['codes']['InteractionSignal']['segments'] if s['value']=='3'];events=[]
 if equal:
  for s in tor:
   i=s['first_row'];manual=next((j for j in range(i,len(vt)) if vc['AutomationMode'][j]=='0'),None)
   events.append({'TOR_first_row':i,'TOR_first_time':canonical(vt[i]),'TOR_last_row':s['last_row'],'TOR_next_record_time':s['next_record_time'],'environment_code_at_TOR':ec['EnvironmentalEvent'][i],'automation_code_at_TOR':vc['AutomationMode'][i],'first_manual_record_at_or_after_TOR':manual,'first_manual_time':canonical(vt[manual]) if manual is not None else None,'source_time_difference_to_first_manual':canonical(vt[manual]-vt[i]) if manual is not None else None,'recording_last_time':canonical(vt[-1]),'source_time_difference_to_last_record':canonical(vt[-1]-vt[i]),'interpretation':'Stored state/message arithmetic only; not driver first-action latency, success, continuous collision monitoring or recovery.'})
 return {'artifact_id':'reiyah.mand-timing.result','version':'0.1.0','selection':{'participant':1,'scenario':'anger'},'files':[er,vr],'alignment':{'same_rows':len(et)==len(vt),'every_numeric_time_equal':equal,'every_time_token_equal':es==vs},'TOR_observations':events,'qualification':{'stored_time_alignment':'supported_for_selected_files' if equal else 'not_qualified','physical_clock_unit_origin_error_bound':'not_qualified','native_hz_documented':20,'delivered_hz_documented':256,'upsampling_adds_native_precision':False,'event_detector_and_annotation_latency':'not_qualified','continuous_collision_monitoring_and_censoring':'not_qualified','no_accident_code_means_success':False,'recovery_labels_admitted':False,'readiness_model_admitted':False,'Gate_A_operator_accepted':False}}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--environment',required=True);p.add_argument('--vehicle',required=True);p.add_argument('--output',required=True);a=p.parse_args();pathlib.Path(a.output).write_text(json.dumps(analyze(a.environment,a.vehicle),indent=2)+'\n')
