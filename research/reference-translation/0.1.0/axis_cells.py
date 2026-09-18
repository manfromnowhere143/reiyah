"""Exact continuous cells for one-axis translation of a fixed rectangle."""
from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True, order=True)
class Cell:
    left: Fraction
    right: Fraction

    def __post_init__(self):
        if type(self.left) not in (int, Fraction) or type(self.right) not in (int, Fraction):
            raise ValueError('Cell endpoints must be exact rationals')
        object.__setattr__(self, 'left', Fraction(self.left))
        object.__setattr__(self, 'right', Fraction(self.right))
        if self.right < self.left:
            raise ValueError('Reversed cell')

    @property
    def point(self):
        return self.left == self.right

    def representative(self):
        return (self.left + self.right) / 2

    def contains(self, value):
        return value == self.left if self.point else self.left < value < self.right


def edge_interval(base, detection, axis, width, height):
    """Closed legal positions at which a fixed-shape box has IoU >= 1/2."""
    if axis not in (0, 1):
        raise ValueError('Invalid translation axis')
    base = tuple(map(Fraction, base)); detection = tuple(map(Fraction, detection))
    other = 1 - axis
    extent = base[axis + 2] - base[axis]
    orth = base[other + 2] - base[other]
    d_extent = detection[axis + 2] - detection[axis]
    d_orth = detection[other + 2] - detection[other]
    if min(extent, orth, d_extent, d_orth) <= 0:
        raise ValueError('Nonpositive rectangle area')
    domain = Fraction(width if axis == 0 else height) - extent
    if domain < 0:
        raise ValueError('Reference extent exceeds image')
    overlap = min(base[other + 2], detection[other + 2]) - max(base[other], detection[other])
    if overlap <= 0:
        return None
    required = (extent * orth + d_extent * d_orth) / (3 * overlap)
    if required > min(extent, d_extent):
        return None
    left = max(Fraction(0), detection[axis] + required - extent)
    right = min(domain, detection[axis + 2] - required)
    return (left, right) if left <= right else None


def partition(base, detections, axis, width, height):
    base = tuple(map(Fraction, base))
    if axis not in (0, 1) or not (0 <= base[0] < base[2] <= width and 0 <= base[1] < base[3] <= height):
        raise ValueError('Invalid base image geometry or axis')
    limit = Fraction(width if axis == 0 else height) - (base[axis + 2] - base[axis])
    points = {Fraction(0), limit, base[axis]}
    intervals = [edge_interval(base, detection, axis, width, height) for detection in detections]
    for bounds in intervals:
        if bounds is not None:
            points.update(bounds)
    ordered = sorted(points)
    cells = []
    for index, point in enumerate(ordered):
        if index:
            cells.append(Cell(ordered[index - 1], point))
        cells.append(Cell(point, point))
    return cells, intervals


def minimum_radius(cell, original):
    """Infimum distance to a cell, and whether that distance is attained."""
    original = Fraction(original)
    if cell.point:
        return abs(cell.left - original), True
    if cell.contains(original):
        return Fraction(0), True
    return (cell.left - original, False) if original <= cell.left else (original - cell.right, False)


def reachable(cell, original, radius):
    """An attained exact position in the cell/radius intersection, or None."""
    original, radius = Fraction(original), Fraction(radius)
    if radius < 0:
        raise ValueError('Negative radius')
    if cell.point:
        return cell.left if abs(cell.left - original) <= radius else None
    left = max(cell.left, original - radius)
    right = min(cell.right, original + radius)
    if left < right:
        return (left + right) / 2
    if left == right and cell.contains(left):
        return left
    return None


def translate(base, axis, position):
    if axis not in (0, 1):
        raise ValueError('Invalid translation axis')
    base = list(map(Fraction, base)); position = Fraction(position)
    extent = base[axis + 2] - base[axis]
    base[axis], base[axis + 2] = position, position + extent
    return tuple(base)
