"""Finite probability reference, independent of acquisition/objective formulas."""

from fractions import Fraction
from itertools import combinations


def variance_by_enumeration(losses, probabilities):
    n = len(losses)
    if n < 2 or len(probabilities) != n or len(losses[0]) < 2:
        raise ValueError("shape")
    k = len(losses[0])
    if any(len(row) != k for row in losses):
        raise ValueError("shape")
    q = [Fraction(value) for value in probabilities]
    if any(value <= 0 for value in q) or sum(q) != 1:
        raise ValueError("probability")
    rows = [[Fraction(value) for value in row] for row in losses]
    result = []
    for left, right in combinations(range(k), 2):
        outcomes = [
            (prob, (row[left] - row[right]) / (n * prob)) for row, prob in zip(rows, q)
        ]
        mean = sum(prob * estimate for prob, estimate in outcomes)
        target = sum(row[left] - row[right] for row in rows) / n
        if mean != target:
            raise ValueError("expectation")
        variance = sum(prob * (estimate - mean) ** 2 for prob, estimate in outcomes)
        result.append(
            {"pair": [left, right], "expectation": str(mean), "variance": str(variance)}
        )
    return sum(Fraction(row["variance"]) for row in result), result
