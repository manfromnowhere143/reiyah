"""Fair cost-to-checked-decision experiment under the frozen plan (PLAN_COST_EXPERIMENT.json).

Every selector uses the same checker, the same query costs and the same declared answer source.
A cheap sound proof is tried before any solver call each round and its time is charged. Queries
are counted until the first checked decision; nothing is subtracted afterwards.

Usage: python -B cost_experiment.py INPUT_DIR UNIT_DIR PRIVATE_OUT_DIR PUBLIC_OUT_JSON [--workers N]
"""
import hashlib
import json
import os
import random
import sys
import time
from fractions import Fraction
from multiprocessing import Pool

from sufficiency import Case, POLICIES
from localization import GeoCase, _answer
import ihs

PLAN = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'PLAN_COST_EXPERIMENT.json')))
BATCH = PLAN['budgets']['batch']
MAX_ROUNDS = PLAN['budgets']['max_rounds']


def seed_for(case_id, selector):
    return int(hashlib.sha256((case_id + selector).encode()).hexdigest()[:8], 16)


# ----------------------------------------------------------------- deletion family
def deletion_run(case, selector, case_id):
    rng = random.Random(seed_for(case_id, selector))
    confirmed = set()
    state = {}
    families = []
    queries = rounds = cert_calls = solver_calls = 0
    solver_seconds = select_seconds = cheap_seconds = 0.0
    t0 = time.perf_counter()
    labels = case.labels
    while True:
        # cheap sound proof first
        tc = time.perf_counter()
        margin = case.delta() - case.tolerance
        unit = case.fn + case.fp
        sound = Fraction(0)
        for a in case.anchors:
            free = sum(1 for o in a.objects_with_edge if (a.id, o) not in confirmed)
            sound += a.weight * unit * min(a.gain(), free)
        cheap_seconds += time.perf_counter() - tc
        cert_calls += 1
        if sound < margin:
            status = 'sufficient_by_sound_tier'
            break
        ts = time.perf_counter()
        cert = case.certificate(frozenset(confirmed))
        solver_seconds += time.perf_counter() - ts
        solver_calls += 1
        if cert['solver'] == 'sufficient':
            status = 'sufficient'
            break
        if cert['solver'] is None:
            status = 'solver_failed'
            break
        if rounds >= MAX_ROUNDS or len(confirmed) >= len(labels):
            status = 'budget_exhausted'
            break
        tsel = time.perf_counter()
        if selector == 'hitting_set_online':
            fam = ihs.minimal_adverse(case, cert['_counterexample'], margin)
            picks = []
            if fam:
                families.append(fam)
                hs, _ = ihs.min_hitting_set(labels, families)
                picks = [l for l in sorted(hs) if l not in confirmed][:BATCH]
                if not picks:
                    picks = sorted(fam)[:BATCH]
        elif selector == 'counterexample_guided':
            picks = [l for l in cert['_counterexample'] if l not in confirmed][:BATCH]
        else:
            picks = POLICIES[selector](case, confirmed, BATCH, rng, state)
        select_seconds += time.perf_counter() - tsel
        if not picks:
            status = 'no_candidates'
            break
        for l in picks:
            queries += 1
            confirmed.add(l)     # declared oracle: every label present
        rounds += 1
    return {'family': 'deletion', 'selector': selector, 'queries': queries, 'rounds': rounds,
            'status': status, 'certificate_calls': cert_calls, 'solver_calls': solver_calls,
            'solver_seconds': round(solver_seconds, 2), 'selection_seconds': round(select_seconds, 2),
            'cheap_proof_seconds': round(cheap_seconds, 3), 'wall_seconds': round(time.perf_counter() - t0, 2),
            'labels': len(labels)}


