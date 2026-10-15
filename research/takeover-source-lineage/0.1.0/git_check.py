"""Standard Git checks the retained tree objects and every recursive root listing."""
import argparse,json,pathlib,subprocess,tempfile

def check(data):
 def require(ok,why):
  if not ok:raise ValueError(why)
 objects=data['tree_objects'];roots={c['tree'] for c in data['commits']};total=0
 with tempfile.TemporaryDirectory(prefix='reiyah-git-trees-') as tmp:
  def git(*args,body=None):
   return subprocess.run(['git','-C',tmp,*args],input=body,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=10).stdout
  git('init','--bare','--quiet')
  for oid,entries in objects.items():
   raw=bytearray()
   for entry in entries:
    raw.extend((entry['mode']+' '+entry['name']).encode('utf-8'));raw.append(0);raw.extend(bytes.fromhex(entry['oid']))
   require(git('hash-object','-w','-t','tree','--stdin',body=bytes(raw)).decode().strip()==oid,'git_hash_mismatch')
  for root in sorted(roots):
   expected={};stack=[('',root)]
   while stack:
    prefix,oid=stack.pop()
    for entry in objects[oid]:
     name=prefix+entry['name'];require(name not in expected,'duplicate_path');expected[name]=(entry['mode'],entry['type'],entry['oid'])
     if entry['type']=='tree':stack.append((name+'/',entry['oid']))
   actual={}
   for row in git('ls-tree','--full-tree','-r','-t','-z',root).split(b'\0'):
    if not row:continue
    meta,name=row.split(b'\t',1);mode,kind,oid=meta.decode().split(' ');actual[name.decode()]=(mode.lstrip('0'),kind,oid)
   require(actual==expected,'git_recursive_listing_mismatch');total+=len(actual)
 return {'artifact_id':'reiyah.takeover-source-lineage.git-verification','version':'0.1.0','verified':True,'git_tree_objects':len(objects),'recursive_root_inventories':len(roots),'recursive_entries_checked':total,'method':'Git hash-object and ls-tree in a fresh temporary bare object store; no upstream executable code or blob payload','commit_identity_or_signature_verified':False,'dataset_capture_binding_established':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--inventory',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 data=json.loads(pathlib.Path(a.inventory).read_bytes());pathlib.Path(a.output).write_text(json.dumps(check(data),indent=2)+'\n')
