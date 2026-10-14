# A checked partial prefix remains an incomplete observation

Document ID: `reiyah.multiorg.abrupt-termination-audit`. Version: `0.1.0`.
Lifecycle status: `exploratory`. 14 October 2026.

The original complete-pair checker refused the disk-floor termination because
SIGKILL left no structured worker final record. That refusal and the worker's
files remain unchanged. A separate post-stop auditor now checks the evidence
that actually persisted, without manufacturing the missing final record.

## Observed result

One network-denied saved-file audit completed in 6.25 seconds outer wall time,
within its 300-second budget. It verified all 69 original freeze bindings before
and after, reconstructed the 312 prospective tensors for this image, and checked
the exact failed-supervisor receipt, materialized worker policy and retained
2,450-file inventory.

All 70 consecutive Faster tile captures and their 70 persisted admissions passed.
Their 2,310 arrays contain 1,272 raw final-output rows. The checks cover exact
array names, bytes, dtype, shape and payload digests, input identities, explicit
proposal origin, direct-removal selection, and scalar per-tile projection.
No orphan, torn or unqualified file was found in this retained inventory.
No YOLO tile was captured. Missing work remains unknown.

The audit reports **zero complete model endpoints and zero complete pairs**.
It does not run a model, perform whole-image NMS, match references or derive a
ranking. Seventy checked captures provide a lower bound on returned forward
outputs; exact total starts, total completions and any in-flight state remain
unknown. The status is `failed_attempt_saved_tiles_audited`, preserving the
original failed attempt.

## Qualification and scope

Seventeen authored controls passed before the actual audit. They cover altered
source/process bindings, output identity, invalid geometry, missing and duplicate
ordinals, torn arrays and JSON, missing or invalid admission receipts, orphan
files, symlinks, inventory changes and attempts to promote a partial result.
One control starts an authored fixture writer, waits for its READY marker and
sends SIGKILL to that exact owned child. The saved prefix is then checked without
a terminal record. This is a narrow process control, not production-supervisor
reproduction or filesystem crash-durability qualification.

Two qualification failures are retained: a test f-string syntax error, then a
macOS `/var` versus `/private/var` fixture-path mismatch. Both were corrected
before the successful controls and single actual audit. No production evidence
or frozen pair checker was changed. The auditor reuses the exact qualified
per-tile checker; this is internal assisted checking, not independent neural
execution or scientific replication.

The complete audit remains private because it indexes retained prediction files.
Its SHA-256 is `54ed1a141a6f6b7e2fe1db794b791286c9f3d401d2f21fbb8c4ccd29e4aa4399`.
The [result summary](result.json) and [provenance](provenance.json) bind its
execution, code, qualification and input inventory. No new image/model inference
was performed after the resource stop.

## Replay

From the repository root, in the qualified NumPy environment:

```sh
python -B research/multiorg-reference-admission/0.6.0/postmortem/test_audit_partial.py
```

The controls create temporary authored fixtures and one temporary child process.
They use no dataset payloads, model inference or network. The public replay
executes the same 17 controls. The operational next dependency remains
[storage capacity and stability](DECISION.md).
