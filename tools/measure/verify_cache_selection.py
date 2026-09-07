#!/usr/bin/env python3
"""Verify the retained cache-policy audit; local development evidence only."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from audit_cache_selection import policy_from_sources
from replay_reference_population_audit import digest
from reference_noise_counterexample import experiment


def summary_table(result):
    data = result["result"]
    membership = data["annotation_membership"]
    rows = [("Official validation scenes", data["validation_scene_count"]),
            ("Official validation frames", data["validation_frame_count"]),
            ("All validation annotations", data["validation_annotation_count"]),
            ("Unmapped categories", data["selection_reason_counts"]["unmapped_category"]),
            ("Mapped annotations outside the strict class range", data["selection_reason_counts"]["outside_class_range"]),
            ("Annotations selected by the declared cache policy", membership["expected_annotation_count"]),
            ("Selected annotations with zero lidar and radar points", data["included_zero_point_annotations"]),
            ("Validation frames without selected annotations", data["frames_without_selected_annotations"]),
            ("Expected annotation IDs absent from the cache", membership["expected_absent_from_cache"]),
            ("Cache annotation IDs outside the expected set", membership["cache_absent_from_expected"]),
            ("Cached rows with a checked metadata disagreement", membership["cache_metadata_mismatches"])]
    return "\n".join(["| Quantity | Count |", "| --- | ---: |"] + [f"| {key} | {value:,} |" for key, value in rows])


def check_table(text, result):
    if text.count(summary_table(result)) != 1:
        raise ValueError("cache selection table does not match retained result")


def public_specification(spec, private_digest):
    projection = json.loads(json.dumps(spec))
    names = projection["policy"].pop("validation_scene_names")
    raw = (json.dumps(names, sort_keys=True, separators=(",", ":")) + "\n").encode()
    projection["policy"]["validation_scene_count"] = len(names)
    projection["policy"]["validation_scene_names_sha256"] = hashlib.sha256(raw).hexdigest()
    return {"artifact_id": "reiyah.cache-selection-public-specification.0.1.0", "version": "0.1.0",
            "private_spec_sha256": private_digest,
            "disclosure": "Aggregate policy projection; the full scene-identifier list remains in private custody",
            "specification": projection}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--baseline-root", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    task = args.private_root.parent
    evidence = root / "evidence/cache-selection"
    names = {"result": "result-0.1.0.json", "spec": "spec-0.1.0.json", "source-ledger": "source-ledger-0.1.0.json",
             "capture": "capture-0.1.0.json", "regression": "regression-0.1.0.json"}
    docs = {key: json.loads((evidence / name).read_bytes()) for key, name in names.items()}
    result, ledger = docs["result"], docs["source-ledger"]
    run = args.private_root / "cache-selection-1"
    spec = json.loads((run / "spec.json").read_bytes())
    if (run / "result.json").read_bytes() != (evidence / names["result"]).read_bytes():
        raise ValueError("public and private result records differ")
    if result["spec_sha256"] != digest(run / "spec.json"):
        raise ValueError("result is bound to a different specification")
    if docs["spec"] != public_specification(spec, digest(run / "spec.json")):
        raise ValueError("public specification projection differs from the private executed specification")
    if spec["source_ledger_sha256"] != digest(evidence / names["source-ledger"]):
        raise ValueError("source ledger binding differs")
    if spec["historical_split_sha256"] != digest(root / "evidence/nuscenes_splits_devkit.py"):
        raise ValueError("historical split differs")
    if policy_from_sources(task / "external-sources", root / "evidence/nuscenes_splits_devkit.py") != spec["policy"]:
        raise ValueError("literal upstream policy differs")
    for entry in ledger["entries"]:
        source = task / "external-sources" / (entry["source_id"] + ".payload")
        if digest(source) != entry["sha256"] or source.stat().st_size != entry["byte_size"] or entry["gate_a_evidence_eligible"] is not False:
            raise ValueError("retained primary-source custody differs")
    for name, sha in spec["sources"].items():
        if digest(root / "tools/measure" / name) != sha:
            raise ValueError("executed code differs")
    for name, binding in spec["inputs"].items():
        path = args.data_root / name
        if digest(path) != binding["sha256"] or path.stat().st_size != binding["bytes"]:
            raise ValueError("retained raw input differs")
    for capture, stem in ((docs["capture"], "cache-selection"), (docs["regression"], "regression")):
        if capture["exit_code"] != 0:
            raise ValueError("recorded process did not succeed")
        for kind, binding in capture["streams"].items():
            path = task / "checks" / (stem + "." + kind)
            if digest(path) != binding["sha256"] or path.stat().st_size != binding["byte_size"]:
                raise ValueError("process stream differs")
    if (task / "checks/cache-selection.stdout").read_bytes() != (evidence / names["result"]).read_bytes():
        raise ValueError("published aggregate differs from completed process stdout")
    for name, binding in docs["regression"]["sources"].items():
        if digest(root / "tools/measure" / name) != binding:
            raise ValueError("regression source differs")
    for binding in result["private_output_closure"]:
        path = run / binding["path"]
        if digest(path) != binding["sha256"] or path.stat().st_size != binding["bytes"]:
            raise ValueError("private per-annotation output differs")
    counts, classes, annotations, included, mismatch_count = Counter(), Counter(), set(), set(), 0
    with (run / "annotation-dispositions.private.jsonl").open() as stream:
        for raw in stream:
            row = json.loads(raw)
            if row["annotation_id"] in annotations:
                raise ValueError("repeated annotation disposition")
            annotations.add(row["annotation_id"])
            counts[row["selection_reason"]] += 1
            mismatch_count += bool(row["cache_metadata_errors"])
            if row["selection_reason"] == "included":
                included.add(row["sample_token"])
                classes[row["mapped_class"]] += 1
    outcome = result["result"]
    if (dict(counts) != outcome["selection_reason_counts"] or dict(classes) != outcome["included_class_counts"]
            or len(annotations) != outcome["validation_annotation_count"]
            or len(included) != outcome["frames_with_selected_annotations"]
            or mismatch_count != outcome["annotation_membership"]["cache_metadata_mismatches"]):
        raise ValueError("private dispositions do not reproduce aggregate")
    differences = json.loads((run / "membership-differences.private.json").read_bytes())
    if any(len(values) != outcome["annotation_membership"][key] for key, values in differences.items()):
        raise ValueError("private identity differences do not reproduce aggregate")
    if outcome["physical_false_positive_rate"] is not None:
        raise ValueError("unearned physical conclusion")
    noise = json.loads((evidence / "reference-noise-control-0.1.0.json").read_bytes())
    if noise != experiment():
        raise ValueError("exact reference-noise control differs")
    noise_capture = json.loads((evidence / "reference-noise-capture-0.1.0.json").read_bytes())
    if noise_capture["exit_code"] != 0:
        raise ValueError("reference-noise process failed")
    for kind, binding in noise_capture["streams"].items():
        path = task / "checks" / ("reference-noise." + kind)
        if digest(path) != binding["sha256"] or path.stat().st_size != binding["byte_size"]:
            raise ValueError("reference-noise stream differs")
    if (task / "checks/reference-noise.stdout").read_bytes() != (evidence / "reference-noise-control-0.1.0.json").read_bytes():
        raise ValueError("reference-noise output differs from captured process")
    report = (root / "docs/CACHE_SELECTION_AUDIT_2026-09-07.md").read_text()
    check_table(report, result)
    count = outcome["annotation_membership"]["expected_annotation_count"]
    wrong = report.replace(f"| {count:,} |", f"| {count + 1:,} |")
    if wrong == report:
        raise ValueError("numeric counterexample was not constructed")
    try:
        check_table(wrong, result)
    except ValueError:
        pass
    else:
        raise ValueError("table control failed to reject changed output")
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
    for directory in (evidence, root / "tools/measure"):
        for path in directory.iterdir():
            if path.is_file() and ((directory == evidence and path.name not in ("verification-0.1.0.json", "gate-b-check-0.1.0.json"))
                    or path.name in ("audit_cache_selection.py", "test_cache_selection.py", "verify_cache_selection.py", "reference_noise_counterexample.py")):
                bound[str(path.relative_to(root))] = digest(path)
    print(json.dumps({"artifact_id": "reiyah.cache-selection-verification.0.1.0", "version": "0.1.0", "status": "pass",
                      "mode": "development", "gate_a_release": False, "operator_acceptance": "unaccepted",
                      "scope": ["Retained private input, source and output digests", "Completed audit and nine test process captures",
                                "Per-annotation aggregate rederivation", "Exact shared-reference noise counterexample and matched-marginal ablation",
                                "Numeric table binding with altered-output control",
                                "Every predecessor file except four explicitly allowed navigation documents"],
                      "unchanged_predecessor_files": compared, "bound_files": bound,
                      "limits": ["Integrity and reaggregation, not independent physical reference or independent acceptance",
                                 "This check does not repeat the complete metadata calculation or historical experiments"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
