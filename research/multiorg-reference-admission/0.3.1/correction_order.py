#!/usr/bin/env python3
"""Authored finite counterexample only. No data, models, or third-party imports."""
from fractions import Fraction
import json


def lineage_mask(rows):
    retained, excluded = [], []
    for row in rows:
        if row['origin'] == 'authored_rpn_padding':
            excluded.append(row['id'])
        elif row['origin'] == 'authored_genuine_proposal':
            retained.append(row)
        else:
            raise ValueError('unresolved origin')
    return retained, excluded


def area(box):
    return max(0, box[2] - box[0]) * max(0, box[3] - box[1])


def overlap(a, b):
    intersection = max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
    union = area(a) + area(b) - intersection
    if union <= 0:
        raise ValueError('undefined zero-union overlap')
    return Fraction(intersection, union)


def ranked_nms_then_cap(rows, cap):
    # Authored explicit continuous-coordinate NMS; ties retain input order.
    ranked = sorted(enumerate(rows), key=lambda entry: (-Fraction(entry[1]['score']), entry[0]))
    kept = []
    for _, row in ranked:
        if all(overlap(row['box'], prior['box']) <= Fraction(1, 2) for prior in kept):
            kept.append(row)
    return kept[:cap]


def main():
    rows = [
        {'id': 'padding', 'box': [0, 0, 0, 0], 'score': '99/100', 'origin': 'authored_rpn_padding'},
        {'id': 'real_a', 'box': [10, 10, 20, 20], 'score': '90/100', 'origin': 'authored_genuine_proposal'},
        {'id': 'real_b', 'box': [30, 30, 40, 40], 'score': '80/100', 'origin': 'authored_genuine_proposal'},
    ]
    pre_rows, excluded_before = lineage_mask(rows)
    early = ranked_nms_then_cap(pre_rows, 2)
    capped = ranked_nms_then_cap(rows, 2)
    late, excluded_after = lineage_mask(capped)
    early_ids, late_ids = [x['id'] for x in early], [x['id'] for x in late]
    assert early_ids == ['real_a', 'real_b']
    assert [x['id'] for x in capped] == ['padding', 'real_a']
    assert late_ids == ['real_a']
    # Equal coordinates cannot substitute for origin evidence.
    zero_real = {'id': 'real_zero', 'box': [0, 0, 0, 0], 'score': '90/100', 'origin': 'authored_genuine_proposal'}
    still_present, excluded = lineage_mask([rows[0], zero_real])
    assert [x['id'] for x in still_present] == ['real_zero'] and excluded == ['padding']
    assert area(still_present[0]['box']) == 0
    result = {
        'artifact_id': 'reiyah.multiorg.correction-order.authored-counterexample',
        'version': '0.1.0', 'status': 'authored_counterexample_confirmed',
        'inputs': rows, 'cap': 2, 'nms_rule': 'suppress IoU > 1/2; continuous coordinates; score descending with stable ties',
        'exclude_before_final_nms_and_cap': early_ids,
        'nms_cap_before_exclusion': [x['id'] for x in capped],
        'exclude_after_final_cap': late_ids,
        'excluded_before': excluded_before, 'excluded_after': excluded_after,
        'equal_zero_origin_control': {'excluded': excluded, 'retained_for_explicit_geometry_refusal': ['real_zero'], 'geometry_only_filter_would_wrongly_hide_genuine_invalid_row': True},
        'scope': 'Possible-input counterexample; authored origins, scores and boxes. No empirical model outputs, image, data or source modules read.',
        'limitations': ['Establishes that correction placement can affect output membership under a cap.', 'Does not establish that an actual tile loses a detection slot or that accuracy, counts or any metric improve.', 'Origin labels are authored assumptions, not a production provenance detector.', 'Zero-union overlap refuses; this example evaluates only zero-versus-positive or positive-versus-positive unions.', 'Genuine invalid geometry remains a refusal, not an automatically excluded placeholder.'],
        'model_executions': 0, 'network_requests': 0,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
