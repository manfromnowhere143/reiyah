#!/usr/bin/env python3
"""Replay retained M4 rectangular fixtures and exact authored counterexamples.

Offline synthetic mathematics only. Historical main(), random probes and the
coupled differential solver are not executed or certified by this audit.
"""
import ast
from fractions import Fraction as F
import hashlib
import importlib.util
import json
from pathlib import Path

from rectangular_coincidence_bounds import bound_ratio, parse_input
from check_rectangular_bounds import verify_bound


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def literal_report_calls(source):
    tree = ast.parse(source)
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    literals = {}
    for node in main.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                literals[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                pass
    calls = sorted((n for n in ast.walk(main) if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Name) and n.func.id == "report"), key=lambda n: n.lineno)
    return [(ast.literal_eval(n.args[0]), literals[n.args[1].id], literals[n.args[2].id],
             next((ast.literal_eval(k.value) for k in n.keywords if k.arg == "tie_single_miss"), False),
             n.lineno) for n in calls]


def main():
    root = Path(__file__).resolve().parents[2]
    controls_path = root / "research/m4-rectangular/0.1.0/controls.json"
    controls = json.loads(controls_path.read_bytes())
    for relative, expected in controls["historical_sources"].items():
        if digest(root / relative) != expected:
            raise ValueError("historical source differs: " + relative)
    source = root / "tools/measure/m4_partial_identification.py"
    spec = importlib.util.spec_from_file_location("retained_m4", source)
    historical = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(historical)
    constants = (historical.GRID_PER_DIM, historical.RANDOM_PROBES, historical.SEED)
    reports = literal_report_calls(source.read_text())
    if len(reports) != controls["historical_replay"]["direct_report_call_count"]:
        raise ValueError("historical report coverage differs")
    rows = []
    for ordinal, (name, cells, budgets, tie, line) in enumerate(reports, 1):
        old_box = historical.budget_box(cells, budgets)
        box = [[F(str(v)) for v in pair] for pair in old_box]
        result = bound_ratio(box)
        checked = verify_bound(result)
        lo, hi, flag, points = historical.optimise(old_box, tie_single_miss=tie)
        upper = result["supremum"]
        extrema_respect_tie = None
        if tie:
            witnesses = [result["infimum"]["witness"], upper["witness"]]
            extrema_respect_tie = all(w["kind"] == "defined_point" and
                F(w["cell_masses"][1]) - box[1][0] == F(w["cell_masses"][2]) - box[2][0]
                for w in witnesses)
            if not extrema_respect_tie:
                raise ValueError("rectangle extrema do not establish bounds on the historical tied subset")
        comparison = "undefined_misclassified_as_unbounded" if flag and upper["kind"] == "finite" else "finite_extrema_agree_with_float_rounding"
        if not flag:
            exact_low = F(result["infimum"]["value"])
            if upper["kind"] != "finite":
                raise ValueError("additional historical classification discrepancy requires review")
            left, right = map(F, upper["supremum_enclosure"])
            if not (abs(lo - float(exact_low)) <= 1e-12 and float(left) - 1e-12 <= hi <= float(right) + 1e-12):
                raise ValueError("additional historical numeric discrepancy requires review")
        rows.append({"case_id": f"historical-{ordinal:02d}", "name": name, "source_line": line,
                     "literal_cells": list(cells), "literal_budgets": budgets,
                     "historical_tie_single_miss": tie, "rectangle_extrema_respect_historical_tie": extrema_respect_tie,
                     "historical": {"grid_infimum": lo, "grid_supremum": hi, "unbounded_flag": flag,
                                    "extremum_points": points},
                     "corrected": result, "algebra_check": checked, "comparison": comparison})
    authored = []
    for case in controls["authored_cases"]:
        raw = (json.dumps(case["input"], sort_keys=True, separators=(",", ":")) + "\n").encode()
        doc = parse_input(raw)
        result = bound_ratio(doc["box"], doc["tolerance"], doc["max_refinements"])
        expected = case["expected"]
        upper = result["supremum"]
        if (None if upper is None else upper["kind"]) != expected["supremum_kind"]:
            raise ValueError("authored supremum classification differs")
        if (None if result["infimum"] is None else result["infimum"]["value"]) != expected["infimum"]:
            raise ValueError("authored infimum differs")
        if expected["exact_supremum"] is not None and upper["supremum_enclosure"] != [expected["exact_supremum"]] * 2:
            raise ValueError("authored exact supremum differs")
        row = {"input": doc, "canonical_input_sha256": hashlib.sha256(raw).hexdigest(),
               "result": result, "algebra_check": verify_bound(result)}
        if doc["artifact_id"] in ("reiyah.m4-control.off-grid-maximum.0.1.0", "reiyah.m4-control.finite-undefined-limit.0.1.0"):
            lo, hi, flag, points = historical.optimise([[float(v) for v in pair] for pair in doc["box"]])
            row["historical"] = {"grid_infimum": lo, "grid_supremum": hi, "unbounded_flag": flag,
                                 "extremum_points": points}
        authored.append(row)
    if constants != (historical.GRID_PER_DIM, historical.RANDOM_PROBES, historical.SEED):
        raise ValueError("historical globals changed")
    sources = ["tools/measure/audit_m4_bounds.py", "tools/measure/rectangular_coincidence_bounds.py",
               "tools/measure/check_rectangular_bounds.py", "tools/measure/m4_partial_identification.py",
               "research/m4-rectangular/0.1.0/controls.json", "evidence/measurement/m4_partial_identification.txt"]
    print(json.dumps({"artifact_id": "reiyah.m4-rectangular-audit.0.1.0", "version": "0.1.0",
                      "lifecycle_status": "exploratory", "sources": {p: digest(root / p) for p in sources},
                      "historical_globals_unchanged": True,
                      "historical_constants": {"grid_per_dimension": constants[0], "random_probes_not_replayed": constants[1], "seed": constants[2]},
                      "historical_report_calls": rows, "authored_controls": authored,
                      "limits": ["All direct rectangular report calls in retained main were exercised; the full historical experiment was not replayed",
                                 "Historical differential constraints and reference-error process validity are outside this audit",
                                 "Independent algorithmic check, written in the same session; no independent human mathematical review",
                                 "Synthetic exact mathematics; no changed camera-lidar measurements, empirical identification or safety claim"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
