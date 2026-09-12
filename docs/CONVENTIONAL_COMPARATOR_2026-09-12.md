# What a conventional analyst concludes from the same evidence

Document ID: `reiyah.conventional-comparator.2026-09-12`

Version: `0.1.0`

Lifecycle status: `proposed`

Lane: independent research and conventional comparator, parallel to the Engine. Changes no Engine
file, no shared handoff, no frozen protocol and no owner checkout. Creates no reference admission,
no reviewer and no human judgement. Gate A remains unaccepted.

## The question

This lane has said several times that its instrument is worth having. It has never said, in a form
anyone could check, what it is worth having **instead of**. Every document here has carried the line
"product differentiation against a competent analyst remains untested". This is that test, written so
that it can come out unfavourable.

The comparator is not a straw man. It is given the same anchors, the same detections, the same
additive loss, the same tolerance and the same admitted readings. It differs in one respect, which is
the respect in which conventional detection benchmarking really differs: **it commits to a single
reading of the reference and reports a number.**

Two such readings are standard practice and both are implemented. The *complete annotation* reading
treats the annotation as true and complete, so anything the detector reports that the annotation does
not contain is a false positive, and where the reference is absent that means nothing is there. The
*single interpretation* reading takes one admitted reading and reports its point value.

## The result that limits this lane, first

**On a cohort whose anchors are all finite, the instrument's `unresolved` state is exactly the
statement that the conventional verdicts disagree across the admitted readings.**

The proof is one line from the definitions. With every anchor finite the enclosure is
`[min_w value_w, max_w value_w]`, and the criterion is `supported` when `min > t`, `excluded` when
`max <= t`. So it is `supported` exactly when every reading is supported, `excluded` exactly when
every reading is excluded, and `unresolved` exactly otherwise, which is exactly when the readings
disagree.

That is a real limit on the claim. On a finite cohort the instrument tells a conventional analyst
nothing they could not have obtained by running their own method once per admitted reading and
comparing the answers. What it contributes is that the comparison is made, and made by default,
rather than depending on an analyst choosing to do it. **When the readings agree, the instrument
contributes confirmation and nothing else**, and it now says so in those words.

Checked on every retained case where it applies, and on 300 random finite cohorts, of which 300 were
applicable and the equivalence held on all 300. Of those, 127 were unresolved and 173 decided, so
both sides of the equivalence are exercised and neither is vacuous.

## The result that supports it, second

**Treating a missing reference as an empty one is not a neutral default. It is the most adverse value
the anchor can take.**

Where the reference is open, the complete-annotation reading contributes exactly `-b * r` at that
anchor: every retained addition is counted as a false positive, because nothing is recorded for it to
match. That number is not measured. It is produced by an assumption about missing data, and the
assumption always points the same way.

On the live two-anchor comparison, which is the comparison this lane exists to serve:

| | value | how it is reached |
|---|---|---|
| conventional, complete annotation | **`-8`** | the 16 retained additions across both anchors are counted as false positives because nothing is recorded to match them |
| instrument | **`[-8, 8]`, unresolved** | the same 16 additions, with the reference not asserted either way |

The conventional number is not near the lower endpoint of the true bound. It **is** the lower
endpoint, exactly. An analyst following standard practice would report that the addition is clearly
harmful, at the worst value the evidence permits, and nothing in their method would tell them that
the opposite endpoint is equally admissible. This is the case for the instrument, and unlike the
first result it is not available to the comparator at any price, because the comparator has no state
for "not asserted".

## What the retained cases show, and what they do not

Of twelve retained cases, ten are ones where the instrument does something substantive and two are
ones where it only confirms.

**That proportion is not an estimate of anything.** Those cases were built by this lane to be hard,
most of them constructed specifically to break something. A population selected for difficulty says
nothing about how often a real cohort is unresolved, and quoting ten of twelve as though it did would
repeat the error this lane retracted yesterday, where a number measured under one condition was
carried into a claim that dropped the condition. The honest statement is that both outcomes occur and
that their frequency in practice is unmeasured.

## Scope, and the hypothesis that does the work

The equivalence is stated for cohorts whose anchors are **all finite** and which admit **at least one
reading**. Both conditions are load-bearing and both are checked rather than assumed.

Once an anchor is open the equivalence fails, and it fails in the direction that matters: the
instrument can report `unresolved` while every admitted reading agrees, because the open contribution
widens the enclosure past a disagreement that does not exist among the readings. A test constructs
exactly that cohort. So `unresolved` means two different things depending on the cohort, and they
should not be conflated: on a finite cohort it reports disagreement between readings, and on an open
cohort it reports that a reference was never asserted.

Where no reading is admitted at all, the conventional method has nothing to run, and it fills the gap
by assuming. That is the live comparison's situation.

## Limits

The comparator implements two standard readings of a reference. It is not a survey of practice, it is
not calibrated against any published pipeline, and no external analyst has reviewed whether it
represents their method fairly. The cases are synthetic except the live two-anchor comparison, which
is real in its anchors and its retained addition counts and has no admitted reference. Nothing here
establishes physical coverage, planner behaviour, risk or a product advantage, and no claim is made
that a conventional analyst would be careless. The first result above says the opposite: on a finite
cohort a careful conventional analyst reaches the instrument's answer by hand.

## Reproduce

```sh
python3 -B tools/measure/conventional_comparator.py research/cohort-packet/0.1.0/open-two-anchor.json
python3 -B tools/measure/conventional_comparator.py research/cohort-packet/0.1.0/oppositely-coupled.json
python3 -B -m unittest discover -s tools/measure -p 'test_conventional_comparator.py'
```

Eleven tests, about 0.2 seconds. Exact rational arithmetic, standard library only, no data read.

## Non-claims

An internal research artifact, retained as `proposed`. Not independent external scientific review,
not an operator acceptance, not a safety, compliance or vendor claim, and not a benchmark of any
named method, product or team. No released `1.2` byte, frozen protocol, claim-register entry, Engine
file or other owner's work is modified.
