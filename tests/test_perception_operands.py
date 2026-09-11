"""Equal evidence, exact duplicate identities, source forgeries and stage refusal."""
from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools import perception_assistance as assistance, perception_binding as binding, perception_operands as operands
from tools.perception_decision import checker, contract as decision, kernel, nuscenes
from tests.test_perception_assistance import fixture
from tests.test_perception_observation import read, replace, tree
from tests.test_perception_windows import identity_file


class OperandsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.request, _, self.catalog = fixture(self.root)
        self.spec = identity_file(self.root/'request.json', decision.encoded(self.request))
        self.assistance = self.root/'assistance'
        result = assistance.run(Path(self.spec['path']), self.spec['sha256'], 'configuration-2', self.assistance)
        self.digest = result['preparation_sha256']
        self.files, self.receipt = operands.load_assistance(self.assistance, self.digest, self.spec['sha256'])

    def reject(self, fn, code):
        with self.assertRaises(decision.Invalid) as caught:
            fn()
        self.assertEqual(caught.exception.code, code)

    def prepare(self, output):
        return operands.run(Path(self.spec['path']), self.spec['sha256'], self.assistance, self.digest, output)

    def changed(self, name, change):
        files = dict(self.files)
        value = decision.parse(files[name]); change(value)
        files[name] = decision.encoded(value)
        return files

    def test_equal_complete_preparation_and_existing_checker(self):
        a, b = self.root/'a', self.root/'b'
        first, second = self.prepare(a), self.prepare(b)
        self.assertEqual(first, second); self.assertEqual(tree(a), tree(b))
        self.assertEqual(first['summary'], {'comparison_anchors': 2, 'context_keyframes': 10,
            'mapped_rows': 12, 'qualified_records': 4,
            'retained': {'base': {'state': 'observed', 'value': 2}, 'additions': {'state': 'observed', 'value': 2}}})
        self.assertFalse(first['assisted_evidence_released']); self.assertFalse(first['decision_evaluated'])
        common = decision.parse((a/'common/operands.json').read_bytes())
        neutral_bytes = (a/'common/comparison.json').read_bytes()
        self.assertEqual(common['comparison_sha256'], hashlib.sha256(neutral_bytes).hexdigest())
        neutral = decision.validate(decision.parse(neutral_bytes))
        original = read(self.request['comparison'])
        expected, result = kernel.produce(original), kernel.produce(neutral)
        checker.check(original, expected); checker.check(neutral, result)
        self.assertEqual(expected['result'], result['result'])
        self.assertEqual((a/'common/assistance.json').read_bytes(), self.files['common/assistance.json'])
        for anchor in common['anchors']:
            self.assertEqual(len(anchor['trace']), 6)
            self.assertEqual(sum(t['retention'] == 'ineligible' for t in anchor['trace']), 4)
            for row in anchor['qualified_records']:
                self.assertEqual(row['detection']['record_sha256'], hashlib.sha256(decision.encoded(row['record'])).hexdigest())
        for token in (str(self.root), 'sample_token', 'source_sha256', 'base:', 'camera:', 'f0-2'):
            self.assertNotIn(token.encode(), neutral_bytes + (a/'common/operands.json').read_bytes())
        self.reject(lambda: self.prepare(a), 'OUTPUT_EXISTS')

    def test_individually_valid_other_request_cannot_supply_assistance(self):
        changed = deepcopy(self.request)
        case = read(changed['comparison']); case['loss']['tolerance'] = decision.wire(Fraction(1, 5))
        replace(changed, 'comparison', case)
        other = identity_file(self.root/'other-request.json', decision.encoded(changed))
        self.reject(lambda: operands.run(Path(other['path']), other['sha256'], self.assistance, self.digest, self.root/'out'),
                    'OPERANDS_ASSISTANCE')

    def test_reordered_equal_population_rows_cannot_change_identity(self):
        def reorder(common):
            frame = next(f for f in common['frames'] if len(f['predictions']['configuration-1'].get('value', [])) == 3)
            rows = frame['predictions']['configuration-1']['value']; rows[0], rows[1] = rows[1], rows[0]
        files = self.changed('common/assistance.json', reorder)
        self.reject(lambda: operands.materialize(self.request, files, self.receipt), 'OPERANDS_ROWS')

    def test_role_swap_and_wrong_comparison_frame_are_rejected(self):
        files = self.changed('operator/source-custody.json', lambda s: s.update(
            configuration_roles={'base': 'configuration-1', 'camera': 'configuration-2'}))
        self.reject(lambda: operands.materialize(self.request, files, self.receipt), 'OPERANDS_ROWS')
        files = self.changed('common/assistance.json', lambda s: s['windows'][0].update(comparison_frame_id='frame-0001'))
        self.reject(lambda: operands.materialize(self.request, files, self.receipt), 'OPERANDS_POPULATION')

    def test_duplicate_frames_and_boolean_clocks_are_rejected(self):
        files = self.changed('operator/source-custody.json', lambda s: s['frames'].__setitem__(1, deepcopy(s['frames'][0])))
        self.reject(lambda: operands.materialize(self.request, files, self.receipt), 'OPERANDS_POPULATION')

    def test_context_state_count_and_sample_are_bound(self):
        for mutation, code in (('state', 'OPERANDS_SOURCE'), ('count', 'OPERANDS_SOURCE'), ('sample', 'PREDICTION_SAMPLE')):
            with self.subTest(mutation=mutation):
                common = decision.parse(self.files['common/assistance.json'])
                source = decision.parse(self.files['operator/source-custody.json'])
                index = -1 if mutation == 'state' else 1
                public, private = common['frames'][index], source['frames'][index]
                stored = private['predictions']['base']
                if mutation == 'state': stored['full_rows'] = {'state': 'observed', 'value': []}
                elif mutation == 'count': stored['full_rows']['value'].pop()
                else: stored['full_rows']['value'][0]['sample_token'] = 'another-sample'
                public['predictions']['configuration-2'] = assistance.sources.prediction_rows(
                    operands.restore_source(stored['full_rows']), public['id']+'-configuration-2')
                files = self.files | {'common/assistance.json': decision.encoded(common),
                                     'operator/source-custody.json': decision.encoded(source)}
                self.reject(lambda: operands.materialize(self.request, files, self.receipt), code)
        files = self.changed('operator/source-custody.json', lambda s: s['frames'][0].update(timestamp_us=True))
        self.reject(lambda: operands.materialize(self.request, files, self.receipt), 'OPERANDS_POPULATION')

    def test_forged_trace_that_passes_binding_fails_normalization_replay(self):
        normal = read(self.request['normalizations']); normal[0]['trace'][0]['retention'] = 'ineligible'
        replace(self.request, 'normalizations', normal)
        files = dict(self.files); files['operator/normalizations.json'] = decision.encoded(normal)
        bound = binding.build(self.request)
        files['operator/binding-report.json'] = decision.encoded(bound)
        receipt = deepcopy(self.receipt); receipt['binding_inputs'] = bound['inputs']
        self.reject(lambda: operands.materialize(self.request, files, receipt), 'ASSISTANCE_NORMALIZATION')

    def test_reviewed_reference_and_joint_constraints_cannot_be_reopened(self):
        for mutation in ('finite', 'variable', 'clause'):
            def change(case):
                if mutation == 'finite': case['anchors'][0]['reference'] = {'state': 'finite', 'objects': [], 'edges': []}
                elif mutation == 'variable': case['model']['variables'] = ['joint']
                else: case['model']['clauses'] = [[]]
            files = self.changed('operator/comparison.json', change)
            self.reject(lambda: operands.materialize(self.request, files, self.receipt), 'OPERANDS_REFERENCE_STAGE')

    def test_assistance_wrong_hash_extra_entries_limits_and_symlink(self):
        self.reject(lambda: operands.load_assistance(self.assistance, '0'*64, self.spec['sha256']), 'OPERANDS_DIGEST')
        path = self.assistance/'PREPARATION.json'
        original = path.read_bytes()
        for change, code in ((lambda r: r['files'].__setitem__(1, deepcopy(r['files'][0])), 'OPERANDS_ASSISTANCE'),
                             (lambda r: r['files'][0].update(byte_size=operands.MAX_BYTES+1), 'OPERANDS_SIZE'),
                             (lambda r: r['files'][0].update(byte_size=True), 'OPERANDS_SIZE')):
            receipt = decision.parse(original); change(receipt); data = decision.encoded(receipt); path.write_bytes(data)
            self.reject(lambda: operands.load_assistance(self.assistance, hashlib.sha256(data).hexdigest(), self.spec['sha256']), code)
        path.write_bytes(original)
        (self.assistance/'common/extra').write_text('unexpected')
        self.reject(lambda: operands.load_assistance(self.assistance, self.digest, self.spec['sha256']), 'OPERANDS_ASSISTANCE')
        (self.assistance/'common/extra').unlink()
        target = self.assistance/'common/READER.md'; backup = self.root/'reader'; target.rename(backup); target.symlink_to(backup)
        with self.assertRaises(OSError): operands.load_assistance(self.assistance, self.digest, self.spec['sha256'])

    def test_changed_assistance_bytes_and_input_overlapping_output_fail(self):
        path = self.assistance/'common/assistance.json'; raw = path.read_bytes(); path.write_bytes(b'X'+raw[1:])
        self.reject(lambda: self.prepare(self.root/'out'), 'OPERANDS_DIGEST')
        self.assertFalse((self.root/'out').exists())
        self.reject(lambda: self.prepare(self.assistance/'nested-output'), 'OPERANDS_OUTPUT')

    def test_duplicate_rows_and_boundary_suppression_remain_distinct(self):
        case = read(self.request['comparison'])
        sample = 'synthetic-sample'
        def row(x, score):
            return {'sample_token': sample, 'detection_name': 'car', 'translation': [x, 20, 0], 'detection_score': score}
        base = {'state': 'observed', 'value': [row(10, 1), row(10, 1)]}
        camera = {'state': 'observed', 'value': [row(Decimal('11.99'), 1), row(12, Decimal('.30')),
            row(12, Decimal('.30')), row(60, Decimal('.30')), row(Decimal('60.01'), 1)]}
        anchor, normal = nuscenes.normalize_frame(sample_token=sample, anchor_id='synthetic', ego_xy=[10, 20],
            weight=Fraction(1), base=base, camera=camera, source_sha256={r: 'a'*64 for r in ('base', 'camera', 'clock')})
        case['anchors'] = [anchor]
        neutral, views, maps = operands.project(case, [normal], [{'anchor_id': 'synthetic', 'sample_token': sample,
            'window_id': 'window-0001'}], {sample: {'frame_id': 'frame-0001'}}, {'base': 'configuration-2', 'camera': 'configuration-1'})
        self.assertEqual(len(neutral['anchors'][0]['base']['value']), 2)
        self.assertEqual(len(neutral['anchors'][0]['additions']['value']), 2)
        base_ids = [n['id'] for n in neutral['anchors'][0]['base']['value']]
        self.assertEqual(len(set(base_ids)), 2)
        trace = views[0]['trace']
        self.assertEqual(trace[2]['blocked_by'], base_ids[0])
        self.assertEqual(trace[4]['blocked_by'], trace[3]['row_id'])
        self.assertEqual(trace[5]['retention'], 'addition_retained')
        self.assertFalse(trace[6]['range_eligible'])
        self.assertEqual(len(maps[0]['detections']), 6)

    def test_unavailable_states_and_substantive_text_are_preserved(self):
        case = read(self.request['comparison']); sample = 'synthetic'
        base = {'state': 'abstained', 'reason': 'Substantive source reason retained for both analysts'}
        camera = {'state': 'observed', 'value': []}
        anchor, normal = nuscenes.normalize_frame(sample_token=sample, anchor_id=sample, ego_xy=[10, 20], weight=Fraction(1),
            base=base, camera=camera, source_sha256={'base': None, 'camera': 'b'*64, 'clock': 'c'*64})
        case['anchors'] = [anchor]; case['assumptions'] = ['Declared condition remains visible even if identifying']
        neutral, views, _ = operands.project(case, [normal], [{'anchor_id': sample, 'sample_token': sample,
            'window_id': 'window-0001'}], {sample: {'frame_id': 'frame-0001'}}, {'base': 'configuration-2', 'camera': 'configuration-1'})
        self.assertEqual(neutral['anchors'][0]['base'], base)
        self.assertEqual(neutral['anchors'][0]['additions']['state'], 'unknown')
        self.assertEqual(neutral['assumptions'], case['assumptions'])
        self.assertIsNone(views[0]['input_counts']['configuration-2'])
        self.assertEqual(views[0]['input_counts']['configuration-1'], 0)
        result = kernel.produce(neutral); checker.check(neutral, result)
        self.assertEqual(result['result']['execution_status'], 'input_blocked')
        self.assertEqual(operands.retained_summary(neutral, 'base'),
                         {'state': 'unavailable', 'observed_partial_count': 0, 'unavailable_anchors': 1})


if __name__ == '__main__':
    unittest.main()
