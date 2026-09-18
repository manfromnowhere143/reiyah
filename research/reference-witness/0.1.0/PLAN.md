# Resolve retained timing bound gaps

Version: `0.1.0`. Status: `exploratory`. Freeze before actual refined searches.
The complete preceding timing results are already known. This is an explicitly
adaptive follow-up to all seven rows labeled `bound_gap`, not a new sample,
held-out confirmation or detector selection experiment.

Keep the preceding 64 images, 73 overlapping cases, four temporal contracts,
known modeled references, unknown-instance censuses, prediction packets, exact
IoU threshold 1/2, height threshold 25, unit penalties and strict improvement
criterion unchanged. Select every image/partial-contract pair belonging to
those seven rows: 14 pairs across 12 images. Four pairs have no optional
unknowns and are retained without unnecessary geometric search. Every other
case/component is inherited by exact byte identity. Recompute and retain all
292 case/contract rows. Do not change universal bounds or blocked membership.

## Finite geometric construction

For each selected image requiring search, take every exact eligible prediction
rectangle, known modeled reference rectangle, and rectangle from the preceding
coarse search pool as a base. Keep each base's shape and orthogonal position
fixed and sweep each coordinate axis over the whole legal image canvas.
Partition the domain at every IoU=1/2 transition, both canvas endpoints and
the original position. Retain each boundary point and the exact rational
midpoint of each open interval. Include the base rectangles themselves.

Deduplicate exact geometry. Compute the common neighborhood of each rectangle
against the union of both detectors' prediction identities. Retain the
lexicographically smallest rectangle for each distinct nonempty neighborhood.
An empty neighborhood cannot affect either matching rank and is equivalent to
omitting that optional reference. Repeated copies of a retained neighborhood
remain allowed for distinct unknown instances. This covers the declared
one-axis sweeps, not every possible four-dimensional rectangle.

Stop construction, retain its failure and inherit previous worlds if there
are more than 100,000 unique rectangles or 4,096 nonempty neighborhoods. No
silent truncation. This cap does not shrink the underlying unknown family.

## Bounded matching search

Search multisets of up to the declared unknown count, with at most 128 total
known plus optional references in an attained native proof. Seed incumbents
with the known-only world and both preceding attained worlds after mapping
their neighborhoods to the new representatives. Check that the mapping
preserves both matching ranks. Enumerate nondecreasing candidate-index tuples
in breadth-first, lexicographic order, allowing repeated indices. Cache by
the full tuple; charge each distinct conventional flow measurement once.

After a tuple with ranks rA,rB, the preceding optional-reference bound with
the remaining unknown count encloses every descendant. Prune only when that
enclosure cannot improve either incumbent. A zero-gain intermediate tuple
must remain eligible for expansion. Stop once both universal endpoints are
attained, the finite search is exhausted, or 50,000 distinct flow measurements
have been performed per image/contract. Include seed measurements in the cap.
Record a reference-limit stop if unsearched longer tuples remain relevant.
Identical current/union unknown membership may reuse a search, charged once.

Keep each previous attained world when it is tied or better. Otherwise retain
the improved world with its exact rectangle coordinates, assigned unknown
identities, conventional ranks and native matching certificate. Both methods
receive identical operands. No query-saving or runtime-superiority claim is
made. A failed or capped search leaves the prior valid evidence intact.

## Verification and interpretation

Before actual data, test narrow threshold regions, repeated geometry,
non-improving intermediate states, exhaustive tiny multiset comparisons,
zero budgets, construction limits, reference limits and malformed membership.
A separate checker reconstructs axis partitions using piecewise overlaps,
checks neighborhoods with an independent exact IoU expression, verifies
selected worlds with augmenting paths and checks native proof payloads.
Replay search accounting deterministically; do not treat a shared search
implementation as independent verification of its completeness. Completeness
of the unrestricted family is asserted only when both universal endpoints
have independently checked attained worlds.

Retain all seven target outcomes, all 292 updated rows, unchanged universal
decisions, all failed attempts and measured command costs. Distinguish a
remaining bound gap from demonstrated opposing worlds. The primary timing
result already has opposing worlds and cannot become a supported replacement
claim through this search. No new images, metadata, model calls, training,
network downloads or reserved outcomes. All 1,433 reserved images stay closed.
Human work and complete economic savings remain unmeasured.
