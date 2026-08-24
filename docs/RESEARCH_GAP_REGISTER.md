# HARBOR Research Gap Register

## Status and interpretation

| Field | Value |
|---|---|
| As-of date | 2026-08-24 |
| Lifecycle status | Proposed |
| Authority | Forensic research-audit record only |
| Gate A membership | Gate A `1.1.1` governance-correction candidate with frozen public `1.1.0` predecessor; operator unaccepted |
| Gate B status | Not defined and not authorized |
| Runtime authorization | False |

This register separates defects in the current semantic architecture from research capabilities
that belong only in a separately authorized future gate. It also separates public-distribution
work from scientific evidence.

The register records the audit basis for the frozen Gate A `1.1.0` packet and its narrow `1.1.1`
governance-correction candidate. It does not itself amend a schema, manifest, validation plan,
evidence index, validation report, or operator decision. External links use the evidence labels in
[FRONTIER_BASELINE_2026.md](FRONTIER_BASELINE_2026.md). Every linked but unretained source is a
discovery pointer, not retained evidence.

## Classification

Classification records the type of the original finding. The separate status field records
whether the finding remains open or has a bounded closure.

| Classification | Meaning |
|---|---|
| **GATE_A_SEMANTIC_BLOCKER** | Normative Gate A prose required a static semantic property that the audited schemas and production validation could not represent or enforce. |
| **GATE_A_RELEASE_BLOCKER** | The live repository or release description did not match the exact frozen closeout state. |
| **GATE_B_RESEARCH_PREREQUISITE** | A candidate scientific capability needed before an empirical HARBOR program could be credible. Its absence does not authorize Gate B and is not automatically a defect in the limited Gate A bootstrap. |
| **PUBLIC_RELEASE_PREREQUISITE** | Rights, custody, distribution, or reproducibility work needed before a public packet could be described honestly. Empirical or scientific publication remains unauthorized. |
| **RESIDUAL_UNKNOWN** | A material fact that current evidence cannot resolve. |
| **NON_BLOCKER** | A current Gate A boundary or integrity feature that should be preserved. |

Priorities are P0 for immediate semantic or release integrity, P1 for required research design
before any study, and P2 for later assurance or release maturity.

## Gate A semantic audit closures

### RGA-001: Observation availability and decision information set

| Field | Value |
|---|---|
| Priority | P0 |
| Classification | **GATE_A_SEMANTIC_BLOCKER** |
| Status | Closed for static architecture in Gate A `1.1.0`; no empirical support created |
| Current requirement | [SCIENTIFIC_CHARTER.md](SCIENTIFIC_CHARTER.md), sections 5 and 6, requires measurement time, availability time, decision information-set membership, and exclusion of later observations. [THREAT_MODEL.md](THREAT_MODEL.md), TM-009, claims this leakage is detectable. |
| Historical finding | The `1.0.0` observation and decision objects could not demonstrate that an input was available to the relevant actor at belief or decision time. Event time and recorded time were not substitutes for availability time. |
| Gate A 1.1 closure | [human-automation-assessment.schema.json](../schemas/v1.1/human-automation-assessment.schema.json) separates observation definitions from event, recorded, and availability measurements; binds frozen belief and decision information sets; records source actors and disclosure; and requires production chronology and membership reconciliation. |
| Failure consequence | Temporal leakage can remain semantically unrepresentable while GA-13 and TM-009 appear satisfied. |
| Closure evidence | Gate A `1.1.0` schemas, typed known-good fixtures, reason-specific temporal and membership mutations, exhaustive reference classification, and production validation. |

### RGA-002: Belief holder, target, conditioning, and calibration

