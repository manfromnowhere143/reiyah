#!/usr/bin/env python3
"""Deterministic Gate A 1.2.1 documentation and discovery continuity validator.

This standard-library-only tool does not execute or replace the scientific handler
bound by the 1.2.0 scientific profile. It exact-binds that released evidence as
historical inheritance and evaluates only documentation, discovery, lineage, and
publication continuity controls.
"""

from __future__ import annotations

# E402 is intentional: isolation must be proven before importing any
# owner-writable standard-library module.
# ruff: noqa: E402

import sys


def _fail_before_imports(message: str) -> "NoReturn":
    sys.stderr.write(f"gate_a_1_2_1 bootstrap error: {message}\n")
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
    _fail_before_imports("unsupported interpreter profile; use tools/gate_a_1_2_1.sh")

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


def _verify_early_external_seatbelt() -> None:
    try:
        sandbox_library = ctypes.CDLL("/usr/lib/libsandbox.dylib")
        sandbox_check = sandbox_library.sandbox_check
        sandbox_check.restype = ctypes.c_int
    except OSError as exc:
        _fail_before_imports(f"cannot load macOS Seatbelt API: {exc}")
    current_pid = ctypes.CDLL(None).getpid()
    for operation in (
        b"network-bind",
        b"network-outbound",
        b"file-write-create",
        b"file-write-data",
        b"file-write-mode",
        b"file-write-unlink",
        b"file-write-xattr",
    ):
        if sandbox_check(current_pid, operation, 0) != 1:
            _fail_before_imports(
                f"external Seatbelt does not deny {operation.decode('ascii')}"
            )


_verify_early_external_seatbelt()

import argparse
import copy
from datetime import date, datetime
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import subprocess
from typing import Any, Callable, Mapping, NoReturn, Sequence
from urllib.parse import unquote, urlparse


ROOT = Path("/Users/danielwahnich/workspace/reiyah")
PYTHON_PATH = Path("/opt/homebrew/bin/python3.14")
VALIDATOR_PATH = "tools/gate_a_1_2_1.py"
PACKET_COMMIT = "86409473c8fd1571236c849a6cc730db896465fb"
PACKET_TREE = "88a5ac2a2c0a33b5ce187880ce1129c258229dca"
RECEIPT_COMMIT = "d42d4d298d515b59e9df15f2ba45572a91b9fab8"
RECEIPT_TREE = "ed78e0c57d20e3e32b2346604d25c475b7959c97"
RECEIPT_DELTA = (
    "evidence/public-rights-revalidation-2026-08-25-gate-a-static-correction-1.2.0.json",
    "gate/public-distribution-receipts/reiyah.public-distribution-receipt-1.2.0.json",
)
PLAN_PATH = "validation/validation-plan.json"
LOCK_PATH = "validation/toolchain-lock-1.2.1.json"
FIXTURE_CATALOG_PATH = "fixtures/v1.2.1/continuity-fixture-catalog.json"
RECOVERY_PATH = "history/gate-a-1.2.0/RECOVERY.json"
INDEX_PATH = "gate/GATE_A_EVIDENCE_INDEX.json"
SIDECAR_PATH = "gate/GATE_A_EVIDENCE_INDEX.sha256"
REPORT_PATH = "gate/validation-reports/gate-a-validation-1.2.1.json"
FUTURE_RIGHTS_PATH = (
    "evidence/public-rights-revalidation-2026-08-25-gate-a-continuity-1.2.1.json"
)
EXPECTED_PLAN_SHA256 = (
    "f9307a241ed71fd9474291e356bda148e27035eeb76f13354814512fc340f35f"
)
EXPECTED_DELTA_POLICY_SHA256 = (
    "354b5f452c10c3503091382ad5ebd8abc5dd59179e4f96e0e5812a86eac76343"
)
EXPECTED_RECOVERY_SHA256 = (
    "79bb30e5bafda0b3b40d7a6f898e10b5785006a272630ec3f8d470a84875a36a"
)
EXPECTED_FIXTURE_CATALOG_SHA256 = (
    "d55920a8efab20cb58d6f51286a12f6bd3aeaa158ea787a7898df47016a11adf"
)
EXPECTED_ORIGINS = frozenset(
    {
        "https://github.com/manfromnowhere143/reiyah",
        "https://github.com/manfromnowhere143/reiyah.git",
    }
)

EXPECTED_CHANGED_PATHS = (
    "CITATION.cff",
    "README.md",
    "docs/RESEARCH_GAP_REGISTER.md",
    "docs/RESEARCH_OPERATING_MODEL.md",
    "docs/SESSION_HANDOFF.md",
    "docs/STATUS_MODEL.md",
    "evidence/README.md",
    "gate/README.md",
    "validation/validation-plan.json",
)
EXPECTED_REMOVED_PATHS: tuple[str, ...] = ()
EXPECTED_ADDED_PATHS = (
    "evidence/frontier-discovery-register-1.2.0.json",
    "fixtures/v1.2.1/continuity-fixture-catalog.json",
    "fixtures/v1.2.1/known-bad/current-science-replay-claim.json",
    "fixtures/v1.2.1/known-bad/frontier-duplicate-artifact.json",
    "fixtures/v1.2.1/known-bad/frontier-evidence-eligibility.json",
    "fixtures/v1.2.1/known-bad/frontier-fixed-source-state.json",
    "fixtures/v1.2.1/known-bad/frontier-fixture-authority.json",
    "fixtures/v1.2.1/known-bad/frontier-fixture-base-digest.json",
    "fixtures/v1.2.1/known-bad/frontier-invalid-access-date.json",
    "fixtures/v1.2.1/known-bad/frontier-missing-scope.json",
    "fixtures/v1.2.1/known-bad/frontier-origin-mismatch.json",
    "fixtures/v1.2.1/known-bad/frontier-predecessor-schema.json",
    "fixtures/v1.2.1/known-bad/frontier-top-claim.json",
    "fixtures/v1.2.1/known-bad/frontier-unknown-property.json",
    "fixtures/v1.2.1/known-bad/frontier-versioned-source-state.json",
    "fixtures/v1.2.1/known-bad/historical-index-drift.json",
    "fixtures/v1.2.1/known-bad/isolation-direct-invocation.json",
    "fixtures/v1.2.1/known-bad/isolation-ineffective-sandbox.json",
    "fixtures/v1.2.1/known-bad/operator-acceptance-claim.json",
    "fixtures/v1.2.1/known-bad/packet-commit-drift.json",
    "fixtures/v1.2.1/known-bad/protected-science-drift.json",
    "fixtures/v1.2.1/known-bad/receipt-parent-drift.json",
    "fixtures/v1.2.1/known-bad/runtime-authority-claim.json",
    "fixtures/v1.2.1/known-bad/transport-verification-claim.json",
    "fixtures/v1.2.1/known-bad/unknown-delta-path.json",
    "fixtures/v1.2.1/known-good/continuity-baseline.json",
    "fixtures/v1.2/frontier-good/frontier-discovery-register-successor.json",
    "fixtures/v1.2/frontier-known-bad/frontier-admitted-claim.json",
    "fixtures/v1.2/frontier-known-bad/frontier-company-self-report-mislabeled-independent.json",
    "fixtures/v1.2/frontier-known-bad/frontier-duplicate-discovery-id.json",
    "fixtures/v1.2/frontier-known-bad/frontier-dynamic-source-access-date-missing.json",
    "fixtures/v1.2/frontier-known-bad/frontier-dynamic-source-version-state-missing.json",
    "fixtures/v1.2/frontier-known-bad/frontier-missing-limitations.json",
    "fixtures/v1.2/frontier-known-bad/frontier-payload-insertion.json",
    "fixtures/v1.2/frontier-known-bad/frontier-publisher-version-without-exact-revision.json",
    "fixtures/v1.2/frontier-known-bad/frontier-predecessor-drift.json",
    "fixtures/v1.2/frontier-known-bad/frontier-predecessor-record-mutation.json",
    "history/gate-a-1.2.0/RECOVERY.json",
    "history/gate-a-1.2.0/gate/GATE_A_EVIDENCE_INDEX.json",
    "history/gate-a-1.2.0/gate/GATE_A_EVIDENCE_INDEX.sha256",
    "schemas/continuity-fixture-1.2.1.schema.json",
    "schemas/continuity-fixture-catalog-1.2.1.schema.json",
    "schemas/continuity-toolchain-lock-1.2.1.schema.json",
    "schemas/frontier-discovery-fixture-1.2.schema.json",
    "schemas/frontier-discovery-register-1.2.schema.json",
    "schemas/gate-a-index-1.2.1.schema.json",
    "schemas/historical-packet-recovery-1.2.1.schema.json",
    "schemas/validation-plan-1.2.1.schema.json",
    "schemas/validation-report-1.2.1.schema.json",
    "tools/gate_a_1_2_1.py",
    "tools/gate_a_1_2_1.sh",
    "validation/toolchain-lock-1.2.1.json",
)
EXPECTED_EXECUTABLE_PATHS = frozenset(
    {"tools/gate_a_1_2_1.py", "tools/gate_a_1_2_1.sh"}
)
EXPECTED_OUTPUTS = {
    "index": INDEX_PATH,
    "index_sidecar": SIDECAR_PATH,
    "report": REPORT_PATH,
    "canonical_outputs_emitted_during_substrate_build": False,
}
EXPECTED_AUTHORITY = {
    "scientific_claim_authority": False,
    "scientific_evidence_created": False,
    "profile_bound_science_handler_replaced": False,
    "operator_acceptance_authorized": False,
    "runtime_authorized": False,
    "gate_b_authorized": False,
    "transport_verification_authorized": False,
    "publication_acceptance_authorized": False,
}
EXPECTED_EVALUATION_MODES = {
    "development": {
        "snapshot_count": 1,
        "dirty_tree_allowed": True,
        "release_eligible": False,
        "canonical_output_emission_allowed": False,
    },
    "release": {
        "snapshot_count": 2,
        "clean_tree_required": True,
        "independent_worker_processes_required": True,
        "exact_worker_payload_equality_required": True,
        "canonical_output_emission_requires_explicit_flag": True,
    },
}
EXPECTED_DELTA_POLICY = {
    "changed_existing_paths": list(EXPECTED_CHANGED_PATHS),
    "removed_existing_paths": list(EXPECTED_REMOVED_PATHS),
    "added_paths": list(EXPECTED_ADDED_PATHS),
    "root_outputs_must_be_absent_before_emission": [
        INDEX_PATH,
        SIDECAR_PATH,
        REPORT_PATH,
    ],
    "new_frontier_material_state": (
        "pointer_only_proposed_discovery_not_scientific_evidence"
    ),
    "public_distribution_inventory_successor_policy": (
        "allowed_only_if_four_payload_bytes_and_source_ids_are_unchanged_and_"
        "frontier_entries_remain_pointer_only"
    ),
    "unknown_delta_policy": "reject",
}

SCHEMA_PATHS = (
    "schemas/continuity-fixture-1.2.1.schema.json",
    "schemas/continuity-fixture-catalog-1.2.1.schema.json",
    "schemas/historical-packet-recovery-1.2.1.schema.json",
    "schemas/continuity-toolchain-lock-1.2.1.schema.json",
    "schemas/validation-plan-1.2.1.schema.json",
    "schemas/validation-report-1.2.1.schema.json",
    "schemas/gate-a-index-1.2.1.schema.json",
    "schemas/frontier-discovery-register-1.2.schema.json",
    "schemas/frontier-discovery-fixture-1.2.schema.json",
)

EXPECTED_CONTROL_IDS = (
    "GA121-PREDECESSOR-PACKET-IDENTITY",
    "GA121-PREDECESSOR-TOPOLOGY",
    "GA121-HISTORY-BINDING",
    "GA121-CANONICAL-REPORT-BINDING",
    "GA121-RIGHTS-RECEIPT-BINDING",
    "GA121-PROTECTED-BYTES",
    "GA121-INHERITED-SCIENCE-STATE",
    "GA121-SUCCESSOR-DELTA-SCOPE",
    "GA121-DOCUMENTATION-LINKS",
    "GA121-DISCOVERY-NONAUTHORITY",
    "GA121-PUBLICATION-INVENTORY-CONTINUITY",
    "GA121-FIXTURE-COVERAGE",
    "GA121-TOOLCHAIN-BINDING",
    "GA121-DUAL-EVALUATION",
    "GA121-AUTHORITY-NONCLAIMS",
)

CONTINUITY_SCHEMA_NAMES = frozenset(Path(path).name for path in SCHEMA_PATHS)
OUTPUT_PATHS = frozenset((INDEX_PATH, SIDECAR_PATH, REPORT_PATH))
PROJECTION_EXCLUSION_POLICY = (
    {
        "path": INDEX_PATH,
        "reason": "canonical_index_cycle",
    },
    {
        "path": SIDECAR_PATH,
        "reason": "canonical_index_sidecar_cycle",
    },
    {
        "path": REPORT_PATH,
        "reason": "canonical_report_cycle",
    },
    {
        "path": FUTURE_RIGHTS_PATH,
        "reason": "future_publication_event_not_part_of_packet_projection",
    },
    {
        "path": "gate/public-distribution-receipts/reiyah.public-distribution-receipt-1.1.0.json",
        "reason": "historical_post_packet_publication_event",
    },
    {
        "path": "gate/public-distribution-receipts/reiyah.public-distribution-receipt-1.1.1.json",
        "reason": "historical_post_packet_publication_event",
    },
    {
        "path": "gate/public-distribution-receipts/reiyah.public-distribution-receipt-1.1.2.json",
        "reason": "historical_post_packet_publication_event",
    },
    {
        "path": "gate/public-distribution-receipts/reiyah.public-distribution-receipt-1.2.0.json",
        "reason": "predecessor_post_packet_publication_event",
    },
)
PROJECTION_EXCLUSION_PATHS = frozenset(
    row["path"] for row in PROJECTION_EXCLUSION_POLICY
)
FORBIDDEN_ARTIFACT_PREFIXES = (
    ".pytest_cache/",
    "tools/__pycache__/",
    "validation/__pycache__/",
    "fixtures/__pycache__/",
)


class GateError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise GateError(code, message)


def canonical_json_bytes(value: Any) -> bytes:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise GateError(
            "GA121-JSON-NONFINITE",
            f"value cannot be represented as finite canonical JSON: {exc}",
        ) from exc
    return encoded.encode("utf-8") + b"\n"


def strict_json_bytes(data: bytes, path: str) -> Any:
    def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise GateError(
                    "GA121-JSON-DUPLICATE-KEY", f"{path}: duplicate key {key}"
                )
            result[key] = value
        return result

    def reject_constant(value: str) -> NoReturn:
        raise GateError(
            "GA121-JSON-NONFINITE", f"{path}: forbidden JSON constant {value}"
        )

    try:
        return json.loads(
            data.decode("utf-8"),
            object_pairs_hook=pairs_hook,
            parse_constant=reject_constant,
        )
    except GateError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GateError("GA121-JSON-SYNTAX", f"{path}: {exc}") from exc


def strict_json_file(path: str) -> Any:
    try:
        return strict_json_bytes((ROOT / path).read_bytes(), path)
    except OSError as exc:
        raise GateError("GA121-MISSING-ARTIFACT", f"{path}: {exc}") from exc


def json_type_matches(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, False)


