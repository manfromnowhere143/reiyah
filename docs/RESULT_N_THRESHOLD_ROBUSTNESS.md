# Result N: the conditional coefficient survives the score threshold, and does not cross independence

Document ID: `reiyah.result-n-threshold-robustness`

Version: `0.1.0`

Lifecycle status: `proposed`

## The cheapest attack on Results L and M

Results L and M report the conditional coefficient at one operating point, score `>= 0.3`.
The first objection a reviewer raises costs nothing: the threshold is arbitrary, so pick a
stricter one and the residual dependence may vanish, which would make the RSS Definition 32
critique an artifact of a single operating point rather than a property of the two channels.

Result D already answered this for the **marginal** coefficient, and the answer there is
*yes, it falls*: `2.271, 1.878, 1.587, 1.363, 1.239` at thresholds `0.1 .. 0.5`. That is
expected and says nothing about mechanism, because the marginal number is shared difficulty
and residual coupling added together. The open question is about the **conditional**
coefficient: the coefficient left after class, range, visibility, weather and motion are
stripped out, the one that actually indicts independence. Does *it* stay above 1.0 across
the operating range, or does it collapse to independence somewhere?

## The design: change the threshold and nothing else

This runs Results L and M's exact L5 machinery at each threshold and changes one thing. Same
five admissible confounders, same `MIN_STRATUM` floor, same instance-clustered bootstrap,
same seed `20260828`. The common support is fixed by **ground-truth stratum counts** and is
therefore the identical 131,722-row population at every threshold, so a change in the
coefficient is the threshold and never a change of population or of conditioning.

The tool reproduces the score-`0.3` conditional coefficient of Result L (`1.151`) and
Result M (`1.096`) exactly as its self-check, which is what licenses reading the other rows.

## The sweep, on the fixed common support

**Mapillary (camera) x Megvii (lidar)**

| score >= | marginal c (L0) | conditional c (L5) | L5 excludes 1.0 |
|---|---|---|---|
| 0.10 | 2.304 [2.247, 2.359] | 1.360 [1.325, 1.380] | yes |
| 0.20 | 1.900 [1.865, 1.935] | 1.238 [1.217, 1.250] | yes |
| 0.30 | 1.602 [1.577, 1.627] | **1.151 [1.138, 1.160]** | yes |
| 0.40 | 1.373 [1.356, 1.390] | 1.089 [1.081, 1.095] | yes |
| 0.50 | 1.245 [1.232, 1.258] | 1.051 [1.046, 1.055] | yes |

**Mapillary (camera) x PointPillars (lidar)**

| score >= | marginal c (L0) | conditional c (L5) | L5 excludes 1.0 |
|---|---|---|---|
| 0.10 | 1.928 [1.877, 1.978] | 1.249 [1.221, 1.268] | yes |
| 0.20 | 1.569 [1.543, 1.594] | 1.139 [1.126, 1.149] | yes |
| 0.30 | 1.401 [1.383, 1.419] | **1.096 [1.087, 1.103]** | yes |
| 0.40 | 1.290 [1.276, 1.304] | 1.069 [1.062, 1.074] | yes |
| 0.50 | 1.197 [1.186, 1.207] | 1.043 [1.038, 1.047] | yes |

## Answer

**Ten measurements, ten intervals above independence.** Across the whole operating range,
for both lidar detectors, the conditional coefficient's 95% interval excludes 1.0.

Two facts, stated as measured, neither softened nor oversold:

1. **It attenuates.** The conditional coefficient declines as the threshold tightens
   (`1.360 -> 1.051` for Megvii, `1.249 -> 1.043` for PointPillars). As only confident
   detections remain, the residual coupling shrinks toward independence. At `score >= 0.5`
   the excess is small, about 5% and 4%, though still statistically distinguishable from 1.0.

2. **It never reaches independence in the measured range.** The lower bound of every
   interval at every threshold, for both detectors, is above 1.0. The marginal coefficient,
   which carries shared difficulty as well, falls faster and further; the part that survives
   conditioning falls slower and does not cross 1.0 anywhere measured.

The honest reading is not "the dependence is threshold-independent" - it plainly weakens as
the threshold tightens. It is that the residual coupling is present and significant across
the entire operating range a detector is actually run at, and is therefore not a property of
the `0.3` operating point.

## What this adds

Together with Result M, the finding is now robust along two independent axes: the detector
(a second, architecturally distinct lidar backbone) and the score threshold (the full
`0.1 .. 0.5` range). The two cheapest objections to the headline - "it is one model pair"
and "it is one operating point" - are both answered on evidence rather than assumed away.

## What this does not add

It does not close the camera axis: every pair here shares the one Mapillary camera model, so
the coefficient's robustness to the *camera* detector is still untested and needs a second
camera-only detector. It does not widen identification: this remains association after
declared conditioning, not a causal effect, bounded by the covariates nuScenes annotates,
with unmeasured common causes still possible.

## Consequence

RSS Definition 32's channel-independence assumption fails on this evidence not at one lucky
operating point but across the range of thresholds a deployed detector uses, for two
different lidar detectors. The safety-argument consequence in Result G (evidence scales as
the square root of the marginal coefficient) is unchanged in form; this result hardens the
premise it rests on.

## Provenance

`evidence/measurement/result_n.txt` records both commands, both full sweeps, and the
self-check that reproduces Results L and M at `0.3`.

## Non-claims

No scientific support, safety finding, compliance determination, comparative claim about any
detector or vendor, and no operator acceptance. Two published detection outputs on one public
split, retained as `proposed`. No released `1.2` byte is modified.
