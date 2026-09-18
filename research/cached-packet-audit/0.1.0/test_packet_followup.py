import copy
import json
from pathlib import Path
import tempfile
import unittest

from packet_followup import (NAMES, alignment, checked_extent_rows, extent_summary,
                             inclusive_vector)


def fixture():
    images=[{'image_id':str(i),'first_row':i,'metadata':{'emit_ts_ns':i,
             'capture_ms':i+.125,'timing':{'load':i*1000000+125000,'preprocess':2222000+i*1000,
                                          'inference':3333000+i*1000,'decode':444000}}} for i in range(8)]
    vectors=[inclusive_vector(i,'float32_stages') for i in images[5:]]
    chart={'series':[{'name':name,'data':[{'x':i,'y':v[j]} for i,v in enumerate(vectors)]}
                     for j,name in enumerate(NAMES)]}
    return images,chart


class FollowupControls(unittest.TestCase):
    def test_inclusive_rounding_and_offset(self):
        images,chart=fixture();r=alignment(images,chart)
        matched=[t for t in r['trials'] if t['all_tuples_match']]
        self.assertEqual(len(matched),3)
        self.assertTrue(all(t['offset']==5 and t['conversion']=='float32_stages' for t in matched))
        self.assertTrue(all(t['omitted_image_ids']==['0','1','2','3','4'] for t in matched))
        self.assertEqual(r['capture_equals_load_count'],8)
        self.assertFalse(r['publisher_omission_intention_established'])

    def test_single_component_change_is_not_tolerated(self):
        images,chart=fixture();chart['series'][1]['data'][0]['y']+=1e-10
        r=alignment(images,chart);self.assertEqual(r['matching_trials'],0)
        self.assertTrue(any(t['component_matches']['capture_ms']==3 for t in r['trials']))

    def test_capture_load_mismatch_remains_explicit(self):
        images,chart=fixture();images[0]['metadata']['capture_ms']+=.001
        self.assertEqual(alignment(images,chart)['capture_equals_load_count'],7)

    def test_negative_nanoseconds_and_unknown_conversion_rejected(self):
        images,_=fixture()
        with self.assertRaises(ValueError):inclusive_vector(images[0],'invented')
        images[0]['metadata']['timing']['load']=-1
        with self.assertRaises(ValueError):inclusive_vector(images[0],'direct_stages')

    def test_extent_dimensions_overlap_and_rows_remain(self):
        rows=[{'name':'a','box2d':[0,.5,0,.2],'box2d_score':.1},
              {'name':'a','box2d':[.5,.5,.2,-.1],'box2d_score':.2},
              {'name':'b','box2d':[1,1,0,0],'box2d_score':.3},
              {'name':'c','box2d':None,'box2d_score':None}]
        before=copy.deepcopy(rows);bad,total=checked_extent_rows(rows,{0,1,2})
        self.assertEqual(total,4);self.assertEqual(rows,before)
        r=extent_summary(bad);self.assertEqual(r['flagged_rows'],3);self.assertEqual(r['affected_images'],2)
        self.assertEqual(r['geometry_counts'],{'both_zero':1,'center_on_canvas_boundary':2,
            'center_outside_canvas':0,'negative_height':1,'negative_width':0,'zero_height':1,'zero_width':2})
        self.assertEqual(r['rows_repaired_or_dropped'],0)

    def test_flag_identity_and_allocation_mismatches_fail(self):
        rows=[{'name':'a','box2d':[.5,.5,0,.2],'box2d_score':.1}]
        for expected in (set(),{0,1}):
            with self.assertRaises(ValueError):checked_extent_rows(rows,expected)
        with self.assertRaises(ValueError):checked_extent_rows(rows,{0},maximum_rows=0)

    def test_complete_three_file_pipeline_with_known_geometry_and_timing(self):
        import polars as pl
        from packet_followup import analyze, verify
        from packet_run import put, read
        from packet_view import make_view, sha
        with tempfile.TemporaryDirectory() as temporary:
            area=Path(temporary);sources=area/'sources';sources.mkdir();base=area/'base'
            inputs=[]
            for session in ('e89','e93','e9c'):
                images,chart=fixture();folder=base/'analysis'/session;folder.mkdir(parents=True)
                rows=[{'name':r['image_id'],**r['metadata'],'label_index':0,
                       'box2d':[.5,.5,0. if i==2 else .2,.2],'box2d_score':.7} for i,r in enumerate(images)]
                rows[7].update(box2d=None,box2d_score=None,label_index=None)
                schema={'name':pl.String,'timing':pl.Struct({'load':pl.Int64,'preprocess':pl.Int64,
                    'inference':pl.Int64,'decode':pl.Int64}),'capture_ms':pl.Float64,'emit_ts_ns':pl.UInt64,
                    'label_index':pl.UInt64,'box2d':pl.Array(pl.Float32,4),'box2d_score':pl.Float32}
                source=sources/f'edgefirst-v-{session}-predictions.parquet'
                pl.DataFrame(rows,schema=schema).write_parquet(source);make_view(source,folder/'view')
                put(folder/'IMAGES.json',images)
                (folder/'ROW_DIAGNOSTICS.jsonl').write_text(json.dumps({'row':2,'issue':'nonpositive_box_extent'})+'\n')
                put(sources/f'edgefirst-{session}-t_inline_timings.json',chart)
                inputs.append({'path':str(source),'bytes':source.stat().st_size,'sha256':sha(source)})
            frozen={'bindings':inputs};analyze(area,base,frozen,area/'run')
            verify(area,base,frozen,area/'run',area/'verification')
            result=read(area/'run/RESULTS.json')
            self.assertEqual([r['timing_matching_trials'] for r in result['files']],[3,3,3])
            self.assertTrue(all(r['extent_summary']['flagged_rows']==1 for r in result['files']))
            self.assertTrue(read(area/'verification/VERIFICATION.json')['all_allocated_files_verified'])


if __name__=='__main__':unittest.main()
