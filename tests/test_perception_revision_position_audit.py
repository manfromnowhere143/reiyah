"""Observation conditioning challenged by raw finite geometry and changed outputs."""
from copy import deepcopy
from fractions import Fraction
import hashlib
from itertools import product
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_perception_revision import ratio, brute_count
from test_perception_revision_localization import fixture
from tools.perception_revision import contract, localization, localization_checker
from tools.perception_revision import position_contract as positions
from tools.perception_revision import position_audit, position_checker


def answers(case, request, values):
    refs = {(a['id'], r['id']): r for a in request['anchors'] for r in a['references']}
    return {'artifact_id': 'reiyah.perception-revision.position-observations', 'version': '0.1.0',
            'cohort_id': case['cohort_id'], 'reference_context_sha256': case['reference_context_sha256'],
            'observation_basis': 'hypothetical', 'observations': [
                {'anchor': aid, 'object': oid, 'subject_sha256': positions.subject_digest(case, request, aid, refs[aid, oid]),
                 'evidence_sha256': hashlib.sha256(contract.encoded([aid, oid, [contract.wire(v) for v in xy], contract.wire(radius)])).hexdigest(),
                 'xy': [contract.wire(v) for v in xy], 'radius': contract.wire(radius)}
                for (aid, oid), (xy, radius) in values.items()]}