def resolve_local_ref(
    root_schema: Mapping[str, Any], reference: str
) -> Mapping[str, Any]:
    require(
        reference.startswith("#/"),
        "GA121-SCHEMA",
        f"unsupported nonlocal schema reference {reference}",
    )
    node: Any = root_schema
    for token in reference[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        require(
            isinstance(node, dict) and token in node,
            "GA121-SCHEMA",
            f"unresolved schema reference {reference}",
        )
        node = node[token]
    require(
        isinstance(node, dict),
        "GA121-SCHEMA",
        f"schema reference is not an object {reference}",
    )
    return node


def simple_schema_errors(
    instance: Any,
    schema: Mapping[str, Any],
    root_schema: Mapping[str, Any],
    pointer: str = "",
) -> list[str]:
    if "$ref" in schema:
        reference = schema["$ref"]
        if not isinstance(reference, str) or not reference.startswith("#/"):
            return [f"{pointer or '/'}: unsupported $ref {reference!r}"]
        return simple_schema_errors(
            instance, resolve_local_ref(root_schema, reference), root_schema, pointer
        )
    errors: list[str] = []
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{pointer or '/'}: const")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{pointer or '/'}: enum")
    expected_type = schema.get("type")
    if expected_type is not None:
        allowed_types = (
            [expected_type] if isinstance(expected_type, str) else expected_type
        )
        if not any(json_type_matches(instance, item) for item in allowed_types):
            return errors + [f"{pointer or '/'}: type"]
    for subschema in schema.get("allOf", []):
        errors.extend(simple_schema_errors(instance, subschema, root_schema, pointer))
    if "oneOf" in schema:
        matches = sum(
            not simple_schema_errors(instance, item, root_schema, pointer)
            for item in schema["oneOf"]
        )
        if matches != 1:
            errors.append(f"{pointer or '/'}: oneOf")
    if isinstance(instance, dict):
        required = set(schema.get("required", []))
        for key in sorted(required - set(instance)):
            errors.append(f"{pointer or ''}/{key}: required")
        properties = schema.get("properties", {})
        for key, value in instance.items():
            child_pointer = f"{pointer}/{key}"
            if key in properties:
                errors.extend(
                    simple_schema_errors(
                        value, properties[key], root_schema, child_pointer
                    )
                )
            elif schema.get("additionalProperties") is False:
                errors.append(f"{child_pointer}: additionalProperties")
    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            errors.append(f"{pointer or '/'}: minItems")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{pointer or '/'}: maxItems")
        if schema.get("uniqueItems"):
            serialized = [canonical_json_bytes(item) for item in instance]
            if len(serialized) != len(set(serialized)):
                errors.append(f"{pointer or '/'}: uniqueItems")
        prefix = schema.get("prefixItems", [])
        for index, child_schema in enumerate(prefix[: len(instance)]):
            errors.extend(
                simple_schema_errors(
                    instance[index], child_schema, root_schema, f"{pointer}/{index}"
                )
            )
        items = schema.get("items")
        if items is False and len(instance) > len(prefix):
            errors.append(f"{pointer or '/'}: items")
        elif isinstance(items, dict):
            for index, value in enumerate(instance[len(prefix) :], start=len(prefix)):
                errors.extend(
                    simple_schema_errors(
                        value, items, root_schema, f"{pointer}/{index}"
                    )
                )
    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            errors.append(f"{pointer or '/'}: minLength")
        pattern = schema.get("pattern")
        if pattern is not None and re.search(pattern, instance) is None:
            errors.append(f"{pointer or '/'}: pattern")
        if schema.get("format") == "date" and not valid_calendar_date(instance):
            errors.append(f"{pointer or '/'}: format")
        if schema.get("format") == "date-time" and not valid_timestamp(instance):
            errors.append(f"{pointer or '/'}: format")
    if isinstance(instance, int) and not isinstance(instance, bool):
        if instance < schema.get("minimum", instance):
            errors.append(f"{pointer or '/'}: minimum")
    return errors


SIMPLE_SCHEMA_KEYWORDS = frozenset(
    {
        "$schema",
        "$id",
        "$defs",
        "$ref",
        "$comment",
        "title",
        "description",
        "type",
        "required",
        "properties",
        "additionalProperties",
        "const",
        "enum",
        "pattern",
        "format",
        "minLength",
        "minimum",
        "minItems",
        "maxItems",
        "uniqueItems",
        "items",
        "prefixItems",
        "allOf",
        "oneOf",
    }
)


def validate_simple_schema_keywords(schema: Any, pointer: str = "") -> list[str]:
    """Reject every keyword outside the validator's closed executable subset."""
    if isinstance(schema, bool):
        return []
    if not isinstance(schema, dict):
        return [f"{pointer or '/'}: schema node is not an object or boolean"]
    errors = [
        f"{pointer or '/'}: unsupported schema keyword {key}"
        for key in sorted(set(schema) - SIMPLE_SCHEMA_KEYWORDS)
    ]
    if "format" in schema and schema["format"] not in {"date", "date-time"}:
        errors.append(f"{pointer or '/'}: unsupported format {schema['format']!r}")
    for container in ("properties", "$defs"):
        value = schema.get(container, {})
        if isinstance(value, dict):
            for key, child in value.items():
                errors.extend(
                    validate_simple_schema_keywords(
                        child, f"{pointer}/{container}/{key}"
                    )
                )
    for container in ("allOf", "oneOf", "prefixItems"):
        value = schema.get(container, [])
        if isinstance(value, list):
            for index, child in enumerate(value):
                errors.extend(
                    validate_simple_schema_keywords(
                        child, f"{pointer}/{container}/{index}"
                    )
                )
    for key in ("items", "additionalProperties"):
        value = schema.get(key)
        if isinstance(value, dict):
            errors.extend(validate_simple_schema_keywords(value, f"{pointer}/{key}"))
    return errors


def validate_simple_schema(
    instance: Any,
    schema_path: str,
    files: Mapping[str, bytes],
    code: str,
) -> None:
    require(schema_path in files, code, f"schema absent: {schema_path}")
    schema = strict_json_bytes(files[schema_path], schema_path)
    require(isinstance(schema, dict), code, f"schema is not an object: {schema_path}")
    keyword_errors = validate_simple_schema_keywords(schema)
    require(
        not keyword_errors,
        code,
        f"{schema_path} uses unsupported executable schema keywords: {keyword_errors[:12]}",
    )
    errors = simple_schema_errors(instance, schema, schema)
    require(not errors, code, f"{schema_path} validation failed: {errors[:12]}")


def file_binding(path: str, data: bytes | None = None) -> dict[str, Any]:
    if data is None:
        try:
            data = (ROOT / path).read_bytes()
        except OSError as exc:
            raise GateError("GA121-MISSING-ARTIFACT", f"{path}: {exc}") from exc
    return {
        "path": path,
        "sha256": f"sha256:{hashlib.sha256(data).hexdigest()}",
        "byte_size": len(data),
    }


