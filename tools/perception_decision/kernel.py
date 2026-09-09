"""Producer of exact finite-model or conservative paired-loss enclosures."""
from fractions import Fraction
from itertools import product

from .contract import MAX_WORLDS, MAX_WORK, rational, wire


def _true(items, world):
    return all(world[item['variable']] == item['value'] for item in items)


def _admitted(model, world):
    return all(any(world[l['variable']] == l['value'] for l in clause)
               for clause in model['clauses'])


def _graph(anchor, world):
    objects = {o['id'] for o in anchor['reference']['objects'] if _true(o['when'], world)}
    return {(e['detection'], e['object']) for e in anchor['reference']['edges']
            if e['object'] in objects and _true(e['when'], world)}


def _matching_certificate(left, edges):
    neighbors = {d: sorted(o for v, o in edges if v == d) for d in sorted(left)}
    right_match = {}

    def augment(d, seen):
        for obj in neighbors[d]:
            if obj in seen:
                continue
            seen.add(obj)
            if obj not in right_match or augment(right_match[obj], seen):
                right_match[obj] = d
                return True
        return False

    for d in sorted(left):
        augment(d, set())
    left_match = {d: obj for obj, d in right_match.items()}
    reached_left = set(left) - set(left_match)
    reached_right = set()
    queue = sorted(reached_left)
    while queue:
        d = queue.pop()
        for obj in neighbors[d]:
            if left_match.get(d) == obj or obj in reached_right:
                continue
            reached_right.add(obj)
            if obj in right_match and right_match[obj] not in reached_left:
                reached_left.add(right_match[obj])
                queue.append(right_match[obj])
    return {'matching': [[d, o] for d, o in sorted(left_match.items())],
            'cover': {'detections': sorted(set(left) - reached_left),
                      'objects': sorted(reached_right)}}


def _classification(lower, upper, tolerance):
    improvement = ('supported' if lower > tolerance else
                   'excluded' if upper <= tolerance else 'unresolved')
    preference = ('prefer_augmented' if lower > tolerance else
                  'prefer_base' if upper < -tolerance else
                  'equivalent_within_tolerance' if lower >= -tolerance and upper <= tolerance
                  else 'unresolved')
    return {'improvement_criterion': improvement, 'preference': preference}


def _capacity(case):
    worlds = 2 ** len(case['model']['variables'])
    work = 1 + len(case['model']['variables']) + sum(map(len, case['model']['clauses']))
    for a in case['anchors']:
        if a['reference']['state'] == 'finite':
            size = len(a['base']['value']) + len(a['additions']['value'])
            ref = a['reference']
            work += sum(len(row['when']) for row in ref['objects'] + ref['edges'])
            work += 4 * (size + 1) * (len(ref['objects']) + len(ref['edges']) + 1)
    return worlds, worlds * work


def produce(case):
    """Accept a validated contract; caller must run the separate checker before use."""
    result = {'execution_status': 'succeeded', 'model_status': 'not_checked',
              'enclosure_kind': 'unavailable', 'bounds': None,
              'decision': {'improvement_criterion': 'not_evaluated', 'preference': 'not_evaluated'},
              'reference_scope': case['evidence_kind'], 'sampling_scope': 'fixed_selected_cohort',
              'statistical_confidence_level': None, 'physical_coverage': 'not_established',
              'authority_state': 'research_only'}
    missing = [{'anchor': a['id'], 'role': role, 'state': a[role]['state']}
               for a in case['anchors'] for role in ('base', 'additions') if a[role]['state'] != 'observed']
    if missing:
        result['execution_status'] = 'input_blocked'
        return {'result': result, 'proof': {'kind': 'input_blocked', 'unavailable': missing}}
    fn, fp, tolerance = [rational(case['loss'][k]) for k in ('false_negative', 'false_positive', 'tolerance')]
    total_r = sum(rational(a['weight']) * len(a['additions']['value']) for a in case['anchors'])
    variables = case['model']['variables']
    world_count, work = _capacity(case)
    if world_count > MAX_WORLDS or work > MAX_WORK:
        assignment = case['model'].get('feasible_assignment', [False] * len(variables))
        witness = assignment if _admitted(case['model'], dict(zip(variables, assignment))) else None
        result.update(execution_status='resource_limited',
                      model_status='consistent' if witness is not None else 'not_checked',
                      enclosure_kind='unconditional_count_bound',
                      bounds={'lower': wire(-fp * total_r), 'upper': wire(fn * total_r)})
        if witness is not None:
            result['decision'] = _classification(-fp * total_r, fn * total_r, tolerance)
        return {'result': result, 'proof': {'kind': 'count_bound', 'reason': 'resource_limit',
                                           'feasible_assignment': witness}}
    certificates, lows, highs = [], [], []
    any_open = any(a['reference']['state'] == 'open' for a in case['anchors'])
    for values in product((False, True), repeat=len(variables)):
        world = dict(zip(variables, values))
        if not _admitted(case['model'], world):
            continue
        low = high = Fraction(0)
        rows = []
        for a in case['anchors']:
            weight, r = rational(a['weight']), len(a['additions']['value'])
            if a['reference']['state'] == 'open':
                low -= weight * fp * r
                high += weight * fn * r
                continue
            base = {d['id'] for d in a['base']['value']}
            augmented = base | {d['id'] for d in a['additions']['value']}
            edges = _graph(a, world)
            a_cert = _matching_certificate(base, {(d, o) for d, o in edges if d in base})
            c_cert = _matching_certificate(augmented, edges)
            gain = len(c_cert['matching']) - len(a_cert['matching'])
            delta = (fn + fp) * gain - fp * r
            low += weight * delta
            high += weight * delta
            rows.append({'anchor': a['id'], 'base': a_cert, 'augmented': c_cert})
        certificates.append({'assignment': list(values), 'anchors': rows})
        lows.append(low)
        highs.append(high)
    proof = {'kind': 'enumerated', 'worlds': certificates}
    if not certificates:
        result['model_status'] = 'inconsistent'
        return {'result': result, 'proof': proof}
    lower, upper = min(lows), max(highs)
    result.update(model_status='consistent',
                  enclosure_kind='conservative_open_reference' if any_open else 'exact_for_finite_model',
                  bounds={'lower': wire(lower), 'upper': wire(upper)},
                  decision=_classification(lower, upper, tolerance))
    return {'result': result, 'proof': proof}
