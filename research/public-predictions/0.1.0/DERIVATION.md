# Bounds, certificate size and attained adverse worlds

Version `0.1.0`. Scope: the frozen development protocol, not an empirical error
model or a general physical-safety guarantee.

For one image let `a=|A|`, `b=|B|`, and let `mA,mB` be maximum matching ranks
against the same reference. Unit matching loss gives
`delta = a-b+2(mB-mA)`. Shared prediction IDs denote identical geometry and
category; duplicate occurrences retain distinct IDs. The symmetric-difference
matching inequality gives `-s <= delta <= s`, where `s=|A symmetric_difference B|`.
Equal outputs have `s=0` for every admissible reference and need no observation.

For one arbitrary reference edit, form bases consisting of the original
reference and each possible one-reference deletion. Inserting one rectangle
can increase either rank by at most one and cannot decrease either rank. For
base ranks `u,v`, every insertion has delta between

`a-b + 2(v-min(a,u+1))` and `a-b + 2(min(b,v+1)-u)`.

These enclosures also contain the no-insertion base. Taking the minimum lower
and maximum upper across bases covers insertion, deletion and replacement;
intersecting with `[-s,s]` retains a sound bound. It allows combinations of
rank changes that may not share a geometric witness, so it is an enclosure
until an admitted world attains its endpoint. Both conventional and native
arms receive this same bound. The conventional implementation caches usable
edges across deletions. The native path retains the actual compilation,
proposal and checking work it performs; that cost is not hidden.

Let an observed image have nominal delta `d`, residual interval `[l,u]`, and
unobserved radius `s`. Independent per-image residual bounds add. Under a
single global edit, sum observed nominal values and unobserved `[-s,s]`, then
subtract the largest observed `d-l` and add the largest observed `u-d`.
Unobserved `[-s,s]` already allows every reference, including an edited one.
The union over possible edit locations is contained in this enclosure; no
addition-only monotonicity argument is used for replacement.

## Retrospective minimum observation count

For supporting improvement, start from lower total `-sum(s)`. Observing an
image gains `s+d` under exact answers, or `s+l` under per-image residuals.
For excluding strict improvement, start from upper total `sum(s)` and gain
`s-d` or `s-u`. These gains are nonnegative. With equal query costs, the sum
of the `k` largest gains is the maximum progress any `k` observations can
make. Support needs progress strictly greater than `sum(s)`; exclusion needs
at least `sum(s)`. This distinction retains threshold equality correctly.

For the global-edit family, net progress for a subset is sum of nominal gains
minus its maximum relevant residual penalty. Enumerate possible penalty caps
from zero and the observed penalties. Within a cap, order allowed gains. Any
optimal subset has a maximum penalty represented by one cap, so the best
sufficient prefix across caps has minimum cardinality. The separate verifier
bounds the progress of any subset with one fewer query, without calling the
floor solver. Exhaustive small-subset controls cover both decision directions
and the strict threshold. Complete-information unresolved cases have no
finite certifying subset under the given bounds; report `null`, not zero.

The calculation is retrospective. It uses answers unavailable to the actual
selectors. It proves a certificate-size floor for these bounds, not that a
selector can know the optimal subset without observing its answers.

## Exact geometric witnesses

The search starts from declared rectangle constructions, source rectangles
and prediction rectangles. For each fixed shape and fixed orthogonal position,
it considers all cells along one translation axis. At IoU at least one half,
intersection area must be at least one third of the sum of the two areas.
With fixed orthogonal overlap `h`, the necessary axial overlap is therefore
`r=(area_reference+area_detection)/(3h)`. If `r` exceeds either axial extent,
there is no matching position. Otherwise a translated left coordinate `x`
must lie in the closed interval

`[detection_left+r-reference_width, detection_right-r]`,

intersected with the image domain. Vertical translation follows the same
argument with coordinates exchanged. Graph adjacency is constant on every
open cell between interval endpoints; the endpoints themselves must also be
evaluated because IoU equality is admitted. Exact rational midpoint and
endpoint representatives avoid numerical epsilon assumptions.

This covers the declared finite union of axis sweeps, not every four-dimensional
rectangle. Equal neighborhoods can be collapsed because the matching graph
has the same new reference vertex and edges. Each candidate is tested against
the original reference and each single deletion. Retained extrema are rebuilt
as full geometric worlds and checked through the native matching checker.

For these actual inputs, both attained extrema equal the universal bound on
every image. Thus no omitted geometry can improve those extrema. Per-image
worlds compose independently; a global-one-edit world chooses one location.
Every unresolved complete-answer case has a supported and an excluded world
inside its declared budget. More queries returning the same kind of answer
cannot distinguish those worlds.

Finally, sort the largest per-image downward changes from nominal. If the sum
of the largest `k` changes is smaller than the positive nominal total, no
allowed `k`-image world can exclude improvement. An attained composition at
the first crossing supplies the matching upper bound. Here 14 images allow
damage at most 36 against total 37, and a 15-image composition reaches -1.
The bound is specifically one arbitrary eligible edit per affected image.
