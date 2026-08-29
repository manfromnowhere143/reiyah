# Gate B claim audit, 2026-08-29

Document ID: `reiyah.gate-b.claim-audit-2026-08-29`

Version: `0.1.0`

Lifecycle status: `proposed`

Read-only audit of the Gate B result chain at commit `1447a7ed5a36168eaa656b62858feba04a5bd193`,
branch `gate-b-measurement`, worktree `/Users/danielwahnich/workspace/reiyah-gate-b`, clean and in
sync with `origin/gate-b-measurement`. The worktree is a linked worktree of the canonical Reiyah
repository: `git rev-parse --git-common-dir` resolves to
`/Users/danielwahnich/workspace/reiyah/.git`, and `AGENTS.md` is byte-identical to the canonical
copy at `sha256:60790cd1cc6edbe13748539e54e4d3f732b5fd4759fde37aeb126d997f990795`.

## 1. Determinism reproduction

Every script below was re-executed offline against the local intermediates and its output
compared byte for byte with the committed transcript. No input was refetched and no network was
contacted.

| Script | Transcript | Result |
|---|---|---|
| `result_d.py` | `result_d.txt` | byte-identical |
| `result_e.py` | `result_e.txt` | byte-identical |
| `result_i_worst_group_dependence.py` | `result_i.txt` | byte-identical |
| `result_k_evidence_cost_interval.py` | `result_k.txt` | byte-identical |
| `result_l_convergence.py` | `result_l.txt` | byte-identical |
| `audit_result_e_clustering.py` | `audit_result_e_clustering.txt` | byte-identical |
| `audit_result_h_accuracy_claim.py` | `audit_result_h_accuracy_claim.txt` | byte-identical |
| `audit_result_i_robustness.py` | `audit_result_i_robustness.txt` | byte-identical |
| `estimand_counterexamples.py` | `estimand_counterexamples.txt` | byte-identical, twice |

Determinism is established for the reproduced set. **Determinism is not validity.** Every script
reproduces its own arithmetic; none of that speaks to the estimand, the universe, the reference
process, or the identification questions below.

## 2. Validation-provenance states

Three distinct and non-interchangeable states are used:

| State | Meaning |
|---|---|
| `artifact_of_record` | Checked by the shipped offline production handler |
| `port` | Checked by a declared faithful reimplementation of a shipped handler |
| `spec_reimplementation` | Checked by an implementation derived from specification prose, with no shipped handler executed |

| Record set | Checker | State |
|---|---|---|
| 8,976 joint records | `tools/measure/semantic_joint_1_3.py`, self-declared "a faithful port of the derivation logic in tools/gate_a_1_2_0_science.py" | `port` |
| 3 worst-group records | `tools/measure/semantic_worst_group_1_3.py`, rules "derived from docs/MATHEMATICAL_SPECIFICATION.md section 5.7 and docs/SCIENTIFIC_CHARTER.md section 9.7" | `spec_reimplementation` |

**No Gate B record has ever been validated by the artifact of record.** The worst-group records
are one provenance level weaker than previously described, because the checker is not a port of a
shipped handler at all.

## 3. Claim table

Population for every measured row is the nuScenes validation split as cached in
`gt_val_cache.json`. Unit is the tracked instance unless stated. `AoR` is validation-provenance
state from section 2. No row is independently replicated: every row shares this repository's
code, this operator, and this machine, which is disclosed dependence, not replication.

