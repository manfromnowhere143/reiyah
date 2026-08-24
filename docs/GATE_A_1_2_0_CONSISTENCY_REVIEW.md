# Gate A 1.2.0 Candidate Consistency Review

## Status and authority

This record preserves an internal adversarial review of the Gate A 1.2.0 correction candidate.
It is model-assisted advisory analysis, not independent evidence, operator acceptance,
scientific support, a safety assessment, a standards opinion, or runtime authorization.

The candidate is not frozen. Every disposition recorded here is the pre-replay state `open`.
This document is the immutable finding definition, not a mutable closure ledger. The canonical
validation report for one exact candidate projection must independently derive the ordered
required, closed, and open finding-ID sets from the controls below. A report may classify a
finding as closed only when every bound requirement passes in that same replay; the review is not
edited afterward, avoiding a digest cycle. Passing schema validation or a fixture-specific branch
is insufficient.

## Review method

The review traces each claimed control across the normative specification, schema, versioned
manifest binding, production validator, known-good fixture, minimally changed known-bad fixture,
and canonical report. It also challenges identifier resolution, temporal order, denominator
closure, evidence eligibility, and authority separation at the boundaries between those layers.

For each finding, closure requires all of the following on one immutable candidate projection:

1. explicit normative semantics;
2. operands sufficient to evaluate those semantics;
3. a closed schema that requires the operands;
4. a production rule that independently derives the disposition;
5. a known-good fixture accepted by the production path;
6. a reason-specific known-bad fixture rejected by that same path;
7. exact manifest and tool-digest bindings;
8. deterministic index and report bytes from a clean release replay.

## Candidate findings

