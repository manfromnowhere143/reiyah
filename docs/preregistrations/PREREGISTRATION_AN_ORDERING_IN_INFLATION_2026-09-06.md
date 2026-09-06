# Preregistration AN: the same-kind ordering in the inflation quantity, at operating points not yet examined

Document ID: `reiyah.preregistration-an-ordering-in-inflation`

Version: `0.1.0`

Lifecycle status: `preregistered`

Written and committed before the tool was run at these operating points. Result AJ falsified the
same-kind ordering at 0.50 in the effective-independence quantity; Result AM (exploratory) located
that failure in the summary statistic and in a near-blind camera, and named this test. The Result
AF tool is imported unchanged with its threshold assigned to 0.20 and 0.40, neither yet examined.
Predictions are in the inflation quantity (P(all miss) over the product of miss rates) unless
stated, on all annotated objects.

## Predictions, each falsifiable by the transcript

| id | prediction | falsified if |
|---|---|---|
| AN-1 | at both 0.20 and 0.40, the two-lidar pair's inflation exceeds every cross-kind pair's inflation, bands not overlapping | any cross pair's band overlaps or exceeds the lidar pair's at either point |
| AN-2 | at 0.20, the two-camera pair's inflation exceeds every cross-kind pair containing FCOS3D (regime comparable, FCOS3D miss rate under 80 percent) | either FCOS3D cross pair at or above the camera pair, or FCOS3D miss rate at or above 80 percent making the prediction void, stated in advance as void not falsified |
| AN-3 | at 0.40 no prediction is made for the camera pair; it is recorded whichever way it falls | (none) |
| AN-4 | monotonicity between measured neighbours: every pair's inflation at 0.20 lies between its 0.10 and 0.30 values, and at 0.40 between its 0.30 and 0.50 values | any pair outside either interval |
| AN-5 | the full jury's effective independence at 0.20 lies between its 0.10 value (1.94) and its 0.30 value (2.10), and at 0.40 between 2.10 and its 0.50 value (2.60) | outside either interval |
| AN-6 | the three-channel sub-juries keep the ordering "two cameras plus a lidar" above "one camera plus two lidars" in effective independence at both points, as at 0.30 | any reversal |

AN-1 is the second arm of the law restated in the quantity the diagnostic pointed to. AN-4 and
AN-5 are interpolation forecasts: the cheapest kind, stated because a law that cannot interpolate
between its own measurements is not a law. AN-6 is a forecast the program has not examined before.

## Procedure

`tools/measure/result_af_sensor_jury.py` imported unchanged with `SCORE` assigned to 0.20 and
then 0.40, two runs, byte identity required, transcript retained as
`evidence/measurement/result_an.txt`. Verdicts from this transcript together with the retained
AF and AJ transcripts for the neighbour values, stated as such.

## Outcome

AN-4 and AN-5 supported; AN-1 falsified at 0.40 (bands touch); AN-2 falsified; AN-6 falsified at
0.40; AN-3 recorded. See [`RESULT_AN_ORDERING_IN_INFLATION.md`](../RESULT_AN_ORDERING_IN_INFLATION.md).

## Non-claims

A preregistration, not a result. Released detector outputs on the public nuScenes validation split;
no detector is executed; no released `1.2` byte is involved.
