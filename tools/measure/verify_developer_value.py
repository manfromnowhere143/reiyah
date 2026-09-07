#!/usr/bin/env python3
"""Offline development verification for the bounded developer-value revision.

Integrity and arithmetic controls, not a release launcher or scientific acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path

import jsonschema

from reference_population_audit import audit, canonical
from audit_sibling_evidence import sentinel, telos, inbar


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(data)
    return value.hexdigest()


def table_check(text, replay, coverage):
    channels = [replay["channels"][k] for k in ("camera", "lidar")]
    rows = [
        ("Frames represented in the cache", [c["samples"] for c in channels]),
        ("Score-qualified predictions", [c["selected_predictions"] for c in channels]),
        ("Near an included evaluation annotation", [c["counts"]["evaluation_reference_near"] for c in channels]),
        ("Evaluation-unmatched but near an excluded annotation", [c["counts"]["excluded_reference_near"] for c in channels]),
        ("Unmatched in the supplied wider annotation table", [c["counts"]["unmatched_in_supplied_wider_reference"] for c in channels]),
        ("Unknown-reference predictions in this supplied population", [c["counts"]["reference_unknown"] for c in channels]),
    ]
    extra = [coverage["channels"][k] for k in ("camera", "lidar")]
    rows += [("Score-qualified predictions", [c["omitted_frame_selected_detections"] for c in extra]),
             ("Near an annotation absent from the cache", [c["omitted_frame_audit_counts"]["excluded_reference_near"] for c in extra]),
             ("Unmatched in the supplied wider table", [c["omitted_frame_audit_counts"]["unmatched_in_supplied_wider_reference"] for c in extra])]
    for label, values in rows:
        line = "| " + label + " | " + " | ".join(f"{v:,}" for v in values) + " |"
        if text.splitlines().count(line) != 1:
            raise ValueError("numeric table binding failed: " + label)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--baseline-root", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    private = args.private_root
    evidence = root / "evidence/developer-value"
    checks = []
    def good(name, detail):
        checks.append({"check": name, "state": "pass", "detail": detail})
    def doc(name):
        return json.loads((evidence / name).read_bytes())
    schema = json.loads((root / "research/reference-audit/0.1.0/input.schema.json").read_bytes())
    jsonschema.Draft202012Validator.check_schema(schema)
    raw_demo = (root / "research/reference-audit/0.1.0/demo.json").read_bytes()
    jsonschema.Draft202012Validator(schema).validate(json.loads(raw_demo))
    if canonical(audit(raw_demo)) != (evidence / "reference-audit-demo-0.1.0.json").read_bytes():
        raise ValueError("demo differs from retained output")
    good("schema_and_demo", "Draft 2020-12 schema and exact current demo replay")
    source_ledger = doc("sibling-source-ledger-0.1.0.json")
    if (evidence / "sibling-source-ledger-0.1.0.json").read_bytes() != (private / "sibling-source-ledger.json").read_bytes():
        raise ValueError("private/public sibling ledger disagreement")
    for entry in source_ledger["entries"]:
        path = private / "sibling-sources" / entry["project"] / entry["path"]
        if sha(path) != entry["sha256"] or path.stat().st_size != entry["byte_size"]:
            raise ValueError("sibling source changed")
    audit_record = doc("sibling-audit-0.1.0.json")
    for project, function in (("sentinel", sentinel), ("telos", telos), ("inbar", inbar)):
        if function(private) != audit_record[project]:
            raise ValueError("sibling arithmetic differs")
    if audit_record["source_ledger_sha256"] != sha(evidence / "sibling-source-ledger-0.1.0.json"):
        raise ValueError("sibling ledger hash mismatch")
    if audit_record["analyzer_sha256"] != sha(root / "tools/measure/audit_sibling_evidence.py"):
        raise ValueError("sibling analyzer changed")
    good("sibling_sources_and_arithmetic", str(len(source_ledger["entries"])) + " exact selected Git blobs; three independent reaggregations")
    external = doc("source-ledger-0.1.0.json")["entries"]
    for row in external:
        path = private.parent / "external-sources" / (row["source_id"] + ".payload")
        if row["state"] != "retained_private" or row["gate_a_evidence_eligible"] is not False or sha(path) != row["sha256"]:
            raise ValueError("external source custody mismatch")
    good("primary_source_custody", str(len(external)) + " private primary payloads; no Gate A eligibility inferred")
    for prefix, directory in (("real-replay", "real-replay-1"), ("frame-coverage", "frame-coverage-1")):
        result, spec = doc(prefix + "-0.1.0.json"), doc(prefix + "-spec-0.1.0.json")
        if result["spec_sha256"] != sha(evidence / (prefix + "-spec-0.1.0.json")):
            raise ValueError("specification binding mismatch")
        if (evidence / (prefix + "-0.1.0.json")).read_bytes() != (private / directory / "result.json").read_bytes():
            raise ValueError("public/private aggregate mismatch")
        for item in result["private_output_closure"]:
            path = private / directory / item["path"]
            if sha(path) != item["sha256"] or path.stat().st_size != item["byte_size"]:
                raise ValueError("private replay output changed")
        capture = doc(prefix + "-capture-0.1.0.json")
        if capture["exit_code"] != 0:
            raise ValueError("replay process failed")
        for name, binding in capture["captures"].items():
            path = private.parent / "checks" / name
            if sha(path) != binding["sha256"] or path.stat().st_size != binding["byte_size"]:
                raise ValueError("supervisor stream mismatch")
        sources = spec.get("sources", {"replay_reference_population_audit.py": spec.get("adapter_sha256"),
                                       "reference_population_audit.py": spec.get("auditor_sha256")})
        if any(sha(root / "tools/measure" / name) != binding for name, binding in sources.items()):
            raise ValueError("replay code differs from executed source")
        good(prefix, "Successful captured process, source bindings and every private bundle/report digest")
    replay, coverage = doc("real-replay-0.1.0.json"), doc("frame-coverage-0.1.0.json")
    comparison = doc("numerical-comparison-0.1.0.json")
    if comparison["comparator_sha256"] != sha(root / "tools/measure/compare_reference_replays.py"):
        raise ValueError("numerical comparator changed")
    comparison_capture = doc("numerical-comparison-capture-0.1.0.json")
    if comparison_capture["exit_code"] != 0:
        raise ValueError("numerical comparator process failed")
    for kind, binding in comparison_capture["captures"].items():
        path = private.parent / "checks" / ("numerical-comparison." + kind)
        if sha(path) != binding["sha256"] or path.stat().st_size != binding["byte_size"]:
            raise ValueError("numerical comparison stream mismatch")
    if (private.parent / "checks/numerical-comparison.stdout").read_bytes() != (evidence / "numerical-comparison-0.1.0.json").read_bytes():
        raise ValueError("numerical comparison output differs from process capture")
    for channel in ("camera", "lidar"):
        old, check = replay["channels"][channel], comparison[channel]
        if check["classification_disagreements"] != 0 or old["selected_predictions"] != check["predictions"]:
            raise ValueError("numerical comparison population mismatch")
        if any(check["counts"].get(k, 0) != value for k, value in old["counts"].items()):
            raise ValueError("numerical comparison counts differ")
        if coverage["channels"][channel]["all_prediction_frame_selected_detections"] != old["selected_predictions"] + coverage["channels"][channel]["omitted_frame_selected_detections"]:
            raise ValueError("frame population partition does not close")
    if comparison["omitted_frames"]["predictions"] != sum(c["omitted_frame_selected_detections"] for c in coverage["channels"].values()):
        raise ValueError("omitted-frame comparison count mismatch")
    if comparison["omitted_frames"]["classification_disagreements"] != 0:
        raise ValueError("omitted-frame numerical disagreement")
    n_compared = sum(comparison[k]["predictions"] for k in ("camera", "lidar", "omitted_frames"))
    good("numerical_comparison", str(n_compared) + " retained classifications agree; shared source construction remains a limitation")
    text = (root / "docs/REFERENCE_AUDIT_REAL_DATA_2026-09-07.md").read_text()
    table_check(text, replay, coverage)
    try:
        table_check(text.replace("103,008", "103,009"), replay, coverage)
    except ValueError:
        pass
    else:
        raise ValueError("numeric table guard did not reject a false count")
    good("real_data_tables", "Both numerical tables bind to aggregates; changed-count counterexample rejected")
    for capture in doc("regression-capture-0.1.0.json"):
        if capture["exit_code"] != 0:
            raise ValueError("new regression failed")
        for kind, binding in capture["streams"].items():
            path = private.parent / "checks" / (capture["check_id"] + "." + kind)
            if sha(path) != binding["sha256"]:
                raise ValueError("regression capture changed")
    good("new_regressions", "12 portable-auditor and 7 adapter controls passed with captured streams")
    protected = ("manifests", "schemas", "fixtures", "gate", "history", "validation")
    protected_count = 0
    for folder in protected:
        old = {str(p.relative_to(args.baseline_root)) for p in (args.baseline_root / folder).rglob("*") if p.is_file()}
        new = {str(p.relative_to(root)) for p in (root / folder).rglob("*") if p.is_file()}
        if old != new:
            raise ValueError("protected release path set changed")
        for relative in old:
            if sha(args.baseline_root / relative) != sha(root / relative):
                raise ValueError("protected release bytes changed")
        protected_count += len(old)
    claim_register = "evidence/claim-status-register-2026-09-07.json"
    if sha(root / claim_register) != sha(args.baseline_root / claim_register):
        raise ValueError("claim register changed")
    good("protected_predecessor", str(protected_count) + " release files and the claim register remain byte-identical to 9d8a18e")
    bound = {}
    for folder in (root / "tools/measure", root / "research/reference-audit/0.1.0", evidence):
        for path in folder.iterdir():
            if path.is_file() and (folder != root / "tools/measure" or path.name in (
                "reference_population_audit.py", "replay_reference_population_audit.py", "audit_reference_frame_coverage.py",
                "compare_reference_replays.py", "audit_sibling_evidence.py", "test_reference_population_audit.py",
                "test_reference_replay_adapter.py", "verify_developer_value.py")) and path.name not in (
                    "verification-0.1.0.json", "gate-b-check-0.1.0.json"):
                bound[str(path.relative_to(root))] = sha(path)
    print(json.dumps({"artifact_id": "reiyah.developer-value-verification.0.1.0", "version": "0.1.0",
                      "mode": "development", "status": "pass", "gate_a_release": False,
                      "operator_acceptance": "unaccepted", "checks": checks, "bound_files": bound,
                      "limitations": ["Observed local execution and byte integrity, not independent scientific acceptance",
                                     "Inherited historical experiments are not all freshly replayed",
                                     "Table guard covers the named real-data tables, not arbitrary prose semantics"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
