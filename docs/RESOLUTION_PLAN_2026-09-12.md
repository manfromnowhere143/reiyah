# How many observations decide, and when none of them will

Document ID: `reiyah.resolution-plan.2026-09-12`

Version: `0.1.0`

Lifecycle status: `proposed`

Lane: independent research and conventional comparator, parallel to the Engine. Changes no Engine
file, no shared handoff, no frozen protocol and no owner checkout. Creates no reference admission,
no reviewer and no human judgement. Gate A remains unaccepted.

## The question and the result

Classifying single questions says which observations **can** move the enclosure. It does not say how
many are needed, in what order, or whether the declared alternatives can settle the comparison at
all. All three are computable exactly, before anyone looks.

A set of questions partitions the admitted worlds by answer. The set **resolves** the comparison when
every cell yields a definite improvement criterion. The plan is an adaptive decision tree over the
declared questions and its cost is the **worst-case** number of answers required.

| case | state | result |
|---|---|---|
| matching trap | resolvable | **1 observation**, and it names which: `A.d` |
| sixteen-object construction | resolvable | **1 observation**, and it picks a disputed base neighbour, not one of the sixteen candidates |
| three independent copies | resolvable | **3 observations** worst case, of 3 available |
| geometry ambiguity | **unresolvable by declared questions** | no presence question separates `d_reachable` from `d_unreachable` |

## The negative result is the one that matters

Two admitted worlds can agree on **which objects exist** and differ only on **which detections could
match them**. No question of the form "is this object present" separates them. The comparison is then
unresolvable by object discovery, however long a reviewer looks.

The program returns `unresolvable_by_declared_questions` and names the worlds it cannot separate,
rather than producing a plan that would not work. **Not all reference uncertainty is existence
uncertainty**, and the kind that is not cannot be settled by finding objects. A review programme that
meets this needs a different kind of observation, on geometry, calibration or timing, and no amount
of the same kind will do.

## What the sixteen-object case now produces on its own

The construction that refuted this lane's earlier judgement count has all sixteen candidate objects
confirmed in every admitted world. The planner reports `[-8, 8]` unresolved, then offers **one**
observation, and the question it names is a **disputed base neighbour**, never one of the sixteen.
The candidate questions do not even appear as available, because they do not split the worlds.

The lesson that had to be learned by refutation is now produced automatically by the instrument. That
is the check worth having: the tool gives the advice that the correction taught, without being told.

## Worst case, not expected

The depth reported is a guarantee over the declared alternatives. It is not an expectation, because
no probability over reference interpretations has been established in this program, and it is not a
human time estimate. An earlier artifact in this lane predicted review effort from an assumed
Bernoulli race and was withdrawn; this does not reinstate it under a new name. There is no prior
here, no expected count and no predicted cost.

## Verification

Eight tests. An independent brute force enumerates every subset of questions directly, rather than by
the planner's recursion, and finds the smallest **fixed** resolving set. A fixed resolving set is one
valid strategy, so the adaptive optimum can never exceed it, and that inequality is asserted on two
cases. The unresolvable case is confirmed twice: the planner returns no plan, and the brute force
finds no resolving subset of any size. Depth-one claims are checked by confirming both branches are
decided. The resource bound is checked to refuse before searching.

## Limits

The questions come from the **declared** alternatives and are presence questions only. An
`unresolvable` verdict means these questions cannot settle the comparison, not that no observation
could. Discovering new alternatives is a separate obligation this does not discharge. No reference
interpretation is invented, admitted or implied, and no reviewer or judgement is created. The cases
are synthetic and labelled synthetic. Nothing here establishes physical coverage, planner behaviour
or risk, and product differentiation against a competent analyst remains untested.

## Reproduce

```sh
python3 -B tools/measure/resolution_plan.py research/cohort-packet/0.1.0/matching-trap-plan-case.json
python3 -B tools/measure/resolution_plan.py research/cohort-packet/0.1.0/geometry-ambiguity-plan-case.json
python3 -B -m unittest discover -s tools/measure -p test_resolution_plan.py
```

No data is read. Exact rational arithmetic, standard library only, about 0.012 seconds for the
planner and its eight tests. Reports are byte-identical across runs.

## Non-claims

An internal research artifact, retained as `proposed`. Not independent external scientific review,
not an operator acceptance, not a safety, compliance or vendor claim, and not a reviewer protocol.
No released `1.2` byte, frozen protocol, claim-register entry, Engine file or other owner's work is
modified.
