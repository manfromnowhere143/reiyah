# Resource admission for the remaining fixed comparison

Document ID: `reiyah.resource-admission.method-review`. Version: `0.1.0`.
Lifecycle status: `exploratory`. 14 October 2026.

The immediate problem is capacity, not detector selection. The last worker stopped
below its unchanged 4 GiB floor. Its receipt omitted the exact triggering free-byte
sample. A later host snapshot cannot recover that measurement or identify which
writer consumed the space. The next change must improve admission and observability
without converting incomplete model coverage into an endpoint.

## Primary-source findings

Apple's current APFS documentation describes shared capacity across volumes and
shared blocks between clones. Summing volume free space overcounts shared capacity;
summing file allocations does not measure exclusive physical ownership or predict
the bytes a deletion will reclaim. Keep logical size, reported allocated blocks and
filesystem available bytes as separate observations. Neither a clone nor a sparse
placeholder establishes exclusive capacity for a later computation.

The locally retained Python `shutil.disk_usage` implementation computes available
bytes as `f_bavail * f_frsize`. Use that measured value on the actual destination
filesystem. Do not substitute a user-interface estimate, inferred purgeable capacity
or a sum over APFS volumes. Apple's important-usage capacity key is a different API;
we did not establish that it provides an exclusive reservation and will not use it
to relax this gate.

Current uv documentation provides native cache maintenance and warns against manual
cache mutation. Its storage documentation includes environments in the cache, and
the CLI documentation warns that symlink installations can depend on cache contents.
Consequently, a large cache is only a candidate for recovery. Inventory its categories,
coupling and active consumers before choosing a native maintenance command. Preserve
model/data payloads, installed environments, research evidence and unrelated files.
The retained upstream symlink-deletion issue is closed; that fact alone is not proof
that the installed binary or a proposed invocation is safe.

## Engineering decision

Require a fixed capacity plan before the worker is launched. Admission requires the
unchanged floor, full prospective retained-output allowance and an explicit margin
at every preflight observation and again immediately before launch. Record all sampled
available bytes, timestamps and observation gaps in a bounded journal. Retain the
exact observation and reason for any stop; observation or journal failure refuses
the run. A stop reason cannot become success if the child exits zero during a race.

Use the same rule during execution with a conservative remaining-output allowance.
Record output logical bytes and reported allocated blocks, with file-count and walk
time bounds. Keep observer overhead and journal/log retention bounded. Maintain the
existing network-denied worker, time, sampled RSS and per-file limits. Kill only the
owned child. A process success still requires scientific output admission separately.

Repeated samples establish observed headroom over their interval. They do not prevent
other writers or guarantee capacity between samples. A tested monitor supplies better
failure evidence, not dedicated storage, hard real-time containment or scientific
superiority. This new supervisor requires explicit qualification against the pair
checker before it can supervise empirical work.

## Alternatives and falsification

- Native, bounded cleanup of demonstrably unused cache entries: first recovery option
  after custody checks; measure actual filesystem change rather than assuming size.
- Separate storage with sufficient capacity: appropriate if safe recovery is inadequate;
  requires byte-bound transfer and qualification of destination/runtime assumptions.
- Lowering the floor, removing retained results or selecting easier images: rejected.
- Preallocating a large placeholder on the nearly full shared volume: not selected;
  it consumes the scarce resource and does not solve unbounded competing writers.

The qualification must demonstrate prelaunch refusal without starting a worker,
recorded runtime capacity stops, malformed/missing sample refusal, bounded log/output
handling and retention of a stop despite a concurrent zero exit. The actual host must
then pass a separately frozen observation window and budget before an empirical plan
can be admitted. A failed host gate is an unresolved resource dependency, not a detector
or reference-comparison result.

## Retained sources

Eight fresh primary-source bodies total 380,502 bytes and remain private in `sources/`;
`sources/ledger.json` records URLs, access times, hashes and redistribution boundaries.
The local Python source is separately bound by `sources/LOCAL_SHUTIL.json`.

- [Apple: About Apple File System](https://developer.apple.com/documentation/foundation/about-apple-file-system)
- [Apple: shared file content](https://developer.apple.com/documentation/foundation/urlresourcevalues/maysharefilecontent)
- [Apple: important-usage capacity](https://developer.apple.com/documentation/foundation/urlresourcekey/volumeavailablecapacityforimportantusagekey)
- [Python: disk usage](https://docs.python.org/3.13/library/shutil.html#shutil.disk_usage)
- [pip: caching](https://pip.pypa.io/en/stable/topics/caching/)
- [uv: cache maintenance](https://docs.astral.sh/uv/concepts/cache/)
- [uv: storage locations](https://docs.astral.sh/uv/reference/storage/)
- [uv: reported cache symlink escape](https://github.com/astral-sh/uv/issues/19542)
