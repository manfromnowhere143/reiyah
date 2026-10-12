#!/usr/bin/env python3
"""Post-execution validation controls; input/output mutations, never new science."""
import argparse, hashlib, json, pathlib, subprocess, sys, time
p=argparse.ArgumentParser();p.add_argument('--source',required=True,type=pathlib.Path);p.add_argument('--output',required=True,type=pathlib.Path);p.add_argument('--controls',required=True,type=pathlib.Path);a=p.parse_args()
a.controls.mkdir(exist_ok=False)
bad=a.controls/'altered-member.bin';raw=bytearray(a.source.read_bytes());raw[-1]^=1;bad.write_bytes(raw)
target=a.controls/'altered-result';target.mkdir();(target/'trace.jsonl').symlink_to((a.output/'trace.jsonl').resolve());r=json.loads((a.output/'result.json').read_text());r['aggregates']['all']['mean_delta']='0/1';(target/'result.json').write_text(json.dumps(r,indent=2)+'\n')
base=pathlib.Path(__file__).resolve().parent
commands=[('producer_changed_source',base/'reproduce.py',bad,a.controls/'must-not-exist',2,'compressed source identity differs'),('checker_changed_source',base/'checker.py',bad,a.output,1,'source hash mismatch'),('checker_changed_result',base/'checker.py',a.source,target,1,'aggregate metrics mismatch')]
records=[]
for name,script,source,output,code,reason in commands:
 argv=[sys.executable,'-B',str(script),'--source',str(source),'--output',str(output)];start=time.monotonic();run=subprocess.run(argv,capture_output=True,timeout=120)
 (a.controls/(name+'.stdout')).write_bytes(run.stdout);(a.controls/(name+'.stderr')).write_bytes(run.stderr)
 record={'name':name,'exit':run.returncode,'expected_exit':code,'expected_reason':reason,'stderr':run.stderr.decode(),'seconds':time.monotonic()-start,'passed':run.returncode==code and reason in run.stderr.decode()};records.append(record)
(a.controls/'result.json').write_text(json.dumps({'controls':records,'all_passed':all(r['passed'] for r in records)},indent=2)+'\n')
print(json.dumps(records,indent=2));raise SystemExit(0 if all(r['passed'] for r in records) else 1)
