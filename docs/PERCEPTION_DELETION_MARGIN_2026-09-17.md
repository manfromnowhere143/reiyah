# Checking minimum reference-deletion counts

Document ID: `reiyah.perception-deletion-margin`. Version: `0.1.0`.
Lifecycle status: `exploratory`.

## What this adds

The Engine supplies `deletion-margin` and `verify-deletion-margin` through the
[revision interface](../research/perception-revision/0.1.0/README.md). They check a
minimum adverse deletion count and a necessary lower bound on confirmed-present
observations. The checker uses explicit matchings and equal-size vertex covers;
it never invokes a matching algorithm, adversarial search or mixed-integer solver.
This separates proof verification from the research lane's choice of optimizer.

The method supports independent A/B output membership. The census consumed here
still compares a base with that base plus retained additions. An augmented output
is not the standalone output of the second detector.

## Census result

The preceding [consumer review](PERCEPTION_CENSUS_REVIEW_2026-09-17.md) checked
aggregate arithmetic and selected forty-frame proofs. This checkpoint checks
the actual graph inputs for the fixed population of 3,000 comparisons: twenty
ordered model pairs across 150 scenes. All 3,000 graph files match the copied
private index, and a separate strict readback checks their normalized inputs,
packets and result bindings.

| Checked outcome | Comparisons |
|---|---:|
| Supported baseline, exact minimum adverse deletion count and necessary confirmation bound | 1,125 |
| Baseline already excludes strict improvement | 1,865 |
| Existing work limit reached; no verdict verified by this method | 10 |

There are no disagreements with the research rows on any of the 2,990 evaluated
graphs: loss, criterion, counts, pool size and deletion floor all agree. Every
one of the 1,125 supported rows attains its floor, and its necessary-confirmation
bound agrees. The ten limited units were reported as excluded by research; that
classification is not independently verified here. Their identifiers remain in
the [verification record](../research/perception-revision/0.1.0/deletion-margin-verification.json).

Across the 1,125 supported comparisons:

| Quantity | p10 | Median | p90 |
|---|---:|---:|---:|
| Exact minimum adverse deletions | 3 | 27 | 106 |
| Minimum as share of included labels | 0.44% | 2.41% | 7.48% |
| Necessary confirmed-present observations | 35 | 131 | 289 |
| Necessary confirmations as share of included labels | 3.49% | 11.50% | 23.05% |

These are descriptive quantiles of dependent comparisons, not confidence
intervals or estimates for future driving. The maximum checked minimum is 575.
On the forty-frame Mapillary-base/Megvii-addition case, the proof checks a pool
of 354, an exact minimum of 49 and a necessary confirmation bound of 306.
The separate sufficiency checker is still needed to establish that a proposed
confirmed set actually settles the decision.

The consumer pass took 321.0 seconds: 289.2 in input preparation/admission,
17.45 in proof production and 7.04 in proof checking, plus remaining IO and
orchestration. Snapshotting took 3.8 seconds and subsequent byte/binding
readback 24.2 seconds. Other tests ran concurrently during part of the census.
These are local phase observations, not an isolated speed benchmark or avoided
inference/human work. The full preparation cost is not omitted.

The claims were selected from research commit
`7501c2f2e46baf23272564df924ce15fa005dda7`. The graph files also contain coordinates
from ongoing localization work; this consumer explicitly projects their declared
membership and edges, binds the extra source fields, and does not adopt localization
conclusions. The geometry fields are not silently converted into matching evidence.
Raw prediction/annotation joins were not rebuilt for every unit. Solver-derived
sufficient-audit upper bounds and random-trial rates were not replayed.

## The argument the checker verifies

Let `M_B` be a matching and `C_B` a vertex cover of the same size r in B's graph.
Every edge has an endpoint in the cover; every matching uses distinct endpoints.
These two facts prove that the maximum matching size is r without searching for
another matching.

Select a pool P of reference vertices in `C_B` with no incident A edge. Every such
vertex must be matched in `M_B`: otherwise removing it from the cover would leave
a cover smaller than the matching. For any subset S of P:

