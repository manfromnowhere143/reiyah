"""Bounds over exhaustive tiny common-edge graphs and geometric witnesses."""
from copy import deepcopy
from fractions import Fraction
import itertools
import unittest

from timing_bounds import (CONTRACTS, candidates, case_rows, certify, digest, flow_rank, optional_bounds,
                           outcome, q, search, w, world_references)


def rectangle(identity, coordinates):
    row = {'id': identity, 'xyxy': list(map(w, coordinates))}
    return {**row, 'record_sha256': digest(row)}


def image(a, b):
    return {'id': 'synthetic', 'ordinal': 0, 'width': 100, 'height': 100, 'image_sha256': '0'*64,
            'policy_sha256': '1'*64, 'reference_input_state': 'available',
            'output_a': {'state': 'observed', 'value': a}, 'output_b': {'state': 'observed', 'value': b}}


class BoundsTests(unittest.TestCase):
    def test_exhaustive_shared_graphs_with_two_optional_vertices(self):
        identities = ['a', 'b', 'c']; nodes = {key: rectangle(key, [0, 0, 25, 25]) for key in identities}
        subsets = [set(key for index, key in enumerate(identities) if mask & (1 << index)) for mask in range(8)]
        checked = 0
        for left_a, left_b in [(set(), set()), ({'a'}, {'a'}), ({'a', 'b'}, {'b', 'c'}), ({'a', 'b', 'c'}, {'a'})]:
            item = image([nodes[x] for x in sorted(left_a)], [nodes[x] for x in sorted(left_b)])
            for base_neighbors in subsets:
                edges = {(key, 'known') for key in base_neighbors}
                ranks = [flow_rank(left, {'known'}, {(a, b) for a, b in edges if a in left}) for left in (left_a, left_b)]
                for count in range(3):
                    lo, hi = optional_bounds(item, ranks, count)
                    for neighborhoods in itertools.product(subsets, repeat=count):
                        right = {'known'} | {str(i) for i in range(count)}
                        all_edges = edges | {(key, str(i)) for i, neighbors in enumerate(neighborhoods) for key in neighbors}
                        mr = [flow_rank(left, right, {(a, b) for a, b in all_edges if a in left}) for left in (left_a, left_b)]
                        delta = len(left_a)-len(left_b)+2*(mr[1]-mr[0])
                        self.assertLessEqual(lo, delta); self.assertLessEqual(delta, hi); checked += 1
        self.assertEqual(checked, 2336)

    def test_identical_predictions_remain_exact_under_unknowns(self):
        row = rectangle('same', [0, 0, 30, 30]); item = image([row], [row])
        self.assertEqual(optional_bounds(item, [0, 0], 100), (0, 0))

    def test_rank_inconsistency_rejected(self):
        row = rectangle('same', [0, 0, 30, 30]); item = image([row], [row])
        with self.assertRaisesRegex(ValueError, 'contradicts'):
            optional_bounds(item, [0, 1], 2)

    def test_missing_unknown_count_is_not_zero(self):
        with self.assertRaises(ValueError):
            optional_bounds(image([], []), [0, 0], None)
        with self.assertRaises(ValueError):
            optional_bounds(image([], []), [0, 0], True)

    def test_geometric_opposite_worlds_and_native_agreement(self):
        item = image([rectangle('a', [0, 0, 25, 25])], [])
        pool = candidates(item); result = search(item, [], ['instance'], pool)
        self.assertEqual(list(map(q, result['bounds'])), [-1, 1])
        self.assertEqual(q(result['worlds']['lower']['measurement']['delta']), -1)
        self.assertEqual(q(result['worlds']['upper']['measurement']['delta']), 1)
        proofs = {}
        for direction in ('lower', 'upper'):
            key = certify(item, [], ['instance'], result['worlds'][direction]['candidate_indices'], pool['rectangles'], proofs)
            self.assertEqual(proofs[key]['measurement'], result['worlds'][direction]['measurement'])

    def test_unknown_geometry_can_repeat_for_distinct_instances(self):
        item = image([rectangle('a', [0, 0, 25, 25]), rectangle('b', [0, 0, 25, 25])], [])
        pool = candidates(item); result = search(item, [], ['i0', 'i1'], pool)
        self.assertEqual(q(result['worlds']['lower']['measurement']['delta']), -2)
        indices = result['worlds']['lower']['candidate_indices']; self.assertEqual(len(indices), 2)
        refs = world_references([], ['i0', 'i1'], indices, pool['rectangles'])
        self.assertNotEqual(refs[0]['id'], refs[1]['id'])

    def test_zero_search_budget_preserves_unresolved_bound_gap(self):
        item = image([rectangle('a', [0, 0, 25, 25])], [])
        result = search(item, [], ['i'], candidates(item), evaluation_limit=0)
        self.assertEqual(result['candidate_evaluations'], 0)
        self.assertEqual(result['worlds']['lower']['stop'], 'evaluation_limit')
        self.assertEqual(q(result['worlds']['lower']['measurement']['delta']), 1)
        self.assertEqual(outcome(tuple(map(q, result['bounds']))), 'unresolved')

    def test_candidate_pool_truncation_is_explicit(self):
        item = image([rectangle('a', [25, 25, 75, 75])], [])
        pool = candidates(item, limit=2)
        self.assertEqual(pool['eligible_before_cap'], 5); self.assertTrue(pool['truncated'])
        self.assertEqual(len(pool['rectangles']), 2)

    def test_candidates_remain_in_frame_and_height_eligible(self):
        item = image([rectangle('a', [0, 0, 25, 25])], [])
        pool = candidates(item)
        self.assertEqual(len(pool['rectangles']), 3)
        for geometry in pool['rectangles']:
            x1, y1, x2, y2 = map(q, geometry)
            self.assertTrue(0 <= x1 < x2 <= 100 and 0 <= y1 < y2 <= 100 and y2-y1 >= 25)

    def test_unknown_census_must_be_unique(self):
        item = image([], [])
        with self.assertRaisesRegex(ValueError, 'sorted unique'):
            search(item, [], ['i', 'i'], candidates(item))

    def test_optional_budget_cannot_be_exceeded(self):
        with self.assertRaisesRegex(ValueError, 'budget'):
            world_references([], ['i'], [0, 0], [[w(x) for x in [0, 0, 25, 25]]])

    def test_full_case_retains_blocked_member(self):
        available = {'state': 'available', 'bounds': [w(1), w(1)], 'attained': [w(1), w(1)], 'proof_keys': ['a', 'a']}
        records = {'i0': {'contracts': {key: deepcopy(available) for key in CONTRACTS}},
                   'i1': {'contracts': {key: {'state': 'input_blocked', 'reason': 'missing_census'} for key in CONTRACTS}}}
        cases = [{'id': 'both', 'group': 'primary', 'images': ['i0', 'i1']}, {'id': 'one', 'group': 'image', 'images': ['i0']}]
        rows = case_rows(cases, records)
        self.assertEqual(len(rows), 8)
        for row in rows[:4]:
            self.assertEqual(row['allocated_images'], 2); self.assertEqual(row['membership'], ['i0', 'i1'])
            self.assertEqual(row['decision'], 'input_blocked'); self.assertIsNone(row['bounds'])
        self.assertTrue(all(row['decision'] == 'supported' for row in rows[4:]))

    def test_attained_opposites_differ_from_a_bound_gap(self):
        for attained, evidence in [([-1, 1], 'opposite_worlds'), ([1, 1], 'bound_gap')]:
            value = {'state': 'available', 'bounds': [w(-1), w(1)], 'attained': list(map(w, attained)), 'proof_keys': ['a', 'b']}
            records = {'i': {'contracts': {key: value for key in CONTRACTS}}}
            rows = case_rows([{'id': 'c', 'group': 'primary', 'images': ['i']}], records)
            self.assertTrue(all(row['decision'] == 'unresolved' and row['evidence'] == evidence for row in rows))

    def test_zero_excludes_strict_improvement(self):
        self.assertEqual(outcome((0, 0)), 'excluded')
        self.assertEqual(outcome((0, 1)), 'unresolved')


if __name__ == '__main__':
    unittest.main()
