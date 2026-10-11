# Human channel H6: the total-both-miss, measured with an interval

Document ID: `reiyah.human-channel.h6-total-both-miss`

Version: `0.2.0`

Lifecycle status: `corrected`

## Interpretation correction, 2026-10-10

The [dated correction](../research/claim-correction/0.1.0/README.md) governs this result. Original
transcripts and numerical measurements are preserved. Detector-selected
coefficients do not bound population dependence; gaze does not identify
awareness. No universal independence law or safety-evidence credit follows.

## Reference-defined measurement

H5 measured cross-agent coincidence on objects the detector at least weakly saw, and reported a
near-one proxy coefficient there. The dangerous case is the total joint miss: an object that is really
present, that the automation detects **not at all**, and that the human also does not attend. That
needs a reference for "present" beyond the deployed detector. BDD-A carries no ground-truth boxes,
and BDD100K's labels cannot be joined to it (the clips are renumbered with no mapping, confirmed
from the data). The implemented construction uses a stronger reference
detector to define selected candidate objects and an edge detector as the automation channel.
An unmatched reference box is a reference-defined miss, not independently established physical blindness.

- reference candidates: Faster R-CNN ResNet50-FPN v2, driving classes, score `>= 0.6`
- automation model under study: SSDLite MobileNetV3, score `>= 0.25`; run offline
- reference-defined automation miss: no eligible automation box overlaps the
  reference at IoU `>= 0.5`; this includes localization and matching effects
- historical "human miss" proxy: gaze-heatmap density below the per-run median
- `c = P(both miss) / [ P(auto miss) * P(human miss) ]`, a descriptive ratio for these operational variables

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

The edge detector fails to match 84.5% of the selected reference boxes under
these thresholds. The low-gaze proxy and reference-defined automation miss have
a recorded coefficient near one. The interval sits just below 1.0. This is an
offline reference-defined result; physical blindness is not identified.

## What it says, stated to its tolerance

Historical summaries follow. Their events and populations differ, so these
coefficients do not rank kinds of redundancy:

| Redundancy pairing | coefficient | reading |
|---|---|---|
| Two sensors, camera x lidar | 1.15 [1.14, 1.16] | worse than independent, fails together |
| One human, observation x response | 1.46 | worse than independent |
| Human x automation, uncertain miss (H5) | 0.97 | selected proxy coefficient |
| **Human x automation, total miss (H6)** | **0.98 [0.96, 0.998]** | **selected proxy coefficient** |

The interpretation of a general difference between kinds of redundancy is
withdrawn. The observed marginals strongly constrain the normalized coefficient.
No causal mechanism or preference for a kind of redundancy is identified here.

## The bounds, load-bearing

1. The reference is a strong detector, not human ground truth, so this is the joint miss on the
   strong-model-selected set. Neither the normalized coefficient nor its rate
   is thereby a lower bound on the full physical population.
2. The gaze comes from attentive laboratory observers. Results H3 and H4
   concern separate populations and outcomes; they cannot establish conditional
   human-machine independence in this construction.
3. The gaze is an in-lab aggregate over observers, SSDLite is one edge detector and not any product,
   and this is descriptive, on one public research dataset.

## Safety interpretation withdrawn

The former Result S evidence multiplier and proposed human-machine safety
credit are withdrawn. The required transfer to safety-critic errors, fusion
rule, uniform dependence bound and statistical estimator is not established.

## Adversarial reading, 2026-09-06

A context-free reader (model-assisted, advisory, same model family as the author) read this document against its transcript alone. The points below are the ones that changed a sentence; the full record is `evidence/review-model-assisted-2026-09-06.json`.

1. **The marginals nearly force the result.** With P(automation miss) 84.5 percent and P(human
   miss) 50 percent, the coefficient is confined by the Fréchet bounds to about [0.82, 1.18]
   whatever the true dependence. "Not worse than independent" is therefore close to forced by the
   marginals, and this coefficient cannot be compared on the same scale as same-kind coefficients
   whose marginals permit values of 2 or 3. The register entry is narrowed to say so; the
   H5 and H5b coefficients also require their stated selection limits; their ceiling is 2.0.
2. An 84.5 percent total-miss rate for a small edge detector at 0.25 on objects a strong detector
   finds at 0.6 was initially described as genuine blindness. H6b examined the
   reference-defined mismatch the same evening: the miss is
   size-driven (100 percent on the smallest quarter of boxes, 42.6 on the largest), loosening the
   match recovers three points, and the category lists are identical. Those
   diagnostics narrow pipeline explanations; they do not establish physical
   blindness against independent truth. The ceiling caveat in point 1 stands.
3. The band uses 96 of 100 clips; four lack gaze video or reference objects.

## Non-claims

Research-use public data (Xia et al. 2018, BDD-A), retained as `proposed`. A strong detector as
reference, not human ground truth; no population lower bound on the joint-miss
rate or coefficient. The word silent is not claimed: no warning, indication,
or fallback channel is observed here, and the register reserves
joint silent miss for an audited monitor adapter. Pretrained torchvision detectors are executed on
the public frames to produce the automation channel; no model is trained. Descriptive, not a causal
effect, not a safety determination, not a claim about any product. No released `1.2` byte is
involved.
