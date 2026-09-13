# How much verified third source evidence is enough, when the table itself may be wrong

Document ID: `reiyah.table-robustness.2026-09-13`

Version: `0.2.0`

Supersedes `0.1.0` of the same document ID. It removes the declared budget from the critical path and
refines one number this lane published one commit earlier.

Lifecycle status: `proposed`

Lane: independent research and conventional comparator, parallel to the Engine. Changes no Engine
file, no shared handoff, no frozen protocol and no owner checkout. Creates no reference admission,
no reviewer and no human judgement. Gate A remains unaccepted.

## The gap this closes

The identification result assumed the observed counts were counts of real, unique, eligible objects
with correct cross channel identities. Raw detector output does not establish that. A false
detection, a duplicate, a wrong association or a class, range or time exclusion changes the
supposedly observed cells, and the conclusion is a statement about the corrected table rather than
the raw one.

In the elementary notation, with `w` captured by both channels, `x` and `y` by one each, `u` pair
misses seen by an additional source and `m` the objects no source saw:

```
c > 1   if and only if   w * (u + m) > x * y
```

which is the same statement as the earlier `m * w > a * b - u * S`, asserted as a test over 400
random tables. **No statistical independence assumption about the additional source appears in it.**
That is worth stating carefully rather than celebrating: the condition needs the counts to be
**valid**, which is an observation obligation, and validity, statistical independence of the
channels, and procedural independence of a review are three different things. Only the first is
addressed here.

Because `w >= 0`, the condition is hardest at `m = 0`, so a table settles the sign for every unseen
count exactly when `w * u > x * y`.

## How much evidence the retained table actually needed

On the retained table `w = 27, x = 10, y = 13, u = 23`:

| quantity | value |
|---|---|
| margin `w * u - x * y` | `491` |
| smallest `u` that settles the sign, holding `w`, `x`, `y` | **`5`** |
| observed `u` | `23`, which is `23/5` of the requirement |

So conditional on the first three counts being correct, **five verified pair misses would have been
enough**. This is an evidence obligation stated as a number, not a promise about how many review
attempts it takes to obtain them.

## Which errors actually bind

The kinds of error are not equally damaging, and the ordering is the useful output. Each row is the
largest allowance of one correction kind that still settles the sign, computed exactly and checked
against direct evaluation of the resulting table.

| correction | survives up to | breaks at |
|---|---|---|
| a pair miss was really captured by the first channel (`u` to `x`) | **12** of 23 | 13 |
| a pair miss was really captured by the second channel (`u` to `y`) | 13 of 23 | 14 |
| a joint capture was really a single capture (`w` to `x`) | 13 of 27 | 14 |
| a pair miss object was spurious or ineligible (`u` removed) | **18** of 23 | 19 |
| a joint capture was spurious or ineligible (`w` removed) | 21 of 27 | 22 |
| any correction that favours the conclusion | all | never |

**Misassociation binds before spuriousness**: 12 tolerated against 18. The reason is structural. An
object wrongly counted as a pair miss when the first channel did detect it leaves `u` and arrives in
`x`, so it weakens the left side and strengthens the right side at once. An object that is simply not
a real object only leaves `u`.

That is an actionable observation obligation. For this conclusion, verifying that a pair miss object
was genuinely missed by both channels is worth more than verifying that it exists.

## Attacking the conclusion

A declared, bounded budget says how many objects in each cell may be wrong and in which direction.
Every admissible corrected table is enumerated, and the sign is reported as surviving only if it
holds for all of them. The adverse completion that comes closest to breaking it is retained, so the
answer is checked by evaluating one table rather than by trusting the search.

| declared budget | corrected tables | worst margin | sign survives |
|---|---|---|---|
| none | 1 | `491` | yes |
| 2 into `x`, 2 into `y`, 5 removed | 54 | `198` | yes |
| 6 into `x`, 6 into `y`, 11 removed, 5 of `w` into `x`, 5 of `w` removed | 21,168 | `-399` | **no** |

The destroying completion is `w = 22, x = 21, y = 19, u = 0`. The adversary does not perturb the
counts independently; it moves objects out of `u` and into `x` and `y`, which is the coupled move,
and only then removes the rest. **A model that jittered each count on its own would miss it.**

Nothing here invents an error budget, a sampling frame, a probability or a human judgement. The
budget is an input, defended by whoever declares it, and the module refuses to run without one.

## Removing the budget from the critical path

Version 0.1.0 closed by naming its own open obligation: **nothing verifies that a declared
correction budget is large enough, and a budget smaller than reality gives a confident wrong
answer.** A required input that nobody can check is a weakness, so the question is inverted.

Instead of asking whether a claim survives a declared budget, ask **how many recorded objects would
have to be wrong, in the most damaging combination, before the claim fails**. That number needs no
budget. An observation programme can weigh it against its own process, which is a question it is
competent to answer, rather than committing to a budget in advance.

On the retained table, of 73 recorded objects:

```
the sign  c > 1  fails only if at least 12 of them are wrong,
and only in a combination that splits the pair misses between both channels.
```

The search is over every allocation of corrections across all twelve move kinds, so no direction is
assumed away. Restricting to the six that can damage the sign returns the same number in 18,563
allocations instead of 2,704,155, and that restriction is **asserted as a test rather than taken on
trust**, because it is sound for the sign and not for the constant claim below.

## Correction: a per kind tolerance is not a breakdown number

