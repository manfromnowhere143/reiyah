"""Execute the frozen authored compatibility study, retaining partial failures."""

import argparse
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from bridge import Refusal, convert, digest  # noqa: E402
from fixtures import large_cases, refusal_cases, small_cases  # noqa: E402
from reference import conventional  # noqa: E402
from tools.perception_decision import (
    checker as old_checker,
    contract as old_contract,
    kernel,
)  # noqa: E402
from tools.perception_revision import audit, audit_checker  # noqa: E402


def one(original):
    started = time.perf_counter()
    converted = convert(original)
    payload = audit.produce(converted["case"], converted["request"], method="monotone")
    assert (
        audit_checker.check(converted["case"], converted["request"], payload)
        == payload["result"]
    )
    bounds = payload["result"]["bounds"]
    decision = None
    if bounds is not None:
        decision = kernel._classification(
            old_contract.rational(bounds["lower"]),
            old_contract.rational(bounds["upper"]),
            old_contract.rational(original["loss"]["tolerance"]),
        )
    engine_seconds = time.perf_counter() - started
    started = time.perf_counter()
    old_contract.validate(original)
    old = kernel.produce(original)
    assert old_checker.check(original, old) == old["result"]
    legacy_seconds = time.perf_counter() - started
    started = time.perf_counter()
    # Same original valid contract and common parser, independent matching
    # implementation and direct original-input endpoint calculation.
    old_contract.validate(original)
    other = conventional(original)
    conventional_seconds = time.perf_counter() - started
    return {
        "id": original["comparison_id"],
        "input_sha256": digest(original),
        "conversion": converted,
        "engine": {"payload": payload, "mapped_decision": decision},
        "legacy": old,
        "conventional": other,
        "seconds": {
            "conversion_production_checking": engine_seconds,
            "legacy_validation_production_checking": legacy_seconds,
            "conventional_validation_assignment_certification": conventional_seconds,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    args = parser.parse_args()
    path = Path(args.output)
    assert not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "document_id": "reiyah.presence-endpoints.execution",
        "version": "0.1.0",
        "status": "running_authored_development",
        "cases": [],
        "guard_controls": [],
        "actual_new_observations": 0,
        "empirical_cases": 0,
        "production_code_changed": False,
        "novel_solver": False,
        "comparative_advantage": "not_established",
        "independent_authorship": False,
        "cost_scope": "One fixed execution order per case, engine then legacy then conventional. "
        "Existing engine producer invokes its checker and workflow checks saved output again. "
        "Shared validation and parser; scopes are recorded, not a universal speed benchmark.",
    }
    started = time.perf_counter()
    try:
        for original in list(small_cases()) + large_cases():
            record["cases"].append(one(original))
        for name, expected, original in refusal_cases():
            observed = "accepted"
            try:
                convert(original)
            except Refusal as exc:
                observed = str(exc)
            record["guard_controls"].append(
                {
                    "id": name,
                    "expected": expected,
                    "observed": observed,
                    "passed": observed == expected,
                }
            )
            if observed != expected:
                raise AssertionError((name, expected, observed))
        record["status"] = "executed_check_pending"
    except Exception as exc:
        record["status"] = "failure_retained"
        record["error"] = type(exc).__name__ + ": " + str(exc)
        raise
    finally:
        record["workflow_seconds"] = time.perf_counter() - started
        with path.open("x") as output:
            json.dump(record, output, indent=2)
            output.write("\n")
    print(
        json.dumps(
            {
                "status": record["status"],
                "cases": len(record["cases"]),
                "guard_controls": len(record["guard_controls"]),
                "workflow_seconds": record["workflow_seconds"],
            }
        )
    )


if __name__ == "__main__":
    main()
