#!/usr/bin/env python3
"""Failure-only diagnostics around an exact-bound, unchanged numerical worker.

Diagnostic reconstruction is never supplied to the numerical worker. Raw arrays
remain private; .npy storage always forbids pickle. This is not model evaluation.
"""
from __future__ import annotations
import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import sys
import types
import numpy as np

WORKER_SHA256 = '9a708bf6a22e9350980e0d08d0e90c2c56f7b9cc4a73b7fd55f22c9ef3f33e0c'
OWNER = Path(__file__).resolve().parents[1]
MAX_ARRAY_BYTES = 16 * 1024 * 1024
MAX_CAPTURE_BYTES = 32 * 1024 * 1024
MAX_ARRAYS = 24
MAX_JSON_BYTES = 1024 * 1024
MAX_ROW_SUMMARIES = 128
MAX_ANALYSIS_ROWS = 200000


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_worker(path=None):
    path = Path(path or Path(__file__).with_name('run_pair.py')).resolve(strict=True)
    data = path.read_bytes()
    if sha(data) != WORKER_SHA256:
        raise ValueError('original numerical worker hash mismatch')
    module = types.ModuleType('_reiyah_bound_numerical_worker')
    module.__file__ = str(path)
    # Compile exactly the bytes just hashed, without import caches or rereading.
    exec(compile(data, str(path), 'exec'), module.__dict__)
    return module


def array_identity(value):
    if not isinstance(value, np.ndarray):
        return {'container_type': type(value).__name__, 'exact_ndarray': False}
    result = {'exact_ndarray': True, 'shape': list(value.shape),
              'dtype': value.dtype.str, 'nbytes': int(value.nbytes)}
    if value.dtype.hasobject or value.nbytes > MAX_ARRAY_BYTES:
        result['data_hash_status'] = 'refused_object_dtype_or_size_cap'
    else:
        result['c_order_data_sha256'] = sha(value.tobytes(order='C'))
    return result


def context_from_frame(frame, worker, row, column, side):
    result = {'execute_frame_verified': False, 'rescaled_row': row,
              'rescaled_column': column, 'resized_side': side}
    if frame is None or frame.f_code is not worker.execute.__code__ or frame.f_globals is not worker.__dict__:
        return result
    local = frame.f_locals
    image = local.get('image', {})
    model = local.get('model')
    manifest = local.get('m', {})
    result.update({'execute_frame_verified': True, 'model': model,
                   'image_id': image.get('id'), 'image_source': image.get('source'),
                   'model_source': manifest.get('models', {}).get(model),
                   'protocol_source': manifest.get('protocol'),
                   'ordinal': local.get('ordinal'),
                   'image_shape_hw': local.get('shape'),
                   'rescaled_shape_hw': local.get('resized_shape'),
                   'tile_count_expected': len(local.get('roster', [])),
                   'manifest_sha256': local.get('manifest_sha256'),
                   'tensor': array_identity(local.get('tensor'))})
    return result


def number_text(value):
    # NPY is authoritative; these strings are readable diagnostic summaries.
    return {'repr': str(value), 'float_hex': float(value).hex()}


