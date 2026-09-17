"""Monotone audit proofs challenged by independent finite matching enumeration."""
from copy import deepcopy
from fractions import Fraction
from itertools import combinations, product
import unittest
from unittest.mock import patch

from test_perception_revision import direct_delta, finite, ratio, request_for
from tools.perception_revision import audit, audit_checker, contract
from tools.perception_revision import monotone_plan, monotone_producer


def subsets(values):
    return [frozenset(c) for n in range(len(values) + 1) for c in combinations(values, n)]


def independent_ranks(left, objects, edges):
    """Enumerate partial injections once; obtain ranks for every induced subset."""
    images = {frozenset()}
    for assignment in product([None] + objects, repeat=len(left)):
        used = [o for o in assignment if o is not None]
        if len(used) == len(set(used)) and all(o is None or (d, o) in edges for d, o in zip(left, assignment)):
            images.add(frozenset(used))
    return {s: max(len(image) for image in images if image <= s) for s in subsets(objects)}


def direct_values(case, request):
    """Independent world/observation/deletion loops; no Engine audit-domain helper."""
    values = []
    names = case['model']['variables']
    for bits in product((False, True), repeat=len(names)):
        env = dict(zip(names, bits))
        if not all(any(env[t['variable']] == t['value'] for t in clause) for clause in case['model']['clauses']):
            continue
        present = [(a['id'], o['id']) for a in case['anchors'] for o in a['reference']['objects']
                   if all(env[t['variable']] == t['value'] for t in o['when'])]
        for removed in subsets(present):
            if len(removed) > request['deletion_budget']:
                continue
            remaining = set(present) - removed
            if not all(((o['anchor'], o['object']) in remaining) == (o['outcome'] == 'present')
                       for o in request['observations']):
                continue
            values.append(direct_delta(case, removed, env))
    return values


