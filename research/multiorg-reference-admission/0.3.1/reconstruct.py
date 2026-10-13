#!/usr/bin/env python3
"""Preprocessing-only reconstruction; never imports ONNX or loads model bytes."""
import argparse
import ast
import hashlib
import importlib.metadata
import io
import json
import math
import os
from pathlib import Path
import resource
import sys
import time
import numpy as np

OWNER = Path(__file__).resolve().parents[1]
WORKER_SHA = '9a708bf6a22e9350980e0d08d0e90c2c56f7b9cc4a73b7fd55f22c9ef3f33e0c'
TENSOR_SHA = '675a5f2aba2565e568feeb93fddc20aaed89a43a9bbeea393bf6336b84ae49d1'
NAMES = {'prepare_image', 'model_input', 'tile_roster'}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read_json(path):
    def unique(items):
        result = {}
        for key, value in items:
            if key in result: raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))

def checked(record, cap=100000000):
    path = Path(record['path']).resolve(strict=True)
    if not path.is_relative_to(OWNER) or not path.is_file() or path.stat().st_size > cap:
        raise ValueError('private input path or byte cap')
    data = path.read_bytes()
    if sha(data) != record['sha256']: raise ValueError('input digest mismatch')
    return data

def primitives(source):
    if sha(source) != WORKER_SHA: raise ValueError('original preprocessing source digest')
    tree = ast.parse(source)
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in NAMES]
    if {node.name for node in selected} != NAMES: raise ValueError('preprocessing function set')
    models = [node for node in tree.body if isinstance(node, ast.Assign)
              and any(isinstance(target, ast.Name) and target.id == 'MODELS' for target in node.targets)]
    if len(models) != 1: raise ValueError('model constants')
    namespace = {'np': np, 'MODELS': ast.literal_eval(models[0].value)}
    exec(compile(ast.Module(body=selected, type_ignores=[]), '<exact-bound-preprocessing-only>', 'exec'), namespace)
    return namespace

