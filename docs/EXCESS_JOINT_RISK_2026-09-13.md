# The quantity the ratio was standing in for

Document ID: `reiyah.excess-joint-risk.2026-09-13`

Version: `0.1.0`

Lifecycle status: `proposed`

Lane: independent research and conventional comparator. Changes no Engine file, no Gate B file, no
shared handoff and no owner checkout. Gate A remains unaccepted.

This document records a violation of this programme's own normative contract, the correction, and
two further corrections that arrived with it.

## The violation

`docs/ESTIMAND_RSS_DEFINITION_32.md` carries clause 4, normative:

> "`c` is not comparable across operating points. Any contrast must match or condition on marginals."

and CE-4 in the same document shows why: one channel's operating point moved, **coupling structure
untouched**, sends `c` from `1.8186` to `1.2262`.

Earlier today this lane published a document comparing `c` across nine operating points and reading
the `5.29` times movement as evidence that **independence is worst exactly where safety cases live**.
That is a statement about coupling, drawn from a comparison the contract forbids. An external review
caught it. This lane did not, even after independently discovering the marginal problem and applying
matched marginals elsewhere.

## The correction, which reverses the reading

The permitted quantity is the absolute excess joint miss rate:

```
delta  =  P(both miss)  -  P(A misses) * P(B misses)
```

the extra joint failures per object above independence. It is not a ratio of two shrinking marginals,
it is defined where a marginal is zero, and it is what a safety budget is denominated in.

| captured fraction | `c` (forbidden to compare) | excess per thousand objects |
|---|---|---|
| 0.967 | 2.14 to 5.71 | **38.8 to 87.4** |
| 0.898 | 1.55 to 3.85 | **66.2 to 139.5** |
| 0.789 | 1.12 to 1.90 | 42.3 to 117.9 |
| 0.505 | 1.00 to 1.21 | 0.2 to 95.7 |

**The burden peaks at intermediate capture and falls away on both sides.** At the highest capture the
absolute excess is lower than at `0.898`. The ratio rose while the burden fell, which is precisely
the artifact CE-4 predicts.

The earlier sentence is withdrawn, not softened. Whether any part of the ratio's movement reflects
changing dependence rather than normalisation is an open identification problem, and this document
does not answer it.

## Second correction: the novelty claim

Assessing sensor reliability and error dependence **without a reference truth is not new**, and this
lane should stop implying it is. Berk, Schubert, Kroll, Buschardt and Straub, *Reliability Assessment
of Safety-Critical Sensor Information: Does One Need a Reference Truth?*, IEEE Transactions on
Reliability, 2019, addresses that category directly. Estimating classifier accuracies from unlabelled
predictions is established statistics, for example Jaffe, Nadler and Kluger, AISTATS 2015.

What may be narrow and new here is a label free **sign and bound for this particular Definition 32
constant**, under stated assumptions, with a breakdown guarantee. That is what should be claimed, and
nothing wider.

## Third result, negative: the failure is diffuse

If the coupling were concentrated in a small region, a designer could restrict the operating domain
and recover redundancy. That would have been the useful product. It is false.

At the matched `0.30` operating point, ranking the population by excess joint misses:

| worst share of population | share of the total excess it carries |
|---|---|
| 1 percent | 1.6 to 2.6 percent |
| 5 percent | 7.2 to 14.3 percent |
| 25 percent | 30.7 to 44.9 percent |

**There is no small blind spot to exclude.** The excess is spread across the population, only mildly
concentrated. A blind spot atlas would have nothing to point at, and that idea is refuted by this
lane's own data before it was built.

## A fourth observation, suggestive only

At a matched miss rate of `0.30`, splitting same modality pairs by architecture family:

| grouping | coupling | pairs |
|---|---|---|
| same modality, same architecture | 2.246 to 2.563 | 2 |
| same modality, different architecture | 2.293 to 2.325 | 2 |
| different modality | 1.769 to 1.894 | 6 |

Changing the architecture while keeping the sensor lands **inside** the same architecture range.
Changing the sensor moves out of it. The reading would be that diversity of sensor buys decoupling
and diversity of software does not, which would matter to anyone counting a diverse software stack on
one sensor as redundancy.

**Two pairs per cell is not evidence for a law.** It is recorded as an observation with its sample
size attached, and it is the kind of thing a crossed design with several pairs per cell would settle.

## What is still not settled

The identification problem behind the ratio's movement. Whether the modality ordering is sensor
physics or construction lineage, which the architecture split hints at and cannot resolve at this
sample size. No statistical uncertainty, resampling band or sampling model is computed anywhere in
this document. No vendor architecture is measured, no deployed system is evaluated, and no safety
conclusion about any vehicle follows.

## Reproduce

```sh
python3 -B tools/measure/excess_joint_risk.py
python3 -B -m unittest discover -s tools/measure -p 'test_excess_joint_risk.py'
```

Sixteen tests, exact rational arithmetic, standard library only. The retained counts carry the
digests of the source caches, held read only by the Gate B lane, and contain no raw record, score or
annotation token.

## Non-claims

An internal research artifact, retained as `proposed`. Not independent external scientific review,
not an operator acceptance, not a safety, compliance or vendor claim.
