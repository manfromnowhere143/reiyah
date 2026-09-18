# Retained mission cost reconciliation

Version `0.1.0`. Status `exploratory`. This is accounting of completed work,
not another outcome comparison or a test of economic savings.

Freeze the source inventory and implementation before producing a snapshot.
Include every root-level JSON receipt in the active packet's `logs`, all
physical download lines and their retained response bodies, every inference
line and exact request, runtime/image custody receipts, publication receipts,
and the published result/cost summaries. New snapshots use new freezes and
directories; an earlier snapshot is never silently extended or overwritten.

Normalize one event per physical request or outer process. A STARTED receipt
and its COMPLETED receipt describe one attempt. Copied review timers are aliases,
not new work. Physical download lines remain distinct even when an early receipt
identifier was accidentally reused. Exact decimal durations and integer
microsecond timestamps avoid arithmetic rounding of retained values.

Report the union of observed outer intervals, duration sums, overlap and
category totals separately. Category unions overlap and cannot be added into
a global union. Duration-only records lack intervals and never enter that
union. Monotonic process durations and UTC timestamp differences are different
measurements; retain both without forcing them to match. None measures CPU
time, full session work or human review. An unmeasured interval stays unknown.

Check every source byte binding, pair each started/completed phase, verify
prediction-call membership and cumulative charges, and verify inference
intervals are inside their corresponding launches. Report nested matching,
native proof and verification costs separately from outer costs. Previously
published cost summaries are references, never additional physical events.
Preserve failed attempts and distinguish a failed command from an intentionally
rejected fault probe inside a successful test suite. HTTP/transport status does
not establish semantic success or source admission. Retain application errors
carried by successful HTTP responses separately.

Download accounting concerns received body bytes, including errors and repeated
content. Also report unique content bytes; never use deduplication to reduce
the charged resource budget. Network headers, outbound requests, Git traffic,
unmetered browser/search traffic and historical assets remain unmeasured.
Read source responses only as inert data. Do not open images or reserved data.

Controls must reject negative/nonfinite/bool durations, malformed/non-UTC or
reversed timestamps, duplicate physical events, unknown event properties,
missing/extra allocated calls, cumulative-charge drift, escaped source paths,
source tampering and incomplete phase pairing. Compare interval union against
an independent sweep implementation on exhaustive small synthetic intervals.
Retain first failures and corrections. Run the default research consistency
check before publication. This is not Gate A release validation or independent
scientific replication.

All 1,433 reserved images remain closed. No inference, training, installation,
paid compute or new third-party payload acquisition is needed for accounting.
Human work, full economics, customer demand and savings remain unknown.
