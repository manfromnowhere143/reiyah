# Human channel H5b: the cross-agent coefficient with its band

Document ID: `reiyah.human-channel.h5b-cross-agent-interval`

Version: `0.1.0`

Lifecycle status: `proposed`

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

1. **The human-machine cell holds with a band that excludes fail-together.** The coefficient's
   upper bound is 0.993, below 1; the human and the machine do not go blind to the same
   detectable objects more than independence predicts, and the band sits pointedly below every
   same-kind coefficient in the program (sensors 1.10 to 1.29 with bands of a hundredth, LLM pairs
   1.3 to 2.3, the human's own channels 1.46 [1.04, 1.90]).

2. **This is a re-measurement, not an exact reproduction of H5.** H5's retained run covered 651
   frames and 13,904 objects; this run, with the arguments recorded (120 clips at 0.4 frames per
   second), covered 519 frames and 11,104 objects. The exact arguments of the H5 run were not
   recorded, and the frame sampling evidently differed. The two coefficients, 0.972 and 0.962, and
   H6's 0.981 [0.962, 0.998], agree within the band.

3. **Determinism on the accelerator is a stated question, not an assumption.** The detector runs on
   the machine's GPU path; a second pass with identical arguments is recorded below once complete.

## Non-claims

Same measurement as H5 with a band; the median split is recomputed on this sample and held fixed
inside the bootstrap. In-lab aggregate gaze from engaged observers; the object set is the
detector's detections, so this is a floor on cross-agent dependence, not a certificate of
independence. Research-use public data; terms not retained. Descriptive, not a causal claim, not a
safety determination. Transcript `evidence/h5b_cross_agent_interval.txt`; raw rows
`evidence/h5b_raw.npz` (not committed, regenerable). No released `1.2` byte is involved.
