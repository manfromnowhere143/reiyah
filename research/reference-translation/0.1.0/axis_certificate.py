"""Separate piecewise overlap and matching checks for translation coverage.

This module does not call the producer's edge-interval formula, cell search,
flow matcher, minimum-query solver or critical-radius event sweep.
"""
from fractions import Fraction


def axis_overlap(position, extent, left, right):
    return max(Fraction(0), min(position + extent, right) - max(position, left))


def piecewise_interval(base, detection, axis, width, height):
    base = tuple(map(Fraction, base)); detection = tuple(map(Fraction, detection))
    if axis not in (0, 1):
        raise ValueError('Unknown axis')
    other = 1 - axis
    extent = base[axis + 2] - base[axis]
    orth = base[other + 2] - base[other]
    d_extent = detection[axis + 2] - detection[axis]
    d_orth = detection[other + 2] - detection[other]
    limit = Fraction(width if axis == 0 else height) - extent
    if min(extent, orth, d_extent, d_orth) <= 0 or limit < 0:
        raise ValueError('Invalid rectangle')
    orth_overlap = max(Fraction(0), min(base[other + 2], detection[other + 2]) - max(base[other], detection[other]))
    if orth_overlap == 0:
        return None
    required = (extent * orth + d_extent * d_orth) / (3 * orth_overlap)
    dleft, dright = detection[axis], detection[axis + 2]
    points = {Fraction(0), limit}
    # All changes of slope for min/max in the overlap expression.
    points.update(value for value in [dleft - extent, dleft, dright - extent, dright] if 0 <= value <= limit)
    ordered = sorted(points); admitted = []
    if limit == 0:
        return (Fraction(0), Fraction(0)) if axis_overlap(0, extent, dleft, dright) >= required else None
    for left, right in zip(ordered, ordered[1:]):
        fl = axis_overlap(left, extent, dleft, dright) - required
        fr = axis_overlap(right, extent, dleft, dright) - required
        if fl >= 0 and fr >= 0:
            admitted.append((left, right))
        elif fl < 0 and fr < 0:
            continue
        else:
            root = left - fl * (right - left) / (fr - fl)
            admitted.append((left, root) if fl >= 0 else (root, right))
    if not admitted:
        return None
    lower, upper = admitted[0]
    for left, right in admitted[1:]:
        if left > upper:
            raise ValueError('Unexpected disconnected overlap superlevel set')
        upper = max(upper, right)
    return lower, upper


def expected_cells(base, detections, axis, width, height):
    base = tuple(map(Fraction, base))
    limit = Fraction(width if axis == 0 else height) - (base[axis + 2] - base[axis])
    positions = {Fraction(0), limit, base[axis]}
    intervals = []
    for detection in detections:
        found = piecewise_interval(base, detection, axis, width, height)
        intervals.append(found)
        if found is not None:
            positions.update(found)
    ordered = sorted(positions)
    cells = []
    for index, value in enumerate(ordered):
        if index:
            cells.append((ordered[index - 1], value))
        cells.append((value, value))
    return cells, intervals


def maximum_matching(adjacency):
    """Independent augmenting-path cardinality, with no flow-network code."""
    right_owner = {}
    def augment(left, seen):
        for right in sorted(adjacency[left]):
            if right in seen:
                continue
            seen.add(right)
            if right not in right_owner or augment(right_owner[right], seen):
                right_owner[right] = left
                return True
        return False
    for left in sorted(adjacency):
        augment(left, set())
    return len(right_owner)


def exact_iou(first, second):
    a, b = tuple(map(Fraction, first)), tuple(map(Fraction, second))
    intersection = max(Fraction(0), min(a[2], b[2]) - max(a[0], b[0])) * max(
        Fraction(0), min(a[3], b[3]) - max(a[1], b[1]))
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - intersection
    if union <= 0:
        raise ValueError('Invalid area')
    return intersection / union


def checked_radius_membership(left, right, center, radius):
    """Reachability computed from interval intersections, independent of activation metadata."""
    lower = max(left, center - radius); upper = min(right, center + radius)
    if lower > upper:
        return False
    if left == right:
        return lower == upper == left
    return lower < upper or left < lower == upper < right
