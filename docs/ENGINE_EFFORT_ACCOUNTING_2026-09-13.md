# What Engine's recorded command costs establish

Document ID: `reiyah.engine.effort-accounting`

Version: `0.1.0`

Lifecycle status: `exploratory`

The first fourteen closed checkpoints of the 13 September autonomous window contain **204
outer command records**. Their reported monotonic durations sum to **1,066.581210004165767142
seconds**. Their UTC intervals cover **996.660066 seconds**. Neither number measures total
engineering or human review effort. The selected clock span is **30,495.949062 seconds**, from
05:58:25 UTC to the member-equivalence closeout at 14:26:40.949062 UTC.

This changes how Engine costs should be consumed: select the original execution record, count
unsuccessful commands, retain nested details without adding their duration to their parent,
and report unmeasured effort explicitly. It supplies Engine's own evidence accounting, without
extending Fable's comparator or estimating which method wins on effort.

## Selection, comparison and result

The selected `WINDOW.json` and all fourteen closeouts were copied and bound before extraction.
All 5,922 closed file bindings, totaling 178,033,113 bytes, were checked. Each of the 204 canonical
`checks/<job>/receipt.json` records was then checked against its closeout, command specification,
original capture directory, supervisor and output streams. The public
[observations](../research/engine-effort-accounting/0.1.0/observations.json) contain the exact
recorded timing fields, execution identities and source digests; no capture payload or human
judgment is included. A second source reader compares every projected command field and
independently computes Decimal sums and a UTC endpoint sweep.

| Quantity | Result | Interpretation |
|---|---:|---|
| Canonical outer commands | 204 | 190 zero exits and 14 nonzero exits, all retained |
| Copied receipts | 124 | Same executions distributed in outboxes; not new runs |
| Nested viewer receipts | 33 | Synchronous child runs covered by three retained parent reproductions |
| Sum of reported monotonic durations | 1,066.581210004165767142 s | Recorded command intervals on their monotonic clock, not CPU or human time |
| Sum of reported UTC interval lengths | 1,066.615142 s | Separate local clock observations |
| Union of reported UTC intervals | 996.660066 s | Simultaneous intervals counted once |
| UTC overlap excess | 69.955076 s | UTC interval sum minus UTC union; no subtraction across clock types |
| Largest reported child RSS field | 298,909,696 bytes | Maximum of selected per-supervisor observations; not total system peak memory |
| Human and participant review effort | Unmeasured | Missing measurements do not become zero |

The 29,499.288996 seconds outside these captured UTC intervals are **uncovered by these
receipts**, not idle time. Editing, reasoning, source inspection, tool operations without this
supervisor and checkpoint preparation are incompletely captured. Chrome observation has no
receipt in this format; its duration and memory fields are null with an explicit missing
measurement state. This is not a complete ledger of all work or a detector comparison cost.

A competent conventional analyst can perform the same selection and ordinary timeline
accounting. The implementation offers a reproducible calculation, with no demonstrated speed
or effort advantage over that analyst. Summing every receipt file is retained as a deliberately
incorrect control, not presented as a competent baseline. Distinct executions are identified by
their source-bound capture paths; identical output bytes or timestamps alone do not identify
an execution. Missing source relationships must be resolved, not guessed from display names.

Nonzero exit status is not synonymous with a software defect. The retained stale-capture
command correctly rejects an incorrect binding. Other nonzero runs include missing dependencies,
an unsuccessful push, failed engineering probes and test failures. Each original transcript
remains available; no unsuccessful run was dropped from the selected cost total.

## Mathematical and platform boundaries

For reported UTC intervals `[s_i,e_i)`, the timeline quantity is the length of their union.
Sorting and merging overlapping or touching intervals computes this exactly on the stored
integer microsecond timestamps. The independent check sweeps endpoint multiplicities; the
tests compare both methods with direct occupied integer cells over all 1,024 subsets of ten
tiny intervals. These are exact calculations on recorded numbers, not clock calibration.

Recorded monotonic durations are parsed from their JSON decimal spelling and summed with
exact rational arithmetic. Those many decimal digits preserve the source representation;
they do not establish corresponding measurement accuracy. The existing supervisor stores
Python floating-point differences, reads the UTC clock separately and includes stream hashing
before its ending observations. Its intervals therefore do not isolate only the child process.
It does not record CPU time or validate clock adjustments, sleep behavior or scheduling load.

The selected runtime is Python **3.14.2** on macOS **14.4**. Its observed `get_clock_info` reports
`mach_absolute_time()` for monotonic time and adjustable `clock_gettime(CLOCK_REALTIME)` for
wall time. The official [Python time documentation](https://docs.python.org/3.14/library/time.html#time.monotonic)
describes the distinct clock semantics; the selected page displayed Python **3.14.7**, not the
executed runtime version. The [resource documentation](https://docs.python.org/3.14/library/resource.html)
describes `RUSAGE_CHILDREN` as terminated, waited-for child processes. The installed Apple SDK
`getrusage(2)` manual, internally dated 4 June 1993, specifies the RSS field in bytes; its
`clock_gettime(3)` manual, internally dated 26 January 2016, distinguishes clock domains.
Source dates are not installed OS versions. Exact source bytes, dates, access and redistribution
notes are retained privately in `SOURCE_LEDGER.json`; no third-party payload is redistributed.

Each outer receipt comes from a fresh supervisor running one command. Nested reproduction
receipts explicitly store a cumulative child RSS field and lack an ending UTC timestamp. They
remain details, with their parent relation checked through the command's output path and the
synchronous reproduction code. No child UTC end is manufactured by adding a monotonic duration
to a UTC start. Per-command memory maxima are neither additive memory consumption nor a
measurement of simultaneous total memory. Shared trusted components include the capture
supervisor, Python's JSON/time/resource facilities and the selected operating system.

## Failure, validation and next check

The first extractor assumed every outbox retained the complete `checks/<job>` display path.
Two consumer exchanges shorten it to `checks/receipt.json`; the first attempt stopped at that
assertion. The original failed extractor and transcript remain closed evidence. The correction
uses the copied command specification's original capture directory, requires exact agreement
with its canonical specification and checks the receipt bytes. It does not silently choose a
matching filename or discard a copy.

The standalone checks cover copied and nested records, distinct runs, missing measurements,
nonzero exits, overlapping intervals, exact decimals, malformed and reversed timestamps,
forged copy relationships, duplicate execution identities and JSON keys, and interface identity.
The complete retained timeline also passes the independent sweep. Repeated public analysis
produces byte-identical output. [Verification](../research/engine-effort-accounting/0.1.0/verification.json)
binds source, projection, output, failed and corrected preparation, tests and local command costs.
This audit's preparation costs are separate from the fourteen-checkpoint input selection.

No Engine runtime, admission, matching, viewer, reference interface or Fable source changed.
The prior 404 repository tests and 93 measurement tests remain retained with their source
bindings; they are not claimed as newly replayed. The bounded research audit has its own fresh
checks. No Gate A release evidence is created.

The next falsifier is an original execution omitted from the declared selection, a copied or
nested execution counted again, or a source-bound timing field that does not reproduce the
published calculation. More broadly, a fair detector comparison still needs prospective effort
records for preparation, verification, review, computation, integration and repair, for both
analysts using the same evidence and allowed methods. This retrospective Engine subset cannot
establish that comparison. The actual two-window enclosure remains **[-8,8]**; human reference
judgments, actual participant usability and external scientific review remain missing. Gate A
is unaccepted. P005 is operator-reported published; no further publication or outreach is authorized.
