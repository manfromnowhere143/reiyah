# HARBOR Status and Unknown-State Model

Document ID: `reiyah.status-model`

Version: `1.2.0`

Lifecycle status: `proposed`

Normative scope: Gate A architecture artifacts and deterministic validation fixtures

## 1. Purpose

This document defines the statuses that Reiyah records. It prevents an absent or invalid
observation from becoming a negative value, prevents an inconclusive result from becoming a
failed result, and prevents architecture completion from becoming operator acceptance.

The keywords **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, and **MAY** are normative.
All examples are informative unless explicitly marked normative.

## 2. Independent state axes

An artifact MAY carry values from several axes, but an implementation MUST NOT substitute a
value from one axis for a value from another.

| Axis | Question answered | Examples |
| --- | --- | --- |
| Epistemic state | Is a particular field usable as an observation or estimate? | `observed`, `missing`, `sensor_invalid` |
| Lifecycle status | Where is a claim, experiment, result, or evidence object in its review lifecycle? | `proposed`, `running`, `supported` |
| Validity disposition | Is an object eligible for a declared analysis and why? | eligible, excluded with reason, validity unknown |
| Gate completion | Are all required architecture artifacts present and deterministically valid? | incomplete, architecture-complete |
| Operator decision | Did an authorized human decide on the exact hash-bound artifact set? | unaccepted, accepted, rejected, deferred |
| Integrity state | Do recorded bytes match a recorded digest? | verified, mismatch, not checked |
| Distribution event | What did the publisher assert about one exact publication act? | not published, asserted unverified |
| Independent transport | Did a separately authorized observation retain the exact remote bytes? | `not_evaluated` before a record; record outcomes `independently_verified`, `failed`, or `inconclusive` |

Passing validation is an integrity signal. It is not scientific support, independent review,
or operator acceptance.

## 3. Epistemic states

Every scalar or structured measurement that may be unavailable MUST use the discriminated
measurement representation defined in `schemas/common.schema.json`. A bare JSON `null`, an
empty string, a sentinel number, or a default Boolean MUST NOT represent epistemic state.

| State | Normative meaning | Value allowed? |
| --- | --- | --- |
| `observed` | A value was obtained inside the declared measurement and validity procedure. | Exactly one typed `value` is REQUIRED. |
| `missing` | A value was expected and in principle measurable, but is absent. | `value` is prohibited; a reason is REQUIRED. |
| `unmeasured` | The protocol did not make or retain this measurement. | `value` is prohibited; a reason is REQUIRED. |
| `out_of_distribution` | The input is outside the declared support or transfer boundary. | `value` is prohibited; a reason and boundary reference are REQUIRED by the governing protocol. |
| `sensor_invalid` | A producing sensor or acquisition chain failed a declared validity check. | `value` is prohibited; a reason and check reference are REQUIRED by the governing protocol. |
| `abstained` | A decision or estimator deliberately declined to emit a value under a declared abstention rule. | `value` is prohibited; a reason and rule reference are REQUIRED by the governing protocol. |

These states are mutually exclusive for one measurement at one recorded time. A later
correction MUST create a new version or correction record; it MUST NOT silently rewrite the
original state.

### 3.1 Zero and false are observations

Numeric zero and Boolean false are permitted only in an `observed` measurement whose typed
value is actually zero or false. The following coercions are prohibited:

- `missing` to `0`, `false`, negative, normal, safe, or ready;
- `unmeasured` to `0`, a population mean, or an imputed subgroup;
- `out_of_distribution` to a confident in-distribution label;
- `sensor_invalid` to the last valid value without a separate, declared derived record; and
- `abstained` to the highest-ranked class or a default action.

### 3.2 Derived values and imputation

Gate A does not authorize operational imputation. A future research protocol MAY propose a
derived or imputed value only if it records the original measurement unchanged, gives the
derived value a different identifier, names the transformation, parameters, provenance, and
uncertainty, and evaluates results with and without that transformation. The derived record
MUST NOT change the epistemic state of the source record.

