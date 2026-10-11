"""Conventional threshold/reference screen with exact integer policy bounds."""
import argparse
import collections
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time

import numpy as np
import pycocotools
from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, obj):
    with path.open('x') as stream:
        json.dump(obj, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def verify_inputs(predictions, original, revised):
    study = Path(__file__).resolve().parent
    protocol = json.loads((study / 'protocol.json').read_bytes())
    for path, binding in zip((predictions, original, revised), protocol['input_bindings']):
        assert path.stat().st_size == binding['bytes']
        assert digest(path) == binding['sha256']
    assert np.__version__ == '2.2.6'
    assert importlib.metadata.version('pycocotools') == '2.0.11'
    package = Path(pycocotools.__file__).parent
    expected = json.loads((study / 'environment.json').read_bytes())['python_source_sha256']
    for name, value in expected.items():
        assert digest(package / name) == value
    return protocol, {p.name: digest(p) for p in package.iterdir() if p.suffix in ('.py', '.so')}


def evaluate(reference, predictions):
    gt = COCO(str(reference))
    dt = gt.loadRes(str(predictions)) if isinstance(predictions, Path) else gt.loadRes(predictions)
    evaluator = COCOeval(gt, dt, 'bbox')
    evaluator.params.imgIds = sorted(gt.getImgIds())
    evaluator.params.catIds = sorted(gt.getCatIds())
    evaluator.params.iouThrs = np.array([0.5])
    evaluator.params.areaRng = [[0, 10000000000]]
    evaluator.params.areaRngLbl = ['all']
    evaluator.params.maxDets = [100]
    evaluator.evaluate()
    return gt, evaluator


def count_table(evaluator, cutoff):
    table = {int(i): {'TP': 0, 'FP': 0, 'FN': 0, 'ignored_detections': 0,
                      'submitted_after_cap': 0} for i in evaluator.params.imgIds}
    for row in evaluator.evalImgs:
        if row is None:
            continue
        selected = np.asarray(row['dtScores']) >= cutoff
        ignored = row['dtIgnore'][0].astype(bool)
        matched = row['dtMatches'][0] > 0
        tp = int(np.sum(selected & ~ignored & matched))
        fp = int(np.sum(selected & ~ignored & ~matched))
        ng = int(np.sum(~row['gtIgnore'].astype(bool)))
        assert 0 <= tp <= ng
        counts = table[int(row['image_id'])]
        counts['TP'] += tp
        counts['FP'] += fp
        counts['FN'] += ng - tp
        counts['ignored_detections'] += int(np.sum(selected & ignored))
        counts['submitted_after_cap'] += int(np.sum(selected))
    return table


def summarize_worlds(tables, image_ids):
    rows = []
    for image_id in image_ids:
        world = {}
        for reference in ('original', 'revised'):
            a, b = tables[reference]['A'][image_id], tables[reference]['B'][image_id]
            world[reference] = (a['FP'] + a['FN']) - (b['FP'] + b['FN'])
        lower, upper = min(world.values()), max(world.values())
        rows.append({'image_id': image_id, 'delta': world, 'lower': lower, 'upper': upper,
                     'lower_witness': min(world, key=world.get),
                     'upper_witness': max(world, key=world.get)})
    lower, upper = sum(r['lower'] for r in rows), sum(r['upper'] for r in rows)
    decision = 'B' if lower > 0 else 'A' if upper < 0 else 'unresolved'
    completed = sum(r['delta']['revised'] for r in rows)
    oracle = None
    if decision != 'unresolved':
        oracle = {'minimum_reveals': 0, 'reason': 'Conventional initial bounds already decide.'}
    elif completed != 0:
        if completed > 0:
            gains = sorted((r['delta']['revised'] - r['lower'] for r in rows), reverse=True)
            margin = lower
        else:
            gains = sorted((r['upper'] - r['delta']['revised'] for r in rows), reverse=True)
            margin = -upper
        count = 0
        for gain in gains:
            margin += gain
            count += 1
            if margin > 0:
                break
        assert margin > 0
        oracle = {'minimum_reveals': count, 'reason': 'Full-information largest endpoint gains; unit costs only.'}
    else:
        oracle = {'minimum_reveals': None, 'reason': 'Completed reference is tied; no strict winner.'}
    return rows, {'lower': lower, 'upper': upper, 'robust_choice': decision,
                  'all_original_delta': sum(r['delta']['original'] for r in rows),
                  'all_revised_delta': completed, 'oracle_unit_cost_reveals': oracle}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--predictions', type=Path, required=True)
    parser.add_argument('--original', type=Path, required=True)
    parser.add_argument('--revised', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    protocol, package_hashes = verify_inputs(args.predictions, args.original, args.revised)
    args.output.mkdir(parents=True, exist_ok=False)
    references = {name: json.loads(path.read_bytes()) for name, path in
                  [('original', args.original), ('revised', args.revised)]}
    image_specs = lambda d: {i['id']: (i['width'], i['height']) for i in d['images']}
    category_specs = lambda d: {c['id']: c['name'] for c in d['categories']}
    assert image_specs(references['original']) == image_specs(references['revised'])
    assert category_specs(references['original']) == category_specs(references['revised'])
    image_ids = sorted(image_specs(references['original']))
    raw = json.loads(args.predictions.read_bytes())
    assert set(r['image_id'] for r in raw) == set(image_ids)
    output_counts = {}
    for arm, cutoff in [('A', 0.25), ('B', 0.50)]:
        counts = collections.Counter()
        for row in raw:
            if row['score'] >= cutoff:
                assert row['bbox'][2] > 0 and row['bbox'][3] > 0
                counts[row['image_id']] += 1
        output_counts[arm] = {'raw_rows_above_cutoff': sum(counts.values()),
                              'derived_empty_images': len(image_ids) - len(counts),
                              'roster_images': len(image_ids)}
    del raw
    tables, times = {}, {}
    for name, reference in [('original', args.original), ('revised', args.revised)]:
        before = time.monotonic()
        gt, evaluator = evaluate(reference, args.predictions)
        tables[name] = {arm: count_table(evaluator, cutoff) for arm, cutoff in [('A', .25), ('B', .50)]}
        times[name] = time.monotonic() - before
        del gt, evaluator
    rows, interval = summarize_worlds(tables, image_ids)
    totals = {ref: {arm: {metric: sum(row[metric] for row in table.values())
                         for metric in ('TP', 'FP', 'FN', 'ignored_detections', 'submitted_after_cap')}
                    for arm, table in arms.items()} for ref, arms in tables.items()}
    result = {'artifact_id': 'reiyah.threshold-reference-screen.result', 'version': '0.1.0',
              'lifecycle_status': 'exploratory', 'image_count': len(image_ids),
              'configurations': output_counts, 'totals': totals, 'delta_interval': interval,
              'images_with_reference_sensitive_delta': sum(r['lower'] != r['upper'] for r in rows),
              'protocol_sha256': digest(Path(__file__).with_name('protocol.json')),
              'scope': 'Two fixed score-file configurations under a declared finite reference-policy family. Conventional bounds, no Reiyah arm or actual human-work saving.'}
    dump(args.output / 'result.json', result)
    dump(args.output / 'private_counts.json', tables)
    dump(args.output / 'private_witnesses.json', rows)
    dump(args.output / 'execution.json', {'wall_seconds': time.monotonic() - started,
         'reference_stage_seconds': times, 'package_sha256': package_hashes,
         'source_sha256': digest(Path(__file__)), 'numpy': np.__version__,
         'pycocotools': importlib.metadata.version('pycocotools')})
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