1. Removing S leaves a matching of size `r-|S|`.
2. Removing S from the original cover leaves a cover of size `r-|S|`.
3. Thus B's maximum matching decreases by exactly `|S|`.
4. A's graph loses no edges, so its maximum matching is unchanged.

With nonnegative loss penalties a and b and uniform positive anchor weight w,
each such deletion lowers the improvement by exactly `s=(a+b)*w`. A general
reference deletion can change each matching size by only zero or one, so it cannot
lower the improvement by more than s. For original improvement delta and strict
tolerance t, the lower bound on the number of adverse deletions is:

```text
k = ceil((delta-t)/s), when delta > t.
```

If the combined pool across all anchors has at least k members, any k-member
subset attains the bound. This proves an exact minimum and retains a concrete
adverse subset. The proof does not require A to be a subset of B.

If the pool has m members, any sufficient confirmed-present set must cover at
least `m-k+1` of them when the remaining-error budget permits k deletions.
Otherwise an unconfirmed k-subset remains an adverse interpretation. This is
only a necessary condition. Confirming one adverse witness, or merely meeting
this count, need not exclude other counterexamples. Contradictory audit answers
must be handled by the separate audit contract, not counted as confirmations.

This is established matching and cover reasoning applied to the declared loss.
It is not a novelty claim, a sufficient-audit optimizer or evidence of actual
label errors.

## Limits and trust boundary

This proof method requires one unconditional finite reference world, uniform
anchor weights, observed outputs and a positive loss step. Other inputs retain
`unsupported_scope` or `input_blocked`. If a pool is too small, attainment stays
`lower_bound_only`; an adverse set has not been established. A baseline already
at or below tolerance has minimum zero.

The existing input, graph, packet and work limits are unchanged. In addition to
the normal matching estimate, admission charges one `D_B+T+E` cover traversal per
anchor. Budget exhaustion reports `resource_limited`. No reference worlds,
anchors or difficult units are discarded to manufacture an exact result.

Shared trusted code includes strict input admission, rational arithmetic, the
scope/work policy and the matching/cover verifier. Producer and checker separately
calculate the result. Both verify declared graphs; source accuracy and physical
truth are upstream premises. The private census snapshot is consumer-bound and
is not a new research-owner campaign seal or a replay of every raw-source join.

## Validation and retained artifacts

The new controls enumerate 29,724 small-graph deletion/loss calculations using
independent partial injections. They include independent replacements, ambiguous
matching, every pool subset, strict equality, a shared deletion budget and
counterexamples to treating an adverse witness as a sufficient audit. Negative
controls reject forged matchings, covers, pools, results and packet bindings.
The checker still works with producer and matcher calls disabled.

The first targeted test run exposed two fixture defects: a manually miscounted
coverage total and missing required reasons in unknown/open test inputs. Their
receipts remain retained. The test fixtures were corrected; no mathematical
expectation or Engine admission rule was weakened. The corrected target suite,
492 repository tests, 93 measurement tests and four real CLI commands pass.

A first source readback also correctly failed when the rational-only native graph
parser encountered a source coordinate float. A separate source-JSON check now
admits finite coordinate numbers and rejects duplicate keys, nonfinite values and
non-JSON constants. The native parser is unchanged; only normalized exact-rational
graphs enter the Engine. Both readback attempts and the three parser rejection
controls are retained.

The private checkpoint is
`~/.codex/reports/reiyah/engine-deletion-margin-2026-09-17-3ydilss1/`.
Its PLAN fixes the population and falsifiers; SNAPSHOT binds all selected bytes;
GATE retains the forty-frame comparison and six rejecting mutation controls.
RESULTS and the per-unit packets distinguish checked, rejected and limited cases.
The final verification, closeout and seal bind the completed checkpoint.

No model inference, cloud compute, human audit, public post or outreach is part
of this work. Gate A remains unaccepted. Reduced total validation cost and
frontier superiority require the separate matched experiment described in the
[next-mission gates](REIYAH_NEXT_MISSION_2026-09-17.md).
