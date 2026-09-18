from copy import deepcopy
from fractions import Fraction as F
import unittest

from planar_search import digest, moved_world, prepare, q, search, w
from compare_math import measure


def box(identity, x=10, y=10, width=30, height=30):
    xyxy = [w(F(value)) for value in (x, y, x + width, y + height)]
    return {'id': identity, 'record_sha256': digest({'id': identity, 'xyxy': xyxy}), 'xyxy': xyxy}


def image(a, b):
    return {'id': 'image-00', 'ordinal': 0, 'width': 100, 'height': 100,
            'image_sha256': 'a' * 64, 'policy_sha256': 'b' * 64,
            'output_a': {'state': 'observed', 'value': a}, 'output_b': {'state': 'observed', 'value': b},
            'reference_input_state': 'available'}


class PlanarSearchControls(unittest.TestCase):
    def test_diagonal_reversal_precedes_axis_only_reversal(self):
        im = image([], [box('b')]); refs = [box('r')]; basis = prepare(im, refs)
        at4 = search(im, refs, basis, F(4))
        at6 = search(im, refs, basis, F(6))
        self.assertTrue(at4['exact_extrema']); self.assertEqual(list(map(q, at4['universal_bounds'])), [1, 1])
        self.assertTrue(at6['exact_extrema']); self.assertEqual(list(map(q, at6['attained_bounds'])), [-1, 1])
        edit = at6['witnesses']['lower']['edit']
        self.assertNotEqual(q(edit['offset'][0]), 0); self.assertNotEqual(q(edit['offset'][1]), 0)
        self.assertLessEqual(q(edit['linf_distance']), 6)

    def test_coupled_shared_predictions_have_no_artificial_rank_gap(self):
        common = box('shared'); im = image([common], [deepcopy(common)]); refs = [box('r')]
        result = search(im, refs, prepare(im, refs), 64)
        self.assertEqual(list(map(q, result['universal_bounds'])), [0, 0])
        self.assertTrue(result['exact_extrema']); self.assertEqual(len(result['nodes']), 1)

    def test_work_limit_retains_a_bound_gap_without_inventing_its_attainment(self):
        im = image([box('a', 15, 10, 15, 30)], [box('b')]); refs = [box('r')]
        result = search(im, refs, prepare(im, refs), 10, maximum_regions=1)
        self.assertEqual(result['state'], 'bounded_with_gap')
        self.assertEqual(result['stopped_limits'], ['region_limit'])
        self.assertEqual(list(map(q, result['universal_bounds'])), [-2, 2])
        self.assertEqual(list(map(q, result['attained_bounds'])), [0, 0])
        self.assertEqual(result['leaf_indices'], [0]); self.assertEqual(result['unresolved_leaf_indices'], [0])

    def test_cover_survives_refinement_and_retains_every_child(self):
        im = image([box('a', 15, 10, 15, 30)], [box('b')]); refs = [box('r')]
        result = search(im, refs, prepare(im, refs), 10, maximum_regions=31, maximum_depth=6)
        self.assertLessEqual(len(result['nodes']), 31)
        self.assertTrue(any(node['children'] for node in result['nodes']))
        incoming = {index: 0 for index in range(len(result['nodes']))}
        for node in result['nodes']:
            if node['children']:
                self.assertEqual(len(node['children']), 2)
                for child in node['children']: incoming[child] += 1
        self.assertEqual(incoming[0], 0)
        self.assertTrue(all(count == 1 for index, count in incoming.items() if index))
        for x in range(0, 21, 2):
            for y in range(0, 21, 2):
                world, _ = moved_world(im, refs, 0, (F(x), F(y)), F(10))
                value = q(measure(im, world, 'exact_projection', 'conventional')['nominal']['delta'])
                self.assertLessEqual(q(result['universal_bounds'][0]), value)
                self.assertLessEqual(value, q(result['universal_bounds'][1]))

    def test_empty_reference_is_observed_and_unavailable_input_rejected(self):
        im = image([], [box('b')]); result = search(im, [], prepare(im, []), 64)
        self.assertEqual(result['nodes'], []); self.assertTrue(result['exact_extrema'])
        self.assertEqual(list(map(q, result['universal_bounds'])), [-1, -1])
        broken = deepcopy(im); broken['reference_input_state'] = 'unavailable'
        with self.assertRaises(ValueError): prepare(broken, [])

    def test_cached_native_proof_remains_bound_to_identical_current_world(self):
        im = image([], [box('b')]); refs = [box('r')]; basis = prepare(im, refs); cache = {}
        first = search(im, refs, basis, 0, native_cache=cache)
        second = search(im, refs, basis, 1, native_cache=cache)
        self.assertEqual(len(first['new_native_proofs']), 1)
        self.assertEqual(second['new_native_proofs'], [])
        self.assertEqual(set(first['proofs']), set(second['proofs']))
        broken = deepcopy(basis); broken['reference_sha256'] = 'c' * 64
        with self.assertRaises(ValueError): search(im, refs, broken, 1)

    def test_seed_cannot_change_shape_or_exceed_current_radius(self):
        im = image([], [box('b')]); refs = [box('r')]; basis = prepare(im, refs)
        seed = {'edit': {'operation': 'translation', 'source_reference_id': 'r',
                        'source_reference_sha256': refs[0]['record_sha256'],
                        'translated_reference': box('moved', 21, 10)}}
        with self.assertRaises(ValueError): search(im, refs, basis, 10, axis_witnesses=[seed])
        seed['edit']['translated_reference'] = box('moved', 10, 10, 31, 30)
        with self.assertRaises(ValueError): search(im, refs, basis, 10, axis_witnesses=[seed])


if __name__ == '__main__':
    unittest.main()
