"""Offline custody and metadata audit, not a physical calibration validator."""

import argparse
import hashlib
import json
from pathlib import Path
import sys


class Invalid(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise Invalid(code)


def pairs(items):
    out = {}
    for key, value in items:
        require(key not in out, "duplicate_json_key")
        out[key] = value
    return out


def nonfinite(_value):
    raise Invalid("nonfinite_json")


def read_json(path):
    return json.loads(
        Path(path).read_text(), object_pairs_hook=pairs, parse_constant=nonfinite
    )


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fields(value, expected, code):
    require(isinstance(value, dict) and set(value) == set(expected), code)


def bind_freeze(packet, expected):
    path = packet / "freeze.json"
    require(digest(path) == expected, "freeze_digest")
    freeze = read_json(path)
    require(
        digest(Path(sys.executable).resolve()) == freeze["runtime"]["sha256"],
        "runtime_digest",
    )
    for name, identity in freeze["files"].items():
        require(Path(name).name == name, "freeze_path")
        file = packet / name
        require(file.is_file(), "frozen_file_missing")
        require(
            file.stat().st_size == identity["bytes"]
            and digest(file) == identity["sha256"],
            "frozen_file_digest",
        )
    return freeze


def validate_review(review, source_ids):
    fields(
        review,
        (
            "document_id",
            "version",
            "status",
            "inspection_scope",
            "facts",
            "requirements",
            "outcomes",
            "uncertainty_values",
            "review_authority",
        ),
        "review_fields",
    )
    require(
        review["document_id"] == "reiyah.physical-source.qualification"
        and review["version"] == "0.1.0"
        and review["status"] == "exploratory",
        "review_identity",
    )
    expected_codes = {
        "source_identity": "documented",
        "two_actor_samples": "unmeasured",
        "body_geometry": "unresolved",
        "pose_uncertainty": "unresolved",
        "clock_residual": "unresolved",
        "inter_sample_motion": "unresolved",
        "whole_trajectory_coverage": "unresolved",
        "distribution_scope": "unresolved",
    }
    require(isinstance(review["requirements"], list), "requirements")
    rows = review["requirements"]
    require(len(rows) == len(expected_codes), "requirements")
    seen = set()
    for row in rows:
        fields(
            row,
            ("code", "assessment", "evidence_ids", "finding", "needed_record"),
            "requirement_fields",
        )
        code = row["code"]
        require(code in expected_codes and code not in seen, "requirements")
        seen.add(code)
        require(row["assessment"] == expected_codes[code], "review_scope_changed")
        require(
            isinstance(row["evidence_ids"], list)
            and row["evidence_ids"]
            and set(row["evidence_ids"]) <= source_ids,
            "evidence_reference",
        )
        require(
            all(
                isinstance(row[k], str) and row[k] for k in ("finding", "needed_record")
            ),
            "missing_review_text",
        )
    # These labels constrain this exposed review. They do not authorize future sources.
    expected_outcomes = {
        "physical_clearance": "unresolved",
        "physical_experiment": "blocked",
        "physical_benchmark_admitted": False,
        "sampled_proxy_executed": False,
        "physical_case_count": 0,
        "reserved_images_closed": 1433,
        "independent_replication": False,
        "gate_a_operator_accepted": False,
    }
    require(review["outcomes"] == expected_outcomes, "review_outcomes")
    require(
        all(
            type(review["outcomes"][k]) is type(v) for k, v in expected_outcomes.items()
        ),
        "review_outcome_types",
    )
    expected_unknowns = {
        "physical_position_bound_m",
        "physical_heading_bound_rad",
        "dataset_clock_bound_seconds",
        "global_clearance_rate_bound_mps",
        "simultaneous_coverage_probability",
    }
    fields(review["uncertainty_values"], expected_unknowns, "unknown_fields")
    require(
        all(v is None for v in review["uncertainty_values"].values()), "unknown_values"
    )


def bind_sources(ledger, sources):
    fields(
        ledger,
        (
            "document_id",
            "version",
            "primary_sources",
            "derived_sources",
            "captured_body_bytes",
            "derived_text_bytes",
            "eligibility",
            "untrusted",
        ),
        "ledger_fields",
    )
    require(ledger["untrusted"] is True, "source_authority")
    ids = set()
    allowed = set()
    for row in ledger["primary_sources"] + ledger["derived_sources"]:
        name = row["source_id"]
        require(Path(name).name == name and name not in ids, "source_name")
        ids.add(name)
        allowed.add(name)
        body = sources / name
        require(body.is_file() and not body.is_symlink(), "source_missing")
        require(
            body.stat().st_size == row["bytes"] and digest(body) == row["sha256"],
            "source_digest",
        )
    for row in ledger["primary_sources"]:
        receipt = sources / (row["source_id"] + ".receipt.json")
        allowed.add(receipt.name)
        require(
            receipt.is_file() and digest(receipt) == row["receipt_sha256"],
            "receipt_digest",
        )
        observed = read_json(receipt)
        require(
            all(
                observed[k] == row[k] for k in ("url", "bytes", "sha256", "http_status")
            ),
            "receipt_content",
        )
        require(
            observed["status"] == row["capture_status"] == "captured"
            and observed["http_status"] == 200,
            "source_http",
        )
    for row in ledger["derived_sources"]:
        require(row["parent_id"] in ids, "derived_parent")
    require({p.name for p in sources.iterdir()} == allowed, "unallocated_source")
    require(
        sum(r["bytes"] for r in ledger["primary_sources"])
        == ledger["captured_body_bytes"],
        "source_accounting",
    )
    require(
        sum(r["bytes"] for r in ledger["derived_sources"])
        == ledger["derived_text_bytes"],
        "derived_accounting",
    )
    return ids


def git_blob(path):
    body = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(body)).encode() + b"\0" + body).hexdigest()


