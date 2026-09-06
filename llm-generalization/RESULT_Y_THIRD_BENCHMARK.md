# Result Y: the LLM law on a third benchmark, and where the residual almost vanishes

Document ID: `reiyah.result-y-third-benchmark`

Version: `0.1.0`

Lifecycle status: `proposed`

## The objection this answers

Results T, U and W rest on MMLU and ARC-Challenge, two multiple-choice benchmarks. A third,
HellaSwag (the leaderboard's 10-shot commonsense completion task, four choices), tests whether the
law is a property of question-answering benchmarks or of the models. Same seven models, same
estimand, same join rule, 10,019 questions answered by all seven.

## The replication

| quantity | MMLU (T, U) | ARC-Challenge (W) | HellaSwag (this result) |
|---|---|---|---|
| marginal `c` (all pairs) | 1.32 | 1.76 | **2.32** |
| same-family vs cross-family marginal | 1.52 vs 1.29 | 1.87 vs 1.73 | 2.43 vs 2.30 |
| conditional `c` (beyond shared difficulty) | 1.10 | 1.05 | **1.03** |
| same-family vs cross-family conditional | 1.15 vs 1.09 | 1.06 vs 1.05 | 1.04 vs 1.03 |
| P(all wrong) vs independent | 14x | 28x | **210x** |
| jury effective independent models | 3.6 of 7 | 1.6 of 6 | **1.28 of 7** |
| P(correct given two agree) | 64.8% | 57.9% | 62.5% |
| unanimous share of questions | 5.5% | 51.9% | 79.3% |
| unanimous-yet-wrong | 10.4% | 37.2% | 34.0% |

## What it says, both halves

1. **Every direction of the law reappears a third time.** Marginal `c` is above 1 for every pairing,
   same-family above cross-family, the conditional residual above 1, the jury's effective size a
   fraction of its nominal size, and agreement over-trusted. On HellaSwag a seven-model jury carries
   the effective diversity of 1.28 independent models: the seven models are, for the purpose of
   failing, very nearly one model.

2. **The residual beyond shared difficulty is nearly zero here.** The conditional coefficient is
   1.03, against 1.10 on MMLU and 1.05 on ARC, and the same-family margin in the conditional is
   0.01. On HellaSwag the coupling is almost entirely the questions themselves: the models all fail
   on the same hard items because the items are hard, not because the models share a lineage. The
   method removes the measurable shared difficulty and reports what is left, and here what is left
   is small. That is the honest reading and it is stated as the headline of the residual, not
   buried.

3. **The consequence for juries is unchanged and larger.** Whether the coupling is lineage or
   difficulty does not matter to a jury: unanimity on HellaSwag occurs on 79 percent of questions
   and is wrong on 34 percent of those. Agreement is over-trusted for either reason, and the
   over-trust grows with the share of unanimous items.

## Consequence

The law now rests on three benchmarks in three task families. The marginal statement (redundant
LLM channels fail together, far beyond independence, and their agreement is over-trusted) is robust
across all three. The mechanism statement (same-lineage models share blind spots beyond shared
difficulty) is supported on MMLU, modest on ARC, and near the floor on HellaSwag; it is therefore
stated as benchmark-dependent and not as universal.

## Non-claims

Public leaderboard per-question outputs on a third benchmark, retained as `proposed`. Same estimand;
the marginal coefficient includes shared question difficulty and the conditional removes the
measurable part. Descriptive, not a causal claim, not a safety determination, a robustness
replication and not a driving result. Transcript `evidence/result_y_hellaswag.txt` re-runs
byte-identically. No LLM is executed. No released `1.2` byte is involved.
