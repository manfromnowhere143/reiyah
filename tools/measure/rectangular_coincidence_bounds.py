#!/usr/bin/env python3
"""Rational enclosures of coincidence-ratio extrema on a rectangular cell domain.

These are mathematical bounds for supplied nonnegative cell ranges, not a
reference-error model, a sampling-confidence interval or a safety certificate.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as F
import hashlib
import json
from math import isqrt
from pathlib import Path
import re
import sys


NUMBER = re.compile(r"(?:0|[1-9][0-9]{0,31})(?:\.[0-9]{1,32}|/[1-9][0-9]{0,31})?\Z")
CELL_NAMES = ("both", "a_only", "b_only", "neither")


def number(value):
    if type(value) is int or isinstance(value, F):
        result = F(value)
    elif isinstance(value, str) and NUMBER.fullmatch(value):
        result = F(value)
    else:
        raise ValueError("expected an exact nonnegative integer, Fraction or bounded numeric string")
    if result < 0:
        raise ValueError("cell ranges must be nonnegative")
    return result


def ratio(point):
    a, b, c, d = map(number, point)
    denominator = (a + b) * (a + c)
    return None if denominator == 0 else a * (a + b + c + d) / denominator


def exact_sqrt(value):
    numerator, denominator = isqrt(value.numerator), isqrt(value.denominator)
    if numerator * numerator == value.numerator and denominator * denominator == value.denominator:
        return F(numerator, denominator)
    return None


def point_witness(point):
    value = ratio(point)
    if value is None:
        raise ValueError("an undefined point cannot witness a finite coefficient")
    return {"kind": "defined_point", "cell_masses": [str(v) for v in point], "coefficient": str(value)}


def finite_upper(low, high, attained, witness, refinements=0, tolerance=F(1, 10**12)):
    if low > high:
        raise ValueError("invalid supremum enclosure")
    return {"kind": "finite", "supremum_enclosure": [str(low), str(high)],
            "attained_on_defined_domain": attained, "witness": witness,
            "enclosure_width": str(high - low), "requested_width": str(tolerance),
            "requested_width_met": high - low <= tolerance, "refinements": refinements}


def bound_ratio(box, tolerance=F(1, 10**12), max_refinements=256):
    if not isinstance(box, (list, tuple)) or len(box) != 4:
        raise ValueError("four cell ranges are required")
    ranges = []
    for bounds in box:
        if not isinstance(bounds, (list, tuple)) or len(bounds) != 2:
            raise ValueError("each cell requires lower and upper endpoints")
        low, high = map(number, bounds)
        if low > high:
            raise ValueError("lower endpoint exceeds upper endpoint")
        ranges.append((low, high))
    tolerance = number(tolerance)
    if tolerance <= 0 or type(max_refinements) is not int or not 0 <= max_refinements <= 512:
        raise ValueError("positive tolerance and 0 to 512 refinements required")
    (al, au), (bl, bu), (cl, cu), (dl, du) = ranges
    defined = au > 0 or (bu > 0 and cu > 0)
    empty = al == bl == cl == dl == 0
    undefined_positive = al == 0 and ((bl == 0 and cu + du > 0) or (cl == 0 and bu + du > 0))
    result = {"model": "nonnegative rectangular cell masses", "cell_order": list(CELL_NAMES),
              "box": [[str(lo), str(hi)] for lo, hi in ranges],
              "defined_domain_exists": defined, "empty_universe_feasible": empty,
              "undefined_positive_universe_feasible": undefined_positive,
              "infimum": None, "supremum": None}
    if not defined:
        result["state"] = "undefined_on_all_positive_universes" if undefined_positive else "empty_universe_only"
        return result
    result["state"] = "some_positive_universes_undefined" if undefined_positive else "all_positive_universes_defined"
    if au == 0:
        point = (F(0), bu, cu, dl)
        result["infimum"] = {"value": "0", "attained": True, "witness": point_witness(point)}
        result["supremum"] = finite_upper(F(0), F(0), True, point_witness(point), tolerance=tolerance)
        return result
    # b,c decrease the ratio; d increases it. The one-dimensional minimum is at an endpoint.
    candidates = [(ratio((a, bu, cu, dl)), a) for a in {al, au} if ratio((a, bu, cu, dl)) is not None]
    minimum, amin = min(candidates)
    result["infimum"] = {"value": str(minimum), "attained": True, "witness": point_witness((amin, bu, cu, dl))}
    b, c, d = bl, cl, du
    if b == c == 0:
        if al == 0 and d > 0:
            result["supremum"] = {"kind": "unbounded", "supremum_enclosure": None,
                                  "attained_on_defined_domain": False,
                                  "witness": {"kind": "diverging_sequence", "cell_masses": ["a_upper/k", "0", "0", str(d)],
                                              "a_upper": str(au), "integer_k_minimum": 1,
                                              "coefficient": "1 + (d/a_upper)*k"}}
        else:
            a = al if al > 0 else au
            value = ratio((a, b, c, d))
            result["supremum"] = finite_upper(value, value, True, point_witness((a, b, c, d)), tolerance=tolerance)
        return result
    if b == 0 or c == 0:
        if al == 0 and d > 0:
            value = 1 + d / (b + c)
            witness = {"kind": "finite_boundary_limit", "limit_cell_masses": ["0", str(b), str(c), str(d)],
                       "approach": "a=a_upper/k for positive integer k tending to infinity", "a_upper": str(au),
                       "limit_coefficient": str(value), "limit_point_is_defined": False}
            result["supremum"] = finite_upper(value, value, False, witness, tolerance=tolerance)
        else:
            a = al if al > 0 else au
            value = ratio((a, b, c, d))
            result["supremum"] = finite_upper(value, value, True, point_witness((a, b, c, d)), tolerance=tolerance)
        return result
    s, t = b + c, b * c

    def derivative_sign(a):
        return -d * a * a + 2 * t * a + t * (s + d)

    if derivative_sign(al) <= 0:
        a = al
    elif derivative_sign(au) >= 0:
        a = au
    else:
        radical = exact_sqrt(t * t + d * t * (s + d))
        if radical is not None:
            a = (t + radical) / d
        else:
            low, high = al, au
            best_a = max((al, au), key=lambda v: ratio((v, b, c, d)))
            best = ratio((best_a, b, c, d))
            steps = 0
            while True:
                upper = high * (high + s + d) / ((low + b) * (low + c))
                if upper - best <= tolerance or steps == max_refinements:
                    break
                middle = (low + high) / 2
                value = ratio((middle, b, c, d))
                if value > best:
                    best, best_a = value, middle
                sign = derivative_sign(middle)
                if sign == 0:
                    result["supremum"] = finite_upper(value, value, True, point_witness((middle, b, c, d)), steps + 1, tolerance)
                    return result
                if sign > 0:
                    low = middle
                else:
                    high = middle
                steps += 1
            witness = {"kind": "unique_stationary_root", "fixed_bcd": [str(b), str(c), str(d)],
                       "a_bracket": [str(low), str(high)],
                       "derivative_polynomial_coefficients": [str(-d), str(2 * t), str(t * (s + d))],
                       "derivative_signs": ["positive", "negative"],
                       "supremum_lower_witness": point_witness((best_a, b, c, d)),
                       "supremum_upper_rule": "high*(high+b+c+d)/((low+b)*(low+c))"}
            result["supremum"] = finite_upper(best, upper, True, witness, steps, tolerance)
            return result
    value = ratio((a, b, c, d))
    result["supremum"] = finite_upper(value, value, True, point_witness((a, b, c, d)), tolerance=tolerance)
    return result


def parse_input(raw):
    if len(raw) > 16384:
        raise ValueError("input exceeds bounded mathematical task size")

    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError("duplicate JSON property")
            out[key] = value
        return out

    def invalid_number(_):
        raise ValueError("use exact numeric strings, not floating-point JSON")

    doc = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_float=invalid_number, parse_constant=invalid_number)
    if not isinstance(doc, dict) or set(doc) != {"schema_version", "artifact_id", "box", "tolerance", "max_refinements"}:
        raise ValueError("missing or unknown input property")
    if doc["schema_version"] != "reiyah.rectangular-coincidence-input.v1":
        raise ValueError("unsupported input version")
    if not isinstance(doc["artifact_id"], str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,159}", doc["artifact_id"]):
        raise ValueError("invalid artifact identity")
    if (not isinstance(doc["box"], list) or len(doc["box"]) != 4
            or any(not isinstance(pair, list) or len(pair) != 2 or any(not isinstance(v, str) for v in pair) for pair in doc["box"])
            or not isinstance(doc["tolerance"], str)):
        raise ValueError("CLI cell endpoints and tolerance must be exact numeric strings")
    return doc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        with args.input.open("rb") as stream:
            raw = stream.read(16385)
        doc = parse_input(raw)
        result = bound_ratio(doc["box"], doc["tolerance"], doc["max_refinements"])
    except (OSError, ValueError, UnicodeError, RecursionError) as exc:
        print(json.dumps({"status": "invalid", "diagnostic": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps({"schema_version": "reiyah.rectangular-coincidence-bounds.v1", "lifecycle_status": "exploratory",
                      "input_artifact_id": doc["artifact_id"], "input_sha256": hashlib.sha256(raw).hexdigest(),
                      "analyzer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "result": result,
                      "limits": ["Bounds concern the declared rectangle, not a justified empirical reference model",
                                 "Sampling uncertainty, unknown constraints and coupled reference-error constraints are not supplied by this calculation",
                                 "Mathematical witnesses are not physical-reference or safety certificates"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