| ID | Area | Blocking inconsistency | Required correction | Pre-replay disposition |
| --- | --- | --- | --- | --- |
| `CR-001` | Belief and human reconciliation | A normalized vector can omit or duplicate states, use a state space inconsistent with the referenced object and information set, or drift from the observation and decision records it is meant to reconcile. | Require exact state-space coverage and uniqueness, protocol-bound probability closure, object identity, information-set identity, and aligned event, availability, observation, belief, and decision times. | `open` |
| `CR-002` | Observation | Measurement validity and value epistemic state can disagree, and object, information-set, or time references can drift across records. | Require independent validity and value-state axes, reject incompatible combinations, and reconcile exact object, information-set, event-time, and availability-time bindings. | `open` |
| `CR-003` | Causal policy effects and preregistration | Treatment and outcome roles, estimand identity, selected adjustment-set identity, and identification disposition are not necessarily bound to the graph and query being validated. Distinct split names alone do not prove a frozen disjoint partition. | Require a typed back-door query, exact protocol estimand operands, observed treatment and outcome roles, graph identity, selected-set membership, and a biconditional identification derivation. Bind exact split member manifests, pre-outcome freeze, disjointness, completeness, and typed stratification inputs. Reject unsupported strategy branches. | `open` |
| `CR-004` | Readiness and recoverability | A positive-weight unknown readiness capability can be imputed into a confident aggregate. No-event, incomplete observation, and non-observed recovery operands can be reported as terminal recovery or a precise recovery time. | Propagate every positively weighted unknown capability into the exact unresolved set and aggregate disposition. Derive recovered, censored, competing-event, invalid, and non-observed outcomes from the frozen window and complete event sequence. | `open` |
| `CR-005` | Off-policy evaluation | Policy identities can be inert; history and information-set identities can be ambiguous; and step coverage, terminal state, support cells, weight transformation, cumulative weights, effective sample size, and its sufficiency disposition can be mutually inconsistent. | Bind role-typed policy identities to frozen per-history tables; require exact history prefixes and globally unique trajectory, history, and information-set identities; require exact-once support cells, horizon and terminal closure, exact transformations, cumulative weights, and threshold-derived horizon-specific ESS. Keep estimator outputs non-observed inside Gate A. | `open` |
| `CR-006` | Joint silent misses | Exact joint failure can be asserted from marginal channel rates or self-declared aggregate cells without member-complete linked joint opportunities. | Bind an exact opportunity set; retain common object, clock, window, per-opportunity reference, channel, warning, and fallback states; derive all aggregate cells and summaries from exact member-complete rows; and preserve explicit nonidentifiability when any required row operand is unresolved. | `open` |
| `CR-007` | OOD, selective prediction, and worst groups | Reference-unknown and detector-unknown axes can overlap or fail to form an atomic exhaustive partition. A coordinated deletion can remove a group from both a self-declared universe and its results. | Require disjoint atomic cells over both OOD axes and reconcile every count and rate. Bind conformal and worst-group universes to exact versioned group sets, partition every member into sufficient, insufficient, or unknown, then derive the overall disposition and tied worst set from eligible groups only. | `open` |
| `CR-008` | Transfer, conformal, and assumption evidence | Assumptions can be self-labeled as satisfied while carrying no eligible evidence. Coverage can be asserted without exact numerators, denominators, or group-scope semantics, and transfer direction or population harmonization can be inert. | Keep favorable guarantees and transfer eligibility unavailable without a retained evidence resolver. Require exact coverage operands and scope, bind metric direction and harmonization, propagate unresolved operands, and derive every disposition without trusting favorable booleans. | `open` |
| `CR-009` | Typed references and lifecycle lineage | A syntactically valid identifier can resolve to a definition with the wrong kind, record kind, actor type, version, or owning collection. A lineage reference can dangle or permit earlier lifecycle events to be rewritten. | Publish exhaustive reference classifiers; resolve structured, bare-registry, local-document, schema, artifact, and evidence-gap shapes through exact contracts; exact-bind application estimands; and require every scientific successor to append to an immutable byte-resolved predecessor history. | `open` |
| `CR-010` | Execution binding | The scientific profile can omit the external launcher or semantic module while naming only the primary validator. | Bind launcher, primary validator, scientific module, and complete toolchain lock by path and SHA-256 digest. | `open` |
| `CR-011` | Public rights | The successor packet can rely on a predecessor rights schema or treat a synthetic probe as a real publication observation. | Close the static architecture only by defining and exact-binding the 1.2 rights schema, freshness rule, and reason-specific synthetic rejection. A fresh retained rights observation remains a separate prerequisite at the actual publication event and is not created by architecture validation. | `open` |
| `CR-012` | Transport verification | A transport record can claim independence without authentication, authorization, evidence closure, packet identity, or valid chronology. | Close the static interface only by requiring and testing distinct observer and verifier roles, authority bases, resolved evidence IDs, exact packet bindings, and post-publication chronology. A real independent observation remains `not_evaluated` until a separately authorized event occurs. | `open` |
| `CR-013` | Canonical report | A pass can coexist with failed control counts, execution errors, acceptance, or transport claims that contradict the report result. | Enforce cross-field count equality and result implications semantically; keep operator acceptance and transport `not_evaluated` in offline Gate A validation. | `open` |
| `CR-014` | Catalog integrity | Fixture IDs or paths can collide even when each catalog row is individually schema-valid. | Enforce global uniqueness of fixture IDs and paths, exact filesystem set reconciliation, and exact expected primary diagnostics. | `open` |
| `CR-015` | Version chronology | A successor research registry can carry a date earlier than the retained correction investigation. | Bind release chronology to the declared 2026-08-24 correction date and reject inconsistent successor ordering. | `open` |
| `CR-016` | Documentation truthfulness | Present-tense completion language can precede the canonical report and operator decision. | Describe controls as candidate intentions until deterministic evidence exists, and keep architecture completeness, acceptance, transport, science, safety, and compliance as separate states. | `open` |

## Static architecture evidence still required

Closure cannot be inferred from worktree inspection. Before any publication decision, the
candidate must produce and retain:

1. strict schema and instance validation for every 1.2 artifact;
2. one-to-one fixture catalog and filesystem reconciliation;
3. exact reason-specific diagnostics for every declared bad fixture;
4. a complete validation plan bound to the final tool bytes;
5. a canonical evidence index and sidecar from one immutable projection;
6. a canonical report whose counts, digests, and state implications reconcile;
7. byte-identical repeated release executions from a clean committed tree.

## Separate publication-event prerequisites

Static architecture closure cannot create or predate a distribution event. Before a push, public
distribution separately requires a fresh rights observation and explicit operator publication
authority. After publication, an append-only receipt may record only the publisher's local
assertions. Any independent transport-verification claim additionally requires a separately
authorized observation made after publication and bound to the same exact bytes.

Until those records exist, Gate A 1.2.0 remains an unaccepted correction candidate and the
smallest authorized scope remains static architecture plus deterministic synthetic validation.
