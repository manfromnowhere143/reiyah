#!/usr/bin/env python3
# Copyright 2026 Daniel Wahnich
# SPDX-License-Identifier: Apache-2.0
"""Deterministic, read-only, offline validation for the Reiyah Gate A packet."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote

sys.dont_write_bytecode = True

try:
    from jsonschema import Draft202012Validator, FormatChecker
    from referencing import Registry, Resource
except ImportError as dependency_import_error:  # pragma: no cover - exercised by missing-toolchain environments
    Draft202012Validator = None  # type: ignore[assignment]
    FormatChecker = None  # type: ignore[assignment]
    Registry = None  # type: ignore[assignment]
    Resource = None  # type: ignore[assignment]
    DEPENDENCY_IMPORT_ERROR: Exception | None = dependency_import_error
else:
    DEPENDENCY_IMPORT_ERROR = None


CANONICAL_ROOT = Path("/Users/danielwahnich/workspace/reiyah")
SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"
PLAN_PATH = "validation/validation-plan.json"
CATALOG_PATH = "fixtures/fixture-catalog.json"
INDEX_PATH = "gate/GATE_A_EVIDENCE_INDEX.json"
SIDECAR_PATH = "gate/GATE_A_EVIDENCE_INDEX.sha256"
LEGACY_TEMPLATE_PATH = "gate/decisions/OPERATOR_DECISION.template.json"
V111_TEMPLATE_PATH = "gate/decisions/OPERATOR_DECISION-1.1.1.template.json"
TEMPLATE_PATH = "gate/decisions/OPERATOR_DECISION-1.1.2.template.json"
ACTUAL_DECISION_PREFIX = "reiyah.gate-a-decision-"
REPORT_PATH = "gate/validation-reports/gate-a-validation-1.1.2.json"
HISTORICAL_V11_REPORT_PATH = "gate/validation-reports/gate-a-validation-1.1.0.json"
HISTORICAL_V111_REPORT_PATH = "gate/validation-reports/gate-a-validation-1.1.1.json"
ACTIVE_SOURCE_LEDGER_PATH = "evidence/source-ledger-1.1.0.json"
ACTIVE_STANDARDS_CROSSWALK_PATH = "evidence/standards-crosswalk-1.1.0.json"
PUBLIC_DISTRIBUTION_INVENTORY_PATH = "evidence/public-distribution-inventory-1.1.0.json"
PUBLIC_CUSTODY_PROFILE_PATH = "evidence/public-evidence-custody-profile-1.1.0.json"
FRONTIER_DISCOVERY_REGISTER_PATH = "evidence/frontier-discovery-register-1.1.0.json"
PUBLIC_RIGHTS_REVALIDATION_PATH = "evidence/public-rights-revalidation-2026-08-23.json"
SUCCESSOR_PUBLIC_RIGHTS_REVALIDATION_PATH = "evidence/public-rights-revalidation-2026-08-24.json"
SUCCESSOR_PUBLIC_RIGHTS_REVALIDATION_DIGEST = "sha256:eb8c31af34d4068a5d63dbd0dac2f4a27600ca5c027a36ee73abed9d8fee9c20"
SUCCESSOR_PUBLIC_RIGHTS_REVALIDATION_SIZE = 4955
CURRENT_PUBLIC_RIGHTS_REVALIDATION_PATH = "evidence/public-rights-revalidation-2026-08-24-1.1.2.json"
HISTORICAL_RECOVERY_PATH = "history/gate-a-1.0.0/RECOVERY.json"
HISTORICAL_INDEX_PATH = "history/gate-a-1.0.0/gate/GATE_A_EVIDENCE_INDEX.json"
HISTORICAL_SIDECAR_PATH = "history/gate-a-1.0.0/gate/GATE_A_EVIDENCE_INDEX.sha256"
HISTORICAL_V11_INDEX_PATH = "history/gate-a-1.1.0/gate/GATE_A_EVIDENCE_INDEX.json"
HISTORICAL_V11_SIDECAR_PATH = "history/gate-a-1.1.0/gate/GATE_A_EVIDENCE_INDEX.sha256"
HISTORICAL_V11_INDEX_DIGEST = "sha256:91149ec8bfc9a3999ce95d8c18ce0d558cf974b0afb412a7ac11027c63056c7a"
HISTORICAL_V11_REPORT_DIGEST = "sha256:89d96c947f909782c0a5ccc4f677114a8a2c9dd2f24e6a342a667f6526144db0"
HISTORICAL_V111_INDEX_PATH = "history/gate-a-1.1.1/gate/GATE_A_EVIDENCE_INDEX.json"
HISTORICAL_V111_SIDECAR_PATH = "history/gate-a-1.1.1/gate/GATE_A_EVIDENCE_INDEX.sha256"
HISTORICAL_V111_INDEX_DIGEST = "sha256:308f65ba2693c13fa71d081dad3f74f56ec80617e97497a2606c0d88a07b2ceb"
HISTORICAL_V111_REPORT_DIGEST = "sha256:76c0dcce583beb02b121776e14bc9df41833a26c5c49488270d96861b3e33806"
PUBLIC_RECEIPT_PREFIX = "gate/public-distribution-receipts/reiyah.public-distribution-receipt-"
INITIAL_PUBLIC_RECEIPT_PATH = "gate/public-distribution-receipts/reiyah.public-distribution-receipt-1.1.0.json"
INITIAL_PUBLIC_RECEIPT_DIGEST = "sha256:d805ad1bab46e087338fb3c7ac049f9c1e9edbbd782fa6960db1f8e3eca57139"
SUCCESSOR_PUBLIC_RECEIPT_PATH = "gate/public-distribution-receipts/reiyah.public-distribution-receipt-1.1.1.json"
SUCCESSOR_PUBLIC_RECEIPT_DIGEST = "sha256:6156a35d3dfb2c4f0d46cbf48845867da6c942b69ed734a4056ae1e36910aa11"
SUCCESSOR_PUBLIC_RECEIPT_SIZE = 7565
SCIENTIFIC_CONTRACT_PROFILE_PATH = "manifests/scientific/harbor-scientific-contract-profile-1.1.0.json"
V11_PROTOCOL_RELEASE_ID = "reiyah.protocol.harbor-gate-a@1.1.0"
V11_MISSION_RELEASE_ID = "reiyah.mission@1.1.0"
DECISION_PACKET_SPECS: dict[str, dict[str, str]] = {
    "1.1.1": {
        "schema_path": "schemas/operator-decision-record-1.1.1.schema.json",
        "template_path": V111_TEMPLATE_PATH,
        "index_artifact_id": "reiyah.artifact.gate-a-index-1.1.1",
        "index_schema_id": "https://schemas.reiyah.invalid/gate-a/1.1.1/gate-a-index.schema.json",
        "index_physical_path": HISTORICAL_V111_INDEX_PATH,
        "index_sha256": HISTORICAL_V111_INDEX_DIGEST,
        "report_artifact_id": "reiyah.validation-report.gate-a-1.1.1",
        "report_schema_id": "https://schemas.reiyah.invalid/gate-a/1.1.1/validation-report.schema.json",
        "report_path": HISTORICAL_V111_REPORT_PATH,
        "report_sha256": HISTORICAL_V111_REPORT_DIGEST,
    },
    "1.1.2": {
        "schema_path": "schemas/operator-decision-record-1.1.2.schema.json",
        "template_path": TEMPLATE_PATH,
        "index_artifact_id": "reiyah.artifact.gate-a-index-1.1.2",
        "index_schema_id": "https://schemas.reiyah.invalid/gate-a/1.1.2/gate-a-index.schema.json",
        "index_physical_path": INDEX_PATH,
        "index_sha256": "",
        "report_artifact_id": "reiyah.validation-report.gate-a-1.1.2",
        "report_schema_id": "https://schemas.reiyah.invalid/gate-a/1.1.2/validation-report.schema.json",
        "report_path": REPORT_PATH,
        "report_sha256": "",
    },
}
V11_MUTATION_SCHEMA_ID = "https://schemas.reiyah.invalid/scientific-contract/1.1.0/scientific-contract-mutation-fixture.schema.json"
V11_APPLICATION_RULES = {
    "https://schemas.reiyah.invalid/scientific-contract/1.1.0/human-automation-assessment.schema.json": "GA-HUMAN-AUTOMATION-CONTRACT",
    "https://schemas.reiyah.invalid/scientific-contract/1.1.0/joint-performance-evaluation.schema.json": "GA-JOINT-PERFORMANCE-CONTRACT",
    "https://schemas.reiyah.invalid/scientific-contract/1.1.0/study-design-preregistration.schema.json": "GA-STUDY-DESIGN-CONTRACT",
    "https://schemas.reiyah.invalid/scientific-contract/1.1.0/sequential-off-policy-evaluation.schema.json": "GA-SEQUENTIAL-OPE-CONTRACT",
    "https://schemas.reiyah.invalid/scientific-contract/1.1.0/evaluation-assurance-bundle.schema.json": "GA-EVALUATION-ASSURANCE-CONTRACT",
}
V11_PUBLIC_PAYLOAD_SOURCE_IDS = frozenset(
    {
        "src.iso.26262-1.2018.open-data",
        "src.iso.21448.2022.open-data",
        "src.iso-tr.21959-1.2020.open-data",
        "src.iso-pas.8800.2024.open-data",
    }
)
V11_POINTER_SOURCE_IDS = frozenset(
    {
        "src.nist.ai-100-1.2023.pdf",
        "src.nist.ai-100-1.2023.publication-page",
        "src.unece.r157.rev1.2025.documentation",
        "src.unece.wp29.2022-59-rev1.authentic-text",
    }
)

SCIENTIFIC_SCHEMA_IDS = frozenset(
    {
        "https://schemas.reiyah.invalid/gate-a/1.0.0/observation.schema.json",
        "https://schemas.reiyah.invalid/gate-a/1.0.0/latent-belief.schema.json",
        "https://schemas.reiyah.invalid/gate-a/1.0.0/decision.schema.json",
        "https://schemas.reiyah.invalid/gate-a/1.0.0/intervention.schema.json",
        "https://schemas.reiyah.invalid/gate-a/1.0.0/outcome.schema.json",
        "https://schemas.reiyah.invalid/gate-a/1.0.0/evidence-object.schema.json",
        "https://schemas.reiyah.invalid/gate-a/1.0.0/experiment.schema.json",
        "https://schemas.reiyah.invalid/gate-a/1.0.0/result.schema.json",
        "https://schemas.reiyah.invalid/gate-a/1.0.0/claim-register.schema.json",
    }
)
OBJECT_SCHEMA_IDS = frozenset(
    schema_id
    for schema_id in SCIENTIFIC_SCHEMA_IDS
    if schema_id.rsplit("/", 1)[-1]
    in {
        "observation.schema.json",
        "latent-belief.schema.json",
        "decision.schema.json",
        "intervention.schema.json",
        "outcome.schema.json",
        "evidence-object.schema.json",
    }
)
EXPERIMENT_SCHEMA_ID = "https://schemas.reiyah.invalid/gate-a/1.0.0/experiment.schema.json"
RESULT_SCHEMA_ID = "https://schemas.reiyah.invalid/gate-a/1.0.0/result.schema.json"
CLAIM_REGISTER_SCHEMA_ID = "https://schemas.reiyah.invalid/gate-a/1.0.0/claim-register.schema.json"
PROTOCOL_MANIFEST_SCHEMA_ID = "https://schemas.reiyah.invalid/gate-a/1.0.0/protocol-manifest.schema.json"
PROTOCOL_MANIFEST_SCHEMA_IDS = frozenset(
    {
        PROTOCOL_MANIFEST_SCHEMA_ID,
        "https://schemas.reiyah.invalid/gate-a/1.1.0/protocol-manifest.schema.json",
    }
)
PROTOCOL_DEFINITION_REGISTRY_SCHEMA_ID = (
    "https://schemas.reiyah.invalid/gate-a/1.0.0/protocol-definition-registry.schema.json"
)
PROTOCOL_DEFINITION_REGISTRY_SCHEMA_IDS = frozenset(
    {
        PROTOCOL_DEFINITION_REGISTRY_SCHEMA_ID,
        "https://schemas.reiyah.invalid/gate-a/1.1.0/protocol-definition-registry.schema.json",
    }
)
PREREGISTRATION_RECORD_SCHEMA_ID = (
    "https://schemas.reiyah.invalid/gate-a/1.0.0/preregistration-record.schema.json"
)
ANALYSIS_SPECIFICATION_SCHEMA_ID = (
    "https://schemas.reiyah.invalid/gate-a/1.0.0/analysis-specification.schema.json"
)
FROZEN_SOURCE_IDENTITIES: dict[str, dict[str, Any]] = {
    "src.iso.26262-1.2018.open-data": {
        "retained_path": "evidence/sources/iso-open-data-68383-20260819.jsonl",
        "sha256": "sha256:305ca3de040b5d216fc5ae9a79100ac2aaab470b41b0b2e6a0a32d653be04e1d",
        "title": "ISO 26262-1:2018 Road vehicles — Functional safety — Part 1: Vocabulary",
        "publisher": {"state": "observed", "value": "International Organization for Standardization (ISO)"},
        "document_identifier": {"state": "observed", "value": "ISO 26262-1:2018"},
        "exact_version": {"state": "observed", "value": "ISO 26262-1:2018, edition 2"},
        "publication_date": {"state": "observed", "value": "2018-12-17"},
    },
    "src.iso.21448.2022.open-data": {
        "retained_path": "evidence/sources/iso-open-data-77490-20260819.jsonl",
        "sha256": "sha256:4c172bebc38e108d7b9568dcea8eb1a13252cd13f5e48cf46a9e18e4a12fbb86",
        "title": "ISO 21448:2022 Road vehicles — Safety of the intended functionality",
        "publisher": {"state": "observed", "value": "International Organization for Standardization (ISO)"},
        "document_identifier": {"state": "observed", "value": "ISO 21448:2022"},
        "exact_version": {"state": "observed", "value": "ISO 21448:2022, edition 1"},
        "publication_date": {"state": "observed", "value": "2022-06-30"},
    },
    "src.iso-tr.21959-1.2020.open-data": {
        "retained_path": "evidence/sources/iso-open-data-78088-20260819.jsonl",
        "sha256": "sha256:b92adcf7a8203d4e141057163c2d42b7bc79686542255d4a81962116326db223",
        "title": "ISO/TR 21959-1:2020 Road vehicles — Human performance and state in the context of automated driving — Part 1: Common underlying concepts",
        "publisher": {"state": "observed", "value": "International Organization for Standardization (ISO)"},
        "document_identifier": {"state": "observed", "value": "ISO/TR 21959-1:2020"},
        "exact_version": {"state": "observed", "value": "ISO/TR 21959-1:2020, edition 2"},
        "publication_date": {"state": "observed", "value": "2020-01-09"},
    },
    "src.iso-pas.8800.2024.open-data": {
        "retained_path": "evidence/sources/iso-open-data-83303-20260819.jsonl",
        "sha256": "sha256:55b96ac98610215c67189fb758be9aba9224d9409dfdb09dad0ed0aeb03e5d45",
        "title": "ISO/PAS 8800:2024 Road vehicles — Safety and artificial intelligence",
        "publisher": {"state": "observed", "value": "International Organization for Standardization (ISO)"},
        "document_identifier": {"state": "observed", "value": "ISO/PAS 8800:2024"},
        "exact_version": {"state": "observed", "value": "ISO/PAS 8800:2024, edition 1"},
        "publication_date": {"state": "observed", "value": "2024-12-13"},
    },
    "src.nist.ai-100-1.2023.publication-page": {
        "retained_path": "evidence/sources/nist-ai-rmf-1.0-publication-page-20260822.html",
        "sha256": "sha256:d0dc9896118eef5dbd8feb7be09fd43fd3882b80df47afa8f7031dc2ae4f0e47",
        "title": "Artificial Intelligence Risk Management Framework (AI RMF 1.0)",
        "publisher": {"state": "observed", "value": "National Institute of Standards and Technology (NIST)"},
        "document_identifier": {"state": "observed", "value": "NIST AI 100-1"},
        "exact_version": {"state": "observed", "value": "AI RMF 1.0"},
        "publication_date": {"state": "observed", "value": "2023-01-26"},
    },
    "src.nist.ai-100-1.2023.pdf": {
        "retained_path": "evidence/sources/nist-ai-100-1-2023.pdf",
        "sha256": "sha256:7576edb531d9848825814ee88e28b1795d3a84b435b4b797d3670eafdc4a89f1",
        "title": "Artificial Intelligence Risk Management Framework (AI RMF 1.0)",
        "publisher": {"state": "observed", "value": "National Institute of Standards and Technology (NIST)"},
        "document_identifier": {"state": "observed", "value": "NIST AI 100-1"},
        "exact_version": {"state": "observed", "value": "AI RMF 1.0"},
        "publication_date": {"state": "observed", "value": "2023-01-26"},
    },
    "src.unece.r157.rev1.2025.documentation": {
        "retained_path": "evidence/sources/unece-r157-rev1-2025.pdf",
        "sha256": "sha256:552b579225f98f66d97019d5712fe8ea26bb5e369943c34328c46537a1de537c",
        "title": "Addendum 156 — UN Regulation No. 157, Revision 1, 01 series of amendments",
        "publisher": {"state": "observed", "value": "United Nations Economic Commission for Europe (UNECE)"},
        "document_identifier": {"state": "observed", "value": "E/ECE/TRANS/505/Rev.3/Add.156/Rev.1"},
        "exact_version": {"state": "observed", "value": "E/ECE/TRANS/505/Rev.3/Add.156/Rev.1"},
        "publication_date": {"state": "observed", "value": "2025-03-27"},
    },
    "src.unece.wp29.2022-59-rev1.authentic-text": {
        "retained_path": "evidence/sources/unece-wp29-2022-59-rev1.pdf",
        "sha256": "sha256:ff2a05d9cdb6501dbe4d4b730a5457efadc5724f6b5d2dc7f3bc194472743a23",
        "title": "Proposal for the 01 series of amendments to UN Regulation No. 157 (Automated Lane Keeping Systems), Revision 1",
        "publisher": {"state": "observed", "value": "United Nations Economic Commission for Europe (UNECE)"},
        "document_identifier": {"state": "observed", "value": "ECE/TRANS/WP.29/2022/59/Rev.1"},
        "exact_version": {"state": "observed", "value": "ECE/TRANS/WP.29/2022/59/Rev.1"},
        "publication_date": {"state": "observed", "value": "2022-05-30"},
    },
}
SCHEMA_OBJECT_KINDS = {
    "https://schemas.reiyah.invalid/gate-a/1.0.0/observation.schema.json": "observation",
    "https://schemas.reiyah.invalid/gate-a/1.0.0/latent-belief.schema.json": "latent_belief",
    "https://schemas.reiyah.invalid/gate-a/1.0.0/decision.schema.json": "decision",
    "https://schemas.reiyah.invalid/gate-a/1.0.0/intervention.schema.json": "intervention",
    "https://schemas.reiyah.invalid/gate-a/1.0.0/outcome.schema.json": "outcome",
    "https://schemas.reiyah.invalid/gate-a/1.0.0/evidence-object.schema.json": "evidence",
}

CONTROL_EVIDENCE: dict[str, tuple[str, ...]] = {
    "GA-01": ("AGENTS.md", "docs/SESSION_HANDOFF.md"),
    "GA-02": ("docs/SCIENTIFIC_CHARTER.md", "manifests/mission/reiyah-mission-1.1.0.json"),
    "GA-03": ("docs/CLAIMS_AND_NON_CLAIMS.md", "manifests/claims/proposed-claims-and-non-claims-1.0.0.json"),
    "GA-04": ("docs/MATHEMATICAL_SPECIFICATION.md", "docs/ARCHITECTURE.md", "schemas/common-1.1.schema.json"),
    "GA-05": ("docs/STATUS_MODEL.md", "schemas/common.schema.json", CATALOG_PATH),
    "GA-06": ("docs/STATUS_MODEL.md", "schemas/common.schema.json", CATALOG_PATH),
    "GA-07": ("docs/MATHEMATICAL_SPECIFICATION.md", "manifests/protocol/harbor-gate-a-protocol-1.1.0.json"),
    "GA-08": ("docs/SCIENTIFIC_CHARTER.md", "docs/MATHEMATICAL_SPECIFICATION.md"),
    "GA-09": ("manifests/manifest-release-ledger.json",),
    "GA-10": ("docs/SOURCE_POLICY.md", ACTIVE_SOURCE_LEDGER_PATH, "evidence/public-evidence-custody-profile-1.1.0.json"),
    "GA-11": ("docs/STANDARDS_CROSSWALK.md", ACTIVE_STANDARDS_CROSSWALK_PATH),
    "GA-12": ("docs/THREAT_MODEL.md",),
    "GA-13": ("schemas/common.schema.json", CATALOG_PATH),
    "GA-14": ("tools/validate_gate_a.py", PLAN_PATH, CATALOG_PATH),
    "GA-15": ("docs/ARCHITECTURE.md", "tools/validate_gate_a.py"),
    "GA-16": (INDEX_PATH, SIDECAR_PATH),
}
REQUIRED_CONTROL_IDS = tuple(f"GA-{number:02d}" for number in range(1, 17))

EXPECTED_KINDS = (
    "observation",
    "latent_belief",
    "decision",
    "intervention",
    "outcome",
    "evidence",
)
EXPECTED_EPISTEMIC_STATES = (
    "observed",
    "missing",
    "unmeasured",
    "out_of_distribution",
    "sensor_invalid",
    "abstained",
)
EXPECTED_LIFECYCLE_STATUSES = (
    "proposed",
    "exploratory",
    "preregistered",
    "running",
    "blocked",
    "invalid",
    "null",
    "inconclusive",
    "failed",
    "supported",
    "contradicted",
    "replicated",
    "corrected",
    "retracted",
)

EPISTEMIC_RULES = {
    "missing": "GA-EPISTEMIC-MISSING-COERCION",
    "unmeasured": "GA-EPISTEMIC-UNMEASURED-COERCION",
    "out_of_distribution": "GA-EPISTEMIC-OOD-COERCION",
    "sensor_invalid": "GA-EPISTEMIC-SENSOR-INVALID-COERCION",
    "abstained": "GA-EPISTEMIC-ABSTAINED-COERCION",
}


class StrictJSONError(ValueError):
    """JSON bytes are ambiguous or outside the finite RFC-compatible data model."""


class DuplicateJSONKeyError(StrictJSONError):
    """A JSON object repeats a member name before dictionary construction."""


class NonFiniteJSONError(StrictJSONError):
    """A JSON number parses to NaN or an infinity."""


def strict_json_loads(data: str | bytes) -> Any:
    def reject_constant(token: str) -> Any:
        raise NonFiniteJSONError(f"non-finite JSON constant {token!r}")

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise DuplicateJSONKeyError(f"duplicate JSON object member {key!r}")
            result[key] = value
        return result

    value = json.loads(data, parse_constant=reject_constant, object_pairs_hook=unique_object)

    def require_finite(item: Any, trail: tuple[Any, ...] = ()) -> None:
        if isinstance(item, float) and not math.isfinite(item):
            raise NonFiniteJSONError(f"non-finite JSON number at {trail!r}")
        if isinstance(item, dict):
            for key, child in item.items():
                require_finite(child, trail + (key,))
        elif isinstance(item, list):
            for index, child in enumerate(item):
                require_finite(child, trail + (index,))

    require_finite(value)
    return value


class ExecutionFailure(RuntimeError):
    """Validation could not execute safely and must exit 2."""

    def __init__(self, message: str, path: str = "tools/validate_gate_a.py") -> None:
        super().__init__(message)
        self.path = path


class IdentityFailure(ExecutionFailure):
    """The repository preflight failed its pure identity-authority diagnostic."""

    def __init__(self, diagnostic: dict[str, Any]) -> None:
        super().__init__(diagnostic["message"], diagnostic["path"])
        self.diagnostic = diagnostic


class RepositoryView:
    """Read-only repository bytes with an optional in-memory mutation overlay."""

    def __init__(self, root: Path, overlay: dict[str, bytes | None] | None = None) -> None:
        self.root = root
        self.overlay = dict(overlay or {})

    @staticmethod
    def validate_relative(relative: str) -> None:
        if (
            not isinstance(relative, str)
            or not relative
            or relative.startswith("/")
            or "\\" in relative
            or any(part in {"", ".", ".."} for part in relative.split("/"))
        ):
            raise ValueError(f"unsafe repository-relative path {relative!r}")

    def absolute(self, relative: str) -> Path:
        self.validate_relative(relative)
        candidate = self.root / relative
        try:
            candidate.parent.resolve().relative_to(self.root)
        except (OSError, ValueError) as exc:
            raise ValueError(f"repository path escapes root: {relative}") from exc
        return candidate

    def read_bytes(self, relative: str) -> bytes:
        self.validate_relative(relative)
        if relative in self.overlay:
            value = self.overlay[relative]
            if value is None:
                raise FileNotFoundError(relative)
            return value
        absolute = self.absolute(relative)
        if absolute.is_symlink():
            raise OSError(f"repository symlink is not readable as bound bytes: {relative}")
        return absolute.read_bytes()

    def read_text(self, relative: str) -> str:
        return self.read_bytes(relative).decode("utf-8")

    def read_json(self, relative: str) -> Any:
        return strict_json_loads(self.read_text(relative))

    def is_file(self, relative: str) -> bool:
        self.validate_relative(relative)
        if relative in self.overlay:
            return self.overlay[relative] is not None
        candidate = self.absolute(relative)
        return candidate.is_file() or candidate.is_symlink()

    def is_symlink(self, relative: str) -> bool:
        self.validate_relative(relative)
        if relative in self.overlay:
            return False
        return self.absolute(relative).is_symlink()

    def iter_files(self) -> list[str]:
        paths: set[str] = set()
        for candidate in self.root.rglob("*"):
            if candidate.is_file() or candidate.is_symlink():
                paths.add(candidate.relative_to(self.root).as_posix())
        for relative, value in self.overlay.items():
            self.validate_relative(relative)
            if value is None:
                paths.discard(relative)
            else:
                paths.add(relative)
        return sorted(paths)


def canonical_json_bytes(data: Any) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def parse_exact_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not re.fullmatch(
        r"[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])T"
        r"(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](?:\.[0-9]+)?Z",
        value,
    ):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    return parsed if parsed.tzinfo == timezone.utc else None


def identity_authority_diagnostics(
    context: dict[str, Any],
    path: str = "AGENTS.md",
    object_id: str | None = None,
) -> list[dict[str, Any]]:
    expected = ("Reiyah", str(CANONICAL_ROOT), str(CANONICAL_ROOT), "Reiyah")
    actual = (
        context.get("named_project"),
        context.get("working_directory"),
        context.get("git_root"),
        context.get("instruction_project"),
    )
    script_root = context.get("script_root", str(CANONICAL_ROOT))
    if actual == expected and script_root == str(CANONICAL_ROOT):
        return []
    return [
        make_diagnostic(
            "GA-IDENTITY-AUTHORITY-MISMATCH",
            path,
            "Project, working directory, Git root, validator root, and instruction authority do not all identify canonical Reiyah.",
            object_id,
        )
    ]


def decode_pointer(pointer: str) -> list[str]:
    if pointer == "":
        return []
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError(f"invalid RFC 6901 JSON pointer {pointer!r}")
    return [token.replace("~1", "/").replace("~0", "~") for token in pointer[1:].split("/")]


def mutate_json(document: Any, operation: str, pointer: str, value: Any = None) -> Any:
    """Apply one deterministic add/replace/remove mutation to an in-memory JSON value."""

    # A JSON round trip avoids sharing mutable fixture structures with cached production data.
    result = strict_json_loads(json.dumps(document, ensure_ascii=False, allow_nan=False))
    tokens = decode_pointer(pointer)
    if not tokens:
        if operation == "remove":
            raise ValueError("cannot remove an entire JSON document with a JSON pointer")
        return value
    parent = result
    for token in tokens[:-1]:
        if isinstance(parent, list):
            if not token.isdigit() or int(token) >= len(parent):
                raise ValueError(f"JSON pointer array token does not resolve: {token}")
            parent = parent[int(token)]
        elif isinstance(parent, dict) and token in parent:
            parent = parent[token]
        else:
            raise ValueError(f"JSON pointer token does not resolve: {token}")
    final = tokens[-1]
    if isinstance(parent, list):
        if operation == "add" and final == "-":
            parent.append(value)
        elif final.isdigit() and int(final) < len(parent):
            if operation == "remove":
                parent.pop(int(final))
            elif operation == "replace":
                parent[int(final)] = value
            elif operation == "add":
                parent.insert(int(final), value)
            else:
                raise ValueError(f"unsupported JSON mutation operation {operation!r}")
        else:
            raise ValueError(f"JSON pointer array token does not resolve: {final}")
    elif isinstance(parent, dict):
        if operation == "remove":
            if final not in parent:
                raise ValueError(f"cannot remove absent JSON member {final!r}")
            del parent[final]
        elif operation == "replace":
            if final not in parent:
                raise ValueError(f"cannot replace absent JSON member {final!r}")
            parent[final] = value
        elif operation == "add":
            parent[final] = value
        else:
            raise ValueError(f"unsupported JSON mutation operation {operation!r}")
    else:
        raise ValueError("JSON pointer parent is not a container")
    return result


def digest_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def json_pointer(parts: Iterable[Any]) -> str:
    encoded = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(encoded) if encoded else "/"


def object_identifier(data: Any) -> str | None:
    if not isinstance(data, dict):
        return None
    for key in (
        "fixture_id",
        "object_id",
        "result_id",
        "experiment_id",
        "source_id",
        "mapping_id",
        "release_id",
        "record_id",
        "artifact_id",
    ):
        value = data.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def make_diagnostic(
    rule_id: str,
    path: str,
    message: str,
    object_id: str | None = None,
) -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "severity": "error",
        "path": path,
        "object_id": object_id,
        "message": message,
    }


def diagnostic_key(item: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(item["rule_id"]),
        str(item["path"]),
        "" if item["object_id"] is None else str(item["object_id"]),
        str(item["message"]),
    )


def toolchain_provenance() -> dict[str, str]:
    def installed(distribution: str) -> str:
        try:
            return package_version(distribution)
        except PackageNotFoundError:
            return "not-installed"

    return {
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "jsonschema_version": installed("jsonschema"),
        "referencing_version": installed("referencing"),
        "schema_dialect": SCHEMA_DIALECT,
    }


def empty_fixture_summary() -> dict[str, Any]:
    return {
        "catalog_id": "reiyah.fixture-catalog.gate-a",
        "total": 0,
        "known_good_total": 0,
        "known_good_passed": 0,
        "known_bad_total": 0,
        "known_bad_rejected_for_declared_rule": 0,
        "unexpected_outcomes": 0,
    }


def empty_check_summary() -> dict[str, int]:
    return {
        "schemas_checked": 0,
        "normative_instances_checked": 0,
        "fixture_cases_checked": 0,
        "retained_sources_checked": 0,
        "indexed_artifacts_checked": 0,
        "v11_required_properties_exercised": 0,
        "v11_required_mutations_rejected": 0,
    }


def empty_control_summary() -> dict[str, Any]:
    return {
        "required_control_ids": list(REQUIRED_CONTROL_IDS),
        "covered_control_ids": [],
        "passed_control_ids": [],
        "failed_control_ids": list(REQUIRED_CONTROL_IDS),
        "external_control_summary": {
            "control_id": "GA-17",
            "status": "not_evaluated",
            "decision_record_id": None,
            "diagnostics": [],
        },
    }


def build_report(
    *,
    mode: str,
    result: str,
    exit_code: int,
    architecture_status: str,
    index_binding: dict[str, str] | None,
    diagnostics: list[dict[str, Any]],
    fixture_summary: dict[str, Any],
    check_summary: dict[str, int],
    control_summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_id": "https://schemas.reiyah.invalid/gate-a/1.1.2/validation-report.schema.json",
        "schema_version": "1.1.2",
        "artifact_id": "reiyah.validation-report.gate-a-1.1.2",
        "report_id": "reiyah.validation-report.gate-a",
        "version": "1.1.2",
        "validation_plan_id": "reiyah.validation-plan.gate-a-public-1.1.2",
        "mission_release_id": V11_MISSION_RELEASE_ID,
        "protocol_release_id": V11_PROTOCOL_RELEASE_ID,
        "distribution_profile": "public_open_source",
        "source_ledger_version": "1.1.0",
        "mode": mode,
        "result": result,
        "exit_code": exit_code,
        "architecture_status": architecture_status,
        "index_binding": index_binding,
        "offline": True,
        "read_only": True,
        "runtime_authorized": False,
        "acceptance_created": False,
        "diagnostic_sort": ["rule_id", "path", "object_id", "message"],
        "diagnostics": sorted(diagnostics, key=diagnostic_key),
        "fixture_summary": fixture_summary,
        "check_summary": check_summary,
        "control_summary": control_summary,
        "toolchain": toolchain_provenance(),
    }


class GateAValidator:
    def __init__(self, root: Path, fixture_only: bool) -> None:
        self.root = root
        self.view = RepositoryView(root)
        self.fixture_only = fixture_only
        self.diagnostics: list[dict[str, Any]] = []
        self.schemas: dict[str, dict[str, Any]] = {}
        self.schema_paths: dict[str, str] = {}
        self.registry: Any = None
        self.format_checker: Any = None
        self.plan: dict[str, Any] = {}
        self.catalog: dict[str, Any] = {}
        self.fixture_summary = empty_fixture_summary()
        self.check_summary = empty_check_summary()
        self.index_binding: dict[str, str] | None = None
        self.covered_control_ids: set[str] = set()
        self._json_cache: dict[str, Any] = {}

    def add(
        self,
        rule_id: str,
        path: str,
        message: str,
        object_id: str | None = None,
    ) -> None:
        self.diagnostics.append(make_diagnostic(rule_id, path, message, object_id))

    def absolute(self, relative: str) -> Path:
        if not isinstance(relative, str) or not relative:
            raise ExecutionFailure("artifact path is absent or not a string")
        candidate = self.root / relative
        try:
            resolved_parent = candidate.parent.resolve()
            resolved_parent.relative_to(self.root)
        except (OSError, ValueError) as exc:
            raise ExecutionFailure(f"artifact path escapes Reiyah root: {relative}") from exc
        return candidate

    def read_json_execution(self, relative: str) -> Any:
        if relative in self._json_cache:
            return self._json_cache[relative]
        path = self.absolute(relative)
        if path.is_symlink():
            raise ExecutionFailure(f"required validator input is a forbidden symlink: {relative}", relative)
        try:
            data = strict_json_loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ExecutionFailure(f"required validator input is missing: {relative}", relative) from exc
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, StrictJSONError) as exc:
            raise ExecutionFailure(f"cannot parse required validator input {relative}: {exc}", relative) from exc
        self._json_cache[relative] = data
        return data

    def read_json_contract(self, relative: str) -> Any | None:
        if relative in self._json_cache:
            return self._json_cache[relative]
        path = self.absolute(relative)
        if path.is_symlink():
            self.add("GA-ARTIFACT-SYMLINK", relative, "Normative JSON artifact must not be a symlink.")
            return None
        try:
            data = strict_json_loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            self.add("GA-REQUIRED-ARTIFACT-MISSING", relative, "Required JSON artifact is missing.")
            return None
        except DuplicateJSONKeyError as exc:
            self.add("GA-JSON-DUPLICATE-KEY", relative, f"JSON object member names must be unique before parsing: {exc}")
            return None
        except NonFiniteJSONError as exc:
            self.add("GA-NONFINITE-NUMBER", relative, f"JSON numbers must be finite: {exc}")
            return None
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            self.add("GA-JSON-MALFORMED", relative, f"JSON cannot be parsed: {exc}")
            return None
        self._json_cache[relative] = data
        return data

    def read_view_json(self, view: RepositoryView, relative: str) -> Any | None:
        try:
            return view.read_json(relative)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            return None

    def mutation_view(self, mutations: Any) -> RepositoryView:
        if not isinstance(mutations, list):
            raise ValueError("production mutations must be an array")
        overlay: dict[str, bytes | None] = {}
        view = RepositoryView(self.root, overlay)
        for mutation in mutations:
            if not isinstance(mutation, dict):
                raise ValueError("production mutation must be an object")
            operation = mutation.get("operation")
            relative = mutation.get("path")
            if not isinstance(relative, str):
                raise ValueError("production mutation path is absent")
            RepositoryView.validate_relative(relative)
            if operation == "add_file":
                content = mutation.get("content_utf8")
                if not isinstance(content, str):
                    raise ValueError("add_file requires content_utf8")
                overlay[relative] = content.encode("utf-8")
            elif operation == "remove" and "json_pointer" not in mutation:
                overlay[relative] = None
            elif operation in {"add", "replace", "remove"}:
                pointer = mutation.get("json_pointer")
                if not isinstance(pointer, str):
                    raise ValueError(f"{operation} requires json_pointer")
                current_view = RepositoryView(self.root, overlay)
                canonical_report_path = REPORT_PATH
                if relative == canonical_report_path and relative not in overlay:
                    # Shell redirection truncates its destination before this process starts.
                    # The report-coverage mutation must therefore be derived solely from the
                    # current in-memory architecture report, never from retained output bytes.
                    document = self.canonical_architecture_report()
                else:
                    document = current_view.read_json(relative)
                changed = mutate_json(document, operation, pointer, mutation.get("value"))
                overlay[relative] = canonical_json_bytes(changed)
            else:
                raise ValueError(f"unsupported production mutation operation {operation!r}")
            view = RepositoryView(self.root, overlay)
        return view

    def validate_schema_definitions(self) -> None:
        schema_files = sorted(
            (self.root / "schemas").rglob("*.schema.json"),
            key=lambda item: item.relative_to(self.root).as_posix(),
        )
        if not schema_files:
            raise ExecutionFailure("no schemas are available", "schemas")
        resources: list[tuple[str, Any]] = []
        for path in schema_files:
            relative = path.relative_to(self.root).as_posix()
            try:
                schema = strict_json_loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, StrictJSONError) as exc:
                raise ExecutionFailure(f"schema cannot be parsed: {exc}", relative) from exc
            if not isinstance(schema, dict):
                raise ExecutionFailure("schema root must be an object", relative)
            schema_id = schema.get("$id")
            if not isinstance(schema_id, str):
                raise ExecutionFailure("schema lacks a string $id", relative)
            if schema.get("$schema") != SCHEMA_DIALECT:
                self.add("GA-SCHEMA-DIALECT", relative, "Schema does not pin Draft 2020-12.", schema_id)
            if schema_id in self.schemas:
                self.add("GA-SCHEMA-ID-DUPLICATE", relative, f"Duplicate schema $id {schema_id}.", schema_id)
            try:
                Draft202012Validator.check_schema(schema)
            except Exception as exc:  # jsonschema exposes multiple schema-error subclasses
                self.add("GA-SCHEMA-DEFINITION", relative, f"Invalid Draft 2020-12 schema: {exc}", schema_id)
            self.schemas[schema_id] = schema
            self.schema_paths[schema_id] = relative
            try:
                resources.append((schema_id, Resource.from_contents(schema)))
            except Exception as exc:
                raise ExecutionFailure(f"schema cannot enter local registry: {exc}", relative) from exc
        try:
            self.registry = Registry().with_resources(resources)
            self.format_checker = FormatChecker()
        except Exception as exc:
            raise ExecutionFailure(f"cannot construct local schema registry: {exc}", "schemas") from exc
        self.check_summary["schemas_checked"] = len(schema_files)

    def instance_diagnostics(self, data: Any, relative: str) -> list[dict[str, Any]]:
        if not isinstance(data, dict):
            return [make_diagnostic("GA-SCHEMA-INSTANCE", relative, "Normative JSON root must be an object.")]
        schema_id = data.get("schema_id")
        if not isinstance(schema_id, str) or schema_id not in self.schemas:
            return [
                make_diagnostic(
                    "GA-SCHEMA-UNKNOWN",
                    relative,
                    f"Unknown or absent schema_id {schema_id!r}.",
                    object_identifier(data),
                )
            ]
        validator = Draft202012Validator(
            self.schemas[schema_id],
            registry=self.registry,
            format_checker=self.format_checker,
        )
        errors = sorted(
            validator.iter_errors(data),
            key=lambda error: (tuple(str(part) for part in error.absolute_path), error.message),
        )
        return [
            make_diagnostic(
                "GA-SCHEMA-INSTANCE",
                relative,
                f"{json_pointer(error.absolute_path)}: {error.message}",
                object_identifier(data),
            )
            for error in errors
        ]

    def validate_instance_global(self, data: Any, relative: str) -> None:
        self.check_summary["normative_instances_checked"] += 1
        self.diagnostics.extend(self.instance_diagnostics(data, relative))

    def load_plan_and_catalog(self) -> None:
        self.plan = self.read_json_execution(PLAN_PATH)
        self.catalog = self.read_json_execution(CATALOG_PATH)
        self.validate_instance_global(self.plan, PLAN_PATH)
        self.validate_instance_global(self.catalog, CATALOG_PATH)

    def check_toolchain(self) -> None:
        lock_path = "validation/requirements.lock"
        path = self.absolute(lock_path)
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            self.add("GA-TOOLCHAIN-LOCK", lock_path, f"Cannot read dependency lock: {exc}")
            return
        locked: dict[str, str] = {}
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.count("==") != 1:
                self.add("GA-TOOLCHAIN-LOCK", lock_path, f"Non-exact dependency entry: {stripped}")
                continue
            name, pinned = stripped.split("==", 1)
            locked[name] = pinned
        expected = {
            "attrs": "26.1.0",
            "jsonschema": "4.26.0",
            "jsonschema-specifications": "2025.9.1",
            "referencing": "0.37.0",
            "rpds-py": "0.30.0",
        }
        if locked != expected:
            self.add("GA-TOOLCHAIN-LOCK", lock_path, "Dependency lock does not equal the frozen Gate A surface.")
        if platform.python_implementation() != "CPython" or platform.python_version() != "3.14.2":
            self.add(
                "GA-TOOLCHAIN-MISMATCH",
                lock_path,
                f"Expected CPython 3.14.2, found {platform.python_implementation()} {platform.python_version()}.",
            )
        for distribution, expected_version in expected.items():
            try:
                actual_version = package_version(distribution)
            except PackageNotFoundError:
                actual_version = "not-installed"
            if actual_version != expected_version:
                self.add(
                    "GA-TOOLCHAIN-MISMATCH",
                    lock_path,
                    f"Expected {distribution} {expected_version}, found {actual_version}.",
                )

    def check_required_artifacts(self) -> None:
        required = self.plan.get("required_artifacts", [])
        if not isinstance(required, list):
            self.add("GA-VALIDATION-PLAN", PLAN_PATH, "required_artifacts must be an array.")
            return
        for relative in sorted(value for value in required if isinstance(value, str)):
            path = self.absolute(relative)
            if not path.is_file():
                self.add("GA-REQUIRED-ARTIFACT-MISSING", relative, "Required Gate A artifact is missing.")
            elif path.is_symlink():
                self.add("GA-ARTIFACT-SYMLINK", relative, "Normative Gate A artifacts must not be symlinks.")

    def check_gate_control_coverage(self) -> None:
        gate_path = "docs/PRE_IMPLEMENTATION_GATE.md"
        try:
            gate_text = self.absolute(gate_path).read_text(encoding="utf-8")
        except OSError as exc:
            self.add("GA-VALIDATION-PLAN", gate_path, f"Cannot read pre-implementation gate: {exc}")
            return
        declared_controls = {
            match.group(1)
            for match in re.finditer(r"^\| (GA-(?:0[1-9]|1[0-7])) \|", gate_text, re.MULTILINE)
        }
        expected_with_external = set(REQUIRED_CONTROL_IDS) | {"GA-17"}
        if declared_controls != expected_with_external:
            self.add(
                "GA-VALIDATION-PLAN",
                gate_path,
                f"Gate control table must be exactly GA-01..GA-17; missing={sorted(expected_with_external - declared_controls)}, extra={sorted(declared_controls - expected_with_external)}.",
            )
        rules = self.plan.get("rules", [])
        plan_controls: set[str] = set()
        plan_rule_ids: set[str] = set()
        if not isinstance(rules, list):
            self.add("GA-VALIDATION-PLAN", PLAN_PATH, "rules must be an array.")
            return
        for rule in rules:
            if not isinstance(rule, dict):
                self.add("GA-VALIDATION-PLAN", PLAN_PATH, "Every validation rule must be an object.")
                continue
            rule_id = rule.get("rule_id")
            controls = rule.get("gate_controls")
            if not isinstance(rule_id, str) or rule_id in plan_rule_ids:
                self.add("GA-VALIDATION-PLAN", PLAN_PATH, f"Validation rule ID is absent or duplicated: {rule_id!r}.")
            elif not isinstance(controls, list) or not controls:
                self.add("GA-VALIDATION-PLAN", PLAN_PATH, f"Validation rule {rule_id} lacks gate-control coverage.", rule_id)
            else:
                plan_rule_ids.add(rule_id)
                plan_controls.update(control for control in controls if isinstance(control, str))
                unknown = set(controls) - expected_with_external
                if unknown:
                    self.add("GA-VALIDATION-PLAN", PLAN_PATH, f"Validation rule {rule_id} references unknown controls {sorted(unknown)}.", rule_id)
        missing_plan_controls = set(REQUIRED_CONTROL_IDS) - plan_controls
        if missing_plan_controls:
            self.add("GA-VALIDATION-PLAN", PLAN_PATH, f"Validation rules do not cover architecture controls {sorted(missing_plan_controls)}.")

        required_artifacts = set(self.plan.get("required_artifacts", [])) if isinstance(self.plan.get("required_artifacts"), list) else set()
        index = self.read_json_contract(INDEX_PATH)
        indexed_paths = {
            item.get("artifact", {}).get("path")
            for item in index.get("artifacts", [])
            if isinstance(index, dict) and isinstance(item, dict) and isinstance(item.get("artifact"), dict)
        } if isinstance(index, dict) else set()
        for control_id in REQUIRED_CONTROL_IDS:
            evidence_paths = CONTROL_EVIDENCE[control_id]
            missing_required = sorted(path for path in evidence_paths if path not in required_artifacts and path not in {INDEX_PATH, SIDECAR_PATH})
            missing_files = sorted(path for path in evidence_paths if not self.absolute(path).is_file())
            missing_indexed = sorted(path for path in evidence_paths if path not in indexed_paths and path not in {INDEX_PATH, SIDECAR_PATH})
            if missing_required or missing_files or missing_indexed:
                self.add(
                    "GA-VALIDATION-PLAN",
                    PLAN_PATH,
                    f"{control_id} lacks required control evidence; not_required={missing_required}, missing={missing_files}, not_indexed={missing_indexed}.",
                    control_id,
                )
            elif control_id in plan_controls:
                self.covered_control_ids.add(control_id)

    def normative_json_paths(self) -> list[str]:
        candidates: set[Path] = set()
        for directory in ("manifests", "fixtures"):
            candidates.update((self.root / directory).rglob("*.json"))
        candidates.update((self.root / "evidence").glob("*.json"))
        candidates.update((self.root / "validation").glob("*.json"))
        index = self.root / INDEX_PATH
        if index.is_file():
            candidates.add(index)
        return sorted(path.relative_to(self.root).as_posix() for path in candidates)

    def validate_normative_instances(self) -> None:
        for relative in self.normative_json_paths():
            data = self.read_json_contract(relative)
            if data is not None:
                self.validate_instance_global(data, relative)
                if isinstance(data, dict) and data.get("schema_id") in V11_APPLICATION_RULES:
                    self.diagnostics.extend(self.v11_application_diagnostics(data, relative))

    def check_operator_template(self) -> None:
        template = self.read_json_contract(TEMPLATE_PATH)
        if not isinstance(template, dict):
            return
        notice = template.get("template_notice")
        if template.get("is_template") is not True or not isinstance(notice, str) or "DELIBERATELY INVALID" not in notice:
            self.add(
                "GA-OPERATOR-TEMPLATE",
                TEMPLATE_PATH,
                "Operator template must declare is_template true and its deliberately invalid notice.",
            )
        errors = self.instance_diagnostics(template, TEMPLATE_PATH)
        if not errors:
            self.add(
                "GA-OPERATOR-TEMPLATE-VALID",
                TEMPLATE_PATH,
                "The non-normative operator template unexpectedly validates as an actual decision.",
            )

    def check_vocabulary_bindings(self) -> None:
        schema_contracts = (
            (
                "https://schemas.reiyah.invalid/gate-a/1.0.0/common.schema.json",
                "schemas/common.schema.json",
                True,
            ),
            (
                "https://schemas.reiyah.invalid/scientific-contract/1.1.0/common.schema.json",
                "schemas/v1.1/scientific-contract-common.schema.json",
                False,
            ),
        )
        for schema_id, schema_path, requires_object_kind in schema_contracts:
            common = self.schemas.get(schema_id, {})
            defs = common.get("$defs", {}) if isinstance(common, dict) else {}
            comparisons: list[tuple[tuple[Any, ...], tuple[str, ...], str]] = [
                (tuple(defs.get("epistemicState", {}).get("enum", [])), EXPECTED_EPISTEMIC_STATES, "epistemic states"),
                (tuple(defs.get("lifecycleStatus", {}).get("enum", [])), EXPECTED_LIFECYCLE_STATUSES, "lifecycle statuses"),
            ]
            if requires_object_kind:
                comparisons.insert(0, (tuple(defs.get("objectKind", {}).get("enum", [])), EXPECTED_KINDS, "object kinds"))
            for actual, expected, label in comparisons:
                if actual != expected:
                    self.add("GA-VOCABULARY-MISMATCH", schema_path, f"Closed {label} do not match the repository contract.")

        for protocol_path in (
            "manifests/protocol/harbor-gate-a-protocol-1.0.0.json",
            "manifests/protocol/harbor-gate-a-protocol-1.1.0.json",
        ):
            protocol = self.read_json_contract(protocol_path)
            if isinstance(protocol, dict):
                if tuple(protocol.get("scientific_layers", [])) != EXPECTED_KINDS:
                    self.add("GA-VOCABULARY-MISMATCH", protocol_path, "Protocol scientific layers do not match the six-kind contract.")
                if tuple(protocol.get("epistemic_states", [])) != EXPECTED_EPISTEMIC_STATES:
                    self.add("GA-VOCABULARY-MISMATCH", protocol_path, "Protocol epistemic states do not match the contract.")
                if tuple(protocol.get("lifecycle_vocabulary", [])) != EXPECTED_LIFECYCLE_STATUSES:
                    self.add("GA-VOCABULARY-MISMATCH", protocol_path, "Protocol lifecycle vocabulary does not match the contract.")

    def manifest_release_diagnostics(self, view: RepositoryView) -> list[dict[str, Any]]:
        ledger_path = "manifests/manifest-release-ledger.json"
        ledger = self.read_view_json(view, ledger_path)
        if not isinstance(ledger, dict):
            return [make_diagnostic("GA-MANIFEST-INVENTORY", ledger_path, "Manifest release ledger is absent or malformed.")]
        entries = ledger.get("entries", [])
        if not isinstance(entries, list):
            return [make_diagnostic("GA-MANIFEST-INVENTORY", ledger_path, "Manifest release ledger entries are absent or malformed.")]
        diagnostics: list[dict[str, Any]] = []
        seen_release_ids: set[str] = set()
        seen_paths: set[str] = set()
        manifest_paths = sorted(
            relative
            for relative in view.iter_files()
            if re.fullmatch(r"manifests/(?:mission|protocol)/[^/]+\.json", relative)
        )
        frozen_release_paths = {
            "reiyah.mission@1.0.0": ("mission", "manifests/mission/reiyah-mission-1.0.0.json"),
            "reiyah.mission@1.1.0": ("mission", "manifests/mission/reiyah-mission-1.1.0.json"),
            "reiyah.protocol.harbor-gate-a@1.0.0": (
                "protocol",
                "manifests/protocol/harbor-gate-a-protocol-1.0.0.json",
            ),
            "reiyah.protocol.harbor-gate-a@1.1.0": (
                "protocol",
                "manifests/protocol/harbor-gate-a-protocol-1.1.0.json",
            ),
        }
        observed_release_contract = [
            (
                entry.get("release_id"),
                entry.get("manifest_kind"),
                entry.get("artifact_binding", {}).get("path")
                if isinstance(entry.get("artifact_binding"), dict)
                else None,
            )
            for entry in entries
            if isinstance(entry, dict)
        ]
        expected_release_contract = sorted(
            (release_id, kind, relative)
            for release_id, (kind, relative) in frozen_release_paths.items()
        )
        observed_release_contract_sorted = sorted(
            observed_release_contract,
            key=lambda item: tuple("" if value is None else str(value) for value in item),
        )
        if observed_release_contract_sorted != expected_release_contract or manifest_paths != sorted(
            relative for _, relative in frozen_release_paths.values()
        ):
            diagnostics.append(
                make_diagnostic(
                    "GA-MANIFEST-LINEAGE",
                    ledger_path,
                    "Gate A 1.1.0 freezes exactly the immutable 1.0 and 1.1 mission/protocol release chains; silent additional releases require a separately versioned architecture packet; "
                    f"expected={expected_release_contract}, observed={observed_release_contract_sorted}, files={manifest_paths}.",
                )
            )
        ledger_paths: set[str] = set()
        semantic_version_pattern = r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
        all_entries_by_id: dict[str, list[dict[str, Any]]] = {}
        manifests_by_release_id: dict[str, dict[str, Any]] = {}
        for candidate in entries:
            if isinstance(candidate, dict) and isinstance(candidate.get("release_id"), str):
                all_entries_by_id.setdefault(candidate["release_id"], []).append(candidate)
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            release_id = entry.get("release_id")
            binding = entry.get("artifact_binding")
            if not isinstance(release_id, str) or not isinstance(binding, dict):
                continue
            relative = binding.get("path")
            if release_id in seen_release_ids:
                diagnostics.append(make_diagnostic("GA-RELEASE-ID-REUSE", ledger_path, f"Duplicate release identifier {release_id}.", release_id))
            seen_release_ids.add(release_id)
            if not isinstance(relative, str):
                continue
            if relative in seen_paths:
                diagnostics.append(make_diagnostic("GA-MANIFEST-PATH-DUPLICATE", ledger_path, f"Manifest path is listed more than once: {relative}.", release_id))
            seen_paths.add(relative)
            ledger_paths.add(relative)
            if not view.is_file(relative):
                diagnostics.append(make_diagnostic("GA-REFERENCE-DANGLING", ledger_path, f"Manifest binding path does not exist: {relative}.", release_id))
                continue
            try:
                raw = view.read_bytes(relative)
            except (OSError, ValueError):
                diagnostics.append(make_diagnostic("GA-REFERENCE-DANGLING", ledger_path, f"Manifest binding path is unreadable: {relative}.", release_id))
                continue
            actual_digest = digest_bytes(raw)
            if binding.get("sha256") != actual_digest:
                diagnostics.append(make_diagnostic("GA-MANIFEST-MUTATION", relative, "Manifest bytes do not match the append-only ledger binding.", release_id))
            manifest = self.read_view_json(view, relative)
            if not isinstance(manifest, dict):
                continue
            diagnostics.extend(self.instance_diagnostics(manifest, relative))
            manifests_by_release_id[release_id] = manifest
            expected_kind = entry.get("manifest_kind")
            suffix_match = re.search(rf"@({semantic_version_pattern})$", release_id)
            release_version = suffix_match.group(1) if suffix_match else None
            if release_version is None or release_version != entry.get("version") or release_version != manifest.get("version"):
                diagnostics.append(make_diagnostic("GA-MANIFEST-LINEAGE", relative, f"Release identifier suffix, ledger version, and manifest version must be the same semantic version; suffix={release_version!r}, ledger={entry.get('version')!r}, manifest={manifest.get('version')!r}.", release_id))
            expected_manifest_schema = (
                f"https://schemas.reiyah.invalid/gate-a/{release_version}/{expected_kind}-manifest.schema.json"
                if release_version is not None and expected_kind in {"mission", "protocol"}
                else None
            )
            if expected_manifest_schema is None or manifest.get("schema_id") != expected_manifest_schema or binding.get("schema_id") != expected_manifest_schema:
                diagnostics.append(make_diagnostic("GA-MANIFEST-LINEAGE", relative, f"Manifest kind/version must bind its exact versioned schema; expected={expected_manifest_schema!r}, manifest={manifest.get('schema_id')!r}, ledger={binding.get('schema_id')!r}.", release_id))
            checks = (
                (manifest.get("release_id"), release_id, "release_id"),
                (manifest.get("manifest_kind"), expected_kind, "manifest_kind"),
                (manifest.get("artifact_id"), binding.get("artifact_id"), "artifact_id"),
                (manifest.get("schema_id"), binding.get("schema_id"), "schema_id"),
                (manifest.get("version"), binding.get("version"), "version"),
                (manifest.get("version"), entry.get("version"), "ledger version"),
                (manifest.get("release_stage"), entry.get("release_stage"), "release_stage"),
                (manifest.get("lifecycle_status"), entry.get("lifecycle_status"), "lifecycle_status"),
                (manifest.get("relation"), entry.get("relation"), "relation"),
                (manifest.get("operator_acceptance"), entry.get("operator_acceptance"), "operator_acceptance"),
            )
            for actual, expected, label in checks:
                if actual != expected:
                    diagnostics.append(make_diagnostic("GA-MANIFEST-BINDING", relative, f"Manifest {label} does not match its ledger entry.", release_id))
            if expected_kind == "protocol":
                mission_release_id = manifest.get("mission_release_id")
                mission_matches = [
                    candidate
                    for candidate in all_entries_by_id.get(mission_release_id, [])
                    if candidate.get("manifest_kind") == "mission"
                ] if isinstance(mission_release_id, str) else []
                if len(mission_matches) != 1:
                    diagnostics.append(make_diagnostic("GA-MANIFEST-LINEAGE", relative, f"Protocol mission_release_id must resolve exactly once to a mission ledger release; matches={len(mission_matches)}.", release_id))
                for policy_field in (
                    "lifecycle_transition_policy",
                    "evidence_binding_policy",
                    "result_binding_policy",
                    "scientific_dependency_policy",
                    "belief_normalization_policy",
                ):
                    policy = manifest.get(policy_field)
                    if not isinstance(policy, dict) or policy.get("protocol_release_id") != release_id or policy.get("runtime_execution_authorized") is not False:
                        diagnostics.append(make_diagnostic("GA-MANIFEST-LINEAGE", relative, f"Protocol {policy_field} must be owned by the enclosing release and keep runtime unauthorized.", release_id))
                registry_reference = manifest.get("definition_registry")
                registry_path = registry_reference.get("path") if isinstance(registry_reference, dict) else None
                registry = self.read_view_json(view, registry_path) if isinstance(registry_path, str) else None
                try:
                    registry_raw = view.read_bytes(registry_path) if isinstance(registry_path, str) else None
                except (OSError, ValueError):
                    registry_raw = None
                if (
                    not isinstance(registry_reference, dict)
                    or not isinstance(registry, dict)
                    or registry_raw is None
                    or registry_reference.get("sha256") != digest_bytes(registry_raw)
                    or registry.get("protocol_release_id") != release_id
                    or registry.get("artifact_id") != registry_reference.get("artifact_id")
                    or registry.get("schema_id") != registry_reference.get("schema_id")
                    or registry.get("version") != registry_reference.get("version")
                ):
                    diagnostics.append(make_diagnostic("GA-MANIFEST-LINEAGE", relative, "Protocol definition registry is not an exact current typed artifact owned by this release.", release_id))
            relation = entry.get("relation")
            if isinstance(relation, dict) and relation.get("type") != "initial":
                prior = relation.get("prior_release_id")
                if prior not in seen_release_ids and prior not in {item.get("release_id") for item in entries if isinstance(item, dict)}:
                    diagnostics.append(make_diagnostic("GA-REFERENCE-DANGLING", ledger_path, f"Prior manifest release does not resolve: {prior}.", release_id))

        entries_by_id = {
            entry.get("release_id"): entry
            for entry in entries
            if isinstance(entry, dict) and isinstance(entry.get("release_id"), str)
        }
        lineage_heads: dict[str, str] = {}
        for manifest_kind in ("mission", "protocol"):
            kind_entries = [entry for entry in entries if isinstance(entry, dict) and entry.get("manifest_kind") == manifest_kind]
            if not kind_entries:
                diagnostics.append(make_diagnostic("GA-MANIFEST-LINEAGE", ledger_path, f"Manifest lineage has no {manifest_kind} release."))
                continue
            roots: list[str] = []
            children: dict[str, list[str]] = {
                entry["release_id"]: []
                for entry in kind_entries
                if isinstance(entry.get("release_id"), str)
            }
            for entry in kind_entries:
                release_id = entry.get("release_id")
                if not isinstance(release_id, str):
                    continue
                relation = entry.get("relation")
                relation_type = relation.get("type") if isinstance(relation, dict) else None
                prior_id = relation.get("prior_release_id") if isinstance(relation, dict) else None
                if relation_type == "initial":
                    roots.append(release_id)
                    if prior_id is not None:
                        diagnostics.append(make_diagnostic("GA-MANIFEST-LINEAGE", ledger_path, "Initial manifest release cannot name a predecessor.", release_id))
                    continue
                prior = entries_by_id.get(prior_id)
                if not isinstance(prior, dict) or prior_id == release_id or prior.get("manifest_kind") != manifest_kind:
                    diagnostics.append(make_diagnostic("GA-MANIFEST-LINEAGE", ledger_path, f"Manifest predecessor must resolve to a distinct release of the same kind: {prior_id!r}.", release_id))
                    continue
                current_manifest = manifests_by_release_id.get(release_id)
                prior_manifest = manifests_by_release_id.get(prior_id)
                identity_field = "mission_id" if manifest_kind == "mission" else "protocol_id"
                current_stem = release_id.rsplit("@", 1)[0] if "@" in release_id else None
                prior_stem = prior_id.rsplit("@", 1)[0] if isinstance(prior_id, str) and "@" in prior_id else None
                if (
                    not isinstance(current_manifest, dict)
                    or not isinstance(prior_manifest, dict)
                    or current_manifest.get(identity_field) != prior_manifest.get(identity_field)
                    or not isinstance(current_manifest.get(identity_field), str)
                    or current_stem != prior_stem
                    or current_stem != current_manifest.get(identity_field)
                ):
                    diagnostics.append(
                        make_diagnostic(
                            "GA-MANIFEST-LINEAGE",
                            ledger_path,
                            f"{manifest_kind} successors must preserve predecessor {identity_field} and the exact release-id stem; current={current_manifest.get(identity_field) if isinstance(current_manifest, dict) else None!r}/{current_stem!r}, prior={prior_manifest.get(identity_field) if isinstance(prior_manifest, dict) else None!r}/{prior_stem!r}.",
                            release_id,
                        )
                    )
                children.setdefault(prior_id, []).append(release_id)
                current_version = entry.get("version")
                prior_version = prior.get("version")
                version_pattern = rf"^{semantic_version_pattern}$"
                current_match = re.fullmatch(version_pattern, current_version) if isinstance(current_version, str) else None
                prior_match = re.fullmatch(version_pattern, prior_version) if isinstance(prior_version, str) else None
                if not current_match or not prior_match or tuple(map(int, current_match.groups())) <= tuple(map(int, prior_match.groups())):
                    diagnostics.append(make_diagnostic("GA-MANIFEST-LINEAGE", ledger_path, f"Manifest successor version {current_version!r} must be strictly newer than predecessor {prior_version!r}.", release_id))
                current_suffix = re.search(rf"@({semantic_version_pattern})$", release_id)
                prior_suffix = re.search(rf"@({semantic_version_pattern})$", prior_id) if isinstance(prior_id, str) else None
                if (
                    current_suffix is None
                    or prior_suffix is None
                    or tuple(map(int, current_suffix.groups()[1:])) <= tuple(map(int, prior_suffix.groups()[1:]))
                ):
                    diagnostics.append(make_diagnostic("GA-MANIFEST-LINEAGE", ledger_path, f"Manifest successor release_id suffix must be strictly newer than predecessor suffix: {release_id!r} vs {prior_id!r}.", release_id))
            if len(roots) != 1:
                diagnostics.append(make_diagnostic("GA-MANIFEST-LINEAGE", ledger_path, f"{manifest_kind} lineage must have exactly one initial root; found={sorted(roots)}."))
            branches = sorted(release_id for release_id, descendants in children.items() if len(descendants) > 1)
            if branches:
                diagnostics.append(make_diagnostic("GA-MANIFEST-LINEAGE", ledger_path, f"{manifest_kind} lineage branches at {branches}."))
            heads = sorted(release_id for release_id, descendants in children.items() if not descendants)
            if len(heads) != 1:
                diagnostics.append(make_diagnostic("GA-MANIFEST-LINEAGE", ledger_path, f"{manifest_kind} lineage must have exactly one head; found={heads}."))
            else:
                lineage_heads[manifest_kind] = heads[0]
            if len(roots) == 1:
                visited: set[str] = set()
                current: str | None = roots[0]
                while current is not None and current not in visited:
                    visited.add(current)
                    descendants = children.get(current, [])
                    current = descendants[0] if len(descendants) == 1 else None
                expected_ids = set(children)
                if visited != expected_ids:
                    diagnostics.append(make_diagnostic("GA-MANIFEST-LINEAGE", ledger_path, f"{manifest_kind} lineage is cyclic, branched, or disconnected; unreachable={sorted(expected_ids - visited)}."))

        current_protocol_id = lineage_heads.get("protocol")
        current_mission_id = lineage_heads.get("mission")
        current_protocol = manifests_by_release_id.get(current_protocol_id) if current_protocol_id is not None else None
        if (
            current_protocol_id is not None
            and current_mission_id is not None
            and (
                not isinstance(current_protocol, dict)
                or current_protocol.get("mission_release_id") != current_mission_id
            )
        ):
            diagnostics.append(
                make_diagnostic(
                    "GA-MANIFEST-LINEAGE",
                    ledger_path,
                    "The unique current protocol head must bind the unique current mission head through mission_release_id; "
                    f"protocol_head={current_protocol_id!r}, bound_mission={current_protocol.get('mission_release_id') if isinstance(current_protocol, dict) else None!r}, mission_head={current_mission_id!r}.",
                    current_protocol_id,
                )
            )

        decision_records: dict[str, list[dict[str, Any]]] = {}
        for relative in view.iter_files():
            if not re.fullmatch(r"gate/decisions/reiyah\.gate-a-decision-[a-z0-9.-]+\.json", relative):
                continue
            record = self.read_view_json(view, relative)
            record_id = record.get("record_id") if isinstance(record, dict) else None
            if isinstance(record_id, str):
                decision_records.setdefault(record_id, []).append(record)
        requires_decision_validation = False
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            release_id = entry.get("release_id")
            acceptance = entry.get("operator_acceptance")
            acceptance_state = acceptance.get("state") if isinstance(acceptance, dict) else None
            record_id = acceptance.get("record_id") if isinstance(acceptance, dict) else None
            if acceptance_state == "unaccepted" and record_id is None:
                if entry.get("lifecycle_status") in {"supported", "contradicted", "replicated"}:
                    diagnostics.append(make_diagnostic("GA-ACCEPTANCE-REPLAY", ledger_path, "Evidentiary manifest lifecycle cannot be asserted without a bound operator decision.", release_id if isinstance(release_id, str) else None))
                continue
            candidates = decision_records.get(record_id, []) if isinstance(record_id, str) else []
            expected_binding = entry.get("artifact_binding")
            matching = [
                record
                for record in candidates
                if any(
                    isinstance(item, dict)
                    and item.get("release_id") == release_id
                    and item.get("artifact") == expected_binding
                    for item in record.get("manifest_release_bindings", [])
                )
            ]
            if len(matching) != 1:
                diagnostics.append(make_diagnostic("GA-ACCEPTANCE-REPLAY", ledger_path, f"Manifest operator acceptance record must resolve exactly once and bind release {release_id!r}; matches={len(matching)}.", release_id if isinstance(release_id, str) else None))
            else:
                requires_decision_validation = True
        if requires_decision_validation:
            diagnostics.extend(self.actual_decision_diagnostics(view))
        if ledger_paths != set(manifest_paths):
            missing = sorted(set(manifest_paths) - ledger_paths)
            extra = sorted(ledger_paths - set(manifest_paths))
            diagnostics.append(make_diagnostic("GA-MANIFEST-INVENTORY", ledger_path, f"Manifest ledger/file mismatch; unlisted={missing}, dangling={extra}."))
        return sorted(diagnostics, key=diagnostic_key)

    def check_manifest_releases(self) -> None:
        self.diagnostics.extend(self.manifest_release_diagnostics(self.view))

    def research_function_registry_diagnostics(self, view: RepositoryView) -> list[dict[str, Any]]:
        """Validate the declared research workflow as one exact, acyclic contract DAG."""
        relative = "manifests/research/harbor-research-function-registry-1.1.0.json"
        document = self.read_view_json(view, relative)
        if not isinstance(document, dict):
            return [make_diagnostic("GA-RESEARCH-FUNCTION-REGISTRY", relative, "Research-function registry is absent or malformed.")]
        diagnostics = self.instance_diagnostics(document, relative)
        functions = document.get("functions")
        if not isinstance(functions, list):
            return sorted(diagnostics + [make_diagnostic("GA-RESEARCH-FUNCTION-REGISTRY", relative, "Research-function registry functions must be an array.")], key=diagnostic_key)
        records = [item for item in functions if isinstance(item, dict)]
        identifiers = [item.get("function_id") for item in records]
        sequences = [item.get("sequence") for item in records]
        issues: list[str] = []
        if len(records) != len(functions):
            issues.append("every function entry must be an object")
        if any(not isinstance(item, str) for item in identifiers) or len(identifiers) != len(set(identifiers)):
            issues.append("function_id values must be nonempty and globally unique")
        if sequences != list(range(1, len(records) + 1)):
            issues.append(f"function sequence must be exactly 1..{len(records)} in array order")
        if document.get("dependency_order") != identifiers:
            issues.append("dependency_order must equal the complete function_id sequence exactly")
        by_id = {
            item["function_id"]: item
            for item in records
            if isinstance(item.get("function_id"), str)
        }
        position = {identifier: index for index, identifier in enumerate(identifiers) if isinstance(identifier, str)}
        adjacency: dict[str, list[str]] = {identifier: [] for identifier in position}
        for item in records:
            identifier = item.get("function_id")
            if not isinstance(identifier, str):
                continue
            dependencies = item.get("depends_on")
            if not isinstance(dependencies, list) or any(not isinstance(value, str) for value in dependencies):
                issues.append(f"{identifier}: depends_on must contain identifiers")
                continue
            if len(dependencies) != len(set(dependencies)):
                issues.append(f"{identifier}: dependency identifiers are duplicated")
            for dependency in dependencies:
                if dependency not in by_id:
                    issues.append(f"{identifier}: dependency {dependency!r} does not resolve")
                elif dependency == identifier or position[dependency] >= position[identifier]:
                    issues.append(f"{identifier}: dependency {dependency!r} must precede its consumer")
                else:
                    adjacency[identifier].append(dependency)

        visiting: set[str] = set()
        visited: set[str] = set()

        def has_cycle(identifier: str) -> bool:
            if identifier in visiting:
                return True
            if identifier in visited:
                return False
            visiting.add(identifier)
            result = any(has_cycle(dependency) for dependency in adjacency.get(identifier, []))
            visiting.discard(identifier)
            visited.add(identifier)
            return result

        if any(has_cycle(identifier) for identifier in adjacency):
            issues.append("function dependency graph must be acyclic")

        produced: dict[str, list[tuple[int, str, str, str]]] = {}
        for item in records:
            identifier = item.get("function_id")
            sequence = item.get("sequence")
            if not isinstance(identifier, str) or not isinstance(sequence, int):
                continue
            for output in item.get("outputs", []):
                if not isinstance(output, dict):
                    continue
                contract_id = output.get("contract_id")
                availability = output.get("availability")
                schema_id = output.get("schema_id")
                kind = output.get("kind")
                if availability == "gate_a_defined":
                    if not isinstance(schema_id, str) or schema_id not in self.schemas:
                        issues.append(f"{identifier}: Gate-A output {contract_id!r} has no locally resolved schema")
                    if isinstance(contract_id, str) and isinstance(kind, str) and isinstance(schema_id, str):
                        produced.setdefault(contract_id, []).append((sequence, identifier, kind, schema_id))
                elif schema_id is not None:
                    issues.append(f"{identifier}: nonlocal output {contract_id!r} must not assert a local schema")
        for item in records:
            identifier = item.get("function_id")
            sequence = item.get("sequence")
            if not isinstance(identifier, str) or not isinstance(sequence, int):
                continue
            for contract in item.get("inputs", []):
                if not isinstance(contract, dict):
                    continue
                contract_id = contract.get("contract_id")
                availability = contract.get("availability")
                schema_id = contract.get("schema_id")
                kind = contract.get("kind")
                if availability == "gate_a_defined":
                    if not isinstance(schema_id, str) or schema_id not in self.schemas:
                        issues.append(f"{identifier}: Gate-A input {contract_id!r} has no locally resolved schema")
                    matches = [
                        candidate
                        for candidate in produced.get(contract_id, [])
                        if candidate[0] < sequence
                    ] if isinstance(contract_id, str) else []
                    exact = [candidate for candidate in matches if candidate[2] == kind and candidate[3] == schema_id]
                    if len(exact) != 1:
                        issues.append(f"{identifier}: Gate-A input {contract_id!r} must match exactly one earlier producer by contract/kind/schema; matches={len(exact)}")
                elif schema_id is not None:
                    issues.append(f"{identifier}: external/unavailable input {contract_id!r} must explicitly remain nonlocal")
        if document.get("lifecycle_status") != "proposed" or document.get("architecture_only") is not True or document.get("runtime_authorized") is not False:
            issues.append("registry must remain proposed architecture only with runtime unauthorized")
        if issues:
            diagnostics.append(make_diagnostic("GA-RESEARCH-FUNCTION-REGISTRY", relative, f"Research-function contract graph is inconsistent: {sorted(set(issues))}.", document.get("registry_id") if isinstance(document.get("registry_id"), str) else None))
        return sorted(diagnostics, key=diagnostic_key)

    def check_research_function_registry(self) -> None:
        self.diagnostics.extend(self.research_function_registry_diagnostics(self.view))

    def scientific_contract_profile_diagnostics(self, view: RepositoryView) -> list[dict[str, Any]]:
        """Validate the exact v1.1 package and its exhaustive, typed reference map."""
        diagnostics: list[dict[str, Any]] = []
        profile = self.read_view_json(view, SCIENTIFIC_CONTRACT_PROFILE_PATH)
        if not isinstance(profile, dict):
            return [make_diagnostic("GA-SCIENTIFIC-CONTRACT-V11", SCIENTIFIC_CONTRACT_PROFILE_PATH, "The Gate A 1.1 scientific-contract profile is absent or malformed.")]
        diagnostics.extend(self.instance_diagnostics(profile, SCIENTIFIC_CONTRACT_PROFILE_PATH))

        expected_schema_paths = {
            "schemas/v1.1/scientific-contract-common.schema.json",
            "schemas/v1.1/human-automation-assessment.schema.json",
            "schemas/v1.1/joint-performance-evaluation.schema.json",
            "schemas/v1.1/sequential-off-policy-evaluation.schema.json",
            "schemas/v1.1/study-design-preregistration.schema.json",
            "schemas/v1.1/evaluation-assurance-bundle.schema.json",
            "schemas/v1.1/scientific-contract-mutation-fixture.schema.json",
            "schemas/protocol-definition-registry-1.1.schema.json",
        }
        schema_bindings = profile.get("schema_bindings") if isinstance(profile.get("schema_bindings"), list) else []
        observed_schema_paths: list[str] = []
        schema_issues: list[str] = []
        for binding in schema_bindings:
            if not isinstance(binding, dict):
                schema_issues.append("schema binding is not an object")
                continue
            relative = binding.get("path")
            if isinstance(relative, str):
                observed_schema_paths.append(relative)
            try:
                raw = view.read_bytes(relative) if isinstance(relative, str) else None
            except (OSError, ValueError):
                raw = None
            target = self.read_view_json(view, relative) if raw is not None and isinstance(relative, str) else None
            if raw is None or not isinstance(target, dict):
                schema_issues.append(f"{relative!r} does not resolve to strict local schema bytes")
                continue
            if binding.get("sha256") != digest_bytes(raw):
                schema_issues.append(f"{relative!r} digest is stale")
            if target.get("$id") != binding.get("schema_id"):
                schema_issues.append(f"{relative!r} schema identifier does not match its target")
            if binding.get("version") != "1.1.0" or "/1.1.0/" not in str(binding.get("schema_id")):
                schema_issues.append(f"{relative!r} is not an exact Gate A 1.1 schema binding")
        if set(observed_schema_paths) != expected_schema_paths or len(observed_schema_paths) != len(set(observed_schema_paths)) or schema_issues:
            diagnostics.append(make_diagnostic("GA-SCIENTIFIC-CONTRACT-V11", SCIENTIFIC_CONTRACT_PROFILE_PATH, f"Scientific schema bindings must equal the exact eight-file package; paths={observed_schema_paths}, issues={sorted(set(schema_issues))}."))

        expected_application_ids = set(V11_APPLICATION_RULES)
        application_ids = profile.get("application_schema_ids")
        if not isinstance(application_ids, list) or set(application_ids) != expected_application_ids or len(application_ids) != len(set(application_ids)):
            diagnostics.append(make_diagnostic("GA-SCIENTIFIC-CONTRACT-V11", SCIENTIFIC_CONTRACT_PROFILE_PATH, "application_schema_ids must equal the unique five-application Gate A 1.1 set."))

        catalog_entries = [
            entry
            for entry in self.catalog.get("fixtures", [])
            if isinstance(entry, dict) and isinstance(entry.get("path"), str) and entry["path"].startswith("fixtures/v1.1/")
        ]
        expected_fixture_bindings: dict[str, dict[str, Any]] = {}
        for entry in catalog_entries:
            relative = entry["path"]
            try:
                raw = view.read_bytes(relative)
            except (OSError, ValueError):
                raw = None
            if raw is None:
                continue
            expected_fixture_bindings[relative] = {
                "fixture_id": entry.get("fixture_id"),
                "classification": entry.get("classification"),
                "path": relative,
                "sha256": digest_bytes(raw),
                "expected_rule_id": entry.get("expected_primary_rule_id"),
            }
        profile_fixture_bindings = profile.get("fixture_bindings") if isinstance(profile.get("fixture_bindings"), list) else []
        observed_fixture_bindings = {
            binding.get("path"): binding
            for binding in profile_fixture_bindings
            if isinstance(binding, dict) and isinstance(binding.get("path"), str)
        }
        if (
            len(observed_fixture_bindings) != len(profile_fixture_bindings)
            or set(observed_fixture_bindings) != set(expected_fixture_bindings)
            or any(observed_fixture_bindings.get(path) != expected for path, expected in expected_fixture_bindings.items())
        ):
            diagnostics.append(make_diagnostic("GA-SCIENTIFIC-CONTRACT-V11", SCIENTIFIC_CONTRACT_PROFILE_PATH, f"fixture_bindings must exactly equal every v1.1 catalog entry and current bytes; expected={len(expected_fixture_bindings)}, observed={len(profile_fixture_bindings)}."))

        expected_production_rules = {
            "GA-SCIENTIFIC-CONTRACT-V11",
            "GA-SCIENTIFIC-REFERENCE-RESOLUTION",
            "GA-V11-REQUIRED-PROPERTY-SWEEP",
            "GA-PROTOCOL-DEFINITION-UNRESOLVED",
            *V11_APPLICATION_RULES.values(),
        }
        production_rules = profile.get("production_rule_ids")
        if not isinstance(production_rules, list) or set(production_rules) != expected_production_rules or len(production_rules) != len(set(production_rules)):
            diagnostics.append(make_diagnostic("GA-SCIENTIFIC-CONTRACT-V11", SCIENTIFIC_CONTRACT_PROFILE_PATH, f"production_rule_ids must equal the exact nine-rule v1.1 enforcement set; expected={sorted(expected_production_rules)}."))
        closures = profile.get("gap_closures") if isinstance(profile.get("gap_closures"), list) else []
        closure_ids = [item.get("gap_id") for item in closures if isinstance(item, dict)]
        closure_paths = [path for item in closures if isinstance(item, dict) for path in item.get("evidence_paths", []) if isinstance(path, str)]
        if set(closure_ids) != {"RGA-001", "RGA-002", "RGA-003"} or len(closure_ids) != 3 or any(not view.is_file(path) for path in closure_paths):
            diagnostics.append(make_diagnostic("GA-SCIENTIFIC-CONTRACT-V11", SCIENTIFIC_CONTRACT_PROFILE_PATH, "RGA-001..003 closure records must be unique and every declared evidence path must exist."))
        if (
            profile.get("lifecycle_status") != "proposed"
            or profile.get("operator_acceptance_state") != "unaccepted"
            or profile.get("architecture_only") is not True
            or profile.get("runtime_authorized") is not False
            or profile.get("gate_b_authorized") is not False
            or profile.get("scientific_support_claimed") is not False
            or profile.get("safety_case_claimed") is not False
        ):
            diagnostics.append(make_diagnostic("GA-SCIENTIFIC-CONTRACT-V11", SCIENTIFIC_CONTRACT_PROFILE_PATH, "The scientific-contract profile must remain proposed, unaccepted, architecture-only, non-runtime, and non-authoritative."))

        contract = profile.get("reference_resolution_contract") if isinstance(profile.get("reference_resolution_contract"), dict) else {}
        classes = contract.get("pointer_classes") if isinstance(contract.get("pointer_classes"), list) else []
        version_contract = contract.get("version_binding_contract") if isinstance(contract.get("version_binding_contract"), dict) else {}
        version_bindings = version_contract.get("bindings") if isinstance(version_contract.get("bindings"), list) else []
        reference_issues: list[str] = []
        if (
            contract.get("pointer_syntax") != "json_pointer_glob_v1"
            or contract.get("classification_exhaustive") is not True
            or contract.get("unclassified_reference_policy") != "reject"
            or contract.get("multiple_classification_policy") != "reject"
            or contract.get("exact_version_required") is not True
        ):
            reference_issues.append("reference-resolution root policy is not the exact fail-closed contract")
        class_ids = [item.get("class_id") for item in classes if isinstance(item, dict)]
        if len(class_ids) != len(classes) or len(class_ids) != len(set(class_ids)):
            reference_issues.append("pointer class identifiers must be present and unique")
        if (
            version_contract.get("binding_exhaustive") is not True
            or version_contract.get("missing_version_policy") != "reject"
            or version_contract.get("multiple_version_policy") != "reject"
            or version_contract.get("wildcard_alignment_policy") != "same_capture_tuple"
        ):
            reference_issues.append("version-binding root policy is not the exact fail-closed contract")
        version_binding_ids = [item.get("binding_id") for item in version_bindings if isinstance(item, dict)]
        if len(version_binding_ids) != len(version_bindings) or len(version_binding_ids) != len(set(version_binding_ids)):
            reference_issues.append("version-binding identifiers must be present and unique")

        documents: dict[str, tuple[str, dict[str, Any]]] = {}
        for entry in catalog_entries:
            if entry.get("classification") != "known_good":
                continue
            relative = entry["path"]
            document = self.read_view_json(view, relative)
            schema_id = document.get("schema_id") if isinstance(document, dict) else None
            if isinstance(document, dict) and schema_id in expected_application_ids:
                if schema_id in documents:
                    reference_issues.append(f"application schema {schema_id!r} has multiple known-good roots")
                documents[schema_id] = (relative, document)
        if set(documents) != expected_application_ids:
            reference_issues.append(f"known-good application roots are incomplete: {sorted(set(expected_application_ids) - set(documents))}")

        def decode_pointer_pattern(pattern: Any) -> tuple[str, ...] | None:
            if not isinstance(pattern, str) or not pattern.startswith("/"):
                return None
            return tuple(part.replace("~1", "/").replace("~0", "~") for part in pattern[1:].split("/"))

        def pointer_matches(pattern: tuple[str, ...], pointer: tuple[str, ...]) -> bool:
            return len(pattern) == len(pointer) and all(expected == "*" or expected == actual for expected, actual in zip(pattern, pointer))

        def pointer_captures(pattern: tuple[str, ...], pointer: tuple[str, ...]) -> tuple[str, ...] | None:
            if not pointer_matches(pattern, pointer):
                return None
            return tuple(actual for expected, actual in zip(pattern, pointer) if expected == "*")

        def materialize_pointer(pattern: tuple[str, ...], captures: tuple[str, ...]) -> tuple[str, ...] | None:
            required = sum(token == "*" for token in pattern)
            if required > len(captures):
                return None
            capture_index = 0
            materialized: list[str] = []
            for token in pattern:
                if token == "*":
                    materialized.append(captures[capture_index])
                    capture_index += 1
                else:
                    materialized.append(token)
            return tuple(materialized)

        def walk_nodes(value: Any, pointer: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], Any]]:
            yield pointer, value
            if isinstance(value, dict):
                for key in sorted(value):
                    yield from walk_nodes(value[key], pointer + (key,))
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    yield from walk_nodes(item, pointer + (str(index),))

        classes_by_schema: dict[str, list[dict[str, Any]]] = {schema_id: [] for schema_id in expected_application_ids}
        parsed_patterns: dict[str, list[tuple[str, ...]]] = {}
        for pointer_class in classes:
            if not isinstance(pointer_class, dict):
                reference_issues.append("pointer class is not an object")
                continue
            class_id = pointer_class.get("class_id")
            schema_id = pointer_class.get("application_schema_id")
            patterns = [decode_pointer_pattern(item) for item in pointer_class.get("pointer_patterns", [])]
            if not isinstance(class_id, str) or schema_id not in expected_application_ids or not patterns or any(item is None for item in patterns):
                reference_issues.append(f"pointer class {class_id!r} has an invalid application or pattern")
                continue
            if pointer_class.get("cardinality") not in {"exactly_one", "zero_or_one", "one_or_more", "zero_or_more"}:
                reference_issues.append(f"pointer class {class_id!r} has an invalid cardinality")
            classes_by_schema[schema_id].append(pointer_class)
            parsed_patterns[class_id] = [item for item in patterns if item is not None]

        parsed_version_bindings: list[tuple[dict[str, Any], list[tuple[str, ...]], tuple[str, ...]]] = []
        binding_pattern_owners: dict[tuple[str, tuple[str, ...]], list[str]] = {}
        for binding in version_bindings:
            if not isinstance(binding, dict):
                reference_issues.append("version binding is not an object")
                continue
            binding_id = binding.get("binding_id")
            schema_id = binding.get("application_schema_id")
            identity_patterns = [decode_pointer_pattern(item) for item in binding.get("identity_pointer_patterns", [])]
            version_pattern = decode_pointer_pattern(binding.get("version_pointer_pattern"))
            if (
                not isinstance(binding_id, str)
                or schema_id not in expected_application_ids
                or not identity_patterns
                or any(item is None for item in identity_patterns)
                or version_pattern is None
                or binding.get("version_source") not in {"sibling", "inherited"}
                or not isinstance(binding.get("wildcard_alignment_required"), bool)
                or binding.get("cardinality") != "exactly_one"
            ):
                reference_issues.append(f"version binding {binding_id!r} is malformed")
                continue
            concrete_identity_patterns = [item for item in identity_patterns if item is not None]
            if binding.get("wildcard_alignment_required") is True and any(
                sum(token == "*" for token in item) != sum(token == "*" for token in version_pattern)
                for item in concrete_identity_patterns
            ):
                reference_issues.append(f"version binding {binding_id!r} cannot align wildcard capture tuples")
            for pattern in concrete_identity_patterns:
                binding_pattern_owners.setdefault((schema_id, pattern), []).append(binding_id)
                exact_classes = [
                    pointer_class
                    for pointer_class in classes_by_schema.get(schema_id, [])
                    if pattern in parsed_patterns.get(pointer_class.get("class_id"), [])
                ]
                compound_classes = [
                    pointer_class
                    for pointer_class in classes_by_schema.get(schema_id, [])
                    if pattern[-1:] == ("actor_id",)
                    and pattern[:-1] in parsed_patterns.get(pointer_class.get("class_id"), [])
                    and pointer_class.get("value_shape") == "actor_reference"
                ]
                if len(exact_classes) + len(compound_classes) != 1:
                    reference_issues.append(f"version binding {binding_id!r} identity /{'/'.join(pattern)} must belong to exactly one pointer class")
            parsed_version_bindings.append((binding, concrete_identity_patterns, version_pattern))
        if any(len(owners) != 1 for owners in binding_pattern_owners.values()):
            reference_issues.append("each version-bound identity pattern must belong to exactly one binding")
        for schema_id, pointer_classes in classes_by_schema.items():
            for pointer_class in pointer_classes:
                if pointer_class.get("semantic_role") != "definition" or pointer_class.get("value_shape") != "stable_identifier":
                    continue
                for pattern in parsed_patterns.get(pointer_class.get("class_id"), []):
                    if len(binding_pattern_owners.get((schema_id, pattern), [])) != 1:
                        reference_issues.append(f"{schema_id}: definition /{'/'.join(pattern)} lacks one exact version binding")

        parsed_membership_bindings: dict[str, tuple[dict[str, Any], list[tuple[str, ...]]]] = {}
        for schema_id, pointer_classes in classes_by_schema.items():
            for pointer_class in pointer_classes:
                membership = pointer_class.get("membership_binding")
                if membership is None:
                    continue
                class_id = pointer_class.get("class_id")
                container_patterns = [decode_pointer_pattern(item) for item in membership.get("container_id_pointer_patterns", [])] if isinstance(membership, dict) else []
                if (
                    not isinstance(class_id, str)
                    or pointer_class.get("value_shape") != "stable_identifier"
                    or not isinstance(membership, dict)
                    or not container_patterns
                    or any(item is None for item in container_patterns)
                    or not isinstance(membership.get("container_target_kind"), str)
                    or membership.get("member_ids_field") != "member_ids"
                    or membership.get("container_identity_policy") not in {"exact_single_container", "all_declared_containers_same_identity"}
                    or not isinstance(membership.get("wildcard_alignment_required"), bool)
                ):
                    reference_issues.append(f"pointer class {class_id!r} has a malformed membership binding")
                    continue
                concrete_container_patterns = [item for item in container_patterns if item is not None]
                for container_pattern in concrete_container_patterns:
                    owners = [
                        candidate
                        for candidate in pointer_classes
                        if container_pattern in parsed_patterns.get(candidate.get("class_id"), [])
                        and candidate.get("owner_class") == "protocol_definition_registry"
                        and membership.get("container_target_kind") in candidate.get("target_kinds", [])
                    ]
                    if len(owners) != 1:
                        reference_issues.append(f"membership binding {class_id!r} container /{'/'.join(container_pattern)} must resolve through one typed registry pointer class")
                parsed_membership_bindings[class_id] = (membership, concrete_container_patterns)

        def patterns_overlap(left: tuple[str, ...], right: tuple[str, ...]) -> bool:
            return len(left) == len(right) and all(a == b or a == "*" or b == "*" for a, b in zip(left, right))

        for schema_id, pointer_classes in classes_by_schema.items():
            for left_index, left in enumerate(pointer_classes):
                for right in pointer_classes[left_index + 1:]:
                    if any(
                        patterns_overlap(left_pattern, right_pattern)
                        for left_pattern in parsed_patterns.get(left.get("class_id"), [])
                        for right_pattern in parsed_patterns.get(right.get("class_id"), [])
                    ):
                        reference_issues.append(f"{schema_id}: pointer classes {left.get('class_id')!r} and {right.get('class_id')!r} overlap on a schema-permitted surface")

        reference_shape_names = {
            "actorReference": "actor_reference",
            "versionedReference": "versioned_reference",
            "versionedReferenceBinding": "versioned_reference_binding",
            "unavailableVersionedReference": "versioned_reference_binding",
            "artifactReference": "artifact_reference",
            "artifactBinding": "artifact_binding",
            "unavailableArtifactReference": "artifact_binding",
            "recordArtifactReference": "record_artifact_reference",
            "evidenceReference": "evidence_reference",
            "stableIdentifier": "stable_identifier",
            "releaseIdentifier": "release_identifier",
        }

        def resolve_schema_ref(reference: Any, base_schema_id: str) -> tuple[dict[str, Any], str] | None:
            if not isinstance(reference, str):
                return None
            target_part, separator, fragment = reference.partition("#")
            if target_part:
                target_id = target_part if "://" in target_part else base_schema_id.rsplit("/", 1)[0] + "/" + target_part
            else:
                target_id = base_schema_id
            target: Any = self.schemas.get(target_id)
            if not isinstance(target, dict):
                return None
            if separator and fragment:
                if not fragment.startswith("/"):
                    return None
                for token in fragment[1:].split("/"):
                    decoded = unquote(token).replace("~1", "/").replace("~0", "~")
                    if not isinstance(target, dict) or decoded not in target:
                        return None
                    target = target[decoded]
            return (target, target_id) if isinstance(target, dict) else None

        def declared_reference_shape(node: Any, base_schema_id: str, seen: set[tuple[str, str]] | None = None) -> str | None:
            if not isinstance(node, dict):
                return None
            seen = set(seen or set())
            reference = node.get("$ref")
            if isinstance(reference, str):
                name = reference.rsplit("/", 1)[-1]
                if name in reference_shape_names:
                    return reference_shape_names[name]
                marker = (base_schema_id, reference)
                if marker in seen:
                    return None
                seen.add(marker)
                resolved = resolve_schema_ref(reference, base_schema_id)
                if resolved is not None:
                    return declared_reference_shape(resolved[0], resolved[1], seen)
            shapes = {
                shape
                for keyword in ("allOf", "oneOf", "anyOf")
                for branch in node.get(keyword, []) if isinstance(node.get(keyword), list)
                for shape in [declared_reference_shape(branch, base_schema_id, seen)]
                if shape is not None
            }
            if shapes == {"versioned_reference", "versioned_reference_binding"}:
                return "versioned_reference_binding"
            return next(iter(shapes)) if len(shapes) == 1 else None

        def schema_reference_surfaces(root_schema: dict[str, Any], root_schema_id: str) -> dict[tuple[str, ...], str]:
            surfaces: dict[tuple[str, ...], str] = {}
            active: set[tuple[int, str, tuple[str, ...]]] = set()

            def record_surface(pointer: tuple[str, ...], shape: str) -> None:
                previous = surfaces.get(pointer)
                if previous is None or previous == shape:
                    surfaces[pointer] = shape
                elif {previous, shape} == {"artifact_binding", "artifact_reference"}:
                    # A conditional can narrow an artifactBinding branch to its exact
                    # artifactReference arm without changing the full schema surface.
                    surfaces[pointer] = "artifact_binding"
                elif {previous, shape} == {"versioned_reference", "versioned_reference_binding"}:
                    surfaces[pointer] = "versioned_reference_binding"
                else:
                    surfaces[pointer] = f"incompatible:{previous}|{shape}"

            def walk_schema(node: Any, base_schema_id: str, pointer: tuple[str, ...], depth: int = 0) -> None:
                if not isinstance(node, dict) or depth > 80:
                    return
                node_shape = declared_reference_shape(node, base_schema_id)
                if pointer and node_shape is not None:
                    record_surface(pointer, node_shape)
                    return
                marker = (id(node), base_schema_id, pointer)
                if marker in active:
                    return
                active.add(marker)
                reference = node.get("$ref")
                if isinstance(reference, str):
                    resolved = resolve_schema_ref(reference, base_schema_id)
                    if resolved is not None:
                        walk_schema(resolved[0], resolved[1], pointer, depth + 1)
                properties = node.get("properties")
                if isinstance(properties, dict):
                    for name, child in properties.items():
                        child_pointer = pointer + (name,)
                        shape = declared_reference_shape(child, base_schema_id)
                        if shape is not None:
                            record_surface(child_pointer, shape)
                            continue
                        if isinstance(name, str) and (name.endswith("_id") or name in {"schema_id", "protocol_release_id", "mission_release_id"}):
                            record_surface(child_pointer, "schema_identifier" if name == "schema_id" else "release_identifier" if name.endswith("release_id") else "stable_identifier")
                        elif isinstance(name, str) and name.endswith("_ids") and isinstance(child, dict):
                            record_surface(child_pointer + ("*",), "stable_identifier")
                        walk_schema(child, base_schema_id, child_pointer, depth + 1)
                items = node.get("items")
                if isinstance(items, dict):
                    walk_schema(items, base_schema_id, pointer + ("*",), depth + 1)
                for keyword in ("allOf", "oneOf", "anyOf", "if", "then", "else"):
                    branches = node.get(keyword)
                    if isinstance(branches, list):
                        for branch in branches:
                            walk_schema(branch, base_schema_id, pointer, depth + 1)
                    elif isinstance(branches, dict):
                        walk_schema(branches, base_schema_id, pointer, depth + 1)
                active.discard(marker)

            walk_schema(root_schema, root_schema_id, ())
            return surfaces

        for schema_id in sorted(expected_application_ids):
            root_schema = self.schemas.get(schema_id)
            if not isinstance(root_schema, dict):
                reference_issues.append(f"{schema_id}: application schema is absent from the recursive local registry")
                continue
            for surface, expected_shape in sorted(schema_reference_surfaces(root_schema, schema_id).items()):
                matches = [
                    pointer_class
                    for pointer_class in classes_by_schema.get(schema_id, [])
                    if any(pointer_matches(pattern, surface) for pattern in parsed_patterns.get(pointer_class.get("class_id"), []))
                ]
                if len(matches) != 1:
                    reference_issues.append(f"{schema_id}: schema-permitted /{'/'.join(surface)} has {len(matches)} pointer classifications")
                elif matches[0].get("value_shape") != expected_shape:
                    reference_issues.append(f"{schema_id}: schema-permitted /{'/'.join(surface)} shape {expected_shape!r} conflicts with class {matches[0].get('value_shape')!r}")

        def typed_reference_object(value: Any) -> bool:
            if not isinstance(value, dict):
                return False
            keys = set(value)
            return bool(
                {"actor_id", "actor_type", "version"} <= keys
                or {"record_id", "record_kind", "version"} <= keys
                or {"artifact_id", "path", "sha256", "schema_id", "version"} <= keys
                or ({"availability_state", "expected_artifact_id"} <= keys)
                or ({"availability_state", "expected_record_id", "expected_record_kind", "expected_version"} <= keys)
                or {"evidence_id", "version"} <= keys
            )

        def reference_candidates(value: Any, pointer: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], Any]]:
            if isinstance(value, dict):
                if pointer and typed_reference_object(value):
                    yield pointer, value
                    return
                for key in sorted(value):
                    child = value[key]
                    child_pointer = pointer + (key,)
                    if isinstance(child, str) and (key.endswith("_id") or key in {"artifact_id", "protocol_release_id", "mission_release_id"}):
                        yield child_pointer, child
                    elif isinstance(child, list) and key.endswith("_ids"):
                        for index, item in enumerate(child):
                            if isinstance(item, str):
                                yield child_pointer + (str(index),), item
                    yield from reference_candidates(child, child_pointer)
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    yield from reference_candidates(item, pointer + (str(index),))

        local_definitions: dict[tuple[str, str, str, str], list[tuple[str, str]]] = {}
        graph_definitions: dict[tuple[str, str, str], list[tuple[str, str]]] = {}
        matched_values: list[tuple[dict[str, Any], str, tuple[str, ...], Any]] = []
        for schema_id, (relative, document) in documents.items():
            pointer_classes = classes_by_schema.get(schema_id, [])
            nodes = list(walk_nodes(document))
            for pointer, value in nodes:
                matches = [
                    pointer_class
                    for pointer_class in pointer_classes
                    if any(pointer_matches(pattern, pointer) for pattern in parsed_patterns.get(pointer_class.get("class_id"), []))
                ]
                if len(matches) > 1:
                    reference_issues.append(f"{relative}: /{'/'.join(pointer)} has multiple pointer classifications {[item.get('class_id') for item in matches]}")
                elif len(matches) == 1:
                    matched_values.append((matches[0], relative, pointer, value))
            for pointer, value in reference_candidates(document):
                matches = [
                    pointer_class
                    for pointer_class in pointer_classes
                    if any(pointer_matches(pattern, pointer) for pattern in parsed_patterns.get(pointer_class.get("class_id"), []))
                ]
                if len(matches) != 1:
                    reference_issues.append(f"{relative}: /{'/'.join(pointer)} is reference-bearing but has {len(matches)} classifications")

        def pointer_value(document: Any, pointer: tuple[str, ...]) -> tuple[bool, Any]:
            current = document
            for token in pointer:
                if isinstance(current, dict) and token in current:
                    current = current[token]
                elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
                    current = current[int(token)]
                else:
                    return False, None
            return True, current

        def semantic_contract_version(value: Any) -> tuple[int, int, int] | None:
            match = re.fullmatch(
                r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)",
                value,
            ) if isinstance(value, str) else None
            return tuple(int(part) for part in match.groups()) if match else None

        bound_versions: dict[tuple[str, tuple[str, ...]], str] = {}
        for schema_id, (relative, document) in documents.items():
            for pointer, identity_value in walk_nodes(document):
                matched_bindings: list[tuple[dict[str, Any], tuple[str, ...], tuple[str, ...]]] = []
                for binding, identity_patterns, version_pattern in parsed_version_bindings:
                    if binding.get("application_schema_id") != schema_id:
                        continue
                    for identity_pattern in identity_patterns:
                        captures = pointer_captures(identity_pattern, pointer)
                        if captures is not None:
                            matched_bindings.append((binding, captures, version_pattern))
                if not matched_bindings:
                    continue
                if len(matched_bindings) != 1:
                    reference_issues.append(f"{relative}: /{'/'.join(pointer)} matches {len(matched_bindings)} version bindings")
                    continue
                binding, captures, version_pattern = matched_bindings[0]
                version_pointer = materialize_pointer(version_pattern, captures)
                if (
                    version_pointer is None
                    or (
                        binding.get("wildcard_alignment_required") is True
                        and sum(token == "*" for token in version_pattern) != len(captures)
                    )
                ):
                    reference_issues.append(f"{relative}: /{'/'.join(pointer)} cannot align its version-binding wildcard captures")
                    continue
                found, version_value = pointer_value(document, version_pointer)
                if not found or semantic_contract_version(version_value) is None:
                    reference_issues.append(f"{relative}: /{'/'.join(pointer)} has no exact semantic version at /{'/'.join(version_pointer)}")
                    continue
                bound_versions[(relative, pointer)] = version_value
                parent_found, parent = pointer_value(document, pointer[:-1])
                if parent_found and isinstance(parent, dict) and isinstance(parent.get("version"), str) and parent.get("version") != version_value:
                    reference_issues.append(f"{relative}: /{'/'.join(pointer)} intrinsic version disagrees with its declared version binding")
                matching_classes = [
                    pointer_class
                    for pointer_class in classes_by_schema.get(schema_id, [])
                    if any(pointer_matches(pattern, pointer) for pattern in parsed_patterns.get(pointer_class.get("class_id"), []))
                    or (
                        pointer[-1:] == ("actor_id",)
                        and any(pointer_matches(pattern, pointer[:-1]) for pattern in parsed_patterns.get(pointer_class.get("class_id"), []))
                        and pointer_class.get("value_shape") == "actor_reference"
                    )
                ]
                expected_versions = {
                    pointer_class.get("expected_version")
                    for pointer_class in matching_classes
                    if pointer_class.get("expected_version") is not None
                }
                if len(expected_versions) > 1 or (expected_versions and version_value not in expected_versions):
                    reference_issues.append(f"{relative}: /{'/'.join(pointer)} bound version {version_value!r} conflicts with its pointer-class version")

        def occurrence_version(
            pointer_class: dict[str, Any],
            relative: str,
            pointer: tuple[str, ...],
            supplied_version: Any,
        ) -> str | None:
            bound = bound_versions.get((relative, pointer))
            if bound is None and pointer_class.get("value_shape") == "actor_reference":
                bound = bound_versions.get((relative, pointer + ("actor_id",)))
            if isinstance(bound, str):
                if isinstance(supplied_version, str) and supplied_version != bound:
                    reference_issues.append(f"{relative}: /{'/'.join(pointer)} embedded version disagrees with its exact version binding")
                return bound
            return supplied_version if isinstance(supplied_version, str) else None

        def canonical_kind(value: Any) -> str | None:
            return f"reiyah.kind.{re.sub('_', '-', value)}" if isinstance(value, str) else None

        documents_by_path = {relative: document for relative, document in documents.values()}

        def sibling_version(relative: str, pointer: tuple[str, ...]) -> str | None:
            current: Any = documents_by_path.get(relative)
            for token in pointer[:-1]:
                if isinstance(current, dict):
                    current = current.get(token)
                elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
                    current = current[int(token)]
                else:
                    return None
            return current.get("version") if isinstance(current, dict) and isinstance(current.get("version"), str) else None

        def value_identity(pointer_class: dict[str, Any], value: Any) -> tuple[str | None, str | None, str | None, str | None]:
            shape = pointer_class.get("value_shape")
            expected_version = pointer_class.get("expected_version")
            if shape in {"stable_identifier", "schema_identifier", "release_identifier"}:
                return (value if isinstance(value, str) else None, None, expected_version, None)
            if shape == "actor_reference" and isinstance(value, dict):
                return (value.get("actor_id"), "reiyah.kind.actor", value.get("version"), value.get("actor_type"))
            if shape in {"versioned_reference", "named_version_reference", "versioned_reference_binding"} and isinstance(value, dict):
                if value.get("availability_state") in {"not_available_in_gate_a", "not_authorized_in_gate_a"}:
                    return (
                        value.get("expected_record_id"),
                        canonical_kind(value.get("expected_record_kind")),
                        value.get("expected_version"),
                        None,
                    )
                return (value.get("record_id"), canonical_kind(value.get("record_kind")), value.get("version"), None)
            if shape == "record_artifact_reference" and isinstance(value, dict):
                return (value.get("record_id"), canonical_kind(value.get("record_kind")), value.get("version"), None)
            if shape == "evidence_reference" and isinstance(value, dict):
                return (value.get("evidence_id"), "reiyah.kind.evidence-record", value.get("version"), None)
            return (None, None, None, None)

        for pointer_class, relative, pointer, value in matched_values:
            if pointer_class.get("semantic_role") != "definition" or value is None:
                continue
            identifier, supplied_kind, supplied_version, _ = value_identity(pointer_class, value)
            target_kinds = pointer_class.get("target_kinds", [])
            if not isinstance(identifier, str) or not target_kinds:
                reference_issues.append(f"{relative}: /{'/'.join(pointer)} does not define a typed identity")
                continue
            if pointer_class.get("cardinality") != "exactly_one":
                reference_issues.append(f"{relative}: /{'/'.join(pointer)} definition must declare exactly_one cardinality")
            if supplied_kind is not None and supplied_kind not in target_kinds:
                reference_issues.append(f"{relative}: /{'/'.join(pointer)} definition kind {supplied_kind!r} is outside {target_kinds}")
                continue
            definition_kind = supplied_kind or target_kinds[0]
            declared_sibling_version = sibling_version(relative, pointer)
            version_value = occurrence_version(pointer_class, relative, pointer, supplied_version)
            if version_value is None and pointer_class.get("value_shape") == "stable_identifier":
                reference_issues.append(f"{relative}: /{'/'.join(pointer)} definition has no exact declared version binding")
                continue
            version_value = version_value or declared_sibling_version or pointer_class.get("expected_version")
            if version_value != pointer_class.get("expected_version"):
                reference_issues.append(f"{relative}: /{'/'.join(pointer)} definition version is not exact")
            location = (relative, "/" + "/".join(pointer))
            local_definitions.setdefault((relative, identifier, definition_kind, str(version_value)), []).append(location)
            graph_definitions.setdefault((identifier, definition_kind, str(version_value)), []).append(location)
        for key, locations in local_definitions.items():
            if len(locations) != 1:
                reference_issues.append(f"application-document definition {key!r} is ambiguous at {locations}")
        for key, locations in graph_definitions.items():
            if len(locations) != 1:
                reference_issues.append(f"application-graph definition {key!r} is ambiguous at {locations}")

        registry_document = self.read_view_json(view, "manifests/definitions/harbor-gate-a-definition-registry-1.1.0.json")
        registry_definitions = registry_document.get("definitions", []) if isinstance(registry_document, dict) and isinstance(registry_document.get("definitions"), list) else []
        registry_targets: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
        for definition in registry_definitions:
            if not isinstance(definition, dict):
                continue
            identifier = definition.get("definition_id")
            kind = canonical_kind(definition.get("kind"))
            version_value = definition.get("version")
            if isinstance(identifier, str) and isinstance(kind, str) and isinstance(version_value, str):
                registry_targets.setdefault((identifier, kind, version_value), []).append(definition)
                member_kind = {
                    "reiyah.kind.state-space": "reiyah.kind.state-space-member",
                    "reiyah.kind.action-space": "reiyah.kind.action-space-member",
                    "reiyah.kind.choice-set": "reiyah.kind.choice-set-member",
                }.get(kind)
                if member_kind is not None:
                    for member_id in definition.get("member_ids", []):
                        if isinstance(member_id, str):
                            registry_targets.setdefault((member_id, member_kind, version_value), []).append(definition)
        ledger = self.read_view_json(view, "manifests/manifest-release-ledger.json")
        release_targets: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
        for entry in ledger.get("entries", []) if isinstance(ledger, dict) else []:
            if not isinstance(entry, dict):
                continue
            kind = canonical_kind(f"{entry.get('manifest_kind')}_release")
            key = (entry.get("release_id"), kind, entry.get("version"))
            if all(isinstance(item, str) for item in key):
                release_targets.setdefault(key, []).append(entry)

        repository_targets: dict[tuple[str, str, str], list[tuple[str, dict[str, Any]]]] = {}
        v11_root_contracts = {
            "https://schemas.reiyah.invalid/scientific-contract/1.1.0/human-automation-assessment.schema.json": ("assessment_id", "human-automation-assessment"),
            "https://schemas.reiyah.invalid/scientific-contract/1.1.0/joint-performance-evaluation.schema.json": ("evaluation_id", "joint-performance-evaluation"),
            "https://schemas.reiyah.invalid/scientific-contract/1.1.0/sequential-off-policy-evaluation.schema.json": ("evaluation_id", "sequential-off-policy-evaluation"),
            "https://schemas.reiyah.invalid/scientific-contract/1.1.0/study-design-preregistration.schema.json": ("study_id", "study-design-preregistration"),
            "https://schemas.reiyah.invalid/scientific-contract/1.1.0/evaluation-assurance-bundle.schema.json": ("assurance_bundle_id", "evaluation-assurance-bundle"),
        }
        for candidate_path in view.iter_files():
            if not candidate_path.endswith(".json"):
                continue
            candidate = self.read_view_json(view, candidate_path)
            if not isinstance(candidate, dict):
                continue
            candidate_schema = candidate.get("schema_id")
            contract = v11_root_contracts.get(candidate_schema)
            if contract is not None:
                identifier, kind = candidate.get(contract[0]), f"reiyah.kind.{contract[1]}"
            else:
                legacy_kind = SCHEMA_OBJECT_KINDS.get(candidate_schema)
                identifier = candidate.get("object_id") if legacy_kind is not None else None
                kind = "reiyah.kind.evidence-record" if legacy_kind == "evidence" else canonical_kind(legacy_kind)
            version_value = candidate.get("version")
            if isinstance(identifier, str) and isinstance(kind, str) and isinstance(version_value, str):
                repository_targets.setdefault((identifier, kind, version_value), []).append((candidate_path, candidate))

        for pointer_class, relative, pointer, value in matched_values:
            if value is None:
                if pointer_class.get("cardinality") not in {"zero_or_one", "zero_or_more"}:
                    reference_issues.append(f"{relative}: /{'/'.join(pointer)} is null but cardinality is {pointer_class.get('cardinality')!r}")
                continue
            if pointer_class.get("semantic_role") == "definition":
                continue
            owner = pointer_class.get("owner_class")
            target_kinds = pointer_class.get("target_kinds", [])
            expected_version = pointer_class.get("expected_version")
            pointer_text = "/" + "/".join(pointer)
            if pointer_class.get("value_shape") == "versioned_reference_binding" and owner == "explicit_unavailable":
                if not isinstance(value, dict):
                    reference_issues.append(f"{relative}: {pointer_text} is not a versioned-reference binding")
                    continue
                expected_kind = canonical_kind(value.get("expected_record_kind"))
                if (
                    value.get("availability_state") not in {"not_available_in_gate_a", "not_authorized_in_gate_a"}
                    or not isinstance(value.get("expected_record_id"), str)
                    or expected_kind not in target_kinds
                    or value.get("expected_version") != expected_version
                    or value.get("gate_b_authorized") is not False
                    or value.get("runtime_execution_authorized") is not False
                    or value.get("earliest_permitted_gate") != "B_after_explicit_operator_acceptance"
                ):
                    reference_issues.append(f"{relative}: {pointer_text} explicit-unavailable reference is incomplete, kind-incompatible, or authoritative")
                continue
            if pointer_class.get("value_shape") == "record_artifact_reference":
                if not isinstance(value, dict):
                    reference_issues.append(f"{relative}: {pointer_text} is not an immutable record-artifact reference")
                    continue
                path = value.get("path")
                try:
                    raw = view.read_bytes(path) if isinstance(path, str) else None
                except (OSError, ValueError):
                    raw = None
                target = self.read_view_json(view, path) if raw is not None and isinstance(path, str) and path.endswith(".json") else None
                target_schema_id = target.get("schema_id") if isinstance(target, dict) else None
                target_record_contract = {
                    "https://schemas.reiyah.invalid/scientific-contract/1.1.0/human-automation-assessment.schema.json": ("assessment_id", "human_automation_assessment"),
                    "https://schemas.reiyah.invalid/scientific-contract/1.1.0/joint-performance-evaluation.schema.json": ("evaluation_id", "joint_performance_evaluation"),
                    "https://schemas.reiyah.invalid/scientific-contract/1.1.0/sequential-off-policy-evaluation.schema.json": ("evaluation_id", "sequential_off_policy_evaluation"),
                    "https://schemas.reiyah.invalid/scientific-contract/1.1.0/study-design-preregistration.schema.json": ("study_id", "study_design_preregistration"),
                    "https://schemas.reiyah.invalid/scientific-contract/1.1.0/evaluation-assurance-bundle.schema.json": ("assurance_bundle_id", "evaluation_assurance_bundle"),
                }.get(target_schema_id)
                target_record_id = target.get(target_record_contract[0]) if isinstance(target, dict) and target_record_contract is not None else None
                target_record_kind = canonical_kind(target_record_contract[1]) if target_record_contract is not None else None
                def semantic_version(value: Any) -> tuple[int, int, int] | None:
                    match = re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", value) if isinstance(value, str) else None
                    return tuple(int(part) for part in match.groups()) if match else None

                prior_version = semantic_version(value.get("version"))
                current_version = semantic_version(documents_by_path.get(relative, {}).get("version"))
                if (
                    raw is None
                    or value.get("sha256") != digest_bytes(raw)
                    or not isinstance(target, dict)
                    or target.get("artifact_id") != value.get("artifact_id")
                    or target_record_id != value.get("record_id")
                    or target_record_kind != canonical_kind(value.get("record_kind"))
                    or target.get("schema_id") != value.get("schema_id")
                    or target.get("version") != value.get("version")
                    or prior_version is None
                    or current_version is None
                    or not prior_version < current_version
                ):
                    reference_issues.append(f"{relative}: {pointer_text} immutable record-artifact reference does not resolve exact repository identity and bytes")
                continue
            if pointer_class.get("value_shape") in {"artifact_binding", "artifact_reference"}:
                if not isinstance(value, dict):
                    reference_issues.append(f"{relative}: {pointer_text} is not an artifact binding")
                    continue
                if pointer_class.get("value_shape") == "artifact_binding" and value.get("availability_state") in {"not_available_in_gate_a", "not_authorized_in_gate_a"}:
                    expected_kind = canonical_kind(value.get("expected_artifact_kind"))
                    compatible_kinds = set(target_kinds) | {item.removesuffix("-artifact") for item in target_kinds}
                    if (
                        expected_kind not in compatible_kinds
                        or value.get("gate_b_authorized") is not False
                        or value.get("runtime_execution_authorized") is not False
                        or value.get("earliest_permitted_gate") != "B_after_explicit_operator_acceptance"
                    ):
                        reference_issues.append(f"{relative}: {pointer_text} explicit-unavailable branch is kind-incompatible or authoritative")
                    continue
                path = value.get("path")
                try:
                    raw = view.read_bytes(path) if isinstance(path, str) else None
                except (OSError, ValueError):
                    raw = None
                target = self.read_view_json(view, path) if raw is not None and isinstance(path, str) and path.endswith(".json") else None
                if (
                    raw is None
                    or value.get("sha256") != digest_bytes(raw)
                    or not isinstance(target, dict)
                    or target.get("artifact_id") != value.get("artifact_id")
                    or target.get("schema_id") != value.get("schema_id")
                    or target.get("version") != value.get("version")
                ):
                    reference_issues.append(f"{relative}: {pointer_text} exact artifact branch does not resolve current repository identity and bytes")
                continue
            identifier, supplied_kind, supplied_version, actor_type = value_identity(pointer_class, value)
            if not isinstance(identifier, str):
                reference_issues.append(f"{relative}: {pointer_text} does not carry the declared reference shape")
                continue
            declared_sibling_version = sibling_version(relative, pointer)
            version_value = occurrence_version(pointer_class, relative, pointer, supplied_version)
            version_value = version_value or declared_sibling_version or expected_version
            if expected_version is not None and version_value != expected_version:
                reference_issues.append(f"{relative}: {pointer_text} version {version_value!r} is not exact {expected_version!r}")
            kinds = [supplied_kind] if supplied_kind is not None else list(target_kinds)
            if supplied_kind is not None and supplied_kind not in target_kinds:
                reference_issues.append(f"{relative}: {pointer_text} supplied kind {supplied_kind!r} is outside {target_kinds}")
                continue
            membership_contract = parsed_membership_bindings.get(pointer_class.get("class_id"))
            if membership_contract is not None:
                membership, container_patterns = membership_contract
                member_patterns = parsed_patterns.get(pointer_class.get("class_id"), [])
                member_captures = [
                    captures
                    for pattern in member_patterns
                    for captures in [pointer_captures(pattern, pointer)]
                    if captures is not None
                ]
                container_occurrences: list[tuple[tuple[str, ...], Any]] = []
                current_document = documents_by_path.get(relative)
                for container_pattern in container_patterns:
                    if membership.get("wildcard_alignment_required") is True:
                        for captures in member_captures:
                            materialized = materialize_pointer(container_pattern, captures)
                            if materialized is None or sum(token == "*" for token in container_pattern) != len(captures):
                                continue
                            found, container_value = pointer_value(current_document, materialized)
                            if found:
                                container_occurrences.append((materialized, container_value))
                    else:
                        container_occurrences.extend(
                            (candidate_pointer, candidate_value)
                            for candidate_pointer, candidate_value in walk_nodes(current_document)
                            if pointer_matches(container_pattern, candidate_pointer)
                        )
                unique_container_occurrences = {
                    (container_pointer, container_value)
                    for container_pointer, container_value in container_occurrences
                    if isinstance(container_value, str)
                }
                container_ids = [container_value for _, container_value in sorted(unique_container_occurrences)]
                identity_policy = membership.get("container_identity_policy")
                if (
                    (identity_policy == "exact_single_container" and len(unique_container_occurrences) != 1)
                    or (identity_policy == "all_declared_containers_same_identity" and (not container_ids or len(set(container_ids)) != 1))
                ):
                    reference_issues.append(f"{relative}: {pointer_text} membership container identity is missing, ambiguous, or inconsistent")
                else:
                    for container_pointer, container_id in sorted(unique_container_occurrences):
                        container_classes = [
                            candidate
                            for candidate in classes_by_schema.get(documents_by_path.get(relative, {}).get("schema_id"), [])
                            if any(pointer_matches(pattern, container_pointer) for pattern in parsed_patterns.get(candidate.get("class_id"), []))
                        ]
                        container_version = None
                        if len(container_classes) == 1:
                            container_version = occurrence_version(container_classes[0], relative, container_pointer, None)
                            container_version = container_version or sibling_version(relative, container_pointer) or container_classes[0].get("expected_version")
                        container_targets = registry_targets.get(
                            (container_id, membership.get("container_target_kind"), str(container_version)),
                            [],
                        )
                        members = container_targets[0].get(membership.get("member_ids_field"), []) if len(container_targets) == 1 else []
                        if len(container_targets) != 1 or not isinstance(members, list) or members.count(identifier) != 1:
                            reference_issues.append(f"{relative}: {pointer_text} is not an exact member of registry container {container_id!r}@{container_version!r}")
            if owner == "schema_catalog":
                matches = [identifier] if identifier in self.schemas and self.schema_paths.get(identifier) in expected_schema_paths else []
            elif owner == "manifest_release_ledger":
                matches = [item for kind in kinds for item in release_targets.get((identifier, kind, str(version_value)), [])]
            elif owner == "protocol_definition_registry":
                matches = [item for kind in kinds for item in registry_targets.get((identifier, kind, str(version_value)), [])]
                if actor_type is not None and (len(matches) != 1 or matches[0].get("actor_type") != actor_type):
                    matches = []
            elif owner == "application_document":
                matches = [item for kind in kinds for item in local_definitions.get((relative, identifier, kind, str(version_value)), [])]
            elif owner == "application_graph":
                matches = [item for kind in kinds for item in graph_definitions.get((identifier, kind, str(version_value)), [])]
            elif owner == "canonical_repository":
                matches = [item for kind in kinds for item in repository_targets.get((identifier, kind, str(version_value)), [])]
            else:
                matches = []
            cardinality = pointer_class.get("cardinality")
            resolution_valid = len(matches) == 1
            if cardinality not in {"exactly_one", "zero_or_one", "one_or_more", "zero_or_more"}:
                resolution_valid = False
            if not resolution_valid:
                reference_issues.append(f"{relative}: {pointer_text} must satisfy {cardinality!r} through {owner} with one exact target per present value; identity={identifier!r}, kinds={kinds}, version={version_value!r}, matches={len(matches)}")

        if reference_issues:
            diagnostics.append(make_diagnostic("GA-SCIENTIFIC-REFERENCE-RESOLUTION", SCIENTIFIC_CONTRACT_PROFILE_PATH, f"Gate A 1.1 reference classification/resolution failed: {sorted(set(reference_issues))[:80]}.", profile.get("profile_id") if isinstance(profile.get("profile_id"), str) else None))
        return sorted(diagnostics, key=diagnostic_key)

    def check_scientific_contract_profile(self) -> None:
        self.diagnostics.extend(self.scientific_contract_profile_diagnostics(self.view))

    def source_inventory_diagnostics(self, view: RepositoryView) -> list[dict[str, Any]]:
        legacy_overlay = "evidence/source-ledger.json" in view.overlay
        ledger_path = "evidence/source-ledger.json" if legacy_overlay else ACTIVE_SOURCE_LEDGER_PATH
        ledger = self.read_view_json(view, ledger_path)
        if not isinstance(ledger, dict) or not isinstance(ledger.get("records"), list):
            return [make_diagnostic("GA-UNLEDGERED-SOURCE", ledger_path, "Source ledger is absent or malformed.")]
        ledger_paths: list[str] = []
        for record in ledger["records"]:
            if not isinstance(record, dict):
                continue
            retained_path = record.get("retained_path")
            if not isinstance(retained_path, str) and isinstance(record.get("retained_payload"), dict):
                retained_path = record["retained_payload"].get("path")
            if isinstance(retained_path, str):
                ledger_paths.append(retained_path)
        actual_paths = {
            relative
            for relative in view.iter_files()
            if relative.startswith("evidence/sources/")
        }
        declared_paths = set(ledger_paths)
        diagnostics: list[dict[str, Any]] = []
        if len(ledger_paths) != len(declared_paths):
            diagnostics.append(
                make_diagnostic(
                    "GA-UNLEDGERED-SOURCE",
                    ledger_path,
                    "Retained source ledger paths are not unique.",
                )
            )
        if actual_paths != declared_paths:
            diagnostics.append(
                make_diagnostic(
                    "GA-UNLEDGERED-SOURCE",
                    ledger_path,
                    "Retained source directory must exactly equal ledger paths; "
                    f"unledgered={sorted(actual_paths - declared_paths)}, "
                    f"missing={sorted(declared_paths - actual_paths)}.",
                )
            )
        return diagnostics

    @staticmethod
    def git_metadata_path_allowed(relative: str) -> bool:
        git_relative = relative.removeprefix(".git/")
        exact = {
            "HEAD",
            "config",
            "description",
            "index",
            "COMMIT_EDITMSG",
            "ORIG_HEAD",
            "FETCH_HEAD",
            "packed-refs",
            "info/exclude",
            "info/refs",
            "objects/info/packs",
            "objects/info/commit-graph",
        }
        if git_relative in exact:
            return True
        patterns = (
            r"hooks/[A-Za-z0-9._-]+\.sample",
            r"objects/[0-9a-f]{2}/[0-9a-f]{38}",
            r"objects/pack/pack-[0-9a-f]{40,64}\.(?:pack|idx|rev|bitmap)",
            r"refs/(?:heads|tags|remotes)/[A-Za-z0-9._/-]+",
            r"logs/(?:HEAD|refs/(?:heads|tags|remotes)/[A-Za-z0-9._/-]+)",
            r"worktrees/[A-Za-z0-9._-]+/(?:HEAD|ORIG_HEAD|commondir|gitdir|index|logs/HEAD)",
        )
        return any(re.fullmatch(pattern, git_relative) for pattern in patterns)

    def is_plan_excluded(self, relative: str) -> bool:
        excluded = self.plan.get("index", {}).get("excluded_paths", [])
        if not isinstance(excluded, list):
            return False
        for value in excluded:
            if not isinstance(value, str):
                continue
            if value.endswith("/") and relative.startswith(value):
                return True
            if value == "gate/decisions/reiyah.gate-a-decision-" and relative.startswith(value):
                return True
            if value == "gate/public-distribution-receipts/reiyah.public-distribution-receipt-" and relative.startswith(value):
                return True
            if relative == value:
                return True
        return False

    def excluded_path_allowed(self, view: RepositoryView, relative: str) -> bool:
        if relative == INDEX_PATH:
            data = self.read_view_json(view, relative)
            return (
                isinstance(data, dict)
                and data.get("schema_id") == "https://schemas.reiyah.invalid/gate-a/1.1.2/gate-a-index.schema.json"
                and data.get("artifact_id") == "reiyah.artifact.gate-a-index-1.1.2"
                and data.get("index_id") == "reiyah.gate-a-evidence-index"
                and data.get("runtime_authorized") is False
                and (not self.schemas or not self.instance_diagnostics(data, relative))
            )
        if relative == SIDECAR_PATH:
            try:
                text = view.read_text(relative)
            except (OSError, UnicodeDecodeError, ValueError):
                return False
            return bool(re.fullmatch(rf"sha256:[0-9a-f]{{64}}  {re.escape(INDEX_PATH)}\n", text))
        if relative == REPORT_PATH:
            # Shell redirection opens and truncates this one derived output before validation
            # starts, so exactly zero in-progress bytes are allowed.  A completed excluded
            # output is still an inert, strict, canonically encoded validation report; the
            # cycle-breaking exclusion is never an opacity grant for runtime/private payloads.
            try:
                raw = view.read_bytes(relative)
            except (OSError, ValueError):
                return False
            if raw == b"":
                return True
            forbidden_markers = (
                b"-----BEGIN " + b"PRIVATE KEY-----",
                b"-----BEGIN RSA " + b"PRIVATE KEY-----",
                b"-----BEGIN OPENSSH " + b"PRIVATE KEY-----",
            )
            if raw.startswith((b"#!", b"\x7fELF", b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"MZ")) or any(
                marker in raw for marker in forbidden_markers
            ):
                return False
            try:
                report = strict_json_loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError, StrictJSONError):
                return False
            if (
                not isinstance(report, dict)
                or report.get("schema_id") != "https://schemas.reiyah.invalid/gate-a/1.1.2/validation-report.schema.json"
                or report.get("artifact_id") != "reiyah.validation-report.gate-a-1.1.2"
                or report.get("report_id") != "reiyah.validation-report.gate-a"
                or report.get("offline") is not True
                or report.get("read_only") is not True
                or report.get("runtime_authorized") is not False
                or report.get("acceptance_created") is not False
            ):
                return False
            if self.schemas and self.instance_diagnostics(report, relative):
                return False
            canonical = (
                json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
            ).encode("utf-8")
            return raw == canonical
        if relative.startswith("gate/decisions/reiyah.gate-a-decision-"):
            if not re.fullmatch(r"gate/decisions/reiyah\.gate-a-decision-[a-z0-9.-]+\.json", relative):
                return False
            try:
                raw = view.read_bytes(relative)
                record = strict_json_loads(raw.decode("utf-8"))
            except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError, StrictJSONError):
                return False
            canonical = (
                json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
            ).encode("utf-8") if isinstance(record, dict) else b""
            return (
                isinstance(record, dict)
                and record.get("schema_id") in {
                    "https://schemas.reiyah.invalid/gate-a/1.1.1/operator-decision-record.schema.json",
                    "https://schemas.reiyah.invalid/gate-a/1.1.2/operator-decision-record.schema.json",
                }
                and raw == canonical
                and (not self.schemas or not self.instance_diagnostics(record, relative))
            )
        if relative.startswith("gate/public-distribution-receipts/reiyah.public-distribution-receipt-"):
            if not re.fullmatch(r"gate/public-distribution-receipts/reiyah\.public-distribution-receipt-[a-z0-9.-]+\.json", relative):
                return False
            try:
                raw = view.read_bytes(relative)
                receipt = strict_json_loads(raw.decode("utf-8"))
            except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError, StrictJSONError):
                return False
            canonical = (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8") if isinstance(receipt, dict) else b""
            return (
                isinstance(receipt, dict)
                and receipt.get("schema_id") in {
                    "https://schemas.reiyah.invalid/gate-a/1.1.0/public-distribution-receipt.schema.json",
                    "https://schemas.reiyah.invalid/gate-a/1.1.1/public-distribution-receipt.schema.json",
                    "https://schemas.reiyah.invalid/gate-a/1.1.2/public-distribution-receipt.schema.json",
                }
                and raw == canonical
                and (not self.schemas or not self.instance_diagnostics(receipt, relative))
            )
        if relative.startswith(".git/"):
            return self.git_metadata_path_allowed(relative)
        if relative == ".DS_Store":
            return False
        if relative.startswith(".pytest_cache/"):
            return False
        pycache_prefixes = (
            "__pycache__/",
            "tools/__pycache__/",
            "validation/__pycache__/",
            "fixtures/__pycache__/",
            "fixtures/good/__pycache__/",
            "fixtures/bad/__pycache__/",
        )
        for prefix in pycache_prefixes:
            if relative.startswith(prefix):
                # Bytecode/cache bytes are never architecture inputs and are not needed for
                # the no-bytecode validator entry point.  Reject presence rather than trusting
                # a filename that could conceal arbitrary executable or private payloads.
                return False
        return False

    def repository_inventory_diagnostics(self, view: RepositoryView) -> list[dict[str, Any]]:
        diagnostics = self.source_inventory_diagnostics(view)
        source_ledger = self.read_view_json(view, ACTIVE_SOURCE_LEDGER_PATH)
        retained_source_paths = {
            record.get("retained_payload", {}).get("path")
            for record in source_ledger.get("records", [])
            if isinstance(source_ledger, dict) and isinstance(record, dict) and isinstance(record.get("retained_payload"), dict) and isinstance(record.get("retained_payload", {}).get("path"), str)
        } if isinstance(source_ledger, dict) else set()
        private_names = {".env", "credentials", "credentials.json", "id_rsa", "id_ed25519", "secrets.json"}
        private_suffixes = {".key", ".pem", ".p12", ".pfx", ".kdbx"}
        runtime_names = {
            "Dockerfile",
            "docker-compose.yml",
            "docker-compose.yaml",
            "Procfile",
            "Makefile",
            "package.json",
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
            "Cargo.toml",
            "go.mod",
            "go.sum",
        }
        runtime_suffixes = {
            ".app", ".bash", ".bin", ".c", ".cc", ".class", ".cpp", ".cs", ".db",
            ".dll", ".dylib", ".exe", ".go", ".h", ".hpp", ".ipynb", ".jar", ".java",
            ".js", ".jsx", ".kt", ".lua", ".mjs", ".node", ".onnx", ".parquet", ".php",
            ".pickle", ".pkl", ".pt", ".pth", ".r", ".rb", ".rs", ".scala", ".sh", ".so",
            ".sqlite", ".sqlite3", ".swift", ".ts", ".tsx", ".wasm", ".zsh",
        }
        authorized_tools = {"tools/build_gate_a_index.py", "tools/validate_gate_a.py"}
        authored_suffixes = {".cff", ".json", ".md"}
        for relative in view.iter_files():
            name = relative.rsplit("/", 1)[-1]
            suffix = Path(relative).suffix.lower()
            if (
                relative.startswith("history/gate-a-1.1.0/")
                and relative not in {HISTORICAL_V11_INDEX_PATH, HISTORICAL_V11_SIDECAR_PATH}
            ):
                diagnostics.append(
                    make_diagnostic(
                        "GA-INDEX-ROLE-INELIGIBLE",
                        relative,
                        "Gate A 1.1.0 history is closed to exactly the retained published index and sidecar; no additional bytes may hide under that prefix.",
                    )
                )
            if (
                relative.startswith("history/gate-a-1.1.1/")
                and relative not in {HISTORICAL_V111_INDEX_PATH, HISTORICAL_V111_SIDECAR_PATH}
            ):
                diagnostics.append(
                    make_diagnostic(
                        "GA-INDEX-ROLE-INELIGIBLE",
                        relative,
                        "Gate A 1.1.1 history is closed to exactly the retained published index and sidecar; no additional bytes may hide under that prefix.",
                    )
                )
            excluded = self.is_plan_excluded(relative)
            reserved_excluded_location = (
                relative.startswith("gate/validation-reports/")
                and relative not in {
                    "gate/validation-reports/gate-a-validation-1.0.0.json",
                    HISTORICAL_V11_REPORT_PATH,
                    HISTORICAL_V111_REPORT_PATH,
                }
            )
            if view.is_symlink(relative):
                rule = "GA-EXCLUDED-PATH-INTRUSION" if excluded or reserved_excluded_location else "GA-ARTIFACT-SYMLINK"
                diagnostics.append(make_diagnostic(rule, relative, "Repository symlink cannot bind exact in-root bytes and is forbidden."))
                continue
            allowed_excluded_metadata = (excluded or reserved_excluded_location) and self.excluded_path_allowed(view, relative)
            if (excluded or reserved_excluded_location) and not allowed_excluded_metadata:
                diagnostics.append(
                    make_diagnostic(
                        "GA-EXCLUDED-PATH-INTRUSION",
                        relative,
                        "Excluded location contains a file outside its exact derived-output or metadata pattern.",
                    )
                )
            if name in private_names or suffix in private_suffixes:
                diagnostics.append(make_diagnostic("GA-PRIVATE-DATA-PROHIBITED", relative, "Secret/private artifact filename is prohibited at Gate A."))
            if name in runtime_names or suffix in runtime_suffixes:
                diagnostics.append(make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", relative, "Runtime/deployment artifact type is prohibited at Gate A."))
            if suffix == ".py" and relative not in authorized_tools:
                diagnostics.append(make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", relative, "Python outside the two exact authorized offline tools is prohibited at Gate A."))
            allowed_architecture_artifact = (
                suffix in authored_suffixes
                or relative == ".gitignore"
                or relative in {".gitattributes", "LICENSE", "NOTICE"}
                or relative == "validation/requirements.lock"
                or relative == SIDECAR_PATH
                or suffix == ".sha256"
                or relative in retained_source_paths
                or relative in authorized_tools
            )
            if not allowed_architecture_artifact and not allowed_excluded_metadata:
                diagnostics.append(make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", relative, "File is outside the fail-closed Gate A architecture/source/tool artifact allowlist."))
            try:
                raw = view.read_bytes(relative)
            except (OSError, ValueError):
                raw = None
            private_markers = (
                b"-----BEGIN " + b"PRIVATE KEY-----",
                b"-----BEGIN RSA " + b"PRIVATE KEY-----",
                b"-----BEGIN OPENSSH " + b"PRIVATE KEY-----",
            )
            if raw is not None and not relative.startswith(".git/") and any(marker in raw for marker in private_markers):
                diagnostics.append(make_diagnostic("GA-PRIVATE-DATA-PROHIBITED", relative, "Private-key material signature is prohibited at Gate A."))
            if raw is not None and allowed_excluded_metadata and not relative.startswith(".git/") and raw.startswith(
                (b"\x7fELF", b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"MZ")
            ):
                diagnostics.append(make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", relative, "Executable binary signature is prohibited in an excluded path."))
            if allowed_excluded_metadata:
                continue
            if raw is None:
                continue
            json_payloads = [raw] if suffix == ".json" else raw.splitlines() if suffix == ".jsonl" else []
            for payload in json_payloads:
                if not payload.strip():
                    continue
                try:
                    strict_json_loads(payload)
                except DuplicateJSONKeyError as exc:
                    diagnostics.append(make_diagnostic("GA-JSON-DUPLICATE-KEY", relative, f"JSON object member names must be unique before parsing: {exc}"))
                    break
                except NonFiniteJSONError as exc:
                    diagnostics.append(make_diagnostic("GA-NONFINITE-NUMBER", relative, f"JSON numbers must be finite: {exc}"))
                    break
                except (UnicodeDecodeError, json.JSONDecodeError):
                    break
            # The private marker scan runs before excluded-path handling above, so every
            # non-Git repository byte surface is covered exactly once.
            if raw.startswith(b"#!") and relative not in authorized_tools:
                diagnostics.append(make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", relative, "Executable shebang is forbidden outside the two authorized offline tools."))
            if relative not in authorized_tools and not relative.startswith(".git/") and relative not in view.overlay:
                try:
                    executable = bool(view.absolute(relative).stat().st_mode & 0o111)
                except (OSError, ValueError):
                    executable = False
                if executable:
                    diagnostics.append(make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", relative, "Executable mode is forbidden outside the two authorized offline tools."))
            if not relative.startswith(".git/objects/") and raw.startswith((b"\x7fELF", b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"MZ")):
                diagnostics.append(make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", relative, "Executable binary signature is prohibited at Gate A."))
        return sorted(diagnostics, key=diagnostic_key)

    def sources_crosswalk_diagnostics(self, view: RepositoryView) -> list[dict[str, Any]]:
        if (
            "evidence/source-ledger.json" not in view.overlay
            and "evidence/standards-crosswalk.json" not in view.overlay
        ):
            return self.public_sources_crosswalk_diagnostics(view)
        ledger_path = "evidence/source-ledger.json"
        crosswalk_path = "evidence/standards-crosswalk.json"
        ledger = self.read_view_json(view, ledger_path)
        crosswalk = self.read_view_json(view, crosswalk_path)
        if not isinstance(ledger, dict) or not isinstance(crosswalk, dict):
            return [make_diagnostic("GA-SOURCE-INVENTORY", ledger_path, "Source ledger or standards crosswalk is absent or malformed.")]
        records = ledger.get("records", [])
        entries = crosswalk.get("entries", [])
        if not isinstance(records, list) or not isinstance(entries, list):
            return [make_diagnostic("GA-SOURCE-INVENTORY", ledger_path, "Source ledger records or crosswalk entries are absent or malformed.")]
        diagnostics = self.source_inventory_diagnostics(view)
        if len(records) != 8:
            diagnostics.append(make_diagnostic("GA-SOURCE-INVENTORY", ledger_path, f"Expected 8 frozen source records, found {len(records)}."))
        observed_source_ids = [
            record.get("source_id")
            for record in records
            if isinstance(record, dict) and isinstance(record.get("source_id"), str)
        ]
        if set(observed_source_ids) != set(FROZEN_SOURCE_IDENTITIES):
            diagnostics.append(
                make_diagnostic(
                    "GA-SOURCE-INVENTORY",
                    ledger_path,
                    "Gate A 1.0.0 source identities must equal the frozen eight-source contract; "
                    f"missing={sorted(set(FROZEN_SOURCE_IDENTITIES) - set(observed_source_ids))}, "
                    f"extra={sorted(set(observed_source_ids) - set(FROZEN_SOURCE_IDENTITIES))}.",
                )
            )
        if len(entries) != 7:
            diagnostics.append(make_diagnostic("GA-CROSSWALK-INVENTORY", crosswalk_path, f"Expected 7 frozen crosswalk entries, found {len(entries)}."))
        source_ids: set[str] = set()
        source_records_by_id: dict[str, list[dict[str, Any]]] = {}
        eligible_retained_source_ids: set[str] = set()
        retained_paths: set[str] = set()
        for record in records:
            if not isinstance(record, dict):
                continue
            record_path = ledger_path
            diagnostics.extend(self.instance_diagnostics(record, record_path))
            source_id = record.get("source_id")
            relative = record.get("retained_path")
            identity_issues: list[str] = []
            if isinstance(source_id, str):
                source_records_by_id.setdefault(source_id, []).append(record)
                if source_id in source_ids:
                    diagnostics.append(make_diagnostic("GA-SOURCE-ID-DUPLICATE", ledger_path, f"Duplicate source_id {source_id}.", source_id))
                source_ids.add(source_id)
                frozen_identity = FROZEN_SOURCE_IDENTITIES.get(source_id)
                if frozen_identity is None:
                    identity_issues.append("source_id is not in the frozen Gate A identity contract")
                else:
                    identity_issues.extend(
                        field
                        for field in (
                            "retained_path",
                            "sha256",
                            "title",
                            "publisher",
                            "document_identifier",
                            "exact_version",
                            "publication_date",
                        )
                        if record.get(field) != frozen_identity.get(field)
                    )
            else:
                frozen_identity = None
                identity_issues.append("source_id")
            if identity_issues:
                diagnostics.append(
                    make_diagnostic(
                        "GA-STANDARDS-EVIDENCE-INCOMPLETE",
                        ledger_path,
                        f"Source ledger identity must equal the frozen Gate A 1.0.0 contract; mismatches={sorted(set(identity_issues))}.",
                        source_id if isinstance(source_id, str) else None,
                    )
                )
            if not isinstance(relative, str):
                continue
            if relative in retained_paths:
                diagnostics.append(make_diagnostic("GA-SOURCE-PATH-DUPLICATE", ledger_path, f"Duplicate retained source path {relative}.", source_id if isinstance(source_id, str) else None))
            retained_paths.add(relative)
            if not view.is_file(relative):
                diagnostics.append(make_diagnostic("GA-REFERENCE-DANGLING", ledger_path, f"Retained source path is absent: {relative}.", source_id if isinstance(source_id, str) else None))
                continue
            if view.is_symlink(relative):
                diagnostics.append(make_diagnostic("GA-ARTIFACT-SYMLINK", relative, "Retained source must be exact local bytes, not a symlink.", source_id if isinstance(source_id, str) else None))
                continue
            try:
                raw = view.read_bytes(relative)
            except (OSError, ValueError):
                diagnostics.append(make_diagnostic("GA-REFERENCE-DANGLING", ledger_path, f"Retained source path is unreadable: {relative}.", source_id if isinstance(source_id, str) else None))
                continue
            source_bytes_match = (
                record.get("byte_size") == len(raw)
                and record.get("sha256") == digest_bytes(raw)
            )
            if record.get("byte_size") != len(raw):
                diagnostics.append(make_diagnostic("GA-SOURCE-SIZE-MISMATCH", relative, f"Declared byte_size {record.get('byte_size')} does not match {len(raw)}.", source_id if isinstance(source_id, str) else None))
            if record.get("sha256") != digest_bytes(raw):
                diagnostics.append(make_diagnostic("GA-DIGEST-MISMATCH", relative, "Retained source SHA-256 does not match exact bytes.", source_id if isinstance(source_id, str) else None))
            full_normative_text = record.get("evidence_class") == "full_normative_text"
            if record.get("normative_text_available") is not full_normative_text:
                diagnostics.append(make_diagnostic("GA-STANDARDS-SCOPE-INFLATION", ledger_path, "normative_text_available must be true exactly for full_normative_text evidence.", source_id if isinstance(source_id, str) else None))
            suffix = Path(relative).suffix.lower()
            if suffix == ".pdf" and not raw.startswith(b"%PDF-"):
                diagnostics.append(make_diagnostic("GA-SOURCE-FORMAT", relative, "Retained PDF does not begin with the inert %PDF- signature.", source_id if isinstance(source_id, str) else None))
            elif suffix == ".jsonl":
                lines = raw.splitlines()
                parsed_line: Any = None
                if not raw.endswith(b"\n") or len(lines) != 1:
                    diagnostics.append(make_diagnostic("GA-SOURCE-FORMAT", relative, "Retained JSONL range must contain exactly one complete newline-terminated record.", source_id if isinstance(source_id, str) else None))
                else:
                    try:
                        parsed_line = strict_json_loads(lines[0].decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError, StrictJSONError):
                        parsed_line = None
                    if not isinstance(parsed_line, dict):
                        diagnostics.append(make_diagnostic("GA-SOURCE-FORMAT", relative, "Retained JSONL record is not one UTF-8 JSON object.", source_id if isinstance(source_id, str) else None))
                if isinstance(parsed_line, dict) and isinstance(frozen_identity, dict):
                    reference = parsed_line.get("reference")
                    title = parsed_line.get("title")
                    english_title = title.get("en") if isinstance(title, dict) else None
                    edition = parsed_line.get("edition")
                    publication_date = parsed_line.get("publicationDate")
                    extracted = {
                        "document_identifier": {"state": "observed", "value": reference},
                        "title": f"{reference} {english_title}" if isinstance(reference, str) and isinstance(english_title, str) else None,
                        "publication_date": {"state": "observed", "value": publication_date},
                        "exact_version": {
                            "state": "observed",
                            "value": f"{reference}, edition {edition}",
                        } if isinstance(reference, str) and isinstance(edition, int) else None,
                    }
                    extracted_mismatches = sorted(
                        field
                        for field, extracted_value in extracted.items()
                        if extracted_value != record.get(field)
                    )
                    if extracted_mismatches:
                        diagnostics.append(
                            make_diagnostic(
                                "GA-STANDARDS-EVIDENCE-INCOMPLETE",
                                relative,
                                "Structured ISO retained bytes do not exactly derive the ledger identity; "
                                f"mismatches={extracted_mismatches}.",
                                source_id if isinstance(source_id, str) else None,
                            )
                        )
            elif suffix == ".html":
                try:
                    decoded = raw.decode("utf-8").strip()
                except UnicodeDecodeError:
                    decoded = ""
                if not decoded:
                    diagnostics.append(make_diagnostic("GA-SOURCE-FORMAT", relative, "Retained HTML is not nonempty UTF-8 text.", source_id if isinstance(source_id, str) else None))
                if source_id == "src.nist.ai-100-1.2023.publication-page" and decoded:
                    required_tokens = (
                        "Artificial Intelligence Risk Management Framework (AI RMF 1.0)",
                        "NIST AI 100-1",
                        "2023-01-26",
                        "National Institute of Standards and Technology",
                    )
                    missing_tokens = [token for token in required_tokens if token not in decoded]
                    if missing_tokens:
                        diagnostics.append(
                            make_diagnostic(
                                "GA-STANDARDS-EVIDENCE-INCOMPLETE",
                                relative,
                                f"Retained NIST publication HTML lacks frozen identity tokens: {missing_tokens}.",
                                source_id,
                            )
                        )
            if isinstance(source_id, str) and source_bytes_match:
                eligible_retained_source_ids.add(source_id)
        mapping_ids: list[str] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            mapping_id = entry.get("mapping_id") if isinstance(entry.get("mapping_id"), str) else None
            if isinstance(mapping_id, str):
                mapping_ids.append(mapping_id)
            raw_entry_source_ids = entry.get("source_ids")
            entry_source_ids = raw_entry_source_ids if isinstance(raw_entry_source_ids, list) else []
            for source_id in entry_source_ids:
                if source_id not in source_ids:
                    diagnostics.append(make_diagnostic("GA-REFERENCE-DANGLING", crosswalk_path, f"Crosswalk source_id does not resolve: {source_id}.", mapping_id))
            if entry.get("lifecycle_status") != "proposed":
                diagnostics.append(make_diagnostic("GA-STANDARDS-UNSUPPORTED-CLAIM", crosswalk_path, "Standards mapping lifecycle must remain proposed.", mapping_id))
            identity_source_id = entry.get("identity_source_id")
            identity_matches = source_records_by_id.get(identity_source_id, []) if isinstance(identity_source_id, str) else []
            identity_issues: list[str] = []
            if not isinstance(identity_source_id, str) or identity_source_id not in entry_source_ids:
                identity_issues.append("identity_source_id must be a member of source_ids")
            if len(identity_matches) != 1:
                identity_issues.append(f"identity source ledger matches={len(identity_matches)}")
            elif identity_source_id not in eligible_retained_source_ids:
                identity_issues.append("identity source retained bytes are not eligible")
            else:
                identity_record = identity_matches[0]
                external_reference = entry.get("external_reference") if isinstance(entry.get("external_reference"), dict) else {}
                external_title = external_reference.get("title")
                exact_identity_checks = (
                    (external_reference.get("publisher"), identity_record.get("publisher"), "publisher"),
                    (
                        external_title.get("value") if isinstance(external_title, dict) else None,
                        identity_record.get("title"),
                        "title",
                    ),
                    (external_reference.get("document_identifier"), identity_record.get("document_identifier"), "document_identifier"),
                    (external_reference.get("exact_version"), identity_record.get("exact_version"), "exact_version"),
                    (external_reference.get("publication_date"), identity_record.get("publication_date"), "publication_date"),
                )
                identity_issues.extend(
                    f"external_reference.{field} != identity source {field}"
                    for actual, expected, field in exact_identity_checks
                    if actual != expected
                )
            evidence_issues: list[str] = list(identity_issues)
            if entry.get("mapping_state") != "evidence_gap":
                external_reference = entry.get("external_reference") if isinstance(entry.get("external_reference"), dict) else {}
                observed_surfaces = {
                    "exact_version": external_reference.get("exact_version"),
                    "publication_date": external_reference.get("publication_date"),
                    "scope": entry.get("scope"),
                    "comparator": entry.get("comparator"),
                    "requirement_locator": entry.get("requirement_locator"),
                }
                unresolved_sources = sorted(
                    repr(source_id)
                    for source_id in entry_source_ids
                    if not isinstance(source_id, str) or source_id not in eligible_retained_source_ids
                ) if isinstance(raw_entry_source_ids, list) else [repr(raw_entry_source_ids)]
                incomplete_fields = sorted(
                    field
                    for field, measurement in observed_surfaces.items()
                    if not isinstance(measurement, dict)
                    or measurement.get("state") != "observed"
                    or not isinstance(measurement.get("value"), str)
                    or not measurement["value"].strip()
                )
                unique_source_count = len(set(source_id for source_id in entry_source_ids if isinstance(source_id, str)))
                if (
                    not isinstance(raw_entry_source_ids, list)
                    or not entry_source_ids
                    or len(entry_source_ids) != unique_source_count
                    or unresolved_sources
                    or incomplete_fields
                ):
                    evidence_issues.append(
                        "non-gap mapping requires unique resolved retained sources and observed exact version, publication date, scope, comparator, and requirement locator; "
                        f"unresolved_sources={unresolved_sources}, incomplete_fields={incomplete_fields}"
                    )
            if evidence_issues:
                diagnostics.append(
                    make_diagnostic(
                        "GA-STANDARDS-EVIDENCE-INCOMPLETE",
                        crosswalk_path,
                        "Standards mapping identity and retained evidence must resolve exactly; "
                        f"issues={sorted(set(evidence_issues))}.",
                        mapping_id,
                    )
                )
        if crosswalk.get("compliance_claimed") is not False:
            diagnostics.append(make_diagnostic("GA-STANDARDS-UNSUPPORTED-CLAIM", crosswalk_path, "Gate A crosswalk may not claim compliance."))
        if len(mapping_ids) != len(set(mapping_ids)):
            diagnostics.append(make_diagnostic("GA-STANDARDS-MAPPING-AMBIGUOUS", crosswalk_path, "Standards crosswalk mapping_id values must be present and unique."))
        return sorted(diagnostics, key=diagnostic_key)

    def exact_artifact_binding_issues(
        self,
        view: RepositoryView,
        binding: Any,
        expected_path: str,
        require_target_identity: bool = True,
        physical_path: str | None = None,
    ) -> list[str]:
        """Compare a logical custody binding with exact current or retained historical bytes."""

        if not isinstance(binding, dict):
            return ["binding is not an object"]
        issues: list[str] = []
        if binding.get("path") != expected_path:
            issues.append(f"path must equal {expected_path!r}")
        target_path = expected_path if physical_path is None else physical_path
        try:
            raw = view.read_bytes(target_path)
        except (OSError, ValueError):
            return issues + [f"target bytes {target_path!r} are absent or unreadable"]
        target = self.read_view_json(view, target_path)
        expected_fields: dict[str, Any] = {"sha256": digest_bytes(raw)}
        if require_target_identity or "byte_size" in binding:
            expected_fields["byte_size"] = len(raw)
        if isinstance(target, dict) and require_target_identity:
            expected_fields["artifact_id"] = target.get("artifact_id")
            expected_fields["version"] = target.get("version")
            if "schema_id" in binding:
                expected_fields["schema_id"] = target.get("schema_id")
        for field, expected in expected_fields.items():
            if binding.get(field) != expected:
                issues.append(f"{field} does not bind exact target bytes/identity")
        return issues

    def public_sources_crosswalk_diagnostics(self, view: RepositoryView) -> list[dict[str, Any]]:
        ledger_path = ACTIVE_SOURCE_LEDGER_PATH
        crosswalk_path = ACTIVE_STANDARDS_CROSSWALK_PATH
        ledger = self.read_view_json(view, ledger_path)
        crosswalk = self.read_view_json(view, crosswalk_path)
        if not isinstance(ledger, dict) or not isinstance(crosswalk, dict):
            return [make_diagnostic("GA-SOURCE-INVENTORY", ledger_path, "Active 1.1 source ledger or standards crosswalk is absent or malformed.")]
        diagnostics = self.source_inventory_diagnostics(view)
        diagnostics.extend(self.instance_diagnostics(ledger, ledger_path))
        diagnostics.extend(self.instance_diagnostics(crosswalk, crosswalk_path))
        records = ledger.get("records")
        entries = crosswalk.get("entries")
        if not isinstance(records, list) or not isinstance(entries, list):
            diagnostics.append(make_diagnostic("GA-SOURCE-INVENTORY", ledger_path, "Active ledger records and crosswalk entries must be arrays."))
            return sorted(diagnostics, key=diagnostic_key)

        by_id: dict[str, list[dict[str, Any]]] = {}
        retained_ids: set[str] = set()
        pointer_ids: set[str] = set()
        retained_paths: set[str] = set()
        for record in records:
            if not isinstance(record, dict):
                diagnostics.append(make_diagnostic("GA-SOURCE-INVENTORY", ledger_path, "Every active source record must be an object."))
                continue
            source_id = record.get("source_id")
            if not isinstance(source_id, str):
                diagnostics.append(make_diagnostic("GA-SOURCE-INVENTORY", ledger_path, "Every active source record requires source_id."))
                continue
            by_id.setdefault(source_id, []).append(record)
            retained = record.get("retained_payload")
            prior = record.get("prior_observed_payload")
            frozen = FROZEN_SOURCE_IDENTITIES.get(source_id)
            if not isinstance(frozen, dict):
                diagnostics.append(make_diagnostic("GA-SOURCE-INVENTORY", ledger_path, "Active source_id is outside the frozen eight-source identity contract.", source_id))
            else:
                identity_mismatches = sorted(
                    field
                    for field in ("title", "publisher", "document_identifier", "exact_version", "publication_date")
                    if record.get(field) != frozen.get(field)
                )
                payload_identity = retained if isinstance(retained, dict) else prior if isinstance(prior, dict) else {}
                if payload_identity.get("path") != frozen.get("retained_path") or payload_identity.get("sha256") != frozen.get("sha256"):
                    identity_mismatches.append("payload path/digest")
                if identity_mismatches:
                    diagnostics.append(make_diagnostic("GA-STANDARDS-EVIDENCE-INCOMPLETE", ledger_path, f"Active source identity differs from the frozen retained-byte/prior-observation contract: {sorted(set(identity_mismatches))}.", source_id))
            if isinstance(retained, dict):
                retained_ids.add(source_id)
                retained_path = retained.get("path")
                if record.get("custody_state") != "retained_payload" or record.get("evidence_eligibility") != "eligible_for_proposed_mapping":
                    diagnostics.append(make_diagnostic("GA-SOURCE-INVENTORY", ledger_path, "A retained payload must be custody-state retained_payload and eligible only for proposed mapping.", source_id))
                if not isinstance(retained_path, str) or retained_path in retained_paths:
                    diagnostics.append(make_diagnostic("GA-SOURCE-PATH-DUPLICATE", ledger_path, "Retained source paths must be present and unique.", source_id))
                    continue
                retained_paths.add(retained_path)
                try:
                    raw = view.read_bytes(retained_path)
                except (OSError, ValueError):
                    diagnostics.append(make_diagnostic("GA-REFERENCE-DANGLING", ledger_path, f"Retained source path is absent: {retained_path!r}.", source_id))
                    continue
                if retained.get("sha256") != digest_bytes(raw):
                    diagnostics.append(make_diagnostic("GA-DIGEST-MISMATCH", retained_path, "Active retained-source digest does not match exact bytes.", source_id))
                if retained.get("byte_size") != len(raw):
                    diagnostics.append(make_diagnostic("GA-SOURCE-SIZE-MISMATCH", retained_path, "Active retained-source byte_size does not match exact bytes.", source_id))
                if Path(retained_path).suffix.lower() == ".jsonl":
                    lines = raw.splitlines()
                    parsed: Any = None
                    if not raw.endswith(b"\n") or len(lines) != 1:
                        diagnostics.append(make_diagnostic("GA-SOURCE-FORMAT", retained_path, "ISO Open Data retention must be exactly one newline-terminated JSONL object.", source_id))
                    else:
                        try:
                            parsed = strict_json_loads(lines[0].decode("utf-8"))
                        except (UnicodeDecodeError, json.JSONDecodeError, StrictJSONError):
                            parsed = None
                    if isinstance(parsed, dict):
                        reference = parsed.get("reference")
                        title = parsed.get("title")
                        english_title = title.get("en") if isinstance(title, dict) else None
                        edition = parsed.get("edition")
                        extracted = {
                            "title": f"{reference} {english_title}" if isinstance(reference, str) and isinstance(english_title, str) else None,
                            "document_identifier": {"state": "observed", "value": reference},
                            "exact_version": {"state": "observed", "value": f"{reference}, edition {edition}"} if isinstance(reference, str) and isinstance(edition, int) else None,
                            "publication_date": {"state": "observed", "value": parsed.get("publicationDate")},
                        }
                        mismatches = sorted(field for field, value in extracted.items() if record.get(field) != value)
                        if mismatches:
                            diagnostics.append(make_diagnostic("GA-STANDARDS-EVIDENCE-INCOMPLETE", retained_path, f"Structured retained bytes do not exactly derive ledger identity fields {mismatches}.", source_id))
                    else:
                        diagnostics.append(make_diagnostic("GA-SOURCE-FORMAT", retained_path, "Retained JSONL bytes are not one strict JSON object.", source_id))
            else:
                pointer_ids.add(source_id)
                prior_path = prior.get("path") if isinstance(prior, dict) else None
                if (
                    record.get("custody_state") != "pointer_only"
                    or record.get("evidence_eligibility") != "ineligible_pointer_only"
                    or not isinstance(prior, dict)
                    or prior.get("admissible_under_this_profile") is not False
                    or prior.get("distribution_payload_authorized") is not False
                ):
                    diagnostics.append(make_diagnostic("GA-SOURCE-INVENTORY", ledger_path, "A pointer-only record must disclose ineligible prior-observation metadata without re-admitting bytes.", source_id))
                if isinstance(prior_path, str) and view.is_file(prior_path):
                    diagnostics.append(make_diagnostic("GA-UNLEDGERED-SOURCE", prior_path, "Pointer-only historical payload bytes must be absent from the active public worktree.", source_id))

        duplicate_ids = sorted(source_id for source_id, matches in by_id.items() if len(matches) != 1)
        if (
            duplicate_ids
            or set(by_id) != V11_PUBLIC_PAYLOAD_SOURCE_IDS | V11_POINTER_SOURCE_IDS
            or retained_ids != V11_PUBLIC_PAYLOAD_SOURCE_IDS
            or pointer_ids != V11_POINTER_SOURCE_IDS
        ):
            diagnostics.append(make_diagnostic("GA-SOURCE-INVENTORY", ledger_path, f"Active source inventory must equal the exact four retained ISO plus four pointer-only source contract; duplicates={duplicate_ids}, retained={sorted(retained_ids)}, pointers={sorted(pointer_ids)}."))

        binding_issues = self.exact_artifact_binding_issues(view, crosswalk.get("source_ledger_ref"), ledger_path)
        if binding_issues:
            diagnostics.append(make_diagnostic("GA-STANDARDS-EVIDENCE-INCOMPLETE", crosswalk_path, f"Crosswalk source-ledger binding is stale or incomplete: {binding_issues}."))
        if crosswalk.get("lifecycle_status") != "proposed" or crosswalk.get("compliance_claimed") is not False:
            diagnostics.append(make_diagnostic("GA-STANDARDS-UNSUPPORTED-CLAIM", crosswalk_path, "The active crosswalk must remain proposed and must not claim compliance."))
        mapping_ids: list[str] = []
        for entry in entries:
            if not isinstance(entry, dict):
                diagnostics.append(make_diagnostic("GA-CROSSWALK-INVENTORY", crosswalk_path, "Every active crosswalk entry must be an object."))
                continue
            mapping_id = entry.get("mapping_id")
            if isinstance(mapping_id, str):
                mapping_ids.append(mapping_id)
            evidence_refs = entry.get("evidence_source_refs") if isinstance(entry.get("evidence_source_refs"), list) else []
            discovery_refs = entry.get("discovery_source_refs") if isinstance(entry.get("discovery_source_refs"), list) else []
            evidence_ids = [item.get("source_id") for item in evidence_refs if isinstance(item, dict)]
            discovery_ids = [item.get("source_id") for item in discovery_refs if isinstance(item, dict)]
            issues: list[str] = []
            for item, expected_pool, label in (
                *[(item, retained_ids, "evidence") for item in evidence_refs],
                *[(item, pointer_ids, "discovery") for item in discovery_refs],
            ):
                if not isinstance(item, dict) or item.get("version") != "1.1.0" or item.get("source_id") not in expected_pool:
                    issues.append(f"{label} source reference is unresolved, wrong-version, or evidence-ineligible: {item!r}")
            if len(evidence_ids) != len(set(evidence_ids)) or len(discovery_ids) != len(set(discovery_ids)) or set(evidence_ids) & set(discovery_ids):
                issues.append("evidence and discovery source references must be unique and disjoint")
            identity_ref = entry.get("identity_source_ref")
            identity_id = identity_ref.get("source_id") if isinstance(identity_ref, dict) else None
            identity_matches = by_id.get(identity_id, []) if isinstance(identity_id, str) else []
            if not isinstance(identity_ref, dict) or identity_ref.get("version") != "1.1.0" or identity_id not in set(evidence_ids) | set(discovery_ids) or len(identity_matches) != 1:
                issues.append("identity_source_ref must resolve exactly once among the entry's evidence/discovery references")
            else:
                identity = identity_matches[0]
                external = entry.get("external_reference") if isinstance(entry.get("external_reference"), dict) else {}
                parity = {
                    "publisher": identity.get("publisher"),
                    "title": {"state": "observed", "value": identity.get("title")},
                    "document_identifier": identity.get("document_identifier"),
                    "exact_version": identity.get("exact_version"),
                    "publication_date": identity.get("publication_date"),
                }
                mismatches = sorted(field for field, expected in parity.items() if external.get(field) != expected)
                if mismatches:
                    issues.append(f"external_reference does not exactly equal the selected ledger identity fields {mismatches}")
            state = entry.get("mapping_state")
            if state == "partial_mapping":
                if not evidence_ids:
                    issues.append("partial_mapping requires at least one eligible retained evidence source")
            elif state == "evidence_gap":
                if evidence_ids or not discovery_ids:
                    issues.append("evidence_gap requires no evidence refs and at least one pointer-only discovery ref")
            else:
                issues.append(f"mapping_state is not an allowed active state: {state!r}")
            if state == "partial_mapping":
                for field in ("scope", "comparator", "requirement_locator"):
                    value = entry.get(field)
                    if not isinstance(value, dict) or value.get("state") != "observed" or not isinstance(value.get("value"), str) or not value["value"].strip():
                        issues.append(f"{field} must be a nonempty observed exact measurement")
            if entry.get("lifecycle_status") != "proposed" or "not" not in str(entry.get("prohibited_interpretation", "")).lower():
                issues.append("mapping must remain proposed with an explicit prohibited interpretation")
            if issues:
                diagnostics.append(make_diagnostic("GA-STANDARDS-EVIDENCE-INCOMPLETE", crosswalk_path, f"Active standards mapping is ineligible: {sorted(set(issues))}.", mapping_id if isinstance(mapping_id, str) else None))
        if len(mapping_ids) != len(entries) or len(mapping_ids) != len(set(mapping_ids)):
            diagnostics.append(make_diagnostic("GA-STANDARDS-MAPPING-AMBIGUOUS", crosswalk_path, "Active standards mapping_id values must be present and unique."))
        return sorted(diagnostics, key=diagnostic_key)

    def historical_recovery_diagnostics(self, view: RepositoryView) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        recovery = self.read_view_json(view, HISTORICAL_RECOVERY_PATH)
        archived_index = self.read_view_json(view, HISTORICAL_INDEX_PATH)
        if not isinstance(recovery, dict) or not isinstance(archived_index, dict):
            return [make_diagnostic("GA-HISTORICAL-RECOVERY-INELIGIBLE", HISTORICAL_RECOVERY_PATH, "Historical recovery record or archived predecessor index is absent or malformed.")]
        diagnostics.extend(self.instance_diagnostics(recovery, HISTORICAL_RECOVERY_PATH))
        indexed_by_path: dict[str, list[dict[str, Any]]] = {}
        for item in archived_index.get("artifacts", []):
            binding = item.get("artifact") if isinstance(item, dict) else None
            original = binding.get("path") if isinstance(binding, dict) else None
            if isinstance(original, str):
                indexed_by_path.setdefault(original, []).append(binding)
        expected_classes = {
            "AGENTS.md": "digest_verified_reconstruction",
            "README.md": "digest_verified_reconstruction",
            "gate/decisions/OPERATOR_DECISION.template.json": "digest_verified_reconstruction",
            "manifests/manifest-release-ledger.json": "pre_overwrite_archival_copy",
        }
        recovered = recovery.get("recovered_artifacts")
        observed_originals: list[str] = []
        if not isinstance(recovered, list):
            recovered = []
        for entry in recovered:
            if not isinstance(entry, dict):
                continue
            original = entry.get("original_path")
            if isinstance(original, str):
                observed_originals.append(original)
            matches = indexed_by_path.get(original, []) if isinstance(original, str) else []
            binding = entry.get("recovered_binding")
            issues: list[str] = []
            if len(matches) != 1:
                issues.append(f"original predecessor index matches={len(matches)}")
            else:
                predecessor = matches[0]
                if entry.get("expected_sha256") != predecessor.get("sha256"):
                    issues.append("expected_sha256 does not equal predecessor index binding")
            if entry.get("recovery_class") != expected_classes.get(original):
                issues.append("recovery_class does not equal the exact path-specific recovery contract")
            if entry.get("digest_matches_predecessor_index") is not True:
                issues.append("digest_matches_predecessor_index is not true")
            recovered_path = binding.get("path") if isinstance(binding, dict) else None
            if not isinstance(recovered_path, str):
                issues.append("recovered path is absent")
            else:
                try:
                    raw = view.read_bytes(recovered_path)
                except (OSError, ValueError):
                    issues.append("recovered bytes are absent")
                else:
                    if binding.get("sha256") != digest_bytes(raw) or entry.get("expected_sha256") != digest_bytes(raw):
                        issues.append("recovered bytes do not match both recovered and expected digests")
                    if entry.get("expected_byte_size") != len(raw):
                        issues.append("recovered byte size does not equal expected_byte_size")
            if issues:
                diagnostics.append(make_diagnostic("GA-HISTORICAL-RECOVERY-INELIGIBLE", HISTORICAL_RECOVERY_PATH, f"Historical artifact recovery is ineligible: {sorted(set(issues))}.", original if isinstance(original, str) else None))
        if set(observed_originals) != set(expected_classes) or len(observed_originals) != len(set(observed_originals)):
            diagnostics.append(make_diagnostic("GA-HISTORICAL-RECOVERY-INELIGIBLE", HISTORICAL_RECOVERY_PATH, f"Recovered original paths must equal the exact four-path contract; observed={observed_originals}."))

        packet_paths = {
            "index": HISTORICAL_INDEX_PATH,
            "sidecar": HISTORICAL_SIDECAR_PATH,
            "validation_report": "gate/validation-reports/gate-a-validation-1.0.0.json",
        }
        packet_bindings = recovery.get("packet_bindings") if isinstance(recovery.get("packet_bindings"), dict) else {}
        for label, expected_path in packet_paths.items():
            issues = self.exact_artifact_binding_issues(
                view,
                packet_bindings.get(label),
                expected_path,
                require_target_identity=False,
            )
            if issues:
                diagnostics.append(make_diagnostic("GA-HISTORICAL-RECOVERY-INELIGIBLE", HISTORICAL_RECOVERY_PATH, f"Historical {label} binding is stale: {issues}."))
        try:
            archived_raw = view.read_bytes(HISTORICAL_INDEX_PATH)
            sidecar_raw = view.read_bytes(HISTORICAL_SIDECAR_PATH)
        except (OSError, ValueError):
            archived_raw = None
            sidecar_raw = None
        if archived_raw is not None:
            expected_sidecar = f"{digest_bytes(archived_raw)}  {INDEX_PATH}\n".encode("utf-8")
            if sidecar_raw != expected_sidecar:
                diagnostics.append(make_diagnostic("GA-HISTORICAL-RECOVERY-INELIGIBLE", HISTORICAL_SIDECAR_PATH, "Archived sidecar does not exactly bind the archived predecessor index bytes."))
        dispositions = recovery.get("public_dispositions") if isinstance(recovery.get("public_dispositions"), dict) else {}
        if (
            recovery.get("private_recovery_source_included") is not False
            or recovery.get("custody_continuity") != "interrupted_and_disclosed"
            or dispositions.get("recovery_derivation_publicly_replayable") is not False
            or dispositions.get("uninterrupted_custody_claimed") is not False
            or dispositions.get("predecessor_operator_accepted") is not False
            or dispositions.get("predecessor_published") is not False
            or dispositions.get("scientific_support_created") is not False
            or dispositions.get("current_gate_acceptance_created") is not False
        ):
            diagnostics.append(make_diagnostic("GA-HISTORICAL-RECOVERY-INELIGIBLE", HISTORICAL_RECOVERY_PATH, "Recovery must disclose interrupted custody, absent private source, unpublished/unaccepted predecessor, and no new authority."))
        return sorted(diagnostics, key=diagnostic_key)

    def public_custody_diagnostics(self, view: RepositoryView) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        paths = (
            PUBLIC_CUSTODY_PROFILE_PATH,
            ACTIVE_SOURCE_LEDGER_PATH,
            ACTIVE_STANDARDS_CROSSWALK_PATH,
            FRONTIER_DISCOVERY_REGISTER_PATH,
            PUBLIC_DISTRIBUTION_INVENTORY_PATH,
            PUBLIC_RIGHTS_REVALIDATION_PATH,
            SUCCESSOR_PUBLIC_RIGHTS_REVALIDATION_PATH,
            HISTORICAL_RECOVERY_PATH,
        )
        documents: dict[str, dict[str, Any]] = {}
        for relative in paths:
            document = self.read_view_json(view, relative)
            if not isinstance(document, dict):
                diagnostics.append(make_diagnostic("GA-PUBLIC-CUSTODY-CONTRACT", relative, "Required public custody artifact is absent or malformed."))
                continue
            documents[relative] = document
            diagnostics.extend(self.instance_diagnostics(document, relative))
        ledger = documents.get(ACTIVE_SOURCE_LEDGER_PATH, {})
        profile = documents.get(PUBLIC_CUSTODY_PROFILE_PATH, {})
        frontier = documents.get(FRONTIER_DISCOVERY_REGISTER_PATH, {})
        inventory = documents.get(PUBLIC_DISTRIBUTION_INVENTORY_PATH, {})
        rights = documents.get(PUBLIC_RIGHTS_REVALIDATION_PATH, {})
        successor_rights = documents.get(SUCCESSOR_PUBLIC_RIGHTS_REVALIDATION_PATH, {})
        current_rights = self.read_view_json(view, CURRENT_PUBLIC_RIGHTS_REVALIDATION_PATH)
        if isinstance(current_rights, dict):
            diagnostics.extend(self.instance_diagnostics(current_rights, CURRENT_PUBLIC_RIGHTS_REVALIDATION_PATH))
        else:
            current_rights = {}
        if not all(isinstance(item, dict) for item in (ledger, profile, frontier, inventory, rights)):
            return sorted(diagnostics, key=diagnostic_key)

        receipt_schema_specs: dict[int, dict[str, Any]] = {
            2: {
                "version": "1.1.1",
                "receipt_path": SUCCESSOR_PUBLIC_RECEIPT_PATH,
                "schema_path": "schemas/public-distribution-receipt-1.1.1.schema.json",
                "schema_id": "https://schemas.reiyah.invalid/gate-a/1.1.1/public-distribution-receipt.schema.json",
                "artifact_id": "reiyah.artifact.public-distribution-receipt-1.1.1",
                "receipt_id": "reiyah.public-distribution-receipt.governance-correction-publication",
                "authorization": {
                    "basis_state": "observed_current_operator_instruction",
                    "recorded_date": "2026-08-24",
                    "authorized_action": "publish_exact_static_gate_a_1.1.1_governance_correction",
                    "scope_limit": "Exact static Gate A 1.1.1 governance-correction packet and the unchanged four eligible retained payloads; no new evidence, private data, runtime, deployment, or unauthorized source payloads.",
                    "operator_identity_authentication": "not_evaluated",
                    "ga17_effect": "not_evaluated",
                    "gate_a_acceptance_effect": "none",
                    "scientific_publication_acceptance_effect": "none",
                    "runtime_execution_effect": "none",
                },
                "bindings": {
                    "rights_revalidation_ref": {
                        "artifact_id": "reiyah.artifact.public-rights-revalidation-2026-08-24",
                        "version": "1.1.1",
                        "path": SUCCESSOR_PUBLIC_RIGHTS_REVALIDATION_PATH,
                    },
                    "published_index_ref": {
                        "artifact_id": "reiyah.artifact.gate-a-index-1.1.1",
                        "version": "1.1.1",
                        "path": INDEX_PATH,
                    },
                    "validation_report_ref": {
                        "artifact_id": "reiyah.validation-report.gate-a-1.1.1",
                        "version": "1.1.1",
                        "path": HISTORICAL_V111_REPORT_PATH,
                    },
                    "prior_receipt_ref": {
                        "artifact_id": "reiyah.artifact.public-distribution-receipt-1.1.0",
                        "version": "1.1.0",
                        "path": INITIAL_PUBLIC_RECEIPT_PATH,
                        "sha256": INITIAL_PUBLIC_RECEIPT_DIGEST,
                        "byte_size": 6857,
                    },
                },
            },
            3: {
                "version": "1.1.2",
                "receipt_path": "gate/public-distribution-receipts/reiyah.public-distribution-receipt-1.1.2.json",
                "schema_path": "schemas/public-distribution-receipt-1.1.2.schema.json",
                "schema_id": "https://schemas.reiyah.invalid/gate-a/1.1.2/public-distribution-receipt.schema.json",
                "artifact_id": "reiyah.artifact.public-distribution-receipt-1.1.2",
                "receipt_id": "reiyah.public-distribution-receipt.documentation-continuity-publication",
                "authorization": {
                    "basis_state": "observed_current_operator_instruction",
                    "recorded_date": "2026-08-24",
                    "authorized_action": "publish_exact_static_gate_a_1.1.2_documentation_continuity_successor",
                    "scope_limit": "Exact static Gate A 1.1.2 documentation-and-continuity successor packet and the unchanged four eligible retained payloads; no new scientific evidence, private data, runtime, deployment, or unauthorized source payloads.",
                    "operator_identity_authentication": "not_evaluated",
                    "ga17_effect": "not_evaluated",
                    "gate_a_acceptance_effect": "none",
                    "scientific_publication_acceptance_effect": "none",
                    "runtime_execution_effect": "none",
                },
                "bindings": {
                    "rights_revalidation_ref": {
                        "artifact_id": "reiyah.artifact.public-rights-revalidation-2026-08-24-1.1.2",
                        "version": "1.1.2",
                        "path": CURRENT_PUBLIC_RIGHTS_REVALIDATION_PATH,
                    },
                    "published_index_ref": {
                        "artifact_id": "reiyah.artifact.gate-a-index-1.1.2",
                        "version": "1.1.2",
                        "path": INDEX_PATH,
                    },
                    "validation_report_ref": {
                        "artifact_id": "reiyah.validation-report.gate-a-1.1.2",
                        "version": "1.1.2",
                        "path": REPORT_PATH,
                    },
                    "prior_receipt_ref": {
                        "artifact_id": "reiyah.artifact.public-distribution-receipt-1.1.1",
                        "version": "1.1.1",
                        "path": SUCCESSOR_PUBLIC_RECEIPT_PATH,
                        "sha256": SUCCESSOR_PUBLIC_RECEIPT_DIGEST,
                        "byte_size": SUCCESSOR_PUBLIC_RECEIPT_SIZE,
                    },
                },
            },
        }
        receipt_authorizations = {
            sequence: spec["authorization"]
            for sequence, spec in receipt_schema_specs.items()
        }
        common_receipt_bindings = {
            "custody_profile_ref": {
                "artifact_id": "reiyah.artifact.public-evidence-custody-profile-1.1.0",
                "version": "1.1.0",
                "path": PUBLIC_CUSTODY_PROFILE_PATH,
            },
            "source_ledger_ref": {
                "artifact_id": "reiyah.artifact.source-ledger-1.1.0",
                "version": "1.1.0",
                "path": ACTIVE_SOURCE_LEDGER_PATH,
            },
            "frontier_discovery_register_ref": {
                "artifact_id": "reiyah.artifact.frontier-discovery-register-1.1.0",
                "version": "1.1.0",
                "path": FRONTIER_DISCOVERY_REGISTER_PATH,
            },
            "distribution_inventory_ref": {
                "artifact_id": "reiyah.artifact.public-distribution-inventory-1.1.0",
                "version": "1.1.0",
                "path": PUBLIC_DISTRIBUTION_INVENTORY_PATH,
            },
        }

        for sequence, spec in receipt_schema_specs.items():
            schema_path = spec["schema_path"]
            schema = self.read_view_json(view, schema_path)
            authorization_schema = (
                schema.get("$defs", {}).get("successorDistributionAuthorization")
                if isinstance(schema, dict) and isinstance(schema.get("$defs"), dict)
                else None
            )
            authorization_properties = (
                authorization_schema.get("properties")
                if isinstance(authorization_schema, dict)
                and isinstance(authorization_schema.get("properties"), dict)
                else {}
            )
            authorization_required = (
                authorization_schema.get("required")
                if isinstance(authorization_schema, dict)
                and isinstance(authorization_schema.get("required"), list)
                else []
            )
            observed_authorization = {
                field: value.get("const") if isinstance(value, dict) else None
                for field, value in authorization_properties.items()
            }

            def constrained_binding_constants(field: str) -> dict[str, Any]:
                properties = schema.get("properties") if isinstance(schema, dict) else None
                node = properties.get(field) if isinstance(properties, dict) else None
                branches = node.get("allOf") if isinstance(node, dict) else None
                constants: dict[str, Any] = {}
                if isinstance(branches, list):
                    for branch in branches:
                        branch_properties = branch.get("properties") if isinstance(branch, dict) else None
                        if not isinstance(branch_properties, dict):
                            continue
                        for name, definition in branch_properties.items():
                            if isinstance(definition, dict) and "const" in definition:
                                constants[name] = definition.get("const")
                return constants

            expected_bindings = {**common_receipt_bindings, **spec["bindings"]}
            required = (
                schema.get("required")
                if isinstance(schema, dict) and isinstance(schema.get("required"), list)
                else []
            )
            properties = (
                schema.get("properties")
                if isinstance(schema, dict) and isinstance(schema.get("properties"), dict)
                else {}
            )
            readback = properties.get("remote_readback") if isinstance(properties.get("remote_readback"), dict) else {}
            readback_required = readback.get("required") if isinstance(readback.get("required"), list) else []
            readback_properties = readback.get("properties") if isinstance(readback.get("properties"), dict) else {}
            if (
                not isinstance(schema, dict)
                or schema.get("$id") != spec["schema_id"]
                or properties.get("distribution_authorization", {}).get("$ref") != "#/$defs/successorDistributionAuthorization"
                or properties.get("artifact_id", {}).get("const") != spec["artifact_id"]
                or properties.get("receipt_id", {}).get("const") != spec["receipt_id"]
                or observed_authorization != spec["authorization"]
                or set(authorization_required) != set(spec["authorization"])
                or authorization_schema.get("additionalProperties") is not False
                or properties.get("receipt_sequence", {}).get("const") != sequence
                or "validation_report_ref" not in required
                or "tree_contains_exact_validation_report" not in readback_required
                or readback_properties.get("tree_contains_exact_validation_report", {}).get("const") is not True
                or any(constrained_binding_constants(field) != expected for field, expected in expected_bindings.items())
            ):
                diagnostics.append(
                    make_diagnostic(
                        "GA-PUBLIC-DISTRIBUTION-RECEIPT",
                        schema_path,
                        f"The event-specific receipt schema must freeze sequence {sequence}, its exact prior receipt, fresh rights observation, packet index/report identities, and static-only authorization without creating runtime, acceptance, scientific, or GA-17 authority.",
                    )
                )

        ledger_records = ledger.get("records") if isinstance(ledger.get("records"), list) else []
        ledger_by_id = {
            item.get("source_id"): item
            for item in ledger_records
            if isinstance(item, dict) and isinstance(item.get("source_id"), str)
        }
        retained_payload_ids = {
            source_id for source_id, record in ledger_by_id.items()
            if isinstance(record.get("retained_payload"), dict)
        }
        distributable_ids = {
            source_id
            for source_id, record in ledger_by_id.items()
            if source_id in retained_payload_ids
            and record.get("record_role") == "retained_source"
            and record.get("custody_state") == "retained_payload"
            and record.get("redistribution_state") in {"permitted_with_attribution", "permitted_with_conditions"}
            and record.get("evidence_eligibility") == "eligible_for_proposed_mapping"
        }
        pointer_ids = set(ledger_by_id) - distributable_ids
        if distributable_ids != V11_PUBLIC_PAYLOAD_SOURCE_IDS or pointer_ids != V11_POINTER_SOURCE_IDS:
            diagnostics.append(make_diagnostic("GA-PUBLIC-CUSTODY-CONTRACT", ACTIVE_SOURCE_LEDGER_PATH, f"Public custody must preserve the exact four distributable ISO and four pointer-only sources; distributable={sorted(distributable_ids)}, pointers={sorted(pointer_ids)}."))
        frontier_records = frontier.get("records") if isinstance(frontier.get("records"), list) else []
        frontier_ids = [item.get("discovery_id") for item in frontier_records if isinstance(item, dict)]
        if len(frontier_ids) != len(frontier_records) or len(frontier_ids) != len(set(frontier_ids)):
            diagnostics.append(make_diagnostic("GA-PUBLIC-CUSTODY-CONTRACT", FRONTIER_DISCOVERY_REGISTER_PATH, "Frontier discovery IDs must be present and unique."))
        for item in frontier_records:
            if not isinstance(item, dict):
                continue
            if (
                item.get("custody_state") != "pointer_only"
                or item.get("redistribution_state") != "pointer_metadata_only"
                or item.get("evidence_eligibility") != "ineligible_pointer_only"
                or item.get("retained_payload") is not None
                or item.get("payload_redistribution_authorized") is not False
                or item.get("claims_admitted") is not False
            ):
                diagnostics.append(make_diagnostic("GA-PUBLIC-CUSTODY-CONTRACT", FRONTIER_DISCOVERY_REGISTER_PATH, "Every frontier record must remain pointer-only, payload-absent, evidence-ineligible, and non-authoritative.", item.get("discovery_id") if isinstance(item.get("discovery_id"), str) else None))
        if (
            frontier.get("claims_admitted") is not False
            or frontier.get("payload_distribution_authorized") is not False
            or frontier.get("runtime_execution_authorized") is not False
        ):
            diagnostics.append(make_diagnostic("GA-PUBLIC-CUSTODY-CONTRACT", FRONTIER_DISCOVERY_REGISTER_PATH, "Frontier register cannot admit claims, payload distribution, or runtime execution."))

        for relative, binding, target in (
            (ACTIVE_SOURCE_LEDGER_PATH, ledger.get("custody_profile_ref"), PUBLIC_CUSTODY_PROFILE_PATH),
            (FRONTIER_DISCOVERY_REGISTER_PATH, frontier.get("custody_profile_ref"), PUBLIC_CUSTODY_PROFILE_PATH),
            (PUBLIC_DISTRIBUTION_INVENTORY_PATH, inventory.get("source_ledger_ref"), ACTIVE_SOURCE_LEDGER_PATH),
            (PUBLIC_DISTRIBUTION_INVENTORY_PATH, inventory.get("frontier_discovery_register_ref"), FRONTIER_DISCOVERY_REGISTER_PATH),
            (PUBLIC_DISTRIBUTION_INVENTORY_PATH, inventory.get("rights_revalidation_ref"), PUBLIC_RIGHTS_REVALIDATION_PATH),
        ):
            issues = self.exact_artifact_binding_issues(view, binding, target)
            if issues:
                diagnostics.append(make_diagnostic("GA-PUBLIC-CUSTODY-CONTRACT", relative, f"Custody graph binding for {target!r} is stale or incomplete: {issues}."))

        inventory_entries = inventory.get("entries") if isinstance(inventory.get("entries"), list) else []
        inventory_ids: list[str] = []
        include_ids: set[str] = set()
        pointer_inventory_ids: set[str] = set()
        for entry in inventory_entries:
            if not isinstance(entry, dict):
                continue
            source_ref = entry.get("source_ref") if isinstance(entry.get("source_ref"), dict) else {}
            source_id = source_ref.get("source_id")
            inventory_ids.append(source_id if isinstance(source_id, str) else "")
            record = ledger_by_id.get(source_id) if isinstance(source_id, str) else None
            issues: list[str] = []
            if source_ref.get("version") != "1.1.0" or not isinstance(record, dict):
                issues.append("source_ref does not resolve exact active-ledger identity/version")
            action = entry.get("distribution_action")
            if action == "include_payload":
                if isinstance(source_id, str):
                    include_ids.add(source_id)
                if not isinstance(record, dict) or source_id not in distributable_ids or entry.get("payload") != record.get("retained_payload"):
                    issues.append("include_payload must exactly equal a retained, redistributable, proposed-mapping-eligible ledger payload")
                if not entry.get("attribution") or not entry.get("caveats"):
                    issues.append("included payload requires attribution and caveats")
            elif action in {"publish_pointer_only", "exclude"}:
                if isinstance(source_id, str):
                    pointer_inventory_ids.add(source_id)
                if not isinstance(record, dict) or source_id not in pointer_ids or entry.get("payload") is not None:
                    issues.append("pointer/excluded action must bind a non-distributable ledger record and null inventory payload")
            else:
                issues.append(f"unsupported distribution_action {action!r}")
            if issues:
                diagnostics.append(make_diagnostic("GA-PUBLIC-CUSTODY-CONTRACT", PUBLIC_DISTRIBUTION_INVENTORY_PATH, f"Distribution entry is inconsistent with the active ledger: {sorted(set(issues))}.", source_id if isinstance(source_id, str) else None))
        if len(inventory_ids) != len(set(inventory_ids)) or set(inventory_ids) != set(ledger_by_id) or include_ids != distributable_ids or pointer_inventory_ids != pointer_ids:
            diagnostics.append(make_diagnostic("GA-PUBLIC-CUSTODY-CONTRACT", PUBLIC_DISTRIBUTION_INVENTORY_PATH, f"Inventory entries/actions must exactly partition the active ledger by eligibility; included={sorted(include_ids)}, distributable={sorted(distributable_ids)}, pointer_actions={sorted(pointer_inventory_ids)}, non_distributable={sorted(pointer_ids)}."))
        count_checks = {
            "authorized_payload_count": len(distributable_ids),
            "public_payload_count": len(distributable_ids),
            "pointer_only_count": len(pointer_ids),
            "discovery_pointer_count": len(frontier_records),
        }
        for field, expected in count_checks.items():
            if inventory.get(field) != expected:
                diagnostics.append(make_diagnostic("GA-PUBLIC-CUSTODY-CONTRACT", PUBLIC_DISTRIBUTION_INVENTORY_PATH, f"{field} must equal recomputed count {expected}."))
        shared_false_fields = (
            "distribution_executed",
            "gate_a_acceptance_conferred",
            "scientific_publication_acceptance_conferred",
        )
        for document, relative in ((profile, PUBLIC_CUSTODY_PROFILE_PATH), (inventory, PUBLIC_DISTRIBUTION_INVENTORY_PATH)):
            if any(document.get(field) is not False for field in shared_false_fields) or document.get("ga17_status") != "not_evaluated" or document.get("runtime_execution_authorized") is not False:
                diagnostics.append(make_diagnostic("GA-PUBLIC-CUSTODY-CONTRACT", relative, "Pre-distribution custody artifacts must remain unexecuted, runtime-free, non-accepting, and GA-17 not_evaluated."))
        if profile.get("authorized_payload_count") != len(distributable_ids) or profile.get("scientific_support_claimed") is not False or profile.get("compliance_claimed") is not False:
            diagnostics.append(make_diagnostic("GA-PUBLIC-CUSTODY-CONTRACT", PUBLIC_CUSTODY_PROFILE_PATH, "Custody profile payload count and non-authority fields do not equal the active retained-source boundary."))

        covered = rights.get("covered_payload_source_ids")
        excluded = rights.get("excluded_pointer_source_ids")
        basis = rights.get("basis_observations") if isinstance(rights.get("basis_observations"), list) else []
        expected_urls = [
            "https://www.iso.org/open-data.html#iso_deliverables_metadata",
            "https://www.nist.gov/open/copyright-fair-use-and-licensing-statements-srd-data-software-and-technical-series-publications",
        ]
        observed_urls = [item.get("official_url") for item in basis if isinstance(item, dict)]
        nist_pointer_ids = {
            source_id for source_id in pointer_ids
            if source_id.startswith("src.nist.")
            and isinstance(ledger_by_id[source_id].get("prior_observed_payload"), dict)
        }
        if (
            not isinstance(covered, list)
            or set(covered) != distributable_ids
            or len(covered) != len(set(covered))
            or not isinstance(excluded, list)
            or set(excluded) != nist_pointer_ids
            or len(excluded) != len(set(excluded))
            or observed_urls != expected_urls
            or rights.get("all_included_payloads_covered") is not True
            or rights.get("preflight_outcome") != "included_iso_basis_consistent_nist_payload_excluded"
        ):
            diagnostics.append(make_diagnostic("GA-PUBLIC-CUSTODY-CONTRACT", PUBLIC_RIGHTS_REVALIDATION_PATH, "Rights preflight must exactly cover included ISO payloads, exclude NIST pointer payloads, and preserve the canonical ISO/NIST observation order/outcome."))
        observed_at = parse_exact_utc(rights.get("observed_at"))
        if observed_at is None or any(parse_exact_utc(item.get("observed_at")) != observed_at for item in basis if isinstance(item, dict)):
            diagnostics.append(make_diagnostic("GA-PUBLIC-CUSTODY-CONTRACT", PUBLIC_RIGHTS_REVALIDATION_PATH, "Rights observations must use one exact valid UTC observation time."))
        if (
            rights.get("distribution_authorization_created") is not False
            or rights.get("qualified_legal_review_performed") is not False
            or rights.get("legal_conclusion_created") is not False
            or rights.get("gate_a_acceptance_conferred") is not False
            or rights.get("ga17_status") != "not_evaluated"
        ):
            diagnostics.append(make_diagnostic("GA-PUBLIC-CUSTODY-CONTRACT", PUBLIC_RIGHTS_REVALIDATION_PATH, "Rights observation cannot create legal/operator authority, acceptance, or GA-17 evaluation."))

        successor_basis = successor_rights.get("basis_observations") if isinstance(successor_rights.get("basis_observations"), list) else []
        successor_observed_at = parse_exact_utc(successor_rights.get("observed_at"))
        prior_observed_at = parse_exact_utc(rights.get("observed_at"))
        successor_issues = self.exact_artifact_binding_issues(
            view,
            successor_rights.get("prior_observation_ref"),
            PUBLIC_RIGHTS_REVALIDATION_PATH,
        ) if isinstance(successor_rights, dict) else ["successor rights observation is absent"]
        if (
            not isinstance(successor_rights, dict)
            or successor_rights.get("schema_id") != "https://schemas.reiyah.invalid/gate-a/1.1.1/public-rights-revalidation.schema.json"
            or successor_rights.get("version") != "1.1.1"
            or successor_issues
            or successor_observed_at is None
            or prior_observed_at is None
            or successor_observed_at <= prior_observed_at
            or any(parse_exact_utc(item.get("observed_at")) != successor_observed_at for item in successor_basis if isinstance(item, dict))
            or [item.get("official_url") for item in successor_basis if isinstance(item, dict)] != expected_urls
            or set(successor_rights.get("covered_payload_source_ids", [])) != distributable_ids
            or set(successor_rights.get("excluded_pointer_source_ids", [])) != nist_pointer_ids
            or successor_rights.get("all_included_payloads_covered") is not True
            or successor_rights.get("preflight_outcome") != "included_iso_basis_consistent_nist_payload_excluded"
            or successor_rights.get("distribution_authorization_created") is not False
            or successor_rights.get("qualified_legal_review_performed") is not False
            or successor_rights.get("legal_conclusion_created") is not False
            or successor_rights.get("gate_a_acceptance_conferred") is not False
            or successor_rights.get("ga17_status") != "not_evaluated"
        ):
            diagnostics.append(make_diagnostic("GA-PUBLIC-CUSTODY-CONTRACT", SUCCESSOR_PUBLIC_RIGHTS_REVALIDATION_PATH, f"The required successor rights observation must exactly and chronologically extend the immutable initial observation while preserving the same four-payload/two-NIST-pointer non-authority boundary; prior_issues={successor_issues}."))

        current_basis = current_rights.get("basis_observations") if isinstance(current_rights.get("basis_observations"), list) else []
        current_observed_at = parse_exact_utc(current_rights.get("observed_at"))
        current_prior_observed_at = parse_exact_utc(successor_rights.get("observed_at"))
        current_issues = self.exact_artifact_binding_issues(
            view,
            current_rights.get("prior_observation_ref"),
            SUCCESSOR_PUBLIC_RIGHTS_REVALIDATION_PATH,
        ) if isinstance(current_rights, dict) else ["current rights observation is absent"]
        if current_rights and (
            current_rights.get("schema_id") != "https://schemas.reiyah.invalid/gate-a/1.1.2/public-rights-revalidation.schema.json"
            or current_rights.get("version") != "1.1.2"
            or current_issues
            or current_observed_at is None
            or current_prior_observed_at is None
            or current_observed_at <= current_prior_observed_at
            or any(parse_exact_utc(item.get("observed_at")) != current_observed_at for item in current_basis if isinstance(item, dict))
            or [item.get("official_url") for item in current_basis if isinstance(item, dict)] != expected_urls
            or set(current_rights.get("covered_payload_source_ids", [])) != distributable_ids
            or set(current_rights.get("excluded_pointer_source_ids", [])) != nist_pointer_ids
            or current_rights.get("all_included_payloads_covered") is not True
            or current_rights.get("preflight_outcome") != "included_iso_basis_consistent_nist_payload_excluded"
            or current_rights.get("distribution_authorization_created") is not False
            or current_rights.get("qualified_legal_review_performed") is not False
            or current_rights.get("legal_conclusion_created") is not False
            or current_rights.get("gate_a_acceptance_conferred") is not False
            or current_rights.get("ga17_status") != "not_evaluated"
        ):
            diagnostics.append(make_diagnostic("GA-PUBLIC-CUSTODY-CONTRACT", CURRENT_PUBLIC_RIGHTS_REVALIDATION_PATH, f"The Gate A 1.1.2 rights observation must exactly and chronologically extend the immutable 1.1.1 observation while preserving the same four-payload/two-NIST-pointer non-authority boundary; prior_issues={current_issues}."))

        try:
            historical_v11_index_raw = view.read_bytes(HISTORICAL_V11_INDEX_PATH)
            historical_v11_sidecar = view.read_text(HISTORICAL_V11_SIDECAR_PATH)
        except (OSError, UnicodeDecodeError, ValueError):
            historical_v11_index_raw = None
            historical_v11_sidecar = None
        expected_historical_sidecar = f"{HISTORICAL_V11_INDEX_DIGEST}  {INDEX_PATH}\n"
        if (
            historical_v11_index_raw is None
            or digest_bytes(historical_v11_index_raw) != HISTORICAL_V11_INDEX_DIGEST
            or historical_v11_sidecar != expected_historical_sidecar
        ):
            diagnostics.append(
                make_diagnostic(
                    "GA-PUBLIC-DISTRIBUTION-RECEIPT",
                    HISTORICAL_V11_INDEX_PATH,
                    "The immutable Gate A 1.1.0 index snapshot and sidecar must preserve the exact bytes bound by the initial public receipt.",
                )
            )

        try:
            historical_v111_index_raw = view.read_bytes(HISTORICAL_V111_INDEX_PATH)
            historical_v111_sidecar = view.read_text(HISTORICAL_V111_SIDECAR_PATH)
        except (OSError, UnicodeDecodeError, ValueError):
            historical_v111_index_raw = None
            historical_v111_sidecar = None
        expected_historical_v111_sidecar = f"{HISTORICAL_V111_INDEX_DIGEST}  {INDEX_PATH}\n"
        if (
            historical_v111_index_raw is None
            or digest_bytes(historical_v111_index_raw) != HISTORICAL_V111_INDEX_DIGEST
            or historical_v111_sidecar != expected_historical_v111_sidecar
        ):
            diagnostics.append(
                make_diagnostic(
                    "GA-PUBLIC-DISTRIBUTION-RECEIPT",
                    HISTORICAL_V111_INDEX_PATH,
                    "The immutable Gate A 1.1.1 index snapshot and sidecar must preserve the exact bytes bound by receipt sequence two.",
                )
            )

        receipt_paths = sorted(
            relative for relative in view.iter_files()
            if re.fullmatch(r"gate/public-distribution-receipts/reiyah\.public-distribution-receipt-[a-z0-9.-]+\.json", relative)
        )
        try:
            initial_receipt_raw = view.read_bytes(INITIAL_PUBLIC_RECEIPT_PATH)
        except (OSError, ValueError):
            initial_receipt_raw = None
        if initial_receipt_raw is None or digest_bytes(initial_receipt_raw) != INITIAL_PUBLIC_RECEIPT_DIGEST:
            diagnostics.append(
                make_diagnostic(
                    "GA-PUBLIC-DISTRIBUTION-RECEIPT",
                    INITIAL_PUBLIC_RECEIPT_PATH,
                    "The excluded initial public receipt must remain present at its exact path with immutable published digest d805ad1b…; semantic validity cannot substitute for byte identity.",
                )
            )
        try:
            successor_receipt_raw = view.read_bytes(SUCCESSOR_PUBLIC_RECEIPT_PATH)
        except (OSError, ValueError):
            successor_receipt_raw = None
        if (
            successor_receipt_raw is None
            or digest_bytes(successor_receipt_raw) != SUCCESSOR_PUBLIC_RECEIPT_DIGEST
            or len(successor_receipt_raw) != SUCCESSOR_PUBLIC_RECEIPT_SIZE
        ):
            diagnostics.append(
                make_diagnostic(
                    "GA-PUBLIC-DISTRIBUTION-RECEIPT",
                    SUCCESSOR_PUBLIC_RECEIPT_PATH,
                    "The excluded sequence-two receipt must remain present at its exact path, digest, and byte size; semantic validity cannot substitute for byte identity.",
                )
            )
        receipts: list[tuple[str, dict[str, Any]]] = []
        for relative in receipt_paths:
            receipt = self.read_view_json(view, relative)
            if not isinstance(receipt, dict):
                diagnostics.append(make_diagnostic("GA-PUBLIC-DISTRIBUTION-RECEIPT", relative, "Distribution receipt is malformed."))
                continue
            receipts.append((relative, receipt))
            diagnostics.extend(self.instance_diagnostics(receipt, relative))
            issues: list[str] = []
            receipt_sequence = receipt.get("receipt_sequence")
            if receipt_sequence == 1:
                if (
                    relative != INITIAL_PUBLIC_RECEIPT_PATH
                    or receipt.get("schema_id") != "https://schemas.reiyah.invalid/gate-a/1.1.0/public-distribution-receipt.schema.json"
                    or receipt.get("schema_version") != "1.1.0"
                    or receipt.get("version") != "1.1.0"
                ):
                    issues.append("receipt sequence 1 must be the exact immutable 1.1.0 initial receipt contract")
            elif receipt_sequence in receipt_schema_specs:
                receipt_spec = receipt_schema_specs[receipt_sequence]
                if (
                    relative != receipt_spec["receipt_path"]
                    or receipt.get("schema_id") != receipt_spec["schema_id"]
                    or receipt.get("schema_version") != receipt_spec["version"]
                    or receipt.get("version") != receipt_spec["version"]
                    or receipt.get("artifact_id") != receipt_spec["artifact_id"]
                    or receipt.get("receipt_id") != receipt_spec["receipt_id"]
                    or receipt.get("distribution_authorization") != receipt_authorizations[receipt_sequence]
                ):
                    issues.append(f"receipt sequence {receipt_sequence} must use its exact event schema/version and static-only authorization")
            else:
                issues.append("this packet permits only immutable receipt sequence 1 and versioned successor sequences 2 and 3")
            for field, target in (
                ("custody_profile_ref", PUBLIC_CUSTODY_PROFILE_PATH),
                ("source_ledger_ref", ACTIVE_SOURCE_LEDGER_PATH),
                ("frontier_discovery_register_ref", FRONTIER_DISCOVERY_REGISTER_PATH),
                ("distribution_inventory_ref", PUBLIC_DISTRIBUTION_INVENTORY_PATH),
            ):
                issues.extend(f"{field}: {issue}" for issue in self.exact_artifact_binding_issues(view, receipt.get(field), target))

            rights_binding = receipt.get("rights_revalidation_ref") if isinstance(receipt.get("rights_revalidation_ref"), dict) else {}
            receipt_rights_path = rights_binding.get("path")
            allowed_rights_contracts = {
                PUBLIC_RIGHTS_REVALIDATION_PATH: (
                    "https://schemas.reiyah.invalid/gate-a/1.1.0/public-rights-revalidation.schema.json",
                    "1.0.0",
                ),
                SUCCESSOR_PUBLIC_RIGHTS_REVALIDATION_PATH: (
                    "https://schemas.reiyah.invalid/gate-a/1.1.1/public-rights-revalidation.schema.json",
                    "1.1.1",
                ),
                CURRENT_PUBLIC_RIGHTS_REVALIDATION_PATH: (
                    "https://schemas.reiyah.invalid/gate-a/1.1.2/public-rights-revalidation.schema.json",
                    "1.1.2",
                ),
            }
            receipt_rights: dict[str, Any] = {}
            expected_rights_contract = allowed_rights_contracts.get(receipt_rights_path)
            if expected_rights_contract is None:
                issues.append("rights_revalidation_ref path is not an allowed versioned rights observation")
            else:
                issues.extend(
                    f"rights_revalidation_ref: {issue}"
                    for issue in self.exact_artifact_binding_issues(view, rights_binding, receipt_rights_path)
                )
                candidate_rights = self.read_view_json(view, receipt_rights_path)
                if isinstance(candidate_rights, dict):
                    receipt_rights = candidate_rights
                    diagnostics.extend(self.instance_diagnostics(receipt_rights, receipt_rights_path))
                    expected_schema_id, expected_version = expected_rights_contract
                    if receipt_rights.get("schema_id") != expected_schema_id or receipt_rights.get("version") != expected_version:
                        issues.append("rights observation schema/version does not match its versioned path")
                else:
                    issues.append("rights observation target is absent or malformed")
            expected_rights_path_by_sequence = {
                1: PUBLIC_RIGHTS_REVALIDATION_PATH,
                2: SUCCESSOR_PUBLIC_RIGHTS_REVALIDATION_PATH,
                3: CURRENT_PUBLIC_RIGHTS_REVALIDATION_PATH,
            }
            if receipt_rights_path != expected_rights_path_by_sequence.get(receipt_sequence):
                issues.append("receipt sequence must bind its exact event-specific rights observation path")

            index_binding = receipt.get("published_index_ref") if isinstance(receipt.get("published_index_ref"), dict) else {}
            index_version = index_binding.get("version")
            if (
                receipt_sequence == 1
                and index_version == "1.1.0"
                and index_binding.get("artifact_id") == "reiyah.artifact.gate-a-index-1.1.0"
                and index_binding.get("sha256") == HISTORICAL_V11_INDEX_DIGEST
            ):
                index_physical_path = HISTORICAL_V11_INDEX_PATH
            elif (
                receipt_sequence == 2
                and index_version == "1.1.1"
                and index_binding.get("artifact_id") == "reiyah.artifact.gate-a-index-1.1.1"
                and index_binding.get("sha256") == HISTORICAL_V111_INDEX_DIGEST
            ):
                index_physical_path = HISTORICAL_V111_INDEX_PATH
            elif (
                receipt_sequence == 3
                and index_version == "1.1.2"
                and index_binding.get("artifact_id") == "reiyah.artifact.gate-a-index-1.1.2"
            ):
                index_physical_path = INDEX_PATH
            else:
                index_physical_path = None
                issues.append("published_index_ref must bind the exact historical 1.1.0/1.1.1 index for sequences 1/2 or the current 1.1.2 index for sequence 3")
            if index_physical_path is not None:
                issues.extend(
                    f"published_index_ref: {issue}"
                    for issue in self.exact_artifact_binding_issues(
                        view,
                        index_binding,
                        INDEX_PATH,
                        physical_path=index_physical_path,
                    )
                )
            report_specs = {
                2: (
                    "reiyah.validation-report.gate-a-1.1.1",
                    "1.1.1",
                    HISTORICAL_V111_REPORT_PATH,
                ),
                3: (
                    "reiyah.validation-report.gate-a-1.1.2",
                    "1.1.2",
                    REPORT_PATH,
                ),
            }
            if receipt_sequence in report_specs:
                expected_report_id, expected_report_version, expected_report_path = report_specs[receipt_sequence]
                report_binding = receipt.get("validation_report_ref")
                if (
                    not isinstance(report_binding, dict)
                    or report_binding.get("artifact_id") != expected_report_id
                    or report_binding.get("version") != expected_report_version
                ):
                    issues.append(f"validation_report_ref must bind the exact sequence-{receipt_sequence} report identity")
                else:
                    issues.extend(
                        f"validation_report_ref: {issue}"
                        for issue in self.exact_artifact_binding_issues(view, report_binding, expected_report_path)
                    )
            payloads = receipt.get("distributed_payloads") if isinstance(receipt.get("distributed_payloads"), list) else []
            payload_by_id = {
                item.get("source_ref", {}).get("source_id"): item.get("payload")
                for item in payloads if isinstance(item, dict) and isinstance(item.get("source_ref"), dict)
            }
            expected_payloads = {source_id: ledger_by_id[source_id].get("retained_payload") for source_id in distributable_ids}
            attribution = receipt.get("attribution_fulfillment") if isinstance(receipt.get("attribution_fulfillment"), list) else []
            attribution_ids = [item.get("source_ref", {}).get("source_id") for item in attribution if isinstance(item, dict) and isinstance(item.get("source_ref"), dict)]
            if payload_by_id != expected_payloads or set(attribution_ids) != distributable_ids or len(attribution_ids) != len(set(attribution_ids)):
                issues.append("distributed payload and attribution sets do not exactly equal the four included inventory payloads")
            try:
                notice_text = view.read_text("NOTICE")
            except (OSError, UnicodeDecodeError, ValueError):
                notice_text = ""
            inventory_by_id = {
                entry.get("source_ref", {}).get("source_id"): entry
                for entry in inventory_entries
                if isinstance(entry, dict) and isinstance(entry.get("source_ref"), dict)
            }
            for source_id in sorted(distributable_ids):
                obligations = inventory_by_id.get(source_id, {}).get("attribution", [])
                if not isinstance(obligations, list) or not obligations or any(not isinstance(text, str) or text not in notice_text for text in obligations):
                    issues.append(f"NOTICE does not contain every exact inventory attribution obligation for {source_id}")
            published_at = parse_exact_utc(receipt.get("published_at"))
            readback = receipt.get("remote_readback") if isinstance(receipt.get("remote_readback"), dict) else {}
            verified_at = parse_exact_utc(readback.get("verified_at"))
            recorded_at = parse_exact_utc(receipt.get("recorded_at"))
            receipt_basis = receipt_rights.get("basis_observations") if isinstance(receipt_rights.get("basis_observations"), list) else []
            receipt_observed_at = parse_exact_utc(receipt_rights.get("observed_at"))
            receipt_observed_urls = [item.get("official_url") for item in receipt_basis if isinstance(item, dict)]
            receipt_covered = receipt_rights.get("covered_payload_source_ids") if isinstance(receipt_rights.get("covered_payload_source_ids"), list) else []
            receipt_excluded = receipt_rights.get("excluded_pointer_source_ids") if isinstance(receipt_rights.get("excluded_pointer_source_ids"), list) else []
            if (
                set(receipt_covered) != distributable_ids
                or set(receipt_excluded) != nist_pointer_ids
                or receipt_observed_urls != expected_urls
                or receipt_rights.get("all_included_payloads_covered") is not True
                or receipt_rights.get("preflight_outcome") != "included_iso_basis_consistent_nist_payload_excluded"
                or receipt_observed_at is None
                or any(parse_exact_utc(item.get("observed_at")) != receipt_observed_at for item in receipt_basis if isinstance(item, dict))
                or receipt_rights.get("distribution_authorization_created") is not False
                or receipt_rights.get("qualified_legal_review_performed") is not False
                or receipt_rights.get("legal_conclusion_created") is not False
                or receipt_rights.get("gate_a_acceptance_conferred") is not False
                or receipt_rights.get("ga17_status") != "not_evaluated"
            ):
                issues.append("receipt rights observation does not preserve the exact custody boundary, canonical official-page observations, or non-authority invariants")
            prior_rights_path_by_successor = {
                SUCCESSOR_PUBLIC_RIGHTS_REVALIDATION_PATH: PUBLIC_RIGHTS_REVALIDATION_PATH,
                CURRENT_PUBLIC_RIGHTS_REVALIDATION_PATH: SUCCESSOR_PUBLIC_RIGHTS_REVALIDATION_PATH,
            }
            prior_rights_path = prior_rights_path_by_successor.get(receipt_rights_path)
            if prior_rights_path is not None:
                prior_rights_issues = self.exact_artifact_binding_issues(
                    view,
                    receipt_rights.get("prior_observation_ref"),
                    prior_rights_path,
                )
                prior_rights = self.read_view_json(view, prior_rights_path)
                prior_rights_observed_at = parse_exact_utc(prior_rights.get("observed_at")) if isinstance(prior_rights, dict) else None
                if prior_rights_issues or prior_rights_observed_at is None or receipt_observed_at is None or receipt_observed_at <= prior_rights_observed_at:
                    issues.append(f"successor rights observation must exactly and chronologically follow its immutable immediate predecessor: {prior_rights_issues}")
            freshness = receipt_rights.get("freshness_policy") if isinstance(receipt_rights.get("freshness_policy"), dict) else {}
            age_seconds = (published_at - receipt_observed_at).total_seconds() if receipt_observed_at is not None and published_at is not None else None
            if None in (receipt_observed_at, published_at, verified_at, recorded_at) or not (receipt_observed_at <= published_at <= verified_at <= recorded_at):
                issues.append("receipt chronology must satisfy rights observation <= publication <= remote readback <= recording")
            if (
                freshness.get("maximum_age_seconds") != 3600
                or freshness.get("new_observation_required_for_each_payload_distribution_event") is not True
                or age_seconds is None
                or age_seconds < 0
                or age_seconds > 3600
                or receipt.get("rights_observation_age_seconds") != age_seconds
            ):
                issues.append("receipt must recompute a same-event rights observation age within the exact 3600-second freshness policy")
            if receipt.get("published_repository_url") != "https://github.com/manfromnowhere143/reiyah" or receipt.get("published_ref") != "refs/heads/main":
                issues.append("receipt must bind the canonical public repository and refs/heads/main")
            if receipt_sequence in {2, 3} and readback.get("tree_contains_exact_validation_report") is not True:
                issues.append(f"receipt sequence {receipt_sequence} remote readback must attest that the published tree contains the exact bound validation report")
            if (
                receipt.get("distribution_executed") is not True
                or receipt.get("runtime_execution_authorized") is not False
                or receipt.get("ga17_status") != "not_evaluated"
                or receipt.get("gate_a_acceptance_conferred") is not False
                or receipt.get("scientific_publication_acceptance_conferred") is not False
                or receipt.get("scientific_support_claimed") is not False
                or receipt.get("compliance_claimed") is not False
            ):
                issues.append("receipt cannot authorize runtime, scientific/compliance/acceptance authority, or GA-17 evaluation")
            if issues:
                diagnostics.append(make_diagnostic("GA-PUBLIC-DISTRIBUTION-RECEIPT", relative, f"Distribution receipt is ineligible: {sorted(set(issues))}.", receipt.get("receipt_id") if isinstance(receipt.get("receipt_id"), str) else None))
        if receipts:
            receipt_ids = [record.get("receipt_id") for _, record in receipts]
            artifact_ids = [record.get("artifact_id") for _, record in receipts]
            receipt_rights_paths = [
                record.get("rights_revalidation_ref", {}).get("path")
                if isinstance(record.get("rights_revalidation_ref"), dict)
                else None
                for _, record in receipts
            ]
            if (
                any(not isinstance(value, str) for value in receipt_ids + artifact_ids)
                or len(receipt_ids) != len(set(receipt_ids))
                or len(artifact_ids) != len(set(artifact_ids))
                or len(receipt_paths) != len(set(receipt_paths))
                or any(not isinstance(value, str) for value in receipt_rights_paths)
                or len(receipt_rights_paths) != len(set(receipt_rights_paths))
            ):
                diagnostics.append(make_diagnostic("GA-PUBLIC-DISTRIBUTION-RECEIPT", receipts[0][0], "Receipt paths, receipt_id values, artifact_id values, and per-event rights observation paths must each be globally unique."))
            by_sequence = {record.get("receipt_sequence"): (relative, record) for relative, record in receipts if isinstance(record.get("receipt_sequence"), int)}
            sequences = sorted(by_sequence)
            if sequences != list(range(1, len(receipts) + 1)) or len(by_sequence) != len(receipts):
                diagnostics.append(make_diagnostic("GA-PUBLIC-DISTRIBUTION-RECEIPT", receipts[0][0], "Receipt sequences must be unique and contiguous from one."))
            previous: tuple[str, dict[str, Any]] | None = None
            for sequence in sequences:
                relative, receipt = by_sequence[sequence]
                prior_ref = receipt.get("prior_receipt_ref")
                if sequence == 1:
                    if prior_ref is not None:
                        diagnostics.append(make_diagnostic("GA-PUBLIC-DISTRIBUTION-RECEIPT", relative, "First receipt must have null prior_receipt_ref."))
                elif previous is None:
                    diagnostics.append(make_diagnostic("GA-PUBLIC-DISTRIBUTION-RECEIPT", relative, "Receipt lineage is disconnected."))
                else:
                    prior_path, prior = previous
                    issues = self.exact_artifact_binding_issues(view, prior_ref, prior_path)
                    if issues or receipt.get("history_policy") != "append_only_linear":
                        diagnostics.append(make_diagnostic("GA-PUBLIC-DISTRIBUTION-RECEIPT", relative, f"Receipt prior edge is stale or non-linear: {issues}."))
                    current_time = parse_exact_utc(receipt.get("recorded_at"))
                    prior_time = parse_exact_utc(prior.get("recorded_at"))
                    if current_time is None or prior_time is None or current_time <= prior_time:
                        diagnostics.append(make_diagnostic("GA-PUBLIC-DISTRIBUTION-RECEIPT", relative, "Successor receipt time must be strictly later than its predecessor."))
                    if (
                        receipt.get("published_index_ref", {}).get("sha256") != prior.get("published_index_ref", {}).get("sha256")
                        and receipt.get("published_git_commit") == prior.get("published_git_commit")
                    ):
                        diagnostics.append(make_diagnostic("GA-PUBLIC-DISTRIBUTION-RECEIPT", relative, "A successor that publishes different index bytes must bind a distinct immutable Git commit."))
                previous = (relative, receipt)

        diagnostics.extend(self.historical_recovery_diagnostics(view))
        return sorted(diagnostics, key=diagnostic_key)

    def predecessor_packet_drift_diagnostics(self, view: RepositoryView) -> list[dict[str, Any]]:
        """Lock released 1.1.0 and 1.1.1 bytes outside explicit successor surfaces."""

        diagnostics: list[dict[str, Any]] = []
        try:
            predecessor_raw = view.read_bytes(HISTORICAL_V11_INDEX_PATH)
            predecessor = strict_json_loads(predecessor_raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, StrictJSONError, ValueError):
            predecessor_raw = None
            predecessor = None
        if predecessor_raw is None or digest_bytes(predecessor_raw) != HISTORICAL_V11_INDEX_DIGEST or not isinstance(predecessor, dict):
            return [make_diagnostic("GA-PREDECESSOR-PACKET-DRIFT", HISTORICAL_V11_INDEX_PATH, "The exact frozen Gate A 1.1.0 predecessor index is absent, malformed, or digest-mismatched.")]

        try:
            report_raw = view.read_bytes(HISTORICAL_V11_REPORT_PATH)
            report = strict_json_loads(report_raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, StrictJSONError, ValueError):
            report_raw = None
            report = None
        if (
            report_raw is None
            or digest_bytes(report_raw) != HISTORICAL_V11_REPORT_DIGEST
            or not isinstance(report, dict)
            or report.get("schema_id") != "https://schemas.reiyah.invalid/gate-a/1.1.0/validation-report.schema.json"
            or report.get("artifact_id") != "reiyah.validation-report.gate-a-1.1.0"
            or report.get("version") != "1.1.0"
            or report.get("acceptance_created") is not False
            or report.get("control_summary", {}).get("external_control_summary", {}).get("status") != "not_evaluated"
        ):
            diagnostics.append(make_diagnostic("GA-PREDECESSOR-PACKET-DRIFT", HISTORICAL_V11_REPORT_PATH, "The frozen Gate A 1.1.0 report must preserve exact digest, schema/artifact/version identity, no acceptance, and GA-17 not_evaluated."))

        mutable_successor_paths = {
            "CITATION.cff",
            "README.md",
            "docs/FRONTIER_BASELINE_2026.md",
            "docs/RESEARCH_GAP_REGISTER.md",
            "docs/SESSION_HANDOFF.md",
            "docs/STATUS_MODEL.md",
            "docs/VALIDATION.md",
            "evidence/README.md",
            "gate/README.md",
            CATALOG_PATH,
            PLAN_PATH,
            "tools/build_gate_a_index.py",
            "tools/validate_gate_a.py",
        }
        drift: list[str] = []
        artifacts = predecessor.get("artifacts") if isinstance(predecessor.get("artifacts"), list) else []
        for item in artifacts:
            binding = item.get("artifact") if isinstance(item, dict) and isinstance(item.get("artifact"), dict) else {}
            relative = binding.get("path")
            if not isinstance(relative, str) or relative in mutable_successor_paths:
                continue
            try:
                current_raw = view.read_bytes(relative)
            except (OSError, ValueError):
                drift.append(f"{relative}: absent")
                continue
            if binding.get("sha256") != digest_bytes(current_raw):
                drift.append(f"{relative}: digest changed")
        if drift:
            diagnostics.append(
                make_diagnostic(
                    "GA-PREDECESSOR-PACKET-DRIFT",
                    HISTORICAL_V11_INDEX_PATH,
                    "Released 1.1.0 paths outside the explicit governance-correction surface must remain byte-exact; "
                    f"drift={sorted(drift)}.",
                )
            )

        try:
            immediate_raw = view.read_bytes(HISTORICAL_V111_INDEX_PATH)
            immediate = strict_json_loads(immediate_raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, StrictJSONError, ValueError):
            immediate_raw = None
            immediate = None
        if (
            immediate_raw is None
            or digest_bytes(immediate_raw) != HISTORICAL_V111_INDEX_DIGEST
            or not isinstance(immediate, dict)
        ):
            diagnostics.append(make_diagnostic("GA-PREDECESSOR-PACKET-DRIFT", HISTORICAL_V111_INDEX_PATH, "The exact frozen Gate A 1.1.1 predecessor index is absent, malformed, or digest-mismatched."))
            return sorted(diagnostics, key=diagnostic_key)

        try:
            immediate_report_raw = view.read_bytes(HISTORICAL_V111_REPORT_PATH)
            immediate_report = strict_json_loads(immediate_report_raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, StrictJSONError, ValueError):
            immediate_report_raw = None
            immediate_report = None
        if (
            immediate_report_raw is None
            or digest_bytes(immediate_report_raw) != HISTORICAL_V111_REPORT_DIGEST
            or not isinstance(immediate_report, dict)
            or immediate_report.get("schema_id") != "https://schemas.reiyah.invalid/gate-a/1.1.1/validation-report.schema.json"
            or immediate_report.get("artifact_id") != "reiyah.validation-report.gate-a-1.1.1"
            or immediate_report.get("version") != "1.1.1"
            or immediate_report.get("acceptance_created") is not False
            or immediate_report.get("control_summary", {}).get("external_control_summary", {}).get("status") != "not_evaluated"
        ):
            diagnostics.append(make_diagnostic("GA-PREDECESSOR-PACKET-DRIFT", HISTORICAL_V111_REPORT_PATH, "The frozen Gate A 1.1.1 report must preserve exact digest, schema/artifact/version identity, no acceptance, and GA-17 not_evaluated."))

        immediate_drift: list[str] = []
        immediate_artifacts = immediate.get("artifacts") if isinstance(immediate.get("artifacts"), list) else []
        for item in immediate_artifacts:
            binding = item.get("artifact") if isinstance(item, dict) and isinstance(item.get("artifact"), dict) else {}
            relative = binding.get("path")
            if not isinstance(relative, str) or relative in mutable_successor_paths:
                continue
            try:
                current_raw = view.read_bytes(relative)
            except (OSError, ValueError):
                immediate_drift.append(f"{relative}: absent")
                continue
            if binding.get("sha256") != digest_bytes(current_raw):
                immediate_drift.append(f"{relative}: digest changed")
        if immediate_drift:
            diagnostics.append(
                make_diagnostic(
                    "GA-PREDECESSOR-PACKET-DRIFT",
                    HISTORICAL_V111_INDEX_PATH,
                    "Released 1.1.1 paths outside the explicit documentation-and-continuity successor surface must remain byte-exact; "
                    f"drift={sorted(immediate_drift)}.",
                )
            )
        return sorted(diagnostics, key=diagnostic_key)

    def check_predecessor_packet_drift(self) -> None:
        self.diagnostics.extend(self.predecessor_packet_drift_diagnostics(self.view))

    def check_public_custody(self) -> None:
        self.diagnostics.extend(self.public_custody_diagnostics(self.view))

    def check_sources_and_crosswalk(self) -> None:
        self.diagnostics.extend(self.sources_crosswalk_diagnostics(self.view))
        ledger = self.read_view_json(self.view, ACTIVE_SOURCE_LEDGER_PATH)
        records = ledger.get("records", []) if isinstance(ledger, dict) else []
        if isinstance(records, list):
            self.check_summary["normative_instances_checked"] += len(records)
            self.check_summary["retained_sources_checked"] = len(records)

    def narrative_bindings_diagnostics(self, view: RepositoryView) -> list[dict[str, Any]]:
        plan = self.read_view_json(view, PLAN_PATH)
        bindings = plan.get("narrative_bindings") if isinstance(plan, dict) else None
        if not isinstance(bindings, list) or not bindings:
            return [make_diagnostic("GA-NARRATIVE-BINDING-MISMATCH", PLAN_PATH, "Validation plan narrative_bindings must be a nonempty array.")]
        diagnostics: list[dict[str, Any]] = []
        binding_ids: set[str] = set()
        identities: set[tuple[Any, Any, Any]] = set()

        def markdown_tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
            lines = text.splitlines()
            tables: list[tuple[list[str], list[list[str]]]] = []
            index = 0
            while index + 1 < len(lines):
                if not lines[index].startswith("|") or not re.fullmatch(r"\|?(?:\s*:?-+:?\s*\|)+", lines[index + 1].strip()):
                    index += 1
                    continue
                headers = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
                rows: list[list[str]] = []
                index += 2
                while index < len(lines) and lines[index].startswith("|"):
                    cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
                    if len(cells) == len(headers):
                        rows.append(cells)
                    index += 1
                tables.append((headers, rows))
            return tables

        def uncode(value: str) -> str:
            stripped = value.strip()
            return stripped[1:-1] if len(stripped) >= 2 and stripped.startswith("`") and stripped.endswith("`") and stripped.count("`") == 2 else stripped

        def claims_narrative_diagnostics(narrative_path: str, machine_path: str, binding_id: str | None) -> list[dict[str, Any]]:
            try:
                text = view.read_text(narrative_path)
                manifest = view.read_json(machine_path)
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
                return [make_diagnostic("GA-NARRATIVE-BINDING-MISMATCH", narrative_path, "Claims narrative or machine register is absent or malformed.", binding_id)]
            if not isinstance(manifest, dict) or not isinstance(manifest.get("items"), list):
                return [make_diagnostic("GA-NARRATIVE-BINDING-MISMATCH", machine_path, "Claims machine register has no item array.", binding_id)]
            mismatches: list[str] = []
            metadata = {
                match.group(1): uncode(match.group(2))
                for match in re.finditer(r"^\| (Version|Lifecycle status) \| (.+) \|$", text, re.MULTILINE)
            }
            if metadata.get("Version") != manifest.get("version"):
                mismatches.append("document version")
            if metadata.get("Lifecycle status") != manifest.get("lifecycle_status"):
                mismatches.append("document lifecycle status")
            items = [item for item in manifest["items"] if isinstance(item, dict)]
            machine_by_id: dict[str, dict[str, Any]] = {}
            for item in items:
                item_id = item.get("item_id")
                if not isinstance(item_id, str) or item_id in machine_by_id:
                    mismatches.append(f"duplicate/absent machine item {item_id!r}")
                elif isinstance(item_id, str):
                    machine_by_id[item_id] = item
            table_map = {tuple(headers): rows for headers, rows in markdown_tables(text)}
            repo_headers = ("ID", "Version", "Exact candidate assertion", "Current status", "Evidence gap", "Falsifier", "Prohibited interpretation")
            science_headers = ("ID", "Version", "Exact proposed proposition", "Required comparator or contrast", "Required primary estimand", "Current status")
            trace_headers = ("ID", "Current evidence gap", "Required falsifier/contradiction condition", "Prohibited interpretation")
            nonclaim_headers = ("ID", "Version", "Lifecycle status", "Reiyah/HARBOR does **not** claim that…", "Why prohibited at Gate A")
            required_headers = (repo_headers, science_headers, trace_headers, nonclaim_headers)
            if any(headers not in table_map for headers in required_headers):
                mismatches.append("required claims tables")
                return [make_diagnostic("GA-NARRATIVE-BINDING-MISMATCH", narrative_path, f"Claims narrative semantic parity failed; mismatches={sorted(set(mismatches))}.", binding_id)]

            rendered_ids: list[str] = []
            for row in table_map[repo_headers]:
                item_id, version, proposition, status, gap, falsifier, prohibited = row
                item_id, version, status = uncode(item_id), uncode(version), uncode(status)
                rendered_ids.append(item_id)
                item = machine_by_id.get(item_id)
                expected = (
                    version,
                    proposition,
                    status,
                    gap,
                    falsifier,
                    prohibited,
                )
                actual = (
                    item.get("version") if item else None,
                    item.get("proposition") if item else None,
                    item.get("lifecycle_status") if item else None,
                    item.get("evidence_binding", {}).get("gap_reason") if item and isinstance(item.get("evidence_binding"), dict) else None,
                    item.get("falsifier_or_decision_rule") if item else None,
                    item.get("prohibited_interpretation") if item else None,
                )
                if item is None or item.get("kind") != "claim" or actual != expected:
                    mismatches.append(f"repository assertion {item_id}")
            science_rows: dict[str, list[str]] = {}
            for row in table_map[science_headers]:
                item_id, version, proposition, comparator, estimand, status = row
                item_id, version, status = uncode(item_id), uncode(version), uncode(status)
                rendered_ids.append(item_id)
                science_rows[item_id] = row
                item = machine_by_id.get(item_id)
                expected_scope = f"Comparator: {comparator.rstrip('.')}. Primary estimand: {estimand.rstrip('.')}."
                if (
                    item is None
                    or item.get("kind") != "claim"
                    or item.get("version") != version
                    or item.get("proposition") != proposition
                    or item.get("lifecycle_status") != status
                    or item.get("scope") != expected_scope
                ):
                    mismatches.append(f"scientific proposition {item_id}")
            trace_ids: list[str] = []
            for row in table_map[trace_headers]:
                item_id, gap, falsifier, prohibited = row
                item_id = uncode(item_id)
                trace_ids.append(item_id)
                item = machine_by_id.get(item_id)
                actual = (
                    item.get("evidence_binding", {}).get("gap_reason") if item and isinstance(item.get("evidence_binding"), dict) else None,
                    item.get("falsifier_or_decision_rule") if item else None,
                    item.get("prohibited_interpretation") if item else None,
                )
                if item_id not in science_rows or actual != (gap, falsifier, prohibited):
                    mismatches.append(f"scientific trace {item_id}")
            if set(trace_ids) != set(science_rows) or len(trace_ids) != len(set(trace_ids)):
                mismatches.append("scientific trace item set")
            for row in table_map[nonclaim_headers]:
                item_id, version, status, prohibited, scope = row
                item_id, version, status = uncode(item_id), uncode(version), uncode(status)
                rendered_ids.append(item_id)
                item = machine_by_id.get(item_id)
                if (
                    item is None
                    or item.get("kind") != "non_claim"
                    or item.get("version") != version
                    or item.get("lifecycle_status") != status
                    or item.get("prohibited_interpretation") != prohibited
                    or item.get("scope") != scope
                ):
                    mismatches.append(f"non-claim {item_id}")
            if len(rendered_ids) != len(set(rendered_ids)) or set(rendered_ids) != set(machine_by_id):
                mismatches.append("complete unique claim/non-claim item set")
            return [] if not mismatches else [make_diagnostic("GA-NARRATIVE-BINDING-MISMATCH", narrative_path, f"Claims narrative semantic parity failed; mismatches={sorted(set(mismatches))}.", binding_id)]

        def standards_narrative_diagnostics(narrative_path: str, machine_path: str, binding_id: str | None) -> list[dict[str, Any]]:
            try:
                text = view.read_text(narrative_path)
                crosswalk = view.read_json(machine_path)
                ledger = view.read_json(ACTIVE_SOURCE_LEDGER_PATH)
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
                return [make_diagnostic("GA-NARRATIVE-BINDING-MISMATCH", narrative_path, "Standards narrative, crosswalk, or source ledger is absent or malformed.", binding_id)]
            mismatches: list[str] = []
            as_of_match = re.search(r"^\*\*As of:\*\*\s*([^\s]+)\s*$", text, re.MULTILINE)
            status_match = re.search(r"^\*\*Lifecycle status:\*\*\s*`([^`]+)`\s*$", text, re.MULTILINE)
            compliance_match = re.search(r"^\*\*Compliance claimed:\*\*\s*`([^`]+)`\s*$", text, re.MULTILINE)
            if not isinstance(crosswalk, dict) or as_of_match is None or as_of_match.group(1) != crosswalk.get("as_of_date"):
                mismatches.append("as_of_date")
            if not isinstance(crosswalk, dict) or status_match is None or status_match.group(1) != crosswalk.get("lifecycle_status"):
                mismatches.append("lifecycle_status")
            if not isinstance(crosswalk, dict) or compliance_match is None or compliance_match.group(1) != "false" or crosswalk.get("compliance_claimed") is not False:
                mismatches.append("compliance_claimed false")
            tables = markdown_tables(text)
            source_rows = [
                row
                for headers, rows in tables
                if headers and headers[0] == "Source ID"
                for row in rows
            ]
            mapping_rows = next((rows for headers, rows in tables if headers and headers[0] == "Mapping ID"), [])
            narrative_source_ids = [uncode(row[0]) for row in source_rows]
            narrative_mapping_ids = [uncode(row[0]) for row in mapping_rows]
            machine_source_ids = {
                source.get("source_id")
                for source in ledger.get("records", [])
                if isinstance(ledger, dict) and isinstance(source, dict) and isinstance(source.get("source_id"), str)
            } if isinstance(ledger, dict) else set()
            entries = crosswalk.get("entries", []) if isinstance(crosswalk, dict) else []
            machine_mapping_ids = [entry.get("mapping_id") for entry in entries if isinstance(entry, dict) and isinstance(entry.get("mapping_id"), str)]
            crosswalk_source_ids: set[str] = set()
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                # Gate A 1.0 used a flat source_ids array.  Gate A 1.1 makes the
                # identity/evidence/discovery roles explicit and versioned.  Narrative
                # parity compares the union because all eight ledger identities must
                # remain rendered, including pointer-only discovery sources.
                crosswalk_source_ids.update(
                    source_id
                    for source_id in entry.get("source_ids", [])
                    if isinstance(source_id, str)
                )
                identity_source = entry.get("identity_source_ref")
                if isinstance(identity_source, dict) and isinstance(identity_source.get("source_id"), str):
                    crosswalk_source_ids.add(identity_source["source_id"])
                for field in ("evidence_source_refs", "discovery_source_refs"):
                    crosswalk_source_ids.update(
                        source_ref["source_id"]
                        for source_ref in entry.get(field, [])
                        if isinstance(source_ref, dict) and isinstance(source_ref.get("source_id"), str)
                    )
            if len(narrative_source_ids) != len(set(narrative_source_ids)) or set(narrative_source_ids) != machine_source_ids or crosswalk_source_ids != machine_source_ids:
                mismatches.append("complete unique retained source ID set")
            if len(narrative_mapping_ids) != len(set(narrative_mapping_ids)) or len(machine_mapping_ids) != len(set(machine_mapping_ids)) or set(narrative_mapping_ids) != set(machine_mapping_ids):
                mismatches.append("complete unique mapping ID set")
            affirmative_patterns = (
                r"\bcompliance claimed:\s*(?:true|yes)\b",
                r"\b(?:Reiyah|HARBOR|Gate A)\s+(?:is|has been)\s+(?:fully\s+)?compliant\b",
                r"\b(?:Reiyah|HARBOR|Gate A)\s+complies with\b",
                r"\b(?:Reiyah|HARBOR|Gate A)\s+is certified (?:to|under)\b",
            )
            if any(re.search(pattern, text, re.IGNORECASE) for pattern in affirmative_patterns):
                mismatches.append("affirmative compliance wording")
            return [] if not mismatches else [make_diagnostic("GA-NARRATIVE-BINDING-MISMATCH", narrative_path, f"Standards narrative semantic parity failed; mismatches={sorted(set(mismatches))}.", binding_id)]

        for binding in bindings:
            if not isinstance(binding, dict):
                diagnostics.append(make_diagnostic("GA-NARRATIVE-BINDING-MISMATCH", PLAN_PATH, "Narrative binding entry is not an object."))
                continue
            binding_id = binding.get("binding_id")
            narrative = binding.get("narrative")
            machine = binding.get("machine")
            identity = (
                binding.get("scope"),
                narrative.get("path") if isinstance(narrative, dict) else None,
                machine.get("path") if isinstance(machine, dict) else None,
            )
            if not isinstance(binding_id, str) or binding_id in binding_ids:
                diagnostics.append(make_diagnostic("GA-NARRATIVE-BINDING-MISMATCH", PLAN_PATH, f"Narrative binding_id is absent or duplicated: {binding_id!r}.", binding_id if isinstance(binding_id, str) else None))
            else:
                binding_ids.add(binding_id)
            if identity in identities:
                diagnostics.append(make_diagnostic("GA-NARRATIVE-BINDING-MISMATCH", PLAN_PATH, f"Narrative scope/path identity is duplicated: {identity!r}.", binding_id if isinstance(binding_id, str) else None))
            identities.add(identity)
            for role, artifact in (("narrative", narrative), ("machine", machine)):
                relative = artifact.get("path") if isinstance(artifact, dict) else None
                declared_digest = artifact.get("sha256") if isinstance(artifact, dict) else None
                try:
                    safe_path = isinstance(relative, str)
                    if safe_path:
                        RepositoryView.validate_relative(relative)
                except ValueError:
                    safe_path = False
                if not safe_path or not view.is_file(relative) or view.is_symlink(relative):
                    diagnostics.append(make_diagnostic("GA-NARRATIVE-BINDING-MISMATCH", PLAN_PATH, f"{role} binding path must resolve to a regular repository file: {relative!r}.", binding_id if isinstance(binding_id, str) else None))
                    continue
                try:
                    actual_digest = hashlib.sha256(view.read_bytes(relative)).hexdigest()
                except (OSError, ValueError):
                    actual_digest = None
                if declared_digest != actual_digest:
                    diagnostics.append(make_diagnostic("GA-NARRATIVE-BINDING-MISMATCH", relative, f"{role} bytes do not match validation-plan SHA-256 binding.", binding_id if isinstance(binding_id, str) else None))
            narrative_path = narrative.get("path") if isinstance(narrative, dict) else None
            machine_path = machine.get("path") if isinstance(machine, dict) else None
            if isinstance(narrative_path, str) and isinstance(machine_path, str) and view.is_file(narrative_path) and view.is_file(machine_path):
                if narrative_path == "docs/CLAIMS_AND_NON_CLAIMS.md" and machine_path == "manifests/claims/proposed-claims-and-non-claims-1.0.0.json":
                    diagnostics.extend(claims_narrative_diagnostics(narrative_path, machine_path, binding_id if isinstance(binding_id, str) else None))
                elif narrative_path == "docs/STANDARDS_CROSSWALK.md" and machine_path == ACTIVE_STANDARDS_CROSSWALK_PATH:
                    diagnostics.extend(standards_narrative_diagnostics(narrative_path, machine_path, binding_id if isinstance(binding_id, str) else None))
        return sorted(diagnostics, key=diagnostic_key)

    def check_narrative_bindings(self) -> None:
        self.diagnostics.extend(self.narrative_bindings_diagnostics(self.view))

    def check_claim_id_parity(self) -> None:
        document_path = "docs/CLAIMS_AND_NON_CLAIMS.md"
        manifest_path = "manifests/claims/proposed-claims-and-non-claims-1.0.0.json"
        try:
            text = self.absolute(document_path).read_text(encoding="utf-8")
        except OSError as exc:
            self.add("GA-CLAIM-PARITY", document_path, f"Cannot read claim document: {exc}")
            return
        manifest = self.read_json_contract(manifest_path)
        if not isinstance(manifest, dict):
            return
        document_ids = set(re.findall(r"`(reiyah\.(?:claim|nonclaim)\.[a-z0-9.-]+)`", text))
        manifest_ids = {
            item.get("item_id")
            for item in manifest.get("items", [])
            if isinstance(item, dict) and isinstance(item.get("item_id"), str)
        }
        if document_ids != manifest_ids:
            self.add(
                "GA-CLAIM-PARITY",
                manifest_path,
                f"Claim ID mismatch; document-only={sorted(document_ids - manifest_ids)}, manifest-only={sorted(manifest_ids - document_ids)}.",
            )

    @staticmethod
    def event_offset(record: dict[str, Any]) -> tuple[str, str, str, float] | None:
        point = record.get("event_time")
        if not isinstance(point, dict):
            window = record.get("measurement_window")
            point = window.get("start") if isinstance(window, dict) else None
        if not isinstance(point, dict):
            return None
        offset = point.get("offset")
        origin = point.get("origin")
        if not isinstance(offset, dict) or offset.get("state") != "observed" or not isinstance(offset.get("value"), (int, float)):
            return None
        if not isinstance(origin, dict) or origin.get("state") != "observed" or not isinstance(origin.get("value"), str):
            return None
        clock = point.get("clock_id")
        unit = point.get("unit")
        if not isinstance(clock, str) or not isinstance(unit, str):
            return None
        return clock, unit, origin["value"], float(offset["value"])

    def semantic_object_chain(
        self,
        objects: list[tuple[str, dict[str, Any]]],
        *,
        require_exact_kind_set: bool = True,
        view: RepositoryView | None = None,
    ) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        selected_view = view or self.view
        by_key: dict[tuple[str, str], dict[str, Any]] = {}
        source_path: dict[tuple[str, str], str] = {}
        graph: dict[tuple[str, str], set[tuple[str, str]]] = {}
        evidence_inherited_context: dict[tuple[str, str], dict[str, Any]] = {}
        kinds: list[str] = []
        for relative, record in objects:
            diagnostics.extend(self.instance_diagnostics(record, relative))
            object_id = record.get("object_id")
            version = record.get("version")
            kind = record.get("object_kind")
            if isinstance(kind, str):
                kinds.append(kind)
            if isinstance(object_id, str) and isinstance(version, str):
                key = (object_id, version)
                if key in by_key:
                    diagnostics.append(make_diagnostic("GA-IDENTIFIER-DUPLICATE", relative, f"Duplicate object identity {object_id}@{version}.", object_id))
                by_key[key] = record
                source_path[key] = relative
            if "provenance" not in record:
                diagnostics.append(make_diagnostic("GA-PROVENANCE-MISSING", relative, "Scientific object lacks provenance.", object_id if isinstance(object_id, str) else None))
        if require_exact_kind_set and sorted(kinds) != sorted(EXPECTED_KINDS):
            diagnostics.append(make_diagnostic("GA-KIND-CONFLATION", objects[0][0] if objects else "fixtures", f"Canonical chain kinds must be exactly {list(EXPECTED_KINDS)}, found {sorted(kinds)}."))

        expected_dependency_rules = {
            "observation": set(),
            "latent_belief": {"observation"},
            "decision": {"observation", "latent_belief"},
            "intervention": {"decision"},
            "outcome": {"observation", "decision", "intervention"},
            "evidence": set(EXPECTED_KINDS),
        }
        dependency_cache: dict[str, dict[str, set[str]] | None] = {}
        dependency_reported: set[str] = set()

        def dependency_rules(release_id: Any, owner_path: str, owner_id: Any) -> dict[str, set[str]] | None:
            if not isinstance(release_id, str):
                return None
            if release_id in dependency_cache:
                return dependency_cache[release_id]
            protocol_path, protocol, protocol_mismatches = self.protocol_manifest_context(selected_view, release_id)
            policy = protocol.get("scientific_dependency_policy") if isinstance(protocol, dict) and not protocol_mismatches else None
            observed: dict[str, set[str]] = {}
            duplicate_owner = False
            if isinstance(policy, dict):
                for rule in policy.get("record_kind_rules", []):
                    if not isinstance(rule, dict) or not isinstance(rule.get("owner_record_kind"), str) or not isinstance(rule.get("allowed_input_kinds"), list):
                        continue
                    owner_kind = rule["owner_record_kind"]
                    if owner_kind in observed:
                        duplicate_owner = True
                    observed[owner_kind] = {kind for kind in rule["allowed_input_kinds"] if isinstance(kind, str)}
            valid = (
                isinstance(policy, dict)
                and policy.get("protocol_release_id") == release_id
                and policy.get("global_acyclicity_required") is True
                and policy.get("runtime_execution_authorized") is False
                and not duplicate_owner
                and observed == expected_dependency_rules
            )
            dependency_cache[release_id] = observed if valid else None
            if not valid and release_id not in dependency_reported:
                diagnostics.append(make_diagnostic("GA-REFERENCE-WRONG-KIND", protocol_path or owner_path, "Scientific dependency policy is absent, ambiguous, weakened, or not owned by the exact protocol release.", owner_id if isinstance(owner_id, str) else None))
                dependency_reported.add(release_id)
            return dependency_cache[release_id]

        def check_reference(
            owner_path: str,
            owner: dict[str, Any],
            reference: Any,
            expected_kind: str | None,
            temporal_input: bool,
            provenance_input: bool = False,
        ) -> None:
            if not isinstance(reference, dict):
                return
            object_id = reference.get("object_id")
            version = reference.get("version")
            declared_kind = reference.get("object_kind")
            key = (object_id, version)
            target = by_key.get(key) if isinstance(object_id, str) and isinstance(version, str) else None
            if target is None:
                diagnostics.append(make_diagnostic("GA-REFERENCE-DANGLING", owner_path, f"Reference does not resolve: {object_id}@{version}.", owner.get("object_id")))
                return
            actual_kind = target.get("object_kind")
            if actual_kind != declared_kind or (expected_kind is not None and actual_kind != expected_kind):
                diagnostics.append(make_diagnostic("GA-REFERENCE-WRONG-KIND", owner_path, f"Reference {object_id}@{version} has kind {actual_kind}, declared {declared_kind}, expected {expected_kind}.", owner.get("object_id")))
                return
            owner_key = (owner.get("object_id"), owner.get("version"))
            if all(isinstance(value, str) for value in owner_key):
                graph.setdefault(owner_key, set()).add(key)
                if owner_key == key:
                    diagnostics.append(make_diagnostic("GA-REFERENCE-CYCLE", owner_path, f"Scientific record cannot reference itself: {object_id}@{version}.", owner.get("object_id")))
            if provenance_input:
                release_id = owner.get("protocol_release_id")
                rules = dependency_rules(release_id, owner_path, owner.get("object_id"))
                allowed = rules.get(owner.get("object_kind"), set()) if isinstance(rules, dict) else set()
                if isinstance(rules, dict) and actual_kind not in allowed:
                    diagnostics.append(make_diagnostic("GA-REFERENCE-WRONG-KIND", owner_path, f"Protocol dependency policy forbids {owner.get('object_kind')!r} provenance input from {actual_kind!r}.", owner.get("object_id")))
            context_mismatches: list[str] = []
            for field in ("protocol_release_id", "encounter_id"):
                owner_value = owner.get(field)
                target_value = target.get(field)
                if owner_value is not None and target_value is not None and owner_value != target_value:
                    context_mismatches.append(field)
            if owner.get("object_kind") in {"observation", "latent_belief", "outcome"} and actual_kind in {"observation", "latent_belief", "outcome"}:
                owner_object = owner.get("physical_object_id")
                target_object = target.get("physical_object_id")
                if owner_object is not None and target_object is not None and owner_object != target_object:
                    context_mismatches.append("physical_object_id")
            owner_context = owner.get("context_rules")
            target_context = target.get("context_rules")
            if isinstance(owner_context, dict) and isinstance(target_context, dict) and owner_context != target_context:
                context_mismatches.append("context_rules")
            elif owner.get("object_kind") == "evidence" and isinstance(target_context, dict) and all(isinstance(value, str) for value in owner_key):
                inherited = evidence_inherited_context.get(owner_key)
                if inherited is None:
                    evidence_inherited_context[owner_key] = target_context
                elif inherited != target_context:
                    context_mismatches.append("evidence inherited context_rules")
            if context_mismatches:
                diagnostics.append(make_diagnostic("GA-CONTEXT-MISMATCH", owner_path, f"Reference {object_id}@{version} crosses incompatible scientific context fields: {sorted(context_mismatches)}.", owner.get("object_id")))
            if temporal_input:
                upstream_time = self.event_offset(target)
                owner_time = self.event_offset(owner)
                if upstream_time is not None and owner_time is not None:
                    if upstream_time[:3] != owner_time[:3]:
                        diagnostics.append(make_diagnostic("GA-TIME-CLOCK-MISMATCH", owner_path, f"Referenced time basis differs for {object_id}.", owner.get("object_id")))
                    elif upstream_time[3] > owner_time[3]:
                        diagnostics.append(make_diagnostic("GA-TEMPORAL-LEAKAGE", owner_path, f"Input {object_id} occurs after the owner's index time.", owner.get("object_id")))
                upstream_recorded = target.get("provenance", {}).get("recorded_at") if isinstance(target.get("provenance"), dict) else None
                owner_recorded = owner.get("provenance", {}).get("recorded_at") if isinstance(owner.get("provenance"), dict) else None
                if isinstance(upstream_recorded, str) and isinstance(owner_recorded, str):
                    try:
                        upstream_timestamp = datetime.fromisoformat(upstream_recorded.replace("Z", "+00:00"))
                        owner_timestamp = datetime.fromisoformat(owner_recorded.replace("Z", "+00:00"))
                    except ValueError:
                        diagnostics.append(make_diagnostic("GA-TIME-FORMAT", owner_path, f"Cannot compare recorded_at provenance for {object_id}.", owner.get("object_id")))
                    else:
                        if upstream_timestamp > owner_timestamp:
                            diagnostics.append(make_diagnostic("GA-TEMPORAL-LEAKAGE", owner_path, f"Input {object_id} was recorded after the owner record.", owner.get("object_id")))

        for relative, record in objects:
            dependency_rules(record.get("protocol_release_id"), relative, record.get("object_id"))
            field_rules: tuple[tuple[str, str | None, bool], ...] = (
                ("observation_refs", "observation", True),
                ("belief_refs", "latent_belief", True),
                ("decision_refs", "decision", True),
                ("intervention_refs", "intervention", True),
                ("target_object_refs", None, False),
            )
            for field, expected_kind, temporal in field_rules:
                references = record.get(field, [])
                if isinstance(references, list):
                    for reference in references:
                        check_reference(relative, record, reference, expected_kind, temporal)
            if "decision_ref" in record:
                check_reference(relative, record, record.get("decision_ref"), "decision", True)
            provenance = record.get("provenance")
            if isinstance(provenance, dict):
                for reference in provenance.get("input_refs", []):
                    check_reference(relative, record, reference, None, True, True)

            if record.get("object_kind") == "latent_belief":
                belief = record.get("belief")
                if isinstance(belief, dict) and belief.get("state") == "observed":
                    release_id = record.get("protocol_release_id")
                    protocol_path, protocol, protocol_mismatches = self.protocol_manifest_context(selected_view, release_id)
                    expected_policy = {
                        "policy_id": "reiyah.belief-normalization-policy.harbor-gate-a",
                        "version": protocol.get("version") if isinstance(protocol, dict) else None,
                        "protocol_release_id": release_id,
                        "applies_to": "observed_categorical_belief_components",
                        "sum_target": 1,
                        "absolute_tolerance": 0.000001,
                        "comparison": "absolute_error_lte",
                        "record_tolerance_must_equal_policy": True,
                        "runtime_execution_authorized": False,
                    }
                    normalization_policy = protocol.get("belief_normalization_policy") if isinstance(protocol, dict) and not protocol_mismatches else None
                    tolerance = belief.get("sum_tolerance")
                    if normalization_policy != expected_policy or tolerance != expected_policy["absolute_tolerance"]:
                        diagnostics.append(
                            make_diagnostic(
                                "GA-BELIEF-POLICY-MISMATCH",
                                protocol_path or relative,
                                "Observed categorical belief normalization must use the exact ledger-bound protocol target, tolerance, comparison, and record-tolerance equality policy; "
                                f"protocol_mismatches={protocol_mismatches}, record_tolerance={tolerance!r}.",
                                record.get("object_id"),
                            )
                        )
                    components = belief.get("components", [])
                    state_ids = [item.get("state_id") for item in components if isinstance(item, dict)]
                    probabilities = [item.get("probability") for item in components if isinstance(item, dict)]
                    if len(state_ids) != len(set(state_ids)):
                        diagnostics.append(make_diagnostic("GA-BELIEF-STATE-DUPLICATE", relative, "Belief component state IDs are not unique.", record.get("object_id")))
                    if all(isinstance(value, (int, float)) for value in probabilities):
                        total = float(sum(probabilities))
                        if abs(total - float(expected_policy["sum_target"])) > float(expected_policy["absolute_tolerance"]):
                            diagnostics.append(make_diagnostic("GA-BELIEF-NORMALIZATION", relative, f"Belief probabilities sum to {total}, outside the exact protocol-owned tolerance.", record.get("object_id")))

            if record.get("object_kind") == "outcome":
                window = record.get("measurement_window")
                if isinstance(window, dict):
                    start_record = {"event_time": window.get("start")}
                    end_record = {"event_time": window.get("end")}
                    start = self.event_offset(start_record)
                    end = self.event_offset(end_record)
                    if start is not None and end is not None:
                        if start[:3] != end[:3] or start[3] > end[3]:
                            diagnostics.append(make_diagnostic("GA-TIME-INTERVAL", relative, "Outcome measurement interval is unordered or changes time basis.", record.get("object_id")))
                declared_decisions = {
                    (reference.get("object_id"), reference.get("version"))
                    for reference in record.get("decision_refs", [])
                    if isinstance(reference, dict)
                }
                for intervention_ref in record.get("intervention_refs", []):
                    if not isinstance(intervention_ref, dict):
                        continue
                    intervention = by_key.get((intervention_ref.get("object_id"), intervention_ref.get("version")))
                    decision_ref = intervention.get("decision_ref") if isinstance(intervention, dict) else None
                    decision_key = (decision_ref.get("object_id"), decision_ref.get("version")) if isinstance(decision_ref, dict) else None
                    if decision_key is not None and decision_key not in declared_decisions:
                        diagnostics.append(make_diagnostic("GA-REFERENCE-CHAIN-INCOHERENT", relative, f"Outcome intervention {intervention_ref.get('object_id')!r} derives from decision {decision_key[0]}@{decision_key[1]}, which is absent from outcome.decision_refs.", record.get("object_id")))

        visiting: set[tuple[str, str]] = set()
        visited: set[tuple[str, str]] = set()

        def visit(node: tuple[str, str], trail: list[tuple[str, str]]) -> None:
            if node in visiting:
                cycle_start = trail.index(node) if node in trail else 0
                cycle = trail[cycle_start:] + [node]
                relative = source_path.get(node, "manifests/examples/object-chain")
                diagnostics.append(make_diagnostic("GA-REFERENCE-CYCLE", relative, f"Scientific reference graph contains a cycle: {' -> '.join(f'{item[0]}@{item[1]}' for item in cycle)}.", node[0]))
                return
            if node in visited:
                return
            visiting.add(node)
            for target in sorted(graph.get(node, set())):
                visit(target, trail + [node])
            visiting.discard(node)
            visited.add(node)

        for node in sorted(by_key):
            visit(node, [])
        return sorted(diagnostics, key=diagnostic_key)

    def canonical_chain_objects(self) -> list[tuple[str, dict[str, Any]]]:
        paths = [
            "manifests/examples/object-chain/observation.json",
            "manifests/examples/object-chain/latent-belief.json",
            "manifests/examples/object-chain/decision.json",
            "manifests/examples/object-chain/intervention.json",
            "manifests/examples/object-chain/outcome.json",
            "manifests/examples/object-chain/evidence.json",
        ]
        result: list[tuple[str, dict[str, Any]]] = []
        for relative in paths:
            data = self.read_json_contract(relative)
            if isinstance(data, dict):
                result.append((relative, data))
        return result

    def check_canonical_chain(self) -> None:
        self.diagnostics.extend(self.semantic_object_chain(self.canonical_chain_objects()))

    def scientific_instance_paths(self, view: RepositoryView) -> list[str]:
        paths: set[str] = set()
        index = self.read_view_json(view, INDEX_PATH)
        if isinstance(index, dict):
            for item in index.get("artifacts", []):
                binding = item.get("artifact") if isinstance(item, dict) else None
                if not isinstance(binding, dict):
                    continue
                relative = binding.get("path")
                if (
                    item.get("role") != "schema"
                    and isinstance(relative, str)
                    and binding.get("schema_id") in SCIENTIFIC_SCHEMA_IDS
                ):
                    paths.add(relative)
        for relative in view.iter_files():
            if not relative.endswith(".json"):
                continue
            data = self.read_view_json(view, relative)
            if isinstance(data, dict) and data.get("schema_id") in SCIENTIFIC_SCHEMA_IDS:
                paths.add(relative)
        return sorted(paths)

    def claim_register_diagnostics(self, view: RepositoryView) -> list[dict[str, Any]]:
        document_path = "docs/CLAIMS_AND_NON_CLAIMS.md"
        manifest_path = "manifests/claims/proposed-claims-and-non-claims-1.0.0.json"
        try:
            text = view.read_text(document_path)
            manifest = view.read_json(manifest_path)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            return [make_diagnostic("GA-CLAIM-REGISTER-MISMATCH", manifest_path, "Narrative or machine-readable claim register is absent or malformed.")]
        if not isinstance(manifest, dict):
            return [make_diagnostic("GA-CLAIM-REGISTER-MISMATCH", manifest_path, "Machine-readable claim register is not an object.")]
        items = manifest.get("items")
        if not isinstance(items, list):
            return [make_diagnostic("GA-CLAIM-REGISTER-MISMATCH", manifest_path, "Machine-readable claim items are absent.")]
        document_ids = re.findall(r"`(reiyah\.(?:claim|nonclaim)\.[a-z0-9.-]+)`", text)
        item_ids = [item.get("item_id") for item in items if isinstance(item, dict) and isinstance(item.get("item_id"), str)]
        diagnostics: list[dict[str, Any]] = []
        if len(item_ids) != len(set(item_ids)):
            diagnostics.append(make_diagnostic("GA-CLAIM-REGISTER-MISMATCH", manifest_path, "Machine-readable claim/non-claim IDs are not unique."))
        if set(document_ids) != set(item_ids):
            diagnostics.append(
                make_diagnostic(
                    "GA-CLAIM-REGISTER-MISMATCH",
                    manifest_path,
                    "Narrative and machine-readable claim IDs differ; "
                    f"narrative_only={sorted(set(document_ids) - set(item_ids))}, "
                    f"machine_only={sorted(set(item_ids) - set(document_ids))}.",
                )
            )
        claims = [item for item in items if isinstance(item, dict) and item.get("kind") == "claim"]
        nonclaims = [item for item in items if isinstance(item, dict) and item.get("kind") == "non_claim"]
        if len(claims) != 12 or len(nonclaims) != 20 or len(items) != 32:
            diagnostics.append(make_diagnostic("GA-CLAIM-REGISTER-MISMATCH", manifest_path, f"Frozen register must contain 12 claims and 20 non-claims; found {len(claims)} and {len(nonclaims)}."))
        for item in items:
            if not isinstance(item, dict):
                continue
            item_id = item.get("item_id") if isinstance(item.get("item_id"), str) else None
            binding = item.get("evidence_binding")
            expected_state = "evidence_gap" if item.get("kind") == "claim" else "not_applicable"
            if item.get("lifecycle_status") != "proposed" or not isinstance(binding, dict) or binding.get("state") != expected_state:
                diagnostics.append(make_diagnostic("GA-CLAIM-REGISTER-MISMATCH", manifest_path, "Claim kind, proposed status, and evidence disposition are inconsistent.", item_id))
        acceptance = manifest.get("operator_acceptance")
        if not isinstance(acceptance, dict) or acceptance != {"state": "unaccepted", "record_id": None}:
            diagnostics.append(make_diagnostic("GA-CLAIM-REGISTER-MISMATCH", manifest_path, "Claim register must remain explicitly operator-unaccepted."))
        return sorted(diagnostics, key=diagnostic_key)

    def mission_boundary_diagnostics(self, view: RepositoryView) -> list[dict[str, Any]]:
        manifest_path = "manifests/mission/reiyah-mission-1.0.0.json"
        protocol_path = "manifests/protocol/harbor-gate-a-protocol-1.0.0.json"
        charter_path = "docs/SCIENTIFIC_CHARTER.md"
        try:
            mission = view.read_json(manifest_path)
            protocol = view.read_json(protocol_path)
            charter = view.read_text(charter_path)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            return [make_diagnostic("GA-MISSION-BOUNDARY-INCOMPLETE", manifest_path, "Mission manifest, first protocol, or scientific charter is absent or malformed.")]
        if not isinstance(mission, dict) or not isinstance(protocol, dict):
            return [make_diagnostic("GA-MISSION-BOUNDARY-INCOMPLETE", manifest_path, "Mission manifest or first protocol is not an object.")]
        diagnostics: list[dict[str, Any]] = []
        exact_checks = (
            (mission.get("mission_id"), "reiyah.mission", "mission_id"),
            (mission.get("release_id"), "reiyah.mission@1.0.0", "release_id"),
            (mission.get("lifecycle_status"), "proposed", "lifecycle_status"),
            (mission.get("release_stage"), "candidate", "release_stage"),
            (mission.get("repository_identity", {}).get("project") if isinstance(mission.get("repository_identity"), dict) else None, "Reiyah", "repository project"),
            (mission.get("repository_identity", {}).get("canonical_root") if isinstance(mission.get("repository_identity"), dict) else None, str(CANONICAL_ROOT), "canonical root"),
            (mission.get("program_identity", {}).get("working_name") if isinstance(mission.get("program_identity"), dict) else None, "HARBOR", "working program name"),
            (mission.get("program_identity", {}).get("expansion") if isinstance(mission.get("program_identity"), dict) else None, "Human-Automation Readiness, Belief & Operational Risk", "proposed working program expansion"),
            (mission.get("program_identity", {}).get("name_status") if isinstance(mission.get("program_identity"), dict) else None, "proposed", "program-name status"),
            (protocol.get("protocol_id"), "reiyah.protocol.harbor-gate-a", "first protocol_id"),
            (protocol.get("release_id"), "reiyah.protocol.harbor-gate-a@1.0.0", "first protocol release_id"),
            (protocol.get("mission_release_id"), "reiyah.mission@1.0.0", "first protocol mission release"),
        )
        for actual, expected, label in exact_checks:
            if actual != expected:
                diagnostics.append(make_diagnostic("GA-MISSION-BOUNDARY-INCOMPLETE", manifest_path, f"Mission {label} is not the canonical proposed Gate A value."))
        scope = mission.get("gate_a_scope")
        required_prohibited = {
            "product runtime",
            "deployment",
            "physical-control integration",
            "private-data ingestion",
            "publication machinery",
            "model training or live inference",
            "live network dependencies",
            "operational safety or compliance claims",
        }
        prohibited = set(scope.get("prohibited", [])) if isinstance(scope, dict) and isinstance(scope.get("prohibited"), list) else set()
        if prohibited != required_prohibited or not isinstance(scope, dict) or len(scope.get("authorized", [])) != 2 or len(scope.get("advancement_requires", [])) != 2:
            diagnostics.append(make_diagnostic("GA-MISSION-BOUNDARY-INCOMPLETE", manifest_path, "Mission authorization, prohibition, and advancement boundaries are incomplete."))
        invariant_ids = {
            item.get("invariant_id")
            for item in mission.get("scientific_invariants", [])
            if isinstance(item, dict)
        }
        if len(invariant_ids) != 7 or None in invariant_ids:
            diagnostics.append(make_diagnostic("GA-MISSION-BOUNDARY-INCOMPLETE", manifest_path, "Mission must retain seven distinct scientific invariants."))
        narrative_markers = (
            "reiyah.scientific-charter",
            "Reiyah is not a driver-monitoring classifier",
            "does not authorize live sensing",
            "unit of analysis",
            "falsifi",
        )
        if any(marker.lower() not in charter.lower() for marker in narrative_markers):
            diagnostics.append(make_diagnostic("GA-MISSION-BOUNDARY-INCOMPLETE", charter_path, "Scientific charter lacks a required identity, exclusion, unit, or falsifiability boundary."))
        return sorted(diagnostics, key=diagnostic_key)

    def threat_coverage_diagnostics(self, view: RepositoryView) -> list[dict[str, Any]]:
        threat_path = "docs/THREAT_MODEL.md"
        plan_path = PLAN_PATH
        try:
            text = view.read_text(threat_path)
            plan = view.read_json(plan_path)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            return [make_diagnostic("GA-THREAT-COVERAGE-INCOMPLETE", threat_path, "Threat model or validation plan is absent or malformed.")]
        if not isinstance(plan, dict):
            return [make_diagnostic("GA-THREAT-COVERAGE-INCOMPLETE", plan_path, "Validation plan is not an object.")]
        rows: dict[str, list[str]] = {}
        for line in text.splitlines():
            match = re.match(r"^\| `(TM-[0-9]{3})` \|", line)
            if match:
                rows[match.group(1)] = [part.strip() for part in line.strip().strip("|").split("|")]
        expected = {f"TM-{number:03d}" for number in range(1, 28)}
        diagnostics: list[dict[str, Any]] = []
        if set(rows) != expected:
            diagnostics.append(make_diagnostic("GA-THREAT-COVERAGE-INCOMPLETE", threat_path, f"Threat catalogue IDs must be exactly TM-001..TM-027; missing={sorted(expected - set(rows))}, extra={sorted(set(rows) - expected)}."))
        incomplete = sorted(threat_id for threat_id, fields in rows.items() if len(fields) != 5 or any(len(field) < 12 for field in fields[1:]))
        if incomplete:
            diagnostics.append(make_diagnostic("GA-THREAT-COVERAGE-INCOMPLETE", threat_path, f"Threat rows lack meaningful scenario, prevention, detection, or residual-risk text: {incomplete}."))
        family_threats = {
            threat_id
            for family in plan.get("critical_families", [])
            if isinstance(family, dict)
            for threat_id in family.get("threat_ids", [])
            if isinstance(threat_id, str)
        }
        if not family_threats or not family_threats <= set(rows):
            diagnostics.append(make_diagnostic("GA-THREAT-COVERAGE-INCOMPLETE", plan_path, f"Critical-family threat references do not resolve: {sorted(family_threats - set(rows))}."))
        return sorted(diagnostics, key=diagnostic_key)

    def artifact_reference_diagnostics(
        self,
        view: RepositoryView,
        documents: Iterable[tuple[str, dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        """Resolve every artifact-reference-shaped value in schema-bound documents."""

        index = self.read_view_json(view, INDEX_PATH)
        indexed_by_path: dict[str, list[dict[str, Any]]] = {}
        if isinstance(index, dict):
            for item in index.get("artifacts", []):
                binding = item.get("artifact") if isinstance(item, dict) else None
                relative = binding.get("path") if isinstance(binding, dict) else None
                if isinstance(relative, str):
                    indexed_by_path.setdefault(relative, []).append(binding)

        references: list[tuple[str, list[Any], dict[str, Any]]] = []

        def visit(owner_path: str, value: Any, parts: list[Any]) -> None:
            if isinstance(value, dict):
                if {"artifact_id", "path", "sha256"} <= set(value):
                    references.append((owner_path, parts, value))
                for key, child in value.items():
                    visit(owner_path, child, parts + [key])
            elif isinstance(value, list):
                for index_value, child in enumerate(value):
                    visit(owner_path, child, parts + [index_value])

        for owner_path, document in documents:
            visit(owner_path, document, [])

        diagnostics: list[dict[str, Any]] = []
        for owner_path, parts, reference in references:
            pointer = json_pointer(parts)
            artifact_id = reference.get("artifact_id") if isinstance(reference.get("artifact_id"), str) else None
            relative = reference.get("path")
            try:
                RepositoryView.validate_relative(relative)
            except ValueError:
                diagnostics.append(make_diagnostic("GA-ARTIFACT-BINDING-INELIGIBLE", owner_path, f"{pointer}: retained artifact path is unsafe or absent: {relative!r}.", artifact_id))
                continue
            indexed = indexed_by_path.get(relative, [])
            if len(indexed) != 1:
                diagnostics.append(make_diagnostic("GA-ARTIFACT-BINDING-INELIGIBLE", owner_path, f"{pointer}: retained artifact path {relative!r} must resolve exactly once in the evidence index; matches={len(indexed)}.", artifact_id))
                continue
            index_binding = indexed[0]
            try:
                raw = view.read_bytes(relative)
            except (OSError, ValueError):
                diagnostics.append(make_diagnostic("GA-ARTIFACT-BINDING-INELIGIBLE", owner_path, f"{pointer}: retained artifact path does not resolve to current repository bytes: {relative!r}.", artifact_id))
                continue
            actual_digest = digest_bytes(raw)
            mismatches: list[str] = []
            for field in ("artifact_id", "schema_id", "version"):
                declared = reference.get(field)
                if declared is not None and declared != index_binding.get(field):
                    mismatches.append(field)
            if reference.get("sha256") != actual_digest:
                mismatches.append("sha256")
            if index_binding.get("sha256") != actual_digest:
                mismatches.append("indexed sha256")
            if relative.endswith(".json"):
                target = self.read_view_json(view, relative)
                if not isinstance(target, dict):
                    mismatches.append("target JSON")
                else:
                    for field in ("artifact_id", "schema_id", "version"):
                        declared = reference.get(field)
                        if declared is not None and target.get(field) != declared:
                            mismatches.append(f"target {field}")
            if mismatches:
                diagnostics.append(make_diagnostic("GA-ARTIFACT-BINDING-INELIGIBLE", owner_path, f"{pointer}: retained artifact reference does not bind exact indexed current bytes for {relative!r}; mismatches={sorted(set(mismatches))}.", artifact_id))
        return sorted(diagnostics, key=diagnostic_key)

    def protocol_manifest_context(
        self,
        view: RepositoryView,
        release_id: Any,
    ) -> tuple[str | None, dict[str, Any] | None, list[str]]:
        """Resolve one protocol release through the immutable ledger and current bytes."""

        mismatches: list[str] = []
        ledger = self.read_view_json(view, "manifests/manifest-release-ledger.json")
        entries = [
            entry
            for entry in ledger.get("entries", [])
            if isinstance(ledger, dict)
            and isinstance(entry, dict)
            and entry.get("manifest_kind") == "protocol"
            and entry.get("release_id") == release_id
        ] if isinstance(ledger, dict) else []
        if len(entries) != 1:
            return None, None, [f"protocol ledger matches={len(entries)}"]
        entry = entries[0]
        binding = entry.get("artifact_binding")
        relative = binding.get("path") if isinstance(binding, dict) else None
        if not isinstance(relative, str):
            return None, None, ["protocol artifact path"]
        try:
            raw = view.read_bytes(relative)
            manifest = strict_json_loads(raw.decode("utf-8"))
        except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError, StrictJSONError):
            return relative, None, ["protocol current JSON bytes"]
        if not isinstance(binding, dict) or not isinstance(manifest, dict):
            return relative, None, ["protocol binding/manifest object"]
        manifest_schema_id = manifest.get("schema_id")
        checks = (
            (binding.get("sha256"), digest_bytes(raw), "ledger sha256"),
            (binding.get("artifact_id"), manifest.get("artifact_id"), "artifact_id"),
            (binding.get("schema_id"), manifest_schema_id, "ledger schema_id"),
            (binding.get("version"), manifest.get("version"), "version"),
            (manifest.get("release_id"), release_id, "release_id"),
            (manifest.get("manifest_kind"), "protocol", "manifest_kind"),
        )
        mismatches.extend(label for actual, expected, label in checks if actual != expected)
        if manifest_schema_id not in PROTOCOL_MANIFEST_SCHEMA_IDS:
            mismatches.append("manifest schema_id")
        if isinstance(manifest.get("version"), str):
            expected_schema = (
                "https://schemas.reiyah.invalid/gate-a/"
                f"{manifest['version']}/protocol-manifest.schema.json"
            )
            if manifest_schema_id != expected_schema:
                mismatches.append("versioned manifest schema_id")
        return relative, manifest, sorted(set(mismatches))

    def protocol_definition_diagnostics(
        self,
        view: RepositoryView,
        records: Iterable[tuple[str, dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        """Resolve every protocol-governed scientific identifier through its exact registry."""

        diagnostics: list[dict[str, Any]] = []
        records_list = list(records)
        ledger = self.read_view_json(view, "manifests/manifest-release-ledger.json")
        release_ids = sorted(
            {
                *(
                    record.get("protocol_release_id")
                    for _, record in records_list
                    if isinstance(record.get("protocol_release_id"), str)
                ),
                *(
                    entry.get("release_id")
                    for entry in ledger.get("entries", [])
                    if isinstance(ledger, dict)
                    and isinstance(entry, dict)
                    and entry.get("manifest_kind") == "protocol"
                    and isinstance(entry.get("release_id"), str)
                ),
            }
        )
        registries: dict[str, tuple[str, dict[tuple[str, str], list[dict[str, Any]]], dict[str, list[dict[str, Any]]], dict[str, Any]]] = {}
        for release_id in release_ids:
            protocol_path, protocol, protocol_mismatches = self.protocol_manifest_context(view, release_id)
            if not isinstance(protocol, dict) or protocol_mismatches:
                diagnostics.append(
                    make_diagnostic(
                        "GA-PROTOCOL-DEFINITION-UNRESOLVED",
                        protocol_path or "manifests/manifest-release-ledger.json",
                        f"Protocol release cannot govern definitions from exact ledger-bound bytes; mismatches={protocol_mismatches}.",
                        release_id,
                    )
                )
                continue
            reference = protocol.get("definition_registry")
            registry_path = reference.get("path") if isinstance(reference, dict) else None
            try:
                registry_raw = view.read_bytes(registry_path)
                registry = strict_json_loads(registry_raw.decode("utf-8"))
            except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError, StrictJSONError, TypeError):
                registry_raw = None
                registry = None
            mismatches: list[str] = []
            if not isinstance(reference, dict):
                mismatches.append("typed definition_registry reference")
            if not isinstance(registry, dict) or registry_raw is None:
                mismatches.append("registry current JSON bytes")
            else:
                checks = (
                    (reference.get("schema_id"), registry.get("schema_id"), "reference schema_id"),
                    (reference.get("artifact_id"), registry.get("artifact_id"), "artifact_id"),
                    (reference.get("version"), registry.get("version"), "version"),
                    (reference.get("sha256"), digest_bytes(registry_raw), "sha256"),
                    (registry.get("protocol_release_id"), release_id, "protocol_release_id"),
                    (registry.get("version"), reference.get("version"), "registry release version"),
                )
                mismatches.extend(label for actual, expected, label in checks if actual != expected)
                if registry.get("schema_id") not in PROTOCOL_DEFINITION_REGISTRY_SCHEMA_IDS:
                    mismatches.append("target schema_id")
                diagnostics.extend(self.instance_diagnostics(registry, registry_path))
            if mismatches or not isinstance(registry, dict) or not isinstance(registry_path, str):
                diagnostics.append(
                    make_diagnostic(
                        "GA-PROTOCOL-DEFINITION-UNRESOLVED",
                        protocol_path or "manifests/manifest-release-ledger.json",
                        f"Protocol definition registry is not an exact typed release binding; mismatches={sorted(set(mismatches))}.",
                        release_id,
                    )
                )
                continue
            by_kind_id: dict[tuple[str, str], list[dict[str, Any]]] = {}
            by_id: dict[str, list[dict[str, Any]]] = {}
            seen_triples: set[tuple[str, str, str]] = set()
            definitions = registry.get("definitions")
            if not isinstance(definitions, list):
                definitions = []
            for definition in definitions:
                if not isinstance(definition, dict):
                    continue
                kind = definition.get("kind")
                definition_id = definition.get("definition_id")
                version = definition.get("version")
                if not all(isinstance(value, str) for value in (kind, definition_id, version)):
                    continue
                triple = (kind, definition_id, version)
                if triple in seen_triples:
                    diagnostics.append(make_diagnostic("GA-PROTOCOL-DEFINITION-UNRESOLVED", registry_path, f"Duplicate protocol definition identity {kind}:{definition_id}@{version}.", definition_id))
                seen_triples.add(triple)
                by_kind_id.setdefault((kind, definition_id), []).append(definition)
                by_id.setdefault(definition_id, []).append(definition)
                if (
                    definition.get("owner_protocol_release_id") != release_id
                    or definition.get("version") != registry.get("version")
                    or definition.get("lifecycle_status") == "retracted"
                ):
                    diagnostics.append(make_diagnostic("GA-PROTOCOL-DEFINITION-UNRESOLVED", registry_path, f"Definition {kind}:{definition_id}@{version} is not an active member of protocol {release_id}.", definition_id))
            ambiguous = sorted(f"{kind}:{identifier}" for (kind, identifier), matches in by_kind_id.items() if len(matches) != 1)
            if ambiguous:
                diagnostics.append(make_diagnostic("GA-PROTOCOL-DEFINITION-UNRESOLVED", registry_path, f"Registry identifiers do not resolve uniquely within kind: {ambiguous}."))
            globally_ambiguous = sorted(identifier for identifier, matches in by_id.items() if len(matches) != 1)
            if globally_ambiguous:
                diagnostics.append(make_diagnostic("GA-PROTOCOL-DEFINITION-UNRESOLVED", registry_path, f"definition_id values must be globally unique across kinds and versions: {globally_ambiguous}."))
            protocol_estimands = [
                item.get("estimand_id")
                for item in protocol.get("estimands", [])
                if isinstance(item, dict) and isinstance(item.get("estimand_id"), str)
            ]
            registry_estimands = {identifier for (kind, identifier) in by_kind_id if kind == "estimand"}
            if len(protocol_estimands) != len(set(protocol_estimands)) or set(protocol_estimands) != registry_estimands:
                diagnostics.append(
                    make_diagnostic(
                        "GA-PROTOCOL-DEFINITION-UNRESOLVED",
                        protocol_path or registry_path,
                        "Protocol estimands must be unique and exactly equal the selected registry estimand membership; "
                        f"protocol_only={sorted(set(protocol_estimands) - registry_estimands)}, registry_only={sorted(registry_estimands - set(protocol_estimands))}.",
                        release_id,
                    )
                )
            registries[release_id] = (registry_path, by_kind_id, by_id, protocol)

        bound_registry_paths = {context[0] for context in registries.values()}
        inventory_registry_paths: set[str] = set()
        for relative in view.iter_files():
            if not relative.endswith(".json"):
                continue
            document = self.read_view_json(view, relative)
            if isinstance(document, dict) and document.get("schema_id") in PROTOCOL_DEFINITION_REGISTRY_SCHEMA_IDS:
                inventory_registry_paths.add(relative)
        if inventory_registry_paths != bound_registry_paths:
            diagnostics.append(
                make_diagnostic(
                    "GA-PROTOCOL-DEFINITION-UNRESOLVED",
                    "manifests/manifest-release-ledger.json",
                    "Protocol definition registry inventory must exactly equal the set bound by ledger-valid protocol releases; "
                    f"unbound={sorted(inventory_registry_paths - bound_registry_paths)}, missing={sorted(bound_registry_paths - inventory_registry_paths)}.",
                )
            )

        resolution_cache: dict[tuple[str, str, str, str, str], dict[str, Any] | None] = {}

        def require_definition(
            owner_path: str,
            owner_id: str | None,
            release_id: Any,
            identifier: Any,
            expected_kind: str,
            pointer: str,
        ) -> dict[str, Any] | None:
            if not isinstance(identifier, str):
                return None
            cache_key = (owner_path, str(release_id), identifier, expected_kind, pointer)
            if cache_key in resolution_cache:
                return resolution_cache[cache_key]
            registry_context = registries.get(release_id)
            if registry_context is None:
                resolution_cache[cache_key] = None
                return None
            registry_path, by_kind_id, by_id, _ = registry_context
            matches = by_kind_id.get((expected_kind, identifier), [])
            if len(matches) == 1:
                resolution_cache[cache_key] = matches[0]
                return matches[0]
            observed_kinds = sorted({item.get("kind") for item in by_id.get(identifier, []) if isinstance(item.get("kind"), str)})
            diagnostics.append(
                make_diagnostic(
                    "GA-PROTOCOL-DEFINITION-UNRESOLVED",
                    owner_path,
                    f"{pointer}: {identifier!r} must resolve exactly once as {expected_kind!r} in {registry_path}; matches={len(matches)}, observed_kinds={observed_kinds}.",
                    owner_id,
                )
            )
            resolution_cache[cache_key] = None
            return None

        source_ledger = self.read_view_json(view, ACTIVE_SOURCE_LEDGER_PATH)
        source_ids = {
            source.get("source_id")
            for source in source_ledger.get("records", [])
            if isinstance(source_ledger, dict) and isinstance(source, dict) and isinstance(source.get("source_id"), str)
        } if isinstance(source_ledger, dict) else set()

        def require_actor(
            owner_path: str,
            owner_id: str | None,
            release_id: Any,
            actor_type: Any,
            actor_id: Any,
            pointer: str,
        ) -> None:
            if actor_type in {"software", "model", "derived_process"}:
                require_definition(owner_path, owner_id, release_id, actor_id, "producer", pointer)
            elif actor_type == "human":
                # Human actor identifiers are deliberately opaque/pseudonymous here.
                # Repository definitions cannot authenticate a person or confer authority.
                return
            elif actor_type == "instrument":
                require_definition(owner_path, owner_id, release_id, actor_id, "sensor", pointer)
            elif actor_type == "external_source" and actor_id not in source_ids:
                diagnostics.append(make_diagnostic("GA-PROTOCOL-DEFINITION-UNRESOLVED", owner_path, f"{pointer}: external source actor {actor_id!r} does not resolve in the exact source ledger.", owner_id))
            elif actor_type not in {"software", "model", "derived_process", "human", "instrument", "external_source"}:
                diagnostics.append(make_diagnostic("GA-PROTOCOL-DEFINITION-UNRESOLVED", owner_path, f"{pointer}: unknown actor/producer type {actor_type!r}.", owner_id))

        for owner_path, record in records_list:
            release_id = record.get("protocol_release_id")
            if release_id not in registries:
                continue
            owner_id = object_identifier(record)
            provenance = record.get("provenance")
            if isinstance(provenance, dict):
                require_actor(owner_path, owner_id, release_id, provenance.get("producer_type"), provenance.get("producer_id"), "/provenance/producer_id")
                require_definition(owner_path, owner_id, release_id, provenance.get("method_id"), "method", "/provenance/method_id")
            for event_index, event in enumerate(record.get("lifecycle_history", [])):
                actor = event.get("actor") if isinstance(event, dict) else None
                if isinstance(actor, dict):
                    require_actor(owner_path, owner_id, release_id, actor.get("actor_type"), actor.get("actor_id"), f"/lifecycle_history/{event_index}/actor/actor_id")

            def resolve_generic_rules(value: Any, parts: list[Any]) -> None:
                if isinstance(value, dict):
                    for key, child in value.items():
                        pointer = json_pointer(parts + [key])
                        if key == "rule_id":
                            require_definition(owner_path, owner_id, release_id, child, "rule", pointer)
                        elif key == "rule_ids" and isinstance(child, list):
                            for index, rule_id in enumerate(child):
                                require_definition(owner_path, owner_id, release_id, rule_id, "rule", json_pointer(parts + [key, index]))
                        resolve_generic_rules(child, parts + [key])
                elif isinstance(value, list):
                    for index, child in enumerate(value):
                        resolve_generic_rules(child, parts + [index])

            resolve_generic_rules(record, [])
            context_rules = record.get("context_rules")
            if isinstance(context_rules, dict):
                for field in (
                    "encounter_construction_rule_id",
                    "object_identity_rule_id",
                    "temporal_correspondence_rule_id",
                ):
                    require_definition(owner_path, owner_id, release_id, context_rules.get(field), "rule", f"/context_rules/{field}")
            schema_id = record.get("schema_id")
            record_kind = SCHEMA_OBJECT_KINDS.get(schema_id)
            if record_kind is not None:
                for rule_index, rule_id in enumerate(record.get("validity", {}).get("rule_ids", [])) if isinstance(record.get("validity"), dict) else []:
                    require_definition(owner_path, owner_id, release_id, rule_id, "rule", f"/validity/rule_ids/{rule_index}")
                event_times: list[tuple[str, Any]] = []
                if isinstance(record.get("event_time"), dict):
                    event_times.append(("/event_time/clock_id", record["event_time"].get("clock_id")))
                window = record.get("measurement_window")
                if isinstance(window, dict):
                    for end in ("start", "end"):
                        point = window.get(end)
                        if isinstance(point, dict):
                            event_times.append((f"/measurement_window/{end}/clock_id", point.get("clock_id")))
                for pointer, clock_id in event_times:
                    require_definition(owner_path, owner_id, release_id, clock_id, "clock", pointer)
                if record_kind in {"observation", "outcome"}:
                    for measurement_index, measurement in enumerate(record.get("measurements", [])):
                        if not isinstance(measurement, dict):
                            continue
                        if "construct_id" in measurement:
                            require_definition(owner_path, owner_id, release_id, measurement.get("construct_id"), "construct", f"/measurements/{measurement_index}/construct_id")
                        if "sensor_id" in measurement:
                            require_definition(owner_path, owner_id, release_id, measurement.get("sensor_id"), "sensor", f"/measurements/{measurement_index}/sensor_id")
                        value = measurement.get("value")
                        if isinstance(value, dict) and "rule_id" in value:
                            require_definition(owner_path, owner_id, release_id, value.get("rule_id"), "rule", f"/measurements/{measurement_index}/value/rule_id")
                if record_kind == "latent_belief":
                    state_space = require_definition(owner_path, owner_id, release_id, record.get("state_space_id"), "state_space", "/state_space_id")
                    members = set(state_space.get("member_ids", [])) if isinstance(state_space, dict) and isinstance(state_space.get("member_ids"), list) else set()
                    observed_members = {
                        component.get("state_id")
                        for component in record.get("belief", {}).get("components", [])
                        if isinstance(record.get("belief"), dict) and isinstance(component, dict) and isinstance(component.get("state_id"), str)
                    }
                    if state_space is not None and observed_members != members:
                        diagnostics.append(make_diagnostic("GA-PROTOCOL-DEFINITION-UNRESOLVED", owner_path, f"/belief/components: state members must exactly equal selected state-space membership; missing={sorted(members - observed_members)}, extra={sorted(observed_members - members)}.", owner_id))
                    require_definition(owner_path, owner_id, release_id, record.get("inference_specification_id"), "inference_specification", "/inference_specification_id")
                elif record_kind == "decision":
                    choice_set = require_definition(owner_path, owner_id, release_id, record.get("choice_set_id"), "choice_set", "/choice_set_id")
                    members = set(choice_set.get("member_ids", [])) if isinstance(choice_set, dict) and isinstance(choice_set.get("member_ids"), list) else set()
                    selected_action = record.get("selected_action")
                    selected_value = selected_action.get("value") if isinstance(selected_action, dict) and selected_action.get("state") == "observed" else None
                    if choice_set is not None and isinstance(selected_value, str) and selected_value not in members:
                        diagnostics.append(make_diagnostic("GA-PROTOCOL-DEFINITION-UNRESOLVED", owner_path, f"/selected_action/value: {selected_value!r} is not a member of choice set {record.get('choice_set_id')!r}.", owner_id))
                    require_definition(owner_path, owner_id, release_id, record.get("decision_rule_id"), "decision_rule", "/decision_rule_id")
                elif record_kind == "intervention":
                    require_definition(owner_path, owner_id, release_id, record.get("assignment_mechanism_id"), "assignment_mechanism", "/assignment_mechanism_id")
                    for field in ("delivered_level", "received_level", "adherence"):
                        value = record.get(field)
                        if isinstance(value, dict) and "rule_id" in value:
                            require_definition(owner_path, owner_id, release_id, value.get("rule_id"), "rule", f"/{field}/rule_id")
                elif record_kind == "outcome":
                    require_definition(owner_path, owner_id, release_id, record.get("outcome_definition_id"), "outcome_definition", "/outcome_definition_id")
                elif record_kind == "evidence":
                    require_definition(owner_path, owner_id, release_id, record.get("method_id"), "method", "/method_id")
                    for criterion_index, criterion_id in enumerate(record.get("criterion_ids", [])):
                        require_definition(owner_path, owner_id, release_id, criterion_id, "decision_rule", f"/criterion_ids/{criterion_index}")
            elif schema_id == EXPERIMENT_SCHEMA_ID:
                for index, identifier in enumerate(record.get("outcome_definition_ids", [])):
                    require_definition(owner_path, owner_id, release_id, identifier, "outcome_definition", f"/outcome_definition_ids/{index}")
                for index, identifier in enumerate(record.get("estimand_ids", [])):
                    require_definition(owner_path, owner_id, release_id, identifier, "estimand", f"/estimand_ids/{index}")
                for index, identifier in enumerate(record.get("inclusion_rules", [])):
                    require_definition(owner_path, owner_id, release_id, identifier, "inclusion_rule", f"/inclusion_rules/{index}")
                for index, identifier in enumerate(record.get("exclusion_rules", [])):
                    require_definition(owner_path, owner_id, release_id, identifier, "exclusion_rule", f"/exclusion_rules/{index}")
                assignment = record.get("assignment_mechanism")
                if isinstance(assignment, dict):
                    require_definition(owner_path, owner_id, release_id, assignment.get("mechanism_id"), "assignment_mechanism", "/assignment_mechanism/mechanism_id")
                for index, assumption in enumerate(record.get("identification_assumptions", [])):
                    if isinstance(assumption, dict):
                        require_definition(owner_path, owner_id, release_id, assumption.get("assumption_id"), "assumption", f"/identification_assumptions/{index}/assumption_id")
                for index, boundary in enumerate(record.get("validity_boundaries", [])):
                    if isinstance(boundary, dict):
                        require_definition(owner_path, owner_id, release_id, boundary.get("boundary_id"), "validity_boundary", f"/validity_boundaries/{index}/boundary_id")
                policy = record.get("epistemic_policy")
                if isinstance(policy, dict):
                    require_definition(owner_path, owner_id, release_id, policy.get("abstention_rule_id"), "rule", "/epistemic_policy/abstention_rule_id")
                subgroup = record.get("subgroup_plan")
                if isinstance(subgroup, dict):
                    for index, identifier in enumerate(subgroup.get("group_definition_ids", [])):
                        require_definition(owner_path, owner_id, release_id, identifier, "group", f"/subgroup_plan/group_definition_ids/{index}")
                    require_definition(owner_path, owner_id, release_id, subgroup.get("minimum_information_rule_id"), "minimum_information_rule", "/subgroup_plan/minimum_information_rule_id")
                analysis = record.get("analysis_plan")
                if isinstance(analysis, dict):
                    require_definition(owner_path, owner_id, release_id, analysis.get("analysis_specification_id"), "analysis_specification", "/analysis_plan/analysis_specification_id")
                    require_definition(owner_path, owner_id, release_id, analysis.get("uncertainty_method_id"), "uncertainty_method", "/analysis_plan/uncertainty_method_id")
                    require_definition(owner_path, owner_id, release_id, analysis.get("multiplicity_rule_id"), "multiplicity_rule", "/analysis_plan/multiplicity_rule_id")
                    for index, identifier in enumerate(analysis.get("decision_rule_ids", [])):
                        require_definition(owner_path, owner_id, release_id, identifier, "decision_rule", f"/analysis_plan/decision_rule_ids/{index}")
            elif schema_id == RESULT_SCHEMA_ID:
                require_definition(owner_path, owner_id, release_id, record.get("analysis_specification_id"), "analysis_specification", "/analysis_specification_id")
                require_definition(owner_path, owner_id, release_id, record.get("primary_metric_id"), "metric", "/primary_metric_id")
                for metric_index, metric in enumerate(record.get("metric_results", [])):
                    if not isinstance(metric, dict):
                        continue
                    require_definition(owner_path, owner_id, release_id, metric.get("metric_id"), "metric", f"/metric_results/{metric_index}/metric_id")
                    require_definition(owner_path, owner_id, release_id, metric.get("estimand_id"), "estimand", f"/metric_results/{metric_index}/estimand_id")
                    require_definition(owner_path, owner_id, release_id, metric.get("outcome_definition_id"), "outcome_definition", f"/metric_results/{metric_index}/outcome_definition_id")
                    require_definition(owner_path, owner_id, release_id, metric.get("abstention_rule_id"), "rule", f"/metric_results/{metric_index}/abstention_rule_id")
                    require_definition(owner_path, owner_id, release_id, metric.get("decision_rule_id"), "decision_rule", f"/metric_results/{metric_index}/decision_rule_id")
                    disposition = metric.get("worst_group_disposition")
                    if isinstance(disposition, dict) and "selection_rule_id" in disposition:
                        require_definition(owner_path, owner_id, release_id, disposition.get("selection_rule_id"), "rule", f"/metric_results/{metric_index}/worst_group_disposition/selection_rule_id")
                    for index, rule_id in enumerate(metric.get("validity", {}).get("rule_ids", [])) if isinstance(metric.get("validity"), dict) else []:
                        require_definition(owner_path, owner_id, release_id, rule_id, "rule", f"/metric_results/{metric_index}/validity/rule_ids/{index}")
                    uncertainty = metric.get("uncertainty")
                    if isinstance(uncertainty, dict) and "method_id" in uncertainty:
                        require_definition(owner_path, owner_id, release_id, uncertainty.get("method_id"), "uncertainty_method", f"/metric_results/{metric_index}/uncertainty/method_id")
                    for group_index, group in enumerate(metric.get("group_results", [])):
                        if not isinstance(group, dict):
                            continue
                        require_definition(owner_path, owner_id, release_id, group.get("group_id"), "group", f"/metric_results/{metric_index}/group_results/{group_index}/group_id")
                        uncertainty = group.get("uncertainty")
                        if isinstance(uncertainty, dict) and "method_id" in uncertainty:
                            require_definition(owner_path, owner_id, release_id, uncertainty.get("method_id"), "uncertainty_method", f"/metric_results/{metric_index}/group_results/{group_index}/uncertainty/method_id")
            elif schema_id == ANALYSIS_SPECIFICATION_SCHEMA_ID:
                require_definition(owner_path, owner_id, release_id, record.get("primary_metric_id"), "metric", "/primary_metric_id")
                for index, identifier in enumerate(record.get("outcome_definition_ids", [])):
                    require_definition(owner_path, owner_id, release_id, identifier, "outcome_definition", f"/outcome_definition_ids/{index}")
                for index, identifier in enumerate(record.get("estimand_ids", [])):
                    require_definition(owner_path, owner_id, release_id, identifier, "estimand", f"/estimand_ids/{index}")
                for index, identifier in enumerate(record.get("inclusion_rules", [])):
                    require_definition(owner_path, owner_id, release_id, identifier, "inclusion_rule", f"/inclusion_rules/{index}")
                for index, identifier in enumerate(record.get("exclusion_rules", [])):
                    require_definition(owner_path, owner_id, release_id, identifier, "exclusion_rule", f"/exclusion_rules/{index}")
                assignment = record.get("assignment_mechanism")
                if isinstance(assignment, dict):
                    require_definition(owner_path, owner_id, release_id, assignment.get("mechanism_id"), "assignment_mechanism", "/assignment_mechanism/mechanism_id")
                for index, assumption in enumerate(record.get("identification_assumptions", [])):
                    if isinstance(assumption, dict):
                        require_definition(owner_path, owner_id, release_id, assumption.get("assumption_id"), "assumption", f"/identification_assumptions/{index}/assumption_id")
                for index, boundary in enumerate(record.get("validity_boundaries", [])):
                    if isinstance(boundary, dict):
                        require_definition(owner_path, owner_id, release_id, boundary.get("boundary_id"), "validity_boundary", f"/validity_boundaries/{index}/boundary_id")
                require_definition(owner_path, owner_id, release_id, record.get("observation_boundary_id"), "validity_boundary", "/observation_boundary_id")
                epistemic_policy = record.get("epistemic_policy")
                if isinstance(epistemic_policy, dict):
                    require_definition(owner_path, owner_id, release_id, epistemic_policy.get("abstention_rule_id"), "rule", "/epistemic_policy/abstention_rule_id")
                subgroup = record.get("subgroup_plan")
                if isinstance(subgroup, dict):
                    for index, identifier in enumerate(subgroup.get("group_definition_ids", [])):
                        require_definition(owner_path, owner_id, release_id, identifier, "group", f"/subgroup_plan/group_definition_ids/{index}")
                    require_definition(owner_path, owner_id, release_id, subgroup.get("minimum_information_rule_id"), "minimum_information_rule", "/subgroup_plan/minimum_information_rule_id")
                analysis = record.get("analysis_plan")
                if isinstance(analysis, dict):
                    require_definition(owner_path, owner_id, release_id, analysis.get("analysis_specification_id"), "analysis_specification", "/analysis_plan/analysis_specification_id")
                    require_definition(owner_path, owner_id, release_id, analysis.get("uncertainty_method_id"), "uncertainty_method", "/analysis_plan/uncertainty_method_id")
                    require_definition(owner_path, owner_id, release_id, analysis.get("multiplicity_rule_id"), "multiplicity_rule", "/analysis_plan/multiplicity_rule_id")
                    for index, identifier in enumerate(analysis.get("decision_rule_ids", [])):
                        require_definition(owner_path, owner_id, release_id, identifier, "decision_rule", f"/analysis_plan/decision_rule_ids/{index}")
                for metric_index, metric in enumerate(record.get("metric_specifications", [])):
                    if not isinstance(metric, dict):
                        continue
                    require_definition(owner_path, owner_id, release_id, metric.get("metric_id"), "metric", f"/metric_specifications/{metric_index}/metric_id")
                    require_definition(owner_path, owner_id, release_id, metric.get("estimand_id"), "estimand", f"/metric_specifications/{metric_index}/estimand_id")
                    require_definition(owner_path, owner_id, release_id, metric.get("outcome_definition_id"), "outcome_definition", f"/metric_specifications/{metric_index}/outcome_definition_id")
                    require_definition(owner_path, owner_id, release_id, metric.get("decision_rule_id"), "decision_rule", f"/metric_specifications/{metric_index}/decision_rule_id")
                    require_definition(owner_path, owner_id, release_id, metric.get("abstention_rule_id"), "rule", f"/metric_specifications/{metric_index}/abstention_rule_id")
                    require_definition(owner_path, owner_id, release_id, metric.get("uncertainty_method_id"), "uncertainty_method", f"/metric_specifications/{metric_index}/uncertainty_method_id")
            elif schema_id == PREREGISTRATION_RECORD_SCHEMA_ID:
                analysis_reference = record.get("analysis_specification")
                if isinstance(analysis_reference, dict):
                    require_definition(owner_path, owner_id, release_id, analysis_reference.get("analysis_specification_id"), "analysis_specification", "/analysis_specification/analysis_specification_id")
                boundary = record.get("observation_boundary")
                if isinstance(boundary, dict):
                    require_definition(owner_path, owner_id, release_id, boundary.get("boundary_id"), "validity_boundary", "/observation_boundary/boundary_id")
        return sorted(diagnostics, key=diagnostic_key)

    def scientific_lifecycle_diagnostics(
        self,
        records: Iterable[tuple[str, dict[str, Any]]],
        view: RepositoryView,
    ) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        lineage_groups: dict[tuple[str, str], list[tuple[str, dict[str, Any]]]] = {}

        def lifecycle_identity(record: dict[str, Any]) -> tuple[str | None, str | None]:
            schema_id = record.get("schema_id")
            kind = SCHEMA_OBJECT_KINDS.get(schema_id)
            identifier = record.get("object_id") if kind is not None else None
            if schema_id == EXPERIMENT_SCHEMA_ID:
                kind = "experiment"
                identifier = record.get("experiment_id")
            elif schema_id == RESULT_SCHEMA_ID:
                kind = "result"
                identifier = record.get("result_id")
            return kind if isinstance(kind, str) else None, identifier if isinstance(identifier, str) else None

        records_list = list(records)
        for relative, record in records_list:
            kind, identifier = lifecycle_identity(record)
            if kind is not None and identifier is not None:
                lineage_groups.setdefault((kind, identifier), []).append((relative, record))
        for relative, record in records_list:
            schema_id = record.get("schema_id")
            record_kind = SCHEMA_OBJECT_KINDS.get(schema_id)
            record_id = record.get("object_id") if record_kind is not None else None
            lineage_rule = "GA-SCIENTIFIC-LINEAGE"
            if schema_id == EXPERIMENT_SCHEMA_ID:
                record_kind = "experiment"
                record_id = record.get("experiment_id")
            elif schema_id == RESULT_SCHEMA_ID:
                record_kind = "result"
                record_id = record.get("result_id")
                lineage_rule = "GA-RESULT-LINEAGE"
            if record_kind is None:
                continue
            history = record.get("lifecycle_history")
            if not isinstance(history, list) or not history:
                diagnostics.append(make_diagnostic("GA-STATUS-HISTORY-CURRENT", relative, "Scientific lifecycle_history must be present and nonempty.", record_id if isinstance(record_id, str) else None))
                continue
            statuses = [event.get("status") if isinstance(event, dict) else None for event in history]
            diagnostics.extend(
                self.status_diagnostics(
                    {"status_history": statuses},
                    relative,
                    record_id if isinstance(record_id, str) else None,
                    view=view,
                    record_kind=record_kind,
                    protocol_release_id=record.get("protocol_release_id") if isinstance(record.get("protocol_release_id"), str) else None,
                )
            )
            diagnostics.extend(self.history_time_diagnostics(history, relative, record_id if isinstance(record_id, str) else None))
            event_ids: set[str] = set()
            for index, event in enumerate(history):
                if not isinstance(event, dict):
                    diagnostics.append(make_diagnostic("GA-STATUS-HISTORY-CURRENT", relative, f"Lifecycle event {index} is not an object.", record_id if isinstance(record_id, str) else None))
                    continue
                event_id = event.get("event_id")
                if not isinstance(event_id, str) or event_id in event_ids:
                    diagnostics.append(make_diagnostic("GA-STATUS-HISTORY-CURRENT", relative, f"Lifecycle event_id must be present and unique: {event_id!r}.", record_id if isinstance(record_id, str) else None))
                else:
                    event_ids.add(event_id)
                if event.get("sequence") != index + 1:
                    diagnostics.append(make_diagnostic("GA-STATUS-HISTORY-CURRENT", relative, f"Lifecycle sequences must be contiguous 1..N; event {index} declares {event.get('sequence')!r}.", record_id if isinstance(record_id, str) else None))
                expected_prior_status = None if index == 0 else statuses[index - 1]
                if event.get("prior_status") != expected_prior_status:
                    diagnostics.append(make_diagnostic("GA-STATUS-HISTORY-CURRENT", relative, f"Lifecycle event {index} prior_status does not equal the preceding event status.", record_id if isinstance(record_id, str) else None))
                prior_artifact = event.get("prior_artifact")
                if index == 0:
                    if prior_artifact is not None:
                        diagnostics.append(make_diagnostic(lineage_rule, relative, "Initial lifecycle event cannot bind a predecessor artifact.", record_id if isinstance(record_id, str) else None))
                    continue
                if not isinstance(prior_artifact, dict):
                    diagnostics.append(make_diagnostic(lineage_rule, relative, f"Lifecycle event {index} must bind its exact predecessor artifact.", record_id if isinstance(record_id, str) else None))
                    continue
                prior_path = prior_artifact.get("path")
                prior_version = prior_artifact.get("version")
                current_version = record.get("version")
                version_pattern = r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
                prior_match = re.fullmatch(version_pattern, prior_version) if isinstance(prior_version, str) else None
                current_match = re.fullmatch(version_pattern, current_version) if isinstance(current_version, str) else None
                mismatches: list[str] = []
                if prior_artifact.get("record_id") != record_id:
                    mismatches.append("record_id")
                if prior_artifact.get("record_kind") != record_kind:
                    mismatches.append("record_kind")
                if prior_artifact.get("schema_id") != schema_id:
                    mismatches.append("schema_id")
                if prior_path == relative:
                    mismatches.append("distinct path")
                if not prior_match or not current_match or tuple(map(int, prior_match.groups())) >= tuple(map(int, current_match.groups())):
                    mismatches.append("older version")
                try:
                    prior_raw = view.read_bytes(prior_path)
                    prior_record = strict_json_loads(prior_raw.decode("utf-8"))
                except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError, StrictJSONError, TypeError):
                    prior_raw = None
                    prior_record = None
                    mismatches.append("current predecessor bytes")
                if prior_raw is not None and prior_artifact.get("sha256") != digest_bytes(prior_raw):
                    mismatches.append("sha256")
                if isinstance(prior_record, dict):
                    prior_record_kind = SCHEMA_OBJECT_KINDS.get(prior_record.get("schema_id"))
                    if prior_record.get("schema_id") == EXPERIMENT_SCHEMA_ID:
                        prior_record_kind = "experiment"
                    elif prior_record.get("schema_id") == RESULT_SCHEMA_ID:
                        prior_record_kind = "result"
                    checks = (
                        (prior_record.get("artifact_id"), prior_artifact.get("artifact_id"), "artifact_id"),
                        (object_identifier(prior_record), record_id, "logical record_id"),
                        (prior_record_kind, record_kind, "target record_kind"),
                        (prior_record.get("version"), prior_version, "target version"),
                        (prior_record.get("lifecycle_status"), event.get("prior_status"), "target lifecycle_status"),
                    )
                    mismatches.extend(label for actual, expected, label in checks if actual != expected)
                    prior_history = prior_record.get("lifecycle_history")
                    if not isinstance(prior_history, list) or len(prior_history) != index or history[:index] != prior_history:
                        mismatches.append("exact append-only lifecycle_history prefix")
                if mismatches:
                    diagnostics.append(make_diagnostic(lineage_rule, relative, f"Lifecycle predecessor is ineligible; mismatches={sorted(set(mismatches))}.", record_id if isinstance(record_id, str) else None))
            if statuses[-1] != record.get("lifecycle_status"):
                diagnostics.append(make_diagnostic("GA-STATUS-HISTORY-CURRENT", relative, "Current lifecycle_status does not equal the final lifecycle event.", record_id if isinstance(record_id, str) else None))
        for (record_kind, record_id), group in sorted(lineage_groups.items()):
            lineage_rule = "GA-RESULT-LINEAGE" if record_kind == "result" else "GA-SCIENTIFIC-LINEAGE"
            paths = {relative for relative, _ in group}
            versions = [record.get("version") for _, record in group]
            artifact_ids = [record.get("artifact_id") for _, record in group]
            issues: list[str] = []
            if any(not isinstance(version, str) for version in versions) or len(versions) != len(set(versions)):
                issues.append("unique exact versions")
            if any(not isinstance(artifact_id, str) for artifact_id in artifact_ids) or len(artifact_ids) != len(set(artifact_ids)):
                issues.append("unique artifact IDs")
            predecessor_by_path: dict[str, str | None] = {}
            children_by_path: dict[str, set[str]] = {relative: set() for relative in paths}
            for relative, record in group:
                history = record.get("lifecycle_history")
                predecessor: str | None = None
                if isinstance(history, list) and len(history) > 1 and isinstance(history[-1], dict):
                    prior_artifact = history[-1].get("prior_artifact")
                    predecessor = prior_artifact.get("path") if isinstance(prior_artifact, dict) and isinstance(prior_artifact.get("path"), str) else None
                    if predecessor not in paths:
                        issues.append(f"{relative} immediate predecessor resolves within the logical-record group")
                    else:
                        children_by_path[predecessor].add(relative)
                elif not isinstance(history, list) or len(history) != 1:
                    issues.append(f"{relative} root/successor lifecycle shape")
                predecessor_by_path[relative] = predecessor
            roots = sorted(relative for relative, predecessor in predecessor_by_path.items() if predecessor is None)
            heads = sorted(relative for relative, children in children_by_path.items() if not children)
            branches = sorted(relative for relative, children in children_by_path.items() if len(children) > 1)
            if len(roots) != 1:
                issues.append(f"exactly one root (observed {roots})")
            if len(heads) != 1:
                issues.append(f"exactly one current head (observed {heads})")
            if branches:
                issues.append(f"no branching predecessors (observed {branches})")
            if len(roots) == 1:
                visited: set[str] = set()
                current: str | None = roots[0]
                while current is not None and current not in visited:
                    visited.add(current)
                    children = children_by_path.get(current, set())
                    current = next(iter(children)) if len(children) == 1 else None
                if visited != paths:
                    issues.append(f"one acyclic connected chain (unvisited {sorted(paths - visited)})")
            if issues:
                diagnostics.append(
                    make_diagnostic(
                        lineage_rule,
                        sorted(paths)[-1],
                        f"Scientific lifecycle versions must form one immutable linear root-to-head chain; violations={sorted(set(issues))}.",
                        record_id,
                    )
                )
        return sorted(diagnostics, key=diagnostic_key)

    def preregistration_diagnostics(
        self,
        view: RepositoryView,
        owner_path: str,
        experiment: dict[str, Any],
    ) -> list[dict[str, Any]]:
        preregistration = experiment.get("preregistration")
        if not isinstance(preregistration, dict):
            return []
        experiment_id = experiment.get("experiment_id") if isinstance(experiment.get("experiment_id"), str) else None
        reference = preregistration.get("retained_artifact")
        diagnostics: list[dict[str, Any]] = []
        if not isinstance(reference, dict) or not isinstance(reference.get("path"), str):
            if preregistration.get("status") == "preregistered":
                diagnostics.append(make_diagnostic("GA-ARTIFACT-BINDING-INELIGIBLE", owner_path, "Preregistered experiment lacks a typed retained preregistration artifact.", experiment_id))
            return diagnostics
        relative = reference["path"]
        try:
            raw = view.read_bytes(relative)
            record = strict_json_loads(raw.decode("utf-8"))
        except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError, StrictJSONError):
            return [make_diagnostic("GA-ARTIFACT-BINDING-INELIGIBLE", owner_path, f"Preregistration artifact does not resolve to current JSON bytes: {relative!r}.", experiment_id)]
        binding_mismatches: list[str] = []
        freeze_mismatches: list[str] = []
        chronology_mismatches: list[str] = []
        if not isinstance(record, dict):
            binding_mismatches.append("record object")
        else:
            diagnostics.extend(self.instance_diagnostics(record, relative))
            diagnostics.extend(self.artifact_reference_diagnostics(view, [(relative, record)]))
            checks = (
                (reference.get("schema_id"), PREREGISTRATION_RECORD_SCHEMA_ID, "reference schema_id"),
                (record.get("schema_id"), PREREGISTRATION_RECORD_SCHEMA_ID, "target schema_id"),
                (record.get("artifact_id"), reference.get("artifact_id"), "artifact_id"),
                (record.get("version"), reference.get("version"), "version"),
                (record.get("experiment", {}).get("experiment_id") if isinstance(record.get("experiment"), dict) else None, experiment.get("experiment_id"), "experiment_id"),
                (record.get("experiment", {}).get("version") if isinstance(record.get("experiment"), dict) else None, experiment.get("version"), "experiment version"),
                (record.get("protocol_release_id"), experiment.get("protocol_release_id"), "protocol_release_id"),
            )
            binding_mismatches.extend(label for actual, expected, label in checks if actual != expected)
            if reference.get("sha256") != digest_bytes(raw):
                binding_mismatches.append("sha256")
            if record.get("observation_boundary") != preregistration.get("observation_boundary"):
                freeze_mismatches.append("experiment/preregistration observation_boundary")
            frozen_at = parse_exact_utc(record.get("frozen_at"))
            boundary = record.get("observation_boundary")
            opens_at = parse_exact_utc(boundary.get("opens_at")) if isinstance(boundary, dict) else None
            if frozen_at is None or opens_at is None or frozen_at >= opens_at:
                chronology_mismatches.append("frozen_at before observation boundary")
            preregistration_events = [
                event
                for event in experiment.get("lifecycle_history", [])
                if isinstance(event, dict) and event.get("status") == "preregistered"
            ]
            analysis_reference = record.get("analysis_specification")
            if isinstance(analysis_reference, dict) and isinstance(analysis_reference.get("path"), str):
                try:
                    analysis_raw = view.read_bytes(analysis_reference["path"])
                    analysis_document = strict_json_loads(analysis_raw.decode("utf-8"))
                except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError, StrictJSONError):
                    analysis_raw = None
                    analysis_document = None
                    binding_mismatches.append("analysis specification bytes")
                else:
                    if analysis_reference.get("sha256") != digest_bytes(analysis_raw):
                        binding_mismatches.append("analysis specification sha256")
                    if not isinstance(analysis_document, dict):
                        binding_mismatches.append("analysis specification object")
                    else:
                        diagnostics.extend(self.instance_diagnostics(analysis_document, analysis_reference["path"]))
                        identity_checks = (
                            (analysis_reference.get("schema_id"), ANALYSIS_SPECIFICATION_SCHEMA_ID, "analysis reference schema_id"),
                            (analysis_document.get("schema_id"), ANALYSIS_SPECIFICATION_SCHEMA_ID, "analysis target schema_id"),
                            (analysis_document.get("artifact_id"), analysis_reference.get("artifact_id"), "analysis artifact_id"),
                            (analysis_document.get("analysis_specification_id"), analysis_reference.get("analysis_specification_id"), "analysis_specification_id"),
                            (analysis_document.get("version"), analysis_reference.get("version"), "analysis version"),
                            (analysis_document.get("protocol_release_id"), experiment.get("protocol_release_id"), "analysis protocol_release_id"),
                        )
                        binding_mismatches.extend(label for actual, expected, label in identity_checks if actual != expected)
                        experiment_analysis_id = experiment.get("analysis_plan", {}).get("analysis_specification_id") if isinstance(experiment.get("analysis_plan"), dict) else None
                        if analysis_document.get("analysis_specification_id") != experiment_analysis_id:
                            freeze_mismatches.append("experiment analysis_specification_id")
                        parity_fields = (
                            "target_population",
                            "unit_of_analysis",
                            "sampling_frame",
                            "observation_window",
                            "exposure",
                            "comparator",
                            "outcome_definition_ids",
                            "estimand_ids",
                            "inclusion_rules",
                            "exclusion_rules",
                            "assignment_mechanism",
                            "identification_assumptions",
                            "validity_boundaries",
                            "epistemic_policy",
                            "subgroup_plan",
                            "analysis_plan",
                        )
                        freeze_mismatches.extend(
                            field
                            for field in parity_fields
                            if analysis_document.get(field) != experiment.get(field)
                        )
                        if isinstance(boundary, dict) and analysis_document.get("observation_boundary_id") != boundary.get("boundary_id"):
                            freeze_mismatches.append("analysis observation_boundary_id")
            else:
                binding_mismatches.append("analysis specification reference")
            if preregistration.get("status") == "preregistered":
                registered_at = parse_exact_utc(preregistration.get("registered_at"))
                if len(preregistration_events) != 1:
                    chronology_mismatches.append("one preregistered lifecycle event")
                    event_time = None
                else:
                    event_time = parse_exact_utc(preregistration_events[0].get("recorded_at"))
                if (
                    frozen_at is None
                    or registered_at is None
                    or event_time is None
                    or opens_at is None
                    or not (frozen_at <= registered_at <= event_time < opens_at)
                ):
                    chronology_mismatches.append("frozen_at <= registered_at <= preregistered event < boundary opens_at")
        if binding_mismatches:
            diagnostics.append(make_diagnostic("GA-ARTIFACT-BINDING-INELIGIBLE", owner_path, f"Preregistration record or nested analysis artifact does not bind exact typed current bytes; mismatches={sorted(set(binding_mismatches))}.", experiment_id))
        if freeze_mismatches:
            diagnostics.append(make_diagnostic("GA-PREREGISTRATION-FREEZE-MISMATCH", owner_path, f"Preregistered analysis does not exactly freeze the experiment specification; mismatches={sorted(set(freeze_mismatches))}.", experiment_id))
        if chronology_mismatches:
            diagnostics.append(make_diagnostic("GA-PREREGISTRATION-CHRONOLOGY", owner_path, f"Preregistration chronology is ineligible; mismatches={sorted(set(chronology_mismatches))}.", experiment_id))
        return sorted(diagnostics, key=diagnostic_key)

    def analysis_specification_diagnostics(
        self,
        view: RepositoryView,
        relative: str,
        analysis: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Validate a frozen analysis internally, independently of any later result."""

        analysis_id = analysis.get("analysis_specification_id") if isinstance(analysis.get("analysis_specification_id"), str) else None
        mismatches: list[str] = []
        metrics = [item for item in analysis.get("metric_specifications", []) if isinstance(item, dict)]
        metric_ids = [item.get("metric_id") for item in metrics if isinstance(item.get("metric_id"), str)]
        if len(metric_ids) != len(metrics) or len(metric_ids) != len(set(metric_ids)):
            mismatches.append("metric_id values must be present and unique")
        primary_metric_id = analysis.get("primary_metric_id")
        if sum(1 for metric in metrics if metric.get("metric_id") == primary_metric_id) != 1:
            mismatches.append("primary_metric_id must resolve exactly once")
        analysis_plan = analysis.get("analysis_plan") if isinstance(analysis.get("analysis_plan"), dict) else {}
        epistemic_policy = analysis.get("epistemic_policy") if isinstance(analysis.get("epistemic_policy"), dict) else {}
        if analysis_plan.get("analysis_specification_id") != analysis_id:
            mismatches.append("analysis_plan.analysis_specification_id")
        declared_estimands = set(item for item in analysis.get("estimand_ids", []) if isinstance(item, str))
        declared_outcomes = set(item for item in analysis.get("outcome_definition_ids", []) if isinstance(item, str))
        declared_decision_rules = set(item for item in analysis_plan.get("decision_rule_ids", []) if isinstance(item, str))
        expected_abstention = epistemic_policy.get("abstention_rule_id")
        expected_uncertainty = analysis_plan.get("uncertainty_method_id")
        _, protocol, protocol_mismatches = self.protocol_manifest_context(view, analysis.get("protocol_release_id"))
        protocol_estimands: dict[str, list[dict[str, Any]]] = {}
        if isinstance(protocol, dict) and not protocol_mismatches:
            for estimand in protocol.get("estimands", []):
                if isinstance(estimand, dict) and isinstance(estimand.get("estimand_id"), str):
                    protocol_estimands.setdefault(estimand["estimand_id"], []).append(estimand)
        else:
            mismatches.append(f"exact protocol estimand authority ({protocol_mismatches})")
        for index, metric in enumerate(metrics):
            prefix = f"metric_specifications[{index}]"
            estimand_id = metric.get("estimand_id")
            if estimand_id not in declared_estimands:
                mismatches.append(f"{prefix}.estimand_id membership")
            if metric.get("outcome_definition_id") not in declared_outcomes:
                mismatches.append(f"{prefix}.outcome_definition_id membership")
            if metric.get("target_population") != analysis.get("target_population"):
                mismatches.append(f"{prefix}.target_population")
            if metric.get("comparator") != analysis.get("comparator"):
                mismatches.append(f"{prefix}.comparator")
            if metric.get("decision_rule_id") not in declared_decision_rules:
                mismatches.append(f"{prefix}.decision_rule_id")
            if metric.get("abstention_rule_id") != expected_abstention:
                mismatches.append(f"{prefix}.abstention_rule_id")
            if metric.get("uncertainty_method_id") != expected_uncertainty:
                mismatches.append(f"{prefix}.uncertainty_method_id")
            estimand_matches = protocol_estimands.get(estimand_id, [])
            if len(estimand_matches) != 1:
                mismatches.append(f"{prefix}.unique protocol estimand")
            else:
                if metric.get("metric_class") != estimand_matches[0].get("metric_class"):
                    mismatches.append(f"{prefix}.metric_class")
                if metric.get("direction") != estimand_matches[0].get("direction"):
                    mismatches.append(f"{prefix}.direction")
        if not mismatches:
            return []
        return [
            make_diagnostic(
                "GA-ANALYSIS-SPECIFICATION-INCONSISTENT",
                relative,
                f"Frozen analysis specification is internally inconsistent before result evaluation; mismatches={sorted(set(mismatches))}.",
                analysis_id,
            )
        ]

    def scientific_semantics_diagnostics(self, view: RepositoryView) -> list[dict[str, Any]]:
        paths = self.scientific_instance_paths(view)
        records: list[tuple[str, dict[str, Any]]] = []
        diagnostics: list[dict[str, Any]] = []
        seen_artifacts: dict[str, str] = {}
        seen_primary: dict[tuple[str, str, str], str] = {}
        for relative in paths:
            data = self.read_view_json(view, relative)
            if not isinstance(data, dict):
                diagnostics.append(make_diagnostic("GA-SCHEMA-INSTANCE", relative, "Indexed scientific instance is absent or malformed."))
                continue
            schema_id = data.get("schema_id")
            if schema_id not in SCIENTIFIC_SCHEMA_IDS:
                diagnostics.append(make_diagnostic("GA-SCHEMA-UNKNOWN", relative, "Indexed scientific schema binding does not match instance schema_id.", object_identifier(data)))
                continue
            expected_kind = SCHEMA_OBJECT_KINDS.get(schema_id)
            if expected_kind is not None and data.get("object_kind") != expected_kind:
                diagnostics.append(make_diagnostic("GA-KIND-CONFLATION", relative, f"Schema {schema_id.rsplit('/', 1)[-1]} requires object_kind {expected_kind!r}, not {data.get('object_kind')!r}.", object_identifier(data)))
            records.append((relative, data))
            local_id_surfaces = (
                ("measurements", "measurement_id"),
                ("identification_assumptions", "assumption_id"),
                ("validity_boundaries", "boundary_id"),
            )
            for field, identifier_field in local_id_surfaces:
                items = data.get(field)
                if not isinstance(items, list):
                    continue
                identifiers = [item.get(identifier_field) for item in items if isinstance(item, dict)]
                string_identifiers = [identifier for identifier in identifiers if isinstance(identifier, str)]
                if len(string_identifiers) != len(set(string_identifiers)):
                    diagnostics.append(make_diagnostic("GA-IDENTIFIER-DUPLICATE", relative, f"Local {field} {identifier_field} values are not unique.", object_identifier(data)))
            artifact_id = data.get("artifact_id")
            if isinstance(artifact_id, str):
                if artifact_id in seen_artifacts:
                    diagnostics.append(make_diagnostic("GA-IDENTIFIER-DUPLICATE", relative, f"Duplicate scientific artifact_id {artifact_id}; first seen at {seen_artifacts[artifact_id]}.", artifact_id))
                seen_artifacts[artifact_id] = relative
            primary_id = object_identifier(data)
            version = data.get("version")
            if isinstance(primary_id, str) and isinstance(version, str):
                key = (schema_id, primary_id, version)
                if key in seen_primary:
                    diagnostics.append(make_diagnostic("GA-IDENTIFIER-DUPLICATE", relative, f"Duplicate scientific identity {primary_id}@{version}; first seen at {seen_primary[key]}.", primary_id))
                seen_primary[key] = relative

        protocol_governed_records = list(records)
        governed_paths = {relative for relative, _ in protocol_governed_records}
        for relative in view.iter_files():
            if relative in governed_paths or not relative.endswith(".json"):
                continue
            data = self.read_view_json(view, relative)
            if isinstance(data, dict) and data.get("schema_id") in {
                ANALYSIS_SPECIFICATION_SCHEMA_ID,
                PREREGISTRATION_RECORD_SCHEMA_ID,
            }:
                protocol_governed_records.append((relative, data))
                diagnostics.extend(self.instance_diagnostics(data, relative))
        objects = [(relative, data) for relative, data in records if data.get("schema_id") in OBJECT_SCHEMA_IDS]
        diagnostics.extend(self.semantic_object_chain(objects, require_exact_kind_set=False, view=view))
        diagnostics.extend(self.scientific_lifecycle_diagnostics(records, view))
        experiment_paths = [relative for relative, data in records if data.get("schema_id") in {EXPERIMENT_SCHEMA_ID, RESULT_SCHEMA_ID}]
        diagnostics.extend(self.experiment_result_diagnostics(experiment_paths, view))
        diagnostics.extend(self.claim_register_diagnostics(view))
        for relative, record in protocol_governed_records:
            if record.get("schema_id") == ANALYSIS_SPECIFICATION_SCHEMA_ID:
                diagnostics.extend(self.analysis_specification_diagnostics(view, relative, record))
        diagnostics.extend(self.protocol_definition_diagnostics(view, protocol_governed_records))

        release_ledger = self.read_view_json(view, "manifests/manifest-release-ledger.json")
        artifact_documents = list(protocol_governed_records)
        if isinstance(release_ledger, dict):
            artifact_documents.append(("manifests/manifest-release-ledger.json", release_ledger))
            for entry in release_ledger.get("entries", []):
                binding = entry.get("artifact_binding") if isinstance(entry, dict) else None
                relative = binding.get("path") if isinstance(binding, dict) else None
                if not isinstance(entry, dict) or entry.get("manifest_kind") != "protocol" or not isinstance(relative, str):
                    continue
                protocol_document = self.read_view_json(view, relative)
                if isinstance(protocol_document, dict):
                    artifact_documents.append((relative, protocol_document))
        diagnostics.extend(self.artifact_reference_diagnostics(view, artifact_documents))
        mission_release_ids = {
            entry.get("release_id")
            for entry in release_ledger.get("entries", [])
            if isinstance(release_ledger, dict) and isinstance(entry, dict) and entry.get("manifest_kind") == "mission"
        } if isinstance(release_ledger, dict) else set()
        protocol_release_ids = {
            entry.get("release_id")
            for entry in release_ledger.get("entries", [])
            if isinstance(release_ledger, dict) and isinstance(entry, dict) and entry.get("manifest_kind") == "protocol"
        } if isinstance(release_ledger, dict) else set()
        for relative, data in records:
            schema_id = data.get("schema_id")
            if schema_id in OBJECT_SCHEMA_IDS | {RESULT_SCHEMA_ID} and data.get("protocol_release_id") not in protocol_release_ids:
                diagnostics.append(make_diagnostic("GA-REFERENCE-DANGLING", relative, f"protocol_release_id does not resolve: {data.get('protocol_release_id')}.", object_identifier(data)))
            if schema_id == EXPERIMENT_SCHEMA_ID:
                if data.get("mission_release_id") not in mission_release_ids:
                    diagnostics.append(make_diagnostic("GA-REFERENCE-DANGLING", relative, f"mission_release_id does not resolve: {data.get('mission_release_id')}.", object_identifier(data)))
                if data.get("protocol_release_id") not in protocol_release_ids:
                    diagnostics.append(make_diagnostic("GA-REFERENCE-DANGLING", relative, f"protocol_release_id does not resolve: {data.get('protocol_release_id')}.", object_identifier(data)))

        source_ledger = self.read_view_json(view, ACTIVE_SOURCE_LEDGER_PATH)
        retained_source_ids = {
            record.get("source_id")
            for record in source_ledger.get("records", [])
            if isinstance(source_ledger, dict)
            and isinstance(record, dict)
            and isinstance(record.get("source_id"), str)
        } if isinstance(source_ledger, dict) else set()
        early_evidence_statuses = {"proposed", "exploratory", "preregistered", "running", "blocked"}
        evidentiary_statuses = {"supported", "contradicted", "replicated"}
        objects_by_id: dict[str, list[tuple[str, dict[str, Any]]]] = {}
        objects_by_key: dict[tuple[str, str], list[tuple[str, dict[str, Any]]]] = {}
        for object_path, object_record in objects:
            object_id = object_record.get("object_id")
            object_version = object_record.get("version")
            if isinstance(object_id, str):
                objects_by_id.setdefault(object_id, []).append((object_path, object_record))
                if isinstance(object_version, str):
                    objects_by_key.setdefault((object_id, object_version), []).append((object_path, object_record))

        evidence_policy_cache: dict[str, dict[str, Any] | None] = {}
        evidence_policy_invalid_reported: set[str] = set()

        def evidence_policy_for(release_id: Any) -> dict[str, Any] | None:
            if not isinstance(release_id, str):
                return None
            if release_id in evidence_policy_cache:
                return evidence_policy_cache[release_id]
            _, protocol, protocol_mismatches = self.protocol_manifest_context(view, release_id)
            policy = protocol.get("evidence_binding_policy") if isinstance(protocol, dict) and not protocol_mismatches else None
            required_arrays = (
                "terminal_consumer_statuses",
                "allowed_active_evidence_statuses",
                "support_like_consumer_statuses",
                "universally_disallowed_evidence_statuses",
            )
            canonical_sets = {
                "terminal_consumer_statuses": {"invalid", "null", "inconclusive", "failed", "supported", "contradicted", "replicated", "corrected", "retracted"},
                "allowed_active_evidence_statuses": {"invalid", "inconclusive", "failed", "supported", "contradicted", "replicated", "corrected"},
                "support_like_consumer_statuses": {"supported", "contradicted", "replicated"},
                "universally_disallowed_evidence_statuses": {"proposed", "exploratory", "preregistered", "running", "blocked", "null", "retracted"},
            }
            canonical_witness_rules = [
                {"consumer_status": "invalid", "eligible_evidence_statuses": ["invalid"], "minimum_witnesses": 1},
                {"consumer_status": "null", "eligible_evidence_statuses": ["supported"], "minimum_witnesses": 1},
                {"consumer_status": "inconclusive", "eligible_evidence_statuses": ["inconclusive"], "minimum_witnesses": 1},
                {"consumer_status": "failed", "eligible_evidence_statuses": ["failed"], "minimum_witnesses": 1},
                {"consumer_status": "supported", "eligible_evidence_statuses": ["supported", "replicated"], "minimum_witnesses": 1},
                {"consumer_status": "contradicted", "eligible_evidence_statuses": ["contradicted"], "minimum_witnesses": 1},
                {"consumer_status": "replicated", "eligible_evidence_statuses": ["replicated"], "minimum_witnesses": 1},
            ]
            if (
                not isinstance(policy, dict)
                or policy.get("protocol_release_id") != release_id
                or policy.get("evidence_ref_version_required") is not True
                or policy.get("support_like_requires_valid_evidence") is not True
                or policy.get("witness_status_rules") != canonical_witness_rules
                or policy.get("null_witness_decision_criterion_match_required") is not True
                or policy.get("corrected_evidence_support_like_sole_witness_allowed") is not False
                or policy.get("correction_retraction_events_allow_any_eligible_active_evidence") is not True
                or policy.get("corrected_evidence_requires_current_successor") is not True
                or policy.get("prior_artifact_versions_current_bindable") is not False
                or policy.get("runtime_execution_authorized") is not False
                or any(not isinstance(policy.get(field), list) or not policy.get(field) for field in required_arrays)
                or any(set(policy.get(field, [])) != expected for field, expected in canonical_sets.items())
            ):
                if release_id not in evidence_policy_invalid_reported:
                    diagnostics.append(make_diagnostic("GA-EVIDENCE-POLICY-INCOMPLETE", "manifests/manifest-release-ledger.json", f"Protocol {release_id!r} evidence_binding_policy does not preserve the exact Gate A lifecycle sets and fail-closed invariants.", release_id))
                    evidence_policy_invalid_reported.add(release_id)
                policy = None
            evidence_policy_cache[release_id] = policy
            return policy

        superseded_evidence_keys: set[tuple[str, str]] = set()
        for successor_path, successor in objects:
            if successor.get("object_kind") != "evidence":
                continue
            successor_id = successor.get("object_id")
            for event in successor.get("lifecycle_history", []):
                prior = event.get("prior_artifact") if isinstance(event, dict) else None
                if not isinstance(prior, dict) or prior.get("record_kind") != "evidence" or prior.get("record_id") != successor_id:
                    continue
                prior_id = prior.get("record_id")
                prior_version = prior.get("version")
                prior_path = prior.get("path")
                try:
                    prior_raw = view.read_bytes(prior_path)
                    prior_record = strict_json_loads(prior_raw.decode("utf-8"))
                except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError, StrictJSONError, TypeError):
                    continue
                if (
                    isinstance(prior_id, str)
                    and isinstance(prior_version, str)
                    and prior.get("sha256") == digest_bytes(prior_raw)
                    and isinstance(prior_record, dict)
                    and prior_record.get("object_id") == prior_id
                    and prior_record.get("version") == prior_version
                    and prior_record.get("object_kind") == "evidence"
                    and successor_path != prior_path
                ):
                    superseded_evidence_keys.add((prior_id, prior_version))

        record_targets: dict[tuple[str, str, str], list[tuple[str, dict[str, Any]]]] = {}

        def add_record_target(kind: str, identifier: Any, version: Any, path: str, record: dict[str, Any]) -> None:
            if not isinstance(identifier, str) or not isinstance(version, str):
                return
            record_targets.setdefault((kind, identifier, version), []).append((path, record))

        for record_path, record in records:
            schema_id = record.get("schema_id")
            if schema_id == EXPERIMENT_SCHEMA_ID:
                add_record_target("experiment", record.get("experiment_id"), record.get("version"), record_path, record)
            elif schema_id == RESULT_SCHEMA_ID:
                add_record_target("result", record.get("result_id"), record.get("version"), record_path, record)
                for metric in record.get("metric_results", []):
                    if isinstance(metric, dict):
                        add_record_target("metric", metric.get("metric_id"), record.get("version"), record_path, metric)
            elif schema_id == CLAIM_REGISTER_SCHEMA_ID:
                for item in record.get("items", []):
                    if isinstance(item, dict) and item.get("kind") == "claim":
                        add_record_target("claim", item.get("item_id"), item.get("version"), record_path, item)

        for key, targets in record_targets.items():
            if len(targets) > 1:
                diagnostics.append(make_diagnostic("GA-IDENTIFIER-DUPLICATE", targets[-1][0], f"Duplicate scientific record identity {key[0]}:{key[1]}@{key[2]}.", key[1]))

        def evidence_object_has_retained_basis(record: dict[str, Any]) -> bool:
            basis = record.get("basis")
            if not isinstance(basis, dict) or basis.get("state") != "retained":
                return False
            source_record_ids = basis.get("source_record_ids")
            return (
                isinstance(source_record_ids, list)
                and bool(source_record_ids)
                and all(
                    isinstance(source_id, str) and source_id in retained_source_ids
                    for source_id in source_record_ids
                )
            )

        def validate_evidence_binding(
            owner_path: str,
            owner_id: str | None,
            status: Any,
            binding: Any,
            context: str,
            consumer_ref: tuple[str, str, str] | None,
            consumer_protocol_release_id: str | None,
            required_criterion_ids: Iterable[str] | None = None,
        ) -> None:
            selected_release = consumer_protocol_release_id
            if selected_release is None:
                available_releases = sorted(evidence_policy_cache) or sorted(
                    {
                        target.get("protocol_release_id")
                        for _, target in objects
                        if target.get("object_kind") == "evidence" and isinstance(target.get("protocol_release_id"), str)
                    }
                )
                if len(available_releases) == 1:
                    selected_release = available_releases[0]
            policy = evidence_policy_for(selected_release)
            if not isinstance(policy, dict):
                diagnostics.append(
                    make_diagnostic(
                        "GA-EVIDENCE-BINDING-INELIGIBLE",
                        owner_path,
                        f"{context} cannot resolve an exact governing protocol evidence-binding policy for {selected_release!r}.",
                        owner_id,
                    )
                )
                return
            terminal_statuses = set(policy["terminal_consumer_statuses"])
            active_evidence_statuses = set(policy["allowed_active_evidence_statuses"])
            support_like_statuses = set(policy["support_like_consumer_statuses"])
            universally_disallowed = set(policy["universally_disallowed_evidence_statuses"])
            witness_rule = next(
                (
                    rule
                    for rule in policy.get("witness_status_rules", [])
                    if isinstance(rule, dict) and rule.get("consumer_status") == status
                ),
                None,
            )
            witness_statuses = set(witness_rule.get("eligible_evidence_statuses", [])) if isinstance(witness_rule, dict) else set()
            minimum_witnesses = witness_rule.get("minimum_witnesses", 0) if isinstance(witness_rule, dict) else 0
            eligible_witness_count = 0
            binding_state = binding.get("state") if isinstance(binding, dict) else None
            if status in terminal_statuses and binding_state != "retained":
                diagnostics.append(
                    make_diagnostic(
                        "GA-EVIDENCE-BINDING-INELIGIBLE",
                        owner_path,
                        f"{context} lifecycle {status!r} requires a retained eligible evidence binding, not {binding_state!r}.",
                        owner_id,
                    )
                )
            if binding_state == "evidence_gap":
                return
            if binding_state != "retained":
                diagnostics.append(
                    make_diagnostic(
                        "GA-EVIDENCE-BINDING-INELIGIBLE",
                        owner_path,
                        f"{context} evidence binding state is unknown or absent: {binding_state!r}.",
                        owner_id,
                    )
                )
                return
            evidence_refs = binding.get("evidence_refs") if isinstance(binding, dict) else None
            if not isinstance(evidence_refs, list) or not evidence_refs:
                diagnostics.append(
                    make_diagnostic(
                        "GA-EVIDENCE-BINDING-INELIGIBLE",
                        owner_path,
                        f"{context} retained evidence binding must contain at least one versioned evidence reference.",
                        owner_id,
                    )
                )
                return
            for evidence_ref in evidence_refs:
                evidence_id = evidence_ref.get("evidence_id") if isinstance(evidence_ref, dict) else None
                evidence_version = evidence_ref.get("version") if isinstance(evidence_ref, dict) else None
                targets = objects_by_key.get((evidence_id, evidence_version), []) if isinstance(evidence_id, str) and isinstance(evidence_version, str) else []
                if not targets:
                    available_versions = sorted(
                        target.get("version")
                        for _, target in objects_by_id.get(evidence_id, [])
                        if isinstance(target.get("version"), str)
                    ) if isinstance(evidence_id, str) else []
                    diagnostics.append(
                        make_diagnostic(
                            "GA-REFERENCE-DANGLING",
                            owner_path,
                            f"{context} evidence reference does not resolve exactly: {evidence_id!r}@{evidence_version!r}; available_versions={available_versions}.",
                            owner_id,
                        )
                    )
                    continue
                if len(targets) != 1:
                    diagnostics.append(
                        make_diagnostic(
                            "GA-EVIDENCE-BINDING-INELIGIBLE",
                            owner_path,
                            f"{context} evidence reference {evidence_id!r}@{evidence_version!r} resolves ambiguously to {len(targets)} objects.",
                            owner_id,
                        )
                    )
                    continue
                target_path, target = targets[0]
                if target.get("object_kind") != "evidence":
                    diagnostics.append(
                        make_diagnostic(
                            "GA-REFERENCE-WRONG-KIND",
                            owner_path,
                            f"{context} evidence_id {evidence_id!r} resolves to {target.get('object_kind')!r}, not 'evidence' ({target_path}).",
                            owner_id,
                        )
                    )
                elif not evidence_object_has_retained_basis(target):
                    diagnostics.append(
                        make_diagnostic(
                            "GA-EVIDENCE-BINDING-INELIGIBLE",
                            owner_path,
                            f"{context} evidence_id {evidence_id!r} does not have a retained, source-ledger-resolved evidence basis.",
                            owner_id,
                        )
                    )
                else:
                    evidence_status = target.get("lifecycle_status")
                    eligible_for_witness = True
                    if target.get("protocol_release_id") != selected_release:
                        eligible_for_witness = False
                        diagnostics.append(
                            make_diagnostic(
                                "GA-EVIDENCE-BINDING-INELIGIBLE",
                                owner_path,
                                f"{context} evidence {evidence_id!r}@{evidence_version!r} is governed by a different protocol release.",
                                owner_id,
                            )
                        )
                    if (evidence_id, evidence_version) in superseded_evidence_keys:
                        eligible_for_witness = False
                        diagnostics.append(
                            make_diagnostic(
                                "GA-EVIDENCE-BINDING-INELIGIBLE",
                                owner_path,
                                f"{context} evidence {evidence_id!r}@{evidence_version!r} is a superseded or withdrawn predecessor version.",
                                owner_id,
                            )
                        )
                    if evidence_status in universally_disallowed:
                        eligible_for_witness = False
                        diagnostics.append(
                            make_diagnostic(
                                "GA-EVIDENCE-BINDING-INELIGIBLE",
                                owner_path,
                                f"{context} evidence {evidence_id!r}@{evidence_version!r} has universally non-bindable lifecycle {evidence_status!r}.",
                                owner_id,
                            )
                        )
                    elif status in terminal_statuses and evidence_status not in active_evidence_statuses:
                        eligible_for_witness = False
                        diagnostics.append(
                            make_diagnostic(
                                "GA-EVIDENCE-BINDING-INELIGIBLE",
                                owner_path,
                                f"{context} terminal lifecycle {status!r} cites evidence with non-active lifecycle {evidence_status!r}.",
                                owner_id,
                            )
                        )
                    if consumer_ref is not None:
                        target_kind, target_id, target_version = consumer_ref
                        if target_kind in EXPECTED_KINDS:
                            reciprocal = {
                                "object_id": target_id,
                                "object_kind": target_kind,
                                "version": target_version,
                            }
                            target_refs = target.get("target_object_refs")
                        else:
                            reciprocal = {
                                "target_kind": target_kind,
                                "target_id": target_id,
                                "version": target_version,
                            }
                            target_refs = target.get("target_record_refs")
                        if not isinstance(target_refs, list) or reciprocal not in target_refs:
                            eligible_for_witness = False
                            diagnostics.append(
                                make_diagnostic(
                                    "GA-EVIDENCE-BINDING-INELIGIBLE",
                                    owner_path,
                                    f"{context} evidence_id {evidence_id!r} lacks reciprocal exact target reference {target_kind}:{target_id}@{target_version}.",
                                    owner_id,
                                )
                            )
                    if status in support_like_statuses:
                        validity = target.get("validity")
                        if policy.get("support_like_requires_valid_evidence") is not True or not isinstance(validity, dict) or validity.get("state") != "valid":
                            eligible_for_witness = False
                        if required_criterion_ids is not None:
                            required_criteria = {criterion for criterion in required_criterion_ids if isinstance(criterion, str)}
                            observed_criteria = set(target.get("criterion_ids", [])) if isinstance(target.get("criterion_ids"), list) else set()
                            if not required_criteria or not required_criteria <= observed_criteria:
                                eligible_for_witness = False
                    if status == "null" and policy.get("null_witness_decision_criterion_match_required") is True:
                        required_criteria = {criterion for criterion in (required_criterion_ids or []) if isinstance(criterion, str)}
                        observed_criteria = set(target.get("criterion_ids", [])) if isinstance(target.get("criterion_ids"), list) else set()
                        if not required_criteria or not required_criteria <= observed_criteria:
                            eligible_for_witness = False
                    if evidence_status not in witness_statuses:
                        eligible_for_witness = False
                    if eligible_for_witness:
                        eligible_witness_count += 1
            if isinstance(minimum_witnesses, int) and minimum_witnesses > 0 and eligible_witness_count < minimum_witnesses:
                diagnostics.append(
                    make_diagnostic(
                        "GA-EVIDENCE-WITNESS-MISSING",
                        owner_path,
                        f"{context} lifecycle {status!r} requires at least {minimum_witnesses} eligible evidence witness(es) with lifecycle in {sorted(witness_statuses)}; observed={eligible_witness_count}.",
                        owner_id,
                    )
                )

        for relative, data in objects:
            if data.get("object_kind") == "evidence":
                evidence_id = data.get("object_id") if isinstance(data.get("object_id"), str) else None
                for target_ref in data.get("target_object_refs", []):
                    if not isinstance(target_ref, dict):
                        continue
                    target_id = target_ref.get("object_id")
                    target_version = target_ref.get("version")
                    target_kind = target_ref.get("object_kind")
                    targets = objects_by_key.get((target_id, target_version), []) if isinstance(target_id, str) and isinstance(target_version, str) else []
                    exact = [candidate for candidate in targets if candidate[1].get("object_kind") == target_kind]
                    if len(exact) == 1:
                        continue
                    if targets and not exact:
                        diagnostics.append(make_diagnostic("GA-REFERENCE-WRONG-KIND", relative, f"Evidence target object {target_id!r}@{target_version!r} resolves only as kinds {sorted({candidate[1].get('object_kind') for candidate in targets})}, not {target_kind!r}.", evidence_id))
                    else:
                        diagnostics.append(make_diagnostic("GA-REFERENCE-DANGLING", relative, f"Evidence target object does not resolve exactly once: {target_kind}:{target_id}@{target_version}; matches={len(exact)}.", evidence_id))
                for target_ref in data.get("target_record_refs", []):
                    if not isinstance(target_ref, dict):
                        continue
                    target_kind = target_ref.get("target_kind")
                    target_id = target_ref.get("target_id")
                    target_version = target_ref.get("version")
                    key = (target_kind, target_id, target_version)
                    targets = record_targets.get(key, []) if all(isinstance(value, str) for value in key) else []
                    if len(targets) == 1:
                        continue
                    same_id = [candidate for candidate in record_targets if candidate[1] == target_id]
                    if same_id and all(candidate[0] != target_kind for candidate in same_id):
                        diagnostics.append(make_diagnostic("GA-REFERENCE-WRONG-KIND", relative, f"Evidence target record {target_id!r} resolves only as kinds {sorted({candidate[0] for candidate in same_id})}, not {target_kind!r}.", evidence_id))
                    else:
                        diagnostics.append(make_diagnostic("GA-REFERENCE-DANGLING", relative, f"Evidence target record does not resolve exactly once: {target_kind}:{target_id}@{target_version}; matches={len(targets)}.", evidence_id))
                status = data.get("lifecycle_status")
                basis = data.get("basis")
                basis_state = basis.get("state") if isinstance(basis, dict) else None
                if status not in early_evidence_statuses and basis_state != "retained":
                    diagnostics.append(
                        make_diagnostic(
                            "GA-EVIDENCE-BASIS-INELIGIBLE",
                            relative,
                            f"Evidence lifecycle {status!r} requires a retained basis, not {basis_state!r}.",
                            evidence_id,
                        )
                    )
                if basis_state == "retained":
                    referenced_source_ids = basis.get("source_record_ids", []) if isinstance(basis, dict) else []
                    unresolved = sorted(
                        repr(source_id)
                        for source_id in referenced_source_ids
                        if not isinstance(source_id, str) or source_id not in retained_source_ids
                    ) if isinstance(referenced_source_ids, list) else [repr(referenced_source_ids)]
                    if not isinstance(referenced_source_ids, list) or not referenced_source_ids or unresolved:
                        diagnostics.append(
                            make_diagnostic(
                                "GA-EVIDENCE-BASIS-INELIGIBLE",
                                relative,
                                "Retained evidence basis must reference one or more exact source_id values from the source ledger; "
                                f"unresolved={unresolved}.",
                                evidence_id,
                            )
                        )
                elif basis_state != "evidence_gap":
                    diagnostics.append(
                        make_diagnostic(
                            "GA-EVIDENCE-BASIS-INELIGIBLE",
                            relative,
                            f"Evidence basis state is unknown or absent: {basis_state!r}.",
                            evidence_id,
                        )
                    )
                validity = data.get("validity")
                if status in evidentiary_statuses and (
                    not isinstance(validity, dict) or validity.get("state") != "valid"
                ):
                    diagnostics.append(
                        make_diagnostic(
                            "GA-EVIDENCE-BASIS-INELIGIBLE",
                            relative,
                            f"Evidence lifecycle {status!r} requires validity.state 'valid'.",
                            evidence_id,
                        )
                    )
        for relative, record in records:
            schema_id = record.get("schema_id")
            if schema_id == EXPERIMENT_SCHEMA_ID:
                experiment_id = record.get("experiment_id") if isinstance(record.get("experiment_id"), str) else None
                experiment_version = record.get("version") if isinstance(record.get("version"), str) else None
                validate_evidence_binding(
                    relative,
                    experiment_id,
                    record.get("lifecycle_status"),
                    record.get("evidence_binding"),
                    "Experiment",
                    ("experiment", experiment_id, experiment_version) if experiment_id and experiment_version else None,
                    record.get("protocol_release_id") if isinstance(record.get("protocol_release_id"), str) else None,
                    record.get("analysis_plan", {}).get("decision_rule_ids", []) if isinstance(record.get("analysis_plan"), dict) else [],
                )
            elif schema_id == RESULT_SCHEMA_ID:
                result_id = record.get("result_id") if isinstance(record.get("result_id"), str) else None
                result_version = record.get("version") if isinstance(record.get("version"), str) else None
                result_ref = ("result", result_id, result_version) if result_id and result_version else None
                result_binding = record.get("evidence_binding")
                primary_metrics = [
                    metric
                    for metric in record.get("metric_results", [])
                    if isinstance(metric, dict) and metric.get("metric_id") == record.get("primary_metric_id")
                ]
                result_required_criteria = [primary_metrics[0].get("decision_rule_id")] if len(primary_metrics) == 1 else []
                validate_evidence_binding(
                    relative,
                    result_id,
                    record.get("lifecycle_status"),
                    result_binding,
                    "Result",
                    result_ref,
                    record.get("protocol_release_id") if isinstance(record.get("protocol_release_id"), str) else None,
                    result_required_criteria,
                )
                for metric_index, metric in enumerate(record.get("metric_results", [])):
                    if not isinstance(metric, dict):
                        continue
                    metric_id = metric.get("metric_id") if isinstance(metric.get("metric_id"), str) else result_id
                    metric_binding = metric.get("evidence_binding", result_binding)
                    validate_evidence_binding(
                        relative,
                        metric_id,
                        metric.get("interpretation_status"),
                        metric_binding,
                        f"Result metric {metric_index}",
                        ("metric", metric_id, result_version) if metric_id and result_version else None,
                        record.get("protocol_release_id") if isinstance(record.get("protocol_release_id"), str) else None,
                        [metric.get("decision_rule_id")],
                    )
        for relative, record in records:
            schema_id = record.get("schema_id")
            record_kind = SCHEMA_OBJECT_KINDS.get(schema_id)
            record_id = record.get("object_id") if record_kind is not None else None
            if schema_id == EXPERIMENT_SCHEMA_ID:
                record_kind = "experiment"
                record_id = record.get("experiment_id")
            elif schema_id == RESULT_SCHEMA_ID:
                record_kind = "result"
                record_id = record.get("result_id")
            if not isinstance(record_kind, str) or not isinstance(record_id, str) or not isinstance(record.get("version"), str):
                continue
            consumer_ref = (record_kind, record_id, record["version"])
            if schema_id == RESULT_SCHEMA_ID:
                primary_metrics = [
                    metric
                    for metric in record.get("metric_results", [])
                    if isinstance(metric, dict) and metric.get("metric_id") == record.get("primary_metric_id")
                ]
                history_required_criteria = [primary_metrics[0].get("decision_rule_id")] if len(primary_metrics) == 1 else []
            elif schema_id == EXPERIMENT_SCHEMA_ID:
                history_required_criteria = record.get("analysis_plan", {}).get("decision_rule_ids", []) if isinstance(record.get("analysis_plan"), dict) else []
            elif record_kind == "evidence":
                history_required_criteria = record.get("criterion_ids", []) if isinstance(record.get("criterion_ids"), list) else []
            else:
                history_required_criteria = None
            for history_index, event in enumerate(record.get("lifecycle_history", [])):
                if not isinstance(event, dict):
                    continue
                history_refs = event.get("evidence_refs")
                history_binding = {
                    "state": "retained" if isinstance(history_refs, list) and bool(history_refs) else "evidence_gap",
                    "evidence_refs": history_refs if isinstance(history_refs, list) else [],
                }
                validate_evidence_binding(
                    relative,
                    record_id,
                    event.get("status"),
                    history_binding,
                    f"{record_kind} lifecycle_history event {history_index}",
                    consumer_ref,
                    record.get("protocol_release_id") if isinstance(record.get("protocol_release_id"), str) else None,
                    history_required_criteria,
                )
        evidence_citation_graph: dict[tuple[str, str], set[tuple[str, str]]] = {}
        evidence_paths_by_key: dict[tuple[str, str], str] = {}
        for relative, record in objects:
            if record.get("object_kind") != "evidence" or not isinstance(record.get("object_id"), str) or not isinstance(record.get("version"), str):
                continue
            owner_key = (record["object_id"], record["version"])
            evidence_paths_by_key[owner_key] = relative
            for event in record.get("lifecycle_history", []):
                if not isinstance(event, dict):
                    continue
                for evidence_ref in event.get("evidence_refs", []):
                    if isinstance(evidence_ref, dict) and isinstance(evidence_ref.get("evidence_id"), str) and isinstance(evidence_ref.get("version"), str):
                        evidence_citation_graph.setdefault(owner_key, set()).add((evidence_ref["evidence_id"], evidence_ref["version"]))
        evidence_visiting: set[tuple[str, str]] = set()
        evidence_visited: set[tuple[str, str]] = set()

        def visit_evidence(node: tuple[str, str], trail: list[tuple[str, str]]) -> None:
            if node in evidence_visiting:
                cycle_start = trail.index(node) if node in trail else 0
                cycle = trail[cycle_start:] + [node]
                diagnostics.append(make_diagnostic("GA-REFERENCE-CYCLE", evidence_paths_by_key.get(node, "manifests/examples/object-chain"), f"Evidence lifecycle citation graph contains a cycle: {' -> '.join(f'{item[0]}@{item[1]}' for item in cycle)}.", node[0]))
                return
            if node in evidence_visited:
                return
            evidence_visiting.add(node)
            for target in sorted(evidence_citation_graph.get(node, set())):
                if target in evidence_paths_by_key:
                    visit_evidence(target, trail + [node])
            evidence_visiting.discard(node)
            evidence_visited.add(node)

        for node in sorted(evidence_paths_by_key):
            visit_evidence(node, [])
        for relative, register in records:
            if register.get("schema_id") != CLAIM_REGISTER_SCHEMA_ID:
                continue
            for item in register.get("items", []):
                if not isinstance(item, dict) or item.get("kind") != "claim":
                    continue
                validate_evidence_binding(
                    relative,
                    item.get("item_id") if isinstance(item.get("item_id"), str) else None,
                    item.get("lifecycle_status"),
                    item.get("evidence_binding"),
                    "Claim",
                    ("claim", item["item_id"], item["version"])
                    if isinstance(item.get("item_id"), str) and isinstance(item.get("version"), str)
                    else None,
                    None,
                    [item.get("decision_rule_id")],
                )
        return sorted(diagnostics, key=diagnostic_key)

    def check_global_scientific_semantics(self) -> None:
        self.diagnostics.extend(self.scientific_semantics_diagnostics(self.view))

    @staticmethod
    def history_time_diagnostics(history: Any, path: str, object_id: str | None = None) -> list[dict[str, Any]]:
        if not isinstance(history, list):
            return []
        diagnostics: list[dict[str, Any]] = []
        prior: datetime | None = None
        for index, event in enumerate(history):
            recorded_at = event.get("recorded_at") if isinstance(event, dict) else None
            current = parse_exact_utc(recorded_at)
            if current is None:
                diagnostics.append(make_diagnostic("GA-STATUS-HISTORY-TIME", path, f"Status history event {index} recorded_at must be an exact valid UTC timestamp ending in Z.", object_id))
            elif prior is not None and current <= prior:
                diagnostics.append(make_diagnostic("GA-STATUS-HISTORY-TIME", path, f"Status history event {index} must be strictly later than its predecessor.", object_id))
            if current is not None:
                prior = current
        return diagnostics

    def status_diagnostics(
        self,
        payload: dict[str, Any],
        path: str,
        object_id: str | None = None,
        *,
        view: RepositoryView | None = None,
        record_kind: str | None = None,
        protocol_release_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Validate lifecycle vocabulary/transitions from the exact governing protocol."""

        history = payload.get("status_history", [])
        unknown = [status for status in history if status not in EXPECTED_LIFECYCLE_STATUSES]
        if unknown:
            return [make_diagnostic("GA-STATUS-UNKNOWN", path, f"Unknown lifecycle status {unknown[0]!r}.", object_id)]
        selected_view = view or self.view
        selected_kind = record_kind or "experiment"
        if not isinstance(protocol_release_id, str):
            return [
                make_diagnostic(
                    "GA-STATUS-ILLEGAL-TRANSITION",
                    path,
                    "Lifecycle transition authority requires an explicit protocol_release_id; no historical default is inferred.",
                    object_id,
                )
            ]
        selected_release = protocol_release_id
        protocol_path, protocol, protocol_mismatches = self.protocol_manifest_context(selected_view, selected_release)
        if not isinstance(protocol, dict) or protocol_mismatches:
            return [
                make_diagnostic(
                    "GA-STATUS-ILLEGAL-TRANSITION",
                    path,
                    f"Lifecycle transition authority cannot resolve exact protocol {selected_release!r}; mismatches={protocol_mismatches}.",
                    object_id,
                )
            ]
        policy = protocol.get("lifecycle_transition_policy")
        policy_mismatches: list[str] = []
        if not isinstance(policy, dict):
            policy_mismatches.append("policy object")
        else:
            if policy.get("protocol_release_id") != selected_release:
                policy_mismatches.append("protocol_release_id")
            if policy.get("history_policy") != "append_only_immutable_successor":
                policy_mismatches.append("history_policy")
            if policy.get("runtime_execution_authorized") is not False:
                policy_mismatches.append("runtime_execution_authorized")
        scopes = [
            scope
            for scope in policy.get("entity_scopes", [])
            if isinstance(policy, dict) and isinstance(scope, dict) and scope.get("record_kind") == selected_kind
        ] if isinstance(policy, dict) else []
        if len(scopes) != 1:
            policy_mismatches.append(f"entity scope matches={len(scopes)}")
            allowed_statuses: set[str] = set()
        else:
            allowed_values = scopes[0].get("allowed_statuses")
            allowed_statuses = {status for status in allowed_values if isinstance(status, str)} if isinstance(allowed_values, list) else set()
            if not allowed_statuses:
                policy_mismatches.append("allowed statuses")
        transitions = policy.get("transitions") if isinstance(policy, dict) else None
        explicit: set[tuple[str, str]] = set()
        if isinstance(transitions, list):
            for transition in transitions:
                if not isinstance(transition, dict) or selected_kind not in transition.get("entity_kinds", []):
                    continue
                prior = transition.get("from_status")
                current = transition.get("to_status")
                if isinstance(prior, str) and isinstance(current, str) and transition.get("requires_immutable_successor") is True:
                    explicit.add((prior, current))
        else:
            policy_mismatches.append("transition table")
        correction_rule = policy.get("correction_retraction_rule") if isinstance(policy, dict) else None
        correction_pairs: set[tuple[str, str]] = set()
        if isinstance(correction_rule, dict) and selected_kind in correction_rule.get("entity_kinds", []):
            eligible = correction_rule.get("eligible_prior_statuses")
            corrected = correction_rule.get("correction_status")
            retracted = correction_rule.get("retraction_status")
            if isinstance(eligible, list) and isinstance(corrected, str) and isinstance(retracted, str):
                correction_pairs = {
                    (prior, successor)
                    for prior in eligible
                    if isinstance(prior, str)
                    for successor in (corrected, retracted)
                }
            if correction_rule.get("retracted_is_terminal") is not True:
                policy_mismatches.append("retracted terminal rule")
        else:
            policy_mismatches.append("correction/retraction scope")
        if policy_mismatches:
            return [
                make_diagnostic(
                    "GA-STATUS-ILLEGAL-TRANSITION",
                    protocol_path or path,
                    f"Governing lifecycle transition policy is incomplete or inconsistent; mismatches={sorted(set(policy_mismatches))}.",
                    object_id,
                )
            ]
        if history and history[0] != policy.get("initial_status"):
            return [make_diagnostic("GA-STATUS-ILLEGAL-TRANSITION", path, f"Initial lifecycle status must equal protocol initial_status {policy.get('initial_status')!r}.", object_id)]
        unauthorized = [status for status in history if status not in allowed_statuses]
        if unauthorized:
            return [make_diagnostic("GA-STATUS-ILLEGAL-TRANSITION", path, f"Lifecycle status {unauthorized[0]!r} is not permitted for protocol entity kind {selected_kind!r}.", object_id)]
        for prior, current in zip(history, history[1:]):
            if (prior, current) not in explicit | correction_pairs:
                return [make_diagnostic("GA-STATUS-ILLEGAL-TRANSITION", path, f"Illegal lifecycle transition {prior!r} -> {current!r}.", object_id)]
        return []

    def recursive_measurement_diagnostics(self, data: Any, relative: str) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []

        def visit(value: Any, parts: list[Any]) -> None:
            if isinstance(value, dict):
                state = value.get("state")
                if state in EXPECTED_EPISTEMIC_STATES:
                    if state == "observed":
                        observed_worst_group = (
                            bool(parts)
                            and parts[-1] == "worst_group_disposition"
                            and isinstance(value.get("group_ids"), list)
                            and bool(value["group_ids"])
                            and isinstance(value.get("selection_rule_id"), str)
                        )
                        if "value" not in value and "components" not in value and not observed_worst_group:
                            diagnostics.append(make_diagnostic("GA-EPISTEMIC-OBSERVED-INCOMPLETE", relative, f"{json_pointer(parts)}: observed state lacks a value."))
                    elif "value" in value or "reason" not in value:
                        diagnostics.append(make_diagnostic(EPISTEMIC_RULES[state], relative, f"{json_pointer(parts)}: non-observed state carries a value or lacks a reason."))
                    if state in {"out_of_distribution", "sensor_invalid", "abstained"} and not isinstance(value.get("rule_id"), str):
                        diagnostics.append(make_diagnostic("GA-EPISTEMIC-RULE-MISSING", relative, f"{json_pointer(parts)}: {state} requires an explicit rule_id."))
                for key, child in value.items():
                    visit(child, parts + [key])
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    visit(child, parts + [index])

        visit(data, [])
        return diagnostics

    def normative_measurement_diagnostics(self, view: RepositoryView) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        for relative in self.scientific_instance_paths(view):
            data = self.read_view_json(view, relative)
            if data is not None:
                diagnostics.extend(self.recursive_measurement_diagnostics(data, relative))
        return sorted(diagnostics, key=diagnostic_key)

    def check_normative_measurements(self) -> None:
        self.diagnostics.extend(self.normative_measurement_diagnostics(self.view))

    def experiment_result_diagnostics(
        self,
        paths: list[str],
        view: RepositoryView | None = None,
    ) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        selected_view = view or self.view
        experiments: dict[tuple[str, str], tuple[str, dict[str, Any]]] = {}
        results: list[tuple[str, dict[str, Any]]] = []
        release_ledger = self.read_view_json(selected_view, "manifests/manifest-release-ledger.json")
        protocol_manifests: dict[str, dict[str, Any]] = {}
        if isinstance(release_ledger, dict):
            for entry in release_ledger.get("entries", []):
                binding = entry.get("artifact_binding") if isinstance(entry, dict) else None
                if not isinstance(entry, dict) or entry.get("manifest_kind") != "protocol" or not isinstance(binding, dict):
                    continue
                manifest = self.read_view_json(selected_view, binding.get("path")) if isinstance(binding.get("path"), str) else None
                if isinstance(entry.get("release_id"), str) and isinstance(manifest, dict):
                    protocol_manifests[entry["release_id"]] = manifest
        analysis_specifications: dict[tuple[str, str], list[tuple[str, dict[str, Any]]]] = {}
        preregistration_eligible: dict[str, bool] = {}
        for candidate_path in selected_view.iter_files():
            if not candidate_path.endswith(".json"):
                continue
            candidate = self.read_view_json(selected_view, candidate_path)
            if not isinstance(candidate, dict) or candidate.get("schema_id") != ANALYSIS_SPECIFICATION_SCHEMA_ID:
                continue
            protocol_release_id = candidate.get("protocol_release_id")
            analysis_specification_id = candidate.get("analysis_specification_id")
            if isinstance(protocol_release_id, str) and isinstance(analysis_specification_id, str):
                analysis_specifications.setdefault((protocol_release_id, analysis_specification_id), []).append((candidate_path, candidate))
        for relative in paths:
            data = self.read_view_json(view, relative) if view is not None else self.read_json_contract(relative)
            if not isinstance(data, dict):
                diagnostics.append(make_diagnostic("GA-REQUIRED-ARTIFACT-MISSING", relative, "Fixture schema instance is missing or malformed."))
                continue
            if view is None or view is not self.view:
                diagnostics.extend(self.instance_diagnostics(data, relative))
            if data.get("schema_id", "").endswith("/experiment.schema.json"):
                preregistration_diagnostics = self.preregistration_diagnostics(selected_view, relative, data)
                diagnostics.extend(preregistration_diagnostics)
                preregistration = data.get("preregistration")
                preregistration_eligible[relative] = (
                    not preregistration_diagnostics
                    and isinstance(preregistration, dict)
                    and preregistration.get("status") == "preregistered"
                    and isinstance(preregistration.get("retained_artifact"), dict)
                )
                experiment_id = data.get("experiment_id")
                experiment_version = data.get("version")
                experiment_key = (experiment_id, experiment_version)
                if experiment_key in experiments:
                    diagnostics.append(make_diagnostic("GA-IDENTIFIER-DUPLICATE", relative, f"Duplicate experiment identity {experiment_id}@{experiment_version}.", experiment_id))
                if isinstance(experiment_id, str) and isinstance(experiment_version, str):
                    experiments[(experiment_id, experiment_version)] = (relative, data)
                protocol = protocol_manifests.get(data.get("protocol_release_id"))
                if not isinstance(protocol, dict) or protocol.get("mission_release_id") != data.get("mission_release_id"):
                    diagnostics.append(make_diagnostic("GA-CONTEXT-MISMATCH", relative, "Experiment mission_release_id does not equal the exact protocol release mission binding.", experiment_id if isinstance(experiment_id, str) else None))
                raw_history = data.get("lifecycle_history", data.get("status_history"))
                status_history = [event.get("status") if isinstance(event, dict) else None for event in raw_history] if isinstance(raw_history, list) else []
                if not status_history:
                    diagnostics.append(make_diagnostic("GA-STATUS-HISTORY-CURRENT", relative, "Experiment status_history must be present and nonempty.", data.get("experiment_id")))
                diagnostics.extend(
                    self.status_diagnostics(
                        {"status_history": status_history},
                        relative,
                        data.get("experiment_id"),
                        view=selected_view,
                        record_kind="experiment",
                        protocol_release_id=data.get("protocol_release_id") if isinstance(data.get("protocol_release_id"), str) else None,
                    )
                )
                diagnostics.extend(self.history_time_diagnostics(raw_history, relative, data.get("experiment_id")))
                if status_history and status_history[-1] != data.get("lifecycle_status"):
                    diagnostics.append(make_diagnostic("GA-STATUS-HISTORY-CURRENT", relative, "Experiment current lifecycle status does not equal the final history event.", data.get("experiment_id")))
                preregistration = data.get("preregistration")
                preregistration_status = preregistration.get("status") if isinstance(preregistration, dict) else None
                preregistration_history = [status for status in status_history if status in {"proposed", "exploratory", "preregistered"}]
                expected_preregistration_status = preregistration_history[-1] if preregistration_history else None
                if preregistration_status != expected_preregistration_status:
                    diagnostics.append(make_diagnostic("GA-STATUS-HISTORY-CURRENT", relative, f"Experiment preregistration status {preregistration_status!r} does not match its latest history state {expected_preregistration_status!r}.", data.get("experiment_id")))
                boundaries = data.get("validity_boundaries")
                boundary_ids = [item.get("boundary_id") for item in boundaries if isinstance(item, dict)] if isinstance(boundaries, list) else []
                boundary_dimensions = [item.get("dimension") for item in boundaries if isinstance(item, dict)] if isinstance(boundaries, list) else []
                required_dimensions = {"population", "object", "time", "sensor", "reference", "support", "protocol"}
                if (
                    not isinstance(boundaries, list)
                    or len(boundary_ids) != len(set(boundary_ids))
                    or len(boundary_dimensions) != len(set(boundary_dimensions))
                    or set(boundary_dimensions) != required_dimensions
                ):
                    diagnostics.append(make_diagnostic("GA-VALIDITY-BOUNDARY-INCOMPLETE", relative, f"Experiment validity boundaries must have unique IDs and exactly one of each required dimension; observed={sorted(set(boundary_dimensions))}.", data.get("experiment_id")))
                if data.get("runtime_execution_authorized") is not False:
                    diagnostics.append(make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", relative, "Experiment fixture authorizes runtime execution.", data.get("experiment_id")))
            elif data.get("schema_id", "").endswith("/result.schema.json"):
                results.append((relative, data))
                raw_history = data.get("lifecycle_history", data.get("status_history"))
                status_history = [event.get("status") if isinstance(event, dict) else None for event in raw_history] if isinstance(raw_history, list) else []
                if not status_history:
                    diagnostics.append(make_diagnostic("GA-STATUS-HISTORY-CURRENT", relative, "Result status_history must be present and nonempty.", data.get("result_id")))
                diagnostics.extend(
                    self.status_diagnostics(
                        {"status_history": status_history},
                        relative,
                        data.get("result_id"),
                        view=selected_view,
                        record_kind="result",
                        protocol_release_id=data.get("protocol_release_id") if isinstance(data.get("protocol_release_id"), str) else None,
                    )
                )
                diagnostics.extend(self.history_time_diagnostics(raw_history, relative, data.get("result_id")))
                if status_history and status_history[-1] != data.get("lifecycle_status"):
                    diagnostics.append(make_diagnostic("GA-STATUS-HISTORY-CURRENT", relative, "Result current lifecycle status does not equal the final history event.", data.get("result_id")))
        experiment_head_paths: dict[str, set[str]] = {}
        for experiment_id in {key[0] for key in experiments if isinstance(key[0], str)}:
            group = [(path, record) for (candidate_id, _), (path, record) in experiments.items() if candidate_id == experiment_id]
            predecessor_paths = {
                prior.get("path")
                for _, record in group
                for event in record.get("lifecycle_history", [])
                if isinstance(event, dict)
                for prior in [event.get("prior_artifact")]
                if isinstance(prior, dict) and isinstance(prior.get("path"), str)
            }
            experiment_head_paths[experiment_id] = {path for path, _ in group if path not in predecessor_paths}
        result_head_paths: dict[str, set[str]] = {}
        for candidate_id in {record.get("result_id") for _, record in results if isinstance(record.get("result_id"), str)}:
            group = [(path, record) for path, record in results if record.get("result_id") == candidate_id]
            predecessor_paths = {
                prior.get("path")
                for _, record in group
                for event in record.get("lifecycle_history", [])
                if isinstance(event, dict)
                for prior in [event.get("prior_artifact")]
                if isinstance(prior, dict) and isinstance(prior.get("path"), str)
            }
            result_head_paths[candidate_id] = {path for path, _ in group if path not in predecessor_paths}
        result_keys: set[tuple[Any, Any]] = set()
        for relative, result in results:
            result_key = (result.get("result_id"), result.get("version"))
            if result_key in result_keys:
                diagnostics.append(make_diagnostic("GA-IDENTIFIER-DUPLICATE", relative, f"Duplicate result identity {result_key[0]}@{result_key[1]}.", result.get("result_id")))
            result_keys.add(result_key)
            result_id = result.get("result_id")
            lifecycle_status = result.get("lifecycle_status")
            replication = result.get("replicates_result")
            replication_lineage_valid = False
            if lifecycle_status != "replicated" and replication is not None:
                diagnostics.append(make_diagnostic("GA-RESULT-LINEAGE", relative, f"Result lifecycle {lifecycle_status!r} cannot declare replicates_result.", result_id))
            elif lifecycle_status == "replicated":
                mismatches: list[str] = []
                _, replication_protocol, replication_protocol_mismatches = self.protocol_manifest_context(selected_view, result.get("protocol_release_id"))
                replication_policy = replication_protocol.get("result_binding_policy") if isinstance(replication_protocol, dict) and not replication_protocol_mismatches else None
                if not isinstance(replication_policy, dict) or replication_policy.get("current_replication_target_required") is not True:
                    mismatches.append("protocol requires current replication target")
                if not isinstance(replication, dict):
                    mismatches.append("missing typed replication reference")
                    replicated_record = None
                else:
                    replication_path = replication.get("path")
                    try:
                        replicated_raw = selected_view.read_bytes(replication_path)
                        replicated_record = strict_json_loads(replicated_raw.decode("utf-8"))
                    except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError, StrictJSONError, TypeError):
                        replicated_raw = None
                        replicated_record = None
                        mismatches.append("current target bytes")
                    if replication.get("record_id") == result_id:
                        mismatches.append("distinct record_id")
                    if replication.get("record_kind") != "result" or replication.get("schema_id") != RESULT_SCHEMA_ID:
                        mismatches.append("typed result kind/schema")
                    if replicated_raw is not None and replication.get("sha256") != digest_bytes(replicated_raw):
                        mismatches.append("sha256")
                    if isinstance(replicated_record, dict):
                        checks = (
                            (replicated_record.get("artifact_id"), replication.get("artifact_id"), "artifact_id"),
                            (replicated_record.get("result_id"), replication.get("record_id"), "record_id"),
                            (replicated_record.get("version"), replication.get("version"), "version"),
                            (replicated_record.get("schema_id"), RESULT_SCHEMA_ID, "schema_id"),
                            (replicated_record.get("protocol_release_id"), result.get("protocol_release_id"), "protocol_release_id"),
                            (replicated_record.get("analysis_specification_id"), result.get("analysis_specification_id"), "analysis_specification_id"),
                        )
                        mismatches.extend(label for actual, expected, label in checks if actual != expected)
                        if replicated_record.get("experiment_ref") == result.get("experiment_ref"):
                            mismatches.append("distinct experiment_ref/study identity")
                        current_metric_contract = {
                            (
                                metric.get("metric_id"),
                                metric.get("estimand_id"),
                                metric.get("metric_class"),
                                metric.get("outcome_definition_id"),
                                metric.get("direction"),
                            )
                            for metric in result.get("metric_results", [])
                            if isinstance(metric, dict)
                        }
                        replicated_metric_contract = {
                            (
                                metric.get("metric_id"),
                                metric.get("estimand_id"),
                                metric.get("metric_class"),
                                metric.get("outcome_definition_id"),
                                metric.get("direction"),
                            )
                            for metric in replicated_record.get("metric_results", [])
                            if isinstance(metric, dict)
                        }
                        if current_metric_contract != replicated_metric_contract:
                            mismatches.append("comparable metric/estimand/outcome/direction contract")
                        if replicated_record.get("lifecycle_status") not in {"supported", "replicated"}:
                            mismatches.append("eligible replicated lifecycle")
                        target_heads = result_head_paths.get(replicated_record.get("result_id"), set())
                        if len(target_heads) != 1 or replication_path not in target_heads:
                            mismatches.append("unique current non-superseded result head")
                if mismatches:
                    diagnostics.append(make_diagnostic("GA-RESULT-LINEAGE", relative, f"replicates_result is ineligible; mismatches={sorted(set(mismatches))}.", result_id if isinstance(result_id, str) else None))
                else:
                    replication_lineage_valid = True
            experiment_ref = result.get("experiment_ref")
            experiment_id = experiment_ref.get("experiment_id") if isinstance(experiment_ref, dict) else None
            experiment_version = experiment_ref.get("version") if isinstance(experiment_ref, dict) else None
            experiment_entry = experiments.get((experiment_id, experiment_version)) if isinstance(experiment_id, str) and isinstance(experiment_version, str) else None
            if experiment_entry is None:
                available_versions = sorted(key[1] for key in experiments if key[0] == experiment_id)
                diagnostics.append(make_diagnostic("GA-REFERENCE-DANGLING", relative, f"Result experiment_ref does not resolve exactly: {experiment_id}@{experiment_version}; available_versions={available_versions}.", result.get("result_id")))
                continue
            _, experiment = experiment_entry
            experiment_path = experiment_entry[0]
            if result.get("protocol_release_id") != experiment.get("protocol_release_id"):
                diagnostics.append(make_diagnostic("GA-CONTEXT-MISMATCH", relative, "Result protocol_release_id does not equal its exact experiment protocol release.", result.get("result_id")))
            if result.get("analysis_specification_id") != experiment.get("analysis_plan", {}).get("analysis_specification_id"):
                diagnostics.append(make_diagnostic("GA-CONTEXT-MISMATCH", relative, "Result analysis specification does not match the exact experiment version.", result.get("result_id")))
            _, protocol, protocol_mismatches = self.protocol_manifest_context(selected_view, result.get("protocol_release_id"))
            result_binding_policy = protocol.get("result_binding_policy") if isinstance(protocol, dict) and not protocol_mismatches else None
            policy_fields_valid = (
                isinstance(result_binding_policy, dict)
                and result_binding_policy.get("protocol_release_id") == result.get("protocol_release_id")
                and result_binding_policy.get("exact_experiment_version_required") is True
                and result_binding_policy.get("protocol_release_parity_required") is True
                and result_binding_policy.get("analysis_specification_parity_required") is True
                and result_binding_policy.get("primary_metric_parity_required") is True
                and result_binding_policy.get("current_experiment_head_required") is True
                and result_binding_policy.get("current_replication_target_required") is True
                and result_binding_policy.get("runtime_execution_authorized") is False
                and set(result_binding_policy.get("scientific_disposition_result_statuses", [])) == {"null", "inconclusive", "supported", "contradicted", "replicated"}
                and result_binding_policy.get("metric_derived_result_statuses") == ["invalid", "null", "inconclusive", "failed", "supported", "contradicted", "replicated"]
                and set(result_binding_policy.get("eligible_exact_experiment_statuses", [])) == {"running", "corrected"}
                and result_binding_policy.get("required_experiment_history_status") == "running"
                and set(result_binding_policy.get("preregistered_experiment_required_for_statuses", [])) == {"null", "inconclusive", "supported", "contradicted", "replicated"}
                and result_binding_policy.get("preregistered_before_running_required") is True
                and set(result_binding_policy.get("disallowed_experiment_statuses", [])) == {"proposed", "exploratory", "preregistered", "blocked", "invalid", "failed", "retracted"}
            )
            if not policy_fields_valid:
                diagnostics.append(make_diagnostic("GA-RESULT-EXPERIMENT-INELIGIBLE", relative, "Result cannot resolve an exact governing protocol result-binding policy.", result.get("result_id")))
            else:
                disposition_statuses = set(result_binding_policy.get("scientific_disposition_result_statuses", []))
                if result.get("lifecycle_status") in disposition_statuses:
                    eligible_statuses = set(result_binding_policy.get("eligible_exact_experiment_statuses", []))
                    required_history_status = result_binding_policy.get("required_experiment_history_status")
                    experiment_history = [event.get("status") for event in experiment.get("lifecycle_history", []) if isinstance(event, dict)]
                    preregistered_indexes = [index for index, item in enumerate(experiment_history) if item == "preregistered"]
                    running_indexes = [index for index, item in enumerate(experiment_history) if item == required_history_status]
                    preregistered_before_running = any(
                        preregistered_index < running_index
                        for preregistered_index in preregistered_indexes
                        for running_index in running_indexes
                    )
                    current_heads = experiment_head_paths.get(experiment_id, set())
                    if (
                        experiment.get("lifecycle_status") not in eligible_statuses
                        or required_history_status not in experiment_history
                        or not preregistered_before_running
                        or not preregistration_eligible.get(experiment_path, False)
                        or len(current_heads) != 1
                        or experiment_path not in current_heads
                    ):
                        diagnostics.append(
                            make_diagnostic(
                                "GA-RESULT-EXPERIMENT-INELIGIBLE",
                                relative,
                                f"Scientific result disposition {result.get('lifecycle_status')!r} requires the unique current experiment head in {sorted(eligible_statuses)}, an exact retained preregistration, and preregistered-before-{required_history_status}; observed={experiment.get('lifecycle_status')!r}/{experiment_history}, preregistration_eligible={preregistration_eligible.get(experiment_path, False)}, preregistered_before_running={preregistered_before_running}, heads={sorted(current_heads)}.",
                                result.get("result_id"),
                            )
                        )
            declared_estimands = set(experiment.get("estimand_ids", []))
            declared_groups = set(experiment.get("subgroup_plan", {}).get("group_definition_ids", []))
            declared_decision_rules = set(experiment.get("analysis_plan", {}).get("decision_rule_ids", [])) if isinstance(experiment.get("analysis_plan"), dict) else set()
            declared_abstention_rule = experiment.get("epistemic_policy", {}).get("abstention_rule_id") if isinstance(experiment.get("epistemic_policy"), dict) else None
            analysis_matches = analysis_specifications.get((result.get("protocol_release_id"), result.get("analysis_specification_id")), [])
            analysis_specification = analysis_matches[0][1] if len(analysis_matches) == 1 else None
            if len(analysis_matches) != 1:
                diagnostics.append(make_diagnostic("GA-RESULT-SPECIFICATION-MISMATCH", relative, f"Result analysis_specification_id must resolve exactly once under its protocol; matches={len(analysis_matches)}.", result.get("result_id")))
            protocol_estimand_list = protocol.get("estimands", []) if isinstance(protocol, dict) else []
            protocol_estimands: dict[str, list[dict[str, Any]]] = {}
            for estimand in protocol_estimand_list:
                if isinstance(estimand, dict) and isinstance(estimand.get("estimand_id"), str):
                    protocol_estimands.setdefault(estimand["estimand_id"], []).append(estimand)
            result_metrics = [metric for metric in result.get("metric_results", []) if isinstance(metric, dict)]
            result_metric_ids = [metric.get("metric_id") for metric in result_metrics if isinstance(metric.get("metric_id"), str)]
            frozen_metric_ids = [
                metric.get("metric_id")
                for metric in analysis_specification.get("metric_specifications", [])
                if isinstance(analysis_specification, dict) and isinstance(metric, dict) and isinstance(metric.get("metric_id"), str)
            ] if isinstance(analysis_specification, dict) else []
            if len(result_metric_ids) != len(set(result_metric_ids)):
                diagnostics.append(make_diagnostic("GA-IDENTIFIER-DUPLICATE", relative, "Result metric_id values must be unique.", result.get("result_id")))
            if len(frozen_metric_ids) != len(set(frozen_metric_ids)) or set(result_metric_ids) != set(frozen_metric_ids):
                diagnostics.append(make_diagnostic("GA-RESULT-SPECIFICATION-MISMATCH", relative, f"Result metric inventory must exactly equal the frozen analysis metric inventory; missing={sorted(set(frozen_metric_ids) - set(result_metric_ids))}, extra={sorted(set(result_metric_ids) - set(frozen_metric_ids))}.", result.get("result_id")))
            primary_metric_id = result.get("primary_metric_id")
            primary_metrics = [metric for metric in result_metrics if metric.get("metric_id") == primary_metric_id]
            frozen_primary_metric_id = analysis_specification.get("primary_metric_id") if isinstance(analysis_specification, dict) else None
            primary_mismatches: list[str] = []
            if not isinstance(primary_metric_id, str) or len(primary_metrics) != 1:
                primary_mismatches.append("result primary_metric_id must select exactly one metric")
            if primary_metric_id != frozen_primary_metric_id:
                primary_mismatches.append("result primary_metric_id must equal the frozen analysis primary metric")
            metric_derived_statuses = set(result_binding_policy.get("metric_derived_result_statuses", [])) if policy_fields_valid else set()
            primary_interpretation = primary_metrics[0].get("interpretation_status") if len(primary_metrics) == 1 else None
            if (
                result.get("lifecycle_status") in metric_derived_statuses
                or primary_interpretation in metric_derived_statuses
            ) and (
                len(primary_metrics) != 1
                or primary_interpretation != result.get("lifecycle_status")
            ):
                primary_mismatches.append("metric-derived result lifecycle must equal the primary metric interpretation_status")
            if primary_mismatches:
                diagnostics.append(make_diagnostic("GA-RESULT-STATUS-MISMATCH", relative, f"Result primary-metric status contract failed: {sorted(set(primary_mismatches))}.", result.get("result_id")))
            for metric in result.get("metric_results", []):
                if not isinstance(metric, dict):
                    continue
                metric_id = metric.get("metric_id")
                allowed_metric_statuses = {"proposed", "exploratory", "blocked"} | metric_derived_statuses
                if metric.get("interpretation_status") not in allowed_metric_statuses:
                    diagnostics.append(
                        make_diagnostic(
                            "GA-RESULT-STATUS-MISMATCH",
                            relative,
                            f"Metric interpretation_status {metric.get('interpretation_status')!r} is outside the exact protocol result disposition set and the three nonterminal metric states.",
                            metric_id,
                        )
                    )
                if metric.get("interpretation_status") == "replicated":
                    if lifecycle_status != "replicated":
                        diagnostics.append(make_diagnostic("GA-RESULT-STATUS-MISMATCH", relative, "A replicated metric requires replicated result lifecycle status.", metric_id))
                    if not replication_lineage_valid:
                        diagnostics.append(make_diagnostic("GA-RESULT-LINEAGE", relative, "A replicated metric requires a valid current distinct result-level replication lineage with an exact comparable metric contract.", metric_id))
                if metric.get("decision_rule_id") not in declared_decision_rules:
                    diagnostics.append(make_diagnostic("GA-METRIC-POLICY-BINDING", relative, f"Metric decision_rule_id is not declared by the experiment analysis plan: {metric.get('decision_rule_id')!r}.", metric_id))
                if metric.get("abstention_rule_id") != declared_abstention_rule:
                    diagnostics.append(make_diagnostic("GA-METRIC-POLICY-BINDING", relative, f"Metric abstention_rule_id does not equal the experiment epistemic policy: {metric.get('abstention_rule_id')!r} != {declared_abstention_rule!r}.", metric_id))
                if metric.get("estimand_id") not in declared_estimands:
                    diagnostics.append(make_diagnostic("GA-REFERENCE-DANGLING", relative, f"Metric estimand is not declared by experiment: {metric.get('estimand_id')}.", metric_id))
                specification_mismatches: list[str] = []
                if metric.get("target_population") != experiment.get("target_population"):
                    specification_mismatches.append("target_population")
                if metric.get("comparator") != experiment.get("comparator"):
                    specification_mismatches.append("comparator")
                if metric.get("outcome_definition_id") not in set(experiment.get("outcome_definition_ids", [])):
                    specification_mismatches.append("outcome_definition_id experiment membership")
                estimand_matches = protocol_estimands.get(metric.get("estimand_id"), [])
                if len(estimand_matches) != 1:
                    specification_mismatches.append("unique protocol estimand")
                else:
                    if metric.get("metric_class") != estimand_matches[0].get("metric_class"):
                        specification_mismatches.append("metric_class")
                    if metric.get("direction") != estimand_matches[0].get("direction"):
                        specification_mismatches.append("direction")
                if isinstance(analysis_specification, dict):
                    metric_specs = [
                        item
                        for item in analysis_specification.get("metric_specifications", [])
                        if isinstance(item, dict) and item.get("metric_id") == metric_id
                    ]
                    if len(metric_specs) != 1:
                        specification_mismatches.append("unique frozen metric specification")
                    else:
                        frozen_policy_mismatches = [
                            field
                            for field in ("decision_rule_id", "abstention_rule_id")
                            if metric.get(field) != metric_specs[0].get(field)
                        ]
                        if frozen_policy_mismatches:
                            diagnostics.append(
                                make_diagnostic(
                                    "GA-METRIC-POLICY-BINDING",
                                    relative,
                                    f"Metric policy IDs differ from the exact frozen metric specification: {frozen_policy_mismatches}.",
                                    metric_id,
                                )
                            )
                        for field in (
                            "estimand_id",
                            "metric_class",
                            "outcome_definition_id",
                            "direction",
                            "target_population",
                            "comparator",
                        ):
                            if metric.get(field) != metric_specs[0].get(field):
                                specification_mismatches.append(f"frozen {field}")
                        expected_uncertainty_method = experiment.get("analysis_plan", {}).get("uncertainty_method_id") if isinstance(experiment.get("analysis_plan"), dict) else None
                        frozen_uncertainty_method = metric_specs[0].get("uncertainty_method_id")
                        frozen_confidence_level = metric_specs[0].get("confidence_level")
                        if frozen_uncertainty_method != expected_uncertainty_method:
                            specification_mismatches.append("frozen uncertainty_method_id/experiment analysis plan")
                        uncertainty_surfaces = [("metric", metric.get("uncertainty"))] + [
                            (f"group {group.get('group_id')}", group.get("uncertainty"))
                            for group in metric.get("group_results", [])
                            if isinstance(group, dict)
                        ]
                        for uncertainty_label, uncertainty in uncertainty_surfaces:
                            if not isinstance(uncertainty, dict) or uncertainty.get("method_id") != expected_uncertainty_method or uncertainty.get("method_id") != frozen_uncertainty_method:
                                specification_mismatches.append(f"{uncertainty_label} uncertainty_method_id")
                            if not isinstance(uncertainty, dict) or uncertainty.get("confidence_level") != frozen_confidence_level:
                                specification_mismatches.append(f"{uncertainty_label} confidence_level")
                if specification_mismatches:
                    diagnostics.append(make_diagnostic("GA-RESULT-SPECIFICATION-MISMATCH", relative, f"Result metric differs from its exact experiment, protocol estimand, or frozen analysis specification; mismatches={sorted(set(specification_mismatches))}.", metric_id))
                counts = metric.get("epistemic_counts", {})
                metric_estimate = metric.get("estimate") if isinstance(metric.get("estimate"), dict) else {}
                metric_uncertainty = metric.get("uncertainty") if isinstance(metric.get("uncertainty"), dict) else {}
                metric_lower = metric_uncertainty.get("lower") if isinstance(metric_uncertainty.get("lower"), dict) else {}
                metric_upper = metric_uncertainty.get("upper") if isinstance(metric_uncertainty.get("upper"), dict) else {}

                def observed_number(surface: dict[str, Any]) -> float | None:
                    value = surface.get("value")
                    if surface.get("state") != "observed" or not isinstance(value, (int, float)) or isinstance(value, bool):
                        return None
                    numeric = float(value)
                    return numeric if math.isfinite(numeric) else None

                def interval_mismatches(
                    estimate_surface: dict[str, Any],
                    uncertainty_surface: dict[str, Any],
                    label: str,
                ) -> list[str]:
                    lower_surface = uncertainty_surface.get("lower") if isinstance(uncertainty_surface.get("lower"), dict) else {}
                    upper_surface = uncertainty_surface.get("upper") if isinstance(uncertainty_surface.get("upper"), dict) else {}
                    estimate_value = observed_number(estimate_surface)
                    lower_value = observed_number(lower_surface)
                    upper_value = observed_number(upper_surface)
                    issues: list[str] = []
                    if estimate_surface.get("state") == "observed":
                        if estimate_value is None or lower_value is None or upper_value is None:
                            issues.append(f"{label} observed estimate requires two observed finite interval bounds")
                        elif not (lower_value <= estimate_value <= upper_value):
                            issues.append(f"{label} interval must satisfy lower <= estimate <= upper")
                    else:
                        if lower_surface.get("state") == "observed" or upper_surface.get("state") == "observed":
                            issues.append(f"{label} non-observed estimate cannot carry observed interval bounds")
                        if lower_surface.get("state") != upper_surface.get("state"):
                            issues.append(f"{label} non-observed interval bound states must match")
                    return issues

                uncertainty_issues = interval_mismatches(metric_estimate, metric_uncertainty, "metric")
                if uncertainty_issues:
                    diagnostics.append(
                        make_diagnostic(
                            "GA-RESULT-SPECIFICATION-MISMATCH",
                            relative,
                            f"Metric uncertainty is incoherent; mismatches={sorted(set(uncertainty_issues))}.",
                            metric_id,
                        )
                    )
                if isinstance(counts, dict) and all(isinstance(counts.get(state), int) for state in EXPECTED_EPISTEMIC_STATES):
                    total = sum(counts[state] for state in EXPECTED_EPISTEMIC_STATES)
                    observed = counts["observed"]
                    coverage = metric.get("coverage", {})
                    coverage_value = observed_number(coverage) if isinstance(coverage, dict) else None
                    if total <= 0:
                        diagnostics.append(make_diagnostic("GA-DENOMINATOR-MISMATCH", relative, "Metric epistemic denominator is zero.", metric_id))
                    elif coverage_value is not None:
                        if abs(coverage_value - observed / total) > 1e-12:
                            diagnostics.append(make_diagnostic("GA-DENOMINATOR-MISMATCH", relative, "Metric coverage does not equal observed/total epistemic counts.", metric_id))
                    confident_numeric = (
                        metric_estimate.get("state") == "observed"
                        or metric_lower.get("state") == "observed"
                        or metric_upper.get("state") == "observed"
                    )
                    scientific_disposition = metric.get("interpretation_status") in metric_derived_statuses
                    result_scientific_disposition = metric_id == primary_metric_id and result.get("lifecycle_status") in metric_derived_statuses
                    if (
                        observed <= 0
                        or coverage_value is None
                        or coverage_value <= 0
                    ) and (confident_numeric or scientific_disposition or result_scientific_disposition):
                        diagnostics.append(
                            make_diagnostic(
                                "GA-DENOMINATOR-MISMATCH",
                                relative,
                                "A metric with zero/unobserved coverage or no observed units cannot retain observed estimate/uncertainty or a scientific disposition.",
                                metric_id,
                            )
                        )
                if metric.get("metric_class") == "worst_group":
                    group_ids = [group.get("group_id") for group in metric.get("group_results", []) if isinstance(group, dict) and isinstance(group.get("group_id"), str)]
                    result_groups = set(group_ids)
                    if len(group_ids) != len(result_groups):
                        diagnostics.append(make_diagnostic("GA-IDENTIFIER-DUPLICATE", relative, "Worst-group result group_id values must be unique.", metric_id))
                    if result_groups != declared_groups:
                        diagnostics.append(make_diagnostic("GA-GROUP-OMITTED", relative, f"Worst-group result set differs from declared set; missing={sorted(declared_groups - result_groups)}, extra={sorted(result_groups - declared_groups)}.", metric_id))
                    sample_total = sum(group.get("sample_size", 0) for group in metric.get("group_results", []) if isinstance(group, dict) and isinstance(group.get("sample_size"), int))
                    if isinstance(counts, dict) and sample_total != sum(value for value in counts.values() if isinstance(value, int)):
                        diagnostics.append(make_diagnostic("GA-DENOMINATOR-MISMATCH", relative, "Worst-group sample sizes do not reconcile to metric epistemic counts.", metric_id))
                    for group in metric.get("group_results", []):
                        if not isinstance(group, dict):
                            continue
                        group_id = group.get("group_id") if isinstance(group.get("group_id"), str) else metric_id
                        group_estimate = group.get("estimate") if isinstance(group.get("estimate"), dict) else {}
                        group_uncertainty = group.get("uncertainty") if isinstance(group.get("uncertainty"), dict) else {}
                        group_coverage = group.get("coverage") if isinstance(group.get("coverage"), dict) else {}
                        group_coverage_value = observed_number(group_coverage)
                        group_sample_size = group.get("sample_size")
                        group_interval_issues = interval_mismatches(group_estimate, group_uncertainty, f"group {group_id}")
                        if group_interval_issues:
                            diagnostics.append(
                                make_diagnostic(
                                    "GA-RESULT-SPECIFICATION-MISMATCH",
                                    relative,
                                    f"Group uncertainty is incoherent; mismatches={sorted(set(group_interval_issues))}.",
                                    group_id if isinstance(group_id, str) else None,
                                )
                            )
                        implied_observed = (
                            float(group_sample_size) * group_coverage_value
                            if isinstance(group_sample_size, int) and group_coverage_value is not None
                            else None
                        )
                        count_basis_valid = (
                            isinstance(group_sample_size, int)
                            and group_sample_size > 0
                            and group_coverage_value is not None
                            and group_coverage_value > 0
                            and group_coverage_value <= 1
                            and implied_observed is not None
                            and implied_observed >= 1
                            and abs(implied_observed - round(implied_observed)) <= 1e-12
                        )
                        group_confident = (
                            group_estimate.get("state") == "observed"
                            or (isinstance(group_uncertainty.get("lower"), dict) and group_uncertainty["lower"].get("state") == "observed")
                            or (isinstance(group_uncertainty.get("upper"), dict) and group_uncertainty["upper"].get("state") == "observed")
                        )
                        if not count_basis_valid and (group_confident or group.get("information_disposition") == "sufficient"):
                            diagnostics.append(
                                make_diagnostic(
                                    "GA-WORST-GROUP-MISMATCH",
                                    relative,
                                    "A zero/unobserved/invalid-coverage group cannot be sufficient or carry observed estimate/uncertainty; coverage must imply a positive integral observed count from sample_size.",
                                    group_id if isinstance(group_id, str) else None,
                                )
                            )
                    disposition = metric.get("worst_group_disposition")
                    direction = metric.get("direction")
                    eligible_group_estimates = {
                        group.get("group_id"): float(group.get("estimate", {}).get("value"))
                        for group in metric.get("group_results", [])
                        if isinstance(group, dict)
                        and group.get("information_disposition") == "sufficient"
                        and isinstance(group.get("group_id"), str)
                        and isinstance(group.get("estimate"), dict)
                        and group.get("estimate", {}).get("state") == "observed"
                        and isinstance(group.get("estimate", {}).get("value"), (int, float))
                        and isinstance(group.get("sample_size"), int)
                        and group.get("sample_size") > 0
                        and isinstance(group.get("coverage"), dict)
                        and observed_number(group.get("coverage")) is not None
                        and observed_number(group.get("coverage")) > 0
                    }
                    all_groups_eligible = set(eligible_group_estimates) == declared_groups == result_groups
                    disposition_observed = isinstance(disposition, dict) and disposition.get("state") == "observed"
                    if not all_groups_eligible and disposition_observed:
                        diagnostics.append(make_diagnostic("GA-WORST-GROUP-MISMATCH", relative, "An observed worst-group extremum is prohibited when any declared group is absent, non-observed, or below the sufficient-information criterion.", metric_id))
                    elif all_groups_eligible:
                        expected_worst: set[str] = set()
                        if direction in {"higher_is_better", "lower_is_better"}:
                            extreme = min(eligible_group_estimates.values()) if direction == "higher_is_better" else max(eligible_group_estimates.values())
                            expected_worst = {group_id for group_id, estimate in eligible_group_estimates.items() if estimate == extreme}
                        observed_worst = set(disposition.get("group_ids", [])) if isinstance(disposition, dict) and isinstance(disposition.get("group_ids"), list) else set()
                        selection_rule_id = disposition.get("selection_rule_id") if isinstance(disposition, dict) else None
                        if (
                            not disposition_observed
                            or
                            direction == "signed_contrast"
                            or observed_worst != expected_worst
                            or selection_rule_id != "reiyah.rule.direction-aware-all-ties"
                        ):
                            diagnostics.append(make_diagnostic("GA-WORST-GROUP-MISMATCH", relative, f"Observed worst-group disposition must select every direction-aware tied eligible extremum; expected={sorted(expected_worst)}, observed={sorted(observed_worst)}, direction={direction!r}.", metric_id))
        return diagnostics

    def check_experiment_results(self) -> None:
        paths = sorted(
            relative
            for relative in self.scientific_instance_paths(self.view)
            if isinstance(self.read_view_json(self.view, relative), dict)
            and self.read_view_json(self.view, relative).get("schema_id") in {EXPERIMENT_SCHEMA_ID, RESULT_SCHEMA_ID}
        )
        self.diagnostics.extend(self.experiment_result_diagnostics(paths))

    @staticmethod
    def observed_v11_value(surface: Any) -> Any | None:
        if isinstance(surface, dict) and surface.get("state") == "observed":
            return surface.get("value")
        return None

    @staticmethod
    def v11_reference_key(reference: Any) -> tuple[Any, Any, Any] | None:
        if not isinstance(reference, dict):
            return None
        if {"record_id", "record_kind", "version"} <= set(reference):
            return (reference.get("record_id"), reference.get("record_kind"), reference.get("version"))
        if {"availability_state", "expected_record_id", "expected_record_kind", "expected_version"} <= set(reference):
            return (reference.get("expected_record_id"), reference.get("expected_record_kind"), reference.get("expected_version"))
        return None

    def v11_required_property_counts(
        self,
        document: dict[str, Any],
        relative: str,
    ) -> tuple[int, int, list[dict[str, Any]]]:
        """Return deterministic required-member mutation coverage without side effects."""
        schema_id = document.get("schema_id")
        schema = self.schemas.get(schema_id) if isinstance(schema_id, str) else None
        if not isinstance(schema, dict):
            return (0, 0, [make_diagnostic("GA-V11-REQUIRED-PROPERTY-SWEEP", relative, "Required-property sweep cannot resolve the application schema.")])
        validator = Draft202012Validator(schema, registry=self.registry, format_checker=self.format_checker)
        pointers: list[str] = []

        def walk(value: Any, parts: list[str]) -> None:
            if isinstance(value, dict):
                for key in sorted(value):
                    escaped = key.replace("~", "~0").replace("/", "~1")
                    pointers.append("/" + "/".join(parts + [escaped]))
                    walk(value[key], parts + [escaped])
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    walk(item, parts + [str(index)])

        walk(document, [])
        exercised = 0
        rejected = 0
        diagnostics: list[dict[str, Any]] = []
        for pointer in pointers:
            mutated = mutate_json(document, "remove", pointer)
            errors = list(validator.iter_errors(mutated))
            if any(error.validator == "required" for error in errors):
                exercised += 1
                if errors:
                    rejected += 1
                else:  # defensive: unreachable for a conforming validator
                    diagnostics.append(make_diagnostic("GA-V11-REQUIRED-PROPERTY-SWEEP", relative, f"Required property removal unexpectedly passed at {pointer}."))
        if exercised != rejected:
            diagnostics.append(make_diagnostic("GA-V11-REQUIRED-PROPERTY-SWEEP", relative, f"Required-property mutation coverage is incomplete: exercised={exercised}, rejected={rejected}."))
        return exercised, rejected, diagnostics

    def v11_required_property_sweep(self, document: dict[str, Any], relative: str) -> list[dict[str, Any]]:
        """Remove every exercised object member and prove every required member rejects.

        This is deterministic structural coverage over the same resolved Draft 2020-12
        validator used for production instances.  It does not substitute for the explicit
        cross-field semantic mutations below.
        """
        exercised, rejected, diagnostics = self.v11_required_property_counts(document, relative)
        self.check_summary["v11_required_properties_exercised"] += exercised
        self.check_summary["v11_required_mutations_rejected"] += rejected
        return diagnostics

    def v11_application_diagnostics(
        self,
        document: Any,
        relative: str,
        view: RepositoryView | None = None,
    ) -> list[dict[str, Any]]:
        if not isinstance(document, dict):
            return [make_diagnostic("GA-SCIENTIFIC-CONTRACT-V11", relative, "Scientific-contract application root must be an object.")]
        schema_id = document.get("schema_id")
        rule_id = V11_APPLICATION_RULES.get(schema_id, "GA-SCIENTIFIC-CONTRACT-V11")
        issues: list[str] = []
        selected_view = view or self.view
        schema_errors = self.instance_diagnostics(document, relative)
        if schema_errors:
            issues.extend(f"schema:{item['message']}" for item in schema_errors[:12])
        if document.get("protocol_release_id") != V11_PROTOCOL_RELEASE_ID:
            issues.append("protocol_release_id must bind the current Gate A 1.1 protocol")
        if document.get("runtime_execution_authorized") is not False:
            issues.append("runtime execution must remain unauthorized")
        if document.get("lifecycle_status") != "proposed":
            issues.append("Gate A 1.1 scientific-contract interfaces must remain proposed")
        if "scientific_claim_authorized" in document and document.get("scientific_claim_authorized") is not False:
            issues.append("scientific claims cannot be authorized by a contract instance")

        exact_artifact_keys: set[tuple[Any, Any, Any]] = set()
        unavailable_artifact_keys: set[tuple[Any, Any, Any]] = set()

        def inspect_artifact_bindings(value: Any, pointer: str = "") -> None:
            if isinstance(value, dict):
                if {"artifact_id", "schema_id", "version", "path", "sha256"} <= set(value):
                    key = (value.get("artifact_id"), value.get("schema_id"), value.get("version"))
                    if key in exact_artifact_keys:
                        issues.append(f"{pointer or '/'} repeats one exact artifact identity")
                    exact_artifact_keys.add(key)
                    path = value.get("path")
                    try:
                        raw = selected_view.read_bytes(path) if isinstance(path, str) else None
                    except (OSError, ValueError):
                        raw = None
                    target = self.read_view_json(selected_view, path) if isinstance(path, str) and raw is not None and path.endswith(".json") else None
                    if raw is None:
                        issues.append(f"{pointer or '/'} exact artifact path does not resolve to retained repository bytes")
                    else:
                        if value.get("sha256") != digest_bytes(raw):
                            issues.append(f"{pointer or '/'} exact artifact digest does not match retained bytes")
                        if not isinstance(target, dict):
                            issues.append(f"{pointer or '/'} exact JSON artifact is malformed")
                        elif (
                            target.get("artifact_id") != value.get("artifact_id")
                            or target.get("schema_id") != value.get("schema_id")
                            or target.get("version") != value.get("version")
                        ):
                            issues.append(f"{pointer or '/'} exact artifact identity/schema/version does not match its target")
                elif value.get("availability_state") in {"not_available_in_gate_a", "not_authorized_in_gate_a"} and "expected_artifact_id" in value:
                    key = (value.get("expected_artifact_id"), value.get("expected_schema_id"), value.get("expected_version"))
                    if key in unavailable_artifact_keys:
                        issues.append(f"{pointer or '/'} repeats one unavailable artifact identity")
                    unavailable_artifact_keys.add(key)
                    expected_schema = value.get("expected_schema_id")
                    expected_version = value.get("expected_version")
                    if (
                        (expected_schema is not None and expected_schema not in self.schemas)
                        or ((expected_schema is None) != (expected_version is None))
                        or value.get("gate_b_authorized") is not False
                        or value.get("runtime_execution_authorized") is not False
                        or value.get("earliest_permitted_gate") != "B_after_explicit_operator_acceptance"
                    ):
                        issues.append(f"{pointer or '/'} unavailable artifact gap must use matched schema/version knowledge (or explicit null unknowns) and confer no Gate-B/runtime authority")
                for key in sorted(value):
                    escaped = key.replace("~", "~0").replace("/", "~1")
                    inspect_artifact_bindings(value[key], f"{pointer}/{escaped}")
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    inspect_artifact_bindings(item, f"{pointer}/{index}")

        inspect_artifact_bindings(document)

        def timestamp(value: Any) -> datetime | None:
            return parse_exact_utc(self.observed_v11_value(value) if isinstance(value, dict) else value)

        def ids(items: Any, key: str) -> list[str]:
            return [item.get(key) for item in items if isinstance(item, dict) and isinstance(item.get(key), str)] if isinstance(items, list) else []

        def unavailable_reference(reference: Any, expected_kind: str) -> bool:
            return bool(
                isinstance(reference, dict)
                and reference.get("availability_state") in {"not_available_in_gate_a", "not_authorized_in_gate_a"}
                and isinstance(reference.get("expected_record_id"), str)
                and reference.get("expected_record_kind") == expected_kind
                and reference.get("expected_version") == "1.1.0"
                and reference.get("earliest_permitted_gate") == "B_after_explicit_operator_acceptance"
                and reference.get("gate_b_authorized") is False
                and reference.get("runtime_execution_authorized") is False
            )

        definition_registry = self.read_view_json(selected_view, "manifests/definitions/harbor-gate-a-definition-registry-1.1.0.json")
        definition_rows = definition_registry.get("definitions", []) if isinstance(definition_registry, dict) and isinstance(definition_registry.get("definitions"), list) else []

        def definition(identifier: Any, kind: str) -> dict[str, Any] | None:
            matches = [
                item
                for item in definition_rows
                if isinstance(item, dict)
                and item.get("definition_id") == identifier
                and item.get("kind") == kind
                and item.get("version") == "1.1.0"
                and item.get("owner_protocol_release_id") == V11_PROTOCOL_RELEASE_ID
            ]
            return matches[0] if len(matches) == 1 else None

        if "mission_release_id" in document and document.get("mission_release_id") != V11_MISSION_RELEASE_ID:
            issues.append("application must bind the current Gate A 1.1 mission release")

        history = document.get("lifecycle_history") if isinstance(document.get("lifecycle_history"), list) else []
        sequences = [event.get("sequence") for event in history if isinstance(event, dict)]
        history_times = [parse_exact_utc(event.get("recorded_at")) for event in history if isinstance(event, dict)]
        event_ids = [event.get("event_id") for event in history if isinstance(event, dict)]
        if (
            not history
            or len(sequences) != len(history)
            or sequences != list(range(1, len(history) + 1))
            or not all(isinstance(value, str) for value in event_ids)
            or len(event_ids) != len(set(event_ids))
            or any(value is None for value in history_times)
            or any(later <= earlier for earlier, later in zip(history_times, history_times[1:]) if earlier is not None and later is not None)
            or history[0].get("prior_status") is not None
            or history[0].get("status") != "proposed"
            or history[0].get("prior_artifact") is not None
            or any(current.get("prior_status") != prior.get("status") for prior, current in zip(history, history[1:]) if isinstance(prior, dict) and isinstance(current, dict))
            or not isinstance(history[-1], dict)
            or history[-1].get("status") != document.get("lifecycle_status")
        ):
            issues.append("lifecycle history must be a unique, contiguous, monotone, append-only chain ending at the current status")
        for index, event in enumerate(history[1:], start=1):
            if not isinstance(event, dict):
                continue
            prior = event.get("prior_artifact") if isinstance(event.get("prior_artifact"), dict) else {}
            prior_path = prior.get("path")
            prior_document = self.read_view_json(selected_view, prior_path) if isinstance(prior_path, str) else None
            if (
                not isinstance(prior_document, dict)
                or prior_document.get("lifecycle_history") != history[:index]
                or prior_document.get("lifecycle_status") != event.get("prior_status")
            ):
                issues.append(f"lifecycle event sequence {index + 1} must append exactly once to its immutable immediate predecessor history")

        if schema_id == "https://schemas.reiyah.invalid/scientific-contract/1.1.0/human-automation-assessment.schema.json":
            belief = document.get("belief_assessment") if isinstance(document.get("belief_assessment"), dict) else {}
            decision = document.get("decision_record") if isinstance(document.get("decision_record"), dict) else {}
            readiness = document.get("readiness_assessment") if isinstance(document.get("readiness_assessment"), dict) else {}
            recovery = document.get("recoverability_assessment") if isinstance(document.get("recoverability_assessment"), dict) else {}
            holder = belief.get("belief_holder")
            target = belief.get("target", {}).get("target_agent_ref") if isinstance(belief.get("target"), dict) else None
            actor_surfaces = {
                "belief holder": holder,
                "belief target": target,
                "decision actor": decision.get("decision_actor"),
                "readiness subject": readiness.get("subject_agent_ref"),
                "recoverability subject": recovery.get("subject_agent_ref"),
            }
            if not unavailable_reference(document.get("encounter_ref"), "encounter"):
                issues.append("the Gate A human assessment encounter must remain an explicit non-authoritative unavailable reference")
            for label, actor in actor_surfaces.items():
                if not isinstance(actor, dict) or not isinstance(actor.get("actor_id"), str) or not isinstance(actor.get("actor_type"), str):
                    issues.append(f"{label} must resolve as a typed actor reference")
            target_id = target.get("actor_id") if isinstance(target, dict) else None
            holder_id = holder.get("actor_id") if isinstance(holder, dict) else None
            if isinstance(holder_id, str) and holder_id == target_id:
                issues.append("belief holder and target actor must remain distinct typed roles")
            if any(
                isinstance(surface, dict) and surface.get("actor_id") != target_id
                for surface in (readiness.get("subject_agent_ref"), recovery.get("subject_agent_ref"))
            ):
                issues.append("belief target, readiness subject, and recoverability subject must identify the same actor")
            authority = decision.get("authority") if isinstance(decision.get("authority"), dict) else {}
            authority_state = authority.get("authority_state") if isinstance(authority.get("authority_state"), dict) else {}
            authority_observed = authority_state.get("state") == "observed"
            if authority_observed != isinstance(authority.get("basis_ref"), dict):
                issues.append("an observed decision-authority disposition requires one typed basis reference; a non-observed disposition requires null basis")
            choice_set = definition(decision.get("choice_set_id"), "choice_set")
            selected_choice = self.observed_v11_value(decision.get("selected_action"))
            if selected_choice is not None and (
                choice_set is None
                or selected_choice not in choice_set.get("member_ids", [])
            ):
                issues.append("observed selected action must be an exact member of the referenced protocol choice set")
            distribution = belief.get("distribution") if isinstance(belief.get("distribution"), dict) else {}
            if distribution.get("state") == "observed":
                components = distribution.get("components", [])
                probabilities = [item.get("probability") for item in components if isinstance(item, dict)] if isinstance(components, list) else []
                state_ids = [item.get("state_id") for item in components if isinstance(item, dict)] if isinstance(components, list) else []
                state_space = definition(belief.get("calibration_target", {}).get("target_state_space_id") if isinstance(belief.get("calibration_target"), dict) else None, "state_space")
                expected_state_ids = set(state_space.get("member_ids", [])) if isinstance(state_space, dict) and isinstance(state_space.get("member_ids"), list) else set()
                tolerance = distribution.get("normalization_tolerance")
                if (
                    len(probabilities) != len(components)
                    or any(not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)) for value in probabilities)
                    or not isinstance(tolerance, (int, float))
                    or abs(sum(float(value) for value in probabilities if isinstance(value, (int, float))) - 1.0) > float(tolerance or 0)
                    or len(state_ids) != len(set(state_ids))
                    or not expected_state_ids
                    or set(state_ids) != expected_state_ids
                ):
                    issues.append("observed belief probabilities must be finite, normalized, and cover the exact protocol-owned target state-space members")
            calibration = belief.get("calibration_target") if isinstance(belief.get("calibration_target"), dict) else {}
            reference_process = calibration.get("reference_process_ref") if isinstance(calibration.get("reference_process_ref"), dict) else {}
            if (
                not isinstance(reference_process.get("actor_id"), str)
                or reference_process.get("actor_type") != "derived_process"
                or reference_process.get("version") != "1.1.0"
                or not isinstance(calibration.get("decision_loss_rule_id"), str)
            ):
                issues.append("calibration target must bind a typed reference process and decision-loss rule")
            abstention = belief.get("abstention_policy") if isinstance(belief.get("abstention_policy"), dict) else {}
            if abstention.get("forced_confidence_prohibited") is not True or not abstention.get("eligible_states"):
                issues.append("belief abstention policy must preserve explicit non-observed states and prohibit forced confidence")
            decided_at = timestamp(decision.get("decided_at"))
            belief_set = belief.get("conditioning_information_set") if isinstance(belief.get("conditioning_information_set"), dict) else {}
            decision_set = decision.get("information_set") if isinstance(decision.get("information_set"), dict) else {}
            if decision_set.get("post_freeze_additions_prohibited") is not True:
                issues.append("decision information set must be immutable after freeze")
            availability_by_ref: dict[tuple[Any, Any, Any], dict[str, Any]] = {}
            for item in document.get("observation_availability", []):
                if not isinstance(item, dict):
                    continue
                key = self.v11_reference_key(item.get("observation_ref"))
                if key is None or key in availability_by_ref:
                    issues.append("observation availability references must be typed and unique")
                    continue
                availability_by_ref[key] = item
                ordered = [timestamp(item.get(name)) for name in ("event_time", "recorded_at", "available_at")]
                if None in ordered or decided_at is None or not (ordered[0] <= ordered[1] <= ordered[2] <= decided_at):
                    issues.append(f"observation {key[0]!r} must satisfy event <= recorded <= available <= decision")
                if item.get("availability_before_decision") is not True:
                    issues.append("availability_before_decision assertion must remain true and be recomputed")
            belief_items = belief_set.get("items", []) if isinstance(belief_set.get("items"), list) else []
            decision_items = decision_set.get("items", []) if isinstance(decision_set.get("items"), list) else []
            belief_refs = {self.v11_reference_key(item.get("item_ref")) for item in belief_items if isinstance(item, dict)}
            decision_refs = {self.v11_reference_key(item.get("item_ref")) for item in decision_items if isinstance(item, dict)}
            available_refs = set(availability_by_ref)
            if None in belief_refs | decision_refs or belief_refs != decision_refs or belief_refs != available_refs:
                issues.append("belief, decision, and observation-availability information sets must reconcile exactly")
            for item in belief_items + decision_items:
                if not isinstance(item, dict):
                    continue
                key = self.v11_reference_key(item.get("item_ref"))
                source = availability_by_ref.get(key, {})
                if timestamp(item.get("available_at")) != timestamp(source.get("available_at")):
                    issues.append(f"information-set availability does not match the observation record for {key}")
                source_ref = item.get("source_ref") if isinstance(item.get("source_ref"), dict) else {}
                availability_source = source.get("availability_source") if isinstance(source.get("availability_source"), dict) else {}
                capture_source = source.get("capture_source_ref") if isinstance(source.get("capture_source_ref"), dict) else {}
                source_identity = tuple(source_ref.get(field) for field in ("actor_id", "actor_type", "version"))
                if source_identity != tuple(availability_source.get(field) for field in ("actor_id", "actor_type", "version")) or source_identity != tuple(capture_source.get(field) for field in ("actor_id", "actor_type", "version")):
                    issues.append(f"information-set source does not reconcile to capture and availability sources for {key}")
            for info_set, label in ((belief_set, "belief"), (decision_set, "decision")):
                frozen = parse_exact_utc(info_set.get("frozen_at"))
                if frozen is None or decided_at is None or frozen > decided_at:
                    issues.append(f"{label} information set must freeze no later than the decision")
            info_ref_expected = (belief_set.get("information_set_id"), belief_set.get("version"))
            for surface, label in ((readiness, "readiness"), (recovery, "recoverability")):
                ref = surface.get("information_set_ref") if isinstance(surface.get("information_set_ref"), dict) else {}
                if (ref.get("information_set_id"), ref.get("version")) != info_ref_expected:
                    issues.append(f"{label} must bind the exact conditioning information set")
            required_capabilities = set(readiness.get("task_definition", {}).get("required_capability_ids", [])) if isinstance(readiness.get("task_definition"), dict) else set()
            capability_ids = ids(readiness.get("capability_estimates"), "capability_id")
            if not required_capabilities or len(capability_ids) != len(set(capability_ids)) or set(capability_ids) != required_capabilities:
                issues.append("readiness must represent every required task capability exactly once")
            if readiness.get("proxy_substitution_prohibited") is not True or not isinstance(readiness.get("decision_rule_id"), str) or not isinstance(readiness.get("loss_function_id"), str):
                issues.append("readiness requires a registered decision/loss contract and prohibits proxy substitution")
            readiness_window = readiness.get("assessment_window") if isinstance(readiness.get("assessment_window"), dict) else {}
            ready_open, ready_close = timestamp(readiness_window.get("opens_at")), timestamp(readiness_window.get("closes_at"))
            ready_as_of = timestamp(readiness.get("as_of_time"))
            if None in (ready_open, ready_close, ready_as_of) or not (ready_open <= ready_as_of <= ready_close):
                issues.append("readiness as-of time must lie inside its registered assessment window")
            recovery_window = recovery.get("opportunity_window") if isinstance(recovery.get("opportunity_window"), dict) else {}
            recovery_open, recovery_close = timestamp(recovery_window.get("opens_at")), timestamp(recovery_window.get("closes_at"))
            event_ids: list[str] = []
            previous_event: datetime | None = None
            for event in recovery.get("recovery_events", []):
                if not isinstance(event, dict):
                    continue
                event_id, event_time = event.get("event_id"), timestamp(event.get("occurred_at"))
                if isinstance(event_id, str):
                    event_ids.append(event_id)
                if event_time is None or recovery_open is None or recovery_close is None or not (recovery_open <= event_time <= recovery_close) or (previous_event is not None and event_time < previous_event):
                    issues.append("recovery event history must be monotone and contained by the recovery opportunity window")
                previous_event = event_time
            if not event_ids or len(event_ids) != len(set(event_ids)):
                issues.append("recoverability requires a nonempty uniquely identified event history")
            competing = recovery.get("competing_event_policy") if isinstance(recovery.get("competing_event_policy"), dict) else {}
            censoring = recovery.get("censoring_policy") if isinstance(recovery.get("censoring_policy"), dict) else {}
            if competing.get("omission_prohibited") is not True or censoring.get("omission_prohibited") is not True or not censoring.get("censoring_event_ids"):
                issues.append("recoverability must bind explicit competing-event and censoring dispositions")

        elif schema_id == "https://schemas.reiyah.invalid/scientific-contract/1.1.0/joint-performance-evaluation.schema.json":
            opportunity = document.get("opportunity_definition") if isinstance(document.get("opportunity_definition"), dict) else {}
            eligible = self.observed_v11_value(opportunity.get("eligible_opportunities"))
            if not isinstance(eligible, int) or isinstance(eligible, bool) or eligible <= 0 or opportunity.get("denominator_reconciliation_required") is not True:
                issues.append("joint evaluation requires a positive observed common opportunity denominator")
            actor_performance = document.get("actor_performance") if isinstance(document.get("actor_performance"), dict) else {}
            actor_miss_rates: dict[str, float] = {}
            for actor_name in ("human", "automation"):
                actor = actor_performance.get(actor_name) if isinstance(actor_performance.get(actor_name), dict) else {}
                counts = [self.observed_v11_value(actor.get(name)) for name in ("detections", "misses", "abstentions", "invalid_observations")]
                actor_eligible = self.observed_v11_value(actor.get("eligible_opportunities"))
                miss_rate = self.observed_v11_value(actor.get("miss_rate"))
                if actor_eligible != eligible or any(not isinstance(value, int) for value in counts) or sum(value for value in counts if isinstance(value, int)) != eligible:
                    issues.append(f"{actor_name} channel counts must reconcile exactly to the shared opportunity denominator")
                if isinstance(eligible, int) and eligible > 0 and isinstance(miss_rate, (int, float)) and isinstance(counts[1], int) and abs(float(miss_rate) - counts[1] / eligible) > 1e-12:
                    issues.append(f"{actor_name} miss rate must equal misses/opportunities")
                elif isinstance(miss_rate, (int, float)):
                    actor_miss_rates[actor_name] = float(miss_rate)
            joint = document.get("joint_silent_miss") if isinstance(document.get("joint_silent_miss"), dict) else {}
            human_misses = self.observed_v11_value(joint.get("human_misses"))
            automation_misses = self.observed_v11_value(joint.get("automation_misses"))
            joint_misses = self.observed_v11_value(joint.get("joint_silent_misses"))
            joint_rate = self.observed_v11_value(joint.get("joint_silent_miss_rate"))
            if (
                self.observed_v11_value(joint.get("eligible_opportunities")) != eligible
                or not isinstance(eligible, int)
                or eligible <= 0
                or not all(isinstance(value, int) for value in (human_misses, automation_misses, joint_misses))
                or joint_misses > min(human_misses, automation_misses)
                or not isinstance(joint_rate, (int, float))
                or abs(float(joint_rate) - joint_misses / eligible) > 1e-12
                or not isinstance(joint.get("dependence_analysis"), dict)
            ):
                issues.append("joint silent misses, rate, and dependence analysis must reconcile to both actor marginals")
            dependence = joint.get("dependence_analysis") if isinstance(joint.get("dependence_analysis"), dict) else {}
            expected_independence = self.observed_v11_value(dependence.get("expected_joint_rate_under_independence"))
            observed_dependence = self.observed_v11_value(dependence.get("observed_joint_rate"))
            excess_dependence = self.observed_v11_value(dependence.get("excess_joint_rate"))
            dependence_ratio = self.observed_v11_value(dependence.get("dependence_ratio"))
            reconstructed_independence = actor_miss_rates.get("human", math.nan) * actor_miss_rates.get("automation", math.nan)
            if (
                not all(isinstance(value, (int, float)) and math.isfinite(float(value)) for value in (expected_independence, observed_dependence, excess_dependence, dependence_ratio))
                or not math.isfinite(reconstructed_independence)
                or abs(float(expected_independence) - reconstructed_independence) > 1e-12
                or not isinstance(joint_rate, (int, float))
                or abs(float(observed_dependence) - float(joint_rate)) > 1e-12
                or abs(float(excess_dependence) - (float(observed_dependence) - float(expected_independence))) > 1e-12
                or float(expected_independence) <= 0
                or abs(float(dependence_ratio) - float(observed_dependence) / float(expected_independence)) > 1e-9
            ):
                issues.append("dependence analysis must exactly reconstruct independent, observed, excess, and ratio quantities")
            selective = document.get("selective_prediction") if isinstance(document.get("selective_prediction"), dict) else {}
            selective_counts = [self.observed_v11_value(selective.get(name)) for name in ("accepted_predictions", "abstentions", "ood_predictions", "sensor_invalid_predictions")]
            total_predictions = self.observed_v11_value(selective.get("total_predictions"))
            coverage = self.observed_v11_value(selective.get("coverage"))
            if selective.get("threshold_preregistered") is not True or not isinstance(total_predictions, int) or total_predictions <= 0 or any(not isinstance(value, int) for value in selective_counts) or sum(value for value in selective_counts if isinstance(value, int)) != total_predictions or not isinstance(coverage, (int, float)) or (isinstance(selective_counts[0], int) and isinstance(total_predictions, int) and total_predictions > 0 and abs(float(coverage) - selective_counts[0] / total_predictions) > 1e-12):
                issues.append("selective prediction threshold, counts, and coverage must be preregistered and arithmetically coherent")
            ood = document.get("ood_evaluation") if isinstance(document.get("ood_evaluation"), dict) else {}
            if ood.get("unresolved_items_retained") is not True:
                issues.append("OOD evaluation must retain unresolved items explicitly")
            conformal = document.get("conformal_evaluation") if isinstance(document.get("conformal_evaluation"), dict) else {}
            if not isinstance(conformal.get("calibration_dataset_ref"), dict) or not isinstance(conformal.get("exchangeability_assessment"), dict):
                issues.append("conformal evaluation requires a typed calibration set and explicit exchangeability disposition")
            transfer = document.get("transfer_evaluation") if isinstance(document.get("transfer_evaluation"), dict) else {}
            access_times = [parse_exact_utc(event.get("occurred_at")) for event in transfer.get("target_access_chronology", []) if isinstance(event, dict)]
            if not transfer.get("shift_dimensions") or not access_times or any(value is None for value in access_times) or access_times != sorted(access_times):
                issues.append("transfer evaluation requires declared shift dimensions and monotone target-access chronology")
            source_performance = self.observed_v11_value(transfer.get("source_performance"))
            target_performance = self.observed_v11_value(transfer.get("target_performance"))
            transfer_gap = self.observed_v11_value(transfer.get("transfer_gap"))
            if all(isinstance(value, (int, float)) for value in (source_performance, target_performance, transfer_gap)) and abs(float(transfer_gap) - (float(target_performance) - float(source_performance))) > 1e-12:
                issues.append("transfer gap must equal target performance minus source performance")
            worst = document.get("worst_group_evaluation") if isinstance(document.get("worst_group_evaluation"), dict) else {}
            declared_groups = worst.get("group_definition_ids", []) if isinstance(worst.get("group_definition_ids"), list) else []
            result_groups = ids(worst.get("group_results"), "group_id")
            conformal_groups = ids(conformal.get("conditional_group_results"), "group_id")
            if len(conformal_groups) != len(set(conformal_groups)) or set(conformal_groups) != set(declared_groups):
                issues.append("conditional conformal results must exactly cover the declared worst-group universe")
            if len(declared_groups) != len(set(declared_groups)) or len(result_groups) != len(set(result_groups)) or set(declared_groups) != set(result_groups) or worst.get("omission_prohibited") is not True or worst.get("all_ties_required") is not True:
                issues.append("worst-group results must cover the unique declared group universe without omission")
            eligible_values: dict[str, float] = {}
            for group in worst.get("group_results", []):
                if not isinstance(group, dict):
                    continue
                sample_size = self.observed_v11_value(group.get("sample_size"))
                performance = self.observed_v11_value(group.get("performance"))
                if group.get("information_disposition") == "sufficient" and isinstance(sample_size, int) and sample_size > 0 and isinstance(performance, (int, float)):
                    eligible_values[group.get("group_id")] = float(performance)
            disposition = worst.get("worst_group_disposition") if isinstance(worst.get("worst_group_disposition"), dict) else {}
            if set(eligible_values) != set(declared_groups):
                if disposition.get("state") == "observed":
                    issues.append("an observed worst group is prohibited when any declared group has insufficient information")
            elif eligible_values:
                extreme = min(eligible_values.values()) if worst.get("direction") == "higher_is_better" else max(eligible_values.values())
                expected = {key for key, value in eligible_values.items() if value == extreme}
                if disposition.get("state") != "observed" or set(disposition.get("group_ids", [])) != expected or disposition.get("selection_rule_id") != worst.get("selection_rule_id"):
                    issues.append("worst-group disposition must select every direction-aware tied extremum")

        elif schema_id == "https://schemas.reiyah.invalid/scientific-contract/1.1.0/study-design-preregistration.schema.json":
            if document.get("mission_release_id") != V11_MISSION_RELEASE_ID:
                issues.append("study design must bind the current mission release")
            prereg = document.get("preregistration") if isinstance(document.get("preregistration"), dict) else {}
            registered_at = timestamp(prereg.get("registered_at"))
            boundary = prereg.get("observation_boundary") if isinstance(prereg.get("observation_boundary"), dict) else {}
            boundary_open, boundary_close = timestamp(boundary.get("opens_at")), timestamp(boundary.get("closes_at"))
            preregistration_executed = prereg.get("status") != "proposed"
            if (
                None in (boundary_open, boundary_close)
                or not boundary_open < boundary_close
                or prereg.get("immutable_after_registration") is not True
                or prereg.get("outcome_access_before_registration_prohibited") is not True
                or (preregistration_executed and (registered_at is None or registered_at >= boundary_open))
                or (not preregistration_executed and registered_at is not None)
            ):
                issues.append("executed preregistration must be immutable and precede the observation boundary; a proposed design must not assert execution time")
            power = document.get("power_analysis") if isinstance(document.get("power_analysis"), dict) else {}
            if power.get("state") != "observed" or power.get("estimand_id") not in document.get("estimand_ids", []) or not isinstance(power.get("required_sample_size"), int) or power.get("required_sample_size", 0) <= 0:
                issues.append("power analysis must be observed, positive, and bind a declared estimand")
            stopping = document.get("stopping_rule") if isinstance(document.get("stopping_rule"), dict) else {}
            if stopping.get("optional_stopping_prohibited") is not True:
                issues.append("optional stopping must be prohibited by the frozen stopping rule")
            graph = document.get("causal_graph") if isinstance(document.get("causal_graph"), dict) else {}
            node_ids = ids(graph.get("nodes"), "node_id")
            if len(node_ids) != len(set(node_ids)):
                issues.append("causal DAG node identifiers must be unique")
            edges = [(edge.get("from_node_id"), edge.get("to_node_id")) for edge in graph.get("edges", []) if isinstance(edge, dict)]
            adjacency: dict[str, set[str]] = {node: set() for node in node_ids}
            for source, target in edges:
                if source not in adjacency or target not in adjacency or source == target:
                    issues.append("causal DAG edges must resolve to distinct declared nodes")
                else:
                    adjacency[source].add(target)
            visiting: set[str] = set()
            visited: set[str] = set()
            def cyclic(node: str) -> bool:
                if node in visiting:
                    return True
                if node in visited:
                    return False
                visiting.add(node)
                result = any(cyclic(child) for child in adjacency.get(node, set()))
                visiting.discard(node)
                visited.add(node)
                return result
            if graph.get("acyclicity_asserted") is not True or any(cyclic(node) for node in node_ids):
                issues.append("causal graph must be an actually acyclic declared DAG")
            control = document.get("control_strategy") if isinstance(document.get("control_strategy"), dict) else {}
            adjustment_sets = graph.get("adjustment_sets", []) if isinstance(graph.get("adjustment_sets"), list) else []
            adjustment_set_ids = ids(adjustment_sets, "adjustment_set_id")
            if len(adjustment_set_ids) != len(set(adjustment_set_ids)):
                issues.append("causal adjustment-set identifiers must be unique")
            declared_adjustment_values: list[set[str]] = []
            for adjustment_set in adjustment_sets:
                members = adjustment_set.get("node_ids", []) if isinstance(adjustment_set, dict) and isinstance(adjustment_set.get("node_ids"), list) else []
                if not members or len(members) != len(set(members)) or any(member not in set(node_ids) for member in members):
                    issues.append("every adjustment set must contain a unique nonempty subset of declared causal DAG nodes")
                declared_adjustment_values.append(set(members))
            graph_ref_fields = {
                "treatment_node_ids": graph.get("treatment_node_ids", []),
                "outcome_node_ids": graph.get("outcome_node_ids", []),
                "adjustment_variable_ids": control.get("adjustment_variable_ids", []),
                "negative_control_exposure_ids": control.get("negative_control_exposure_ids", []),
                "negative_control_outcome_ids": control.get("negative_control_outcome_ids", []),
                "prohibited_control_ids": control.get("prohibited_control_ids", []),
            }
            for field, values in graph_ref_fields.items():
                if not isinstance(values, list) or any(value not in set(node_ids) for value in values) or len(values) != len(set(values)):
                    issues.append(f"{field} must resolve uniquely to declared causal DAG nodes")
            selected_adjustments = set(control.get("adjustment_variable_ids", [])) if isinstance(control.get("adjustment_variable_ids"), list) else set()
            if selected_adjustments and selected_adjustments not in declared_adjustment_values:
                issues.append("control-strategy adjustment variables must equal one explicitly declared DAG adjustment set")
            missingness = document.get("missingness_plan") if isinstance(document.get("missingness_plan"), dict) else {}
            if missingness.get("coercion_to_zero_prohibited") is not True or missingness.get("complete_case_default_prohibited") is not True:
                issues.append("missingness must stay explicit and cannot default to zero or complete-case deletion")
            splits = document.get("data_splits") if isinstance(document.get("data_splits"), dict) else {}
            partitions = splits.get("partitions", []) if isinstance(splits.get("partitions"), list) else []
            partition_ids = ids(partitions, "partition_id")
            if len(partition_ids) != len(set(partition_ids)) or splits.get("group_leakage_prohibited") is not True or splits.get("temporal_leakage_prohibited") is not True or splits.get("test_reuse_prohibited") is not True:
                issues.append("data splits must be unique, frozen, and prohibit group/temporal leakage and test reuse")
            freeze_deadline = registered_at if preregistration_executed else boundary_open
            for partition in partitions:
                frozen = parse_exact_utc(partition.get("frozen_at")) if isinstance(partition, dict) else None
                if frozen is None or freeze_deadline is None or frozen > freeze_deadline:
                    issues.append("every data partition must freeze no later than executed preregistration or the proposed observation boundary")
            chronology = document.get("access_chronology", [])
            sequences = [event.get("sequence") for event in chronology if isinstance(event, dict)] if isinstance(chronology, list) else []
            chronology_times = [parse_exact_utc(event.get("recorded_at")) for event in chronology if isinstance(event, dict)] if isinstance(chronology, list) else []
            chronology_deadline = registered_at if preregistration_executed else boundary_open
            if not chronology or sequences != list(range(1, len(sequences) + 1)) or any(value is None for value in chronology_times) or chronology_times != sorted(chronology_times) or chronology_deadline is None or chronology_times[-1] > chronology_deadline:
                issues.append("study access chronology must be contiguous, monotone, and no later than executed preregistration or the proposed observation boundary")
            if prereg.get("status") == "proposed" and any(isinstance(event, dict) and event.get("action") == "analysis_preregistered" for event in chronology):
                issues.append("a proposed preregistration cannot record analysis_preregistered as an accomplished access event")
            for deviation in document.get("deviations", []):
                if isinstance(deviation, dict) and deviation.get("authorized_by_preregistration") is True:
                    issues.append("post-registration deviations cannot be relabeled as preregistered")

        elif schema_id == "https://schemas.reiyah.invalid/scientific-contract/1.1.0/sequential-off-policy-evaluation.schema.json":
            if document.get("mission_release_id") != V11_MISSION_RELEASE_ID or document.get("policy_versions_exact") is not True:
                issues.append("sequential OPE must bind current mission and exact behavior/target policy versions")
            behavior = document.get("behavior_policy") if isinstance(document.get("behavior_policy"), dict) else {}
            target = document.get("target_policy") if isinstance(document.get("target_policy"), dict) else {}
            if not unavailable_reference(behavior.get("policy_ref"), "policy") or not unavailable_reference(target.get("policy_ref"), "policy"):
                issues.append("Gate A behavior and target policies must remain explicit non-authoritative unavailable versioned references")
            if behavior.get("action_space_id") != target.get("action_space_id") or behavior.get("information_set_schema_id") != target.get("information_set_schema_id") or self.v11_reference_key(behavior.get("policy_ref")) == self.v11_reference_key(target.get("policy_ref")):
                issues.append("behavior and target policies must be distinct exact versions over the same action and information spaces")
            action_space = definition(behavior.get("action_space_id"), "action_space")
            action_members = set(action_space.get("member_ids", [])) if isinstance(action_space, dict) and isinstance(action_space.get("member_ids"), list) else set()
            if not action_members:
                issues.append("OPE action space must resolve to a nonempty protocol-owned member set")
            horizon = document.get("horizon") if isinstance(document.get("horizon"), dict) else {}
            max_steps = horizon.get("maximum_steps")
            weights: list[float] = []
            trajectory_ids: list[str] = []
            for trajectory in document.get("trajectories", []):
                if not isinstance(trajectory, dict):
                    continue
                trajectory_ids.append(trajectory.get("trajectory_id"))
                if not unavailable_reference(trajectory.get("encounter_ref"), "encounter") or not unavailable_reference(trajectory.get("behavior_policy_ref"), "policy") or not unavailable_reference(trajectory.get("target_policy_ref"), "policy"):
                    issues.append("every Gate A trajectory must preserve explicit unavailable encounter and policy bindings")
                if self.v11_reference_key(trajectory.get("behavior_policy_ref")) != self.v11_reference_key(behavior.get("policy_ref")) or self.v11_reference_key(trajectory.get("target_policy_ref")) != self.v11_reference_key(target.get("policy_ref")):
                    issues.append("every trajectory must bind the exact root behavior and target policy versions")
                steps = trajectory.get("steps", []) if isinstance(trajectory.get("steps"), list) else []
                if (
                    not isinstance(max_steps, int)
                    or len(steps) > max_steps
                    or (horizon.get("horizon_type") == "fixed" and len(steps) != max_steps)
                    or [step.get("step_index") for step in steps if isinstance(step, dict)] != list(range(len(steps)))
                ):
                    issues.append("trajectory steps must be contiguous and within the frozen horizon")
                started_at = parse_exact_utc(trajectory.get("started_at"))
                ended_at = parse_exact_utc(trajectory.get("ended_at"))
                step_times = [parse_exact_utc(step.get("observed_at")) for step in steps if isinstance(step, dict)]
                if None in [started_at, ended_at, *step_times] or not (started_at <= ended_at) or step_times != sorted(step_times) or any(not (started_at <= value <= ended_at) for value in step_times if value is not None):
                    issues.append("trajectory and step timestamps must be monotone and bounded by the trajectory window")
                terminal_values = [self.observed_v11_value(step.get("terminal")) for step in steps if isinstance(step, dict)]
                if terminal_values and (terminal_values[-1] is not True or any(value is True for value in terminal_values[:-1])):
                    issues.append("only the final trajectory step may carry the observed terminal disposition")
                for step in steps:
                    if not isinstance(step, dict):
                        continue
                    if step.get("action_id") not in action_members:
                        issues.append("every trajectory action must be an exact member of the frozen action space")
                    information_set = step.get("information_set") if isinstance(step.get("information_set"), dict) else {}
                    information_frozen = parse_exact_utc(information_set.get("frozen_at"))
                    step_observed = parse_exact_utc(step.get("observed_at"))
                    if information_frozen is None or step_observed is None or information_frozen > step_observed or information_set.get("post_freeze_additions_prohibited") is not True:
                        issues.append("every OPE step information set must be immutable and frozen no later than the action observation")
                    behavior_p = self.observed_v11_value(step.get("behavior_propensity"))
                    target_p = self.observed_v11_value(step.get("target_propensity"))
                    if not isinstance(behavior_p, (int, float)) or not 0 < float(behavior_p) <= 1 or not isinstance(target_p, (int, float)) or not 0 <= float(target_p) <= 1:
                        issues.append("every observed OPE step requires finite positive behavior and bounded target propensity")
                    else:
                        weights.append(float(target_p) / float(behavior_p))
            if len(trajectory_ids) != len(set(trajectory_ids)):
                issues.append("trajectory identifiers must be unique")
            support = document.get("support_assessment") if isinstance(document.get("support_assessment"), dict) else {}
            unsupported = self.observed_v11_value(support.get("unsupported_action_count"))
            unsupported_actions = support.get("unsupported_actions") if isinstance(support.get("unsupported_actions"), list) else []
            if (
                support.get("extrapolation_prohibited") is not True
                or not isinstance(unsupported, int)
                or isinstance(unsupported, bool)
                or unsupported != len(unsupported_actions)
                or any(not isinstance(action, str) for action in unsupported_actions)
                or len(unsupported_actions) != len(set(unsupported_actions))
                or any(action not in action_members for action in unsupported_actions)
            ):
                issues.append("support assessment must prohibit extrapolation and exactly enumerate distinct unsupported frozen actions")
            behavior_propensities = [
                self.observed_v11_value(step.get("behavior_propensity"))
                for trajectory in document.get("trajectories", [])
                if isinstance(trajectory, dict)
                for step in trajectory.get("steps", [])
                if isinstance(step, dict)
            ]
            numeric_behavior_propensities = [
                float(value)
                for value in behavior_propensities
                if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))
            ]
            minimum_behavior = self.observed_v11_value(support.get("minimum_behavior_propensity"))
            if behavior_propensities and (
                len(numeric_behavior_propensities) != len(behavior_propensities)
                or
                not isinstance(minimum_behavior, (int, float))
                or abs(float(minimum_behavior) - min(numeric_behavior_propensities)) > 1e-12
            ):
                issues.append("support assessment must report the exact minimum observed behavior propensity")
            weight_policy = document.get("importance_weight_policy") if isinstance(document.get("importance_weight_policy"), dict) else {}
            max_weight = self.observed_v11_value(weight_policy.get("maximum_observed_weight"))
            if weight_policy.get("zero_behavior_propensity_prohibited") is not True or (weights and (not isinstance(max_weight, (int, float)) or abs(float(max_weight) - max(weights)) > 1e-12)):
                issues.append("importance-weight policy must prohibit zero behavior propensity and report the exact maximum weight")
            ess = document.get("effective_sample_size") if isinstance(document.get("effective_sample_size"), dict) else {}
            ess_value = self.observed_v11_value(ess.get("value"))
            expected_ess = (sum(weights) ** 2 / sum(weight * weight for weight in weights)) if weights and sum(weight * weight for weight in weights) > 0 else None
            if ess.get("trajectory_count") != len(trajectory_ids) or not isinstance(ess_value, (int, float)) or expected_ess is None or abs(float(ess_value) - expected_ess) > 1e-12 or not 0 < float(ess_value) <= len(trajectory_ids):
                issues.append("effective sample size must equal the exact Kish reconstruction and remain bounded by trajectory count")
            reward_id = document.get("reward_definition", {}).get("signal_id") if isinstance(document.get("reward_definition"), dict) else None
            cost_ids = set(ids(document.get("cost_definitions"), "signal_id"))
            constraint_ids = set(ids(document.get("safety_constraints"), "constraint_id"))
            if len(cost_ids) != len(document.get("cost_definitions", [])) or len(constraint_ids) != len(document.get("safety_constraints", [])):
                issues.append("cost and safety-constraint identifiers must be unique")
            for constraint in document.get("safety_constraints", []):
                if isinstance(constraint, dict) and constraint.get("cost_signal_id") not in cost_ids:
                    issues.append("every safety constraint must bind one declared cost signal")
            for trajectory in document.get("trajectories", []):
                if not isinstance(trajectory, dict):
                    continue
                for step in trajectory.get("steps", []):
                    if not isinstance(step, dict):
                        continue
                    step_costs = ids(step.get("costs"), "cost_signal_id")
                    if len(step_costs) != len(set(step_costs)) or set(step_costs) != cost_ids:
                        issues.append("every trajectory step must report each frozen cost signal exactly once")
            for estimator in document.get("estimators", []):
                if not isinstance(estimator, dict):
                    continue
                if estimator.get("target_signal_id") not in {reward_id} | cost_ids:
                    issues.append("OPE estimator target signal must resolve to the frozen reward or cost definitions")
                observed_constraints = set(ids(estimator.get("safety_constraint_results"), "constraint_id"))
                if observed_constraints != constraint_ids:
                    issues.append("every OPE estimator must report every frozen safety constraint exactly once")
            estimator_ids = ids(document.get("estimators"), "estimator_id")
            if len(estimator_ids) != len(set(estimator_ids)):
                issues.append("OPE estimator identifiers must be unique")

        elif schema_id == "https://schemas.reiyah.invalid/scientific-contract/1.1.0/evaluation-assurance-bundle.schema.json":
            if document.get("mission_release_id") != V11_MISSION_RELEASE_ID:
                issues.append("assurance interface must bind the current mission release")
            if document.get("deployment_authorized") is not False or document.get("compliance_claimed") is not False:
                issues.append("assurance interface cannot authorize deployment or claim compliance")
            odd = document.get("odd_specification") if isinstance(document.get("odd_specification"), dict) else {}
            if not odd.get("exit_conditions") or not isinstance(odd.get("unknown_dimension_policy"), dict) or odd.get("outside_domain_policy", {}).get("continued_confident_operation_prohibited") is not True:
                issues.append("ODD requires explicit exit, unknown-dimension, and outside-domain contracts")
            dataset_ids: list[str] = []
            for dataset in document.get("dataset_governance", []):
                if not isinstance(dataset, dict):
                    continue
                dataset_ids.append(dataset.get("dataset_id"))
                if not dataset.get("sources") or not isinstance(dataset.get("ethics_review"), dict) or dataset.get("partition_leakage_prohibited") is not True:
                    issues.append("dataset governance requires source/consent authority, ethics disposition, and leakage prohibition")
                label_governance = dataset.get("label_governance") if isinstance(dataset.get("label_governance"), dict) else {}
                instruction_ref = label_governance.get("instruction_ref") if isinstance(label_governance.get("instruction_ref"), dict) else {}
                instruction_artifact = label_governance.get("instruction_artifact") if isinstance(label_governance.get("instruction_artifact"), dict) else {}
                if (
                    instruction_ref.get("availability_state") not in {"not_available_in_gate_a", "not_authorized_in_gate_a"}
                    or instruction_ref.get("expected_record_kind") != "label_instruction"
                    or instruction_ref.get("expected_version") != "1.1.0"
                    or instruction_artifact.get("availability_state") not in {"not_available_in_gate_a", "not_authorized_in_gate_a"}
                    or instruction_artifact.get("expected_artifact_kind") != "label_instruction"
                    or not isinstance(instruction_ref.get("expected_record_id"), str)
                    or not isinstance(instruction_artifact.get("expected_artifact_id"), str)
                ):
                    issues.append("label governance must preserve a typed unavailable instruction identity and matching unavailable artifact role")
                partitions = dataset.get("partitions", []) if isinstance(dataset.get("partitions"), list) else []
                partition_ids = ids(partitions, "partition_id")
                if len(partition_ids) != len(set(partition_ids)):
                    issues.append("dataset partitions must have unique identifiers")
                split_frozen = parse_exact_utc(dataset.get("split_frozen_at"))
                for partition in partitions:
                    available = timestamp(partition.get("available_from")) if isinstance(partition, dict) else None
                    if split_frozen is None or available is None or available < split_frozen:
                        issues.append("dataset partitions cannot become available before the frozen split")
            if len(dataset_ids) != len(set(dataset_ids)):
                issues.append("dataset identifiers must be unique")
            scenario_ids = ids(document.get("scenarios"), "scenario_id")
            test_ids = ids(document.get("test_cases"), "test_case_id")
            if len(scenario_ids) != len(set(scenario_ids)) or len(test_ids) != len(set(test_ids)):
                issues.append("scenario and test-case identifiers must be unique")
            for scenario in document.get("scenarios", []):
                if isinstance(scenario, dict) and (not scenario.get("unknowns") or not scenario.get("expected_outcomes")):
                    issues.append("every scenario must preserve explicit unknowns and expected outcomes")
            for test in document.get("test_cases", []):
                if not isinstance(test, dict):
                    continue
                scenario_key = self.v11_reference_key(test.get("scenario_ref"))
                if scenario_key is None or scenario_key[0] not in scenario_ids or not isinstance(test.get("oracle"), dict) or not test.get("abstention_criteria"):
                    issues.append("every test case must bind a declared scenario, typed oracle, and abstention contract")
                system_ref = test.get("system_ref") if isinstance(test.get("system_ref"), dict) else {}
                if test.get("system_version") != system_ref.get("version"):
                    issues.append("test-case system_version must equal the exact typed system actor version")
                criteria_sets = [
                    test.get(field, []) if isinstance(test.get(field), list) else []
                    for field in ("pass_criteria", "fail_criteria", "abstention_criteria")
                ]
                if any(len(values) != len(set(values)) for values in criteria_sets) or any(set(criteria_sets[left]) & set(criteria_sets[right]) for left, right in ((0, 1), (0, 2), (1, 2))):
                    issues.append("test pass, fail, and abstention criteria must be unique and pairwise disjoint")
            benchmark = document.get("benchmark_specification") if isinstance(document.get("benchmark_specification"), dict) else {}
            metric_ids = ids(benchmark.get("metrics"), "metric_id")
            primary = benchmark.get("primary_metric_id")
            primary_marked = [metric.get("metric_id") for metric in benchmark.get("metrics", []) if isinstance(metric, dict) and metric.get("primary") is True]
            if len(metric_ids) != len(set(metric_ids)) or primary_marked != [primary] or benchmark.get("post_hoc_relabeling_prohibited") is not True or benchmark.get("benchmark_status") != "proposed":
                issues.append("benchmark metric inventory, primary metric, freeze, and proposed status must be exact")
            safety = document.get("safety_case") if isinstance(document.get("safety_case"), dict) else {}
            claim_statuses = [claim.get("claim_status") for claim in safety.get("claims", []) if isinstance(claim, dict)]
            claim_ids = ids(safety.get("claims"), "claim_id")
            hazard_ids = ids(safety.get("hazards"), "hazard_id")
            if len(claim_ids) != len(set(claim_ids)) or len(hazard_ids) != len(set(hazard_ids)):
                issues.append("safety argument claim and hazard identifiers must be unique")
            for scenario in document.get("scenarios", []):
                if not isinstance(scenario, dict):
                    continue
                if any(hazard not in set(hazard_ids) for hazard in scenario.get("hazards", [])):
                    issues.append("scenario hazards must resolve to the static safety-argument hazard inventory")
                if self.v11_reference_key(scenario.get("odd_ref")) != (odd.get("odd_id"), "odd", odd.get("version")):
                    issues.append("every scenario must bind the exact declared ODD identity/version")
            for argument_link in safety.get("argument_links", []):
                if not isinstance(argument_link, dict) or argument_link.get("claim_id") not in set(claim_ids) or any(hazard not in set(hazard_ids) for hazard in argument_link.get("hazard_ids", [])):
                    issues.append("every safety argument link must resolve one declared claim and only declared hazards")
            if safety.get("safety_case_status") != "proposed" or safety.get("operator_acceptance_state") != "not_evaluated" or safety.get("compliance_claimed") is not False or any(status != "proposed" for status in claim_statuses):
                issues.append("static safety-argument interface, claims, compliance, and GA-17 must remain proposed/not-evaluated")

        if issues:
            return [
                make_diagnostic(
                    rule_id,
                    relative,
                    "Gate A 1.1 scientific-contract application is ineligible; violations=" + repr(sorted(set(issues))),
                    object_identifier(document),
                )
            ]
        return []

    def v11_mutation_diagnostics(self, fixture: dict[str, Any], relative: str) -> list[dict[str, Any]]:
        base_path = fixture.get("base_fixture_path")
        target_schema_id = fixture.get("target_schema_id")
        if not isinstance(base_path, str) or target_schema_id not in V11_APPLICATION_RULES:
            return [make_diagnostic("GA-FIXTURE-HANDLER", relative, "Scientific-contract mutation lacks a supported base path or target schema.", fixture.get("fixture_id"))]
        base = self.read_json_execution(base_path)
        if not isinstance(base, dict) or base.get("schema_id") != target_schema_id:
            return [make_diagnostic("GA-FIXTURE-HANDLER", relative, "Scientific-contract mutation base does not exactly bind target_schema_id.", fixture.get("fixture_id"))]
        mutated: Any = base
        try:
            for mutation in fixture.get("mutations", []):
                if not isinstance(mutation, dict):
                    raise ValueError("mutation is not an object")
                mutated = mutate_json(
                    mutated,
                    mutation.get("operation"),
                    mutation.get("json_pointer"),
                    mutation.get("value"),
                )
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            return [make_diagnostic("GA-FIXTURE-HANDLER", relative, f"Cannot apply scientific-contract production mutation: {exc}", fixture.get("fixture_id"))]
        overlay = {base_path: canonical_json_bytes(mutated)}
        diagnostics = self.v11_application_diagnostics(mutated, base_path, RepositoryView(self.root, overlay))
        target_schema = self.schemas.get(target_schema_id)
        if isinstance(target_schema, dict):
            validator = Draft202012Validator(target_schema, registry=self.registry, format_checker=self.format_checker)
            if any(error.validator == "required" for error in validator.iter_errors(mutated)):
                diagnostics.append(
                    make_diagnostic(
                        "GA-V11-REQUIRED-PROPERTY-SWEEP",
                        base_path,
                        "The production schema rejected a required-property removal from a valid v1.1 application.",
                        fixture.get("fixture_id"),
                    )
                )
        return diagnostics

    def operator_decision_contract_diagnostics(
        self,
        view: RepositoryView,
        end_to_end: bool = False,
        packet_version: str = "1.1.2",
    ) -> list[dict[str, Any]]:
        """Prove the versioned decision interface is satisfiable without creating authority."""

        spec = DECISION_PACKET_SPECS.get(packet_version)
        if spec is None:
            return [make_diagnostic("GA-OPERATOR-DECISION-CONTRACT", "schemas", f"Unsupported operator-decision packet version {packet_version!r}.")]
        schema_path = spec["schema_path"]
        template_path = spec["template_path"]
        schema = self.read_view_json(view, schema_path)
        template = self.read_view_json(view, template_path)
        ledger = self.read_view_json(view, "manifests/manifest-release-ledger.json")
        issues: list[str] = []
        if not isinstance(schema, dict) or not isinstance(template, dict) or not isinstance(ledger, dict):
            return [make_diagnostic("GA-OPERATOR-DECISION-CONTRACT", schema_path, "The versioned decision schema, template, or release ledger is absent or malformed.")]

        def at(document: Any, *keys: str) -> Any:
            current = document
            for key in keys:
                if not isinstance(current, dict):
                    return None
                current = current.get(key)
            return current

        expected_index = {
            "artifact_id": spec["index_artifact_id"],
            "path": INDEX_PATH,
            "schema_id": spec["index_schema_id"],
            "version": packet_version,
        }
        expected_report = {
            "artifact_id": spec["report_artifact_id"],
            "path": spec["report_path"],
            "schema_id": spec["report_schema_id"],
            "version": packet_version,
        }
        schema_expectations = {
            "schema $id": (schema.get("$id"), f"https://schemas.reiyah.invalid/gate-a/{packet_version}/operator-decision-record.schema.json"),
            "schema_id const": (at(schema, "properties", "schema_id", "const"), f"https://schemas.reiyah.invalid/gate-a/{packet_version}/operator-decision-record.schema.json"),
            "schema_version const": (at(schema, "properties", "schema_version", "const"), packet_version),
            "index artifact": (at(schema, "$defs", "indexBinding", "allOf",), None),
            "1.1 protocol schema": (at(schema, "$defs", "protocolReleaseBinding1_1", "properties", "artifact", "allOf"), None),
        }
        for label, (actual, expected) in schema_expectations.items():
            if expected is not None and actual != expected:
                issues.append(f"{label} is {actual!r}, expected {expected!r}")
        index_properties = at(schema, "$defs", "indexBinding", "allOf")
        report_properties = at(schema, "$defs", "validationReportBinding", "allOf")
        protocol_properties = at(schema, "$defs", "protocolReleaseBinding1_1", "properties", "artifact", "allOf")
        index_properties = index_properties[1].get("properties", {}) if isinstance(index_properties, list) and len(index_properties) > 1 and isinstance(index_properties[1], dict) else {}
        report_properties = report_properties[1].get("properties", {}) if isinstance(report_properties, list) and len(report_properties) > 1 and isinstance(report_properties[1], dict) else {}
        protocol_properties = protocol_properties[1].get("properties", {}) if isinstance(protocol_properties, list) and len(protocol_properties) > 1 and isinstance(protocol_properties[1], dict) else {}
        for field, expected in expected_index.items():
            if at(index_properties, field, "const") != expected:
                issues.append(f"decision schema index {field} does not bind {expected!r}")
        for field, expected in expected_report.items():
            if at(report_properties, field, "const") != expected:
                issues.append(f"decision schema report {field} does not bind {expected!r}")
        if at(protocol_properties, "schema_id", "const") != "https://schemas.reiyah.invalid/gate-a/1.1.0/protocol-manifest.schema.json":
            issues.append("the unchanged 1.1 protocol release is not typed by the exact 1.1 protocol-manifest schema")

        release_entries = ledger.get("entries") if isinstance(ledger.get("entries"), list) else []
        ledger_bindings = {
            entry.get("release_id"): entry.get("artifact_binding")
            for entry in release_entries
            if isinstance(entry, dict) and isinstance(entry.get("release_id"), str) and isinstance(entry.get("artifact_binding"), dict)
        }
        expected_release_ids = {
            "reiyah.mission@1.0.0",
            "reiyah.protocol.harbor-gate-a@1.0.0",
            V11_MISSION_RELEASE_ID,
            V11_PROTOCOL_RELEASE_ID,
        }
        if set(ledger_bindings) != expected_release_ids:
            issues.append(f"release ledger set is {sorted(ledger_bindings)}, expected {sorted(expected_release_ids)}")

        if (
            template.get("schema_id") != schema.get("$id")
            or template.get("schema_version") != packet_version
            or template.get("version") != packet_version
            or template.get("is_template") is not True
            or template.get("scientific_claims_accepted") is not False
            or not isinstance(template.get("template_notice"), str)
        ):
            issues.append(f"versioned template identity/non-authority fields do not match the {packet_version} decision contract")
        template_digest_placeholder = "sha256:REPLACE_WITH_64_LOWERCASE_HEX_DIGEST"
        template_index = template.get("architecture_completeness_binding") if isinstance(template.get("architecture_completeness_binding"), dict) else {}
        template_report = template.get("validation_report_binding") if isinstance(template.get("validation_report_binding"), dict) else {}
        template_artifact_bindings = template.get("artifact_bindings") if isinstance(template.get("artifact_bindings"), list) else []
        if template_artifact_bindings != [template_index]:
            issues.append("template artifact_bindings must contain exactly the same single current-index reference as architecture_completeness_binding")
        if template_index.get("sha256") != template_digest_placeholder or template_report.get("sha256") != template_digest_placeholder:
            issues.append("template current-index and report digest slots must retain the exact recognizable replacement placeholder")
        for field, expected in expected_index.items():
            if template_index.get(field) != expected:
                issues.append(f"template index {field} does not bind {expected!r}")
        for field, expected in expected_report.items():
            if template_report.get(field) != expected:
                issues.append(f"template report {field} does not bind {expected!r}")
        template_release_items = template.get("manifest_release_bindings") if isinstance(template.get("manifest_release_bindings"), list) else []
        template_release_order = [item.get("release_id") for item in template_release_items if isinstance(item, dict)]
        ledger_release_order = [
            entry.get("release_id")
            for entry in release_entries
            if isinstance(entry, dict) and isinstance(entry.get("release_id"), str)
        ]
        if template_release_order != ledger_release_order or len(template_release_items) != len(expected_release_ids):
            issues.append("template manifest_release_bindings must preserve the exact four-entry release-ledger order without duplicates")
        template_releases = {
            item.get("release_id"): item.get("artifact")
            for item in template_release_items
            if isinstance(item, dict) and isinstance(item.get("artifact"), dict)
        }
        if set(template_releases) != expected_release_ids:
            issues.append("template does not bind exactly the immutable four-release ledger set")
        for release_id, ledger_binding in ledger_bindings.items():
            template_binding = template_releases.get(release_id)
            for field in ("artifact_id", "path", "schema_id", "version"):
                if not isinstance(template_binding, dict) or template_binding.get(field) != ledger_binding.get(field):
                    issues.append(f"template {release_id} {field} does not equal the release ledger")
            if not isinstance(template_binding, dict) or template_binding.get("sha256") != template_digest_placeholder:
                issues.append(f"template {release_id} digest slot does not retain the exact recognizable replacement placeholder")

        digest = "sha256:" + ("a" * 64)
        index_reference = {**expected_index, "sha256": digest}
        report_reference = {**expected_report, "sha256": digest}
        synthetic = {
            "schema_id": schema.get("$id"),
            "schema_version": packet_version,
            "artifact_id": f"reiyah.synthetic.operator-decision-contract-{packet_version}",
            "record_id": f"reiyah.synthetic.operator-decision-contract-{packet_version}",
            "version": packet_version,
            "record_kind": "operator_gate_decision",
            "is_template": False,
            "gate_id": "reiyah.gate-a",
            "decision": "deferred",
            "operator_identity": "operator.synthetic-governance-contract",
            "authority_basis": "Synthetic schema satisfiability test only; it authenticates no operator and creates no authority.",
            "decided_at": "2026-08-24T00:00:00Z",
            "rationale": "Synthetic deferred record used only to prove the static decision schema is satisfiable against exact packet and release identities; it is never retained as an operator decision.",
            "risk_acknowledgements": template.get("risk_acknowledgements"),
            "artifact_bindings": [index_reference],
            "manifest_release_bindings": [
                {"release_id": release_id, "artifact": binding}
                for release_id, binding in ledger_bindings.items()
            ],
            "architecture_completeness_binding": index_reference,
            "validation_report_binding": report_reference,
            "scientific_claims_accepted": False,
            "decision_sequence": 1,
            "history_policy": "append_only_linear",
            "supersedes_record_id": None,
            "supersedes_record_sha256": None,
        }
        try:
            validator = Draft202012Validator(schema, registry=self.registry, format_checker=self.format_checker)
            schema_errors = sorted(validator.iter_errors(synthetic), key=lambda error: (list(error.absolute_path), error.message))
        except Exception as exc:  # pragma: no cover - converted to deterministic contract failure
            schema_errors = []
            issues.append(f"synthetic satisfiability evaluation failed: {exc}")
        if schema_errors:
            rendered = [f"/{'/'.join(str(part) for part in error.absolute_path)}: {error.message}" for error in schema_errors]
            issues.append(f"synthetic deferred non-authoritative record is not schema-satisfiable: {rendered}")
        template_only_overlay = dict(view.overlay)
        for candidate in view.iter_files():
            if (
                re.fullmatch(r"gate/decisions/[^/]+\.json", candidate)
                and candidate not in {LEGACY_TEMPLATE_PATH, V111_TEMPLATE_PATH, TEMPLATE_PATH}
            ):
                template_only_overlay[candidate] = None
        template_scan_diagnostics = self.actual_decision_diagnostics(RepositoryView(self.root, template_only_overlay))
        if template_scan_diagnostics:
            issues.append("the shared actual-decision discovery path misclassifies one of the three exact immutable templates")
        if end_to_end:
            current_index_raw: bytes | None
            current_report_raw: bytes | None
            try:
                current_index_raw = view.read_bytes(spec["index_physical_path"])
            except (OSError, ValueError):
                current_index_raw = None
            try:
                current_report_raw = view.read_bytes(spec["report_path"])
            except (OSError, ValueError):
                current_report_raw = None

            # The canonical report is produced by stdout redirection after validation,
            # so an absent or zero-byte output is an expected generation window. Once
            # both current artifacts contain bytes, require the shared exact replay path.
            if current_index_raw and current_report_raw:
                try:
                    current_index = strict_json_loads(current_index_raw.decode("utf-8"))
                    current_report = strict_json_loads(current_report_raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError, StrictJSONError, ValueError) as exc:
                    current_index = None
                    current_report = None
                    issues.append(f"current {packet_version} index/report cannot support end-to-end decision replay: {exc}")
                if (
                    not isinstance(current_index, dict)
                    or current_index.get("schema_id") != expected_index["schema_id"]
                    or current_index.get("artifact_id") != expected_index["artifact_id"]
                    or current_index.get("version") != expected_index["version"]
                ):
                    issues.append(f"current root evidence index is not the exact {packet_version} packet identity")
                if (
                    not isinstance(current_report, dict)
                    or current_report.get("schema_id") != expected_report["schema_id"]
                    or current_report.get("artifact_id") != expected_report["artifact_id"]
                    or current_report.get("version") != expected_report["version"]
                ):
                    issues.append(f"current validation report is not the exact {packet_version} packet identity")
            else:
                current_index = None
                current_report = None

            if current_index_raw and current_report_raw and isinstance(current_index, dict) and isinstance(current_report, dict):
                replay_index_reference = {**expected_index, "sha256": digest_bytes(current_index_raw)}
                replay_report_reference = {**expected_report, "sha256": digest_bytes(current_report_raw)}
                replay_record = dict(synthetic)
                replay_record["artifact_bindings"] = [replay_index_reference]
                replay_record["architecture_completeness_binding"] = replay_index_reference
                replay_record["validation_report_binding"] = replay_report_reference
                replay_overlay = dict(view.overlay)
                for candidate in view.iter_files():
                    if (
                        re.fullmatch(r"gate/decisions/[^/]+\.json", candidate)
                        and candidate not in {LEGACY_TEMPLATE_PATH, V111_TEMPLATE_PATH, TEMPLATE_PATH}
                    ):
                        replay_overlay[candidate] = None
                replay_path = "gate/decisions/reiyah.gate-a-decision-synthetic-contract.json"
                replay_overlay[replay_path] = canonical_json_bytes(replay_record)
                replay_diagnostics = self.actual_decision_diagnostics(RepositoryView(self.root, replay_overlay))
                if replay_diagnostics:
                    issues.append(
                        "synthetic exact-digest decision fails the shared actual-decision replay path: "
                        + repr(sorted({item.get("rule_id") for item in replay_diagnostics}))
                    )
        if issues:
            return [
                make_diagnostic(
                    "GA-OPERATOR-DECISION-CONTRACT",
                    schema_path,
                    f"Gate A {packet_version} operator-decision schema/template/release/index/report contract is inconsistent; "
                    f"violations={sorted(set(issues))}.",
                )
            ]
        return []

    def public_distribution_receipt_contract_diagnostics(
        self,
        view: RepositoryView,
        variant: str,
        receipt_sequence: int = 2,
    ) -> list[dict[str, Any]]:
        """Exercise a versioned receipt path without retaining a publication event."""

        if receipt_sequence == 3:
            return self.public_distribution_receipt_v112_contract_diagnostics(view, variant)
        if receipt_sequence != 2:
            return [
                make_diagnostic(
                    "GA-PUBLIC-DISTRIBUTION-RECEIPT",
                    "schemas/public-distribution-receipt-1.1.2.schema.json",
                    f"Unsupported synthetic receipt sequence {receipt_sequence!r}.",
                )
            ]
        if variant == "current":
            # Sequence two is no longer hypothetical. Replay the exact retained event
            # so its known-good fixture cannot silently substitute regenerated bytes.
            return self.public_custody_diagnostics(view)

        def failure(message: str) -> list[dict[str, Any]]:
            return [
                make_diagnostic(
                    "GA-PUBLIC-DISTRIBUTION-RECEIPT",
                    "schemas/public-distribution-receipt-1.1.1.schema.json",
                    message,
                )
            ]

        def clone_json(value: Any) -> Any:
            return strict_json_loads(canonical_json_bytes(value).decode("utf-8"))

        old_rights = self.read_view_json(view, PUBLIC_RIGHTS_REVALIDATION_PATH)
        initial_receipt = self.read_view_json(view, INITIAL_PUBLIC_RECEIPT_PATH)
        predecessor_index = self.read_view_json(view, HISTORICAL_V11_INDEX_PATH)
        predecessor_report = self.read_view_json(view, HISTORICAL_V11_REPORT_PATH)
        if not all(isinstance(item, dict) for item in (old_rights, initial_receipt, predecessor_index, predecessor_report)):
            return failure("Synthetic successor feasibility requires the exact retained 1.1.0 rights, receipt, index, and report objects.")

        try:
            old_rights_raw = view.read_bytes(PUBLIC_RIGHTS_REVALIDATION_PATH)
            initial_receipt_raw = view.read_bytes(INITIAL_PUBLIC_RECEIPT_PATH)
        except (OSError, ValueError):
            return failure("Synthetic successor feasibility cannot read immutable predecessor rights/receipt bytes.")

        synthetic_index = clone_json(predecessor_index)
        synthetic_index.update(
            {
                "schema_id": "https://schemas.reiyah.invalid/gate-a/1.1.1/gate-a-index.schema.json",
                "schema_version": "1.1.1",
                "artifact_id": "reiyah.artifact.gate-a-index-1.1.1",
                "version": "1.1.1",
                "as_of_date": "2026-08-24",
                "prior_candidate_observation": {
                    "artifact_id": "reiyah.artifact.gate-a-index-1.1.0",
                    "version": "1.1.0",
                    "sha256": HISTORICAL_V11_INDEX_DIGEST,
                    "observed_on": "2026-08-23",
                    "distribution_state": "public_packet_published_receipt_bound",
                    "evidence_eligible": False,
                },
            }
        )
        synthetic_index_raw = canonical_json_bytes(synthetic_index)

        synthetic_report = clone_json(predecessor_report)
        synthetic_report.update(
            {
                "schema_id": "https://schemas.reiyah.invalid/gate-a/1.1.1/validation-report.schema.json",
                "schema_version": "1.1.1",
                "artifact_id": "reiyah.validation-report.gate-a-1.1.1",
                "version": "1.1.1",
                "validation_plan_id": "reiyah.validation-plan.gate-a-public-1.1.1",
                "index_binding": {
                    "path": INDEX_PATH,
                    "sha256": digest_bytes(synthetic_index_raw),
                },
            }
        )
        synthetic_report_raw = canonical_json_bytes(synthetic_report)

        synthetic_rights = clone_json(old_rights)
        synthetic_rights.update(
            {
                "schema_id": "https://schemas.reiyah.invalid/gate-a/1.1.1/public-rights-revalidation.schema.json",
                "schema_version": "1.1.1",
                "artifact_id": "reiyah.artifact.public-rights-revalidation-2026-08-24",
                "observation_id": "reiyah.public-rights-revalidation.governance-correction-publication",
                "version": "1.1.1",
                "observed_at": "2026-08-24T10:00:00Z",
                "prior_observation_ref": {
                    "artifact_id": old_rights.get("artifact_id"),
                    "version": old_rights.get("version"),
                    "path": PUBLIC_RIGHTS_REVALIDATION_PATH,
                    "sha256": digest_bytes(old_rights_raw),
                    "byte_size": len(old_rights_raw),
                },
            }
        )
        for observation in synthetic_rights.get("basis_observations", []):
            if isinstance(observation, dict):
                observation["observed_at"] = synthetic_rights["observed_at"]
        synthetic_rights_raw = canonical_json_bytes(synthetic_rights)

        expected_successor_authorization = {
            "basis_state": "observed_current_operator_instruction",
            "recorded_date": "2026-08-24",
            "authorized_action": "publish_exact_static_gate_a_1.1.1_governance_correction",
            "scope_limit": "Exact static Gate A 1.1.1 governance-correction packet and the unchanged four eligible retained payloads; no new evidence, private data, runtime, deployment, or unauthorized source payloads.",
            "operator_identity_authentication": "not_evaluated",
            "ga17_effect": "not_evaluated",
            "gate_a_acceptance_effect": "none",
            "scientific_publication_acceptance_effect": "none",
            "runtime_execution_effect": "none",
        }
        synthetic_receipt = clone_json(initial_receipt)
        synthetic_receipt.update(
            {
                "schema_id": "https://schemas.reiyah.invalid/gate-a/1.1.1/public-distribution-receipt.schema.json",
                "schema_version": "1.1.1",
                "artifact_id": "reiyah.artifact.public-distribution-receipt-1.1.1",
                "receipt_id": "reiyah.public-distribution-receipt.governance-correction-publication",
                "version": "1.1.1",
                "recorded_at": "2026-08-24T10:05:20Z",
                "published_at": "2026-08-24T10:05:00Z",
                "published_git_commit": "b" * 40,
                "receipt_sequence": 2,
                "prior_receipt_ref": {
                    "artifact_id": initial_receipt.get("artifact_id"),
                    "version": initial_receipt.get("version"),
                    "path": INITIAL_PUBLIC_RECEIPT_PATH,
                    "sha256": digest_bytes(initial_receipt_raw),
                    "byte_size": len(initial_receipt_raw),
                },
                "rights_revalidation_ref": {
                    "artifact_id": synthetic_rights.get("artifact_id"),
                    "version": synthetic_rights.get("version"),
                    "path": SUCCESSOR_PUBLIC_RIGHTS_REVALIDATION_PATH,
                    "sha256": digest_bytes(synthetic_rights_raw),
                    "byte_size": len(synthetic_rights_raw),
                },
                "published_index_ref": {
                    "artifact_id": synthetic_index.get("artifact_id"),
                    "version": synthetic_index.get("version"),
                    "path": INDEX_PATH,
                    "sha256": digest_bytes(synthetic_index_raw),
                    "byte_size": len(synthetic_index_raw),
                },
                "validation_report_ref": {
                    "artifact_id": synthetic_report.get("artifact_id"),
                    "version": synthetic_report.get("version"),
                    "path": REPORT_PATH,
                    "sha256": digest_bytes(synthetic_report_raw),
                    "byte_size": len(synthetic_report_raw),
                },
                "rights_observation_age_seconds": 300,
                "distribution_authorization": expected_successor_authorization,
                "remote_readback": {
                    **synthetic_receipt.get("remote_readback", {}),
                    "verified_at": "2026-08-24T10:05:10Z",
                    "tree_contains_exact_validation_report": True,
                },
            }
        )

        if variant == "legacy_authorization_reuse":
            synthetic_receipt["schema_id"] = "https://schemas.reiyah.invalid/gate-a/1.1.0/public-distribution-receipt.schema.json"
            synthetic_receipt["schema_version"] = "1.1.0"
            synthetic_receipt["version"] = "1.1.0"
            synthetic_receipt["distribution_authorization"] = clone_json(initial_receipt.get("distribution_authorization"))
            synthetic_receipt.pop("validation_report_ref", None)
        elif variant == "missing_validation_report_binding":
            synthetic_receipt.pop("validation_report_ref", None)
        elif variant == "missing_validation_report_readback":
            synthetic_receipt["remote_readback"].pop("tree_contains_exact_validation_report", None)
        elif variant == "stale_index_binding":
            synthetic_receipt["published_index_ref"] = {
                "artifact_id": "reiyah.artifact.gate-a-index-1.1.0",
                "version": "1.1.0",
                "path": INDEX_PATH,
                "sha256": HISTORICAL_V11_INDEX_DIGEST,
                "byte_size": len(canonical_json_bytes(predecessor_index)),
            }
        elif variant == "stale_rights_binding":
            synthetic_receipt["rights_revalidation_ref"]["sha256"] = "sha256:" + ("c" * 64)
        elif variant == "stale_report_binding":
            synthetic_receipt["validation_report_ref"]["sha256"] = "sha256:" + ("c" * 64)
        elif variant == "stale_prior_receipt_binding":
            synthetic_receipt["prior_receipt_ref"]["sha256"] = "sha256:" + ("c" * 64)
        elif variant == "stale_custody_binding":
            synthetic_receipt["custody_profile_ref"]["sha256"] = "sha256:" + ("c" * 64)
        elif variant == "chronology_mismatch":
            synthetic_receipt["published_at"] = "2026-08-24T09:59:59Z"
            synthetic_receipt["rights_observation_age_seconds"] = 0
        elif variant == "rights_chronology_mismatch":
            synthetic_rights["observed_at"] = "2026-08-22T10:00:00Z"
            for observation in synthetic_rights.get("basis_observations", []):
                if isinstance(observation, dict):
                    observation["observed_at"] = synthetic_rights["observed_at"]
            synthetic_rights_raw = canonical_json_bytes(synthetic_rights)
            synthetic_receipt["rights_revalidation_ref"]["sha256"] = digest_bytes(synthetic_rights_raw)
            synthetic_receipt["rights_revalidation_ref"]["byte_size"] = len(synthetic_rights_raw)
        elif variant == "same_commit_reuse":
            synthetic_receipt["published_git_commit"] = initial_receipt.get("published_git_commit")
        elif variant != "current":
            return failure(f"Unknown synthetic successor receipt variant {variant!r}.")

        synthetic_receipt_path = "gate/public-distribution-receipts/reiyah.public-distribution-receipt-1.1.1.json"
        overlay = dict(view.overlay)
        overlay[INDEX_PATH] = synthetic_index_raw
        overlay[REPORT_PATH] = synthetic_report_raw
        overlay[SUCCESSOR_PUBLIC_RIGHTS_REVALIDATION_PATH] = synthetic_rights_raw
        overlay[synthetic_receipt_path] = canonical_json_bytes(synthetic_receipt)
        synthetic_view = RepositoryView(self.root, overlay)
        diagnostics = self.public_custody_diagnostics(synthetic_view)
        if variant == "current":
            diagnostics.extend(self.instance_diagnostics(synthetic_index, INDEX_PATH))
            diagnostics.extend(self.instance_diagnostics(synthetic_report, REPORT_PATH))
        return sorted(diagnostics, key=diagnostic_key)

    def public_distribution_receipt_v112_contract_diagnostics(
        self,
        view: RepositoryView,
        variant: str,
    ) -> list[dict[str, Any]]:
        """Exercise an unpublished sequence-three event in an isolated overlay."""

        schema_path = "schemas/public-distribution-receipt-1.1.2.schema.json"

        def failure(message: str) -> list[dict[str, Any]]:
            return [make_diagnostic("GA-PUBLIC-DISTRIBUTION-RECEIPT", schema_path, message)]

        def clone_json(value: Any) -> Any:
            return strict_json_loads(canonical_json_bytes(value).decode("utf-8"))

        prior_rights = self.read_view_json(view, SUCCESSOR_PUBLIC_RIGHTS_REVALIDATION_PATH)
        prior_receipt = self.read_view_json(view, SUCCESSOR_PUBLIC_RECEIPT_PATH)
        prior_index = self.read_view_json(view, HISTORICAL_V111_INDEX_PATH)
        prior_report = self.read_view_json(view, HISTORICAL_V111_REPORT_PATH)
        if not all(isinstance(item, dict) for item in (prior_rights, prior_receipt, prior_index, prior_report)):
            return failure("Synthetic sequence-three feasibility requires the exact retained 1.1.1 rights, receipt, index, and report objects.")
        try:
            prior_rights_raw = view.read_bytes(SUCCESSOR_PUBLIC_RIGHTS_REVALIDATION_PATH)
            prior_receipt_raw = view.read_bytes(SUCCESSOR_PUBLIC_RECEIPT_PATH)
        except (OSError, ValueError):
            return failure("Synthetic sequence-three feasibility cannot read immutable 1.1.1 rights and receipt bytes.")
        if (
            digest_bytes(prior_rights_raw) != SUCCESSOR_PUBLIC_RIGHTS_REVALIDATION_DIGEST
            or len(prior_rights_raw) != SUCCESSOR_PUBLIC_RIGHTS_REVALIDATION_SIZE
            or digest_bytes(prior_receipt_raw) != SUCCESSOR_PUBLIC_RECEIPT_DIGEST
            or len(prior_receipt_raw) != SUCCESSOR_PUBLIC_RECEIPT_SIZE
        ):
            return failure("Synthetic sequence-three feasibility refuses non-canonical 1.1.1 predecessor bytes.")

        synthetic_index = clone_json(prior_index)
        synthetic_index.update(
            {
                "schema_id": "https://schemas.reiyah.invalid/gate-a/1.1.2/gate-a-index.schema.json",
                "schema_version": "1.1.2",
                "artifact_id": "reiyah.artifact.gate-a-index-1.1.2",
                "version": "1.1.2",
                "as_of_date": "2026-08-24",
                "prior_candidate_observation": {
                    "artifact_id": "reiyah.artifact.gate-a-index-1.1.1",
                    "version": "1.1.1",
                    "sha256": HISTORICAL_V111_INDEX_DIGEST,
                    "observed_on": "2026-08-24",
                    "distribution_state": "public_packet_published_receipt_bound",
                    "evidence_eligible": False,
                },
            }
        )
        synthetic_index_raw = canonical_json_bytes(synthetic_index)

        synthetic_report = clone_json(prior_report)
        synthetic_report.update(
            {
                "schema_id": "https://schemas.reiyah.invalid/gate-a/1.1.2/validation-report.schema.json",
                "schema_version": "1.1.2",
                "artifact_id": "reiyah.validation-report.gate-a-1.1.2",
                "version": "1.1.2",
                "validation_plan_id": "reiyah.validation-plan.gate-a-public-1.1.2",
                "index_binding": {
                    "path": INDEX_PATH,
                    "sha256": digest_bytes(synthetic_index_raw),
                },
            }
        )
        synthetic_report_raw = canonical_json_bytes(synthetic_report)

        synthetic_rights = clone_json(prior_rights)
        synthetic_rights.update(
            {
                "schema_id": "https://schemas.reiyah.invalid/gate-a/1.1.2/public-rights-revalidation.schema.json",
                "schema_version": "1.1.2",
                "artifact_id": "reiyah.artifact.public-rights-revalidation-2026-08-24-1.1.2",
                "observation_id": "reiyah.public-rights-revalidation.documentation-continuity-publication",
                "version": "1.1.2",
                "observed_at": "2026-08-24T10:00:00Z",
                "prior_observation_ref": {
                    "artifact_id": prior_rights.get("artifact_id"),
                    "version": prior_rights.get("version"),
                    "path": SUCCESSOR_PUBLIC_RIGHTS_REVALIDATION_PATH,
                    "sha256": digest_bytes(prior_rights_raw),
                    "byte_size": len(prior_rights_raw),
                },
            }
        )
        for observation in synthetic_rights.get("basis_observations", []):
            if isinstance(observation, dict):
                observation["observed_at"] = synthetic_rights["observed_at"]
        synthetic_rights_raw = canonical_json_bytes(synthetic_rights)

        synthetic_receipt = clone_json(prior_receipt)
        synthetic_receipt.update(
            {
                "schema_id": "https://schemas.reiyah.invalid/gate-a/1.1.2/public-distribution-receipt.schema.json",
                "schema_version": "1.1.2",
                "artifact_id": "reiyah.artifact.public-distribution-receipt-1.1.2",
                "receipt_id": "reiyah.public-distribution-receipt.documentation-continuity-publication",
                "version": "1.1.2",
                "recorded_at": "2026-08-24T10:05:20Z",
                "published_at": "2026-08-24T10:05:00Z",
                "published_git_commit": "c" * 40,
                "receipt_sequence": 3,
                "prior_receipt_ref": {
                    "artifact_id": prior_receipt.get("artifact_id"),
                    "version": prior_receipt.get("version"),
                    "path": SUCCESSOR_PUBLIC_RECEIPT_PATH,
                    "sha256": digest_bytes(prior_receipt_raw),
                    "byte_size": len(prior_receipt_raw),
                },
                "rights_revalidation_ref": {
                    "artifact_id": synthetic_rights.get("artifact_id"),
                    "version": synthetic_rights.get("version"),
                    "path": CURRENT_PUBLIC_RIGHTS_REVALIDATION_PATH,
                    "sha256": digest_bytes(synthetic_rights_raw),
                    "byte_size": len(synthetic_rights_raw),
                },
                "published_index_ref": {
                    "artifact_id": synthetic_index.get("artifact_id"),
                    "version": synthetic_index.get("version"),
                    "path": INDEX_PATH,
                    "sha256": digest_bytes(synthetic_index_raw),
                    "byte_size": len(synthetic_index_raw),
                },
                "validation_report_ref": {
                    "artifact_id": synthetic_report.get("artifact_id"),
                    "version": synthetic_report.get("version"),
                    "path": REPORT_PATH,
                    "sha256": digest_bytes(synthetic_report_raw),
                    "byte_size": len(synthetic_report_raw),
                },
                "rights_observation_age_seconds": 300,
                "distribution_authorization": {
                    "basis_state": "observed_current_operator_instruction",
                    "recorded_date": "2026-08-24",
                    "authorized_action": "publish_exact_static_gate_a_1.1.2_documentation_continuity_successor",
                    "scope_limit": "Exact static Gate A 1.1.2 documentation-and-continuity successor packet and the unchanged four eligible retained payloads; no new scientific evidence, private data, runtime, deployment, or unauthorized source payloads.",
                    "operator_identity_authentication": "not_evaluated",
                    "ga17_effect": "not_evaluated",
                    "gate_a_acceptance_effect": "none",
                    "scientific_publication_acceptance_effect": "none",
                    "runtime_execution_effect": "none",
                },
                "remote_readback": {
                    **synthetic_receipt.get("remote_readback", {}),
                    "verified_at": "2026-08-24T10:05:10Z",
                    "tree_contains_exact_validation_report": True,
                },
            }
        )

        if variant == "legacy_authorization_reuse":
            synthetic_receipt["schema_id"] = "https://schemas.reiyah.invalid/gate-a/1.1.1/public-distribution-receipt.schema.json"
            synthetic_receipt["schema_version"] = "1.1.1"
            synthetic_receipt["version"] = "1.1.1"
            synthetic_receipt["distribution_authorization"] = clone_json(prior_receipt.get("distribution_authorization"))
        elif variant == "missing_validation_report_binding":
            synthetic_receipt.pop("validation_report_ref", None)
        elif variant == "missing_validation_report_readback":
            synthetic_receipt["remote_readback"].pop("tree_contains_exact_validation_report", None)
        elif variant == "stale_index_binding":
            synthetic_receipt["published_index_ref"]["sha256"] = "sha256:" + ("d" * 64)
        elif variant == "stale_rights_binding":
            synthetic_receipt["rights_revalidation_ref"]["sha256"] = "sha256:" + ("d" * 64)
        elif variant == "stale_report_binding":
            synthetic_receipt["validation_report_ref"]["sha256"] = "sha256:" + ("d" * 64)
        elif variant == "stale_prior_receipt_binding":
            synthetic_receipt["prior_receipt_ref"]["sha256"] = "sha256:" + ("d" * 64)
        elif variant == "stale_custody_binding":
            synthetic_receipt["custody_profile_ref"]["sha256"] = "sha256:" + ("d" * 64)
        elif variant == "same_commit_reuse":
            synthetic_receipt["published_git_commit"] = prior_receipt.get("published_git_commit")
        elif variant == "chronology_mismatch":
            synthetic_receipt["published_at"] = "2026-08-24T09:59:59Z"
            synthetic_receipt["rights_observation_age_seconds"] = 0
        elif variant == "rights_chronology_mismatch":
            synthetic_rights["observed_at"] = "2026-08-24T07:00:00Z"
            for observation in synthetic_rights.get("basis_observations", []):
                if isinstance(observation, dict):
                    observation["observed_at"] = synthetic_rights["observed_at"]
            synthetic_rights_raw = canonical_json_bytes(synthetic_rights)
            synthetic_receipt["rights_revalidation_ref"]["sha256"] = digest_bytes(synthetic_rights_raw)
            synthetic_receipt["rights_revalidation_ref"]["byte_size"] = len(synthetic_rights_raw)
        elif variant != "current":
            return failure(f"Unknown synthetic sequence-three receipt variant {variant!r}.")

        receipt_path = "gate/public-distribution-receipts/reiyah.public-distribution-receipt-1.1.2.json"
        overlay = dict(view.overlay)
        overlay[INDEX_PATH] = synthetic_index_raw
        overlay[REPORT_PATH] = synthetic_report_raw
        overlay[CURRENT_PUBLIC_RIGHTS_REVALIDATION_PATH] = synthetic_rights_raw
        overlay[receipt_path] = canonical_json_bytes(synthetic_receipt)
        return self.public_custody_diagnostics(RepositoryView(self.root, overlay))

    def fixture_case_diagnostics(self, case: dict[str, Any], case_path: str) -> list[dict[str, Any]]:
        payload = case.get("payload", {})
        if not isinstance(payload, dict):
            return [make_diagnostic("GA-FIXTURE-HANDLER", case_path, "Fixture payload is not an object.", case.get("fixture_id"))]
        kind = payload.get("kind")
        fixture_id = case.get("fixture_id") if isinstance(case.get("fixture_id"), str) else None
        if case.get("classification") == "known_bad" and kind not in {"production_mutation", "identity", "production_identity", "public_distribution_receipt_contract"}:
            return [make_diagnostic("GA-FIXTURE-HANDLER", case_path, "Known-bad fixtures must invoke a production RepositoryView diagnostic or the exact shared identity preflight.", fixture_id)]
        if kind == "production_mutation":
            mutations = payload.get("mutations")
            if fixture_id == "reiyah.fixture.bad.excluded-canonical-report-private-bytes":
                expected_legacy_mutation = {
                    "operation": "add_file",
                    "path": HISTORICAL_V11_REPORT_PATH,
                    "content_utf8": '#!/usr/bin/env python3\nopen("gate/pwned.json", "w").write("{}")\n',
                }
                if (
                    case_path != "fixtures/bad/excluded-canonical-report-private-bytes.json"
                    or payload.get("production_check") != "repository_inventory"
                    or mutations != [expected_legacy_mutation]
                ):
                    return [make_diagnostic("GA-FIXTURE-HANDLER", case_path, "The immutable legacy canonical-report intrusion fixture no longer has its exact released shape.", fixture_id)]
                mutations = [{**expected_legacy_mutation, "path": REPORT_PATH}]
            try:
                view = self.mutation_view(mutations)
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                return [make_diagnostic("GA-FIXTURE-HANDLER", case_path, f"Cannot construct production mutation view: {exc}", fixture_id)]
            production_check = payload.get("production_check")
            if production_check == "repository_inventory":
                return self.repository_inventory_diagnostics(view)
            if production_check == "scope_inventory":
                return self.scope_inventory_diagnostics(view)
            if production_check == "normative_measurements":
                return self.normative_measurement_diagnostics(view)
            if production_check == "sources_crosswalk":
                return self.sources_crosswalk_diagnostics(view)
            if production_check == "narrative_bindings":
                return self.narrative_bindings_diagnostics(view)
            if production_check == "manifest_releases":
                return self.manifest_release_diagnostics(view)
            if production_check == "research_registry":
                return self.research_function_registry_diagnostics(view)
            if production_check == "public_custody":
                return self.public_custody_diagnostics(view)
            if production_check == "historical_recovery":
                return self.historical_recovery_diagnostics(view)
            if production_check == "scientific_contract_profile":
                return self.scientific_contract_profile_diagnostics(view)
            if production_check == "operator_decision_contract":
                mutation_paths = {
                    item.get("path")
                    for item in payload.get("mutations", [])
                    if isinstance(item, dict) and isinstance(item.get("path"), str)
                }
                packet_version = "1.1.1" if any("1.1.1" in path for path in mutation_paths) else "1.1.2"
                return self.operator_decision_contract_diagnostics(view, packet_version=packet_version)
            if production_check == "predecessor_packet":
                return self.predecessor_packet_drift_diagnostics(view)
            if production_check == "evidence_index":
                return self.index_canonical_diagnostics(view)
            if production_check == "decision_history":
                records: list[tuple[str, dict[str, Any]]] = []
                for relative in view.iter_files():
                    if not relative.startswith("gate/decisions/reiyah.gate-a-decision-") or not relative.endswith(".json"):
                        continue
                    record = self.read_view_json(view, relative)
                    if isinstance(record, dict):
                        records.append((relative, record))
                return self.decision_history_diagnostics(records, view)
            if production_check == "validation_report":
                mutation_paths = [
                    item.get("path")
                    for item in payload.get("mutations", [])
                    if isinstance(item, dict) and isinstance(item.get("path"), str)
                ]
                relative = next(
                    (path for path in mutation_paths if path.startswith("gate/validation-reports/") and path.endswith(".json")),
                    REPORT_PATH,
                )
                return self.validation_report_coverage_diagnostics(self.read_view_json(view, relative), relative)
            if production_check == "scientific_semantics":
                return self.scientific_semantics_diagnostics(view)
            if production_check == "mission_boundary":
                return self.mission_boundary_diagnostics(view)
            if production_check == "claim_register":
                return self.claim_register_diagnostics(view)
            if production_check == "threat_coverage":
                return self.threat_coverage_diagnostics(view)
            if production_check == "actual_decisions":
                return self.actual_decision_diagnostics(view)
            return [make_diagnostic("GA-FIXTURE-HANDLER", case_path, f"Unknown production_check {production_check!r}.", fixture_id)]
        if kind == "operator_decision_contract":
            schema_path = payload.get("schema_path")
            packet_version = "1.1.1" if schema_path == "schemas/operator-decision-record-1.1.1.schema.json" else "1.1.2"
            return self.operator_decision_contract_diagnostics(self.view, packet_version=packet_version)
        if kind == "public_distribution_receipt_contract":
            return self.public_distribution_receipt_contract_diagnostics(
                self.view,
                payload.get("variant"),
                payload.get("receipt_sequence", 2),
            )
        if kind in {"identity", "production_identity"}:
            return identity_authority_diagnostics(payload, case_path, fixture_id)
        if kind == "canonical_chain":
            objects: list[tuple[str, dict[str, Any]]] = []
            for relative in payload.get("paths", []):
                data = self.read_json_contract(relative)
                if isinstance(data, dict):
                    objects.append((relative, data))
                else:
                    return [make_diagnostic("GA-REQUIRED-ARTIFACT-MISSING", relative, "Canonical chain fixture target is absent.", fixture_id)]
            return self.semantic_object_chain(objects)
        if kind == "schema_instances":
            return self.experiment_result_diagnostics(list(payload.get("paths", [])))
        if kind == "kind_separation":
            return [] if payload.get("declared_kind") == payload.get("payload_kind") else [make_diagnostic("GA-KIND-CONFLATION", case_path, "Declared kind does not match payload kind.", fixture_id)]
        if kind == "epistemic_measurements":
            diagnostics: list[dict[str, Any]] = []
            for measurement in payload.get("measurements", []):
                if not isinstance(measurement, dict):
                    continue
                source_state = measurement.get("source_state")
                emitted_state = measurement.get("emitted_state")
                if source_state == "observed":
                    if emitted_state != "observed" or "emitted_value" not in measurement:
                        diagnostics.append(make_diagnostic("GA-EPISTEMIC-OBSERVED-INCOMPLETE", case_path, "Observed fixture measurement lacks an observed value.", measurement.get("measurement_id")))
                elif source_state in EPISTEMIC_RULES:
                    if emitted_state != source_state or "emitted_value" in measurement or not measurement.get("reason"):
                        diagnostics.append(make_diagnostic(EPISTEMIC_RULES[source_state], case_path, f"{source_state} was coerced or lost its reason.", measurement.get("measurement_id")))
            return diagnostics
        if kind == "lifecycle_status":
            return self.status_diagnostics(
                payload,
                case_path,
                fixture_id,
                view=self.view,
                record_kind="experiment",
                protocol_release_id="reiyah.protocol.harbor-gate-a@1.0.0",
            )
        if kind == "temporal_information_set":
            return [] if payload.get("input_available_at") <= payload.get("index_time") else [make_diagnostic("GA-TEMPORAL-LEAKAGE", case_path, "Input availability is later than the index time.", fixture_id)]
        if kind == "provenance":
            return [] if payload.get("provenance_present") is True else [make_diagnostic("GA-PROVENANCE-MISSING", case_path, "Synthetic record lacks provenance.", payload.get("record_id"))]
        if kind == "digest":
            actual = digest_bytes(payload.get("actual_utf8", "").encode("utf-8"))
            return [] if payload.get("declared_sha256") == actual else [make_diagnostic("GA-DIGEST-MISMATCH", case_path, "Declared SHA-256 does not match exact synthetic bytes.", fixture_id)]
        if kind == "typed_reference":
            objects = {
                (item.get("object_id"), item.get("version")): item
                for item in payload.get("objects", [])
                if isinstance(item, dict)
            }
            reference = payload.get("reference", {})
            target = objects.get((reference.get("object_id"), reference.get("version"))) if isinstance(reference, dict) else None
            if target is None:
                return [make_diagnostic("GA-REFERENCE-DANGLING", case_path, "Synthetic object reference does not resolve.", fixture_id)]
            if target.get("object_kind") != reference.get("object_kind") or target.get("object_kind") != payload.get("expected_kind"):
                return [make_diagnostic("GA-REFERENCE-WRONG-KIND", case_path, "Resolved synthetic reference has the wrong scientific kind.", fixture_id)]
            return []
        if kind == "manifest_binding":
            return [] if payload.get("bound_sha256") == payload.get("current_sha256") else [make_diagnostic("GA-MANIFEST-MUTATION", case_path, "Manifest release binding does not match current bytes.", payload.get("release_id"))]
        if kind == "release_ledger":
            seen: dict[str, str] = {}
            for entry in payload.get("entries", []):
                release_id = entry.get("release_id")
                digest = entry.get("sha256")
                if release_id in seen and seen[release_id] != digest:
                    return [make_diagnostic("GA-RELEASE-ID-REUSE", case_path, "One release identifier binds different digests.", release_id)]
                seen[release_id] = digest
            return []
        if kind == "denominator":
            counts = payload.get("state_counts", {})
            total = sum(counts.values()) if isinstance(counts, dict) and all(isinstance(value, int) for value in counts.values()) else -1
            return [] if total == payload.get("eligible_total") else [make_diagnostic("GA-DENOMINATOR-MISMATCH", case_path, "Epistemic counts do not reconcile to eligible_total.", fixture_id)]
        if kind == "group_coverage":
            declared = set(payload.get("declared_group_ids", []))
            results = set(payload.get("result_group_ids", []))
            return [] if declared == results else [make_diagnostic("GA-GROUP-OMITTED", case_path, f"Declared and represented groups differ; missing={sorted(declared - results)}.", fixture_id)]
        if kind == "determinism":
            allowed = {"repository_bytes", "interpreter", "local_schema_library"}
            unexpected = set(payload.get("input_sources", [])) - allowed
            return [] if not unexpected else [make_diagnostic("GA-NONDETERMINISTIC-INPUT", case_path, f"Nondeterministic inputs declared: {sorted(unexpected)}.", fixture_id)]
        if kind == "standards_claim":
            exact_fields = (
                payload.get("retained_exact_version"),
                payload.get("retained_publication_date"),
                payload.get("retained_scope"),
                payload.get("retained_comparator"),
                payload.get("retained_source_bytes"),
            )
            valid = payload.get("compliance_claimed") is False and all(value is True for value in exact_fields)
            return [] if valid else [make_diagnostic("GA-STANDARDS-UNSUPPORTED-CLAIM", case_path, "Standards mapping claims compliance or lacks exact retained evidence fields.", fixture_id)]
        if kind == "acceptance_binding":
            valid = (
                payload.get("bound_index_sha256") == payload.get("current_index_sha256")
                and payload.get("operator_authorized") is True
                and payload.get("architecture_complete") is True
            )
            return [] if valid else [make_diagnostic("GA-ACCEPTANCE-REPLAY", case_path, "Acceptance is stale, unauthorized, or not bound to architecture completeness.", fixture_id)]
        if kind == "data_boundary":
            valid = payload.get("data_classification") in {"synthetic", "public_evidence"} and payload.get("contains_real_records") is False
            return [] if valid else [make_diagnostic("GA-PRIVATE-DATA-PROHIBITED", case_path, "Private, secret, operational, or real records are prohibited at Gate A.", fixture_id)]
        if kind == "scope_boundary":
            allowed = {"documentation", "schema_validation", "synthetic_fixtures", "offline_digest_checking", "retained_public_evidence"}
            prohibited = set(payload.get("capabilities", [])) - allowed
            return [] if not prohibited else [make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", case_path, f"Unauthorized capabilities declared: {sorted(prohibited)}.", fixture_id)]
        if kind == "evidence_index":
            forbidden = {payload.get("index_path"), payload.get("sidecar_path"), payload.get("validation_report_path")}
            forbidden.update(payload.get("operator_decision_paths", []))
            circular = sorted(set(payload.get("indexed_paths", [])) & forbidden)
            return [] if not circular else [make_diagnostic("GA-INDEX-CIRCULAR", case_path, f"Index includes excluded derived paths: {circular}.", fixture_id)]
        return [make_diagnostic("GA-FIXTURE-HANDLER", case_path, f"No fixture handler for payload kind {kind!r}.", fixture_id)]

    def check_fixture_contract(self, cases: list[tuple[dict[str, Any], str]]) -> None:
        rule_items = self.plan.get("rules", [])
        rule_ids = [item.get("rule_id") for item in rule_items if isinstance(item, dict)]
        if len(rule_ids) != len(set(rule_ids)):
            self.add("GA-VALIDATION-PLAN", PLAN_PATH, "Validation rule IDs are not unique.")
        family_ids = [item.get("family_id") for item in self.plan.get("critical_families", []) if isinstance(item, dict)]
        if len(family_ids) != len(set(family_ids)):
            self.add("GA-VALIDATION-PLAN", PLAN_PATH, "Critical family IDs are not unique.")
        unknown_family_rules = {
            rule_id
            for family in self.plan.get("critical_families", [])
            if isinstance(family, dict)
            for rule_id in family.get("rule_ids", [])
            if rule_id not in set(rule_ids)
        }
        if unknown_family_rules:
            self.add("GA-VALIDATION-PLAN", PLAN_PATH, f"Critical families reference unknown rules: {sorted(unknown_family_rules)}.")
        bad_rules = [
            entry.get("expected_primary_rule_id")
            for entry in self.catalog.get("fixtures", [])
            if isinstance(entry, dict) and entry.get("classification") == "known_bad"
        ]
        for case, relative in cases:
            if case.get("classification") != "known_bad":
                continue
            payload = case.get("payload")
            kind = payload.get("kind") if isinstance(payload, dict) else None
            if kind not in {"production_mutation", "identity", "production_identity", "public_distribution_receipt_contract"}:
                self.add("GA-FIXTURE-COVERAGE", relative, "Known-bad fixture bypasses the production diagnostic path.", case.get("fixture_id"))
        for rule_id in rule_ids:
            count = bad_rules.count(rule_id)
            if count < 1:
                self.add("GA-FIXTURE-COVERAGE", CATALOG_PATH, f"Rule {rule_id} requires at least one primary known-bad fixture, found {count}.", rule_id)

    def run_fixtures(self) -> None:
        entries = self.catalog.get("fixtures", [])
        if not isinstance(entries, list):
            raise ExecutionFailure("fixture catalog lacks a fixtures array", CATALOG_PATH)
        catalog_ids: set[str] = set()
        catalog_paths: set[str] = set()
        cases: list[tuple[dict[str, Any], str]] = []
        v11_cases: list[tuple[dict[str, Any], str, dict[str, Any]]] = []
        self.fixture_summary["total"] = len(entries)
        for entry in entries:
            if not isinstance(entry, dict):
                self.add("GA-FIXTURE-CATALOG", CATALOG_PATH, "Catalog fixture entry is not an object.")
                continue
            fixture_id = entry.get("fixture_id")
            relative = entry.get("path")
            if not isinstance(fixture_id, str) or not isinstance(relative, str):
                self.add("GA-FIXTURE-CATALOG", CATALOG_PATH, "Catalog fixture entry lacks fixture_id or path.")
                continue
            if fixture_id in catalog_ids:
                self.add("GA-FIXTURE-CATALOG", CATALOG_PATH, f"Duplicate fixture_id {fixture_id}.", fixture_id)
            if relative in catalog_paths:
                self.add("GA-FIXTURE-CATALOG", CATALOG_PATH, f"Duplicate fixture path {relative}.", fixture_id)
            catalog_ids.add(fixture_id)
            catalog_paths.add(relative)
            case = self.read_json_execution(relative)
            schema_errors = self.instance_diagnostics(case, relative)
            if schema_errors:
                self.diagnostics.extend(schema_errors)
                continue
            if not isinstance(case, dict):
                continue
            schema_id = case.get("schema_id")
            if schema_id == V11_MUTATION_SCHEMA_ID or schema_id in V11_APPLICATION_RULES:
                v11_cases.append((case, relative, entry))
                if entry.get("classification") == "known_good":
                    expected_fixture_id = case.get("artifact_id")
                    if schema_id not in V11_APPLICATION_RULES or fixture_id != expected_fixture_id or entry.get("expected_primary_rule_id") is not None:
                        self.add("GA-FIXTURE-CATALOG", relative, "V1.1 direct known-good entry must use its artifact_id and null expected rule.", fixture_id)
                else:
                    expected_rule = entry.get("expected_primary_rule_id")
                    allowed_rules = {
                        V11_APPLICATION_RULES.get(case.get("target_schema_id")),
                        "GA-V11-REQUIRED-PROPERTY-SWEEP",
                    }
                    if schema_id != V11_MUTATION_SCHEMA_ID or case.get("fixture_id") != fixture_id or expected_rule not in allowed_rules:
                        self.add("GA-FIXTURE-CATALOG", relative, "V1.1 mutation catalog entry does not match its fixture ID and application production rule.", fixture_id)
                continue
            cases.append((case, relative))
            expected_rule = case.get("expected", {}).get("primary_rule_id")
            comparisons = (
                (case.get("fixture_id"), fixture_id, "fixture_id"),
                (case.get("classification"), entry.get("classification"), "classification"),
                (expected_rule, entry.get("expected_primary_rule_id"), "expected primary rule"),
            )
            for actual, expected, label in comparisons:
                if actual != expected:
                    self.add("GA-FIXTURE-CATALOG", relative, f"Case {label} does not match its catalog entry.", fixture_id)
        undeclared: list[str] = []
        for path in sorted((self.root / "fixtures").rglob("*.json")):
            relative = path.relative_to(self.root).as_posix()
            if relative == CATALOG_PATH or relative in {"fixtures/good/experiment.json", "fixtures/good/result.json"}:
                continue
            data = self.read_json_execution(relative)
            if (
                isinstance(data, dict)
                and (
                    data.get("schema_id") == "https://schemas.reiyah.invalid/gate-a/1.0.0/fixture-case.schema.json"
                    or data.get("schema_id") == "https://schemas.reiyah.invalid/gate-a/1.1.1/fixture-case.schema.json"
                    or data.get("schema_id") == "https://schemas.reiyah.invalid/gate-a/1.1.2/fixture-case.schema.json"
                    or data.get("schema_id") == V11_MUTATION_SCHEMA_ID
                    or data.get("schema_id") in V11_APPLICATION_RULES
                )
                and relative not in catalog_paths
            ):
                undeclared.append(relative)
        if undeclared:
            self.add("GA-FIXTURE-CATALOG", CATALOG_PATH, f"Fixture-case files are not cataloged: {undeclared}.")

        self.check_fixture_contract(cases)
        for case, relative in sorted(cases, key=lambda item: item[0].get("fixture_id", "")):
            fixture_id = case.get("fixture_id")
            classification = case.get("classification")
            expected_rule = case.get("expected", {}).get("primary_rule_id")
            observed = self.fixture_case_diagnostics(case, relative)
            observed_rules = {item["rule_id"] for item in observed}
            self.check_summary["fixture_cases_checked"] += 1
            if classification == "known_good":
                self.fixture_summary["known_good_total"] += 1
                if observed:
                    self.fixture_summary["unexpected_outcomes"] += 1
                    self.add("GA-FIXTURE-GOOD-FAILED", relative, f"Known-good fixture produced rules {sorted(observed_rules)}.", fixture_id)
                else:
                    self.fixture_summary["known_good_passed"] += 1
            else:
                self.fixture_summary["known_bad_total"] += 1
                if expected_rule in observed_rules:
                    self.fixture_summary["known_bad_rejected_for_declared_rule"] += 1
                else:
                    self.fixture_summary["unexpected_outcomes"] += 1
                    if not observed:
                        self.add("GA-FIXTURE-UNEXPECTED-PASS", relative, f"Known-bad fixture passed; expected {expected_rule}.", fixture_id)
                    else:
                        self.add("GA-FIXTURE-WRONG-REASON", relative, f"Expected {expected_rule}, observed {sorted(observed_rules)}.", fixture_id)

        for case, relative, entry in sorted(v11_cases, key=lambda item: item[1]):
            classification = entry.get("classification")
            fixture_id = entry.get("fixture_id")
            expected_rule = entry.get("expected_primary_rule_id")
            if classification == "known_good":
                observed = self.v11_application_diagnostics(case, relative)
                observed.extend(self.v11_required_property_sweep(case, relative))
            else:
                observed = self.v11_mutation_diagnostics(case, relative)
            observed_rules = {item["rule_id"] for item in observed}
            self.check_summary["fixture_cases_checked"] += 1
            if classification == "known_good":
                self.fixture_summary["known_good_total"] += 1
                if observed:
                    self.fixture_summary["unexpected_outcomes"] += 1
                    self.add("GA-FIXTURE-GOOD-FAILED", relative, f"Known-good v1.1 application produced rules {sorted(observed_rules)}.", fixture_id)
                else:
                    self.fixture_summary["known_good_passed"] += 1
            else:
                self.fixture_summary["known_bad_total"] += 1
                if expected_rule in observed_rules:
                    self.fixture_summary["known_bad_rejected_for_declared_rule"] += 1
                elif observed:
                    self.fixture_summary["unexpected_outcomes"] += 1
                    self.add("GA-FIXTURE-WRONG-REASON", relative, f"Expected {expected_rule}, observed {sorted(observed_rules)}.", fixture_id)
                else:
                    self.fixture_summary["unexpected_outcomes"] += 1
                    self.add("GA-FIXTURE-UNEXPECTED-PASS", relative, f"Known-bad v1.1 mutation passed; expected {expected_rule}.", fixture_id)

    def check_markdown_links(self) -> None:
        link_pattern = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
        recovery = self.read_view_json(self.view, HISTORICAL_RECOVERY_PATH)
        opaque_recovered_markdown: dict[str, str] = {}
        for entry in recovery.get("recovered_artifacts", []) if isinstance(recovery, dict) else []:
            binding = entry.get("recovered_binding") if isinstance(entry, dict) else None
            recovered_path = binding.get("path") if isinstance(binding, dict) else None
            expected_digest = entry.get("expected_sha256") if isinstance(entry, dict) else None
            if isinstance(recovered_path, str) and recovered_path.endswith(".md") and isinstance(expected_digest, str):
                opaque_recovered_markdown[recovered_path] = expected_digest
        for path in sorted(self.root.rglob("*.md")):
            relative = path.relative_to(self.root).as_posix()
            if relative in opaque_recovered_markdown:
                try:
                    if digest_bytes(path.read_bytes()) == opaque_recovered_markdown[relative]:
                        # These exact recovered bytes are authenticated by the recovery record.
                        # Their links were authored relative to the predecessor root and are
                        # historical content, not current navigational assertions.
                        continue
                except OSError:
                    pass
            try:
                text = path.read_text(encoding="utf-8")
            except OSError as exc:
                self.add("GA-DOCUMENT-LINK", relative, f"Cannot read Markdown: {exc}")
                continue
            for raw_target in link_pattern.findall(text):
                target = raw_target.strip()
                if target.startswith("<") and target.endswith(">"):
                    target = target[1:-1]
                if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target) or target.startswith("#"):
                    continue
                target = unquote(target.split("#", 1)[0].split("?", 1)[0])
                if not target:
                    continue
                linked = (path.parent / target).resolve()
                try:
                    linked.relative_to(self.root)
                except ValueError:
                    self.add("GA-DOCUMENT-LINK", relative, f"Internal link escapes repository: {raw_target}")
                    continue
                if not linked.exists():
                    self.add("GA-DOCUMENT-LINK", relative, f"Internal link target is missing: {raw_target}")

    def scope_inventory_diagnostics(self, view: RepositoryView) -> list[dict[str, Any]]:
        diagnostics = self.repository_inventory_diagnostics(view)
        plan = self.read_view_json(view, PLAN_PATH)
        bindings = plan.get("authorized_tool_bindings") if isinstance(plan, dict) else None
        expected_tool_paths = ["tools/build_gate_a_index.py", "tools/validate_gate_a.py"]
        binding_issues: list[str] = []
        if not isinstance(bindings, list) or len(bindings) != 2:
            binding_issues.append("authorized_tool_bindings must contain exactly two entries")
            bindings = []
        observed_tool_paths = [
            binding.get("path")
            for binding in bindings
            if isinstance(binding, dict)
        ]
        if observed_tool_paths != expected_tool_paths:
            binding_issues.append(
                f"authorized tool paths/order must equal {expected_tool_paths}, observed={observed_tool_paths}"
            )
        for binding in bindings:
            if not isinstance(binding, dict):
                binding_issues.append("authorized tool binding is not an object")
                continue
            relative = binding.get("path")
            if not isinstance(relative, str) or relative not in expected_tool_paths:
                continue
            try:
                raw = view.read_bytes(relative)
            except (OSError, ValueError):
                binding_issues.append(f"{relative} bytes are absent")
                continue
            observed_digest = digest_bytes(raw)
            if binding.get("sha256") != observed_digest:
                binding_issues.append(
                    f"{relative} digest mismatch: declared={binding.get('sha256')!r}, observed={observed_digest!r}"
                )
        if binding_issues:
            diagnostics.append(
                make_diagnostic(
                    "GA-RUNTIME-SCOPE-INTRUSION",
                    PLAN_PATH,
                    "Authorized offline tool source must exactly match the validation-plan byte bindings; "
                    f"violations={sorted(set(binding_issues))}.",
                )
            )
        allowed_suffixes = {"", ".cff", ".gitignore", ".html", ".json", ".jsonl", ".lock", ".md", ".pdf", ".py", ".pyc", ".sha256"}
        for relative in view.iter_files():
            if relative.startswith(".git/") or self.is_plan_excluded(relative):
                continue
            suffix = Path(relative).suffix.lower()
            if Path(relative).name != ".gitignore" and suffix not in allowed_suffixes:
                diagnostics.append(make_diagnostic("GA-INVENTORY-UNKNOWN-TYPE", relative, f"Unrecognized Gate A file suffix {suffix!r}."))
            if view.is_symlink(relative):
                diagnostics.append(make_diagnostic("GA-ARTIFACT-SYMLINK", relative, "Gate A artifact is a symlink and does not bind local bytes directly."))
        runtime_imports = {
            "builtins",
            "ftplib",
            "grpc",
            "imaplib",
            "os",
            "paramiko",
            "poplib",
            "shutil",
            "smtplib",
            "socket",
            "ssl",
            "tempfile",
            "requests",
            "http.client",
            "http.server",
            "urllib.request",
            "aiohttp",
            "flask",
            "fastapi",
            "torch",
            "tensorflow",
            "sklearn",
        }
        nondeterministic_imports = {"random", "secrets", "time", "uuid"}

        def dotted_name(value: ast.AST) -> str | None:
            if isinstance(value, ast.Name):
                return value.id
            if isinstance(value, ast.Attribute):
                parent = dotted_name(value.value)
                return f"{parent}.{value.attr}" if parent else None
            return None

        def constant_string_dict(value: ast.AST) -> dict[str, str] | None:
            if not isinstance(value, ast.Dict) or len(value.keys) != len(value.values):
                return None
            result: dict[str, str] = {}
            for key_node, item_node in zip(value.keys, value.values):
                if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
                    return None
                if not isinstance(item_node, ast.Constant) or not isinstance(item_node.value, str):
                    return None
                if key_node.value in result:
                    return None
                result[key_node.value] = item_node.value
            return result

        def authorized_subprocess_run(node: ast.Call, relative: str) -> bool:
            if dotted_name(node.func) != "subprocess.run" or len(node.args) != 1:
                return False
            command = node.args[0]
            if not isinstance(command, ast.List):
                return False
            keyword_values = {
                keyword.arg: keyword.value
                for keyword in node.keywords
                if isinstance(keyword.arg, str)
            }
            if len(keyword_values) != len(node.keywords):
                return False
            git_command = ["git", "rev-parse", "--show-toplevel"]
            observed_constants = [
                item.value if isinstance(item, ast.Constant) and isinstance(item.value, str) else None
                for item in command.elts
            ]
            if observed_constants == git_command:
                expected_keywords = {"cwd", "check", "capture_output", "text", "env"}
                environment = constant_string_dict(keyword_values.get("env", ast.Constant(None)))
                return (
                    relative in {"tools/build_gate_a_index.py", "tools/validate_gate_a.py"}
                    and set(keyword_values) == expected_keywords
                    and isinstance(keyword_values["cwd"], ast.Name)
                    and keyword_values["cwd"].id == "CANONICAL_ROOT"
                    and isinstance(keyword_values["check"], ast.Constant)
                    and keyword_values["check"].value is False
                    and isinstance(keyword_values["capture_output"], ast.Constant)
                    and keyword_values["capture_output"].value is True
                    and isinstance(keyword_values["text"], ast.Constant)
                    and keyword_values["text"].value is True
                    and environment
                    == {"LC_ALL": "C", "PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin"}
                )
            builder_command = (
                len(command.elts) == 3
                and dotted_name(command.elts[0]) == "sys.executable"
                and isinstance(command.elts[1], ast.Constant)
                and command.elts[1].value == "-B"
                and isinstance(command.elts[2], ast.Constant)
                and command.elts[2].value == "tools/build_gate_a_index.py"
            )
            if builder_command:
                expected_keywords = {"cwd", "check", "capture_output", "env"}
                environment = constant_string_dict(keyword_values.get("env", ast.Constant(None)))
                cwd = keyword_values.get("cwd")
                return (
                    relative == "tools/validate_gate_a.py"
                    and set(keyword_values) == expected_keywords
                    and isinstance(cwd, ast.Attribute)
                    and isinstance(cwd.value, ast.Name)
                    and cwd.value.id == "self"
                    and cwd.attr == "root"
                    and isinstance(keyword_values["check"], ast.Constant)
                    and keyword_values["check"].value is False
                    and isinstance(keyword_values["capture_output"], ast.Constant)
                    and keyword_values["capture_output"].value is True
                    and environment
                    == {
                        "LC_ALL": "C",
                        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin",
                        "PYTHONDONTWRITEBYTECODE": "1",
                    }
                )
            return False

        write_call_names = {
            "FileType",
            "chmod",
            "chown",
            "copy",
            "copy2",
            "dump",
            "hardlink_to",
            "link",
            "makedirs",
            "mkdir",
            "move",
            "open",
            "remove",
            "rename",
            "replace",
            "rmdir",
            "rmtree",
            "symlink_to",
            "touch",
            "truncate",
            "unlink",
            "write",
            "write_bytes",
            "write_text",
            "writelines",
        }
        process_call_names = {
            "call",
            "check_call",
            "check_output",
            "execv",
            "execve",
            "fork",
            "popen",
            "Popen",
            "posix_spawn",
            "spawnl",
            "spawnv",
            "system",
        }
        dynamic_call_names = {
            "__import__",
            "compile",
            "eval",
            "exec",
            "getattr",
            "globals",
            "input",
            "locals",
            "setattr",
            "vars",
        }
        nondeterministic_call_names = {
            "getenv",
            "monotonic",
            "now",
            "perf_counter",
            "process_time",
            "sleep",
            "time",
            "today",
            "urandom",
            "utcnow",
            "uuid1",
            "uuid4",
        }
        nondeterministic_attributes = {
            "environ",
            "stdin",
            "st_atime",
            "st_atime_ns",
            "st_ctime",
            "st_ctime_ns",
            "st_mtime",
            "st_mtime_ns",
        }
        allowed_plain_imports: dict[str, set[tuple[str, str | None]]] = {
            "tools/build_gate_a_index.py": {
                (name, None)
                for name in ("argparse", "hashlib", "json", "math", "re", "subprocess", "sys")
            },
            "tools/validate_gate_a.py": {
                (name, None)
                for name in ("argparse", "ast", "hashlib", "json", "math", "platform", "re", "subprocess", "sys")
            },
        }
        allowed_from_imports: dict[str, dict[str, set[tuple[str, str | None]]]] = {
            "tools/build_gate_a_index.py": {
                "__future__": {("annotations", None)},
                "pathlib": {("Path", None)},
                "typing": {("Any", None)},
            },
            "tools/validate_gate_a.py": {
                "__future__": {("annotations", None)},
                "datetime": {("datetime", None), ("timezone", None)},
                "importlib.metadata": {("PackageNotFoundError", None), ("version", "package_version")},
                "pathlib": {("Path", None)},
                "typing": {("Any", None), ("Callable", None), ("Iterable", None)},
                "urllib.parse": {("unquote", None)},
                "jsonschema": {("Draft202012Validator", None), ("FormatChecker", None)},
                "referencing": {("Registry", None), ("Resource", None)},
            },
        }
        tool_paths = sorted(relative for relative in view.iter_files() if re.fullmatch(r"tools/[^/]+\.py", relative))
        for relative in tool_paths:
            try:
                tree = ast.parse(view.read_text(relative), filename=relative)
            except (OSError, UnicodeDecodeError, ValueError, SyntaxError) as exc:
                diagnostics.append(make_diagnostic("GA-VALIDATOR-SOURCE", relative, f"Cannot parse validator source: {exc}"))
                continue
            parents = {
                child: parent
                for parent in ast.walk(tree)
                for child in ast.iter_child_nodes(parent)
            }
            for node in ast.walk(tree):
                imported: list[str] = []
                if isinstance(node, ast.Import):
                    imported = [alias.name for alias in node.names]
                    unauthorized_aliases = sorted(
                        f"{alias.name} as {alias.asname}" if alias.asname else alias.name
                        for alias in node.names
                        if (alias.name, alias.asname) not in allowed_plain_imports.get(relative, set())
                    )
                    if unauthorized_aliases:
                        diagnostics.append(make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", relative, f"Imports are outside the exact authorized offline-tool allowlist: {unauthorized_aliases}."))
                    for alias in node.names:
                        if alias.name == "subprocess" and alias.asname is not None:
                            diagnostics.append(make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", relative, "The audited subprocess module may not be imported through an alias."))
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported = [node.module]
                    allowed_aliases = allowed_from_imports.get(relative, {}).get(node.module, set()) if node.level == 0 else set()
                    unauthorized_aliases = sorted(
                        f"{alias.name} as {alias.asname}" if alias.asname else alias.name
                        for alias in node.names
                        if (alias.name, alias.asname) not in allowed_aliases
                    )
                    if unauthorized_aliases or node.module not in allowed_from_imports.get(relative, {}):
                        diagnostics.append(make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", relative, f"From-import is outside the exact authorized offline-tool allowlist: module={node.module!r}, names={unauthorized_aliases or [alias.name for alias in node.names]}."))
                    if node.module == "subprocess":
                        diagnostics.append(make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", relative, "Direct subprocess symbol imports bypass the exact audited call surface."))
                for module in imported:
                    if any(module == banned or module.startswith(banned + ".") for banned in nondeterministic_imports):
                        diagnostics.append(make_diagnostic("GA-NONDETERMINISTIC-INPUT", relative, f"Nondeterministic import is forbidden in Gate A tooling: {module}."))
                    elif any(module == banned or module.startswith(banned + ".") for banned in runtime_imports):
                        diagnostics.append(make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", relative, f"Prohibited runtime or network import: {module}."))
                if isinstance(node, ast.Attribute) and node.attr in nondeterministic_attributes:
                    diagnostics.append(make_diagnostic("GA-NONDETERMINISTIC-INPUT", relative, f"Environment, input-stream, or filesystem-clock surface is forbidden: {node.attr}."))
                if isinstance(node, ast.Attribute):
                    if node.attr == "modules":
                        diagnostics.append(make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", relative, "Interpreter module-registry reflection is forbidden in Gate A tooling."))
                    allowed_dunder = (
                        node.attr == "__init__"
                        and isinstance(node.value, ast.Call)
                        and isinstance(node.value.func, ast.Name)
                        and node.value.func.id == "super"
                    ) or (
                        node.attr == "__name__"
                        and isinstance(node.value, ast.Call)
                        and isinstance(node.value.func, ast.Name)
                        and node.value.func.id == "type"
                    )
                    if node.attr.startswith("__") and node.attr.endswith("__") and not allowed_dunder:
                        diagnostics.append(make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", relative, f"Dunder reflection or callable indirection is forbidden in Gate A tooling: {node.attr}."))
                    attribute_name = dotted_name(node) or ""
                    if attribute_name.startswith("subprocess."):
                        parent = parents.get(node)
                        direct_authorized_call = (
                            isinstance(parent, ast.Call)
                            and parent.func is node
                            and node.attr == "run"
                            and authorized_subprocess_run(parent, relative)
                        )
                        if not direct_authorized_call:
                            diagnostics.append(make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", relative, f"Process callable reference or alias is forbidden: {attribute_name}."))
                    if node.attr == "run":
                        parent = parents.get(node)
                        exact_run = (
                            isinstance(parent, ast.Call)
                            and parent.func is node
                            and authorized_subprocess_run(parent, relative)
                        )
                        if not exact_run:
                            diagnostics.append(make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", relative, "A terminal run callable is forbidden unless it is an exact audited subprocess.run invocation."))
                    direct_call = isinstance(parents.get(node), ast.Call) and parents[node].func is node
                    if node.attr in write_call_names and not direct_call:
                        diagnostics.append(make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", relative, f"Filesystem/mutable-output callable reference or alias is forbidden: {node.attr}."))
                    if node.attr in nondeterministic_call_names and not direct_call:
                        diagnostics.append(make_diagnostic("GA-NONDETERMINISTIC-INPUT", relative, f"Nondeterministic callable reference or alias is forbidden: {node.attr}."))
                dangerous_name_references = {"open"} | dynamic_call_names | write_call_names | nondeterministic_call_names | process_call_names
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in dangerous_name_references:
                    parent = parents.get(node)
                    if not (isinstance(parent, ast.Call) and parent.func is node):
                        diagnostics.append(make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", relative, f"Dangerous built-in callable reference or alias is forbidden: {node.id}."))
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id == "subprocess":
                    parent = parents.get(node)
                    if not (isinstance(parent, ast.Attribute) and parent.value is node):
                        diagnostics.append(make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", relative, "The subprocess module itself may not be aliased or passed as a value."))
                if isinstance(node, ast.Call):
                    if isinstance(node.func, (ast.Subscript, ast.Call, ast.Lambda)):
                        diagnostics.append(make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", relative, "Subscripted, returned, or lambda callable indirection is forbidden in Gate A tooling."))
                    qualified_name = dotted_name(node.func) or ""
                    if qualified_name:
                        function_name = qualified_name.rsplit(".", 1)[-1]
                    elif isinstance(node.func, ast.Attribute):
                        function_name = node.func.attr
                    elif isinstance(node.func, ast.Name):
                        function_name = node.func.id
                    else:
                        function_name = ""
                    if qualified_name == "subprocess.run":
                        if not authorized_subprocess_run(node, relative):
                            diagnostics.append(make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", relative, "Only the exact audited Git identity or canonical index-builder subprocess invocation is permitted."))
                        continue
                    if function_name == "run":
                        diagnostics.append(make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", relative, "A run call is forbidden unless it is an exact audited subprocess.run invocation."))
                    if function_name in process_call_names:
                        diagnostics.append(make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", relative, f"Process or shell invocation is forbidden outside the exact audited subprocess calls: {qualified_name or function_name}."))
                    dynamic_indirection = (
                        qualified_name in dynamic_call_names
                        or qualified_name in {f"builtins.{name}" for name in dynamic_call_names}
                    )
                    if dynamic_indirection:
                        diagnostics.append(make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", relative, f"Dynamic code/import/IO indirection is forbidden in Gate A tooling: {function_name}."))
                    stdout_write = qualified_name in {"sys.stdout.write", "sys.stdout.buffer.write", "sys.stderr.write", "sys.stderr.buffer.write"}
                    safe_string_replace = (
                        function_name == "replace"
                        and len(node.args) == 2
                        and all(isinstance(argument, ast.Constant) and isinstance(argument.value, str) for argument in node.args)
                        and (node.args[0].value, node.args[1].value)
                        in {("~1", "/"), ("~0", "~"), ("~", "~0"), ("/", "~1"), ("Z", "+00:00")}
                    )
                    if function_name in write_call_names and not stdout_write and not safe_string_replace:
                        diagnostics.append(make_diagnostic("GA-RUNTIME-SCOPE-INTRUSION", relative, f"Filesystem or mutable-output call is forbidden in Gate A tooling: {qualified_name or function_name}."))
                    if function_name in nondeterministic_call_names:
                        diagnostics.append(make_diagnostic("GA-NONDETERMINISTIC-INPUT", relative, f"Nondeterministic clock, environment, or entropy call is forbidden: {qualified_name or function_name}."))
        return sorted(diagnostics, key=diagnostic_key)

    def check_scope_inventory(self) -> None:
        self.diagnostics.extend(self.scope_inventory_diagnostics(self.view))

    def canonical_index_output(self) -> tuple[bytes | None, str | None]:
        try:
            completed = subprocess.run(
                [sys.executable, "-B", "tools/build_gate_a_index.py"],
                cwd=self.root,
                check=False,
                capture_output=True,
                env={
                    "LC_ALL": "C",
                    "PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin",
                    "PYTHONDONTWRITEBYTECODE": "1",
                },
            )
        except OSError as exc:
            return None, f"canonical builder could not execute: {exc}"
        if completed.returncode != 0:
            stderr = completed.stderr.decode("utf-8", errors="replace").strip()
            return None, f"canonical builder refused with exit {completed.returncode}: {stderr}"
        return completed.stdout, None

    def index_canonical_diagnostics(self, view: RepositoryView) -> list[dict[str, Any]]:
        expected_raw, error = self.canonical_index_output()
        diagnostics: list[dict[str, Any]] = []
        if expected_raw is None:
            diagnostics.append(make_diagnostic("GA-INDEX-NONCANONICAL", INDEX_PATH, error or "Canonical builder failed."))
        try:
            actual_raw = view.read_bytes(INDEX_PATH)
            actual = strict_json_loads(actual_raw.decode("utf-8"))
        except DuplicateJSONKeyError as exc:
            diagnostics.append(make_diagnostic("GA-JSON-DUPLICATE-KEY", INDEX_PATH, f"Evidence index JSON member names must be unique: {exc}"))
            return sorted(diagnostics, key=diagnostic_key)
        except NonFiniteJSONError as exc:
            diagnostics.append(make_diagnostic("GA-NONFINITE-NUMBER", INDEX_PATH, f"Evidence index JSON numbers must be finite: {exc}"))
            return sorted(diagnostics, key=diagnostic_key)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, StrictJSONError) as exc:
            diagnostics.append(make_diagnostic("GA-INDEX-NONCANONICAL", INDEX_PATH, f"Saved index cannot be inspected: {exc}"))
            return sorted(diagnostics, key=diagnostic_key)
        if expected_raw is not None:
            try:
                expected = strict_json_loads(expected_raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError, StrictJSONError) as exc:
                diagnostics.append(make_diagnostic("GA-INDEX-NONCANONICAL", INDEX_PATH, f"Canonical builder output is malformed: {exc}"))
                expected = None
        else:
            expected = None
        if expected_raw is not None and (actual_raw != expected_raw or actual != expected):
            diagnostics.append(
                make_diagnostic(
                    "GA-INDEX-NONCANONICAL",
                    INDEX_PATH,
                    "Saved evidence index bytes and whole object do not exactly equal canonical builder output.",
                    actual.get("index_id") if isinstance(actual, dict) else None,
                )
            )
        if isinstance(actual, dict) and (
            actual.get("operator_acceptance_state") != "unaccepted"
            or actual.get("operator_decision_binding") is not None
        ):
            diagnostics.append(
                make_diagnostic(
                    "GA-ACCEPTANCE-REPLAY",
                    INDEX_PATH,
                    "Bootstrap index must remain unaccepted with no operator decision binding.",
                    actual.get("index_id") if isinstance(actual.get("index_id"), str) else None,
                )
            )
        artifacts = actual.get("artifacts", []) if isinstance(actual, dict) else []
        if isinstance(artifacts, list):
            exact_roles = {
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
                "docs/FRONTIER_BASELINE_2026.md": "frontier_baseline",
                "docs/GLOSSARY.md": "glossary",
                "docs/MATHEMATICAL_SPECIFICATION.md": "mathematical_specification",
                "docs/PRE_IMPLEMENTATION_GATE.md": "preimplementation_gate",
                "docs/RESEARCH_GAP_REGISTER.md": "research_gap_register",
                "docs/RESEARCH_OPERATING_MODEL.md": "research_operating_model",
                "docs/SCIENTIFIC_CHARTER.md": "scientific_charter",
                "docs/SESSION_HANDOFF.md": "session_handoff",
                "docs/SOURCE_POLICY.md": "source_policy",
                "docs/STANDARDS_CROSSWALK.md": "standards_crosswalk",
                "docs/STATUS_MODEL.md": "status_model",
                "docs/THREAT_MODEL.md": "threat_model",
                "docs/VALIDATION.md": "validation_specification",
                "evidence/README.md": "evidence_custody_documentation",
                FRONTIER_DISCOVERY_REGISTER_PATH: "frontier_discovery_register",
                PUBLIC_DISTRIBUTION_INVENTORY_PATH: "public_distribution_inventory",
                PUBLIC_CUSTODY_PROFILE_PATH: "public_evidence_custody_profile",
                PUBLIC_RIGHTS_REVALIDATION_PATH: "public_rights_revalidation",
                SUCCESSOR_PUBLIC_RIGHTS_REVALIDATION_PATH: "public_rights_revalidation",
                CURRENT_PUBLIC_RIGHTS_REVALIDATION_PATH: "public_rights_revalidation",
                ACTIVE_SOURCE_LEDGER_PATH: "source_ledger",
                "evidence/source-ledger.json": "historical_source_ledger",
                ACTIVE_STANDARDS_CROSSWALK_PATH: "standards_crosswalk",
                "evidence/standards-crosswalk.json": "historical_standards_crosswalk",
                CATALOG_PATH: "fixture_catalog",
                "gate/validation-reports/gate-a-validation-1.0.0.json": "historical_candidate_artifact",
                HISTORICAL_V11_REPORT_PATH: "historical_candidate_artifact",
                HISTORICAL_V111_REPORT_PATH: "historical_candidate_artifact",
                "gate/README.md": "acceptance_procedure",
                LEGACY_TEMPLATE_PATH: "operator_decision_template",
                V111_TEMPLATE_PATH: "operator_decision_template",
                TEMPLATE_PATH: "operator_decision_template",
                HISTORICAL_V111_INDEX_PATH: "historical_candidate_artifact",
                HISTORICAL_V111_SIDECAR_PATH: "historical_candidate_artifact",
                "manifests/manifest-release-ledger.json": "manifest_release_ledger",
                "manifests/history/manifest-release-ledger-1.0.0.json": "historical_manifest_release_ledger",
                SCIENTIFIC_CONTRACT_PROFILE_PATH: "scientific_contract_profile",
                HISTORICAL_RECOVERY_PATH: "historical_packet_recovery",
                "validation/requirements.lock": "repository_metadata",
                PLAN_PATH: "validation_specification",
                "tools/validate_gate_a.py": "offline_validator",
                "tools/build_gate_a_index.py": "index_builder",
            }
            media_types = {
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
            fixture_schema_ids = {
                "https://schemas.reiyah.invalid/gate-a/1.0.0/fixture-case.schema.json",
                "https://schemas.reiyah.invalid/gate-a/1.1.1/fixture-case.schema.json",
                "https://schemas.reiyah.invalid/gate-a/1.1.2/fixture-case.schema.json",
                V11_MUTATION_SCHEMA_ID,
            }
            mission_schema_ids = {
                "https://schemas.reiyah.invalid/gate-a/1.0.0/mission-manifest.schema.json",
                "https://schemas.reiyah.invalid/gate-a/1.1.0/mission-manifest.schema.json",
            }
            exact_role_schema_ids = {
                "manifest_release_ledger": {"https://schemas.reiyah.invalid/gate-a/1.1.0/manifest-release-ledger.schema.json"},
                "historical_manifest_release_ledger": {"https://schemas.reiyah.invalid/gate-a/1.0.0/manifest-release-ledger.schema.json"},
                "source_ledger": {"https://schemas.reiyah.invalid/gate-a/1.1.0/source-ledger.schema.json"},
                "historical_source_ledger": {"https://schemas.reiyah.invalid/gate-a/1.0.0/source-ledger.schema.json"},
                "standards_crosswalk": {"https://schemas.reiyah.invalid/gate-a/1.1.0/standards-crosswalk.schema.json"},
                "historical_standards_crosswalk": {"https://schemas.reiyah.invalid/gate-a/1.0.0/standards-crosswalk.schema.json"},
                "frontier_discovery_register": {"https://schemas.reiyah.invalid/gate-a/1.1.0/frontier-discovery-register.schema.json"},
                "public_distribution_inventory": {"https://schemas.reiyah.invalid/gate-a/1.1.0/public-distribution-inventory.schema.json"},
                "public_evidence_custody_profile": {"https://schemas.reiyah.invalid/gate-a/1.1.0/public-evidence-custody-profile.schema.json"},
                "public_rights_revalidation": {
                    "https://schemas.reiyah.invalid/gate-a/1.1.0/public-rights-revalidation.schema.json",
                    "https://schemas.reiyah.invalid/gate-a/1.1.1/public-rights-revalidation.schema.json",
                    "https://schemas.reiyah.invalid/gate-a/1.1.2/public-rights-revalidation.schema.json",
                },
                "fixture_catalog": {"https://schemas.reiyah.invalid/gate-a/1.1.2/fixture-catalog.schema.json"},
                "operator_decision_template": {
                    "https://schemas.reiyah.invalid/gate-a/1.1.0/operator-decision-record.schema.json",
                    "https://schemas.reiyah.invalid/gate-a/1.1.1/operator-decision-record.schema.json",
                    "https://schemas.reiyah.invalid/gate-a/1.1.2/operator-decision-record.schema.json",
                },
                "historical_packet_recovery": {"https://schemas.reiyah.invalid/gate-a/1.1.0/historical-packet-recovery.schema.json"},
            }
            ledger_document = self.read_view_json(view, "manifests/manifest-release-ledger.json")
            manifest_paths_by_kind = {
                kind: {
                    entry.get("artifact_binding", {}).get("path")
                    for entry in ledger_document.get("entries", [])
                    if isinstance(ledger_document, dict)
                    and isinstance(entry, dict)
                    and entry.get("manifest_kind") == kind
                    and isinstance(entry.get("artifact_binding"), dict)
                    and isinstance(entry.get("artifact_binding", {}).get("path"), str)
                }
                for kind in ("mission", "protocol")
            } if isinstance(ledger_document, dict) else {"mission": set(), "protocol": set()}
            source_document = self.read_view_json(view, ACTIVE_SOURCE_LEDGER_PATH)
            ledger_source_paths = {
                record.get("retained_payload", {}).get("path")
                for record in source_document.get("records", [])
                if isinstance(source_document, dict)
                and isinstance(record, dict)
                and isinstance(record.get("retained_payload"), dict)
                and isinstance(record.get("retained_payload", {}).get("path"), str)
            } if isinstance(source_document, dict) else set()
            catalog_document = self.read_view_json(view, CATALOG_PATH)
            catalog_classification = {
                fixture.get("path"): fixture.get("classification")
                for fixture in catalog_document.get("fixtures", [])
                if isinstance(catalog_document, dict)
                and isinstance(fixture, dict)
                and isinstance(fixture.get("path"), str)
                and isinstance(fixture.get("classification"), str)
            } if isinstance(catalog_document, dict) else {}
            protocol_registry_paths: set[str] = set()
            for protocol_path in manifest_paths_by_kind.get("protocol", set()):
                protocol = self.read_view_json(view, protocol_path)
                registry_path = protocol.get("definition_registry", {}).get("path") if isinstance(protocol, dict) and isinstance(protocol.get("definition_registry"), dict) else None
                if isinstance(registry_path, str):
                    protocol_registry_paths.add(registry_path)
            canonical_claim_path = "manifests/claims/proposed-claims-and-non-claims-1.0.0.json"
            canonical_chain_paths = {
                f"manifests/examples/object-chain/{name}.json"
                for name in ("observation", "latent-belief", "decision", "intervention", "outcome", "evidence")
            }

            def strict_role(relative: str) -> str | None:
                if relative in exact_roles:
                    return exact_roles[relative]
                if relative in ledger_source_paths:
                    return "retained_source"
                if relative.startswith("evidence/sources/"):
                    return None
                if relative.startswith("schemas/") and relative.endswith(".schema.json"):
                    return "schema"
                if relative.startswith("fixtures/good/") and relative.endswith(".json"):
                    return "known_good_fixture"
                if relative.startswith("fixtures/bad/") and relative.endswith(".json"):
                    return "known_bad_fixture"
                if relative.startswith("fixtures/v1.1/good/") and relative.endswith(".json"):
                    return "known_good_fixture"
                if relative.startswith("fixtures/v1.1/known-bad/") and relative.endswith(".json"):
                    return "known_bad_fixture"
                if relative in manifest_paths_by_kind.get("mission", set()):
                    return "mission_manifest"
                if relative.startswith("manifests/mission/"):
                    return None
                if relative in manifest_paths_by_kind.get("protocol", set()):
                    return "protocol_manifest"
                if relative.startswith("manifests/protocol/"):
                    return None
                if relative in protocol_registry_paths:
                    return "protocol_definition_registry"
                if relative.startswith("manifests/definitions/"):
                    return None
                if relative.startswith("manifests/research/") and relative.endswith(".json"):
                    return "research_function_registry"
                if relative == canonical_claim_path:
                    return "claims_and_non_claims"
                if relative.startswith("manifests/claims/"):
                    return None
                if relative in canonical_chain_paths:
                    return "known_good_fixture"
                if relative.startswith("manifests/examples/object-chain/"):
                    return None
                if relative.startswith("history/gate-a-1.0.0/"):
                    return "historical_candidate_artifact"
                if relative in {HISTORICAL_V11_INDEX_PATH, HISTORICAL_V11_SIDECAR_PATH}:
                    return "historical_candidate_artifact"
                if relative.startswith("history/gate-a-1.1.0/"):
                    return None
                if relative in {HISTORICAL_V111_INDEX_PATH, HISTORICAL_V111_SIDECAR_PATH}:
                    return "historical_candidate_artifact"
                if relative.startswith("history/gate-a-1.1.1/"):
                    return None
                return None

            indexed_items_by_path: dict[str, list[dict[str, Any]]] = {}
            for item in artifacts:
                binding = item.get("artifact") if isinstance(item, dict) else None
                relative = binding.get("path") if isinstance(binding, dict) else None
                if isinstance(relative, str):
                    indexed_items_by_path.setdefault(relative, []).append(item)
            role_violations: list[str] = []
            for relative in view.iter_files():
                if self.is_plan_excluded(relative):
                    continue
                expected_role = strict_role(relative)
                items = indexed_items_by_path.get(relative, [])
                if expected_role is None:
                    role_violations.append(f"{relative}: no exact Gate A role")
                    continue
                if len(items) != 1:
                    role_violations.append(f"{relative}: indexed matches={len(items)}")
                    continue
                item = items[0]
                binding = item.get("artifact") if isinstance(item.get("artifact"), dict) else {}
                expected_media = "text/plain" if relative in {".gitattributes", ".gitignore", "LICENSE", "NOTICE"} else media_types.get(Path(relative).suffix.lower())
                if item.get("role") != expected_role:
                    role_violations.append(f"{relative}: role={item.get('role')!r}, expected={expected_role!r}")
                if item.get("media_type") != expected_media:
                    role_violations.append(f"{relative}: media_type={item.get('media_type')!r}, expected={expected_media!r}")
                document = self.read_view_json(view, relative) if relative.endswith(".json") else None
                document_schema = (
                    document.get("$id") if expected_role == "schema" else document.get("schema_id")
                ) if isinstance(document, dict) else None
                if relative.endswith(".json") and binding.get("schema_id") != document_schema:
                    role_violations.append(f"{relative}: indexed schema_id does not equal target schema_id")
                allowed_role_schemas = exact_role_schema_ids.get(expected_role)
                if (
                    allowed_role_schemas is not None
                    and relative.endswith(".json")
                    and document_schema not in allowed_role_schemas
                ):
                    role_violations.append(f"{relative}: {expected_role} role has wrong schema")
                if expected_role == "mission_manifest" and document_schema not in mission_schema_ids:
                    role_violations.append(f"{relative}: mission role has wrong schema")
                elif expected_role == "protocol_manifest" and document_schema not in PROTOCOL_MANIFEST_SCHEMA_IDS:
                    role_violations.append(f"{relative}: protocol role has wrong schema")
                elif expected_role == "protocol_definition_registry" and document_schema not in PROTOCOL_DEFINITION_REGISTRY_SCHEMA_IDS:
                    role_violations.append(f"{relative}: definition-registry role has wrong schema")
                elif expected_role == "research_function_registry" and document_schema != "https://schemas.reiyah.invalid/gate-a/1.1.0/research-function-registry.schema.json":
                    role_violations.append(f"{relative}: research-function-registry role has wrong schema")
                elif expected_role == "scientific_contract_profile" and document_schema != "https://schemas.reiyah.invalid/gate-a/1.1.0/scientific-contract-profile.schema.json":
                    role_violations.append(f"{relative}: scientific-contract-profile role has wrong schema")
                elif relative == canonical_claim_path and document_schema != CLAIM_REGISTER_SCHEMA_ID:
                    role_violations.append(f"{relative}: claim-register role has wrong schema")
                elif expected_role == "known_bad_fixture":
                    if document_schema not in fixture_schema_ids or catalog_classification.get(relative) != "known_bad":
                        role_violations.append(f"{relative}: known-bad role is not an exact catalogued fixture case")
                elif expected_role == "known_good_fixture" and document_schema in fixture_schema_ids and catalog_classification.get(relative) != "known_good":
                    role_violations.append(f"{relative}: fixture-case known-good role is not catalogued")
                elif relative in canonical_chain_paths and document_schema not in OBJECT_SCHEMA_IDS:
                    role_violations.append(f"{relative}: canonical-chain role has wrong scientific schema")
            extra_index_paths = sorted(set(indexed_items_by_path) - set(view.iter_files()))
            if extra_index_paths:
                role_violations.append(f"index paths absent from repository view={extra_index_paths}")
            if role_violations:
                diagnostics.append(
                    make_diagnostic(
                        "GA-INDEX-ROLE-INELIGIBLE",
                        INDEX_PATH,
                        f"Indexed and repository artifacts must satisfy exact role, media, schema, ledger, and fixture-catalog ownership; violations={sorted(set(role_violations))}.",
                    )
                )
            indexed_paths = {
                item.get("artifact", {}).get("path")
                for item in artifacts
                if isinstance(item, dict) and isinstance(item.get("artifact"), dict)
            }
            circular = sorted(
                path
                for path in indexed_paths
                if isinstance(path, str)
                and (
                    path in {INDEX_PATH, SIDECAR_PATH, REPORT_PATH}
                    or path.startswith("gate/decisions/reiyah.gate-a-decision-")
                )
            )
            if circular:
                diagnostics.append(make_diagnostic("GA-INDEX-CIRCULAR", INDEX_PATH, f"Evidence index includes forbidden self-derived paths: {circular}."))
            missing_versions = sorted(
                item.get("artifact", {}).get("path")
                for item in artifacts
                if isinstance(item, dict)
                and isinstance(item.get("artifact"), dict)
                and not isinstance(item["artifact"].get("version"), str)
            )
            if missing_versions:
                diagnostics.append(make_diagnostic("GA-INDEX-NONCANONICAL", INDEX_PATH, f"Every indexed artifact binding requires an explicit version; missing={missing_versions}."))
            ledger = self.read_view_json(view, ACTIVE_SOURCE_LEDGER_PATH)
            ledger_paths = {
                record.get("retained_payload", {}).get("path")
                for record in ledger.get("records", [])
                if isinstance(ledger, dict)
                and isinstance(record, dict)
                and isinstance(record.get("retained_payload"), dict)
                and isinstance(record.get("retained_payload", {}).get("path"), str)
            } if isinstance(ledger, dict) else set()
            role_paths = {
                item.get("artifact", {}).get("path")
                for item in artifacts
                if isinstance(item, dict)
                and item.get("role") == "retained_source"
                and isinstance(item.get("artifact"), dict)
            }
            if role_paths != ledger_paths:
                diagnostics.append(make_diagnostic("GA-UNLEDGERED-SOURCE", INDEX_PATH, f"retained_source roles must exactly equal source-ledger paths; unledgered_roles={sorted(role_paths - ledger_paths)}, missing_roles={sorted(ledger_paths - role_paths)}."))
        return sorted(diagnostics, key=diagnostic_key)

    def check_index(self) -> None:
        index_path = self.absolute(INDEX_PATH)
        if not index_path.is_file():
            self.add("GA-INDEX-MISSING", INDEX_PATH, "Gate A evidence index is required for architecture completeness.")
            return
        raw = index_path.read_bytes()
        index_digest = digest_bytes(raw)
        self.index_binding = {"path": INDEX_PATH, "sha256": index_digest}
        index = self.read_json_contract(INDEX_PATH)
        if not isinstance(index, dict):
            return
        sidecar = self.absolute(SIDECAR_PATH)
        expected_sidecar = f"{index_digest}  {INDEX_PATH}\n".encode("utf-8")
        if not sidecar.is_file():
            self.add("GA-INDEX-SIDECAR", SIDECAR_PATH, "Index SHA-256 sidecar is missing.")
        elif sidecar.read_bytes() != expected_sidecar:
            self.add("GA-INDEX-SIDECAR", SIDECAR_PATH, "Index sidecar bytes do not exactly bind the current index.")
        if index.get("architecture_status") != "architecture_complete":
            self.add("GA-INDEX-STATUS", INDEX_PATH, "Candidate index must declare architecture_complete for a successful full validation.")
        self.diagnostics.extend(self.index_canonical_diagnostics(self.view))
        actual_artifacts = index.get("artifacts")
        self.check_summary["indexed_artifacts_checked"] = len(actual_artifacts) if isinstance(actual_artifacts, list) else 0

    def expected_fixture_summary(self) -> dict[str, Any]:
        entries = self.catalog.get("fixtures", []) if isinstance(self.catalog, dict) else []
        entries = entries if isinstance(entries, list) else []
        good = sum(1 for entry in entries if isinstance(entry, dict) and entry.get("classification") == "known_good")
        bad = sum(1 for entry in entries if isinstance(entry, dict) and entry.get("classification") == "known_bad")
        return {
            "catalog_id": "reiyah.fixture-catalog.gate-a",
            "total": len(entries),
            "known_good_total": good,
            "known_good_passed": good,
            "known_bad_total": bad,
            "known_bad_rejected_for_declared_rule": bad,
            "unexpected_outcomes": 0,
        }

    def expected_check_summary(self) -> dict[str, int]:
        ledger = self.read_json_contract(ACTIVE_SOURCE_LEDGER_PATH)
        records = ledger.get("records", []) if isinstance(ledger, dict) else []
        required_exercised = 0
        required_rejected = 0
        for entry in self.catalog.get("fixtures", []) if isinstance(self.catalog, dict) else []:
            if not isinstance(entry, dict) or entry.get("classification") != "known_good":
                continue
            relative = entry.get("path")
            if not isinstance(relative, str) or not relative.startswith("fixtures/v1.1/good/"):
                continue
            document = self.read_json_contract(relative)
            if isinstance(document, dict) and document.get("schema_id") in V11_APPLICATION_RULES:
                exercised, rejected, _ = self.v11_required_property_counts(document, relative)
                required_exercised += exercised
                required_rejected += rejected
        expected_raw, _ = self.canonical_index_output()
        indexed_count = 0
        if expected_raw is not None:
            try:
                expected_index = strict_json_loads(expected_raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError, StrictJSONError):
                expected_index = None
            if isinstance(expected_index, dict) and isinstance(expected_index.get("artifacts"), list):
                indexed_count = len(expected_index["artifacts"])
        return {
            "schemas_checked": len(list(self.root.rglob("schemas/**/*.schema.json"))),
            # Plan/catalog are validated once while loading and once as normative files;
            # source-records embedded by the ledger are dispatched individually.
            "normative_instances_checked": 2 + len(self.normative_json_paths()) + (len(records) if isinstance(records, list) else 0),
            "fixture_cases_checked": len(self.catalog.get("fixtures", [])) if isinstance(self.catalog.get("fixtures"), list) else 0,
            "retained_sources_checked": len(records) if isinstance(records, list) else 0,
            "indexed_artifacts_checked": indexed_count,
            "v11_required_properties_exercised": required_exercised,
            "v11_required_mutations_rejected": required_rejected,
        }

    def canonical_architecture_report(self, view: RepositoryView | None = None) -> dict[str, Any]:
        selected_view = view or self.view
        index_binding: dict[str, str] | None = None
        try:
            raw = selected_view.read_bytes(INDEX_PATH)
        except (OSError, ValueError):
            pass
        else:
            index_binding = {"path": INDEX_PATH, "sha256": digest_bytes(raw)}
        full_controls = {
            "required_control_ids": list(REQUIRED_CONTROL_IDS),
            "covered_control_ids": list(REQUIRED_CONTROL_IDS),
            "passed_control_ids": list(REQUIRED_CONTROL_IDS),
            "failed_control_ids": [],
            "external_control_summary": {
                "control_id": "GA-17",
                "status": "not_evaluated",
                "decision_record_id": None,
                "diagnostics": [],
            },
        }
        return build_report(
            mode="full",
            result="pass",
            exit_code=0,
            architecture_status="architecture_complete",
            index_binding=index_binding,
            diagnostics=[],
            fixture_summary=self.expected_fixture_summary(),
            check_summary=self.expected_check_summary(),
            control_summary=full_controls,
        )

    def validation_report_coverage_diagnostics(
        self,
        report: Any,
        relative: str,
        view: RepositoryView | None = None,
    ) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        if not isinstance(report, dict):
            return [make_diagnostic("GA-VALIDATION-REPORT-COVERAGE", relative, "Validation report is absent or malformed.")]
        expected_fixtures = self.expected_fixture_summary()
        expected_checks = self.expected_check_summary()
        if report.get("fixture_summary") != expected_fixtures:
            diagnostics.append(make_diagnostic("GA-VALIDATION-REPORT-COVERAGE", relative, f"Fixture summary does not equal current exact coverage counts; expected={expected_fixtures}."))
        if report.get("check_summary") != expected_checks:
            diagnostics.append(make_diagnostic("GA-VALIDATION-REPORT-COVERAGE", relative, f"Check summary does not equal current exact coverage counts; expected={expected_checks}."))
        required_pass_shape = {
            "mode": "full",
            "result": "pass",
            "exit_code": 0,
            "architecture_status": "architecture_complete",
            "offline": True,
            "read_only": True,
            "runtime_authorized": False,
            "acceptance_created": False,
        }
        for field, expected in required_pass_shape.items():
            if report.get(field) != expected:
                diagnostics.append(make_diagnostic("GA-VALIDATION-REPORT-COVERAGE", relative, f"Architecture report {field} must equal {expected!r}."))
        expected_control = self.canonical_architecture_report(view)["control_summary"]
        if report.get("control_summary") != expected_control:
            diagnostics.append(make_diagnostic("GA-VALIDATION-REPORT-COVERAGE", relative, "Architecture report does not show exact passed GA-01..GA-16 control coverage with GA-17 external."))
        if report.get("index_binding") != self.canonical_architecture_report(view).get("index_binding"):
            diagnostics.append(make_diagnostic("GA-VALIDATION-REPORT-COVERAGE", relative, "Architecture report does not bind the current evidence-index digest."))
        return sorted(diagnostics, key=diagnostic_key)

    def decision_history_diagnostics(
        self,
        records: list[tuple[str, dict[str, Any]]],
        view: RepositoryView | None = None,
    ) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        by_id: dict[str, tuple[str, dict[str, Any]]] = {}
        artifact_ids: dict[str, str] = {}
        times: dict[str, str] = {}
        parsed_times: dict[str, datetime] = {}
        sequences: dict[str, int] = {}
        for relative, record in records:
            record_id = record.get("record_id")
            artifact_id = record.get("artifact_id")
            decided_at = record.get("decided_at")
            if not isinstance(record_id, str) or not record_id:
                diagnostics.append(make_diagnostic("GA-DECISION-HISTORY", relative, "Decision history record_id is absent."))
                continue
            if record_id in by_id:
                diagnostics.append(make_diagnostic("GA-DECISION-HISTORY", relative, f"Duplicate decision record_id {record_id}.", record_id))
            by_id[record_id] = (relative, record)
            if not isinstance(artifact_id, str) or not artifact_id:
                diagnostics.append(make_diagnostic("GA-DECISION-HISTORY", relative, "Decision artifact_id is absent.", record_id))
            elif artifact_id in artifact_ids:
                diagnostics.append(make_diagnostic("GA-DECISION-HISTORY", relative, f"Duplicate decision artifact_id {artifact_id}.", record_id))
            else:
                artifact_ids[artifact_id] = record_id
            parsed = parse_exact_utc(decided_at)
            if parsed is None:
                diagnostics.append(make_diagnostic("GA-DECISION-HISTORY", relative, "decided_at must be an exact valid UTC timestamp ending in Z.", record_id))
            else:
                parsed_times[record_id] = parsed
            if isinstance(decided_at, str):
                if decided_at in times:
                    diagnostics.append(make_diagnostic("GA-DECISION-HISTORY", relative, f"Decision time {decided_at} is reused.", record_id))
                times[decided_at] = record_id
            sequence = record.get("decision_sequence")
            if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
                diagnostics.append(make_diagnostic("GA-DECISION-HISTORY", relative, "decision_sequence must be a positive integer.", record_id))
            else:
                if sequence in sequences.values():
                    diagnostics.append(make_diagnostic("GA-DECISION-HISTORY", relative, f"decision_sequence {sequence} is reused.", record_id))
                sequences[record_id] = sequence
            if record.get("history_policy") != "append_only_linear":
                diagnostics.append(make_diagnostic("GA-DECISION-HISTORY", relative, "history_policy must be append_only_linear.", record_id))

        roots: list[str] = []
        children: dict[str, list[str]] = {record_id: [] for record_id in by_id}
        for record_id, (relative, record) in by_id.items():
            prior = record.get("supersedes_record_id")
            if prior is None:
                roots.append(record_id)
                if sequences.get(record_id) != 1 or record.get("supersedes_record_sha256") is not None:
                    diagnostics.append(make_diagnostic("GA-DECISION-HISTORY", relative, "The sole root must be sequence 1 with null prior digest.", record_id))
            elif not isinstance(prior, str) or prior not in by_id:
                diagnostics.append(make_diagnostic("GA-DECISION-HISTORY", relative, f"supersedes_record_id does not resolve: {prior!r}.", record_id))
            else:
                children[prior].append(record_id)
                if prior in sequences and record_id in sequences and sequences[record_id] != sequences[prior] + 1:
                    diagnostics.append(make_diagnostic("GA-DECISION-HISTORY", relative, "A superseding decision sequence must be exactly prior sequence plus one.", record_id))
                prior_relative = by_id[prior][0]
                try:
                    prior_raw = (view or self.view).read_bytes(prior_relative)
                except (OSError, ValueError):
                    prior_raw = canonical_json_bytes(by_id[prior][1])
                if record.get("supersedes_record_sha256") != digest_bytes(prior_raw):
                    diagnostics.append(make_diagnostic("GA-DECISION-HISTORY", relative, "supersedes_record_sha256 does not bind exact prior decision bytes.", record_id))
                if prior in parsed_times and record_id in parsed_times and parsed_times[record_id] <= parsed_times[prior]:
                    diagnostics.append(make_diagnostic("GA-DECISION-HISTORY", relative, "A superseding decision must have a strictly later UTC decision time.", record_id))
        if records and len(roots) != 1:
            diagnostics.append(make_diagnostic("GA-DECISION-HISTORY", records[0][0], f"Decision history must contain exactly one root; found {sorted(roots)}."))
        branches = sorted(record_id for record_id, descendants in children.items() if len(descendants) > 1)
        if branches:
            diagnostics.append(make_diagnostic("GA-DECISION-HISTORY", by_id[branches[0]][0], f"Decision history branches at {branches}."))
        heads = sorted(record_id for record_id, descendants in children.items() if not descendants)
        if records and len(heads) != 1:
            diagnostics.append(make_diagnostic("GA-DECISION-HISTORY", records[0][0], f"Decision history must contain exactly one head; found {heads}."))
        if len(roots) == 1:
            visited: set[str] = set()
            current: str | None = roots[0]
            while current is not None and current not in visited:
                visited.add(current)
                descendants = children.get(current, [])
                current = descendants[0] if len(descendants) == 1 else None
            if visited != set(by_id):
                diagnostics.append(make_diagnostic("GA-DECISION-HISTORY", records[0][0], f"Decision history is cyclic, branched, or disconnected; unreachable={sorted(set(by_id) - visited)}."))
            elif {sequences.get(record_id) for record_id in visited} != set(range(1, len(visited) + 1)):
                diagnostics.append(make_diagnostic("GA-DECISION-HISTORY", records[0][0], f"Decision sequence values must be exactly 1..{len(visited)} along the chain."))
        return sorted(diagnostics, key=diagnostic_key)

    def actual_decision_diagnostics(self, view: RepositoryView) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        actual_paths = sorted(
            relative
            for relative in view.iter_files()
            if re.fullmatch(r"gate/decisions/[^/]+\.json", relative)
            and relative not in {LEGACY_TEMPLATE_PATH, V111_TEMPLATE_PATH, TEMPLATE_PATH}
        )
        if not actual_paths:
            return []
        ledger = self.read_view_json(view, "manifests/manifest-release-ledger.json")
        ledger_by_release = {
            entry.get("release_id"): entry.get("artifact_binding")
            for entry in ledger.get("entries", [])
            if isinstance(ledger, dict) and isinstance(entry, dict)
        } if isinstance(ledger, dict) else {}
        records: list[tuple[str, dict[str, Any]]] = []
        for relative in actual_paths:
            if not re.fullmatch(r"gate/decisions/reiyah\.gate-a-decision-[a-z0-9.-]+\.json", relative):
                diagnostics.append(make_diagnostic("GA-OPERATOR-DECISION-NAME", relative, "Actual decision path must exactly match gate/decisions/reiyah.gate-a-decision-<stable-suffix>.json."))
            record = self.read_view_json(view, relative)
            if not isinstance(record, dict):
                diagnostics.append(make_diagnostic("GA-ACCEPTANCE-REPLAY", relative, "Actual decision record is absent or malformed."))
                continue
            records.append((relative, record))
            diagnostics.extend(self.instance_diagnostics(record, relative))
        diagnostics.extend(self.decision_history_diagnostics(records, view))

        for relative, record in records:
            record_id = record.get("record_id") if isinstance(record.get("record_id"), str) else None
            if record.get("is_template") is not False:
                diagnostics.append(make_diagnostic("GA-ACCEPTANCE-REPLAY", relative, "Actual decision record is still marked as a template.", record_id))
            for field in ("artifact_id", "record_id"):
                value = record.get(field)
                if not isinstance(value, str) or re.search(r"(?:replace|placeholder|\bTBD\b|\bTODO\b)", value, re.IGNORECASE):
                    diagnostics.append(make_diagnostic("GA-ACCEPTANCE-REPLAY", relative, f"Decision {field} must be a non-placeholder stable identifier.", record_id))
            meaningful_fields = {
                "operator_identity": 3,
                "authority_basis": 20,
                "rationale": 40,
            }
            for field, minimum in meaningful_fields.items():
                value = record.get(field)
                placeholder = isinstance(value, str) and re.search(r"(?:replace|placeholder|\bTBD\b|\bTODO\b)", value, re.IGNORECASE)
                if not isinstance(value, str) or len(value.strip()) < minimum or placeholder:
                    diagnostics.append(make_diagnostic("GA-ACCEPTANCE-REPLAY", relative, f"Decision {field} must contain meaningful non-placeholder text of at least {minimum} characters.", record_id))

            packet_version = record.get("schema_version")
            spec = DECISION_PACKET_SPECS.get(packet_version) if isinstance(packet_version, str) else None
            if (
                spec is None
                or record.get("schema_id") != f"https://schemas.reiyah.invalid/gate-a/{packet_version}/operator-decision-record.schema.json"
                or record.get("version") != packet_version
            ):
                diagnostics.append(make_diagnostic("GA-ACCEPTANCE-REPLAY", relative, "Decision must use one exact supported versioned operator-decision contract.", record_id))
                continue
            try:
                packet_index_raw = view.read_bytes(spec["index_physical_path"])
            except (OSError, ValueError):
                packet_index_raw = None
            expected_index_digest = digest_bytes(packet_index_raw) if packet_index_raw is not None else None
            if packet_version == "1.1.1" and expected_index_digest != spec["index_sha256"]:
                expected_index_digest = None
                diagnostics.append(make_diagnostic("GA-ACCEPTANCE-REPLAY", relative, "The historical 1.1.1 decision packet index is absent or no longer byte-exact.", record_id))
            expected_index_reference = {
                "artifact_id": spec["index_artifact_id"],
                "path": INDEX_PATH,
                "sha256": expected_index_digest,
                "schema_id": spec["index_schema_id"],
                "version": packet_version,
            }
            index_bindings = [binding for binding in record.get("artifact_bindings", []) if isinstance(binding, dict) and binding.get("path") == INDEX_PATH]
            architecture_binding = record.get("architecture_completeness_binding", {})
            if index_bindings != [expected_index_reference] or architecture_binding != expected_index_reference:
                diagnostics.append(make_diagnostic("GA-ACCEPTANCE-REPLAY", relative, f"Decision does not exactly bind the canonical {packet_version} packet index in both required locations.", record_id))
            release_bindings = record.get("manifest_release_bindings", [])
            observed_release_ids: set[str] = set()
            for release_binding in release_bindings:
                if not isinstance(release_binding, dict):
                    continue
                release_id = release_binding.get("release_id")
                artifact = release_binding.get("artifact")
                observed_release_ids.add(release_id)
                if ledger_by_release.get(release_id) != artifact:
                    diagnostics.append(make_diagnostic("GA-ACCEPTANCE-REPLAY", relative, f"Manifest release binding does not match ledger for {release_id}.", record_id))
            if observed_release_ids != set(ledger_by_release):
                diagnostics.append(make_diagnostic("GA-ACCEPTANCE-REPLAY", relative, "Decision does not bind exactly every mission/protocol release.", record_id))
            report_binding = record.get("validation_report_binding")
            try:
                report_raw = view.read_bytes(spec["report_path"])
            except (OSError, ValueError):
                report_raw = None
            report_digest = digest_bytes(report_raw) if report_raw is not None else None
            expected_report_reference = {
                "artifact_id": spec["report_artifact_id"],
                "path": spec["report_path"],
                "sha256": report_digest,
                "schema_id": spec["report_schema_id"],
                "version": packet_version,
            }
            if packet_version == "1.1.1" and report_digest != spec["report_sha256"]:
                diagnostics.append(make_diagnostic("GA-ACCEPTANCE-REPLAY", relative, "The historical 1.1.1 validation report is absent or no longer byte-exact.", record_id))
            if report_binding != expected_report_reference or report_raw is None:
                diagnostics.append(make_diagnostic("GA-ACCEPTANCE-REPLAY", relative, f"Decision lacks the exact {packet_version} validation-report binding.", record_id))
                continue
            try:
                report = strict_json_loads(report_raw.decode("utf-8"))
            except DuplicateJSONKeyError as exc:
                report = None
                diagnostics.append(make_diagnostic("GA-JSON-DUPLICATE-KEY", spec["report_path"], f"Bound validation report JSON member names must be unique: {exc}", record_id))
            except NonFiniteJSONError as exc:
                report = None
                diagnostics.append(make_diagnostic("GA-NONFINITE-NUMBER", spec["report_path"], f"Bound validation report JSON numbers must be finite: {exc}", record_id))
            except (UnicodeDecodeError, json.JSONDecodeError):
                report = None
            if isinstance(report, dict):
                diagnostics.extend(self.instance_diagnostics(report, spec["report_path"]))
            if packet_version == "1.1.2":
                expected_report = self.canonical_architecture_report(view)
                expected_report_raw = (json.dumps(expected_report, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
                diagnostics.extend(self.validation_report_coverage_diagnostics(report, spec["report_path"], view))
                if not isinstance(report, dict) or report != expected_report or report_raw != expected_report_raw:
                    diagnostics.append(make_diagnostic("GA-ACCEPTANCE-REPLAY", relative, "Bound 1.1.2 validation report is not semantically identical to a freshly generated, decision-independent full report for the current index.", record_id))
        return sorted(diagnostics, key=diagnostic_key)

    def check_actual_decisions(self) -> None:
        self.diagnostics.extend(self.actual_decision_diagnostics(self.view))

    def check_current_report_coverage(self) -> None:
        expected_fixtures = self.expected_fixture_summary()
        expected_checks = self.expected_check_summary()
        if self.fixture_summary != expected_fixtures:
            self.add("GA-VALIDATION-REPORT-COVERAGE", CATALOG_PATH, f"Live fixture coverage does not equal exact expected counts; expected={expected_fixtures}, actual={self.fixture_summary}.")
        if self.check_summary != expected_checks:
            self.add("GA-VALIDATION-REPORT-COVERAGE", PLAN_PATH, f"Live validation coverage does not equal exact expected counts; expected={expected_checks}, actual={self.check_summary}.")
        if self.covered_control_ids != set(REQUIRED_CONTROL_IDS):
            self.add("GA-VALIDATION-REPORT-COVERAGE", PLAN_PATH, f"Covered architecture controls must be exactly GA-01..GA-16; missing={sorted(set(REQUIRED_CONTROL_IDS) - self.covered_control_ids)}.")

    def diagnostic_controls(self, diagnostic: dict[str, Any]) -> set[str]:
        rule_controls = {
            rule.get("rule_id"): {
                control
                for control in rule.get("gate_controls", [])
                if isinstance(control, str) and control in set(REQUIRED_CONTROL_IDS) | {"GA-17"}
            }
            for rule in self.plan.get("rules", [])
            if isinstance(rule, dict) and isinstance(rule.get("rule_id"), str)
        } if isinstance(self.plan, dict) else {}
        rule_id = diagnostic.get("rule_id")
        controls = set(rule_controls.get(rule_id, set()))
        if rule_id == "GA-OPERATOR-DECISION-NAME":
            controls.add("GA-17")
        if controls == {"GA-17"}:
            return controls
        path = diagnostic.get("path")
        if isinstance(path, str):
            for control_id, evidence_paths in CONTROL_EVIDENCE.items():
                if any(path == evidence_path or path.startswith(evidence_path.removesuffix("/") + "/") for evidence_path in evidence_paths):
                    controls.add(control_id)
        if not controls:
            controls.add("GA-14")
        return controls

    def architecture_diagnostics(self) -> list[dict[str, Any]]:
        return [
            diagnostic
            for diagnostic in self.diagnostics
            if self.diagnostic_controls(diagnostic) & set(REQUIRED_CONTROL_IDS)
        ]

    def control_summary(self) -> dict[str, Any]:
        failed: set[str] = set()
        for diagnostic in self.diagnostics:
            failed.update(self.diagnostic_controls(diagnostic) & set(REQUIRED_CONTROL_IDS))
        covered = set(self.covered_control_ids)
        passed = covered - failed
        return {
            "required_control_ids": list(REQUIRED_CONTROL_IDS),
            "covered_control_ids": [control for control in REQUIRED_CONTROL_IDS if control in covered],
            "passed_control_ids": [control for control in REQUIRED_CONTROL_IDS if control in passed],
            "failed_control_ids": [control for control in REQUIRED_CONTROL_IDS if control in failed],
            "external_control_summary": {
                "control_id": "GA-17",
                # Repository bytes can prove internal structure and digest integrity, but
                # cannot authenticate external operator authority.  The offline validator
                # therefore never upgrades, rejects, or otherwise evaluates GA-17.
                "status": "not_evaluated",
                "decision_record_id": None,
                "diagnostics": [],
            },
        }

    def execute_validation(self) -> None:
        self.validate_schema_definitions()
        self.load_plan_and_catalog()
        self.check_toolchain()
        if self.fixture_only:
            self.run_fixtures()
            return
        self.check_required_artifacts()
        self.check_gate_control_coverage()
        self.validate_normative_instances()
        self.check_operator_template()
        self.check_vocabulary_bindings()
        self.check_manifest_releases()
        self.check_research_function_registry()
        self.check_scientific_contract_profile()
        self.check_sources_and_crosswalk()
        self.check_public_custody()
        self.check_predecessor_packet_drift()
        self.check_narrative_bindings()
        self.diagnostics.extend(self.mission_boundary_diagnostics(self.view))
        self.diagnostics.extend(self.threat_coverage_diagnostics(self.view))
        self.check_global_scientific_semantics()
        self.check_normative_measurements()
        self.run_fixtures()
        self.check_markdown_links()
        self.check_scope_inventory()
        self.check_index()
        self.check_current_report_coverage()
        self.diagnostics.extend(self.operator_decision_contract_diagnostics(self.view, end_to_end=True))
        self.check_actual_decisions()


def verify_identity_before_repository_read() -> None:
    cwd = Path.cwd().resolve()
    script_root = Path(__file__).resolve().parent.parent
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
        raise ExecutionFailure(f"cannot resolve Git root: {exc}", "AGENTS.md") from exc
    git_root = completed.stdout.strip()
    if completed.returncode != 0:
        git_root = ""
    diagnostics = identity_authority_diagnostics(
        {
            "named_project": "Reiyah",
            "working_directory": str(cwd),
            "git_root": git_root,
            "instruction_project": "Reiyah",
            "script_root": str(script_root),
        }
    )
    if diagnostics:
        raise IdentityFailure(diagnostics[0])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("human", "json"), default="human")
    parser.add_argument("--fixture-only", action="store_true")
    return parser.parse_args()


def emit_report(report: dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n")
        return
    if report["result"] == "pass":
        if report["mode"] == "fixture_only":
            print(
                "PASS: all "
                f"{report['fixture_summary']['known_good_total']} known-good fixtures passed and all "
                f"{report['fixture_summary']['known_bad_total']} known-bad fixtures failed for their declared rule."
            )
        else:
            binding = report.get("index_binding") or {}
            print(f"PASS: Gate A architecture is internally complete for {binding.get('sha256')}.")
        print("Operator acceptance created: false")
        return
    print(f"{report['result'].upper()}: {len(report['diagnostics'])} diagnostic(s).")
    for diagnostic in report["diagnostics"]:
        identifier = f" [{diagnostic['object_id']}]" if diagnostic["object_id"] else ""
        print(f"{diagnostic['rule_id']} {diagnostic['path']}{identifier}: {diagnostic['message']}")
    print("Operator acceptance created: false")


def execution_error_report(mode: str, failure: Exception) -> dict[str, Any]:
    path = failure.path if isinstance(failure, ExecutionFailure) else "tools/validate_gate_a.py"
    diagnostics = [failure.diagnostic] if isinstance(failure, IdentityFailure) else [make_diagnostic("GA-EXECUTION-INTERNAL", path, str(failure))]
    return build_report(
        mode=mode,
        result="execution_error",
        exit_code=2,
        architecture_status="not_evaluated",
        index_binding=None,
        diagnostics=diagnostics,
        fixture_summary=empty_fixture_summary(),
        check_summary=empty_check_summary(),
        control_summary=empty_control_summary(),
    )


def main() -> int:
    args = parse_args()
    mode = "fixture_only" if args.fixture_only else "full"
    if DEPENDENCY_IMPORT_ERROR is not None:
        report = execution_error_report(mode, ExecutionFailure(f"missing local validation dependency: {DEPENDENCY_IMPORT_ERROR}"))
        emit_report(report, args.format)
        return 2
    try:
        verify_identity_before_repository_read()
        validator = GateAValidator(CANONICAL_ROOT, args.fixture_only)
        validator.execute_validation()
        diagnostics = sorted(validator.diagnostics, key=diagnostic_key)
        if diagnostics:
            result = "fail"
            exit_code = 1
        else:
            result = "pass"
            exit_code = 0
        if args.fixture_only:
            architecture_status = "not_evaluated"
        else:
            architecture_status = "invalid" if validator.architecture_diagnostics() else "architecture_complete"
        report = build_report(
            mode=mode,
            result=result,
            exit_code=exit_code,
            architecture_status=architecture_status,
            index_binding=None if args.fixture_only else validator.index_binding,
            diagnostics=diagnostics,
            fixture_summary=validator.fixture_summary,
            check_summary=validator.check_summary,
            control_summary=validator.control_summary(),
        )
        report_schema_id = report["schema_id"]
        report_validator = Draft202012Validator(
            validator.schemas[report_schema_id],
            registry=validator.registry,
            format_checker=validator.format_checker,
        )
        report_errors = sorted(report_validator.iter_errors(report), key=lambda error: (tuple(str(part) for part in error.absolute_path), error.message))
        if report_errors:
            details = "; ".join(f"{json_pointer(error.absolute_path)}: {error.message}" for error in report_errors[:5])
            raise ExecutionFailure(f"validator emitted a report that violates its schema: {details}")
    except Exception as exc:
        failure = exc if isinstance(exc, ExecutionFailure) else ExecutionFailure(f"unhandled validator error: {type(exc).__name__}: {exc}")
        report = execution_error_report(mode, failure)
        exit_code = 2
    emit_report(report, args.format)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
