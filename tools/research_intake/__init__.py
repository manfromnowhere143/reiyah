"""Offline research-proposal intake; structural readiness never grants authority.

Only the standard library is used. Source bytes establish identity and literal
quotation, not entailment, observation validity or scientific support. Every
assessment and observation qualification remains a supplied reviewer assertion.
"""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile

VERSION = "0.1.0"
MAX_RECORD = 1 << 20
MAX_SOURCE = 4 << 20
MAX_TOTAL = 16 << 20
IDENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")
WORK = re.compile(r"(?:arxiv:[0-9]{4}\.[0-9]{4,5}|doi:10\.[0-9]{4,9}/[a-z0-9._;()/:-]+|repo:github\.com/[a-z0-9_.-]+/[a-z0-9_.-]+|local:[a-z0-9][a-z0-9._/-]*)")


class Invalid(ValueError):
    def __init__(self, code, detail):
        self.code, self.detail = code, detail
        super().__init__(f"{code}: {detail}")


def require(ok, code, detail):
    if not ok:
        raise Invalid(code, detail)


def canonical(value):
    try:
        return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    except (ValueError, TypeError, RecursionError, UnicodeError) as exc:
        raise Invalid("JSON", "Cannot encode a finite bounded record") from exc


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def parse(data):
    require(type(data) is bytes and len(data) <= MAX_RECORD, "RECORD_SIZE", "Record exceeds 1 MiB")
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "DUPLICATE_KEY", key)
            result[key] = value
        return result
    def integer(token):
        require(len(token) <= 32, "NUMBER", "Oversized integer")
        return int(token)
    def bad_number(_):
        raise Invalid("NUMBER", "Use bounded integers; floats and nonfinite values are not admitted")
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=pairs,
                          parse_int=integer, parse_float=bad_number, parse_constant=bad_number)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise Invalid("JSON", "Invalid UTF-8 JSON") from exc


def fields(value, names):
    require(type(value) is dict and set(value) == set(names.split()),
            "FIELDS", "Missing or unknown properties")


def text(value, limit=4096, empty=False):
    require(type(value) is str and (empty or bool(value.strip())) and len(value) <= limit
            and "\0" not in value, "TEXT", "Invalid bounded text")


def ident(value):
    require(type(value) is str and IDENT.fullmatch(value) is not None, "ID", "Invalid identifier")


def integer(value, lo, hi):
    require(type(value) is int and lo <= value <= hi, "NUMBER", "Invalid bounded integer")


def sha(value):
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
            "SHA256", "Expected lowercase SHA-256")


def work(value):
    require(type(value) is str and len(value) <= 512 and WORK.fullmatch(value) is not None
            and ".." not in value.split("/"), "WORK_ID", "Expected canonical work identity")


def version(value):
    ident(value)
    require(value.lower() not in ("unknown", "latest", "main", "master", "head"),
            "VERSION", "A mutable or unknown version is not pinned")


def rows(value, maximum=128, nonempty=False):
    require(type(value) is list and (not nonempty or bool(value)) and len(value) <= maximum,
            "COUNT", "Invalid bounded collection")
    return value


def unique(values, code="DUPLICATE_ID"):
    require(len(values) == len(set(values)), code, "Duplicate identity")


def validate_mission(mission):
    fields(mission, "artifact_id schema_version project mission_id mission_version decision assumptions closure")
    require(mission["artifact_id"] == "research-intake.mission" and mission["schema_version"] == VERSION,
            "SCHEMA", "Unsupported mission schema")
    ident(mission["project"]); ident(mission["mission_id"]); version(mission["mission_version"])
    text(mission["decision"])
    assumptions = {}
    for row in rows(mission["assumptions"], nonempty=True):
        fields(row, "id description requires_observation")
        ident(row["id"]); text(row["description"])
        require(type(row["requires_observation"]) is bool, "TYPE", "requires_observation must be Boolean")
        require(row["id"] not in assumptions, "DUPLICATE_ID", "Duplicate mission assumption")
        assumptions[row["id"]] = row
    closure = mission["closure"]
    fields(closure, "state reason prior_sources")
    require(closure["state"] in ("open", "closed"), "STATE", "Unknown closure state")
    text(closure["reason"])
    prior = []
    for source in rows(closure["prior_sources"], 128):
        fields(source, "work_id source_version sha256")
        work(source["work_id"]); version(source["source_version"]); sha(source["sha256"])
        prior.append((source["work_id"], source["source_version"], source["sha256"]))
    unique(prior)
    require(closure["state"] != "closed" or bool(prior), "CLOSURE", "Closed mission needs its prior source identities")
    return assumptions, prior


