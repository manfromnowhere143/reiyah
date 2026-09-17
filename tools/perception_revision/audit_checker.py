"""Conclude audit sufficiency from checked worlds, covers and deletion bounds.

Observations are supplied conditional premises. Their bytes do not authenticate
a reviewer or establish physical truth. No search or matching solver runs here.
"""
from fractions import Fraction
from itertools import combinations
from math import comb

from tools.perception_decision.checker import _assignment, _keys, _require
from .checker import checked_count_bounds, checked_delta, checked_worlds
from .contract import (MAX_AUDIT_VARIANTS, MAX_WORLDS, MAX_WORK, ROLES, admitted,
                       capacity, enabled, encoded, rational, wire)


def unavailable(case):
    if any(a[r]['state'] != 'observed' for a in case['anchors'] for r in ROLES):
        return 'input_blocked'
    if any(a['reference']['state'] == 'open' for a in case['anchors']):
        return 'open_reference'
    count, unit = capacity(case)
    if count > MAX_WORLDS or count * unit > MAX_WORK:
        return 'resource_limit'
    return None


def domain(case, request, env):
    """Keep joint worlds; an absent observation may already hold in a world."""
    present = {(a['id'], o['id']) for a in case['anchors'] for o in a['reference']['objects']
               if enabled(o['when'], env)}
    kept = {(o['anchor'], o['object']) for o in request['observations'] if o['outcome'] == 'present'}
    absent = {(o['anchor'], o['object']) for o in request['observations'] if o['outcome'] == 'absent'}
    required = absent & present
    if not kept <= present or len(required) > request['deletion_budget']:
        return None
    return frozenset(required), tuple(sorted(present - kept - required)), request['deletion_budget'] - len(required)


def edits(required, free, budget):
    for size in range(min(len(free), budget) + 1):
        for chosen in combinations(free, size):
            yield frozenset(required | set(chosen))


def enumeration_allowed(case, domains):
    total = 0
    _, unit = capacity(case)
    for required, free, budget in domains:
        for size in range(min(len(free), budget) + 1):
            total += comb(len(free), size)
            if total > MAX_AUDIT_VARIANTS or total * unit > MAX_WORK:
                return False
    return True


def deletion_set(value):
    _require(type(value) is list, 'Deletion members must be a list')
    keys = []
    for row in value:
        _keys(row, ('anchor', 'object'))
        _require(type(row['anchor']) is str and type(row['object']) is str, 'Malformed deletion identity')
        keys.append((row['anchor'], row['object']))
    _require(len(keys) == len(set(keys)), 'Repeated deletion')
    return frozenset(keys)


def bounded_interval(case, env, entries, required, free, budget):
    baseline, upper = checked_delta(case, env, entries, required)
    _require(baseline == upper, 'Audit requires finite reference graphs')
    fn, fp = (rational(case['loss'][k]) for k in ('false_negative', 'false_positive'))
    weights = {a['id']: rational(a['weight']) for a in case['anchors']}
    costs = sorted(((fn + fp) * weights[aid] for aid, _ in free), reverse=True)
    radius = sum(costs[:budget])
    protected_lower = protected_upper = Fraction(0)
    free_set = set(free)
    rows = {row['anchor']: row for row in entries}
    for a in case['anchors']:
        counts, protected = [], []
        for role in ROLES:
            matching = rows[a['id']][role]['matching']
            vulnerable = sum((a['id'], pair[1]) in free_set for pair in matching)
            counts.append(len(matching))
            protected.append(len(matching) - min(budget, vulnerable))
        offset = fp * (len(a['output_b']['value']) - len(a['output_a']['value']))
        protected_lower += weights[a['id']] * ((fn + fp) * (protected[1] - counts[0]) - offset)
        protected_upper += weights[a['id']] * ((fn + fp) * (counts[1] - protected[0]) - offset)
    count_lo, count_hi = checked_count_bounds(case)
    lower = max(baseline - radius, protected_lower, count_lo)
    upper = min(baseline + radius, protected_upper, count_hi)
    _require(lower <= upper, 'Inconsistent deletion enclosure')
    return lower, upper


