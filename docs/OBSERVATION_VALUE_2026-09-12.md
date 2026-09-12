# Which observations can change the decision

Document ID: `reiyah.observation-value.2026-09-12`

Version: `0.1.0`

Lifecycle status: `proposed`

Lane: independent research and conventional comparator, parallel to the Engine. Changes no Engine
file, no shared handoff, no frozen protocol and no owner checkout. Creates no reference admission,
no reviewer and no human judgement. Gate A remains unaccepted.

## The question and the result

A comparison with several admitted interpretations is unresolved because nobody yet knows which one
holds. **Not every unknown matters, and which ones matter is computable before anyone looks.**

For each declared question of the form "is this object present at this anchor", the admitted worlds
split into two cells. Comparing the cell enclosures with the enclosure over all worlds classifies
the question exactly:

| classification | meaning |
|---|---|
| `decisive` | some cell decides an improvement criterion the full set leaves unresolved |
| `narrowing` | no cell decides, but some cell is strictly narrower |
| `inert` | every cell has the identical enclosure; the observation cannot change anything |
| `already_settled` | the object has the same presence in every admitted world |

On the retained cases:

| case | enclosure | width | questions |
|---|---|---:|---|
| matching trap | `[-1, 1]` | 2 | 1 already settled, **1 decisive** |
| separated geometry | `[1, 1]` | 0 | 2 already settled, **2 inert** |

In the matching trap the disputed object is decisive: resolving it collapses `[-1, 1]` to a point
and the criterion becomes `excluded` if absent and `supported` if present. In the separated geometry
both remaining questions are inert, and a reviewer who answered them would have learned nothing
about the decision.

## The finding worth keeping

**The same disputed object is decisive in one geometry and inert in another.** In the trap, the base
and the addition compete for one known object, so admitting the disputed object reallocates the
matching and frees the addition. In the separated geometry the addition already has its own object,
so the disputed one changes both configurations equally and the difference is untouched.

Relevance is therefore a property of the **local matching structure**, not of the object, its class,
its distance or how uncertain it looks. No heuristic over object attributes can reproduce this
classification, because the quantity it depends on is the matching itself.

## Why this is exact rather than expected

The classification uses no probability over reference interpretations, because none has been
established in this program. It is not an expected-value ordering, and it does not rank questions by
how likely a world is. It answers only whether an observation **can** move the declared enclosure.

That restraint is deliberate. An earlier artifact in this lane predicted review outcomes from an
assumed Bernoulli race over additions, and that forecast was withdrawn. This does not reinstate it
in another form: there is no prior here, no expected count and no predicted cost.

## Falsifiable check, and it held

An `inert` classification makes a strong promise: resolving that question cannot move the enclosure.
It was attacked exhaustively. For the separated geometry, every admitted subset of worlds that
splits on the inert question was enumerated, the enclosure recomputed on the whole subset and on
each cell, and compared. **Eighteen comparisons, zero changes.** The test is retained, and a future
edit that makes an inert question movable will fail it.

## What this is for

The Engine lane is building the ability for a reviewer to open, display and trace an observation.
This computes where looking is worth the time. The two compose: one supplies the act of observation,
the other supplies its ordering. Neither substitutes for the other, and neither creates a judgement.

It also bears directly on the public commitment to test whether this work improves an integration
decision against a competent analyst **with all effort counted**. Effort is counted in observations,
and an analyst who reviews inert questions spends effort for nothing. Whether that advantage is real
in practice is untested and is not claimed here.

## Limits

The questions come from the **declared** alternatives. A question absent from the admitted worlds is
not classified, and discovering new alternatives is a separate obligation this does not discharge.
No reference interpretation is invented, admitted or implied. The cases are synthetic and labelled
synthetic. Nothing here establishes physical coverage, planner behaviour or risk, and nothing here
demonstrates product differentiation, which remains untested against a real analyst.

## A defect repaired in the same checkpoint

The cohort checker emitted a `preference` and never verified it, so `prefer_augmented` could be
forged and confirmed. That is the claim a reader cares about most. The checker now derives both the
improvement criterion and the preference from the enclosure and the declared tolerance, and requires
an unresolved cohort to pair `not_evaluated` with `not_evaluated`. Four tests pin it.

## Reproduce

```sh
python3 -B tools/measure/observation_value.py research/cohort-packet/0.1.0/matching-trap-observation-case.json
python3 -B -m unittest discover -s tools/measure -p test_observation_value.py
```

No data is read. Exact rational arithmetic, standard library only, about 0.005 seconds for the
classifier and its nine tests.

## Non-claims

An internal research artifact, retained as `proposed`. Not independent external scientific review,
not an operator acceptance, not a safety, compliance or vendor claim, and not a reviewer protocol.
No released `1.2` byte, frozen protocol, claim-register entry, Engine file or other owner's work is
modified.
