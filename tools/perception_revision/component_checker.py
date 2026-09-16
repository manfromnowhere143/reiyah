"""Check local matching proofs and exact global deletion-budget extrema.

No matching solver, MILP solver, selector or producer is invoked. Input parsing,
world semantics, component partitioning and work screening are shared trusted
code; exhaustive independent loss tests exercise this boundary.
"""
from fractions import Fraction

from tools.perception_decision.checker import _assignment, _cardinality, _keys, _require
from .component_plan import VERSION, make_plan, variants
from .contract import encoded, rational


def combine(curves, budget):
    """Exact extrema with one shared at-most budget, not a budget per anchor."""
    if budget >= sum(max(curve) for curve in curves):
        return (sum((min(lo for lo, _ in curve.values()) for curve in curves), Fraction(0)),
                sum((max(hi for _, hi in curve.values()) for curve in curves), Fraction(0)))
    totals = {0: (Fraction(0), Fraction(0))}
    for curve in curves:
        following = {}
        for used, (low, high) in totals.items():
            for local, (clow, chigh) in curve.items():
                count = used + local
                if count > budget:
                    continue
                lo, hi = low + clow, high + chigh
                if count in following:
                    lo, hi = min(lo, following[count][0]), max(hi, following[count][1])
                following[count] = (lo, hi)
        totals = following
    return min(v[0] for v in totals.values()), max(v[1] for v in totals.values())


def intervals(case, domains, proof):
    """Return (intervals, exact), or None for a checked resource-limit proof."""
    plan = make_plan(case, domains)
    if plan.limit:
        _require(encoded(proof) == encoded({'kind': 'component_resource_limit',
                 'version': VERSION, 'reason': plan.limit}), 'False component work-limit proof')
        return None
    _keys(proof, ('kind', 'version', 'worlds'))
    _require(proof['kind'] == 'component_deletions' and proof['version'] == VERSION,
             'Unknown component proof or version')
    _require(type(proof['worlds']) is list and len(proof['worlds']) == len(plan.worlds),
             'Missing or invented component world')
    supplied = {}
    for row in proof['worlds']:
        _keys(row, ('assignment', 'components'))
        _assignment(row['assignment'], case['model']['variables'])
        bits = tuple(row['assignment'])
        _require(bits not in supplied, 'Repeated component world')
        supplied[bits] = row['components']
    _require(set(supplied) == {w.bits for w in plan.worlds}, 'Permitted joint world omitted')
    fn, fp = (rational(case['loss'][key]) for key in ('false_negative', 'false_positive'))
    weights = {a['id']: rational(a['weight']) for a in case['anchors']}
    offset = -fp * sum(weights[a['id']] * (len(a['output_b']['value']) -
                      len(a['output_a']['value'])) for a in case['anchors'])
    results = []
    exact = True
    for world in plan.worlds:
        rows = supplied[world.bits]
        _require(type(rows) is list and len(rows) == len(world.components), 'Component omitted or invented')
        curves = []
        for c, method, row in zip(world.components, world.methods, rows):
            _keys(row, ('anchor', 'objects', 'kind') if c.cancels else
                       ('anchor', 'objects', 'kind', 'variants'))
            _require(row['anchor'] == c.anchor and encoded(row['objects']) == encoded(sorted(c.objects)),
                     'Component identity or partition changed')
            if c.cancels:
                _require(row['kind'] == 'equal_outputs', 'Equal graphs must cancel')
                continue
            _require(row['kind'] == method and type(row['variants']) is list,
                     'Component method does not follow the checked work plan')
            enumerated = method == 'enumerated'
            exact &= enumerated
            expected = list(variants(c, world.budget)) if enumerated else [()]
            _require(len(row['variants']) == len(expected), 'Local deletion state omitted or invented')
            curve = {}
            for removed, entry in zip(expected, row['variants']):
                _keys(entry, ('deletions', 'output_a', 'output_b'))
                _require(encoded(entry['deletions']) == encoded(list(removed)),
                         'Local deletion identity or coverage changed')
                present = c.objects - set(removed)
                sizes = []
                for role, left in (('output_a', c.output_a), ('output_b', c.output_b)):
                    edges = {(d, o) for d, o in c.edges if d in left and o in present}
                    sizes.append(_cardinality(entry[role], set(left), present, edges))
                value = weights[c.anchor] * (fn + fp) * (sizes[1] - sizes[0])
                count = len(removed)
                lo, hi = curve.get(count, (value, value))
                curve[count] = min(lo, value), max(hi, value)
            if not enumerated:
                # A deletion removes at most one match from either role. The
                # common-output bound also holds for every remaining subset.
                # Protected edges in this checked matching survive every free
                # deletion. These are enclosures, not attained extrema.
                free = set(c.free)
                vulnerable_a, vulnerable_b = (sum(o in free for _, o in row['variants'][0][r]['matching'])
                                              for r in ('output_a', 'output_b'))
                p, q = len(c.output_a - c.output_b), len(c.output_b - c.output_a)
                gain = sizes[1] - sizes[0]
                unit = weights[c.anchor] * (fn + fp)
                curve = {}
                for count in range(min(len(c.free), world.budget) + 1):
                    lo = max(-p, gain - count, gain - min(count, vulnerable_b))
                    hi = min(q, gain + count, gain + min(count, vulnerable_a))
                    _require(lo <= hi, 'Invalid conservative component bound')
                    curve[count] = unit * lo, unit * hi
            curves.append(curve)
        lo, hi = combine(curves, world.budget)
        results.append((offset + lo, offset + hi))
    return results, exact
