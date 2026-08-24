# Gate A Threat Model

| Field | Value |
| --- | --- |
| Document ID | `reiyah.threat-model` |
| Version | `1.2.0` |
| Lifecycle status | `proposed` |
| Scope | Static Gate A artifacts, fixtures, offline validators, distribution records, and acceptance records |

This threat model protects scientific and architectural integrity. It does not claim
cybersecurity assurance, vehicle safety, privacy compliance, or deployment suitability.

## 1. Authorized system boundary

Gate A contains only reviewable repository artifacts and deterministic offline validators.
There is no product runtime, live data path, network service, model training or inference,
private-data store, empirical-publication system, or physical-control interface. Static public
repository transport is separately bounded by an exact distribution inventory. A local receipt
is a retained transport assertion, not independent proof of a remote observation.

Any component that introduces one of those capabilities is outside the boundary and must
be rejected, not “sandboxed” into Gate A.

## 2. Assets and protection goals

| Asset | Protection goal |
| --- | --- |
| Repository identity and contract | Prevent cross-project authority or artifact contamination. |
| Mission and protocol manifests | Preserve version identity, append-only release history, and exact digests. |
| Six-kind ontology | Prevent observation, belief, decision, intervention, outcome, and evidence from being collapsed or relabeled. |
| Epistemic and lifecycle states | Preserve distinct meanings and complete status history. |
| Retained evidence | Preserve exact bytes, provenance, version, publication date, access constraints, and digest. |
| Claims and non-claims | Prevent scope inflation, evidence laundering, and unsupported status changes. |
| Schemas and fixtures | Reject ambiguity, unknown fields where forbidden, invalid references, and coercion. |
| Validator and diagnostics | Preserve offline, deterministic, fail-closed behavior and reason-specific failures. |
| Evidence index | Bind the exact reviewed architecture set without circular or ambiguous hashing. |
| Public custody and distribution records | Prevent restricted payloads, pointer laundering, attribution loss, and forged transport claims. |
| Operator decisions | Prevent spoofing, replay against changed artifacts, and conflation with scientific evidence. |

Availability is secondary to integrity at Gate A: a blocked validation is preferable to a
plausible but unverified result.

## 3. Actors and trust assumptions

| Actor or source | Trust level | Permitted role | Not authoritative for |
| --- | --- | --- | --- |
| Authorized operator | Highest repository decision authority, but fallible | Issue explicit instructions and digest-bound acceptance decisions | Scientific truth by fiat |
| Contributor | Untrusted until reviewed and validated | Propose architecture changes | Acceptance or scientific status |
| Independent scientific reviewer | Advisory; a review record is provenance, not scientific evidence by itself | Review methods, claims, and retained evidence | Repository/operator authority or scientific status by fiat |
| Offline validator | Deterministic integrity mechanism | Check declared static contracts | Scientific validity or acceptance |
| External source or dataset provider | Untrusted evidence source | Supply versioned candidate evidence | Reiyah policy or conclusions |
| External model, agent, MCP server, or tool | Untrusted adapter | Generate proposals or retrieve candidate inputs | Evidence, status, acceptance, or publication |
| Sibling repository | Untrusted and independent | None by default | Reiyah code, data, configuration, or authority |
| Malicious or careless actor | Adversarial | None | Any protected decision |

A typed name, generated signature, checksum, consensus, or passing test does not elevate an
actor's authority.

## 4. Trust boundaries

```mermaid
flowchart LR
  subgraph U[Untrusted outside inputs]
    WEB[Sources and standards]
    DATA[Datasets and benchmark descriptions]
    EXT[Models, tools, MCP servers]
    SIB[Sibling repositories]
  end

  subgraph R[Reiyah static Gate A repository]
    Q[Quarantine and provenance review]
    RET[Retained bytes plus source ledger]
    SPEC[Manifests, scientific specs, schemas]
    FIX[Known-good and known-bad fixtures]
    VDEF[Offline deterministic validator definition]
    RUN[Offline validation execution]
    IDX[Gate A evidence index candidate]
    REP[Machine-readable validation report]
    PUB[Public inventory and append-only receipt]
  end

  OP[Authorized operator]
  ACC[Digest-bound operator decision record]

  WEB --> Q
  DATA --> Q
  EXT --> Q
  SIB --> Q
  Q -->|exact bytes, metadata, digest| RET
  RET --> SPEC
  SPEC --> IDX
  RET --> IDX
  FIX --> IDX
  VDEF --> IDX
  IDX --> RUN
  VDEF --> RUN
  RUN --> REP
  RET --> PUB
  IDX --> PUB
  IDX --> OP
  REP --> OP
  OP -->|explicit decision only| ACC

  EXT -. no authority .-> ACC
  RUN -. cannot accept .-> ACC
  RET -. identity is not truth .-> ACC
```

