"""Compose checked fixed-world addition certificates under declared split weights.

This API checks source certificates, then derives weighted deletion bounds without
matching, optimization or sampling. Expected membership is a caller-bound premise;
it is never inferred from whichever certificates happened to succeed.
"""
from fractions import Fraction

from .contract import (MAX_INPUT_BYTES, MAX_PACKET_BYTES, encoded, rational,
                       require, unique, validate, wire)
from .margin_checker import check as check_member

MAX_MEMBERS = 256
MAX_TOTAL_INPUT_BYTES = 64 * 1024 * 1024
MAX_TOTAL_PROOF_BYTES = 64 * 1024 * 1024


def crossing(groups, target):
    """Fewest unit-cost items whose sorted per-item bounds reach target.

    Each (step, capacity) group contains capacity separate deletions with that
    bound. A failure to reach target is explicit, not an attained optimum.
    """
    if target <= 0:
        return 0
    total, count = Fraction(0), 0
    for step, capacity in sorted(groups, reverse=True):
        if step <= 0 or capacity <= 0:
            continue
        gap = (target - total) / step
        needed = (gap.numerator + gap.denominator - 1) // gap.denominator
        take = min(capacity, needed)
        total += take * step
        count += take
        if total >= target:
            return count
    return None


def evaluate(members, expected_ids, tolerance):
    """Return bounds and an attaining pool witness when available.

    members: {id, weight, case, certificate} rows; certificate is the native
    deletion-margin payload. Bind exact operand/proof bytes at the IO boundary.
    Every input is validated and every member certificate checked here. A parent
    packet or study manifest must bind expected_ids, weights and tolerance before
    using the result as evidence. This does not verify external dataset coverage.
    """
    require(type(members) is list and 0 < len(members) <= MAX_MEMBERS,
            'SPLIT_MEMBERS', 'A split needs 1..256 declared members')
    require(type(expected_ids) is list and all(type(x) is str for x in expected_ids),
            'SPLIT_MEMBERS', 'Expected membership must be an explicit identifier list')
    unique(expected_ids, 'Expected split members')
    require(all(type(m) is dict and set(m) == {'id', 'weight', 'case', 'certificate'}
                and type(m['id']) is str for m in members),
            'SPLIT_MEMBER', 'Unexpected or missing member fields')
    unique([m['id'] for m in members], 'Split members')
    require({m['id'] for m in members} == set(expected_ids),
            'SPLIT_MEMBERS', 'A declared member is missing or invented')
    weights = [rational(m['weight']) for m in members]
    tol = rational(tolerance)
    require(tol >= 0 and all(w >= 0 for w in weights) and sum(weights) == 1,
            'SPLIT_WEIGHTS', 'Nonnegative weights must sum to one; tolerance is nonnegative')
    sizes = [(len(encoded(m['case'])), len(encoded(m['certificate']))) for m in members]
    require(all(a <= MAX_INPUT_BYTES and b <= MAX_PACKET_BYTES for a, b in sizes)
            and sum(a for a, _ in sizes) <= MAX_TOTAL_INPUT_BYTES
            and sum(b for _, b in sizes) <= MAX_TOTAL_PROOF_BYTES,
            'SPLIT_SIZE', 'Per-member or declared aggregate byte limit exceeded')
    results, unsupported, anchors_seen, losses = [], [], set(), set()
    for m in members:
        case = validate(m['case'])
        require(case['comparison_id'] == m['id'], 'SPLIT_BINDING', 'Wrong member comparison')
        # Anchor IDs are local to their declared cohort. Different scenes can
        # both contain a-0; the same cohort/anchor cannot be counted twice.
        ids = {(case['cohort_id'], a['id']) for a in case['anchors']}
        require(not (ids & anchors_seen), 'SPLIT_ANCHORS', 'Cohort/anchor records occur in more than one member')
        anchors_seen.update(ids)
        fn, fp = (rational(case['loss'][k]) for k in ('false_negative', 'false_positive'))
        losses.add((fn, fp))
        result = check_member(case, m['certificate'])
        results.append({'id': m['id'], 'execution_status': result['execution_status']})
        if result['model_status'] != 'consistent':
            unsupported.append({'id': m['id'], 'reason': result['execution_status']})
        elif any(not {d['id'] for d in a['output_a']['value']} <=
                     {d['id'] for d in a['output_b']['value']} for a in case['anchors']):
            unsupported.append({'id': m['id'], 'reason': 'requires_preserved_base_additions'})
    require(len(losses) == 1, 'SPLIT_LOSS', 'Members require the same declared loss penalties')
    result = {
        'artifact_id': 'reiyah.perception-revision.split-margin-result', 'version': '0.1.0',
        'execution_status': 'unavailable_members' if unsupported else 'succeeded',
        'margin_status': 'not_evaluated', 'baseline_delta': None,
        'baseline_criterion': 'not_evaluated', 'tolerance': wire(tol),
        'deletion_lower_bound': None, 'deletion_upper_bound': None,
        'minimum_adverse_deletions': None, 'robust_through': None, 'witness_delta': None,
        'witness': [], 'member_checks': results, 'unavailable': unsupported,
        'family': 'independent_reference_record_deletions_preserved_base',
        'scope': 'Declared weighted finite population; membership, weights and fixed references are premises',
        'audit_sufficiency': 'not_established', 'physical_coverage': 'not_established',
        'statistical_confidence_level': None, 'authority_state': 'research_only'
    }
    if unsupported:
        return result
    fn, fp = next(iter(losses))
    delta, groups, candidates = Fraction(0), [], []
    for m, outer_weight in zip(members, weights):
        case, payload = m['case'], m['certificate']
        delta += outer_weight * rational(payload['result']['baseline_delta'])
        proofs = {r['anchor']: r for r in payload['proof']['anchors']}
        by_anchor = {a['id']: a for a in case['anchors']}
        for a in case['anchors']:
            proof = proofs[a['id']]
            gain = len(proof['output_b']['matching']) - len(proof['output_a']['matching'])
            require(gain >= 0, 'SPLIT_GAIN', 'A preserved base cannot have negative matching gain')
            step = outer_weight * rational(a['weight']) * (fn + fp)
            # Deleting k reference vertices changes either matching rank by at
            # most k. The gain cannot drop below zero when A is contained in B.
            # Hence the total adverse decrease is at most step*min(k, gain).
            groups.append((step, gain))
        for item in payload['proof']['pool']:
            a = by_anchor[item['anchor']]
            step = outer_weight * rational(a['weight']) * (fn + fp)
            candidates.append((step, m['id'], item['anchor'], item['object']))
    result.update(baseline_delta=wire(delta),
                  baseline_criterion='supported' if delta > tol else 'excluded')
    if delta <= tol:
        result.update(margin_status='criterion_already_excluded', deletion_lower_bound=0,
                      deletion_upper_bound=0, minimum_adverse_deletions=0, witness_delta=wire(delta))
        return result
    target = delta - tol
    lower = crossing(groups, target)
    require(lower is not None, 'SPLIT_BOUND', 'An additions comparison must allow complete reference deletion')
    # Every subset of the checked right-cover pool removes exactly its own
    # cardinality from B's rank and none from A's rank. Different member records
    # are disjoint, so these decreases add with the declared weights.
    selected, drop = [], Fraction(0)
    for step, mid, aid, oid in sorted(candidates, key=lambda r: (-r[0], r[1:])):
        if step == 0:
            continue
        selected.append({'member': mid, 'anchor': aid, 'object': oid})
        drop += step
        if drop >= target:
            break
    upper = len(selected) if drop >= target else None
    require(upper is None or lower <= upper, 'SPLIT_BOUND', 'Attained upper bound contradicts universal lower bound')
    result.update(margin_status='exact' if lower == upper else 'bounded',
                  deletion_lower_bound=lower, deletion_upper_bound=upper,
                  minimum_adverse_deletions=lower if lower == upper else None,
                  robust_through=lower - 1)
    if upper is not None:
        result.update(witness=selected, witness_delta=wire(delta - drop))
    return result
