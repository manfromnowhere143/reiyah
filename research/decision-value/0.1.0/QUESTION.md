# Frozen question and source selection, 0.1.0

Status: exploratory reproduction and decision audit, not a blind benchmark.
Question chosen before deliberate numeric trajectory/checkpoint inspection.
Published aggregate results, README examples, and calibration offsets have
already been read. The GitHub commit-metadata capture incidentally retained
ground-truth CSV patches; their numeric contents have not been displayed or
processed. Those prior exposures remain recorded, not relabelled as held out.

## Decision

For a completed mapping run, should the published FAST-LIO-SAM offline trajectory
replace its published online trajectory if the rule is strictly smaller mean
squared global position error over the complete named checkpoint cohort?

Evaluate all four named sequences separately. The criterion is improvement
relative to the same recorded reference, with zero as the natural comparison
boundary. It is not a safety distance, economic benefit or real-time driving
recommendation. Offline full-trajectory processing uses future information, so
this result can concern completed maps only. No causal online claim follows.

Let A be the stored online positions, B the stored offline positions, and Q the
published checkpoint coordinates after the declared publisher transformations.
For N frozen visits, compare Delta=(sum||B_i-Q_i||² - sum||A_i-Q_i||²)/N.
Negative supports the nominal recorded-reference replacement; positive excludes;
zero is a tie. Missing or invalid operands block the full-cohort conclusion.
Any unresolved numeric discrepancy is retained, never forced to a sign.
Report each mode's actual associations, coverage, squared loss, RMSE and Delta.
Do not pool these dependent repeated-location sequences into an accuracy estimate.

Physical accuracy remains a separate unresolved claim. Static-anchor standard
deviation below5mm and estimated reference accuracy below1cm are not deterministic
per-row error bounds. Source code applies a48.22m SLAM geoid/frame correction,
whereas GNSS uses48.5m. Reproduce the declared transformation, disclose this
reference-frame premise and seek its provenance; do not silently recalibrate it
or call the shared transformation independently validated.

## Frozen operands

Use commit f2921a58caf5a87c1f4f73b48c6f2a5e35f92924 and full tree
804e8dd598f5d5b6515a98badae3c89f89cd31d8 from Willyzw/rtk-slam-eval.
Use ALL checkpoint rows and online/offline FAST-LIO-SAM trajectories in:
construction_seq1, construction_seq2, stadtgarten_seq1, stadtgarten_seq2.
For each sequence capture exactly:
ground_truth/SEQUENCE.csv,
trajectories/fast_lio_sam/SEQUENCE/enu_origin.json,
trajectories/fast_lio_sam/SEQUENCE/traj_online.txt,
trajectories/fast_lio_sam/SEQUENCE/traj_offline.txt.
All16complete file lengths/Git blob identities are frozen in question-freeze.json.
No additional model outputs, GNSS raw streams, images, video or sensor archives.
No inference, trajectory regeneration, dependency installation or threshold tuning.
No subset replacement if a file or case fails. Expected published visit counts
are16,16,36,19 respectively; discrepancies remain explicit.

Use publisher nearest-time semantics with max_dt2s and source order breaking
ties, initially for exact reproduction. A two-second association limit is not
a proven stationary-interval bound. Report actual offsets and missing matches.
Check time finiteness/order/duplicates, raw row shape, source identity, point/visit
identity, complete coverage and consistent origins. Do not substitute0 or drop a
difficult visit. Reference-point semantics are base center, as documented.
No second IMU-to-base transformation may be applied without source evidence.

## Comparison and falsification

C0: retain unmodified publisher reader, coordinate and metric behavior as a
separately authored reproduction. Its summary is not automatically a complete
cohort decision. Its dependency graph for this non-plotting slice uses NumPy,
already available. Do not install the broader optional requirements.

C1, the competent conventional comparator: use the same input identities,
reference/clock premises, complete expected cohort and explicit unknown rules;
validate coverage before comparing the publisher-derived squared losses.
This wrapper is authored here and must be disclosed. Avoid claiming an advantage
by comparing Reiyah only against incomplete summaries or withheld information.

Reiyah: produce a minimal checked decision record from the same bound operands.
A separate arithmetic path reconstructs row identities, nearest associations
and the pairwise loss calculation; shared publisher coordinate conversion is a
declared trusted dependency unless separately checked. Do not fill outcomes as
constants, import one arm's final verdict as the other's expectation, or label
same-author wrappers independent replication.

After a full code/protocol freeze, run both paths and controls. Include missing
pose coverage, changed checkpoint identity, nonfinite/nonnumeric value, repeated
timestamp ambiguity, wrong time unit, incompatible origin/reference frame,
wrong aggregate decision, missing case and unsupported physical-claim mutations.
Preserve every actual first failure and any frozen correction.

Measure full acquisition/preparation, equal-scope computation, separate checking,
receipt/storage overhead and integration costs. Do not equate logical lookup
counts with real survey or human-effort savings. No new engineering effort
measurement has been retroactively obtained.

Investment decision: do not expand a new monitoring framework merely because
nominal results reproduce. Advance a comparative-value claim only if this
experiment demonstrates a useful verified distinction against C1 at equal
information with relevant costs counted. Parity or pure additional overhead is a
valid negative. An actual source/publisher discrepancy is valuable to reproduce
but is not automatically a Reiyah algorithmic advantage or a company accusation.
No outreach or upstream issue filing is authorized.

## Boundaries and next gate

This is one bounded decision audit selected from a concrete primary public lead.
It is not another parameter sweep on exposed Reiyah data. Source/derived cap8MiB,
artifact cap128MiB,5GiB free floor, execution/checking600process seconds each;
failures count. All raw third-party bodies and full traces remain private.
Retain rights uncertainty for the unlicensed code repository, independently from
the HF sensor dataset's CC-BY4 declaration and project page's CC-BY-SA4 text.
Only authored code and permissible derived aggregate facts may later be staged.

This question freeze precedes data inspection. The full implementation freeze
must precede scientific execution. Preserve the historical controller, all closed
owners and all1,433reserved images. Continuing Reiyah mission remains authorized.

