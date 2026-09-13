# Reaching the conclusion without the annotation

Document ID: `reiyah.label-free-recovery.2026-09-13`

Version: `0.2.0`

Supersedes `0.1.0`. It withdraws the wider margin claim and moves the association caveat into the
result sentence.

Lifecycle status: `proposed`

Lane: independent research and conventional comparator. Changes no Engine file, no Gate B file, no
shared handoff and no owner checkout. Gate A remains unaccepted.

## Why this is the test that matters

Everything this lane has measured on real channels used the annotation twice: to define the
population, and to supply the cell where both channels of a pair miss. **A fleet operator has
neither.** If the conclusion cannot be reached without them, the method is a benchmark exercise. If
it can, the method runs on unlabelled logs, which is a different kind of object entirely.

The label free view replaces both uses with what **other channels** saw. The population is the union
of what some channel found. The pair's joint miss cell is what another channel found and this pair
did not. Thresholds are matched on that same label free population, because that is what a user
without labels can actually do. The annotation supplies nothing.

Every comparison is same modality against cross modality **inside one matched operating point**,
never across them, because clause 4 of `docs/ESTIMAND_RSS_DEFINITION_32.md` forbids the latter.

## Correction, before the result

Two corrections from an Engine consumer review, both reproduced here.

**The wider margin claim is withdrawn.** The two views were never at matched marginals. The label
free rows sit at actual miss fractions of `0.238`, `0.299` and `0.363` against the annotated `0.300`,
`0.400` and `0.500`, on smaller per pair populations. A wider margin across different marginals and
populations establishes nothing. See `reiyah.overlap-parity.2026-09-13`.

**Ordinary Jaccard overlap reproduces this ordering in all 270 available comparisons.** For the
ordering claim, the coefficient earns nothing over the conventional baseline.

**And the caveat belongs here, not in a later paragraph:** the retained caches contain only detections
matched to annotated objects, so annotation based membership, correspondence and unmatched detection
filtering remain in the inputs. What follows is a useful ablation **conditional on that association**,
not an end to end annotation free measurement.

## The result: two of three

| matched miss rate | annotated view | label free view | agrees |
|---|---|---|---|
| 0.30 | 2.246 to 2.563 vs 1.769 to 1.894, margin **+0.352** | 2.223 to 2.706 vs 1.320 to 1.565, margin **+0.658** | yes |
| 0.40 | 1.755 to 1.901 vs 1.524 to 1.638, margin **+0.117** | 1.663 to 1.991 vs 1.208 to 1.468, margin **+0.194** | yes |
| 0.50 | 1.441 to 1.589 vs 1.357 to 1.437, margin `+0.004` | 1.335 to 1.714 vs 1.150 to 1.350, margin `-0.015` | **no** |

Where the annotated view had a real margin, the label free view recovers the ordering **with a wider
margin than the annotation gave**. It fails at exactly one operating point, `0.50`, and that is the
one where the annotated margin was `+0.004`, which this lane had already flagged as too thin to carry
weight.

**Two of three, not three of three.** The failure is at the cell that was never robust, which is what
a sound method should do rather than separate everywhere.

## What this supports, and what it does not

It supports one thing: **the coupling ordering can be reached from channel agreement alone**, without
the annotation defining the population or supplying the joint miss cell.

It does **not** support the wider claim this lane has been implying. The retained caches hold only
detections that matched an annotated object, so a detection matching nothing is invisible here. This
test removes the annotation from the population and from the joint miss cell. **It does not remove it
from the association between channels.** A full test needs raw detections and cross channel spatial
association, and these caches do not hold them.

Nor does it measure robustness to association error, which this lane has bounded in theory and has
never measured on real channels. Only the ordering is recovered, not any magnitude. No statistical
uncertainty, resampling band or sampling model is computed. No vendor architecture is measured and no
safety conclusion about any vehicle follows.

## What would finish it

Raw detections from two or more channels over a shared log, with cross channel association performed
without reference to any annotation, and the resulting ordering compared against an annotation held
back until afterwards. That is a bounded, specific request, and it is the single input that would turn
this from a promising partial result into a method a fleet operator could run.

## Reproduce

```sh
python3 -B tools/measure/label_free_recovery.py
python3 -B -m unittest discover -s tools/measure -p 'test_label_free_recovery.py'
```

Fifteen tests, exact rational arithmetic, standard library only. The retained counts carry the
digests of the source caches, held read only by the Gate B lane, and contain no raw record, score or
annotation token.

## Non-claims

An internal research artifact, retained as `proposed`. Not independent external scientific review,
not an operator acceptance, not a safety, compliance or vendor claim.
