# Gate B Session Handoff

Read `AGENTS.md` first, then this. Resolve every state from the exact artifacts named here, never
from this prose. This file is a continuation contract, not authority.

## 1. Where you are, and where this work is

**This work is not on the branch you are probably sitting on.**

| Worktree | Branch | Contents | Uncommitted |
|---|---|---|---|
| `~/workspace/reiyah` | `gate-a-1.2.1-continuity` | the 1.2.1 continuity workstream, **another owner** | 28 paths, leave them alone |
| `~/workspace/reiyah-gate-b` | `gate-b-measurement` | everything described below | 0, all pushed |

```sh
cd ~/workspace/reiyah-gate-b && git log --oneline -1     # expect 2ee1693 or later
```

Branch cut from released `d42d4d2`, so no `1.2.0` byte is touched and the `1.2.1` workstream is
undisturbed. **Never switch branches inside `~/workspace/reiyah`**: that would drag 28 uncommitted
paths belonging to someone else. Use the worktree.

Published at `https://github.com/manfromnowhere143/reiyah/tree/gate-b-measurement`.

## 2. What this workstream is

Gate A established that Reiyah can state what would have to be true for a measurement to be
believable, tested against 611 deterministic synthetic fixtures. Gate B applies those contracts to
measurements taken from public data. The contract authorizing it is
[`GATE_B_MEASUREMENT_CONTRACT.md`](GATE_B_MEASUREMENT_CONTRACT.md), lifecycle `proposed`.

**No model is executed anywhere in this work.** It reads publicly licensed dataset metadata and
publicly released prediction files and computes contingency tables. GA-15 is not engaged.

## 3. Exact state

| Item | State |
|---|---|
| Branch | `gate-b-measurement`, clean, **8 commits unpushed** as of 2026-08-29 |
| Schema successor | `schemas/v1.3/`, **proposed** |
| Executable contract successor | `manifests/definitions/joint-silent-miss-contract-1.3.0.json`, **proposed, not in the registry, and NOT REGISTRABLE FROM THIS LANE**; see section 10 |
| Real records | 8,976 built, **0 semantic violations**, validated by a **port**; the 3 worst-group records by a **spec reimplementation**, which is weaker still |
| Claim status | machine-readable in [`claim-status-register-2026-08-29.json`](../evidence/claim-status-register-2026-08-29.json); enforced by `tools/measure/check_claim_reconciliation.py` |
| Evidence-cost figures | **withdrawn as stated**, retained with lineage; see [`ESTIMAND_RSS_DEFINITION_32.md`](ESTIMAND_RSS_DEFINITION_32.md) section 6 |
| Reference-error identification | **`unknown`**; no blinded reannotation performed; solver exercised on synthetic fixtures only |
| Operator acceptance | none |
| Scientific support | none |
| Released `1.2` bytes modified | none |

## 4. What was measured

Transcripts in `evidence/measurement/`, tooling in `tools/measure/`. Results A through H are
tabulated in [`GATE_B_MEASUREMENT_CONTRACT.md`](GATE_B_MEASUREMENT_CONTRACT.md) section 3. The
headline facts:

- The official nuScenes evaluation removes **12,694 of 134,565** validation ground-truth objects,
  **9.43%**, before scoring any detector. Ten adversarial audits pass, including one that
  reproduces nuScenes' published 6,019 validation samples exactly.
- A per-object matcher reproduces published mAP on four detectors: Megvii 51.97 against 51.90,
  Mapillary 29.58 against 29.80, PointPillars 29.54 against 29.50. CenterPoint reconstructs 61.59
  and is **not validated** against a confirmed figure.
- Redundancy is weakest on the close-range car. Pooled conditional lift 1.156, worst eligible
  group 6.946 with a simultaneous band of [2.221, 11.671]. Across three detector pairs the
  worst region is a close-range car every time; the exact stratum is pair-specific. See
  [`RESULT_I_WORST_GROUP_DEPENDENCE.md`](RESULT_I_WORST_GROUP_DEPENDENCE.md) and
  [`RESULT_J_WORST_REGION_ACROSS_PAIRS.md`](RESULT_J_WORST_REGION_ACROSS_PAIRS.md).
- Camera and lidar failures are not independent. Marginal lift 1.587 at score 0.3, conditional
  1.156 after stratifying on class, range and visibility, cluster-robust 95% interval
  [1.144, 1.166] at the tracked-instance unit. The CMH of 4,924 was computed at the box
  unit; design effect 5.02, so the honest statistic is about 982 on 1 df.
