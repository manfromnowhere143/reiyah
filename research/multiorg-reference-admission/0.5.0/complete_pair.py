#!/usr/bin/env python3
"""Complete first-image analysis endpoint for explicitly named model variants.

The original numerical preprocessing/projection/NMS modules remain byte-bound.
Every Faster tile is checked against its own origin/direct-removal contract;
this runner never manufactures an original-model baseline from corrected taps.
"""
import argparse
import gc
import hashlib
import io
import json
import math
import os
from pathlib import Path
import time
import types

import numpy as np

OWNER = Path(__file__).resolve().parent.parent
ORIGINAL_SHA = '9a708bf6a22e9350980e0d08d0e90c2c56f7b9cc4a73b7fd55f22c9ef3f33e0c'
PROJECTION_SHA = '7cf0103cd7876585004310f6a3457add033bab2bc91b8b5ca750b15982a47425'
FASTER_SHA = 'a26f494f548ed8410a809252b2acaae97e2efa189fcee963a5b8a09dd4c13b63'
YOLO_SHA = '02ed40f0cbdcf9023390e9723a1c310d5dd3f4d18a3ad1c3774f71ff74969ee6'
IMAGE_SHA = '8828e0a9f94d6c44ea03be2e62623e812830f339d9c905b7a368edcb7e821eb0'
IMAGE_ID = 'MultiOrg_v2/test/Macros/Plate_4/image_7/image_7.tiff'
TAPS_SHA = 'c08932819200b816fa9c0dca38bf32e159325aa0a9e46cb7ada071c004acb8ba'
PINS = {'faster': FASTER_SHA, 'yolo': YOLO_SHA, 'original': ORIGINAL_SHA,
        'projection': PROJECTION_SHA, 'taps': TAPS_SHA,
        'origin_reference': '7b665ff849c2ba5a383e414de7d62fede77273dbb9f19f08057756bddc04cb17',
        'reference_core': '428579d22cfa49588c76172999c90beab3cb57e13a04540aa5bdc6ac413f1d7c',
        'input_roster': '7de68d1d0f6ca67d143c3db3a40efa3d4d4d70f657d031371229262483a1ce35'}
REFERENCE_KEYS = {'origin_reference', 'reference_core'}
VARIANTS = {'faster': 'reiyah.multiorg.validity-preserving-export.observation/0.4.0',
            'yolo': 'MultiOrg-2026-released-YOLO-unchanged'}
SHAPES = {'original': [5720, 6385], 'rescaled': [2860, 3192], 'padded': [3328, 3584]}
ROSTER = [[r, c] for r in range(0, 2860, 256) for c in range(0, 3192, 256)]
LIMITS = {'wall_seconds': 600, 'memory_bytes': 3221225472,
          'max_tiles_per_image': 156, 'max_raw_boxes_per_image': 200000,
          'max_array_file_bytes': 67108864, 'max_array_total_bytes': 134217728}
DERIVED_ARRAY_BYTES = 66823136
ARRAY_DERIVATION_SHA = '000a141a08e5c4060784204fab6e7f5665f2ed04af6fb03b9f8751634518a516'
SCOPE = 'all_declared_tiles_analysis_score_float32_strictly_gt_0.5_only'
STORAGE_STATUS = 'not_defined_or_exported_by_this_contract'
MAX_JSON = 67108864


def sha(data): return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def file_sha(path, cap=300000000):
    if Path(path).stat().st_size > cap: raise ValueError('input byte cap')
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for data in iter(lambda: f.read(1048576), b''): h.update(data)
    return h.hexdigest()


def confined(path, exists=True):
    path = Path(path)
    if '..' in path.parts: raise ValueError('path traversal')
    path = path.resolve(strict=exists)
    if not path.is_relative_to(OWNER) or (exists and not path.is_file()):
        raise ValueError('path outside owner or not a regular file')
    return path


