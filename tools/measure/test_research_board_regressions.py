"""Offline regressions for concrete research-board counterexamples.

Run with an interpreter providing numpy, scipy, and jsonschema:
  python -m unittest discover -s tools/measure -p 'test_research_board_regressions.py' -v

No dataset, network, model, or active-worktree mutation is required.
"""
import importlib.util
import io
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    'reference_audit', ROOT / 'tools/measure/result_ao_reference_population_audit.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class MatcherExitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='reiyah-matcher-test-')
        self.addCleanup(self.tmp.cleanup)
        self.case = pathlib.Path(self.tmp.name)
        (self.case / 'gt.json').write_text(json.dumps([{
            'cls': 'car', 'sample_token': 's1', 'xy': [0, 0],
            'ego_xy': [0, 0], 'nl': 1, 'nr': 0}]))
        (self.case / 'pred.json').write_text(json.dumps({'results': {'s1': []}}))
        self.output = self.case / 'output.json'

    def run_matcher(self, expected):
        return subprocess.run([
            sys.executable, '-B', str(ROOT / 'tools/measure/match.py'),
            str(self.case / 'gt.json'), str(self.case / 'pred.json'),
            str(self.output), '--validate', expected], capture_output=True, timeout=20)

    def test_rejected_accuracy_does_not_create_artifact(self):
        result = self.run_matcher('99')
        self.assertEqual(result.returncode, 1)
        self.assertIn(b'[FAIL]', result.stderr)
        self.assertFalse(self.output.exists())

    def test_rejected_accuracy_preserves_existing_artifact(self):
        self.output.write_bytes(b'previous result, not from this failed run')
        result = self.run_matcher('99')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.output.read_bytes(), b'previous result, not from this failed run')

    def test_valid_zero_accuracy_emits_valid_empty_match_set(self):
        result = self.run_matcher('0')
        self.assertEqual(result.returncode, 0, result.stderr)
        artifact = json.loads(self.output.read_text())
        self.assertEqual(artifact['reconstructed_mAP'], 0)
        self.assertTrue(all(not v for v in artifact['matched_at_2m'].values()))

    def test_nonfinite_and_out_of_range_comparators_are_refused(self):
        for value in ['nan', 'inf', '-1', '101']:
            with self.subTest(value=value):
                result = self.run_matcher(value)
                self.assertEqual(result.returncode, 2)
                self.assertFalse(self.output.exists())


class ReferencePopulationTests(unittest.TestCase):
    def test_excluding_an_annotation_can_create_a_false_absence_flag(self):
        prediction = np.array([[10., 0.]])
        filtered = np.array([[0., 0.]])
        full = np.array([[0., 0.], [10., 0.]])
        self.assertGreater(audit.reference_distances(prediction, filtered)[0][0], 2)
        self.assertLessEqual(audit.reference_distances(prediction, full)[0][0], 2)

    def test_missing_sample_and_empty_sample_are_different(self):
        with self.assertRaisesRegex(ValueError, 'omits'):
            audit.require_sample_coverage({}, {'s1'})
        audit.require_sample_coverage({'s1': []}, {'s1'})

    def test_missing_reference_cannot_certify_absence(self):
        with self.assertRaisesRegex(ValueError, 'unavailable'):
            audit.reference_distances(np.array([[0., 0.]]), [])

    def test_ego_relative_transport_does_not_preserve_static_world_geometry(self):
        static_object = np.array([[10., 0.]])
        relocated = audit.ego_relocate(
            static_object, np.array([0., 0.]), np.array([5., 0.]), 0., 0.)
        self.assertEqual(audit.count_coincidence(static_object, static_object), 1)
        self.assertEqual(audit.count_coincidence(static_object, relocated), 0)

    def test_empty_donor_is_zero_coincidence(self):
        self.assertEqual(audit.count_coincidence(np.array([[0., 0.]]), np.empty((0, 2))), 0)

    def test_annotation_stream_handles_utf8_split_across_reads(self):
        class TinyReads(io.BytesIO):
            def read(self, _size=-1):
                return super().read(1)
        payload = json.dumps([{'text': 'café'}, {'x': 3}], ensure_ascii=False).encode()
        self.assertEqual(list(audit.stream_array(TinyReads(payload))), [{'text': 'café'}, {'x': 3}])

    def test_annotation_stream_rejects_incomplete_or_malformed_reference(self):
        for payload in [b'[{}', b'[{},]', b'[{},,{}]', b'[{} {}]', b'{}', b'[{}] {}']:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                list(audit.stream_array(io.BytesIO(payload)))

    def test_audit_cannot_overwrite_source_input(self):
        with tempfile.TemporaryDirectory(prefix='reiyah-output-test-') as temp:
            source = pathlib.Path(temp) / 'gt_val_cache.json'
            source.write_bytes(b'original source')
            result = subprocess.run([
                sys.executable, '-B', str(ROOT / 'tools/measure/result_ao_reference_population_audit.py'),
                '--data-root', temp, '--output', str(source)], capture_output=True, timeout=20)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b'Outputs must be distinct', result.stderr)
            self.assertEqual(source.read_bytes(), b'original source')


class ReplayExitTests(unittest.TestCase):
    def exercise_producer(self, exit_code):
        with tempfile.TemporaryDirectory(prefix='reiyah-replay-test-') as temp:
            scratch = pathlib.Path(temp)
            # Copy only tracked artifact directories relevant to this checker. No input caches.
            for name in ['docs', 'evidence', 'schemas', 'validation', 'tools',
                         'human-channel', 'llm-generalization', 'research']:
                shutil.copytree(ROOT / name, scratch / name,
                                ignore=shutil.ignore_patterns('__pycache__'))
            for p in ROOT.glob('*.md'):
                shutil.copy2(p, scratch / p.name)
            manifest_path = scratch / 'validation/gate-b-replay-manifest.json'
            manifest = json.loads(manifest_path.read_text())
            for row in manifest['transcripts']:
                if row['replay_class'] == 'local_deterministic':
                    row['replay_class'] = 'argv_unrecorded_historical'
            target = manifest['transcripts'][0]
            target['replay_class'] = 'local_deterministic'
            producer = ('import pathlib,sys;'
                        'sys.stdout.buffer.write(pathlib.Path(sys.argv[1]).read_bytes());'
                        f'sys.exit({exit_code})')
            target['argv'] = [sys.executable, '-B', '-c', producer, target['transcript']]
            manifest_path.write_text(json.dumps(manifest))
            report_path = scratch / 'test-report.json'
            result = subprocess.run([
                sys.executable, '-B', 'tools/measure/gate_b_check.py',
                '--replay', 'local_deterministic', '--json', str(report_path)],
                cwd=scratch, capture_output=True, timeout=90)
            self.assertEqual(result.returncode, 1 if exit_code else 0, result.stdout + result.stderr)
            report = json.loads(report_path.read_text())
            item = next(x for x in report['items'] if x['transcript'] == target['transcript'])
            self.assertEqual(item['process_returncode'], exit_code)
            self.assertEqual(item['raw_stdout_sha256'], target['sha256'])
            self.assertEqual(item['replay_state'], 'diverged' if exit_code else 'replicated')
            failed = [c for c in report['checks'] if c['state'] == 'fail']
            self.assertEqual(len(failed), 1 if exit_code else 0, failed)
            if exit_code:
                self.assertTrue(failed[0]['check'].startswith('REPLAY'))

    def test_matching_stdout_cannot_hide_failed_process(self):
        self.exercise_producer(17)

    def test_successful_matching_producer_is_accepted(self):
        self.exercise_producer(0)


if __name__ == '__main__':
    unittest.main()