| Field | Value |
|---|---|
| Priority | P0 |
| Classification | **GATE_A_SEMANTIC_BLOCKER** |
| Status | Closed for static architecture in Gate A `1.1.0`; construct validity remains unknown |
| Current requirement | [SCIENTIFIC_CHARTER.md](SCIENTIFIC_CHARTER.md), section 9.1, requires conditioning information set, applicability domain, calibration target, and abstention. [ARCHITECTURE.md](ARCHITECTURE.md), section 7, requires target, conditioning observations, method, applicability, and abstention. |
| Historical finding | The `1.0.0` latent-belief object had no mandatory belief-holder role, target-agent relation, conditioning information-set ID, calibration target, reference-process ID, or explicit applicability domain. |
| Gate A 1.1 closure | The human-automation contract binds holder and actor type, target agent or object, frozen conditioning information, applicability domain, calibration target, reference process, scoring and loss rules, explicit abstention, and a state distribution constrained to the exact named state space. |
| Frontier basis | [AAAI 2025 no-free-lunch paper](https://ojs.aaai.org/index.php/AAAI/article/view/33574) and [NBER 2025 collaboration paper](https://www.nber.org/papers/w33949), both **EXTERNAL_PRIMARY_UNRETAINED**. |
| Failure consequence | Joint belief and complementarity can be ambiguous or unfalsifiable even when probability normalization passes. |
| Closure evidence | Gate A `1.1.0` schema, typed definition registry, known-good fixture, actor and calibration mutations, state-space containment mutation, and production validation. |

### RGA-003: Seven construct-specific minimum contracts are not machine enforced

| Field | Value |
|---|---|
| Priority | P0 |
| Classification | **GATE_A_SEMANTIC_BLOCKER** |
| Status | Closed for static architecture in Gate A `1.1.0`; execution and evidence remain unauthorized |
| Current requirement | [ARCHITECTURE.md](ARCHITECTURE.md), section 7, calls its object-belief, readiness, recoverability, joint-silent-miss, causal, transfer, and worst-group fields minimum static contracts and states that prose does not replace machine-checked bindings. |
| Historical finding | The `1.0.0` generic analysis and result objects could validate while omitting the architecture document's own construct-specific minimum. |
| Gate A 1.1 closure | Five application schemas now type human belief, readiness and recoverability; joint opportunity, dependence, transfer, selective prediction, OOD, conformal and worst-group evaluation; sequential OPE; study design and preregistration; and ODD, dataset, scenario, test, benchmark and safety-case assurance. |
| Failure consequence | A future preregistration or result can validate while omitting the architecture document's own declared minimum. |
| Closure evidence | Gate A `1.1.0` application schemas, scientific contract profile, protocol definition registry, typed fixtures, full required-property mutation sweep, and construct-specific production rules. |

## Current Gate A release blockers

### RGA-004: Live Git remote contradicted the frozen handoff

| Field | Value |
|---|---|
| Priority | P0 |
| Classification | **GATE_A_RELEASE_BLOCKER** |
| Status | Closed for repository identity and frozen `1.1.0` transport on 2026-08-23; the receipt remains separate from the pre-distribution index |
| Historical bytes | The historical `1.0.0` handoff said no remote was assumed or configured. |
| Verified live observation | Git root inspection, `gh` authentication, and GitHub repository inspection identify origin as `https://github.com/manfromnowhere143/reiyah.git`, owned by the authenticated account and configured public. The user explicitly directed that Reiyah remain open source and authorized the static push. |
| Closure | The `1.1.0` handoff records the verified public remote without granting it scientific, safety, acceptance, or publication authority. Post-push commit identity and readback are bound by the RGA-020 closure and the append-only distribution receipt. |
| Failure consequence | The remote gains no authority, but release identity, reproducibility, and closeout reporting are inconsistent. |
| Closure evidence | Verified Git root and origin, authenticated GitHub owner, public visibility, explicit operator distribution instruction, successor handoff, and later transport receipt. |

### RGA-005: Authorized add-only audit documents are outside the frozen index

| Field | Value |
|---|---|
| Priority | P0 |
| Classification | **GATE_A_RELEASE_BLOCKER** |
| Status | Closed by the add-only Gate A `1.1.0` candidate; operator acceptance remains uncreated |
| Historical closeout | The retained Gate A `1.0.0` index and report remain historical evidence for their exact bytes. They are not silently rewritten or treated as current validation. |
| New paths | docs/FRONTIER_BASELINE_2026.md, docs/RESEARCH_OPERATING_MODEL.md, and docs/RESEARCH_GAP_REGISTER.md |
| Gap | These documents are intentionally not part of Gate A `1.0.0`. Their addition changed the live repository inventory, so the historical report cannot validate them. |
| Closure evidence | The `1.1.0` successor adopts the documents through its own manifests, schemas, validation plan, acyclic evidence index, and deterministic report while preserving the historical packet unchanged. |

## Gate B research prerequisites

### RGA-006: No retained methodological frontier

| Field | Value |
|---|---|
| Priority | P1 |
| Classification | **GATE_B_RESEARCH_PREREQUISITE** |
| Status | Open |
| Current evidence | The historical `1.0.0` ledger recorded eight standards or guidance payloads. The public `1.1.0` profile retains four ISO Open Data metadata payloads as eligible and carries four NIST or UN sources as ineligible pointers. Neither profile retains an empirical benchmark dataset or independent scientific review. |
| Gap | The research frontier reviewed in [FRONTIER_BASELINE_2026.md](FRONTIER_BASELINE_2026.md) is URL-only and cannot support a protocol or claim. |
| Closure evidence | Retain permitted exact paper and dataset-description bytes, versions, dates, authors, publisher, access, license, digest, scope, comparator, and limitations in a successor ledger. Obtain independent methodological review. |

### RGA-007: Preregistration evidence and execution remain absent

| Field | Value |
|---|---|
| Priority | P1 |
| Classification | **GATE_B_RESEARCH_PREREQUISITE** |
| Status | Open |
| Current machine surface | [study-design-preregistration.schema.json](../schemas/v1.1/study-design-preregistration.schema.json) now types design family, observation boundary, causal graph, adjustment sets, negative controls, missingness, power, stopping, interim looks, multiplicity, splits, access chronology, deviations, and frozen analysis artifacts. |
| Gap | No authorized empirical preregistration, retained study inputs, independently reviewed numeric thresholds, sample-size justification, or execution record exists. Static completeness does not validate the proposed design choices. |
| Closure evidence | An independently reviewed, immutable empirical preregistration bound before data access, plus retained evidence for every design choice and an authorized execution gate. |

### RGA-008: Complementarity and joint silent miss lack retained empirical basis

| Field | Value |
|---|---|
| Priority | P1 |
| Classification | **GATE_B_RESEARCH_PREREQUISITE** |
| Status | Open |
| Current basis | [joint-performance-evaluation.schema.json](../schemas/v1.1/joint-performance-evaluation.schema.json) types common opportunities, per-actor performance, joint silent misses, dependence analysis, selective prediction, OOD, conformal, transfer, and worst-group evaluation. The human contract separately types disclosure and actor information sets. |
| Gap | No retained opportunity corpus, independently validated reference process, harmonized standalone and team comparator, human effort or adherence evidence, or empirical dependence model exists. |
| Frontier basis | [AAAI no-free-lunch paper](https://ojs.aaai.org/index.php/AAAI/article/view/33574), [NBER collaboration paper](https://www.nber.org/papers/w33949), and [PILOT-DSM](https://www.sciencedirect.com/science/article/pii/S0001457526002745), all **EXTERNAL_PRIMARY_UNRETAINED**. |
| Closure evidence | Retained opportunities and actor information, independently validated reference and membership processes, frozen standalone and team losses, preregistered dependence analysis, and replication. |

### RGA-009: Readiness lacks construct validation and empirical phase tests

| Field | Value |
|---|---|
| Priority | P1 |
| Classification | **GATE_B_RESEARCH_PREREQUISITE** |
| Status | Open |
| Current static surface | The human contract separates readiness dimensions, required capabilities, task, assessment window, estimates, decision rule, loss, recovery event history, competing events, censoring, and terminal state. |
| Gap | No retained measurement-validation evidence shows that gaze, workload, drowsiness, probes, subjective ratings, or takeover timing measure the proposed dimensions. Phase-specific empirical validity and discordance rules remain unestablished. |
| Frontier basis | [Situation-awareness measure comparison](https://www.sciencedirect.com/science/article/pii/S0001457525002283), [perceived-awareness and hazard-recognition mismatch](https://www.sciencedirect.com/science/article/pii/S0003687025000985), and [task-demand phase effects](https://www.sciencedirect.com/science/article/pii/S0141938225001544), all **EXTERNAL_PRIMARY_UNRETAINED**. |
| Closure evidence | Multi-method measurement model, convergent and discriminant validity, task and time-budget context, phase outcomes, discordance disposition, repeated-person dependence, and a falsifier where a proxy improves but recovery or hazard outcome does not. |

### RGA-010: Recoverability event process lacks empirical basis

| Field | Value |
|---|---|
| Priority | P1 |
| Classification | **GATE_B_RESEARCH_PREREQUISITE** |
| Status | Open |
| Current static surface | The human contract types an opportunity window, recovery criterion, event history, competing-event policy, censoring policy, probability, time to recovery, and terminal state. |
| Gap | No retained data or independent validation establishes a feasible window, recovery criterion, observation process, competing-event treatment, or transfer across drivers, vehicles, tasks, and ODDs. |
| Frontier basis | [Obstacle, alertness, and takeover-process study](https://www.sciencedirect.com/science/article/pii/S1369847825002566) and [TD2D dataset descriptor](https://www.nature.com/articles/s41597-025-04781-8), both **EXTERNAL_PRIMARY_UNRETAINED**. |
| Closure evidence | Retained event-process data, independently justified survival or multistate estimand, frozen censoring and competing-event policy, repeated-person analysis, observation-coverage audit, sensitivity analysis, and replication. |

### RGA-011: Sequential and off-policy evidence and execution are absent

| Field | Value |
|---|---|
| Priority | P1 |
| Classification | **GATE_B_RESEARCH_PREREQUISITE** |
| Status | Open |
| Current basis | [sequential-off-policy-evaluation.schema.json](../schemas/v1.1/sequential-off-policy-evaluation.schema.json) types trajectories, steps, behavior and target policies, propensities, information sets, reward and costs, horizon, support, effective sample size, weights, estimators, uncertainty, and safety constraints. |
| Gap | Gate A contains no eligible policy artifacts, logged trajectories, behavior-policy evidence, supported action data, estimator execution, or independently reviewed identification argument. All policy and encounter bindings remain explicitly unavailable. |
| Frontier basis | [ICLR safety-constrained policy evaluation](https://proceedings.iclr.cc/paper_files/paper/2025/hash/5681251fa039cf49d6d11b906eded1b3-Abstract-Conference.html), [ICML nonignorable missingness](https://openreview.net/forum?id=So6DMbeAak), [ICML history-dependent behavior policy](https://openreview.net/forum?id=BrLuZ0HOnb), and [NeurIPS OPE model selection](https://openreview.net/forum?id=gQ8kIhu8JA). Labels: **EXTERNAL_PRIMARY_UNRETAINED**. |
| Closure evidence | A separately authorized study with retained exact policies and logs, independently reviewed support and identification assumptions, frozen estimator selection, uncertainty and sensitivity analysis, and replication. |

### RGA-012: OOD and abstention guarantees lack eligible calibration evidence

| Field | Value |
|---|---|
| Priority | P1 |
| Classification | **GATE_B_RESEARCH_PREREQUISITE** |
| Status | Open |
| Current basis | The joint evaluation contract distinguishes missing, unmeasured, OOD, sensor-invalid and abstained outcomes and types selective risk, unconditional risk, coverage, calibration dataset, exchangeability, guarantee scope and conditional groups. |
| Gap | No eligible calibration release, frozen selector or detector artifact, retained exchangeability assessment, shift model, finite-sample execution, or independent group-conditional review exists. |
| Frontier basis | [Reject-option conformal paper](https://www.sciencedirect.com/science/article/pii/S2666827025000477), [generalized shift conformal paper](https://proceedings.mlr.press/v258/wang25l.html), and [group-conditional conformal paper](https://proceedings.mlr.press/v267/gao25c.html). Labels: **EXTERNAL_PRIMARY_UNRETAINED**. |
| Closure evidence | Retained calibration and target releases, frozen assumptions and reject causes, finite-sample coverage and error-reject results, shift invalidation, group-conditional review, and replication. |

### RGA-013: Transfer contract lacks retained source-to-target evidence

| Field | Value |
|---|---|
| Priority | P1 |
| Classification | **GATE_B_RESEARCH_PREREQUISITE** |
| Status | Open |
| Current static surface | The joint contract types source and target domains, ODD references, shift taxonomy, adaptation allowance, target-label access, access chronology, assumptions, source and target performance, transfer gap, overlap and uncertainty. |
| Gap | No retained source and target releases, measurement-invariance evidence, harmonization mapping, supported overlap analysis, frozen adaptation, or independently reviewed target evaluation exists. |
| Closure evidence | Retained versioned domains and releases, access chronology, frozen adaptation and tuning disclosure, supported overlap and conditional coverage, invalidation for absent support, target-only reporting, and independent replication. |

### RGA-014: Worst-group validation lacks membership and simultaneous-inference contracts

| Field | Value |
|---|---|
| Priority | P1 |
| Classification | **GATE_B_RESEARCH_PREREQUISITE** |
| Status | Open |
| Current strength | Gate A requires every preregistered group, explicit low-information disposition, coverage, uncertainty, and all direction-aware worst ties. |
| Gap | Group definitions are synthetic registry entries. No membership measurement model, membership uncertainty, effective sample size, group-conditional calibration, simultaneous interval method, subgroup model-selection boundary, or utility tradeoff metrics are typed. |
| Closure evidence | Retained group definitions, measurement validity, intersection policy, membership unknowns, simultaneous inference, multiplicity, minimum information, calibration, and complete result reporting. |

### RGA-015: Dataset and benchmark evidence remain absent

| Field | Value |
|---|---|
| Priority | P1 |
| Classification | **GATE_B_RESEARCH_PREREQUISITE** |
| Status | Open |
| Current boundary | Gate A prohibits private-data ingestion. [evaluation-assurance-bundle.schema.json](../schemas/v1.1/evaluation-assurance-bundle.schema.json) provides static dataset, source, partition, ethics, label-governance, test, comparator, metric, leakage, contamination, maintenance and benchmark interfaces with unavailable payload bindings. |
| Gap | No dataset payload, participant or consent record, sensor-synchronization evidence, annotation execution, adjudication result, split artifact, contamination analysis, benchmark run, maintenance history, or independent review exists. |
| Frontier basis | [TD2D descriptor](https://www.nature.com/articles/s41597-025-04781-8), official [Croissant RAI](https://docs.mlcommons.org/croissant/docs/croissant-rai-spec.html), [BenchRisk](https://proceedings.neurips.cc/paper_files/paper/2025/hash/92a0af72659802465884eaad8443ea89-Abstract-Datasets_and_Benchmarks_Track.html), and [benchmark-contamination study](https://proceedings.mlr.press/v267/sun25t.html). Mixed labels: **EXTERNAL_PRIMARY_UNRETAINED**, **EXTERNAL_OFFICIAL_UNRETAINED**, and bounded **REIYAH_INFERENCE**. |
| Closure evidence | Authorized and retained dataset releases, participant and rights governance, immutable splits, executed contamination and leakage review, benchmark runs, correction and maintenance history, and independent audit. |

### RGA-016: Scenario, ODD, and safety-case evidence remain absent

| Field | Value |
|---|---|
| Priority | P2 |
| Classification | **GATE_B_RESEARCH_PREREQUISITE** |
| Status | Open |
| Current strength | The evaluation-assurance contract now types ODD dimensions and bounds, scenarios and timelines, test cases and oracles, hazards, claims, arguments, defeaters, assumptions, evidence references and residual risk. It explicitly authorizes no safety claim. |
| Gap | No retained scenario corpus, executed test, validated oracle, accepted hazard analysis, evidence-backed safety argument, exact standards review, change-impact result, or independent safety authority exists. |
| Frontier basis | Official [ISO 34505:2025](https://www.iso.org/standard/78954.html), official [ASAM OpenODD 1.0.0](https://publications.pages.asam.net/standards/ASAM_OpenODD/ASAM_OpenODD/latest/specification/index.html), and the 2026 [credible safety-case paper](https://www.sciencedirect.com/science/article/pii/S0022437525001641). |
| Closure evidence | Static interface schemas, exact retained standards evidence, independent safety review, and a separately authorized safety gate. This gap must not be closed by calling Gate A a safety case. |

### RGA-017: Scientific falsifiers need frontier-specific failure conditions

| Field | Value |
|---|---|
| Priority | P1 |
| Classification | **GATE_B_RESEARCH_PREREQUISITE** |
| Status | Open |
| Current strength | [CLAIMS_AND_NON_CLAIMS.md](CLAIMS_AND_NON_CLAIMS.md) keeps all scientific claims proposed and states that generic terms must become executable contradiction boundaries before preregistration. |
| Gap | Current falsifiers do not yet require failure when a team underperforms the best standalone actor, a readiness proxy diverges from hazard or recovery outcome, object-set coverage fails, OPE support or effective sample size is inadequate, estimators disagree materially, group-conditional coverage fails, target-shift assumptions fail, or benchmark contamination is unresolved. |
| Closure evidence | Numeric or executable boundaries, retained evidence, immutable preregistration, and fixtures for every claim-specific invalidation route. |

### RGA-018: Tesla and Mobileye comparisons lack eligible comparator records

| Field | Value |
|---|---|
| Priority | P1 |
| Classification | **GATE_B_RESEARCH_PREREQUISITE** |
| Status | Open |
| Tesla basis | [Tesla FSD (Supervised) Safety Report](https://www.tesla.com/fsd/safety) and [Tesla FSD support page](https://www.tesla.com/support/fsd), both **COMPANY_SELF_REPORT_UNRETAINED**. |
| Mobileye basis | [Mobileye DMS](https://www.mobileye.com/blog/presenting-the-mobileye-driver-monitoring-system-fusing-road-safety-inside-the-cabin/), [Mobileye RSS](https://www.mobileye.com/technology/responsibility-sensitive-safety/), and [Mobileye product-team perspectives](https://www.mobileye.com/blog/tackling-global-regulations-and-safety-standards/), all **COMPANY_SELF_REPORT_UNRETAINED**. |
| Gap | No retained exact product, software, hardware, supervision, ODD, region, telemetry, outcome, opportunity, driver, or comparator releases. Tesla's reviewed report page names no scientific analysis team. Mobileye's named Sensing Product team page expressly limits its statements to personal perspectives. |
| Closure evidence | Retained company bytes and manuals; exact product and evidence identities; authority limitations; harmonized opportunity and outcome definitions; eligible independent data; and a preregistered comparison that preserves every vendor-specific boundary. Company claims alone remain ineligible. |

## Public release prerequisites

### RGA-019: Source custody and redistribution state were conflated

| Field | Value |
|---|---|
| Priority | P0 |
| Classification | **PUBLIC_RELEASE_PREREQUISITE** |
| Status | Closed for the exact Gate A `1.1.0` public profile; no legal conclusion created |
| Current machine surface | [public-evidence-custody-profile-1.1.0.json](../evidence/public-evidence-custody-profile-1.1.0.json), [public-distribution-inventory-1.1.0.json](../evidence/public-distribution-inventory-1.1.0.json), and the `1.1.0` source ledger separate custody, redistribution, profile eligibility, payload, upstream identity, rights basis, and omission reason. |
| UN disposition | Both UN PDFs are absent from the public worktree, preserved only in private quarantine with previously observed identity metadata, and represented publicly as evidence-ineligible pointers. No redistribution basis is inferred. |
| NIST disposition | Both the mutable publication-page HTML and NIST AI 100-1 PDF are absent from the public worktree and represented as evidence-ineligible pointers because document-specific third-party-material review remains unresolved. |
| Failure consequence | Without the public-profile closure, distribution could expose apparently restricted UN bytes, include scanner-triggering web content, or omit bytes while falsely preserving retained-evidence status. |
| Closure evidence | Distribution-aware schemas, successor ledger and crosswalk, exact public inventory, external quarantine recovery record, current rights-page observation, four ODC-By payloads with attribution, excluded-path enforcement, and explicit operator authorization for static public repository distribution. |

#### Required evidence-state design

The internal Gate A 1.0.0 release remains immutable. The `1.1.0` successor separates these
orthogonal fields:

- custody state: retained in internal profile, retained in public profile, external pointer only,
  unavailable, or quarantined;
- redistribution state: permitted, prohibited, permission required, restricted, or unmeasured;
- evidence eligibility for the exact profile: eligible only when the required bytes are present
  and verified;
- upstream identity: exact publisher, document symbol, version, date, locator, observed digest,
  byte size, media type, and retrieval time;
- profile payload: exact included path and digest, or null with an omission reason;
- derivation state: official source bytes, exact mirror, derived metadata, extraction, or
  transcription; and
- rights basis: exact reviewed source, date, reviewer, jurisdictional limitation, and unresolved
  questions.

An observed digest for omitted bytes is identity metadata. It is not a retained-source digest in
the public profile.

#### Clean public-profile treatment

1. Omit the two UN PDF payloads unless written permission or another applicable distribution
   basis is retained and reviewed.
2. Keep canonical UN document symbols, official locators, previously observed digest and size,
   retrieval date, and omission reason in pointer records.
3. Mark those records ineligible as retained evidence for the public profile.
4. Downgrade every public crosswalk mapping whose positive basis depends on the omitted UN bytes
   to an explicit evidence gap. The public validator must not fetch them.
5. Provide an informative acquisition recipe and expected digest only for a separate locally
   augmented profile. User-acquired bytes may become locally verifiable, but they do not make the
   base public packet evidence-complete.
6. Do not sanitize the NIST HTML in place. Sanitized bytes would be a derived artifact with a new
   digest and would no longer be the official retained snapshot.
7. Quarantine or omit the raw HTML from the public profile. Where publication-specific rights
   review permits, use the clean NIST AI 100-1 Technical Series PDF as the retained public
   evidence and make it the identity source in a successor crosswalk.
8. If publication-page fields are needed, create a derived metadata record with complete
   provenance and label it derived. Do not call it official catalog metadata.
9. Create new source-schema, source-ledger, standards-crosswalk, distribution-manifest,
   evidence-index, and validation-report releases as applicable. Preserve predecessor relations
   and never reuse a release ID.
10. Bind any later operator decision to one exact distribution profile. Internal, public,
    restricted, and locally augmented profiles must never be treated as interchangeable.

Static repository distribution is authorized only for the exact public inventory. Empirical or
scientific publication remains outside Gate A authority.

### RGA-020: Public release required an immutable transport identity

| Field | Value |
|---|---|
| Priority | P0 |
| Classification | **PUBLIC_RELEASE_PREREQUISITE** |
| Status | Closed for frozen Gate A `1.1.0` by append-only receipt sequence 1; successor transport state is receipt-controlled |
| Historical state | At the initial read-only inspection, the repository had a configured origin but no HEAD commit, and all files were untracked. That observation is historical and does not describe the frozen public release. |
| Frozen `1.1.0` state | The indexed packet is commit `aa5f9b9b455219536183630b0be1e801a18a575e`; the evidence-index digest is `sha256:91149ec8bfc9a3999ce95d8c18ce0d558cf974b0afb412a7ac11027c63056c7a`; and commit `68854b474f7c4ebd95cc79ced56411c2d5935f78` adds only the append-only public distribution receipt. |
| Closure evidence | Receipt `reiyah.public-distribution-receipt.initial-publication`, sequence 1, binds the exact packet commit, index, inventory, rights observation, payloads, attribution, public remote, `main` ref, and verified readback. Its digest is `sha256:d805ad1bab46e087338fb3c7ac049f9c1e9edbbd782fa6960db1f8e3eca57139`. It creates no scientific or operator authority. |
| `1.1.1` boundary | The indexed governance correction cannot contain its own later commit or remote readback. A valid successor receipt is the sole transport authority for its exact index; absence of that receipt means transport is unverified. Frozen `1.1.0` identities cannot serve as placeholders. |

## Residual unknowns

### RGA-021: External frontier sources are not retained

All research, Tesla, Mobileye, ISO 34505, ASAM OpenODD, Croissant, UN terms, NIST reuse, and
safety-case links in the three 2026 audit documents are unretained. Their exact current bytes,
license states, later revisions, corrections, and availability remain **UNKNOWN** to the Gate A
evidence system.

### RGA-022: Empirical feasibility is unknown

No eligible dataset, sample-size analysis, measurement-validation study, policy log, subgroup
coverage assessment, independent replication, or safety review exists in Reiyah. Whether HARBOR's
proposed constructs can be measured reliably and usefully is **UNKNOWN**.

### RGA-023: Full threat completeness is unknowable

The current validator has deterministic coverage for declared rules, but no finite schema
or fixture set proves that every scientific, security, rights, or release threat is known.

## Non-blockers to preserve

| ID | Finding | Evidence |
|---|---|---|
| RGA-NB-001 | The named project, working directory, Git root, and loaded repository instructions all identify Reiyah. | AGENTS.md and read-only Git-root inspection. |
| RGA-NB-002 | Gate A clearly separates architecture completeness from operator acceptance. GA-17 remains external and not evaluated. | [PRE_IMPLEMENTATION_GATE.md](PRE_IMPLEMENTATION_GATE.md) and the retained validation report. |
| RGA-NB-003 | No product runtime, live inference, model training, deployment, physical control, private-data ingestion, or publication machinery is authorized. | [SESSION_HANDOFF.md](SESSION_HANDOFF.md) and [PRE_IMPLEMENTATION_GATE.md](PRE_IMPLEMENTATION_GATE.md). |
| RGA-NB-004 | Missing, unmeasured, OOD, sensor-invalid, and abstained states are distinct and protected against coercion. | Scientific schemas, mathematical specification, and reason-specific fixtures. |
| RGA-NB-005 | Observation, latent belief, decision, intervention, outcome, and evidence remain separate object kinds. | Scientific charter, schemas, object-chain fixtures, and semantic validation. |
| RGA-NB-006 | Mission and protocol releases are append-only, digest-bound, and operator-unaccepted. | Manifest releases, release ledger, evidence index, and report. |
| RGA-NB-007 | The pre-audit frozen packet produced a deterministic full-validation pass with 25 schemas, 122 normative instances, 91 fixtures, eight retained sources, 164 indexed artifacts, zero diagnostics, GA-01 through GA-16 passed, and GA-17 not evaluated. | [gate-a-validation-1.0.0.json](../gate/validation-reports/gate-a-validation-1.0.0.json). This is a historical integrity result for its exact index, not a scientific result. |
| RGA-NB-008 | All scientific claims, the HARBOR expansion, and the construct definitions remain proposed, with no accepted scientific claim. | [CLAIMS_AND_NON_CLAIMS.md](CLAIMS_AND_NON_CLAIMS.md), protocol manifest, and handoff. |
| RGA-NB-009 | Company pages and exact team names are explicitly limited to attribution and comparator discovery in the 2026 audit documents. | [FRONTIER_BASELINE_2026.md](FRONTIER_BASELINE_2026.md) and [RESEARCH_OPERATING_MODEL.md](RESEARCH_OPERATING_MODEL.md). |
| RGA-NB-010 | URL-only pointers remain ineligible as retained evidence. | [SOURCE_POLICY.md](SOURCE_POLICY.md). |

## Recommended decision posture

The Gate A `1.1.0` successor closes RGA-001 through RGA-003 for static architecture only. That
closure means the declared contracts are machine-representable and adversarially checked. It
does not establish construct validity, empirical feasibility, scientific support, safety,
compliance, or operator acceptance.

RGA-006 through RGA-018 are candidate prerequisites for later scientific work. They do not
authorize or define Gate B.

RGA-019 is closed for the exact public `1.1.0` evidence profile. RGA-020 is closed for the frozen
`1.1.0` transport by append-only receipt sequence 1. Gate A `1.1.1` is a governance correction
with the `1.1.0` mission, protocol, and evidence profile unchanged. Its sidecar and canonical
report identify the exact review target; only a valid event-specific successor receipt can
establish its later packet commit and remote readback. Neither receipt sequence 1 nor a successor
receipt can alter GA-17 or turn omitted or URL-only source bytes into retained evidence.
