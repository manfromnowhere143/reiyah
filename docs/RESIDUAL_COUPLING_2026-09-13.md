# The joint failure that difficulty does not explain

Document ID: `reiyah.residual-coupling.2026-09-13`

Version: `0.1.0`

Lifecycle status: `proposed`

Lane: independent research and conventional comparator. Changes no Engine file, no Gate B file, no
shared handoff and no owner checkout. Gate A remains unaccepted.

## The objection this answers

A dependence coefficient above 1 has an innocent explanation available, and it is the first thing a
good engineer will say: **hard objects are hard for everyone.** Far away, occluded, few returns, and
two channels miss together without sharing anything beyond the object. If that accounts for the
coupling, a redundancy argument can be repaired by conditioning on difficulty and there is no deep
problem.

The retained annotation records the difficulty variables directly: lidar return count per object,
range from the ego vehicle, annotated visibility band, class and scene condition. So the objection is
testable, and it was tested.

## The method

Within a stratum `s` of a difficulty variable, conditional independence predicts
`n_s * (a_s/n_s) * (b_s/n_s)` joint misses. Pooling across strata gives the coefficient that would
hold with the variable held fixed:

```
c_within  =  sum_s observed_s  /  sum_s ( a_s * b_s / n_s )
```

and `(c - c_within) / (c - 1)` is the share of the excess the variable explains. This is the
classical stratified comparison applied to the estimand in `docs/ESTIMAND_RSS_DEFINITION_32.md`,
in exact rational arithmetic over retained integer counts.

## The result

Holding lidar return density, range and visibility fixed **together** removes **57 to 70 percent** of
the excess. It does not remove the coupling, and it does not remove the ordering.

| after holding range, visibility and return density fixed | residual coefficient |
|---|---|
| two lidar | **2.22 to 2.31** |
| two camera | 1.64 |
| camera and lidar | **1.39 to 1.56** |

**Every two lidar pair remains above every other pair after conditioning.** Scene condition explains
nothing at all, to within one percent, on every pair.

So the innocent explanation is insufficient. There is a residue, it is large, and it is structured by
modality rather than by difficulty.

## Why the residue is the number that matters

The part of joint failure explained by difficulty is, in principle, **engineerable**. A designer can
add range margin, handle occlusion, threshold on return density, and reduce it. That is what a
competent safety argument already does.

The residue cannot be reached that way, because those variables have already been held fixed. It is
the joint failure that remains **after** a designer has done everything the measurable difficulty
variables permit. And a two lidar pair carries roughly **1.5 times** the residue of a camera and
lidar pair.

Stated for a safety case: a redundancy argument that conditions on range, occlusion and sensor
return density, which is a good argument, still underestimates two lidar joint failure by a factor of
about **2.2**.

## What this does not settle

**Unexplained by these variables is not unexplainable.** A variable nobody recorded could account for
the residue, and this test cannot see it.

**Shared training data remains a live candidate.** All five channels are public research detectors
trained on the same split, and that is exactly the confound this lane set out to kill. It is not
dead. What is dead is the simplest deflationary reading, that coupling is merely difficulty. The
decisive experiment remains a same modality pair that does not share training data, and the retained
evidence does not contain one.

No statistical uncertainty, resampling band or sampling model is computed here; these are finite
population counts over one validation set at one match rule and one operating point. The Gate B
lane's own values carry bands that this does not reproduce or replace. No vendor architecture is
measured and no safety conclusion about any vehicle follows.

## Reproduce

```sh
python3 -B tools/measure/residual_coupling.py
python3 -B -m unittest discover -s tools/measure -p 'test_residual_coupling.py'
```

Sixteen tests, about 0.03 seconds, exact rational arithmetic, standard library only. The retained
counts carry the digests of the source caches, which are held read only by the Gate B lane, and
contain no raw record, score or annotation token.

## Non-claims

An internal research artifact, retained as `proposed`. Not independent external scientific review,
not an operator acceptance, not a safety, compliance or vendor claim. It names five public research
detectors because they are the retained inputs, and evaluates no deployed system.
