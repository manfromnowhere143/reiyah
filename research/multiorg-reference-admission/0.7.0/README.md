# Capacity recovery and the selected cohort

Safe cleanup made a new bounded attempt possible. One more selected image now
has a complete, checked detector pair: **two of the four selected images are
complete**. The next image stopped when available storage fell below its
remaining-capacity allowance. The final selected image was not started.

The complete new pair contains 156 tiles per model, 312 forward passes and
5,460 retained arrays totaling 5,839,207 bytes. The unchanged numerical checker,
behind a newly qualified resource-receipt consumer, verifies the input tensors,
saved outputs, origin handling, coordinate conversion and global NMS. Faster has
251 analysis detections; YOLO has 9. Detection counts are not a comparison of
accuracy. No new reference matching was performed.

| Stage | Retained outcome |
| --- | --- |
| Prior Plate 4 / image 7 | Complete pair and three reference comparisons retained from [0.5.0](../0.5.0/README.md). |
| Plate 23 / image 0 | New complete pair; 5,460 arrays checked. |
| Normal Plate 31 / image 6 | Interrupted at the remaining-capacity boundary; no terminal result. |
| Plate 23 / image 1 | Not started after the stop. |
| Four-image, twelve-case endpoint | Incomplete; no new cohort ranking or scientific null. |

The interrupted worker stopped after 77.005 worker seconds, or 86.949 supervisor
seconds including preflight. Available space was 7,577,542,656 bytes against a
7,817,443,568-byte remaining-capacity requirement, still above the unchanged
4 GiB floor. The immediately preceding sample recorded 8,653,103,104 bytes.
The journal records that decline; it does not identify the writer or prove a
swap explanation. The worker was absent at closeout. Partial files remain
retained and are not treated as a complete observation.

## What changed

The [consumer contract](consumer/CONTRACT.md) now admits the actual new
supervisor schema before using the unchanged numerical checker. It binds outer
exit, receipt, journal, log, source freeze and runtime, and rejects missing or
inconsistent evidence. The [matching adapter](matching/README.md) qualifies
this explicit composition while preserving the original matching arithmetic.
It remains empirically unexecuted because the full cohort is unavailable.

The public source projection passes **85 authored controls**: 16 resource,
5 numerical-checker integration, 28 inherited matching and 36 resource-matching
cases. A separate review adds 46 consumer controls; eight harmless launcher
controls cover success, nonzero exits, exclusive logs and timeout cleanup.
These are same-investigation checks, not independent scientific replication.
All 112 prospective inference bindings remain unchanged.

## Cleanup and next dependency

The operator authorized safe Mac cleanup. Selected disposable files had
5,284,786,176 bytes of recorded allocation, excluding native cache removals
without exact byte reports. Personal files, installed runtimes, active
environments, research evidence and retained release archives were preserved.
Recorded allocation is not a claim of exclusive physical bytes reclaimed.
See the [aggregate cleanup record](cleanup-summary.json).

This attempt is closed. Preserve both complete pairs and every failed record.
The next dependency is more durable capacity for the two still-incomplete
selected images, followed by a fresh bounded plan and exact reuse qualification.
The observed storage variability cannot be resolved by relabeling partial
output or lowering the existing floor. No replacement image, model or scoring
rule is justified by this stop.

The owner reached empirical closeout in 7,380.803 wall seconds, exceeding its
7,200-second target. Only required evidence verification and publication followed;
no additional empirical attempt or matching run was made. Earlier costs remain.

Read the [exact result](result.json), [methods and limits](METHODS.md),
[public replay](public-replay.json), [consumer review](review/CODE_REVIEW.json),
[launch review](review/LAUNCH_REVIEW.json) and [provenance](provenance.json).
The broader HARBOR mission remains; this milestone establishes neither
scientific superiority, complete-work savings nor Gate A operator acceptance.

## Reproduce authored controls

From the repository root, in an existing environment with the previously pinned
numeric dependencies, the consumer controls are:

```sh
python -B research/multiorg-reference-admission/0.7.0/consumer/test_resource_consumer.py
python -B research/multiorg-reference-admission/0.7.0/consumer/test_integration.py --support research/multiorg-reference-admission/0.6.0 --supervisor research/multiorg-reference-admission/0.6.1/monitor/supervise.py
```

The [matching instructions](matching/README.md) specify its authored replay.
Raw images, weights and annotations remain private. Authored replay does not
recreate neural execution or complete the missing empirical comparisons.

The exact `run_recovered_cohort.py` is retained for source review and the
harmless `review/test_launch_capture.py` controls. Its empirical main belongs
to this closed owner; it is not an authorization or command to rerun the study.
