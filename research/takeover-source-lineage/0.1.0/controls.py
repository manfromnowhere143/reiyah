"""Deliberate tree corruption and incomplete history must not pass the audit."""
import copy,json,pathlib,tempfile
import audit
ROOT=pathlib.Path(__file__).parent;base=audit.load(ROOT/'inventory.json');checks=[]
def rejected(name,expected,mutate):
 data=copy.deepcopy(base);mutate(data)
 try:audit.audit(data)
 except ValueError as error:
  if str(error)!=expected:raise AssertionError((name,expected,str(error))) from error
  checks.append({'control':name,'rejected_for':str(error)})
 else:raise AssertionError(name)
rejected('alter_tree_entry_name','tree_order',lambda d:d['tree_objects'][next(iter(d['tree_objects']))][0].update(name='changed-name'))
def corrupt_blob(data):
 for entries in data['tree_objects'].values():
  for entry in entries:
   if entry['type']=='blob':
    entry['oid']=('0' if entry['oid'][0]!='0' else '1')+entry['oid'][1:];return
 raise AssertionError('no_blob')
rejected('corrupt_blob_identity','git_tree_hash',corrupt_blob)
rejected('omit_referenced_tree','commit_shape',lambda d:d['tree_objects'].pop(next(iter(d['tree_objects']))))
rejected('omit_parent_commit','missing_parent',lambda d:d['commits'].pop(1))
rejected('forge_complete_entry_count','truncated_tree_inventory',lambda d:d['root_sources'][0].update(entries=d['root_sources'][0]['entries']-1))
rejected('omit_root_source','root_source_coverage',lambda d:d['root_sources'].pop())
rejected('invent_parent_cycle','parent_cycle',lambda d:d['commits'][0].update(parents=[d['commits'][0]['oid']]))
with tempfile.TemporaryDirectory() as tmp:
 path=pathlib.Path(tmp)/'duplicate.json';path.write_text('{"heads":{},"heads":{}}')
 try:audit.load(path)
 except ValueError as error:
  if str(error)!='duplicate_json_key':raise AssertionError(str(error)) from error
  checks.append({'control':'duplicate_json_key','rejected_for':str(error)})
 else:raise AssertionError('duplicate_json_key')
print(json.dumps({'artifact_id':'reiyah.takeover-source-lineage.controls','version':'0.1.0','passed':len(checks),'checks':checks},indent=2))
