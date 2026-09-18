# Retained-score operating-policy sensitivity

Version `0.1.0`. Status: `exploratory`. Freeze this plan, source qualification,
implementation and controls before computing new threshold-dependent outcomes.
All preceding development results are known. No threshold is selected for
deployment or presented as a held-out improvement.

## Scope and source qualification

Use only the same 64 exposed images, two qualified local prediction packets,
original annotation projection and verified temporal reference worlds. Both
packets explicitly retain scores strictly greater than 0.25, every image and
the distinction between publisher-empty, processed, failed and missing. Verify
the original source bindings, complete allocation, exact configuration,
admission, score range and eligible-operand reconstruction before freezing.
Do not read images, raw head tensors, weights, additional metadata or reserved
outcomes. No inference, downloads, training or recalibration.

The policy is a stricter filter of the retained, already postprocessed output:
keep a detection exactly when its retained decimal score is greater than t,
for t in [1/4,1]. YOLO11n's NMS and YOLO26n's end-to-end export remain separate
source contracts. Do not claim a fresh predictor execution or altered NMS.
No statement about missing below-floor detections is possible from this packet
study. Scores are not assumed calibrated probabilities. Equal numeric thresholds
do not establish equal detector operating conditions.

Keep car category, height at least 25, exact-decimal coordinates, IoU at least
1/2, maximum one-to-one matching and unit false-positive/miss costs. Reassign
metric identities after each filter by exact geometry and duplicate occurrence
count, so equal multisets share identities even when different source duplicate
occurrences survive. Preserve a separate source-detection join and every
excluded row. Missing source inputs cannot become a filtered-empty result.

## Allocations

1. On the primary full 64-image case, evaluate the complete common-threshold
   continuum. Partition [1/4,1] at every distinct eligible score from either
   model. Use left-closed/right-open cells with representative equal to the
   left boundary, plus the singleton t=1. Strict comparison removes tied
   scores together at the boundary. Retain every cell, including duplicate
   metric states and the empty-output endpoint.
2. Retain all 73 original overlapping cases at the eight fixed anchor thresholds
   1/4,7/20,1/2,13/20,4/5,9/10,19/20,1. Preserve full membership and all blocked
   inputs. Do not add favorable subgroups or treat rows as independent trials.
3. For the nominal projected reference only, retain each detector's complete
   individual threshold curve and every Cartesian pair of those cells on the
   primary allocation. Report its attained false positives, misses and unit
   loss; preserve ties. Summarize the nondominated false-positive/miss points
   and, for every integer false-positive budget from zero through the larger
   floor prediction count, the fewest attained misses under that budget for
   each detector. Retain all feasible tied threshold cells. An infeasible budget
   remains unavailable, not zero misses. This is a retrospective development
   frontier, not an owner-approved policy or a new measured cost.

## Seven reference contracts

Retain the original exact projection, one arbitrary edit per image and one
arbitrary edit globally, plus current-strict, current-partial, union-strict
and union-partial temporal contracts. Their reference premises and eligibility
are unchanged. A blocked temporal image blocks its whole case even when a
threshold produces empty outputs. Do not substitute a complete subset.

For each distinct filtered image state, compute the original-reference ranks,
all single-reference-deletion ranks and the preceding competent conventional
deletion/enlargement bound, clipped by the shared-prediction bound. Use the
same mathematics for both checking paths. Compute known temporal ranks and
the fixed-census optional-reference bounds using the original unknown counts.
Global-edit case bounds use the greatest single-image adverse deviation;
per-image and temporal bounds sum over the complete allocated case.

Use an unchanged finite bank of admitted worlds: original and all one-reference
deletions, both preceding geometric one-edit witnesses, and every retained
temporal proof world admissible for its current/union unknown census. Recompute
their ranks on the filtered predictions; do not reuse a native payload for
changed operands. Select the bank's smallest/largest differences, preserving
all bank measurements. No new geometric search occurs. A bank with no opposing
worlds does not prove a universally unresolved case decidable: label it a bound
gap. Earlier opposite worlds and all source results remain intact.

## Checks, bounds and cost

Cache measurements only by the exact filtered image and reference bytes.
Conventional max-flow and native proofs use identical operands. A separate
checker rebuilds filtering, duplicate identities, threshold coverage and case
membership; checks matching through augmenting paths and native payloads; and
independently derives the arithmetic and false-positive budget minima. Search
or source failures remain retained, never dropped cases.

Before actual scoring, test threshold equality/ties, empty versus missing,
duplicate identity remapping, incomplete packet joins, exact interval coverage,
matching changes after deletion, shared-identity bounds, global/per-image
composition, blocked temporal cases, frontier dominance/ties/infeasibility,
and corrupted proof/result records. At the inherited floor, require the nominal
comparison and all universal reference-family bounds to match their retained
predecessors. This is a regression constraint, not another independent result.

Resource caps: at most 1,024 individual threshold cells per detector, 2,048
common cells, 4,096 distinct filtered image states, 20,000 distinct native
world certificates and 1,000,000 nominal cell pairs. Each actual scoring or
verification process has a 1,200-second wall limit. Reaching a cap is an explicit
incomplete outcome; never reduce the allocation to get a favorable answer.
These are local offline research calculations, not additional model calls.

Publish all scalar case/threshold results and detector curves with scoped
nuScenes attribution. Keep per-detection score/geometry joins, source image identifiers, native
payloads and private world operands outside public Git. Retain complete private
cell-pair outcomes, all limits/failures and known phase costs. Do not convert
case counts, calibration assumptions, proxy loss or runtime into human savings,
customer demand, empirical error rates or operational safety. All 1,433 reserved
images remain closed; the original ten-hour clock and excluded interruption
remain unchanged.