- **WITHDRAWN, historical.** This bullet formerly converted the measured dependence into a
  validation-evidence budget. Every such figure is withdrawn from current scientific use. The
  superseded values are retained in
  [`claim-status-register-2026-08-29.json`](../evidence/claim-status-register-2026-08-29.json)
  and in the Result G, I, J and K transcripts. RSS Corollary 3 is a three-subsystem
  majority-vote bound over safety-critic miss **and** ghost mistakes; it is not a validated
  conversion from a measured two-channel detection-miss `c` into a validation-mile or
  evidence-budget multiplier. See
  [`ESTIMAND_RSS_DEFINITION_32.md`](ESTIMAND_RSS_DEFINITION_32.md) section 6 for the five
  conditions that would have to hold before any such figure returns.
- Across six detector pairs, same-modality and cross-modality separate completely.
  The former claim that joint-failure odds **rise with the accuracy of both models**
  (7.01, 15.86, 31.99) is **withdrawn**: no computation produced it, the trend has a
  permutation p of 0.167 on three non-independent points, and two pairs at identical
  weaker-model accuracy differ by 2.26x. See
  [`AUDIT_INFERENCE_UNIT_AND_ACCURACY_CLAIM.md`](AUDIT_INFERENCE_UNIT_AND_ACCURACY_CLAIM.md).

## 5. Corrections, all of them

Eleven claims were withdrawn or narrowed. Every one made the result smaller. All remain in place
with their refutations attached; **do not tidy them away**. The two most recent are in
[`AUDIT_INFERENCE_UNIT_AND_ACCURACY_CLAIM.md`](AUDIT_INFERENCE_UNIT_AND_ACCURACY_CLAIM.md).

| Claim | Verdict |
|---|---|
| Censoring biases dependence toward independence | false, it inflates about 3% |
| Dependence is worst at long range | false, worst up close |
| Qiu's published estimate inherits the filter | false, independent pipeline |
| Zero lidar points implies undetectable | false, 18.13% recovered |
| Quote the conditional coefficient against RSS | wrong quantity for that bound |
| Evidence scales linearly in c | superseded twice: the sqrt(c) replacement is itself now **withdrawn as stated**, see the register |
| GA-15 forbids this work living in Reiyah | false, over-cautious; work folded back in |
| Both-channel miss is a joint **silent** miss | false, silence is not establishable here |
| Every record is `nonidentifiable_unknown` | false, unknown does not propagate from an unreached operand |

**Wherever Results D, E, G or H are described as measuring joint *silent* misses, the word silent
is wrong and must be removed.** They measure both-channel misses. RSS Definition 32 concerns joint
subsystem error rather than silence, so that work is unaffected in substance.

## 6. What the contract taught us

Five refusals, each correct, each revealing that the usage was wrong rather than the contract.

1. Channel roles were encoded in property names, so machine against machine was inexpressible.
2. `object_ref.record_kind` was pinned to `vehicle_object`, so a pedestrian could not be an
   opportunity. **The most serious**, for a mission naming vulnerable road users.
3. Eight sections rejected a non-observed state, so a partial measurement was unrepresentable,
   which inverts Reiyah's own status model one level up.
4. Silent joint miss requires warning and fallback, which this source does not observe.
5. Unknown propagation is conditional on the operand being reached.

Limits 1 to 3 were found by pointing the schema at real data. Limit 4 by reading the semantic
rules. **Limit 5 only surrendered to executing them**, which is why executing matters.

Details: [`SCHEMA_1_3_FINDINGS.md`](SCHEMA_1_3_FINDINGS.md),
[`CONTRACT_CAUGHT_AN_ERROR.md`](CONTRACT_CAUGHT_AN_ERROR.md),
[`FIRST_SEMANTICALLY_VALIDATED_MEASUREMENT.md`](FIRST_SEMANTICALLY_VALIDATED_MEASUREMENT.md).

## 7. The unit, which matters more than it looks

The contract requires every row to bind the same `object_ref` and `occurred_at` to be strictly
increasing. That is not a limitation: an opportunity set is **one common object over a time
series**, as section 5.11 of the mathematical specification states.

nuScenes objects are tracked, so 8,976 instances at mean 15 observations fit exactly. **This is
also the correct statistical unit**: treating fifteen near-identical boxes of one tracked object
as independent is the clustering error in our own traps table. The contract demanded the right unit
before we thought to apply it. Any future analysis must cluster on `instance_token`.

## 8. Reproducing

