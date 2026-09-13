# What survives when the coefficient is attacked with its own weaknesses

Document ID: `reiyah.modality-coupling.2026-09-13`

Version: `0.1.0`

Lifecycle status: `proposed`

Lane: independent research and conventional comparator. Changes no Engine file, no Gate B file, no
shared handoff and no owner checkout. Gate A remains unaccepted.

This document withdraws two claims this lane published earlier today, and states the one that
survives everything.

## Objection one: the coefficient is not marginal free

`c` rises as miss rates fall. This lane's own operating point sweep showed that directly, across a
factor of 5.3. And the lidar channels here simply detect more than the camera channels:

| channel | miss rate |
|---|---|
| centerpoint, megvii, pointpillars (lidar) | 0.111, 0.134, 0.139 |
| fcos3d, mapillary (camera) | 0.231, 0.244 |

So the finding that *the most coupled pair is always a lidar pair* may be nothing but an artifact of
lidar detecting more. **It is.**

Thresholding every channel to the same miss rate removes it. At a matched rate of `0.50` the two
camera pair reaches `1.589` while every lidar pair sits between `1.441` and `1.527`: the ordering
**reverses**. The same happens under a marginal free odds ratio.

**That claim is withdrawn.**

## Objection two: coarse strata manufacture residue

Conditioning on a bucketed variable leaves within bucket variation, and that alone produces apparent
residual coupling. So the residue this lane reported must be tested against refinement:

| stratification | cells | two lidar residue |
|---|---|---|
| none | 1 | 3.83 to 5.72 |
| visibility, range 10 m, return band | 100 | **2.22 to 2.31** (as published) |
| visibility, range 5 m, exact returns to 60, class | 7,458 | 1.53 to 1.78 |
| visibility, range 2 m, returns to 200, condition | 25,285 | 1.41 to 1.59 |

It is still falling at the finest level the data supports. **The reported residue of 2.22 to 2.31
described the stratification, not the channels. That magnitude is withdrawn as unidentified**, and no
replacement magnitude is offered, because the sequence has not converged and the finest cells average
about five objects, where the pooled estimator is not reliable.

## What survives both objections, and everything else

One ordering, and it is strict.

| matched miss rate | cells | same modality | cross modality | gap |
|---|---|---|---|---|
| 0.30 | 1 | 2.246 to 2.563 | 1.769 to 1.894 | +0.352 |
| 0.30 | 100 | 1.492 to 1.566 | 1.194 to 1.271 | +0.221 |
| 0.30 | 7,458 | 1.285 to 1.366 | 1.113 to 1.148 | +0.137 |
| 0.40 | 1 | 1.755 to 1.901 | 1.524 to 1.638 | +0.117 |
| 0.40 | 100 | 1.312 to 1.347 | 1.135 to 1.190 | +0.122 |
| 0.40 | 7,458 | 1.185 to 1.235 | 1.075 to 1.108 | +0.077 |
| 0.50 | 1 | 1.441 to 1.589 | 1.357 to 1.437 | +0.004 |
| 0.50 | 100 | 1.185 to 1.243 | 1.105 to 1.144 | +0.042 |
| 0.50 | 7,458 | 1.109 to 1.156 | 1.055 to 1.076 | +0.033 |

**Same modality pairs are strictly more coupled than cross modality pairs, with no overlap between
the ranges, in nine of nine controlled comparisons.** Marginals are verified matched to within
`1/500`. On top of this the ordering also holds at all nine operating points of the earlier sweep,
at all seven stratification refinements, and under a marginal free odds ratio.

The gap at the loosest cell is `+0.004`, which is thin, and no statistical uncertainty is computed
here, so nothing should rest on that cell alone. The conditioned cells carry the weight.

**The magnitude is not identified and is not claimed. The ordering is.** That is the part a design
decision can rest on: two channels of the same kind fail together more than two of different kinds,
and holding both detection rate and physical difficulty fixed does not remove it.

## What is still not settled

**Shared training data remains a live candidate for the ordering itself.** All five channels are
public research detectors trained on the same split, and same modality channels plausibly share more
of that inheritance. This test cannot separate the two, and the decisive experiment is still a same
modality pair that does not share a training split.

No statistical uncertainty, resampling band or sampling model is computed. No vendor architecture is
measured, no deployed system is evaluated, and no safety conclusion about any vehicle follows.

## Reproduce

```sh
python3 -B tools/measure/modality_coupling.py
python3 -B -m unittest discover -s tools/measure -p 'test_modality_coupling.py'
```

Seventeen tests, about 0.02 seconds, exact rational arithmetic, standard library only. The retained
counts carry the digests of the source caches, held read only by the Gate B lane, and contain no raw
record, score or annotation token.

## Non-claims

An internal research artifact, retained as `proposed`. Not independent external scientific review,
not an operator acceptance, not a safety, compliance or vendor claim.
