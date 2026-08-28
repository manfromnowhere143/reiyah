# HARBOR Research Operating Model

## Status and scope

| Field | Value |
|---|---|
| As-of date | 2026-08-25 |
| Lifecycle status | Proposed |
| Authority | Informative research-audit proposal only |
| Gate A membership | Public Gate A `1.2.0` static architecture packet; `architecture_complete`; operator unaccepted |
| Gate B status | Not defined and not authorized |
| Runtime, data collection, training, inference, deployment, or control authorization | False |

This operating model describes how a future HARBOR research program could become
evidence-bearing without weakening Reiyah's current authority, unknown-state, or immutable-release
rules. It creates no role assignment, hiring decision, study approval, data authority,
empirical or scientific publication authority, scientific support, or operator acceptance.

The exact Gate A `1.2.0` canonical report closes `CR-001` through `CR-016` and passes GA-01
through GA-16 with zero diagnostics. Receipt sequence four exists, with publisher transport
`asserted_unverified` and independent transport `not_evaluated`. GA-17 remains `not_evaluated`,
operator acceptance remains `unaccepted`, and runtime and Gate B authorization remain `false`.
These are bounded architecture and distribution states, not scientific results.

A `1.2.1` continuity successor is tracked in
[GitHub issue #1](https://github.com/manfromnowhere143/reiyah/issues/1). This operating model
cannot validate or publish it. Resolve those states only from exact versioned machine records;
absent them, treat the successor as proposed.

The external links in this document are unretained discovery pointers. Their evidentiary labels
are defined in [FRONTIER_BASELINE_2026.md](FRONTIER_BASELINE_2026.md). A linked source is not
retained evidence until exact bytes and constraints enter a versioned source ledger.

## Operating objective

HARBOR should operate as a program of falsifiable research functions, not as one model, one
driver score, one vendor comparison, or one aggregate benchmark. The unit of work is a
versioned research question whose observations, beliefs, decisions, interventions, outcomes,
and evidence remain separately identifiable.

The operating model has four simultaneous duties:

1. preserve what each human and automation actor could know at each decision time;
2. define construct and causal validity before outcome inspection;
3. evaluate selective, transferred, sequential, and subgroup behavior without hiding unknowns;
   and
4. keep scientific judgment, safety assurance, operator acceptance, and release authority
   separate.

The current discovery checkpoint is
[`frontier-discovery-register-1.2.0.json`](../evidence/frontier-discovery-register-1.2.0.json).
It exact-preserves the 38-record `1.1.0` baseline and appends 16 records, for 54 total. Every row
remains pointer-only, evidence-ineligible, payload-free, and non-supporting. The register sharpens
questions about supervision, degraded sensing, recovery opportunity, teleoperation, semantic
failure discovery, human reference models, exposure matching, and claim-to-artifact lineage. It
does not establish a comparator result or Reiyah advantage.

## Authority and role separation

Roles are functions, not titles. A person, vendor, laboratory, or named team receives no
authority merely because a document names it.

| Function | Minimum responsibility | Must remain separate from |
|---|---|---|
| Operator | Authorize scope and make an external decision on exact digests. | Scientific truth, source interpretation, validator output. |
| Program steward | Maintain question inventory, dependency ordering, and release proposals. | Operator acceptance and independent review. |
| Evidence curator | Resolve source identity, retain exact bytes, record constraints, and preserve versions. | Deciding that a claim is supported. |
| Measurement lead | Define latent targets, reference processes, construct validity, and measurement error. | Treating a proxy as ground truth. |
| Human-factors lead | Define tasks, information displays, workload, situation awareness, readiness phases, and recovery behavior. | Product advocacy and operational driver classification. |
| Causal-design lead | Define interventions, assignment, estimands, identification assumptions, falsifiers, and sensitivity analyses. | Outcome-driven relabeling. |
| Sequential-evaluation lead | Define logged trajectories, behavior and target policies, support, estimators, and safety-cost estimands. | Online exploration or deployment. |
| Statistical lead | Define uncertainty, multiplicity, calibration, abstention, subgroup, and transfer analysis. | Selecting a favorable result after inspection. |
| Data steward | Define dataset identity, access, consent, privacy, lineage, splits, leakage, and retention. | Silent private-data ingestion. |
| Benchmark steward | Define comparator eligibility, test cases, contamination controls, maintenance, and sunset rules. | Marketing or leaderboard authority. |
| Safety-case lead | Define hazards, ODD, claims, arguments, evidence, assumptions, defeaters, and change impact. | Scientific acceptance and product release authority. |
| Independent reviewer | Challenge evidence, methods, conflicts, and closure claims from outside the producing workstream. | Authorship of the reviewed artifact where independence is claimed. |
| Validator maintainer | Encode deterministic static rules and reason-specific failures. | Scientific interpretation and operator acceptance. |

One person may perform multiple functions only when the exact conflict is declared and no
independence claim is made. An independent review record must name the reviewer, producing team,
relationship, scope, reviewed digests, conflicts, unresolved objections, and decision boundary.

### Exact team-name rule

Every record must use the exact name and authority limitation present in its source.

- HARBOR is a proposed program name, not evidence that a team exists or is qualified.
- The Tesla Vehicle Safety Report page reviewed for the 2026 frontier baseline does not name a
  scientific analysis team. Reiyah must record that team identity as unknown rather than invent
  Tesla AI, Autopilot team, or another label.
- Mobileye's
  [regulations and safety standards page](https://www.mobileye.com/blog/tackling-global-regulations-and-safety-standards/)
  identifies Mobileye's Sensing Product team and two named employees, while expressly limiting
  their statements to personal perspectives that are not Mobileye's official position.
- A company page reporting an external assessment does not substitute for the assessor's exact
  report, scope, exclusions, findings, certificate identity, and validity period.
- A paper's authors are the authors of that paper. They are not an independent replication team
  unless a separate retained record establishes that role.

## Required research objects

The six Gate A object kinds remain the foundation. Gate A `1.1.0` added typed components for the
minimum static research contracts. Gate A `1.2.0` retained and strengthened that static surface
without creating runtime behavior. The sections below describe the current static contracts and
the evidence a future empirical program would still need.

### Actor and information-set objects

An actor component identifies the person, automation process, reference process, or explicitly
defined joint procedure; its role; version; authority; available channels; and applicable
protocol. It must not contain a product command.

An information-set component identifies:

- the actor and decision or belief time;
- each referenced observation, belief, display, warning, map, policy, or prior action;
- event time, measurement time, availability time, and recorded time;
- whether the item was displayed, perceived, withheld, masked, invalid, or unavailable;
- the disclosure policy and any randomization;
- prohibited future or outcome information; and
- the rule that establishes temporal eligibility.

This closes the current mismatch between the requirements in
[SCIENTIFIC_CHARTER.md](SCIENTIFIC_CHARTER.md) and the fields available in
[observation.schema.json](../schemas/observation.schema.json),
[latent-belief.schema.json](../schemas/latent-belief.schema.json), and
[decision.schema.json](../schemas/decision.schema.json).

### Belief and reference objects

The human-automation contract requires belief holder, target actor or object, latent target, relation,
horizon, state space, conditioning information-set ID, elicitation or inference method,
calibration target, reference-process ID, applicability domain, selective-prediction method,
abstention reason, and measurement validity.

Human belief, automation belief, a human belief about automation, a joint decision procedure,
and reference truth must never share an untyped belief holder. The 2025
[AAAI no-free-lunch result](https://ojs.aaai.org/index.php/AAAI/article/view/33574) and
[NBER collaboration study](https://www.nber.org/papers/w33949) make marginal calibration,
information disclosure, and effort explicit design concerns. Labels:
**EXTERNAL_PRIMARY_UNRETAINED**.

### Opportunity and channel objects

The joint-performance contract uses a common opportunity object with:

- a reference-defined relevant-object set;
- object and temporal correspondence;
- human, automation, and fallback opportunity states;
- channel-specific validity and information availability;
- detection, comprehension, warning, and response criteria;
- channel-specific windows and indication modalities;
- dependence-model and comparator IDs; and
- explicit unknown, invalid, and abstained operands.

The 2026
[PILOT-DSM paper](https://www.sciencedirect.com/science/article/pii/S0001457526002745)
and Mobileye's 2025
[DMS product page](https://www.mobileye.com/blog/presenting-the-mobileye-driver-monitoring-system-fusing-road-safety-inside-the-cabin/)
motivate object-set coverage as a research question. The paper is
**EXTERNAL_PRIMARY_UNRETAINED**. The company page is
**COMPANY_SELF_REPORT_UNRETAINED**.

### Phase and event-process objects

The human-automation contract binds perception, comprehension, projection, decision,
motor initiation, and control-stabilization phases. Each phase should distinguish proxy,
construct, outcome, and reference measurements.

A recovery event process identifies challenge onset, independently defined feasible
window, recovery criterion, event time, censoring type, competing event, invalidity, repeated
attempts, and observation process. Generic scalar measurements and one censoring string are not
enough for a future survival or multistate analysis.

### Policy and trajectory objects

The Gate A `1.1.0` sequential-evaluation contract represents:

- episode, trajectory, time step, state, observation history, action, reward, safety cost, and
  next state;
- behavior-policy and target-policy IDs and exact versions;
- action propensity, whether known or estimated, method, conditioning history, and provenance;
- horizon, discount, terminal state, censoring, missingness, and interference;
- support, overlap, effective sample size, importance-weight tail, truncation, and clipping;
- candidate estimators, nuisance models, hyperparameters, selection data, and holdout boundary;
- estimator agreement or disagreement, uncertainty, and sensitivity; and
- safety constraints and partial-identification bounds.

The design basis includes the 2025
[safety-constrained policy-evaluation paper](https://proceedings.iclr.cc/paper_files/paper/2025/hash/5681251fa039cf49d6d11b906eded1b3-Abstract-Conference.html),
[nonignorable-missingness paper](https://openreview.net/forum?id=So6DMbeAak),
[history-dependent behavior-policy paper](https://openreview.net/forum?id=BrLuZ0HOnb),
and [OPE model-selection paper](https://openreview.net/forum?id=gQ8kIhu8JA).
Labels: **EXTERNAL_PRIMARY_UNRETAINED**.

These objects are specifications only. They do not authorize policy learning, simulation,
network access, vehicle data acquisition, online exploration, inference, or control.

### Dataset, benchmark, scenario, and safety-case objects

The evaluation-assurance contract provides static fields for a dataset release to bind exact
files, versions, digests, media, license, access,
provenance, consent and ethics scope, collection and sensor configurations, participant and
scenario structure, synchronization, missingness, annotation and adjudication, derived lineage,
splits, leakage, contamination, intended uses, prohibited uses, maintenance, corrections, and
sunset.

A benchmark release binds purpose, intended decision, eligible users, tasks, units,
comparator versions, data-access chronology, submission and tuning rules, endpoints,
uncertainty, subgroup and transfer requirements, item-level fidelity, contamination controls,
failure-mode register, change policy, deprecation, and sunset.

A scenario and test-case record binds ODD, unique ID, objective, inputs, steps, platform,
expected result, frequency, criticality, complexity, coverage target, and validity. Candidate
official references are
[ISO 34505:2025](https://www.iso.org/standard/78954.html) and
[ASAM OpenODD 1.0.0](https://publications.pages.asam.net/standards/ASAM_OpenODD/ASAM_OpenODD/latest/specification/index.html).
Labels: **EXTERNAL_OFFICIAL_UNRETAINED**.

A safety-case record binds claim, context, argument, evidence, assumptions, defeaters,
hazards, ODD, acceptance criteria, evidence credibility, implementation checks, change impact,
and in-service evidence. The 2026 paper
[Building a credible case for safety](https://www.sciencedirect.com/science/article/pii/S0022437525001641)
is a candidate methodological source, labeled **EXTERNAL_PRIMARY_UNRETAINED**. Gate A provides
interfaces only and remains outside safety-case authorization.

## Research workstreams

### Workstream A: Ontology and measurement

Deliverables:

- actor, information-set, belief-holder, reference-process, and availability-time contracts;
- construct maps for belief, situation awareness, readiness, recovery, and object relevance;
- multi-method convergent, discriminant, and criterion-validity plans;
- measurement-error, rater, sensor, and reference-process sensitivity; and
- reason-specific known-bad fixtures for temporal availability, actor conflation, proxy
  substitution, and reference leakage.

### Workstream B: Human-automation complementarity

Deliverables:

- human-only, automation-only, team, fallback, better-agent, and complementarity-potential
  comparator definitions;
- disclosure, withholding, workload, effort, adherence, and trust measurements;
- common relevant-object opportunities and joint-miss dependence models;
- object-set and scan-path coverage endpoints; and
- falsifiers for collaboration that performs no better than the best eligible standalone actor.

### Workstream C: Causal and sequential evaluation

Deliverables:

- static and longitudinal causal estimands;
- randomization, quasi-experimental, observational, and off-policy design families;
- causal graphs, negative controls, placebo outcomes, interference, contamination, missingness,
  and censoring plans;
- trajectory and policy-logging contracts;
- support and estimator diagnostics; and
- sensitivity bounds that force inconclusive or invalid status when identification fails.

### Workstream D: Unknowns, transfer, and worst groups

Deliverables:

- novelty and ambiguity rejection;
- calibration-set, exchangeability, and shift-assumption records;
- risk-coverage and error-reject curves;
- group-conditional and target-conditional coverage;
- domain, shift, adaptation, and target-access chronology;
- group-membership validity and uncertainty; and
- simultaneous uncertainty, effective sample size, and low-information dispositions.

The candidate sources are the 2025
[reject-option paper](https://www.sciencedirect.com/science/article/pii/S2666827025000477),
[conformal shift paper](https://proceedings.mlr.press/v258/wang25l.html), and
[group-conditional conformal paper](https://proceedings.mlr.press/v267/gao25c.html).
Labels: **EXTERNAL_PRIMARY_UNRETAINED**.

### Workstream E: Data and benchmark governance

Deliverables:

- dataset, distribution, participant, scenario, sensor, annotation, and split releases;
- rights, access, consent, ethics, privacy, retention, and deletion boundaries;
- duplicate, leakage, contamination, and cross-release lineage checks;
- benchmark purpose, risk, maintenance, correction, deprecation, and sunset records; and
- public and restricted evidence profiles with non-interchangeable digests.

Candidate references are the
[TD2D primary data descriptor](https://www.nature.com/articles/s41597-025-04781-8),
[Croissant RAI specification](https://docs.mlcommons.org/croissant/docs/croissant-rai-spec.html),
[BenchRisk](https://proceedings.neurips.cc/paper_files/paper/2025/hash/92a0af72659802465884eaad8443ea89-Abstract-Datasets_and_Benchmarks_Track.html),
and the 2025
[benchmark-contamination paper](https://proceedings.mlr.press/v267/sun25t.html).
The TD2D descriptor is **EXTERNAL_PRIMARY_UNRETAINED**. Croissant is
**EXTERNAL_OFFICIAL_UNRETAINED**. BenchRisk and the benchmark-contamination paper are
**EXTERNAL_PRIMARY_UNRETAINED**. Their use outside their original domains is a bounded
**REIYAH_INFERENCE**.

### Workstream F: Safety and standards interface

Deliverables:

- hazard, ODD, scenario, test-case, safety-claim, argument, defeater, and evidence interfaces;
- exact standards identities and applicability gaps;
- evidence-diversity and credibility assessment;
- change-impact and invalidation rules; and
- a boundary that prevents scientific results, company reports, validation, and operator
  acceptance from becoming a safety conclusion.

This workstream defines no compliance target and authorizes no safety case, product, or road test.

## Research lifecycle

The proposed lifecycle is sequential and fail-closed.

1. **Question proposal:** Record the question, stakeholders, scope, anticipated harms,
   non-claims, and candidate falsifiers.
2. **Frontier review:** Search primary research and official sources. Label every source and
   preserve unknowns.
3. **Evidence retention:** Retain permitted exact bytes and metadata. Record rights and access
   separately. URL-only items remain pointers.
4. **Construct review:** Freeze actor, target, information set, measurement model, reference
   process, validity, and proxy limitations.
5. **Dataset feasibility:** Define data origin, consent, privacy, collection, lineage, split,
   coverage, and access chronology. No ingestion occurs under Gate A.
6. **Design review:** Freeze design family, estimand, assignment, causal assumptions, sample
   size, power or precision, stopping, missingness, censoring, multiplicity, subgroups, transfer,
   and sensitivity.
7. **Static preregistration:** Digest-bind the complete analysis and observation boundary before
   outcomes become accessible.
8. **Execution authorization:** Requires a separately defined and accepted future gate. It is not
   implied by any earlier stage.
9. **Result construction:** Preserve estimates, uncertainty, coverage, unknowns, deviations,
   assumption checks, estimator disagreement, and invalidity.
10. **Independent review:** Review exact source, protocol, data, code, result, and conflict
    digests. Review cannot create operator acceptance.
11. **Claim decision:** Apply the preregistered rule. Unsupported assumptions force bounded,
    inconclusive, contradicted, or invalid dispositions as specified.
12. **Correction and replication:** Create immutable successors. Retain negative, contradictory,
    corrected, and retracted results.
13. **Release decision:** Separately assess redistribution rights, private-data boundaries,
    safety interpretation, and exact public-profile contents.

## Preregistration minimum

A future preregistration should be invalid unless it binds:

- question, primary hypothesis, contradiction rule, and prohibited interpretation;
- study-design family and unit of assignment, analysis, and dependence;
- population, sampling frame, inclusion, exclusion, recruitment, and observation boundary;
- actor, belief, information-set, display, task, intervention, and comparator versions;
- estimand, outcome, horizon, time zero, event process, and direction;
- measurement model, reference process, validity, and discordance handling;
- sample-size, power, precision, simulation, stopping, interim, and deviation rules;
- causal graph, assumptions, negative controls, interference, contamination, and sensitivity;
- missingness, censoring, competing events, abstention, and OOD;
- dataset releases, split unit, access chronology, preprocessing, and contamination checks;
- primary and secondary metrics, multiplicity, uncertainty, subgroup and transfer analysis;
- sequential-policy, propensity, support, effective-sample-size, and estimator-selection fields
  where applicable;
- seeds and environment only where static deterministic reproduction requires them; and
- exact artifact paths, versions, digests, source IDs, and reviewer scope.

The Gate A `1.1.0` study and application schemas type the static structure needed to express this
minimum. No empirical preregistration, retained study input, executed analysis, or reviewed
numeric decision boundary currently satisfies it.

## Tesla and Mobileye comparator protocol

Tesla and Mobileye may enter HARBOR only as versioned, bounded external comparators.

For Tesla, the comparator record should bind the exact FSD (Supervised) name, software and
hardware versions, vehicle configuration, region, road class, supervision state, engagement and
five-second collision-attribution policy, telemetry capture process, denominator, comparator
fleet, and known exclusions from the
[official report](https://www.tesla.com/fsd/safety). The company report remains
**COMPANY_SELF_REPORT_UNRETAINED** until retained. Even after retention it would remain a
self-report, not independent causal or safety evidence.

For Mobileye, the record should distinguish Surround ADAS, SuperVision, Chauffeur, Drive, DMS,
REM, RSS, hardware, supervision class, and ODD. The
[DMS page](https://www.mobileye.com/blog/presenting-the-mobileye-driver-monitoring-system-fusing-road-safety-inside-the-cabin/)
may motivate an object-attention comparator. Label: **COMPANY_SELF_REPORT_UNRETAINED**. The
[RSS page](https://www.mobileye.com/technology/responsibility-sensitive-safety/)
may motivate a formal-rule comparator. Neither establishes effectiveness, construct validity,
compliance, or safety. Label: **COMPANY_SELF_REPORT_UNRETAINED**.

No cross-vendor comparison is eligible without harmonized opportunity, object, driver,
vehicle, road, region, version, telemetry, outcome, and missingness definitions. Marketing
claims and rolling web counters are not benchmark results.

## Validation model

Static validators test structure and declared semantics only. Gate A `1.1.0` controls include:

- observation availability precedes belief and decision use;
- every belief names a holder, target, information set, reference, calibration target, and
  applicability domain;
- human, automation, joint, fallback, and reference roles cannot resolve to the same untyped ID;
- every readiness component and recovery phase appears with validity and epistemic disposition;
- every joint-miss opportunity contains all channel operands and a dependence policy;
- sequential results bind behavior and target policies, propensities, support, estimator, and
  selection protocol;
- all calibration guarantees carry calibration-set and assumption validity;
- every transfer result binds source, target, shift, adaptation, and access chronology;
- every preregistered group appears with membership validity, effective sample size, coverage,
  uncertainty, and information disposition;
- every dataset and benchmark release binds exact distributions, lineage, rights, splits,
  contamination, maintenance, and sunset;
- every company or team statement retains source type and authority limitation; and
- every public profile counts only included bytes as retained evidence.

Known-bad fixtures mutate canonical artifacts and invoke the same production diagnostics as full
validation. Future empirical validity, numeric thresholds, data quality, and scientific
interpretation remain outside static validation. Passing these checks is an integrity signal, not
scientific evidence.

## Immutable release and distribution model

The historical Gate A 1.0.0 files must not be overwritten. This document and the other 2026 audit
records were first adopted by the add-only public 1.1 architecture lineage and remain present in
the immutable public `1.2.0` packet, with versioned schema, manifest, ledger, index, report, and
governance bindings as applicable. The recovered historical 1.0 anchors and digests remain
separately verifiable, with interrupted custody disclosed in the recovery record.

Future releases should separate:

- an internal retained-evidence profile;
- a public redistribution profile;
- any restricted-data profile; and
- an optional locally augmented profile whose user-supplied source bytes are verified offline.

Each profile needs an exact member inventory, digests, evidence-eligibility rules, rights state,
omission reasons, predecessor relation, and validation report. A pointer may carry an upstream
identity and an expected digest, but it is not retained evidence in a profile that omits the
bytes. Profiles are not interchangeable, and operator acceptance must bind one exact profile.

Static public repository distribution is separately authorized within the exact public custody
inventory. Empirical or scientific publication remains outside Gate A and requires new explicit
authority.

## Gate boundary

### Gate A static closures

The public `1.1.0` packet closed three defects found in the historical packet without executing
research. It represents event, record, and availability time; frozen actor information sets;
belief holder, target, calibration, and applicability; and construct-specific contracts for
human-automation assessment, joint performance, sequential off-policy evaluation, study design,
and evaluation assurance. Exact reference ownership, version binding, epistemic rules, and
reason-specific mutations make those static obligations fail closed.

The public `1.2.0` correction added executable reconciliation, derivation, eligibility,
reference, release-isolation, and transport-separation contracts. Its exact canonical report
records `architecture_complete`, closes `CR-001` through `CR-016`, and leaves GA-17 and
independent transport `not_evaluated`. The sequence-four receipt records only publisher transport
as `asserted_unverified`.

These are architecture closures only. They do not establish that any construct is measurable,
valid, safe, useful, or supported. They do not create retained empirical evidence or authorize
data collection, model execution, a later gate, or empirical or scientific publication.

### Candidate Gate B research prerequisites

The following are future research capabilities and do not make Gate A invalid by their absence:

- retained primary scientific literature and independent review;
- empirical construct-validation protocols;
- eligible datasets and data governance;
- sample-size, stopping, missingness, censoring, and sensitivity plans;
- retained and independently reviewed complementarity, sequential OPE, transfer, worst-group,
  and selective-prediction protocols;
- retained benchmark, scenario, ODD, and safety-case evidence beyond the static interfaces; and
- authorized execution, data collection, analysis, replication, and release processes.

Gate B remains undefined. This list is a proposed prerequisite inventory, not an authorization or
gate specification.

## Stop conditions

Work must stop, record the protocol-applicable state, and avoid unsupported promotion when:

- unresolved project, Git-root, remote, release, or authority identity is `blocked`;
- unavailable source bytes, rights, or exact versions remain `unmeasured` or `blocked`;
- an unestablished actor information set or observation availability makes the affected analysis
  `invalid` or `inconclusive`;
- unsupported reference or measurement validity makes the affected result `invalid` or
  `inconclusive`;
- failed causal identification, positivity, support, or exchangeability receives the declared
  `invalid` or `inconclusive` disposition;
- inapplicable calibration or coverage guarantees are recorded as invalid under the observed
  shift, with the relevant epistemic state preserved;
- an absent required group, domain, channel, phase, or epistemic state invalidates completeness;
- unauthorized private data, empirical publication, runtime, or physical-control work is
  `blocked`;
- an unsubstantiated independence claim is `invalid`; or
- a public profile that counts omitted bytes as retained evidence is `invalid`.
