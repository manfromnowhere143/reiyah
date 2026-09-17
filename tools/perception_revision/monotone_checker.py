"""Check addition-audit extrema without matching, search, or solver calls.

Shared eligibility for common detections is guaranteed by the input contract.
For A subset B, the matching-rank difference is monotone in the reference set.
Deleting all free objects is a lower bound even if that exceeds the error budget;
it is an attained endpoint only when the single shared budget admits it.
"""
from tools.perception_decision.checker import _assignment, _keys, _require
from .checker import checked_delta
from .contract import encoded, rational
from .monotone_plan import VERSION, admission


def confirmation_lower_bound(case, request):
    """Necessary count for all-present audits with every other deletion allowed.

    This is not a bound on arbitrary audit policies, contradictory answers or
    bounded-error requests. Attainment requires a separately checked sufficient
    request with exactly this many confirmed-present observations.
    """
    if (case['model']['variables'] or case['model']['clauses']
            or any(o['outcome'] != 'present' for o in request['observations'])
            or request['deletion_budget'] < sum(len(a['reference']['objects']) for a in case['anchors'])):
        return None
    weights = {rational(a['weight']) for a in case['anchors']}
    if len(weights) != 1:
        return None
    weight = next(iter(weights))
    fn, fp = (rational(case['loss'][key]) for key in ('false_negative', 'false_positive'))
    step = weight * (fn + fp)
    if step == 0:
        return None
    offset = fp * sum(rational(a['weight']) * (len(a['output_b']['value']) -
                      len(a['output_a']['value'])) for a in case['anchors'])
    ratio = (rational(case['loss']['tolerance']) + offset) / step
    return max(0, ratio.numerator // ratio.denominator + 1)


def bounds(case, domains, proof):
    from .audit_checker import bounded_interval
    plan = admission(case, domains)
    if plan['reason'] is not None:
        expected = {'kind': 'monotone_unavailable', 'version': VERSION, **plan}
        _require(encoded(proof) == encoded(expected), 'False monotone admission outcome')
        return {'limit': plan['reason'], 'intervals': [], 'exact': False, 'adverse': None}
    _keys(proof, ('kind', 'version', 'worlds'))
    _require(proof['kind'] == 'monotone_deletions' and proof['version'] == VERSION,
             'Unknown monotone proof or version')
    _require(type(proof['worlds']) is list and len(proof['worlds']) == len(domains),
             'Compatible joint world omitted or invented')
    supplied = {}
    for row in proof['worlds']:
        _keys(row, ('assignment', 'lower', 'upper'))
        _assignment(row['assignment'], case['model']['variables'])
        bits = tuple(row['assignment'])
        _require(bits not in supplied, 'Repeated monotone world')
        supplied[bits] = row
    _require(set(supplied) == {bits for bits, _, _ in domains}, 'Wrong compatible joint worlds')
    intervals, attainable = [], []
    exact = True
    for bits, env, (required, free, budget) in domains:
        row = supplied[bits]
        lower, lower_hi = checked_delta(case, env, row['lower'], required | set(free))
        upper, upper_hi = checked_delta(case, env, row['upper'], required)
        _require(lower == lower_hi and upper == upper_hi and lower <= upper,
                 'Monotone endpoints are not ordered finite values')
        cheap_lo, cheap_hi = bounded_interval(case, env, row['upper'], required, free, budget)
        lo, hi = max(lower, cheap_lo), min(upper, cheap_hi)
        _require(lo <= hi and hi == upper, 'Bounds disagree with the admitted upper endpoint')
        lower_admitted = len(free) <= budget
        if lower_admitted:
            _require(lo == lower, 'A bound excludes the admitted lower endpoint')
            attainable.append(lower)
        # The upper endpoint deletes only required absences, hence is always admitted.
        attainable.append(upper)
        exact &= lower_admitted or lo == hi
        intervals.append((lo, hi))
    tolerance = rational(case['loss']['tolerance'])
    adverse = [value for value in attainable if value <= tolerance]
    return {'limit': None, 'intervals': intervals, 'exact': exact,
            'adverse': min(adverse) if adverse else None}
