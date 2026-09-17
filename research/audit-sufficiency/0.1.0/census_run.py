"""Certified robustness census over rebuilt decision units.

For every unit: the exact decision and criterion; for supported units the arithmetic floor
(robust to any floor-1 deletions), the carrier structure and additive-pool cut (proven lower
bound on a sufficient audit), a certified sufficient set from the addition-adjacent policy with
the solver-tier stopping rule (upper bound), and a Monte Carlo comparator: the fraction of
random deletion sets of size floor and 2*floor that overturn the criterion.

Usage: python -B census_run.py UNIT_DIR OUT_JSON [--workers N] [--limit N]
Aggregate rows only; no annotation identities are written.
"""
import hashlib
import json
import os
import random
import sys
import time
from fractions import Fraction
from multiprocessing import Pool

from sufficiency import Case, run_policy


def structure(case):
    delta = case.delta()
    unit = case.fn + case.fp
    carriers = pool = base_edge = 0
    for a in case.anchors:
        g = a.gain()
        base_set = set(a.base)
        for o in a.objects_with_edge:
            if g - a.gain(frozenset([o])) == 1:
                carriers += 1
                if any(d in base_set for d in a.object_edges[o]):
                    base_edge += 1
                else:
                    pool += 1
    steps = {a.weight * unit for a in case.anchors}
    step = steps.pop()
    margin = delta - case.tolerance
    k_floor = int(-(-margin // step)) if margin > 0 else 0
    lb = max(0, pool - k_floor + 1) if k_floor and pool >= k_floor else (0 if not k_floor else None)
    return delta, k_floor, carriers, base_edge, pool, lb


def monte_carlo(case, k, trials, rng):
    labels = case.labels
    if k <= 0 or k > len(labels):
        return None
    crossed = 0
    for _ in range(trials):
        s = frozenset(rng.sample(labels, k))
        if case.delta(s) <= case.tolerance:
            crossed += 1
    return crossed / trials


def one(path):
    t0 = time.perf_counter()
    raw = json.load(open(path))
    case = Case(raw)
    delta, k_floor, carriers, base_edge, pool, lb = structure(case)
    row = {'unit': raw['comparison_id'], 'base': raw['comparison_id'].split('__')[0],
           'addition': raw['comparison_id'].split('__')[1], 'scene': raw['cohort_id'],
           'frames': len(case.anchors), 'labels': len(case.labels),
           'base_detections': sum(len(a.base) for a in case.anchors),
           'additions': sum(len(a.additions) for a in case.anchors),
           'delta': str(delta), 'criterion': case.criterion(delta), 'k_floor': k_floor,
           'carriers': carriers, 'carriers_with_base_edge': base_edge, 'additive_pool': pool,
           'audit_lower_bound': lb}
    if case.criterion(delta) == 'supported' and case.labels:
        rng = random.Random(int(hashlib.sha256(raw['comparison_id'].encode()).hexdigest()[:8], 16))
        rec = run_policy(case, 'addition_adjacent', batch=20)
        row.update({'audit_upper_bound': rec['confirmed'] if rec['solver'] == 'sufficient' else None,
                    'upper_bound_status': rec['solver'], 'policy_rounds': rec['rounds'],
                    'mc_cross_rate_at_floor': monte_carlo(case, k_floor, 200, rng),
                    'mc_cross_rate_at_2x_floor': monte_carlo(case, 2 * k_floor, 200, rng),
                    'floor_share_of_labels': round(k_floor / len(case.labels), 4)})
        # exact: at the floor, a crossing set exists iff the pool has >= floor members
        # (sufficient condition) or the solver finds one under budget = floor
        row['exact_crossing_at_floor'] = ('pool' if pool >= k_floor else
                                          case.certificate(budget=k_floor)['solver'] == 'insufficient')
    row['seconds'] = round(time.perf_counter() - t0, 1)
    return row


def main():
    unit_dir, out = sys.argv[1], sys.argv[2]
    workers = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 4
    limit = int(sys.argv[sys.argv.index('--limit') + 1]) if '--limit' in sys.argv else None
    files = sorted(os.path.join(unit_dir, f) for f in os.listdir(unit_dir) if f.endswith('.json') and f != 'INDEX.json')
    if limit:
        files = files[:limit]
    t0 = time.perf_counter()
    rows = []
    with Pool(workers) as pool:
        for i, row in enumerate(pool.imap_unordered(one, files, chunksize=2), 1):
            rows.append(row)
            if i % 50 == 0 or i == len(files):
                print('done', i, 'of', len(files), round(time.perf_counter() - t0, 1), 's', flush=True)
                json.dump({'rows': rows, 'seconds': round(time.perf_counter() - t0, 1), 'complete': i == len(files)},
                          open(out, 'w'), indent=1)
    json.dump({'rows': rows, 'seconds': round(time.perf_counter() - t0, 1), 'complete': True}, open(out, 'w'), indent=1)


if __name__ == '__main__':
    main()
