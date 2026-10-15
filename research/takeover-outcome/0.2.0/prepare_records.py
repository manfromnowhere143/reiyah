"""Extract only the five uniquely named required fields; preserve suffix defects."""
import csv,fractions,hashlib,json,pathlib,re,sys
TASKS=('0back','1back','2back','audiobook listening','auditory gaming','auditory texting','baseline','ebook reading','gaming','texting')
PREFIX=['criticalEventType','criticalEventOccurrenceTime','scenarioEndTime','takeoverResult','reactionTime']
SUFFIX='NASA-TLX,NASA-RTLX,mentalDemand,physicalDemand,temporalDemand,performance,effort,frustration,weightOfMentalDemand,weightOfPhysicalDemand,weightOfTemporalDemand,weightOfPerformance,weightOfEffort,weightOfFrustration'.split(',')
EVENTS={'front_vehicle':'F','left_pedestrian':'L','right_pedestrian':'R'}
def parse(raw):
 if len(raw)>4096:raise ValueError('source_size')
 rows=list(csv.reader(raw.decode('utf-8-sig').splitlines(),strict=True))
 if len(rows)!=2:raise ValueError('source_row_count')
 header,values=rows
 if header[:5]!=PREFIX or any(header.count(k)!=1 for k in PREFIX):raise ValueError('required_header')
 if len(values)!=len(header):raise ValueError('row_width')
 d=dict(zip(PREFIX,values[:5]))
 if d['criticalEventType'] not in EVENTS:raise ValueError('source_event')
 if d['takeoverResult'] not in ('Success','Failure'):raise ValueError('source_outcome')
 for k in PREFIX[1:3]+[PREFIX[4]]:
  if len(d[k])>40 or not re.fullmatch('[0-9]+(?:[.][0-9]+)?',d[k]) or fractions.Fraction(d[k])>10000000:raise ValueError('source_time')
 if fractions.Fraction(d['scenarioEndTime'])<fractions.Fraction(d['criticalEventOccurrenceTime'])+fractions.Fraction(d['reactionTime']):raise ValueError('source_time_order')
 return {'event':EVENTS[d['criticalEventType']],'outcome':d['takeoverResult'],'reaction_ms':d['reactionTime'],'event_ms':d['criticalEventOccurrenceTime'],'end_ms':d['scenarioEndTime']},{'full_header_matches':header==PREFIX+SUFFIX,'row_columns':len(values),'header_columns':len(header),'workload_suffix_consumed':False}
def prepare(root):
 records=[];admission=[]
 for n in range(1,51):
  for task in TASKS:
   driver=f'D{n:02}';p=root/driver/task/'takeoverScenarioInformations.csv'
   r={'id':driver+'/'+task,'driver':driver,'task':task,'event':None,'outcome':None,'reaction_ms':None,'event_ms':None,'end_ms':None,'source_sha256':None,'status':'missing','issues':[]}
   info={'id':r['id'],'full_header_matches':None,'workload_suffix_consumed':False}
   if p.exists():
    raw=p.read_bytes();r['source_sha256']=hashlib.sha256(raw).hexdigest()
    try:fields,details=parse(raw);r.update(fields,status='valid');info.update(details)
    except (ValueError,KeyError,UnicodeError,csv.Error) as error:r.update(status='invalid',issues=[str(error)])
   else:r['issues']=['missing_source_file']
   records.append(r);admission.append(info)
 return {'artifact_id':'reiyah.takeover-outcome.records','version':'0.2.0','source_doi':'10.5281/zenodo.14185964','license':'CC-BY-4.0','records':records},{'artifact_id':'reiyah.takeover-outcome.admission','version':'0.2.0','records':admission}
if __name__=='__main__':
 r,a=prepare(pathlib.Path(sys.argv[1]));pathlib.Path(sys.argv[2]).write_text(json.dumps(r,indent=2)+'\n');pathlib.Path(sys.argv[3]).write_text(json.dumps(a,indent=2)+'\n')
