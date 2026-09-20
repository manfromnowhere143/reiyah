# Measured costs and boundaries

Document ID: reiyah.continuous-envelope.costs-note. Version 0.1.0.
Lifecycle status: exploratory.

The [machine ledger](costs.json) separates completed source, execution, checking,
control and packaging receipts through its stated cutoff. Both actual runs
together cost 0.246243584 outer-process seconds; their separate actual checks
together cost 0.210207459. The first control suite failed and cost 1.880039583;
the corrected suite cost 1.872006625. These distinct tasks and repeated checks
are not matched latency trials or independent evidence counts.

Five public source captures retain 2,187,752 bytes; PDF text extraction adds
96,827 derived bytes. Source and derived bytes stay private. Owned mutation
copies and the preserved initial projection are included in artifact accounting.
The fresh Git checkout is counted separately; a shared Git metadata warning is
retained without unrelated cleanup. Ceilings are 8 MiB of sources, 128 MiB of
new artifacts, 600 seconds each of execution and checking, and a 5 GiB free floor.
Point storage samples do not prove unseen peak memory or disk use.

Nested retrieval, child-process, control and publication timings are retained
without adding them twice to their parent envelopes. Timed setup Git commands
and tool reports lacking complete UTC placement remain separately identified.
The public cutoff excludes this write and later consistency/integration/readback;
the private FINAL_COSTS and final confirmation receipts retain those later costs.

The failed precision-forgery test, pre-freeze lint failure and three mistaken
read-only paths remain. Neither actual case execution failed or hit a cap.
Active engineering effort, reviewer time, charges, energy, peak process memory
and complete workflow cost remain unknown. No savings ratio or padded useful
hours are claimed; the original closed ten-hour assignment is not restarted.
