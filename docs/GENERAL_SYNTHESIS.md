# The independence assumption, measured: sensors, humans, and AI

Document ID: `reiyah.general-synthesis`

Version: `0.1.0`

Lifecycle status: `proposed`

This is the single reading of the whole measurement program. Each claim links to the result that
establishes it; every number is measured on public data and reproducible from this repository. The
non-claims at the foot are the exact boundary of what has and has not been shown. This document
supersedes nothing and modifies no released architecture byte; it ties the results together.

## The one claim

Every safety and ensemble argument for autonomous and AI systems rests on a single load-bearing
assumption: that redundant channels fail independently. It is almost never measured. Measured with
one estimand across three domains, it fails wherever the channels are of a similar kind, holds only
where they are genuinely different, understates the safety-evidence budget by a measurable factor,
and can be monitored live from the channels' outputs alone.

## The estimand, and why it travels

For two channels `A` and `B` observing the same opportunity, the coincidence coefficient of RSS
Definition 32 is

```
c = P(A fails and B fails) / [ P(A fails) * P(B fails) ].
```

`c = 1` is independence; `c > 1` means the channels fail together beyond independence. This is not
specific to sensors. `A` and `B` can be a camera and a lidar, a driver's observation and response,
or two language models judging the same question. The estimand is the same, so the finding travels.

The method is the same in every domain: take public per-item predictions, admit a channel only if
it reproduces its published accuracy, compute `c`, test it against every cheap dismissal, and
red-team it. Nothing is claimed that a public reproduction cannot recover.

## Domain one: two automation channels

On the nuScenes benchmark a camera detector and a lidar detector miss the same objects more than
independence predicts, `c = 1.151` after conditioning on class, range, visibility, weather and
motion ([Result L](RESULT_L_CONVERGENCE.md)), and it survives four independent robustness axes:
a second lidar ([M](RESULT_M_CROSS_DETECTOR_REPLICATION.md)), every operating threshold
([N](RESULT_N_THRESHOLD_ROBUSTNESS.md)), unmeasured confounding with an E-value of 2 to 3
([O](RESULT_O_SENSITIVITY_EVALUE.md)), and a second camera ([Q](RESULT_Q_CAMERA_AXIS_AND_MODALITY_GRID.md)).
Two sharpening results keep the method honest: the coefficient is smallest exactly where the sensors
jointly miss the most objects, so `c` alone cannot certify redundancy
([P](RESULT_P_COEFFICIENT_VS_ABSOLUTE.md)); and an inviting accuracy trend is mostly the marginal
arithmetic of `P`, not coupling ([R](RESULT_R_ACCURACY_COUPLING.md)). The workstream red-teams
itself ([threats](MEASUREMENT_THREATS_TO_VALIDITY.md)). The 2x2 modality grid shows two lidars
couple most (1.29), a camera and a lidar less (1.10 to 1.15).

## Domain two: the human

On the 100-Car Naturalistic Driving Study, in real conflicts the driver was looking forward at the
moment of the event two thirds of the time: observation is not detection
([human-channel H2](../human-channel/H2_GLANCE_AT_CONFLICT.md)). The human's own two channels,
looking and acting, fail together with the same coefficient the sensors do, `c = 1.46`
([H3](../human-channel/H3_OBSERVATION_RESPONSE_JOINT.md)). In modern Level 3 automation a
visual-manual distraction slows the human's takeover by a quarter
([H4](../human-channel/H4_DCPT_TAKEOVER.md)). And the cross-agent question no prior work had
measured: a validated detector against the driver gaze heatmap, taken to the automation's total
blindness with a clustered interval, gives `c = 0.98`, approximately independent
([H5](../human-channel/H5_CROSS_AGENT_JOINT.md), [H6](../human-channel/H6_TOTAL_BOTH_MISS.md)).

## Domain three: AI juries

Carried to LLM ensembles, self-consistency and multi-model cross-checking, the same law appears.
On MMLU, seven models fail together, models of one lineage more than of different lineages, and a
seven-model jury has the effective diversity of 3.6 independent models
([T](../llm-generalization/RESULT_T_LLM_INDEPENDENCE.md)). Agreement is an over-trusted signal:
when two models agree they are correct 65% of the time, and when all seven agree they are still
wrong 10% ([U](../llm-generalization/RESULT_U_AGREEMENT_RELIABILITY.md)). The finding replicates on
ARC-Challenge, where a six-model jury has the effective diversity of 1.6 and unanimity is wrong 37%
of the time ([W](../llm-generalization/RESULT_W_SECOND_BENCHMARK.md)), and on HellaSwag, where the
jury's effective diversity is 1.28 and the residual beyond shared difficulty is nearly zero, so the
lineage mechanism is benchmark-dependent while the marginal law is not
([Y](../llm-generalization/RESULT_Y_THIRD_BENCHMARK.md)).

