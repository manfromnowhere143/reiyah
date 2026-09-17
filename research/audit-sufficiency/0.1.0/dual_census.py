"""Solver-free (dual) robustness tier over the supported census units at each epsilon.

Usage: python -B dual_census.py UNIT_DIR CENSUS_RESULTS_JSON OUT_JSON --epsilons 0.1 0.25 0.5 1.0 [--workers N]
Per unit and epsilon: sound, dual and solver max drops and the dual status. Aggregates only.
"""
import json, os, sys, time
from multiprocessing import Pool
from localization import GeoCase


def one(args):
    path, eps_list = args
    raw = json.load(open(path))
    out = {'unit': raw['comparison_id'], 'by_epsilon': {}}
    for eps in eps_list:
        t0 = time.perf_counter()
        c = GeoCase(raw, eps).certificate(realize=False)
        out['by_epsilon'][eps] = {k: c.get(k) for k in ('margin', 'sound_max_drop', 'sound', 'dual_max_drop', 'dual', 'solver_max_drop', 'status')}
        out['by_epsilon'][eps]['seconds'] = round(time.perf_counter() - t0, 2)
    return out


def main():
    unit_dir, census, out = sys.argv[1:4]
    eps = []
    for v in sys.argv[sys.argv.index('--epsilons') + 1:]:
        if v.startswith('--'):
            break
        eps.append(v)
    workers = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 4
    units = sorted(r['unit'] for r in json.load(open(census))['rows'] if r['criterion'] == 'supported')
    files = [(os.path.join(unit_dir, u + '.json'), eps) for u in units]
    rows = []
    t0 = time.perf_counter()
    with Pool(workers) as pool:
        for i, r in enumerate(pool.imap_unordered(one, files, chunksize=2), 1):
            rows.append(r)
            if i % 50 == 0 or i == len(files):
                print('done', i, 'of', len(files), round(time.perf_counter() - t0, 1), flush=True)
                json.dump({'epsilons': eps, 'rows': rows, 'complete': i == len(files)}, open(out, 'w'), indent=1)


if __name__ == '__main__':
    main()
