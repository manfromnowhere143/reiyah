#!/usr/bin/env python3
"""Explicit analysis-only endpoint; retain all raw outputs, never export storage."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
import os
from pathlib import Path
import resource
import sys
import time
import types
import numpy as np

OWNER = Path(__file__).resolve().parents[1]
ORIGINAL_SHA = '9a708bf6a22e9350980e0d08d0e90c2c56f7b9cc4a73b7fd55f22c9ef3f33e0c'
PROJECTION_SHA = '7cf0103cd7876585004310f6a3457add033bab2bc91b8b5ca750b15982a47425'
SUPPLEMENT_SHA = 'edf53f094e41a219027054c9f70fea1f14bd4081010fd2fafaabca4b4e265e26'
MAX_RAW_FILE_BYTES = 64 * 1024 * 1024
MAX_RAW_TOTAL_BYTES = 64 * 1024 * 1024
MAX_JSON_BYTES = 64 * 1024 * 1024
SCOPE = 'all_declared_tiles_analysis_score_float32_strictly_gt_0.5_only'
STORAGE_STATUS = 'not_defined_or_exported_by_this_contract'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def bound_module(path, expected, name):
    raw = Path(path).read_bytes()
    if sha(raw) != expected:
        raise ValueError(name + ' digest mismatch')
    module = types.ModuleType(name)
    module.__file__ = str(Path(path).resolve())
    exec(compile(raw, module.__file__, 'exec'), module.__dict__)
    return module


def load_components():
    original = bound_module(Path(__file__).with_name('run_pair.py'), ORIGINAL_SHA, '_original_worker')
    projection = bound_module(Path(__file__).with_name('projection.py'), PROJECTION_SHA, '_qualified_projection')
    path = OWNER / 'protocol/analysis-projection.json'
    data = original.checked_file({'path': str(path), 'sha256': SUPPLEMENT_SHA}, 1048576)
    return original, projection, json.loads(data)


def write_json(path, value, original):
    data = original.canonical(value) + b'\n'
    if len(data) > MAX_JSON_BYTES:
        raise ValueError('output JSON byte cap')
    with Path(path).open('xb') as stream:
        stream.write(data)
    return {'file': Path(path).name, 'sha256': sha(data), 'bytes': len(data)}


class RawStore:
    def __init__(self, destination):
        self.destination = Path(destination)
        self.bytes = 0

    def save(self, stem, outputs):
        if not isinstance(outputs, (list, tuple)) or len(outputs) != 2:
            raise ValueError('two raw output arrays required')
        estimate = 0
        for array in outputs:
            if not isinstance(array, np.ndarray) or array.dtype.hasobject:
                raise ValueError('raw output must be a non-object ndarray')
            if array.nbytes + 4096 > MAX_RAW_FILE_BYTES:
                raise ValueError('raw output per-file byte cap')
            estimate += array.nbytes + 4096
        if self.bytes + estimate > MAX_RAW_TOTAL_BYTES:
            raise ValueError('raw output total byte cap')
        rows = []
        for index, array in enumerate(outputs):
            path = self.destination / (stem + '-' + str(index) + '.npy')
            with path.open('xb') as stream:
                np.save(stream, array, allow_pickle=False)
            count = path.stat().st_size
            if count > MAX_RAW_FILE_BYTES or self.bytes + count > MAX_RAW_TOTAL_BYTES:
                raise ValueError('raw output actual byte cap')
            self.bytes += count
            rows.append({'file': str(path.relative_to(self.destination.parent)),
                         'sha256': file_sha(path), 'bytes': count,
                         'dtype': array.dtype.str, 'shape': list(array.shape),
                         'c_order_data_sha256': sha(array.tobytes(order='C'))})
        return rows


def numeric_list(value):
    return np.asarray(value).tolist()


def execute(manifest_path, destination, *, original=None, projection=None, supplement=None):
    import cv2
    import onnxruntime as ort
    import tifffile
    if original is None:
        original, projection, supplement = load_components()
    manifest = original.validated_manifest(manifest_path)
    expected_limits = {'wall_seconds': 600, 'memory_bytes': 3221225472,
                       'max_tiles_per_image': 512, 'max_raw_boxes_per_image': 200000}
    if manifest['limits'] != expected_limits or len(manifest['images']) != 1:
        raise ValueError('exact single-image resource contract required')
    if manifest['images'][0]['id'] != supplement['image_id']:
        raise ValueError('frozen first image required')
    manifest_sha = file_sha(manifest_path)
    own_sha = file_sha(__file__)
    source_pins = {str(Path(__file__).with_name('run_pair.py')): ORIGINAL_SHA,
                   str(Path(__file__).with_name('projection.py')): PROJECTION_SHA,
                   str(OWNER / 'protocol/analysis-projection.json'): SUPPLEMENT_SHA}
    for path, expected in source_pins.items():
        if file_sha(path) != expected:
            raise ValueError('source contract changed')
    destination = Path(destination)
    if destination.exists() or not destination.parent.resolve().is_relative_to(OWNER):
        raise ValueError('new output directory under owner required')
    destination.mkdir(mode=0o700)
    raw_dir = destination / 'raw'
    raw_dir.mkdir(mode=0o700)
    store = RawStore(raw_dir)
    started = time.monotonic()
    deadline = started + manifest['limits']['wall_seconds']
    cv2.setNumThreads(1)
    cpu = manifest['limits']['wall_seconds'] * original.CONFIG['intra_threads']
    resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 2))
    resource.setrlimit(resource.RLIMIT_FSIZE, (67108864, 67108864))
    observations = []
    for model in ('faster', 'yolo'):
        spec = original.MODELS[model]
        raw = original.checked_file(manifest['models'][model], 300000000,
                                    expected_md5=spec['md5'], expected_size=spec['bytes'])
        options = ort.SessionOptions()
        options.intra_op_num_threads = original.CONFIG['intra_threads']
        options.inter_op_num_threads = original.CONFIG['inter_threads']
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        session = ort.InferenceSession(raw, sess_options=options, providers=['CPUExecutionProvider'])
        del raw
        if session.get_providers() != ['CPUExecutionProvider'] or len(session.get_inputs()) != 1 or len(session.get_outputs()) != 2:
            raise ValueError('unexpected provider or ONNX IO contract')
        inp = session.get_inputs()[0]
        if inp.type != 'tensor(float)' or len(inp.shape) != 4:
            raise ValueError('unexpected ONNX input dtype/rank')
        image = manifest['images'][0]
        begin = time.monotonic()
        if begin >= deadline:
            raise TimeoutError('worker wall budget')
        contents = original.checked_file(image['source'], 100000000)
        with tifffile.TiffFile(io.BytesIO(contents)) as tf:
            series = tf.series[0]
            if len(tf.series) != 1 or math.prod(series.shape) > 80000000:
                raise ValueError('unsupported TIFF series or decompressed size cap')
            data = series.asarray()
        del contents
        pixels, resized_shape, shape = original.prepare_image(data)
        del data
        roster = original.tile_roster(*map(int, resized_shape))
        if len(roster) > manifest['limits']['max_tiles_per_image']:
            raise ValueError('tile work cap; no partial-image endpoint')
        if len(roster) != supplement['expected_actual_first_image_tiles_per_model']:
            raise ValueError('frozen whole-image tile population differs')
        tile_results, trace, raw_seen = [], [], 0
        stem = sha(original.canonical([image['id'], model]))
        for ordinal, (row, column) in enumerate(roster):
            if time.monotonic() >= deadline:
                raise TimeoutError('worker wall budget')
            tensor, side = original.model_input(pixels[row:row + 512, column:column + 512], model)
            for expected, actual in zip(inp.shape, tensor.shape):
                if type(expected) is int and expected != actual:
                    raise ValueError('graph input shape incompatible with current preprocessing')
            tensor_identity = {'dtype': tensor.dtype.str, 'shape': list(tensor.shape),
                               'c_order_data_sha256': sha(tensor.tobytes(order='C')),
                               'observation_time': 'before_session_run'}
            outputs = session.run(None, {inp.name: tensor})
            # Raw preservation happens before projection or a row-contract refusal.
            saved = store.save(stem + '-' + str(ordinal), outputs)
            tile_receipt = {'image_id': image['id'], 'model': model, 'ordinal': ordinal,
                            'rescaled_row': row, 'rescaled_column': column,
                            'image_shape_hw': shape, 'rescaled_shape_hw': resized_shape,
                            'tile_count_expected': len(roster), 'resized_side': side,
                            'image_source_sha256': image['source']['sha256'],
                            'model_source_sha256': manifest['models'][model]['sha256'],
                            'tensor': tensor_identity, 'raw_outputs': saved,
                            'all_raw_rows_completed_before_tile': raw_seen,
                            'observed_detection_rows': int(outputs[0].shape[1]) if outputs[0].ndim == 3 else None,
                            'status': 'raw_outputs_retained_before_projection'}
            write_json(raw_dir / (stem + '-' + str(ordinal) + '.json'), tile_receipt, original)
            projected = projection.project_tile(outputs, row, column, side,
                decoder=original.decode_output,
                remaining_raw_rows=manifest['limits']['max_raw_boxes_per_image'] - raw_seen)
            raw_seen += projected['all_raw_rows']
            if raw_seen > manifest['limits']['max_raw_boxes_per_image']:
                raise ValueError('all-raw-row work cap')
            tile_results.append({'ordinal': ordinal, 'projection': projected})
            counts = {key: projected[key] for key in ('all_raw_rows', 'high_rows', 'low_rows',
                'storage_eligible_rows', 'below_storage_floor_rows', 'raw_above_half_converted_not_above_half_rows')}
            trace.append({**tile_receipt, 'status': 'tile_analysis_projection_defined', **counts,
                'analysis_original_row_indices': numeric_list(projected['original_row_indices']),
                'low_geometry_anomaly_indices': {k: numeric_list(v) for k, v in projected['low_geometry_anomalies'].items()},
                'storage_eligible_low_geometry_anomaly_indices': {k: numeric_list(v) for k, v in projected['storage_eligible_low_geometry_anomalies'].items()},
                'low_transformed_geometry': projected['low_transformed_geometry']})
        complete = projection.complete_projection(tile_results, expected_tiles=len(roster),
                    raw_cap=manifest['limits']['max_raw_boxes_per_image'], nms=original.stable_nms)
        raw_prefix, total = [], 0
        for tile in trace:
            raw_prefix.append(total)
            total += tile['all_raw_rows']
        predictions = [{'id': raw_prefix[tile] + row, 'tile_ordinal': tile,
                        'original_row_index': row, 'box_xyxy': list(map(int, box)), 'score': float(score)}
            for (tile, row), box, score in zip(complete['analysis_row_ids'], complete['analysis_boxes'], complete['analysis_scores'])]
        result = {'artifact_id': 'reiyah.multiorg.analysis-projection.image', 'version': '0.1.0',
                  'status': 'complete', 'completion_scope': SCOPE, 'storage_output_status': STORAGE_STATUS,
                  'image_id': image['id'], 'model': model, 'image_shape_hw': shape,
                  'rescaled_shape_hw': resized_shape, 'tile_count_expected': len(roster),
                  'tile_count_completed': len(trace), 'tiles': trace, 'raw_onnx_rows': raw_seen,
                  'analysis_predictions': predictions, 'empty_analysis': not bool(predictions),
                  'analysis_identity': 'original raw row ordinal across ordered tiles; tile/row fields retained',
                  'analysis_outside_image': original.outside_count([p['box_xyxy'] for p in predictions], shape),
                  'low_anomaly_scope': 'all_raw_low_rows_including_below_floor_padding; storage-eligible subset separately reported; not a model-defect label',
                  'low_transformed_geometry': 'not_evaluated_not_claimed_valid',
                  'supplemental_protocol_sha256': SUPPLEMENT_SHA, 'projection_sha256': PROJECTION_SHA,
                  'original_worker_sha256': ORIGINAL_SHA, 'wall_seconds': time.monotonic() - begin,
                  'onnx_input': {'name': inp.name, 'shape': inp.shape, 'type': inp.type},
                  'onnx_outputs': [{'name': v.name, 'shape': v.shape, 'type': v.type} for v in session.get_outputs()]}
        original.checked_file(image['source'], 100000000)
        desc = write_json(destination / (stem + '.json'), result, original)
        observations.append({**desc, 'image_id': image['id'], 'model': model,
                             'analysis_count': len(predictions), 'raw_onnx_rows': raw_seen,
                             'completion_scope': SCOPE})
        original.checked_file(manifest['models'][model], 300000000,
                              expected_md5=spec['md5'], expected_size=spec['bytes'])
        del session
    original.checked_file(manifest['protocol'], 1048576)
    if file_sha(manifest_path) != manifest_sha or file_sha(__file__) != own_sha:
        raise ValueError('manifest or adapter changed')
    for path, expected in source_pins.items():
        if file_sha(path) != expected:
            raise ValueError('source contract changed')
    final = {'artifact_id': 'reiyah.multiorg.analysis-projection.run', 'version': '0.1.0',
             'status': 'complete', 'completion_scope': SCOPE, 'storage_output_status': STORAGE_STATUS,
             'manifest': manifest, 'manifest_sha256': manifest_sha, 'config': original.CONFIG,
             'runner_sha256': own_sha, 'original_worker_sha256': ORIGINAL_SHA,
             'projection_sha256': PROJECTION_SHA, 'supplemental_protocol_sha256': SUPPLEMENT_SHA,
             'environment': original.environment(), 'observations': observations,
             'raw_array_files_bytes': store.bytes, 'wall_seconds': time.monotonic() - started}
    write_json(destination / 'result.json', final, original)
    return final


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--worker', action='store_true', required=True)
    p.add_argument('--manifest', required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()
    os.umask(0o077)
    execute(args.manifest, args.output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