```sh
cd ~/workspace/reiyah-gate-b
python3 tools/measure/fetch_predictions.py predictions        # ~250 MB, HTTP range requests
curl -o meta.tgz https://motional-nuscenes.s3.amazonaws.com/public/v1.0/v1.0-trainval_meta.tgz
shasum -a 256 meta.tgz    # must be db48746b10e3544d5ef619eaa3d687e3960626fe1b4422ed856711da5aa7325b
python3 tools/measure/build_gt_cache.py gt_val_cache.json < meta.tgz
python3 tools/measure/match.py gt_val_cache.json predictions/megvii_val.json matched_megvii.json --validate 51.9
python3 tools/measure/match.py gt_val_cache.json predictions/mapillary_val.json matched_mapillary.json --validate 29.8
python3 tools/measure/build_joint_records_per_instance.py gt_val_cache.json \
    first=matched_mapillary.json second=matched_megvii.json joint_records_per_instance.jsonl
python3 tools/measure/semantic_joint_1_3.py joint_records_per_instance.jsonl
```

No GPU. Large intermediates are gitignored and reproducible. **Never use a bare pipe over an
unreliable connection**: one silently corrupted transfer was caught only because `gsutil cp`
verifies CRC32C, and a pipe would have carried it into the analysis.

**`gcloud` needs interactive reauth** (`gcloud auth login`). Not blocking, because the official
Motional S3 source is public and gives better provenance anyway.

## 9. Compute, already built

`sentinel-gpu` in `us-west1-a`: `g2-standard-8`, NVIDIA L4 24 GB, currently TERMINATED, with
`/datasets/nuscenes-full` holding the complete trainval set including 342 GB of sweeps. About one
dollar an hour running, near zero stopped. **Stop it when not computing.** Not needed for anything
described above.

Its torch is 2.9.1 with CUDA 12.9, while mmcv 2.1.0 ships wheels only to cu121. **Do not downgrade
torch on that box**, it belongs to Sentinel. Use a container if inference is ever required.

## 9a. Session of 2026-08-28, what changed and what to distrust

Seven results and audits were added in one session. Read this section before trusting any
number quoted elsewhere in this file, because two long-standing figures were corrected.

**Corrected, do not use the old values.**

- Result E's CMH of 4,924 was computed at the box unit. The design effect is 5.02, so the
  honest statistic is about 982 on 1 df. The point estimate 1.156 is unchanged and the
  conclusion stands. `audit_result_e_clustering.py`.
- "Joint-failure odds rise with the accuracy of both models" is **withdrawn**. No
  computation produced it: `result_h.py` binds `MAP` and never reads it. Permutation p is
  0.167 on three non-independent points, two of which rest on CenterPoint's unvalidated
  accuracy, and two pairs at identical weaker-model accuracy differ by 2.26x.
  `audit_result_h_accuracy_claim.py`.
- Result I's worst-stratum identity is **pair-specific**, narrowed by Result J. Its
  regional finding holds across all three pairs.

**Added.**

| Result | One line |
|---|---|
| I | Pooling hid it: worst eligible group `car` 0-20 m `v80-100` at lift 6.946, simultaneous 95% [2.221, 11.671], against a pooled 1.156. Survives four attacks. Evidence base is 34 instances; never quote without the band. |
| J | The worst *region* generalises across three pairs, the worst *stratum* does not. One pair's extremum has a lower bound of 0.992 and is **not established**. |
| K | The marginal `c` at the instance unit with an interval, which stands. Its evidence-cost columns are **withdrawn as stated**; the superseded figures are retained in the transcript and the register. Pays Audit 1's interval debt for D and G. |
| L | The conditional coefficient **converges and not to independence**: 1.151, 95% CI [1.138, 1.160], on a common support. Closes open question 2. |
| M | First `worst_group_evaluation` records from measured data. The unknown-group rule fires for real. Closes open question 3. |

**A trap now on the record.** Conditioning on `num_lidar_pts` moves the coefficient
-0.044, ten times more than any admissible covariate. It is the lidar return itself and
sits on the path being measured. It looks like convergence and is mechanical. Never use
it. See [`RESULT_L_CONVERGENCE.md`](RESULT_L_CONVERGENCE.md).

**Two defects found in this session's own work, both recorded rather than quietly fixed.**

1. The first robustness script coerced an ineligible stratum into a numeric rank of 110
   and reported a false FAIL. The coercion was removed; the criterion was not loosened.
   Recorded in [`RESULT_I_WORST_GROUP_DEPENDENCE.md`](RESULT_I_WORST_GROUP_DEPENDENCE.md).
2. The first worst-group mutation set reported nine FAILs that were mutations inapplicable
   to their record, not rule defects. The set is now precondition-aware and the run fails
   unless every rule is rejected by at least one applicable replay somewhere.

**A new `1.3` schema limit.** `joint_silent_miss` is a bare `$ref` where its seven sibling
sections are a `oneOf` with `nonObservedMeasurement`, so a record that did not measure
joint silent misses cannot be expressed without fabricating four identities. The section
is omitted, the whole-record schema failure is retained as the evidence, and a one-line
`1.4` successor change is proposed. See
[`SCHEMA_1_3_FINDING_JOINT_SILENT_MISS.md`](SCHEMA_1_3_FINDING_JOINT_SILENT_MISS.md).
**Do not apply it to a released `1.3` byte.**