class MonotoneAuditTests(unittest.TestCase):
    def evaluate(self, case, request):
        contract.validate(case)
        contract.validate_request(case, request)
        payload = audit.produce(case, request, method='monotone')
        self.assertEqual(audit_checker.check(case, request, payload), payload['result'])
        return payload

    def check_against_values(self, case, request, payload):
        actual = direct_values(case, request)
        result = audit_checker.check(case, request, payload)
        if not actual:
            self.assertEqual(result['model_status'], 'inconsistent')
            self.assertEqual(result['sufficiency'], 'not_evaluated')
            return
        self.assertEqual(result['model_status'], 'consistent')
        lo, hi = (contract.rational(result['bounds'][k]) for k in ('lower', 'upper'))
        self.assertLessEqual(lo, min(actual))
        self.assertGreaterEqual(hi, max(actual))
        if result['enclosure_kind'] == 'exact_for_finite_error_family':
            self.assertEqual((lo, hi), (min(actual), max(actual)))
        tolerance = contract.rational(case['loss']['tolerance'])
        if result['sufficiency'] == 'sufficient':
            self.assertGreater(min(actual), tolerance)
        if result['sufficiency'] == 'insufficient':
            self.assertLessEqual(min(actual), tolerance)
            self.assertIn(contract.rational(result['counterexample_value']), actual)

    def test_all_small_addition_graphs_preserve_gain_under_reference_insertion(self):
        checks = 0
        for nb, ne, no in product(range(3), range(3), range(4)):
            aa = ['a' + str(i) for i in range(nb)]
            bb = aa + ['b' + str(i) for i in range(ne)]
            objects = ['o' + str(i) for i in range(no)]
            choices = list(product(bb, objects))
            for mask in range(1 << len(choices)):
                edges = {e for i, e in enumerate(choices) if mask & (1 << i)}
                ar, br = (independent_ranks(left, objects, edges) for left in (aa, bb))
                for s in subsets(objects):
                    for obj in set(objects) - s:
                        enlarged = s | {obj}
                        self.assertGreaterEqual(br[enlarged] - ar[enlarged], br[s] - ar[s])
                        checks += 1
        self.assertEqual(checks, 65761)

    def test_every_small_observation_pattern_and_shared_budget(self):
        checked = 0
        for nb, ne, no in product(range(2), range(2), range(4)):
            aa = ['a'] if nb else []
            bb = aa + (['b'] if ne else [])
            objects = ['o' + str(i) for i in range(no)]
            choices = list(product(bb, objects))
            for mask in range(1 << len(choices)):
                edges = {e for i, e in enumerate(choices) if mask & (1 << i)}
                case = finite(aa, bb, objects, edges)
                contract.validate(case)
                aid = case['anchors'][0]['id']
                for answers in product(('unqueried', 'present', 'absent'), repeat=no):
                    outcomes = [(aid, o, value) for o, value in zip(objects, answers) if value != 'unqueried']
                    for budget in range(no + 1):
                        request = request_for(case, budget, outcomes)
                        payload = audit.produce(case, request, method='monotone')
                        self.check_against_values(case, request, payload)
                        checked += 1
        self.assertEqual(checked, 9481)

    def test_joint_worlds_unequal_weights_absences_and_inconsistency(self):
        case = finite(['a'], ['a', 'b'], ['x', 'y'], {('a', 'x'), ('b', 'y')})
        case['model'] = {'variables': ['v'], 'clauses': []}
        first = case['anchors'][0]
        first['weight'] = ratio(1, 3)
        first['reference']['objects'][1]['when'] = [{'variable': 'v', 'value': True}]
        second = deepcopy(first); second.update(id='second', weight=ratio(2, 3))
        second['reference']['objects'][1]['when'] = [{'variable': 'v', 'value': False}]
        second['reference']['edges'][0]['when'] = [{'variable': 'v', 'value': True}]
        case['anchors'].append(second)
        case['loss'].update(false_negative=ratio(1, 3), false_positive=ratio(2))
        for budget in range(5):
            for outcomes in [[], [(first['id'], 'y', 'present')], [('second', 'y', 'absent')],
                             [(first['id'], 'y', 'present'), ('second', 'y', 'present')]]:
                request = request_for(case, budget, outcomes)
                self.check_against_values(case, request, self.evaluate(case, request))
        # A required absence consumes no budget in a world where the object is absent.
        request = request_for(case, 0, [(first['id'], 'y', 'absent')])
        payload = self.evaluate(case, request)
        self.assertEqual([r['assignment'] for r in payload['proof']['worlds']], [[False]])

    def test_infeasible_endpoint_does_not_become_a_counterexample(self):
        case = finite([], ['b1', 'b2'], ['x', 'y'], {('b1', 'x'), ('b2', 'y')})
        request = request_for(case, 0)
        result = self.evaluate(case, request)['result']
        self.assertEqual(result['sufficiency'], 'sufficient')
        self.assertEqual(result['bounds'], {'lower': ratio(2), 'upper': ratio(2)})
        self.assertIsNone(result['counterexample_value'])
        request = request_for(case, 1)
        result = self.evaluate(case, request)['result']
        self.assertEqual(result['sufficiency'], 'unresolved')
        self.assertIsNone(result['counterexample_value'])
        request = request_for(case, 2)
        self.assertEqual(self.evaluate(case, request)['result']['sufficiency'], 'insufficient')

    def test_strict_threshold_and_one_global_budget(self):
        case = finite([], ['b1', 'b2'], ['x', 'y'], {('b1', 'x'), ('b2', 'y')})
        second = deepcopy(case['anchors'][0]); second['id'] = 'second'; case['anchors'].append(second)
        for a in case['anchors']:
            a['weight'] = ratio(1, 2)
        outcomes = [(a['id'], 'x', 'present') for a in case['anchors']]
        request = request_for(case, 1, outcomes)
        result = self.evaluate(case, request)['result']
        self.assertEqual(result['sufficiency'], 'sufficient')
        self.assertEqual(contract.rational(result['bounds']['lower']), 1)
        self.assertEqual(result['enclosure_kind'], 'conservative_monotone_bound')
        case['loss']['tolerance'] = ratio(0)
        request = request_for(case, 2, outcomes)
        result = self.evaluate(case, request)['result']
        self.assertEqual(result['sufficiency'], 'insufficient')
        self.assertEqual(result['counterexample_value'], ratio(0))

    def test_independent_replacement_counterexample_excludes_theorem(self):
        case = finite(['a'], ['b'], ['x', 'y'], {('a', 'x'), ('b', 'y')})
        aid = case['anchors'][0]['id']
        self.assertGreater(direct_delta(case, {(aid, 'x')}), direct_delta(case))
        result = self.evaluate(case, request_for(case, 2))['result']
        self.assertEqual(result['execution_status'], 'scope_unavailable')
        self.assertEqual(result['sufficiency'], 'not_evaluated')

    def test_attained_confirmation_floor_and_its_scope(self):
        case = finite([], ['b1', 'b2'], ['x', 'y'], {('b1', 'x'), ('b2', 'y')})
        aid = case['anchors'][0]['id']
        request = request_for(case, 2, [(aid, o, 'present') for o in ('x', 'y')])
        result = self.evaluate(case, request)['result']
        self.assertEqual(result['confirmed_present_lower_bound'], 2)
        self.assertEqual(result['minimum_confirmed_present_count'], 2)
        # Non-attaining requests must not acquire a minimum-size certificate.
        smaller = request_for(case, 2, [(aid, 'x', 'present')])
        result = self.evaluate(case, smaller)['result']
        self.assertEqual(result['confirmed_present_lower_bound'], 2)
        self.assertIsNone(result['minimum_confirmed_present_count'])
        bounded = deepcopy(request); bounded['deletion_budget'] = 1
        self.assertIsNone(self.evaluate(case, bounded)['result']['confirmed_present_lower_bound'])
        absent = request_for(case, 2, [(aid, 'x', 'absent')])
        self.assertIsNone(self.evaluate(case, absent)['result']['confirmed_present_lower_bound'])
        joint = deepcopy(case); joint['model']['variables'] = ['v']
        self.assertIsNone(self.evaluate(joint, request)['result']['confirmed_present_lower_bound'])
        case['loss'].update(false_negative=ratio(3), false_positive=ratio(0), tolerance=ratio(0))
        result = self.evaluate(case, smaller)['result']
        self.assertEqual(result['minimum_confirmed_present_count'], 1)
        forged = self.evaluate(case, request)
        forged['result']['minimum_confirmed_present_count'] = 2
        with self.assertRaises(contract.Invalid):
            audit_checker.check(case, request, forged)

    def test_reject_mutations_and_never_call_the_producer_in_checker(self):
        case = finite([], ['b'], ['x'], {('b', 'x')})
        case['model'] = {'variables': ['v'], 'clauses': []}
        request = request_for(case, 1)
        payload = self.evaluate(case, request)
        forged = []
        value = deepcopy(payload); value['proof']['worlds'].pop(); forged.append(value)
        value = deepcopy(payload); value['proof']['worlds'][1]['assignment'] = [False]; forged.append(value)
        value = deepcopy(payload); value['proof']['worlds'][0]['lower'] = value['proof']['worlds'][0]['upper']; forged.append(value)
        value = deepcopy(payload); value['proof']['worlds'][0]['upper'][0]['output_b']['cover']['objects'].clear(); value['proof']['worlds'][0]['upper'][0]['output_b']['cover']['detections'].clear(); forged.append(value)
        value = deepcopy(payload); value['result']['sufficiency'] = 'sufficient'; forged.append(value)
        value = deepcopy(payload); value['result']['bounds']['lower'] = ratio(100); forged.append(value)
        value = deepcopy(payload); value['proof']['version'] = '0.2.0'; forged.append(value)
        for value in forged:
            with self.assertRaises(contract.Invalid):
                audit_checker.check(case, request, value)
        with patch.object(monotone_producer, 'propose', side_effect=AssertionError('producer called')), \
                patch.object(audit, 'world_proposal', side_effect=AssertionError('matcher called')):
            self.assertEqual(audit_checker.check(case, request, payload), payload['result'])

    def test_missing_open_zero_penalty_and_endpoint_work_limits(self):
        original = finite([], ['b'], ['x'], {('b', 'x')})
        for state, expected in [('unknown', 'input_blocked'), ('open', 'scope_unavailable')]:
            case = deepcopy(original)
            if state == 'unknown':
                case['anchors'][0]['output_b'] = {'state': state, 'reason': 'test missing source'}
            else:
                case['anchors'][0]['reference'] = {'state': state, 'reason': 'test open source'}
            self.assertEqual(self.evaluate(case, request_for(case, 1))['result']['execution_status'], expected)
        case = deepcopy(original); case['loss'].update(false_negative=ratio(0), false_positive=ratio(0))
        self.check_against_values(case, request_for(case, 1), self.evaluate(case, request_for(case, 1)))
        request = request_for(original, 1)
        with patch.object(monotone_plan, 'MAX_WORK', 1):
            payload = self.evaluate(original, request)
            self.assertEqual(payload['result']['execution_status'], 'resource_limited')
            self.assertEqual(payload['result']['sufficiency'], 'unresolved')
        with self.assertRaises(contract.Invalid):
            audit_checker.check(original, request, payload)


if __name__ == '__main__':
    unittest.main()
