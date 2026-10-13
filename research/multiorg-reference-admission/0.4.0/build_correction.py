#!/usr/bin/env python3
"""Graph-specific, batch-one RPN-origin validity correction, version 0.4.0.

Only the exact pinned graph is accepted. No geometry is used to identify
padding. This names a new export variant; it does not repair prior results.
"""
import argparse
import hashlib
import json
from pathlib import Path

SOURCE_SHA256 = 'fbf748e6d8b896bed9ee1eb15d5dd1409369de5e32c4746c4173aa4c10e7bebd'
PREFIX = 'reiyah_validity_v040'
PRE = '/Where_6_output_0'
INDICES = '/TopK_6_output_1'
FOREGROUND = '/Slice_14_output_0'
UNMASKED = PREFIX + '/unmasked_foreground'
VALID = PREFIX + '/valid_rpn_origin'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def mask_nodes(pre=PRE, indices=INDICES, foreground=UNMASKED, output=FOREGROUND):
    """The same seven nodes are exercised in authored ONNX/ORT controls."""
    import onnx
    h = onnx.helper
    def node(op, inputs, suffix, outputs=None, **attributes):
        return h.make_node(op, inputs, outputs or [PREFIX + '/' + suffix],
                           name=PREFIX + '/node_' + suffix, **attributes)
    axis = PREFIX + '/axis1'
    shape = PREFIX + '/pre_shape'
    count = PREFIX + '/pre_count'
    expanded = PREFIX + '/valid_expanded'
    zero = PREFIX + '/zero'
    return [
        node('Constant', [], 'axis1', value=h.make_tensor('axis', 7, [], [1])),
        node('Shape', [pre], 'pre_shape'),
        node('Gather', [shape, axis], 'pre_count', axis=0),
        node('Less', [indices, count], 'valid_rpn_origin', outputs=[VALID]),
        node('Unsqueeze', [VALID], 'valid_expanded', axes=[2]),
        node('Constant', [], 'zero', value=h.make_tensor('zero', 1, [], [0.])),
        node('Where', [expanded, foreground, zero], 'masked_foreground', outputs=[output]),
    ]


def constant(model, output):
    import onnx
    found = [n for n in model.graph.node if output in n.output]
    if len(found) != 1 or found[0].op_type != 'Constant':
        raise ValueError('required constant producer')
    attrs = {a.name: a for a in found[0].attribute}
    if set(attrs) != {'value'}:
        raise ValueError('constant encoding')
    return onnx.numpy_helper.to_array(attrs['value'].t)


def verify_preservation(original, corrected, inserted):
    """Restore exactly the declared edits, then compare the entire proto."""
    batch = corrected.graph.input[0].type.tensor_type.shape.dim[0]
    if batch.WhichOneof('value') != 'dim_value' or batch.dim_value != 1:
        raise ValueError('batch-one guard changed')
    restored = type(corrected)()
    restored.CopyFrom(corrected)
    inserted_by_name = {n.name: n.SerializeToString(deterministic=True) for n in inserted}
    retained = []
    found = set()
    for node in restored.graph.node:
        if node.name in inserted_by_name:
            if node.name in found or node.SerializeToString(deterministic=True) != inserted_by_name[node.name]:
                raise ValueError('inserted node changed')
            found.add(node.name)
        else:
            retained.append(node)
    if found != set(inserted_by_name):
        raise ValueError('inserted roster mismatch')
    del restored.graph.node[:]
    restored.graph.node.extend(retained)
    renamed = [n for n in restored.graph.node if list(n.output) == [UNMASKED]]
    if len(renamed) != 1:
        raise ValueError('renamed producer mismatch')
    renamed[0].output[0] = FOREGROUND
    # Only the input's batch dimension is restored; other input edits fail.
    restored.graph.input[0].type.tensor_type.shape.dim[0].CopyFrom(
        original.graph.input[0].type.tensor_type.shape.dim[0])
    before = original.SerializeToString(deterministic=True)
    if restored.SerializeToString(deterministic=True) != before:
        raise ValueError('undeclared original graph change')
    return digest(before)


