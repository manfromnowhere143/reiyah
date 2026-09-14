"""Seal an exchange packet with an origin this lane can stand behind.

The comparator 0.1.0 packet carried a blanket sentence saying every payload came
from the distributed commit. Seventeen did. The eighteenth was a status file this
lane generated at seal time, declared under a repository path that holds different
bytes at that commit, and the sentence made the whole packet's source binding
false. A consumer stopped there, correctly, before reading anything else.

The repair is not a promise to be careful. Every payload is classified and the
classification is checked against Git:

  committed   a repository path is declared, the path exists at the declared
              commit, and the payload bytes equal that blob exactly.
  generated   no repository path is declared. The payload is what it is, with a
              digest and no claim of provenance beyond this seal.

A payload that declares a repository path whose blob differs is a refusal, not a
warning, and no manifest is written. A generated payload is never described as
committed, and there is no sentence anywhere that speaks for all payloads at once.

The same seal also holds the transport boundary the repository already states in
`docs/STATUS_MODEL.md` and RGA-020. A publisher cannot verify its own transport. A
fresh clone taken by the publisher, from the publisher's own push, is publisher
readback: it rules out a working tree or index discrepancy and nothing else. The
comparator 0.2.0 manifest called exactly that an independent transport
verification, which is a state this repository reserves for a separately
authorized observation. Every manifest now carries
`transport_verification_state: asserted_unverified`, and a header that claims
independent transport is refused rather than corrected in prose later.

Standard library only. Reads Git through `git cat-file`; writes nothing but the
manifest and its digest.
"""
import hashlib
import json
import os
import subprocess
import sys

VERSION = "0.2.0"


TRANSPORT_STATE = "asserted_unverified"
TRANSPORT_CLAIM = "independent_transport"


class SealError(Exception):
    """The packet cannot be sealed with an accurate origin."""


def refuse_transport_claim(header):
    """A publisher may not label its own readback an independent verification."""
    text = json.dumps(header or {}, sort_keys=True).lower()
    for phrase in ("independent_transport", "independently transported",
                   "independent transport"):
        if phrase in text:
            raise SealError(
                "the header claims independent transport verification. A publisher's own clone "
                "of its own push is publisher readback; an independent transport state needs a "
                "separately authorized observation record. See docs/STATUS_MODEL.md and RGA-020")


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def blob_at(repository, commit, path):
    """The exact committed bytes, or None when the path is not in that commit."""
    result = subprocess.run(["git", "-C", repository, "cat-file", "blob", f"{commit}:{path}"],
                            capture_output=True)
    return result.stdout if result.returncode == 0 else None


def classify(directory, declared, repository, commit):
    """One record per payload, with its origin established rather than asserted."""
    records, refusals = [], []
    for name in sorted(os.listdir(directory)):
        if name.startswith("MANIFEST"):
            continue
        with open(os.path.join(directory, name), "rb") as handle:
            data = handle.read()
        entry = {"outbox_file": name, "byte_size": len(data), "sha256": digest_bytes(data)}
        path = declared.get(name)
        if path is None:
            entry["origin"] = "generated"
            entry["repository_path"] = None
            entry["note"] = "produced at seal time; no committed source is claimed for it"
        else:
            committed = blob_at(repository, commit, path)
            entry["repository_path"] = path
            if committed is None:
                entry["origin"] = "declared_path_absent"
                refusals.append(f"{name}: {path} is not in {commit}")
            elif committed != data:
                entry["origin"] = "declared_path_differs"
                entry["committed_sha256"] = digest_bytes(committed)
                entry["committed_byte_size"] = len(committed)
                refusals.append(f"{name}: bytes differ from {commit}:{path}")
            else:
                entry["origin"] = "committed"
                entry["verified_against"] = f"{commit}:{path}"
        records.append(entry)
    return records, refusals


def seal(directory, repository, commit, declared, header=None):
    """Write the manifest, or refuse and write nothing."""
    refuse_transport_claim(header)
    records, refusals = classify(directory, declared, repository, commit)
    if refusals:
        raise SealError("origin could not be established for: " + "; ".join(refusals))
    manifest = dict(header or {})
    manifest.update({
        "seal_version": VERSION,
        "source_commit": commit,
        "transport_verification_state": TRANSPORT_STATE,
        "transport_boundary": ("a publisher's own readback of its own push. It rules out a "
                               "working tree or index discrepancy and establishes no independent "
                               "transport observation"),
        "origin_policy": ("every payload is classified. A committed payload was compared byte for "
                          "byte against its blob at this commit. A generated payload claims no "
                          "committed source. No statement here covers all payloads at once"),
        "payload_counts": {
            "committed": sum(1 for r in records if r["origin"] == "committed"),
            "generated": sum(1 for r in records if r["origin"] == "generated")},
        "files": records,
    })
    text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    with open(os.path.join(directory, "MANIFEST.json"), "w", encoding="utf-8") as handle:
        handle.write(text)
    seal_digest = digest_bytes(text.encode("utf-8"))
    with open(os.path.join(directory, "MANIFEST.sha256"), "w", encoding="utf-8") as handle:
        handle.write(f"{seal_digest}  MANIFEST.json\n")
    return {"manifest_sha256": seal_digest, "payloads": len(records),
            "committed": manifest["payload_counts"]["committed"],
            "generated": manifest["payload_counts"]["generated"]}


def main(argv):
    if len(argv) != 5:
        sys.stderr.write("usage: seal_outbox.py OUTBOX_DIR REPOSITORY COMMIT DECLARED.json\n")
        return 2
    with open(argv[4], "r", encoding="utf-8") as handle:
        spec = json.load(handle)
    try:
        result = seal(argv[1], argv[2], argv[3], spec.get("declared", {}), spec.get("header"))
    except SealError as error:
        sys.stderr.write(f"refused: {error}\n")
        return 1
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
