"""Check certificates without invoking the producer or its matching algorithm."""
from fractions import Fraction

from .contract import Invalid, MAX_WORLDS, MAX_WORK, encoded, rational, wire


def _require(ok, detail):
    if not ok:
        raise Invalid('CERTIFICATE_INVALID', detail)


def _keys(value, keys):
    _require(type(value) is dict and set(value) == set(keys), 'Unexpected certificate fields')


def _assignment(values, variables):
    _require(type(values) is list and len(values) == len(variables)
             and all(type(v) is bool for v in values), 'Invalid assignment representation')
    return {name: values[i] for i, name in enumerate(variables)}


def _satisfies(env, clauses):
    for clause in clauses:
        if not any(env[literal['variable']] is literal['value'] for literal in clause):
            return False
    return True


def _enabled(guard, env):
    for literal in guard:
        if env[literal['variable']] is not literal['value']:
            return False
    return True


def _cardinality(cert, left, objects, edges):
    _keys(cert, ('matching', 'cover'))
    _keys(cert['cover'], ('detections', 'objects'))
    matching = cert['matching']
    _require(type(matching) is list, 'Matching must be a list')
    used_left, used_right = set(), set()
    for pair in matching:
        _require(type(pair) is list and len(pair) == 2 and all(type(x) is str for x in pair),
                 'Malformed matching edge')
        d, o = pair
        _require((d, o) in edges and d not in used_left and o not in used_right,
                 'Matching has a missing edge or reused endpoint')
        used_left.add(d)
        used_right.add(o)
    cover = []
    for role, universe in (('detections', left), ('objects', objects)):
        values = cert['cover'][role]
        _require(type(values) is list and all(type(x) is str for x in values), 'Malformed cover')
        vertices = set(values)
        _require(len(vertices) == len(values) and vertices <= universe, 'Invalid cover vertices')
        cover.append(vertices)
    _require(all(d in cover[0] or o in cover[1] for d, o in edges), 'An edge is not covered')
    _require(len(used_left) == len(cover[0]) + len(cover[1]), 'Matching and cover sizes differ')
    return len(used_left)


