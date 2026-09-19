"""Write the authored, pre-outcome allocation; version 0.1.0."""
from pathlib import Path
from fractions import Fraction as F
import json
import sys

def make():
    cases = []
    def add(name, values, weights=None, proxies=None, statuses=None, tau='0', clusters=None):
        n = len(values)
        weights = weights or [F(1,n)]*n
        weights = [F(x)/sum(map(F,weights)) for x in weights]
        proxies = proxies if proxies is not None else ['0']*n
        statuses = statuses or ['observed']*n
        clusters = clusters or [str(i) for i in range(n)]
        units = []
        for i,v in enumerate(values):
            lo,hi = v if isinstance(v,tuple) else (v,v)
            units.append({'id': f'u{i}', 'weight':str(weights[i]), 'lower':str(F(lo)), 'upper':str(F(hi)),
                          'proxy':str(F(proxies[i])), 'status':statuses[i], 'cluster':clusters[i]})
        cases.append({'id':name, 'version':'0.1.0', 'threshold':str(F(tau)), 'units':units, 'purpose':name.replace('_',' ')})
    add('point_positive', ['1']*6)
    add('point_negative', ['-1']*6)
    add('point_tie', ['0']*6)
    add('near_positive', ['1/100']*6)
    add('near_negative', ['-1/100']*6)
    add('alternating_tie', ['-1','1']*3)
    add('mixed_positive', ['-1']+['1']*5)
    add('mixed_negative', ['1']+['-1']*5)
    add('interval_positive', [('1/5','3/5')]*6)
    add('interval_negative', [('-3/5','-1/5')]*6)
    add('interval_straddling', [('-1/5','1/5')]*6)
    add('wide_reference', [('-1','1')]*6)
    add('heavy_positive', ['1','-1','-1','-1'], weights=[7,1,1,1])
    add('heavy_negative', ['-1','1','1','1'], weights=[7,1,1,1])
    add('weighted_tie', ['1','1','-1'], weights=[1,1,2])
    add('proxy_aligned', ['1','1','1','-1'], weights=[4,3,2,1], proxies=['1','1','1','-1'])
    add('proxy_reversed', ['1','1','1','-1'], weights=[4,3,2,1], proxies=['-1','-1','-1','1'])
    add('proxy_constant', ['1','1','1','-1'], weights=[4,3,2,1])
    add('missing_heavy', [('-1','1'),'1','1','1'], weights=[7,1,1,1], statuses=['missing']+['observed']*3)
    add('invalid_heavy', [('-1','1'),'1','1','1'], weights=[7,1,1,1], statuses=['sensor_invalid']+['observed']*3)
    add('abstained_light', ['1','1','1',('-1','1')], statuses=['observed']*3+['abstained'])
    add('zero_weight_members', ['1/2','1/2',('-1','1'),('-1','1')], weights=[1,1,0,0], statuses=['observed','observed','missing','abstained'])
    add('upper_threshold_boundary', ['1']*3, tau='1')
    add('lower_threshold_boundary', ['-1']*3, tau='-1')
    add('extreme_sampling_mass', ['-1','1','1'], weights=[9998,1,1], proxies=['-1','1','1'])
    add('clustered_members', ['-1/5']*3+['2/5']*3, clusters=['scene_a']*3+['scene_b']*3)
    add('all_unavailable_states', [('-1','1')]*5, statuses=['missing','unmeasured','out_of_distribution','sensor_invalid','abstained'])
    add('rational_threshold_tie', ['1','1','0'], tau='2/3')
    assert len(cases)==28
    return {'document_id':'reiyah.sequential-audit.fixtures','version':'0.1.0','status':'exploratory',
            'origin':'Authored deterministic methods fixtures, no empirical observations or prospective value evidence',
            'alpha_per_procedure_population':'1/20','alpha_per_direction':'1/40','bet_fraction':'1/2',
            'populations':cases}

if __name__ == '__main__':
    path=Path(sys.argv[1]); assert not path.exists()
    path.write_text(json.dumps(make(),indent=2)+'\n')
    print('28 authored populations written; no audit outcomes computed.')
