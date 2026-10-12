#!/usr/bin/env python3
"""Named-case mutation challenges for the separate exact-choice verifier.

Inputs are the frozen producer's four canonical named records. Every mutation
and checker response is preserved in the caller's private work directory.
This script imports the checker solely for its explicit label-domain challenges;
all trace/protocol challenges invoke a fresh checker subprocess.
"""

import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode = True
import verify


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--named", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, default=verify.DEFAULT_PROTOCOL)
    args = parser.parse_args(argv)
    started = time.monotonic()
    args.workdir.mkdir(parents=True, exist_ok=False)
    results = []
    protocol = verify.load_protocol(args.protocol)
    raw = gzip.decompress(args.named.read_bytes())
    lines = raw.splitlines(keepends=True)
    if len(lines) != 4:
        raise verify.Rejection("control_setup: expected exactly four named records")
    base = [json.loads(line) for line in lines]
    if b"".join(verify.canonical(record) for record in base) != raw:
        raise verify.Rejection("control_setup: input is noncanonical")

    def challenge(name, data=raw, changed_protocol=None, expect_failure=True, fragment=None,
                  compressed_mutation=None):
        remaining = 150 - (time.monotonic() - started)
        if remaining <= 0:
            raise verify.Rejection("resource_limit: controls 150-second cap")
        trace = args.workdir / (name + ".jsonl.gz")
        compressed = gzip.compress(data, mtime=0)
        if compressed_mutation is not None:
            compressed = compressed_mutation(compressed)
        trace.write_bytes(compressed)
        selected_protocol = args.protocol
        if changed_protocol is not None:
            selected_protocol = args.workdir / (name + ".protocol.json")
            selected_protocol.write_bytes(verify.canonical(changed_protocol))
        output = args.workdir / (name + ".verification.json")
        command = [sys.executable, str(Path(verify.__file__).resolve()),
                   "--named-only", "--named", str(trace), "--protocol", str(selected_protocol),
                   "--output", str(output)]
        run = subprocess.run(command, capture_output=True, text=True, timeout=remaining)
        (args.workdir / (name + ".stdout.txt")).write_text(run.stdout)
        (args.workdir / (name + ".stderr.txt")).write_text(run.stderr)
        receipt = json.loads(output.read_bytes()) if output.exists() else {}
        failure = receipt.get("failure", "")
        correct = (run.returncode == 1 and receipt.get("status") == "invalid" and
                   (fragment is None or fragment in failure)) if expect_failure else (
                       run.returncode == 0 and receipt.get("status") == "supported")
        results.append({"id": name, "expected": "reject" if expect_failure else "accept",
                        "matched": correct, "exit_code": run.returncode, "failure": failure,
                        "input_sha256": hashlib.sha256(trace.read_bytes()).hexdigest()})

    def mutate(name, edit, fragment):
        records = copy.deepcopy(base)
        edit(records)
        challenge(name, b"".join(verify.canonical(record) for record in records), fragment=fragment)

    challenge("known-good", expect_failure=False)
    modified = copy.deepcopy(protocol)
    modified["population"]["grid"].append({"n": 1, "k": 4})
    challenge("extra-protocol-population", changed_protocol=modified, fragment="protocol_hash")
    modified = copy.deepcopy(protocol)
    modified["named_cases"].pop()
    challenge("omitted-protocol-case", changed_protocol=modified, fragment="protocol_hash")
    modified = copy.deepcopy(protocol)
    modified["unexpected"] = True
    challenge("unknown-protocol-property", changed_protocol=modified, fragment="protocol_hash")

    # Majority case averages all permutations. Stable row order breaks this.
    def wrong_tie(records):
        record = records[1]
        n = len(record["candidates"][0]["prediction"])
        for w, labels in enumerate(verify.domain(n)[0]):
            for model, candidate in enumerate(record["candidates"]):
                order = sorted(range(n), key=lambda row: candidate["ranks"][row])
                cumulative = area = 0
                for row in order:
                    previous = cumulative
                    cumulative += int(candidate["prediction"][row] != labels[row])
                    area += previous + cumulative
                record["risks"][w][model] = area
    mutate("wrong-tie-averaging", wrong_tie, ".risks")

    def right_endpoint(records):
        record = records[2]
        n = len(record["candidates"][0]["prediction"])
        for w, labels in enumerate(verify.domain(n)[0]):
            for model, candidate in enumerate(record["candidates"]):
                cumulative = area = 0
                for row in sorted(range(n), key=lambda row: candidate["ranks"][row]):
                    cumulative += int(candidate["prediction"][row] != labels[row])
                    area += 2 * cumulative
                record["risks"][w][model] = area
    mutate("right-endpoint-metric", right_endpoint, ".risks")
    mutate("omitted-model", lambda x: x[0]["candidates"].pop(), ".candidates:length")
    mutate("omitted-history", lambda x: x[0]["histories"].pop(), ".histories:length")
    mutate("boolean-integer", lambda x: x[0]["risks"][0].__setitem__(0, False), ":type")
    mutate("changed-bound", lambda x: x[0]["histories"][0]["bounds"][0].__setitem__(0, 999), ".bounds")
    mutate("changed-winner", lambda x: x[3]["histories"][0].__setitem__("winner", 1), ".winner")
    mutate("changed-certificate", lambda x: x[0]["certificates"].__setitem__(0, 99), ".certificates")
    mutate("changed-policy-cost", lambda x: x[0]["policy_queries"].__setitem__(0, 99), ".policy_queries")
    mutate("changed-fixed-cost", lambda x: x[0]["fixed_queries"][0].__setitem__(0, 99), ".fixed_queries")
    mutate("changed-width-cost", lambda x: x[0]["width_queries"].__setitem__(0, 99), ".width_queries")
    mutate("changed-tree-depth", lambda x: x[0]["histories"][0].__setitem__("depth", 99), ".depth")
    mutate("changed-tree-query", lambda x: x[0]["histories"][0].__setitem__("query", 99), ".query")
    mutate("unknown-record-property", lambda x: x[0].__setitem__("extra", 0), ":keys")
    mutate("wrong-case-identity", lambda x: x[0]["id"].__setitem__(2, "unlisted"), ".id")
    mutate("unavailable-trace-label", lambda x: x[0]["candidates"][0]["prediction"].__setitem__(0, None), ":type")
    mutate("boolean-trace-label", lambda x: x[0]["candidates"][0]["prediction"].__setitem__(0, False), ":type")
    mutate("missing-prediction-field", lambda x: x[0]["candidates"][0].pop("prediction"), ":keys")
    def swap_unknown_and_observed_zero(records):
        history = records[0]["histories"]
        history[0], history[1] = history[1], history[0]
    mutate("unknown-versus-observed-zero", swap_unknown_and_observed_zero, ".histories")
    challenge("truncated-population", b"".join(lines[:-1]), fragment="trace_truncated")
    challenge("noncanonical-spacing", b" " + raw, fragment="noncanonical")
    challenge("missing-final-newline", raw[:-1], fragment="noncanonical")
    challenge("extra-case", raw + lines[0], fragment="trace_extra")
    challenge("gzip-nonzero-mtime", fragment="gzip_header",
              compressed_mutation=lambda b: b[:4] + b"\x01" + b[5:])
    challenge("gzip-optional-filename", fragment="gzip_header",
              compressed_mutation=lambda b: b[:3] + b"\x08" + b[4:10] + b"trace.jsonl\x00" + b[10:])
    challenge("gzip-optional-comment", fragment="gzip_header",
              compressed_mutation=lambda b: b[:3] + b"\x10" + b[4:10] + b"comment\x00" + b[10:])
    challenge("gzip-truncated-trailer", fragment="end-of-stream",
              compressed_mutation=lambda b: b[:-4])

    for name, labels in (("none", None), ("missing", [0]), ("unknown", [0, None]),
                         ("negative", [0, -1]), ("boolean", [False, 1]),
                         ("string", [0, "1"]), ("float", [0, 1.0]), ("nonbinary", [0, 2])):
        rejected = False
        try:
            verify.validate_labels(labels, 2)
        except verify.Rejection:
            rejected = True
        results.append({"id": "strict-label-" + name, "expected": "reject", "matched": rejected})
    results.append({"id": "strict-label-valid-zero", "expected": "accept",
                    "matched": verify.validate_labels([0, 0], 2) == (0, 0)})
    report = {"artifact_id": "reiyah.exact-choice-baseline.controls", "version": "0.1.0",
              "protocol_sha256": verify.PROTOCOL_SHA256,
              "checker_sha256": verify.digest(verify.__file__), "controls_sha256": verify.digest(__file__),
              "named_gzip_sha256": verify.digest(args.named), "cases": results,
              "status": "supported" if all(r["matched"] for r in results) else "invalid"}
    args.output.write_bytes(verify.canonical(report))
    print(json.dumps({"status": report["status"], "checks": len(results)}))
    return 0 if report["status"] == "supported" else 1


if __name__ == "__main__":
    sys.exit(main())