**Reproducibility.** `matched_pointpillars.json` was rebuilt and gated at 29.54 against a
published 29.50 before use. All `matched_*.json` are gitignored; regenerate with
`tools/measure/match.py` and never admit a match set that fails its `--validate` gate.
CenterPoint remains excluded for weak provenance and is not readmitted.

**Every new tool is seeded and re-runs byte-identically.** If one does not, stop and find
out why before trusting anything it produced.

## 10. The next smallest action

**The former first item is REVOKED as unreachable from this lane, on verified grounds.** It read:
release the `1.3.0` executable contract into the definition registry so the shipped science module
rather than a port can execute these checks. The 2026-08-29 audit established that this cannot be
done here, and the reason is now bound to bytes rather than inferred.

`tools/gate_a_1_2_0_science.py` in this worktree is Git blob
`a32c6cfa948ee1005a99937e54670991999db253`, byte-identical to the frozen Gate A `C_packet` copy at
`801eacf`. Its guard `executable_contract_binding_violations` compares the registry entry against
`FROZEN_EXECUTABLE_CONTRACT_DEFINITIONS`, a constant **inside that released module**, by exact
equality. The bound `1.2.0` contract hardcodes synthetic subject identities:
`reiyah.opportunity-set.synthetic-joint-observed` and siblings, `reiyah.object.synthetic_vehicle`,
and synthetic human and automation channel refs. **The artifact of record can therefore only ever
validate the synthetic fixture it was frozen against.** Registering a `1.3.0` contract would
require changing a released Gate A byte, which is prohibited in place and needs a Gate A science
module successor. That is another lane.

So the `1.3.0` proposal's own diagnosis is confirmed correct, the port was forced rather than
chosen, and the honest validation state of every Gate B record is `port` or `spec_reimplementation`
until a Gate A successor exists. See [`CLAIM_AUDIT_2026-08-29.md`](CLAIM_AUDIT_2026-08-29.md)
section 4.

**Do not weaken the substitution guard.** It may not be removed, relaxed to a subset check, or
made advisory. It is working exactly as designed: it is refusing real data because the contract it
was frozen against names a fixture. If the choice is between a validator that refuses real data and
one that can be talked into anything, keep the refusal.

The next smallest actions that ARE reachable from this lane, in order:

1. Restate Result H at the instance unit. Audit 1 required it for D, G and H; K did D and G, H is
   still box-unit and its six pairwise figures still carry no interval.
2. A second independent camera detector. All three cross-modality pairs share Mapillary, so that
   column has no internal replication, and no modern camera-only nuScenes predictions are published
   anywhere. Obtaining one means running inference.
2. **CLOSED** by [`RESULT_L_CONVERGENCE.md`](RESULT_L_CONVERGENCE.md). On a common support the
   sequence converges to 1.151, 95% CI [1.138, 1.160], excluding independence. Weather and motion
   state each move it by only -0.004. `num_lidar_pts` was decided **inadmissible**: it is the lidar
   return itself and conditioning on it blocks the measured path, moving the estimate -0.044 for
   mechanical reasons. Object size and truncation are not in the cache and remain untested.
3. **CLOSED.** `worst_group_evaluation` now has three records built from measured data, and the
   unknown-group rule has fired against something real: grouping by motion state yields
   disposition `unknown` with no extremum, because 315 of 8,976 tracked objects appear in fewer
   than two keyframes and their motion membership is not derivable. 67 of those are vulnerable
   road users. Ten semantic rules with 23 rejection replays, all rejecting for their declared
   reason. Tools `build_worst_group_records.py` and `semantic_worst_group_1_3.py`; records at
   `evidence/measurement/worst-group-records.jsonl`. It surfaced a new `1.3` limit, recorded in
   [`SCHEMA_1_3_FINDING_JOINT_SILENT_MISS.md`](SCHEMA_1_3_FINDING_JOINT_SILENT_MISS.md).

## 11. Standards

Plain reviewable Markdown, JSON and deterministic scripts. **No em dash in any repository
document.** Every claim carries the epistemic state of its evidence. A computed number is not a
measurement, a passing validator is not acceptance, a checksum is not truth, and generated prose is
not evidence. Failures are information: keep them as diagnostics, open findings, contradictions or
retractions, and never weaken a check to make a run pass.

## 12. Required closeout

State, separately and from exact records: worktree, branch, commit, and cleanliness; which schemas
and contracts are proposed against released; how many records validate and against which validator,
the ported one or the shipped one; every claim withdrawn since the last handoff; and the next
smallest authorized action.
