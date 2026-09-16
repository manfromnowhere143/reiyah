"""Deletion factorization versus global direct-loss enumeration and forgeries."""
from copy import deepcopy
from fractions import Fraction
from itertools import combinations, product
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.perception_revision import audit, audit_checker, component_plan, component_producer, contract
from tools.perception_revision.component_checker import combine
from test_perception_revision import direct_delta, finite, ratio, request_for


def all_losses(case, request):
    """Global subsets and partial injections; no component or matching code."""
    values = []
    names = case['model']['variables']
    for bits in product((False, True), repeat=len(names)):
        env = dict(zip(names, bits))
        if not all(any(env[t['variable']] == t['value'] for t in clause)
                   for clause in case['model']['clauses']):
            continue
        objects = [(a['id'], o['id']) for a in case['anchors'] for o in a['reference']['objects']
                   if all(env[t['variable']] == t['value'] for t in o['when'])]
        for size in range(min(request['deletion_budget'], len(objects)) + 1):
            for chosen in combinations(objects, size):
                kept = set(objects) - set(chosen)
                if all(((o['anchor'], o['object']) in kept) == (o['outcome'] == 'present')
                       for o in request['observations']):
                    values.append(direct_delta(case, frozenset(chosen), env))
    return values


class ComponentAuditTests(unittest.TestCase):
    def evaluate(self, case, request):
        contract.validate(case)
        contract.validate_request(case, request)
        payload = audit.produce(case, request, method='components')
        self.assertEqual(payload['result'], audit_checker.check(case, request, payload))
        expected = all_losses(case, request)
        if expected:
            self.assertEqual(payload['result']['bounds'], {'lower': ratio(min(expected)), 'upper': ratio(max(expected))})
            self.assertEqual(payload['result']['sufficiency'],
                             'sufficient' if min(expected) > contract.rational(case['loss']['tolerance']) else 'insufficient')
        else:
            self.assertEqual(payload['result']['model_status'], 'inconsistent')
        return payload

    def test_every_small_replacement_graph_and_observation_against_global_subsets(self):
        checked = 0
        objects = ['x', 'y']
        edges = list(product(['a', 'b', 's'], objects))
        for mask in range(1 << len(edges)):
            case = finite(['a', 's'], ['b', 's'], objects,
                          {e for i, e in enumerate(edges) if mask & (1 << i)})
            case['loss'].update(false_negative=ratio(2, 3), false_positive=ratio(3, 2))
            aid = case['anchors'][0]['id']
            for outcomes, budget in product(product((None, 'present', 'absent'), repeat=2), range(3)):
                request = request_for(case, budget, [(aid, o, answer) for o, answer in zip(objects, outcomes) if answer])
                self.evaluate(case, request)
                checked += 1
        self.assertEqual(checked, 1728)

    def test_single_budget_across_components_and_anchors(self):
        case = finite([], ['b'], ['x'], {('b', 'x')})
        a = case['anchors'][0]
        a['weight'] = ratio(1, 3)
        b = deepcopy(a)
        b.update(id='second', weight=ratio(2, 3))
        case['anchors'].append(b)
        for budget in range(4):
            self.evaluate(case, request_for(case, budget))
        result = self.evaluate(case, request_for(case, 1))['result']
        self.assertEqual(result['bounds']['lower'], ratio(-1, 3))

    def test_joint_worlds_required_absence_and_incompatible_observations(self):
        case = finite([], ['b'], ['x', 'y'], {('b', 'x'), ('b', 'y')})
        a = case['anchors'][0]
        case['model'] = {'variables': ['v', 'u'], 'clauses': [[{'variable': 'v', 'value': True},
                                                               {'variable': 'u', 'value': True}]]}
        a['reference']['objects'][0]['when'] = [{'variable': 'v', 'value': True}]
        a['reference']['objects'][1]['when'] = [{'variable': 'v', 'value': False}]
        a['reference']['edges'][1]['when'] = [{'variable': 'u', 'value': True}]
        b = deepcopy(a)
        a['weight'] = b['weight'] = ratio(1, 2)
        b['id'] = 'second'
        b['reference']['objects'][0]['when'][0]['value'] = False
        b['reference']['objects'][1]['when'][0]['value'] = True
        case['anchors'].append(b)
        for answer, budget in product(('present', 'absent'), range(3)):
            self.evaluate(case, request_for(case, budget, [(a['id'], 'x', answer)]))
        self.evaluate(case, request_for(case, 0, [(a['id'], 'x', 'present'), (a['id'], 'y', 'present')]))

    def test_isolated_objects_cancellation_and_equal_string_on_opposite_sides(self):
        case = finite(['same', 'isolated_a'], ['same', 'b'], ['same', 'lonely'],
                      {('same', 'same'), ('b', 'same')})
        aid = case['anchors'][0]['id']
        self.evaluate(case, request_for(case, 1, [(aid, 'lonely', 'absent')]))
        case = finite(['s'], ['s'], ['x', 'y'], {('s', 'x'), ('s', 'y')})
        proof = self.evaluate(case, request_for(case, 2))['proof']
        self.assertEqual(proof['worlds'][0]['components'][0]['kind'], 'equal_outputs')
        with patch.object(component_producer, '_matching_certificate', side_effect=AssertionError('no matching needed')):
            self.evaluate(case, request_for(case, 2))

    def test_local_joint_deletion_with_inert_single_labels(self):
        case = finite(['a'], ['a', 'b'], ['x', 'y', 'z'],
                      {('a', 'x'), ('a', 'y'), ('a', 'z'), ('b', 'x'), ('b', 'y'), ('b', 'z')})
        for budget in range(4):
            self.evaluate(case, request_for(case, budget))
        one = self.evaluate(case, request_for(case, 1))
        two = self.evaluate(case, request_for(case, 2))
        self.assertEqual(one['result']['sufficiency'], 'sufficient')
        self.assertEqual(two['result']['sufficiency'], 'insufficient')

    def test_checker_never_calls_producer_or_matcher(self):
        case = finite([], ['b'], ['x'], {('b', 'x')})
        request = request_for(case, 0)
        payload = audit.produce(case, request, method='components')
        with patch.object(component_producer, 'propose', side_effect=AssertionError('producer disabled')), \
             patch.object(component_producer, '_matching_certificate', side_effect=AssertionError('matcher disabled')), \
             patch.object(audit, 'produce', side_effect=AssertionError('audit producer disabled')):
            self.assertEqual(audit_checker.check(case, request, payload), payload['result'])

    def test_reject_proof_mutations(self):
        case = finite([], ['b1', 'b2'], ['x', 'y'], {('b1', 'x'), ('b2', 'y')})
        request = request_for(case, 1)
        payload = audit.produce(case, request, method='components')
        mutations = [
            lambda p: p['proof'].update(version='0.2.0'),
            lambda p: p['proof']['worlds'].clear(),
            lambda p: p['proof']['worlds'].append(deepcopy(p['proof']['worlds'][0])),
            lambda p: p['proof']['worlds'][0]['components'].pop(),
            lambda p: p['proof']['worlds'][0]['components'].reverse(),
            lambda p: p['proof']['worlds'][0]['components'][0]['variants'].pop(),
            lambda p: p['proof']['worlds'][0]['components'][0]['variants'].reverse(),
            lambda p: p['proof']['worlds'][0]['components'][0].update(kind='equal_outputs'),
            lambda p: p['proof']['worlds'][0]['components'][0]['variants'][0]['output_b']['matching'].clear(),
            lambda p: p['proof']['worlds'][0]['components'][0]['objects'].append('invented'),
            lambda p: p['result'].update(sufficiency='sufficient'),
            lambda p: p['proof'].update(secret_override=True),
        ]
        for mutate in mutations:
            changed = deepcopy(payload)
            mutate(changed)
            with self.assertRaises(contract.Invalid):
                audit_checker.check(case, request, changed)

    def test_resource_limits_are_explicit_and_not_reinterpreted_as_support(self):
        case = finite([], ['b1', 'b2'], ['x', 'y'], {('b1', 'x'), ('b2', 'y')})
        request = request_for(case, 1)
        for name in ('MAX_LOCAL_STATES', 'MAX_MATCH_WORK', 'MAX_COMBINE_WORK'):
            with patch.object(component_plan, name, 0):
                payload = audit.produce(case, request, method='components')
                self.assertEqual(payload['proof']['kind'], 'component_resource_limit')
                self.assertEqual(audit_checker.check(case, request, payload)['sufficiency'], 'unresolved')
            with self.assertRaises(contract.Invalid):
                audit_checker.check(case, request, payload)
        # Real local-state refusal, not just a patched constant.
        dense = finite(['s'], ['s']+['b'+str(i) for i in range(15)], ['x'+str(i) for i in range(15)],
                       {edge for i in range(15) for edge in [('s', 'x'+str(i)), ('b'+str(i), 'x'+str(i))]})
        payload = audit.produce(dense, request_for(dense, 15), method='components')
        self.assertEqual(payload['proof']['kind'], 'component_deletions')
        self.assertEqual(payload['result']['enclosure_kind'], 'conservative_component_bound')
        self.assertEqual(payload['result']['sufficiency'], 'unresolved')

    def test_exchangeable_labels_cover_all_global_deletion_subsets(self):
        case = finite(['a'], ['a', 'b'], ['x', 'y', 'z', 'w'],
                      set(product(['a', 'b'], ['x', 'y', 'z', 'w'])))
        aid = case['anchors'][0]['id']
        for answer, budget in product(('present', 'absent'), range(5)):
            self.evaluate(case, request_for(case, budget, [(aid, 'x', answer)]))
        payload = self.evaluate(case, request_for(case, 4))
        states = payload['proof']['worlds'][0]['components'][0]['variants']
        self.assertEqual(len(states), 5)  # all 16 subsets represented by cardinality
        # A changed neighbor breaks the equivalence, even though class is shared.
        case['anchors'][0]['reference']['edges'].pop()
        self.evaluate(case, request_for(case, 4))

    def test_bounded_components_enclose_all_deletions_without_claiming_existence(self):
        candidates = list(product(['a', 'b', 's'], ['x', 'y']))
        for mask in range(1 << len(candidates)):
            case = finite(['a', 's'], ['b', 's'], ['x', 'y'],
                          {e for i, e in enumerate(candidates) if mask & (1 << i)})
            for budget in (1, 2):
                request = request_for(case, budget)
                with patch.object(component_plan, 'MAX_LOCAL_STATES', 2):
                    payload = audit.produce(case, request, method='components')
                    audit_checker.check(case, request, payload)
                result = payload['result']
                values = all_losses(case, request)
                self.assertLessEqual(contract.rational(result['bounds']['lower']), min(values))
                self.assertGreaterEqual(contract.rational(result['bounds']['upper']), max(values))
                if result['sufficiency'] == 'sufficient':
                    self.assertGreater(min(values), contract.rational(case['loss']['tolerance']))
                if result['sufficiency'] == 'insufficient':
                    self.assertLessEqual(min(values), contract.rational(case['loss']['tolerance']))

    def test_unavailable_inputs_and_default_producer_unchanged(self):
        case = finite([], ['b'], ['x'], {('b', 'x')})
        request = request_for(case, 1)
        self.assertEqual(audit.produce(case, request)['proof']['kind'], 'counterexample')
        case['anchors'][0]['reference'] = {'state': 'open', 'reason': 'unknown'}
        payload = audit.produce(case, request, method='components')
        self.assertEqual(payload['result']['execution_status'], 'scope_unavailable')
        with self.assertRaises(contract.Invalid):
            audit.produce(case, request, method='invented')
        with self.assertRaises(contract.Invalid):
            audit.produce(case, request, candidate={}, method='components')

    def test_budget_convolution_against_cartesian_product(self):
        curves = [{0: (Fraction(1), Fraction(3)), 1: (Fraction(-2), Fraction(0))},
                  {0: (Fraction(-1, 3), Fraction(2)), 1: (Fraction(-4), Fraction(1)),
                   2: (Fraction(-2), Fraction(3))}]
        for budget in range(5):
            combinations_ = [((curves[0][i][0]+curves[1][j][0]),
                              (curves[0][i][1]+curves[1][j][1]))
                             for i, j in product(curves[0], curves[1]) if i+j <= budget]
            self.assertEqual(combine(curves, budget),
                             (min(v[0] for v in combinations_), max(v[1] for v in combinations_)))

    def test_cli_opt_in_verified_with_selected_request_bytes(self):
        case = finite([], ['b'], ['x'], {('b', 'x')})
        request = request_for(case, 0)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            inp, req, out = (root / n for n in ('input.json', 'request.json', 'packet.json'))
            inp.write_bytes(contract.encoded(case))
            req.write_bytes(contract.encoded(request))
            digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
            common = ['--input', str(inp), '--input-sha256', digest(inp),
                      '--request', str(req), '--request-sha256', digest(req)]
            prefix = [sys.executable, '-B', '-m', 'tools.perception_revision']
            cwd = Path(__file__).resolve().parents[1]
            run = subprocess.run(prefix + ['audit', *common, '--proof-method', 'components', '--output', str(out)],
                                 cwd=cwd, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(out.read_bytes())['payload']['proof']['kind'], 'component_deletions')
            verify = prefix + ['verify-audit', *common, '--packet', str(out), '--packet-sha256', digest(out)]
            checked = subprocess.run(verify, cwd=cwd, capture_output=True)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(json.loads(checked.stdout)['result']['sufficiency'], 'sufficient')
            request['deletion_budget'] = 1
            req.write_bytes(contract.encoded(request))
            verify[verify.index('--request-sha256') + 1] = digest(req)
            rejected = subprocess.run(verify, cwd=cwd, capture_output=True)
            self.assertEqual(rejected.returncode, 2)
            self.assertEqual(json.loads(rejected.stderr)['code'], 'PACKET_BINDING')


if __name__ == '__main__':
    unittest.main()
