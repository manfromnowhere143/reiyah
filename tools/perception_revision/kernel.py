"""Proposal routines; every emitted calculation must pass the separate checker."""
import copy
from fractions import Fraction

from tools.perception_decision.kernel import _matching_certificate
from tools.perception_decision.checker import _cardinality
from .contract import (Invalid, MAX_WORLDS, MAX_WORK, ROLES, admitted, anchor_bounds,
                       capacity, encoded, graph, rational, require, wire, worlds)


def initial(case):
    return {'execution_status': 'succeeded', 'model_status': 'not_checked',
            'enclosure_kind': 'unavailable', 'bounds': None,
            'decision': {'improvement_criterion': 'not_evaluated', 'preference': 'not_evaluated'},
            'reference_scope': case['evidence_kind'], 'sampling_scope': 'fixed_selected_cohort',
            'statistical_confidence_level': None, 'physical_coverage': 'not_established',
            'authority_state': 'research_only'}


def classify(lower, upper, tolerance):
    criterion = 'supported' if lower > tolerance else 'excluded' if upper <= tolerance else 'unresolved'
    preference = ('prefer_b' if lower > tolerance else 'prefer_a' if upper < -tolerance else
                  'equivalent_within_tolerance' if lower >= -tolerance and upper <= tolerance else 'unresolved')
    return {'improvement_criterion': criterion, 'preference': preference}


def project_certificate(old, left, present, edges):
    """A surviving matching and restricted cover are sufficient only at equal size."""
    projected = {'matching': [pair for pair in old['matching'] if tuple(pair) in edges],
                 'cover': {'detections': [d for d in old['cover']['detections'] if d in left],
                           'objects': [o for o in old['cover']['objects'] if o in present]}}
    try:
        _cardinality(projected, left, present, edges)
    except Invalid:
        return None
    return projected


def produce(case, prior=None, counters=None):
    counters = counters if counters is not None else {'reused_certificates': 0, 'computed_certificates': 0}
    cache = {}
    if prior is not None:
        old_case, old_payload = prior
        from .checker import check
        check(old_case, old_payload)
        require(case['cohort_id'] == old_case['cohort_id']
                and {a['id'] for a in case['anchors']} == {a['id'] for a in old_case['anchors']},
                'REVALIDATION_COHORT', 'An anchor cannot silently disappear from the prior population')
        if old_payload['proof']['kind'] == 'enumerated':
            for world in old_payload['proof']['worlds']:
                env_key = tuple(sorted(zip(old_case['model']['variables'], world['assignment'])))
                for row in world['anchors']:
                    for role in ROLES:
                        cache[(env_key, row['anchor'], role)] = row[role]
    result = initial(case)
    missing = [{'anchor': a['id'], 'role': role, 'state': a[role]['state']}
               for a in case['anchors'] for role in ROLES if a[role]['state'] != 'observed']
    if missing:
        result['execution_status'] = 'input_blocked'
        return {'result': result, 'proof': {'kind': 'input_blocked', 'unavailable': missing}}
    fn, fp, tolerance = (rational(case['loss'][k]) for k in ('false_negative', 'false_positive', 'tolerance'))
    count, unit = capacity(case)
    if count > MAX_WORLDS or count * unit > MAX_WORK:
        assignment = case['model'].get('feasible_assignment', [False] * len(case['model']['variables']))
        witness = assignment if admitted(case['model'], dict(zip(case['model']['variables'], assignment))) else None
        lower = sum(rational(a['weight']) * anchor_bounds(a, fn, fp)[0] for a in case['anchors'])
        upper = sum(rational(a['weight']) * anchor_bounds(a, fn, fp)[1] for a in case['anchors'])
        result.update(execution_status='resource_limited', enclosure_kind='unconditional_count_bound',
                      model_status='consistent' if witness is not None else 'not_checked',
                      bounds={'lower': wire(lower), 'upper': wire(upper)})
        if witness is not None:
            result['decision'] = classify(lower, upper, tolerance)
        return {'result': result, 'proof': {'kind': 'count_bound', 'reason': 'resource_limit', 'feasible_assignment': witness}}
    proof_worlds, lows, highs = [], [], []
    for bits, env in worlds(case['model']):
        low = high = Fraction(0)
        rows = []
        for a in case['anchors']:
            weight = rational(a['weight'])
            if a['reference']['state'] == 'open':
                lo, hi = anchor_bounds(a, fn, fp)
                low += weight * lo
                high += weight * hi
                continue
            present, edges = graph(a, env)
            row = {'anchor': a['id']}
            sizes = []
            for role in ROLES:
                left = {d['id'] for d in a[role]['value']}
                selected = {(d, o) for d, o in edges if d in left}
                old = cache.get((tuple(sorted(env.items())), a['id'], role))
                cert = project_certificate(old, left, present, selected) if old is not None else None
                if cert is None:
                    cert = _matching_certificate(left, selected)
                    counters['computed_certificates'] += 1
                else:
                    counters['reused_certificates'] += 1
                row[role] = copy.deepcopy(cert)
                sizes.append(len(cert['matching']))
            delta = (fn + fp) * (sizes[1] - sizes[0]) - fp * (len(a['output_b']['value']) - len(a['output_a']['value']))
            low += weight * delta
            high += weight * delta
            rows.append(row)
        proof_worlds.append({'assignment': list(bits), 'anchors': rows})
        lows.append(low)
        highs.append(high)
    if not proof_worlds:
        result['model_status'] = 'inconsistent'
    else:
        lower, upper = min(lows), max(highs)
        result.update(model_status='consistent',
                      enclosure_kind='conservative_open_reference' if any(a['reference']['state'] == 'open' for a in case['anchors']) else 'exact_for_finite_model',
                      bounds={'lower': wire(lower), 'upper': wire(upper)},
                      decision=classify(lower, upper, tolerance))
    return {'result': result, 'proof': {'kind': 'enumerated', 'worlds': proof_worlds}}
