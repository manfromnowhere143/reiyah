# Partition-contained metadata and SDK checkpoint

Document ID: `reiyah.training-partition-checkpoint.2026-09-07`

Version: `0.1.0`

Lifecycle status: `exploratory`

This engine checkpoint extends main
`ce925e6ba640858c099c29460287fc6419b1afe5`. It follows the
[training-file inventory](TRAINING_INPUT_FINDINGS_2026-09-07.md) and implements
the metadata portion of the [training comparison](TRAINING_OVERLAP_NEXT_EXPERIMENT_2026-09-07.md).
All three earlier split proposals are preserved. Subset membership uses their
collection logs and scene names; detector outcomes have no role in selection.

All six training subsets and the full validation subset load successfully
through the exact nuScenes SDK 1.2.0 implementation. Every selected metadata
reference resolves within its subset. Every emitted camera/lidar source also
belongs to the preceding inventoried request. The
[retained results](../evidence/training-partitions/results-0.1.0.json) bind the
actual table bytes, source lists, SDK versions and comparisons.

| Proposal | U samples | V samples | SDK loads |
|---|---:|---:|---|
| 20260910 | 15,085 | 13,045 | Both passed |
| 20260911 | 13,969 | 14,161 | Both passed |
| 20260912 | 11,608 | 16,522 | Both passed |

The validation subset contains 6,019 samples and also passed. Each training pair
contains all 28,130 official training samples on its frozen 50 logs. Direct
readback confirms that log, scene, sample and instance identities are disjoint
between U, V and validation within each proposal. Emitted camera/lidar
filenames also have no overlap between those groups, and each training sample
has the same source row across all three proposals. The three proposals reuse
the same source population; they are not three independent datasets.

The sampled SDK box centers, orientations, dimensions and camera intrinsics
agree with the explicit calculation under the predeclared absolute tolerance
of 1e-8. These are numerical consistency checks on shared metadata, not
physical accuracy measurements.

## What the artifacts contain

The builder streams the exact source archive into a private SQLite index to
bound memory. It checks foreign keys, annotation attributes, sequence counts,
endpoints, reciprocal links, scene containment, temporal order and keyframe
channel coverage. It then writes actual SDK JSON tables for each whole-log
subset. A reference outside that subset is an error; it cannot enlarge the
group to make the reference resolve. Failed work does not emit a successful
result record. Selected numeric values retain decimal precision. Output table
rows and annotation source lists use deterministic token ordering; original
array order is not preserved.

The first import failed on a global filename uniqueness assumption. The
[duplicate census](../evidence/training-partitions/radar-alias-audit-0.1.0.json)
found ten radar paths reused at adjacent scene boundaries, with matching
timestamp, sensor, pose and calibration values and no reuse across logs. The
corrected builder preserves both rows under that explicit boundary rule. Other
filename reuse remains an error. The failed producer and run are retained.

Only the map table's `log_tokens` lists are projected to the selected logs.
Map pixels remain the original shared geographic context. Taxonomies also
remain shared. The official schema says instance identities are not tracked
across scenes, so separate instance tokens do not establish separate physical
objects. The [source ledger](../evidence/training-partitions/sdk-source-ledger-0.1.0.json)
binds the retained SDK wheel, relevant implementation files and exact schema
document revision; it confers no scientific authority.

The SDK consumer writes a private source row for every sample: all six camera
keyframes, its lidar keyframe, up to ten real earlier lidar candidates, and every
annotation identity. Short histories remain short. Every referenced sensor
filename and token must occur in the exact preceding inventoried request.
That binds this source list to the earlier availability census; it does not
repeat the disk inspection or decode a sensor file. The retained
[converter and loader sources](../evidence/training-partitions/converter-source-ledger-0.1.0.json)
show why the candidate list contains ten earlier frames: the converter defaults
to ten while the selected recipe can randomly draw nine. The initial nine-frame
audit proposal was superseded before SDK execution; its original record remains.

For a fixed sample in every selected log, the SDK's box centers and orientations
are compared with an explicit world-to-ego-to-sensor matrix calculation across
all seven channels. Camera intrinsics, dimensions and annotation population
must also agree. Unavailable SDK velocities remain NaN. This is a metadata
geometry check. The legacy FCOS3D prediction geometry discrepancy remains
unresolved until the actual model preprocessing and predictions are tested.

## Replay, custody and integration

Private custody is `~/.codex/reports/reiyah/training-partitions-2026-09-07/`.
`private/metadata-index-2.sqlite`, the subset directories and compressed temporal
source rows contain the derived data. Raw metadata, maps, per-file identities,
upstream source payloads and SDK wheels remain private. Public artifacts contain
own code, aggregate counts, source pointers and exact digests.

The [verification plan](../evidence/training-partitions/verification-plan-0.1.2.json)
was retained before any subset SDK smoke ran. The two new tools expose their
required input identities through `--help`. Exact executed commands, exit
codes and stream digests are retained in the task's `checks/` directories.
The index is an integrity-bound implementation cache; byte-identical SQLite
recreation across SQLite versions is not claimed.

All 166 offline tests pass: 73 repository tests and 93 inherited tool tests.
The final [execution record](../evidence/training-partitions/execution-0.1.0.json)
binds the run receipts, sources and checks. Gate B development checks pass;
the 52 historical replay entries retain their previous reports and were not
freshly replayed here. The optional attack suite was not run. No Gate A release
validation or operator acceptance is inferred.

The canonical Gate A and separate Gate B owner worktrees are preserved. The
operator authorized engine research and checked main integration. Gate A
remains operator-unaccepted. No new cloud resources are needed for this local
step, and no UI/UX files are part of its change.

## Next discriminating work

Build fresh model-specific annotation caches and the actual object point
database from these contained sources. The CenterPoint database must not reuse
the original full-training object database. Check real point/image decoding,
temporal transforms, voxelization and camera box conventions in the exact
model pipeline before a training run. This checkpoint does not execute that
pipeline or establish training readiness.

Freeze calibration logs, initialization exposure, common optimization steps,
repetitions, operating thresholds and the minimum useful effect before new
fits. The shared-training contrast and second-dataset replication remain
unmeasured. Independent reference adjudication remains unavailable; no human
judgment is generated by this engineering work.
