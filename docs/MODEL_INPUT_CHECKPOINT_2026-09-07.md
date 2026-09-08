# Model input and adapter checkpoint

Document ID: `reiyah.model-input-checkpoint.2026-09-07`

Version: `0.1.0`

Lifecycle status: `exploratory`

The three executed model-input runs and a separate recount of their retrieved
records agree on 204 passing samples, zero failed samples and 1,224 camera
images. The population was fixed from metadata before
payload outcomes: the first, second and middle sample of the first scene in
all 50 training and 18 validation collection logs. These are engineering smoke
checks on selected examples, not a random sample or a complete payload census.
The [aggregate](../evidence/model-inputs/results-0.1.0.json) retains the exact
selection, producer, runtime, output and private cache digests. All 24 files in
the retrieved archive match its retained catalog. Log, scene, sample and checked
source-file sets are disjoint across the two training groups and validation.

The actual installed MMDetection3D 0.17.1 converter, point loader, camera
adapter and box classes match the retained upstream release byte for byte.
The existing container image is fixed by its content identity. The runtime
uses nuScenes SDK 1.1.11; the preceding metadata checkpoint used SDK 1.2.0.
The relevant older SDK source bytes also match a freshly retained publisher
wheel. Version names alone are not the source comparison.

The actual historical CenterPoint test pipeline changes its input on all 129
selected cases with ten candidate sweeps when the NumPy seed changes from
20260907 to 20260908. One draw excludes candidate 4; the other excludes
candidate 0. Thus both source choice and order change. The separately tested
nearest-nine loader gives identical point rows across those two seeds on all
204 selected samples. This does not measure an effect on detector predictions.
A fixed seed can reproduce a fixed run; the default recipe still makes the
selected sweep history depend on random-number consumption.

The point checks decode every candidate file, compare temporal transforms with
an explicit rigid transform, and compare actual voxel coordinates, occupancy,
first-occurrence order and retained point values. Camera checks run the full
historical test pipeline and compare normalization, padding, intrinsics and
flip state with the explicit calculation. Scene-start sweep padding is
recorded as repeated current-keyframe points, not nine independent past frames.
The 2,713 distinct decoded files include 1,489 lidar files containing 51,691,104
point rows and 1,224 camera files. The maximum rigid-transform discrepancy is
1.365e-12, below the fixed 1e-8 tolerance; camera normalization agrees exactly.
Voxel checks execute the actual CPU operator. CUDA-kernel equivalence has not
been checked. The 68 scene-start cases have repeated-keyframe padding.

A separate synthetic test confirms two camera adapter defects. The upstream
exporter changes the dimensions in its caller's tensor; exporting that tensor
again changes the exported dimensions. A wrapper that passes a copy leaves the
caller unchanged and gives identical repeated results. The historical inverse
also selects x,y velocity from a camera box whose planar velocity occupies x,z.
The tested correction preserves x,z and leaves the other box parameters intact.
These defects do not establish the cause of the old FCOS3D performance gap.

The converter also produced three fresh lidar information caches and three
monocular annotation caches for this exact smoke population. They contain
7,397 camera annotations; 40 have unavailable velocity. Their upstream cache
representation retains NaN. Source inspection shows both model dataset parsers
can replace missing velocity with zero. A training consumer must preserve an
explicit availability mask and avoid treating that replacement as observed
motion. Training readiness is not established by these cache builds.

The first converter attempt replaced the SDK sample table and invalidated its
reverse indexes. It failed before payload checks and emitted no passing result.
The successful successor restricts converter iteration through a view while
SDK lookup methods retain the unchanged, contained metadata tables. The frozen
selection bytes are identical when reproduced by the retained selector.

All 173 offline tests pass, including seven new tests for corrupt point inputs,
unknown values, quaternion validity, exporter custody and selected SDK lookup.
A separate check in the pinned runtime accepts a valid image and rejects three
malformed-image cases for their declared reasons. The inverse-velocity wrapper
also preserves unavailable velocity. The older test-discovery command
pointed at a nonexistent directory; the corrected documented discovery passes.

## Custody and verification

Google reauthentication restored access on 2026-09-08. Detailed private outputs
were retrieved, every selected sample recounted, and the remaining runtime
checks completed. The first readback rejected two locally reconstructed reports:
parsing integer sweep-count keys as strings changed their sorted order. No value
changed. Restoring only the original integer keys reproduces all three original
cloud result files byte for byte. Both representations remain retained.

The [execution record](../evidence/model-inputs/execution-0.1.0.json) binds the
successful checks and earlier failed attempts. The
[Gate B development check](../evidence/model-inputs/development-check-0.1.0.json)
passes. Its 52 historical replay entries are retained, not freshly replayed here;
the optional attack suite was not run. These are engineering integrity checks,
not independent scientific or transport verification or a new Gate A release.

This checkpoint extends main `3a2f836926eaf5d780861d3b3fdc40dd9e041c9b`.
Resolve checked integration and publisher readbacks from Git and the private
task's `delivery.json`; a document cannot certify its own publication.

The private task is `~/.codex/reports/reiyah/model-inputs-2026-09-07/`.
The original GPU VM was started successfully; no new cloud disks or instances
were allocated. An idle census found no running containers, GPU processes or
logged-in users before shutdown. The cloud API reports the original VM stopped
at 2026-09-08T04:18:49Z, with its original disk attachments and both disks retained.
The dataset was mounted read-only in network-disabled containers.
Raw metadata, per-file records, model caches and third-party sources remain
private. No model fitting or inference was run. Gate A remains unaccepted and
independent human reference judgments remain unavailable. Owner worktrees and
UI/UX files are unchanged.

The next scientific work remains full contained training caches and object point
databases, an explicit unknown-velocity loss policy, and a fixed calibration,
initialization and optimization protocol. The legacy FCOS3D prediction geometry
needs a controlled replay through the complete export path. No historical
benchmark is rewritten by this engineering checkpoint.
