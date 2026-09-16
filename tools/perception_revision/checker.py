"""Verify complete joint worlds and matching/cover witnesses without a matcher."""
from fractions import Fraction

from tools.perception_decision.checker import _assignment, _cardinality, _keys, _require
from .contract import Invalid, MAX_WORLDS, MAX_WORK, ROLES, admitted, capacity, encoded, rational, wire


def result_template(case):
    return {'execution_status': 'succeeded', 'model_status': 'not_checked',
            'enclosure_kind': 'unavailable', 'bounds': None,
            'decision': {'improvement_criterion': 'not_evaluated', 'preference': 'not_evaluated'},
            'reference_scope': case['evidence_kind'], 'sampling_scope': 'fixed_selected_cohort',
            'statistical_confidence_level': None, 'physical_coverage': 'not_established',
            'authority_state': 'research_only'}


def checked_classification(lower, upper, tolerance):
    criterion = 'unresolved'
    preference = 'unresolved'
    if upper <= tolerance:
        criterion = 'excluded'
    if lower > tolerance:
        criterion, preference = 'supported', 'prefer_b'
    elif upper < -tolerance:
        preference = 'prefer_a'
    elif lower >= -tolerance and upper <= tolerance:
        preference = 'equivalent_within_tolerance'
    return {'improvement_criterion': criterion, 'preference': preference}


def checked_worlds(case):
    names = case['model']['variables']
    for mask in range(1 << len(names)):
        bits = tuple(bool(mask & (1 << i)) for i in range(len(names)))
        env = dict(zip(names, bits))
        if admitted(case['model'], env):
            yield bits, env


def checked_count_bounds(case):
    fn, fp = (rational(case['loss'][k]) for k in ('false_negative', 'false_positive'))
    lower = upper = Fraction(0)
    for anchor in case['anchors']:
        aa, bb = ({d['id'] for d in anchor[r]['value']} for r in ROLES)
        removed, added = len(aa - bb), len(bb - aa)
        w = rational(anchor['weight'])
        lower -= w * (fn * removed + fp * added)
        upper += w * (fn * added + fp * removed)
    return lower, upper


def checked_delta(case, env, entries, removed=frozenset()):
    _require(type(entries) is list, 'Anchor proofs must be a list')
    by_anchor = {}
    for entry in entries:
        _keys(entry, ('anchor', *ROLES))
        _require(type(entry['anchor']) is str and entry['anchor'] not in by_anchor, 'Repeated or malformed anchor')
        by_anchor[entry['anchor']] = entry
    finite = {a['id'] for a in case['anchors'] if a['reference']['state'] == 'finite'}
    _require(set(by_anchor) == finite, 'Finite anchor omitted or invented')
    fn, fp = (rational(case['loss'][k]) for k in ('false_negative', 'false_positive'))
    low = high = Fraction(0)
    for a in case['anchors']:
        aa, bb = ({d['id'] for d in a[r]['value']} for r in ROLES)
        p, q = len(aa - bb), len(bb - aa)
        w = rational(a['weight'])
        if a['reference']['state'] == 'open':
            low -= w * (fn * p + fp * q)
            high += w * (fn * q + fp * p)
            continue
        present = {o['id'] for o in a['reference']['objects']
                   if (a['id'], o['id']) not in removed
                   and all(env[t['variable']] is t['value'] for t in o['when'])}
        sizes = []
        for role, left in zip(ROLES, (aa, bb)):
            edges = {(e['detection'], e['object']) for e in a['reference']['edges']
                     if e['detection'] in left and e['object'] in present
                     and all(env[t['variable']] is t['value'] for t in e['when'])}
            sizes.append(_cardinality(by_anchor[a['id']][role], left, present, edges))
        gain = sizes[1] - sizes[0]
        _require(-p <= gain <= q, 'Common-output cardinality bound violated')
        delta = w * ((fn + fp) * gain - fp * (len(bb) - len(aa)))
        low += delta
        high += delta
    return low, high


def check(case, payload):
    """Input must have passed contract.validate; no producer call occurs here."""
    _keys(payload, ('result', 'proof'))
    proof = payload['proof']
    _require(type(proof) is dict, 'Proof must be an object')
    expected = result_template(case)
    missing = [{'anchor': a['id'], 'role': role, 'state': a[role]['state']}
               for a in case['anchors'] for role in ROLES if a[role]['state'] != 'observed']
    if missing:
        _require(encoded(proof) == encoded({'kind': 'input_blocked', 'unavailable': missing}), 'Unavailable output omitted')
        expected['execution_status'] = 'input_blocked'
    else:
        count, unit = capacity(case)
        allowed = count <= MAX_WORLDS and count * unit <= MAX_WORK
        lower = upper = None
        if proof.get('kind') == 'count_bound':
            _keys(proof, ('kind', 'reason', 'feasible_assignment'))
            _require(not allowed and proof['reason'] == 'resource_limit', 'False resource limit')
            lower, upper = checked_count_bounds(case)
            expected.update(execution_status='resource_limited', enclosure_kind='unconditional_count_bound')
            if proof['feasible_assignment'] is not None:
                env = _assignment(proof['feasible_assignment'], case['model']['variables'])
                _require(admitted(case['model'], env), 'Inconsistent model witness')
                expected['model_status'] = 'consistent'
        elif proof.get('kind') == 'enumerated':
            _keys(proof, ('kind', 'worlds'))
            _require(allowed, 'Enumeration exceeds work limit')
            _require(type(proof['worlds']) is list and len(proof['worlds']) <= count, 'Invalid worlds')
            supplied = {}
            for row in proof['worlds']:
                _keys(row, ('assignment', 'anchors'))
                env = _assignment(row['assignment'], case['model']['variables'])
                key = tuple(row['assignment'])
                _require(key not in supplied and admitted(case['model'], env), 'Duplicate or inadmissible world')
                supplied[key] = row
            permitted = dict(checked_worlds(case))
            _require(set(supplied) == set(permitted), 'A permitted joint world is missing')
            if not permitted:
                expected['model_status'] = 'inconsistent'
            else:
                intervals = [checked_delta(case, env, supplied[bits]['anchors']) for bits, env in permitted.items()]
                lower = min(x[0] for x in intervals)
                upper = max(x[1] for x in intervals)
                expected.update(model_status='consistent', enclosure_kind='conservative_open_reference'
                                if any(a['reference']['state'] == 'open' for a in case['anchors']) else 'exact_for_finite_model')
        else:
            raise Invalid('CERTIFICATE_INVALID', 'Unknown proof kind')
        if lower is not None:
            expected['bounds'] = {'lower': wire(lower), 'upper': wire(upper)}
            if expected['model_status'] == 'consistent':
                expected['decision'] = checked_classification(lower, upper, rational(case['loss']['tolerance']))
    _require(encoded(payload['result']) == encoded(expected), 'Result not entailed by certificate')
    return expected
