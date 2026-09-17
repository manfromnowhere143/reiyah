"""Exact geometry certificates challenged by independent finite calculations."""
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

from test_perception_revision import finite, ratio, brute_count
from tools.perception_revision import contract, cli, localization, localization_checker
from tools.perception_revision import localization_contract as geometry


def fixture(aa=(), bb=('d',), dets=None, refs=None, radius=Fraction(1, 10)):
    dets = dets or {'d': ('car', (Fraction(0), Fraction(0)))}
    refs = refs if refs is not None else {'o': ('car', (Fraction(19, 10), Fraction(0)))}
    threshold = Fraction(2)
    edges = {(d, o) for d, (dc, xy) in dets.items() for o, (oc, uv) in refs.items()
             if d in set(aa) | set(bb) and dc == oc and sum((x-y)**2 for x, y in zip(xy, uv)) < threshold**2}
    case = finite(list(aa), list(bb), list(refs), edges)
    case['loss'] = {'false_negative': ratio(1), 'false_positive': ratio(1), 'tolerance': ratio(1, 10)}
    anchor = case['anchors'][0]
    anchor['weight'] = ratio(1)
    case['anchors'] = [anchor]
    request = {'artifact_id': 'reiyah.perception-revision.localization-request', 'version': '0.1.0',
               'comparison_id': case['comparison_id'], 'reference_context_sha256': case['reference_context_sha256'],
               'coordinate_system': 'shared_planar_metres', 'family': 'independent_closed_reference_balls',
               'matching_rule': 'strict_same_class_center_distance', 'threshold': ratio(2),
               'position_basis': 'hypothetical', 'anchors': [{'id': anchor['id'], 'detections': [], 'references': []}]}
    known = {d['id']: d for r in contract.ROLES for d in anchor[r]['value']}
    for key, (cls, xy) in dets.items():
        if key in known:
            request['anchors'][0]['detections'].append({**known[key], 'class': cls, 'xy': [contract.wire(v) for v in xy]})
    for key, (cls, xy) in refs.items():
        request['anchors'][0]['references'].append({'id': key, 'record_sha256': hashlib.sha256(key.encode()).hexdigest(),
            'class': cls, 'xy': [contract.wire(v) for v in xy], 'radius': contract.wire(radius)})
    contract.validate(case)
    geometry.validate_request(case, request)
    return case, request


def witness(case, changes):
    return {'artifact_id': 'reiyah.perception-revision.localization-witness', 'version': '0.1.0',
            'displacements': [{'anchor': case['anchors'][0]['id'], 'object': oid,
                               'shift': [contract.wire(v) for v in xy]} for oid, xy in changes.items()]}


