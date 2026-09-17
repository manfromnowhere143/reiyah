"""Check universal geometry bounds and explicit shifts without a solver."""
from fractions import Fraction
from tools.perception_decision.checker import _cardinality, _keys, _require
from .checker import checked_classification, result_template
from .contract import MAX_WORK, encoded, rational, wire
from .localization_contract import VERSION, displacement_graphs, matching_work, prepare


def conclude(case, request, proof):
    _require(type(proof) is dict, 'Geometry proof must be an object')
    result = result_template(case)
    result.update(geometry_family=request['family'], position_basis=request['position_basis'],
                  robustness='not_evaluated', witness_value=None)
    reason, prepared = prepare(case, request)
    if reason is None and proof.get('kind') not in ('localization_displacement', 'localization_linear') and matching_work(prepared) > MAX_WORK:
        reason = 'matching_work_limit'
    if reason is not None:
        _require(encoded(proof) == encoded({'kind': 'localization_unavailable', 'version': VERSION, 'reason': reason}),
                 'False geometry unavailability outcome')
        result['execution_status'] = ('input_blocked' if reason == 'unavailable_outputs' else
                                      'resource_limited' if reason.endswith('_limit') else 'scope_unavailable')
        if reason.endswith('_limit'):
            result['robustness'] = 'unresolved'
        return result
    if proof.get('kind') == 'localization_linear':
        from .linear_bounds import check as check_linear
        _keys(proof, ('kind', 'version', 'linear_certificate'))
        _require(proof['version'] == VERSION, 'Unknown linear proof version')
        gains = check_linear(prepared, proof['linear_certificate'])
        fn, fp = (rational(case['loss'][k]) for k in ('false_negative', 'false_positive'))
        lower = upper = Fraction(0)
        for row in prepared['rows']:
            aa, bb, count = row['a'], row['b'], len(row['references'])
            aid = row['anchor']['id']
            lo = max(-min(len(aa - bb), count), gains.get((aid, 'b_minus_a'), -min(len(aa - bb), count)))
            hi = min(min(len(bb - aa), count), -gains.get((aid, 'a_minus_b'), -min(len(bb - aa), count)))
            _require(lo <= hi, 'Inconsistent checked linear bounds')
            weight = rational(row['anchor']['weight'])
            offset = fp * (len(bb) - len(aa))
            lower += weight * ((fn + fp) * lo - offset)
            upper += weight * ((fn + fp) * hi - offset)
        tolerance = rational(case['loss']['tolerance'])
        result.update(model_status='consistent', bounds={'lower': wire(lower), 'upper': wire(upper)},
                      enclosure_kind='constant_for_declared_geometry_family' if lower == upper else 'conservative_linear_geometry_enclosure',
                      decision=checked_classification(lower, upper, tolerance),
                      robustness='robust' if lower > tolerance else 'excluded_for_family' if upper <= tolerance else 'unresolved')
        return result
    witness = proof.get('kind') == 'localization_displacement'
    _keys(proof, ('kind', 'version', 'anchors', 'candidate') if witness else ('kind', 'version', 'anchors'))
    _require(proof['version'] == VERSION and proof['kind'] in ('localization_displacement', 'localization_envelope'),
             'Unknown geometry proof kind/version')
    displaced = displacement_graphs(request, prepared, proof['candidate']) if witness else None
    _require(matching_work(prepared, displaced) <= MAX_WORK, 'Geometry proof exceeds work limit')
    _require(type(proof['anchors']) is list, 'Geometry anchor proofs must be a list')
    supplied = {}
    for entry in proof['anchors']:
        _keys(entry, ('anchor', 'output_a', 'output_b') if witness else ('anchor', 'a_possible', 'b_guaranteed'))
        _require(type(entry['anchor']) is str and entry['anchor'] not in supplied, 'Repeated geometry anchor')
        supplied[entry['anchor']] = entry
    _require(set(supplied) == {a['id'] for a in case['anchors']}, 'Missing or invented geometry anchor')
    fn, fp = (rational(case['loss'][k]) for k in ('false_negative', 'false_positive'))
    lower = upper = Fraction(0)
    for row in prepared['rows']:
        anchor, aa, bb = row['anchor'], row['a'], row['b']
        objects = set(row['references'])
        entry = supplied[anchor['id']]
        if witness:
            edges = displaced[anchor['id']]
            ca = _cardinality(entry['output_a'], aa, objects, {(d, o) for d, o in edges if d in aa})
            cb = _cardinality(entry['output_b'], bb, objects, {(d, o) for d, o in edges if d in bb})
            gain_lo = gain_hi = cb - ca
        else:
            must, may = row['guaranteed'], row['possible']
            a_cert, b_cert = entry['a_possible'], entry['b_guaranteed']
            a_hi = _cardinality(a_cert, aa, objects, {(d, o) for d, o in may if d in aa})
            b_lo = _cardinality(b_cert, bb, objects, {(d, o) for d, o in must if d in bb})
            # A subset of a matching is still a matching in every admitted graph.
            a_lo = sum(tuple(pair) in must for pair in a_cert['matching'])
            # Extend the checked B cover over every still-uncovered possible edge.
            left = set(b_cert['cover']['detections']); right = set(b_cert['cover']['objects'])
            uncovered = {(d, o) for d, o in may if d in bb and d not in left and o not in right}
            extension = min(len({d for d, _ in uncovered}), len({o for _, o in uncovered}))
            b_hi = min(len(bb), len(objects), b_lo + extension)
            gain_lo, gain_hi = max(-len(aa - bb), b_lo - a_hi), min(len(bb - aa), b_hi - a_lo)
        _require(-len(aa - bb) <= gain_lo <= gain_hi <= len(bb - aa), 'Invalid shared-output rank enclosure')
        weight = rational(anchor['weight'])
        offset = fp * (len(bb) - len(aa))
        lower += weight * ((fn + fp) * gain_lo - offset)
        upper += weight * ((fn + fp) * gain_hi - offset)
    result['model_status'] = 'consistent'
    tolerance = rational(case['loss']['tolerance'])
    if witness:
        _require(lower == upper, 'Displacement does not give one finite value')
        result.update(enclosure_kind='single_admitted_displacement', witness_value=wire(lower),
                      robustness='refuted_by_displacement' if lower <= tolerance else 'unresolved')
    else:
        result.update(bounds={'lower': wire(lower), 'upper': wire(upper)},
                      enclosure_kind='constant_for_declared_geometry_family' if lower == upper else 'conservative_geometry_enclosure',
                      decision=checked_classification(lower, upper, tolerance),
                      robustness='robust' if lower > tolerance else 'excluded_for_family' if upper <= tolerance else 'unresolved')
    return result


def check(case, request, payload):
    _keys(payload, ('result', 'proof'))
    result = conclude(case, request, payload['proof'])
    _require(encoded(result) == encoded(payload['result']), 'Result not entailed by geometry proof')
    return result
