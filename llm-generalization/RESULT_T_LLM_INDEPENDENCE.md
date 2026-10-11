# Result T: the independence assumption beyond driving - LLM juries fail together

Document ID: `reiyah.result-t-llm-independence`

Version: `0.2.0`

Lifecycle status: `corrected`

## Interpretation correction, 2026-10-10

The [dated correction](../research/claim-correction/0.1.0/README.md) governs this result. Original
transcripts and numerical measurements are preserved. These results describe
the selected models and benchmarks. A universal independence law, an identified
count of independent models and a safety-evidence credit are not established.

## Archived-output measurement

This study computes coincident-wrong ratios from archived model answers.
Independence is one comparison model, not a premise required by every voting
or self-consistency method. Sharing a ratio with a sensor study does not
identify the same latent event or transport a safety guarantee.

Data: the public v1 Open LLM Leaderboard per-question results, MMLU 5-shot, per-question
correctness. Seven models across five families, joined on 13,937 questions by a hash of the
example. `wrong_m(q)` is model `m` answering `q` incorrectly, and
`c(i,j) = P(both wrong) / [ P(i wrong) * P(j wrong) ]`.

## The result

| finding | value |
|---|---|
| marginal `c`, all 21 model pairs | mean **1.323**, range [1.019, 1.967], every pair above 1 |
| same-family pairs (3 Llama sizes) | mean marginal `c` = **1.522** |
| cross-family pairs (18) | mean marginal `c` = **1.290** |
| conditional `c` (beyond shared question difficulty) | mean **1.097**, range [0.971, 1.358] |
| same-family conditional `c` | 1.148 |
| cross-family conditional `c` | 1.088 |
| 7-model jury, P(all wrong) observed | **8.31%** |
| 7-model jury, P(all wrong) if independent | 0.59% |
| inflation over independence | **14x** |
| **homogeneous-equivalent model-count summary** | **3.60** (not an identified count of independent models) |

## What it says

1. **LLM juries fail together.** Every one of the 21 model pairs has `c > 1`; the models get the
   same questions wrong more than independence predicts. This describes these selected
   models and questions; it does not determine every ensemble method's assumptions.

2. **The selected same-family contrast is benchmark-specific.** (Narrowed on 2026-09-06 by Result AC: the
   same-family excess beyond shared difficulty is 0.058 [0.050, 0.066] on MMLU and includes zero on
   ARC-Challenge and HellaSwag; the marginal excess holds on all three.) The three
   Llama size pairs have a larger marginal mean than the selected cross-family pairs
   (1.522 versus 1.290). This is one lineage, not a causal intervention on lineage
   or a general ordering across sensors, humans and language models.

3. **The coupling survives conditioning.** Conditioned on question difficulty measured by the other
   models (leave the pair out), the coefficient falls but stays above 1 (1.097), just as the
   camera-lidar coefficient stayed above 1 after conditioning on scene difficulty. The residual is relative to a difficulty proxy;
   unmeasured difficulty and other explanations remain possible.

4. **The homogeneous-equivalent summary is 3.6.** The observed rate at which all seven models
   miss the same question is 14 times what independence predicts, and the effective number of
   independent models is 3.60. This is an arithmetic summary, not an identified number of independent votes.

## The unification

The older cross-domain table is retained for traceability. Different event
definitions, marginals and populations prevent treating it as a universal law:

| domain | same-kind pairing | cross-kind pairing |
|---|---|---|
| sensors | two lidars, c = 1.29 | camera x lidar, c = 1.10 to 1.15; human x machine, c ~ 1 |
| the human | eyes x hands, c = 1.46 | (n/a) |
| LLM juries | same family, c = 1.52 | cross family, c = 1.29 |

The former universal same-kind/cross-kind law is withdrawn. These descriptive
contrasts do not establish independent failure from architectural difference.

## Consequence for practice

Result S's applied evidence-cost interpretation was withdrawn. The jury
coefficient and homogeneous-equivalent summary supply no safety-validation
multiplier or redundancy credit. Evaluate actual ensemble decisions against
calibrated baselines on the intended task and keep transfer failures visible.

## Adversarial reading, 2026-09-06

A context-free reader (model-assisted, advisory, same model family as the author) read this document against its transcript alone. The points below are the ones that changed a sentence; the full record is `evidence/review-model-assisted-2026-09-06.json`.

1. The conditional coefficient's per-pair range is [0.971, 1.358]: not every pair exceeds 1 after
   difficulty conditioning, only the mean does. The sentence "the coupling survives conditioning"
   is a statement about the mean.
2. Difficulty is estimated from the other five models' errors, so the residual is measured against
   a proxy built from the same coupled jury. Answered the same evening by Result AL: with difficulty
   measured by an independent seven-family jury the residual is 1.094 [1.088, 1.098] and the
   same-family excess 0.098 [0.089, 0.108].
3. "Half the votes you convened are, in effect, echoes" is a reading of the effective-model count,
   which is a summary statistic of the all-wrong rate, not a count of redundant models.

## Non-claims

Public leaderboard per-question correctness on one benchmark (MMLU 5-shot), retained as `proposed`.
The marginal coefficient includes shared question difficulty; the conditional coefficient removes
the measurable part of it. Descriptive, not a causal claim, not a safety determination, and a
generalization demonstration of the estimand, not a driving result. No released `1.2` byte is
involved.
