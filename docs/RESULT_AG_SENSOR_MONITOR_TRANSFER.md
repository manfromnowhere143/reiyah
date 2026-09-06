# Result AG: the sensor monitor transfers across a changed camera, not across a changed lidar or operating point

Document ID: `reiyah.result-ag-sensor-monitor-transfer`

Version: `0.1.0`

Lifecycle status: `proposed`

## The sensor analogue of Result X

Result X showed the LLM monitor transfers across juries on one task. Result AD showed the
object-level sensor monitor reads cross-channel context with a boosted model. This fits that
monitor once, on the primary pair (Mapillary x Megvii at 0.30, training scenes), and reads it
without refit on the held-out scenes of a second camera (FCOS3D x Megvii), a second lidar
(Mapillary x PointPillars), and a second operating point (Mapillary x Megvii at 0.50), against the
score-alone baseline calibrated on the target and the in-domain ceiling refitted on the target's
own training scenes. Row construction is a copy of Result AA's, self-checked to reproduce AA's row
counts exactly (90,946 rows; 37,142 camera-only; 53,804 lidar-only).

## The result, held-out scenes

| configuration | score alone AUC | P1 monitor, own + context: AUC / ECE | in-domain ceiling: AUC / ECE | transfer loss, AUC |
|---|---|---|---|---|
| P1 Mapillary x Megvii at 0.30 (in domain) | 0.676 | 0.866 / 0.020 | 0.866 / 0.020 | 0 |
| P2 second camera, FCOS3D x Megvii | 0.696 | **0.872 / 0.031** | 0.877 / 0.009 | 0.005 |
| P3 second lidar, Mapillary x PointPillars | 0.693 | 0.750 / 0.099 | 0.822 / 0.020 | 0.072 |
| P4 second operating point, at 0.50 | 0.649 | 0.818 / 0.075 | 0.859 / 0.015 | 0.041 |

Per channel: on P2 the transferred monitor reads lidar-only detections at 0.885 against an 0.888
ceiling and camera-only at 0.714 against 0.752; on P3 lidar-only falls to 0.780 against 0.843; on
P4 camera-only falls to 0.755 against 0.846. On P4 the context features add nothing over own
features (0.818 against 0.821), where in domain they add 0.02.

## What it says

1. **Transfer follows the score semantics of the channel that changed.** Swapping the camera
   costs 0.005 AUC: the lidar channel, which carries most of the realness signal, is unchanged, and
   the new camera's lone detections are read nearly as well as a refit would. Swapping the lidar
   costs 0.072 and breaks calibration: PointPillars' scores mean something different from Megvii's
   and the monitor reads them on the wrong scale. Changing the operating point costs 0.041, because
   the disagreement population itself changes (77 percent real at 0.50 against 44 percent at 0.30).

2. **The sensor monitor and the LLM monitor have the same transfer law.** Across channels whose
   outputs keep their meaning (a new jury of the same kind of output; a new camera beside the same
   lidar), transfer is nearly lossless. Across a change in what the outputs mean (a new benchmark;
   a new lidar; a new threshold), it is not, and no refit-free fix has been found. The instrument
   is portable across like channels and must be calibrated for the semantics it reads.

3. **What this does not show.** Every configuration shares the nuScenes training split, and the
   two transfer pairs each share one channel with the primary pair. This is transfer within one
   benchmark's detector ecosystem, not across deployments.

## Non-claims

Released detector outputs on the public nuScenes validation split, retained as `proposed`. One
boosted model class, no tuning. Descriptive, not a safety determination, not a certificate about
any deployed system. Transcript `evidence/measurement/result_ag.txt` re-runs byte-identically (two
runs). No detector is executed. No released `1.2` byte is involved.
