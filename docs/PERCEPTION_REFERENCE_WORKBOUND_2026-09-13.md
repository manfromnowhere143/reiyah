# Keep the compiler: dense work-bound audit, 2026-09-13

The [audit](../research/perception-reference-workbound/0.1.0/README.md) disproved the suspected
missing edge-cost defect. The compiler emits unconditional edges, so the only graph-condition
literals charged by the evaluator belong to objects. The existing preflight is a conservative
upper bound on its declared work estimate. Production code, core limits and interfaces stay
unchanged. One new regression pins the adjacent dense-graph budget boundary.

The first falsifier used 64 synthetic worlds and a complete seven-detection graph, with 46
invariant objects and one world-varying object. Direct coordinate-based injections and
detection-count upper bounds establish the two anchors' +1/-1 losses and joint value zero.
The current compiler returns [0,0], improving on the selected pre-sharing baseline's [-1,0].
Its work is 1,830,336, below the preflight 1,830,848. The missing-cost hypothesis fails.

At 56 invariant objects, actual work is 1,994,176 and the finite result remains [0,0]. At 57,
the proposed bound exceeds the unchanged 2,000,000 limit. Sharing is declined, preserving the
mixed [-1,0] enclosure instead of forcing a global count-only fallback. Current and baseline
compiled inputs, compilation receipts and checked packets are byte-identical for that case.
This is conditional computational evidence; the dense geometry is not a physical observation.

All 391 repository tests pass in a fresh 53.47-second run, including the new boundary test.
The earlier 93 measurement tests are retained against 107 unchanged files, not replayed.
Probe processes run separately and their source/input/output identities, time and memory are
in [verification](../research/perception-reference-workbound/0.1.0/verification.json) and the
private checkpoint. Rejected assumptions, test warnings and original failures remain retained.
No latency comparison, human-effort advantage, scientific novelty or physical truth is claimed.

The chosen decision is to keep the existing bounded method. A more elaborate cost planner or
new compiler interface has earned no place through this audit. Fable's planner, checker and
reference-error model remain its separate lane; no new correction was selected or sibling
source/ref/status/outbox/process changed here. The prior scoped acceptance of its sealed
5762ac0 consumer repairs remains bound to that earlier Engine exchange.

The next useful question returns to practical observation: can a separately supported Chrome
connection provide an observable, bounded viewing action while the native desktop service is
unavailable? Inspect the official Chrome capability and its prerequisites once; do not repeat
the unchanged native bootstrap. If it offers no independent path, retain that limitation and
the existing manual viewer procedure. Do not build another viewer without a working observation
path or fabricate a human record. Actual participant return takes priority over preparation.

Real bounds [-8,8]; no admitted human references; participant usability and external scientific
review missing. Gate A unaccepted; physical study unrun with no cohort or seed. P005 is
operator-reported published; no further publication or outreach. The autonomous window continues.
