from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
import unittest

from tools.perception_revision.contract import Invalid
from tools.perception_revision.nuscenes import normalize_frame


def row(x=0, score='0.9'):
    return {'sample_token': 'sample', 'detection_name': 'car', 'translation': [x, 0, 0],
            'detection_score': Decimal(score)}


class ReplacementNormalizationTests(unittest.TestCase):
    def normalize(self, aa, bb, same_source=False):
        return normalize_frame(sample_token='sample', anchor_id='anchor', ego_xy=[0, 0],
            weight=Fraction(1), output_a=aa, output_b=bb,
            source_sha256={'output_a': 'a' * 64, 'output_b': ('a' if same_source else 'b') * 64,
                           'clock': 'c' * 64})

    def test_outputs_are_independent_and_no_cross_suppression_occurs(self):
        aa = {'state': 'observed', 'value': [row()]}
        bb = {'state': 'observed', 'value': [row(), row(1), row(50, '0.30'), row(51), row(0, '0.299')]}
        original = deepcopy(bb)
        anchor, receipt = self.normalize(aa, bb)
        self.assertEqual(bb, original)
        self.assertEqual(len(anchor['output_a']['value']), 1)
        self.assertEqual(len(anchor['output_b']['value']), 3)
        self.assertEqual(len(receipt['trace']), 6)
        self.assertEqual(receipt['additional_suppression'], 'none')
        missing = {'state': 'missing', 'reason': 'A not available'}
        anchor, _ = self.normalize(missing, bb)
        self.assertEqual(anchor['output_a'], missing)
        self.assertEqual(len(anchor['output_b']['value']), 3)

    def test_common_source_rows_share_identity_but_conflicting_bytes_fail(self):
        observed = {'state': 'observed', 'value': [row()]}
        anchor, receipt = self.normalize(observed, observed, same_source=True)
        self.assertEqual(anchor['output_a'], anchor['output_b'])
        self.assertEqual(len(receipt['qualified_records']), 1)
        changed = deepcopy(observed)
        changed['value'][0]['translation'][0] = 1
        with self.assertRaises(Invalid) as raised:
            self.normalize(observed, changed, same_source=True)
        self.assertEqual(raised.exception.code, 'COMMON_OUTPUT_IDENTITY')

    def test_wrong_sample_and_binary_float_cannot_enter_qualification(self):
        observed = {'state': 'observed', 'value': [row()]}
        changed = deepcopy(observed)
        changed['value'][0]['sample_token'] = 'another-sample'
        with self.assertRaises(Invalid):
            self.normalize(observed, changed)
        changed = deepcopy(observed)
        changed['value'][0]['detection_score'] = 0.9
        with self.assertRaises(Invalid):
            self.normalize(observed, changed)


if __name__ == '__main__':
    unittest.main()
