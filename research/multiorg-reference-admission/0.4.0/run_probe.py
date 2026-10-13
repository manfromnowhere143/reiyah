#!/usr/bin/env python3
"""Frozen two-pass observation of a distinct batch-one validity variant.

No scientific comparison, geometry repair, retry, or whole-image completion.
The separate checker compares origin validity and final selection.
"""
import argparse
import gc
import hashlib
import importlib.util
import json
from pathlib import Path
import time

OWNER = Path(__file__).resolve().parent.parent
SUPPORT_PATH = Path(__file__).resolve().with_name('trace_support.py')
SUPPORT_SHA = '732264b47b54d68d5a5c8b89fedc2a4a1f8bacd42021e463424eb0e8390a12ff'
SOURCE_SHA = 'fbf748e6d8b896bed9ee1eb15d5dd1409369de5e32c4746c4173aa4c10e7bebd'
PINS = {
    'baseline': 'c9fc9b16bcb6ed4a6f45313d9712fe9671b2943362e67add989a46c964cc2799',
    'corrected': 'a26f494f548ed8410a809252b2acaae97e2efa189fcee963a5b8a09dd4c13b63',
    'build': '80272e29b269d6b42a1d68921d46d924417b649686e80dec2777cd969027691a',
    'taps': 'c08932819200b816fa9c0dca38bf32e159325aa0a9e46cb7ada071c004acb8ba',
    'prior_result': '2b7747c2119f9d79020bf6ebe82c459a408235af81ca58a240aed4803f4bb7f1',
    'support': SUPPORT_SHA,
}
BASELINE_TAPS_CANONICAL_SHA = '2b377fde0f8302da223f9f674b7fa8cdc06e5c52c38f20437ec9d1b50aa71ad5'
TENSOR = {'dtype': '<f4', 'shape': [1, 3, 800, 800],
          'c_order_data_sha256': '675a5f2aba2565e568feeb93fddc20aaed89a43a9bbeea393bf6336b84ae49d1'}
IMAGE_ID = 'exposed-first-image-tile9'
LIMITS = {'wall_seconds': 60, 'memory_bytes': 3221225472}


