"""Authored custody controls; no accident or driver behavior is simulated."""
from pathlib import Path
import argparse,copy,hashlib,json,tempfile,shutil
from audit import audit

def main():
 p=argparse.ArgumentParser();p.add_argument('--sources',type=Path,required=True);p.add_argument('--inputs',type=Path,required=True);p.add_argument('--findings',type=Path,required=True);a=p.parse_args()
 original=json.loads(a.inputs.read_bytes());notes=json.loads(a.findings.read_bytes());assert audit(a.sources,original,notes)['passed'];checks=[]
 tests=[('substitute_source','source_identity'),('missing_source','source_missing'),('duplicate_source','duplicate_source'),('traversal','source_path'),('bad_span','span_identity'),('bad_range','span_range'),('claim_recovery','unsupported_qualification'),('unknown_as_zero','unmeasured_population'),('broken_release_binding','released_code_binding')]
 for name,reason in tests:
  with tempfile.TemporaryDirectory(prefix='mand-semantics-control-') as td:
   root=Path(td);m=copy.deepcopy(original);f=copy.deepcopy(notes)
   for row in m['files']:shutil.copyfile(a.sources/row['name'],root/row['name'])
   if name=='substitute_source':(root/'DataExtraction.py').write_bytes((root/'DataExtraction.py').read_bytes()+b'\n')
   elif name=='missing_source':(root/'article.html').unlink()
   elif name=='duplicate_source':m['files'].append(copy.deepcopy(m['files'][0]))
   elif name=='traversal':m['files'][0]['name']='../release.json'
   elif name=='bad_span':f['notes'][0]['locator']['span_sha256']='0'*64
   elif name=='bad_range':f['notes'][0]['locator']['byte_end_exclusive']=-1
   elif name=='claim_recovery':f['decision']['recovery_labels_admitted']=True
   elif name=='unknown_as_zero':f['decision']['positive_control_population_count']=0
   else:
    obj=json.loads((root/'release.json').read_bytes());next(r for r in obj['data']['latestVersion']['files'] if r['dataFile']['filename']=='DataExtraction.py')['dataFile']['checksum']['value']='0'*32
    raw=json.dumps(obj).encode();(root/'release.json').write_bytes(raw);row=next(r for r in m['files'] if r['name']=='release.json');row.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
   try:audit(root,m,f)
   except ValueError as exc:
    assert str(exc)==reason,(name,str(exc));checks.append({'case':name,'rejected_for':reason})
   else:raise AssertionError('accepted '+name)
 print(json.dumps({'artifact_id':'reiyah.mand-semantics.controls','version':'0.1.0','passed':len(checks),'checks':checks},indent=2))
if __name__=='__main__':main()
