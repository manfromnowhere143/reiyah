# HARBOR Scientific Charter

| Field | Value |
| --- | --- |
| Document ID | `reiyah.scientific-charter` |
| Version | `1.1.0` |
| Lifecycle status | `proposed` |
| Program name | HARBOR, Human-Automation Readiness, Belief & Operational Risk |
| Authority | Candidate architecture subordinate to `AGENTS.md` |
| Scope | Gate A architecture and deterministic offline evaluation contracts only |

The HARBOR name, its expansion, and every scientific proposition in this document are
proposed. This charter is not evidence of scientific validity, operational readiness,
safety, standards compliance, or operator acceptance.

## 1. Normative language

In this document, **must** and **must not** state Gate A requirements. **Should** states a
review expectation that requires an explicit rationale when not followed. Informative
explanations do not override the requirements.

## 2. Mission and boundary

Reiyah is an evidence and benchmark engine for studying object-level driver-vehicle
belief, human-automation readiness, recoverability, joint silent misses, causal policy
effects, explicit unknowns, transfer, and worst-group performance.

Reiyah is not a driver-monitoring classifier. Gate A does not authorize live sensing,
model training or inference, private-data ingestion, vehicle control, deployment,
empirical or scientific publication, or an operational safety decision. It defines a reviewable scientific
contract and static mechanisms that can reject malformed architecture artifacts.

## 3. Scientific questions

The program is organized around questions, not foregone conclusions:

1. Can an object-level joint representation of driver, vehicle, automation, environment,
   and salient entities support better-specified readiness estimates than declared
   comparators?
2. Under a named request, intervention, or hazard horizon, what is the distribution of
   time and conditions required to regain a protocol-defined recoverable state?
3. When do human and automation channels fail silently together, and how should their
   dependence change risk estimates?
4. What causal effect does a named policy or intervention have on a pre-specified outcome
   under explicit identification assumptions?
5. Which results transfer across declared domains, and where do they fail under explicit
   out-of-distribution tests?
6. What is the performance and uncertainty of every pre-declared group, including the
   worst valid group, without hiding small, missing, or invalid groups?

Each question must be converted to a versioned protocol with a population, unit of
analysis, comparator, estimand, endpoint, time horizon, validity rules, uncertainty rule,
and rejection criteria before its status can become `preregistered`.

Preregistered status additionally requires a retained typed preregistration record that
binds the exact experiment and analysis-specification artifacts and versions, the exact
protocol release, a UTC freeze time, and a declared later observation boundary. Indexed
narrative text is not a preregistration record, and neither preregistration nor the record
authorizes runtime execution.

## 4. Unit of analysis

The default root unit is a versioned **person-vehicle-automation encounter**, never a person
alone. An **object episode** is a scoped interval within an encounter for an identified
physical or operational object, such as a road actor, control affordance, hazard, or
automation state. A protocol must select and name its analytic unit and must state how
dependence across time, objects, people, vehicles, encounters, sites, and repeated episodes
is handled.

Object identity must be explicit. Merging, splitting, loss of track, identity uncertainty,
and reacquisition must be represented as events or validity states; they must not be
silently converted into a continuous, confidently identified object.

## 5. Six-layer scientific ontology

Every scientific record must declare exactly one of these object kinds. Shared identifiers
may connect kinds, but no kind may impersonate another.

| Kind | Meaning | Required conceptual content | Must not be treated as |
| --- | --- | --- | --- |
| `observation` | A measurement or recorded assertion available at a declared time | source, measurement time, availability time, validity state, provenance | ground truth, latent state, or outcome merely because it was recorded |
| `latent_belief` | A distribution, set, interval, or explicit abstention over an unobserved state | target, conditioning observations, method/version, uncertainty, validity | an observation or known fact |
| `decision` | A protocol-defined selection, classification, ranking, or proposed action | decision time, information set, policy/version, alternatives, abstention semantics | an intervention that actually occurred |
| `intervention` | A recorded, assigned, or hypothetical exposure intended to change a process | assignment/exposure type, time, dose or policy, compliance, provenance | a decision, outcome, or causal effect |
| `outcome` | A protocol-defined post-index event or quantity used to assess a question | outcome window, ascertainment rule, validity, provenance | a contemporaneous input or intervention |
| `evidence` | Retained source bytes plus provenance, or a derivation whose complete input chain terminates in retained source bytes | source identity, exact version, bytes/digest and derivation where applicable, access constraints, scope | scientific truth, acceptance, or a substitute for the five other kinds |

