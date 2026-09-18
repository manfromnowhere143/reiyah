"""Retrospective finite operating curves; no calibrated probabilities."""
from operating_sources import require

MAX_PAIRS = 1000000


def frontier(curve):
    require(curve and len({row['cell_id'] for row in curve}) == len(curve), 'Missing or repeated curve cells')
    require(all(type(row['false_positives']) is int and row['false_positives'] >= 0
                and type(row['misses']) is int and row['misses'] >= 0 for row in curve), 'Invalid curve counts')
    points = sorted({(row['false_positives'], row['misses']) for row in curve}); best = None; result = []
    for fp, fn in points:
        if best is None or fn < best:
            result.append({'false_positives': fp, 'misses': fn,
                           'cell_ids': [row['cell_id'] for row in curve if (row['false_positives'], row['misses']) == (fp, fn)]})
            best = fn
    return result


def budget_minima(curve, maximum):
    require(type(maximum) is int and maximum >= 0, 'Invalid false-positive budget')
    rows = []
    for budget in range(maximum+1):
        feasible = [row for row in curve if row['false_positives'] <= budget]
        best = min((row['misses'] for row in feasible), default=None)
        rows.append({'false_positive_budget': budget, 'state': 'available' if feasible else 'infeasible',
                     'minimum_misses': best, 'cell_ids': [row['cell_id'] for row in feasible if row['misses'] == best]})
    return rows


def compare_curves(first, second, maximum_budget, pair_limit=MAX_PAIRS):
    require(len(first)*len(second) <= pair_limit, 'Nominal threshold pair limit')
    frontiers = [frontier(curve) for curve in (first, second)]
    minima = [budget_minima(curve, maximum_budget) for curve in (first, second)]
    budgets = []
    for a, b in zip(*minima):
        available = a['state'] == b['state'] == 'available'
        difference = a['minimum_misses']-b['minimum_misses'] if available else None
        budgets.append({'false_positive_budget': a['false_positive_budget'], 'roles': [a, b],
                        'miss_difference_old_minus_new': difference,
                        'comparison': 'unavailable' if not available else 'new_fewer_misses' if difference > 0
                        else 'old_fewer_misses' if difference < 0 else 'equal_misses'})
    matrix = []; positive = nonpositive = 0
    for a in first:
        values = [a['false_positives']+a['misses']-b['false_positives']-b['misses'] for b in second]
        matrix.append({'old_cell_id': a['cell_id'], 'old_minus_new_total_loss': values})
        positive += sum(value > 0 for value in values); nonpositive += sum(value <= 0 for value in values)
    minima_loss = []
    for curve in (first, second):
        best = min(row['false_positives']+row['misses'] for row in curve)
        minima_loss.append({'minimum_unit_loss': best, 'cell_ids': [row['cell_id'] for row in curve
                                                                  if row['false_positives']+row['misses'] == best]})
    return {'frontiers': frontiers, 'false_positive_budgets': budgets,
            'nominal_pair_grid': {'new_cell_ids': [row['cell_id'] for row in second], 'rows': matrix,
                                 'allocated_pairs': len(first)*len(second), 'positive_pairs': positive,
                                 'nonpositive_pairs': nonpositive},
            'retrospective_minimum_unit_losses': minima_loss, 'thresholds_selected_for_deployment': False}