def load_json(path, cap=1048576):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            if key in out: raise ValueError('duplicate JSON property')
            out[key] = value
        return out
    path = confined(path)
    if path.stat().st_size > cap: raise ValueError('JSON cap')
    return json.loads(path.read_bytes(), object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def write_json(path, value):
    raw = canonical(value) + b'\n'
    if len(raw) > MAX_JSON: raise ValueError('output JSON cap')
    with Path(path).open('xb') as f: f.write(raw)
    return {'file': Path(path).name, 'sha256': sha(raw), 'bytes': len(raw)}


def module(path, expected, name):
    raw = confined(path).read_bytes()
    if len(raw) > 1048576 or sha(raw) != expected: raise ValueError('component digest mismatch')
    value = types.ModuleType(name); value.__file__ = str(Path(path).resolve())
    exec(compile(raw, value.__file__, 'exec'), value.__dict__)
    return value


def bind(manifest_path):
    m = load_json(manifest_path)
    if not isinstance(m, dict) or set(m) != {'protocol', 'images', 'models', 'limits'}:
        raise ValueError('manifest schema')
    if not isinstance(m['models'], dict) or set(m['models']) != set(PINS) | REFERENCE_KEYS:
        raise ValueError('component/model roster')
    if (not isinstance(m['images'], list) or len(m['images']) != 1
            or set(m['images'][0]) != {'id', 'source'} or m['images'][0]['id'] != IMAGE_ID):
        raise ValueError('first image identity')
    if m['limits'] != LIMITS or any(type(m['limits'][key]) is not int for key in LIMITS):
        raise ValueError('exact resource contract')
    refs = {'protocol': m['protocol'], 'image': m['images'][0]['source'], **m['models']}
    paths = {}
    for key, ref in refs.items():
        if not isinstance(ref, dict) or set(ref) != {'path', 'sha256'}:
            raise ValueError('source binding schema')
        if not isinstance(ref['sha256'], str) or len(ref['sha256']) != 64:
            raise ValueError('source digest format')
        path = confined(ref['path'])
        if file_sha(path) != ref['sha256'] or (key in PINS and ref['sha256'] != PINS[key]):
            raise ValueError('source binding mismatch: ' + key)
        paths[key] = path
    if refs['image']['sha256'] != IMAGE_SHA: raise ValueError('different source image')
    if paths['original'] != Path(__file__).with_name('run_pair.py').resolve():
        raise ValueError('original numerical module location')
    if paths['projection'] != Path(__file__).with_name('projection.py').resolve():
        raise ValueError('projection module location')
    if paths['reference_core'] != paths['origin_reference'].with_name('reference_core.py'):
        raise ValueError('imported reference core location')
    protocol = load_json(paths['protocol'])
    expected = {'artifact_id', 'version', 'worker_contract', 'image_id', 'shapes', 'tile_roster',
                'model_variants', 'model_order', 'config', 'component_sha256', 'array_budget', 'limits'}
    if not isinstance(protocol, dict) or set(protocol) != expected:
        raise ValueError('protocol schema')
    if (protocol['artifact_id'] != 'reiyah.multiorg.complete-pair-protocol'
            or protocol['version'] != '0.5.0'
            or protocol['worker_contract'] != 'complete_first_image_analysis_pair_v050'
            or protocol['image_id'] != IMAGE_ID or protocol['model_order'] != ['faster', 'yolo']
            or protocol['model_variants'] != VARIANTS or protocol['limits'] != LIMITS):
        raise ValueError('protocol identity or execution contract')
    if protocol['shapes'] != SHAPES or protocol['tile_roster'] != ROSTER:
        raise ValueError('prospective shape/tile roster')
    if any(type(x) is not int for shape in protocol['shapes'].values() for x in shape):
        raise ValueError('shape integer schema')
    if any(not isinstance(row, list) or len(row) != 2 or any(type(x) is not int for x in row)
           for row in protocol['tile_roster']):
        raise ValueError('tile integer schema')
    comps = protocol['component_sha256']
    if not isinstance(comps, dict) or set(comps) != {'original', 'projection', 'taps'} | REFERENCE_KEYS:
        raise ValueError('component pin roster')
    if any(comps[key] != refs[key]['sha256'] for key in comps):
        raise ValueError('protocol component binding')
    budget = protocol['array_budget']
    if (not isinstance(budget, dict) or set(budget) != {'per_file_bytes', 'total_bytes', 'derived_maximum_bytes', 'derivation_sha256'}
            or type(budget['derived_maximum_bytes']) is not int
            or budget['derived_maximum_bytes'] != DERIVED_ARRAY_BYTES
            or budget['derivation_sha256'] != ARRAY_DERIVATION_SHA
            or budget['per_file_bytes'] != LIMITS['max_array_file_bytes']
            or budget['total_bytes'] != LIMITS['max_array_total_bytes']):
        raise ValueError('prospective array budget')
    original = module(paths['original'], ORIGINAL_SHA, '_original_numeric_worker')
    projection = module(paths['projection'], PROJECTION_SHA, '_original_analysis_projection')
    if protocol['config'] != original.CONFIG: raise ValueError('numerical config differs')
    reference = module(paths['origin_reference'], refs['origin_reference']['sha256'], '_origin_reference')
    taps = load_json(paths['taps'])
    if not isinstance(taps, list) or len(taps) != 31: raise ValueError('corrected tap roster')
    if tuple(['dets', 'labels'] + [t['name'] for t in taps]) != reference.NAMES:
        raise ValueError('reference and graph name rosters differ')
    return m, refs, paths, protocol, original, projection, reference, taps


def checked_input_roster(path):
    roster = load_json(path)
    if (roster.get('artifact_id') != 'reiyah.multiorg.complete-pair.input-roster'
            or roster.get('version') != '0.5.0' or roster.get('status') != 'complete'
            or roster.get('original_worker_sha256') != ORIGINAL_SHA
            or roster.get('image_source_sha256') != IMAGE_SHA or roster.get('image_id') != IMAGE_ID
            or roster.get('image_shape_hw') != SHAPES['original']
            or roster.get('rescaled_shape_hw') != SHAPES['rescaled']
            or roster.get('padded_shape_hw') != SHAPES['padded']
            or roster.get('roster') != ROSTER or roster.get('tiles_per_model') != len(ROSTER)):
        raise ValueError('input roster identity or population')
    rows = roster.get('tensors')
    if not isinstance(rows, list) or len(rows) != 2 * len(ROSTER):
        raise ValueError('input tensor roster cardinality')
    for index, row in enumerate(rows):
        model, ordinal = ['faster', 'yolo'][index // len(ROSTER)], index % len(ROSTER)
        if (set(row) != {'model', 'ordinal', 'rescaled_row', 'rescaled_column', 'resized_side', 'tensor'}
                or row['model'] != model or type(row['ordinal']) is not int or row['ordinal'] != ordinal
                or [row['rescaled_row'], row['rescaled_column']] != ROSTER[ordinal]
                or row['resized_side'] != (800 if model == 'faster' else 416)):
            raise ValueError('input tensor roster ordering/identity')
    return roster


class RawStore:
    def __init__(self, root): self.root, self.bytes, self.files = root, 0, 0

    def save(self, stem, names, outputs):
        if not isinstance(outputs, (list, tuple)) or not 1 <= len(outputs) <= 64:
            raise ValueError('raw output collection cap')
        estimate = 0
        for value in outputs:
            if not isinstance(value, np.ndarray) or value.dtype.hasobject or value.dtype.kind not in 'biuf':
                raise ValueError('raw output must be numeric non-object array')
            if value.nbytes + 4096 > LIMITS['max_array_file_bytes']:
                raise ValueError('raw array per-file cap')
            estimate += value.nbytes + 4096
        if self.bytes + estimate > LIMITS['max_array_total_bytes']:
            raise ValueError('raw aggregate array cap')
        saved = []
        for index, value in enumerate(outputs):
            path = self.root / (stem + '-' + str(index) + '.npy')
            with path.open('xb') as f: np.save(f, value, allow_pickle=False)
            size = path.stat().st_size
            if size > LIMITS['max_array_file_bytes'] or self.bytes + size > LIMITS['max_array_total_bytes']:
                raise ValueError('actual raw array byte cap')
            self.bytes += size; self.files += 1
            saved.append({'name': names[index] if index < len(names) else 'UNEXPECTED_OUTPUT_POSITION_' + str(index),
                'file': str(path.relative_to(self.root.parent)), 'sha256': file_sha(path), 'bytes': size,
                'dtype': value.dtype.str, 'shape': list(value.shape),
                'c_order_data_sha256': sha(value.tobytes(order='C'))})
        return saved


def prepare(source, original):
    import tifffile
    contents = confined(source).read_bytes()
    if len(contents) > 100000000: raise ValueError('image byte cap')
    with tifffile.TiffFile(io.BytesIO(contents)) as tf:
        if len(tf.series) != 1 or math.prod(tf.series[0].shape) > 80000000:
            raise ValueError('TIFF series/decoded pixel cap')
        data = tf.series[0].asarray()
    pixels, resized, shape = original.prepare_image(data)
    actual_roster = [list(x) for x in original.tile_roster(*map(int, resized))]
    if (list(shape) != SHAPES['original'] or list(resized) != SHAPES['rescaled']
            or list(pixels.shape) != SHAPES['padded'] or actual_roster != ROSTER):
        raise ValueError('actual image reconstruction/whole tile coverage differs')
    if len(actual_roster) != LIMITS['max_tiles_per_image']:
        raise ValueError('whole-image tile count differs')
    return pixels, list(resized), list(shape), actual_roster


def make_session(path, model, original):
    import onnxruntime as ort
    raw = path.read_bytes()
    if model == 'yolo':
        spec = original.MODELS['yolo']
        if len(raw) != spec['bytes'] or hashlib.md5(raw).hexdigest() != spec['md5']:
            raise ValueError('original YOLO size/MD5 identity')
    elif len(raw) != 165474438:
        raise ValueError('corrected observation graph size')
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2; options.inter_op_num_threads = 1
    options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    # Pinned ORT1.23 constructor and run() both otherwise retry EP failures.
    session = ort.InferenceSession(raw, sess_options=options, providers=['CPUExecutionProvider'],
                                   enable_fallback=False)
    session.disable_fallback()
    return session


def io_contract(session, model, taps):
    if session.get_providers() != ['CPUExecutionProvider']: raise ValueError('CPU provider required')
    ins = session.get_inputs()
    if len(ins) != 1 or ins[0].name != 'input' or ins[0].type != 'tensor(float)' or len(ins[0].shape) != 4:
        raise ValueError('ONNX input contract')
    if model == 'faster' and (type(ins[0].shape[0]) is not int or ins[0].shape[0] != 1):
        raise ValueError('corrected batch-one signature')
    names = ['dets', 'labels'] + ([t['name'] for t in taps] if model == 'faster' else [])
    if len(set(names)) != len(names) or [v.name for v in session.get_outputs()] != names:
        raise ValueError('exact named ONNX output roster')
    return ins[0], names


def checked_outputs(names, outputs, model, taps):
    if len(outputs) != len(names): raise ValueError('returned named output count')
    specs = [{'name': 'dets', 'elem_type': 1, 'rank': 3}, {'name': 'labels', 'elem_type': 7, 'rank': 2}]
    if model == 'faster': specs += taps
    for spec, value in zip(specs, outputs):
        if value.dtype.str != {1: '<f4', 7: '<i8', 9: '|b1'}[spec['elem_type']] or value.ndim != spec['rank']:
            raise ValueError('returned output dtype/rank: ' + spec['name'])
        if value.dtype.kind == 'f' and not np.isfinite(value).all():
            raise ValueError('nonfinite named output: ' + spec['name'])
    return dict(zip(names, outputs))


def execute(manifest_path, destination):
    import cv2
    import onnxruntime as ort
    manifest_path, destination = confined(manifest_path), confined(destination, exists=False)
    destination.mkdir(mode=0o700, exist_ok=False)
    raw_dir = destination / 'raw'; raw_dir.mkdir(mode=0o700)
    admissions_dir = destination / 'admissions'; admissions_dir.mkdir(mode=0o700)
    store, started = RawStore(raw_dir), time.monotonic()
    record = {'artifact_id': 'reiyah.multiorg.complete-analysis-pair', 'version': '0.5.0',
        'status': 'failed', 'stage': 'binding', 'completion_scope': SCOPE, 'storage_output_status': STORAGE_STATUS,
        'runner_sha256': file_sha(__file__), 'manifest_sha256': file_sha(manifest_path, 1048576),
        'forward_passes_started': 0, 'forward_passes_completed': 0, 'expected_tiles_per_model': len(ROSTER),
        'tile_coverage': {m: {'captured': 0, 'admitted': 0, 'complete': False} for m in ('faster', 'yolo')},
        'observations': [], 'last_raw_receipt': None, 'last_admission_receipt': None,
        'scope': 'corrected Faster observation variant plus unchanged YOLO; no original-model counterfactual'}
    failure = None
    try:
        m, refs, paths, protocol, original, projection, reference, taps = bind(manifest_path)
        record.update(manifest=m, source_bindings=refs, protocol_sha256=refs['protocol']['sha256'],
                      config=original.CONFIG, model_variants=VARIANTS,
                      original_worker_sha256=ORIGINAL_SHA, projection_sha256=PROJECTION_SHA,
                      environment=original.environment())
        if ort.__version__ != '1.23.0' or np.__version__ != '2.2.6':
            raise ValueError('qualified numerical runtime versions')
        cv2.setNumThreads(1)
        record['fallback_policy'] = 'constructor_enable_fallback_false_and_session_disable_fallback; no hidden retry'
        deadline = started + LIMITS['wall_seconds']
        def budget():
            if time.monotonic() >= deadline: raise TimeoutError('worker wall budget')
        record['stage'] = 'image_preprocessing'
        pixels, resized, shape, roster = prepare(paths['image'], original)
        input_roster = checked_input_roster(paths['input_roster'])
        if sha(pixels.tobytes(order='C')) != input_roster['quantized_pixels_c_order_sha256']:
            raise ValueError('quantized input identity differs from prospective roster')
        budget()
        # Every expected tile is verified before the first model session or run.
        for row, column in roster:
            if pixels[row:row+512, column:column+512].shape != (512, 512):
                raise ValueError('incomplete prospective tile')
        record['actual_tile_roster'] = roster
        record['actual_image_shapes'] = {'original': shape, 'rescaled': resized, 'padded': list(pixels.shape)}
        for model in ['faster', 'yolo']:
            record.update(stage='model_session', active_model=model, active_tile_ordinal=None)
            budget()
            session = make_session(paths[model], model, original)
            inp, names = io_contract(session, model, taps)
            begin = time.monotonic()
            tile_results, trace, raw_seen = [], [], 0
            stem = sha(original.canonical([IMAGE_ID, model]))
            for ordinal, (row, column) in enumerate(roster):
                record.update(stage='tile_input', active_tile_ordinal=ordinal)
                budget()
                tensor, side = original.model_input(pixels[row:row+512, column:column+512], model)
                if tensor.dtype != np.float32 or not np.isfinite(tensor).all():
                    raise ValueError('invalid preprocessed tensor')
                for expected, actual in zip(inp.shape, tensor.shape):
                    if type(expected) is int and expected != actual: raise ValueError('ONNX input shape mismatch')
                tensor_identity = {'dtype': tensor.dtype.str, 'shape': list(tensor.shape),
                    'c_order_data_sha256': sha(tensor.tobytes(order='C')), 'observation_time': 'before_session_run'}
                expected_tensor = input_roster['tensors'][(0 if model == 'faster' else len(roster)) + ordinal]
                if (side != expected_tensor['resized_side']
                        or {k: tensor_identity[k] for k in ('dtype', 'shape', 'c_order_data_sha256')} != expected_tensor['tensor']):
                    raise ValueError('actual tensor differs from prospective roster')
                record['stage'] = 'model_forward'; record['forward_passes_started'] += 1
                outputs = session.run(names, {inp.name: tensor})
                record['forward_passes_completed'] += 1
                record['stage'] = 'raw_capture'
                saved = store.save(stem + '-' + str(ordinal), names, outputs)
                raw_dets = next((value for name, value in zip(names, outputs) if name == 'dets'), None)
                observed_n = int(raw_dets.shape[1]) if raw_dets is not None and raw_dets.ndim == 3 else None
                receipt = {'image_id': IMAGE_ID, 'model': model, 'model_variant': VARIANTS[model],
                    'ordinal': ordinal, 'rescaled_row': row, 'rescaled_column': column,
                    'image_shape_hw': shape, 'rescaled_shape_hw': resized, 'tile_count_expected': len(roster),
                    'resized_side': side, 'image_source_sha256': refs['image']['sha256'],
                    'model_source_sha256': refs[model]['sha256'], 'tensor': tensor_identity,
                    'raw_outputs': saved, 'all_raw_rows_completed_before_tile': raw_seen,
                    'observed_detection_rows': observed_n, 'status': 'raw_outputs_retained_before_admission'}
                receipt_path = raw_dir / (stem + '-' + str(ordinal) + '.json')
                desc = write_json(receipt_path, receipt)
                record['last_raw_receipt'] = {**desc, 'file': str(receipt_path.relative_to(destination))}
                record['tile_coverage'][model]['captured'] += 1
                record['stage'] = 'tile_admission'
                named = checked_outputs(names, outputs, model, taps)
                origin = reference.validate_tile(named) if model == 'faster' else None
                if model == 'faster' and (not isinstance(origin, dict)
                        or origin.get('status') != 'corrected_variant_tile_admitted'
                        or origin.get('original_baseline_comparison_performed') is not False):
                    raise ValueError('origin helper did not admit corrected variant tile')
                budget()
                projected = projection.project_tile([named['dets'], named['labels']], row, column, side,
                    decoder=original.decode_output, remaining_raw_rows=LIMITS['max_raw_boxes_per_image'] - raw_seen)
                raw_seen += projected['all_raw_rows']
                tile_results.append({'ordinal': ordinal, 'projection': projected})
                counts = {key: projected[key] for key in ('all_raw_rows', 'high_rows', 'low_rows',
                    'storage_eligible_rows', 'below_storage_floor_rows', 'raw_above_half_converted_not_above_half_rows')}
                admitted = {**receipt, 'status': 'tile_analysis_projection_defined', **counts,
                    'origin_admission': origin,
                    'analysis_original_row_indices': projected['original_row_indices'].tolist(),
                    'low_geometry_anomaly_indices': {k: v.tolist() for k, v in projected['low_geometry_anomalies'].items()},
                    'storage_eligible_low_geometry_anomaly_indices': {k: v.tolist() for k, v in projected['storage_eligible_low_geometry_anomalies'].items()},
                    'low_transformed_geometry': projected['low_transformed_geometry']}
                admission_path = admissions_dir / (stem + '-' + str(ordinal) + '.json')
                admission_desc = write_json(admission_path, admitted)
                record['last_admission_receipt'] = {**admission_desc, 'file': str(admission_path.relative_to(destination))}
                trace.append(admitted)
                record['tile_coverage'][model]['admitted'] += 1
                budget()
            record['stage'] = 'whole_image_nms'
            complete = projection.complete_projection(tile_results, expected_tiles=len(roster),
                raw_cap=LIMITS['max_raw_boxes_per_image'], nms=original.stable_nms)
            prefix, total = [], 0
            for tile in trace: prefix.append(total); total += tile['all_raw_rows']
            predictions = [{'id': prefix[tile] + raw_row, 'tile_ordinal': tile, 'original_row_index': raw_row,
                'box_xyxy': list(map(int, box)), 'score': float(score)}
                for (tile, raw_row), box, score in zip(complete['analysis_row_ids'], complete['analysis_boxes'], complete['analysis_scores'])]
            result = {'artifact_id': 'reiyah.multiorg.complete-analysis-image', 'version': '0.5.0',
                'status': 'complete', 'completion_scope': SCOPE, 'storage_output_status': STORAGE_STATUS,
                'image_id': IMAGE_ID, 'model': model, 'model_variant': VARIANTS[model],
                'model_source_sha256': refs[model]['sha256'], 'image_shape_hw': shape, 'rescaled_shape_hw': resized,
                'tile_count_expected': len(roster), 'tile_count_completed': len(trace), 'tiles': trace,
                'raw_onnx_rows': raw_seen, 'analysis_predictions': predictions, 'empty_analysis': not bool(predictions),
                'analysis_identity': 'original raw row ordinal across ordered tiles; tile/row retained',
                'analysis_outside_image': original.outside_count([p['box_xyxy'] for p in predictions], shape),
                'onnx_input': {'name': inp.name, 'shape': inp.shape, 'type': inp.type},
                'onnx_output_names': names, 'providers': session.get_providers(),
                'protocol_sha256': refs['protocol']['sha256'], 'original_worker_sha256': ORIGINAL_SHA,
                'projection_sha256': PROJECTION_SHA, 'wall_seconds': time.monotonic() - begin}
            desc = write_json(destination / (stem + '.json'), result)
            record['observations'].append({**desc, 'image_id': IMAGE_ID, 'model': model,
                'model_variant': VARIANTS[model], 'analysis_count': len(predictions), 'raw_onnx_rows': raw_seen,
                'completion_scope': SCOPE})
            record['tile_coverage'][model]['complete'] = True
            del session, tile_results, trace
            gc.collect(); budget()
        if record['forward_passes_completed'] != 2 * len(roster): raise ValueError('pair coverage incomplete')
        for key, ref in refs.items():
            if file_sha(paths[key]) != ref['sha256']: raise ValueError('source changed during execution: ' + key)
        if file_sha(manifest_path, 1048576) != record['manifest_sha256'] or file_sha(__file__) != record['runner_sha256']:
            raise ValueError('manifest/runner changed during execution')
        record.update(status='complete', stage='complete', active_model=None, active_tile_ordinal=None)
    except BaseException as exc:
        failure = exc; record['error'] = type(exc).__name__ + ': ' + str(exc)
        raise
    finally:
        record.update(raw_array_files_bytes=store.bytes, raw_array_file_count=store.files,
                      wall_seconds=time.monotonic() - started)
        try: write_json(destination / ('result.json' if record['status'] == 'complete' else 'failure.json'), record)
        except Exception:
            if failure is None: raise
    return record


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--worker', action='store_true', required=True)
    p.add_argument('--manifest', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); os.umask(0o077)
    result = execute(a.manifest, a.output)
    print(json.dumps({'status': result['status'], 'completed_forwards': result['forward_passes_completed'],
                      'raw_array_bytes': result['raw_array_files_bytes']}))


if __name__ == '__main__': main()