def correct(source):
    import onnx
    if len(source) > 300_000_000 or digest(source) != SOURCE_SHA256:
        raise ValueError('unqualified source graph')
    original = onnx.load_model_from_string(source)
    if len(original.graph.input) != 1 or original.graph.input[0].name != 'input':
        raise ValueError('source input contract')
    if len(original.graph.input[0].type.tensor_type.shape.dim) != 4:
        raise ValueError('source input rank')
    if any(n.name.startswith(PREFIX) or any(x.startswith(PREFIX) for x in n.output)
           for n in original.graph.node):
        raise ValueError('namespace collision')
    if [x.name for x in original.graph.output] != ['dets', 'labels']:
        raise ValueError('source output roster')
    nms = [n for n in original.graph.node if n.name == '/NonMaxSuppression_1']
    if len(nms) != 1 or nms[0].op_type != 'NonMaxSuppression':
        raise ValueError('final NMS contract')
    threshold = constant(original, nms[0].input[4])
    if threshold.dtype.str != '<f4' or threshold.shape != (1,) or threshold.tobytes().hex() != 'cdcc4c3d':
        raise ValueError('positive score threshold changed')
    nms_cap = constant(original, nms[0].input[2])
    if nms_cap.dtype.str != '<i8' or nms_cap.shape != () or int(nms_cap) != 200:
        raise ValueError('NMS cap changed')
    producers = [n for n in original.graph.node if FOREGROUND in n.output]
    if len(producers) != 1 or producers[0].op_type != 'Slice' or list(producers[0].output) != [FOREGROUND]:
        raise ValueError('foreground producer changed')
    corrected = type(original)()
    corrected.CopyFrom(original)
    corrected.graph.input[0].type.tensor_type.shape.dim[0].Clear()
    corrected.graph.input[0].type.tensor_type.shape.dim[0].dim_value = 1
    inserted = mask_nodes()
    nodes = []
    for node in corrected.graph.node:
        if FOREGROUND in node.output:
            node.output[0] = UNMASKED
            nodes.append(node)
            nodes.extend(inserted)
        else:
            nodes.append(node)
    del corrected.graph.node[:]
    corrected.graph.node.extend(nodes)
    original_proto = verify_preservation(original, corrected, inserted)
    onnx.checker.check_model(corrected)
    data = corrected.SerializeToString(deterministic=True)
    return corrected, {
        'artifact_id': 'reiyah.multiorg.validity-preserving-export', 'version': '0.4.0',
        'lifecycle_status': 'exploratory', 'source_sha256': SOURCE_SHA256,
        'corrected_sha256': digest(data), 'corrected_bytes': len(data),
        'original_parsed_proto_sha256': original_proto, 'original_fields_otherwise_unchanged': True,
        'edits': ['input batch dimension fixed to1', 'original foreground Slice output renamed',
                  'seven origin-mask nodes inserted before all original foreground consumers'],
        'batch_support': [1], 'mask': 'TopK_6_output_1 < Shape(Where_6_output_0)[1]',
        'masked_score': 0.0, 'unchanged_NMS_score_threshold': float(threshold[0]),
        'unchanged_NMS_score_threshold_float32_hex': threshold.tobytes().hex(),
        'unchanged_NMS_per_class_cap': int(nms_cap),
        'origin_exclusion_only': 'explicit appended RPN operand; no coordinate predicate',
        'genuine_invalid_geometry': 'preserved for downstream explicit refusal',
        'checker': 'passed', 'onnx_version': onnx.__version__,
        'inserted_nodes': [n.name for n in inserted],
        'unmasked_foreground_name': UNMASKED, 'origin_mask_name': VALID,
        'scope': 'distinct graph variant; no empirical, complete-image or performance claim',
    }


def append_observations(corrected, taps):
    import onnx
    if not isinstance(taps, list) or not 1 <= len(taps) <= 64:
        raise ValueError('observation count')
    observed = type(corrected)()
    observed.CopyFrom(corrected)
    available = {x for n in observed.graph.node for x in n.output}
    seen = {x.name for x in observed.graph.output}
    for tap in taps:
        if set(tap) != {'name', 'elem_type', 'rank', 'role'}:
            raise ValueError('observation schema')
        name, typ, rank = tap['name'], tap['elem_type'], tap['rank']
        if name not in available or name in seen:
            raise ValueError('missing or duplicate observation')
        if type(typ) is not int or typ not in (1, 7, 9) or type(rank) is not int or not 1 <= rank <= 4:
            raise ValueError('observation type')
        seen.add(name)
        observed.graph.output.append(onnx.helper.make_tensor_value_info(name, typ, [None] * rank))
    restored = type(observed)()
    restored.CopyFrom(observed)
    del restored.graph.output[len(corrected.graph.output):]
    if restored.SerializeToString(deterministic=True) != corrected.SerializeToString(deterministic=True):
        raise ValueError('observation mutation')
    onnx.checker.check_model(observed)
    return observed


def main():
    p = argparse.ArgumentParser()
    for flag in ('source', 'taps', 'output'):
        p.add_argument('--' + flag, required=True, type=Path)
    a = p.parse_args()
    if a.source.stat().st_size > 300_000_000 or a.taps.stat().st_size > 65536:
        raise ValueError('input cap')
    corrected, report = correct(a.source.read_bytes())
    tap_bytes = a.taps.read_bytes()
    taps = json.loads(tap_bytes)
    observed = append_observations(corrected, taps)
    observation_bytes = observed.SerializeToString(deterministic=True)
    report.update(observation_sha256=digest(observation_bytes), observation_bytes=len(observation_bytes),
                  observation_only_outputs=taps, taps_sha256=digest(tap_bytes),
                  builder_sha256=digest(Path(__file__).read_bytes()))
    a.output.mkdir(exist_ok=False)
    (a.output / 'corrected.onnx').write_bytes(corrected.SerializeToString(deterministic=True))
    (a.output / 'observation.onnx').write_bytes(observation_bytes)
    (a.output / 'build.json').write_bytes(canonical(report) + b'\n')
    print(json.dumps({'status': 'built_not_executed', 'corrected_sha256': report['corrected_sha256'],
                      'observation_sha256': report['observation_sha256']}))


if __name__ == '__main__':
    main()
