"""Audit-cost-to-sufficient-verdict experiment on retained comparison cases.

Usage: python -B experiment.py INPUT_DIR PRIVATE_OUT_DIR PUBLIC_RESULTS_JSON

INPUT_DIR holds the sealed comparison inputs (private; nuScenes annotation tokens).
PRIVATE_OUT_DIR receives identity-bearing outputs (confirmed sets, counterexamples).
PUBLIC_RESULTS_JSON receives aggregate counts and timings only.

Everything is a computational assay on declared benchmark labels taken as the audit oracle,
plus an injected-error control. No human audit occurred; no claim about physical truth.
"""
from fractions import Fraction
import hashlib
import json
import random
import sys
import time
from pathlib import Path

from sufficiency import Case, POLICIES, run_policy, __version__

inputs = Path(sys.argv[1])
private = Path(sys.argv[2])
public_path = Path(sys.argv[3])
private.mkdir(parents=True, exist_ok=True)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pub(cert):
    return {k: v for k, v in cert.items() if not k.startswith('_')}


report = {'module_version': __version__, 'started': time.strftime('%Y-%m-%dT%H:%M:%S'),
          'inputs': {p.name: sha(p) for p in sorted(inputs.glob('*.json'))}, 'cases': {}}
t_all = time.perf_counter()

# ------------------------------------------------------------------ forty-frame case
before = json.load(open(inputs / 'BEFORE_INPUT.json'))
after = json.load(open(inputs / 'AFTER_INPUT.json'))
forty = Case(before)
keys_before = {(a['id'], o['id']) for a in before['anchors'] for o in a['reference']['objects']}
keys_after = {(a['id'], o['id']) for a in after['anchors'] for o in a['reference']['objects']}
witness1 = frozenset(keys_before - keys_after)
probe = json.load(open(inputs / 'DISJOINT_WITNESS_PROBE.json'))


