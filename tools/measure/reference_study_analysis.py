"""Unknown-preserving analysis of a two-stage reference audit.

The outcomes concern a fallible, specified review protocol. These calculations
never establish physical truth, reviewer independence, or operator acceptance.
"""
import math


def stratified_srs_bounds(population_n, case_ids, case_bounds, confidence=.95, groups=4):
    """Finite-population randomization inference; no IID-scene claim.

    For L_i <= Y_i <= U_i, estimate the population endpoint means by SRS
    sample endpoint means. Hoeffding without replacement bounds each relevant
    one-sided error by exp(-2*n*epsilon**2). Union over 2*groups tails.
    """
    n = len(case_ids)
    if not 0 < confidence < 1 or groups < 1 or population_n < 0 or n > population_n:
        raise ValueError('Invalid sampling design')
    if len(set(case_ids)) != n:
        raise ValueError('Duplicate sampled case')
    if not population_n:
        return {'state': 'empty_population', 'population_n': 0, 'point_estimate': None,
                'confidence_set': None}
    if not n:
        raise ValueError('Nonempty stratum has no sampled cases')
    values = [case_bounds.get(i, (0, 1)) for i in case_ids]
    if any(not 0 <= lo <= hi <= 1 for lo, hi in values):
        raise ValueError('Invalid outcome bounds')
    lower = sum(v[0] for v in values) / n
    upper = sum(v[1] for v in values) / n
    margin = math.sqrt(math.log(2 * groups / (1 - confidence)) / (2 * n)) if n < population_n else 0.
    unresolved = sum(lo != hi for lo, hi in values)
    return {'state': 'awaiting_independent_review' if unresolved == n else 'review_protocol_estimate',
            'population_n': population_n, 'sampled_n': n, 'resolved_n': n - unresolved,
            'unresolved_or_unreviewed_n': unresolved,
            'support_lower_estimate': lower, 'support_upper_estimate': upper,
            'simultaneous_confidence_level': confidence, 'simultaneous_groups': groups,
            'sampling_margin': margin, 'confidence_set': [max(0., lower-margin), min(1., upper+margin)],
            'point_estimate': lower if unresolved == 0 else None,
            'physical_truth_estimate': None,
            'assumption': 'Uniform sampling without replacement of fixed potential review outcomes; reviewer systematic error and unseen environments are outside the bound.'}


def consensus_bounds(reviews, packet, schema):
    """No review, unusable evidence, or disagreement remains [0, 1]."""
    import jsonschema
    usable = {item['evidence_id']: item['asset_sha256'] for item in packet['evidence']
              if item['state'] == 'available'}
    identities = set()
    answers = []
    for review in reviews:
        jsonschema.Draft202012Validator(schema).validate(review)
        if review['case_id'] != packet['case_id'] or review['protocol_sha256'] != packet['protocol_sha256']:
            raise ValueError('Review case or protocol identity mismatch')
        if review['reviewer_id'] in identities:
            raise ValueError('Repeated reviewer identity does not constitute two reviews')
        identities.add(review['reviewer_id'])
        for citation in review['evidence']:
            if usable.get(citation['evidence_id']) != citation['asset_sha256']:
                raise ValueError('Review cites unavailable or changed sensor evidence')
        decisive = review['outcome'] in ('supported', 'inconsistent')
        if decisive and (review['validity'] != 'usable' or not review['evidence']):
            raise ValueError('Decisive review requires usable cited evidence')
        answers.append(review['outcome'] if review['validity'] == 'usable' else 'unresolved')
    if len(answers) > 2:
        raise ValueError('Third-review adjudication requires a separate protocol')
    if len(answers) != 2 or answers[0] != answers[1]:
        return (0, 1)
    return (1, 1) if answers[0] == 'supported' else (0, 0) if answers[0] == 'inconsistent' else (0, 1)


def two_stage_bounds(cells, case_bounds, confidence=0.95):
    """Per-stratum HT endpoint estimates and conservative confidence sets.

    S scenes, m sampled. Each cell supplies N_s, n_s, and n_s case IDs.
    Missing outcomes are intervals, not nonresponse deletion. The one-sided
    scene bound uses Hoeffding for simple random sampling without replacement;
    the conditional within-scene bound uses its independent-stratum extension.
    Union bound: 4 tails, alpha/4 each (two stages times two endpoints).
    No independence between detections in the physical world is assumed.
    Sampling randomization and fixed potential reviewer outcomes are assumed.
    """
    if not 0 < confidence < 1 or not cells:
        raise ValueError('Invalid confidence level or empty scene population')
    S = len(cells)
    selected = [c for c in cells if c['selected']]
    m = len(selected)
    if m == 0:
        raise ValueError('No scenes selected')
    N = sum(c['population_n'] for c in cells)
    if N == 0:
        return {'state': 'empty_population', 'population_n': 0,
                'ht_lower_estimate': None, 'ht_upper_estimate': None,
                'confidence_set': None, 'point_estimate': None}
    seen = set()
    lo = hi = within_squares = 0.0
    reviewed = unresolved = 0
    for c in cells:
        count = c['population_n']
        ids = c['case_ids']
        n = len(ids)
        if not isinstance(count, int) or count < 0 or n > count:
            raise ValueError('Invalid population or sample size')
        if (not c['selected'] and n) or (c['selected'] and count and not n):
            raise ValueError('Missing selected cases or cases in an unselected scene')
        if not n:
            continue
        weight = S * count / (m * N * n)
        for identity in ids:
            if identity in seen:
                raise ValueError('Duplicate sampled case')
            seen.add(identity)
            lower, upper = case_bounds.get(identity, (0, 1))
            if not 0 <= lower <= upper <= 1:
                raise ValueError('Invalid outcome bounds')
            lo += weight * lower
            hi += weight * upper
            reviewed += lower == upper
            unresolved += lower != upper
        if n < count:
            within_squares += n * weight * weight
    tail_log = math.log(4 / (1 - confidence))
    max_cluster = max(c['population_n'] for c in cells)
    scene_margin = (S * max_cluster / N * math.sqrt(tail_log / (2 * m))) if m < S else 0.
    within_margin = math.sqrt(0.5 * tail_log * within_squares)
    margin = scene_margin + within_margin
    # Projection is for the confidence set ONLY; preserve raw HT endpoint estimates.
    confidence_set = [max(0., lo - margin), min(1., hi + margin)]
    return {'state': 'awaiting_independent_review' if reviewed == 0 else 'review_protocol_estimate',
            'population_n': N, 'sampled_n': len(seen), 'resolved_n': reviewed,
            'unresolved_or_unreviewed_n': unresolved, 'ht_lower_estimate': lo,
            'ht_upper_estimate': hi, 'confidence_level': confidence,
            'scene_sampling_margin': scene_margin, 'within_scene_sampling_margin': within_margin,
            'confidence_set': confidence_set, 'point_estimate': lo if unresolved == 0 else None,
            'physical_truth_estimate': None,
            'assumption': 'Randomized finite-population sample; fixed potential review outcomes. Does not cover systematic reviewer error.'}
