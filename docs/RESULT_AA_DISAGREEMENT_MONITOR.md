# Result AA: a per-object disagreement monitor on the driving channels, and context adds nothing

Document ID: `reiyah.result-aa-disagreement-monitor`

Version: `0.1.0`

Lifecycle status: `proposed`; the context increment is `inconclusive`, the per-channel realness result is `measured`

## The estimand Result Z pointed to

Result Z found that at the scene level a jointly missed object leaves no output, so the
coupling-aware monitor form cannot see it. This moves to the one place a runtime redundancy
question does leave an output: a disagreement, an object reported by exactly one channel (no
same-class detection of the other channel within 2 m). The stack must decide whether to trust it.
The question is whether cross-channel context (what the other channel reports nearby, how much the
channels agree in this keyframe) predicts whether the lone detection is real, beyond the detector's
own confidence and the object's own attributes.

- channels: Mapillary (camera) and Megvii (lidar) at the 0.30 operating point
- unit: one single-channel detection; 90,946 of them over 5,953 keyframes (37,142 camera-only,
  53,804 lidar-only)
- label: real if a same-class annotated object lies within 2 m, one-to-one by score. The labeling
  matcher is self-checked against the validated per-object matcher: every annotated object the
  validated matcher scored at or above 0.30 is marked real by the labeler, 72,093 of 72,093 for the
  camera and 88,824 of 88,824 for the lidar
- models: the detector's own score, isotonic-calibrated; own features (score, class, distance from
  ego, channel); own plus six context features (agreement fraction, single-channel counts per
  channel, distance to the nearest other-channel detection, other-channel detections within 5 m,
  mean score of agreeing pairs)
- split: scene-clustered from the scene table in the pinned archive; 60 held-out scenes, then
  five-fold grouped cross-validation

## The result

| held-out scenes | n | real | score alone AUC | own features AUC | own + context AUC |
|---|---|---|---|---|---|
| camera-only detections | 13,941 | 31.2% | 0.590 | 0.653 | 0.648 |
| lidar-only detections | 20,800 | 51.7% | 0.715 | 0.835 | 0.844 |
| all single-channel | 34,741 | 43.5% | 0.676 | 0.788 | 0.792 |

| five-fold grouped cross-validation | AUC | Brier | ECE |
|---|---|---|---|
| score alone | 0.679 +/- 0.011 | 0.218 +/- 0.005 | 0.017 +/- 0.005 |
| own features | 0.785 +/- 0.009 | 0.185 +/- 0.004 | 0.021 +/- 0.003 |
| own + context | 0.788 +/- 0.008 | 0.184 +/- 0.004 | 0.020 +/- 0.002 |

Each context feature alone, against realness on the held-out scenes: agreement 0.527, camera-only
count 0.518, lidar-only count 0.550, nearest other-channel detection 0.610, other-channel
detections within 5 m 0.585, score of agreeing pairs 0.513.

## What it says

1. **Whether a lone detection is real is predictable, from the detection itself.** The detector's
   score alone is a weak guide (AUC 0.68); adding class, range and channel lifts it to 0.79, with
   the lidar's lone detections far more predictable (0.84) than the camera's (0.65). A camera-only
   detection is real less than a third of the time; a lidar-only one about half. This is a measured
   per-channel result and it is useful to a fusion rule, but it is not the coupling story.

2. **Cross-channel context adds nothing measurable.** Six context features raise the AUC from
   0.785 to 0.788 across the folds, inside the spread, and change Brier and ECE by less than their
   spread. The strongest single context feature, distance to the nearest other-channel detection,
   reaches 0.61 alone and is absorbed by the object's own attributes.

3. **The two-sensor conjecture is now unsupported on two estimands.** At the scene level (Z) and
   at the object level (AA), on this pair and operating point with linear and calibrated models,
   the coupling-aware form buys nothing over what the stack already knows. The program's sentence
   that the same monitor form applies to two sensors is retained only as a conjecture with two
   failed tests. What the measured coupling (Results L to R) changes is the evidence calculus and
   the credit given to redundancy; it has not been shown to be readable live from sensor outputs.

## Non-claims

Two released detectors on the public nuScenes validation split, retained as `proposed`. Realness is
a same-class annotated object within 2 m, by a labeling matcher self-checked against the validated
matcher. One pair, one operating point, linear and isotonic models; not a safety determination, not
a certificate about any deployed system, and not a refutation of every possible sensor monitor.
Transcript `evidence/measurement/result_aa.txt` re-runs byte-identically (three runs). No detector
is executed. No released `1.2` byte is involved.
