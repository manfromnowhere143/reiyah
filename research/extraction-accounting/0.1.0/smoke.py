"""Optional CPU integration check on authored tiny videos; no dataset/model.

Requires an installed FFmpeg with lavfi/color, FFV1, Matroska and JPEG support.
All commands, process logs, inputs, plans and results stay in a new directory.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

import extract


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact-root',type=Path,required=True)
    parser.add_argument('--ffmpeg',type=Path,required=True)
    args=parser.parse_args()
    root=args.artifact_root.absolute(); root.mkdir(parents=True,exist_ok=False)
    ffmpeg=args.ffmpeg.resolve(strict=True)
    commands=[]

    def invoke(name,argv):
        with (root/(name+'.stdout.txt')).open('xb') as out, (root/(name+'.stderr.txt')).open('xb') as err:
            result=subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=out,stderr=err,timeout=30,check=False)
        commands.append({'name':name,'argv':argv,'returncode':result.returncode,
                         'stdout':extract.fingerprint(root/(name+'.stdout.txt')),
                         'stderr':extract.fingerprint(root/(name+'.stderr.txt'))})
        extract.write_new(root/(name+'.command.json'),commands[-1])
        return result.returncode

    extract.require(invoke('ffmpeg-version',[str(ffmpeg),'-version'])==0,'FFmpeg version failed')
    for role,color in (('camera','red'),('gaze','blue')):
        argv=[str(ffmpeg),'-nostdin','-n','-hide_banner','-loglevel','error','-f','lavfi',
              '-i',f'color=c={color}:s=32x32:r=2:d=2','-threads','1','-c:v','ffv1',str(root/(role+'.mkv'))]
        extract.require(invoke('generate-'+role,argv)==0,'Authored video generation failed')
    (root/'corrupt.mkv').write_bytes(b'Authored invalid media; no third-party payload.\n')
    results=[]
    cases=(('complete',2,'gaze.mkv',0,None),
           ('equally-short',3,'gaze.mkv',3,'frame_membership_mismatch'),
           ('extra-frames',1,'gaze.mkv',3,'frame_membership_mismatch'),
           ('corrupt-gaze',2,'corrupt.mkv',3,'extraction_process_failed'),
           ('missing-gaze',2,'absent.mkv',3,'source_missing'))
    for name,expected,gaze_name,exit_code,reason in cases:
        plan={'artifact_id':'reiyah.extraction-plan','version':extract.VERSION,'fps':'1',
              'clips':[{'id':'authored','expected_frames':expected}]}
        clip=plan['clips'][0]
        for role,filename in (('camera','camera.mkv'),('gaze',gaze_name)):
            source=root/filename
            digest=extract.fingerprint(source if source.exists() else root/'gaze.mkv')['sha256']
            clip[role]={'path':str(source),'sha256':digest}
        plan_path=root/(name+'.plan.json'); extract.write_new(plan_path,plan)
        output=root/(name+'-output')
        actual=invoke(name,[sys.executable,'-B',str(Path(extract.__file__).resolve()),
                           '--plan',str(plan_path),'--plan-sha256',extract.sha(plan_path.read_bytes()),
                           '--output',str(output),'--ffmpeg',str(ffmpeg)])
        extract.require(actual==exit_code,'Unexpected extraction process status: '+name)
        raw=(output/'ledger.json').read_bytes(); ledger=extract.decode(raw)
        reasons=[s['reason'] for c in ledger['clips'] for s in c['streams'].values()]
        pairs=None
        if reason is None:
            pairs=extract.require_complete(plan,output,extract.sha(raw))
            extract.require(len(pairs)==2,'Unexpected authored pair count')
        else:
            extract.require(ledger['accounting_status']=='blocked' and reason in reasons,'Expected rejection missing')
            try:
                extract.require_complete(plan,output,extract.sha(raw))
            except extract.Invalid:
                pass
            else:
                raise extract.Invalid('Blocked run exposed pairs')
        results.append({'case':name,'returncode':actual,'expected_reason':reason,'observed_reasons':reasons,
                        'frame_pairs':None if pairs is None else len(pairs),
                        'ledger_sha256':extract.sha(raw),'status':'passed'})
    summary={'artifact_id':'reiyah.extraction-authored-smoke','version':extract.VERSION,
             'ffmpeg':{'path':str(ffmpeg),**extract.fingerprint(ffmpeg)},'cases':results,
             'measurement_status':'not_performed','physical_synchronization':'not_established',
             'scope':'Authored CPU decoding/accounting controls only; no historical experiment rerun.'}
    extract.write_new(root/'summary.json',summary)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
