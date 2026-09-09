"""Exact nominal rigid transforms; no pose accuracy or object-motion inference.

Decimal source operands become rational numbers. Quaternion scale is removed by
division by its squared norm, avoiding a rounded square root. The near-unit check
is an input-format screen, not an uncertainty bound on the physical rotation.
"""
from fractions import Fraction

from tools.perception_decision.contract import wire
from tools.perception_decision.nuscenes import _number
from tools.perception_inputs.source_io import require

MAX_SQUARED_NORM_ERROR = Fraction(1, 1_000_000)


def vector(values, count):
    require(type(values) is list and len(values) == count,
            'GEOMETRY_SHAPE', 'Expected a fixed-length numeric source vector')
    return tuple(_number(v) for v in values)


def rotation(quaternion):
    w, x, y, z = vector(quaternion, 4)
    s = w*w + x*x + y*y + z*z
    require(abs(s-1) <= MAX_SQUARED_NORM_ERROR, 'GEOMETRY_QUATERNION',
            'Squared quaternion norm is outside the declared near-unit input profile')
    return ((1-2*(y*y+z*z)/s, 2*(x*y-z*w)/s, 2*(x*z+y*w)/s),
            (2*(x*y+z*w)/s, 1-2*(x*x+z*z)/s, 2*(y*z-x*w)/s),
            (2*(x*z-y*w)/s, 2*(y*z+x*w)/s, 1-2*(x*x+y*y)/s))


def rigid(translation, quaternion):
    t, r = vector(translation, 3), rotation(quaternion)
    return tuple(r[i] + (t[i],) for i in range(3)) + ((Fraction(0), Fraction(0), Fraction(0), Fraction(1)),)


def multiply(left, right):
    return tuple(tuple(sum(left[i][k]*right[k][j] for k in range(4))
                       for j in range(4)) for i in range(4))


def inverse(matrix):
    # R is orthogonal exactly under the rational quaternion construction.
    return tuple(tuple(matrix[j][i] for j in range(3)) +
                 (-sum(matrix[j][i]*matrix[j][3] for j in range(3)),)
                 for i in range(3)) + ((Fraction(0), Fraction(0), Fraction(0), Fraction(1)),)


def intrinsic(values):
    require(type(values) is list and len(values) == 3,
            'GEOMETRY_INTRINSIC', 'Expected a 3-by-3 pinhole intrinsic matrix')
    k = tuple(vector(row, 3) for row in values)
    require(k[0][0] > 0 and k[1][1] > 0 and k[1][0] == 0 and k[2] == (0, 0, 1),
            'GEOMETRY_INTRINSIC', 'Unsupported pinhole intrinsic form')
    return k


def matrix_wire(matrix):
    return [[wire(v) for v in row] for row in matrix]
