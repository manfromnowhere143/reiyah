"""Account for declared additional timers without changing the frozen core."""
import argparse
from datetime import datetime,timezone,timedelta
from decimal import Decimal,InvalidOperation
import hashlib,json
from pathlib import Path
import shutil,tarfile


def require(ok,message):
    if not ok:raise ValueError(message)


def read(path):return json.loads(Path(path).read_text(),parse_float=Decimal)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()


def number(value):
    require(type(value) in (Decimal,int,str),'Non-exact timer token')
    try:v=Decimal(value)
    except InvalidOperation as exc:raise ValueError('Malformed timer') from exc
    require(v.is_finite() and v>=0,'Invalid timer');return v


def contained(inner,outer):
    values=[]
    for value in (outer['started_utc'],inner['started_utc'],inner['finished_utc'],outer['finished_utc']):
        parsed=datetime.fromisoformat(value)
        require(parsed.utcoffset()==timedelta(0),'Timer boundary is not UTC');values.append(parsed)
    return values==sorted(values)


def put(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2,sort_keys=True,default=lambda x:format(x,'f'));stream.write('\n')


def timers(value,pointer=''):
    out=[]
    if isinstance(value,dict):
        for key,child in value.items():
            path=pointer+'/'+key
            if isinstance(child,(dict,list)):out+=timers(child,path)
            elif 'seconds' in key and child is not None:
                out.append({'field':path,'seconds':format(number(child),'f')})
    elif isinstance(value,list):
        for i,child in enumerate(value):out+=timers(child,pointer+'/'+str(i))
    return out


def reference(source,field,seconds,kind,owner=None,state=None):
    return {'source':source,'field':field,'seconds':format(number(seconds),'f'),
            'accounting':kind,'owner_phase':owner,'state':state,'added_to_outer_union':False}


def archive_json(archive,manifest,member):
    rows={r['path']:r for r in manifest['files']};require(member in rows,'Unlisted archive member')
    require(not Path(member).is_absolute() and '..' not in Path(member).parts,'Unsafe archive member')
    with tarfile.open(archive,'r:gz') as handle:
        matches=[r for r in handle.getmembers() if r.name==member]
        require(len(matches)==1 and matches[0].isfile(),'Ambiguous or nonregular member')
        raw=handle.extractfile(matches[0]).read()
    require(len(raw)==rows[member]['bytes'] and hashlib.sha256(raw).hexdigest()==rows[member]['sha256'],
            'Archive member bytes differ')
    return json.loads(raw,parse_float=Decimal)


def freeze(root,output):
    require(not output.exists(),'Supplement snapshot exists');output.mkdir(parents=True)
    source=output/'inputs';source.mkdir()
    paths={
        'private/source-followup-01/nullable-reader-synthetic-01/RESULT.json':'unwrapped_reader_attempts',
        'private/source-followup-01/nullable-reader-synthetic-01/PHYSICAL_VIEW_RESULT.json':'unwrapped_physical_view',
        'private/cached-packet-audit-01/analysis/RESULTS.json':'nested:cached-audit-01',
        'private/cached-packet-audit-01/verification/VERIFICATION.json':'nested:cached-verify-01',
        'private/cached-packet-audit-01/followup/analysis/RESULTS.json':'nested:cached-followup-audit-01',
        'private/cached-packet-audit-01/followup/verification/VERIFICATION.json':'nested:cached-followup-verify-01',
        'private/policy-loss-envelope-01/analysis/RESULTS.json':'nested:envelope-analysis-01',
        'private/policy-loss-envelope-01/verification/VERIFICATION.json':'nested:envelope-verify-02',
        'private/storage-recovery-01/COMPLETED.json':'storage_recovery',
        'private/storage-recovery-01/SYNTHETIC_OUTPUTS.tar.gz':'synthetic_archive',
        'candidate/research/cached-packet-audit/0.1.0/summary.json':'published_snapshot_alias',
        'candidate/research/policy-loss-envelope/0.1.0/summary.json':'published_snapshot_and_failed_launch',
        'logs/cached-followup-controls-01.stdout':'nested_stdout:cached-followup-controls-01',
        'logs/envelope-controls-02.stdout':'nested_stdout:envelope-controls-02'}
    for n in (1,2,3):paths[f'logs/cached-synthetic-{n:02d}-COMPLETED.json']='owner_phase'
    for role in list(paths.values()):
        if role.startswith(('nested:','nested_stdout:')):
            phase=role.split(':',1)[1];paths['logs/'+phase+'-COMPLETED.json']='owner_phase'
    paths['logs/storage-recovery-01-COMPLETED.json']='owner_phase'
    bindings=[]
    for relative,role in sorted(paths.items()):
        path=root/relative;require(path.is_file() and not path.is_symlink(),'Supplement input absent')
        target=source/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
        require(sha(path)==sha(target),'Supplement copy differs')
        bindings.append({'path':relative,'role':role,'bytes':target.stat().st_size,'sha256':sha(target)})
    code=[]
    for path in [Path(__file__),Path(__file__).with_name('test_cost_supplement.py')]:
        target=output/path.name;shutil.copyfile(path,target)
        code.append({'path':str(path.resolve()),'bytes':path.stat().st_size,'sha256':sha(path)})
    record={'artifact_id':'reiyah.mission-costs.supplement-freeze','version':'0.1.0','cutoff_utc':utc(),
            'inputs':bindings,'implementation':code,'no_new_source_or_outcome_access':True}
    put(output/'FREEZE.json',record);print({'bindings':len(bindings)+len(code),'freeze_sha256':sha(output/'FREEZE.json')})


