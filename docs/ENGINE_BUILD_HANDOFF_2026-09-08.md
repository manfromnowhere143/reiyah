# Engine build handoff

Document ID: `reiyah.engine-build-handoff.2026-09-08`

Version: `0.1.0`

Lifecycle status: `proposed`

This is a continuation checkpoint for the incoming engine session. Resolve live repository and
process state before acting. Recorded running states describe their observation time, not a
promise that the processes remain live when this document is read.

```json
{
  "project": "Reiyah",
  "canonical_root": "/Users/danielwahnich/workspace/reiyah",
  "public_remote": "https://github.com/manfromnowhere143/reiyah.git",
  "workstream": "offline engine research",
  "stop_request": "operator requested a proper checkpoint and machine-readable handoff",
  "primary_private_handoff": "~/.codex/reports/reiyah/training-cache-2026-09-08/private/HANDOFF.json",
  "private_task": "~/.codex/reports/reiyah/training-cache-2026-09-08/",
  "readme_repair_commit": "cddd73fc1f727555f84431ca1e19baa6692966a6",
  "completed": [
    "CPU and CUDA actual loss/head probes",
    "actual annotation parsers on fixed smoke population",
    "synthetic actual augmentation and object sampling controls",
    "full validation model caches and separate recount"
  ],
  "running_at_checkpoint": ["cache-train-1-1", "cache-train-2-1"],
  "not_started": ["training object databases", "four new detector fits"],
  "gate_a_operator_acceptance": "unaccepted",
  "independent_human_judgments": 0
}
```

## First actions

1. Verify the canonical root, remote, active worktrees and live main. Read `AGENTS.md` and the
   architecture handoff. Both existing owner worktrees are separate; use an isolated main export.
2. Read the private `HANDOFF.json`, including exact source/result hashes, retained command arrays,
   cloud/container IDs, resource changes, execution receipts and historical attribution request.
3. Inspect `checks/cache-train-1-1/receipt.json` and `checks/cache-train-2-1/receipt.json`. Absence
   means completion has not been recorded. Check the retained stdout tails and actual cloud
   containers before deciding whether to resume, wait or investigate. Do not launch duplicate
   builds or reuse output identities.
4. On successful completion, retrieve each original `result.json`, `samples.private.jsonl`,
   `model_infos.pkl` and `model_infos_mono3d.coco.json`. Match original stdout, file hashes and
   exact source group. Run the separate recount before admitting the group as complete.
5. Apply the explicit camera-decoding reporting correction from the
   [checkpoint](TRAINING_CACHE_CHECKPOINT_2026-09-08.md). Retain the original results unchanged.

## Next scientific dependency

Construct fresh object point databases from each matching training group. The historical
CenterPoint database recipe uses ten candidate sweeps with padding and near-origin point removal;
its test input recipe is a different nine-sweep policy. Preserve unknown velocity in the database,
record source membership and every selection/filter, check actual cropped point payloads, and
retain zero-point object entries explicitly. The private handoff records storage limits and
available source paths. No object database was created in this outgoing checkpoint.

Before detector fits, freeze the calibration/evaluation populations, initialization exposure,
common training-step budget, repeats and uncertainty design. Report joint-risk, marginal-product
and covariance contrasts separately, with absolute rates, coverage and unknown bounds. See the
[unchanged experiment design](TRAINING_OVERLAP_NEXT_EXPERIMENT_2026-09-07.md). A shared benchmark
or shared pretrained detector cannot be relabeled as independent training history.

## Repository, presentation and attribution

The README repair restores six Mermaid views and the complete architecture explanation while
retaining current scientific qualifications. Preserve that depth. Update demonstrated findings
and status precisely; do not replace the front page with a succession of review verdicts.

New commits must have Daniel Wahnich as author and committer, without AI coauthor trailers.
The private handoff also retains an outstanding operator request concerning historical
repository attribution, with exact history and its impact on shared commit identities.

Public Git receives own source and permitted aggregates only. Dataset tokens, sensor payloads,
model weights, raw review evidence, session transcripts and credentials remain private. The VM
is intentionally left available for the running cache jobs at this checkpoint. After retrieving
results, inspect fresh activity and restore its original stopped state if no incoming-session or
other owner job needs it. No new instance or disk was allocated in this task.
