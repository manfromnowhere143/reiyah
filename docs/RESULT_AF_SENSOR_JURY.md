# Result AF: the sensor jury in the LLM jury's quantity

Document ID: `reiyah.result-af-sensor-jury`

Version: `0.1.0`

Lifecycle status: `proposed`

## One quantity for both arms of the law

Result T stated the LLM finding as one number, the effective number of independent models in a
jury, from the observed rate at which every member fails on the same item against the rate
independence predicts. The sensor arm had never been stated that way. This does so for the
four-detector jury on nuScenes val (Mapillary and FCOS3D, cameras; Megvii and PointPillars,
lidars), per annotated object at the 0.30 operating point, with an instance-clustered bootstrap
band (B = 1000), for the full jury and every sub-jury.

## The result, all annotated objects

| jury | k | P(all miss) | inflation over independence | effective independent channels |
|---|---|---|---|---|
| two cameras | 2 | 41.0% | 1.43 [1.42, 1.45] | 1.45 [1.44, 1.46] of 2 |
| two lidars | 2 | 27.9% | 1.71 [1.69, 1.74] | 1.43 [1.42, 1.44] of 2 |
| Mapillary x Megvii (camera x lidar) | 2 | 25.1% | 1.59 [1.57, 1.61] | 1.52 [1.51, 1.53] of 2 |
| Mapillary x PointPillars | 2 | 31.0% | 1.39 [1.37, 1.41] | 1.56 [1.55, 1.57] of 2 |
| FCOS3D x Megvii | 2 | 29.7% | 1.42 [1.40, 1.44] | 1.64 [1.63, 1.66] of 2 |
| FCOS3D x PointPillars | 2 | 38.2% | 1.29 [1.28, 1.31] | 1.60 [1.59, 1.61] of 2 |
| full jury: 2 cameras + 2 lidars | 4 | 20.9% | 4.48 [4.31, 4.67] | **2.10 [2.08, 2.13] of 4** |

The eligible-only denominator (objects with any lidar or radar return) gives 2.20 [2.17, 2.23] of 4
and the same ordering throughout. Per-detector miss rates at 0.30: 46.4, 61.6, 34.0 and 47.9
percent.

## What it says

1. **Four sensors provide the joint-failure protection of about two.** The full jury's effective
   independence is 2.10 of 4, with a band of a few hundredths; every four-way miss occurs 4.5 times
   as often as independence predicts. Beside the LLM juries (3.60 of 7 on MMLU, 1.64 of 6 on ARC,
   1.28 of 7 on HellaSwag), the sensor jury sits in the same range in the same quantity.

2. **The same-kind versus cross-kind ordering holds in this quantity too.** The two cameras (1.45
   of 2) and the two lidars (1.43 of 2) are the least independent pairs; every camera-lidar pair is
   more independent (1.52 to 1.64 of 2), with non-overlapping bands. This is the marginal ordering
   at one operating point; the conditional ordering is Results L to R.

3. **A defect found and corrected in this result's own tool.** The first draft resampled whole
   tracked instances for the eligible-only denominator while the point estimate used only eligible
   objects, so the eligible-only band excluded its own point. The bootstrap now keeps only the
   masked objects of each drawn instance; the correction is recorded in the tool.

## Non-claims

Released detector outputs on the public nuScenes validation split, marginal quantities at one
operating point including shared scene difficulty, retained as `proposed`. All four detectors were
trained on the nuScenes training split, a shared-data threat already on record. Descriptive, not a
safety determination, not a certificate about any deployed system. Transcript
`evidence/measurement/result_af.txt` re-runs byte-identically (two runs after the correction). No
detector is executed. No released `1.2` byte is involved.
