#!/usr/bin/env python3
"""Authored finite AUGRC baseline. No engine imports, source payloads or network.

Integer shared-label contrast bounds and covering certificates, based on
Kuboyama, arXiv:2609.18622v1. This is not the author's implementation.
"""
import argparse
from collections import Counter
from functools import lru_cache
import gzip
import hashlib
from itertools import combinations, permutations, product
import json
from pathlib import Path

PROTOCOL_SHA256 = 'e3e134d7423a721fd673ee021cd5404f6b32cee7d0cefad322179a33899afd0d'


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


def read_protocol(path):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != PROTOCOL_SHA256:
        raise ValueError('protocol binding mismatch')
    return json.loads(data)


def validate_candidate(prediction, ranks):
    n = len(prediction)
    if not n or len(ranks) != n:
        raise ValueError('candidate length')
    if any(type(x) is not int or x not in (0, 1) for x in prediction):
        raise ValueError('prediction must be observed binary integers')
    if any(type(x) is not int or not 0 <= x < n for x in ranks):
        raise ValueError('rank domain')
    if set(ranks) != set(range(max(ranks) + 1)):
        raise ValueError('ranks must be dense ordered groups')


def validate_history(history, n):
    if len(history) != n or any(type(x) is not int or x not in (0, 1, 2) for x in history):
        raise ValueError('history must explicitly distinguish unknown from observed labels')


@lru_cache(None)
def coefficients(prediction, ranks):
    validate_candidate(prediction, ranks)
    n = len(prediction)
    weights = tuple(2*n - sum(r < rank for r in ranks) - sum(r <= rank for r in ranks)
                    for rank in ranks)
    constant = sum(w*p for w, p in zip(weights, prediction))
    slope = tuple(w*(1-2*p) for w, p in zip(weights, prediction))
    return constant, slope


def candidates(n):
    ranks = [r for r in product(range(n), repeat=n)
             if set(r) == set(range(max(r)+1))]
    return [(p, r) for p in product((0, 1), repeat=n) for r in ranks]


def record(identifier, models):
    n, k = len(models[0][0]), len(models)
    coeff = [coefficients(*m) for m in models]
    pairs = list(combinations(range(k), 2))
    contrast = [(coeff[j][0]-coeff[t][0], tuple(a-b for a,b in zip(coeff[j][1],coeff[t][1])))
                for j,t in pairs]
    histories = list(product((0,1,2), repeat=n))
    worlds = list(product((0,1), repeat=n))
    subsets = sorted(range(1 << n), key=lambda m: (m.bit_count(), m))
    orders = list(permutations(range(n)))

    @lru_cache(None)
    def bounds_winner(h):
        out = []
        for c, b in contrast:
            known = c + sum(b[i]*(v-1) for i,v in enumerate(h) if v)
            out.append((known + sum(min(0,b[i]) for i,v in enumerate(h) if not v),
                        known + sum(max(0,b[i]) for i,v in enumerate(h) if not v)))
        for q in range(k):
            if all((out[z][0] > 0 if t == q else out[z][1] <= 0)
                   for z,(j,t) in enumerate(pairs) if j == q or t == q):
                return out, q
        return out, None

    @lru_cache(None)
    def policy(h):
        if bounds_winner(h)[1] is not None:
            return 0, None
        choices = []
        for i,v in enumerate(h):
            if not v:
                children = [h[:i]+(label,)+h[i+1:] for label in (1,2)]
                choices.append((1+max(policy(child)[0] for child in children), i))
        return min(choices)

    def path(y, order=None):
        h = (0,)*n
        used = 0
        while bounds_winner(h)[1] is None:
            i = policy(h)[1] if order is None else order[used]
            h = h[:i]+(y[i]+1,)+h[i+1:]
            used += 1
        return used

    risks = [[c + sum(a*v for a,v in zip(b,y)) for c,b in coeff] for y in worlds]
    certificates = []
    for y, ry in zip(worlds, risks):
        q = min(range(k), key=lambda j: (ry[j], j))
        constraints = []
        for j in range(k):
            if j == q:
                continue
            c = coeff[j][0]-coeff[q][0]
            b = tuple(a-d for a,d in zip(coeff[j][1],coeff[q][1]))
            lower = c + sum(min(0, v) for v in b)
            demand = max(0, (1 if j < q else 0)-lower)
            gains = tuple(v*z-min(0,v) for v,z in zip(b,y))
            constraints.append((demand, gains))
        certificate = next(mask.bit_count() for mask in subsets
                           if all(sum(g for i,g in enumerate(gains) if mask & (1<<i)) >= demand
                                  for demand,gains in constraints))
        certificates.append(certificate)
    width_order = sorted(range(n), key=lambda i: (-max(abs(b[i]) for _,b in contrast), i))
    return {
        'id': identifier,
        'candidates': [{'prediction': list(p), 'ranks': list(r)} for p,r in models],
        'risks': risks,
        'histories': [{'bounds': bounds_winner(h)[0], 'winner': bounds_winner(h)[1],
                       'depth': policy(h)[0], 'query': policy(h)[1]} for h in histories],
        'certificates': certificates,
        'policy_queries': [path(y) for y in worlds],
        'fixed_queries': [[path(y, order) for order in orders] for y in worlds],
        'width_queries': [path(y, width_order) for y in worlds],
    }


