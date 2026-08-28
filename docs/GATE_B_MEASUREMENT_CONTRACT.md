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
| D | superseded | Marginal joint-failure lift between camera and lidar detectors, 1.24 to 2.37 by operating point. |
| E | measured, narrowed | Conditioning on class, range and visibility removes 73.4% of that excess. Conditional lift 1.156, cluster-robust 95% interval [1.144, 1.166] at the tracked-instance unit. The published CMH of 4,924 is computed at the box unit; the design effect is 5.02, so the honest statistic is about 982 on 1 df. Conclusion stands, evidence narrowed. See [`AUDIT_INFERENCE_UNIT_AND_ACCURACY_CLAIM.md`](AUDIT_INFERENCE_UNIT_AND_ACCURACY_CLAIM.md). |
| F | measured | The lidar arm recovers 18.13% of the removed objects, closing Result B's upper bound. |
| G | derived | Required validation evidence scales as the square root of the lift, so the real cost is about 26% more evidence, not 59%. |
| H | measured | Across six detector pairs and three lidar architectures, same-modality and cross-modality pairs separate completely. |
| H-accuracy | withdrawn | "Joint-failure odds rise with the accuracy of both models." No computation produced this: `result_h.py` binds `MAP` and never reads it. Three non-independent odds ratios, permutation p 0.167, two points resting on an unvalidated accuracy figure, and two pairs at identical weaker-model accuracy differing by 2.26x. Retained with its refutation in [`AUDIT_INFERENCE_UNIT_AND_ACCURACY_CLAIM.md`](AUDIT_INFERENCE_UNIT_AND_ACCURACY_CLAIM.md). |

A seventh correction arrived later and is the most substantive: the measurements record
both-channel misses, not joint *silent* misses, which are not establishable from a source that
observes no warning and no fallback. See [`CONTRACT_CAUGHT_AN_ERROR.md`](CONTRACT_CAUGHT_AN_ERROR.md).

Eight claims were withdrawn or corrected during this work. Every one made the result smaller. They
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