class PositionAuditTests(unittest.TestCase):
    def evaluate(self, case, request, observations):
        before = contract.encoded([case, request, observations])
        payload = position_audit.produce(case, request, observations)
        self.assertEqual(position_checker.check(case, request, observations, payload), payload['result'])
        self.assertEqual(before, contract.encoded([case, request, observations]))
        return payload

    def one(self, case, request, xy, radius):
        return answers(case, request, {(case['anchors'][0]['id'], 'o'): (xy, radius)})

    def test_empty_answers_preserve_existing_enclosure(self):
        case, request = fixture()
        original = localization.produce(case, request)['result']
        result = self.evaluate(case, request, answers(case, request, {}))['result']
        for key in ('bounds', 'decision', 'robustness', 'execution_status'):
            self.assertEqual(result[key], original[key])
        self.assertEqual(result['supplied_observation_count'], 0)

    def test_residual_error_is_retained_and_unfavorable_answer_changes_graph(self):
        case, request = fixture(refs={'o': ('car', (Fraction(39, 20), Fraction(0)))})
        uncertain = self.one(case, request, (Fraction(39, 20), Fraction(0)), Fraction(1, 10))
        self.assertEqual(self.evaluate(case, request, uncertain)['result']['robustness'], 'unresolved')
        exact = self.one(case, request, (Fraction(39, 20), Fraction(0)), Fraction(0))
        self.assertEqual(self.evaluate(case, request, exact)['result']['bounds'], {'lower': ratio(1), 'upper': ratio(1)})
        adverse = self.one(case, request, (Fraction(41, 20), Fraction(0)), Fraction(0))
        payload = self.evaluate(case, request, adverse)
        self.assertEqual(payload['result']['bounds'], {'lower': ratio(-1), 'upper': ratio(-1)})
        self.assertEqual(payload['result']['decision']['preference'], 'prefer_a')
        _, derived = positions.condition(case, request, adverse)
        self.assertEqual(derived[0]['anchors'][0]['reference']['edges'], [])
        self.assertEqual(len(case['anchors'][0]['reference']['edges']), 1)

    def test_containment_partial_overlap_and_closed_tangency(self):
        origin = {'xy': [ratio(0), ratio(0)], 'radius': ratio(1)}
        cases = [((0, 0), Fraction(1), ('equal', 'prior')),
                 ((0, 0), Fraction(1, 2), ('observation_contained', 'observation')),
                 ((0, 0), Fraction(2), ('prior_contained', 'prior')),
                 ((1, 0), Fraction(1), ('partial_overlap', 'prior')),
                 ((2, 0), Fraction(1), ('partial_overlap', 'prior')),
                 ((Fraction(2001, 1000), 0), Fraction(1), ('disjoint', None)),
                 ((Fraction(3, 5), Fraction(4, 5)), Fraction(0), ('observation_contained', 'observation'))]
        for xy, radius, expected in cases:
            answer = {'xy': [contract.wire(v) for v in xy], 'radius': contract.wire(radius)}
            self.assertEqual(positions.ball_relation(origin, answer), expected)
        case, request = fixture(radius=Fraction(1, 5))
        observed = self.one(case, request, (Fraction(41, 20), Fraction(0)), Fraction(3, 20))
        payload = self.evaluate(case, request, observed)
        self.assertEqual(payload['result']['partial_intersection_enclosures'], 1)
        self.assertEqual(payload['proof']['conditioning']['records'][0]['enclosure'], 'observation')
        self.assertEqual(payload['result']['robustness'], 'unresolved')

    def test_disjoint_answers_do_not_produce_vacuous_robustness(self):
        case, request = fixture()
        observed = self.one(case, request, (Fraction(5), Fraction(0)), Fraction(1, 10))
        payload = self.evaluate(case, request, observed)
        result = payload['result']
        self.assertEqual(result['conditioning_status'], 'inconsistent_premises')
        self.assertEqual(result['model_status'], 'inconsistent')
        self.assertIsNone(result['bounds'])
        self.assertEqual(result['decision']['improvement_criterion'], 'not_evaluated')
        self.assertIsNone(payload['proof']['geometry'])

    def test_same_observation_reused_but_old_verdict_cannot_survive_changed_detector(self):
        case, request = fixture(radius=Fraction(1, 2))
        observed = self.one(case, request, (Fraction(19, 10), Fraction(0)), Fraction(1, 20))
        old = self.evaluate(case, request, observed)
        self.assertEqual(old['result']['robustness'], 'robust')
        new, geometry = fixture(bb=('different',), dets={'different': ('car', (Fraction(5), Fraction(0)))}, radius=Fraction(1, 2))
        new['comparison_id'] = 'changed-output'; geometry['comparison_id'] = new['comparison_id']
        result = self.evaluate(new, geometry, observed)['result']
        self.assertEqual(result['bounds'], {'lower': ratio(-1), 'upper': ratio(-1)})
        with self.assertRaises(contract.Invalid):
            position_checker.check(new, geometry, observed, old)

    def test_subject_binding_excludes_detector_threshold_and_uncertainty_radius(self):
        case, request = fixture()
        observed = self.one(case, request, (Fraction(19, 10), Fraction(0)), Fraction(1, 20))
        changed = deepcopy(request)
        changed['anchors'][0]['references'][0]['radius'] = ratio(1, 2)
        changed['threshold'] = ratio(3)
        positions.validate_observations(case, changed, observed)
        self.assertEqual(self.evaluate(case, changed, observed)['result']['robustness'], 'robust')

    def test_changed_subject_or_context_rejects_without_silent_drop(self):
        case, request = fixture()
        observed = self.one(case, request, (Fraction(19, 10), Fraction(0)), Fraction(1, 20))
        for field, value in [('record_sha256', '0'*64), ('class', 'pedestrian'), ('xy', [ratio(39,20), ratio(0)])]:
            changed = deepcopy(request); changed['anchors'][0]['references'][0][field] = value
            with self.assertRaises(contract.Invalid): self.evaluate(case, changed, observed)
        for key, value in [('cohort_id', 'other'), ('reference_context_sha256', '0'*64)]:
            changed = deepcopy(case); changed[key] = value
            geometry = deepcopy(request)
            if key == 'reference_context_sha256': geometry[key] = value
            with self.assertRaises(contract.Invalid): self.evaluate(changed, geometry, observed)
        changed = deepcopy(observed); changed['observations'][0]['object'] = 'absent'
        with self.assertRaises(contract.Invalid): self.evaluate(case, request, changed)

    def test_schema_duplicate_and_radius_failures(self):
        case, request = fixture()
        observed = self.one(case, request, (Fraction(19, 10), Fraction(0)), Fraction(1, 20))
        bad = []
        value=deepcopy(observed); del value['observations'][0]['radius']; bad.append(value)
        value=deepcopy(observed); value['observations'][0]['confirmed']=True; bad.append(value)
        value=deepcopy(observed); value['observations'][0]['radius']=ratio(-1); bad.append(value)
        value=deepcopy(observed); value['observations'][0]['xy']=[ratio(10_000_001),ratio(0)]; bad.append(value)
        value=deepcopy(observed); value['observations'].append(deepcopy(value['observations'][0])); bad.append(value)
        value=deepcopy(observed); value['observations'][0]['evidence_sha256']='invalid'; bad.append(value)
        for value in bad:
            with self.assertRaises(contract.Invalid): self.evaluate(case, request, value)

    def test_missing_open_joint_and_resource_limits_do_not_give_a_decision(self):
        case, request = fixture()
        observed = answers(case, request, {})
        joint=deepcopy(case); joint['model']['variables']=['coupled']
        self.assertEqual(self.evaluate(joint, request, observed)['result']['execution_status'], 'scope_unavailable')
        missing=deepcopy(case); missing['anchors'][0]['output_b']={'state':'unknown','reason':'missing'}
        geometry=deepcopy(request); geometry['anchors'][0]['detections']=[]
        self.assertEqual(self.evaluate(missing, geometry, observed)['result']['execution_status'], 'input_blocked')
        opened=deepcopy(case); opened['anchors'][0]['reference']={'state':'open','reason':'unbounded'}
        geometry=deepcopy(request); geometry['anchors'][0]['references']=[]
        self.assertEqual(self.evaluate(opened, geometry, observed)['result']['execution_status'], 'scope_unavailable')
        with patch.object(positions, 'MAX_WORK', 1):
            payload=self.evaluate(case, request, observed)
            self.assertEqual(payload['result']['execution_status'], 'resource_limited')
        with self.assertRaises(contract.Invalid): position_checker.check(case, request, observed, payload)
        with patch.object(positions, 'MAX_INPUT_BYTES', 1):
            with self.assertRaises(contract.Invalid): self.evaluate(case, request, observed)

    def test_original_nominal_graph_checked_even_after_shift(self):
        case, request = fixture(radius=Fraction(1, 2))
        observed = self.one(case, request, (Fraction(21,10),Fraction(0)), Fraction(0))
        case['anchors'][0]['reference']['edges']=[]
        with self.assertRaisesRegex(contract.Invalid, 'Original geometry'): self.evaluate(case,request,observed)

    def test_all_sampled_intersection_worlds_fit_bounds_from_independent_matching(self):
        dets={'a':('car',(Fraction(0),Fraction(0))), 'b':('car',(Fraction(3),Fraction(0)))}
        offsets=[(Fraction(0),Fraction(0)),(Fraction(1,2),Fraction(0)),(Fraction(-1,2),Fraction(0)),
                 (Fraction(0),Fraction(1,2)),(Fraction(0),Fraction(-1,2))]
        checked=0; examined=0
        for ax,bx in product(range(4),repeat=2):
            refs={'x':('car',(Fraction(ax),Fraction(0))), 'y':('car',(Fraction(bx),Fraction(0)))}
            for aa,bb in [(('a',),('a','b')),(('a',),('b',)),((),('a','b')),(('a','b'),('a',))]:
                for shift in (Fraction(0), Fraction(1,4)):
                    case, request=fixture(aa,bb,dets,refs,Fraction(1,2))
                    aid=case['anchors'][0]['id']
                    received={o:((xy[0]+shift,xy[1]),Fraction(1,2)) for o,(_,xy) in refs.items()}
                    observed=answers(case,request,{(aid,o):v for o,v in received.items()})
                    result=self.evaluate(case,request,observed)['result']
                    lo,hi=(contract.rational(result['bounds'][k]) for k in ('lower','upper'))
                    examined+=1
                    for sx,sy in product(offsets,repeat=2):
                        points={o:tuple(v+s for v,s in zip(refs[o][1],delta)) for o,delta in [('x',sx),('y',sy)]}
                        if any(sum((u-v)**2 for u,v in zip(points[o],received[o][0])) > received[o][1]**2 for o in refs):
                            continue
                        edges={(d,o) for d,(_,xy) in dets.items() for o,uv in points.items()
                               if sum((u-v)**2 for u,v in zip(xy,uv)) < 4}
                        ma,mb=(brute_count(list(side),list(refs),edges) for side in (aa,bb))
                        value=2*(mb-ma)-(len(bb)-len(aa))
                        self.assertLessEqual(lo,value);self.assertGreaterEqual(hi,value)
                        checked+=1
        self.assertEqual(examined,128)
        self.assertEqual(checked,1856)

    def test_forged_conditioning_geometry_and_result_rejected_without_producer(self):
        case,request=fixture()
        observed=self.one(case,request,(Fraction(19,10),Fraction(0)),Fraction(0))
        payload=self.evaluate(case,request,observed)
        bad=[]
        value=deepcopy(payload);value['proof']['conditioning']['records'][0]['enclosure']='prior';bad.append(value)
        value=deepcopy(payload);value['proof']['conditioning']['derived_input_sha256']='0'*64;bad.append(value)
        value=deepcopy(payload);value['proof']['geometry']['anchors']=[];bad.append(value)
        value=deepcopy(payload);value['proof']['geometry']['kind']='localization_displacement';bad.append(value)
        value=deepcopy(payload);value['result']['bounds']['lower']=ratio(99);bad.append(value)
        for value in bad:
            with self.assertRaises(contract.Invalid):position_checker.check(case,request,observed,value)
        with patch.object(position_audit,'produce',side_effect=AssertionError('producer called')), \
             patch.object(localization,'produce',side_effect=AssertionError('geometry producer called')), \
             patch.object(localization,'_matching_certificate',side_effect=AssertionError('matcher called')):
            self.assertEqual(position_checker.check(case,request,observed,payload),payload['result'])

    def test_cli_binds_three_operands_and_current_packet(self):
        case,request=fixture()
        observed=self.one(case,request,(Fraction(19,10),Fraction(0)),Fraction(0))
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for name,value in [('input',case),('request',request),('observations',observed)]:
                (root/(name+'.json')).write_bytes(contract.encoded(value))
            digest=lambda name:hashlib.sha256((root/(name+'.json')).read_bytes()).hexdigest()
            operands=[]
            for name in ('input','request','observations'):
                operands.extend(['--'+name,str(root/(name+'.json')),'--'+name+'-sha256',digest(name)])
            cmd=[sys.executable,'-B','-m','tools.perception_revision']
            cwd=Path(__file__).resolve().parents[1]
            production=subprocess.run(cmd+['position-audit',*operands,'--output',str(root/'packet.json')],cwd=cwd,capture_output=True)
            self.assertEqual(production.returncode,0,production.stderr)
            checking=subprocess.run(cmd+['verify-position-audit',*operands,'--packet',str(root/'packet.json'),'--packet-sha256',digest('packet')],cwd=cwd,capture_output=True)
            self.assertEqual(checking.returncode,0,checking.stderr)
            self.assertEqual(json.loads(checking.stdout)['result']['robustness'],'robust')
            failed=subprocess.run(cmd+['verify-position-audit',*operands[:-1],'0'*64,'--packet',str(root/'packet.json'),'--packet-sha256',digest('packet')],cwd=cwd,capture_output=True)
            self.assertEqual(failed.returncode,2)
            self.assertFalse(failed.stdout)


if __name__=='__main__':
    unittest.main()
