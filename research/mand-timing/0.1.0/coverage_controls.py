"""Critical coverage corruptions must fail for their declared reason."""
import argparse,copy,json,pathlib
import coverage

def main(workbook):
 sheets,digest=coverage.read(workbook);checks=[]
 def reject(name,reason,change):
  data=copy.deepcopy(sheets);change(data)
  try:coverage.project(data,digest)
  except ValueError as e:
   if str(e)!=reason:raise AssertionError((name,reason,str(e))) from e
   checks.append({'control':name,'rejected_for':reason})
  else:raise AssertionError(name)
 reject('wrong_environment_header','coverage_headers',lambda d:d['AvailableSensorData']['C3'].update(value='Other'))
 reject('duplicate_participant','participant_identity',lambda d:d['AvailableSensorData']['B5'].update(value='1'))
 reject('order_participant_mismatch','order_identity',lambda d:d['ScenarioCombination']['B4'].update(value='2'))
 reject('invalid_availability_value','availability_code',lambda d:d['AvailableSensorData']['Q4'].update(value='2'))
 reject('indistinguishable_order_legend','ambiguous_color_legend',lambda d:d['ScenarioCombination']['I4'].update(font_color=d['ScenarioCombination']['I5']['font_color']))
 reject('unknown_order_font_color','unknown_order_color',lambda d:d['ScenarioCombination']['C4'].update(font_color={'rgb':'FF112233'}))
 reject('incorrect_cached_total','cached_coverage_total_mismatch',lambda d:d['AvailableSensorData']['AL58'].update(value='234'))
 return {'artifact_id':'reiyah.mand-timing.coverage-controls','version':'0.1.0','passed':len(checks),'checks':checks}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--workbook',required=True);a=p.parse_args();print(json.dumps(main(a.workbook),indent=2))
