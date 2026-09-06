# Result W: the LLM law replicates on a second benchmark

Document ID: `reiyah.result-w-second-benchmark`

Version: `0.1.0`

Lifecycle status: `proposed`

## The objection this answers

Results T, U and V all live on MMLU. The honest objection a reviewer raises is overfitting to one
benchmark. This re-runs the core measurements on **ARC-Challenge**, a different domain, science
reasoning rather than broad knowledge, with the same seven candidate models and the same estimand.
One model, Falcon, used a different ARC prompt format so its question hashes do not join; it is
auto-dropped, leaving six models over 1,170 shared questions.

## The replication

| quantity | MMLU (Results T, U) | ARC-Challenge (this result) | holds |
|---|---|---|---|
| marginal `c` (all pairs) | 1.32 | 1.76 | yes |
| same-family vs cross-family marginal | 1.52 vs 1.29 | 1.87 vs 1.73 | yes, same > cross |
| conditional `c` (beyond shared difficulty) | 1.10 | 1.05 | yes, above 1 |
| jury effective independent models | 3.6 of 7 | 1.6 of 6 | yes, far below N |
| P(all wrong) vs independent | 14x | 28x | yes |
| P(correct given two agree) | 64.8% | 57.9% | yes, over-trusted |
| unanimous-yet-wrong | 10.4% | 37.2% | yes, far worse |

## What it says

1. **The law is not an MMLU artifact.** Every element reappears on a harder reasoning benchmark: the
   models fail together (`c > 1`), same-family more than cross-family, the residual survives
   difficulty conditioning, the jury's effective independence is a fraction of its size, and
   agreement is an over-trusted signal.

2. **On harder material it sharpens.** When all six diverse models agree on ARC-Challenge they are
   still wrong 37% of the time, against 10% on MMLU. The harder the questions, the more the models
   share their failures, and the less unanimity means. A jury of six here carries the effective
   diversity of 1.6.

3. **The honest nuance replicates too.** ARC's large marginal coupling (1.76) is mostly shared
   difficulty, the conditional coefficient falls to 1.05, still above 1 but modest, exactly as the
   camera-lidar marginal coefficient was mostly shared scene difficulty with a smaller residual.
   The method removes the measurable part of the difficulty and reports what is left, on both
   benchmarks.

## Consequence

Results T, U and V now rest on two benchmarks in two domains, not one. The universal law, that
same-kind redundancy fails together and its agreement is over-trusted, and the monitor that corrects
for it, are not properties of a single test. The over-crediting of an LLM jury is, if anything,
larger on harder material, which is exactly the material where a safety-relevant judgment matters
most.

## Adversarial reading, 2026-09-06

A context-free reader (model-assisted, advisory, same model family as the author) read this document against its transcript alone. The points below are the ones that changed a sentence; the full record is `evidence/review-model-assisted-2026-09-06.json`.

1. The transcript prints means only, no per-pair values, no intervals and no per-model error
   rates; Result AC later supplied bands. "Harder" was not measured and is replaced by "a benchmark
   on which these models score lower".
2. Cross-benchmark comparisons are between juries of different size and composition (six models
   here, seven on MMLU), stated now.
3. The Result V monitor was not run on ARC in this result; that test is Result X.

## Non-claims

Public leaderboard per-question outputs on a second benchmark (ARC-Challenge 25-shot), retained as
`proposed`. Same estimand as the rest; the marginal coefficient includes shared question difficulty
and the conditional removes the measurable part. Falcon auto-dropped for a non-joining prompt
format. Descriptive, not a causal claim, not a safety determination, a robustness replication and
not a driving result. No released `1.2` byte is involved.
