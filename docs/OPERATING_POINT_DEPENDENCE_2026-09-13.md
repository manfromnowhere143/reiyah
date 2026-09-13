# Where redundancy fails worst

Document ID: `reiyah.operating-point-dependence.2026-09-13`

Version: `0.2.0`

Supersedes `0.1.0`, withdrawing one claim.

Lifecycle status: `proposed`

Lane: independent research and conventional comparator, parallel to the Engine. This is an
independent recomputation of a Gate B measurement lane result, and an extension of it. It changes no
Engine file, no Gate B file, no shared handoff and no owner checkout. Gate A remains unaccepted.

## The question

The Gate B lane established that redundancy across genuinely different kinds buys independence while
redundancy across similar kinds does not, and reported a dependence coefficient for sensor pairs.
Two things were worth checking. Does that result survive a recomputation by a different route, and
does it hold at the operating point a system actually runs at?

The estimand is the one bound in `docs/ESTIMAND_RSS_DEFINITION_32.md`:

```
c  =  P(both channels miss)  /  ( P(A misses) * P(B misses) )
```

Five public research detectors, three lidar and two camera, over one annotated validation
population of `134,565` objects at a 2 m match rule. Every input is an integer count taken from a
retained aggregate file; no raw record, score, annotation token or source identifier enters this
lane, and the source digests are recorded.

## What the recomputation confirms

**At every one of the nine operating points examined, the most coupled pair is a same modality pair,
and it is always a lidar pair.** That is the Gate B claim as that lane carefully stated it, reached
here from different counts and a different calculation.

## What it qualifies

The stronger reading, that **every** same kind pair beats **every** different kind pair, is not
supported at any operating point examined, for two separate reasons.

The two camera pair sits below the most coupled camera and lidar pair almost throughout, which the
Gate B lane had already noted itself. And near a captured fraction of `0.79` a camera and lidar pair
reaches `1.569` while a lidar pair sits at `1.386`, so even lidar dominance is not pairwise.

**Same kind redundancy is more coupled at the top, not pair by pair.** A design rule stated pairwise
would be wrong, and the counterexample is retained rather than smoothed.

## The extension, and why it is the part that matters

The ordering is robust to the operating point. **The magnitude is not.**

| captured fraction | two lidar | two camera | camera and lidar |
|---|---|---|---|
| 0.967 | **3.83 to 5.71** | 2.55 | 2.14 to 2.70 |
| 0.898 | 2.29 to 3.85 | 1.82 | 1.55 to 2.03 |
| 0.789 | 1.39 to 1.90 | 1.17 | 1.12 to 1.57 |
| 0.621 | 1.17 to 1.38 | 1.01 | 1.01 to 1.18 |
| 0.350 | **1.05 to 1.08** | 1.00 | 1.00 to 1.00 |

The most coupled pair moves by a factor of `5.29` across the sweep. At a conservative operating point
every pair looks close to independent. At the operating point where nearly every annotated object is
captured, two lidars fail together `5.7` times more often than independence predicts.

The direction is the uncomfortable one. **A redundancy argument is written for the operating point a
system runs at, which is the high capture end, and that is exactly where the independence assumption
is worst.** A redundancy claim validated at a conservative threshold can look sound and be wrong by a
large factor where it ships. Nothing in a validation report would show it, because the coefficient is
not usually computed at all.

## Withdrawn: the lidar specific reading

This document reported that the most coupled pair is always a **lidar** pair. That is withdrawn.

The coefficient is not marginal free and rises as miss rates fall, which this document itself
measured. The lidar channels here detect more than the camera channels, so the lidar ordering could
be an artifact of the marginals, and it is. Thresholding every channel to the same miss rate reverses
it: at a matched rate of `0.50` the two camera pair exceeds every lidar pair.

What survives, and is established in `reiyah.modality-coupling.2026-09-13`, is the weaker and
marginal free statement: **same** modality pairs are strictly more coupled than **cross** modality
pairs, at every matched miss rate and every conditioning level.

## What this is not

These are five public research detectors that share a training split. Shared provenance is one
reason a coefficient exceeds 1, and it is a reason to expect these numbers to be larger than a
carefully diversified architecture would produce. **Nothing here measures any vendor architecture,
and the numbers do not transfer.** What transfers is the method and the shape of the curve.

There is no statistical uncertainty here, no resampling band and no sampling model: these are finite
population counts over one retained validation set at one match rule. The Gate B lane's own reported
values carry bands and operating point sweeps that this recomputation does not reproduce or replace.
The annotated population is not established to be physically complete, and objects no channel
recorded are outside it entirely. No safety conclusion about any vehicle follows from any of it.

## Reproduce

```sh
python3 -B tools/measure/operating_point_dependence.py
python3 -B -m unittest discover -s tools/measure -p 'test_operating_point_dependence.py'
```

Nineteen tests, about 0.03 seconds, exact rational arithmetic, standard library only. The retained
counts are regenerated from caches held read only by the Gate B lane; their digests are recorded in
the counts file so a reader can confirm which bytes produced them.

## Non-claims

An internal research artifact, retained as `proposed`. Not independent external scientific review,
not an operator acceptance, not a safety, compliance or vendor claim, and not a benchmark of any
named product or team. It names five public research detectors because they are the retained inputs,
and evaluates no deployed system. No released `1.2` byte, frozen protocol, claim-register entry,
Engine file, Gate B file or other owner's work is modified.
