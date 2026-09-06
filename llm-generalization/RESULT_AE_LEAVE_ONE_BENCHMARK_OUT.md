# Result AE: calibrating on two benchmarks does not transfer to a third, and can be worse than chance

Document ID: `reiyah.result-ae-leave-one-benchmark-out`

Version: `0.1.0`

Lifecycle status: `proposed`

## The last transfer question

Results X and X2 established that the monitor transfers across juries on one task, fails across
tasks, and that no label-free rescaling repairs it. The remaining deployment question was whether
calibrating on diverse tasks buys transfer to an unseen task. This fits the monitor on jury A's
items from two benchmarks and reads the third, for each held-out choice, on jury A and on the
unseen jury B, against the naive baseline, the single-benchmark reference (fitted on MMLU only),
and the in-domain ceiling on the held-out benchmark.

## The result

| held-out benchmark, jury | naive AUC | fitted on the other two: AUC / ECE | fitted on MMLU only: AUC / ECE | in-domain ceiling AUC / ECE |
|---|---|---|---|---|
| MMLU, jury A | 0.719 | 0.742 / 0.348 | (in-sample, not a test) | 0.851 / 0.019 |
| MMLU, jury B | 0.683 | 0.686 / 0.367 | 0.853 / 0.032 (Result X) | 0.856 / 0.015 |
| ARC, jury A | 0.618 | 0.598 / 0.052 | 0.575 / 0.184 | 0.665 / 0.054 |
| ARC, jury B | 0.583 | 0.593 / 0.108 | 0.610 / 0.213 | 0.623 / 0.068 |
| HellaSwag, jury A | 0.593 | **0.386** / 0.412 | **0.367** / 0.373 | 0.708 / 0.017 |
| HellaSwag, jury B | 0.507 | 0.510 / 0.377 | 0.502 / 0.332 | 0.720 / 0.010 |

## What it says

1. **Diversity of calibration does not buy task transfer.** Reading MMLU after fitting on ARC and
   HellaSwag gives an AUC of 0.74 on jury A and 0.69 on jury B, against 0.85 in domain, with
   calibration errors above 0.3; reading ARC after fitting on MMLU and HellaSwag lands at the naive
   baseline. The two-benchmark fit improves calibration on ARC (ECE 0.052 and 0.108 against 0.184 and
   0.213 for the MMLU-only fit) and does not restore discrimination anywhere (corrected 2026-09-06).

2. **On HellaSwag the transferred monitor is worse than chance.** Fitted on either MMLU alone or on
   MMLU and ARC, it reads jury A on HellaSwag at an AUC of 0.37 to 0.39: the relation between the
   output features and joint failure inverts on that task, so the monitor confidently assigns low
   risk to the items the jury gets wrong. A monitor deployed across tasks without task calibration
   is not merely uninformative there; it is misleading. The in-domain ceiling on HellaSwag is 0.71,
   so the signal exists and is task-specific.

3. **The deployment statement is now complete and closed.** Fit per task, read across channels.
   Three independent attempts to escape task calibration (raw transfer, label-free rescaling,
   multi-task calibration) failed, one of them into anti-correlation. That is the boundary of the
   instrument, and it is recorded as firmly as the instrument's successes.

## Adversarial reading, 2026-09-06

A context-free reader (model-assisted, advisory, same model family as the author) read this document against its transcript alone. The points below are the ones that changed a sentence; the full record is `evidence/review-model-assisted-2026-09-06.json`.

1. "Not better than the one-benchmark fit anywhere that is a fair comparison" is contradicted by
   the transcript on calibration: on ARC the two-benchmark fit's ECE (0.052 and 0.108) is far
   better than the MMLU-only fit's (0.184 and 0.213) and matches the in-domain ceiling, and its AUC
   is higher in three of four fair comparisons. Corrected: multi-task calibration improves
   calibration on ARC and does not restore discrimination anywhere.
2. The below-chance result is jury A on HellaSwag; jury B on HellaSwag is at chance (0.510). Stated.

## Non-claims

Public leaderboard outputs, retained as `proposed`. Three benchmarks, two juries; jury sizes differ
by benchmark under the non-joining rule, and the features are size-normalized only where they can
be. Not a deployed product, not a safety determination, not a driving result. Transcript
`evidence/result_ae.txt` re-runs byte-identically (two runs). No released `1.2` byte is involved.
