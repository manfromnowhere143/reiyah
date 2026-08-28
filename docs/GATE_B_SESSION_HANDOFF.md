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
| Branch | `gate-b-measurement`, clean, pushed, 14 commits |
| Schema successor | `schemas/v1.3/`, **proposed** |
| Executable contract successor | `manifests/definitions/joint-silent-miss-contract-1.3.0.json`, **proposed, not in the registry** |
| Real records | 8,976 built, **0 semantic violations** |
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
- Camera and lidar failures are not independent. Marginal lift 1.587 at score 0.3, conditional
  1.156 after stratifying on class, range and visibility, CMH 4,924 on 1 df.
- Required validation evidence scales as **sqrt(c)**, so the cost is about **26% more evidence**,
  not 59%.
- Across six detector pairs, same-modality and cross-modality separate completely, and
  joint-failure odds **rise with the accuracy of both models**: 7.01, 15.86, 31.99.

## 5. Corrections, all of them

Nine claims were withdrawn or narrowed. Every one made the result smaller. All remain in place with
their refutations attached; **do not tidy them away**.

| Claim | Verdict |
|---|---|
| Censoring biases dependence toward independence | false, it inflates about 3% |
| Dependence is worst at long range | false, worst up close |
| Qiu's published estimate inherits the filter | false, independent pipeline |
| Zero lidar points implies undetectable | false, 18.13% recovered |
| Quote the conditional coefficient against RSS | wrong quantity for that bound |
| Evidence scales linearly in c | false, it scales as sqrt(c) |
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
also the correct statistical unit** — treating fifteen near-identical boxes of one tracked object
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

## 10. The next smallest action

Release the `1.3.0` executable contract into the definition registry so the **shipped science
module**, not our faithful port, can execute these checks. `tools/measure/semantic_joint_1_3.py`
is a port with the guard split into policy and subject per
[`EXECUTABLE_CONTRACT_1_3_PROPOSAL.md`](EXECUTABLE_CONTRACT_1_3_PROPOSAL.md); it is not the real
validator, and the records are therefore validated by a faithful reimplementation rather than by
the artifact of record.

**Do not weaken the substitution guard to get there.** It may not be removed, relaxed to a subset
check, or made advisory. If the choice is between a validator that refuses real data and one that
can be talked into anything, keep the refusal.

After that, in order:

1. A second independent camera detector. All three cross-modality pairs share Mapillary, so that
   column has no internal replication, and no modern camera-only nuScenes predictions are published
   anywhere. Obtaining one means running inference.
2. Convergence of the conditional coefficient, which fell 1.525, 1.318, 1.156 without obviously
   converging. Stratify additionally on object size, truncation and motion state. **Careful:**
   `num_lidar_pts` is arguably a mediator of lidar failure rather than a confounder, so
   conditioning on it may delete the path being measured. Decide which it is before using it.
3. `worst_group_evaluation` on real data, now that vulnerable road users are representable. 1,994
   of the 8,976 tracked objects are vulnerable road users, and the unknown-group rule has never
   been exercised against anything real.

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
