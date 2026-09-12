"""Source-bound synthetic admission, semantic loss and adversarial packet checks."""
from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import perception_admission as admission, perception_assistance as assistance
from tools import perception_operands as operands, perception_reviewed_operands as reviewed
from tools.perception_decision import checker, contract, kernel, nuscenes
from tests.test_perception_admission import prepared_review, save
from tests.test_perception_assistance import fixture
from tests.test_perception_observation import read, tree
from tests.test_perception_reference import independent_matching


def prepared_inputs(root, edit_ledger=None):
    """Actual synthetic source/package/review bytes, never human observations."""
    source_root = root/'sources'; source_root.mkdir()
    request, _, _ = fixture(source_root)
    review_root = root/'reviews'; review_root.mkdir()
    observation = read(request['observation_custody'])['request']
    with patch('tests.test_perception_admission.prepare', return_value=(observation, deepcopy(request))):
        review_request = prepared_review(review_root)
    if edit_ledger:
        ledger = read(review_request['adjudication'])
        edit_ledger(ledger)
        review_request['adjudication'] = save(review_root, 'adjudication.json', ledger)
    request_spec = save(root, 'admission-request.json', review_request)
    bind_spec = review_request['binding_request']
    report = root/'admission.json'
    admitted = admission.run(Path(request_spec['path']), request_spec['sha256'], report)
    assistance_path = root/'assistance'
    assisted = assistance.run(Path(bind_spec['path']), bind_spec['sha256'], 'configuration-2', assistance_path)
    return {'binding_request': Path(bind_spec['path']), 'binding_request_sha256': bind_spec['sha256'],
        'admission_request': Path(request_spec['path']), 'admission_request_sha256': request_spec['sha256'],
        'admission_report': report, 'admission_report_sha256': admitted['report_sha256'],
        'assistance': assistance_path, 'preparation_sha256': assisted['preparation_sha256']}


def direct_world_losses(report):
    """Independent exhaustive geometric matching; no Engine edges, model or matcher."""
    req = read(report['inputs']['binding_request'])
    case, normals = read(req['comparison']), read(req['normalizations'])
    anchor_by_window = {w['window_id']: w['anchor_id'] for w in report['binding']['windows']}
    a, b = (contract.rational(case['loss'][k]) for k in ('false_negative', 'false_positive'))
    results = []
    for world in report['adjudication']['worlds']:
        total = Fraction(0)
        for entry in world['windows']:
            anchor_id = anchor_by_window[entry['window_id']]
            anchor = next(x for x in case['anchors'] if x['id'] == anchor_id)
            normal = next(x for x in normals if x['anchor_id'] == anchor_id)
            rows = {r['detection']['id']: r['record'] for r in normal['qualified_records']}
            def positions(nodes):
                return [(rows[n['id']]['class'], tuple(contract.rational(v) for v in rows[n['id']]['xy'])) for n in nodes]
            base = positions(anchor['base']['value']); added = positions(anchor['additions']['value'])
            objects = [(o['class'], tuple(contract.rational(v) for v in o['xy'])) for o in entry['objects']]
            gain = independent_matching(base+added, objects)-independent_matching(base, objects)
            total += contract.rational(anchor['weight'])*((a+b)*gain-b*len(added))
        results.append(total)
    return results


class ReviewedOperandsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.inputs = prepared_inputs(self.root)

    def reject(self, code, fn):
        with self.assertRaises(contract.Invalid) as caught:
            fn()
        self.assertEqual(caught.exception.code, code)

    def source(self):
        return contract.parse(self.inputs['admission_report'].read_bytes())

    def projection(self):
        files, _ = reviewed.materialize(**self.inputs)
        neutral = contract.parse(files['common/comparison.json'])
        maps = contract.parse(files['common/renamings.json'])['anchors']
        original = self.source()['compiled_input']
        # This neutral open counterpart is used only to check row correspondence.
        open_case = deepcopy(neutral)
        open_case['model'] = {'variables': [], 'clauses': []}
        for a in open_case['anchors']: a['reference'] = {'state': 'open', 'reason': 'Synthetic check counterpart'}
        return original, neutral, open_case, maps

    def test_full_private_basis_repeat_bytes_and_geometric_comparator(self):
        first, second = self.root/'first', self.root/'second'
        result = reviewed.run(first, **self.inputs)
        self.assertEqual(result, reviewed.run(second, **self.inputs))
        self.assertEqual(tree(first), tree(second))
        checked = reviewed.check(first, result['preparation_sha256'], **self.inputs)
        self.assertEqual(checked['status'], 'checked_against_selected_sources')
        self.assertEqual((first/'common/admission.json').read_bytes(), self.inputs['admission_report'].read_bytes())
        case = contract.parse((first/'common/comparison.json').read_bytes())
        packet = kernel.produce(case)
        with patch.object(kernel, '_matching_certificate', side_effect=AssertionError('Producer used by checker')):
            checker.check(case, packet)
        direct = direct_world_losses(self.source())
        self.assertEqual(direct, [-1, 1])
        self.assertEqual(tuple(contract.rational(packet['result']['bounds'][s]) for s in ('lower', 'upper')),
                         (min(direct), max(direct)))
        self.assertEqual(case['model'], self.source()['compiled_input']['model'])
        self.assertFalse(result['assisted_evidence_released'])
        self.assertEqual(case['evidence_kind'], 'synthetic')

    def test_rules_describe_the_reviewed_stage_and_preserve_loss_conventions(self):
        files, _ = reviewed.materialize(**self.inputs)
        rules = contract.parse(files['common/rules.json'])
        common = contract.parse(files['common/operands.json'])
        self.assertEqual(rules['reference_stage'], common['reference_stage'])
        previous = contract.parse((operands.GUIDES/'rules.json').read_bytes())
        for key in ('loss', 'decision_rules', 'later_reference_rule', 'candidate_suppression'):
            self.assertEqual(rules[key], previous[key])
        self.assertEqual(common['rules_sha256'], reviewed.digest(files['common/rules.json']))

    def test_cross_anchor_coupling_and_unused_world_encoding(self):
        other = self.root/'coupled'; other.mkdir()
        def change(ledger):
            x, y = ledger['worlds']
            x['windows'][1], y['windows'][1] = y['windows'][1], x['windows'][1]
            third = deepcopy(x); third['id'] = 'third-explicit-world'
            third['rationale'] = 'Same graph, distinct retained interpretation basis.'
            ledger['worlds'].append(third)
        inputs = prepared_inputs(other, change)
        files, _ = reviewed.materialize(**inputs)
        case = contract.parse(files['common/comparison.json'])
        report = contract.parse(files['common/admission.json'])
        self.assertEqual(direct_world_losses(report), [0, 0, 0])
        self.assertEqual(len(case['model']['variables']), 2)
        self.assertEqual(len(case['model']['clauses']), 1)
        packet = kernel.produce(case); checker.check(case, packet)
        self.assertEqual([contract.rational(packet['result']['bounds'][s]) for s in ('lower', 'upper')], [0, 0])
        self.assertEqual(len(report['adjudication']['worlds']), 3)

    def test_stripping_finite_reference_is_rejected_even_with_equal_coarse_interval(self):
        original, neutral, open_case, maps = self.projection()
        stripped = deepcopy(neutral)
        for a in stripped['anchors']: a['reference'] = {'state': 'open', 'reason': 'Illicit loss of review'}
        self.assertEqual(kernel.produce(stripped)['result']['bounds'], kernel.produce(neutral)['result']['bounds'])
        self.reject('REVIEWED_SEMANTICS', lambda: reviewed.check_projection(original, stripped, open_case, maps))

    def test_world_model_edges_weights_tolerance_and_reason_loss_are_rejected(self):
        original, neutral, open_case, maps = self.projection()
        def weights(c):
            c['anchors'][0]['weight'] = contract.wire(Fraction(1, 3))
            c['anchors'][1]['weight'] = contract.wire(Fraction(2, 3))
        edits = [lambda c: c['model']['clauses'].append([{'variable': c['model']['variables'][0], 'value': False}]),
            lambda c: c['anchors'][0]['reference']['edges'].pop(),
            lambda c: c['anchors'][0]['reference']['objects'][0].update(when=[]),
            weights, lambda c: c['loss'].update(tolerance=contract.wire(Fraction(1, 5))),
            lambda c: c['assumptions'].pop()]
        for index, edit in enumerate(edits):
            case = deepcopy(neutral); edit(case)
            with self.subTest(index=index):
                self.reject('REVIEWED_SEMANTICS', lambda: reviewed.check_projection(original, case, open_case, maps))

    def test_wrong_selected_admission_request_and_valid_report_are_rejected(self):
        raw = self.inputs['admission_request'].read_bytes()
        request = contract.parse(raw)
        ledger = read(request['adjudication']); ledger['worlds'].pop()
        request['adjudication'] = save(self.root, 'other-adjudication.json', ledger)
        other_spec = save(self.root, 'other-request.json', request)
        other_report = self.root/'other-report.json'
        result = admission.run(Path(other_spec['path']), other_spec['sha256'], other_report)
        inputs = self.inputs | {'admission_report': other_report, 'admission_report_sha256': result['report_sha256']}
        self.reject('REVIEWED_ADMISSION', lambda: reviewed.materialize(**inputs))
        changed = self.inputs | {'admission_request': Path(other_spec['path'])}
        self.reject('OPERANDS_DIGEST', lambda: reviewed.materialize(**changed))

    def test_other_binding_cannot_be_selected_by_admission(self):
        request = contract.parse(self.inputs['admission_request'].read_bytes())
        binding_copy = save(self.root, 'other-binding.json', read(request['binding_request']))
        request['binding_request'] = binding_copy
        other = save(self.root, 'other-admission-request.json', request)
        inputs = self.inputs | {'admission_request': Path(other['path']), 'admission_request_sha256': other['sha256']}
        self.reject('REVIEWED_BINDING', lambda: reviewed.materialize(**inputs))

    def test_rehashed_admission_source_forgery_is_rejected(self):
        for name, edit in [('time', lambda r: r['binding']['windows'][0].update(anchor_timestamp_us=9)),
                           ('proposal', lambda r: r['proposal_registry'].clear()),
                           ('world', lambda r: r['adjudication']['worlds'].pop()),
                           ('source', lambda r: r['inputs']['discoveries'][0].update(sha256='a'*64))]:
            report = self.source(); edit(report)
            other = save(self.root, 'forged-'+name+'.json', report)
            inputs = self.inputs | {'admission_report': Path(other['path']), 'admission_report_sha256': other['sha256']}
            with self.subTest(name=name): self.reject('REVIEWED_ADMISSION', lambda: reviewed.materialize(**inputs))

    def test_unknown_coverage_retains_dispositions_and_stays_open(self):
        other = self.root/'unknown'; other.mkdir()
        inputs = prepared_inputs(other, lambda r: r.update(joint_coverage={'state': 'unknown', 'reason': 'Synthetic incomplete coverage'}))
        files, record = reviewed.materialize(**inputs)
        report = contract.parse(files['common/admission.json'])
        self.assertEqual(set(record['summary']['reference_states'].values()), {'open'})
        self.assertEqual(len(report['world_accounting']), 4)
        self.assertEqual(len(report['proposal_registry']), 4)
        self.assertEqual(report['reference']['joint_coverage']['state'], 'unknown')

    def test_wrong_time_is_open_and_explicit_exclusion_can_be_finite_empty(self):
        for kind in ('time', 'empty'):
            other = self.root/kind; other.mkdir()
            def change(ledger):
                for world in ledger['worlds']:
                    for window in world['windows']:
                        if kind == 'time':
                            window['objects'][0]['timestamp_us'] += 1
                        else:
                            for obj in window['objects']:
                                window['unrepresented'] += [{'member': m, 'state': 'excluded_by_assumption',
                                    'reason': 'Explicit synthetic exclusion, not an unobserved empty source.'} for m in obj['members']]
                            window['objects'].clear()
            files, receipt = reviewed.materialize(**prepared_inputs(other, change))
            case = contract.parse(files['common/comparison.json'])
            if kind == 'time':
                self.assertEqual(set(receipt['summary']['reference_states'].values()), {'open'})
                self.assertIn('object_time_differs', case['anchors'][0]['reference']['reason'])
            else:
                self.assertEqual(set(receipt['summary']['reference_states'].values()), {'finite'})
                self.assertFalse(case['anchors'][0]['reference']['objects'])
                packet = kernel.produce(case); checker.check(case, packet)
                self.assertEqual([contract.rational(packet['result']['bounds'][s]) for s in ('lower', 'upper')], [-1, -1])

    def test_unavailable_and_equal_valued_rows_keep_distinct_identities(self):
        def row(x): return {'sample_token': 's', 'detection_name': 'car', 'translation': [x, 20, 0], 'detection_score': 1}
        for available in (True, False):
            base = {'state': 'observed', 'value': [row(10), row(10)]} if available else {'state': 'missing', 'reason': 'Synthetic missing output'}
            anchor, normal = nuscenes.normalize_frame(sample_token='s', anchor_id='one', ego_xy=[10, 20], weight=Fraction(1),
                base=base, camera={'state': 'observed', 'value': []},
                source_sha256={'base': 'a'*64 if available else None, 'camera': 'b'*64, 'clock': 'c'*64})
            case = read(read(self.source()['inputs']['binding_request'])['comparison']); case['anchors'] = [anchor]
            neutral, _, maps = operands.project(case, [normal], [{'anchor_id': 'one', 'sample_token': 's', 'window_id': 'window-0001'}],
                {'s': {'frame_id': 'frame-0001'}}, {'base': 'configuration-2', 'camera': 'configuration-1'})
            compiled = deepcopy(case)
            if available: compiled['anchors'][0]['reference'] = {'state': 'finite', 'objects': [], 'edges': []}
            projected = reviewed.project(compiled, neutral, maps)
            if available:
                self.assertEqual(len({n['id'] for n in projected['anchors'][0]['base']['value']}), 2)
                self.assertEqual(projected['anchors'][0]['reference']['state'], 'finite')
            else:
                self.assertEqual(projected['anchors'][0]['base'], base)
                forged = deepcopy(projected); forged['anchors'][0]['base'] = {'state': 'observed', 'value': []}
                self.reject('REVIEWED_MAPPING', lambda: reviewed.check_projection(compiled, forged, neutral, maps))

    def test_modified_packet_and_rehashed_receipt_are_rejected(self):
        output = self.root/'packet'; result = reviewed.run(output, **self.inputs)
        path = output/'common/admission.json'; original = path.read_bytes()
        report = contract.parse(original); report['world_accounting'].pop()
        path.write_bytes(contract.encoded(report))
        self.reject('OPERANDS_SIZE', lambda: reviewed.check(output, result['preparation_sha256'], **self.inputs))
        receipt = contract.parse((output/'PREPARATION.json').read_bytes())
        for f in receipt['files']:
            if f['path'] == 'common/admission.json': f.update(byte_size=path.stat().st_size, sha256=reviewed.digest(path.read_bytes()))
        data = contract.encoded(receipt); (output/'PREPARATION.json').write_bytes(data)
        self.reject('REVIEWED_PACKET', lambda: reviewed.check(output, reviewed.digest(data), **self.inputs))

    def test_existing_overlapping_and_symlink_outputs_are_refused(self):
        out = self.root/'packet'; result = reviewed.run(out, **self.inputs)
        self.reject('OUTPUT_EXISTS', lambda: reviewed.run(out, **self.inputs))
        self.reject('REVIEWED_OUTPUT', lambda: reviewed.run(self.inputs['assistance']/'nested', **self.inputs))
        symlink = self.root/'alias'; symlink.symlink_to(out, target_is_directory=True)
        self.reject('REVIEWED_PACKET', lambda: reviewed.check(symlink, result['preparation_sha256'], **self.inputs))

    def test_byte_budget_does_not_clip_and_failed_run_has_no_output(self):
        out = self.root/'oversized'
        with patch.object(reviewed, 'MAX_BYTES', 1):
            self.reject('REVIEWED_SIZE', lambda: reviewed.run(out, **self.inputs))
        self.assertFalse(out.exists())

    def test_cli_rejects_malformed_source_without_a_report(self):
        inputs = dict(self.inputs)
        spec = save(self.root, 'malformed.json', {'artifact_id': 'wrong'})
        inputs.update(admission_request=Path(spec['path']), admission_request_sha256=spec['sha256'])
        argv = [sys.executable, '-B', '-m', 'tools.perception_reviewed_operands', 'prepare']
        for key, value in inputs.items(): argv += ['--'+key.replace('_', '-'), str(value)]
        out = self.root/'cli-output'; argv += ['--output', str(out)]
        result = subprocess.run(argv, cwd=reviewed.ROOT, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stderr)['code'], 'ADMISSION_FIELDS')
        self.assertFalse(out.exists())


if __name__ == '__main__':
    unittest.main()
