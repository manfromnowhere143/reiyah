# HARBOR Methodological Frontier Baseline, 2026

## Status and authority

| Field | Value |
|---|---|
| As-of date | 2026-08-23 |
| Lifecycle status | Proposed |
| Scope | External methodological review for the HARBOR research program |
| Gate status | Gate A 1.1 architecture candidate; operator unaccepted |
| Runtime authorization | False |
| Scientific support created | False |
| Operator acceptance created | False |

This document records the research baseline proposed for the Gate A 1.1 architecture candidate.
It does not mutate the historical 1.0 packet, authorize Gate B, validate a product, create a
safety case, or support a performance claim. Its external links are discovery pointers. No
linked paper, standard, company page, dataset, or certificate has been made evidence-eligible by
this document. Under
[SOURCE_POLICY.md](SOURCE_POLICY.md), a URL without retained bytes is not retained evidence.

## Evidence labels

Every external statement below uses one of these labels.

| Label | Meaning | Permitted use |
|---|---|---|
| **GATE_A_RETAINED** | Exact bytes and metadata are already recorded in the Gate A source ledger. | Describe the bounded content and its recorded limitations. |
| **EXTERNAL_PRIMARY_UNRETAINED** | A primary research paper or primary dataset paper was reviewed at its publisher or conference page, but its bytes are not retained by Reiyah. | Identify a candidate method, falsifier, or research requirement. |
| **EXTERNAL_OFFICIAL_UNRETAINED** | An official standards or public-project page was reviewed, but its bytes are not retained by Reiyah. | Identify a candidate governance or assurance requirement without claiming compliance. |
| **COMPANY_SELF_REPORT_UNRETAINED** | A company-authored page describes its own product, data, method, or assessment. | Define a comparator or open question, never independent evidence of effectiveness or safety. |
| **REIYAH_INFERENCE** | A proposed implication drawn from one or more labeled sources. | Shape a future static contract after independent review. |
| **UNKNOWN** | The reviewed material does not establish the fact. | Preserve the gap without filling it by assumption. |

Passing Gate A validation, a company name, a research-team name, an author list, a standards
body, a certificate summary, or consensus does not change these labels.

## Program and team-name limits

HARBOR remains the proposed expansion Human-Automation Readiness, Belief & Operational Risk.
The name identifies a candidate research program only. It does not establish a research team,
expertise, independence, authorship, scientific validity, or operator authority.

The same rule applies to external names:

