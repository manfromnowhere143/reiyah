"""Adversarial checks on full refined image records and retained proofs."""
from copy import deepcopy
import unittest

from witness_pool import q, w
from witness_run import refine
from witness_verify import check_image
from timing_bounds import CONTRACTS, candidates, certify, search
from test_timing_bounds import image, rectangle


def synthetic():
    item = image([rectangle('a', [30, 30, 60, 60])], [rectangle('b', [31, 30, 61, 60])])
    pool = candidates(item); unknown = ['u']; found = search(item, [], unknown, pool); proofs = {}
    keys = [certify(item, [], unknown, found['worlds'][direction]['candidate_indices'], pool['rectangles'], proofs)
            for direction in ('lower', 'upper')]
    partial = {'state': 'available', 'unknown_count': 1, 'bounds': found['bounds'],
               'attained': [proofs[key]['measurement']['delta'] for key in keys], 'proof_keys': keys}
    blocked = {'state': 'input_blocked', 'reason': 'motion_unavailable_for_census_instances',
               'bounds': None, 'attained': None, 'proof_keys': None}
    parent = {'image_id': item['id'], 'state': 'complete', 'known_references': [],
        'known_only_measurement': found['known'], 'current_unknown_instances': unknown,
        'union_unknown_instances': unknown, 'candidate_pool': pool, 'searches': {'current': found, 'union': found},
        'proofs': proofs, 'contracts': {key: deepcopy(partial if key.endswith('_partial') else blocked) for key in CONTRACTS}}
    contracts = ['current_partial', 'union_partial']; record = refine(item, parent, contracts)
    return item, parent, contracts, record


class VerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.item, cls.parent, cls.contracts, cls.record = synthetic()

    def check(self, record, cache=None):
        return check_image(record, self.parent, self.item, self.contracts,
                           cache if cache is not None else {'native': set(), 'native_check_seconds': 0.0})

    def test_complete_refinement_and_membership_reuse(self):
        failures, measurements = self.check(self.record)
        self.assertEqual(failures, {}); self.assertGreater(measurements, 0)
        self.assertEqual(self.record['refinement']['contracts']['union_partial']['reused_from'], 'current_partial')
        self.assertEqual(list(map(q, self.record['contracts']['current_partial']['attained'])), [-2, 2])

    def test_pool_neighborhood_forgery_rejected(self):
        bad = deepcopy(self.record); bad['refinement']['pool']['neighborhoods'][0] = []
        with self.assertRaisesRegex(ValueError, 'coverage'): self.check(bad)

    def test_pool_threshold_cell_omission_rejected(self):
        bad = deepcopy(self.record); bad['refinement']['pool']['axis_cells'] -= 1
        with self.assertRaisesRegex(ValueError, 'coverage'): self.check(bad)

    def test_unknown_instance_omission_rejected(self):
        bad = deepcopy(self.record); bad['current_unknown_instances'] = []
        with self.assertRaisesRegex(ValueError, 'Inherited evidence'): self.check(bad)

    def test_search_count_forgery_rejected(self):
        bad = deepcopy(self.record); bad['refinement']['contracts']['current_partial']['search']['unique_flow_measurements'] += 1
        with self.assertRaisesRegex(ValueError, 'accounting'): self.check(bad)

    def test_zero_width_universal_bound_forgery_rejected(self):
        bad = deepcopy(self.record); bad['contracts']['current_partial']['bounds'] = [w(0), w(0)]
        with self.assertRaisesRegex(ValueError, 'Contract changed'): self.check(bad)

    def test_native_payload_mutation_after_cached_check_rejected(self):
        cache = {'native': set(), 'native_check_seconds': 0.0}; self.check(self.record, cache)
        bad = deepcopy(self.record); key = bad['refinement']['contracts']['current_partial']['searched_proof_keys'][0]
        bad['proofs'][key]['proof']['payload']['result']['bounds']['lower'] = w(99)
        with self.assertRaises(Exception): self.check(bad, cache)

    def test_complete_component_cannot_be_silently_dropped(self):
        bad = deepcopy(self.record); del bad['refinement']['contracts']['union_partial']
        with self.assertRaisesRegex(ValueError, 'omitted'): self.check(bad)

    def test_inherited_endpoint_cannot_be_lost(self):
        bad = deepcopy(self.record); bad['contracts']['current_partial']['attained'] = [w(0), w(0)]
        with self.assertRaisesRegex(ValueError, 'Contract changed'): self.check(bad)


if __name__ == '__main__':
    unittest.main()
