"""Frozen diagnostic of one timing formula and already flagged box extents."""
import argparse
from collections import Counter
import ctypes
import json
from pathlib import Path
import resource
import sys
import time

from packet_core import encoded, require
from packet_run import check_freeze, put, read, utc
from packet_timing import f32
from packet_view import sha


NAMES=['capture_ms','preprocess_ms','inference_ms','postprocess_ms']


def orderings(images):
    return {'first_appearance':sorted(images,key=lambda r:r['first_row']),
            'lexical_image_id':sorted(images,key=lambda r:r['image_id']),
            'emission_timestamp':sorted(images,key=lambda r:(r['metadata']['emit_ts_ns'],r['image_id']))}


def inclusive_vector(image,mode):
    m=image['metadata'];t=m['timing']
    require(all(type(t[k]) is int and t[k]>=0 for k in ('load','preprocess','inference','decode')),
            'Invalid source nanoseconds')
    values=[(t['load']+t['preprocess'])/1000000,t['inference']/1000000,t['decode']/1000000]
    if mode=='float32_stages':values=[f32(x) for x in values]
    else:require(mode=='direct_stages','Unknown conversion')
    return [m['capture_ms'],*values]


def chart_vectors(chart):
    require([s['name'] for s in chart['series']]==NAMES,'Unexpected chart series')
    counts={len(s['data']) for s in chart['series']};require(len(counts)==1,'Unequal chart lengths')
    count=counts.pop()
    require(all(all(p['x']==i for i,p in enumerate(s['data'])) for s in chart['series']),
            'Unexpected chart order')
    return [[s['data'][i]['y'] for s in chart['series']] for i in range(count)]


def alignment(images,chart):
    actual=chart_vectors(chart);count=len(actual);trials=[]
    for order,rows in sorted(orderings(images).items()):
        for offset in range(6):
            if offset+count>len(rows):continue
            for mode in ('direct_stages','float32_stages'):
                expected=[inclusive_vector(r,mode) for r in rows[offset:offset+count]]
                components=[sum(a[i]==e[i] for a,e in zip(actual,expected)) for i in range(4)]
                trials.append({'ordering':order,'offset':offset,'conversion':mode,
                    'component_matches':dict(zip(NAMES,components)),
                    'exact_tuple_matches':sum(a==e for a,e in zip(actual,expected)),
                    'all_tuples_match':all(a==e for a,e in zip(actual,expected)),
                    'omitted_image_ids':[r['image_id'] for r in rows[:offset]+rows[offset+count:]]})
    return {'chart_images':count,'prediction_images':len(images),'trials':trials,
            'matching_trials':sum(t['all_tuples_match'] for t in trials),
            'capture_equals_load_count':sum(r['metadata']['capture_ms']==r['metadata']['timing']['load']/1000000
                                             for r in images),
            'publisher_omission_intention_established':False}


def extent_summary(rows):
    counts=Counter();scores=[]
    for row in rows:
        x,y,w,h=row['box2d'];scores.append(row['box2d_score'])
        for name,present in [('zero_width',w==0),('zero_height',h==0),('negative_width',w<0),
                             ('negative_height',h<0),('both_zero',w==0 and h==0),
                             ('center_on_canvas_boundary',x in (0,1) or y in (0,1)),
                             ('center_outside_canvas',x<0 or x>1 or y<0 or y>1)]:
            counts[name]+=int(present)
    return {'flagged_rows':len(rows),'affected_images':len({r['name'] for r in rows}),
            'geometry_counts':dict(sorted(counts.items())),
            'minimum_flagged_score':min(scores,default=None),'maximum_flagged_score':max(scores,default=None),
            'rows_repaired_or_dropped':0}


def checked_extent_rows(rows,expected_ordinals,maximum_rows=1000000):
    bad=[];total=0
    for i,row in enumerate(rows):
        require(i<maximum_rows,'Follow-up row cap');total+=1;box=row['box2d']
        flagged=box is not None and (box[2]<=0 or box[3]<=0)
        require(flagged==(i in expected_ordinals),'Original diagnostic row set differs')
        if flagged:bad.append({'row':i,**row})
    require(all(0<=i<total for i in expected_ordinals),'Diagnostic row outside file')
    return bad,total


def check_bindings(frozen):
    for b in frozen['bindings']:
        p=Path(b['path']);require(p.is_file() and p.stat().st_size==b['bytes'] and sha(p)==b['sha256'],
                                  'Follow-up frozen input changed')


def analyze(area,base,frozen,output):
    import pyarrow.parquet as pq
    require(not output.exists(),'Follow-up output exists');output.mkdir(parents=True)
    tick=time.perf_counter();start=utc();results=[]
    for session in ('e89','e93','e9c'):
        run=base/'analysis'/session;out=output/session;out.mkdir();clock=time.perf_counter()
        images=read(run/'IMAGES.json');chart=read(area/'sources'/f'edgefirst-{session}-t_inline_timings.json')
        timing=alignment(images,chart);put(out/'TIMING.json',timing)
        ordinals={x['row'] for line in (run/'ROW_DIAGNOSTICS.jsonl').read_text().splitlines()
                  if (x:=json.loads(line))['issue']=='nonpositive_box_extent'}
        p=pq.ParquetFile(run/'view/physical-list-view.parquet')
        def rows():
            for batch in p.iter_batches(batch_size=4096,columns=['name','box2d','box2d_score','label_index'],
                                         use_threads=False):yield from batch.to_pylist()
        bad,total=checked_extent_rows(rows(),ordinals)
        put(out/'FLAGGED_ROWS.json',bad)
        result={'session':session,'rows':total,'extent_summary':extent_summary(bad),
                'timing_matching_trials':timing['matching_trials'],
                'capture_equals_load_count':timing['capture_equals_load_count'],
                'timing_sha256':sha(out/'TIMING.json'),'flagged_rows_sha256':sha(out/'FLAGGED_ROWS.json'),
                'seconds':time.perf_counter()-clock}
        results.append(result);print(json.dumps(result),flush=True)
    check_bindings(frozen)
    result={'artifact_id':'reiyah.cached-packet-audit.followup','version':'0.1.0','status':'exploratory',
            'started_utc':start,'finished_utc':utc(),'seconds':time.perf_counter()-tick,'files':results,
            'peak_resident_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'new_image_reads':0,'new_model_calls':0,'reserved_images_closed':1433,
            'fully_admitted_cached_packets':0,'original_audit_results_unchanged':True}
    put(output/'RESULTS.json',result)


