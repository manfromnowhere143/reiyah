"""Synthetic full-world checks across filters and all reference contracts."""
from copy import deepcopy
from fractions import Fraction
import unittest

from operating_sources import ANCHORS, ROLES, digest, filtered_image, filtered_operand, q, w
from operating_math import FAMILIES, aggregate, analyze_state, measured_world, world_banks
from operating_certificate import check_case, independent_analysis, verify_proof
from operating_verify import check_bank
from timing_bounds import unknown_rectangle
from test_timing_bounds import image, rectangle


def synthetic_sources():
    original = [rectangle('r1', [10, 10, 40, 40]), rectangle('r2', [60, 60, 90, 90])]
    addition = rectangle('inserted', [65, 10, 95, 40])
    edit = {'search_state': 'complete', 'search': {'witnesses': {}}}
    for direction, removed, inserted in [('lower', 'r2', addition), ('upper', 'r1', None)]:
        operation = 'deletion' if inserted is None else 'replacement'
        refs = [row for row in original if row['id'] != removed]+([] if inserted is None else [inserted])
        edit['search']['witnesses'][direction] = {'edit': {'operation': operation, 'removed_reference': removed,
                                                         'inserted_reference': inserted}, 'altered_references': refs}
    known = original[:1]; optional = unknown_rectangle('u', addition['xyxy'])
    temporal = {'known_references': known, 'current_unknown_instances': ['u'], 'union_unknown_instances': None,
                'proofs': {'known': {'references': known}, 'optional': {'references': known+[optional]}}}
    a = [(0.4, [10, 10, 40, 40]), (0.9, [60, 60, 90, 90])]
    b = [(0.8, [10, 10, 40, 40]), (0.6, [65, 10, 95, 40])]
    item = image([], []); packets = {}
    for role, values in zip(ROLES, (a, b)):
        row = {'id': item['id'], 'state': 'processed', 'detections': [
            {'id': 'd'+str(i), 'category_id': 2, 'category_name': 'car', 'score': score, 'xyxy': box}
            for i, (score, box) in enumerate(values)]}
        item[role], _ = filtered_operand(row, Fraction(1, 4)); packets[role] = {item['id']: row}
    return item, packets, original, edit, temporal


class MathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_image, cls.packets, cls.original, cls.edit, cls.temporal = synthetic_sources()
        cls.bank = world_banks(cls.original, cls.edit, cls.temporal); cls.proofs = {}; cls.states = {}; cls.by_threshold = {}
        for threshold in ANCHORS:
            item, custody = filtered_image(cls.original_image, cls.packets, threshold, '3'*64)
            key = digest({'image': item, 'custody': custody})
            if key not in cls.states:
                cls.states[key] = {'image': item, 'custody': custody, 'analysis': analyze_state(item, cls.bank, cls.proofs)}
            cls.by_threshold[threshold] = key

    def test_world_bank_eligibility_and_census(self):
        check_bank(self.bank, self.original, self.edit, self.temporal)
        self.assertEqual(self.bank['temporal']['union']['state'], 'input_blocked')
        self.assertEqual(len(self.bank['deletions']), 3)

    def test_all_filtered_states_and_native_proofs_independently_agree(self):
        cache = {'native': set(), 'native_check_seconds': 0.0}
        for key, proof in self.proofs.items(): verify_proof(key, proof, cache)
        for state in self.states.values():
            self.assertEqual(state['analysis'], independent_analysis(state['image'], self.bank, self.proofs))
        self.assertEqual(len(cache['native']), len(self.proofs))

    def test_all_anchor_and_family_rows_agree(self):
        case = {'id': 'one', 'group': 'primary', 'images': ['synthetic']}; count = 0
        for threshold, key in self.by_threshold.items():
            for family in FAMILIES:
                row = aggregate(case, family, [key], self.states)
                check_case(row, case, family, [key], self.states, self.proofs); count += 1
        self.assertEqual(count, 56)

    def test_empty_predictions_do_not_relabel_missing_union_census(self):
        key = self.by_threshold[Fraction(1)]; state = self.states[key]
        self.assertEqual(state['analysis']['prediction_counts'], [0, 0])
        self.assertEqual(state['analysis']['families']['union_partial']['state'], 'input_blocked')
        self.assertEqual(state['analysis']['families']['current_strict']['state'], 'input_blocked')
        self.assertEqual(list(map(q, state['analysis']['families']['current_partial']['bounds'])), [0, 0])

    def test_full_case_composition_global_and_per_image(self):
        original_key = self.by_threshold[Fraction(1, 4)]; state = deepcopy(self.states[original_key])
        state['image']['id'] = 'another'; proofs = dict(self.proofs)
        state['analysis'] = analyze_state(state['image'], self.bank, proofs)
        key = digest({'image': state['image'], 'custody': state['custody']}); states = {**self.states, key: state}
        case = {'id': 'both', 'group': 'primary', 'images': ['synthetic', 'another']}
        for family in FAMILIES:
            row = aggregate(case, family, [original_key, key], states)
            check_case(row, case, family, [original_key, key], states, proofs)
        global_row = aggregate(case, 'one_edit_global', [original_key, key], states)
        per_image = aggregate(case, 'one_edit_per_image', [original_key, key], states)
        self.assertLessEqual(q(per_image['bounds'][0]), q(global_row['bounds'][0]))
        self.assertGreaterEqual(q(per_image['bounds'][1]), q(global_row['bounds'][1]))

    def test_cached_world_cost_not_duplicated(self):
        proof = next(iter(self.proofs.values())); cache = {}
        first = measured_world(proof['image'], proof['references'], cache)
        second = measured_world(deepcopy(proof['image']), deepcopy(proof['references']), cache)
        self.assertEqual(first, second); self.assertEqual(len(cache), 1)

    def test_deleted_world_omission_rejected(self):
        bank = deepcopy(self.bank); bank['deletions'].pop()
        with self.assertRaisesRegex(ValueError, 'world bank'): check_bank(bank, self.original, self.edit, self.temporal)

    def test_unknown_census_cannot_be_replaced_with_empty(self):
        bank = deepcopy(self.bank); bank['temporal']['union'] = {'state': 'available', 'unknown_count': 0, 'unknown_ids': [], 'worlds': []}
        with self.assertRaisesRegex(ValueError, 'census'): check_bank(bank, self.original, self.edit, self.temporal)

    def test_forged_case_bound_and_membership_rejected(self):
        case = {'id': 'one', 'group': 'primary', 'images': ['synthetic']}; key = self.by_threshold[Fraction(1, 4)]
        original = aggregate(case, 'one_edit_per_image', [key], self.states)
        bad = deepcopy(original); bad['bounds'][0] = w(99)
        with self.assertRaisesRegex(ValueError, 'Case bounds'): check_case(bad, case, 'one_edit_per_image', [key], self.states, self.proofs)
        bad = deepcopy(original); bad['membership'] = []
        with self.assertRaisesRegex(ValueError, 'allocation'): check_case(bad, case, 'one_edit_per_image', [key], self.states, self.proofs)

    def test_native_payload_mutation_is_rechecked_after_cache(self):
        key, proof = next(iter(self.proofs.items())); cache = {'native': set(), 'native_check_seconds': 0.0}
        verify_proof(key, proof, cache); bad = deepcopy(proof)
        bad['proof']['payload']['result']['bounds']['lower'] = w(99)
        with self.assertRaises(Exception): verify_proof(key, bad, cache)

    def test_changed_reference_world_cannot_reuse_old_proof(self):
        key, proof = next(iter(self.proofs.items())); bad = deepcopy(proof)
        bad['references'] = [rectangle('forged', [0, 0, 25, 25])]
        with self.assertRaisesRegex(ValueError, 'substitutes'): verify_proof(key, bad, {'native': set(), 'native_check_seconds': 0.0})


if __name__ == '__main__':
    unittest.main()
