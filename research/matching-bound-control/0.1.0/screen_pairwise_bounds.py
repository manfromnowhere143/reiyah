"""Authored comparator control: pairwise IoU bounds versus greedy COCO AP50.

No inference, dataset, paper reproduction, or Reiyah performance experiment.
"""
from fractions import Fraction as F
from pathlib import Path
import contextlib
import hashlib
import importlib.metadata
import io
import itertools
import json
import time

import numpy as np
import pycocotools
from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval

ROOT = Path(__file__).parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def iou(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    intersection = max(F(0), min(ax+aw, bx+bw)-max(ax, bx)) * max(F(0), min(ay+ah, by+bh)-max(ay, by))
    return intersection / (aw*ah + bw*bh - intersection)


def greedy(matrix):
    used, matches = set(), []
    for row in matrix:
        eligible = [(v, j) for j, v in enumerate(row) if j not in used and v >= F(1, 2)]
        target = max(eligible)[1] if eligible else None
        matches.append(None if target is None else target+1)
        if target is not None:
            used.add(target)
    return matches


def exact_ap(matches):
    true_positives = 0
    points = []
    for index, target in enumerate(matches, 1):
        true_positives += target is not None
        points.append((F(true_positives, 2), F(true_positives, index)))
    return sum(max((precision for recall, precision in points if recall >= F(t, 100)), default=F(0))
               for t in range(101)) / 101


def max_count(matrix):
    counts = []
    for assignment in itertools.product([None, 0, 1], repeat=2):
        used = [v for v in assignment if v is not None]
        if len(set(used)) != len(used):
            continue
        if all(v is None or matrix[i][v] >= F(1, 2) for i, v in enumerate(assignment)):
            counts.append(len(used))
    return max(counts)


def main():
    began = time.perf_counter()
    plan_path = ROOT / 'PAIRWISE_BOUND_SCREEN_PLAN.json'
    require(sha(plan_path) == 'fd5a6d693378153f3d444506f609bebe7e1d6ce4876971204a2a8122edddc79a', 'Plan changed')
    plan = json.loads(plan_path.read_text())
    refs = [list(map(F, r)) for r in plan['references_xywh']]
    preds = [list(map(F, r)) for r in plan['predictions_xywh']]
    radii = list(map(F, plan['reference_iou_distance_radii']))
    nominal = [[iou(d, g) for g in refs] for d in preds]
    matrices = {'nominal': nominal,
                'pairwise_lower': [[max(F(0), v-radii[j]) for j, v in enumerate(row)] for row in nominal],
                'pairwise_upper': [[min(F(1), v+radii[j]) for j, v in enumerate(row)] for row in nominal]}
    require(all(matrices['pairwise_lower'][i][j] <= nominal[i][j] <= matrices['pairwise_upper'][i][j]
                for i in range(2) for j in range(2)), 'Invalid entrywise enclosure')
    package = Path(pycocotools.__file__).parent
    require(importlib.metadata.version('pycocotools') == '2.0.11', 'Unexpected evaluator version')
    require(sha(package/'cocoeval.py') == '988485f79624cd42ceed9335d284df4cdcdf7b3d583e052fcbed2dd6bccf0267', 'Evaluator changed')
    results = {}
    console = io.StringIO()
    with contextlib.redirect_stdout(console):
        for name, matrix in matrices.items():
            gt = COCO()
            gt.dataset = {'info': {}, 'images': [{'id': 1, 'width': 60, 'height': 30}],
                          'categories': [{'id': 1, 'name': 'authored'}],
                          'annotations': [{'id': j+1, 'image_id': 1, 'category_id': 1,
                                           'bbox': list(map(float, box)), 'area': float(box[2]*box[3]),
                                           'iscrowd': 0} for j, box in enumerate(refs)]}
            gt.createIndex()
            dt = gt.loadRes([{'image_id': 1, 'category_id': 1, 'bbox': list(map(float, box)),
                              'score': float(F(plan['prediction_scores'][i]))} for i, box in enumerate(preds)])
            evaluator = COCOeval(gt, dt, 'bbox')
            evaluator.params.iouThrs = np.array([.5])
            if name != 'nominal':
                # An explicitly authored overlap substitution; the official
                # evaluate/accumulate/matching implementation stays unchanged.
                evaluator.computeIoU = lambda image, category: np.array(matrix, dtype=float)
            evaluator.evaluate()
            evaluator.accumulate()
            require(np.allclose(evaluator.ious[(1, 1)], np.array(matrix, dtype=float), rtol=0, atol=1e-12), 'IoU mismatch')
            native = next(row for row in evaluator.evalImgs if row and row['aRng'] == [0, 10000000000.0])
            native_matches = [int(v) or None for v in native['dtMatches'][0]]
            exact_matches = greedy(matrix)
            require(native_matches == exact_matches, 'Greedy trace disagreement')
            exact = exact_ap(exact_matches)
            ap = float(evaluator.eval['precision'][0, :, 0, 0, -1].mean())
            require(abs(ap-float(exact)) < 1e-12, 'AP disagreement')
            results[name] = {'iou_matrix_rational': [[str(v) for v in row] for row in matrix],
                             'matched_reference_ids': exact_matches, 'AP50_exact': str(exact),
                             'AP50_native_fraction': ap, 'maximum_cardinality_matches': max_count(matrix)}
    require(results['nominal']['AP50_exact'] == '1', 'Nominal control failed')
    require(results['pairwise_upper']['AP50_exact'] == '51/101', 'Proposed failure not reproduced')
    result = {'artifact_id': 'reiyah.pairwise-bound-screen.result', 'version': '0.1.0',
              'status': 'authored_counterexample_verified', 'plan_sha256': sha(plan_path),
              'script_sha256': sha(Path(__file__)), 'evaluations': results,
              'claim': 'Elementwise overlap bounds alone do not yield valid AP bounds when fed to confidence-ordered greedy matching.',
              'witness': 'The nominal reference is itself an admissible zero-perturbation world, and its AP50 exceeds the value computed from the elementwise upper matrix.',
              'not_established': ['defect in the paper implementation or published results', 'empirical frequency',
                                  'novelty', 'Reiyah advantage', 'real workflow savings'],
              'method': 'Authored exact rational geometry and AP plus unchanged pycocotools matching/accumulation; injected overlap matrices disclosed.',
              'numpy': np.__version__, 'pycocotools': importlib.metadata.version('pycocotools'),
              'cocoeval_sha256': sha(package/'cocoeval.py'), 'wall_seconds': time.perf_counter()-began}
    with (ROOT/'PAIRWISE_BOUND_SCREEN_RESULT.json').open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write('\n')
    with (ROOT/'PAIRWISE_BOUND_SCREEN.log').open('x') as stream:
        stream.write(console.getvalue())
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
