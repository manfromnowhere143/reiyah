"""Exact constant-penalty loss transfer and complete share-domain partitions."""
from fractions import Fraction

SHARES = (Fraction(0), Fraction(1, 5), Fraction(1, 3), Fraction(1, 2), Fraction(2, 3),
          Fraction(4, 5), Fraction(8, 9), Fraction(16, 17), Fraction(1))
POLICY = {'kind': 'common_constant_penalty_share', 'false_positive_weight': '1-p',
          'miss_weight': 'p', 'domain': ['0/1', '1/1'], 'prediction_sets': 'fixed',
          'matching': 'maximum_one_to_one_at_iou_at_least_one_half'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_policy(value):
    require(type(value) is dict and value == POLICY, 'Only the declared common constant-weight contract is supported')


def share(value):
    value = Fraction(value)
    require(0 <= value <= 1, 'Penalty share must lie in the closed unit interval')
    return value


def loss(predictions, references, matching, p):
    require(all(type(value) is int and value >= 0 for value in (predictions, references, matching))
            and matching <= min(predictions, references), 'Invalid prediction/reference/matching counts')
    p = share(p)
    return (1 - p) * (predictions - matching) + p * (references - matching)


def difference(count_difference, rank_difference, p):
    return (1 - share(p)) * Fraction(count_difference) + Fraction(rank_difference)


def transfer(unit_value, count_difference, p):
    return Fraction(unit_value) / 2 + (Fraction(1, 2) - share(p)) * Fraction(count_difference)


def bounds(unit_bounds, count_difference, p):
    low, high = map(Fraction, unit_bounds)
    require(low <= high, 'Reversed source enclosure')
    return transfer(low, count_difference, p), transfer(high, count_difference, p)


def decision(interval):
    low, high = map(Fraction, interval)
    require(low <= high, 'Reversed weighted enclosure')
    return 'supported' if low > 0 else 'excluded' if high <= 0 else 'unresolved'


def partition(unit_bounds, count_difference):
    low, high = map(Fraction, unit_bounds); count_difference = Fraction(count_difference)
    require(low <= high, 'Reversed source enclosure')
    cuts = {Fraction(0), Fraction(1)}
    if count_difference:
        for value in (low, high):
            root = (value + count_difference) / (2 * count_difference)
            if 0 <= root <= 1:
                cuts.add(root)
    ordered = sorted(cuts); cells = []
    for index, point in enumerate(ordered):
        if index:
            left = ordered[index - 1]; representative = (left + point) / 2
            interval = bounds((low, high), count_difference, representative)
            cells.append({'left': left, 'right': point, 'point': False, 'representative': representative,
                          'bounds': interval, 'decision': decision(interval)})
        interval = bounds((low, high), count_difference, point)
        cells.append({'left': point, 'right': point, 'point': True, 'representative': point,
                      'bounds': interval, 'decision': decision(interval)})
    return cells


def penalty_ratio(p):
    p = share(p)
    return None if p == 1 else p / (1 - p)
