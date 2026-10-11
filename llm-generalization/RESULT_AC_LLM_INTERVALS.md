# Result AC: intervals for every LLM-jury coefficient, and the lineage effect narrows to one benchmark

Document ID: `reiyah.result-ac-llm-intervals`

Version: `0.2.0`

Lifecycle status: `corrected`; descriptive measurements retained

## Interpretation correction, 2026-10-10

The [dated correction](../research/claim-correction/0.1.0/README.md) governs this result. Original
transcripts and numerical measurements are preserved. These results describe
the selected models and benchmarks. A universal independence law, an identified
count of independent models and a safety-evidence credit are not established.

## Why

Results T, U, W and Y report point estimates. The program's rule for the sensors is never to quote a
coefficient without its band. This puts a question-resampled percentile bootstrap (B = 1000,
seeded) on every headline LLM quantity on all three benchmarks, with the definitions of Results T
and U unchanged. The unit of resampling is the question, the unit of the join.

## The intervals

| quantity | MMLU (7 models, 13,937) | ARC-Challenge (6 models, 1,170) | HellaSwag (7 models, 10,019) |
|---|---|---|---|
| marginal `c`, mean | 1.323 [1.313, 1.334] | 1.761 [1.689, 1.844] | 2.319 [2.270, 2.369] |
| conditional `c`, mean | 1.098 [1.096, 1.101] | 1.057 [1.050, 1.064] | 1.028 [1.026, 1.030] |
| same minus cross, marginal | 0.232 [0.217, 0.247] | 0.142 [0.095, 0.188] | 0.126 [0.111, 0.142] |
| **same minus cross, conditional** | **0.058 [0.050, 0.066]** | **0.007 [-0.008, 0.021]** | **-0.001 [-0.004, 0.002]** |
| P(all wrong) / independent | 14.2 [13.3, 15.1] | 27.8 [22.0, 36.1] | 209.6 [183.7, 239.7] |
| effective independent models | 3.60 [3.53, 3.68] | 1.64 [1.57, 1.71] | 1.28 [1.27, 1.30] |
| P(correct given two agree) | 0.648 [0.640, 0.655] | 0.579 [0.550, 0.609] | 0.625 [0.616, 0.635] |
| unanimous share | 0.055 [0.052, 0.059] | 0.519 [0.491, 0.547] | 0.793 [0.785, 0.801] |
| unanimous-yet-wrong | 0.104 [0.081, 0.124] | 0.372 [0.335, 0.409] | 0.340 [0.330, 0.351] |

## What it says

1. **Every marginal statement holds with a band that excludes independence and excludes zero
   difference.** Coupling far above 1, agreement over-trusted, a jury with a fraction of its nominal
   diversity, and same-family marginal coupling above cross-family, on all three benchmarks, with
   intervals that never touch the null.

2. **The lineage effect beyond shared difficulty holds on one benchmark and not on two.** The
   conditional same-minus-cross margin is 0.058 [0.050, 0.066] on MMLU, 0.007 [-0.008, 0.021] on
   ARC-Challenge, and -0.001 [-0.004, 0.002] on HellaSwag. Result T's statement that "models of one
   lineage fail together more than models of different lineages, beyond shared difficulty" is
   therefore narrowed: it is supported on MMLU and not established on the other two, where the
   estimated interval does not establish a nonzero contrast after the stated adjustment. The marginal version of the statement stands on
   all three.

3. **The conditional residual itself is above 1 on every benchmark, with tight bands.** 1.098,
   1.057 and 1.028, none of whose intervals reach 1. These are residuals relative to a measured difficulty proxy,
   not identification of a cause; unmeasured difficulty remains possible.

## Bounded interpretation

The selected models have excess marginal error coincidence on these benchmarks.
The conditional same-family contrast is established under the stated resampling
procedure on MMLU and not established on the other two. No universal law,
lineage causality or physical-safety consequence follows. Agreement accuracy
is descriptive; no independence null for agreement reliability was computed.

## Adversarial reading, 2026-09-06

A context-free reader (model-assisted, advisory, same model family as the author) read this document against its transcript alone. The points below are the ones that changed a sentence; the full record is `evidence/review-model-assisted-2026-09-06.json`.

1. The same-family contrast is three Llama-2 size pairs against eighteen cross pairs: one lineage.
   Nothing here supports a statement about lineage as a variable; the finding is about the Llama-2
   family on MMLU. Stated now.
2. An ARC interval of [-0.008, 0.021] means not established, which is what the register records;
   "the whole excess is shared difficulty" is too strong and is withdrawn as a sentence.
3. No independence null for agreement reliability is computed; its band describes sampling
   variation, not distance from a null.

## Non-claims

Public leaderboard outputs, retained as `proposed`. Intervals are question-resampled percentile
bootstraps and describe sampling variation over questions only; they do not cover model selection,
prompt format, or benchmark choice, and questions are not clustered by subject. Descriptive, not a
causal claim, not a safety determination, not a driving result. Transcript `evidence/result_ac.txt`
re-runs byte-identically (three runs). No LLM is executed. No released `1.2` byte is involved.
