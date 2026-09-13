"""Exercise Engine output separation using complete synthetic workflows only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source_identity(root):
    paths=set((root/'tools').glob('perception*.py'))
    for p in (root/'tools').glob('perception_*'):
        if p.is_dir():paths.update(p.glob('*.py'))
    paths.update((root/'tests').glob('test_perception*.py'))
    for name in ('rehearsal','assistance','operands','reviewed-operands','discovery','observation'):
        paths.update(p for p in (root/'research'/('perception-'+name)/'0.1.0').rglob('*') if p.is_file())
    rows=[{'path':p.relative_to(root).as_posix(),'byte_size':p.stat().st_size,'sha256':digest(p.read_bytes())} for p in sorted(paths)]
    return digest(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()),rows


def inventory(root):
    return {p.relative_to(root).as_posix():
            ({'kind':'file','sha256':digest(p.read_bytes()),'byte_size':p.stat().st_size} if p.is_file()
             else {'kind':'directory'}) for p in sorted(root.rglob('*'))}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root',type=Path,required=True)
    p.add_argument('--source-sha256',required=True)
    p.add_argument('--expect',choices=('vulnerable','protected'),required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();root=args.source_root.resolve()
    source,identities=source_identity(root)
    if source!=args.source_sha256:raise SystemExit('Selected source closure differs')
    args.output.mkdir()
    sys.path.insert(0,str(root))
    from tools import perception_binding as binding,perception_admission as admission
    from tools import perception_assistance as assistance,perception_rehearsal as rehearsal
    from tools import perception_operands as operands,perception_reviewed_operands as reviewed
    from tools.perception_decision.contract import Invalid,encoded
    from tools.perception_observation import package
    from tests.test_perception_reviewed_operands import prepared_inputs
    from tests.test_perception_observation import fixture
    from tests.test_perception_admission import save

    diagnostics={'binding':'BINDING_PRIVATE_OUTPUT','admission':'ADMISSION_PRIVATE_OUTPUT',
                 'rehearsal':'REHEARSAL_OUTPUT','assistance':'ASSISTANCE_OUTPUT',
                 'operands':'OPERANDS_OUTPUT','reviewed':'REVIEWED_OUTPUT','observation':'OBS_CUSTODY'}
    reports=[];skipped=[]
    with tempfile.TemporaryDirectory(prefix='synthetic-separation-',dir=args.output) as temp:
        work=Path(temp);probe=work/'case-probe';probe.mkdir()
        supports_case_alias=probe.with_name('CASE-PROBE').exists() and probe.with_name('CASE-PROBE').samefile(probe)
        kinds=[(k,'package') for k in diagnostics if k!='observation']+[(k,'assistance') for k in ('operands','reviewed')]
        for kind,target_role in kinds:
            for form in ('direct','symlink','case_alias'):
                name=f'{kind}-{target_role}-{form}'
                if form=='case_alias' and not supports_case_alias:
                    skipped.append({'case':name,'reason':'Filesystem does not resolve this case alias'});continue
                base=work/name;base.mkdir();inputs=prepared_inputs(base)
                request=json.loads(inputs['binding_request'].read_bytes())
                evidence=Path(request['package']['path']);seal=request['package']['seal_sha256']
                target=evidence if target_role=='package' else inputs['assistance']
                selected=target
                if form=='symlink':
                    selected=base/'destination-alias';selected.symlink_to(target,target_is_directory=True)
                elif form=='case_alias':
                    selected=target.with_name(target.name.upper());assert selected.samefile(target)
                output=selected/'unexpected-private-output'
                before=inventory(target);package.verify(evidence,seal)
                operation='succeeded';returned=None
                try:
                    if kind=='binding':returned=binding.run(inputs['binding_request'],inputs['binding_request_sha256'],output)
                    elif kind=='admission':returned=admission.run(inputs['admission_request'],inputs['admission_request_sha256'],output)
                    elif kind=='rehearsal':returned=rehearsal.run(inputs['binding_request'],inputs['binding_request_sha256'],'c'*32,output)
                    elif kind=='assistance':returned=assistance.run(inputs['binding_request'],inputs['binding_request_sha256'],'configuration-2',output)
                    elif kind=='operands':returned=operands.run(inputs['binding_request'],inputs['binding_request_sha256'],inputs['assistance'],inputs['preparation_sha256'],output)
                    else:returned=reviewed.run(output,**inputs)
                except Invalid as exc:operation=exc.code
                after=inventory(target);validation='verified'
                try:
                    if target_role=='package':package.verify(evidence,seal)
                    else:operands.load_assistance(inputs['assistance'],inputs['preparation_sha256'],inputs['binding_request_sha256'])
                except Invalid as exc:validation=exc.code
                rows={'case':name,'workflow':kind,'target':target_role,'form':form,'operation':operation,
                      'target_after':validation,'target_unchanged':before==after,'output_exists':os.path.lexists(output),
                      'added_entries':sorted(set(after)-set(before)),
                      'changed_original_entries':sorted(k for k in before if k not in after or before[k]!=after[k]),
                      'original_entries':len(before),'package_seal_sha256':seal}
                reports.append(rows)
                capture=args.output/name;capture.mkdir()
                (capture/'before-inventory.json').write_bytes(encoded(before))
                (capture/'after-inventory.json').write_bytes(encoded(after))
                if returned is not None:(capture/'returned.json').write_bytes(encoded(returned))
        for form in ('direct','symlink','case_alias'):
            name='observation-new-package-'+form
            if form=='case_alias' and not supports_case_alias:
                skipped.append({'case':name,'reason':'Filesystem does not resolve this case alias'});continue
            base=work/name;base.mkdir();request=fixture(base);output=base/'observations'
            selected=output
            if form=='symlink':
                selected=base/'destination-alias';selected.symlink_to(output,target_is_directory=True)
            elif form=='case_alias':selected=output.with_name('OBSERVATIONS')
            private=selected/'private-custody.json';operation='succeeded';returned=None
            try:returned=package.build(request,output,private)
            except Invalid as exc:operation=exc.code
            validation='unsealed'
            if returned is not None:
                try:package.verify(output,returned['seal_sha256']);validation='verified'
                except Invalid as exc:validation=exc.code
            contents=inventory(output)
            reports.append({'case':name,'workflow':'observation','target':'new-package','form':form,
                            'operation':operation,'target_after':validation,'output_exists':output.exists(),
                            'private_output_exists':os.path.lexists(private),'completion_seal_exists':(output/'SEAL.json').exists(),
                            'files_written':sorted(k for k,v in contents.items() if v['kind']=='file'),
                            'directories_created':sorted(k for k,v in contents.items() if v['kind']=='directory')})
    matches=[]
    for row in reports:
        vulnerable=args.expect=='vulnerable' and row['form']=='case_alias'
        if row['workflow']=='observation':
            valid=(row['operation']=='succeeded' and row['target_after']=='OBS_FILE_SET' and row['private_output_exists'] and row['completion_seal_exists']) if vulnerable else (
                row['operation']==diagnostics['observation'] and not row['files_written'] and not row['completion_seal_exists'] and not row['private_output_exists'])
        else:
            valid=(row['operation']=='succeeded' and row['target_after']!='verified' and not row['target_unchanged'] and row['output_exists']) if vulnerable else (
                row['operation']==diagnostics[row['workflow']] and row['target_after']=='verified' and row['target_unchanged'] and not row['output_exists'])
            valid=valid and not row['changed_original_entries']
        matches.append(valid)
    result={'artifact_id':'reiyah.output-separation.reproduction','version':'0.1.0','source_sha256':source,
            'expected_state':args.expect,'cases':reports,'skipped_cases':skipped,'expectation_met':all(matches),
            'unexpected_cases':[r['case'] for r,match in zip(reports,matches) if not match],
            'scope':'Complete synthetic source/review controls only; no actual human judgments or real package mutations',
            'actual_human_records_created':0}
    (args.output/'SOURCE_BINDINGS.json').write_bytes(encoded(identities))
    (args.output/'RESULTS.json').write_bytes(encoded(result))
    if source_identity(root)[0]!=source:raise SystemExit('Source changed during reproduction')
    print(json.dumps({'cases':len(reports),'skipped':len(skipped),'expectation_met':all(matches),
                      'unexpected_cases':result['unexpected_cases'],'results_sha256':digest((args.output/'RESULTS.json').read_bytes())},sort_keys=True))
    return 0 if all(matches) else 1


if __name__=='__main__':raise SystemExit(main())
