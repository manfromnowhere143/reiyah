# Measured costs and cutoffs

Document ID: reiyah.frontier-expansion.cost-report. Version 0.1.0.
Lifecycle status: exploratory.

The [public snapshot](costs.json) ends at 2026-09-20T12:57:46.397016Z.
It contains 43 timed intervals: their recorded-duration sum is 44.884927915 seconds;
the union of their UTC envelopes is 42.762462 seconds. Coarse web envelopes
overlap some command activity. The totals are partial instrumentation, not
active engineering time, total task duration or a bill.

| Measured category | Outer duration, seconds |
| --- | ---: |
| Candidate setup, 14 commands | 1.963735001 |
| Source batches, including failed relative-path launch | 15.227921249 |
| Authored execution | 0.067796708 |
| Separate allocated checking | 0.063765000 |
| Controls, including failed nested-sandbox harness | 1.915561416 |
| Corrected supervisor/binding harness | 0.597456375 |
| Packaging before snapshot | 0.048692166 |
| Ten coarse web-tool envelopes | 25.000000000 |

Both scientific process categories remain below their separate 600-second
cumulative caps. The corrected harness is recorded under the supervisor's
`online` category because its network-denial child must start outside a parent
macOS sandbox; it performs no retrieval. Scientific execution and checking
entered the denial policy before Python startup. This snapshot precedes the
later whitespace/freeze correction documented in [correction.json](correction.json).
Both executions total 0.140959375 seconds and both checks total 0.125685875.
The failed staging attempt, corrected binding checks and later costs remain in
the final local closeout; no algorithm or case outcome changed.

All 27 direct retrieval attempts remain: 23 HTTP-200 bodies and four failures.
HTTP 200 alone does not establish a usable paper or article. The source bodies
occupy 3,479,463 bytes, including retained error pages. New study artifacts at
the snapshot total 4,445,614 bytes against 134,217,728 allowed. The checkout
is separately 35,858,996 bytes; free space is 24,108,744,704 bytes against a
5 GiB floor. Later publication/readback changes those sizes and costs.

Per-source timers, control subprocesses and later Git/readback subcommands are
nested measurements, not additional work to add to their outer receipts.
Untimed interpretation, authoring, exploratory reads/edits, initial discovery,
human work and whole-session billing remain unknown. No useful seconds,
dollar savings, human observation savings or empirical latency advantage are
inferred. No new inference/training, paid compute or reserved-image access ran.

The first known instrumentation is 2026-09-20T12:26:53Z; actual user-turn start
is unknown. This work does not restart the completed ten-hour assignment.
Its original start 2026-09-17T22:28:16Z and excluded 44,963.785396 seconds remain
historical accounting.

The current cost-snapshot command, later checks, integration, push/readback and
closeout are excluded from this committed snapshot. The owned packet's final
CLOSEOUT and cost events retain those later completed receipts. Failures are
charged where they occurred, not erased by successful retries.
