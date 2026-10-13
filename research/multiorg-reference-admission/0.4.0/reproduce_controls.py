#!/usr/bin/env python3
"""Replay authored controls; no empirical image or detector forward passes."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess

def main():
    ap=argparse.ArgumentParser()
    for name in ('parser-python','runtime-python','graph','output'):ap.add_argument('--'+name,required=True)
    ap.add_argument('--source',help='Optional exact original ONNX for five static graph controls; never executed')
    a=ap.parse_args();packet=Path(__file__).resolve().parent;root=Path(a.output).resolve()
    graph=Path(a.graph).resolve()
    if hashlib.sha256(graph.read_bytes()).hexdigest()!='efdf18c9029db8dca26a70de8103920f18501fbf7ba94fe4ae74ea1b6a43ee77':
        raise ValueError('exact static graph metadata required')
    root.mkdir(parents=True,exist_ok=False)
    for group,names in {'implementation':['build_correction.py','qualify_correction.py','taps.json'],
                        'execution':['run_probe.py','test_run_probe.py','trace_support.py'],
                        'reference':['check_correction.py','test_reference.py','THIRD_PARTY_NOTICES.md']}.items():
        (root/group).mkdir()
        for name in names:shutil.copyfile(packet/name,root/group/name)
    shutil.copyfile(graph,root/'execution/original-graph.json')
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
    env['REIYAH_GRAPH_DESCRIPTION']=str(root/'execution/original-graph.json')
    commands=[('mask',[a.parser_python,'-B',str(root/'implementation/qualify_correction.py'),'--runtime',a.runtime_python,'--output',str(root/'implementation/controls')]),
              ('capture',[a.runtime_python,'-B',str(root/'execution/test_run_probe.py')]),
              ('reference',[a.runtime_python,'-B',str(root/'reference/test_reference.py')])]
    if a.source:commands[0][1].extend(['--source',str(Path(a.source).resolve())])
    outcomes=[]
    for name,cmd in commands:
        with (root/(name+'.stdout')).open('x') as out,(root/(name+'.stderr')).open('x') as err:
            r=subprocess.run(cmd,cwd=root,env=env,stdout=out,stderr=err,timeout=120)
        outcomes.append({'name':name,'command':cmd,'returncode':r.returncode})
        if r.returncode:break
    passed=len(outcomes)==3 and all(x['returncode']==0 for x in outcomes)
    counts={}
    if passed:
        counts['mask']=json.loads((root/'implementation/controls/QUALIFICATION.json').read_text())['count']
        counts['capture']=json.loads((root/'execution/QUALIFICATION_worker.json').read_text())['count']
        match=re.search(r'Ran (\d+) tests', (root/'reference.stderr').read_text())
        if not match:raise ValueError('reference test count missing')
        counts['reference']=int(match[1])
        passed=counts=={'mask':20 if a.source else 15,'capture':20,'reference':15}
    receipt={'status':'passed' if passed else 'failed','actual_controls':sum(counts.values()),'counts':counts,'commands':outcomes,
             'scope':'Authored tiny ONNX fixture, mocked capture and direct reference controls; zero empirical model forwards.'}
    (root/'RESULT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'status':receipt['status'],'actual_controls':receipt['actual_controls']}))
    if not passed:raise SystemExit(1)

if __name__=='__main__':main()
