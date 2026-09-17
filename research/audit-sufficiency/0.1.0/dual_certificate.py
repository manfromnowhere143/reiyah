"""Solver-free lower bounds for the adversary programs, by exact rational LP duality.

Both adversaries (deletion in sufficiency.py, boundary flips in localization.py) are programs

    minimise c^T x   subject to  lo <= A x <= hi,  0 <= x <= 1,  some x integer.

For any multipliers y_lo >= 0 on the lower rows and y_hi >= 0 on the upper rows, every feasible
x (integer or not) satisfies

    c^T x >= y_lo^T lo - y_hi^T hi + sum_j min(0, r_j),   r = c - A^T (y_lo - y_hi),

because y_lo^T (A x - lo) >= 0, y_hi^T (hi - A x) >= 0 and 0 <= x_j <= 1 (Neumaier and
Shcherbina, 2004). The multipliers come from the LP relaxation's dual as floats, are converted to
rationals, and the bound is then evaluated exactly; no property of the solver is trusted. The
adversary's objective is an integer (a gain), so the bound rounds up.

A certificate is the rational vector y with the two row index sets; a checker recomputes the
bound from the program's exact data. `certified_min_objective` <= true optimum always.
"""
from fractions import Fraction

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix


def rational_matrix(A):
    A = csr_matrix(A)
    return A


def rigorous_bound(cost, A, lo, hi, y_lo, y_hi):
    """Exact evaluation of the Neumaier-Shcherbina bound for rational multipliers."""
    A = csr_matrix(A)
    n = A.shape[1]
    # r = c - A^T (y_lo - y_hi), exactly
    y = [y_lo[i] - y_hi[i] for i in range(A.shape[0])]
    r = [Fraction(int(round(c))) if float(c).is_integer() else Fraction(c) for c in cost]
    A_coo = A.tocoo()
    for i, j, v in zip(A_coo.row, A_coo.col, A_coo.data):
        if y[i] != 0:
            r[j] -= Fraction(int(v)) * y[i] if float(v).is_integer() else Fraction(v) * y[i]
    bound = Fraction(0)
    for i in range(A.shape[0]):
        if y_lo[i]:
            assert lo[i] != -np.inf
            bound += y_lo[i] * Fraction(int(lo[i]))
        if y_hi[i]:
            assert hi[i] != np.inf
            bound -= y_hi[i] * Fraction(int(hi[i]))
    bound += sum((min(Fraction(0), rj) for rj in r), Fraction(0))
    return bound


def dual_bound(cost, A, lo, hi, denominator_limit=10 ** 6):
    """Solve the LP relaxation, rationalize its duals, and return the rigorous bound with the certificate."""
    A = csr_matrix(A)
    m, n = A.shape
    lo = np.asarray(lo, dtype=float)
    hi = np.asarray(hi, dtype=float)
    # linprog form: A_ub x <= b_ub. Lower rows: -A x <= -lo. Upper rows: A x <= hi.
    rows_lo = [i for i in range(m) if lo[i] != -np.inf]
    rows_hi = [i for i in range(m) if hi[i] != np.inf]
    A_ub = None
    b_ub = []
    blocks = []
    if rows_lo:
        blocks.append(-A[rows_lo])
        b_ub.extend((-lo[i] for i in rows_lo))
    if rows_hi:
        blocks.append(A[rows_hi])
        b_ub.extend((hi[i] for i in rows_hi))
    from scipy.sparse import vstack
    A_ub = vstack(blocks).tocsr()
    res = linprog(c=np.asarray(cost, dtype=float), A_ub=A_ub, b_ub=np.asarray(b_ub), bounds=(0, 1), method='highs')
    if res.status != 0:
        return None
    marg = -np.asarray(res.ineqlin.marginals)   # multipliers >= 0 for A_ub x <= b_ub
    y_lo = [Fraction(0)] * m
    y_hi = [Fraction(0)] * m
    k = 0
    for i in rows_lo:
        y_lo[i] = max(Fraction(0), Fraction(float(marg[k])).limit_denominator(denominator_limit))
        k += 1
    for i in rows_hi:
        y_hi[i] = max(Fraction(0), Fraction(float(marg[k])).limit_denominator(denominator_limit))
        k += 1
    bound = rigorous_bound(cost, A, lo, hi, y_lo, y_hi)
    return {'bound': bound, 'lp_value': float(res.fun), 'y_lo': y_lo, 'y_hi': y_hi}
