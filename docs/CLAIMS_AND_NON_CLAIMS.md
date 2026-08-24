# Gate A Claims and Non-Claims Register

| Field | Value |
| --- | --- |
| Document ID | `reiyah.claims-and-nonclaims` |
| Version | `1.0.0` |
| Lifecycle status | `proposed` |
| Applies to | HARBOR Gate A architecture |

This register controls what may be said about Reiyah during Gate A. It contains proposed
research propositions and explicit non-claims. It does not report scientific findings.

## 1. Claim classes

Reiyah distinguishes three classes:

1. **Repository assertions** are narrow, locally inspectable statements about static
   artifacts. Validator success may support an integrity assertion, but not scientific
   truth.
2. **Scientific propositions** are falsifiable hypotheses requiring a frozen protocol and
   retained evidence. Every proposition below remains `proposed`.
3. **Operational, safety, compliance, and superiority claims** are forbidden in Gate A.

Claim identifiers and wording are versioned. Editing the substantive wording creates a new
claim version; it must not silently reuse prior evidence or status.

## 2. Candidate repository assertions

These assertions may be evaluated only after the complete Gate A packet exists. Their
initial status is `proposed`.

| ID | Version | Exact candidate assertion | Current status | Evidence gap | Falsifier | Prohibited interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| `reiyah.claim.repository.kind-separation` | `1.0.0` | Gate A defines observation, latent belief, decision, intervention, outcome, and evidence as separate object kinds. | `proposed` | No exact evidence-index-bound schema and semantic-validation report is linked. | Any eligible record can validate while omitting a kind, impersonating another kind, or using an untyped cross-kind reference. | Future data or a future system necessarily respects the separation. |
| `reiyah.claim.repository.epistemic-separation` | `1.0.0` | Gate A represents `observed`, `missing`, `unmeasured`, `out_of_distribution`, `sensor_invalid`, and `abstained` as distinct epistemic states. | `proposed` | No bound schema plus complete reason-specific fixture report is linked. | Any non-observed state can validate as a zero/false/negative/default, without a reason, or as an alias of another state. | Measurements are valid or the missingness assumptions are correct. |
| `reiyah.claim.repository.lifecycle-separation` | `1.0.0` | Gate A preserves every required lifecycle status without aliasing. | `proposed` | No bound status-schema and transition-fixture report is linked. | A required status is absent/aliased, an illegal transition passes, or prior status history can be overwritten. | Any specific scientific status assignment is valid. |
| `reiyah.claim.repository.offline-validation` | `1.0.0` | Gate A validation is deterministic, offline, and fail-closed for its declared static inputs. | `proposed` | No repeated, network-disabled, byte-compared validation report is linked. | An unchanged replay changes comparable diagnostics/exit status, uses the network, or accepts an unknown/error condition. | The architecture is scientifically correct, secure in every environment, or safe. |
| `reiyah.claim.repository.acceptance-binding` | `1.0.0` | Gate A operator-decision records are digest-bound and separate from validation results. | `proposed` | No bound operator-decision-schema positive/negative fixture report is linked. | A stale/mismatched digest validates, a validator can self-accept, or a record without exact operator identity, authority basis, UTC time, rationale, risk acknowledgement, manifest releases, or matching architecture-completeness evidence validates. | An authorized operator has accepted Gate A. |

No repository assertion is `supported` merely because this document states it. Its
evidence link must name the exact validation report and artifact digests.

## 3. Proposed scientific propositions

The following are research directions with no retained supporting evidence at bootstrap.
Terms such as “improves” or “reveals” are conditional propositions, not results.

