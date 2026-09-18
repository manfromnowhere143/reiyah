"""Retrospective minimum query subsets under the frozen stopping mathematics.

All answers are known here. This is a certificate-size lower bound, never an
available selection policy. Only equal unit observation costs are addressed.
"""
from fractions import Fraction

from admission import require
from compare_math import FAMILIES, decision, interval, linked, open_interval, q, wire_interval


def minimum_certificate(images, measurements, family):
    require(family in FAMILIES and images, 'FAMILY', 'Nonempty declared family required')
    if not all(linked(image) for image in images):
        return {'decision': 'input_blocked', 'full_bounds': None, 'retrospective_all_answers_known': False,
                'minimum_queries': None, 'sufficient_subset': None, 'reason': 'Unavailable inputs are not empty answers.'}
    require(all(image['id'] in measurements for image in images), 'ANSWER', 'Full retrospective answers required')
    full = interval(images, measurements, family); outcome = decision(full)
    base = {'decision': outcome, 'full_bounds': wire_interval(full), 'retrospective_all_answers_known': True}
    if outcome in ('unresolved', 'input_blocked'):
        return {**base, 'minimum_queries': None, 'sufficient_subset': None,
                'reason': 'Complete supplied information does not certify a decision under these bounds.'}
    initial = interval(images, {}, family)
    if decision(initial) == outcome:
        return {**base, 'minimum_queries': 0, 'sufficient_subset': [], 'subset_bounds': wire_interval(initial)}
    direction = 1 if outcome == 'supported' else -1
    threshold = sum(open_interval(image)[1] for image in images)
    rows = []
    for image in images:
        radius = open_interval(image)[1]
        if radius == 0:
            continue
        measured = measurements[image['id']]
        nominal = q(measured['nominal']['delta']); lo, hi = map(q, measured['edit_bounds'])
        if family == 'one_edit_per_image':
            contribution = lo if direction == 1 else -hi; penalty = Fraction(0)
        else:
            contribution = direction * nominal
            penalty = nominal - lo if direction == 1 else hi - nominal
            if family == 'exact_projection':
                penalty = Fraction(0)
        gain = radius + contribution
        require(gain >= 0 and penalty >= 0 and (family != 'one_edit_global' or gain >= penalty),
                'BOUND', 'Answers must preserve monotonic sound enclosures')
        rows.append({'id': image['id'], 'ordinal': image['ordinal'], 'gain': gain, 'penalty': penalty})
    penalties = sorted({Fraction(0)} | {row['penalty'] for row in rows}) if family == 'one_edit_global' else [Fraction(0)]
    candidates = []
    for limit in penalties:
        ordered = sorted((row for row in rows if row['penalty'] <= limit), key=lambda row: (-row['gain'], row['ordinal']))
        gain = penalty = Fraction(0); selected = []
        for row in ordered:
            selected.append(row['id']); gain += row['gain']; penalty = max(penalty, row['penalty'])
            enough = gain - penalty > threshold if outcome == 'supported' else gain - penalty >= threshold
            if enough:
                candidates.append(selected); break
    require(candidates, 'BOUND', 'Resolved full case must have a sufficient query subset')
    chosen = min(candidates, key=lambda values: (len(values), values))
    subset_bounds = interval(images, {iid: measurements[iid] for iid in chosen}, family)
    require(decision(subset_bounds) == outcome, 'BOUND', 'Constructed subset does not certify the full decision')
    return {**base, 'minimum_queries': len(chosen), 'sufficient_subset': chosen, 'subset_bounds': wire_interval(subset_bounds)}
