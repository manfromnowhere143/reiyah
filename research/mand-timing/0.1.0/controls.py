"""Authored missingness, clock, code and boundary controls, separate from empirical records."""
import csv,json,pathlib,tempfile
import audit
checks=[]
def passed(name,ok):
 if not ok:raise AssertionError(name)
 checks.append({'control':name,'passed':True})
for raw,want,name in [('', 'missing','blank_is_missing'),('0','0','zero_is_observed_zero'),('NaN','nonfinite','NaN_is_nonfinite'),('n/a','invalid','text_is_invalid'),('3.5','invalid_code:3.5','fractional_code_not_rounded'),('17','invalid_code:17','out_of_range_code_not_admitted')]:passed(name,audit.code(raw,set(range(17)))==want)
with tempfile.TemporaryDirectory() as tmp:
 root=pathlib.Path(tmp);env=root/'Environment.txt';veh=root/'Vehicle.txt'
 def write(path,header,rows):
  with path.open('w',newline='') as f:csv.writer(f).writerows([header,*rows])
 def reject(name,reason,header,rows):
  write(env,header,rows)
  try:audit.inspect(env)
  except ValueError as e:
   if str(e)!=reason:raise AssertionError((name,reason,str(e))) from e
   checks.append({'control':name,'rejected_for':reason})
  else:raise AssertionError(name)
 reject('duplicate_header','headers',['time','EnvironmentalEvent','time'],[['0','0','0']])
 reject('extra_field','row_width',['time','EnvironmentalEvent'],[['0','0','unexpected']])
 reject('missing_time','time_not_finite',['time','EnvironmentalEvent'],[['','0']])
 reject('nonfinite_time','time_not_finite',['time','EnvironmentalEvent'],[['NaN','0']])
 reject('no_records','empty_records',['time','EnvironmentalEvent'],[])
 for rows,name in [([['0','0'],['0','0']],'duplicate_time_detected'),([['1','0'],['0','0']],'decreasing_time_detected')]:
  write(env,['time','EnvironmentalEvent'],rows);report,*_=audit.inspect(env);passed(name,report['strictly_increasing'] is False)
 write(env,['time','EnvironmentalEvent'],[['0','0'],['0.00390625','5']]);write(veh,['time','InteractionSignal','AutomationMode'],[['0','0',''],['0.00390625','3','3']]);x=audit.analyze(env,veh)
 passed('missing_automation_not_manual',x['files'][1]['codes']['AutomationMode']['counts']=={'3':1,'missing':1})
 passed('unobserved_manual_action_not_zero_latency',x['TOR_observations'][0]['first_manual_time'] is None and x['TOR_observations'][0]['source_time_difference_to_first_manual'] is None)
 passed('final_segment_has_no_invented_endpoint',x['files'][1]['codes']['InteractionSignal']['segments'][-1]['next_record_time'] is None)
 passed('no_collision_code_does_not_imply_success',x['qualification']['no_accident_code_means_success'] is False and x['qualification']['recovery_labels_admitted'] is False)
 write(veh,['time','InteractionSignal','AutomationMode'],[['0','0',''],['0.0078125','3','3']]);x=audit.analyze(env,veh)
 passed('misaligned_clocks_not_qualified',x['alignment']['every_numeric_time_equal'] is False and x['qualification']['stored_time_alignment']=='not_qualified' and x['TOR_observations']==[])
print(json.dumps({'artifact_id':'reiyah.mand-timing.controls','version':'0.1.0','passed':len(checks),'checks':checks},indent=2))