- The current [Tesla Full Self-Driving (Supervised) Vehicle Safety Report](https://www.tesla.com/fsd/safety)
  is labeled **COMPANY_SELF_REPORT_UNRETAINED**. The reviewed page identifies Tesla as the
  publisher but does not identify a scientific analysis team, protocol authors, independent
  review team, or replication team. Those identities are **UNKNOWN**.
- Mobileye's page titled
  [Tackling global regulations and safety standards](https://www.mobileye.com/blog/tackling-global-regulations-and-safety-standards/)
  names the exact group as Mobileye's Sensing Product team and names Nir Hamzani and Shai
  Hershkovich. The page expressly says their perspectives are personal and do not represent
  Mobileye's official position. The team name therefore supports attribution only. It does not
  support a company conclusion, regulatory interpretation, compliance finding, or scientific
  claim. Label: **COMPANY_SELF_REPORT_UNRETAINED**.
- Mobileye's product and safety-method pages are company proposals unless exact independent
  assessment artifacts are retained and reviewed. Label:
  **COMPANY_SELF_REPORT_UNRETAINED**. A Mobileye page reporting a 2026 TÜV SÜD
  recommendation is not the underlying certificate, audit scope, findings, exclusions, or
  continuing-validity record. Those underlying facts remain **UNKNOWN** in Reiyah.
- An author list on a primary paper establishes attribution to that paper. It does not establish
  independent replication, freedom from conflicts, or authority over Reiyah.

Future evidence records must preserve the exact name used by the source, the named person's
role, the publisher, the statement's scope, and whether the source itself limits the speaker's
authority. Reiyah must not normalize a product group, corporate blog, academic lab, standards
committee, or vendor into an undifferentiated expert team.

## Modern methods baseline

The baseline below is a candidate research minimum. Each proposed requirement is a
**REIYAH_INFERENCE** until independently reviewed, retained, versioned, and adopted in a
successor protocol.

### 1. Object-level human and automation belief

The current scientific charter defines belief as uncertainty over an identified object or
relation, not as latent truth. The frontier review motivates two further requirements.

First, collaboration quality cannot be inferred from marginal calibration. The AAAI 2025 paper
[A No Free Lunch Theorem for Human-AI Collaboration](https://ojs.aaai.org/index.php/AAAI/article/view/33574)
shows that calibrated probabilistic agents do not make nontrivial deterministic collaboration
uniformly beneficial. Label: **EXTERNAL_PRIMARY_UNRETAINED**.

Second, the information shown to a person can alter belief and effort. The 2025 NBER paper
[Designing Human-AI Collaboration: A Sufficient-Statistic Approach](https://www.nber.org/papers/w33949)
allows biased human beliefs and effort crowd-out, and reports under-response to AI predictions
and reduced effort under confident AI information. Label: **EXTERNAL_PRIMARY_UNRETAINED**.

The proposed HARBOR static contract therefore needs:

- a belief holder and actor role, such as human, automation, reference process, or explicitly
  defined joint procedure;
- the target object, relation, latent state, horizon, and state-space version;
- the exact conditioning information set and the availability time of every member;
- the display and disclosure policy, including information withheld from each actor;
- the elicitation or inference method, calibration target, reference process, and applicability
  domain;
- human-only, automation-only, team, fallback, and oracle or complementarity-potential
  comparators; and
- proper-scoring, calibration, coverage, abstention, and decision-loss outcomes.

### 2. Readiness and recoverability as validated constructs

HARBOR therefore proposes that driver-state proxies must not be treated as interchangeable with
situation awareness, readiness, hazard recognition, or successful recovery. Label:
**REIYAH_INFERENCE**.

The 2025 primary study
[How to assess situation awareness while driving with automation?](https://www.sciencedirect.com/science/article/pii/S0001457525002283)
compares subjective, gaze, performance, and probe measures and finds context-dependent
relationships. The 2025 study
[The mismatch between perceived situation awareness and hazard recognition in automated driving](https://www.sciencedirect.com/science/article/pii/S0003687025000985)
reports higher perceived situation awareness alongside slower hazard recognition under
automation. Labels: **EXTERNAL_PRIMARY_UNRETAINED**.

The 2025 study
[How task demands influence driver behaviour in conditionally automated driving](https://www.sciencedirect.com/science/article/pii/S0141938225001544)
reports that time budget, non-driving tasks, lane context, and scenario complexity affect
different takeover phases. The 2025 study
[How do obstacle characteristics and driver alertness affect the takeover process?](https://www.sciencedirect.com/science/article/pii/S1369847825002566)
separates situation-understanding time from takeover-reaction time and models perceived risk as
a mediator. Labels: **EXTERNAL_PRIMARY_UNRETAINED**.

The proposed minimum is a phase-resolved construct:

1. relevant-object perception;
2. comprehension of object and automation state;
3. projection of near-term hazard evolution;
4. decision formation;
5. motor initiation;
6. control stabilization or declared safe recovery; and
7. failure, censoring, competing event, or epistemic invalidity.

Each phase needs a declared measurement model, method-specific validity, repeated-person or
vehicle dependence, time budget, scenario context, and a rule for discordant subjective,
behavioral, physiological, gaze, probe, and outcome measures. Gaze or workload alone must not
serve as readiness ground truth.

A fresh 2026 review reinforces two boundaries. The Human Factors study
[With a Little Help From My Car](https://journals.sagepub.com/doi/10.1177/00187208261422917)
reports that the content and presentation of shared vehicle situation awareness changed
driver-initiated disengagement behavior in a simulator. Perception highlighting, confidence,
and projection were not interchangeable. The Transportation Research Part F study
[Will drivers cognitively disengage from previous tasks following scheduled takeovers?](https://doi.org/10.1016/j.trf.2026.103641)
models attention residue after a scheduled takeover and reports dependence on situational
motivation, mind-wandering tendency, and driving demand. Labels:
**EXTERNAL_PRIMARY_UNRETAINED**.

These studies do not validate a HARBOR construct. They strengthen the proposed requirement that
information disclosure is an intervention with its own version, timing, modality, and audience,
and that recovery cannot be reduced to first control input. The observation window must continue
through declared stabilization, failure, censoring, or a competing event.

### 3. Object-set coverage and joint silent misses

The 2026 primary paper
[PILOT-DSM: Risk perception-aligned takeover prompting framework via coverage-gap assessment](https://www.sciencedirect.com/science/article/pii/S0001457526002745)
frames the problem as whether a driver covered the set of risk-relevant objects, rather than only
the single highest-risk object. It compares a driver's scan path with expert strategies and
withholds prompts when no coverage gap is detected. Label: **EXTERNAL_PRIMARY_UNRETAINED**.

Mobileye's 2025
[Driver Monitoring System product page](https://www.mobileye.com/blog/presenting-the-mobileye-driver-monitoring-system-fusing-road-safety-inside-the-cabin/)
describes fusing driver gaze with external scene information to identify unattended critical
objects and condition takeover requests. This is a useful industry comparator, not independent
validation. Label: **COMPANY_SELF_REPORT_UNRETAINED**.

The proposed HARBOR joint-silent-miss record needs a versioned relevant-object set, independent
reference process, per-channel opportunity, per-channel validity, detection and response
criteria, indication modality, display availability, fallback behavior, temporal windows,
object correspondence, and a dependence model. Human and automation marginals are insufficient.
The primary falsifier is a valid joint method that performs no better than, or worse than, the
best eligible standalone actor after equal opportunity and information accounting.

### 4. Causal and sequential policy evaluation

The current Gate A potential-outcome contrast defines a static average policy effect. It does not
by itself specify repeated interventions or adaptive policies.

The ICLR 2025 paper
[Efficient Policy Evaluation with Safety Constraint for Reinforcement Learning](https://proceedings.iclr.cc/paper_files/paper/2025/hash/5681251fa039cf49d6d11b906eded1b3-Abstract-Conference.html)
uses logged state, action, reward, cost, and next-state tuples and addresses behavior-policy
design, variance, and safety constraints. The ICML 2025 paper
[Off-Policy Evaluation under Nonignorable Missing Data](https://openreview.net/forum?id=So6DMbeAak)
shows that nonignorable missingness can bias policy-value estimates and proposes explicit
missingness assumptions and inference. Labels: **EXTERNAL_PRIMARY_UNRETAINED**.

The ICML 2025 paper
[Demystifying the Paradox of Importance Sampling with an Estimated History-Dependent Behavior Policy](https://openreview.net/forum?id=BrLuZ0HOnb)
shows that behavior-policy history changes finite-sample bias and asymptotic variance. The
NeurIPS 2025 paper
[Model Selection for Off-policy Evaluation](https://openreview.net/forum?id=gQ8kIhu8JA)
shows that off-policy estimators have their own model-selection and hyperparameter problem.
Labels: **EXTERNAL_PRIMARY_UNRETAINED**.

A future static OPE contract needs trajectory and time-step identity, state and observation
history, behavior and target policy versions, action propensities and provenance, reward and
safety-cost definitions, horizon and discounting, terminal and censoring rules, support and
positivity diagnostics, effective sample size, weight-tail and truncation rules, estimator
candidates, estimator-selection data boundaries, uncertainty, estimator disagreement, missingness
mechanism, confounding sensitivity, and safety-constraint estimands. This requirement does not
authorize policy learning, online exploration, data collection, or runtime execution.

### 5. Explicit unknown, OOD, and abstention

The 2025 paper
[Classification with reject option: Distribution-free error guarantees via conformal prediction](https://www.sciencedirect.com/science/article/pii/S2666827025000477)
distinguishes novelty rejection from ambiguity rejection and uses error-reject curves. Its
guarantee depends on calibration data representing the evaluated distribution. Label:
**EXTERNAL_PRIMARY_UNRETAINED**.

The AISTATS 2025 paper
[Conformal Prediction Under Generalized Covariate Shift with Posterior Drift](https://proceedings.mlr.press/v258/wang25l.html)
requires an explicit source-to-target shift model and weighting for target-domain coverage. The
ICML 2025 paper
[Bridging Fairness and Efficiency in Conformal Inference](https://proceedings.mlr.press/v267/gao25c.html)
addresses undercoverage in underrepresented groups and the width-versus-coverage tradeoff.
Labels: **EXTERNAL_PRIMARY_UNRETAINED**.

The proposed HARBOR contract must separately record novelty rejection, ambiguity rejection,
sensor invalidity, missingness, unmeasured state, and protocol abstention. It must bind calibration
set identity, exchangeability or shift assumptions, guarantee type, target and group-conditional
coverage, accepted and rejected denominators, risk-coverage and error-reject curves, and a
guarantee-validity disposition under shift.

### 6. Transfer and worst-group validation

Transfer requires source and target release identity, shift taxonomy, adaptation allowance,
target-data access chronology, target tuning, support overlap, and measurement invariance.
Worst-group evaluation requires a frozen group universe, membership measurement validity,
intersection construction, effective sample size, simultaneous or multiplicity-aware intervals,
group-conditional calibration, and explicit low-information groups.

Aggregate target performance, a pooled calibration result, or a single worst point estimate is
not enough. This requirement is supported by the shift and group-conditional conformal papers
above. Label: **REIYAH_INFERENCE**.

### 7. Dataset and benchmark governance

The 2025 primary data descriptor
[A Dataset on Takeover during Distracted L2 Automated Driving](https://www.nature.com/articles/s41597-025-04781-8)
documents 50 participants, 500 scenarios, multiple sensor modalities, synchronization,
experimental conditions, ethics review, consent, missing sensor data, subject-level validation,
and limitations. It is a useful example of the metadata HARBOR would need, not an eligible
HARBOR dataset. Label: **EXTERNAL_PRIMARY_UNRETAINED**.

The official [Croissant RAI 1.0 specification](https://docs.mlcommons.org/croissant/docs/croissant-rai-spec.html)
and [Croissant 1.1 specification](https://docs.mlcommons.org/croissant/docs/croissant-spec-1.1.html)
provide versioned machine-readable concepts for dataset resources, structure, provenance,
collection, annotation, sensitive information, use limitations, maintenance, and derived
lineage. Label: **EXTERNAL_OFFICIAL_UNRETAINED**.

The NeurIPS 2025 paper
[Risk Management for Mitigating Benchmark Failure Modes: BenchRisk](https://proceedings.neurips.cc/paper_files/paper/2025/hash/92a0af72659802465884eaad8443ea89-Abstract-Datasets_and_Benchmarks_Track.html)
organizes benchmark risk around comprehensiveness, intelligibility, consistency, correctness,
and longevity. The ICML 2025 paper
[The Emperor's New Clothes in Benchmarking?](https://proceedings.mlr.press/v267/sun25t.html)
shows why aggregate accuracy alone can obscure item-level fidelity and contamination resistance.
These studies concern language-model benchmarks, so transfer to HARBOR is a bounded governance
inference, not direct automotive evidence. Labels: **EXTERNAL_PRIMARY_UNRETAINED** and
**REIYAH_INFERENCE**.

A future dataset and benchmark release needs exact file digests, license and access states,
collection and sensor versions, consent and ethics scope, participant and scenario dependence,
annotation and adjudication, reference-process independence, split unit, preprocessing freeze,
duplicate and leakage controls, contamination assessment, intended use, prohibited use,
maintenance, corrections, deprecation, and sunset policy.

### 8. Scenario, ODD, and safety-case interfaces

The official [ISO 34505:2025 page](https://www.iso.org/standard/78954.html) says test cases
include identifiers, objectives, inputs, steps, platforms, expected results, scenario evaluation,
and coverage over requirements, operational domain, and test criteria. The official
[ASAM OpenODD 1.0.0 specification](https://publications.pages.asam.net/standards/ASAM_OpenODD/ASAM_OpenODD/latest/specification/index.html)
provides a machine-readable operational-domain baseline. Labels:
**EXTERNAL_OFFICIAL_UNRETAINED**.

The 2026 primary paper
[Building a credible case for safety: Approach proposal for Automated Driving Systems](https://www.sciencedirect.com/science/article/pii/S0022437525001641)
proposes layered architectural, behavioral, and in-service arguments, acceptance criteria, and
credibility assessment. Label: **EXTERNAL_PRIMARY_UNRETAINED**.

HARBOR should expose static interfaces for ODD, scenario, test-case, hazard, claim, argument,
evidence, assumption, defeater, validity, and change impact before any safety claim is possible.
Gate A is correctly not a safety case. These interfaces are future prerequisites only and do not
authorize simulation, road testing, control, deployment, or certification.

## Tesla and Mobileye as bounded comparators

### 2026 engineering frontier snapshot

The two programs' official materials describe different technical emphases. The comparison below
records what those materials say they are trying to solve. Every row is
**COMPANY_SELF_REPORT_UNRETAINED** and is represented only as pointer metadata in
[`frontier-discovery-register-1.1.0.json`](../evidence/frontier-discovery-register-1.1.0.json).

| Program | Company-stated 2026 focus | HARBOR research challenge |
|---|---|---|
| Tesla autonomy | Tesla's [Q1 2026 update](https://ir.tesla.com/_flysystem/s3/sec/000162828026026551/tsla-20260422-gen.pdf) describes FSD v14.3 work on reinforcement learning for long-tail cases, a revised vision encoder for low-visibility perception, a rewritten compiler, lower inference latency, and a path toward unsupervised use. Its [Q2 2026 update](https://assets-ir.tesla.com/tesla-contents/IR/TSLA-Q2-2026-Update.pdf) reports continued FSD and Robotaxi development and Cybercab production. | Test exact model, hardware, supervision, service area, software-update, support, and telemetry versions. Evaluate object opportunities, human and automation information sets, interventions, joint silent misses, recovery, shift, and worst groups instead of accepting fleet miles or aggregate collision ratios as sufficient. |
| Mobileye autonomy | Mobileye's [CES 2026 account](https://www.mobileye.com/blog/takeaways-from-the-mobileye-press-conference-with-ceo-prof-amnon-shashua-at-ces-2026/) describes a spectrum from Surround ADAS and L2++ through consumer L3/L4 and robotaxis, with EyeQ, REM, RSS, multimodal perception, world modeling, planning, and reduced teleoperation. Its [Q2 2026 update](https://ir.mobileye.com/news-releases/news-release-details/mobileye-releases-second-quarter-2026-results-updates-guidance) describes preparation for MOIA public testing, vertically integrated robotaxi operations, and high-volume ADAS programs. | Test whether modular claims remain valid across sensor, map, policy, driver-monitoring, ODD, fleet-operation, and organizational boundaries. Preserve dependence between channels, teleoperation and fallback exposure, domain exits, actor information, and exact comparator releases. |
| Mobileye long-tail development | The company-authored [Driving the long tail](https://www.mobileye.com/opinion/driving-the-long-tail/) account proposes separating failure discovery from failure resolution, using semantic failure classes, retrieval or generation of variations, and reproducibility testing. | Require independent reference processes, frozen failure taxonomies, provenance for generated variants, deduplication, selection-bias accounting, held-out reproduction, and evidence that a concentrated training signal generalizes beyond the discovered cluster. |
| Mobileye semantic failure discovery | Mobileye's [May 2026 Meteor account](https://www.mobileye.com/blog/diagnosing-the-long-tail-how-mobileye-turns-edge-cases-into-targeted-training/) describes multi-agent analysis over driving video using vision-language embeddings, automated reasoning, semantic search, targeted training, and reproducibility checks. | Measure retrieval recall against independently adjudicated failures, preserve the query and taxonomy freeze, separate discovery data from resolution and evaluation data, audit generated variants, and test whether apparent cluster repair transfers to untouched environments and worst groups. |
| Mobileye cabin-road fusion | Mobileye's [March 2026 DMS announcement](https://www.mobileye.com/news/mobileye-secures-major-dms-production-program-with-leading-us-automaker/) says DMS and occupant monitoring can run with ADAS perception on an EyeQ6 platform and relate driver state to road context. | Distinguish gaze, attention, belief, readiness, decision, and successful recovery. Test object-level coverage and discordance instead of treating a cabin signal as readiness ground truth. |
| Mobileye integrated L2+ | Mobileye's [August 2026 hands-off account](https://www.mobileye.com/blog/hands-off-driving-goes-mainstream-enabling-l2-at-scale/) describes EyeQ6H, REM localization, external and cabin sensing, parking transitions, driver monitoring, and feedback across ADAS and higher-automation programs. | Preserve the exact integration boundary. Test whether map, perception, policy, display, driver-monitoring, and fallback failures are dependent, and report coverage by ODD, hardware, software, supervision mode, geography, and group. |

The objective is not to imitate either stack or to assert comparative advantage. HARBOR asks a
distinct research question: can a versioned human-automation system support independently
falsifiable analysis of object-level belief, causal policy value, recoverability, joint misses,
transfer, and complete worst-group behavior? No current Reiyah artifact answers that question
empirically or supports a superiority claim.

### Tesla

Tesla's official pages state that FSD (Supervised) requires active driver supervision and does
not make the vehicle autonomous. Tesla separately describes Robotaxi as a driverless service in
limited service areas with passenger pull-over and support controls. These are distinct
operational modes and must not share a denominator without an exact mode and service-boundary
mapping. The current Vehicle Safety Report attributes a collision to FSD when it was active
within five seconds before the event, compares telemetry-defined collision rates across control
categories, and describes shift-to-park mileage packets and collision-event packets. Labels:
**COMPANY_SELF_REPORT_UNRETAINED**.

HARBOR may use this only to define research questions about:

- exact software, hardware, region, road-class, and control-state versions;
- engagement, disengagement, takeover request, intervention, and post-disengagement windows;
- exposure miles versus relevant object or hazard opportunities;
- telemetry capture failure, selection, missingness, and vehicle-level clustering;
- comparator eligibility and confounding by road, vehicle, driver, weather, and feature
  availability; and
- collision, injury, severity, near-miss, and silent-miss outcomes.

The reviewed Tesla pages do not give Reiyah item-level data, a frozen independent protocol,
driver-belief records, an eligible causal design, subgroup completeness, or independent
replication. Safety and causal benefit therefore remain **UNKNOWN** to Reiyah.

### Mobileye

Mobileye's product pages distinguish hands-off eyes-on, hands-off eyes-off, and driverless
functions within product, manual, ODD, and legal limits. Its 2026 disclosures discuss Surround
ADAS, SuperVision, Chauffeur, Drive, cabin-road fusion, REM map intelligence, RSS policy,
long-tail scenario discovery, and robotaxi operations. Its DMS page describes linking cabin gaze
with external objects and adapting takeover requests. Its RSS page describes a company-proposed
formal safety model. Labels: **COMPANY_SELF_REPORT_UNRETAINED**. Treating these materials as one
comparator surface is a **REIYAH_INFERENCE**, not a company or empirical conclusion.

HARBOR may use these pages to define versioned comparators for object coverage, driver and
automation information sets, alert and fallback policies, ODD boundaries, and formal safety-rule
claims. The pages do not establish construct validity, detection accuracy, effectiveness,
comparability to Tesla, compliance, or safety. Those conclusions remain **UNKNOWN**.

Tesla and Mobileye must never be pooled into a vendor category without preserving product,
software, hardware, supervision, ODD, geography, data-generation, comparator, and evidence
differences.

## Retention and review boundary

Before any item in this baseline influences a preregistered protocol:

1. retain the exact source bytes where redistribution and access constraints permit;
2. record exact title, authors or named team, publisher, version, date, URL, retrieval time,
   media type, digest, byte size, license and access constraints, and limitations;
3. distinguish research papers, official standards metadata, official standard text, company
   self-report, product manual, dataset bytes, and independent assessment;
4. obtain domain, human-factors, causal, statistical, data-governance, and safety review as
   applicable;
5. create new append-only source-ledger and protocol successors without overwriting an earlier
   release; and
6. keep operator acceptance, scientific evidence, safety assurance, and publication authority
   separate.

No linked source in this document currently satisfies those steps.
