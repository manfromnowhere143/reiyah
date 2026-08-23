#!/usr/bin/env python3
# Copyright 2026 Daniel Wahnich
# SPDX-License-Identifier: Apache-2.0
"""Emit the deterministic, acyclic Gate A evidence index or its sidecar.

This builder reads repository bytes and writes only to stdout. Redirecting its output is an
explicit caller action; the builder itself never mutates the repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


CANONICAL_ROOT = Path("/Users/danielwahnich/workspace/reiyah")
INDEX_PATH = "gate/GATE_A_EVIDENCE_INDEX.json"
SIDECAR_PATH = "gate/GATE_A_EVIDENCE_INDEX.sha256"
ACTUAL_DECISION_PREFIX = "gate/decisions/reiyah.gate-a-decision-"
PUBLIC_RECEIPT_PREFIX = "gate/public-distribution-receipts/reiyah.public-distribution-receipt-"
DEFAULT_ARTIFACT_VERSION = "1.1.0"
AUTHORIZED_TOOL_PATHS = frozenset(
    {"tools/build_gate_a_index.py", "tools/validate_gate_a.py"}
)

EXCLUSIONS: tuple[dict[str, str], ...] = (
    {
        "exclusion_id": "reiyah.exclusion.index-self",
        "match_kind": "exact",
        "path": INDEX_PATH,
        "reason": "The evidence index cannot hash itself without a circular identity.",
    },
    {
        "exclusion_id": "reiyah.exclusion.index-sidecar",
        "match_kind": "exact",
        "path": SIDECAR_PATH,
        "reason": "The sidecar is derived from the index bytes and cannot be an indexed input.",
    },
    {
        "exclusion_id": "reiyah.exclusion.validation-reports",
        "match_kind": "exact",
        "path": "gate/validation-reports/gate-a-validation-1.1.0.json",
        "reason": "The canonical validation report is an output bound to the index, not an index input.",
    },
    {
        "exclusion_id": "reiyah.exclusion.operator-decisions",
        "match_kind": "prefix",
        "path": ACTUAL_DECISION_PREFIX,
        "reason": "Append-only operator decisions bind an index digest and therefore remain outside it.",
    },
    {
        "exclusion_id": "reiyah.exclusion.public-distribution-receipts",
        "match_kind": "prefix",
        "path": PUBLIC_RECEIPT_PREFIX,
        "reason": "Append-only post-distribution receipts bind the published packet and therefore remain outside the pre-distribution index.",
    },
    {
        "exclusion_id": "reiyah.exclusion.git-metadata",
        "match_kind": "prefix",
        "path": ".git/",
        "reason": "Git implementation metadata is transient and is not part of the reviewed architecture surface.",
    },
    {
        "exclusion_id": "reiyah.exclusion.macos-metadata",
        "match_kind": "exact",
        "path": ".DS_Store",
        "reason": "Finder metadata is transient and non-normative.",
    },
    {
        "exclusion_id": "reiyah.exclusion.pytest-cache",
        "match_kind": "prefix",
        "path": ".pytest_cache/",
        "reason": "Test-run cache bytes are nondeterministic validation outputs.",
    },
    {
        "exclusion_id": "reiyah.exclusion.root-pycache",
        "match_kind": "prefix",
        "path": "__pycache__/",
        "reason": "Interpreter bytecode cache is transient toolchain output.",
    },
    {
        "exclusion_id": "reiyah.exclusion.tools-pycache",
        "match_kind": "prefix",
        "path": "tools/__pycache__/",
        "reason": "Interpreter bytecode cache is transient toolchain output.",
    },
    {
        "exclusion_id": "reiyah.exclusion.validation-pycache",
        "match_kind": "prefix",
        "path": "validation/__pycache__/",
        "reason": "Interpreter bytecode cache is transient toolchain output.",
    },
    {
        "exclusion_id": "reiyah.exclusion.fixtures-pycache",
        "match_kind": "prefix",
        "path": "fixtures/__pycache__/",
        "reason": "Interpreter bytecode cache is transient toolchain output.",
    },
    {
        "exclusion_id": "reiyah.exclusion.good-fixtures-pycache",
        "match_kind": "prefix",
        "path": "fixtures/good/__pycache__/",
        "reason": "Interpreter bytecode cache is transient toolchain output.",
    },
    {
        "exclusion_id": "reiyah.exclusion.bad-fixtures-pycache",
        "match_kind": "prefix",
        "path": "fixtures/bad/__pycache__/",
        "reason": "Interpreter bytecode cache is transient toolchain output.",
    },
)

EXACT_ROLES: dict[str, str] = {
    ".gitattributes": "repository_metadata",
    ".gitignore": "repository_metadata",
    "AGENTS.md": "repository_contract",
    "CITATION.cff": "citation_metadata",
    "CONTRIBUTING.md": "contribution_policy",
    "LICENSE": "open_source_license",
    "NOTICE": "attribution_notice",
    "README.md": "repository_overview",
    "SECURITY.md": "security_policy",
    "docs/ARCHITECTURE.md": "architecture_specification",
    "docs/CLAIMS_AND_NON_CLAIMS.md": "claims_and_non_claims",
    "docs/GLOSSARY.md": "glossary",
    "docs/MATHEMATICAL_SPECIFICATION.md": "mathematical_specification",
    "docs/PRE_IMPLEMENTATION_GATE.md": "preimplementation_gate",
    "docs/SCIENTIFIC_CHARTER.md": "scientific_charter",
    "docs/SESSION_HANDOFF.md": "session_handoff",
    "docs/SOURCE_POLICY.md": "source_policy",
    "docs/STANDARDS_CROSSWALK.md": "standards_crosswalk",
    "docs/STATUS_MODEL.md": "status_model",
    "docs/THREAT_MODEL.md": "threat_model",
    "docs/VALIDATION.md": "validation_specification",
    "docs/FRONTIER_BASELINE_2026.md": "frontier_baseline",
    "docs/RESEARCH_GAP_REGISTER.md": "research_gap_register",
    "docs/RESEARCH_OPERATING_MODEL.md": "research_operating_model",
    "evidence/README.md": "evidence_custody_documentation",
    "evidence/frontier-discovery-register-1.1.0.json": "frontier_discovery_register",
    "evidence/public-distribution-inventory-1.1.0.json": "public_distribution_inventory",
    "evidence/public-evidence-custody-profile-1.1.0.json": "public_evidence_custody_profile",
    "evidence/public-rights-revalidation-2026-08-23.json": "public_rights_revalidation",
    "evidence/source-ledger-1.1.0.json": "source_ledger",
    "evidence/source-ledger.json": "historical_source_ledger",
    "evidence/standards-crosswalk-1.1.0.json": "standards_crosswalk",
    "evidence/standards-crosswalk.json": "historical_standards_crosswalk",
    "fixtures/fixture-catalog.json": "fixture_catalog",
    "gate/validation-reports/gate-a-validation-1.0.0.json": "historical_candidate_artifact",
    "gate/README.md": "acceptance_procedure",
    "gate/decisions/OPERATOR_DECISION.template.json": "operator_decision_template",
    "manifests/manifest-release-ledger.json": "manifest_release_ledger",
    "manifests/history/manifest-release-ledger-1.0.0.json": "historical_manifest_release_ledger",
    "manifests/scientific/harbor-scientific-contract-profile-1.1.0.json": "scientific_contract_profile",
    "history/gate-a-1.0.0/RECOVERY.json": "historical_packet_recovery",
    "validation/requirements.lock": "repository_metadata",
    "validation/validation-plan.json": "validation_specification",
    "tools/validate_gate_a.py": "offline_validator",
    "tools/build_gate_a_index.py": "index_builder",
}

DOC_MEDIA_TYPES = {
    ".cff": "application/yaml",
    ".html": "text/html",
    ".json": "application/json",
    ".jsonl": "application/x-ndjson",
    ".lock": "text/plain",
    ".md": "text/markdown",
    ".pdf": "application/pdf",
    ".py": "text/x-python",
    ".sha256": "text/plain",
}

ROLE_SCHEMA_IDS: dict[str, frozenset[str]] = {
    "manifest_release_ledger": frozenset({
        "https://schemas.reiyah.invalid/gate-a/1.1.0/manifest-release-ledger.schema.json"
    }),
    "historical_manifest_release_ledger": frozenset({
        "https://schemas.reiyah.invalid/gate-a/1.0.0/manifest-release-ledger.schema.json"
    }),
    "source_ledger": frozenset({
        "https://schemas.reiyah.invalid/gate-a/1.1.0/source-ledger.schema.json"
    }),
    "historical_source_ledger": frozenset({
        "https://schemas.reiyah.invalid/gate-a/1.0.0/source-ledger.schema.json"
    }),
    "standards_crosswalk": frozenset({
        "https://schemas.reiyah.invalid/gate-a/1.1.0/standards-crosswalk.schema.json"
    }),
    "historical_standards_crosswalk": frozenset({
        "https://schemas.reiyah.invalid/gate-a/1.0.0/standards-crosswalk.schema.json"
    }),
    "frontier_discovery_register": frozenset({
        "https://schemas.reiyah.invalid/gate-a/1.1.0/frontier-discovery-register.schema.json"
    }),
    "public_distribution_inventory": frozenset({
        "https://schemas.reiyah.invalid/gate-a/1.1.0/public-distribution-inventory.schema.json"
    }),
    "public_evidence_custody_profile": frozenset({
        "https://schemas.reiyah.invalid/gate-a/1.1.0/public-evidence-custody-profile.schema.json"
    }),
    "public_rights_revalidation": frozenset({
        "https://schemas.reiyah.invalid/gate-a/1.1.0/public-rights-revalidation.schema.json"
    }),
    "fixture_catalog": frozenset({
        "https://schemas.reiyah.invalid/gate-a/1.1.0/fixture-catalog.schema.json"
    }),
    "operator_decision_template": frozenset({
        "https://schemas.reiyah.invalid/gate-a/1.1.0/operator-decision-record.schema.json"
    }),
    "historical_packet_recovery": frozenset({
        "https://schemas.reiyah.invalid/gate-a/1.1.0/historical-packet-recovery.schema.json"
    }),
    "mission_manifest": frozenset({
        "https://schemas.reiyah.invalid/gate-a/1.0.0/mission-manifest.schema.json",
        "https://schemas.reiyah.invalid/gate-a/1.1.0/mission-manifest.schema.json",
    }),
    "protocol_manifest": frozenset({
        "https://schemas.reiyah.invalid/gate-a/1.0.0/protocol-manifest.schema.json",
        "https://schemas.reiyah.invalid/gate-a/1.1.0/protocol-manifest.schema.json",
    }),
    "protocol_definition_registry": frozenset({
        "https://schemas.reiyah.invalid/gate-a/1.0.0/protocol-definition-registry.schema.json",
        "https://schemas.reiyah.invalid/gate-a/1.1.0/protocol-definition-registry.schema.json",
    }),
    "known_bad_fixture": frozenset({
        "https://schemas.reiyah.invalid/gate-a/1.0.0/fixture-case.schema.json",
        "https://schemas.reiyah.invalid/scientific-contract/1.1.0/scientific-contract-mutation-fixture.schema.json",
    }),
    "known_good_fixture": frozenset({
        "https://schemas.reiyah.invalid/gate-a/1.0.0/fixture-case.schema.json",
        "https://schemas.reiyah.invalid/gate-a/1.0.0/analysis-specification.schema.json",
        "https://schemas.reiyah.invalid/gate-a/1.0.0/preregistration-record.schema.json",
        "https://schemas.reiyah.invalid/gate-a/1.0.0/observation.schema.json",
        "https://schemas.reiyah.invalid/gate-a/1.0.0/latent-belief.schema.json",
        "https://schemas.reiyah.invalid/gate-a/1.0.0/decision.schema.json",
        "https://schemas.reiyah.invalid/gate-a/1.0.0/intervention.schema.json",
        "https://schemas.reiyah.invalid/gate-a/1.0.0/outcome.schema.json",
        "https://schemas.reiyah.invalid/gate-a/1.0.0/evidence-object.schema.json",
        "https://schemas.reiyah.invalid/gate-a/1.0.0/experiment.schema.json",
        "https://schemas.reiyah.invalid/gate-a/1.0.0/result.schema.json",
        "https://schemas.reiyah.invalid/scientific-contract/1.1.0/human-automation-assessment.schema.json",
        "https://schemas.reiyah.invalid/scientific-contract/1.1.0/joint-performance-evaluation.schema.json",
        "https://schemas.reiyah.invalid/scientific-contract/1.1.0/study-design-preregistration.schema.json",
        "https://schemas.reiyah.invalid/scientific-contract/1.1.0/sequential-off-policy-evaluation.schema.json",
        "https://schemas.reiyah.invalid/scientific-contract/1.1.0/evaluation-assurance-bundle.schema.json",
    }),
    "research_function_registry": frozenset({
        "https://schemas.reiyah.invalid/gate-a/1.1.0/research-function-registry.schema.json"
    }),
    "scientific_contract_profile": frozenset({
        "https://schemas.reiyah.invalid/gate-a/1.1.0/scientific-contract-profile.schema.json"
    }),
}


class BuildFailure(RuntimeError):
    """A fail-closed deterministic inventory error."""


def reject_nonfinite_constant(token: str) -> Any:
    raise ValueError(f"non-finite JSON number is forbidden: {token}")


def reject_duplicate_members(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object member is forbidden: {key!r}")
        result[key] = value
    return result


def strict_json_loads(text: str) -> Any:
    value = json.loads(
        text,
        parse_constant=reject_nonfinite_constant,
        object_pairs_hook=reject_duplicate_members,
    )
    stack = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, float) and not math.isfinite(current):
            raise ValueError("non-finite JSON number is forbidden")
        if isinstance(current, dict):
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)
    return value


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def is_excluded(path: str) -> bool:
    for exclusion in EXCLUSIONS:
        if exclusion["match_kind"] == "exact" and path == exclusion["path"]:
            return True
        if exclusion["match_kind"] == "prefix" and path.startswith(exclusion["path"]):
            return True
    return False


def role_for(path: str) -> str:
    if path in EXACT_ROLES:
        return EXACT_ROLES[path]
    if path.startswith("evidence/sources/"):
        return "retained_source"
    if path.startswith("schemas/") and path.endswith(".schema.json"):
        return "schema"
    if path.startswith("fixtures/good/") and path.endswith(".json"):
        return "known_good_fixture"
    if path.startswith("fixtures/bad/") and path.endswith(".json"):
        return "known_bad_fixture"
    if path.startswith("fixtures/v1.1/good/") and path.endswith(".json"):
        return "known_good_fixture"
    if path.startswith("fixtures/v1.1/known-bad/") and path.endswith(".json"):
        return "known_bad_fixture"
    if path.startswith("manifests/mission/") and path.endswith(".json"):
        return "mission_manifest"
    if path.startswith("manifests/protocol/") and path.endswith(".json"):
        return "protocol_manifest"
    if path.startswith("manifests/definitions/") and path.endswith(".json"):
        return "protocol_definition_registry"
    if path.startswith("manifests/research/") and path.endswith(".json"):
        return "research_function_registry"
    if path.startswith("manifests/claims/") and path.endswith(".json"):
        return "claims_and_non_claims"
    if path.startswith("manifests/examples/object-chain/") and path.endswith(".json"):
        return "known_good_fixture"
    if path.startswith("history/gate-a-1.0.0/"):
        return "historical_candidate_artifact"
    raise BuildFailure(f"undeclared Gate A artifact role for {path}")


def media_type_for(path: str) -> str:
    if path in {".gitattributes", ".gitignore", "LICENSE", "NOTICE"}:
        return "text/plain"
    suffix = Path(path).suffix.lower()
    try:
        return DOC_MEDIA_TYPES[suffix]
    except KeyError as exc:
        raise BuildFailure(f"undeclared media type for {path}") from exc


def derived_artifact_id(path: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-")
    if len(slug) > 125:
        slug = slug[:92].rstrip("-") + "-" + hashlib.sha256(path.encode("utf-8")).hexdigest()[:24]
    return "reiyah.artifact.indexed-" + slug


def json_metadata(path: str, raw: bytes) -> tuple[str | None, str | None, str | None]:
    if not path.endswith(".json"):
        return None, None, None
    try:
        data = strict_json_loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise BuildFailure(f"malformed indexed JSON artifact {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise BuildFailure(f"indexed JSON artifact must be an object: {path}")

    if path == "gate/decisions/OPERATOR_DECISION.template.json":
        artifact_id = "reiyah.artifact.operator-decision-template"
    else:
        candidate = data.get("artifact_id")
        artifact_id = candidate if isinstance(candidate, str) and not candidate.startswith("replace.") else None

    schema_id = data.get("schema_id") if isinstance(data.get("schema_id"), str) else None
    if path.startswith("schemas/"):
        schema_id = data.get("$id") if isinstance(data.get("$id"), str) else None

    version = data.get("version")
    if not isinstance(version, str):
        version = data.get("schema_version") if isinstance(data.get("schema_version"), str) else None
    if path.startswith("schemas/") and version is None:
        version = (
            "1.1.0"
            if "/1.1.0/" in str(schema_id)
            or "-1.1.schema.json" in path
            or path.startswith("schemas/v1.1/")
            else "1.0.0"
        )
    return artifact_id, schema_id, version


def retained_source_artifact_ids(root: Path) -> dict[str, str]:
    ledger_path = root / "evidence/source-ledger-1.1.0.json"
    try:
        ledger = strict_json_loads(ledger_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise BuildFailure(f"cannot read source ledger: {exc}") from exc
    records = ledger.get("records")
    if not isinstance(records, list):
        raise BuildFailure("source ledger records must be an array")
    result: dict[str, str] = {}
    source_ids: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise BuildFailure("source ledger records must be objects")
        retained_payload = record.get("retained_payload")
        if retained_payload is None:
            if record.get("evidence_eligibility") != "ineligible_pointer_only":
                raise BuildFailure(
                    "source record without retained bytes is not explicitly pointer-only: "
                    f"{record.get('source_id')!r}"
                )
            continue
        if not isinstance(retained_payload, dict):
            raise BuildFailure("retained_payload must be an object or null")
        retained_path = retained_payload.get("path")
        source_id = record.get("source_id")
        if not isinstance(retained_path, str) or not retained_path.startswith("evidence/sources/"):
            raise BuildFailure(f"invalid retained source path in ledger: {retained_path!r}")
        if not isinstance(source_id, str) or not source_id:
            raise BuildFailure(f"invalid source_id for retained path {retained_path}")
        if retained_path in result:
            raise BuildFailure(f"duplicate retained source path in ledger: {retained_path}")
        if source_id in source_ids:
            raise BuildFailure(f"duplicate source_id in ledger: {source_id}")
        source_ids.add(source_id)
        result[retained_path] = "reiyah.artifact.retained-" + re.sub(
            r"[^a-z0-9]+", "-", source_id.lower()
        ).strip("-")

    sources_root = root / "evidence/sources"
    actual_paths: set[str] = set()
    if sources_root.is_symlink():
        raise BuildFailure("retained source directory symlink is forbidden")
    if sources_root.is_dir():
        for candidate in sources_root.rglob("*"):
            relative = candidate.relative_to(root).as_posix()
            if candidate.is_symlink():
                raise BuildFailure(f"retained source symlink is forbidden: {relative}")
            if candidate.is_file():
                actual_paths.add(relative)
    ledger_paths = set(result)
    if actual_paths != ledger_paths:
        raise BuildFailure(
            "retained source inventory does not exactly equal the source ledger; "
            f"unledgered={sorted(actual_paths - ledger_paths)}, "
            f"missing={sorted(ledger_paths - actual_paths)}"
        )
    return result


def verify_authorized_tool_bindings(root: Path, plan: dict[str, Any]) -> None:
    """Refuse to index tool bytes not explicitly frozen by the validation plan."""
    bindings = plan.get("authorized_tool_bindings")
    if not isinstance(bindings, list) or len(bindings) != len(AUTHORIZED_TOOL_PATHS):
        raise BuildFailure("validation plan must freeze exactly the two authorized tools")
    observed_paths: set[str] = set()
    for binding in bindings:
        if not isinstance(binding, dict) or set(binding) != {"path", "sha256"}:
            raise BuildFailure("authorized tool bindings must contain only path and sha256")
        relative = binding.get("path")
        expected_digest = binding.get("sha256")
        if not isinstance(relative, str) or relative not in AUTHORIZED_TOOL_PATHS:
            raise BuildFailure(f"unauthorized or malformed tool binding path: {relative!r}")
        if relative in observed_paths:
            raise BuildFailure(f"duplicate authorized tool binding: {relative}")
        observed_paths.add(relative)
        absolute = root / relative
        if absolute.is_symlink() or not absolute.is_file():
            raise BuildFailure(f"authorized tool must be an exact regular file: {relative}")
        actual_digest = sha256_bytes(absolute.read_bytes())
        if expected_digest != actual_digest:
            raise BuildFailure(
                f"authorized tool digest mismatch for {relative}: "
                f"expected={expected_digest!r}, actual={actual_digest}"
            )
    if observed_paths != AUTHORIZED_TOOL_PATHS:
        raise BuildFailure(
            f"authorized tool binding set mismatch: {sorted(observed_paths)}"
        )


def inventory_paths(root: Path) -> list[str]:
    paths: list[str] = []
    for candidate in root.rglob("*"):
        relative = candidate.relative_to(root).as_posix()
        if is_excluded(relative):
            continue
        if candidate.is_symlink():
            raise BuildFailure(
                f"indexed symlink is forbidden: {relative}"
            )
        if not candidate.is_file():
            continue
        if "__pycache__" in candidate.relative_to(root).parts:
            raise BuildFailure(f"nested __pycache__ lacks an explicit prefix exclusion: {relative}")
        paths.append(relative)
    return sorted(paths)


def build_index(root: Path) -> dict[str, Any]:
    if root.resolve() != CANONICAL_ROOT:
        raise BuildFailure(f"builder root is not canonical Reiyah: {root.resolve()}")

    plan = strict_json_loads((root / "validation/validation-plan.json").read_text(encoding="utf-8"))
    if not isinstance(plan, dict):
        raise BuildFailure("validation plan must be a JSON object")
    verify_authorized_tool_bindings(root, plan)
    plan_exclusions = plan.get("index", {}).get("excluded_paths")
    expected_exclusions = [entry["path"] for entry in EXCLUSIONS]
    if plan_exclusions != expected_exclusions:
        raise BuildFailure("validation-plan exclusions do not exactly match builder exclusions")

    source_ids = retained_source_artifact_ids(root)
    artifacts: list[dict[str, Any]] = []
    seen_artifact_ids: set[str] = set()

    for relative in inventory_paths(root):
        absolute = root / relative
        raw = absolute.read_bytes()
        artifact_id, schema_id, version = json_metadata(relative, raw)
        if relative in source_ids:
            artifact_id = source_ids[relative]
        if artifact_id is None:
            artifact_id = derived_artifact_id(relative)
        if version is None:
            version = DEFAULT_ARTIFACT_VERSION
        if artifact_id in seen_artifact_ids:
            raise BuildFailure(f"duplicate indexed artifact_id {artifact_id}")
        seen_artifact_ids.add(artifact_id)

        role = role_for(relative)
        allowed_schema_ids = ROLE_SCHEMA_IDS.get(role)
        if relative.startswith("manifests/claims/"):
            allowed_schema_ids = frozenset({
                "https://schemas.reiyah.invalid/gate-a/1.0.0/claim-register.schema.json"
            })
        if (
            allowed_schema_ids is not None
            and relative.endswith(".json")
            and schema_id not in allowed_schema_ids
        ):
            raise BuildFailure(
                f"artifact {relative} cannot claim role {role} with schema_id {schema_id!r}"
            )

        binding: dict[str, Any] = {
            "artifact_id": artifact_id,
            "path": relative,
            "sha256": sha256_bytes(raw),
        }
        if schema_id is not None:
            binding["schema_id"] = schema_id
        binding["version"] = version
        artifacts.append(
            {
                "role": role,
                "media_type": media_type_for(relative),
                "digest_algorithm": "sha256",
                "artifact": binding,
            }
        )

    return {
        "schema_id": "https://schemas.reiyah.invalid/gate-a/1.1.0/gate-a-index.schema.json",
        "schema_version": "1.1.0",
        "artifact_id": "reiyah.artifact.gate-a-index-1.1.0",
        "index_id": "reiyah.gate-a-evidence-index",
        "version": "1.1.0",
        "as_of_date": "2026-08-23",
        "lifecycle_status": "proposed",
        "architecture_status": "architecture_complete",
        "operator_acceptance_state": "unaccepted",
        "operator_decision_binding": None,
        "mission_release_id": "reiyah.mission@1.1.0",
        "protocol_release_id": "reiyah.protocol.harbor-gate-a@1.1.0",
        "distribution_profile": "public_open_source",
        "source_ledger_version": "1.1.0",
        "prior_candidate_observation": {
            "artifact_id": "reiyah.artifact.gate-a-index-1.0.0",
            "version": "1.0.0",
            "sha256": "sha256:3341696a730d2c4a4788f19612fc547eff926715b321e6d6bea99e2850c11944",
            "observed_on": "2026-08-22",
            "distribution_state": "internal_candidate_not_published",
            "evidence_eligible": False,
        },
        "artifacts": artifacts,
        "exclusions": list(EXCLUSIONS),
        "validation_profile": {
            "entrypoint": "tools/validate_gate_a.py",
            "offline_required": True,
            "deterministic_required": True,
            "fail_closed_required": True,
        },
        "known_good_expectation": "all_pass",
        "known_bad_expectation": "all_fail_for_declared_reason",
        "runtime_authorized": False,
    }


def verify_identity() -> None:
    cwd = Path.cwd().resolve()
    script_root = Path(__file__).resolve().parent.parent
    if cwd != CANONICAL_ROOT or script_root != CANONICAL_ROOT:
        raise BuildFailure(
            f"identity gate mismatch: cwd={cwd}, script_root={script_root}, expected={CANONICAL_ROOT}"
        )
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=CANONICAL_ROOT,
            check=False,
            capture_output=True,
            text=True,
            env={"LC_ALL": "C", "PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin"},
        )
    except OSError as exc:
        raise BuildFailure(f"cannot resolve Git root: {exc}") from exc
    git_root = completed.stdout.strip()
    if completed.returncode != 0 or git_root != str(CANONICAL_ROOT):
        raise BuildFailure(
            f"identity gate mismatch: Git root={git_root!r}, expected={CANONICAL_ROOT}"
        )


def canonical_index_bytes(index: dict[str, Any]) -> bytes:
    return (json.dumps(index, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sidecar",
        action="store_true",
        help="emit the canonical SHA-256 sidecar line instead of the index JSON",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        verify_identity()
        index = build_index(CANONICAL_ROOT)
        raw = canonical_index_bytes(index)
    except (BuildFailure, OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Gate A index build refused: {exc}", file=sys.stderr)
        return 2
    if args.sidecar:
        sys.stdout.write(f"{sha256_bytes(raw)}  {INDEX_PATH}\n")
    else:
        sys.stdout.buffer.write(raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
