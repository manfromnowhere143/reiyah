"""Known-bad limits and exhaustive tiny matching comparisons."""
from fractions import Fraction
from itertools import combinations_with_replacement
import unittest

from witness_pool import build_pool, q, w
from witness_search import graph_search, search
from witness_verify import independent_pool
from timing_bounds import candidates, search as coarse_search
from test_timing_bounds import image, rectangle
from axis_certificate import maximum_matching


def brute(item, known, edges, neighborhoods, count):
    values = []
    for size in range(count+1):
        for indices in combinations_with_replacement(range(len(neighborhoods)), size):
            ranks = []
            for role in ('output_a', 'output_b'):
                left = {row['id'] for row in item[role]['value']}
                adjacency = {key: {('base', ref) for a, ref in edges if a == key} for key in left}
                for j, index in enumerate(indices):
                    for key in set(neighborhoods[index]) & left: adjacency[key].add(('added', j))
                ranks.append(maximum_matching(adjacency))
            values.append(len(item['output_a']['value'])-len(item['output_b']['value'])+2*(ranks[1]-ranks[0]))
    return min(values), max(values)


class SearchTests(unittest.TestCase):
    def test_narrow_threshold_regions_resolve_coarse_gap(self):
        item = image([rectangle('a', [30, 30, 60, 60])], [rectangle('b', [31, 30, 61, 60])])
        coarse = candidates(item); old = coarse_search(item, [], ['i'], coarse)
        self.assertEqual([q(old['worlds'][key]['measurement']['delta']) for key in ('lower', 'upper')], [0, 0])
        pool = build_pool(item, [], coarse['rectangles'])
        self.assertEqual(pool, independent_pool(item, [], coarse['rectangles']))
        result = search(item, [], ['i'], pool)
        self.assertEqual([q(world['measurement']['delta']) for world in result['worlds']], [-2, 2])
        self.assertTrue(result['universal_endpoints_attained'])

    def test_zero_gain_intermediate_world_must_be_expanded(self):
        item = image([rectangle(x, [0, 0, 25, 25]) for x in ('a0', 'a1')],
                     [rectangle(x, [0, 0, 25, 25]) for x in ('b0', 'b1')])
        neighborhoods = [('a0', 'b0'), ('a0', 'b1')]
        result = graph_search(item, [], set(), neighborhoods, 2)
        self.assertEqual([q(world['measurement']['delta']) for world in result['worlds']], [0, 2])
        self.assertEqual(result['worlds'][1]['indices'], [0, 1])
        self.assertEqual(result['stop'], 'finite_pool_exhausted')

    def test_exhaustive_tiny_multisets_with_shared_and_disjoint_ids(self):
        ids = ('a', 'b', 'c'); nodes = {key: rectangle(key, [0, 0, 25, 25]) for key in ids}
        neighborhoods = [tuple(key for j, key in enumerate(ids) if mask & (1 << j)) for mask in range(1, 8)]
        comparisons = 0
        for first, second in [(('a', 'b'), ('b', 'c')), (('a', 'b'), ('c',)), (('a', 'b', 'c'), ())]:
            item = image([nodes[key] for key in first], [nodes[key] for key in second])
            for mask in range(8):
                edges = {(key, 'known') for j, key in enumerate(ids) if mask & (1 << j)}
                for count in range(4):
                    result = graph_search(item, ['known'], edges, neighborhoods, count)
                    self.assertEqual(tuple(q(world['measurement']['delta']) for world in result['worlds']),
                                     brute(item, ['known'], edges, neighborhoods, count))
                    self.assertTrue(result['finite_pool_search_complete']); comparisons += 1
        self.assertEqual(comparisons, 96)

    def test_duplicate_neighborhoods_represent_distinct_unknowns(self):
        item = image([rectangle(key, [0, 0, 25, 25]) for key in ('a', 'b')], [])
        result = graph_search(item, [], set(), [('a', 'b')], 2)
        self.assertEqual(result['worlds'][0]['indices'], [0, 0])
        self.assertEqual(q(result['worlds'][0]['measurement']['delta']), -2)

    def test_measurement_cap_preserves_known_world_and_gap(self):
        item = image([rectangle('a', [0, 0, 25, 25])], [])
        result = graph_search(item, [], set(), [('a',)], 1, measurement_limit=1)
        self.assertEqual(result['unique_flow_measurements'], 1)
        self.assertEqual(result['stop'], 'evaluation_limit')
        self.assertFalse(result['finite_pool_search_complete'])
        self.assertEqual([q(world['measurement']['delta']) for world in result['worlds']], [1, 1])

    def test_reference_cap_is_not_a_smaller_unknown_family(self):
        item = image([rectangle(key, [0, 0, 25, 25]) for key in ('a', 'b')], [])
        result = graph_search(item, [], set(), [('a', 'b')], 2, reference_limit=1)
        self.assertEqual(result['stop'], 'reference_limit')
        self.assertEqual(list(map(q, result['bounds'])), [-2, 2])
        self.assertEqual(q(result['worlds'][0]['measurement']['delta']), 0)

    def test_seeded_worlds_keep_ranks_and_charge_cache_once(self):
        item = image([rectangle('a', [0, 0, 25, 25])], [])
        seed = {'indices': [0], 'measurement': {'ranks': [1, 0], 'delta': w(-1)}}
        result = graph_search(item, [], set(), [('a',)], 1, [seed, seed])
        self.assertEqual(result['unique_flow_measurements'], 2)
        self.assertEqual(result['stop'], 'universal_endpoints_attained')

    def test_forged_seed_rank_rejected(self):
        item = image([rectangle('a', [0, 0, 25, 25])], [])
        with self.assertRaisesRegex(ValueError, 'changed matching'):
            graph_search(item, [], set(), [('a',)], 1,
                         [{'indices': [0], 'measurement': {'ranks': [0, 0], 'delta': w(1)}}])

    def test_missing_and_zero_budgets_are_not_empty_evidence(self):
        item = image([], [])
        for count in (None, True, -1):
            with self.assertRaises(ValueError): graph_search(item, [], set(), [], count)
        with self.assertRaises(ValueError): graph_search(item, [], set(), [], 0, measurement_limit=0)

    def test_pool_limits_fail_without_truncation(self):
        item = image([rectangle('a', [20, 20, 50, 50])], [])
        with self.assertRaisesRegex(ValueError, 'Rectangle construction limit'):
            build_pool(item, [], [], rectangle_limit=1)
        with self.assertRaisesRegex(ValueError, 'Neighborhood construction limit'):
            build_pool(item, [], [], neighborhood_limit=0)

    def test_ineligible_base_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Ineligible'):
            build_pool(image([], []), [], [[w(x) for x in (0, 0, 25, 24)]])

    def test_empty_outputs_keep_optional_missing_distinct_from_observation(self):
        item = image([], []); pool = build_pool(item, [], [])
        self.assertEqual(pool['rectangles'], [])
        result = search(item, [], ['missing'], pool)
        self.assertEqual(result['unknown_ids'], ['missing'])
        self.assertEqual(result['unknown_count'], 1)
        self.assertEqual(list(map(q, result['bounds'])), [0, 0])


if __name__ == '__main__':
    unittest.main()
