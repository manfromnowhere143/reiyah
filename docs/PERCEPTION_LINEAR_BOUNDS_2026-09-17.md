# Exact linear certificates for reference-position uncertainty

Document ID: `reiyah.perception-linear-bounds`. Version: `0.1.0`.

Lifecycle status: `exploratory`. Checked development calculation, 17 September 2026.

## Result

The Engine now checks rational linear-bound certificates without calling an optimizer.
On the retained forty-frame Mapillary base plus retained Megvii additions, the new
proof establishes a loss improvement of **at least 9/20 (0.45)** for every allowed
class-preserving planar reference shift of **at most 0.5 m**. The strict criterion
is improvement greater than 1/10. No additional position observations are supplied.

| Method on the same input and 0.5 m family | Checked interval | Criterion |
|---|---|---|
| Ordinary guaranteed/possible matching envelope | [-57/20, 153/10] | Unresolved |
| Shared-edge linear certificate and count upper bound | [9/20, 369/20] | Supported |
| Same linear certificate through the empty position-observation interface | [9/20, 369/20] | Supported; zero supplied observations |
| Same geometry and coefficients, tolerance changed to 1/2 | [9/20, 369/20] | Unresolved |

The improved lower bound resolves the decision; the upper bound is looser. Neither
interval endpoint is claimed to be attainable. This is not an exact worst-case
optimum, interval domination, a measured query saving or a complete-cost advantage.
The original 2,299 references, 738 additions, uniform 1/40 frame weights, unit
miss/false-positive penalties and strict 2 m same-class matching are retained.
Outputs, reference membership and classes stay fixed. These are exposed 2019–2020
benchmark outputs, not a new physical study or a calibrated error distribution.

## What is checked

For each anchor, let G- and G+ be the guaranteed and possible matching edges from
the exact geometric contract. Every admitted geometric realization has edges E
with G- contained in E contained in G+. Shared detections use the same edge-presence
variable on both sides of the comparison. Allowing independent uncertain edge
values is an outer relaxation: it includes potentially non-geometric graphs.

For the forward direction, introduce a vertex cover of B, a matching of A, and
one shared presence variable for each uncertain edge. All variables lie in [0,1].
The native program imposes these constraints:

- A B-cover must cover each present edge. A guaranteed edge requires the sum of
  its two cover variables to be at least one; an uncertain edge requires that
  sum to be at least its presence variable.
- An A-matching edge cannot exceed its presence variable. Each detection and
  reference has matching capacity one.
- The objective is the B-cover size minus the A-matching size. Detection and
  reference vertices have separate namespaces, even if their ID strings coincide.

Every actual graph has a feasible assignment formed from its minimum B-cover and
maximum A-matching. By bipartite matching/cover equality, that assignment's objective
is exactly `TP_B - TP_A`. Consequently a lower bound for the relaxation is a lower
bound for every admitted geometric realization. Swapping the roles bounds the
reverse difference. Independent A/B output membership is supported.

The Engine rebuilds sparse integer constraints `A*x >= b`, objective c, and the
ordered variables and rows. For any supplied nonnegative rational multipliers y,

```text
c*x >= b*y + sum_j min(0, c_j - (A^T*y)_j),   0 <= x_j <= 1.
```

This follows by adding `y*(A*x-b) >= 0` and minimizing each residual term over its
unit interval. Exact rational arithmetic avoids a numerical solver's tolerance.
Round the resulting lower bound up to an integer **per anchor**, then apply the
declared weights and the existing loss identity:

```text
delta = (false_negative + false_positive) * (TP_B - TP_A)
        - false_positive * (D_B - D_A).
```

Missing directions retain the common-output count bounds, tightened by the known
reference count. Empty certificates can be valid and uninformative. An inconclusive
relaxation neither proves a physical counterexample nor proves that a stronger
method cannot settle the decision.

Program version `shared_matching_box_lp.0.1.0`, canonical program digest, anchor and
direction bind the proposal. Unknown or duplicate subjects, missing multipliers,
negative/noncanonical/oversized coefficients, stale programs and forged conclusions
reject. Changed observations are conditioned first; a certificate must bind the
resulting program. A changed loss or tolerance always requires recomputing the
conclusion, even when the matching coefficients remain applicable.

## Interface and resource limits

