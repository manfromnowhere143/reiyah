# Fixed-procedure pilot: launch failure retained

Study ID: `reiyah.multiorg.fixed-procedure`, version `0.2.0`.
12 October 2026. Engineering attempt failed; scientific endpoint not evaluated.

**The first paired-image launch failed in process supervision. No predictions
were saved, no complete detector pair was produced, and no ranking or reference
sensitivity result exists.** This is an integration failure, not an observed
empty output, an inference timeout or a scientific null.

The [execution record](execution.json) retains the failure and acquisition
identities. The parent supervisor was placed inside the network-denial sandbox.
Its `/bin/ps` memory-monitor invocation was denied, and its cleanup killed the
spawned worker. The outer attempt returned an error after 0.282 seconds. The
exact point reached inside the worker is not established by the empty log.

The [frozen protocol](protocol.json) requires stopping empirical execution in
this owner after first-attempt failure. That stop was honored. The numerical
runner, source bytes, selected image order, score threshold, loss and metric
were not changed. A [separate supervisor correction](../0.2.1/README.md) is
qualified using authored workers only; no empirical retry is hidden here.

## What was completed

The [preceding complete audit](../0.1.0/README.md) retained all 55 images and
165 annotation files. Its direct guarded-union representation exceeded the
native object cap on every image. This separate protocol was frozen after
those structural counts but before image, model or prediction acquisition.

Twenty-eight images fit the object cap when each reference procedure is checked
separately. Four were selected in a fixed hash order. The first complete-image
pilot is `MultiOrg_v2/test/Macros/Plate_4/image_7/image_7.tiff`; it was not chosen
using model outputs. No easier image or alternative detector replaced it.

| Qualification | Retained outcome |
| --- | --- |
| Source model identity | Faster R-CNN and YOLOv3 ONNX files match the published sizes and MD5s; SHA-256s retained. |
| Runtime | 17 pinned binary-wheel distributions; 108,209,279 download bytes; 59.1 seconds installation and checks. |
| Numerical and input controls | 25 authored decoder, NMS, custody, preprocessing, TIFF and provider controls passed in the installed runtime. |
| Actual TIFF input | One 5,720 × 6,385 uint16 plane; 156 complete tiles after the declared downsampling/padding. |
| Matching and composition | Producer controls and 10 separately authored oracle controls passed; neither evaluated empirical predictions. |
| Paired inference | One failed launch, zero saved prediction outputs, zero complete image pairs. |
| Four-image primary endpoint | Not evaluated. |

Input qualification is not model-graph qualification. The released ONNX input,
operator and output contracts remain to be tested in an actual complete run.
No model or reference tuning follows from this infrastructure failure.

## The proposed computation

For each image and each of the three recorded reference procedures,
[compare.py](compare.py) builds a fixed-reference case using the existing native
kernel and checker. A conventional maximum-cardinality matcher checks the same
IoU ≥ 1/2 graph. The loss is `FP + FN`, with strict prediction confidence > 0.5.
Every native object, detection, edge, work and packet limit remains in force.

The exact image/procedure loss differences are then composed into two mean-loss
intervals: one preserving a whole-cohort procedure, and one allowing a declared
imagewise mixture. This is composition of checked fixed cases, not one native
certificate over the entire reference family. The ordinary complete matching
census and min/sum arithmetic are the baseline. One complete paired image would
establish only feasibility; all four frozen images are required for the primary
cross-image question.

## Reproduction boundary and next dependency

[run_pair.py](run_pair.py) preserves the exact numerical runner used in the failed
attempt, including its original launcher for forensic reproduction. **Do not put
that parent launcher inside the sandbox.** The corrected supervisor launches its
unchanged `--worker` branch inside network denial and monitors it from outside.
The numerical worker has no download or training path. Its private input manifest
must bind the protocol, model and image hashes and explicit wall, memory and work
limits. Stage the byte-identical runner as `inference/run_pair.py` under a private
owner; its confinement rule intentionally refuses inputs outside that owner.

[requirements.txt](requirements.txt) pins all installed distributions;
[environment.json](environment.json) additionally retains wheel hashes and local
platform details. These identify this runtime, not a portable reproducible build.
Public input descriptors are in the execution record; raw weights, images,
annotations and local logs remain private. The independent mathematical checker
is prepared and hash-bound in [provenance](provenance.json), but has no empirical
result to verify.

The next bounded attempt must first record the supervisor change and fresh
resource limits, rebind the retained payloads, and run the same first image and
pair. Do not redownload matching payloads, repeat source discovery, expand to
55-image inference, or change the selected cohort to get a successful outcome.
Only a complete, checked first pair can qualify extension to the other three
frozen images. Current evidence establishes no detector preference, scientific
superiority, automotive transfer or human-work saving.
