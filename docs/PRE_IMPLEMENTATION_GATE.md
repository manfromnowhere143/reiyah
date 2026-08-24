# Gate A: Pre-Implementation Architecture Gate

Document version: `1.2.0`

## 1. Decision boundary

Gate A determines whether Reiyah has a reviewable, falsifiable, evidence-bound architecture
before any implementation is considered. Gate A does **not** approve a product, runtime,
model, dataset, study, intervention, empirical or scientific publication, safety case, or
standards-compliance claim.

The gate has two deliberately separate decisions:

1. **Architecture completeness:** a deterministic validator confirms that every required
   artifact exists and the machine-checkable contracts are internally consistent.
2. **Operator acceptance:** an authorized human reviews the exact, hash-bound evidence index
   and records `accepted`, `rejected`, or `deferred` with a rationale.

Architecture completeness without operator acceptance leaves `architecture_status` as
`architecture_complete` and `operator_acceptance_state` as `unaccepted`. It grants no authority
beyond review of the static packet.

## 2. Normative controls

The identifiers below are stable. A validator result is evidence about a control; it is not
the authority that waives or accepts the control.

| Control | Requirement | Architecture evidence | Failure effect |
|---|---|---|---|
| GA-01 | Repository identity and authority resolve uniquely to Reiyah. | `AGENTS.md`, handoff | Block |
| GA-02 | Mission, exclusions, units of analysis, and falsifiers are explicit. | scientific charter, mission manifest | Block |
| GA-03 | Claims and non-claims are individually identified and evidence-status bound. | claims register | Block |
| GA-04 | Observation, latent belief, decision, intervention, outcome, and evidence remain distinct. | formal model, schemas, diagrams | Block |
| GA-05 | Missing, unmeasured, OOD, sensor-invalid, and abstained remain explicit and non-coercible. | status model, schemas, bad fixtures | Block |
| GA-06 | Every required lifecycle status retains a distinct definition and transition rule. | status model, schemas, fixtures | Block |
| GA-07 | Estimands, comparators, assumptions, uncertainty, validity domains, and abstention are specified. | mathematical specification, protocol manifest | Block |
| GA-08 | Readiness, recoverability, joint silent miss, causal effect, transfer, and worst-group evaluation are falsifiable and not reducible to one classifier score. | scientific charter, mathematical specification | Block |
| GA-09 | Mission and protocol releases are versioned, digest-bound, append-only, and supersession-aware. | manifests, release ledger | Block |
| GA-10 | Sources retain bytes and provenance; external inputs have no acceptance authority. | source policy, source ledger, retained evidence | Block |
| GA-11 | Standards mappings identify exact version/date/scope/evidence/gaps and make no compliance claim. | dated crosswalk | Block |
| GA-12 | Threats, trust boundaries, mitigations, detection evidence, and residual risks are explicit. | threat model | Block |
| GA-13 | Schemas and global semantics reject ambiguity, unknown fields where normative, invalid or ineligible evidence bindings, invalid references, and collapsed unknowns. | JSON Schemas, fixtures | Block |
| GA-14 | Validation starts inside the locked pre-runtime isolation boundary, reads the same immutable projection through two separately loaded, state-reset release evaluations, is offline, deterministic, fail-closed, replayable, demonstrates production-path rejection for every declared known-bad fixture, reconciles exact coverage totals, and reports zero diagnostics for completion. | launcher, toolchain lock, validator, fixture catalog, control summary, validation report | Block |
| GA-15 | The architecture shows no product runtime, live inference, deployment, physical control, private ingestion, or publication machinery. | repository inventory, architecture diagram | Block |
| GA-16 | The complete review surface is listed in a digest-bound evidence index. | Gate A evidence index and sidecar digest | Block |
| GA-17 | An authorized operator makes an explicit decision on the exact evidence-index digest. | operator-created acceptance record | Leaves Gate A unaccepted when unevaluated |

## 3. Architecture completeness rule

Controls GA-01 through GA-16 must pass. Each failure is blocking; there is no weighted score
or majority override. A control may be marked `not_applicable` only if its own wording permits
that state and the operator records a rationale; none of GA-01 through GA-16 currently permit
it. GA-17 is accounted separately as an external operator control, not as an architecture
check.

The architecture-completeness result is one of:

- `incomplete`: required evidence is absent or validation has not run;
- `invalid`: a required check or known-good fixture fails, or a known-bad fixture passes;
- `architecture_complete`: GA-01 through GA-16 pass for one evidence-index digest; or
- `stale`: a previously complete artifact or its digest changed.

These are gate states, not scientific result statuses.

For the Gate A `1.2.0` correction candidate, `architecture_complete` additionally requires all of
the following for one exact index digest:

- the external launcher enters the locked Seatbelt policy before CPython starts and the validator
  exact-matches the declared platform, executable, standard-library, extension-module, and
  dependency bytes;
- the release snapshot is a clean immutable Git tree, while development snapshots remain
  explicitly ineligible as release evidence;