### 5.1 Separation requirements

- Each kind must use its own stable identifier namespace, provenance, event time, and
  record-creation time.
- An observation used to construct a latent belief must be referenced, not copied and
  relabeled as belief.
- A decision must identify the information available at decision time. Later observations
  and outcomes are forbidden from that information set.
- An intended decision and an observed intervention must remain distinct even when their
  values match.
- Outcome ascertainment must be specified independently of the decision being scored.
- Evidence records may support or contradict claims only through an explicit claim-evidence
  link. A checksum proves byte identity, not truth.
- Linked observations, beliefs, decisions, interventions, and outcomes must carry identical
  protocol-owned encounter-construction, object-identity, and temporal-correspondence rules.
  Evidence inherits context through typed targets rather than shared strings alone.
- Provenance inputs must follow the exact protocol dependency table and the complete
  scientific graph must be acyclic, including evidence-to-evidence derivations.

## 6. Time and provenance

At minimum, protocols must distinguish:

- **event time:** when the represented event occurred;
- **availability time:** when it could legitimately enter a decision information set;
- **recorded time:** when the repository record was created; and
- **review time:** when a reviewer made a recorded decision.

Time basis, precision, timezone or monotonic-clock semantics, interval closure, and allowed
clock uncertainty must be declared. A missing timestamp is not time zero. Ambiguous
ordering must remain ambiguous and must not be resolved using outcomes.

Every derived record must identify its immediate inputs, derivation method and version,
and deterministic parameters. Provenance chains must terminate in retained evidence or an
explicitly declared unavailable/untrusted source boundary.

## 7. Epistemic state and unknowns

Every value that can be unavailable or invalid must carry one of these explicit epistemic
states:

| State | Meaning |
| --- | --- |
| `observed` | A value is present and valid under the declared measurement contract. |
| `missing` | A value expected under the contract is absent for a recorded known or explicitly unknown reason. |
| `unmeasured` | The protocol or acquisition process did not attempt this measurement. |
| `out_of_distribution` | The value or context lies outside the declared applicability domain. |
| `sensor_invalid` | Measurement was attempted but failed a declared sensor or quality rule. |
| `abstained` | A method explicitly declined to produce a value under its declared rule. |

Every non-`observed` state must include a reason. Protocols may add structured detail but
must not merge these states. None may be encoded as numeric zero, Boolean false, a negative
class, normality, success, or a confident label. JSON `null`, omission, sentinel numbers,
and empty strings are not substitutes for an epistemic state.

Analyses must report denominators before and after every exclusion, the count of each
epistemic state, and the sensitivity of conclusions to permitted missingness assumptions.
An applicability-domain failure must not be presented as ordinary in-domain error.

## 8. Lifecycle status model

The allowed lifecycle values are exactly:

`proposed`, `exploratory`, `preregistered`, `running`, `blocked`, `invalid`, `null`,
`inconclusive`, `failed`, `supported`, `contradicted`, `replicated`, `corrected`, and
`retracted`.

They are not interchangeable:

| Status | Required interpretation |
| --- | --- |
| `proposed` | Candidate wording or design; neither accepted nor evidentially established. |
| `exploratory` | Analysis was not governed by a frozen preregistered protocol. |
| `preregistered` | Exact protocol was immutable and digest-bound before eligible analysis began. |
| `running` | Authorized evaluation has begun and no terminal result is assigned. |
| `blocked` | Progress stopped for a recorded dependency or authority reason. |
| `invalid` | A design, data, execution, or integrity violation prevents the intended inference. |
| `null` | A valid pre-specified analysis produced a protocol-defined null result; it never means unavailable data. |
| `inconclusive` | Valid evidence cannot resolve the proposition under the declared decision rule. |
| `failed` | A declared execution, quality, or performance criterion was not met; this is not automatically scientific contradiction. |
| `supported` | Retained evidence for the exact proposition met its pre-specified evidentiary rule within its stated scope. |
| `contradicted` | Retained evidence for the exact proposition met its pre-specified contradiction rule within its stated scope. |
| `replicated` | An eligible independent replication met the pre-specified replication rule. |
| `corrected` | A discoverable successor fixes a recorded defect without erasing prior history. |
| `retracted` | The record is withdrawn for a stated reason but remains discoverable and must not be treated as current support. |

