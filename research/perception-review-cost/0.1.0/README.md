# An addition count does not bound the observations needed to assess it

Document ID: `reiyah.perception-review-cost.guide`

Version: `0.1.0` · Status: `exploratory` · Evidence: synthetic

**Question:** Does one retained addition imply that one object judgment can settle its value?
**Result:** No. In the construction below, even with the candidate-associated object already
confirmed, two disputed objects require two exact presence queries in the worst case.

This is a consequence of conventional maximum matching, not a new detector result. It extends
the public [matching-competition example](../../perception-decision-review/0.1.0/README.md) to
make the observation-cost assumption inspectable before a human review is budgeted.

## Fixed comparison and permitted observations

Preserve a base detection at x=0 and add one detection at x=3. The known same-class object A is
at x=1.5. Two disputed same-class objects, B0 at x=-1 and B1 at x=-0.5, may independently be
present or absent. Eligibility is strict distance below 2. The addition survives suppression
against the base. Only the base can match B0 or B1; both detections can match A.

Every admitted interpretation has exactly the same evidence about the addition and A. An
allowed query reveals the existence of exactly one disputed object. Geometry, class, source
coverage and the existence of A are fixed assumptions. A query has unit cost and is error-free.
This is a deliberately specified mathematical query model, not a claim that human review
works this way or that a frame inspection reveals only one fact.

With unit false-negative and false-positive penalties, the paired loss is
`delta = loss_base - loss_augmented = 2 * matching_gain - 1`:

| B0 present | B1 present | base TP | augmented TP | base loss | augmented loss | delta |
|---|---|---:|---:|---:|---:|---:|
| no | no | 1 | 1 | 0 | 1 | -1 |
| no | yes | 1 | 2 | 1 | 0 | +1 |
| yes | no | 1 | 2 | 1 | 0 | +1 |
| yes | yes | 1 | 2 | 2 | 1 | +1 |

A positive answer to either query settles the preference. If the first answer is negative,
the second object can still reverse it. The worst case therefore needs two queries, although
there is only one addition and no competition between added detections. Confirming A alone
does not help: it was already present in every admitted interpretation.

For N such disputed neighbors, the all-absent interpretation requires N presence queries in
this model. Before every disputed object has been queried, an unqueried one could exist and
reverse the preference. Querying all N also suffices, so the minimum worst-case query count is
exactly N. This proof concerns the specified observation interface, not a universal human-cost
law. A richer observation could resolve several alternatives at once; incomplete discovery or
uncertain identity could leave more work.

The bound `0 <= matching_gain <= retained_additions` bounds the value of a count. It does not
bound the evidence or effort required to identify that count. Treating each addition as an
independent conversion trial needs a separate justification that this example does not satisfy.

## The cohort decision must remain the same decision

The Engine's two exposed development anchors retain 9 and 7 additions, with common weights
1/2. For unit penalties and tolerance 1/10, the declared weighted difference is
`delta = gain_1 + gain_2 - 8`. Improvement is supported for fully specified integer gains
exactly when their sum is at least 9. With uncertain references, this must hold for every
admitted joint interpretation; it is not enough that one possible interpretation reaches 9.

Separate per-anchor preference decisions are a different target. Gains 7 and 2 give respective
differences +5 and -3, yet their weighted difference is +1. A per-anchor stopping race cannot
silently replace the cohort criterion. No actual gain, reference judgment, independence
assumption, transferable prior or probability of a review outcome is supplied by this arithmetic.

## Reproduce and challenge

```sh
python3 -B research/perception-review-cost/0.1.0/reproduce.py
```

Compare stdout with [expected.json](expected.json). The standard-library calculation imports
no Engine code. It enumerates partial injective assignments to calculate the losses directly,
then minimizes worst-case depth over all allowed adaptive binary query trees for N=1,2,4,8.
It also checks the weighted criterion over all 80 possible integer gain pairs. The two-object
[Engine input](two-disputed-objects.json) is checked separately by the current producer and
its matching/vertex-cover certificate checker; see [verification](verification.json).

The strongest useful challenge is to the observation model: what can one real reviewer
observation resolve, and which alternatives remain afterward? Record that answer and total
preparation, discovery, correction and adjudication effort during an actual staged review.
Do not promote an assumed Bernoulli race to a physical-review cost prediction.

These checks establish a finite computational counterexample. No physical review or external
scientific review has occurred. The real open-reference comparison remains [-8,8]; the
60-scene study remains unselected and unrun. This example changes no frozen review protocol
and does not supply a numerical human budget.
