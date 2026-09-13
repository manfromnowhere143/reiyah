# What the dependence coefficient can be, when the objects that define it are the missing ones

Document ID: `reiyah.joint-miss-identification.2026-09-13`

Version: `0.2.0`

Supersedes `0.1.0` of the same document ID, correcting four statements. Every superseded claim is
quoted below rather than removed.

Lifecycle status: `proposed`

Lane: independent research and conventional comparator, parallel to the Engine. Changes no Engine
file, no shared handoff, no frozen protocol and no owner checkout. Creates no reference admission,
no reviewer and no human judgement. Gate A remains unaccepted.

## The question

The dependence estimand of this programme is

```
c = P(both channels miss) / ( P(A misses) * P(B misses) )
```

which `docs/ESTIMAND_RSS_DEFINITION_32.md` binds to the smallest admissible constant in Definition
32 of the retained primary source. Every result in this lane so far has been about comparing
detectors against a reference. None has asked whether `c` can be recovered at all.

It is the sharpest instance of the problem the admission sensitivity work exposed, because the
objects in the numerator of `c` are **exactly the objects no channel reported**. They leave no trace
in any channel's output. Two channels sort a population into four cells, `n11` both detect, `n10` and
`n01` one each, and `m` neither, and only the first three can be counted. Writing `S` for the
observed total and `N = S + m`,

```
c(m) = m * N / ( (n01 + m) * (n10 + m) )
```

## Four results

**One: two channels do not identify the coefficient.** As `m` runs over the non negative integers,
`c(m)` rises from `0`, reaches an interior maximum above `1`, and falls back towards `1`. On the
retained counts `n11 = 10, n10 = 5, n01 = 5` the coefficient ranges over `[0, 4/3]`. The same three
observed numbers are consistent with near total negative dependence and with substantial positive
dependence. No care with `n11`, `n10` or `n01` narrows this, because the unknown is in a cell none of
them touch.

**Two: the standard repair assumes the answer.** Filling the missing cell with the Lincoln and
Petersen capture recapture estimate `m = n01 * n10 / n11` gives `c = 1` **exactly**, for every
`n11`, `n10`, `n01`. Not approximately, and not on average. The identity is asserted as a test over
200 random tables. It is not a coincidence: that estimator is derived by assuming the two channels
are independent, and `c = 1` is the statement that they are. A pipeline that fills the joint silent
miss cell by capture recapture and then reports `c` has reported its own assumption, and would do so
with any data whatsoever.

**Three: the sign question reduces exactly.** For any number of channels, writing `u` for the
observed objects the pair both miss, `a` and `b` for the observed objects each misses, `w` for the
observed objects both detect and `S` for all observed objects,

```
c(m) > 1   if and only if   m * w  >  a * b - u * S
```

So asking whether two channels are positively coupled is exactly asking whether the number of objects
nobody saw exceeds `(a*b - u*S) / w`. With two channels `u = 0` and the threshold is the capture
recapture figure again. This is what a reference programme actually has to deliver: **a bound on the
dark figure tight enough to fall entirely on one side of that threshold.** Tighter buys precision in
`c`. Looser leaves the sign open however many objects are annotated.

**Four: a third channel can settle the sign with no reference at all.** If

```
a * b  <=  u * S
```

the threshold is at or below zero, so `c > 1` for **every** admissible dark figure, and the
conclusion holds without annotating anything. This cannot happen with two channels, where `u = 0`
forces the threshold non negative, and that is asserted as a test. It becomes possible as soon as a
third channel observes objects the pair both missed, because those objects are direct evidence about
the very cell that was unobservable.

The retained table `three-channel-sign-settled` is an instance. Threshold `-491/27`, and the
coefficient for the pair sits in `(1, 1679/1188]` across every possible dark figure, with an infimum
of `1` that is never reached. Collapsing the third channel away puts the threshold back above zero,
which is also a test: the third channel is doing the work, not the arithmetic.

## What this changes

The joint silent miss question has **two routes, not one**. Bounding the dark figure by reference
annotation is the hard route, and it is the one this programme has been organised around. Adding an
independent channel that sees some of what the pair misses is the other, and for the sign question it
can be sufficient on its own. The two are not equivalent: a reference bound gives a value for `c`,
while a third channel can give only the sign unless the dark figure is also bounded. But the sign is
what a one sided constant in Definition 32 is about, and the second route does not require solving
the reference problem first.

## Two corrections made while building this

The first version searched for the range of `c` by assuming it was unimodal in `m`. That is true for
two channels, where the derivative's quadratic is downward with a non negative value at zero, but it
was an assumption rather than a result and it does not obviously survive a third channel. The search
now locates every real root of that quadratic using exact integer square roots and brackets each one,
assuming no monotonicity at all, and it is checked against a full scan on both two and three channel
tables.

The second was found by reading output rather than trusting it. With no upper bound on `m`, the
first version reported the smallest value among the integers it examined as the range's lower end.
On the three channel table the coefficient descends towards `1` from above, so the true infimum is
`1` and it is never attained, while the reported lower end was `24/17`. **An unattained limit and an
attained extreme are different things**, and the report now carries both separately with an
attainment flag. The earlier figure was not a rounding matter; it was a bound stated where no bound
held.

## Corrections to version 0.1.0

