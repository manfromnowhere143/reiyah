"""Check deletion margins without matching, search, or a solver optimality claim."""
from fractions import Fraction

from tools.perception_decision.checker import _cardinality, _keys, _require
from .contract import ROLES, encoded, rational, wire
from .margin_contract import result_template, unavailable


def endpoints(value):
    _require(type(value) is list, 'Reference endpoints must be a list')
    result = []
    for item in value:
        _keys(item, ('anchor', 'object'))
        _require(all(type(item[k]) is str for k in ('anchor', 'object')), 'Malformed endpoint')
        result.append((item['anchor'], item['object']))
    _require(result == sorted(set(result)), 'Endpoints must be unique and canonically ordered')
    return result


def check(case, payload):
    """The input must already pass contract.validate and its byte-size limit."""
    _keys(payload, ('result', 'proof'))
    expected = result_template(case)
    stopped = unavailable(case)
    if stopped:
        expected['execution_status'] = stopped[0]
        _require(encoded(payload['proof']) == encoded(stopped[1]), 'False scope or resource claim')
    else:
        proof = payload['proof']
        _keys(proof, ('kind', 'anchors', 'pool', 'witness'))
        _require(proof['kind'] == 'covered_reference_pool', 'Wrong deletion-margin proof')
        _require(type(proof['anchors']) is list, 'Anchor certificates must be a list')
        by_id = {}
        for row in proof['anchors']:
            _keys(row, ('anchor', *ROLES))
            _require(type(row['anchor']) is str and row['anchor'] not in by_id, 'Repeated or malformed anchor')
            by_id[row['anchor']] = row
        _require(set(by_id) == {a['id'] for a in case['anchors']}, 'Anchor omitted or invented')
        fn, fp = (rational(case['loss'][k]) for k in ('false_negative', 'false_positive'))
        tolerance = rational(case['loss']['tolerance'])
        delta, eligible, object_count = Fraction(0), set(), 0
        for a in case['anchors']:
            # Scope admission guarantees a single unconditional finite world.
            objects = {o['id'] for o in a['reference']['objects']}
            object_count += len(objects)
            edges = {(e['detection'], e['object']) for e in a['reference']['edges']}
            aa, bb = ({d['id'] for d in a[r]['value']} for r in ROLES)
            counts = []
            for role, left in zip(ROLES, (aa, bb)):
                counts.append(_cardinality(by_id[a['id']][role], left, objects,
                                           {(d, o) for d, o in edges if d in left}))
            adjacent_a = {o for d, o in edges if d in aa}
            eligible.update((a['id'], o) for o in by_id[a['id']]['output_b']['cover']['objects']
                            if o not in adjacent_a)
            delta += rational(a['weight']) * ((fn + fp) * (counts[1] - counts[0]) - fp * (len(bb) - len(aa)))
        pool, witness = endpoints(proof['pool']), endpoints(proof['witness'])
        _require(set(pool) == eligible, 'Pool does not match the checked cover and A-edge conditions')
        step = (fn + fp) * rational(case['anchors'][0]['weight'])
        expected.update(model_status='consistent', baseline_delta=wire(delta),
                        baseline_criterion='supported' if delta > tolerance else 'excluded',
                        per_deletion_bound=wire(step), pool_size=len(pool))
        if delta <= tolerance:
            _require(not witness, 'An already excluded verdict needs no deletion')
            expected.update(margin_status='criterion_already_excluded', minimum_adverse_deletions=0,
                            deletion_lower_bound=0, witness_delta=wire(delta))
        else:
            ratio = (delta - tolerance) / step
            floor = (ratio.numerator + ratio.denominator - 1) // ratio.denominator
            expected.update(margin_status='lower_bound_only', deletion_lower_bound=floor,
                            robust_through=min(object_count, floor - 1))
            if len(pool) >= floor:
                _require(witness == pool[:floor], 'Adverse witness must be the canonical floor-sized pool subset')
                expected.update(margin_status='exact', minimum_adverse_deletions=floor,
                                witness_delta=wire(delta - step * floor),
                                necessary_confirmations=len(pool) - floor + 1)
            else:
                _require(not witness, 'No attained bound was proved by this pool')
    _require(encoded(payload['result']) == encoded(expected), 'Deletion-margin result does not follow from proof')
    return expected
