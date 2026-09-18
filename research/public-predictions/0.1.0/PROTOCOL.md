# Frozen public-checkpoint development comparison

Protocol ID: `reiyah.public-predictions.development-comparison`.
Version: `0.1.0`. Status: `exploratory`.

This protocol is frozen before calculating replacement scores. The image
allocation was frozen before any new inference. Feasibility checks of one and
eight images may inspect prediction tensors and decoding agreement; they do
not inspect replacement losses or reference answers. A dated private freeze
binds this document, membership, checkpoint bytes and export settings. A later
implementation freeze binds the executable comparison before its scored run.
Changes create a retained amendment and a new freeze; they do not replace an
earlier result.

## Decision and population

The primary question is whether replacing the frozen public YOLO11n checkpoint
with the frozen public YOLO26n checkpoint strictly reduces mean unit-cost
car detection matching loss on the fixed 64-image development allocation.
This is one model-pair decision on one exposed cohort. It is not a customer
revision history, a two-family study, a three-revision study, COCO or KITTI AP,
physical safety evidence, or an outcome-reserved test.

The allocation contains 64 previously exposed nuScenes CAM_FRONT keyframes,
selected by the retained hash ordering of sensor-sample identifiers from 226
available, previously exposed camera inputs. Selection does not use new
predictions or scores. These inputs inherit earlier case selection and may
share scenes, timestamps and objects. Retain and report those dependencies;
do not treat the images as independent customer decisions. All 1,433 REC-D
outcome-reserved images remain closed.

Retain all 64 assigned images. A prediction or reference failure is a blocked
input, never an empty list. Do not silently replace the cohort with complete
cases. If necessary, declare a secondary available subset with its exact
exclusions and label its decision separately from the primary allocation.

The diagnostic allocations are 64 single-image cases and eight consecutive
eight-image blocks in frozen allocation order. Together with the primary
64-image case, these are 73 overlapping cases, not 73 independent revisions.
Do not add cases in response to favorable scores.

## Frozen export and eligible rectangles

Use only the two retained, byte-bound public checkpoints. Both exports use
the same retained Ultralytics implementation, existing local CPU, FP32,
batch one, 640-square centered linear letterboxing, padding 114, RGB tensor
normalization by 255, confidence strictly greater than 0.25, and at most 300
detections. YOLO11n uses class-aware NMS at IoU 0.7; YOLO26n uses its explicit
end-to-end head with no external NMS. These model-specific decoding contracts
are explicit, not assumed identical. Preserve all source FP32 coordinate
values after publisher clipping and inversion; no decimal rounding is added.
The packet retains all 80 classes, every allocated image and every failure.

For this decision only, select COCO class ID 2, `car`, and rectangles with
pixel height at least 25. Retain all exclusions with their stated rule.
The height cutoff is this development protocol's eligibility rule; it does
not import another benchmark's metric, difficulty policy or authority.
Reference eligibility is nuScenes category `vehicle.car`, positive clipped
area and projected height at least 25. Other categories are out of this
decision's scope, not negative labels. IDs shared across models require
identical eligible geometry and category. Duplicate rows within an output
remain distinct prediction occurrences rather than being silently deduplicated.

Interpret retained JSON numeric spellings as exact rationals for matching.
Two eligible rectangles have an edge exactly when their ordinary continuous
area intersection-over-union is at least 1/2. Use maximum one-to-one matching.
For output P, supplied reference R and matching rank m(P,R),

`L(P,R) = |P| + |R| - 2 m(P,R)`.

The per-image improvement is
`delta = L(A,R) - L(B,R) = |A| - |B| + 2(m(B,R)-m(A,R))`.
The cohort metric is the unweighted mean delta. Tolerance is exactly zero:
support strict improvement only when the valid lower bound is greater than
zero; exclude strict improvement when the upper bound is at most zero.
Otherwise remain unresolved. This is a replacement decision; addition-only
monotonicity is inapplicable.

## Observation and residual uncertainty

One observation unit returns the complete eligible annotation projection for
one requested image, with source applicability and an explicit availability
state. The source is the already held, byte-bound public nuScenes annotation
archive and the retained official devkit 2D projection procedure. It projects
3D corners in the camera frame, retains positive-depth corners, clips their
projected convex hull to the image and takes its enclosing rectangle. Include
all publisher visibility bins. Do not replace projection failures with empty
answers. Qualify category, timestamp, calibration, pose and image bindings.

This answer is a geometric annotation proxy. It is not a newly corrected box,
a tight visible-object annotation, measured human inspection, complete
physical truth, or evidence that occluded objects can be seen. One query is
one replayed public annotation lookup, not one timed reviewer task.

Evaluate three separately reported contracts:

1. `exact_projection`: the supplied eligible rectangles are exact premises
   for this proxy calculation. No physical-truth claim follows.
2. `one_edit_per_image`: after observing each image, its true eligible
   reference may differ by at most one arbitrary insertion, deletion or
   replacement of a rectangle. Replacement includes displacement. Entry to
   or exit from the car class is represented by insertion or deletion.
   Edits across images may be correlated and adversarial.
