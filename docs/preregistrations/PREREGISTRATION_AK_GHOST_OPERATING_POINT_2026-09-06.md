# Preregistration AK: the ghost coefficient at an operating point not yet examined, with numeric ranges

Document ID: `reiyah.preregistration-ak-ghost-operating-point`

Version: `0.1.0`

Lifecycle status: `preregistered`

Written and committed before the tools were run at this operating point. Results AH, AH2 and AH3
measured ghost coincidence and persistence at 0.30 (four configurations) and at 0.50 (one
configuration). This states, in advance and with numeric ranges, what the Result AH and AH2 tools,
imported unchanged with only their score threshold assigned to 0.10, will show on the primary pair
(Mapillary x Megvii). At 0.10 both detectors report many more low-confidence boxes, so the ghost
share of detections should rise and the coincidence structure should persist.

## Predictions, each falsifiable by the transcript

| id | prediction | falsified if |
|---|---|---|
| AK-1 | camera ghost share of detections above 23.7 percent (its 0.30 value) and lidar ghost share above 19.9 percent | either at or below its 0.30 value |
| AK-2 | `c_ghost` against the within-scene time-shift null between 3.0 and 12.0, band excluding 1 | point outside [3.0, 12.0] or band reaching 1 |
| AK-3 | `c_ghost` against the rotation null between 6.0 and 20.0 | outside that range |
| AK-4 | the sanity coefficient for true detections against the rotation null between 5.0 and 12.0, and below the rotation-null ghost coefficient | outside the range, or at or above the ghost coefficient |
| AK-5 | coincident-ghost recurrence in the next keyframe (AH2 form) between 30 and 60 percent, and above both lone-ghost recurrences | outside the range, or at or below either lone-ghost recurrence |
| AK-6 | true-detection recurrence above 70 percent, as at 0.30 | at or below 70 |

AK-2 through AK-5 are the first numeric-range forecasts for the ghost results. The ranges are set
from the spread already observed across four configurations (time-shift 4.6 to 9.8; rotation 9.9
to 17.3; sanity 7.9 to 9.7) widened by roughly a third on each side, and their width is recorded
as the honest precision of the finding as it stands.

## Procedure

`tools/measure/result_ah_ghost_coincidence.py` and `tools/measure/result_ah2_ghost_persistence.py`
imported unchanged with `SCORE` assigned to 0.10, two runs each, byte identity required,
transcript retained as `evidence/measurement/result_ak.txt`. Verdicts from the transcript alone,
recorded whichever way they fall.

## Non-claims

A preregistration, not a result. Released detector outputs on the public nuScenes validation split;
no detector is executed; no released `1.2` byte is involved.
