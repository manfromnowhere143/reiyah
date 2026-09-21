"""Frozen authored baseline audit. No empirical model execution or new estimator."""

import argparse
import ast
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time
from types import SimpleNamespace

from reference import variance_by_enumeration

CASES = {
    "theorem2_k4": [[0, 0, 0, 1], [0, 0, 1, 1]],
    "k2_contrast": [[0, 1], [1, 0]],
    "k3_binary": [[0, 0, 1], [0, 1, 1]],
    "k4_equal_spread": [[0, 0, 0, 1], [1, 0, 0, 0]],
    "all_equal": [[0, 0, 0, 0], [1, 1, 1, 1]],
}
QUERY_SHA = "530a21147c4a6ff79d7a51e1f54049f42eafa99e4434e4ad6c1c88d1cdc0a360"


def coefficients(losses):
    absolute, squared = [], []
    for row in losses:
        differences = [
            Fraction(row[i]) - Fraction(row[j])
            for i in range(len(row))
            for j in range(i + 1, len(row))
        ]
        absolute.append(sum(abs(value) for value in differences))
        squared.append(sum(value * value for value in differences))
    return absolute, squared


def normalized(weights):
    total = sum(weights)
    return (
        [value / total for value in weights]
        if total
        else [Fraction(1, len(weights))] * len(weights)
    )


def closed_variance(losses, q):
    _, squared = coefficients(losses)
    k = len(losses[0])
    centered = sum(
        sum(Fraction(row[i]) - Fraction(row[j]) for row in losses) ** 2
        for i in range(k)
        for j in range(i + 1, k)
    )
    return (
        sum(value / probability for value, probability in zip(squared, q)) - centered
    ) / len(losses) ** 2


def classical_optimum(weights):
    with localcontext() as context:
        context.prec = 60
        roots = [
            (Decimal(value.numerator) / Decimal(value.denominator)).sqrt()
            for value in weights
        ]
        total = sum(roots)
        return (
            [str(value / total) for value in roots]
            if total
            else [str(Decimal(1) / len(weights))] * len(weights)
        )


def source_mechanism(source, losses):
    # Explicit mechanism reproduction only: no import or execution of Numba/JIT.
    import numpy as np

    body = source.read_bytes()
    if hashlib.sha256(body).hexdigest() != QUERY_SHA:
        raise ValueError("query_source_identity")
    tree = ast.parse(body)
    names = ("q_by_loss_diff_sub", "q_by_loss_diff")
    functions = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in names
    ]
    if tuple(node.name for node in functions) != names:
        raise ValueError("query_function_selection")
    for node in functions:
        node.decorator_list = []
    selected = ast.Module(body=functions, type_ignores=[])
    ast.fix_missing_locations(selected)
    namespace = {"np": np, "numba": SimpleNamespace(prange=range)}
    exec(compile(selected, str(source), "exec"), namespace)
    # N x K authored zero-one losses; make K x N x 2 possible-label losses.
    rows = np.array(losses, dtype=float)
    possible = np.stack([rows.T, 1 - rows.T], axis=2)
    oracle = np.zeros((len(losses), 2))
    oracle[:, 0] = 1
    published = {}
    absolute, _ = coefficients(losses)
    for eps in (Fraction(0), Fraction(1, 100)):
        if not sum(absolute) and not eps:
            published["eps_0"] = {
                "status": "not_executed_undefined_normalization",
                "reason": "all acquisition weights zero",
            }
            continue
        actual = namespace["q_by_loss_diff"](
            possible, oracle, list(range(len(losses))), eps=float(eps)
        )
        expected = normalized([value + eps for value in absolute])
        if not np.allclose(
            actual, [float(value) for value in expected], rtol=1e-14, atol=0
        ):
            raise ValueError("source_query_discrepancy")
        published["eps_" + str(eps)] = {
            "status": "matched",
            "q_float": actual.tolist(),
            "q_rational_reference": list(map(str, expected)),
            "actual_native_numba_execution": False,
        }
    return {
        "source_sha256": QUERY_SHA,
        "selected_function_names": names,
        "transformed_ast_sha256": hashlib.sha256(
            ast.dump(selected, include_attributes=False).encode()
        ).hexdigest(),
        "adaptation": "Remove JIT decorators; supply NumPy and serial numba.prange=range; original selected function bodies unchanged.",
        "surrogate": "point mass at authored known label; oracle mechanism control",
        "queries": published,
    }


def run(root):
    started = time.perf_counter()
    source = root / "private/sources/hara-code-src--query.py"
    results = []
    for name, losses in CASES.items():
        absolute, squared = coefficients(losses)
        distributions = {
            "published_oracle_l1": normalized(absolute),
            "rational_challenger": [Fraction(7, 15), Fraction(8, 15)],
            "uniform": [Fraction(1, 2), Fraction(1, 2)],
            "published_default_eps_rational": normalized(
                [value + Fraction(1, 100) for value in absolute]
            ),
        }
        records = []
        for method, q in distributions.items():
            value = closed_variance(losses, q)
            checked, pairs = variance_by_enumeration(losses, q)
            if value != checked:
                raise ValueError("objective_reference_disagreement")
            records.append(
                {
                    "method": method,
                    "q": list(map(str, q)),
                    "sum_pair_variances": str(value),
                    "reference_pairs": pairs,
                }
            )
        results.append(
            {
                "case": name,
                "authored_loss_rows": losses,
                "absolute_pair_sums": list(map(str, absolute)),
                "squared_pair_sums": list(map(str, squared)),
                "classical_optimum_q_decimal": classical_optimum(squared),
                "distributions": records,
                "source_mechanism": source_mechanism(source, losses),
            }
        )
    main = results[0]
    values = {
        row["method"]: Fraction(row["sum_pair_variances"])
        for row in main["distributions"]
    }
    return {
        "document_id": "reiyah.comparison-design.audit",
        "version": "0.1.0",
        "status": "exploratory_authored_mathematical_audit",
        "hypothesis": "published general-K oracle rule minimizes sum of pairwise conditional variances",
        "verdict": "contradicted_by_feasible_distribution"
        if values["rational_challenger"] < values["published_oracle_l1"]
        else "counterexample_not_established",
        "exact_improvement": str(
            values["published_oracle_l1"] - values["rational_challenger"]
        ),
        "cases": results,
        "numba_available": False,
        "native_numba_executed": False,
        "empirical_model_selection_runs": 0,
        "reiyah_comparative_advantage": "not_established",
        "workflow_seconds": time.perf_counter() - started,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("owner", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = run(args.owner)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "status",
                    "verdict",
                    "exact_improvement",
                    "workflow_seconds",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
