# Preregistration AI: the LLM jury law on a benchmark not yet examined

Document ID: `reiyah.preregistration-ai-winogrande`

Version: `0.1.0`

Lifecycle status: `preregistered`

Written and committed before the tool was run on the task. The law so far summarizes measurements
on MMLU, ARC-Challenge and HellaSwag. A law that predicts is a different thing. This states, in
advance, what the same seven models and the same estimand will show on Winogrande (the archived
leaderboard's 5-shot, two-choice commonsense task), then the Result Y tool is run on it unchanged.

## Predictions, each falsifiable by the transcript

| id | prediction | falsified if |
|---|---|---|
| AI-1 | marginal `c` exceeds 1 for every model pair that joins | any pair at or below 1 |
| AI-2 | same-family marginal `c` exceeds cross-family marginal `c` | same at or below cross |
| AI-3 | mean conditional `c` exceeds 1 | at or below 1 |
| AI-4 | the jury's effective independent models are fewer than half its size | at or above N/2 |
| AI-5 | P(all wrong) exceeds five times the independent rate | at or below 5x |
| AI-6 | P(correct given two models agree) is below 90 percent | at or above 90 |
| AI-7 | unanimous-yet-wrong exceeds 5 percent of unanimous items | at or below 5 |
| AI-8 | the conditional same-minus-cross margin is smaller than the marginal margin | not smaller |

A two-choice task is stated as the hardest case for AI-2 and AI-8 in advance: with two options,
agreement by chance is high and the family signal is expected to be weak; the predictions are
nonetheless made without softening. No prediction names a number beyond the thresholds above,
because the program has no model that yields one; that absence is recorded as the honest limit of
the law as it stands.

## Procedure

`bdda-venv/bin/python llm-generalization/tools/result_y_third_benchmark.py winogrande`, two runs,
byte identity required, transcript retained as `llm-generalization/evidence/result_ai_winogrande.txt`.
Models that do not join by the Result W rule are dropped and named. The verdict per prediction is
`supported` or `falsified` from the transcript alone, recorded in the result document and the
register, whichever way it falls.

## Deviation, recorded before any result was read

The first run of the unchanged Result Y tool loaded no model: the Winogrande files carry no
`gold` index, only an `answer` string naming the correct option, and the tool's silent skip on a
missing column left the jury empty (the transcript of that failed run is retained in the session
log, not in the repository, since it produced no measurement). The procedure is amended to a copy
of the tool, `result_ai_winogrande.py`, that maps `answer` to a gold index and refuses any model on
which the mapping disagrees with the file's own `acc` flag on any row. No prediction is changed.
This amendment was committed before the amended tool was run.

## Deviation 2, recorded before any result was read

The amended tool joined only three of seven models: the `hashes` field is stored as a string in
the Llama Winogrande runs and is absent in Qwen's 2024-format file. The three-model output is not
the test and is not read as one. The procedure is amended a second time: questions join by the
SHA-256 of the verbatim `example` text, as Result X does for both formats, and gold is taken from
`answer` when `gold` is absent or empty, with the same per-row `acc` check. No prediction is
changed. Committed before the run.

## Deviation 3, recorded before any result was read

The second rerun still joined three models: the run selector took, for each Llama model, a run
whose predictions are stored as text, while a later 5-shot run stores them as numbers; and Qwen's
2024-format file carries no gold at all. The procedure is amended a third time: among each
model's 5-shot Winogrande runs, the latest whose predictions parse as numbers is used, and gold
for gold-less files is recovered at join time from a gold-bearing model on the same question and
checked against every model's own `acc` on every joined row, exactly Result X's rule. No
prediction is changed. Committed before the run. Three procedural deviations before a
preregistered test is a finding about the archive's heterogeneity and about the tool, and is
recorded as such.

## Non-claims

A preregistration, not a result. Public leaderboard outputs; no LLM is executed; no released `1.2`
byte is involved.