| ID | Estimand | Unit | Comparator | Status | Principal limitation |
|---|---|---|---|---|---|
| A | Count and share of validation ground-truth objects removed by the official evaluation filter | object | none | `measured` | descriptive only |
| B | Whether the removal criterion is defined on range-sensor returns | rule | none | `measured` | documentary |
| C | Whether the published dependence literature inherits that filter | n/a | none | `rejected` | hypothesis refuted by its authors |
| D | Marginal `c` by operating point | box, superseded by K at instance | independence | `superseded` | point estimates only |
| E | Conditional `c` after class, range, visibility | instance | independence | `measured, narrowed` | non-identified per estimand note section 4 |
| F | Share of removed objects the lidar arm recovers | object | none | `measured` | descriptive |
| G | Evidence-cost consequence | `derived_arithmetic` | independence | **`withdrawn as stated`** | **no data path**, section 3.4, plus scope mismatch, estimand note 6.2 |
| H | Same-modality against cross-modality separation | object_track | independence | **`superseded`**; successor is **`inconclusive`** | Unit debt closed 2026-08-29. CenterPoint removed as excluded by Result J; three pairs remain; arms lack the required internal replication |
| H-acc | Joint-failure odds rise with model accuracy | n/a | none | `withdrawn` | no computation produced it |
| I | Worst-group `c` | instance | independence | `measured` | 34 tracked instances at the extremum; not identified; reference error unbounded |
| J | Worst-region generalisation across three pairs | instance | independence | `measured, narrows I` | one pair's extremum not established |
| K | `c` with instance-clustered intervals, both denominators | instance | independence | `measured` for `c`; **`withdrawn as stated`** for every evidence-cost column | see estimand note 6.2 |
| L | Convergence of conditional `c` on common support | instance | independence | `measured` | CI model, adjustment set not claimed sufficient |
| M | First `worst_group_evaluation` records, unknown-group rule fired | instance | none | `measured` | `spec_reimplementation` only |

### 3.1 Claims withdrawn or narrowed by this audit

| Claim | Prior state | New state | Ground |
|---|---|---|---|
| Evidence requirement is "+26.0%, 95% CI [25.0, 26.9]" | measured | **withdrawn as stated** | Corollary 3 scope: three-subsystem arity, miss-and-ghost requirement, safety-critic population, no confidence level in source |
| "97,596 examples per subsystem, CI [96,860, 98,332]" | measured | **withdrawn as stated** | same |
| Worst group costs "163.5%" more evidence | measured | **withdrawn as stated** | same |
| `RSS_BASELINE_N = 77460` is "RSS's own worked example" | asserted in code comment | **narrowed** to a Reiyah derivation | the number is absent from the primary text |
| Reiyah's `c` is the Eckhardt and Lee intensity function | asserted in prior session analysis, never committed | **withdrawn** | no primary text retained |
| Worst-group records validated by "a faithful port" | stated in handoff section 10 | **narrowed** to `spec_reimplementation` | the checker derives rules from specification prose |
| Any `c` value indicates protective diversity or common cause | implied by prior framing | **withdrawn** | CE-1 through CE-5 |

### 3.2 Claims confirmed by this audit

| Claim | Ground |
|---|---|
| `RSS Corollary 3 gives P <= 6 c p^2` | verbatim in retained primary text, custody S-01 |
| The 1.2.0 executable contract "could only be applied to the synthetic fixture it was written against" | verified directly against the released bytes, section 4 |
| Every reproduced script is deterministic | section 1 |

### 3.4 A second defect in Result G, found by adversarial reproduction

Result G was reproduced during this audit and is byte-identical to its transcript. That is not
reassurance. `tools/measure/result_g.py` **reads no data of any kind**: it contains no `sys.argv`
use, no `open`, and no `json.load`. Its coefficients live in two literal dictionaries,
`MARGINAL` and `CONDITIONAL`, hand-transcribed as rounded values from another result's printed
output. Result G reproduces byte-identically precisely **because it depends on nothing**.

The transcription is demonstrably lossy, and the loss is visible in the repository's own bytes:

| Path | Examples per subsystem at score 0.3 | Coefficient used |
|---|---|---|
| `result_g.txt` (withdrawn figure, retained) | 97,581 | the rounded literal `1.587` |
| `result_k.txt` (withdrawn figure, retained) | 97,596 | the recomputed `1.587483` |

The 15-example gap exists only because a rounded number was retyped into a script instead of
computed. The magnitude is immaterial; the provenance is not. Result G is arithmetic over
literals, not a measurement, and its declared status of `derived, bounded` overstated it.

