from copy import deepcopy
from fractions import Fraction as F
import unittest

from trade_run import build_case, incomplete_case
from trade_sources import families, q, w
from trade_verify import check_incomplete, check_row


def fixture():
    case = {'id': 'two-images', 'group': 'primary', 'images': ['first', 'second']}
    family_list = families(); contexts = {}; pool = {}; verified = {}
    # Abstract source worlds with fixed prediction counts and varying rank differences.
    for iid, count, ranks in [('first', 2, (-1, -2, 0)), ('second', -1, (1, 0, 2))]:
        keys = []
        for label, rank_difference in zip(('nominal', 'lower', 'upper'), ranks):
            key = iid + ':' + label; keys.append(key); unit = count + 2*rank_difference
            pool[key] = {'world': [{'id': key}], 'measurement': {'delta': w(F(unit))}}
            verified[key] = {'image_id': iid, 'unit': F(unit), 'false_positive_difference': count+rank_difference,
                             'miss_difference': rank_difference}
        contexts[iid] = {'nominal': keys[0], 'original': pool[keys[0]]['world'], 'count_difference': count, 'families': {}}
        for family in family_list:
            selected = [keys[0], keys[0]] if family['kind'] == 'exact_projection' else keys[1:]
            contexts[iid]['families'][family['id']] = {'worlds': selected,
                'unit_bounds': [pool[key]['measurement']['delta'] for key in selected]}
    return case, contexts, pool, verified


class TradeRunControls(unittest.TestCase):
    def test_all_declared_family_compositions_and_displayed_shares_verify(self):
        case, contexts, pool, verified = fixture()
        for family in families():
            row = build_case(case, family, contexts, pool)
            self.assertGreaterEqual(check_row(row, case, family, contexts, pool, verified), 3)
            self.assertEqual(len(row['grid']), 9)

    def test_global_edit_budget_differs_from_product_world(self):
        case, contexts, pool, verified = fixture(); available = {f['id']: f for f in families()}
        global_row = build_case(case, available['one_edit_global'], contexts, pool)
        product_row = build_case(case, available['one_edit_per_image'], contexts, pool)
        self.assertEqual(list(map(q, global_row['source']['unit_bounds'])), [F(-1, 2), F(3, 2)])
        self.assertEqual(list(map(q, product_row['source']['unit_bounds'])), [F(-3, 2), F(5, 2)])
        broken = deepcopy(global_row); broken['source']['worlds'] = product_row['source']['worlds']
        with self.assertRaises(ValueError): check_row(broken, case, available['one_edit_global'], contexts, pool, verified)

    def test_missing_case_member_or_wrong_component_rejected(self):
        case, contexts, pool, verified = fixture(); family = families()[0]
        row = build_case(case, family, contexts, pool); broken = deepcopy(row)
        broken['source']['worlds'][0].pop()
        with self.assertRaises(ValueError): check_row(broken, case, family, contexts, pool, verified)
        broken = deepcopy(row); broken['source']['worlds'][0][0]['component'] = 'second:nominal'
        with self.assertRaises(ValueError): check_row(broken, case, family, contexts, pool, verified)

    def test_changed_weight_sign_ratio_or_source_bound_rejected(self):
        case, contexts, pool, verified = fixture(); family = families()[0]; row = build_case(case, family, contexts, pool)
        broken = deepcopy(row); broken['grid'][3]['bounds'][0] = w(F(99))
        with self.assertRaises(ValueError): check_row(broken, case, family, contexts, pool, verified)
        broken = deepcopy(row); broken['grid'][-1]['ratio_kind'] = 'finite'; broken['grid'][-1]['miss_fp_ratio'] = w(F(999))
        with self.assertRaises(ValueError): check_row(broken, case, family, contexts, pool, verified)
        broken = deepcopy(row); broken['source']['unit_bounds'][0] = w(F(-99))
        with self.assertRaises(ValueError): check_row(broken, case, family, contexts, pool, verified)

    def test_absence_retains_all_settings_without_zero_or_decision(self):
        case, _, _, _ = fixture(); family = families()[0]; row = incomplete_case(case, family, 'Required source missing')
        check_incomplete(row, case, family); self.assertEqual(len(row['grid']), 9)
        broken = deepcopy(row); broken['grid'][0]['decision'] = 'excluded'
        with self.assertRaises(ValueError): check_incomplete(broken, case, family)
        broken = deepcopy(row); broken['grid'].pop()
        with self.assertRaises(ValueError): check_incomplete(broken, case, family)


if __name__ == '__main__':
    unittest.main()