def load_support():
    if SUPPORT_PATH.stat().st_size > 1048576 or hashlib.sha256(SUPPORT_PATH.read_bytes()).hexdigest() != SUPPORT_SHA:
        raise ValueError('support source binding')
    spec = importlib.util.spec_from_file_location('frozen_trace_support', SUPPORT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


S = load_support()


def confined(path, exists=True):
    path = Path(path)
    if '..' in path.parts:
        raise ValueError('path traversal')
    path = path.resolve(strict=exists)
    if not path.is_relative_to(OWNER) or (exists and not path.is_file()):
        raise ValueError('path outside owner or not regular')
    return path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def validate_taps(taps):
    if not isinstance(taps, list) or not 1 <= len(taps) <= 64:
        raise ValueError('tap collection')
    seen = {'dets', 'labels'}
    for tap in taps:
        if not isinstance(tap, dict) or set(tap) != {'name', 'rank', 'elem_type', 'role'}:
            raise ValueError('tap schema')
        name, rank, typ = tap['name'], tap['rank'], tap['elem_type']
        if not isinstance(name, str) or not name or name in seen:
            raise ValueError('duplicate or invalid output')
        if type(rank) is not int or not 1 <= rank <= 4 or type(typ) is not int or typ not in (1, 7, 9):
            raise ValueError('tap type')
        seen.add(name)


def bind(manifest):
    m = S.read_json(manifest)
    if not isinstance(m, dict) or set(m) != {'protocol', 'images', 'models', 'limits'}:
        raise ValueError('manifest schema')
    if not isinstance(m['models'], dict) or set(m['models']) != set(PINS):
        raise ValueError('model reference roster')
    if not isinstance(m['images'], list) or len(m['images']) != 1:
        raise ValueError('image roster')
    if set(m['images'][0]) != {'id', 'source'} or m['images'][0]['id'] != IMAGE_ID:
        raise ValueError('image identity')
    if m['limits'] != LIMITS or any(type(m['limits'][key]) is not int for key in LIMITS):
        raise ValueError('resource contract')
    refs = {'protocol': m['protocol'], 'tensor': m['images'][0]['source'], **m['models']}
    paths = {}
    for name, ref in refs.items():
        if not isinstance(ref, dict) or set(ref) != {'path', 'sha256'}:
            raise ValueError('source reference schema')
        if not isinstance(ref['sha256'], str) or len(ref['sha256']) != 64:
            raise ValueError('source digest format')
        path = confined(ref['path'])
        if S.digest(path) != ref['sha256'] or (name in PINS and ref['sha256'] != PINS[name]):
            raise ValueError('source identity: ' + name)
        paths[name] = path
    if paths['support'] != SUPPORT_PATH.resolve() or Path(S.__file__).resolve() != paths['support']:
        raise ValueError('imported support identity')
    protocol, build, taps = (S.read_json(paths[name]) for name in ('protocol', 'build', 'taps'))
    if set(protocol) != {'worker_contract', 'tensor', 'input_name', 'original_outputs',
                         'max_saved_array_bytes', 'baseline_taps', 'corrected_taps'}:
        raise ValueError('protocol schema')
    tensor_spec = protocol['tensor']
    if (not isinstance(tensor_spec, dict) or set(tensor_spec) != set(TENSOR)
            or not isinstance(tensor_spec['shape'], list)
            or any(type(dimension) is not int for dimension in tensor_spec['shape'])):
        raise ValueError('tensor schema')
    if (protocol['worker_contract'] != 'origin_validity_observation_v040'
            or protocol['tensor'] != TENSOR or protocol['input_name'] != 'input'
            or protocol['original_outputs'] != ['dets', 'labels']
            or type(protocol['max_saved_array_bytes']) is not int
            or protocol['max_saved_array_bytes'] != S.ARRAY_CAP):
        raise ValueError('frozen protocol contract')
    validate_taps(protocol['baseline_taps']); validate_taps(protocol['corrected_taps'])
    if hashlib.sha256(canonical(protocol['baseline_taps'])).hexdigest() != BASELINE_TAPS_CANONICAL_SHA:
        raise ValueError('baseline tap roster binding')
    if protocol['corrected_taps'] != taps or taps[:len(protocol['baseline_taps'])] != protocol['baseline_taps']:
        raise ValueError('corrected tap roster binding')
    if (build.get('artifact_id') != 'reiyah.multiorg.validity-preserving-export'
            or build.get('version') != '0.4.0' or build.get('source_sha256') != SOURCE_SHA
            or build.get('observation_sha256') != PINS['corrected']
            or build.get('taps_sha256') != PINS['taps'] or build.get('observation_only_outputs') != taps
            or build.get('checker') != 'passed' or build.get('batch_support') != [1]
            or build.get('original_fields_otherwise_unchanged') is not True):
        raise ValueError('correction build contract')
    return refs, paths, protocol


def prior_arrays(path, names):
    import numpy as np
    prior = S.read_json(path)
    if (prior.get('status') != 'complete' or prior.get('stage') != 'complete'
            or prior.get('forward_passes_completed') != 2
            or prior.get('baseline_matches_prior_bitwise') is not True
            or prior.get('tapped_matches_baseline_bitwise') is not True):
        raise ValueError('prior capture incomplete')
    rows = prior.get('arrays')
    if not isinstance(rows, list) or not 1 <= len(rows) <= 68:
        raise ValueError('prior array roster')
    arrays, pins, files, named = {}, [], set(), set()
    total = 0
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'name', 'stage', 'file', 'sha256', 'bytes',
                                                    'dtype', 'shape', 'c_order_data_sha256'}:
            raise ValueError('prior array schema')
        filename = row['file']
        if not isinstance(filename, str) or Path(filename).name != filename or not filename.endswith('.npy'):
            raise ValueError('prior array path')
        identity = (row['stage'], row['name'])
        if filename in files or identity in named or row['stage'] not in ('baseline', 'tapped'):
            raise ValueError('prior duplicate or unexpected array')
        files.add(filename); named.add(identity)
        file = confined(path.parent / filename)
        if type(row['bytes']) is not int or row['bytes'] != file.stat().st_size:
            raise ValueError('prior file length')
        total += row['bytes']
        if total > S.ARRAY_CAP or S.digest(file, S.ARRAY_CAP) != row['sha256']:
            raise ValueError('prior array digest or byte cap')
        array = S.load_array(file)
        desc = S.array_descriptor(array)
        if any(desc[key] != row[key] for key in desc):
            raise ValueError('prior array content identity')
        if array.dtype.kind == 'f' and not np.isfinite(array).all():
            raise ValueError('prior nonfinite output')
        pins.append((file, row['sha256']))
        if row['stage'] == 'tapped': arrays[row['name']] = array
    if list(arrays) != names or {name for stage, name in named if stage == 'baseline'} != {'dets', 'labels'}:
        raise ValueError('prior output roster mismatch')
    return arrays, pins


