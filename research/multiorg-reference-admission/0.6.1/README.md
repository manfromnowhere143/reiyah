# Resource admission before another detector attempt

The supervisor now refuses inadequate capacity before launching a worker and
records the exact measurements behind a resource stop. Forty-four authored
controls pass. A separately frozen check of the actual destination filesystem
then refused launch: 2,719,948,800 bytes were available against a 7,825,578,224-byte
admission threshold. No worker or detector inference started.

This addresses the missing resource observations in the [previous interrupted
attempt](../0.6.0/README.md). It does not complete that attempt or the four-image
comparison. All previously selected images, model variants, numerical methods
and reference procedures remain unchanged.

## What changed

- Preflight and immediate prelaunch samples must cover the unchanged 4 GiB floor,
  full output allowance, allocation-rounding allowance and explicit margin.
- Running samples preserve the exact triggering available-byte reading and check
  the remaining allowance. Missing observations, excessive gaps and write errors
  prevent success. Logical size and reported allocated blocks remain distinct.
- A worker exiting zero cannot overwrite a recorded resource stop. Missing final
  output cannot become an empty or completed observation.
- Receipt publication first writes and file-syncs an exclusive pending file,
  then creates the final link without overwrite. A failed sync does not publish
  a final receipt. Consumers still require the supervisor's successful outer
  execution and matching journal; a final-looking file alone is insufficient.

The [supervisor contract](monitor/README.md) states the bounded journal, output,
RSS, wall-time and file-size behavior. Observations are sampled. APFS capacity is
shared, and file allocation counts do not establish exclusive occupancy. No
reservation, continuous enforcement, arbitrary descendant containment or
power-loss durability is claimed.

## The actual host check

The probe used a harmless authored worker and the real system observation
provider. Its prospective plan allowed 256 MiB of output, a 3 GiB margin and
10,000 files, above the unchanged 4 GiB floor. On this filesystem the rounding
allowance was 40,950,000 bytes. The margin is an explicit engineering allowance,
chosen equal to the existing empirical RSS ceiling; it is not a proved bound
on swap growth or other writers.

The first observation failed admission. Three journal rows retain preflight,
stop and final measurements. Worker PID remained absent and the output directory
was never created. Seventeen frozen bindings were unchanged. This is a measured
capacity refusal, not evidence that a future run has stable headroom.

The read-only storage audit found about 6.24 GB of reported uv cache allocation,
including nine cached environments and two open cache-lock descriptors. That
cache was not qualified for deletion. Smaller enumerated caches total about
600 MB, insufficient even to reach the bare floor at the observed free-space
level. No separate external writable volume was observed. No cache, research
evidence or unrelated file was removed, and no other process was stopped.

Read the [exact result](result.json), [storage summary](storage-summary.json),
[methods and alternatives](METHODS.md), [source ledger](sources.json),
[review](review/CODE_REVIEW.json) and [provenance](provenance.json).

## Reproduction and limits

On macOS, in the retained Python 3.14.2 standard-library environment, run from
the repository root:

```sh
python3 -B research/multiorg-reference-admission/0.6.1/monitor/test_supervise.py
python3 -B research/multiorg-reference-admission/0.6.1/review/adversarial_controls.py \
  --supervisor research/multiorg-reference-admission/0.6.1/monitor/supervise.py \
  --archive /tmp/reiyah-resource-controls-new \
  --report /tmp/reiyah-resource-controls-new.json
```

The suites execute 24 and 20 authored cases, using tiny fixture workers and
explicitly marked injected resource observations. Each real child enters the
retained network-denial policy. The host observer must remain outside that
worker sandbox so it can sample RSS. The first development invocation wrapped
the observer too and failed; its log is retained. Earlier receipt-persistence
controls also motivated the pending-file correction before the actual probe.
These are internal checks, not independent scientific replication.

The new receipt schema still requires a qualified downstream pair-checker
adapter before empirical use. Adequate capacity and a fresh bounded execution
freeze are also required. The original comparison still needs four complete
image pairs and twelve reference cases. This milestone establishes neither
scientific superiority, complete-work savings nor Gate A operator acceptance.
