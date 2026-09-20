# What presence observations can identify

Version 0.1.0. Status: exploratory development construction, not a new
state-of-the-art theorem or empirical measurement of physical objects.

The inherited optional-reference contract fixes known modeled references K.
Each of k named unknown instances is absent/ineligible or contributes one
eligible rectangle. Rectangles have positive width, height at least 25 pixels,
and lie inside the canvas. Distinct instances may share geometry. No minimum
width, aspect-ratio restriction, or exclusion between instances is declared.
Both detectors use the same world, IoU >= 1/2 and maximum one-to-one matching.
For unit false-positive and miss penalties,

`D(T) = |A| - |B| + 2 (m(B,T) - m(A,T))`.

For a finite nonempty prediction set, let a be its smallest positive box area.
Inside a canvas at least 25 pixels high, choose a rectangle of height 25 and
width min(1, canvas width, a/100). Its area is at most a/4. With any prediction
P, IoU <= area(rectangle)/area(P) <= 1/4 < 1/2. It therefore has no matching
edge. With no predictions, any eligible rectangle has no matching edge.

Adding such an isolated reference changes neither matching rank, hence leaves
D unchanged. Complete every absent unknown identity with a distinct isolated
reference. The resulting world has all k unknown instances present/eligible,
preserves K and D, and stays in the inherited contract. Multiplicity remains:
each added reference is a separate right vertex, even with repeated geometry.

Consequently the attainable D values with at most k references equal those
with exactly k present/eligible references, for this contract. The reverse
inclusion is immediate. This statement is about attainable values, not the
tightness of inherited universal bounds or completeness of a finite search.
The tested native certificates additionally require |K|+k <= 128; the selected
retained states have maximum 28. Rational arithmetic avoids rounding an edge.

Apply this construction separately to both retained endpoint worlds for each
allocated case. Every image then has identical complete presence/eligibility
answers and identical counts in the two worlds. If the means still satisfy
Delta_low <= 0 < Delta_high, this transcript cannot identify the decision.
An adaptive policy asking only those presence/count questions receives the
same answers in the two worlds. Randomization cannot supply a zero-error
guarantee for both. We do not claim that every possible presence transcript is
ambiguous: an absent answer can rule out these particular witnesses.

Geometry-dependent matching neighborhoods contain information that presence
does not. The complete bipartite adjacency of each role to the shared named
references suffices to compute this particular unit loss. This is a sufficient
computational observation, not a claim that it is the cheapest or available
physical measurement. Neither object presence alone nor a sensing scheduler
establishes correct time, class, geometry or the census itself.

The deliberately narrow isolated boxes expose the breadth of the declared
model. They are not asserted to be physically plausible cars. A legitimate
minimum width, shape, motion, occlusion or cross-instance constraint would need
external justification and a new frozen observation contract; selecting it
after seeing these witnesses would not validate it.

Construction uses inherited max-flow/native proof production. The separate
checker imports no new construction code: it validates the full census and
unchanged parent prefix, checks geometry and zero adjacency with a separate
IoU path, recomputes matching through augmenting paths, checks native proof
payloads, and recomposes every allocated case. Parent non-target rows are
exact-bound to retained verification, not falsely counted as new replay.
