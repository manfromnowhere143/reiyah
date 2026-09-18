# Two-coordinate reference translation on the same exposed inputs

Plan ID: `reiyah.translation-2d.development-plan`.
Version: `0.1.0`. Status: `exploratory`.

The axis-only result at 770bbb2 is already known. It cannot certify simultaneous
two-coordinate motion. Freeze this plan and its implementation before any new
2D search. Preserve the previous protocols, broader arbitrary-edit results,
axis infimum, query floors and baseline parity. This is a declared exploratory
follow-up on the same exposed development population.

## Family and decisions

Reuse exactly the same 64 images, two frozen checkpoint outputs, supplied eligible
reference rectangles, 73 cases, IoU threshold of at least 1/2, unit matching loss
and strict positive mean improvement criterion. No new image, model, inference,
download, training, human review or reserved outcome is part of this plan.
All 1,433 REC-D outcome-reserved images remain closed.

At most one existing eligible reference rectangle per image may translate by
offsets `(dx,dy)` with `max(abs(dx),abs(dy)) <= r`. Both coordinates may change
at once. Its shape and category stay fixed and the translated rectangle must
remain wholly inside its image. The unchanged answer is allowed. Movements
across images may be arbitrarily correlated. This product uncertainty set
does not enforce a shared physical trajectory or camera-calibration model.
It is a declared stress set, not a measured error rate or actual reviewer
precision. Insertion, deletion, class change, resizing and more than one
edited rectangle per image remain outside this particular family.

Evaluate the same radii **0, 1, 2, 4, 8, 16, 32, 64 pixels** and every one of the 73 cases.
Retain all 584 case/radius rows. Report universal enclosures and attained values
separately. A decision may be unresolved because both decisions have admitted
worlds, or because a remaining bound gap is not closed within the work limit.
Do not equate a lower bound crossing zero with an attained excluding world.

After the fixed radii, perform at most eight deterministic bisection steps
for the primary supported-radius / attained-reversal-radius bracket, initially
[0,8]. The previous radius 8 axis witness is already a valid candidate in the
larger 2D family, but recheck its exact geometric applicability. A step moves
the supported endpoint only when the universal lower bound is strictly
positive, and moves the reversal endpoint only when an admitted world has
nonpositive delta. If neither is established, stop that bracket search and
retain the bound gap. Report a bracket, not an exact minimum or infimum.
Do not alter the radius sequence or work limit after examining new results.

## Sound geometry and common matching mathematics

A translated fixed-size rectangle has a rectangular legal position domain.
For each prediction, compute exact minimum and maximum intersection area
over that domain from the two separable one-dimensional overlap ranges.
The overlap on one axis is piecewise linear; its extrema occur at domain
endpoints or its finitely many slope changes. At IoU at least 1/2, intersection
must be at least one third of the sum of the two fixed areas. This gives
edges that hold everywhere and edges that can hold somewhere in the domain.

Remove the potentially moving reference from the original matching graph.
Adding one new reference increases each output's matching rank by zero or
one. Its rank increases exactly when its neighborhood intersects the output's
augmentable prediction set: an augmenting path must start at the new unmatched
reference and use one of those neighbors. Compute these sets against the
unchanged deletion base. Shared prediction identities remain shared, preserving
the joint constraints between the two outputs.

Enumerate the four possible pairs of rank increments consistent with mandatory
and possible neighbors. Their loss differences enclose every geometric
position in the domain. This neighborhood relaxation may admit combinations
with no geometric witness; never call it exact geometry on that basis alone.
Supply all this mathematics to the conventional implementation. Native proofs
check actual attained geometric worlds, not an invented physical world for
each relaxed graph combination.

## Bounded spatial refinement

Evaluate deterministic corners and the center of each domain and retain any
attained improvement of the current per-image extrema. Previous axis witnesses
at the same frozen radius may be used as declared initial candidates, with
their source and radius checked. They are already exposed answers, not hidden
information supplied to a new selector experiment.

Refine a region only if its sound interval can improve an attained per-image
extremum. Split its longest nonzero side at the exact midpoint; break ties on
x. Both children are closed, so their union includes the shared split boundary.
Choose the next region by the largest remaining integer outcome gap, then
reference ordinal and tree path. Stop when every remaining interval lies
inside the attained extrema, or when the fixed work limit is reached.

Use at most **2,048 evaluated regions per image/radius** and depth at most 24.
Cache deletion-base mathematics, evaluated positions and identical checked
worlds within their exact source context. Reuse an already computed radius
when bisection requests it again; retain its original cost instead of counting
a cached lookup as fresh research. Do not raise the inherited Engine limit.
Each stopped region remains in a covering partition with its valid bounds.
No unresolved region may be dropped from a reported universal enclosure.

The independent verifier reconstructs overlap extrema and augmentability with
separate matching arithmetic, verifies the entire covering subdivision tree,
checks native attained worlds, and recomputes every case and bracket update.
It must reject omitted children, gaps in coverage, invalid split boundaries,
changed shape/radius/source, impossible shared-neighbor combinations, an
unattained bound presented as a world, and an unsupported bracket step.

## Evidence and costs

Test synthetic geometry, exhaustive small graph/neighborhood controls and
known-bad subdivision/bracket claims before freezing the actual run. Retain
complete assigned results, first failures, work-limited nodes and all source
bindings. Record preparation, search, proof/checking, verification and failed
attempts without adding nested costs twice. Human work and complete economics
remain unknown. Public artifacts contain authored code, synthetic controls
and derived summaries with the existing nuScenes attribution/terms; raw
geometry, per-region operands and proofs stay private.

This follow-up tests the observation contract, not query selection, customer
demand or savings. A counterexample narrows what a review must establish; it
does not measure how often the corresponding error happens. Any post-freeze
change to scientific criteria or implementation requires a retained amendment
and new run identity.
