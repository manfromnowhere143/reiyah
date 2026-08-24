#!/usr/bin/env python3
# Copyright 2026 Daniel Wahnich
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed validation substrate for the Reiyah Gate A 1.2.0 packet.

This program is intentionally independent from the legacy Gate A validators.  It
does not implement product behavior or scientific acceptance.  It establishes a
read-only execution profile, takes one development snapshot or two separately
loaded release snapshots in fresh isolated worker interpreters, verifies a
byte-level toolchain lock, supplies deterministic JSON Schema format predicates,
and replays validator-security fixtures.

Supported invocations use the byte-bound external launcher, which enters Seatbelt
before CPython starts and then selects CPython's isolated, no-site, no-bytecode
profile:

    tools/gate_a_1_2_0.sh --snapshot-mode development --output human

    tools/gate_a_1_2_0.sh --snapshot-mode release --output json

Development mode is never release evidence.  Release mode requires an immutable
Git tree and a completely clean worktree, including no untracked paths.
"""

# E402 is intentionally exempted only for this module: the fail-closed
# interpreter-profile and external-Seatbelt probes must execute before any
# non-built-in import can load owner-writable code.
# ruff: noqa: E402

from __future__ import annotations

import sys


def _fail_before_imports(message: str) -> "NoReturn":
    sys.stderr.write(f"gate_a_1_2_0 bootstrap error: {message}\n")
    raise SystemExit(2)


_flags = sys.flags
if not (
    _flags.isolated == 1
    and _flags.ignore_environment == 1
    and _flags.no_user_site == 1
    and _flags.no_site == 1
    and _flags.safe_path
    and _flags.dont_write_bytecode == 1
):
    _fail_before_imports("unsupported interpreter profile; use tools/gate_a_1_2_0.sh")


# The canonical launcher applies the same policy before CPython loads any
# owner-writable standard-library module.  This built-in-only probe must run
# before importing even ctypes; direct Python invocation is unsupported.
try:
    _external_probe = open(__file__, "r+b", buffering=0)
except PermissionError as _external_probe_error:
    if _external_probe_error.errno != 1:
        _fail_before_imports(
            f"external Seatbelt write probe returned errno {_external_probe_error.errno}"
        )
else:
    _external_probe.close()
    _fail_before_imports("external Seatbelt launcher is absent or ineffective")


import ctypes


_EARLY_SEATBELT_PROFILE = (
    b"(version 1)\n"
    b"(allow default)\n"
    b"(deny network*)\n"
    b"(deny file-write*)\n"
    b'(allow file-write-data (literal "/dev/null"))'
)


def _verify_early_external_seatbelt() -> None:
    try:
        _sandbox_library = ctypes.CDLL("/usr/lib/libsandbox.dylib")
        _sandbox_check = _sandbox_library.sandbox_check
        _sandbox_check.restype = ctypes.c_int
    except OSError as _sandbox_error:
        _fail_before_imports(f"cannot load macOS Seatbelt API: {_sandbox_error}")
    _current_pid = ctypes.CDLL(None).getpid()
    for _operation in (
        b"network-bind",
        b"network-outbound",
        b"file-write-create",
        b"file-write-data",
        b"file-write-mode",
        b"file-write-unlink",
        b"file-write-xattr",
    ):
        if _sandbox_check(_current_pid, _operation, 0) != 1:
            _fail_before_imports(
                f"external Seatbelt does not deny {_operation.decode('ascii')}"
            )


_verify_early_external_seatbelt()


import argparse
import copy
import csv
import errno
import hashlib
import ipaddress
import io
import json
import math
import os
import plistlib
import re
import socket
import stat
import subprocess
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Callable, Mapping, NoReturn, Sequence
from urllib.parse import urlsplit


ARTIFACT_VERSION = "1.2.0"
PROTOCOL_RELEASE_ID = "reiyah.protocol.harbor-gate-a@1.2.0"
MISSION_RELEASE_ID = "reiyah.mission@1.1.0"
CANONICAL_ROOT = Path("/Users/danielwahnich/workspace/reiyah")
TOOL_PATH = "tools/gate_a_1_2_0.py"
LAUNCHER_PATH = "tools/gate_a_1_2_0.sh"
SCIENCE_MODULE_PATH = "tools/gate_a_1_2_0_science.py"
LOCK_PATH = "validation/toolchain-lock-1.2.0.json"
PLAN_PATH = "validation/validation-plan.json"
PLAN_SCHEMA_PATH = "schemas/validation-plan-1.2.schema.json"
INDEX_SCHEMA_PATH = "schemas/gate-a-index-1.2.schema.json"
REPORT_SCHEMA_PATH = "schemas/validation-report-1.2.schema.json"
COMMON_SCHEMA_PATH = "schemas/common-1.2.schema.json"
SECURITY_FIXTURE_PREFIX = "fixtures/v1.2/known-bad/validator-security-"
GOVERNANCE_FIXTURE_PREFIX = "fixtures/v1.2/known-bad/governance-"
GOVERNANCE_GOOD_PREFIX = "fixtures/v1.2/governance-good/"
GOVERNANCE_BASELINE_PREFIX = "fixtures/v1.2/governance/"
PUBLICATION_EVENT_BASELINE_PATH = (
    "fixtures/v1.2/governance/publication-event-synthetic-baseline.json"
)
TRANSPORT_OBSERVATION_BASELINE_PATH = (
    "fixtures/v1.2/governance/transport-observation-synthetic-baseline.json"
)
GOVERNANCE_POSITIVE_SCHEMA_PATH = "schemas/governance-positive-fixture-1.2.schema.json"
PUBLICATION_EVENT_SCHEMA_PATH = "schemas/publication-event-fixture-1.2.schema.json"
PUBLICATION_EVENT_MUTATION_SCHEMA_PATH = (
    "schemas/publication-event-mutation-fixture-1.2.schema.json"
)
TRANSPORT_OBSERVATION_SCHEMA_PATH = (
    "schemas/transport-observation-fixture-1.2.schema.json"
)
TRANSPORT_OBSERVATION_MUTATION_SCHEMA_PATH = (
    "schemas/transport-observation-mutation-fixture-1.2.schema.json"
)
RIGHTS_CAPTURE_SCHEMA_PATH = "schemas/rights-observation-capture-1.2.schema.json"
PUBLIC_RIGHTS_SCHEMA_PATH = "schemas/public-rights-revalidation-1.2.schema.json"
PUBLIC_DISTRIBUTION_RECEIPT_SCHEMA_PATH = (
    "schemas/public-distribution-receipt-1.2.schema.json"
)
ACTUAL_PUBLIC_RIGHTS_PATH = (
    "evidence/public-rights-revalidation-2026-08-25-gate-a-static-correction-1.2.0.json"
)
ACTUAL_PUBLIC_RECEIPT_PATH = (
    "gate/public-distribution-receipts/reiyah.public-distribution-receipt-1.2.0.json"
)
SCIENCE_SCHEMA_PATHS = (
    "schemas/v1.2/evaluation-assurance-bundle.schema.json",
    "schemas/v1.2/human-automation-assessment.schema.json",
    "schemas/v1.2/joint-performance-evaluation.schema.json",
    "schemas/v1.2/scientific-contract-common.schema.json",
    "schemas/v1.2/scientific-contract-mutation-fixture.schema.json",
    "schemas/v1.2/sequential-off-policy-evaluation.schema.json",
    "schemas/v1.2/study-design-preregistration.schema.json",
)
SCIENCE_GOOD_PREFIX = "fixtures/v1.2/good/"
SCIENCE_BAD_PREFIX = "fixtures/v1.2/known-bad/"
PROTOCOL_MANIFEST_PATH = "manifests/protocol/harbor-gate-a-protocol-1.2.0.json"
DEFINITION_REGISTRY_PATH = (
    "manifests/definitions/harbor-gate-a-definition-registry-1.2.0.json"
)
SCIENTIFIC_PROFILE_PATH = (
    "manifests/scientific/harbor-scientific-contract-profile-1.2.0.json"
)
RESEARCH_REGISTRY_PATH = (
    "manifests/research/harbor-research-function-registry-1.2.0.json"
)

NARRATIVE_CANDIDATE_MARKERS = MappingProxyType(
    {
        "README.md": "Gate A `1.2.0` is an operator-unaccepted correction candidate.",
        "docs/GATE_A_1_2_0_CONSISTENCY_REVIEW.md": (
            "Every disposition recorded here is the pre-replay state `open`."
        ),
        "docs/SESSION_HANDOFF.md": (
            "Gate A `1.2.0` remains operator-unaccepted; architecture status must be "
            "resolved from the exact canonical report and repeated byte-identical release replay."
        ),
    }
)

NORMATIVE_MARKDOWN_SURFACE: Mapping[str, str] = MappingProxyType(
    {
        "AGENTS.md": (
            "Gate A authorizes architecture and deterministic evaluation fixtures "
            "and validators only."
        ),
        "docs/SCIENTIFIC_CHARTER.md": (
            "This charter is not evidence of scientific validity"
        ),
        "docs/CLAIMS_AND_NON_CLAIMS.md": (
            "Operational, safety, compliance, and superiority claims"
        ),
        "docs/PRE_IMPLEMENTATION_GATE.md": (
            "Gate A does **not** approve a product, runtime"
        ),
        "docs/ARCHITECTURE.md": "| Runtime authorization | None |",
        "docs/MATHEMATICAL_SPECIFICATION.md": "It does not implement",
        "docs/THREAT_MODEL.md": "There is no product runtime",
        "docs/VALIDATION.md": "It does not train or execute a model",
    }
)

# These tables are executable dispatch declarations, not evidence.  The closed
# validation plan must name this exact producer/selector surface before the
# stage collector is allowed to emit S03 or the coverage resolver is allowed to
# emit S16.  Keeping the declarations independent of the plan prevents a plan
# edit from silently inventing a producer or evidence selector.
STAGE_PRODUCER_DISPATCH: Mapping[str, str] = MappingProxyType(
    {
        "reiyah.stage-evidence.snapshot-release-projection@1.2.0": "GA12-STAGE-RELEASE-PROJECTION",
        "reiyah.stage-evidence.toolchain-pre-post-integrity@1.2.0": "GA12-STAGE-TOOLCHAIN-INTEGRITY",
        "reiyah.stage-evidence.validation-plan-contract@1.2.0": "GA12-STAGE-PLAN-CONTRACT",
        "reiyah.stage-evidence.predecessor-inheritance@1.2.0": "GA12-STAGE-PREDECESSOR-INHERITANCE",
        "reiyah.stage-evidence.repository-authority-and-normative-architecture@1.2.0": "GA12-STAGE-NORMATIVE-ARCHITECTURE",
        "reiyah.stage-evidence.manifest-lineage@1.2.0": "GA12-STAGE-MANIFEST-LINEAGE",
        "reiyah.stage-evidence.source-and-standards-custody@1.2.0": "GA12-STAGE-SOURCE-STANDARDS-CUSTODY",
        "reiyah.stage-evidence.threat-and-no-runtime-boundary@1.2.0": "GA12-STAGE-THREAT-NO-RUNTIME",
        "reiyah.stage-evidence.schema-and-format-corpus@1.2.0": "GA12-STAGE-SCHEMA-FORMAT-CORPUS",
        "reiyah.stage-evidence.scientific-contract-replay@1.2.0": "GA12-STAGE-SCIENTIFIC-CONTRACT-REPLAY",
        "reiyah.stage-evidence.scientific-profile-and-reference-inventory@1.2.0": "GA12-STAGE-SCIENTIFIC-PROFILE-REFERENCES",
        "reiyah.stage-evidence.publication-governance-replay@1.2.0": "GA12-STAGE-PUBLICATION-GOVERNANCE",
        "reiyah.stage-evidence.transport-governance-replay@1.2.0": "GA12-STAGE-TRANSPORT-GOVERNANCE",
        "reiyah.stage-evidence.validator-security-replay@1.2.0": "GA12-STAGE-VALIDATOR-SECURITY",
        "reiyah.stage-evidence.fixture-catalog-reconciliation@1.2.0": "GA12-STAGE-FIXTURE-CATALOG",
        "reiyah.stage-evidence.rule-control-threat-coverage@1.2.0": "GA12-STAGE-RULE-CONTROL-THREAT-COVERAGE",
        "reiyah.stage-evidence.narrative-candidate-nonclaim@1.2.0": "GA12-STAGE-NARRATIVE-NONCLAIM",
        "reiyah.stage-evidence.canonical-index-readback@1.2.0": "GA12-STAGE-CANONICAL-INDEX",
        "reiyah.stage-evidence.report-implication-engine@1.2.0": "GA12-STAGE-REPORT-IMPLICATIONS",
        "reiyah.stage-evidence.dual-release-evaluation-match@1.2.0": "GA12-STAGE-DUAL-RELEASE-EVALUATION",
    }
)

STAGE_OBSERVATION_DISPATCH: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "reiyah.stage-evidence.snapshot-release-projection@1.2.0": (
            "reiyah.stage-observation.candidate-projection-inventory@1.2.0",
        ),
        "reiyah.stage-evidence.toolchain-pre-post-integrity@1.2.0": (
            "reiyah.stage-observation.toolchain-pre-post-integrity@1.2.0",
        ),
        "reiyah.stage-evidence.validation-plan-contract@1.2.0": (
            "reiyah.stage-observation.validation-plan-closed-contract@1.2.0",
        ),
        "reiyah.stage-evidence.predecessor-inheritance@1.2.0": (
            "reiyah.stage-observation.predecessor-inheritance-reconciliation@1.2.0",
        ),
        "reiyah.stage-evidence.repository-authority-and-normative-architecture@1.2.0": (
            "reiyah.stage-observation.repository-authority-normative-architecture@1.2.0",
        ),
        "reiyah.stage-evidence.manifest-lineage@1.2.0": (
            "reiyah.stage-observation.manifest-lineage-append-only@1.2.0",
        ),
        "reiyah.stage-evidence.source-and-standards-custody@1.2.0": (
            "reiyah.stage-observation.source-standards-custody-reconciliation@1.2.0",
        ),
        "reiyah.stage-evidence.threat-and-no-runtime-boundary@1.2.0": (
            "reiyah.stage-observation.threat-no-runtime-boundary@1.2.0",
        ),
        "reiyah.stage-evidence.schema-and-format-corpus@1.2.0": (
            "reiyah.stage-observation.schema-format-corpus-replay@1.2.0",
        ),
        "reiyah.stage-evidence.scientific-contract-replay@1.2.0": (
            "reiyah.stage-observation.scientific-good-bad-replay@1.2.0",
        ),
        "reiyah.stage-evidence.scientific-profile-and-reference-inventory@1.2.0": (
            "reiyah.stage-observation.profile-reference-inventory-reconciliation@1.2.0",
        ),
        "reiyah.stage-evidence.publication-governance-replay@1.2.0": (
            "reiyah.stage-observation.publication-governance-replay@1.2.0",
        ),
        "reiyah.stage-evidence.transport-governance-replay@1.2.0": (
            "reiyah.stage-observation.transport-governance-replay@1.2.0",
        ),
        "reiyah.stage-evidence.validator-security-replay@1.2.0": (
            "reiyah.stage-observation.validator-security-replay@1.2.0",
        ),
        "reiyah.stage-evidence.fixture-catalog-reconciliation@1.2.0": (
            "reiyah.stage-observation.fixture-catalog-filesystem-reconciliation@1.2.0",
        ),
        "reiyah.stage-evidence.rule-control-threat-coverage@1.2.0": (
            "reiyah.stage-observation.rule-control-threat-exact-coverage@1.2.0",
        ),
        "reiyah.stage-evidence.narrative-candidate-nonclaim@1.2.0": (
            "reiyah.stage-observation.narrative-candidate-nonclaim-reconciliation@1.2.0",
        ),
        "reiyah.stage-evidence.canonical-index-readback@1.2.0": (
            "reiyah.stage-observation.canonical-index-byte-readback@1.2.0",
        ),
        "reiyah.stage-evidence.report-implication-engine@1.2.0": (
            "reiyah.stage-observation.report-implication-canary-replay@1.2.0",
        ),
        "reiyah.stage-evidence.dual-release-evaluation-match@1.2.0": (
            "reiyah.stage-observation.two-release-evaluations-byte-identical@1.2.0",
        ),
    }
)

EXECUTABLE_NESTED_CONTRACT_IDS = (
    "reiyah.executable-contract.ope-policy-distribution",
    "reiyah.executable-contract.causal-identification",
    "reiyah.executable-contract.readiness-unknown-propagation",
    "reiyah.executable-contract.recovery-event-derivation",
    "reiyah.executable-contract.transfer-eligibility",
    "reiyah.executable-contract.conformal-guarantee-disposition",
    "reiyah.executable-contract.ood-population-partition",
    "reiyah.executable-contract.worst-group-eligibility",
    "reiyah.executable-contract.human-belief-observation-decision-reconciliation",
    "reiyah.executable-contract.joint-silent-miss-identifiability",
    "reiyah.executable-contract.assumption-evidence-eligibility",
)
NESTED_CONTRACT_PRODUCER_DISPATCH: Mapping[str, str] = MappingProxyType(
    {
        **{
            contract_id: "GA12-STAGE-SCIENTIFIC-CONTRACT-REPLAY"
            for contract_id in EXECUTABLE_NESTED_CONTRACT_IDS
        },
        "reiyah.cross-cutting-contract.lifecycle-history-integrity": "GA12-STAGE-SCIENTIFIC-CONTRACT-REPLAY",
        "reiyah.cross-cutting-contract.typed-reference-integrity": "GA12-STAGE-SCIENTIFIC-PROFILE-REFERENCES",
        "reiyah.cross-cutting-contract.architecture-nonclaim-boundary": "GA12-STAGE-SCIENTIFIC-PROFILE-REFERENCES",
    }
)

EVIDENCE_SELECTOR_PRODUCER_DISPATCH: Mapping[str, str] = MappingProxyType(
    {
        "reiyah.evidence-selector.science.belief-reconciliation": "GA12-STAGE-SCIENTIFIC-CONTRACT-REPLAY",
        "reiyah.evidence-selector.science.observation-validity-reconciliation": "GA12-STAGE-SCIENTIFIC-CONTRACT-REPLAY",
        "reiyah.evidence-selector.science.causal-preregistration": "GA12-STAGE-SCIENTIFIC-CONTRACT-REPLAY",
        "reiyah.evidence-selector.science.readiness-recovery": "GA12-STAGE-SCIENTIFIC-CONTRACT-REPLAY",
        "reiyah.evidence-selector.science.ope-closure": "GA12-STAGE-SCIENTIFIC-CONTRACT-REPLAY",
        "reiyah.evidence-selector.science.joint-silent-miss": "GA12-STAGE-SCIENTIFIC-CONTRACT-REPLAY",
        "reiyah.evidence-selector.science.ood-worst-group": "GA12-STAGE-SCIENTIFIC-CONTRACT-REPLAY",
        "reiyah.evidence-selector.science.transfer-conformal-assumption": "GA12-STAGE-SCIENTIFIC-CONTRACT-REPLAY",
        "reiyah.evidence-selector.governance.publication-static-interface": "GA12-STAGE-PUBLICATION-GOVERNANCE",
        "reiyah.evidence-selector.governance.transport-static-interface": "GA12-STAGE-TRANSPORT-GOVERNANCE",
        "reiyah.evidence-selector.security.execution-integrity": "GA12-STAGE-VALIDATOR-SECURITY",
        "reiyah.evidence-selector.security.fixture-catalog-integrity": "GA12-STAGE-VALIDATOR-SECURITY",
        "reiyah.evidence-selector.security.narrative-nonclaim": "GA12-STAGE-VALIDATOR-SECURITY",
        "reiyah.evidence-selector.security.reference-path-coverage": "GA12-STAGE-VALIDATOR-SECURITY",
        "reiyah.evidence-selector.security.report-implications": "GA12-STAGE-REPORT-IMPLICATIONS",
        "reiyah.evidence-selector.security.science-lineage": "GA12-STAGE-VALIDATOR-SECURITY",
        "reiyah.evidence-selector.security.successor-chronology": "GA12-STAGE-VALIDATOR-SECURITY",
        "reiyah.evidence-selector.security.transport-self-attestation": "GA12-STAGE-VALIDATOR-SECURITY",
    }
)

ASSURANCE_APPLICATION_SCHEMA_ID = (
    "https://schemas.reiyah.invalid/scientific-contract/1.2.0/"
    "evaluation-assurance-bundle.schema.json"
)
HUMAN_APPLICATION_SCHEMA_ID = (
    "https://schemas.reiyah.invalid/scientific-contract/1.2.0/"
    "human-automation-assessment.schema.json"
)
JOINT_APPLICATION_SCHEMA_ID = (
    "https://schemas.reiyah.invalid/scientific-contract/1.2.0/"
    "joint-performance-evaluation.schema.json"
)
OPE_APPLICATION_SCHEMA_ID = (
    "https://schemas.reiyah.invalid/scientific-contract/1.2.0/"
    "sequential-off-policy-evaluation.schema.json"
)
STUDY_APPLICATION_SCHEMA_ID = (
    "https://schemas.reiyah.invalid/scientific-contract/1.2.0/"
    "study-design-preregistration.schema.json"
)

EXECUTABLE_CONTRACT_MATRIX_METADATA_KEYS = (
    "contract_id",
    "contract_kind",
    "version",
    "derivation_authority",
)
EXECUTABLE_CONTRACT_MATRIX_TARGETS: Mapping[str, tuple[str, str, str]] = (
    MappingProxyType(
        {
            "reiyah.executable-contract.ope-policy-distribution": (
                "ope",
                "fixtures/v1.2/good/sequential-off-policy-evaluation.json",
                OPE_APPLICATION_SCHEMA_ID,
            ),
            "reiyah.executable-contract.causal-identification": (
                "causal",
                "fixtures/v1.2/good/study-design-preregistration.json",
                STUDY_APPLICATION_SCHEMA_ID,
            ),
            "reiyah.executable-contract.readiness-unknown-propagation": (
                "readiness",
                "fixtures/v1.2/good/human-automation-assessment.json",
                HUMAN_APPLICATION_SCHEMA_ID,
            ),
            "reiyah.executable-contract.recovery-event-derivation": (
                "recovery",
                "fixtures/v1.2/good/human-automation-assessment.json",
                HUMAN_APPLICATION_SCHEMA_ID,
            ),
            "reiyah.executable-contract.transfer-eligibility": (
                "transfer",
                "fixtures/v1.2/good/joint-performance-evaluation.json",
                JOINT_APPLICATION_SCHEMA_ID,
            ),
            "reiyah.executable-contract.conformal-guarantee-disposition": (
                "conformal",
                "fixtures/v1.2/good/joint-performance-evaluation.json",
                JOINT_APPLICATION_SCHEMA_ID,
            ),
            "reiyah.executable-contract.ood-population-partition": (
                "ood",
                "fixtures/v1.2/good/joint-performance-evaluation.json",
                JOINT_APPLICATION_SCHEMA_ID,
            ),
            "reiyah.executable-contract.worst-group-eligibility": (
                "worst",
                "fixtures/v1.2/good/joint-performance-evaluation.json",
                JOINT_APPLICATION_SCHEMA_ID,
            ),
            "reiyah.executable-contract.human-belief-observation-decision-reconciliation": (
                "human",
                "fixtures/v1.2/good/human-automation-assessment.json",
                HUMAN_APPLICATION_SCHEMA_ID,
            ),
            "reiyah.executable-contract.joint-silent-miss-identifiability": (
                "joint",
                "fixtures/v1.2/good/joint-performance-evaluation.json",
                JOINT_APPLICATION_SCHEMA_ID,
            ),
            "reiyah.executable-contract.assumption-evidence-eligibility": (
                "assumption",
                "fixtures/v1.2/good/joint-performance-evaluation.json",
                JOINT_APPLICATION_SCHEMA_ID,
            ),
        }
    )
)
EXECUTABLE_CONTRACT_MATRIX_EXPECTATIONS: Mapping[str, Mapping[str, str]] = (
    MappingProxyType(
        {
            "reiyah.rule.ope-policy-distribution": MappingProxyType(
                {
                    "rule_id": "GA-OPE-ACTION-DISTRIBUTION",
                    "instance_pointer": "/policy_bindings",
                    "reason": "Every policy distribution must cover the exact action space once and sum to one.",
                }
            ),
            "reiyah.rule.causal-identification": MappingProxyType(
                {
                    "rule_id": "GA-CAUSAL-IDENTIFICATION-DISPOSITION",
                    "instance_pointer": "/identification_queries",
                    "reason": "A complete back-door query must report identified if and only if its eligible adjustment set d-separates treatment and outcome; complete open paths must report not_identified.",
                }
            ),
            "reiyah.rule.readiness-unknown-propagation": MappingProxyType(
                {
                    "rule_id": "GA-READINESS-UNKNOWN-PROPAGATION",
                    "instance_pointer": "/readiness",
                    "reason": "Any required or positively weighted unresolved capability must appear in the unresolved set and force a nonobserved aggregate with unknown disposition.",
                }
            ),
            "reiyah.rule.recovery-event-derivation": MappingProxyType(
                {
                    "rule_id": "GA-RECOVERY-EVENT-DERIVATION",
                    "instance_pointer": "/recovery",
                    "reason": "The outcome must bind the earliest qualifying recovery event inside the frozen window.",
                }
            ),
            "reiyah.rule.transfer-eligibility": MappingProxyType(
                {
                    "rule_id": "GA-TRANSFER-DISPOSITION",
                    "instance_pointer": "/transfer_evaluation",
                    "reason": "Transfer disposition must be unknown for unresolved operands and not_identified only for complete operands proving a non-applicable eligibility condition.",
                }
            ),
            "reiyah.rule.conformal-guarantee-disposition": MappingProxyType(
                {
                    "rule_id": "GA-CONFORMAL-GUARANTEE-ASSUMPTION",
                    "instance_pointer": "/conformal_evaluation/guarantee",
                    "reason": "A finite-sample conformal guarantee cannot be asserted when exchangeability is unmeasured.",
                }
            ),
            "reiyah.rule.ood-population-partition": MappingProxyType(
                {
                    "rule_id": "GA-OOD-DISJOINT-PARTITION",
                    "instance_pointer": "/ood_evaluation",
                    "reason": "The nine disjoint reference-by-detector cells must exhaust the OOD population exactly once.",
                }
            ),
            "reiyah.rule.worst-group-eligibility": MappingProxyType(
                {
                    "rule_id": "GA-WORST-GROUP-INFORMATION",
                    "instance_pointer": "/worst_group_evaluation",
                    "reason": "Group information disposition must be computed from all executable minimum-information thresholds.",
                }
            ),
            "reiyah.rule.human-belief-observation-decision-reconciliation": MappingProxyType(
                {
                    "rule_id": "GA-HUMAN-INFORMATION-SET-RECONCILIATION",
                    "instance_pointer": "/belief/information_set",
                    "reason": "The frozen decision information set must contain exact typed references to both the observation and the belief.",
                }
            ),
            "reiyah.rule.joint-silent-miss-identifiability": MappingProxyType(
                {
                    "rule_id": "GA-JOINT-COMMON-OPPORTUNITY-DERIVATION",
                    "instance_pointer": "/joint_silent_miss",
                    "reason": "Joint silent-miss marginals and intersection must derive from one disjoint common-opportunity contingency partition.",
                }
            ),
            "reiyah.rule.assumption-evidence-eligibility": MappingProxyType(
                {
                    "rule_id": "GA-ASSUMPTION-EVIDENCE-ELIGIBILITY",
                    "instance_pointer": "/transfer_evaluation/invariance/evidence_refs",
                    "reason": "Empty evidence arrays cannot establish overlap or invariance or admit a comparable transfer disposition.",
                }
            ),
        }
    )
)

OPE_REGISTRY_MANIFEST_CASE_IDS = (
    "reiyah.validator-canary.ope-registry.behavior-role",
    "reiyah.validator-canary.ope-registry.behavior-policy-ref",
    "reiyah.validator-canary.ope-registry.behavior-action-space",
    "reiyah.validator-canary.ope-registry.behavior-action-order",
    "reiyah.validator-canary.ope-registry.behavior-bound-artifact",
    "reiyah.validator-canary.ope-registry.behavior-history-order",
    "reiyah.validator-canary.ope-registry.behavior-history-duplicate",
    "reiyah.validator-canary.ope-registry.behavior-probability-content",
    "reiyah.validator-canary.ope-registry.target-role",
    "reiyah.validator-canary.ope-registry.target-policy-ref",
    "reiyah.validator-canary.ope-registry.target-action-space",
    "reiyah.validator-canary.ope-registry.target-action-order",
    "reiyah.validator-canary.ope-registry.target-bound-artifact",
    "reiyah.validator-canary.ope-registry.target-history-order",
    "reiyah.validator-canary.ope-registry.target-history-duplicate",
    "reiyah.validator-canary.ope-registry.target-probability-content",
    "reiyah.validator-canary.ope-registry.trajectory-member-order",
    "reiyah.validator-canary.ope-registry.trajectory-member-substitution",
    "reiyah.validator-canary.ope-registry.trajectory-bound-artifact",
)
OPE_REGISTRY_MANIFEST_CASE_SET_SHA256 = (
    "ce51192c862be27439dc4ce17ddf8ac6188e6e47d218e3ec5b6a4d9aee768fe0"
)

JOINT_OPPORTUNITY_REGISTRY_MANIFEST_CASE_IDS = (
    "reiyah.validator-canary.joint-opportunity-registry.member-order",
    "reiyah.validator-canary.joint-opportunity-registry.member-substitution",
    "reiyah.validator-canary.joint-opportunity-registry.member-completeness",
    "reiyah.validator-canary.joint-opportunity-registry.row-completeness",
    "reiyah.validator-canary.joint-opportunity-registry.coordinated-completeness",
    "reiyah.validator-canary.joint-opportunity-registry.bound-artifact",
    "reiyah.validator-canary.joint-opportunity-registry.object-binding",
    "reiyah.validator-canary.joint-opportunity-registry.clock-binding",
    "reiyah.validator-canary.joint-opportunity-registry.window-binding",
    "reiyah.validator-canary.joint-opportunity-registry.window-open",
    "reiyah.validator-canary.joint-opportunity-registry.window-close",
    "reiyah.validator-canary.joint-opportunity-registry.row-order",
    "reiyah.validator-canary.joint-opportunity-registry.row-opportunity-id",
    "reiyah.validator-canary.joint-opportunity-registry.row-object",
    "reiyah.validator-canary.joint-opportunity-registry.row-clock",
    "reiyah.validator-canary.joint-opportunity-registry.row-window",
    "reiyah.validator-canary.joint-opportunity-registry.row-time",
    "reiyah.validator-canary.joint-opportunity-registry.row-reference-state",
    "reiyah.validator-canary.joint-opportunity-registry.row-reference-validity",
    "reiyah.validator-canary.joint-opportunity-registry.human-channel-ref",
    "reiyah.validator-canary.joint-opportunity-registry.human-outcome",
    "reiyah.validator-canary.joint-opportunity-registry.automation-channel-ref",
    "reiyah.validator-canary.joint-opportunity-registry.automation-outcome",
    "reiyah.validator-canary.joint-opportunity-registry.warning-rule",
    "reiyah.validator-canary.joint-opportunity-registry.warning-outcome",
    "reiyah.validator-canary.joint-opportunity-registry.fallback-rule",
    "reiyah.validator-canary.joint-opportunity-registry.fallback-outcome",
)
JOINT_OPPORTUNITY_REGISTRY_MANIFEST_CASE_SET_SHA256 = (
    "6c56047693430ef225cb260aec3d535e709c0715f0a343ea2c80912fcc136ac2"
)

ASSURANCE_GOOD_FIXTURE_ID = "reiyah.fixture.good.v12.evaluation-assurance-bundle"
ASSURANCE_BLOCKED_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.evaluation-assurance-bundle-blocked"
)
HUMAN_GOOD_FIXTURE_ID = "reiyah.fixture.good.v12.human-automation-assessment"
HUMAN_OPTIONAL_UNKNOWN_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.human-automation-assessment-optional-unknown"
)
HUMAN_OBSERVATION_ABSTAINED_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.human-automation-assessment-observation-abstained"
)
HUMAN_OBSERVATION_MISSING_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.human-automation-assessment-observation-missing"
)
HUMAN_OBSERVATION_OOD_GOOD_FIXTURE_ID = "reiyah.fixture.good.v12.human-automation-assessment-observation-out-of-distribution"
HUMAN_OBSERVATION_SENSOR_INVALID_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.human-automation-assessment-observation-sensor-invalid"
)
HUMAN_OBSERVATION_UNMEASURED_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.human-automation-assessment-observation-unmeasured"
)
HUMAN_READINESS_NOT_READY_WEIGHTED_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.human-automation-assessment-readiness-not-ready-weighted"
)
HUMAN_READINESS_READY_BOOLEAN_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.human-automation-assessment-readiness-ready-boolean"
)
HUMAN_READINESS_READY_WEIGHTED_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.human-automation-assessment-readiness-ready-weighted"
)
HUMAN_RECOVERY_NO_EVENT_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.human-automation-assessment-recovery-no-event"
)
HUMAN_RECOVERY_CENSORING_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.human-automation-assessment-recovery-censoring"
)
HUMAN_RECOVERY_COMPETING_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.human-automation-assessment-recovery-competing"
)
HUMAN_RECOVERY_INPUT_NONOBSERVED_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.human-automation-assessment-recovery-input-nonobserved"
)
HUMAN_RECOVERY_INCOMPLETE_WINDOW_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.human-automation-assessment-recovery-incomplete-window"
)
HUMAN_RECOVERY_INVALID_WINDOW_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.human-automation-assessment-recovery-invalid-window"
)
HUMAN_RECOVERY_AMBIGUOUS_TIE_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.human-automation-assessment-recovery-ambiguous-tie"
)
JOINT_GOOD_FIXTURE_ID = "reiyah.fixture.good.v12.joint-performance-evaluation"
JOINT_NONOBSERVED_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.joint-performance-nonobserved"
)
JOINT_CONFORMAL_BELOW_TARGET_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.joint-performance-conformal-below-target"
)
JOINT_CONFORMAL_UNKNOWN_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.joint-performance-conformal-unknown"
)
JOINT_ZERO_OPPORTUNITIES_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.joint-performance-zero-opportunities"
)
JOINT_SELECTIVE_ZERO_ACCEPTED_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.joint-performance-selective-zero-accepted"
)
JOINT_OOD_ALL_UNKNOWN_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.joint-performance-ood-all-unknown"
)
OPE_GOOD_FIXTURE_ID = "reiyah.fixture.good.v12.sequential-off-policy-evaluation"
OPE_UNSUPPORTED_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.sequential-off-policy-evaluation-unsupported"
)
OPE_ALL_ZERO_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.sequential-off-policy-evaluation-all-zero"
)
OPE_MAXIMUM_HORIZON_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.sequential-off-policy-evaluation-maximum-horizon"
)
OPE_UPPER_CLIP_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.sequential-off-policy-evaluation-upper-clip"
)
OPE_SELF_NORMALIZED_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.sequential-off-policy-evaluation-self-normalized"
)
STUDY_GOOD_FIXTURE_ID = "reiyah.fixture.good.v12.study-design-preregistration"
STUDY_NOT_IDENTIFIED_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.study-design-preregistration-not-identified"
)
STUDY_UNKNOWN_GOOD_FIXTURE_ID = (
    "reiyah.fixture.good.v12.study-design-preregistration-unknown"
)

ALL_APPLICATION_SCHEMA_IDS = tuple(
    sorted(
        (
            ASSURANCE_APPLICATION_SCHEMA_ID,
            HUMAN_APPLICATION_SCHEMA_ID,
            JOINT_APPLICATION_SCHEMA_ID,
            OPE_APPLICATION_SCHEMA_ID,
            STUDY_APPLICATION_SCHEMA_ID,
        )
    )
)
ALL_GOOD_FIXTURE_IDS = tuple(
    sorted(
        (
            ASSURANCE_GOOD_FIXTURE_ID,
            ASSURANCE_BLOCKED_GOOD_FIXTURE_ID,
            HUMAN_GOOD_FIXTURE_ID,
            HUMAN_OBSERVATION_ABSTAINED_GOOD_FIXTURE_ID,
            HUMAN_OBSERVATION_MISSING_GOOD_FIXTURE_ID,
            HUMAN_OBSERVATION_OOD_GOOD_FIXTURE_ID,
            HUMAN_OBSERVATION_SENSOR_INVALID_GOOD_FIXTURE_ID,
            HUMAN_OBSERVATION_UNMEASURED_GOOD_FIXTURE_ID,
            HUMAN_OPTIONAL_UNKNOWN_GOOD_FIXTURE_ID,
            HUMAN_READINESS_NOT_READY_WEIGHTED_GOOD_FIXTURE_ID,
            HUMAN_READINESS_READY_BOOLEAN_GOOD_FIXTURE_ID,
            HUMAN_READINESS_READY_WEIGHTED_GOOD_FIXTURE_ID,
            HUMAN_RECOVERY_NO_EVENT_GOOD_FIXTURE_ID,
            HUMAN_RECOVERY_CENSORING_GOOD_FIXTURE_ID,
            HUMAN_RECOVERY_COMPETING_GOOD_FIXTURE_ID,
            HUMAN_RECOVERY_INPUT_NONOBSERVED_GOOD_FIXTURE_ID,
            HUMAN_RECOVERY_INCOMPLETE_WINDOW_GOOD_FIXTURE_ID,
            HUMAN_RECOVERY_INVALID_WINDOW_GOOD_FIXTURE_ID,
            HUMAN_RECOVERY_AMBIGUOUS_TIE_GOOD_FIXTURE_ID,
            JOINT_GOOD_FIXTURE_ID,
            JOINT_NONOBSERVED_GOOD_FIXTURE_ID,
            JOINT_CONFORMAL_BELOW_TARGET_GOOD_FIXTURE_ID,
            JOINT_CONFORMAL_UNKNOWN_GOOD_FIXTURE_ID,
            JOINT_ZERO_OPPORTUNITIES_GOOD_FIXTURE_ID,
            JOINT_SELECTIVE_ZERO_ACCEPTED_GOOD_FIXTURE_ID,
            JOINT_OOD_ALL_UNKNOWN_GOOD_FIXTURE_ID,
            OPE_GOOD_FIXTURE_ID,
            OPE_UNSUPPORTED_GOOD_FIXTURE_ID,
            OPE_ALL_ZERO_GOOD_FIXTURE_ID,
            OPE_MAXIMUM_HORIZON_GOOD_FIXTURE_ID,
            OPE_UPPER_CLIP_GOOD_FIXTURE_ID,
            OPE_SELF_NORMALIZED_GOOD_FIXTURE_ID,
            STUDY_GOOD_FIXTURE_ID,
            STUDY_NOT_IDENTIFIED_GOOD_FIXTURE_ID,
            STUDY_UNKNOWN_GOOD_FIXTURE_ID,
        )
    )
)
GOOD_FIXTURE_PATH_TO_ID: Mapping[str, str] = MappingProxyType(
    {
        "fixtures/v1.2/good/evaluation-assurance-bundle.json": ASSURANCE_GOOD_FIXTURE_ID,
        "fixtures/v1.2/good/evaluation-assurance-bundle-blocked.json": (
            ASSURANCE_BLOCKED_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/human-automation-assessment.json": HUMAN_GOOD_FIXTURE_ID,
        "fixtures/v1.2/good/human-automation-assessment-observation-abstained.json": (
            HUMAN_OBSERVATION_ABSTAINED_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/human-automation-assessment-observation-missing.json": (
            HUMAN_OBSERVATION_MISSING_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/human-automation-assessment-observation-out-of-distribution.json": (
            HUMAN_OBSERVATION_OOD_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/human-automation-assessment-observation-sensor-invalid.json": (
            HUMAN_OBSERVATION_SENSOR_INVALID_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/human-automation-assessment-observation-unmeasured.json": (
            HUMAN_OBSERVATION_UNMEASURED_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/human-automation-assessment-optional-unknown.json": (
            HUMAN_OPTIONAL_UNKNOWN_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/human-automation-assessment-readiness-not-ready-weighted.json": (
            HUMAN_READINESS_NOT_READY_WEIGHTED_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/human-automation-assessment-readiness-ready-boolean.json": (
            HUMAN_READINESS_READY_BOOLEAN_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/human-automation-assessment-readiness-ready-weighted.json": (
            HUMAN_READINESS_READY_WEIGHTED_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/human-automation-assessment-recovery-no-event.json": (
            HUMAN_RECOVERY_NO_EVENT_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/human-automation-assessment-recovery-censoring.json": (
            HUMAN_RECOVERY_CENSORING_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/human-automation-assessment-recovery-competing.json": (
            HUMAN_RECOVERY_COMPETING_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/human-automation-assessment-recovery-input-nonobserved.json": (
            HUMAN_RECOVERY_INPUT_NONOBSERVED_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/human-automation-assessment-recovery-incomplete-window.json": (
            HUMAN_RECOVERY_INCOMPLETE_WINDOW_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/human-automation-assessment-recovery-invalid-window.json": (
            HUMAN_RECOVERY_INVALID_WINDOW_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/human-automation-assessment-recovery-ambiguous-tie.json": (
            HUMAN_RECOVERY_AMBIGUOUS_TIE_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/joint-performance-evaluation.json": JOINT_GOOD_FIXTURE_ID,
        "fixtures/v1.2/good/joint-performance-nonobserved.json": (
            JOINT_NONOBSERVED_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/joint-performance-conformal-below-target.json": (
            JOINT_CONFORMAL_BELOW_TARGET_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/joint-performance-conformal-unknown.json": (
            JOINT_CONFORMAL_UNKNOWN_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/joint-performance-zero-opportunities.json": (
            JOINT_ZERO_OPPORTUNITIES_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/joint-performance-selective-zero-accepted.json": (
            JOINT_SELECTIVE_ZERO_ACCEPTED_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/joint-performance-ood-all-unknown.json": (
            JOINT_OOD_ALL_UNKNOWN_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/sequential-off-policy-evaluation.json": OPE_GOOD_FIXTURE_ID,
        "fixtures/v1.2/good/sequential-off-policy-evaluation-unsupported.json": (
            OPE_UNSUPPORTED_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/sequential-off-policy-evaluation-all-zero.json": (
            OPE_ALL_ZERO_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/sequential-off-policy-evaluation-maximum-horizon.json": (
            OPE_MAXIMUM_HORIZON_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/sequential-off-policy-evaluation-upper-clip.json": (
            OPE_UPPER_CLIP_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/sequential-off-policy-evaluation-self-normalized.json": (
            OPE_SELF_NORMALIZED_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/study-design-preregistration.json": STUDY_GOOD_FIXTURE_ID,
        "fixtures/v1.2/good/study-design-preregistration-not-identified.json": (
            STUDY_NOT_IDENTIFIED_GOOD_FIXTURE_ID
        ),
        "fixtures/v1.2/good/study-design-preregistration-unknown.json": (
            STUDY_UNKNOWN_GOOD_FIXTURE_ID
        ),
    }
)

CONTRACT_ESTIMAND_IDS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "reiyah.executable-contract.ope-policy-distribution": (
            "reiyah.estimand.sequential-policy-value",
        ),
        "reiyah.executable-contract.causal-identification": (
            "reiyah.estimand.synthetic-risk-difference",
        ),
        "reiyah.executable-contract.readiness-unknown-propagation": (
            "reiyah.estimand.readiness",
        ),
        "reiyah.executable-contract.recovery-event-derivation": (
            "reiyah.estimand.recoverability",
        ),
        "reiyah.executable-contract.transfer-eligibility": (
            "reiyah.estimand.transfer",
        ),
        "reiyah.executable-contract.conformal-guarantee-disposition": (
            "reiyah.estimand.conformal-coverage",
        ),
        "reiyah.executable-contract.ood-population-partition": (
            "reiyah.estimand.ood-selective-risk-coverage",
        ),
        "reiyah.executable-contract.worst-group-eligibility": (
            "reiyah.estimand.worst-group",
        ),
        "reiyah.executable-contract.human-belief-observation-decision-reconciliation": (
            "reiyah.estimand.object-belief-quality",
        ),
        "reiyah.executable-contract.joint-silent-miss-identifiability": (
            "reiyah.estimand.joint-silent-miss",
        ),
        "reiyah.executable-contract.assumption-evidence-eligibility": (),
    }
)

CONTRACT_APPLICATION_SCHEMA_IDS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "reiyah.executable-contract.ope-policy-distribution": (
            OPE_APPLICATION_SCHEMA_ID,
        ),
        "reiyah.executable-contract.causal-identification": (
            STUDY_APPLICATION_SCHEMA_ID,
        ),
        "reiyah.executable-contract.readiness-unknown-propagation": (
            HUMAN_APPLICATION_SCHEMA_ID,
        ),
        "reiyah.executable-contract.recovery-event-derivation": (
            HUMAN_APPLICATION_SCHEMA_ID,
        ),
        "reiyah.executable-contract.transfer-eligibility": (
            JOINT_APPLICATION_SCHEMA_ID,
        ),
        "reiyah.executable-contract.conformal-guarantee-disposition": (
            JOINT_APPLICATION_SCHEMA_ID,
        ),
        "reiyah.executable-contract.ood-population-partition": (
            JOINT_APPLICATION_SCHEMA_ID,
        ),
        "reiyah.executable-contract.worst-group-eligibility": (
            JOINT_APPLICATION_SCHEMA_ID,
        ),
        "reiyah.executable-contract.human-belief-observation-decision-reconciliation": (
            HUMAN_APPLICATION_SCHEMA_ID,
        ),
        "reiyah.executable-contract.joint-silent-miss-identifiability": (
            JOINT_APPLICATION_SCHEMA_ID,
        ),
        "reiyah.executable-contract.assumption-evidence-eligibility": (
            JOINT_APPLICATION_SCHEMA_ID,
        ),
    }
)

CONTRACT_GOOD_FIXTURE_IDS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "reiyah.executable-contract.ope-policy-distribution": (
            OPE_ALL_ZERO_GOOD_FIXTURE_ID,
            OPE_GOOD_FIXTURE_ID,
            OPE_MAXIMUM_HORIZON_GOOD_FIXTURE_ID,
            OPE_SELF_NORMALIZED_GOOD_FIXTURE_ID,
            OPE_UNSUPPORTED_GOOD_FIXTURE_ID,
            OPE_UPPER_CLIP_GOOD_FIXTURE_ID,
        ),
        "reiyah.executable-contract.causal-identification": (
            STUDY_GOOD_FIXTURE_ID,
            STUDY_NOT_IDENTIFIED_GOOD_FIXTURE_ID,
            STUDY_UNKNOWN_GOOD_FIXTURE_ID,
        ),
        "reiyah.executable-contract.readiness-unknown-propagation": (
            HUMAN_GOOD_FIXTURE_ID,
            HUMAN_OPTIONAL_UNKNOWN_GOOD_FIXTURE_ID,
            HUMAN_READINESS_NOT_READY_WEIGHTED_GOOD_FIXTURE_ID,
            HUMAN_READINESS_READY_BOOLEAN_GOOD_FIXTURE_ID,
            HUMAN_READINESS_READY_WEIGHTED_GOOD_FIXTURE_ID,
        ),
        "reiyah.executable-contract.recovery-event-derivation": (
            HUMAN_GOOD_FIXTURE_ID,
            HUMAN_RECOVERY_AMBIGUOUS_TIE_GOOD_FIXTURE_ID,
            HUMAN_RECOVERY_CENSORING_GOOD_FIXTURE_ID,
            HUMAN_RECOVERY_COMPETING_GOOD_FIXTURE_ID,
            HUMAN_RECOVERY_INCOMPLETE_WINDOW_GOOD_FIXTURE_ID,
            HUMAN_RECOVERY_INPUT_NONOBSERVED_GOOD_FIXTURE_ID,
            HUMAN_RECOVERY_INVALID_WINDOW_GOOD_FIXTURE_ID,
            HUMAN_RECOVERY_NO_EVENT_GOOD_FIXTURE_ID,
        ),
        "reiyah.executable-contract.transfer-eligibility": (
            JOINT_CONFORMAL_BELOW_TARGET_GOOD_FIXTURE_ID,
            JOINT_CONFORMAL_UNKNOWN_GOOD_FIXTURE_ID,
            JOINT_GOOD_FIXTURE_ID,
            JOINT_NONOBSERVED_GOOD_FIXTURE_ID,
        ),
        "reiyah.executable-contract.conformal-guarantee-disposition": (
            JOINT_CONFORMAL_BELOW_TARGET_GOOD_FIXTURE_ID,
            JOINT_CONFORMAL_UNKNOWN_GOOD_FIXTURE_ID,
            JOINT_GOOD_FIXTURE_ID,
        ),
        "reiyah.executable-contract.ood-population-partition": (
            JOINT_GOOD_FIXTURE_ID,
            JOINT_OOD_ALL_UNKNOWN_GOOD_FIXTURE_ID,
            JOINT_SELECTIVE_ZERO_ACCEPTED_GOOD_FIXTURE_ID,
        ),
        "reiyah.executable-contract.worst-group-eligibility": (
            JOINT_CONFORMAL_BELOW_TARGET_GOOD_FIXTURE_ID,
            JOINT_CONFORMAL_UNKNOWN_GOOD_FIXTURE_ID,
            JOINT_GOOD_FIXTURE_ID,
            JOINT_NONOBSERVED_GOOD_FIXTURE_ID,
        ),
        "reiyah.executable-contract.human-belief-observation-decision-reconciliation": (
            HUMAN_GOOD_FIXTURE_ID,
            HUMAN_OBSERVATION_ABSTAINED_GOOD_FIXTURE_ID,
            HUMAN_OBSERVATION_MISSING_GOOD_FIXTURE_ID,
            HUMAN_OBSERVATION_OOD_GOOD_FIXTURE_ID,
            HUMAN_OBSERVATION_SENSOR_INVALID_GOOD_FIXTURE_ID,
            HUMAN_OBSERVATION_UNMEASURED_GOOD_FIXTURE_ID,
        ),
        "reiyah.executable-contract.joint-silent-miss-identifiability": (
            JOINT_GOOD_FIXTURE_ID,
            JOINT_NONOBSERVED_GOOD_FIXTURE_ID,
            JOINT_ZERO_OPPORTUNITIES_GOOD_FIXTURE_ID,
        ),
        "reiyah.executable-contract.assumption-evidence-eligibility": (
            JOINT_GOOD_FIXTURE_ID,
        ),
    }
)

CONTRACT_RULE_IDS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "reiyah.executable-contract.ope-policy-distribution": (
            "GA-OPE-ACTION-DISTRIBUTION",
            "GA-OPE-CUMULATIVE-WEIGHT",
            "GA-OPE-ESS-ALL-ZERO",
            "GA-OPE-ESS-CUMULATIVE",
            "GA-OPE-ESS-HORIZON-COVERAGE",
            "GA-OPE-ESTIMATOR-BINDING",
            "GA-OPE-ESTIMATOR-SELECTION-TIME",
            "GA-OPE-HISTORY-INFORMATION-SET",
            "GA-OPE-HISTORY-SUPPORT",
            "GA-OPE-LOGGED-PROPENSITY",
            "GA-OPE-POLICY-TABLE-BINDING",
            "GA-OPE-STEP-HORIZON-COMPLETENESS",
            "GA-OPE-STEP-RATIO",
            "GA-OPE-TERMINAL-COMPLETENESS",
            "GA-OPE-TRAJECTORY-MANIFEST-BINDING",
            "GA-OPE-WEIGHT-NORMALIZATION",
            "GA-OPE-WEIGHT-TRANSFORMATION",
        ),
        "reiyah.executable-contract.causal-identification": (
            "GA-CAUSAL-ANALYSIS-UNIT-SET-BINDING",
            "GA-CAUSAL-BACKDOOR-OPEN",
            "GA-CAUSAL-DAG-CYCLE",
            "GA-CAUSAL-ESTIMAND-BINDING",
            "GA-CAUSAL-IDENTIFICATION-DISPOSITION",
            "GA-CAUSAL-PROHIBITED-ADJUSTMENT",
            "GA-CAUSAL-QUERY-ROLE",
            "GA-CAUSAL-SELECTED-SET-RECONCILIATION",
            "GA-CAUSAL-SPLIT-FREEZE",
            "GA-CAUSAL-SPLIT-MEMBERSHIP",
            "GA-CAUSAL-SPLIT-REFERENCE",
            "GA-CAUSAL-STRATIFICATION-INPUT",
            "GA-CAUSAL-TEMPORAL-ORDER",
            "GA-STUDY-DESIGN-CHRONOLOGY",
        ),
        "reiyah.executable-contract.readiness-unknown-propagation": (
            "GA-READINESS-AGGREGATION-MISMATCH",
            "GA-READINESS-CAPABILITY-MANIFEST-BINDING",
            "GA-READINESS-CAPABILITY-DIMENSION",
            "GA-READINESS-CRITERION-MISMATCH",
            "GA-READINESS-TEMPORAL-RECONCILIATION",
            "GA-READINESS-UNKNOWN-PROPAGATION",
        ),
        "reiyah.executable-contract.recovery-event-derivation": (
            "GA-RECOVERY-CENSORING-DISPOSITION",
            "GA-RECOVERY-COMPETING-EVENT",
            "GA-RECOVERY-EVENT-CLASSIFICATION",
            "GA-RECOVERY-EVENT-DERIVATION",
            "GA-RECOVERY-EVENT-MANIFEST-BINDING",
            "GA-RECOVERY-INPUT-UNKNOWN-PROPAGATION",
            "GA-RECOVERY-NO-EVENT-CENSORING",
            "GA-RECOVERY-WINDOW-MISMATCH",
        ),
        "reiyah.executable-contract.transfer-eligibility": (
            "GA-TRANSFER-ADAPTATION-DISCLOSURE",
            "GA-TRANSFER-COVERAGE",
            "GA-TRANSFER-DISPOSITION",
            "GA-TRANSFER-DOMAIN-ROLE-BINDING",
            "GA-TRANSFER-GAP",
            "GA-TRANSFER-METRIC-CONTRACT",
            "GA-TRANSFER-TARGET-ACCESS",
        ),
        "reiyah.executable-contract.conformal-guarantee-disposition": (
            "GA-CONFORMAL-COVERAGE-DISPOSITION",
            "GA-CONFORMAL-EMPIRICAL-DERIVATION",
            "GA-CONFORMAL-GROUP-SCOPE",
            "GA-CONFORMAL-GUARANTEE-ASSUMPTION",
            "GA-CONFORMAL-TARGET",
        ),
        "reiyah.executable-contract.ood-population-partition": (
            "GA-OOD-DERIVATION",
            "GA-OOD-DISJOINT-PARTITION",
            "GA-OOD-SELECTIVE-BINDING",
            "GA-SELECTIVE-DERIVATION",
            "GA-SELECTIVE-PARTITION",
        ),
        "reiyah.executable-contract.worst-group-eligibility": (
            "GA-WORST-GROUP-COVERAGE",
            "GA-WORST-GROUP-DISPOSITION",
            "GA-WORST-GROUP-ELIGIBILITY",
            "GA-WORST-GROUP-INFORMATION",
            "GA-WORST-GROUP-TIE",
            "GA-WORST-GROUP-UNKNOWN",
        ),
        "reiyah.executable-contract.human-belief-observation-decision-reconciliation": (
            "GA-BELIEF-DISTRIBUTION-SUM",
            "GA-BELIEF-NORMALIZATION-POLICY-BINDING",
            "GA-BELIEF-STATE-SPACE-COVERAGE",
            "GA-HUMAN-INFORMATION-SET-RECONCILIATION",
            "GA-HUMAN-OBJECT-RECONCILIATION",
            "GA-HUMAN-SUBJECT-RECONCILIATION",
            "GA-HUMAN-TEMPORAL-RECONCILIATION",
            "GA-OBSERVATION-VALIDITY-STATE",
        ),
        "reiyah.executable-contract.joint-silent-miss-identifiability": (
            "GA-JOINT-COMMON-OPPORTUNITY-DERIVATION",
            "GA-JOINT-OPPORTUNITY-CHRONOLOGY",
            "GA-JOINT-OPPORTUNITY-MANIFEST-BINDING",
            "GA-JOINT-OPPORTUNITY-ROW-BINDING",
            "GA-JOINT-SILENT-MISS-DERIVATION",
            "GA-JOINT-SILENT-ROW-DERIVATION",
            "GA-JOINT-UNKNOWN-PROPAGATION",
        ),
        "reiyah.executable-contract.assumption-evidence-eligibility": (
            "GA-ASSUMPTION-EVIDENCE-ELIGIBILITY",
            "GA-ASSUMPTION-SELF-EVIDENCE",
        ),
    }
)

CROSS_CUTTING_CONTRACT_BINDINGS = (
    (
        "reiyah.cross-cutting-contract.lifecycle-history-integrity",
        ALL_APPLICATION_SCHEMA_IDS,
        ALL_GOOD_FIXTURE_IDS,
        (
            "GA-LIFECYCLE-CURRENT-HISTORY",
            "GA-LIFECYCLE-CHRONOLOGY",
            "GA-LIFECYCLE-EVIDENCE-ELIGIBILITY",
        ),
    ),
    (
        "reiyah.cross-cutting-contract.typed-reference-integrity",
        ALL_APPLICATION_SCHEMA_IDS,
        ALL_GOOD_FIXTURE_IDS,
        (
            "GA-ACTOR-REFERENCE-TYPE",
            "GA-ARTIFACT-REFERENCE-RESOLUTION",
            "GA-DOCUMENT-LOCAL-REFERENCE-RESOLUTION",
            "GA-ESTIMAND-REFERENCE-BINDING",
            "GA-EVIDENCE-GAP-REFERENCE-DISPOSITION",
            "GA-REFERENCE-KIND",
            "GA-REFERENCE-VERSION",
            "GA-REGISTRY-BARE-IDENTIFIER-RESOLUTION",
            "GA-SCHEMA-REFERENCE-RESOLUTION",
        ),
    ),
    (
        "reiyah.cross-cutting-contract.architecture-nonclaim-boundary",
        (ASSURANCE_APPLICATION_SCHEMA_ID,),
        tuple(sorted((ASSURANCE_GOOD_FIXTURE_ID, ASSURANCE_BLOCKED_GOOD_FIXTURE_ID))),
        (
            "GA-ASSURANCE-LICENSE-DISPOSITION",
            "GA-ASSURANCE-NO-DEPLOYMENT",
            "GA-ASSURANCE-NONCLAIM",
        ),
    ),
)

PREDECESSOR_PACKET_COMMIT = "ad1a8cae6ad17f26f5a07f43fb60b6c9f55b4b1b"
PREDECESSOR_PACKET_TREE = "5865cbc977ed6e4ccf7bf80ad6d8a64e6c9e5341"
PREDECESSOR_RECEIPT_COMMIT = "656d826cfe6938fd628c0ede7ea15929fe11d90e"
PREDECESSOR_RECEIPT_TREE = "94c32621d7b1d9da42b6aae9df7ca4da82a6e8ed"
PREDECESSOR_INDEX_PATH = "history/gate-a-1.1.2/gate/GATE_A_EVIDENCE_INDEX.json"
PREDECESSOR_SIDECAR_PATH = "history/gate-a-1.1.2/gate/GATE_A_EVIDENCE_INDEX.sha256"
PREDECESSOR_REPORT_PATH = "gate/validation-reports/gate-a-validation-1.1.2.json"
PREDECESSOR_RECEIPT_PATH = (
    "gate/public-distribution-receipts/reiyah.public-distribution-receipt-1.1.2.json"
)
PREDECESSOR_RECOVERY_PATH = "history/gate-a-1.1.2/RECOVERY.json"
PREDECESSOR_FIXTURE_CATALOG_PATH = "fixtures/fixture-catalog.json"
PREDECESSOR_FIXTURE_CATALOG_SHA256 = (
    "f848a4b4f829deab59721ac224815c25860f865514f8c6ca8bccb0294f9658b7"
)
PREDECESSOR_FIXTURE_CATALOG_BYTE_SIZE = 44181
PREDECESSOR_FIXTURE_CATALOG_ROW_COUNT = 196
PREDECESSOR_BINDINGS = {
    PREDECESSOR_INDEX_PATH: (
        "17f3a2e601e9cb4e1c0cd0f97561b1da9ffdc7d5893ed4af4eaccbaf8a67989f",
        182832,
    ),
    PREDECESSOR_SIDECAR_PATH: (
        "d2df35f83aeb4658da54b54f302680947d965752c335647f45be196e95cefdfe",
        105,
    ),
    PREDECESSOR_REPORT_PATH: (
        "06fc3114522c16625da337fe25c71b1fd53abeeaf9c31a11748afc06eb5d66d8",
        2826,
    ),
    PREDECESSOR_RECEIPT_PATH: (
        "e7f3bedac49423d4ba042419056896c507d26ee2bd9a706981abf2131dcda19d",
        7621,
    ),
    PREDECESSOR_RECOVERY_PATH: (
        "ff98c40648d18c931c1198c97c430f5ce31eb93f0738126b7ca60f43440d02da",
        10774,
    ),
}

PYTHON_PATH = Path("/opt/homebrew/bin/python3.14")
GIT_PATH = Path("/usr/bin/git")
SHELL_PATH = Path("/bin/sh")
ENV_PATH = Path("/usr/bin/env")
SANDBOX_EXEC_PATH = Path("/usr/bin/sandbox-exec")
PYTHON_RUNTIME_ROOT = Path(
    "/opt/homebrew/Cellar/python@3.14/3.14.2_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14"
)
PYTHON_FRAMEWORK_PATH = Path(
    "/opt/homebrew/Cellar/python@3.14/3.14.2_1/Frameworks/Python.framework/Versions/3.14/Python"
)
PYTHON_RUNTIME_EXCLUSIONS = ("config-3.14-darwin", "site-packages")

# These bootstrap digests are deliberately duplicated in the reviewed lock.  The
# lock is then read from the immutable/in-memory snapshot, not from a second live
# filesystem read.  A validator cannot establish its own trust without an
# externally retained digest; the packet index is the future external binding.
BOOTSTRAP_EXECUTABLES = {
    str(
        PYTHON_PATH
    ): "3b6b69c61fd3765ab911d701cd17293b4a9154a0cb4973b546f05847f9a164c6",
    str(GIT_PATH): "878004e85c866251cb3941ad57c0e21e4e361b026e139c24eb9a170c46ec8e81",
    str(SHELL_PATH): "75fab21b84ad712398981e76b53721a6db46eb3cc39e85e0abac1bff01b30d3b",
    str(ENV_PATH): "fe531da7d583d35e73ecf2a17aedf8ae4b2ff883de91b20fff5ad79dd7e1c723",
    str(
        SANDBOX_EXEC_PATH
    ): "569aa2e95952f1a355c46f3de02574bc4a90b9d21ec4c3944001f611935ee5ad",
}

SEATBELT_PROFILE = _EARLY_SEATBELT_PROFILE.decode("utf-8")
SEATBELT_PROFILE_SHA256 = hashlib.sha256(SEATBELT_PROFILE.encode("utf-8")).hexdigest()

GUARANTEE_BOUNDARIES = {
    "covered": (
        "Exact declared executable, Python framework, standard-library, dependency RECORD, recorded-file, and "
        "import-root bytes on the named platform; "
        "the external launcher enters Seatbelt before CPython startup; isolated no-site Python startup verifies the "
        "effective denial policy before other standard-library imports; network and filesystem writes are denied "
        "except write-data to /dev/null."
    ),
    "conditional": (
        "Seatbelt enforcement is conditional on the exact locked launcher, macOS build, kernel, sandbox-exec and "
        "libsandbox implementations, shell, env, Python and Git bytes, and an uncompromised operating system."
    ),
    "externally_verified": (
        "Nothing in this offline lock proves GitHub state, independent transport readback, operator acceptance, "
        "scientific validity, executable code identity before first instruction, transitive dynamic-library bytes, "
        "or operating-system integrity."
    ),
}

DATE_PATTERN = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
DATETIME_PATTERN = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})[Tt]"
    r"(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?"
    r"(?:[Zz]|([+-])(\d{2}):(\d{2}))$"
)
URI_SCHEME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*$")
BAD_PERCENT_PATTERN = re.compile(r"%(?![0-9A-Fa-f]{2})")
IPVFUTURE_PATTERN = re.compile(r"^[Vv][0-9A-Fa-f]+\.[A-Za-z0-9._~!$&'()*+,;=:-]+$")
URI_ASCII_CHARACTERS = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    "-._~:/?#[]@!$&'()*+,;=%"
)

# IERS-announced positive UTC leap seconds through the locked 2026-08-24
# validation date.  A later announced event requires a reviewed successor.
ANNOUNCED_POSITIVE_LEAP_SECOND_DATES = frozenset(
    {
        "1972-06-30",
        "1972-12-31",
        "1973-12-31",
        "1974-12-31",
        "1975-12-31",
        "1976-12-31",
        "1977-12-31",
        "1978-12-31",
        "1979-12-31",
        "1981-06-30",
        "1982-06-30",
        "1983-06-30",
        "1985-06-30",
        "1987-12-31",
        "1989-12-31",
        "1990-12-31",
        "1992-06-30",
        "1993-06-30",
        "1994-06-30",
        "1995-12-31",
        "1997-06-30",
        "1998-12-31",
        "2005-12-31",
        "2008-12-31",
        "2012-06-30",
        "2015-06-30",
        "2016-12-31",
    }
)


class GateError(Exception):
    """A deterministic, operator-actionable validation failure."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class SnapshotFile:
    path: str
    mode: str
    data: bytes

    @property
    def size(self) -> int:
        return len(self.data)

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.data).hexdigest()


@dataclass(frozen=True)
class RepositorySnapshot:
    mode: str
    files: Mapping[str, SnapshotFile]
    projection_sha256: str
    file_count: int
    byte_count: int
    commit: str | None
    tree: str | None
    object_format: str | None

    def read(self, path: str) -> bytes:
        try:
            return self.files[path].data
        except KeyError as exc:
            raise GateError(
                "GA12-SNAPSHOT-MISSING", f"snapshot path is absent: {path}"
            ) from exc


@dataclass(frozen=True)
class CandidateProjection:
    files: Mapping[str, SnapshotFile]
    exclusions: tuple[Mapping[str, str], ...]
    serialized: bytes
    sha256: str
    artifact_count: int
    byte_count: int

    def summary(self) -> dict[str, Any]:
        return {
            "serialization": "sorted_path_nul_sha256_nul_byte_count_lf",
            "sha256": f"sha256:{self.sha256}",
            "artifact_count": self.artifact_count,
            "byte_count": self.byte_count,
        }


def stable_regular_bytes(path: Path, *, permit_symlink: bool = False) -> bytes:
    candidate = path
    if path.is_symlink():
        if not permit_symlink:
            raise GateError("GA12-TOOLCHAIN-SYMLINK", f"unexpected symlink: {path}")
        try:
            candidate = path.resolve(strict=True)
        except OSError as exc:
            raise GateError(
                "GA12-TOOLCHAIN-READ", f"cannot resolve {path}: {exc}"
            ) from exc
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(candidate, flags)
    except OSError as exc:
        raise GateError("GA12-TOOLCHAIN-READ", f"cannot read {path}: {exc}") from exc
    try:
        try:
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode):
                raise GateError(
                    "GA12-TOOLCHAIN-FILE-TYPE", f"path is not regular: {path}"
                )
            chunks: list[bytes] = []
            while chunk := os.read(descriptor, 1024 * 1024):
                chunks.append(chunk)
            after = os.fstat(descriptor)
        except OSError as exc:
            raise GateError(
                "GA12-TOOLCHAIN-READ", f"cannot read {path}: {exc}"
            ) from exc
    finally:
        os.close(descriptor)
    identity_before = (
        before.st_dev,
        before.st_ino,
        before.st_mode,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    identity_after = (
        after.st_dev,
        after.st_ino,
        after.st_mode,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    data = b"".join(chunks)
    if identity_before != identity_after or len(data) != before.st_size:
        raise GateError("GA12-TOOLCHAIN-DRIFT", f"path drifted while read: {path}")
    return data


def sha256_file(path: Path, *, permit_symlink: bool = False) -> str:
    return hashlib.sha256(
        stable_regular_bytes(path, permit_symlink=permit_symlink)
    ).hexdigest()


def verify_bootstrap_executables() -> None:
    observed_python = Path(sys.executable)
    if observed_python != PYTHON_PATH:
        raise GateError(
            "GA12-LAUNCHER-PYTHON-PATH",
            f"expected {PYTHON_PATH}, observed {observed_python}",
        )
    for path_text, expected in sorted(BOOTSTRAP_EXECUTABLES.items()):
        path = Path(path_text)
        observed = sha256_file(path, permit_symlink=(path == PYTHON_PATH))
        if observed != expected:
            raise GateError(
                "GA12-BOOTSTRAP-BYTE-MISMATCH",
                f"bootstrap executable digest mismatch for {path}",
            )


def verify_seatbelt_effective() -> None:
    """Confirm the early external and in-process denials with harmless probes.

    The probes do not constitute cryptographic operating-system attestation.  They
    do establish that this process cannot open the validator for writing or bind
    a loopback TCP endpoint under the locked environment.  Outside Seatbelt, both
    operations are available to the repository owner; neither probe changes file
    bytes or transmits a packet.
    """

    target = CANONICAL_ROOT / TOOL_PATH
    flags = os.O_WRONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(target, flags)
    except OSError as exc:
        if exc.errno != errno.EPERM:
            raise GateError(
                "GA12-SANDBOX-WRITE-PROBE",
                f"write-denial probe returned unexpected errno {exc.errno}",
            ) from exc
    else:
        os.close(descriptor)
        raise GateError(
            "GA12-SANDBOX-WRITE-BYPASS",
            "validator file was writable; locked Seatbelt denial is not effective",
        )

    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        try:
            probe.bind(("127.0.0.1", 0))
        except OSError as exc:
            if exc.errno != errno.EPERM:
                raise GateError(
                    "GA12-SANDBOX-NETWORK-PROBE",
                    f"network-denial probe returned unexpected errno {exc.errno}",
                ) from exc
        else:
            raise GateError(
                "GA12-SANDBOX-NETWORK-BYPASS",
                "loopback bind succeeded; locked Seatbelt network denial is not effective",
            )
    finally:
        probe.close()

    outbound_probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        try:
            # UDP connect selects a peer locally but transmits no datagram.
            outbound_probe.connect(("127.0.0.1", 9))
        except OSError as exc:
            if exc.errno != errno.EPERM:
                raise GateError(
                    "GA12-SANDBOX-OUTBOUND-PROBE",
                    f"outbound-denial probe returned unexpected errno {exc.errno}",
                ) from exc
        else:
            raise GateError(
                "GA12-SANDBOX-OUTBOUND-BYPASS",
                "UDP peer selection succeeded; locked Seatbelt outbound denial is not effective",
            )
    finally:
        outbound_probe.close()


def run_git(arguments: Sequence[str], *, check: bool = True) -> bytes:
    process = subprocess.run(
        [
            str(GIT_PATH),
            "-C",
            str(CANONICAL_ROOT),
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "core.untrackedCache=false",
            *arguments,
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env={
            "LANG": "C",
            "LC_ALL": "C",
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
        },
    )
    if check and process.returncode != 0:
        detail = process.stderr.decode("utf-8", "replace").strip()
        raise GateError(
            "GA12-GIT-COMMAND", f"git {' '.join(arguments)} failed: {detail}"
        )
    return process.stdout


def verify_repository_identity() -> None:
    verify_bootstrap_executables()
    verify_seatbelt_effective()
    if Path.cwd().resolve() != CANONICAL_ROOT:
        raise GateError("GA12-IDENTITY-CWD", f"cwd does not identify {CANONICAL_ROOT}")
    root = run_git(["rev-parse", "--show-toplevel"]).decode("utf-8", "strict").strip()
    if root != str(CANONICAL_ROOT):
        raise GateError("GA12-IDENTITY-GIT-ROOT", f"Git root mismatch: {root!r}")


def clean_status() -> bytes:
    return run_git(
        [
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
            "--ignore-submodules=none",
        ]
    )


def ignored_paths() -> bytes:
    return run_git(["ls-files", "--others", "--ignored", "--exclude-standard", "-z"])


def require_release_clean(status_output: bytes, ignored_output: bytes) -> None:
    if status_output or ignored_output:
        raise GateError(
            "GA12-RELEASE-SNAPSHOT-DIRTY",
            "release mode requires no staged, modified, deleted, submodule, untracked, or ignored paths",
        )


def require_release_index_flag(record: bytes) -> None:
    if len(record) < 3 or record[:2] != b"H ":
        path = (
            record[2:].decode("utf-8", "replace") if len(record) >= 2 else "<invalid>"
        )
        raise GateError(
            "GA12-RELEASE-INDEX-FLAG",
            f"assume-unchanged, skip-worktree, unresolved, or unexpected index flag at {path}",
        )


def git_oid(data: bytes, object_format: str, object_type: str = "blob") -> str:
    if object_type not in {"blob", "commit", "tree"}:
        raise GateError(
            "GA12-GIT-OBJECT-TYPE", f"unsupported Git object type: {object_type}"
        )
    framed = (
        object_type.encode("ascii")
        + b" "
        + str(len(data)).encode("ascii")
        + b"\x00"
        + data
    )
    if object_format == "sha1":
        return hashlib.sha1(framed, usedforsecurity=False).hexdigest()
    if object_format == "sha256":
        return hashlib.sha256(framed).hexdigest()
    raise GateError(
        "GA12-GIT-OBJECT-FORMAT", f"unsupported Git object format: {object_format}"
    )


def projection(files: Mapping[str, SnapshotFile]) -> tuple[str, int, int]:
    records = [
        {
            "mode": item.mode,
            "path": path,
            "sha256": item.sha256,
            "size": item.size,
        }
        for path, item in sorted(files.items())
    ]
    encoded = json.dumps(
        records, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return (
        hashlib.sha256(encoded).hexdigest(),
        len(records),
        sum(x["size"] for x in records),
    )


def release_snapshot() -> RepositorySnapshot:
    require_release_clean(clean_status(), ignored_paths())
    commit = run_git(["rev-parse", "--verify", "HEAD^{commit}"]).decode("ascii").strip()
    tree = run_git(["rev-parse", "--verify", "HEAD^{tree}"]).decode("ascii").strip()
    object_format = (
        run_git(["rev-parse", "--show-object-format"]).decode("ascii").strip()
    )
    commit_bytes = run_git(["cat-file", "commit", commit])
    if git_oid(commit_bytes, object_format, "commit") != commit:
        raise GateError(
            "GA12-GIT-COMMIT-DIGEST",
            "HEAD commit bytes do not match its object identifier",
        )
    tree_bytes = run_git(["cat-file", "tree", tree])
    if git_oid(tree_bytes, object_format, "tree") != tree:
        raise GateError(
            "GA12-GIT-TREE-DIGEST", "HEAD tree bytes do not match its object identifier"
        )
    listing = run_git(["ls-tree", "-rz", "--full-tree", "-r", commit])
    files: dict[str, SnapshotFile] = {}
    for raw_record in listing.split(b"\x00"):
        if not raw_record:
            continue
        try:
            header, raw_path = raw_record.split(b"\t", 1)
            mode_raw, object_type, oid_raw = header.split(b" ", 2)
            path = raw_path.decode("utf-8", "strict")
            mode = mode_raw.decode("ascii")
            oid = oid_raw.decode("ascii")
        except (ValueError, UnicodeDecodeError) as exc:
            raise GateError("GA12-GIT-TREE-RECORD", "invalid Git tree record") from exc
        if object_type != b"blob" or mode not in {"100644", "100755"}:
            raise GateError(
                "GA12-GIT-TREE-MODE",
                f"release snapshot rejects non-regular entry {path!r} ({mode_raw!r}, {object_type!r})",
            )
        validate_repository_path(path)
        if path in files:
            raise GateError("GA12-GIT-TREE-DUPLICATE", f"duplicate Git path: {path}")
        data = run_git(["cat-file", "blob", oid])
        if git_oid(data, object_format) != oid:
            raise GateError(
                "GA12-GIT-BLOB-DIGEST", f"Git blob digest mismatch for {path}"
            )
        files[path] = SnapshotFile(path=path, mode=mode, data=data)
    digest, count, byte_count = projection(files)
    snapshot = RepositorySnapshot(
        mode="release",
        files=MappingProxyType(files),
        projection_sha256=digest,
        file_count=count,
        byte_count=byte_count,
        commit=commit,
        tree=tree,
        object_format=object_format,
    )
    verify_release_checkout(snapshot)
    return snapshot


def immutable_git_snapshot_at_commit(
    commit: str,
    object_format: str,
) -> RepositorySnapshot:
    if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", commit):
        raise GateError(
            "GA12-PUBLICATION-EVENT-TOPOLOGY",
            "publication parent commit is not a canonical Git object identifier",
        )
    commit_bytes = run_git(["cat-file", "commit", commit])
    if git_oid(commit_bytes, object_format, "commit") != commit:
        raise GateError(
            "GA12-PUBLICATION-EVENT-TOPOLOGY",
            "publication parent commit bytes differ from its object identifier",
        )
    tree = run_git(["rev-parse", "--verify", f"{commit}^{{tree}}"])
    tree_id = tree.decode("ascii", "strict").strip()
    tree_bytes = run_git(["cat-file", "tree", tree_id])
    if git_oid(tree_bytes, object_format, "tree") != tree_id:
        raise GateError(
            "GA12-PUBLICATION-EVENT-TOPOLOGY",
            "publication parent tree bytes differ from its object identifier",
        )
    files: dict[str, SnapshotFile] = {}
    listing = run_git(["ls-tree", "-rz", "--full-tree", "-r", commit])
    for raw_record in listing.split(b"\x00"):
        if not raw_record:
            continue
        try:
            header, raw_path = raw_record.split(b"\t", 1)
            mode_raw, object_type, oid_raw = header.split(b" ", 2)
            path = raw_path.decode("utf-8", "strict")
            mode = mode_raw.decode("ascii")
            oid = oid_raw.decode("ascii")
        except (ValueError, UnicodeDecodeError) as exc:
            raise GateError(
                "GA12-PUBLICATION-EVENT-TOPOLOGY",
                "publication parent tree record is invalid",
            ) from exc
        if object_type != b"blob" or mode not in {"100644", "100755"}:
            raise GateError(
                "GA12-PUBLICATION-EVENT-TOPOLOGY",
                f"publication parent contains a non-regular entry: {path}",
            )
        validate_repository_path(path)
        if path in files:
            raise GateError(
                "GA12-PUBLICATION-EVENT-TOPOLOGY",
                f"publication parent repeats a path: {path}",
            )
        data = run_git(["cat-file", "blob", oid])
        if git_oid(data, object_format) != oid:
            raise GateError(
                "GA12-PUBLICATION-EVENT-TOPOLOGY",
                f"publication parent blob differs from its object ID: {path}",
            )
        files[path] = SnapshotFile(path=path, mode=mode, data=data)
    digest, count, byte_count = projection(files)
    return RepositorySnapshot(
        mode="release",
        files=MappingProxyType(files),
        projection_sha256=digest,
        file_count=count,
        byte_count=byte_count,
        commit=commit,
        tree=tree_id,
        object_format=object_format,
    )


def verify_release_checkout(snapshot: RepositorySnapshot) -> None:
    """Prove index and live tracked files equal the selected immutable tree."""

    flag_records = run_git(["ls-files", "-v", "-z"])
    for record in flag_records.split(b"\x00"):
        if not record:
            continue
        require_release_index_flag(record)

    index: dict[str, tuple[str, str]] = {}
    for record in run_git(["ls-files", "--stage", "-z"]).split(b"\x00"):
        if not record:
            continue
        try:
            metadata, raw_path = record.split(b"\t", 1)
            raw_mode, raw_oid, raw_stage = metadata.split(b" ", 2)
            path = raw_path.decode("utf-8", "strict")
            mode = raw_mode.decode("ascii")
            oid = raw_oid.decode("ascii")
            stage = raw_stage.decode("ascii")
        except (ValueError, UnicodeDecodeError) as exc:
            raise GateError(
                "GA12-RELEASE-INDEX-RECORD", "invalid Git index record"
            ) from exc
        validate_repository_path(path)
        if stage != "0" or path in index:
            raise GateError(
                "GA12-RELEASE-INDEX-STAGE", f"unmerged or duplicate index entry: {path}"
            )
        index[path] = (mode, oid)

    if set(index) != set(snapshot.files):
        raise GateError(
            "GA12-RELEASE-INDEX-TREE", "Git index paths differ from the selected tree"
        )
    if snapshot.object_format is None:
        raise GateError(
            "GA12-RELEASE-SNAPSHOT-SHAPE", "release snapshot lacks object format"
        )
    for path, item in sorted(snapshot.files.items()):
        expected_index = (item.mode, git_oid(item.data, snapshot.object_format))
        if index[path] != expected_index:
            raise GateError(
                "GA12-RELEASE-INDEX-TREE", f"Git index entry differs from tree: {path}"
            )
        live_path = CANONICAL_ROOT / path
        try:
            metadata = live_path.lstat()
        except OSError as exc:
            raise GateError(
                "GA12-RELEASE-WORKTREE", f"cannot stat tracked path {path}: {exc}"
            ) from exc
        if not stat.S_ISREG(metadata.st_mode):
            raise GateError(
                "GA12-RELEASE-WORKTREE", f"tracked path is not a regular file: {path}"
            )
        live_bytes = stable_regular_bytes(live_path)
        if live_bytes != item.data:
            raise GateError(
                "GA12-RELEASE-WORKTREE", f"tracked bytes differ from tree: {path}"
            )
        expected_executable = item.mode == "100755"
        observed_executable = bool(stat.S_IMODE(metadata.st_mode) & 0o111)
        if observed_executable != expected_executable:
            raise GateError(
                "GA12-RELEASE-WORKTREE-MODE",
                f"tracked execute mode differs from tree: {path}",
            )


def validate_repository_path(path: str) -> None:
    try:
        path.encode("utf-8", "strict")
    except UnicodeEncodeError as exc:
        raise GateError(
            "GA12-SNAPSHOT-PATH", f"repository path is not strict UTF-8: {path!r}"
        ) from exc
    pure = PurePosixPath(path)
    if (
        not path
        or path.startswith("/")
        or "\\" in path
        or "\x00" in path
        or pure.is_absolute()
        or any(part in {"", ".", ".."} for part in pure.parts)
    ):
        raise GateError("GA12-SNAPSHOT-PATH", f"unsafe repository path: {path!r}")


def _filesystem_inventory() -> dict[str, SnapshotFile]:
    files: dict[str, SnapshotFile] = {}

    def walk(directory: Path, relative: PurePosixPath) -> None:
        try:
            entries = sorted(
                os.scandir(directory), key=lambda item: os.fsencode(item.name)
            )
        except OSError as exc:
            raise GateError(
                "GA12-DEVELOPMENT-SNAPSHOT-READ", f"cannot scan {directory}: {exc}"
            ) from exc
        for entry in entries:
            if relative == PurePosixPath(".") and entry.name == ".git":
                continue
            child_relative = (
                PurePosixPath(entry.name)
                if relative == PurePosixPath(".")
                else relative / entry.name
            )
            path_text = child_relative.as_posix()
            validate_repository_path(path_text)
            try:
                metadata = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise GateError(
                    "GA12-DEVELOPMENT-SNAPSHOT-READ", f"cannot stat {path_text}: {exc}"
                ) from exc
            if stat.S_ISLNK(metadata.st_mode):
                raise GateError(
                    "GA12-DEVELOPMENT-SNAPSHOT-SYMLINK",
                    f"symlink rejected: {path_text}",
                )
            if stat.S_ISDIR(metadata.st_mode):
                walk(Path(entry.path), child_relative)
                continue
            if not stat.S_ISREG(metadata.st_mode):
                raise GateError(
                    "GA12-DEVELOPMENT-SNAPSHOT-SPECIAL",
                    f"special path rejected: {path_text}",
                )
            flags = (
                os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
            )
            try:
                descriptor = os.open(entry.path, flags)
            except OSError as exc:
                raise GateError(
                    "GA12-DEVELOPMENT-SNAPSHOT-OPEN", f"cannot open {path_text}: {exc}"
                ) from exc
            try:
                before = os.fstat(descriptor)
                chunks: list[bytes] = []
                while chunk := os.read(descriptor, 1024 * 1024):
                    chunks.append(chunk)
                after = os.fstat(descriptor)
            finally:
                os.close(descriptor)
            observed = (
                before.st_dev,
                before.st_ino,
                before.st_mode,
                before.st_size,
                before.st_mtime_ns,
                before.st_ctime_ns,
            )
            final = (
                after.st_dev,
                after.st_ino,
                after.st_mode,
                after.st_size,
                after.st_mtime_ns,
                after.st_ctime_ns,
            )
            data = b"".join(chunks)
            if observed != final or len(data) != before.st_size:
                raise GateError(
                    "GA12-DEVELOPMENT-SNAPSHOT-DRIFT",
                    f"file drifted while read: {path_text}",
                )
            mode = f"{stat.S_IMODE(before.st_mode):04o}"
            files[path_text] = SnapshotFile(path=path_text, mode=mode, data=data)

    walk(CANONICAL_ROOT, PurePosixPath("."))
    return files


def development_snapshot() -> RepositorySnapshot:
    first = _filesystem_inventory()
    first_digest, first_count, first_bytes = projection(first)
    second = _filesystem_inventory()
    second_digest, second_count, second_bytes = projection(second)
    require_development_projection_match(
        (first_digest, first_count, first_bytes),
        (second_digest, second_count, second_bytes),
    )
    return RepositorySnapshot(
        mode="development",
        files=MappingProxyType(first),
        projection_sha256=first_digest,
        file_count=first_count,
        byte_count=first_bytes,
        commit=None,
        tree=None,
        object_format=None,
    )


def require_development_projection_match(before: object, after: object) -> None:
    if before != after:
        raise GateError(
            "GA12-DEVELOPMENT-SNAPSHOT-DRIFT",
            "repository inventory changed between complete filesystem observations",
        )


def finalize_snapshot(snapshot: RepositorySnapshot) -> None:
    if snapshot.mode == "release":
        current_commit = (
            run_git(["rev-parse", "--verify", "HEAD^{commit}"]).decode("ascii").strip()
        )
        current_tree = (
            run_git(["rev-parse", "--verify", "HEAD^{tree}"]).decode("ascii").strip()
        )
        if current_commit != snapshot.commit or current_tree != snapshot.tree:
            raise GateError(
                "GA12-RELEASE-SNAPSHOT-DRIFT",
                "HEAD or its tree changed during validation",
            )
        require_release_clean(clean_status(), ignored_paths())
        verify_release_checkout(snapshot)
        return
    current = _filesystem_inventory()
    digest, count, byte_count = projection(current)
    require_development_projection_match(
        (snapshot.projection_sha256, snapshot.file_count, snapshot.byte_count),
        (digest, count, byte_count),
    )


def reject_constant(value: str) -> NoReturn:
    raise ValueError(f"non-finite JSON number is forbidden: {value}")


def finite_json_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"JSON number overflows the finite binary64 profile: {value}")
    return parsed


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON property: {key}")
        result[key] = value
    return result


def strict_json(data: bytes, path: str) -> Any:
    try:
        text = data.decode("utf-8", "strict")
        return json.loads(
            text,
            object_pairs_hook=reject_duplicate_pairs,
            parse_constant=reject_constant,
            parse_float=finite_json_float,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise GateError(
            "GA12-STRICT-JSON", f"invalid strict JSON at {path}: {exc}"
        ) from exc


def is_calendar_date(value: object) -> bool:
    if not isinstance(value, str):
        return True
    match = DATE_PATTERN.fullmatch(value)
    if not match:
        return False
    try:
        parsed = date(int(match[1]), int(match[2]), int(match[3]))
    except ValueError:
        return False
    return parsed.isoformat() == value


def is_rfc3339_datetime(value: object) -> bool:
    if not isinstance(value, str):
        return True
    match = DATETIME_PATTERN.fullmatch(value)
    if not match:
        return False
    year, month, day, hour, minute, second = (
        int(match[index]) for index in range(1, 7)
    )
    if hour > 23 or minute > 59 or second > 60:
        return False
    if match[8] is not None:
        offset_hour, offset_minute = int(match[9]), int(match[10])
        if offset_hour > 23 or offset_minute > 59:
            return False
    offset_minutes = 0
    if match[8] is not None:
        offset_minutes = int(match[9]) * 60 + int(match[10])
        if match[8] == "-":
            offset_minutes = -offset_minutes
    try:
        parsed = datetime(
            year,
            month,
            day,
            hour,
            minute,
            min(second, 59),
            tzinfo=timezone(timedelta(minutes=offset_minutes)),
        )
    except ValueError:
        return False
    if second == 60:
        # Leap-second validity is an announced UTC fact, not merely a month-end
        # shape.  Convert any numeric-offset representation to UTC and require a
        # member of the reviewed table above.
        utc = parsed.astimezone(timezone.utc)
        if (
            utc.hour != 23
            or utc.minute != 59
            or utc.date().isoformat() not in ANNOUNCED_POSITIVE_LEAP_SECOND_DATES
        ):
            return False
    return True


def is_absolute_uri(value: object) -> bool:
    if not isinstance(value, str):
        return True
    if (
        not value
        or not value.isascii()
        or any(ord(char) <= 0x20 or ord(char) == 0x7F for char in value)
    ):
        return False
    if any(character not in URI_ASCII_CHARACTERS for character in value):
        return False
    if "\\" in value or BAD_PERCENT_PATTERN.search(value):
        return False
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    if not URI_SCHEME_PATTERN.fullmatch(parsed.scheme):
        return False
    if parsed.scheme.lower() in {"http", "https"}:
        if not parsed.netloc or parsed.hostname is None or not parsed.hostname:
            return False
        try:
            _ = parsed.port
        except ValueError:
            return False
        if parsed.username is not None or parsed.password is not None:
            return False
        bracketed_authority = parsed.netloc.startswith("[")
        if "[" in value or "]" in value:
            if (
                not bracketed_authority
                or value.count("[") != 1
                or value.count("]") != 1
            ):
                return False
        if bracketed_authority:
            closing = parsed.netloc.find("]")
            if closing < 0:
                return False
            literal = parsed.netloc[1:closing]
            if IPVFUTURE_PATTERN.fullmatch(literal) is None:
                try:
                    ipaddress.IPv6Address(literal)
                except ipaddress.AddressValueError:
                    return False
    elif not value[len(parsed.scheme) + 1 :]:
        return False
    elif "[" in value or "]" in value:
        return False
    return True


def is_https_uri(value: object) -> bool:
    if not isinstance(value, str):
        return True
    if not is_absolute_uri(value):
        return False
    return urlsplit(value).scheme.lower() == "https"


FORMAT_CHECKERS: Mapping[str, Callable[[object], bool]] = MappingProxyType(
    {
        "date": is_calendar_date,
        "date-time": is_rfc3339_datetime,
        "uri": is_absolute_uri,
        "https-uri": is_https_uri,
    }
)
FORMAT_DIAGNOSTICS = {
    "date": "GA12-FORMAT-DATE",
    "date-time": "GA12-FORMAT-DATE-TIME",
    "uri": "GA12-FORMAT-URI",
    "https-uri": "GA12-FORMAT-HTTPS-URI",
}

REQUIRED_SECURITY_FIXTURES = {
    "reiyah.fixture.validator-security.actual-publication-event-fault-matrix@1.2.0": "GA12-PUBLICATION-EVENT-ACTUAL-CANARY-COVERAGE",
    "reiyah.fixture.validator-security.catalog-byte-digest@1.2.0": "GA12-FIXTURE-CATALOG-BYTE-DIGEST",
    "reiyah.fixture.validator-security.catalog-byte-size@1.2.0": "GA12-FIXTURE-CATALOG-BYTE-SIZE",
    "reiyah.fixture.validator-security.catalog-duplicate-id@1.2.0": "GA12-FIXTURE-CATALOG-ID-UNIQUE",
    "reiyah.fixture.validator-security.catalog-duplicate-path@1.2.0": "GA12-FIXTURE-CATALOG-PATH-UNIQUE",
    "reiyah.fixture.validator-security.catalog-expected-primary-rule@1.2.0": "GA12-FIXTURE-CATALOG-EXPECTED-PRIMARY-RULE",
    "reiyah.fixture.validator-security.catalog-fixture-schema@1.2.0": "GA12-FIXTURE-CATALOG-FIXTURE-SCHEMA",
    "reiyah.fixture.validator-security.catalog-identity-source@1.2.0": "GA12-FIXTURE-CATALOG-IDENTITY-SOURCE",
    "reiyah.fixture.validator-security.catalog-missing-row@1.2.0": "GA12-FIXTURE-CATALOG-MISSING-ROW",
    "reiyah.fixture.validator-security.catalog-replay-mode@1.2.0": "GA12-FIXTURE-CATALOG-REPLAY-MODE",
    "reiyah.fixture.validator-security.catalog-target-schema@1.2.0": "GA12-FIXTURE-CATALOG-TARGET-SCHEMA",
    "reiyah.fixture.validator-security.catalog-unexpected-row@1.2.0": "GA12-FIXTURE-CATALOG-UNEXPECTED-ROW",
    "reiyah.fixture.validator-security.development-drift@1.2.0": "GA12-DEVELOPMENT-SNAPSHOT-DRIFT",
    "reiyah.fixture.validator-security.executable-contract-operand-matrix@1.2.0": "GA12-EXECUTABLE-CONTRACT-OPERAND-COVERAGE",
    "reiyah.fixture.validator-security.invalid-date-time@1.2.0": "GA12-FORMAT-DATE-TIME",
    "reiyah.fixture.validator-security.invalid-uri@1.2.0": "GA12-FORMAT-URI",
    "reiyah.fixture.validator-security.joint-opportunity-registry-manifest-binding-matrix@1.2.0": "GA12-JOINT-OPPORTUNITY-REGISTRY-MANIFEST-CANARY-COVERAGE",
    "reiyah.fixture.validator-security.missing-isolation@1.2.0": "GA12-LAUNCHER-PROFILE",
    "reiyah.fixture.validator-security.narrative-state-contradiction@1.2.0": "GA12-NARRATIVE-STATE-CONSISTENCY",
    "reiyah.fixture.validator-security.normative-surface-path-substitution@1.2.0": "GA12-NORMATIVE-ARCHITECTURE-SURFACE",
    "reiyah.fixture.validator-security.ope-registry-manifest-binding-matrix@1.2.0": "GA12-OPE-REGISTRY-MANIFEST-CANARY-COVERAGE",
    "reiyah.fixture.validator-security.plan-tool-binding-launcher@1.2.0": "GA12-PLAN-TOOL-BINDING",
    "reiyah.fixture.validator-security.plan-tool-binding-primary-validator@1.2.0": "GA12-PLAN-TOOL-BINDING",
    "reiyah.fixture.validator-security.plan-tool-binding-science-module@1.2.0": "GA12-PLAN-TOOL-BINDING",
    "reiyah.fixture.validator-security.plan-tool-binding-toolchain-lock@1.2.0": "GA12-PLAN-TOOL-BINDING",
    "reiyah.fixture.validator-security.profile-execution-binding@1.2.0": "GA12-SCIENCE-PROFILE-EXECUTION",
    "reiyah.fixture.validator-security.profile-execution-launcher-binding@1.2.0": "GA12-SCIENCE-PROFILE-EXECUTION",
    "reiyah.fixture.validator-security.profile-execution-tool-binding@1.2.0": "GA12-SCIENCE-PROFILE-EXECUTION",
    "reiyah.fixture.validator-security.profile-execution-toolchain-lock-binding@1.2.0": "GA12-SCIENCE-PROFILE-EXECUTION",
    "reiyah.fixture.validator-security.reference-path-duplicate@1.2.0": "GA12-REFERENCE-PATH-COVERAGE",
    "reiyah.fixture.validator-security.reference-path-handler-only@1.2.0": "GA12-REFERENCE-PATH-COVERAGE",
    "reiyah.fixture.validator-security.reference-path-missing@1.2.0": "GA12-REFERENCE-PATH-COVERAGE",
    "reiyah.fixture.validator-security.release-dirty-state@1.2.0": "GA12-RELEASE-SNAPSHOT-DIRTY",
    "reiyah.fixture.validator-security.release-index-flag@1.2.0": "GA12-RELEASE-INDEX-FLAG",
    "reiyah.fixture.validator-security.release-worker-fault-matrix@1.2.0": "GA12-DUAL-EVALUATION-CANARY-COVERAGE",
    "reiyah.fixture.validator-security.report-good-count-mismatch@1.2.0": "GA12-REPORT-GOOD-COUNT",
    "reiyah.fixture.validator-security.report-governance-count-mismatch@1.2.0": "GA12-REPORT-GOVERNANCE-COUNT",
    "reiyah.fixture.validator-security.report-science-bad-count-mismatch@1.2.0": "GA12-REPORT-SCIENCE-BAD-COUNT",
    "reiyah.fixture.validator-security.report-security-count-mismatch@1.2.0": "GA12-REPORT-SECURITY-COUNT",
    "reiyah.fixture.validator-security.registry-definition-id-duplicate@1.2.0": "GA12-REGISTRY-DEFINITION-ID-UNIQUE",
    "reiyah.fixture.validator-security.registry-executable-contract-id-duplicate@1.2.0": "GA12-REGISTRY-EXECUTABLE-CONTRACT-ID-UNIQUE",
    "reiyah.fixture.validator-security.registry-reference-kind-id-duplicate@1.2.0": "GA12-REGISTRY-REFERENCE-KIND-ID-UNIQUE",
    "reiyah.fixture.validator-security.research-registry-earlier-date@1.2.0": "GA12-RESEARCH-REGISTRY-CHRONOLOGY",
    "reiyah.fixture.validator-security.science-artifact-id-duplicate@1.2.0": "GA12-SCIENCE-ARTIFACT-ID-UNIQUE",
    "reiyah.fixture.validator-security.science-lineage-fork@1.2.0": "GA12-SCIENCE-LINEAGE-FORK",
    "reiyah.fixture.validator-security.science-logical-version-duplicate@1.2.0": "GA12-SCIENCE-LOGICAL-VERSION-UNIQUE",
    "reiyah.fixture.validator-security.selector-fixture-set-digest-mismatch@1.2.0": "GA12-PLAN-EVIDENCE-SELECTOR-DIGEST",
    "reiyah.fixture.validator-security.selector-missing-fixture@1.2.0": "GA12-PLAN-EVIDENCE-SELECTOR-FIXTURE-MISSING",
    "reiyah.fixture.validator-security.selector-missing-observation@1.2.0": "GA12-PLAN-EVIDENCE-SELECTOR-OBSERVATION-MISSING",
    "reiyah.fixture.validator-security.selector-producer-substitution@1.2.0": "GA12-PLAN-EVIDENCE-SELECTOR-PRODUCER",
    "reiyah.fixture.validator-security.selector-unexpected-fixture@1.2.0": "GA12-PLAN-EVIDENCE-SELECTOR-FIXTURE-UNEXPECTED",
    "reiyah.fixture.validator-security.self-membership-byte-mismatch@1.2.0": "GA12-SELF-MEMBERSHIP",
    "reiyah.fixture.validator-security.toolchain-byte-mismatch@1.2.0": "GA12-TOOLCHAIN-BYTE-MISMATCH",
    "reiyah.fixture.validator-security.transport-self-attestation@1.2.0": "GA12-TRANSPORT-EXTERNALLY-UNVERIFIED",
    "reiyah.fixture.validator-security.unknown-format@1.2.0": "GA12-FORMAT-CHECKER-UNKNOWN",
}

GOVERNANCE_POSITIVE_PATH_TO_ID = {
    "fixtures/v1.2/governance-good/iso-rights-observation-capture.json": (
        "reiyah.fixture.governance-good.iso-rights-observation-capture@1.2.0"
    ),
    "fixtures/v1.2/governance-good/nist-rights-observation-capture.json": (
        "reiyah.fixture.governance-good.nist-rights-observation-capture@1.2.0"
    ),
    "fixtures/v1.2/governance-good/public-distribution-receipt.json": (
        "reiyah.fixture.governance-good.public-distribution-receipt@1.2.0"
    ),
    "fixtures/v1.2/governance-good/public-rights-revalidation.json": (
        "reiyah.fixture.governance-good.public-rights-revalidation@1.2.0"
    ),
}

REQUIRED_PUBLICATION_GOVERNANCE_FIXTURES = {
    "reiyah.fixture.governance.capture-chronology@1.2.0": "GA12-CAPTURE-CHRONOLOGY",
    "reiyah.fixture.governance.capture-no-credentials@1.2.0": "GA12-CAPTURE-NO-CREDENTIALS",
    "reiyah.fixture.governance.capture-no-raw-body@1.2.0": "GA12-CAPTURE-NO-RAW-BODY",
    "reiyah.fixture.governance.capture-response-digest-scope@1.2.0": "GA12-CAPTURE-RESPONSE-DIGEST-SCOPE",
    "reiyah.fixture.governance.capture-role-path@1.2.0": "GA12-CAPTURE-ROLE-PATH",
    "reiyah.fixture.governance.capture-schema-binding@1.2.0": "GA12-CAPTURE-SCHEMA-BINDING",
    "reiyah.fixture.governance.capture-url@1.2.0": "GA12-CAPTURE-URL",
    "reiyah.fixture.governance.positive-byte-binding@1.2.0": "GA12-GOVERNANCE-POSITIVE-BYTE-BINDING",
    "reiyah.fixture.governance.publication-event-binding@1.2.0": "GA12-PUBLICATION-EVENT-BINDING",
    "reiyah.fixture.governance.publication-event-chronology@1.2.0": "GA12-PUBLICATION-EVENT-CHRONOLOGY",
    "reiyah.fixture.governance.publication-topology-exclusion@1.2.0": "GA12-PUBLICATION-TOPOLOGY-EXCLUSION",
    "reiyah.fixture.governance.publication-topology-packet-state@1.2.0": "GA12-PUBLICATION-TOPOLOGY-PACKET-STATE",
    "reiyah.fixture.governance.publication-topology-receipt-state@1.2.0": "GA12-PUBLICATION-TOPOLOGY-RECEIPT-STATE",
    "reiyah.fixture.governance.publication-topology-self-cycle@1.2.0": "GA12-PUBLICATION-TOPOLOGY-SELF-CYCLE",
    "reiyah.fixture.governance.receipt-independent-verification-claim@1.2.0": "GA12-RECEIPT-INDEPENDENT-VERIFICATION-CLAIM",
    "reiyah.fixture.governance.receipt-stale-rights-schema@1.2.0": "GA12-RIGHTS-SCHEMA-BINDING",
    "reiyah.fixture.governance.rights-capture-binding@1.2.0": "GA12-RIGHTS-CAPTURE-BINDING",
    "reiyah.fixture.governance.rights-capture-coverage@1.2.0": "GA12-RIGHTS-CAPTURE-COVERAGE",
    "reiyah.fixture.governance.rights-capture-freshness@1.2.0": "GA12-RIGHTS-CAPTURE-FRESHNESS",
}

REQUIRED_TRANSPORT_GOVERNANCE_FIXTURES = {
    "reiyah.fixture.governance.transport-authorization-capture-lower-bound@1.2.0": "GA12-TRANSPORT-CHRONOLOGY",
    "reiyah.fixture.governance.transport-authorization-commit-mismatch@1.2.0": "GA12-TRANSPORT-AUTHORIZATION-BINDING",
    "reiyah.fixture.governance.transport-authorization-event-mismatch@1.2.0": "GA12-TRANSPORT-AUTHORIZATION-BINDING",
    "reiyah.fixture.governance.transport-authorization-expiry-boundary@1.2.0": "GA12-TRANSPORT-CHRONOLOGY",
    "reiyah.fixture.governance.transport-authorization-index-mismatch@1.2.0": "GA12-TRANSPORT-AUTHORIZATION-BINDING",
    "reiyah.fixture.governance.transport-authorization-receipt-boundary@1.2.0": "GA12-TRANSPORT-CHRONOLOGY",
    "reiyah.fixture.governance.transport-authorization-reference-binding-mismatch@1.2.0": "GA12-TRANSPORT-AUTHORIZATION-BINDING",
    "reiyah.fixture.governance.transport-authorization-report-mismatch@1.2.0": "GA12-TRANSPORT-AUTHORIZATION-BINDING",
    "reiyah.fixture.governance.transport-authorization-start-boundary@1.2.0": "GA12-TRANSPORT-CHRONOLOGY",
    "reiyah.fixture.governance.transport-authorization-target-identity-mismatch@1.2.0": "GA12-TRANSPORT-AUTHORIZATION-BINDING",
    "reiyah.fixture.governance.transport-chronology-violation@1.2.0": "GA12-TRANSPORT-CHRONOLOGY",
    "reiyah.fixture.governance.transport-dangling-evidence@1.2.0": "GA12-TRANSPORT-EVIDENCE-RESOLUTION",
    "reiyah.fixture.governance.transport-evidence-duplicate-retained-id@1.2.0": "GA12-TRANSPORT-EVIDENCE-RESOLUTION",
    "reiyah.fixture.governance.transport-evidence-payload-digest-mismatch@1.2.0": "GA12-TRANSPORT-EVIDENCE-RESOLUTION",
    "reiyah.fixture.governance.transport-evidence-payload-digest-recomputation@1.2.0": "GA12-TRANSPORT-EVIDENCE-RESOLUTION",
    "reiyah.fixture.governance.transport-evidence-payload-size-mismatch@1.2.0": "GA12-TRANSPORT-EVIDENCE-RESOLUTION",
    "reiyah.fixture.governance.transport-evidence-payload-size-recomputation@1.2.0": "GA12-TRANSPORT-EVIDENCE-RESOLUTION",
    "reiyah.fixture.governance.transport-evidence-unused-retained@1.2.0": "GA12-TRANSPORT-EVIDENCE-RESOLUTION",
    "reiyah.fixture.governance.transport-evidence-wrapper-record-mismatch@1.2.0": "GA12-TRANSPORT-EVIDENCE-RESOLUTION",
    "reiyah.fixture.governance.transport-insubstantive-independence-basis@1.2.0": "GA12-TRANSPORT-OBSERVER-INDEPENDENCE-BASIS",
    "reiyah.fixture.governance.transport-missing-authorization@1.2.0": "GA12-TRANSPORT-AUTHORIZATION-BINDING",
    "reiyah.fixture.governance.transport-observed-boundary@1.2.0": "GA12-TRANSPORT-CHRONOLOGY",
    "reiyah.fixture.governance.transport-observer-identity-collision@1.2.0": "GA12-TRANSPORT-OBSERVER-IDENTITY-SEPARATION",
    "reiyah.fixture.governance.transport-publication-c-packet-binding-mismatch@1.2.0": "GA12-TRANSPORT-PUBLICATION-BINDING",
    "reiyah.fixture.governance.transport-publication-stale-digest@1.2.0": "GA12-TRANSPORT-PUBLICATION-BYTE-BINDING",
    "reiyah.fixture.governance.transport-publication-stale-size@1.2.0": "GA12-TRANSPORT-PUBLICATION-BYTE-BINDING",
    "reiyah.fixture.governance.transport-publication-strict-boundary-equality@1.2.0": "GA12-TRANSPORT-CHRONOLOGY",
    "reiyah.fixture.governance.transport-publication-topology-mismatch@1.2.0": "GA12-TRANSPORT-PUBLICATION-BINDING",
    "reiyah.fixture.governance.transport-receipt-binding-mismatch@1.2.0": "GA12-TRANSPORT-PUBLICATION-BINDING",
    "reiyah.fixture.governance.transport-reference-chronology-violation@1.2.0": "GA12-TRANSPORT-EVIDENCE-REFERENCE-CHRONOLOGY",
    "reiyah.fixture.governance.transport-unauthenticated-verifier@1.2.0": "GA12-TRANSPORT-OBSERVER-AUTHENTICATION",
}

REQUIRED_GOVERNANCE_FIXTURES = {
    **REQUIRED_PUBLICATION_GOVERNANCE_FIXTURES,
    **REQUIRED_TRANSPORT_GOVERNANCE_FIXTURES,
}

SCIENCE_SELECTOR_REQUIRED_OBSERVATIONS: Mapping[str, tuple[Mapping[str, Any], ...]] = (
    MappingProxyType(
        {
            "reiyah.evidence-selector.science.belief-reconciliation": (
                {
                    "observation_id": "reiyah.selector-observation.science.belief-reconciliation-known-good@1.2.0",
                    "fixture_ids": (
                        "reiyah.fixture.good.v12.human-automation-assessment",
                        "reiyah.fixture.good.v12.human-automation-assessment-observation-abstained",
                        "reiyah.fixture.good.v12.human-automation-assessment-observation-missing",
                        "reiyah.fixture.good.v12.human-automation-assessment-observation-out-of-distribution",
                        "reiyah.fixture.good.v12.human-automation-assessment-observation-sensor-invalid",
                        "reiyah.fixture.good.v12.human-automation-assessment-observation-unmeasured",
                    ),
                },
                {
                    "observation_id": "reiyah.selector-observation.science.belief-reconciliation-known-bad@1.2.0",
                    "fixture_ids": (
                        "reiyah.fixture.bad.belief_distribution_sum_mismatch",
                        "reiyah.fixture.bad.belief_normalization_policy_binding_mismatch",
                        "reiyah.fixture.bad.belief_state_space_coverage_mismatch",
                        "reiyah.fixture.bad.estimand_binding_human_belief_mismatch",
                        "reiyah.fixture.bad.estimand_operand_human_belief_gap",
                        "reiyah.fixture.bad.human_information_set_reconciliation_mismatch",
                        "reiyah.fixture.bad.human_object_reconciliation_mismatch",
                        "reiyah.fixture.bad.human_observation_availability_after_belief",
                        "reiyah.fixture.bad.human_observation_availability_before_measurement",
                        "reiyah.fixture.bad.human_observation_availability_nonobserved",
                        "reiyah.fixture.bad.human_observation_event_after_measurement",
                        "reiyah.fixture.bad.human_observation_event_nonobserved",
                        "reiyah.fixture.bad.human_subject_belief_holder_mismatch",
                        "reiyah.fixture.bad.human_subject_decision_actor_mismatch",
                        "reiyah.fixture.bad.human_subject_readiness_mismatch",
                        "reiyah.fixture.bad.human_temporal_reconciliation_mismatch",
                    ),
                },
            ),
            "reiyah.evidence-selector.science.observation-validity-reconciliation": (
                {
                    "observation_id": "reiyah.selector-observation.science.observation-validity-reconciliation-known-good@1.2.0",
                    "fixture_ids": (
                        "reiyah.fixture.good.v12.human-automation-assessment",
                        "reiyah.fixture.good.v12.human-automation-assessment-observation-abstained",
                        "reiyah.fixture.good.v12.human-automation-assessment-observation-missing",
                        "reiyah.fixture.good.v12.human-automation-assessment-observation-out-of-distribution",
                        "reiyah.fixture.good.v12.human-automation-assessment-observation-sensor-invalid",
                        "reiyah.fixture.good.v12.human-automation-assessment-observation-unmeasured",
                    ),
                },
                {
                    "observation_id": "reiyah.selector-observation.science.observation-validity-reconciliation-known-bad@1.2.0",
                    "fixture_ids": (
                        "reiyah.fixture.bad.human_information_set_reconciliation_mismatch",
                        "reiyah.fixture.bad.human_object_reconciliation_mismatch",
                        "reiyah.fixture.bad.human_observation_availability_after_belief",
                        "reiyah.fixture.bad.human_observation_availability_before_measurement",
                        "reiyah.fixture.bad.human_observation_availability_nonobserved",
                        "reiyah.fixture.bad.human_observation_event_after_measurement",
                        "reiyah.fixture.bad.human_observation_event_nonobserved",
                        "reiyah.fixture.bad.human_temporal_reconciliation_mismatch",
                        "reiyah.fixture.bad.observation_validity_abstained_mismatch",
                        "reiyah.fixture.bad.observation_validity_missing_mismatch",
                        "reiyah.fixture.bad.observation_validity_out_of_distribution_mismatch",
                        "reiyah.fixture.bad.observation_validity_sensor_invalid_mismatch",
                        "reiyah.fixture.bad.observation_validity_state_mismatch",
                        "reiyah.fixture.bad.observation_validity_unmeasured_mismatch",
                    ),
                },
            ),
            "reiyah.evidence-selector.science.causal-preregistration": (
                {
                    "observation_id": "reiyah.selector-observation.science.causal-preregistration-known-good@1.2.0",
                    "fixture_ids": (
                        "reiyah.fixture.good.v12.study-design-preregistration",
                        "reiyah.fixture.good.v12.study-design-preregistration-not-identified",
                        "reiyah.fixture.good.v12.study-design-preregistration-unknown",
                    ),
                },
                {
                    "observation_id": "reiyah.selector-observation.science.causal-preregistration-known-bad@1.2.0",
                    "fixture_ids": (
                        "reiyah.fixture.bad.causal_analysis_unit_coordinated_drop",
                        "reiyah.fixture.bad.causal_analysis_unit_duplicate",
                        "reiyah.fixture.bad.causal_analysis_unit_ref_wrong_id",
                        "reiyah.fixture.bad.causal_analysis_unit_ref_wrong_kind",
                        "reiyah.fixture.bad.causal_analysis_unit_reordered",
                        "reiyah.fixture.bad.causal_analysis_unit_role_substitution",
                        "reiyah.fixture.bad.causal_backdoor_open",
                        "reiyah.fixture.bad.causal_collider_adjustment",
                        "reiyah.fixture.bad.causal_dag_cycle",
                        "reiyah.fixture.bad.causal_duplicate_treatment_role",
                        "reiyah.fixture.bad.causal_estimand_binding_mismatch",
                        "reiyah.fixture.bad.causal_identification_disposition_not_identified",
                        "reiyah.fixture.bad.causal_identification_disposition_unknown",
                        "reiyah.fixture.bad.causal_prohibited_adjustment",
                        "reiyah.fixture.bad.causal_query_outcome_role_mismatch",
                        "reiyah.fixture.bad.causal_query_treatment_role_mismatch",
                        "reiyah.fixture.bad.causal_selected_adjustment_set_mismatch",
                        "reiyah.fixture.bad.causal_split_late_freeze",
                        "reiyah.fixture.bad.causal_split_member_omission",
                        "reiyah.fixture.bad.causal_split_member_overlap",
                        "reiyah.fixture.bad.causal_split_member_reordered",
                        "reiyah.fixture.bad.causal_split_outcome_stratification",
                        "reiyah.fixture.bad.causal_split_reference_duplicate",
                        "reiyah.fixture.bad.causal_split_unit_role_substitution",
                        "reiyah.fixture.bad.causal_stratification_late_availability",
                        "reiyah.fixture.bad.causal_stratification_role_mismatch",
                        "reiyah.fixture.bad.causal_stratification_unobserved_node",
                        "reiyah.fixture.bad.causal_temporal_order",
                        "reiyah.fixture.bad.causal_treatment_endpoint_unobserved",
                        "reiyah.fixture.bad.causal_unmeasured_adjustment",
                        "reiyah.fixture.bad.estimand_binding_study_causal_mismatch",
                        "reiyah.fixture.bad.estimand_operand_causal_comparator",
                        "reiyah.fixture.bad.reference_document_local_unresolved",
                        "reiyah.fixture.bad.study_adjustment_set_late_freeze",
                        "reiyah.fixture.bad.study_design_freeze_after_feature_access",
                        "reiyah.fixture.bad.study_design_freeze_binding_mismatch",
                    ),
                },
            ),
            "reiyah.evidence-selector.science.readiness-recovery": (
                {
                    "observation_id": "reiyah.selector-observation.science.readiness-recovery-known-good@1.2.0",
                    "fixture_ids": (
                        "reiyah.fixture.good.v12.human-automation-assessment",
                        "reiyah.fixture.good.v12.human-automation-assessment-optional-unknown",
                        "reiyah.fixture.good.v12.human-automation-assessment-readiness-not-ready-weighted",
                        "reiyah.fixture.good.v12.human-automation-assessment-readiness-ready-boolean",
                        "reiyah.fixture.good.v12.human-automation-assessment-readiness-ready-weighted",
                        "reiyah.fixture.good.v12.human-automation-assessment-recovery-ambiguous-tie",
                        "reiyah.fixture.good.v12.human-automation-assessment-recovery-censoring",
                        "reiyah.fixture.good.v12.human-automation-assessment-recovery-competing",
                        "reiyah.fixture.good.v12.human-automation-assessment-recovery-incomplete-window",
                        "reiyah.fixture.good.v12.human-automation-assessment-recovery-input-nonobserved",
                        "reiyah.fixture.good.v12.human-automation-assessment-recovery-invalid-window",
                        "reiyah.fixture.good.v12.human-automation-assessment-recovery-no-event",
                    ),
                },
                {
                    "observation_id": "reiyah.selector-observation.science.readiness-recovery-known-bad@1.2.0",
                    "fixture_ids": (
                        "reiyah.fixture.bad.estimand_binding_human_readiness_mismatch",
                        "reiyah.fixture.bad.estimand_binding_human_recovery_mismatch",
                        "reiyah.fixture.bad.estimand_operand_readiness_criterion",
                        "reiyah.fixture.bad.estimand_operand_recovery_criterion",
                        "reiyah.fixture.bad.readiness_aggregation_mismatch",
                        "reiyah.fixture.bad.readiness_as_of_before_window",
                        "reiyah.fixture.bad.readiness_capability_dimension_duplicate",
                        "reiyah.fixture.bad.readiness_capability_manifest_coordinated_omission",
                        "reiyah.fixture.bad.readiness_capability_manifest_ref_substitution",
                        "reiyah.fixture.bad.readiness_criterion_mismatch",
                        "reiyah.fixture.bad.readiness_optional_unknown_imputed_zero",
                        "reiyah.fixture.bad.readiness_unknown_confident_aggregate",
                        "reiyah.fixture.bad.readiness_window_inverted",
                        "reiyah.fixture.bad.recovery_ambiguous_tie_reason_mismatch",
                        "reiyah.fixture.bad.recovery_censoring_disposition_mismatch",
                        "reiyah.fixture.bad.recovery_censoring_policy_substitution",
                        "reiyah.fixture.bad.recovery_competing_event_mismatch",
                        "reiyah.fixture.bad.recovery_competing_policy_substitution",
                        "reiyah.fixture.bad.recovery_duration_event_mismatch",
                        "reiyah.fixture.bad.recovery_elapsed_near_equality",
                        "reiyah.fixture.bad.recovery_elapsed_unit_mismatch",
                        "reiyah.fixture.bad.recovery_event_manifest_complete_through_mismatch",
                        "reiyah.fixture.bad.recovery_event_manifest_completeness_mismatch",
                        "reiyah.fixture.bad.recovery_event_manifest_coordinated_omission",
                        "reiyah.fixture.bad.recovery_event_manifest_ref_substitution",
                        "reiyah.fixture.bad.recovery_event_outside_window",
                        "reiyah.fixture.bad.recovery_event_type_role_mismatch",
                        "reiyah.fixture.bad.recovery_incomplete_window_confident_outcome",
                        "reiyah.fixture.bad.recovery_incomplete_window_reason_mismatch",
                        "reiyah.fixture.bad.recovery_input_nonobserved_reason_mismatch",
                        "reiyah.fixture.bad.recovery_invalid_window_reason_mismatch",
                        "reiyah.fixture.bad.recovery_late_event_selected",
                        "reiyah.fixture.bad.recovery_no_event_censoring_mismatch",
                        "reiyah.fixture.bad.recovery_no_event_reason_mismatch",
                        "reiyah.fixture.bad.recovery_nonobserved_event_time_confident_outcome",
                        "reiyah.fixture.bad.recovery_nonobserved_input_confident_outcome",
                    ),
                },
            ),
            "reiyah.evidence-selector.science.ope-closure": (
                {
                    "observation_id": "reiyah.selector-observation.science.ope-closure-known-good@1.2.0",
                    "fixture_ids": (
                        "reiyah.fixture.good.v12.sequential-off-policy-evaluation",
                        "reiyah.fixture.good.v12.sequential-off-policy-evaluation-all-zero",
                        "reiyah.fixture.good.v12.sequential-off-policy-evaluation-maximum-horizon",
                        "reiyah.fixture.good.v12.sequential-off-policy-evaluation-self-normalized",
                        "reiyah.fixture.good.v12.sequential-off-policy-evaluation-unsupported",
                        "reiyah.fixture.good.v12.sequential-off-policy-evaluation-upper-clip",
                    ),
                },
                {
                    "observation_id": "reiyah.selector-observation.science.ope-closure-known-bad@1.2.0",
                    "fixture_ids": (
                        "reiyah.fixture.bad.estimand_binding_ope_mismatch",
                        "reiyah.fixture.bad.estimand_operand_ope_policy_role",
                        "reiyah.fixture.bad.ope_action_distribution_mismatch",
                        "reiyah.fixture.bad.ope_contract_freeze_after_outcome",
                        "reiyah.fixture.bad.ope_cumulative_weight_mismatch",
                        "reiyah.fixture.bad.ope_duplicate_history_id",
                        "reiyah.fixture.bad.ope_duplicate_information_set_id",
                        "reiyah.fixture.bad.ope_duplicate_trajectory_id",
                        "reiyah.fixture.bad.ope_ess_all_zero_confident",
                        "reiyah.fixture.bad.ope_ess_cumulative_mismatch",
                        "reiyah.fixture.bad.ope_ess_horizon_missing",
                        "reiyah.fixture.bad.ope_estimator_selection_after_outcome",
                        "reiyah.fixture.bad.ope_estimator_weight_binding_mismatch",
                        "reiyah.fixture.bad.ope_final_terminal_false",
                        "reiyah.fixture.bad.ope_history_prefix_wrong_action",
                        "reiyah.fixture.bad.ope_history_support_failure",
                        "reiyah.fixture.bad.ope_information_set_after_outcome",
                        "reiyah.fixture.bad.ope_logged_propensity_mismatch",
                        "reiyah.fixture.bad.ope_maximum_horizon_exceeded",
                        "reiyah.fixture.bad.ope_observed_horizon_mismatch",
                        "reiyah.fixture.bad.ope_policy_table_coherent_probability_swap",
                        "reiyah.fixture.bad.ope_policy_table_role_substitution",
                        "reiyah.fixture.bad.ope_step_index_gap",
                        "reiyah.fixture.bad.ope_step_ratio_mismatch",
                        "reiyah.fixture.bad.ope_support_duplicate_required_cell",
                        "reiyah.fixture.bad.ope_terminal_before_final",
                        "reiyah.fixture.bad.ope_trajectory_manifest_coordinated_omission",
                        "reiyah.fixture.bad.ope_weight_normalization_mismatch",
                        "reiyah.fixture.bad.ope_weight_transformation_mismatch",
                    ),
                },
            ),
            "reiyah.evidence-selector.science.joint-silent-miss": (
                {
                    "observation_id": "reiyah.selector-observation.science.joint-silent-miss-known-good@1.2.0",
                    "fixture_ids": (
                        "reiyah.fixture.good.v12.joint-performance-evaluation",
                        "reiyah.fixture.good.v12.joint-performance-nonobserved",
                        "reiyah.fixture.good.v12.joint-performance-zero-opportunities",
                    ),
                },
                {
                    "observation_id": "reiyah.selector-observation.science.joint-silent-miss-known-bad@1.2.0",
                    "fixture_ids": (
                        "reiyah.fixture.bad.estimand_binding_joint_miss_mismatch",
                        "reiyah.fixture.bad.estimand_operand_joint_opportunity",
                        "reiyah.fixture.bad.joint_common_opportunity_derivation_mismatch",
                        "reiyah.fixture.bad.joint_nonobserved_operands_confident_summary",
                        "reiyah.fixture.bad.joint_opportunity_aggregate_coherent_swap",
                        "reiyah.fixture.bad.joint_opportunity_channel_role_swap",
                        "reiyah.fixture.bad.joint_opportunity_coordinated_member_omission",
                        "reiyah.fixture.bad.joint_opportunity_cross_object",
                        "reiyah.fixture.bad.joint_opportunity_duplicate_id",
                        "reiyah.fixture.bad.joint_opportunity_fallback_flip",
                        "reiyah.fixture.bad.joint_opportunity_member_order_swap",
                        "reiyah.fixture.bad.joint_opportunity_outside_window",
                        "reiyah.fixture.bad.joint_opportunity_set_ref_substitution",
                        "reiyah.fixture.bad.joint_opportunity_warning_flip",
                        "reiyah.fixture.bad.joint_opportunity_warning_nonobserved_confident_summary",
                        "reiyah.fixture.bad.joint_opportunity_window_mismatch",
                        "reiyah.fixture.bad.joint_silent_miss_derivation_mismatch",
                    ),
                },
            ),
            "reiyah.evidence-selector.science.ood-worst-group": (
                {
                    "observation_id": "reiyah.selector-observation.science.ood-worst-group-known-good@1.2.0",
                    "fixture_ids": (
                        "reiyah.fixture.good.v12.joint-performance-conformal-below-target",
                        "reiyah.fixture.good.v12.joint-performance-conformal-unknown",
                        "reiyah.fixture.good.v12.joint-performance-evaluation",
                        "reiyah.fixture.good.v12.joint-performance-nonobserved",
                        "reiyah.fixture.good.v12.joint-performance-ood-all-unknown",
                        "reiyah.fixture.good.v12.joint-performance-selective-zero-accepted",
                    ),
                },
                {
                    "observation_id": "reiyah.selector-observation.science.ood-worst-group-known-bad@1.2.0",
                    "fixture_ids": (
                        "reiyah.fixture.bad.conformal_aggregate_coverage_mismatch",
                        "reiyah.fixture.bad.conformal_calibration_test_collision",
                        "reiyah.fixture.bad.conformal_coordinated_group_drop",
                        "reiyah.fixture.bad.conformal_coverage_disposition_mismatch",
                        "reiyah.fixture.bad.conformal_disjoint_aggregate_mismatch",
                        "reiyah.fixture.bad.conformal_false_exchangeability_guarantee",
                        "reiyah.fixture.bad.conformal_group_count_mismatch",
                        "reiyah.fixture.bad.conformal_group_scope_mismatch",
                        "reiyah.fixture.bad.conformal_split_role_swap",
                        "reiyah.fixture.bad.conformal_target_mismatch",
                        "reiyah.fixture.bad.conformal_unknown_disposition_relabel",
                        "reiyah.fixture.bad.conformal_zero_denominator_confident",
                        "reiyah.fixture.bad.estimand_binding_conformal_mismatch",
                        "reiyah.fixture.bad.estimand_binding_ood_mismatch",
                        "reiyah.fixture.bad.estimand_binding_worst_group_mismatch",
                        "reiyah.fixture.bad.estimand_operand_conformal_method",
                        "reiyah.fixture.bad.estimand_operand_ood_rule_role",
                        "reiyah.fixture.bad.estimand_operand_worst_population",
                        "reiyah.fixture.bad.ood_confusion_partition_mismatch",
                        "reiyah.fixture.bad.ood_detected_count_mismatch",
                        "reiyah.fixture.bad.ood_rate_derivation_mismatch",
                        "reiyah.fixture.bad.ood_reference_unknown_count_mismatch",
                        "reiyah.fixture.bad.ood_selective_binding_mismatch",
                        "reiyah.fixture.bad.selective_partition_mismatch",
                        "reiyah.fixture.bad.selective_risk_derivation_mismatch",
                        "reiyah.fixture.bad.worst_group_coordinated_group_drop",
                        "reiyah.fixture.bad.worst_group_coverage_mismatch",
                        "reiyah.fixture.bad.worst_group_eligibility_mismatch",
                        "reiyah.fixture.bad.worst_group_insufficient_partition_omission",
                        "reiyah.fixture.bad.worst_group_minimum_information_bypass",
                        "reiyah.fixture.bad.worst_group_no_eligible_confident_value",
                        "reiyah.fixture.bad.worst_group_no_eligible_relabel_unknown",
                        "reiyah.fixture.bad.worst_group_nonobserved_ess_mislabeled_insufficient",
                        "reiyah.fixture.bad.worst_group_tie_mismatch",
                        "reiyah.fixture.bad.worst_group_unknown_observed_extremum",
                        "reiyah.fixture.bad.worst_group_unknown_partition_omission",
                        "reiyah.fixture.bad.worst_group_unknown_relabel_no_eligible",
                        "reiyah.fixture.known-bad.v12.worst-group-executable-threshold-binding",
                    ),
                },
            ),
            "reiyah.evidence-selector.science.transfer-conformal-assumption": (
                {
                    "observation_id": "reiyah.selector-observation.science.transfer-conformal-assumption-known-good@1.2.0",
                    "fixture_ids": (
                        "reiyah.fixture.good.v12.joint-performance-conformal-below-target",
                        "reiyah.fixture.good.v12.joint-performance-conformal-unknown",
                        "reiyah.fixture.good.v12.joint-performance-evaluation",
                        "reiyah.fixture.good.v12.joint-performance-nonobserved",
                    ),
                },
                {
                    "observation_id": "reiyah.selector-observation.science.transfer-conformal-assumption-known-bad@1.2.0",
                    "fixture_ids": (
                        "reiyah.fixture.bad.conformal_aggregate_coverage_mismatch",
                        "reiyah.fixture.bad.conformal_calibration_test_collision",
                        "reiyah.fixture.bad.conformal_coordinated_group_drop",
                        "reiyah.fixture.bad.conformal_coverage_disposition_mismatch",
                        "reiyah.fixture.bad.conformal_disjoint_aggregate_mismatch",
                        "reiyah.fixture.bad.conformal_established_empty_evidence",
                        "reiyah.fixture.bad.conformal_established_inline_evidence",
                        "reiyah.fixture.bad.conformal_established_self_evidence",
                        "reiyah.fixture.bad.conformal_false_exchangeability_guarantee",
                        "reiyah.fixture.bad.conformal_group_count_mismatch",
                        "reiyah.fixture.bad.conformal_group_scope_mismatch",
                        "reiyah.fixture.bad.conformal_split_role_swap",
                        "reiyah.fixture.bad.conformal_target_mismatch",
                        "reiyah.fixture.bad.conformal_unknown_disposition_relabel",
                        "reiyah.fixture.bad.conformal_zero_denominator_confident",
                        "reiyah.fixture.bad.estimand_binding_conformal_mismatch",
                        "reiyah.fixture.bad.estimand_binding_transfer_mismatch",
                        "reiyah.fixture.bad.estimand_operand_conformal_method",
                        "reiyah.fixture.bad.estimand_operand_transfer_unit",
                        "reiyah.fixture.bad.transfer_analysis_freeze_equality",
                        "reiyah.fixture.bad.transfer_coverage_mismatch",
                        "reiyah.fixture.bad.transfer_domain_role_swap",
                        "reiyah.fixture.bad.transfer_established_empty_evidence",
                        "reiyah.fixture.bad.transfer_gap_mismatch",
                        "reiyah.fixture.bad.transfer_invariance_state_mismatch",
                        "reiyah.fixture.bad.transfer_label_access_before_target",
                        "reiyah.fixture.bad.transfer_metric_contract_mismatch",
                        "reiyah.fixture.bad.transfer_metric_direction_mismatch",
                        "reiyah.fixture.bad.transfer_nonobserved_source_confident_gap",
                        "reiyah.fixture.bad.transfer_not_identified_relabel_unknown",
                        "reiyah.fixture.bad.transfer_overlap_failed_observed_gap",
                        "reiyah.fixture.bad.transfer_population_harmonization_state_mismatch",
                        "reiyah.fixture.bad.transfer_source_domain_equals_target",
                        "reiyah.fixture.bad.transfer_source_zero_observed_estimate",
                        "reiyah.fixture.bad.transfer_supervised_missing_label_time",
                        "reiyah.fixture.bad.transfer_target_access_before_freeze",
                        "reiyah.fixture.bad.transfer_target_zero_observed_estimate",
                        "reiyah.fixture.bad.transfer_undisclosed_target_tuning",
                        "reiyah.fixture.bad.transfer_unknown_relabel_not_identified",
                        "reiyah.fixture.bad.transfer_unsupervised_label_use",
                    ),
                },
            ),
        }
    )
)


def evidence_selector_observation_dispatch() -> Mapping[str, Mapping[str, Any]]:
    science_selector_ids = tuple(
        selector_id
        for selector_id in EVIDENCE_SELECTOR_PRODUCER_DISPATCH
        if selector_id.startswith("reiyah.evidence-selector.science.")
    )
    if set(SCIENCE_SELECTOR_REQUIRED_OBSERVATIONS) != set(science_selector_ids):
        raise GateError(
            "GA12-PLAN-EVIDENCE-SELECTOR-DISPATCH",
            "the eight code-side science selector observations are not frozen",
        )
    publication_positive_ids = (
        *GOVERNANCE_POSITIVE_PATH_TO_ID.values(),
        "reiyah.fixture.governance.publication-event-synthetic-baseline@1.2.0",
    )
    transport_positive_ids = (
        "reiyah.fixture.governance.transport-observation-synthetic-baseline@1.2.0",
    )
    execution_fixture_ids = (
        "reiyah.fixture.validator-security.actual-publication-event-fault-matrix@1.2.0",
        "reiyah.fixture.validator-security.development-drift@1.2.0",
        "reiyah.fixture.validator-security.missing-isolation@1.2.0",
        "reiyah.fixture.validator-security.plan-tool-binding-launcher@1.2.0",
        "reiyah.fixture.validator-security.plan-tool-binding-primary-validator@1.2.0",
        "reiyah.fixture.validator-security.plan-tool-binding-science-module@1.2.0",
        "reiyah.fixture.validator-security.plan-tool-binding-toolchain-lock@1.2.0",
        "reiyah.fixture.validator-security.profile-execution-binding@1.2.0",
        "reiyah.fixture.validator-security.profile-execution-launcher-binding@1.2.0",
        "reiyah.fixture.validator-security.profile-execution-tool-binding@1.2.0",
        "reiyah.fixture.validator-security.profile-execution-toolchain-lock-binding@1.2.0",
        "reiyah.fixture.validator-security.release-dirty-state@1.2.0",
        "reiyah.fixture.validator-security.release-index-flag@1.2.0",
        "reiyah.fixture.validator-security.release-worker-fault-matrix@1.2.0",
        "reiyah.fixture.validator-security.self-membership-byte-mismatch@1.2.0",
        "reiyah.fixture.validator-security.toolchain-byte-mismatch@1.2.0",
    )
    catalog_fixture_ids = (
        "reiyah.fixture.validator-security.catalog-byte-digest@1.2.0",
        "reiyah.fixture.validator-security.catalog-byte-size@1.2.0",
        "reiyah.fixture.validator-security.catalog-duplicate-id@1.2.0",
        "reiyah.fixture.validator-security.catalog-duplicate-path@1.2.0",
        "reiyah.fixture.validator-security.catalog-expected-primary-rule@1.2.0",
        "reiyah.fixture.validator-security.catalog-fixture-schema@1.2.0",
        "reiyah.fixture.validator-security.catalog-identity-source@1.2.0",
        "reiyah.fixture.validator-security.catalog-missing-row@1.2.0",
        "reiyah.fixture.validator-security.catalog-replay-mode@1.2.0",
        "reiyah.fixture.validator-security.catalog-target-schema@1.2.0",
        "reiyah.fixture.validator-security.catalog-unexpected-row@1.2.0",
    )
    report_implication_fixture_ids = (
        "reiyah.fixture.validator-security.report-good-count-mismatch@1.2.0",
        "reiyah.fixture.validator-security.report-governance-count-mismatch@1.2.0",
        "reiyah.fixture.validator-security.report-science-bad-count-mismatch@1.2.0",
        "reiyah.fixture.validator-security.report-security-count-mismatch@1.2.0",
        "reiyah.fixture.validator-security.selector-fixture-set-digest-mismatch@1.2.0",
        "reiyah.fixture.validator-security.selector-missing-fixture@1.2.0",
        "reiyah.fixture.validator-security.selector-missing-observation@1.2.0",
        "reiyah.fixture.validator-security.selector-producer-substitution@1.2.0",
        "reiyah.fixture.validator-security.selector-unexpected-fixture@1.2.0",
    )
    static_rows: dict[str, tuple[Mapping[str, Any], ...]] = {
        "reiyah.evidence-selector.governance.publication-static-interface": (
            {
                "observation_id": "reiyah.selector-observation.governance.publication-positive@1.2.0",
                "fixture_ids": publication_positive_ids,
            },
            {
                "observation_id": "reiyah.selector-observation.governance.publication-known-bad@1.2.0",
                "fixture_ids": tuple(REQUIRED_PUBLICATION_GOVERNANCE_FIXTURES),
            },
        ),
        "reiyah.evidence-selector.governance.transport-static-interface": (
            {
                "observation_id": "reiyah.selector-observation.governance.transport-positive@1.2.0",
                "fixture_ids": transport_positive_ids,
            },
            {
                "observation_id": "reiyah.selector-observation.governance.transport-known-bad@1.2.0",
                "fixture_ids": tuple(REQUIRED_TRANSPORT_GOVERNANCE_FIXTURES),
            },
        ),
        "reiyah.evidence-selector.security.execution-integrity": (
            {
                "observation_id": "reiyah.selector-observation.security.execution-integrity@1.2.0",
                "fixture_ids": execution_fixture_ids,
            },
        ),
        "reiyah.evidence-selector.security.fixture-catalog-integrity": (
            {
                "observation_id": "reiyah.selector-observation.security.fixture-catalog-integrity@1.2.0",
                "fixture_ids": catalog_fixture_ids,
            },
        ),
        "reiyah.evidence-selector.security.narrative-nonclaim": (
            {
                "observation_id": "reiyah.selector-observation.security.narrative-nonclaim@1.2.0",
                "fixture_ids": (
                    "reiyah.fixture.validator-security.narrative-state-contradiction@1.2.0",
                    "reiyah.fixture.validator-security.normative-surface-path-substitution@1.2.0",
                ),
            },
        ),
        "reiyah.evidence-selector.security.reference-path-coverage": (
            {
                "observation_id": "reiyah.selector-observation.security.reference-path-coverage@1.2.0",
                "fixture_ids": (
                    "reiyah.fixture.validator-security.reference-path-missing@1.2.0",
                    "reiyah.fixture.validator-security.reference-path-duplicate@1.2.0",
                    "reiyah.fixture.validator-security.reference-path-handler-only@1.2.0",
                ),
            },
            {
                "observation_id": "reiyah.selector-observation.security.registry-uniqueness@1.2.0",
                "fixture_ids": (
                    "reiyah.fixture.validator-security.registry-definition-id-duplicate@1.2.0",
                    "reiyah.fixture.validator-security.registry-reference-kind-id-duplicate@1.2.0",
                    "reiyah.fixture.validator-security.registry-executable-contract-id-duplicate@1.2.0",
                ),
            },
        ),
        "reiyah.evidence-selector.security.report-implications": (
            {
                "observation_id": "reiyah.selector-observation.security.report-implications@1.2.0",
                "fixture_ids": report_implication_fixture_ids,
            },
        ),
        "reiyah.evidence-selector.security.science-lineage": (
            {
                "observation_id": "reiyah.selector-observation.security.science-lineage@1.2.0",
                "fixture_ids": (
                    "reiyah.fixture.validator-security.science-artifact-id-duplicate@1.2.0",
                    "reiyah.fixture.validator-security.science-logical-version-duplicate@1.2.0",
                    "reiyah.fixture.validator-security.science-lineage-fork@1.2.0",
                ),
            },
        ),
        "reiyah.evidence-selector.security.successor-chronology": (
            {
                "observation_id": "reiyah.selector-observation.security.successor-chronology@1.2.0",
                "fixture_ids": (
                    "reiyah.fixture.validator-security.research-registry-earlier-date@1.2.0",
                ),
            },
        ),
        "reiyah.evidence-selector.security.transport-self-attestation": (
            {
                "observation_id": "reiyah.selector-observation.security.transport-self-attestation@1.2.0",
                "fixture_ids": (
                    "reiyah.fixture.validator-security.transport-self-attestation@1.2.0",
                ),
            },
        ),
    }
    combined: dict[str, Mapping[str, Any]] = {}
    for selector_id, producer_check_id in EVIDENCE_SELECTOR_PRODUCER_DISPATCH.items():
        observations = (
            SCIENCE_SELECTOR_REQUIRED_OBSERVATIONS.get(selector_id)
            if selector_id in science_selector_ids
            else static_rows.get(selector_id)
        )
        if not observations:
            raise GateError(
                "GA12-PLAN-EVIDENCE-SELECTOR-DISPATCH",
                f"selector observations are absent: {selector_id}",
            )
        combined[selector_id] = {
            "producer_check_id": producer_check_id,
            "required_observations": tuple(observations),
        }
    return MappingProxyType(combined)


def check_format_canaries() -> dict[str, int]:
    cases: dict[str, tuple[tuple[object, ...], tuple[object, ...]]] = {
        "date": (
            ("2026-08-24", "2000-02-29"),
            ("2026-02-29", "2026-13-01", "2026-8-24", "not-a-date"),
        ),
        "date-time": (
            (
                "2026-08-24T00:00:00Z",
                "2026-08-24T00:00:00.123456+03:00",
                "1990-12-31T23:59:60Z",
            ),
            (
                "2026-02-30T12:00:00Z",
                "2026-08-24T24:00:00Z",
                "2026-08-24T00:00:00",
                "2026-08-24 00:00:00Z",
                "2026-08-31T23:59:60Z",
                "1900-06-30T23:59:60Z",
            ),
        ),
        "uri": (
            (
                "https://schemas.reiyah.invalid/x",
                "http://[v1.a]/",
                "urn:reiyah:test:1",
            ),
            (
                "not a uri",
                "https://",
                "https://example.invalid/%ZZ",
                "https://example.invalid/{bad}",
                "https://example.invalid/[bad]",
                "urn:x|y",
                "/relative",
            ),
        ),
        "https-uri": (
            ("https://github.com/manfromnowhere143/reiyah",),
            ("http://example.invalid", "https://", "urn:reiyah:test"),
        ),
    }
    valid_count = 0
    invalid_count = 0
    for name, (valid, invalid) in sorted(cases.items()):
        checker = FORMAT_CHECKERS[name]
        for value in valid:
            if not checker(value):
                raise GateError(
                    "GA12-FORMAT-CANARY", f"{name} rejected valid canary {value!r}"
                )
            valid_count += 1
        for value in invalid:
            if checker(value):
                raise GateError(
                    "GA12-FORMAT-CANARY", f"{name} accepted invalid canary {value!r}"
                )
            invalid_count += 1
    return {"valid_canaries": valid_count, "invalid_canaries": invalid_count}


def schema_format_coverage(snapshot: RepositorySnapshot) -> dict[str, Any]:
    declarations: dict[str, int] = {}
    schema_count = 0

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            format_name = value.get("format")
            if format_name is not None:
                if not isinstance(format_name, str):
                    raise GateError(
                        "GA12-FORMAT-DECLARATION", "schema format must be a string"
                    )
                declarations[format_name] = declarations.get(format_name, 0) + 1
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    for path, item in sorted(snapshot.files.items()):
        if path.startswith("schemas/") and path.endswith(".schema.json"):
            schema_count += 1
            visit(strict_json(item.data, path))
    unknown = sorted(set(declarations) - set(FORMAT_CHECKERS))
    if unknown:
        raise GateError(
            "GA12-FORMAT-CHECKER-UNKNOWN",
            f"schemas declare unregistered formats: {', '.join(unknown)}",
        )
    return {
        "schema_count": schema_count,
        "declarations": dict(sorted(declarations.items())),
        "registered_checkers": sorted(FORMAT_CHECKERS),
    }


def validate_schema_corpus(
    snapshot: RepositorySnapshot,
    dependencies: Mapping[str, Any],
    instance_paths: set[str],
) -> dict[str, Any]:
    schema_paths = sorted(
        path
        for path in snapshot.files
        if path.startswith("schemas/") and path.endswith(".schema.json")
    )
    schemas: dict[str, Any] = {}
    path_by_id: dict[str, str] = {}
    for path in schema_paths:
        schema = strict_json(snapshot.read(path), path)
        if not isinstance(schema, dict) or not isinstance(schema.get("$id"), str):
            raise GateError("GA12-SCHEMA-CORPUS", f"schema lacks object/$id: {path}")
        schema_id = schema["$id"]
        if schema_id in schemas:
            raise GateError(
                "GA12-SCHEMA-CORPUS",
                f"duplicate schema ID at {path_by_id[schema_id]} and {path}",
            )
        schemas[schema_id] = schema
        path_by_id[schema_id] = path
    Draft202012Validator = dependencies["Draft202012Validator"]
    Resource = dependencies["Resource"]
    Registry = dependencies["Registry"]
    try:
        for schema_id, schema in sorted(schemas.items()):
            Draft202012Validator.check_schema(schema)
        registry = Registry().with_resources(
            (schema_id, Resource.from_contents(schema))
            for schema_id, schema in sorted(schemas.items())
        )
    except Exception as exc:
        raise GateError(
            "GA12-SCHEMA-CORPUS-METAVALIDATION", f"schema corpus is invalid: {exc}"
        ) from exc
    checker = local_format_checker(dependencies)
    validators = {
        schema_id: Draft202012Validator(
            schema, registry=registry, format_checker=checker
        )
        for schema_id, schema in schemas.items()
    }
    json_artifact_count = 0
    normative_instance_count = 0
    for path in sorted(item for item in instance_paths if item.endswith(".json")):
        value = strict_json(snapshot.read(path), path)
        json_artifact_count += 1
        if not isinstance(value, dict) or not isinstance(value.get("schema_id"), str):
            continue
        schema_id = value["schema_id"]
        if schema_id not in validators:
            raise GateError(
                "GA12-SCHEMA-CORPUS-RESOLUTION",
                f"instance schema_id is unresolved: {path}: {schema_id}",
            )
        errors = schema_error_records(validators[schema_id], value)
        if errors:
            first = errors[0]
            raise GateError(
                "GA12-SCHEMA-CORPUS-INSTANCE",
                f"{path} failed {first['schema_keyword']} at {first['instance_pointer']}: {first['message']}",
            )
        normative_instance_count += 1
    return {
        "schema_count": len(schema_paths),
        "json_artifact_count": json_artifact_count,
        "normative_instance_count": normative_instance_count,
    }


def canonical_record_digest(records: list[dict[str, Any]]) -> str:
    encoded = json.dumps(
        records, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def regular_file_record(path: Path, logical_path: str) -> dict[str, Any]:
    data = stable_regular_bytes(path)
    return {
        "path": logical_path,
        "sha256": hashlib.sha256(data).hexdigest(),
        "size": len(data),
    }


def distribution_observation(specification: Mapping[str, Any]) -> dict[str, Any]:
    required = {"name", "version", "site_packages", "dist_info", "import_roots"}
    if not required.issubset(specification):
        missing = sorted(required - set(specification))
        raise GateError(
            "GA12-TOOLCHAIN-LOCK-SHAPE", f"dependency missing fields: {missing}"
        )
    site_packages = Path(specification["site_packages"])
    dist_info = site_packages / specification["dist_info"]
    record_path = dist_info / "RECORD"
    metadata_path = dist_info / "METADATA"
    if (
        not site_packages.is_absolute()
        or not site_packages.is_dir()
        or site_packages.is_symlink()
        or not dist_info.is_dir()
        or dist_info.is_symlink()
    ):
        raise GateError(
            "GA12-TOOLCHAIN-PATH",
            f"invalid distribution path for {specification['name']}",
        )
    try:
        metadata_text = stable_regular_bytes(metadata_path).decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise GateError(
            "GA12-TOOLCHAIN-METADATA", f"invalid METADATA for {specification['name']}"
        ) from exc
    observed_version = next(
        (
            line.removeprefix("Version: ")
            for line in metadata_text.splitlines()
            if line.startswith("Version: ")
        ),
        None,
    )
    record_bytes = stable_regular_bytes(record_path)
    record_rows: list[dict[str, Any]] = []
    try:
        parsed_rows = list(
            csv.reader(io.StringIO(record_bytes.decode("utf-8", "strict")))
        )
    except (UnicodeDecodeError, csv.Error) as exc:
        raise GateError(
            "GA12-TOOLCHAIN-RECORD",
            f"invalid RECORD for {specification['name']}: {exc}",
        ) from exc
    for row in parsed_rows:
        if len(row) != 3:
            raise GateError(
                "GA12-TOOLCHAIN-RECORD",
                f"invalid RECORD row for {specification['name']}",
            )
        logical = row[0]
        unresolved_candidate = site_packages / logical
        candidate = unresolved_candidate.resolve()
        # Distribution scripts may legitimately be relative paths into the same
        # Homebrew prefix.  Escapes outside /opt/homebrew are never accepted.
        if not str(candidate).startswith("/opt/homebrew/"):
            raise GateError(
                "GA12-TOOLCHAIN-RECORD-PATH",
                f"RECORD path escapes trusted prefix: {logical}",
            )
        if unresolved_candidate.is_symlink():
            raise GateError(
                "GA12-TOOLCHAIN-SYMLINK", f"RECORD symlink rejected: {logical}"
            )
        record_rows.append(regular_file_record(unresolved_candidate, logical))
    record_rows.sort(key=lambda item: item["path"])

    root_rows: list[dict[str, Any]] = []
    for root_name in sorted(specification["import_roots"]):
        if (
            not isinstance(root_name, str)
            or "/" in root_name
            or root_name in {"", ".", ".."}
        ):
            raise GateError(
                "GA12-TOOLCHAIN-IMPORT-ROOT", f"unsafe import root: {root_name!r}"
            )
        root = site_packages / root_name
        if root.is_symlink():
            raise GateError(
                "GA12-TOOLCHAIN-IMPORT-ROOT", f"invalid import root: {root}"
            )
        if root.is_file():
            root_rows.append(regular_file_record(root, root_name))
            continue
        if not root.is_dir():
            raise GateError(
                "GA12-TOOLCHAIN-IMPORT-ROOT", f"invalid import root: {root}"
            )
        for directory, directory_names, filenames in os.walk(root, followlinks=False):
            directory_names.sort()
            filenames.sort()
            for directory_name in directory_names:
                if (Path(directory) / directory_name).is_symlink():
                    raise GateError(
                        "GA12-TOOLCHAIN-SYMLINK",
                        f"dependency directory symlink rejected: {Path(directory) / directory_name}",
                    )
            for filename in filenames:
                item_path = Path(directory) / filename
                logical = item_path.relative_to(site_packages).as_posix()
                root_rows.append(regular_file_record(item_path, logical))
    root_rows.sort(key=lambda item: item["path"])
    return {
        "name": specification["name"],
        "version": observed_version,
        "record_sha256": hashlib.sha256(record_bytes).hexdigest(),
        "recorded_file_count": len(record_rows),
        "recorded_files_sha256": canonical_record_digest(record_rows),
        "import_root_file_count": len(root_rows),
        "import_roots_sha256": canonical_record_digest(root_rows),
    }


def system_version() -> dict[str, str]:
    system_plist = Path("/System/Library/CoreServices/SystemVersion.plist")
    try:
        data = plistlib.loads(stable_regular_bytes(system_plist))
    except (OSError, plistlib.InvalidFileException) as exc:
        raise GateError(
            "GA12-PLATFORM-READ", f"cannot read macOS version: {exc}"
        ) from exc
    uname = os.uname()
    return {
        "system": uname.sysname,
        "machine": uname.machine,
        "kernel_release": uname.release,
        "kernel_version": uname.version,
        "product_version": str(data.get("ProductVersion", "")),
        "product_build_version": str(data.get("ProductBuildVersion", "")),
        "python_implementation": sys.implementation.name,
        "python_version": sys.version.split()[0],
    }


def executable_observation(path: Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    return {
        "path": str(path),
        "resolved_path": str(resolved),
        "sha256": sha256_file(path, permit_symlink=(path == PYTHON_PATH)),
        "size": resolved.stat().st_size,
    }


def python_runtime_template() -> dict[str, Any]:
    return {
        "stdlib_root": str(PYTHON_RUNTIME_ROOT),
        "excluded_subtrees": list(PYTHON_RUNTIME_EXCLUSIONS),
        "framework_path": str(PYTHON_FRAMEWORK_PATH),
    }


def python_runtime_observation(specification: Mapping[str, Any]) -> dict[str, Any]:
    if specification != {
        **python_runtime_template(),
        **{
            key: specification[key]
            for key in (
                "stdlib_file_count",
                "stdlib_tree_sha256",
                "framework_size",
                "framework_sha256",
            )
            if key in specification
        },
    }:
        raise GateError(
            "GA12-TOOLCHAIN-LOCK-BINDING", "Python runtime coordinates are unauthorized"
        )
    root = Path(specification["stdlib_root"])
    if not root.is_dir() or root.is_symlink():
        raise GateError("GA12-TOOLCHAIN-PATH", f"invalid Python stdlib root: {root}")
    exclusions = set(specification["excluded_subtrees"])
    rows: list[dict[str, Any]] = []
    for directory, directory_names, filenames in os.walk(root, followlinks=False):
        relative_directory = Path(directory).relative_to(root)
        if relative_directory == Path("."):
            directory_names[:] = sorted(
                name for name in directory_names if name not in exclusions
            )
        else:
            directory_names.sort()
        filenames.sort()
        for directory_name in directory_names:
            if (Path(directory) / directory_name).is_symlink():
                raise GateError(
                    "GA12-TOOLCHAIN-SYMLINK",
                    f"Python runtime directory symlink rejected: {Path(directory) / directory_name}",
                )
        for filename in filenames:
            item_path = Path(directory) / filename
            logical = item_path.relative_to(root).as_posix()
            rows.append(regular_file_record(item_path, logical))
    rows.sort(key=lambda item: item["path"])
    framework = stable_regular_bytes(Path(specification["framework_path"]))
    return {
        "stdlib_file_count": len(rows),
        "stdlib_tree_sha256": canonical_record_digest(rows),
        "framework_size": len(framework),
        "framework_sha256": hashlib.sha256(framework).hexdigest(),
    }


def observed_toolchain(dependency_specs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    runtime_specification = python_runtime_template()
    return {
        "platform": system_version(),
        "execution_profile": {
            "required_python_flags": ["-I", "-S", "-B"],
            "seatbelt_application": "external_launcher_with_early_libsandbox_policy_checks",
            "seatbelt_profile_sha256": SEATBELT_PROFILE_SHA256,
            "network_policy": "denied_by_locked_macos_seatbelt_profile",
            "filesystem_write_policy": "denied_except_write_data_to_dev_null",
        },
        "executables": {
            "env": executable_observation(ENV_PATH),
            "git": executable_observation(GIT_PATH),
            "python": executable_observation(PYTHON_PATH),
            "sandbox_exec": executable_observation(SANDBOX_EXEC_PATH),
            "shell": executable_observation(SHELL_PATH),
        },
        "python_runtime": {
            **runtime_specification,
            **python_runtime_observation(runtime_specification),
        },
        "dependencies": [distribution_observation(spec) for spec in dependency_specs],
    }


def require_exact_keys(
    value: Mapping[str, Any], expected: set[str], context: str
) -> None:
    if set(value) != expected:
        raise GateError(
            "GA12-TOOLCHAIN-LOCK-SHAPE",
            f"{context} keys differ; missing={sorted(expected - set(value))}, extra={sorted(set(value) - expected)}",
        )


def require_toolchain_match(locked: object, observed: object, context: str) -> None:
    if locked != observed:
        raise GateError(
            "GA12-TOOLCHAIN-BYTE-MISMATCH", f"locked {context} differs from observation"
        )


def validate_toolchain_lock(snapshot: RepositorySnapshot) -> dict[str, Any]:
    value = strict_json(snapshot.read(LOCK_PATH), LOCK_PATH)
    if not isinstance(value, dict):
        raise GateError("GA12-TOOLCHAIN-LOCK-SHAPE", "toolchain lock must be an object")
    required = {
        "artifact_id",
        "artifact_version",
        "lifecycle_status",
        "mission_release_id",
        "protocol_release_id",
        "platform",
        "python_runtime",
        "execution_profile",
        "executables",
        "dependencies",
        "guarantee_boundaries",
    }
    require_exact_keys(value, required, "toolchain lock")
    expected_scalars = {
        "artifact_id": "reiyah.validation-toolchain-lock@1.2.0",
        "artifact_version": ARTIFACT_VERSION,
        "lifecycle_status": "proposed",
        "mission_release_id": MISSION_RELEASE_ID,
        "protocol_release_id": PROTOCOL_RELEASE_ID,
    }
    for key, expected in expected_scalars.items():
        if value.get(key) != expected:
            raise GateError(
                "GA12-TOOLCHAIN-LOCK-BINDING", f"{key} must equal {expected!r}"
            )
    dependencies = value.get("dependencies")
    if not isinstance(dependencies, list) or not dependencies:
        raise GateError(
            "GA12-TOOLCHAIN-LOCK-SHAPE", "dependencies must be a non-empty list"
        )
    expected_observations: list[dict[str, Any]] = []
    names: set[str] = set()
    templates = dependency_templates()
    if len(dependencies) != len(templates):
        raise GateError(
            "GA12-TOOLCHAIN-LOCK-BINDING",
            f"expected {len(templates)} dependency entries, observed {len(dependencies)}",
        )
    for dependency, template in zip(dependencies, templates, strict=True):
        if not isinstance(dependency, dict):
            raise GateError(
                "GA12-TOOLCHAIN-LOCK-SHAPE", "dependency lock must be an object"
            )
        expected_fields = {
            "name",
            "version",
            "site_packages",
            "dist_info",
            "import_roots",
            "record_sha256",
            "recorded_file_count",
            "recorded_files_sha256",
            "import_root_file_count",
            "import_roots_sha256",
        }
        require_exact_keys(
            dependency, expected_fields, f"dependency {dependency.get('name')!r}"
        )
        name = dependency["name"]
        if not isinstance(name, str) or name in names:
            raise GateError(
                "GA12-TOOLCHAIN-LOCK-SHAPE",
                f"invalid/duplicate dependency name: {name!r}",
            )
        names.add(name)
        for coordinate in (
            "name",
            "version",
            "site_packages",
            "dist_info",
            "import_roots",
        ):
            if dependency[coordinate] != template[coordinate]:
                raise GateError(
                    "GA12-TOOLCHAIN-LOCK-BINDING",
                    f"dependency {name!r} has an unauthorized {coordinate}",
                )
        for digest_name in (
            "record_sha256",
            "recorded_files_sha256",
            "import_roots_sha256",
        ):
            digest_value = dependency[digest_name]
            if (
                not isinstance(digest_value, str)
                or re.fullmatch(r"[0-9a-f]{64}", digest_value) is None
            ):
                raise GateError(
                    "GA12-TOOLCHAIN-LOCK-SHAPE",
                    f"dependency {name!r} has an invalid {digest_name}",
                )
        for count_name in ("recorded_file_count", "import_root_file_count"):
            count_value = dependency[count_name]
            if (
                not isinstance(count_value, int)
                or isinstance(count_value, bool)
                or count_value < 1
            ):
                raise GateError(
                    "GA12-TOOLCHAIN-LOCK-SHAPE",
                    f"dependency {name!r} has an invalid {count_name}",
                )
        expected_observations.append(
            {
                key: dependency[key]
                for key in dependency
                if key not in {"site_packages", "dist_info", "import_roots"}
            }
        )
    boundaries = value["guarantee_boundaries"]
    if not isinstance(boundaries, dict):
        raise GateError(
            "GA12-TOOLCHAIN-LOCK-SHAPE", "guarantee_boundaries must be an object"
        )
    require_exact_keys(
        boundaries,
        {"covered", "conditional", "externally_verified"},
        "guarantee_boundaries",
    )
    if not all(isinstance(item, str) and item for item in boundaries.values()):
        raise GateError(
            "GA12-TOOLCHAIN-LOCK-SHAPE",
            "guarantee boundaries must be non-empty strings",
        )
    if boundaries != GUARANTEE_BOUNDARIES:
        raise GateError(
            "GA12-TOOLCHAIN-LOCK-BINDING",
            "guarantee_boundaries differ from the validator's exact claim boundary",
        )

    observed = observed_toolchain(dependencies)
    repeated_observation = observed_toolchain(dependencies)
    if repeated_observation != observed:
        raise GateError(
            "GA12-TOOLCHAIN-DRIFT",
            "platform, executable, or dependency bytes changed between complete observations",
        )
    for key in ("platform", "python_runtime", "execution_profile", "executables"):
        require_toolchain_match(value[key], observed[key], key)
    require_toolchain_match(
        expected_observations,
        observed["dependencies"],
        "dependency version, RECORD, recorded-file, or import-root bytes",
    )
    return {
        "dependency_count": len(dependencies),
        "dependency_names": sorted(names),
        "seatbelt_profile_sha256": SEATBELT_PROFILE_SHA256,
    }


def activate_locked_schema_dependencies() -> dict[str, Any]:
    site_packages = "/opt/homebrew/lib/python3.14/site-packages"
    if site_packages in sys.path:
        raise GateError(
            "GA12-DEPENDENCY-ACTIVATION-ORDER",
            "site-packages was active before the byte-level toolchain lock passed",
        )
    optional_format_dependencies = (
        "fqdn",
        "idna",
        "isoduration",
        "jsonpointer",
        "rfc3339_validator",
        "rfc3986_validator",
        "rfc3987",
        "uri_template",
        "webcolors",
    )
    for name in optional_format_dependencies:
        if name in sys.modules:
            raise GateError(
                "GA12-DEPENDENCY-ACTIVATION-ORDER",
                f"optional format dependency was imported before activation: {name}",
            )
        sys.modules[name] = None
    sys.path.append(site_packages)
    try:
        from jsonschema import Draft202012Validator, FormatChecker
        from referencing import Registry, Resource
    except ImportError as exc:
        raise GateError(
            "GA12-DEPENDENCY-IMPORT", f"locked schema dependency import failed: {exc}"
        ) from exc
    allowed_roots = {
        "attr",
        "attrs",
        "jsonschema",
        "jsonschema_specifications",
        "referencing",
        "rpds",
        "typing_extensions.py",
    }
    unexpected: set[str] = set()
    for module in tuple(sys.modules.values()):
        module_path = getattr(module, "__file__", None)
        if not isinstance(module_path, str) or not module_path.startswith(
            site_packages + "/"
        ):
            continue
        relative = module_path[len(site_packages) + 1 :]
        root_name = relative.split("/", 1)[0]
        if root_name not in allowed_roots:
            unexpected.add(root_name)
    if unexpected:
        raise GateError(
            "GA12-DEPENDENCY-IMPORT-SURFACE",
            f"unlocked site-packages modules were imported: {', '.join(sorted(unexpected))}",
        )
    return {
        "Draft202012Validator": Draft202012Validator,
        "FormatChecker": FormatChecker,
        "Registry": Registry,
        "Resource": Resource,
    }


def load_science_module(snapshot: RepositorySnapshot) -> Mapping[str, Any]:
    source = snapshot.read(SCIENCE_MODULE_PATH)
    try:
        code = compile(
            source, SCIENCE_MODULE_PATH, "exec", dont_inherit=True, optimize=0
        )
        namespace: dict[str, Any] = {
            "__builtins__": __builtins__,
            "__file__": SCIENCE_MODULE_PATH,
            "__name__": "reiyah_gate_a_1_2_0_science",
        }
        exec(code, namespace, namespace)
    except Exception as exc:
        raise GateError(
            "GA12-SCIENCE-MODULE-LOAD",
            f"cannot load snapshot science predicates: {exc}",
        ) from exc
    for name in (
        "SUPPORTED_RULE_IDS",
        "REFERENCE_PATH_HANDLER_CONTRACT",
        "ScienceContractError",
        "apply_mutations",
        "semantic_violations",
    ):
        if name not in namespace:
            raise GateError("GA12-SCIENCE-MODULE-API", f"science module lacks {name}")
    return MappingProxyType(namespace)


def schema_error_records(validator: Any, instance: Any) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for error in sorted(
        validator.iter_errors(instance),
        key=lambda item: (
            tuple(str(part) for part in item.absolute_path),
            tuple(str(part) for part in item.absolute_schema_path),
            item.message,
        ),
    ):
        pointer = "".join(
            "/" + str(part).replace("~", "~0").replace("/", "~1")
            for part in error.absolute_path
        )
        output.append(
            {
                "instance_pointer": pointer,
                "schema_keyword": str(error.validator),
                "message": error.message,
            }
        )
    return output


def local_format_checker(dependencies: Mapping[str, Any]) -> Any:
    checker = dependencies["FormatChecker"](formats=[])
    for format_name, predicate in sorted(FORMAT_CHECKERS.items()):
        checker.checks(format_name)(predicate)
    return checker


def validator_for_schema(
    snapshot: RepositorySnapshot,
    dependencies: Mapping[str, Any],
    schema_path: str,
    resource_paths: Sequence[str],
) -> Any:
    resources: dict[str, Any] = {}
    root_schema: Any = None
    for path in sorted(set(resource_paths) | {schema_path}):
        value = strict_json(snapshot.read(path), path)
        if not isinstance(value, dict) or not isinstance(value.get("$id"), str):
            raise GateError(
                "GA12-SCHEMA-RESOURCE", f"schema resource lacks object/$id: {path}"
            )
        if value["$id"] in resources:
            raise GateError(
                "GA12-SCHEMA-RESOURCE", f"duplicate schema resource ID: {value['$id']}"
            )
        resources[value["$id"]] = value
        if path == schema_path:
            root_schema = value
    Draft202012Validator = dependencies["Draft202012Validator"]
    try:
        Draft202012Validator.check_schema(root_schema)
        registry = dependencies["Registry"]().with_resources(
            (schema_id, dependencies["Resource"].from_contents(schema))
            for schema_id, schema in sorted(resources.items())
        )
        return Draft202012Validator(
            root_schema,
            registry=registry,
            format_checker=local_format_checker(dependencies),
        )
    except Exception as exc:
        raise GateError(
            "GA12-SCHEMA-METAVALIDATION",
            f"cannot construct validator for {schema_path}: {exc}",
        ) from exc


def validate_bound_bytes(
    snapshot: RepositorySnapshot,
    binding: Mapping[str, Any],
    diagnostic: str,
) -> dict[str, Any]:
    path = binding.get("path")
    if not isinstance(path, str):
        raise GateError(diagnostic, "artifact binding lacks a path")
    item = snapshot.files.get(path)
    if item is None:
        raise GateError(diagnostic, f"bound artifact is absent: {path}")
    expected_digest = f"sha256:{item.sha256}"
    if (
        binding.get("sha256") != expected_digest
        or binding.get("byte_size") != item.size
    ):
        raise GateError(diagnostic, f"artifact bytes differ from binding: {path}")
    return {"path": path, "sha256": expected_digest, "byte_size": item.size}


def validate_plan_evidence_dispatch(plan: Mapping[str, Any]) -> dict[str, int]:
    """Reconcile plan-declared stage/selector names with executable dispatch.

    JSON Schema closes the reviewed plan values, but it cannot prove that this
    validator implements every named producer.  This independent comparison is
    deliberately performed while loading the plan, before S03 or S16 can be
    emitted.
    """

    stage_contract = plan.get("stage_evidence_contract")
    if not isinstance(stage_contract, Mapping):
        raise GateError(
            "GA12-PLAN-STAGE-DISPATCH",
            "stage_evidence_contract must be an object",
        )
    primitive_stages = stage_contract.get("primitive_stages")
    if not isinstance(primitive_stages, list) or not all(
        isinstance(row, Mapping) for row in primitive_stages
    ):
        raise GateError(
            "GA12-PLAN-STAGE-DISPATCH",
            "primitive stage declarations must be object rows",
        )
    declared_stage_dispatch = {
        row.get("token_id"): row.get("producer_check_id") for row in primitive_stages
    }
    if len(declared_stage_dispatch) != len(
        primitive_stages
    ) or declared_stage_dispatch != dict(STAGE_PRODUCER_DISPATCH):
        raise GateError(
            "GA12-PLAN-STAGE-DISPATCH",
            "plan primitive stage producers differ from executable dispatch",
        )
    declared_stage_order = [row["token_id"] for row in primitive_stages]
    if declared_stage_order != list(STAGE_PRODUCER_DISPATCH):
        raise GateError(
            "GA12-PLAN-STAGE-DISPATCH",
            "plan primitive stage order differs from executable dispatch",
        )
    declared_observation_dispatch = {
        row.get("token_id"): tuple(row.get("required_observation_ids", ()))
        for row in primitive_stages
    }
    if declared_observation_dispatch != dict(STAGE_OBSERVATION_DISPATCH):
        raise GateError(
            "GA12-PLAN-STAGE-OBSERVATION-DISPATCH",
            "plan primitive stage observations differ from executable dispatch",
        )

    nested_ids = stage_contract.get("nested_contract_ids")
    if nested_ids != list(NESTED_CONTRACT_PRODUCER_DISPATCH):
        raise GateError(
            "GA12-PLAN-NESTED-CONTRACT-DISPATCH",
            "plan nested contract IDs differ from executable producer dispatch",
        )

    producer_to_token = {
        producer_check_id: token_id
        for token_id, producer_check_id in STAGE_PRODUCER_DISPATCH.items()
    }
    correction_contract = plan.get("correction_closure_contract")
    if not isinstance(correction_contract, Mapping):
        raise GateError(
            "GA12-PLAN-EVIDENCE-SELECTOR-DISPATCH",
            "correction_closure_contract must be an object",
        )
    finding_requirements = correction_contract.get("finding_evidence_requirements")
    common_tokens = correction_contract.get("common_required_stage_token_ids")
    if not isinstance(finding_requirements, list) or not isinstance(
        common_tokens, list
    ):
        raise GateError(
            "GA12-PLAN-EVIDENCE-SELECTOR-DISPATCH",
            "correction evidence requirements must be arrays",
        )
    declared_selectors: set[str] = set()
    finding_ids: list[str] = []
    for row in finding_requirements:
        if not isinstance(row, Mapping):
            raise GateError(
                "GA12-PLAN-EVIDENCE-SELECTOR-DISPATCH",
                "finding evidence requirement must be an object",
            )
        finding_id = row.get("finding_id")
        if not isinstance(finding_id, str):
            raise GateError(
                "GA12-PLAN-EVIDENCE-SELECTOR-DISPATCH",
                "finding evidence requirement lacks finding_id",
            )
        finding_ids.append(finding_id)
        additional = row.get("additional_required_stage_token_ids")
        nested = row.get("required_nested_contract_ids")
        selectors = row.get("required_evidence_selectors")
        if not all(
            isinstance(value, list) for value in (additional, nested, selectors)
        ):
            raise GateError(
                "GA12-PLAN-EVIDENCE-SELECTOR-DISPATCH",
                f"finding requirement arrays are malformed: {finding_id}",
            )
        if not set(additional).issubset(STAGE_PRODUCER_DISPATCH):
            raise GateError(
                "GA12-PLAN-STAGE-DISPATCH",
                f"finding names an unimplemented stage token: {finding_id}",
            )
        if not set(nested).issubset(NESTED_CONTRACT_PRODUCER_DISPATCH):
            raise GateError(
                "GA12-PLAN-NESTED-CONTRACT-DISPATCH",
                f"finding names an unimplemented nested contract: {finding_id}",
            )
        required_tokens = set(common_tokens) | set(additional)
        for selector in selectors:
            if selector not in EVIDENCE_SELECTOR_PRODUCER_DISPATCH:
                raise GateError(
                    "GA12-PLAN-EVIDENCE-SELECTOR-DISPATCH",
                    f"finding names an unimplemented evidence selector: {selector}",
                )
            producer = EVIDENCE_SELECTOR_PRODUCER_DISPATCH[selector]
            if producer_to_token[producer] not in required_tokens:
                raise GateError(
                    "GA12-PLAN-EVIDENCE-SELECTOR-DISPATCH",
                    f"selector producer is not required by {finding_id}: {selector}",
                )
            declared_selectors.add(selector)
    if declared_selectors != set(EVIDENCE_SELECTOR_PRODUCER_DISPATCH):
        raise GateError(
            "GA12-PLAN-EVIDENCE-SELECTOR-DISPATCH",
            "plan evidence selector set differs from executable dispatch",
        )
    if finding_ids != correction_contract.get("required_finding_ids") or len(
        finding_ids
    ) != len(set(finding_ids)):
        raise GateError(
            "GA12-PLAN-CORRECTION-COVERAGE",
            "finding requirements must be an exact ordered partition of required findings",
        )

    controls = plan.get("control_contract")
    if not isinstance(controls, Mapping):
        raise GateError(
            "GA12-PLAN-CONTROL-COVERAGE", "control_contract must be an object"
        )
    control_rows = controls.get("control_evidence_requirements")
    control_ids = controls.get("offline_control_ids")
    if not isinstance(control_rows, list) or not isinstance(control_ids, list):
        raise GateError(
            "GA12-PLAN-CONTROL-COVERAGE",
            "control evidence requirements must be arrays",
        )
    observed_control_ids: list[str] = []
    for row in control_rows:
        if not isinstance(row, Mapping):
            raise GateError(
                "GA12-PLAN-CONTROL-COVERAGE",
                "control evidence requirement must be an object",
            )
        observed_control_ids.append(row.get("control_id"))
        if not set(row.get("required_stage_token_ids", ())).issubset(
            STAGE_PRODUCER_DISPATCH
        ) or not set(row.get("required_nested_contract_ids", ())).issubset(
            NESTED_CONTRACT_PRODUCER_DISPATCH
        ):
            raise GateError(
                "GA12-PLAN-CONTROL-COVERAGE",
                f"control names an unimplemented producer: {row.get('control_id')}",
            )
    if observed_control_ids != control_ids or len(observed_control_ids) != len(
        set(observed_control_ids)
    ):
        raise GateError(
            "GA12-PLAN-CONTROL-COVERAGE",
            "control requirements must be an exact ordered partition of offline controls",
        )
    return {
        "primitive_stage_count": len(primitive_stages),
        "nested_contract_count": len(nested_ids),
        "evidence_selector_count": len(declared_selectors),
        "control_requirement_count": len(control_rows),
        "finding_requirement_count": len(finding_requirements),
    }


def validate_exclusion_contract(
    plan: Mapping[str, Any],
) -> tuple[Mapping[str, str], ...]:
    candidate = plan["candidate_projection"]
    exclusions = candidate["excluded_paths"]
    mandatory = {
        ("exact", plan["index_path"]),
        ("exact", plan["index_sidecar_path"]),
        ("exact", plan["canonical_report_path"]),
        ("prefix", "gate/decisions/reiyah.gate-a-decision-"),
        (
            "prefix",
            "gate/public-distribution-receipts/reiyah.public-distribution-receipt-",
        ),
        ("prefix", ".git/"),
    }
    observed: set[tuple[str, str]] = set()
    for exclusion in exclusions:
        matcher = (exclusion["match_kind"], exclusion["path"])
        if matcher in observed:
            raise GateError(
                "GA12-PLAN-EXCLUSION-UNIQUE", f"duplicate exclusion matcher: {matcher}"
            )
        observed.add(matcher)
        kind, path = matcher
        is_structural = matcher in mandatory
        is_macos_cache = kind == "exact" and path == ".DS_Store"
        is_future_rights_event_artifact = (
            kind == "exact"
            and path
            == "evidence/public-rights-revalidation-2026-08-25-gate-a-static-correction-1.2.0.json"
        )
        parts = PurePosixPath(path.removesuffix("/")).parts
        is_cache = (
            kind == "prefix"
            and path.endswith("/")
            and parts
            and parts[-1] in {"__pycache__", ".pytest_cache"}
        )
        if not (
            is_structural
            or is_future_rights_event_artifact
            or is_macos_cache
            or is_cache
        ):
            raise GateError(
                "GA12-PLAN-EXCLUSION-UNAUTHORIZED",
                f"candidate projection exclusion is outside the closed structural/cache boundary: {matcher}",
            )
    missing = sorted(mandatory - observed)
    if missing:
        raise GateError(
            "GA12-PLAN-EXCLUSION-MISSING",
            f"mandatory candidate exclusions are absent: {missing}",
        )
    return tuple(MappingProxyType(dict(item)) for item in exclusions)


PLAN_TOOL_BINDING_CONTRACT = (
    ("external_launcher", LAUNCHER_PATH),
    ("validator_and_index_renderer", TOOL_PATH),
    ("scientific_derivation_module", SCIENCE_MODULE_PATH),
    ("toolchain_lock", LOCK_PATH),
)


def validate_plan_tool_bindings(
    snapshot: RepositorySnapshot,
    bindings: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if len(bindings) != len(PLAN_TOOL_BINDING_CONTRACT):
        raise GateError(
            "GA12-PLAN-TOOL-BINDING",
            "plan must contain the exact four ordered tool bindings",
        )
    evidence: list[dict[str, Any]] = []
    for binding, (role, path) in zip(bindings, PLAN_TOOL_BINDING_CONTRACT, strict=True):
        if binding.get("role") != role or binding.get("path") != path:
            raise GateError(
                "GA12-PLAN-TOOL-BINDING",
                f"unexpected tool role/path for {role}",
            )
        evidence.append(
            {
                "role": role,
                **validate_bound_bytes(snapshot, binding, "GA12-PLAN-TOOL-BINDING"),
            }
        )
    return evidence


def load_validation_plan(
    snapshot: RepositorySnapshot,
    dependencies: Mapping[str, Any],
) -> tuple[Mapping[str, Any], dict[str, Any]]:
    plan = strict_json(snapshot.read(PLAN_PATH), PLAN_PATH)
    if not isinstance(plan, dict):
        raise GateError("GA12-PLAN-SHAPE", "validation plan must be an object")
    validator = validator_for_schema(
        snapshot,
        dependencies,
        PLAN_SCHEMA_PATH,
        (COMMON_SCHEMA_PATH,),
    )
    errors = schema_error_records(validator, plan)
    if errors:
        first = errors[0]
        raise GateError(
            "GA12-PLAN-SCHEMA",
            f"validation plan failed {first['schema_keyword']} at {first['instance_pointer']}: {first['message']}",
        )
    rule_ids = [rule["rule_id"] for rule in plan["rules"]]
    if len(rule_ids) != len(set(rule_ids)):
        raise GateError(
            "GA12-PLAN-RULE-ID", "validation plan rule_id values must be unique"
        )
    required = set(plan["required_artifacts"])
    mandatory_required = {
        PLAN_PATH,
        PLAN_SCHEMA_PATH,
        INDEX_SCHEMA_PATH,
        REPORT_SCHEMA_PATH,
        COMMON_SCHEMA_PATH,
        TOOL_PATH,
        LAUNCHER_PATH,
        SCIENCE_MODULE_PATH,
        LOCK_PATH,
        PROTOCOL_MANIFEST_PATH,
        DEFINITION_REGISTRY_PATH,
        SCIENTIFIC_PROFILE_PATH,
    }
    if not mandatory_required.issubset(required):
        raise GateError(
            "GA12-PLAN-REQUIRED-ARTIFACT",
            f"plan omits validator-critical artifacts: {sorted(mandatory_required - required)}",
        )
    missing_required = sorted(required - set(snapshot.files))
    if missing_required:
        raise GateError(
            "GA12-PLAN-REQUIRED-ARTIFACT",
            f"required artifacts are absent: {missing_required}",
        )
    tool_evidence = validate_plan_tool_bindings(snapshot, plan["tool_bindings"])
    narrative_evidence: list[dict[str, Any]] = []
    narrative_bindings = plan.get("narrative_bindings")
    if not isinstance(narrative_bindings, list) or len(narrative_bindings) != len(
        NARRATIVE_CANDIDATE_MARKERS
    ):
        raise GateError(
            "GA12-PLAN-NARRATIVE-BINDING",
            "plan must bind the exact three candidate narratives",
        )
    for binding, expected_path in zip(
        narrative_bindings, NARRATIVE_CANDIDATE_MARKERS, strict=True
    ):
        if not isinstance(binding, Mapping) or binding.get("path") != expected_path:
            raise GateError(
                "GA12-PLAN-NARRATIVE-BINDING",
                f"unexpected narrative binding path: {expected_path}",
            )
        narrative_evidence.append(
            validate_bound_bytes(snapshot, binding, "GA12-PLAN-NARRATIVE-BINDING")
        )
    dispatch_evidence = validate_plan_evidence_dispatch(plan)
    exclusions = validate_exclusion_contract(plan)
    return MappingProxyType(plan), {
        "plan_id": plan["plan_id"],
        "rule_count": len(rule_ids),
        "required_artifact_count": len(required),
        "tool_bindings": tool_evidence,
        "narrative_bindings": narrative_evidence,
        "evidence_dispatch": dispatch_evidence,
        "exclusion_count": len(exclusions),
    }


def exclusion_matches(path: str, exclusion: Mapping[str, str]) -> bool:
    return (
        path == exclusion["path"]
        if exclusion["match_kind"] == "exact"
        else path.startswith(exclusion["path"])
    )


def candidate_projection(
    snapshot: RepositorySnapshot,
    plan: Mapping[str, Any],
) -> CandidateProjection:
    exclusions = validate_exclusion_contract(plan)
    included: dict[str, SnapshotFile] = {}
    for path, item in snapshot.files.items():
        matches = [
            exclusion for exclusion in exclusions if exclusion_matches(path, exclusion)
        ]
        if len(matches) > 1:
            raise GateError(
                "GA12-PROJECTION-EXCLUSION-OVERLAP", f"multiple exclusions match {path}"
            )
        if not matches:
            included[path] = item
    rows: list[bytes] = []
    for path in sorted(included, key=lambda value: value.encode("utf-8")):
        item = included[path]
        rows.append(
            path.encode("utf-8")
            + b"\x00"
            + item.sha256.encode("ascii")
            + b"\x00"
            + str(item.size).encode("ascii")
            + b"\n"
        )
    serialized = b"".join(rows)
    return CandidateProjection(
        files=MappingProxyType(included),
        exclusions=exclusions,
        serialized=serialized,
        sha256=hashlib.sha256(serialized).hexdigest(),
        artifact_count=len(included),
        byte_count=sum(item.size for item in included.values()),
    )


def hard_bound_predecessor_bytes(
    snapshot: RepositorySnapshot, path: str
) -> dict[str, Any]:
    expected_digest, expected_size = PREDECESSOR_BINDINGS[path]
    item = snapshot.files.get(path)
    if item is None:
        raise GateError(
            "GA12-PREDECESSOR-BINDING", f"predecessor binding is absent: {path}"
        )
    if item.sha256 != expected_digest or item.size != expected_size:
        raise GateError(
            "GA12-PREDECESSOR-BINDING", f"predecessor byte binding differs: {path}"
        )
    return {
        "path": path,
        "sha256": f"sha256:{expected_digest}",
        "byte_size": expected_size,
    }


def verify_predecessor_git_objects(snapshot: RepositorySnapshot) -> dict[str, str]:
    object_format = (
        run_git(["rev-parse", "--show-object-format"]).decode("ascii", "strict").strip()
    )
    if object_format != "sha1":
        raise GateError(
            "GA12-PREDECESSOR-GIT-OBJECT",
            f"predecessor commits require sha1 repository, observed {object_format}",
        )
    for commit in (PREDECESSOR_PACKET_COMMIT, PREDECESSOR_RECEIPT_COMMIT):
        content = run_git(["cat-file", "commit", commit])
        if git_oid(content, object_format, "commit") != commit:
            raise GateError(
                "GA12-PREDECESSOR-GIT-OBJECT", f"commit object digest differs: {commit}"
            )
    packet_tree = (
        run_git(["rev-parse", f"{PREDECESSOR_PACKET_COMMIT}^{{tree}}"])
        .decode("ascii")
        .strip()
    )
    receipt_tree = (
        run_git(["rev-parse", f"{PREDECESSOR_RECEIPT_COMMIT}^{{tree}}"])
        .decode("ascii")
        .strip()
    )
    receipt_parent = (
        run_git(["rev-parse", f"{PREDECESSOR_RECEIPT_COMMIT}^"]).decode("ascii").strip()
    )
    if (
        packet_tree != PREDECESSOR_PACKET_TREE
        or receipt_tree != PREDECESSOR_RECEIPT_TREE
        or receipt_parent != PREDECESSOR_PACKET_COMMIT
    ):
        raise GateError(
            "GA12-PREDECESSOR-GIT-LINEAGE",
            "predecessor commit trees or first-parent lineage differ",
        )
    historical_index = snapshot.read(PREDECESSOR_INDEX_PATH)
    canonical_report = snapshot.read(PREDECESSOR_REPORT_PATH)
    publisher_receipt = snapshot.read(PREDECESSOR_RECEIPT_PATH)
    if (
        run_git(
            ["show", f"{PREDECESSOR_PACKET_COMMIT}:gate/GATE_A_EVIDENCE_INDEX.json"]
        )
        != historical_index
    ):
        raise GateError(
            "GA12-PREDECESSOR-GIT-BYTES",
            "historical index is not the packet commit blob",
        )
    if (
        run_git(["show", f"{PREDECESSOR_PACKET_COMMIT}:{PREDECESSOR_REPORT_PATH}"])
        != canonical_report
    ):
        raise GateError(
            "GA12-PREDECESSOR-GIT-BYTES",
            "canonical 1.1.2 report is not the packet commit blob",
        )
    if (
        run_git(["show", f"{PREDECESSOR_RECEIPT_COMMIT}:{PREDECESSOR_RECEIPT_PATH}"])
        != publisher_receipt
    ):
        raise GateError(
            "GA12-PREDECESSOR-GIT-BYTES",
            "seq-3 receipt is not the receipt-bearing commit blob",
        )
    return {
        "packet_commit": PREDECESSOR_PACKET_COMMIT,
        "packet_tree": PREDECESSOR_PACKET_TREE,
        "receipt_bearing_commit": PREDECESSOR_RECEIPT_COMMIT,
        "receipt_tree": PREDECESSOR_RECEIPT_TREE,
    }


def validate_predecessor_inheritance(
    snapshot: RepositorySnapshot,
    plan: Mapping[str, Any],
    candidate: CandidateProjection,
) -> tuple[dict[str, Any], Mapping[str, Mapping[str, Any]]]:
    predecessor_plan = plan["predecessor_inheritance"]
    plan_binding_names = {
        "historical_index": PREDECESSOR_INDEX_PATH,
        "historical_sidecar": PREDECESSOR_SIDECAR_PATH,
        "canonical_report": PREDECESSOR_REPORT_PATH,
        "publisher_receipt": PREDECESSOR_RECEIPT_PATH,
        "recovery_record": PREDECESSOR_RECOVERY_PATH,
    }
    bindings: dict[str, dict[str, Any]] = {}
    for name, path in plan_binding_names.items():
        expected = hard_bound_predecessor_bytes(snapshot, path)
        if predecessor_plan[name] != expected:
            raise GateError(
                "GA12-PREDECESSOR-PLAN-BINDING",
                f"plan {name} binding differs from hard-bound bytes",
            )
        bindings[name] = expected
    git_evidence = verify_predecessor_git_objects(snapshot)
    recovery = strict_json(
        snapshot.read(PREDECESSOR_RECOVERY_PATH), PREDECESSOR_RECOVERY_PATH
    )
    expected_recovery_values = {
        ("release_commits", "packet", "commit"): PREDECESSOR_PACKET_COMMIT,
        ("release_commits", "packet", "tree"): PREDECESSOR_PACKET_TREE,
        ("release_commits", "receipt_bearing", "commit"): PREDECESSOR_RECEIPT_COMMIT,
        ("release_commits", "receipt_bearing", "tree"): PREDECESSOR_RECEIPT_TREE,
        (
            "release_commits",
            "receipt_bearing",
            "first_parent",
        ): PREDECESSOR_PACKET_COMMIT,
        ("canonical_versioned_artifacts", "validation_report", "sha256"): bindings[
            "canonical_report"
        ]["sha256"],
        ("canonical_versioned_artifacts", "distribution_receipt", "sha256"): bindings[
            "publisher_receipt"
        ]["sha256"],
    }
    for keys, expected in expected_recovery_values.items():
        value: Any = recovery
        for key in keys:
            value = value[key] if isinstance(value, dict) and key in value else None
        if value != expected:
            raise GateError(
                "GA12-PREDECESSOR-RECOVERY",
                f"recovery binding differs at {'/'.join(keys)}",
            )
    historical_index = strict_json(
        snapshot.read(PREDECESSOR_INDEX_PATH), PREDECESSOR_INDEX_PATH
    )
    if (
        not isinstance(historical_index, dict)
        or historical_index.get("version") != "1.1.2"
    ):
        raise GateError(
            "GA12-PREDECESSOR-INDEX", "historical predecessor index identity differs"
        )
    artifacts = historical_index.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != 347:
        raise GateError(
            "GA12-PREDECESSOR-INDEX",
            "historical predecessor index must contain exactly 347 artifacts",
        )
    predecessor_entries: dict[str, Mapping[str, Any]] = {}
    for entry in artifacts:
        artifact = entry.get("artifact") if isinstance(entry, dict) else None
        path = artifact.get("path") if isinstance(artifact, dict) else None
        digest = artifact.get("sha256") if isinstance(artifact, dict) else None
        if (
            not isinstance(path, str)
            or not isinstance(digest, str)
            or path in predecessor_entries
        ):
            raise GateError(
                "GA12-PREDECESSOR-INDEX",
                "historical index has invalid or duplicate artifact paths",
            )
        predecessor_entries[path] = entry
    changed = predecessor_plan["changed_paths"]
    added = predecessor_plan["added_paths"]
    removed = predecessor_plan["removed_paths"]
    if (
        changed != sorted(changed)
        or added != sorted(added)
        or removed != sorted(removed)
    ):
        raise GateError(
            "GA12-PREDECESSOR-PLAN-ORDER",
            "changed, added, and removed path sets must be bytewise sorted",
        )
    changed_set = set(changed)
    added_set = set(added)
    predecessor_paths = set(predecessor_entries)
    if not changed_set.issubset(predecessor_paths):
        raise GateError(
            "GA12-PREDECESSOR-PLAN-CHANGED",
            f"changed paths are not predecessor artifacts: {sorted(changed_set - predecessor_paths)}",
        )
    missing = sorted(predecessor_paths - set(candidate.files))
    if missing != removed:
        raise GateError(
            "GA12-PREDECESSOR-MISSING",
            f"predecessor removal set differs: expected={removed}, observed={missing}",
        )
    drift: list[str] = []
    unchanged_count = 0
    for path, entry in sorted(predecessor_entries.items()):
        if path not in candidate.files:
            continue
        old_digest = entry["artifact"]["sha256"]
        current_digest = f"sha256:{candidate.files[path].sha256}"
        if path in changed_set:
            if current_digest == old_digest:
                raise GateError(
                    "GA12-PREDECESSOR-CHANGED-NOOP",
                    f"declared correction did not change bytes: {path}",
                )
        elif current_digest != old_digest:
            drift.append(path)
        else:
            unchanged_count += 1
    if drift:
        raise GateError(
            "GA12-PREDECESSOR-UNEXPECTED-DRIFT",
            f"undeclared predecessor drift: {drift}",
        )
    actual_added = set(candidate.files) - predecessor_paths
    if added_set != actual_added:
        raise GateError(
            "GA12-PREDECESSOR-ADDED-SET",
            f"successor added set differs: missing={sorted(actual_added - added_set)}, unexpected={sorted(added_set - actual_added)}",
        )
    summary = {
        "subject_version": "1.1.2",
        "historical_index_binding": bindings["historical_index"],
        "historical_sidecar_binding": bindings["historical_sidecar"],
        "canonical_report_binding": bindings["canonical_report"],
        "publisher_receipt_binding": bindings["publisher_receipt"],
        "recovery_record_binding": bindings["recovery_record"],
        "predecessor_artifact_count": len(predecessor_entries),
        "unchanged_artifact_count": unchanged_count,
        "changed_paths": changed,
        "added_paths": added,
        "removed_paths": removed,
        "missing_paths": [],
        "unexpected_drift_paths": [],
    }
    evidence = {"git_objects": git_evidence, **summary}
    return evidence, MappingProxyType(predecessor_entries)


ADDED_EXACT_ROLES = {
    "docs/GATE_A_1_1_2_ADVERSARIAL_REVIEW.md": "adversarial_review",
    "docs/GATE_A_1_2_0_CONSISTENCY_REVIEW.md": "adversarial_review",
    "evidence/rights-observations/2026-08-25-iso-open-data-gate-a-static-correction-1.2.0.json": (
        "rights_observation_capture_manifest"
    ),
    "evidence/rights-observations/2026-08-25-nist-technical-series-gate-a-static-correction-1.2.0.json": (
        "rights_observation_capture_manifest"
    ),
    "gate/decisions/OPERATOR_DECISION-1.2.0.template.json": "operator_decision_template",
    PREDECESSOR_REPORT_PATH: "historical_candidate_artifact",
    PREDECESSOR_RECOVERY_PATH: "historical_packet_recovery",
    PREDECESSOR_INDEX_PATH: "historical_candidate_artifact",
    PREDECESSOR_SIDECAR_PATH: "historical_candidate_artifact",
    LAUNCHER_PATH: "validation_launcher",
    TOOL_PATH: "offline_validator",
    SCIENCE_MODULE_PATH: "offline_validator",
    LOCK_PATH: "toolchain_lock",
}

MEDIA_TYPES = {
    ".cff": "application/yaml",
    ".html": "text/html",
    ".json": "application/json",
    ".jsonl": "application/x-ndjson",
    ".lock": "text/plain",
    ".md": "text/markdown",
    ".pdf": "application/pdf",
    ".py": "text/x-python",
    ".sh": "text/x-shellscript",
    ".sha256": "text/plain",
    ".yaml": "application/yaml",
    ".yml": "application/yaml",
}


def role_for_candidate(path: str, predecessor_entry: Mapping[str, Any] | None) -> str:
    if predecessor_entry is not None:
        return str(predecessor_entry["role"])
    if path in ADDED_EXACT_ROLES:
        return ADDED_EXACT_ROLES[path]
    if path.startswith("fixtures/v1.2/good/") and path.endswith(".json"):
        return "known_good_fixture"
    if path.startswith("fixtures/v1.2/governance-good/") and path.endswith(".json"):
        return "known_good_fixture"
    if path.startswith("fixtures/v1.2/governance/") and path.endswith(".json"):
        return "known_good_fixture"
    if path.startswith("fixtures/v1.2/known-bad/") and path.endswith(".json"):
        return "known_bad_fixture"
    if path.startswith("schemas/") and path.endswith(".schema.json"):
        return "schema"
    if path.startswith("manifests/mission/") and path.endswith(".json"):
        return "mission_manifest"
    if path.startswith("manifests/protocol/") and path.endswith(".json"):
        return "protocol_manifest"
    if path.startswith("manifests/definitions/") and path.endswith(".json"):
        return "protocol_definition_registry"
    if path.startswith("manifests/research/") and path.endswith(".json"):
        return "research_function_registry"
    if path.startswith("manifests/scientific/") and path.endswith(".json"):
        return "scientific_contract_profile"
    if path.startswith("manifests/history/") and path.endswith(".json"):
        return "manifest_release_ledger"
    if path.startswith("history/gate-a-1.1.2/"):
        return "historical_candidate_artifact"
    raise GateError("GA12-INDEX-ROLE", f"no closed Gate A 1.2 artifact role for {path}")


def media_type_for_candidate(path: str) -> str:
    if path in {".gitattributes", ".gitignore", "LICENSE", "NOTICE"}:
        return "text/plain"
    suffix = PurePosixPath(path).suffix.lower()
    if suffix not in MEDIA_TYPES:
        raise GateError("GA12-INDEX-MEDIA-TYPE", f"no closed media type for {path}")
    return MEDIA_TYPES[suffix]


def derived_artifact_id(path: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-")
    if len(slug) > 125:
        slug = (
            slug[:92].rstrip("-")
            + "-"
            + hashlib.sha256(path.encode("utf-8")).hexdigest()[:24]
        )
    return "reiyah.artifact.indexed-" + slug


def candidate_artifact_reference(
    path: str,
    item: SnapshotFile,
    predecessor_entry: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if (
        predecessor_entry is not None
        and predecessor_entry["artifact"].get("sha256") == f"sha256:{item.sha256}"
    ):
        predecessor_artifact = predecessor_entry["artifact"]
        reference = {
            "artifact_id": predecessor_artifact["artifact_id"],
            "path": path,
            "sha256": f"sha256:{item.sha256}",
            "version": predecessor_artifact.get("version", "1.1.2"),
        }
        if isinstance(predecessor_artifact.get("schema_id"), str):
            reference["schema_id"] = predecessor_artifact["schema_id"]
        return reference
    artifact_id: str | None = None
    schema_id: str | None = None
    version: str | None = None
    if path.endswith(".json"):
        value = strict_json(item.data, path)
        if not isinstance(value, dict):
            raise GateError(
                "GA12-INDEX-JSON-SHAPE",
                f"indexed JSON artifact must be an object: {path}",
            )
        candidate_id = value.get("artifact_id")
        if isinstance(candidate_id, str) and not candidate_id.startswith("replace."):
            artifact_id = candidate_id
        schema_id = (
            value.get("$id") if path.startswith("schemas/") else value.get("schema_id")
        )
        if not isinstance(schema_id, str):
            schema_id = None
        version_value = value.get("version", value.get("schema_version"))
        if isinstance(version_value, str):
            version = version_value
        elif schema_id is not None:
            match = re.search(r"/(\d+\.\d+(?:\.\d+)?)/", schema_id)
            if match is not None:
                parts = match.group(1).split(".")
                version = match.group(1) if len(parts) == 3 else match.group(1) + ".0"
    if path == PREDECESSOR_INDEX_PATH:
        artifact_id = "reiyah.artifact.historical-gate-a-index-1.1.2"
        version = "1.1.2"
    if artifact_id is None:
        artifact_id = derived_artifact_id(path)
    if version is None:
        version = ARTIFACT_VERSION
    reference = {
        "artifact_id": artifact_id,
        "path": path,
        "sha256": f"sha256:{item.sha256}",
        "version": version,
    }
    if schema_id is not None:
        reference["schema_id"] = schema_id
    return reference


def rendered_exclusions(candidate: CandidateProjection) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for exclusion in candidate.exclusions:
        slug = (
            re.sub(r"[^a-z0-9]+", "-", exclusion["path"].lower()).strip("-") or "root"
        )
        exclusion_id = "reiyah.exclusion.gate-a-1-2-0-" + slug
        if exclusion_id in seen_ids:
            exclusion_id += "-" + exclusion["match_kind"]
        if exclusion_id in seen_ids:
            raise GateError(
                "GA12-INDEX-EXCLUSION-ID",
                f"derived exclusion ID collision: {exclusion['path']}",
            )
        seen_ids.add(exclusion_id)
        output.append({"exclusion_id": exclusion_id, **dict(exclusion)})
    return output


def render_candidate_index(
    snapshot: RepositorySnapshot,
    dependencies: Mapping[str, Any],
    plan: Mapping[str, Any],
    candidate: CandidateProjection,
    predecessor_summary: Mapping[str, Any],
    predecessor_entries: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], bytes]:
    artifacts: list[dict[str, Any]] = []
    artifact_ids: set[str] = set()
    for path in sorted(candidate.files, key=lambda value: value.encode("utf-8")):
        item = candidate.files[path]
        predecessor_entry = predecessor_entries.get(path)
        reference = candidate_artifact_reference(path, item, predecessor_entry)
        if reference["artifact_id"] in artifact_ids:
            raise GateError(
                "GA12-INDEX-ARTIFACT-ID",
                f"duplicate indexed artifact ID: {reference['artifact_id']}",
            )
        artifact_ids.add(reference["artifact_id"])
        artifacts.append(
            {
                "role": role_for_candidate(path, predecessor_entry),
                "media_type": media_type_for_candidate(path),
                "digest_algorithm": "sha256",
                "byte_size": item.size,
                "artifact": reference,
            }
        )
    predecessor = plan["predecessor_inheritance"]
    index = {
        "schema_id": "https://schemas.reiyah.invalid/gate-a/1.2.0/gate-a-index.schema.json",
        "schema_version": ARTIFACT_VERSION,
        "artifact_id": "reiyah.artifact.gate-a-index-1.2.0",
        "index_id": "reiyah.gate-a-evidence-index",
        "version": ARTIFACT_VERSION,
        "as_of_date": "2026-08-25",
        "lifecycle_status": "proposed",
        "architecture_status": "candidate_pending_canonical_report",
        "operator_acceptance_state": "unaccepted",
        "ga_17_state": "not_evaluated",
        "operator_decision_binding": None,
        "mission_release_id": MISSION_RELEASE_ID,
        "protocol_release_id": PROTOCOL_RELEASE_ID,
        "distribution_profile": "public_open_source",
        "source_ledger_version": "1.1.0",
        "predecessor_binding": {
            "index": {
                "artifact_id": "reiyah.artifact.historical-gate-a-index-1.1.2",
                "path": predecessor["historical_index"]["path"],
                "sha256": predecessor["historical_index"]["sha256"],
                "version": "1.1.2",
            },
            "validation_report": {
                "artifact_id": "reiyah.validation-report.gate-a-1.1.2",
                "path": predecessor["canonical_report"]["path"],
                "sha256": predecessor["canonical_report"]["sha256"],
                "version": "1.1.2",
            },
            "recovery_record": {
                "artifact_id": "reiyah.artifact.gate-a-1.1.2-recovery-1.2.0",
                "path": predecessor["recovery_record"]["path"],
                "sha256": predecessor["recovery_record"]["sha256"],
                "schema_id": "https://schemas.reiyah.invalid/gate-a/1.2.0/historical-packet-recovery.schema.json",
                "version": ARTIFACT_VERSION,
            },
        },
        "predecessor_correction_scope": {
            "review_path": "docs/GATE_A_1_1_2_ADVERSARIAL_REVIEW.md",
            "finding_ids": [f"AR-{number:03d}" for number in range(1, 13)],
            "changed_predecessor_paths": predecessor_summary["changed_paths"],
            "added_paths": predecessor_summary["added_paths"],
            "removed_predecessor_paths": predecessor_summary["removed_paths"],
            "unchanged_predecessor_artifact_count": predecessor_summary[
                "unchanged_artifact_count"
            ],
        },
        "candidate_projection": {
            "algorithm": "sha256",
            **candidate.summary(),
        },
        "artifacts": artifacts,
        "exclusions": rendered_exclusions(candidate),
        "validation_profile": {
            "entrypoint": LAUNCHER_PATH,
            "implementation": TOOL_PATH,
            "toolchain_lock": LOCK_PATH,
            "release_snapshot_mode": "immutable_clean_git_tree",
            "offline_required": True,
            "deterministic_required": True,
            "fail_closed_required": True,
        },
        "known_good_expectation": "all_pass",
        "known_bad_expectation": "all_fail_for_declared_reason",
        "transport_verification_state": "not_evaluated",
        "runtime_authorized": False,
        "gate_b_authorized": False,
    }
    validator = validator_for_schema(
        snapshot, dependencies, INDEX_SCHEMA_PATH, (COMMON_SCHEMA_PATH,)
    )
    errors = schema_error_records(validator, index)
    if errors:
        first = errors[0]
        raise GateError(
            "GA12-INDEX-SCHEMA",
            f"rendered index failed {first['schema_keyword']} at {first['instance_pointer']}: {first['message']}",
        )
    encoded = (
        json.dumps(
            index, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        + b"\n"
    )
    return index, encoded


def artifact_set_digest(snapshot: RepositorySnapshot, paths: Sequence[str]) -> str:
    records = [
        {
            "path": path,
            "sha256": hashlib.sha256(snapshot.read(path)).hexdigest(),
            "size": len(snapshot.read(path)),
        }
        for path in sorted(paths)
    ]
    return canonical_record_digest(records)


def validate_reference_bytes(
    snapshot: RepositorySnapshot,
    reference: Mapping[str, Any],
    expected_path: str,
    diagnostic: str,
) -> None:
    if reference.get("path") != expected_path:
        raise GateError(diagnostic, f"artifact reference path differs: {expected_path}")
    item = snapshot.files.get(expected_path)
    if (
        item is None
        or reference.get("sha256") != f"sha256:{item.sha256}"
        or reference.get("byte_size") != item.size
    ):
        raise GateError(
            diagnostic, f"artifact reference digest differs: {expected_path}"
        )


def validate_protocol_artifact_bindings(
    snapshot: RepositorySnapshot,
    dependencies: Mapping[str, Any],
) -> dict[str, Any]:
    protocol = strict_json(
        snapshot.read(PROTOCOL_MANIFEST_PATH), PROTOCOL_MANIFEST_PATH
    )
    if not isinstance(protocol, dict):
        raise GateError(
            "GA12-PROTOCOL-SHAPE", "the 1.2 protocol manifest must be an object"
        )
    validator = validator_for_schema(
        snapshot,
        dependencies,
        "schemas/protocol-manifest-1.2.schema.json",
        (COMMON_SCHEMA_PATH,),
    )
    errors = schema_error_records(validator, protocol)
    if errors:
        first = errors[0]
        raise GateError(
            "GA12-PROTOCOL-SCHEMA",
            f"protocol failed {first['schema_keyword']} at {first['instance_pointer']}: {first['message']}",
        )
    bindings = (
        (
            protocol["correction_contract"]["adversarial_review"],
            "docs/GATE_A_1_1_2_ADVERSARIAL_REVIEW.md",
        ),
        (
            protocol["correction_contract"]["candidate_consistency_review"],
            "docs/GATE_A_1_2_0_CONSISTENCY_REVIEW.md",
        ),
        (protocol["definition_registry"], DEFINITION_REGISTRY_PATH),
        (protocol["scientific_contract_profile"], SCIENTIFIC_PROFILE_PATH),
        (protocol["research_function_registry"], RESEARCH_REGISTRY_PATH),
        (
            protocol["public_evidence_profile"],
            "evidence/public-evidence-custody-profile-1.1.0.json",
        ),
    )
    for reference, expected_path in bindings:
        validate_reference_bytes(
            snapshot,
            reference,
            expected_path,
            "GA12-PROTOCOL-ARTIFACT-BINDING",
        )
    research = strict_json(
        snapshot.read(RESEARCH_REGISTRY_PATH), RESEARCH_REGISTRY_PATH
    )
    if not isinstance(research, dict):
        raise GateError(
            "GA12-RESEARCH-REGISTRY-SHAPE",
            "the successor research-function registry must be an object",
        )
    research_validator = validator_for_schema(
        snapshot,
        dependencies,
        "schemas/research-function-registry-1.2.schema.json",
        (COMMON_SCHEMA_PATH,),
    )
    research_errors = schema_error_records(research_validator, research)
    if research_errors:
        first = research_errors[0]
        raise GateError(
            "GA12-RESEARCH-REGISTRY-SCHEMA",
            f"research registry failed {first['schema_keyword']} at {first['instance_pointer']}: {first['message']}",
        )
    validate_successor_chronology(protocol, research)
    return {
        "protocol_release_id": protocol["release_id"],
        "exact_artifact_binding_count": len(bindings),
    }


def validate_successor_chronology(
    protocol: Mapping[str, Any],
    research_registry: Mapping[str, Any],
) -> None:
    correction_date = "2026-08-24"
    if (
        protocol.get("created_on") != correction_date
        or research_registry.get("as_of_date") != correction_date
        or protocol.get("release_id") != PROTOCOL_RELEASE_ID
        or research_registry.get("version") != ARTIFACT_VERSION
    ):
        raise GateError(
            "GA12-RESEARCH-REGISTRY-CHRONOLOGY",
            "the protocol and successor research registry must share the exact retained 2026-08-24 correction date",
        )


def validate_narrative_state_operands(
    protocol: Mapping[str, Any],
    profile: Mapping[str, Any],
    narratives: Mapping[str, str],
) -> None:
    machine_state_valid = (
        protocol.get("release_stage") == "candidate"
        and protocol.get("lifecycle_status") == "proposed"
        and protocol.get("operator_acceptance", {}).get("state") == "unaccepted"
        and protocol.get("correction_contract", {}).get(
            "candidate_findings_must_close_before_architecture_complete"
        )
        is True
        and protocol.get("correction_contract", {}).get("runtime_execution_authorized")
        is False
        and profile.get("profile_status") == "candidate"
        and profile.get("lifecycle_status") == "proposed"
        and profile.get("operator_acceptance_state") == "unaccepted"
        and profile.get("architecture_only") is True
        and profile.get("runtime_authorized") is False
        and profile.get("gate_b_authorized") is False
        and profile.get("scientific_support_claimed") is False
        and profile.get("safety_case_claimed") is False
    )
    markers_valid = set(narratives) == set(NARRATIVE_CANDIDATE_MARKERS) and all(
        marker in narratives.get(path, "")
        for path, marker in NARRATIVE_CANDIDATE_MARKERS.items()
    )
    if not machine_state_valid or not markers_valid:
        raise GateError(
            "GA12-NARRATIVE-STATE-CONSISTENCY",
            "protocol/profile candidate nonclaim state and the three bounded candidate narrative markers must agree",
        )


def validate_narrative_state(snapshot: RepositorySnapshot) -> dict[str, Any]:
    protocol = strict_json(
        snapshot.read(PROTOCOL_MANIFEST_PATH), PROTOCOL_MANIFEST_PATH
    )
    profile = strict_json(
        snapshot.read(SCIENTIFIC_PROFILE_PATH), SCIENTIFIC_PROFILE_PATH
    )
    if not isinstance(protocol, dict) or not isinstance(profile, dict):
        raise GateError(
            "GA12-NARRATIVE-STATE-CONSISTENCY",
            "protocol and profile candidate state operands must be objects",
        )
    narratives: dict[str, str] = {}
    for path in NARRATIVE_CANDIDATE_MARKERS:
        try:
            narratives[path] = snapshot.read(path).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise GateError(
                "GA12-NARRATIVE-STATE-CONSISTENCY",
                f"candidate narrative is not UTF-8: {path}",
            ) from exc
    validate_narrative_state_operands(protocol, profile, narratives)
    return {"candidate_marker_count": len(narratives), "state": "candidate_unaccepted"}


def validate_normative_markdown_surface_operands(
    documents: Mapping[str, bytes],
) -> dict[str, Any]:
    expected_paths = tuple(NORMATIVE_MARKDOWN_SURFACE)
    if tuple(documents) != expected_paths:
        raise GateError(
            "GA12-NORMATIVE-ARCHITECTURE-SURFACE",
            "normative Markdown surface path membership/order differs from the closed inventory",
        )
    rows: list[dict[str, Any]] = []
    for path, required_marker in NORMATIVE_MARKDOWN_SURFACE.items():
        payload = documents[path]
        if not isinstance(payload, bytes):
            raise GateError(
                "GA12-NORMATIVE-ARCHITECTURE-SURFACE",
                f"normative Markdown operand is not bytes: {path}",
            )
        try:
            narrative = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise GateError(
                "GA12-NORMATIVE-ARCHITECTURE-SURFACE",
                f"normative Markdown operand is not UTF-8: {path}",
            ) from exc
        if required_marker not in narrative:
            raise GateError(
                "GA12-NORMATIVE-ARCHITECTURE-SURFACE",
                f"normative Markdown operand lacks its bounded nonclaim marker: {path}",
            )
        rows.append(
            {
                "path": path,
                "sha256": f"sha256:{hashlib.sha256(payload).hexdigest()}",
                "byte_size": len(payload),
            }
        )
    return {
        "document_count": len(rows),
        "documents": rows,
        "document_set_sha256": evidence_sha256(rows),
        "candidate_nonclaim_markers_verified": True,
    }


def validate_normative_markdown_surface(
    snapshot: RepositorySnapshot,
) -> dict[str, Any]:
    return validate_normative_markdown_surface_operands(
        {path: snapshot.read(path) for path in NORMATIVE_MARKDOWN_SURFACE}
    )


REFERENCE_STRUCTURED_DEFINITION_CLASSIFICATIONS: Mapping[str, str] = MappingProxyType(
    {
        "actorReference": "actor_reference",
        "artifactReference": "artifact_reference",
        "evidenceGapBinding": "explicit_evidence_gap",
        "ruleReference": "rule_reference",
        "versionedReference": "versioned_reference",
    }
)

APPLICATION_SCHEMA_PATH_BY_ID: Mapping[str, str] = MappingProxyType(
    {
        ASSURANCE_APPLICATION_SCHEMA_ID: SCIENCE_SCHEMA_PATHS[0],
        HUMAN_APPLICATION_SCHEMA_ID: SCIENCE_SCHEMA_PATHS[1],
        JOINT_APPLICATION_SCHEMA_ID: SCIENCE_SCHEMA_PATHS[2],
        OPE_APPLICATION_SCHEMA_ID: SCIENCE_SCHEMA_PATHS[5],
        STUDY_APPLICATION_SCHEMA_ID: SCIENCE_SCHEMA_PATHS[6],
    }
)


def _json_schema_fragment(document: Mapping[str, Any], fragment: str) -> Any:
    if fragment == "":
        return document
    if not fragment.startswith("/"):
        raise GateError(
            "GA12-REFERENCE-PATH-COVERAGE",
            f"unsupported non-pointer schema fragment: {fragment!r}",
        )
    value: Any = document
    for raw_token in fragment[1:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, Mapping) or token not in value:
            raise GateError(
                "GA12-REFERENCE-PATH-COVERAGE",
                f"schema reference fragment does not resolve: {fragment!r}",
            )
        value = value[token]
    return value


def _instance_pointer_child(pointer: str, token: object) -> str:
    encoded = str(token).replace("~", "~0").replace("/", "~1")
    return f"{pointer}/{encoded}"


def _candidate_reference_binding(
    schema_id: str,
    pointer_glob: str,
    candidate_node_kind: str,
    detected_classification: str,
) -> dict[str, Any]:
    base = {
        "schema_id": schema_id,
        "pointer_glob": pointer_glob,
        "candidate_node_kind": candidate_node_kind,
        "expected_registry_kind": None,
        "local_collection_pointer": None,
    }
    if pointer_glob.endswith("/evidence_refs/*/evidence_ref"):
        # Assumption evidence references have the outer versioned-reference
        # shape, but Gate A 1.2 deliberately has no retained scientific-
        # evidence resolver.  They are owned by the containing assumption
        # predicate, which fails every favorable disposition closed.  Treating
        # these paths as ordinary typed references would advertise a resolver
        # that production intentionally does not possess.
        return base | {
            "classification": "versioned_reference",
            "owner": "explicit_unavailable",
            "expected_kind_policy": "declared_reference_kind",
            "resolution_policy": "assumption_evidence_fail_closed",
            "handler": "assumption_evidence_violations",
        }
    if detected_classification == "rule_reference":
        return base | {
            "classification": "rule_reference",
            "owner": "protocol_definition_registry",
            "expected_kind_policy": "declared_reference_kind",
            "resolution_policy": "typed_registry_reference",
            "handler": "typed_reference_violations",
        }
    if detected_classification == "versioned_reference":
        return base | {
            "classification": "versioned_reference",
            "owner": "protocol_definition_registry",
            "expected_kind_policy": "declared_reference_kind",
            "resolution_policy": "typed_registry_reference",
            "handler": "typed_reference_violations",
        }
    if detected_classification == "actor_reference":
        return base | {
            "classification": "actor_reference",
            "owner": "protocol_definition_registry",
            "expected_kind_policy": "actor_reference_contract",
            "resolution_policy": "typed_registry_reference",
            "handler": "typed_reference_violations",
        }
    if detected_classification == "artifact_reference":
        return base | {
            "classification": "artifact_reference",
            "owner": "repository_snapshot",
            "expected_kind_policy": "declared_artifact_kind",
            "resolution_policy": "exact_snapshot_artifact",
            "handler": "lifecycle_policy_violations",
        }
    if detected_classification == "explicit_evidence_gap":
        return base | {
            "classification": "explicit_evidence_gap",
            "owner": "explicit_unavailable",
            "expected_kind_policy": "not_applicable",
            "resolution_policy": "explicit_non_supporting_gap",
            "handler": "evidence_gap_reference_violations",
        }
    if detected_classification == "schema_reference":
        return base | {
            "classification": "schema_reference",
            "owner": "schema_registry",
            "expected_kind_policy": "schema_identity",
            "resolution_policy": "exact_local_schema",
            "handler": "schema_reference_violations",
        }
    if detected_classification != "stable_identifier":
        raise GateError(
            "GA12-REFERENCE-PATH-COVERAGE",
            f"unrecognized candidate node classification at {schema_id}{pointer_glob}",
        )

    def identity() -> dict[str, Any]:
        return base | {
            "classification": "identity_declaration",
            "owner": "application_identity_space",
            "expected_kind_policy": "not_applicable",
            "resolution_policy": "unique_identity_declaration",
            "handler": "classified_reference_path_violations",
        }

    def registry(kind: str) -> dict[str, Any]:
        return base | {
            "classification": "registry_bare_identifier",
            "owner": "protocol_definition_registry",
            "expected_kind_policy": "exact_registry_kind",
            "expected_registry_kind": kind,
            "resolution_policy": "exact_registry_definition",
            "handler": "classified_reference_path_violations",
        }

    def local(collection: str) -> dict[str, Any]:
        return base | {
            "classification": "document_local_identifier",
            "owner": "application_document",
            "expected_kind_policy": "not_applicable",
            "local_collection_pointer": collection,
            "resolution_policy": "exact_document_member",
            "handler": "classified_reference_path_violations",
        }

    if pointer_glob in {"/artifact_id", "/lifecycle_history/*/event_id"}:
        return identity()
    if pointer_glob.endswith("/basis_ids/*"):
        if (
            schema_id == HUMAN_APPLICATION_SCHEMA_ID
            and pointer_glob == "/readiness/aggregate/estimate/basis_ids/*"
        ):
            return local("/readiness/capabilities/*/capability_id")
        return registry("constraint")

    if schema_id == ASSURANCE_APPLICATION_SCHEMA_ID:
        registry_kinds = {
            "/benchmark_contract/benchmark_id": "benchmark",
            "/bundle_id": "assurance_bundle",
            "/dataset_governance/dataset_id": "dataset",
            "/dataset_governance/ethics_review/assumption_id": "assumption",
            "/odd_contract/odd_id": "odd",
            "/safety_case/case_id": "safety_case",
            "/scenario_contract/scenario_set_id": "scenario_set",
        }
        identity_paths = {
            "/safety_case/claims/*/claim_id",
            "/safety_case/hazards/*/hazard_id",
            "/test_contracts/*/test_id",
        }
        if pointer_glob in registry_kinds:
            return registry(registry_kinds[pointer_glob])
        if pointer_glob in identity_paths:
            return identity()
        if pointer_glob == "/safety_case/claims/*/hazard_refs/*":
            return local("/safety_case/hazards/*/hazard_id")

    if schema_id == HUMAN_APPLICATION_SCHEMA_ID:
        identity_paths = {
            "/assessment_id",
            "/belief/belief_id",
            "/belief/information_set/information_set_id",
            "/decision/decision_id",
            "/decision/information_set/information_set_id",
            "/observation/observation_id",
            "/readiness/readiness_id",
            "/recovery/events/*/event_id",
            "/recovery/index_event/event_id",
            "/recovery/recovery_id",
        }
        registry_kinds = {
            "/belief/normalization_policy_binding/policy_id": "constraint",
            "/belief/state_space/state_ids/*": "state",
            "/belief/state_space/state_space_id": "state_space",
            "/decision/action_space_id": "action_space",
            "/decision/selected_action/value": "action",
            "/readiness/capabilities/*/capability_id": "capability",
            "/readiness/capabilities/*/dimension_id": "dimension",
            "/readiness/window/clock_id": "clock",
            "/readiness/window/window_id": "window",
            "/recovery/events/*/event_type": "event_type",
            "/recovery/index_event/event_type": "event_type",
            "/recovery/window/clock_id": "clock",
            "/recovery/window/window_id": "window",
        }
        local_collections = {
            "/belief/distribution/probabilities/*/state_id": "/belief/state_space/state_ids/*",
            "/readiness/unresolved_capability_ids/*": "/readiness/capabilities/*/capability_id",
            "/recovery/outcome/qualifying_event_id/value": "/recovery/events/*/event_id",
        }
        if pointer_glob in identity_paths:
            return identity()
        if pointer_glob in registry_kinds:
            return registry(registry_kinds[pointer_glob])
        if pointer_glob in local_collections:
            return local(local_collections[pointer_glob])

    if schema_id == JOINT_APPLICATION_SCHEMA_ID:
        if pointer_glob in {
            "/evaluation_id",
            "/joint_silent_miss/opportunity_rows/*/opportunity_id",
        }:
            return identity()
        if pointer_glob.endswith("/assumption_id"):
            return registry("assumption")
        registry_kinds = {
            "/conformal_evaluation/group_universe/*": "group",
            "/joint_silent_miss/opportunity_rows/*/clock_id": "clock",
            "/joint_silent_miss/opportunity_rows/*/window_id": "window",
            "/joint_silent_miss/opportunity_window/clock_id": "clock",
            "/joint_silent_miss/opportunity_window/window_id": "window",
            "/transfer_evaluation/metric_contract/metric_contract_id": "metric",
            "/transfer_evaluation/source_result/domain_id": "domain",
            "/transfer_evaluation/source_result/metric_contract_id": "metric",
            "/transfer_evaluation/target_result/domain_id": "domain",
            "/transfer_evaluation/target_result/metric_contract_id": "metric",
            "/worst_group_evaluation/group_universe/*": "group",
            "/worst_group_evaluation/shared_metric_contract/metric_id": "metric",
        }
        local_collections = {
            "/conformal_evaluation/group_results/*/group_id": "/conformal_evaluation/group_universe/*",
            "/worst_group_evaluation/eligible_group_ids/*": "/worst_group_evaluation/group_universe/*",
            "/worst_group_evaluation/group_results/*/group_id": "/worst_group_evaluation/group_universe/*",
            "/worst_group_evaluation/insufficient_group_ids/*": "/worst_group_evaluation/group_universe/*",
            "/worst_group_evaluation/unknown_group_ids/*": "/worst_group_evaluation/group_universe/*",
            "/worst_group_evaluation/worst_group_ids/*": "/worst_group_evaluation/group_universe/*",
        }
        if pointer_glob in registry_kinds:
            return registry(registry_kinds[pointer_glob])
        if pointer_glob in local_collections:
            return local(local_collections[pointer_glob])

    if schema_id == OPE_APPLICATION_SCHEMA_ID:
        identity_paths = {
            "/evaluation_id",
            "/trajectories/*/steps/*/history_id",
            "/trajectories/*/steps/*/information_set/information_set_id",
            "/trajectories/*/trajectory_id",
        }
        registry_kinds = {
            "/behavior_policy/action_space/action_ids/*": "action",
            "/behavior_policy/action_space/action_space_id": "action_space",
            "/effective_sample_size_by_horizon/*/weight_set_id": "weight_set",
            "/estimators/*/estimator_id": "estimator",
            "/estimators/*/weight_set_id": "weight_set",
            "/reward_contract/reward_signal_id": "reward_signal",
            "/support_assessment/required_cells/*/action_id": "action",
            "/support_assessment/unsupported_cells/*/action_id": "action",
            "/target_policy/action_space/action_ids/*": "action",
            "/target_policy/action_space/action_space_id": "action_space",
            "/trajectories/*/steps/*/behavior_distribution/*/action_id": "action",
            "/trajectories/*/steps/*/history_prefix/*/logged_action_id": "action",
            "/trajectories/*/steps/*/logged_action_id": "action",
            "/trajectories/*/steps/*/target_distribution/*/action_id": "action",
            "/weight_construction/weight_set_id": "weight_set",
        }
        local_collections = {
            "/estimator_selection/candidate_estimator_ids/*": "/estimators/*/estimator_id",
            "/estimator_selection/selected_estimator_ids/*": "/estimators/*/estimator_id",
            "/support_assessment/required_cells/*/history_id": "/trajectories/*/steps/*/history_id",
            "/support_assessment/unsupported_cells/*/history_id": "/trajectories/*/steps/*/history_id",
        }
        if pointer_glob in identity_paths:
            return identity()
        if pointer_glob in registry_kinds:
            return registry(registry_kinds[pointer_glob])
        if pointer_glob in local_collections:
            return local(local_collections[pointer_glob])

    if schema_id == STUDY_APPLICATION_SCHEMA_ID:
        if pointer_glob in {
            "/deviations/*/deviation_id",
            "/identification_queries/*/query_id",
            "/split_policy/analysis_unit_ids/*",
        }:
            return identity()
        registry_kinds = {
            "/adjustment_sets/*/adjustment_set_id": "adjustment_set",
            "/causal_graph/graph_id": "graph",
            "/causal_graph/nodes/*/node_id": "graph_node",
            "/estimands/*/estimand_id": "estimand",
            "/split_policy/split_unit": "unit",
            "/study_id": "record_identity",
            "/unit_of_analysis": "unit",
        }
        local_collections = {
            "/adjustment_sets/*/node_ids/*": "/causal_graph/nodes/*/node_id",
            "/causal_graph/edges/*/from_node_id": "/causal_graph/nodes/*/node_id",
            "/causal_graph/edges/*/to_node_id": "/causal_graph/nodes/*/node_id",
            "/control_strategy/selected_adjustment_set_ids/*": "/adjustment_sets/*/adjustment_set_id",
            "/estimands/*/outcome_node_id": "/causal_graph/nodes/*/node_id",
            "/estimands/*/treatment_node_id": "/causal_graph/nodes/*/node_id",
            "/identification_queries/*/adjustment_set_id": "/adjustment_sets/*/adjustment_set_id",
            "/identification_queries/*/estimand_id": "/estimands/*/estimand_id",
            "/identification_queries/*/outcome_node_id": "/causal_graph/nodes/*/node_id",
            "/identification_queries/*/treatment_node_id": "/causal_graph/nodes/*/node_id",
            **{
                f"/split_policy/split_manifests/{index}/member_ids/*": "/split_policy/analysis_unit_ids/*"
                for index in range(3)
            },
            **{
                f"/split_policy/split_manifests/{index}/stratification_input_refs/*/node_id": "/causal_graph/nodes/*/node_id"
                for index in range(3)
            },
        }
        if pointer_glob in registry_kinds:
            return registry(registry_kinds[pointer_glob])
        if pointer_glob in local_collections:
            return local(local_collections[pointer_glob])

    raise GateError(
        "GA12-REFERENCE-PATH-COVERAGE",
        f"stable identifier candidate has no exact owner/handler binding: {schema_id}{pointer_glob}",
    )


def derive_reference_path_inventory(snapshot: RepositorySnapshot) -> dict[str, Any]:
    common_path = "schemas/v1.2/scientific-contract-common.schema.json"
    common = strict_json(snapshot.read(common_path), common_path)
    if not isinstance(common, Mapping) or not isinstance(common.get("$defs"), Mapping):
        raise GateError(
            "GA12-REFERENCE-PATH-COVERAGE",
            "scientific common schema definitions are unavailable",
        )
    stable_definition = common["$defs"].get("stableIdentifier", {})
    stable_pattern = (
        stable_definition.get("pattern")
        if isinstance(stable_definition, Mapping)
        else None
    )
    if not isinstance(stable_pattern, str):
        raise GateError(
            "GA12-REFERENCE-PATH-COVERAGE",
            "stable identifier schema pattern is unavailable",
        )
    stable_identifier = re.compile(stable_pattern)
    candidate_rows: list[dict[str, Any]] = []
    lexical_paths: set[tuple[str, str]] = set()
    schema_closed_empty_arrays: set[tuple[str, str]] = set()

    for schema_id, schema_path in sorted(APPLICATION_SCHEMA_PATH_BY_ID.items()):
        application = strict_json(snapshot.read(schema_path), schema_path)
        if not isinstance(application, Mapping) or application.get("$id") != schema_id:
            raise GateError(
                "GA12-REFERENCE-PATH-COVERAGE",
                f"application schema identity differs at {schema_path}",
            )
        candidates: dict[str, tuple[str, str]] = {
            "/schema_id": ("schema_identifier", "schema_reference")
        }
        uninhabitable_array_prefixes: set[str] = set()

        def add_candidate(pointer: str, node_kind: str, classification: str) -> None:
            if any(
                pointer.startswith(f"{prefix}/*")
                for prefix in uninhabitable_array_prefixes
            ):
                return
            previous = candidates.get(pointer)
            current = (node_kind, classification)
            if previous is not None and previous != current:
                raise GateError(
                    "GA12-REFERENCE-PATH-COVERAGE",
                    f"schema path has multiple candidate shapes: {schema_id}{pointer}",
                )
            candidates[pointer] = current

        def reference_target(
            reference: str, current_document: Mapping[str, Any]
        ) -> tuple[Mapping[str, Any], str, str | None]:
            location, separator, fragment = reference.partition("#")
            if separator == "":
                fragment = ""
            if location == "":
                target_document = current_document
            elif location == "common.schema.json":
                target_document = common
            else:
                raise GateError(
                    "GA12-REFERENCE-PATH-COVERAGE",
                    f"application schema reference escapes the closed local graph: {reference}",
                )
            definition_name = (
                fragment.rsplit("/", 1)[-1] if fragment.startswith("/$defs/") else None
            )
            return target_document, fragment, definition_name

        def visit(
            node: Any,
            current_document: Mapping[str, Any],
            pointer: str,
            stack: frozenset[tuple[int, str, str]],
        ) -> None:
            if not isinstance(node, Mapping):
                return
            # Collect sibling allOf refinements before following a shared
            # definition.  A maxItems:0 array has no materialized instance
            # descendants, so its item schema is not an executable reference
            # path and must not be advertised in the handler inventory.
            for branch in node.get("allOf", []):
                if not isinstance(branch, Mapping):
                    continue
                branch_properties = branch.get("properties", {})
                if not isinstance(branch_properties, Mapping):
                    continue
                for property_name, property_schema in branch_properties.items():
                    if (
                        isinstance(property_schema, Mapping)
                        and property_schema.get("maxItems") == 0
                    ):
                        uninhabitable_array_prefixes.add(
                            _instance_pointer_child(pointer, property_name)
                        )
                        schema_closed_empty_arrays.add(
                            (
                                schema_id,
                                _instance_pointer_child(pointer, property_name),
                            )
                        )
            if any(
                pointer.startswith(f"{prefix}/*")
                for prefix in uninhabitable_array_prefixes
            ):
                return
            reference = node.get("$ref")
            if isinstance(reference, str):
                target_document, fragment, definition_name = reference_target(
                    reference, current_document
                )
                if definition_name in REFERENCE_STRUCTURED_DEFINITION_CLASSIFICATIONS:
                    add_candidate(
                        pointer,
                        "structured_reference",
                        REFERENCE_STRUCTURED_DEFINITION_CLASSIFICATIONS[
                            definition_name
                        ],
                    )
                    return
                if definition_name == "stableIdentifier":
                    add_candidate(pointer, "stable_identifier", "stable_identifier")
                    return
                stack_key = (id(target_document), fragment, pointer)
                if stack_key not in stack:
                    visit(
                        _json_schema_fragment(target_document, fragment),
                        target_document,
                        pointer,
                        stack | {stack_key},
                    )

            for keyword in ("allOf", "oneOf", "anyOf"):
                branches = node.get(keyword, [])
                if not isinstance(branches, list):
                    continue
                structured_shapes: set[str] = set()
                for branch in branches:
                    branch_reference = (
                        branch.get("$ref") if isinstance(branch, Mapping) else None
                    )
                    if not isinstance(branch_reference, str):
                        continue
                    _, _, definition_name = reference_target(
                        branch_reference, current_document
                    )
                    if (
                        definition_name
                        in REFERENCE_STRUCTURED_DEFINITION_CLASSIFICATIONS
                    ):
                        structured_shapes.add(
                            REFERENCE_STRUCTURED_DEFINITION_CLASSIFICATIONS[
                                definition_name
                            ]
                        )
                if structured_shapes:
                    if len(structured_shapes) != 1:
                        raise GateError(
                            "GA12-REFERENCE-PATH-COVERAGE",
                            f"schema path combines incompatible structured references: {schema_id}{pointer}",
                        )
                    add_candidate(
                        pointer, "structured_reference", next(iter(structured_shapes))
                    )
                    return

            leaf_name = pointer.rsplit("/", 1)[-1] if pointer else ""
            const_value = node.get("const")
            if (
                isinstance(const_value, str)
                and stable_identifier.fullmatch(const_value)
                and re.search(r"_(?:id|ids|ref|refs)$", leaf_name)
            ):
                add_candidate(pointer, "stable_identifier", "stable_identifier")

            for keyword in ("allOf", "oneOf", "anyOf"):
                for branch in node.get(keyword, []):
                    visit(branch, current_document, pointer, stack)
            properties = node.get("properties", {})
            if isinstance(properties, Mapping):
                for property_name, child in properties.items():
                    child_pointer = _instance_pointer_child(pointer, property_name)
                    if property_name in {
                        "basis_ids",
                        "prior_artifact",
                        "schema_id",
                    } or re.search(r"_(?:id|ids|ref|refs)$", property_name):
                        lexical_paths.add((schema_id, child_pointer))
                    visit(child, current_document, child_pointer, stack)
            if "items" in node:
                visit(node["items"], current_document, f"{pointer}/*", stack)
            prefix_items = node.get("prefixItems", [])
            if isinstance(prefix_items, list):
                for index, child in enumerate(prefix_items):
                    visit(child, current_document, f"{pointer}/{index}", stack)

        visit(application, application, "", frozenset())
        for pointer, (node_kind, classification) in sorted(candidates.items()):
            candidate_rows.append(
                _candidate_reference_binding(
                    schema_id, pointer, node_kind, classification
                )
            )

    candidate_paths = {
        (row["schema_id"], row["pointer_glob"]) for row in candidate_rows
    }
    uncovered_lexical = {
        item
        for item in lexical_paths
        if not any(
            candidate_schema == item[0]
            and (
                candidate_pointer == item[1]
                or candidate_pointer.startswith(f"{item[1]}/")
                or item[1].startswith(f"{candidate_pointer}/")
            )
            for candidate_schema, candidate_pointer in candidate_paths
        )
    }
    allowed_exemptions = {
        (schema_id, pointer): ("closed_release_metadata_const", "schema_const")
        for schema_id in ALL_APPLICATION_SCHEMA_IDS
        for pointer in ("/mission_release_id", "/protocol_release_id")
    }
    allowed_exemptions[
        (
            HUMAN_APPLICATION_SCHEMA_ID,
            "/belief/scoring_contract/scoring_rule_ref",
        )
    ] = ("schema_closed_null_nonreference", "schema_null")
    allowed_exemptions[
        (
            HUMAN_APPLICATION_SCHEMA_ID,
            "/belief/normalization_policy_binding/protocol_release_id",
        )
    ] = ("closed_release_metadata_const", "schema_const")
    for empty_schema_id, empty_pointer in schema_closed_empty_arrays:
        allowed_exemptions[(empty_schema_id, empty_pointer)] = (
            "schema_closed_empty_array_nonreference",
            "schema_max_items_zero",
        )
    if uncovered_lexical != set(allowed_exemptions):
        raise GateError(
            "GA12-REFERENCE-PATH-COVERAGE",
            "lexical identifier/reference paths differ from the exact candidate-or-exemption partition: "
            f"unclassified={sorted(uncovered_lexical - set(allowed_exemptions))}, "
            f"stale_exemptions={sorted(set(allowed_exemptions) - uncovered_lexical)}",
        )
    exemptions = [
        {
            "schema_id": schema_id,
            "pointer_glob": pointer,
            "reason": allowed_exemptions[(schema_id, pointer)][0],
            "enforcement": allowed_exemptions[(schema_id, pointer)][1],
        }
        for schema_id, pointer in sorted(uncovered_lexical)
    ]
    bindings = sorted(
        candidate_rows,
        key=lambda item: (
            item["schema_id"],
            item["pointer_glob"],
            item["candidate_node_kind"],
            item["classification"],
        ),
    )
    binding_bytes = json.dumps(
        bindings, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    exemption_bytes = json.dumps(
        exemptions, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return {
        "derivation": "resolved_draft_2020_12_application_instance_graph",
        "array_path_token": "*",
        "candidate_node_policy": "stable_identifier_or_structured_reference_or_root_schema_id",
        "identity_declarations_explicit": True,
        "binding_count": len(bindings),
        "bindings_sha256": f"sha256:{hashlib.sha256(binding_bytes).hexdigest()}",
        "bindings": bindings,
        "lexical_exemption_count": len(exemptions),
        "lexical_exemptions_sha256": f"sha256:{hashlib.sha256(exemption_bytes).hexdigest()}",
        "non_reference_exemptions": exemptions,
    }


def validate_reference_path_inventory_operands(
    derived: Mapping[str, Any],
    declared: Mapping[str, Any],
    handler_contract: Mapping[str, Any],
) -> None:
    if declared != derived:
        raise GateError(
            "GA12-REFERENCE-PATH-COVERAGE",
            "profile reference inventory must value-exactly equal the independently derived schema graph and handler dispatch inventory",
        )
    expected_handler_contract = reference_path_handler_contract(
        derived.get("bindings", [])
    )
    if handler_contract != expected_handler_contract:
        raise GateError(
            "GA12-REFERENCE-PATH-COVERAGE",
            "the independently frozen science-handler dispatch contract differs from the schema-derived candidate rows",
        )
    path_keys = [(row["schema_id"], row["pointer_glob"]) for row in derived["bindings"]]
    if len(path_keys) != len(set(path_keys)):
        raise GateError(
            "GA12-REFERENCE-PATH-COVERAGE",
            "a schema candidate path has multiple classifications",
        )


def reference_path_handler_contract(
    bindings: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    rows = list(bindings)
    serialized = json.dumps(
        rows, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    handler_counts: dict[str, int] = {}
    classification_counts: dict[str, int] = {}
    for row in rows:
        handler = row.get("handler")
        classification = row.get("classification")
        if not isinstance(handler, str) or not isinstance(classification, str):
            raise GateError(
                "GA12-REFERENCE-PATH-COVERAGE",
                "handler dispatch rows must name a handler and classification",
            )
        handler_counts[handler] = handler_counts.get(handler, 0) + 1
        classification_counts[classification] = (
            classification_counts.get(classification, 0) + 1
        )
    return {
        "contract_version": ARTIFACT_VERSION,
        "binding_count": len(rows),
        "bindings_sha256": f"sha256:{hashlib.sha256(serialized).hexdigest()}",
        "handler_counts": dict(sorted(handler_counts.items())),
        "classification_counts": dict(sorted(classification_counts.items())),
    }


def validate_reference_path_inventory(
    snapshot: RepositorySnapshot,
    declared: Mapping[str, Any],
    handler_contract: Mapping[str, Any],
) -> dict[str, Any]:
    derived = derive_reference_path_inventory(snapshot)
    validate_reference_path_inventory_operands(derived, declared, handler_contract)
    return {
        "binding_count": derived["binding_count"],
        "bindings_sha256": derived["bindings_sha256"],
        "lexical_exemption_count": derived["lexical_exemption_count"],
        "lexical_exemptions_sha256": derived["lexical_exemptions_sha256"],
    }


def validate_scientific_profile(
    snapshot: RepositorySnapshot,
    dependencies: Mapping[str, Any],
    science: Mapping[str, Any],
) -> dict[str, Any]:
    profile = strict_json(
        snapshot.read(SCIENTIFIC_PROFILE_PATH), SCIENTIFIC_PROFILE_PATH
    )
    if not isinstance(profile, dict):
        raise GateError("GA12-SCIENCE-PROFILE", "scientific profile must be an object")
    validator = validator_for_schema(
        snapshot,
        dependencies,
        "schemas/scientific-contract-profile-1.2.schema.json",
        (COMMON_SCHEMA_PATH,),
    )
    errors = schema_error_records(validator, profile)
    if errors:
        first = errors[0]
        raise GateError(
            "GA12-SCIENCE-PROFILE-SCHEMA",
            f"scientific profile failed {first['schema_keyword']} at {first['instance_pointer']}: {first['message']}",
        )
    validate_reference_bytes(
        snapshot,
        profile["prior_profile_binding"],
        "manifests/scientific/harbor-scientific-contract-profile-1.1.0.json",
        "GA12-SCIENCE-PROFILE-BINDING",
    )
    validate_reference_bytes(
        snapshot,
        profile["adversarial_review_binding"],
        "docs/GATE_A_1_1_2_ADVERSARIAL_REVIEW.md",
        "GA12-SCIENCE-PROFILE-BINDING",
    )
    validate_reference_bytes(
        snapshot,
        profile["consistency_review_binding"],
        "docs/GATE_A_1_2_0_CONSISTENCY_REVIEW.md",
        "GA12-SCIENCE-PROFILE-BINDING",
    )
    validate_reference_bytes(
        snapshot,
        profile["definition_registry_binding"],
        DEFINITION_REGISTRY_PATH,
        "GA12-SCIENCE-PROFILE-BINDING",
    )
    schema_bindings = {
        binding["path"]: binding for binding in profile["schema_bindings"]
    }
    if set(schema_bindings) != set(SCIENCE_SCHEMA_PATHS):
        raise GateError(
            "GA12-SCIENCE-PROFILE-SCHEMAS", "profile science schema path set differs"
        )
    for path, binding in schema_bindings.items():
        validate_reference_bytes(
            snapshot, binding, path, "GA12-SCIENCE-PROFILE-SCHEMAS"
        )
        schema = strict_json(snapshot.read(path), path)
        if binding.get("schema_id") != schema.get("$id"):
            raise GateError(
                "GA12-SCIENCE-PROFILE-SCHEMAS", f"profile schema ID differs: {path}"
            )
    fixture_bindings = profile["fixture_bindings"]
    fixture_paths = [binding["path"] for binding in fixture_bindings]
    fixture_ids = [binding["fixture_id"] for binding in fixture_bindings]
    if len(fixture_paths) != len(set(fixture_paths)) or len(fixture_ids) != len(
        set(fixture_ids)
    ):
        raise GateError(
            "GA12-SCIENCE-PROFILE-FIXTURES",
            "profile fixture paths and IDs must be unique",
        )
    expected_paths = {
        path
        for path in snapshot.files
        if path.startswith(SCIENCE_GOOD_PREFIX) and path.endswith(".json")
    } | {item["path"] for item in science["diagnostics"]}
    if set(fixture_paths) != expected_paths:
        raise GateError(
            "GA12-SCIENCE-PROFILE-FIXTURES",
            f"profile fixture set differs: missing={sorted(expected_paths - set(fixture_paths))}, unexpected={sorted(set(fixture_paths) - expected_paths)}",
        )
    diagnostic_by_path = {
        item["path"]: item["rule_id"] for item in science["diagnostics"]
    }
    for binding in fixture_bindings:
        path = binding["path"]
        item = snapshot.files[path]
        if binding["sha256"] != f"sha256:{item.sha256}":
            raise GateError(
                "GA12-SCIENCE-PROFILE-FIXTURES",
                f"profile fixture digest differs: {path}",
            )
        if path in diagnostic_by_path:
            fixture = strict_json(item.data, path)
            if (
                binding["classification"] != "known_bad"
                or binding["expected_rule_id"] != diagnostic_by_path[path]
                or binding["fixture_id"] != fixture.get("fixture_id")
            ):
                raise GateError(
                    "GA12-SCIENCE-PROFILE-FIXTURES",
                    f"known-bad fixture binding differs: {path}",
                )
        elif (
            binding["classification"] != "known_good"
            or binding["expected_rule_id"] is not None
            or GOOD_FIXTURE_PATH_TO_ID.get(path) != binding["fixture_id"]
        ):
            raise GateError(
                "GA12-SCIENCE-PROFILE-FIXTURES",
                f"known-good fixture binding differs: {path}",
            )
    if set(GOOD_FIXTURE_PATH_TO_ID) != {
        path
        for path in snapshot.files
        if path.startswith(SCIENCE_GOOD_PREFIX) and path.endswith(".json")
    }:
        raise GateError(
            "GA12-SCIENCE-PROFILE-FIXTURES",
            "the frozen six-fixture positive science set differs from the snapshot",
        )
    production_rule_list = profile["production_rule_ids"]
    production_rules = set(production_rule_list)
    executed_rules = {item["rule_id"] for item in science["diagnostics"]}
    if production_rules != executed_rules or production_rule_list != sorted(
        executed_rules
    ):
        raise GateError(
            "GA12-SCIENCE-PROFILE-RULES",
            f"profile production rule set/order differs: missing={sorted(executed_rules - production_rules)}, unexpected={sorted(production_rules - executed_rules)}",
        )
    registry = strict_json(
        snapshot.read(DEFINITION_REGISTRY_PATH), DEFINITION_REGISTRY_PATH
    )
    protocol = strict_json(
        snapshot.read(PROTOCOL_MANIFEST_PATH), PROTOCOL_MANIFEST_PATH
    )
    if not isinstance(registry, dict) or not isinstance(protocol, dict):
        raise GateError(
            "GA12-SCIENCE-PROFILE-CONTRACTS", "registry and protocol must be objects"
        )
    registry_contracts = [
        definition["executable_contract"]
        for definition in registry.get("definitions", [])
        if isinstance(definition, dict)
        and isinstance(definition.get("executable_contract"), dict)
    ]
    registry_contract_ids = [
        contract.get("contract_id") for contract in registry_contracts
    ]
    protocol_contract_ids = protocol.get("correction_contract", {}).get(
        "required_executable_contract_ids", []
    )
    profile_contracts = profile["derived_invariant_contracts"]
    profile_contract_ids = [
        item["executable_contract_id"] for item in profile_contracts
    ]
    expected_contract_order = tuple(CONTRACT_ESTIMAND_IDS)
    contract_set_invalid = (
        tuple(registry_contract_ids) != expected_contract_order
        or any(
            contract.get("version") != ARTIFACT_VERSION
            for contract in registry_contracts
        )
        or tuple(protocol_contract_ids) != expected_contract_order
        or tuple(profile_contract_ids) != expected_contract_order
    )
    if contract_set_invalid:
        raise GateError(
            "GA12-SCIENCE-PROFILE-CONTRACTS",
            "profile derived contracts must exactly equal the 11 unique v1.2 registry and protocol correction contracts",
        )
    profile_contract_by_id = {
        item["executable_contract_id"]: item for item in profile_contracts
    }
    if set(profile_contract_by_id) != set(CONTRACT_ESTIMAND_IDS) or any(
        tuple(profile_contract_by_id[contract_id]["protocol_estimand_ids"])
        != estimand_ids
        for contract_id, estimand_ids in CONTRACT_ESTIMAND_IDS.items()
    ):
        raise GateError(
            "GA12-SCIENCE-PROFILE-ESTIMANDS",
            "each derived contract must bind its exact frozen protocol estimand list",
        )
    protocol_estimands = protocol.get("estimands", [])
    protocol_estimand_ids = [
        item.get("estimand_id")
        for item in protocol_estimands
        if isinstance(item, Mapping)
    ]
    registry_estimands = [
        item
        for item in registry.get("definitions", [])
        if isinstance(item, Mapping) and item.get("kind") == "estimand"
    ]
    registry_estimand_ids = [item.get("definition_id") for item in registry_estimands]
    required_estimand_ids = {
        estimand_id
        for estimand_ids in CONTRACT_ESTIMAND_IDS.values()
        for estimand_id in estimand_ids
    }
    estimand_resolution_invalid = (
        len(protocol_estimand_ids) != len(set(protocol_estimand_ids))
        or len(registry_estimand_ids) != len(set(registry_estimand_ids))
        or set(protocol_estimand_ids) != set(registry_estimand_ids)
        or not required_estimand_ids.issubset(set(protocol_estimand_ids))
        or any(
            item.get("version") != ARTIFACT_VERSION
            or item.get("owner_protocol_release_id") != PROTOCOL_RELEASE_ID
            for item in registry_estimands
        )
    )
    if estimand_resolution_invalid:
        raise GateError(
            "GA12-SCIENCE-PROFILE-ESTIMANDS",
            "profile estimands must resolve exactly once in matching protocol and v1.2 registry estimand sets",
        )
    dependencies_by_id = {
        item["executable_contract_id"]: item["depends_on_executable_contract_ids"]
        for item in profile_contracts
    }
    unresolved_dependencies = sorted(
        dependency
        for contract_id, dependencies_for_contract in dependencies_by_id.items()
        for dependency in dependencies_for_contract
        if dependency not in dependencies_by_id or dependency == contract_id
    )
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit_contract(contract_id: str) -> bool:
        if contract_id in visiting:
            return False
        if contract_id in visited:
            return True
        visiting.add(contract_id)
        if any(
            not visit_contract(dependency)
            for dependency in dependencies_by_id[contract_id]
        ):
            return False
        visiting.remove(contract_id)
        visited.add(contract_id)
        return True

    dependency_cycle = bool(unresolved_dependencies) or any(
        not visit_contract(contract_id) for contract_id in sorted(dependencies_by_id)
    )
    derived_rule_union = {
        rule_id for item in profile_contracts for rule_id in item["required_rule_ids"]
    }
    profile_good_ids = {
        binding["fixture_id"]
        for binding in fixture_bindings
        if binding["classification"] == "known_good"
    }
    domain_binding_invalid = any(
        tuple(item["application_schema_ids"])
        != CONTRACT_APPLICATION_SCHEMA_IDS[item["executable_contract_id"]]
        or tuple(item["good_fixture_ids"])
        != CONTRACT_GOOD_FIXTURE_IDS[item["executable_contract_id"]]
        or tuple(item["required_rule_ids"])
        != CONTRACT_RULE_IDS[item["executable_contract_id"]]
        for item in profile_contracts
    )
    cross_cutting_contracts = profile["cross_cutting_rule_contracts"]
    cross_cutting_invalid = len(cross_cutting_contracts) != len(
        CROSS_CUTTING_CONTRACT_BINDINGS
    )
    for item, expected in zip(
        cross_cutting_contracts, CROSS_CUTTING_CONTRACT_BINDINGS, strict=True
    ):
        contract_id, application_schema_ids, good_fixture_ids, required_rule_ids = (
            expected
        )
        if (
            item["contract_id"] != contract_id
            or tuple(item["application_schema_ids"]) != application_schema_ids
            or tuple(item["good_fixture_ids"]) != good_fixture_ids
            or tuple(item["required_rule_ids"]) != required_rule_ids
        ):
            cross_cutting_invalid = True
    cross_cutting_rule_union = {
        rule_id
        for item in cross_cutting_contracts
        for rule_id in item["required_rule_ids"]
    }
    classifier_contract = profile["reference_resolution_contract"]
    science_module = load_science_module(snapshot)
    handler_contract = science_module.get("REFERENCE_PATH_HANDLER_CONTRACT")
    if not isinstance(handler_contract, Mapping):
        raise GateError(
            "GA12-REFERENCE-PATH-COVERAGE",
            "science module reference handler contract is unavailable",
        )
    reference_path_summary = validate_reference_path_inventory(
        snapshot,
        classifier_contract["application_path_inventory"],
        handler_contract,
    )
    classifiers = classifier_contract["classifiers"]
    classifier_ids = [item["classifier_id"] for item in classifiers]
    classifier_shapes = [item["shape"] for item in classifiers]
    expected_classifier_owner_and_rules = {
        "rule_reference": (
            "protocol_definition_registry",
            ("GA-REFERENCE-KIND", "GA-REFERENCE-VERSION"),
        ),
        "versioned_reference": (
            "protocol_definition_registry",
            ("GA-REFERENCE-KIND", "GA-REFERENCE-VERSION"),
        ),
        "actor_reference": (
            "protocol_definition_registry",
            ("GA-ACTOR-REFERENCE-TYPE", "GA-REFERENCE-VERSION"),
        ),
        "schema_reference": (
            "schema_registry",
            ("GA-SCHEMA-REFERENCE-RESOLUTION",),
        ),
        "artifact_reference": (
            "repository_snapshot",
            ("GA-ARTIFACT-REFERENCE-RESOLUTION",),
        ),
        "document_local_reference": (
            "application_document",
            ("GA-DOCUMENT-LOCAL-REFERENCE-RESOLUTION",),
        ),
        "explicit_evidence_gap": (
            "explicit_unavailable",
            ("GA-EVIDENCE-GAP-REFERENCE-DISPOSITION",),
        ),
        "registry_bare_identifier": (
            "protocol_definition_registry",
            ("GA-REGISTRY-BARE-IDENTIFIER-RESOLUTION",),
        ),
        "document_local_identifier": (
            "application_document",
            ("GA-DOCUMENT-LOCAL-REFERENCE-RESOLUTION",),
        ),
    }
    reference_classifier_invalid = (
        len(classifier_ids) != len(set(classifier_ids))
        or len(classifier_shapes) != len(set(classifier_shapes))
        or set(classifier_shapes) != set(expected_classifier_owner_and_rules)
        or any(
            (item["owner"], tuple(item["failure_rule_ids"]))
            != expected_classifier_owner_and_rules[item["shape"]]
            for item in classifiers
        )
    )
    contract_binding_invalid = (
        dependency_cycle
        or tuple(profile["application_schema_ids"]) != ALL_APPLICATION_SCHEMA_IDS
        or profile_good_ids != set(ALL_GOOD_FIXTURE_IDS)
        or domain_binding_invalid
        or cross_cutting_invalid
        or bool(derived_rule_union & cross_cutting_rule_union)
        or derived_rule_union | cross_cutting_rule_union != production_rules
        or reference_classifier_invalid
    )
    if contract_binding_invalid:
        raise GateError(
            "GA12-SCIENCE-PROFILE-CONTRACTS",
            "derived and cross-cutting contracts must be exact, acyclic, disjoint, classifier-bound, and together cover all production rules and goods",
        )
    execution = profile["execution_integrity_contract"]
    expected_execution = {
        "launcher_binding": LAUNCHER_PATH,
        "tool_binding": TOOL_PATH,
        "science_module_binding": SCIENCE_MODULE_PATH,
        "toolchain_lock_binding": LOCK_PATH,
    }
    for key, path in expected_execution.items():
        validate_reference_bytes(
            snapshot, execution[key], path, "GA12-SCIENCE-PROFILE-EXECUTION"
        )
    return {
        "profile_id": profile["profile_id"],
        "schema_binding_count": len(schema_bindings),
        "fixture_binding_count": len(fixture_bindings),
        "production_rule_count": len(production_rules),
        "derived_contract_count": len(profile_contracts),
        "cross_cutting_contract_count": len(cross_cutting_contracts),
        "reference_path_binding_count": reference_path_summary["binding_count"],
        "reference_path_bindings_sha256": reference_path_summary["bindings_sha256"],
        "reference_path_lexical_exemption_count": reference_path_summary[
            "lexical_exemption_count"
        ],
        "reference_path_lexical_exemptions_sha256": reference_path_summary[
            "lexical_exemptions_sha256"
        ],
    }


def predecessor_fixture_catalog_contract() -> list[Mapping[str, Any]]:
    raw = run_git(
        [
            "show",
            f"{PREDECESSOR_RECEIPT_COMMIT}:{PREDECESSOR_FIXTURE_CATALOG_PATH}",
        ]
    )
    if (
        len(raw) != PREDECESSOR_FIXTURE_CATALOG_BYTE_SIZE
        or hashlib.sha256(raw).hexdigest() != PREDECESSOR_FIXTURE_CATALOG_SHA256
    ):
        raise GateError(
            "GA12-FIXTURE-CATALOG-HISTORICAL-BINDING",
            "retained predecessor fixture catalog bytes differ from the frozen binding",
        )
    predecessor = strict_json(
        raw, f"{PREDECESSOR_RECEIPT_COMMIT}:{PREDECESSOR_FIXTURE_CATALOG_PATH}"
    )
    if not isinstance(predecessor, Mapping) or not isinstance(
        predecessor.get("fixtures"), list
    ):
        raise GateError(
            "GA12-FIXTURE-CATALOG-HISTORICAL-SHAPE",
            "retained predecessor fixture catalog must contain a fixture array",
        )
    rows = predecessor["fixtures"]
    if len(rows) != PREDECESSOR_FIXTURE_CATALOG_ROW_COUNT:
        raise GateError(
            "GA12-FIXTURE-CATALOG-HISTORICAL-COUNT",
            "retained predecessor fixture catalog row count differs",
        )
    expected_keys = {
        "fixture_id",
        "path",
        "classification",
        "expected_primary_rule_id",
    }
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise GateError(
                "GA12-FIXTURE-CATALOG-HISTORICAL-SHAPE",
                f"retained predecessor fixture row {index} is not an object",
            )
        require_exact_keys(
            row, expected_keys, f"predecessor fixture catalog row {index}"
        )
        if (
            not isinstance(row.get("fixture_id"), str)
            or not isinstance(row.get("path"), str)
            or row["path"].startswith("fixtures/v1.2/")
            or row.get("classification") not in {"known_good", "known_bad"}
            or (
                row.get("classification") == "known_good"
                and row.get("expected_primary_rule_id") is not None
            )
            or (
                row.get("classification") == "known_bad"
                and not isinstance(row.get("expected_primary_rule_id"), str)
            )
        ):
            raise GateError(
                "GA12-FIXTURE-CATALOG-HISTORICAL-SHAPE",
                f"retained predecessor fixture row {index} has invalid identity or classification",
            )
    validate_fixture_catalog_uniqueness(predecessor)
    return rows


def catalog_fixture_record(
    snapshot: RepositorySnapshot, path: str
) -> Mapping[str, Any]:
    if path not in snapshot.files:
        raise GateError(
            "GA12-FIXTURE-CATALOG-PATH", f"catalog fixture path is absent: {path}"
        )
    record = strict_json(snapshot.read(path), path)
    if not isinstance(record, Mapping) or not isinstance(record.get("schema_id"), str):
        raise GateError(
            "GA12-FIXTURE-CATALOG-RECORD-SHAPE",
            f"catalog fixture must be an object with schema_id: {path}",
        )
    return record


def catalog_attestation(snapshot: RepositorySnapshot, path: str) -> tuple[str, int]:
    item = snapshot.files[path]
    return f"sha256:{item.sha256}", item.size


def historical_catalog_row(
    snapshot: RepositorySnapshot,
    predecessor_row: Mapping[str, Any],
) -> dict[str, Any]:
    path = str(predecessor_row["path"])
    record = catalog_fixture_record(snapshot, path)
    frozen_path_binding = path.startswith("fixtures/v1.1/good/")
    if (
        not frozen_path_binding
        and record.get("fixture_id") != predecessor_row["fixture_id"]
    ):
        raise GateError(
            "GA12-FIXTURE-CATALOG-IDENTITY",
            f"historical embedded fixture identity differs from predecessor catalog: {path}",
        )
    digest, byte_size = catalog_attestation(snapshot, path)
    return {
        "fixture_id": predecessor_row["fixture_id"],
        "path": path,
        "classification": predecessor_row["classification"],
        "fixture_family": "retained_historical",
        "replay_mode": "retained_not_replayed",
        "fixture_identity_source": (
            "frozen_path_binding" if frozen_path_binding else "embedded_fixture_id"
        ),
        "fixture_schema_id": record["schema_id"],
        "target_schema_id": None,
        "sha256": digest,
        "byte_size": byte_size,
        "expected_primary_rule_id": predecessor_row["expected_primary_rule_id"],
    }


def current_catalog_row(
    snapshot: RepositorySnapshot,
    path: str,
    validated_identity: tuple[str, str, str | None],
) -> dict[str, Any]:
    fixture_id, classification, expected_rule = validated_identity
    record = catalog_fixture_record(snapshot, path)
    fixture_schema_id = record["schema_id"]
    name = PurePosixPath(path).name
    publication_schema_id = (
        "https://schemas.reiyah.invalid/gate-a/1.2.0/"
        "publication-event-fixture.schema.json"
    )
    transport_schema_id = (
        "https://schemas.reiyah.invalid/gate-a/1.2.0/"
        "transport-observation-fixture.schema.json"
    )

    if path.startswith("fixtures/v1.2/good/"):
        expected_fixture_id = f"reiyah.fixture.good.v12.{PurePosixPath(path).stem}"
        derived = (
            "known_good",
            "scientific_contract",
            "production_accept",
            "frozen_path_binding",
            fixture_schema_id,
            None,
        )
        if fixture_id != expected_fixture_id:
            raise GateError(
                "GA12-FIXTURE-CATALOG-IDENTITY",
                f"scientific positive fixture path binding differs: {path}",
            )
    elif path.startswith("fixtures/v1.2/governance-good/"):
        derived = (
            "known_good",
            "publication_governance",
            "governance_accept",
            "embedded_fixture_id",
            record.get("target_schema_id"),
            None,
        )
    elif path == "fixtures/v1.2/governance/publication-event-synthetic-baseline.json":
        derived = (
            "known_good",
            "publication_governance",
            "governance_accept",
            "embedded_fixture_id",
            publication_schema_id,
            None,
        )
    elif (
        path == "fixtures/v1.2/governance/transport-observation-synthetic-baseline.json"
    ):
        derived = (
            "known_good",
            "transport_governance",
            "governance_accept",
            "embedded_fixture_id",
            transport_schema_id,
            None,
        )
    elif path.startswith("fixtures/v1.2/known-bad/") and name.startswith(
        "validator-security-"
    ):
        derived = (
            "known_bad",
            "validator_security",
            "validator_security_singleton_reject",
            "embedded_fixture_id",
            None,
            record.get("expected_diagnostic"),
        )
    elif path.startswith("fixtures/v1.2/known-bad/") and name.startswith(
        "governance-transport-"
    ):
        replay = record.get("expected_replay")
        if not isinstance(replay, Mapping):
            raise GateError(
                "GA12-FIXTURE-CATALOG-REPLAY-METADATA",
                f"transport fixture lacks expected_replay: {path}",
            )
        layer = replay.get("rejection_layer")
        derived = (
            "known_bad",
            "transport_governance",
            (
                "governance_semantic_singleton_reject"
                if layer == "semantic"
                else "governance_canonical_schema_reject"
                if layer == "structural_schema"
                else None
            ),
            "embedded_fixture_id",
            record.get("target_schema_id"),
            record.get("expected_diagnostic"),
        )
    elif path.startswith("fixtures/v1.2/known-bad/") and name.startswith("governance-"):
        replay = record.get("expected_replay")
        if not isinstance(replay, Mapping):
            raise GateError(
                "GA12-FIXTURE-CATALOG-REPLAY-METADATA",
                f"publication fixture lacks expected_replay: {path}",
            )
        layer = replay.get("rejection_layer")
        derived = (
            "known_bad",
            "publication_governance",
            (
                "governance_semantic_singleton_reject"
                if layer == "semantic"
                else "governance_canonical_schema_reject"
                if layer == "structural_schema"
                else None
            ),
            "embedded_fixture_id",
            replay.get("target_schema_id"),
            record.get("expected_diagnostic"),
        )
    elif path.startswith("fixtures/v1.2/known-bad/"):
        failure = record.get("expected_failure")
        if not isinstance(failure, Mapping):
            raise GateError(
                "GA12-FIXTURE-CATALOG-REPLAY-METADATA",
                f"scientific mutation fixture lacks expected_failure: {path}",
            )
        keyword = failure.get("schema_keyword")
        derived = (
            "known_bad",
            "scientific_contract",
            (
                "semantic_singleton_reject"
                if keyword == "semantic"
                else "canonical_schema_reject"
            ),
            "embedded_fixture_id",
            record.get("target_schema_id"),
            failure.get("rule_id"),
        )
    else:
        raise GateError(
            "GA12-FIXTURE-CATALOG-V12-PATH",
            f"current fixture path is outside the closed fixture layout: {path}",
        )

    (
        derived_classification,
        family,
        replay_mode,
        identity_source,
        target_schema_id,
        derived_rule,
    ) = derived
    if (
        classification != derived_classification
        or expected_rule != derived_rule
        or replay_mode is None
        or not isinstance(target_schema_id, str)
        and family != "validator_security"
    ):
        raise GateError(
            "GA12-FIXTURE-CATALOG-REPLAY-METADATA",
            f"production replay metadata and fixture declaration differ: {path}",
        )
    if (
        identity_source == "embedded_fixture_id"
        and record.get("fixture_id") != fixture_id
    ):
        raise GateError(
            "GA12-FIXTURE-CATALOG-IDENTITY",
            f"embedded fixture identity differs from production replay identity: {path}",
        )
    digest, byte_size = catalog_attestation(snapshot, path)
    return {
        "fixture_id": fixture_id,
        "path": path,
        "classification": classification,
        "fixture_family": family,
        "replay_mode": replay_mode,
        "fixture_identity_source": identity_source,
        "fixture_schema_id": fixture_schema_id,
        "target_schema_id": target_schema_id,
        "sha256": digest,
        "byte_size": byte_size,
        "expected_primary_rule_id": expected_rule,
    }


CATALOG_ROW_FIELD_DIAGNOSTICS = MappingProxyType(
    {
        "sha256": "GA12-FIXTURE-CATALOG-BYTE-DIGEST",
        "byte_size": "GA12-FIXTURE-CATALOG-BYTE-SIZE",
        "fixture_schema_id": "GA12-FIXTURE-CATALOG-FIXTURE-SCHEMA",
        "target_schema_id": "GA12-FIXTURE-CATALOG-TARGET-SCHEMA",
        "fixture_identity_source": "GA12-FIXTURE-CATALOG-IDENTITY-SOURCE",
        "replay_mode": "GA12-FIXTURE-CATALOG-REPLAY-MODE",
        "expected_primary_rule_id": ("GA12-FIXTURE-CATALOG-EXPECTED-PRIMARY-RULE"),
    }
)


def validate_fixture_catalog_rows(
    observed_rows: Sequence[Mapping[str, Any]],
    expected_rows: Sequence[Mapping[str, Any]],
) -> None:
    """Exact catalog-to-snapshot reconciliation shared by production and canaries."""

    observed_paths = [row.get("path") for row in observed_rows]
    expected_paths = [row.get("path") for row in expected_rows]
    observed_path_set = set(observed_paths)
    expected_path_set = set(expected_paths)
    missing_paths = sorted(expected_path_set - observed_path_set)
    unexpected_paths = sorted(observed_path_set - expected_path_set)
    if missing_paths:
        raise GateError(
            "GA12-FIXTURE-CATALOG-MISSING-ROW",
            f"fixture catalog omits expected rows: {missing_paths}",
        )
    if unexpected_paths:
        raise GateError(
            "GA12-FIXTURE-CATALOG-UNEXPECTED-ROW",
            f"fixture catalog contains unexpected rows: {unexpected_paths}",
        )
    if observed_paths != expected_paths:
        raise GateError(
            "GA12-FIXTURE-CATALOG-ORDER",
            "fixture catalog order must equal predecessor row order followed by "
            "UTF-8 ordered current rows",
        )
    for index, (observed, expected) in enumerate(
        zip(observed_rows, expected_rows, strict=True)
    ):
        if observed == expected:
            continue
        differing = sorted(
            key
            for key in set(observed) | set(expected)
            if observed.get(key) != expected.get(key)
        )
        diagnostic = (
            CATALOG_ROW_FIELD_DIAGNOSTICS[differing[0]]
            if len(differing) == 1 and differing[0] in CATALOG_ROW_FIELD_DIAGNOSTICS
            else "GA12-FIXTURE-CATALOG-ROW"
        )
        raise GateError(
            diagnostic,
            f"fixture catalog row {index} differs at {differing}: "
            f"{expected.get('path')}",
        )


def validate_fixture_catalog(
    snapshot: RepositorySnapshot,
    dependencies: Mapping[str, Any],
    expected_v12: Mapping[str, tuple[str, str, str | None]],
) -> dict[str, Any]:
    catalog_path = "fixtures/fixture-catalog.json"
    catalog = strict_json(snapshot.read(catalog_path), catalog_path)
    if not isinstance(catalog, dict):
        raise GateError("GA12-FIXTURE-CATALOG", "fixture catalog must be an object")
    validator = validator_for_schema(
        snapshot,
        dependencies,
        "schemas/fixture-catalog-1.2.schema.json",
        (COMMON_SCHEMA_PATH,),
    )
    errors = schema_error_records(validator, catalog)
    if errors:
        first = errors[0]
        raise GateError(
            "GA12-FIXTURE-CATALOG-SCHEMA",
            f"fixture catalog failed {first['schema_keyword']} at {first['instance_pointer']}: {first['message']}",
        )
    validate_fixture_catalog_uniqueness(catalog)

    allowed_current_parents = {
        "fixtures/v1.2/good",
        "fixtures/v1.2/governance",
        "fixtures/v1.2/governance-good",
        "fixtures/v1.2/known-bad",
    }
    current_files = {
        path
        for path in snapshot.files
        if path.startswith("fixtures/v1.2/")
        and path.endswith(".json")
        and str(PurePosixPath(path).parent) in allowed_current_parents
    }
    unclassified_current = sorted(
        path
        for path in snapshot.files
        if path.startswith("fixtures/v1.2/")
        and path.endswith(".json")
        and path not in current_files
    )
    if unclassified_current:
        raise GateError(
            "GA12-FIXTURE-CATALOG-V12-PATH",
            f"current JSON fixtures are outside the closed fixture layout: {unclassified_current}",
        )
    if set(expected_v12) != current_files:
        raise GateError(
            "GA12-FIXTURE-CATALOG-V12",
            "production-replayed and filesystem current fixture sets differ: "
            f"missing={sorted(current_files - set(expected_v12))}, "
            f"unexpected={sorted(set(expected_v12) - current_files)}",
        )

    predecessor_rows = predecessor_fixture_catalog_contract()
    expected_rows = [
        historical_catalog_row(snapshot, predecessor_row)
        for predecessor_row in predecessor_rows
    ]
    expected_rows.extend(
        current_catalog_row(snapshot, path, expected_v12[path])
        for path in sorted(expected_v12, key=lambda value: value.encode("utf-8"))
    )
    entries = catalog["fixtures"]
    validate_fixture_catalog_rows(entries, expected_rows)

    family_count_accumulator: dict[str, int] = {}
    replay_mode_count_accumulator: dict[str, int] = {}
    for row in entries:
        family = row["fixture_family"]
        replay_mode = row["replay_mode"]
        family_count_accumulator[family] = family_count_accumulator.get(family, 0) + 1
        replay_mode_count_accumulator[replay_mode] = (
            replay_mode_count_accumulator.get(replay_mode, 0) + 1
        )
    family_counts = dict(sorted(family_count_accumulator.items()))
    replay_mode_counts = dict(sorted(replay_mode_count_accumulator.items()))
    current_rows = [
        row for row in entries if row["replay_mode"] != "retained_not_replayed"
    ]
    historical_paths = [
        row["path"] for row in entries if row["replay_mode"] == "retained_not_replayed"
    ]
    current_paths = [row["path"] for row in current_rows]
    return {
        "catalog_fixture_count": len(entries),
        "retained_historical_fixture_count": len(historical_paths),
        "current_replay_fixture_count": len(current_rows),
        "v12_fixture_count": len(current_rows),
        "current_replay_known_good_count": sum(
            row["classification"] == "known_good" for row in current_rows
        ),
        "current_replay_known_bad_count": sum(
            row["classification"] == "known_bad" for row in current_rows
        ),
        "historical_fixture_set_sha256": artifact_set_digest(
            snapshot, historical_paths
        ),
        "current_fixture_set_sha256": artifact_set_digest(snapshot, current_paths),
        "family_counts": family_counts,
        "replay_mode_counts": replay_mode_counts,
    }


def validate_fixture_catalog_uniqueness(catalog: Mapping[str, Any]) -> None:
    entries = catalog.get("fixtures")
    if not isinstance(entries, list) or any(
        not isinstance(entry, Mapping) for entry in entries
    ):
        raise GateError(
            "GA12-FIXTURE-CATALOG-SHAPE", "fixture catalog entries must be objects"
        )
    fixture_ids = [entry.get("fixture_id") for entry in entries]
    paths = [entry.get("path") for entry in entries]
    if any(not isinstance(fixture_id, str) for fixture_id in fixture_ids) or len(
        fixture_ids
    ) != len(set(fixture_ids)):
        raise GateError(
            "GA12-FIXTURE-CATALOG-ID-UNIQUE",
            "fixture catalog fixture_id values must be globally unique before indexing",
        )
    if any(not isinstance(path, str) for path in paths) or len(paths) != len(
        set(paths)
    ):
        raise GateError(
            "GA12-FIXTURE-CATALOG-PATH-UNIQUE",
            "fixture catalog paths must be globally unique before filesystem reconciliation",
        )


def validate_definition_registry_uniqueness(registry: Mapping[str, Any]) -> None:
    definitions = registry.get("definitions")
    reference_contracts = registry.get("reference_kind_contracts")
    if not isinstance(definitions, list) or not isinstance(reference_contracts, list):
        raise GateError(
            "GA12-SCIENCE-REGISTRY-SHAPE", "registry collections must be arrays"
        )
    definition_ids = [
        definition.get("definition_id")
        for definition in definitions
        if isinstance(definition, Mapping)
    ]
    if len(definition_ids) != len(definitions) or len(definition_ids) != len(
        set(definition_ids)
    ):
        raise GateError(
            "GA12-REGISTRY-DEFINITION-ID-UNIQUE",
            "definition_id values must be present and globally unique before resolution",
        )
    reference_kind_ids = [
        contract.get("reference_kind_id")
        for contract in reference_contracts
        if isinstance(contract, Mapping)
    ]
    if len(reference_kind_ids) != len(reference_contracts) or len(
        reference_kind_ids
    ) != len(set(reference_kind_ids)):
        raise GateError(
            "GA12-REGISTRY-REFERENCE-KIND-ID-UNIQUE",
            "reference_kind_id values must be present and globally unique before resolution",
        )
    executable_contract_ids = [
        definition["executable_contract"].get("contract_id")
        for definition in definitions
        if isinstance(definition, Mapping)
        and isinstance(definition.get("executable_contract"), Mapping)
    ]
    if any(
        not isinstance(contract_id, str) for contract_id in executable_contract_ids
    ) or len(executable_contract_ids) != len(set(executable_contract_ids)):
        raise GateError(
            "GA12-REGISTRY-EXECUTABLE-CONTRACT-ID-UNIQUE",
            "executable contract_id values must be present and globally unique before contract resolution",
        )
    definitions_by_id = {
        definition["definition_id"]: definition
        for definition in definitions
        if isinstance(definition, Mapping)
        and isinstance(definition.get("definition_id"), str)
    }
    for definition in definitions:
        if not isinstance(definition, Mapping) or definition.get("kind") not in {
            "state_space",
            "action_space",
            "group_set",
            "analysis_unit_set",
            "trajectory_set",
        }:
            continue
        member_ids = definition.get("member_ids")
        required_member_kind = {
            "state_space": "state",
            "action_space": "action",
            "group_set": "group",
            "analysis_unit_set": "analysis_unit",
            "trajectory_set": "trajectory",
        }[definition["kind"]]
        members_valid = (
            isinstance(member_ids, list)
            and bool(member_ids)
            and all(isinstance(member_id, str) for member_id in member_ids)
            and len(member_ids) == len(set(member_ids))
        )
        if members_valid:
            for member_id in member_ids:
                member = definitions_by_id.get(member_id)
                if (
                    not isinstance(member, Mapping)
                    or member.get("kind") != required_member_kind
                    or member.get("version") != ARTIFACT_VERSION
                    or member.get("owner_protocol_release_id") != PROTOCOL_RELEASE_ID
                ):
                    members_valid = False
                    break
        if not members_valid:
            raise GateError(
                "GA-REGISTRY-BARE-IDENTIFIER-RESOLUTION",
                f"{definition.get('definition_id')} members must be unique and exact-resolve to {required_member_kind} definitions owned by {PROTOCOL_RELEASE_ID}",
            )
    for definition in definitions:
        if not isinstance(definition, Mapping) or definition.get("kind") not in {
            "trajectory_set",
            "policy_table",
        }:
            continue
        bound_artifact_ids = definition.get("bound_artifact_ids")
        authority_valid = (
            isinstance(bound_artifact_ids, list)
            and bool(bound_artifact_ids)
            and all(isinstance(item, str) for item in bound_artifact_ids)
            and len(bound_artifact_ids) == len(set(bound_artifact_ids))
            and definition.get("synthetic_fixture_only") is True
            and definition.get("evidence_eligible") is False
            and definition.get("real_data_resolution_authorized") is False
        )
        contents_valid = True
        if definition["kind"] == "policy_table":
            policy_ref = definition.get("policy_ref")
            policy_definition = (
                definitions_by_id.get(policy_ref.get("record_id"))
                if isinstance(policy_ref, Mapping)
                else None
            )
            action_space = definitions_by_id.get(definition.get("action_space_id"))
            action_ids = definition.get("action_ids")
            action_definitions_valid = (
                isinstance(action_ids, list)
                and bool(action_ids)
                and all(isinstance(item, str) for item in action_ids)
                and len(action_ids) == len(set(action_ids))
                and all(
                    isinstance(definitions_by_id.get(action_id), Mapping)
                    and definitions_by_id[action_id].get("kind") == "action"
                    and definitions_by_id[action_id].get("version") == ARTIFACT_VERSION
                    and definitions_by_id[action_id].get("owner_protocol_release_id")
                    == PROTOCOL_RELEASE_ID
                    for action_id in action_ids
                )
            )
            rows = definition.get("history_probability_rows")
            history_ids: list[object] = []
            rows_valid = isinstance(rows, list) and bool(rows)
            for row in rows if isinstance(rows, list) else []:
                history_ids.append(row.get("history_id"))
                probabilities = row.get("probabilities")
                rows_valid = rows_valid and (
                    isinstance(row.get("history_id"), str)
                    and isinstance(probabilities, list)
                    and [item.get("action_id") for item in probabilities] == action_ids
                    and all(
                        isinstance(item.get("probability"), (int, float))
                        and not isinstance(item.get("probability"), bool)
                        for item in probabilities
                    )
                )
            rows_valid = rows_valid and len(history_ids) == len(set(history_ids))
            contents_valid = (
                isinstance(policy_definition, Mapping)
                and policy_definition.get("kind") == "record_identity"
                and policy_definition.get("record_kind") == "reiyah.kind.policy"
                and policy_definition.get("version") == ARTIFACT_VERSION
                and policy_definition.get("owner_protocol_release_id")
                == PROTOCOL_RELEASE_ID
                and policy_ref.get("record_kind") == "reiyah.kind.policy"
                and policy_ref.get("version") == ARTIFACT_VERSION
                and definition.get("policy_role") in {"behavior", "target"}
                and isinstance(action_space, Mapping)
                and action_space.get("kind") == "action_space"
                and action_space.get("version") == ARTIFACT_VERSION
                and action_space.get("owner_protocol_release_id") == PROTOCOL_RELEASE_ID
                and action_space.get("member_ids") == action_ids
                and action_definitions_valid
                and rows_valid
            )
        if not authority_valid or not contents_valid:
            raise GateError(
                "GA-REGISTRY-BARE-IDENTIFIER-RESOLUTION",
                f"{definition.get('definition_id')} must be a unique, protocol-owned, synthetic-only OPE manifest whose typed members exact-resolve and confer no real-data or evidence authority",
            )
    for definition in definitions:
        if (
            not isinstance(definition, Mapping)
            or definition.get("kind") != "opportunity_set"
        ):
            continue
        bound_artifact_ids = definition.get("bound_artifact_ids")
        member_ids = definition.get("member_ids")
        rows = definition.get("opportunity_contracts")
        object_ref = definition.get("object_ref")
        window = definition.get("opportunity_window")
        authority_valid = (
            isinstance(bound_artifact_ids, list)
            and bool(bound_artifact_ids)
            and all(isinstance(item, str) for item in bound_artifact_ids)
            and len(bound_artifact_ids) == len(set(bound_artifact_ids))
            and definition.get("synthetic_fixture_only") is True
            and definition.get("evidence_eligible") is False
            and definition.get("real_data_resolution_authorized") is False
        )

        def resolved_definition(
            reference: object,
            *,
            required_kind: str,
            required_record_kind: str | None = None,
        ) -> Mapping[str, Any] | None:
            if not isinstance(reference, Mapping):
                return None
            resolved = definitions_by_id.get(reference.get("record_id"))
            valid = (
                isinstance(resolved, Mapping)
                and resolved.get("kind") == required_kind
                and resolved.get("version") == ARTIFACT_VERSION
                and resolved.get("owner_protocol_release_id") == PROTOCOL_RELEASE_ID
                and reference.get("version") == ARTIFACT_VERSION
            )
            if required_record_kind is not None:
                valid = (
                    valid
                    and resolved.get("record_kind") == required_record_kind
                    and reference.get("record_kind") == required_record_kind
                )
            return resolved if valid else None

        object_definition = resolved_definition(
            object_ref,
            required_kind="record_identity",
            required_record_kind="reiyah.kind.vehicle_object",
        )
        clock_definition = (
            definitions_by_id.get(window.get("clock_id"))
            if isinstance(window, Mapping)
            else None
        )
        window_definition = (
            definitions_by_id.get(window.get("window_id"))
            if isinstance(window, Mapping)
            else None
        )
        try:
            opened_at = datetime.fromisoformat(window["opened_at"][:-1] + "+00:00")
            closed_at = datetime.fromisoformat(window["closed_at"][:-1] + "+00:00")
        except (KeyError, TypeError, ValueError):
            opened_at = None
            closed_at = None
        contents_valid = (
            isinstance(member_ids, list)
            and all(isinstance(item, str) for item in member_ids)
            and len(member_ids) == len(set(member_ids))
            and isinstance(rows, list)
            and [row.get("opportunity_id") for row in rows if isinstance(row, Mapping)]
            == member_ids
            and len(rows) == len(member_ids)
            and isinstance(object_definition, Mapping)
            and isinstance(clock_definition, Mapping)
            and clock_definition.get("kind") == "clock"
            and clock_definition.get("version") == ARTIFACT_VERSION
            and clock_definition.get("owner_protocol_release_id") == PROTOCOL_RELEASE_ID
            and isinstance(window_definition, Mapping)
            and window_definition.get("kind") == "window"
            and window_definition.get("version") == ARTIFACT_VERSION
            and window_definition.get("owner_protocol_release_id")
            == PROTOCOL_RELEASE_ID
            and opened_at is not None
            and closed_at is not None
            and opened_at <= closed_at
        )
        previous_observed_at: datetime | None = None
        for row in rows if isinstance(rows, list) else []:
            if not isinstance(row, Mapping):
                contents_valid = False
                continue
            human = row.get("human_channel")
            automation = row.get("automation_channel")
            warning = row.get("warning")
            fallback = row.get("fallback")
            human_definition = resolved_definition(
                human.get("channel_ref") if isinstance(human, Mapping) else None,
                required_kind="record_identity",
                required_record_kind="reiyah.kind.observation_channel",
            )
            automation_definition = resolved_definition(
                automation.get("channel_ref")
                if isinstance(automation, Mapping)
                else None,
                required_kind="record_identity",
                required_record_kind="reiyah.kind.observation_channel",
            )

            def rule_reference_valid(value: object) -> bool:
                if not isinstance(value, Mapping):
                    return False
                rule = definitions_by_id.get(value.get("rule_id"))
                return (
                    isinstance(rule, Mapping)
                    and rule.get("kind") == "inclusion_rule"
                    and rule.get("version") == ARTIFACT_VERSION
                    and rule.get("owner_protocol_release_id") == PROTOCOL_RELEASE_ID
                    and value.get("rule_kind") == "reiyah.kind.event_rule"
                    and value.get("version") == ARTIFACT_VERSION
                )

            occurred = row.get("occurred_at")
            occurred_value = (
                occurred.get("value")
                if isinstance(occurred, Mapping) and occurred.get("state") == "observed"
                else None
            )
            try:
                occurred_at = (
                    datetime.fromisoformat(occurred_value[:-1] + "+00:00")
                    if isinstance(occurred_value, str)
                    else None
                )
            except ValueError:
                occurred_at = None
            if occurred_at is not None:
                contents_valid = (
                    contents_valid
                    and opened_at is not None
                    and closed_at is not None
                    and opened_at <= occurred_at <= closed_at
                    and (
                        previous_observed_at is None
                        or previous_observed_at < occurred_at
                    )
                )
                previous_observed_at = occurred_at

            def observed_or_nonobserved(
                value: object, allowed_observed_values: set[str]
            ) -> bool:
                return isinstance(value, Mapping) and (
                    (
                        value.get("state") == "observed"
                        and value.get("value") in allowed_observed_values
                    )
                    or value.get("state")
                    in {
                        "missing",
                        "unmeasured",
                        "out_of_distribution",
                        "sensor_invalid",
                        "abstained",
                    }
                )

            contents_valid = contents_valid and (
                row.get("object_ref") == object_ref
                and isinstance(window, Mapping)
                and row.get("clock_id") == window.get("clock_id")
                and row.get("window_id") == window.get("window_id")
                and isinstance(human_definition, Mapping)
                and isinstance(automation_definition, Mapping)
                and human.get("channel_ref") != automation.get("channel_ref")
                and rule_reference_valid(
                    warning.get("rule_ref") if isinstance(warning, Mapping) else None
                )
                and rule_reference_valid(
                    fallback.get("rule_ref") if isinstance(fallback, Mapping) else None
                )
                and observed_or_nonobserved(
                    row.get("reference_state"), {"opportunity_present"}
                )
                and observed_or_nonobserved(row.get("reference_validity"), {"valid"})
                and observed_or_nonobserved(
                    human.get("outcome") if isinstance(human, Mapping) else None,
                    {"miss", "detected"},
                )
                and observed_or_nonobserved(
                    automation.get("outcome")
                    if isinstance(automation, Mapping)
                    else None,
                    {"miss", "detected"},
                )
                and observed_or_nonobserved(
                    warning.get("outcome") if isinstance(warning, Mapping) else None,
                    {"issued", "not_issued"},
                )
                and observed_or_nonobserved(
                    fallback.get("outcome") if isinstance(fallback, Mapping) else None,
                    {"activated", "not_activated"},
                )
            )
        if not authority_valid or not contents_valid:
            raise GateError(
                "GA-REGISTRY-BARE-IDENTIFIER-RESOLUTION",
                f"{definition.get('definition_id')} must be a unique, protocol-owned, synthetic-only opportunity manifest whose complete ordered typed rows exact-resolve and confer no real-data or evidence authority",
            )
    for definition in definitions:
        if not isinstance(definition, Mapping) or definition.get("kind") not in {
            "capability_set",
            "recovery_event_manifest",
        }:
            continue
        bound_artifact_ids = definition.get("bound_artifact_ids")
        authority_valid = (
            isinstance(bound_artifact_ids, list)
            and bool(bound_artifact_ids)
            and all(isinstance(item, str) for item in bound_artifact_ids)
            and len(bound_artifact_ids) == len(set(bound_artifact_ids))
            and definition.get("synthetic_fixture_only") is True
            and definition.get("evidence_eligible") is False
            and definition.get("real_data_resolution_authorized") is False
        )
        if definition["kind"] == "capability_set":
            contracts = definition.get("capability_contracts")
            identities: list[tuple[object, object]] = []
            contents_valid = isinstance(contracts, list) and bool(contracts)
            for row in contracts if isinstance(contracts, list) else []:
                capability = definitions_by_id.get(row.get("capability_id"))
                dimension = definitions_by_id.get(row.get("dimension_id"))
                criterion = definitions_by_id.get(row.get("criterion_rule_id"))
                identities.append((row.get("capability_id"), row.get("dimension_id")))
                if (
                    not isinstance(capability, Mapping)
                    or capability.get("kind") != "capability"
                    or not isinstance(dimension, Mapping)
                    or dimension.get("kind") != "dimension"
                    or not isinstance(criterion, Mapping)
                    or criterion.get("definition_id")
                    != "reiyah.rule.capability_threshold"
                    or criterion.get("kind") != "decision_rule"
                    or any(
                        item.get("version") != ARTIFACT_VERSION
                        or item.get("owner_protocol_release_id") != PROTOCOL_RELEASE_ID
                        for item in (capability, dimension, criterion)
                    )
                ):
                    contents_valid = False
            contents_valid = contents_valid and len(identities) == len(set(identities))
        else:
            contracts = definition.get("event_contracts")
            event_ids: list[object] = []
            contents_valid = isinstance(contracts, list)
            for row in contracts if isinstance(contracts, list) else []:
                event_type = definitions_by_id.get(row.get("event_type"))
                event_ids.append(row.get("event_id"))
                if (
                    not isinstance(event_type, Mapping)
                    or event_type.get("kind") != "event_type"
                    or event_type.get("version") != ARTIFACT_VERSION
                    or event_type.get("owner_protocol_release_id")
                    != PROTOCOL_RELEASE_ID
                ):
                    contents_valid = False
            complete = definition.get("window_observation_complete")
            contents_valid = (
                contents_valid
                and len(event_ids) == len(set(event_ids))
                and (
                    (
                        complete is True
                        and isinstance(definition.get("complete_through"), str)
                    )
                    or (
                        complete is False and definition.get("complete_through") is None
                    )
                )
            )
        if not authority_valid or not contents_valid:
            raise GateError(
                "GA-REGISTRY-BARE-IDENTIFIER-RESOLUTION",
                f"{definition.get('definition_id')} must be a unique, protocol-owned, synthetic-only manifest whose typed members exact-resolve and confer no real-data or evidence authority",
            )


def _matrix_leaf_rows(
    value: Any,
    tokens: tuple[str, ...] = (),
) -> list[tuple[tuple[str, ...], Any]]:
    rows: list[tuple[tuple[str, ...], Any]] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not tokens and key in EXECUTABLE_CONTRACT_MATRIX_METADATA_KEYS:
                continue
            rows.extend(_matrix_leaf_rows(child, tokens + (str(key),)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            rows.extend(_matrix_leaf_rows(child, tokens + (str(index),)))
    else:
        rows.append((tokens, value))
    return rows


def _matrix_pointer(tokens: Sequence[str]) -> str:
    pointer = ""
    for token in tokens:
        pointer = _instance_pointer_child(pointer, token)
    return pointer


def _matrix_case_slug(tokens: Sequence[str]) -> str:
    return "-".join(
        re.sub(r"[^a-z0-9]+", "-", token.replace("_", "-").lower()).strip("-")
        for token in tokens
    )


def derive_executable_contract_operand_cases(
    registry: Mapping[str, Any],
) -> list[dict[str, Any]]:
    definitions = registry.get("definitions")
    if not isinstance(definitions, list):
        raise GateError(
            "GA12-EXECUTABLE-CONTRACT-OPERAND-COVERAGE",
            "definition registry lacks an ordered definitions array",
        )
    replacement_overrides: Mapping[tuple[str, str], Any] = MappingProxyType(
        {
            ("ope", "normalization_tolerance"): 2e-12,
            ("ope", "relative_tolerance"): 1,
            ("ope", "minimum_effective_sample_size"): 3,
            ("causal", "requires_pre_treatment"): False,
            ("causal", "requires_observed"): False,
            ("causal", "acyclicity_sufficient"): True,
            ("readiness", "safety_critical_compensation_allowed"): True,
            ("transfer", "minimum_observed_count"): 2,
            ("transfer", "arithmetic_absolute_tolerance"): 2e-12,
            ("transfer", "relative_tolerance"): 1,
            ("conformal", "guarantee_separate_from_empirical_coverage"): False,
            ("conformal", "arithmetic_absolute_tolerance"): 2e-12,
            ("conformal", "relative_tolerance"): 1,
            ("ood", "disjoint_required"): False,
            ("ood", "exhaustive_required"): False,
            ("ood", "derived_rates_required"): False,
            ("ood", "reference_detector_axes_disjoint"): False,
            ("worst", "minimum_count"): 31,
            ("worst", "minimum_coverage"): 0.81,
            ("worst", "minimum_effective_sample_size"): 21,
            ("worst", "maximum_interval_width"): 0.26,
            ("worst", "arithmetic_absolute_tolerance"): 2e-12,
            ("worst", "relative_tolerance"): 1,
            ("worst", "tie_absolute_tolerance"): 2e-12,
        }
    )
    semantic_scalar_rows = {
        ("ope", "normalization_tolerance"),
        ("worst", "minimum_count"),
        ("worst", "minimum_coverage"),
        ("worst", "minimum_effective_sample_size"),
        ("worst", "maximum_interval_width"),
    }
    aggregate_const_arrays = {
        "prohibited_roles",
        "analysis_unit_member_ids",
        "event_type_role_bindings",
        "required_conditions",
        "joint_axis_cells",
        "common_opportunity_cells",
        "opportunity_set_ids",
    }
    aggregate_const_objects = {
        "analysis_unit_set_ref",
        "automation_channel_ref",
        "behavior_policy_ref",
        "calibration_set_ref",
        "capability_criterion_rule_ref",
        "censoring_policy_ref",
        "competing_event_policy_ref",
        "fallback_rule_ref",
        "human_channel_ref",
        "object_ref",
        "opportunity_rule_ref",
        "recovery_criterion_ref",
        "test_set_ref",
        "target_policy_ref",
        "warning_rule_ref",
    }
    rows: list[dict[str, Any]] = []
    observed_contract_ids: list[str] = []
    for definition_index, definition in enumerate(definitions):
        if not isinstance(definition, Mapping):
            continue
        contract = definition.get("executable_contract")
        if not isinstance(contract, Mapping):
            continue
        contract_id = contract.get("contract_id")
        definition_id = definition.get("definition_id")
        target = EXECUTABLE_CONTRACT_MATRIX_TARGETS.get(contract_id)
        expectation = EXECUTABLE_CONTRACT_MATRIX_EXPECTATIONS.get(definition_id)
        if (
            not isinstance(contract_id, str)
            or not isinstance(definition_id, str)
            or target is None
            or expectation is None
        ):
            raise GateError(
                "GA12-EXECUTABLE-CONTRACT-OPERAND-COVERAGE",
                f"executable contract lacks an independent matrix dispatch: {contract_id}",
            )
        observed_contract_ids.append(contract_id)
        short_name, target_good_path, target_schema_id = target
        states = contract.get("states")
        for relative_tokens, _value in _matrix_leaf_rows(contract):
            relative_path = "/".join(relative_tokens)
            pointer_tokens = (
                "definitions",
                str(definition_index),
                "executable_contract",
                *relative_tokens,
            )
            leaf_pointer = _matrix_pointer(pointer_tokens)
            is_ood_state = short_name == "ood" and relative_tokens[0] == "states"
            is_semantic = (
                is_ood_state
                or (
                    short_name,
                    relative_path,
                )
                in semantic_scalar_rows
            )
            if is_ood_state:
                if not isinstance(states, list) or len(states) != 6:
                    raise GateError(
                        "GA12-EXECUTABLE-CONTRACT-OPERAND-COVERAGE",
                        "OOD state contract must contain the exact six ordered states",
                    )
                state_index = int(relative_tokens[1])
                adjacent_index = (state_index + 1) % len(states)
                mutations = [
                    {
                        "operation": "replace",
                        "json_pointer": _matrix_pointer(
                            (
                                "definitions",
                                str(definition_index),
                                "executable_contract",
                                "states",
                                str(state_index),
                            )
                        ),
                        "value": states[adjacent_index],
                    },
                    {
                        "operation": "replace",
                        "json_pointer": _matrix_pointer(
                            (
                                "definitions",
                                str(definition_index),
                                "executable_contract",
                                "states",
                                str(adjacent_index),
                            )
                        ),
                        "value": states[state_index],
                    },
                ]
            else:
                mutations = [
                    {
                        "operation": "replace",
                        "json_pointer": leaf_pointer,
                        "value": replacement_overrides.get(
                            (short_name, relative_path),
                            "__mutated_contract_operand__",
                        ),
                    }
                ]
            registry_primary: dict[str, str] | None = None
            if not is_semantic:
                if (
                    short_name == "ope"
                    and relative_path == "minimum_effective_sample_size"
                ):
                    primary_pointer = _matrix_pointer(pointer_tokens[:-1])
                    primary_keyword = "oneOf"
                elif (
                    relative_tokens[0]
                    in aggregate_const_arrays | aggregate_const_objects
                ):
                    primary_pointer = _matrix_pointer(pointer_tokens[:4])
                    primary_keyword = "const"
                else:
                    primary_pointer = leaf_pointer
                    primary_keyword = "const"
                registry_primary = {
                    "schema_keyword": primary_keyword,
                    "instance_pointer": primary_pointer,
                }
            rows.append(
                {
                    "case_id": (
                        "reiyah.fixture.validator-security.eco."
                        f"{short_name}.{_matrix_case_slug(relative_tokens)}@1.2.0"
                    ),
                    "contract_id": contract_id,
                    "definition_id": definition_id,
                    "registry_leaf_pointer": leaf_pointer,
                    "mutations": mutations,
                    "target_good_path": target_good_path,
                    "target_schema_id": target_schema_id,
                    "declared_registry_layer": (
                        "semantic" if is_semantic else "structural"
                    ),
                    "expected_registry_primary": registry_primary,
                    "expected_semantic_singleton": dict(expectation),
                }
            )
    if observed_contract_ids != list(EXECUTABLE_CONTRACT_MATRIX_TARGETS):
        raise GateError(
            "GA12-EXECUTABLE-CONTRACT-OPERAND-COVERAGE",
            "registry executable contract order differs from matrix dispatch",
        )
    expected_counts = [25, 26, 8, 21, 18, 14, 20, 10, 9, 34, 4]
    observed_counts = [
        sum(row["contract_id"] == contract_id for row in rows)
        for contract_id in observed_contract_ids
    ]
    if (
        len(rows) != 189
        or len({row["case_id"] for row in rows}) != 189
        or observed_counts != expected_counts
        or sum(row["declared_registry_layer"] == "structural" for row in rows) != 178
        or sum(row["declared_registry_layer"] == "semantic" for row in rows) != 11
    ):
        raise GateError(
            "GA12-EXECUTABLE-CONTRACT-OPERAND-COVERAGE",
            "derived executable contract leaf partition differs from 189=178+11",
        )
    return rows


def _require_executable_contract_matrix_cases(
    derived: Sequence[Mapping[str, Any]],
    declared: object,
) -> None:
    if not isinstance(declared, list) or declared != list(derived):
        raise GateError(
            "GA12-EXECUTABLE-CONTRACT-OPERAND-COVERAGE",
            "declared executable contract cases differ from independent registry derivation",
        )


def validate_executable_contract_operand_matrix(
    snapshot: RepositorySnapshot,
    dependencies: Mapping[str, Any],
    probe: Mapping[str, Any],
) -> dict[str, Any]:
    if (
        probe.get("registry_path") != DEFINITION_REGISTRY_PATH
        or probe.get("registry_schema_path")
        != "schemas/protocol-definition-registry-1.2.schema.json"
        or probe.get("metadata_leaf_names")
        != list(EXECUTABLE_CONTRACT_MATRIX_METADATA_KEYS)
        or probe.get("derivation_order")
        != "definition_array_then_depth_first_insertion_order_nonmetadata_leaves"
    ):
        raise GateError(
            "GA12-EXECUTABLE-CONTRACT-OPERAND-COVERAGE",
            "matrix derivation operands differ from the closed contract",
        )
    pristine_registry = strict_json(
        snapshot.read(DEFINITION_REGISTRY_PATH), DEFINITION_REGISTRY_PATH
    )
    protocol = strict_json(
        snapshot.read(PROTOCOL_MANIFEST_PATH), PROTOCOL_MANIFEST_PATH
    )
    if not isinstance(pristine_registry, dict) or not isinstance(protocol, dict):
        raise GateError(
            "GA12-EXECUTABLE-CONTRACT-OPERAND-COVERAGE",
            "matrix registry/protocol operands must be objects",
        )
    derived = derive_executable_contract_operand_cases(pristine_registry)
    _require_executable_contract_matrix_cases(derived, probe.get("cases"))

    registry_validator = validator_for_schema(
        snapshot,
        dependencies,
        "schemas/protocol-definition-registry-1.2.schema.json",
        (COMMON_SCHEMA_PATH,),
    )
    target_validators = {
        schema_id: validator_for_schema(
            snapshot,
            dependencies,
            APPLICATION_SCHEMA_PATH_BY_ID[schema_id],
            SCIENCE_SCHEMA_PATHS,
        )
        for schema_id in {
            HUMAN_APPLICATION_SCHEMA_ID,
            JOINT_APPLICATION_SCHEMA_ID,
            OPE_APPLICATION_SCHEMA_ID,
            STUDY_APPLICATION_SCHEMA_ID,
        }
    }
    science = load_science_module(snapshot)
    reference_inventory = derive_reference_path_inventory(snapshot)
    handler_contract = science["REFERENCE_PATH_HANDLER_CONTRACT"]
    artifact_inventory = science_artifact_inventory(snapshot)
    lifecycle_policy = protocol.get("lifecycle_transition_policy")
    if not isinstance(lifecycle_policy, Mapping):
        raise GateError(
            "GA12-EXECUTABLE-CONTRACT-OPERAND-COVERAGE",
            "matrix protocol lacks lifecycle policy",
        )
    target_goods: dict[str, Mapping[str, Any]] = {}
    result_rows: list[dict[str, Any]] = []
    for case in derived:
        target_path = case["target_good_path"]
        target = target_goods.get(target_path)
        if target is None:
            value = strict_json(snapshot.read(target_path), target_path)
            if not isinstance(value, dict):
                raise GateError(
                    "GA12-EXECUTABLE-CONTRACT-OPERAND-COVERAGE",
                    f"matrix target good is not an object: {target_path}",
                )
            target_errors = schema_error_records(
                target_validators[case["target_schema_id"]], value
            )
            if target_errors:
                raise GateError(
                    "GA12-EXECUTABLE-CONTRACT-OPERAND-COVERAGE",
                    f"matrix target good is schema-invalid: {target_path}",
                )
            target = value
            target_goods[target_path] = target
        mutated_registry: Any = pristine_registry
        for mutation in case["mutations"]:
            mutated_registry = replace_json_pointer(mutated_registry, mutation)
        registry_errors = schema_error_records(registry_validator, mutated_registry)
        expected_primary = case["expected_registry_primary"]
        layer = case["declared_registry_layer"]
        if layer == "structural":
            observed_primary = registry_errors[0] if registry_errors else None
            if (
                observed_primary is None
                or {
                    "schema_keyword": observed_primary["schema_keyword"],
                    "instance_pointer": observed_primary["instance_pointer"],
                }
                != expected_primary
            ):
                raise GateError(
                    "GA12-EXECUTABLE-CONTRACT-OPERAND-COVERAGE",
                    f"matrix structural primary differs: {case['case_id']}",
                )
        elif registry_errors:
            raise GateError(
                "GA12-EXECUTABLE-CONTRACT-OPERAND-COVERAGE",
                f"matrix semantic case is registry-schema-invalid: {case['case_id']}",
            )
        try:
            semantic_errors = science["semantic_violations"](
                target,
                lifecycle_policy,
                mutated_registry,
                protocol,
                {
                    "artifact_inventory": artifact_inventory,
                    "instance_path": target_path,
                    "expected_schema_id": case["target_schema_id"],
                    "reference_path_bindings": reference_inventory["bindings"],
                    "reference_path_handler_contract": handler_contract,
                },
            )
        except science["ScienceContractError"] as exc:
            raise GateError(
                "GA12-EXECUTABLE-CONTRACT-OPERAND-COVERAGE",
                f"matrix semantic execution failed: {case['case_id']}: {exc}",
            ) from exc
        if semantic_errors != [case["expected_semantic_singleton"]]:
            raise GateError(
                "GA12-EXECUTABLE-CONTRACT-OPERAND-COVERAGE",
                f"matrix direct semantic singleton differs: {case['case_id']}",
            )
        result_rows.append(
            {
                "case_id": case["case_id"],
                "registry_layer": layer,
                "registry_primary_matched": True,
                "semantic_singleton_matched": True,
            }
        )

    canary = probe.get("coverage_canary")
    if canary != {"operation": "remove", "json_pointer": "/cases/188"}:
        raise GateError(
            "GA12-EXECUTABLE-CONTRACT-OPERAND-COVERAGE",
            "matrix coverage canary differs from the closed final-row removal",
        )
    canary_cases = copy.deepcopy(probe["cases"])
    canary_cases.pop()
    diagnostic = captured_gate_diagnostic(
        lambda: _require_executable_contract_matrix_cases(derived, canary_cases)
    )
    if diagnostic != "GA12-EXECUTABLE-CONTRACT-OPERAND-COVERAGE":
        raise GateError(
            "GA12-EXECUTABLE-CONTRACT-OPERAND-COVERAGE",
            "matrix missing-row canary did not reach the coverage resolver",
        )
    return {
        "case_count": len(result_rows),
        "structural_registry_case_count": sum(
            row["registry_layer"] == "structural" for row in result_rows
        ),
        "semantic_registry_case_count": sum(
            row["registry_layer"] == "semantic" for row in result_rows
        ),
        "direct_semantic_singleton_count": len(result_rows),
        "case_set_sha256": canonical_record_digest(derived),
        "result_set_sha256": canonical_record_digest(result_rows),
        "coverage_canary_diagnostic": diagnostic,
    }


def _derive_ope_registry_manifest_binding_cases(
    registry: Mapping[str, Any], target_artifact_id: str
) -> list[dict[str, Any]]:
    definitions = registry.get("definitions")
    if not isinstance(definitions, list):
        raise GateError(
            "GA12-OPE-REGISTRY-MANIFEST-CANARY-COVERAGE",
            "OPE registry-manifest cases require the ordered definition array",
        )
    definition_indexes: dict[str, int] = {}
    for index, definition in enumerate(definitions):
        if not isinstance(definition, Mapping) or not isinstance(
            definition.get("definition_id"), str
        ):
            continue
        definition_id = definition["definition_id"]
        if definition_id in definition_indexes:
            raise GateError(
                "GA12-OPE-REGISTRY-MANIFEST-CANARY-COVERAGE",
                f"OPE registry-manifest case target is duplicated: {definition_id}",
            )
        definition_indexes[definition_id] = index

    def definition_index(definition_id: str) -> int:
        index = definition_indexes.get(definition_id)
        if index is None:
            raise GateError(
                "GA12-OPE-REGISTRY-MANIFEST-CANARY-COVERAGE",
                f"OPE registry-manifest case target is absent: {definition_id}",
            )
        return index

    def pointer_value(pointer: str) -> Any:
        value: Any = registry
        for token in pointer[1:].split("/"):
            value = value[int(token)] if isinstance(value, list) else value[token]
        return copy.deepcopy(value)

    def replace(pointer: str, value: Any) -> dict[str, Any]:
        return {
            "operation": "replace",
            "json_pointer": pointer,
            "value": copy.deepcopy(value),
        }

    def remove(pointer: str) -> dict[str, Any]:
        return {"operation": "remove", "json_pointer": pointer}

    def swap(pointer: str, left: int, right: int) -> list[dict[str, Any]]:
        return [
            replace(f"{pointer}/{left}", pointer_value(f"{pointer}/{right}")),
            replace(f"{pointer}/{right}", pointer_value(f"{pointer}/{left}")),
        ]

    policy_reason = (
        "Every behavior and target distribution must exact-bind the "
        "artifact-bound protocol-owned synthetic policy table selected for its "
        "role and history; the table is static resolver evidence, not an executed "
        "policy."
    )
    trajectory_reason = (
        "The retained trajectory identities must exact-bind the complete ordered "
        "artifact-bound protocol-owned synthetic trajectory manifest; the manifest "
        "is static resolver evidence, not a real dataset population."
    )
    rows: list[dict[str, Any]] = []
    for role, definition_id, alternate_policy_id in (
        (
            "behavior",
            "reiyah.policy-table.synthetic-behavior-base",
            "reiyah.policy.synthetic_target",
        ),
        (
            "target",
            "reiyah.policy-table.synthetic-target-base",
            "reiyah.policy.synthetic_behavior",
        ),
    ):
        index = definition_index(definition_id)
        definition = definitions[index]
        if not isinstance(definition, Mapping):
            raise GateError(
                "GA12-OPE-REGISTRY-MANIFEST-CANARY-COVERAGE",
                f"OPE policy-table case target is not an object: {definition_id}",
            )
        prefix = f"/definitions/{index}"
        bound_artifact_ids = definition.get("bound_artifact_ids")
        history_rows = definition.get("history_probability_rows")
        if (
            not isinstance(bound_artifact_ids, list)
            or target_artifact_id not in bound_artifact_ids
            or not isinstance(history_rows, list)
            or len(history_rows) != 4
        ):
            raise GateError(
                "GA12-OPE-REGISTRY-MANIFEST-CANARY-COVERAGE",
                f"OPE policy-table case preconditions differ: {definition_id}",
            )
        distribution_pointer = f"/trajectories/0/steps/0/{role}_distribution"
        reference_pointer = f"/{role}_policy/policy_table_ref"
        role_cases: tuple[tuple[str, list[dict[str, Any]], str], ...] = (
            (
                "role",
                [
                    replace(
                        f"{prefix}/policy_role",
                        "target" if role == "behavior" else "behavior",
                    )
                ],
                reference_pointer,
            ),
            (
                "policy-ref",
                [replace(f"{prefix}/policy_ref/record_id", alternate_policy_id)],
                reference_pointer,
            ),
            (
                "action-space",
                [
                    replace(
                        f"{prefix}/action_space_id",
                        "reiyah.action_space.synthetic_acknowledgement",
                    )
                ],
                reference_pointer,
            ),
            (
                "action-order",
                swap(f"{prefix}/action_ids", 0, 1)
                + [
                    mutation
                    for row_index in range(4)
                    for mutation in swap(
                        f"{prefix}/history_probability_rows/{row_index}/probabilities",
                        0,
                        1,
                    )
                ],
                distribution_pointer,
            ),
            (
                "bound-artifact",
                [
                    remove(
                        f"{prefix}/bound_artifact_ids/"
                        f"{bound_artifact_ids.index(target_artifact_id)}"
                    )
                ],
                reference_pointer,
            ),
            (
                "history-order",
                swap(f"{prefix}/history_probability_rows", 0, 1),
                distribution_pointer,
            ),
            (
                "history-duplicate",
                [
                    replace(
                        f"{prefix}/history_probability_rows/1/history_id",
                        history_rows[0]["history_id"],
                    )
                ],
                f"/trajectories/0/steps/1/{role}_distribution",
            ),
            (
                "probability-content",
                [
                    replace(
                        f"{prefix}/history_probability_rows/0/probabilities/0/probability",
                        0.4,
                    ),
                    replace(
                        f"{prefix}/history_probability_rows/0/probabilities/1/probability",
                        0.6,
                    ),
                ],
                distribution_pointer,
            ),
        )
        for predicate_id, mutations, pointer in role_cases:
            rows.append(
                {
                    "case_id": (
                        f"reiyah.validator-canary.ope-registry.{role}-{predicate_id}"
                    ),
                    "family": "policy_table",
                    "definition_id": definition_id,
                    "predicate_id": predicate_id,
                    "mutations": mutations,
                    "expected_semantic_singleton": {
                        "rule_id": "GA-OPE-POLICY-TABLE-BINDING",
                        "instance_pointer": pointer,
                        "reason": policy_reason,
                    },
                }
            )

    trajectory_definition_id = "reiyah.trajectory-set.synthetic-ope"
    trajectory_index = definition_index(trajectory_definition_id)
    trajectory_definition = definitions[trajectory_index]
    if not isinstance(trajectory_definition, Mapping):
        raise GateError(
            "GA12-OPE-REGISTRY-MANIFEST-CANARY-COVERAGE",
            "OPE trajectory-manifest case target is not an object",
        )
    trajectory_prefix = f"/definitions/{trajectory_index}"
    trajectory_bound_ids = trajectory_definition.get("bound_artifact_ids")
    if (
        not isinstance(trajectory_bound_ids, list)
        or target_artifact_id not in trajectory_bound_ids
    ):
        raise GateError(
            "GA12-OPE-REGISTRY-MANIFEST-CANARY-COVERAGE",
            "OPE trajectory-manifest bound-artifact precondition differs",
        )
    trajectory_cases: tuple[tuple[str, list[dict[str, Any]]], ...] = (
        (
            "member-order",
            swap(f"{trajectory_prefix}/member_ids", 0, 1),
        ),
        (
            "member-substitution",
            [
                replace(
                    f"{trajectory_prefix}/member_ids/1",
                    "reiyah.trajectory.synthetic_c",
                )
            ],
        ),
        (
            "bound-artifact",
            [
                remove(
                    f"{trajectory_prefix}/bound_artifact_ids/"
                    f"{trajectory_bound_ids.index(target_artifact_id)}"
                )
            ],
        ),
    )
    for predicate_id, mutations in trajectory_cases:
        rows.append(
            {
                "case_id": (
                    f"reiyah.validator-canary.ope-registry.trajectory-{predicate_id}"
                ),
                "family": "trajectory_manifest",
                "definition_id": trajectory_definition_id,
                "predicate_id": predicate_id,
                "mutations": mutations,
                "expected_semantic_singleton": {
                    "rule_id": "GA-OPE-TRAJECTORY-MANIFEST-BINDING",
                    "instance_pointer": "/trajectories",
                    "reason": trajectory_reason,
                },
            }
        )
    return rows


def _require_ope_registry_manifest_case_contract(
    cases: object,
) -> None:
    valid = (
        isinstance(cases, list)
        and tuple(
            case.get("case_id") if isinstance(case, Mapping) else None for case in cases
        )
        == OPE_REGISTRY_MANIFEST_CASE_IDS
        and canonical_record_digest(cases) == OPE_REGISTRY_MANIFEST_CASE_SET_SHA256
    )
    if not valid:
        raise GateError(
            "GA12-OPE-REGISTRY-MANIFEST-CANARY-COVERAGE",
            "derived OPE registry-manifest case map differs from the frozen exact matrix",
        )


def validate_ope_registry_manifest_binding_matrix(
    snapshot: RepositorySnapshot,
    dependencies: Mapping[str, Any],
) -> dict[str, Any]:
    registry = strict_json(
        snapshot.read(DEFINITION_REGISTRY_PATH), DEFINITION_REGISTRY_PATH
    )
    protocol = strict_json(
        snapshot.read(PROTOCOL_MANIFEST_PATH), PROTOCOL_MANIFEST_PATH
    )
    target_path = "fixtures/v1.2/good/sequential-off-policy-evaluation.json"
    target = strict_json(snapshot.read(target_path), target_path)
    if (
        not isinstance(registry, dict)
        or not isinstance(protocol, dict)
        or not isinstance(target, dict)
        or target.get("schema_id") != OPE_APPLICATION_SCHEMA_ID
        or not isinstance(target.get("artifact_id"), str)
    ):
        raise GateError(
            "GA12-OPE-REGISTRY-MANIFEST-CANARY-COVERAGE",
            "OPE registry-manifest matrix inputs do not bind the exact registry, protocol, and target good",
        )
    cases = _derive_ope_registry_manifest_binding_cases(registry, target["artifact_id"])
    _require_ope_registry_manifest_case_contract(cases)

    registry_validator = validator_for_schema(
        snapshot,
        dependencies,
        "schemas/protocol-definition-registry-1.2.schema.json",
        (COMMON_SCHEMA_PATH,),
    )
    target_validator = validator_for_schema(
        snapshot,
        dependencies,
        APPLICATION_SCHEMA_PATH_BY_ID[OPE_APPLICATION_SCHEMA_ID],
        SCIENCE_SCHEMA_PATHS,
    )
    if schema_error_records(target_validator, target):
        raise GateError(
            "GA12-OPE-REGISTRY-MANIFEST-CANARY-COVERAGE",
            "OPE registry-manifest matrix target good is target-schema-invalid",
        )
    science = load_science_module(snapshot)
    reference_inventory = derive_reference_path_inventory(snapshot)
    handler_contract = science["REFERENCE_PATH_HANDLER_CONTRACT"]
    artifact_inventory = science_artifact_inventory(snapshot)
    lifecycle_policy = protocol.get("lifecycle_transition_policy")
    if not isinstance(lifecycle_policy, Mapping):
        raise GateError(
            "GA12-OPE-REGISTRY-MANIFEST-CANARY-COVERAGE",
            "OPE registry-manifest matrix protocol lacks lifecycle policy",
        )

    result_rows: list[dict[str, Any]] = []
    for case in cases:
        try:
            mutated_registry = science["apply_mutations"](registry, case["mutations"])
        except science["ScienceContractError"] as exc:
            raise GateError(
                "GA12-OPE-REGISTRY-MANIFEST-CANARY-COVERAGE",
                f"OPE registry-manifest mutation failed: {case['case_id']}: {exc}",
            ) from exc
        registry_errors = schema_error_records(registry_validator, mutated_registry)
        if registry_errors:
            first = registry_errors[0]
            raise GateError(
                "GA12-OPE-REGISTRY-MANIFEST-CANARY-COVERAGE",
                f"OPE registry-manifest case is registry-schema-invalid: "
                f"{case['case_id']}: {first['schema_keyword']}@"
                f"{first['instance_pointer']}",
            )
        try:
            semantic_errors = science["semantic_violations"](
                target,
                lifecycle_policy,
                mutated_registry,
                protocol,
                {
                    "artifact_inventory": artifact_inventory,
                    "instance_path": target_path,
                    "expected_schema_id": OPE_APPLICATION_SCHEMA_ID,
                    "reference_path_bindings": reference_inventory["bindings"],
                    "reference_path_handler_contract": handler_contract,
                },
            )
        except science["ScienceContractError"] as exc:
            raise GateError(
                "GA12-OPE-REGISTRY-MANIFEST-CANARY-COVERAGE",
                f"OPE registry-manifest semantic execution failed: "
                f"{case['case_id']}: {exc}",
            ) from exc
        if semantic_errors != [case["expected_semantic_singleton"]]:
            raise GateError(
                "GA12-OPE-REGISTRY-MANIFEST-CANARY-COVERAGE",
                f"OPE registry-manifest case did not reach its exact production "
                f"singleton: {case['case_id']}: {semantic_errors}",
            )
        result_rows.append(
            {
                "case_id": case["case_id"],
                "family": case["family"],
                "predicate_id": case["predicate_id"],
                "semantic_singleton_matched": True,
            }
        )

    unknown_case_canary = copy.deepcopy(cases)
    unknown_case_canary.append(
        {
            "case_id": "reiyah.validator-canary.ope-registry.unknown",
            "family": "unknown",
            "definition_id": "reiyah.invalid",
            "predicate_id": "unknown",
            "mutations": [],
            "expected_semantic_singleton": {},
        }
    )
    missing_case_diagnostics = tuple(
        captured_gate_diagnostic(
            lambda missing_index=missing_index: (
                _require_ope_registry_manifest_case_contract(
                    [
                        copy.deepcopy(case)
                        for case_index, case in enumerate(cases)
                        if case_index != missing_index
                    ]
                )
            )
        )
        for missing_index in range(len(cases))
    )
    unknown_case_diagnostic = captured_gate_diagnostic(
        lambda: _require_ope_registry_manifest_case_contract(unknown_case_canary)
    )
    if (
        set(missing_case_diagnostics) != {"GA12-OPE-REGISTRY-MANIFEST-CANARY-COVERAGE"}
        or unknown_case_diagnostic != "GA12-OPE-REGISTRY-MANIFEST-CANARY-COVERAGE"
    ):
        raise GateError(
            "GA12-OPE-REGISTRY-MANIFEST-CANARY-COVERAGE",
            "OPE registry-manifest exhaustive remove-one/unknown case canaries did not fail closed",
        )
    return {
        "case_count": len(result_rows),
        "policy_table_case_count": sum(
            row["family"] == "policy_table" for row in result_rows
        ),
        "trajectory_manifest_case_count": sum(
            row["family"] == "trajectory_manifest" for row in result_rows
        ),
        "semantic_singleton_count": len(result_rows),
        "case_set_sha256": canonical_record_digest(cases),
        "result_set_sha256": canonical_record_digest(result_rows),
        "coverage_canary_diagnostic": ("GA12-OPE-REGISTRY-MANIFEST-CANARY-COVERAGE"),
    }


def _derive_joint_opportunity_registry_manifest_binding_cases(
    registry: Mapping[str, Any], target_artifact_id: str
) -> list[dict[str, Any]]:
    definitions = registry.get("definitions")
    if not isinstance(definitions, list):
        raise GateError(
            "GA12-JOINT-OPPORTUNITY-REGISTRY-MANIFEST-CANARY-COVERAGE",
            "joint opportunity registry-manifest cases require the ordered definition array",
        )
    matches = [
        (index, definition)
        for index, definition in enumerate(definitions)
        if isinstance(definition, Mapping)
        and definition.get("definition_id")
        == "reiyah.opportunity-set.synthetic-joint-observed"
    ]
    if len(matches) != 1:
        raise GateError(
            "GA12-JOINT-OPPORTUNITY-REGISTRY-MANIFEST-CANARY-COVERAGE",
            "observed synthetic opportunity manifest must resolve exactly once",
        )
    definition_index, definition = matches[0]
    prefix = f"/definitions/{definition_index}"
    member_pointer = f"{prefix}/member_ids"
    row_pointer = f"{prefix}/opportunity_contracts"
    bound_artifact_ids = definition.get("bound_artifact_ids")
    rows = definition.get("opportunity_contracts")
    if (
        not isinstance(bound_artifact_ids, list)
        or target_artifact_id not in bound_artifact_ids
        or not isinstance(rows, list)
        or len(rows) != 4
    ):
        raise GateError(
            "GA12-JOINT-OPPORTUNITY-REGISTRY-MANIFEST-CANARY-COVERAGE",
            "observed opportunity manifest case preconditions differ",
        )

    def pointer_value(pointer: str) -> Any:
        value: Any = registry
        for token in pointer[1:].split("/"):
            value = value[int(token)] if isinstance(value, list) else value[token]
        return copy.deepcopy(value)

    def replace(pointer: str, value: Any) -> dict[str, Any]:
        return {
            "operation": "replace",
            "json_pointer": pointer,
            "value": copy.deepcopy(value),
        }

    def remove(pointer: str) -> dict[str, Any]:
        return {"operation": "remove", "json_pointer": pointer}

    def swap(pointer: str, left: int, right: int) -> list[dict[str, Any]]:
        return [
            replace(f"{pointer}/{left}", pointer_value(f"{pointer}/{right}")),
            replace(f"{pointer}/{right}", pointer_value(f"{pointer}/{left}")),
        ]

    manifest_pointer = "/joint_silent_miss/opportunity_rows"
    reference_pointer = "/joint_silent_miss/opportunity_set_ref"
    cases: tuple[tuple[str, str, list[dict[str, Any]], str], ...] = (
        ("member-order", "manifest", swap(member_pointer, 0, 1), manifest_pointer),
        (
            "member-substitution",
            "manifest",
            [
                replace(
                    f"{member_pointer}/3",
                    "reiyah.opportunity.synthetic.nonobserved.004",
                )
            ],
            manifest_pointer,
        ),
        (
            "member-completeness",
            "manifest",
            [remove(f"{member_pointer}/3")],
            manifest_pointer,
        ),
        (
            "row-completeness",
            "manifest",
            [remove(f"{row_pointer}/3")],
            manifest_pointer,
        ),
        (
            "coordinated-completeness",
            "manifest",
            [remove(f"{member_pointer}/3"), remove(f"{row_pointer}/3")],
            manifest_pointer,
        ),
        (
            "bound-artifact",
            "manifest",
            [
                remove(
                    f"{prefix}/bound_artifact_ids/"
                    f"{bound_artifact_ids.index(target_artifact_id)}"
                )
            ],
            reference_pointer,
        ),
        (
            "object-binding",
            "manifest",
            [
                replace(
                    f"{prefix}/object_ref/record_id",
                    "reiyah.object.synthetic_vehicle_alternate",
                ),
                *[
                    replace(
                        f"{row_pointer}/{row_index}/object_ref/record_id",
                        "reiyah.object.synthetic_vehicle_alternate",
                    )
                    for row_index in range(4)
                ],
            ],
            manifest_pointer,
        ),
        (
            "clock-binding",
            "manifest",
            [
                replace(
                    f"{prefix}/opportunity_window/clock_id",
                    "reiyah.clock.synthetic-monotonic",
                ),
                *[
                    replace(
                        f"{row_pointer}/{row_index}/clock_id",
                        "reiyah.clock.synthetic-monotonic",
                    )
                    for row_index in range(4)
                ],
            ],
            manifest_pointer,
        ),
        (
            "window-binding",
            "manifest",
            [
                replace(
                    f"{prefix}/opportunity_window/window_id",
                    "reiyah.window.readiness_001",
                ),
                *[
                    replace(
                        f"{row_pointer}/{row_index}/window_id",
                        "reiyah.window.readiness_001",
                    )
                    for row_index in range(4)
                ],
            ],
            manifest_pointer,
        ),
        (
            "window-open",
            "manifest",
            [
                replace(
                    f"{prefix}/opportunity_window/opened_at",
                    "2026-08-24T07:59:00Z",
                )
            ],
            manifest_pointer,
        ),
        (
            "window-close",
            "manifest",
            [
                replace(
                    f"{prefix}/opportunity_window/closed_at",
                    "2026-08-24T08:11:00Z",
                )
            ],
            manifest_pointer,
        ),
        (
            "row-order",
            "manifest",
            swap(member_pointer, 0, 1) + swap(row_pointer, 0, 1),
            manifest_pointer,
        ),
        (
            "row-opportunity-id",
            "row_operand",
            [
                replace(
                    f"{member_pointer}/0",
                    "reiyah.opportunity.synthetic.nonobserved.001",
                ),
                replace(
                    f"{row_pointer}/0/opportunity_id",
                    "reiyah.opportunity.synthetic.nonobserved.001",
                ),
            ],
            manifest_pointer,
        ),
        (
            "row-object",
            "row_operand",
            [
                replace(
                    f"{row_pointer}/0/object_ref/record_id",
                    "reiyah.object.synthetic_vehicle_alternate",
                )
            ],
            manifest_pointer,
        ),
        (
            "row-clock",
            "row_operand",
            [
                replace(
                    f"{row_pointer}/0/clock_id",
                    "reiyah.clock.synthetic-monotonic",
                )
            ],
            manifest_pointer,
        ),
        (
            "row-window",
            "row_operand",
            [
                replace(
                    f"{row_pointer}/0/window_id",
                    "reiyah.window.readiness_001",
                )
            ],
            manifest_pointer,
        ),
        (
            "row-time",
            "row_operand",
            [
                replace(
                    f"{row_pointer}/0/occurred_at/value",
                    "2026-08-24T08:01:30Z",
                )
            ],
            manifest_pointer,
        ),
        (
            "row-reference-state",
            "row_operand",
            [
                replace(
                    f"{row_pointer}/0/reference_state/value",
                    "opportunity_absent",
                )
            ],
            manifest_pointer,
        ),
        (
            "row-reference-validity",
            "row_operand",
            [replace(f"{row_pointer}/0/reference_validity/value", "invalid")],
            manifest_pointer,
        ),
        (
            "human-channel-ref",
            "row_operand",
            [
                replace(
                    f"{row_pointer}/0/human_channel/channel_ref/record_id",
                    "reiyah.channel.synthetic_automation_observation",
                )
            ],
            manifest_pointer,
        ),
        (
            "human-outcome",
            "row_operand",
            [replace(f"{row_pointer}/0/human_channel/outcome/value", "detected")],
            manifest_pointer,
        ),
        (
            "automation-channel-ref",
            "row_operand",
            [
                replace(
                    f"{row_pointer}/0/automation_channel/channel_ref/record_id",
                    "reiyah.channel.synthetic_human_observation",
                )
            ],
            manifest_pointer,
        ),
        (
            "automation-outcome",
            "row_operand",
            [
                replace(
                    f"{row_pointer}/0/automation_channel/outcome/value",
                    "detected",
                )
            ],
            manifest_pointer,
        ),
        (
            "warning-rule",
            "row_operand",
            [
                replace(
                    f"{row_pointer}/0/warning/rule_ref/rule_id",
                    "reiyah.rule.joint_fallback_observation",
                )
            ],
            manifest_pointer,
        ),
        (
            "warning-outcome",
            "row_operand",
            [replace(f"{row_pointer}/0/warning/outcome/value", "issued")],
            manifest_pointer,
        ),
        (
            "fallback-rule",
            "row_operand",
            [
                replace(
                    f"{row_pointer}/0/fallback/rule_ref/rule_id",
                    "reiyah.rule.joint_warning_observation",
                )
            ],
            manifest_pointer,
        ),
        (
            "fallback-outcome",
            "row_operand",
            [replace(f"{row_pointer}/0/fallback/outcome/value", "activated")],
            manifest_pointer,
        ),
    )
    reason = (
        "The complete ordered opportunity identities and typed rows must exact-bind "
        "one artifact-bound protocol-owned synthetic manifest; it is static resolver "
        "evidence, not a real population."
    )
    return [
        {
            "case_id": (
                f"reiyah.validator-canary.joint-opportunity-registry.{predicate_id}"
            ),
            "family": family,
            "definition_id": definition["definition_id"],
            "predicate_id": predicate_id,
            "mutations": mutations,
            "expected_semantic_singleton": {
                "rule_id": "GA-JOINT-OPPORTUNITY-MANIFEST-BINDING",
                "instance_pointer": expected_pointer,
                "reason": reason,
            },
        }
        for predicate_id, family, mutations, expected_pointer in cases
    ]


def _require_joint_opportunity_registry_manifest_case_contract(
    cases: object,
) -> None:
    valid = (
        isinstance(cases, list)
        and tuple(
            case.get("case_id") if isinstance(case, Mapping) else None for case in cases
        )
        == JOINT_OPPORTUNITY_REGISTRY_MANIFEST_CASE_IDS
        and canonical_record_digest(cases)
        == JOINT_OPPORTUNITY_REGISTRY_MANIFEST_CASE_SET_SHA256
    )
    if not valid:
        raise GateError(
            "GA12-JOINT-OPPORTUNITY-REGISTRY-MANIFEST-CANARY-COVERAGE",
            "derived joint opportunity registry-manifest case map differs from the frozen exact matrix",
        )


def validate_joint_opportunity_registry_manifest_binding_matrix(
    snapshot: RepositorySnapshot,
    dependencies: Mapping[str, Any],
) -> dict[str, Any]:
    registry = strict_json(
        snapshot.read(DEFINITION_REGISTRY_PATH), DEFINITION_REGISTRY_PATH
    )
    protocol = strict_json(
        snapshot.read(PROTOCOL_MANIFEST_PATH), PROTOCOL_MANIFEST_PATH
    )
    target_path = "fixtures/v1.2/good/joint-performance-evaluation.json"
    target = strict_json(snapshot.read(target_path), target_path)
    if (
        not isinstance(registry, dict)
        or not isinstance(protocol, dict)
        or not isinstance(target, dict)
        or target.get("schema_id") != JOINT_APPLICATION_SCHEMA_ID
        or not isinstance(target.get("artifact_id"), str)
    ):
        raise GateError(
            "GA12-JOINT-OPPORTUNITY-REGISTRY-MANIFEST-CANARY-COVERAGE",
            "joint opportunity registry-manifest matrix inputs do not bind the exact registry, protocol, and target good",
        )
    cases = _derive_joint_opportunity_registry_manifest_binding_cases(
        registry, target["artifact_id"]
    )
    _require_joint_opportunity_registry_manifest_case_contract(cases)
    registry_validator = validator_for_schema(
        snapshot,
        dependencies,
        "schemas/protocol-definition-registry-1.2.schema.json",
        (COMMON_SCHEMA_PATH,),
    )
    target_validator = validator_for_schema(
        snapshot,
        dependencies,
        APPLICATION_SCHEMA_PATH_BY_ID[JOINT_APPLICATION_SCHEMA_ID],
        SCIENCE_SCHEMA_PATHS,
    )
    if schema_error_records(target_validator, target):
        raise GateError(
            "GA12-JOINT-OPPORTUNITY-REGISTRY-MANIFEST-CANARY-COVERAGE",
            "joint opportunity registry-manifest target good is target-schema-invalid",
        )
    science = load_science_module(snapshot)
    reference_inventory = derive_reference_path_inventory(snapshot)
    handler_contract = science["REFERENCE_PATH_HANDLER_CONTRACT"]
    artifact_inventory = science_artifact_inventory(snapshot)
    lifecycle_policy = protocol.get("lifecycle_transition_policy")
    if not isinstance(lifecycle_policy, Mapping):
        raise GateError(
            "GA12-JOINT-OPPORTUNITY-REGISTRY-MANIFEST-CANARY-COVERAGE",
            "joint opportunity registry-manifest protocol lacks lifecycle policy",
        )
    result_rows: list[dict[str, Any]] = []
    for case in cases:
        try:
            mutated_registry = science["apply_mutations"](registry, case["mutations"])
        except science["ScienceContractError"] as exc:
            raise GateError(
                "GA12-JOINT-OPPORTUNITY-REGISTRY-MANIFEST-CANARY-COVERAGE",
                f"joint opportunity registry-manifest mutation failed: "
                f"{case['case_id']}: {exc}",
            ) from exc
        registry_errors = schema_error_records(registry_validator, mutated_registry)
        if registry_errors:
            first = registry_errors[0]
            raise GateError(
                "GA12-JOINT-OPPORTUNITY-REGISTRY-MANIFEST-CANARY-COVERAGE",
                f"joint opportunity registry-manifest case is registry-schema-invalid: "
                f"{case['case_id']}: {first['schema_keyword']}@"
                f"{first['instance_pointer']}",
            )
        try:
            semantic_errors = science["semantic_violations"](
                target,
                lifecycle_policy,
                mutated_registry,
                protocol,
                {
                    "artifact_inventory": artifact_inventory,
                    "instance_path": target_path,
                    "expected_schema_id": JOINT_APPLICATION_SCHEMA_ID,
                    "reference_path_bindings": reference_inventory["bindings"],
                    "reference_path_handler_contract": handler_contract,
                },
            )
        except science["ScienceContractError"] as exc:
            raise GateError(
                "GA12-JOINT-OPPORTUNITY-REGISTRY-MANIFEST-CANARY-COVERAGE",
                f"joint opportunity registry-manifest semantic execution failed: "
                f"{case['case_id']}: {exc}",
            ) from exc
        if semantic_errors != [case["expected_semantic_singleton"]]:
            raise GateError(
                "GA12-JOINT-OPPORTUNITY-REGISTRY-MANIFEST-CANARY-COVERAGE",
                f"joint opportunity registry-manifest case did not reach its exact "
                f"production singleton: {case['case_id']}: {semantic_errors}",
            )
        result_rows.append(
            {
                "case_id": case["case_id"],
                "family": case["family"],
                "predicate_id": case["predicate_id"],
                "semantic_singleton_matched": True,
            }
        )
    missing_case_diagnostics = tuple(
        captured_gate_diagnostic(
            lambda missing_index=missing_index: (
                _require_joint_opportunity_registry_manifest_case_contract(
                    [
                        copy.deepcopy(case)
                        for case_index, case in enumerate(cases)
                        if case_index != missing_index
                    ]
                )
            )
        )
        for missing_index in range(len(cases))
    )
    unknown_cases = copy.deepcopy(cases)
    unknown_cases.append(
        {
            "case_id": "reiyah.validator-canary.joint-opportunity-registry.unknown",
            "family": "unknown",
            "definition_id": "reiyah.invalid",
            "predicate_id": "unknown",
            "mutations": [],
            "expected_semantic_singleton": {},
        }
    )
    unknown_case_diagnostic = captured_gate_diagnostic(
        lambda: _require_joint_opportunity_registry_manifest_case_contract(
            unknown_cases
        )
    )
    diagnostic = "GA12-JOINT-OPPORTUNITY-REGISTRY-MANIFEST-CANARY-COVERAGE"
    if (
        set(missing_case_diagnostics) != {diagnostic}
        or unknown_case_diagnostic != diagnostic
    ):
        raise GateError(
            diagnostic,
            "joint opportunity registry-manifest exhaustive remove-one/unknown case canaries did not fail closed",
        )
    return {
        "case_count": len(result_rows),
        "manifest_case_count": sum(row["family"] == "manifest" for row in result_rows),
        "row_operand_case_count": sum(
            row["family"] == "row_operand" for row in result_rows
        ),
        "semantic_singleton_count": len(result_rows),
        "case_set_sha256": canonical_record_digest(cases),
        "result_set_sha256": canonical_record_digest(result_rows),
        "coverage_canary_diagnostic": diagnostic,
    }


SCIENCE_LOGICAL_RECORD_ID_FIELDS = MappingProxyType(
    {
        ASSURANCE_APPLICATION_SCHEMA_ID: "bundle_id",
        HUMAN_APPLICATION_SCHEMA_ID: "assessment_id",
        JOINT_APPLICATION_SCHEMA_ID: "evaluation_id",
        OPE_APPLICATION_SCHEMA_ID: "evaluation_id",
        STUDY_APPLICATION_SCHEMA_ID: "study_id",
    }
)


def science_artifact_inventory(
    snapshot: RepositorySnapshot,
) -> Mapping[str, Mapping[str, Any]]:
    inventory: dict[str, Mapping[str, Any]] = {}
    for path in sorted(
        item
        for item in snapshot.files
        if item.startswith(SCIENCE_GOOD_PREFIX) and item.endswith(".json")
    ):
        document = strict_json(snapshot.read(path), path)
        if not isinstance(document, dict):
            raise GateError(
                "GA12-SCIENCE-ARTIFACT-INVENTORY",
                f"science good is not an object: {path}",
            )
        schema_id = document.get("schema_id")
        logical_field = SCIENCE_LOGICAL_RECORD_ID_FIELDS.get(schema_id)
        record_kind = document.get("record_kind")
        if (
            logical_field is None
            or not isinstance(record_kind, str)
            or not isinstance(document.get(logical_field), str)
            or not isinstance(document.get("created_at"), str)
        ):
            raise GateError(
                "GA12-SCIENCE-ARTIFACT-INVENTORY",
                f"science artifact identity is incomplete: {path}",
            )
        item = snapshot.files[path]
        inventory[path] = MappingProxyType(
            {
                "artifact_id": document.get("artifact_id"),
                "artifact_kind": f"reiyah.kind.{record_kind}",
                "version": document.get("version"),
                "schema_id": schema_id,
                "record_kind": record_kind,
                "logical_record_id": document[logical_field],
                "lifecycle_status": document.get("lifecycle_status"),
                "lifecycle_history": document.get("lifecycle_history"),
                "created_at": document.get("created_at"),
                "predecessor_path": (
                    document["lifecycle_history"][-1]["prior_artifact"].get("path")
                    if isinstance(document.get("lifecycle_history"), list)
                    and len(document["lifecycle_history"]) > 1
                    and isinstance(document["lifecycle_history"][-1], dict)
                    and isinstance(
                        document["lifecycle_history"][-1].get("prior_artifact"), dict
                    )
                    else None
                ),
                "sha256": f"sha256:{item.sha256}",
                "byte_size": item.size,
            }
        )
    validate_science_artifact_lineage(
        [dict({"path": path}, **metadata) for path, metadata in inventory.items()]
    )
    return MappingProxyType(inventory)


def validate_science_artifact_lineage(records: Sequence[Mapping[str, Any]]) -> None:
    """Require one immutable, fork-free version lineage for every logical record."""
    artifact_ids = [record.get("artifact_id") for record in records]
    if any(not isinstance(value, str) for value in artifact_ids) or len(
        set(artifact_ids)
    ) != len(artifact_ids):
        raise GateError(
            "GA12-SCIENCE-ARTIFACT-ID-UNIQUE",
            "every scientific artifact_id must identify exactly one immutable version artifact",
        )
    logical_versions = [
        (
            record.get("schema_id"),
            record.get("logical_record_id"),
            record.get("version"),
        )
        for record in records
    ]
    if any(
        not all(isinstance(value, str) for value in key) for key in logical_versions
    ) or len(set(logical_versions)) != len(logical_versions):
        raise GateError(
            "GA12-SCIENCE-LOGICAL-VERSION-UNIQUE",
            "each schema, logical record, and semantic-version tuple must be unique",
        )
    by_path = {
        record.get("path"): record
        for record in records
        if isinstance(record.get("path"), str)
    }
    if len(by_path) != len(records):
        raise GateError(
            "GA12-SCIENCE-LINEAGE-FORK", "scientific artifact paths must be unique"
        )
    groups: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for record in records:
        key = (str(record.get("schema_id")), str(record.get("logical_record_id")))
        groups.setdefault(key, []).append(record)
    for key, group in groups.items():
        group_paths = {str(record["path"]) for record in group}
        child_counts: dict[str, int] = {path: 0 for path in group_paths}
        roots: list[str] = []
        for record in group:
            path = str(record["path"])
            predecessor = record.get("predecessor_path")
            if predecessor is None:
                roots.append(path)
                continue
            if predecessor not in group_paths or predecessor == path:
                raise GateError(
                    "GA12-SCIENCE-LINEAGE-FORK",
                    f"logical record {key} has an unresolved or self predecessor",
                )
            child_counts[str(predecessor)] += 1
        heads = [path for path, children in child_counts.items() if children == 0]
        if (
            len(roots) != 1
            or len(heads) != 1
            or any(children > 1 for children in child_counts.values())
        ):
            raise GateError(
                "GA12-SCIENCE-LINEAGE-FORK",
                f"logical record {key} must have exactly one root, one head, and no forks",
            )
        visited: set[str] = set()
        cursor = heads[0]
        while cursor not in visited:
            visited.add(cursor)
            predecessor = by_path[cursor].get("predecessor_path")
            if predecessor is None:
                break
            cursor = str(predecessor)
        if visited != group_paths or cursor != roots[0]:
            raise GateError(
                "GA12-SCIENCE-LINEAGE-FORK",
                f"logical record {key} is cyclic or disconnected",
            )


def validate_scientific_contracts(
    snapshot: RepositorySnapshot,
    dependencies: Mapping[str, Any],
) -> dict[str, Any]:
    science = load_science_module(snapshot)
    protocol = strict_json(
        snapshot.read(PROTOCOL_MANIFEST_PATH), PROTOCOL_MANIFEST_PATH
    )
    if (
        not isinstance(protocol, dict)
        or protocol.get("release_id") != PROTOCOL_RELEASE_ID
        or not isinstance(protocol.get("lifecycle_transition_policy"), dict)
    ):
        raise GateError(
            "GA12-SCIENCE-PROTOCOL-BINDING",
            "science predicates require the exact Gate A 1.2.0 lifecycle policy",
        )
    lifecycle_policy = protocol["lifecycle_transition_policy"]
    definition_registry = strict_json(
        snapshot.read(DEFINITION_REGISTRY_PATH), DEFINITION_REGISTRY_PATH
    )
    if (
        not isinstance(definition_registry, dict)
        or definition_registry.get("protocol_release_id") != PROTOCOL_RELEASE_ID
        or not isinstance(definition_registry.get("reference_kind_contracts"), list)
        or not isinstance(definition_registry.get("actor_reference_contract"), dict)
    ):
        raise GateError(
            "GA12-SCIENCE-REGISTRY-BINDING",
            "science predicates require the exact Gate A 1.2.0 typed reference registry",
        )
    definition_registry_validator = validator_for_schema(
        snapshot,
        dependencies,
        "schemas/protocol-definition-registry-1.2.schema.json",
        (COMMON_SCHEMA_PATH,),
    )
    definition_registry_errors = schema_error_records(
        definition_registry_validator, definition_registry
    )
    if definition_registry_errors:
        first = definition_registry_errors[0]
        raise GateError(
            "GA12-SCIENCE-REGISTRY-SCHEMA",
            f"definition registry failed {first['schema_keyword']} at {first['instance_pointer']}: {first['message']}",
        )
    validate_definition_registry_uniqueness(definition_registry)
    artifact_inventory = science_artifact_inventory(snapshot)
    schema_paths = sorted(
        path
        for path in snapshot.files
        if path.startswith("schemas/v1.2/") and path.endswith(".schema.json")
    )
    if tuple(schema_paths) != SCIENCE_SCHEMA_PATHS:
        raise GateError(
            "GA12-SCIENCE-SCHEMA-SET",
            f"expected exactly {len(SCIENCE_SCHEMA_PATHS)} v1.2 science schemas, observed {len(schema_paths)}",
        )
    schemas: dict[str, Any] = {}
    schema_path_by_id: dict[str, str] = {}
    for path in schema_paths:
        schema = strict_json(snapshot.read(path), path)
        if not isinstance(schema, dict) or not isinstance(schema.get("$id"), str):
            raise GateError(
                "GA12-SCIENCE-SCHEMA-SHAPE", f"schema lacks object/$id: {path}"
            )
        schema_id = schema["$id"]
        if schema_id in schemas:
            raise GateError(
                "GA12-SCIENCE-SCHEMA-ID", f"duplicate science schema $id: {schema_id}"
            )
        schemas[schema_id] = schema
        schema_path_by_id[schema_id] = path
    format_checker = local_format_checker(dependencies)
    Registry = dependencies["Registry"]
    Resource = dependencies["Resource"]
    registry = Registry().with_resources(
        (schema_id, Resource.from_contents(schema))
        for schema_id, schema in sorted(schemas.items())
    )
    Draft202012Validator = dependencies["Draft202012Validator"]
    validators: dict[str, Any] = {}
    for schema_id, schema in sorted(schemas.items()):
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            raise GateError(
                "GA12-SCIENCE-SCHEMA-METAVALIDATION",
                f"invalid Draft 2020-12 schema {schema_path_by_id[schema_id]}: {exc}",
            ) from exc
        validators[schema_id] = Draft202012Validator(
            schema,
            registry=registry,
            format_checker=format_checker,
        )
    reference_path_inventory = derive_reference_path_inventory(snapshot)
    handler_contract = science["REFERENCE_PATH_HANDLER_CONTRACT"]
    if not isinstance(handler_contract, Mapping):
        raise GateError(
            "GA12-REFERENCE-PATH-COVERAGE",
            "science module reference handler contract must be an object",
        )
    if handler_contract != reference_path_handler_contract(
        reference_path_inventory["bindings"]
    ):
        raise GateError(
            "GA12-REFERENCE-PATH-COVERAGE",
            "science handler contract differs from the schema-derived reference inventory",
        )
    discovered_good_paths = {
        path
        for path in snapshot.files
        if path.startswith(SCIENCE_GOOD_PREFIX) and path.endswith(".json")
    }
    raw_profile = strict_json(
        snapshot.read(SCIENTIFIC_PROFILE_PATH), SCIENTIFIC_PROFILE_PATH
    )
    if not isinstance(raw_profile, dict) or not isinstance(
        raw_profile.get("fixture_bindings"), list
    ):
        raise GateError(
            "GA12-SCIENCE-GOOD-SET",
            "scientific profile fixture bindings are unavailable",
        )
    raw_profiled_good_paths = [
        binding.get("path")
        for binding in raw_profile["fixture_bindings"]
        if isinstance(binding, dict) and binding.get("classification") == "known_good"
    ]
    if not raw_profiled_good_paths or not all(
        isinstance(path, str) for path in raw_profiled_good_paths
    ):
        raise GateError(
            "GA12-SCIENCE-GOOD-SET",
            "profile known-good paths must be non-empty strings",
        )
    profiled_good_paths = set(raw_profiled_good_paths)
    if (
        len(raw_profiled_good_paths) != len(profiled_good_paths)
        or profiled_good_paths != discovered_good_paths
    ):
        raise GateError(
            "GA12-SCIENCE-GOOD-SET",
            f"profile and repository known-good sets differ: missing={sorted(discovered_good_paths - profiled_good_paths)}, unexpected={sorted(profiled_good_paths - discovered_good_paths)}",
        )
    good_paths = sorted(discovered_good_paths)
    good_by_path: dict[str, Any] = {}
    for path in good_paths:
        instance = strict_json(snapshot.read(path), path)
        if (
            not isinstance(instance, dict)
            or instance.get("schema_id") not in validators
        ):
            raise GateError(
                "GA12-SCIENCE-GOOD-BINDING",
                f"good fixture target schema is unknown: {path}",
            )
        schema_id = instance["schema_id"]
        errors = schema_error_records(validators[schema_id], instance)
        if errors:
            raise GateError(
                "GA12-SCIENCE-GOOD-SCHEMA",
                f"good fixture failed {errors[0]['schema_keyword']} at {errors[0]['instance_pointer']}: {path}",
            )
        try:
            semantic_errors = science["semantic_violations"](
                instance,
                lifecycle_policy,
                definition_registry,
                protocol,
                {
                    "artifact_inventory": artifact_inventory,
                    "instance_path": path,
                    "expected_schema_id": schema_id,
                    "reference_path_bindings": reference_path_inventory["bindings"],
                    "reference_path_handler_contract": handler_contract,
                },
            )
        except science["ScienceContractError"] as exc:
            raise GateError(
                "GA12-SCIENCE-SEMANTIC-EXECUTION", f"{path}: {exc}"
            ) from exc
        if semantic_errors:
            first = semantic_errors[0]
            raise GateError(
                "GA12-SCIENCE-GOOD-SEMANTIC",
                f"good fixture triggered {first['rule_id']} at {first['instance_pointer']}: {path}",
            )
        good_by_path[path] = instance
    mutation_schema_id = "https://schemas.reiyah.invalid/scientific-contract/1.2.0/scientific-contract-mutation-fixture.schema.json"
    mutation_paths: list[str] = []
    for path in sorted(
        item
        for item in snapshot.files
        if item.startswith(SCIENCE_BAD_PREFIX) and item.endswith(".json")
    ):
        candidate_fixture = strict_json(snapshot.read(path), path)
        if (
            isinstance(candidate_fixture, dict)
            and candidate_fixture.get("schema_id") == mutation_schema_id
        ):
            mutation_paths.append(path)
    if not mutation_paths:
        raise GateError(
            "GA12-SCIENCE-MUTATION-SET", "no scientific mutation fixtures were declared"
        )
    declared_rules: set[str] = set()
    fixture_ids: set[str] = set()
    schema_rejection_count = 0
    diagnostics: list[dict[str, Any]] = []
    for path in mutation_paths:
        fixture = strict_json(snapshot.read(path), path)
        fixture_schema_errors = schema_error_records(
            validators[mutation_schema_id], fixture
        )
        if fixture_schema_errors:
            raise GateError(
                "GA12-SCIENCE-MUTATION-SCHEMA",
                f"mutation declaration invalid at {fixture_schema_errors[0]['instance_pointer']}: {path}",
            )
        fixture_id = fixture["fixture_id"]
        if fixture_id in fixture_ids:
            raise GateError(
                "GA12-SCIENCE-MUTATION-ID",
                f"duplicate mutation fixture ID: {fixture_id}",
            )
        fixture_ids.add(fixture_id)
        base_path = fixture["base_fixture_path"]
        if base_path not in good_by_path:
            raise GateError(
                "GA12-SCIENCE-MUTATION-BASE",
                f"mutation base is not an exact good fixture: {path}",
            )
        base = good_by_path[base_path]
        if base["schema_id"] != fixture["target_schema_id"]:
            raise GateError(
                "GA12-SCIENCE-MUTATION-BINDING",
                f"target schema differs from base: {path}",
            )
        try:
            mutated = science["apply_mutations"](base, fixture["mutations"])
        except science["ScienceContractError"] as exc:
            raise GateError("GA12-SCIENCE-MUTATION-APPLY", f"{path}: {exc}") from exc
        target_schema_errors = schema_error_records(
            validators[fixture["target_schema_id"]], mutated
        )
        if target_schema_errors:
            schema_rejection_count += 1
        expected = fixture["expected_failure"]
        expected_rule = expected["rule_id"]
        declared_rules.add(expected_rule)
        expected_keyword = expected.get("schema_keyword")
        if expected_keyword == "semantic" and target_schema_errors:
            first = target_schema_errors[0]
            raise GateError(
                "GA12-SCIENCE-MUTATION-SEMANTIC-REACHABILITY",
                f"{path}: semantic-primary mutation is target-schema-invalid at "
                f"{first['instance_pointer']} ({first['schema_keyword']}): {first['message']}",
            )
        if expected_keyword != "semantic":
            observed_primary = target_schema_errors[0] if target_schema_errors else None
            structural_match = (
                observed_primary is not None
                and observed_primary["schema_keyword"] == expected_keyword
                and observed_primary["instance_pointer"] == expected["instance_pointer"]
            )
            if not structural_match:
                raise GateError(
                    "GA12-SCIENCE-MUTATION-STRUCTURAL-PRIMARY",
                    f"{path}: declared structural failure "
                    f"{expected_keyword}@{expected['instance_pointer']} is not the canonical first schema diagnostic; observed={observed_primary}",
                )
            diagnostics.append(
                {
                    "fixture_id": fixture_id,
                    "path": path,
                    "rule_id": expected_rule,
                    "declared_instance_pointer": expected["instance_pointer"],
                    "schema_rejected": True,
                    "semantic_violation_count": 0,
                }
            )
            continue
        try:
            semantic_errors = science["semantic_violations"](
                mutated,
                lifecycle_policy,
                definition_registry,
                protocol,
                {
                    "artifact_inventory": artifact_inventory,
                    "instance_path": base_path,
                    "expected_schema_id": fixture["target_schema_id"],
                    "reference_path_bindings": reference_path_inventory["bindings"],
                    "reference_path_handler_contract": handler_contract,
                },
            )
        except science["ScienceContractError"] as exc:
            raise GateError("GA12-SCIENCE-MUTATION-APPLY", f"{path}: {exc}") from exc
        expected_tuple = {
            "rule_id": expected_rule,
            "instance_pointer": expected["instance_pointer"],
            "reason": expected["reason"],
        }
        if semantic_errors != [expected_tuple]:
            raise GateError(
                "GA12-SCIENCE-MUTATION-PRIMARY",
                f"{path}: production diagnostic must equal the one declared semantic tuple; observed={semantic_errors}",
            )
        diagnostics.append(
            {
                "fixture_id": fixture_id,
                "path": path,
                "rule_id": expected_rule,
                "declared_instance_pointer": expected["instance_pointer"],
                "schema_rejected": bool(target_schema_errors),
                "semantic_violation_count": len(semantic_errors),
            }
        )
    supported_rules = set(science["SUPPORTED_RULE_IDS"])
    if declared_rules != supported_rules:
        raise GateError(
            "GA12-SCIENCE-RULE-COVERAGE",
            f"declared and implemented semantic rule sets differ: missing={sorted(declared_rules - supported_rules)}, extra={sorted(supported_rules - declared_rules)}",
        )
    return {
        "schema_count": len(schema_paths),
        "schema_set_sha256": artifact_set_digest(snapshot, schema_paths),
        "good_fixture_count": len(good_paths),
        "good_fixture_set_sha256": artifact_set_digest(snapshot, good_paths),
        "mutation_fixture_count": len(mutation_paths),
        "mutation_fixture_set_sha256": artifact_set_digest(snapshot, mutation_paths),
        "semantic_rule_count": len(declared_rules),
        "schema_rejected_mutation_count": schema_rejection_count,
        "semantic_rejected_mutation_count": len(diagnostics),
        "diagnostics": diagnostics,
    }


def captured_gate_diagnostic(operation: Callable[[], None]) -> str | None:
    try:
        operation()
    except GateError as exc:
        return exc.code
    return None


def evaluate_transport_boundary(
    snapshot: RepositorySnapshot,
    publisher_receipt_path: str,
    independent_record_paths: Sequence[str],
    claimed_state: str,
) -> dict[str, Any]:
    receipt = strict_json(snapshot.read(publisher_receipt_path), publisher_receipt_path)
    if not isinstance(receipt, dict) or not isinstance(receipt.get("receipt_id"), str):
        raise GateError(
            "GA12-TRANSPORT-RECEIPT", "publisher receipt must be an identified object"
        )
    # Repository-held publisher assertions are historical inputs only.  This
    # offline validator has neither an authenticated independent observer nor
    # external readback authority, even when the receipt narrates a readback.
    if independent_record_paths:
        raise GateError(
            "GA12-TRANSPORT-INDEPENDENT-RECORD-EXTERNAL",
            "independent transport records require separately authenticated external verification",
        )
    derived_state = "not_evaluated"
    if claimed_state != derived_state:
        raise GateError(
            "GA12-TRANSPORT-EXTERNALLY-UNVERIFIED",
            "publisher receipt assertions cannot establish independent transport verification",
        )
    return {
        "status": derived_state,
        "publisher_receipt_path": publisher_receipt_path,
        "publisher_receipt_is_independent_verification": False,
        "independent_record_id": None,
    }


def governance_time(value: object) -> datetime | None:
    if not is_rfc3339_datetime(value) or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(
            value[:-1] + "+00:00" if value.endswith(("Z", "z")) else value
        )
    except ValueError:
        return None


def validate_actual_publication_schema(
    snapshot: RepositorySnapshot,
    dependencies: Mapping[str, Any],
    schema_path: str,
    instance: Mapping[str, Any],
    diagnostic: str,
) -> None:
    resource_paths = tuple(
        sorted(
            path
            for path in snapshot.files
            if path.startswith("schemas/") and path.endswith(".schema.json")
        )
    )
    validator = validator_for_schema(
        snapshot, dependencies, schema_path, resource_paths
    )
    errors = schema_error_records(validator, instance)
    if errors:
        validate_actual_publication_event_guard(
            actual_publication_event_guard_operands(schema_valid=False)
        )


ACTUAL_PUBLICATION_EVENT_GUARD_BASELINE: Mapping[str, bool] = MappingProxyType(
    {
        "rights_present": True,
        "receipt_present": True,
        "schema_valid": True,
        "byte_bindings_equal": True,
        "reference_bindings_equal": True,
        "rights_preflight_eligible": True,
        "chronology_valid": True,
        "parent_packet_binding_equal": True,
        "event_delta_exact": True,
        "candidate_projection_equal": True,
        "canonical_index_equal": True,
        "canonical_report_equal": True,
    }
)
ACTUAL_PUBLICATION_EVENT_CANARY_EXPECTED: Mapping[str, str] = MappingProxyType(
    {
        "missing_guard_operand": "GA12-PUBLICATION-EVENT-ACTUAL-SCHEMA",
        "unexpected_guard_operand": "GA12-PUBLICATION-EVENT-ACTUAL-SCHEMA",
        "rights_only_presence": "GA12-PUBLICATION-EVENT-ARTIFACT-PRESENCE",
        "receipt_only_presence": "GA12-PUBLICATION-EVENT-ARTIFACT-PRESENCE",
        "schema_mismatch": "GA12-PUBLICATION-EVENT-ACTUAL-SCHEMA",
        "byte_mismatch": "GA12-PUBLICATION-EVENT-ACTUAL-BYTE-BINDING",
        "reference_mismatch": "GA12-PUBLICATION-EVENT-ACTUAL-REFERENCE-BINDING",
        "false_rights_coverage": "GA12-PUBLICATION-EVENT-ACTUAL-RIGHTS-PREFLIGHT",
        "blocked_rights_preflight": "GA12-PUBLICATION-EVENT-ACTUAL-RIGHTS-PREFLIGHT",
        "inconclusive_rights_preflight": "GA12-PUBLICATION-EVENT-ACTUAL-RIGHTS-PREFLIGHT",
        "stale_chronology": "GA12-PUBLICATION-EVENT-CHRONOLOGY",
        "wrong_parent_packet": "GA12-PUBLICATION-EVENT-ACTUAL-TOPOLOGY",
        "extra_or_changed_path": "GA12-PUBLICATION-EVENT-ACTUAL-TOPOLOGY",
        "changed_candidate_projection": "GA12-PUBLICATION-EVENT-ACTUAL-TOPOLOGY",
        "changed_canonical_index": "GA12-PUBLICATION-EVENT-ACTUAL-TOPOLOGY",
        "changed_canonical_report": "GA12-PUBLICATION-EVENT-ACTUAL-TOPOLOGY",
    }
)


def actual_publication_event_guard_operands(
    **overrides: bool,
) -> dict[str, bool]:
    if not set(overrides).issubset(ACTUAL_PUBLICATION_EVENT_GUARD_BASELINE):
        raise GateError(
            "GA12-PUBLICATION-EVENT-ACTUAL-SCHEMA",
            "actual publication-event guard received an unknown operand",
        )
    return {**ACTUAL_PUBLICATION_EVENT_GUARD_BASELINE, **overrides}


def actual_rights_preflight_eligible(
    all_included_payloads_covered: object,
    preflight_outcome: object,
) -> bool:
    return (
        all_included_payloads_covered is True
        and preflight_outcome
        == "eligible_payload_basis_observed_pointer_payloads_excluded"
    )


def validate_actual_publication_event_guard(
    operands: Mapping[str, bool],
) -> None:
    required = set(ACTUAL_PUBLICATION_EVENT_GUARD_BASELINE)
    if set(operands) != required or not all(
        isinstance(value, bool) for value in operands.values()
    ):
        raise GateError(
            "GA12-PUBLICATION-EVENT-ACTUAL-SCHEMA",
            "actual publication-event guard operands are not the closed boolean record",
        )
    if operands["rights_present"] != operands["receipt_present"]:
        raise GateError(
            "GA12-PUBLICATION-EVENT-ARTIFACT-PRESENCE",
            "actual rights and receipt artifacts must be jointly absent or jointly present",
        )
    if not operands["schema_valid"]:
        raise GateError(
            "GA12-PUBLICATION-EVENT-ACTUAL-SCHEMA",
            "actual publication artifact failed its closed production schema",
        )
    if not operands["byte_bindings_equal"]:
        raise GateError(
            "GA12-PUBLICATION-EVENT-ACTUAL-BYTE-BINDING",
            "actual publication artifact bytes differ from a declared binding",
        )
    if not operands["reference_bindings_equal"]:
        raise GateError(
            "GA12-PUBLICATION-EVENT-ACTUAL-REFERENCE-BINDING",
            "actual publication reference join differs",
        )
    if not operands["rights_preflight_eligible"]:
        raise GateError(
            "GA12-PUBLICATION-EVENT-ACTUAL-RIGHTS-PREFLIGHT",
            "actual rights preflight does not cover every included payload or is not eligible",
        )
    if not operands["chronology_valid"]:
        raise GateError(
            "GA12-PUBLICATION-EVENT-CHRONOLOGY",
            "actual publication chronology/freshness differs",
        )
    if not operands["parent_packet_binding_equal"]:
        raise GateError(
            "GA12-PUBLICATION-EVENT-ACTUAL-TOPOLOGY",
            "actual C_receipt parent/C_packet binding differs",
        )
    if not operands["event_delta_exact"]:
        raise GateError(
            "GA12-PUBLICATION-EVENT-ACTUAL-TOPOLOGY",
            "actual C_receipt event-artifact delta differs",
        )
    if not operands["candidate_projection_equal"]:
        raise GateError(
            "GA12-PUBLICATION-EVENT-ACTUAL-TOPOLOGY",
            "candidate projection changed across C_packet and C_receipt",
        )
    if not operands["canonical_index_equal"]:
        raise GateError(
            "GA12-PUBLICATION-EVENT-ACTUAL-TOPOLOGY",
            "canonical index changed across C_packet and C_receipt",
        )
    if not operands["canonical_report_equal"]:
        raise GateError(
            "GA12-PUBLICATION-EVENT-ACTUAL-TOPOLOGY",
            "canonical report changed across C_packet and C_receipt",
        )


def require_exact_canary_matrix(
    observed: Mapping[str, str | None],
    expected: Mapping[str, str],
    diagnostic: str,
) -> None:
    if tuple(observed) != tuple(expected) or dict(observed) != dict(expected):
        raise GateError(
            diagnostic,
            "canary case IDs/order or exact diagnostics differ from the frozen matrix",
        )


def actual_publication_event_fault_canary_matrix() -> str:
    positive_jointly_present = actual_publication_event_guard_operands()
    positive_jointly_absent = actual_publication_event_guard_operands(
        rights_present=False,
        receipt_present=False,
    )
    positive_diagnostics = (
        captured_gate_diagnostic(
            lambda: validate_actual_publication_event_guard(positive_jointly_present)
        ),
        captured_gate_diagnostic(
            lambda: validate_actual_publication_event_guard(positive_jointly_absent)
        ),
    )
    if positive_diagnostics != (None, None):
        raise GateError(
            "GA12-PUBLICATION-EVENT-ACTUAL-CANARY-COVERAGE",
            "jointly present/absent positive event guard baselines were rejected",
        )
    cases = {
        "missing_guard_operand": (
            {
                key: value
                for key, value in positive_jointly_present.items()
                if key != "canonical_report_equal"
            },
            "GA12-PUBLICATION-EVENT-ACTUAL-SCHEMA",
        ),
        "unexpected_guard_operand": (
            {**positive_jointly_present, "unexpected_operand": True},
            "GA12-PUBLICATION-EVENT-ACTUAL-SCHEMA",
        ),
        "rights_only_presence": (
            actual_publication_event_guard_operands(receipt_present=False),
            "GA12-PUBLICATION-EVENT-ARTIFACT-PRESENCE",
        ),
        "receipt_only_presence": (
            actual_publication_event_guard_operands(rights_present=False),
            "GA12-PUBLICATION-EVENT-ARTIFACT-PRESENCE",
        ),
        "schema_mismatch": (
            actual_publication_event_guard_operands(schema_valid=False),
            "GA12-PUBLICATION-EVENT-ACTUAL-SCHEMA",
        ),
        "byte_mismatch": (
            actual_publication_event_guard_operands(byte_bindings_equal=False),
            "GA12-PUBLICATION-EVENT-ACTUAL-BYTE-BINDING",
        ),
        "reference_mismatch": (
            actual_publication_event_guard_operands(reference_bindings_equal=False),
            "GA12-PUBLICATION-EVENT-ACTUAL-REFERENCE-BINDING",
        ),
        "false_rights_coverage": (
            actual_publication_event_guard_operands(
                rights_preflight_eligible=actual_rights_preflight_eligible(
                    False,
                    "eligible_payload_basis_observed_pointer_payloads_excluded",
                )
            ),
            "GA12-PUBLICATION-EVENT-ACTUAL-RIGHTS-PREFLIGHT",
        ),
        "blocked_rights_preflight": (
            actual_publication_event_guard_operands(
                rights_preflight_eligible=actual_rights_preflight_eligible(
                    True, "blocked_rights_uncertain"
                )
            ),
            "GA12-PUBLICATION-EVENT-ACTUAL-RIGHTS-PREFLIGHT",
        ),
        "inconclusive_rights_preflight": (
            actual_publication_event_guard_operands(
                rights_preflight_eligible=actual_rights_preflight_eligible(
                    True, "inconclusive"
                )
            ),
            "GA12-PUBLICATION-EVENT-ACTUAL-RIGHTS-PREFLIGHT",
        ),
        "stale_chronology": (
            actual_publication_event_guard_operands(chronology_valid=False),
            "GA12-PUBLICATION-EVENT-CHRONOLOGY",
        ),
        "wrong_parent_packet": (
            actual_publication_event_guard_operands(parent_packet_binding_equal=False),
            "GA12-PUBLICATION-EVENT-ACTUAL-TOPOLOGY",
        ),
        "extra_or_changed_path": (
            actual_publication_event_guard_operands(event_delta_exact=False),
            "GA12-PUBLICATION-EVENT-ACTUAL-TOPOLOGY",
        ),
        "changed_candidate_projection": (
            actual_publication_event_guard_operands(candidate_projection_equal=False),
            "GA12-PUBLICATION-EVENT-ACTUAL-TOPOLOGY",
        ),
        "changed_canonical_index": (
            actual_publication_event_guard_operands(canonical_index_equal=False),
            "GA12-PUBLICATION-EVENT-ACTUAL-TOPOLOGY",
        ),
        "changed_canonical_report": (
            actual_publication_event_guard_operands(canonical_report_equal=False),
            "GA12-PUBLICATION-EVENT-ACTUAL-TOPOLOGY",
        ),
    }
    observed = {
        case_id: captured_gate_diagnostic(
            lambda operands=operands: validate_actual_publication_event_guard(operands)
        )
        for case_id, (operands, _expected) in cases.items()
    }
    declared_case_diagnostics = {
        case_id: diagnostic for case_id, (_operands, diagnostic) in cases.items()
    }
    if declared_case_diagnostics != dict(ACTUAL_PUBLICATION_EVENT_CANARY_EXPECTED):
        raise GateError(
            "GA12-PUBLICATION-EVENT-ACTUAL-CANARY-COVERAGE",
            "actual publication-event case construction differs from the frozen matrix",
        )
    require_exact_canary_matrix(
        observed,
        ACTUAL_PUBLICATION_EVENT_CANARY_EXPECTED,
        "GA12-PUBLICATION-EVENT-ACTUAL-CANARY-COVERAGE",
    )
    for removed_case_id in ACTUAL_PUBLICATION_EVENT_CANARY_EXPECTED:
        missing_case = {
            case_id: diagnostic
            for case_id, diagnostic in observed.items()
            if case_id != removed_case_id
        }
        if (
            captured_gate_diagnostic(
                lambda missing_case=missing_case: require_exact_canary_matrix(
                    missing_case,
                    ACTUAL_PUBLICATION_EVENT_CANARY_EXPECTED,
                    "GA12-PUBLICATION-EVENT-ACTUAL-CANARY-COVERAGE",
                )
            )
            != "GA12-PUBLICATION-EVENT-ACTUAL-CANARY-COVERAGE"
        ):
            raise GateError(
                "GA12-PUBLICATION-EVENT-ACTUAL-CANARY-COVERAGE",
                "actual publication-event remove-one coverage canary did not "
                f"fail closed for {removed_case_id}",
            )
    return "GA12-PUBLICATION-EVENT-ACTUAL-CANARY-COVERAGE"


def actual_artifact_reference_matches(
    snapshot: RepositorySnapshot,
    reference: Mapping[str, Any],
    expected_path: str,
) -> bool:
    item = snapshot.files.get(expected_path)
    return (
        reference.get("path") == expected_path
        and item is not None
        and reference.get("sha256") == f"sha256:{item.sha256}"
        and reference.get("byte_size") == item.size
    )


def validate_actual_capture_manifests(
    snapshot: RepositorySnapshot,
    dependencies: Mapping[str, Any],
    topology: Mapping[str, Any],
) -> tuple[list[Mapping[str, Any]], list[dict[str, Any]], list[datetime]]:
    declarations = topology.get("capture_manifests")
    if not isinstance(declarations, list) or len(declarations) != 2:
        raise GateError(
            "GA12-PUBLICATION-EVENT-STATIC-CONTRACT",
            "static publication topology must declare exactly two capture manifests",
        )
    captures: list[Mapping[str, Any]] = []
    bindings: list[dict[str, Any]] = []
    completion_times: list[datetime] = []
    exact_fields = (
        ("artifact_id", "artifact_id"),
        ("artifact_path", "artifact_path"),
        ("capture_id", "capture_id"),
        ("schema_id", "schema_id"),
        ("version", "version"),
        ("capture_role", "capture_role"),
        ("observation_mode", "observation_mode"),
        ("retained_capture_extent", "retained_capture_extent"),
        ("requested_url", "requested_url"),
        ("final_url", "final_url"),
    )
    for declaration in declarations:
        if not isinstance(declaration, Mapping):
            raise GateError(
                "GA12-PUBLICATION-EVENT-STATIC-CONTRACT",
                "capture declaration must be an object",
            )
        path = declaration.get("artifact_path")
        if not isinstance(path, str) or path not in snapshot.files:
            raise GateError(
                "GA12-PUBLICATION-EVENT-ARTIFACT-PRESENCE",
                f"prepacket capture manifest is absent: {path}",
            )
        capture = strict_json(snapshot.read(path), path)
        if not isinstance(capture, Mapping):
            raise GateError(
                "GA12-PUBLICATION-EVENT-ACTUAL-SCHEMA",
                f"capture manifest is not an object: {path}",
            )
        validate_actual_publication_schema(
            snapshot,
            dependencies,
            RIGHTS_CAPTURE_SCHEMA_PATH,
            capture,
            "GA12-PUBLICATION-EVENT-ACTUAL-SCHEMA",
        )
        if any(
            capture.get(record_field) != declaration.get(declaration_field)
            for record_field, declaration_field in exact_fields
        ) or not (
            declaration.get("included_in_candidate_projection") is True
            and declaration.get("binds_candidate_git_commit") is False
            and declaration.get("index_role") == "rights_observation_capture_manifest"
        ):
            raise GateError(
                "GA12-PUBLICATION-EVENT-ACTUAL-REFERENCE-BINDING",
                f"capture record differs from its static role/path declaration: {path}",
            )
        started = governance_time(capture.get("observation_started_at"))
        completed = governance_time(capture.get("observation_completed_at"))
        direct = governance_mapping(capture.get("direct_http_attempt"))
        retrieval = (
            governance_time(direct.get("retrieval_completed_at"))
            if direct is not None
            else None
        )
        if (
            started is None
            or completed is None
            or retrieval is None
            or not started <= retrieval <= completed
        ):
            validate_actual_publication_event_guard(
                actual_publication_event_guard_operands(chronology_valid=False)
            )
        if capture.get("observation_mode") == (
            "adapter_observation_with_blocked_direct_attempt"
        ):
            adapter = governance_mapping(capture.get("adapter_observation"))
            if not (
                adapter is not None
                and governance_time(adapter.get("observation_completed_at"))
                == completed
                and direct.get("http_status") == 403
                and capture.get("unretained_response_measurement") is None
                and capture.get("source_bytes_exposed_to_reiyah_observer") is False
            ):
                raise GateError(
                    "GA12-PUBLICATION-EVENT-ACTUAL-REFERENCE-BINDING",
                    "ISO capture mode operands contradict the static blocked-direct contract",
                )
        elif capture.get("observation_mode") == "direct_http_metadata_digest":
            if not (
                capture.get("adapter_observation") is None
                and retrieval == completed
                and direct.get("http_status") == 200
                and isinstance(capture.get("unretained_response_measurement"), Mapping)
                and capture.get("source_bytes_exposed_to_reiyah_observer") is True
            ):
                raise GateError(
                    "GA12-PUBLICATION-EVENT-ACTUAL-REFERENCE-BINDING",
                    "NIST capture mode operands contradict the static direct-HTTP contract",
                )
        else:
            raise GateError(
                "GA12-PUBLICATION-EVENT-ACTUAL-REFERENCE-BINDING",
                f"capture mode is not predeclared: {path}",
            )
        item = snapshot.files[path]
        captures.append(capture)
        completion_times.append(completed)
        bindings.append(
            {
                "artifact_id": capture["artifact_id"],
                "path": path,
                "sha256": f"sha256:{item.sha256}",
                "byte_size": item.size,
                "schema_id": capture["schema_id"],
                "version": capture["version"],
            }
        )
    return captures, bindings, completion_times


def validate_actual_publication_event_state(
    snapshot: RepositorySnapshot,
    dependencies: Mapping[str, Any],
    plan: Mapping[str, Any],
    candidate: CandidateProjection,
    index_bytes: bytes,
) -> dict[str, Any]:
    if (
        snapshot.mode != "release"
        or snapshot.commit is None
        or snapshot.object_format is None
    ):
        raise GateError(
            "GA12-PUBLICATION-EVENT-ACTUAL-TOPOLOGY",
            "actual publication-event validation requires an immutable release snapshot",
        )
    topology = plan.get("static_publication_topology")
    protocol = strict_json(
        snapshot.read(PROTOCOL_MANIFEST_PATH), PROTOCOL_MANIFEST_PATH
    )
    if not isinstance(topology, Mapping) or not isinstance(protocol, Mapping):
        raise GateError(
            "GA12-PUBLICATION-EVENT-STATIC-CONTRACT",
            "plan/protocol publication topology is absent",
        )
    if protocol.get("static_publication_topology") != topology:
        raise GateError(
            "GA12-PUBLICATION-EVENT-STATIC-CONTRACT",
            "plan and protocol static publication topology differ",
        )
    rights_declaration = governance_mapping(topology.get("rights_revalidation"))
    receipt_declaration = governance_mapping(topology.get("publisher_receipt"))
    if not (
        rights_declaration is not None
        and receipt_declaration is not None
        and rights_declaration.get("artifact_path") == ACTUAL_PUBLIC_RIGHTS_PATH
        and receipt_declaration.get("artifact_path") == ACTUAL_PUBLIC_RECEIPT_PATH
    ):
        raise GateError(
            "GA12-PUBLICATION-EVENT-STATIC-CONTRACT",
            "event artifact paths differ from the closed publication topology",
        )
    captures, capture_bindings, capture_times = validate_actual_capture_manifests(
        snapshot, dependencies, topology
    )
    rights_present = ACTUAL_PUBLIC_RIGHTS_PATH in snapshot.files
    receipt_present = ACTUAL_PUBLIC_RECEIPT_PATH in snapshot.files
    validate_actual_publication_event_guard(
        actual_publication_event_guard_operands(
            rights_present=rights_present,
            receipt_present=receipt_present,
        )
    )
    if not rights_present:
        packet_complete = plan["canonical_report_path"] in snapshot.files
        return {
            "state": (
                "candidate_packet_event_artifacts_absent"
                if packet_complete
                else "prepacket_bootstrap_event_artifacts_absent"
            ),
            "distribution_event_id": topology["distribution_event_id"],
            "observed_snapshot_commit": snapshot.commit,
            "candidate_packet_commit": snapshot.commit if packet_complete else None,
            "receipt_bearing_commit": None,
            "event_artifact_count": 0,
            "capture_manifest_count": len(capture_bindings),
            "capture_manifest_bindings": capture_bindings,
            "transport_verification_state": "not_evaluated",
            "publisher_receipt_is_independent_verification": False,
        }

    rights = strict_json(
        snapshot.read(ACTUAL_PUBLIC_RIGHTS_PATH), ACTUAL_PUBLIC_RIGHTS_PATH
    )
    receipt = strict_json(
        snapshot.read(ACTUAL_PUBLIC_RECEIPT_PATH), ACTUAL_PUBLIC_RECEIPT_PATH
    )
    if not isinstance(rights, Mapping) or not isinstance(receipt, Mapping):
        raise GateError(
            "GA12-PUBLICATION-EVENT-ACTUAL-SCHEMA",
            "actual rights and receipt artifacts must be objects",
        )
    validate_actual_publication_schema(
        snapshot,
        dependencies,
        PUBLIC_RIGHTS_SCHEMA_PATH,
        rights,
        "GA12-PUBLICATION-EVENT-ACTUAL-SCHEMA",
    )
    validate_actual_publication_schema(
        snapshot,
        dependencies,
        PUBLIC_DISTRIBUTION_RECEIPT_SCHEMA_PATH,
        receipt,
        "GA12-PUBLICATION-EVENT-ACTUAL-SCHEMA",
    )
    validate_actual_publication_event_guard(
        actual_publication_event_guard_operands(
            rights_preflight_eligible=actual_rights_preflight_eligible(
                rights.get("all_included_payloads_covered"),
                rights.get("preflight_outcome"),
            )
        )
    )

    basis_observations = rights.get("basis_observations")
    if not isinstance(basis_observations, list) or len(basis_observations) != 2:
        raise GateError(
            "GA12-PUBLICATION-EVENT-ACTUAL-REFERENCE-BINDING",
            "rights record does not bind the exact two capture observations",
        )
    for capture, binding, basis in zip(
        captures, capture_bindings, basis_observations, strict=True
    ):
        if not isinstance(basis, Mapping) or not (
            basis.get("capture_manifest_ref") == binding
            and basis.get("basis_id") == capture.get("basis_id")
            and basis.get("publisher") == capture.get("publisher")
            and basis.get("official_url") == capture.get("requested_url")
            and basis.get("observation_mode") == capture.get("observation_mode")
            and basis.get("observed_at") == capture.get("observation_completed_at")
            and basis.get("observation_completed_at")
            == capture.get("observation_completed_at")
            and basis.get("related_source_ids") == capture.get("related_source_ids")
        ):
            validate_actual_publication_event_guard(
                actual_publication_event_guard_operands(reference_bindings_equal=False)
            )

    rights_ref = governance_mapping(receipt.get("rights_revalidation_ref"))
    index_ref = governance_mapping(receipt.get("published_index_ref"))
    report_ref = governance_mapping(receipt.get("validation_report_ref"))
    intended = governance_mapping(rights.get("intended_distribution"))
    intended_index = (
        governance_mapping(intended.get("index_ref")) if intended is not None else None
    )
    intended_report = (
        governance_mapping(intended.get("validation_report_ref"))
        if intended is not None
        else None
    )
    if not all(
        item is not None
        for item in (
            rights_ref,
            index_ref,
            report_ref,
            intended,
            intended_index,
            intended_report,
        )
    ):
        validate_actual_publication_event_guard(
            actual_publication_event_guard_operands(reference_bindings_equal=False)
        )
    assert rights_ref is not None
    assert index_ref is not None
    assert report_ref is not None
    assert intended is not None
    assert intended_index is not None
    assert intended_report is not None
    initial_byte_bindings_equal = all(
        actual_artifact_reference_matches(snapshot, reference, path)
        for reference, path in (
            (rights_ref, ACTUAL_PUBLIC_RIGHTS_PATH),
            (index_ref, plan["index_path"]),
            (report_ref, plan["canonical_report_path"]),
        )
    )
    validate_actual_publication_event_guard(
        actual_publication_event_guard_operands(
            byte_bindings_equal=initial_byte_bindings_equal,
        )
    )
    for field, expected_path in (
        ("custody_profile_ref", "evidence/public-evidence-custody-profile-1.1.0.json"),
        ("source_ledger_ref", "evidence/source-ledger-1.1.0.json"),
        (
            "frontier_discovery_register_ref",
            "evidence/frontier-discovery-register-1.1.0.json",
        ),
        (
            "distribution_inventory_ref",
            "evidence/public-distribution-inventory-1.1.0.json",
        ),
        ("prior_receipt_ref", PREDECESSOR_RECEIPT_PATH),
    ):
        reference = governance_mapping(receipt.get(field))
        if reference is None:
            raise GateError(
                "GA12-PUBLICATION-EVENT-ACTUAL-REFERENCE-BINDING",
                f"actual receipt lacks {field}",
            )
        validate_actual_publication_event_guard(
            actual_publication_event_guard_operands(
                byte_bindings_equal=actual_artifact_reference_matches(
                    snapshot, reference, expected_path
                ),
            )
        )
    prior_observation = governance_mapping(rights.get("prior_observation_ref"))
    if prior_observation is None:
        raise GateError(
            "GA12-PUBLICATION-EVENT-ACTUAL-REFERENCE-BINDING",
            "actual rights record lacks prior observation custody",
        )
    validate_actual_publication_event_guard(
        actual_publication_event_guard_operands(
            byte_bindings_equal=actual_artifact_reference_matches(
                snapshot,
                prior_observation,
                "evidence/public-rights-revalidation-2026-08-24-1.1.2.json",
            ),
        )
    )

    ledger = strict_json(
        snapshot.read("evidence/source-ledger-1.1.0.json"),
        "evidence/source-ledger-1.1.0.json",
    )
    ledger_records = ledger.get("records") if isinstance(ledger, Mapping) else None
    distributed = receipt.get("distributed_payloads")
    if not isinstance(ledger_records, list) or not isinstance(distributed, list):
        raise GateError(
            "GA12-PUBLICATION-EVENT-ACTUAL-REFERENCE-BINDING",
            "receipt payload/source-ledger operands are malformed",
        )
    retained_by_id = {
        row.get("source_id"): row.get("retained_payload")
        for row in ledger_records
        if isinstance(row, Mapping) and row.get("retained_payload") is not None
    }
    for payload_row in distributed:
        source_ref = (
            governance_mapping(payload_row.get("source_ref"))
            if isinstance(payload_row, Mapping)
            else None
        )
        payload_ref = (
            governance_mapping(payload_row.get("payload"))
            if isinstance(payload_row, Mapping)
            else None
        )
        source_id = source_ref.get("source_id") if source_ref else None
        if payload_ref is None or retained_by_id.get(source_id) != payload_ref:
            raise GateError(
                "GA12-PUBLICATION-EVENT-ACTUAL-REFERENCE-BINDING",
                f"distributed payload differs from source-ledger custody: {source_id}",
            )
        validate_actual_publication_event_guard(
            actual_publication_event_guard_operands(
                byte_bindings_equal=actual_artifact_reference_matches(
                    snapshot, payload_ref, str(payload_ref.get("path"))
                ),
            )
        )

    parent_line = (
        run_git(["rev-list", "--parents", "-n", "1", snapshot.commit])
        .decode("ascii", "strict")
        .strip()
        .split()
    )
    if len(parent_line) != 2 or parent_line[0] != snapshot.commit:
        validate_actual_publication_event_guard(
            actual_publication_event_guard_operands(parent_packet_binding_equal=False)
        )
    parent_commit = parent_line[1]
    if not (
        receipt.get("published_git_commit") == parent_commit
        and intended.get("candidate_git_commit") == parent_commit
        and parent_commit != snapshot.commit
    ):
        validate_actual_publication_event_guard(
            actual_publication_event_guard_operands(parent_packet_binding_equal=False)
        )
    parent_snapshot = immutable_git_snapshot_at_commit(
        parent_commit, snapshot.object_format
    )
    event_paths = {ACTUAL_PUBLIC_RIGHTS_PATH, ACTUAL_PUBLIC_RECEIPT_PATH}
    added_paths = set(snapshot.files) - set(parent_snapshot.files)
    removed_paths = set(parent_snapshot.files) - set(snapshot.files)
    changed_paths = {
        path
        for path in set(snapshot.files) & set(parent_snapshot.files)
        if (
            snapshot.files[path].mode != parent_snapshot.files[path].mode
            or snapshot.files[path].data != parent_snapshot.files[path].data
        )
    }
    if (
        added_paths != event_paths
        or removed_paths
        or changed_paths
        or event_paths & set(parent_snapshot.files)
    ):
        validate_actual_publication_event_guard(
            actual_publication_event_guard_operands(event_delta_exact=False)
        )
    parent_plan = strict_json(parent_snapshot.read(PLAN_PATH), PLAN_PATH)
    if parent_plan != plan or not isinstance(parent_plan, Mapping):
        validate_actual_publication_event_guard(
            actual_publication_event_guard_operands(candidate_projection_equal=False)
        )
    parent_candidate = candidate_projection(parent_snapshot, parent_plan)
    if parent_candidate.serialized != candidate.serialized:
        validate_actual_publication_event_guard(
            actual_publication_event_guard_operands(candidate_projection_equal=False)
        )
    index_equal = plan["index_path"] in parent_snapshot.files and parent_snapshot.read(
        plan["index_path"]
    ) == snapshot.read(plan["index_path"])
    report_equal = plan[
        "canonical_report_path"
    ] in parent_snapshot.files and parent_snapshot.read(
        plan["canonical_report_path"]
    ) == snapshot.read(plan["canonical_report_path"])
    validate_actual_publication_event_guard(
        actual_publication_event_guard_operands(
            canonical_index_equal=index_equal,
            canonical_report_equal=report_equal,
        )
    )
    if snapshot.read(plan["index_path"]) != index_bytes:
        validate_actual_publication_event_guard(
            actual_publication_event_guard_operands(canonical_index_equal=False)
        )

    report = strict_json(
        snapshot.read(plan["canonical_report_path"]),
        plan["canonical_report_path"],
    )
    report_index_binding = (
        governance_mapping(report.get("index_binding"))
        if isinstance(report, Mapping)
        else None
    )
    if not (
        report_index_binding is not None
        and all(
            report_index_binding.get(key) == index_ref.get(key)
            for key in ("path", "sha256", "byte_size")
        )
    ):
        validate_actual_publication_event_guard(
            actual_publication_event_guard_operands(reference_bindings_equal=False)
        )
    rights_item = snapshot.files[ACTUAL_PUBLIC_RIGHTS_PATH]
    expected_rights_ref = {
        "artifact_id": rights.get("artifact_id"),
        "path": ACTUAL_PUBLIC_RIGHTS_PATH,
        "sha256": f"sha256:{rights_item.sha256}",
        "byte_size": rights_item.size,
        "schema_id": rights.get("schema_id"),
        "version": rights.get("version"),
    }
    readback = governance_mapping(receipt.get("remote_readback_assertion"))
    if not (
        rights_ref == expected_rights_ref
        and intended_index == index_ref
        and intended_report == report_ref
        and intended.get("distribution_event_id")
        == rights.get("distribution_event_id")
        == receipt.get("distribution_event_id")
        == topology.get("distribution_event_id")
        and intended.get("repository_url") == receipt.get("published_repository_url")
        and intended.get("repository_ref") == receipt.get("published_ref")
        and intended.get("mission_release_id") == receipt.get("mission_release_id")
        and intended.get("protocol_release_id") == receipt.get("protocol_release_id")
        and readback is not None
        and readback.get("observed_repository_url")
        == receipt.get("published_repository_url")
        and readback.get("observed_ref") == receipt.get("published_ref")
        and readback.get("observed_git_commit") == parent_commit
        and readback.get("observed_index_sha256") == index_ref.get("sha256")
        and readback.get("observed_validation_report_sha256")
        == report_ref.get("sha256")
        and receipt.get("transport_verification_state") == "asserted_unverified"
        and receipt.get("transport_verification_record_ref") is None
    ):
        validate_actual_publication_event_guard(
            actual_publication_event_guard_operands(reference_bindings_equal=False)
        )

    rights_observed = governance_time(rights.get("observed_at"))
    authorization = governance_mapping(receipt.get("distribution_authorization"))
    authorized_at = (
        governance_time(authorization.get("observed_at"))
        if authorization is not None
        else None
    )
    published_at = governance_time(receipt.get("published_at"))
    readback_at = (
        governance_time(readback.get("asserted_at")) if readback is not None else None
    )
    recorded_at = governance_time(receipt.get("recorded_at"))
    oldest_capture = min(capture_times)
    age_seconds = (
        (published_at - oldest_capture).total_seconds()
        if published_at is not None
        else None
    )
    if not (
        rights_observed is not None
        and authorized_at is not None
        and published_at is not None
        and readback_at is not None
        and recorded_at is not None
        and all(completed <= rights_observed for completed in capture_times)
        and rights_observed
        <= authorized_at
        <= published_at
        <= readback_at
        <= recorded_at
        and age_seconds is not None
        and age_seconds >= 0
        and age_seconds <= 3600
        and age_seconds.is_integer()
        and receipt.get("oldest_capture_age_seconds") == int(age_seconds)
    ):
        validate_actual_publication_event_guard(
            actual_publication_event_guard_operands(chronology_valid=False)
        )

    return {
        "state": "direct_child_event_artifacts_validated",
        "distribution_event_id": topology["distribution_event_id"],
        "candidate_packet_commit": parent_commit,
        "receipt_bearing_commit": snapshot.commit,
        "event_artifact_count": 2,
        "capture_manifest_count": len(capture_bindings),
        "capture_manifest_bindings": capture_bindings,
        "rights_binding": expected_rights_ref,
        "receipt_binding": {
            "artifact_id": receipt["artifact_id"],
            "path": ACTUAL_PUBLIC_RECEIPT_PATH,
            "sha256": (f"sha256:{snapshot.files[ACTUAL_PUBLIC_RECEIPT_PATH].sha256}"),
            "byte_size": snapshot.files[ACTUAL_PUBLIC_RECEIPT_PATH].size,
            "schema_id": receipt["schema_id"],
            "version": receipt["version"],
        },
        "candidate_projection_byte_identical": True,
        "canonical_index_byte_identical": True,
        "canonical_report_byte_identical": True,
        "transport_verification_state": "asserted_unverified",
        "publisher_receipt_is_independent_verification": False,
    }


def replace_json_pointer(base: Any, mutation: Mapping[str, Any]) -> Any:
    if (
        set(mutation) != {"operation", "json_pointer", "value"}
        or mutation.get("operation") != "replace"
    ):
        raise GateError(
            "GA12-GOVERNANCE-MUTATION-SHAPE",
            "governance fixtures permit exactly one RFC 6901 replace mutation",
        )
    pointer = mutation.get("json_pointer")
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise GateError(
            "GA12-GOVERNANCE-MUTATION-POINTER",
            "governance mutation pointer must be non-root",
        )

    tokens: list[str] = []
    for encoded in pointer[1:].split("/"):
        token = ""
        index = 0
        while index < len(encoded):
            if encoded[index] != "~":
                token += encoded[index]
                index += 1
                continue
            if index + 1 >= len(encoded) or encoded[index + 1] not in {"0", "1"}:
                raise GateError(
                    "GA12-GOVERNANCE-MUTATION-POINTER", "invalid RFC 6901 escape"
                )
            token += "~" if encoded[index + 1] == "0" else "/"
            index += 2
        tokens.append(token)

    result = copy.deepcopy(base)
    parent = result
    for token in tokens[:-1]:
        if isinstance(parent, list):
            if not token.isdigit() or (len(token) > 1 and token.startswith("0")):
                raise GateError(
                    "GA12-GOVERNANCE-MUTATION-POINTER", "invalid array index"
                )
            index = int(token)
            if index >= len(parent):
                raise GateError(
                    "GA12-GOVERNANCE-MUTATION-POINTER",
                    "array index is outside baseline",
                )
            parent = parent[index]
        elif isinstance(parent, dict) and token in parent:
            parent = parent[token]
        else:
            raise GateError(
                "GA12-GOVERNANCE-MUTATION-POINTER", "mutation parent is absent"
            )
    token = tokens[-1]
    if isinstance(parent, list):
        if not token.isdigit() or (len(token) > 1 and token.startswith("0")):
            raise GateError(
                "GA12-GOVERNANCE-MUTATION-POINTER", "invalid replacement array index"
            )
        index = int(token)
        if index >= len(parent):
            raise GateError(
                "GA12-GOVERNANCE-MUTATION-POINTER", "replacement array index is absent"
            )
        parent[index] = copy.deepcopy(mutation["value"])
    elif isinstance(parent, dict):
        if token not in parent:
            raise GateError(
                "GA12-GOVERNANCE-MUTATION-POINTER", "replacement property is absent"
            )
        parent[token] = copy.deepcopy(mutation["value"])
    else:
        raise GateError(
            "GA12-GOVERNANCE-MUTATION-POINTER", "replacement parent is scalar"
        )
    return result


def governance_schema_validators(
    snapshot: RepositorySnapshot,
    dependencies: Mapping[str, Any],
) -> dict[str, Any]:
    resource_paths = tuple(
        sorted(
            path
            for path in snapshot.files
            if path.startswith("schemas/") and path.endswith(".schema.json")
        )
    )
    schema_paths = (
        GOVERNANCE_POSITIVE_SCHEMA_PATH,
        PUBLICATION_EVENT_SCHEMA_PATH,
        PUBLICATION_EVENT_MUTATION_SCHEMA_PATH,
        TRANSPORT_OBSERVATION_SCHEMA_PATH,
        TRANSPORT_OBSERVATION_MUTATION_SCHEMA_PATH,
    )
    return {
        path: validator_for_schema(snapshot, dependencies, path, resource_paths)
        for path in schema_paths
    }


def apply_governance_fixture_mutations(
    baseline: Mapping[str, Any],
    fixture: Mapping[str, Any],
) -> dict[str, Any]:
    has_one = isinstance(fixture.get("mutation"), Mapping)
    has_many = isinstance(fixture.get("mutations"), list)
    if has_one == has_many:
        raise GateError(
            "GA12-GOVERNANCE-MUTATION-SHAPE",
            "typed governance fixture must declare exactly one of mutation or mutations",
        )
    mutations = [fixture["mutation"]] if has_one else fixture["mutations"]
    if not mutations or not all(isinstance(item, Mapping) for item in mutations):
        raise GateError(
            "GA12-GOVERNANCE-MUTATION-SHAPE",
            "typed governance mutation list must be a non-empty object sequence",
        )
    pointers = [item.get("json_pointer") for item in mutations]
    if len(pointers) != len(set(pointers)):
        raise GateError(
            "GA12-GOVERNANCE-MUTATION-POINTER",
            "typed governance mutation pointers must be unique",
        )
    result: Any = copy.deepcopy(baseline)
    for mutation in mutations:
        result = replace_json_pointer(result, mutation)
    if not isinstance(result, dict):
        raise GateError(
            "GA12-GOVERNANCE-MUTATION-SHAPE",
            "typed governance mutation changed the baseline root type",
        )
    return result


def governance_mapping(value: object) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def exact_reference_fields(
    reference: object,
    expected: Mapping[str, Any],
    fields: Sequence[str],
) -> bool:
    return isinstance(reference, Mapping) and all(
        reference.get(field) == expected.get(field) for field in fields
    )


def publication_event_violations(
    snapshot: RepositorySnapshot,
    event: Mapping[str, Any],
    positive_wrappers: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    """Return the exact primary synthetic publication-governance diagnostic.

    This resolver proves only the internal consistency and byte custody of typed
    synthetic fixtures.  Observer assertions and wrapper records remain
    non-authoritative, evidence-ineligible, and incapable of establishing a real
    distribution event, legal conclusion, Gate A acceptance, or runtime authority.
    """
    capture_envelopes = event.get("capture_manifests")
    rights_envelope = governance_mapping(event.get("rights_revalidation"))
    receipt = governance_mapping(event.get("publisher_receipt"))
    topology = governance_mapping(event.get("topology_observation"))
    if not (
        isinstance(capture_envelopes, list)
        and len(capture_envelopes) == 2
        and all(isinstance(item, Mapping) for item in capture_envelopes)
        and rights_envelope is not None
        and receipt is not None
        and topology is not None
    ):
        return ["GA12-CAPTURE-SCHEMA-BINDING"]

    capture_records = [
        governance_mapping(envelope.get("record")) for envelope in capture_envelopes
    ]
    if any(record is None for record in capture_records):
        return ["GA12-CAPTURE-SCHEMA-BINDING"]
    captures = [record for record in capture_records if record is not None]

    # Mode-specific capture chronology is independent of later event chronology.
    capture_times: list[datetime] = []
    for capture in captures:
        started = governance_time(capture.get("observation_started_at"))
        completed = governance_time(capture.get("observation_completed_at"))
        direct = governance_mapping(capture.get("direct_http_attempt"))
        retrieval = (
            governance_time(direct.get("retrieval_completed_at")) if direct else None
        )
        mode = capture.get("observation_mode")
        invalid = (
            started is None
            or completed is None
            or retrieval is None
            or not started <= retrieval <= completed
        )
        if mode == "adapter_observation_with_blocked_direct_attempt":
            adapter = governance_mapping(capture.get("adapter_observation"))
            adapter_completed = (
                governance_time(adapter.get("observation_completed_at"))
                if adapter
                else None
            )
            invalid = (
                invalid
                or adapter_completed != completed
                or retrieval > adapter_completed
            )
        elif mode == "direct_http_metadata_digest":
            invalid = (
                invalid
                or capture.get("adapter_observation") is not None
                or retrieval != completed
            )
        else:
            invalid = True
        if invalid:
            return ["GA12-CAPTURE-CHRONOLOGY"]
        capture_times.append(completed)

    rights = governance_mapping(rights_envelope.get("record"))
    if rights is None:
        return ["GA12-RIGHTS-CAPTURE-BINDING"]
    basis_observations = rights.get("basis_observations")
    if not isinstance(basis_observations, list) or len(basis_observations) != len(
        captures
    ):
        return ["GA12-RIGHTS-CAPTURE-BINDING"]
    captures_by_basis = {
        capture.get("basis_id"): (envelope, capture)
        for envelope, capture in zip(capture_envelopes, captures, strict=True)
    }
    if len(captures_by_basis) != len(captures):
        return ["GA12-RIGHTS-CAPTURE-BINDING"]
    capture_ref_fields = (
        "artifact_id",
        "path",
        "sha256",
        "byte_size",
        "schema_id",
        "version",
    )
    for basis in basis_observations:
        if (
            not isinstance(basis, Mapping)
            or basis.get("basis_id") not in captures_by_basis
        ):
            return ["GA12-RIGHTS-CAPTURE-BINDING"]
        envelope, capture = captures_by_basis[basis["basis_id"]]
        expected_capture_ref = {
            "artifact_id": capture.get("artifact_id"),
            "path": envelope.get("path"),
            "sha256": envelope.get("sha256"),
            "byte_size": envelope.get("byte_size"),
            "schema_id": capture.get("schema_id"),
            "version": capture.get("version"),
        }
        binding_invalid = not (
            envelope.get("path") == capture.get("artifact_path")
            and exact_reference_fields(
                basis.get("capture_manifest_ref"),
                expected_capture_ref,
                capture_ref_fields,
            )
            and basis.get("publisher") == capture.get("publisher")
            and basis.get("official_url") == capture.get("requested_url")
            and basis.get("observation_mode") == capture.get("observation_mode")
            and basis.get("observed_at") == capture.get("observation_completed_at")
            and basis.get("observation_completed_at")
            == capture.get("observation_completed_at")
            and basis.get("related_source_ids") == capture.get("related_source_ids")
            and capture.get("distribution_event_id")
            == rights.get("distribution_event_id")
        )
        if binding_invalid:
            return ["GA12-RIGHTS-CAPTURE-BINDING"]

    published_at = governance_time(receipt.get("published_at"))
    freshness_policy = governance_mapping(rights.get("freshness_policy"))
    oldest_capture = min(capture_times)
    age_seconds = (
        (published_at - oldest_capture).total_seconds()
        if published_at is not None
        else None
    )
    if not (
        freshness_policy is not None
        and isinstance(freshness_policy.get("maximum_age_seconds"), int)
        and isinstance(receipt.get("oldest_capture_age_seconds"), int)
        and age_seconds is not None
        and age_seconds >= 0
        and age_seconds == receipt.get("oldest_capture_age_seconds")
        and age_seconds <= freshness_policy["maximum_age_seconds"]
    ):
        return ["GA12-RIGHTS-CAPTURE-FRESHNESS"]

    receipt_state_invalid = not (
        topology.get("receipt_bearing_parent_commit")
        == topology.get("candidate_packet_commit")
        and topology.get("receipt_bearing_commit")
        != topology.get("candidate_packet_commit")
        and topology.get("receipt_commit_contains_rights") is True
        and topology.get("receipt_commit_contains_receipt") is True
        and topology.get("candidate_projection_sha256_before")
        == topology.get("candidate_projection_sha256_after")
        and topology.get("canonical_index_sha256_before")
        == topology.get("canonical_index_sha256_after")
        and topology.get("canonical_report_sha256_before")
        == topology.get("canonical_report_sha256_after")
    )
    if receipt_state_invalid:
        return ["GA12-PUBLICATION-TOPOLOGY-RECEIPT-STATE"]

    rights_observed = governance_time(rights.get("observed_at"))
    distribution_authorization = governance_mapping(
        receipt.get("distribution_authorization")
    )
    authorized_at = (
        governance_time(distribution_authorization.get("observed_at"))
        if distribution_authorization
        else None
    )
    readback = governance_mapping(receipt.get("remote_readback_assertion"))
    readback_at = governance_time(readback.get("asserted_at")) if readback else None
    recorded_at = governance_time(receipt.get("recorded_at"))
    if not (
        rights_observed is not None
        and authorized_at is not None
        and published_at is not None
        and readback_at is not None
        and recorded_at is not None
        and all(completed <= rights_observed for completed in capture_times)
        and rights_observed
        <= authorized_at
        <= published_at
        <= readback_at
        <= recorded_at
    ):
        return ["GA12-PUBLICATION-EVENT-CHRONOLOGY"]

    intended = governance_mapping(rights.get("intended_distribution"))
    rights_ref = governance_mapping(receipt.get("rights_revalidation_ref"))
    index_ref = governance_mapping(receipt.get("published_index_ref"))
    report_ref = governance_mapping(receipt.get("validation_report_ref"))
    intended_index = governance_mapping(intended.get("index_ref")) if intended else None
    intended_report = (
        governance_mapping(intended.get("validation_report_ref")) if intended else None
    )
    rights_expected_ref = {
        "artifact_id": rights.get("artifact_id"),
        "path": rights_envelope.get("path"),
        "sha256": rights_envelope.get("sha256"),
        "byte_size": rights_envelope.get("byte_size"),
        "schema_id": rights.get("schema_id"),
        "version": rights.get("version"),
    }
    binding_invalid = not (
        intended is not None
        and rights_ref is not None
        and index_ref is not None
        and report_ref is not None
        and intended_index == index_ref
        and intended_report == report_ref
        and exact_reference_fields(rights_ref, rights_expected_ref, capture_ref_fields)
        and rights_envelope.get("path") == rights.get("artifact_path")
        and intended.get("distribution_event_id")
        == rights.get("distribution_event_id")
        == receipt.get("distribution_event_id")
        == topology.get("distribution_event_id")
        and intended.get("repository_url") == receipt.get("published_repository_url")
        and intended.get("repository_ref") == receipt.get("published_ref")
        and intended.get("candidate_git_commit")
        == receipt.get("published_git_commit")
        == topology.get("candidate_packet_commit")
        == topology.get("receipt_published_git_commit")
        and intended.get("mission_release_id") == receipt.get("mission_release_id")
        and intended.get("protocol_release_id") == receipt.get("protocol_release_id")
        and readback is not None
        and readback.get("observed_repository_url")
        == receipt.get("published_repository_url")
        and readback.get("observed_ref") == receipt.get("published_ref")
        and readback.get("observed_git_commit") == receipt.get("published_git_commit")
        and readback.get("observed_index_sha256") == index_ref.get("sha256")
        and readback.get("observed_validation_report_sha256")
        == report_ref.get("sha256")
        and topology.get("canonical_index_sha256_before") == index_ref.get("sha256")
        and topology.get("canonical_report_sha256_before") == report_ref.get("sha256")
        and topology.get("candidate_packet_capture_paths")
        == [envelope.get("path") for envelope in capture_envelopes]
    )
    if binding_invalid:
        return ["GA12-PUBLICATION-EVENT-BINDING"]

    references = event.get("governance_positive_fixture_refs")
    expected_roles = (
        "iso_capture_manifest",
        "nist_capture_manifest",
        "rights_revalidation",
        "publisher_receipt",
    )
    embedded_by_role: dict[str, Mapping[str, Any]] = {
        "iso_capture_manifest": captures[0],
        "nist_capture_manifest": captures[1],
        "rights_revalidation": rights,
        "publisher_receipt": receipt,
    }
    if not (
        isinstance(references, list)
        and [
            item.get("fixture_role") for item in references if isinstance(item, Mapping)
        ]
        == list(expected_roles)
    ):
        return ["GA12-GOVERNANCE-POSITIVE-BYTE-BINDING"]
    for reference in references:
        if not isinstance(reference, Mapping):
            return ["GA12-GOVERNANCE-POSITIVE-BYTE-BINDING"]
        path = reference.get("path")
        wrapper = positive_wrappers.get(path) if isinstance(path, str) else None
        if wrapper is None or path not in snapshot.files:
            return ["GA12-GOVERNANCE-POSITIVE-BYTE-BINDING"]
        item = snapshot.files[path]
        role = reference.get("fixture_role")
        expected_record = embedded_by_role.get(role) if isinstance(role, str) else None
        wrapper_invalid = not (
            reference.get("fixture_id") == wrapper.get("fixture_id")
            and reference.get("fixture_schema_id") == wrapper.get("schema_id")
            and reference.get("target_schema_id") == wrapper.get("target_schema_id")
            and reference.get("target_artifact_id") == wrapper.get("target_artifact_id")
            and reference.get("sha256") == f"sha256:{item.sha256}"
            and reference.get("byte_size") == item.size
            and wrapper.get("fixture_role") == role
            and wrapper.get("record") == expected_record
            and wrapper.get("target_artifact_id")
            == (expected_record.get("artifact_id") if expected_record else None)
        )
        if wrapper_invalid:
            return ["GA12-GOVERNANCE-POSITIVE-BYTE-BINDING"]
    return []


def transport_observation_violations(
    snapshot: RepositorySnapshot,
    fixture: Mapping[str, Any],
    publication_event: Mapping[str, Any],
) -> list[str]:
    """Return the exact primary synthetic transport-governance diagnostic.

    The nested independently-verified state is a schema operand only.  This
    resolver never converts a wrapper assertion into authenticated identity,
    retained external evidence, independent transport verification, or any
    scientific, publication, acceptance, legal, compliance, or runtime authority.
    """
    publication_ref = governance_mapping(fixture.get("publication_event_baseline_ref"))
    if (
        publication_ref is None
        or publication_ref.get("path") != PUBLICATION_EVENT_BASELINE_PATH
    ):
        return ["GA12-TRANSPORT-PUBLICATION-BYTE-BINDING"]
    actual_publication_bytes = snapshot.read(PUBLICATION_EVENT_BASELINE_PATH)
    publication_byte_invalid = not (
        publication_ref.get("fixture_id") == publication_event.get("fixture_id")
        and publication_ref.get("schema_id") == publication_event.get("schema_id")
        and publication_ref.get("sha256")
        == f"sha256:{hashlib.sha256(actual_publication_bytes).hexdigest()}"
        and publication_ref.get("byte_size") == len(actual_publication_bytes)
    )
    if publication_byte_invalid:
        return ["GA12-TRANSPORT-PUBLICATION-BYTE-BINDING"]

    receipt_operand = governance_mapping(fixture.get("publication_receipt_operand"))
    publication_receipt = governance_mapping(publication_event.get("publisher_receipt"))
    publication_topology = governance_mapping(
        publication_event.get("topology_observation")
    )
    transport_operand = governance_mapping(fixture.get("transport_record_operand"))
    transport = (
        governance_mapping(transport_operand.get("record"))
        if transport_operand is not None
        else None
    )
    if not (
        receipt_operand is not None
        and publication_receipt is not None
        and publication_topology is not None
        and transport_operand is not None
        and transport is not None
    ):
        return ["GA12-TRANSPORT-PUBLICATION-BINDING"]

    selected_topology = governance_mapping(receipt_operand.get("selected_topology"))
    selected_keys = (
        "artifact_id",
        "receipt_id",
        "schema_id",
        "version",
        "distribution_event_id",
        "published_repository_url",
        "published_ref",
        "published_git_commit",
        "published_index_ref",
        "validation_report_ref",
        "published_at",
        "recorded_at",
    )
    expected_selected = {key: publication_receipt.get(key) for key in selected_keys}
    receipt_ref = governance_mapping(transport.get("receipt_ref"))
    receipt_binding_fields = (
        "artifact_id",
        "path",
        "sha256",
        "byte_size",
        "schema_id",
        "version",
    )
    publication_positive_refs = publication_event.get(
        "governance_positive_fixture_refs"
    )
    publisher_positive_ids = (
        {
            item.get("fixture_id")
            for item in publication_positive_refs
            if isinstance(item, Mapping)
            and item.get("fixture_role") == "publisher_receipt"
        }
        if isinstance(publication_positive_refs, list)
        else set()
    )
    publication_binding_invalid = not (
        selected_topology == expected_selected
        and receipt_operand.get("source_fixture_id")
        == publication_event.get("fixture_id")
        and receipt_operand.get("source_record_pointer") == "/publisher_receipt"
        and receipt_operand.get("source_positive_fixture_id") in publisher_positive_ids
        and receipt_operand.get("artifact_id") == publication_receipt.get("artifact_id")
        and receipt_operand.get("schema_id") == publication_receipt.get("schema_id")
        and receipt_operand.get("version") == publication_receipt.get("version")
        and exact_reference_fields(receipt_ref, receipt_operand, receipt_binding_fields)
        and publication_topology.get("distribution_event_id")
        == publication_receipt.get("distribution_event_id")
        and publication_topology.get("candidate_packet_commit")
        == publication_receipt.get("published_git_commit")
        and publication_topology.get("receipt_published_git_commit")
        == publication_receipt.get("published_git_commit")
        and publication_topology.get("canonical_index_sha256_before")
        == publication_receipt.get("published_index_ref", {}).get("sha256")
        and publication_topology.get("canonical_report_sha256_before")
        == publication_receipt.get("validation_report_ref", {}).get("sha256")
        and transport.get("distribution_event_id")
        == publication_receipt.get("distribution_event_id")
        and transport.get("repository_url")
        == publication_receipt.get("published_repository_url")
        and transport.get("repository_ref") == publication_receipt.get("published_ref")
        and transport.get("observed_git_commit")
        == publication_receipt.get("published_git_commit")
        and transport.get("index_ref") == publication_receipt.get("published_index_ref")
        and transport.get("validation_report_ref")
        == publication_receipt.get("validation_report_ref")
    )
    if publication_binding_invalid:
        return ["GA12-TRANSPORT-PUBLICATION-BINDING"]

    authorization_operand = governance_mapping(fixture.get("authorization_operand"))
    authorization = (
        governance_mapping(authorization_operand.get("record"))
        if authorization_operand is not None
        else None
    )
    authorization_ref = governance_mapping(transport.get("authorization_record_ref"))
    expected_authorization_ref = {
        "artifact_id": authorization.get("artifact_id") if authorization else None,
        "authorization_id": authorization.get("authorization_id")
        if authorization
        else None,
        "path": authorization_operand.get("artifact_path")
        if authorization_operand
        else None,
        "sha256": authorization_operand.get("sha256")
        if authorization_operand
        else None,
        "byte_size": authorization_operand.get("byte_size")
        if authorization_operand
        else None,
        "schema_id": authorization_operand.get("target_schema_id")
        if authorization_operand
        else None,
        "version": authorization.get("version") if authorization else None,
    }
    authorization_ref_fields = (
        "artifact_id",
        "authorization_id",
        "path",
        "sha256",
        "byte_size",
        "schema_id",
        "version",
    )
    authorization_invalid = not (
        authorization_operand is not None
        and authorization is not None
        and authorization_ref is not None
        and exact_reference_fields(
            authorization_ref,
            expected_authorization_ref,
            authorization_ref_fields,
        )
        and authorization_operand.get("target_schema_id")
        == authorization.get("schema_id")
        and authorization.get("authorized_transport_record_id")
        == transport.get("record_id")
        and authorization.get("distribution_event_id")
        == transport.get("distribution_event_id")
        and authorization.get("mission_release_id")
        == transport.get("mission_release_id")
        == MISSION_RELEASE_ID
        and authorization.get("protocol_release_id")
        == transport.get("protocol_release_id")
        == PROTOCOL_RELEASE_ID
        and authorization.get("repository_url") == transport.get("repository_url")
        and authorization.get("repository_ref") == transport.get("repository_ref")
        and authorization.get("authorized_git_commit")
        == transport.get("observed_git_commit")
        and authorization.get("index_ref") == transport.get("index_ref")
        and authorization.get("validation_report_ref")
        == transport.get("validation_report_ref")
        and authorization.get("authorization_scope")
        == "one_independent_static_transport_observation"
        and authorization.get("single_use") is True
        and authorization.get("authorizer_identity_authentication_state")
        == "independently_authenticated"
    )
    if authorization_invalid:
        return ["GA12-TRANSPORT-AUTHORIZATION-BINDING"]

    observer = governance_mapping(transport.get("observer"))
    if (
        observer is None
        or observer.get("identity_authentication_state")
        != "independently_authenticated"
    ):
        return ["GA12-TRANSPORT-OBSERVER-AUTHENTICATION"]
    identity_invalid = not (
        observer.get("independent_from_publisher") is True
        and observer.get("identity_separation_policy")
        == "observer_id_must_not_equal_publisher_identity"
        and isinstance(observer.get("observer_id"), str)
        and isinstance(observer.get("publisher_identity"), str)
        and observer.get("observer_id") != observer.get("publisher_identity")
    )
    if identity_invalid:
        return ["GA12-TRANSPORT-OBSERVER-IDENTITY-SEPARATION"]

    independence_basis = observer.get("independence_basis")
    stripped_basis = (
        independence_basis.strip() if isinstance(independence_basis, str) else ""
    )
    normalized_basis = " ".join(stripped_basis.casefold().split())
    prohibited_basis_fragments = (
        "publisher self-assertion",
        "placeholder",
        "same as publisher",
        "to be determined",
    )
    if (
        not 80 <= len(stripped_basis) <= 4000
        or normalized_basis in {"n/a", "na", "none", "tbd", "todo", "unknown"}
        or any(fragment in normalized_basis for fragment in prohibited_basis_fragments)
    ):
        return ["GA12-TRANSPORT-OBSERVER-INDEPENDENCE-BASIS"]

    retained_operands = fixture.get("retained_evidence_operands")
    observations = transport.get("observations")
    transport_evidence = transport.get("observation_evidence")
    evidence_invalid = not (
        isinstance(retained_operands, list)
        and isinstance(observations, list)
        and isinstance(transport_evidence, list)
        and all(isinstance(item, Mapping) for item in retained_operands)
        and all(isinstance(item, Mapping) for item in observations)
        and all(isinstance(item, Mapping) for item in transport_evidence)
    )
    retained_records: list[Mapping[str, Any]] = []
    if not evidence_invalid:
        for operand in retained_operands:
            payload = operand.get("payload")
            record = governance_mapping(operand.get("record"))
            if not isinstance(payload, str) or record is None:
                evidence_invalid = True
                break
            payload_bytes = payload.encode("utf-8")
            actual_digest = f"sha256:{hashlib.sha256(payload_bytes).hexdigest()}"
            if not (
                operand.get("payload_encoding") == "utf-8"
                and operand.get("payload_binding_scope") == "utf8_payload_string_bytes"
                and operand.get("payload_sha256") == actual_digest
                and operand.get("payload_byte_size") == len(payload_bytes)
                and record.get("sha256") == actual_digest
                and record.get("byte_size") == len(payload_bytes)
            ):
                evidence_invalid = True
                break
            retained_records.append(record)
    if not evidence_invalid:
        retained_ids = [record.get("evidence_id") for record in retained_records]
        transport_ids = [item.get("evidence_id") for item in transport_evidence]
        observation_ids = [item.get("observation_id") for item in observations]
        references = [
            reference
            for observation in observations
            for reference in observation.get("evidence_refs", [])
        ]
        evidence_invalid = not (
            all(isinstance(item, str) for item in retained_ids)
            and all(isinstance(item, str) for item in transport_ids)
            and all(isinstance(item, str) for item in observation_ids)
            and all(isinstance(item, str) for item in references)
            and len(retained_ids) == len(set(retained_ids))
            and len(transport_ids) == len(set(transport_ids))
            and len(observation_ids) == len(set(observation_ids))
            and set(retained_ids) == set(transport_ids) == set(references)
        )
        if not evidence_invalid:
            transport_evidence_by_id = {
                item["evidence_id"]: item for item in transport_evidence
            }
            evidence_invalid = any(
                transport_evidence_by_id.get(record["evidence_id"]) != record
                for record in retained_records
            )
    if evidence_invalid:
        return ["GA12-TRANSPORT-EVIDENCE-RESOLUTION"]

    evidence_times = {
        item["evidence_id"]: governance_time(item.get("captured_at"))
        for item in transport_evidence
    }
    reference_chronology_invalid = transport.get("reference_chronology_policy") != (
        "each_referenced_evidence_captured_at_lte_referencing_observation_observed_at"
    )
    if not reference_chronology_invalid:
        for observation in observations:
            observed_at = governance_time(observation.get("observed_at"))
            if observed_at is None or any(
                evidence_times.get(reference) is None
                or evidence_times[reference] > observed_at
                for reference in observation.get("evidence_refs", [])
            ):
                reference_chronology_invalid = True
                break
    if reference_chronology_invalid:
        return ["GA12-TRANSPORT-EVIDENCE-REFERENCE-CHRONOLOGY"]

    published_at = governance_time(publication_receipt.get("published_at"))
    receipt_recorded_at = governance_time(publication_receipt.get("recorded_at"))
    authorized_at = governance_time(authorization.get("authorized_at"))
    valid_until = governance_time(authorization.get("valid_until"))
    transport_observed_at = governance_time(transport.get("observed_at"))
    transport_recorded_at = governance_time(transport.get("recorded_at"))
    observation_times = [
        governance_time(item.get("observed_at")) for item in observations
    ]
    capture_times = [
        governance_time(item.get("captured_at")) for item in transport_evidence
    ]
    all_event_times = [*observation_times, *capture_times]
    chronology_invalid = (
        any(value is None for value in all_event_times)
        or published_at is None
        or receipt_recorded_at is None
        or authorized_at is None
        or valid_until is None
        or transport_observed_at is None
        or transport_recorded_at is None
        or not receipt_recorded_at <= authorized_at
        or not all(
            published_at < value for value in all_event_times if value is not None
        )
        or not all(
            authorized_at <= value for value in all_event_times if value is not None
        )
        or not all(
            value <= transport_observed_at
            for value in all_event_times
            if value is not None
        )
        or not transport_observed_at <= transport_recorded_at
        or not transport_observed_at <= valid_until
    )
    if chronology_invalid:
        return ["GA12-TRANSPORT-CHRONOLOGY"]
    return []


def governance_fixture_path(fixture_id: str) -> str:
    prefix = "reiyah.fixture.governance."
    suffix = "@1.2.0"
    if not fixture_id.startswith(prefix) or not fixture_id.endswith(suffix):
        raise GateError(
            "GA12-GOVERNANCE-FIXTURE-ID",
            f"governance fixture ID is outside the frozen namespace: {fixture_id}",
        )
    name = fixture_id[len(prefix) : -len(suffix)]
    return f"{GOVERNANCE_FIXTURE_PREFIX}{name}.json"


def require_schema_acceptance(
    validator: Any,
    instance: Any,
    path: str,
    diagnostic: str,
) -> None:
    errors = schema_error_records(validator, instance)
    if errors:
        first = errors[0]
        raise GateError(
            diagnostic,
            f"{path} failed {first['schema_keyword']} at "
            f"{first['instance_pointer']}: {first['message']}",
        )


def validate_governance_fixtures(
    snapshot: RepositorySnapshot,
    dependencies: Mapping[str, Any],
) -> dict[str, Any]:
    validators = governance_schema_validators(snapshot, dependencies)
    positive_paths = sorted(
        path
        for path in snapshot.files
        if path.startswith(GOVERNANCE_GOOD_PREFIX) and path.endswith(".json")
    )
    if set(positive_paths) != set(GOVERNANCE_POSITIVE_PATH_TO_ID):
        raise GateError(
            "GA12-GOVERNANCE-POSITIVE-SET",
            "typed publication positive fixture paths differ; "
            f"missing={sorted(set(GOVERNANCE_POSITIVE_PATH_TO_ID) - set(positive_paths))}, "
            f"unexpected={sorted(set(positive_paths) - set(GOVERNANCE_POSITIVE_PATH_TO_ID))}",
        )
    baseline_paths = sorted(
        path
        for path in snapshot.files
        if path.startswith(GOVERNANCE_BASELINE_PREFIX) and path.endswith(".json")
    )
    expected_baseline_paths = {
        PUBLICATION_EVENT_BASELINE_PATH,
        TRANSPORT_OBSERVATION_BASELINE_PATH,
    }
    if set(baseline_paths) != expected_baseline_paths:
        raise GateError(
            "GA12-GOVERNANCE-BASELINE-SET",
            "typed governance baseline paths differ; "
            f"missing={sorted(expected_baseline_paths - set(baseline_paths))}, "
            f"unexpected={sorted(set(baseline_paths) - expected_baseline_paths)}",
        )

    positive_validator = validators[GOVERNANCE_POSITIVE_SCHEMA_PATH]
    positive_wrappers: dict[str, Mapping[str, Any]] = {}
    positive_ids: set[str] = set()
    for path in positive_paths:
        wrapper = strict_json(snapshot.read(path), path)
        if not isinstance(wrapper, dict):
            raise GateError(
                "GA12-GOVERNANCE-POSITIVE-SHAPE",
                f"typed governance positive must be an object: {path}",
            )
        require_schema_acceptance(
            positive_validator,
            wrapper,
            path,
            "GA12-GOVERNANCE-POSITIVE-SCHEMA",
        )
        fixture_id = wrapper.get("fixture_id")
        if (
            fixture_id != GOVERNANCE_POSITIVE_PATH_TO_ID[path]
            or fixture_id in positive_ids
        ):
            raise GateError(
                "GA12-GOVERNANCE-POSITIVE-ID",
                f"typed governance positive identity differs or is duplicated: {path}",
            )
        positive_ids.add(fixture_id)
        positive_wrappers[path] = wrapper

    publication_event = strict_json(
        snapshot.read(PUBLICATION_EVENT_BASELINE_PATH),
        PUBLICATION_EVENT_BASELINE_PATH,
    )
    transport_baseline = strict_json(
        snapshot.read(TRANSPORT_OBSERVATION_BASELINE_PATH),
        TRANSPORT_OBSERVATION_BASELINE_PATH,
    )
    if not isinstance(publication_event, dict) or not isinstance(
        transport_baseline, dict
    ):
        raise GateError(
            "GA12-GOVERNANCE-BASELINE-SHAPE",
            "typed governance baselines must be objects",
        )
    require_schema_acceptance(
        validators[PUBLICATION_EVENT_SCHEMA_PATH],
        publication_event,
        PUBLICATION_EVENT_BASELINE_PATH,
        "GA12-PUBLICATION-BASELINE-SCHEMA",
    )
    require_schema_acceptance(
        validators[TRANSPORT_OBSERVATION_SCHEMA_PATH],
        transport_baseline,
        TRANSPORT_OBSERVATION_BASELINE_PATH,
        "GA12-TRANSPORT-BASELINE-SCHEMA",
    )
    if publication_event.get("fixture_id") != (
        "reiyah.fixture.governance.publication-event-synthetic-baseline@1.2.0"
    ):
        raise GateError(
            "GA12-PUBLICATION-BASELINE-ID",
            "typed publication baseline identity differs from the frozen contract",
        )
    if transport_baseline.get("fixture_id") != (
        "reiyah.fixture.governance.transport-observation-synthetic-baseline@1.2.0"
    ):
        raise GateError(
            "GA12-TRANSPORT-BASELINE-ID",
            "typed transport baseline identity differs from the frozen contract",
        )
    publication_baseline_diagnostics = publication_event_violations(
        snapshot,
        publication_event,
        positive_wrappers,
    )
    if publication_baseline_diagnostics:
        raise GateError(
            "GA12-PUBLICATION-BASELINE-REJECTED",
            f"typed publication baseline triggered {publication_baseline_diagnostics}",
        )
    transport_baseline_diagnostics = transport_observation_violations(
        snapshot,
        transport_baseline,
        publication_event,
    )
    if transport_baseline_diagnostics:
        raise GateError(
            "GA12-TRANSPORT-BASELINE-REJECTED",
            f"typed transport baseline triggered {transport_baseline_diagnostics}",
        )

    bad_paths = sorted(
        path
        for path in snapshot.files
        if path.startswith(GOVERNANCE_FIXTURE_PREFIX) and path.endswith(".json")
    )
    expected_bad_paths = {
        governance_fixture_path(fixture_id)
        for fixture_id in REQUIRED_GOVERNANCE_FIXTURES
    }
    if set(bad_paths) != expected_bad_paths:
        raise GateError(
            "GA12-GOVERNANCE-FIXTURE-SET",
            "typed governance known-bad paths differ; "
            f"missing={sorted(expected_bad_paths - set(bad_paths))}, "
            f"unexpected={sorted(set(bad_paths) - expected_bad_paths)}",
        )

    publication_mutation_validator = validators[PUBLICATION_EVENT_MUTATION_SCHEMA_PATH]
    transport_mutation_validator = validators[
        TRANSPORT_OBSERVATION_MUTATION_SCHEMA_PATH
    ]
    publication_target_validator = validators[PUBLICATION_EVENT_SCHEMA_PATH]
    transport_target_validator = validators[TRANSPORT_OBSERVATION_SCHEMA_PATH]
    publication_mutation_schema_id = (
        "https://schemas.reiyah.invalid/gate-a/1.2.0/"
        "publication-event-mutation-fixture.schema.json"
    )
    transport_mutation_schema_id = (
        "https://schemas.reiyah.invalid/gate-a/1.2.0/"
        "transport-observation-mutation-fixture.schema.json"
    )
    publication_observed: dict[str, str] = {}
    transport_observed: dict[str, str] = {}
    diagnostics: dict[str, int] = {}
    publication_structural = 0
    publication_semantic = 0
    transport_structural = 0
    transport_semantic = 0
    mutation_pointer_count = 0
    publication_baseline_frozen = copy.deepcopy(publication_event)
    transport_baseline_frozen = copy.deepcopy(transport_baseline)

    def resolve_publication_semantics(value: Mapping[str, Any]) -> list[str]:
        return publication_event_violations(snapshot, value, positive_wrappers)

    def resolve_transport_semantics(value: Mapping[str, Any]) -> list[str]:
        return transport_observation_violations(
            snapshot,
            value,
            publication_event,
        )

    for path in bad_paths:
        fixture = strict_json(snapshot.read(path), path)
        if not isinstance(fixture, dict):
            raise GateError(
                "GA12-GOVERNANCE-FIXTURE-SHAPE",
                f"typed governance mutation fixture must be an object: {path}",
            )
        fixture_schema_id = fixture.get("schema_id")
        if fixture_schema_id == publication_mutation_schema_id:
            envelope_validator = publication_mutation_validator
            target_validator = publication_target_validator
            baseline = publication_event
            expected_baseline_id = publication_event["fixture_id"]
            required_contract = REQUIRED_PUBLICATION_GOVERNANCE_FIXTURES
            observed_contract = publication_observed
            semantic_resolver: Callable[[Mapping[str, Any]], list[str]] = (
                resolve_publication_semantics
            )
            family = "publication"
        elif fixture_schema_id == transport_mutation_schema_id:
            envelope_validator = transport_mutation_validator
            target_validator = transport_target_validator
            baseline = transport_baseline
            expected_baseline_id = transport_baseline["fixture_id"]
            required_contract = REQUIRED_TRANSPORT_GOVERNANCE_FIXTURES
            observed_contract = transport_observed
            semantic_resolver = resolve_transport_semantics
            family = "transport"
        else:
            raise GateError(
                "GA12-GOVERNANCE-FIXTURE-SCHEMA-ID",
                f"typed governance mutation schema is not frozen: {path}",
            )
        require_schema_acceptance(
            envelope_validator,
            fixture,
            path,
            "GA12-GOVERNANCE-MUTATION-SCHEMA",
        )
        fixture_id = fixture.get("fixture_id")
        expected_diagnostic = fixture.get("expected_diagnostic")
        if (
            not isinstance(fixture_id, str)
            or fixture_id not in required_contract
            or required_contract[fixture_id] != expected_diagnostic
            or governance_fixture_path(fixture_id) != path
            or fixture_id in observed_contract
            or fixture.get("baseline_fixture_id") != expected_baseline_id
        ):
            raise GateError(
                "GA12-GOVERNANCE-FIXTURE-BINDING",
                f"typed governance mutation release, path, baseline, or diagnostic binding differs: {path}",
            )
        mutated = apply_governance_fixture_mutations(baseline, fixture)
        mutations = fixture.get("mutations")
        mutation_pointer_count += len(mutations) if isinstance(mutations, list) else 1
        if (
            publication_event != publication_baseline_frozen
            or transport_baseline != transport_baseline_frozen
        ):
            raise GateError(
                "GA12-GOVERNANCE-BASELINE-MUTATED",
                f"typed governance mutation changed a shared baseline in place: {path}",
            )
        target_errors = schema_error_records(target_validator, mutated)
        replay = fixture.get("expected_replay")
        if not isinstance(replay, Mapping):
            raise GateError(
                "GA12-GOVERNANCE-REPLAY-SHAPE",
                f"typed governance mutation lacks expected_replay: {path}",
            )
        rejection_layer = replay.get("rejection_layer")
        if rejection_layer == "structural_schema":
            if not target_errors or (family == "transport" and len(target_errors) != 1):
                raise GateError(
                    "GA12-GOVERNANCE-STRUCTURAL-COUNT",
                    f"{path}: structural fixture did not produce its frozen canonical "
                    f"schema-error cardinality; observed={target_errors}",
                )
            primary = target_errors[0]
            if not (
                primary["schema_keyword"] == replay.get("schema_keyword")
                and primary["instance_pointer"] == replay.get("instance_pointer")
                and replay.get("semantic_replay_required") is False
                and replay.get("exact_singleton_semantic_diagnostic_required") is False
            ):
                raise GateError(
                    "GA12-GOVERNANCE-STRUCTURAL-PRIMARY",
                    f"{path}: canonical structural primary differs: {primary}",
                )
            if family == "publication":
                publication_structural += 1
            else:
                transport_structural += 1
        elif rejection_layer == "semantic":
            if target_errors:
                first = target_errors[0]
                raise GateError(
                    "GA12-GOVERNANCE-SEMANTIC-REACHABILITY",
                    f"{path}: semantic fixture failed {first['schema_keyword']} at "
                    f"{first['instance_pointer']}: {first['message']}",
                )
            actual = semantic_resolver(mutated)
            if not (
                replay.get("schema_keyword") == "semantic"
                and replay.get("instance_pointer") is None
                and replay.get("semantic_replay_required") is True
                and replay.get("exact_singleton_semantic_diagnostic_required") is True
                and actual == [expected_diagnostic]
            ):
                raise GateError(
                    "GA12-GOVERNANCE-SEMANTIC-PRIMARY",
                    f"{path}: expected only {expected_diagnostic}, observed {actual}",
                )
            if family == "publication":
                publication_semantic += 1
            else:
                transport_semantic += 1
        else:
            raise GateError(
                "GA12-GOVERNANCE-REPLAY-LAYER",
                f"typed governance rejection layer is not frozen: {path}",
            )
        observed_contract[fixture_id] = expected_diagnostic
        diagnostics[expected_diagnostic] = diagnostics.get(expected_diagnostic, 0) + 1

    if publication_observed != REQUIRED_PUBLICATION_GOVERNANCE_FIXTURES:
        raise GateError(
            "GA12-PUBLICATION-FIXTURE-COVERAGE",
            "typed publication fixture IDs or diagnostics differ from the frozen 19-case set",
        )
    if transport_observed != REQUIRED_TRANSPORT_GOVERNANCE_FIXTURES:
        raise GateError(
            "GA12-TRANSPORT-FIXTURE-COVERAGE",
            "typed transport fixture IDs or diagnostics differ from the frozen 31-case set",
        )
    if publication_structural + publication_semantic != len(
        REQUIRED_PUBLICATION_GOVERNANCE_FIXTURES
    ) or transport_structural + transport_semantic != len(
        REQUIRED_TRANSPORT_GOVERNANCE_FIXTURES
    ):
        raise GateError(
            "GA12-GOVERNANCE-REPLAY-PARTITION",
            "typed governance structural/semantic partitions do not cover "
            "their exact required fixture sets",
        )

    validated_positive_catalog = {
        **{
            path: [fixture_id, "known_good", None]
            for path, fixture_id in sorted(GOVERNANCE_POSITIVE_PATH_TO_ID.items())
        },
        PUBLICATION_EVENT_BASELINE_PATH: [
            publication_event["fixture_id"],
            "known_good",
            None,
        ],
        TRANSPORT_OBSERVATION_BASELINE_PATH: [
            transport_baseline["fixture_id"],
            "known_good",
            None,
        ],
    }
    positive_bindings = [
        {
            "path": path,
            "fixture_id": validated_positive_catalog[path][0],
            "sha256": f"sha256:{snapshot.files[path].sha256}",
            "byte_size": snapshot.files[path].size,
        }
        for path in sorted(validated_positive_catalog)
    ]
    publication_bad_paths = sorted(
        governance_fixture_path(fixture_id)
        for fixture_id in REQUIRED_PUBLICATION_GOVERNANCE_FIXTURES
    )
    transport_bad_paths = sorted(
        governance_fixture_path(fixture_id)
        for fixture_id in REQUIRED_TRANSPORT_GOVERNANCE_FIXTURES
    )
    publication_positive_paths = sorted(
        path
        for path in validated_positive_catalog
        if path != TRANSPORT_OBSERVATION_BASELINE_PATH
    )
    transport_positive_paths = [TRANSPORT_OBSERVATION_BASELINE_PATH]
    return {
        "fixture_count": len(bad_paths),
        "positive_fixture_count": len(validated_positive_catalog),
        "validated_positive_catalog": validated_positive_catalog,
        "diagnostics": dict(sorted(diagnostics.items())),
        "fixture_set_sha256": artifact_set_digest(snapshot, bad_paths),
        "positive_fixture_set_sha256": artifact_set_digest(
            snapshot,
            sorted(validated_positive_catalog),
        ),
        "publication": {
            "positive_count": len(publication_positive_paths),
            "known_bad_count": len(publication_bad_paths),
            "structural_rejection_count": publication_structural,
            "semantic_singleton_rejection_count": publication_semantic,
            "known_bad_set_sha256": artifact_set_digest(
                snapshot, publication_bad_paths
            ),
            "baseline_sha256": snapshot.files[PUBLICATION_EVENT_BASELINE_PATH].sha256,
            "baseline_byte_size": snapshot.files[PUBLICATION_EVENT_BASELINE_PATH].size,
        },
        "transport": {
            "positive_count": len(transport_positive_paths),
            "known_bad_count": len(transport_bad_paths),
            "structural_rejection_count": transport_structural,
            "semantic_singleton_rejection_count": transport_semantic,
            "known_bad_set_sha256": artifact_set_digest(snapshot, transport_bad_paths),
            "baseline_sha256": snapshot.files[
                TRANSPORT_OBSERVATION_BASELINE_PATH
            ].sha256,
            "baseline_byte_size": snapshot.files[
                TRANSPORT_OBSERVATION_BASELINE_PATH
            ].size,
        },
        "observed_evidence": {
            "positive_bindings": positive_bindings,
            "mutation_pointer_count": mutation_pointer_count,
            "publication_replay": {
                "positive_fixture_ids": [
                    validated_positive_catalog[path][0]
                    for path in publication_positive_paths
                ],
                "known_bad_fixture_ids": list(REQUIRED_PUBLICATION_GOVERNANCE_FIXTURES),
            },
            "transport_replay": {
                "positive_fixture_ids": [
                    validated_positive_catalog[path][0]
                    for path in transport_positive_paths
                ],
                "known_bad_fixture_ids": list(REQUIRED_TRANSPORT_GOVERNANCE_FIXTURES),
            },
            "real_publication_event_claimed": False,
            "real_independent_transport_event_claimed": False,
            "independent_transport_state_conferred": False,
            "acceptance_or_runtime_authority_conferred": False,
        },
    }


def validate_report_count_equalities(summary: Mapping[str, Any]) -> None:
    if summary.get("science_good_passed") != summary.get("science_good_total"):
        raise GateError(
            "GA12-REPORT-GOOD-COUNT",
            "canonical report must show every good fixture passing",
        )
    if summary.get("science_known_bad_rejected_for_declared_rule") != summary.get(
        "science_known_bad_total"
    ):
        raise GateError(
            "GA12-REPORT-SCIENCE-BAD-COUNT",
            "canonical report must show every science known-bad rejected for its declared rule",
        )
    if summary.get(
        "validator_security_rejected_for_declared_diagnostic"
    ) != summary.get("validator_security_known_bad_total"):
        raise GateError(
            "GA12-REPORT-SECURITY-COUNT",
            "canonical report must show every validator-security fixture rejected for its declared diagnostic",
        )
    if summary.get("governance_rejected_for_declared_diagnostic") != summary.get(
        "governance_known_bad_total"
    ):
        raise GateError(
            "GA12-REPORT-GOVERNANCE-COUNT",
            "canonical report must show every governance fixture rejected for its declared diagnostic",
        )


SECURITY_CANARY_ZERO_DIGEST = "sha256:" + "0" * 64


def fixture_catalog_reconciliation_canary(
    snapshot: RepositorySnapshot,
    operation: object,
) -> str | None:
    target_path = "fixtures/v1.2/known-bad/validator-security-invalid-uri.json"
    target = strict_json(snapshot.read(target_path), target_path)
    if not isinstance(target, Mapping):
        return "GA12-SECURITY-FIXTURE-KIND"
    expected = current_catalog_row(
        snapshot,
        target_path,
        (
            str(target.get("fixture_id")),
            "known_bad",
            str(target.get("expected_diagnostic")),
        ),
    )
    expected_rows = [expected]
    observed_rows = copy.deepcopy(expected_rows)
    field_by_operation = {
        "byte_digest": ("sha256", SECURITY_CANARY_ZERO_DIGEST),
        "byte_size": ("byte_size", expected["byte_size"] + 1),
        "fixture_schema": (
            "fixture_schema_id",
            "https://schemas.reiyah.invalid/gate-a/1.2.0/substituted-fixture.schema.json",
        ),
        "target_schema": (
            "target_schema_id",
            "https://schemas.reiyah.invalid/gate-a/1.2.0/substituted-target.schema.json",
        ),
        "identity_source": ("fixture_identity_source", "substituted_identity"),
        "replay_mode": ("replay_mode", "substituted_replay"),
        "expected_primary_rule": (
            "expected_primary_rule_id",
            "GA12-SYNTHETIC-SUBSTITUTION",
        ),
    }
    if operation == "missing_row":
        observed_rows = []
    elif operation == "unexpected_row":
        unexpected = copy.deepcopy(expected)
        unexpected["fixture_id"] = "reiyah.fixture.synthetic.unexpected@1.2.0"
        unexpected["path"] = "fixtures/v1.2/known-bad/synthetic-unexpected.json"
        observed_rows.append(unexpected)
    elif operation in field_by_operation:
        field, value = field_by_operation[operation]
        observed_rows[0][field] = value
    else:
        return "GA12-SECURITY-FIXTURE-KIND"
    return captured_gate_diagnostic(
        lambda: validate_fixture_catalog_rows(observed_rows, expected_rows)
    )


def selector_contract_canary_diagnostic(
    snapshot: RepositorySnapshot,
    operation: object,
) -> str | None:
    selector_id = "reiyah.evidence-selector.security.narrative-nonclaim"
    fixture_id = "reiyah.fixture.validator-security.narrative-state-contradiction@1.2.0"
    fixture_path = (
        "fixtures/v1.2/known-bad/validator-security-narrative-state-contradiction.json"
    )
    extra_fixture_id = "reiyah.fixture.validator-security.invalid-uri@1.2.0"
    extra_fixture_path = "fixtures/v1.2/known-bad/validator-security-invalid-uri.json"
    expected = {
        "producer_check_id": EVIDENCE_SELECTOR_PRODUCER_DISPATCH[selector_id],
        "required_observations": (
            {
                "observation_id": (
                    "reiyah.selector-observation.security.narrative-nonclaim@1.2.0"
                ),
                "fixture_ids": (fixture_id,),
            },
        ),
    }
    catalog_by_id = {
        fixture_id: {"path": fixture_path},
        extra_fixture_id: {"path": extra_fixture_path},
    }
    digest = evidence_sha256(
        artifact_rows_for_fixture_ids(snapshot, catalog_by_id, [fixture_id])
    )
    producer_to_token = {
        producer: token for token, producer in STAGE_PRODUCER_DISPATCH.items()
    }
    declared = {
        "selector_id": selector_id,
        "producer_stage_token_id": producer_to_token[expected["producer_check_id"]],
        "producer_check_id": expected["producer_check_id"],
        "required_observations": [
            {
                "observation_id": expected["required_observations"][0][
                    "observation_id"
                ],
                "fixture_ids": [fixture_id],
                "fixture_set_sha256": digest,
            }
        ],
        "projection_policy": (
            "ordered_fixture_ids_resolved_through_validated_catalog_to_path_sha256_size"
        ),
    }
    if operation == "missing_observation":
        declared["required_observations"] = []
    elif operation == "missing_fixture":
        declared["required_observations"][0]["fixture_ids"] = []
    elif operation == "unexpected_fixture":
        declared["required_observations"][0]["fixture_ids"].append(extra_fixture_id)
    elif operation == "producer_substitution":
        declared["producer_check_id"] = "GA12-STAGE-SCHEMA-CORPUS"
    elif operation == "fixture_set_digest_mismatch":
        declared["required_observations"][0]["fixture_set_sha256"] = (
            SECURITY_CANARY_ZERO_DIGEST
        )
    else:
        return "GA12-SECURITY-FIXTURE-KIND"
    return captured_gate_diagnostic(
        lambda: project_selector_evidence_row(
            snapshot,
            SECURITY_CANARY_ZERO_DIGEST,
            declared,
            selector_id,
            expected,
            catalog_by_id,
        )
    )


def fixture_diagnostic(
    snapshot: RepositorySnapshot,
    probe: Mapping[str, Any],
    *,
    observed_pre_report_canary_fixture_summary: Mapping[str, Any] | None = None,
) -> str | None:
    kind = probe.get("kind")
    if kind == "format":
        format_name = probe.get("format")
        if not isinstance(format_name, str) or format_name not in FORMAT_CHECKERS:
            return "GA12-FORMAT-CHECKER-UNKNOWN"
        return (
            None
            if FORMAT_CHECKERS[format_name](probe.get("value"))
            else FORMAT_DIAGNOSTICS[format_name]
        )
    if kind == "launcher_profile":
        flags = probe.get("flags")
        return None if flags == ["-I", "-S", "-B"] else "GA12-LAUNCHER-PROFILE"
    if kind == "toolchain_digest":
        return captured_gate_diagnostic(
            lambda: require_toolchain_match(
                probe.get("locked_sha256"),
                probe.get("observed_sha256"),
                "fixture digest",
            )
        )
    if kind == "release_state":
        status = b" M synthetic\x00" if probe.get("dirty") is True else b""
        return captured_gate_diagnostic(lambda: require_release_clean(status, b""))
    if kind == "release_index_flag":
        flag = probe.get("flag")
        record = f"{flag} synthetic".encode("utf-8") if isinstance(flag, str) else b""
        return captured_gate_diagnostic(lambda: require_release_index_flag(record))
    if kind == "development_projection":
        return captured_gate_diagnostic(
            lambda: require_development_projection_match(
                probe.get("before_sha256"), probe.get("after_sha256")
            )
        )
    if kind == "transport_evidence":
        return captured_gate_diagnostic(
            lambda: evaluate_transport_boundary(
                snapshot,
                str(probe.get("publisher_receipt_path")),
                probe.get("independent_transport_record_paths", []),
                str(probe.get("claimed_state")),
            )
        )
    if kind == "registry_uniqueness":
        registry_path = probe.get("registry_path")
        if registry_path != DEFINITION_REGISTRY_PATH:
            return "GA12-SECURITY-FIXTURE-KIND"
        registry = strict_json(snapshot.read(registry_path), registry_path)
        if not isinstance(registry, dict) or not isinstance(
            probe.get("mutation"), dict
        ):
            return "GA12-SECURITY-FIXTURE-KIND"
        validate_definition_registry_uniqueness(registry)
        mutated = replace_json_pointer(registry, probe["mutation"])
        return captured_gate_diagnostic(
            lambda: validate_definition_registry_uniqueness(mutated)
        )
    if kind == "science_artifact_lineage":
        baseline = probe.get("baseline_records")
        mutation = probe.get("mutation")
        if not isinstance(baseline, list) or not isinstance(mutation, dict):
            return "GA12-SECURITY-FIXTURE-KIND"
        validate_science_artifact_lineage(baseline)
        mutated = replace_json_pointer({"records": baseline}, mutation)
        return captured_gate_diagnostic(
            lambda: validate_science_artifact_lineage(mutated["records"])
        )
    if kind == "fixture_catalog_uniqueness":
        catalog_path = probe.get("catalog_path")
        if catalog_path != "fixtures/fixture-catalog.json":
            return "GA12-SECURITY-FIXTURE-KIND"
        catalog = strict_json(snapshot.read(catalog_path), catalog_path)
        if not isinstance(catalog, dict) or not isinstance(probe.get("mutation"), dict):
            return "GA12-SECURITY-FIXTURE-KIND"
        validate_fixture_catalog_uniqueness(catalog)
        mutated = replace_json_pointer(catalog, probe["mutation"])
        return captured_gate_diagnostic(
            lambda: validate_fixture_catalog_uniqueness(mutated)
        )
    if kind == "fixture_catalog_reconciliation":
        if probe.get("catalog_path") != "fixtures/fixture-catalog.json":
            return "GA12-SECURITY-FIXTURE-KIND"
        return fixture_catalog_reconciliation_canary(snapshot, probe.get("operation"))
    if kind == "successor_chronology":
        protocol = strict_json(
            snapshot.read(PROTOCOL_MANIFEST_PATH), PROTOCOL_MANIFEST_PATH
        )
        research = strict_json(
            snapshot.read(RESEARCH_REGISTRY_PATH), RESEARCH_REGISTRY_PATH
        )
        if (
            not isinstance(protocol, dict)
            or not isinstance(research, dict)
            or not isinstance(probe.get("mutation"), dict)
        ):
            return "GA12-SECURITY-FIXTURE-KIND"
        validate_successor_chronology(protocol, research)
        operands = replace_json_pointer(
            {"protocol": protocol, "research_registry": research}, probe["mutation"]
        )
        return captured_gate_diagnostic(
            lambda: validate_successor_chronology(
                operands["protocol"], operands["research_registry"]
            )
        )
    if kind == "narrative_state":
        protocol = strict_json(
            snapshot.read(PROTOCOL_MANIFEST_PATH), PROTOCOL_MANIFEST_PATH
        )
        profile = strict_json(
            snapshot.read(SCIENTIFIC_PROFILE_PATH), SCIENTIFIC_PROFILE_PATH
        )
        if (
            not isinstance(protocol, dict)
            or not isinstance(profile, dict)
            or not isinstance(probe.get("mutation"), dict)
        ):
            return "GA12-SECURITY-FIXTURE-KIND"
        try:
            narratives = {
                path: snapshot.read(path).decode("utf-8")
                for path in NARRATIVE_CANDIDATE_MARKERS
            }
        except UnicodeDecodeError:
            return "GA12-NARRATIVE-STATE-CONSISTENCY"
        validate_narrative_state_operands(protocol, profile, narratives)
        operands = replace_json_pointer(
            {"protocol": protocol, "profile": profile, "narratives": narratives},
            probe["mutation"],
        )
        return captured_gate_diagnostic(
            lambda: validate_narrative_state_operands(
                operands["protocol"], operands["profile"], operands["narratives"]
            )
        )
    if kind == "normative_markdown_surface":
        if probe.get("operation") != "substitute_architecture_path":
            return "GA12-SECURITY-FIXTURE-KIND"
        documents = {path: snapshot.read(path) for path in NORMATIVE_MARKDOWN_SURFACE}
        validate_normative_markdown_surface_operands(documents)
        substituted = dict(documents)
        payload = substituted.pop("docs/ARCHITECTURE.md")
        substituted["docs/ARCHITECTURE-SUBSTITUTED.md"] = payload
        return captured_gate_diagnostic(
            lambda: validate_normative_markdown_surface_operands(substituted)
        )
    if kind == "reference_path_inventory":
        operation = probe.get("operation")
        if probe.get("profile_path") != SCIENTIFIC_PROFILE_PATH or operation not in {
            "missing_declared_binding",
            "duplicate_declared_classification",
            "handler_only_path",
        }:
            return "GA12-SECURITY-FIXTURE-KIND"
        derived = derive_reference_path_inventory(snapshot)
        declared = copy.deepcopy(derived)
        science = load_science_module(snapshot)
        handler_contract = copy.deepcopy(science["REFERENCE_PATH_HANDLER_CONTRACT"])
        if operation == "missing_declared_binding":
            declared["bindings"].pop()
        elif operation == "duplicate_declared_classification":
            declared["bindings"].append(copy.deepcopy(declared["bindings"][0]))
        else:
            handler_bindings = copy.deepcopy(derived["bindings"])
            handler_only = copy.deepcopy(handler_bindings[0])
            handler_only["pointer_glob"] = "/handler_only_nonexistent_id"
            handler_bindings.append(handler_only)
            handler_contract = reference_path_handler_contract(handler_bindings)
        return captured_gate_diagnostic(
            lambda: validate_reference_path_inventory_operands(
                derived, declared, handler_contract
            )
        )
    if kind == "scientific_profile_execution_binding":
        expected_roles = {
            "launcher_binding": LAUNCHER_PATH,
            "tool_binding": TOOL_PATH,
            "science_module_binding": SCIENCE_MODULE_PATH,
            "toolchain_lock_binding": LOCK_PATH,
        }
        binding_role = probe.get("binding_role")
        if (
            probe.get("profile_path") != SCIENTIFIC_PROFILE_PATH
            or binding_role not in expected_roles
            or not isinstance(probe.get("mutation"), Mapping)
        ):
            return "GA12-SECURITY-FIXTURE-KIND"
        profile = strict_json(
            snapshot.read(SCIENTIFIC_PROFILE_PATH), SCIENTIFIC_PROFILE_PATH
        )
        if not isinstance(profile, dict):
            return "GA12-SECURITY-FIXTURE-KIND"
        execution = profile.get("execution_integrity_contract")
        if not isinstance(execution, Mapping) or not isinstance(
            execution.get(binding_role), Mapping
        ):
            return "GA12-SECURITY-FIXTURE-KIND"
        validate_reference_bytes(
            snapshot,
            execution[binding_role],
            expected_roles[binding_role],
            "GA12-SCIENCE-PROFILE-EXECUTION",
        )
        mutated = replace_json_pointer(profile, probe["mutation"])
        return captured_gate_diagnostic(
            lambda: validate_reference_bytes(
                snapshot,
                mutated["execution_integrity_contract"][binding_role],
                expected_roles[binding_role],
                "GA12-SCIENCE-PROFILE-EXECUTION",
            )
        )
    if kind == "validation_plan_tool_binding":
        role = probe.get("binding_role")
        roles = [item[0] for item in PLAN_TOOL_BINDING_CONTRACT]
        if (
            probe.get("plan_path") != PLAN_PATH
            or role not in roles
            or probe.get("operation") != "replace_bound_sha256_with_zero"
        ):
            return "GA12-SECURITY-FIXTURE-KIND"
        plan = strict_json(snapshot.read(PLAN_PATH), PLAN_PATH)
        if not isinstance(plan, Mapping) or not isinstance(
            plan.get("tool_bindings"), list
        ):
            return "GA12-SECURITY-FIXTURE-KIND"
        bindings = copy.deepcopy(plan["tool_bindings"])
        validate_plan_tool_bindings(snapshot, bindings)
        matches = [row for row in bindings if row.get("role") == role]
        if len(matches) != 1:
            return "GA12-SECURITY-FIXTURE-KIND"
        matches[0]["sha256"] = SECURITY_CANARY_ZERO_DIGEST
        return captured_gate_diagnostic(
            lambda: validate_plan_tool_bindings(snapshot, bindings)
        )
    if kind == "self_membership":
        if probe.get("operation") != "substitute_primary_validator_byte":
            return "GA12-SECURITY-FIXTURE-KIND"
        baseline = {
            "launcher": snapshot.read(LAUNCHER_PATH),
            "primary_validator": snapshot.read(TOOL_PATH),
            "science_module": snapshot.read(SCIENCE_MODULE_PATH),
        }
        observed = dict(baseline)
        observed["primary_validator"] += b"\nsynthetic-byte-substitution"
        return captured_gate_diagnostic(
            lambda: require_self_membership_bytes(baseline, observed)
        )
    if kind == "evidence_selector_contract":
        return selector_contract_canary_diagnostic(snapshot, probe.get("operation"))
    if kind == "release_evaluation_worker_fault_matrix":
        if probe.get("operation") != "replay_closed_worker_fault_matrix":
            return "GA12-SECURITY-FIXTURE-KIND"
        return release_worker_fault_canary_matrix()
    if kind == "actual_publication_event_fault_matrix":
        if probe.get("operation") != "replay_closed_actual_event_fault_matrix":
            return "GA12-SECURITY-FIXTURE-KIND"
        return actual_publication_event_fault_canary_matrix()
    if kind == "canonical_report_fixture_summary":
        if (
            probe.get("baseline_source") != "observed_pre_report_canary_fixture_summary"
            or not isinstance(observed_pre_report_canary_fixture_summary, Mapping)
            or not isinstance(probe.get("mutation"), Mapping)
        ):
            return "GA12-SECURITY-FIXTURE-KIND"
        baseline = dict(observed_pre_report_canary_fixture_summary)
        validate_report_count_equalities(baseline)
        mutation = probe["mutation"]
        pointer = mutation.get("json_pointer")
        if (
            mutation.get("operation") != "decrement_integer"
            or mutation.get("delta") != 1
            or not isinstance(pointer, str)
            or not pointer.startswith("/")
        ):
            return "GA12-SECURITY-FIXTURE-KIND"
        key = pointer[1:].replace("~1", "/").replace("~0", "~")
        current = baseline.get(key)
        if not isinstance(current, int) or isinstance(current, bool):
            return "GA12-SECURITY-FIXTURE-KIND"
        mutated = copy.deepcopy(baseline)
        mutated[key] = current - 1
        return captured_gate_diagnostic(
            lambda: validate_report_count_equalities(mutated)
        )
    return "GA12-SECURITY-FIXTURE-KIND"


def validate_security_fixtures(
    snapshot: RepositorySnapshot,
    dependencies: Mapping[str, Any],
    science: Mapping[str, Any],
    governance: Mapping[str, Any],
) -> dict[str, Any]:
    paths = sorted(
        path
        for path in snapshot.files
        if path.startswith(SECURITY_FIXTURE_PREFIX) and path.endswith(".json")
    )
    if not paths:
        raise GateError(
            "GA12-SECURITY-FIXTURES-MISSING", "no validator-security fixtures found"
        )
    fixture_ids: set[str] = set()
    observed_contract: dict[str, str] = {}
    diagnostics: dict[str, int] = {}
    parsed_fixtures: list[tuple[str, Mapping[str, Any]]] = []
    executable_contract_matrix: dict[str, Any] | None = None
    joint_opportunity_registry_manifest_binding_matrix: dict[str, Any] | None = None
    ope_registry_manifest_binding_matrix: dict[str, Any] | None = None
    expected_keys = {
        "schema_id",
        "artifact_version",
        "expected_diagnostic",
        "fixture_class",
        "fixture_id",
        "mission_release_id",
        "probe",
        "protocol_release_id",
        "synthetic_fixture_only",
    }
    validator = validator_for_schema(
        snapshot,
        dependencies,
        "schemas/validator-security-fixture-1.2.schema.json",
        (COMMON_SCHEMA_PATH,),
    )
    for path in paths:
        fixture = strict_json(snapshot.read(path), path)
        if not isinstance(fixture, dict):
            raise GateError(
                "GA12-SECURITY-FIXTURE-SHAPE", f"fixture must be an object: {path}"
            )
        errors = schema_error_records(validator, fixture)
        if errors:
            first = errors[0]
            raise GateError(
                "GA12-SECURITY-FIXTURE-SCHEMA",
                f"{path}: fixture failed {first['schema_keyword']} at "
                f"{first['instance_pointer']}: {first['message']}",
            )
        require_exact_keys(fixture, expected_keys, path)
        bindings = {
            "schema_id": (
                "https://schemas.reiyah.invalid/gate-a/1.2.0/"
                "validator-security-fixture.schema.json"
            ),
            "artifact_version": ARTIFACT_VERSION,
            "fixture_class": "known-bad-validator-security",
            "mission_release_id": MISSION_RELEASE_ID,
            "protocol_release_id": PROTOCOL_RELEASE_ID,
            "synthetic_fixture_only": True,
        }
        for key, expected in bindings.items():
            if fixture.get(key) != expected:
                raise GateError(
                    "GA12-SECURITY-FIXTURE-BINDING", f"{path}: {key} mismatch"
                )
        fixture_id = fixture.get("fixture_id")
        if not isinstance(fixture_id, str) or fixture_id in fixture_ids:
            raise GateError(
                "GA12-SECURITY-FIXTURE-ID", f"invalid/duplicate fixture_id at {path}"
            )
        fixture_ids.add(fixture_id)
        probe = fixture.get("probe")
        if not isinstance(probe, dict):
            raise GateError(
                "GA12-SECURITY-FIXTURE-SHAPE", f"probe must be an object: {path}"
            )
        parsed_fixtures.append((path, fixture))

    ordinary_fixtures = [
        item
        for item in parsed_fixtures
        if item[1]["probe"].get("kind") != "canonical_report_fixture_summary"
    ]
    report_canary_fixtures = [
        item
        for item in parsed_fixtures
        if item[1]["probe"].get("kind") == "canonical_report_fixture_summary"
    ]
    if len(report_canary_fixtures) != 4:
        raise GateError(
            "GA12-SECURITY-FIXTURE-COVERAGE",
            "exactly four report-summary meta-canaries must run after ordinary security replay",
        )

    def record_observed(
        path: str,
        fixture: Mapping[str, Any],
        actual: str | None,
    ) -> None:
        expected = fixture.get("expected_diagnostic")
        if not isinstance(expected, str) or not expected.startswith("GA12-"):
            raise GateError(
                "GA12-SECURITY-FIXTURE-SHAPE",
                f"{path}: expected_diagnostic must be a GA12 diagnostic string",
            )
        if actual is None:
            raise GateError(
                "GA12-SECURITY-FIXTURE-NOT-REJECTED",
                f"{path}: known-bad probe was accepted",
            )
        if actual != expected:
            raise GateError(
                "GA12-SECURITY-FIXTURE-EXPECTED",
                f"{path}: expected {expected!r}, observed {actual!r}",
            )
        fixture_id = fixture["fixture_id"]
        observed_contract[fixture_id] = actual
        diagnostics[actual] = diagnostics.get(actual, 0) + 1

    for path, fixture in ordinary_fixtures:
        if fixture["probe"].get("kind") == "executable_contract_operand_matrix":
            if executable_contract_matrix is not None:
                raise GateError(
                    "GA12-EXECUTABLE-CONTRACT-OPERAND-COVERAGE",
                    "exactly one executable contract operand matrix is permitted",
                )
            executable_contract_matrix = validate_executable_contract_operand_matrix(
                snapshot,
                dependencies,
                fixture["probe"],
            )
            actual = executable_contract_matrix["coverage_canary_diagnostic"]
        elif (
            fixture["probe"].get("kind")
            == "joint_opportunity_registry_manifest_binding_matrix"
        ):
            if joint_opportunity_registry_manifest_binding_matrix is not None:
                raise GateError(
                    "GA12-JOINT-OPPORTUNITY-REGISTRY-MANIFEST-CANARY-COVERAGE",
                    "exactly one joint opportunity registry-manifest binding matrix is permitted",
                )
            joint_opportunity_registry_manifest_binding_matrix = (
                validate_joint_opportunity_registry_manifest_binding_matrix(
                    snapshot,
                    dependencies,
                )
            )
            actual = joint_opportunity_registry_manifest_binding_matrix[
                "coverage_canary_diagnostic"
            ]
        elif fixture["probe"].get("kind") == "ope_registry_manifest_binding_matrix":
            if ope_registry_manifest_binding_matrix is not None:
                raise GateError(
                    "GA12-OPE-REGISTRY-MANIFEST-CANARY-COVERAGE",
                    "exactly one OPE registry-manifest binding matrix is permitted",
                )
            ope_registry_manifest_binding_matrix = (
                validate_ope_registry_manifest_binding_matrix(
                    snapshot,
                    dependencies,
                )
            )
            actual = ope_registry_manifest_binding_matrix["coverage_canary_diagnostic"]
        else:
            actual = fixture_diagnostic(snapshot, fixture["probe"])
        record_observed(
            path,
            fixture,
            actual,
        )

    if executable_contract_matrix is None:
        raise GateError(
            "GA12-EXECUTABLE-CONTRACT-OPERAND-COVERAGE",
            "executable contract operand matrix fixture is absent",
        )
    if joint_opportunity_registry_manifest_binding_matrix is None:
        raise GateError(
            "GA12-JOINT-OPPORTUNITY-REGISTRY-MANIFEST-CANARY-COVERAGE",
            "joint opportunity registry-manifest binding matrix fixture is absent",
        )
    if ope_registry_manifest_binding_matrix is None:
        raise GateError(
            "GA12-OPE-REGISTRY-MANIFEST-CANARY-COVERAGE",
            "OPE registry-manifest binding matrix fixture is absent",
        )

    pre_report_canary_fixture_summary = {
        "science_good_total": science["good_fixture_count"],
        "science_good_passed": science["good_fixture_count"],
        "science_known_bad_total": science["mutation_fixture_count"],
        "science_known_bad_rejected_for_declared_rule": science[
            "semantic_rejected_mutation_count"
        ],
        "validator_security_known_bad_total": len(ordinary_fixtures),
        "validator_security_rejected_for_declared_diagnostic": len(ordinary_fixtures),
        "governance_known_bad_total": governance["fixture_count"],
        "governance_rejected_for_declared_diagnostic": governance["fixture_count"],
    }
    validate_report_count_equalities(pre_report_canary_fixture_summary)
    for path, fixture in report_canary_fixtures:
        record_observed(
            path,
            fixture,
            fixture_diagnostic(
                snapshot,
                fixture["probe"],
                observed_pre_report_canary_fixture_summary=(
                    pre_report_canary_fixture_summary
                ),
            ),
        )
    if observed_contract != REQUIRED_SECURITY_FIXTURES:
        raise GateError(
            "GA12-SECURITY-FIXTURE-COVERAGE",
            "validator-security fixture IDs or required diagnostics differ from the locked coverage set",
        )
    return {
        "fixture_count": len(paths),
        "ordinary_fixture_count": len(ordinary_fixtures),
        "report_canary_fixture_count": len(report_canary_fixtures),
        "pre_report_canary_fixture_summary": (pre_report_canary_fixture_summary),
        "executable_contract_operand_matrix": executable_contract_matrix,
        "joint_opportunity_registry_manifest_binding_matrix": (
            joint_opportunity_registry_manifest_binding_matrix
        ),
        "ope_registry_manifest_binding_matrix": (ope_registry_manifest_binding_matrix),
        "diagnostics": dict(sorted(diagnostics.items())),
    }


def require_self_membership_bytes(
    snapshot_bytes: Mapping[str, bytes],
    executing_bytes: Mapping[str, bytes],
) -> None:
    if tuple(snapshot_bytes) != tuple(executing_bytes):
        raise GateError(
            "GA12-SELF-MEMBERSHIP",
            "executing-byte role set/order differs from snapshot membership",
        )
    differing = [
        role for role in snapshot_bytes if snapshot_bytes[role] != executing_bytes[role]
    ]
    if differing:
        raise GateError(
            "GA12-SELF-MEMBERSHIP",
            "executing launcher/tool/science-module bytes differ from snapshot "
            f"membership: {differing}",
        )


def verify_snapshot_membership(snapshot: RepositorySnapshot) -> dict[str, str]:
    tool = snapshot.read(TOOL_PATH)
    launcher = snapshot.read(LAUNCHER_PATH)
    science_module = snapshot.read(SCIENCE_MODULE_PATH)
    lock = snapshot.read(LOCK_PATH)
    try:
        live_tool = stable_regular_bytes(CANONICAL_ROOT / TOOL_PATH)
        live_launcher = stable_regular_bytes(CANONICAL_ROOT / LAUNCHER_PATH)
        live_science_module = stable_regular_bytes(CANONICAL_ROOT / SCIENCE_MODULE_PATH)
    except GateError as exc:
        raise GateError(
            "GA12-SELF-MEMBERSHIP", f"cannot read launcher/tool: {exc}"
        ) from exc
    require_self_membership_bytes(
        {
            "launcher": launcher,
            "primary_validator": tool,
            "science_module": science_module,
        },
        {
            "launcher": live_launcher,
            "primary_validator": live_tool,
            "science_module": live_science_module,
        },
    )
    return {
        "launcher_sha256": hashlib.sha256(launcher).hexdigest(),
        "science_module_sha256": hashlib.sha256(science_module).hexdigest(),
        "tool_sha256": hashlib.sha256(tool).hexdigest(),
        "toolchain_lock_sha256": hashlib.sha256(lock).hexdigest(),
    }


def verify_plan_rule_coverage(
    plan: Mapping[str, Any],
    science: Mapping[str, Any],
    security: Mapping[str, Any],
    governance: Mapping[str, Any],
) -> dict[str, Any]:
    planned = {rule["rule_id"]: rule for rule in plan["rules"]}
    science_rules = {item["rule_id"] for item in science["diagnostics"]}
    security_rules = set(security["diagnostics"])
    governance_rules = set(governance["diagnostics"])
    required = science_rules | security_rules | governance_rules
    missing = sorted(required - set(planned))
    if missing:
        raise GateError(
            "GA12-PLAN-RULE-COVERAGE",
            f"fixture-backed production rules are absent from plan: {missing}",
        )
    not_fixture_bound = sorted(
        rule_id for rule_id in required if not planned[rule_id]["bad_fixture_required"]
    )
    if not_fixture_bound:
        raise GateError(
            "GA12-PLAN-RULE-COVERAGE",
            f"fixture-backed rules deny their fixture requirement: {not_fixture_bound}",
        )
    return {
        "planned_rule_count": len(planned),
        "science_fixture_rule_count": len(science_rules),
        "security_fixture_rule_count": len(security_rules),
        "governance_fixture_rule_count": len(governance_rules),
    }


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def json_ready(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): json_ready(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(child) for child in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise GateError(
        "GA12-DUAL-EVALUATION-WORKER-PROTOCOL",
        f"worker payload contains a non-JSON value: {type(value).__name__}",
    )


def evidence_sha256(value: Any) -> str:
    return f"sha256:{hashlib.sha256(canonical_json_bytes(value)).hexdigest()}"


def ordered_unique(values: Sequence[str]) -> list[str]:
    observed: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in observed:
            observed.add(value)
            result.append(value)
    return result


def validate_candidate_contract(
    snapshot: RepositorySnapshot,
    plan: Mapping[str, Any],
    candidate: CandidateProjection,
) -> dict[str, Any]:
    expected_paths = sorted(
        candidate.files,
        key=lambda value: value.encode("utf-8"),
    )
    declared_paths = plan.get("required_artifacts")
    if declared_paths != expected_paths:
        declared_set = (
            set(declared_paths) if isinstance(declared_paths, list) else set()
        )
        expected_set = set(expected_paths)
        raise GateError(
            "GA12-PLAN-REQUIRED-ARTIFACT",
            "required_artifacts must equal the UTF-8 ordered candidate projection: "
            f"missing={sorted(expected_set - declared_set)}, "
            f"unexpected={sorted(declared_set - expected_set)}",
        )
    if PLAN_PATH not in candidate.files:
        raise GateError(
            "GA12-PLAN-REQUIRED-ARTIFACT",
            "the validation plan must bind itself inside the candidate projection",
        )
    return {
        "required_artifact_count": len(expected_paths),
        "required_artifact_set_sha256": evidence_sha256(expected_paths),
        "candidate_projection_sha256": f"sha256:{candidate.sha256}",
    }


def validate_manifest_lineage(
    snapshot: RepositorySnapshot,
    dependencies: Mapping[str, Any],
) -> dict[str, Any]:
    ledger_path = "manifests/manifest-release-ledger.json"
    prior_path = "manifests/history/manifest-release-ledger-1.1.0.json"
    schema_path = "schemas/manifest-release-ledger-1.2.schema.json"
    ledger = strict_json(snapshot.read(ledger_path), ledger_path)
    prior = strict_json(snapshot.read(prior_path), prior_path)
    protocol = strict_json(
        snapshot.read(PROTOCOL_MANIFEST_PATH), PROTOCOL_MANIFEST_PATH
    )
    research = strict_json(
        snapshot.read(RESEARCH_REGISTRY_PATH), RESEARCH_REGISTRY_PATH
    )
    if not all(
        isinstance(value, Mapping) for value in (ledger, prior, protocol, research)
    ):
        raise GateError(
            "GA12-MANIFEST-LINEAGE-SHAPE",
            "manifest ledger, predecessor, protocol, and research registry must be objects",
        )
    validator = validator_for_schema(
        snapshot,
        dependencies,
        schema_path,
        (COMMON_SCHEMA_PATH,),
    )
    errors = schema_error_records(validator, ledger)
    if errors:
        first = errors[0]
        raise GateError(
            "GA12-MANIFEST-LINEAGE-SCHEMA",
            f"manifest ledger failed {first['schema_keyword']} at "
            f"{first['instance_pointer']}: {first['message']}",
        )
    prior_item = snapshot.files[prior_path]
    prior_binding = ledger.get("prior_ledger_binding")
    if (
        not isinstance(prior_binding, Mapping)
        or prior_binding.get("path") != prior_path
        or prior_binding.get("sha256") != f"sha256:{prior_item.sha256}"
        or prior_binding.get("version") != "1.1.0"
        or prior_binding.get("artifact_id")
        != "reiyah.artifact.manifest-release-ledger-1.1.0"
    ):
        raise GateError(
            "GA12-MANIFEST-LINEAGE-PREDECESSOR",
            "the 1.2 ledger does not exact-bind the immutable 1.1 predecessor",
        )
    prior_entries = prior.get("entries")
    current_entries = ledger.get("entries")
    if (
        not isinstance(prior_entries, list)
        or len(prior_entries) != 4
        or not isinstance(current_entries, list)
        or len(current_entries) != 5
        or current_entries[:4] != prior_entries
    ):
        raise GateError(
            "GA12-MANIFEST-LINEAGE-PREFIX",
            "the current ledger must preserve the exact four-entry predecessor prefix",
        )
    release_ids = [
        row.get("release_id") for row in current_entries if isinstance(row, Mapping)
    ]
    if len(release_ids) != len(current_entries) or len(release_ids) != len(
        set(release_ids)
    ):
        raise GateError(
            "GA12-MANIFEST-LINEAGE-RELEASE-ID",
            "manifest ledger release IDs must be complete and unique",
        )
    successor = current_entries[-1]
    protocol_item = snapshot.files[PROTOCOL_MANIFEST_PATH]
    expected_successor = {
        "manifest_kind": "protocol",
        "release_id": PROTOCOL_RELEASE_ID,
        "version": ARTIFACT_VERSION,
        "release_stage": "candidate",
        "lifecycle_status": "proposed",
    }
    if any(successor.get(key) != value for key, value in expected_successor.items()):
        raise GateError(
            "GA12-MANIFEST-LINEAGE-SUCCESSOR",
            "the fifth ledger row must be the unaccepted Gate A 1.2 protocol correction",
        )
    relation = successor.get("relation")
    binding = successor.get("artifact_binding")
    if (
        not isinstance(relation, Mapping)
        or relation.get("type") != "corrects"
        or relation.get("prior_release_id") != "reiyah.protocol.harbor-gate-a@1.1.0"
        or not isinstance(binding, Mapping)
        or binding.get("path") != PROTOCOL_MANIFEST_PATH
        or binding.get("sha256") != f"sha256:{protocol_item.sha256}"
        or binding.get("version") != ARTIFACT_VERSION
        or successor.get("operator_acceptance")
        != {"state": "unaccepted", "record_id": None}
    ):
        raise GateError(
            "GA12-MANIFEST-LINEAGE-SUCCESSOR",
            "the fifth ledger row relation, bytes, or acceptance state differs",
        )
    if any(
        row.get("manifest_kind") == "mission" and row.get("version") == ARTIFACT_VERSION
        for row in current_entries
    ):
        raise GateError(
            "GA12-MANIFEST-LINEAGE-MISSION-INVENTION",
            "Gate A 1.2 must not invent a mission 1.2 release",
        )
    if ledger.get("as_of_date") != protocol.get("created_on") or ledger.get(
        "as_of_date"
    ) != research.get("as_of_date"):
        raise GateError(
            "GA12-MANIFEST-LINEAGE-CHRONOLOGY",
            "ledger, protocol, and research-registry correction dates must agree",
        )
    return {
        "entry_count": len(current_entries),
        "inherited_entry_count": len(prior_entries),
        "successor_release_id": successor["release_id"],
        "prior_ledger_sha256": f"sha256:{prior_item.sha256}",
        "protocol_sha256": f"sha256:{protocol_item.sha256}",
        "entry_set_sha256": evidence_sha256(current_entries),
    }


def validate_source_standards_custody(
    snapshot: RepositorySnapshot,
    dependencies: Mapping[str, Any],
) -> dict[str, Any]:
    ledger_path = "evidence/source-ledger-1.1.0.json"
    crosswalk_path = "evidence/standards-crosswalk-1.1.0.json"
    ledger_schema_path = "schemas/source-ledger-1.1.schema.json"
    crosswalk_schema_path = "schemas/standards-crosswalk-1.1.schema.json"
    base_common_path = "schemas/common.schema.json"
    legacy_common_path = "schemas/common-1.1.schema.json"
    custody_schema_path = "schemas/public-evidence-custody-profile-1.1.schema.json"
    ledger = strict_json(snapshot.read(ledger_path), ledger_path)
    crosswalk = strict_json(snapshot.read(crosswalk_path), crosswalk_path)
    if not isinstance(ledger, Mapping) or not isinstance(crosswalk, Mapping):
        raise GateError(
            "GA12-SOURCE-STANDARDS-SHAPE",
            "source ledger and standards crosswalk must be objects",
        )
    resources = (
        base_common_path,
        legacy_common_path,
        COMMON_SCHEMA_PATH,
        ledger_schema_path,
        custody_schema_path,
    )
    for path, instance, schema_path in (
        (ledger_path, ledger, ledger_schema_path),
        (crosswalk_path, crosswalk, crosswalk_schema_path),
    ):
        validator = validator_for_schema(
            snapshot,
            dependencies,
            schema_path,
            resources,
        )
        errors = schema_error_records(validator, instance)
        if errors:
            first = errors[0]
            raise GateError(
                "GA12-SOURCE-STANDARDS-SCHEMA",
                f"{path} failed {first['schema_keyword']} at "
                f"{first['instance_pointer']}: {first['message']}",
            )
    validate_reference_bytes(
        snapshot,
        crosswalk["source_ledger_ref"],
        ledger_path,
        "GA12-SOURCE-STANDARDS-LEDGER-BINDING",
    )
    records = ledger.get("records")
    entries = crosswalk.get("entries")
    if not isinstance(records, list) or not isinstance(entries, list):
        raise GateError(
            "GA12-SOURCE-STANDARDS-SHAPE",
            "source records and crosswalk entries must be arrays",
        )
    source_ids = [row.get("source_id") for row in records if isinstance(row, Mapping)]
    mapping_ids = [row.get("mapping_id") for row in entries if isinstance(row, Mapping)]
    if (
        len(source_ids) != len(records)
        or len(source_ids) != len(set(source_ids))
        or len(mapping_ids) != len(entries)
        or len(mapping_ids) != len(set(mapping_ids))
    ):
        raise GateError(
            "GA12-SOURCE-STANDARDS-IDENTITY",
            "source and mapping identifiers must be complete and unique",
        )
    records_by_id = {row["source_id"]: row for row in records}
    retained_paths: set[str] = set()
    retained_eligible_ids: set[str] = set()
    pointer_ids: set[str] = set()
    for record in records:
        retained = record.get("retained_payload")
        if record.get("custody_state") == "retained_payload":
            if (
                record.get("record_role") != "retained_source"
                or record.get("evidence_eligibility") != "eligible_for_proposed_mapping"
                or not isinstance(retained, Mapping)
            ):
                raise GateError(
                    "GA12-SOURCE-STANDARDS-CUSTODY",
                    f"retained source contract differs: {record['source_id']}",
                )
            path = retained.get("path")
            if not isinstance(path, str) or path in retained_paths:
                raise GateError(
                    "GA12-SOURCE-STANDARDS-CUSTODY",
                    f"retained payload path is invalid or duplicate: {record['source_id']}",
                )
            item = snapshot.files.get(path)
            if (
                item is None
                or retained.get("sha256") != f"sha256:{item.sha256}"
                or retained.get("byte_size") != item.size
                or retained.get("media_type") != "application/octet-stream"
            ):
                raise GateError(
                    "GA12-SOURCE-STANDARDS-PAYLOAD-BINDING",
                    f"retained source payload bytes or media type differ: {path}",
                )
            retained_paths.add(path)
            retained_eligible_ids.add(record["source_id"])
        else:
            if (
                record.get("record_role") != "historical_pointer"
                or record.get("custody_state") != "pointer_only"
                or record.get("evidence_eligibility") != "ineligible_pointer_only"
                or retained is not None
            ):
                raise GateError(
                    "GA12-SOURCE-STANDARDS-CUSTODY",
                    f"pointer-only source contract differs: {record['source_id']}",
                )
            pointer_ids.add(record["source_id"])
    source_payload_paths = {
        path for path in snapshot.files if path.startswith("evidence/sources/")
    }
    if retained_paths != source_payload_paths:
        raise GateError(
            "GA12-SOURCE-STANDARDS-UNLEDGERED",
            "retained source directory and ledger payload set differ: "
            f"unledgered={sorted(source_payload_paths - retained_paths)}, "
            f"missing={sorted(retained_paths - source_payload_paths)}",
        )
    for entry in entries:
        identity_ref = entry.get("identity_source_ref")
        evidence_refs = entry.get("evidence_source_refs")
        discovery_refs = entry.get("discovery_source_refs")
        if (
            not isinstance(identity_ref, Mapping)
            or not isinstance(evidence_refs, list)
            or not isinstance(discovery_refs, list)
        ):
            raise GateError(
                "GA12-SOURCE-STANDARDS-REFERENCE",
                f"mapping reference arrays differ: {entry['mapping_id']}",
            )
        referenced = [identity_ref, *evidence_refs, *discovery_refs]
        for reference in referenced:
            source_id = reference.get("source_id")
            record = records_by_id.get(source_id)
            if record is None or reference.get("version") != record.get("version"):
                raise GateError(
                    "GA12-SOURCE-STANDARDS-REFERENCE",
                    f"mapping source reference does not resolve exactly: {entry['mapping_id']}",
                )
        if entry.get("mapping_state") == "partial_mapping":
            evidence_ids = [ref["source_id"] for ref in evidence_refs]
            if (
                not evidence_ids
                or not set(evidence_ids).issubset(retained_eligible_ids)
                or discovery_refs
            ):
                raise GateError(
                    "GA12-SOURCE-STANDARDS-ELIGIBILITY",
                    f"partial mapping evidence eligibility differs: {entry['mapping_id']}",
                )
            identity = records_by_id[identity_ref["source_id"]]
            external = entry.get("external_reference")
            if not isinstance(external, Mapping):
                raise GateError(
                    "GA12-SOURCE-STANDARDS-IDENTITY",
                    f"external identity is absent: {entry['mapping_id']}",
                )
            field_map = {
                "title": "title",
                "document_identifier": "document_identifier",
                "exact_version": "exact_version",
                "publication_date": "publication_date",
                "publisher": "publisher",
            }
            for external_key, record_key in field_map.items():
                record_value = identity.get(record_key)
                expected = (
                    record_value
                    if isinstance(record_value, Mapping)
                    else {"state": "observed", "value": record_value}
                )
                if external.get(external_key) != expected:
                    raise GateError(
                        "GA12-SOURCE-STANDARDS-IDENTITY",
                        f"mapping identity differs at {external_key}: {entry['mapping_id']}",
                    )
            for field in ("scope", "comparator", "requirement_locator"):
                value = entry.get(field)
                if not isinstance(value, Mapping) or value.get("state") != "observed":
                    raise GateError(
                        "GA12-SOURCE-STANDARDS-SCOPE",
                        f"partial mapping lacks observed {field}: {entry['mapping_id']}",
                    )
        elif entry.get("mapping_state") == "evidence_gap":
            if evidence_refs or not all(
                ref.get("source_id") in pointer_ids for ref in discovery_refs
            ):
                raise GateError(
                    "GA12-SOURCE-STANDARDS-ELIGIBILITY",
                    f"evidence-gap mapping admits eligible evidence: {entry['mapping_id']}",
                )
            for field in ("scope", "requirement_locator"):
                value = entry.get(field)
                if not isinstance(value, Mapping) or value.get("state") != "unmeasured":
                    raise GateError(
                        "GA12-SOURCE-STANDARDS-SCOPE",
                        f"evidence-gap mapping must keep {field} unmeasured: {entry['mapping_id']}",
                    )
            comparator = entry.get("comparator")
            exact_internal_comparator = {
                "state": "observed",
                "value": "NIST AI RMF 1.0 generic voluntary risk framework versus "
                "the proposed automotive evidence protocol "
                "reiyah.protocol.harbor-gate-a@1.1.0; no framework "
                "implementation or profile is claimed.",
            }
            if not (
                isinstance(comparator, Mapping)
                and (
                    comparator.get("state") == "unmeasured"
                    or (
                        entry.get("mapping_id")
                        == "map.nist.ai-rmf-1.0.risk-governance"
                        and comparator == exact_internal_comparator
                    )
                )
            ):
                raise GateError(
                    "GA12-SOURCE-STANDARDS-SCOPE",
                    "evidence-gap comparator is neither unmeasured nor the exact "
                    f"bounded internal declaration: {entry['mapping_id']}",
                )
        else:
            raise GateError(
                "GA12-SOURCE-STANDARDS-SCOPE",
                f"unsupported mapping state: {entry['mapping_id']}",
            )
    if crosswalk.get("compliance_claimed") is not False:
        raise GateError(
            "GA12-SOURCE-STANDARDS-NONCLAIM",
            "the standards crosswalk must not claim compliance",
        )
    return {
        "source_record_count": len(records),
        "retained_payload_count": len(retained_paths),
        "pointer_only_count": len(pointer_ids),
        "mapping_count": len(entries),
        "retained_payload_set_sha256": artifact_set_digest(
            snapshot, sorted(retained_paths)
        ),
        "mapping_set_sha256": evidence_sha256(entries),
    }


def validate_threat_no_runtime_boundary(
    snapshot: RepositorySnapshot,
    plan: Mapping[str, Any],
    candidate: CandidateProjection,
) -> dict[str, Any]:
    threat_path = "docs/THREAT_MODEL.md"
    try:
        text = snapshot.read(threat_path).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GateError(
            "GA12-THREAT-MODEL-UTF8",
            "threat model must be strict UTF-8",
        ) from exc
    threat_ids = re.findall(r"^\| \`(TM-[0-9]{3})\` \|", text, re.MULTILINE)
    expected_threat_ids = [f"TM-{index:03d}" for index in range(1, 38)]
    if threat_ids != expected_threat_ids or len(threat_ids) != len(set(threat_ids)):
        raise GateError(
            "GA12-THREAT-MODEL-COVERAGE",
            "threat model must contain the exact ordered TM-001 through TM-037 catalogue",
        )
    profile = strict_json(
        snapshot.read(SCIENTIFIC_PROFILE_PATH), SCIENTIFIC_PROFILE_PATH
    )
    protocol = strict_json(
        snapshot.read(PROTOCOL_MANIFEST_PATH), PROTOCOL_MANIFEST_PATH
    )
    if not isinstance(profile, Mapping) or not isinstance(protocol, Mapping):
        raise GateError(
            "GA12-NO-RUNTIME-BOUNDARY",
            "protocol and scientific profile must be objects",
        )
    false_flag_names = {
        "runtime_authorized",
        "runtime_execution_authorized",
        "gate_b_authorized",
        "acceptance_authorized",
        "scientific_support_claimed",
        "safety_case_claimed",
    }
    observed_flags: list[dict[str, Any]] = []

    def visit_flags(value: Any, pointer: str) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                child_pointer = _instance_pointer_child(pointer, key)
                if key in false_flag_names:
                    if child is not False:
                        raise GateError(
                            "GA12-NO-RUNTIME-BOUNDARY",
                            f"authority flag must remain false at {child_pointer}",
                        )
                    observed_flags.append({"pointer": child_pointer, "value": False})
                visit_flags(child, child_pointer)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit_flags(child, _instance_pointer_child(pointer, index))

    visit_flags(plan, "/plan")
    visit_flags(protocol, "/protocol")
    visit_flags(profile, "/profile")
    prohibited_path_patterns = (
        re.compile(
            r"(^|/)(?:runtime|deployment|private-data|training|inference|models?|services?)(?:/|$)",
            re.I,
        ),
        re.compile(
            r"(^|/)(?:Dockerfile|docker-compose[^/]*|\.env|credentials?[^/]*|secrets?[^/]*)$",
            re.I,
        ),
        re.compile(r"\.(?:onnx|pt|pth|ckpt|tflite|pb|joblib|pickle|pem|key)$", re.I),
    )
    prohibited_paths = [
        path
        for path in candidate.files
        if any(pattern.search(path) for pattern in prohibited_path_patterns)
    ]
    if prohibited_paths:
        raise GateError(
            "GA12-NO-RUNTIME-PATH",
            f"candidate projection contains prohibited runtime/private artifacts: {prohibited_paths}",
        )
    allowed_executable_paths = {LAUNCHER_PATH, TOOL_PATH, SCIENCE_MODULE_PATH}
    executable_current_paths = {
        path
        for path, item in candidate.files.items()
        if path in allowed_executable_paths or item.mode in {"100755", "0755"}
    }
    unexpected_executable_paths = sorted(
        executable_current_paths - allowed_executable_paths
    )
    if unexpected_executable_paths:
        raise GateError(
            "GA12-NO-RUNTIME-EXECUTABLE",
            f"candidate has executable paths outside the validator surface: {unexpected_executable_paths}",
        )
    planned_rules = plan.get("rules")
    controls = plan.get("control_contract", {}).get("offline_control_ids")
    if not isinstance(planned_rules, list) or not isinstance(controls, list):
        raise GateError(
            "GA12-THREAT-RULE-CROSSLINK",
            "plan rule and control contracts must be arrays",
        )
    linked_threat_ids = {
        threat_id for row in planned_rules for threat_id in row.get("threat_ids", ())
    }
    linked_control_ids = {
        control_id
        for row in planned_rules
        for control_id in row.get("gate_controls", ())
    }
    if linked_threat_ids != set(expected_threat_ids) or linked_control_ids != set(
        controls
    ):
        raise GateError(
            "GA12-THREAT-RULE-CROSSLINK",
            "plan rule crosslinks must cover the exact threat and offline-control universes",
        )
    validate_candidate_contract(snapshot, plan, candidate)
    return {
        "threat_count": len(threat_ids),
        "rule_count": len(planned_rules),
        "control_count": len(controls),
        "false_authority_flag_count": len(observed_flags),
        "candidate_artifact_count": candidate.artifact_count,
        "allowed_executable_count": len(executable_current_paths),
        "threat_set_sha256": evidence_sha256(threat_ids),
        "authority_flag_set_sha256": evidence_sha256(observed_flags),
    }


class StageEvidenceCollector:
    """Emit closed stage rows only from completed producer observations."""

    def __init__(
        self,
        candidate_projection_sha256: str,
        required_token_ids: Sequence[str],
    ) -> None:
        self._candidate_projection_sha256 = candidate_projection_sha256
        self._required_token_ids = tuple(required_token_ids)
        self._rows: list[dict[str, Any]] = []
        self._observed: set[str] = set()

    def record(
        self,
        token_id: str,
        producer_check_id: str,
        observations: Sequence[tuple[str, int, Any]],
    ) -> None:
        if token_id not in self._required_token_ids:
            raise GateError(
                "GA12-STAGE-EVIDENCE-UNEXPECTED",
                f"stage collector received an unexpected token: {token_id}",
            )
        if token_id in self._observed:
            raise GateError(
                "GA12-STAGE-EVIDENCE-DUPLICATE",
                f"stage collector received a duplicate token: {token_id}",
            )
        expected_index = len(self._rows)
        if self._required_token_ids[expected_index] != token_id:
            raise GateError(
                "GA12-STAGE-EVIDENCE-ORDER",
                f"stage token order differs at position {expected_index}: {token_id}",
            )
        expected_producer = STAGE_PRODUCER_DISPATCH.get(token_id)
        if producer_check_id != expected_producer:
            raise GateError(
                "GA12-STAGE-EVIDENCE-PRODUCER",
                f"stage producer differs for {token_id}: {producer_check_id}",
            )
        observation_rows: list[dict[str, Any]] = []
        observation_ids: set[str] = set()
        for observation_id, subject_count, payload in observations:
            if observation_id in observation_ids:
                raise GateError(
                    "GA12-STAGE-EVIDENCE-OBSERVATION-DUPLICATE",
                    f"duplicate observation ID for {token_id}: {observation_id}",
                )
            if (
                not isinstance(subject_count, int)
                or isinstance(subject_count, bool)
                or subject_count < 1
            ):
                raise GateError(
                    "GA12-STAGE-EVIDENCE-SUBJECT-COUNT",
                    f"invalid subject count for {observation_id}",
                )
            observation_ids.add(observation_id)
            observation_rows.append(
                {
                    "observation_id": observation_id,
                    "subject_count": subject_count,
                    "evidence_sha256": evidence_sha256(payload),
                }
            )
        if not observation_rows:
            raise GateError(
                "GA12-STAGE-EVIDENCE-OBSERVATION-MISSING",
                f"stage token has no completed producer observation: {token_id}",
            )
        observed_observation_ids = tuple(
            row["observation_id"] for row in observation_rows
        )
        expected_observation_ids = STAGE_OBSERVATION_DISPATCH[token_id]
        if observed_observation_ids != expected_observation_ids:
            raise GateError(
                "GA12-STAGE-EVIDENCE-OBSERVATION-DISPATCH",
                f"stage observations differ for {token_id}: "
                f"expected={expected_observation_ids}, "
                f"observed={observed_observation_ids}",
            )
        row = {
            "token_id": token_id,
            "producer_check_id": producer_check_id,
            "candidate_projection_sha256": self._candidate_projection_sha256,
            "observations": observation_rows,
        }
        row["evidence_sha256"] = evidence_sha256(row)
        self._rows.append(row)
        self._observed.add(token_id)

    def finish(self) -> list[dict[str, Any]]:
        observed_ids = [row["token_id"] for row in self._rows]
        if observed_ids != list(self._required_token_ids):
            missing = [
                token_id
                for token_id in self._required_token_ids
                if token_id not in self._observed
            ]
            raise GateError(
                "GA12-STAGE-EVIDENCE-MISSING",
                f"stage collector is incomplete: {missing}",
            )
        return copy.deepcopy(self._rows)


def artifact_rows_for_paths(
    snapshot: RepositorySnapshot,
    paths: Sequence[str],
) -> list[dict[str, Any]]:
    if len(paths) != len(set(paths)):
        raise GateError(
            "GA12-EVIDENCE-ARTIFACT-DUPLICATE",
            "artifact evidence preimage contains a duplicate path",
        )
    rows: list[dict[str, Any]] = []
    for path in paths:
        item = snapshot.files.get(path)
        if item is None:
            raise GateError(
                "GA12-EVIDENCE-ARTIFACT-MISSING",
                f"evidence artifact path is absent: {path}",
            )
        rows.append({"path": path, "sha256": item.sha256, "size": item.size})
    return rows


def current_catalog_rows_by_id(
    snapshot: RepositorySnapshot,
) -> dict[str, Mapping[str, Any]]:
    catalog_path = "fixtures/fixture-catalog.json"
    catalog = strict_json(snapshot.read(catalog_path), catalog_path)
    if not isinstance(catalog, Mapping) or not isinstance(
        catalog.get("fixtures"), list
    ):
        raise GateError(
            "GA12-FIXTURE-CATALOG-SHAPE",
            "validated fixture catalog is unavailable for evidence projection",
        )
    rows: dict[str, Mapping[str, Any]] = {}
    paths: set[str] = set()
    for row in catalog["fixtures"]:
        if (
            not isinstance(row, Mapping)
            or row.get("replay_mode") == "retained_not_replayed"
        ):
            continue
        fixture_id = row.get("fixture_id")
        path = row.get("path")
        if (
            not isinstance(fixture_id, str)
            or not isinstance(path, str)
            or fixture_id in rows
            or path in paths
        ):
            raise GateError(
                "GA12-FIXTURE-CATALOG-IDENTITY",
                "current evidence catalog IDs and paths must be unique",
            )
        item = snapshot.files.get(path)
        if (
            item is None
            or row.get("sha256") != f"sha256:{item.sha256}"
            or row.get("byte_size") != item.size
        ):
            raise GateError(
                "GA12-FIXTURE-CATALOG-BYTE-BINDING",
                f"catalog evidence row does not bind live bytes: {fixture_id}",
            )
        rows[fixture_id] = row
        paths.add(path)
    return rows


def artifact_rows_for_fixture_ids(
    snapshot: RepositorySnapshot,
    catalog_by_id: Mapping[str, Mapping[str, Any]],
    fixture_ids: Sequence[str],
) -> list[dict[str, Any]]:
    if len(fixture_ids) != len(set(fixture_ids)):
        raise GateError(
            "GA12-EVIDENCE-SELECTOR-FIXTURE-DUPLICATE",
            "fixture evidence preimage contains a duplicate fixture ID",
        )
    paths: list[str] = []
    for fixture_id in fixture_ids:
        row = catalog_by_id.get(fixture_id)
        if row is None:
            raise GateError(
                "GA12-EVIDENCE-SELECTOR-FIXTURE-MISSING",
                f"evidence fixture ID does not resolve in the validated catalog: {fixture_id}",
            )
        paths.append(str(row["path"]))
    return artifact_rows_for_paths(snapshot, paths)


def build_nested_contract_evidence(
    snapshot: RepositorySnapshot,
    candidate: CandidateProjection,
    plan: Mapping[str, Any],
    science: Mapping[str, Any],
    catalog_by_id: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    profile = strict_json(
        snapshot.read(SCIENTIFIC_PROFILE_PATH), SCIENTIFIC_PROFILE_PATH
    )
    if not isinstance(profile, Mapping):
        raise GateError(
            "GA12-NESTED-CONTRACT-EVIDENCE",
            "scientific profile must be an object",
        )
    contracts: dict[str, Mapping[str, Any]] = {}
    for row in profile.get("derived_invariant_contracts", ()):
        if not isinstance(row, Mapping):
            raise GateError(
                "GA12-NESTED-CONTRACT-EVIDENCE",
                "derived contract row must be an object",
            )
        contract_id = row.get("executable_contract_id")
        if not isinstance(contract_id, str) or contract_id in contracts:
            raise GateError(
                "GA12-NESTED-CONTRACT-EVIDENCE",
                "derived contract IDs must be complete and unique",
            )
        contracts[contract_id] = row
    for row in profile.get("cross_cutting_rule_contracts", ()):
        if not isinstance(row, Mapping):
            raise GateError(
                "GA12-NESTED-CONTRACT-EVIDENCE",
                "cross-cutting contract row must be an object",
            )
        contract_id = row.get("contract_id")
        if not isinstance(contract_id, str) or contract_id in contracts:
            raise GateError(
                "GA12-NESTED-CONTRACT-EVIDENCE",
                "cross-cutting contract IDs must be complete and unique",
            )
        contracts[contract_id] = row
    declared_contract_ids = plan["stage_evidence_contract"]["nested_contract_ids"]
    if list(contracts) != list(declared_contract_ids):
        raise GateError(
            "GA12-NESTED-CONTRACT-EVIDENCE",
            "profile contract order differs from the plan stage contract",
        )
    fixture_binding_by_id = {
        row["fixture_id"]: row
        for row in profile.get("fixture_bindings", ())
        if isinstance(row, Mapping) and isinstance(row.get("fixture_id"), str)
    }
    diagnostic_rows = science.get("diagnostics")
    if not isinstance(diagnostic_rows, list):
        raise GateError(
            "GA12-NESTED-CONTRACT-EVIDENCE",
            "science diagnostic rows are unavailable",
        )
    result: list[dict[str, Any]] = []
    projection_sha256 = f"sha256:{candidate.sha256}"
    for contract_id in declared_contract_ids:
        contract = contracts[contract_id]
        application_schema_ids = list(contract["application_schema_ids"])
        production_rule_ids = list(contract["required_rule_ids"])
        known_good_fixture_ids = list(contract["good_fixture_ids"])
        known_bad_fixture_ids = sorted(
            {
                diagnostic["fixture_id"]
                for diagnostic in diagnostic_rows
                if diagnostic["rule_id"] in set(production_rule_ids)
            }
        )
        if not all(
            (
                application_schema_ids,
                production_rule_ids,
                known_good_fixture_ids,
                known_bad_fixture_ids,
            )
        ):
            raise GateError(
                "GA12-NESTED-CONTRACT-EVIDENCE",
                f"nested contract lacks positive or negative evidence: {contract_id}",
            )
        try:
            application_paths = [
                APPLICATION_SCHEMA_PATH_BY_ID[schema_id]
                for schema_id in application_schema_ids
            ]
        except KeyError as exc:
            raise GateError(
                "GA12-NESTED-CONTRACT-EVIDENCE",
                f"nested contract names an unknown application schema: {contract_id}",
            ) from exc
        for fixture_id in (*known_good_fixture_ids, *known_bad_fixture_ids):
            if fixture_id not in fixture_binding_by_id:
                raise GateError(
                    "GA12-NESTED-CONTRACT-EVIDENCE",
                    f"profile fixture binding is absent for {fixture_id}",
                )
            if fixture_id not in catalog_by_id:
                raise GateError(
                    "GA12-NESTED-CONTRACT-EVIDENCE",
                    f"catalog fixture binding is absent for {fixture_id}",
                )
            if (
                fixture_binding_by_id[fixture_id]["path"]
                != catalog_by_id[fixture_id]["path"]
            ):
                raise GateError(
                    "GA12-NESTED-CONTRACT-EVIDENCE",
                    f"profile and catalog fixture paths differ for {fixture_id}",
                )
        row = {
            "contract_id": contract_id,
            "producer_check_id": NESTED_CONTRACT_PRODUCER_DISPATCH[contract_id],
            "candidate_projection_sha256": projection_sha256,
            "application_schema_ids": application_schema_ids,
            "production_rule_ids": production_rule_ids,
            "application_schema_set_sha256": evidence_sha256(
                artifact_rows_for_paths(snapshot, application_paths)
            ),
            "production_rule_set_sha256": evidence_sha256(production_rule_ids),
            "known_good_fixture_ids": known_good_fixture_ids,
            "known_bad_fixture_ids": known_bad_fixture_ids,
            "known_good_fixture_set_sha256": evidence_sha256(
                artifact_rows_for_fixture_ids(
                    snapshot, catalog_by_id, known_good_fixture_ids
                )
            ),
            "known_bad_fixture_set_sha256": evidence_sha256(
                artifact_rows_for_fixture_ids(
                    snapshot, catalog_by_id, known_bad_fixture_ids
                )
            ),
        }
        row["evidence_sha256"] = evidence_sha256(row)
        result.append(row)
    return result


def project_selector_evidence_row(
    snapshot: RepositorySnapshot,
    candidate_projection_sha256: str,
    declared: Mapping[str, Any],
    selector_id: str,
    expected: Mapping[str, Any],
    catalog_by_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    producer_to_token = {
        producer: token for token, producer in STAGE_PRODUCER_DISPATCH.items()
    }
    required_keys = {
        "selector_id",
        "producer_stage_token_id",
        "producer_check_id",
        "required_observations",
        "projection_policy",
    }
    require_exact_keys(
        declared,
        required_keys,
        f"evidence selector registry row {selector_id}",
    )
    producer_check_id = expected["producer_check_id"]
    expected_token_id = producer_to_token[producer_check_id]
    if (
        declared["selector_id"] != selector_id
        or declared["producer_check_id"] != producer_check_id
        or declared["producer_stage_token_id"] != expected_token_id
        or declared["projection_policy"]
        != "ordered_fixture_ids_resolved_through_validated_catalog_to_path_sha256_size"
    ):
        raise GateError(
            "GA12-PLAN-EVIDENCE-SELECTOR-PRODUCER",
            f"selector producer or projection policy differs: {selector_id}",
        )
    expected_observations = expected["required_observations"]
    declared_observations = declared["required_observations"]
    if len(declared_observations) != len(expected_observations):
        raise GateError(
            "GA12-PLAN-EVIDENCE-SELECTOR-OBSERVATION-MISSING",
            f"selector observation count differs: {selector_id}",
        )
    projections: list[dict[str, Any]] = []
    for declared_observation, expected_observation in zip(
        declared_observations, expected_observations, strict=True
    ):
        require_exact_keys(
            declared_observation,
            {"observation_id", "fixture_ids", "fixture_set_sha256"},
            f"selector observation {selector_id}",
        )
        if (
            declared_observation["observation_id"]
            != expected_observation["observation_id"]
        ):
            raise GateError(
                "GA12-PLAN-EVIDENCE-SELECTOR-OBSERVATION-MISSING",
                f"selector observation ID differs: {selector_id}",
            )
        fixture_ids = list(expected_observation["fixture_ids"])
        declared_fixture_ids = declared_observation["fixture_ids"]
        if declared_fixture_ids != fixture_ids:
            expected_set = set(fixture_ids)
            declared_set = set(declared_fixture_ids)
            diagnostic = (
                "GA12-PLAN-EVIDENCE-SELECTOR-FIXTURE-MISSING"
                if expected_set - declared_set
                else "GA12-PLAN-EVIDENCE-SELECTOR-FIXTURE-UNEXPECTED"
            )
            raise GateError(
                diagnostic,
                f"selector fixture set/order differs: {selector_id}",
            )
        digest = evidence_sha256(
            artifact_rows_for_fixture_ids(snapshot, catalog_by_id, fixture_ids)
        )
        if declared_observation["fixture_set_sha256"] != digest:
            raise GateError(
                "GA12-PLAN-EVIDENCE-SELECTOR-DIGEST",
                f"selector artifact-set digest differs: {selector_id}",
            )
        projections.append(
            {
                "observation_id": expected_observation["observation_id"],
                "fixture_ids": fixture_ids,
                "fixture_set_sha256": digest,
            }
        )
    row = {
        "selector_id": selector_id,
        "producer_stage_token_id": expected_token_id,
        "candidate_projection_sha256": candidate_projection_sha256,
        "observation_projections": projections,
    }
    row["evidence_sha256"] = evidence_sha256(row)
    return row


def build_selector_evidence(
    snapshot: RepositorySnapshot,
    candidate: CandidateProjection,
    plan: Mapping[str, Any],
    catalog_by_id: Mapping[str, Mapping[str, Any]],
    expected_dispatch: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    correction = plan.get("correction_closure_contract")
    registry = (
        correction.get("evidence_selector_registry")
        if isinstance(correction, Mapping)
        else None
    )
    if not isinstance(registry, list):
        raise GateError(
            "GA12-PLAN-EVIDENCE-SELECTOR-REGISTRY",
            "plan evidence selector registry must be an ordered array",
        )
    if [row.get("selector_id") for row in registry] != list(expected_dispatch):
        raise GateError(
            "GA12-PLAN-EVIDENCE-SELECTOR-REGISTRY",
            "plan selector order/set differs from the executable selector dispatch",
        )
    projection_sha256 = f"sha256:{candidate.sha256}"
    result: list[dict[str, Any]] = []
    for declared, (selector_id, expected) in zip(
        registry, expected_dispatch.items(), strict=True
    ):
        result.append(
            project_selector_evidence_row(
                snapshot,
                projection_sha256,
                declared,
                selector_id,
                expected,
                catalog_by_id,
            )
        )
    return result


def reduce_control_evidence(
    plan: Mapping[str, Any],
    observed_token_ids: Sequence[str],
    observed_nested_contract_ids: Sequence[str],
) -> dict[str, Any]:
    token_set = set(observed_token_ids)
    nested_set = set(observed_nested_contract_ids)
    requirements = plan["control_contract"]["control_evidence_requirements"]
    required_ids = list(plan["control_contract"]["offline_control_ids"])
    results: list[dict[str, Any]] = []
    covered_ids: list[str] = []
    passed_ids: list[str] = []
    failed_ids: list[str] = []
    for requirement in requirements:
        control_id = requirement["control_id"]
        required_tokens = list(requirement["required_stage_token_ids"])
        required_nested = list(requirement["required_nested_contract_ids"])
        observed_tokens = [
            token_id for token_id in required_tokens if token_id in token_set
        ]
        observed_nested = [
            contract_id for contract_id in required_nested if contract_id in nested_set
        ]
        missing_tokens = [
            token_id for token_id in required_tokens if token_id not in token_set
        ]
        missing_nested = [
            contract_id
            for contract_id in required_nested
            if contract_id not in nested_set
        ]
        if all(
            token_id in STAGE_PRODUCER_DISPATCH for token_id in required_tokens
        ) and all(
            contract_id in NESTED_CONTRACT_PRODUCER_DISPATCH
            for contract_id in required_nested
        ):
            covered_ids.append(control_id)
        status = "pass" if not missing_tokens and not missing_nested else "fail"
        (passed_ids if status == "pass" else failed_ids).append(control_id)
        result = {
            "control_id": control_id,
            "required_stage_token_ids": required_tokens,
            "observed_stage_token_ids": observed_tokens,
            "missing_stage_token_ids": missing_tokens,
            "required_nested_contract_ids": required_nested,
            "observed_nested_contract_ids": observed_nested,
            "missing_nested_contract_ids": missing_nested,
            "status": status,
        }
        result["evidence_sha256"] = evidence_sha256(result)
        results.append(result)
    if [row["control_id"] for row in requirements] != required_ids:
        raise GateError(
            "GA12-CONTROL-REDUCER-COVERAGE",
            "control evidence requirements do not match the required control order",
        )
    summary = {
        "required_control_ids": required_ids,
        "covered_control_ids": covered_ids,
        "passed_control_ids": passed_ids,
        "failed_control_ids": failed_ids,
        "results": results,
        "external_control": {
            "control_id": plan["control_contract"]["external_control_id"],
            "status": plan["control_contract"]["external_control_state"],
            "decision_record_id": None,
        },
    }
    summary["evidence_sha256"] = evidence_sha256(summary)
    return summary


def reduce_correction_evidence(
    plan: Mapping[str, Any],
    token_rows: Sequence[Mapping[str, Any]],
    nested_rows: Sequence[Mapping[str, Any]],
    selector_rows: Sequence[Mapping[str, Any]],
    catalog_by_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    token_ids = [row["token_id"] for row in token_rows]
    nested_by_id = {row["contract_id"]: row for row in nested_rows}
    selector_by_id = {row["selector_id"]: row for row in selector_rows}
    token_set = set(token_ids)
    correction = plan["correction_closure_contract"]
    common_tokens = list(correction["common_required_stage_token_ids"])
    requirements = correction["finding_evidence_requirements"]
    required_ids = list(correction["required_finding_ids"])
    results: list[dict[str, Any]] = []
    closed_ids: list[str] = []
    open_ids: list[str] = []
    for requirement in requirements:
        finding_id = requirement["finding_id"]
        required_tokens = ordered_unique(
            [
                *common_tokens,
                *requirement["additional_required_stage_token_ids"],
            ]
        )
        required_nested = list(requirement["required_nested_contract_ids"])
        required_selectors = list(requirement["required_evidence_selectors"])
        observed_tokens = [
            token_id for token_id in required_tokens if token_id in token_set
        ]
        observed_nested = [
            contract_id
            for contract_id in required_nested
            if contract_id in nested_by_id
        ]
        observed_selectors = [
            selector_id
            for selector_id in required_selectors
            if selector_id in selector_by_id
        ]
        missing_tokens = [
            token_id for token_id in required_tokens if token_id not in token_set
        ]
        missing_nested = [
            contract_id
            for contract_id in required_nested
            if contract_id not in nested_by_id
        ]
        missing_selectors = [
            selector_id
            for selector_id in required_selectors
            if selector_id not in selector_by_id
        ]
        production_rule_ids: list[str] = []
        known_good_fixture_ids: list[str] = []
        known_bad_fixture_ids: list[str] = []
        for contract_id in required_nested:
            row = nested_by_id.get(contract_id)
            if row is None:
                continue
            production_rule_ids.extend(row["production_rule_ids"])
            known_good_fixture_ids.extend(row["known_good_fixture_ids"])
            known_bad_fixture_ids.extend(row["known_bad_fixture_ids"])
        for selector_id in required_selectors:
            row = selector_by_id.get(selector_id)
            if row is None:
                continue
            for observation in row["observation_projections"]:
                for fixture_id in observation["fixture_ids"]:
                    catalog_row = catalog_by_id.get(fixture_id)
                    if catalog_row is None:
                        raise GateError(
                            "GA12-CORRECTION-EVIDENCE-RESOLUTION",
                            f"selector fixture does not resolve: {fixture_id}",
                        )
                    classification = catalog_row["classification"]
                    if classification == "known_good":
                        known_good_fixture_ids.append(fixture_id)
                    elif classification == "known_bad":
                        known_bad_fixture_ids.append(fixture_id)
                        rule_id = catalog_row.get("expected_primary_rule_id")
                        if not isinstance(rule_id, str):
                            raise GateError(
                                "GA12-CORRECTION-EVIDENCE-RESOLUTION",
                                f"known-bad selector fixture lacks a production rule: {fixture_id}",
                            )
                        production_rule_ids.append(rule_id)
                    else:
                        raise GateError(
                            "GA12-CORRECTION-EVIDENCE-RESOLUTION",
                            f"selector fixture has unsupported classification: {fixture_id}",
                        )
        status = (
            "closed"
            if not missing_tokens and not missing_nested and not missing_selectors
            else "open"
        )
        (closed_ids if status == "closed" else open_ids).append(finding_id)
        result = {
            "finding_id": finding_id,
            "required_stage_token_ids": required_tokens,
            "observed_stage_token_ids": observed_tokens,
            "missing_stage_token_ids": missing_tokens,
            "required_nested_contract_ids": required_nested,
            "observed_nested_contract_ids": observed_nested,
            "missing_nested_contract_ids": missing_nested,
            "required_evidence_selector_ids": required_selectors,
            "observed_evidence_selector_ids": observed_selectors,
            "missing_evidence_selector_ids": missing_selectors,
            "production_rule_ids": ordered_unique(production_rule_ids),
            "known_good_fixture_ids": ordered_unique(known_good_fixture_ids),
            "known_bad_fixture_ids": ordered_unique(known_bad_fixture_ids),
        }
        result["evidence_projection_sha256"] = evidence_sha256(result)
        result["status"] = status
        results.append(result)
    if [row["finding_id"] for row in requirements] != required_ids:
        raise GateError(
            "GA12-CORRECTION-REDUCER-COVERAGE",
            "finding evidence requirements do not match required finding order",
        )
    summary = {
        "required_finding_ids": required_ids,
        "closed_finding_ids": closed_ids,
        "open_finding_ids": open_ids,
        "results": results,
    }
    summary["evidence_sha256"] = evidence_sha256(summary)
    return summary


def reduce_final_report_implication(
    stage_evidence: Mapping[str, Any],
    control_summary: Mapping[str, Any],
    closure_summary: Mapping[str, Any],
    fixture_summary: Mapping[str, Any],
    producer_diagnostics: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Pure, fail-closed derivation of the final report outcome tuple."""

    required_tokens = list(stage_evidence.get("required_token_ids", ()))
    observed_tokens = list(stage_evidence.get("observed_token_ids", ()))
    missing_tokens = list(stage_evidence.get("missing_token_ids", ()))
    unexpected_tokens = list(stage_evidence.get("unexpected_token_ids", ()))
    token_partition_valid = (
        len(required_tokens) == len(set(required_tokens))
        and len(observed_tokens) == len(set(observed_tokens))
        and missing_tokens
        == [token for token in required_tokens if token not in set(observed_tokens)]
        and unexpected_tokens
        == [token for token in observed_tokens if token not in set(required_tokens)]
    )
    required_controls = list(control_summary.get("required_control_ids", ()))
    passed_controls = list(control_summary.get("passed_control_ids", ()))
    failed_controls = list(control_summary.get("failed_control_ids", ()))
    control_partition_valid = (
        passed_controls
        == [item for item in required_controls if item not in set(failed_controls)]
        and not (set(passed_controls) & set(failed_controls))
        and set(passed_controls) | set(failed_controls) == set(required_controls)
    )
    required_findings = list(closure_summary.get("required_finding_ids", ()))
    closed_findings = list(closure_summary.get("closed_finding_ids", ()))
    open_findings = list(closure_summary.get("open_finding_ids", ()))
    finding_partition_valid = (
        closed_findings
        == [item for item in required_findings if item not in set(open_findings)]
        and not (set(closed_findings) & set(open_findings))
        and set(closed_findings) | set(open_findings) == set(required_findings)
    )
    unexpected_outcomes = fixture_summary.get("unexpected_outcomes")
    complete = (
        token_partition_valid
        and not missing_tokens
        and not unexpected_tokens
        and control_partition_valid
        and not failed_controls
        and finding_partition_valid
        and not open_findings
        and unexpected_outcomes == 0
        and not producer_diagnostics
    )
    diagnostics = [dict(row) for row in producer_diagnostics]
    if not complete:
        diagnostics.append(
            {
                "rule_id": "GA12-REPORT-IMPLICATION",
                "severity": "error",
                "path": PLAN_PATH,
                "object_id": "reiyah.validation-plan.gate-a-public-1.2.0",
                "message": (
                    "observed stage, control, correction, fixture, or producer "
                    "evidence does not imply architecture completeness"
                ),
            }
        )
    return {
        "complete": complete,
        "result": "pass" if complete else "fail",
        "exit_code": 0 if complete else 1,
        "architecture_status": ("architecture_complete" if complete else "invalid"),
        "diagnostics": diagnostics,
    }


def run_report_implication_canaries(plan: Mapping[str, Any]) -> dict[str, Any]:
    stage_ids = list(STAGE_PRODUCER_DISPATCH)
    precomparison_ids = stage_ids[:-1]
    nested_ids = list(NESTED_CONTRACT_PRODUCER_DISPATCH)
    selector_ids = list(EVIDENCE_SELECTOR_PRODUCER_DISPATCH)
    full_controls = reduce_control_evidence(plan, stage_ids, nested_ids)
    synthetic_nested = [
        {
            "contract_id": contract_id,
            "production_rule_ids": [f"GA12-SYNTHETIC-{index:03d}"],
            "known_good_fixture_ids": [f"reiyah.fixture.synthetic.good.{index}"],
            "known_bad_fixture_ids": [f"reiyah.fixture.synthetic.bad.{index}"],
        }
        for index, contract_id in enumerate(nested_ids, 1)
    ]
    synthetic_selectors = [
        {
            "selector_id": selector_id,
            "observation_projections": [],
        }
        for selector_id in selector_ids
    ]
    synthetic_catalog: dict[str, Mapping[str, Any]] = {}
    full_findings = reduce_correction_evidence(
        plan,
        [{"token_id": token_id} for token_id in stage_ids],
        synthetic_nested,
        synthetic_selectors,
        synthetic_catalog,
    )
    if (
        full_controls["passed_control_ids"] != full_controls["required_control_ids"]
        or full_controls["failed_control_ids"]
        or full_findings["closed_finding_ids"] != full_findings["required_finding_ids"]
        or full_findings["open_finding_ids"]
    ):
        raise GateError(
            "GA12-REPORT-IMPLICATION-CANARY",
            "complete synthetic evidence did not imply complete control/finding closure",
        )
    full_stage = {
        "required_token_ids": stage_ids,
        "observed_token_ids": stage_ids,
        "missing_token_ids": [],
        "unexpected_token_ids": [],
    }
    clean_fixtures = {"unexpected_outcomes": 0}
    complete_outcome = reduce_final_report_implication(
        full_stage, full_controls, full_findings, clean_fixtures
    )
    if complete_outcome != {
        "complete": True,
        "result": "pass",
        "exit_code": 0,
        "architecture_status": "architecture_complete",
        "diagnostics": [],
    }:
        raise GateError(
            "GA12-REPORT-IMPLICATION-CANARY",
            "complete synthetic evidence did not produce the exact success tuple",
        )
    missing_stage = precomparison_ids[0]
    stage_failure = reduce_control_evidence(
        plan,
        [token_id for token_id in stage_ids if token_id != missing_stage],
        nested_ids,
    )
    missing_nested = nested_ids[0]
    nested_failure = reduce_control_evidence(
        plan,
        stage_ids,
        [contract_id for contract_id in nested_ids if contract_id != missing_nested],
    )
    selector_failure = reduce_correction_evidence(
        plan,
        [{"token_id": token_id} for token_id in stage_ids],
        synthetic_nested,
        [row for row in synthetic_selectors if row["selector_id"] != selector_ids[0]],
        synthetic_catalog,
    )
    if (
        not stage_failure["failed_control_ids"]
        or not nested_failure["failed_control_ids"]
        or not selector_failure["open_finding_ids"]
    ):
        raise GateError(
            "GA12-REPORT-IMPLICATION-CANARY",
            "missing synthetic stage/nested/selector evidence did not fail closed",
        )
    missing_s20_stage = {
        **full_stage,
        "observed_token_ids": precomparison_ids,
        "missing_token_ids": [stage_ids[-1]],
    }
    missing_stage_state = {
        **full_stage,
        "observed_token_ids": [
            token_id for token_id in stage_ids if token_id != missing_stage
        ],
        "missing_token_ids": [missing_stage],
    }
    failure_cases = [
        (
            "missing_s20_fails",
            reduce_final_report_implication(
                missing_s20_stage, full_controls, full_findings, clean_fixtures
            ),
        ),
        (
            "missing_stage_or_failed_control_fails",
            reduce_final_report_implication(
                missing_stage_state, stage_failure, full_findings, clean_fixtures
            ),
        ),
        (
            "missing_nested_or_failed_control_fails",
            reduce_final_report_implication(
                full_stage, nested_failure, full_findings, clean_fixtures
            ),
        ),
        (
            "missing_selector_or_open_finding_fails",
            reduce_final_report_implication(
                full_stage, full_controls, selector_failure, clean_fixtures
            ),
        ),
        (
            "unexpected_fixture_outcome_fails",
            reduce_final_report_implication(
                full_stage,
                full_controls,
                full_findings,
                {"unexpected_outcomes": 1},
            ),
        ),
        (
            "producer_diagnostic_fails",
            reduce_final_report_implication(
                full_stage,
                full_controls,
                full_findings,
                clean_fixtures,
                (
                    {
                        "rule_id": "GA12-SYNTHETIC-PRODUCER",
                        "severity": "error",
                        "path": PLAN_PATH,
                        "object_id": "reiyah.synthetic",
                        "message": "synthetic producer diagnostic",
                    },
                ),
            ),
        ),
    ]
    for canary_id, outcome in failure_cases:
        if (
            outcome["complete"] is not False
            or outcome["result"] != "fail"
            or outcome["exit_code"] != 1
            or outcome["architecture_status"] != "invalid"
            or not outcome["diagnostics"]
        ):
            raise GateError(
                "GA12-REPORT-IMPLICATION-CANARY",
                f"{canary_id} did not produce the exact failure tuple",
            )
    canary_rows = [
        {
            "canary_id": "complete_evidence_closes",
            "expected": "pass/0/architecture_complete/diagnostics_empty",
            "observed": complete_outcome,
        },
        {
            "canary_id": "missing_stage_fails",
            "expected": missing_stage,
            "observed": stage_failure["failed_control_ids"],
        },
        {
            "canary_id": "missing_nested_fails",
            "expected": missing_nested,
            "observed": nested_failure["failed_control_ids"],
        },
        {
            "canary_id": "missing_selector_opens",
            "expected": selector_ids[0],
            "observed": selector_failure["open_finding_ids"],
        },
        *[
            {
                "canary_id": canary_id,
                "expected": "fail/1/invalid/diagnostics_nonempty",
                "observed": {
                    "result": outcome["result"],
                    "exit_code": outcome["exit_code"],
                    "architecture_status": outcome["architecture_status"],
                    "diagnostic_count": len(outcome["diagnostics"]),
                },
            }
            for canary_id, outcome in failure_cases
        ],
    ]
    return {
        "canary_count": len(canary_rows),
        "canary_set_sha256": evidence_sha256(canary_rows),
        "canaries": canary_rows,
    }


def verify_index_readback(
    snapshot: RepositorySnapshot,
    plan: Mapping[str, Any],
    rendered_index: bytes,
) -> dict[str, Any]:
    index_path = plan["index_path"]
    sidecar_path = plan["index_sidecar_path"]
    actual_index = snapshot.read(index_path)
    if actual_index != rendered_index:
        raise GateError(
            "GA12-INDEX-READBACK",
            "repository index bytes differ from the shared projection renderer",
        )
    index_digest = hashlib.sha256(rendered_index).hexdigest()
    expected_sidecar = f"sha256:{index_digest}  {index_path}\n".encode("ascii")
    actual_sidecar = snapshot.read(sidecar_path)
    if actual_sidecar != expected_sidecar:
        raise GateError(
            "GA12-INDEX-SIDECAR",
            "index sidecar bytes differ from the canonical index binding",
        )
    return {
        "path": index_path,
        "sha256": f"sha256:{index_digest}",
        "byte_size": len(rendered_index),
        "sidecar_path": sidecar_path,
        "sidecar_sha256": f"sha256:{hashlib.sha256(actual_sidecar).hexdigest()}",
        "sidecar_byte_size": len(actual_sidecar),
    }


def expected_catalog_contract(
    snapshot: RepositorySnapshot,
    science: Mapping[str, Any],
    security: Mapping[str, Any],
    governance: Mapping[str, Any],
) -> dict[str, tuple[str, str, str | None]]:
    expected: dict[str, tuple[str, str, str | None]] = {}
    for path in sorted(
        path
        for path in snapshot.files
        if path.startswith(SCIENCE_GOOD_PREFIX) and path.endswith(".json")
    ):
        fixture_name = PurePosixPath(path).stem
        expected[path] = (
            f"reiyah.fixture.good.v12.{fixture_name}",
            "known_good",
            None,
        )
    for diagnostic in science["diagnostics"]:
        fixture = strict_json(snapshot.read(diagnostic["path"]), diagnostic["path"])
        expected[diagnostic["path"]] = (
            fixture["fixture_id"],
            "known_bad",
            diagnostic["rule_id"],
        )
    for path, identity in sorted(governance["validated_positive_catalog"].items()):
        if path in expected:
            raise GateError(
                "GA12-FIXTURE-CATALOG-PATH-UNIQUE",
                f"validated governance positive collides with another fixture: {path}",
            )
        expected[path] = identity
    for prefix in (SECURITY_FIXTURE_PREFIX, GOVERNANCE_FIXTURE_PREFIX):
        for path in sorted(
            path
            for path in snapshot.files
            if path.startswith(prefix) and path.endswith(".json")
        ):
            fixture = strict_json(snapshot.read(path), path)
            expected[path] = (
                fixture["fixture_id"],
                "known_bad",
                fixture["expected_diagnostic"],
            )
    if sum(security["diagnostics"].values()) != security["fixture_count"]:
        raise GateError(
            "GA12-SECURITY-FIXTURE-COVERAGE",
            "security diagnostic counts do not equal replayed fixture count",
        )
    return expected


def exact_plan_rule_coverage(
    plan: Mapping[str, Any],
    catalog_by_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    fixture_ids_by_rule: dict[str, list[str]] = {}
    for fixture_id, row in catalog_by_id.items():
        if row["classification"] != "known_bad":
            continue
        rule_id = row.get("expected_primary_rule_id")
        if not isinstance(rule_id, str):
            raise GateError(
                "GA12-PLAN-RULE-COVERAGE",
                f"known-bad catalog row lacks a primary rule: {fixture_id}",
            )
        fixture_ids_by_rule.setdefault(rule_id, []).append(fixture_id)
    for fixture_ids in fixture_ids_by_rule.values():
        fixture_ids.sort()
    planned_rows = plan["rules"]
    planned_ids = [row["rule_id"] for row in planned_rows]
    expected_ids = sorted(fixture_ids_by_rule)
    if planned_ids != expected_ids:
        raise GateError(
            "GA12-PLAN-RULE-COVERAGE",
            "plan rules must equal the exact fixture-backed production universe: "
            f"missing={sorted(set(expected_ids) - set(planned_ids))}, "
            f"unexpected={sorted(set(planned_ids) - set(expected_ids))}",
        )
    for row in planned_rows:
        rule_id = row["rule_id"]
        if (
            row.get("known_bad_fixture_ids") != fixture_ids_by_rule[rule_id]
            or row.get("bad_fixture_required") is not True
        ):
            raise GateError(
                "GA12-PLAN-RULE-FIXTURE-BINDING",
                f"plan rule fixture set differs for {rule_id}",
            )
    return {
        "planned_rule_count": len(planned_rows),
        "fixture_backed_rule_count": len(fixture_ids_by_rule),
        "known_bad_fixture_count": sum(
            len(fixture_ids) for fixture_ids in fixture_ids_by_rule.values()
        ),
        "rule_fixture_matrix_sha256": evidence_sha256(
            [
                {
                    "rule_id": rule_id,
                    "known_bad_fixture_ids": fixture_ids_by_rule[rule_id],
                }
                for rule_id in expected_ids
            ]
        ),
    }


def _stage_observation(
    token_id: str,
    subject_count: int,
    payload: Any,
) -> tuple[str, int, Any]:
    observation_ids = STAGE_OBSERVATION_DISPATCH[token_id]
    if len(observation_ids) != 1:
        raise GateError(
            "GA12-STAGE-EVIDENCE-OBSERVATION-DISPATCH",
            f"single-observation producer received a multi-observation contract: {token_id}",
        )
    return observation_ids[0], subject_count, payload


RELEASE_PRE_REPORT_INPUT_KEYS = (
    "membership",
    "toolchain",
    "candidate_contract",
    "plan_evidence",
    "predecessor",
    "normative_architecture",
    "protocol_evidence",
    "profile",
    "plan",
    "manifest_lineage",
    "source_standards",
    "threat_boundary",
    "schema_corpus",
    "format_canaries",
    "format_coverage",
    "science",
    "governance",
    "security",
    "catalog",
    "rule_coverage",
    "narrative",
    "index_binding",
    "implication_canaries",
)


def collect_release_pre_report_token_rows(
    candidate: CandidateProjection,
    inputs: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if tuple(inputs) != RELEASE_PRE_REPORT_INPUT_KEYS:
        raise GateError(
            "GA12-STAGE-EVIDENCE-INPUT-CONTRACT",
            "release pre-report producer inputs differ from the closed order",
        )
    stage_ids = list(STAGE_PRODUCER_DISPATCH)[:-1]
    collector = StageEvidenceCollector(
        f"sha256:{candidate.sha256}",
        stage_ids,
    )
    report_driving_stage_specs = report_driving_stage_payload_specs(
        membership=inputs["membership"],
        toolchain=inputs["toolchain"],
        predecessor=inputs["predecessor"],
        science=inputs["science"],
        security=inputs["security"],
        governance=inputs["governance"],
        catalog=inputs["catalog"],
    )
    stage_payloads: list[tuple[str, int, Any]] = [
        (
            stage_ids[0],
            candidate.artifact_count,
            {
                "candidate_projection": candidate.summary(),
                "candidate_serialization_sha256": (
                    "sha256:" + hashlib.sha256(candidate.serialized).hexdigest()
                ),
                "required_artifact_contract": inputs["candidate_contract"],
            },
        ),
        (
            stage_ids[1],
            report_driving_stage_specs[stage_ids[1]][0],
            report_driving_stage_specs[stage_ids[1]][1],
        ),
        (
            stage_ids[2],
            inputs["candidate_contract"]["required_artifact_count"],
            {
                "plan": inputs["plan_evidence"],
                "candidate_contract": inputs["candidate_contract"],
            },
        ),
        (
            stage_ids[3],
            report_driving_stage_specs[stage_ids[3]][0],
            report_driving_stage_specs[stage_ids[3]][1],
        ),
        (
            stage_ids[4],
            inputs["normative_architecture"]["document_count"]
            + inputs["protocol_evidence"]["exact_artifact_binding_count"],
            {
                "protocol": inputs["protocol_evidence"],
                "profile_id": inputs["profile"]["profile_id"],
                "plan_id": inputs["plan"]["plan_id"],
                "normative_markdown_surface": inputs["normative_architecture"],
            },
        ),
        (
            stage_ids[5],
            inputs["manifest_lineage"]["entry_count"],
            inputs["manifest_lineage"],
        ),
        (
            stage_ids[6],
            inputs["source_standards"]["source_record_count"]
            + inputs["source_standards"]["mapping_count"],
            inputs["source_standards"],
        ),
        (
            stage_ids[7],
            inputs["threat_boundary"]["threat_count"],
            inputs["threat_boundary"],
        ),
        (
            stage_ids[8],
            inputs["schema_corpus"]["schema_count"]
            + inputs["format_canaries"]["valid_canaries"]
            + inputs["format_canaries"]["invalid_canaries"],
            {
                "schema_corpus": inputs["schema_corpus"],
                "format_canaries": inputs["format_canaries"],
                "format_coverage": inputs["format_coverage"],
            },
        ),
        (
            stage_ids[9],
            report_driving_stage_specs[stage_ids[9]][0],
            report_driving_stage_specs[stage_ids[9]][1],
        ),
        (
            stage_ids[10],
            inputs["profile"]["fixture_binding_count"]
            + inputs["profile"]["reference_path_binding_count"],
            inputs["profile"],
        ),
        (
            stage_ids[11],
            report_driving_stage_specs[stage_ids[11]][0],
            report_driving_stage_specs[stage_ids[11]][1],
        ),
        (
            stage_ids[12],
            report_driving_stage_specs[stage_ids[12]][0],
            report_driving_stage_specs[stage_ids[12]][1],
        ),
        (
            stage_ids[13],
            report_driving_stage_specs[stage_ids[13]][0],
            report_driving_stage_specs[stage_ids[13]][1],
        ),
        (
            stage_ids[14],
            report_driving_stage_specs[stage_ids[14]][0],
            report_driving_stage_specs[stage_ids[14]][1],
        ),
        (
            stage_ids[15],
            inputs["rule_coverage"]["planned_rule_count"],
            inputs["rule_coverage"],
        ),
        (
            stage_ids[16],
            inputs["narrative"]["candidate_marker_count"],
            inputs["narrative"],
        ),
        (stage_ids[17], 2, inputs["index_binding"]),
        (
            stage_ids[18],
            inputs["implication_canaries"]["canary_count"],
            inputs["implication_canaries"],
        ),
    ]
    for token_id, subject_count, payload in stage_payloads:
        collector.record(
            token_id,
            STAGE_PRODUCER_DISPATCH[token_id],
            [_stage_observation(token_id, subject_count, payload)],
        )
    return collector.finish()


def evaluate_snapshot(
    snapshot: RepositorySnapshot,
    *,
    require_index_readback: bool,
    collect_release_stage_evidence: bool,
    activated_dependencies: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    membership = verify_snapshot_membership(snapshot)
    first_toolchain = validate_toolchain_lock(snapshot)
    dependencies = (
        activated_dependencies
        if activated_dependencies is not None
        else activate_locked_schema_dependencies()
    )
    protocol_evidence = validate_protocol_artifact_bindings(snapshot, dependencies)
    plan, plan_evidence = load_validation_plan(snapshot, dependencies)
    candidate = candidate_projection(snapshot, plan)
    candidate_contract = validate_candidate_contract(snapshot, plan, candidate)
    predecessor, predecessor_entries = validate_predecessor_inheritance(
        snapshot, plan, candidate
    )
    schema_corpus = validate_schema_corpus(
        snapshot,
        dependencies,
        set(predecessor["changed_paths"]) | set(predecessor["added_paths"]),
    )
    format_canaries = check_format_canaries()
    format_coverage = schema_format_coverage(snapshot)
    governance = validate_governance_fixtures(snapshot, dependencies)
    science = validate_scientific_contracts(snapshot, dependencies)
    profile = validate_scientific_profile(snapshot, dependencies, science)
    normative_architecture = validate_normative_markdown_surface(snapshot)
    narrative = validate_narrative_state(snapshot)
    security = validate_security_fixtures(
        snapshot,
        dependencies,
        science,
        governance,
    )
    expected_catalog = expected_catalog_contract(
        snapshot, science, security, governance
    )
    catalog = validate_fixture_catalog(snapshot, dependencies, expected_catalog)
    catalog_by_id = current_catalog_rows_by_id(snapshot)
    rule_coverage = exact_plan_rule_coverage(plan, catalog_by_id)
    manifest_lineage = validate_manifest_lineage(snapshot, dependencies)
    source_standards = validate_source_standards_custody(snapshot, dependencies)
    threat_boundary = validate_threat_no_runtime_boundary(snapshot, plan, candidate)
    post_toolchain = validate_toolchain_lock(snapshot)
    if post_toolchain != first_toolchain:
        raise GateError(
            "GA12-TOOLCHAIN-POSTLOAD",
            "post-import toolchain observation differs from initial lock evidence",
        )
    index, index_bytes = render_candidate_index(
        snapshot,
        dependencies,
        plan,
        candidate,
        predecessor,
        predecessor_entries,
    )
    index_binding = (
        verify_index_readback(snapshot, plan, index_bytes)
        if require_index_readback
        else None
    )
    publication_event_state = (
        validate_actual_publication_event_state(
            snapshot,
            dependencies,
            plan,
            candidate,
            index_bytes,
        )
        if snapshot.mode == "release"
        else {
            "state": "not_evaluated_development_snapshot",
            "transport_verification_state": "not_evaluated",
            "publisher_receipt_is_independent_verification": False,
        }
    )
    nested_rows = build_nested_contract_evidence(
        snapshot,
        candidate,
        plan,
        science,
        catalog_by_id,
    )
    selector_rows = build_selector_evidence(
        snapshot,
        candidate,
        plan,
        catalog_by_id,
        evidence_selector_observation_dispatch(),
    )
    implication_canaries = run_report_implication_canaries(plan)
    transport = evaluate_transport_boundary(
        snapshot,
        PREDECESSOR_RECEIPT_PATH,
        (),
        plan["transport_policy"]["offline_state"],
    )
    token_rows: list[dict[str, Any]] = []
    pre_report_stage_evidence_bytes: bytes | None = None
    evaluation_comparable: dict[str, Any] | None = None
    evaluation_sha256_value: str | None = None
    if collect_release_stage_evidence:
        if snapshot.mode != "release" or index_binding is None:
            raise GateError(
                "GA12-STAGE-EVIDENCE-RELEASE-MODE",
                "release stage evidence requires a release snapshot and exact index readback",
            )
        stage_ids = list(STAGE_PRODUCER_DISPATCH)[:-1]
        collector = StageEvidenceCollector(
            f"sha256:{candidate.sha256}",
            stage_ids,
        )
        report_driving_stage_specs = report_driving_stage_payload_specs(
            membership=membership,
            toolchain=post_toolchain,
            predecessor=predecessor,
            science=science,
            security=security,
            governance=governance,
            catalog=catalog,
        )
        stage_payloads: list[tuple[str, int, Any]] = [
            (
                stage_ids[0],
                candidate.artifact_count,
                {
                    "candidate_projection": candidate.summary(),
                    "candidate_serialization_sha256": f"sha256:{hashlib.sha256(candidate.serialized).hexdigest()}",
                    "required_artifact_contract": candidate_contract,
                },
            ),
            (
                stage_ids[1],
                report_driving_stage_specs[stage_ids[1]][0],
                report_driving_stage_specs[stage_ids[1]][1],
            ),
            (
                stage_ids[2],
                candidate_contract["required_artifact_count"],
                {
                    "plan": plan_evidence,
                    "candidate_contract": candidate_contract,
                },
            ),
            (
                stage_ids[3],
                report_driving_stage_specs[stage_ids[3]][0],
                report_driving_stage_specs[stage_ids[3]][1],
            ),
            (
                stage_ids[4],
                normative_architecture["document_count"]
                + protocol_evidence["exact_artifact_binding_count"],
                {
                    "protocol": protocol_evidence,
                    "profile_id": profile["profile_id"],
                    "plan_id": plan["plan_id"],
                    "normative_markdown_surface": normative_architecture,
                },
            ),
            (
                stage_ids[5],
                manifest_lineage["entry_count"],
                manifest_lineage,
            ),
            (
                stage_ids[6],
                source_standards["source_record_count"]
                + source_standards["mapping_count"],
                source_standards,
            ),
            (
                stage_ids[7],
                threat_boundary["threat_count"],
                threat_boundary,
            ),
            (
                stage_ids[8],
                schema_corpus["schema_count"]
                + format_canaries["valid_canaries"]
                + format_canaries["invalid_canaries"],
                {
                    "schema_corpus": schema_corpus,
                    "format_canaries": format_canaries,
                    "format_coverage": format_coverage,
                },
            ),
            (
                stage_ids[9],
                report_driving_stage_specs[stage_ids[9]][0],
                report_driving_stage_specs[stage_ids[9]][1],
            ),
            (
                stage_ids[10],
                profile["fixture_binding_count"]
                + profile["reference_path_binding_count"],
                profile,
            ),
            (
                stage_ids[11],
                report_driving_stage_specs[stage_ids[11]][0],
                report_driving_stage_specs[stage_ids[11]][1],
            ),
            (
                stage_ids[12],
                report_driving_stage_specs[stage_ids[12]][0],
                report_driving_stage_specs[stage_ids[12]][1],
            ),
            (
                stage_ids[13],
                report_driving_stage_specs[stage_ids[13]][0],
                report_driving_stage_specs[stage_ids[13]][1],
            ),
            (
                stage_ids[14],
                report_driving_stage_specs[stage_ids[14]][0],
                report_driving_stage_specs[stage_ids[14]][1],
            ),
            (
                stage_ids[15],
                rule_coverage["planned_rule_count"],
                rule_coverage,
            ),
            (
                stage_ids[16],
                narrative["candidate_marker_count"],
                narrative,
            ),
            (
                stage_ids[17],
                2,
                index_binding,
            ),
            (
                stage_ids[18],
                implication_canaries["canary_count"],
                implication_canaries,
            ),
        ]
        for token_id, subject_count, payload in stage_payloads:
            collector.record(
                token_id,
                STAGE_PRODUCER_DISPATCH[token_id],
                [_stage_observation(token_id, subject_count, payload)],
            )
        token_rows = collector.finish()
        projected_token_rows = collect_release_pre_report_token_rows(
            candidate,
            {
                "membership": membership,
                "toolchain": post_toolchain,
                "candidate_contract": candidate_contract,
                "plan_evidence": plan_evidence,
                "predecessor": predecessor,
                "normative_architecture": normative_architecture,
                "protocol_evidence": protocol_evidence,
                "profile": profile,
                "plan": plan,
                "manifest_lineage": manifest_lineage,
                "source_standards": source_standards,
                "threat_boundary": threat_boundary,
                "schema_corpus": schema_corpus,
                "format_canaries": format_canaries,
                "format_coverage": format_coverage,
                "science": science,
                "governance": governance,
                "security": security,
                "catalog": catalog,
                "rule_coverage": rule_coverage,
                "narrative": narrative,
                "index_binding": index_binding,
                "implication_canaries": implication_canaries,
            },
        )
        if token_rows != projected_token_rows:
            raise GateError(
                "GA12-STAGE-EVIDENCE-PROJECTION",
                "central stage collector and factored S01-S19 projection differ",
            )
        token_rows = projected_token_rows
        pre_report_bundle = {
            "token_rows": token_rows,
            "nested_contract_rows": nested_rows,
            "selector_rows": selector_rows,
        }
        pre_report_stage_evidence_bytes = canonical_json_bytes(pre_report_bundle)
        evaluation_comparable = {
            "candidate_projection_sha256": f"sha256:{candidate.sha256}",
            "candidate_projection_artifact_count": candidate.artifact_count,
            "candidate_projection_byte_count": candidate.byte_count,
            "canonical_index_sha256": f"sha256:{hashlib.sha256(index_bytes).hexdigest()}",
            "canonical_index_byte_size": len(index_bytes),
            "pre_report_stage_evidence_sha256": f"sha256:{hashlib.sha256(pre_report_stage_evidence_bytes).hexdigest()}",
            "pre_report_stage_evidence_byte_size": len(pre_report_stage_evidence_bytes),
        }
        evaluation_sha256_value = evidence_sha256(evaluation_comparable)
    finalize_snapshot(snapshot)
    return {
        "snapshot": snapshot,
        "dependencies": dependencies,
        "plan": plan,
        "candidate": candidate,
        "predecessor": predecessor,
        "science": science,
        "security": security,
        "governance": governance,
        "toolchain": post_toolchain,
        "transport": transport,
        "publication_event_state": publication_event_state,
        "catalog": catalog,
        "catalog_by_id": catalog_by_id,
        "index": index,
        "index_bytes": index_bytes,
        "index_binding": index_binding,
        "token_rows": token_rows,
        "nested_contract_rows": nested_rows,
        "selector_rows": selector_rows,
        "pre_report_stage_evidence_bytes": pre_report_stage_evidence_bytes,
        "evaluation_comparable": evaluation_comparable,
        "evaluation_sha256": evaluation_sha256_value,
        "development_checks": {
            "GA12-STAGE-TOOLCHAIN-INTEGRITY": {
                "membership": membership,
                "toolchain": post_toolchain,
            },
            "GA12-STAGE-PLAN-CONTRACT": plan_evidence,
            "GA12-STAGE-PREDECESSOR-INHERITANCE": predecessor,
            "GA12-STAGE-MANIFEST-LINEAGE": manifest_lineage,
            "GA12-STAGE-SOURCE-STANDARDS-CUSTODY": source_standards,
            "GA12-STAGE-THREAT-NO-RUNTIME": threat_boundary,
            "GA12-STAGE-SCIENTIFIC-CONTRACT-REPLAY": science,
            "GA12-STAGE-VALIDATOR-SECURITY": security,
            "GA12-STAGE-FIXTURE-CATALOG": catalog,
            "GA12-STAGE-RULE-CONTROL-THREAT-COVERAGE": rule_coverage,
            "GA12-STAGE-REPORT-IMPLICATIONS": implication_canaries,
        },
    }


REPORT_DRIVING_WORKER_SECTION_KEYS = (
    "predecessor",
    "science",
    "security",
    "governance",
    "toolchain",
    "transport",
    "catalog",
    "catalog_by_id",
)


def report_driving_stage_payload_specs(
    *,
    membership: Mapping[str, Any],
    toolchain: Mapping[str, Any],
    predecessor: Mapping[str, Any],
    science: Mapping[str, Any],
    security: Mapping[str, Any],
    governance: Mapping[str, Any],
    catalog: Mapping[str, Any],
) -> dict[str, tuple[int, Any]]:
    """Project report-driving results into their exact S01-S19 observations."""

    return {
        "reiyah.stage-evidence.toolchain-pre-post-integrity@1.2.0": (
            toolchain["dependency_count"] + len(membership),
            {
                "snapshot_membership": membership,
                "preload_toolchain": toolchain,
                "postload_toolchain": toolchain,
                "pre_post_equal": True,
            },
        ),
        "reiyah.stage-evidence.predecessor-inheritance@1.2.0": (
            predecessor["predecessor_artifact_count"],
            predecessor,
        ),
        "reiyah.stage-evidence.scientific-contract-replay@1.2.0": (
            science["good_fixture_count"] + science["mutation_fixture_count"],
            science,
        ),
        "reiyah.stage-evidence.publication-governance-replay@1.2.0": (
            governance["publication"]["positive_count"]
            + governance["publication"]["known_bad_count"],
            {
                "publication": governance["publication"],
                "positive_bindings": [
                    row
                    for row in governance["observed_evidence"]["positive_bindings"]
                    if row["path"] != TRANSPORT_OBSERVATION_BASELINE_PATH
                ],
            },
        ),
        "reiyah.stage-evidence.transport-governance-replay@1.2.0": (
            governance["transport"]["positive_count"]
            + governance["transport"]["known_bad_count"],
            {
                "transport": governance["transport"],
                "positive_bindings": [
                    row
                    for row in governance["observed_evidence"]["positive_bindings"]
                    if row["path"] == TRANSPORT_OBSERVATION_BASELINE_PATH
                ],
            },
        ),
        "reiyah.stage-evidence.validator-security-replay@1.2.0": (
            security["fixture_count"],
            security,
        ),
        "reiyah.stage-evidence.fixture-catalog-reconciliation@1.2.0": (
            catalog["catalog_fixture_count"],
            catalog,
        ),
    }


def expected_stage_token_row(
    token_id: str,
    candidate_projection_sha256: str,
    subject_count: int,
    payload: Any,
) -> dict[str, Any]:
    observation_ids = STAGE_OBSERVATION_DISPATCH.get(token_id)
    producer_check_id = STAGE_PRODUCER_DISPATCH.get(token_id)
    if (
        observation_ids is None
        or len(observation_ids) != 1
        or producer_check_id is None
    ):
        raise GateError(
            "GA12-DUAL-EVALUATION-WORKER-PROTOCOL",
            f"report-driving stage projection is not a closed single observation: {token_id}",
        )
    row = {
        "token_id": token_id,
        "producer_check_id": producer_check_id,
        "candidate_projection_sha256": candidate_projection_sha256,
        "observations": [
            {
                "observation_id": observation_ids[0],
                "subject_count": subject_count,
                "evidence_sha256": evidence_sha256(payload),
            }
        ],
    }
    row["evidence_sha256"] = evidence_sha256(row)
    return row


def validate_report_driving_stage_bindings(
    token_rows: Sequence[Mapping[str, Any]],
    candidate_projection_sha256: str,
    specs: Mapping[str, tuple[int, Any]],
) -> None:
    for token_id, (subject_count, payload) in specs.items():
        matches = [row for row in token_rows if row.get("token_id") == token_id]
        expected = expected_stage_token_row(
            token_id,
            candidate_projection_sha256,
            subject_count,
            payload,
        )
        if len(matches) != 1 or matches[0] != expected:
            raise GateError(
                "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
                f"report-driving section does not bind its exact stage observation: {token_id}",
            )


def validate_release_worker_report_inputs(
    payload: Mapping[str, Any],
    expected_report_inputs: Mapping[str, Any],
    *,
    membership: Mapping[str, Any],
    candidate_projection_sha256: str,
) -> None:
    if tuple(expected_report_inputs) != REPORT_DRIVING_WORKER_SECTION_KEYS:
        raise GateError(
            "GA12-DUAL-EVALUATION-WORKER-PROTOCOL",
            "outer report-driving input contract differs from the closed section order",
        )
    for section in REPORT_DRIVING_WORKER_SECTION_KEYS:
        require_release_worker_binding(
            payload[section],
            expected_report_inputs[section],
            "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
            f"worker report-driving section differs from outer replay: {section}",
        )
    specs = report_driving_stage_payload_specs(
        membership=membership,
        toolchain=expected_report_inputs["toolchain"],
        predecessor=expected_report_inputs["predecessor"],
        science=expected_report_inputs["science"],
        security=expected_report_inputs["security"],
        governance=expected_report_inputs["governance"],
        catalog=expected_report_inputs["catalog"],
    )
    validate_report_driving_stage_bindings(
        payload["token_rows"],
        candidate_projection_sha256,
        specs,
    )


RELEASE_WORKER_OUTER_EVIDENCE_KEYS = (
    "token_rows",
    "nested_contract_rows",
    "selector_rows",
)


def validate_release_worker_outer_evidence(
    payload: Mapping[str, Any],
    expected: Mapping[str, Any],
) -> None:
    if tuple(expected) != RELEASE_WORKER_OUTER_EVIDENCE_KEYS:
        raise GateError(
            "GA12-DUAL-EVALUATION-WORKER-PROTOCOL",
            "outer evidence expectation differs from the closed collection order",
        )
    differing = [
        key
        for key in RELEASE_WORKER_OUTER_EVIDENCE_KEYS
        if payload[key] != expected[key]
    ]
    if differing:
        raise GateError(
            "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
            f"worker evidence collections differ from outer replay: {differing}",
        )


RELEASE_EVALUATION_WORKER_PROTOCOL_ID = (
    "reiyah.protocol.release-evaluation-worker@1.2.0"
)
RELEASE_EVALUATION_WORKER_PAYLOAD_KEYS = frozenset(
    {
        "worker_protocol_id",
        "fresh_process_snapshot_loaded",
        "snapshot_identity",
        "plan",
        "candidate_summary",
        "candidate_serialized_sha256",
        "predecessor",
        "science",
        "security",
        "governance",
        "toolchain",
        "transport",
        "publication_event_state",
        "catalog",
        "catalog_by_id",
        "index",
        "index_binding",
        "token_rows",
        "nested_contract_rows",
        "selector_rows",
        "evaluation_comparable",
        "evaluation_sha256",
    }
)


def require_release_worker_payload_envelope(
    payload: Mapping[str, Any],
) -> None:
    if set(payload) != RELEASE_EVALUATION_WORKER_PAYLOAD_KEYS:
        raise GateError(
            "GA12-DUAL-EVALUATION-WORKER-PROTOCOL",
            "release worker payload keys differ from the closed protocol",
        )
    if (
        payload.get("worker_protocol_id") != RELEASE_EVALUATION_WORKER_PROTOCOL_ID
        or payload.get("fresh_process_snapshot_loaded") is not True
    ):
        raise GateError(
            "GA12-DUAL-EVALUATION-WORKER-PROTOCOL",
            "release worker protocol or snapshot-load assertion differs",
        )


def require_release_worker_binding(
    observed: Any,
    expected: Any,
    diagnostic: str,
    context: str,
) -> None:
    if observed != expected:
        raise GateError(diagnostic, context)


RELEASE_WORKER_BINDING_EXPECTATION_KEYS = frozenset(
    {
        "snapshot_identity",
        "plan",
        "candidate_summary",
        "candidate_serialized_sha256",
        "index_binding",
        "evaluation_comparable_prefix",
    }
)


def validate_release_worker_payload_bindings(
    payload: Mapping[str, Any],
    expected: Mapping[str, Any],
) -> tuple[bytes, dict[str, Any]]:
    require_release_worker_payload_envelope(payload)
    if set(expected) != RELEASE_WORKER_BINDING_EXPECTATION_KEYS:
        raise GateError(
            "GA12-DUAL-EVALUATION-WORKER-PROTOCOL",
            "release worker binding expectation keys differ",
        )
    require_release_worker_binding(
        payload["snapshot_identity"],
        expected["snapshot_identity"],
        "GA12-DUAL-EVALUATION-CANDIDATE-MISMATCH",
        "worker snapshot identity differs from the outer immutable snapshot",
    )
    require_release_worker_binding(
        payload["plan"],
        expected["plan"],
        "GA12-DUAL-EVALUATION-WORKER-PROTOCOL",
        "worker plan differs from outer snapshot bytes",
    )
    require_release_worker_binding(
        payload["candidate_summary"],
        expected["candidate_summary"],
        "GA12-DUAL-EVALUATION-CANDIDATE-MISMATCH",
        "worker candidate summary differs from independently loaded outer bytes",
    )
    require_release_worker_binding(
        payload["candidate_serialized_sha256"],
        expected["candidate_serialized_sha256"],
        "GA12-DUAL-EVALUATION-CANDIDATE-MISMATCH",
        "worker candidate serialization digest differs from independently loaded outer bytes",
    )
    require_release_worker_binding(
        payload["index_binding"],
        expected["index_binding"],
        "GA12-DUAL-EVALUATION-INDEX-MISMATCH",
        "worker index binding differs from outer exact readback",
    )
    token_rows = payload["token_rows"]
    nested_rows = payload["nested_contract_rows"]
    selector_rows = payload["selector_rows"]
    if not all(
        isinstance(value, list) for value in (token_rows, nested_rows, selector_rows)
    ):
        raise GateError(
            "GA12-DUAL-EVALUATION-WORKER-PROTOCOL",
            "worker evidence row collections must be arrays",
        )
    pre_report_stage_evidence_bytes = canonical_json_bytes(
        {
            "token_rows": token_rows,
            "nested_contract_rows": nested_rows,
            "selector_rows": selector_rows,
        }
    )
    comparable_prefix = expected["evaluation_comparable_prefix"]
    if not isinstance(comparable_prefix, Mapping) or set(comparable_prefix) != {
        "candidate_projection_sha256",
        "candidate_projection_artifact_count",
        "candidate_projection_byte_count",
        "canonical_index_sha256",
        "canonical_index_byte_size",
    }:
        raise GateError(
            "GA12-DUAL-EVALUATION-WORKER-PROTOCOL",
            "release worker comparable-prefix expectation differs",
        )
    expected_comparable = {
        **comparable_prefix,
        "pre_report_stage_evidence_sha256": (
            "sha256:" + hashlib.sha256(pre_report_stage_evidence_bytes).hexdigest()
        ),
        "pre_report_stage_evidence_byte_size": len(pre_report_stage_evidence_bytes),
    }
    require_release_worker_binding(
        payload["evaluation_comparable"],
        expected_comparable,
        "GA12-DUAL-EVALUATION-DIGEST-MISMATCH",
        "worker comparable record does not bind reconstructed bytes",
    )
    require_release_worker_binding(
        payload["evaluation_sha256"],
        evidence_sha256(expected_comparable),
        "GA12-DUAL-EVALUATION-DIGEST-MISMATCH",
        "worker comparable digest does not bind reconstructed bytes",
    )
    return pre_report_stage_evidence_bytes, expected_comparable


def require_distinct_release_worker_records(
    first: Mapping[str, Any],
    second: Mapping[str, Any],
    worker_process_ids: Sequence[int],
) -> None:
    if (
        first is second
        or len(worker_process_ids) != 2
        or len(set(worker_process_ids)) != 2
    ):
        raise GateError(
            "GA12-DUAL-EVALUATION-SNAPSHOT-REUSE",
            "release evaluations reused a worker process or evaluation record",
        )


RELEASE_WORKER_FAULT_CANARY_EXPECTED: Mapping[str, str] = MappingProxyType(
    {
        "missing_payload_key": "GA12-DUAL-EVALUATION-WORKER-PROTOCOL",
        "extra_payload_key": "GA12-DUAL-EVALUATION-WORKER-PROTOCOL",
        "false_freshness_assertion": "GA12-DUAL-EVALUATION-WORKER-PROTOCOL",
        "snapshot_identity_substitution": "GA12-DUAL-EVALUATION-CANDIDATE-MISMATCH",
        "plan_substitution": "GA12-DUAL-EVALUATION-WORKER-PROTOCOL",
        "candidate_summary_substitution": "GA12-DUAL-EVALUATION-CANDIDATE-MISMATCH",
        "candidate_serialization_digest_substitution": "GA12-DUAL-EVALUATION-CANDIDATE-MISMATCH",
        "index_binding_substitution": "GA12-DUAL-EVALUATION-INDEX-MISMATCH",
        "pre_report_row_digest_substitution": "GA12-DUAL-EVALUATION-DIGEST-MISMATCH",
        "comparable_record_substitution": "GA12-DUAL-EVALUATION-DIGEST-MISMATCH",
        "comparable_digest_substitution": "GA12-DUAL-EVALUATION-DIGEST-MISMATCH",
        "outer_predecessor_section_substitution": "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
        "outer_science_section_substitution": "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
        "outer_security_section_substitution": "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
        "outer_governance_section_substitution": "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
        "outer_toolchain_section_substitution": "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
        "outer_transport_section_substitution": "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
        "outer_catalog_section_substitution": "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
        "outer_catalog_by_id_section_substitution": "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
        "report_driving_stage_observation_substitution": "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
        "outer_full_token_collection_coherent_substitution": "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
        "outer_nested_collection_coherent_substitution": "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
        "outer_selector_collection_coherent_substitution": "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
        "cross_evaluation_snapshot_substitution": "GA12-DUAL-EVALUATION-CANDIDATE-MISMATCH",
        "cross_evaluation_candidate_bytes_substitution": "GA12-DUAL-EVALUATION-CANDIDATE-MISMATCH",
        "cross_evaluation_index_bytes_substitution": "GA12-DUAL-EVALUATION-INDEX-MISMATCH",
        "cross_evaluation_evidence_bytes_substitution": "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
        "cross_evaluation_comparable_substitution": "GA12-DUAL-EVALUATION-DIGEST-MISMATCH",
        "cross_evaluation_digest_substitution": "GA12-DUAL-EVALUATION-DIGEST-MISMATCH",
        "cross_evaluation_predecessor_section_substitution": "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
        "cross_evaluation_science_section_substitution": "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
        "cross_evaluation_security_section_substitution": "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
        "cross_evaluation_governance_section_substitution": "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
        "cross_evaluation_toolchain_section_substitution": "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
        "cross_evaluation_transport_section_substitution": "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
        "cross_evaluation_catalog_section_substitution": "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
        "cross_evaluation_catalog_by_id_section_substitution": "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
        "duplicate_worker_pid": "GA12-DUAL-EVALUATION-SNAPSHOT-REUSE",
        "reused_evaluation_record": "GA12-DUAL-EVALUATION-SNAPSHOT-REUSE",
        "malformed_direct_worker_invocation": "GA12-DUAL-EVALUATION-WORKER-PROTOCOL",
    }
)


def release_worker_fault_canary_matrix() -> str:
    snapshot_identity = {
        "mode": "release",
        "projection_sha256": "sha256:" + "1" * 64,
        "file_count": 1,
        "byte_count": 1,
        "commit": "2" * 40,
        "tree": "3" * 40,
        "object_format": "sha1",
    }
    plan = {"plan_id": "reiyah.synthetic.worker-plan"}
    candidate_serialized = b"synthetic-candidate\n"
    candidate = CandidateProjection(
        files=MappingProxyType({}),
        exclusions=(),
        serialized=candidate_serialized,
        sha256=hashlib.sha256(candidate_serialized).hexdigest(),
        artifact_count=0,
        byte_count=0,
    )
    candidate_summary = candidate.summary()
    index_bytes = b'{"synthetic_index":true}\n'
    index_binding = {
        "index_sha256": "sha256:" + hashlib.sha256(index_bytes).hexdigest(),
        "index_byte_size": len(index_bytes),
    }
    outer_membership = {
        "artifact_count": 1,
        "projection_sha256": snapshot_identity["projection_sha256"],
    }
    report_inputs = {
        "predecessor": {"predecessor_artifact_count": 1},
        "science": {
            "good_fixture_count": 1,
            "mutation_fixture_count": 1,
        },
        "security": {"fixture_count": 1},
        "governance": {
            "publication": {"positive_count": 1, "known_bad_count": 1},
            "transport": {"positive_count": 1, "known_bad_count": 1},
            "observed_evidence": {
                "positive_bindings": [
                    {
                        "path": "fixtures/v1.2/governance-good/synthetic-publication.json",
                        "fixture_id": "reiyah.synthetic.publication",
                    },
                    {
                        "path": TRANSPORT_OBSERVATION_BASELINE_PATH,
                        "fixture_id": "reiyah.synthetic.transport",
                    },
                ]
            },
        },
        "toolchain": {"dependency_count": 1},
        "transport": {"status": "not_evaluated"},
        "catalog": {"catalog_fixture_count": 1},
        "catalog_by_id": {
            "reiyah.synthetic.fixture": {
                "path": "fixtures/v1.2/known-bad/synthetic.json"
            }
        },
    }
    synthetic_stage_specs = report_driving_stage_payload_specs(
        membership=outer_membership,
        toolchain=report_inputs["toolchain"],
        predecessor=report_inputs["predecessor"],
        science=report_inputs["science"],
        security=report_inputs["security"],
        governance=report_inputs["governance"],
        catalog=report_inputs["catalog"],
    )
    token_rows = []
    for token_id in list(STAGE_PRODUCER_DISPATCH)[:-1]:
        subject_count, stage_payload = synthetic_stage_specs.get(
            token_id,
            (1, {"synthetic_stage_token_id": token_id}),
        )
        token_rows.append(
            expected_stage_token_row(
                token_id,
                candidate_summary["sha256"],
                subject_count,
                stage_payload,
            )
        )
    nested_rows = [{"contract_id": "reiyah.synthetic.contract"}]
    selector_rows = [{"selector_id": "reiyah.synthetic.selector"}]
    pre_report_bytes = canonical_json_bytes(
        {
            "token_rows": token_rows,
            "nested_contract_rows": nested_rows,
            "selector_rows": selector_rows,
        }
    )
    comparable_prefix = {
        "candidate_projection_sha256": candidate_summary["sha256"],
        "candidate_projection_artifact_count": 0,
        "candidate_projection_byte_count": 0,
        "canonical_index_sha256": "sha256:" + hashlib.sha256(index_bytes).hexdigest(),
        "canonical_index_byte_size": len(index_bytes),
    }
    comparable = {
        **comparable_prefix,
        "pre_report_stage_evidence_sha256": (
            "sha256:" + hashlib.sha256(pre_report_bytes).hexdigest()
        ),
        "pre_report_stage_evidence_byte_size": len(pre_report_bytes),
    }
    expected_bindings = {
        "snapshot_identity": snapshot_identity,
        "plan": plan,
        "candidate_summary": candidate_summary,
        "candidate_serialized_sha256": (
            "sha256:" + hashlib.sha256(candidate_serialized).hexdigest()
        ),
        "index_binding": index_binding,
        "evaluation_comparable_prefix": comparable_prefix,
    }
    baseline_payload = {key: None for key in RELEASE_EVALUATION_WORKER_PAYLOAD_KEYS}
    baseline_payload.update(
        {
            "worker_protocol_id": RELEASE_EVALUATION_WORKER_PROTOCOL_ID,
            "fresh_process_snapshot_loaded": True,
            "snapshot_identity": snapshot_identity,
            "plan": plan,
            "candidate_summary": candidate_summary,
            "candidate_serialized_sha256": expected_bindings[
                "candidate_serialized_sha256"
            ],
            "index": {"synthetic_index": True},
            "index_binding": index_binding,
            "token_rows": token_rows,
            "nested_contract_rows": nested_rows,
            "selector_rows": selector_rows,
            "evaluation_comparable": comparable,
            "evaluation_sha256": evidence_sha256(comparable),
            **report_inputs,
        }
    )
    validate_release_worker_payload_bindings(baseline_payload, expected_bindings)
    validate_release_worker_report_inputs(
        baseline_payload,
        report_inputs,
        membership=outer_membership,
        candidate_projection_sha256=candidate_summary["sha256"],
    )
    outer_evidence = {
        "token_rows": token_rows,
        "nested_contract_rows": nested_rows,
        "selector_rows": selector_rows,
    }
    validate_release_worker_outer_evidence(baseline_payload, outer_evidence)

    def binding_diagnostic(
        mutate: Callable[[dict[str, Any]], None],
    ) -> str | None:
        mutated = copy.deepcopy(baseline_payload)
        mutate(mutated)
        return captured_gate_diagnostic(
            lambda: validate_release_worker_payload_bindings(mutated, expected_bindings)
        )

    def report_input_diagnostic(
        mutate: Callable[[dict[str, Any]], None],
    ) -> str | None:
        mutated = copy.deepcopy(baseline_payload)
        mutate(mutated)
        return captured_gate_diagnostic(
            lambda: validate_release_worker_report_inputs(
                mutated,
                report_inputs,
                membership=outer_membership,
                candidate_projection_sha256=candidate_summary["sha256"],
            )
        )

    def coherent_outer_evidence_diagnostic(
        mutate: Callable[[dict[str, Any]], None],
    ) -> str | None:
        mutated = copy.deepcopy(baseline_payload)
        mutate(mutated)
        mutated_pre_report_bytes = canonical_json_bytes(
            {
                "token_rows": mutated["token_rows"],
                "nested_contract_rows": mutated["nested_contract_rows"],
                "selector_rows": mutated["selector_rows"],
            }
        )
        mutated_comparable = {
            **comparable_prefix,
            "pre_report_stage_evidence_sha256": (
                "sha256:" + hashlib.sha256(mutated_pre_report_bytes).hexdigest()
            ),
            "pre_report_stage_evidence_byte_size": len(mutated_pre_report_bytes),
        }
        mutated["evaluation_comparable"] = mutated_comparable
        mutated["evaluation_sha256"] = evidence_sha256(mutated_comparable)

        def replay_production_guards() -> None:
            validate_release_worker_payload_bindings(mutated, expected_bindings)
            validate_release_worker_report_inputs(
                mutated,
                report_inputs,
                membership=outer_membership,
                candidate_projection_sha256=candidate_summary["sha256"],
            )
            validate_release_worker_outer_evidence(mutated, outer_evidence)

        return captured_gate_diagnostic(replay_production_guards)

    baseline_evaluation = {
        "snapshot_identity": snapshot_identity,
        "candidate": candidate,
        "index_bytes": index_bytes,
        "pre_report_stage_evidence_bytes": pre_report_bytes,
        "evaluation_comparable": comparable,
        "evaluation_sha256": evidence_sha256(comparable),
        **report_inputs,
    }

    def equality_diagnostic(
        mutate: Callable[[dict[str, Any]], None],
    ) -> str | None:
        mutated = {
            **baseline_evaluation,
            "snapshot_identity": copy.deepcopy(snapshot_identity),
            "evaluation_comparable": copy.deepcopy(comparable),
        }
        mutate(mutated)
        return captured_gate_diagnostic(
            lambda: require_release_evaluation_equality(baseline_evaluation, mutated)
        )

    def mutate_unbound_token_row(payload: dict[str, Any]) -> None:
        row = payload["token_rows"][0]
        row["observations"][0]["evidence_sha256"] = "sha256:" + "9" * 64
        row_without_digest = {
            key: value for key, value in row.items() if key != "evidence_sha256"
        }
        row["evidence_sha256"] = evidence_sha256(row_without_digest)

    def mutate_report_driving_stage_row(payload: dict[str, Any]) -> None:
        token_id = next(iter(synthetic_stage_specs))
        row = next(
            item for item in payload["token_rows"] if item["token_id"] == token_id
        )
        row["observations"][0]["subject_count"] += 1

    def mutate_nested_row(payload: dict[str, Any]) -> None:
        payload["nested_contract_rows"][0]["contract_id"] = (
            "reiyah.synthetic.substituted-contract"
        )

    def mutate_selector_row(payload: dict[str, Any]) -> None:
        payload["selector_rows"][0]["selector_id"] = (
            "reiyah.synthetic.substituted-selector"
        )

    observed: dict[str, str | None] = {
        "missing_payload_key": binding_diagnostic(
            lambda payload: payload.pop("index_binding")
        ),
        "extra_payload_key": binding_diagnostic(
            lambda payload: payload.__setitem__("unexpected", None)
        ),
        "false_freshness_assertion": binding_diagnostic(
            lambda payload: payload.__setitem__("fresh_process_snapshot_loaded", False)
        ),
        "snapshot_identity_substitution": binding_diagnostic(
            lambda payload: payload["snapshot_identity"].__setitem__("tree", "4" * 40)
        ),
        "plan_substitution": binding_diagnostic(
            lambda payload: payload["plan"].__setitem__(
                "plan_id", "reiyah.synthetic.substituted-plan"
            )
        ),
        "candidate_summary_substitution": binding_diagnostic(
            lambda payload: payload["candidate_summary"].__setitem__(
                "artifact_count", 1
            )
        ),
        "candidate_serialization_digest_substitution": binding_diagnostic(
            lambda payload: payload.__setitem__(
                "candidate_serialized_sha256", "sha256:" + "5" * 64
            )
        ),
        "index_binding_substitution": binding_diagnostic(
            lambda payload: payload["index_binding"].__setitem__("index_byte_size", 999)
        ),
        "pre_report_row_digest_substitution": binding_diagnostic(
            lambda payload: payload["token_rows"][0].__setitem__(
                "token_id", "reiyah.synthetic.substituted-stage"
            )
        ),
        "comparable_record_substitution": binding_diagnostic(
            lambda payload: payload["evaluation_comparable"].__setitem__(
                "canonical_index_byte_size", 999
            )
        ),
        "comparable_digest_substitution": binding_diagnostic(
            lambda payload: payload.__setitem__(
                "evaluation_sha256", "sha256:" + "6" * 64
            )
        ),
        **{
            f"outer_{section}_section_substitution": report_input_diagnostic(
                lambda payload, section=section: payload.__setitem__(
                    section,
                    {**payload[section], "synthetic_substitution": True},
                )
            )
            for section in REPORT_DRIVING_WORKER_SECTION_KEYS
        },
        "report_driving_stage_observation_substitution": report_input_diagnostic(
            mutate_report_driving_stage_row
        ),
        "outer_full_token_collection_coherent_substitution": coherent_outer_evidence_diagnostic(
            mutate_unbound_token_row
        ),
        "outer_nested_collection_coherent_substitution": coherent_outer_evidence_diagnostic(
            mutate_nested_row
        ),
        "outer_selector_collection_coherent_substitution": coherent_outer_evidence_diagnostic(
            mutate_selector_row
        ),
        "cross_evaluation_snapshot_substitution": equality_diagnostic(
            lambda evaluation: evaluation["snapshot_identity"].__setitem__(
                "tree", "7" * 40
            )
        ),
        "cross_evaluation_candidate_bytes_substitution": equality_diagnostic(
            lambda evaluation: evaluation.__setitem__(
                "candidate",
                CandidateProjection(
                    files=MappingProxyType({}),
                    exclusions=(),
                    serialized=b"substituted-candidate\n",
                    sha256=hashlib.sha256(b"substituted-candidate\n").hexdigest(),
                    artifact_count=0,
                    byte_count=0,
                ),
            )
        ),
        "cross_evaluation_index_bytes_substitution": equality_diagnostic(
            lambda evaluation: evaluation.__setitem__(
                "index_bytes", b'{"synthetic_index":false}\n'
            )
        ),
        "cross_evaluation_evidence_bytes_substitution": equality_diagnostic(
            lambda evaluation: evaluation.__setitem__(
                "pre_report_stage_evidence_bytes", b"substituted\n"
            )
        ),
        "cross_evaluation_comparable_substitution": equality_diagnostic(
            lambda evaluation: evaluation["evaluation_comparable"].__setitem__(
                "canonical_index_byte_size", 999
            )
        ),
        "cross_evaluation_digest_substitution": equality_diagnostic(
            lambda evaluation: evaluation.__setitem__(
                "evaluation_sha256", "sha256:" + "8" * 64
            )
        ),
        **{
            f"cross_evaluation_{section}_section_substitution": equality_diagnostic(
                lambda evaluation, section=section: evaluation.__setitem__(
                    section,
                    {
                        **evaluation[section],
                        "synthetic_substitution": True,
                    },
                )
            )
            for section in REPORT_DRIVING_WORKER_SECTION_KEYS
        },
        "duplicate_worker_pid": captured_gate_diagnostic(
            lambda: require_distinct_release_worker_records({}, {}, (1001, 1001))
        ),
        "reused_evaluation_record": captured_gate_diagnostic(
            lambda: require_distinct_release_worker_records(
                baseline_evaluation, baseline_evaluation, (1001, 1002)
            )
        ),
        "malformed_direct_worker_invocation": captured_gate_diagnostic(
            lambda: validate_release_worker_cli_operands(
                cycle_mode="ordinary_release",
                supplied_parent_pid=1001,
                observed_parent_pid=1002,
                worker_pid=1003,
                snapshot_mode="release",
                output="json",
            )
        ),
    }
    require_exact_canary_matrix(
        observed,
        RELEASE_WORKER_FAULT_CANARY_EXPECTED,
        "GA12-DUAL-EVALUATION-CANARY-COVERAGE",
    )
    for removed_case_id in RELEASE_WORKER_FAULT_CANARY_EXPECTED:
        remove_one = {
            case_id: diagnostic
            for case_id, diagnostic in observed.items()
            if case_id != removed_case_id
        }
        if (
            captured_gate_diagnostic(
                lambda remove_one=remove_one: require_exact_canary_matrix(
                    remove_one,
                    RELEASE_WORKER_FAULT_CANARY_EXPECTED,
                    "GA12-DUAL-EVALUATION-CANARY-COVERAGE",
                )
            )
            != "GA12-DUAL-EVALUATION-CANARY-COVERAGE"
        ):
            raise GateError(
                "GA12-DUAL-EVALUATION-CANARY-COVERAGE",
                "release worker remove-one coverage canary did not fail "
                f"closed for {removed_case_id}",
            )
    return "GA12-DUAL-EVALUATION-CANARY-COVERAGE"


def release_evaluation_worker_payload(
    evaluation: Mapping[str, Any],
) -> dict[str, Any]:
    snapshot = evaluation["snapshot"]
    candidate = evaluation["candidate"]
    if (
        snapshot.mode != "release"
        or evaluation["evaluation_comparable"] is None
        or evaluation["pre_report_stage_evidence_bytes"] is None
    ):
        raise GateError(
            "GA12-DUAL-EVALUATION-WORKER-PROTOCOL",
            "release worker did not produce a complete S01-S19 bundle",
        )
    payload = {
        "worker_protocol_id": RELEASE_EVALUATION_WORKER_PROTOCOL_ID,
        "fresh_process_snapshot_loaded": True,
        "snapshot_identity": {
            "mode": snapshot.mode,
            "projection_sha256": snapshot.projection_sha256,
            "file_count": snapshot.file_count,
            "byte_count": snapshot.byte_count,
            "commit": snapshot.commit,
            "tree": snapshot.tree,
            "object_format": snapshot.object_format,
        },
        "plan": evaluation["plan"],
        "candidate_summary": candidate.summary(),
        "candidate_serialized_sha256": (
            f"sha256:{hashlib.sha256(candidate.serialized).hexdigest()}"
        ),
        "predecessor": evaluation["predecessor"],
        "science": evaluation["science"],
        "security": evaluation["security"],
        "governance": evaluation["governance"],
        "toolchain": evaluation["toolchain"],
        "transport": evaluation["transport"],
        "publication_event_state": evaluation["publication_event_state"],
        "catalog": evaluation["catalog"],
        "catalog_by_id": evaluation["catalog_by_id"],
        "index": evaluation["index"],
        "index_binding": evaluation["index_binding"],
        "token_rows": evaluation["token_rows"],
        "nested_contract_rows": evaluation["nested_contract_rows"],
        "selector_rows": evaluation["selector_rows"],
        "evaluation_comparable": evaluation["evaluation_comparable"],
        "evaluation_sha256": evaluation["evaluation_sha256"],
    }
    return json_ready(payload)


def hydrate_release_evaluation_worker_payload(
    snapshot: RepositorySnapshot,
    dependencies: Mapping[str, Any],
    payload: Mapping[str, Any],
    outer_evaluation: Mapping[str, Any],
) -> dict[str, Any]:
    require_release_worker_payload_envelope(payload)
    expected_snapshot_identity = {
        "mode": snapshot.mode,
        "projection_sha256": snapshot.projection_sha256,
        "file_count": snapshot.file_count,
        "byte_count": snapshot.byte_count,
        "commit": snapshot.commit,
        "tree": snapshot.tree,
        "object_format": snapshot.object_format,
    }
    outer_plan = outer_evaluation["plan"]
    candidate = outer_evaluation["candidate"]
    index = payload["index"]
    if not isinstance(index, Mapping) or index != outer_evaluation["index"]:
        raise GateError(
            "GA12-DUAL-EVALUATION-INDEX-MISMATCH",
            "worker index payload differs from the outer production replay",
        )
    index_bytes = outer_evaluation["index_bytes"]
    outer_index_binding = outer_evaluation["index_binding"]
    pre_report_stage_evidence_bytes, comparable = (
        validate_release_worker_payload_bindings(
            payload,
            {
                "snapshot_identity": expected_snapshot_identity,
                "plan": outer_plan,
                "candidate_summary": candidate.summary(),
                "candidate_serialized_sha256": (
                    "sha256:" + hashlib.sha256(candidate.serialized).hexdigest()
                ),
                "index_binding": outer_index_binding,
                "evaluation_comparable_prefix": {
                    "candidate_projection_sha256": f"sha256:{candidate.sha256}",
                    "candidate_projection_artifact_count": candidate.artifact_count,
                    "candidate_projection_byte_count": candidate.byte_count,
                    "canonical_index_sha256": (
                        "sha256:" + hashlib.sha256(index_bytes).hexdigest()
                    ),
                    "canonical_index_byte_size": len(index_bytes),
                },
            },
        )
    )
    outer_publication_event_state = outer_evaluation["publication_event_state"]
    require_release_worker_binding(
        payload["publication_event_state"],
        outer_publication_event_state,
        "GA12-PUBLICATION-EVENT-ACTUAL-BYTE-BINDING",
        "worker actual publication-event observation differs from outer Git bytes",
    )
    outer_report_inputs = {
        section: outer_evaluation[section]
        for section in REPORT_DRIVING_WORKER_SECTION_KEYS
    }
    outer_membership = outer_evaluation["development_checks"][
        "GA12-STAGE-TOOLCHAIN-INTEGRITY"
    ]["membership"]
    validate_release_worker_report_inputs(
        payload,
        outer_report_inputs,
        membership=outer_membership,
        candidate_projection_sha256=f"sha256:{candidate.sha256}",
    )
    validate_release_worker_outer_evidence(
        payload,
        {
            "token_rows": outer_evaluation["token_rows"],
            "nested_contract_rows": outer_evaluation["nested_contract_rows"],
            "selector_rows": outer_evaluation["selector_rows"],
        },
    )
    if (
        pre_report_stage_evidence_bytes
        != outer_evaluation["pre_report_stage_evidence_bytes"]
    ):
        raise GateError(
            "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
            "worker canonical pre-report bytes differ from outer replay",
        )
    return {
        "snapshot": snapshot,
        "snapshot_identity": expected_snapshot_identity,
        "dependencies": dependencies,
        "plan": outer_plan,
        "candidate": candidate,
        "predecessor": outer_report_inputs["predecessor"],
        "science": outer_report_inputs["science"],
        "security": outer_report_inputs["security"],
        "governance": outer_report_inputs["governance"],
        "toolchain": outer_report_inputs["toolchain"],
        "transport": outer_report_inputs["transport"],
        "publication_event_state": outer_publication_event_state,
        "catalog": outer_report_inputs["catalog"],
        "catalog_by_id": outer_report_inputs["catalog_by_id"],
        "index": dict(index),
        "index_bytes": index_bytes,
        "index_binding": outer_index_binding,
        "token_rows": outer_evaluation["token_rows"],
        "nested_contract_rows": outer_evaluation["nested_contract_rows"],
        "selector_rows": outer_evaluation["selector_rows"],
        "pre_report_stage_evidence_bytes": outer_evaluation[
            "pre_report_stage_evidence_bytes"
        ],
        "evaluation_comparable": dict(comparable),
        "evaluation_sha256": payload["evaluation_sha256"],
    }


def require_release_evaluation_equality(
    first: Mapping[str, Any],
    second: Mapping[str, Any],
) -> None:
    if first["snapshot_identity"] != second["snapshot_identity"] or (
        first["candidate"].serialized != second["candidate"].serialized
    ):
        raise GateError(
            "GA12-DUAL-EVALUATION-CANDIDATE-MISMATCH",
            "release evaluations loaded different candidate bytes",
        )
    if first["index_bytes"] != second["index_bytes"]:
        raise GateError(
            "GA12-DUAL-EVALUATION-INDEX-MISMATCH",
            "release evaluations rendered different canonical index bytes",
        )
    differing_report_inputs = [
        section
        for section in REPORT_DRIVING_WORKER_SECTION_KEYS
        if first[section] != second[section]
    ]
    if differing_report_inputs:
        raise GateError(
            "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
            "release evaluations emitted different report-driving sections: "
            f"{differing_report_inputs}",
        )
    if (
        first["pre_report_stage_evidence_bytes"]
        != second["pre_report_stage_evidence_bytes"]
    ):
        raise GateError(
            "GA12-DUAL-EVALUATION-EVIDENCE-MISMATCH",
            "release evaluations emitted different pre-report evidence bytes",
        )
    if (
        first["evaluation_comparable"] != second["evaluation_comparable"]
        or first["evaluation_sha256"] != second["evaluation_sha256"]
    ):
        raise GateError(
            "GA12-DUAL-EVALUATION-DIGEST-MISMATCH",
            "release evaluation comparable records or digests differ",
        )


def compare_release_evaluations(
    first: Mapping[str, Any],
    second: Mapping[str, Any],
    worker_process_ids: Sequence[int],
) -> dict[str, Any]:
    require_distinct_release_worker_records(first, second, worker_process_ids)
    require_release_evaluation_equality(first, second)
    plan_bundle = first["plan"]["stage_evidence_contract"]["two_evaluation_bundle"]
    ordered = [
        {
            "role": role,
            "capture_sequence": sequence,
            "evaluation_sha256": first["evaluation_sha256"],
            "fresh_snapshot_loaded": True,
            "shared_mutable_state_reused": False,
        }
        for role, sequence in zip(
            plan_bundle["evaluation_roles"],
            plan_bundle["snapshot_capture_sequence"],
            strict=True,
        )
    ]
    preimage = {
        "evaluation_count": len(ordered),
        "ordered_evaluations": ordered,
        "common_evaluation_sha256": first["evaluation_sha256"],
        "equality_scope": list(plan_bundle["equality_scope"]),
        "byte_equality_scope": list(plan_bundle["byte_equality_scope"]),
    }
    summary = {
        **preimage,
        "canonical_index_byte_equal": first["index_bytes"] == second["index_bytes"],
        "pre_report_stage_evidence_byte_equal": first["pre_report_stage_evidence_bytes"]
        == second["pre_report_stage_evidence_bytes"],
        "evidence_sha256": evidence_sha256(preimage),
    }
    reuse_canary = captured_gate_diagnostic(
        lambda: compare_release_evaluations(
            first, first, (worker_process_ids[0], worker_process_ids[0])
        )
    )
    if reuse_canary != "GA12-DUAL-EVALUATION-SNAPSHOT-REUSE":
        raise GateError(
            "GA12-DUAL-EVALUATION-CANARY",
            "snapshot-reuse fault canary did not reach the comparison guard",
        )
    return {
        "summary": summary,
        "reuse_canary_diagnostic": reuse_canary,
    }


def release_stage_evidence(
    first: Mapping[str, Any],
    comparison: Mapping[str, Any],
) -> dict[str, Any]:
    candidate = first["candidate"]
    token_id = list(STAGE_PRODUCER_DISPATCH)[-1]
    collector = StageEvidenceCollector(
        f"sha256:{candidate.sha256}",
        [token_id],
    )
    collector.record(
        token_id,
        STAGE_PRODUCER_DISPATCH[token_id],
        [
            _stage_observation(
                token_id,
                comparison["summary"]["evaluation_count"],
                comparison,
            )
        ],
    )
    token_rows = [*first["token_rows"], *collector.finish()]
    required_token_ids = list(STAGE_PRODUCER_DISPATCH)
    observed_token_ids = [row["token_id"] for row in token_rows]
    missing_token_ids = [
        token_id
        for token_id in required_token_ids
        if token_id not in observed_token_ids
    ]
    unexpected_token_ids = [
        token_id
        for token_id in observed_token_ids
        if token_id not in required_token_ids
    ]
    evidence_set_preimage = {
        "token_rows": token_rows,
        "nested_contract_rows": first["nested_contract_rows"],
        "selector_rows": first["selector_rows"],
    }
    return {
        "candidate_projection_sha256": f"sha256:{candidate.sha256}",
        "required_token_ids": required_token_ids,
        "observed_token_ids": observed_token_ids,
        "missing_token_ids": missing_token_ids,
        "unexpected_token_ids": unexpected_token_ids,
        "release_evaluations": comparison["summary"],
        **evidence_set_preimage,
        "evidence_set_sha256": evidence_sha256(evidence_set_preimage),
    }


def fixture_summary_from_evaluation(
    evaluation: Mapping[str, Any],
) -> dict[str, Any]:
    snapshot = evaluation["snapshot"]
    science = evaluation["science"]
    security = evaluation["security"]
    governance = evaluation["governance"]
    science_good_passed = science["good_fixture_count"]
    science_bad_rejected = len(science["diagnostics"])
    security_rejected = sum(security["diagnostics"].values())
    governance_good_passed = len(governance["validated_positive_catalog"])
    governance_bad_rejected = sum(governance["diagnostics"].values())
    unexpected = (
        science["good_fixture_count"]
        - science_good_passed
        + science["mutation_fixture_count"]
        - science_bad_rejected
        + security["fixture_count"]
        - security_rejected
        + len(governance["validated_positive_catalog"])
        - governance_good_passed
        + governance["fixture_count"]
        - governance_bad_rejected
    )
    security_paths = sorted(
        path
        for path in snapshot.files
        if path.startswith(SECURITY_FIXTURE_PREFIX) and path.endswith(".json")
    )
    summary = {
        "science_schema_count": science["schema_count"],
        "science_good_total": science["good_fixture_count"],
        "science_good_passed": science_good_passed,
        "science_known_bad_total": science["mutation_fixture_count"],
        "science_known_bad_rejected_for_declared_rule": science_bad_rejected,
        "science_semantic_rule_count": science["semantic_rule_count"],
        "science_schema_rejected_known_bad_count": science[
            "schema_rejected_mutation_count"
        ],
        "validator_security_known_bad_total": security["fixture_count"],
        "validator_security_rejected_for_declared_diagnostic": security_rejected,
        "governance_known_good_total": len(governance["validated_positive_catalog"]),
        "governance_known_good_passed": governance_good_passed,
        "governance_known_bad_total": governance["fixture_count"],
        "governance_rejected_for_declared_diagnostic": governance_bad_rejected,
        "unexpected_outcomes": unexpected,
        "schema_set_sha256": f"sha256:{science['schema_set_sha256']}",
        "good_fixture_set_sha256": f"sha256:{science['good_fixture_set_sha256']}",
        "known_bad_fixture_set_sha256": f"sha256:{science['mutation_fixture_set_sha256']}",
        "security_fixture_set_sha256": f"sha256:{artifact_set_digest(snapshot, security_paths)}",
        "governance_positive_fixture_set_sha256": f"sha256:{governance['positive_fixture_set_sha256']}",
        "governance_known_bad_fixture_set_sha256": f"sha256:{governance['fixture_set_sha256']}",
    }
    validate_report_count_equalities(summary)
    return summary


def render_release_report(
    evaluation: Mapping[str, Any],
    comparison: Mapping[str, Any],
    *,
    require_report_readback: bool,
) -> tuple[dict[str, Any], bytes]:
    snapshot = evaluation["snapshot"]
    dependencies = evaluation["dependencies"]
    plan = evaluation["plan"]
    stage_evidence = release_stage_evidence(evaluation, comparison)
    token_rows = stage_evidence["token_rows"]
    nested_rows = stage_evidence["nested_contract_rows"]
    selector_rows = stage_evidence["selector_rows"]
    control_summary = reduce_control_evidence(
        plan,
        [row["token_id"] for row in token_rows],
        [row["contract_id"] for row in nested_rows],
    )
    closure_summary = reduce_correction_evidence(
        plan,
        token_rows,
        nested_rows,
        selector_rows,
        evaluation["catalog_by_id"],
    )
    fixture_summary = fixture_summary_from_evaluation(evaluation)
    final_outcome = reduce_final_report_implication(
        stage_evidence,
        control_summary,
        closure_summary,
        fixture_summary,
    )
    predecessor = evaluation["predecessor"]
    predecessor_report = {
        key: predecessor[key]
        for key in (
            "subject_version",
            "historical_index_binding",
            "historical_sidecar_binding",
            "canonical_report_binding",
            "publisher_receipt_binding",
            "recovery_record_binding",
            "predecessor_artifact_count",
            "unchanged_artifact_count",
            "changed_paths",
            "added_paths",
            "removed_paths",
            "missing_paths",
            "unexpected_drift_paths",
        )
    }
    toolchain = evaluation["toolchain"]
    transport = evaluation["transport"]
    report = {
        "schema_id": "https://schemas.reiyah.invalid/gate-a/1.2.0/validation-report.schema.json",
        "schema_version": ARTIFACT_VERSION,
        "artifact_id": "reiyah.validation-report.gate-a-1.2.0",
        "record_kind": "canonical_release_report",
        "report_id": "reiyah.validation-report.gate-a",
        "version": ARTIFACT_VERSION,
        "validation_plan_id": plan["plan_id"],
        "mission_release_id": MISSION_RELEASE_ID,
        "protocol_release_id": PROTOCOL_RELEASE_ID,
        "distribution_profile": "public_open_source",
        "source_ledger_version": "1.1.0",
        "result": final_outcome["result"],
        "exit_code": final_outcome["exit_code"],
        "architecture_status": final_outcome["architecture_status"],
        "index_binding": dict(evaluation["index_binding"]),
        "candidate_projection": evaluation["candidate"].summary(),
        "stage_evidence": stage_evidence,
        "predecessor_inheritance": predecessor_report,
        "fixture_summary": fixture_summary,
        "control_summary": control_summary,
        "correction_closure_summary": closure_summary,
        "security_toolchain_summary": {
            "dependency_count": toolchain["dependency_count"],
            "dependency_names": toolchain["dependency_names"],
            "seatbelt_profile_sha256": f"sha256:{toolchain['seatbelt_profile_sha256']}",
            "external_launcher_precedes_python": snapshot.mode == "release",
            "format_checker_count": len(FORMAT_CHECKERS),
            "unknown_formats_rejected": set(
                schema_format_coverage(snapshot)["declarations"]
            ).issubset(FORMAT_CHECKERS),
            "toolchain_postload_reverified": True,
        },
        "transport_summary": {
            "status": transport["status"],
            "publisher_receipt_is_independent_verification": transport[
                "publisher_receipt_is_independent_verification"
            ],
            "independent_record_id": transport["independent_record_id"],
        },
        "offline": plan["offline_required"],
        "read_only": plan["read_only_required"],
        "deterministic": plan["deterministic_required"],
        "release_evidence": snapshot.mode == "release",
        "runtime_authorized": plan["runtime_authorized"],
        "acceptance_created": plan["acceptance_authorized"],
        "operator_acceptance_state": "unaccepted",
        "gate_b_authorized": plan["gate_b_authorized"],
        "diagnostic_sort": ["rule_id", "path", "object_id", "message"],
        "diagnostics": final_outcome["diagnostics"],
    }
    validator = validator_for_schema(
        snapshot,
        dependencies,
        REPORT_SCHEMA_PATH,
        (COMMON_SCHEMA_PATH,),
    )
    errors = schema_error_records(validator, report)
    if errors:
        first = errors[0]
        raise GateError(
            "GA12-REPORT-SCHEMA",
            f"canonical report failed {first['schema_keyword']} at "
            f"{first['instance_pointer']}: {first['message']}",
        )
    encoded = canonical_json_bytes(report) + b"\n"
    if require_report_readback:
        current = snapshot.read(plan["canonical_report_path"])
        if current != encoded:
            raise GateError(
                "GA12-REPORT-READBACK",
                "committed canonical report bytes differ from deterministic replay",
            )
    return report, encoded


def render_development_observation(
    evaluation: Mapping[str, Any],
) -> tuple[dict[str, Any], bytes]:
    snapshot = evaluation["snapshot"]
    plan = evaluation["plan"]
    observed_checks = [
        {
            "producer_check_id": producer_check_id,
            "subject_count": max(1, len(payload)),
            "evidence_sha256": evidence_sha256(payload),
        }
        for producer_check_id, payload in evaluation["development_checks"].items()
    ]
    observation = {
        "schema_id": "https://schemas.reiyah.invalid/gate-a/1.2.0/validation-report.schema.json",
        "schema_version": ARTIFACT_VERSION,
        "artifact_id": "reiyah.validation-observation.gate-a-development-1.2.0",
        "record_kind": "development_observation",
        "observation_id": "reiyah.validation-observation.gate-a-development",
        "version": ARTIFACT_VERSION,
        "validation_plan_id": plan["plan_id"],
        "mission_release_id": MISSION_RELEASE_ID,
        "protocol_release_id": PROTOCOL_RELEASE_ID,
        "result": "development_observation_complete",
        "architecture_status": "not_evaluated",
        "release_evidence": False,
        "canonical_report_emitted": False,
        "candidate_projection": evaluation["candidate"].summary(),
        "rendered_index": {
            "path": plan["index_path"],
            "sha256": f"sha256:{hashlib.sha256(evaluation['index_bytes']).hexdigest()}",
            "byte_size": len(evaluation["index_bytes"]),
            "committed_readback_verified": False,
        },
        "observed_checks": observed_checks,
        "offline": plan["offline_required"],
        "read_only": plan["read_only_required"],
        "deterministic": plan["deterministic_required"],
        "runtime_authorized": plan["runtime_authorized"],
        "acceptance_created": False,
        "operator_acceptance_state": "unaccepted",
        "gate_b_authorized": plan["gate_b_authorized"],
    }
    validator = validator_for_schema(
        snapshot,
        evaluation["dependencies"],
        REPORT_SCHEMA_PATH,
        (COMMON_SCHEMA_PATH,),
    )
    errors = schema_error_records(validator, observation)
    if errors:
        first = errors[0]
        raise GateError(
            "GA12-REPORT-SCHEMA",
            f"development observation failed {first['schema_keyword']} at "
            f"{first['instance_pointer']}: {first['message']}",
        )
    return observation, canonical_json_bytes(observation) + b"\n"


def require_bootstrap_path_state(
    snapshot: RepositorySnapshot,
    plan: Mapping[str, Any],
    mode: str,
) -> None:
    index_paths = {plan["index_path"], plan["index_sidecar_path"]}
    report_path = plan["canonical_report_path"]
    present_index_paths = index_paths & set(snapshot.files)
    report_present = report_path in snapshot.files
    if mode == "emit_index":
        if present_index_paths or report_present:
            raise GateError(
                "GA12-REPORT-CYCLE-STATE",
                "--emit-index requires index, sidecar, and report paths to be absent",
            )
    elif mode == "emit_report":
        if present_index_paths != index_paths or report_present:
            raise GateError(
                "GA12-REPORT-CYCLE-STATE",
                "--emit-report requires committed index and sidecar bytes and an absent report path",
            )
    elif mode == "ordinary_release":
        if present_index_paths != index_paths or not report_present:
            raise GateError(
                "GA12-REPORT-CYCLE-STATE",
                "ordinary release requires committed index, sidecar, and report paths",
            )
    else:
        raise GateError("GA12-INTERNAL", f"unsupported report cycle mode: {mode}")


def validate_release_worker_cli_operands(
    *,
    cycle_mode: str | None,
    supplied_parent_pid: int | None,
    observed_parent_pid: int,
    worker_pid: int,
    snapshot_mode: str,
    output: str,
) -> None:
    if (
        cycle_mode not in {"emit_report", "ordinary_release"}
        or supplied_parent_pid is None
        or supplied_parent_pid <= 1
        or observed_parent_pid != supplied_parent_pid
        or worker_pid == supplied_parent_pid
        or snapshot_mode != "release"
        or output != "json"
    ):
        raise GateError(
            "GA12-DUAL-EVALUATION-WORKER-PROTOCOL",
            "release worker closed CLI/parent-process contract failed",
        )


def start_release_evaluation_worker(cycle_mode: str) -> subprocess.Popen[bytes]:
    if cycle_mode not in {"emit_report", "ordinary_release"}:
        raise GateError(
            "GA12-DUAL-EVALUATION-WORKER-PROTOCOL",
            f"unsupported release worker cycle mode: {cycle_mode}",
        )
    command = [
        str(PYTHON_PATH),
        "-I",
        "-S",
        "-B",
        str(CANONICAL_ROOT / TOOL_PATH),
        "--snapshot-mode",
        "release",
        "--output",
        "json",
        "--release-evaluation-worker",
        "--worker-cycle-mode",
        cycle_mode,
        "--worker-parent-pid",
        str(os.getpid()),
    ]
    try:
        return subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={
                "LANG": "C",
                "LC_ALL": "C",
                "PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin",
            },
        )
    except OSError as exc:
        raise GateError(
            "GA12-DUAL-EVALUATION-WORKER-EXEC",
            f"cannot exec isolated release evaluation worker: {exc}",
        ) from exc


def run_release_evaluation_workers(
    cycle_mode: str,
) -> tuple[list[Mapping[str, Any]], tuple[int, int]]:
    workers = [
        start_release_evaluation_worker(cycle_mode),
        start_release_evaluation_worker(cycle_mode),
    ]
    process_ids = (workers[0].pid, workers[1].pid)
    if len(set(process_ids)) != 2 or os.getpid() in process_ids:
        for worker in workers:
            worker.kill()
            worker.wait()
        raise GateError(
            "GA12-DUAL-EVALUATION-SNAPSHOT-REUSE",
            "release workers do not have two distinct child process identities",
        )
    completed: list[tuple[int, bytes, bytes]] = []
    for worker in workers:
        stdout, stderr = worker.communicate()
        completed.append((worker.returncode, stdout, stderr))
    payloads: list[Mapping[str, Any]] = []
    for ordinal, (returncode, stdout, stderr) in enumerate(completed, 1):
        if returncode != 0 or stderr:
            detail = (stderr or stdout)[:2000].decode("utf-8", "replace")
            raise GateError(
                "GA12-DUAL-EVALUATION-WORKER-EXEC",
                f"release worker {ordinal} failed ({returncode}): {detail}",
            )
        if not stdout.endswith(b"\n") or stdout.count(b"\n") != 1:
            raise GateError(
                "GA12-DUAL-EVALUATION-WORKER-PROTOCOL",
                f"release worker {ordinal} output is not one canonical JSON line",
            )
        payload = strict_json(stdout, f"release evaluation worker {ordinal}")
        if not isinstance(payload, Mapping):
            raise GateError(
                "GA12-DUAL-EVALUATION-WORKER-PROTOCOL",
                f"release worker {ordinal} payload must be an object",
            )
        if canonical_json_bytes(payload) + b"\n" != stdout:
            raise GateError(
                "GA12-DUAL-EVALUATION-WORKER-PROTOCOL",
                f"release worker {ordinal} output is not canonical JSON",
            )
        payloads.append(payload)
    return payloads, process_ids


def build_outputs(
    snapshot: RepositorySnapshot,
    *,
    cycle_mode: str,
) -> tuple[dict[str, Any] | None, bytes | None, dict[str, Any], bytes]:
    if snapshot.mode == "development":
        if cycle_mode != "development":
            raise GateError(
                "GA12-CLI-ARGUMENT",
                "release bootstrap and readback modes require a release snapshot",
            )
        evaluation = evaluate_snapshot(
            snapshot,
            require_index_readback=False,
            collect_release_stage_evidence=False,
        )
        observation, observation_bytes = render_development_observation(evaluation)
        return (
            observation,
            observation_bytes,
            evaluation["index"],
            evaluation["index_bytes"],
        )
    require_bootstrap_path_state(
        snapshot, strict_json(snapshot.read(PLAN_PATH), PLAN_PATH), cycle_mode
    )
    if cycle_mode == "emit_index":
        evaluation = evaluate_snapshot(
            snapshot,
            require_index_readback=False,
            collect_release_stage_evidence=False,
        )
        return None, None, evaluation["index"], evaluation["index_bytes"]
    payloads, worker_process_ids = run_release_evaluation_workers(cycle_mode)
    outer_toolchain = validate_toolchain_lock(snapshot)
    dependencies = activate_locked_schema_dependencies()
    outer_evaluation = evaluate_snapshot(
        snapshot,
        require_index_readback=True,
        collect_release_stage_evidence=True,
        activated_dependencies=dependencies,
    )
    first = hydrate_release_evaluation_worker_payload(
        snapshot,
        dependencies,
        payloads[0],
        outer_evaluation,
    )
    second = hydrate_release_evaluation_worker_payload(
        snapshot,
        dependencies,
        payloads[1],
        outer_evaluation,
    )
    comparison = compare_release_evaluations(first, second, worker_process_ids)
    report, report_bytes = render_release_report(
        first,
        comparison,
        require_report_readback=cycle_mode == "ordinary_release",
    )
    if validate_toolchain_lock(snapshot) != outer_toolchain:
        raise GateError(
            "GA12-TOOLCHAIN-POSTLOAD",
            "outer report reducer toolchain observation drifted",
        )
    finalize_snapshot(snapshot)
    return report, report_bytes, first["index"], first["index_bytes"]


def dependency_templates() -> list[dict[str, Any]]:
    site = "/opt/homebrew/lib/python3.14/site-packages"
    return [
        {
            "name": "attrs",
            "version": "26.1.0",
            "site_packages": site,
            "dist_info": "attrs-26.1.0.dist-info",
            "import_roots": ["attr", "attrs"],
        },
        {
            "name": "jsonschema",
            "version": "4.26.0",
            "site_packages": site,
            "dist_info": "jsonschema-4.26.0.dist-info",
            "import_roots": ["jsonschema"],
        },
        {
            "name": "jsonschema-specifications",
            "version": "2025.9.1",
            "site_packages": site,
            "dist_info": "jsonschema_specifications-2025.9.1.dist-info",
            "import_roots": ["jsonschema_specifications"],
        },
        {
            "name": "referencing",
            "version": "0.37.0",
            "site_packages": site,
            "dist_info": "referencing-0.37.0.dist-info",
            "import_roots": ["referencing"],
        },
        {
            "name": "rpds-py",
            "version": "0.30.0",
            "site_packages": site,
            "dist_info": "rpds_py-0.30.0.dist-info",
            "import_roots": ["rpds"],
        },
        {
            "name": "typing_extensions",
            "version": "4.15.0",
            "site_packages": site,
            "dist_info": "typing_extensions-4.15.0.dist-info",
            "import_roots": ["typing_extensions.py"],
        },
    ]


def print_observed_toolchain(output: str) -> None:
    observed = observed_toolchain(dependency_templates())
    if output == "json":
        print(
            json.dumps(
                observed, ensure_ascii=True, sort_keys=True, separators=(",", ":")
            )
        )
    else:
        print("Gate A 1.2.0 observed toolchain")
        print(
            f"  platform: {observed['platform']['product_version']} ({observed['platform']['product_build_version']})"
        )
        for dependency in observed["dependencies"]:
            print(
                f"  {dependency['name']} {dependency['version']}: "
                f"RECORD {dependency['record_sha256']}, roots {dependency['import_roots_sha256']}"
            )


def render_report(report: Mapping[str, Any], output: str) -> None:
    if output == "json":
        sys.stdout.buffer.write(
            json.dumps(
                report, ensure_ascii=True, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
            + b"\n"
        )
        return
    projection_summary = report["candidate_projection"]
    if report["record_kind"] == "development_observation":
        print(f"Gate A {ARTIFACT_VERSION} development observation: {report['result']}")
        print("  architecture: not_evaluated (development is not release evidence)")
        print(
            f"  candidate projection: {projection_summary['artifact_count']} artifacts, "
            f"{projection_summary['sha256']}"
        )
        print(
            f"  observed producer checks: {len(report['observed_checks'])}; "
            "canonical report emitted: false"
        )
        return
    fixtures = report["fixture_summary"]
    print(
        f"Gate A {ARTIFACT_VERSION} canonical architecture report: {report['result']}"
    )
    print(
        f"  architecture: {report['architecture_status']} (operator acceptance: unaccepted)"
    )
    print(
        f"  candidate projection: {projection_summary['artifact_count']} artifacts, "
        f"{projection_summary['sha256']}"
    )
    print(
        f"  v1.2 science: {fixtures['science_schema_count']} schemas, "
        f"{fixtures['science_good_passed']}/{fixtures['science_good_total']} good, "
        f"{fixtures['science_known_bad_rejected_for_declared_rule']}/"
        f"{fixtures['science_known_bad_total']} known-bad"
    )
    print(
        f"  validator security: {fixtures['validator_security_rejected_for_declared_diagnostic']}/"
        f"{fixtures['validator_security_known_bad_total']} reason-specific rejections"
    )
    print("  GA-17 and independent transport verification: not_evaluated")


class GateArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise GateError("GA12-CLI-ARGUMENT", message)


def parse_arguments(argv: Sequence[str]) -> argparse.Namespace:
    parser = GateArgumentParser(description=__doc__)
    parser.add_argument(
        "--snapshot-mode",
        choices=("development", "release"),
        default="development",
        help="development snapshots filesystem bytes; release validates a clean immutable Git tree",
    )
    parser.add_argument("--output", choices=("human", "json"), default="human")
    parser.add_argument(
        "--observe-toolchain",
        action="store_true",
        help="emit observed lock inputs without validating a repository snapshot",
    )
    parser.add_argument(
        "--emit-index",
        action="store_true",
        help="emit the canonical compact 1.2 index from the same validated in-memory projection",
    )
    parser.add_argument(
        "--emit-report",
        action="store_true",
        help="emit canonical report bytes after exact committed index readback while the report path is absent",
    )
    parser.add_argument(
        "--release-evaluation-worker",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--worker-cycle-mode",
        choices=("emit_report", "ordinary_release"),
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--worker-parent-pid",
        type=int,
        default=None,
        help=argparse.SUPPRESS,
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    try:
        options = parse_arguments(arguments)
        selected_special_modes = sum(
            bool(value)
            for value in (
                options.observe_toolchain,
                options.emit_index,
                options.emit_report,
                options.release_evaluation_worker,
            )
        )
        if selected_special_modes > 1:
            raise GateError(
                "GA12-CLI-ARGUMENT",
                "--observe-toolchain, --emit-index, --emit-report, and the internal worker mode are mutually exclusive",
            )
        worker_arguments_present = (
            options.worker_cycle_mode is not None
            or options.worker_parent_pid is not None
        )
        if worker_arguments_present != options.release_evaluation_worker:
            raise GateError(
                "GA12-CLI-ARGUMENT",
                "internal release worker arguments must be supplied as one closed set",
            )
        verify_repository_identity()
        if options.observe_toolchain:
            print_observed_toolchain(options.output)
            return 0
        if (
            options.emit_index
            or options.emit_report
            or options.release_evaluation_worker
        ) and (options.snapshot_mode != "release" or options.output != "json"):
            raise GateError(
                "GA12-CLI-ARGUMENT",
                "release bootstrap and internal worker modes require --snapshot-mode release --output json",
            )
        if options.release_evaluation_worker:
            validate_release_worker_cli_operands(
                cycle_mode=options.worker_cycle_mode,
                supplied_parent_pid=options.worker_parent_pid,
                observed_parent_pid=os.getppid(),
                worker_pid=os.getpid(),
                snapshot_mode=options.snapshot_mode,
                output=options.output,
            )
        snapshot = (
            release_snapshot()
            if options.snapshot_mode == "release"
            else development_snapshot()
        )
        if options.release_evaluation_worker:
            if options.worker_cycle_mode is None:
                raise GateError(
                    "GA12-DUAL-EVALUATION-WORKER-PROTOCOL",
                    "release worker cycle mode is absent",
                )
            worker_plan = strict_json(snapshot.read(PLAN_PATH), PLAN_PATH)
            require_bootstrap_path_state(
                snapshot,
                worker_plan,
                options.worker_cycle_mode,
            )
            evaluation = evaluate_snapshot(
                snapshot,
                require_index_readback=True,
                collect_release_stage_evidence=True,
            )
            payload = release_evaluation_worker_payload(evaluation)
            sys.stdout.buffer.write(canonical_json_bytes(payload) + b"\n")
            return 0
        cycle_mode = (
            "emit_index"
            if options.emit_index
            else "emit_report"
            if options.emit_report
            else "ordinary_release"
            if options.snapshot_mode == "release"
            else "development"
        )
        report, report_bytes, _index, index_bytes = build_outputs(
            snapshot,
            cycle_mode=cycle_mode,
        )
        if options.emit_index:
            sys.stdout.buffer.write(index_bytes)
            return 0
        if options.emit_report:
            if report is None or report_bytes is None:
                raise GateError(
                    "GA12-INTERNAL",
                    "canonical report bootstrap did not render report bytes",
                )
            sys.stdout.buffer.write(report_bytes)
            return int(report["exit_code"])
        if report is None:
            raise GateError("GA12-INTERNAL", "validation output was not rendered")
        render_report(report, options.output)
        return int(report.get("exit_code", 0))
    except GateError as exc:
        failure = {
            "report_id": "reiyah.validation-execution-error@1.2.0",
            "artifact_version": ARTIFACT_VERSION,
            "protocol_release_id": PROTOCOL_RELEASE_ID,
            "mission_release_id": MISSION_RELEASE_ID,
            "status": "fail",
            "diagnostic": {"code": exc.code, "message": exc.message},
        }
        requested_output = "human"
        for index, argument in enumerate(arguments):
            if (
                argument == "--output"
                and index + 1 < len(arguments)
                and arguments[index + 1] == "json"
            ):
                requested_output = "json"
            elif argument == "--output=json":
                requested_output = "json"
        if requested_output == "json":
            print(
                json.dumps(
                    failure, ensure_ascii=True, sort_keys=True, separators=(",", ":")
                )
            )
        else:
            print(f"Gate A {ARTIFACT_VERSION} validation substrate: fail")
            print(f"  {exc.code}: {exc.message}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
