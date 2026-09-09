"""Synthetic source-boundary checks; no physical study observations are used."""
from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import unittest

from tools.perception_decision import checker, contract, kernel, nuscenes


def prediction(x='0', y='0', score='0.9', label='car'):
    return {'sample_token': 'synthetic-sample', 'translation': [Decimal(x), Decimal(y), 0],
            'detection_score': Decimal(score), 'detection_name': label}


def inputs(base=None, camera=None):
    return {'sample_token': 'synthetic-sample', 'anchor_id': 'synthetic-anchor',
            'ego_xy': [0, 0], 'weight': Fraction(1),
            'base': {'state': 'observed', 'value': [] if base is None else base},
            'camera': {'state': 'observed', 'value': [] if camera is None else camera},
            'source_sha256': {'base': 'a'*64, 'camera': 'b'*64, 'clock': 'c'*64}}


def ids(anchor, role):
    return [row['id'] for row in anchor[role]['value']]


class NuScenesNormalizerTests(unittest.TestCase):
    def normalize(self, values):
        before = deepcopy(values)
        anchor, receipt = nuscenes.normalize_frame(**values)
        # The receipt must retain the normalized records named by core detection hashes.
        records = receipt['qualified_records']
        by_id = {row['detection']['id']: row for row in records}
        self.assertEqual(len(by_id), len(records))
        for row in records:
            self.assertEqual(row['detection']['record_sha256'],
                             hashlib.sha256(contract.encoded(row['record'])).hexdigest())
        self.assertEqual(receipt['normalized_anchor_sha256'], hashlib.sha256(contract.encoded(anchor)).hexdigest())
        for role in ('base', 'additions'):
            if anchor[role]['state'] == 'observed':
                for detection in anchor[role]['value']:
                    self.assertEqual(detection, by_id[detection['id']]['detection'])
        self.assertEqual(values, before)
        return anchor, receipt

    def rejected(self, values, code):
        with self.assertRaises(contract.Invalid) as exc:
            nuscenes.normalize_frame(**values)
        self.assertEqual(exc.exception.code, code)

    def test_exact_score_and_range_boundaries_account_for_every_row(self):
        rows = [prediction('30', '40', '0.30'), prediction('50.000000000000000000000000000001'),
                prediction('0', '0', '0.29999999999999999999999999999999'),
                prediction('50', score='0.299'), prediction('-50', score='1')]
        anchor, receipt = self.normalize(inputs(rows))
        self.assertEqual(ids(anchor, 'base'), ['base:0', 'base:4'])
        self.assertEqual([(r['score_eligible'], r['range_eligible']) for r in receipt['trace']],
                         [(True, True), (True, False), (False, True), (False, True), (True, True)])
        self.assertEqual(receipt['input_counts'], {'base': 5, 'camera': 0})
        self.assertEqual(len(receipt['trace']), 5)

    def test_suppression_gate_is_strict_and_class_specific(self):
        values = inputs([prediction()], [prediction('2'), prediction('1.9999999999999999999999999999999'),
                                         prediction('0', label='pedestrian')])
        anchor, receipt = self.normalize(values)
        self.assertEqual(ids(anchor, 'additions'), ['camera:0', 'camera:2'])
        self.assertEqual(receipt['trace'][2]['retention'], 'suppressed')
        self.assertEqual(receipt['trace'][2]['blocked_by'], 'base:0')

    def test_camera_order_is_score_then_original_index(self):
        values = inputs(camera=[prediction('0', score='0.7'), prediction('1', score='0.9'),
                                prediction('5', score='0.9'), prediction('6', score='0.9')])
        anchor, receipt = self.normalize(values)
        self.assertEqual(ids(anchor, 'additions'), ['camera:1', 'camera:2'])
        self.assertEqual([r['blocked_by'] for r in receipt['trace']], ['camera:1', None, None, 'camera:2'])
        self.assertEqual([r['source_index'] for r in receipt['trace']], [0, 1, 2, 3])

    def test_base_duplicates_are_preserved(self):
        anchor, receipt = self.normalize(inputs([prediction(), prediction()], [prediction('0.1')]))
        self.assertEqual(ids(anchor, 'base'), ['base:0', 'base:1'])
        self.assertEqual(ids(anchor, 'additions'), [])
        self.assertEqual([r['retention'] for r in receipt['trace']],
                         ['base_retained', 'base_retained', 'suppressed'])
        self.assertNotEqual(anchor['base']['value'][0]['record_sha256'], anchor['base']['value'][1]['record_sha256'])

    def test_translation_and_decimal_context_do_not_change_selection(self):
        values = inputs([prediction('0.125', '0.25')], [prediction('2.125', '0.25'), prediction('0.125', '0.25')])
        original, _ = self.normalize(values)
        moved = deepcopy(values)
        shift = [Decimal('1000'), Decimal('-2000')]
        moved['ego_xy'] = shift
        for output in (moved['base'], moved['camera']):
            for row in output['value']:
                row['translation'][:2] = [v+s for v, s in zip(row['translation'], shift)]
        translated, _ = self.normalize(moved)
        self.assertEqual(ids(translated, 'base'), ids(original, 'base'))
        self.assertEqual(ids(translated, 'additions'), ids(original, 'additions'))
        # Fraction arithmetic must not inherit ambient Decimal rounding at a boundary.
        edge_case = inputs(camera=[prediction('50.000000000000000000000000000001')])
        with localcontext() as context:
            context.prec = 2
            low_precision, _ = self.normalize(edge_case)
        self.assertEqual(ids(low_precision, 'additions'), [])

    def test_unavailable_outputs_never_become_observed_empty(self):
        for state in sorted(nuscenes.UNAVAILABLE):
            with self.subTest(state=state):
                values = inputs(camera=[prediction()])
                values['base'] = {'state': state, 'reason': 'frame absent from a known parent source'}
                anchor, receipt = self.normalize(values)
                self.assertEqual(anchor['base'], values['base'])
                self.assertEqual(anchor['additions']['state'], 'unknown')
                self.assertNotIn('value', anchor['additions'])
                self.assertIsNone(receipt['input_counts']['base'])
                self.assertEqual(receipt['source_sha256']['base'], 'a'*64)
                self.assertEqual(receipt['trace'][0]['retention'], 'unknown_base_unavailable')
                values = inputs([prediction()])
                values['camera'] = {'state': state, 'reason': 'source unavailable'}
                values['source_sha256']['camera'] = None
                anchor, receipt = self.normalize(values)
                self.assertEqual(anchor['additions'], values['camera'])
                self.assertIsNone(receipt['input_counts']['camera'])

    def test_normalized_anchor_enters_core_only_as_open_reference(self):
        root = Path(__file__).resolve().parents[1]
        case = json.loads((root / 'research/perception-decision/0.1.0/matching-ambiguity.json').read_text())
        case['model'] = {'variables': [], 'clauses': []}
        for rows, expected in [([], 0), ([prediction('4')], 1)]:
            anchor, _ = self.normalize(inputs([prediction()], rows))
            case['anchors'] = [anchor]
            payload = kernel.produce(contract.validate(case))
            result = checker.check(case, payload)
            self.assertEqual(result['bounds'], {'lower': contract.wire(Fraction(-expected)),
                                                 'upper': contract.wire(Fraction(expected))})
            self.assertEqual(result['physical_coverage'], 'not_established')
            self.assertEqual(result['enclosure_kind'], 'conservative_open_reference')

    def test_required_numbers_reject_float_nonfinite_and_out_of_scope(self):
        invalid = [0.3, True, '0.3', Decimal('NaN'), Decimal('Infinity'), Decimal('1e-33'),
                   Decimal('0.'+'1'*33), 10**12+1]
        for number in invalid:
            for field in ('ego', 'xy', 'score'):
                with self.subTest(number=str(number), field=field):
                    values = inputs([prediction()])
                    if field == 'ego':
                        values['ego_xy'][0] = number
                    elif field == 'xy':
                        values['base']['value'][0]['translation'][0] = number
                    else:
                        values['base']['value'][0]['detection_score'] = number
                    self.rejected(values, 'ADAPTER_NUMBER')
        for score in ('-0.1', '1.01'):
            self.rejected(inputs([prediction(score=score)]), 'ADAPTER_SCORE')

    def test_unused_nonfinite_velocity_is_not_imputed_or_used(self):
        # These fields are outside the declared XY/count computation, not valid measurements.
        row = prediction()
        row.update(velocity=[float('nan'), float('nan')], rotation=None, size=None, attribute_name=None)
        row['translation'][2] = float('nan')
        anchor, receipt = nuscenes.normalize_frame(**inputs([row]))
        self.assertEqual(ids(anchor, 'base'), ['base:0'])
        self.assertIn('velocity', receipt['unused_prediction_fields'])
        self.assertIn('translation_z', receipt['unused_prediction_fields'])
        self.assertNotIn('velocity', receipt['qualified_records'][0]['record'])

    def test_source_identity_binds_normalized_records(self):
        values = inputs([prediction()])
        first, _ = self.normalize(values)
        values['source_sha256']['base'] = 'd'*64
        second, _ = self.normalize(values)
        self.assertEqual(ids(first, 'base'), ids(second, 'base'))
        self.assertNotEqual(first['base']['value'][0]['record_sha256'], second['base']['value'][0]['record_sha256'])
        for digest in (None, 'g'*64, 'a'*63, 'A'*64, 0):
            values['source_sha256']['base'] = digest
            self.rejected(values, 'ADAPTER_SOURCE')

    def test_frame_cap_rejects_without_clipping(self):
        values = inputs([prediction() for _ in range(nuscenes.MAX_FRAME_PREDICTIONS)])
        anchor, receipt = self.normalize(values)
        self.assertEqual(len(anchor['base']['value']), nuscenes.MAX_FRAME_PREDICTIONS)
        self.assertEqual(len(receipt['trace']), nuscenes.MAX_FRAME_PREDICTIONS)
        # The adapter's supported maximum must fit the declared core schema.
        root = Path(__file__).resolve().parents[1]
        case = json.loads((root / 'research/perception-decision/0.1.0/matching-ambiguity.json').read_text())
        case['model'] = {'variables': [], 'clauses': []}
        case['anchors'] = [anchor]
        contract.validate(case)
        values['base']['value'].append(prediction())
        self.rejected(values, 'ADAPTER_AVAILABILITY')

    def test_malformed_frame_contract_rejections(self):
        mutations = [
            ('ADAPTER_SAMPLE', lambda v: v.update(anchor_id='bad/path')),
            ('ADAPTER_SAMPLE', lambda v: v.update(sample_token='')),
            ('ADAPTER_SAMPLE', lambda v: v['base']['value'][0].update(sample_token='other')),
            ('ADAPTER_CLASS', lambda v: v['base']['value'][0].update(detection_name='vehicle.car')),
            ('ADAPTER_COORDINATES', lambda v: v['base']['value'][0].update(translation=[0, 0])),
            ('ADAPTER_COORDINATES', lambda v: v.update(ego_xy=None)),
            ('ADAPTER_AVAILABILITY', lambda v: v.update(base={'state': []})),
            ('ADAPTER_AVAILABILITY', lambda v: v.update(camera={'state': 'missing', 'reason': 'x', 'value': []})),
            ('ADAPTER_AVAILABILITY', lambda v: v.update(camera={'state': 'observed', 'value': None})),
            ('ADAPTER_AVAILABILITY', lambda v: v.update(camera={'state': 'missing', 'reason': ''})),
            ('ADAPTER_SOURCE', lambda v: v['source_sha256'].update(extra='d'*64)),
            ('ADAPTER_SOURCE', lambda v: v['source_sha256'].update(clock=None)),
            ('ADAPTER_WEIGHT', lambda v: v.update(weight=1)),
            ('ADAPTER_WEIGHT', lambda v: v.update(weight=Fraction(1, 10**19))),
            ('ADAPTER_WEIGHT', lambda v: v.update(weight=Fraction(-1))),
        ]
        for code, mutation in mutations:
            with self.subTest(code=code):
                values = inputs([prediction()])
                mutation(values)
                self.rejected(values, code)


if __name__ == '__main__':
    unittest.main()
