# Human channel H5b: the cross-agent coefficient with its band

Document ID: `reiyah.human-channel.h5b-cross-agent-interval`

Version: `0.2.0`

Lifecycle status: `corrected`

## Interpretation correction, 2026-10-10

The [dated correction](../research/claim-correction/0.1.0/README.md) governs this result. Original
transcripts and numerical measurements are preserved. Detector-selected
coefficients do not bound population dependence; gaze does not identify
awareness. No universal independence law or safety-evidence credit follows.

## Why

H5 reported the cross-agent coincidence coefficient, automation miss by human inattention on the
detector's own detections, as a point estimate of 0.972 on 13,904 objects, with no band; H6 had
one. This is the same measurement, unchanged in every definition (detector and weights, score
floor 0.3, operating threshold 0.5, driving classes, gaze alignment, median split), with the clip
id recorded per object so a clip-clustered bootstrap band can be put on the coefficient, and the
raw per-object rows saved.

## The result

BDD-A validation, 120 clips, 519 frames, 11,104 driving objects.

| quantity | value |
|---|---|
| P(automation miss) | 26.8% |
| P(human miss) | 50.0% |
| P(both miss) | 12.9% |
| expected if independent | 13.4% |
| **cross-agent coefficient `c`** | **0.962** |
| clip-clustered bootstrap 95% band (117 clips, B = 2000) | **[0.927, 0.993]** |
| Pearson correlation of automation score and human attention | -0.035 |

## What it says

1. **The selected proxy coefficient has a clip-bootstrap interval below one.**
   Its historical upper endpoint is 0.993. This concerns low score and low gaze
   under the fixed sample split. It supplies neither an independence certificate
   nor a comparison of latent failures across sensors, people and language models.

2. **This is a re-measurement, not an exact reproduction of H5.** H5's retained run covered 651
   frames and 13,904 objects; this run, with the arguments recorded (120 clips at 0.4 frames per
   second), covered 519 frames and 11,104 objects. The exact arguments of the H5 run were not
   recorded, and the frame sampling evidently differed. The two coefficients, 0.972 and 0.962, and
   H6's 0.981 [0.962, 0.998], agree within the band.

3. **The retained account reports matching transcripts on a second pass.**
   This concerns printed summaries with identical arguments on the same machine.
   Transcript equality alone does not establish equality of every unprinted
   detector tensor. Neither pass was rerun for this correction; reproduction
   on a different machine is not established.

## Adversarial reading, 2026-09-06

A context-free reader (model-assisted, advisory, same model family as the author) read this document against its transcript alone. The points below are the ones that changed a sentence; the full record is `evidence/review-model-assisted-2026-09-06.json`.

1. The band resamples clips with the median split held fixed, so it carries clip-sampling
   uncertainty and none of the dichotomization uncertainty; the split's near-zero median is stated
   in H5's adversarial reading.
2. Three of the 120 clips have no gaze video in the archive (clip ids 1738, 1739, 1741) and are
   skipped by the tool, which is why the band uses 117 clips.
   <!-- review-exempt: 1738=clip identifier, not a measurement; 1739=clip identifier; 1741=clip identifier -->
3. The marginals impose a ceiling of 2.0 on the coefficient here, so the band's exclusion of 1 is
   informative; see H5.

## Non-claims

Same measurement as H5 with a band; the median split is recomputed on this sample and held fixed
inside the bootstrap. In-lab aggregate gaze from engaged observers; the object set is the
detector's detections. No population lower bound or certificate of
independence follows. Source access and terms limitations remain in the claim
register and custody record. Descriptive, not a causal claim or safety
determination. Transcript `evidence/h5b_cross_agent_interval.txt`; raw rows
`evidence/h5b_raw.npz` (not committed, regenerable). No released `1.2` byte is involved.
