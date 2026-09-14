# The strongest ordinary comparator, end to end

Date: 2026-09-14. Lane: independent research. Lifecycle status: `proposed`.

Artifacts:
[`research/comparator/0.1.0/end-to-end.json`](../research/comparator/0.1.0/end-to-end.json),
[`research/comparator/0.1.0/verification-cost.json`](../research/comparator/0.1.0/verification-cost.json)

Producers: [`tools/measure/ordinary_comparator.py`](../tools/measure/ordinary_comparator.py),
[`tools/measure/observation_cover.py`](../tools/measure/observation_cover.py)

Checkers: [`tools/measure/check_cohort_packet.py`](../tools/measure/check_cohort_packet.py),
[`tools/measure/check_observation_cover.py`](../tools/measure/check_observation_cover.py)

Tests: 32 across
[`test_observation_cover.py`](../tools/measure/test_observation_cover.py) and
[`test_ordinary_comparator.py`](../tools/measure/test_ordinary_comparator.py),
inside a suite of 676.

## The decision, unchanged

```text
delta = (a + b) * (TP_augmented - TP_base) - b * r
```

over a weighted cohort, with maximum same class one to one matching, matching competition
preserved, complete joint reference alternatives, nonnegative penalties, retained base
detections and a declared tolerance. No coefficient, excess or overlap share is substituted
for it anywhere in this checkpoint.

## The comparator

A competent analyst holding the same anchors, the same detections, the same loss, the same
tolerance and the same admitted readings, using an ordinary matcher, free to abstain and free
to ask adaptive questions. Nothing is withheld from them. Two ordinary readings of the reference
are implemented for them, `complete_annotation` and `single_interpretation`, and both are run.

## The result, in one paragraph

The verdict is a draw, and this lane proved it a draw itself. On a finite cohort the enclosure
returns `unresolved` exactly when the analyst's single reading verdicts disagree, and otherwise
returns their common verdict. That equivalence holds on every case in the artifact. The
measurable difference is not the verdict but the list of things the validation lead is then sent
to go and settle. Across the eight selected cases the analyst's own diff of their readings hands
them **56** disputed reading facts. The certified list is **7**, and both ends of that list are
checkable in linear time without rerunning any search. Against that, verification by certificate
is **slower** than simply recomputing on every retained case, and this lane costs four modules
to integrate where the analyst costs none.

## The observation list

When readings disagree the analyst learns which facts they disagree about, by diffing. That set
is large and most of it is irrelevant to the verdict. The shorter question is which facts have
to be settled.

Call an **atom** one reading fact at one anchor: an object is present, or a named detection could
have matched a named object. For two readings with opposite verdicts, the atoms where they differ
form a **separating set**, and at least one atom inside it has to be settled whatever else is.
A set of atoms meeting every separating set fixes the verdict across every admitted reading.

So the shortest observation list is a minimum hitting set over the separating sets of discordant
reading pairs. It carries the same kind of two sided certificate the matching already carries in
this lane:

- **upper** a cover, checked in linear time by hitting every separating set;
- **lower** a family of pairwise disjoint separating sets, since every cover must spend an atom
  inside each one, so a packing of size `k` forces every cover to have size at least `k`.

When the two meet, the list is proved shortest and **no search runs at all**. That matters,
because the exact search is exponential and this is the part that survives a disputed set far
past any budget it could afford. `sixteen-candidates-plan-case` has 32 disputed atoms and its
certified shortest list is a single atom, reached with no search.

When they do not meet, the report brackets rather than claims. `bracketed-observation-case` has
39 disputed atoms, a packing that forces at least 1 and an exhibited cover of 2. It is retained
precisely so that this state stays exercised.

