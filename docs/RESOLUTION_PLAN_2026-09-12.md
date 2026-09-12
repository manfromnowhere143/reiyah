# How many observations decide, and when none of them will

Document ID: `reiyah.resolution-plan.2026-09-12`

Version: `0.2.0`

Supersedes: `0.1.0` of the same document ID. The corrections are stated in full below and the
superseded claims are quoted rather than removed.

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
| conditional inertness | resolvable | **1 observation**; an initially inert question is retained, not discarded |
| adaptive beats fixed | resolvable | **2 observations**, where the smallest fixed set of questions is **3** |
| geometry ambiguity | **unresolvable by declared questions** | no presence question separates `d_reachable` from `d_unreachable` |
| the live two-anchor comparison | **no admitted reference** | there is no joint world to ask about |

## Correction: an empty population is not an ambiguous one

Version 0.1.0 of this program, run on the live two-anchor comparison, returned

> `unresolvable_by_declared_questions`
>
> "no sequence of declared presence questions makes every cell decided. Some admitted worlds differ
> in a way that asking which objects exist cannot separate, so more looking for objects will not
> settle this"
>
> `indistinguishable_world_groups: []`

There were no admitted worlds. The sentence describes worlds that differ, a separation that cannot
be made, and an ambiguity that was observed, on a population that was empty, and the list of
witnesses it offered was empty too. The absence of a reference basis had been dressed as a property
of a model that had never been stated. It is the more flattering of the two readings: a discovered
limit of observation sounds like a finding, while a missing prerequisite is only a gap.

Four negatives are now distinct, and each names the cell it is talking about:

| state | meaning | witness required |
|---|---|---|
| `no_admitted_reference` | no joint world is admitted. The enclosure is the conditional count bound and no question exists | none, and none is invented |
| `unresolvable_by_declared_questions` | the worlds in the witness cell agree on which objects exist and differ only in which detections could match them | a cell of **two or more** worlds, undecided, that no permitted question divides |
| `blocked_by_unanswerable_questions` | a declared question would divide the witness cell, but the case marks it unanswerable | the withheld question, which must be marked unanswerable in the case and must divide the cell |
| `undecided_single_world` | one fully finite world whose value does not clear the tolerance | the single world |

The witness is recorded during the search, at the moment a cell is found that no question divides.
It is not reconstructed afterwards from what the answer ought to have been.

## Correction: a fixed resolving set cannot certify an adaptive plan

Version 0.1.0 verified depths against a brute force over subsets, and said:

> "A fixed resolving set is one valid strategy, so the adaptive optimum can never exceed it, and that
> inequality is asserted on two cases."

The inequality is true and it is weak. It bounds the adaptive optimum from **above** only, so it
cannot detect an **understated** depth, which is the error that flatters. On every case then
retained, the two numbers happened to be equal, which is why the weakness did not show.

`adaptive-beats-fixed-case.json` is the retained witness that they are not equal. Four admitted
worlds over three anchors, weights `2/5`, `3/10`, `3/10`, tolerance `1/10`:

```
ask B.B_d
  present  ask C.C_d   present -> supported   absent -> excluded
  absent   ask A.A_d   present -> supported   absent -> excluded
```

Two observations, and the second question **differs depending on the first answer**. No fixed set of
two questions resolves the comparison, so the smallest fixed set is three. Adaptivity is worth one
observation here, and the fixed number would have certified `3` as correct while the truth was `2`.

The case was not invented to fit. An exhaustive search over all labelled structures on three
questions returned the smallest gap example, and it was rejected: it required a world value that
falls when a reference object is added, which the additive loss does not permit. The search was then
restricted to monotone labellings, which returned the structure above, and it was realised with three
copies of the matching-trap gadget.

## The negative result is the one that matters

Two admitted worlds can agree on **which objects exist** and differ only on **which detections could
match them**. No question of the form "is this object present" separates them. The comparison is then
unresolvable by object discovery, however long a reviewer looks. **Not all reference uncertainty is
existence uncertainty**, and the kind that is not cannot be settled by finding objects.

That conclusion now requires a named cell, and the cell must be checked: undecided, and divided by no
permitted question. Without one, the claim is refused.

## The checker is not a second copy of the planner

The planner searches top down and minimises. A checker written the same way would be wrong in the
same way and would agree. So `check_resolution_plan.py` asks a **decision** question instead: for a
budget `d`, does any tree of depth at most `d` resolve the cell? A reported depth is accepted only
when the ladder says yes at `d` and no at `d - 1`.

The difference is load-bearing. A plan that asks `A` first on the witness case is a perfectly correct
tree: every node divides the cell it is given, every leaf carries the right verdict, every declared
depth equals one plus its larger branch. It is simply wasteful, at depth `3`. Node-by-node checking
accepts it. Only the oracle refuses it, and the refusal names the reason: the comparison resolves
within `2`.

Seventeen adversaries are retained, each a plan a careless reader would accept: an understated depth,
a wasteful tree, a truncated branch, a flipped leaf verdict, an invented question, swapped branches,
a question asked in a cell that is already decided, a `first_question` that is not the root, an
ambiguity claim on an empty population, an ambiguity claim with a single-world witness, an
unresolvable claim where a plan exists, and a missing-reference claim where worlds exist. Each is
refused with the defect named.