An Engine review supplied counterexamples against the released module. All were reproduced against
the exact source before any repair, and the repairs are at the source of each fault rather than in
the adversary.

**The published boundary condition was wrong by one relation.** Version 0.1.0 said:

> "If `a * b  <=  u * S` the threshold is at or below zero, so `c > 1` for **every** admissible dark
> figure"

At equality the threshold is exactly zero and `c(0) = 1`, so strict inequality does not follow. The
counts `110 = 101 = 011 = 001 = 1` are the witness. The condition for strict positivity is
`a * b < u * S`; equality gives a separate state, `c_at_least_1`, reaching `1` only at a dark figure
of zero. The code used `< 0` and was right; the prose was not.

**Three classifications were missing, and one verdict was emitted where none existed.** Where no
object is detected by both channels the sign condition stops involving the dark figure at all, so
the sign is settled outright rather than left open; version 0.1.0 reported `undetermined` because it
could not divide by `w`. The absence of a division is not the absence of a conclusion. Counts
`n10 = n01 = 1, n11 = 0` give `c(m) = 1 - 1/(m+1)^2 < 1` everywhere, and a constant table gives
`c = 1` everywhere, which also refutes the blanket statement that the limit is never attained.
Separately, `n11 = 10, n10 = 0, n01 = 5` with the count pinned at zero reported `c_at_most_1` while
the coefficient had no value there. **An undefined ratio is not a sign verdict**, and it is now its
own state.

**A range was reported where no minimum exists.** With no upper bound, version 0.1.0 invented a
ceiling from the stationary points and reported the extremes over that window. On `w = 10` with
`x = y = u = 10` there is no stationary point, the window was two integers wide, and the report named
`21/11` as the smallest value when `m = 2` gives `11/6` and no smallest value exists at all. Correct
infimum fields did not excuse a contradictory minimum field. The candidates are now the bound's own
ends and the stationary points inside it, which is complete because the coefficient has at most two
interior extrema, and `minimum` is reported as absent when it does not exist. The declared bounds are
also counts now, so a boolean no longer passes as one.

**The identified set is discrete.** Version 0.1.0 wrote that "every value between `0` and that
maximum" is consistent with the observed counts. The dark figure is an integer, so the identified set
is a discrete set and the interval reported is its enclosure, not a list of reachable values.

**The plug in identity is about one estimator on its own domain.** It holds for the two channel
Lincoln and Petersen plug in where some object is detected by both channels. It is not a statement
about capture recapture methods in general, and estimators that model dependence explicitly or use
more than two channels are outside it. The fitted count is also generally not an integer: on the
retained counts it is `5/2`, so `c = 1` is attained off the grid the count actually lives on.

## Correction: a constant, not a sign

Version 0.1.0 closed by saying a third channel "can give only the sign unless the dark figure is also
bounded". This lane's own arithmetic contradicted that in the same document. Definition 32 of the
retained primary source reads `P[r1 and r2] <= c P[r1] P[r2]`: a **quantitative upper constant**. The
supremum of the coefficient over every admissible dark figure is exactly the smallest constant that
holds whatever the dark figure turns out to be, and it was already being computed.

| table | reference used | smallest admissible constant |
|---|---|---|
| three channel `w=27, x=10, y=13, u=23` | none | `c <= 1679/1188` |
| two channel `10, 5, 5` | none | `c <= 4/3` |

So an additional source supplies a Definition 32 constant with no reference annotation at all, and a
tighter dark figure bound tightens it. That is a stronger result than the one withdrawn.

It is also not enough on its own. A sign test does not discharge Definition 32, which asks for a
number. And the majority vote redundancy argument of Corollary 3 needs marginal miss bounds for each
channel and a specified safety critic event, and covers ghost mistakes as well as misses. None of
those is computed here, and the report says so in the field that carries the constant.

## Limits

This is an identification statement about declared counts. No population is sampled, no channel is
named, no value of `c` is estimated, and nothing here establishes that any real pair of channels is
or is not positively coupled. The counts are illustrative and labelled so.

The analysis assumes the four cells describe one declared opportunity universe with a single unknown
cell, which is the structure the estimand document already requires. It says nothing about sampling
error, about whether objects are independent units, or about what makes a channel's output comparable
to another's. A third channel helps only if it genuinely observes objects the pair missed, and
nothing here verifies that a candidate third channel does so rather than sharing their blind spots;
that is exactly the dependence being measured, and assuming it would repeat result two's error one
level up.

## Reproduce

```sh
python3 -B tools/measure/joint_miss_identification.py 10 5 5
python3 -B tools/measure/joint_miss_identification.py 10 5 5 3 8
python3 -B -m unittest discover -s tools/measure -p 'test_joint_miss_identification.py'
```

Twenty eight tests, about 0.12 seconds. Exact rational arithmetic, standard library only, no data
read. The three channel table is reached through `analyse` with its pattern counts; see the retained
`research/joint-miss-identification/0.1.0/README.md`.

## Non-claims

An internal research artifact, retained as `proposed`. Not independent external scientific review,
not an operator acceptance, not a safety, compliance or vendor claim, and not a measurement of any
channel, product or system. It names no vendor and evaluates no deployed detector. No released `1.2`
byte, frozen protocol, claim-register entry, Engine file or other owner's work is modified.