# ----------------------------------------------------------------- localization family
def localization_run(geo, selector, case_id, residual):
    rng = random.Random(seed_for(case_id, selector + str(residual)))
    confirmed = {}
    families = []
    queries = rounds = cert_calls = solver_calls = 0
    solver_seconds = select_seconds = cheap_seconds = 0.0
    t0 = time.perf_counter()
    all_keys = [(a.id, o) for a in geo.anchors for o, _, _ in a.objects]
    while True:
        tc = time.perf_counter()
        case = geo.case
        margin = case.delta() - case.tolerance
        unit = case.fn + case.fp
        sound = Fraction(0)
        for a in geo.anchors:
            c = {k[1]: v for k, v in confirmed.items() if k[0] == a.id}
            sound += a.weight * unit * min(a.gain(a.present), len(a.flippable(c)))
        cheap_seconds += time.perf_counter() - tc
        cert_calls += 1
        if sound < margin:
            status = 'robust_by_sound_tier'
            break
        ts = time.perf_counter()
        cert = geo.certificate(confirmed, realize=False)
        solver_seconds += time.perf_counter() - ts
        solver_calls += 1
        if cert['status'] == 'robust':
            status = 'robust'
            break
        if cert['status'] == 'solver_failed':
            status = 'solver_failed'
            break
        if rounds >= MAX_ROUNDS or len(confirmed) >= len(all_keys):
            status = 'budget_exhausted'
            break
        tsel = time.perf_counter()
        if selector == 'random':
            pool = [k for k in all_keys if k not in confirmed]
            rng.shuffle(pool)
            picks = pool[:BATCH]
        elif selector == 'boundary_first':
            counts = {}
            for a in geo.anchors:
                c = {k[1]: v for k, v in confirmed.items() if k[0] == a.id}
                for d, o, p in a.flippable(c):
                    if (a.id, o) not in confirmed:
                        counts[(a.id, o)] = counts.get((a.id, o), 0) + 1
            picks = sorted(counts, key=lambda k: (-counts[k], k))[:BATCH]
        elif selector == 'counterexample_guided':
            picks = [m for m in cert['_moved'] if m not in confirmed][:BATCH]
        elif selector == 'hitting_set_online':
            fam = frozenset(m for m in cert['_moved'] if m not in confirmed)
            picks = []
            if fam:
                families.append(fam)
                hs, _ = ihs.min_hitting_set(all_keys, families)
                picks = [k for k in sorted(hs) if k not in confirmed][:BATCH]
                if not picks:
                    picks = sorted(fam)[:BATCH]
        select_seconds += time.perf_counter() - tsel
        if not picks:
            status = 'no_candidates'
            break
        for k in picks:
            queries += 1
            confirmed[k] = _answer(geo, k, residual)
        rounds += 1
    return {'family': 'localization', 'epsilon': '0.5', 'residual': str(Fraction(residual)), 'selector': selector,
            'queries': queries, 'rounds': rounds, 'status': status, 'certificate_calls': cert_calls,
            'solver_calls': solver_calls, 'solver_seconds': round(solver_seconds, 2),
            'selection_seconds': round(select_seconds, 2), 'cheap_proof_seconds': round(cheap_seconds, 3),
            'wall_seconds': round(time.perf_counter() - t0, 2), 'labels': len(all_keys)}


def one(args):
    case_id, path, family, selector, residual = args
    raw = json.load(open(path))
    if family == 'deletion':
        rec = deletion_run(Case(raw), selector, case_id)
    else:
        rec = localization_run(GeoCase(raw, Fraction(1, 2)), selector, case_id, residual)
    rec['case'] = case_id
    return rec


def main():
    input_dir, unit_dir, private, out = sys.argv[1:5]
    workers = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 4
    os.makedirs(private, exist_ok=True)
    cases = [('first', os.path.join(input_dir, 'first_comparison.json')),
             ('second', os.path.join(input_dir, 'second_comparison.json')),
             ('forty', os.path.join(unit_dir, 'mapillary__megvii__scene-0101.json'))]
    cases += [(u, os.path.join(unit_dir, u + '.json')) for u in PLAN['cases']['census_sample']]
    jobs = []
    for cid, path in cases:
        has_xy = cid not in ('first', 'second')
        for sel in PLAN['selectors']['deletion']:
            jobs.append((cid, path, 'deletion', sel, None))
        if has_xy:
            for sel in PLAN['selectors']['localization']:
                for residual in (Fraction(0), Fraction(1, 4)):
                    jobs.append((cid, path, 'localization', sel, residual))
    t0 = time.perf_counter()
    rows = []
    with Pool(workers) as pool:
        for i, rec in enumerate(pool.imap_unordered(one, jobs), 1):
            rows.append(rec)
            print('done', i, 'of', len(jobs), rec['case'], rec['family'], rec['selector'], rec.get('residual', ''), rec['queries'], rec['status'], round(time.perf_counter() - t0, 1), flush=True)
            json.dump({'plan_sha256': hashlib.sha256(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'PLAN_COST_EXPERIMENT.json'), 'rb').read()).hexdigest(),
                       'rows': rows, 'complete': i == len(jobs)}, open(out, 'w'), indent=1)


if __name__ == '__main__':
    main()
