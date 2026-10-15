"""Read the released coverage workbook without recalculation or modification."""
import argparse,hashlib,json,pathlib,zipfile,xml.etree.ElementTree as ET
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def require(ok,why):
 if not ok:raise ValueError(why)
def read(path):
 raw=pathlib.Path(path).read_bytes();sheets={}
 with zipfile.ZipFile(path) as z:
  ss=[''.join(t.text or '' for t in si.findall('.//m:t',NS)) for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',NS)]
  styles=ET.fromstring(z.read('xl/styles.xml'));fonts=styles.find('m:fonts',NS);xfs=styles.find('m:cellXfs',NS)
  rels={e.attrib['Id']:e.attrib['Target'] for e in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
  for sheet in ET.fromstring(z.read('xl/workbook.xml')).findall('m:sheets/m:sheet',NS):
   target=rels[sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
   name=target.lstrip('/') if target.startswith('/') else 'xl/'+target
   tree=ET.fromstring(z.read(name));cells={}
   for cell in tree.findall('m:sheetData/m:row/m:c',NS):
    v=cell.find('m:v',NS);value=v.text if v is not None else None
    if cell.attrib.get('t')=='s':value=ss[int(value)]
    if cell.attrib.get('t')=='inlineStr':value=''.join(t.text or '' for t in cell.findall('.//m:t',NS))
    formula=cell.find('m:f',NS);font=fonts[int(xfs[int(cell.attrib.get('s',0))].attrib.get('fontId',0))];color=font.find('m:color',NS)
    require(cell.attrib['r'] not in cells,'duplicate_cell')
    cells[cell.attrib['r']]={'value':value,'formula':formula.text if formula is not None else None,'font_color':dict(color.attrib) if color is not None else None}
   sheets[sheet.attrib['name']]=cells
 require(pathlib.Path(path).read_bytes()==raw,'source_changed')
 return sheets,hashlib.sha256(raw).hexdigest()
def project(sheets,digest):
 a=sheets['AvailableSensorData'];o=sheets['ScenarioCombination'];names=['Familiarization','No Emotion','Anger','Surprise','Sadness','Fear'];cols=[('C','D'),('J','K'),('Q','R'),('X','Y'),('AE','AF'),('AL','AM')]
 for name,(e,v) in zip(names,cols):
  require(a[e+'2']['value']==name and a[e+'3']['value']=='Environment' and a[v+'3']['value']=='Vehicle','coverage_headers')
 require(o['I4']['value']=='red' and o['J4']['value']==': not driven' and o['I5']['value']=='black' and o['J5']['value']==': driven','order_legend')
 red=o['I4']['font_color'];black=o['I5']['font_color'];require(red!=black,'ambiguous_color_legend')
 rows=[];seen=set()
 for row in range(4,54):
  participant=a['B'+str(row)]['value'];require(participant not in seen and participant==str(row-3),'participant_identity');seen.add(participant)
  require(o['B'+str(row)]['value']==participant,'order_identity')
  slots=[]
  for name,(e,v) in zip(names,cols):
   cells=[e+str(row),v+str(row)];vals=[a[c]['value'] for c in cells]
   require(all(x in ('0','1',None) for x in vals),'availability_code')
   slots.append({'scenario':name.lower().replace(' ',''),'source_cells':cells,'environment':None if vals[0] is None else int(vals[0]),'vehicle':None if vals[1] is None else int(vals[1])})
  order=[]
  for col in 'CDEFG':
   cell=col+str(row);x=o[cell];color=x['font_color'];require(color in (red,black),'unknown_order_color')
   order.append({'scenario':x['value'],'source_cell':cell,'driven':color==black})
  rows.append({'participant':int(participant),'availability':slots,'order':order})
 counts={name.lower().replace(' ',''):sum(r['availability'][j]['environment']==1 and r['availability'][j]['vehicle']==1 for r in rows) for j,name in enumerate(names)}
 require(sum(counts.values())==int(a['AL58']['value'])==int(a['AM58']['value']),'cached_coverage_total_mismatch')
 candidates=[(r['participant'],i+1,s['scenario']) for r in rows for i,s in enumerate(r['order']) if s['driven'] and any(t['scenario']==s['scenario'] and t['environment']==t['vehicle']==1 for t in r['availability'])]
 require(candidates,'no_available_driven_scenario');chosen=min(candidates)
 return {'artifact_id':'reiyah.mand-timing.coverage','version':'0.1.0','source_sha256':digest,'source_sheet':'AvailableSensorData','participant_rows':50,'scenario_slots_including_familiarization':300,'both_channels_available_by_scenario':counts,'both_channels_available':sum(counts.values()),'availability_means_complete_followup':False,'selection_rule':'Lowest participant ID, then first ordered non-familiarization scenario marked driven with both required channels available; no outcome, demographic or smallest-archive selection','selected':{'participant':chosen[0],'order':chosen[1],'scenario':chosen[2]},'participants':rows}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--workbook',required=True);p.add_argument('--output',required=True);a=p.parse_args();s,h=read(a.workbook);pathlib.Path(a.output).write_text(json.dumps(project(s,h),indent=2)+'\n')
