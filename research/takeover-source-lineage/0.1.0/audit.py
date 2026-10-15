"""Verify Git tree metadata and inventory the two retained public branch histories."""
import argparse,hashlib,json,pathlib,re

def require(value,reason):
 if not value:raise ValueError(reason)
def load(path):
 def unique(pairs):
  d=dict(pairs);require(len(d)==len(pairs),'duplicate_json_key');return d
 return json.loads(pathlib.Path(path).read_bytes(),object_pairs_hook=unique)
def payload(entries):
 return b''.join(e['mode'].encode()+b' '+e['name'].encode()+b'\0'+bytes.fromhex(e['oid']) for e in entries)
def audit(data):
 require(set(data)=={'artifact_id','version','heads','commits','root_sources','tree_objects','source_scope'},'input_shape')
 require(data['artifact_id']=='reiyah.takeover-source-lineage.inventory' and data['version']=='0.1.0','identity')
 require(set(data['heads'])=={'main','HAI-lab-KNU-patch-1'},'heads')
 objects=data['tree_objects'];require(objects,'empty_objects');modes={'40000':'tree','100644':'blob','100755':'blob','120000':'blob','160000':'commit'}
 for oid,entries in objects.items():
  require(re.fullmatch('[0-9a-f]{40}',oid),'object_identity');seen=set()
  for e in entries:
   require(set(e)=={'name','mode','type','oid'},'entry_shape')
   require(isinstance(e['name'],str) and e['name'] not in ('','.','..') and '/' not in e['name'] and '\0' not in e['name'] and e['name'] not in seen,'entry_name');seen.add(e['name'])
   require(e['mode'] in modes and e['type']==modes[e['mode']] and re.fullmatch('[0-9a-f]{40}',e['oid']),'entry_type')
   require(e['type']!='tree' or e['oid'] in objects,'missing_subtree')
  require(entries==sorted(entries,key=lambda e:(e['name']+('/' if e['type']=='tree' else '')).encode()),'tree_order')
  raw=payload(entries);require(hashlib.sha1(b'tree '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==oid,'git_tree_hash')
 commits={x['oid']:x for x in data['commits']};require(len(commits)==len(data['commits']) and commits,'commit_duplicates_or_empty')
 for oid,x in commits.items():
  require(set(x)=={'oid','tree','parents','committer_date'} and re.fullmatch('[0-9a-f]{40}',oid) and x['tree'] in objects,'commit_shape')
  require(all(p in commits for p in x['parents']) and len(x['parents'])==len(set(x['parents'])),'missing_parent')
 visited=set();active=set()
 def visit(oid):
  require(oid in commits,'unknown_head');require(oid not in active,'parent_cycle')
  if oid in visited:return
  active.add(oid)
  for parent in commits[oid]['parents']:visit(parent)
  active.remove(oid);visited.add(oid)
 for head in data['heads'].values():visit(head)
 require(visited==set(commits),'unreachable_commit')
 used=set()
 def walk(oid,prefix='',stack=()):
  require(oid not in stack,'tree_cycle');used.add(oid);out={}
  for e in objects[oid]:
   path=prefix+e['name'];out[path]={k:e[k] for k in ('mode','type','oid')}
   if e['type']=='tree':out.update(walk(e['oid'],path+'/',stack+(oid,)))
  return out
 roots={x['tree'] for x in commits.values()};trees={oid:walk(oid) for oid in roots};require(used==set(objects),'unreachable_tree_object')
 sources={x['oid']:x for x in data['root_sources']};require(len(sources)==len(data['root_sources']) and set(sources)==roots,'root_source_coverage')
 for oid,row in sources.items():
  require(set(row)=={'oid','source_sha256','entries','commits'} and re.fullmatch('[0-9a-f]{64}',row['source_sha256']),'source_binding_shape')
  require(row['entries']==len(trees[oid]),'truncated_tree_inventory')
  require(set(row['commits'])=={c for c,x in commits.items() if x['tree']==oid} and len(row['commits'])==len(set(row['commits'])),'tree_commit_mapping')
 current=trees[commits[data['heads']['main']]['tree']]
 variants={(p,e['oid']) for t in trees.values() for p,e in t.items() if e['type']=='blob'}
 main_variants={(p,e['oid']) for p,e in current.items() if e['type']=='blob'};extra=variants-main_variants
 paths=sorted({p for p,_ in variants});controllers=[p for p in paths if 't500' in p.lower()]
 return {'artifact_id':'reiyah.takeover-source-lineage.result','version':'0.1.0','scope':'Two advertised public heads and their retained complete parent closure; not private or unadvertised refs','public_heads':data['heads'],'commits':len(commits),'distinct_root_trees':len(roots),'verified_git_tree_objects':len(objects),'main_blob_paths':len(main_variants),'historical_blob_paths':len(paths),'historical_blob_variants':len(variants),'python_blob_variants':len({x for x in variants if x[0].endswith('.py')}),'additional_historical_python_variants':sorted([{'path':p,'oid':oid} for p,oid in extra if p.endswith('.py')],key=lambda x:(x['path'],x['oid'])),'additional_historical_blob_variants':sorted([{'path':p,'oid':oid} for p,oid in extra],key=lambda x:(x['path'],x['oid'])),'T500RS_paths':controllers,'required_controller_path_present':any(p.endswith('examples/manual_control_T500RS.py') for p in paths),'release_capture_binding_established':False,'readiness_model_admitted':False,'Gate_A_operator_accepted':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--inventory',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 pathlib.Path(a.output).write_text(json.dumps(audit(load(a.inventory)),indent=2)+'\n')