| ID | Version | Exact proposed proposition | Required comparator or contrast | Required primary estimand | Current status |
| --- | --- | --- | --- | --- | --- |
| `reiyah.claim.scientific.joint-belief-readiness` | `1.0.0` | Under a frozen task and horizon, an uncertainty-bearing object-level joint driver-vehicle belief yields better readiness decisions than a declared non-joint comparator. | Versioned non-joint and/or driver-only comparator with identical eligible information | Pre-specified difference in task loss, including abstention and invalid-state costs | `proposed` |
| `reiyah.claim.scientific.explicit-unknowns` | `1.0.0` | Explicit epistemic-state handling materially changes estimated readiness error relative to silent coercion or complete-case analysis. | Frozen missingness/invalidity handling strategies | Pre-specified paired difference in error and coverage, stratified by state | `proposed` |
| `reiyah.claim.scientific.joint-silent-miss` | `1.0.0` | Modeling dependence between human and automation miss events changes estimated joint silent-miss risk relative to a declared independence model. | Versioned independence and dependence models on identical opportunities | Difference in calibrated joint-event risk under a frozen event definition | `proposed` |
| `reiyah.claim.scientific.causal-policy-recoverability` | `1.0.0` | A named policy or intervention changes a named recoverability outcome relative to a frozen comparator policy in a declared target population. | Exact policy versions and assignment mechanism | Pre-specified causal contrast over protocol-defined potential outcomes | `proposed` |
| `reiyah.claim.scientific.recoverability-distribution` | `1.0.0` | A pre-specified recoverability distribution identifies failure modes hidden by a single binary readiness label. | Binary-label summary defined before outcome inspection | Difference in protocol-defined decision loss or detected failure strata | `proposed` |
| `reiyah.claim.scientific.transfer-failure` | `1.0.0` | Pre-declared target-domain evaluation identifies transfer failures not visible in pooled source-domain performance. | Frozen source, target, adaptation, and pooled comparators | Target-domain performance delta and uncertainty under declared validity rules | `proposed` |
| `reiyah.claim.scientific.worst-group-gap` | `1.0.0` | Pre-declared worst-group validation identifies materially worse valid-group performance than aggregate reporting alone. | Aggregate metric and complete eligible group set | Worst valid-group metric, aggregate-to-worst gap, uncertainty, and group validity | `proposed` |

### 3.1 Proposition traceability conditions

The falsifiers below are design requirements, not post-hoc decision rules. Each must be
replaced by a numeric or otherwise executable contradiction boundary in the immutable
protocol before preregistration. A result that fails to cross either support or
contradiction boundaries is `null` or `inconclusive` according to the protocol; it is not
automatically a falsifier.

| ID | Current evidence gap | Required falsifier/contradiction condition | Prohibited interpretation |
| --- | --- | --- | --- |
| `reiyah.claim.scientific.joint-belief-readiness` | No frozen task, comparator, eligible dataset, decision-loss threshold, or retained result evidence. | An eligible pre-specified estimate crosses the contradiction boundary in favor of the non-joint comparator after required validity and abstention accounting. | Joint belief is universally better, establishes safety, or describes latent truth. |
| `reiyah.claim.scientific.explicit-unknowns` | No frozen missingness mechanism, coercion comparator, materiality bound, or retained result evidence. | A valid estimate and uncertainty interval fall within the pre-specified equivalence region for no material change across required state strata. | Explicit states eliminate missing-data bias or justify any imputation. |
| `reiyah.claim.scientific.joint-silent-miss` | No frozen joint-opportunity definition, dependence model, event sample, materiality bound, or retained result evidence. | A valid estimate falls within the pre-specified equivalence region between declared dependence and independence risk estimates. | Human and automation misses are independent, or either marginal rate is safe. |
| `reiyah.claim.scientific.causal-policy-recoverability` | No named policy versions, assignment evidence, identified target population, identification assessment, or retained outcome evidence. | Under an eligible design, the causal contrast and uncertainty meet the protocol's contradiction/equivalence rule for no material policy change or the opposite pre-specified direction. | Association, simulation, or policy recommendation establishes causality or deployment benefit. |
| `reiyah.claim.scientific.recoverability-distribution` | No recovered-state definition, binary comparator, failure-stratum rule, censoring rule, or retained result evidence. | The eligible comparison meets the pre-specified contradiction/equivalence rule: no additional valid failure stratum and no material decision-loss difference. | Binary readiness labels are always inadequate or recovery is guaranteed. |
| `reiyah.claim.scientific.transfer-failure` | No frozen source/target domains, access chronology, adaptation allowance, transfer comparator, or retained result evidence. | All declared target-domain gaps and failure criteria remain within their pre-specified equivalence/acceptability bounds under valid target coverage. | Successful evaluation in one target proves generalization to other domains. |
| `reiyah.claim.scientific.worst-group-gap` | No frozen group universe, membership validity, minimum support rule, materiality bound, or retained result evidence. | With every eligible group represented, the aggregate-to-worst valid-group gap remains within the pre-specified equivalence bound. | A small gap establishes fairness, safety, or adequacy for missing/invalid groups. |

