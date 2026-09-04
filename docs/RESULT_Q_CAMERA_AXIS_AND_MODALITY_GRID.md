# Result Q: the camera axis closed, and what the 2×2 modality grid actually shows

Document ID: `reiyah.result-q-camera-axis-and-modality-grid`

Version: `0.1.0`

Lifecycle status: `proposed`

## The gap this closes

Results L, M, N and O all shared one camera model. Every cross-modality pair used Mapillary,
so the coupling's robustness to the *camera* detector was the one axis left untested. Closing it
required a second camera-only detector's predictions on nuScenes val, which meant running
inference rather than reusing published files.

This result adds that detector — **FCOS3D** — and, because a second camera model finally exists,
completes the full **2×2 modality grid**: two cameras (Mapillary, FCOS3D) crossed with two lidars
(Megvii, PointPillars), plus the two same-modality pairs.

## FCOS3D is a result only because its mAP reproduces

FCOS3D (r101, DCN, finetune) was run on the 6,019 val samples in a pinned container. The gate for
trusting it is reproduction of its published accuracy:

- nuScenes devkit eval: **mAP 0.3207**; published **0.3216**.
- Independent re-aggregation from the retained per-object matches (`match.py --validate`): **31.97**.
- Both reproduce the published figure to within 0.13, so the detection is correct.

One honesty note kept in the record: NDS came out 0.290 against a published ~0.395, because this
container's mmdet3d writes box **size and yaw** in a convention that inflates the scale and
orientation true-positive errors. The mAP, translation error, attribute error and velocity error
all reproduce. Since nuScenes mAP and this workstream's matching are both **center-distance based**
— they use translation, score and class only — the NDS gap does not touch any coefficient here. It
is flagged, not hidden.

## The grid

Conditional coefficient at L5 (class, range, visibility, weather, motion), on the identical
131,722-row common support, instance-clustered bootstrap.

| | Megvii (lidar) | PointPillars (lidar) | FCOS3D (camera) |
|---|---|---|---|
| **Mapillary** (camera) | 1.151 [1.138, 1.160] | 1.096 [1.087, 1.103] | **1.144** [1.136, 1.150] |
| **FCOS3D** (camera) | 1.107 [1.098, 1.113] | 1.072 [1.065, 1.077] | — |
| **Megvii** (lidar) | — | **1.290** [1.273, 1.300] | 1.107 |

Every one of the six pairs excludes 1.0.

## What it shows — reported as measured, not as predicted

1. **The camera axis is closed.** FCOS3D, an architecturally distinct camera detector, crossed
   with both lidars gives 1.107 and 1.072, both above independence. The camera-lidar coupling is
   not an artifact of the Mapillary model. All four cross-modality pairs fall in a tight
   1.072–1.151 band.

2. **The strongest coupling is lidar-lidar (1.290).** Two lidar detectors fail together the most,
   consistent with a shared driver they both depend on — lidar point sparsity, the same mechanism
   Results A and B measured directly (objects with few or zero lidar points).

3. **The surprise: two cameras couple like cross-modality, not like two lidars.** The
   camera-camera pair is 1.144 — inside the cross-modality band, far below the lidar-lidar 1.290.
   This corrects a naive expectation. Result H found same-modality coupling far above
   cross-modality at the *raw* level; at the *conditional* level that effect turns out to be
   almost entirely a **lidar-lidar** effect. Once class, range and visibility are removed, two
   camera models are only as coupled as a camera and a lidar.

## The refined thesis

The failure coupling is governed by **shared failure drivers**, not by same-versus-cross modality
as such. Two lidars share the most — both consume the same point return, and both fail on the same
sparse-point objects — so they couple most. Camera-camera and camera-lidar share less and couple
less. But **all six pairs exceed independence** after five admissible confounders. No pairing, not
even two different modalities, reaches the independence a redundancy safety argument assumes; the
best a second modality does is bring the coefficient down to the ~1.07–1.15 band, never to 1.0.

This is a more defensible statement than "modality diversity is necessary but not sufficient." The
data does not support a blanket same-vs-cross ranking; it supports a driver-based reading, and it
still refutes independence everywhere.

## The robustness program, complete

| Axis | Result | Question | Outcome |
|---|---|---|---|
| Detector (lidar) | M | one lidar model? | survives a second lidar backbone |
| Threshold | N | 0.3 cherry-picked? | excludes 1.0 across 0.1–0.5 |
| Unmeasured confounding | O | conditioning incomplete? | needs E-value 2–3 on both arms to nullify |
| Detector (camera) | **Q** | one camera model? | **survives a second camera backbone** |

The coupling has now been shown robust to the lidar detector, the camera detector, the operating
threshold, and plausible unmeasured confounding. Every axis a reviewer can cheaply attack is
answered on evidence.

## Non-claims

Three published or workstream-derived detection outputs on one public split, retained as
`proposed`. FCOS3D predictions were produced here and validated to published mAP; they carry the
NDS caveat above. Association after declared conditioning, not a causal effect, and not a safety
determination or a comparative claim about any vendor. No released `1.2` byte is modified.
