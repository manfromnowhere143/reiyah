#!/usr/bin/env python3
"""Check retained M4 audit closure and mathematical witnesses; development only."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import re
import sys

from check_rectangular_bounds import verify_bound


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def historical_table(audit):
    names = ["F-01 zero budgets", "F-01 L1 rectangle", "F-01 L2 tied subset", "F-01 L3 tied subset",
             "F-01b L1 asymmetric", "F-01b L2 tied subset", "F-03 thin stratum"]
    rows = ["| Retained fixture | Old displayed classification | Corrected infimum | Corrected supremum |",
            "| --- | --- | ---: | ---: |"]
    for name, row in zip(names, audit["historical_report_calls"]):
        old, new = row["historical"], row["corrected"]
        old_text = "UNBOUNDED" if old["unbounded_flag"] else f"[{old['grid_infimum']:.4f}, {old['grid_supremum']:.4f}]"
        low = float(F(new["infimum"]["value"]))
        high = float(F(new["supremum"]["supremum_enclosure"][1]))
        tail = " (unattained)" if not new["supremum"]["attained_on_defined_domain"] else ""
        rows.append(f"| {name} | {old_text} | {low:.6f} | {high:.6f}{tail} |")
    return "\n".join(rows)


def check_table(text, audit):
    if text.count(historical_table(audit)) != 1:
        raise ValueError("historical comparison table differs from retained audit")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checks-root", type=Path, required=True)
    parser.add_argument("--baseline-root", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    evidence = root / "evidence/m4-bounds"
    audit = json.loads((evidence / "audit-0.1.0.json").read_bytes())
    for path, expected in audit["sources"].items():
        if digest(root / path) != expected:
            raise ValueError("audit source mismatch: " + path)
    if len(audit["historical_report_calls"]) != 7 or len(audit["authored_controls"]) != 9:
        raise ValueError("declared audit case coverage differs")
    for row in audit["historical_report_calls"]:
        if verify_bound(row["corrected"]) != row["algebra_check"]:
            raise ValueError("historical bound witness verification differs")
    for row in audit["authored_controls"]:
        if verify_bound(row["result"]) != row["algebra_check"]:
            raise ValueError("authored bound witness verification differs")
    if sum(r["comparison"] == "undefined_misclassified_as_unbounded" for r in audit["historical_report_calls"]) != 1:
        raise ValueError("historical correction count differs")
    public_stdout = {"audit": "audit-0.1.0.json", "regression": None,
                     "example-solver": "example-report-0.1.0.json", "example-checker": "example-verification-0.1.0.json"}
    for name, published in public_stdout.items():
        capture = json.loads((evidence / (name + "-capture-0.1.0.json")).read_bytes())
        if capture["exit_code"] != 0 or capture["gate_a_release"] is not False:
            raise ValueError("captured process failed or has the wrong authority scope")
        for path, expected in capture["sources"].items():
            if digest(root / path) != expected:
                raise ValueError("captured source differs: " + path)
        for kind, binding in capture["streams"].items():
            source = args.checks_root / (name + "." + kind)
            if source.stat().st_size != binding["byte_size"] or digest(source) != binding["sha256"]:
                raise ValueError("captured stream differs")
        if published and (args.checks_root / (name + ".stdout")).read_bytes() != (evidence / published).read_bytes():
            raise ValueError("published output differs from process stdout")
    regression = (args.checks_root / "regression.stderr").read_text()
    if re.search(r"Ran 21 tests in [0-9.]+s\n\nOK\n\Z", regression) is None:
        raise ValueError("completed regression summary differs")
    example_input = root / "research/m4-rectangular/0.1.0/example.json"
    example_report = evidence / "example-report-0.1.0.json"
    solver = json.loads(example_report.read_bytes())
    checked = json.loads((evidence / "example-verification-0.1.0.json").read_bytes())
    if (solver["input_sha256"] != digest(example_input)
            or solver["analyzer_sha256"] != digest(root / "tools/measure/rectangular_coincidence_bounds.py")
            or checked["input_sha256"] != digest(example_input)
            or checked["report_sha256"] != digest(example_report)
            or checked["checker_sha256"] != digest(root / "tools/measure/check_rectangular_bounds.py")
            or checked["status"] != "verified" or checked["checks"] != verify_bound(solver["result"])):
        raise ValueError("CLI example input, source or algebra closure differs")
    report_path = root / "docs/M4_RECTANGULAR_BOUND_FINDINGS_2026-09-07.md"
    report = report_path.read_text()
    check_table(report, audit)
    changed = report.replace("49.750000 (unattained)", "50.750000 (unattained)")
    try:
        check_table(changed, audit)
    except ValueError:
        pass
    else:
        raise ValueError("altered-number control was not rejected")
    allowed = {"README.md", "docs/SESSION_HANDOFF.md", "docs/GATE_B_SESSION_HANDOFF.md", "docs/RESEARCH_CONTINUATION_2026-09-07.md"}
    compared = 0
    for before in args.baseline_root.rglob("*"):
        if not before.is_file() or "__pycache__" in before.parts:
            continue
        relative = before.relative_to(args.baseline_root)
        if str(relative) in allowed:
            continue
        after = root / relative
        if not after.is_file() or digest(before) != digest(after):
            raise ValueError("unexpected predecessor change: " + str(relative))
        compared += 1
    bound = {}
    for path in root.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(root)
        if (relative.parts[:2] == ("evidence", "m4-bounds") and path.name in ("verification-0.1.0.json", "gate-b-check-0.1.0.json")):
            continue
        if not (args.baseline_root / relative).is_file() or str(relative) in allowed:
            bound[str(relative)] = digest(path)
    print(json.dumps({"artifact_id": "reiyah.m4-bounds-development-verification.0.1.0", "version": "0.1.0",
                      "status": "pass", "mode": "development", "gate_a_release": False,
                      "operator_acceptance": "unaccepted", "historical_report_calls_checked": 7,
                      "authored_controls_checked": 9, "tests_in_successful_capture": 21,
                      "unchanged_predecessor_files": compared, "bound_files": bound,
                      "scope": ["Exact source and completed-process closure", "All retained new mathematical witnesses rechecked",
                                "Report numerical table and altered-number rejection", "Predecessor byte preservation except four navigation documents"],
                      "limits": ["Not a new historical experiment replay", "Not independent human mathematical review",
                                 "Not evidence for an empirical reference process, a sampling interval or safety acceptance"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        print(json.dumps({"status": "invalid", "diagnostic": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
