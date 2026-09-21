"""Check actual audit records, semantic controls and mutations."""

import argparse
from copy import deepcopy
from fractions import Fraction
from decimal import Decimal, localcontext
import json
from pathlib import Path

from reference import variance_by_enumeration


def check(record):
    expected_cases = {
        "theorem2_k4": [[0, 0, 0, 1], [0, 0, 1, 1]],
        "k2_contrast": [[0, 1], [1, 0]],
        "k3_binary": [[0, 0, 1], [0, 1, 1]],
        "k4_equal_spread": [[0, 0, 0, 1], [1, 0, 0, 0]],
        "all_equal": [[0, 0, 0, 0], [1, 1, 1, 1]],
    }
    if [row["case"] for row in record["cases"]] != list(expected_cases):
        raise ValueError("case_cohort")
    if (
        record["empirical_model_selection_runs"] != 0
        or record["native_numba_executed"]
        or record["reiyah_comparative_advantage"] != "not_established"
    ):
        raise ValueError("claim_scope")
    checked = 0
    for case in record["cases"]:
        if case["authored_loss_rows"] != expected_cases[case["case"]]:
            raise ValueError("input_identity")
        rows = case["authored_loss_rows"]
        for item in case["distributions"]:
            value, pairs = variance_by_enumeration(rows, item["q"])
            if (
                item["sum_pair_variances"] != str(value)
                or item["reference_pairs"] != pairs
            ):
                raise ValueError("variance")
            checked += 1
        by_name = {item["method"]: item for item in case["distributions"]}
        if (
            set(by_name)
            != {
                "published_oracle_l1",
                "rational_challenger",
                "uniform",
                "published_default_eps_rational",
            }
            or len(case["distributions"]) != 4
        ):
            raise ValueError("distribution_cohort")
        pair_abs = []
        pair_sq = []
        for row in rows:
            ds = [
                Fraction(left) - Fraction(right)
                for i, left in enumerate(row)
                for right in row[i + 1 :]
            ]
            pair_abs.append(sum(map(abs, ds)))
            pair_sq.append(sum(value * value for value in ds))
        if case["absolute_pair_sums"] != list(map(str, pair_abs)) or case[
            "squared_pair_sums"
        ] != list(map(str, pair_sq)):
            raise ValueError("coefficients")
        for name, addition in (
            ("published_oracle_l1", 0),
            ("published_default_eps_rational", Fraction(1, 100)),
        ):
            ws = [value + addition for value in pair_abs]
            total = sum(ws)
            expected = (
                [value / total for value in ws]
                if total
                else [Fraction(1, len(rows))] * len(rows)
            )
            if by_name[name]["q"] != list(map(str, expected)):
                raise ValueError("query")
        if by_name["rational_challenger"]["q"] != ["7/15", "8/15"] or by_name[
            "uniform"
        ]["q"] != ["1/2", "1/2"]:
            raise ValueError("query")
        with localcontext() as context:
            context.prec = 65
            approx = [Decimal(x) for x in case["classical_optimum_q_decimal"]]
            if any(x <= 0 for x in approx) or abs(sum(approx) - 1) > Decimal("1e-55"):
                raise ValueError("classical_query")
            if any(pair_sq):
                derivatives = [
                    Decimal(v.numerator) / Decimal(v.denominator) / (q * q)
                    for v, q in zip(pair_sq, approx)
                ]
                if abs(derivatives[0] - derivatives[1]) > Decimal("1e-50"):
                    raise ValueError("classical_stationarity")
        mechanism = case["source_mechanism"]
        if (
            mechanism["source_sha256"]
            != "530a21147c4a6ff79d7a51e1f54049f42eafa99e4434e4ad6c1c88d1cdc0a360"
            or mechanism["selected_function_names"]
            != ["q_by_loss_diff_sub", "q_by_loss_diff"]
        ):
            raise ValueError("source_mechanism_identity")
        for eps_key, method in (
            ("eps_0", "published_oracle_l1"),
            ("eps_1/100", "published_default_eps_rational"),
        ):
            query = mechanism["queries"][eps_key]
            if not any(pair_abs) and eps_key == "eps_0":
                if query["status"] != "not_executed_undefined_normalization":
                    raise ValueError("undefined_query_scope")
                continue
            if (
                query["status"] != "matched"
                or query["actual_native_numba_execution"]
                or query["q_rational_reference"] != by_name[method]["q"]
            ):
                raise ValueError("source_query_scope")
            if any(
                abs(float(x) - y) > 1e-14
                for x, y in zip(
                    map(Fraction, query["q_rational_reference"]), query["q_float"]
                )
            ):
                raise ValueError("source_query_numeric")
    main = {
        item["method"]: Fraction(item["sum_pair_variances"])
        for item in record["cases"][0]["distributions"]
    }
    difference = main["published_oracle_l1"] - main["rational_challenger"]
    verdict = (
        "contradicted_by_feasible_distribution"
        if difference > 0
        else "counterexample_not_established"
    )
    if record["verdict"] != verdict or record["exact_improvement"] != str(difference):
        raise ValueError("decision")
    return checked


