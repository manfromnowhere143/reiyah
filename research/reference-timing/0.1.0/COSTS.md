# Known process costs and retained failures

Version `0.1.0`, 18 September 2026. Times are measured local process wall times,
not human review or complete economic costs.

| Phase | Process seconds | Scope |
| --- | ---: | --- |
| Preceding metadata extraction | 55.448330375 | Source hashing, complete streamed tables and scoped joins |
| Declared projection model | 3.078273333 | All 64 images, 1,035 current car records and numerical checks |
| Bounds and attained worlds | 2.832030166 | All four contracts, 8,426 candidate evaluations, matching and native proofs |
| Separate verification | 2.759913166 | Source geometry, 115 native proofs, full cases and retained unknowns |

Within analysis, native graph compilation takes 0.389930496 seconds, proof
production 0.007709585 and native checking 0.007043256. These are nested inside
analysis; do not add them again. Search reuse across identical census contracts
is charged once. The figure and publication scripts are separate measured
phases, not inference.

The snapshot in [summary.json](summary.json) includes 20 completed named
processes, including failed controls and rendering. Their summed process time
is 87.753702872 seconds; the union of their timestamped intervals is
85.439222336 seconds. Two synthetic/control processes overlap. The cutoff is
16:24:25 UTC; the next summary write, repository consistency, review and push
are retained in later private receipts rather than hidden inside this snapshot.
Interactive source/code review, engineering effort, billing and complete human
costs are not fully measured. These numbers do not establish total-work savings.

Retained first failures and corrections:

- The first motion controls rejected a wrong SDK calling convention. The pinned
  exporter uses a module source variable; the adapter now restores that variable
  after each isolated call.
- The second controls rejected NumPy scalar outputs at the JSON boundary. The
  adapter now converts SDK scalars to finite JSON floats before validation.
- The first synthetic fault check correctly rejected a modified proof, but its
  expected diagnostic wording was wrong. The assertion now names the actual
  certificate rejection; the corruption remains rejected after cache reuse.
- The first SVG normalization assertion treated redundant path whitespace as a
  drawing change. Its original PNG/SVG and helper are retained. The corrected
  check preserves every path command/numeric token, other attribute and text;
  the final PNG was visually inspected. Scientific sources were not changed.

All actual-data projection, analysis and verification phases completed on their
first attempts. Missing motion and unavailable union membership are retained
input states, not successful measurements or analysis failures.

No new model call, image read, installation or asset download occurred. Session
asset acquisition remains 227,930,532 bytes and charged inference time remains
11.847570214 seconds. Reused acquisition/export costs remain in the
[predecessor cost record](../../public-predictions/0.1.0/COSTS.md); they are not
zeroed by reuse. The unverified overnight session gap stays excluded from useful
work. All 1,433 reserved images remain closed. Human prices, customer demand and
an owner-accepted decision criterion remain unknown.
