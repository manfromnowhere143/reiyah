# Camera-time reference sensitivity

Version: `0.1.0`. Status: `exploratory`. Freeze this plan and implementation
before any new projection or scored comparison. Earlier development results
and the metadata-only preparation counts are already known.

## Question and allocation

Can the existing replacement proxy be decided after applying one explicit
motion model at the actual camera timestamp, while retaining missing motion
evidence? Use the same 64 exposed CAM_FRONT images, fixed YOLO11n/YOLO26n
outputs, 73 overlapping cases and exact-decimal IoU threshold of 1/2. Keep
car category, 25-pixel minimum height, supplied dimensions and unit false
positive/miss penalties unchanged. Strict improvement means mean old loss
minus new loss greater than zero. No new images, inference, training, downloads,
reserved outcomes, human review or selector comparison occurs.

## Declared motion model

For a current car instance with a valid annotation in the immediately preceding
sample of the same scene, interpolate global center linearly and orientation
by the retained pyquaternion SLERP path. Use the current annotation's dimensions
and category. Use the actual camera pose/calibration from the inherited packet.
The camera time must be in the closed sample-time bracket; its span must be
positive and at most 1,500,000 microseconds. No clamping or extrapolation.
Require reciprocal instance-annotation links, finite positive dimensions,
finite centers, and nonzero finite quaternions. The span limit is a declared
restriction, not a measured accuracy guarantee. Current-time equality permits
the current box without an earlier track.

Project through the retained official 1.2.0 exporter: corners with positive
camera depth, convex hull intersected with the image canvas. This preserves
the predecessor proxy's near-plane and occlusion limitations. Keep every car
in the census before projection; do not select tracks by current visibility,
height, prediction overlap or match status. Record modeled eligible, modeled
outside/too-small, missing motion and invalid geometry separately. Invalid
geometry becomes unavailable, never a negative observation.

These are conditional motion-model outputs, not corrected annotations or
physical truth. Linear motion, SLERP, fixed dimensions, census completeness,
the projection convention and annotation accuracy remain assumptions.

## Four reference contracts

1. `current_strict`: current annotated car instances form the fixed census.
   Every instance must have a usable modeled projection or explicit modeled
   ineligibility. Otherwise the image is input-blocked.
2. `current_partial` (primary): use the same census. Every unavailable instance
   contributes one optional unknown eligible rectangle. It may instead be
   outside the eligible reference set. Its geometry is unrestricted within the
   canvas, with height at least 25 pixels. Missing is represented as uncertainty,
   not replaced by an empty or static box.
3. `union_strict`: use the union of current and immediately preceding annotated
   car instances. Predecessor-only instances have unknown presence/geometry.
   If the preceding sample is unavailable, the union census is unavailable;
   never substitute an empty predecessor.
4. `union_partial`: apply the same optional-rectangle uncertainty to that union.
   A missing preceding sample still blocks the image because census membership
   is unknown. This is a separate scope, not a post-hoc subset of the primary.

Retain all 292 case/contract rows. Any blocked image blocks its entire case
for that contract. Do not silently replace a case with its complete subset.
Unknown objects absent from both annotated censuses remain outside these
contracts. Current-only births and predecessor-only disappearances are not
reinterpreted as proven physical events.

## Bounds and attained worlds

For each image, let nA,nB be fixed prediction counts, rA,rB their maximum
matching cardinalities against the known modeled references, and k the number
of optional unknown rectangles. The known-only world has difference
D0 = nA-nB + 2(rB-rA). A sound enclosure is
[D0-2 min(k,nA-rA), D0+2 min(k,nB-rB)], intersected with the inherited bound
[-s,s], where s is the count of prediction identities unique to either output.
Every optional reference increases each matching rank by zero or one; the
shared-identity bound remains valid. When k=0, this is the exact finite proxy.
Sum image bounds and divide by the case's full allocated image count.

Retain conventional max-flow ranks and native checked matching proofs on the
known world and each attained adverse world. Give both checks identical
geometry and thresholds. This is a certificate check, not a new claim of query
or cost superiority. An enclosing interval is not automatically an attained
extremum or proof of ambiguity.

For constructive stress worlds, use a fixed pool of eligible prediction
rectangles plus each rectangle shifted by one quarter of its width/height
in the four axis directions, retaining only wholly in-canvas candidates.
Deduplicate exact rational geometry, sort lexicographically, and cap the pool
at 256 candidates. For each direction, repeatedly add the candidate yielding
the largest strict improvement of the difference, stopping at k additions,
no strict single-addition improvement, or 4,096 total candidate evaluations
per image/contract. Duplicate geometry for different unknown instances is
allowed. Record truncation and search limits. This deterministic bounded search
does not claim complete geometric search or exact extrema. Known-only and
all attained worlds remain retained even if limits are reached.
Search the lower direction before the upper direction under that shared
evaluation cap; stop a direction once its universal endpoint is attained.
The inherited native adapter allows at most 128 references per attained world;
stop constructive additions at that limit without shrinking the universal
unknown-reference family or claiming that all its worlds were searched.
Identical known geometry and unknown-instance membership reuse the same
search and proof records across census contracts; charge their computation once.

A case is supported if its universal lower bound is positive, excluded if its
universal upper bound is nonpositive, and unresolved otherwise. For unresolved
cases distinguish attained opposite-decision worlds from a remaining bound
gap. Report independently whether each universal endpoint was attained.

## Verification, costs and retention

Before actual data, use synthetic controls for source identity, timestamps,
missing versus empty, changing car eligibility, quaternion antipodes and
rotation, camera transforms, clipping, optional-reference bounds, matching
alternation, search limits and complete-case accounting.

Verify modeled centers/orientations and projection through a separately written
scalar quaternion/matrix and convex polygon clipping implementation. Numerical
agreement tolerance is 1e-7 pixels plus 1e-12 times coordinate magnitude;
retain maximum discrepancy and every failure. The scored operands are the
serialized official-path floating-point outputs interpreted as exact decimal
rationals, not exact real-valued physical geometry. Independently compare
eligibility and matching edges using the alternate projection; a disagreement
blocks that image's numerical verification rather than being rounded away.
Center agreement uses 1e-9 global coordinate units plus 1e-12 relative magnitude;
rotation-matrix entries must agree within 1e-10. These are numerical checks,
not sensor or annotation uncertainty estimates. Report eligibility entry/exit
and the maximum absolute box-coordinate change against the inherited projection
only for successfully modeled objects. Keep originally eligible objects with
unavailable motion in a separate unassessed category.

Recompute conventional ranks independently with augmenting paths, check all
native witnesses, unknown-instance budgets, all bound arithmetic and every
assigned case. Bind complete source membership and derived bytes. Separate
algorithmic agreement from independent scientific replication. Retain source
preparation, projection, search, proof, checking and failed-process costs without
overlapping wall-time double-counting. Human work and full economics stay unknown.
Keep raw geometry and individual private proofs outside public Git; publish
only scoped derived tables, limitations, code, synthetic tests and attribution.
