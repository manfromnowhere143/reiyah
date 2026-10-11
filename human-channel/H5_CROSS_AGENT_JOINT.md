# Human channel H5: detector-score and gaze coincidence on selected objects

Document ID: `reiyah.human-channel.h5-cross-agent-joint`

Version: `0.2.0`

Lifecycle status: `corrected`

## Interpretation correction, 2026-10-10

The [dated correction](../research/claim-correction/0.1.0/README.md) governs this result. Original
transcripts and numerical measurements are preserved. Detector-selected
coefficients do not bound population dependence; gaze does not identify
awareness. No universal independence law or safety-evidence credit follows.

## Measurement definition

On BDD-A (Berkeley DeepDrive Attention, Xia et al. 2018), braking-event clips
carry camera video and laboratory observer gaze heatmaps. The script runs a
pretrained detector and averages gaze intensity inside its selected boxes.
The historical names "automation miss" and "human miss" below refer to these
score and heatmap proxies. They do not measure whether a driver knows an object
is present or can respond to it.

- automation confidence = detector score (Faster R-CNN, COCO, run on the frames)
- human attention = mean gaze-heatmap intensity inside the object box, aligned per the README
- automation miss = score below a `0.5` operating threshold; human miss = gaze attention below the
  per-run median
- `c = P(both miss) / [ P(auto miss) * P(human miss) ]`, a descriptive ratio for these operational variables.

## The result

BDD-A validation, 120 clips, 651 frames, **13,904 driving objects**.

| quantity | value |
|---|---|
| P(automation miss) | 27.0% |
| P(human miss) | 50.0% |
| P(both miss) | 13.1% |
| expected if independent | 13.5% |
| **cross-agent coefficient c** | **0.972** (re-measured 2026-09-06 with a clip-clustered band, H5b: 0.962 [0.927, 0.993]) |
| Pearson corr(automation score, human attention) | -0.022 |

The reported point estimate is near 1 and the correlation near zero. H5 alone
provides no interval or prespecified equivalence margin. These values do not
establish independence. The earlier 200-object pilot used the same construction.

## Historical descriptive comparison

The recorded quantities below have different events, populations and marginals.
They are not a controlled comparison of kinds of redundancy:

| Redundancy pairing | coefficient | reading |
|---|---|---|
| Two sensors, camera x lidar (Result L) | 1.15 | fail together |
| One human, observation x response (Result H3) | 1.46 | fail together |
| **Human x automation (this result)** | **0.97** | **selected proxy coefficient near one** |

The recorded coefficient concerns low detector score and below-median gaze on
selected boxes. It does not establish that different kinds of agents fail
independently, explain a causal mechanism, or validate human-automation teaming.

## The bounds, which are load-bearing

This result is honest only with its limits stated plainly, because they change what may be claimed.

1. **It is measured on detectable objects.** The object set is the detector's detections at score
   `>= 0.3`. Objects the detector misses entirely are unobservable here without ground-truth boxes,
   so the true joint total miss, where **both** channels are totally blind, is not captured. The
   omitted set can move the normalized coefficient in either direction. No population
   lower bound or independence certificate follows; the exact correction gives both completions.
2. **Observer scope is restricted.** The gaze is attentive-observer data. Results
   H3 and H4 concern different outcomes and datasets; they cannot identify a conditional
   independence relation for this human-machine construction.
3. **The gaze is an in-lab aggregate over observers**, not one naturalistic driver, and `c > 1`
   anywhere in this program includes shared scene difficulty, not claimed as pure latent dependence.
4. Descriptive, not clustered, on one public research dataset.

## Safety interpretation withdrawn

The former application of Result S is withdrawn. The descriptive coefficient
is not a validated safety-critic dependence bound and supplies no validation
evidence multiplier, redundancy credit or takeover guarantee.

## Adversarial reading, 2026-09-06

A context-free reader (model-assisted, advisory, same model family as the author) read this document against its transcript alone. The points below are the ones that changed a sentence; the full record is `evidence/review-model-assisted-2026-09-06.json`.

1. **What the human channel measures.** The human miss is a median split, and the median gaze
   mass inside a box is 0.005, near zero. The split therefore separates boxes by whether they carry
   almost any gaze mass at all, a quantity governed in part by box size and position. The
   coefficient is a statement about that operationalization of attention, not about attention as
   such, and the document now says so.
2. **The ceiling the marginals impose.** With P(automation miss) 27 percent and P(human miss) 50
   percent, the coefficient cannot exceed 2.0 whatever the dependence. A band of [0.93, 0.99]
   (H5b) sits well below that ceiling, so it carries information; the H6 construction, with an
   84.5 percent automation miss rate, has a ceiling of 1.18 and carries far less. The human-machine
   comparison must retain these marginal constraints; neither H5 nor H6 establishes a law.

## Non-claims

Research-use public data (Xia et al. 2018, BDD-A), retained as `proposed`. Object detections from a
pretrained model, gaze from an in-lab heatmap; descriptive, not a causal effect, not a safety
determination, not a claim about any product. Measured on the detector-selected set, with no population bound on
cross-agent dependence. No released `1.2` byte is involved.
