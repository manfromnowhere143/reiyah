# Gate B: Offline Measurement Contract

Document ID: `reiyah.gate-b-measurement-contract`

Version: `0.1.0`

Lifecycle status: `proposed`

## 1. Why this document exists

`docs/PRE_IMPLEMENTATION_GATE.md` section 5 states that Gate B is undefined and unauthorized, and
that any Gate B proposal requires a separate explicit operator instruction and its own reviewed
contract. This is that contract, in proposed status. It is not an acceptance and it does not
authorize itself.

Gate A established that Reiyah can state what would have to be true for a measurement to be
believable. It did so against deterministic synthetic fixtures, which is the correct order: the
contract is written before the data arrives, so the data cannot shape the contract. Gate B is the
next step on that path. It applies the contracts to measurements taken from public data.

## 2. Scope, stated narrowly

Gate B as proposed here authorizes exactly this and nothing adjacent to it:

1. reading publicly licensed dataset metadata and publicly released model prediction files;
2. deterministic offline computation over those bytes;
3. emission of typed evidence records under the existing scientific schemas; and
4. retention of those records with exact provenance under the source policy.

It does not authorize model training, model inference, live network dependence during validation,
private data ingestion, human subjects, deployment, physical control, a vehicle interface, a
safety case, or any operational claim. **No model is executed at any point.** The measurements
here consume prediction files that their authors published; the arithmetic is contingency tables
and stratified ratios.

### On GA-15

GA-15 requires that the architecture show no product runtime, live inference, deployment, physical
control, private ingestion, or publication machinery. Nothing in this contract introduces any of
those. Reading a published JSON file of model outputs and computing a contingency table over it is
not inference, in the same way that reading a published table of results is not.

This was initially misjudged in the other direction, and the misjudgement is recorded here rather
than quietly corrected: the measurement work was first placed in a separate repository on the
belief that GA-15 forbade it. That was over-cautious. The work belongs in Reiyah.

## 3. What the measurements found

Full transcripts are retained under `evidence/measurement/`. The tooling is at `tools/measure/`.

| Result | State | Finding |
|---|---|---|
| A | measured | The official nuScenes evaluation removes 12,694 of 134,565 validation ground-truth objects, 9.43%, before scoring any detector. Ten adversarial audits pass. |
| B | measured | The removal criterion is defined on range-sensor returns alone, so it is correlated with lidar failure by construction and not with camera failure. |
| C | rejected | Our hypothesis that the published dependence literature inherited this filter. It does not. |
| D | superseded, bounded | Marginal joint-failure lift between camera and lidar detectors, 1.24 to 2.37 by operating point. Point estimates only; Result K supplies instance-clustered intervals for every operating point and both denominators. |
| E | measured, narrowed | Conditioning on class, range and visibility removes 73.4% of that excess. Conditional lift 1.156, cluster-robust 95% interval [1.144, 1.166] at the tracked-instance unit. The published CMH of 4,924 is computed at the box unit; the design effect is 5.02, so the honest statistic is about 982 on 1 df. Conclusion stands, evidence narrowed. See [`AUDIT_INFERENCE_UNIT_AND_ACCURACY_CLAIM.md`](AUDIT_INFERENCE_UNIT_AND_ACCURACY_CLAIM.md). |
| F | measured | The lidar arm recovers 18.13% of the removed objects, closing Result B's upper bound. |
| G | **withdrawn as stated** | Historical, not for current use. The withdrawn statement and its figures are retained verbatim in [`result_g.txt`](../evidence/measurement/result_g.txt) and in [`claim-status-register-2026-08-29.json`](../evidence/claim-status-register-2026-08-29.json) under `reiyah.gate-b.claim.result-g-derivation`. Withdrawn on two independent grounds. First, provenance: `tools/measure/result_g.py` reads no data of any kind, and its coefficients are hand-transcribed rounded literals copied from another result's printed output, so Result G is arithmetic over literals rather than a measurement. Second, scope: the conversion of `c` into a validation-evidence multiplier misuses RSS Corollary 3. See [`ESTIMAND_RSS_DEFINITION_32.md`](ESTIMAND_RSS_DEFINITION_32.md) section 6. |
| H | measured | Across six detector pairs and three lidar architectures, same-modality and cross-modality pairs separate completely. |
| H-accuracy | withdrawn | "Joint-failure odds rise with the accuracy of both models." No computation produced this: `result_h.py` binds `MAP` and never reads it. Three non-independent odds ratios, permutation p 0.167, two points resting on an unvalidated accuracy figure, and two pairs at identical weaker-model accuracy differing by 2.26x. Retained with its refutation in [`AUDIT_INFERENCE_UNIT_AND_ACCURACY_CLAIM.md`](AUDIT_INFERENCE_UNIT_AND_ACCURACY_CLAIM.md). |
| I | measured | Worst-group dependence. Pooling hides it: conditional lift is 1.156 pooled but **6.946** in the worst eligible stratum, `car` at 0-20 m with `v80-100` visibility, simultaneous 95% [2.221, 11.671] over 120 eligible strata. Universe partitions exactly, 120 sufficient, 12 insufficient, 0 unknown. Survives absence, concentration and operating-point attacks. Evidence base is 34 tracked instances; quote only with the band. See [`RESULT_I_WORST_GROUP_DEPENDENCE.md`](RESULT_I_WORST_GROUP_DEPENDENCE.md). |
| J | measured | Worst-group dependence across three detector pairs. The worst **region** generalises: a close-range car is the worst eligible stratum, and the whole top three, for two camera-lidar pairs and one lidar-lidar pair. The worst **stratum** does not: two pairs put `v80-100` worst, one puts `v60-80`. One pair's extremum is not established, simultaneous lower bound 0.992. Narrows Result I. PointPillars gated at 29.54 against published 29.50; CenterPoint excluded for weak provenance. See [`RESULT_J_WORST_REGION_ACROSS_PAIRS.md`](RESULT_J_WORST_REGION_ACROSS_PAIRS.md). |
| K | measured for `c`; evidence-cost columns **withdrawn as stated** | The dependence estimate stands: marginal `c` at score 0.3 is 1.587, 95% CI [1.564, 1.612] over 8,976 independent tracked objects, and the OFFICIAL denominator gives a higher 1.630, consistent with Result B. This pays the interval debt Audit 1 raised against Results D and G. Every **evidence-cost** column of this result is withdrawn from current scientific use and is retained, with its exact superseded figures, in [`result_k.txt`](../evidence/measurement/result_k.txt) and in [`claim-status-register-2026-08-29.json`](../evidence/claim-status-register-2026-08-29.json) under `reiyah.gate-b.claim.evidence-cost-pooled`. The baseline constant is a Reiyah derivation from Corollary 3, not a figure published by the primary source, which states only "order of `10^5` examples". See [`ESTIMAND_RSS_DEFINITION_32.md`](ESTIMAND_RSS_DEFINITION_32.md) section 6 and [`PRIMARY_SOURCE_CUSTODY_2026-08-29.md`](PRIMARY_SOURCE_CUSTODY_2026-08-29.md) entry S-01. |
| L | measured | The conditional coefficient converges, and not to independence. On a common support of 131,722 rows the sequence is 1.602, 1.539, 1.326, 1.159, 1.155, 1.151; the last two admissible covariates move it by -0.004 each against -0.213 for range. Terminal 1.151, 95% CI [1.138, 1.160], excludes 1.0. Conditioning on `num_lidar_pts` moves it -0.044, ten times more, and is inadmissible as a mediator; that number is recorded as a trap, not an estimate. Closes the handoff's second open question. See [`RESULT_L_CONVERGENCE.md`](RESULT_L_CONVERGENCE.md). |
| M | measured | First `worst_group_evaluation` records from measured data, and the first real exercise of the unknown-group rule. Three records: by class (`identified`, worst is `car` at lift 1.994), by class and range (`identified`, worst is `car` 0-20 m at 4.723), and by motion state (**`unknown`**, no extremum reported, because 315 of 8,976 tracked objects appear in fewer than two keyframes so motion membership is not derivable; 67 of them are vulnerable road users). Ten semantic rules, 23 applicable rejection replays, all rejecting for their declared reason, 10 of 10 rules covered. Surfaced a `1.3` schema limit, see [`SCHEMA_1_3_FINDING_JOINT_SILENT_MISS.md`](SCHEMA_1_3_FINDING_JOINT_SILENT_MISS.md). |