def conclude(case, request, proof):
    """Normative proof checker. The producer may use it to serialize conclusions."""
    _require(type(proof) is dict, 'Audit proof must be an object')
    result = {'execution_status': 'succeeded', 'model_status': 'not_checked',
              'claim': 'improvement_supported', 'sufficiency': 'not_evaluated',
              'enclosure_kind': 'unavailable', 'bounds': None, 'counterexample_value': None,
              'observation_basis': request['observation_basis'],
              'supplied_observations': len(request['observations']),
              'deletion_budget': request['deletion_budget'], 'physical_coverage': 'not_established',
              'statistical_confidence_level': None, 'authority_state': 'research_only'}
    reason = unavailable(case)
    if reason is not None:
        _require(encoded(proof) == encoded({'kind': 'unavailable', 'reason': reason}), 'False unavailable reason')
        result['execution_status'] = {'input_blocked': 'input_blocked', 'open_reference': 'scope_unavailable',
                                      'resource_limit': 'resource_limited'}[reason]
        if reason == 'resource_limit':
            result['sufficiency'] = 'unresolved'
        return result
    tolerance = rational(case['loss']['tolerance'])
    if proof.get('kind') in ('monotone_deletions', 'monotone_unavailable'):
        from .monotone_checker import bounds as monotone_bounds, confirmation_lower_bound
        result.update(confirmed_present_lower_bound=None, minimum_confirmed_present_count=None)
        domains = [(bits, env, active) for bits, env in checked_worlds(case)
                   if (active := domain(case, request, env)) is not None]
        checked = monotone_bounds(case, domains, proof)
        if checked['limit'] is not None:
            limited = checked['limit'] == 'endpoint_work_limit'
            result.update(execution_status='resource_limited' if limited else 'scope_unavailable',
                          sufficiency='unresolved' if limited else 'not_evaluated')
        elif not checked['intervals']:
            result['model_status'] = 'inconsistent'
        else:
            lower = min(v[0] for v in checked['intervals'])
            upper = max(v[1] for v in checked['intervals'])
            adverse = checked['adverse']
            status = ('sufficient' if lower > tolerance else
                      'insufficient' if adverse is not None else 'unresolved')
            result.update(model_status='consistent', sufficiency=status,
                          enclosure_kind='exact_for_finite_error_family' if checked['exact'] else 'conservative_monotone_bound',
                          bounds={'lower': wire(lower), 'upper': wire(upper)},
                          counterexample_value=wire(adverse) if adverse is not None else None)
            floor = confirmation_lower_bound(case, request)
            result['confirmed_present_lower_bound'] = floor
            if floor is not None and len(request['observations']) == floor and status == 'sufficient':
                result['minimum_confirmed_present_count'] = floor
        return result
    if proof.get('kind') in ('component_deletions', 'component_resource_limit'):
        from .component_checker import intervals as component_intervals
        domains = [(bits, env, active) for bits, env in checked_worlds(case)
                   if (active := domain(case, request, env)) is not None]
        checked = component_intervals(case, domains, proof)
        if checked is None:
            result.update(execution_status='resource_limited', sufficiency='unresolved')
        else:
            intervals, exact = checked
            if not intervals:
                result['model_status'] = 'inconsistent'
            else:
                lower, upper = min(x[0] for x in intervals), max(x[1] for x in intervals)
                status = ('sufficient' if lower > tolerance else
                          'insufficient' if exact or upper <= tolerance else 'unresolved')
                result.update(model_status='consistent', sufficiency=status,
                              enclosure_kind='exact_for_finite_error_family' if exact else 'conservative_component_bound',
                              bounds={'lower': wire(lower), 'upper': wire(upper)})
        return result
    if proof.get('kind') == 'counterexample':
        _keys(proof, ('kind', 'assignment', 'deletions', 'anchors'))
        env = _assignment(proof['assignment'], case['model']['variables'])
        _require(admitted(case['model'], env), 'Inadmissible counterexample world')
        active = domain(case, request, env)
        _require(active is not None, 'World contradicts observations or error budget')
        required, free, budget = active
        removed = deletion_set(proof['deletions'])
        _require(required <= removed <= required | set(free) and len(removed - required) <= budget,
                 'Counterexample violates observations or deletion family')
        lower, upper = checked_delta(case, env, proof['anchors'], removed)
        _require(lower == upper and lower <= tolerance, 'Witness does not defeat strict improvement')
        result.update(model_status='consistent', sufficiency='insufficient',
                      enclosure_kind='counterexample_only', counterexample_value=wire(lower))
        return result
    _require(proof.get('kind') in ('bounded_deletions', 'enumerated_deletions'), 'Unknown audit proof')
    _keys(proof, ('kind', 'worlds'))
    _require(type(proof['worlds']) is list and len(proof['worlds']) <= MAX_WORLDS, 'Invalid audit worlds')
    domains = {bits: (env, selected) for bits, env in checked_worlds(case)
               if (selected := domain(case, request, env)) is not None}
    supplied = {}
    for row in proof['worlds']:
        _keys(row, ('assignment', 'anchors') if proof['kind'] == 'bounded_deletions' else ('assignment', 'variants'))
        _assignment(row['assignment'], case['model']['variables'])
        key = tuple(row['assignment'])
        _require(key not in supplied, 'Repeated joint world')
        supplied[key] = row
    _require(set(supplied) == set(domains), 'Audit omitted a permitted joint interpretation')
    if not domains:
        result['model_status'] = 'inconsistent'
        return result
    exact = proof['kind'] == 'enumerated_deletions'
    if exact:
        _require(enumeration_allowed(case, [v[1] for v in domains.values()]), 'Deletion enumeration exceeds work limit')
    intervals = []
    for bits, (env, (required, free, budget)) in domains.items():
        row = supplied[bits]
        if not exact:
            intervals.append(bounded_interval(case, env, row['anchors'], required, free, budget))
            continue
        variants = row['variants']
        _require(type(variants) is list and len(variants) <= MAX_AUDIT_VARIANTS, 'Malformed deletion variants')
        by_edit = {}
        for variant in variants:
            _keys(variant, ('deletions', 'anchors'))
            removed = deletion_set(variant['deletions'])
            _require(removed not in by_edit, 'Repeated deletion variant')
            by_edit[removed] = variant
        allowed = set(edits(required, free, budget))
        _require(set(by_edit) == allowed, 'A permitted deletion variant is missing or invented')
        for removed in allowed:
            intervals.append(checked_delta(case, env, by_edit[removed]['anchors'], removed))
    lower, upper = min(x[0] for x in intervals), max(x[1] for x in intervals)
    status = ('sufficient' if lower > tolerance else 'insufficient' if exact or upper <= tolerance else 'unresolved')
    result.update(model_status='consistent', sufficiency=status,
                  enclosure_kind='exact_for_finite_error_family' if exact else 'conservative_deletion_bound',
                  bounds={'lower': wire(lower), 'upper': wire(upper)})
    return result


def check(case, request, payload):
    _keys(payload, ('result', 'proof'))
    result = conclude(case, request, payload['proof'])
    _require(encoded(result) == encoded(payload['result']), 'Audit result not entailed by its proof')
    return result
