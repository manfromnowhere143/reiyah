"""Reuse of actually obtained observations on a distinct comparison.

First comparison: (base, addition_1, scene). Second: (base, addition_2, scene), the same reference
records and the same detector A, a different detector B added. Observations obtained in the first
run (labels confirmed present; positions measured with a residual radius) are checked for
applicability record by record (same object identity in the second unit) and then supplied to
the second run. Reported: first-run cost, second-run cost fresh, second-run cost warm, and the
amortized total. Same selector, same checker, same declared oracle throughout. Confirmed-present
observations remain applicable under a model change because they are about the reference, not
the detectors; that is the claim being measured, not assumed.

Usage: python -B reuse_experiment.py UNIT_DIR CENSUS_RESULTS_JSON OUT_JSON [--limit N]
"""
import hashlib
import json
import os
import random
import sys
import time
from fractions import Fraction

from sufficiency import Case
from localization import GeoCase, _answer
import ihs

BATCH = 10
MAX_ROUNDS = 200


def deletion_guided(case, prior=frozenset()):
    """Counterexample-guided deletion audit starting from prior confirmed labels; returns (extra queries, confirmed)."""
    confirmed = set(prior)
    queries = rounds = 0
    cert = case.certificate(frozenset(confirmed))
    while cert['solver'] == 'insufficient' and rounds < MAX_ROUNDS:
        picks = [l for l in cert['_counterexample'] if l not in confirmed][:BATCH]
        if not picks:
            break
        for l in picks:
            queries += 1
            confirmed.add(l)
        rounds += 1
        cert = case.certificate(frozenset(confirmed))
    return queries, confirmed, cert['solver']


def localization_guided(geo, prior=None, residual=Fraction(1, 4)):
    confirmed = dict(prior or {})
    queries = rounds = 0
    cert = geo.certificate(confirmed, realize=False)
    while cert['status'].startswith('insufficient') and rounds < MAX_ROUNDS:
        picks = [m for m in cert['_moved'] if m not in confirmed][:BATCH]
        if not picks:
            break
        for k in picks:
            queries += 1
            confirmed[k] = _answer(geo, k, residual)
        rounds += 1
        cert = geo.certificate(confirmed, realize=False)
    return queries, confirmed, cert['status']


def main():
    unit_dir, census_path, out = sys.argv[1:4]
    limit = int(sys.argv[sys.argv.index('--limit') + 1]) if '--limit' in sys.argv else None
    rows = json.load(open(census_path))['rows']
    supported = {(r['base'], r['addition'], r['scene']) for r in rows if r['criterion'] == 'supported'}
    # pairs of supported units sharing base and scene with different additions, deterministic order
    triples = sorted(supported, key=lambda t: hashlib.sha256('__'.join(t).encode()).hexdigest())
    pairs = []
    seen = set()
    for b, a1, s in triples:
        for b2, a2, s2 in triples:
            if b2 == b and s2 == s and a2 != a1 and (b, s) not in seen:
                pairs.append(((b, a1, s), (b, a2, s)))
                seen.add((b, s))
                break
    if limit:
        pairs = pairs[:limit]
    results = []
    t0 = time.perf_counter()
    for first, second in pairs:
        u1 = json.load(open(os.path.join(unit_dir, '__'.join(first) + '.json')))
        u2 = json.load(open(os.path.join(unit_dir, '__'.join(second) + '.json')))
        c1, c2 = Case(u1), Case(u2)
        # deletion family
        q1, s1, st1 = deletion_guided(c1)
        labels2 = set(c2.labels)
        applicable = frozenset(l for l in s1 if l in labels2)
        q2_fresh, _, st2f = deletion_guided(c2)
        q2_warm, _, st2w = deletion_guided(c2, applicable)
        row = {'first': '__'.join(first), 'second': '__'.join(second),
               'deletion': {'first_queries': q1, 'first_status': st1, 'observations_obtained': len(s1),
                            'applicable_to_second': len(applicable), 'second_fresh_queries': q2_fresh, 'second_fresh_status': st2f,
                            'second_warm_extra_queries': q2_warm, 'second_warm_status': st2w,
                            'amortized_total_warm': q1 + q2_warm, 'independent_total': q1 + q2_fresh}}
        # localization family at 0.5 m, residual 0.25 m
        g1, g2 = GeoCase(u1, Fraction(1, 2)), GeoCase(u2, Fraction(1, 2))
        lq1, ls1, lst1 = localization_guided(g1)
        keys2 = {(a.id, o) for a in g2.anchors for o, _, _ in a.objects}
        lapp = {k: v for k, v in ls1.items() if k in keys2}
        lq2f, _, lst2f = localization_guided(g2)
        lq2w, _, lst2w = localization_guided(g2, lapp)
        row['localization_0.5m_residual_0.25m'] = {
            'first_queries': lq1, 'first_status': lst1, 'observations_obtained': len(ls1), 'applicable_to_second': len(lapp),
            'second_fresh_queries': lq2f, 'second_fresh_status': lst2f, 'second_warm_extra_queries': lq2w, 'second_warm_status': lst2w,
            'amortized_total_warm': lq1 + lq2w, 'independent_total': lq1 + lq2f}
        results.append(row)
        print(row['first'], '->', row['second'], 'del', q1, q2_fresh, q2_warm, '| loc', lq1, lq2f, lq2w, round(time.perf_counter() - t0, 1), flush=True)
        json.dump({'pairs': results, 'batch': BATCH, 'complete': False}, open(out, 'w'), indent=1)
    summary = {'pairs': len(results),
               'deletion_total_fresh': sum(r['deletion']['independent_total'] for r in results),
               'deletion_total_warm': sum(r['deletion']['amortized_total_warm'] for r in results),
               'deletion_second_saved_queries': sum(r['deletion']['second_fresh_queries'] - r['deletion']['second_warm_extra_queries'] for r in results),
               'localization_total_fresh': sum(r['localization_0.5m_residual_0.25m']['independent_total'] for r in results),
               'localization_total_warm': sum(r['localization_0.5m_residual_0.25m']['amortized_total_warm'] for r in results),
               'localization_second_saved_queries': sum(r['localization_0.5m_residual_0.25m']['second_fresh_queries'] - r['localization_0.5m_residual_0.25m']['second_warm_extra_queries'] for r in results)}
    json.dump({'pairs': results, 'batch': BATCH, 'summary': summary, 'complete': True, 'seconds': round(time.perf_counter() - t0, 1)}, open(out, 'w'), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
