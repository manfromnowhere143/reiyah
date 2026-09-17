# Weighted deletion certificates across scenes

Document ID: `reiyah.perception.split-certificates`. Version: `0.1.0`.
Lifecycle status: `exploratory`. Date: 17 September 2026.

## Question and contract

A detector addition can improve the mean loss over a declared collection of scenes.
How many reference-record deletions can overturn that aggregate decision? Reiyah
now composes checked scene certificates while preserving their different weights.
An attaining counterexample and a universal lower bound are separate obligations.

The selected research return is `4bc28d89a525f6d783d29bbfb3fef41544d6a4a9`,
manifest `732618ef8d8104de589ff6a6ce879cbda10c88e8f78e1be537ff0583dced5f8a`.
All 21 payloads and 20 committed origins match. All 3,000 selected graph bytes
match the earlier sealed Engine snapshot and current owner copies. Their census
rows agree. This is a consumer replay of those derived graphs, not a new rebuild
from every raw sensor, detector and annotation source.

Each ordered pair declares the equal mean of 150 scene-level loss differences.
Each scene weights its frames equally; scenes contain 39, 40 or 41 frames. The
population is exposed development data, and the pairs share scenes and models.
The aggregate is not an official nuScenes leaderboard score. B preserves A and
the additions retained by the declared preparation; it is not standalone B.

## Checked composition

The API is [`tools.perception_revision.split_margin.evaluate`](../tools/perception_revision/split_margin.py).
It consumes explicit expected membership, member weights, a split tolerance, native
comparison inputs and deletion-margin payloads. It validates every input and checks
every member's matching/cover certificate without invoking a matcher or optimizer.
Callers must bind exact input/proof bytes and the population manifest at the IO
boundary. Expected membership is not inferred from successfully evaluated scenes.

Inputs must have fixed finite references and preserved-base additions. Member
penalties agree; weights are nonnegative and sum to one at each level. An unavailable
member makes this proof route unavailable for the aggregate; it is not dropped and
the remaining weights are not renormalized. Anchor identity is `(cohort, anchor)`:
different scenes may use the local name `a-0`, but the same declared record cannot
appear in two members. Physical source identity remains an upstream premise.

Existing per-input, proof, graph and work limits remain unchanged. The new composition
admits at most 256 members, 64 MiB of total encoded inputs and 64 MiB of total encoded
member proofs. This is a collection of checked finite calculations; it neither
enumerates a larger joint latent-world model nor treats resource limits as exact.

### Universal lower bound

Let scene s have outer weight W_s, frame i have within-scene weight w_si, and
g_si be the checked nominal matching gain `TP_B - TP_A`. Let a and b be the miss
and false-detection penalties. A deletion at that frame has per-record decrease
bounded by `c_si = W_s * w_si * (a+b)`.

For k deletions in the frame, the decrease is at most:

```text
c_si * min(k, g_si)
```

Deleting k right vertices changes each matching rank by at most k. Since A remains
a subset of B, the remaining gain is nonnegative, giving the additional g_si cap.
Create g_si abstract slots of value c_si for every frame. If the sum of the K-1
largest slots is smaller than `delta - tolerance`, no set of K-1 deletions can
defeat strict improvement. These slots are upper bounds on possible decrease;
they are not necessarily realizable deletion choices.

### Attained upper bound

The existing member proof supplies reference vertices in a checked minimum B
vertex cover with no A edge. Deleting any subset S of that pool reduces B's rank
by exactly |S|: the surviving cover gives the upper bound and removing vertices
from a maximum matching gives the lower bound. A's graph is unchanged.

Selecting these pool records in decreasing c_si order gives a realizable adverse
set when their decrease reaches the margin. This is an upper bound on the global
minimum. It becomes an exact minimum only when it meets the universal lower bound.
With a gap, the API reports `bounded` and leaves `minimum_adverse_deletions` null.
No sufficient audit, query-policy optimum or human-work reduction follows.

## Scope of replay

The research harness was run against the Engine-owned checkout. All 3,000 legacy
additive producer/checker calls reproduced 2,981 exact agreements and 19 conservative
resource-limit bounds containing the research values, with no contradiction.
The harness's `disagree` list includes those resource limits; they are not nineteen
incorrect values. These inputs have one unconditional world: their limits arise
from the matching-work screening bound, not exponential reference uncertainty.

The new composition separately checks native deletion-margin packets under their
own unchanged work accounting. The retained verification file records complete
membership, every unavailable group, the lower/upper bounds, witness replays and
exact commands. Do not confuse these proof routes or their resource-limit counts.

The smallest selected split witness is PointPillars base plus Mapillary additions:
260 counterfactual label deletions change the aggregate from `180911/959400` to
`31877/319800`, at or below the strict `1/10` threshold. All altered graphs must
have exact before/after calculations for an attained-witness claim. Summing lower
endpoints of conservative intervals would not establish one.

The original forty-frame case is a different comparison: Mapillary camera base
plus retained Megvii lidar additions, with nominal improvement `51/20`.

## Results on the declared 150-scene means

| Preserved-base comparison | Proven minimum or bounds |
|---|---:|
| fcos3d + centerpoint | 4972 |
| fcos3d + mapillary | 2420 |
| fcos3d + megvii | 8458–8481 |
| fcos3d + pointpillars | 4879–4902 |
| mapillary + megvii | 2577 |
| mapillary + pointpillars | 968 |
| pointpillars + fcos3d | 1728–1733 |
| pointpillars + mapillary | 260 |
| pointpillars + megvii | 3120 |

Six minima are exact. The other three rows retain proved lower bounds and checked
attained upper bounds; their global minima remain unresolved within those ranges.
All nine adverse sets were replayed by recomputing 170 changed scene comparisons.
Seven further aggregates are checked excluded. Four CenterPoint-base aggregates
remain unavailable to this composition because ten underlying native margin
certificates retain resource limits. None of those members is omitted.

## Validation and next obligations

The dedicated tests compare weighted bounds and witnesses with 4,096 independently
computed losses over all deletion subsets of small graphs. Controls cover a pool
optimum that does not prove the global minimum, no available witness, threshold
equality, zero weights, omitted members, forged proofs, duplicate record identity,
different scene-local namespaces, resource limits and unavailable replacements.
See [the retained verification](../research/perception-revision/0.1.0/split-verification.json)
for the final suite and census results.

The first aggregate replay rejected repeated local frame names before computation.
The correction scopes identity to cohort and frame, while still rejecting duplicate
records. First failures and successful retries remain in the private checkpoint:
`~/.codex/reports/reiyah/engine-split-certificates-2026-09-17-m2m8wbgj/`.

Fable's next mission is to repair localization boundary/residual-error semantics,
retain displacement and query histories, and measure selection and reuse costs
against strong methods with a common stopping rule. Its selected localization
claims have not acquired geometric verification merely through this deletion replay.
The Engine next checks those observation/witness returns and their applicability.
No inference, cloud compute, physical measurement, post or outreach occurred.
Gate A remains operator-unaccepted. No novelty or frontier-superiority claim follows.
