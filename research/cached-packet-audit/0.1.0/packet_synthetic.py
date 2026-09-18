"""End-to-end three-file fixture with missing, empty, invalid and duplicate rows."""
import argparse
import json
from pathlib import Path
import sys
import time

from packet_core import require
from packet_run import analyze, put, verify
from packet_timing import f32
from packet_view import sha


def main():
    p=argparse.ArgumentParser();p.add_argument('--reader-deps',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    sys.path.insert(0,str(args.reader_deps));import polars as pl
    require(not args.output.exists(),'Synthetic output exists');args.output.mkdir(parents=True)
    area=args.output/'area';source=area/'sources';source.mkdir(parents=True)
    put(source/'coco-instances_val2017.json',{'images':[{'id':i,'width':100,'height':80} for i in range(5000)],
        'categories':[{'id':i+1,'name':'class-'+str(i)} for i in range(80)],'annotations':[]})
    for session in ('e89','e93','e9c'):
        rows=[]
        for i in range(5000):
            if session=='e93' and i==100:continue
            empty=(session=='e93' and i==4999) or (session=='e9c' and i>=4998)
            r={'name':str(i).zfill(12),'label':None if empty else 'class-0',
               'label_index':None if empty else 0,'group':'val',
               'box2d':None if empty else [.5,.5,.2,.2],'box2d_score':None if empty else .75,
               'size':[100,80],'mask':None,'timing':{'load':1000000,'preprocess':1000000+i*1000,
                    'inference':2000000+i*1000,'decode':333333},'capture_ms':i+.125,
               'e2e_ms':i+1.,'emit_ts_ns':i+100,'sahi_tiles':0,'sahi_overlap':None,
               'sahi_e2e_ms':None,'sahi_merge_ms':None}
            if session=='e9c' and i==42:r['box2d_score']=None
            rows.append(r)
            if i==0:rows.append(dict(r))
        schema={'name':pl.String,'label':pl.String,'label_index':pl.UInt64,'group':pl.String,
                'box2d':pl.Array(pl.Float32,4),'box2d_score':pl.Float32,'size':pl.Array(pl.UInt32,2),
                'mask':pl.Binary,'timing':pl.Struct({'load':pl.Int64,'preprocess':pl.Int64,
                'inference':pl.Int64,'decode':pl.Int64}),'capture_ms':pl.Float64,'e2e_ms':pl.Float64,
                'emit_ts_ns':pl.UInt64,'sahi_tiles':pl.UInt32,'sahi_overlap':pl.Float32,
                'sahi_e2e_ms':pl.Float64,'sahi_merge_ms':pl.Float64}
        pl.DataFrame(rows,schema=schema).write_parquet(source/('edgefirst-v-'+session+'-predictions.parquet'))
        unique={r['name']:r for r in rows};selected=list(unique.values())[5:]
        vectors=[[r['capture_ms'],f32(r['timing']['preprocess']/1000000),
                  f32(r['timing']['inference']/1000000),f32(r['timing']['decode']/1000000)] for r in selected]
        chart={'series':[{'name':name,'data':[{'x':i,'y':v[j]} for i,v in enumerate(vectors)]}
                         for j,name in enumerate(['capture_ms','preprocess_ms','inference_ms','postprocess_ms'])]}
        put(source/('edgefirst-'+session+'-t_inline_timings.json'),chart)
    frozen={'sessions':['e89','e93','e9c'],'maximum_rows_per_file':1000000,'bindings':[
        {'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(source.iterdir())]}
    put(args.output/'FREEZE.json',frozen)
    result=analyze(area,frozen,args.output/'analysis')
    checks=verify(area,frozen,args.output/'analysis',args.output/'verification')
    expected=[{'predictions_present':5000},{'predictions_present':4998,'publisher_empty_placeholder':1,'missing':1},
              {'predictions_present':4997,'publisher_empty_placeholder':2,'invalid':1}]
    require([r['states'] for r in result['files']]==expected,'Synthetic state oracle differs')
    require(all(r['duplicates_retained']==1 for r in result['files']),'Synthetic duplicates were dropped')
    require(all(r['timing_matching_trials']>0 for r in result['files']),'Synthetic timing alignment failed')
    put(args.output/'SYNTHETIC_REPORT.json',{'artifact_id':'reiyah.cached-packet-audit.synthetic','version':'0.1.0',
        'synthetic_only':True,'expected_image_states':expected,'all_three_files_verified':True,
        'missing_empty_invalid_and_duplicates_distinct':True,'results_sha256':sha(args.output/'analysis/RESULTS.json'),
        'verification_sha256':sha(args.output/'verification/VERIFICATION.json')})


if __name__=='__main__':main()
