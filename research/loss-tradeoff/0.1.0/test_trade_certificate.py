from copy import deepcopy
from fractions import Fraction as F
import json
from pathlib import Path
import tempfile
import unittest

from trade_certificate import check_admission, check_cells, check_component
from trade_math import partition
from trade_sources import checked_index, component, digest, file_digest, q, w
from compare_math import checked_ranks


def box(identity, x=10, y=10, width=30, height=30):
    values = [w(F(value)) for value in (x, y, x+width, y+height)]
    return {'id': identity, 'record_sha256': digest({'id': identity, 'xyxy': values}), 'xyxy': values}


def image(a=None, b=None):
    return {'id': 'image-00', 'ordinal': 0, 'width': 100, 'height': 100,
            'image_sha256': 'a'*64, 'policy_sha256': 'b'*64, 'reference_input_state': 'available',
            'output_a': {'state': 'observed', 'value': [box('a')] if a is None else a},
            'output_b': {'state': 'observed', 'value': [box('b')] if b is None else b}}


def cache():
    return {'sources': {}, 'counts': {}, 'native': set()}


class TradeCertificateControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.directory = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def fixture(self, im=None, refs=None, mutate=None):
        im = image() if im is None else im; refs = [box('r')] if refs is None else refs
        measured, proof, timing = checked_ranks(im, refs)
        if mutate: mutate(proof)
        key = digest({'subject_sha256': digest(im), 'references': refs}); edit = {'operation': 'none'}
        source = {'radii': {'0': {'lower': {'edit': edit, 'proof_key': key, 'delta': measured['delta']}}},
                  'proofs': {key: {'measurement': measured, 'proof': proof, 'timing': timing,
                                    'subject_sha256': digest(im), 'reference_sha256': digest(refs)}}}
        path = self.directory / 'source.json'; path.write_text(json.dumps(source))
        _, value = component(im, refs, refs, measured, proof, path, '/radii/0/lower',
                             {'kind': 'exact_projection', 'radius': None, 'edit': edit})
        return im, refs, value, {str(path): file_digest(path)}

    def test_native_world_and_direct_counts_verify_and_reuse(self):
        im, refs, value, allowed = self.fixture(); checked = cache()
        first = check_component(im, refs, value, checked, allowed)
        second = check_component(im, refs, value, checked, allowed)
        self.assertEqual(first, second); self.assertEqual(len(checked['native']), 1)
        self.assertEqual(len(checked['counts']), 1); self.assertEqual(first['unit'], 0)

    def test_observed_empty_world_stays_distinct_from_unavailable(self):
        im, refs, value, allowed = self.fixture(image([], []), []); result = check_component(im, refs, value, cache(), allowed)
        self.assertTrue(all(row['references'] == row['matches'] == 0 for row in result['counts']))
        broken = deepcopy(im); broken['output_a'] = {'state': 'unavailable', 'reason': 'no packet'}
        with self.assertRaises((ValueError, KeyError)): check_component(broken, refs, value, cache(), allowed)

    def test_changed_context_counts_or_source_pointer_rejected(self):
        im, refs, value, allowed = self.fixture()
        for field, replacement in [('image_id', 'image-01'), ('subject_sha256', 'c'*64),
                                    ('reference_count', 0), ('prediction_counts', [0, 1])]:
            broken = deepcopy(value); broken[field] = replacement
            with self.assertRaises(ValueError): check_component(im, refs, broken, cache(), allowed)
        broken = deepcopy(value); broken['source']['pointer'] = '/radii/unknown/lower'
        with self.assertRaises(ValueError): check_component(im, refs, broken, cache(), allowed)

    def test_unbound_or_modified_source_bytes_rejected(self):
        im, refs, value, allowed = self.fixture()
        with self.assertRaises(ValueError): check_component(im, refs, value, cache(), {})
        Path(value['source']['path']).write_text('{}')
        with self.assertRaises(ValueError): check_component(im, refs, value, cache(), allowed)

    def test_native_claim_corruption_cannot_enter_as_a_new_source(self):
        def corrupt(proof): proof['payload']['result']['bounds']['lower'] = w(F(99))
        im, refs, value, allowed = self.fixture(mutate=corrupt)
        with self.assertRaises(ValueError): check_component(im, refs, value, cache(), allowed)

    def test_proof_mutation_after_cache_check_rejected(self):
        im, refs, value, allowed = self.fixture(); checked = cache(); check_component(im, refs, value, checked, allowed)
        broken = deepcopy(value); broken['native_proof']['payload']['result']['bounds']['upper'] = w(F(99))
        with self.assertRaises(ValueError): check_component(im, refs, broken, checked, allowed)

    def test_single_edit_budget_and_translation_shape_radius_source(self):
        refs = [box('r')]; moved = box('m', 12, 10)
        axis_edit = {'operation': 'translation', 'source_reference_id': 'r', 'source_reference_sha256': refs[0]['record_sha256'],
                     'axis': 0, 'position': w(F(12)), 'distance': w(F(2)), 'translated_reference': moved}
        admission = {'kind': 'axis_translation', 'radius': w(F(2)), 'edit': axis_edit}
        check_admission(refs, [moved], admission)
        broken = deepcopy(admission); broken['radius'] = w(F(1))
        with self.assertRaises(ValueError): check_admission(refs, [moved], broken)
        broken = deepcopy(admission); broken['edit']['axis'] = 1
        with self.assertRaises(ValueError): check_admission(refs, [moved], broken)
        changed = box('m', 12, 10, 31); broken = deepcopy(admission); broken['edit']['translated_reference'] = changed
        with self.assertRaises(ValueError): check_admission(refs, [changed], broken)
        arbitrary = {'kind': 'one_edit_per_image', 'radius': None,
                     'edit': {'operation': 'insertion', 'removed_reference': None, 'inserted_reference': moved}}
        check_admission(refs, refs+[moved], arbitrary)
        with self.assertRaises(ValueError): check_admission(refs, refs+[moved, box('extra')], arbitrary)

    def test_complete_index_rejects_missing_duplicate_changed_and_wrong_identity(self):
        path = self.directory/'image-00.json'; path.write_text('{}')
        entry = {'image_id': 'image-00', 'path': path.name, 'sha256': file_digest(path)}
        self.assertEqual(checked_index([entry], {'image-00'}, self.directory), {'image-00': path})
        for entries in ([], [entry, entry]):
            with self.assertRaises(ValueError): checked_index(entries, {'image-00'}, self.directory)
        broken = deepcopy(entry); broken['image_id'] = 'image-01'
        with self.assertRaises(ValueError): checked_index([broken], {'image-00'}, self.directory)
        path.write_text('{"changed":true}')
        with self.assertRaises(ValueError): checked_index([entry], {'image-00'}, self.directory)

    def test_continuum_includes_equality_and_rejects_missing_endpoint_or_false_sign(self):
        functions = [(F(3), F(-4)), (F(3), F(-4))]
        cells = [{key: w(value) if isinstance(value, F) else list(map(w, value)) if key == 'bounds' else value
                  for key, value in cell.items()} for cell in partition((2, 2), 4)]
        self.assertEqual(check_cells(cells, functions), 5)
        broken = deepcopy(cells); broken.pop(2)
        with self.assertRaises(ValueError): check_cells(broken, functions)
        broken = deepcopy(cells); broken[2]['decision'] = 'supported'
        with self.assertRaises(ValueError): check_cells(broken, functions)
        broken = deepcopy(cells); broken[1]['right'] = w(F(7, 10))
        with self.assertRaises(ValueError): check_cells(broken, functions)


if __name__ == '__main__':
    unittest.main()
