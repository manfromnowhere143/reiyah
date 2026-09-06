# Result AN: the ordering in the inflation quantity, forecast at 0.20 and 0.40; interpolation holds, ordering does not

Document ID: `reiyah.result-an-ordering-in-inflation`

Version: `0.1.0`

Lifecycle status: `proposed`; the predictions were `preregistered` before the run; three are falsified in at least one arm

## What was predicted, and what the bytes say

[`PREREGISTRATION_AN_ORDERING_IN_INFLATION_2026-09-06.md`](preregistrations/PREREGISTRATION_AN_ORDERING_IN_INFLATION_2026-09-06.md)
was committed before the Result AF tool, imported unchanged with its threshold assigned to 0.20
and 0.40, was run. Neighbour values for the interpolation forecasts come from the retained AF
(0.30) and AJ (0.10, 0.50) transcripts, as the preregistration stated. All annotated objects.

| id | prediction | 0.20 | 0.40 | verdict |
|---|---|---|---|---|
| AN-1 | two-lidar inflation above every cross pair, bands not overlapping | lidars 2.29 [2.24, 2.34] against highest cross 1.88 [1.85, 1.91] | lidars 1.39 [1.37, 1.40] against Mapillary x Megvii 1.36 [1.35, 1.38], bands touching | supported at 0.20, **falsified at 0.40** as written |
| AN-2 | two-camera inflation above both FCOS3D cross pairs at 0.20 (FCOS3D miss 43.0 percent, so not void) | cameras 1.82 [1.79, 1.85] against FCOS3D x Megvii 1.85 [1.82, 1.89] | (no prediction) | **falsified** |
| AN-3 | camera pair at 0.40 recorded, no prediction | | cameras 1.17 against 1.16 and 1.12; FCOS3D miss 81.9 percent | recorded |
| AN-4 | every pair's inflation at 0.20 between its 0.10 and 0.30 values, and at 0.40 between 0.30 and 0.50 | six of six | six of six | supported |
| AN-5 | full-jury effective independence between neighbours | 1.94 [1.92, 1.96], at the 0.10 value 1.94, inside on the boundary | 2.38 [2.35, 2.41] inside [2.10, 2.60] | supported, 0.20 at the boundary |
| AN-6 | two cameras plus a lidar above one camera plus two lidars, both points | 1.81 and 1.75 against 1.74 and 1.74 | 2.12 and 2.15 against 1.88 and **2.13** | supported at 0.20 by point, **falsified at 0.40** |

## What it says

1. **The mechanism interpolates; the ordering does not travel.** Every one of the twelve
   interpolation comparisons and both jury ranges fell inside their neighbours, so the coefficient
   behaves smoothly with the operating point in the way Results P, AJ and this test describe. The
   orderings between pairs are a different matter: they hold cleanly at 0.10 and 0.30, and at 0.20
   and 0.40 a cross pair equals or edges a same-kind pair.
2. **What survives across all five operating points.** The two-lidar pair is the most coupled pair
   by point estimate at 0.10, 0.20, 0.30, 0.40 and 0.50, with non-overlapping bands at four of the
   five. That is the sensor arm of the law stated to its evidence. The two-camera pair is not
   reliably above the cross pairs at any point other than 0.30, and its collapse from 0.40 onward
   is the second camera's blindness.
3. **The forecasts are recorded as they fell.** Two supported, one recorded, three falsified in at
   least one arm. The program's directional understanding of the sensor ordering was too strong;
   its understanding of the coefficient's motion with the threshold was right. Both are now in the
   register.

## Non-claims

Released detector outputs on the public nuScenes validation split, retained as `proposed`.
Marginal quantities including shared scene difficulty; the shared-training-data threat applies.
The imported tool's non-claims line names 0.30 literally; the banner is the point run. Descriptive,
not a safety determination. Transcript `evidence/measurement/result_an.txt` re-runs
byte-identically (two runs). No detector is executed. No released `1.2` byte is involved.