def controls(record):
    count = check(record)
    results = []
    rows = record["cases"][0]["authored_loss_rows"]
    q = [Fraction(3, 7), Fraction(4, 7)]
    original, _ = variance_by_enumeration(rows, q)
    for name, changed, probs in (
        ("model_permutation", [row[::-1] for row in rows], q),
        ("point_permutation", rows[::-1], q[::-1]),
    ):
        value, _ = variance_by_enumeration(changed, probs)
        if value != original:
            raise ValueError(name)
        results.append({"id": name, "passed": True})
    for probs in (["0", "1"], ["-1", "2"], ["1/3", "1/3"]):
        try:
            variance_by_enumeration(rows, probs)
        except ValueError as exc:
            if str(exc) != "probability":
                raise
            results.append(
                {"id": "invalid_probability_" + "_".join(probs), "passed": True}
            )
        else:
            raise ValueError("invalid_probability_accepted")
    for case in record["cases"][1:]:
        ds = {
            item["method"]: Fraction(item["sum_pair_variances"])
            for item in case["distributions"]
        }
        if (
            ds["published_oracle_l1"] != ds["uniform"]
            or ds["published_oracle_l1"] > ds["rational_challenger"]
        ):
            raise ValueError("positive_control")
        results.append({"id": "preserve_" + case["case"], "passed": True})
    mutations = [
        ("missing_case", "case_cohort", lambda r: r["cases"].pop()),
        (
            "loss_change",
            "input_identity",
            lambda r: r["cases"][0]["authored_loss_rows"][0].__setitem__(0, 1),
        ),
        (
            "variance_change",
            "variance",
            lambda r: r["cases"][0]["distributions"][0].update(sum_pair_variances="0"),
        ),
        ("false_decision", "decision", lambda r: r.update(verdict="supported")),
        (
            "claim_empirical",
            "claim_scope",
            lambda r: r.update(empirical_model_selection_runs=1),
        ),
        ("claim_jit", "claim_scope", lambda r: r.update(native_numba_executed=True)),
        (
            "claim_advantage",
            "claim_scope",
            lambda r: r.update(reiyah_comparative_advantage="established"),
        ),
    ]
    for name, reason, mutate in mutations:
        changed = deepcopy(record)
        mutate(changed)
        try:
            check(changed)
        except ValueError as exc:
            if str(exc) != reason:
                raise
            results.append({"id": name, "expected": reason, "passed": True})
        else:
            raise ValueError("mutation_accepted:" + name)
    return {
        "document_id": "reiyah.comparison-design.check",
        "version": "0.1.0",
        "status": "passed",
        "distributions_checked": count,
        "controls": results,
        "independent_authorship": False,
        "scope": "authored finite probability and explicit software-mechanism check; no empirical model selection",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = controls(json.loads(args.result.read_text()))
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
