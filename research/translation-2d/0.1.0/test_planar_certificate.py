from copy import deepcopy
from fractions import Fraction as F
from itertools import product
import random
import unittest

from planar_certificate import check_basis, check_search, neighbors, overlap_limits, relaxed_pairs
from planar_search import prepare, search, w
from test_planar_search import box, image


class PlanarCertificateControls(unittest.TestCase):
    def fixture(self, limit=31):
        im = image([box('a', 15, 10, 15, 30)], [box('b')]); refs = [box('r')]
        basis = prepare(im, refs); result = search(im, refs, basis, 10, maximum_regions=limit, maximum_depth=6)
        checked = check_basis(im, refs, basis)
        return im, refs, checked, result

    def test_trapezoid_extrema_against_dense_rational_control(self):
        rng = random.Random(9018)
        for _ in range(300):
            lo = F(rng.randrange(-20, 30), 3); hi = lo + F(rng.randrange(0, 30), 3)
            extent = F(rng.randrange(1, 30), 3); left = F(rng.randrange(-20, 30), 3)
            right = left + F(rng.randrange(1, 30), 3)
            low, high = overlap_limits(lo, hi, extent, left, right)
            points = {lo + (hi - lo) * F(i, 50) for i in range(51)}
            points.update(p for p in (left, right - extent, left - extent, right) if lo <= p <= hi)
            values = [max(F(0), min(p + extent, right) - max(p, left)) for p in points]
            self.assertEqual((low, high), (min(values), max(values)))

    def test_constructive_pair_relaxation_exhaustive_shared_neighbors(self):
        ids = {'a', 'b', 'c'}; subsets = [{x for x, bit in zip(sorted(ids), flags) if bit} for flags in product((0, 1), repeat=3)]
        for must, may, a, b in product(subsets, repeat=4):
            if not must <= may: continue
            expected = sorted({(int(bool(n & a)), int(bool(n & b))) for n in subsets if must <= n <= may})
            self.assertEqual(relaxed_pairs(must, may, a, b), [list(row) for row in expected])

    def test_full_cover_and_retained_gap_verify(self):
        for cap in (1, 31):
            im, refs, checked, result = self.fixture(cap)
            report = check_search(im, refs, checked, result, 10)
            self.assertEqual(report['regions'], len(result['nodes']))
            self.assertEqual(report['exact'], result['exact_extrema'])
            self.assertGreater(report['unresolved_regions'], 0)

    def test_empty_observed_reference_and_shared_edges_verify(self):
        for im, refs in [(image([], [box('b')]), []), (image([box('same')], [box('same')]), [box('r')])]:
            basis = prepare(im, refs); checked = check_basis(im, refs, basis)
            value = check_search(im, refs, checked, search(im, refs, basis, 64), 64)
            self.assertTrue(value['exact'])

    def test_missing_child_or_leaf_and_shifted_split_rejected(self):
        im, refs, checked, result = self.fixture()
        broken = deepcopy(result); broken['nodes'][0]['children'].pop()
        with self.assertRaises(ValueError): check_search(im, refs, checked, broken, 10)
        broken = deepcopy(result); broken['leaf_indices'].pop()
        with self.assertRaises(ValueError): check_search(im, refs, checked, broken, 10)
        broken = deepcopy(result); child = broken['nodes'][0]['children'][1]
        broken['nodes'][child]['domain'][0] = w(F(100))
        with self.assertRaises(ValueError): check_search(im, refs, checked, broken, 10)

    def test_omitted_reference_and_orphan_region_rejected(self):
        im, refs, checked, result = self.fixture()
        broken = deepcopy(result); broken['roots'] = []
        with self.assertRaises(ValueError): check_search(im, refs, checked, broken, 10)
        broken = deepcopy(result); broken['nodes'].append(deepcopy(broken['nodes'][-1]))
        with self.assertRaises(ValueError): check_search(im, refs, checked, broken, 10)

    def test_relaxed_bound_cannot_be_presented_as_attained(self):
        im, refs, checked, result = self.fixture(1)
        broken = deepcopy(result); broken['attained_bounds'] = broken['universal_bounds']; broken['exact_extrema'] = True
        with self.assertRaises(ValueError): check_search(im, refs, checked, broken, 10)
        broken = deepcopy(result); broken['nodes'][0]['bounds'][0] += 2
        with self.assertRaises(ValueError): check_search(im, refs, checked, broken, 10)

    def test_preparation_augmentability_source_or_rank_change_rejected(self):
        im = image([], [box('b')]); refs = [box('r')]; basis = prepare(im, refs)
        for key, value in [('augmentable_b', []), ('ranks', [0, 1]), ('reference_id', 'another')]:
            broken = deepcopy(basis); broken['bases'][0][key] = value
            with self.assertRaises(ValueError): check_basis(im, refs, broken)

    def test_wrong_radius_shape_source_and_attained_delta_rejected(self):
        im = image([], [box('b')]); refs = [box('r')]; basis = prepare(im, refs)
        result = search(im, refs, basis, 6); checked = check_basis(im, refs, basis)
        check_search(im, refs, checked, result, 6)
        for mutate in ('radius', 'shape', 'source', 'delta'):
            broken = deepcopy(result); witness = broken['witnesses']['lower']; edit = witness['edit']
            if mutate == 'radius': edit['linf_distance'] = w(F(0))
            if mutate == 'shape': edit['translated_reference']['xyxy'][2] = w(F(99))
            if mutate == 'source': edit['source_reference_sha256'] = 'c' * 64
            if mutate == 'delta': witness['delta'] = w(F(-3))
            with self.assertRaises(ValueError): check_search(im, refs, checked, broken, 6)

    def test_previously_checked_native_proof_mutation_rejected(self):
        im, refs, checked, result = self.fixture(1); check_search(im, refs, checked, result, 10)
        broken = deepcopy(result); key = next(iter(broken['proofs']))
        broken['proofs'][key]['proof']['payload']['result']['bounds']['lower'] = w(F(99))
        with self.assertRaises(ValueError): check_search(im, refs, checked, broken, 10)

    def test_enlarged_work_limit_or_discarded_unresolved_leaf_rejected(self):
        im, refs, checked, result = self.fixture(1)
        broken = deepcopy(result); broken['limits']['maximum_regions'] = 4096
        with self.assertRaises(ValueError): check_search(im, refs, checked, broken, 10)
        broken = deepcopy(result); broken['unresolved_leaf_indices'] = []
        with self.assertRaises(ValueError): check_search(im, refs, checked, broken, 10)


if __name__ == '__main__':
    unittest.main()
