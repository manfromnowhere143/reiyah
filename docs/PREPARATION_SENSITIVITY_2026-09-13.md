# What the original rows decide about an integration choice

Document ID: `reiyah.preparation-sensitivity.2026-09-13`

Version: `0.1.0`

Lifecycle status: `proposed`

Lane: independent research and conventional comparator. Consumes the Engine's
`original-predictions-0.1.0` packet and changes no Engine file, no common operand, no admission,
viewer, shared handoff or main. Gate A remains unaccepted.

## The question and the answer

**Does the added detector deserve further integration work?** The Engine's additive loss answers it:

```
delta = (a + b) * (TP_augmented - TP_base) - b * r
```

and `r`, the retained additions, is the one term computable with no reference at all. Whatever the
references turn out to be, `delta` lies in `[-b*r, a*r]`, so `r` alone fixes how wide the answer can
be.

The answer from these rows is **abstain**, for two reasons rather than one.

Without admitted references, `TP_base` and `TP_augmented` are unknown and the sign of `delta` is
open. That was expected. What was not is that **`r` is not determined by the rows either.**

## The measurement

Over the exact 4,876 submitted rows in the packet, across 16 already exposed frames, each row
carrying its own source index, byte offset, size and digest, and with the producer performing no
association and admitting no reference:

| score cutoff | radius | retained additions | coarse bound on `delta` |
|---|---|---|---|
| none | 0.5 m | **2,661** | `[-2661, 2661]` |
| none | 4 m | 2,043 | `[-2043, 2043]` |
| 0.3 | 0.5 m | 373 | `[-373, 373]` |
| 0.3 | 4 m | 139 | `[-139, 139]` |
| 0.5 | 4 m | **89** | `[-89, 89]` |

`r` spans `89` to `2,661`, a ratio of **29.9**. Every preparation in that grid is defensible, and
they do not support the same bound.

## Which preparation choice carries it

Separating the two knobs on the same rows:

| knob | effect on `r` |
|---|---|
| score cutoff | **21.6x** |
| association radius | 2.9x |

**The score cutoff dominates the association radius by roughly seven to one.**

This reverses the previous checkpoint, which found the association radius dominant for the
dependence threshold by 14 times against 6 percent. The two decisions are sensitive to different
preparation choices, and **neither can be assumed from the other**. A sensitivity established for one
quantity says nothing about the next one.

## What this is not

The Engine's real comparison is `[-8, 8]` over two windows. These are 16 frames. **The two are not
the same scope and the numbers are not comparable.** The distance between them is preparation this
lane does not own and must not duplicate, and nothing here says that preparation is wrong.

What it does say is narrower and still worth a validation lead's attention: the quantity that fixes
how wide an integration answer can be is **mostly a function of preparation rather than of the
detector outputs**, so the preparation has to be justified rather than inherited.

## The conventional analyst gets the same number

Unmatched additions are an overlap quantity. A competent analyst with ordinary overlap computes the
same `r`. **The parity holds for a third time.** What overlap does not report is the sensitivity
decomposition above, and that is the entire added value of this checkpoint.

## What would settle it

A declared per row coordinate and timing uncertainty for these rows would justify an association
radius rather than leaving it chosen. Admitted references would close the sign. Neither exists in
this lane's custody, and neither is invented here.

## Reproduce

```sh
python3 -B tools/measure/preparation_sensitivity.py
python3 -B -m unittest discover -s tools/measure -p 'test_preparation_sensitivity.py'
```

Eighteen tests, exact integer counts, standard library only. The retained counts carry the packet's
request digest, its own digest, and the per row digest count of 4,876. No payload is redistributed
and no source identifier is retained.

## Non-claims

An internal research artifact, retained as `proposed`. Not independent external scientific review,
not an operator acceptance, not a safety, compliance or vendor claim. These are exposed development
frames, so any later comparison against annotations is a reproducible retrospective falsification
and not a blind validation.
