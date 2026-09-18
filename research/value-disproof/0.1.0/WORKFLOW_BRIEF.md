# Workflow and case request brief

Version 0.1.7, 18 September 2026. Prepared locally; no outreach sent.

Purpose: determine whether a recurring perception revision decision is expensive
because of uncertain reference evidence, and whether resolving that uncertainty
changes a decision the team actually makes. Target five detailed accounts and
two concrete comparisons from independent teams. These are acquisition targets,
not existing customer evidence.

The concrete current candidate is a decision to replace a frozen YOLO11n
checkpoint with a frozen YOLO26n checkpoint on a fixed 64-image exposed camera
cohort, requiring strictly smaller mean car matching loss. The
[executed development comparison](../../public-predictions/0.1.0/README.md)
supplies complete checkpoint/configuration/image bindings and a runnable
conventional baseline. Both resolved primary contracts already reach their
minimum query counts, 46 with exact projected reference and 47 with one possible
reference edit globally. Checked stopping makes the same decisions and queries.
This does not identify a team that uses this particular proxy as a release gate.

The specific missing workflow evidence is what inspecting an image establishes.
The current answer is a replayed geometric projection of public 3D annotations,
not a timed human correction. Allowing one arbitrary eligible box edit per
image leaves the primary decision unresolved; an admissible 15-image world
reverses it. That stress budget is not a measured annotation-error rate.
The derived result portions retain the [nuScenes attribution and terms](../../public-predictions/0.1.0/DISTRIBUTION.md).

A separately frozen [localized translation test](../../reference-translation/0.1.0/README.md)
keeps the primary proxy decision supported at 4 pixels, while an admissible
world at approximately 7.7109 pixels changes 19 images and reverses it. The
exact critical infimum is about 7.6792 pixels and is not attained. This only
allows one fixed-size reference translated along one axis per image. It
identifies a concrete precision question for an owner; it does not measure
how often a reviewer makes that error.

The subsequent [simultaneous translation result](../../translation-2d/0.1.0/README.md)
retains support through a 5-pixel coordinate radius and exhibits an excluding
world at 5.03125 pixels. All evaluated extrema verify; the reported critical
bracket is not an exact infimum or a measured reviewer tolerance. Allowing
both coordinates to move widens the stress family. Equal false-positive and
miss penalties are another explicit premise still needing owner justification.

The [penalty-tradeoff study](../../loss-tradeoff/0.1.0/README.md) makes that premise
concrete: against the supplied projection, the candidate has 58 fewer false
positives and 21 more misses. Nominal strict improvement requires the miss
penalty to be less than 58/21 times the false-positive penalty. With a 5-pixel
two-coordinate residual, universal support requires a ratio below 40/39.
The broader one-edit-per-image primary family remains unresolved for every
common nonnegative penalty share. An owner must justify the actual loss,
the cost of an unresolved decision and the residual reference contract before
interpreting this proxy as a release criterion. These decision weights are
not measured human costs or evidence of customer demand.

The [camera-time sensitivity](../../reference-timing/0.1.0/README.md) tests one
explicit interpolation premise while retaining missing motion. The current
census has 62 unavailable car instances across 25 images. Allowing their
geometry/presence to remain unknown leaves the primary comparison unresolved,
with checked worlds on both sides of strict improvement. Including preceding-
only cars also leaves one image's census unavailable, blocking the complete
population for that broader contract. Interpolation is not a human correction
or evidence that publisher annotations are wrong. An owner needs to establish
what time, visibility and object census the reference actually covers, how
missing tracks are adjudicated, and which uncertainty survives that process.
The subsequent [geometric witness refinement](../../reference-witness/0.1.0/README.md)
finds checked opposing worlds for all seven previously unproved gaps. Every
one of the 57 unresolved timing rows now has that evidence. This resolves the
mathematical gap while preserving the missing-information obstacle: selecting
more efficiently among the same admitted answers cannot settle those cases.

The [retained-score operating study](../../operating-policy/0.1.0/README.md)
shows why the operating criterion also matters. On this exposed cohort, the
retrospective minimum nominal unit losses are 207 for YOLO11n and 210 for
YOLO26n, despite the new checkpoint's lower loss at the shared 0.25 cutoff.
At an allowed false-positive count of 69, the old checkpoint can attain 154
misses versus the new checkpoint's 156. Neither frontier uniformly dominates.
These observations choose no deployment threshold or calibrated score model.
All 515 common stricter-threshold cells with remaining detections still have
opposing worlds under the one-edit-per-image contract. An owner must specify
the acceptable false-positive/miss tradeoff and a prospective operating-policy
validation procedure; equal numeric score thresholds alone do not establish it.

A decision owner would need to provide genuine old/new revision provenance,
the actual release criterion, complete image membership with failures retained,
the best existing baseline, and an authorized observation/adjudication process.
They would need to measure whether review resolves missing objects, class
changes, occlusion, box displacement and correlated scene errors; record the
precision and uncertainty that remain; and explain what action follows an
unresolved comparison. A new study must freeze these obligations before
accessing its reserved outcomes.

For this candidate, separately measure cold preparation and integration,
actual reviewer and adjudicator time, failed or repeated reviews, shared
reference reuse across real revisions, native proof/checking overhead and
agreed full cost. Instrument both competent workflows with the same information
and correctness/resolution obligations. Machine timings and annotation lookup
counts already exist; reviewer time, prices, demand and an owner-approved
release decision remain unknown. The 3x-observation and 2x-full-cost investment
targets remain unmet. Do not start outreach or treat this brief as a customer
conversation.

Ask about the most recent specific instance:

1. What exact revision and acceptance criterion were being compared? Did the team
   actually wait for this result before taking an action?
2. Which uncertain labels, missing objects, positions, calibration or conditions
   prevented a justified decision? What measurement could distinguish the cases?
3. Who prepared, inspected and adjudicated the evidence? How long did each stage
   take, including repeated work, failed reviews and unresolved cases?
4. Which scripts, analytical bounds, cached observations, sample audits or
   selection methods already reduced the work? What remained expensive?
5. What error/resolution obligation is required? What happens if the comparison
   remains inconclusive? Which missed regressions matter operationally?
6. Who owns the budget and recurring decision? Which real cost rates and invoices
   can be used? Would a continuing pilot be useful if the measured gain survives?

For a candidate comparison, request an explicit authorized data/access scope:

- A and B outputs from genuine documented revisions, timestamps and provenance;
- a fixed evaluation population, scene/sequence membership, metric and thresholds;
- original reference evidence, available correction mechanism and residual ambiguity;
- measurement instructions, attainable precision, reviewer qualifications and costs;
- preprocessing, frames, calibration, source rights and permitted retention;
- the current best workflow, baseline scripts and already cached observations;
- actual outcomes kept separate from method development until the protocol freezes.

Record unavailable fields as unknown. Different detector names alone are not a
revision history. Do not ask a team to disclose confidential records without an
appropriate data arrangement. Start with a description or a shareable minimal
example if that is what the owner authorizes.

For timed work, separately record preparation, integration, observation, review,
adjudication, proof generation/checking, retries, repair and wall time. Keep cold
start and a fixed revision-sequence amortization separate. Report every assigned
comparison, even if it times out or cannot be resolved. Query counts multiplied
by invented prices do not measure human savings.
