# Result T: the independence assumption beyond driving - LLM juries fail together

Document ID: `reiyah.result-t-llm-independence`

Version: `0.1.0`

Lifecycle status: `proposed`

## The estimand is not about cars

The whole program measured whether redundant channels fail independently, the assumption every
safety and ensemble argument leans on. The coefficient of RSS Definition 32 is not specific to
sensors; it applies to any two channels a system calls independent. The largest unmeasured such
assumption in AI today is the LLM jury: self-consistency, majority vote, and multi-model
cross-checking all assume the models err independently, so aggregating cuts the error. This tests
that, with the identical method used for the sensors, public per-item predictions and the
Definition 32 coefficient.

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
| **effective number of independent models** | **3.60** (you convene 7, you get 3.6) |

## What it says

1. **LLM juries fail together.** Every one of the 21 model pairs has `c > 1`; the models get the
   same questions wrong more than independence predicts. A jury is not the sum of independent
   opinions it is treated as.

2. **The same-kind versus cross-kind law replicates.** (Narrowed on 2026-09-06 by Result AC: the
   same-family excess beyond shared difficulty is 0.058 [0.050, 0.066] on MMLU and includes zero on
   ARC-Challenge and HellaSwag; the marginal excess holds on all three.) Models of one lineage (three
   Llama sizes) fail together more than models of different lineages (1.522 versus 1.290), exactly as two
   same-modality sensors fail together more than a camera and a lidar. Similar systems share their
   blind spots; genuinely different systems are more independent. The same law, in a different
   domain.

3. **The coupling survives conditioning.** Conditioned on question difficulty measured by the other
   models (leave the pair out), the coefficient falls but stays above 1 (1.097), just as the
   camera-lidar coefficient stayed above 1 after conditioning on scene difficulty. Part of the raw
   coupling is shared difficulty; part is not.

4. **A seven-model jury has the diversity of 3.6.** The observed rate at which all seven models
   miss the same question is 14 times what independence predicts, and the effective number of
   independent models is 3.60. Half the votes you convened are, in effect, echoes.

## The unification

Placed beside the rest of the program, one law now spans three domains:

| domain | same-kind pairing | cross-kind pairing |
|---|---|---|
| sensors | two lidars, c = 1.29 | camera x lidar, c = 1.10 to 1.15; human x machine, c ~ 1 |
| the human | eyes x hands, c = 1.46 | (n/a) |
| LLM juries | same family, c = 1.52 | cross family, c = 1.29 |

**Redundancy across genuinely different kinds buys independence; redundancy across similar kinds
does not.** The independence assumption is a load-bearing fiction wherever redundancy is claimed,
and it fails most for the systems that share the most. This is the general statement the driving
measurements were a special case of.

## Consequence for practice

Result S showed required validation evidence scales as `sqrt(c)` per credited independent channel.
For an ensemble the analogue is the effective model count: a jury credited as `N` independent votes
provides `n_eff` here, 3.6 of 7. Any argument that convenes multiple LLMs to cross-check a
safety-relevant judgment, and credits their agreement as independent confirmation, is over-crediting
by the same factor, and by more when the models share a lineage.

## Adversarial reading, 2026-09-06

A context-free reader (model-assisted, advisory, same model family as the author) read this document against its transcript alone. The points below are the ones that changed a sentence; the full record is `evidence/review-model-assisted-2026-09-06.json`.

1. The conditional coefficient's per-pair range is [0.971, 1.358]: not every pair exceeds 1 after
   difficulty conditioning, only the mean does. The sentence "the coupling survives conditioning"
   is a statement about the mean.
2. Difficulty is estimated from the other five models' errors, so the residual is measured against
   a proxy built from the same coupled jury; a finer, independent difficulty measure could move it.
3. "Half the votes you convened are, in effect, echoes" is a reading of the effective-model count,
   which is a summary statistic of the all-wrong rate, not a count of redundant models.

## Non-claims

Public leaderboard per-question correctness on one benchmark (MMLU 5-shot), retained as `proposed`.
The marginal coefficient includes shared question difficulty; the conditional coefficient removes
the measurable part of it. Descriptive, not a causal claim, not a safety determination, and a
generalization demonstration of the estimand, not a driving result. No released `1.2` byte is
involved.