An observed categorical latent belief records the exact normalization tolerance owned by its
protocol release; the record cannot choose a looser value. Gate A fixes
`belief_normalization_policy.absolute_tolerance` and every observed belief's
`belief.normalization_policy_binding.absolute_tolerance` to `0.000001`, with absolute error
from one required to be no greater than that value. The remaining policy identity, release,
scope, comparison, and authorization fields must also match exactly.

## 4. Lifecycle statuses

The following strings are the complete Gate A lifecycle vocabulary. They are distinct even
when downstream reporting would prefer to combine them.

| Status | Normative meaning |
| --- | --- |
| `proposed` | Authored but neither preregistered nor accepted as supported. Generated content begins here. |
| `exploratory` | Analysis or design is explicitly hypothesis-generating and may change. |
| `preregistered` | Protocol and decision rules were fixed and retained before the declared observation boundary. |
| `running` | Authorized execution has begun and has not reached a result disposition. Gate A itself authorizes no runtime execution. |
| `blocked` | Progress is prevented by a recorded dependency or authority gap; no result is implied. |
| `invalid` | A protocol, observation, analysis, or result violated a declared validity requirement. |
| `null` | A valid analysis produced a result consistent with its declared null criterion. This is not missing or failed execution. |
| `inconclusive` | The valid retained evidence does not resolve the preregistered decision criterion. |
| `failed` | A declared process or test failed; this does not by itself contradict a scientific claim. |
| `supported` | Retained evidence met a preregistered support criterion within a stated scope. It is not proof or universal truth. |
| `contradicted` | Retained evidence met a preregistered contradiction criterion within a stated scope. |
| `replicated` | A distinct retained study met its declared replication criterion and names the study replicated. |
| `corrected` | A discoverable successor corrects an earlier record without erasing it. |
| `retracted` | The record remains discoverable but is withdrawn from active evidentiary use with a rationale. |

### 4.1 Usage rules

1. Producers MUST store the exact status; summary views MAY group statuses only when they
   preserve the original and disclose the grouping rule.
2. `null`, `inconclusive`, and `failed` MUST NOT be interchanged.
3. `invalid` MUST NOT be included in an estimand unless a preregistered sensitivity analysis
   explicitly targets invalid records; it remains discoverable either way.
4. `supported`, `contradicted`, and `replicated` require retained evidence and declared
   criteria. Model review, signatures, checksums, tests, or consensus alone cannot confer
   them.
5. A correction or retraction MUST be a new immutable artifact version for the same logical
   record. Its lifecycle event MUST bind the existing predecessor's distinct artifact ID,
   same logical record ID, same record kind and schema, older version, repository path, and
   SHA-256 digest and byte size. The predecessor history is the successor history's exact
   append-only prefix, and the predecessor remains discoverable.
6. Status changes MUST be new auditable records or new immutable releases. In-place status
   mutation of a released manifest is prohibited.
7. A claim, experiment, result, or evidence object with `invalid`, `null`, `inconclusive`,
   `failed`, `supported`, `contradicted`, `replicated`, `corrected`, or `retracted` status MUST
   bind retained evidence for that exact version. An evidence gap is compatible with
   `proposed`, `exploratory`, `preregistered`, `running`, or `blocked`, but cannot substantiate
   an evidentiary disposition. Every identifier in a binding declared `retained` MUST resolve
   to an evidence object whose own basis is retained and resolves to the source ledger. A
   result metric inherits its result-level binding; each lifecycle event separately names
   versioned evidence references for that event. Bare evidence IDs are prohibited. The exact
   protocol release's `evidence_binding_policy` determines which active evidence statuses are
   bindable. Proposed, exploratory, preregistered, running, blocked, null, and retracted evidence is
   never current-bindable. A corrected evidence artifact is current-bindable only as the
   validated successor, never by referencing a predecessor named in `prior_artifact`. A
   `supported`, `contradicted`, or `replicated` consumer MUST bind evidence with a `valid`
   validity assessment. At least one compatible witness is also required: `invalid`,
   `inconclusive`, `failed`, `contradicted`, and `replicated` consumers require the matching
   evidence status; `supported` permits `supported` or `replicated`; and `null` requires
   `supported` evidence that meets the frozen null decision criterion. Corrected evidence may
   supplement but cannot be the sole support-like witness. Correction and retraction events
   may cite any otherwise eligible active evidence. These constraints prevent status
   laundering but do not establish truth, sufficiency, independence, or authority.
