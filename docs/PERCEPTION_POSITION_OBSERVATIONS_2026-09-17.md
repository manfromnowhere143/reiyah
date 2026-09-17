# Position observations that remain applicable after detector changes

Document ID: `reiyah.perception.position-observations`. Version: `0.1.0`.
Lifecycle status: `exploratory`.

## What changes

The Engine now accepts a returned position and its explicit residual error, checks
which reference it concerns, and computes a new conditional comparison. The same
observation bytes can apply to different detector outputs. Each new comparison
requires a current matching/cover proof; an observation's survival does not make
the earlier conclusion survive.

This adds `position-audit` and `verify-position-audit` to the
[offline revision interface](../research/perception-revision/0.1.0/README.md).
It builds on the [localization envelope](PERCEPTION_LOCALIZATION_CERTIFICATES_2026-09-17.md).
It does not choose queries, measure human effort, or authenticate the supplied
observations. Those remain separate obligations in the
[competitive experiment](REIYAH_NEXT_MISSION_2026-09-17.md).

## Observation and applicability contract

The [strict observation schema](../research/perception-revision/0.1.0/position-observations.schema.json)
requires a cohort, reference-context digest, observation basis, and one answer per
queried reference. Every answer supplies:

- Anchor and reference identifiers.
- A subject digest and an evidence-record digest.
- A rational planar position and a nonnegative closed residual radius, including zero when asserted.

`position_contract.subject_digest(case, geometry_request, anchor_id, reference)`
binds the cohort, reference context, coordinate convention, anchor, original
reference record digest, class and nominal center. It deliberately excludes
detector outputs, loss, matching threshold and prior uncertainty radius. A change
to those quantities requires a new conclusion; it need not invalidate a position
observation. Every supplied observation must match; none is silently discarded.

The upstream reference context must identify the physical frame, time and reference
interpretation. Equal identifiers or hashes check agreement of supplied premises;
they cannot establish that the physical source or frame assignment is correct.
The development reference digests bind normalized rational point records from an
already retained derived census source. This checkpoint does not repeat original
sensor/prediction custody or collect independent measurements.

Missing observations leave the original uncertainty in place. Duplicate answers
reject: repeated or conflicting measurements of the same reference need a separate
contract. There is no `confirmed` flag that fixes adjacency while leaving a nonzero
position error unrepresented. Reusing an answer requires retaining its original
evidence and basis, not changing its fingerprint until a new comparison accepts it.

## Mathematics and proof boundary

For each object, the prior ball is P = B(c,r); a supplied observation asserts
M = B(m,s). The remaining positions are P ∩ M. Both radii are nonnegative and
closed. Different objects retain the declared independent uncertainty family.

Exact rational squared-distance tests establish:

```text
P ∩ M is empty       iff ||c-m||² > (r+s)²
M is contained in P iff s <= r and ||c-m||² <= (r-s)²
P is contained in M iff r <= s and ||c-m||² <= (s-r)²
```

Disjoint balls yield `inconsistent_premises`, with no numerical bound or decision.
The software cannot decide which source premise was wrong. It does not discard a
contradictory answer or treat an empty feasible set as evidence of improvement.

For a nonempty intersection, the method uses the smaller of the two balls as an
outer enclosure, with the prior winning equal-radius ties. Containment makes this
enclosure exact as a set; partial overlap is explicitly conservative. In particular,
external tangency remains nonempty. The method does not compute an optimal enclosure
of the lens and does not claim that its interval endpoints are attainable.

Only anchors whose selected center changes require rebuilding nominal adjacency.
The original nominal graph is checked before replacement. Unchanged-center inputs
are checked through the existing geometry preparation. Fixed detections, classes,
weights, loss and threshold are preserved. A fresh matching/cover certificate then
bounds the loss on the enclosing balls. Because every feasible intersection lies
inside its enclosing ball, the bound also covers every observation-compatible
position. A robust result therefore entails the strict criterion under the supplied
premises. A bound crossing the threshold remains unresolved.

The separate checker repeats applicability and conditioning, checks derived operand
digests, and checks the matching and equal-size vertex covers without calling a
matching optimizer. It shares strict parsing, geometry and conditioning code with
the producer; the finite independent challenges below test this shared boundary.
An adverse point in an outer ball need not lie in P ∩ M. Consequently this command
accepts universal enclosure proofs only, not displacement proofs from the larger
set. The existing localization witness command remains separate.

