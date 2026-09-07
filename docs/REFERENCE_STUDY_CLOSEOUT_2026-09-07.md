# Reference study implementation closeout

Document ID: `reiyah.reference-study-closeout.2026-09-07`

Version: `0.1.0`

Lifecycle status: `exploratory`

This revision executes the next investigation chosen by the
[research board](RESEARCH_BOARD_2026-09-07.md). It is based on local research commit
`4deb1d19ef1db6fa37fb6b20ca0b4ffda93c4bcc` and is isolated from both active worktrees.
The [study report](REFERENCE_ADJUDICATION_STUDY_2026-09-07.md) contains the question,
prior work, rejected design, mathematical assumptions, experiment and next decision.

## Completed empirical preparation

The replacement sampling protocol was frozen before independent judgments. Two selection
runs produced identical bytes: 240 detections, 60 in each reference group, covering 93 scenes.
The first design and its failed precision check remain retained. Neither sample is described
as unseen-data preregistration.

All 4,284 requested sensor assets were recovered, totaling 935,193,288 bytes. The transferred
archive and each individual asset matched their source hashes. Three source metadata tables
also matched the exact local archive. Format and image-dimension checks passed. The packets
contain 4,956 available evidence slots and 84 explicit scene-boundary slots; repeated uses of
one file are not counted as independent sensor files.

Every case's fixed center projects inside at least one available current camera image. This
does not demonstrate object visibility or existence. Across 1,440 case-camera slots, absolute
sensor/reference offsets have median 0.0244045 s, 95th percentile 0.04418645 s and maximum
0.047047 s. At an assumed speed of 30 m/s, the largest displacement scenario is 1.41141 m.
None exceeds 2 m in this selected cohort. This does not bound annotation error or establish
that any candidate is mislocalized.

Original camera files are displayed with separate geometry overlays, and local lidar views
retain links to the raw scans. A rendered case was visually inspected for source-image loading,
marker display, chronology, evidence identifiers and uncertainty wording. This engineering
inspection supplies no independent adjudication labels.

## What remains unmeasured

Independent reviewers have not been assigned or verified, and zero judgments have been
collected. Every group retains a [0, 1] support confidence set. Physical-performance estimates
are null. Review agreement, if later collected, will measure a fallible evidence-review
protocol; it will not automatically become ground truth or a safety claim.

The [reviewer instructions](../research/reference-study/0.2.0/REVIEWER_INSTRUCTIONS.md)
and bound schema are ready. The next required observation is the two independent, blinded
human judgments per selected case. No external messages were sent and no model was substituted
for a reviewer. A third-review procedure, modality ablation or confirmation cohort requires
its own prospective protocol; it cannot be silently added to this one.

## Integrity and validation

The [run closure](../evidence/reference-study/run-closure-0.2.0.json) binds the new source
files, inherited helper, protocol releases, schema, aggregates and numerical environment.
It is a development-run record, not a hermetic release environment or independent scientific
replication. The selection key, source cases, images, scans, rendering and retrieval inventory
are retained privately under `reference-study-2026-09-07` outside public Git.

The reference-study test suite exercises 16 scientific and integrity counterexamples,
including coordinate composition, invalid sensor data, reference exclusions, equal-probability
selection, exact finite-population coverage, unresolved mass, failed citations and repeated
reviewer identity. The earlier 14 research-board regression tests retain the matcher rejection
and failed-process counterexamples. Their scratch-copy input closure now includes the new
research directory, so link checking remains meaningful.

Executed outcomes are recorded in the
[study regression record](../evidence/reference-study/regression-0.2.0.json),
[board regression record](../evidence/reference-study/board-regression-0.2.0.json),
[study verification record](../evidence/reference-study/verification-0.2.0.json) and
[Gate B development check](../evidence/reference-study/gate-b-check-0.2.0.json).
The existing replay manifest and claim register are unchanged: this revision prepares the
next measurement rather than admitting a new physical-performance claim. Existing transcript
digest checks are not represented as fresh replays of all historical experiments.

## Workspace, cloud and authority boundaries

The original GPU VM could not start because its zone lacked L4 capacity. A temporary clone
of the separate dataset disk was attached read-only to an ephemeral CPU reader and mounted
without journal replay. Only the selected public sensor assets and metadata checks were
read for this study. The original disk stayed attached to the original stopped VM. Temporary
reader and clone cleanup is recorded in the
[cloud closeout](../evidence/reference-study/cloud-closeout-0.2.0.json).

No original perception model, online monitor, driving runtime, training, deployment or public
dataset upload was added. Raw third-party payloads are absent from the research commit.
The Gate A contracts and release operands are unchanged. The research README and handoffs
are navigation updates, not a newly validated Gate A release packet. Operator acceptance
remains unaccepted, and the preceding K129 contract replay is not promoted into implementation
or empirical authority. This task does not claim a new Gate A change or release.

The local topic branch is `research/2026-09-07-reference-study`; commits use Daniel Wahnich
alone as author and committer. Neither active worktree is switched or edited. The separate
Gate B historical replay update at `9464ff79a823a91037604bb8343e984b29c128a5` remains separate.
No merge or push is claimed by this closeout.