Before any proposition becomes `preregistered`, its manifest must replace every generic
term with an operational definition; name population, unit, context, time zero, horizon,
endpoint, applicability domain, exclusion rule, subgroup set, uncertainty method,
decision threshold, and contradiction rule; and bind exact comparator and evidence inputs.

## 4. Explicit non-claims

The following statements are not authorized, including as marketing shorthand, abstract
language, diagram captions, metadata, or implications. Every `reiyah.nonclaim.*` record has lifecycle
status `proposed` because this register itself is proposed. For every
`reiyah.nonclaim.*` record,
`evidence_gap` and `falsifier` are explicitly **not applicable**: each is a normative Gate A
scope boundary, not an empirical proposition. Evidence cannot falsify a current boundary;
only a superseding, operator-authorized contract version can change it. The forbidden
statement in the fourth column is the record's `prohibited_interpretation`.

| ID | Version | Lifecycle status | Reiyah/HARBOR does **not** claim that… | Why prohibited at Gate A |
| --- | --- | --- | --- | --- |
| `reiyah.nonclaim.driver-monitoring-classifier` | `1.0.0` | `proposed` | it is a driver-monitoring classifier or a replacement for one. | The mission is an evidence and benchmark engine with a joint object-level scope. |
| `reiyah.nonclaim.context-free-readiness` | `1.0.0` | `proposed` | it measures a person's universal, intrinsic, or context-free readiness. | Readiness must be task-, horizon-, context-, and loss-relative. |
| `reiyah.nonclaim.live-operation` | `1.0.0` | `proposed` | it performs live sensing, monitoring, inference, intervention, alerting, or vehicle control. | No runtime or physical-control integration is authorized. |
| `reiyah.nonclaim.safety-or-deployment` | `1.0.0` | `proposed` | it is safe, safer, validated for safety, fail-safe, or suitable for deployment. | Gate A contains architecture checks, not operational safety evidence. |
| `reiyah.nonclaim.compliance-or-certification` | `1.0.0` | `proposed` | it complies with, is certified under, or satisfies any law, regulation, or standard. | Crosswalks expose mappings and gaps only; no compliance determination exists. |
| `reiyah.nonclaim.benchmark-superiority` | `1.0.0` | `proposed` | any benchmark, model, policy, or representation is superior. | No accepted protocol or eligible benchmark result exists. |
| `reiyah.nonclaim.association-is-causation` | `1.0.0` | `proposed` | an association, prediction, simulation, or retrospective comparison is a causal policy effect. | Causal claims require explicit estimands and identification assumptions. |
| `reiyah.nonclaim.absence-is-negative` | `1.0.0` | `proposed` | absence of an observation means zero, false, normal, safe, or a negative class. | Epistemic states must remain explicit and distinct. |
| `reiyah.nonclaim.belief-is-truth` | `1.0.0` | `proposed` | a latent belief is ground truth or a calibrated probability merely because it is numeric. | Beliefs require target, method, uncertainty, validity, and calibration evidence. |
| `reiyah.nonclaim.decision-is-intervention` | `1.0.0` | `proposed` | a decision occurred as an intervention, or an intervention caused a later outcome. | Decision, exposure, outcome, and causal effect are separate constructs. |
| `reiyah.nonclaim.aggregate-establishes-transfer-fairness` | `1.0.0` | `proposed` | aggregate performance establishes transfer, fairness, or worst-group adequacy. | Domains and all eligible groups require separate validity and uncertainty reporting. |
| `reiyah.nonclaim.omit-invalid-group` | `1.0.0` | `proposed` | a missing or invalid group may be omitted from worst-group analysis. | Omission changes the target and can conceal uncertainty or harm. |
| `reiyah.nonclaim.integrity-signal-is-evidence` | `1.0.0` | `proposed` | generated prose, model review, consensus, a signature, a checksum, or a passing test is scientific evidence. | These are proposals, reviews, integrity signals, or acceptance signals only. |
| `reiyah.nonclaim.external-authority` | `1.0.0` | `proposed` | an external model, dataset, paper, MCP server, standard, or sibling repository has Reiyah authority. | External systems are untrusted adapters or evidence sources. |
| `reiyah.nonclaim.validation-is-acceptance` | `1.0.0` | `proposed` | Gate A is accepted because its architecture is complete or validators pass. | Acceptance requires a separate authorized, digest-bound operator record. |
| `reiyah.nonclaim.harbor-name-final` | `1.0.0` | `proposed` | the HARBOR name or expansion is final. | It remains a proposed working name pending explicit operator review. |
| `reiyah.nonclaim.retention-is-truth` | `1.0.0` | `proposed` | retained evidence is true merely because its bytes and digest are recorded. | Retention establishes identity and provenance, not truth or applicability. |
| `reiyah.nonclaim.adverse-status-is-support` | `1.0.0` | `proposed` | a `null`, `inconclusive`, `failed`, `invalid`, `contradicted`, or `retracted` result supports a proposition. | These statuses have distinct meanings and cannot be laundered into support. |
| `reiyah.nonclaim.private-data-authorized` | `1.0.0` | `proposed` | Gate A authorizes collection or ingestion of private human or vehicle data. | Only static architecture artifacts and deterministic fixtures are authorized. |
| `reiyah.nonclaim.publication-ready` | `1.0.0` | `proposed` | Reiyah is ready for publication or public benchmark release. | Publication machinery and public claims are outside Gate A. |

