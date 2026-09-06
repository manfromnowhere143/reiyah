# Result AB: the sensor monitors on a second camera, a second lidar, and a second operating point

Document ID: `reiyah.result-ab-sensor-monitor-replication`

Version: `0.1.0`

Lifecycle status: `proposed`, verdict `inconclusive` on every configuration

## Why

Results Z and AA left the two-sensor monitor conjecture unsupported on one pair at one operating
point, and their registered reconsideration requirements asked for a second pair and a second
operating point before the conjecture may be called anything stronger. This reruns both tools,
imported unchanged, on FCOS3D x Megvii at 0.30 (second camera), Mapillary x PointPillars at 0.30
(second lidar), and Mapillary x Megvii at 0.50 (second operating point). Each pair's match set had
passed its published-mAP gate before use. The imported tools print their own default channel names
in their header lines; the configuration actually run is the banner above each block in the
transcript.

## Scene-level joint-blindness monitor (Result Z form), five-fold grouped cross-validation

| configuration | proportional baseline, Spearman / AUC | monitor, Spearman / AUC |
|---|---|---|
| Mapillary x Megvii at 0.30 (Result Z) | 0.611 +/- 0.088 / 0.804 +/- 0.042 | 0.600 +/- 0.079 / 0.811 +/- 0.045 |
| FCOS3D x Megvii at 0.30 | 0.662 +/- 0.080 / 0.829 +/- 0.029 | 0.640 +/- 0.067 / 0.825 +/- 0.028 |
| Mapillary x PointPillars at 0.30 | 0.633 +/- 0.054 / 0.816 +/- 0.019 | 0.609 +/- 0.059 / 0.809 +/- 0.029 |
| Mapillary x Megvii at 0.50 | 0.688 +/- 0.062 / 0.834 +/- 0.042 | 0.687 +/- 0.047 / 0.861 +/- 0.029 |

## Per-object disagreement monitor (Result AA form), five-fold grouped cross-validation

| configuration | own features, AUC | own + context, AUC |
|---|---|---|
| Mapillary x Megvii at 0.30 (Result AA) | 0.785 +/- 0.009 | 0.788 +/- 0.008 |
| FCOS3D x Megvii at 0.30 | 0.813 +/- 0.016 | 0.817 +/- 0.017 |
| Mapillary x PointPillars at 0.30 | 0.731 +/- 0.010 | 0.734 +/- 0.009 |
| Mapillary x Megvii at 0.50 | 0.779 +/- 0.013 | 0.779 +/- 0.014 |

## What it says

On every configuration the coupling-aware form's increment over its baseline is inside the fold
spread, and at the scene level it is negative as often as positive. The per-channel realness result
of AA replicates in shape: lone lidar detections are far more predictable from their own attributes
than lone camera detections, and the second camera's lone detections are barely predictable at all
(AUC 0.58). The two-sensor conjecture is now unsupported on three pairs and two operating points
with linear models; Result AD supplies the non-linear test the register also required.

## Non-claims

Replication on released nuScenes validation predictions, retained as `proposed`. Descriptive, not a
safety determination, not a certificate about any deployed system. Transcript
`evidence/measurement/result_ab.txt` re-runs byte-identically. No detector is executed. No
released `1.2` byte is involved.
