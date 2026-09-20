"""Eight allocated rejection controls and two frozen-file mutation controls."""

import argparse
import copy
import json
from pathlib import Path
import shutil
import tempfile

import audit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--freeze-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    packet = Path(__file__).resolve().parent
    freeze = audit.bind_freeze(packet, args.freeze_sha256)
    audit.audit(packet, args.sources, freeze)
    ledger = audit.read_json(packet / "sources.json")
    review = audit.read_json(packet / "qualification.json")
    ids = {
        r["source_id"] for r in ledger["primary_sources"] + ledger["derived_sources"]
    }
    results = []

    def reject(name, expected, action):
        try:
            action()
        except audit.Invalid as error:
            audit.require(
                str(error) == expected, "wrong_rejection:" + name + ":" + str(error)
            )
            results.append({"id": name, "expected_reason": expected, "status": "pass"})
        else:
            raise audit.Invalid("false_acceptance:" + name)

    def alter_review(change):
        value = copy.deepcopy(review)
        change(value)
        audit.validate_review(value, ids)

    reject(
        "physical_promotion",
        "review_outcomes",
        lambda: alter_review(
            lambda x: x["outcomes"].update(physical_benchmark_admitted=True)
        ),
    )
    reject(
        "unknown_to_zero",
        "unknown_values",
        lambda: alter_review(
            lambda x: x["uncertainty_values"].update(physical_position_bound_m=0)
        ),
    )
    reject(
        "clock_requirement_omitted",
        "requirements",
        lambda: alter_review(lambda x: x["requirements"].pop(4)),
    )
    reject(
        "unknown_review_property",
        "review_fields",
        lambda: alter_review(lambda x: x.update(accepted_by_model=True)),
    )
    with tempfile.TemporaryDirectory(prefix="physical-source-controls-") as temp:
        root = Path(temp)
        for mode, reason in (
            ("absent", "source_missing"),
            ("changed", "source_digest"),
            ("receipt", "receipt_digest"),
        ):
            target = root / mode
            shutil.copytree(args.sources, target)
            body = target / "hf-pinned.json"
            if mode == "absent":
                body.unlink()
            elif mode == "changed":
                body.write_bytes(body.read_bytes() + b" ")
            else:
                receipt = target / "hf-pinned.json.receipt.json"
                receipt.write_bytes(receipt.read_bytes() + b" ")
            reject("source_" + mode, reason, lambda: audit.bind_sources(ledger, target))
            shutil.rmtree(target)
        bad = root / "duplicate.json"
        bad.write_text('{"status":"unresolved","status":"supported"}')
        reject(
            "duplicate_json_property",
            "duplicate_json_key",
            lambda: audit.read_json(bad),
        )
        for name in ("qualification.json", "audit.py"):
            target = root / name.replace(".", "_")
            shutil.copytree(packet, target)
            file = target / name
            file.write_bytes(file.read_bytes() + b"\n")
            reject(
                "frozen_" + name,
                "frozen_file_digest",
                lambda: audit.bind_freeze(target, args.freeze_sha256),
            )
            shutil.rmtree(target)
    audit.require(not args.output.exists(), "output_exists")
    result = {
        "document_id": "reiyah.physical-source.controls",
        "version": "0.1.0",
        "freeze_sha256": args.freeze_sha256,
        "status": "pass",
        "results": results,
        "rejection_controls": 8,
        "frozen_file_controls": 2,
        "scope": "Artifact integrity and claim-scope guard tests, not calibration or scientific replication",
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