class LocalizationTests(unittest.TestCase):
    def evaluate(self, case, request, candidate=None):
        payload = localization.produce(case, request, candidate)
        self.assertEqual(localization_checker.check(case, request, payload), payload['result'])
        return payload

    def test_strict_inner_outer_boundaries_and_zero_radius(self):
        for radius in (Fraction(0), Fraction(1, 10), Fraction(2), Fraction(3)):
            for distance in (Fraction(0), abs(2-radius), 2+radius):
                must, may = geometry.edge_bounds(distance**2, Fraction(2), radius)
                self.assertEqual(must, distance+radius < 2)
                self.assertEqual(may, max(0, distance-radius) < 2)
        case, request = fixture()
        self.assertEqual(self.evaluate(case, request)['result']['robustness'], 'unresolved')
        adverse = self.evaluate(case, request, witness(case, {'o': (Fraction(1, 10), Fraction(0))}))
        self.assertEqual(adverse['result']['robustness'], 'refuted_by_displacement')
        self.assertEqual(adverse['result']['witness_value'], ratio(-1))
        self.assertIsNone(adverse['result']['bounds'])
        request['anchors'][0]['references'][0]['radius'] = ratio(0)
        result = self.evaluate(case, request)['result']
        self.assertEqual(result['bounds'], {'lower': ratio(1), 'upper': ratio(1)})
        self.assertEqual(result['robustness'], 'robust')
        with self.assertRaises(contract.Invalid):
            self.evaluate(case, request, witness(case, {'o': (Fraction(1, 10), Fraction(0))}))

    def test_nonzero_measurement_error_is_not_exact_adjacency(self):
        case, request = fixture(refs={'o': ('car', (Fraction(39, 20), Fraction(0)))})
        self.assertEqual(self.evaluate(case, request)['result']['robustness'], 'unresolved')
        result = self.evaluate(case, request, witness(case, {'o': (Fraction(1, 20), Fraction(0))}))['result']
        self.assertEqual(result['robustness'], 'refuted_by_displacement')

    def test_two_dimensional_radius_and_closed_disc_boundary(self):
        case, request = fixture(refs={'o': ('car', (Fraction(0), Fraction(0)))}, radius=Fraction(1))
        request['threshold'] = ratio(1)
        result = self.evaluate(case, request, witness(case, {'o': (Fraction(3,5), Fraction(4,5))}))['result']
        self.assertEqual(result['robustness'], 'refuted_by_displacement')
        with self.assertRaises(contract.Invalid):
            self.evaluate(case, request, witness(case, {'o': (Fraction(4,5), Fraction(4,5))}))

    def test_displacement_preparation_is_charged_before_proof_admission(self):
        case, request = fixture(radius=Fraction(0))
        reason, prepared = geometry.prepare(case, request)
        self.assertIsNone(reason)
        candidate = witness(case, {})
        moved = geometry.displacement_graphs(request, prepared, candidate)
        ordinary = geometry.matching_work(prepared)
        self.assertEqual(geometry.matching_work(prepared, moved), ordinary + prepared['pairs'])
        with patch.object(localization, 'MAX_WORK', ordinary):
            with self.assertRaises(contract.Invalid): localization.produce(case, request, candidate)

    def test_all_small_grid_displacements_fit_independent_loss_enclosure(self):
        # Discrete challenges falsify continuous bounds; they do not prove completeness.
        dets = {'a': ('car', (Fraction(0), Fraction(0))), 'b': ('car', (Fraction(3), Fraction(0)))}
        shifts = [(Fraction(0), Fraction(0)), (Fraction(1, 2), Fraction(0)),
                  (Fraction(-1, 2), Fraction(0)), (Fraction(0), Fraction(1, 2)), (Fraction(0), Fraction(-1, 2))]
        checked = 0
        for ax, bx in product(range(5), repeat=2):
            refs = {'x': ('car', (Fraction(ax), Fraction(0))), 'y': ('car', (Fraction(bx), Fraction(0)))}
            for aa, bb in [(('a',), ('a', 'b')), (('a',), ('b',)), ((), ('a', 'b')), (('a','b'), ('a',))]:
                case, request = fixture(aa, bb, dets, refs, Fraction(1, 2))
                result = self.evaluate(case, request)['result']
                lower, upper = (contract.rational(result['bounds'][k]) for k in ('lower', 'upper'))
                for sx, sy in product(shifts, repeat=2):
                    moved = {o: tuple(v+s for v, s in zip(refs[o][1], shift)) for o, shift in [('x',sx),('y',sy)]}
                    edges = {(d,o) for d,(_,xy) in dets.items() for o,uv in moved.items()
                             if sum((x-y)**2 for x,y in zip(xy,uv)) < 4}
                    ra, rb = (brute_count(list(side), list(refs), edges) for side in (aa,bb))
                    value = 2*(rb-ra) - (len(bb)-len(aa))
                    self.assertLessEqual(lower, value)
                    self.assertGreaterEqual(upper, value)
                    checked += 1
        self.assertEqual(checked, 2500)

    def test_class_filter_and_shared_detection_cancellation(self):
        case, request = fixture(('d',), ('d',), refs={'o': ('pedestrian', (Fraction(0), Fraction(0)))}, radius=Fraction(3))
        result = self.evaluate(case, request)['result']
        self.assertEqual(result['bounds'], {'lower': ratio(0), 'upper': ratio(0)})
        request['anchors'][0]['references'][0]['class'] = 'car'
        with self.assertRaisesRegex(contract.Invalid, 'nominal'):
            self.evaluate(case, request)

    def test_different_anchor_weights_and_strict_threshold(self):
        case, request = fixture(radius=Fraction(0))
        second = deepcopy(case['anchors'][0]); second['id'] = 'second'
        second['output_a'] = deepcopy(second['output_b']); second['output_b']['value'] = []
        case['anchors'][0]['weight'] = ratio(3,4); second['weight'] = ratio(1,4)
        case['anchors'].append(second)
        second_request = deepcopy(request['anchors'][0]); second_request['id'] = 'second'
        request['anchors'].append(second_request)
        case['loss']['tolerance'] = ratio(1,2)
        contract.validate(case)
        result = self.evaluate(case, request)['result']
        self.assertEqual(result['bounds'], {'lower': ratio(1,2), 'upper': ratio(1,2)})
        self.assertEqual(result['robustness'], 'excluded_for_family')

    def test_exact_nominal_graph_complete_membership_and_context(self):
        case, request = fixture()
        bad = []
        v=deepcopy(request); v['anchors'][0]['references'].clear(); bad.append(v)
        v=deepcopy(request); v['anchors'][0]['detections'][0]['record_sha256']='0'*64; bad.append(v)
        v=deepcopy(request); v['reference_context_sha256']='0'*64; bad.append(v)
        v=deepcopy(request); v['anchors'][0]['references'][0]['radius']=ratio(-1); bad.append(v)
        v=deepcopy(request); v['anchors'][0]['references'][0]['confirmed']=True; bad.append(v)
        v=deepcopy(request); v['threshold']=ratio(0); bad.append(v)
        v=deepcopy(request); v['anchors'][0]['detections'][0]['xy'][0]=ratio(10_000_001); bad.append(v)
        v=deepcopy(request); v['anchors'][0]['references'].append(deepcopy(v['anchors'][0]['references'][0])); bad.append(v)
        for value in bad:
            with self.assertRaises(contract.Invalid): self.evaluate(case, value)
        case['anchors'][0]['reference']['edges'].clear()
        with self.assertRaises(contract.Invalid): self.evaluate(case, request)

    def test_missing_open_joint_and_work_limits_are_explicit(self):
        case, request = fixture()
        joint=deepcopy(case); joint['model']['variables']=['joint']
        self.assertEqual(self.evaluate(joint, request)['result']['execution_status'], 'scope_unavailable')
        missing=deepcopy(case); missing['anchors'][0]['output_b']={'state':'unknown','reason':'unavailable'}
        missing_request=deepcopy(request); missing_request['anchors'][0]['detections']=[]
        self.assertEqual(self.evaluate(missing, missing_request)['result']['execution_status'], 'input_blocked')
        opened=deepcopy(case); opened['anchors'][0]['reference']={'state':'open','reason':'unbounded'}
        opened_request=deepcopy(request); opened_request['anchors'][0]['references']=[]
        self.assertEqual(self.evaluate(opened, opened_request)['result']['execution_status'], 'scope_unavailable')
        with patch.object(geometry, 'MAX_WORK', 1):
            self.assertEqual(self.evaluate(case, request)['result']['execution_status'], 'resource_limited')
        with patch.object(geometry, 'MAX_EDGES', 0):
            self.assertEqual(self.evaluate(case, request)['result']['execution_status'], 'resource_limited')
        with patch.object(localization, 'MAX_WORK', 1), patch.object(localization_checker, 'MAX_WORK', 1):
            payload=self.evaluate(case, request)
            self.assertEqual(payload['result']['execution_status'],'resource_limited')
        with self.assertRaises(contract.Invalid): localization_checker.check(case, request, payload)

    def test_mutations_and_no_solver_in_checker(self):
        case, request=fixture(radius=Fraction(0))
        payload=self.evaluate(case, request)
        mutations=[]
        v=deepcopy(payload); v['proof']['anchors']=[]; mutations.append(v)
        v=deepcopy(payload); v['proof']['version']='0.2.0'; mutations.append(v)
        v=deepcopy(payload); v['proof']['anchors'][0]['b_guaranteed']['cover']['objects']=[]; v['proof']['anchors'][0]['b_guaranteed']['cover']['detections']=[]; mutations.append(v)
        v=deepcopy(payload); v['result']['bounds']['lower']=ratio(100); mutations.append(v)
        for value in mutations:
            with self.assertRaises(contract.Invalid): localization_checker.check(case, request, value)
        with patch.object(localization,'produce',side_effect=AssertionError('producer called')), patch.object(localization,'_matching_certificate',side_effect=AssertionError('matcher called')):
            self.assertEqual(localization_checker.check(case, request, payload),payload['result'])
        case,request=fixture()
        payload=self.evaluate(case,request,witness(case,{'o':(Fraction(1,10),Fraction(0))}))
        payload['proof']['candidate']['displacements'][0]['shift'][0]=ratio(1)
        with self.assertRaises(contract.Invalid): localization_checker.check(case,request,payload)

    def test_cli_binds_all_operands_and_rejects_cross_kind_packet(self):
        case,request=fixture()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for name,value in [('input',case),('request',request),('witness',witness(case,{'o':(Fraction(1,10),Fraction(0))}))]:
                (root/(name+'.json')).write_bytes(contract.encoded(value))
            digest=lambda name:hashlib.sha256((root/(name+'.json')).read_bytes()).hexdigest()
            operands=['--input',str(root/'input.json'),'--input-sha256',digest('input'),'--request',str(root/'request.json'),'--request-sha256',digest('request')]
            cmd=[sys.executable,'-B','-m','tools.perception_revision']
            cwd=Path(__file__).resolve().parents[1]
            production=subprocess.run(cmd+['localization',*operands,'--candidate',str(root/'witness.json'),'--candidate-sha256',digest('witness'),'--output',str(root/'packet.json')],cwd=cwd,capture_output=True)
            self.assertEqual(production.returncode,0,production.stderr)
            checking=subprocess.run(cmd+['verify-localization',*operands,'--packet',str(root/'packet.json'),'--packet-sha256',digest('packet')],cwd=cwd,capture_output=True)
            self.assertEqual(checking.returncode,0,checking.stderr)
            self.assertEqual(json.loads(checking.stdout)['result']['robustness'],'refuted_by_displacement')
            with self.assertRaises(contract.Invalid):
                cli.read_packet(case,digest('input'),root/'packet.json',digest('packet'),digest('request'))
            failed=subprocess.run(cmd+['verify-localization',*operands[:-1],'0'*64,'--packet',str(root/'packet.json'),'--packet-sha256',digest('packet')],cwd=cwd,capture_output=True)
            self.assertEqual(failed.returncode,2)
            self.assertFalse(failed.stdout)


if __name__ == '__main__':
    unittest.main()
