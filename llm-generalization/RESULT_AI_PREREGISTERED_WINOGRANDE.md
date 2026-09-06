# Result AI: the preregistered test, eight predictions, eight supported

Document ID: `reiyah.result-ai-preregistered-winogrande`

Version: `0.1.0`

Lifecycle status: `proposed`; the predictions were `preregistered` before the run

## What was predicted, and what the bytes say

[`PREREGISTRATION_AI_WINOGRANDE_2026-09-06.md`](../docs/preregistrations/PREREGISTRATION_AI_WINOGRANDE_2026-09-06.md)
was committed before any run on Winogrande (the archived leaderboard's 5-shot, two-choice
commonsense task), with eight falsifiable predictions and the two-choice case named in advance as
the hardest for the family predictions. Seven models, 1,267 questions answered by all, gold checked
against every file's own correctness flag on every row.

| id | prediction | transcript | verdict |
|---|---|---|---|
| AI-1 | marginal `c` above 1 for every joining pair | minimum over 21 pairs 2.260, maximum 3.132 | supported |
| AI-2 | same-family marginal above cross-family | 2.809 against 2.500 | supported |
| AI-3 | mean conditional `c` above 1 | 1.134 (per-pair minimum 1.004) | supported |
| AI-4 | effective independent models below half the jury | 2.06 of 7 | supported |
| AI-5 | P(all wrong) above five times the independent rate | 1,210 times | supported |
| AI-6 | P(correct given two agree) below 90 percent | 81.8 percent | supported |
| AI-7 | unanimous-yet-wrong above 5 percent | 9.8 percent of 54.9 percent unanimous | supported |
| AI-8 | conditional same-minus-cross margin smaller than marginal margin | 0.066 against 0.309 | supported |

## What it says

1. **The law predicted a benchmark it had never seen.** Every direction held, on a two-choice task
   where chance agreement is high and where AI-2 and AI-8 were named as the hardest cases. This is
   the first time the program's law has been used to forecast rather than to summarize, and the
   forecast was right on all eight counts.

2. **The quantities are extreme here.** Seven models agree unanimously on 55 percent of questions,
   are wrong on 10 percent of those, and fail all together 1,210 times more often than independence
   predicts, so the jury has the effective diversity of two. On a two-choice task the marginal
   coefficient is bounded above by the reciprocal of the smaller error rate, which is why it sits
   near 2.5 for every pair; the conditional residual, 1.13, is the informative number and it
   exceeds MMLU's.

3. **The honest limit stands.** The preregistration recorded that the program has no model that
   yields a numerical forecast beyond thresholds; the test is directional. It also required four
   procedural deviations before the run, each committed before the corresponding rerun and each
   about the archive's heterogeneous file formats, not about the predictions. Those are findings
   about the archive and the tool, and they are recorded in the preregistration.

## Non-claims

Public leaderboard outputs on a fourth benchmark, retained as `proposed`. Same estimand; the
marginal coefficient includes shared question difficulty and, on a two-choice task, is bounded
above by the error rates. No band is reported here; the intervals machinery of Result AC could be
applied and was not part of the preregistration. Descriptive, not a causal claim, not a safety
determination, not a driving result. Transcript `evidence/result_ai_winogrande.txt` re-runs
byte-identically (two runs). No LLM is executed. No released `1.2` byte is involved.