def source_bytes(root_fd, relative, size):
    text(relative, 1024)
    parts = relative.split("/")
    require(not relative.startswith("/") and "\\" not in relative
            and all(p not in ("", ".", "..") for p in parts), "SOURCE_PATH", "Expected a root-relative path without traversal")
    fd = os.dup(root_fd)
    try:
        for part in parts[:-1]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd); fd = next_fd
        opened = os.open(parts[-1], os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW, dir_fd=fd)
        with os.fdopen(opened, "rb") as stream:
            require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), "SOURCE_TYPE", "Source is not a regular file")
            data = stream.read(size + 1)
        require(len(data) == size, "SOURCE_SIZE", "Source byte size differs")
        return data
    except OSError as exc:
        raise Invalid("SOURCE_PATH", "Missing source, symlink or invalid source path") from exc
    finally:
        os.close(fd)


def validate_sources(sources, root_fd):
    catalog, payloads, identities, total = {}, {}, [], 0
    for source in rows(sources, 64):
        fields(source, "id work_id source_version sha256 byte_size path role captured_at access terms disposition reason")
        sid = source["id"]; ident(sid); work(source["work_id"])
        require(sid not in catalog, "DUPLICATE_ID", "Duplicate source identifier")
        require(source["role"] in ("abstract", "full_text", "code", "metadata"), "STATE", "Unknown source role")
        require(source["disposition"] in ("included", "excluded", "unavailable"), "STATE", "Unknown screening disposition")
        for field in ("access", "terms", "reason"): text(source[field])
        captured = source["captured_at"]
        require(type(captured) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z", captured), "TIME", "Expected a UTC capture timestamp")
        try: datetime.fromisoformat(captured.replace("Z", "+00:00"))
        except ValueError as exc: raise Invalid("TIME", "Invalid calendar timestamp") from exc
        if source["disposition"] == "unavailable":
            require(all(source[k] is None for k in ("source_version", "sha256", "byte_size", "path")),
                    "UNAVAILABLE", "Unavailable bytes cannot carry invented local identities")
        else:
            version(source["source_version"]); sha(source["sha256"])
            integer(source["byte_size"], 1, MAX_SOURCE)
            total += source["byte_size"]
            require(total <= MAX_TOTAL, "SOURCE_BUDGET", "Source bytes exceed 16 MiB")
            data = source_bytes(root_fd, source["path"], source["byte_size"])
            require(hashlib.sha256(data).hexdigest() == source["sha256"], "SOURCE_DIGEST", "Source bytes differ from pinned digest")
            try: data.decode("utf-8")
            except UnicodeError as exc: raise Invalid("SOURCE_UTF8", "Evidence sources must be UTF-8 text") from exc
            identities.append((source["work_id"], source["source_version"], source["sha256"]))
            payloads[sid] = data
        catalog[sid] = source
    unique(identities, "DUPLICATE_SOURCE")
    return catalog, payloads, total


def validate_evidence(evidence, catalog, payloads):
    spans = {}
    for span in rows(evidence, 256):
        fields(span, "id source_id source_version source_sha256 start_byte end_byte quote kind")
        ident(span["id"]); ident(span["source_id"])
        require(span["id"] not in spans, "DUPLICATE_ID", "Duplicate evidence identifier")
        sid = span["source_id"]
        require(sid in catalog and catalog[sid]["disposition"] == "included", "EVIDENCE_SOURCE", "Evidence must reference an included source")
        source = catalog[sid]
        require(span["source_version"] == source["source_version"] and span["source_sha256"] == source["sha256"],
                "EVIDENCE_BINDING", "Evidence has a stale or different source identity")
        require(span["kind"] in ("method", "observation", "limitation"), "STATE", "Unknown evidence kind")
        integer(span["start_byte"], 0, len(payloads[sid]))
        integer(span["end_byte"], span["start_byte"] + 1, len(payloads[sid]))
        text(span["quote"], 65536)
        require(span["end_byte"] - span["start_byte"] <= 65536, "SPAN_SIZE", "Evidence span too large")
        require(payloads[sid][span["start_byte"]:span["end_byte"]] == span["quote"].encode("utf-8"),
                "EVIDENCE_SPAN", "Literal evidence does not match exact UTF-8 byte span")
        spans[span["id"]] = span
    return spans


def assess(mission, dossier, source_root):
    """Return a proposal-readiness diagnostic; no acquisition or code execution."""
    for record in (mission, dossier):
        require(len(canonical(record)) <= MAX_RECORD, "RECORD_SIZE", "Record exceeds 1 MiB")
    assumptions, prior = validate_mission(mission)
    fields(dossier, "artifact_id schema_version project mission_id mission_version mission_sha256 proposal retrieval sources evidence assessments reopening")
    require(dossier["artifact_id"] == "research-intake.dossier" and dossier["schema_version"] == VERSION,
            "SCHEMA", "Unsupported dossier schema")
    require(all(dossier[k] == mission[k] for k in ("project", "mission_id", "mission_version"))
            and dossier["mission_sha256"] == digest(mission), "MISSION_BINDING", "Dossier belongs to different mission bytes, version or project")
    proposal = dossier["proposal"]
    fields(proposal, "id technique comparator decision_impact falsifier cost")
    ident(proposal["id"])
    for k in ("technique", "comparator", "decision_impact", "falsifier"): text(proposal[k])
    fields(proposal["cost"], "engineering_minutes cpu_seconds source_bytes")
    integer(proposal["cost"]["engineering_minutes"], 1, 4800)
    integer(proposal["cost"]["cpu_seconds"], 1, 86400)
    integer(proposal["cost"]["source_bytes"], 0, MAX_TOTAL)
    retrieval = dossier["retrieval"]
    fields(retrieval, "state scope limitations")
    require(retrieval["state"] in ("complete", "incomplete"), "STATE", "Unknown retrieval state")
    text(retrieval["scope"])
    for value in rows(retrieval["limitations"], 64): text(value)
    require(retrieval["state"] != "incomplete" or bool(retrieval["limitations"]),
            "RETRIEVAL", "Incomplete retrieval needs an explicit limitation")
    try: root_fd = os.open(source_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError as exc: raise Invalid("SOURCE_ROOT", "Expected an existing nonsymlink source directory") from exc
    try: catalog, payloads, total = validate_sources(dossier["sources"], root_fd)
    finally: os.close(root_fd)
    spans = validate_evidence(dossier["evidence"], catalog, payloads)
    assessments, missing, incompatible = {}, [], []
    for row in rows(dossier["assessments"], 128):
        fields(row, "assumption_id state reason evidence_ids observation_state")
        aid = row["assumption_id"]; ident(aid)
        require(aid in assumptions and aid not in assessments, "ASSUMPTION_ID", "Unknown or duplicated assumption")
        require(row["state"] in ("compatible", "incompatible", "unknown"), "STATE", "Unknown compatibility state")
        require(row["observation_state"] in ("not_required", "qualified", "missing", "unqualified"), "STATE", "Unknown observation state")
        text(row["reason"])
        refs = rows(row["evidence_ids"], 64)
        for ref in refs: ident(ref)
        unique(refs)
        require(all(ref in spans for ref in refs), "EVIDENCE_REF", "Missing evidence reference")
        needs_observation = assumptions[aid]["requires_observation"]
        require(needs_observation or row["observation_state"] == "not_required", "OBSERVATION", "Unexpected observation qualification")
        require(not needs_observation or row["observation_state"] != "not_required", "OBSERVATION", "Required observations cannot be waived")
        strong = [spans[ref] for ref in refs if catalog[spans[ref]["source_id"]]["role"] in ("full_text", "code")
                  and (row["state"] != "compatible" or spans[ref]["kind"] != "limitation")]
        observed = [spans[ref] for ref in refs if spans[ref]["kind"] == "observation"
                    and catalog[spans[ref]["source_id"]]["role"] != "abstract"]
        if row["state"] == "incompatible": incompatible.append(aid)
        if row["state"] == "unknown": missing.append({"assumption": aid, "reason": "assessment_unknown"})
        if row["state"] != "unknown" and not (strong or (needs_observation and observed)):
            missing.append({"assumption": aid, "reason": "full_text_code_or_required_observation_support_missing"})
        if needs_observation and (row["observation_state"] != "qualified" or not observed):
            missing.append({"assumption": aid, "reason": "qualified_observation_record_missing"})
        assessments[aid] = row
    for aid in sorted(set(assumptions) - set(assessments)):
        missing.append({"assumption": aid, "reason": "assessment_missing"})
    if retrieval["state"] == "incomplete": missing.append({"reason": "retrieval_incomplete"})
    reopen = dossier["reopening"]
    fields(reopen, "state source_ids rationale")
    require(reopen["state"] in ("not_requested", "proposed"), "STATE", "Unknown reopening state")
    text(reopen["rationale"])
    refs = rows(reopen["source_ids"], 64)
    for ref in refs: ident(ref)
    unique(refs)
    require(all(ref in catalog and catalog[ref]["disposition"] == "included" for ref in refs),
            "REOPENING", "Reopening references must be included sources")
    require(reopen["state"] != "not_requested" or not refs, "REOPENING", "Unrequested reopening cannot supply a basis")
    prior_hashes = {p[2] for p in prior}
    used_evidence = {ref for row in assessments.values() for ref in row["evidence_ids"]}
    new_basis = [sid for sid in refs if catalog[sid]["sha256"] not in prior_hashes
                 and (catalog[sid]["work_id"], catalog[sid]["source_version"], catalog[sid]["sha256"]) not in prior
                 and any(spans[ref]["source_id"] == sid for ref in used_evidence)
                 and catalog[sid]["role"] != "abstract"]
    changes = [{"source_id": sid, "identity_change":
                "same_work_version_different_bytes" if any(p[:2] == (catalog[sid]["work_id"], catalog[sid]["source_version"]) for p in prior)
                else "version_and_bytes_changed" if any(p[0] == catalog[sid]["work_id"] for p in prior)
                else "new_work_identity"} for sid in new_basis]
    closed = mission["closure"]["state"] == "closed"
    status = ("closed_no_new_basis" if closed and (reopen["state"] != "proposed" or not new_basis)
              else "incompatible" if incompatible else "needs_evidence" if missing else "ready_for_review")
    return {"artifact_id": "research-intake.assessment", "schema_version": VERSION,
            "project": mission["project"], "mission_id": mission["mission_id"], "mission_version": mission["mission_version"],
            "mission_sha256": digest(mission), "dossier_sha256": digest(dossier), "status": status,
            "missing": missing, "incompatible_assumptions": incompatible,
            "retrieval": retrieval, "screening": dossier["sources"], "source_bytes_checked": total,
            "assessments": dossier["assessments"], "proposal": proposal,
            "reopening": {"proposed": reopen["state"] == "proposed", "candidate_changed_source_ids": new_basis,
                          "identity_changes": changes},
            "boundaries": {"literal_source_bytes_verified": True, "semantic_entailment_verified": False,
                           "observation_validity_verified": False, "scientific_support_established": False,
                           "material_novelty_verified": False, "rights_verified": False, "source_metadata_verified": False,
                           "mission_currentness_verified": False, "temporal_eligibility_verified": False,
                           "build_authorized": False, "reopening_authorized": False,
                           "assessment_basis": "supplied_reviewer_assertions_and_structural_checks",
                           "retrieval_complete_means": "declared_bounded_scope_only_not_exhaustive_literature",
                           "source_versions_mean": "provided_pinned_identities_not_externally_verified_current_versions",
                           "qualified_observation_means": "dossier_reviewer_assertion_not_tool_established_channel_validity",
                           "cost_basis": "proposed_next_test_resource_caps_not_measured_work"}}


def read_record(path):
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as stream:
            require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), "RECORD_TYPE", "Expected a regular record file")
            return parse(stream.read(MAX_RECORD + 1))
    except OSError as exc:
        raise Invalid("RECORD_PATH", "Cannot read record without following symlinks") from exc


def write_new(path, value):
    """Atomic no-overwrite output; never replace a preexisting identity."""
    target = Path(path)
    try: fd, temporary = tempfile.mkstemp(prefix=".research-intake-", dir=target.parent)
    except OSError as exc: raise Invalid("OUTPUT", "Cannot create output in the specified directory") from exc
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(canonical(value)); stream.flush(); os.fsync(stream.fileno())
        os.link(temporary, target)
    except OSError as exc:
        raise Invalid("OUTPUT", "Cannot create a new output; existing files are never overwritten") from exc
    finally:
        os.unlink(temporary)
