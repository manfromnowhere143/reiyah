# What the decision costs in human judgements, and why no ordering reduces it

Document ID: `reiyah.review-cost.2026-09-13`

Version: `0.1.0`

Lifecycle status: `proposed`

Lane: independent research and conventional comparator. Changes no Engine file, no common operand,
no admission, viewer, shared handoff or main. Gate A remains unaccepted.

## Why this question, and not another statistic

Three times an ordinary overlap baseline has reproduced this lane's result: the coefficient's
ordering, the raw two channel sign, and the retained addition count. Each of those was a **scalar
summary**, and a scalar computed from counts is exactly where a simple baseline competes. Producing a
fourth scalar would be a fourth parity.

So this asks a different kind of question, one overlap has no analogue for. Not what the number is,
but **how many human judgements it takes to decide, and whether choosing what to look at first
helps.**

## The setting

With `r` retained additions and `k` of them corresponding to a real object the base missed,

```
delta = (a + b) * k - b * r,        0 <= k <= r
```

so the coarse bound is `[-b*r, a*r]` and the sign turns on `k` against `b*r/(a+b)`. A reviewer
resolving one addition learns whether it belongs to `k`.

## Result one: a ranked review queue cannot narrow faster

Resolving any record narrows the interval by exactly `a + b`, **whichever record it is**. The width
after `j` judgements is `(a + b) * (r - j)`, and nothing about the choice enters.

That refutes the obvious product, a prioritised review list, before it was built. It is the second
product idea this lane has killed with its own data rather than shipped.

## Result two: the worst case is every record

The decision is the sign, not the width, so early stopping is possible once one side is settled. It
does not help in the worst case.

Solving the adversarial game exactly, the worst case number of judgements is **`r`: every retained
addition must be resolved.** Verified exhaustively for `r` up to 15 across seven penalty pairs
including asymmetric ones, with no exception.

A first draft of this document claimed an exception at `b = 0`, where no penalty falls on false
positives, on the reasoning that the threshold sits at zero and one confirmed addition settles the
sign. **That is wrong, and a test caught it before publication.** With `b = 0` the adversary answers
not real every time, `k` stays at zero, the negative side is settled only when no records remain, and
the cost is `r` again. The result is universal rather than conditional, which is stronger than what
was first written.

The reason is short: while a decision needs `k` compared against a threshold strictly inside
`[0, r]`, or against zero from below, the adversary can always answer so that both outcomes stay
reachable, and only exhausting the records removes that freedom.

## Result three: the live comparison costs sixteen

The Engine's real comparison carries two anchors with `r = 9` and `r = 7` at equal weight, giving
`[-8, 8]`. Solving the two anchor adaptive game exactly:

**16 worst case reference judgements, which is the total.**

And it is invariant to structure. Every split of 16 across two anchors returns 16. Every weighting
tested, including `3/4` against `1/4` and `1/10` against `9/10`, returns 16.

## What this means for a validation lead

The previous checkpoint measured that `r` moves by **29.9 times** across defensible preparations,
with the score cutoff alone accounting for 21.6 times. This checkpoint shows that `r` then fixes the
review cost exactly.

Put together: **the entire human cost of the decision is fixed by preparation, before anyone looks at
anything, and no ordering of the review reduces it. The only lever is preparation. Reviewer
cleverness is not a lever at all.**

That is a statement about where to spend effort, and it is the first result in this lane that an
overlap baseline has no way to produce, because it is a property of the decision procedure rather
than of a count.

## What is not claimed

This is **worst case**. An expected case would need a prior over which additions are real. None is
established here, and inventing one so that prioritisation looks useful is precisely the move this
lane refuses. Whether a justified prior exists is open, and it would change result two while leaving
result one untouched.

The unit of effort is declared rather than measured: one resolved record counts as one judgement, and
nothing here establishes that human effort is constant across records. The retained additions are not
established to be physical objects, and no value for the loss itself follows without admitted
references.

## Reproduce

```sh
python3 -B tools/measure/review_cost.py
python3 -B tools/measure/review_cost.py 9 7
python3 -B -m unittest discover -s tools/measure -p 'test_review_cost.py'
```

Twenty tests, exact rational arithmetic, standard library only, no data read. A comparison larger
than the exact search budget returns a resource limit, never a claim that the cost is unbounded.

## Non-claims

An internal research artifact, retained as `proposed`. Not independent external scientific review,
not an operator acceptance, not a safety, compliance or vendor claim. It creates no reviewer, no
reference and no human judgement, and admits none.