See the [method README](../research/perception-revision/0.1.0/README.md#exact-linear-bounds)
and [certificate schema](../research/perception-revision/0.1.0/linear-certificate.schema.json).
The optional `--linear-certificate FILE --linear-certificate-sha256 SHA` works with
`localization` and `position-audit`. Existing verification commands check the
resulting packets. An explicit displacement and a universal linear certificate
cannot be supplied as the same method. Legacy commands keep their default behavior.

The standalone linear proof charges original geometry work plus a conservative
program estimate before construction. It does not also generate the old matching
proof. The 2,000,000 work ceiling is unchanged. Per requested anchor/direction,
the added estimate is `40 * (possible_edges + |A| + |B| + reference_count + 1)`.
Constructed rows, variables and sparse terms must fit that estimate. Certificates
retain the 4 MB input limit; multiplier numerators/denominators are at most 256 bits,
and intermediate rational numerators/denominators at most 4,096 bits.

The first assay tried to combine both proof methods and was rejected at 2,259,784
estimated work units. That failure is retained. The corrected standalone linear
path uses 521,340 geometry units plus 416,360 program units on this case. No ceiling
was raised. These counts are resource guards, not seconds or economic cost.

## Validation and displacement replay

All **542 repository tests pass**. Nine new tests include **4,608 independently
enumerated graph/role/direction cases**, explicit matchings and covers, colliding
left/right ID strings, malformed certificates, bounded arithmetic, conditioned
observations, reverse comparisons and unresolved fallback. The checker imports no
optimizer. Producer and checker still share schemas, exact geometry, the native
program builder and rational conventions; this is not independent scientific review.

The 14 targeted measurement regressions and default research consistency check also
pass. The latter binds 52 historical transcripts; it does not rerun those experiments.

Seven fresh CLI calls cover ordinary and linear production/verification, the empty
position-observation packet and rejection of a negative coefficient without writing
an output. Single-run local times were 2.91/1.41 seconds for ordinary production/check
and 3.02/1.49 seconds for linear production/check. Position production/check took
8.51/2.98 seconds. Optimizer/source acquisition and human effort are excluded, so
these are operation timings, not an economic benchmark or speed advantage.

The remaining 235 exhibited displacement requests were also checked:

| Closed per-record shift radius | Requests | Engine-checked witnesses | Work-limited |
|---|---:|---:|---:|
| 0.10 m, retained preceding post check | 44 | 44 | 0 |
| 0.25 m, retained preceding post check | 97 | 97 | 0 |
| 0.50 m, fresh replay | 128 | 127 | 1 |
| 1.00 m, fresh replay | 107 | 107 | 0 |

The total is **375 checked witnesses and one work limit**, combining the earlier
141 checks with 235 fresh attempts. The work limit is CenterPoint plus retained
PointPillars, scene-0105, radius 0.5 m (`LOCALIZATION_WITNESS_WORK`); it is not counted
as a checked counterexample. There are no other failures. Counts across radii overlap;
they are not independent verdicts or observations of actual label errors. The fresh
replay took 151.96 seconds under the captured supervisor. It does not rerun the full
research search, random-noise assay or raw-source preparation.

## What comes next

The selected research cost and reuse files retain aggregate counts and statuses,
but their drivers do not persist ordered query/answer histories or per-prefix
certificates. Reuse admission there checks matching record IDs, not the complete
native context/subject binding. Those returns cannot yet establish the Engine-checked
first stopping point or a native observation-reuse saving. This does not itself
falsify the reported research counts.

Preserve those completed experiments. A separately versioned follow-up should retain
complete histories and use the strongest applicable common checker and conventional
baseline, including the endpoint proof/direct matching construction for deletions
and this linear proof for positions. Cases already resolved with zero queries are
draws for the selectors. Report actual initial and additional queries, deferrals,
source qualification, preparation, selection, optimization, checking and total costs.
Residual uncertainty that defeats one method remains unresolved, not fundamentally
uncertifiable. Source qualification and Engine checking remain separate from research
selection and optimization.

## Provenance and established mathematics

The selected research return is commit `b3125c4a97c0029a1f70aba7d0ab5105a9b3d233`,
manifest `f3236723041c938d120ef4e5f97d2fe2c0b97840343b95809f9f2b1f93a030f1`.
All 38 payload bindings and declared committed origins were checked. The Engine
independently reconstructs the constraints; a retained adapter translates the frozen
multiplier row labels. It does not invoke the research LP compiler, optimizer,
matching routine or checker. Only its inspected input-representation adapter is reused.

Exact bounds and separate certificate verification have established predecessors:
[Neumaier and Shcherbina, 2002 preprint, later published in 2004](https://optimization-online.org/2002/06/494/)
and [Cheung, Gleixner and Steffy, arXiv v2, 1 January 2019](https://arxiv.org/abs/1611.08832v2).
No novelty over these methods or frontier superiority is claimed.

The [verification record](../research/perception-revision/0.1.0/linear-bounds-verification.json)
binds exact inputs, outputs, sources and command receipts. Complete benchmark operands,
literature access/rights records, the rejected first attempt and replay outputs stay in
the private checkpoint `~/.codex/reports/reiyah/engine-linear-bounds-2026-09-17-9pp_3nju/`.
The public synthetic example needs no dataset; reproducing the benchmark result also
requires the qualified private operands. No third-party payload is added to public Git.
Gate A remains operator-unaccepted. No new physical measurement, model inference,
cloud campaign, post or outreach was performed by this checkpoint.