No arrow represents a runtime vehicle or human-data flow. The operator decision record is
a repository-governance decision, not scientific evidence.

## 5. Threat catalogue

Residual risk is stated even where a mitigation exists. Threat identifiers are stable
within this version.

| ID | Threat and attack/failure scenario | Required preventive control | Required detection or rejection | Residual risk |
| --- | --- | --- | --- | --- |
| `TM-001` | **Repository identity confusion:** work intended for Reiyah is performed under another Git root or sibling instructions. | Resolve canonical working directory and Git root before repository actions; forbid sibling imports by default. | Validation and task closeout record the exact root; mismatch halts work. | A compromised filesystem or Git binary can misreport identity. |
| `TM-002` | **Cross-repository contamination:** code, data, authority, or conclusions are copied from a sibling. | Treat siblings as untrusted external sources; require explicit provenance and retained evidence. | Inventory flags undeclared origins and foreign paths. | Human authors may fail to disclose copied concepts. |
| `TM-003` | **Source substitution or link drift:** a URL later serves different bytes or a local source is replaced. | Retain permitted bytes and record exact version, date, metadata, constraints, and SHA-256 digest; observe mutable rights pages immediately before public distribution. | Recompute payload digests offline; reject mismatches, URL-only positive evidence, unreachable rights pages, and observed rights contradictions. | A digest establishes sameness, not authenticity, truth, or legal effect. |
| `TM-004` | **Evidence laundering:** generated prose, a review, signature, consensus, or test is cited as independent evidence. | Type evidence and authority records separately; restrict eligible claim links. | Semantic validation rejects ineligible evidence kinds for scientific support. | Sophisticated circular citations may need human investigation. |
| `TM-005` | **Manifest or history rewrite:** mission/protocol content or recovered predecessor identity changes without a new version or disclosure. | Append-only release IDs, canonical serialization, content digests, supersession links, and exact recovery bindings. | Reject duplicate IDs, predecessor digest mismatch, recovered-byte mismatch, and acceptance binding mismatch. | Git history and private custody context can be rewritten outside the validator's view. |
| `TM-006` | **Ontology collapse:** observation, latent belief, decision, intervention, outcome, or evidence is relabeled to simplify analysis. | Separate schemas, namespaces, timestamps, provenance, and allowed references. | Known-bad cross-kind and illegal-edge fixtures must fail for declared reasons. | Semantically misleading values can still satisfy a syntactic schema. |
| `TM-007` | **Unknown coercion:** missing, unmeasured, OOD, sensor-invalid, or abstained becomes zero, false, normal, or negative. | Closed epistemic-state enum; reason required for every non-observed state; prohibit sentinels. | Fixtures exercise every state and coercion pattern; denominator checks fail closed. | A plausible numeric value can conceal upstream coercion not visible in retained provenance. |
| `TM-008` | **Status laundering:** `exploratory`, `null`, `inconclusive`, `failed`, `invalid`, or `retracted` is presented as support. | Closed lifecycle enum, append-only transitions, claim-language rules. | Reject illegal transitions, absent history, overwritten records, and incompatible claim links. | Human summaries may overstate a technically correct status. |
| `TM-009` | **Outcome or future-information leakage:** later observations enter a decision or belief information set. | Record event and availability times, index time, information-set membership, and protocol windows. | Temporal validator rejects unavailable inputs and ambiguous ordering where the protocol requires order. | Incorrect source timestamps may evade detection. |
| `TM-010` | **Decision/intervention conflation:** a proposed action is assumed executed, or observed exposure is assumed assigned. | Separate kinds and IDs; record assignment, delivery, receipt, adherence, and provenance independently. | Reject causal links lacking intervention and assignment records. | Unrecorded non-adherence or contamination can remain. |
| `TM-011` | **Post-hoc outcome, comparator, or subgroup relabeling:** favorable definitions replace frozen ones after outcome access. | Digest-bound preregistered protocol; new release for any substantive change; deviation log. | Compare evaluation inputs to the frozen protocol and reject mismatches. | Unauthorized outcome access may not be observable from repository artifacts. |
| `TM-012` | **Causal overclaim:** association or simulation is labeled a policy effect despite confounding, interference, or positivity failures. | Require explicit estimand, assignment mechanism, identification assumptions, diagnostics, and sensitivity plan. | Claims validator rejects causal language without a bound eligible protocol and evidence. | Assumptions can be documented yet false or empirically untestable. |
| `TM-013` | **Joint-miss identifiability laundering:** marginal miss rates are multiplied, paired, or otherwise presented as an exact joint silent-miss result without joint event observations or an identified dependence model. | Pre-specify an exact opportunity-set identity and member list, common object and window, per-opportunity reference and channel states, warning and fallback availability, dependence model, and target estimand; distinguish observed joint events from model-derived bounds or estimates. | Derive every aggregate cell from the exact member-complete opportunity rows; reject marginal-only arithmetic, coordinated row/set omission, undeclared factorization, unavailable-channel coercion, and inconsistent identifiability. | Sparse joint events or untestable dependence assumptions may leave only partial identification or irreducible uncertainty. |
| `TM-014` | **Denominator manipulation:** invalid, abstained, small, or poorly performing cases are removed from reported coverage. | Record inclusion flow and per-state counts before/after every exclusion. | Reconcile denominators and reject unexplained loss or double counting. | Source populations may already embody selection bias. |
| `TM-015` | **Worst-group erasure:** an empty, invalid, or low-performing group is omitted so another group appears worst. | Bind the record to an exact versioned group-set definition and retain sufficient, insufficient, and unknown results for the complete member set. | Reconcile the external set, declared universe, result rows, eligibility partitions, and tied extremum; a coordinated universe-and-row deletion still fails. | Unmeasured group attributes can make membership unknowable. |
| `TM-016` | **Transfer leakage or target tuning:** target outcomes influence source training, threshold selection, split construction, or adaptation beyond protocol. | Freeze source/target domains, exact split manifests and member sets, allowed adaptation, stratification inputs, and access chronology. | Enforce split-member disjointness and completeness, pre-outcome freeze, typed stratification inputs, and declared target-label access. | Organizational knowledge leakage may be impossible to prove absent. |
| `TM-017` | **Benchmark gaming, fixture overfitting, or review-closure laundering:** validator logic special-cases known fixtures, or a report marks a correction finding closed without its mapped production evidence. | General rules, diverse reason-specific fixtures, immutable expected failures, exact validation-plan SHA-256 bindings for the launcher, primary validator, science module, and toolchain lock, plus a fixed finding-to-check-and-fixture map. | Mutation/adversarial fixtures, exact source-binding checks, diff review, and same-snapshot derivation of required, closed, and open finding sets; reject changed expectations, bound bytes, or closure mappings without a reviewed successor. | A finite fixture set and source binding cannot establish semantic completeness or prevent coordinated malicious change to every authority artifact. |
| `TM-018` | **Nondeterministic validation:** clocks, locale, ordering, randomness, filesystem paths, or network results change diagnostics. | Offline execution, canonical sorting/serialization, pinned dialects, no wall-clock fields in compared output, fixed seeds where allowed. | Repeat validation and compare exit code and report bytes. | Platform/library differences may remain unless the environment is fully pinned. |
| `TM-019` | **Fail-open validation:** unknown schemas, properties, IDs, references, exceptions, or unresolved correction findings are ignored. | Closed schemas where specified; explicit allowlists; exact correction-finding partition; nonzero exit on any unknown, internal error, or unresolved required finding. | Known-bad fixtures for each rejection path, self-test inventory, and report implications that forbid `architecture_complete` unless required findings equal closed findings and open findings are empty. | Unmodeled semantic errors can still pass. |
| `TM-020` | **Acceptance spoofing or replay:** a typed/generated approval is attached to changed artifacts. | Require declared operator identity and authority basis, UTC decision time, rationale, risk acknowledgement, exact path, algorithm, evidence-index digest, manifest releases, matching architecture-completeness evidence, and separate out-of-band identity/authority verification. | Recompute bindings and reject malformed or stale records; keep GA-17 `not_evaluated` until an authorized human independently verifies identity and authority. | Repository records cannot authenticate a human identity or authority. |
| `TM-021` | **Circular evidence index:** an index directly or indirectly hashes itself, its generated validation output, or a post-push receipt that names its commit. | Define an acyclic inventory; exclude the index, sidecar, emitted report, acceptance records, and append-only distribution receipts from indexed entries. | Dependency-cycle, excluded-path, canonical-index, and duplicate-path checks. | Later packaging can accidentally introduce a second ambiguous inventory. |
| `TM-022` | **Standards scope inflation:** catalog metadata or partial text is described as full normative evidence or compliance. | Record exact document/version/date, source type, retained extent, scope, comparator, and unresolved gaps. | Crosswalk validator rejects support/compliance status and absent retained evidence. | Standards access restrictions may prevent full-text retention and leave unresolved gaps. |
| `TM-023` | **Poisoned or restricted evidence:** malicious bytes, active content, or incompatible access or licence conditions enter the repository. | Treat retained files as inert bytes; separate retained, pointer-only, and excluded states; bind an exact public inventory; never execute evidence. | Allowlisted static inspection, exact set reconciliation, quarantine, attribution checks, and fail-closed exclusion when rights remain unresolved. | File parsers used outside Gate A may contain vulnerabilities, and automated checks cannot create legal clearance. |
| `TM-024` | **Unauthorized private-data ingestion:** real human or vehicle records are placed in fixtures/evidence. | Synthetic, non-identifying fixtures only; explicit provenance and prohibited-data rule. | Inventory/content review blocks suspected private or secret material. | Automated detection cannot prove that realistic synthetic data is not real. |
| `TM-025` | **Runtime or physical-control scope creep:** architectural components become live services, inference, alerts, or actuator interfaces. | Gate A allowlist permits documentation, schemas, fixtures, evidence records, and the digest-bound launcher, primary validator, science module, and toolchain lock only. | Full inventory checks, exact source and lock bindings, AST restrictions, and mutations reject servers, writes, shell/network calls, dynamic indirection, device interfaces, training/inference, and deployment configs. | Static review cannot prove all future dual-use semantics; opaque Git implementation metadata remains outside Gate A authority. |
| `TM-026` | **Identifier collision, ownership ambiguity, or typed-reference substitution:** two objects share an ID or a reference resolves to an absent, wrong-kind, wrong-record-kind, or wrong-version object. | Namespaced identifiers plus a schema-derived path inventory classifying every reference and stable-ID path exactly once, with explicit identity declarations and expected owner, kind, version, member set, and cardinality. | Enforce inventory totality and disjointness, artifact and logical-version uniqueness, registry composite-member kinds, exact actor typing, local membership, and added-unclassified-path probes. | External identifiers may remain semantically ambiguous even when structurally resolved. |
| `TM-027` | **Correction/retraction erasure or fork:** an unfavorable record disappears, earlier events are rewritten, or two successors claim one predecessor. | Exact predecessor artifact bytes and size, lifecycle-prefix equality, distinct artifact versions, preserved logical identity, and one linear head. | Repository-level lineage graph rejects cycles, forks, orphaned predecessors, duplicate logical versions, and altered history prefixes. | A repository rewrite can remove all local evidence of a record. |
| `TM-028` | **Derived-value self-attestation:** a record supplies plausible operands and a favorable aggregate, validity, sufficiency, or support flag that was never recomputed, or silently shrinks both a self-declared universe and its rows before recomputation. | Require typed executable rule bindings, all operands needed for derivation, and an exact externally bound source universe wherever completeness is claimed. | Recompute each derived value and disposition; reject mismatch and coordinated universe-and-row deletion even when the schema shape is valid. | A correctly recomputed quantity can still rest on false measurements, incomplete upstream custody, or false assumptions. |
| `TM-029` | **Off-policy support inflation:** policy identities are inert, history rows are ambiguous, only logged-action propensities are retained, step ratios are treated as independent trajectories, transformed weights are presented as raw, or trajectories disappear from a self-declared population. | Bind role-typed policy identities to frozen per-history probability tables and an exact versioned dataset trajectory-set manifest; retain unique trajectory, history, and information-set identities, exact history prefixes, complete distributions, support cells, cumulative weights, transformation parameters, and ESS threshold. | Reject role/ref swaps, wrong history contents or freeze times, duplicate or omitted identities or support cells, coordinated trajectory-and-support deletion, incomplete distributions, target-supported zero behavior probability, weight mismatch, or ESS disposition mismatch. | Positivity can appear adequate in a finite sample while remaining weak in the target population; Gate A synthetic manifests do not establish real dataset completeness. |
| `TM-030` | **Graphical-identification laundering:** an acyclic graph and declared adjustment set are treated as proof of causal identification. | Type treatment, outcome, node role, temporal order, observability, prohibited roles, and identification strategy. | Derive strategy-specific validity and reject forbidden mediators, colliders, descendants, or unblocked paths. | Graph correctness and causal assumptions remain scientific questions that static validation cannot establish. |
| `TM-031` | **Unknown hidden by aggregate or event summary:** an unknown required capability is masked by a readiness score, a capability disappears from a self-declared universe, or a recovery outcome conflicts with an incomplete event history. | Require externally bound versioned capability and event-set manifests, exact member reconciliation, unknown propagation, exact unresolved sets, frozen windows, typed events, and derived event-time dispositions. | Recompute readiness and the earliest qualifying recovery, censoring, or competing event; reject coordinated capability/member or event/member deletion. | Upstream measurements, manifest completeness, and event labels can still be wrong; Gate A fixtures are synthetic only. |
| `TM-032` | **Transfer or conformal scope laundering:** metric direction, harmonization, overlap, invariance, target access, tuning, or guarantee assumptions are absent while a result remains qualified. | Separate structured eligibility, empirical result, and guarantee disposition; require every scoped condition. | Reject an eligible or unqualified result when a required condition is failed, unknown, contradictory, or missing. | Required assumptions may be recorded as established without adequate empirical support. |
| `TM-033` | **OOD or worst-group denominator laundering:** counts, rates, coverage, and minimum-information status do not reconcile, or an ineligible group is omitted from the extremum. | Require exact population partitions and typed minimum count, coverage, effective-sample-size, and interval-width criteria. | Recompute totals, rates, group eligibility, ties, partial extrema, and complete-result disposition. | Sparse intersections can remain irreducibly inconclusive even under correct accounting. |
| `TM-034` | **Schema format bypass:** an environment lacks an optional date-time or URI checker while validation reports success. | Use a closed locally implemented format set and reject every undeclared format. | Run positive and negative checker canaries and reason-specific malformed-format fixtures. | The chosen format subset may still be too permissive for a future use case. |
| `TM-035` | **Validation snapshot race:** repository bytes change between semantic validation, inventory construction, and final reporting. | Read one immutable Git-tree or development snapshot and bind its canonical projection digest. | Recheck release identity or the complete development inventory after validation and reject drift. | A hostile process that changes and perfectly restores bytes between observations is outside the non-atomic filesystem guarantee. |
| `TM-036` | **Pre-guard code execution:** user-site, path-shadowed, or modified dependency code executes before offline and read-only controls begin. | Start with a standard-library bootstrap under isolated Python, verify executable and dependency bytes, then enter the locked platform sandbox before third-party import. | Refuse unsupported flags, paths, platform bytes, dependency trees, or sandbox profiles. | A compromised operating system, interpreter, Git binary, or sandbox is outside Gate A's static proof boundary. |
| `TM-037` | **Receipt or transport self-verification:** locally authored receipt fields, an unauthenticated observer, an unauthorized verifier, or evidence created outside the declared chronology is treated as independent proof that a public remote is current or reachable. | Separate internal receipt-chain consistency from an externally acquired, digest-bound transport observation; require distinct observer identity, authentication basis, authorization basis, evidence references, observation scope, and timestamps ordered after the publication event. | Offline validation reports transport as `not_evaluated`; any later transport evaluator resolves evidence IDs, verifies exact packet bindings, enforces observer and verifier roles, and rejects impossible chronology or self-asserted independence. | Remote state can change immediately after an observation, repository artifacts cannot prove human identity or organizational authority, and historical reachability remains unknown without a trusted attestation. |

