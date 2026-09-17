"""Summarize the certified robustness census and reconcile it with the research lane's census index.

Usage: python -B census_summary.py CENSUS_RESULTS_JSON FABLE_INDEX_JSON FABLE_CLOSED_JSON OUT_JSON
Writes aggregate tables only.
"""
import json
import statistics
import sys
from collections import Counter, defaultdict
from fractions import Fraction

rows = json.load(open(sys.argv[1]))['rows']
fable = json.load(open(sys.argv[2]))['units']
closed = {(u['base'], u['addition'], u['scene']): u for u in json.load(open(sys.argv[3]))['units']}
by_key = {(r['base'], r['addition'], r['scene']): r for r in rows}

# ------------------------------------------------ reconciliation with the research lane census
recon = {'units_compared': 0, 'decision_equal': 0, 'decision_differs': [], 'floor_equal': 0,
         'floor_differs': [], 'counts_equal': 0, 'counts_differ': [], 'status_equal': 0, 'status_differs': []}
for u in fable:
    key = (u['base'], u['addition'], u['scene'])
    r = by_key.get(key)
    if r is None:
        continue
    recon['units_compared'] += 1
    if Fraction(u['decision']) == Fraction(r['delta']):
        recon['decision_equal'] += 1
    else:
        recon['decision_differs'].append({'unit': r['unit'], 'fable': u['decision'], 'here': r['delta']})
    if (u['annotations'], u['base_detections'], u['additions']) == (r['labels'], r['base_detections'], r['additions']):
        recon['counts_equal'] += 1
    else:
        recon['counts_differ'].append({'unit': r['unit'], 'fable': [u['annotations'], u['base_detections'], u['additions']],
                                       'here': [r['labels'], r['base_detections'], r['additions']]})
    fk = u['k_floor'] if u['status'] != 'budget_exhausted' else closed[key]['k_floor']
    if u['status'] == 'unsupported_baseline':
        fk = 0
    if fk == r['k_floor']:
        recon['floor_equal'] += 1
    else:
        recon['floor_differs'].append({'unit': r['unit'], 'fable': fk, 'here': r['k_floor']})
    fs = 'supported' if u['status'] in ('certified_at_floor', 'budget_exhausted') else 'excluded'
    if fs == r['criterion']:
        recon['status_equal'] += 1
    else:
        recon['status_differs'].append({'unit': r['unit'], 'fable': u['status'], 'here': r['criterion']})

# ------------------------------------------------ census tables
supported = [r for r in rows if r['criterion'] == 'supported']
excluded = [r for r in rows if r['criterion'] == 'excluded']


def q(vals):
    vals = sorted(vals)
    if not vals:
        return None
    return {'n': len(vals), 'min': vals[0], 'p10': vals[int(0.1 * (len(vals) - 1))], 'median': vals[len(vals) // 2],
            'p90': vals[int(0.9 * (len(vals) - 1))], 'max': vals[-1], 'mean': round(statistics.mean(vals), 4)}


def share(r, k):
    return round(r[k] / r['labels'], 4) if r.get(k) is not None and r['labels'] else None


summary = {
    'units': len(rows), 'supported': len(supported), 'excluded': len(excluded),
    'reconciliation_with_research_lane_census': {k: (v if not isinstance(v, list) else {'count': len(v), 'first': v[:5]})
                                                 for k, v in recon.items()},
    'floor_deletions': q([r['k_floor'] for r in supported]),
    'floor_share_of_labels': q([r['floor_share_of_labels'] for r in supported]),
    'exact_crossing_at_floor': Counter(str(r['exact_crossing_at_floor']) for r in supported),
    'audit_lower_bound_share': q([share(r, 'audit_lower_bound') for r in supported if r['audit_lower_bound'] is not None]),
    'audit_upper_bound_share': q([share(r, 'audit_upper_bound') for r in supported if r.get('audit_upper_bound') is not None]),
    'upper_bound_status': Counter(str(r.get('upper_bound_status')) for r in supported),
    'interval_width_labels': q([r['audit_upper_bound'] - r['audit_lower_bound'] for r in supported
                                if r.get('audit_upper_bound') is not None and r['audit_lower_bound'] is not None]),
    'monte_carlo_cross_rate_at_floor': q([r['mc_cross_rate_at_floor'] for r in supported if r.get('mc_cross_rate_at_floor') is not None]),
    'monte_carlo_cross_rate_at_2x_floor': q([r['mc_cross_rate_at_2x_floor'] for r in supported if r.get('mc_cross_rate_at_2x_floor') is not None]),
    'units_where_random_never_crossed_at_floor_but_exact_set_exists': sum(
        1 for r in supported if r.get('mc_cross_rate_at_floor') == 0.0 and r['exact_crossing_at_floor'] in ('pool', True)),
    'units_where_random_never_crossed_at_2x_floor_but_exact_set_exists': sum(
        1 for r in supported if r.get('mc_cross_rate_at_2x_floor') == 0.0 and r['exact_crossing_at_floor'] in ('pool', True)),
    'carrier_pool_share': q([round(r['additive_pool'] / r['labels'], 4) for r in supported if r['labels']]),
    'seconds_per_supported_unit': q([r['seconds'] for r in supported]),
}
pairs = defaultdict(lambda: {'units': 0, 'supported': 0, 'floors': [], 'lb': [], 'ub': [], 'mc_zero_at_floor': 0})
for r in rows:
    p = pairs['%s -> +%s' % (r['base'], r['addition'])]
    p['units'] += 1
    if r['criterion'] == 'supported':
        p['supported'] += 1
        p['floors'].append(r['k_floor'])
        if r['audit_lower_bound'] is not None:
            p['lb'].append(share(r, 'audit_lower_bound'))
        if r.get('audit_upper_bound') is not None:
            p['ub'].append(share(r, 'audit_upper_bound'))
        if r.get('mc_cross_rate_at_floor') == 0.0:
            p['mc_zero_at_floor'] += 1
summary['by_pair'] = {k: {'units': v['units'], 'supported': v['supported'],
                          'median_floor': (sorted(v['floors'])[len(v['floors']) // 2] if v['floors'] else None),
                          'median_lower_bound_share': (sorted(v['lb'])[len(v['lb']) // 2] if v['lb'] else None),
                          'median_upper_bound_share': (sorted(v['ub'])[len(v['ub']) // 2] if v['ub'] else None),
                          'random_never_crossed_at_floor': v['mc_zero_at_floor']}
                      for k, v in sorted(pairs.items())}
json.dump(summary, open(sys.argv[4], 'w'), indent=1, default=str)
print(json.dumps({k: v for k, v in summary.items() if k != 'by_pair'}, indent=1, default=str))
print(json.dumps(summary['by_pair'], indent=1, default=str))
