# Full-answer opportunity and adverse-world analysis

Analysis ID: `reiyah.public-predictions.full-answer-analysis`.
Version: `0.1.0`. Status: `exploratory`.

This analysis follows the frozen comparison. Its observed results already
include conventional/checked query parity, a worse candidate selector in four
dependent cases, and unresolved per-image residual uncertainty on the primary
cohort. Retain those outcomes. This analysis does not change a selector, query
history, prediction packet, protocol tolerance or result row.

Use the same 64 assigned development images, 73 overlapping cases, eligible
rectangles, matching loss and three reference contracts. Materialize all 64
already prepared answers for retrospective analysis and record that access
and its cost separately. No outcome-reserved input or new inference is used.

## Minimum sufficient query subsets

For each fully observed case, calculate its result using the same sound
stopping bounds. If that result is unresolved, there is no sufficient subset
under those bounds. Do not assign it a finite query floor or a cost per
resolved decision.

For a resolved case, find the smallest subset of its supplied answers that
would already give that same decision. With additive exact or per-image
bounds, each answer contributes a known nonnegative improvement from the
unobserved bound. Sorting those improvements gives the exact minimum subset
size for equal unit query costs. Preserve strictness: a lower bound must be
greater than zero for support; an upper bound at zero excludes improvement.

For the global-one-edit contract, the observed nominal contributions are
additive, with one maximum residual penalty. Enumerate the finite possible
maximum penalties. At each penalty, restrict to answers whose penalties do
not exceed it and sort their nominal improvements. The best resulting subset
is the exact minimum under these bounds. Check against exhaustive subsets on
small synthetic cases before using it on the development cohort.

This calculation deliberately knows all answers. It is a retrospective
certificate-size floor, not an available selector or an observation-saving
method. Compare it with actual arm queries to bound the remaining possible
improvement under the declared mathematics. It does not bound all imaginable
future contracts or different evidence sources.

## Admissible geometric edits

For each image, retain its nominal reference and all single-reference
deletions. Search insertions and replacements with exact rational geometry.
Every new rectangle must have positive area, remain inside that image and
have height at least 25. A car-class entry/exit is an insertion/deletion.

Start with visible prediction and observed reference rectangles, plus the
predecessor's fixed shift, half-size and doubled-size constructions clipped
to the current image. Also sweep each retained base shape horizontally and
vertically through exact matching boundaries. For a horizontal translation
of a fixed rectangle with width w, height h and fixed vertical overlap v
with detection D, IoU at least 1/2 requires intersection area at least
`(area(D) + w*h) / 3`. If v is positive, this gives an exact closed interval
of admissible left coordinates. Evaluate every interval endpoint and a
rational midpoint between adjacent endpoints inside the image domain.
The vertical construction is symmetric.

Collapse candidate rectangles only when they have the same matching
neighborhood over both outputs; retain a concrete representative. For each
deletion base, measure insertion of each candidate neighborhood. This supplies
explicit nominal, deletion, insertion or replacement worlds with conventional
matching and independently checked native matching for retained extrema.

The finite search is exhaustive over its declared axis-sweep cells, not over
all four-dimensional rectangle geometry. A candidate does not become an
admissible reference because it is convenient: check the full canvas, height,
edit count and category semantics. Cap candidate construction at 100,000
rectangles and neighborhood evaluation at 2,000,000 base/candidate pairs per
image. Retain a bounded-search failure or gap explicitly; never silently
truncate and call the result exhaustive.

Compose per-image worlds to challenge all unresolved case/family pairs. For
the global-one-edit family, change at most one image. For the per-image family,
change at most one rectangle in each affected image; those edits may be
correlated. A retained opposite-decision world establishes that no selector
using only the allowed observations can guarantee a unique decision across
those worlds. If the search finds no opposite world, report the remaining
bound/geometry gap instead of claiming robustness.

On the primary cohort, also compute the minimum number of edited images
needed to exclude the nominal strict improvement, within the one-edit-per-
image set. Sort sound per-image maximum loss changes to obtain a universal
lower bound on that number. Sort achieved adverse changes to produce an
upper bound with a concrete combined world. Equality gives a conditional
exact edit threshold; a gap remains a gap. This is sensitivity to a declared
adversary, not an annotation-error frequency, independence assumption or
probability of model failure.

## Retention

Freeze the analysis code and its input bindings before the actual search.
Retain every assigned image and case, candidate/neighborhood counts, search
limits, costs, extreme worlds, matching checks and unresolved gaps. Validate
the geometric boundary construction on synthetic exact threshold cases.
Recompute every composed adverse decision. Keep data-derived rectangles and
answers private under their source terms. Publish scoped aggregates and
limitations, preserving all earlier parity and failure findings.
