"""Separate finite inventory check, without importing the audit producer."""
from pathlib import Path
import argparse,hashlib,json,re
p=argparse.ArgumentParser();p.add_argument('--sources',type=Path,required=True);p.add_argument('--inputs',type=Path,required=True);p.add_argument('--findings',type=Path,required=True);p.add_argument('--result',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
manifest=json.loads(a.inputs.read_bytes());result=json.loads(a.result.read_bytes());notes=json.loads(a.findings.read_bytes());total=0
for item in manifest['files']:
 b=(a.sources/item['name']).read_bytes();assert len(b)==item['bytes'];assert hashlib.sha256(b).hexdigest()==item['sha256'];total+=len(b)
release=json.loads((a.sources/'release.json').read_bytes())['data']['latestVersion'];rows=release['files'];names=[r['dataFile']['filename'] for r in rows]
assert result['release_files']==len(rows)==56 and len(set(names))==56
assert result['participant_archives']==len([n for n in names if n.startswith('P') and n.endswith('.7z')])==50
assert result['other_archives']==['EEG-BIDS.7z']
assert result['nonarchive_files']==[n for n in names if not n.endswith('.7z')]
assert result['restricted_files']==sum(bool(r['restricted']) for r in rows)==0
code=(a.sources/'DataExtraction.py').read_bytes();meta=next(r['dataFile'] for r in rows if r['dataFile']['filename']=='DataExtraction.py');assert hashlib.md5(code).hexdigest()==meta['checksum']['value'] and len(code)==meta['filesize']
funcs=[{'name':m.group(1),'first_line':i+1} for i,line in enumerate(code.decode().splitlines()) if (m:=re.match(r'^def (\w+)\(',line))]
assert funcs==[{k:r[k] for k in ('name','first_line')} for r in result['code_functions']] and len(funcs)==6
assert all(v==0 for v in result['source_term_mentions'].values())
for term in result['source_term_mentions']:assert term.lower() not in code.decode().lower()
for note in notes['notes']:
 b=(a.sources/note['source']).read_bytes();x=note['locator'];assert hashlib.sha256(b[x['byte_start']:x['byte_end_exclusive']]).hexdigest()==x['span_sha256']
for n,m in [('thesis.txt','thesis-text-metadata.json'),('thesis-license.txt','thesis-license-metadata.json')]:
 b=(a.sources/n).read_bytes();meta=json.loads((a.sources/m).read_bytes())['_embedded']['bitstreams'][0];assert len(b)==meta['sizeBytes'] and hashlib.md5(b).hexdigest()==meta['checkSum']['value']
assert result['input_files_checked']==len(manifest['files'])==11 and result['input_bytes_checked']==total
assert result['code_executed'] is False and result['new_participant_records']==0
assert result['semantic_interpretation_automatically_proved'] is False and result['original_pdf_acquired'] is False
assert result['Gate_A_accepted'] is False and result['recovery_labels_admitted'] is False
out={'artifact_id':'reiyah.mand-semantics.verification','version':'0.1.0','passed':True,'input_files_checked':11,'input_bytes_checked':total,'release_rows_checked':56,'top_level_functions_checked':6,'source_spans_checked':len(notes['notes']),'text_and_license_repository_checksums_match':True,'method':'Separate file digest, JSON inventory and top-level line inspection; no producer import. Human source interpretation separately reviewed, not mechanically proved.','independent_scientific_replication':False}
with a.output.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
