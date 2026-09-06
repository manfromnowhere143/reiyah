# Result U: agreement is not confidence - predicting joint failure from outputs alone

Document ID: `reiyah.result-u-agreement-reliability`

Version: `0.1.0`

Lifecycle status: `proposed`

## From measuring joint failure to reading it live

Everything before this measured joint failure against ground truth, after the fact. The step toward
an instrument is to read the risk from the channels' own outputs, with no ground truth. An ensemble
already does this implicitly: it treats agreement between models as confidence, and unanimity as
near-certainty. Result T showed the models are coupled, so they agree on the same wrong answers too.
This measures how much that degrades agreement as a signal, which is exactly what a live monitor
would read.

Data: public v1 Open LLM Leaderboard, MMLU 5-shot, seven models, 13,937 questions. Each model's
chosen answer is the argmax of its per-choice log-probabilities; agreement is choosing the same
answer.

## The result

**When two models agree on an answer:**

| pair | P(agree) | P(correct given agree) | P(both wrong given agree) |
|---|---|---|---|
| Llama-2-7b + Llama-2-13b | 55% | 65.0% | 35.0% |
| Llama-2-7b + Llama-2-70b | 50% | 77.1% | 22.9% |
| Llama-2-7b + Mistral-7B | 53% | 71.5% | 28.5% |
| Llama-2-7b + Falcon-7b | 32% | 46.5% | 53.5% |
| Llama-2-13b + Llama-2-70b | 63% | 76.6% | 23.4% |
| **average over 21 pairs** | | **64.8%** | **35.2%** |

**The full seven-model jury:**

| quantity | value |
|---|---|
| questions where all seven chose the same answer (unanimous) | 5.5% |
| of those, **unanimous and wrong** | **10.4%** (80 questions) |

## What it says

1. **Agreement is only about 65% reliable.** When two models choose the same answer, they are wrong
   together more than a third of the time. An ensemble that reads agreement as confidence is reading
   a signal that is right two times in three, not the near-certainty it is treated as.

2. **Unanimity is not certainty.** When all seven diverse models agree, they are still wrong one time
   in ten. Coupled models share the same misconceptions, so they concentrate on the same wrong
   answer, and the ensemble has no way to tell a confident-correct consensus from a confident-wrong
   one from the outputs alone, unless it accounts for the coupling.

3. **Agreement is a runtime signal.** Agreement and unanimity are read from the models' outputs;
   their reliability, the quantities above, needs the gold labels and is measured here after the
   fact (corrected 2026-09-06). A live monitor that knows the measured coupling can correct the confidence it reads
   from agreement, downweighting consensus among coupled channels. That is the seed of the instrument
   the whole program points toward: not measuring joint failure after the fact, but estimating it as
   it happens.

## The link to the safety calculus

Result S corrected required validation evidence by `sqrt(c)` per independent channel, and Result T
showed a seven-model jury has the effective diversity of 3.6. This closes the loop at runtime: the
over-crediting is not only in the offline evidence budget, it is in every live decision that trusts
agreement, and it is the same coupling in both places.

## Adversarial reading, 2026-09-06

A context-free reader (model-assisted, advisory, same model family as the author) read this document against its transcript alone. The points below are the ones that changed a sentence; the full record is `evidence/review-model-assisted-2026-09-06.json`.

1. P(correct given agreement) and the unanimous-yet-wrong rate are computed against gold labels;
   agreement itself is read from outputs, its reliability is not. The phrase "from outputs alone"
   applies to the signal, not to its measured reliability. Corrected below.
2. No independence baseline for agreement reliability is computed here; the transcript's own
   baseline for shared wrong answers is a uniform approximation. "Over-trusted" therefore means
   lower than 1 by a measured amount, not lower than what independence would predict; that
   comparison is not made in this result.

## Non-claims

Public leaderboard outputs on one benchmark (MMLU 5-shot), retained as `proposed`. Agreement is the
argmax choice; the unanimous-and-wrong rate is for these specific seven models on this benchmark;
descriptive, not a causal claim, not a safety determination, and a runtime-signal demonstration, not
a deployed monitor and not a driving result. No released `1.2` byte is involved.
