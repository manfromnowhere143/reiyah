# Result Z: a scene-level joint-blindness monitor on the driving channels, and it does not beat density

Document ID: `reiyah.result-z-scene-blindness-monitor`

Version: `0.1.0`

Lifecycle status: `proposed`, verdict `inconclusive`

## The claim under test

Results V and X built and transferred a coupling-aware monitor for LLM juries, and the program has
said since Result V that "the same form applies to two sensors." That sentence had never been
tested on the sensors. This is the test, on the camera and lidar channels the program measured.

The question a fused stack cannot answer from its own outputs is how many present objects both
channels are blind to right now; that count is invisible at runtime by construction. A monitor can
still try to estimate it from what the two channels do report in a keyframe: how many detections
each makes, how many agree (same class within 2 m), how confident the agreeing and disagreeing
detections are, how many vulnerable road users only one channel reports. The measured coupling
(Results L to R) is what would make those output patterns informative about the invisible count.

- channels: Mapillary (camera) and Megvii (lidar) released predictions at the 0.30 operating point
- unit: one keyframe; 6,019 scored, 5,953 with annotated objects, 134,565 objects
- target: annotated objects in the keyframe that both channels missed, by the validated matcher
- split: scene-clustered from the nuScenes scene table read out of the pinned metadata archive
  (150 scenes; a timestamp-gap segmentation over every keyframe is computed as a cross-check and
  no scene straddles a segment); 60 held-out scenes, then five-fold grouped cross-validation
- model: Poisson regression on 14 output-only features
- baselines: constant (training mean) and proportional (a scalar times the number of objects the
  fusion reports, fitted on training scenes), the best a stack can do that assumes what it sees is
  what there is

## The result

Joint misses per keyframe: mean 5.66, median 4, zero in 9.5 percent of keyframes, against 22.6
annotated objects and 26.3 fusion-reported objects per keyframe.

| held-out scenes, all annotated objects | Spearman | Pearson | MAE | AUC, top-quartile blind frames |
|---|---|---|---|---|
| constant | 0.000 | 0.000 | 4.32 | 0.500 |
| proportional (fusion object count) | 0.673 | 0.545 | 3.15 | 0.829 |
| monitor (14 output features) | 0.684 | 0.561 | 3.19 | 0.851 |

| five-fold grouped cross-validation | Spearman | MAE | AUC |
|---|---|---|---|
| proportional | 0.611 +/- 0.088 | 3.18 +/- 0.38 | 0.804 +/- 0.042 |
| monitor | 0.600 +/- 0.079 | 3.20 +/- 0.37 | 0.811 +/- 0.045 |

The eligible-only target (objects with any lidar or radar return) gives the same picture. The
monitor's calibration by predicted quintile is honest at the top (10.7 predicted against 10.5
actual) and over-predicts at the bottom (2.3 against 1.3).

## What it says

1. **Scene density predicts joint blindness, and the output pattern adds almost nothing to it.**
   The number of objects the fusion reports already carries a Spearman correlation of 0.67 with the
   number it is jointly blind to; crowded frames hide more. The fourteen coupling-aware features
   raise that to 0.68 on the held-out scenes and lower it to 0.60 against 0.61 across the folds. The
   increment is inside the cross-validation spread on every metric. As a count estimator at the
   scene level, the coupling-aware form has no demonstrated value over density.

2. **The claim that the same monitor form applies to two sensors is not supported by this test.**
   It is not refuted either: this is one target, one operating point, one pair, and a linear model.
   But the sentence may no longer be stated as if it were established. It is downgraded to a
   conjecture with one failed scene-level test against it.

3. **Why the LLM result does not carry over.** For a jury, every item is observed by every channel
   and the outputs on that item are the whole evidence, so agreement patterns are informative about
   that item's failure. For two sensors, the jointly missed object produces no output at all; the
   only trace it leaves is indirect, through the scene's clutter, and clutter is what the proportional
   baseline already reads. A sensor monitor that wants to see the coupling would need per-object
   evidence, for example disagreements on reported objects, which is a different estimand.

## Non-claims

Two released detectors on the public nuScenes validation split, retained as `proposed` with the
verdict `inconclusive`. The target counts annotated objects both channels missed, a lower bound on
what is present. Descriptive, not a safety determination, not a certificate about any deployed
system. A Poisson regression is fitted; no detector is executed. The metadata archive is the pinned
`meta.tgz` (SHA-256 `db48746b10e3544d5ef619eaa3d687e3960626fe1b4422ed856711da5aa7325b`). Transcript
`evidence/measurement/result_z.txt` re-runs byte-identically (three runs). No released `1.2` byte is
involved.
