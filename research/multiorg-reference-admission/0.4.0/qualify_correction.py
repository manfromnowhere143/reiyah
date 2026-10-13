#!/usr/bin/env python3
"""Small authored ONNX controls using the correction's exact mask helper.

No empirical model or image is executed. Parser and ORT Python are separate.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def authored_model():
    import onnx
    import build_correction as b
    h = onnx.helper
    nodes = b.mask_nodes('pre', 'origin_indices', 'unmasked', 'masked')
    def node(op, inputs, outputs, **attrs): nodes.append(h.make_node(op, inputs, outputs, **attrs))
    def const(name, typ, dims, values):
        node('Constant', [], [name], value=h.make_tensor(name, typ, dims, values))
    const('axis1', 7, [], [1]); const('cap2', 7, [], [2])
    const('nms_max', 7, [], [200]); const('iou', 1, [], [.5]); const('threshold', 1, [], [.05])
    node('Shape', ['origin_indices'], ['indices_shape'])
    node('Gather', ['indices_shape', 'axis1'], ['available'], axis=0)
    node('Less', ['available', 'cap2'], ['below_cap'])
    node('Where', ['below_cap', 'available', 'cap2'], ['k_scalar'])
    node('Unsqueeze', ['k_scalar'], ['k'], axes=[0])
    node('Squeeze', ['masked'], ['scores'], axes=[2])
    node('TopK', ['scores', 'k'], ['top_scores', 'top_indices'], axis=1)
    node('Squeeze', ['boxes'], ['boxes_flat'], axes=[0])
    node('Squeeze', ['top_indices'], ['index_flat'], axes=[0])
    node('Gather', ['boxes_flat', 'index_flat'], ['top_boxes_flat'], axis=0)
    node('Unsqueeze', ['top_boxes_flat'], ['top_boxes'], axes=[0])
    node('Unsqueeze', ['top_scores'], ['nms_scores'], axes=[1])
    node('NonMaxSuppression', ['top_boxes', 'nms_scores', 'nms_max', 'iou', 'threshold'], ['selected'])
    inputs = [h.make_tensor_value_info('pre', 1, [1, None, 5]),
              h.make_tensor_value_info('origin_indices', 7, [1, None]),
              h.make_tensor_value_info('unmasked', 1, [1, None, 1]),
              h.make_tensor_value_info('boxes', 1, [1, None, 4])]
    outputs = [h.make_tensor_value_info(b.VALID, 9, [1, None]),
               h.make_tensor_value_info('masked', 1, [1, None, 1]),
               h.make_tensor_value_info('top_indices', 7, [1, None]),
               h.make_tensor_value_info('selected', 7, [None, 3])]
    model = h.make_model(h.make_graph(nodes, 'authored-origin-mask-before-selection', inputs, outputs),
                        opset_imports=[h.make_opsetid('', 11)])
    model.ir_version = 6
    onnx.checker.check_model(model)
    return model


def runtime_controls(root):
    import numpy as np
    import onnxruntime as ort
    import build_correction as b
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2; options.inter_op_num_threads = 1
    options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    session = ort.InferenceSession(str(root / 'authored.onnx'), options, providers=['CPUExecutionProvider'])
    assert session.get_providers() == ['CPUExecutionProvider']
    passed, cases = [], []
    def run(name, count, order, scores, boxes, expected_valid, expected_kept):
        inputs = {'pre': np.zeros((1, count, 5), np.float32),
                  'origin_indices': np.array([order], np.int64),
                  'unmasked': np.array(scores, np.float32).reshape(1, -1, 1),
                  'boxes': np.array([boxes], np.float32)}
        valid, masked, top_indices, selected = session.run(None, inputs)
        assert valid.dtype == np.bool_ and valid.tolist() == [expected_valid]
        original = inputs['unmasked'][0, :, 0]
        assert masked[0, :, 0].tobytes() == np.where(valid[0], original, np.float32(0)).tobytes()
        kept = [int(top_indices[batch, idx]) for batch, cls, idx in selected]
        assert kept == expected_kept, (name, kept, expected_kept)
        cases.append({'name': name, 'pre_count': count, 'origin_indices': order,
                      'original_scores': original.tolist(), 'mask': valid.tolist(),
                      'masked_scores': masked.tolist(), 'selected_ROI_indices': kept})
        passed.append(name)
        return valid, masked, kept
    ordinary = [[1, 1, 2, 2], [4, 4, 5, 5], [0, 0, 0, 0]]
    run('cap_two_recovers_both_genuine_slots', 2, [0, 1, 2], [.9, .8, .99], ordinary,
        [True, True, False], [0, 1])
    # Merely dropping the padded row after original cap2 would retain only ROI0.
    assert [x for x in sorted(range(3), key=lambda x: -[.9, .8, .99][x])[:2] if x < 2] == [0]
    passed.append('post_cap_deletion_counterexample_retained')
    run('empty_genuine_population_masks_only_placeholder', 0, [0], [.99], [[0, 0, 0, 0]],
        [False], [])
    valid, masked, kept = run('genuine_equal_zero_geometry_remains_origin_valid', 1, [0, 1], [.8, .99],
                             [[0, 0, 0, 0], [0, 0, 0, 0]], [True, False], [0])
    assert masked[0, 0, 0] > .5 and kept == [0]
    # Its later positive-extent obligation still fails; the builder has not repaired it.
    genuine_box = [0, 0, 0, 0]
    assert not (genuine_box[2] > genuine_box[0] and genuine_box[3] > genuine_box[1])
    passed.append('genuine_high_invalid_box_remains_available_for_explicit_refusal')
    run('reordered_placeholder_is_identified_by_index_not_position', 2, [2, 1, 0], [.99, .8, .9],
        [ordinary[2], ordinary[1], ordinary[0]], [False, True, True], [2, 1])
    run('equal_genuine_scores_preserve_lower_ROI_index_order', 2, [0, 2, 1], [.8, .99, .8],
        [ordinary[0], ordinary[2], ordinary[1]], [True, False, True], [0, 2])
    run('low_genuine_zero_score_keeps_validity_without_forced_detection', 1, [0, 1], [0, .99],
        [[0, 0, 0, 0], [0, 0, 0, 0]], [True, False], [])
    # Scores just above the existing threshold remain byte-identical when valid.
    above = float(np.nextafter(np.float32(.05), np.float32(1)))
    run('positive_threshold_boundary_preserved', 1, [0, 1], [above, .99],
        [ordinary[0], ordinary[2]], [True, False], [0])
    run('exact_existing_threshold_equality_remains_excluded_by_NMS', 1, [0, 1], [.05, .99],
        [ordinary[0], ordinary[2]], [True, False], [])
    run('IoU_exactly_half_retains_both', 2, [0, 1, 2], [.9, .8, .99],
        [[0, 0, 2, 1], [0, 0, 1, 1], [0, 0, 0, 0]], [True, True, False], [0, 1])
    next_edge = float(np.nextafter(np.float32(1), np.float32(2)))
    run('IoU_above_half_after_one_float32_edge_step_suppresses', 2, [0, 1, 2], [.9, .8, .99],
        [[0, 0, 2, 1], [0, 0, next_edge, 1], [0, 0, 0, 0]], [True, True, False], [0])
    run('identical_tied_genuine_candidates_keep_lower_input_index', 2, [0, 1, 2], [.8, .8, .99],
        [[0, 0, 1, 1], [0, 0, 1, 1], [0, 0, 0, 0]], [True, True, False], [0])
    batch2 = {'pre': np.zeros((2, 1, 5), np.float32),
              'origin_indices': np.zeros((2, 1), np.int64),
              'unmasked': np.ones((2, 1, 1), np.float32),
              'boxes': np.zeros((2, 1, 4), np.float32)}
    try: session.run(None, batch2)
    except Exception as exc:
        assert 'Got: 2 Expected: 1' in str(exc)
    else: raise AssertionError('unsupported batch2 accepted')
    passed.append('batch2_rejected_by_ONNX_runtime_input_contract')
    report = {'status': 'passed', 'controls': passed, 'count': len(passed), 'cases': cases,
              'runtime_version': ort.__version__, 'numpy_version': np.__version__,
              'scope': 'authored ONNX graph only; empirical model and image never loaded'}
    (root / 'runtime-controls.json').write_text(json.dumps(report, indent=2) + '\n')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--runtime')
    p.add_argument('--source', type=Path, help='optional exact source for static preservation controls only')
    p.add_argument('--runtime-controls', action='store_true')
    a = p.parse_args()
    if a.runtime_controls:
        runtime_controls(a.output.resolve()); return
    import build_correction as b
    a.output.mkdir(exist_ok=False)
    root = a.output.resolve()
    model = authored_model()
    (root / 'authored.onnx').write_bytes(model.SerializeToString(deterministic=True))
    passed = []
    try: b.correct(model.SerializeToString())
    except ValueError as exc: assert str(exc) == 'unqualified source graph'
    else: raise AssertionError('unbound model accepted')
    passed.append('different_source_graph_rejected')
    command = [a.runtime, '-B', str(Path(__file__).resolve()), '--runtime-controls', '--output', str(root)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=60)
    (root / 'runtime.stdout').write_text(result.stdout)
    (root / 'runtime.stderr').write_text(result.stderr)
    if result.returncode: raise RuntimeError('authored runtime controls failed; see retained stderr')
    runtime = json.loads((root / 'runtime-controls.json').read_text())
    passed += runtime['controls']
    if a.source:
        import onnx
        if a.source.stat().st_size > 300_000_000:
            raise ValueError('static source byte cap')
        source_bytes = a.source.read_bytes()
        original = onnx.load_model_from_string(source_bytes)
        corrected, static_report = b.correct(source_bytes)
        inserted = b.mask_nodes()
        assert static_report['original_fields_otherwise_unchanged']
        passed.append('exact_source_static_correction_and_preservation_pass')
        saved_name = corrected.graph.node[0].name
        corrected.graph.node[0].name = 'authored_undeclared_change'
        try: b.verify_preservation(original, corrected, inserted)
        except ValueError: passed.append('undeclared_original_node_change_rejected')
        else: raise AssertionError('undeclared change accepted')
        corrected.graph.node[0].name = saved_name
        corrected.graph.input[0].type.tensor_type.shape.dim[0].dim_value = 2
        try: b.verify_preservation(original, corrected, inserted)
        except ValueError: passed.append('altered_batch_guard_rejected')
        else: raise AssertionError('batch guard change accepted')
        corrected.graph.input[0].type.tensor_type.shape.dim[0].dim_value = 1
        for name, taps in [('missing_observation_rejected', [{'name': 'absent', 'rank': 2, 'elem_type': 1, 'role': 'control'}]),
                           ('duplicate_original_output_rejected', [{'name': 'dets', 'rank': 3, 'elem_type': 1, 'role': 'control'}])]:
            try: b.append_observations(corrected, taps)
            except ValueError: passed.append(name)
            else: raise AssertionError(name)
    report = {'status': 'passed', 'controls': passed, 'count': len(passed),
              'scripts': {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                          for name in ['build_correction.py', 'qualify_correction.py']},
              'runtime_command': command, 'empirical_forward_passes': 0}
    if a.source:
        report['static_source_sha256'] = hashlib.sha256(source_bytes).hexdigest()
    (root / 'QUALIFICATION.json').write_bytes(b.canonical(report) + b'\n')
    print(json.dumps({'status': 'passed', 'controls': len(passed)}))


if __name__ == '__main__':
    main()
