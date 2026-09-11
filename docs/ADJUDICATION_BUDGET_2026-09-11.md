# What closing the open comparison costs, in human judgements

Document ID: `reiyah.adjudication-budget.2026-09-11`

Version: `0.1.0`

Lifecycle status: `proposed`

Lane: independent research, parallel to the Engine. Changes no released byte, no frozen protocol,
no Engine file and no owner checkout. Creates no acceptance, no reviewer and no scientific
authority. Gate A remains unaccepted and the physical study has not run.

## The question and the result

The retained comparison is open and returns the bound of ignorance. The useful question is not how
wide that is but what closing it costs. **The budget is computable before any judgement is made.**

Review does not have to measure the gain. Under the contract's decision rules the comparison
resolves as soon as the gain is placed on one side of a threshold available in closed form:

```text
supported  iff  g > tau,        tau = (t + b*r) / (a + b)
excluded   iff  g <= tau
```

For the two anchors, with unit penalties and tolerance `1/10`:

| retained additions | `tau` | supported needs | excluded needs | worst case | expected |
|---:|---:|---:|---:|---:|---:|
| 9 | `91/20` | 5 conversions | 5 non-conversions | 9 | 6.83 |
| 7 | `71/20` | 4 conversions | 4 non-conversions | 7 | 5.36 |

Adjudicating everything is 16 judgements. **Stopping early saves nothing in the worst case**, because
for these `r` the two stopping counts sum to `r + 1`. It saves about **3.8 judgements in expectation**,
bringing the expected cost to **12.20**. That is the honest arithmetic and the worst case is reported
first on purpose.

## What the measured conversion rate predicts

Using this lane's own full-split conversion rate of `66/223` at the same score floor as the prior:

| anchor | probability the review returns `improvement supported` |
|---:|---:|
| `r = 9` | **0.0939** |
| `r = 7` | **0.1209** |

So under the measured rate the comparison most likely resolves **against** the addition. That is a
prior and not a property of these anchors, measured on a different population with a different
reference, and it is falsifiable by exactly the review it budgets. Stating it before the review is
the point; it is cheap to be right afterwards.

Sensitivity, because the prediction is only as good as the prior:

| conversion prior | expected judgements | probability supported, per anchor |
|---|---:|---|
| `1/10` | 9.99 | 0.0009, 0.0027 |
| `66/223` measured | 12.20 | 0.0939, 0.1209 |
| `1/2` | 13.35 | 0.5, 0.5 |
| `3/4` | 11.70 | 0.9511, 0.9294 |

The expected cost is highest near `1/2`, which is what a threshold race does: an ambiguous world is
the expensive one to adjudicate. A team that believes its addition is clearly good or clearly bad
should expect to spend less, in both directions.

## The declared model, and where it is an approximation

A reviewer adjudicates **objects**, not detections, and the gain is a maximum matching over the
admitted objects rather than a sum of independent per-addition outcomes. Two retained additions can
still compete for one object, because the rule suppresses an addition near a **base** detection and
not near another addition.

The sequential model here treats each retained addition as one conversion trial. It is exact when no
two retained additions can match the same object, and otherwise it is an **upper bound on the number
of judgements**, since `r` additions cannot produce more than `r` gain. That is stated rather than
buried, and it is the first thing to attack.

## Verification

The threshold is checked against the contract's own decision rule at every gain for `r` up to 20,
and the stopping counts are checked to be the smallest that force each branch. The expected-trial
computation is exact rational dynamic programming and is cross-checked against an independent
40,000-run simulation at three stopping pairs. The supported probability is verified to be a
probability, monotone in the prior, and exactly `1/2` at a fair prior by symmetry.

## What this does not establish

No reviewer exists, none is invented, and nothing here creates one. It is not a review protocol, not
a blinding or independence claim, not a physical reference, and not an assertion that the addition is
good or bad. It is a cost and a prediction attached to a decision that is currently open, both
falsifiable by the same sixteen judgements.

## Reproduce

```sh
python3 -B tools/measure/adjudication_budget.py
python3 -B -m unittest discover -s tools/measure -p test_decision_packet.py
```

No data is read. Exact rational arithmetic, standard library only, well under a second.

## Non-claims

An internal research artifact, retained as `proposed`. Not independent external scientific review,
not an operator acceptance, not a safety, compliance or vendor claim. No released `1.2` byte, frozen
protocol, claim-register entry or other owner's work is modified.
