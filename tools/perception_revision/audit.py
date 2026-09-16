"""Bounded proof proposals; candidate audit selection belongs to the caller."""
from fractions import Fraction

from tools.perception_decision.kernel import _matching_certificate
from tools.perception_decision.checker import _assignment, _keys
from .contract import Invalid, ROLES, admitted, graph, rational, require, worlds
from .audit_checker import conclude, deletion_set, domain, edits, enumeration_allowed, unavailable


def members(removed):
    return [{'anchor': aid, 'object': oid} for aid, oid in sorted(removed)]


def world_proposal(case, env, removed):
    rows = []
    delta = Fraction(0)
    fn, fp = (rational(case['loss'][k]) for k in ('false_negative', 'false_positive'))
    for a in case['anchors']:
        _, edges = graph(a, env, removed)
        row = {'anchor': a['id']}
        sizes = []
        for role in ROLES:
            left = {d['id'] for d in a[role]['value']}
            row[role] = _matching_certificate(left, {(d, o) for d, o in edges if d in left})
            sizes.append(len(row[role]['matching']))
        delta += rational(a['weight']) * ((fn + fp) * (sizes[1] - sizes[0])
                 - fp * (len(a['output_b']['value']) - len(a['output_a']['value'])))
        rows.append(row)
    return rows, delta


def produce(case, request, candidate=None):
    reason = unavailable(case)
    if reason is not None:
        proof = {'kind': 'unavailable', 'reason': reason}
        return {'result': conclude(case, request, proof), 'proof': proof}
    if candidate is not None:
        _keys(candidate, ('assignment', 'deletions'))
        env = _assignment(candidate['assignment'], case['model']['variables'])
        require(admitted(case['model'], env), 'AUDIT_CANDIDATE', 'Inadmissible candidate world')
        removed = deletion_set(candidate['deletions'])
        active = domain(case, request, env)
        require(active is not None, 'AUDIT_CANDIDATE', 'Candidate conflicts with observations')
        required, free, budget = active
        require(required <= removed <= required | set(free) and len(removed - required) <= budget,
                'AUDIT_CANDIDATE', 'Candidate violates deletion family or observations')
        rows, delta = world_proposal(case, env, removed)
        require(delta <= rational(case['loss']['tolerance']), 'AUDIT_NOT_COUNTEREXAMPLE', 'Candidate does not overturn improvement')
        proof = {'kind': 'counterexample', 'assignment': candidate['assignment'], 'deletions': members(removed), 'anchors': rows}
        return {'result': conclude(case, request, proof), 'proof': proof}
    selected = [(bits, env, active) for bits, env in worlds(case['model'])
                if (active := domain(case, request, env)) is not None]
    exact = enumeration_allowed(case, [row[2] for row in selected])
    proof = {'kind': 'enumerated_deletions' if exact else 'bounded_deletions', 'worlds': []}
    for bits, env, (required, free, budget) in selected:
        variants = []
        for removed in edits(required, free, budget) if exact else [required]:
            rows, delta = world_proposal(case, env, removed)
            if delta <= rational(case['loss']['tolerance']):
                counter = {'kind': 'counterexample', 'assignment': list(bits), 'deletions': members(removed), 'anchors': rows}
                return {'result': conclude(case, request, counter), 'proof': counter}
            if exact:
                variants.append({'deletions': members(removed), 'anchors': rows})
        proof['worlds'].append({'assignment': list(bits), 'variants': variants} if exact else
                               {'assignment': list(bits), 'anchors': rows})
    return {'result': conclude(case, request, proof), 'proof': proof}
