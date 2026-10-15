"""Separate Fraction/SQLite calculations check all source rows and categorical runs."""
import argparse,collections,csv,hashlib,json,pathlib,re,sqlite3,zipfile,xml.etree.ElementTree as ET
from fractions import Fraction
NUM=re.compile(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z')
RULES={'Environment.txt':{'EnvironmentalEvent':set(range(7))},'Vehicle.txt':{'InteractionSignal':set(range(17)),'AutomationMode':{-1,0,1,2,3}}}
def require(ok,why):
 if not ok:raise ValueError(why)
def classify(raw):
 if raw=='':return 'missing',None
 if raw.lower().lstrip('+-') in ('nan','snan','inf','infinity'):return 'nonfinite',None
 if not NUM.fullmatch(raw):return 'invalid',None
 return 'finite',Fraction(raw)
def state(raw,allowed):
 kind,v=classify(raw)
 if kind!='finite':return kind
 if v.denominator!=1 or v.numerator not in allowed:return 'invalid_code:'+raw
 return str(v.numerator)
def verify(environment,vehicle,result,workbook,coverage):
 db=sqlite3.connect(':memory:');db.execute('CREATE TABLE clocks (file TEXT, i INTEGER, token TEXT, numerator INTEGER, denominator INTEGER, PRIMARY KEY(file,i))');db.execute('CREATE TABLE codes (file TEXT, field TEXT, i INTEGER, value TEXT)')
 rows_checked=fields_checked=segments_checked=0
 for source in [environment,vehicle]:
  p=pathlib.Path(source);expected=next(f for f in result['files'] if f['file']==p.name);h=hashlib.sha256(p.read_bytes()).hexdigest();require(h==expected['sha256'],'source_digest');rules=RULES[p.name];stats={};gaps=collections.Counter();prev=None;times=[];code_batch=[];clock_batch=[]
  with p.open(newline='') as f:
   reader=csv.DictReader(f);require(reader.fieldnames==expected['header'],'headers')
   for name in reader.fieldnames:stats[name]={'states':collections.Counter(),'first_finite_row':None,'last_finite_row':None,'distance_unavailable_99000':0}
   for i,d in enumerate(reader):
    require(None not in d and all(v is not None for v in d.values()),'row_width')
    t=Fraction(d['time']);times.append(t);clock_batch.append((p.name,i,d['time'],t.numerator,t.denominator))
    if prev is not None:gaps[t-prev]+=1
    prev=t
    for name,raw in d.items():
     kind,value=classify(raw);v=stats[name];v['states'][kind]+=1
     if kind=='finite':
      if v['first_finite_row'] is None:v['first_finite_row']=i
      v['last_finite_row']=i
      if name.startswith('DistanceTo') and 'Vehicle' in name and value==99000:v['distance_unavailable_99000']+=1
    for name,allowed in rules.items():code_batch.append((p.name,name,i,state(d[name],allowed)))
    if len(clock_batch)>=1000:
     db.executemany('INSERT INTO clocks VALUES(?,?,?,?,?)',clock_batch);db.executemany('INSERT INTO codes VALUES(?,?,?,?)',code_batch);clock_batch=[];code_batch=[]
   db.executemany('INSERT INTO clocks VALUES(?,?,?,?,?)',clock_batch);db.executemany('INSERT INTO codes VALUES(?,?,?,?)',code_batch)
  require(len(times)==expected['rows'],'row_count');rows_checked+=len(times)
  require(times[0]==Fraction(expected['first_time']) and times[-1]==Fraction(expected['last_time']),'endpoints')
  require(gaps=={Fraction(k):v for k,v in expected['time_differences'].items()},'gap_histogram')
  require(all(t==Fraction(i,256) for i,t in enumerate(times))==expected['exact_row_index_over_256'],'time_grid')
  require(all(g>0 for g in gaps)==expected['strictly_increasing'],'monotonicity')
  for name,stat in stats.items():stat['states']=dict(stat['states']);require(stat==expected['fields'][name],'field_states:'+name);fields_checked+=1
  for name,code in expected['codes'].items():
   counts=dict(db.execute('SELECT value,COUNT(*) FROM codes WHERE file=? AND field=? GROUP BY value',(p.name,name)));require(counts==code['counts'],'code_counts')
   sql='''WITH ordered AS (SELECT i,value,LAG(value) OVER (ORDER BY i) AS previous FROM codes WHERE file=? AND field=?), marked AS (SELECT i,value,CASE WHEN previous IS NULL OR previous != value THEN 1 ELSE 0 END AS change FROM ordered), grouped AS (SELECT i,value,SUM(change) OVER (ORDER BY i) AS segment FROM marked) SELECT value,MIN(i),MAX(i) FROM grouped GROUP BY segment ORDER BY MIN(i)'''
   runs=db.execute(sql,(p.name,name)).fetchall();require(len(runs)==len(code['segments']),'run_count')
   for (value,start,stop),want in zip(runs,code['segments']):
    require((value,start,stop)==(want['value'],want['first_row'],want['last_row']),'run_boundary')
    require(times[start]==Fraction(want['first_time']) and times[stop]==Fraction(want['last_time']),'run_time')
    if stop+1<len(times):require(times[stop+1]==Fraction(want['next_record_time']),'following_time')
    else:require(want['next_record_time'] is None,'censoring_boundary')
    segments_checked+=1
  if p.name=='Vehicle.txt':vehicle_times=times
 a=db.execute('SELECT COUNT(*) FROM clocks a JOIN clocks b ON a.i=b.i WHERE a.file=? AND b.file=? AND a.token=b.token',('Environment.txt','Vehicle.txt')).fetchone()[0]
 n=result['files'][0]['rows'];require(a==n and result['alignment']=={'same_rows':True,'every_numeric_time_equal':True,'every_time_token_equal':True},'all_clock_pairs')
 tor=db.execute('''SELECT c.i FROM codes c LEFT JOIN codes p ON p.file=c.file AND p.field=c.field AND p.i=c.i-1 WHERE c.file='Vehicle.txt' AND c.field='InteractionSignal' AND c.value='3' AND (p.value IS NULL OR p.value!='3') ORDER BY c.i''').fetchall()
 require(len(tor)==len(result['TOR_observations']),'TOR_count')
 for (i,),expected in zip(tor,result['TOR_observations']):
  manual=db.execute("SELECT MIN(i) FROM codes WHERE file='Vehicle.txt' AND field='AutomationMode' AND value='0' AND i>=?",(i,)).fetchone()[0]
  require(i==expected['TOR_first_row'] and manual==expected['first_manual_record_at_or_after_TOR'],'TOR_manual_rows')
  require(vehicle_times[manual]-vehicle_times[i]==Fraction(expected['source_time_difference_to_first_manual']),'manual_difference')
  require(vehicle_times[-1]-vehicle_times[i]==Fraction(expected['source_time_difference_to_last_record']),'last_record_difference')
 # Independent worksheet value lookup and SQL aggregation of all 600 required availability cells.
 ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'};raw=pathlib.Path(workbook).read_bytes();require(hashlib.sha256(raw).hexdigest()==coverage['source_sha256'],'workbook_digest')
 with zipfile.ZipFile(workbook) as z:
  shared=[''.join(t.text or '' for t in s.findall('.//m:t',ns)) for s in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',ns)]
  tree=ET.fromstring(z.read('xl/worksheets/sheet1.xml'));cells={}
  for c in tree.findall('.//m:sheetData/m:row/m:c',ns):
   v=c.find('m:v',ns)
   if v is not None:cells[c.attrib['r']]=shared[int(v.text)] if c.attrib.get('t')=='s' else v.text
 db.execute('CREATE TABLE availability (participant INTEGER, scenario TEXT, environment INTEGER, vehicle INTEGER)')
 slots=['familiarization','noemotion','anger','surprise','sadness','fear'];cols=[('C','D'),('J','K'),('Q','R'),('X','Y'),('AE','AF'),('AL','AM')]
 for row in range(4,54):
  participant=int(cells['B'+str(row)])
  for j,(e,v) in enumerate(cols):
   ev=int(cells[e+str(row)]);vv=int(cells[v+str(row)]);record=coverage['participants'][row-4]['availability'][j]
   require((record['environment'],record['vehicle'])==(ev,vv),'source_coverage_cell');db.execute('INSERT INTO availability VALUES(?,?,?,?)',(participant,slots[j],ev,vv))
 got=dict(db.execute('SELECT scenario,COUNT(*) FROM availability WHERE environment=1 AND vehicle=1 GROUP BY scenario'));require(got==coverage['both_channels_available_by_scenario'],'coverage_counts')
 db.close()
 return {'artifact_id':'reiyah.mand-timing.verification','version':'0.1.0','passed':True,'source_rows_checked':rows_checked,'aligned_row_pairs':a,'field_state_summaries_checked':fields_checked,'categorical_runs_checked':segments_checked,'TOR_onsets_checked':len(tor),'coverage_cells_checked':600,'method':'Separate Fraction arithmetic and SQLite GROUP BY/window functions over original permitted files; worksheet XML value lookup separately checks all 600 availability cells. No producer import. Integrity/calculation check, not independent scientific replication.'}
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for n in ['environment','vehicle','result','workbook','coverage','output']:p.add_argument('--'+n,required=True)
 a=p.parse_args();x=verify(a.environment,a.vehicle,json.loads(pathlib.Path(a.result).read_bytes()),a.workbook,json.loads(pathlib.Path(a.coverage).read_bytes()));pathlib.Path(a.output).write_text(json.dumps(x,indent=2)+'\n')