| case | criterion | analyst diff | certified list | lower bound |
|---|---|---|---|---|
| `open-two-anchor` | unresolved | not applicable | not applicable | waits on a reference |
| `matching-trap` | unresolved | 2 | 1 | 1 |
| `oppositely-coupled` | excluded | 4 | 0 | 0 |
| `worst-group-flip-case` | excluded | 4 | 0 | 0 |
| `three-copies-plan-case` | unresolved | 6 | 3 | 3 |
| `adaptive-beats-fixed-varying-edges-case` | unresolved | 8 | 2 | 2 |
| `sixteen-candidates-plan-case` | unresolved | 32 | 1 | 1 |
| `ghost-burden-three` | excluded | 0 | 0 | 0 |

The two rows with a diff of 4 and a list of 0 are the more useful direction. The verdict is
already decided and the four disputed facts never need settling at all. Telling a lead to stop
looking is worth as much as telling them where to look.

On 1400 synthetic cohorts built by a generator written in this lane, every instance accepted by
both checkers: 683 already decided, 386 certified shortest, 331 bracketed. Mean analyst diff
52.605 atoms, mean list 0.79. Those shares describe the generator and nothing else. No claim is
made about how often a real cohort is already decided.

## Where this lane is behind

**Verification.** Checking a reported enclosure by certificate instead of rerunning a matcher is
slower on every retained case, by factors of 0.08 to 0.41. It overtakes recomputation between 30
and 90 detections and reaches about 4.7 times faster at 900.

| detections | certificate ms | analyst recompute ms | ratio |
|---|---|---|---|
| 30 | 0.1513 | 0.1075 | 0.71 |
| 90 | 0.5071 | 0.9125 | 1.80 |
| 225 | 1.8520 | 7.0188 | 3.79 |
| 450 | 6.1942 | 28.0575 | 4.53 |
| 900 | 26.2998 | 123.8631 | 4.71 |

The retained cases are all below the crossover. On this lane's own evidence the certificate is
the wrong tool for them.

**Integration.** Four modules against none. A consumer trusts `cohort_packet` and
`observation_cover` to produce, and `check_cohort_packet` and `check_observation_cover` to check.
The checkers import nothing from the producers and run neither a matcher nor a search; that is
asserted in the test suite, not in prose. The shared trusted surface is the JSON module,
`Fraction` and integer arithmetic, and two declared string conventions. It is still four modules
the analyst does not have to install.

**Preparation and computation.** Level. The analyst prepares the same readings and runs the same
matchers over them. The measured build times sit within a factor of 1.2 of the analyst's own
reading pass on every case.

## What is not claimed

- The observation list is a function of the shared readings. An analyst holding them could
  compute it too. What is measured is its length and its checkability, not exclusive access.
- Every verdict here is over admitted readings, never over the physical world.
- The live two window comparison is still open at `[-8, 8]` with no admitted reading and no human
  reference. It is reported as `waits_on_a_reference`, which names the open anchors rather than
  any atom. No reading was invented for it and no resolved real example is manufactured.
- No person has run either method on this cohort. Every human cost is `unmeasured`, and command
  time is not offered as a proxy for it.
- The exact shortest list is searched only below a declared budget of 22 candidate atoms. Past it
  the report brackets.

## What could refute this

1. A cohort where the certified list is no shorter than the diff. The generator produces one
   whenever every disputed atom lies in some separating set and no two coincide; none appeared in
   1400 instances, but the construction permits it and the claim is registered against it.
2. A real cohort whose disputed set is small enough that the diff was never a burden. Then the
   list saves nothing and the only remaining difference is the checkability.
3. An analyst measured with ordinary source tracing and viewing tools who reaches the same
   shortened list as fast. Nothing here measures a person, so this is open.
4. A separating set structure where the packing bound is loose often enough that `bracketed` is
   the normal state. It already is at 20 objects and 20 readings in the generator, where 4 of 200
   instances need a list and none of them is certified shortest.

The headline is registered in [`tools/measure/headline_audit.py`](../tools/measure/headline_audit.py)
as `standing, bounded`, with the three artifacts that limit it cited there. The register now
distinguishes an artifact that refutes a headline from one that bounds it, because a standing
headline with no stated limit is the shape most of this lane's withdrawn claims arrived in.