## 6. Abuse and misuse cases

The architecture must anticipate these foreseeable misuses:

- presenting a Gate A diagram as a deployed safety architecture;
- using readiness as a durable score of an individual rather than a contextual construct;
- treating abstention as failure by the person or as success by automation;
- ranking groups without measurement-validity and uncertainty disclosure;
- asserting standards compliance from a crosswalk row;
- selecting only supported claims while hiding null, invalid, contradictory, or retracted
  records;
- converting retrospective observations into fictional interventions; and
- feeding synthetic fixtures into a real control, employment, insurance, or enforcement
  decision.

Documentation and diagnostics must label Gate A outputs as non-operational and
architecture-only. Mitigating language reduces misuse risk but cannot eliminate it.

## 7. Fail-closed response

For identity, schema, reference, digest, provenance, unknown-state, status, temporal,
fixture, or acceptance errors, validators must:

1. return a nonzero exit status;
2. emit deterministic machine-readable diagnostics with stable rule ID, artifact path,
   object ID where available, and reason;
3. produce no acceptance or scientific-status mutation;
4. make no network request or automatic repair; and
5. preserve all contradictory diagnostics rather than stopping after a favorable subset.

Automatic coercion, imputation, source fetching, status upgrading, signature generation,
or expectation rewriting is forbidden.