3. `one_edit_global`: at most one such rectangle edit in the whole case,
   including any of its observed or still unobserved images.

These are declared stress sets, not measured error rates or confidence
intervals. Every edited rectangle must remain in the same image, have
positive area, be clipped to its bounds and satisfy the height policy.
The global budget applies per diagnostic case; overlapping cases do not
constitute independent global-error experiments. Unknown reference cardinality
before a query must not be inferred from an annotation count or source digest.

Before observing an image, use the sound symmetric-difference matching bound
on the visible outputs. For observed answers, compute exact nominal ranks
and sound one-edit rank bounds, clipped by the same open bound. Use the
stronger conventional deletion/enlargement bound when its premises are
proved and implemented before scoring; give identical mathematics to all
arms. A finite candidate search supplies witnesses, not a universal guarantee
that no other rectangle can reverse a decision.

If complete allowed observation leaves the primary or a diagnostic case
unresolved, examine that information limit. Retain concrete admissible worlds
on opposite sides of the strict decision where found, with executable matching
checks. If only a bound gap remains, say so. Do not optimize selection to
claim it can recover information the observation contract never supplies.

## Methods and information boundary

Use a four-cell comparison with the same frozen outputs, metric, residual
contract, query interface and observation-unit budget:

| Arm | Selector | Stopping arithmetic |
| --- | --- | --- |
| A | Largest remaining open-bound width, then frozen image ordinal | Conventional independent matching and sound interval bounds |
| B | Same selector as A | Reiyah checked matching plus the same interval bounds |
| C | Largest absolute prediction-count difference, then open width, then ordinal | Same checked stopping as B |
| D | Same selector as C | Same conventional stopping as A |

The fixed candidate selector uses only eligible predictions. It is not
trained, tuned or selected after outcomes. Random selection is not the
headline comparator. The conventional implementation receives maximum
matching, direct sufficient stopping and all valid bound improvements used
by Reiyah. Include a direct full-eligible-image audit as a cost reference;
zero-width identical-output images need no observation. Use IHS only if a
finite alternative-world premise makes it applicable; do not relabel a
missing-reference problem as that different finite search problem.

After the scored comparison, compute the minimum number of queries that
could certify each fully observed decision using these same bounds and
unit observation costs. This retrospective certificate-size floor may use
the retained answers; it is an informed lower bound, never an executable
selector that was blinded to them. For additive bounds, order each answer's
actual bound improvement. For the global-edit bound, condition on each
possible maximum residual penalty and solve the resulting ordered-gain
problem. Validate this calculation against exhaustive small subsets.
Compare observed query counts to this floor to distinguish selector slack
from the limited remaining opportunity under the declared mathematics.

All arms receive identical cache policy. A case starts with no observed
reference answers; cache each returned answer and measurement within that
case. Report a separate distinct-image union for shared preparation across
dependent cases and arms. Do not charge a source lookup only to one arm.
The observation budget is at most one query per allocated nonzero-width
image. A failed query remains a query and blocks a required input. Both-zero-
query comparisons are ties; cost per resolved decision is undefined if no
decisions resolve.

Only the service process reads private answer files. A worker initially
receives prediction operands, frozen ordering/cases, public protocol and
availability diagnostics needed to preserve blocked inputs. It does not
receive reference rectangles, counts, digests, matching graphs, loss hints
or correction-derived alternatives before a query. The response to a query
then supplies its bound answer. Reference preparation provenance and hashes
remain outside the visible packet. Document actual process and filesystem
boundaries; dataflow separation is not independent blinding.

## Retention, verification and cost

Freeze and retain implementation/source bindings before the scored run.
Retain incremental query logs, exact returned answers, every stopping point,
final outcomes, all assigned cases, native proof payloads and conventional
cross-checks. Include known-bad admission and observation controls. Replay
all newly produced decisions and witnesses, including adverse and blocked
ones. Same-code replay is not independent scientific replication.

Report actual query counts, selection, source service, matching, compilation,
proof production and proof checking time. Include acquisition attempts,
download bytes, environment setup, export feasibility/retries, full exports,
reference preparation, integration, testing and verification. Preserve wall
intervals and do not add overlapping intervals as elapsed session time.
The local feasibility cap is 2 GiB of all new asset/dependency downloads and
60 cumulative minutes charged to prediction calls; it is not a benchmark
cost budget. Include retained failure costs.

Human preparation, review and integration effort, billing, agreed cost rates,
customer demand and economic savings remain unknown unless measured. A
compute-only ratio is not total-work savings. The prior parity results remain
unchanged. The investment targets remain at least 3x fewer expensive
observations and 2x lower full cost at matched correctness and resolution;
these are targets, not claims made by this development protocol.

Public Git receives owned code, the protocol, scoped aggregate results and
source/terms descriptions. Keep image and annotation payloads, weights,
private answers and outputs without established redistribution permission
outside Git. Attribution and derivative-data terms must be retained and
reviewed for the exact artifact being distributed. No outreach, deployment,
paid service, training, reserve opening or Gate A acceptance is part of this
experiment.