8. A non-claim is a normative scope boundary. In the Gate A register it MUST remain
   `proposed` and use the distinct `not_applicable` evidence state rather than pretending that
   empirical evidence supports or falsifies the boundary.
9. Gate A claim-register items are proposals only. Claims use `evidence_gap`; non-claims use
   `not_applicable`. This register does not advertise terminal claim transitions without a
   future versioned claim-record history contract.
10. Gate A source records remain `proposed`. Retained bytes and a matching digest establish
    identity and availability, not scientific support or replication.

### 4.2 Transition constraints

Lifecycle transitions depend on entity type and the governing protocol. A protocol MUST
declare an allowed transition table before execution. At minimum:

- a proposed design may become exploratory or preregistered;
- only a preregistered or explicitly exploratory study may become running;
- only a running, valid analysis may directly yield `null`, `inconclusive`, `supported`, or
  `contradicted`;
- `failed` describes process failure, while `invalid` describes violated validity;
- `replicated` requires a separate result reference;
- any non-retracted record may be followed by a `corrected` successor; and
- any released record may be retracted, but the record and relation remain discoverable.

The schemas validate vocabulary and required relations. Repository validation MUST resolve
the record's exact `protocol_release_id` and derive the permitted entity/status pair from that
release's versioned `lifecycle_transition_policy`; a hardcoded validator table is not status
authority. The transition table remains a proposed protocol contract and does not by itself
justify a transition or authorize execution.

### 4.3 Lifecycle-history contract

Every observation, latent belief, research decision, intervention, outcome, evidence object,
experiment, and result MUST contain a nonempty `lifecycle_history`. Each event contains a
stable event ID, one-based sequence, exact prior and new statuses, an exact UTC `recorded_at`,
typed actor identity, substantive rationale, versioned `evidence_refs`, and a
`prior_artifact` reference.

Sequence one is the only root: it has `prior_status: null`, `prior_artifact: null`, and status
`proposed`. Every later event has a non-null prior status and binds the immediately preceding
immutable artifact. Event IDs are unique, sequence is contiguous, times increase, each prior
status equals the preceding event's status, and the final event status equals the record's
current `lifecycle_status`. These cross-event requirements are semantic checks because JSON
Schema cannot compare array elements or repository bytes.
The logical record `created_at` equals the first event time and is preserved by every successor.

The successor never embeds its own digest. Its new event binds only the already-existing
predecessor bytes; the Gate A index binds the successor bytes externally. This avoids an
impossible self-digest cycle while preserving an exact append-only lineage.

### 4.4 Typed preregistration

The word “preregistered” in prose cannot confer `preregistered` status. An experiment with
that lifecycle MUST bind a retained artifact governed by
`schemas/preregistration-record.schema.json`. The record fixes the exact experiment ID and
version, protocol release, versioned and digested analysis specification, UTC freeze time,
and declared observation boundary. Validation MUST establish that the retained bytes and
digest match, all bindings equal the experiment, and `frozen_at` is strictly earlier than the
boundary's `opens_at`. The record contains `runtime_execution_authorized: false`; neither the
record nor preregistered status authorizes execution.

### 4.5 Result and context eligibility

