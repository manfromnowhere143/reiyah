# The census: my measure is empty, and the distribution underneath it is not

Document ID: `reiyah.scale-study.census.2026-09-15`

Version: `0.2.0`

Lifecycle status: `corrected`

> **Its central inference is withdrawn.** The Engine consumer supplied an executable counterexample
> against my exact committed module: one base at `x=0`, one addition at `x=3`, three objects between
> them. No single deletion changes the gain, every pair does, so the floor is 1 and the true minimum
> is 2. My search only ever chose deletions that immediately removed one unit of gain, so
> `k_observed` could only equal `k_floor` and the `certified_above_floor` branch was unreachable.
> **Zero above-floor results therefore proved nothing.** The derivation was wrong too: `k_floor <= G`
> bounds the gain that must be removed, not the number of deletions needed to remove it.
>
> What survives: the 1,124 witnesses are verified crossings at exactly `k_floor`, and the floor is a
> proved lower bound, so each is its unit's exact minimum. Among the 1,127 supported units the floor
> frequency lies in `[1124/1127, 1]` and the above-floor frequency in `[0, 3/1127]`, which is a
> descriptive high floor frequency and not a theorem.
>
> Full record: [`research/scale-study/0.3.0/CORRECTION.json`](../research/scale-study/0.3.0/CORRECTION.json).

Date: 2026-09-15. Lane: independent research.

Protocol frozen before any outcome at
`4c601ca94bc1e34e155fda0b16a7e45d660c5084e913f5630938224b74686368`.
Artifacts: [`census-summary.json`](../research/scale-study/0.2.0/census-summary.json),
[`census-index.json`](../research/scale-study/0.2.0/census-index.json) with all 3,000 units.

## The declared result

> Among **3,000** declared annotation conditional decisions under the Engine additive loss and the
> single record deletion family, **1,124** were certified at their arithmetic floor, **0** above it,
> and **3** remained unresolved. **1,873** had an unsupported baseline.

150 scenes, 20 ordered pairs among five public submissions, 3,000 of 3,000 units computed in 463
seconds, 0.146 seconds per unit on average.

## The measure I proposed is empty, and the census proves it

Zero of 1,124 resolved units exceeded the floor. Not a small number: **zero**.

The pilot derivation predicted this. With unit penalties and equal frame weights, `D·F = 2G − R`,
so `k_floor ≤ G` always, each deletion removes at most one unit of gain, and there is always enough
removable gain to reach the floor. A ratio above one needs reassignment to block every remaining
single unit removal, and across 1,124 real units that never once happened.

So the fragility ratio is not a property of the annotations. It restates the arithmetic. The two
earlier case studies, presented as a replication because both showed ratio 1, were replicating a
fact about the loss function. **The ratio is withdrawn as a quantity of interest**, but not for the reason given here. It is
withdrawn because it was never measured: the search could only ever return the floor. Whether any
real unit has a minimum above its floor is now an open question, not a settled zero.

## What is underneath it, and this part is real

The absolute number of deletions needed varies by nearly three orders of magnitude.

| quantity | value |
|---|---:|
| minimum | **1** |
| 10th percentile | 3 |
| 25th percentile | 10 |
| median | **26** |
| 75th percentile | 60 |
| 90th percentile | 106 |
| maximum | **575** |

Normalised by the scene's own qualifying annotations:

| quantity | value |
|---|---:|
| minimum | 0.0006 |
| median | **0.0239** |
| maximum | 0.2166 |

So the median supported scene level comparison is removed by correcting about **2.4 percent** of
that scene's annotations. The most robust needs 21.7 percent, 575 of 2,655. And at the other end:

- **37 units are overturned by deleting a single annotation.**
- **169 units, 15.0 percent of those resolved, need five deletions or fewer.**
- **271 units, 24.1 percent, need one percent or less of their scene's labels.**

A quarter of the supported comparisons in this census rest on one percent of the annotations they
are scored against. That is a statement about this loss on this data, and it is the number worth
carrying forward.

## Most additions are not improvements

**1,873 of 3,000 units, 62.4 percent, have an unsupported baseline**: under the declared loss and
tolerance the added detector does not clear the threshold at all. These are adverse outcomes and
they are retained as first class results, not filtered out of a success rate.

## Three unresolved units, retained

| scene | pair | floor | status |
|---|---|---:|---|
| scene-0276 | fcos3d + pointpillars | 137 | budget exhausted |
| scene-0345 | fcos3d + megvii | 283 | budget exhausted |
| scene-0345 | fcos3d + pointpillars | 256 | budget exhausted |

They are counted in the denominator. No frequency here is computed as if they had resolved.

## What was checked, and what it cost

The census was rebuilt from the original tables: 6,019 frames in 150 scenes, zero join failures,
192,041 census annotations giving 148,440 included under the common 50 m rule, 47 declared empty
frames retained. All five submissions qualified with zero missing coordinates.

The pilot's declared first falsifier did not fire: an independent implementation written from the
protocol, sharing no matcher, agreed on 20 of 20 units as exact rationals. `scale_study.py` carries
22 tests including the non additivity adversary and 300 randomised agreements against a separate
matcher.

Every reported witness was verified by full recomputation of both matchings before it was counted.

## What this does not establish

No annotation has been checked, so there is no label error rate and no probability of anything. The
3,000 units share 150 scenes, 5 submissions and their objects; they are not 3,000 independent
experiments and no uncertainty statement about a wider population is made. This is the Engine
additive loss with unit penalties and a 50 m common range, not official mAP or NDS, so it is not a
study of published leaderboard results. Nothing here speaks to human effort, deployment practice,
customer value or novelty. Label errors destabilising benchmark rankings is prior art from
Northcutt, Athalye and Mueller, NeurIPS 2021.

## Next falsifier

The distribution above is descriptive of one dataset under one loss. The falsifier is a second
dataset: if the normalised edit count distribution there is materially different, the shape is a
property of nuScenes annotation density rather than of benchmark decisions. If it is similar, that
is the first evidence the shape is not dataset specific.

The narrower open question is whether any ratio above one exists at all under this loss. The census
says no in 1,124 attempts, and the derivation says it needs a structural accident. A constructed
example would settle whether it is possible or impossible, and impossible would be the cleaner
result: it would mean the floor is the answer and the search is unnecessary.
