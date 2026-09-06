# Result X: the monitor transfers across juries, and not across benchmarks

Document ID: `reiyah.result-x-monitor-transfer`

Version: `0.1.0`

Lifecycle status: `proposed`

## The question Result V could not answer

Result V fitted the coupling-aware monitor on a split of one seven-model jury and evaluated it on
held-out items of the same jury. A deployed instrument does not get that: it is fitted once and
then reads channels it has never seen, on material it was not calibrated on. This fits the monitor
once, on jury A on MMLU, and never refits it. It then reads a second jury of seven models from seven
other families (Yi, EleutherAI GPT-NeoX, Google Gemma, Microsoft Phi, BigScience BLOOM, StabilityAI
StableLM, OpenLM OpenLLaMA), none in jury A, on MMLU and on ARC-Challenge. Each transfer is
compared against the naive assumption (risk equals one minus agreement) and against the in-domain
ceiling, a monitor refitted on the target itself, so the cost of not recalibrating is measured.

Two format facts are recorded rather than hidden. The 2024 leaderboard files carry no gold answer,
only a per-row correctness flag; gold is recovered at join time from a 2023-format model on the same
question and checked against that flag on every row, which held on 100 percent of rows for every
model on both benchmarks. On ARC-Challenge two jury B models and one jury A model use a different
prompt format whose questions do not join, and are dropped by the same rule Result W used.

## The result

| transfer | jury | n | naive AUC | monitor AUC | naive ECE | monitor ECE | in-domain ceiling AUC / ECE |
|---|---|---|---|---|---|---|---|
| X1: unseen jury, same benchmark (MMLU) | 7 unseen families | 13,937 | 0.683 | **0.853** | 0.053 | **0.032** | 0.856 / 0.015 |
| X4: unseen jury, different size (MMLU) | 5 of those | 13,937 | 0.697 | **0.852** | 0.074 | **0.023** | 0.854 / 0.010 |
| X2: unseen jury and unseen benchmark (ARC) | 5 unseen families | 1,170 | 0.583 | 0.610 | 0.298 | 0.213 | 0.623 / 0.068 |
| X3: same jury, unseen benchmark (ARC) | 6 of jury A | 1,170 | **0.618** | 0.575 | 0.312 | 0.184 | 0.665 / 0.054 |

On the unanimous items, where the naive assumption assigns zero risk:

| transfer | unanimous items | actual wrong | monitor risk |
|---|---|---|---|
| X1 | 126 | 23.8% | 20.3% |
| X4 | 539 | 19.7% | 17.3% |
| X2 | 520 | 41.0% | 22.7% |
| X3 | 607 | 37.2% | 26.5% |

## What it says, both halves

1. **The monitor transfers across channels.** Read on seven models it never saw, from seven
   families it never saw, it reaches an AUC of 0.853 against an in-domain ceiling of 0.856, and a
   calibration error of 0.032 against a ceiling of 0.015. Recalibrating on the new jury would buy
   almost nothing. On the new jury's unanimous items it assigns 20 percent risk where the truth is
   24 percent and the naive assumption says zero. The coupling it learned is a property of how
   redundant channels fail, not of the seven channels it learned it from. It also survives a change
   of jury size from seven to five.

2. **The monitor does not transfer across benchmarks.** Read on ARC-Challenge, its discrimination
   falls to the naive baseline or below it (0.575 against 0.618 for jury A), and its calibration
   breaks: the lowest-risk band predicts 6 percent and realizes 38 percent. The per-model confidence
   margins on a 25-shot reasoning task are on a different scale from 5-shot knowledge questions, and
   the monitor reads that scale as confidence it is not. Even the in-domain ceiling on ARC is weak
   (AUC 0.62 to 0.67), so part of the loss is that the output features carry less signal there.

3. **The honest reading for deployment.** A coupling-aware monitor can be fitted on one set of
   channels and read on another, but it must be calibrated on the task distribution it will read.
   Channel transfer holds; task transfer does not. Any claim that the instrument is deployable
   without task-level recalibration is contradicted by this result.

## Consequence for the program

Result V is upgraded from a one-jury demonstration to a channel-transferable one, and bounded at the
same time: the instrument is portable across channels and not across tasks. The next honest tests
are a monitor fitted on driving channel outputs rather than benchmark outputs, and a margin
normalization that is itself learned without labels, which is not attempted here.

## Adversarial reading, 2026-09-06

A context-free reader (model-assisted, advisory, same model family as the author) read this document against its transcript alone. The points below are the ones that changed a sentence; the full record is `evidence/review-model-assisted-2026-09-06.json`.

1. Channel transfer is tested on the same 13,937 MMLU items the monitor was fitted on, with a
   different jury; the item distribution is unchanged, so "transfer across channels" here means
   across models on the same items. X4 is a subset of jury B, not an independent jury.
2. Recalibrating on the new jury halves the calibration error (0.032 to 0.015); "would buy almost
   nothing" is true of discrimination and not of calibration.

## Non-claims

Public leaderboard outputs, retained as `proposed`. Transfer between two juries of public base
models on two benchmarks; not a deployed product, not a safety determination, not a driving result.
Margins are not rescaled between juries or benchmarks, by design, because a deployed monitor would
not know the new channels' scales either. Gold for the 2024-format files is recovered at join time
and verified per row. A logistic-regression monitor is fitted; no LLM is executed. Transcript
`evidence/result_x.txt` re-runs byte-identically (three runs compared). No released `1.2` byte is
involved.
