"""Separate scalar interpolation, rigid transforms and polygon clipping checks.

No numpy, scipy, pyquaternion, shapely or SDK projection code is called here.
Agreement checks float computation; it does not certify real physical geometry.
"""
from fractions import Fraction
import itertools
import math


def unit(values):
    if len(values) != 4 or any(not math.isfinite(x) for x in values):
        raise ValueError('Invalid quaternion')
    length = math.hypot(*values)
    if length == 0:
        raise ValueError('Zero quaternion')
    return [x / length for x in values]


def slerp(start, finish, fraction):
    a, b = unit(start), unit(finish)
    dot = math.fsum(x*y for x, y in zip(a, b))
    if dot < 0:
        b = [-x for x in b]; dot = -dot
    dot = max(-1.0, min(1.0, dot))
    if dot > 0.9995:
        return unit([x + fraction*(y-x) for x, y in zip(a, b)])
    angle = math.acos(dot)
    left = math.sin((1-fraction)*angle) / math.sin(angle)
    right = math.sin(fraction*angle) / math.sin(angle)
    return unit([left*x + right*y for x, y in zip(a, b)])


def alternate_motion(current, previous, amount, kind):
    if kind == 'current_time':
        return {'translation': list(map(float, current['translation'])),
                'rotation': unit(current['rotation']), 'size': list(map(float, current['size']))}
    fraction = float(Fraction(amount))
    center = [(1-fraction)*a + fraction*b for a, b in zip(previous['translation'], current['translation'])]
    return {'translation': center, 'rotation': slerp(previous['rotation'], current['rotation'], fraction),
            'size': list(map(float, current['size']))}


def rotation(values):
    w, x, y, z = unit(values)
    return [[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
            [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
            [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]]


def multiply(matrix, vector):
    return [math.fsum(a*b for a, b in zip(row, vector)) for row in matrix]


def inverse_transform(point, pose):
    matrix = rotation(pose['rotation'])
    relative = [x-y for x, y in zip(point, pose['translation'])]
    return [math.fsum(matrix[j][i]*relative[j] for j in range(3)) for i in range(3)]


def cross(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])


def hull(points):
    points = sorted(set(map(tuple, points)))
    if len(points) <= 1:
        return points
    low, high = [], []
    for point in points:
        while len(low) >= 2 and cross(low[-2], low[-1], point) <= 0:
            low.pop()
        low.append(point)
    for point in reversed(points):
        while len(high) >= 2 and cross(high[-2], high[-1], point) <= 0:
            high.pop()
        high.append(point)
    return low[:-1] + high[:-1]


def clip(polygon, width, height):
    for axis, boundary, keep_greater in [(0, 0, True), (0, width, False), (1, 0, True), (1, height, False)]:
        if not polygon:
            return []
        output = []; previous = polygon[-1]
        prev_in = previous[axis] >= boundary if keep_greater else previous[axis] <= boundary
        for point in polygon:
            inside = point[axis] >= boundary if keep_greater else point[axis] <= boundary
            if inside != prev_in:
                amount = (boundary-previous[axis]) / (point[axis]-previous[axis])
                intersection = tuple(boundary if j == axis else previous[j] + amount*(point[j]-previous[j]) for j in (0, 1))
                output.append(intersection)
            if inside:
                output.append(point)
            previous, prev_in = point, inside
        polygon = output
    return polygon


def project(modeled, pose, calibration, width=1600, height=900):
    dimensions = modeled['size']; matrix = rotation(modeled['rotation']); points = []
    for sx, sy, sz in itertools.product((-1, 1), repeat=3):
        local = [sx*dimensions[1]/2, sy*dimensions[0]/2, sz*dimensions[2]/2]
        global_point = [a+b for a, b in zip(multiply(matrix, local), modeled['translation'])]
        camera = inverse_transform(inverse_transform(global_point, pose), calibration)
        if camera[2] <= 0:
            continue
        homogeneous = multiply(calibration['camera_intrinsic'], camera)
        points.append((homogeneous[0]/homogeneous[2], homogeneous[1]/homogeneous[2]))
    if not points:
        return None
    polygon = clip(hull(points), width, height)
    if not polygon:
        return None
    xs, ys = zip(*polygon); box = [min(xs), min(ys), max(xs), max(ys)]
    if box[0] >= box[2] or box[1] >= box[3]:
        raise ValueError('Degenerate projected hull')
    return box


def eligible(coordinates):
    return coordinates is not None and Fraction(str(coordinates[3])) - Fraction(str(coordinates[1])) >= 25


def close_coordinates(first, second):
    if (first is None) != (second is None):
        raise ValueError('Projection visibility disagreement')
    if first is None:
        return 0.0
    errors = [abs(a-b) for a, b in zip(first, second)]
    if any(error > 1e-7 + 1e-12*max(abs(a), abs(b)) for error, a, b in zip(errors, first, second)):
        raise ValueError('Projection coordinate disagreement')
    if eligible(first) != eligible(second):
        raise ValueError('Projection eligibility disagreement')
    return max(errors, default=0.0)


def close_motion(first, second):
    if first['size'] != second['size']:
        raise ValueError('Modeled dimensions differ')
    errors = [abs(a-b) for a, b in zip(first['translation'], second['translation'])]
    if any(error > 1e-9 + 1e-12*max(abs(a), abs(b))
           for error, a, b in zip(errors, first['translation'], second['translation'])):
        raise ValueError('Interpolated centers differ')
    a, b = rotation(first['rotation']), rotation(second['rotation'])
    angular = max(abs(a[i][j]-b[i][j]) for i in range(3) for j in range(3))
    if angular > 1e-10:
        raise ValueError('Interpolated orientations differ')
    return {'center_absolute_error': max(errors, default=0.0), 'rotation_matrix_absolute_error': angular}