def check(snapshot,frozen):
    for row in frozen['inputs']:
        require(not Path(row['path']).is_absolute() and '..' not in Path(row['path']).parts,'Invalid supplement path')
        path=snapshot/'inputs'/row['path'];require(path.is_file() and not path.is_symlink()
            and path.stat().st_size==row['bytes'] and sha(path)==row['sha256'],'Supplement input changed')
    for row in frozen['implementation']:
        path=Path(row['path']);require(path.stat().st_size==row['bytes'] and sha(path)==row['sha256'],
                                      'Supplement implementation changed')


def reconcile(snapshot,frozen):
    source=snapshot/'inputs';rows=[];owners={}
    for binding in frozen['inputs']:
        if binding['role']=='owner_phase':
            value=read(source/binding['path']);owners[value['stage']]=value
    for binding in frozen['inputs']:
        path=source/binding['path'];name=binding['path'];role=binding['role']
        if role=='unwrapped_reader_attempts':
            for i,attempt in enumerate(read(path)['attempts']):
                rows.append(reference(name,f'/attempts/{i}/seconds',attempt['seconds'],'duration_only',state=attempt['state']))
        elif role=='unwrapped_physical_view':
            value=read(path);rows.append(reference(name,'/seconds',value['seconds'],'duration_only',state=value['state']))
        elif role.startswith('nested:'):
            owner=role.split(':')[1];value=read(path);outer=owners[owner]
            require(contained(value,outer),
                    'Nested record outside owner phase')
            rows += [reference(name,t['field'],t['seconds'],'nested_reference',owner) for t in timers(value)]
        elif role.startswith('nested_stdout:'):
            owner=role.split(':')[1]
            for i,line in enumerate(path.read_text().splitlines()):
                try:value=json.loads(line,parse_float=Decimal)
                except json.JSONDecodeError:continue
                rows += [reference(name,f'/line/{i}'+t['field'],t['seconds'],'stdout_nested_reference',owner)
                         for t in timers(value)]
        elif role=='published_snapshot_alias':
            rows += [reference(name,t['field'],t['seconds'],'published_snapshot_reference') for t in timers(read(path))]
        elif role=='published_snapshot_and_failed_launch':
            value=read(path)
            for t in timers(value):
                kind='tool_duration_only' if t['field'] in ('/startup_failure/tool_wall_seconds',
                     '/startup_failure/secondary_result_view_tool_wall_seconds') else 'published_snapshot_reference'
                rows.append(reference(name,t['field'],t['seconds'],kind,state='failed' if kind=='tool_duration_only' else None))
        elif role=='storage_recovery':
            value=read(path);require('storage-recovery-01' in owners and contained(value,owners['storage-recovery-01']),
                                     'Storage recovery timer lacks its containing phase')
            rows.append(reference(name,'/seconds',value['seconds'],'nested_reference','storage-recovery-01'))
        elif role in ('owner_phase','synthetic_archive'):pass
        else:raise ValueError('Unclassified supplemental input')
    archive=source/'private/storage-recovery-01/SYNTHETIC_OUTPUTS.tar.gz'
    manifest=read(source/'private/storage-recovery-01/COMPLETED.json')
    require(sha(archive)==manifest['archive_sha256'],'Archive identity differs')
    for entry in manifest['files']:
        member=entry['path']
        if not member.endswith(('/analysis/RESULTS.json','/verification/VERIFICATION.json')):continue
        owner=Path(member).parts[1];require(owner in owners,'Archived output lacks owner process')
        value=archive_json(archive,manifest,member)
        require(contained(value,owners[owner]),
                'Archived record outside owner phase')
        rows += [reference('archive:'+member,t['field'],t['seconds'],'archived_synthetic_nested_reference',owner)
                 for t in timers(value)]
    identities=[(r['source'],r['field']) for r in rows];require(len(set(identities))==len(identities),'Duplicate supplemental timer')
    require(all(r['owner_phase'] is None or r['owner_phase'] in owners for r in rows),'Unbound timer owner')
    direct=[r for r in rows if r['accounting']=='duration_only']
    tool=[r for r in rows if r['accounting']=='tool_duration_only']
    require(len(direct)==4 and len(tool)==2,'Supplemental duration allocation differs')
    return {'artifact_id':'reiyah.mission-costs.supplement','version':'0.1.0','cutoff_utc':frozen['cutoff_utc'],
        'freeze_sha256':sha(snapshot/'FREEZE.json'),'timers':rows,'new_outer_intervals':[],
        'additional_reader_duration_only_records':len(direct),
        'additional_reader_duration_token_sum_seconds':format(sum((number(r['seconds']) for r in direct),Decimal(0)),'f'),
        'failed_tool_duration_only_records':len(tool),
        'failed_tool_duration_token_sum_seconds':format(sum((number(r['seconds']) for r in tool),Decimal(0)),'f'),
        'no_supplemental_duration_added_to_outer_union':True,'nested_and_snapshot_values_not_additive':True,
        'full_economic_cost':None,'human_seconds':None,'reserved_images_closed':1433}


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--freeze-only',action='store_true');p.add_argument('--snapshot',type=Path);args=p.parse_args()
    if args.freeze_only:freeze(args.root.resolve(),args.output.resolve());return
    frozen=read(args.snapshot/'FREEZE.json');check(args.snapshot,frozen)
    report=reconcile(args.snapshot,frozen);args.output.mkdir(parents=True,exist_ok=False)
    put(args.output/'SUPPLEMENT.json',report);check(args.snapshot,frozen)
    print({'timer_references':len(report['timers']),'reader_duration_only':report['additional_reader_duration_only_records'],
           'failed_tool_durations':report['failed_tool_duration_only_records'],'report_sha256':sha(args.output/'SUPPLEMENT.json')})


if __name__=='__main__':main()
