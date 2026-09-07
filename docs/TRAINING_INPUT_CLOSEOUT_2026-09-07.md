# Training-input checkpoint

Document ID: `reiyah.training-input-closeout.2026-09-07`

Version: `0.1.0`

Lifecycle status: `exploratory`

This engine-only checkpoint extends main
`4ebb8003d7456e1b3e16568483473db908ee0104`. The operator explicitly supplied
cloud authentication and authorized dataset/box access, continuing the prior
request for checked main integration. The canonical Gate A and separate Gate B
owner worktrees remain untouched. Start future repository work at the canonical
Reiyah root and resolve its actual branch before using this private export.

Read the [findings](TRAINING_INPUT_FINDINGS_2026-09-07.md). The complete file
inventory, separate enumeration, metadata binding, full checkpoint identity
comparison and upstream recipe inspection resolve the prior availability
question. They identify the concrete inputs that must be contained within each
training partition. No shared-training effect or new detector benchmark is
measured here.

## Replay and custody

Private custody is `~/.codex/reports/reiyah/training-overlap-2026-09-07/`.
The exact public input archive remains in the earlier developer-value task.
`private/sensor-request-2.private.jsonl.gz` is the final metadata request;
`private/sensor-inventory-1/` holds the complete observations and original
report. Public own aggregates and source pointers live under
`evidence/training-overlap/`. Per-file/per-log identifiers, datasets, checkpoint
bytes and upstream source payloads remain private.

The new `inventory_training_sensors.py` tool prepares the request and scans
declared immutable roots. It distinguishes missing, empty, nonregular,
unreadable-metadata, unresolved-link and multiple-copy states. A failed or
incomplete scan never writes `result.json`. Ten authored tests exercise these
boundaries, including validation-only availability and a truncated population.
The initial request was superseded after the path check was tightened; the
successful final request binds the final source bytes. No frozen predecessor
producer, training split or result was overwritten.

```sh
python -B tools/measure/inventory_training_sensors.py prepare \
  --meta /private/meta.tgz \
  --meta-sha256 db48746b10e3544d5ef619eaa3d687e3960626fe1b4422ed856711da5aa7325b \
  --splits evidence/nuscenes_splits_devkit.py \
  --splits-sha256 eab6fa5e2536a2a85bd9451fb35771833e262b4b96319a6b26fee1dce8f4e2cd \
  --output /new/request.private.jsonl.gz
python -B tools/measure/inventory_training_sensors.py scan \
  --request /private/sensor-request-2.private.jsonl.gz \
  --request-sha256 588a6fae1577ea378417885c46bb0b6fbce848b986a0a8dfd5ac3ac98a1585c7 \
  --root /read-only/dataset --output-dir /new/inventory
python -B -m unittest discover -s tests -p 'test_*.py' -v
python -B -m unittest discover -s tools/measure -p 'test_*.py' -v
python -B tools/measure/gate_b_check.py --json /new/development-check.json
```

The [execution record](../evidence/training-overlap/execution-0.1.0.json)
binds the actual checks and their scope. Historical replay rows retain their
existing reports; they were not freshly replayed for this file-inventory change.
No Gate A release validation or operator acceptance is inferred from these
Gate B development checks.

## Cloud closeout and next action

The existing GPU start operation finished with a capacity error, despite the
asynchronous submission command returning zero. That failure is retained.
A temporary CPU reader inspected read-only clones. Attaching both Ubuntu boot
volumes during startup caused an EFI-label conflict; detaching the source copy,
booting the reader and attaching the copy afterward resolved it. No original
disk contents were modified. Direct SSH was unavailable; the existing IAP
route worked without firewall changes.

The reader, its disposable boot disk and both clones were deleted. API readback
confirms their absence and the original VM remains stopped with its original
disks attached. `private/cloud-closeout-1.json` retains the exact resource
identities and readback; it is a publisher-performed observation.

Claim register [0.2.26](../evidence/claim-status-register-2026-09-07T160458Z.json)
carries all 52 earlier claims and adds two scoped claims. Only the existing
shared-training claim's explanatory notes and evidence paths change; its
`not_established` status and forbidden scientific use remain. Its original
register is preserved.

Next: build partition-contained training inputs and verify actual loader and
geometry behavior, then freeze the fitting/calibration budget before new
outcomes. Exact initialization exposure and GPU capacity remain unresolved.
The independent reference study still has zero human judgments. Gate A remains
operator-unaccepted. Resolve the final main commit and push readback from Git
and this task's private `delivery.json`; no UI/UX change is part of this work.
