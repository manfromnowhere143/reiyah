#!/usr/bin/env python3
"""Two-pass diagnostic only. Original once, appended-output graph once.

Execution requires the separately frozen supervisor/manifest. It never repairs,
filters, projects, or exports scientific detections. Saved intermediate values
are observations, not an independently recomputed neural-network execution.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import time

ARRAY_CAP = 67_108_864
MODEL_CAP = 300_000_000


def digest(path, cap=MODEL_CAP):
    if path.stat().st_size > cap:
        raise ValueError('bound input byte cap')
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON property')
            result[key] = value
        return result
    if path.stat().st_size > 1048576:
        raise ValueError('JSON cap')
    return json.loads(path.read_text(), object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def write_json(path, value):
    data = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode() + b'\n'
    if len(data) > 1048576:
        raise ValueError('JSON output cap')
    with path.open('xb') as f:
        f.write(data)


def array_descriptor(array):
    import numpy as np
    if not isinstance(array, np.ndarray) or array.dtype.hasobject or array.dtype.kind not in 'biuf':
        raise ValueError('numeric non-object array required')
    if array.nbytes > ARRAY_CAP:
        raise ValueError('array byte cap')
    return {'dtype': array.dtype.str, 'shape': list(array.shape),
            'c_order_data_sha256': hashlib.sha256(array.tobytes(order='C')).hexdigest()}


def same_bits(left, right):
    return (left.dtype.str == right.dtype.str and left.shape == right.shape
            and left.tobytes(order='C') == right.tobytes(order='C'))


def load_array(path):
    import numpy as np
    if path.stat().st_size > ARRAY_CAP:
        raise ValueError('NPY byte cap')
    # No pickle; mmap prevents a forged enormous shape from allocating its payload.
    array = np.load(path, allow_pickle=False, mmap_mode='r')
    array_descriptor(array)
    return array


class ArrayStore:
    def __init__(self, output):
        self.output, self.bytes, self.records = output, 0, []

    def save(self, stage, names, arrays):
        import numpy as np
        if len(names) != len(arrays) or len(names) != len(set(names)):
            raise ValueError('output collection mismatch')
        descriptors = [array_descriptor(array) for array in arrays]
        # NPY headers are small here; use a conservative 4096-byte allowance.
        if self.bytes + sum(array.nbytes + 4096 for array in arrays) > ARRAY_CAP:
            raise ValueError('aggregate saved-array byte cap')
        for name, array, desc in zip(names, arrays, descriptors):
            filename = '%s-%02d.npy' % (stage, len(self.records))
            path = self.output / filename
            with path.open('xb') as f:
                np.save(f, array, allow_pickle=False)
            size = path.stat().st_size
            self.bytes += size
            self.records.append(dict(desc, name=name, stage=stage, file=filename,
                                     bytes=size, sha256=digest(path, ARRAY_CAP)))


def session(path):
    import onnxruntime as ort
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    # Default optimization setting matches the unchanged original worker.
    return ort.InferenceSession(path.read_bytes(), sess_options=options,
                                providers=['CPUExecutionProvider'])


def execute(manifest_path, output):
    import numpy as np
    import onnxruntime as ort
    start = time.monotonic()
    output.mkdir(exist_ok=False)
    store = ArrayStore(output)
    record = {'artifact_id': 'reiyah.multiorg.graph-observation', 'version': '0.1.0',
              'status': 'failed', 'scope': 'one saved tensor; diagnostic only; no complete image or pair',
              'stage': 'bindings', 'forward_passes_started': 0, 'forward_passes_completed': 0,
              'baseline_matches_prior_bitwise': False, 'tapped_matches_baseline_bitwise': False,
              'runner_sha256': digest(Path(__file__), 1048576), 'arrays': store.records,
              'numpy_version': np.__version__, 'onnxruntime_version': ort.__version__}
    try:
        m = read_json(manifest_path)
        if set(m) != {'protocol', 'images', 'models', 'limits'} or len(m['images']) != 1:
            raise ValueError('manifest schema')
        required = {'baseline', 'tapped', 'taps', 'build', 'expected_dets', 'expected_labels'}
        if set(m['models']) != required or set(m['images'][0]) != {'id', 'source'}:
            raise ValueError('source schema')
        if m['limits'] != {'wall_seconds': 60, 'memory_bytes': 3221225472}:
            raise ValueError('execution limit contract')
        refs = {'protocol': m['protocol'], 'tensor': m['images'][0]['source'], **m['models']}
        paths = {}
        for key, ref in refs.items():
            if not isinstance(ref, dict) or set(ref) != {'path', 'sha256'}:
                raise ValueError('binding schema')
            path = Path(ref['path']).resolve(strict=True)
            if not path.is_file() or digest(path) != ref['sha256']:
                raise ValueError('input identity: ' + key)
            paths[key] = path
        record['manifest_sha256'] = digest(manifest_path, 1048576)
        record['source_bindings'] = refs
        record['image_id'] = m['images'][0]['id']
        protocol, build, taps = (read_json(paths[k]) for k in ('protocol', 'build', 'taps'))
        if protocol.get('worker_contract') != 'append_only_graph_trace_v1':
            raise ValueError('protocol contract')
        if protocol.get('original_outputs') != ['dets', 'labels'] or protocol.get('input_name') != 'input':
            raise ValueError('input/output contract')
        if protocol.get('max_saved_array_bytes') != ARRAY_CAP:
            raise ValueError('array limit contract')
        if (build.get('source_sha256') != refs['baseline']['sha256']
                or build.get('augmented_sha256') != refs['tapped']['sha256']
                or build.get('taps_sha256') != refs['taps']['sha256']
                or build.get('original_outputs') != ['dets', 'labels']
                or build.get('appended_outputs') != taps
                or build.get('original_fields_unchanged') is not True
                or build.get('checker') != 'passed'):
            raise ValueError('append-only build binding')
        names = ['dets', 'labels'] + [tap['name'] for tap in taps]
        if len(names) != len(set(names)) or len(taps) > 64:
            raise ValueError('tap roster')
        tensor = load_array(paths['tensor'])
        if array_descriptor(tensor) != protocol['tensor']:
            raise ValueError('tensor content identity')
        if tensor.dtype.str != '<f4' or tensor.ndim != 4 or not np.isfinite(tensor).all():
            raise ValueError('tensor domain')
        expected = [load_array(paths['expected_dets']), load_array(paths['expected_labels'])]
        original = session(paths['baseline'])
        record['baseline_providers'] = original.get_providers()
        if record['baseline_providers'] != ['CPUExecutionProvider']:
            raise ValueError('original provider mismatch')
        if [x.name for x in original.get_outputs()] != ['dets', 'labels']:
            raise ValueError('original output roster')
        if [x.name for x in original.get_inputs()] != ['input']:
            raise ValueError('original input roster')
        record['stage'] = 'baseline_forward'
        record['forward_passes_started'] += 1
        baseline = original.run(['dets', 'labels'], {'input': tensor})
        record['forward_passes_completed'] += 1
        store.save('baseline', ['dets', 'labels'], baseline)
        if any(array.dtype.kind == 'f' and not np.isfinite(array).all() for array in baseline):
            raise ValueError('nonfinite baseline output')
        if not all(same_bits(x, y) for x, y in zip(baseline, expected)):
            raise ValueError('original output differs from prior observation')
        record['baseline_matches_prior_bitwise'] = True
        del original
        gc.collect()
        augmented = session(paths['tapped'])
        record['tapped_providers'] = augmented.get_providers()
        if record['tapped_providers'] != ['CPUExecutionProvider']:
            raise ValueError('tapped provider mismatch')
        if [x.name for x in augmented.get_outputs()] != names:
            raise ValueError('tapped output roster')
        if [x.name for x in augmented.get_inputs()] != ['input']:
            raise ValueError('tapped input roster')
        record['stage'] = 'tapped_forward'
        record['forward_passes_started'] += 1
        tapped = augmented.run(names, {'input': tensor})
        record['forward_passes_completed'] += 1
        store.save('tapped', names, tapped)
        if any(array.dtype.kind == 'f' and not np.isfinite(array).all() for array in tapped):
            raise ValueError('nonfinite diagnostic output')
        for tap, array in zip(taps, tapped[2:]):
            expected_dtype = '<f4' if tap['elem_type'] == 1 else '<i8'
            if array.dtype.str != expected_dtype or array.ndim != tap['rank']:
                raise ValueError('tap type or rank mismatch: ' + tap['name'])
        if not all(same_bits(x, y) for x, y in zip(baseline, tapped[:2])):
            raise ValueError('tapped original outputs differ from baseline')
        record['tapped_matches_baseline_bitwise'] = True
        for key, ref in refs.items():
            if digest(paths[key]) != ref['sha256']:
                raise ValueError('input changed during execution: ' + key)
        record.update(status='complete', stage='complete')
    except BaseException as exc:
        record.update(error=type(exc).__name__ + ': ' + str(exc))
        raise
    finally:
        record.update(saved_array_bytes=store.bytes, wall_seconds=time.monotonic() - start)
        write_json(output / ('result.json' if record['status'] == 'complete' else 'failure.json'), record)
    return record


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--worker', action='store_true', required=True)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = execute(a.manifest, a.output)
    print(json.dumps({'status': result['status'], 'forward_passes': result['forward_passes_completed'],
                      'saved_array_bytes': result['saved_array_bytes']}))


if __name__ == '__main__':
    main()
