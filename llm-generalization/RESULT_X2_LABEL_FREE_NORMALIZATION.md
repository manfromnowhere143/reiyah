# Result X2: a label-free normalization does not repair task transfer, and it costs channel transfer

Document ID: `reiyah.result-x2-label-free-normalization`

Version: `0.1.0`

Lifecycle status: `proposed`

## The hypothesis Result X named

Result X found the monitor transfers across juries and fails across benchmarks, and named a
suspect: the per-model confidence margins on a 25-shot reasoning task sit on a different scale from
5-shot knowledge questions. If that were the whole story, a normalization that uses only the
target's own unlabeled outputs would repair it. This tests exactly that: each model's margins are
replaced by their within-model empirical quantile on the set being read, with no label used. The
monitor is fitted once on jury A on MMLU with normalized margins and never refitted. Everything
else is imported from the Result X tool unchanged.

## The result

| transfer | Result X, raw margins: AUC / ECE | normalized: AUC / ECE | in-domain ceiling, normalized |
|---|---|---|---|
| X2-1: unseen jury, MMLU | 0.853 / 0.032 | 0.787 / 0.025 | 0.796 / 0.013 |
| X2-4: five of that jury, MMLU | 0.852 / 0.023 | 0.810 / 0.024 | 0.817 / 0.020 |
| X2-2: unseen jury, ARC-Challenge | 0.610 / 0.213 | 0.602 / 0.178 | 0.609 / 0.062 |
| X2-3: jury A, ARC-Challenge | 0.575 / 0.184 | 0.641 / 0.147 | 0.680 / 0.027 |

On the ARC unanimous items the normalized monitor assigns 15 to 16 percent risk where the truth is
37 to 41 percent; its lowest-risk band predicts 2 percent and realizes 33 to 38 percent.

## What it says

1. **The task failure is not a scale problem.** Normalizing the margins leaves the ARC transfers at
   or near the naive baseline in discrimination (0.60 and 0.64 against 0.58 and 0.62) and leaves
   the calibration broken. Even a monitor refitted on ARC itself reaches only 0.61 to 0.68. The
   output features carry less information about joint failure on that benchmark, and no label-free
   rescaling recovers what is not there.

2. **The raw scale was information, not noise.** On the unseen MMLU jury, normalization lowers the
   AUC from 0.853 to 0.787, and lowers the in-domain ceiling by the same amount. The absolute size
   of a model's confidence margin, compared across models, is part of what the coupling-aware
   monitor reads; replacing it with a within-model rank throws that away.

3. **The honest reading for deployment stands and sharpens.** The monitor is portable across
   channels on the same task, and it must be calibrated on the task it reads. The cheap fix that
   would have made it portable across tasks does not work, and it is recorded as not working.

## Adversarial reading, 2026-09-06

A context-free reader (model-assisted, advisory, same model family as the author) read this document against its transcript alone. The points below are the ones that changed a sentence; the full record is `evidence/review-model-assisted-2026-09-06.json`.

1. The normalization partly helped on task transfer: on ARC, jury A, AUC rose from 0.575 to 0.641
   (above the naive 0.618) and every ARC calibration error fell. It did not restore task transfer
   (still far below the in-domain ceiling, low-risk bands still broken), and it cost channel-transfer
   discrimination while slightly improving its calibration (0.032 to 0.025). The headline
   "does not repair" is kept with that accounting; "not a scale problem" is narrowed to "not only a
   scale problem".

## Non-claims

Public leaderboard outputs, retained as `proposed`. The normalization uses only the outputs of the
set being read, never a label; one normalization (within-model empirical quantile) was tested,
stated in advance, and no other was tried. Same juries, benchmarks, features, model and seed as
Result X. Not a deployed product, not a safety determination, not a driving result. Transcript
`evidence/result_x2.txt` re-runs byte-identically (three runs). No released `1.2` byte is involved.