A result with `null`, `inconclusive`, `supported`, `contradicted`, or `replicated` status MUST
bind an exact experiment ID and version. Under the exact protocol's `result_binding_policy`,
that experiment is eligible only when currently `running` or a validated `corrected` successor
whose history contains `preregistered` before `running` and whose retained preregistration
artifact passes binding, freeze-parity, and pre-boundary chronology checks. Proposed,
exploratory-only, preregistered-only, blocked, invalid, failed, and retracted experiments are
ineligible. Protocol release and analysis specification must match exactly. Both the analysis
specification and result name one `primary_metric_id`.
That ID must resolve to exactly one frozen metric mapping and one result metric. For
`invalid`, `null`, `inconclusive`, `failed`, `supported`, `contradicted`, or `replicated`, the
result lifecycle status equals the primary metric's interpretation status. Corrected and
retracted remain lineage statuses rather than metric-derived dispositions. Every metric's
decision-rule and abstention-rule IDs are frozen in the typed analysis specification and must
equal the result metric.

The five non-evidence scientific object kinds carry identical protocol-owned encounter,
object-identity, and temporal-correspondence rule bindings along linked edges. The protocol's
dependency policy constrains allowed provenance input kinds and requires global acyclicity.
Status validity does not repair a context mismatch or dependency cycle.

## 5. Validity dispositions

Each experiment and result MUST declare its target population, observation window, sensor
validity rules, exclusion rules, distribution boundary, subgroup coverage, and abstention
rule before its disposition can be interpreted.

An experiment and its typed analysis specification MUST each contain exactly one population,
object, time, sensor, reference, support, and protocol validity boundary. A result inherits
the exact set through its versioned experiment reference; a changed boundary requires new
experiment and analysis-specification versions.

An exclusion MUST retain:

- the excluded record identifier;
- the exact preregistered rule identifier;
- the observed fact that triggered that rule, itself with provenance;
- who or what applied the rule and when; and
- whether the exclusion changes any estimand denominator.

Post-hoc relabeling of outcomes, omission of a low-performing subgroup, and silent dropping
of abstentions are prohibited. Unknown eligibility remains unknown rather than ineligible.

## 6. Gate A completion and acceptance

### 6.1 Current public Gate A state

For the exact public Gate A `1.2.0` packet, the canonical report records
`architecture_complete`, closes `CR-001` through `CR-016`, passes GA-01 through GA-16, and
contains zero diagnostics. Receipt sequence four exists at the direct-child receipt commit and
records publisher transport as `asserted_unverified`. Independent transport remains
`not_evaluated`; GA-17 is `not_evaluated`; operator acceptance is `unaccepted`; and runtime and
Gate B authorization are both `false`.

