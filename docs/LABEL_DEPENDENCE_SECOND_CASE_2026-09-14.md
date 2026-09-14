# The second case replicates, and the raw breakdown number would have hidden it

Document ID: `reiyah.label-dependence.second-case.2026-09-14`

Version: `0.1.0`

Lifecycle status: `proposed`

Date: 2026-09-14. Lane: independent research.

Analysis preregistered at `7a513c501c5ada227206ed5028f78b436b36cd83ae9db3f8a648fad8e3f82b81`,
written and published **before the second case existed**, while its anchor weights, its margin and
its label count were unknown here.

Artifacts: [`research/label-dependence/0.4.0/second-case-singles.json`](../research/label-dependence/0.4.0/second-case-singles.json),
[`research/label-dependence/0.4.0/second-case-breakdown.json`](../research/label-dependence/0.4.0/second-case-breakdown.json),
[`research/annotation-case/0.2.0/source-reconstruction.json`](../research/annotation-case/0.2.0/source-reconstruction.json)

## The result

| case | anchors | labels | weight | decision | tolerance | margin | largest step | k_floor | k_observed | ratio |
|---|---:|---:|---|---|---|---|---|---:|---:|---:|
| first | 2 | 106 | 1/2 | +1 | 1/10 | 9/10 | 1 | 1 | 1 | **1** |
| second | 14 | 737 | 1/14 | 2/7 | 1/10 | 13/70 | 1/7 | 2 | 2 | **1** |

Both verdicts sit exactly at their arithmetic floor. The sensitivity result repeats.

The raw breakdown numbers are **1 and 2**, and comparing those directly would have said the second
case was twice as robust. It is not. It is as fragile as its own arithmetic allows, exactly like the
first. The difference in the raw number is entirely explained by a smaller margin spread over
fourteen anchors at weight `1/14` instead of two at `1/2`.

## The trap this walked into, and why it was set first

The mandated single deletion family on the second case: **737 deletions, zero criterion changes,
every one still `supported` and `prefer_augmented`.** Read plainly that is a robustness result.

It is not a result at all. Deleting one annotation reduces its anchor's gain by at most one, so it
moves the weighted decision by at most `(a + b) * weight = 1/7`. The margin above tolerance is
`13/70`, which is larger. **No single deletion on this case could ever have changed the criterion,
whatever the annotation said.** Zero changes was forced by the weights and the margin before any
label was looked at.

That is why the floor and the ratio were built and published before the case arrived. Reporting
"737 deletions, no change, robust" would have been a false result, and this lane would have produced
it in good faith.

The signed loss difference is worth reporting separately from the criterion, as declared: the
weighted delta ranges over `[1/7, 2/7]` across the family. Every single deletion costs the addition
something or nothing; none makes it harmful, and none reaches the threshold.

## The witness, and why no exhaustive pair search was run

Since the floor is 2, no set of size 1 can cross, so any size 2 set that crosses is minimal by
construction. One verified witness settles `k_observed` exactly, and enumerating all 271,216 pairs
would establish nothing further about the minimum. The brief asked for a checked bound or a small
witness rather than a forced search, and the floor is that bound.

Matching is computed per anchor, so two gain carrying labels in **different** anchors each remove
one unit of gain independently. Two units cost `2/7`, which takes the decision from `2/7` to `0`,
at or below the tolerance. The construction is then verified by full recomputation rather than
trusted:

| anchor | class | local index |
|---|---|---:|
| `remaining-window-0001` | barrier | 20 |
| `remaining-window-0002` | barrier | 7 |

Result: weighted delta `0`, criterion `excluded`, preference `equivalent_within_tolerance`.

An adversarial control is retained: two gain carrying labels **inside one anchor** are not
guaranteed independent, because the matching can reassign around one of them. The pair tested here
also crosses, at `0` and `excluded`. Two evaluations, 0.008 seconds, against 271,216 for the
exhaustive alternative.

53 of the 737 labels individually carry a unit of gain, spread across 13 of the 14 anchors: 35
barriers, 6 cars, 6 pedestrians, 5 traffic cones, 1 bicycle.

## The independent reconstruction underneath

Rebuilt here from the original tables before any of the above was accepted, to the same standard as
the first case.

| quantity | reconstructed here | declared |
|---|---:|---:|
| anchors | 14 | 14 |
| original annotations | 841 | 841 |
| included | 737 | 737 |
| excluded beyond 50 m | 101 | 101 |
| excluded, category not in the detection map | 3 | 3 |

The three unmapped rows are all `human.pedestrian.stroller`, which is not a nuScenes detection
class. Membership is identical token for token with zero class disagreements.

The closest excluded annotation sits at **50.065 metres** against a 50 metre boundary, a margin of
6.5 centimetres. On the first case it was 28 centimetres. Membership on both cases is close to its
own boundary, which is a property of the declared range and not a defect.

## Three corrections to the first checkpoint, reproduced before repair

Each was reported by the consumer, reproduced here on the exact selected source, and repaired.

**The packet header named the wrong case.** The label dependence manifest asserted
`8e79f363…`, the physical open case, while every payload recorded `ebfebf67…`, the annotation case.
Both digests are real, so nothing looked wrong. The seal now cross checks a header's asserted case
digest against the digests the payloads themselves carry and refuses to write a manifest when no
payload supports it. The failing shape is a retained test.

**The insertion family recorded only the singles range.** Singles range over `[1, 2]`; all 190 pairs
range over `[1, 3]`. The no criterion change conclusion survives, but reporting the singles range
alone understated the family's reach. Both extrema are now recorded separately.

**The insertion rule was a graph neighbourhood, not a distance.** Version 0.2.0 joined an inserted
object to every same class detection that already shared one of its detection's objects. The
consumer's control shows the gap: detections at `(0, 0)` and `(3, 0)` sharing an object at
`(1.5, 0)`, with an insertion at `(3, 0)`. Under the declared strict 2 metre rule only the detection
at `(3, 0)` reaches it; the old rule connected both. On the first case all 20 singles and 190 pairs
happened to agree with the coordinates, which is luck and not a reason. The rule now applies the
declared distance to the supplied coordinates in exact rationals, and **refuses to run at all**
without them rather than falling back on a heuristic. Rerun under the corrected rule, the first
case's conclusion is unchanged.

One wording correction with no code behind it: the deletion family was declared before its own
outcomes, and the insertion family was declared before its own outcomes and after the deletion
result. Saying both were fixed before every result in that checkpoint would have been wrong.

## What follows, and what does not

For these two cases: a benchmark verdict that clears its threshold by less than two units of gain
can be removed by deleting the smallest number of labels its own arithmetic permits, and the labels
that do it are identifiable and few.

What does not follow. Nothing about other scenes: both cases draw on the same two scenes and neither
is held out. Nothing about label error rates, because no annotation has been checked and a count of
hypothetical corrections is not a probability. Nothing about human time, industry practice or
customer value. Nothing about the physical comparison, which remains open at its own state. The six
first case witnesses are not a measured reduction of review work, and correct labels there would not
settle other error families.

An ordinary analyst with the same bytes can compute the floor, the family and the witness. The
shortcuts used here are stated so they can use them too: the per deletion bound `(a + b) * weight`,
the per anchor independence of the matching, and the fact that a witness at the floor is minimal
without search.

## Next falsifier

A case whose fragility ratio is above one: a verdict that survives more deletions than its
arithmetic requires. That would show the ratio distinguishes cases rather than always returning one,
which two cases cannot establish. A third case from a different scene would also separate the
finding from these two scenes, which is the larger gap and is not this lane's to close.
