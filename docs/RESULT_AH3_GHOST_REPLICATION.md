# Result AH3: the ghost coefficient replicates on a second camera, a second lidar, and a second operating point

Document ID: `reiyah.result-ah3-ghost-replication`

Version: `0.1.0`

Lifecycle status: `proposed`

## Why

Result AH's register entry asked for a second pair and a second operating point before the ghost
coefficient is read as more than one pair. This reruns the Result AH tool, imported unchanged, on
FCOS3D x Megvii at 0.30, Mapillary x PointPillars at 0.30, and Mapillary x Megvii at 0.50, with
every definition and null as in AH and scene-clustered bands.

## The result

| configuration | camera ghosts / lidar ghosts | `c_ghost`, rotation null | `c_real` sanity, rotation null | **`c_ghost`, within-scene time-shift null** |
|---|---|---|---|---|
| Mapillary x Megvii at 0.30 (AH) | 23.7% / 19.9% | 11.73 [10.46, 13.30] | 8.14 [7.43, 9.00] | **6.18 [4.60, 10.31]** |
| FCOS3D x Megvii at 0.30 | 12.0% / 19.9% | 10.78 [9.31, 12.53] | 8.26 [7.60, 9.01] | **9.80 [7.08, 14.82]** |
| Mapillary x PointPillars at 0.30 | 23.7% / 18.7% | 9.85 [8.76, 11.40] | 7.93 [7.29, 8.70] | **4.60 [3.43, 9.69]** |
| Mapillary x Megvii at 0.50 | 10.7% / 6.2% | 17.25 [13.15, 24.86] | 9.65 [9.00, 10.43] | **7.66 [3.82, 24.33]** |

## What it says

1. **Ghosts coincide beyond independence on every configuration, against the strong null.** The
   within-scene time-shift coefficient is 4.6 to 9.8 with lower bounds of 3.4 to 7.1; no
   configuration's band reaches 1. The finding does not depend on the camera, the lidar, or the
   operating point.

2. **The sanity row behaves the same everywhere.** True detections co-locate 7.9 to 9.7 times above
   the rotation null on every configuration, so the rotation coefficients are inflated by road
   geometry everywhere and the time-shift coefficient remains the load-bearing one.

3. **The bands widen at the stricter operating point.** At 0.50 there are fewer ghosts and fewer
   keyframes with a time-shift partner, and the band is [3.8, 24.3]; the point estimate is not the
   headline there, the lower bound is.

Every caveat of Result AH applies to each configuration: an upper bound under reference error, a
lenient ghost definition, and Result AH2's finding that at least half of the coincident ghosts are
momentary was measured on the primary pair only.

## Adversarial reading, 2026-09-06

A context-free reader (model-assisted, advisory, same model family as the author) read this document against its transcript alone. The points below are the ones that changed a sentence; the full record is `evidence/review-model-assisted-2026-09-06.json`.

1. Coverage of the time-shift null per configuration: 2,666, 3,492 and 1,093 of 5,953 keyframes.
   At 0.50 the null rests on 1,093 keyframes and its band is [3.82, 24.33].
2. On Mapillary x PointPillars the car, truck and bicycle rows (4.74, 4.63, 2.96 against the
   rotation null) fall below that configuration's sanity coefficient for true detections (7.93), so
   the replication there rests on the barrier, pedestrian and cone rows and on a time-shift
   coefficient whose point estimate sits at AH's lower bound.
3. "Does not depend on the camera, the lidar, or the operating point" is narrowed: one alternative
   of each was tested, the coefficient varies two-fold across them, and Result AK then found the
   finding does not hold at 0.10.

## Non-claims

Replication of Result AH on released nuScenes validation predictions, retained as `proposed`. Not a
safety determination, not a certificate about any deployed system. Transcript
`evidence/measurement/result_ah3.txt` re-runs byte-identically (two runs). No detector is executed.
No released `1.2` byte is involved.
