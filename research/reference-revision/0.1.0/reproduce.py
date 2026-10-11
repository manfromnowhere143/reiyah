"""Replay four pinned COCO bbox evaluations, offline, on existing CPU resources.

Accepts only the exact inputs in inputs.json. This is a fixed-file reproduction
harness, not a general input validator, inference system or Reiyah comparison arm.
"""
import argparse
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
MODELS = ('r50', 'r101')
REFERENCES = {'original': 'instances_val2017.json', 'revised': 'instances_valrem.json'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def input_identity(data):
    manifest = read(ROOT / 'inputs.json')
    for row in manifest['files']:
        path = data / row['name']
        require(path.stat().st_size == row['bytes'] and sha(path) == row['sha256'],
                'Input identity mismatch: ' + row['name'])
    return {row['name']: row['sha256'] for row in manifest['files']}


def environment():
    import pycocotools
    manifest = read(ROOT / 'inputs.json')
    versions = {name: importlib.metadata.version(name) for name in manifest['dependencies']}
    require(versions == manifest['dependencies'], 'Use the pinned requirements.txt')
    package = Path(pycocotools.__file__).parent
    for name, expected in manifest['pure_python_package_sha256'].items():
        require(sha(package / name) == expected, 'Evaluator source changed: ' + name)
    # Native builds differ by platform; record their identities without claiming
    # that a different platform reproduced the original native environment.
    return {'python': sys.version, 'platform': platform.platform(), 'packages': versions,
            'package_sha256': {p.name: sha(p) for p in sorted(package.iterdir())
                               if p.is_file() and p.suffix in ('.py', '.so', '.pyd')}}


def worker(data, output, reference, model):
    began = time.perf_counter()
    identity = input_identity(data)
    env = environment()
    import numpy as np
    from pycocotools.coco import COCO
    from pycocotools.cocoeval import COCOeval
    gt = COCO(str(data / REFERENCES[reference]))
    dt = gt.loadRes(str(data / (model + '.json')))
    evaluator = COCOeval(gt, dt, 'bbox')
    require(len(evaluator.params.imgIds) == 5000 and len(evaluator.params.catIds) == 80,
            'Unexpected population')
    require(evaluator.params.maxDets == [1, 10, 100], 'Unexpected maxDets')
    require(np.allclose(evaluator.params.iouThrs, np.linspace(.5, .95, 10)) and
            np.allclose(evaluator.params.recThrs, np.linspace(0, 1, 101)), 'Unexpected thresholds')
    evaluator.evaluate()
    evaluator.accumulate()
    evaluator.summarize()
    names = ('AP', 'AP50', 'AP75', 'AP_small', 'AP_medium', 'AP_large',
             'AR1', 'AR10', 'AR100', 'AR_small', 'AR_medium', 'AR_large')
    precision = evaluator.eval['precision'][:, :, :, 0, 2]
    categories = {}
    for k, category in enumerate(evaluator.params.catIds):
        values = precision[:, :, k]
        valid = values[values > -1]
        categories[str(category)] = float(np.mean(valid)) if len(valid) else None
    observed_images = {row['image_id'] for row in dt.anns.values()}
    metrics = {'metrics_fraction_scale': dict(zip(names, map(float, evaluator.stats))),
               'category_AP_fraction_scale': categories,
               'absent_detection_image_ids': sorted(set(gt.imgs) - observed_images)}
    require(input_identity(data) == identity, 'Input changed during scoring')
    key = reference + '_' + model
    write(output / (key + '.json'), {
        'artifact_id': 'reiyah.reference-revision.replay.' + key, 'version': '0.1.0',
        'measurement': metrics, 'input_sha256': identity, 'environment': env,
        'script_sha256': sha(Path(__file__)), 'reference_annotations': len(gt.anns),
        'prediction_rows': len(dt.anns), 'rows_filtered': 0,
        'original_inference_completion': 'unverified',
        'missing_row_interpretation': 'No submitted detections; successful empty inference not established',
        'Reiyah_arm': 'not_run', 'human_work': 'not_measured',
        'scoring_seconds': time.perf_counter() - began,
        'timing_scope': 'Worker validation, imports, loading and scoring; excludes acquisition and human work'})


def compare(actual, expected, tolerance, path='result'):
    if isinstance(expected, dict):
        require(type(actual) is dict and actual.keys() == expected.keys(), path + ': key mismatch')
        for key in expected:
            compare(actual[key], expected[key], tolerance, path + '.' + key)
    elif isinstance(expected, list):
        require(type(actual) is list and len(actual) == len(expected), path + ': length mismatch')
        for i, value in enumerate(expected):
            compare(actual[i], value, tolerance, path + '.' + str(i))
    elif type(expected) is float:
        require(type(actual) in (float, int) and math.isfinite(actual) and
                abs(actual - expected) <= tolerance, path + ': numeric mismatch')
    else:
        require(type(actual) is type(expected) and actual == expected, path + ': value mismatch')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='Fresh directory outside the source tree')
    parser.add_argument('--worker-reference', choices=REFERENCES, help=argparse.SUPPRESS)
    parser.add_argument('--worker-model', choices=MODELS, help=argparse.SUPPRESS)
    args = parser.parse_args()
    data, output = args.data_dir.resolve(), args.output.resolve()
    require(not output.is_relative_to(ROOT.parents[2]), 'Keep run artifacts outside the repository')
    if args.worker_reference or args.worker_model:
        require(bool(args.worker_reference and args.worker_model), 'Incomplete worker specification')
        worker(data, output, args.worker_reference, args.worker_model)
        return
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    try:
        input_identity(data)
        environment()
        with (output / 'qualification.log').open('x') as log:
            subprocess.run([sys.executable, '-B', str(ROOT / 'qualify.py'),
                            '--data-dir', str(data), '--output', str(output / 'compatibility.json')],
                           stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                           check=True, timeout=60)
        write(output / 'started.json', {'script_sha256': sha(Path(__file__)),
              'inputs_manifest_sha256': sha(ROOT / 'inputs.json'),
              'expected_sha256': sha(ROOT / 'expected.json'), 'status': 'running'})
        expected = read(ROOT / 'expected.json')
        runs = {}
        for reference in REFERENCES:
            for model in MODELS:
                key = reference + '_' + model
                argv = [sys.executable, '-B', str(Path(__file__).resolve()),
                        '--data-dir', str(data), '--output', str(output),
                        '--worker-reference', reference, '--worker-model', model]
                with (output / (key + '.log')).open('x') as log:
                    subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT,
                                   stdin=subprocess.DEVNULL, check=True, timeout=180)
                runs[key] = read(output / (key + '.json'))['measurement']
        compare(runs, expected['runs'], expected['tolerance_fraction_scale'])
        gaps = {ref: 100 * (runs[ref + '_r101']['metrics_fraction_scale']['AP'] -
                           runs[ref + '_r50']['metrics_fraction_scale']['AP']) for ref in REFERENCES}
        require(all(gap > 1e-10 for gap in gaps.values()), 'Expected global ordering changed')
        reversals = []
        for cat in runs['original_r50']['category_AP_fraction_scale']:
            differences = [100 * (runs[ref + '_r101']['category_AP_fraction_scale'][cat] -
                                  runs[ref + '_r50']['category_AP_fraction_scale'][cat]) for ref in REFERENCES]
            if differences[0] * differences[1] < 0 and all(abs(v) > 1e-10 for v in differences):
                reversals.append(int(cat))
        # Per-category expected values, including categories with no reversal,
        # were checked above. No selection based on the four changed signs.
        result = {'artifact_id': 'reiyah.reference-revision.reproduction', 'version': '0.1.0',
                  'status': 'matched_retained_numeric_results', 'evaluations': len(runs),
                  'B_minus_A_AP_points': gaps, 'global_strict_order_reversal': False,
                  'descriptive_category_reversal_ids': reversals,
                  'wall_seconds': time.perf_counter() - started,
                  'scope': 'Fixed score files under two references; no independent scientific replication, Reiyah advantage or human work saving'}
        write(output / 'result.json', result)
        print(json.dumps(result, indent=2))
    except Exception as exc:
        write(output / 'failure.json', {'status': 'failed', 'exception': type(exc).__name__, 'detail': str(exc)})
        raise


if __name__ == '__main__':
    main()