Status changes must be append-only events containing a stable event ID, contiguous sequence,
typed actor, exact UTC time, prior status, new status, reason, versioned evidence references,
and the exact predecessor artifact identity, kind, schema, version, path, and digest. Only a
`proposed` root has null prior fields. The successor does not embed its own digest; the index
binds that artifact externally. `null`, `inconclusive`, and `failed` must never be used as
generic synonyms. Detailed transition semantics are defined in `docs/STATUS_MODEL.md`; the
allowed entity/status pairs are owned by the exact protocol release rather than validator
code.

## 9. Core constructs and minimum protocol contracts

### 9.1 Object-level driver-vehicle belief

A belief is a time-indexed uncertainty-bearing representation over a declared latent state
for identified objects and relations. It must declare the conditioning information set,
applicability domain, calibration target, and abstention rule. It must not be presented as
the latent truth. An observed categorical belief's probability sum is checked against the
exact owning protocol's target and absolute tolerance; Gate A fixes that tolerance at
`0.000001`, and a record cannot choose a different value.

### 9.2 Readiness

Readiness is not a universal person label. It must be defined relative to a named task or
intervention, initiation time, horizon, operating context, required capabilities, and loss
function. A protocol must state whether readiness is an estimated probability,
distribution, set, ordinal construct, or decision rule.

### 9.3 Recoverability

Recoverability must be defined as an outcome or potential-outcome quantity relative to a
specified challenge onset, a feasible recovery window defined independently of the observed
response, and a protocol-defined safe recovery condition. Time to recovery, failure to
recover, right-censoring, competing events, and epistemic invalidity must remain distinct.

### 9.4 Joint silent miss

A silent miss requires a pre-specified relevant condition established by an independent
reference process, human-channel and automation-channel opportunities, detection criteria,
response windows, and absence-of-warning or fallback semantics. Joint risk must model
dependence; multiplying marginal miss rates is not allowed without a justified independence
assumption. Unobserved opportunities and invalid channels must not count as successful
detections or misses.

### 9.5 Causal policy effect

A causal claim must name the treatment or policy versions, assignment mechanism, target
population, potential-outcome estimand, time zero, comparator, interference assumptions,
identification assumptions, censoring, and sensitivity analyses. Association, prediction,
or post-hoc policy simulation alone cannot establish a causal effect.

### 9.6 Transfer

A transfer evaluation must freeze a source domain, target domain, adaptation allowance,
comparator, endpoint, and shift taxonomy before target outcomes are inspected. Domain
identity and out-of-distribution states must be retained. Pooled performance cannot replace
target-domain reporting.

### 9.7 Worst-group validation

Groups and intersection rules must be declared before outcome inspection. Every eligible
group's denominator, epistemic-state counts, estimate, uncertainty, and validity must be
reported. An empty, underpowered, missing, or invalid group must remain explicit; it cannot
be dropped so that a different group becomes the reported worst group.

The mathematical definitions and admissible estimands are specified separately in
`docs/MATHEMATICAL_SPECIFICATION.md`.

Gate A 1.1 represents these minimum contracts in strict static schemas and synthetic fixtures.
That closes a representability and rejection-logic gap only. It does not validate any construct,
measurement, estimator, comparator, threshold, policy, dataset, or safety argument. The exact
scientific contract profile must classify every reference-bearing field by JSON path as
document-local, owned by the protocol definition registry, or an exact versioned external
reference, with expected kind and cardinality. An unclassified or unresolved identifier is
invalid.

## 10. Comparator, benchmark, and evaluation discipline

Every benchmark protocol must bind:

1. an immutable protocol identifier and version;
2. a population, episode definition, inclusion rule, and fixed split policy;
3. a complete comparator name, version, configuration, and allowed inputs;
4. primary and secondary endpoints, estimands, thresholds, and uncertainty methods;
5. information-availability and leakage controls;
6. subgroup and transfer-domain definitions;
7. explicit epistemic-state and abstention scoring;
8. multiplicity and exploratory-analysis handling;
9. deterministic environment and randomization seeds where randomness is permitted; and
10. failure, invalidation, correction, and retraction rules.