class Summary:
    def __init__(self):
        self.counts = Counter()
        self.histograms = {name: Counter() for name in (
            'certificate_size', 'fixed_queries', 'fixed_minus_certificate',
            'width_queries', 'width_minus_certificate', 'adaptive_queries',
            'adaptive_minus_certificate', 'minimax_minus_max_certificate')}

    def add(self, row):
        self.counts.update(cases=1, histories=len(row['histories']), labelings=len(row['risks']),
                           fixed_paths=sum(map(len,row['fixed_queries'])))
        self.counts['resolved_histories'] += sum(h['winner'] is not None for h in row['histories'])
        hist = self.histograms
        depth = row['histories'][0]['depth']
        if depth != max(row['policy_queries']):
            raise ValueError('adaptive depth/path mismatch')
        hist['minimax_minus_max_certificate'][depth-max(row['certificates'])] += 1
        for cert, fixed, width, adaptive in zip(row['certificates'], row['fixed_queries'],
                                               row['width_queries'], row['policy_queries']):
            hist['certificate_size'][cert] += 1
            for name, values in (('fixed', fixed), ('width',[width]), ('adaptive',[adaptive])):
                for value in values:
                    if value < cert:
                        raise ValueError('acquisition undercuts hindsight minimum')
                    hist[name+'_queries'][value] += 1
                    hist[name+'_minus_certificate'][value-cert] += 1

    def report(self):
        return {'counts': dict(sorted(self.counts.items())),
                'histograms': {name: {str(k): v for k,v in sorted(hist.items())}
                               for name,hist in sorted(self.histograms.items())}}


def write_trace(path, rows):
    digest = hashlib.sha256()
    total = 0
    with path.open('wb') as raw:
        with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as target:
            for row in rows:
                data = canonical(row)
                digest.update(data)
                total += len(data)
                target.write(data)
    return {'uncompressed_sha256': digest.hexdigest(), 'uncompressed_bytes': total,
            'gzip_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'gzip_bytes': path.stat().st_size}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    protocol = read_protocol(Path(__file__).with_name('protocol.json'))
    args.output_dir.mkdir(parents=True, exist_ok=False)
    total, grids = Summary(), []

    def grid_rows():
        for grid in protocol['population']['grid']:
            n,k = grid['n'],grid['k']
            subtotal = Summary()
            pool = candidates(n)
            for index,models in enumerate(product(pool, repeat=k)):
                row = record([n,k,index], models)
                total.add(row)
                subtotal.add(row)
                yield row
            grids.append({'n':n,'k':k, **subtotal.report()})

    trace = write_trace(args.output_dir/'trace.jsonl.gz', grid_rows())
    named_rows, named_results = [], []
    for case in protocol['named_cases']:
        n,k = len(case['labels']),len(case['prediction'])
        row = record([n,k,case['id']], list(zip(map(tuple,case['prediction']),map(tuple,case['ranks']))))
        named_rows.append(row)
        label_index = list(product((0,1),repeat=n)).index(tuple(case['labels']))
        order_index = list(permutations(range(n))).index(tuple(case['order']))
        ry = row['risks'][label_index]
        named_results.append({'id':case['id'], 'scaled_risks':ry, 'scale':2*n*n,
            'winner':min(range(k), key=lambda j:(ry[j],j)),
            'minimum_certificate':row['certificates'][label_index],
            'declared_order_queries':row['fixed_queries'][label_index][order_index],
            'width_queries':row['width_queries'][label_index],
            'adaptive_queries':row['policy_queries'][label_index],
            'minimax_depth':row['histories'][0]['depth'],
            'maximum_certificate':max(row['certificates']),
            'initial_universal_winner':row['histories'][0]['winner']})
    named_trace = write_trace(args.output_dir/'named.jsonl.gz', iter(named_rows))
    result = {'artifact_id':'reiyah.exact-choice-baseline.result','version':'0.1.0',
              'lifecycle_status':'exploratory','protocol_sha256':PROTOCOL_SHA256,
              'population':total.report(),'grids':grids,'named_cases':named_results,
              'trace':trace,'named_trace':named_trace,
              'scope':'Authored finite mathematical qualification; not measured human work or independent scientific replication.'}
    (args.output_dir/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'produced','counts':total.report()['counts'],'trace':trace}))


if __name__ == '__main__':
    main()