## 5. Claim admission record

Gate A has no machine path for advancing a claim beyond `proposed`. The following is a
future-gate admission contract, not a Gate A capability or publication workflow. A claim may
enter a future evidence index only if its separately authorized machine-readable record
includes:

- stable claim identifier, claim version, and exact wording;
- claim class and current lifecycle status with append-only history;
- author, creation time, and all correction or supersession links;
- target population, unit, scope, operational context, and applicability boundary;
- exact comparator, endpoint, time horizon, estimand, and uncertainty rule;
- protocol identifier, immutable version, digest, and preregistration timing;
- complete supporting, contradictory, null, invalid, and retracted evidence links;
- source versions, publication dates, retained-byte digests, and access constraints;
- subgroup, intersection, transfer-domain, missingness, and abstention handling;
- limitations, unresolved threats, and falsification/contradiction criteria; and
- reviewer decisions separated from operator acceptance.

Unknown or inapplicable values must be explicit; blank fields cannot be interpreted as
“none.” A claim with a missing required field remains `proposed` or becomes `blocked` or
`invalid` under the applicable protocol.

## 6. Language by status

| Status family | Permitted formulation | Forbidden implication |
| --- | --- | --- |
| `proposed`, `exploratory` | “We propose…”, “An exploratory analysis suggests…” | confirmation, validation, causality, generality |
| `preregistered`, `running` | “The protocol specifies…”, “Evaluation is running…” | result, trend, success |
| `blocked`, `invalid`, `failed` | State the exact blocker, invalidity, or failed criterion | substantive null or contradiction unless separately established |
| `null`, `inconclusive` | State the frozen decision rule and uncertainty | equivalence, absence of effect, safety |
| `supported`, `contradicted` | Quote exact proposition and bounded protocol scope | truth outside scope or independent replication |
| `replicated` | State the independent replication protocol and scope | universal truth or deployment readiness |
| `corrected`, `retracted` | Link prior and successor records and explain impact | erasure of the prior record or unchanged support |

## 7. Review and change control

Scientific review may recommend a status but cannot fabricate evidence or operator
acceptance. Status events and claim versions are append-only. Corrections must create a
new version linked to the superseded record; retractions remain discoverable.

This register itself remains `proposed` until it is included by exact path and digest in a
Gate A evidence index and separately accepted by an authorized operator. Acceptance of the
register would approve the architecture boundary only, not the scientific propositions.
