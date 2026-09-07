#!/usr/bin/env python3
"""Separate arithmetic check for the fixed synthetic report, not a safety validator.

Uses Decimal logarithms rather than the producer's rational series. This numerical
comparison does not independently prove the log enclosure or the TV theorem.
"""

from decimal import Decimal as D, ROUND_CEILING, localcontext
from fractions import Fraction as F
import json
from pathlib import Path
import sys


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_report(r):
    require(r["artifact_id"] == "reiyah.rare-event-dependence-limits.2026-09-07", "wrong artifact")
    require(r["version"] == "0.1.0", "wrong version")
    require(r["observed_physical_performance"] is None and r["safety_validation_budget"] is None,
            "synthetic arithmetic cannot supply a physical result")
    q = r["rare_pair"]
    require(F(q["marginal_a"]) == F(1, 100000) == F(q["marginal_b"]), "wrong fixed marginals")
    rows = [tuple(map(F, q[key])) for key in ("null_law", "alternative_law")]
    for row, c in zip(rows, (1, 2)):
        require(len(row) == 4 and sum(row) == 1 and min(row) >= 0, "invalid full law")
        a, b, c_only, _ = row
        require(a + b == F(1, 100000) == a + c_only, "changed marginal")
        require(a / ((a + b) * (a + c_only)) == c, "wrong joint coefficient")
    require(F(q["null_c"]) == 1 and F(q["alternative_c"]) == 2, "wrong coefficient label")
    distance = sum(abs(x - y) for x, y in zip(*rows)) / 2
    require(distance == F(q["single_observation_tv"]), "wrong total variation")
    require(q["n"] == 100000 and F(q["alpha"]) == F(1, 20), "wrong fixed design")
    require(F(q["any_test_power_upper_bound"]) == F(q["alpha"]) + q["n"] * distance,
            "wrong power bound")
    gap = (F(q["desired_power"]) - F(q["alpha"])) / distance
    require(F(q["desired_power"]) == F(19, 20), "wrong desired power")
    require(q["necessary_n_from_tv_union_bound"] == -(-gap.numerator // gap.denominator),
            "wrong necessary sample size")
    require(q["necessary_n_is_sufficient"] is False, "necessary is not sufficient")
    checks = []
    require(len(r["zero_event_rules"]) == 3, "three declared rules required")
    expected_rules = [("single_channel_failure", F(1, 100000)),
                      ("joint_failure_at_c_1", F(1, 10000000000)),
                      ("joint_failure_at_c_2", F(1, 5000000000))]
    for row, (event, threshold) in zip(r["zero_event_rules"], expected_rules):
        require(row["event"] == event and F(row["probability_threshold"]) == threshold
                and F(row["alpha"]) == F(1, 20), "changed event, threshold or confidence")
    for precision in (80, 120):
        with localcontext() as ctx:
            ctx.prec = precision
            def dec(x):
                x = F(x)
                return D(x.numerator) / D(x.denominator)
            for row in r["zero_event_rules"]:
                ratio = dec(row["alpha"]).ln() / (1 - dec(row["probability_threshold"])).ln()
                require(int(ratio.to_integral_value(rounding=ROUND_CEILING)) == row["n"],
                        "separate logarithm calculation disagrees")
                require(dec(row["ratio_lower"]) <= ratio <= dec(row["ratio_upper"]),
                        "separate numerical value outside claimed enclosure")
                checks.append({"event": row["event"], "decimal_precision": precision, "n": row["n"]})
    for row in r["mixture_controls"].values():
        weights = list(map(F, row["weights"]))
        cells = [tuple(map(F, x)) for x in row["stratum_laws"]]
        require(len(weights) == len(cells) == len(row["stratum_c"]), "stratum count mismatch")
        require(sum(weights) == 1 and min(weights) >= 0, "invalid weights")
        for cell, coefficient in zip(cells, row["stratum_c"]):
            require(len(cell) == 4 and sum(cell) == 1 and min(cell) >= 0, "invalid stratum law")
            a, b, c, _ = cell
            require(F(coefficient) == a / ((a + b) * (a + c)), "wrong stratum coefficient")
        mixed = tuple(sum(w * x[k] for w, x in zip(weights, cells)) for k in range(4))
        require(tuple(map(F, row["mixture_law"])) == mixed, "wrong mixture law")
        a, b, c, _ = mixed
        require(F(row["mixture_c"]) == a / ((a + b) * (a + c)), "wrong mixture coefficient")
        expected = sum(w * (x[0] + x[1]) * (x[0] + x[2]) for w, x in zip(weights, cells))
        require(F(row["conditional_aggregate_c"]) == a / expected, "wrong aggregate coefficient")
    return {"status": "pass", "scope": "fixed-report arithmetic cross-check; no producer import",
            "numeric_checks": checks, "physical_performance": None}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: check_rare_event_limits.py limits.json")
    payload = Path(sys.argv[1]).read_bytes()
    require(len(payload) <= 1048576, "report exceeds fixed check size limit")
    print(json.dumps(check_report(json.loads(payload)), indent=2, sort_keys=True))
