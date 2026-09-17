"""Propose matching/cover proofs of attained reference-deletion margins."""
from fractions import Fraction

from tools.perception_decision.kernel import _matching_certificate
from .contract import ROLES, graph, rational, wire
from .margin_contract import result_template, unavailable


def right_cover(cert, left, objects, edges):
    """Choose a minimum cover favoring object vertices, using reverse reachability.

    This construction is untrusted by the checker: every returned matching and
    cover must satisfy the ordinary independent cardinality obligations.
    """
    left_match = dict(cert['matching'])
    right_match = {o: d for d, o in cert['matching']}
    neighbors = {o: [] for o in objects}
    for d, o in sorted(edges):
        neighbors[o].append(d)
    reached_right = objects - set(right_match)
    reached_left = set()
    queue = sorted(reached_right)
    while queue:
        o = queue.pop()
        for d in neighbors[o]:
            if right_match.get(o) == d or d in reached_left:
                continue
            reached_left.add(d)
            if d in left_match and left_match[d] not in reached_right:
                reached_right.add(left_match[d])
                queue.append(left_match[d])
    return {'matching': cert['matching'],
            'cover': {'detections': sorted(reached_left),
                      'objects': sorted(objects - reached_right)}}


def produce(case):
    """Input must pass contract.validate; output must pass margin_checker.check."""
    result = result_template(case)
    stopped = unavailable(case)
    if stopped:
        result['execution_status'] = stopped[0]
        return {'result': result, 'proof': stopped[1]}
    fn, fp, tolerance = (rational(case['loss'][k]) for k in
                         ('false_negative', 'false_positive', 'tolerance'))
    rows, pool = [], []
    delta = Fraction(0)
    for a in case['anchors']:
        objects, edges = graph(a, {})
        aa, bb = ({d['id'] for d in a[r]['value']} for r in ROLES)
        row = {'anchor': a['id']}
        for role, left in zip(ROLES, (aa, bb)):
            selected = {(d, o) for d, o in edges if d in left}
            cert = _matching_certificate(left, selected)
            row[role] = right_cover(cert, left, objects, selected) if role == 'output_b' else cert
        a_neighbors = {o for d, o in edges if d in aa}
        pool.extend((a['id'], o) for o in row['output_b']['cover']['objects'] if o not in a_neighbors)
        gain = len(row['output_b']['matching']) - len(row['output_a']['matching'])
        delta += rational(a['weight']) * ((fn + fp) * gain - fp * (len(bb) - len(aa)))
        rows.append(row)
    pool.sort()
    step = (fn + fp) * rational(case['anchors'][0]['weight'])
    result.update(model_status='consistent', baseline_delta=wire(delta),
                  per_deletion_bound=wire(step), pool_size=len(pool),
                  baseline_criterion='supported' if delta > tolerance else 'excluded')
    witness = []
    if delta <= tolerance:
        result.update(margin_status='criterion_already_excluded', minimum_adverse_deletions=0,
                      deletion_lower_bound=0, witness_delta=wire(delta))
    else:
        quotient = (delta - tolerance) / step
        floor = -(-quotient.numerator // quotient.denominator)
        result.update(margin_status='lower_bound_only', deletion_lower_bound=floor,
                      robust_through=min(floor - 1, sum(len(a['reference']['objects']) for a in case['anchors'])))
        if len(pool) >= floor:
            witness = pool[:floor]
            result.update(margin_status='exact', minimum_adverse_deletions=floor,
                          witness_delta=wire(delta - floor * step),
                          necessary_confirmations=len(pool) - floor + 1)
    endpoints = lambda values: [{'anchor': a, 'object': o} for a, o in values]
    return {'result': result, 'proof': {'kind': 'covered_reference_pool', 'anchors': rows,
                                       'pool': endpoints(pool), 'witness': endpoints(witness)}}