Version 0.1.0 published the tolerance table above and it remains correct as stated: twelve
misassociations into `x` alone are survivable, and the thirteenth breaks the sign. It would be wrong
to read that as "the conclusion tolerates twelve wrong objects". **It tolerates eleven.**

Twelve objects moved from `u` to `x` leave the sign standing. Twelve objects split six into `x` and
six into `y` do not. The reason is that the right hand side is a product: balancing the growth
between `x` and `y` maximises `x * y`, so a mixed attack is strictly more damaging than any single
kind. Every minimal breaking attack on the sign is such a split, and none is a single kind.

This is why the exhaustive search earns its cost over the per kind table. The per kind numbers are
each true about their own kind and understate the attack by one when read together.

## The quantitative claim is an order of magnitude more fragile

Definition 32 asks for a **constant**, not a sign, so the robustness an RSS style argument depends on
is the robustness of the constant. It is far worse.

| claim | breakdown | cheapest attack |
|---|---|---|
| `c > 1`, the sign | **12** of 73 | 5 pair misses into `x`, 7 into `y` |
| `c <= 1679/1188`, the observed constant | **1** | one pair miss object was ineligible |
| `c <= 3/2` | **2** | 2 single captures were really joint captures |
| `c <= 8/5` | 4 | the same move |
| `c <= 2` | 10 | the same move |
| `c <= 3` | more than 12 | none found within 12 |

Two things follow, and the second is the one worth carrying.

A tight constant is destroyed by **two** wrong objects where the sign needs twelve. A programme that
reported the sign as robust and then quoted the constant as though the same robustness applied would
be wrong by a factor of six on this table.

And the two claims are threatened by **opposite errors**. The cheapest attack on the sign moves pair
misses into single captures. The cheapest attack on the constant moves single captures into joint
captures, and that move **raises** the sign margin from `491` to `563` while pushing the coefficient
from `1679/1188` past `3/2`. The correction that most strengthens one claim is the one that destroys
the other. An observation programme cannot verify "the errors that matter" without first saying which
claim it is defending, and the two verification tasks are not the same task.

## A coefficient certificate is not an integration decision

`ghost-burden-none` and `ghost-burden-three` have the **same capture table**: the same object captured
by both channels, the same object by the base only, the same `tp_base` and `tp_augmented`. A detection
that matches nothing changes no cell of that table and therefore no coefficient bound. It changes the
false positive burden, and the additive loss moves from `+1` to `-2`, flipping the integration verdict
from `supported` to `excluded`.

So a certificate about the dependence coefficient supports the conclusion it is about, and does not
stand in for the decision. The integration question keeps its base detections, its joint reference
alternatives, its matching competition, its weights, its tolerance and its additive loss assumptions,
and none of those is visible in a capture table.

## Comparison against the baselines

| | this method | direct exhaustive evaluation | conventional cross product plug in |
|---|---|---|---|
| what it answers | does the sign survive every admissible corrected table | the same, and it is the same enumeration | what the unseen count would be under an independence assumption |
| correctness | exact integers, no approximation | exact | exact arithmetic, but it fixes what it should bound |
| sharpness | the exact worst completion, with a one line certificate | identical | none; it returns `c = 1` by construction |
| evidence required | observed cells plus a defended correction budget | the same | observed cells only |
| runtime | 0.2 ms empty, 0.6 ms at 54 tables, 205 ms at 21,168, 9.4 s at 907,038 | identical, this **is** that baseline | microseconds |
| memory | under 16 KiB peak at every size measured | identical | negligible |
| integration burden | one module, standard library, no shared state | none | none |

The honest reading is that this method **is** the direct exhaustive baseline, with the move model and
the certificate added. It claims no algorithmic advance. Its contribution is the dependence aware
move model and the retained worst completion, and its cost grows with the product of the declared
allowances, which is why a budget too large to enumerate returns `unresolved` rather than a verdict.
A resource limit is not an impossibility result and is never reported as one.

The cross product plug in is cheaper and answers a different question. It cannot be attacked by a
correction budget at all, because it fixes the unseen count instead of bounding it.

## Limits

This is finite population identification under a declared budget. It carries **no statistical
uncertainty, no sampling model and no claim about physical accuracy**, and those three stay distinct
from it. The budget is an assertion about how wrong a table may be; nothing here verifies that the
assertion is true, and a budget smaller than reality gives a confident wrong answer.

The move model covers misplacement between the four cells and removal. It does not cover an object
that should be in the table and is in no cell at all, which is the unseen count `m` and is already
handled by taking the condition at its hardest point. It does not cover a correction that splits one
recorded object into two, or merges two into one, beyond what the move counts represent.

The tables here are declared illustrative counts. No population is sampled, no channel or vendor is
named, no deployed detector is evaluated, and nothing establishes that any real pair of channels is
or is not positively coupled. The two window comparison this lane exists to serve remains `[-8, 8]`
with no admitted reference.

## Reproduce

```sh
python3 -B -m unittest discover -s tools/measure -p 'test_table_robustness.py'
```

Thirty six tests, about 20 seconds, the bulk of it the full twelve move search that verifies the six
move restriction. Exact integer and rational arithmetic, standard library only, no data read, no
probability. The breakdown search returns `unresolved` when it passes its allocation cap, because a
resource limit is not an impossibility result.

## Non-claims

An internal research artifact, retained as `proposed`. Not independent external scientific review,
not an operator acceptance, not a safety, compliance or vendor claim, and not a statement that any
vehicle or system is safe to ship. No released `1.2` byte, frozen protocol, claim-register entry,
Engine file or other owner's work is modified.