Bounded-error conditioning and conservative set enclosures are established methods;
this is an application to the current detector-loss contract. The primary background
review is Jaulin, Kieffer, Braems and Walter, *Guaranteed nonlinear estimation using
constraint propagation on sets*, International Journal of Control 74(18), 2001,
[DOI 10.1080/00207170110090642](https://doi.org/10.1080/00207170110090642).
Its author-hosted bytes, access metadata and digest are retained privately. No
redistribution permission or novelty claim is inferred.

## Limits and statuses

The current method supports finite unconditional references and complete observed
A/B outputs. Missing outputs remain blocked; open and joint latent reference models
remain scope-unavailable. Class changes, insertions, deletions, correlated position
errors and repeated measurements are not silently reduced to this position family.
Use their existing applicable contracts or report the missing capability.

The existing 4 MiB input, 16 MiB packet, 128-anchor, 128-reference-per-anchor and
2,048-possible-edge-per-anchor limits remain. Observations have the same 4 MiB input
ceiling and at most 16,384 records. Coordinates/radii retain the magnitude and exact
rational limits of the localization interface. The 2,000,000-unit work screen charges
the existing geometry/matching estimate, two extra nominal passes for changed-center
anchors, and supplied observations. It is a deterministic algorithm screen, not a
measurement of all repeated validation calls or wall time. Captures retain those
costs separately. No limit is raised to obtain a desired result.

## Development evidence

The [verification record](../research/perception-revision/0.1.0/position-observations-verification.json)
retains the exact source and assay bindings, results, checks and costs. These are
exposed development inputs. The fixed answer order is the existing anchor/reference
order; answers use nominal centers and declared residual radii. They are hypothetical
measurement premises, not newly observed correct labels.

The tests exercise unchanged and shifted centers, unfavorable answers, residual
error, both containment directions, partial overlap, tangency, disjoint premises,
changed source/context, missing inputs, joint scope, resource bounds and forged
proofs. Independent direct matching enumeration checks 1,856 finite position worlds
inside admitted intersections across 128 small comparison/answer problems. These
finite challenges can expose a defect; the set-inclusion argument supplies the
continuous soundness obligation.

A synthetic replacement changes a previously robust +1 result to exact -1 while
the identical position observation remains applicable. The old proof rejects on
the changed output. This demonstrates why reusing evidence and reusing conclusions
must be separate operations.

On the retained forty-frame case, hypothetical nominal-center answers reduce a
prior radius of 0.50 m to a residual 0.25 m for the supplied records:

| Supplied answers, fixed order | Checked improvement interval | Criterion |
|---|---|---|
| 0 | [-57/20, 153/10] | unresolved |
| 100 | [-14/5, 76/5] | unresolved |
| 500 | [-12/5, 71/5] | unresolved |
| 1,000 | [-8/5, 253/20] | unresolved |
| 2,299 | [1/2, 229/20] | supported |

These sampled prefixes do not establish the first stopping count or a minimum
audit. All 2,299 hypothetical exact-center answers instead give [51/20,51/20].
Eight completed API calculations agree with ordinary same-center recomputation;
all remain within the unchanged limits. Ten fresh CLI calls check output bindings,
including an inconsistent synthetic answer. All 533 repository tests pass, thirteen
of them new. The assay supervisor retains 154.56 seconds over preparation, production,
checking, ordinary recomputation and CLI repetitions. Tests overlapped; call scopes
differ and no timing ratio is a claimed advantage.

For the changed-output check, two already exposed census configurations share the
same cohort/reference identity and all 2,299 observation bytes. Mapillary camera
plus retained Megvii lidar additions gives [1/2,229/20]; replacing those additions
with retained PointPillars lidar additions gives [-49/20,191/20], unresolved. The
old proof rejects on the latter. The reference records apply; the conclusion still
requires work. This does not prove that all stronger methods would remain unresolved.
Both B configurations retain the base: neither is a standalone added-detector output.

The historical forty-frame export uses a different cohort/context identity and its
capsule rejects on the census input as supplied. The changed-output check therefore
uses a separately declared capsule on the two native census representations, without
overriding any identity. No original observations are relabeled as reusable evidence.

## Next consumer action

The research lane should supply actual computational query histories, including
returned centers, residual errors, source evidence, failed/unresolved answers and
all incurred queries. Use the same checked stopping rule for every selector and
conventional baseline. Reapply still-applicable observations to the next comparison,
then count the additional queries and work. A retained set's size is not the query
history, and successful applicability alone is not a measured saving.

The Engine will consume the sealed histories and check their sources, applicability,
decisions and cost accounting. Gate A acceptance is unchanged; no cloud computation,
new inference, physical measurement, human audit, post or outreach is part of this
checkpoint.
