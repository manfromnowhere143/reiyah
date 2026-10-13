#!/usr/bin/env python3
"""Authored mock-session controls. Never executes a detector or ONNX model."""
import hashlib
import json
from pathlib import Path
import tempfile
import types
from unittest.mock import patch

import numpy as np
import run_probe as w


class Fixture:
    def __init__(self, root):
        self.root = root
        self.calls = []
        self.mode = 'normal'
        self.sentinel = RuntimeError('authored ORT failure')
        self.tensor = np.zeros((1, 3, 2, 2), np.float32)
        self.tensor_desc = w.S.array_descriptor(self.tensor)
        self.base_taps = [{'name': 'authored_feature', 'rank': 2, 'elem_type': 1, 'role': 'control'}]
        self.corr_taps = self.base_taps + [
            {'name': 'reiyah_validity_v040/unmasked_foreground', 'rank': 3, 'elem_type': 1, 'role': 'control'},
            {'name': 'reiyah_validity_v040/valid_rpn_origin', 'rank': 2, 'elem_type': 9, 'role': 'control'}]
        self.base = [np.array([[[1, 1, 2, 2, .8]]], np.float32), np.array([[0]], np.int64),
                     np.array([[.5]], np.float32)]
        self.corrected = self.base + [np.array([[[.8]]], np.float32), np.array([[True]], np.bool_)]
        for name in ['baseline', 'corrected']:
            (root / (name + '.bin')).write_bytes(('authored-' + name).encode())
        np.save(root / 'tensor.npy', self.tensor, allow_pickle=False)
        self.write('taps.json', self.corr_taps)
        self.prior_dir = root / 'prior'; self.prior_dir.mkdir()
        store = w.S.ArrayStore(self.prior_dir)
        store.save('baseline', ['dets', 'labels'], self.base[:2])
        store.save('tapped', ['dets', 'labels', 'authored_feature'], self.base)
        self.write('prior/result.json', {'status': 'complete', 'stage': 'complete',
            'forward_passes_completed': 2, 'baseline_matches_prior_bitwise': True,
            'tapped_matches_baseline_bitwise': True, 'arrays': store.records})
        build = {'artifact_id': 'reiyah.multiorg.validity-preserving-export', 'version': '0.4.0',
            'source_sha256': w.SOURCE_SHA, 'observation_sha256': self.ref('corrected.bin')['sha256'],
            'taps_sha256': self.ref('taps.json')['sha256'], 'observation_only_outputs': self.corr_taps,
            'checker': 'passed', 'batch_support': [1], 'original_fields_otherwise_unchanged': True}
        self.write('build.json', build)
        self.protocol = {'worker_contract': 'origin_validity_observation_v040', 'tensor': self.tensor_desc,
            'input_name': 'input', 'original_outputs': ['dets', 'labels'], 'max_saved_array_bytes': w.S.ARRAY_CAP,
            'baseline_taps': self.base_taps, 'corrected_taps': self.corr_taps}
        self.write('protocol.json', self.protocol)
        self.manifest = {'protocol': self.ref('protocol.json'),
            'images': [{'id': w.IMAGE_ID, 'source': self.ref('tensor.npy')}],
            'models': {key: self.ref(filename) for key, filename in {
                'baseline': 'baseline.bin', 'corrected': 'corrected.bin', 'build': 'build.json',
                'taps': 'taps.json', 'prior_result': 'prior/result.json'}.items()}, 'limits': dict(w.LIMITS)}
        self.manifest['models']['support'] = {'path': str(w.SUPPORT_PATH), 'sha256': w.SUPPORT_SHA}
        self.pins = {name: ref['sha256'] for name, ref in self.manifest['models'].items()}
        self.save_manifest()

    def write(self, name, value):
        (self.root / name).write_bytes(w.canonical(value) + b'\n')

    def ref(self, name):
        path = self.root / name
        return {'path': str(path), 'sha256': w.S.digest(path)}

    def save_manifest(self): self.write('manifest.json', self.manifest)

    def repin(self, key, filename):
        self.manifest['models'][key] = self.ref(filename)
        self.pins[key] = self.manifest['models'][key]['sha256']
        self.save_manifest()

    def session(self, path):
        stage = 'baseline' if path.name == 'baseline.bin' else 'corrected'
        fixture = self
        class Session:
            def get_providers(self):
                return ['CUDAExecutionProvider'] if fixture.mode == 'provider' else ['CPUExecutionProvider']
            def get_outputs(self):
                names = ['dets', 'labels'] + [t['name'] for t in (fixture.base_taps if stage == 'baseline' else fixture.corr_taps)]
                if fixture.mode == 'unexpected_output': names[-1] = 'unexpected'
                return [types.SimpleNamespace(name=n) for n in names]
            def get_inputs(self):
                batch = 'batch' if stage == 'baseline' or fixture.mode == 'unguarded_batch' else 1
                return [types.SimpleNamespace(name='input', type='tensor(float)', shape=[batch, 3, 2, 2])]
            def run(self, names, inputs):
                fixture.calls.append(stage)
                if fixture.mode == 'runtime_failure' and stage == 'corrected': raise fixture.sentinel
                arrays = [x.copy() for x in (fixture.base if stage == 'baseline' else fixture.corrected)]
                if fixture.mode == 'baseline_mismatch' and stage == 'baseline': arrays[2][0, 0] = .6
                if fixture.mode == 'nonfinite' and stage == 'corrected': arrays[2][0, 0] = np.nan
                if fixture.mode == 'wrong_mask_type' and stage == 'corrected': arrays[-1] = arrays[-1].astype(np.int64)
                if fixture.mode == 'source_change' and stage == 'corrected':
                    (fixture.root / 'corrected.bin').write_bytes(b'changed-source')
                return arrays
        return Session()

    def execute(self):
        with patch.object(w, 'PINS', self.pins), patch.object(w, 'TENSOR', self.tensor_desc), \
             patch.object(w, 'BASELINE_TAPS_CANONICAL_SHA', hashlib.sha256(w.canonical(self.base_taps)).hexdigest()), \
             patch.object(w.S, 'session', self.session):
            return w.execute(self.root / 'manifest.json', self.root / 'output')