def verify(area,base,frozen,run,output):
    import polars as pl
    require(not output.exists(),'Follow-up verification exists');output.mkdir(parents=True)
    tick=time.perf_counter();start=utc();checks=[];result=read(run/'RESULTS.json')
    for record in result['files']:
        session=record['session'];clock=time.perf_counter()
        table=pl.read_parquet(area/'sources'/f'edgefirst-v-{session}-predictions.parquet',parallel='none',
                             columns=['name','box2d','box2d_score','label_index','timing','capture_ms','emit_ts_ns'])
        expected_bad=read(run/session/'FLAGGED_ROWS.json');actual_bad=[];images={}
        for ordinal,row in enumerate(table.iter_rows(named=True)):
            if row['name'] not in images:
                images[row['name']]={'image_id':row['name'],'first_row':ordinal,
                    'metadata':{k:row[k] for k in ('timing','capture_ms','emit_ts_ns')}}
            if row['box2d'] is not None and (row['box2d'][2]<=0 or row['box2d'][3]<=0):
                actual_bad.append({'row':ordinal,**{k:row[k] for k in ('name','box2d','box2d_score','label_index')}})
        require(encoded(actual_bad)==encoded(expected_bad),'Original/derived flagged rows differ')
        require(extent_summary(actual_bad)==record['extent_summary'],'Extent aggregate differs')
        require(table.height==record['rows'],'Row count differs');del table
        timing=read(run/session/'TIMING.json')
        chart=read(area/'sources'/f'edgefirst-{session}-t_inline_timings.json')
        arrays=[series['data'] for series in chart['series']];count=len(arrays[0]);orders=orderings(list(images.values()))
        expected_keys={(order,offset,mode) for order in orders for offset in range(6)
                       for mode in ('direct_stages','float32_stages') if offset+count<=len(images)}
        require({(t['ordering'],t['offset'],t['conversion']) for t in timing['trials']}==expected_keys
                and len(timing['trials'])==len(expected_keys),'Follow-up trial allocation differs')
        matches=0
        for trial in timing['trials']:
            rows=orders[trial['ordering']];offset=trial['offset'];parts=[0]*4;tuples=0
            for index,image in enumerate(rows[offset:offset+count]):
                m=image['metadata'];t=m['timing'];expected=[m['capture_ms']]
                for ns in (t['load']+t['preprocess'],t['inference'],t['decode']):
                    v=ns/1000000
                    expected.append(ctypes.c_float(v).value if trial['conversion']=='float32_stages' else v)
                equal=[arrays[j][index]['y']==expected[j] for j in range(4)]
                parts=[a+int(b) for a,b in zip(parts,equal)];tuples+=int(all(equal))
            require(dict(zip(NAMES,parts))==trial['component_matches'] and tuples==trial['exact_tuple_matches']
                    and (tuples==count)==trial['all_tuples_match'],'Separate timing arithmetic differs')
            require([r['image_id'] for r in rows[:offset]+rows[offset+count:]]==trial['omitted_image_ids'],
                    'Omitted image membership differs')
            matches+=int(tuples==count)
        require(matches==timing['matching_trials']==record['timing_matching_trials'],'Timing match count differs')
        capture=sum(r['metadata']['capture_ms']==r['metadata']['timing']['load']/1000000 for r in images.values())
        require(capture==timing['capture_equals_load_count']==record['capture_equals_load_count'],'Capture/load differs')
        require(sha(run/session/'FLAGGED_ROWS.json')==record['flagged_rows_sha256']
                and sha(run/session/'TIMING.json')==record['timing_sha256'],'Follow-up output bytes differ')
        checks.append({'session':session,'flagged_rows':len(actual_bad),'all_flagged_rows_match':True,
                       'all_timing_trials_verified':True,'seconds':time.perf_counter()-clock})
        print(json.dumps(checks[-1]),flush=True)
    require([x['session'] for x in checks]==['e89','e93','e9c'],'Follow-up session allocation differs')
    check_bindings(frozen)
    put(output/'VERIFICATION.json',{'artifact_id':'reiyah.cached-packet-audit.followup-verification',
        'version':'0.1.0','started_utc':start,'finished_utc':utc(),'seconds':time.perf_counter()-tick,
        'files':checks,'results_sha256':sha(run/'RESULTS.json'),'all_allocated_files_verified':True,
        'shared_extent_aggregation_and_ordering_helpers':True,'independent_scientific_replication':False})


def main():
    p=argparse.ArgumentParser();p.add_argument('--area',type=Path,required=True)
    p.add_argument('--base',type=Path,required=True);p.add_argument('--freeze',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--verify-run',type=Path);args=p.parse_args()
    sys.path.insert(0,str(args.area/'private/reader-deps'));frozen=read(args.freeze);check_bindings(frozen)
    if args.verify_run is None:analyze(args.area,args.base,frozen,args.output)
    else:verify(args.area,args.base,frozen,args.verify_run,args.output)


if __name__=='__main__':main()