def check(case, payload):
    """Return the verified result or raise Invalid. Input must already be validated."""
    _keys(payload, ('result', 'proof'))
    proof = payload['proof']
    _require(type(proof) is dict, 'Proof must be an object')
    expected = {'execution_status': 'succeeded', 'model_status': 'not_checked',
                'enclosure_kind': 'unavailable', 'bounds': None,
                'decision': {'improvement_criterion': 'not_evaluated', 'preference': 'not_evaluated'},
                'reference_scope': case['evidence_kind'], 'sampling_scope': 'fixed_selected_cohort',
                'statistical_confidence_level': None, 'physical_coverage': 'not_established',
                'authority_state': 'research_only'}
    unavailable = []
    for a in case['anchors']:
        for role in ('base', 'additions'):
            if a[role]['state'] != 'observed':
                unavailable.append({'anchor': a['id'], 'role': role, 'state': a[role]['state']})
    if unavailable:
        _require(encoded(proof) == encoded({'kind': 'input_blocked', 'unavailable': unavailable}),
                 'Unavailable output was omitted or replaced')
        expected['execution_status'] = 'input_blocked'
        _require(encoded(payload['result']) == encoded(expected), 'Blocked result was promoted')
        return expected

    fn = rational(case['loss']['false_negative'])
    fp = rational(case['loss']['false_positive'])
    tolerance = rational(case['loss']['tolerance'])
    variables, clauses = case['model']['variables'], case['model']['clauses']
    state_count = 1 << len(variables)
    unit_work = 1 + len(variables) + sum(len(c) for c in clauses)
    for anchor in case['anchors']:
        ref = anchor['reference']
        if ref['state'] == 'finite':
            unit_work += sum(len(obj['when']) for obj in ref['objects'])
            unit_work += sum(len(edge['when']) for edge in ref['edges'])
            unit_work += 4 * (1 + len(anchor['base']['value']) + len(anchor['additions']['value'])) * (
                1 + len(ref['edges']) + len(ref['objects']))
    full_allowed = state_count <= MAX_WORLDS and state_count * unit_work <= MAX_WORK
    lower = upper = None
    if proof.get('kind') == 'count_bound':
        _keys(proof, ('kind', 'reason', 'feasible_assignment'))
        _require(not full_allowed and proof['reason'] == 'resource_limit', 'False resource-limit claim')
        additions = sum(rational(a['weight']) * len(a['additions']['value']) for a in case['anchors'])
        lower, upper = -fp * additions, fn * additions
        expected.update(execution_status='resource_limited', enclosure_kind='unconditional_count_bound')
        if proof['feasible_assignment'] is not None:
            env = _assignment(proof['feasible_assignment'], variables)
            _require(_satisfies(env, clauses), 'Invalid model-consistency witness')
            expected['model_status'] = 'consistent'
    elif proof.get('kind') == 'enumerated':
        _keys(proof, ('kind', 'worlds'))
        _require(full_allowed, 'Enumeration exceeds the checker budget')
        _require(type(proof['worlds']) is list and len(proof['worlds']) <= state_count,
                 'Invalid world list')
        supplied = {}
        for row in proof['worlds']:
            _keys(row, ('assignment', 'anchors'))
            env = _assignment(row['assignment'], variables)
            key = tuple(row['assignment'])
            _require(key not in supplied and _satisfies(env, clauses), 'Duplicate or inadmissible world')
            supplied[key] = row
        admitted = []
        for mask in range(state_count):
            bits = tuple(bool(mask & (1 << i)) for i in range(len(variables)))
            env = dict(zip(variables, bits))
            if _satisfies(env, clauses):
                admitted.append(bits)
        _require(set(supplied) == set(admitted), 'The proof omitted a permitted reference interpretation')
        finite_ids = {a['id'] for a in case['anchors'] if a['reference']['state'] == 'finite'}
        lows, highs = [], []
        for bits in admitted:
            env = dict(zip(variables, bits))
            entries = supplied[bits]['anchors']
            _require(type(entries) is list, 'Anchor certificates must be a list')
            by_anchor = {}
            for entry in entries:
                _keys(entry, ('anchor', 'base', 'augmented'))
                _require(type(entry['anchor']) is str and entry['anchor'] not in by_anchor,
                         'Repeated or invalid anchor certificate')
                by_anchor[entry['anchor']] = entry
            _require(set(by_anchor) == finite_ids, 'Finite anchors are missing or invented')
            lo = hi = Fraction(0)
            for anchor in case['anchors']:
                w = rational(anchor['weight'])
                n_added = len(anchor['additions']['value'])
                ref = anchor['reference']
                if ref['state'] == 'open':
                    lo += w * (-fp * n_added)
                    hi += w * (fn * n_added)
                    continue
                present = {obj['id'] for obj in ref['objects'] if _enabled(obj['when'], env)}
                base_ids = {d['id'] for d in anchor['base']['value']}
                all_ids = base_ids | {d['id'] for d in anchor['additions']['value']}
                cardinalities = []
                for role, left in (('base', base_ids), ('augmented', all_ids)):
                    edges = {(e['detection'], e['object']) for e in ref['edges']
                             if e['detection'] in left and e['object'] in present and _enabled(e['when'], env)}
                    cardinalities.append(_cardinality(by_anchor[anchor['id']][role], left, present, edges))
                gain = cardinalities[1] - cardinalities[0]
                _require(0 <= gain <= n_added, 'Nested cardinality bound violated')
                delta = w * ((fn + fp) * gain - fp * n_added)
                lo += delta
                hi += delta
            lows.append(lo)
            highs.append(hi)
        if not admitted:
            expected['model_status'] = 'inconsistent'
        else:
            lower, upper = min(lows), max(highs)
            expected['model_status'] = 'consistent'
            expected['enclosure_kind'] = ('conservative_open_reference'
                                         if len(finite_ids) != len(case['anchors']) else 'exact_for_finite_model')
    else:
        raise Invalid('CERTIFICATE_INVALID', 'Unknown proof kind')
    if lower is not None:
        expected['bounds'] = {'lower': wire(lower), 'upper': wire(upper)}
        if expected['model_status'] == 'consistent':
            if lower > tolerance:
                expected['decision'] = {'improvement_criterion': 'supported', 'preference': 'prefer_augmented'}
            else:
                expected['decision']['improvement_criterion'] = 'excluded' if upper <= tolerance else 'unresolved'
                preference = 'unresolved'
                if upper < -tolerance:
                    preference = 'prefer_base'
                elif lower >= -tolerance and upper <= tolerance:
                    preference = 'equivalent_within_tolerance'
                expected['decision']['preference'] = preference
    _require(encoded(payload['result']) == encoded(expected), 'Reported result is not entailed by its certificate')
    return expected
