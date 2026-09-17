"""Replay in a fresh private directory using only the 64 admitted development exports."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
from common import ROOT, VERSION, file_digest, need, put, utc


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',required=True,help='Closed reference-corrections report root')
    parser.add_argument('--output',required=True,help='New private directory outside Git and the source packet')
    args=parser.parse_args()
    source=Path(args.source).resolve(); area=Path(args.output).resolve()
    need(not area.is_relative_to(source) and not area.is_relative_to(ROOT),'Do not write into source custody or Git')
    area.mkdir()
    for name in ['inputs','oracle','runs','logs','sources']:
        (area/name).mkdir()
    (area/'candidate').symlink_to(ROOT,target_is_directory=True)
    code=Path(__file__).resolve().parent
    for name in ['PLAN.json','REFINEMENT_PLAN.json']:
        with (area/name).open('xb') as output:
            output.write((code/name).read_bytes())
    put(area/'SESSION.json',{'artifact_id':'reiyah.correction-observation.reproduction','version':VERSION,
        'started_utc':utc(),'source':str(source),'code_root':str(ROOT),
        'scope':'Replay of exposed development; original protocol dates are retained, not new preregistration.'})
    def run(script,*arguments):
        with (area/'logs'/(script+'.txt')).open('x') as output:
            subprocess.run([sys.executable,'-B',str(code/script),*map(str,arguments)],
                           stdout=output,stderr=subprocess.STDOUT,check=True,cwd=ROOT)
        print(script+' completed',flush=True)
    def bind(path,files):
        put(area/path,{'artifact_id':'reiyah.correction-observation.reproduction-freeze','version':VERSION,
            'frozen_utc':utc(),'bindings':[{'path':str(p.relative_to(area)),'sha256':file_digest(p),
                                         'bytes':p.stat().st_size} for p in files]})
    run('prepare.py',area,source)
    files=[area/n for n in ['PLAN.json','inputs/visible.json','sources/BINDINGS.json','PREPARATION.json']]
    files+=sorted((area/'candidate/research/correction-observation/0.1.0').glob('*.py'))
    files+=sorted((area/'candidate/tools/perception_revision').glob('*.py'))
    files+=sorted((area/'candidate/tools/perception_decision').glob('*.py'))
    files+=sorted((area/'candidate/research/perception-revision/0.1.0').glob('*.schema.json'))
    files+=sorted((area/'oracle').glob('*.json'))
    bind('FREEZE.json',files)
    run('experiment.py','--run',area)
    run('verify.py',area)
    run('analyze.py',area)
    files=[area/n for n in ['REFINEMENT_PLAN.json','FREEZE.json','runs/assay-01/RESULTS.json',
                           'runs/analysis-01/SUMMARY.json','runs/analysis-01/FULL_OBSERVATIONS.json']]
    files+=sorted((area/'candidate/research/correction-observation/0.1.0').glob('*.py'))
    bind('REFINEMENT_FREEZE.json',files)
    run('refine.py',area)
    run('verify_analysis.py',area)
    print('Complete: '+str(area),flush=True)


if __name__=='__main__':
    main()
