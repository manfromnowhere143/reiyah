# Preregistration AJ: the sensor jury at operating points not yet examined

Document ID: `reiyah.preregistration-aj-sensor-jury-operating-points`

Version: `0.1.0`

Lifecycle status: `preregistered`

Written and committed before the tool was run at these operating points. Result AF measured the
four-detector jury (two cameras, two lidars) at the 0.30 operating point only. This states, in
advance, what the same tool, imported unchanged with only its score threshold assigned, will show
at 0.10 and at 0.50, on all annotated objects.

## Predictions, each falsifiable by the transcript

| id | prediction | falsified if |
|---|---|---|
| AJ-1 | at both operating points, every pair's inflation over independence exceeds 1 with a band excluding 1 | any pair's band reaches 1 |
| AJ-2 | at both operating points, the two same-kind pairs (two cameras, two lidars) have lower effective independence than every cross-kind pair, with non-overlapping bands | any cross-kind pair's band overlaps a same-kind pair's band |
| AJ-3 | at both operating points, the full jury has fewer than 3 effective independent channels | at or above 3 at either point |
| AJ-4 | mechanism, from Result P: for every pair, the marginal inflation over independence is lower at 0.50 than at 0.30, and higher at 0.10 than at 0.30, because higher thresholds raise every marginal miss rate and a ratio is deflated by its marginals | any pair violates either ordering |
| AJ-5 | the full jury's effective independence is between 1.5 and 3.0 at both points | outside that range at either point |

AJ-4 is the first mechanism-based forecast in the program: it follows from a result (P) rather
than from a pattern. AJ-5 is the first numerical range forecast; it is deliberately wide, and its
width is recorded as the honest precision of the law as it stands.

## Procedure

`tools/measure/result_af_sensor_jury.py` imported unchanged with `SCORE` assigned to 0.10 and
then 0.50, two runs, byte identity required, transcript retained as
`evidence/measurement/result_aj.txt`. Verdicts per prediction from the transcript alone, recorded
in the result document and the register, whichever way they fall.

## Outcome

Four of five supported; AJ-2 falsified at 0.50, where one camera misses 94 percent of objects;
see [`RESULT_AJ_SENSOR_JURY_OPERATING_POINTS.md`](../RESULT_AJ_SENSOR_JURY_OPERATING_POINTS.md).

## Non-claims

A preregistration, not a result. Released detector outputs on the public nuScenes validation split;
no detector is executed; no released `1.2` byte is involved.
