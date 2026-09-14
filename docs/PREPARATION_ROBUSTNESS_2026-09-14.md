# Auditing our own claim across admissible preparations

Document ID: `reiyah.preparation-robustness.2026-09-14`

Version: `0.2.0`

Supersedes `0.1.0`, which reported a flip witness. Answering one consumer question withdrew it.

Lifecycle status: `proposed`

Lane: independent research and conventional comparator. Changes no Engine file, no common operand,
no admission, viewer, shared handoff or main. Gate A remains unaccepted.

## Three withdrawals first

A consumer review found three defects in `review-cost-0.1.0`. All three were reproduced here before
anything else was done, and all three are withdrawn.

**The worst case is not invariant to the anchor weights.** At weights `(99/100, 1/100)` this lane's
own function returns **9**, not 16, at tolerance `0` and at the Engine's `1/10`. Three weightings
were swept and the word "invariant" was written. That is a sweep generalised into a theorem.

**The review cost model does not transfer to the Engine loss.** It assumed `r` independently
observable binary facts, one per retained addition. In this lane's own `matching-trap` case the
addition is identical in both worlds and only the disputed **base** neighbour differs, yet the loss
moves from `-1` to `+1`. Matching competition is global, so an addition carries no local truth bit.

**"No ordering helps without a prior" contradicts an artifact this lane published four checkpoints
earlier.** `resolution-plan-0.3.0` retains a case with adaptive depth `2` against a smallest fixed
set of `3`, with no probability anywhere in the calculation.

The third is the one that should worry a reader. It is not a mathematical error; it is a lane
contradicting its own retained evidence and not noticing.

## The process repair

`headline_audit.py` registers every published headline with the assumptions it needs and the
retained artifacts that could refute it, and refuses to clear a standing headline that one of them
contradicts. It runs before a checkpoint is published.

It cannot know a counterexample nobody registered, it does not verify any arithmetic, and a headline
passing it is unexamined rather than confirmed. It catches exactly one failure: a claim that
contradicts evidence this lane already holds. That is the failure that just occurred.

## The bounded demonstration

The claim under audit is this lane's own: **same modality detector pairs are more coupled than cross
modality pairs at matched miss rates**, from `modality-coupling-0.1.0`. It carries an engineering
consequence, buy sensor diversity rather than software diversity, so its robustness is worth knowing.

**The family was written down and digested before any result was computed**, at
`8e633b95e594c8b9c13061cb0af2ce19e0049a317013f3687a3c742144ac367c`. Forty eight preparations from
class scope, range band and visibility floor. Each is a standard published evaluation scope choice,
and **none changes any detector's output**.

The detector score cutoff is deliberately **excluded**. Raising it changes the system being
evaluated, so a flip obtained that way is a configuration comparison and not uncertainty about one
fixed configuration. It is held at the matched miss rate instead.

## Withdrawn: the flip witness

Version 0.1.0 reported that the claim fails in 5 of 48 evaluation scopes, every failure at close
range. A consumer required each comparison to state whether it changes scope, operating point,
evidence interpretation, or several of these. Answering that withdrew the result.

Each preparation re-thresholded every detector to the same miss rate **inside its own subset**. That
keeps marginals comparable, which the estimand contract requires, and it silently moves the score
cutoff with the scope. On vehicles within 30 metres at the best visibility band the cutoffs move by
up to **`+0.521`**. So every one of the 48 preparations changed the scope **and** the operating point
of every detector, and the checkpoint did not say so.

Holding the cutoffs at their full scope values, so the configuration is genuinely fixed, **all five
failing cells hold**, by margins from `+0.151` to `+1.512`.

**The flip was an operating point effect, not a scope effect. It is withdrawn.**

## And the other arm is not clean either

Fixing the cutoffs leaves the marginals unmatched. In **0 of 48** preparations do the five detectors
reach the same miss rate, and this lane's own estimand contract states that the coefficient is not
comparable across marginals. The one failure in that arm, vulnerable road users within 30 metres,
spans achieved miss rates from `0.210` to `0.337`, so it is not a clean counterexample either.

## The result is an obstruction, not an answer

| arm | marginals | operating point |
|---|---|---|
| matched rate | comparable, in 9 of 35 exactly equal | **moves with the scope** |
| fixed cutoff | **never matched, 0 of 48** | fixed |

**No preparation in this family isolates the scope effect for this estimand**, because the
coefficient is marginal dependent and a population subset changes the marginals. That is a
structural statement about auditing a marginal dependent quantity across sub populations, and it is
worth more than the flip would have been, because it says why the audit cannot be completed rather
than reporting a result that a second question dissolves.

What survives is narrower and carries its scope: the claim holds at full scope with matched
marginals, and this family cannot extend it to sub scopes.

**The consumer requirement did the work, not the method.** Asking what each comparison changes
withdrew a published result and replaced it with an obstruction.

## The withdrawn version's result

## The result: the claim is not robust

| outcome | preparations |
|---|---|
| predicate holds | 30 |
| **predicate fails** | **5** |
| undefined | 13 |

**Every one of the five failures is a close range scope.** At vehicles within 30 metres the ordering
interleaves:

| coefficient | kind | pair |
|---|---|---|
| 2.531 | same | centerpoint/megvii |
| 2.490 | same | fcos3d/mapillary |
| 2.132 | same | megvii/pointpillars |
| **2.124** | **cross** | **centerpoint/fcos3d** |
| 2.118 | cross | fcos3d/megvii |
| **2.092** | **same** | **centerpoint/pointpillars** |

The responsible pair is named: `centerpoint/pointpillars`, two lidars with different architectures,
falling below two camera and lidar pairs.

The margin carries as much as the sign. The claim holds at full scope by `+0.4409` at its best and
fails by `-0.1057` at its worst. That worst failure is **not** a knife edge, which matters because
this lane has been burned by a thin margin before and now reports the margin rather than a bare
boolean.

**The scope was part of the claim all along, and was not stated when the claim was published.**

## The comparator, honestly

The baseline is the ordinary full grid over the same family, which is multiverse analysis in the
sense of Bell, Kampman, Dodge and Lawrence, *Modeling the Machine Learning Multiverse*, NeurIPS 2022.

**This lane ran that grid. The grid is not a competitor it beat; it is the method that produced the
result.** Nothing here outperforms an analyst sweeping the same family, and the parity that has now
held four times holds again.

What the procedure added is not algorithmic. It is that the family was fixed before the result, that
evaluation scope was separated from configuration change, and that the responsible pair is named.
That is discipline, and it should not be sold as an advantage.

## What is not established

Nothing about physical risk, human effort or industry practice. The close range structure suggests a
reading, that both modalities are strong nearby so their residual failures become object specific
rather than modality specific, and **that reading is not tested here**. This is retrospective and
annotation conditional, it admits no independent human reference, and it changes nothing about the
live Engine comparison, which remains `[-8, 8]`.

## Reproduce

```sh
python3 -B tools/measure/headline_audit.py
python3 -B tools/measure/preparation_robustness.py
python3 -B -m unittest discover -s tools/measure -p 'test_preparation_robustness.py'
```

Seventeen tests, about 6.7 seconds for the grid over 134,565 annotated objects, exact rational
arithmetic, standard library only.

## Non-claims

An internal research artifact, retained as `proposed`. Not independent external scientific review,
not an operator acceptance, not a safety, compliance or vendor claim, and not a market position.
