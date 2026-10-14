#!/usr/bin/env python3
"""Authored mock pair and exact pinned ORT failure-policy controls; no inference."""
import argparse
import contextlib
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import types
from unittest.mock import patch

import numpy as np
import complete_pair as w


class Fixture:
    def __init__(self, root):
        self.root = root; self.calls = []; self.mode = 'normal'; self.sessions = []
        self.error = RuntimeError('authored run failure')
        self.roster = [[0, 0], [0, 256]]
        self.shapes = {'original': [2, 514], 'rescaled': [1, 257], 'padded': [512, 768]}
        self.image_id = w.ALLOWED_IMAGE_IDS[0]
        self.image_sha = 'd' * 64
        self.limits = {'wall_seconds': 600, 'memory_bytes': 3221225472, 'max_tiles_per_image': 2,
            'max_raw_boxes_per_image': 200000, 'max_array_file_bytes': 67108864, 'max_array_total_bytes': 134217728}
        self.contract = {'image_id': self.image_id, 'image_sha256': self.image_sha, 'image_bytes': 14,
            'shapes': self.shapes, 'tile_roster': self.roster, 'input_roster_sha256': 'c' * 64,
            'limits': self.limits, 'array_budget': {'authored': True}}
        self.pixels = np.zeros((512, 768), np.uint8)
        self.tensor = np.zeros((1, 3, 8, 8), np.float32)
        self.original = w.module(Path(w.__file__).with_name('run_pair.py'), w.ORIGINAL_SHA, '_test_original')
        self.projection = w.module(Path(w.__file__).with_name('projection.py'), w.PROJECTION_SHA, '_test_projection')
        self.original.model_input = lambda pixels, model: (self.tensor.copy(), 800 if model == 'faster' else 416)
        self.taps = [{'name': 'authored_tap_' + str(i), 'rank': 2, 'elem_type': 1, 'role': 'control'} for i in range(31)]
        names = ['dets', 'labels'] + [x['name'] for x in self.taps]
        self.reference = types.SimpleNamespace(NAMES=tuple(names), validate_tile=self.admit)
        self.refs, self.paths = {}, {}
        for key in ['protocol', 'image', 'faster', 'yolo', 'original', 'projection', 'taps', 'origin_reference', 'reference_core']:
            path = root / (key + '.bin'); path.write_bytes(('authored-' + key).encode())
            self.paths[key] = path; self.refs[key] = {'path': str(path), 'sha256': w.file_sha(path)}
        rows = []
        for model in ['faster', 'yolo']:
            for ordinal, (row, column) in enumerate(self.roster):
                rows.append({'model': model, 'ordinal': ordinal, 'rescaled_row': row, 'rescaled_column': column,
                    'resized_side': 800 if model == 'faster' else 416,
                    'tensor': {'dtype': '<f4', 'shape': list(self.tensor.shape),
                               'c_order_data_sha256': w.sha(self.tensor.tobytes())}})
        self.input_roster = {'artifact_id': 'reiyah.multiorg.complete-pair.input-roster', 'version': '0.6.0',
            'status': 'complete', 'original_worker_sha256': w.ORIGINAL_SHA, 'image_source_sha256': self.image_sha,
            'image_id': self.image_id, 'image_shape_hw': self.shapes['original'], 'rescaled_shape_hw': self.shapes['rescaled'],
            'padded_shape_hw': self.shapes['padded'], 'roster': self.roster, 'tiles_per_model': 2, 'tensors': rows,
            'quantized_pixels_c_order_sha256': w.sha(self.pixels.tobytes())}
        path = root / 'input-roster.json'; path.write_bytes(w.canonical(self.input_roster))
        self.paths['input_roster'] = path; self.refs['input_roster'] = {'path': str(path), 'sha256': w.file_sha(path)}
        self.manifest = root / 'manifest.json'; self.manifest.write_bytes(b'{"authored_fixture":true}')

    def admit(self, named):
        if self.mode == 'origin_failure': raise ValueError('authored origin refusal')
        if self.mode == 'origin_unadmitted': return {'status': 'failed'}
        return {'status': 'corrected_variant_tile_admitted', 'original_baseline_comparison_performed': False}

    def session(self, path, model, original):
        fixture = self
        class Session:
            def get_providers(self): return ['CPUExecutionProvider']
            def get_inputs(self): return [types.SimpleNamespace(name='input', type='tensor(float)', shape=[1, 3, 'H', 'W'])]
            def get_outputs(self):
                names = ['dets', 'labels'] + ([t['name'] for t in fixture.taps] if model == 'faster' else [])
                if fixture.mode == 'wrong_names': names[0], names[1] = names[1], names[0]
                return [types.SimpleNamespace(name=x) for x in names]
            def run(self, names, feed):
                ordinal = sum(x[0] == model for x in fixture.calls)
                fixture.calls.append((model, ordinal))
                if fixture.mode == 'runtime_failure' and model == 'faster' and ordinal == 1: raise fixture.error
                if fixture.mode == 'yolo_failure' and model == 'yolo': raise fixture.error
                score = 0.0 if fixture.mode == 'empty' else .8
                values = [np.array([[[1, 1, 4, 4, score]]], np.float32), np.zeros((1, 1), np.int64)]
                if fixture.mode == 'high_invalid': values[0][0, 0, :4] = 0
                if fixture.mode == 'nonfinite': values[0][0, 0, 0] = np.nan
                if model == 'faster': values += [np.zeros((1, 1), np.float32) for _ in fixture.taps]
                if fixture.mode == 'source_mutation' and model == 'yolo' and ordinal == 1:
                    fixture.paths['image'].write_bytes(b'mutated')
                if fixture.mode == 'wrong_yolo_dtype' and model == 'yolo': values[1] = values[1].astype(np.int32)
                return values
        result = Session(); self.sessions.append(result); return result

    def execute(self):
        bound = ({'authored_fixture': True}, self.refs, self.paths, {}, self.original, self.projection, self.reference, self.taps, self.contract)
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(w, 'bind', return_value=bound))
            stack.enter_context(patch.object(w, 'prepare', return_value=(self.pixels, self.shapes['rescaled'], self.shapes['original'], self.roster)))
            stack.enter_context(patch.object(w, 'make_session', self.session))
            return w.execute(self.manifest, self.root / 'output')