def check_session(session, names, corrected):
    if session.get_providers() != ['CPUExecutionProvider']:
        raise ValueError('CPU provider contract')
    if [x.name for x in session.get_outputs()] != names:
        raise ValueError('session output roster')
    inputs = session.get_inputs()
    if len(inputs) != 1 or inputs[0].name != 'input' or inputs[0].type != 'tensor(float)':
        raise ValueError('session input contract')
    if len(inputs[0].shape) != 4 or inputs[0].shape[1] != 3:
        raise ValueError('session input rank/channel')
    if corrected and (type(inputs[0].shape[0]) is not int or inputs[0].shape[0] != 1):
        raise ValueError('corrected batch-one guard')


def check_values(values, taps):
    import numpy as np
    specs = [{'elem_type': 1, 'rank': 3}, {'elem_type': 7, 'rank': 2}] + taps
    if len(values) != len(specs):
        raise ValueError('output count')
    for array, spec in zip(values, specs):
        if array.dtype.str != {1: '<f4', 7: '<i8', 9: '|b1'}[spec['elem_type']] or array.ndim != spec['rank']:
            raise ValueError('output dtype or rank')
        if array.dtype.kind == 'f' and not np.isfinite(array).all():
            raise ValueError('nonfinite observed output')


def execute(manifest_path, output):
    import numpy as np
    import onnxruntime as ort
    manifest_path, output = confined(manifest_path), confined(output, exists=False)
    output.mkdir(exist_ok=False)
    store, start = S.ArrayStore(output), time.monotonic()
    record = {'artifact_id': 'reiyah.multiorg.validity-observation', 'version': '0.4.0',
              'status': 'failed', 'stage': 'bindings', 'forward_passes_started': 0,
              'forward_passes_completed': 0, 'baseline_matches_prior_bitwise': False,
              'runner_sha256': S.digest(Path(__file__), 1048576),
              'manifest_sha256': S.digest(manifest_path, 1048576), 'image_id': IMAGE_ID,
              'numpy_version': np.__version__, 'onnxruntime_version': ort.__version__,
              'arrays': store.records,
              'scope': 'capture only; separate correction comparator required; no complete image or pair'}
    failure = None
    try:
        refs, paths, protocol = bind(manifest_path)
        record['source_bindings'] = refs
        names = {stage: ['dets', 'labels'] + [t['name'] for t in protocol[key]]
                 for stage, key in [('baseline', 'baseline_taps'), ('corrected', 'corrected_taps')]}
        prior, array_pins = prior_arrays(paths['prior_result'], names['baseline'])
        tensor = S.load_array(paths['tensor'])
        if S.array_descriptor(tensor) != TENSOR or not np.isfinite(tensor).all():
            raise ValueError('saved tensor identity/domain')
        for stage in ['baseline', 'corrected']:
            record['stage'] = stage + '_session'
            model = S.session(paths[stage])
            check_session(model, names[stage], stage == 'corrected')
            record[stage + '_providers'] = model.get_providers()
            record['stage'] = stage + '_forward'
            record['forward_passes_started'] += 1
            values = model.run(names[stage], {'input': tensor})
            record['forward_passes_completed'] += 1
            store.save(stage, names[stage], values)
            check_values(values, protocol[stage + '_taps'])
            if stage == 'baseline':
                if not all(S.same_bits(value, prior[name]) for name, value in zip(names[stage], values)):
                    raise ValueError('baseline differs from prior capture')
                record['baseline_matches_prior_bitwise'] = True
            del model, values
            gc.collect()
        for key, ref in refs.items():
            if S.digest(paths[key]) != ref['sha256']:
                raise ValueError('source changed during execution: ' + key)
        for file, sha in array_pins:
            if S.digest(file, S.ARRAY_CAP) != sha:
                raise ValueError('prior array changed during execution')
        if S.digest(manifest_path, 1048576) != record['manifest_sha256']:
            raise ValueError('manifest changed during execution')
        record.update(status='complete', stage='complete')
    except BaseException as exc:
        failure = exc
        record['error'] = type(exc).__name__ + ': ' + str(exc)
        raise
    finally:
        record.update(saved_array_bytes=store.bytes, wall_seconds=time.monotonic() - start)
        try:
            S.write_json(output / ('result.json' if record['status'] == 'complete' else 'failure.json'), record)
        except Exception:
            if failure is None: raise
    return record


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--worker', action='store_true', required=True)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = execute(a.manifest, a.output)
    print(json.dumps({'status': result['status'], 'forward_passes_completed': result['forward_passes_completed'],
                      'saved_array_bytes': result['saved_array_bytes']}))


if __name__ == '__main__':
    main()