def structure(case):
    """Carriers, provably additive pool, packing of disjoint floor witnesses."""
    delta = case.delta()
    unit = (case.fn + case.fp)
    carriers, pool, base_edge_carriers = [], [], []
    for a in case.anchors:
        g = a.gain()
        base_set = set(a.base)
        for o in a.objects_with_edge:
            if g - a.gain(frozenset([o])) == 1:
                carriers.append((a.id, o))
                if any(d in base_set for d in a.object_edges[o]):
                    base_edge_carriers.append((a.id, o))
                else:
                    pool.append((a.id, o))
    # smallest weighted step from one deletion (weights may differ across anchors)
    steps = sorted({a.weight * unit for a in case.anchors})
    margin = delta - case.tolerance
    k_floor = None
    if len(steps) == 1:
        k_floor = -(-margin // steps[0])
    # greedy packing of disjoint witnesses at the floor, each verified by full recomputation
    packing = []
    if k_floor is not None:
        used = set()
        while True:
            current = {a.id: set() for a in case.anchors}
            gains = {a.id: a.gain() for a in case.anchors}
            members = []
            for aid, o in carriers:
                if (aid, o) in used or len(members) >= k_floor:
                    continue
                a = case.by_id[aid]
                trial = current[aid] | {o}
                g = a.gain(frozenset(trial))
                if gains[aid] - g == 1:
                    current[aid] = trial
                    gains[aid] = g
                    members.append((aid, o))
            if len(members) < k_floor:
                break
            d = case.delta(frozenset(members))
            assert d == delta - k_floor * steps[0]
            if d > case.tolerance:
                break
            packing.append(members)
            used.update(members)
    return {'delta': str(delta), 'criterion': case.criterion(delta), 'margin': str(margin),
            'labels': len(case.labels), 'carriers': len(carriers),
            'carriers_with_base_edge': len(base_edge_carriers), 'additive_pool': len(pool),
            'k_floor': None if k_floor is None else int(k_floor),
            'disjoint_floor_witnesses_constructed': len(packing),
            'sufficient_audit_lower_bound': (None if k_floor is None else
                                             max(len(packing), len(pool) - int(k_floor) + 1)),
            '_pool': pool, '_packing': packing}


t = time.perf_counter()
s40 = structure(forty)
s40['seconds'] = round(time.perf_counter() - t, 2)
d_w1 = forty.delta(witness1)
w2 = frozenset((m['anchor'], m['object']) for m in probe['members']) if 'members' in probe else None
s40['witness1_size'] = len(witness1)
s40['witness1_delta'] = str(d_w1)
if w2:
    s40['codex_disjoint_witness_delta'] = str(forty.delta(w2))
    s40['codex_disjoint_witness_overlap'] = len(w2 & witness1)

# certificates for the two named confirmed sets under the declared family with budget 49
certs = {}
for name, conf in (('none', frozenset()), ('witness1', witness1), ('additive_pool', frozenset(s40['_pool']))):
    t = time.perf_counter()
    c_unb = forty.certificate(conf)
    c_b49 = forty.certificate(conf, budget=49)
    certs[name] = {'unbounded': pub(c_unb), 'budget_49': pub(c_b49),
                   'seconds': round(time.perf_counter() - t, 2)}
    (private / ('forty-cert-%s.json' % name)).write_text(json.dumps(
        {'confirmed': sorted(conf), 'unbounded': c_unb, 'budget_49': c_b49}, indent=1, default=str))

# ------------------------------------------------------------------ policies, unbounded family
policy_runs = []
plans = [('random', 0), ('random', 1), ('random', 2), ('degree', 0), ('addition_adjacent', 0),
         ('influence', 0), ('counterexample_guided', 0)]
for name, seed in plans:
    saved = private / ('forty-policy-%s-%d.json' % (name, seed))
    if saved.exists():
        rec = json.load(open(saved))
        rec['_confirmed'] = [tuple(l) for l in rec['_confirmed']]
        policy_runs.append({k: v for k, v in rec.items() if not k.startswith('_')})
        print('policy (saved)', name, seed, rec['queries'], rec['solver'], flush=True)
        continue
    rec = run_policy(forty, name, batch=10, seed=seed)
    final = forty.certificate(frozenset(rec['_confirmed']), budget=49)
    rec['budget_49_after'] = final['solver']
    policy_runs.append({k: v for k, v in rec.items() if not k.startswith('_')})
    (private / ('forty-policy-%s-%d.json' % (name, seed))).write_text(json.dumps(rec, indent=1, default=str))
    print('policy', name, seed, rec['queries'], rec['solver'], rec['seconds'], flush=True)

# ------------------------------------------------------------------ injected-error control
error_runs = []
for name in ('influence', 'counterexample_guided'):
    for seed in (0, 1):
        rng = random.Random(100 + seed)
        absent_plan = {l for l in forty.labels if rng.random() < 0.05}

        def oracle(label, absent_plan=absent_plan):
            return label not in absent_plan

        rec = run_policy(forty, name, batch=10, seed=seed, oracle=oracle)
        rec['planted_absent'] = len(absent_plan)
        error_runs.append({k: v for k, v in rec.items() if not k.startswith('_')})
        (private / ('forty-error-%s-%d.json' % (name, seed))).write_text(json.dumps(rec, indent=1, default=str))
        print('error', name, seed, rec['queries'], rec['absent_found'], rec['final_delta'], rec['solver'], flush=True)

# ------------------------------------------------------------------ reuse under a changed decision rule
reuse = []
base_run = json.load(open(private / 'forty-policy-counterexample_guided-0.json'))
prior = frozenset(tuple(l) for l in base_run['_confirmed'])
for label, fn, fp, tol in (('fn1_fp4', 1, 4, Fraction(1, 10)), ('fn4_fp1', 4, 1, Fraction(1, 10)),
                           ('fn1_fp1_tol1_2', 1, 1, Fraction(1, 2))):
    variant = forty.with_loss(Fraction(fn), Fraction(fp), tol)
    d = variant.delta()
    row = {'variant': label, 'delta': str(d), 'criterion': variant.criterion(d)}
    if variant.criterion(d) == 'supported':
        fresh = run_policy(variant, 'counterexample_guided', batch=10)
        warm = run_policy(variant, 'counterexample_guided', batch=10, confirmed=prior)
        row.update({'fresh_queries': fresh['queries'], 'fresh_solver': fresh['solver'],
                    'warm_prior_confirmed': len(prior), 'warm_extra_queries': warm['queries'],
                    'warm_solver': warm['solver'],
                    'prior_confirmed_still_applicable': True,
                    'note': 'same world and same observations; only loss or tolerance changed, so confirmed presence remains applicable'})
    else:
        row['note'] = 'criterion excluded under this rule; sufficiency of an exclusion is not modeled by the deletion family'
    reuse.append(row)
    print('reuse', row, flush=True)

# ------------------------------------------------------------------ ordinary cache versus full recomputation
t = time.perf_counter()
for _ in range(5):
    forty.delta()
full = (time.perf_counter() - t) / 5
touched = {aid for aid, _ in witness1}
t = time.perf_counter()
for _ in range(5):
    after_case = forty.without(witness1)
    # cached: recompute only touched anchors, reuse the rest
    total = Fraction(0)
    for a in after_case.anchors:
        if a.id in touched:
            total += a.weight * after_case.anchor_delta(a)
        else:
            total += a.weight * forty.anchor_delta(forty.by_id[a.id])
    assert total == d_w1
partial = (time.perf_counter() - t) / 5
cache = {'full_recompute_seconds': round(full, 4), 'touched_anchor_recompute_seconds': round(partial, 4),
         'touched_anchors': len(touched), 'note': 'wall time on one Mac for matching only; excludes source preparation, hashing, verification and any human work'}

report['cases']['forty_frame'] = {
    'structure': {k: v for k, v in s40.items() if not k.startswith('_')},
    'certificates': certs, 'policy_runs': policy_runs, 'injected_error_runs': error_runs,
    'reuse_under_changed_rule': reuse, 'cache_check': cache}
(private / 'forty-structure.json').write_text(json.dumps(s40, indent=1, default=str))

# ------------------------------------------------------------------ first and second cases
for name, fname in (('first', 'first_comparison.json'), ('second', 'second_comparison.json')):
    case = Case(json.load(open(inputs / fname)))
    s = structure(case)
    runs = []
    for pol in ('random', 'influence', 'counterexample_guided'):
        rec = run_policy(case, pol, batch=5)
        runs.append({k: v for k, v in rec.items() if not k.startswith('_')})
        (private / ('%s-policy-%s.json' % (name, pol))).write_text(json.dumps(rec, indent=1, default=str))
    report['cases'][name] = {'structure': {k: v for k, v in s.items() if not k.startswith('_')},
                             'policy_runs': runs}
    print(name, report['cases'][name]['structure'], flush=True)

report['seconds'] = round(time.perf_counter() - t_all, 1)
public_path.write_text(json.dumps(report, indent=1))
print(json.dumps(report, indent=1))
