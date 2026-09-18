from copy import deepcopy
from fractions import Fraction as Q
from itertools import product
import unittest

from envelope_math import best, compare, minimizing_domains, validate
from envelope_check import evaluate, lower_hull, verify


def lines(points):return [{'id':'line-'+str(i),'fp':fp,'fn':fn} for i,(fp,fn) in enumerate(points)]


def crossing_oracle(rows):
    boundaries={Q(0),Q(1)}
    for a,b in product(rows,repeat=2):
        change=(a['fn']-a['fp'])-(b['fn']-b['fp'])
        if change:
            x=Q(b['fp']-a['fp'],change)
            if 0<x<1:boundaries.add(x)
    ordered=sorted(boundaries)
    probes=ordered+[(a+b)/2 for a,b in zip(ordered,ordered[1:])]
    winners={r['id']:[] for r in rows}
    for p in probes:
        losses=[(1-p)*r['fp']+p*r['fn'] for r in rows];minimum=min(losses)
        for row,loss in zip(rows,losses):
            if loss==minimum:winners[row['id']].append(p)
    return {key:None if not values else [str(min(values)),str(max(values))] for key,values in winners.items()}


class EnvelopeControls(unittest.TestCase):
    def test_known_switch_duplicate_and_endpoint_only_ties(self):
        rows=lines([(0,4),(2,0),(0,5),(0,4)])
        domains=minimizing_domains(rows)['lines']
        self.assertEqual([r['minimizing_domain'] for r in domains],
                         [['0','1/3'],['1/3','1'],['0','0'],['0','1/3']])
        self.assertEqual(domains[2]['state'],'point_only')
        self.assertEqual(best(rows,Q(0))[1],['line-0','line-2','line-3'])
        self.assertEqual(best(rows,Q(1,3))[1],['line-0','line-1','line-3'])

    def test_same_slope_and_unsupported_nondominated_point(self):
        rows=lines([(0,4),(2,3),(4,0),(1,5)])
        domains=minimizing_domains(rows)['lines']
        self.assertEqual(domains[1]['state'],'never_minimal')
        self.assertEqual(domains[3]['state'],'never_minimal')
        self.assertEqual(len(lower_hull(rows)),2)

    def test_two_model_sign_reversals_and_fixed_cutoff_disagreement(self):
        old=lines([(0,4),(4,0)]);new=lines([(1,1)])
        result=compare(old,new,2);report=verify(old,new,result)
        self.assertEqual(result['breakpoints'],['0','1/4','1/2','3/4','1'])
        intervals=[c for c in result['partition'] if c['kind']=='open_interval']
        self.assertEqual([c['envelope_comparison'] for c in intervals],
                         ['old_lower','new_lower','new_lower','old_lower'])
        self.assertTrue(intervals[-1]['comparison_changes'])
        self.assertTrue(report['all_optimizer_ties_retained'])

    def test_all_equal_curves_tie_everywhere(self):
        old=lines([(0,0),(0,0)]);new=lines([(0,0)])
        result=compare(old,new,1);verify(old,new,result)
        self.assertTrue(all(c['envelope_comparison']=='tie' for c in result['partition']))
        self.assertTrue(all(c['old_minimizers']==['line-0','line-1'] for c in result['partition']))

    def test_all_729_tiny_three_line_sets_against_crossing_oracle(self):
        points=list(product(range(3),repeat=2));count=0
        for sample in product(points,repeat=3):
            rows=lines(sample);expected=crossing_oracle(rows)
            actual=minimizing_domains(rows)
            self.assertEqual({r['id']:r['minimizing_domain'] for r in actual['lines']},expected)
            for segment in lower_hull(rows):
                p=(segment['left']+segment['right'])/2
                self.assertEqual(segment['intercept']+segment['slope']*p,min(evaluate(r,p) for r in rows))
            count+=1
        self.assertEqual(count,729)

    def test_all_256_tiny_two_model_allocations(self):
        curves=[lines(pair) for pair in product([(0,0),(0,2),(2,0),(1,1)],repeat=2)]
        count=0
        for old,new in product(curves,repeat=2):
            result=compare(old,new,3);verify(old,new,result)
            for cell in result['partition']:
                p=Q(cell['probe']);a=min(evaluate(r,p) for r in old);b=min(evaluate(r,p) for r in new)
                self.assertEqual(Q(cell['delta_mean_at_probe']),(a-b)/3)
            count+=1
        self.assertEqual(count,256)

    def test_bad_counts_allocations_and_caps(self):
        for rows in ([],lines([(0,1)]*601),[{'id':'a','fp':True,'fn':0}],lines([(-1,2)])):
            with self.assertRaises(ValueError):validate(rows)
        rows=lines([(0,1),(1,0)]);rows[1]['id']=rows[0]['id']
        with self.assertRaises(ValueError):validate(rows)
        with self.assertRaises(ValueError):compare(lines([(0,1)]),lines([(1,0)]),0)

    def test_checker_rejects_false_ties_signs_and_incomplete_coverage(self):
        old=lines([(0,4),(4,0),(0,5)]);new=lines([(1,1)])
        original=compare(old,new,2)
        changes=[lambda r:r['envelopes'][0]['lines'][2].update(minimizing_domain=None),
                 lambda r:r['partition'][0].update(old_minimizers=['line-0']),
                 lambda r:r['partition'][1].update(envelope_comparison='new_lower'),
                 lambda r:r['partition'][1].update(delta_mean_coefficients=['999','999']),
                 lambda r:r['partition'].pop(),
                 lambda r:r['partition'][1].update(right_closed=True),
                 lambda r:r['partition'][1].update(strict_new_improvement='supported_nominal')]
        for change in changes:
            r=deepcopy(original);change(r)
            with self.assertRaises(ValueError):verify(old,new,r)


if __name__=='__main__':unittest.main()
