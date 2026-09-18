# Known costs and unmeasured work

Version `0.1.0`. Snapshot: `2026-09-18T01:06:43.959225+00:00`. This is a cost snapshot of the first completed experiment during the ongoing ten-hour continuation, not its final duration or a measured economic total.

## Acquisition and bounded export

All 112 physical HTTP request receipts account for 227,930,532 received bytes, including failure bodies. Their summed request duration is 408.270013 seconds; requests sometimes overlap. Five receipts have unsuccessful HTTP status or a transport error. Other semantic failures, including JSON-RPC errors carried by HTTP 200, remain in the source qualification record and are not miscounted as successful packet admission.

An early concurrent receipt ordinal was reused; both physical payloads and their bytes count. Later acquisition uses a request-wide lock. No source bytes, weights or dependencies were downloaded after the two OpenCV diagnostic-source requests. Existing runtimes, imagery and annotations were reused; their historical acquisition costs are unknown.

All 146 staged calls consume 11.847570214 charged prediction seconds, of which 9.674367586 are instrumented forward time and 0.135535291 separate decoder checking. Those are nested durations. The charged ledger is conservative whole-call time, including preparation/decoding around each model call. Six successful stages cover one, eight and 64 images for each frozen checkpoint. The first failed launch was a pre-inference thread-contract check and is retained as a failed attempt, not a successful empty image.

The machine is the existing local arm64 Mac, macOS 14.4, 10 logical CPUs and 16 GiB memory; inference uses CPU FP32 with two PyTorch threads. No paid or cloud compute was purchased. The 2 GiB/60-minute limits are feasibility ceilings, not benchmark costs or a permission to omit preparation.

## Recorded process costs

| Phase | Outer process seconds |
| --- | ---: |
| All seven local export attempts | 31.607666 |
| Reference projection and archive scan | 278.271513 |
| Comparison packet preparation | 0.882730 |
| First assay attempt, failed before querying | 0.202324 |
| Completed four-arm assay | 24.926901 |
| Assay replay | 24.912712 |
| Full-answer search and query floors | 29.101349 |
| Full-answer verification | 0.875551 |
| Integrated 83-control suite | 1.875883 |

These outer durations include nested work. In particular, the projection includes its archive scan; the assay includes all workers, queries and proof/checking work; inference is already inside export-process time. Setup/import, runtime hashing, source acquisition, boundary probes, controls and failed attempts are retained individually in [costs.json](costs.json).

The union of all retained timestamped request/process intervals in this snapshot is **765.651417 seconds**. Their duration sum is 841.737583 seconds, which is not elapsed work because intervals overlap. Duration-only records without an exact interval remain separate; they are not added to the union. This union excludes uninstrumented coding, research, integration and review, so it is not the total session duration or total work.

## Actual comparison work

| Arm | Queries over 219 dependent rows | Resolved | Unresolved | Sum of row elapsed seconds | Nested proof generation | Nested proof checking |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 502 | 99 | 120 | 1.167061 | 0.000000 | 0.000000 |
| B | 502 | 99 | 120 | 10.881440 | 0.165299 | 0.147551 |
| C | 511 | 99 | 120 | 10.894324 | 0.166321 | 0.148556 |
| D | 511 | 99 | 120 | 1.162401 | 0.000000 | 0.000000 |

All arms receive equal observation/cache contracts and the same valid mathematics. The conventional path retains usable edges across reference deletions; the current native path compiles and checks its actual separate proof obligations. That implementation overhead is included. Proof/check columns are already part of each row duration; measurement/compilation counters also nest and must not be added again. Query service across the whole assay is 0.174562915 seconds, inside the assay duration. A query is a replayed public annotation lookup, not a timed human review.

Each case starts with an empty answer cache. The 73 cases and three contracts overlap; the union is only 64 prepared images, 60 of which are queried by each arm across the entire assay. Source preparation is shared equally. Summed rows are diagnostic work, not 876 independent customer decisions or 2026 independent images. Both-zero-query rows remain ties. A cost-per-resolved-decision with a zero denominator is undefined; none is converted into a favorable ratio.

## Failures and unknowns

Retained first failures include nullable Parquet decoding, protected public-source endpoints, a TLS hostname mismatch and an unavailable source mirror, unsafe archive-member rejection, actual Ultralytics settings-directory correction, OpenCV thread reporting, an exact-decimal eligibility counterexample, sandbox ancestor metadata, prohibited nested sandbox application, and two Python module-name collisions during replay/verifier development. Each correction preserves the original failing artifact. The first research consistency invocation preceded the cost document and correctly rejected its missing links; the completed document is checked again before publication. No test expectation or scientific criterion was weakened.

Unknown costs include full historical custody/setup, uninstrumented implementation and integration effort, reviewer/adjudicator work, actual customer delays, hardware depreciation, electricity, prices and billing. Session elapsed time is recorded separately in private SESSION/PROGRESS; it is not human review time. There is no total-work or economic savings estimate, no amortization over an invented customer revision sequence, and no evidence that the 3x/2x investment targets are met.
