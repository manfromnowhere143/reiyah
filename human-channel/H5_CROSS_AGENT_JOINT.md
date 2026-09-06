# Human channel H5: the cross-agent joint, and where independence finally holds

Document ID: `reiyah.human-channel.h5-cross-agent-joint`

Version: `0.1.0`

Lifecycle status: `proposed`

## The measurement the whole program pointed at

Every earlier result measured redundancy within one kind of channel: two sensors, or one human's
own looking and acting. This measures across the two kinds of agent on the same encounter. On
BDD-A (Berkeley DeepDrive Attention, research-use license, Xia et al. 2018), each braking-event
clip carries the camera video and a driver gaze-attention heatmap over the same scene. A validated
object detector on the frames is the automation channel; the gaze heatmap over the same objects is
the human channel. The Definition 32 question, now across a human and a machine: do they go blind
to the same objects more than independence predicts.

- automation confidence = detector score (Faster R-CNN, COCO, run on the frames)
- human attention = mean gaze-heatmap intensity inside the object box, aligned per the README
- automation miss = score below a `0.5` operating threshold; human miss = gaze attention below the
  per-run median
- `c = P(both miss) / [ P(auto miss) * P(human miss) ]`, the same estimand as everywhere else.

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

The coefficient is indistinguishable from 1, and the correlation is essentially zero, stable from a
200-object pilot to the 13,904-object run.

## What it says, and why it is the sharpest line in the body of work

Placed beside the rest:

| Redundancy pairing | coefficient | reading |
|---|---|---|
| Two sensors, camera x lidar (Result L) | 1.15 | fail together |
| One human, observation x response (Result H3) | 1.46 | fail together |
| **Human x automation (this result)** | **0.97** | **approximately independent** |

The finding is not that redundancy always fails. It is that **same-kind redundancy fails and
different-kind redundancy roughly holds.** Two sensors share a substrate, the point return, and so
share their blind spots. A human's eyes and hands share one attention budget, and so fail together
when it is spent. But a human and a machine are blind for genuinely different reasons, and across
the detectable objects here their neglect does not coincide. That is the one pairing where the
independence a safety case assumes survives contact with data, and it is exactly the
human-automation teaming that Level 2 and Level 3 systems rely on.

## The bounds, which are load-bearing

This result is honest only with its limits stated plainly, because they change what may be claimed.

1. **It is measured on detectable objects.** The object set is the detector's detections at score
   `>= 0.3`. Objects the detector misses entirely are unobservable here without ground-truth boxes,
   so the true joint total miss, where **both** channels are totally blind, is not captured. That
   omitted set can only push dependence up, so `c ~ 1` is a floor on cross-agent dependence, not a
   certificate of independence.
2. **It holds only while the human is engaged.** The gaze here is attentive-observer data. Results
   H3 and H4 show a distracted human's own channels collapse and takeover slows, so the independence
   is conditional on an attending human, not a property of the pairing under distraction.
3. **The gaze is an in-lab aggregate over observers**, not one naturalistic driver, and `c > 1`
   anywhere in this program includes shared scene difficulty, not claimed as pure latent dependence.
4. Descriptive, not clustered, on one public research dataset.

## Consequence for the corrected calculus

The corrected safety calculus (Result S) inflates required validation evidence by `sqrt(c)` per
redundant layer. This result says the human-automation layer, on detectable objects and with an
engaged human, contributes a factor near `sqrt(0.97) ~ 1`, essentially no inflation, in contrast to
the same-kind layers. The safety reading is specific: credit the human-automation redundancy only
under the conditions where it was independent here, an attending human and objects the machine can
at least partially see, and never as a blanket independence.

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
   cell of the law rests on H5 and H5b, not on H6.

## Non-claims

Research-use public data (Xia et al. 2018, BDD-A), retained as `proposed`. Object detections from a
pretrained model, gaze from an in-lab heatmap; descriptive, not a causal effect, not a safety
determination, not a claim about any product. Measured on the detectable set, a lower bound on
cross-agent dependence. No released `1.2` byte is involved.