## 8. Verification obligations

Gate A must include at least one known-bad fixture for every critical rejection family:
identity/authority mismatch, kind conflation, each epistemic-state coercion class, illegal
status or transition, temporal leakage, missing provenance, bad digest, dangling/wrong-type
reference, manifest mutation/version reuse, denominator mismatch, omitted group,
non-deterministic input, unsupported standards claim, acceptance replay, prohibited private
data, runtime-scope intrusion, missing mission boundary, claim-register mismatch, incomplete
threat coverage, non-normalized belief, ineligible or unresolved evidence basis or consumer binding, unledgered
retained source, excluded-path intrusion, noncanonical complete index, incomplete validation
report, conflicting decision history, and circular evidence indexing.

Gate A 1.2.0 additionally requires reason-specific cases for complete policy distributions,
history-level support, logged-propensity parity, cumulative trajectory weights, causal adjustment
validity, readiness unknown propagation, recovery event derivation, transfer eligibility,
conformal guarantee disposition, OOD partition arithmetic, worst-group information eligibility,
unsupported schema formats, malformed dates and URIs, snapshot drift, launch isolation,
dependency-byte mismatch, exact joint-event identifiability, typed-reference kind substitution,
catalog ID and path uniqueness, transport-observer authority, evidence closure, and receipt-only
transport self-attestation.

Every bad fixture must declare its single primary expected rule ID. It may trigger secondary
diagnostics, but passing for the wrong reason does not satisfy the fixture contract.

Architecture-hardening cases operate on the same immutable snapshot and production diagnostic
functions used by a full validation run. Writing mutated fixtures into the repository during
validation is forbidden. A fixture-only condition that duplicates or weakens the production rule
does not satisfy TM-017 or this obligation.

## 9. Residual-risk statement

Static schemas and validators can establish internal consistency, byte identity, and
declared rejection behavior. They cannot establish that external evidence is true, that a
scientific design is causally identified, that measurements are valid, that all threats are
known, that a reviewer is independent, or that a future implementation will be safe.

These residual risks remain open after architecture completion and after operator
acceptance. Any future gate must create a new threat-model version and evidence set rather
than treating Gate A as inherited operational assurance.
