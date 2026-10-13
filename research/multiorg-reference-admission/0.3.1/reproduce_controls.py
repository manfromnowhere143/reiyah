#!/usr/bin/env python3
"""Replay authored controls with exact graph metadata; no empirical inference.

The graph metadata comes from inspect_graph.py applied to the pinned model.
The ONNX Runtime forward passes here use only the tiny authored fixture.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--parser-python',required=True)
    ap.add_argument('--runtime-python',required=True)
    ap.add_argument('--graph',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args(); packet=Path(__file__).resolve().parent; root=a.output.resolve()
    graph=a.graph.read_bytes()
    if hashlib.sha256(graph).hexdigest()!='efdf18c9029db8dca26a70de8103920f18501fbf7ba94fe4ae74ea1b6a43ee77':
        raise ValueError('exact graph metadata required; run pinned inspector first')
    root.mkdir(parents=True,exist_ok=False)
    for name in ('probe','review','trace','graph','candidate/research/multiorg-reference-admission/0.2.0'):
        (root/name).mkdir(parents=True,exist_ok=True)
    (root/'graph/GRAPH.json').write_bytes(graph)
    shutil.copyfile(packet.parent/'0.2.0/run_pair.py',root/'candidate/research/multiorg-reference-admission/0.2.0/run_pair.py')
    for group,names in [('probe',['reconstruct.py','test_reconstruct.py']),('review',['check_lineage.py','test_check_lineage.py']),('trace',['build_taps.py','trace_worker.py','qualify.py'])]:
        for name in names: shutil.copyfile(packet/name,root/group/name)
    commands=[('preprocessing',[a.runtime_python,'-B',str(root/'probe/test_reconstruct.py')]),
              ('lineage',[a.runtime_python,'-B',str(root/'review/test_check_lineage.py')]),
              ('capture',[a.parser_python,'-B',str(root/'trace/qualify.py'),'--runtime',a.runtime_python,'--output',str(root/'trace/controls')]),
              ('correction-order',[sys.executable,'-B',str(packet/'correction_order.py')])]
    results=[]
    for name,cmd in commands:
        with (root/(name+'.stdout')).open('w') as out,(root/(name+'.stderr')).open('w') as err:
            result=subprocess.run(cmd,cwd=root,stdout=out,stderr=err,timeout=120)
        results.append({'name':name,'command':cmd,'returncode':result.returncode})
        if result.returncode: break
    passed=len(results)==len(commands) and all(x['returncode']==0 for x in results)
    record={'status':'pass'if passed else 'fail','commands':results,'expected_authored_controls':34,
            'graph_metadata_sha256':hashlib.sha256(graph).hexdigest(),
            'scope':'Authored inputs plus exact static graph metadata. Only the tiny authored model executes; no empirical model/image inference or scientific result reproduction.'}
    (root/'RESULT.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'status':record['status'],'expected_authored_controls':34}))
    if not passed:raise SystemExit(1)

if __name__=='__main__':main()
