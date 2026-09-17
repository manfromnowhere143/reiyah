"""Split-level (leaderboard) robustness margins for each ordered detector pair.

Declared aggregate: the pair verdict on the validation split is the equal-weight mean over the
150 scene decisions (frames equally weighted within a scene, as in the census); criterion:
strict improvement above tolerance 1/10.

Deletion. A deletion in scene s removes at most one gain unit, worth (a+b)/frames_s at scene
level and (a+b)/(frames_s * 150) at split level; the additive pool of scene s supplies pool_s such
deletions exactly. The adversary therefore takes the largest per-deletion steps first, across
scenes. The resulting minimum overturning count is exact when the pools suffice (every
supported unit's pool met its floor in the census) and otherwise a lower bound.

Localization. Per-scene solver maxima at epsilon add across scenes (the adversary acts
independently per scene), including excluded scenes, whose gain the adversary can still lower. The pair verdict is robust at epsilon when the sum is below the split
margin; solver-limit scenes contribute their sound bound and mark the row as bounded.

Usage: python -B split_level.py CENSUS_RESULTS_JSON LOCALIZATION_SUPPORTED_JSON LOCALIZATION_EXCLUDED_JSON OUT_JSON
"""
import json
import sys
from collections import defaultdict
from fractions import Fraction

census = json.load(open(sys.argv[1]))['rows']
loc = {r['unit']: r for r in json.load(open(sys.argv[2]))['rows']}
loc.update({r['unit']: r for r in json.load(open(sys.argv[3]))['rows']})
tol = Fraction(1, 10)
pairs = defaultdict(list)
for r in census:
    pairs['%s -> +%s' % (r['base'], r['addition'])].append(r)
out = {}
for pair, rows in sorted(pairs.items()):
    n = len(rows)
    delta = sum(Fraction(r['delta']) for r in rows) / n
    row = {'scenes': n, 'labels': sum(r['labels'] for r in rows), 'split_delta': str(delta),
           'criterion': 'supported' if delta > tol else 'excluded',
           'scenes_supported': sum(1 for r in rows if r['criterion'] == 'supported')}
    if delta > tol:
        margin = delta - tol
        steps = []
        for r in rows:
            step = Fraction(2, r['frames'] * n)
            steps.extend([step] * r['additive_pool'])
        steps.sort(reverse=True)
        acc = Fraction(0)
        k = None
        for i, s in enumerate(steps, 1):
            acc += s
            if acc >= margin:
                k = i
                break
        row['deletions_to_overturn'] = k
        row['deletions_share_of_labels'] = None if k is None else round(k / row['labels'], 5)
        row['deletion_bound_kind'] = 'exact_by_pool' if k is not None else 'pool_insufficient_lower_bound_only'
        eps_rows = {}
        for eps in ('0.1', '0.25', '0.5', '1.0'):
            drop = Fraction(0)
            bounded = 0
            for r in rows:
                e = loc[r['unit']]['by_epsilon'][eps]
                if e.get('solver_max_drop') is not None:
                    drop += Fraction(e['solver_max_drop']) / n
                else:
                    bounded += 1
                    if e.get('sound_max_drop') is not None:
                        drop += Fraction(e['sound_max_drop']) / n
                    else:
                        drop += (Fraction(r['delta']) + Fraction(r['additions'], r['frames'])) / n
            eps_rows[eps] = {'max_drop': str(drop), 'robust': drop < margin, 'scenes_bounded_not_solved': bounded}
        row['localization'] = eps_rows
        row['largest_robust_epsilon_m'] = max([float(e) for e, v in eps_rows.items() if v['robust']] or [0.0])
    out[pair] = row
json.dump(out, open(sys.argv[4], 'w'), indent=1)
for pair, row in out.items():
    if row['criterion'] == 'supported':
        print('%-28s delta %-8s scenes+ %3d  deletions %5s (%s%%)  robust to %.2f m  %s' % (
            pair, str(row['split_delta'])[:8], row['scenes_supported'], row['deletions_to_overturn'],
            None if row['deletions_share_of_labels'] is None else round(100 * row['deletions_share_of_labels'], 2),
            row['largest_robust_epsilon_m'], {e: v['robust'] for e, v in row['localization'].items()}))
    else:
        print('%-28s delta %-8s scenes+ %3d  excluded' % (pair, str(row['split_delta'])[:8], row['scenes_supported']))
