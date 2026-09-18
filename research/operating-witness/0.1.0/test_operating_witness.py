"""Filtered synthetic worlds, composition and critical evidence mutations."""
from copy import deepcopy
from fractions import Fraction
import unittest

from operating_witness import aggregate, digest, refine
from operating_witness_verify import check_refinement, edited_world
from operating_certificate import check_case, verify_proof
from operating_math import analyze_state, world_banks, FAMILIES
from operating_sources import ANCHORS, filtered_image, q, w
from test_operating_math import synthetic_sources


class WitnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        image, packets, original, edit, temporal = synthetic_sources()
        cls.bank = world_banks(original, edit, temporal); cls.proofs = {}; cls.rows = []
        for threshold in ANCHORS:
            item, custody = filtered_image(image, packets, threshold, '3' * 64)
            before = {'image': item, 'custody': custody, 'analysis': analyze_state(item, cls.bank, cls.proofs)}
            # Deliberately restrict the inherited attained bank to its nominal world.
            # This creates a concrete valid, incomplete witness bank for the adapter.
            for family in ('one_edit_global', 'one_edit_per_image'):
                value = before['analysis']['families'][family]
                value['attained'] = [before['analysis']['nominal']['delta']] * 2
                value['proof_keys'] = [before['analysis']['nominal_proof_key']] * 2
            new = {}; after, detail = refine(before, cls.bank, new)
            cls.rows.append((before, after, detail, new))

    def test_all_anchors_and_families_have_separate_case_checks(self):
        checks = 0
        for before, after, detail, new in self.rows:
            check_refinement(before, after, self.bank, detail, new)
            key = digest({'image': before['image'], 'custody': before['custody']})
            case = {'id': 'synthetic-case', 'group': 'primary', 'images': [before['image']['id']]}
            states = {key: after}; proofs = {**self.proofs, **new}
            for family in FAMILIES:
                row = aggregate(case, family, [key], states)
                check_case(row, case, family, [key], states, proofs); checks += 1
        self.assertEqual(checks, 56)
        self.assertTrue(any(any(r[2].get('improved_endpoints', [])) for r in self.rows))

    def test_new_native_worlds_have_separate_matching(self):
        cache = {'native': set(), 'native_check_seconds': 0.0}
        for _, _, _, new in self.rows:
            for key, proof in new.items(): verify_proof(key, proof, cache)
        self.assertGreater(len(cache['native']), 0)

    def test_inherited_exact_state_is_kept(self):
        before = deepcopy(self.rows[-1][0]); value = before['analysis']['families']['one_edit_per_image']
        self.assertEqual(value['bounds'], value['attained'])
        after, detail = refine(before, self.bank, {})
        self.assertEqual(detail['state'], 'inherited_exact'); self.assertEqual(before, after)

    def test_failure_retains_original_state_and_reason(self):
        before = self.rows[0][0]
        detail = {'state': 'search_incomplete', 'new_search': True, 'error': 'Declared synthetic cap'}
        check_refinement(before, deepcopy(before), self.bank, detail, {})
        bad = deepcopy(before); bad['image']['width'] += 1
        with self.assertRaisesRegex(ValueError, 'failed state'): check_refinement(before, bad, self.bank, detail, {})

    def test_changed_bound_and_other_family_are_rejected(self):
        before, after, detail, new = next(r for r in self.rows if r[2]['state'] == 'complete')
        for family in ('one_edit_per_image', 'current_partial'):
            bad = deepcopy(after); bad['analysis']['families'][family]['bounds'][0] = w(99)
            with self.assertRaisesRegex(ValueError, 'another input'): check_refinement(before, bad, self.bank, detail, new)

    def test_forged_edit_and_omitted_proof_are_rejected(self):
        before, after, detail, new = next(r for r in self.rows if r[2]['state'] == 'complete')
        bad = deepcopy(detail); bad['search']['witnesses']['lower']['edit']['removed_reference'] = 'missing'
        with self.assertRaises(ValueError): check_refinement(before, after, self.bank, bad, new)
        with self.assertRaisesRegex(ValueError, 'proof omitted'): check_refinement(before, after, self.bank, detail, {})

    def test_unavailable_input_does_not_become_empty(self):
        bad = deepcopy(self.rows[0][0]); bad['analysis']['families']['one_edit_per_image']['state'] = 'input_blocked'
        with self.assertRaisesRegex(ValueError, 'unavailable'): refine(bad, self.bank, {})

    def test_native_payload_mutation_is_rejected(self):
        key, original = next(iter(next(r[3] for r in self.rows if r[3]).items()))
        bad = deepcopy(original); bad['proof']['payload']['result']['bounds']['lower'] = w(99)
        with self.assertRaises(Exception): verify_proof(key, bad, {'native': set(), 'native_check_seconds': 0.0})


if __name__ == '__main__': unittest.main()
