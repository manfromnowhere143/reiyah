# Gate B measurement: camera and lidar fail together, and it matters for the safety math

Document ID: `reiyah.gate-b-findings-synthesis`

Version: `0.1.0`

Lifecycle status: `proposed`

This is the one-page reading of the Gate B measurement workstream (Results A through O). Every
number here is measured on public data and reproducible from this repository; each claim links
to the result that establishes it. The non-claims at the foot are not boilerplate - they are the
exact boundary of what has and has not been shown.

## The finding in one sentence

On the nuScenes validation split, a camera detector and a lidar detector **fail on the same
objects more often than independence predicts, even after conditioning on class, range,
visibility, weather and motion** - and that residual coupling is robust to the detector, to the
score threshold, and to plausible unmeasured confounding.

## Why it is worth a safety engineer's attention

Mobileye's RSS paper (Shalev-Shwartz, Shammah, Shashua, arXiv:1708.06374) argues that direct
statistical validation of an autonomous vehicle would need on the order of `10^9` hours.
**Definition 32** escapes that cost by positing *c-approximate independence* between subsystem
errors, and **Corollary 3** uses it to cut the required evidence to about `10^5`. The coefficient
`c` is never estimated anywhere in the paper, and independence is assumed rather than measured.

If two perception channels fail together more than independently, that assumption is optimistic
and the evidence reduction is overstated. This workstream measures the coefficient the safety
argument leaves unmeasured.

## The core result, and its four robustness axes

![Gate B robustness: the conditional coefficient stays above independence across thresholds and detectors](gate_b_robustness_figure.svg)

The conditional coefficient is the joint-failure rate divided by what independence would predict
*within* each stratum of the five confounders. Above 1.0 means the channels miss the same objects
more than independence allows. The headline value is `1.151` for Mapillary x Megvii at score
`>= 0.3` ([Result L](RESULT_L_CONVERGENCE.md)). What turns one measurement into a finding is that
it survives every cheap way to dismiss it:

| Axis | Result | Objection answered | Outcome at score >= 0.3 |
|---|---|---|---|
| **Detector** | [M](RESULT_M_CROSS_DETECTOR_REPLICATION.md) | "it is one model pair" | Replace the entire lidar backbone with PointPillars (half the accuracy): c = **1.096**, still excludes 1.0 |
| **Score threshold** | [N](RESULT_N_THRESHOLD_ROBUSTNESS.md) | "0.3 is cherry-picked" | Sweep 0.1 to 0.5, both detectors: **10 of 10** intervals exclude 1.0 |
| **Unmeasured confounding** | [O](RESULT_O_SENSITIVITY_EVALUE.md) | "you did not measure everything" | A hidden common cause must reach **E-value 3.03** (Megvii) / **2.13** (PointPillars) on both arms to nullify it |
| **Detector (camera)** | [Q](RESULT_Q_CAMERA_AXIS_AND_MODALITY_GRID.md) | "it is one camera model" | Replace the camera with FCOS3D (validated to published mAP): crossed with both lidars, c = **1.107** / **1.072**, still excludes 1.0 |

The E-value is the decisive honesty move: instead of only declaring that an unmeasured common
cause *could* exist, it states how strong one would have to be. A confounder associated with both
camera and lidar failure by less than roughly two to three on the risk-ratio scale, beyond the
five measured covariates, cannot explain the coupling away.

## What is stated as measured, and not oversold

- **The coupling attenuates.** As the score threshold tightens and only confident detections
  remain, the conditional coefficient declines toward independence (Megvii `1.360 -> 1.051`). It
  does not reach it anywhere measured, but the effect at strict thresholds is small.
- **This is association, not causation.** Every coefficient is measured after declared
  conditioning. No causal effect is claimed, and no adjustment set is claimed sufficient for
  identification.
- **It is bounded by what nuScenes annotates.** Object size and truncation are not in this cache
  and were not tested; the E-value says how strong such a factor would have to matter, not that it
  does not.
- **The one detector axis that was open is now closed.** The camera axis (Result Q) was the last
  gap — every pair used to share the Mapillary camera. A second camera detector, FCOS3D, validated
  to its published mAP, crossed with both lidars stays above independence (1.107, 1.072). The four
  detector/threshold/confounding axes are complete; what remains genuinely open is *external* audit
  — these results are reproducible and self-checked, but retained as `proposed`, not independently
  reviewed.

## Two results that sharpen the picture

- **The coefficient is smallest where the sensors jointly miss most** ([Result P](RESULT_P_COEFFICIENT_VS_ABSOLUTE.md)).
  `c = P(both) / (P_A·P_B)` is a ratio deflated by the marginal miss rates. As the threshold
  tightens, `c` falls toward independence (2.27 → 1.24) while the *absolute* joint-miss rate rises
  from ~10% to ~51% of all objects. A redundancy argument that certifies safety by exhibiting a
  small `c` can sit on the worst absolute joint failure; `c` must be read with the marginals, never
  alone.
- **What the 2×2 modality grid shows** ([Result Q](RESULT_Q_CAMERA_AXIS_AND_MODALITY_GRID.md)). With
  two cameras and two lidars, all six pairs exceed independence. The strongest coupling is
  lidar-lidar (1.290) — shared point sparsity. Two cameras couple like cross-modality (1.144), not
  like two lidars. So the coupling is governed by *shared failure drivers*, not by same-versus-cross
  modality, and no pairing reaches the independence a redundancy safety case assumes.

## Reproduce it

The matched prediction caches and the ground-truth cache are built by the tools in
`tools/measure/` (see [GATE_B_SESSION_HANDOFF.md](GATE_B_SESSION_HANDOFF.md) for the data setup).
With those in place, each axis is one command:

```
# headline conditional coefficient (Result L / M)
python3 tools/measure/result_l_convergence.py \
    gt_val_cache.json matched_mapillary.json matched_megvii.json

# threshold robustness, both detectors (Result N)
python3 tools/measure/result_n_threshold_robustness.py \
    gt_val_cache.json matched_mapillary.json matched_pointpillars.json

# E-value sensitivity to unmeasured confounding (Result O)
python3 tools/measure/result_o_sensitivity_evalue.py \
    gt_val_cache.json matched_mapillary.json matched_megvii.json

# regenerate this figure
python3 tools/measure/make_synthesis_figure.py > docs/gate_b_robustness_figure.svg
```

Raw outputs are retained under `evidence/measurement/` (`result_l.txt` through `result_o.txt`).
Result N reproduces Result L's `1.151` at 0.3 exactly; Result O reproduces Result E's conditional
odds ratio of `2.810` to `2.776`. Those self-checks are what license reading the rest.

## Where this sits in the whole result set

Results A through F establish the measurement apparatus and a separate finding (the nuScenes
evaluation pipeline removes a range-sensor-selected 9.43% of ground-truth objects before scoring,
biasing dependence estimates toward independence). Results D, E, G through K measure and interpret
the coefficient and carry it into the RSS argument. Results L through O, summarised here, close the
convergence question and harden it along the three axes. Each result records its own withdrawals:
several claims from this workstream were refuted on evidence and left standing in the record *with*
their refutations attached rather than edited out.

## Non-claims

This is Gate B measurement on two published detection outputs over one public split, retained as
`proposed`. No scientific support, safety finding, compliance determination, comparative claim
about any detector or vendor, operator acceptance, or runtime authorization is asserted. No
released `1.2` architecture byte is modified by this workstream. The public remote is a
distribution channel with no scientific, safety, or acceptance authority.
