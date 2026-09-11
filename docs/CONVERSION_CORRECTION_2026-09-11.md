# Correction: three defects in the conversion measurement, and the corrected numbers

Document ID: `reiyah.conversion-correction.2026-09-11`

Version: `0.1.0`

Lifecycle status: `corrected`

Corrects [the conversion findings](ADDITION_CONVERSION_2026-09-11.md) version `0.1.0`, published in
this lane at commit `ebfc019`. The defects were found in external review of the published code, not
by this lane. They are reproduced, isolated one at a time on the real data, and corrected here. The
original document and its evidence remain in Git history unchanged.

## What was wrong

| # | defect | effect on the reported conversion |
|---|---|---|
| 1 | one score floor was applied to the base and the addition **together**, so the floor sweep changed the installed configuration as well as the candidate | **fatal to the sweep's interpretation** |
| 2 | keyframes with no eligible reference object were skipped, because the loop iterated the annotation table | negligible here, `0.2960` to `0.2958` |
| 3 | the declared `50 m` limit was applied to annotations and not to predictions | material, `0.2960` to `0.3182` |

Defects 2 and 3 push in opposite directions, which is why the published point estimate was close to
the corrected one and the published **sweep** was not.

## The headline that is withdrawn

Version `0.1.0` reported a score-floor sweep as **"the same pair, the same population, only the score
floor changed"** and concluded that the required penalty ratio moves by **a factor of about 69**.

That sentence was false. The code moved the base detector's threshold at the same time, so the sweep
compared different installed configurations. **The factor of 69 is withdrawn as stated.**

Holding the base at `0.30` and moving only the addition's floor, with defects 2 and 3 also corrected:

| base floor | addition floor | retained additions | gain | conversion | break-even `a/b` |
|---|---|---:|---:|---:|---:|
| 0.30 | 0.10 | 174,468 | 18,523 | 0.1062 | 8.419 |
| 0.30 | 0.30 | 31,047 | 9,878 | 0.3182 | 2.143 |
| 0.30 | 0.50 | 6,640 | 2,610 | 0.3931 | 1.544 |

The corrected span is **5.45x**, not 69x.

## The corrected measurements

All at base and addition floor `0.30`, the `50 m` limit applied to predictions as well as
annotations, and every keyframe included.

| base | addition | retained additions | gain | conversion | break-even `a/b` | published was |
|---|---|---:|---:|---:|---:|---|
| megvii lidar | mapillary camera | 31,047 | 9,878 | **0.3182** | **2.143** | 0.2960 / 2.379 |
| mapillary camera | megvii lidar | 46,981 | 24,581 | **0.5232** | **0.911** | 0.4861 / 1.057 |
| megvii lidar | pointpillars lidar | 22,774 | 6,001 | **0.2635** | **2.795** | 0.2626 / 2.809 |

## What survives, and what does not

**Survives.** The direction of the addition matters: adding the lidar to the camera breaks even at
`0.911` where adding the camera to the lidar needs `2.143`. The operating point of the addition is
still the larger lever than the modality choice, at `5.45x` against `1.30x`.

**Does not survive.** The claim that the operating point moves the answer by about seventy times, and
the specific numbers `0.0284`, `34.24`, `0.6692` and `0.494`, which came from a confounded sweep.
They are withdrawn as stated rather than deleted, and the original document retains them in history.

**Weakened.** The qualitative statement that the operating point dominates the modality choice is
retained, but the margin is about a factor of four, not about fifty. That is a different sentence and
it should be written as the smaller one.

## The downstream number that moved

The [adjudication budget](ADJUDICATION_BUDGET_2026-09-11.md) used the conversion rate as its prior.
With the corrected prior of `9878/31047`, the probability the review returns `improvement supported`
rises from `0.0939` and `0.1209` to **`0.1226` and `0.1508`**, and the expected judgement count from
`12.196` to **`12.414`**. The prediction is unchanged in direction: under the measured rate the
comparison most likely still resolves against the addition.

## What this says about the process

The defects were in code this lane wrote, published and quoted. They were caught by someone reading
that code and running small controlled tests, which is exactly the check the lane asks others to
perform and had not performed on itself. The correct response to the review was to reproduce the
claims before answering, and that is what happened here: each defect was isolated on the real data
before any of it was written down.

The corrected tool takes every population and threshold choice as a **separately declared parameter**
and reports the variant it ran, so a sweep cannot silently move two things again.

## Reproduce

```sh
python3 -B tools/measure/conversion_rate_v2.py CACHE PRED megvii mapillary 0.30 0.30 yes yes
python3 -B tools/measure/conversion_rate_v2.py CACHE PRED megvii mapillary 0.30 0.10 yes yes
```

The last four arguments are the base floor, the addition floor, whether keyframes without reference
objects are included, and whether the range limit applies to predictions. The retained isolation runs
for each defect are under `evidence/decision-packet/corrected/`.

## Known remaining limit

Ego position is read from the annotation cache, so a keyframe with no annotation row has no ego and
its predictions cannot be range filtered. Those frames are counted and skipped in the range-filtered
variant rather than silently included, and the count is reported in each output.

## Non-claims

An internal correction, retained as `corrected`. Not independent external scientific review, not an
operator acceptance, not a safety, compliance or vendor claim. Reference relative, finite population,
no sampling statement. No released `1.2` byte, frozen protocol or other owner's work is modified.