## The law

| domain | same-kind pairing | cross-kind pairing |
|---|---|---|
| sensors | two lidars, c = 1.29 | camera x lidar, c = 1.10 to 1.15; human x machine, c ~ 1 |
| the human | eyes x hands, c = 1.46 | (n/a) |
| LLM juries | same family, c = 1.52 (MMLU), 1.87 (ARC), 2.43 (HellaSwag) | cross family, c = 1.29 (MMLU), 1.73 (ARC), 2.30 (HellaSwag) |

**Redundancy across genuinely different kinds buys independence; redundancy across similar kinds
does not.** Similar channels share a substrate and share their blind spots. Genuinely different
ones do not. The independence assumption is a load-bearing fiction wherever redundancy is claimed,
and it fails most for the systems that share the most.

## The consequence, corrected

Under RSS Corollary 3 ([S](RESULT_S_CORRECTED_SAFETY_CALCULUS.md)), holding the bound fixed, the
admissible per-channel error rate shrinks as `1/sqrt(c)`, so a validation campaign sized under
independence is undersized wherever `c > 1`. The evidence-budget percentages once derived from this
are withdrawn as stated and remain withdrawn: the corollary concerns a three-subsystem vote over miss
and ghost mistakes on safety-critic errors, and the measured two-channel detection-miss `c` does not
yet meet its five stated conditions. Reiyah reports `c` with its absolute-risk vector and no
evidence-budget percentage. The human-machine layer, at `c` about 1, adds essentially no correction.
Two coupled sensors provide the joint-failure protection of about one and a half independent
channels, and a seven-model jury the diversity of 3.6; both are illustrative effective-count
readings, not evidence budgets.

## The instrument

The coupling can be read live. A monitor that sees only the channels' outputs on an item, with no
ground truth, returns a calibrated probability that the ensemble is wrong, having learned the
coupling from a labeled calibration set ([V](../llm-generalization/RESULT_V_DEPLOYED_MONITOR.md)).
On held-out data it beats the naive agreement heuristic on every metric (AUC 0.845 against 0.719,
expected calibration error 0.015 against 0.045), and on unanimous items where the naive assumption
assigns zero risk it assigns the 11.6% the data actually carries. Fitted once and never refitted, it
reads a second jury of seven unseen families at an AUC of 0.853 against an in-domain ceiling of
0.856, so the coupling it learned is a property of redundancy, not of the channels it learned it
from; read on a second benchmark it falls to the naive baseline and its calibration breaks
([X](../llm-generalization/RESULT_X_MONITOR_TRANSFER.md)). The instrument is portable across
channels and must be calibrated on the task it reads. Carried to the driving channels as a
scene-level estimator of how many present objects both sensors missed, the coupling-aware form does
not beat a baseline that scales with how many objects the fusion reports
([Z](RESULT_Z_SCENE_BLINDNESS_MONITOR.md), `inconclusive`), and at the object level, on
detections only one channel reports, cross-channel context adds nothing to the detection's own
attributes ([AA](RESULT_AA_DISAGREEMENT_MONITOR.md)). A jointly missed object leaves no output, so
the sentence that the same form applies to two sensors is a conjecture with two failed tests, not a
result. What the measured coupling changes is the evidence calculus and the credit given to
redundancy; it has not been shown to be readable live from sensor outputs.

## What is proven, and what is open

Proven, and reproducible from this repository: the coefficient exceeds 1 for similar-kind redundancy
across three domains and two benchmarks; it is approximately 1 for a human and a machine; a campaign
sized under independence is undersized in the direction and ordering the coefficient gives, with no
percentage claimed; and a calibrated, output-only monitor corrects the over-confidence. Every result is `proposed`, self-checked against independent anchors,
robustness-tested, and red-teamed, with the marginal and conditional coefficients kept distinct and
the demonstrations labeled as demonstrations.

Open, and stated plainly: no independent external review has been retained, which is the honest
ceiling on current confidence and the next thing that would raise it; the driving results are
association after declared conditioning on public benchmarks, not a certificate about any deployed
system; the human results are on naturalistic and simulator data with an engaged human; and the
LLM monitor is validated across two juries on one benchmark, fails across benchmarks without
recalibration, and is not deployed. The law is stated to its
evidence and no further.

## Non-claims

A synthesis of measurements on public data, retained as `proposed`. No scientific support, safety
finding, compliance determination, comparative claim about any vendor, operator acceptance, or
runtime authorization is asserted. RSS is reproduced from retained primary text under fair use for
analysis. No released `1.2` architecture byte is modified by this workstream.
