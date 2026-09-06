# Human channel H4: distraction and takeover response in L3 automation

Document ID: `reiyah.human-channel.h4-dcpt-takeover`

Version: `0.1.0`

Lifecycle status: `proposed`

## Why a second dataset

The 100-Car results are from human driving with no automation. The mission's relevance lives
where a human is the backup to automation, so this brings in a modern L3 conditional-automation
study, DCPT (Hu et al., Zenodo, doi:10.5281/zenodo.17354775, CC BY 4.0 as recorded by the publisher;
custody in `evidence/public-data-custody-2026-09-06.json`), and measures the human's response when
the automation hands control back.

In DCPT the automation drives while the participant does one of nine non-driving tasks, then a
takeover request is issued at a random time and the participant resumes control. The response
measure is the takeover time. Because the request timing is random, the automation handover is
independent of the human's state by construction, so this is not the cross-agent dependence
measurement; it is the human readiness-to-response relationship in a real L3 setting.

The trial identifiers encode the task, participant, and takeover time, so this result is derived
from the 60 KB metadata table alone, with no large media download.

## The result

1,080 takeover trials, 40 participants.

| Non-driving task | n | takeover time (mean) |
|---|---|---|
| No task | 117 | 1.99 s |
| Watching video (center screen) | 120 | 2.01 s |
| Radio | 120 | 2.03 s |
| Chatting with passenger | 126 | 2.05 s |
| Phone call | 113 | 2.17 s |
| Eating | 116 | 2.36 s |
| Reading | 121 | 2.48 s |
| Playing game | 123 | 2.49 s |
| Messaging | 124 | 2.51 s |

Grouped by how the task loads the driver:

| Group | n | takeover time (mean) | vs no task |
|---|---|---|---|
| No task | 117 | 1.99 s | - |
| Cognitive-only (phone call, radio, chatting) | 359 | 2.08 s | +0.09 s |
| Visual-manual (game, messaging, reading, eating) | 484 | 2.46 s | **+0.47 s (+24%)** |

## What it says

1. **The kind of distraction is what matters, not distraction in general.** Tasks that take the
   eyes and hands off the road, playing a game, messaging, reading, eating, slow the takeover by
   about half a second, roughly 24%. Tasks that mainly load attention while the eyes stay freer,
   a phone call, the radio, chatting, cost almost nothing.

2. **Half a second is not small here.** At highway speed a 0.47 s delay is on the order of 15 m of
   additional travel before the human has control. The human-as-backup assumption a Level 3
   safety case relies on is weakest exactly for the tasks people actually do on a phone.

3. **The same coupling, in a modern setting.** The human's observation state, what they were
   absorbed in, predicts their response quality, the takeover time. This is the observation-to-
   response link H3 measured in 100-Car, now in L3 automation, the setting the mission is about.

## What this is not

A driving-simulator study, not on-road. The takeover request is random, so this measures readiness
to response, not the cross-agent human-automation dependence, which needs a hazard where the
automation's and the human's detection can each fail; that is the next design. Takeover time is the
reaction to resume control, not a collision outcome. Trials cluster within 40 participants, and the
figures here are descriptive across trials, not a participant-clustered inferential test, though the
visual-manual versus no-task gap is large relative to its spread.

## Adversarial reading, 2026-09-06

A context-free reader (model-assisted, advisory, same model family as the author) read this document against its transcript alone. The points below are the ones that changed a sentence; the full record is `evidence/review-model-assisted-2026-09-06.json`.

1. The task watching video (eyes on the center screen, mean 2.01 s) belongs to neither group and
   is indistinguishable from no task (1.99 s). The visual-manual group was defined in the tool
   before the numbers were read, but it was not preregistered, and the contrast of +0.47 s depends
   on which tasks are labelled visual-manual; with video included the group mean falls. Stated as
   a limit of the grouping, not of the data.
2. The 15 m sentence is arithmetic on an assumed highway speed, not a measurement.

## Non-claims

Descriptive statistics on a public CC BY 4.0 dataset, retained as `proposed`. Not a causal effect,
not a safety determination, not a claim about any product. No released `1.2` byte is involved.