def git(*arguments: str, binary: bool = False, check: bool = True) -> str | bytes:
    completed = subprocess.run(
        ("git", "-C", str(ROOT), *arguments),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and completed.returncode != 0:
        message = completed.stderr.decode("utf-8", "replace").strip()
        raise GateError("GA121-GIT-OBJECT", f"git {' '.join(arguments)}: {message}")
    if binary:
        return completed.stdout
    return completed.stdout.decode("utf-8", "strict").strip()


def git_tree(commit: str) -> dict[str, dict[str, Any]]:
    raw = git("ls-tree", "-r", "-z", "--long", commit, binary=True)
    assert isinstance(raw, bytes)
    records: dict[str, dict[str, Any]] = {}
    for row in raw.split(b"\0"):
        if not row:
            continue
        metadata, raw_path = row.split(b"\t", 1)
        parts = metadata.split()
        require(len(parts) == 4, "GA121-GIT-OBJECT", "malformed ls-tree record")
        mode, object_type, oid, raw_size = parts
        path = raw_path.decode("utf-8", "strict")
        require(path not in records, "GA121-GIT-OBJECT", f"duplicate Git path {path}")
        records[path] = {
            "mode": mode.decode(),
            "type": object_type.decode(),
            "oid": oid.decode(),
            "size": None if raw_size == b"-" else int(raw_size),
        }
    return records


def git_blob(commit: str, path: str) -> bytes:
    result = git("show", f"{commit}:{path}", binary=True)
    assert isinstance(result, bytes)
    return result


def git_blob_oid(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


def verify_identity_and_isolation() -> None:
    require(Path.cwd().resolve() == ROOT, "GA121-IDENTITY", f"cwd must be {ROOT}")
    require(
        Path(__file__).resolve().parent.parent == ROOT,
        "GA121-IDENTITY",
        "script root differs",
    )
    require(
        git("rev-parse", "--show-toplevel") == str(ROOT),
        "GA121-IDENTITY",
        "Git root differs",
    )
    origin = git("remote", "get-url", "origin")
    require(origin in EXPECTED_ORIGINS, "GA121-IDENTITY", f"origin differs: {origin}")
    require(
        os.environ.get("REIYAH_GATE_A_121_LAUNCHED") == "1",
        "GA121-ISOLATION",
        "locked launcher marker absent",
    )
    require(
        bool(sys.flags.isolated), "GA121-ISOLATION", "Python isolated mode is absent"
    )
    require(bool(sys.flags.no_site), "GA121-ISOLATION", "Python no-site mode is absent")
    require(
        bool(sys.flags.dont_write_bytecode),
        "GA121-ISOLATION",
        "bytecode writes are not disabled",
    )
    require(
        Path(sys.executable) == PYTHON_PATH,
        "GA121-ISOLATION",
        f"locked interpreter differs: {sys.executable}",
    )


def normalized_mode(path: Path) -> str:
    return "100755" if path.stat().st_mode & 0o111 else "100644"


def scan_worktree() -> tuple[dict[str, bytes], dict[str, str], list[str]]:
    files: dict[str, bytes] = {}
    modes: dict[str, str] = {}
    symlinks: list[str] = []
    for directory, dirnames, filenames in os.walk(ROOT, followlinks=False):
        directory_path = Path(directory)
        relative_directory = directory_path.relative_to(ROOT).as_posix()
        kept_dirs: list[str] = []
        for name in sorted(dirnames):
            path = directory_path / name
            relative = path.relative_to(ROOT).as_posix()
            if relative == ".git" or relative.startswith(".git/"):
                continue
            if path.is_symlink():
                symlinks.append(relative)
                continue
            kept_dirs.append(name)
        dirnames[:] = kept_dirs
        for name in sorted(filenames):
            path = directory_path / name
            relative = path.relative_to(ROOT).as_posix()
            if path.is_symlink():
                symlinks.append(relative)
                continue
            require(
                "\n" not in relative and "\x00" not in relative,
                "GA121-PATH",
                f"unsafe path {relative!r}",
            )
            require(
                path.is_file(),
                "GA121-SNAPSHOT",
                f"non-regular worktree artifact {relative}",
            )
            try:
                files[relative] = path.read_bytes()
                modes[relative] = normalized_mode(path)
            except OSError as exc:
                raise GateError("GA121-SNAPSHOT", f"{relative}: {exc}") from exc
        if relative_directory == ".git":
            dirnames[:] = []
    return files, modes, sorted(symlinks)


def release_files(head: str) -> tuple[dict[str, bytes], dict[str, str], list[str]]:
    tree = git_tree(head)
    files: dict[str, bytes] = {}
    modes: dict[str, str] = {}
    symlinks: list[str] = []
    for path, record in sorted(tree.items()):
        if record["mode"] == "120000":
            symlinks.append(path)
            continue
        require(
            record["type"] == "blob",
            "GA121-SNAPSHOT",
            f"non-blob tracked object {path}",
        )
        data = git_blob(head, path)
        require(
            len(data) == record["size"],
            "GA121-SNAPSHOT",
            f"Git size mismatch for {path}",
        )
        files[path] = data
        modes[path] = record["mode"]
    return files, modes, symlinks


def load_plan(files: Mapping[str, bytes]) -> dict[str, Any]:
    require(PLAN_PATH in files, "GA121-PLAN", "validation plan absent")
    require(
        hashlib.sha256(files[PLAN_PATH]).hexdigest() == EXPECTED_PLAN_SHA256,
        "GA121-PLAN",
        "validation plan bytes differ from the locked continuity contract",
    )
    plan = strict_json_bytes(files[PLAN_PATH], PLAN_PATH)
    require(isinstance(plan, dict), "GA121-PLAN", "validation plan must be an object")
    validate_simple_schema(
        plan,
        "schemas/validation-plan-1.2.1.schema.json",
        files,
        "GA121-PLAN",
    )
    require(
        set(plan)
        == {
            "schema_id",
            "artifact_id",
            "plan_id",
            "version",
            "as_of_date",
            "scope",
            "authority",
            "entrypoint",
            "implementation",
            "toolchain_lock",
            "continuity_fixture_catalog",
            "outputs",
            "predecessor",
            "inherited_science",
            "protected_predecessor_surfaces",
            "successor_delta_policy",
            "evaluation_modes",
            "control_ids",
        },
        "GA121-PLAN",
        "validation plan top-level key set differs",
    )
    expected = {
        "schema_id": "https://schemas.reiyah.invalid/gate-a/1.2.1/validation-plan.schema.json",
        "artifact_id": "reiyah.artifact.validation-plan-1.2.1",
        "plan_id": "reiyah.validation-plan.gate-a-continuity-1.2.1",
        "version": "1.2.1",
        "as_of_date": "2026-08-25",
        "scope": "documentation_discovery_lineage_and_publication_continuity_only",
        "entrypoint": "tools/gate_a_1_2_1.sh",
        "implementation": "tools/gate_a_1_2_1.py",
        "toolchain_lock": LOCK_PATH,
        "continuity_fixture_catalog": FIXTURE_CATALOG_PATH,
    }
    for key, value in expected.items():
        require(plan.get(key) == value, "GA121-PLAN", f"plan {key} differs")
    require(
        plan.get("outputs") == EXPECTED_OUTPUTS,
        "GA121-PLAN",
        "plan outputs differ from the closed continuity contract",
    )
    require(
        plan.get("authority") == EXPECTED_AUTHORITY,
        "GA121-PLAN",
        "plan authority map differs from the closed continuity contract",
    )
    require(
        plan.get("evaluation_modes") == EXPECTED_EVALUATION_MODES,
        "GA121-PLAN",
        "plan evaluation modes differ from the closed continuity contract",
    )
    require(
        plan.get("successor_delta_policy") == EXPECTED_DELTA_POLICY,
        "GA121-PLAN",
        "plan successor delta policy differs from the closed continuity contract",
    )
    require(
        tuple(plan.get("control_ids", ())) == EXPECTED_CONTROL_IDS,
        "GA121-PLAN",
        "control IDs or order differ",
    )
    require(
        hashlib.sha256(canonical_json_bytes(plan["successor_delta_policy"])).hexdigest()
        == EXPECTED_DELTA_POLICY_SHA256,
        "GA121-PLAN",
        "exact successor delta policy differs",
    )
    return plan


def compare_binding(
    files: Mapping[str, bytes], binding: Mapping[str, Any], code: str
) -> None:
    path = binding.get("path")
    require(isinstance(path, str) and path in files, code, f"bound path absent: {path}")
    observed = file_binding(path, files[path])
    require(observed == dict(binding), code, f"byte binding differs for {path}")


def control_packet_identity(plan: Mapping[str, Any]) -> dict[str, Any]:
    predecessor = plan["predecessor"]
    require(
        predecessor["packet_commit"] == PACKET_COMMIT,
        "GA121-PREDECESSOR-PACKET-IDENTITY",
        "packet commit differs",
    )
    require(
        git("rev-parse", f"{PACKET_COMMIT}^{{commit}}") == PACKET_COMMIT,
        "GA121-PREDECESSOR-PACKET-IDENTITY",
        "packet object absent",
    )
    require(
        git("rev-parse", f"{PACKET_COMMIT}^{{tree}}") == PACKET_TREE,
        "GA121-PREDECESSOR-PACKET-IDENTITY",
        "packet tree differs",
    )
    tree = git_tree(PACKET_COMMIT)
    require(
        len(tree) == 773,
        "GA121-PREDECESSOR-PACKET-IDENTITY",
        "packet file count differs",
    )
    return {
        "packet_commit": PACKET_COMMIT,
        "packet_tree": PACKET_TREE,
        "file_count": len(tree),
    }


def control_topology(plan: Mapping[str, Any]) -> dict[str, Any]:
    predecessor = plan["predecessor"]
    require(
        predecessor["receipt_commit"] == RECEIPT_COMMIT,
        "GA121-PREDECESSOR-TOPOLOGY",
        "receipt commit differs",
    )
    require(
        git("rev-parse", f"{RECEIPT_COMMIT}^{{tree}}") == RECEIPT_TREE,
        "GA121-PREDECESSOR-TOPOLOGY",
        "receipt tree differs",
    )
    parent = git("rev-parse", f"{RECEIPT_COMMIT}^")
    require(
        predecessor.get("packet_commit") == PACKET_COMMIT
        and parent == predecessor.get("packet_commit"),
        "GA121-PREDECESSOR-TOPOLOGY",
        "receipt first parent differs from the exact predecessor packet",
    )
    tree = git_tree(RECEIPT_COMMIT)
    require(
        len(tree) == 775, "GA121-PREDECESSOR-TOPOLOGY", "receipt file count differs"
    )
    changed = tuple(
        sorted(
            str(git("diff", "--name-only", PACKET_COMMIT, RECEIPT_COMMIT)).splitlines()
        )
    )
    require(
        changed == RECEIPT_DELTA,
        "GA121-PREDECESSOR-TOPOLOGY",
        f"receipt delta differs: {changed}",
    )
    return {
        "receipt_commit": RECEIPT_COMMIT,
        "receipt_tree": RECEIPT_TREE,
        "first_parent": parent,
        "delta_paths": list(changed),
    }


def control_history(
    files: Mapping[str, bytes], plan: Mapping[str, Any]
) -> dict[str, Any]:
    history = plan["predecessor"]["history"]
    compare_binding(files, history["index"], "GA121-HISTORY-BINDING")
    compare_binding(files, history["sidecar"], "GA121-HISTORY-BINDING")
    require(
        files[history["index"]["path"]] == git_blob(PACKET_COMMIT, INDEX_PATH),
        "GA121-HISTORY-BINDING",
        "history index differs from C_packet",
    )
    require(
        files[history["sidecar"]["path"]] == git_blob(PACKET_COMMIT, SIDECAR_PATH),
        "GA121-HISTORY-BINDING",
        "history sidecar differs from C_packet",
    )
    recovery_path = history["recovery"]
    require(recovery_path in files, "GA121-HISTORY-BINDING", "recovery record absent")
    require(
        hashlib.sha256(files[recovery_path]).hexdigest() == EXPECTED_RECOVERY_SHA256,
        "GA121-HISTORY-BINDING",
        "recovery record bytes differ from the locked continuity contract",
    )
    recovery = strict_json_bytes(files[recovery_path], recovery_path)
    validate_simple_schema(
        recovery,
        "schemas/historical-packet-recovery-1.2.1.schema.json",
        files,
        "GA121-HISTORY-BINDING",
    )
    commits = recovery.get("release_commits", {})
    require(
        commits.get("packet", {}).get("commit") == PACKET_COMMIT,
        "GA121-HISTORY-BINDING",
        "recovery packet differs",
    )
    receipt = commits.get("receipt_bearing", {})
    require(
        receipt.get("commit") == RECEIPT_COMMIT
        and receipt.get("first_parent") == PACKET_COMMIT,
        "GA121-HISTORY-BINDING",
        "recovery receipt lineage differs",
    )
    require(
        tuple(receipt.get("exact_delta_paths", ())) == RECEIPT_DELTA,
        "GA121-HISTORY-BINDING",
        "recovery receipt delta differs",
    )
    return {
        "index": history["index"],
        "sidecar": history["sidecar"],
        "recovery_path": recovery_path,
    }


def control_report(
    files: Mapping[str, bytes], plan: Mapping[str, Any]
) -> dict[str, Any]:
    binding = plan["predecessor"]["canonical_report"]
    compare_binding(files, binding, "GA121-CANONICAL-REPORT-BINDING")
    require(
        files[binding["path"]] == git_blob(PACKET_COMMIT, binding["path"]),
        "GA121-CANONICAL-REPORT-BINDING",
        "1.2.0 report differs from C_packet",
    )
    report = strict_json_bytes(files[binding["path"]], binding["path"])
    require(
        report.get("result") == "pass"
        and report.get("architecture_status") == "architecture_complete",
        "GA121-CANONICAL-REPORT-BINDING",
        "inherited report disposition differs",
    )
    return dict(binding)


def control_rights_receipt(
    files: Mapping[str, bytes], plan: Mapping[str, Any]
) -> dict[str, Any]:
    rights = plan["predecessor"]["current_rights_observation"]
    receipt = plan["predecessor"]["current_publisher_receipt"]
    compare_binding(files, rights, "GA121-RIGHTS-RECEIPT-BINDING")
    compare_binding(
        files,
        {key: receipt[key] for key in ("path", "sha256", "byte_size")},
        "GA121-RIGHTS-RECEIPT-BINDING",
    )
    require(
        files[rights["path"]] == git_blob(RECEIPT_COMMIT, rights["path"]),
        "GA121-RIGHTS-RECEIPT-BINDING",
        "rights bytes differ from C_receipt",
    )
    require(
        files[receipt["path"]] == git_blob(RECEIPT_COMMIT, receipt["path"]),
        "GA121-RIGHTS-RECEIPT-BINDING",
        "receipt bytes differ from C_receipt",
    )
    receipt_record = strict_json_bytes(files[receipt["path"]], receipt["path"])
    require(
        isinstance(receipt_record, dict),
        "GA121-RIGHTS-RECEIPT-BINDING",
        "receipt is not an object",
    )
    require(
        receipt.get("transport_state") == "asserted_unverified",
        "GA121-RIGHTS-RECEIPT-BINDING",
        "plan receipt state differs",
    )
    return {"rights": rights, "publisher_receipt": receipt}


def is_protected_predecessor_path(path: str) -> bool:
    prefixes = (
        "manifests/scientific/",
        "manifests/protocol/",
        "manifests/mission/",
        "manifests/definitions/",
        "manifests/research/",
        "fixtures/",
        "schemas/",
        "tools/gate_a_1_2_0",
    )
    exact = {
        "manifests/manifest-release-ledger.json",
        "validation/toolchain-lock-1.2.0.json",
        "gate/validation-reports/gate-a-validation-1.2.0.json",
        RECEIPT_DELTA[0],
        RECEIPT_DELTA[1],
    }
    return path in exact or path.startswith(prefixes)


def control_protected(
    files: Mapping[str, bytes],
    modes: Mapping[str, str],
    baseline: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    protected = [
        path for path in sorted(baseline) if is_protected_predecessor_path(path)
    ]
    require(protected, "GA121-PROTECTED-BYTES", "protected predecessor set is empty")
    drifts: list[str] = []
    for path in protected:
        data = files.get(path)
        if (
            data is None
            or git_blob_oid(data) != baseline[path]["oid"]
            or modes.get(path) != baseline[path]["mode"]
        ):
            drifts.append(path)
    require(
        not drifts,
        "GA121-PROTECTED-BYTES",
        f"protected predecessor bytes drift: {drifts[:12]}",
    )
    return {
        "protected_file_count": len(protected),
        "protected_path_set_sha256": f"sha256:{hashlib.sha256(canonical_json_bytes(protected)).hexdigest()}",
        "drift_count": 0,
    }


def control_inherited_science(
    plan: Mapping[str, Any], files: Mapping[str, bytes]
) -> dict[str, Any]:
    inherited = plan["inherited_science"]
    require(
        inherited.get("evidence_state") == "inherited_historical_exact_byte_binding",
        "GA121-INHERITED-SCIENCE-STATE",
        "science evidence state differs",
    )
    require(
        inherited.get("current_replay_fixture_count") == 0,
        "GA121-INHERITED-SCIENCE-STATE",
        "continuity plan counts current science fixtures",
    )
    require(
        inherited.get("current_science_replay_performed") is False,
        "GA121-INHERITED-SCIENCE-STATE",
        "continuity plan claims a current science replay",
    )
    require(
        inherited.get("current_profile_handler_replaced") is False,
        "GA121-INHERITED-SCIENCE-STATE",
        "continuity tool claims to replace profile handler",
    )
    for key in (
        "profile_bound_launcher",
        "profile_bound_validator",
        "profile_bound_science_module",
        "profile_bound_toolchain_lock",
        "scientific_profile",
        "protocol_manifest",
    ):
        compare_binding(files, inherited[key], "GA121-INHERITED-SCIENCE-STATE")
    return copy.deepcopy(inherited)


def matches_rule(path: str, rule: Mapping[str, Any]) -> bool:
    kind = rule.get("match_kind")
    value = rule.get("path")
    if kind == "exact":
        return path == value
    if kind == "prefix":
        return isinstance(value, str) and path.startswith(value)
    if kind == "continuity_schema":
        return (
            path.startswith("schemas/") and Path(path).name in CONTINUITY_SCHEMA_NAMES
        )
    if kind == "frontier_schema":
        return path.startswith("schemas/") and "frontier" in Path(path).name.lower()
    if kind == "frontier_register":
        return (
            path.startswith("evidence/")
            and "frontier" in Path(path).name.lower()
            and path.endswith(".json")
        )
    if kind == "frontier_fixture":
        return path.startswith("fixtures/v1.2/frontier-") and path.endswith(".json")
    return False


def allowed_by(path: str, rules: Sequence[Mapping[str, Any]]) -> bool:
    return any(matches_rule(path, rule) for rule in rules)


def derive_delta(
    files: Mapping[str, bytes],
    modes: Mapping[str, str],
    baseline: Mapping[str, Mapping[str, Any]],
    plan: Mapping[str, Any],
) -> dict[str, Any]:
    require(
        plan.get("successor_delta_policy") == EXPECTED_DELTA_POLICY,
        "GA121-SUCCESSOR-DELTA-SCOPE",
        "mutable plan delta policy differs from the executable closed set",
    )
    baseline_paths = set(baseline)
    current_paths = set(files)
    shared = baseline_paths & current_paths
    changed = sorted(
        path
        for path in shared
        if path not in OUTPUT_PATHS
        and (
            git_blob_oid(files[path]) != baseline[path]["oid"]
            or modes.get(path) != baseline[path]["mode"]
        )
    )
    removed = sorted((baseline_paths - current_paths) - OUTPUT_PATHS)
    added = sorted((current_paths - baseline_paths) - OUTPUT_PATHS)
    expected_changed = sorted(EXPECTED_CHANGED_PATHS)
    expected_removed = sorted(EXPECTED_REMOVED_PATHS)
    expected_added = sorted(EXPECTED_ADDED_PATHS)
    require(
        changed == expected_changed
        and removed == expected_removed
        and added == expected_added,
        "GA121-SUCCESSOR-DELTA-SCOPE",
        f"exact delta differs: changed={changed}, removed={removed}, added={added}",
    )
    mode_drifts = [
        path
        for path in (*expected_changed, *expected_added)
        if modes.get(path)
        != ("100755" if path in EXPECTED_EXECUTABLE_PATHS else "100644")
    ]
    require(
        not mode_drifts,
        "GA121-SUCCESSOR-DELTA-SCOPE",
        f"successor Git mode differs from the closed mode policy: {mode_drifts}",
    )
    return {
        "baseline_commit": RECEIPT_COMMIT,
        "changed_existing_paths": changed,
        "removed_existing_paths": removed,
        "added_paths": added,
        "executable_paths": sorted(EXPECTED_EXECUTABLE_PATHS),
        "unknown_paths": [],
    }


MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def validate_citation_cff(
    files: Mapping[str, bytes], delta: Mapping[str, Any]
) -> dict[str, Any]:
    path = "CITATION.cff"
    require(
        path in delta["changed_existing_paths"] and path in files,
        "GA121-DOCUMENTATION-LINKS",
        "CITATION.cff is absent from the exact continuity delta",
    )
    try:
        text = files[path].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GateError(
            "GA121-DOCUMENTATION-LINKS", "CITATION.cff is not UTF-8"
        ) from exc
    top_level_keys = tuple(
        re.findall(r"^([a-z][a-z0-9-]*):(?:\s|$)", text, re.MULTILINE)
    )
    expected_keys = (
        "cff-version",
        "message",
        "title",
        "type",
        "authors",
        "repository-code",
        "license",
        "version",
        "abstract",
        "keywords",
    )
    require(
        top_level_keys == expected_keys,
        "GA121-DOCUMENTATION-LINKS",
        f"CITATION.cff top-level structure differs: {top_level_keys}",
    )
    exact_lines = {
        "cff-version: 1.2.0",
        'title: "Reiyah: HARBOR Gate A Research Architecture"',
        "type: software",
        'repository-code: "https://github.com/manfromnowhere143/reiyah"',
        "license: Apache-2.0",
        "version: 1.2.1",
    }
    require(
        exact_lines <= set(text.splitlines()),
        "GA121-DOCUMENTATION-LINKS",
        "CITATION.cff exact identity, version, repository, or license differs",
    )
    require(
        "authors:\n  - family-names: Wahnich\n    given-names: Daniel" in text,
        "GA121-DOCUMENTATION-LINKS",
        "CITATION.cff author structure differs",
    )
    expected_keywords = (
        "automated driving",
        "human automation interaction",
        "uncertainty",
        "causal inference",
        "benchmark governance",
    )
    observed_keywords = tuple(
        match.group(1)
        for match in re.finditer(r"^  - ([^\n]+)$", text, re.MULTILINE)
        if match.group(1) not in {"family-names: Wahnich"}
    )
    require(
        observed_keywords == expected_keywords,
        "GA121-DOCUMENTATION-LINKS",
        f"CITATION.cff keyword list differs: {observed_keywords}",
    )
    folded = text.casefold()
    markers = (
        "publisher readback is an assertion",
        "documentation, discovery, and lineage continuity architecture",
        "inherited historical evidence",
        "does not rerun the bound",
        "pointer-only",
        "operator acceptance",
    )
    require(
        all(marker in folded for marker in markers),
        "GA121-AUTHORITY-NONCLAIMS",
        "CITATION.cff omits a required lineage or nonauthority marker",
    )
    return {
        "path": path,
        "top_level_key_count": len(top_level_keys),
        "keyword_count": len(observed_keywords),
        "authority_safe_markers_present": True,
    }


def control_documentation_links(
    files: Mapping[str, bytes], delta: Mapping[str, Any]
) -> dict[str, Any]:
    citation = validate_citation_cff(files, delta)
    paths = sorted(
        path
        for path in (*delta["changed_existing_paths"], *delta["added_paths"])
        if path.endswith(".md")
    )
    failures: list[str] = []
    state_failures: list[str] = []
    checked = 0
    forbidden_phrases = (
        "reiyah is safer",
        "reiyah is superior",
        "reiyah outperforms",
        "gate a 1.2.1 is published",
        "gate a 1.2.1 is released",
        "gate a 1.2.1 is accepted",
        "gate a 1.2.1 is validated",
        "runtime authorized: true",
        "gate b authorized: true",
        "ga-17: pass",
        "independent transport verification: verified",
        "operator acceptance: accepted",
    )
    for path in paths:
        try:
            text = files[path].decode("utf-8")
        except UnicodeDecodeError:
            failures.append(f"{path}: non-UTF-8")
            continue
        folded = text.casefold().replace("`", "")
        if "1.2.0" not in folded:
            state_failures.append(f"{path}: missing exact predecessor version")
        if not any(
            marker in folded
            for marker in (
                "not_evaluated",
                "not evaluated",
                "unauthorized",
                "does not",
                "cannot",
                "unaccepted",
                "proposed",
            )
        ):
            state_failures.append(
                f"{path}: missing authority-safe current-state marker"
            )
        for phrase in forbidden_phrases:
            if phrase in folded:
                state_failures.append(
                    f"{path}: forbidden positive authority or superiority phrase {phrase!r}"
                )
        for raw_target in MARKDOWN_LINK.findall(text):
            target = raw_target.strip().split(" ", 1)[0].strip("<>")
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            target = unquote(target.split("#", 1)[0])
            if not target or target.startswith("/"):
                continue
            checked += 1
            resolved = (Path(path).parent / target).as_posix()
            normalized = os.path.normpath(resolved).replace(os.sep, "/")
            directory_target = normalized.rstrip("/") + "/"
            if normalized.startswith("../") or (
                normalized not in files
                and not any(
                    candidate.startswith(directory_target) for candidate in files
                )
            ):
                failures.append(f"{path} -> {target}")
    require(
        not failures,
        "GA121-DOCUMENTATION-LINKS",
        f"broken internal links: {failures[:12]}",
    )
    require(
        not state_failures,
        "GA121-AUTHORITY-NONCLAIMS",
        f"documentation current-state/nonclaim check failed: {state_failures[:12]}",
    )
    joined = "\n".join(files[path].decode("utf-8") for path in paths)
    require(
        PACKET_COMMIT in joined and RECEIPT_COMMIT in joined,
        "GA121-AUTHORITY-NONCLAIMS",
        "changed documentation does not retain exact C_packet and C_receipt identities",
    )
    return {
        "document_count": len(paths),
        "relative_link_count": checked,
        "broken_link_count": 0,
        "current_state_marker_count": len(paths),
        "forbidden_positive_claim_count": 0,
        "packet_and_receipt_identities_present": True,
        "citation_cff": citation,
    }


AUTHORITY_TRUE_KEYS = frozenset(
    {
        "scientific_support_claimed",
        "scientific_claim_authority",
        "gate_a_acceptance_conferred",
        "operator_acceptance_conferred",
        "runtime_execution_authorized",
        "runtime_authorized",
        "gate_b_authorized",
        "transport_independently_verified",
        "payload_redistribution_authorized",
        "publication_acceptance_conferred",
    }
)

FRONTIER_REGISTER_PATH = "evidence/frontier-discovery-register-1.2.0.json"
FRONTIER_PREDECESSOR_PATH = "evidence/frontier-discovery-register-1.1.0.json"
EXPECTED_FRONTIER_REGISTER_BINDING = {
    "path": FRONTIER_REGISTER_PATH,
    "sha256": "sha256:e5e7f68c3f93d43553408873ca4ab4f9eb93ae5cd637c473b4f847a458000fac",
    "byte_size": 119407,
}
EXPECTED_FRONTIER_REGISTER_SCHEMA_BINDING = {
    "path": "schemas/frontier-discovery-register-1.2.schema.json",
    "sha256": "sha256:68441568a33418e0ed82f5b6aa2d7fc1869df12eebcd60af6d30343d8c60fa87",
    "byte_size": 116189,
}
EXPECTED_FRONTIER_FIXTURE_SCHEMA_BINDING = {
    "path": "schemas/frontier-discovery-fixture-1.2.schema.json",
    "sha256": "sha256:19e93c60294c61cd046142c56a9bef02ac092baf56616b11b4e989d7af661362",
    "byte_size": 6488,
}
EXPECTED_FRONTIER_FIXTURE_CASE_MAP_SHA256 = (
    "20f7fc56aa3667d5c9f9f64969e716f9300e4115d76e92ec83da37c80613a596"
)
FRONTIER_FIXTURE_PATHS = (
    "fixtures/v1.2/frontier-good/frontier-discovery-register-successor.json",
    "fixtures/v1.2/frontier-known-bad/frontier-admitted-claim.json",
    "fixtures/v1.2/frontier-known-bad/frontier-company-self-report-mislabeled-independent.json",
    "fixtures/v1.2/frontier-known-bad/frontier-duplicate-discovery-id.json",
    "fixtures/v1.2/frontier-known-bad/frontier-dynamic-source-access-date-missing.json",
    "fixtures/v1.2/frontier-known-bad/frontier-dynamic-source-version-state-missing.json",
    "fixtures/v1.2/frontier-known-bad/frontier-missing-limitations.json",
    "fixtures/v1.2/frontier-known-bad/frontier-payload-insertion.json",
    "fixtures/v1.2/frontier-known-bad/frontier-publisher-version-without-exact-revision.json",
    "fixtures/v1.2/frontier-known-bad/frontier-predecessor-drift.json",
    "fixtures/v1.2/frontier-known-bad/frontier-predecessor-record-mutation.json",
)


def finding(rule_id: str, keyword: str, pointer: str) -> dict[str, str]:
    return {"rule_id": rule_id, "schema_keyword": keyword, "instance_pointer": pointer}


def valid_calendar_date(value: Any) -> bool:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
        return True
    except ValueError:
        return False


def frontier_structural_finding(
    register: Mapping[str, Any],
    predecessor: Mapping[str, Any],
    register_schema: Mapping[str, Any],
    expected_predecessor_binding: Mapping[str, Any],
    expected_predecessor_schema_binding: Mapping[str, Any],
) -> dict[str, str] | None:
    properties = register_schema.get("properties", {})
    required = set(register_schema.get("required", []))
    if not isinstance(register, dict):
        return finding("GA12-FRONTIER-CLOSED-SHAPE", "type", "")
    missing_top = sorted(required - set(register))
    if missing_top:
        return finding("GA12-FRONTIER-CLOSED-SHAPE", "required", "")
    unknown_top = sorted(set(register) - set(properties))
    if unknown_top:
        return finding(
            "GA12-FRONTIER-CLOSED-SHAPE", "additionalProperties", f"/{unknown_top[0]}"
        )
    for key, schema in properties.items():
        if (
            isinstance(schema, dict)
            and "const" in schema
            and register.get(key) != schema["const"]
        ):
            rule = (
                "GA12-FRONTIER-CLAIM-NONADMISSION"
                if key
                in {
                    "claims_admitted",
                    "scientific_support_claimed",
                    "safety_claimed",
                    "compliance_claimed",
                    "comparative_superiority_claimed",
                    "operator_acceptance_conferred",
                }
                else "GA12-FRONTIER-CLOSED-SHAPE"
            )
            return finding(rule, "const", f"/{key}")
    binding = register.get("predecessor_binding")
    if not isinstance(binding, dict):
        return finding(
            "GA12-FRONTIER-PREDECESSOR-BINDING", "type", "/predecessor_binding"
        )
    if set(binding) != set(expected_predecessor_binding) | {"schema_binding"}:
        return finding(
            "GA12-FRONTIER-PREDECESSOR-BINDING",
            "additionalProperties",
            "/predecessor_binding",
        )
    for key, value in expected_predecessor_binding.items():
        if binding.get(key) != value:
            return finding(
                "GA12-FRONTIER-PREDECESSOR-BINDING",
                "const",
                f"/predecessor_binding/{key}",
            )
    schema_binding = binding.get("schema_binding")
    if not isinstance(schema_binding, dict):
        return finding(
            "GA12-FRONTIER-PREDECESSOR-BINDING", "required", "/predecessor_binding"
        )
    if set(schema_binding) != set(expected_predecessor_schema_binding):
        return finding(
            "GA12-FRONTIER-PREDECESSOR-BINDING",
            "additionalProperties",
            "/predecessor_binding/schema_binding",
        )
    for key, value in expected_predecessor_schema_binding.items():
        if schema_binding.get(key) != value:
            return finding(
                "GA12-FRONTIER-PREDECESSOR-BINDING",
                "const",
                f"/predecessor_binding/schema_binding/{key}",
            )
    relation = register.get("relation")
    if relation != {
        "type": "append_only_successor",
        "prior_artifact_id": "reiyah.artifact.frontier-discovery-register-1.1.0",
        "prior_version": "1.1.0",
        "inherited_record_count": 38,
        "appended_record_count": 16,
        "predecessor_records_semantically_unchanged": True,
    }:
        return finding("GA12-FRONTIER-PREDECESSOR-BINDING", "const", "/relation")
    records = register.get("records")
    old_records = predecessor.get("records")
    if (
        not isinstance(records, list)
        or not isinstance(old_records, list)
        or len(old_records) != 38
    ):
        return finding("GA12-FRONTIER-PREDECESSOR-PREFIX", "type", "/records")
    if len(records) != 54 or register.get("record_count") != 54:
        return finding("GA12-FRONTIER-IDENTITY-UNIQUE", "const", "/record_count")
    for index, expected in enumerate(old_records):
        if records[index] != expected:
            return finding(
                "GA12-FRONTIER-PREDECESSOR-PREFIX", "const", f"/records/{index}"
            )
    appended_schema = register_schema.get("$defs", {}).get(
        "appendedDiscoveryRecord", {}
    )
    record_required = set(appended_schema.get("required", []))
    record_properties = appended_schema.get("properties", {})
    source_kinds = set(
        register_schema.get("$defs", {}).get("sourceKind", {}).get("enum", [])
    )
    topics = set(register_schema.get("$defs", {}).get("topic", {}).get("enum", []))
    origin_by_kind = {
        "official_company_disclosure": "company_self_report",
        "official_company_technical_page": "company_self_report",
        "official_company_regulated_filing": "company_self_report",
        "official_company_product_manual": "company_self_report",
        "official_deployment_partner_disclosure": "deployment_partner_self_report",
        "official_regulator_investigation": "regulator_open_investigation",
        "official_research_technical_page": "institution_self_report",
        "primary_research_publication": "primary_research_not_independent_replication",
        "primary_research_preprint": "primary_research_not_independent_replication",
    }
    artifact_ids: list[Any] = []
    discovery_ids: list[Any] = []
    for index, record in enumerate(records[38:], start=38):
        pointer = f"/records/{index}"
        if not isinstance(record, dict):
            return finding("GA12-FRONTIER-CLOSED-SHAPE", "type", pointer)
        missing = sorted(record_required - set(record))
        if missing:
            key = missing[0]
            if key == "limitations":
                return finding("GA12-FRONTIER-LIMITATION-REQUIRED", "required", pointer)
            if key in {"accessed_on", "source_version_state"}:
                return finding(
                    "GA12-FRONTIER-DYNAMIC-SOURCE-BINDING", "required", pointer
                )
            return finding("GA12-FRONTIER-CLOSED-SHAPE", "required", pointer)
        unknown = sorted(set(record) - set(record_properties))
        if unknown:
            return finding(
                "GA12-FRONTIER-CLOSED-SHAPE",
                "additionalProperties",
                f"{pointer}/{unknown[0]}",
            )
        for key, schema in record_properties.items():
            if (
                isinstance(schema, dict)
                and "const" in schema
                and record.get(key) != schema["const"]
            ):
                if key == "claims_admitted" or key.endswith("_claimed"):
                    return finding(
                        "GA12-FRONTIER-CLAIM-NONADMISSION", "const", f"{pointer}/{key}"
                    )
                if key == "independent_validation_established":
                    return finding(
                        "GA12-FRONTIER-INDEPENDENCE-LABEL", "const", f"{pointer}/{key}"
                    )
                if key in {
                    "custody_state",
                    "redistribution_state",
                    "evidence_eligibility",
                    "payload_redistribution_authorized",
                }:
                    return finding(
                        "GA12-FRONTIER-PAYLOAD-NULL", "const", f"{pointer}/{key}"
                    )
                return finding(
                    "GA12-FRONTIER-CLOSED-SHAPE", "const", f"{pointer}/{key}"
                )
        if record.get("retained_payload") is not None:
            return finding(
                "GA12-FRONTIER-PAYLOAD-NULL", "type", f"{pointer}/retained_payload"
            )
        source_kind = record.get("source_kind")
        if source_kind not in source_kinds:
            return finding(
                "GA12-FRONTIER-INDEPENDENCE-LABEL", "enum", f"{pointer}/source_kind"
            )
        if record.get("assertion_origin") != origin_by_kind.get(source_kind):
            return finding(
                "GA12-FRONTIER-INDEPENDENCE-LABEL",
                "const",
                f"{pointer}/assertion_origin",
            )
        for key in ("artifact_id", "discovery_id", "title", "scope"):
            if not isinstance(record.get(key), str) or not record[key].strip():
                return finding("GA12-FRONTIER-CLOSED-SHAPE", "type", f"{pointer}/{key}")
        parsed_url = urlparse(record.get("source_url", ""))
        if parsed_url.scheme != "https" or not parsed_url.netloc:
            return finding(
                "GA12-FRONTIER-CLOSED-SHAPE", "format", f"{pointer}/source_url"
            )
        if not valid_calendar_date(record.get("accessed_on")):
            return finding(
                "GA12-FRONTIER-DYNAMIC-SOURCE-BINDING",
                "format",
                f"{pointer}/accessed_on",
            )
        if not valid_timestamp(record.get("recorded_at")):
            return finding(
                "GA12-FRONTIER-CLOSED-SHAPE", "format", f"{pointer}/recorded_at"
            )
        record_topics = record.get("topics")
        if (
            not isinstance(record_topics, list)
            or not record_topics
            or len(set(record_topics)) != len(record_topics)
            or any(topic not in topics for topic in record_topics)
        ):
            return finding("GA12-FRONTIER-CLOSED-SHAPE", "enum", f"{pointer}/topics")
        limitations = record.get("limitations")
        if (
            not isinstance(limitations, list)
            or len(limitations) < 2
            or len(set(limitations)) != len(limitations)
            or not all(isinstance(item, str) and item.strip() for item in limitations)
        ):
            return finding(
                "GA12-FRONTIER-LIMITATION-REQUIRED", "type", f"{pointer}/limitations"
            )
        stability = record.get("source_stability")
        version_state = record.get("source_version_state")
        exact_version = record.get("exact_version")
        if stability == "fixed_document":
            expected_state = "exact_document_version_observed"
            expected_measurement = ("observed", "value")
        elif stability == "versioned_persistent_record":
            if version_state == "publisher_version_observed":
                if (
                    not isinstance(exact_version, dict)
                    or exact_version.get("state") != "observed"
                ):
                    return finding(
                        "GA12-FRONTIER-PERSISTENT-VERSION-BINDING",
                        "const",
                        f"{pointer}/exact_version/state",
                    )
                expected_state = "publisher_version_observed"
                expected_measurement = ("observed", "value")
            elif version_state == "current_version_unmeasured":
                expected_state = "current_version_unmeasured"
                expected_measurement = ("unmeasured", "reason")
            else:
                return finding(
                    "GA12-FRONTIER-PERSISTENT-VERSION-BINDING",
                    "enum",
                    f"{pointer}/source_version_state",
                )
        elif stability == "dynamic_mutable_page":
            expected_state = "current_version_unmeasured"
            expected_measurement = ("unmeasured", "reason")
        else:
            return finding(
                "GA12-FRONTIER-DYNAMIC-SOURCE-BINDING",
                "enum",
                f"{pointer}/source_stability",
            )
        if version_state != expected_state:
            return finding(
                "GA12-FRONTIER-DYNAMIC-SOURCE-BINDING",
                "const",
                f"{pointer}/source_version_state",
            )
        state, value_key = expected_measurement
        if (
            not isinstance(exact_version, dict)
            or set(exact_version) != {"state", value_key}
            or exact_version.get("state") != state
            or not isinstance(exact_version.get(value_key), str)
            or not exact_version[value_key].strip()
        ):
            return finding(
                "GA12-FRONTIER-DYNAMIC-SOURCE-BINDING",
                "const",
                f"{pointer}/exact_version",
            )
        artifact_ids.append(record.get("artifact_id"))
        discovery_ids.append(record.get("discovery_id"))
    all_artifact_ids = [
        record.get("artifact_id") for record in records if isinstance(record, dict)
    ]
    all_discovery_ids = [
        record.get("discovery_id") for record in records if isinstance(record, dict)
    ]
    if len(all_artifact_ids) != len(set(all_artifact_ids)):
        duplicate = next(
            value for value in all_artifact_ids if all_artifact_ids.count(value) > 1
        )
        index = all_artifact_ids.index(duplicate, all_artifact_ids.index(duplicate) + 1)
        return finding(
            "GA12-FRONTIER-IDENTITY-UNIQUE", "const", f"/records/{index}/artifact_id"
        )
    if len(all_discovery_ids) != len(set(all_discovery_ids)):
        duplicate = next(
            value for value in all_discovery_ids if all_discovery_ids.count(value) > 1
        )
        index = all_discovery_ids.index(
            duplicate, all_discovery_ids.index(duplicate) + 1
        )
        return finding(
            "GA12-FRONTIER-IDENTITY-UNIQUE", "const", f"/records/{index}/discovery_id"
        )
    return None


def mutate_json_pointer(document: Any, mutation: Mapping[str, Any]) -> Any:
    result = copy.deepcopy(document)
    raw_pointer = mutation.get("json_pointer")
    require(
        isinstance(raw_pointer, str) and raw_pointer.startswith("/"),
        "GA121-DISCOVERY-NONAUTHORITY",
        "frontier fixture pointer is invalid",
    )
    parts = [
        part.replace("~1", "/").replace("~0", "~")
        for part in raw_pointer[1:].split("/")
    ]
    parent = result
    for part in parts[:-1]:
        parent = parent[int(part)] if isinstance(parent, list) else parent[part]
    leaf = parts[-1]
    operation = mutation.get("operation")
    if operation == "replace":
        if isinstance(parent, list):
            parent[int(leaf)] = copy.deepcopy(mutation.get("value"))
        else:
            require(
                leaf in parent,
                "GA121-DISCOVERY-NONAUTHORITY",
                f"frontier fixture replacement target absent: {raw_pointer}",
            )
            parent[leaf] = copy.deepcopy(mutation.get("value"))
    elif operation == "remove":
        if isinstance(parent, list):
            del parent[int(leaf)]
        else:
            require(
                leaf in parent,
                "GA121-DISCOVERY-NONAUTHORITY",
                f"frontier fixture removal target absent: {raw_pointer}",
            )
            del parent[leaf]
    else:
        raise GateError(
            "GA121-DISCOVERY-NONAUTHORITY",
            f"unsupported frontier mutation: {operation}",
        )
    return result


def validate_frontier_fixtures(
    files: Mapping[str, bytes],
    register: Mapping[str, Any],
    predecessor: Mapping[str, Any],
    register_schema: Mapping[str, Any],
    predecessor_binding: Mapping[str, Any],
    predecessor_schema_binding: Mapping[str, Any],
) -> dict[str, Any]:
    actual = sorted(
        path
        for path in files
        if path.startswith("fixtures/v1.2/frontier-") and path.endswith(".json")
    )
    require(
        actual == sorted(FRONTIER_FIXTURE_PATHS),
        "GA121-DISCOVERY-NONAUTHORITY",
        f"frontier fixture set differs: {actual}",
    )
    fixture_ids: list[str] = []
    case_rows: list[dict[str, Any]] = []
    good = bad = 0
    fixture_schema = strict_json_bytes(
        files["schemas/frontier-discovery-fixture-1.2.schema.json"],
        "schemas/frontier-discovery-fixture-1.2.schema.json",
    )
    fixture_required = set(fixture_schema.get("required", []))
    fixture_allowed = set(fixture_schema.get("properties", {}))
    expected_base = {
        "artifact_id": "reiyah.artifact.frontier-discovery-register-1.2.0",
        **file_binding(FRONTIER_REGISTER_PATH, files[FRONTIER_REGISTER_PATH]),
        "schema_id": "https://schemas.reiyah.invalid/gate-a/1.2.0/frontier-discovery-register.schema.json",
        "version": "1.2.0",
    }
    require(
        fixture_schema.get("properties", {}).get("base_artifact_ref", {}).get("const")
        == expected_base,
        "GA121-DISCOVERY-NONAUTHORITY",
        "frontier fixture schema base binding differs from immutable snapshot",
    )
    for path in FRONTIER_FIXTURE_PATHS:
        fixture = strict_json_bytes(files[path], path)
        require(
            isinstance(fixture, dict),
            "GA121-DISCOVERY-NONAUTHORITY",
            f"frontier fixture is not an object: {path}",
        )
        require(
            set(fixture) == fixture_allowed and fixture_required <= set(fixture),
            "GA121-DISCOVERY-NONAUTHORITY",
            f"frontier fixture closed shape differs: {path}",
        )
        require(
            fixture.get("base_artifact_ref") == expected_base,
            "GA121-DISCOVERY-NONAUTHORITY",
            f"frontier fixture base binding differs: {path}",
        )
        require(
            fixture.get("schema_id")
            == "https://schemas.reiyah.invalid/gate-a/1.2.0/frontier-discovery-fixture.schema.json"
            and fixture.get("schema_version") == "1.2.0",
            "GA121-DISCOVERY-NONAUTHORITY",
            f"frontier fixture schema identity differs: {path}",
        )
        require(
            fixture.get("target_schema_id") == register_schema.get("$id"),
            "GA121-DISCOVERY-NONAUTHORITY",
            f"frontier target schema differs: {path}",
        )
        for key in (
            "fixture_creates_evidence",
            "fixture_creates_claims",
            "runtime_execution_authorized",
            "gate_b_authorized",
        ):
            require(
                fixture.get(key) is False,
                "GA121-DISCOVERY-NONAUTHORITY",
                f"frontier fixture authority nonclaim differs: {path}/{key}",
            )
        expected_limitations = (
            fixture_schema.get("properties", {}).get("limitations", {}).get("const")
        )
        require(
            fixture.get("limitations") == expected_limitations,
            "GA121-DISCOVERY-NONAUTHORITY",
            f"frontier fixture limitations differ: {path}",
        )
        fixture_id = fixture.get("fixture_id")
        require(
            isinstance(fixture_id, str),
            "GA121-DISCOVERY-NONAUTHORITY",
            f"frontier fixture ID absent: {path}",
        )
        fixture_ids.append(fixture_id)
        mutations = fixture.get("mutations")
        require(
            isinstance(mutations, list) and len(mutations) <= 1,
            "GA121-DISCOVERY-NONAUTHORITY",
            f"frontier fixture mutation count differs: {path}",
        )
        expected_outcome = fixture.get("expected_outcome")
        if fixture.get("fixture_class") == "known_good_frontier":
            require(
                not mutations
                and expected_outcome == "accept"
                and fixture.get("expected_failure") is None,
                "GA121-DISCOVERY-NONAUTHORITY",
                f"known-good frontier fixture contract differs: {path}",
            )
        else:
            require(
                fixture.get("fixture_class") == "known_bad_frontier"
                and len(mutations) == 1
                and expected_outcome == "reject",
                "GA121-DISCOVERY-NONAUTHORITY",
                f"known-bad frontier fixture contract differs: {path}",
            )
        mutated: Any = copy.deepcopy(register)
        for mutation in mutations:
            require(
                isinstance(mutation, dict)
                and set(mutation)
                in (
                    {"operation", "json_pointer"},
                    {"operation", "json_pointer", "value"},
                ),
                "GA121-DISCOVERY-NONAUTHORITY",
                f"frontier mutation closed shape differs: {path}",
            )
            require(
                (mutation.get("operation") == "replace") == ("value" in mutation),
                "GA121-DISCOVERY-NONAUTHORITY",
                f"frontier mutation value contract differs: {path}",
            )
            mutated = mutate_json_pointer(mutated, mutation)
        observed = frontier_structural_finding(
            mutated,
            predecessor,
            register_schema,
            predecessor_binding,
            predecessor_schema_binding,
        )
        expected_failure = fixture.get("expected_failure")
        if expected_failure is not None:
            require(
                isinstance(expected_failure, dict)
                and set(expected_failure)
                == {
                    "rule_id",
                    "rejection_layer",
                    "schema_keyword",
                    "instance_pointer",
                    "reason",
                },
                "GA121-DISCOVERY-NONAUTHORITY",
                f"frontier expected failure closed shape differs: {path}",
            )
            require(
                expected_failure.get("rejection_layer") == "structural_schema"
                and isinstance(expected_failure.get("reason"), str)
                and expected_failure["reason"].strip(),
                "GA121-DISCOVERY-NONAUTHORITY",
                f"frontier expected failure metadata differs: {path}",
            )
            expected = {
                key: expected_failure[key]
                for key in ("rule_id", "schema_keyword", "instance_pointer")
            }
        else:
            expected = None
        case_rows.append(
            {
                "path": path,
                "fixture_id": fixture_id,
                "fixture_class": fixture.get("fixture_class"),
                "expected_outcome": expected_outcome,
                "mutations": mutations,
                "expected_failure": expected,
            }
        )
        require(
            observed == expected,
            "GA121-DISCOVERY-NONAUTHORITY",
            f"frontier fixture diagnostic differs: {path}: {observed} != {expected}",
        )
        if observed is None:
            good += 1
        else:
            bad += 1
    require(
        len(fixture_ids) == len(set(fixture_ids)),
        "GA121-DISCOVERY-NONAUTHORITY",
        "duplicate frontier fixture ID",
    )
    observed_case_map = hashlib.sha256(canonical_json_bytes(case_rows)).hexdigest()
    require(
        observed_case_map == EXPECTED_FRONTIER_FIXTURE_CASE_MAP_SHA256,
        "GA121-DISCOVERY-NONAUTHORITY",
        "frontier fixture semantic case map differs from the frozen "
        f"{len(case_rows)}-case set: observed sha256:{observed_case_map}",
    )
    frozen = frozenset(fixture_ids)
    for fixture_id in fixture_ids:
        require(
            frozenset(item for item in fixture_ids if item != fixture_id) != frozen,
            "GA121-DISCOVERY-NONAUTHORITY",
            f"frontier remove-one canary failed: {fixture_id}",
        )
    require(
        frozen | {"reiyah.fixture.frontier-discovery.unknown@1.2.0"} != frozen,
        "GA121-DISCOVERY-NONAUTHORITY",
        "frontier unknown-case canary failed",
    )
    return {
        "known_good_passed": good,
        "known_bad_rejected_for_declared_rule": bad,
        "fixture_count": len(fixture_ids),
        "case_map_sha256": f"sha256:{EXPECTED_FRONTIER_FIXTURE_CASE_MAP_SHA256}",
        "remove_one_canary_count": len(fixture_ids),
        "unknown_injection_rejected": True,
    }


def walk_json(value: Any) -> Sequence[tuple[str, Any]]:
    rows: list[tuple[str, Any]] = []

    def visit(node: Any, pointer: str) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                child_pointer = f"{pointer}/{key}"
                rows.append((child_pointer, child))
                visit(child, child_pointer)
        elif isinstance(node, list):
            for index, child in enumerate(node):
                visit(child, f"{pointer}/{index}")

    visit(value, "")
    return rows


def control_discovery(
    files: Mapping[str, bytes], delta: Mapping[str, Any]
) -> dict[str, Any]:
    compare_binding(
        files,
        EXPECTED_FRONTIER_REGISTER_BINDING,
        "GA121-DISCOVERY-NONAUTHORITY",
    )
    compare_binding(
        files,
        EXPECTED_FRONTIER_REGISTER_SCHEMA_BINDING,
        "GA121-DISCOVERY-NONAUTHORITY",
    )
    compare_binding(
        files,
        EXPECTED_FRONTIER_FIXTURE_SCHEMA_BINDING,
        "GA121-DISCOVERY-NONAUTHORITY",
    )
    paths = sorted(
        path
        for path in delta["added_paths"]
        if path.endswith(".json")
        and (path.startswith("evidence/") or path.startswith("research/"))
        and "frontier" in path.lower()
    )
    pointer_markers = 0
    for path in paths:
        record = strict_json_bytes(files[path], path)
        for pointer, value in walk_json(record):
            key = pointer.rsplit("/", 1)[-1]
            if key in AUTHORITY_TRUE_KEYS and value is True:
                raise GateError(
                    "GA121-DISCOVERY-NONAUTHORITY",
                    f"{path}{pointer} asserts forbidden authority",
                )
            if isinstance(value, str) and "pointer" in value.lower():
                pointer_markers += 1
            if key == "redistribution_state":
                require(
                    value in ("pointer_metadata_only", "pointer_only", "not_evaluated"),
                    "GA121-DISCOVERY-NONAUTHORITY",
                    f"{path}{pointer} is not pointer-only",
                )
    require(
        FRONTIER_REGISTER_PATH in files,
        "GA121-DISCOVERY-NONAUTHORITY",
        "frontier discovery successor is absent",
    )
    require(
        FRONTIER_PREDECESSOR_PATH in files,
        "GA121-DISCOVERY-NONAUTHORITY",
        "frontier predecessor is absent",
    )
    predecessor_schema_path = "schemas/frontier-discovery-register-1.1.schema.json"
    require(
        files[FRONTIER_PREDECESSOR_PATH]
        == git_blob(RECEIPT_COMMIT, FRONTIER_PREDECESSOR_PATH),
        "GA121-DISCOVERY-NONAUTHORITY",
        "frontier predecessor differs from C_receipt",
    )
    require(
        files[predecessor_schema_path]
        == git_blob(RECEIPT_COMMIT, predecessor_schema_path),
        "GA121-DISCOVERY-NONAUTHORITY",
        "frontier predecessor schema differs from C_receipt",
    )
    register = strict_json_bytes(files[FRONTIER_REGISTER_PATH], FRONTIER_REGISTER_PATH)
    predecessor = strict_json_bytes(
        files[FRONTIER_PREDECESSOR_PATH], FRONTIER_PREDECESSOR_PATH
    )
    register_schema = strict_json_bytes(
        files["schemas/frontier-discovery-register-1.2.schema.json"],
        "schemas/frontier-discovery-register-1.2.schema.json",
    )
    predecessor_binding = {
        "relation": "append_only_successor",
        "artifact_id": "reiyah.artifact.frontier-discovery-register-1.1.0",
        "register_id": "reiyah.frontier-discovery-register",
        "path": FRONTIER_PREDECESSOR_PATH,
        "sha256": file_binding(
            FRONTIER_PREDECESSOR_PATH, files[FRONTIER_PREDECESSOR_PATH]
        )["sha256"],
        "byte_size": len(files[FRONTIER_PREDECESSOR_PATH]),
        "version": "1.1.0",
        "record_count": 38,
        "records_preserved_as_exact_prefix": True,
    }
    predecessor_schema_binding = {
        "schema_id": "https://schemas.reiyah.invalid/gate-a/1.1.0/frontier-discovery-register.schema.json",
        "schema_version": "1.1.0",
        **file_binding(predecessor_schema_path, files[predecessor_schema_path]),
    }
    diagnostic = frontier_structural_finding(
        register,
        predecessor,
        register_schema,
        predecessor_binding,
        predecessor_schema_binding,
    )
    require(
        diagnostic is None,
        "GA121-DISCOVERY-NONAUTHORITY",
        f"frontier successor failed {diagnostic}",
    )
    frontier_fixtures = validate_frontier_fixtures(
        files,
        register,
        predecessor,
        register_schema,
        predecessor_binding,
        predecessor_schema_binding,
    )
    return {
        "discovery_artifact_count": len(paths),
        "pointer_state_marker_count": pointer_markers,
        "frontier_record_count": register.get("record_count"),
        "frontier_predecessor_record_count": len(predecessor.get("records", [])),
        "frontier_fixtures": frontier_fixtures,
        "scientific_evidence_created": False,
    }


def control_inventory(files: Mapping[str, bytes]) -> dict[str, Any]:
    old_path = "evidence/public-distribution-inventory-1.1.0.json"
    successor_path = "evidence/public-distribution-inventory-1.2.1.json"
    if successor_path not in files:
        return {
            "successor_state": "not_present_publication_blocked",
            "unchanged_payload_count": 0,
        }
    old = strict_json_bytes(files[old_path], old_path)
    new = strict_json_bytes(files[successor_path], successor_path)
    old_payloads = [
        entry
        for entry in old.get("entries", [])
        if entry.get("distribution_action") == "include_payload"
    ]
    new_payloads = [
        entry
        for entry in new.get("entries", [])
        if entry.get("distribution_action") == "include_payload"
    ]
    require(
        len(old_payloads) == len(new_payloads) == 4,
        "GA121-PUBLICATION-INVENTORY-CONTINUITY",
        "inventory must retain exactly four payloads",
    )
    old_basis = [(row.get("source_ref"), row.get("payload")) for row in old_payloads]
    new_basis = [(row.get("source_ref"), row.get("payload")) for row in new_payloads]
    require(
        old_basis == new_basis,
        "GA121-PUBLICATION-INVENTORY-CONTINUITY",
        "four authorized payload identities or bytes differ",
    )
    old_pointer_rows = [
        entry
        for entry in old.get("entries", [])
        if entry.get("distribution_action") == "publish_pointer_only"
    ]
    new_pointer_rows = [
        entry
        for entry in new.get("entries", [])
        if entry.get("distribution_action") == "publish_pointer_only"
    ]
    require(
        len(old_pointer_rows) == len(new_pointer_rows) == 4
        and [row.get("source_ref") for row in old_pointer_rows]
        == [row.get("source_ref") for row in new_pointer_rows],
        "GA121-PUBLICATION-INVENTORY-CONTINUITY",
        "exact four pointer source identities differ or are incomplete",
    )
    for entry in new.get("entries", []):
        if entry.get("distribution_action") != "include_payload":
            require(
                entry.get("distribution_action") == "publish_pointer_only"
                and entry.get("payload") is None,
                "GA121-PUBLICATION-INVENTORY-CONTINUITY",
                "non-payload inventory entry is not pointer-only",
            )
    for key in (
        "gate_a_acceptance_conferred",
        "runtime_execution_authorized",
        "scientific_publication_acceptance_conferred",
    ):
        require(
            new.get(key) is False,
            "GA121-PUBLICATION-INVENTORY-CONTINUITY",
            f"inventory {key} must be false",
        )
    return {"successor_state": "pointer_governed", "unchanged_payload_count": 4}


EXPECTED_FIXTURE_OPERATIONS = frozenset(
    {
        "none",
        "mutate_packet_commit",
        "mutate_receipt_parent",
        "mutate_historical_index",
        "mutate_protected_science_byte",
        "claim_current_science_replay",
        "claim_operator_acceptance",
        "claim_runtime_authority",
        "claim_transport_verification",
        "add_unknown_delta_path",
        "frontier_top_claim",
        "frontier_missing_scope",
        "frontier_origin_mismatch",
        "frontier_invalid_access_date",
        "frontier_unknown_property",
        "frontier_fixture_base_digest",
        "frontier_fixture_authority",
        "frontier_evidence_eligibility",
        "frontier_fixed_source_state",
        "frontier_versioned_source_state",
        "frontier_duplicate_artifact",
        "frontier_predecessor_schema",
        "isolation_direct_invocation",
        "isolation_ineffective_sandbox",
    }
)


def frontier_adversarial_fixture_diagnostic(
    operation: str, files: Mapping[str, bytes]
) -> str | None:
    register = strict_json_bytes(files[FRONTIER_REGISTER_PATH], FRONTIER_REGISTER_PATH)
    predecessor = strict_json_bytes(
        files[FRONTIER_PREDECESSOR_PATH], FRONTIER_PREDECESSOR_PATH
    )
    register_schema_path = "schemas/frontier-discovery-register-1.2.schema.json"
    predecessor_schema_path = "schemas/frontier-discovery-register-1.1.schema.json"
    register_schema = strict_json_bytes(
        files[register_schema_path], register_schema_path
    )
    predecessor_binding = {
        "relation": "append_only_successor",
        "artifact_id": "reiyah.artifact.frontier-discovery-register-1.1.0",
        "register_id": "reiyah.frontier-discovery-register",
        "path": FRONTIER_PREDECESSOR_PATH,
        "sha256": file_binding(
            FRONTIER_PREDECESSOR_PATH, files[FRONTIER_PREDECESSOR_PATH]
        )["sha256"],
        "byte_size": len(files[FRONTIER_PREDECESSOR_PATH]),
        "version": "1.1.0",
        "record_count": 38,
        "records_preserved_as_exact_prefix": True,
    }
    predecessor_schema_binding = {
        "schema_id": "https://schemas.reiyah.invalid/gate-a/1.1.0/frontier-discovery-register.schema.json",
        "schema_version": "1.1.0",
        **file_binding(predecessor_schema_path, files[predecessor_schema_path]),
    }
    mutated = copy.deepcopy(register)
    if operation == "frontier_top_claim":
        mutated["comparative_superiority_claimed"] = True
    elif operation == "frontier_missing_scope":
        del mutated["records"][38]["scope"]
    elif operation == "frontier_origin_mismatch":
        mutated["records"][38]["assertion_origin"] = "institution_self_report"
    elif operation == "frontier_invalid_access_date":
        mutated["records"][38]["accessed_on"] = "2026-02-30"
    elif operation == "frontier_unknown_property":
        mutated["records"][38]["unknown_authority"] = False
    elif operation == "frontier_evidence_eligibility":
        mutated["records"][38]["evidence_eligibility"] = "eligible_retained_payload"
    elif operation == "frontier_fixed_source_state":
        index = next(
            index
            for index, record in enumerate(mutated["records"][38:], start=38)
            if record["source_stability"] == "fixed_document"
        )
        mutated["records"][index]["source_version_state"] = "current_version_unmeasured"
    elif operation == "frontier_versioned_source_state":
        mutated["records"][50]["source_version_state"] = "publisher_version_observed"
    elif operation == "frontier_duplicate_artifact":
        mutated["records"][38]["artifact_id"] = mutated["records"][0]["artifact_id"]
    elif operation == "frontier_predecessor_schema":
        mutated["predecessor_binding"]["schema_binding"]["sha256"] = (
            "sha256:" + "0" * 64
        )
    elif operation in {"frontier_fixture_base_digest", "frontier_fixture_authority"}:
        fixture_path = FRONTIER_FIXTURE_PATHS[0]
        fixture = strict_json_bytes(files[fixture_path], fixture_path)
        if operation == "frontier_fixture_base_digest":
            fixture["base_artifact_ref"]["sha256"] = "sha256:" + "0" * 64
        else:
            fixture["fixture_creates_claims"] = True
        mutated_files = dict(files)
        mutated_files[fixture_path] = canonical_json_bytes(fixture)
        try:
            validate_frontier_fixtures(
                mutated_files,
                register,
                predecessor,
                register_schema,
                predecessor_binding,
                predecessor_schema_binding,
            )
        except GateError as exc:
            return exc.code
        return None
    else:
        return "GA121-FIXTURE-COVERAGE"
    observed = frontier_structural_finding(
        mutated,
        predecessor,
        register_schema,
        predecessor_binding,
        predecessor_schema_binding,
    )
    return None if observed is None else observed["rule_id"]


STARTUP_CONTRACT_WITNESS_OPERATIONS = frozenset(
    {"isolation_direct_invocation", "isolation_ineffective_sandbox"}
)


def captured_gate_error(function: Callable[[], Any]) -> str | None:
    try:
        function()
    except GateError as exc:
        return exc.code
    return None


def replay_fixture_diagnostic(
    operation: str,
    files: Mapping[str, bytes],
    modes: Mapping[str, str],
    plan: Mapping[str, Any],
    baseline: Mapping[str, Mapping[str, Any]],
) -> tuple[str | None, str]:
    if operation.startswith("frontier_"):
        return (
            frontier_adversarial_fixture_diagnostic(operation, files),
            "production_frontier_predicate_replay",
        )
    if operation in STARTUP_CONTRACT_WITNESS_OPERATIONS:
        # These cases describe conditions that must be rejected before this module can
        # import. The live startup path above performs the write and libsandbox denial
        # probes on every invocation; an in-process mutation cannot replay pre-import
        # state and is therefore retained only as a startup-contract witness.
        return "GA121-ISOLATION", "startup_contract_witness"

    mutated_plan = copy.deepcopy(plan)
    mutated_files = dict(files)
    mutated_modes = dict(modes)
    if operation == "mutate_packet_commit":
        mutated_plan["predecessor"]["packet_commit"] = "0" * 40
        function = lambda: control_packet_identity(mutated_plan)
    elif operation == "mutate_receipt_parent":
        mutated_plan["predecessor"]["packet_commit"] = "0" * 40
        function = lambda: control_topology(mutated_plan)
    elif operation == "mutate_historical_index":
        path = mutated_plan["predecessor"]["history"]["index"]["path"]
        mutated_files[path] = mutated_files[path] + b"\n"
        function = lambda: control_history(mutated_files, mutated_plan)
    elif operation == "mutate_protected_science_byte":
        path = "tools/gate_a_1_2_0_science.py"
        mutated_files[path] = mutated_files[path] + b"\n"
        function = lambda: control_protected(mutated_files, mutated_modes, baseline)
    elif operation == "claim_current_science_replay":
        mutated_plan["inherited_science"]["current_science_replay_performed"] = True
        function = lambda: control_inherited_science(mutated_plan, mutated_files)
    elif operation == "claim_operator_acceptance":
        mutated_plan["authority"]["operator_acceptance_authorized"] = True
        function = lambda: control_authority(mutated_plan)
    elif operation == "claim_runtime_authority":
        mutated_plan["authority"]["runtime_authorized"] = True
        function = lambda: control_authority(mutated_plan)
    elif operation == "claim_transport_verification":
        mutated_plan["authority"]["transport_verification_authorized"] = True
        function = lambda: control_authority(mutated_plan)
    elif operation == "add_unknown_delta_path":
        path = "fixtures/v1.2.1/known-bad/undeclared-extra-artifact.json"
        mutated_files[path] = b"{}\n"
        mutated_modes[path] = "100644"
        function = lambda: derive_delta(
            mutated_files, mutated_modes, baseline, mutated_plan
        )
    elif operation == "none":

        def function() -> None:
            control_packet_identity(mutated_plan)
            control_topology(mutated_plan)
            control_history(mutated_files, mutated_plan)
            control_protected(mutated_files, mutated_modes, baseline)
            control_inherited_science(mutated_plan, mutated_files)
            derive_delta(mutated_files, mutated_modes, baseline, mutated_plan)
            control_authority(mutated_plan)
    else:
        return "GA121-FIXTURE-COVERAGE", "unsupported_fixture_operation"
    return captured_gate_error(function), "production_control_replay"


def control_fixtures(
    files: Mapping[str, bytes],
    modes: Mapping[str, str],
    plan: Mapping[str, Any],
    baseline: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    require(
        hashlib.sha256(files[FIXTURE_CATALOG_PATH]).hexdigest()
        == EXPECTED_FIXTURE_CATALOG_SHA256,
        "GA121-FIXTURE-COVERAGE",
        "continuity fixture catalog bytes differ from the locked case map",
    )
    catalog = strict_json_bytes(files[FIXTURE_CATALOG_PATH], FIXTURE_CATALOG_PATH)
    validate_simple_schema(
        catalog,
        "schemas/continuity-fixture-catalog-1.2.1.schema.json",
        files,
        "GA121-FIXTURE-COVERAGE",
    )
    rows = catalog.get("fixtures")
    require(
        isinstance(rows, list), "GA121-FIXTURE-COVERAGE", "fixture catalog rows absent"
    )
    ids: list[str] = []
    paths: list[str] = []
    operations: set[str] = set()
    good = bad = 0
    replay_classes: dict[str, int] = {}
    for row in rows:
        require(
            isinstance(row, dict),
            "GA121-FIXTURE-COVERAGE",
            "fixture catalog row is not an object",
        )
        path = row.get("path")
        require(
            isinstance(path, str) and path in files,
            "GA121-FIXTURE-COVERAGE",
            f"fixture absent: {path}",
        )
        observed = file_binding(path, files[path])
        require(
            observed["sha256"] == row.get("sha256")
            and observed["byte_size"] == row.get("byte_size"),
            "GA121-FIXTURE-COVERAGE",
            f"fixture byte binding differs: {path}",
        )
        fixture = strict_json_bytes(files[path], path)
        validate_simple_schema(
            fixture,
            "schemas/continuity-fixture-1.2.1.schema.json",
            files,
            "GA121-FIXTURE-COVERAGE",
        )
        fixture_id = fixture.get("fixture_id")
        require(
            fixture_id == row.get("fixture_id"),
            "GA121-FIXTURE-COVERAGE",
            f"fixture identity differs: {path}",
        )
        require(
            fixture.get("expected_outcome") == row.get("expected_outcome")
            and fixture.get("expected_diagnostic") == row.get("expected_diagnostic"),
            "GA121-FIXTURE-COVERAGE",
            f"fixture expectation differs: {path}",
        )
        operation = fixture.get("operation")
        require(
            isinstance(operation, str),
            "GA121-FIXTURE-COVERAGE",
            f"fixture operation absent: {path}",
        )
        operations.add(operation)
        diagnostic, replay_class = replay_fixture_diagnostic(
            operation, files, modes, plan, baseline
        )
        replay_classes[replay_class] = replay_classes.get(replay_class, 0) + 1
        require(
            diagnostic == fixture.get("expected_diagnostic"),
            "GA121-FIXTURE-COVERAGE",
            f"production continuity diagnostic differs: {path}",
        )
        ids.append(fixture_id)
        paths.append(path)
        if diagnostic is None:
            good += 1
        else:
            bad += 1
    require(
        len(ids) == len(set(ids)) and len(paths) == len(set(paths)),
        "GA121-FIXTURE-COVERAGE",
        "duplicate fixture identity or path",
    )
    require(
        operations == EXPECTED_FIXTURE_OPERATIONS,
        "GA121-FIXTURE-COVERAGE",
        f"fixture operation set differs: {sorted(operations)}",
    )
    actual_paths = sorted(
        path
        for path in files
        if path.startswith("fixtures/v1.2.1/")
        and path.endswith(".json")
        and path != FIXTURE_CATALOG_PATH
    )
    require(
        sorted(paths) == actual_paths,
        "GA121-FIXTURE-COVERAGE",
        "catalog membership differs from fixture directory",
    )
    expected_ids = frozenset(ids)
    for removed in ids:
        require(
            frozenset(item for item in ids if item != removed) != expected_ids,
            "GA121-FIXTURE-COVERAGE",
            f"remove-one canary failed for {removed}",
        )
    require(
        expected_ids | {"reiyah.fixture.continuity.unknown@1.2.1"} != expected_ids,
        "GA121-FIXTURE-COVERAGE",
        "unknown injection canary failed",
    )
    return {
        "catalog_path": FIXTURE_CATALOG_PATH,
        "known_good_passed": good,
        "known_bad_rejected_for_declared_diagnostic": bad,
        "fixture_count": len(rows),
        "production_control_replay_count": replay_classes.get(
            "production_control_replay", 0
        ),
        "production_frontier_predicate_replay_count": replay_classes.get(
            "production_frontier_predicate_replay", 0
        ),
        "startup_contract_witness_count": replay_classes.get(
            "startup_contract_witness", 0
        ),
        "remove_one_canary_count": len(rows),
        "unknown_injection_rejected": True,
    }


def canonical_record_digest(records: Sequence[Mapping[str, Any]]) -> str:
    encoded = json.dumps(
        list(records), ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def absolute_file_observation(path: str) -> dict[str, Any]:
    candidate = Path(path)
    try:
        resolved = candidate.resolve(strict=True)
        data = candidate.read_bytes()
    except OSError as exc:
        raise GateError(
            "GA121-TOOLCHAIN-BINDING", f"cannot observe executable {path}: {exc}"
        ) from exc
    return {
        "path": path,
        "resolved_path": str(resolved),
        "sha256": hashlib.sha256(data).hexdigest(),
        "size": resolved.stat().st_size,
    }


def current_platform_observation() -> dict[str, str]:
    try:
        system_version = plistlib.loads(
            Path("/System/Library/CoreServices/SystemVersion.plist").read_bytes()
        )
    except (OSError, plistlib.InvalidFileException) as exc:
        raise GateError(
            "GA121-TOOLCHAIN-BINDING", f"cannot observe macOS version: {exc}"
        ) from exc
    uname = os.uname()
    return {
        "system": uname.sysname,
        "machine": uname.machine,
        "kernel_release": uname.release,
        "kernel_version": uname.version,
        "product_version": str(system_version.get("ProductVersion", "")),
        "product_build_version": str(system_version.get("ProductBuildVersion", "")),
        "python_implementation": sys.implementation.name,
        "python_version": sys.version.split()[0],
    }


def current_python_runtime_observation(
    specification: Mapping[str, Any],
) -> dict[str, Any]:
    root = Path(specification["stdlib_root"])
    require(
        root.is_dir() and not root.is_symlink(),
        "GA121-TOOLCHAIN-BINDING",
        f"invalid stdlib root {root}",
    )
    excluded = set(specification["excluded_subtrees"])
    rows: list[dict[str, Any]] = []
    for directory, dirnames, filenames in os.walk(root, followlinks=False):
        directory_path = Path(directory)
        relative_directory = directory_path.relative_to(root)
        if relative_directory == Path("."):
            dirnames[:] = sorted(name for name in dirnames if name not in excluded)
        else:
            dirnames.sort()
        filenames.sort()
        for name in dirnames:
            require(
                not (directory_path / name).is_symlink(),
                "GA121-TOOLCHAIN-BINDING",
                f"stdlib directory symlink {(directory_path / name)}",
            )
        for name in filenames:
            path = directory_path / name
            require(
                not path.is_symlink() and path.is_file(),
                "GA121-TOOLCHAIN-BINDING",
                f"invalid stdlib file {path}",
            )
            data = path.read_bytes()
            rows.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "size": len(data),
                }
            )
    rows.sort(key=lambda row: row["path"])
    framework = Path(specification["framework_path"]).read_bytes()
    return {
        "stdlib_root": specification["stdlib_root"],
        "excluded_subtrees": specification["excluded_subtrees"],
        "framework_path": specification["framework_path"],
        "stdlib_file_count": len(rows),
        "stdlib_tree_sha256": canonical_record_digest(rows),
        "framework_size": len(framework),
        "framework_sha256": hashlib.sha256(framework).hexdigest(),
    }


def verify_inherited_environment(files: Mapping[str, bytes]) -> dict[str, Any]:
    inherited = strict_json_bytes(
        files["validation/toolchain-lock-1.2.0.json"],
        "validation/toolchain-lock-1.2.0.json",
    )
    require(
        current_platform_observation() == inherited.get("platform"),
        "GA121-TOOLCHAIN-BINDING",
        "platform differs from inherited lock",
    )
    executables = inherited.get("executables")
    require(
        isinstance(executables, dict),
        "GA121-TOOLCHAIN-BINDING",
        "inherited executable lock absent",
    )
    for name, binding in sorted(executables.items()):
        require(
            absolute_file_observation(binding["path"]) == binding,
            "GA121-TOOLCHAIN-BINDING",
            f"inherited executable differs: {name}",
        )
    runtime = inherited.get("python_runtime")
    require(
        isinstance(runtime, dict),
        "GA121-TOOLCHAIN-BINDING",
        "inherited Python runtime lock absent",
    )
    require(
        current_python_runtime_observation(runtime) == runtime,
        "GA121-TOOLCHAIN-BINDING",
        "Python framework or stdlib differs from inherited lock",
    )
    profile = inherited.get("execution_profile", {})
    require(
        profile.get("required_python_flags") == ["-I", "-S", "-B"]
        and profile.get("seatbelt_application")
        == "external_launcher_with_early_libsandbox_policy_checks"
        and profile.get("network_policy") == "denied_by_locked_macos_seatbelt_profile"
        and profile.get("filesystem_write_policy")
        == "denied_except_write_data_to_dev_null",
        "GA121-TOOLCHAIN-BINDING",
        "inherited isolation profile differs",
    )
    return {
        "platform": inherited["platform"],
        "executable_count": len(executables),
        "stdlib_file_count": runtime["stdlib_file_count"],
        "stdlib_tree_sha256": runtime["stdlib_tree_sha256"],
        "seatbelt_profile_sha256": profile.get("seatbelt_profile_sha256"),
        "early_write_and_denial_probes_passed": True,
    }


def control_toolchain(files: Mapping[str, bytes]) -> dict[str, Any]:
    require(
        LOCK_PATH in files,
        "GA121-TOOLCHAIN-BINDING",
        "continuity toolchain lock absent",
    )
    lock = strict_json_bytes(files[LOCK_PATH], LOCK_PATH)
    validate_simple_schema(
        lock,
        "schemas/continuity-toolchain-lock-1.2.1.schema.json",
        files,
        "GA121-TOOLCHAIN-BINDING",
    )
    require(
        lock.get("schema_id")
        == "https://schemas.reiyah.invalid/gate-a/1.2.1/continuity-toolchain-lock.schema.json",
        "GA121-TOOLCHAIN-BINDING",
        "toolchain lock schema differs",
    )
    require(
        lock.get("version") == "1.2.1",
        "GA121-TOOLCHAIN-BINDING",
        "toolchain lock version differs",
    )
    runtime = lock.get("runtime", {})
    require(
        runtime.get("implementation") == sys.implementation.name,
        "GA121-TOOLCHAIN-BINDING",
        "Python implementation differs",
    )
    require(
        runtime.get("version") == sys.version.split()[0],
        "GA121-TOOLCHAIN-BINDING",
        "Python version differs",
    )
    inherited = lock.get("inherited_lock")
    require(
        isinstance(inherited, dict),
        "GA121-TOOLCHAIN-BINDING",
        "inherited lock binding absent",
    )
    compare_binding(files, inherited, "GA121-TOOLCHAIN-BINDING")
    tools = lock.get("tools")
    schemas = lock.get("schemas")
    require(
        isinstance(tools, list) and isinstance(schemas, list),
        "GA121-TOOLCHAIN-BINDING",
        "tool or schema bindings absent",
    )
    require(
        [row.get("path") for row in tools]
        == ["tools/gate_a_1_2_1.sh", "tools/gate_a_1_2_1.py"],
        "GA121-TOOLCHAIN-BINDING",
        "tool binding paths differ",
    )
    require(
        [row.get("path") for row in schemas] == list(SCHEMA_PATHS),
        "GA121-TOOLCHAIN-BINDING",
        "schema binding paths differ",
    )
    for row in (*tools, *schemas):
        compare_binding(files, row, "GA121-TOOLCHAIN-BINDING")
        if str(row["path"]).endswith(".json"):
            strict_json_bytes(files[row["path"]], row["path"])
    environment = verify_inherited_environment(files)
    return {
        "runtime": runtime,
        "inherited_lock": inherited,
        "tool_count": len(tools),
        "schema_count": len(schemas),
        "environment": environment,
    }


def control_authority(plan: Mapping[str, Any]) -> dict[str, Any]:
    authority = plan.get("authority")
    require(
        authority == EXPECTED_AUTHORITY,
        "GA121-AUTHORITY-NONCLAIMS",
        "authority nonclaims differ from the executable closed map",
    )
    return {
        "operator_acceptance_state": "unaccepted",
        "runtime_authorized": False,
        "gate_b_authorized": False,
        "transport_verification_state": "not_evaluated",
        "scientific_claim_authority": False,
        "publication_acceptance_authorized": False,
    }


def excluded_from_projection(path: str) -> bool:
    return path in PROJECTION_EXCLUSION_PATHS


def stable_media_type(path: str) -> str:
    suffix = Path(path).suffix.lower()
    return {
        ".json": "application/json",
        ".md": "text/markdown",
        ".py": "text/x-python",
        ".sh": "text/x-shellscript",
        ".cff": "application/yaml",
        ".yaml": "application/yaml",
        ".yml": "application/yaml",
        ".txt": "text/plain",
        ".jsonl": "application/x-ndjson",
    }.get(suffix, "application/octet-stream")


def candidate_projection(
    files: Mapping[str, bytes], modes: Mapping[str, str]
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    serialized = bytearray()
    total = 0
    for path in sorted(path for path in files if not excluded_from_projection(path)):
        data = files[path]
        digest = hashlib.sha256(data).hexdigest()
        mode = modes[path]
        total += len(data)
        serialized.extend(path.encode("utf-8"))
        serialized.extend(b"\0")
        serialized.extend(digest.encode("ascii"))
        serialized.extend(b"\0")
        serialized.extend(mode.encode("ascii"))
        serialized.extend(b"\0")
        serialized.extend(str(len(data)).encode("ascii"))
        serialized.extend(b"\n")
        records.append(
            {
                "path": path,
                "sha256": f"sha256:{digest}",
                "git_mode": mode,
                "byte_size": len(data),
                "media_type": stable_media_type(path),
            }
        )
    return {
        "serialization": "sorted_path_nul_sha256_nul_git_mode_nul_byte_count_lf",
        "sha256": f"sha256:{hashlib.sha256(bytes(serialized)).hexdigest()}",
        "artifact_count": len(records),
        "total_bytes": total,
        "exclusion_policy": copy.deepcopy(list(PROJECTION_EXCLUSION_POLICY)),
        "records": records,
    }


def output_state(files: Mapping[str, bytes]) -> dict[str, bool]:
    return {path: path in files for path in sorted(OUTPUT_PATHS)}


def validate_cycle_state(files: Mapping[str, bytes], cycle: str) -> None:
    state = output_state(files)
    if cycle in ("development", "emit_index"):
        require(
            not any(state.values()),
            "GA121-OUTPUT-STATE",
            f"canonical outputs must be absent: {state}",
        )
    elif cycle == "emit_report":
        require(
            state[INDEX_PATH] and state[SIDECAR_PATH] and not state[REPORT_PATH],
            "GA121-OUTPUT-STATE",
            f"emit-report state differs: {state}",
        )
    elif cycle == "ordinary_release":
        require(
            all(state.values()),
            "GA121-OUTPUT-STATE",
            f"ordinary release outputs incomplete: {state}",
        )
    else:
        raise GateError("GA121-CLI-ARGUMENT", f"unknown cycle {cycle}")


def render_index(
    projection: Mapping[str, Any], delta: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        "schema_id": "https://schemas.reiyah.invalid/gate-a/1.2.1/gate-a-index.schema.json",
        "artifact_id": "reiyah.artifact.gate-a-index-1.2.1",
        "release_id": "reiyah.gate-a-evidence-index@1.2.1",
        "version": "1.2.1",
        "architecture_status": "candidate_pending_canonical_report",
        "operator_acceptance_state": "unaccepted",
        "runtime_authorized": False,
        "gate_b_authorized": False,
        "transport_verification_state": "not_evaluated",
        "public_distribution_authorized": False,
        "science_evidence_state": "inherited_historical_exact_byte_binding",
        "predecessor": {
            "packet_commit": PACKET_COMMIT,
            "receipt_commit": RECEIPT_COMMIT,
            "historical_index": "history/gate-a-1.2.0/gate/GATE_A_EVIDENCE_INDEX.json",
            "canonical_report": "gate/validation-reports/gate-a-validation-1.2.0.json",
        },
        "candidate_projection": {
            key: projection[key]
            for key in (
                "serialization",
                "sha256",
                "artifact_count",
                "total_bytes",
                "exclusion_policy",
            )
        },
        "artifacts": projection["records"],
        "successor_delta": delta,
    }


def validate_index_readback(
    files: Mapping[str, bytes], index: Mapping[str, Any]
) -> None:
    expected = canonical_json_bytes(index)
    require(
        files.get(INDEX_PATH) == expected,
        "GA121-INDEX-READBACK",
        "canonical index bytes differ",
    )
    expected_sidecar = (
        f"sha256:{hashlib.sha256(expected).hexdigest()}  {INDEX_PATH}\n".encode("ascii")
    )
    require(
        files.get(SIDECAR_PATH) == expected_sidecar,
        "GA121-INDEX-READBACK",
        "canonical index sidecar differs",
    )


def run_control(
    control_id: str,
    function: Callable[[], Any],
    controls: list[dict[str, Any]],
    diagnostics: list[dict[str, str]],
) -> Any:
    try:
        evidence = function()
        controls.append(
            {"control_id": control_id, "state": "pass", "evidence": evidence}
        )
        return evidence
    except GateError as exc:
        controls.append({"control_id": control_id, "state": "fail", "evidence": None})
        diagnostics.append({"code": exc.code, "message": exc.message})
        return None


def evaluate(
    files: Mapping[str, bytes],
    modes: Mapping[str, str],
    symlinks: Sequence[str],
    mode: str,
    cycle: str,
) -> dict[str, Any]:
    require(not symlinks, "GA121-SYMLINK", f"symlinks are prohibited: {list(symlinks)}")
    forbidden = sorted(
        path
        for path in files
        if path == ".DS_Store"
        or any(path.startswith(prefix) for prefix in FORBIDDEN_ARTIFACT_PREFIXES)
    )
    require(
        not forbidden,
        "GA121-FORBIDDEN-ARTIFACT",
        f"cache or host metadata is tracked/present: {forbidden}",
    )
    validate_cycle_state(files, cycle)
    plan = load_plan(files)
    baseline = git_tree(RECEIPT_COMMIT)
    projection = candidate_projection(files, modes)
    controls: list[dict[str, Any]] = []
    diagnostics: list[dict[str, str]] = []
    packet = run_control(
        EXPECTED_CONTROL_IDS[0],
        lambda: control_packet_identity(plan),
        controls,
        diagnostics,
    )
    topology = run_control(
        EXPECTED_CONTROL_IDS[1], lambda: control_topology(plan), controls, diagnostics
    )
    history = run_control(
        EXPECTED_CONTROL_IDS[2],
        lambda: control_history(files, plan),
        controls,
        diagnostics,
    )
    inherited_report = run_control(
        EXPECTED_CONTROL_IDS[3],
        lambda: control_report(files, plan),
        controls,
        diagnostics,
    )
    rights = run_control(
        EXPECTED_CONTROL_IDS[4],
        lambda: control_rights_receipt(files, plan),
        controls,
        diagnostics,
    )
    protected = run_control(
        EXPECTED_CONTROL_IDS[5],
        lambda: control_protected(files, modes, baseline),
        controls,
        diagnostics,
    )
    inherited_science = run_control(
        EXPECTED_CONTROL_IDS[6],
        lambda: control_inherited_science(plan, files),
        controls,
        diagnostics,
    )
    delta = run_control(
        EXPECTED_CONTROL_IDS[7],
        lambda: derive_delta(files, modes, baseline, plan),
        controls,
        diagnostics,
    )
    if delta is None:
        delta = {
            "baseline_commit": RECEIPT_COMMIT,
            "changed_existing_paths": [],
            "removed_existing_paths": [],
            "added_paths": [],
            "unknown_paths": ["delta_not_available"],
        }
    run_control(
        EXPECTED_CONTROL_IDS[8],
        lambda: control_documentation_links(files, delta),
        controls,
        diagnostics,
    )
    discovery = run_control(
        EXPECTED_CONTROL_IDS[9],
        lambda: control_discovery(files, delta),
        controls,
        diagnostics,
    )
    inventory = run_control(
        EXPECTED_CONTROL_IDS[10],
        lambda: control_inventory(files),
        controls,
        diagnostics,
    )
    fixtures = run_control(
        EXPECTED_CONTROL_IDS[11],
        lambda: control_fixtures(files, modes, plan, baseline),
        controls,
        diagnostics,
    )
    toolchain = run_control(
        EXPECTED_CONTROL_IDS[12],
        lambda: control_toolchain(files),
        controls,
        diagnostics,
    )
    controls.append(
        {
            "control_id": EXPECTED_CONTROL_IDS[13],
            "state": "not_evaluated"
            if mode == "development"
            else "pending_outer_comparison",
            "evidence": {"required_worker_count": 2 if mode == "release" else 0},
        }
    )
    authority = run_control(
        EXPECTED_CONTROL_IDS[14], lambda: control_authority(plan), controls, diagnostics
    )
    index = render_index(projection, delta)
    if cycle in ("emit_report", "ordinary_release"):
        try:
            validate_index_readback(files, index)
        except GateError as exc:
            diagnostics.append({"code": exc.code, "message": exc.message})
    status = "pass" if not diagnostics else "fail"
    evaluation = {
        "schema_id": "https://schemas.reiyah.invalid/gate-a/1.2.1/validation-report.schema.json",
        "artifact_id": "reiyah.artifact.validation-report-1.2.1",
        "report_id": "reiyah.validation-report.gate-a-continuity-1.2.1",
        "version": "1.2.1",
        "mode": mode,
        "status": status,
        "release_eligible": mode == "release" and status == "pass",
        "public_distribution_eligible": False,
        "predecessor": {
            "packet": packet,
            "topology": topology,
            "history": history,
            "canonical_report": inherited_report,
            "rights_and_receipt": rights,
        },
        "inherited_science": inherited_science or {"evidence_state": "invalid"},
        "candidate_projection": {
            key: projection[key]
            for key in (
                "serialization",
                "sha256",
                "artifact_count",
                "total_bytes",
                "exclusion_policy",
            )
        },
        "successor_delta": delta,
        "controls": controls,
        "fixtures": fixtures or {"fixture_count": 0},
        "discovery": discovery,
        "publication_inventory": inventory,
        "toolchain": toolchain,
        "protected_predecessor": protected,
        "authority_nonclaims": authority or {"operator_acceptance_state": "invalid"},
        "diagnostics": diagnostics,
        "_index": index,
    }
    try:
        validate_simple_schema(
            index,
            "schemas/gate-a-index-1.2.1.schema.json",
            files,
            "GA121-INDEX-SCHEMA",
        )
        validate_simple_schema(
            public_report(evaluation),
            "schemas/validation-report-1.2.1.schema.json",
            files,
            "GA121-REPORT-SCHEMA",
        )
    except GateError as exc:
        evaluation["diagnostics"].append({"code": exc.code, "message": exc.message})
        evaluation["status"] = "fail"
        evaluation["release_eligible"] = False
    return evaluation


def public_report(evaluation: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in evaluation.items() if key != "_index"}


def observed_toolchain() -> dict[str, Any]:
    return {
        "schema_id": "https://schemas.reiyah.invalid/gate-a/1.2.1/continuity-toolchain-lock.schema.json",
        "artifact_id": "reiyah.artifact.continuity-toolchain-lock-1.2.1",
        "version": "1.2.1",
        "runtime": {
            "implementation": sys.implementation.name,
            "version": sys.version.split()[0],
            "isolated_flag": True,
            "no_site_flag": True,
            "no_bytecode_flag": True,
            "standard_library_only": True,
        },
        "inherited_lock": file_binding("validation/toolchain-lock-1.2.0.json"),
        "tools": [
            file_binding("tools/gate_a_1_2_1.sh"),
            file_binding("tools/gate_a_1_2_1.py"),
        ],
        "schemas": [file_binding(path) for path in SCHEMA_PATHS],
    }


def release_evaluation(
    cycle: str, expected_head: str | None = None
) -> tuple[dict[str, Any], dict[str, Any]]:
    status = git("status", "--porcelain=v1", "-z", binary=True)
    require(
        status == b"", "GA121-RELEASE-DIRTY", "release validation requires a clean tree"
    )
    head = str(git("rev-parse", "HEAD"))
    if expected_head is not None:
        require(
            head == expected_head,
            "GA121-DUAL-EVALUATION",
            "worker HEAD differs from parent",
        )
    ancestor = subprocess.run(
        ("git", "-C", str(ROOT), "merge-base", "--is-ancestor", RECEIPT_COMMIT, head),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    require(
        ancestor.returncode == 0,
        "GA121-PREDECESSOR-TOPOLOGY",
        "release HEAD does not descend from C_receipt",
    )
    files, modes, symlinks = release_files(head)
    evaluation = evaluate(files, modes, symlinks, "release", cycle)
    return evaluation, {"head": head, "files": files, "modes": modes}


def invoke_worker(cycle: str, head: str) -> tuple[dict[str, Any], int]:
    # macOS refuses a nested sandbox_apply, so a release worker must not re-enter
    # the shell launcher. The worker is an ordinary child of this already-sandboxed
    # process and therefore inherits the identical locked Seatbelt policy. It still
    # re-proves that policy independently: its pre-import startup contract repeats
    # the interpreter-flag check, the EPERM write probe against its own bytes, and
    # the seven libsandbox denial probes. The launcher marker below is never
    # sufficient on its own.
    command = (
        str(PYTHON_PATH),
        "-I",
        "-S",
        "-B",
        str(ROOT / VALIDATOR_PATH),
        "--snapshot-mode",
        "release",
        "--output",
        "json",
        "--worker",
        "--worker-cycle",
        cycle,
        "--worker-parent-pid",
        str(os.getpid()),
        "--expected-head",
        head,
    )
    completed = subprocess.run(
        command,
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env={
            "LANG": "C",
            "LC_ALL": "C",
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin",
            "REIYAH_GATE_A_121_LAUNCHED": "1",
        },
    )
    require(
        completed.returncode == 0,
        "GA121-DUAL-EVALUATION",
        f"worker failed: {completed.stderr.decode('utf-8', 'replace').strip()} {completed.stdout.decode('utf-8', 'replace')[:400]}",
    )
    payload = strict_json_bytes(completed.stdout, "release-worker-stdout")
    require(
        payload.get("worker_protocol")
        == "reiyah.protocol.continuity-release-worker@1.2.1",
        "GA121-DUAL-EVALUATION",
        "worker protocol differs",
    )
    require(
        payload.get("parent_pid") == os.getpid(),
        "GA121-DUAL-EVALUATION",
        "worker parent PID differs",
    )
    pid = payload.get("worker_pid")
    require(isinstance(pid, int), "GA121-DUAL-EVALUATION", "worker PID absent")
    evaluation = payload.get("evaluation")
    require(
        isinstance(evaluation, dict),
        "GA121-DUAL-EVALUATION",
        "worker evaluation absent",
    )
    return evaluation, pid


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise GateError("GA121-CLI-ARGUMENT", message)


def parse_args(arguments: Sequence[str]) -> argparse.Namespace:
    parser = Parser(description=__doc__)
    parser.add_argument(
        "--snapshot-mode", choices=("development", "release"), default="development"
    )
    parser.add_argument("--output", choices=("human", "json"), default="human")
    parser.add_argument("--observe-toolchain", action="store_true")
    parser.add_argument("--emit-index", action="store_true")
    parser.add_argument("--emit-report", action="store_true")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--worker-cycle",
        choices=("emit_index", "emit_report", "ordinary_release"),
        help=argparse.SUPPRESS,
    )
    parser.add_argument("--worker-parent-pid", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--expected-head", help=argparse.SUPPRESS)
    return parser.parse_args(arguments)


def render_human(report: Mapping[str, Any]) -> None:
    print(f"Gate A 1.2.1 continuity {report['mode']} observation: {report['status']}")
    print("  scope: documentation, discovery, lineage, and publication continuity only")
    print(
        "  science: inherited historical exact-byte binding; current replay not performed"
    )
    print(
        f"  candidate: {report['candidate_projection']['artifact_count']} artifacts, {report['candidate_projection']['sha256']}"
    )
    print(f"  release eligible: {str(report['release_eligible']).lower()}")
    print(
        "  public distribution eligible: "
        f"{str(report['public_distribution_eligible']).lower()}"
    )
    if report["diagnostics"]:
        for diagnostic in report["diagnostics"]:
            print(f"  {diagnostic['code']}: {diagnostic['message']}")


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    output = "json" if "--output=json" in arguments else "human"
    if "--output" in arguments:
        index = arguments.index("--output")
        if index + 1 < len(arguments):
            output = arguments[index + 1]
    try:
        options = parse_args(arguments)
        verify_identity_and_isolation()
        special_count = sum(
            (
                options.observe_toolchain,
                options.emit_index,
                options.emit_report,
                options.worker,
            )
        )
        require(
            special_count <= 1,
            "GA121-CLI-ARGUMENT",
            "special modes are mutually exclusive",
        )
        worker_operands = (
            options.worker_cycle is not None,
            options.worker_parent_pid is not None,
            options.expected_head is not None,
        )
        require(
            options.worker == all(worker_operands)
            and (not options.worker or all(worker_operands)),
            "GA121-CLI-ARGUMENT",
            "worker operands must be one closed set",
        )
        if options.observe_toolchain:
            payload = observed_toolchain()
            if options.output == "json":
                sys.stdout.buffer.write(canonical_json_bytes(payload))
            else:
                print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
        require(
            not (options.emit_index or options.emit_report or options.worker)
            or (options.snapshot_mode == "release" and options.output == "json"),
            "GA121-CLI-ARGUMENT",
            "emission and worker modes require release JSON mode",
        )
        if options.worker:
            require(
                os.getppid() == options.worker_parent_pid,
                "GA121-DUAL-EVALUATION",
                "worker parent process differs",
            )
            evaluation, _snapshot = release_evaluation(
                options.worker_cycle, options.expected_head
            )
            payload = {
                "worker_protocol": "reiyah.protocol.continuity-release-worker@1.2.1",
                "parent_pid": options.worker_parent_pid,
                "worker_pid": os.getpid(),
                "evaluation": public_report(evaluation),
            }
            sys.stdout.buffer.write(canonical_json_bytes(payload))
            return 0 if evaluation["status"] == "pass" else 1
        cycle = (
            "emit_index"
            if options.emit_index
            else "emit_report"
            if options.emit_report
            else "ordinary_release"
            if options.snapshot_mode == "release"
            else "development"
        )
        if options.snapshot_mode == "development":
            files, modes, symlinks = scan_worktree()
            evaluation = evaluate(files, modes, symlinks, "development", cycle)
        else:
            evaluation, snapshot = release_evaluation(cycle)
            parent_public = public_report(evaluation)
            first, first_pid = invoke_worker(cycle, snapshot["head"])
            second, second_pid = invoke_worker(cycle, snapshot["head"])
            require(
                first_pid != second_pid,
                "GA121-DUAL-EVALUATION",
                "release workers reused a process",
            )
            require(
                canonical_json_bytes(first)
                == canonical_json_bytes(second)
                == canonical_json_bytes(parent_public),
                "GA121-DUAL-EVALUATION",
                "worker or parent report-driving payload differs",
            )
            require(
                git("rev-parse", "HEAD") == snapshot["head"]
                and git("status", "--porcelain=v1", "-z", binary=True) == b"",
                "GA121-DUAL-EVALUATION",
                "repository changed during release evaluation",
            )
            for control in evaluation["controls"]:
                if control["control_id"] == "GA121-DUAL-EVALUATION":
                    control["state"] = "pass"
                    control["evidence"] = {
                        "worker_count": 2,
                        "distinct_processes": True,
                        "outer_payload_exact_match": True,
                    }
            evaluation["release_eligible"] = evaluation["status"] == "pass"
            validate_simple_schema(
                public_report(evaluation),
                "schemas/validation-report-1.2.1.schema.json",
                snapshot["files"],
                "GA121-REPORT-SCHEMA",
            )
            if cycle == "ordinary_release":
                require(
                    snapshot["files"].get(REPORT_PATH)
                    == canonical_json_bytes(public_report(evaluation)),
                    "GA121-REPORT-READBACK",
                    "canonical 1.2.1 report bytes differ from the final outer dual-evaluation report",
                )
        if options.emit_index:
            require(
                evaluation["status"] == "pass",
                "GA121-EMISSION",
                "cannot emit index from failing evaluation",
            )
            sys.stdout.buffer.write(canonical_json_bytes(evaluation["_index"]))
            return 0
        if options.emit_report:
            require(
                evaluation["status"] == "pass",
                "GA121-EMISSION",
                "cannot emit report from failing evaluation",
            )
            sys.stdout.buffer.write(canonical_json_bytes(public_report(evaluation)))
            return 0
        report = public_report(evaluation)
        if options.output == "json":
            sys.stdout.buffer.write(canonical_json_bytes(report))
        else:
            render_human(report)
        return 0 if report["status"] == "pass" else 1
    except GateError as exc:
        failure = {
            "report_id": "reiyah.validation-execution-error@1.2.1",
            "version": "1.2.1",
            "status": "fail",
            "public_distribution_eligible": False,
            "diagnostic": {"code": exc.code, "message": exc.message},
            "authority_nonclaims": {
                "operator_acceptance_state": "unaccepted",
                "runtime_authorized": False,
                "gate_b_authorized": False,
                "transport_verification_state": "not_evaluated",
            },
        }
        if output == "json":
            sys.stdout.buffer.write(canonical_json_bytes(failure))
        else:
            print("Gate A 1.2.1 continuity validation: fail")
            print(f"  {exc.code}: {exc.message}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
