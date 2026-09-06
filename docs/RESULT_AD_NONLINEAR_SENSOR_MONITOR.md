# Result AD: with a non-linear monitor, cross-channel context is readable at the object level, and still not at the scene level

Document ID: `reiyah.result-ad-nonlinear-sensor-monitor`

Version: `0.1.0`

Lifecycle status: `proposed`; the object-level increment is `measured`, the scene-level form stays `inconclusive`

## The test the register required

Results Z, AA and AB left the two-sensor monitor conjecture unsupported with linear models, and the
register required a non-linear monitor named in advance before anything stronger could be said.
Named here: a histogram gradient-boosted model (200 iterations, learning rate 0.05, default depth,
seeded) replacing the Poisson regression of Result Z (Poisson loss) and the logistic regression of
Result AA under the same isotonic calibration wrapper. Features, labels, splits, baselines and the
verdict rule are imported unchanged; only the model class is swapped by assignment. All four
configurations of Results Z, AA and AB are run.

## Per-object disagreement monitor (AA form), five-fold grouped over scenes

| configuration | own features, AUC | own + context, AUC | increment | verdict |
|---|---|---|---|---|
| Mapillary x Megvii at 0.30 | 0.841 +/- 0.009 | **0.863 +/- 0.008** | +0.022 | outside spread |
| FCOS3D x Megvii at 0.30 | 0.857 +/- 0.016 | 0.867 +/- 0.016 | +0.010 | inside spread |
| Mapillary x PointPillars at 0.30 | 0.794 +/- 0.006 | **0.819 +/- 0.008** | +0.025 | outside spread |
| Mapillary x Megvii at 0.50 | 0.813 +/- 0.012 | **0.839 +/- 0.011** | +0.026 | outside spread |

Brier improves with the AUC on every configuration (for the primary pair 0.161 to 0.150), and ECE
is unchanged within spread. With the linear model (AA, AB) the same increments were 0.000 to 0.004.

## Scene-level joint-blindness monitor (Z form), five-fold grouped over scenes

| configuration | proportional baseline, Spearman / AUC | boosted monitor, Spearman / AUC |
|---|---|---|
| Mapillary x Megvii at 0.30 | 0.611 +/- 0.088 / 0.804 +/- 0.042 | 0.607 +/- 0.091 / 0.808 +/- 0.050 |
| FCOS3D x Megvii at 0.30 | 0.662 +/- 0.080 / 0.829 +/- 0.029 | 0.648 +/- 0.068 / 0.822 +/- 0.023 |
| Mapillary x PointPillars at 0.30 | 0.633 +/- 0.054 / 0.816 +/- 0.019 | 0.615 +/- 0.063 / 0.811 +/- 0.021 |
| Mapillary x Megvii at 0.50 | 0.688 +/- 0.062 / 0.834 +/- 0.042 | 0.722 +/- 0.047 / 0.873 +/- 0.032 |

## What it says

1. **The linear null at the object level was a model limitation.** With a boosted model, what the
   other channel reports nearby and how much the channels agree in the keyframe improve the
   prediction of whether a lone detection is real, by 0.022 to 0.026 AUC outside the fold spread on
   three of four configurations, and by 0.010 inside the spread on the second-camera pair. The
   context interacts with class and range in a way a linear model could not use.

2. **The scene-level null stands.** A jointly missed object leaves no output, and a boosted model
   does not change that: three of four configurations are inside the spread or below the density
   baseline; the fourth, at the 0.50 operating point, shows an increment of 0.039 AUC against a
   spread of 0.03 to 0.04, and is not counted.

3. **The two-sensor conjecture, restated to its evidence.** The coupling-aware monitor form is
   readable on the driving channels at the object level, where a disagreement leaves an output,
   with a non-linear model, on three of four configurations tested. It is not readable at the scene
   level. The sentence "the same form applies to two sensors" is therefore replaced by that
   statement; it is neither the conjecture as first written nor its refutation.

## Adversarial reading, 2026-09-06

A context-free reader (model-assisted, advisory, same model family as the author) read this document against its transcript alone. The points below are the ones that changed a sentence; the full record is `evidence/review-model-assisted-2026-09-06.json`.

1. **The verdict rule, stated and applied symmetrically.** The rule used throughout is: an
   increment counts when it exceeds the larger of the two five-fold spreads being compared. Object
   level: 0.022 against max(0.009, 0.008) counts; 0.010 against 0.016 does not; 0.025 against 0.008
   counts; 0.026 against 0.012 counts. Scene level at 0.50: 0.039 against max(0.042, 0.032) does
   not count. The earlier text applied the rule without stating it, which read as asymmetric; the
   verdicts do not change, and the 0.50 scene-level case is the closest call in the program.
2. The imported tools' non-claims blocks still name a Poisson regression and a logistic model;
   for this run the model is the boosted one named above, and those blocks are stale by design.
3. "Interacts with class and range" is a hypothesis; no interaction analysis is in the transcript.

## Non-claims

Released detector outputs on the public nuScenes validation split, retained as `proposed`. One
boosted model class named in advance; no tuning was performed and no other model was tried.
Descriptive, not a safety determination, not a certificate about any deployed system. Transcript
`evidence/measurement/result_ad.txt` re-runs byte-identically (two runs). No detector is executed.
No released `1.2` byte is involved.
