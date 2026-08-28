# Result L: the conditional coefficient converges, and not to independence

Document ID: `reiyah.result-l-convergence`

Version: `0.1.0`

Lifecycle status: `proposed`

## The open question

`GATE_B_SESSION_HANDOFF.md` section 10 names this the second open item: Result E's
conditional lift fell 1.525, 1.318, 1.156 "without obviously converging". Everything
downstream rests on where that sequence goes. If it reaches 1.0, the dependence in
Results D, E, I, J and K is shared difficulty and nothing more, and the RSS Definition 32
critique collapses. If it settles above 1.0, the two channels fail together beyond what
their common inputs explain.

## Two design faults in the published sequence, both fixed

### Changing denominators

Each added dimension multiplies strata and pushes more rows below the thin-stratum floor.
The published sequence is therefore computed on a shrinking population, which confounds
"conditioning removed association" with "the population changed".

Every level is re-estimated here on a **common support**: the 131,722 rows that survive
the deepest admissible stratification. Only the conditioning varies.

### Mediators

The handoff flags the trap: `num_lidar_pts` may be a mediator of lidar failure rather
than a confounder. This result decides it rather than leaving it open.

A covariate is admissible only if it is a common cause of both channels' failure and is
not itself produced by either detector.

| Covariate | Admissible | Reason |
|---|---|---|
| class | yes | a property of the object |
| range band | yes | geometry, prior to both detectors |
| visibility | yes | occlusion annotation, a cause of failure in both channels |
| weather and lighting | yes | `clear`, `rain`, `night` are scene conditions |
| motion state | yes | derived from the ground-truth track, not from any detector |
| `num_lidar_pts` | **no** | it is the lidar return itself, on the path being measured |
| `num_radar_pts` | **no** | correlates strongly with lidar return, partially blocks the same path |

## The sequence, on a fixed population

| Level | Strata | c | 95% CI | Step |
|---|---|---|---|---|
| L0 none, marginal | 1 | 1.602 | [1.577, 1.627] | |
| L1 + class | 10 | 1.539 | [1.515, 1.560] | -0.063 |
| L2 + range band | 33 | 1.326 | [1.308, 1.341] | -0.213 |
| L3 + visibility | 132 | 1.159 | [1.147, 1.170] | -0.166 |
| L4 + weather and lighting | 334 | 1.155 | [1.143, 1.165] | **-0.004** |
| L5 + motion state | 623 | **1.151** | **[1.138, 1.160]** | **-0.004** |

All estimates use an instance-clustered bootstrap over 8,976 tracked objects, 1,500
replicates, seed `20260828`.

## Answer

**The sequence converges, and not to independence.**

Class, range and visibility carry the association down hard: steps of -0.063, -0.213 and
-0.166. The next two admissible covariates move it by **-0.004 each**, two orders of
magnitude smaller than the range term. The terminal value is 1.151 with a cluster-robust
95% interval of [1.138, 1.160] that excludes 1.0.

Shared observable difficulty explains about 75% of the marginal excess over independence
and does not explain the rest. Camera and lidar fail together beyond what class, range,
visibility, weather and motion account for.

### What this does not prove

Two covariates moving the estimate by 0.004 each is consistent with convergence near
1.15. It is not proof that no further covariate would move it. Unmeasured common causes
remain possible, no adjustment set here is claimed sufficient for identification, and the
result is association after declared conditioning rather than a causal effect. It is also
bounded by what nuScenes annotates: object size and truncation are not available in this
cache and were not tested.

## The mediator error, performed deliberately

| | c | 95% CI | Step from L5 |
|---|---|---|---|
| L5, admissible covariates only | 1.151 | [1.138, 1.160] | |
| L6 + `num_lidar_pts` bucket | 1.107 | [1.096, 1.114] | **-0.044** |

Conditioning on the lidar point count moves the coefficient **ten times more than either
legitimate covariate did**. Someone reaching for it would read that as the sequence
finally converging.

It is not an estimate. `num_lidar_pts` is the lidar return itself; conditioning on it
blocks the path from object to lidar failure that the coefficient exists to measure. The
shrinkage is mechanical, not evidential. The number is recorded so the size of the trap
is on the record and nobody has to rediscover it.

This is the same class of error as Audit 2's withdrawn accuracy claim and the ineligible
rank in Audit 3: a number that looks like progress because it moves in the expected
direction.

## Consequence for the other results

Results D, E, I, J and K stand. Their common premise, that the residual dependence is not
an artifact of the observable difficulty covariates available, is now tested rather than
assumed, on a fixed population, with mediators excluded on stated grounds.

The handoff's second open question is closed for the covariates available here.

## Non-claims

No scientific support, safety finding, compliance determination, comparative claim about
any detector or vendor, and no operator acceptance. Two published detection outputs on one
public split, retained as `proposed`. No released `1.2` byte is modified.