The typed analysis specification additionally names one primary metric and binds each
metric's estimand, outcome, direction, decision rule, abstention rule, uncertainty method,
confidence level, population, and comparator. A metric-derived result status must equal the
primary metric's interpretation status; correction and retraction remain lineage statuses.

The exact protocol release must also digest-bind its typed definition registry, lifecycle
transition policy, scientific-dependency policy, evidence-binding policy, and
result-to-experiment eligibility policy.
Registry entries and protocol estimands remain `proposed` at Gate A. Registry resolution
includes member checks for state spaces and choice sets; mere identifier existence is not
sufficient.

Changing any bound item produces a new protocol release. A favorable result from one
scope must not be generalized to another population, domain, outcome, horizon, or
comparator.

## 11. Evidence and claims

Gate A's claim register is deliberately proposal-only: it cannot represent or confer a
terminal claim status. The claim requirements below govern a future, separately authorized
versioned claim-record contract; they do not add publication machinery or claim-advancement
capability to Gate A.

- Each future claim record must have a stable identifier, exact versioned wording, lifecycle status,
  scope, comparator, protocol link, and versioned evidence-reference set. A bare evidence ID
  is not an exact binding.
- External sources count as retained evidence only when exact bytes, metadata, version,
  publication date, scope, access or license constraints, and digest are recorded in
  `evidence/source-ledger-1.1.0.json` and retained where permitted under `evidence/sources/`.
- Standards mappings in `evidence/standards-crosswalk-1.1.0.json` are gap maps, not compliance
  determinations.
- Generated prose, model output, peer agreement, signatures, checksums, validator success,
  and operator acceptance are not independent scientific evidence.
- Conflicting, corrected, and retracted evidence must remain visible. Evidence must never
  be deleted merely because it weakens a proposition.
- A future claim record can become `supported`, `contradicted`, or `replicated` only through its frozen
  protocol and decision rule. Operator acceptance cannot manufacture that status.
- Terminal consumers require at least one protocol-compatible evidence witness. Matching
  evidence statuses witness invalid, inconclusive, failed, contradicted, and replicated
  dispositions; supported or replicated evidence may witness support; and a null disposition
  requires supported evidence meeting its frozen null criterion. Corrected evidence is not a
  sole support-like witness.
- A terminal scientific result must bind an exact experiment version under the same protocol
  and analysis specification. The experiment must currently be `running` or be a validated
  `corrected` successor whose history contains `preregistered` before `running`, with a
  retained preregistration that passes binding, freeze-parity, and pre-boundary chronology.
  Proposed, exploratory-only, preregistered-only, blocked, invalid, failed, or retracted
  experiments are ineligible.
- Every experiment and typed analysis specification freezes exactly the population, object,
  time, sensor, reference, support, and protocol validity boundaries. Results inherit that
  exact seven-dimension set through the versioned experiment reference.

## 12. Falsifiability and negative evidence

Each scientific proposition must identify an observation or result pattern that would
contradict it and a separate pattern that would be inconclusive. Protocols must preserve
negative, null, failed, invalid, and contradictory results. Stopping, exclusion, endpoint
changes, subgroup changes, and comparator changes after eligible outcome inspection must
be recorded as deviations and cannot remain labeled `preregistered` without a superseding
protocol.

## 13. Human, fairness, and privacy boundary

Gate A contains no private or operational human data. Future protocols, if separately
authorized, must justify every human attribute, minimize data, define access and retention,
address consent or other applicable authority, assess measurement validity across groups,
and prevent group labels from being used as proxies for intrinsic capability. This charter
does not establish ethical, legal, privacy, or regulatory compliance.

## 14. Independence and authority

External models, tools, MCP servers, sources, datasets, standards, reviewers, and sibling
repositories are untrusted inputs or evidence sources. None can accept Gate A, set a
scientific status, or authorize publication or deployment. Scientific review, repository
integrity validation, and operator acceptance are separate functions.

## 15. Gate A completion and acceptance

Gate A can be described as **architecture-complete** only after all required artifacts,
schemas, deterministic fixtures, cross-references, and offline validators pass the frozen
Gate A validation contract. This does not mean Gate A is accepted.

Acceptance requires an authorized operator record naming the exact evidence-index path and
digest, mission and protocol releases, architecture-completeness evidence for that digest,
decision, operator identity and authority basis, UTC decision time, rationale, and
acknowledged residual risks. Any change to a hash-bound accepted artifact invalidates that
acceptance and requires a new record.
