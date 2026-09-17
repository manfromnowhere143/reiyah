# Consumer review of the 3,000-case research census

Document ID: `reiyah.perception.census-consumer`. Version: `0.1.0`.
Lifecycle status: `exploratory`.

## What was checked

The selected research commit is `7501c2f2e46baf23272564df924ce15fa005dda7`, branch
`research/2026-09-16-audit-sufficiency`. Its outbox manifest SHA256 is
`0353f3914f9ccf9f9adef79b48552cdddfcc018d7d01826d625d44990935b276`.
All twelve selected payloads match their digests; all eleven committed origins match Git.
The research checkout has subsequent uncommitted work, which was preserved and not consumed.
The generated REQUEST still names the older 6fbd5f3 checkpoint and forty-frame actions.
The census is selected by the new manifest, committed README and summary.

A consumer-selected snapshot of the private aggregate rows contains exactly the Cartesian
product of twenty ordered detector pairs and 150 scenes, with no repeated unit: 3,000 rows.
Independent aggregation reproduces the nine reported distributions and all twenty pair tables.
The supported/excluded counts are 1,125/1,875. The retained random-trial zero-crossing counts
are 1,048/1,125 at the minimum claimed deletion size and 930/1,125 at twice that size.
The arithmetic floors and audit lower-bound formula agree with every supported row's metadata.

Those raw rows were not digest-bound in the research outbox. The consumer copied and bound them,
checked their stability during the copy and matched their aggregation to the committed summary.
That is useful consistency evidence. It is not a fresh replay of every input graph, solver optimum,
source-preparation operation or Monte Carlo draw.

## The requested forty-frame checks

The current Engine freshly reproduces and checks the previously sealed common inputs:

| Question | Consumer result |
|---|---|
| Original weighted comparison | 51/20 |
| 354 pool members present, 181 other labels deleted | Checked -3/4; insufficient |
| Same 354 confirmations, at most 49 deletions | Sufficient under a conservative checked bound |
| Proposed 373 confirmations, unrestricted remaining deletion | Unresolved by the bounded component checker |
| Direction of the comparison | Mapillary camera base plus retained Megvii lidar additions |

The 373 result does not refute the research solver's claim. Its conservative lower bound reaches
the strict threshold 1/10; the Engine therefore has not proved sufficiency. The census uses a
480-label upper bound for this same forty-frame unit, which the preceding Engine checkpoint
already checks. Do not conflate that census row with the post-hoc 373-member proposal.

## Mathematical scope

For equal anchor weights and unit miss/false-positive penalties, a deletion changes the loss
difference by at most two divided by the number of frames. This gives the reported arithmetic
lower bound on the number of deletions needed to defeat strict improvement.

The research's additive pool imposes two additional properties: a pool object has no edge to
the base output, and deleting it lowers the augmented graph's maximum matching cardinality by
one. Every maximum augmented matching must therefore use each such reference vertex.
Deleting k of them leaves a matching with at least r-k edges, where r is the original maximum.
It cannot leave a larger one: augmenting that larger matching in the original graph preserves
its already matched reference vertices, so a maximum matching would then omit at least one of
the k required vertices, a contradiction. The base matching is unchanged. Thus a sufficiently
large verified pool supplies a crossing set at the
arithmetic floor. A confirmed set must retain at least `pool_size - floor + 1` pool members
to block all floor-sized pool deletions, under these premises.

This explains a conditional certificate construction using established matching theory.
This review checks the formula against the retained rows, not the pool membership proof for
all 1,125 inputs. General replacement comparisons, unequal weights and uncertain eligibility
need their own conditions; this additive construction cannot be transferred by renaming A and B.

## Repairs needed for a reproducible census claim

### Random trials need stable, recorded seeds

The selected `census_run.py` seeds its generator with:

```python
random.Random(hash(raw['comparison_id']) & 0xffff)
```

Python string hashes can vary between processes. A retained three-process probe gives three
different seed values for the same unit. The selected packet and reproduction command do not
record a fixed process hash seed, per-unit random seeds, or sampled-set digests.
The observed 1,048 and 930 counts reconcile; their exact random draws are not reproducible from
the delivered recipe alone.

A successor should derive seeds from stable bytes containing the protocol identity, unit ID,
budget and trial stream; record them, the ordered-label digest, Python/RNG version and draw-set
digest. Preserve the original observations. A rerun with a new seed policy is a new result,
not an overwrite of the old numbers.

### A printed gate must actually reject mismatches

The selected `census_units.py --gate` prints object, edge and count equalities without asserting
them or returning a failing status when they differ. The recorded forty-frame equality is not
contradicted by this code inspection. However, the command is not a fail-closed automated gate.
A successor needs nonzero failure on each mismatch and known-bad controls.

### Bind the changed preparation and distinguish certificate tiers

The research reports 660 units with annotation-count differences from the earlier retained census,
170 changed numerical decisions, 59 changed floors and two changed supported/excluded outcomes.
Its unresolved reference-point difference near 50 metres means this is a newly specified census,
not exact reproduction of the former one. The new counts should remain tied to the new inputs.

The census's upper bounds are research solver-tier results. Calling all of them independently
checked by the Engine would be incorrect. Deliver input, confirmed-set, proof/status and producer
bindings under a fresh immutable exchange identity to support broader consumer verification.
The previous handoff path/version was resealed; consumers must select by commit and manifest
digest and preserve their own snapshots.

## What the random comparison supports

Two hundred random trials without a crossing establish an observed zero-crossing count under
that sampling procedure. They do not prove worst-case robustness. Random corruption and an
adversarial search target different quantities. The census describes their difference on these
retained conditional comparisons; it does not establish superiority over a competent adversarial
validation method or lower total validation cost.

Keep the scientific scope visible: additive detector integration, the declared deletion family,
2019–2020 public detector submissions, overlapping scenes/model pairs and benchmark references.
These are not 3,000 independent experiments or contemporary autonomous-driving systems.
The [separate correction-source result](PERCEPTION_REFERENCE_CORRECTIONS_2026-09-17.md) additionally
shows real supplied reference changes outside a deletion-only family.

## Next action and publication

Fable retains ownership of the comparator, census driver and ongoing work. Its next sealed return
should repair seed custody and gate failure, bind the new preparation and preserve solver/Engine
tiers. Engine should then consume that exact return and extend proof checking across selected
census inputs without enlarging limits or silently dropping unresolved units.

The current census can be described as a qualified development finding with the limits above.
A headline of state-of-the-art superiority, reduced customer validation cost or independently
verified certificates for all census cases is not supported. No post or outreach was sent.
The private consumer report retains selected sources, aggregate checks, the seed probe and fresh
forty-frame proofs. Gate A remains unaccepted.
