#!/usr/bin/env python3
"""Offline development closure for the named, privately retained source probes.

Checks custody and the declared probe observations, not browser correctness,
scientific truth, Gate A release eligibility or operator acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(path.read_text())


def verify(task, owner_readback=False):
    impl, baseline = task / "implementation", task / "baseline"
    public = impl / "evidence/interface-evidence"
    own_result = "evidence/interface-evidence/closure-0.1.0.json"
    navigation = {"README.md", "docs/SESSION_HANDOFF.md", "docs/GATE_B_SESSION_HANDOFF.md",
                  "docs/RESEARCH_CONTINUATION_2026-09-07.md"}
    unchanged, changed = [], []
    for source in sorted(baseline.rglob("*")):
        if not source.is_file():
            continue
        rel = source.relative_to(baseline).as_posix()
        require((impl / rel).is_file(), f"predecessor_removed:{rel}")
        if source.read_bytes() != (impl / rel).read_bytes():
            require(rel in navigation, f"predecessor_changed:{rel}")
            changed.append(rel)
        else:
            unchanged.append(rel)
    require(set(changed) == navigation, "navigation_delta")
    for capture, output in [("console-probe-4-original", "original-probes-0.1.0.json"),
                            ("console-probe-5-repair", "repair-probes-0.1.0.json")]:
        process = read(task / "checks" / (capture + "-process.json"))
        require(process["exit_code"] == 0, f"failed_process:{capture}")
        require(process["producer_sha256"] == sha(impl / "tools/measure/probe_console_evidence.mjs"), "producer_digest")
        for kind in ["stdout", "stderr"]:
            require(process[kind + "_sha256"] == sha(task / "checks" / (capture + "." + kind)), "stream_digest")
        require((public / output).read_bytes() == (task / "checks" / (capture + ".stdout")).read_bytes(), "public_probe_copy")
    original = read(public / "original-probes-0.1.0.json")
    repaired = read(public / "repair-probes-0.1.0.json")
    require(len(original["controls"]) == 12 and len(repaired["controls"]) == 14, "probe_row_counts")
    require(sum(r["result"] == "contract_violation_reproduced" for r in original["controls"]) == 8, "original_failures")
    require({r["id"] for r in repaired["controls"] if r["result"] == "contract_violation_reproduced"} == {"F02", "F03", "F04"}, "remaining_failures")
    require(sum(r["result"] == "repair_control_passed" for r in repaired["controls"]) == 5, "repaired_cases")
    require(sum(r["result"] == "positive_control" for r in repaired["controls"]) == 6, "repair_positive_controls")
    for item in [original, repaired]:
        require(item["console_validation_status"] == "not_established", "console_validation_overclaim")
    repair = read(public / "private-repair-0.1.0.json")
    require(repair["owner_application"] == "not_applied", "owner_application_overclaim")
    require(repair["patch_sha256"] == sha(task / "private/console-repair.patch"), "repair_patch_digest")
    require(repair["typecheck"]["exit_code"] == 0, "typecheck_failed")
    require((public / "external-sources-0.1.0.json").read_bytes() == (task / "external-sources/source-ledger.json").read_bytes(), "external_ledger_copy")
    for source in read(public / "external-sources-0.1.0.json")["sources"]:
        require(source["gate_a_evidence_eligible"] is False, "external_eligibility_overclaim")
        require(source["sha256"] == sha(task / "external-sources" / (source["id"] + ".html")), "external_source_digest")
    gate = read(public / "gate-b-check-0.1.0.json")
    require(all(r["state"] in ["pass", "not_run_here"] for r in gate["checks"]), "gate_b_check_failure")
    require(len(gate["items"]) == 52, "transcript_count")
    replay_counts = {}
    for row in gate["items"]:
        expected_state = "argv_unrecorded_historical" if row["replay_class"] == "argv_unrecorded_historical" else "not_replayed_here"
        require(row["replay_state"] == expected_state, "replay_state_overclaim")
        replay_counts[expected_state] = replay_counts.get(expected_state, 0) + 1
    owners = {}
    for name, source in read(task / "private/source-capture.json")["sources"].items():
        for row in source["files"]:
            require(sha(task / "private" / name / row["path"]) == row["sha256"], f"captured_source_changed:{row['path']}")
        owners[name] = dict(captured_head=source["state_before"]["head"], source_files_verified=len(source["files"]),
                            owner_state_readback="not_requested")
        if not owner_readback:
            continue
        root = Path(source["directory"])
        def git(*args):
            return subprocess.check_output(["git", "-C", str(root), *args]).decode()
        index = Path(git("rev-parse", "--git-path", "index").strip())
        if not index.is_absolute():
            index = root / index
        state = dict(head=git("rev-parse", "HEAD").strip(), branch=git("branch", "--show-current").strip(),
                     status=git("status", "--porcelain"), index_sha256=sha(index))
        require(state == source["state_before"], f"owner_state_changed:{name}")
        for row in source["files"]:
            require(sha(root / row["path"]) == row["sha256"], f"owner_source_changed:{row['path']}")
        owners[name].update(owner_state_readback="unchanged", head_branch_status_index_unchanged=True)
    additions = [p.relative_to(impl).as_posix() for p in impl.rglob("*")
                 if p.is_file() and not (baseline / p.relative_to(impl)).exists()
                 and p.relative_to(impl).as_posix() != own_result]
    bound = {}
    for rel in sorted(additions + changed):
        source = impl / rel
        bound[rel] = sha(source)
        if source.suffix == ".md":
            for link in re.findall(r"\]\(([^)]+)\)", source.read_text()):
                destination = link.split("#")[0]
                if destination and not re.match(r"^[A-Za-z]+:", destination):
                    require((source.parent / destination).exists(), f"broken_link:{rel}:{destination}")
    return dict(artifact_id="reiyah.interface-development-closure.0.1.0", version="0.1.0", mode="development",
                status="pass", gate_a_release_evidence=False, operator_acceptance="unaccepted",
                console_owner_patch_applied=False, unchanged_predecessor_files=len(unchanged),
                modified_predecessor_navigation=changed, source_snapshot_readbacks=owners,
                original_probe_rows=12, repair_probe_rows=14, remaining_reproduced_failures=["F02", "F03", "F04"],
                inherited_replay_states=replay_counts, bound_candidate_files=bound,
                limits=["Artifact/source closure and declared controls only", "No new Gate A release replay",
                        "No browser integration or human scientific review",
                        "Owner-state equality is a readback at this run, not a lock on future work"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--owner-readback", action="store_true", help="also require the live owners to remain at the original captured state; omit for future frozen-artifact replay")
    args = parser.parse_args()
    try:
        result = verify(args.task_root.resolve(), args.owner_readback)
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(json.dumps({"status": "fail", "reason": str(error)}))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
