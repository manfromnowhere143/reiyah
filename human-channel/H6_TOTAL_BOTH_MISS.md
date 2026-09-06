# Human channel H6: the total-both-miss, measured with an interval

Document ID: `reiyah.human-channel.h6-total-both-miss`

Version: `0.1.0`

Lifecycle status: `proposed`

## The deepest question, and why H5 could not answer it

H5 measured cross-agent coincidence on objects the detector at least weakly saw, and found
independence there. The dangerous case is the total joint miss: an object that is really
present, that the automation detects **not at all**, and that the human also does not attend. That
needs a reference for "present" beyond the deployed detector. BDD-A carries no ground-truth boxes,
and BDD100K's labels cannot be joined to it (the clips are renumbered with no mapping, confirmed
from the data). So the correct construction, without an impossible join, uses a strong reference
detector to define the objects present and a realistic deployed detector as the automation channel,
whose total misses on the reference objects are genuine blindness.

- reference (objects present): Faster R-CNN ResNet50-FPN v2, driving classes, score `>= 0.6`
- deployed automation: SSDLite MobileNetV3, a real edge detector, score `>= 0.25`
- automation miss on a reference object: no deployed box overlaps it at IoU `>= 0.5`, i.e. the
  deployed detector gives it no detection at all
- human miss: gaze-heatmap density on the reference box below the per-run median
- `c = P(both miss) / [ P(auto miss) * P(human miss) ]`, the same estimand as everywhere else

## The result

BDD-A validation, 100 clips, 533 frames, **7,735 reference objects**.

| quantity | value |
|---|---|
| P(deployed automation totally misses a present object) | 84.5% |
| P(human misses) | 50.0% |
| P(both miss = the joint total miss) | 41.4% |
| expected if independent | 42.2% |
| **coefficient c** | **0.981** |
| clip-clustered bootstrap 95% CI (96 clips) | **[0.962, 0.998]** |

The edge detector is totally blind to 84.5% of the objects a strong model confidently finds, which
is the deployment reality for cheap perception. And even across those total misses, the human's
neglect does not pile onto the machine's blindness. The interval sits just below 1.0.

## What it says, stated to its tolerance

Read against the rest of the program, with intervals where they exist:

| Redundancy pairing | coefficient | reading |
|---|---|---|
| Two sensors, camera x lidar | 1.15 [1.14, 1.16] | worse than independent, fails together |
| One human, observation x response | 1.46 | worse than independent |
| Human x automation, uncertain miss (H5) | 0.97 | approximately independent |
| **Human x automation, total miss (H6)** | **0.98 [0.96, 0.998]** | **not worse than independent** |

The load-bearing claim is the asymmetry: **same-kind redundancy is substantially above 1; the
human-machine pairing is not**, with the qualification added on 2026-09-06 that this construction's
marginals cap the coefficient at about 1.18, so the informative human-machine evidence is H5 and H5b. The H6 interval grazes 1.0 from below,
so the most that can be said on the upper side is a small complementary tilt, where the machine is
blind the human is slightly more likely to attend, and it is not oversold here: a two-percent effect
with a confidence bound at 0.998 is reported as "approximately independent, and pointedly not the
fail-together pattern of same-kind redundancy."

The mechanism is the honest reason the field's independence assumption survives in exactly one
place. Two sensors share a substrate and share their blind spots. A human's eyes and hands share one
attention budget. But a human and a machine are built and fail differently, so their misses do not
concentrate on the same objects. The redundancy worth building is the one across kinds.

## The bounds, load-bearing

1. The reference is a strong detector, not human ground truth, so this is the joint miss on the
   strong-model-detectable set, still a lower bound, since the strongest model also misses the very
   hardest objects.
2. It holds for an engaged human; the gaze here is attentive-observer data, and Results H3 and H4
   show a distracted human's own channels collapse, so the independence is conditional on attention.
3. The gaze is an in-lab aggregate over observers, SSDLite is one edge detector and not any product,
   and this is descriptive, on one public research dataset.

## Consequence for the corrected calculus

In Result S the corrected evidence requirement inflates by `sqrt(c)` per credited redundancy layer.
Same-kind layers inflate it. The human-automation layer, on this evidence, contributes
`sqrt(0.98) ~ 0.99`, essentially no inflation, and possibly a small credit, but only under the
conditions measured here: an engaged human and objects a strong model can find. Credited as a
blanket independence, it would be an overclaim; credited under those conditions, it is the one
redundancy the data supports.

## Adversarial reading, 2026-09-06

A context-free reader (model-assisted, advisory, same model family as the author) read this document against its transcript alone. The points below are the ones that changed a sentence; the full record is `evidence/review-model-assisted-2026-09-06.json`.

1. **The marginals nearly force the result.** With P(automation miss) 84.5 percent and P(human
   miss) 50 percent, the coefficient is confined by the Fréchet bounds to about [0.82, 1.18]
   whatever the true dependence. "Not worse than independent" is therefore close to forced by the
   marginals, and this coefficient cannot be compared on the same scale as same-kind coefficients
   whose marginals permit values of 2 or 3. The register entry is narrowed to say so; the
   human-machine cell of the law rests on H5 and H5b, whose ceiling is 2.0.
2. An 84.5 percent total-miss rate for a small edge detector at 0.25 on objects a strong detector
   finds at 0.6 is not verified as genuine blindness; a resolution, class-mapping or matching
   defect would produce the same number. Open, and the register requirement now names it.
3. The band uses 96 of 100 clips; four lack gaze video or reference objects.

## Non-claims

Research-use public data (Xia et al. 2018, BDD-A), retained as `proposed`. A strong detector as
reference, not human ground truth; a lower bound on the true joint miss. The word silent is not
claimed: no warning, indication, or fallback channel is observed here, and the register reserves
joint silent miss for an audited monitor adapter. Pretrained torchvision detectors are executed on
the public frames to produce the automation channel; no model is trained. Descriptive, not a causal
effect, not a safety determination, not a claim about any product. No released `1.2` byte is
involved.