def placement(shape, ordinal, recorded_row, recorded_column):
    if len(shape) != 2 or any(type(v) is not int or v <= 0 for v in shape):
        raise ValueError('rescaled shape')
    columns = (shape[1] + 255) // 256
    count = ((shape[0] + 255) // 256) * columns
    if type(ordinal) is not int or not 0 <= ordinal < count: raise ValueError('tile ordinal')
    position = (256 * (ordinal // columns), 256 * (ordinal % columns))
    if position != (recorded_row, recorded_column): raise ValueError('tile placement disagreement')
    return position, count

def write_json(path, obj):
    with Path(path).open('x') as stream:
        json.dump(obj, stream, indent=2, allow_nan=False); stream.write('\n')

def execute(manifest_path, output):
    started = time.monotonic()
    # Refuse even an accidental future model-runtime import in this process.
    def no_model_import(event, args):
        if event == 'import' and args and str(args[0]).split('.')[0] in {'onnx', 'onnxruntime', 'torch'}:
            raise RuntimeError('model runtime import forbidden in reconstruction')
    sys.addaudithook(no_model_import)
    import cv2
    import tifffile
    cv2.setNumThreads(1)
    manifest = read_json(manifest_path)
    if manifest['models'] or manifest['limits'] != {'wall_seconds': 60, 'memory_bytes': 3221225472}:
        raise ValueError('preprocessing-only resource contract')
    contract_bytes = checked(manifest['protocol'], 65536)
    contract = json.loads(contract_bytes)
    output = Path(output)
    if output.exists() or not output.parent.resolve().is_relative_to(OWNER): raise ValueError('new private output required')
    output.mkdir(mode=0o700)
    records = {'contract': manifest['protocol'], 'image': manifest['images'][0]['source'], **contract['sources']}
    source_bytes = {name: checked(record) for name, record in records.items()}
    pre = {name: {'path': record['path'], 'sha256': sha(source_bytes[name]), 'bytes': len(source_bytes[name])}
           for name, record in records.items()}
    pre['reconstruct'] = {'path': __file__, 'sha256': sha(Path(__file__).read_bytes())}
    write_json(output/'bindings-before.json', pre)
    original = primitives(source_bytes['original_worker'])
    receipt = json.loads(source_bytes['tile9_receipt'])
    if receipt['model'] != 'faster' or receipt['ordinal'] != 9 or receipt['tensor']['c_order_data_sha256'] != TENSOR_SHA:
        raise ValueError('exact frozen target receipt required')
    if manifest['images'][0]['id'] != receipt['image_id'] or pre['image']['sha256'] != receipt['image_source_sha256']:
        raise ValueError('image identity disagreement')
    with tifffile.TiffFile(io.BytesIO(source_bytes['image'])) as tf:
        if len(tf.series) != 1 or math.prod(tf.series[0].shape) > 80000000: raise ValueError('TIFF contract')
        data = tf.series[0].asarray()
    original_dtype = data.dtype.str
    pixels, resized, shape = original['prepare_image'](data)
    del data
    if list(shape) != receipt['image_shape_hw'] or list(resized) != receipt['rescaled_shape_hw']:
        raise ValueError('recorded dimensions disagree')
    (row, column), count = placement(list(resized), 9, receipt['rescaled_row'], receipt['rescaled_column'])
    roster = original['tile_roster'](*map(int, resized))
    if count != len(roster) or count != receipt['tile_count_expected'] or roster[9] != (row, column):
        raise ValueError('independent tile roster disagreement')
    tile = pixels[row:row+512, column:column+512]
    tensor, side = original['model_input'](tile, 'faster')
    identity = {'dtype': tensor.dtype.str, 'shape': list(tensor.shape), 'c_order_data_sha256': sha(tensor.tobytes(order='C'))}
    if side != receipt['resized_side'] or identity != {key: receipt['tensor'][key] for key in identity}:
        raise ValueError('reconstructed tensor differs: '+json.dumps(identity))
    if not np.isfinite(tensor).all(): raise ValueError('nonfinite reconstructed tensor')
    with (output/'tensor.npy').open('xb') as stream: np.save(stream, tensor, allow_pickle=False)
    saved = np.load(output/'tensor.npy', allow_pickle=False)
    if saved.dtype != tensor.dtype or saved.shape != tensor.shape or saved.tobytes() != tensor.tobytes():
        raise ValueError('saved tensor readback differs')
    post = {name: {'path': record['path'], 'sha256': sha(checked(record)), 'bytes': len(source_bytes[name])}
            for name, record in records.items()}
    post['reconstruct'] = {'path': __file__, 'sha256': sha(Path(__file__).read_bytes())}
    if pre != post: raise ValueError('source changed during reconstruction')
    write_json(output/'bindings-after.json', post)
    elapsed = time.monotonic()-started
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if elapsed > 60 or peak > 3221225472: raise ValueError('observed reconstruction budget exceeded')
    result = {'artifact_id': 'reiyah.multiorg.tile9-input-reconstruction', 'version': '0.1.0',
        'status': 'complete', 'completion_scope': 'one recorded input tensor reproduced; no inference',
        'image_id': receipt['image_id'], 'image_source_sha256': pre['image']['sha256'], 'image_dtype': original_dtype,
        'image_shape_hw': shape, 'rescaled_shape_hw': resized, 'padded_shape_hw': list(pixels.shape),
        'tile_ordinal': 9, 'rescaled_row': row, 'rescaled_column': column, 'tile_shape_hw': list(tile.shape),
        'roster_size': count, 'tensor': identity, 'matches_recorded_tensor': True,
        'tensor_file': {'path': 'tensor.npy', 'sha256': sha((output/'tensor.npy').read_bytes()), 'bytes': (output/'tensor.npy').stat().st_size},
        'sources_unchanged': True, 'functions_extracted': sorted(NAMES), 'model_files_read': 0, 'model_sessions': 0,
        'forbidden_model_modules_loaded': [name for name in ('onnx', 'onnxruntime', 'torch') if name in sys.modules],
        'python': sys.executable, 'versions': {name: importlib.metadata.version(name) for name in ('numpy','scikit-image','opencv-python-headless','tifffile')},
        'wall_seconds': elapsed, 'process_peak_rss_bytes_darwin': peak,
        'limits': ['Original preprocessing implementation reused, not an independent pixel algorithm.',
                   'Matches the recorded pre-session input bytes; does not attest to model-runtime internal input consumption.',
                   'The upstream application/export input contract is not proven by a Reiyah tensor match.']}
    if result['forbidden_model_modules_loaded']: raise ValueError('unexpected model module')
    write_json(output/'result.json', result)
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', action='store_true', required=True)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(); os.umask(0o077)
    execute(args.manifest, args.output)
