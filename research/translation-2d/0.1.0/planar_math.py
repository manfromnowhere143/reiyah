"""Exact overlap envelopes and coupled one-reference rank increments."""
from fractions import Fraction
from itertools import product


def domain(base, radius, width, height):
    base = tuple(map(Fraction, base)); radius = Fraction(radius)
    x, y, right, bottom = base
    if radius < 0 or not (0 <= x < right <= width and 0 <= y < bottom <= height):
        raise ValueError('Invalid source rectangle or radius')
    return (max(Fraction(0), x - radius), max(Fraction(0), y - radius),
            min(Fraction(width) - (right - x), x + radius),
            min(Fraction(height) - (bottom - y), y + radius))


def overlap(position, span, left, right):
    return max(Fraction(0), min(position + span, right) - max(position, left))


def overlap_range(lo, hi, span, left, right):
    lo, hi, span, left, right = map(Fraction, (lo, hi, span, left, right))
    if lo > hi or span <= 0 or left >= right:
        raise ValueError('Invalid interval or extent')
    points = {lo, hi}
    points.update(p for p in (left - span, left, right - span, right) if lo <= p <= hi)
    values = [overlap(p, span, left, right) for p in points]
    return min(values), max(values)


def edge_envelope(base, detection, region):
    base, detection, region = (tuple(map(Fraction, values)) for values in (base, detection, region))
    width, height = base[2] - base[0], base[3] - base[1]
    dw, dh = detection[2] - detection[0], detection[3] - detection[1]
    if min(width, height, dw, dh) <= 0:
        raise ValueError('Nonpositive box area')
    xmin, xmax = overlap_range(region[0], region[2], width, detection[0], detection[2])
    ymin, ymax = overlap_range(region[1], region[3], height, detection[1], detection[3])
    minimum, maximum = xmin * ymin, xmax * ymax
    required = (width * height + dw * dh) / 3
    return {'must': minimum >= required, 'may': maximum >= required,
            'minimum_intersection': minimum, 'maximum_intersection': maximum,
            'required_intersection': required}


def increment_pairs(must, may, augment_a, augment_b):
    must, may, augment_a, augment_b = map(set, (must, may, augment_a, augment_b))
    if not must <= may:
        raise ValueError('Mandatory neighbor absent from possible neighbors')
    pairs = []
    for a, b in product((0, 1), repeat=2):
        forbidden = (augment_a if a == 0 else set()) | (augment_b if b == 0 else set())
        if must & forbidden:
            continue
        allowed = may - forbidden
        if (a and not allowed & augment_a) or (b and not allowed & augment_b):
            continue
        pairs.append((a, b))
    if not pairs:
        raise ValueError('A valid neighborhood interval must admit at least one rank pair')
    return pairs


def rank_enclosure(base_delta, must, may, augment_a, augment_b):
    pairs = increment_pairs(must, may, augment_a, augment_b)
    values = [base_delta + 2 * (b - a) for a, b in pairs]
    return (min(values), max(values)), pairs


def points(region, original=None):
    x1, y1, x2, y2 = map(Fraction, region)
    if x1 > x2 or y1 > y2:
        raise ValueError('Reversed region')
    values = {(x1, y1), (x1, y2), (x2, y1), (x2, y2), ((x1 + x2) / 2, (y1 + y2) / 2)}
    if original is not None and x1 <= original[0] <= x2 and y1 <= original[1] <= y2:
        values.add(tuple(map(Fraction, original)))
    return sorted(values)


def split(region):
    x1, y1, x2, y2 = map(Fraction, region)
    if x1 > x2 or y1 > y2 or (x1 == x2 and y1 == y2):
        raise ValueError('Region has no splittable extent')
    if x2 - x1 >= y2 - y1:
        midpoint = (x1 + x2) / 2
        return 0, (x1, y1, midpoint, y2), (midpoint, y1, x2, y2)
    midpoint = (y1 + y2) / 2
    return 1, (x1, y1, x2, midpoint), (x1, midpoint, x2, y2)