def main():
    passed = []
    def case(name, action):
        with tempfile.TemporaryDirectory(prefix='authored-worker-', dir=Path(__file__).parent) as tmp:
            fixture = Fixture(Path(tmp))
            action(fixture)
        passed.append(name)

    def failure(f, expected_passes=0, contains=None):
        try: f.execute()
        except Exception as exc:
            if contains: assert contains in str(exc), str(exc)
        else: raise AssertionError('unexpected success')
        receipt = w.S.read_json(f.root / 'output/failure.json')
        assert receipt['status'] == 'failed'
        assert receipt['forward_passes_completed'] == expected_passes
        assert not (f.root / 'output/result.json').exists()
        return receipt

    def success(f):
        r = f.execute()
        assert f.calls == ['baseline', 'corrected']
        assert r['status'] == 'complete' and r['forward_passes_completed'] == 2
        assert r['baseline_matches_prior_bitwise'] and len(r['arrays']) == 8
        assert r['arrays'][-1]['dtype'] == '|b1'
    case('two_pass_mock_capture_with_bool_mask', success)
    def mode_case(mode, count, message):
        def action(f):
            f.mode = mode
            r = failure(f, count, message)
            if count: assert len(r['arrays']) >= 3
        return action
    for name, mode, count, message in [
        ('baseline_mismatch_stops_before_corrected', 'baseline_mismatch', 1, 'baseline differs'),
        ('nonfinite_corrected_retains_arrays_without_completion', 'nonfinite', 2, 'nonfinite'),
        ('unexpected_output_roster_rejected', 'unexpected_output', 0, 'output roster'),
        ('nonCPU_provider_rejected', 'provider', 0, 'CPU provider'),
        ('unsupported_dynamic_corrected_batch_rejected', 'unguarded_batch', 1, 'batch-one'),
        ('wrong_bool_mask_dtype_rejected', 'wrong_mask_type', 2, 'dtype or rank'),
        ('source_mutation_during_execution_rejected', 'source_change', 2, 'source changed')]:
        case(name, mode_case(mode, count, message))
    def runtime_failure(f):
        f.mode = 'runtime_failure'
        try: f.execute()
        except RuntimeError as exc: assert exc is f.sentinel
        else: raise AssertionError('runtime exception lost')
        r = w.S.read_json(f.root / 'output/failure.json')
        assert r['forward_passes_started'] == 2 and r['forward_passes_completed'] == 1
        assert len(r['arrays']) == 3 and not (f.root / 'output/result.json').exists()
    case('runtime_failure_preserves_exception_and_partial_capture', runtime_failure)
    def wrong_source(f):
        (f.root / 'baseline.bin').write_bytes(b'wrong')
        failure(f, contains='source identity')
    case('source_bytes_mismatch_before_any_forward', wrong_source)
    def traversal(f):
        f.manifest['models']['baseline']['path'] = str(f.root / '..' / f.root.name / 'baseline.bin')
        f.save_manifest(); failure(f, contains='path traversal')
    case('path_traversal_rejected', traversal)
    def duplicate(f):
        (f.root / 'manifest.json').write_text('{"protocol":{},"protocol":{}}')
        failure(f, contains='duplicate JSON')
    case('duplicate_JSON_rejected', duplicate)
    def unexpected_property(f):
        f.manifest['extra'] = 1; f.save_manifest(); failure(f, contains='manifest schema')
    case('unexpected_manifest_property_rejected', unexpected_property)
    def wrong_tensor(f):
        f.protocol['tensor']['shape'] = [1, 3, 3, 3]
        f.write('protocol.json', f.protocol); f.manifest['protocol'] = f.ref('protocol.json'); f.save_manifest()
        # Fixture tensor descriptor was aliased intentionally above; restore frozen expected shape.
        f.tensor_desc = w.S.array_descriptor(f.tensor)
        failure(f, contains='frozen protocol')
    case('empirical_tensor_contract_cannot_be_relaxed_by_manifest', wrong_tensor)
    def malformed_shape(f):
        f.protocol['tensor'] = dict(f.tensor_desc, shape=[1.0, 3, 2, 2])
        f.write('protocol.json', f.protocol); f.manifest['protocol'] = f.ref('protocol.json'); f.save_manifest()
        failure(f, contains='tensor schema')
    case('noninteger_tensor_shape_rejected', malformed_shape)
    def duplicate_tap(f):
        f.protocol['baseline_taps'] = f.base_taps * 2
        f.write('protocol.json', f.protocol); f.manifest['protocol'] = f.ref('protocol.json'); f.save_manifest()
        failure(f, contains='duplicate or invalid output')
    case('duplicate_tap_rejected', duplicate_tap)
    def prior_tamper(f):
        row = w.S.read_json(f.prior_dir / 'result.json')['arrays'][-1]
        (f.prior_dir / row['file']).write_bytes(b'corrupted-npy')
        failure(f, contains='prior file length')
    case('prior_array_tamper_rejected', prior_tamper)
    def prior_path(f):
        p = w.S.read_json(f.prior_dir / 'result.json'); p['arrays'][0]['file'] = '../outside.npy'
        f.write('prior/result.json', p); f.repin('prior_result', 'prior/result.json')
        failure(f, contains='prior array path')
    case('prior_array_traversal_rejected', prior_path)
    def support_identity(f):
        copy = f.root / 'support-copy.py'; copy.write_bytes(w.SUPPORT_PATH.read_bytes())
        f.manifest['models']['support']['path'] = str(copy); f.save_manifest()
        failure(f, contains='imported support identity')
    case('support_ref_must_match_imported_file', support_identity)
    def log_failure(f):
        f.mode = 'runtime_failure'
        with patch.object(w.S, 'write_json', side_effect=OSError('authored log failure')):
            try: f.execute()
            except RuntimeError as exc: assert exc is f.sentinel
            else: raise AssertionError('logging replaced original exception')
    case('logging_failure_preserves_original_runtime_exception', log_failure)
    here = Path(__file__).parent
    report = {'status': 'passed', 'count': len(passed), 'controls': passed,
              'scope': 'small authored arrays and mocked sessions; zero model forwards',
              'test_overrides': 'Only in-process unit tests replace numerical source/tensor pins with authored fixture identities.',
              'scripts': {name: w.S.digest(here / name, 1048576)
                          for name in ['run_probe.py', 'test_run_probe.py', 'trace_support.py']}}
    w.S.write_json(here / 'QUALIFICATION_worker.json', report)
    print(json.dumps({'status': 'passed', 'controls': len(passed)}))


if __name__ == '__main__':
    main()
