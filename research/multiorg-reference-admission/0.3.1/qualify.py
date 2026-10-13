#!/usr/bin/env python3
"""Authored controls only; never loads the empirical model or image.

Run with the ONNX parser Python and --runtime pointing to the unmodified ORT
Python. All fixtures and receipts are retained in a new --output directory.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def authored_model():
    import numpy as np
    import onnx
    h, n = onnx.helper, onnx.numpy_helper
    initializers = []
    def const(name, value, dtype=np.float32):
        initializers.append(n.from_array(np.array(value, dtype=dtype), name))
        return name
    const('pre_const', [[[1, 1, 3, 3, .8]]])
    const('pad_const', [[[0, 0, 0, 0, 0]]])
    const('zero', 0); const('one', 1)
    const('score_axis', 4, np.int64); const('x_axis', 0, np.int64)
    const('k', [2], np.int64); const('flat_shape', [2, 5], np.int64)
    const('starts', [0], np.int64); const('ends', [4], np.int64)
    const('axes', [1], np.int64); const('labels_const', [[0, 0]], np.int64)
    nodes = []
    def node(op, ins, outs, **kwargs): nodes.append(h.make_node(op, ins, outs, **kwargs))
    node('ReduceSum', ['input'], ['input_sum'], keepdims=0)
    node('Mul', ['input_sum', 'zero'], ['input_zero'])
    node('Add', ['pre_const', 'input_zero'], ['pre'])
    node('Identity', ['pad_const'], ['pad'])
    node('Concat', ['pre', 'pad'], ['post'], axis=1)
    node('Gather', ['post', 'score_axis'], ['rpn_scores'], axis=2)
    node('TopK', ['rpn_scores', 'k'], ['rpn_sorted_scores', 'rpn_indices'], axis=1)
    node('Squeeze', ['rpn_indices'], ['rpn_index_vector'], axes=[0])
    node('Reshape', ['post', 'flat_shape'], ['post_flat'])
    node('Gather', ['post_flat', 'rpn_index_vector'], ['proposals'], axis=0)
    node('Gather', ['proposals', 'x_axis'], ['x'], axis=1)
    node('Sub', ['one', 'x'], ['one_minus_x'])
    node('Unsqueeze', ['x'], ['x_column'], axes=[1])
    node('Unsqueeze', ['one_minus_x'], ['inverse_column'], axes=[1])
    node('Concat', ['x_column', 'inverse_column'], ['logits'], axis=1)
    node('Softmax', ['logits'], ['probabilities'], axis=1)
    const('foreground_axis', 1, np.int64)
    node('Gather', ['probabilities', 'foreground_axis'], ['foreground'], axis=1)
    node('Unsqueeze', ['foreground'], ['foreground_batch'], axes=[0])
    node('TopK', ['foreground_batch', 'k'], ['final_scores', 'final_indices'], axis=1)
    node('Squeeze', ['final_indices'], ['final_index_vector'], axes=[0])
    node('Slice', ['proposals', 'starts', 'ends', 'axes'], ['boxes'])
    node('Unsqueeze', ['foreground'], ['score_column'], axes=[1])
    node('Concat', ['boxes', 'score_column'], ['candidate_dets'], axis=1)
    node('Gather', ['candidate_dets', 'final_index_vector'], ['ordered_dets'], axis=0)
    node('Unsqueeze', ['ordered_dets'], ['dets'], axes=[0])
    node('Identity', ['labels_const'], ['labels'])
    graph = h.make_graph(nodes, 'authored-zero-pad-reclassification',
                         [h.make_tensor_value_info('input', 1, [1, 3, 1, 1])],
                         [h.make_tensor_value_info('dets', 1, [1, 2, 5]),
                          h.make_tensor_value_info('labels', 7, [1, 2])], initializers)
    model = h.make_model(graph, opset_imports=[h.make_opsetid('', 11)])
    model.ir_version = 6
    onnx.checker.check_model(model)
    return model


def runtime_controls(root):
    import numpy as np
    import trace_worker as w
    passes = []
    def passed(name): passes.append(name)
    tensor = np.zeros((1, 3, 1, 1), dtype=np.float32)
    np.save(root / 'tensor.npy', tensor, allow_pickle=False)
    session = w.session(root / 'original.onnx')
    expected = session.run(['dets', 'labels'], {'input': tensor})
    assert expected[0].shape == (1, 2, 5)
    assert np.array_equal(expected[0][0, 0, :4], np.zeros(4)) and expected[0][0, 0, 4] > .5
    passed('authored_zero_proposal_receives_high_softmax_score')
    del session
    for name, value in zip(['expected_dets', 'expected_labels'], expected):
        np.save(root / (name + '.npy'), value, allow_pickle=False)
    protocol = {'worker_contract': 'append_only_graph_trace_v1', 'input_name': 'input',
                'original_outputs': ['dets', 'labels'], 'max_saved_array_bytes': w.ARRAY_CAP,
                'tensor': w.array_descriptor(tensor)}
    w.write_json(root / 'protocol.json', protocol)
    def ref(filename):
        path = root / filename
        return {'path': str(path), 'sha256': w.digest(path)}
    m = {'protocol': ref('protocol.json'), 'images': [{'id': 'authored-fixture', 'source': ref('tensor.npy')}],
         'models': {key: ref(filename) for key, filename in {
             'baseline': 'original.onnx', 'tapped': 'augmented.onnx', 'taps': 'taps.json',
             'build': 'build.json', 'expected_dets': 'expected_dets.npy',
             'expected_labels': 'expected_labels.npy'}.items()},
         'limits': {'wall_seconds': 60, 'memory_bytes': 3221225472}}
    w.write_json(root / 'manifest.json', m)
    result = w.execute(root / 'manifest.json', root / 'success')
    assert result['status'] == 'complete' and result['forward_passes_completed'] == 2
    assert result['baseline_matches_prior_bitwise'] and result['tapped_matches_baseline_bitwise']
    passed('actual_ORT_authored_baseline_and_tapped_bitwise_parity')
    arrays = {r['name']: np.load(root / 'success' / r['file'], allow_pickle=False)
              for r in result['arrays'] if r['stage'] == 'tapped'}
    roi_index = int(arrays['final_indices'][0, 0])
    original_index = int(arrays['rpn_indices'][0, roi_index])
    assert original_index == arrays['pre'].shape[1] == 1
    assert np.array_equal(arrays['post'][0, original_index], arrays['pad'][0, 0])
    passed('index_lineage_distinguishes_appended_proposal')
    original_session = w.session
    class AlteredSession:
        def __init__(self, real, mode): self.real, self.mode = real, mode
        def __getattr__(self, name): return getattr(self.real, name)
        def run(self, names, inputs):
            values = self.real.run(names, inputs)
            if self.mode == 'parity':
                values[0][0, 0, 4] = np.nextafter(values[0][0, 0, 4], np.float32(0))
            else:
                values[names.index('probabilities')][0, 0] = np.nan
            return values
    for mode, message in [('parity', 'tapped original outputs differ from baseline'),
                          ('nonfinite', 'nonfinite diagnostic output')]:
        def altered_session(path):
            real = original_session(path)
            return AlteredSession(real, mode) if path.name == 'augmented.onnx' else real
        w.session = altered_session
        try:
            try: w.execute(root / 'manifest.json', root / mode)
            except ValueError as exc: assert str(exc) == message
            else: raise AssertionError('altered tapped output accepted')
        finally:
            w.session = original_session
        failure = w.read_json(root / mode / 'failure.json')
        assert failure['forward_passes_completed'] == 2
        assert failure['baseline_matches_prior_bitwise'] and not failure['tapped_matches_baseline_bitwise']
        assert len(failure['arrays']) == len(result['arrays'])
        assert not (root / mode / 'result.json').exists()
        passed('injected_' + mode + '_refusal_retains_arrays_and_no_complete_result')
    positive, negative = np.array([0.], np.float32), np.array([-0.], np.float32)
    assert not w.same_bits(positive, negative)
    assert not w.same_bits(positive, positive.astype(np.float64))
    assert not w.same_bits(positive, positive.reshape(1, 1))
    passed('bitwise_check_rejects_signed_zero_dtype_and_shape_changes')
    altered = expected[0].copy(); altered[0, 0, 4] = np.nextafter(altered[0, 0, 4], np.float32(0))
    np.save(root / 'altered.npy', altered, allow_pickle=False)
    m['models']['expected_dets'] = ref('altered.npy')
    w.write_json(root / 'mismatch-manifest.json', m)
    try: w.execute(root / 'mismatch-manifest.json', root / 'mismatch')
    except ValueError as exc: assert str(exc) == 'original output differs from prior observation'
    else: raise AssertionError('baseline mismatch accepted')
    failure = w.read_json(root / 'mismatch' / 'failure.json')
    assert failure['forward_passes_completed'] == 1 and not (root / 'mismatch' / 'result.json').exists()
    passed('baseline_mismatch_stops_before_augmented_forward_and_retains_failure')
    for value in [np.array([object()], object), np.zeros(w.ARRAY_CAP // 4 + 1, np.float32)]:
        try: w.array_descriptor(value)
        except ValueError: pass
        else: raise AssertionError('array cap/object accepted')
    passed('object_and_individual_array_cap_refused')
    store = w.ArrayStore(root / 'success'); store.bytes = w.ARRAY_CAP - 1
    try: store.save('over', ['x'], [np.zeros(1, np.float32)])
    except ValueError: pass
    else: raise AssertionError('aggregate cap accepted')
    passed('aggregate_array_cap_refused_before_write')
    m['models']['expected_dets']['sha256'] = '0' * 64
    w.write_json(root / 'wrong-binding-manifest.json', m)
    try: w.execute(root / 'wrong-binding-manifest.json', root / 'wrong-binding')
    except ValueError: pass
    else: raise AssertionError('changed input accepted')
    failure = w.read_json(root / 'wrong-binding' / 'failure.json')
    assert failure['forward_passes_started'] == 0
    passed('changed_source_binding_stops_before_inference')
    w.write_json(root / 'runtime-controls.json', {'passed': passes, 'count': len(passes),
                 'scope': 'authored tiny model only; no empirical model/image inference'})


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--runtime')
    p.add_argument('--runtime-controls', action='store_true')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.runtime_controls:
        runtime_controls(a.output.resolve())
        return
    import onnx
    import build_taps as b
    a.output.mkdir(exist_ok=False)
    root = a.output.resolve()
    model = authored_model()
    source = model.SerializeToString(deterministic=True)
    source_hash = hashlib.sha256(source).hexdigest()
    taps = [{'name': name, 'rank': rank, 'elem_type': typ, 'role': 'authored lineage control'}
            for name, rank, typ in [('pre', 3, 1), ('pad', 3, 1), ('post', 3, 1),
                                   ('rpn_indices', 2, 7), ('probabilities', 2, 1), ('final_indices', 2, 7)]]
    tap_bytes = b.canonical(taps) + b'\n'
    built, report = b.augment(source, source_hash, taps)
    report['taps_sha256'] = hashlib.sha256(tap_bytes).hexdigest()
    for filename, data in [('original.onnx', source), ('augmented.onnx', built), ('taps.json', tap_bytes),
                           ('build.json', b.canonical(report) + b'\n')]:
        (root / filename).write_bytes(data)
    passed = ['append_only_original_proto_equality_and_ONNX_checker']
    for name, expected_hash, bad_taps in [
        ('wrong_model_digest_rejected', '0' * 64, taps),
        ('missing_tap_rejected', source_hash, [dict(taps[0], name='absent')]),
        ('duplicate_tap_rejected', source_hash, [taps[0], taps[0]]),
        ('existing_output_duplicate_rejected', source_hash, [dict(taps[0], name='dets')])]:
        try: b.augment(source, expected_hash, bad_taps)
        except ValueError: passed.append(name)
        else: raise AssertionError(name)
    changed = onnx.load_model_from_string(built)
    changed.graph.node[0].name = 'original-field-changed'
    try: b.validate_preservation(model, changed, len(taps))
    except ValueError: passed.append('changed_original_field_rejected')
    else: raise AssertionError('changed original field accepted')
    command = [a.runtime, '-B', str(Path(__file__).resolve()), '--runtime-controls', '--output', str(root)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=60)
    (root / 'runtime.stdout').write_text(result.stdout)
    (root / 'runtime.stderr').write_text(result.stderr)
    if result.returncode: raise RuntimeError('runtime controls failed; see retained stderr')
    runtime_report = json.loads((root / 'runtime-controls.json').read_text())
    passed += runtime_report['passed']
    receipt = {'status': 'passed', 'controls': passed, 'count': len(passed),
               'scope': 'authored fixtures only; no empirical source model or image loaded',
               'scripts': {name: sha(Path(__file__).parent / name)
                           for name in ['build_taps.py', 'trace_worker.py', 'qualify.py']},
               'runtime_command': command}
    (root / 'QUALIFICATION.json').write_bytes(b.canonical(receipt) + b'\n')
    print(json.dumps({'status': 'passed', 'controls': len(passed)}))


if __name__ == '__main__':
    main()