- the exact `1.1.2` historical index, sidecar, canonical report, receipt, and recovery bindings
  reconcile, every unchanged predecessor artifact remains byte-identical, and every changed or
  added path belongs to the closed correction scope;
- all seven `1.2.0` scientific schemas, all valid reference instances, every scientific mutation,
  every governance counterexample, and every validator-security counterexample pass through the
  same production paths;
- the index projection, artifact inventory, exclusion list, fixture catalog, validation plan,
  manifests, release ledger, and reason-specific diagnostics reconcile with their exact bytes;
  and
- two separately loaded, state-reset release evaluations of the unchanged committed projection produce
  byte-identical pre-report stage evidence and index bytes inside one locked invocation; only then
  may one deterministic canonical report render record zero diagnostics, GA-01 through GA-16 as
  passed, no acceptance, and GA-17 separately as `not_evaluated`.

After the report exists, two complete launcher invocations must still emit bytes identical to each
other and to the committed report. That post-render readback is a release and publication
prerequisite. It cannot be an operand inside the earlier report without creating a temporal
self-reference, and the report does not claim to have observed it.

The same report must derive its correction closure from that snapshot. Ordered
`required_finding_ids` are exactly `CR-001` through `CR-016`; closed and open IDs form an exact
disjoint partition; every finding result names the production checks and fixtures that determine
it; and `architecture_complete` is forbidden unless required findings equal closed findings and
the open set is empty.

Counts are recomputed from the immutable candidate projection rather than trusted from prose or
report fields. The index remains `candidate_pending_canonical_report`; only the excluded canonical
report may classify its exact digest as `architecture_complete`.

The offline report's `control_summary.external_control` always records GA-17 as `not_evaluated`
with a null decision-record ID. Repository bytes cannot
authenticate a human or establish authority. The validator may check the structure, bindings,
and history of a present decision record and report defects through ordinary deterministic
diagnostics, but it may not authenticate authority, evaluate GA-17, create the record, select
its decision, or infer acceptance. Only an independently authorized external verifier may
evaluate the composite operator state. A failed or unevaluated external decision does not alter
a still-complete GA-01-through-GA-16 architecture. Gate B remains undefined and unauthorized
regardless of the GA-17 state.

The validation plan also binds each normative narrative to its machine contract by exact safe
paths and lowercase SHA-256 digests. Stale narrative or machine bytes, missing bindings, or
duplicate binding IDs prevent architecture completeness.

A distribution receipt is not part of architecture completeness. It may record a publisher's
exact publication and readback assertions, but it remains `asserted_unverified`. Independent
transport verification requires a distinct authorized observation record bound to the same
repository, commit, index, and report bytes. Neither transport state can evaluate GA-17.

## 4. Operator decision rule

An operator decision is one of `accepted`, `rejected`, or `deferred`; it is distinct from the
scientific lifecycle vocabulary. A record is structurally admissible only when it contains:

- Reiyah project and Gate A identifiers;
- the canonical evidence-index path, artifact ID, schema ID, version, and SHA-256 digest;
- exactly the mission and protocol release identifiers plus their canonical artifact bindings;
- the canonical retained validation-report path, artifact ID, schema ID, version, and digest,
  whose content reports `architecture_complete` for that same index digest;
- a stable operator identifier, independently verified authority basis, UTC decision time,
  decision, and substantive rationale;
- explicit acknowledgement of unresolved risks and of the no-runtime boundary; and
- no unresolved GA-01 through GA-16 failure; and
- a one-based decision sequence and immediate-prior record ID/digest under an
  `append_only_linear` policy, with null predecessor fields only for sequence one.

A generated signature, typed name, self-asserted authority basis, hash, passing check, or
assistant statement is not operator acceptance. Independent verification of human identity and
authority is an additional external requirement that this repository cannot satisfy. A change
to any indexed byte makes the decision stale. Corrections append a new record and preserve the
old record. Repository-wide checks must reject duplicate decision or
artifact IDs, non-increasing UTC times, branches, cycles, sequence gaps, multiple roots,
multiple heads, missing predecessors, and predecessor digest mismatch. JSON Schema constrains
record shape but cannot authenticate the human operator or prove their authority.

Scientific lifecycle advancement is governed separately. Every scientific object,
experiment, and result has append-only immutable lifecycle history; every transition is
authorized only by the exact protocol release's transition table. Preregistered experiment
status requires a typed preregistration record and typed analysis specification frozen before
the declared observation boundary. Terminal results bind an exact eligible experiment
version, and terminal evidence bindings use versioned active evidence references. None of
these records authorizes runtime execution.

Gate A 1.2 application records expose only an explicit evidence-gap binding. No retained
scientific-evidence or experiment-binding resolver is authorized in this release, so favorable or
terminal evidence-requiring scientific dispositions remain rejection targets rather than
attainable states. This does not prevent append-only testing of non-support lifecycle successors.

## 5. Gate B prohibition

Gate B is undefined and unauthorized in this repository. A valid Gate A acceptance would not
define Gate B or authorize implementation. Any Gate B proposal requires a separate explicit
operator instruction and its own reviewed contract. Until then, the permitted work remains
architecture review and correction.
