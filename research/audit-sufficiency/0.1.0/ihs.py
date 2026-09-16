"""Implicit hitting set computation of a minimum sufficient audit set.

A confirmed set is sufficient when it intersects every admissible adverse deletion set.
The implicit hitting set method (Moreno-Centeno and Karp, 2013) alternates two exact steps:

  1. H = a minimum hitting set of the adverse sets K found so far (a MILP).
     |H| is a lower bound on every sufficient set, because every sufficient set hits K.
  2. Certify H with the adversary. If no adverse set survives, H is a minimum sufficient set.
     Otherwise shrink the surviving counterexample to an inclusion-minimal adverse set,
     add it to K, and repeat.

Every adverse set added to K is verified by exact recomputation to cross the tolerance, so
each lower bound is exact given that the hitting-set MILP is solved to optimality. The final
sufficiency claim inherits the solver tier of the certificate.

Usage: python -B ihs.py CASE_JSON PRIVATE_OUT_JSON PUBLIC_OUT_JSON [max_iterations] [seed_witness_count] [minimal_sets_per_iteration]
"""
from fractions import Fraction
import json
import random
import sys
import time

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

from sufficiency import Case


def minimal_adverse(case, deleted, margin):
    """Shrink a crossing deletion set to an inclusion-minimal crossing set.

    Only the touched anchor is recomputed per trial; per-anchor drops are kept incrementally.
    """
    by_anchor = {}
    for aid, o in deleted:
        by_anchor.setdefault(aid, set()).add(o)
    unit = case.fn + case.fp
    base_gain = {aid: case.by_id[aid].gain() for aid in by_anchor}
    current = {aid: set(s) for aid, s in by_anchor.items()}
    drop = {aid: case.by_id[aid].weight * unit * (base_gain[aid] - case.by_id[aid].gain(frozenset(s)))
            for aid, s in current.items()}
    total = sum(drop.values(), Fraction(0))
    assert total >= margin
    for aid in list(current):
        a = case.by_id[aid]
        for o in sorted(current[aid]):
            trial = current[aid] - {o}
            new_drop = a.weight * unit * (base_gain[aid] - a.gain(frozenset(trial))) if trial else Fraction(0)
            if total - drop[aid] + new_drop >= margin:
                current[aid] = trial
                total = total - drop[aid] + new_drop
                drop[aid] = new_drop
        if not current[aid]:
            del current[aid]
    return frozenset((aid, o) for aid, s in current.items() for o in s)


def min_hitting_set(labels, families, cuts=()):
    """Minimum set hitting every family; `cuts` are (label_list, minimum_count) cardinality rows."""
    index = {l: i for i, l in enumerate(labels)}
    n = len(labels)
    rows = len(families) + len(cuts)
    A = lil_matrix((rows, n))
    lo = np.ones(rows)
    for r, fam in enumerate(families):
        for l in fam:
            A[r, index[l]] = 1
    for k, (members, count) in enumerate(cuts):
        r = len(families) + k
        for l in members:
            A[r, index[l]] = 1
        lo[r] = count
    res = milp(c=np.ones(n), constraints=LinearConstraint(A.tocsr(), lo, np.full(rows, np.inf)),
               integrality=np.ones(n), bounds=Bounds(0, 1))
    assert res.status == 0, res.message
    return frozenset(l for l in labels if res.x[index[l]] > 0.5), int(round(res.fun))


def additive_pool_cut(case, margin):
    """Objects with no base edge whose single deletion removes one gain unit form a pool whose
    deletions are exactly additive (alternating-path argument). If deleting k of them crosses the
    margin, every sufficient set contains at least |pool| - k + 1 of them. Returns (pool, count)."""
    unit = case.fn + case.fp
    steps = {a.weight * unit for a in case.anchors}
    if len(steps) != 1:
        return None
    step = steps.pop()
    k = int(-(-margin // step))
    pool = []
    for a in case.anchors:
        g = a.gain()
        base_set = set(a.base)
        for o in a.objects_with_edge:
            if any(d in base_set for d in a.object_edges[o]):
                continue
            if g - a.gain(frozenset([o])) == 1:
                pool.append((a.id, o))
    if len(pool) < k:
        return None
    return pool, len(pool) - k + 1


def run(case, max_iterations=400, seed_count=20, log=print, per_iteration=20):
    started = time.perf_counter()
    delta = case.delta()
    margin = delta - case.tolerance
    labels = case.labels
    families = []
    history = []
    cut = additive_pool_cut(case, margin)
    cuts = [cut] if cut else []
    log('additive pool cut: %s' % ('none' if not cut else '%d of %d' % (cut[1], len(cut[0]))))
    # seed with minimal adverse sets shrunk from randomly permuted full adversary sets
    base = case.certificate()
    full = base['_counterexample']
    rng = random.Random(0)
    for _ in range(seed_count):
        perm = list(full)
        rng.shuffle(perm)
        fam = minimal_adverse(case, perm, margin)
        if fam not in families:
            families.append(fam)
    log('seeded %d minimal adverse sets, sizes %s' % (len(families), sorted(len(f) for f in families)[:10]))
    result = None
    for it in range(1, max_iterations + 1):
        H, lb = min_hitting_set(labels, families, cuts)
        cert = case.certificate(H)
        row = {'iteration': it, 'families': len(families), 'hitting_set_size': len(H), 'lower_bound': lb,
               'solver': cert['solver'], 'sound': cert['sound'],
               'seconds': round(time.perf_counter() - started, 1)}
        history.append(row)
        if cert['solver'] == 'sufficient':
            result = {'status': 'optimal', 'minimum_sufficient_set_size': len(H), 'iterations': it,
                      'families': len(families), 'pool_cut': None if not cut else [len(cut[0]), cut[1]], 'solver_tier': cert['solver'], 'sound_tier': cert['sound'],
                      'budget_49': case.certificate(H, budget=49)['solver'],
                      'seconds': round(time.perf_counter() - started, 1), '_set': sorted(H)}
            log('optimal at iteration %d: %d labels' % (it, len(H)))
            break
        added = 0
        counter = list(cert['_counterexample'])
        for k in range(per_iteration):
            perm = list(counter)
            if k:
                rng.shuffle(perm)
            fam = minimal_adverse(case, perm, margin)
            assert not (fam & H), 'counterexample must avoid the confirmed set'
            if fam not in families:
                families.append(fam)
                added += 1
        if it % 10 == 0 or it < 5:
            log('iter %d lb %d families %d added %d last minimal set %d' % (it, lb, len(families), added, len(fam)))
    if result is None:
        result = {'status': 'iteration_limit', 'lower_bound': history[-1]['lower_bound'],
                  'iterations': max_iterations, 'families': len(families),
                  'seconds': round(time.perf_counter() - started, 1), '_set': None}
    result['history'] = history
    result['delta'] = str(delta)
    result['margin'] = str(margin)
    return result


if __name__ == '__main__':
    case = Case(json.load(open(sys.argv[1])))
    max_it = int(sys.argv[4]) if len(sys.argv) > 4 else 400
    seeds = int(sys.argv[5]) if len(sys.argv) > 5 else 20
    per = int(sys.argv[6]) if len(sys.argv) > 6 else 20
    res = run(case, max_it, seeds, per_iteration=per)
    with open(sys.argv[2], 'w') as f:
        json.dump(res, f, indent=1, default=str)
    with open(sys.argv[3], 'w') as f:
        json.dump({k: v for k, v in res.items() if not k.startswith('_')}, f, indent=1, default=str)
    print(json.dumps({k: v for k, v in res.items() if k not in ('_set', 'history')}, indent=1, default=str))
