# Gate A: Pre-Implementation Architecture Gate

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
| GA-14 | Validation is offline, deterministic, fail-closed, replayable, demonstrates production-path rejection for the declared known-bad fixtures, reconciles exact coverage totals, and reports zero diagnostics for completion. | validator, fixture catalog, control summary, validation report | Block |
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

For the Gate A `1.1.0` architecture candidate, `architecture_complete` additionally
requires a canonical index with an explicit version for every artifact binding and a canonical
full validation report covering the exact frozen schema, normative-instance, fixture, retained-source,
and indexed-artifact totals. Every known-good fixture must pass, every known-bad fixture must
fail for its declared rule, unexpected outcomes and architecture diagnostics must be zero, and
`acceptance_created` must be false. The decision-free closeout report has zero top-level
diagnostics. The report's control summary must cover and pass GA-01 through GA-16 with no failed
control; GA-17 is recorded separately as external.
These totals are recomputed from the canonical repository view rather than trusted from report
fields.

This `1.1.0` packet binds the initial releases and their exact `1.1.0` successors through the
append-only release ledger. Any later correction requires a newly versioned Gate A packet whose
validator rechecks the complete mission and policy surface. Historical `1.0.0` bytes remain
preserved and may not be rewritten or silently treated as the current semantic head.

The offline report's `external_control_summary` always records GA-17 as `not_evaluated` with a
null decision-record ID and no external-control diagnostics. Repository bytes cannot
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

## 5. Gate B prohibition

Gate B is undefined and unauthorized in this repository. A valid Gate A acceptance would not
define Gate B or authorize implementation. Any Gate B proposal requires a separate explicit
operator instruction and its own reviewed contract. Until then, the permitted work remains
architecture review and correction.
