"""Verify every row using fresh native evaluations of prefiltered predictions."""
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


def exact(actual, expected):
    assert json.dumps(actual, sort_keys=True, allow_nan=False) == json.dumps(expected, sort_keys=True, allow_nan=False)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fresh_counts(reference, rows, cutoff):
    gt = COCO(str(reference))
    selected = [dict(r, bbox=list(r['bbox'])) for r in rows if r['score'] >= cutoff]
    dt = gt.loadRes(selected)
    e = COCOeval(gt, dt, 'bbox')
    e.params.imgIds = sorted(gt.getImgIds())
    e.params.catIds = sorted(gt.getCatIds())
    e.params.iouThrs = np.array([0.5])
    e.params.maxDets = [100]
    e.params.areaRng = [[0, 10000000000]]
    e.params.areaRngLbl = ['all']
    e.evaluate()
    out = {str(i): {'TP': 0, 'FP': 0, 'FN': 0, 'ignored_detections': 0,
                    'submitted_after_cap': 0} for i in e.params.imgIds}
    for entry in e.evalImgs:
        if entry is None:
            continue
        target = out[str(entry['image_id'])]
        matched_true = 0
        for match, ignored in zip(entry['dtMatches'][0], entry['dtIgnore'][0]):
            target['submitted_after_cap'] += 1
            if bool(ignored):
                target['ignored_detections'] += 1
            elif match != 0:
                target['TP'] += 1
                matched_true += 1
            else:
                target['FP'] += 1
        target['FN'] += sum(not bool(x) for x in entry['gtIgnore']) - matched_true
    return out, {'raw_rows_above_cutoff': len(selected),
                 'derived_empty_images': len(gt.imgs) - len({r['image_id'] for r in selected}),
                 'roster_images': len(gt.imgs)}


def main():
    parser = argparse.ArgumentParser()
    for name in ('predictions', 'original', 'revised', 'run'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    folder = Path(__file__).parent
    protocol = json.loads((folder / 'protocol.json').read_bytes())
    for path, source in zip((args.predictions, args.original, args.revised), protocol['input_bindings']):
        assert path.stat().st_size == source['bytes'] and sha(path) == source['sha256']
    assert np.__version__ == '2.2.6' and importlib.metadata.version('pycocotools') == '2.0.11'
    package = Path(pycocotools.__file__).parent
    for name, digest in json.loads((folder / 'environment.json').read_bytes())['python_source_sha256'].items():
        assert sha(package / name) == digest
    rows = json.loads(args.predictions.read_bytes())
    retained = json.loads((args.run / 'private_counts.json').read_bytes())
    witnesses = json.loads((args.run / 'private_witnesses.json').read_bytes())
    result = json.loads((args.run / 'result.json').read_bytes())
    exact(result['protocol_sha256'], sha(folder / 'protocol.json'))
    computed = {}
    for name, path in [('original', args.original), ('revised', args.revised)]:
        computed[name] = {}
        for arm, cutoff in [('A', .25), ('B', .5)]:
            table, counts = fresh_counts(path, rows, cutoff)
            exact(table, retained[name][arm])
            exact(counts, result['configurations'][arm])
            exact({key: sum(r[key] for r in table.values()) for key in next(iter(table.values()))},
                  result['totals'][name][arm])
            computed[name][arm] = table
    image_ids = sorted(map(int, computed['original']['A']))
    exact([r['image_id'] for r in witnesses], image_ids)
    exact(result['image_count'], len(image_ids))
    lower = upper = original_delta = revised_delta = sensitive = 0
    for row in witnesses:
        key = str(row['image_id'])
        deltas = {}
        for reference in ('original', 'revised'):
            a, b = computed[reference]['A'][key], computed[reference]['B'][key]
            deltas[reference] = a['FP'] + a['FN'] - b['FP'] - b['FN']
        exact(row['delta'], deltas)
        exact(row['lower'], min(deltas.values()))
        exact(row['upper'], max(deltas.values()))
        assert row['lower_witness'] in deltas and row['upper_witness'] in deltas
        exact(deltas[row['lower_witness']], row['lower'])
        exact(deltas[row['upper_witness']], row['upper'])
        lower += min(deltas.values())
        upper += max(deltas.values())
        original_delta += deltas['original']
        revised_delta += deltas['revised']
        sensitive += min(deltas.values()) != max(deltas.values())
    interval = result['delta_interval']
    for key, value in [('lower', lower), ('upper', upper), ('all_original_delta', original_delta), ('all_revised_delta', revised_delta)]:
        exact(interval[key], value)
    exact(result['images_with_reference_sensitive_delta'], sensitive)
    decision = 'B' if lower > 0 else 'A' if upper < 0 else 'unresolved'
    exact(interval['robust_choice'], decision)
    if decision != 'unresolved':
        exact(interval['oracle_unit_cost_reveals']['minimum_reveals'], 0)
    elif revised_delta != 0:
        gains = ([r['delta']['revised'] - r['lower'] for r in witnesses] if revised_delta > 0
                 else [r['upper'] - r['delta']['revised'] for r in witnesses])
        required = -lower if revised_delta > 0 else upper
        sorted_gains = sorted(gains, reverse=True)
        m = interval['oracle_unit_cost_reveals']['minimum_reveals']
        assert type(m) is int and 1 <= m <= len(gains)
        assert sum(sorted_gains[:m]) > required
        assert sum(sorted_gains[:m - 1]) <= required
    else:
        exact(interval['oracle_unit_cost_reveals']['minimum_reveals'], None)
    # Type and value checks must reject plausible but false substitutions.
    for forged, correct in [(False, 0), (float(lower), lower), (lower + 1, lower),
                            (image_ids[:-1], image_ids)]:
        try:
            exact(forged, correct)
        except AssertionError:
            pass
        else:
            raise AssertionError('Known-bad value accepted')
    output = {'artifact_id': 'reiyah.threshold-reference-screen.verification', 'version': '0.1.0',
              'status': 'passed', 'fresh_prefiltered_native_evaluations': 4,
              'per_image_count_records_verified': len(image_ids) * 4,
              'sharp_per_image_endpoint_pairs_verified': len(witnesses),
              'numeric_type_value_membership_rejections': 4,
              'result_sha256': sha(args.run / 'result.json'),
              'private_counts_sha256': sha(args.run / 'private_counts.json'),
              'private_witnesses_sha256': sha(args.run / 'private_witnesses.json'),
              'verifier_sha256': sha(Path(__file__)),
              'wall_seconds': time.monotonic() - started,
              'scope': 'Separate control flow using the same native evaluator; not independent scientific review.'}
    with (args.run / 'verification.json').open('x') as stream:
        json.dump(output, stream, indent=2)
        stream.write('\n')
    print(json.dumps(output, indent=2), flush=True)


if __name__ == '__main__':
    main()
