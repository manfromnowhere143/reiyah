"""Resolve every supplementary timer directly from its retained source bytes."""
import argparse
from collections import Counter
from datetime import datetime,timezone
from fractions import Fraction
import hashlib,json
from pathlib import Path
import tarfile,time


def need(ok,message):
    if not ok:raise ValueError(message)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(raw):return json.loads(raw,parse_float=Fraction)


def collect(value):
    pending=[('',value)];out={}
    while pending:
        prefix,node=pending.pop()
        if isinstance(node,dict):
            for key,child in node.items():
                field=prefix+'/'+key
                if isinstance(child,(dict,list)):pending.append((field,child))
                elif 'seconds' in key and child is not None:
                    need(type(child) in (int,str,Fraction),'Unexpected source timer type')
                    quantity=Fraction(child);need(quantity>=0,'Negative timer');out[field]=quantity
        elif isinstance(node,list):
            pending.extend((prefix+'/'+str(i),child) for i,child in enumerate(node))
    return out


def verify(snapshot,report_path):
    tick=time.perf_counter();frozen=load((snapshot/'FREEZE.json').read_text());report=load(report_path.read_text())
    source=snapshot/'inputs';values={};roles={};expected={};owners={}
    for b in frozen['inputs']:
        path=source/b['path'];need(path.is_file() and path.stat().st_size==b['bytes'] and sha(path)==b['sha256'],
                                 'Bound supplemental source differs')
        roles[b['path']]=b['role']
        if path.suffix=='.json':values[b['path']]=load(path.read_text())
        if b['role']=='owner_phase':owners[values[b['path']]['stage']]=values[b['path']]
    for b in frozen['implementation']:
        path=Path(b['path']);need(path.stat().st_size==b['bytes'] and sha(path)==b['sha256'],'Implementation binding differs')
    def add(name,field,value,kind,owner=None):
        key=(name,field);need(key not in expected,'Duplicate source timer');expected[key]=(Fraction(value),kind,owner)
    for name,role in roles.items():
        if role=='unwrapped_reader_attempts':
            for i,row in enumerate(values[name]['attempts']):add(name,f'/attempts/{i}/seconds',row['seconds'],'duration_only')
        elif role=='unwrapped_physical_view':add(name,'/seconds',values[name]['seconds'],'duration_only')
        elif role.startswith('nested:'):
            owner=role.split(':')[1]
            for field,value in collect(values[name]).items():add(name,field,value,'nested_reference',owner)
        elif role.startswith('nested_stdout:'):
            owner=role.split(':')[1]
            for i,line in enumerate((source/name).read_text().splitlines()):
                try:decoded=load(line)
                except json.JSONDecodeError:continue
                for field,value in collect(decoded).items():add(name,f'/line/{i}'+field,value,'stdout_nested_reference',owner)
        elif role in ('published_snapshot_alias','published_snapshot_and_failed_launch'):
            for field,value in collect(values[name]).items():
                direct=role=='published_snapshot_and_failed_launch' and field in (
                    '/startup_failure/tool_wall_seconds','/startup_failure/secondary_result_view_tool_wall_seconds')
                add(name,field,value,'tool_duration_only' if direct else 'published_snapshot_reference')
        elif role=='storage_recovery':add(name,'/seconds',values[name]['seconds'],'nested_reference','storage-recovery-01')
        else:need(role in ('owner_phase','synthetic_archive'),'Unknown source role')
    manifest=values['private/storage-recovery-01/COMPLETED.json']
    archive=source/'private/storage-recovery-01/SYNTHETIC_OUTPUTS.tar.gz'
    need(sha(archive)==manifest['archive_sha256'],'Archive hash differs')
    archive_entries={r['path']:r for r in manifest['files']};checked_members=0
    with tarfile.open(archive,'r:gz') as stream:
        members=stream.getmembers();need(len({m.name for m in members})==len(members),'Duplicate archive member')
        for member in members:
            need(member.isfile() and member.name in archive_entries,'Unlisted archive object')
            raw=stream.extractfile(member).read();entry=archive_entries[member.name]
            need(len(raw)==entry['bytes'] and hashlib.sha256(raw).hexdigest()==entry['sha256'],'Archived bytes differ')
            checked_members+=1
            if member.name.endswith(('/analysis/RESULTS.json','/verification/VERIFICATION.json')):
                owner=Path(member.name).parts[1]
                for field,value in collect(load(raw)).items():
                    add('archive:'+member.name,field,value,'archived_synthetic_nested_reference',owner)
    need(checked_members==len(archive_entries),'Missing archive member')
    actual={}
    for row in report['timers']:
        key=(row['source'],row['field']);need(key not in actual,'Repeated reported timer')
        need(row['added_to_outer_union'] is False,'Nested timer added to outer union')
        need(row['owner_phase'] is None or row['owner_phase'] in owners,'Unknown owning process')
        actual[key]=(Fraction(row['seconds']),row['accounting'],row['owner_phase'])
    need(actual==expected,'Timer inventory or exact value differs')
    direct=[v[0] for v in actual.values() if v[1]=='duration_only']
    tool=[v[0] for v in actual.values() if v[1]=='tool_duration_only']
    need(len(direct)==report['additional_reader_duration_only_records']==4,'Reader probe count differs')
    need(len(tool)==report['failed_tool_duration_only_records']==2,'Failed tool count differs')
    need(sum(direct)==Fraction(report['additional_reader_duration_token_sum_seconds']),'Rational reader sum differs')
    need(sum(tool)==Fraction(report['failed_tool_duration_token_sum_seconds']),'Rational tool sum differs')
    need(report['new_outer_intervals']==[] and report['no_supplemental_duration_added_to_outer_union'] is True,
         'Supplement added an unobserved interval')
    need(report['freeze_sha256']==sha(snapshot/'FREEZE.json') and report['cutoff_utc']==frozen['cutoff_utc'],
         'Snapshot identity differs')
    need('/Users/' not in report_path.read_text() and 'https://' not in report_path.read_text(),'Private path or URL in report')
    return {'artifact_id':'reiyah.mission-costs.supplement-verification','version':'0.1.0',
            'report_sha256':sha(report_path),'freeze_sha256':sha(snapshot/'FREEZE.json'),
            'timer_references_checked':len(actual),'archive_members_checked':checked_members,
            'all_source_values_and_inventory_match':True,'rational_duration_sums_match':True,
            'outer_union_unchanged':True,'independent_scientific_replication':False,
            'seconds':time.perf_counter()-tick,'verifier_sha256':sha(Path(__file__))}


def main():
    p=argparse.ArgumentParser();p.add_argument('--snapshot',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=verify(a.snapshot,a.report)
    with a.output.open('x') as stream:json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps(result))


if __name__=='__main__':main()
