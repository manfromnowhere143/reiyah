# Result AK: the preregistered ghost forecast at 0.10, two predictions supported and four falsified

Document ID: `reiyah.result-ak-ghost-operating-point`

Version: `0.1.1`

Lifecycle status: `proposed`; the predictions were `preregistered` before the run; four are falsified

> Reference correction, 2026-09-07: the historical ghost label in this analysis means absence
> from a class/range-filtered annotation cache. [Result AO](RESULT_AO_REFERENCE_POPULATION_AUDIT.md)
> demonstrates material differences from the complete annotation reference. Neither reference
> certifies physical nonexistence. Physical ghost interpretations and any automatic upper-bound
> reading of the coincidence ratio are withdrawn as stated. Numerical results below remain
> historical, reference-relative observations; they have not been physically adjudicated or all
> recomputed under the corrected reference. True-detection controls use that same selected
> reference and do not independently resolve the missing-reference issue.


## What was predicted, and what the bytes say

[`PREREGISTRATION_AK_GHOST_OPERATING_POINT_2026-09-06.md`](preregistrations/PREREGISTRATION_AK_GHOST_OPERATING_POINT_2026-09-06.md)
was committed before the Result AH and AH2 tools, imported unchanged with only their score
threshold assigned to 0.10, were run on the primary pair. All six predictions carried numeric
ranges set from the spread already observed at 0.30 and 0.50.

| id | prediction | transcript at 0.10 | verdict |
|---|---|---|---|
| AK-1 | camera ghost share above 23.7 percent, lidar above 19.9 | 52.8 and 64.3 percent | supported |
| AK-2 | time-shift `c_ghost` in [3.0, 12.0], band excluding 1 | **2.65 [2.47, 2.88]** | **falsified** (band excludes 1, point below range) |
| AK-3 | rotation-null `c_ghost` in [6.0, 20.0] | **3.55 [3.36, 3.77]** | **falsified** |
| AK-4 | sanity coefficient in [5.0, 12.0] and below the rotation-null ghost coefficient | 7.53 [6.97, 8.24], **above** 3.55 | **falsified** |
| AK-5 | coincident-ghost recurrence in [30, 60] percent and above both lone-ghost recurrences | 43.9 [38.5, 48.4]; lone camera 40.7, lone lidar 43.9 | **falsified** (equal to lone lidar) |
| AK-6 | true-detection recurrence above 70 percent | 82.5 [80.7, 83.9] | supported |

The time-shift null covers 4,635 keyframes at 0.10 (3,756 at 0.30) because the more numerous
low-score detections give more keyframes a partner with ghosts.

## What it says

1. **The ghost finding is operating-point dependent, and the forecast said otherwise.** At 0.10
   more than half of all detections are ghosts, and their coincidence beyond the time-shift null is
   2.65, a third of the 0.30 value, while against the rotation null ghosts co-locate less than true
   detections do (3.55 against 7.53), the reverse of 0.30 and 0.50. Result AH's statement that
   phantoms coincide beyond real objects holds at 0.30 and 0.50 and not at 0.10.
2. **Why the forecast failed, as a hypothesis, not a finding.** At 0.10 the ghost population is
   dominated by low-confidence boxes scattered over the scene, which are close to independent
   noise; at 0.30 and above the surviving ghosts are the confident ones, and those are the ones
   that coincide. That is consistent with a shared cause for confident phantoms and none for
   diffuse ones, and it is not tested here.
3. **The persistence reading survives with a fair reference and fails one forecast.** Coincident
   ghosts at 0.10 recur 43.9 percent of the time, inside the forecast range, but no more than lone
   lidar ghosts (43.9), so AK-5 is falsified as written. Result AH2b measured the fair reference at
   0.30 (coincident true detections recur 71.7 percent); at 0.10 the true-detection recurrence is
   82.5 percent, so coincident ghosts remain far less persistent than real objects at both points.
4. **Numeric ranges are what preregistration is for.** Directional forecasts (AI) passed eight of
   eight; the first numeric forecasts (AJ, AK) failed one of five and four of six. The program's
   quantitative understanding of the ghost coefficient is narrower than its directional
   understanding, and this result records the gap rather than the direction alone.

## Consequence

The register entry for ghost coincidence is narrowed to the operating points where it was
observed (0.30 and 0.50, four configurations) and marked as not holding at 0.10 on the primary
pair; the evidence-cost condition on ghosts stays measured, not identified. The public statement
that phantoms coincide six-fold is true of the 0.30 operating point and is now qualified with it
wherever the program states it.

## Non-claims

Released detector outputs on the public nuScenes validation split, retained as `proposed`. Every
caveat of Results AH and AH2 applies; the mechanism in point 2 is a hypothesis. The imported tools'
header lines name 0.30 literally; the banner in the transcript is the operating point run.
Transcript `evidence/measurement/result_ak.txt` re-runs byte-identically (two runs). No detector is
executed. No released `1.2` byte is involved.
