# Audit cost and resource scope

Document ID: `reiyah.roadmap-audit.cost-description`. Version: `0.1.0`.
Lifecycle status: `exploratory`. Dated 19 September 2026.

[costs.json](costs.json) records the exact cutoff and measured intervals.
Instrumentation begins at 16:16:58 UTC. Earlier task reading occurred; its exact
start and total useful effort are not inferred. The completed ten-hour mission
and the separate timing-witness closeout are untouched. This audit does not
restart either clock or include their costs as newly incurred work.

There were 32 search queries in eight calls and 40 direct source retrievals,
including three failed responses. Retained HTTP response bodies total
9,940,583 bytes. These are scholarly pages and HTML papers, not datasets, images,
models or new runtime dependencies. Response-body bytes exclude HTTP/TLS overhead;
the gzip response is charged as received, with decoded reading text stored
separately. No third-party payload bytes enter public Git.

The ledger separates elapsed durations for Git setup, source retrieval, web
search and recorded commands. It computes the union of recorded UTC intervals
instead of summing overlapping work into a false whole-session duration. Those
UTC interval lengths and separately sampled monotonic durations can differ
slightly; they are identified as different measurements. These elapsed values
are not CPU usage, active reasoning time or human work. Many file
reads, edits and tool overhead were not instrumented; a complete useful-effort
total and monetary costs remain unknown. No saving is estimated from query
counts or invented rates.

The 250 MiB ceiling covers new non-checkout artifacts. Checkout size is reported
separately; retained source packets are referenced without copying their data.
Free space stays above the 5 GiB floor. There are no new model calls, image reads,
reserved outcomes, paid compute jobs or delegated agents. Session billing is not
measured by this ledger.

The public snapshot stops before its own accountant finishes. That accountant,
final integrity/consistency checks, integration, push/readback and closeout have
separate private receipts. The final owned CLOSEOUT reports those additions; this
snapshot is not presented as the full cost of publication or the mission.
