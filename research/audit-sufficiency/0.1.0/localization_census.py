"""Localization-robustness census over supported decision units.

Usage: python -B localization_census.py UNIT_DIR CENSUS_RESULTS_JSON OUT_JSON --epsilons 0.1 0.25 0.5 1.0 [--workers N]
For every supported unit and every epsilon: certificate status, solver max drop, boundary
counts, and for non-robust units the counterexample-guided position audit size. Aggregates only.
"""
import json
import os
import sys
import time
from multiprocessing import Pool

from localization import GeoCase, audit_counterexample_guided

def one(args):
    path, EPS = args
    raw = json.load(open(path))
    out = {'unit': raw['comparison_id'], 'labels': sum(len(a['reference']['objects']) for a in raw['anchors']), 'by_epsilon': {}}
    for eps in EPS:
        t0 = time.perf_counter()
        geo = GeoCase(raw, eps)
        cert = geo.certificate()
        row = {k: v for k, v in cert.items() if k in ('status', 'margin', 'solver_max_drop', 'sound', 'boundary_edges_unconfirmed', 'objects_moved', 'objects_unrealized', 'flips', 'achieved')}
        row['boundary_objects'] = len({(a.id, o) for a in geo.anchors for _, o, _ in a.boundary})
        if cert.get('status', '').startswith('insufficient'):
            if eps <= 0.5 or cert.get('boundary_edges_unconfirmed', 0) <= 1500:
                row['audit_guided'] = audit_counterexample_guided(geo, batch=20, max_rounds=40)
            else:
                row['audit_guided'] = {'skipped': 'more than 1500 boundary edges at this epsilon'}
        row['seconds'] = round(time.perf_counter() - t0, 2)
        out['by_epsilon'][str(eps)] = row
    return out


def main():
    unit_dir, census, out = sys.argv[1], sys.argv[2], sys.argv[3]
    EPS = []
    for v in sys.argv[sys.argv.index('--epsilons') + 1:]:
        if v.startswith('--'):
            break
        EPS.append(float(v))
    workers = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 4
    supported = [r['unit'] for r in json.load(open(census))['rows'] if r['criterion'] == 'supported']
    files = [os.path.join(unit_dir, u + '.json') for u in sorted(supported)]
    t0 = time.perf_counter()
    rows = []
    with Pool(workers) as pool:
        for i, row in enumerate(pool.imap_unordered(one, [(f, EPS) for f in files], chunksize=2), 1):
            rows.append(row)
            if i % 50 == 0 or i == len(files):
                print('done', i, 'of', len(files), round(time.perf_counter() - t0, 1), flush=True)
                json.dump({'epsilons': EPS, 'rows': rows, 'complete': i == len(files)}, open(out, 'w'), indent=1)


if __name__ == '__main__':
    main()
