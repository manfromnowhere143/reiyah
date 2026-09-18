"""Bounded artifact alignment; a match is not inferred warmup intent."""
import math
import struct

from packet_core import finite, require


def f32(value): return struct.unpack('>f',struct.pack('>f',value))[0]


def expected_vector(image, mode):
    metadata=image['metadata'];timing=metadata.get('timing') if metadata else None
    if not isinstance(timing,dict):return None
    capture=metadata.get('capture_ms')
    if not finite(capture) or capture<0:return None
    raw=[timing.get(key) for key in ('preprocess','inference','decode')]
    if any(type(v) is not int or v<0 for v in raw):return None
    stages=[v/1000000 for v in raw]
    if mode=='float32_stages':stages=[f32(v) for v in stages]
    elif mode!='direct_stages':raise ValueError('Unknown timing conversion')
    return [capture,*stages]


def align(images,chart):
    names=['capture_ms','preprocess_ms','inference_ms','postprocess_ms']
    require(isinstance(chart,dict) and isinstance(chart.get('series'),list),'Missing timing chart')
    series=chart['series'];require([s['name'] for s in series]==names,'Unexpected timing chart series')
    sizes={len(s['data']) for s in series};require(len(sizes)==1,'Unequal chart series lengths')
    count=sizes.pop()
    require(all(all(p['x']==i and finite(p['y']) and p['y']>=0 for i,p in enumerate(s['data']))
                for s in series),'Invalid chart index or duration')
    chart_vectors=[[s['data'][i]['y'] for s in series] for i in range(count)]
    present=[r for r in images if r['rows']>0]
    orders={'first_appearance':sorted(present,key=lambda r:r['first_row']),
            'lexical_image_id':sorted(present,key=lambda r:r['image_id'])}
    if all(type(r['metadata'].get('emit_ts_ns')) is int for r in present):
        orders['emission_timestamp']=sorted(present,key=lambda r:(r['metadata']['emit_ts_ns'],r['image_id']))
    trials=[]
    for order,rows in sorted(orders.items()):
        for offset in range(6):
            if offset+count>len(rows):continue
            selected=rows[offset:offset+count]
            for mode in ('direct_stages','float32_stages'):
                vectors=[expected_vector(r,mode) for r in selected]
                unavailable=sum(v is None for v in vectors)
                exact=0;differences=[]
                for actual,expected in zip(chart_vectors,vectors):
                    if expected is None:continue
                    exact+=actual==expected
                    differences.extend(abs(a-b) for a,b in zip(actual,expected))
                trials.append({'ordering':order,'offset':offset,'conversion':mode,'compared_images':count,
                               'unavailable':unavailable,'exact_tuple_matches':exact,
                               'maximum_absolute_difference_ms':max(differences,default=None),
                               'all_tuples_match':unavailable==0 and exact==count,
                               'omitted_image_ids':[r['image_id'] for r in rows[:offset]+rows[offset+count:]]})
    return {'chart_images':count,'prediction_images':len(present),'trials':trials,
            'matching_trials':sum(r['all_tuples_match'] for r in trials),
            'historical_warmup_intention_established':False}
