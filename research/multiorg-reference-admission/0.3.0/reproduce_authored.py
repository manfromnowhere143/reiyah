"""Stage and run authored controls only. No model/image acquisition or inference."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True,help='New private directory for fixtures and logs')
    args=parser.parse_args()
    source=Path(__file__).resolve().parent
    owner=args.output.absolute()
    owner.mkdir(mode=0o700)
    for directory in ('inference','protocol','qualification','projection-qualification','verification','authored-inputs'):
        (owner/directory).mkdir()
    pairs=[(source.parent/'0.2.0/run_pair.py','inference/run_pair.py'),
           (source.parent/'0.2.0/protocol.json','protocol/scientific-base.json'),
           (source.parent/'0.2.3/diagnose.py','inference/diagnose.py'),
           (source.parent/'0.2.3/test_diagnose.py','qualification/test_diagnose.py')]
    pairs += [(source/name,'inference/'+name) for name in ('analysis_pair.py','projection.py')]
    pairs += [(source/'contract.json','protocol/analysis-projection.json'),
              (source/'projection.py','projection-qualification/projection.py'),
              (source/'test_projection.py','projection-qualification/test_projection.py'),
              (source/'test_analysis_pair.py','qualification/test_analysis_pair.py'),
              (source/'check_analysis.py','verification/check_analysis.py'),
              (source/'test_check_analysis.py','verification/test_check_analysis.py')]
    for src,dst in pairs:shutil.copyfile(src,owner/dst)
    def binding(path):return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    placeholders={}
    for name in ('image','faster','yolo'):
        path=owner/'authored-inputs'/name
        path.write_bytes(b'Authored placeholder. Never executed as a model or read as a TIFF.\n')
        placeholders[name]=binding(path)
    contract=json.loads((source/'contract.json').read_text())
    manifest={'protocol':binding(owner/'protocol/scientific-base.json'),
              'images':[{'id':contract['image_id'],'source':placeholders['image']}],
              'models':{name:placeholders[name] for name in ('faster','yolo')},
              'limits':{'wall_seconds':600,'memory_bytes':3221225472,
                        'max_tiles_per_image':512,'max_raw_boxes_per_image':200000}}
    (owner/'inference/pilot-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    results=[]
    for name in ('qualification/test_diagnose.py','projection-qualification/test_projection.py',
                 'qualification/test_analysis_pair.py','verification/test_check_analysis.py'):
        start=time.monotonic()
        proc=subprocess.run([sys.executable,'-B',str(owner/name)],cwd=owner,capture_output=True,timeout=120)
        stem=Path(name).stem
        (owner/(stem+'.stdout')).write_bytes(proc.stdout)
        (owner/(stem+'.stderr')).write_bytes(proc.stderr)
        results.append({'test':name,'returncode':proc.returncode,'wall_seconds':time.monotonic()-start,
                        'source_sha256':hashlib.sha256((owner/name).read_bytes()).hexdigest()})
    report={'status':'pass' if all(row['returncode']==0 for row in results) else 'fail',
            'scope':'Authored controls only; mocked model/TIFF sessions; no empirical model execution',
            'python':sys.executable,'tests':results}
    (owner/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
    return 0 if report['status']=='pass' else 1

if __name__=='__main__':raise SystemExit(main())