This is the same class of defect as the previously withdrawn accuracy claim, where `result_h.py`
bound `MAP` and never read it. **Determinism did not catch it and cannot: a script with no
inputs is trivially deterministic.** Byte-identical reproduction is evidence about a script, not
about a measurement.

### 3.5 An executable reconciliation check

`tools/measure/check_claim_reconciliation.py` schema-validates
`evidence/claim-status-register-2026-08-29.json` and then fails closed if any live prose artifact
asserts a figure the register marks `forbidden`, unless that line also carries a withdrawal
marker. Retained transcripts under `evidence/measurement/` and the scripts under `tools/measure/`
are exempt by path prefix: they are historical bytes recording what a script printed, they are
never edited to match a later correction, and editing them would both destroy lineage and break
byte-identical reproduction.

The check was run **before** the correction and failed with 10 violations. Its first version had a
false-negative hole of its own. The register writes the withdrawn value `+26.0%` while prose
writes the same withdrawn figure as `26%`, and writes the withdrawn `163.5%` in bold, so sign
and precision variants escaped. After hardening it with surface-variant
expansion the same pre-correction tree failed with **24** violations across four documents, 14
more than the naive version found. The correction was then applied and the check passes.

A checker that passes before it has been shown to fail is not evidence.

## 4. The artifact-of-record blocker, verified against released bytes

`tools/measure/semantic_joint_1_3.py` exists because the artifact of record cannot accept a real
record. This audit verified that claim rather than accepting it.

1. `tools/gate_a_1_2_0_science.py` in this worktree is byte-identical to the frozen Gate A packet
   copy at `C_packet` `801eacf`: both are Git blob `a32c6cfa948ee1005a99937e54670991999db253`.
   It is a released Gate A byte.
2. It loads cleanly outside a launcher and exposes
   `joint_violations(instance, contracts, definition_registry)`.
3. Its guard, `executable_contract_binding_violations`, requires
   `matches[0].get("executable_contract") == expected["executable_contract"]` where `expected`
   comes from `FROZEN_EXECUTABLE_CONTRACT_DEFINITIONS`, a constant **inside the released module**,
   compared by exact equality, together with exact `version` and `owner_protocol_release_id`.
4. The bound `1.2.0` contract in `manifests/definitions/harbor-gate-a-definition-registry-1.2.0.json`
   at `/definitions/293/executable_contract` hardcodes synthetic subject identities, including
   `opportunity_set_ids` of `reiyah.opportunity-set.synthetic-joint-observed` and siblings,
   `object_ref.record_id` of `reiyah.object.synthetic_vehicle`, and synthetic
   `human_channel_ref` and `automation_channel_ref`.

Therefore the artifact of record can only validate the synthetic fixture it was frozen against.
Making it accept a real record requires changing `FROZEN_EXECUTABLE_CONTRACT_DEFINITIONS` inside a
released Gate A byte, which is prohibited in place and requires a Gate A science-module successor.

**Consequence.** `F7` is not closable from the Gate B lane. The `1.3.0` contract's own stated
rationale is confirmed correct, and the port was the only available path rather than a shortcut.
The honest state of every Gate B record is `port` or `spec_reimplementation` until a Gate A
successor exists. The substitution guard is working as designed and MUST NOT be weakened,
relaxed to a subset check, or made advisory to change this.

## 5. Disclosed dependence

No result in this repository is independently replicated. All results share this repository's
code, one operator, and one machine. Sibling programs in adjacent worktrees share compute with
this program, as recorded in `docs/GATE_B_SESSION_HANDOFF.md` section 9. Shared compute, code,
authorship, or evaluation is disclosed dependence and is never independent validation.

## 6. Non-claims

This audit creates no scientific support, no operator acceptance, no safety or compliance
finding, and no comparative claim. It records reproduction, provenance, and withdrawal states
only. No released `1.2` byte is modified.
