# Result AL: the conditional coefficient with difficulty measured by an independent jury

Document ID: `reiyah.result-al-cross-jury-difficulty`

Version: `0.1.0`

Lifecycle status: `proposed`

## The objection this answers

Result T conditions each pair on question difficulty measured by the other models of the same
jury. The adversarial reading's strongest objection was that this proxy is built from the same
coupled jury, so the residual might be an artifact of the proxy's provenance. This measures
difficulty with the other jury: for every jury A pair, difficulty is the fraction of the seven
jury B models (seven other families, none in jury A) that answer the question wrong, in five
quantiles; and the reverse for jury B pairs. MMLU, 13,937 questions answered by both juries,
question-resampled bands (B = 500).

## The result

| quantity | jury A pairs | jury B pairs |
|---|---|---|
| conditional `c`, same-jury difficulty (Result T definition), mean | 1.098 [1.096, 1.101] | 1.089 [1.087, 1.092] |
| **conditional `c`, other-jury difficulty, mean** | **1.094 [1.088, 1.098]** | **1.016 [1.014, 1.019]** |
| other-jury difficulty, per-pair range | 0.941 to 1.356 | 0.936 to 1.149 |
| other-jury difficulty, same-family (three Llama pairs) | 1.178 [1.167, 1.189] | (no same-family pairs) |
| other-jury difficulty, cross-family | 1.080 [1.075, 1.084] | |
| other-jury difficulty, same minus cross | **0.098 [0.089, 0.108]** | |

## What it says

1. **Jury A's residual is not an artifact of the proxy.** Conditioned on difficulty measured by
   seven unrelated models, the mean coefficient is 1.094, indistinguishable from the 1.098 the
   same-jury proxy gave, and the same-family excess grows to 0.098 [0.089, 0.108] from 0.058. The
   lineage effect on MMLU is at least as large when difficulty is measured independently.
2. **Jury B's residual almost vanishes.** Seven models from seven different families, conditioned
   on difficulty measured by jury A, have a mean coefficient of 1.016 [1.014, 1.019]: once
   difficulty is measured by an independent jury, unrelated models are close to independent. The
   same-jury proxy had given 1.089 for the same pairs, so for a jury with no shared lineage most of
   the same-jury residual was the proxy.
3. **Read together.** The coupling that survives an independent difficulty measure is concentrated
   in the pairs that share a lineage. That is a cleaner statement of the law's LLM arm than Result
   T could make: same-lineage models fail together beyond difficulty; different-lineage models
   mostly do not. It holds on MMLU with one lineage, as Result AC's adversarial reading requires.
4. **Not every pair.** The per-pair range reaches below 1 in both juries (0.941, 0.936); the
   statements above are about means and about the family contrast.

## Non-claims

Public leaderboard outputs, retained as `proposed`. Difficulty from the other jury is still a
proxy, the fraction of seven other models that err; it is independent of the pair measured but
not of item difficulty as such. MMLU only; one lineage (Llama-2 sizes) supplies every same-family
pair. Transcript `evidence/result_al.txt` re-runs byte-identically (two runs). No LLM is executed.
No released `1.2` byte is involved.