A seventh correction arrived later and is the most substantive: the measurements record
both-channel misses, not joint *silent* misses, which are not establishable from a source that
observes no warning and no fallback. See [`CONTRACT_CAUGHT_AN_ERROR.md`](CONTRACT_CAUGHT_AN_ERROR.md).

Ten claims were withdrawn, corrected or narrowed during this work, one of them a defect in a robustness audit's own first version and one of them Result I's worst-stratum identity, narrowed by Result J. Every one made the result smaller. They
are retained with their refutations attached rather than deleted. The two most recent came from
an adversarial audit of this workstream's own statistics and are recorded in
[`AUDIT_INFERENCE_UNIT_AND_ACCURACY_CLAIM.md`](AUDIT_INFERENCE_UNIT_AND_ACCURACY_CLAIM.md).

## 4. Evidence eligibility

Under `docs/SOURCE_POLICY.md`, a URL is not retained evidence. The measurement inputs are treated
as follows:

| Input | Custody | Eligibility |
|---|---|---|
| nuScenes `v1.0-trainval_meta.tgz` | digest recorded, bytes not redistributed | pointer with verified digest |
| nuScenes-hosted detection baselines | digest recorded, bytes not redistributed | pointer with verified digest |
| CenterPoint predictions, third-party mirror | digest recorded, variant unconfirmed | pointer, **explicitly weaker provenance** |
| Derived measurement transcripts | retained in this repository | retained |

The dataset licence is CC BY-NC-SA 4.0, non-commercial. Payload bytes are therefore not
redistributed here; only derived measurements are retained. Analysed metadata hashes to
`sha256:db48746b10e3544d5ef619eaa3d687e3960626fe1b4422ed856711da5aa7325b`, verified against the
official source by exact size and five sampled byte ranges.

## 5. The known gap between contract and data

The Gate A `1.2` joint-performance contract names its two channels `human_channel` and
`automation_channel`. The measurements above compare two machine channels. **The contract cannot
express that comparison without misusing a field name**, which is a representational limit found by
applying the schema to real data rather than to fixtures.

The remedy is a `1.3` successor that replaces the two named properties with a roles array carrying
an explicit channel role. The underlying mathematics is unaffected: cell reconciliation, unknown
propagation and the worst-group partition are all indifferent to what a channel is. This is
recorded as a required successor change and is not applied to any released `1.2` byte.

## 6. Non-claims

This contract creates no scientific support, no safety finding, no compliance determination, no
comparative claim about any detector or vendor, and no operator acceptance. It does not claim that
nuScenes is wrong, that any published number is invalid, or that RSS is unsound. It records what a
documented filter removes, what four published detectors do per object, and what follows
arithmetically.

Advancing any measurement here beyond `proposed` requires the evidence admission process, an
authorized operator decision, and independent review, none of which this document supplies.
