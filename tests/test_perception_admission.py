"""Source admission must retain adverse interpretations and unresolved observations."""
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import perception_admission as admission, perception_binding as binding
from tools.perception_decision import checker, contract, kernel
from tools.perception_discovery import records, custody
from tools.perception_observation import package
from tests.test_perception_binding import prepare
from tests.test_perception_observation import read
from tests.test_perception_reference import xy, independent_matching
from tests.test_perception_windows import identity_file


def save(root, name, value):
    return identity_file(root/name, contract.encoded(value))


def prepared_review(root):
    """Constructed review claims only; no human observation or real-data study."""
    observation, req = prepare(root)
    out, private = root/'package', root/'custody.json'
    delivered = package.build(observation, out, private)
    req['observation_custody'] = identity_file(private, private.read_bytes())
    req['package'] = {'path': str(out), 'seal_sha256': delivered['seal_sha256']}
    bind_spec = save(root, 'binding-request.json', req)
    manifest = json.loads((out/'manifest.json').read_bytes())
    discovery_specs, submissions = [], []
    for index in range(2):
        record = records.draft(manifest, delivered['seal_sha256'], str(index+1)*32)
        record['reviewer_id'] = 'synthetic-reviewer-'+str(index)
        record['completed_at'] = {'state': 'reported', 'utc': '2000-01-01T00:00:00Z'}
        record['reported_exposure'] = {k: 'reported_not_exposed' for k in records.EXPOSURES}
        for row in record['capture_reviews']:
            row.update(state='inspected', limitations='')
        for w in manifest['windows']:
            cid = w['channels']['CAM_FRONT']['captures'][0]['capture_id']
            record['proposals'].append({'id': f'proposal-{len(record["proposals"])+1:05d}', 'window_id': w['id'],
                'description': 'Synthetic known object' if index == 0 else 'Synthetic disputed base neighbor',
                'class_hypotheses': {'state': 'proposed', 'values': ['car']},
                'evidence': [{'capture_id': cid, 'locator': {'kind': 'capture'}}]})
        submitted = save(root, f'discovery-{index}.json', record)
        sealed = root/f'discovery-{index}.sealed.json'
        custody.seal_record(submitted['path'], submitted['sha256'], out, delivered['seal_sha256'], sealed)
        discovery_specs.append(identity_file(sealed, sealed.read_bytes()))
        submissions.append(record)
    predecessors = {'binding_request_sha256': bind_spec['sha256'], 'discovery_sha256': [s['sha256'] for s in discovery_specs]}
    assisted = deepcopy(submissions[0])
    assisted.update(artifact_id='reiyah.perception-admission.assisted', phase='proposal_assisted',
                    record_id='3'*32, reviewer_id='synthetic-assisted-reviewer', proposals=[], inputs=predecessors)
    assisted['completed_at'] = {'state': 'reported', 'utc': '2099-01-01T00:00:00Z'}
    assisted['reported_exposure']['predictions'] = 'reported_exposed'
    assisted_spec = save(root, 'assisted.json', assisted)
    ledger = {'artifact_id': 'reiyah.perception-admission.adjudication', 'version': '0.1.0',
              'record_id': '4'*32, 'reviewer_id': 'synthetic-adjudicator',
              'completed_at': {'state': 'reported', 'utc': '2099-01-01T01:00:00Z'},
              'inputs': predecessors | {'assisted_sha256': assisted_spec['sha256']},
              'joint_coverage': {'state': 'assumed_complete', 'statement': 'Exact constructed two-world example; no physical claim.'},
              'worlds': []}
    times = {w['anchor_id']: w['anchor_timestamp_us'] for w in read(observation['window_report'])['windows']}
    for world_index in range(2):
        world = {'id': 'world-'+str(world_index), 'rationale': 'Synthetic presence/absence alternative.', 'windows': []}
        for wi, window in enumerate(manifest['windows']):
            entry = {'window_id': window['id'], 'unlisted_objects': {'state': 'excluded_by_assumption',
                     'statement': 'Constructed finite population, including the base neighbor.'}, 'objects': [], 'unrepresented': []}
            for ri, record in enumerate(submissions):
                member = admission.digest(record)+':'+record['proposals'][wi]['id']
                obj = {'id': 'known' if ri == 0 else 'neighbor', 'members': [member],
                       'rationale': 'Explicit synthetic point interpretation of retained proposal.',
                       'state': 'point', 'class': 'car', 'xy': xy(Fraction(23, 2) if ri == 0 else 9, 20),
                       'timestamp_us': times['one' if wi == 0 else 'two']}
                if ri == 1 and world_index == 0:
                    entry['unrepresented'].append({'member': member, 'state': 'excluded_by_assumption',
                                                  'reason': 'Absent in this declared synthetic world.'})
                else:
                    entry['objects'].append(obj)
            world['windows'].append(entry)
        ledger['worlds'].append(world)
    request = {'artifact_id': 'reiyah.perception-admission.request', 'version': '0.1.0',
               'binding_request': bind_spec, 'discoveries': discovery_specs,
               'assisted': assisted_spec, 'adjudication': save(root, 'adjudication.json', ledger)}
    return request


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.request = prepared_review(self.root)

    def ledger(self):
        return read(self.request['adjudication'])

    def amend(self, ledger):
        self.request['adjudication'] = save(self.root, 'adjudication.json', ledger)

    def reject(self, code, fn=None):
        with self.assertRaises(contract.Invalid) as raised:
            (fn or (lambda: admission.build(self.request)))()
        self.assertEqual(raised.exception.code, code)

    def check(self):
        report = admission.build(self.request)
        packet = kernel.produce(report['compiled_input'])
        # The checker must not call the producer's matcher.
        with patch.object(kernel, '_matching_certificate', side_effect=AssertionError('Producer matcher invoked')):
            checker.check(report['compiled_input'], packet)
        bounds = tuple(contract.rational(packet['result']['bounds'][s]) for s in ('lower', 'upper'))
        return report, packet, bounds

    def update_record(self, role, edit):
        """Rebind an intentionally revised source, including every dependent source identity."""
        old_ledger = self.ledger()
        assisted = read(self.request['assisted'])
        if type(role) is int:
            value = read(self.request['discoveries'][role]); old_hash = value['canonical_record_sha256']
            edit(value['record'])
            record = value['record']; new_hash = admission.digest(record)
            value['canonical_record_sha256'] = new_hash
            m = custody.manifest(read(self.request['binding_request'])['package']['path'], record['package_seal_sha256'])
            value['summary'] = records.validate(record, m, record['package_seal_sha256'], submission=True)
            self.request['discoveries'][role] = save(self.root, f'discovery-{role}.sealed.json', value)
            # Carry the test's exact new proposal namespace through all dispositions.
            old_ledger = json.loads(json.dumps(old_ledger).replace(old_hash+':', new_hash+':'))
            assisted['inputs']['discovery_sha256'] = [s['sha256'] for s in self.request['discoveries']]
        else:
            old_hash = admission.digest(assisted); edit(assisted); new_hash = admission.digest(assisted)
            old_ledger = json.loads(json.dumps(old_ledger).replace(old_hash+':', new_hash+':'))
        self.request['assisted'] = save(self.root, 'assisted.json', assisted)
        old_ledger['inputs'] = assisted['inputs'] | {'assisted_sha256': self.request['assisted']['sha256']}
        self.amend(old_ledger)

    def test_checked_joint_loss_preserves_base_neighbor_counterexample_and_sources(self):
        report, packet, bounds = self.check()
        self.assertEqual(bounds, (-1, 1))
        self.assertEqual(report['compilation']['joint_world_count'], 2)
        self.assertEqual(len(report['proposal_registry']), 4)
        self.assertEqual(report['adjudication'], self.ledger())
        self.assertEqual(report['global_guards'], [])
        self.assertEqual(report['compiled_input']['evidence_kind'], 'synthetic')
        self.assertFalse(report['decision_evaluated'])
        self.assertEqual(report['human_identity_and_independence'], 'not_established')
        self.assertEqual(report['sealing_before_assisted_exposure'], 'not_established')
        self.assertEqual(report['physical_reference_coverage'], 'not_established')
        self.assertEqual(report['compiled_input']['anchors'][0]['base'], read(read(self.request['binding_request'])['comparison'])['anchors'][0]['base'])
        # Independently structured matching on positions, without compiled graph edges.
        direct = []
        for world in self.ledger()['worlds']:
            total = Fraction(0)
            for entry in world['windows']:
                objects = [(o['class'], tuple(contract.rational(v) for v in o['xy'])) for o in entry['objects']]
                base = [('car', (Fraction(10), Fraction(20)))]; added = base+[('car', (Fraction(13), Fraction(20)))]
                total += Fraction(1, 2)*(2*(independent_matching(added, objects)-independent_matching(base, objects))-1)
            direct.append(total)
        self.assertEqual((min(direct), max(direct)), bounds)

    def test_shared_worlds_are_not_replaced_with_independent_window_choices(self):
        ledger = self.ledger()
        ledger['worlds'][0]['windows'][1], ledger['worlds'][1]['windows'][1] = ledger['worlds'][1]['windows'][1], ledger['worlds'][0]['windows'][1]
        self.amend(ledger)
        report, _, bounds = self.check()
        self.assertEqual(bounds, (0, 0))
        self.assertEqual(len(report['compilation']['choice_variables']), 1)

    def test_unknown_joint_and_unlisted_coverage_never_become_closed(self):
        for location in ('joint', 'window'):
            with self.subTest(location=location):
                ledger = self.ledger()
                if location == 'joint': ledger['joint_coverage'] = {'state': 'unknown', 'reason': 'Unresolved world coverage.'}
                else:
                    ledger['joint_coverage'] = {'state': 'assumed_complete', 'statement': 'Synthetic.'}
                    ledger['worlds'][0]['windows'][0]['unlisted_objects'] = {'state': 'unknown', 'reason': 'Unbounded base neighbors.'}
                self.amend(ledger)
                report, _, _ = self.check()
                expected = {'one': 'open', 'two': 'open' if location == 'joint' else 'finite'}
                self.assertEqual(report['compilation']['anchor_reference_states'], expected)

    def test_omitted_foreign_duplicate_and_unqualified_proposals_fail(self):
        original = self.ledger()
        for defect in ('omitted', 'foreign', 'duplicate', 'unqualified'):
            ledger = deepcopy(original); row = ledger['worlds'][0]['windows'][0]
            if defect == 'omitted': row['unrepresented'].clear()
            if defect == 'foreign': row['objects'][0]['members'] = ledger['worlds'][0]['windows'][1]['objects'][0]['members']
            if defect == 'duplicate': row['unrepresented'].append({'member': row['objects'][0]['members'][0], 'state': 'excluded_by_assumption', 'reason': 'Contradiction.'})
            if defect == 'unqualified': row['objects'][0]['members'] = ['proposal-00001']
            self.amend(ledger)
            with self.subTest(defect=defect): self.reject('ADMISSION_ACCOUNTING' if defect == 'omitted' else 'ADMISSION_MEMBERS')

    def test_unresolved_disposition_and_object_keep_window_open(self):
        original = self.ledger()
        for kind in ('disposition', 'object'):
            ledger = deepcopy(original); row = ledger['worlds'][0]['windows'][0]
            if kind == 'disposition': row['unrepresented'][0]['state'] = 'unresolved'
            else:
                obj = row['objects'][0]
                for key in ('class', 'xy', 'timestamp_us'): obj.pop(key)
                obj.update(state='unresolved', reason='Position cannot be inferred from a locator.')
            self.amend(ledger); report, _, _ = self.check()
            self.assertEqual(report['compilation']['anchor_reference_states'], {'one': 'open', 'two': 'finite'})

    def test_discovery_and_assisted_incomplete_inspection_open_only_affected_window(self):
        for role in (0, 'assisted'):
            self.update_record(role, lambda r: r['capture_reviews'][0].update(state='partly_inspected', limitations='Synthetic occlusion.'))
            report, _, _ = self.check()
            self.assertEqual(report['compilation']['anchor_reference_states'], {'one': 'open', 'two': 'finite'})
            self.update_record(role, lambda r: r['capture_reviews'][0].update(state='inspected', limitations=''))

    def test_unknown_or_contested_discovery_blinding_opens_all_windows(self):
        for state in ('unknown', 'reported_exposed'):
            self.update_record(0, lambda r: r['reported_exposure'].update(predictions=state))
            report, _, _ = self.check()
            self.assertEqual(set(report['compilation']['anchor_reference_states'].values()), {'open'})

    def test_missing_times_are_unresolved_and_reversed_order_is_invalid(self):
        self.update_record('assisted', lambda r: r.update(completed_at={'state': 'unrecorded'}))
        report, _, _ = self.check()
        self.assertIn('assisted_completion_time_unrecorded', report['global_guards'])
        self.assertEqual(set(report['compilation']['anchor_reference_states'].values()), {'open'})
        self.update_record('assisted', lambda r: r.update(completed_at={'state': 'reported', 'utc': '2000-01-01T00:00:00Z'}))
        self.reject('ADMISSION_CHRONOLOGY')

    def test_adjudication_before_assistance_and_completion_after_seal_fail(self):
        ledger = self.ledger(); ledger['completed_at']['utc'] = '2098-01-01T00:00:00Z'; self.amend(ledger)
        self.reject('ADMISSION_CHRONOLOGY')
        ledger['completed_at']['utc'] = '2099-01-01T01:00:00Z'; self.amend(ledger)
        self.update_record(0, lambda r: r.update(completed_at={'state': 'reported', 'utc': '2099-01-01T00:00:00Z'}))
        self.reject('ADMISSION_CHRONOLOGY')

    def test_missing_intermediate_time_does_not_hide_contradicted_predecessor_order(self):
        self.update_record('assisted', lambda r: r.update(completed_at={'state': 'unrecorded'}))
        ledger = self.ledger(); ledger['completed_at']['utc'] = '2000-01-01T00:00:00Z'
        self.amend(ledger)
        self.reject('ADMISSION_CHRONOLOGY')

    def test_fabricated_seal_cannot_promote_an_unassigned_draft(self):
        value = read(self.request['discoveries'][0]); value['record']['reviewer_id'] = None
        value['canonical_record_sha256'] = admission.digest(value['record'])
        self.request['discoveries'][0] = save(self.root, 'discovery-0.sealed.json', value)
        self.reject('DISCOVERY_REVIEWER')

    def test_wrong_predecessor_and_wrong_record_phase_fail(self):
        original = self.ledger()
        for role in ('binding_request_sha256', 'assisted_sha256', 'discovery_sha256'):
            ledger = deepcopy(original); ledger['inputs'][role] = ['f'*64]*2 if role == 'discovery_sha256' else 'f'*64
            self.amend(ledger); self.reject('ADMISSION_PREDECESSOR')
        self.amend(original)
        assisted = read(self.request['assisted']); assisted['phase'] = 'unassisted_discovery'
        self.request['assisted'] = save(self.root, 'assisted.json', assisted)
        self.reject('ADMISSION_PHASE')

    def test_digest_only_basis_or_existing_digest_attached_to_point_is_not_accepted(self):
        original = self.ledger()
        for target, key in (('root', 'basis_sha256'), ('world', 'basis_sha256'), ('object', 'record_sha256')):
            ledger = deepcopy(original)
            row = ledger if target == 'root' else ledger['worlds'][0] if target == 'world' else ledger['worlds'][0]['windows'][0]['objects'][0]
            row[key] = self.request['discoveries'][0]['sha256']
            self.amend(ledger); self.reject('ADMISSION_FIELDS')

    def test_changed_point_or_removed_adverse_world_with_old_expected_digest_fails(self):
        original = self.ledger()
        for defect in ('point', 'world'):
            ledger = deepcopy(original)
            if defect == 'point': ledger['worlds'][0]['windows'][0]['objects'][0]['xy'] = xy(100, 20)
            else: ledger['worlds'].pop()
            Path(self.request['adjudication']['path']).write_bytes(contract.encoded(ledger))
            with self.assertRaises(contract.Invalid) as raised: admission.build(self.request)
            self.assertIn(raised.exception.code, ('SOURCE_SIZE', 'SOURCE_DIGEST'))

    def test_repeated_record_id_and_same_handle_do_not_establish_independence(self):
        self.update_record(1, lambda r: r.update(reviewer_id='synthetic-reviewer-0'))
        report, _, _ = self.check()
        self.assertIn('reviewer_handles_not_distinct', report['global_guards'])
        self.update_record(1, lambda r: r.update(record_id='1'*32))
        self.reject('DISCOVERY_PAIR')

    def test_reference_time_unknown_class_and_invalid_geometry_fail_or_remain_open(self):
        original = self.ledger()
        for defect in ('time', 'class', 'fraction'):
            ledger = deepcopy(original); obj = ledger['worlds'][0]['windows'][0]['objects'][0]
            if defect == 'time': obj['timestamp_us'] += 1
            if defect == 'class': obj['class'] = 'unknown'
            if defect == 'fraction': obj['xy'][0]['denominator'] = '0'
            self.amend(ledger)
            if defect == 'time':
                report, _, _ = self.check(); self.assertEqual(report['compilation']['anchor_reference_states']['one'], 'open')
            else: self.reject('REFERENCE_CLASS' if defect == 'class' else 'REFERENCE_NUMBER')

    def test_complete_empty_proposals_do_not_infer_coverage(self):
        for role in (0, 1, 'assisted'):
            self.update_record(role, lambda r: r.update(proposals=[]))
        ledger = self.ledger(); ledger['joint_coverage'] = {'state': 'unknown', 'reason': 'No exhaustive physical review.'}
        for world in ledger['worlds']:
            for row in world['windows']: row.update(objects=[], unrepresented=[])
        self.amend(ledger); report, _, bounds = self.check()
        self.assertEqual(report['proposal_registry'], {})
        self.assertEqual(bounds, (-1, 1))
        self.assertEqual(set(report['compilation']['anchor_reference_states'].values()), {'open'})

    def test_missing_duplicate_or_unknown_world_window_fails(self):
        original = self.ledger()
        for defect in ('missing', 'duplicate', 'unknown'):
            ledger = deepcopy(original); rows = ledger['worlds'][0]['windows']
            if defect == 'missing': rows.pop()
            if defect == 'duplicate': rows[1] = deepcopy(rows[0])
            if defect == 'unknown': rows[0]['window_id'] = 'window-9999'
            self.amend(ledger); self.reject('ADMISSION_POPULATION')

    def test_budget_failure_does_not_discard_an_adverse_world(self):
        with patch.object(admission, 'MAX_DISPOSITIONS', 7): self.reject('ADMISSION_LIMIT')
        self.assertEqual(len(self.ledger()['worlds']), 2)

    def test_tampered_sealed_summary_and_wrong_package_fail(self):
        original = read(self.request['discoveries'][0])
        for defect in ('summary', 'package'):
            value = deepcopy(original)
            if defect == 'summary': value['summary']['proposals'] = 0
            else:
                value['record']['package_seal_sha256'] = 'f'*64
                value['canonical_record_sha256'] = admission.digest(value['record'])
            self.request['discoveries'][0] = save(self.root, 'discovery-0.sealed.json', value)
            self.reject('DISCOVERY_SEAL' if defect == 'summary' else 'DISCOVERY_BINDING')

    def test_source_changes_during_compilation_are_rejected(self):
        compile_model = admission.reference.compile_model
        def changed(*args):
            value = compile_model(*args)
            path = Path(self.request['adjudication']['path']); path.write_bytes(path.read_bytes()+b' ')
            return value
        with patch.object(admission.reference, 'compile_model', side_effect=changed): self.reject('SOURCE_SIZE')

    def test_package_changes_after_binding_are_rejected(self):
        original = admission.binding.build
        def changed(req):
            value = original(req)
            path = Path(req['package']['path'])/'manifest.json'; path.write_bytes(path.read_bytes()+b' ')
            return value
        with patch.object(admission.binding, 'build', side_effect=changed):
            with self.assertRaises(contract.Invalid): admission.build(self.request)

    def test_fresh_output_and_cli_failures_preserve_private_boundary(self):
        req = save(self.root, 'request.json', self.request); out = self.root/'report.json'
        result = admission.run(req['path'], req['sha256'], out)
        before = out.read_bytes(); self.assertEqual(result['report_sha256'], hashlib.sha256(before).hexdigest())
        self.reject('OUTPUT_EXISTS', lambda: admission.run(req['path'], req['sha256'], out))
        self.assertEqual(out.read_bytes(), before)
        inside = Path(read(self.request['binding_request'])['package']['path'])/'review.json'
        self.reject('ADMISSION_PRIVATE_OUTPUT', lambda: admission.run(req['path'], req['sha256'], inside))
        bad = self.root/'bad-output.json'
        run = subprocess.run([sys.executable, '-B', '-m', 'tools.perception_admission', '--request', req['path'],
                              '--request-sha256', 'f'*64, '--output', str(bad)], capture_output=True)
        self.assertEqual(run.returncode, 2); self.assertFalse(bad.exists())
        self.assertEqual(json.loads(run.stderr)['status'], 'invalid')

    def test_source_code_change_is_rejected(self):
        current = admission.code_identities()
        with patch.object(admission, 'code_identities', side_effect=[current, current+[['changed', 'f'*64]]]):
            self.reject('ADMISSION_CODE_CHANGED')


if __name__ == '__main__':
    unittest.main()