def main():
    p = argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--manifest', type=Path, action='append', default=[], help='repeatable optional real prospective sources for read-only binding controls; no inference')
    a = p.parse_args()
    passed = []
    def case(name, action):
        with tempfile.TemporaryDirectory(prefix='authored-pair-', dir=Path(__file__).parent) as tmp:
            action(Fixture(Path(tmp)))
        passed.append(name)
    def fail(f, text):
        try: f.execute()
        except Exception as exc: assert text in str(exc), str(exc)
        else: raise AssertionError('unexpected completion')
        assert not (f.root / 'output/result.json').exists()
        return w.load_json(f.root / 'output/failure.json')
    def complete(f):
        r = f.execute(); assert r['status'] == 'complete'
        assert r['forward_passes_completed'] == 4 and len(r['observations']) == 2
        assert len(list((f.root / 'output/raw').glob('*.npy'))) == 70
        assert len(list((f.root / 'output/admissions').glob('*.json'))) == 4
        assert all(x == {'captured': 2, 'admitted': 2, 'complete': True} for x in r['tile_coverage'].values())
        for desc in r['observations']:
            image = w.load_json(f.root / 'output' / desc['file'])
            assert image['tile_count_completed'] == 2 and image['raw_onnx_rows'] == 2
    case('complete_mock_pair_all_named_arrays_and_individual_admissions', complete)
    def empty(f):
        f.mode = 'empty'; r = f.execute()
        for desc in r['observations']:
            image = w.load_json(f.root / 'output' / desc['file'])
            assert image['empty_analysis'] and image['analysis_predictions'] == [] and image['raw_onnx_rows'] == 2
    case('complete_observed_empty_analysis_is_distinct_from_missing', empty)
    def partial(f):
        f.mode = 'runtime_failure'; r = fail(f, 'authored run failure')
        assert r['forward_passes_started'] == 2 and r['forward_passes_completed'] == 1
        assert r['tile_coverage']['faster'] == {'captured': 1, 'admitted': 1, 'complete': False}
        assert r['observations'] == [] and r['last_admission_receipt'] is not None
        assert len(list((f.root / 'output/raw').glob('*.npy'))) == 33
    case('runtime_failure_retains_prior_tile_without_inventing_remaining_tiles', partial)
    def second_model_failure(f):
        f.mode = 'yolo_failure'; r = fail(f, 'authored run failure')
        assert len(r['observations']) == 1 and r['tile_coverage']['faster']['complete']
        assert r['tile_coverage']['yolo'] == {'captured': 0, 'admitted': 0, 'complete': False}
    case('one_complete_model_does_not_become_complete_pair', second_model_failure)
    for mode, text in [('wrong_names', 'named ONNX output roster'), ('nonfinite', 'nonfinite named output'),
                       ('origin_failure', 'authored origin refusal'), ('origin_unadmitted', 'did not admit'),
                       ('high_invalid', 'undefined high-score geometry'),
                       ('wrong_yolo_dtype', 'dtype/rank'), ('source_mutation', 'source changed')]:
        def action(f, mode=mode, text=text):
            f.mode = mode; r = fail(f, text)
            if mode != 'wrong_names': assert r['last_raw_receipt'] is not None
            else: assert r['forward_passes_started'] == 0
        case(mode + '_refused_with_explicit_capture_state', action)
    def tensor_mismatch(f):
        f.tensor[0, 0, 0, 0] = 1
        r = fail(f, 'actual tensor differs'); assert r['forward_passes_started'] == 0
    case('tensor_identity_checked_before_forward', tensor_mismatch)
    def bad_roster(f):
        obj = dict(f.input_roster); obj['tensors'] = obj['tensors'][:-1]
        f.paths['input_roster'].write_bytes(w.canonical(obj))
        r = fail(f, 'cardinality'); assert r['forward_passes_started'] == 0
    case('missing_expected_input_tensor_rejected_upfront', bad_roster)
    def bad_slice(f):
        f.pixels = f.pixels[:, :512]
        f.input_roster['quantized_pixels_c_order_sha256'] = w.sha(f.pixels.tobytes())
        f.paths['input_roster'].write_bytes(w.canonical(f.input_roster))
        r = fail(f, 'incomplete prospective tile'); assert r['forward_passes_started'] == 0
    case('all_expected_tile_slices_verified_before_any_forward', bad_slice)
    def cap(f):
        f.limits['max_array_total_bytes'] = 1
        r = fail(f, 'aggregate array cap')
        assert r['forward_passes_completed'] == 1 and r['tile_coverage']['faster']['captured'] == 0
    case('raw_capture_cap_is_refusal_not_empty_output', cap)
    def coverage(f):
        projection = f.projection.project_tile([np.zeros((1,0,5),np.float32), np.zeros((1,0),np.int64)],
            0, 0, 800, decoder=f.original.decode_output, remaining_raw_rows=200000)
        try: f.projection.complete_projection([{'ordinal': 0, 'projection': projection}], expected_tiles=2,
            raw_cap=200000, nms=f.original.stable_nms)
        except ValueError as exc: assert 'incomplete' in str(exc)
        else: raise AssertionError('incomplete whole image accepted')
    case('unchanged_projection_rejects_missing_tile_population', coverage)
    # Exercise the installed Python wrapper, without constructing a C++ model.
    import onnxruntime as ort
    import onnxruntime.capi.onnxruntime_inference_collection as collection
    def policy(f):
        path = f.root / 'fake-model'; path.write_bytes(b'mock')
        original = types.SimpleNamespace(MODELS={'yolo': {'bytes': 4, 'md5': hashlib.md5(b'mock').hexdigest()}})
        calls = []
        def creation_error(self, *args): calls.append(args); raise RuntimeError('authored creation failure')
        with patch.object(ort.InferenceSession, '_create_inference_session', creation_error):
            try: w.make_session(path, 'yolo', original)
            except RuntimeError as exc: assert 'authored creation failure' in str(exc)
            else: raise AssertionError('creation should fail')
        assert len(calls) == 1
        events = []
        class FakeSession:
            def disable_fallback(self): events.append('disabled')
        def constructor(*args, **kwargs):
            assert kwargs['enable_fallback'] is False
            assert kwargs['providers'] == ['CPUExecutionProvider']
            events.append('constructed'); return FakeSession()
        with patch.object(ort, 'InferenceSession', constructor): w.make_session(path, 'yolo', original)
        assert events == ['constructed', 'disabled']
        session = ort.InferenceSession.__new__(ort.InferenceSession)
        session._inputs_meta = []; session._enable_fallback = True
        error = collection.C.EPFail('authored provider failure')
        run_calls = []
        def run(*args): run_calls.append(args); raise error
        session._sess = types.SimpleNamespace(run=run)
        session.disable_fallback()
        try: session.run(['dets'], {})
        except collection.C.EPFail as exc: assert exc is error
        else: raise AssertionError('EPFail swallowed')
        assert len(run_calls) == 1
    case('installed_ORT_constructor_and_run_failure_have_no_hidden_retry', policy)
    def selection(f):
        contracts = {identity: {**copy.deepcopy(f.contract), 'image_id': identity} for identity in w.ALLOWED_IMAGE_IDS}
        with patch.object(w, 'IMAGE_CONTRACTS', contracts):
            for identity in w.ALLOWED_IMAGE_IDS:
                chosen = w.selected_contract(identity)
                assert chosen['image_id'] == identity
                chosen['tile_roster'][0][0] = 99
                assert contracts[identity]['tile_roster'][0][0] == 0
            for identity in ['MultiOrg_v2/test/Macros/Plate_4/image_7/image_7.tiff', 'unselected', None, True, []]:
                try: w.selected_contract(identity)
                except ValueError as exc: assert 'exact remaining' in str(exc)
                else: raise AssertionError('nonselected image admitted')
    case('only_three_exact_selected_images_with_no_shared_mutable_context', selection)
    def missing_contract(f):
        with patch.object(w, 'IMAGE_CONTRACTS', {}):
            try: w.selected_contract(w.ALLOWED_IMAGE_IDS[0])
            except ValueError as exc: assert 'not yet qualified' in str(exc)
            else: raise AssertionError('unqualified image accepted')
    case('absent_exact_contract_cannot_start_execution', missing_contract)
    def cross_image(f):
        f.contract['image_id'] = w.ALLOWED_IMAGE_IDS[1]
        r = fail(f, 'input roster identity'); assert r['forward_passes_started'] == 0
    case('another_selected_images_input_roster_cannot_be_substituted', cross_image)
    def wrong_source(f):
        f.contract['image_sha256'] = 'e' * 64
        r = fail(f, 'input roster identity'); assert r['forward_passes_started'] == 0
    case('input_roster_source_identity_cannot_be_substituted', wrong_source)
    def single_image(f):
        for images in ([], [None], [True], [{'id': f.image_id}],
                       [{'id': f.image_id, 'source': {}}, {'id': f.image_id, 'source': {}}]):
            manifest={'protocol': {}, 'models': {key: {} for key in set(w.PINS) | {'input_roster'}}, 'images': images, 'limits': f.limits}
            path=f.root/'reject-manifest.json';path.write_bytes(w.canonical(manifest))
            try: w.bind(path)
            except ValueError as exc: assert 'single selected image schema' in str(exc)
            else: raise AssertionError('non-single or malformed image accepted')
    case('one_explicit_image_per_invocation_schema', single_image)
    for manifest_index, manifest_path in enumerate(a.manifest, 1):
        label = str(manifest_index) + ":"
        prospective = w.load_json(manifest_path)
        bound = w.bind(manifest_path)
        assert len(bound[7]) == 31 and bound[3]['tile_roster'] == bound[8]['tile_roster']
        passed.append(label + 'real_prospective_manifest_all_source_bindings_pass_without_inference')
        with tempfile.TemporaryDirectory(prefix='authored-binding-', dir=Path(__file__).parent) as tmp:
            tmp = Path(tmp)
            def rejected(name, mutation, message):
                value = json.loads(json.dumps(prospective))
                mutation(value)
                path = tmp / (name + '.json'); path.write_bytes(w.canonical(value))
                try: w.bind(path)
                except ValueError as exc: assert message in str(exc), str(exc)
                else: raise AssertionError('malformed binding accepted: ' + name)
                passed.append(label + name)
            rejected('unknown_manifest_property_rejected', lambda x: x.update(extra=True), 'manifest schema')
            def traversal(x): x['models']['faster']['path'] = str(tmp / '..' / 'faster.onnx')
            rejected('source_path_traversal_rejected', traversal, 'path traversal')
            def wrong_digest(x): x['models']['faster']['sha256'] = '0' * 64
            rejected('model_digest_replacement_rejected', wrong_digest, 'source binding mismatch')
            def boolean_roster(x):
                protocol = w.load_json(x['protocol']['path'])
                protocol['tile_roster'][0][0] = False
                path = tmp / 'boolean-roster-protocol.json'; path.write_bytes(w.canonical(protocol))
                x['protocol'] = {'path': str(path), 'sha256': w.file_sha(path)}
            rejected('boolean_tile_coordinate_cannot_impersonate_integer_zero', boolean_roster, 'tile integer schema')
            path = tmp / 'duplicate.json'; path.write_text('{"protocol":{},"protocol":{}}')
            try: w.bind(path)
            except ValueError as exc: assert 'duplicate JSON' in str(exc)
            else: raise AssertionError('duplicate JSON accepted')
            passed.append(label + 'duplicate_JSON_key_rejected')
    result = {'status': 'passed', 'count': len(passed), 'controls': passed,
        'scope': 'Authored small arrays and mocked model sessions; installed ORT Python retry policy tested without model construction/inference.',
        'test_overrides': 'Two-tile authored fixture replaces prospective bindings/preprocessing/session execution only inside unit tests.',
        'scripts': {name: w.file_sha(Path(__file__).with_name(name)) for name in ['complete_pair.py','test_complete_pair.py','run_pair.py','projection.py']},
        'empirical_forward_passes': 0}
    if a.manifest: result['static_manifest_sha256'] = [w.file_sha(path) for path in a.manifest]
    w.write_json(a.output, result); print(json.dumps({'status': 'passed', 'controls': len(passed)}))


if __name__ == '__main__': main()
