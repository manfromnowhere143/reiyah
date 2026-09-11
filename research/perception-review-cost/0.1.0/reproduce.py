"""Exact synthetic observation-query costs; not a model of human review effort."""
from fractions import Fraction
from functools import lru_cache
from itertools import product
import json


def maximum_matching(left, objects, edges):
    """Enumerate partial injective assignments; no Engine or producer imports."""
    best = 0
    for choices in product([None] + objects, repeat=len(left)):
        selected = [obj for obj in choices if obj is not None]
        if len(selected) != len(set(selected)):
            continue
        if all(obj is None or (det, obj) in edges for det, obj in zip(left, choices)):
            best = max(best, len(selected))
    return best


def example(n):
    """One addition sees known A; only the base can reach any disputed B_i."""
    worlds = list(product((False, True), repeat=n))
    rows = []
    for bits in worlds:
        objects = ['A'] + ['B' + str(i) for i, present in enumerate(bits) if present]
        edges = {('base', obj) for obj in objects} | {('added', 'A')}
        base_tp = maximum_matching(['base'], objects, edges)
        aug_tp = maximum_matching(['base', 'added'], objects, edges)
        base_loss = len(objects) - base_tp + 1 - base_tp
        aug_loss = len(objects) - aug_tp + 2 - aug_tp
        rows.append({'presence': list(bits), 'base_tp': base_tp, 'augmented_tp': aug_tp,
                     'loss_base': base_loss, 'loss_augmented': aug_loss,
                     'delta': base_loss - aug_loss})
    labels = [row['delta'] > 0 for row in rows]

    @lru_cache(None)
    def depth(indices):
        if len({labels[i] for i in indices}) == 1:
            return 0
        costs = []
        for query in range(n):
            partitions = tuple(tuple(i for i in indices if worlds[i][query] is value)
                               for value in (False, True))
            if all(partitions):
                costs.append(1 + max(depth(part) for part in partitions))
        assert costs, 'Distinct complete assignments must admit a separating query'
        return min(costs)

    minimum = depth(tuple(range(len(worlds))))
    assert minimum == n
    assert {row['delta'] for row in rows} == {-1, 1}
    assert all((row['delta'] == 1) == any(row['presence']) for row in rows)
    result = {'retained_additions': 1, 'disputed_base_only_objects': n,
              'candidate_to_known_object_edge': ['added', 'A'],
              'candidate_evidence_identical_in_every_world': True,
              'possible_unit_loss_differences': [-1, 1],
              'minimum_worst_case_exact_presence_queries': minimum}
    if n == 2:
        result['all_worlds'] = rows
    return result


def cohort():
    """This is the supplied loss/weight arithmetic, not independent trials."""
    tolerance = Fraction(1, 10)
    for first, second in product(range(10), range(8)):
        delta = Fraction(1, 2) * (2 * first - 9) + Fraction(1, 2) * (2 * second - 7)
        assert delta == first + second - 8
        assert (delta > tolerance) == (first + second >= 9)
    return {'retained_additions': [9, 7], 'weights': ['1/2', '1/2'],
            'false_negative_penalty': '1', 'false_positive_penalty': '1',
            'tolerance': '1/10', 'weighted_delta': 'gain_1 + gain_2 - 8',
            'improvement_supported_iff_total_gain_at_least': 9,
            'example': {'gains': [7, 2], 'anchor_deltas': [5, -3],
                        'weighted_delta': 1, 'cohort_preference': 'prefer_augmented'},
            'limit': 'Possible integer gains only; no observed gains, priors or review outcomes.'}


def main():
    print(json.dumps({'artifact_id': 'reiyah.perception-review-cost.synthetic-calculation',
                      'version': '0.1.0', 'evidence_kind': 'synthetic',
                      'query': 'Reveal one disputed object presence bit exactly; all other operands fixed.',
                      'cases': [example(n) for n in (1, 2, 4, 8)],
                      'weighted_cohort_arithmetic': cohort(),
                      'physical_judgments': 'not_measured',
                      'expected_human_effort': 'not_established'},
                     sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
