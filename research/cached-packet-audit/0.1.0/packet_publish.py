"""Publish selected authored scalars; never copy prediction or timing payloads."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

from packet_core import require
from packet_followup import check_bindings
from packet_run import check_freeze, put, read
from packet_view import sha


def main():
    p=argparse.ArgumentParser();p.add_argument('--area',type=Path,required=True);args=p.parse_args()
    area=args.area.resolve();here=Path(__file__).resolve().parent;base=area/'private/cached-packet-audit-01'
    follow=base/'followup';frozen=read(base/'FREEZE.json');follow_frozen=read(follow/'FREEZE.json')
    check_freeze(area,frozen);check_bindings(follow_frozen)
    results=read(base/'analysis/RESULTS.json');checks=read(base/'verification/VERIFICATION.json')
    extra=read(follow/'analysis/RESULTS.json');extra_checks=read(follow/'verification/VERIFICATION.json')
    require(results['all_allocated_files_complete'] and checks['all_allocated_files_verified']
            and extra_checks['all_allocated_files_verified'],'Incomplete audit cannot be published as verified')
    require(checks['results_sha256']==sha(base/'analysis/RESULTS.json')
            and extra_checks['results_sha256']==sha(follow/'analysis/RESULTS.json'),'Result identity differs')
    keys=['session','rows','expected_images','observed_images','states','prediction_rows',
          'empty_placeholder_rows','row_errors','row_diagnostics','image_errors','images_with_each_error',
          'minimum_score','maximum_score','maximum_prediction_rows_per_image','images_at_300_predictions',
          'duplicates_retained','class_correspondence','box_policy','box_format_metadata_present',
          'box_normalization_metadata_present','source_sha256','logical_rows_sha256',
          'experiment_admission','blockers','load_seconds','logical_audit_seconds','physical_view_seconds','seconds']
    files=[]
    for row,additional in zip(results['files'],extra['files']):
        require(row['session']==additional['session'],'Follow-up file allocation differs')
        session=row['session'];record={key:row[key] for key in keys}
        record['content_contract']='Every nonempty detection must have strictly positive width and height'
        record['content_contract_passed']=not row['row_errors'] and not row['image_errors']
        record['extent_followup']=additional['extent_summary']
        record['view_identity']=read(base/'analysis'/session/'VIEW.json')
        for label,path in [('original_timing',base/'analysis'/session/'TIMING_ALIGNMENT.json'),
                           ('inclusive_preprocessing_timing',follow/'analysis'/session/'TIMING.json')]:
            timing=read(path);safe={k:v for k,v in timing.items() if k!='trials'};safe['trials']=[]
            for trial in timing['trials']:
                safe['trials'].append({k:v for k,v in trial.items() if k!='omitted_image_ids'}|
                                     {'omitted_images':len(trial['omitted_image_ids'])})
            record[label]=safe
        files.append(record)
    phase_records=[]
    for path in sorted((area/'logs').glob('cached-*-COMPLETED.json')):
        x=read(path);phase_records.append({k:x[k] for k in
            ['stage','started_utc','finished_utc','seconds','exit_code','error']})
    acquisitions=[json.loads(line) for line in (area/'logs/downloads.jsonl').read_text().splitlines()]
    added=acquisitions[112:]
    summary={'artifact_id':'reiyah.cached-packet-audit.public-summary','version':'0.1.0','status':'exploratory',
        'published_snapshot_utc':datetime.now(timezone.utc).isoformat(),
        'original_freeze':{'sha256':sha(base/'FREEZE.json'),'frozen_utc':frozen['frozen_utc'],
                           'bindings':len(frozen['bindings'])},
        'followup_freeze':{'sha256':sha(follow/'FREEZE.json'),'frozen_utc':follow_frozen['frozen_utc'],
                           'bindings':len(follow_frozen['bindings']),'outcome_informed_diagnostic':True},
        'results_sha256':sha(base/'analysis/RESULTS.json'),'verification_sha256':sha(base/'verification/VERIFICATION.json'),
        'followup_results_sha256':sha(follow/'analysis/RESULTS.json'),
        'followup_verification_sha256':sha(follow/'verification/VERIFICATION.json'),
        'files':files,'all_logical_rows_checked_with_both_decoders':sum(r['rows'] for r in files),
        'all_allocated_files_verified':True,'unit_controls':34,'followup_controls':7,
        'complete_synthetic_pipelines_verified':True,'new_model_calls':0,'new_image_reads':0,
        'reserved_images_closed':1433,'fully_admitted_cached_packets':0,
        'independent_scientific_replication':False,'original_results_and_failures_retained':True,
        'bounded_source_followup':{'requests':len(added),'received_body_bytes':sum(x['received_bytes'] for x in added),
                                  'request_limit':32,'body_byte_limit':64*1024**2},
        'phase_costs_before_publication':phase_records,
        'audit_peak_resident_bytes_macos':results['peak_resident_bytes_macos'],
        'verification_peak_resident_bytes_macos':checks['peak_resident_bytes_macos'],
        'human_seconds':None,'full_economic_cost':None,'source_payloads_distributed':False}
    put(here/'summary.json',summary)
    selected=[]
    original_names={'edgefirst-dataset-format.html','edgefirst-format-schema.html','edgefirst-client.rs',
        'edgefirst-client-head.json','edgefirst-client-license.txt','edgefirst-studio-terms.html',
        'edgefirst-profiler-cli-README.md','edgefirst-profiler-cli-CHANGELOG.md','edgefirst-profiler-cli-LICENSE'}
    for row in acquisitions:
        name=Path(row['path']).name
        if row not in added and name not in original_names and not any(name==f'edgefirst-v-{s}-{kind}'
                for s in ('e89','e93','e9c') for kind in ('predictions.parquet','api.json','platform.yaml')):continue
        origin=row['url'];parts=urlsplit(origin)
        if parts.hostname not in {'api.github.com','raw.githubusercontent.com','github.com','edgefirst.studio',
                                   'doc.edgefirst.ai','huggingface.co','arrow.apache.org'}:
            origin='Public-session file route; exact temporary locator retained privately'
        if '?' in origin and parts.hostname not in {'api.github.com','huggingface.co'}:
            origin=origin.split('?',1)[0]
        require(not any(word in origin.lower() for word in ('x-amz','signature=','token=')),'Private locator')
        selected.append({'artifact':name,'origin':origin,'retrieved_utc':row['started_utc'],
            'http_status':row['http_status'],'received_bytes':row['received_bytes'],'sha256':row['sha256'],
            'application_denial':name=='edgefirst-task-11701-public.json',
            'retention':'Private; source payload redistribution is not asserted'})
    member=area/'sources/coco-instances_val2017.json'
    selected.append({'artifact':member.name,'origin':'Official COCO val2017 annotation ZIP member; original custody ledger',
        'bytes':member.stat().st_size,'sha256':sha(member),'use':'Membership, dimensions and categories only',
        'retention':'Private; no image pixels or reference-accuracy scoring'})
    put(here/'sources.json',{'artifact_id':'reiyah.cached-packet-audit.public-sources','version':'0.1.0',
                            'sources':selected,'payloads_distributed':False})
    for name in ('summary.json','sources.json'):
        raw=(here/name).read_text()
        require('/Users/' not in raw and 'omitted_image_ids' not in raw and 'ip-' not in raw,'Private data in public summary')
    print(json.dumps({'files':len(files),'logical_rows':summary['all_logical_rows_checked_with_both_decoders'],
                      'summary_sha256':sha(here/'summary.json'),'source_rows':len(selected)}))


if __name__=='__main__':main()
