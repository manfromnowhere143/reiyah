import csv,hashlib,json,pathlib,sys,fractions,re
TASKS=['0back','1back','2back','audiobook listening','auditory gaming','auditory texting','baseline','ebook reading','gaming','texting']
EVENTS={'front_vehicle':'F','left_pedestrian':'L','right_pedestrian':'R'}
HEADERS='criticalEventType,criticalEventOccurrenceTime,scenarioEndTime,takeoverResult,reactionTime,NASA-TLX,NASA-RTLX,mentalDemand,physicalDemand,temporalDemand,performance,effort,frustration,weightOfMentalDemand,weightOfPhysicalDemand,weightOfTemporalDemand,weightOfPerformance,weightOfEffort,weightOfFrustration'.split(',')
def prepare(root):
 rows=[]
 for n in range(1,51):
  driver=f'D{n:02}'
  for task in TASKS:
   p=root/driver/task/'takeoverScenarioInformations.csv'
   base={'id':driver+'/'+task,'driver':driver,'task':task,'event':None,'outcome':None,'reaction_ms':None,'event_ms':None,'end_ms':None,'source_sha256':None,'status':'missing','issues':[]}
   if not p.exists():base['issues']=['missing_source_file'];rows.append(base);continue
   raw=p.read_bytes();base['source_sha256']=hashlib.sha256(raw).hexdigest()
   try:
    if len(raw)>4096:raise ValueError('source_size')
    parsed=list(csv.reader(raw.decode('utf-8-sig').splitlines(),strict=True))
    if len(parsed)!=2:raise ValueError('source_row_count')
    if parsed[0]!=HEADERS:raise ValueError('source_header')
    if len(parsed[1])!=len(HEADERS):raise ValueError('source_columns')
    d=dict(zip(HEADERS,parsed[1]));base['event']=EVENTS[d['criticalEventType']]
    if d['takeoverResult'] not in ['Success','Failure']:raise ValueError('source_outcome')
    base['outcome']=d['takeoverResult']
    for field,key in [('reactionTime','reaction_ms'),('criticalEventOccurrenceTime','event_ms'),('scenarioEndTime','end_ms')]:
     if not re.fullmatch(r'[0-9]+(?:\.[0-9]+)?',d[field]) or len(d[field])>40:raise ValueError('source_decimal_time')
     base[key]=d[field]
    if fractions.Fraction(base['end_ms'])<fractions.Fraction(base['event_ms'])+fractions.Fraction(base['reaction_ms']):raise ValueError('source_time_order')
    base['status']='valid'
   except (ValueError,KeyError,UnicodeError,csv.Error) as e:base['status']='invalid';base['issues']=[str(e)]
   rows.append(base)
 return {'artifact_id':'reiyah.takeover-outcome.records','version':'0.1.0','source_doi':'10.5281/zenodo.14185964','license':'CC-BY-4.0','records':rows}
if __name__=='__main__':
 pathlib.Path(sys.argv[2]).write_text(json.dumps(prepare(pathlib.Path(sys.argv[1])),indent=2)+'\n')