The `1.2.1` continuity successor tracked in
[GitHub issue #1](https://github.com/manfromnowhere143/reiyah/issues/1) cannot change the exact
status of the immutable `1.2.0` packet. This prose does not establish its validation or
publication state. Resolve those states only from an exact `1.2.1` canonical report and
append-only event record; absent them, treat the successor as proposed.

### 6.2 Acyclic completion model

The Gate A `1.2.0` index and its excluded canonical report use separate fields for the same exact
candidate bytes:

- the index records `architecture_status: candidate_pending_canonical_report`;
- the report records `not_evaluated`, `invalid`, or `architecture_complete`; and
- both record `operator_acceptance_state: unaccepted`.

This separation removes a self-attestation cycle. The index inventories and hashes the candidate
projection. The report may classify that exact index only after release-mode validation. An index
alone never establishes architecture completeness.

An accepted, rejected, or deferred operator decision is an append-only external record that
binds the existing index digest. It is intentionally excluded from the index and MUST NOT be
written back into the index, because doing so would change the digest that the decision binds.
A composite gate state requires both a structurally admissible latest decision record and
independent, out-of-band verification that the named human held the asserted authority. It is
never derived from repository fields, schema validity, or validator output alone and is not
asserted by mutating the candidate index.

`architecture_complete` means only that the required static artifacts are indexed and pass
the declared offline checks with the exact version-specific coverage totals, zero
architecture diagnostics, no created acceptance, and GA-01 through GA-16 covered. The report
accounts for GA-17 separately in `control_summary.external_control`. The offline repository report
always records GA-17 as `not_evaluated` with a null record ID and no external-control
diagnostics: repository bytes cannot authenticate a human or establish authority. Structural,
binding, and history defects in a present decision record remain ordinary deterministic
diagnostics, but they do not turn the validator into an authority verifier. An `accepted`
composite state is valid only after an independently authorized external verifier confirms the
human's identity and authority and only when the decision record binds the exact
index, mission release, protocol release, and retained architecture-completeness report paths,
versions, schema IDs, and SHA-256 digests; identifies the operator and authority; records a UTC
decision time and substantive rationale; acknowledges risks; and passes both schema and global
history validation.

Operator decisions form one append-only linear chain. Sequence one has null predecessor ID
and digest. Every later sequence binds the immediate prior record's ID and digest and has a
strictly later UTC decision time. Duplicate identities, branches, cycles, gaps, multiple roots,
or conflicting heads are invalid. Schema validation constrains one record; repository-wide
validation establishes the chain. Neither check independently authenticates operator identity
or authority.

The validator may check decision-record structure, bindings, and history but MUST NOT select a
decision, create a decision record, authenticate identity or authority, evaluate GA-17, or
convert architecture completeness into acceptance.

Publication and transport use a third independent state axis. A publisher-authored distribution
receipt may retain exact push commands, GitHub identifiers, and remote readback assertions, but
its `transport_verification_state` remains `asserted_unverified`. It cannot verify itself. A
verified transport state requires a separately authorized observation record whose retained
observation bytes and provenance bind the exact repository, commit, index, and report. Neither a
receipt nor an independent transport observation can accept Gate A or support a scientific claim.

No acceptance record exists at bootstrap. Candidate manifests therefore MUST use
`release_stage: candidate`, `lifecycle_status: proposed`, and an `operator_acceptance`
object whose `state` is `unaccepted` and whose `record_id` is `null`.

## 7. Manifest release relations

Mission and protocol releases are append-only. Every release has a globally stable release
identifier and semantic version. It contains exactly one relation:

- `initial`: no predecessor;
- `supersedes`: replaces a prior release without claiming an error;
- `corrects`: fixes a named prior release while preserving it; or
- `retracts`: withdraws a named prior release while preserving it.

Released identifiers MUST never be reused. A candidate that changes after it has been distributed
for review or public transport MUST receive a newly versioned Gate A packet and new packet-level
identities even when it remains unaccepted. The prior packet, report, commit, and receipt remain
discoverable. An accepted artifact that changes for any reason requires a new release and a new
acceptance record; its previous acceptance does not transfer.

The immutable Gate A `1.0.0` packet freezes its ledger and manifest inventory to exactly the
initial mission release `reiyah.mission@1.0.0` and protocol release
`reiyah.protocol.harbor-gate-a@1.0.0`. A later correction or successor remains append-only but
requires a newly versioned Gate A schema, validation plan, index, and report; it cannot silently
enter or redefine the semantic head of packet `1.0.0`.

The public Gate A `1.1.0`, `1.1.1`, `1.1.2`, and `1.2.0` packets are immutable at their exact
indexed commits and digests. Gate A `1.1.1` is the governance correction, and `1.1.2` is its
presentation and continuity successor. Both retain `reiyah.mission@1.1.0` and
`reiyah.protocol.harbor-gate-a@1.1.0` unchanged.

Gate A `1.2.0` is a scientific and validation-integrity correction. It retains the mission and
introduces proposed protocol `reiyah.protocol.harbor-gate-a@1.2.0`, which points to the immutable
`1.1.0` protocol as `corrects`. It inherits every unchanged `1.1.2` indexed artifact by exact
digest, records every changed and added path in a closed validation plan, and removes no
predecessor artifact. Receipt sequence three resolves only the exact `1.1.2` publication event.
Receipt sequence four binds the exact `1.2.0` index, report, event-specific rights observation,
publication commit, and publisher readback assertions. It records `asserted_unverified` and does
not claim independent transport verification. Frozen values are never placeholders.

## 8. Status ownership

Only an authorized operator can set Gate acceptance. Protocol-defined analysis procedures may
produce a result disposition when their retained inputs and execution evidence exist. Authors
may mark authored material `proposed` or `exploratory`; they may not self-promote it to
`supported` without the required evidence. External tools and models never own Reiyah status
authority.