The checker imports no planner code. It shares `cohort_packet.build` for the enclosure and criterion,
and the Python standard library. Fields it does not verify are listed in `fields_not_verified` rather
than passed over in silence.

## An inert question is not a useless one

The Engine lane supplied a case where a question is inert over all admitted worlds and decisive once
another has been answered absent. It is retained here as a regression. The planner filters questions
on whether they **split** the worlds, never on whether they move the enclosure on their own, so a
conditionally decisive question survives to be asked. Discarding initially inert questions before
planning would have lost it.

## What the sixteen-object case now produces on its own

The construction that refuted this lane's earlier judgement count has all sixteen candidate objects
confirmed in every admitted world. The planner reports `[-8, 8]` unresolved, then offers **one**
observation, and the question it names is a **disputed base neighbour**, never one of the sixteen.
The candidate questions do not even appear as available, because they do not split the worlds.

## Worst case, not expected, and only under a declared answer model

The depth reported is a guarantee over the declared alternatives. It is not an expectation, because
no probability over reference interpretations has been established in this program, and it is not a
human time estimate. An earlier artifact in this lane predicted review effort from an assumed
Bernoulli race and was withdrawn; this does not reinstate it under a new name.

It is also a guarantee only if every permitted question can actually be answered, truthfully, as a
binary, at equal cost. **That is an assumption about an observation procedure, not an observation.**
Every result now carries the assumption as a field rather than leaving it implied. Real answers
include *unable to judge*, *ambiguous*, *no evidence at that location* and *not exposed*, and none of
them is the same as *absent*.

The mechanism available today is narrow and deliberately so: a case may mark a declared object
`"answerable": false` with an obstacle string. The planner then excludes that question instead of
counting it as free, and if the withheld question would have divided the witness cell, the result is
`blocked_by_unanswerable_questions`, not an ambiguity claim. The obstacle is then attributed to the
observation procedure, which is where it belongs.

`research/cohort-packet/0.1.0/answer-prerequisites.json` records what is supported and what is not.
Presence questions have a defined measurement: membership in `objects_present` inside an admitted
joint interpretation. Reachability, calibration and timing questions do not. Calling a question
"geometry" names it; it does not define it, and each would need a stated matching rule, frame, units,
threshold, sensor pose and out-of-range convention before any answer to it could change a number this
program computes. Those prerequisites are recorded as missing rather than assumed to be covered.

## The live comparison's actual prerequisite

The two-anchor comparison that this lane exists to serve is at `open_reference_only`, enclosure
`[-8, 8]`. It has no admitted joint world. Every result above is therefore conditional on a
prerequisite this lane cannot supply and does not create: an admitted joint reference interpretation
for each finite anchor. The planner now says so in those words, and names the prerequisite, instead
of reporting an ambiguity it cannot have observed.

## A side result, with its exact scope

The correction above rested on world values being monotone in object presence. That was tested, not
assumed. Across every bipartite gadget with up to three base detections, two added detections and
three reference objects, and a further 400,000 randomly generated gadgets with up to four base
detections, three added detections and five objects, **no case was found where adding a reference
object decreases the additive delta**. This is a negative search result over a stated family. It is
not a theorem, and it is not offered as one; a proof or a counterexample outside that family would
both be useful.

## Verification

Thirty-four tests across two files, `0.02` seconds for the planner on the witness case and `0.19`
seconds for both suites. Reports are byte-identical across runs; the witness case report hashes to
`d664a6bd0ca07064722beb8c4f4b86865ccefb1b876ff9ccb16fd02c5c4f217e`. All 271 tests in `tools/measure`
pass.

## Limits

The questions come from the **declared** alternatives and are presence questions only. An
`unresolvable` verdict means these questions cannot settle the comparison, not that no observation
could. Discovering new alternatives is a separate obligation this does not discharge. The answer
model is an assumption in every case where it is not explicitly narrowed, and the narrowing mechanism
is coarse: a question is answerable or it is not, with no partial, costly or uncertain answer between
them. No reference interpretation is invented, admitted or implied, and no reviewer, exposure record,
competence claim or judgement is created. The cases are synthetic and labelled synthetic. Nothing
here establishes physical coverage, planner behaviour or risk, and product differentiation against a
competent analyst remains untested.

## Reproduce

```sh
python3 -B tools/measure/resolution_plan.py research/cohort-packet/0.1.0/adaptive-beats-fixed-case.json
python3 -B tools/measure/resolution_plan.py research/cohort-packet/0.1.0/open-two-anchor.json
python3 -B tools/measure/resolution_plan.py research/cohort-packet/0.1.0/geometry-ambiguity-plan-case.json > /tmp/plan.json
python3 -B tools/measure/check_resolution_plan.py research/cohort-packet/0.1.0/geometry-ambiguity-plan-case.json /tmp/plan.json
python3 -B -m unittest discover -s tools/measure -p 'test_resolution_plan.py'
python3 -B -m unittest discover -s tools/measure -p 'test_check_resolution_plan.py'
```

No data is read. Exact rational arithmetic, standard library only.

## Non-claims

An internal research artifact, retained as `proposed`. Not independent external scientific review,
not an operator acceptance, not a safety, compliance or vendor claim, and not a reviewer protocol.
No released `1.2` byte, frozen protocol, claim-register entry, Engine file or other owner's work is
modified.
