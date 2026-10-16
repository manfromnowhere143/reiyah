"""Offline custody/inventory checks. Human interpretations are not machine-proved."""
from pathlib import Path
import argparse,ast,hashlib,json,re,warnings

def digest(b): return hashlib.sha256(b).hexdigest()
def require(ok,reason):
    if not ok: raise ValueError(reason)
def audit(root,manifest,findings):
    require(set(manifest)=={'artifact_id','version','files'} and manifest['artifact_id']=='reiyah.mand-semantics.inputs' and manifest['version']=='0.1.0','manifest_schema')
    data={}
    for row in manifest['files']:
        require(set(row)=={'name','bytes','sha256'},'manifest_row_schema')
        n=row['name'];require(type(n) is str and Path(n).name==n and n not in ('.','..'),'source_path')
        require(n not in data,'duplicate_source')
        p=root/n;require(p.is_file(),'source_missing');b=p.read_bytes()
        require(len(b)==row['bytes'] and digest(b)==row['sha256'],'source_identity');data[n]=b
    required={'release.json','DataExtraction.py','article.html','structure.html','thesis-item.json','thesis-bundles.json','thesis-text-metadata.json','thesis-original-metadata.json','thesis.txt','thesis-license-metadata.json','thesis-license.txt'}
    require(set(data)==required,'source_inventory')
    obj=lambda n:json.loads(data[n])
    release=obj('release.json')['data']['latestVersion'];require((release['versionNumber'],release['versionMinorNumber'])==(2,0),'release_version')
    files=release['files'];names=[r['dataFile']['filename'] for r in files];require(len(names)==len(set(names)),'release_duplicate_file')
    scripts=[r for r in files if r['dataFile']['filename'].endswith('.py')];require(len(scripts)==1 and scripts[0]['dataFile']['filename']=='DataExtraction.py','designated_code_inventory')
    code=scripts[0]['dataFile'];require(code['filesize']==len(data['DataExtraction.py']) and code['checksum']=={'type':'MD5','value':hashlib.md5(data['DataExtraction.py']).hexdigest()},'released_code_binding')
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter('always');tree=ast.parse(data['DataExtraction.py'].decode())
    functions=[{'name':n.name,'first_line':n.lineno,'last_line':n.end_lineno} for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
    names_to_find=['EnvironmentalEvent','InteractionSignal','accident','collision','SCANeR']
    mentions={term:len(re.findall(re.escape(term),data['DataExtraction.py'].decode(),re.I)) for term in names_to_find}
    bundles=obj('thesis-bundles.json');require(bundles['page']['totalPages']==1,'bundle_pagination')
    bundle_names=[r['name'] for r in bundles['_embedded']['bundles']]
    require(len(bundle_names)==len(set(bundle_names)) and 'TEXT' in bundle_names and 'ORIGINAL' in bundle_names,'thesis_bundle_identity')
    derivatives=[]
    for m,n,bundle in [('thesis-text-metadata.json','thesis.txt','TEXT'),('thesis-license-metadata.json','thesis-license.txt','LICENSE')]:
        x=obj(m);require(x['page']['totalPages']==1 and len(x['_embedded']['bitstreams'])==1,'derivative_inventory')
        f=x['_embedded']['bitstreams'][0]
        require(f['bundleName']==bundle and f['sizeBytes']==len(data[n]) and f['checkSum']=={'checkSumAlgorithm':'MD5','value':hashlib.md5(data[n]).hexdigest()},'derivative_binding')
        derivatives.append({'name':n,'bytes':len(data[n]),'advertised_size_and_md5_match':True,'id':f['id']})
    spans=[]
    for note in findings['notes']:
        b=data[note['source']];loc=note['locator'];a=loc['byte_start'];z=loc['byte_end_exclusive']
        require(type(a) is int and type(z) is int and 0<=a<z<=len(b),'span_range')
        require(digest(b)==note['source_sha256'] and digest(b[a:z])==loc['span_sha256'],'span_identity')
        spans.append(note['id'])
    require(len(spans)==len(set(spans)),'duplicate_note')
    decision=findings['decision']
    for key in ('release_event_generator_qualified','positive_ego_accident_control_identified','monitoring_and_censoring_qualified','recovery_labels_admitted','readiness_model_admitted','Gate_A_accepted'):
        require(decision[key] is False,'unsupported_qualification')
    require(decision['positive_control_population_count'] is None,'unmeasured_population')
    return {'artifact_id':'reiyah.mand-semantics.audit','version':'0.1.0','passed':True,'input_files_checked':len(data),'input_bytes_checked':sum(map(len,data.values())),'release_version':'2.0','release_files':len(files),'restricted_files':sum(r['restricted'] for r in files),'participant_archives':sum(bool(re.fullmatch(r'P\d+\.7z',n)) for n in names),'other_archives':[n for n in names if n.endswith('.7z') and not re.fullmatch(r'P\d+\.7z',n)],'nonarchive_files':[n for n in names if not n.endswith('.7z')],'code_functions':functions,'source_term_mentions':mentions,'parse_warning_count':len(captured),'code_executed':False,'derivatives':derivatives,'original_pdf_acquired':False,'reviewed_spans_bound':spans,'semantic_interpretation_automatically_proved':False,'new_participant_records':0,'recovery_labels_admitted':False,'Gate_A_accepted':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--sources',type=Path,required=True);p.add_argument('--inputs',type=Path,required=True);p.add_argument('--findings',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=audit(a.sources,json.loads(a.inputs.read_bytes()),json.loads(a.findings.read_bytes()))
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
if __name__=='__main__':main()
