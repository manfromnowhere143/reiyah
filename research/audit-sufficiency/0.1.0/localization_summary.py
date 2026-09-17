"""Aggregate the localization-robustness census. Usage: python -B localization_summary.py IN_JSON OUT_JSON"""
import json
import sys
from collections import Counter, defaultdict

d = json.load(open(sys.argv[1]))
rows = d['rows']


def q(vals):
    vals = sorted(vals)
    if not vals:
        return None
    return {'n': len(vals), 'min': vals[0], 'p10': vals[int(0.1 * (len(vals) - 1))], 'median': vals[len(vals) // 2],
            'p90': vals[int(0.9 * (len(vals) - 1))], 'max': vals[-1]}


summary = {'supported_units': len(rows), 'epsilons': d['epsilons'], 'by_epsilon': {}, 'by_pair': {}}
for eps in d['epsilons']:
    k = str(eps)
    st = Counter(r['by_epsilon'][k]['status'] for r in rows)
    audits = [r['by_epsilon'][k]['audit_guided'] for r in rows if 'audit_guided' in r['by_epsilon'][k]]
    sizes = [a['confirmed_positions'] for a in audits if 'confirmed_positions' in a]
    shares = [a['confirmed_positions'] / r['labels'] for r in rows for a in [r['by_epsilon'][k].get('audit_guided')] if a and 'confirmed_positions' in a]
    summary['by_epsilon'][k] = {
        'status': dict(st),
        'robust_share': round(st.get('robust', 0) / len(rows), 4),
        'boundary_objects_share_of_labels': q([round(r['by_epsilon'][k]['boundary_objects'] / r['labels'], 4) for r in rows if r['labels']]),
        'audit_positions': q(sizes), 'audit_share_of_labels': q([round(s, 4) for s in shares]),
        'audit_final_status': dict(Counter(a.get('final_status', 'timed_out') for a in audits)),
        'seconds': q([r['by_epsilon'][k]['seconds'] for r in rows])}
pairs = defaultdict(lambda: defaultdict(Counter))
for r in rows:
    base, add, _ = r['unit'].split('__')
    for eps in d['epsilons']:
        pairs['%s -> +%s' % (base, add)][str(eps)][r['by_epsilon'][str(eps)]['status']] += 1
summary['by_pair'] = {p: {e: dict(c) for e, c in v.items()} for p, v in sorted(pairs.items())}
json.dump(summary, open(sys.argv[2], 'w'), indent=1)
print(json.dumps({k: v for k, v in summary.items() if k != 'by_pair'}, indent=1))
