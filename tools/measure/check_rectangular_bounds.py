#!/usr/bin/env python3
"""Independent rational-algebra check of rectangular coincidence bound reports.

This module imports neither the solver nor its helpers. The mathematical
reduction assumes exactly the nonnegative rectangular domain in the report.
It is not a proof-assistant kernel or an empirical safety/reference validator.
"""
from fractions import Fraction as F
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def keys(value, expected, context):
    require(isinstance(value, dict) and set(value) == set(expected), "missing or unknown property in " + context)


def rational(value):
    require(isinstance(value, str) and re.fullmatch(
        r"(?:0|[1-9][0-9]{0,2047})(?:/[1-9][0-9]{0,2047}|\.[0-9]{1,32})?", value) is not None,
        "expected a bounded exact rational string")
    try:
        answer = F(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError("invalid rational value") from exc
    require(answer >= 0, "negative probability mass or coefficient")
    return answer


def quadratic_minimum(A, B, C, low, high):
    candidates = [(A * x * x + B * x + C, x) for x in (low, high)]
    if A > 0:
        vertex = -B / (2 * A)
        if low < vertex < high:
            candidates.append((A * vertex * vertex + B * vertex + C, vertex))
    return min(candidates)


def point_value(witness, box):
    keys(witness, ("kind", "cell_masses", "coefficient"), "point witness")
    require(witness["kind"] == "defined_point", "expected a defined-point witness")
    point = list(map(rational, witness["cell_masses"]))
    require(len(point) == 4 and all(lo <= x <= hi for x, (lo, hi) in zip(point, box)), "witness outside supplied rectangle")
    a, b, c, d = point
    require(a + b > 0 and a + c > 0, "undefined point offered as a coefficient witness")
    value = a * sum(point) / ((a + b) * (a + c))
    require(value == rational(witness["coefficient"]), "incorrect point coefficient")
    return value


def verify_bound(result):
    keys(result, ("model", "cell_order", "box", "defined_domain_exists", "empty_universe_feasible",
                  "undefined_positive_universe_feasible", "infimum", "supremum", "state"), "bound result")
    require(result["model"] == "nonnegative rectangular cell masses", "unsupported mathematical model")
    require(result["cell_order"] == ["both", "a_only", "b_only", "neither"], "different contingency convention")
    require(isinstance(result["box"], list) and len(result["box"]) == 4, "invalid rectangle")
    box = [tuple(map(rational, pair)) for pair in result["box"]]
    require(all(len(pair) == 2 and pair[0] <= pair[1] for pair in box), "invalid range")
    (al, au), (bl, bu), (cl, cu), (dl, du) = box
    defined = au > 0 or (bu > 0 and cu > 0)
    empty = all(lo == 0 for lo, _ in box)
    undefined = al == 0 and ((bl == 0 and cu + du > 0) or (cl == 0 and bu + du > 0))
    for key, expected in (("defined_domain_exists", defined), ("empty_universe_feasible", empty),
                          ("undefined_positive_universe_feasible", undefined)):
        require(type(result[key]) is bool and result[key] == expected, "incorrect domain feasibility: " + key)
    if not defined:
        require(result["state"] == ("undefined_on_all_positive_universes" if undefined else "empty_universe_only"), "incorrect undefined-domain state")
        require(result["infimum"] is None and result["supremum"] is None, "numerical coefficient on an entirely undefined domain")
        return {"status": "verified", "domain": result["state"], "global_inequalities": "no defined coefficient exists"}
    require(result["state"] == ("some_positive_universes_undefined" if undefined else "all_positive_universes_defined"), "incorrect defined-domain state")
    lower = result["infimum"]
    keys(lower, ("value", "attained", "witness"), "infimum")
    L = rational(lower["value"])
    require(lower["attained"] is True and point_value(lower["witness"], box) == L, "infimum is not witnessed")
    # On the minimizing face b=bu,c=cu,d=dl, numerator - L*denominator is a quadratic.
    low_poly = (1 - L, (bu + cu) * (1 - L) + dl, -L * bu * cu)
    low_min, low_at = quadratic_minimum(*low_poly, al, au)
    require(low_min >= 0, "claimed lower bound exceeds a feasible coefficient")
    upper = result["supremum"]
    unbounded = al == bl == cl == 0 and au > 0 and du > 0
    if upper["kind"] == "unbounded":
        keys(upper, ("kind", "supremum_enclosure", "attained_on_defined_domain", "witness"), "unbounded supremum")
        require(unbounded, "undefined does not imply an unbounded supremum")
        require(upper["supremum_enclosure"] is None and upper["attained_on_defined_domain"] is False, "invalid infinity representation")
        witness = upper["witness"]
        keys(witness, ("kind", "a_upper", "cell_masses", "integer_k_minimum", "coefficient"), "divergent witness")
        require(witness["kind"] == "diverging_sequence" and rational(witness["a_upper"]) == au, "invalid divergent sequence")
        require(witness["cell_masses"] == ["a_upper/k", "0", "0", str(du)], "wrong divergent sequence masses")
        require(type(witness["integer_k_minimum"]) is int and witness["integer_k_minimum"] == 1, "invalid sequence index")
        require(witness["coefficient"] == "1 + (d/a_upper)*k", "wrong sequence coefficient")
        return {"status": "verified", "domain": result["state"], "lower_polynomial_minimum": str(low_min),
                "upper": "unbounded by an explicit positive-domain sequence"}
    require(upper["kind"] == "finite", "unsupported supremum kind")
    keys(upper, ("kind", "supremum_enclosure", "attained_on_defined_domain", "witness", "enclosure_width",
                 "requested_width", "requested_width_met", "refinements"), "finite supremum")
    require(not unbounded, "finite bound on an unbounded domain")
    enclosure = list(map(rational, upper["supremum_enclosure"]))
    require(len(enclosure) == 2 and enclosure[0] <= enclosure[1], "invalid supremum enclosure")
    S, U = enclosure
    require(L <= S, "infimum exceeds supremum enclosure")
    # On the maximizing face b=bl,c=cl,d=du, U*denominator - numerator is a quadratic.
    up_poly = (U - 1, (bl + cl) * (U - 1) - du, U * bl * cl)
    up_min, up_at = quadratic_minimum(*up_poly, al, au)
    require(up_min >= 0, "claimed upper bound excludes a feasible coefficient")
    width = U - S
    require(rational(upper["enclosure_width"]) == width, "incorrect reported enclosure width")
    requested = rational(upper["requested_width"])
    require(requested > 0 and type(upper["requested_width_met"]) is bool
            and upper["requested_width_met"] == (width <= requested), "incorrect precision status")
    require(type(upper["refinements"]) is int and 0 <= upper["refinements"] <= 512, "invalid refinement count")
    witness = upper["witness"]
    if witness["kind"] == "defined_point":
        require(upper["attained_on_defined_domain"] is True and S == U == point_value(witness, box), "point does not attain the claimed supremum")
    elif witness["kind"] == "finite_boundary_limit":
        keys(witness, ("kind", "limit_cell_masses", "approach", "a_upper", "limit_coefficient", "limit_point_is_defined"), "limit witness")
        require(al == 0 and au > 0 and du > 0 and ((bl == 0 and cl > 0) or (cl == 0 and bl > 0)), "unsupported finite-limit face")
        limit = 1 + du / (bl + cl)
        require(S == U == limit and rational(witness["limit_coefficient"]) == limit, "incorrect finite limit")
        require(witness["limit_cell_masses"] == ["0", str(bl), str(cl), str(du)], "incorrect limit point")
        require(upper["attained_on_defined_domain"] is False and witness["limit_point_is_defined"] is False, "unattained limit misrepresented as defined")
        require(rational(witness["a_upper"]) == au, "invalid finite-limit sequence")
        require(witness["approach"] == "a=a_upper/k for positive integer k tending to infinity", "unsupported finite-limit approach")
    elif witness["kind"] == "unique_stationary_root":
        keys(witness, ("kind", "fixed_bcd", "a_bracket", "derivative_polynomial_coefficients", "derivative_signs",
                       "supremum_lower_witness", "supremum_upper_rule"), "stationary witness")
        require(upper["attained_on_defined_domain"] is True and bl > 0 and cl > 0 and du > 0, "unsupported stationary-root face")
        require(list(map(rational, witness["fixed_bcd"])) == [bl, cl, du], "stationary root on the wrong face")
        left, right = map(rational, witness["a_bracket"])
        require(al <= left < right <= au, "invalid stationary-root bracket")
        t, s = bl * cl, bl + cl
        coeff = [-du, 2 * t, t * (s + du)]
        require(witness["derivative_polynomial_coefficients"] == [str(x) for x in coeff], "wrong stationary polynomial")
        evaluate = lambda x: coeff[0] * x * x + coeff[1] * x + coeff[2]
        require(evaluate(left) > 0 and evaluate(right) < 0 and witness["derivative_signs"] == ["positive", "negative"], "stationary root is not isolated")
        require(point_value(witness["supremum_lower_witness"], box) == S, "supremum lower endpoint has no feasible witness")
        require(witness["supremum_upper_rule"] == "high*(high+b+c+d)/((low+b)*(low+c))", "unsupported enclosure rule")
        require(U == right * (right + s + du) / ((left + bl) * (left + cl)), "enclosure does not follow its stated rational rule")
    else:
        raise ValueError("unsupported supremum witness")
    return {"status": "verified", "domain": result["state"], "lower_polynomial_minimum": str(low_min),
            "lower_polynomial_minimum_at": str(low_at), "upper_polynomial_minimum": str(up_min),
            "upper_polynomial_minimum_at": str(up_at), "upper": "finite rational enclosure verified"}


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON property")
            result[key] = value
        return result
    def invalid(_):
        raise ValueError("floating-point and nonfinite JSON numbers are unsupported")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid, parse_float=invalid)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        with args.input.open("rb") as stream:
            raw_input = stream.read(16385)
        with args.report.open("rb") as stream:
            raw_report = stream.read(1048577)
        require(len(raw_input) <= 16384 and len(raw_report) <= 1048576, "bounded verification input exceeded")
        original, report = strict_json(raw_input), strict_json(raw_report)
        keys(original, ("schema_version", "artifact_id", "box", "tolerance", "max_refinements"), "input")
        keys(report, ("schema_version", "lifecycle_status", "input_artifact_id", "input_sha256", "analyzer_sha256", "result", "limits"), "report")
        require(original["schema_version"] == "reiyah.rectangular-coincidence-input.v1", "unsupported input version")
        require(report["schema_version"] == "reiyah.rectangular-coincidence-bounds.v1", "unsupported report version")
        require(report["lifecycle_status"] == "exploratory", "unsupported report lifecycle")
        require(type(original["max_refinements"]) is int and 0 <= original["max_refinements"] <= 512, "invalid input refinement budget")
        require(isinstance(original["box"], list) and len(original["box"]) == 4
                and all(isinstance(pair, list) and len(pair) == 2 for pair in original["box"]), "invalid input rectangle")
        literals = [v for pair in original["box"] for v in pair] + [original["tolerance"]]
        require(all(isinstance(v, str) and re.fullmatch(r"(?:0|[1-9][0-9]{0,31})(?:\.[0-9]{1,32}|/[1-9][0-9]{0,31})?", v) is not None
                    for v in literals), "unsupported exact input literal")
        require(rational(original["tolerance"]) > 0, "nonpositive tolerance")
        require(isinstance(original["artifact_id"], str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,159}", original["artifact_id"]) is not None, "invalid input identity")
        require(isinstance(report["analyzer_sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", report["analyzer_sha256"]) is not None, "invalid producer digest syntax")
        require(isinstance(report["limits"], list) and all(isinstance(v, str) for v in report["limits"]), "invalid report limits")
        require(report["input_sha256"] == hashlib.sha256(raw_input).hexdigest(), "input digest mismatch")
        require(report["input_artifact_id"] == original["artifact_id"], "input identity mismatch")
        result = report["result"]
        require([[rational(v) for v in pair] for pair in result["box"]] == [[rational(v) for v in pair] for pair in original["box"]], "report addresses a different rectangle")
        if result["supremum"] is not None and result["supremum"]["kind"] == "finite":
            require(rational(result["supremum"]["requested_width"]) == rational(original["tolerance"]), "precision request differs")
            require(result["supremum"]["refinements"] <= original["max_refinements"], "refinement budget exceeded")
        checked = verify_bound(result)
    except (OSError, KeyError, TypeError, ValueError, ZeroDivisionError, RecursionError) as exc:
        print(json.dumps({"status": "invalid", "diagnostic": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps({"schema_version": "reiyah.rectangular-bound-verification.v1", "status": "verified",
                      "input_sha256": hashlib.sha256(raw_input).hexdigest(), "report_sha256": hashlib.sha256(raw_report).hexdigest(),
                      "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "checks": checked,
                      "producer_source_integrity": "not_checked_by_this_algebra_verifier",
                      "scope": "Rational inequalities and extrema witnesses on the supplied rectangle; no empirical or safety acceptance"}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
