"""Human preparation must not invent review or cross the discovery boundary."""
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import perception_rehearsal as rehearsal
from tools.perception_decision import contract as decision
from tools.perception_discovery import records
from tools.perception_observation import package
from tests.test_perception_binding import prepare
from tests.test_perception_observation import read, replace, tree
from tests.test_perception_windows import identity_file


class RehearsalTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.observation, self.request = prepare(self.root)
        self.counter = 0
        self.make_package()
        self.identity = '1234567890abcdef' * 2

    def make_package(self):
        self.counter += 1
        self.package_path = self.root / f'package-{self.counter}'
        custody = self.root / f'custody-{self.counter}.json'
        result = package.build(self.observation, self.package_path, custody)
        self.request['observation_custody'] = identity_file(custody, custody.read_bytes())
        self.request['package'] = {'path': str(self.package_path), 'seal_sha256': result['seal_sha256']}

    def selected(self):
        return identity_file(self.root / 'request.json', decision.encoded(self.request))

    def run_kit(self, out=None):
        request = self.selected()
        return rehearsal.run(request['path'], request['sha256'], self.identity, out or self.root / 'kit')

    def rejected(self, code, fn):
        with self.assertRaises(decision.Invalid) as caught:
            fn()
        self.assertEqual(caught.exception.code, code)

    def test_equal_discovery_material_and_empty_states_with_exact_occurrence_accounting(self):
        before = tree(self.package_path)
        files, context = rehearsal.materialize(self.request, self.identity)
        manifest = json.loads((self.package_path / 'manifest.json').read_bytes())
        drafts = []
        for role in ('discovery-1', 'discovery-2'):
            draft = json.loads(files[f'{role}/discovery-record.draft.json'])
            summary = records.validate(draft, manifest, self.request['package']['seal_sha256'])
            self.assertEqual(summary['inspection_states'], {'not_inspected': 70})
            self.assertEqual(draft['reviewer_id'], None)
            self.assertEqual(draft['completed_at'], {'state': 'unrecorded'})
            self.assertEqual(set(draft['reported_exposure'].values()), {'unknown'})
            self.assertEqual(draft['proposals'], [])
            rows = list(csv.DictReader(io.StringIO(files[f'{role}/capture-index.csv'].decode())))
            self.assertEqual([(r['window_id'], r['capture_id']) for r in rows], records.population(manifest))
            self.assertEqual(len(rows), 70)
            self.assertTrue(all(r['evidence_state'] == 'delivered' for r in rows))
            drafts.append(draft)
        self.assertNotEqual(drafts[0]['record_id'], drafts[1]['record_id'])
        for name in ('START_HERE.md', 'capture-index.csv', 'package-identity.json'):
            self.assertEqual(files[f'discovery-1/{name}'], files[f'discovery-2/{name}'])
        self.assertEqual(files['analysis/conventional-conclusion.draft.json'],
                         files['analysis/engine-conclusion.draft.json'])
        outcome = json.loads(files['analysis/conventional-conclusion.draft.json'])
        self.assertIsNone(outcome['lower']); self.assertIsNone(outcome['upper'])
        self.assertEqual(outcome['status'], 'not_evaluated')
        self.assertEqual(list(csv.DictReader(io.StringIO(files['operator/effort.csv'].decode()))), [])
        self.assertEqual(tree(self.package_path), before)
        self.assertEqual(files, rehearsal.materialize(self.request, self.identity)[0])

    def test_comparison_only_prose_cannot_enter_discovery_folders(self):
        first, _ = rehearsal.materialize(self.request, self.identity)
        case = read(self.request['comparison']); case['comparison_id'] = 'PRIVATE-DETECTOR-IDENTITY'
        case['assumptions'].append('PRIVATE-CANDIDATE-RANKING')
        replace(self.request, 'comparison', case)
        second, _ = rehearsal.materialize(self.request, self.identity)
        for name in first:
            if name.startswith('discovery-'):
                self.assertEqual(first[name], second[name], name)
                self.assertNotIn(b'PRIVATE-', second[name])
                self.assertNotIn(str(self.root).encode(), second[name])
        self.assertNotEqual(first['operator/binding-report.json'], second['operator/binding-report.json'])

    def test_missing_asset_keeps_navigation_row_and_uninspected_draft(self):
        inv = read(self.observation['inventory'])
        (self.root / 'raw' / inv['assets'][0]['filename']).unlink()
        self.make_package()
        files, context = rehearsal.materialize(self.request, self.identity)
        rows = list(csv.DictReader(io.StringIO(files['discovery-1/capture-index.csv'].decode())))
        missing = [r for r in rows if r['evidence_state'] == 'missing']
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]['asset_relative_path'], '')
        self.assertEqual(len(rows), 70)
        draft = json.loads(files['discovery-1/discovery-record.draft.json'])
        row = next(r for r in draft['capture_reviews'] if r['capture_id'] == missing[0]['capture_id'])
        self.assertEqual(row['state'], 'not_inspected')

    def test_wrong_package_binding_or_rehearsal_identity_produces_no_kit(self):
        self.request['package']['seal_sha256'] = 'f' * 64
        self.rejected('BINDING_CUSTODY', self.run_kit)
        self.assertFalse((self.root / 'kit').exists())
        self.make_package()
        self.identity = 'not-a-neutral-identity'
        self.rejected('DISCOVERY_ID', self.run_kit)
        self.assertFalse((self.root / 'kit').exists())

    def test_closed_request_and_hash_are_checked_before_output(self):
        self.request['pretend_review_completed'] = True
        self.rejected('BINDING_REQUEST', self.run_kit)
        self.assertFalse((self.root / 'kit').exists())
        request = self.selected()
        self.rejected('INPUT_DIGEST_MISMATCH', lambda: rehearsal.run(request['path'], '0'*64, self.identity, self.root/'kit'))

    def test_private_fresh_location_and_no_implicit_parent_creation(self):
        for output in (Path('relative-kit'), self.package_path / 'kit', rehearsal.ROOT / 'kit',
                       self.root / 'missing-parent' / 'kit'):
            with self.subTest(output=output):
                self.rejected('REHEARSAL_OUTPUT', lambda: self.run_kit(output))
                self.assertFalse(output.exists())
        target = self.root / 'existing'; target.mkdir(); (target / 'keep').write_bytes(b'owner bytes')
        self.rejected('OUTPUT_EXISTS', lambda: self.run_kit(target))
        self.assertEqual((target / 'keep').read_bytes(), b'owner bytes')
        link = self.root / 'link'; link.symlink_to(self.root / 'missing')
        self.rejected('OUTPUT_EXISTS', lambda: self.run_kit(link))

    def test_request_change_during_preparation_is_rejected_before_writing(self):
        selected = self.selected(); original = rehearsal.materialize
        def changed(*args):
            result = original(*args)
            Path(selected['path']).write_bytes(Path(selected['path']).read_bytes() + b' ')
            return result
        with patch.object(rehearsal, 'materialize', side_effect=changed):
            self.rejected('INPUT_DIGEST_MISMATCH', lambda: rehearsal.run(selected['path'], selected['sha256'], self.identity, self.root/'kit'))
        self.assertFalse((self.root / 'kit').exists())

    def test_code_or_guide_change_and_budget_rejected_without_output(self):
        with patch.object(rehearsal, 'code_identities', side_effect=[[['source','a']], [['source','b']]]):
            self.rejected('REHEARSAL_CODE_CHANGED', self.run_kit)
        self.assertFalse((self.root / 'kit').exists())
        with patch.object(rehearsal, 'MAX_KIT', 1):
            self.rejected('REHEARSAL_LIMIT', self.run_kit)
        self.assertFalse((self.root / 'kit').exists())

    def test_interrupted_write_has_no_completion_record_and_is_not_reused(self):
        original = rehearsal.atomic_write
        calls = 0
        def interrupted(path, data):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError('synthetic disk interruption')
            return original(path, data)
        with patch.object(rehearsal, 'atomic_write', side_effect=interrupted):
            with self.assertRaisesRegex(OSError, 'synthetic disk interruption'):
                self.run_kit()
        self.assertFalse((self.root/'kit/PREPARATION.json').exists())
        self.rejected('OUTPUT_EXISTS', self.run_kit)

    def test_changed_draft_before_completion_is_not_sealed(self):
        original = rehearsal.atomic_write
        def changed(path, data):
            return original(path, data + b' ' if Path(path).name == 'ANALYST.md' else data)
        with patch.object(rehearsal, 'atomic_write', side_effect=changed):
            self.rejected('REHEARSAL_OUTPUT_CHANGED', self.run_kit)
        self.assertFalse((self.root/'kit/PREPARATION.json').exists())

    def test_cli_preparation_receipt_binds_files_without_asserting_review(self):
        selected = self.selected(); output = self.root/'cli-kit'
        argv = [sys.executable, '-B', '-m', 'tools.perception_rehearsal',
                '--binding-request', selected['path'], '--binding-request-sha256', selected['sha256'],
                '--rehearsal-id', self.identity, '--output', str(output)]
        run = subprocess.run(argv, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout); receipt_bytes = (output/'PREPARATION.json').read_bytes()
        self.assertEqual(hashlib.sha256(receipt_bytes).hexdigest(), result['preparation_sha256'])
        receipt = json.loads(receipt_bytes)
        self.assertEqual(receipt['status'], 'unassigned_preparation')
        for field in ('human_review_performed', 'assisted_evidence_released', 'study_selection_performed', 'decision_evaluated'):
            self.assertIs(receipt[field], False)
        expected = {'PREPARATION.json'}
        for spec in receipt['files']:
            data = (output/spec['path']).read_bytes()
            self.assertEqual(len(data), spec['byte_size'])
            self.assertEqual(hashlib.sha256(data).hexdigest(), spec['sha256'])
            expected.add(spec['path'])
        self.assertEqual({str(p.relative_to(output)) for p in output.rglob('*') if p.is_file()}, expected)
        again = subprocess.run(argv, capture_output=True)
        self.assertEqual(again.returncode, 2)
        self.assertEqual(json.loads(again.stderr)['code'], 'OUTPUT_EXISTS')

    def test_extra_material_in_a_discovery_folder_prevents_completion(self):
        original = rehearsal.atomic_write
        def extra(path, data):
            original(path, data)
            if Path(path).name == 'ANALYST.md':
                (self.root / 'kit/discovery-1/extra-predictions.json').write_bytes(b'{}')
        with patch.object(rehearsal, 'atomic_write', side_effect=extra):
            self.rejected('REHEARSAL_OUTPUT_CHANGED', self.run_kit)
        self.assertFalse((self.root/'kit/PREPARATION.json').exists())


if __name__ == '__main__':
    unittest.main()