def extract_facts(sources, source_cap):
    hf = read_json(sources / "hf-pinned.json")
    require(hf == read_json(sources / "hf-info.json"), "hf_revision_drift")
    require(hf["private"] is False and hf["gated"] is False, "public_access")
    names = [r["rfilename"] for r in hf["siblings"]]
    require(len(names) == len(set(names)), "duplicate_inventory_name")
    archives = [r for r in hf["siblings"] if "lfs" in r]
    require(all(r["size"] == r["lfs"]["size"] for r in archives), "lfs_size")
    require(
        all(type(r["size"]) is int and r["size"] >= 0 for r in hf["siblings"]),
        "inventory_size",
    )
    smallest = min(archives, key=lambda row: row["size"])
    commit = read_json(sources / "github-commit.json")
    tree = read_json(sources / "github-tree-object.json")
    require(tree["sha"] == commit["commit"]["tree"]["sha"], "github_tree_identity")
    require(tree["truncated"] is False, "tree_truncated")
    require(
        tree["tree"] == read_json(sources / "github-tree.json")["tree"], "tree_alias"
    )
    for local, remote in (
        ("github-README.md", "README.md"),
        ("github-node.cpp", "ros/scanario/src/target_objects/node.cpp"),
    ):
        item = next(r for r in tree["tree"] if r["path"] == remote)
        require(
            item["size"] == (sources / local).stat().st_size
            and git_blob(sources / local) == item["sha"],
            "github_blob",
        )
    for local, remote in (("hf-LICENSE", "LICENSE"), ("hf-README.md", "README.md")):
        item = next(r for r in hf["siblings"] if r["rfilename"] == remote)
        require(
            item["size"] == (sources / local).stat().st_size
            and git_blob(sources / local) == item["blobId"],
            "hf_blob",
        )
    return {
        "hf_revision": hf["sha"],
        "github_revision": commit["sha"],
        "github_tree": tree["sha"],
        "hf_files": len(hf["siblings"]),
        "archives": len(archives),
        "archive_bytes": sum(r["size"] for r in archives),
        "smallest_archive_path": smallest["rfilename"],
        "smallest_archive_bytes": smallest["size"],
        "ins_archive_bytes": next(
            r["size"] for r in archives if r["rfilename"] == "INS/INS.tar.xz"
        ),
        "github_tree_entries": len(tree["tree"]),
        "github_blobs": sum(r["type"] == "blob" for r in tree["tree"]),
        "archives_at_or_below_source_cap": sum(
            r["size"] <= source_cap for r in archives
        ),
        "archive_payloads_captured": sum(
            p.name.endswith(".tar.xz") for p in sources.iterdir()
        ),
    }


def audit(packet, sources, freeze):
    ledger = read_json(packet / "sources.json")
    review = read_json(packet / "qualification.json")
    ids = bind_sources(ledger, sources)
    validate_review(review, ids)
    facts = extract_facts(sources, freeze["limits"]["source_cap_bytes"])
    require(review["facts"] == facts, "review_inventory")
    require(
        ledger["captured_body_bytes"] + ledger["derived_text_bytes"]
        <= freeze["limits"]["source_cap_bytes"],
        "source_cap",
    )
    return {
        "document_id": "reiyah.physical-source.audit-result",
        "version": "0.1.0",
        "status": "pass",
        "facts": facts,
        "outcomes": review["outcomes"],
        "primary_sources_bound": len(ledger["primary_sources"]),
        "derived_sources_bound": len(ledger["derived_sources"]),
        "captured_body_bytes": ledger["captured_body_bytes"],
        "derived_text_bytes": ledger["derived_text_bytes"],
        "calibration_checked": False,
        "semantic_review_independently_checked": False,
        "scope": "Offline custody and inventory audit; no physical or comparative experiment",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--freeze-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    packet = Path(__file__).resolve().parent
    freeze = bind_freeze(packet, args.freeze_sha256)
    result = audit(packet, args.sources, freeze)
    result["freeze_sha256"] = args.freeze_sha256
    require(not args.output.exists(), "output_exists")
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (Invalid, OSError, ValueError, KeyError, TypeError, StopIteration) as error:
        print(json.dumps({"status": "fail", "reason": str(error)}))
        sys.exit(1)
