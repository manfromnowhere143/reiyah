"""Weighted split bounds checked against direct losses and complete deletion sets."""
from copy import deepcopy
from fractions import Fraction
from itertools import combinations, product
import unittest
from unittest.mock import patch

from test_perception_revision import direct_delta, finite, ratio
from tools.perception_revision import contract, margin, split_margin


def member(name, weight, case):
    case = deepcopy(case)
    case['comparison_id'] = name
    for i, anchor in enumerate(case['anchors']):
        anchor['id'] = name + '-anchor-' + str(i)
    contract.validate(case)
    return {'id': name, 'weight': ratio(weight), 'case': case,
            'certificate': margin.produce(case)}


class SplitMarginTests(unittest.TestCase):
    def evaluate(self, members, tolerance=0):
        return split_margin.evaluate(members, [m['id'] for m in members], ratio(tolerance))

    def test_exhaustive_weighted_graphs_and_deletions(self):
        objects = ['x', 'y']
        possibilities = list(product(['a', 'b'], objects))
        population = []
        for mask in range(16):
            edges = {e for i, e in enumerate(possibilities) if mask & (1 << i)}
            population.append(finite(['a'], ['a', 'b'], objects, edges))
        first = [member('first', Fraction(1, 3), c) for c in population]
        second = [member('second', Fraction(2, 3), c) for c in population]
        calculations = 0
        for one, two in product(first, second):
            members = [one, two]
            records = [(m['id'], a['id'], o['id']) for m in members
                       for a in m['case']['anchors'] for o in a['reference']['objects']]
            values = []
            for k in range(5):
                for removed in combinations(records, k):
                    value = sum(contract.rational(m['weight']) * direct_delta(
                        m['case'], {(a, o) for mid, a, o in removed if mid == m['id']}) for m in members)
                    values.append((k, value))
                    calculations += 1
            for tolerance in (Fraction(0), Fraction(1, 4)):
                result = self.evaluate(members, tolerance)
                actual_min = min(k for k, v in values if v <= tolerance)
                self.assertLessEqual(result['deletion_lower_bound'], actual_min)
                if result['deletion_upper_bound'] is not None:
                    self.assertGreaterEqual(result['deletion_upper_bound'], actual_min)
                    witness = result['witness']
                    observed = sum(contract.rational(m['weight']) * direct_delta(
                        m['case'], {(r['anchor'], r['object']) for r in witness if r['member'] == m['id']}) for m in members)
                    self.assertEqual(observed, contract.rational(result['witness_delta']))
                    self.assertLessEqual(observed, tolerance)
                if result['minimum_adverse_deletions'] is not None:
                    self.assertEqual(result['minimum_adverse_deletions'], actual_min)
        self.assertEqual(calculations, 4096)

    def test_pool_minimum_is_not_a_universal_minimum(self):
        ambiguous = finite([], ['a'], ['x', 'y'], {('a', 'x'), ('a', 'y')})
        names = ['b' + str(i) for i in range(5)]
        independent = finite([], names, names, {(x, x) for x in names})
        rows = [member('high', Fraction(3, 4), ambiguous),
                member('low', Fraction(1, 4), independent)]
        result = self.evaluate(rows, 1)
        self.assertEqual((result['deletion_lower_bound'], result['deletion_upper_bound']), (1, 2))
        self.assertIsNone(result['minimum_adverse_deletions'])
        self.assertEqual(result['margin_status'], 'bounded')
        self.assertEqual(contract.rational(result['witness_delta']), 1)
        self.assertTrue(all(r['member'] == 'low' for r in result['witness']))

    def test_no_pool_witness_stays_unresolved(self):
        ambiguous = finite([], ['a'], ['x', 'y'], {('a', 'x'), ('a', 'y')})
        result = self.evaluate([member('single', 1, ambiguous)])
        self.assertEqual(result['deletion_lower_bound'], 1)
        self.assertIsNone(result['deletion_upper_bound'])
        self.assertIsNone(result['witness_delta'])
        self.assertEqual(result['witness'], [])

    def test_strict_threshold_and_zero_weight_member(self):
        case = finite([], ['b'], ['o'], {('b', 'o')})
        rows = [member('zero', 0, case), member('used', 1, case)]
        result = self.evaluate(rows, 0)
        self.assertEqual(result['minimum_adverse_deletions'], 1)
        self.assertEqual(result['witness'][0]['member'], 'used')
        excluded = self.evaluate(rows, 1)
        self.assertEqual(excluded['margin_status'], 'criterion_already_excluded')
        self.assertEqual(excluded['minimum_adverse_deletions'], 0)

    def test_missing_duplicate_and_rebound_members_rejected(self):
        case = finite([], ['b'], ['o'], {('b', 'o')})
        one, two = member('one', Fraction(1, 2), case), member('two', Fraction(1, 2), case)
        with self.assertRaises(contract.Invalid):
            split_margin.evaluate([one], ['one', 'two'], ratio(0))
        with self.assertRaises(contract.Invalid):
            self.evaluate([one, one])
        for mutate in ('binding', 'anchor', 'weight', 'loss', 'proof', 'pool'):
            bad = deepcopy([one, two])
            if mutate == 'binding':
                bad[1]['case']['comparison_id'] = 'other'
            elif mutate == 'anchor':
                bad[1]['case']['anchors'][0]['id'] = bad[0]['case']['anchors'][0]['id']
            elif mutate == 'weight':
                bad[1]['weight'] = ratio(1)
            elif mutate == 'loss':
                bad[1]['case']['loss']['false_positive'] = ratio(2)
                bad[1]['certificate'] = margin.produce(bad[1]['case'])
            elif mutate == 'proof':
                bad[1]['certificate']['result']['baseline_delta'] = ratio(99)
            else:
                bad[1]['certificate']['proof']['pool'].clear()
            with self.assertRaises(contract.Invalid, msg=mutate):
                self.evaluate(bad)

    def test_unavailable_and_replacement_scope_do_not_disappear(self):
        case = finite([], ['b'], ['o'], {('b', 'o')})
        missing = deepcopy(case)
        missing['anchors'][0]['output_b'] = {'state': 'unknown', 'reason': 'unavailable control'}
        for unavailable in (missing, finite(['a'], ['b'], ['o'], {('b', 'o')})):
            rows = [member('good', Fraction(1, 2), case), member('unavailable', Fraction(1, 2), unavailable)]
            result = self.evaluate(rows)
            self.assertEqual(result['execution_status'], 'unavailable_members')
            self.assertIsNone(result['baseline_delta'])
            self.assertEqual(len(result['member_checks']), 2)
            self.assertEqual(result['unavailable'][0]['id'], 'unavailable')

    def test_anchor_identity_is_scoped_to_declared_cohort(self):
        case = finite([], ['b'], ['o'], {('b', 'o')})
        rows = [member('one', Fraction(1, 2), case), member('two', Fraction(1, 2), case)]
        for m in rows:
            m['case']['cohort_id'] = 'scene-' + m['id']
            m['case']['anchors'][0]['id'] = 'a-0'
            m['certificate'] = margin.produce(m['case'])
        self.assertEqual(self.evaluate(rows)['minimum_adverse_deletions'], 1)
        rows[1]['case']['cohort_id'] = rows[0]['case']['cohort_id']
        with self.assertRaises(contract.Invalid):
            self.evaluate(rows)

    def test_resource_limits_and_no_producer_during_check(self):
        case = finite([], ['b'], ['o'], {('b', 'o')})
        rows = [member('one', 1, case)]
        with patch.object(margin, 'produce', side_effect=AssertionError('producer called')), \
                patch.object(margin, '_matching_certificate', side_effect=AssertionError('matcher called')):
            self.assertEqual(self.evaluate(rows)['minimum_adverse_deletions'], 1)
        with patch.object(split_margin, 'MAX_TOTAL_INPUT_BYTES', 1):
            with self.assertRaises(contract.Invalid):
                self.evaluate(rows)
        with patch('tools.perception_revision.margin_contract.MAX_WORK', 1):
            limited = member('one', 1, case)
            self.assertEqual(self.evaluate([limited])['execution_status'], 'unavailable_members')


if __name__ == '__main__':
    unittest.main()
