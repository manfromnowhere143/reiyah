#!/usr/bin/env python3
"""Append observation outputs only; require unchanged original ModelProto.

Run with the separately qualified ONNX parser environment, not the empirical
ORT environment. This does not execute a model or establish output parity.
"""
import argparse
import hashlib
import json
from pathlib import Path

MAX_MODEL_BYTES = 300_000_000
MAX_TAPS = 64


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def validate_preservation(original, augmented, added):
    """Compare every original proto field after removing only appended outputs."""
    if len(augmented.graph.output) != len(original.graph.output) + added:
        raise ValueError('output count changed')
    restored = type(augmented)()
    restored.CopyFrom(augmented)
    del restored.graph.output[len(original.graph.output):]
    before = original.SerializeToString(deterministic=True)
    after = restored.SerializeToString(deterministic=True)
    if before != after:
        raise ValueError('original ModelProto changed')
    return sha(before)


def augment(source, expected_sha256, taps):
    import onnx
    if len(source) > MAX_MODEL_BYTES or sha(source) != expected_sha256:
        raise ValueError('model source binding')
    if not isinstance(taps, list) or not 1 <= len(taps) <= MAX_TAPS:
        raise ValueError('tap count')
    original = onnx.load_model_from_string(source)
    if any(t.data_location == onnx.TensorProto.EXTERNAL for t in original.graph.initializer):
        raise ValueError('external initializer not admitted')
    available = {name for node in original.graph.node for name in node.output}
    seen = {item.name for item in original.graph.output}
    augmented = type(original)()
    augmented.CopyFrom(original)
    for tap in taps:
        if not isinstance(tap, dict) or set(tap) != {'name', 'elem_type', 'rank', 'role'}:
            raise ValueError('tap schema')
        name, elem_type, rank = tap['name'], tap['elem_type'], tap['rank']
        if not isinstance(name, str) or name not in available:
            raise ValueError('missing tap output')
        if name in seen:
            raise ValueError('duplicate tap output')
        if type(elem_type) is not int or elem_type not in (1, 7):
            raise ValueError('tap element type')
        if type(rank) is not int or not 1 <= rank <= 4:
            raise ValueError('tap rank')
        if not isinstance(tap['role'], str) or not tap['role']:
            raise ValueError('tap role')
        seen.add(name)
        augmented.graph.output.append(onnx.helper.make_tensor_value_info(name, elem_type, [None] * rank))
    original_proto_sha = validate_preservation(original, augmented, len(taps))
    onnx.checker.check_model(augmented)
    result = augmented.SerializeToString(deterministic=True)
    return result, {
        'artifact_id': 'reiyah.multiorg.append-only-graph', 'version': '0.1.0',
        'source_sha256': sha(source), 'source_bytes': len(source),
        'augmented_sha256': sha(result), 'augmented_bytes': len(result),
        'original_parsed_proto_sha256': original_proto_sha,
        'original_fields_unchanged': True, 'checker': 'passed',
        'original_outputs': [item.name for item in original.graph.output],
        'appended_outputs': taps, 'nodes': len(original.graph.node),
        'initializers': len(original.graph.initializer), 'onnx_version': onnx.__version__,
        'scope': 'parsed protobuf equality after removing appended outputs; no inference or parity claim',
    }


def main():
    p = argparse.ArgumentParser()
    for flag in ('source', 'source-sha256', 'taps', 'output'):
        p.add_argument('--' + flag, required=True)
    a = p.parse_args()
    source_path, taps_path, output = Path(a.source), Path(a.taps), Path(a.output)
    if source_path.stat().st_size > MAX_MODEL_BYTES or taps_path.stat().st_size > 65536:
        raise ValueError('input cap')
    output.mkdir(exist_ok=False)
    taps_bytes = taps_path.read_bytes()
    built, report = augment(source_path.read_bytes(), a.source_sha256, json.loads(taps_bytes))
    report.update(taps_sha256=sha(taps_bytes), builder_sha256=sha(Path(__file__).read_bytes()))
    with (output / 'tapped.onnx').open('xb') as f:
        f.write(built)
    with (output / 'build.json').open('xb') as f:
        f.write(canonical(report) + b'\n')
    print(json.dumps({'status': 'built_not_executed', 'sha256': report['augmented_sha256'], 'taps': len(report['appended_outputs'])}))


if __name__ == '__main__':
    main()
