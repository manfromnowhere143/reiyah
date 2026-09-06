# Result AM (exploratory): where the same-kind ordering fails at 0.50, and where it does not

Document ID: `reiyah.result-am-ordering-failure-diagnostic`

Version: `0.1.0`

Lifecycle status: `exploratory`

## Why

Result AJ falsified, at the 0.50 operating point, the preregistered prediction that same-kind
pairs are the least independent, in the effective-independence quantity: the two-camera pair read
1.88 of 2 and the two-lidar pair 1.56 of 2, both above the Mapillary x Megvii cross pair at 1.53.
This is a diagnostic, not preregistered and without bands: the pairwise inflation over independence
for every pair at 0.30 and 0.50, by ego range band and by class, with the two miss rates beside
each cell so the marginal artifact of Result P can be seen where it acts.

## What the map shows

Inflation over independence at 0.50, all annotated objects, by range band (miss rates in percent):

| pair | 0 to 20 m | 20 to 30 m | 30 to 40 m | 40 m and beyond | all |
|---|---|---|---|---|---|
| two lidars | 1.34 (50, 49) | 1.22 (62, 63) | 1.14 (68, 72) | 1.11 (75, 85) | 1.25 (60, 62) |
| Mapillary x Megvii | 1.34 (55, 50) | 1.25 (70, 62) | 1.13 (81, 68) | 1.04 (92, 75) | 1.24 (69, 60) |
| Mapillary x PointPillars | 1.31 (55, 49) | 1.17 (70, 63) | 1.07 (81, 72) | 1.03 (92, 85) | 1.19 (69, 62) |
| two cameras | 1.08 (55, 89) | 1.04 (70, 95) | 1.01 (81, 99) | 1.00 (92, 100) | 1.05 (69, 94) |
| FCOS3D x Megvii | 1.10 (89, 50) | 1.04 (95, 62) | 1.01 (99, 68) | 1.00 (100, 75) | 1.05 (94, 60) |
| FCOS3D x PointPillars | 1.07 (89, 49) | 1.02 (95, 63) | 1.01 (99, 72) | 1.00 (100, 85) | 1.04 (94, 62) |

At 0.30 the same table has the two lidars at 2.07, 1.65, 1.46, 1.28 (1.71 overall) and every pair
ordered as Result AF reported.

## What it says, as a diagnostic

1. **The lidar pair keeps its rank in the inflation quantity.** At 0.50, in every range band and
   overall, the two-lidar pair's inflation equals or exceeds every cross pair's (1.25 against 1.24
   and 1.19 overall). The reversal Result AJ recorded for the lidar pair lives in the
   effective-independence summary, which uses the mean miss rate and distorts when the two rates
   differ; it is not in the inflation. AJ-2 stays falsified as written, because it was written in
   that quantity; the diagnostic locates the failure in the quantity rather than in the coupling.
2. **The camera pair's collapse is the near-blind camera.** With FCOS3D missing 89 to 100 percent
   of objects across the bands, every pair containing it sits at 1.00 to 1.10, the marginal artifact
   of Result P in its extreme form. The camera pair's inflation at 0.30, 1.43, is real coupling; at
   0.50 there is almost nothing left for it to couple with.
3. **The range gradient is the same at both operating points.** Every pair's inflation falls with
   range at both thresholds, as Results D and P showed, and every cell keeps its ordering across
   bands, which is what a marginal artifact operating on top of a stable coupling looks like.

## What this changes

Nothing in the register's verdicts. It suggests, and does not establish, that the law's second arm
should be stated in the inflation quantity, with the effective-independence count kept as a
summary that fails when miss rates diverge, and that the preregistration's choice of quantity was
the error. A preregistration in the inflation quantity would test that; it is not done here.

## Non-claims

Exploratory diagnostic, not preregistered, no bands; marginal quantities including shared
difficulty; released detector outputs on the public nuScenes validation split. Not a result, not a
safety determination. Transcript `evidence/measurement/result_am.txt` re-runs byte-identically (two
runs). No detector is executed. No released `1.2` byte is involved.
