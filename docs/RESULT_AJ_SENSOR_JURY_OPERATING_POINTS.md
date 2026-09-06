# Result AJ: the preregistered sensor-jury test, four predictions supported and one falsified

Document ID: `reiyah.result-aj-sensor-jury-operating-points`

Version: `0.1.0`

Lifecycle status: `proposed`; the predictions were `preregistered` before the run; one is falsified

## What was predicted, and what the bytes say

[`PREREGISTRATION_AJ_SENSOR_JURY_OPERATING_POINTS_2026-09-06.md`](preregistrations/PREREGISTRATION_AJ_SENSOR_JURY_OPERATING_POINTS_2026-09-06.md)
was committed before the Result AF tool, imported unchanged with only its score threshold
assigned, was run at 0.10 and at 0.50. All annotated objects; instance-clustered bands. The
imported tool's non-claims paragraph names 0.30 literally; the banner above each block in the
transcript is the operating point run.

| id | prediction | 0.10 | 0.50 | verdict |
|---|---|---|---|---|
| AJ-1 | every pair's inflation above 1 with a band excluding 1 | lowest pair 1.91 [1.86, 1.96] | lowest pair 1.04 [1.04, 1.04] | supported |
| AJ-2 | same-kind pairs less independent than every cross-kind pair, bands not overlapping | cameras 1.33 [1.32, 1.33], lidars 1.32 [1.30, 1.33] against cross 1.54 to 1.60 | cameras **1.88 [1.87, 1.90]** against cross 1.53 to 2.02 | **falsified at 0.50** |
| AJ-3 | full jury below 3 effective channels | 1.94 [1.92, 1.97] | 2.60 [2.57, 2.63] | supported |
| AJ-4 | every pair's inflation higher at 0.10 and lower at 0.50 than at 0.30 (mechanism of Result P) | 1.91 to 3.64 against 1.29 to 1.71 at 0.30, every pair higher | 1.04 to 1.25, every pair lower | supported |
| AJ-5 | full jury between 1.5 and 3.0 at both points | 1.94 | 2.60 | supported |

Per-detector miss rates at 0.50: Mapillary 68.6 percent, FCOS3D 93.9, Megvii 59.8, PointPillars
61.7; at 0.30 they were 46.4, 61.6, 34.0 and 47.9.

## What it says

1. **The mechanism forecast held on every pair at both points.** Result P said a ratio is deflated
   by its marginals; the preregistration turned that into a forecast about operating points the
   program had not examined, and every one of twelve pair comparisons fell the predicted way. This
   is the first mechanism-based prediction in the program and it is the strongest evidence yet
   that P describes how the coefficient behaves rather than one table.

2. **The same-kind ordering is falsified at 0.50, and the reason is visible in the bytes.** At
   0.50 the second camera misses 94 percent of objects. A channel that misses nearly everything
   cannot fail together with another channel more often than it already fails alone, so its
   pairs read as nearly independent (1.04 to 1.05), and the two-camera pair's effective
   independence rises to 1.88 of 2, above the cross-kind pairs. The ordering holds at 0.10 and at
   0.30, where every channel operates in a comparable regime. The law's second arm is therefore
   narrowed: same-kind pairs are the least independent when the channels operate in comparable
   regimes; a near-blind channel looks independent of everything, and that appearance is the
   marginal artifact Result P named, not diversity.

3. **The effective-independence quantity has a regime limit.** It saturates toward the jury size
   as miss rates approach 1, for the same arithmetic reason. It is reported, as everywhere in the
   program, only beside the miss rates it was computed from.

## Non-claims

Released detector outputs on the public nuScenes validation split, retained as `proposed`.
Marginal quantities including shared scene difficulty; the shared-training-data threat applies.
Descriptive, not a safety determination, not a certificate about any deployed system. Transcript
`evidence/measurement/result_aj.txt` re-runs byte-identically (two runs). No detector is executed.
No released `1.2` byte is involved.
