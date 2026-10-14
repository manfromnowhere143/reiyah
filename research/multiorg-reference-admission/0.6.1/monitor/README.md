# Resource admission supervisor, 0.1.0

This is a separate host supervisor for one owned, byte-bound worker. It retains
the historical supervisor unchanged. Qualification here covers authored resource
controls and harmless fixture workers; it does not authorize or execute detector
inference. The new process receipt is intentionally not presented as compatible
with the historical saved-pair checker.

The observer runs on the host. Its worker alone enters the retained
`sandbox-exec` policy with network denied before Python starts. The worker keeps
the supplied Python entrypoint, a 600-second maximum declared wall limit, a
3 GiB maximum declared sampled RSS limit, CPU limits and a 64 MiB kernel
per-file size limit. Killing targets only the live PID created by this
supervisor. This does not contain arbitrary descendants or impose a hard
address-space limit.

## Capacity contract

The new mandatory `--capacity-plan` and `--capacity-plan-sha256` bind an exact
JSON object with these fields:

```json
{
  "artifact_id": "reiyah.resource-admission.capacity-plan",
  "version": "0.1.0",
  "free_disk_floor_bytes": 4294967296,
  "output_budget_bytes": 268435456,
  "margin_bytes": 3221225472,
  "max_output_files": 10000,
  "preflight_samples": 3,
  "sample_period_seconds": 0.2,
  "max_sample_gap_seconds": 2
}
```

These example values are a prospective budget, not an observed admission.
The floor cannot be lower than 4 GiB; booleans cannot stand in for numeric
budgets. Every required preflight sample and the final prelaunch sample must
admit the full floor, output allocation allowance and margin. A failed capacity,
binding or observation check prevents launch.

`output_budget_bytes` caps the logical bytes in the worker output directory,
worker log, resource journal, policy and process receipt. The allocation
allowance adds `max_output_files * (statvfs.fragment_bytes - 1)` for file
rounding. Two transient 64 KiB receipt links and the next 8 KiB journal row are
reserved in live output checks. Shared filesystem metadata, snapshots,
compression, clone extent sharing and exclusive physical occupancy remain
unmeasured. The explicit margin is additional; the allowance is not a proof of
worst-case APFS physical consumption or eventual deletion yield.

During execution a separate bare-floor stop remains. A stronger new stop also
requires available bytes to cover the floor, remaining allocation allowance
and margin. Remaining allowance is the prospective allocation budget minus
the larger of observed logical and allocated bytes, floored at zero. This is
a new resource contract, not a claim that historical execution used it.

`statvfs.f_bavail * f_frsize` supplies observed available bytes. Purgeable space
is not added. Output observations use `st_size` and `st_blocks * 512`; they
must not be described as exclusive APFS allocation. Traversal is limited to
10,000 files and one second. Missing or erroneous disk/RSS observations remain
unknown and fail closed; sampling gaps and sample durations exceeding the
declared limit also fail closed. Samples do not reserve capacity or guarantee
the floor between observations.

## Records and acceptance

The bounded `.resources.jsonl` stream records preflight, before-launch, running,
stop and final observations when the sink remains writable. Each row is flushed
and file-synced. It carries sequence, wall-clock and monotonic timing, observation
errors, gap/duration, disk fields, logical/allocated output bytes and sampled
RSS. The process receipt preserves the exact triggering row and free-byte
value; a later final row never replaces that trigger.

The journal is limited to 8 MiB/8,192 rows, the log to a sampled 8 MiB and each
receipt to 64 KiB. A `.process.pending` file is created exclusively, written and
file-synced before no-overwrite hard-link publication to `.process.json`.
Only the owned pending file is then removed. A failed sync leaves no published
final receipt. A collision preserves the existing file. Failed cleanup returns
failure even if a final link already exists. No directory-sync, hardware-sync,
power-loss or crash-durability qualification is claimed.

Consumers must require successful outer execution, successful returned and
retained status, `receipt_persisted: true`, no stop cause, unchanged bound inputs,
a complete worker result and the exact hash-matched journal. A final-looking
file alone is insufficient. Worker exit zero cannot override an observed stop.
A missing terminal result is not an empty result. Process completion still
does not establish a scientific endpoint.

## Qualification and harmless system probe

Run `python -B monitor/test_supervise.py` with the host observer outside the
worker sandbox. Each actual fixture worker enters the exact network-denial
policy. Wrapping the host test itself in that macOS sandbox prohibits its
`/bin/ps` observation; the retained first development replay demonstrates that
the guard then fails closed.

The test API permits explicitly recorded `authored_injected` disk/RSS providers;
the CLI exposes no provider-injection option. Disk-fall controls do not fill the
disk. Scaled log and kernel file-size controls test those mechanisms with small
files; they do not write 64 MiB. The standalone `tiny_worker.py` is qualified for
a future, separately frozen system-mode admission probe. It sleeps briefly and
writes only an authored completion marker, with no datasets, models or network
calls. Such a probe is not a detector retry or permission to run one.

The CLI retains the old owner/manifest/worker/Python/output arguments and adds
the capacity-plan arguments. The manifest still binds protocol, images, models
and limits. New schema identity is
`reiyah.resource-admission.supervisor-receipt`, version `0.1.0`.

`QUALIFICATION.json` retains final source hashes, authored coverage and earlier
development failures. `READY.json` identifies the reviewed bytes. Neither
document converts capacity observations into a scientific claim or authority.