class Capture:
    def __init__(self, directory, worker):
        self.directory = Path(directory)
        self.worker = worker
        self.attempted = False

    def save(self, exc, outputs, context, decoder):
        if self.attempted:
            return
        self.attempted = True
        parent = self.directory.parent.resolve(strict=True)
        if not parent.is_relative_to(OWNER) or self.directory.exists():
            raise ValueError('diagnostic directory must be new under owner')
        self.directory.mkdir(mode=0o700)
        tb = exc.__traceback__
        frame = None
        while tb is not None:
            if tb.tb_frame.f_code is decoder.__code__ and tb.tb_frame.f_globals is self.worker.__dict__:
                frame = tb.tb_frame
                break
            tb = tb.tb_next
        locals_ = dict(frame.f_locals) if frame is not None else {}
        report = {'artifact_id': 'reiyah.multiorg.output-diagnostic', 'version': '0.1.0',
                  'status': 'original_decoder_exception_preserved',
                  'original_worker_sha256': WORKER_SHA256,
                  'wrapper_sha256': sha(Path(__file__).read_bytes()),
                  'exception': {'type': type(exc).__name__, 'message': str(exc)[:2048]},
                  'decoder_frame_verified': frame is not None, 'context': context,
                  'limits': {'array_bytes': MAX_ARRAY_BYTES, 'capture_bytes': MAX_CAPTURE_BYTES,
                             'arrays': MAX_ARRAYS, 'row_summaries': MAX_ROW_SUMMARIES,
                             'analysis_rows': MAX_ANALYSIS_ROWS, 'json_bytes': MAX_JSON_BYTES},
                  'arrays': {}, 'capture_refusals': [], 'row_summaries': []}
        used = 0
        def save_array(name, value):
            nonlocal used
            desc = array_identity(value)
            report['arrays'][name] = desc
            if not isinstance(value, np.ndarray) or value.dtype.hasobject:
                desc['retained'] = False
                report['capture_refusals'].append(name + ':not_numeric_ndarray_or_object_dtype')
                return
            if value.nbytes > MAX_ARRAY_BYTES or used + value.nbytes + 4096 > MAX_CAPTURE_BYTES or len(report['arrays']) > MAX_ARRAYS:
                desc['retained'] = False
                report['capture_refusals'].append(name + ':capture_size_cap')
                return
            path = self.directory / (name + '.npy')
            with path.open('xb') as stream:
                np.save(stream, value, allow_pickle=False)
            size = path.stat().st_size
            used += size
            desc.update({'retained': True, 'file': path.name, 'file_bytes': size,
                         'file_sha256': sha(path.read_bytes())})
        if isinstance(outputs, (tuple, list)):
            report['output_container'] = type(outputs).__name__
            report['output_count'] = len(outputs)
            for i, value in enumerate(outputs[:MAX_ARRAYS]):
                save_array('raw_output_' + str(i), value)
            if len(outputs) > MAX_ARRAYS:
                report['capture_refusals'].append('raw_output_count_cap')
        else:
            report['output_container'] = type(outputs).__name__
        for name in ('dets', 'labels', 'mask', 'eligible', 'box'):
            value = locals_.get(name)
            # Raw dets/labels are already captured without duplicating their bytes.
            if name in ('dets', 'labels'):
                report[name + '_decoder_identity'] = array_identity(value)
            elif isinstance(value, np.ndarray):
                save_array('decoder_' + name, value)
        eligible, mask, dets = (locals_.get(x) for x in ('eligible', 'mask', 'dets'))
        message = str(exc)
        analysis_arrays = (eligible, mask, dets, locals_.get('values'))
        analysis_ready = all(isinstance(x, np.ndarray) and not x.dtype.hasobject and x.nbytes <= MAX_ARRAY_BYTES for x in analysis_arrays)
        if analysis_ready and (len(eligible) > MAX_ANALYSIS_ROWS or mask.size > MAX_ANALYSIS_ROWS):
            analysis_ready = False
        if eligible is not None and not analysis_ready:
            report['capture_refusals'].append('row_analysis_size_or_dtype_cap')
        if analysis_ready:
            retained_indices = np.flatnonzero(mask)
            save_array('retained_original_row_indices', retained_indices)
            if message == 'degenerate retained detector box':
                bad = (eligible[:, 2] <= eligible[:, 0]) | (eligible[:, 3] <= eligible[:, 1])
                stage = 'float32_retained_before_scaling'
            elif message == 'floor produced degenerate retained box':
                final = locals_['box']
                bad = (final[:, 2] <= final[:, 0]) | (final[:, 3] <= final[:, 1])
                stage = 'after_original_scaling_offset_floor'
                # Diagnostic-only reconstruction, never returned to the worker.
                scaled = eligible[:, :4] * locals_['factor']
                offset = scaled.copy()
                offset[:, [0, 2]] += np.float32(locals_['column'])
                offset[:, [1, 3]] += np.float32(locals_['row'])
                divided = offset / np.float32(0.5)
                for name, value in [('scale', scaled), ('offset', offset), ('pre_floor', divided)]:
                    save_array('diagnostic_reconstructed_' + name, value)
                report['reconstruction_role'] = 'diagnostic_only_after_original_failure'
            else:
                bad = None
                stage = 'other_original_guard'
            report['guard_stage'] = stage
            if bad is not None:
                indices = retained_indices[bad]
                save_array('offending_original_row_indices', indices)
                report['offending_row_count'] = int(len(indices))
                report['row_summaries_truncated'] = len(indices) > MAX_ROW_SUMMARIES
                raw_bad_count = 0
                collapse_count = 0
                conversion_nonfinite_count = 0
                for index in indices:
                    raw = dets[0, index]
                    converted = locals_['values'][index]
                    raw_finite = bool(np.isfinite(raw[:4]).all())
                    converted_finite = bool(np.isfinite(converted[:4]).all())
                    raw_bad = bool(raw[2] <= raw[0] or raw[3] <= raw[1])
                    float32_bad = bool(converted[2] <= converted[0] or converted[3] <= converted[1])
                    raw_bad_count += int(raw_bad)
                    finite_collapse = bool(raw_finite and converted_finite and not raw_bad and float32_bad)
                    conversion_nonfinite = bool(raw_finite and not converted_finite)
                    collapse_count += int(finite_collapse)
                    conversion_nonfinite_count += int(conversion_nonfinite)
                    if len(report['row_summaries']) < MAX_ROW_SUMMARIES:
                        report['row_summaries'].append({
                            'original_row_index': int(index), 'raw_coordinates': [number_text(x) for x in raw[:4]],
                            'raw_score': number_text(raw[4]), 'float32_coordinates': [number_text(x) for x in converted[:4]],
                            'float32_score': number_text(converted[4]),
                            'raw_nonpositive_extent': raw_bad, 'float32_nonpositive_extent': float32_bad,
                            'raw_coordinates_finite': raw_finite, 'float32_coordinates_finite': converted_finite,
                            'strictly_positive_raw_collapsed_in_float32': finite_collapse,
                            'finite_raw_became_nonfinite_float32': conversion_nonfinite,
                            'float32_score_gte_storage_floor': bool(converted[4] >= np.float32(self.worker.CONFIG['storage_score_gte'])),
                            'float32_score_gt_analysis_threshold': bool(converted[4] > self.worker.CONFIG['analysis_score_gt'])})
                report['offending_raw_nonpositive_extent_count'] = raw_bad_count
                report['offending_strictly_positive_raw_float32_collapse_count'] = collapse_count
                report['offending_finite_raw_nonfinite_float32_count'] = conversion_nonfinite_count
        report['retained_array_file_bytes'] = used
        data = json.dumps(report, sort_keys=True, separators=(',', ':'), allow_nan=False).encode() + b'\n'
        if len(data) > MAX_JSON_BYTES:
            raise ValueError('diagnostic JSON cap')
        with (self.directory / 'diagnostic.json').open('xb') as stream:
            stream.write(data)
        del frame, tb, locals_


def install(worker, capture):
    original = worker.decode_output
    def wrapped(outputs, row, column, resized_side):
        # The exact-bound original does not mutate raw outputs (qualified below).
        caller = inspect.currentframe().f_back
        try:
            try:
                return original(outputs, row, column, resized_side)
            except Exception as exc:
                try:
                    context = context_from_frame(caller, worker, row, column, resized_side)
                    capture.save(exc, outputs, context, original)
                except BaseException as logging_error:
                    try:
                        sys.stderr.write('diagnostic_capture_failed:' + type(logging_error).__name__ + '\n')
                    except BaseException:
                        pass
                raise
        finally:
            del caller
    worker.decode_output = wrapped
    return original


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', action='store_true', required=True)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    os.umask(0o077)
    worker = load_worker()
    output = Path(args.output)
    capture = Capture(output / 'decode-diagnostic', worker)
    install(worker, capture)
    worker.execute(args.manifest, args.output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
