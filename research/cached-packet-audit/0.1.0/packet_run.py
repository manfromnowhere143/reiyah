"""Run and separately decode the frozen three-file content audit."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import resource
import sys
import time

from packet_core import audit, encoded, require
from packet_timing import align
from packet_view import check_view, make_view, sha


def utc(): return datetime.now(timezone.utc).isoformat()


def read(path): return json.loads(path.read_text())


def put(path,value):
    with path.open('x') as handle:json.dump(value,handle,indent=2,sort_keys=True,allow_nan=False);handle.write('\n')


def check_freeze(area,frozen):
    for binding in frozen['bindings']:
        path=Path(binding['path'])
        require(path.is_absolute() and path.is_file() and not path.is_symlink(),'Invalid source binding')
        require(path.stat().st_size==binding['bytes'] and sha(path)==binding['sha256'],'Frozen source changed')
    require(frozen['sessions']==['e89','e93','e9c'] and frozen['maximum_rows_per_file']==1000000,
            'Frozen allocation differs')


def class_correspondence(rows,categories):
    source={r['id']:r['name'] for r in categories}
    dense={i:r['name'] for i,r in enumerate(sorted(categories,key=lambda r:r['id']))}
    observed={(r['index'],r['label']) for r in rows}
    return {'observed_indices':len({i for i,_ in observed}),'observed_index_name_pairs':len(observed),
            'source_coco_ids':{
                'matched':sum(source.get(i)==name for i,name in observed),
                'mismatched':sum(source.get(i)!=name for i,name in observed)},
            'dense_sorted_categories':{'matched':sum(dense.get(i)==name for i,name in observed),
                'mismatched':sum(dense.get(i)!=name for i,name in observed)},
            'automatic_remapping_applied':False,'checkpoint_label_mapping_binding_supplied':False}


def analyze(area,frozen,output):
    import polars as pl
    import pyarrow as pa
    import pyarrow.parquet as pq
    require(pl.__version__=='1.44.2' and pa.__version__=='25.0.1','Reader version differs')
    require(not output.exists(),'Run output already exists');output.mkdir(parents=True)
    start=utc();tick=time.perf_counter()
    index=read(area/'sources/coco-instances_val2017.json')
    expected={str(r['id']).zfill(12):[r['width'],r['height']] for r in index['images']}
    require(len(expected)==5000 and len(index['categories'])==80,'COCO membership index differs')
    results=[]
    for session in frozen['sessions']:
        folder=output/session;folder.mkdir()
        source=area/'sources'/('edgefirst-v-'+session+'-predictions.parquet')
        begin=utc();clock=time.perf_counter()
        try:
            parquet=pq.ParquetFile(source)
            require(parquet.metadata.num_rows<=frozen['maximum_rows_per_file'],'Row cap exceeded')
            require((parquet.schema_arrow.metadata or {}).get(b'box2d_format',b'cxcywh')==b'cxcywh'
                    and (parquet.schema_arrow.metadata or {}).get(b'box2d_normalized',b'true')==b'true',
                    'Unsupported box convention')
            load_tick=time.perf_counter();table=pl.read_parquet(source,parallel='none',use_pyarrow=False)
            load_seconds=time.perf_counter()-load_tick
            with (folder/'ROW_DIAGNOSTICS.jsonl').open('x') as handle:
                def emit(row):handle.write(json.dumps(row,sort_keys=True,separators=(',',':'))+'\n')
                audit_tick=time.perf_counter();result=audit(table.iter_rows(named=True),expected,emit,
                                                          frozen['maximum_rows_per_file'])
                audit_seconds=time.perf_counter()-audit_tick
            del table
            images=result.pop('images');put(folder/'IMAGES.json',images)
            view_tick=time.perf_counter();view,identity=make_view(source,folder/'view')
            view_seconds=time.perf_counter()-view_tick
            put(folder/'VIEW.json',identity)
            timing=align(images,read(area/'sources'/('edgefirst-'+session+'-t_inline_timings.json')))
            put(folder/'TIMING_ALIGNMENT.json',timing)
            result.update(session=session,state='complete',source_sha256=sha(source),
                          image_records_sha256=sha(folder/'IMAGES.json'),
                          row_diagnostics_sha256=sha(folder/'ROW_DIAGNOSTICS.jsonl'),
                          view_record_sha256=sha(folder/'VIEW.json'),
                          timing_alignment_sha256=sha(folder/'TIMING_ALIGNMENT.json'),
                          timing_matching_trials=timing['matching_trials'],
                          class_correspondence=class_correspondence(result['observed_label_indices'],index['categories']),
                          box_policy='Retained specification defaults: normalized cxcywh; no clipping',
                          box_format_metadata_present=b'box2d_format' in (parquet.schema_arrow.metadata or {}),
                          box_normalization_metadata_present=b'box2d_normalized' in (parquet.schema_arrow.metadata or {}),
                          experiment_admission='blocked',
                          blockers=['Historical run checkpoint byte binding absent',
                                    'Full actual preprocessing/decoding settings absent',
                                    'Prediction redistribution permission not established'],
                          load_seconds=load_seconds,logical_audit_seconds=audit_seconds,
                          physical_view_seconds=view_seconds)
        except Exception as exc:
            result={'session':session,'state':'failed','error':type(exc).__name__+': '+str(exc),
                    'experiment_admission':'blocked','partial_files_retained':True}
        result.update(started_utc=begin,finished_utc=utc(),seconds=time.perf_counter()-clock)
        put(folder/'RESULT.json',result);results.append(result)
        print(json.dumps({'session':session,'state':result['state'],'rows':result.get('rows'),
                          'seconds':result['seconds'],'error':result.get('error')}),flush=True)
    check_freeze(area,frozen)
    overall={'artifact_id':'reiyah.cached-packet-audit.results','version':'0.1.0','status':'exploratory',
             'started_utc':start,'finished_utc':utc(),'seconds':time.perf_counter()-tick,
             'files':results,'allocated_files':3,'all_allocated_files_complete':all(r['state']=='complete' for r in results),
             'fully_admitted_cached_packets':0,'new_model_calls':0,'new_image_reads':0,
             'reserved_outcomes_accessed':False,'reserved_images_closed':1433,
             'peak_resident_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             'reference_accuracy_scored':False,'human_seconds':None,'economic_cost':None}
    put(output/'RESULTS.json',overall)
    return overall


def verify(area,frozen,run,output):
    import pyarrow as pa
    import pyarrow.parquet as pq
    require(pa.__version__=='25.0.1','Verifier reader version differs')
    require(not output.exists(),'Verification output already exists');output.mkdir(parents=True)
    start=utc();tick=time.perf_counter();results=read(run/'RESULTS.json')
    index=read(area/'sources/coco-instances_val2017.json')
    expected={str(r['id']).zfill(12):[r['width'],r['height']] for r in index['images']}
    checks=[]
    for result in results['files']:
        session=result['session'];folder=run/session;source=area/'sources'/('edgefirst-v-'+session+'-predictions.parquet')
        require(result['state']=='complete','Incomplete file must remain blocked; complete verification unavailable')
        clock=time.perf_counter();identity=check_view(source,folder/'view/physical-list-view.parquet')
        require(identity==read(folder/'VIEW.json'),'Physical view record differs')
        parquet=pq.ParquetFile(folder/'view/physical-list-view.parquet')
        def rows():
            for batch in parquet.iter_batches(batch_size=4096,use_threads=False):
                yield from batch.to_pylist()
        issue_path=output/(session+'-ROW_DIAGNOSTICS.jsonl')
        with issue_path.open('x') as handle:
            def emit(row):handle.write(json.dumps(row,sort_keys=True,separators=(',',':'))+'\n')
            actual=audit(rows(),expected,emit,frozen['maximum_rows_per_file'])
        images=actual.pop('images')
        require(all(encoded(actual[k])==encoded(result[k]) for k in actual),'Independent decoded audit differs')
        require(encoded(images)==encoded(read(folder/'IMAGES.json')),'Decoded image records differ')
        require(sha(issue_path)==sha(folder/'ROW_DIAGNOSTICS.jsonl'),'Decoded row diagnostics differ')
        require(align(images,read(area/'sources'/('edgefirst-'+session+'-t_inline_timings.json')))
                ==read(folder/'TIMING_ALIGNMENT.json'),'Timing alignment replay differs')
        checks.append({'session':session,'rows':actual['rows'],'logical_rows_sha256':actual['logical_rows_sha256'],
                       'all_logical_rows_match':True,'all_image_records_match':True,
                       'all_row_diagnostics_match':True,'source_data_prefix_preserved':True,
                       'seconds':time.perf_counter()-clock})
        print(json.dumps(checks[-1]),flush=True)
    require([r['session'] for r in checks]==frozen['sessions'],'Verification allocation differs')
    check_freeze(area,frozen)
    report={'artifact_id':'reiyah.cached-packet-audit.verification','version':'0.1.0',
            'started_utc':start,'finished_utc':utc(),'seconds':time.perf_counter()-tick,
            'results_sha256':sha(run/'RESULTS.json'),'files':checks,'all_allocated_files_verified':True,
            'independent_decoding_of_preserved_data_pages':True,'shared_logical_validator':True,
            'independent_scientific_replication':False,'fully_admitted_cached_packets':0,
            'peak_resident_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    put(output/'VERIFICATION.json',report);return report


def main():
    p=argparse.ArgumentParser();p.add_argument('--area',type=Path,required=True)
    p.add_argument('--freeze',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--verify-run',type=Path);args=p.parse_args();area=args.area.resolve()
    os.environ['POLARS_MAX_THREADS']='2';sys.path.insert(0,str(area/'private/reader-deps'))
    frozen=read(args.freeze);check_freeze(area,frozen)
    if args.verify_run is None:analyze(area,frozen,args.output)
    else:verify(area,frozen,args.verify_run,args.output)


if __name__=='__main__':main()
