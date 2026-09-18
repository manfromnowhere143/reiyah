# Cached content audit costs

Version `0.1.0`. Retained command measurements, not full engineering or human
review costs. Exact boundaries and all preparation attempts are in
[summary.json](summary.json); later packaging/check/readback receipts remain
in the private mission ledger.

| Phase | Outer process seconds |
| --- | ---: |
| Full original-file row audit and physical-view creation | 88.878509000 |
| Separate full-row decoding and verification | 89.589805208 |
| Frozen timing/extent follow-up | 3.033344833 |
| Follow-up verification against original files | 5.089698000 |

The original audit's internal timer is 88.121450542 seconds; its verifier's
is 88.898304417. These nest inside the outer processes. Peak resident memory
is 589,185,024 bytes for analysis and 393,101,312 for the separate decoder
check, as reported by macOS. Both fit the declared three-file/one-million-row
and 1,200-second phase limits.

Five preparation control attempts are retained. The first failed because a
generic Arrow metadata rewrite removed a non-Arrow key. A later full
synthetic pipeline failed because the generic writer changed a UInt32
physical type. The final footer-only operation passes 34 controls and the
complete synthetic packet, retaining both first failures. The follow-up's
seven controls also exercise a complete three-file pipeline. These preparation
costs are not discarded or folded into a success-only timer.

The concrete public-source follow-up used 18 requests and 2,391,215 response
body bytes, within its 32-request/64-MiB cap. This includes the denied task
response and primary reader/format documentation. Mission response bodies
now total 230,321,747 bytes, within the 2-GiB acquisition cap. These body
counts exclude protocol overhead, browser/web search and Git transport.

The preliminary nullable-list reader probes retain separate internal timers:
direct read 0.721037542 seconds, explicit-schema read 0.000561583 and list-type
override 0.000359750, all failed. The early synthetic physical-view read takes
0.382268375 seconds. Those duration-only records do not establish additional
nonoverlapping wall intervals. Full source acquisition, publication, earlier
experiments and mission-wide overlap accounting belong to the mission cost
reconciliation, not an invented sum of nested timers.

New image reads, model calls and training are zero. Earlier local exports
remain 146 model calls with 11.847570214 charged inference seconds. Publisher
CUDA timing charts and throughput are external measurements, not this mission's
inference cost. Human seconds, invoices, complete economics and useful work
outside retained command boundaries remain unmeasured. No speedup or saving
is inferred from these audit times.
